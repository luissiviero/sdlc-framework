"""Command-line face of the review pass (build guide step 26), called by ``/sdlc-deploy`` and
by the review job in CI.

    python "${CLAUDE_PLUGIN_ROOT}/plugin/review/cli.py" prompt --root . --id 0001 [--base <ref>]
    python cli.py validate --root . --id 0001 [--base <ref>] [--no-record]
    python cli.py check-run --root . --id 0001 --phase deploy

``prompt`` prints ``REVIEW_PROMPT.md`` with the change filled in — plain text, handed to a
context that did not write the code (decision 12). ``validate`` reads
``changes/<id>-<slug>/evidence/review-findings.json``, checks it against HEAD, adds the
framework findings no model is needed for, recomputes the tally, writes the file back,
records the signatures in ``changes/.review-seen.json`` and prints the JSON verdict.
``check-run`` publishes the summary as the ``sdlc/review`` check run (article p.33 step 3:
"the severity counts that the check run publishes as a machine-readable tally").

Exit codes: 0 ok, 3 the findings file is missing or does not validate (the deploy runbook
re-requests the review once, then parks), 2 usage.
"""

from __future__ import annotations

import argparse
import importlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from gate import artifacts as art  # noqa: E402
from gate import diff as diffmod  # noqa: E402
from hooks._common import utf8_stdout  # noqa: E402
from review import findings as fmod  # noqa: E402
from state import conventions as c  # noqa: E402
from state import gitops  # noqa: E402
from state import status as status_mod

PROMPT_FILE = Path(__file__).resolve().parent / "REVIEW_PROMPT.md"
EXIT_OK, EXIT_USAGE, EXIT_INVALID = 0, 2, 3


def _emit(obj: Any) -> None:
    print(json.dumps(obj, indent=2, sort_keys=True))


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _posix(path: Path) -> str:
    return str(Path(path).resolve()).replace("\\", "/")


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n"
    )


def _change(args) -> tuple[Path, Path, status_mod.Status] | None:
    root = Path(args.root).resolve()
    change_dir = c.find_change_dir(root, args.id)
    if change_dir is None:
        print(f"no change folder for id {args.id}", file=sys.stderr)
        return None
    return root, change_dir, status_mod.read_status(change_dir)


def _base_ref(root: Path, base: str | None) -> str:
    if base:
        return base
    try:
        return diffmod.default_base(root)
    except diffmod.GitUnavailable:
        return "HEAD"


# --- prompt ----------------------------------------------------------------------------------
def render_prompt(
    template: str,
    change_id: str,
    title: str,
    branch: str,
    head: str,
    base: str,
    root: str,
    change_dir: str,
) -> str:
    """``REVIEW_PROMPT.md`` with its seven placeholders filled (the JSON example doubles its
    braces, so ``str.format`` leaves it alone)."""
    return template.format(
        change_id=change_id,
        title=title,
        branch=branch,
        head=head,
        base=base,
        root=root,
        change_dir=change_dir,
    )


RISK_SECTION = """
## Risk-list items this change touches (decision 35)
A risk-list hit does not park the change: it is a line of the "Needs your close look" banner
on this pull request, and the owner's approving review accepts it
(decision 36). You brief the owner on each item
below, in a second file, `{brief}`, one section per item, its name exactly as listed:

```markdown
# Security & policy brief, gate (deploy)

## <item>
- Verdict: continue
- What the change does to it: <one or two sentences, with the files>
- What could break: <one or two sentences>
- How to undo it: <one or two sentences>
```

Your verdict on an item is `continue` or `park`; you never accept a risk. Say park on an
item only for what is an Important finding anyway, and report that finding too: a park on
a risk item is the owner's and never goes to the review panel.

{items}
"""


def risk_section(root: Path, change_id: str, base: str | None) -> str:
    """The prompt's last section when the committed diff touches risk-list items (decision
    35): the items gate (deploy) will report, with where each matched, and the brief file the
    pass writes for them; "" when nothing hits or the hits cannot be read (the gate reports
    them anyway, and the banner then says no brief was written)."""
    from gate import gate as gate_mod  # noqa: PLC0415

    try:
        found = gate_mod.risk_hits_now(root, change_id, c.DEPLOY, base)
    except Exception:  # noqa: BLE001 - the prompt never fails on the risk read
        return ""
    hits = found.get("hits") or {}
    if not hits:
        return ""
    accepted = {str(a).lower() for a in found.get("accepted") or []}
    lines = [
        f"- `{item}`: {', '.join(where[:5])}"
        + (
            " (accepted earlier; brief it for what this change does now)"
            if item.lower() in accepted
            else ""
        )
        for item, where in hits.items()
    ]
    return RISK_SECTION.format(brief=found.get("brief"), items="\n".join(lines))


def cmd_prompt(args) -> int:
    loaded = _change(args)
    if loaded is None:
        return EXIT_USAGE
    root, change_dir, st = loaded
    head = diffmod.head_sha(root) or ""
    branch = gitops.current_branch(root) if gitops.is_repo(root) else ""
    text = render_prompt(
        PROMPT_FILE.read_text(encoding="utf-8"),
        change_id=st.id,
        title=st.title,
        branch=branch,
        head=head,
        base=_base_ref(root, args.base),
        root=_posix(root),
        change_dir=_posix(change_dir),
    )
    text = text.rstrip("\n") + "\n" + risk_section(root, st.id, args.base)
    sys.stdout.write(text if text.endswith("\n") else text + "\n")
    return EXIT_OK


# --- validate --------------------------------------------------------------------------------
def _load(path: Path) -> tuple[dict[str, Any] | None, str]:
    if not path.is_file():
        return None, f"evidence/{art.REVIEW_FINDINGS} is missing: the review pass has not run"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return None, f"evidence/{art.REVIEW_FINDINGS} is unreadable: {exc}"
    if not isinstance(data, dict):
        return None, f"evidence/{art.REVIEW_FINDINGS} is not a JSON object"
    return data, ""


def _framework(root: Path, change_dir: Path, st, base: str | None) -> tuple[list[dict], str]:
    """The findings the rules decide on their own, for the diff base...HEAD."""
    try:
        d = diffmod.collect(root, base)
    except diffmod.GitUnavailable as exc:
        return [], f"no diff available: {exc}"
    ref = d.merge_base or d.base
    items = fmod.framework_findings(
        root, change_dir, st, d.files, lambda rel: diffmod.file_at(root, ref, rel) is not None
    )
    return items, d.note


def cmd_validate(args) -> int:
    loaded = _change(args)
    if loaded is None:
        return EXIT_USAGE
    root, change_dir, st = loaded
    path = change_dir / art.EVIDENCE_DIR / art.REVIEW_FINDINGS
    empty = {"tally": {}, "important": [], "repeated": [], "proposals": [], "summary": ""}
    data, error = _load(path)
    if data is None:
        _emit({"ok": False, "problems": [error], **empty})
        return EXIT_INVALID
    head = diffmod.head_sha(root)
    problems = fmod.validate(data, head)
    if problems:
        # A malformed or stale file is never rewritten: the reviewer is asked again for this
        # HEAD (/sdlc-deploy step 1), and what it wrote stays as it wrote it.
        _emit({"ok": False, "problems": problems, **empty})
        return EXIT_INVALID

    extra, note = _framework(root, change_dir, st, args.base)
    known = {fmod.signature(f) for f in data.get("findings", []) if isinstance(f, dict)}
    data["findings"] = list(data.get("findings", [])) + [
        f for f in extra if fmod.signature(f) not in known
    ]
    data = fmod.normalise(data)
    data.setdefault("at", _now())
    _write_json(path, data)

    record_path = fmod.seen_record_path(root)
    record, _err = _load(record_path)
    updated, repeated = fmod.update_seen(record or {}, data["findings"], st.id, _now())
    if not args.no_record:
        _write_json(record_path, updated)
    proposals = fmod.claude_md_lines(repeated)
    # HANDOFF 6(f): a finding about CLAUDE.md itself is proposed the first time it is seen
    for line in fmod.claude_md_first_time_lines(data["findings"], st.id):
        if line not in proposals:
            proposals.append(line)
    proposals_path = change_dir / art.EVIDENCE_DIR / fmod.PROPOSALS_FILE
    if proposals:
        proposals_path.parent.mkdir(parents=True, exist_ok=True)
        header = (
            '<!-- Proposed CLAUDE.md lines under "Things Claude gets wrong" (article p.34 '
            "step 5). The PR description quotes this file; only the owner edits CLAUDE.md. -->\n"
        )
        proposals_path.write_text(
            header + "\n".join(proposals) + "\n", encoding="utf-8", newline="\n"
        )
    elif proposals_path.exists():
        proposals_path.unlink()

    _emit(
        {
            "ok": True,
            "problems": [],
            "note": note,
            "tally": data["tally"],
            "important": fmod.important(data),
            "repeated": repeated,
            "proposals": proposals,
            "summary": fmod.render_summary(data),
        }
    )
    return EXIT_OK


# --- check-run --------------------------------------------------------------------------------
def _not_evidence_since(root: Path, change_dir: Path, reviewed: str, final: str) -> str:
    """ "" when ``final`` is ``reviewed`` or follows it with only evidence and the run record
    (``findings.allowed_after_review``), else the reason the check is not green there."""
    if not reviewed or not final:
        return "the reviewed commit or the final head is unknown"
    if reviewed == final:
        return ""
    if not diffmod.is_ancestor(root, reviewed, final):
        return f"the final head {final[:10]} does not follow the reviewed {reviewed[:10]}"
    rel = str(Path(change_dir).resolve().relative_to(Path(root).resolve())).replace("\\", "/")
    # every path a commit touched, a rename's both sides and a type change included (the R22
    # review, finding 3: git's default rename detection lists only the new path)
    try:
        out = subprocess.run(
            ["git", "diff", "--name-only", "--no-renames", "-z", f"{reviewed}..{final}"],
            cwd=str(root), capture_output=True, text=True, encoding="utf-8", timeout=120,
        )  # fmt: skip
    except (OSError, subprocess.SubprocessError) as exc:
        return f"the commits after the reviewed one could not be listed: {exc}"
    if out.returncode != 0:
        return "the commits after the reviewed one could not be listed"
    files = [f for f in out.stdout.split("\0") if f]
    other = [f for f in files if not fmod.allowed_after_review(f, rel)]
    if other:
        return f"commits after the reviewed {reviewed[:10]} change: {', '.join(other[:5])}"
    return ""


def cmd_check_run(args) -> int:
    """Publish the tally as the ``sdlc/review`` check run. It never fails the run: with no
    GitHub route (no remote, no ``pr/github.py``, no credentials) the summary was already
    printed by ``validate`` and the PR description carries it."""
    loaded = _change(args)
    if loaded is None:
        return EXIT_USAGE
    root, change_dir, _st = loaded
    path = change_dir / art.EVIDENCE_DIR / art.REVIEW_FINDINGS
    data, error = _load(path)
    if data is None:
        _emit({"ok": False, "problems": [error], "route": "none"})
        return EXIT_INVALID
    data = fmod.normalise(data)
    tally = data["tally"]
    conclusion = "success" if tally["important"] == 0 else "failure"
    title = f"{tally['important']} Important, {tally['nit']} nits"
    summary = fmod.render_summary(data)
    reviewed = str(data.get("head") or "")
    head = str(reviewed or diffmod.head_sha(root) or "")
    if getattr(args, "final_head", False):
        # R22 (decision 36, point 3): the runner posts the check again on the build PR's
        # final head, after its own last commit; green only while every commit after the
        # reviewed one is evidence or the run record, which is what the merge step accepts
        final = diffmod.head_sha(root) or ""
        later = _not_evidence_since(root, change_dir, reviewed, final)
        if later:
            conclusion = "failure"
            title = f"{title}; commits after the reviewed one"
            summary = f"{summary}\n\n{later}"
        head = final or head
    repo = gitops.github_repo(root) if gitops.is_repo(root) else None
    if not repo:
        _emit({"route": "none", "reason": "no GitHub remote: nothing to post the check run to"})
        return EXIT_OK
    try:
        github = importlib.import_module("pr.github")
        create = github.create_check_run
    except (ImportError, AttributeError) as exc:
        _emit({"route": "none", "reason": f"pr/github.py cannot post a check run: {exc}"})
        return EXIT_OK
    try:
        result = create(repo, head, fmod.CHECK_RUN_NAME, conclusion, title, summary, cwd=root)
    except Exception as exc:  # noqa: BLE001 - a missing token must not fail the phase
        _emit({"route": "none", "reason": f"check run not posted: {exc!r}"})
        return EXIT_OK
    if isinstance(result, dict) and (result.get("route") == "none" or result.get("ok") is False):
        # pr/github.py reports "no route" (no gh, no token, a user token that may not create
        # check runs) instead of raising: the summary still reaches the owner in the PR body.
        _emit(
            {
                "route": "none",
                "reason": result.get("reason", "no route to GitHub"),
                "result": result,
            }
        )
        return EXIT_OK
    _emit(
        {
            "route": "check-run",
            "repo": repo,
            "name": fmod.CHECK_RUN_NAME,
            "phase": args.phase,
            "head": head,
            "conclusion": conclusion,
            "title": title,
            "tally": tally,
            "result": result,
        }
    )
    return EXIT_OK


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="sdlc-review", description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)
    for name, fn in (
        ("prompt", cmd_prompt),
        ("validate", cmd_validate),
        ("check-run", cmd_check_run),
    ):
        s = sub.add_parser(name)
        s.add_argument("--root", default=".")
        s.add_argument("--id", required=True)
        s.add_argument("--base", default=None, help="base ref for the diff (default: origin HEAD)")
        if name == "validate":
            s.add_argument(
                "--no-record",
                action="store_true",
                help="do not write changes/.review-seen.json (a dry run)",
            )
        if name == "check-run":
            s.add_argument("--phase", default=c.DEPLOY, choices=c.PHASES)
            s.add_argument(
                "--final-head",
                action="store_true",
                help="post on HEAD, green only if every commit since the reviewed one is "
                "evidence or the run record (the runner, at deploy)",
            )
        s.set_defaults(fn=fn)
    return p


def main(argv: list[str] | None = None) -> int:
    utf8_stdout()  # the prompt carries ``≠``; a cp1252 pipe on Windows raised on it
    args = build_parser().parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
