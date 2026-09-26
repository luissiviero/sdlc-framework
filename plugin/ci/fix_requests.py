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
  to ``gh`` with the same rule, as before).

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


def partition(
    reviews: list[dict[str, Any]],
    threads: list[dict[str, Any]],
    comments: list[dict[str, Any]],
    identities: list[str],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """(requests, not_applied) from the three listings, in their own order: reviews, then
    the threads' comments, then the PR comments."""
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
            DISMISSED if state == "DISMISSED" else None,
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
        judge(_entry("comment", comment), comment)
    return keep, drop


def collect(
    repo: str, number: int, github: Any, config: dict[str, Any], cwd: Path | None = None
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
        identities,
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


def collect_and_write(
    change_dir: Path,
    repo: str,
    number: int,
    github: Any,
    config: dict[str, Any],
    head: str | None,
    cwd: Path | None = None,
) -> dict[str, Any]:
    """Collect, write the file and return a summary for the run's own output."""
    result = collect(repo, number, github, config, cwd=cwd)
    data = {
        "schema_version": SCHEMA_VERSION,
        "repo": repo,
        "pr_number": int(number),
        "head": head,
        "collected_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
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
