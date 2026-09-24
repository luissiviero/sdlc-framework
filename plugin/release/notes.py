"""Release notes of a change (build guide step 32.2; decision 13).

    python notes.py --root <project> --id 0001 [--base <ref>] [--write]

Deterministic markdown, from files and git only (no network, no timestamps in the body). The
commit list leaves out evidence-only commits (the pathspec ``EVIDENCE_ONLY``): the commit that
stores these notes, and the gate and review evidence of every re-run, touch only
``evidence/``, so a re-run of ``/sdlc-deploy`` after a review comment gives the same text
unless the code itself changed:

    # Release notes — change <id>: <title>
    ## What changed      the first sentence of the intent's "## Proposed outcome" (else the title)
    ## Commits           one bullet per commit since the merge base with the default branch
                         that changes something outside changes/*/evidence/
    ## Evidence          the evidence status line of the PR summary (pr/description.py)
    ## Review findings   the tally of evidence/review-findings.json
    ## Links             intent.md, spec.md, plan.md, relative to evidence/release-notes.md

``--write`` stores it as ``changes/<id>-<slug>/evidence/release-notes.md`` (UTF-8, LF) and
prints the path; without it the notes go to stdout. Exit codes: 0 done, 2 usage error (no
change folder). Argument lists only; no shell.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

PLUGIN_DIR = Path(__file__).resolve().parent.parent
if str(PLUGIN_DIR) not in sys.path:
    sys.path.insert(0, str(PLUGIN_DIR))

from gate import artifacts as art  # noqa: E402
from state import conventions as c  # noqa: E402

NOTES_FILE = "release-notes.md"
LINKED = ("intent.md", "spec.md", "plan.md")
NO_HISTORY = "(no git history available)"
# git log pathspecs: the whole tree except the files under changes/<change>/evidence/ (a plain
# ":(exclude)changes/*/evidence" excludes nothing: a wildcard pathspec does not match the
# files below the directory it names)
EVIDENCE_ONLY = (".", ":(exclude,glob)changes/*/evidence/**")
LIST_ITEM_RE = re.compile(r"^\s*(?:[-*]|\d+[.)])\s+(?P<text>.+)$")
SENTENCE_RE = re.compile(r"(?s)^(.*?[.!?])(?:\s|$)")


def _git(root: Path, *args: str) -> str | None:
    """stdout of one git call, or None when git fails or cannot be started."""
    try:
        proc = subprocess.run(
            ["git", *args],
            cwd=str(root),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=60,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return proc.stdout if proc.returncode == 0 else None


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def _first_sentence(body: str) -> str:
    for raw in (body or "").splitlines():
        line = raw.strip()
        if not line or line.startswith(("#", ">", "|")):
            continue
        m = LIST_ITEM_RE.match(line)
        if m:
            line = m.group("text").strip()
        m = SENTENCE_RE.match(line)
        return (m.group(1) if m else line).strip()
    return ""


def _title(change_dir: Path, intent: str) -> str:
    try:
        from state import status as status_mod

        title = status_mod.read_status(change_dir).title
        if title:
            return title
    except Exception:  # noqa: BLE001 - fall back to the intent's heading
        pass
    m = c.DIR_RE.match(change_dir.name)
    return art.intent_title(intent) or (m.group("slug") if m else change_dir.name)


def commits(root: Path, base: str | None = None) -> list[str] | None:
    """``<short sha> <subject>`` per commit since the merge base of ``base`` (default: the
    default branch) and HEAD, oldest first, leaving out commits that touch only
    ``changes/*/evidence/`` (EVIDENCE_ONLY); None when git has no history to give."""
    if _git(root, "rev-parse", "--is-inside-work-tree") is None:
        return None
    if base is None:
        try:
            from gate import diff as diffmod

            base = diffmod.default_base(root)
        except Exception:  # noqa: BLE001 - no base: only HEAD is known
            base = "HEAD"
    if base.startswith("-"):
        return None
    merge_base = (_git(root, "merge-base", base, "HEAD") or "").strip()
    if not merge_base:
        return None
    out = _git(
        root, "log", "--reverse", "--format=%h %s", f"{merge_base}..HEAD", "--", *EVIDENCE_ONLY
    )
    if out is None:
        return None
    return [line.strip() for line in out.splitlines() if line.strip()]


def _evidence_line(change_dir: Path) -> str:
    try:
        from pr import description

        return description.evidence_status(change_dir, "e")
    except Exception as exc:  # noqa: BLE001 - the notes still render
        return f"evidence status unavailable: {exc!r}"


def _findings_line(change_dir: Path) -> str:
    path = change_dir / art.EVIDENCE_DIR / art.REVIEW_FINDINGS
    try:
        from gate import checks

        data, error = checks.load_findings(path)
    except Exception as exc:  # noqa: BLE001
        return f"review findings unavailable: {exc!r}"
    if data is None:
        return (
            f"no {art.REVIEW_FINDINGS}" if error == "missing" else f"{art.REVIEW_FINDINGS} {error}"
        )
    counts = {"important": 0, "nit": 0}
    for finding in data["findings"]:
        if isinstance(finding, dict):
            severity = str(finding.get("severity", "")).lower()
            if severity in counts:
                counts[severity] += 1
    return f"{counts['important']} Important, {counts['nit']} nits"


def build_notes(root: Path, change_id: str, base: str | None = None) -> str:
    """The release notes of ``change_id`` as markdown. Raises ValueError when the change
    folder does not exist."""
    root = Path(root).resolve()
    change_dir = c.find_change_dir(root, change_id)
    if change_dir is None:
        raise ValueError(f"no changes/{change_id}-<slug>/ folder under {root}")
    intent = _read(change_dir / "intent.md")
    title = _title(change_dir, intent)
    outcome = _first_sentence(art.split_sections(intent).get("## Proposed outcome", ""))
    lines = [f"# Release notes — change {change_id}: {title}", "", "## What changed", ""]
    lines.append(outcome or title)
    lines += ["", "## Commits", ""]
    found = commits(root, base)
    if found is None:
        lines.append(NO_HISTORY)
    elif not found:
        lines.append("(no commits since the base)")
    else:
        lines += [f"- {entry}" for entry in found]
    lines += ["", "## Evidence", "", _evidence_line(change_dir)]
    lines += ["", "## Review findings", "", _findings_line(change_dir)]
    lines += ["", "## Links", ""]
    links = [f"- [{name}](../{name})" for name in LINKED if (change_dir / name).is_file()]
    lines += links or ["(no intent.md, spec.md or plan.md in the change folder)"]
    return "\n".join(lines) + "\n"


def write_notes(root: Path, change_id: str, base: str | None = None) -> Path:
    root = Path(root).resolve()
    text = build_notes(root, change_id, base)
    change_dir = c.find_change_dir(root, change_id)
    assert change_dir is not None  # build_notes raised otherwise
    path = change_dir / art.EVIDENCE_DIR / NOTES_FILE
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")
    return path


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="sdlc-release-notes",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--root", default=".")
    p.add_argument("--id", required=True, help="change id, e.g. 0001")
    p.add_argument("--base", default=None, help="base ref (default: the default branch)")
    p.add_argument("--write", action="store_true", help="write evidence/release-notes.md")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    reconfigure = getattr(sys.stdout, "reconfigure", None)
    if callable(reconfigure):
        reconfigure(encoding="utf-8", errors="replace")
    try:
        if args.write:
            print(write_notes(Path(args.root), args.id, args.base))
        else:
            sys.stdout.write(build_notes(Path(args.root), args.id, args.base))
    except ValueError as exc:
        print(f"release-notes: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
