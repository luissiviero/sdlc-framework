"""The generated ``lessons/index.md`` (change 0003; `docs/proposals/okf-adoption.md` R1 on
``lessons/``).

    python plugin/lessons/index.py build --root <path> [--today YYYY-MM-DD]
    python plugin/lessons/index.py check --root <path> [--today YYYY-MM-DD]

``build`` rewrites ``lessons/index.md`` from every ``lessons/*.md`` file's frontmatter
(``README.md`` and ``index.md`` themselves excluded by name): a heading per first tag,
normalised (lower-case; spaces and underscores turned to hyphens) so a spelling drift
cannot split one class across two headings, ordered alphabetically; one line per lesson,
newest first within a heading (``detected.at`` descending, then file name ascending);
``## Retired`` last, grouping every lesson whose ``status`` is ``retired`` regardless of its
tags; ``## Unsorted`` after that, for a file whose frontmatter is missing, does not parse,
or lacks a field a normal line needs (title, description, a tag, ``detected.at`` and
``detected.tier``) — this never raises, so one bad file never stops the build. ``(stale)``
is appended to a line when ``stale_after`` is before ``--today`` (default: the real date).
``check`` exits 1 with a unified diff when the index on disk is not what ``build`` would
write, comparing with any ``(stale)`` suffix stripped from both sides first (so a lesson
crossing ``stale_after`` between two runs is not reported as drift); it prints one note line
per ``## Unsorted`` file either way. A ``detected.at`` or ``stale_after`` that is present but
not a date-shaped string (wrong type, or a month/day out of range) also sends the file to
``## Unsorted`` rather than raising, and a lesson file that is not UTF-8 does too.

The frontmatter is split the same way ``SKILL.md``'s is (``tests/test_policy_skills.py:28``):
a leading and a trailing ``---`` line, read with ``utf-8-sig`` to strip a BOM, then the text
between them parsed with ``plugin/state/yamlish.py`` (no third-party dependency, decision 7).
The index itself is markdown, not YAML, so it is written directly with
``Path.write_text(..., newline="\\n")`` for a byte-identical build on Windows and Linux;
``check`` reads the file on disk in Python's default universal-newline text mode first, so a
CRLF checkout does not false-positive as drift.
"""

from __future__ import annotations

import argparse
import calendar
import difflib
import re
import sys
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any

PLUGIN_DIR = Path(__file__).resolve().parent.parent
if str(PLUGIN_DIR) not in sys.path:
    sys.path.insert(0, str(PLUGIN_DIR))

from state import yamlish  # noqa: E402

LESSONS_DIR = "lessons"
INDEX_FILE = "index.md"
README_FILE = "README.md"
EXCLUDED_FILES = {INDEX_FILE, README_FILE}
RETIRED_STATUS = "retired"
RETIRED_HEADING = "## Retired"
UNSORTED_HEADING = "## Unsorted"
NO_LESSONS_LINE = "No lessons yet."

FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n(.*)$", re.S)
HEADING_RE = re.compile(r"^#{1,6}\s+(\S.*)$")
STALE_SUFFIX_RE = re.compile(r" \(stale\)$", re.MULTILINE)
DATE_RE = re.compile(r"^(\d{4})-(\d{2})")
DATE_SHAPE_RE = re.compile(r"^\d{4}-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])")


@dataclass
class Entry:
    """One lesson file, either rendered or sent to ``## Unsorted``."""

    file_name: str
    ok: bool
    error: str = ""
    heading: str = ""  # the file's first markdown heading, shown when not ok
    title: str = ""
    description: str = ""
    tags: list[str] = field(default_factory=list)
    tier: int | None = None
    detected_at: str = ""
    status: str = "stable"
    stale_after: str | None = None


def _first_heading(text: str) -> str:
    for line in text.splitlines():
        m = HEADING_RE.match(line)
        if m:
            return m.group(1).strip()
    return ""


def _missing_render_fields(fm: dict[str, Any]) -> list[str]:
    problems = []
    if not isinstance(fm.get("title"), str) or not fm["title"].strip():
        problems.append("missing title")
    if not isinstance(fm.get("description"), str) or not fm["description"].strip():
        problems.append("missing description")
    tags = fm.get("tags")
    if not isinstance(tags, list) or not tags:
        problems.append("missing tags")
    detected = fm.get("detected")
    if not isinstance(detected, dict) or not detected.get("at") or detected.get("tier") is None:
        problems.append("missing detected.at or detected.tier")
    return problems


def _bad_field_shapes(fm: dict[str, Any]) -> list[str]:
    """Fields that are present but not the date-shaped string a render needs (wrong type, or
    a month/day out of range): caught here so a bad value sends the file to ``## Unsorted``
    instead of raising later in ``_month_label`` or ``is_stale``."""
    problems = []
    detected = fm.get("detected")
    at = detected.get("at") if isinstance(detected, dict) else None
    if at is not None and not (isinstance(at, str) and DATE_SHAPE_RE.match(at)):
        problems.append(f"detected.at {at!r} is not a date")
    stale_after = fm.get("stale_after")
    if stale_after is not None and not (
        isinstance(stale_after, str) and DATE_SHAPE_RE.match(stale_after)
    ):
        problems.append(f"stale_after {stale_after!r} is not a date")
    return problems


def _read_text(path: Path) -> tuple[str | None, str]:
    try:
        return path.read_text(encoding="utf-8-sig"), ""
    except (OSError, UnicodeDecodeError) as exc:
        return None, str(exc)


def _split(text: str) -> tuple[str, str] | None:
    """(frontmatter text, body) on a leading-and-trailing ``---``, or None: the one place
    that owns the split (as ``SKILL.md``'s reader does, ``tests/test_policy_skills.py:28``),
    so the body (which may itself contain ``key: value``-shaped prose) is never handed to
    the YAML reader."""
    m = FRONTMATTER_RE.match(text)
    return (m.group(1), m.group(2)) if m else None


def read_frontmatter(path: Path) -> tuple[dict[str, Any] | None, str]:
    """(the frontmatter mapping, "") or (None, why): unreadable, no frontmatter block, a
    YAML error, or a document that is not a mapping. No render-field validation — the caller
    (``read_entry`` for the index, ``gate.checks.lesson_and_eval`` for the full required set)
    decides what it needs."""
    text, why = _read_text(path)
    if text is None:
        return None, why
    split = _split(text)
    if split is None:
        return None, "no frontmatter block"
    try:
        fm = yamlish.loads(split[0])
    except yamlish.YamlishError as exc:
        return None, str(exc)
    if not isinstance(fm, dict):
        return None, "frontmatter is not a mapping"
    return fm, ""


def read_entry(path: Path) -> Entry:
    """A lesson file read into an ``Entry``. Never raises: a bad file is sent to
    ``## Unsorted`` with the reason, not a crash."""
    text, why = _read_text(path)
    if text is None:
        return Entry(path.name, ok=False, error=why, heading=path.stem)
    split = _split(text)
    if split is None:
        return Entry(
            path.name, ok=False, error="no frontmatter block", heading=_first_heading(text)
        )
    fm_text, body = split
    try:
        fm = yamlish.loads(fm_text)
    except yamlish.YamlishError as exc:
        return Entry(path.name, ok=False, error=str(exc), heading=_first_heading(body))
    if not isinstance(fm, dict):
        return Entry(
            path.name, ok=False, error="frontmatter is not a mapping", heading=_first_heading(body)
        )
    problems = _missing_render_fields(fm) + _bad_field_shapes(fm)
    if problems:
        return Entry(path.name, ok=False, error="; ".join(problems), heading=_first_heading(body))
    detected = fm["detected"]
    return Entry(
        path.name,
        ok=True,
        title=fm["title"],
        description=fm["description"],
        tags=[str(t) for t in fm["tags"]],
        tier=detected.get("tier"),
        detected_at=str(detected.get("at")),
        status=str(fm.get("status") or "stable"),
        stale_after=fm.get("stale_after"),
    )


def normalise_class(value: str) -> str:
    """``flaky-test``, ``flaky_test`` and ``Flaky Test`` all become ``flaky-test``, so a
    spelling drift never opens a second heading for the same class."""
    return re.sub(r"[ _]+", "-", value.strip().lower())


def _month_label(at: Any) -> str:
    if not isinstance(at, str):
        return ""
    m = DATE_RE.match(at)
    if not m:
        return ""
    year, month = int(m.group(1)), int(m.group(2))
    if not 1 <= month <= 12:
        return ""
    return f"{calendar.month_abbr[month]} {year}"


def _date_only(value: Any) -> str:
    return value[:10] if isinstance(value, str) else ""


def is_stale(stale_after: str | None, today: str) -> bool:
    return bool(stale_after) and _date_only(stale_after) < _date_only(today)


def _sort_entries(entries: list[Entry]) -> list[Entry]:
    """Newest first (``detected.at`` descending), file name ascending on a tie. Two stable
    sorts (by file name, then by date) rather than one combined key: ``sorted(reverse=True)``
    reverses the comparison, not the result, so ties keep the order they arrived in."""
    by_file = sorted(entries, key=lambda e: e.file_name)
    return sorted(by_file, key=lambda e: e.detected_at, reverse=True)


def _escape_link_text(value: str) -> str:
    """Markdown link text: a literal ``\\``, ``[`` or ``]`` would otherwise end the link
    early or nest another one."""
    return value.replace("\\", "\\\\").replace("[", "\\[").replace("]", "\\]")


def _escape_link_target(value: str) -> str:
    """Markdown link target: a literal ``(``, ``)`` or space would otherwise end the link
    target early or split it in two."""
    return value.replace("(", "%28").replace(")", "%29").replace(" ", "%20")


def _render_line(e: Entry, today: str) -> str:
    link = f"[{_escape_link_text(e.title)}]({_escape_link_target(e.file_name)})"
    line = (
        f"* {link} - {e.description}. Tier {e.tier}, "
        f"{_month_label(e.detected_at)}. Tags: {', '.join(e.tags)}."
    )
    if is_stale(e.stale_after, today):
        line += " (stale)"
    return line


def _render_unsorted_line(e: Entry) -> str:
    text = e.heading or e.file_name
    return f"* [{_escape_link_text(text)}]({_escape_link_target(e.file_name)})"


def build_index_text(entries: list[Entry], today: str) -> str:
    stable = [e for e in entries if e.ok and e.status != RETIRED_STATUS]
    retired = [e for e in entries if e.ok and e.status == RETIRED_STATUS]
    unsorted = [e for e in entries if not e.ok]

    blocks: list[list[str]] = [["# Lessons"]]
    if not stable and not retired and not unsorted:
        blocks.append([NO_LESSONS_LINE])
        return "\n\n".join("\n".join(b) for b in blocks) + "\n"

    groups: dict[str, list[Entry]] = {}
    for e in stable:
        groups.setdefault(normalise_class(e.tags[0]), []).append(e)
    for cls in sorted(groups):
        blocks.append([f"## {cls}"] + [_render_line(e, today) for e in _sort_entries(groups[cls])])
    if retired:
        blocks.append([RETIRED_HEADING] + [_render_line(e, today) for e in _sort_entries(retired)])
    if unsorted:
        by_name = sorted(unsorted, key=lambda e: e.file_name)
        blocks.append([UNSORTED_HEADING] + [_render_unsorted_line(e) for e in by_name])
    return "\n\n".join("\n".join(b) for b in blocks) + "\n"


def _read_entries(lessons_dir: Path) -> list[Entry]:
    entries = []
    for path in sorted(lessons_dir.glob("*.md")):
        if path.name in EXCLUDED_FILES:
            continue
        entries.append(read_entry(path))
    return entries


def build(root: Path, today: str | None = None) -> tuple[str, list[str]]:
    """The index text and one note per ``## Unsorted`` file (``"<file>: <reason>"``)."""
    lessons_dir = Path(root) / LESSONS_DIR
    entries = _read_entries(lessons_dir)
    text = build_index_text(entries, today or date.today().isoformat())
    notes = [f"{e.file_name}: {e.error}" for e in entries if not e.ok]
    return text, notes


def check(root: Path, today: str | None = None) -> tuple[bool, str, list[str]]:
    """(ok, unified diff or "", notes). A diff is reported only when the generated text
    differs once any ``(stale)`` suffix is stripped from both sides."""
    text, notes = build(root, today)
    index_path = Path(root) / LESSONS_DIR / INDEX_FILE
    current = index_path.read_text(encoding="utf-8") if index_path.is_file() else ""
    if STALE_SUFFIX_RE.sub("", current) == STALE_SUFFIX_RE.sub("", text):
        return True, "", notes
    diff = "\n".join(
        difflib.unified_diff(
            current.splitlines(),
            text.splitlines(),
            fromfile="lessons/index.md (on disk)",
            tofile="lessons/index.md (built)",
            lineterm="",
        )
    )
    return False, diff, notes


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="index.py", description="The generated lessons/index.md.")
    sub = p.add_subparsers(dest="command", required=True)
    for name in ("build", "check"):
        cmd = sub.add_parser(name)
        cmd.add_argument("--root", default=".")
        cmd.add_argument("--today", default=None)
    return p


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    root = Path(args.root)
    if args.command == "build":
        text, notes = build(root, args.today)
        (root / LESSONS_DIR).mkdir(parents=True, exist_ok=True)
        index_path = root / LESSONS_DIR / INDEX_FILE
        index_path.write_text(text, encoding="utf-8", newline="\n")
        for note in notes:
            print(f"## Unsorted: {note}")
        print(f"wrote {(Path(LESSONS_DIR) / INDEX_FILE).as_posix()}")
        return 0
    ok, diff, notes = check(root, args.today)
    for note in notes:
        print(f"## Unsorted: {note}")
    if not ok:
        print(diff)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
