"""Command-line face of the review pass (build guide step 26), called by ``/sdlc-deploy`` and
by the review job in CI.

    python "${CLAUDE_PLUGIN_ROOT}/plugin/review/cli.py" prompt --root . --id 0001 [--base <ref>]
    python cli.py validate --root . --id 0001 [--base <ref>] [--no-record]
    python cli.py check-run --root . --id 0001 --phase e

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
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from gate import artifacts as art  # noqa: E402
from gate import diff as diffmod  # noqa: E402
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
    head = str(data.get("head") or diffmod.head_sha(root) or "")
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
            s.add_argument("--phase", default="e", choices=c.PHASES)
        s.set_defaults(fn=fn)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
