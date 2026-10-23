"""Collect the fix round's change requests before the model's session starts (0.2.24).

    python framework/plugin/ci/fix_requests.py --root . --id 0001 --repo owner/name --pr-number 12

The workflow gate of ``sdlc-fix.yml`` (D9, 0.2.21) decides who *starts* a round; ``/sdlc-fix``
step 1 (0.2.23) says whose words reach it: reviews and comments whose ``author_association``
is ``OWNER``, ``MEMBER`` or ``COLLABORATOR``, never a ``[bot]``. As prompt text that rule had
two holes (session-7 review): the model still read the non-member's text before applying
it, and a member whose organization membership is private reads as ``CONTRIBUTOR`` or
``NONE`` and was dropped. Here the run collects every review (REST), every review thread
with its resolved flag (GraphQL) and every PR comment (REST) through ``pr/github.py``,
judges each one by the same rule, and writes ``changes/<id>-<slug>/evidence/fix-requests.json``:

- ``requests``: what the round applies - one entry per review with text, per comment of an
  unresolved review thread and per PR comment, with its author, association, text, time,
  link and (for a thread comment) path, line and thread id;
- ``not_applied``: everything else, each with ``why`` (``not applied: not a member of the
  repository``, ``… a bot``, ``… the automation identity``, ``… the thread is resolved``,
  ``… the review was dismissed``) and **without its text** (``body`` null, ``chars`` its
  length): what is not applied is not read either, and the file is committed with the change
  folder. The command copies the lines (author, link, why) into ``evidence/fix-response.md``.
  A review without text is neither: its comments come through its threads;
- ``head``: the commit the run started from, so a by-hand round reads the file only while it
  is current; ``unavailable``: the reason when a reader failed (the command then falls back
  to ``gh`` with the same rule, as before);
- ``applied_earlier`` (decision 34, point 6): a PR comment cannot be resolved and a comment
  review cannot be dismissed, so the round marks each request it applied with ``"applied":
  true`` (``/sdlc-fix`` step 6) and the next round, before it rewrites the file, carries
  every marked ``{kind, id}`` and the earlier file's own ``applied_earlier`` forward: a
  review or a PR comment with such a kind and id goes to ``not_applied`` (``… applied by an
  earlier round``), without its text. Review threads keep the resolved rule and are never
  carried. The session writes the marks and nothing else: after it, the runner restores
  the file to its own copy with only those marks kept (``keep_marks_only``);
- ``trigger``: the link of the owner's ``@claude`` comment that started the round (the
  dispatcher's ``trigger`` input, ``SDLC_TRIGGER``, kept only when it is a comment link of
  this repository's pull requests, ``trigger_link``), null otherwise; until R11 the round's
  record of what started it.

The command's step 1 reads that file only, so the non-member's text is not in what the
session reads; the session still holds ``Bash(gh *)``, so "read none from the PR yourself"
stays a rule of the command, not a mechanism. The private-membership case is not solved here
- GitHub reports what it reports - but it is now visible: the dropped author and why are in
the file and in the response.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PLUGIN_DIR = Path(__file__).resolve().parent.parent  # <framework root>/plugin
if str(PLUGIN_DIR) not in sys.path:
    sys.path.insert(0, str(PLUGIN_DIR))

from gate import artifacts as art  # noqa: E402
from gate.policy import automation_identity, is_automation  # noqa: E402

FILE = "fix-requests.json"
SCHEMA_VERSION = 1
MEMBER_ASSOCIATIONS = ("OWNER", "MEMBER", "COLLABORATOR")
BOT_RE = re.compile(r"\[bot\]$")
NOT_A_MEMBER = "not applied: not a member of the repository"
A_BOT = "not applied: a bot"
AUTOMATION = "not applied: the automation identity"
RESOLVED = "not applied: the thread is resolved"
DISMISSED = "not applied: the review was dismissed"
APPLIED_EARLIER = "not applied: applied by an earlier round"
CARRIED_KINDS = ("review", "comment")  # what cannot be resolved or dismissed (decision 34)
EXIT_OK, EXIT_FAILED, EXIT_USAGE = 0, 1, 2


def why_not(
    author: str | None, kind: str | None, association: str | None, identities
) -> str | None:
    """None when the author's words reach the round, else the reason they do not."""
    login = str(author or "")
    if kind == "Bot" or BOT_RE.search(login):
        return A_BOT
    if is_automation(login, "", list(identities)):
        return AUTOMATION
    if str(association or "").upper() not in MEMBER_ASSOCIATIONS:
        return NOT_A_MEMBER
    return None


def _entry(kind: str, item: dict[str, Any], **extra: Any) -> dict[str, Any]:
    return {
        "kind": kind,
        "id": item.get("id"),
        "author": item.get("author"),
        "association": item.get("association"),
        "body": str(item.get("body") or ""),
        "at": item.get("at"),
        "url": item.get("url"),
        **extra,
    }


def _id_key(value: Any) -> str:
    return str(value).strip()


def _carried_key(kind: Any, ident: Any) -> tuple[str, str] | None:
    """``(kind, id)`` for a review or PR comment with a usable id, else None: review ids and
    comment ids come from separate sequences, so an id alone could name the other kind."""
    if kind not in CARRIED_KINDS or isinstance(ident, bool) or not isinstance(ident, (int, str)):
        return None
    return (str(kind), _id_key(ident)) if _id_key(ident) else None


def applied_earlier(change_dir: Path) -> list[dict[str, Any]]:
    """What earlier rounds applied (decision 34, point 6), read from the committed
    ``evidence/fix-requests.json`` before this round rewrites it: every review or PR comment
    request marked ``"applied": true`` plus the file's own ``applied_earlier``, each as
    ``{"kind", "id"}``. An absent or unreadable file is an empty list: the first round reads
    everything."""
    path = Path(change_dir) / art.EVIDENCE_DIR / FILE
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    if not isinstance(data, dict):
        return []
    found: dict[tuple[str, str], dict[str, Any]] = {}
    earlier = data.get("applied_earlier")
    for value in earlier if isinstance(earlier, list) else []:
        if isinstance(value, dict) and (key := _carried_key(value.get("kind"), value.get("id"))):
            found.setdefault(key, {"kind": key[0], "id": value["id"]})
    requests = data.get("requests")
    for entry in requests if isinstance(requests, list) else []:
        if not isinstance(entry, dict) or entry.get("applied") is not True:
            continue
        if key := _carried_key(entry.get("kind"), entry.get("id")):
            found.setdefault(key, {"kind": key[0], "id": entry["id"]})
    return [found[k] for k in sorted(found, key=lambda k: (k[0], len(k[1]), k[1]))]


def partition(
    reviews: list[dict[str, Any]],
    threads: list[dict[str, Any]],
    comments: list[dict[str, Any]],
    identities: list[str],
    carried: list[dict[str, Any]] | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """(requests, not_applied) from the three listings, in their own order: reviews, then
    the threads' comments, then the PR comments. A review or PR comment whose ``(kind, id)``
    is in ``carried`` (``applied_earlier``) is not applied again; a thread is never carried."""
    done = {
        key
        for value in carried or []
        if isinstance(value, dict) and (key := _carried_key(value.get("kind"), value.get("id")))
    }

    def earlier(kind: str, item: dict[str, Any]) -> str | None:
        return APPLIED_EARLIER if _carried_key(kind, item.get("id")) in done else None

    keep: list[dict[str, Any]] = []
    drop: list[dict[str, Any]] = []

    def judge(entry: dict[str, Any], item: dict[str, Any], settled: str | None = None) -> None:
        why = why_not(item.get("author"), item.get("type"), item.get("association"), identities)
        if why is None and settled:
            why = settled
        if why is None:
            keep.append(entry)
        else:
            # the text itself stays out of the file: what is not applied is not read either
            # (a non-member's text is the injection channel; session-8 review)
            drop.append({**entry, "body": None, "chars": len(entry["body"]), "why": why})

    for review in reviews:
        if not str(review.get("body") or "").strip():
            continue  # its comments come through the threads
        state = str(review.get("state") or "").upper()
        judge(
            _entry("review", review, state=state),
            review,
            DISMISSED if state == "DISMISSED" else earlier("review", review),
        )
    for thread in threads:
        for comment in thread.get("comments") or []:
            entry = _entry(
                "review_comment",
                comment,
                thread=thread.get("id"),
                path=thread.get("path"),
                line=thread.get("line"),
                outdated=bool(thread.get("outdated")),
            )
            judge(entry, comment, RESOLVED if thread.get("resolved") else None)
    for comment in comments:
        judge(_entry("comment", comment), comment, earlier("comment", comment))
    return keep, drop


def collect(
    repo: str,
    number: int,
    github: Any,
    config: dict[str, Any],
    cwd: Path | None = None,
    carried: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """The three listings read and judged: {'ok', 'requests', 'not_applied', 'unavailable',
    'route'}. A reader that fails makes the whole collection unavailable (never a partial
    list read as "nothing to apply")."""
    identities = automation_identity(config)
    reviews = github.pr_reviews(repo, number, cwd=cwd)
    threads = github.pr_review_threads(repo, number, cwd=cwd)
    comments = github.issue_comments(repo, number, cwd=cwd)
    for name, result in (("reviews", reviews), ("review threads", threads), ("comments", comments)):
        if not result.get("ok"):
            reason = f"the {name} could not be read: {result.get('reason') or 'failed'}"
            return {"ok": False, "unavailable": reason, "requests": [], "not_applied": []}
    keep, drop = partition(
        reviews.get("reviews") or [], threads.get("threads") or [], comments.get("comments") or [],
        identities, carried,
    )  # fmt: skip
    return {
        "ok": True,
        "unavailable": None,
        "requests": keep,
        "not_applied": drop,
        "route": reviews.get("route"),
    }


def write(change_dir: Path, data: dict[str, Any]) -> Path:
    path = change_dir / art.EVIDENCE_DIR / FILE
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n"
    )
    return path


def add_request(change_dir: Path, entry: dict[str, Any]) -> dict[str, Any]:
    """Add one request the run itself makes to ``evidence/fix-requests.json`` (decision 29:
    the ``red-targets`` request of an automatic round, built by ``ci/auto_round.py`` from the
    runner's own record, never from the PR). A request with the same ``kind`` and ``id`` is
    replaced, so a repeated step adds it once. Returns the summary the run prints."""
    path = Path(change_dir) / art.EVIDENCE_DIR / FILE
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        data = None
    if not isinstance(data, dict):
        data = {"schema_version": SCHEMA_VERSION, "ok": True, "requests": [], "not_applied": []}
    kept = [
        r
        for r in data.get("requests") or []
        if not (
            isinstance(r, dict)
            and r.get("kind") == entry.get("kind")
            and r.get("id") == entry.get("id")
        )
    ]
    data["requests"] = [*kept, entry]
    write(change_dir, data)
    return {
        "file": FILE,
        "kind": entry.get("kind"),
        "id": entry.get("id"),
        "requests": len(data["requests"]),
    }


TRIGGER_RE = re.compile(r"https://github\.com/([^/\s]+/[^/\s]+)/pull/\d+#issuecomment-\d+")


def trigger_link(value: Any, repo: str | None) -> str | None:
    """``value`` when it is the link of a pull request comment in ``repo`` (``https://
    github.com/<owner>/<repo>/pull/<n>#issuecomment-<id>``), else None. The input reaches
    the run from a dispatch, so anything else is dropped unread: never printed (a workflow
    command in the log) and never written into the file."""
    text = str(value or "").strip()
    match = TRIGGER_RE.fullmatch(text)
    if match is None or not repo or match.group(1).lower() != str(repo).strip().lower():
        return None
    return text


def snapshot(change_dir: Path) -> dict[str, Any] | None:
    """The file as the runner wrote it before the session (decision 34), or None when there
    is none to guard (absent or unreadable)."""
    try:
        data = json.loads((Path(change_dir) / art.EVIDENCE_DIR / FILE).read_text("utf-8"))
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) else None


def _without_uncarried_marks(data: Any) -> Any:
    """``data`` with ``"applied": true`` dropped from every entry that is never carried."""
    if not isinstance(data, dict) or not isinstance(data.get("requests"), list):
        return data
    copy = json.loads(json.dumps(data))
    for entry in copy["requests"]:
        if (
            isinstance(entry, dict)
            and entry.get("applied") is True
            and _carried_key(entry.get("kind"), entry.get("id")) is None
        ):
            del entry["applied"]
    return copy


def keep_marks_only(change_dir: Path, before: dict[str, Any] | None) -> str | None:
    """After the session: the only change the session may make to the file is ``"applied":
    true`` on a request (``/sdlc-fix`` step 6); only the marks on a review or PR comment are
    carried. Anything else (an edited ``applied_earlier``, an added, removed or edited entry) puts
    the runner's copy back with the legitimate marks kept, and returns the one line the run
    logs; None when the file is as allowed. A forged mark would hide an owner's request from
    every later round."""
    if before is None:
        return None
    after = snapshot(change_dir)
    requests = after.get("requests") if isinstance(after, dict) else None
    marks = {
        key
        for entry in (requests if isinstance(requests, list) else [])
        if isinstance(entry, dict)
        and entry.get("applied") is True
        and (key := _carried_key(entry.get("kind"), entry.get("id")))
    }
    expected = json.loads(json.dumps(before))
    for entry in expected.get("requests") or []:
        if isinstance(entry, dict) and _carried_key(entry.get("kind"), entry.get("id")) in marks:
            entry["applied"] = True
    if _without_uncarried_marks(after) == _without_uncarried_marks(expected):
        # a mark on a thread comment or the red-targets request is what step 6 asks for
        # too; it is never carried, so it is left as written and is not a forgery
        return None
    write(change_dir, expected)
    kept = sum(
        1 for e in expected.get("requests") or [] if isinstance(e, dict) and e.get("applied")
    )
    return (
        f"evidence/{FILE}: the session changed more than the applied marks; the runner's copy "
        f"is restored with {kept} mark(s) kept (decision 34)"
    )


def round_fields(change_dir: Path, trigger: str | None = None) -> dict[str, Any]:
    """What every rewrite of the file carries (decision 34): the ids earlier rounds applied,
    read from the file about to be replaced, and the link of the comment that started this
    round (null when the round was started another way)."""
    return {
        "applied_earlier": applied_earlier(change_dir),
        "trigger": str(trigger).strip() if trigger and str(trigger).strip() else None,
    }


def collect_and_write(
    change_dir: Path,
    repo: str,
    number: int,
    github: Any,
    config: dict[str, Any],
    head: str | None,
    cwd: Path | None = None,
    trigger: str | None = None,
) -> dict[str, Any]:
    """Collect, write the file and return a summary for the run's own output."""
    carried = round_fields(change_dir, trigger)
    result = collect(repo, number, github, config, cwd=cwd, carried=carried["applied_earlier"])
    data = {
        "schema_version": SCHEMA_VERSION,
        "repo": repo,
        "pr_number": int(number),
        "head": head,
        "collected_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        **carried,
        **result,
    }
    path = write(change_dir, data)
    return {
        "ok": result["ok"],
        "file": path.name,
        "requests": len(result["requests"]),
        "not_applied": len(result["not_applied"]),
        "unavailable": result["unavailable"],
    }


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="sdlc-fix-requests", description=__doc__.split("\n\n")[0])
    p.add_argument("--root", default=".")
    p.add_argument("--id", required=True, help="four-digit change id")
    p.add_argument("--repo", required=True, help="owner/name")
    p.add_argument("--pr-number", type=int, required=True)
    return p


def main(argv: list[str] | None = None) -> int:
    from pr import github  # noqa: PLC0415

    from hooks._common import ConfigError, load_sdlc_config  # noqa: PLC0415
    from state import conventions as c  # noqa: PLC0415

    args = build_parser().parse_args(argv)
    root = Path(args.root).resolve()
    change_dir = c.find_change_dir(root, args.id)
    if change_dir is None:
        print(f"no change folder for id {args.id}", file=sys.stderr)
        return EXIT_USAGE
    try:
        config = load_sdlc_config(str(root)) or {}
    except ConfigError:
        config = {}
    from gate import diff as gate_diff  # noqa: PLC0415

    head = gate_diff.head_sha(root) if gate_diff.is_repo(root) else None
    summary = collect_and_write(change_dir, args.repo, args.pr_number, github, config, head, root)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return EXIT_OK if summary["ok"] else EXIT_FAILED


if __name__ == "__main__":
    sys.exit(main())
