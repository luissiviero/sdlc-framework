"""Task runner for the SDLC framework repo (decision 7: one runner, Windows and Linux).

Usage: python tasks.py <task>
Tasks: test | lint | format | check | verify | notes-index | decisions-index | choices-index |
       docs-lint | next-free | version-check | help

Everything runs through ``sys.executable -m ...`` with argument lists (no shell), so the
same file works in cmd.exe, PowerShell, Git Bash and a Linux runner. ``notes-index`` runs in
this process: it rewrites ``docs/notes/index.md`` from the notes' frontmatter. So do
``decisions-index`` (``docs/decisions/index.md`` from each decision's heading),
``choices-index`` (``docs/progress/choices.md`` from the records' choices, ROADMAP R65) and
``docs-lint`` (the links, the notes' Claude Code versions and both indexes, ROADMAP R55; the
frontmatter, decision amendments, proposal statuses, shipped rows, version and PR pairs, moved
stubs and Portuguese words, ROADMAP R58; a number taken twice, a rank outside ROADMAP and a
retired term used as a live one, CLAUDE.md's verifying lines against ``sdlc.yaml``, R65).
``verify`` runs every check a pull request needs (ROADMAP R65, part 4). ``next-free`` reads git:
the next free choice, candidate, note, decision and patch on ``main`` and every fetched branch
ahead of it (ROADMAP R65, part 1). ``version-check`` fails a branch that bumps ``plugin.json``
to a version ``main`` already holds or a tag already has (ROADMAP R5's race, choice 257).
"""

from __future__ import annotations

import importlib.util
import json
import re
import shlex
import shutil
import subprocess
import sys
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parent


def _run(*args: str) -> int:
    cmd = [sys.executable, "-m", *args]
    print("$", " ".join(cmd), flush=True)
    return subprocess.call(cmd, cwd=ROOT)


def task_test() -> int:
    """Run the self-tests (layer 1) and the fixture integration tests (layer 2), on every core."""
    # pytest-xdist (pyproject's dev extra, 2026-10-13): the suite spends its time launching
    # processes (git, python, the fakes), not computing, and the Windows job of
    # framework-checks.yml paid about six times the Linux jobs' time for it; `-n auto` spreads
    # the tests over the runner's cores. It stays out of pyproject's addopts so that plain
    # `python -m pytest` keeps working where the dev extra is not reinstalled yet, and this
    # task falls back to one core there too. `worksteal` (2026-10-19): with the default `load`
    # the last few slow end-to-end tests ran on one worker while the others sat idle, about
    # three minutes at the end of the Windows job; an idle worker now takes over queued tests.
    if importlib.util.find_spec("xdist") is None:
        print("pytest-xdist is not installed: running the suite on one core", flush=True)
        return _run("pytest")
    return _run("pytest", "-n", "auto", "--dist", "worksteal")


def task_lint() -> int:
    """ruff check + ruff format --check; zero warnings is the bar (CLAUDE.md)."""
    rc = _run("ruff", "check", ".")
    rc2 = _run("ruff", "format", "--check", ".")
    return rc or rc2


def task_format() -> int:
    """Apply ruff formatting and safe fixes."""
    rc = _run("ruff", "format", ".")
    rc2 = _run("ruff", "check", "--fix", ".")
    return rc or rc2


def task_check() -> int:
    """lint then test; the pre-commit bar for this repo."""
    rc = task_lint()
    return rc or task_test()


# --- the pre-PR set (ROADMAP R65, part 4; choices 252 and 253) -----------------------------
# One owner for the local checks: `sdlc.yaml: commands` holds the build, test and lint
# commands, CLAUDE.md's "Verifying your work" quotes them (docs-lint check 13), and `verify`
# runs them, then the docs lint and `claude plugin validate .` where the CLI is installed.
# A command is split at `&&` and run as argument lists, `python` being this interpreter, so
# the same line runs in cmd.exe, PowerShell and bash. The test command `python -m pytest` runs
# as `tasks.py test`, the same pytest spread over the cores. CI runs `verify` (choice 253).
SDLC_YAML = ROOT / "sdlc.yaml"
COMMAND_KEYS = ("build", "test", "lint")
PYTEST_COMMAND = "python -m pytest"


def read_commands(path: Path | None = None) -> dict[str, str]:
    """``build``, ``test`` and ``lint`` from ``commands`` in ``sdlc.yaml`` ("" when unset)."""
    import yaml

    data = yaml.safe_load((path or SDLC_YAML).read_text(encoding="utf-8-sig")) or {}
    commands = data.get("commands") or {}
    return {key: str(commands.get(key) or "") for key in COMMAND_KEYS}


def command_steps(command: str) -> list[list[str]]:
    """Each ``&&`` part of a command as an argument list, a leading ``python`` replaced by
    this interpreter."""
    steps: list[list[str]] = []
    for part in command.split("&&"):
        args = shlex.split(part.strip())
        if args and args[0] == "python":
            args[0] = sys.executable
        if args:
            steps.append(args)
    return steps


def _run_steps(command: str) -> int:
    rc = 0
    for args in command_steps(command):
        print("$", " ".join(args), flush=True)
        rc = subprocess.call(args, cwd=ROOT) or rc
    return rc


def task_verify() -> int:
    """Every check a PR needs: sdlc.yaml's build, lint and test, docs-lint, the version check,
    plugin validate."""
    commands = read_commands()
    results: list[tuple[str, int | None]] = []
    for key in ("build", "lint"):
        results.append((key, _run_steps(commands[key]) if commands[key] else None))
    results.append(("docs-lint", task_docs_lint()))
    results.append(("version-check", task_version_check()))
    test = commands["test"]
    if not test:
        results.append(("test", None))
    else:
        results.append(("test", task_test() if test == PYTEST_COMMAND else _run_steps(test)))
    claude = shutil.which("claude")
    if claude:
        print("$ claude plugin validate .", flush=True)
        results.append(
            ("plugin validate", subprocess.call([claude, "plugin", "validate", "."], cwd=ROOT))
        )
    else:
        results.append(("plugin validate", None))
    for name, rc in results:
        verdict = (
            "not run (no command or no claude CLI)" if rc is None else "ok" if rc == 0 else "FAIL"
        )
        print(f"verify: {name}: {verdict}")
    return 1 if any(rc for _, rc in results) else 0


# --- the notes index: docs/notes/index.md from the notes' frontmatter -----------------------
# A platform note (docs/notes/<N>.md) carries ``description``, ``tags`` and ``sources`` in its
# frontmatter and this task is the index's only writer (the notes-index work of 2026-10-13, a
# plain PR by the owner's choice). ``read_frontmatter`` and ``is_stale`` come from
# plugin/lessons/index.py unchanged; the layout is this file's own. Standard library only;
# "\n" line endings and UTF-8 on every OS.
NOTES_DIR = ROOT / "docs" / "notes"
NOTES_INDEX = NOTES_DIR / "index.md"
NOTE_FILE_RE = re.compile(r"^(\d+)\.md$")
NOTE_TAGS = (
    "hooks",
    "permissions",
    "sandbox",
    "auth",
    "cli",
    "github-actions",
    "github-api",
    "rulesets",
    "git",
    "windows",
    "plugin-release",
    "gate",
    "detect",
    "evals",
    "sample-runs",
)
NOTE_REQUIRED = ("title", "description", "tags", "sources")
NOTES_INDEX_HEADER = """\
# Notes — platform facts verified against the Claude Code docs and the live runs

A note is one session's batch of facts with one read date: `docs/notes/<N>.md`, number only,
no slug, with `title`, `description`, `tags`, `sources`, `generated.at`, `verified_with` and
`stale_after` in its frontmatter. A note is stale when the environment no longer matches its
`verified_with` (the Claude Code and plugin versions it was read against) or when its
`stale_after` date has passed, whichever comes first; the index marks the second case with
` (stale)`, and `python tasks.py docs-lint` lists every note whose `verified_with` names no
Claude Code version or one other than the pin the jobs install. A note after 49 names one, or
says "no Claude Code fact". A note that replaces an earlier one says so in `supersedes` (the
earlier note's number, or a list of them), and the index marks the earlier note
` (superseded by N)`.

Tags, one section each in this order:
{tags}.
A note appears under every tag it carries; inside a section the notes are in ascending number.

This index is generated by `python tasks.py notes-index` from the notes' frontmatter and is
never edited by hand. A new note carries `description`, `tags` and `sources` and is added by
running the task in the same commit; `tests/test_notes_index.py` fails when the file on disk
differs from what the task would write (the `(stale)` markers aside).
"""
NOTES_INDEX_FOOTER = """\
Sessions are append-only: a later session's file may correct or supersede an earlier one's
reading (each says so inline, e.g. "corrected by §17"); read the latest file on a topic
before relying on an earlier one.
"""


def _lessons_index():
    """``plugin/lessons/index.py``, imported as the tests import it (``plugin`` on the path)."""
    plugin_dir = str(ROOT / "plugin")
    if plugin_dir not in sys.path:
        sys.path.insert(0, plugin_dir)
    from lessons import index as lessons_index

    return lessons_index


def note_problems(fm: dict, tags: tuple[str, ...] = NOTE_TAGS) -> list[str]:
    """Why a note's frontmatter cannot be indexed: a missing field, a tag list that is not a
    list of names or carries a name outside ``tags``, a ``sources`` that is not a non-empty
    list of entries each with a ``resource``."""
    problems = [f"missing {key}" for key in NOTE_REQUIRED if not fm.get(key)]
    note_tags = fm.get("tags")
    if note_tags and (
        not isinstance(note_tags, list) or not all(isinstance(t, str) for t in note_tags)
    ):
        problems.append("tags is not a list of names")
    elif note_tags:
        problems.extend(f"unknown tag {t!r}" for t in note_tags if t not in tags)
    sources = fm.get("sources")
    if sources and not isinstance(sources, list):
        problems.append("sources is not a list")
    elif sources:
        for i, entry in enumerate(sources):
            if not isinstance(entry, dict) or not str(entry.get("resource") or "").strip():
                problems.append(f"sources[{i}] has no resource")
    if "supersedes" in fm and superseded_numbers(fm) is None:
        problems.append("supersedes is not a note number or a list of them")
    return problems


def superseded_numbers(fm: dict) -> list[int] | None:
    """The note numbers a note's ``supersedes`` names ([] when it has none), or None when the
    field is neither a number nor a non-empty list of numbers (a quoted "17" counts as 17)."""
    value = fm.get("supersedes")
    if value is None:
        return []
    values = value if isinstance(value, list) else [value]
    numbers = [
        int(v)
        for v in values
        if (isinstance(v, int) and not isinstance(v, bool)) or (isinstance(v, str) and v.isdigit())
    ]
    return numbers if values and len(numbers) == len(values) else None


def read_notes(notes_dir: Path | None = None) -> tuple[list[tuple[int, dict]], list[str]]:
    """Every ``<N>.md`` in ``notes_dir`` (``NOTES_DIR`` by default) as ``(N, frontmatter)`` in
    ascending number, and one line per note that cannot be indexed (``"<file>: <reason>"``)."""
    lessons_index = _lessons_index()
    notes: list[tuple[int, dict]] = []
    problems: list[str] = []
    for path in sorted((notes_dir or NOTES_DIR).glob("*.md")):
        match = NOTE_FILE_RE.match(path.name)
        if match is None:
            continue
        fm, why = lessons_index.read_frontmatter(path)
        if fm is None:
            problems.append(f"{path.name}: {why}")
            continue
        found = note_problems(fm)
        if found:
            problems.append(f"{path.name}: {'; '.join(found)}")
            continue
        notes.append((int(match.group(1)), fm))
    notes.sort(key=lambda note: note[0])
    numbers = {number for number, _ in notes}
    for number, fm in notes:
        for target in superseded_numbers(fm) or []:
            if target >= number or target not in numbers:
                problems.append(f"{number}.md: supersedes {target}, not an earlier note")
    return notes, problems


def notes_index_text(notes: list[tuple[int, dict]], today: str) -> str:
    """The index: the fixed opening, one section per tag in the list's order (a tag no note
    carries is left out), one line per note under each of its tags, the closing rule."""
    is_stale = _lessons_index().is_stale
    superseded_by: dict[int, list[int]] = {}
    for number, fm in notes:
        for target in superseded_numbers(fm) or []:
            superseded_by.setdefault(target, []).append(number)
    blocks = [NOTES_INDEX_HEADER.format(tags=", ".join(NOTE_TAGS))]
    for tag in NOTE_TAGS:
        lines = []
        for number, fm in notes:
            if tag not in fm["tags"]:
                continue
            line = f"{number}. [{fm['title']}]({number}.md) — {fm['description']}"
            if number in superseded_by:
                line += f" (superseded by {', '.join(map(str, superseded_by[number]))})"
            if is_stale(str(fm.get("stale_after") or ""), today):
                line += " (stale)"
            lines.append(line)
        if lines:
            blocks.append(f"## {tag}\n" + "\n".join(lines) + "\n")
    blocks.append(NOTES_INDEX_FOOTER)
    return "\n".join(blocks)


def build_notes_index(
    notes_dir: Path | None = None, today: str | None = None
) -> tuple[str, list[str]]:
    """(the index text, the problems). ``today`` is a UTC date, the current one by default;
    with problems the text still comes from the notes that could be read."""
    notes, problems = read_notes(notes_dir)
    today = today or datetime.now(timezone.utc).date().isoformat()
    return notes_index_text(notes, today), problems


def task_notes_index() -> int:
    """Rewrite docs/notes/index.md from the notes' frontmatter (1: a note cannot be indexed)."""
    text, problems = build_notes_index(NOTES_DIR)
    for problem in problems:
        print(f"notes-index: {problem}")
    if problems:
        return 1
    NOTES_INDEX.write_text(text, encoding="utf-8", newline="\n")
    shown = NOTES_INDEX.relative_to(ROOT) if NOTES_INDEX.is_relative_to(ROOT) else NOTES_INDEX
    print(f"wrote {shown.as_posix()}")
    return 0


# --- the decisions index: docs/decisions/index.md from each decision's heading -------------
# One line per decision, its title read from the file's own "## <N>. <title>" heading, so an
# amended title reaches the index (ROADMAP R55, choice 236; before it the index was kept by
# hand and decision 30's line kept its first title).
DOCS_DIR = ROOT / "docs"
DECISIONS_DIR = DOCS_DIR / "decisions"
DECISIONS_INDEX = DECISIONS_DIR / "index.md"
DECISION_FILE_RE = re.compile(r"^(\d+)\.md$")
DECISION_HEADING_RE = re.compile(r"^## (\d+)\. (.+)$", re.MULTILINE)
DECISIONS_INDEX_HEADER = """\
# Decisions — accepted and applied in build guide v3

Companion to `BUILD_GUIDE.md`. Step numbers refer to that guide. The accepted alternative is
marked **[ACCEPTED]**.

Decisions 21–26 were added on 2026-09-23 after the plan was audited against the owner's
original objective and the article (session record: PR #22). The mechanism of 21 is the
owner's, the rest are the session's suggestions adopted on the owner's instruction to proceed;
all six were **confirmed on 2026-09-23** by the owner's merge of PR #22.

One file per decision, number only, no slug (`docs/decisions/<N>.md`); each carries `status`,
`reversibility` and `amended_by` in its frontmatter. This index is generated by
`python tasks.py decisions-index` from each file's `## <N>. <title>` heading and is never
edited by hand; `python tasks.py docs-lint` fails when it differs.
"""
DECISIONS_INDEX_FOOTER = """\
Sticky decisions (2, 6, 7, 8, 10, 19) shape files and conventions every later step writes to.
"""


def build_decisions_index(decisions_dir: Path | None = None) -> tuple[str, list[str]]:
    """(the index text, one line per decision file whose heading is missing or names another
    number); with problems the text still lists the decisions that could be read."""
    entries: list[tuple[int, str]] = []
    problems: list[str] = []
    for path in sorted((decisions_dir or DECISIONS_DIR).glob("*.md")):
        match = DECISION_FILE_RE.match(path.name)
        if match is None:
            continue
        number = int(match.group(1))
        heading = DECISION_HEADING_RE.search(path.read_text(encoding="utf-8-sig"))
        if heading is None or int(heading.group(1)) != number:
            problems.append(f"{path.name}: no '## {number}. <title>' heading")
            continue
        entries.append((number, heading.group(2).strip()))
    entries.sort()
    lines = "\n".join(f"{n}. [{title}]({n}.md)" for n, title in entries)
    return f"{DECISIONS_INDEX_HEADER}\n{lines}\n\n{DECISIONS_INDEX_FOOTER}", problems


def task_decisions_index() -> int:
    """Rewrite docs/decisions/index.md from the decisions' headings (1: a heading is wrong)."""
    text, problems = build_decisions_index(DECISIONS_DIR)
    for problem in problems:
        print(f"decisions-index: {problem}")
    if problems:
        return 1
    DECISIONS_INDEX.write_text(text, encoding="utf-8", newline="\n")
    print(f"wrote {DECISIONS_INDEX.relative_to(ROOT).as_posix()}")
    return 0


# --- the docs lint (ROADMAP R55; choices 236 and 237) --------------------------------------
# Deterministic checks only; a contradiction between two notes is a judgment, not a check.
# Failures: a relative link under docs/ that resolves to nothing and is not in the baseline,
# a baseline entry that no longer breaks (the baseline only shrinks), a note after
# LAST_NOTE_WITHOUT_VERSION whose verified_with names no Claude Code version, a note or a
# decision the indexes cannot read, an index that differs from what its task writes.
# Reported only: the notes read on another Claude Code version than the pin, or on none.
# The baseline holds the breaks inside kept records (docs/progress/, docs/handoffs/, notes),
# which choice 126 forbids rewriting; choice 237 keeps them as they are.
LINKS_BASELINE = DOCS_DIR / "links-baseline.txt"
PIN_FILE = ROOT / "plugin" / "init" / "sdlc_init.py"
PIN_RE = re.compile(r'^DEFAULT_CLAUDE_CODE_VERSION = "(\d+\.\d+\.\d+)"', re.MULTILINE)
CLAUDE_CODE_RE = re.compile(r"Claude Code (\d+\.\d+\.\d+)")
NO_CLAUDE_CODE = "no Claude Code fact"
LAST_NOTE_WITHOUT_VERSION = 49
FENCE_RE = re.compile(r"^\s*(```|~~~)")
# a code span may wrap onto the next line, never across a blank one
CODE_SPAN_RE = re.compile(r"(`+)(?:(?!\n[ \t]*\n).)+?\1", re.DOTALL)
LINK_RE = re.compile(r"\]\(\s*<?([^)\s>]+)>?(?:\s+\"[^\"]*\")?\s*\)")
SCHEME_RE = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:")


def link_targets(text: str) -> list[str]:
    """The targets of the inline markdown links in ``text``, outside fenced code blocks and
    code spans."""
    kept: list[str] = []
    in_fence = False
    for line in text.splitlines():
        if FENCE_RE.match(line):
            in_fence = not in_fence
            kept.append("")  # a blank line, so no code span joins across the block
            continue
        kept.append("" if in_fence else line)
    return LINK_RE.findall(CODE_SPAN_RE.sub("", "\n".join(kept)))


def broken_links(docs_dir: Path, root: Path) -> list[tuple[str, str]]:
    """``(file, target)`` for every relative link under ``docs_dir`` (``reference/`` aside:
    the article's text is a source, not a page) that resolves to no file or folder; ``file``
    is relative to ``docs_dir`` in "/" form, a target starting with "/" is read from
    ``root``."""
    found: list[tuple[str, str]] = []
    for path in sorted(docs_dir.rglob("*.md")):
        rel = path.relative_to(docs_dir)
        if rel.parts[0] == "reference":
            continue
        for target in link_targets(path.read_text(encoding="utf-8-sig")):
            if target.startswith("#") or SCHEME_RE.match(target):
                continue
            plain = unquote(target.split("#", 1)[0].split("?", 1)[0])
            base = root / plain.lstrip("/") if plain.startswith("/") else path.parent / plain
            if not base.exists():
                found.append((rel.as_posix(), target))
    return found


def read_links_baseline(path: Path) -> set[tuple[str, str]]:
    """The known breaks: one ``<file><TAB><target>`` per line; blank lines and lines starting
    with "#" are comments."""
    if not path.exists():
        return set()
    entries = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip() and not line.startswith("#"):
            file, _, target = line.partition("\t")
            entries.add((file, target))
    return entries


def read_pin(path: Path | None = None) -> str:
    """The Claude Code version the jobs install (``CLAUDE_CODE_VERSION``), or "" unreadable."""
    match = PIN_RE.search((path or PIN_FILE).read_text(encoding="utf-8"))
    return match.group(1) if match else ""


# --- the docs lint, part 2 (ROADMAP R58, docs/proposals/docs-lint-checks.md) ---------------
# The mechanical classes of the docs consistency review of 2026-10-19
# (docs/reviews/2026-10-19-docs-consistency.md): a frontmatter that is not YAML, a decision
# amended without its amended_by or with the wrong status, a proposal whose status contradicts
# its ROADMAP row, a shipped row left among the candidates, a version paired with another PR
# than its tag's, a citation of a moved stub, a Portuguese word. The version pairs and the
# stubs are read in the living documents only: a kept record (choice 126) keeps a wrong
# sentence beside its correction. Whether a citation means what it says is a reader's
# judgment, not a check.
FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)
AMENDS_RE = re.compile(r"\(amends ([^)]*)\)")
CHOICE_RE = re.compile(r"(?:PROGRESS )?choices? \d+")
DECISION_STATUSES = ("accepted", "amended")
ROADMAP_ROW_RE = re.compile(r"^\| (R\d+) \|")
ROADMAP_FIELD_RE = re.compile(r"\[?\s*(R\d+(?:\s*,\s*R\d+)*)")
SHIPPED_RE = re.compile(r"\bbuilt (?:as plugin|in PR)\b")
# a version tied to its PR by the phrasing ("plugin 1.0.6 in PR #228", "plugin 1.0.2, PR #211",
# "`v1.0.3` = PR #220"), not two events that only share a sentence
VERSION_PR_RES = (
    re.compile(r"\bplugin \**(\d+\.\d+\.\d+)\**(?:,| in(?: the session)?| \(| =) PR #(\d+)"),
    re.compile(r"`v(\d+\.\d+\.\d+)`(?:,| in| \(| =) PR #(\d+)"),
)
MERGE_SUBJECT_RE = re.compile(r"^Merge pull request #(\d+) ")
# check 8: "PR #N merged on/at/as ..." against the PR's merge commit; the claim ends at a
# sentence end, a cell, a bracket or the next PR, and "sample" just before it marks the other
# repository's PR, whose numbers overlap this one's
MERGE_CLAIM_RE = re.compile(
    r"(?P<before>.{0,40}?)(?<![\w#])(?:PR )?#(?P<pr>\d+)[^.;|#\]\n]{0,30}?\bmerged (?:on|at|as)\b"
    r"(?P<claim>(?:[^.;|#\]\n]|\.(?!\s))*)"
)
CLAIM_SHA_RE = re.compile(r"(?:^\s*|\bas |\()`([0-9a-f]{7,40})`")
# a sentence ends at a full stop followed by a space, or at a table cell; "sample" earlier in
# the claim's sentence makes the claim another repository's, maybe (choice 247)
SENTENCE_END_RE = re.compile(r"[.!?]\s|\|")
# the date and the time the claim gives for the merge itself ("merged on <date>", "merged at
# <time> UTC on <date>"), not another event's that shares the clause
CLAIM_DATE_RE = re.compile(r"(?:^\s*|^\s*\d{2}:\d{2}(?::\d{2})? UTC on )(\d{4}-\d{2}-\d{2})\b")
CLAIM_TIME_RE = re.compile(r"^\s*(\d{2}):(\d{2})(?::(\d{2}))? UTC\b")
# a merge commit's time is a second or two from GitHub's merged_at, which the records quote
CLAIM_TIME_SLACK_SECONDS = 90
# the records written before check 8 existed are reported, not failed (choice 126)
MERGE_CLAIMS_SINCE = "2026-10-20"
LAST_NOTE_BEFORE_MERGE_CLAIMS = 53
DATED_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})-")
# a moved stub cited for a fact (by section, or as a source), not named as the file it was
STUB_CITATION_RE = re.compile(
    r"(docs/(?:NOTES|DECISIONS)\.md)`?\s*(?:§|section )\s*\d"
    r"|resource:\s*\"?(docs/(?:NOTES|DECISIONS)\.md)\"?\s*$"
)
# R65, part 6 (S15 of the sources-of-truth study): the code, the template and the workflows
# never point at a moved stub at all; every mention there is a fact's source
CODE_STUB_RE = re.compile(r"(?:docs/)?(?:NOTES|DECISIONS)\.md")
CODE_DIRS = ("plugin", "template", ".github")
CODE_SUFFIXES = (".py", ".md", ".yml", ".yaml", ".json", ".toml", ".txt")
LIVING_DOCS = ("ROADMAP.md", "OPERATING_MODEL.md", "BUILD_GUIDE.md")
LIVING_FOLDERS = ("decisions", "proposals")
# Portuguese words that are not also English words or code names; a proper noun is allowed
WORD_RE = re.compile(r"[^\W\d_]+")
PORTUGUESE_WORDS = frozenset(
    "não você voce também tambem então entao obrigado obrigada fazer está são isso esse "
    "essa aqui agora pelo pela nosso nossa quando onde porque ainda sobre depois antes "
    "projeto decisão mudança revisão tarefa arquivo fluxo melhor preciso deve podemos "
    "vamos feito pronto muito precisa fazendo tudo isto aquilo quais porém enquanto outra "
    "outros outras eles elas meu minha nossos nossas seus suas umas uns".split()
)
PORTUGUESE_ALLOWED = ("São Paulo", "Luís")
# check 9: a running count of the decisions or the notes in a page kept current by hand goes
# stale with the next file (README.md said "The 29 settled decisions" at 36); the indexes hold
# the count, so these pages state none, a correct one included (choice 243)
COUNT_PAGES = ("README.md", "CLAUDE.md", "docs/OPERATING_MODEL.md")
COUNT_CLAIM_RE = re.compile(
    r"\b(?:the |all )?\d+ (?:settled (?:decisions|choices)|decision files|verified (?:notes|facts)"
    r"|platform facts)\b|\ball \d+ (?:decisions|notes)\b",
    re.IGNORECASE,
)
# check 10: a number taken twice fails (ROADMAP R65, part 1; choice 252). A record states its
# choices as the top-level items of a list under a heading that names them ("Choices made
# where the pack left it open", "The owner's choices", "The owner's decision(s)"); its other
# numbered lists ("Live checks", "What was built", a review's findings) count from 1 again,
# so a read of every "N. **" line finds 1 to 8 and 16 to 23 twice. Choices 1 to 15 were
# stated in sessions 1 and 2's PROGRESS.md, which git history alone keeps.
HEADING_RE = re.compile(r"^#{1,6} ")
CHOICE_HEADING_RE = re.compile(
    r"^#{1,6} .*\b(?:choices made|owner['’]s choices|owner['’]s decisions?)\b", re.IGNORECASE
)
CHOICE_ITEM_RE = re.compile(r"^ {0,3}(\d+)\. ")
# the records written before check 10 existed are reported, not failed (choice 126)
NUMBERS_UNIQUE_SINCE = "2026-10-22"
# the records' folder holds two generated pages beside the records
PROGRESS_PAGES = ("index.md", "choices.md")
# check 11: ROADMAP's Order column owns the ranks (R58's rule; ROADMAP R65, part 3). A rank in
# a proposal or a decision stands only inside a dated annotation, the rank at that date; a
# session file names a candidate by its number only (HANDOFF.md) and takes its next free
# numbers from `python tasks.py next-free`. Session files are read from the day after part 3
# was built: every file of 2026-10-22 or before is kept as written (choices 126 and 252).
RANK_RE = re.compile(r"\branks? \d+", re.IGNORECASE)
ANNOTATION_RE = re.compile(r"\*\[\d{4}-\d{2}-\d{2}.*?\]\*")
NEXT_FREE_RE = re.compile(r"\bnext free\b", re.IGNORECASE)
NUMBER_TAKEN_RE = re.compile(r"\b(?:choice|note|decision) \d+|\bR\d+\b|\b\d+\.\d+\.\d+\b")
SESSION_FILES_LINTED_SINCE = "2026-10-23"
# check 12: no retired term as a live one where a reader takes the current state: README.md,
# the manifests, the operating model, ROADMAP and the template. A line that says the term is
# retired, withdrawn, removed or gone, or that carries a dated annotation, passes; the build
# guide is the version-3 plan with its annotations (choice 252, point 6) and is not read. The
# terms are the retired label and keys the plugin still names (``conventions.ACCEPT_RISK_LABEL``,
# ``status.RETIRED_KEYS``) and the words below, which no code keeps.
RETIRED_WORDS = (
    ("profile-based", r"profile-based"),
    ("the Full profile", r"\bfull`? profile\b"),
    ("sdlc:c-approved", r"sdlc:c-approved"),
    ("sdlc:d-approved", r"sdlc:d-approved"),
)
RETIRED_SAID_RE = re.compile(
    r"retired|withdrawn|until 1\.0\.20|removed|\bgone\b|\*\[\d{4}-\d{2}-\d{2}", re.IGNORECASE
)
RETIRED_PAGES = ("README.md", "docs/OPERATING_MODEL.md", "docs/ROADMAP.md")
# check 13: CLAUDE.md's "Verifying your work" quotes `sdlc.yaml: commands` word for word
# (ROADMAP R65, part 4; choice 253): one line per key, "- Build: `<command>` ..."
VERIFY_HEADING = "## Verifying your work"
VERIFY_LINE_RE = re.compile(r"^- (Build|Test|Lint): `([^`]*)`")
RETIRED_FOLDERS = (".claude-plugin", "template")


def _pages(docs_dir: Path, suffixes: tuple[str, ...] = (".md",)) -> list[Path]:
    """Every file under ``docs_dir`` with one of ``suffixes``, ``reference/`` aside, in the
    order of their relative POSIX paths: a Windows path sorts without case, so the order (and
    every report built from it) would otherwise differ between the platforms."""
    return sorted(
        (
            path
            for path in docs_dir.rglob("*")
            if path.suffix in suffixes and path.relative_to(docs_dir).parts[0] != "reference"
        ),
        key=lambda path: path.relative_to(docs_dir).as_posix(),
    )


def _living_docs(docs_dir: Path) -> list[Path]:
    """The pages a session keeps current: ROADMAP, the operating model, the build guide, the
    decisions and the proposals (the records under progress/, handoffs/, notes/ and reviews/
    are annotated, never rewritten)."""
    pages = [docs_dir / name for name in LIVING_DOCS if (docs_dir / name).is_file()]
    for folder in LIVING_FOLDERS:
        pages.extend(sorted((docs_dir / folder).glob("*.md")))
    return pages


def _frontmatter(text: str) -> str:
    """The frontmatter block of ``text`` without its ``---`` lines, or "" when it has none."""
    match = FRONTMATTER_RE.match(text)
    return match.group(1) if match else ""


def frontmatter_problems(docs_dir: Path) -> tuple[list[str], list[str]]:
    """(failures, reports): one failure per page whose frontmatter does not parse as YAML,
    naming the file's line; a report instead when PyYAML (a dev dependency) is absent."""
    try:
        import yaml
    except ImportError:
        return [], ['frontmatter not checked: PyYAML is not installed (pip install -e ".[dev]")']
    failures: list[str] = []
    for path in _pages(docs_dir):
        block = _frontmatter(path.read_text(encoding="utf-8-sig"))
        if not block:
            continue
        try:
            yaml.safe_load(block)
        except yaml.YAMLError as exc:
            mark = getattr(exc, "problem_mark", None)
            line = f":{mark.line + 2}" if mark is not None else ""
            why = getattr(exc, "problem", None) or str(exc).splitlines()[0]
            rel = path.relative_to(docs_dir).as_posix()
            failures.append(f"frontmatter: docs/{rel}{line}: {why}")
    return failures, []


def decision_problems(decisions_dir: Path) -> list[str]:
    """A decision whose heading says ``(amends N)`` missing from decision N's ``amended_by``,
    an ``amended_by`` naming no decision, a ``status`` other than ``amended`` exactly when
    ``amended_by`` is set (change 0001's spec: ``accepted`` or ``amended``)."""
    fields: dict[int, tuple[str, list[int]]] = {}
    amenders: dict[int, list[int]] = {}
    for path in sorted(decisions_dir.glob("*.md")):
        match = DECISION_FILE_RE.match(path.name)
        if match is None:
            continue
        number = int(match.group(1))
        text = path.read_text(encoding="utf-8-sig")
        block = _frontmatter(text)
        status = re.search(r"^status:\s*(\S+)", block, re.MULTILINE)
        amended_by = re.search(r"^amended_by:\s*(.*)$", block, re.MULTILINE)
        numbers = [int(n) for n in re.findall(r"\d+", amended_by.group(1))] if amended_by else []
        fields[number] = (status.group(1) if status else "", numbers)
        heading = DECISION_HEADING_RE.search(text)
        amends = AMENDS_RE.search(heading.group(2)) if heading else None
        if amends:
            for target in re.findall(r"\d+", CHOICE_RE.sub("", amends.group(1))):
                amenders.setdefault(int(target), []).append(number)
    problems: list[str] = []
    for number, (status, amended_by) in sorted(fields.items()):
        for amender in amenders.get(number, []):
            if amender not in amended_by:
                problems.append(
                    f"decisions: {number}.md amended_by lacks {amender} "
                    f"(decision {amender} amends {number})"
                )
        for other in amended_by:
            if other not in fields:
                problems.append(f"decisions: {number}.md amended_by names {other}, no such file")
        expected = DECISION_STATUSES[1] if amended_by else DECISION_STATUSES[0]
        if status != expected:
            problems.append(
                f"decisions: {number}.md status is {status or 'missing'}, expected {expected}"
            )
    return problems


def roadmap_rows(roadmap: Path) -> dict[str, tuple[str, str]]:
    """Each ROADMAP row as ``R<n> -> (its section heading, its Status cell)``; the Status cell
    is read from the row's end (Status, Order, then the closing bar), so a bar inside the
    Candidate column cannot shift it."""
    rows: dict[str, tuple[str, str]] = {}
    section = ""
    for line in roadmap.read_text(encoding="utf-8-sig").splitlines():
        if line.startswith("## "):
            section = line[3:].strip()
            continue
        match = ROADMAP_ROW_RE.match(line)
        if match:
            cells = re.split(r"(?<!\\)\|", line)
            rows[match.group(1)] = (section, cells[-3] if len(cells) >= 8 else "")
    return rows


def proposal_problems(proposals_dir: Path, rows: dict[str, tuple[str, str]]) -> list[str]:
    """A proposal whose ``status`` is ``proposed`` while its ROADMAP row records an acceptance,
    or ``accepted`` while it records none; ROADMAP is the place the status is read (R58's
    rule), the proposal's field a copy. Other status values are not compared."""
    problems: list[str] = []
    for path in sorted(proposals_dir.glob("*.md")):
        block = _frontmatter(path.read_text(encoding="utf-8-sig"))
        status = re.search(r"^status:\s*(.+?)\s*$", block, re.MULTILINE)
        field = re.search(r"^roadmap:\s*(.+)$", block, re.MULTILINE)
        if not status or not field:
            continue
        value = status.group(1).strip("\"'")
        named = ROADMAP_FIELD_RE.match(field.group(1))
        if value not in ("proposed", "accepted") or named is None:
            continue
        for number in re.findall(r"R\d+", named.group(1)):
            if number not in rows:
                problems.append(f"proposals: {path.name} names {number}, not a ROADMAP row")
                continue
            accepted = re.search(r"\baccepted\b", rows[number][1], re.IGNORECASE) is not None
            if accepted != (value == "accepted"):
                said = "records an acceptance" if accepted else "records none"
                problems.append(
                    f"proposals: {path.name} status is {value}, ROADMAP {number} {said}"
                )
    return problems


def shipped_row_problems(rows: dict[str, tuple[str, str]]) -> list[str]:
    """A row whose Status says it was built, still under the candidates' heading; the page's
    own rule moves it under "Done"."""
    return [
        f"ROADMAP: {number} says '{found.group(0)}' but sits under '{section}', not 'Done'"
        for number, (section, status) in rows.items()
        if section.startswith("Candidates") and (found := SHIPPED_RE.search(status))
    ]


def tag_prs(root: Path) -> dict[str, str] | None:
    """``version -> PR number`` for every tag ``v<version>`` on a pull request's merge commit,
    or None when ``root`` has no tags (a shallow or tagless checkout)."""
    try:
        out = subprocess.run(
            ["git", "for-each-ref", "--format=%(refname:short)%09%(*subject)%09%(subject)"]
            + ["refs/tags"],
            cwd=root,
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=True,
        ).stdout
    except (OSError, subprocess.CalledProcessError):
        return None
    pairs: dict[str, str] = {}
    for line in out.splitlines():
        tag, commit_subject, subject = (line.split("\t") + ["", ""])[:3]
        merge = MERGE_SUBJECT_RE.match(commit_subject or subject)
        if tag.startswith("v") and merge:
            pairs[tag[1:]] = merge.group(1)
    return pairs or None


def version_pr_problems(docs_dir: Path, tags: dict[str, str]) -> list[str]:
    """A "plugin X.Y.Z … PR #N" or "`vX.Y.Z` … PR #N" pair in a living document whose PR is not
    the one the tag ``vX.Y.Z`` sits on; a version with no tag is not judged."""
    problems: list[str] = []
    for path in _living_docs(docs_dir):
        rel = path.relative_to(docs_dir).as_posix()
        for number, line in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), 1):
            for pattern in VERSION_PR_RES:
                for version, pr in pattern.findall(line):
                    tagged = tags.get(version)
                    if tagged and tagged != pr:
                        problems.append(
                            f"version: docs/{rel}:{number}: {version} paired with PR #{pr}; "
                            f"v{version} is PR #{tagged}'s merge"
                        )
    return problems


def git_time(text: str) -> datetime:
    """A ``%cI`` time from git. Git 2.55 writes a UTC time with "Z" (2.43 writes "+00:00"),
    and ``datetime.fromisoformat`` reads "Z" only from Python 3.11 on."""
    return datetime.fromisoformat(text[:-1] + "+00:00" if text.endswith("Z") else text)


def pr_merges(root: Path) -> dict[str, tuple[str, datetime]] | None:
    """``PR number -> (merge commit, committer time)`` for every "Merge pull request #N"
    commit reachable from HEAD, the newest first, or None when ``root`` has no such history."""
    try:
        out = subprocess.run(
            ["git", "log", "--format=%H%x09%cI%x09%s"],
            cwd=root,
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=True,
        ).stdout
    except (OSError, subprocess.CalledProcessError):
        return None
    merges: dict[str, tuple[str, datetime]] = {}
    for line in out.splitlines():
        sha, when, subject = (line.split("\t", 2) + ["", ""])[:3]
        merge = MERGE_SUBJECT_RE.match(subject)
        if merge and merge.group(1) not in merges:
            merges[merge.group(1)] = (sha, git_time(when))
    return merges or None


def commit_lookup(root: Path) -> Callable[[str], bool]:
    """Whether a sha names a commit of the repository at ``root`` (``git cat-file -e``),
    remembered per sha."""
    seen: dict[str, bool] = {}

    def known(sha: str) -> bool:
        if sha not in seen:
            try:
                seen[sha] = (
                    subprocess.run(
                        ["git", "cat-file", "-e", f"{sha}^{{commit}}"],
                        cwd=root,
                        capture_output=True,
                    ).returncode
                    == 0
                )
            except OSError:
                seen[sha] = True
        return seen[sha]

    return known


def _merge_claims_fail(docs_dir: Path, path: Path) -> bool:
    """Whether a wrong merge claim in ``path`` fails the lint: a living document, a note after
    ``LAST_NOTE_BEFORE_MERGE_CLAIMS``, or a record dated from ``MERGE_CLAIMS_SINCE`` on; the
    older records are kept as written (choice 126), so their claims are reported."""
    if path in _living_docs(docs_dir):
        return True
    rel = path.relative_to(docs_dir)
    if rel.parts[0] == "notes":
        return path.stem.isdigit() and int(path.stem) > LAST_NOTE_BEFORE_MERGE_CLAIMS
    dated = DATED_RE.match(path.name)
    return bool(dated) and dated.group(1) >= MERGE_CLAIMS_SINCE


def _claim_mismatches(claim: str, sha: str, when: datetime) -> list[str]:
    """What a claim's first sha, date and UTC time say that the merge commit does not."""
    utc = when.astimezone(timezone.utc)
    found: list[str] = []
    said_sha = CLAIM_SHA_RE.search(claim)
    if said_sha and not sha.startswith(said_sha.group(1)):
        found.append(f"merge commit {said_sha.group(1)}, git has {sha[:7]}")
    said_date = CLAIM_DATE_RE.search(claim)
    if said_date and said_date.group(1) not in (utc.date().isoformat(), when.date().isoformat()):
        found.append(f"date {said_date.group(1)}, git has {utc.date().isoformat()} UTC")
    said_time = CLAIM_TIME_RE.search(claim)
    if said_time:
        hours, minutes, seconds = (int(v or 0) for v in said_time.groups())
        said = hours * 3600 + minutes * 60 + seconds
        actual = utc.hour * 3600 + utc.minute * 60 + utc.second
        if abs(said - actual) > CLAIM_TIME_SLACK_SECONDS:
            found.append(f"time {said_time.group(0).strip()}, git has {utc:%H:%M:%S} UTC")
    return found


def merge_claim_problems(
    docs_dir: Path,
    merges: dict[str, tuple[str, datetime]],
    in_repo: Callable[[str], bool] | None = None,
) -> tuple[list[str], list[str]]:
    """(failures, reports): a "PR #N merged on/at/as ..." claim whose sha, date or UTC time is
    not the merge commit's. A PR git does not know (the sample's, an unmerged one) is not
    judged; a claim quoted in a code span (a review citing an error) is not a claim. A claim
    that may be another repository's, its sha not a commit here (``in_repo``) or "sample"
    earlier in its sentence, is reported, never failed: the two repositories' PR numbers
    overlap (choice 247)."""
    failures: list[str] = []
    reports: list[str] = []
    for path in _pages(docs_dir):
        rel = path.relative_to(docs_dir).as_posix()
        strict = _merge_claims_fail(docs_dir, path)
        for number, line in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), 1):
            line = CODE_SPAN_RE.sub(lambda m: "" if "merged" in m.group(0) else m.group(0), line)
            for claim in MERGE_CLAIM_RE.finditer(line):
                known = merges.get(claim.group("pr"))
                if not known or "sample" in claim.group("before").lower():
                    continue
                said_sha = CLAIM_SHA_RE.search(claim.group("claim"))
                prefix = line[: claim.start("pr")]
                ends = list(SENTENCE_END_RE.finditer(prefix))
                sentence = prefix[ends[-1].end() :] if ends else prefix
                foreign = bool(said_sha and in_repo and not in_repo(said_sha.group(1)))
                foreign = foreign or "sample" in sentence.lower()
                for mismatch in _claim_mismatches(claim.group("claim"), *known):
                    text = f"merged: docs/{rel}:{number}: PR #{claim.group('pr')} {mismatch}"
                    if foreign:
                        reports.append(f"{text} (another repository's PR?)")
                    else:
                        (failures if strict else reports).append(text)
    return failures, reports


def stub_problems(docs_dir: Path) -> list[str]:
    """A living document that cites a moved stub (``docs/NOTES.md``, ``docs/DECISIONS.md``)
    for a fact, by section or as a source, instead of ``docs/notes/<N>.md`` (one file per
    former section) or ``docs/decisions/<N>.md``; naming the old file as a file is fine."""
    problems: list[str] = []
    for path in _living_docs(docs_dir):
        rel = path.relative_to(docs_dir).as_posix()
        for number, line in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), 1):
            problems.extend(
                f"stub: docs/{rel}:{number} cites {match.group(1) or match.group(2)}"
                for match in STUB_CITATION_RE.finditer(line)
            )
    return problems


def code_stub_problems(root: Path) -> list[str]:
    """A file under ``plugin/``, ``template/`` or ``.github/`` that names a moved stub
    (``docs/NOTES.md``, ``docs/DECISIONS.md``) instead of ``docs/notes/<N>.md`` or
    ``docs/decisions/<N>.md`` (check 5 widened, R65 part 6)."""
    problems: list[str] = []
    for folder in CODE_DIRS:
        base = root / folder
        if not base.is_dir():
            continue
        for path in sorted(base.rglob("*")):
            if not path.is_file() or path.suffix not in CODE_SUFFIXES:
                continue
            if "__pycache__" in path.parts:
                continue
            rel = path.relative_to(root).as_posix()
            text = path.read_text(encoding="utf-8-sig", errors="replace")
            for number, line in enumerate(text.splitlines(), 1):
                problems.extend(
                    f"stub: {rel}:{number} cites {match.group(0)}"
                    for match in CODE_STUB_RE.finditer(line)
                )
    return problems


def portuguese_problems(docs_dir: Path) -> list[str]:
    """A line of a page or an HTML input under ``docs_dir`` that holds a Portuguese word
    (CLAUDE.md: English only); the proper nouns of ``PORTUGUESE_ALLOWED`` aside."""
    problems: list[str] = []
    for path in _pages(docs_dir, (".md", ".html")):
        rel = path.relative_to(docs_dir).as_posix()
        for number, line in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), 1):
            for allowed in PORTUGUESE_ALLOWED:
                line = line.replace(allowed, "")
            words = sorted({w for w in WORD_RE.findall(line.lower()) if w in PORTUGUESE_WORDS})
            if words:
                problems.append(f"portuguese: docs/{rel}:{number}: {', '.join(words)}")
    return problems


def count_problems(root: Path) -> list[str]:
    """A line of ``COUNT_PAGES`` under ``root`` that states how many decisions or notes there
    are; ``docs/decisions/index.md`` and ``docs/notes/index.md`` are generated and hold it."""
    problems: list[str] = []
    for rel in COUNT_PAGES:
        path = root / rel
        if not path.is_file():
            continue
        for number, line in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), 1):
            problems.extend(
                f'count: {rel}:{number}: "{match.group(0)}"; state no count, the index holds it'
                for match in COUNT_CLAIM_RE.finditer(line)
            )
    return problems


def choice_items(text: str) -> list[tuple[int, int]]:
    """``(choice, line)`` for every choice a record states: an item "N. " at the top level of
    a list under a ``CHOICE_HEADING_RE`` heading, outside fenced code blocks."""
    items: list[tuple[int, int]] = []
    choices = fenced = False
    for number, line in enumerate(text.splitlines(), 1):
        if FENCE_RE.match(line):
            fenced = not fenced
        elif fenced:
            continue
        elif HEADING_RE.match(line):
            choices = bool(CHOICE_HEADING_RE.match(line))
        elif choices and (item := CHOICE_ITEM_RE.match(line)):
            items.append((int(item.group(1)), number))
    return items


def roadmap_items(text: str) -> list[tuple[int, int]]:
    """``(n, line)`` for every ROADMAP row ``| R<n> |``."""
    return [
        (int(match.group(1)[1:]), number)
        for number, line in enumerate(text.splitlines(), 1)
        if (match := ROADMAP_ROW_RE.match(line))
    ]


def numbered_files(folder: Path) -> list[tuple[int, str]]:
    """``(N, file name)`` for every ``<N>.md`` in ``folder``, none when it is missing."""
    if not folder.is_dir():
        return []
    return [
        (int(match.group(1)), path.name)
        for path in sorted(folder.glob("*.md"))
        if (match := NOTE_FILE_RE.match(path.name))
    ]


def _records(docs_dir: Path) -> list[Path]:
    """``docs/PROGRESS.md`` and every record under ``docs/progress/``, by name."""
    records = [docs_dir / "PROGRESS.md"] if (docs_dir / "PROGRESS.md").is_file() else []
    if (docs_dir / "progress").is_dir():
        records.extend(
            sorted(
                (p for p in (docs_dir / "progress").glob("*.md") if p.name not in PROGRESS_PAGES),
                key=lambda p: p.name,
            )
        )
    return records


def number_problems(docs_dir: Path) -> tuple[list[str], list[str]]:
    """(failures, reports) for check 10: a choice two records state, two decision or note
    files with one number, two ROADMAP rows with one number. A choice whose every record is
    older than ``NUMBERS_UNIQUE_SINCE`` is reported, not failed (choice 126); ``PROGRESS.md``
    is the newest record."""
    failures: list[str] = []
    reports: list[str] = []
    places: dict[int, list[tuple[str, bool]]] = {}
    for path in _records(docs_dir):
        rel = path.relative_to(docs_dir).as_posix()
        dated = DATED_RE.match(path.name)
        strict = path.parent == docs_dir or bool(dated and dated.group(1) >= NUMBERS_UNIQUE_SINCE)
        for choice, line in choice_items(path.read_text(encoding="utf-8-sig")):
            places.setdefault(choice, []).append((f"docs/{rel}:{line}", strict))
    for choice, found in sorted(places.items()):
        if len(found) > 1:
            text = f"numbers: choice {choice} taken twice: {', '.join(p for p, _ in found)}"
            (failures if any(strict for _, strict in found) else reports).append(text)
    for kind, folder in (("decision", "decisions"), ("note", "notes")):
        files: dict[int, list[str]] = {}
        for n, name in numbered_files(docs_dir / folder):
            files.setdefault(n, []).append(f"docs/{folder}/{name}")
        failures.extend(
            f"numbers: {kind} {n} taken twice: {', '.join(names)}"
            for n, names in sorted(files.items())
            if len(names) > 1
        )
    roadmap = docs_dir / "ROADMAP.md"
    if roadmap.is_file():
        rows: dict[int, list[str]] = {}
        for n, line in roadmap_items(roadmap.read_text(encoding="utf-8-sig")):
            rows.setdefault(n, []).append(f"docs/ROADMAP.md:{line}")
        failures.extend(
            f"numbers: candidate R{n} taken twice: {', '.join(lines)}"
            for n, lines in sorted(rows.items())
            if len(lines) > 1
        )
    return failures, reports


def rank_problems(docs_dir: Path) -> list[str]:
    """Check 11: a rank outside a dated annotation in ``docs/proposals/`` or ``docs/decisions/``;
    a rank, or a next free number written by hand, in a session file dated from
    ``SESSION_FILES_LINTED_SINCE`` on."""
    problems: list[str] = []
    for folder in ("proposals", "decisions"):
        for path in _pages(docs_dir / folder) if (docs_dir / folder).is_dir() else []:
            rel = path.relative_to(docs_dir).as_posix()
            for number, line in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), 1):
                for match in RANK_RE.finditer(ANNOTATION_RE.sub("", line)):
                    problems.append(
                        f'rank: docs/{rel}:{number}: "{match.group(0)}"; '
                        "ROADMAP's Order column holds it"
                    )
    sessions = docs_dir / "handoffs" / "sessions"
    for path in sorted(sessions.glob("*.md")) if sessions.is_dir() else []:
        dated = DATED_RE.match(path.name)
        if not dated or dated.group(1) < SESSION_FILES_LINTED_SINCE:
            continue
        rel = f"docs/handoffs/sessions/{path.name}"
        for number, line in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), 1):
            problems.extend(
                f'rank: {rel}:{number}: "{match.group(0)}"; name the candidate by its number only'
                for match in RANK_RE.finditer(line)
            )
            if NEXT_FREE_RE.search(line) and NUMBER_TAKEN_RE.search(line):
                problems.append(
                    f"next free: {rel}:{number}: a number written by hand; "
                    "write: python tasks.py next-free"
                )
    return problems


def retired_terms() -> list[tuple[str, re.Pattern[str]]]:
    """``(term, pattern)`` for check 12: the plugin's retired label and keys, then
    ``RETIRED_WORDS``."""
    plugin_dir = str(ROOT / "plugin")
    if plugin_dir not in sys.path:
        sys.path.insert(0, plugin_dir)
    from state import conventions, status

    names = (conventions.ACCEPT_RISK_LABEL, *status.RETIRED_KEYS)
    terms = [(name, re.compile(re.escape(name))) for name in names]
    return terms + [(name, re.compile(word, re.IGNORECASE)) for name, word in RETIRED_WORDS]


def retired_term_problems(root: Path, terms: list[tuple[str, re.Pattern[str]]]) -> list[str]:
    """Check 12: a line of ``RETIRED_PAGES`` or of a file under ``RETIRED_FOLDERS`` that uses a
    retired term and does not say it is retired (``RETIRED_SAID_RE``)."""
    paths = [root / rel for rel in RETIRED_PAGES]
    for folder in RETIRED_FOLDERS:
        if (root / folder).is_dir():
            paths.extend(
                sorted(
                    (p for p in (root / folder).rglob("*") if p.is_file()),
                    key=lambda p: p.relative_to(root).as_posix(),
                )
            )
    problems: list[str] = []
    for path in paths:
        if not path.is_file() or "__pycache__" in path.parts:
            continue
        rel = path.relative_to(root).as_posix()
        text = path.read_text(encoding="utf-8-sig", errors="replace")
        for number, line in enumerate(text.splitlines(), 1):
            if RETIRED_SAID_RE.search(line):
                continue
            problems.extend(
                f'retired: {rel}:{number}: "{term}" as a live term; say it is retired, or drop it'
                for term, pattern in terms
                if pattern.search(line)
            )
    return problems


def verify_line_problems(root: Path) -> list[str]:
    """Check 13: a line of CLAUDE.md's "Verifying your work" that is missing or differs from
    ``sdlc.yaml: commands``; nothing when either file is absent."""
    claude, sdlc = root / "CLAUDE.md", root / "sdlc.yaml"
    if not claude.is_file() or not sdlc.is_file():
        return []
    commands = read_commands(sdlc)
    quoted: dict[str, tuple[int, str]] = {}
    inside = False
    for number, line in enumerate(claude.read_text(encoding="utf-8-sig").splitlines(), 1):
        if line.startswith("## "):
            inside = line.strip() == VERIFY_HEADING
        elif inside and (match := VERIFY_LINE_RE.match(line)):
            quoted[match.group(1).lower()] = (number, match.group(2))
    problems: list[str] = []
    for key in COMMAND_KEYS:
        if key not in quoted:
            problems.append(
                f'commands: CLAUDE.md has no "- {key.title()}:" line under "{VERIFY_HEADING}"'
            )
        elif quoted[key][1] != commands[key]:
            number, text = quoted[key]
            problems.append(
                f"commands: CLAUDE.md:{number}: `{text}` differs from sdlc.yaml commands.{key} "
                f"`{commands[key]}`"
            )
    return problems


# --- the choices index: docs/progress/choices.md from the records (ROADMAP R65, part 2) -----
# Where choice N is stated, so that "choice N" opens without a grep (choice 252, point 3). A
# choice is what check 10 reads; its summary is the item's first bold phrase, which the records
# use as the choice's first sentence, or its first sentence where it has none. The index is
# rewritten by its task only, and docs-lint fails a stale one, as for the decisions and notes.
CHOICES_INDEX = DOCS_DIR / "progress" / "choices.md"
CHOICES_INDEX_HEADER = """\
# Choices — where each numbered choice is stated

Every choice the records number: the number, the record and line that state it, and the
item's first sentence (its bold lead). The records are the files of this folder, one per session
since choice 259; a choice is a top-level item under a heading that states choices, as
`python tasks.py docs-lint` check 10 reads them (ROADMAP R65). Choices 1 to 15 are in sessions
1 and 2's `docs/PROGRESS.md`, which git history alone keeps (`fe20f6a`, `57db1b3`).

This index is generated by `python tasks.py choices-index` and is never edited by hand;
`python tasks.py docs-lint` fails when it differs, so a PR that edits a record runs the task.

| Choice | Record | First sentence |
|---|---|---|
"""
BOLD_RE = re.compile(r"\*\*(.+?)\*\*")
MARKDOWN_LINK_RE = re.compile(r"\[([^\]]*)\]\([^)]*\)")
FIRST_SENTENCE_RE = re.compile(r"^(.+?[.!?])(?:\s|$)")


def choice_summary(item: str) -> str:
    """The first bold phrase of a choice item's text, else its first sentence, with links
    reduced to their text and bars escaped for a table cell."""
    item = MARKDOWN_LINK_RE.sub(r"\1", item)
    bold = BOLD_RE.search(item)
    sentence = FIRST_SENTENCE_RE.match(item)
    text = bold.group(1) if bold else sentence.group(1) if sentence else item
    return text.strip().replace("|", "\\|")


def build_choices_index(docs_dir: Path | None = None) -> str:
    """The index text: one row per choice item in the records, by number, then record."""
    docs_dir = docs_dir or DOCS_DIR
    rows: list[tuple[int, int, str]] = []
    for order, path in enumerate(_records(docs_dir)):
        name = path.name if path.parent.name == "progress" else f"../{path.name}"
        lines = path.read_text(encoding="utf-8-sig").splitlines()
        for choice, line in choice_items("\n".join(lines)):
            item = CHOICE_ITEM_RE.sub("", lines[line - 1], count=1)
            link = f"[{path.name}:{line}]({name})"
            rows.append((choice, order, f"| {choice} | {link} | {choice_summary(item)} |"))
    return CHOICES_INDEX_HEADER + "".join(f"{row}\n" for *_, row in sorted(rows))


def task_choices_index() -> int:
    """Rewrite docs/progress/choices.md from the choices the records state."""
    CHOICES_INDEX.write_text(build_choices_index(DOCS_DIR), encoding="utf-8", newline="\n")
    print(f"wrote {CHOICES_INDEX.relative_to(ROOT).as_posix()}")
    return 0


def lint_docs(
    docs_dir: Path | None = None,
    root: Path | None = None,
    baseline: Path | None = None,
    pin: str | None = None,
) -> tuple[list[str], list[str]]:
    """(failures, reports) for the docs under ``docs_dir`` (``DOCS_DIR`` by default)."""
    docs_dir = docs_dir or DOCS_DIR
    root = root or docs_dir.parent
    pin = read_pin() if pin is None else pin
    failures: list[str] = []
    reports: list[str] = []

    # R58's check 7 first: checks 1 and 2 read frontmatter
    found, said = frontmatter_problems(docs_dir)
    failures.extend(found)
    reports.extend(said)

    known = read_links_baseline(baseline or docs_dir / LINKS_BASELINE.name)
    broken = set(broken_links(docs_dir, root))
    for file, target in sorted(broken - known):
        failures.append(f"broken link: docs/{file} -> {target}")
    for file, target in sorted(known - broken):
        failures.append(f"baseline entry no longer breaks, remove it: {file}\t{target}")
    reports.append(f"{len(known & broken)} known broken links (docs/links-baseline.txt)")

    notes_dir = docs_dir / "notes"
    if notes_dir.is_dir():
        notes, problems = read_notes(notes_dir)
        failures.extend(f"notes: {p}" for p in problems)
        for number, fm in notes:
            verified_with = str(fm.get("verified_with") or "")
            versions = CLAUDE_CODE_RE.findall(verified_with)
            if NO_CLAUDE_CODE in verified_with:
                continue
            if not versions and number > LAST_NOTE_WITHOUT_VERSION:
                failures.append(
                    f"notes: {number}.md names no Claude Code version in verified_with "
                    f'(add one, or "{NO_CLAUDE_CODE}")'
                )
            elif not versions:
                reports.append(f"note {number}: no Claude Code version recorded")
            elif pin not in versions:
                reports.append(
                    f"note {number}: read on Claude Code {', '.join(versions)}, pin {pin}"
                )
        if (notes_dir / "index.md").exists():
            text, _ = build_notes_index(notes_dir)
            on_disk = (notes_dir / "index.md").read_text(encoding="utf-8")
            stale = re.compile(r" \(stale\)$", re.MULTILINE)
            if stale.sub("", text) != stale.sub("", on_disk):
                failures.append("docs/notes/index.md differs: run python tasks.py notes-index")

    decisions_dir = docs_dir / "decisions"
    if decisions_dir.is_dir():
        text, problems = build_decisions_index(decisions_dir)
        failures.extend(f"decisions: {p}" for p in problems)
        index = decisions_dir / "index.md"
        if not index.exists() or index.read_text(encoding="utf-8") != text:
            failures.append("docs/decisions/index.md differs: run python tasks.py decisions-index")
        failures.extend(decision_problems(decisions_dir))

    roadmap = docs_dir / "ROADMAP.md"
    if roadmap.is_file():
        rows = roadmap_rows(roadmap)
        failures.extend(shipped_row_problems(rows))
        if (docs_dir / "proposals").is_dir():
            failures.extend(proposal_problems(docs_dir / "proposals", rows))

    tags = tag_prs(root)
    if tags is None:
        reports.append("version and PR pairs not checked: no tags in this checkout")
    else:
        failures.extend(version_pr_problems(docs_dir, tags))
    merges = pr_merges(root)
    if merges is None:
        reports.append("merge claims not checked: no merge history in this checkout")
    else:
        found, said = merge_claim_problems(docs_dir, merges, commit_lookup(root))
        failures.extend(found)
        reports.extend(said)
    failures.extend(stub_problems(docs_dir))
    failures.extend(code_stub_problems(root))
    failures.extend(portuguese_problems(docs_dir))
    failures.extend(count_problems(root))
    found, said = number_problems(docs_dir)
    failures.extend(found)
    reports.extend(said)
    failures.extend(rank_problems(docs_dir))
    failures.extend(retired_term_problems(root, retired_terms()))
    failures.extend(verify_line_problems(root))
    choices = docs_dir / "progress" / "choices.md"
    if (docs_dir / "PROGRESS.md").is_file() or choices.exists():
        if not choices.exists() or choices.read_text(encoding="utf-8") != build_choices_index(
            docs_dir
        ):
            failures.append("docs/progress/choices.md differs: run python tasks.py choices-index")
    return failures, reports


def task_docs_lint() -> int:
    """Check the docs' links, notes, indexes, cross-file facts and numbers (1: a failure)."""
    failures, reports = lint_docs()
    for line in reports:
        print(f"docs-lint: {line}")
    for line in failures:
        print(f"docs-lint: FAIL {line}")
    print(f"docs-lint: {len(failures)} failure(s)")
    return 1 if failures else 0


# --- the next free numbers (ROADMAP R65, part 1; choices 184 and 252) -----------------------
# Read from git, never from a session file: ``main`` (``origin/main`` once fetched) and every
# local or fetched branch ahead of it, each at its own commit. A number a branch holds above
# the highest on ``main`` is taken above ``main``, named with its branch; the next free number
# is one above the highest taken anywhere. Nothing is reserved (choice 184): two branches may
# take one number, and check 10 fails the second when both reach ``main``.
NEXT_FREE_KINDS = ("choice", "candidate", "note", "decision", "patch")
BASE_REFS = ("refs/remotes/origin/main", "refs/heads/main")
PLUGIN_MANIFEST = ".claude-plugin/plugin.json"
VERSION_RE = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")


def _git(root: Path, *args: str, stdin: bytes | None = None) -> bytes:
    """A git command's output as bytes (``CalledProcessError`` when it fails)."""
    return subprocess.run(
        ["git", *args], cwd=root, input=stdin, capture_output=True, check=True
    ).stdout


def _read_blobs(root: Path, commit: str, paths: list[str]) -> dict[str, str]:
    """``path -> text`` for ``paths`` at ``commit``, in one ``git cat-file --batch``."""
    if not paths:
        return {}
    out = _git(
        root, "cat-file", "--batch", stdin="".join(f"{commit}:{p}\n" for p in paths).encode()
    )
    texts: dict[str, str] = {}
    at = 0
    for path in paths:
        end = out.index(b"\n", at)
        header = out[at:end].split()
        at = end + 1
        if len(header) == 3 and header[1] == b"blob":
            size = int(header[2])
            texts[path] = out[at : at + size].decode("utf-8-sig", errors="replace")
            at += size + 1
    return texts


def _is_record(path: str) -> bool:
    return path == "docs/PROGRESS.md" or (
        path.startswith("docs/progress/")
        and path.count("/") == 2
        and path.endswith(".md")
        and path.rpartition("/")[2] not in PROGRESS_PAGES
    )


def numbers_taken(paths: list[str], texts: dict[str, str]) -> dict[str, set[tuple[int, ...]]]:
    """Every number a tree takes, by kind, each as a tuple so that a version compares as a
    number does: the notes and the decisions from the tree's ``paths``; the choices, the
    ROADMAP rows and the plugin version from ``texts`` (``path -> text``)."""
    taken: dict[str, set[tuple[int, ...]]] = {kind: set() for kind in NEXT_FREE_KINDS}
    for path in paths:
        folder, _, name = path.rpartition("/")
        match = NOTE_FILE_RE.match(name)
        if match and folder in ("docs/notes", "docs/decisions"):
            taken["note" if folder == "docs/notes" else "decision"].add((int(match.group(1)),))
    for path, text in texts.items():
        if path == "docs/ROADMAP.md":
            taken["candidate"].update((n,) for n, _ in roadmap_items(text))
        elif path == PLUGIN_MANIFEST:
            try:
                version = VERSION_RE.match(str(json.loads(text).get("version", "")))
            except (ValueError, AttributeError):
                version = None
            if version:
                taken["patch"].add(tuple(int(v) for v in version.groups()))
        elif _is_record(path):
            taken["choice"].update((n,) for n, _ in choice_items(text))
    return taken


def read_numbers(root: Path, commit: str) -> dict[str, set[tuple[int, ...]]]:
    """The numbers taken at ``commit`` of the repository at ``root``."""
    listed = _git(
        root, "ls-tree", "-r", "-z", "--name-only", commit, "--", "docs", ".claude-plugin"
    )
    paths = [p for p in listed.decode("utf-8").split("\0") if p]
    wanted = [p for p in paths if p in ("docs/ROADMAP.md", PLUGIN_MANIFEST) or _is_record(p)]
    return numbers_taken(paths, _read_blobs(root, commit, wanted))


def main_commit(root: Path) -> tuple[str, str]:
    """(the base ref, its commit): ``origin/main``, else ``main``. ``LookupError`` when neither
    exists."""
    for ref in BASE_REFS:
        try:
            base = _git(root, "rev-parse", "--verify", "-q", f"{ref}^{{commit}}").decode().strip()
        except subprocess.CalledProcessError:
            continue
        return ref, base
    raise LookupError("no main branch: neither origin/main nor main exists")


def branches_ahead(root: Path) -> tuple[str, str, dict[str, list[str]]]:
    """(the base ref, its commit, ``commit -> branch names``) for every local or fetched
    branch, and a detached ``HEAD``, that holds a commit the base lacks; a fetched branch is
    named without its remote. ``LookupError`` when neither ``origin/main`` nor ``main`` exists."""
    ref, base = main_commit(root)
    listed = _git(root, "for-each-ref", "--format=%(refname)%09%(objectname)", "refs/heads")
    listed += _git(root, "for-each-ref", "--format=%(refname)%09%(objectname)", "refs/remotes")
    heads: dict[str, list[str]] = {}
    for line in listed.decode("utf-8").splitlines():
        name, commit = line.split("\t")
        if name == ref or name.endswith("/HEAD"):
            continue
        short = name.split("/", 3)[3] if name.startswith("refs/remotes/") else name[11:]
        if short not in heads.setdefault(commit, []):
            heads[commit].append(short)
    try:
        head = _git(root, "rev-parse", "-q", "--verify", "HEAD^{commit}").decode().strip()
        heads.setdefault(head, ["HEAD"])
    except subprocess.CalledProcessError:
        pass
    ahead = {
        commit: names
        for commit, names in heads.items()
        if int(_git(root, "rev-list", "--count", f"{base}..{commit}").decode()) > 0
    }
    return ref.split("/", 2)[2], base, ahead


def _show(kind: str, number: tuple[int, ...]) -> str:
    text = ".".join(str(n) for n in number)
    return f"R{text}" if kind == "candidate" else text


def next_free(root: Path) -> tuple[str, dict[str, str], list[tuple[str, str, list[str]]], int]:
    """(the base read, as "<ref> at <sha>"; the next free number of each kind; each number
    taken above the base with the branches that hold it, by kind and number; how many
    branches ahead were read)."""
    base_ref, base, ahead = branches_ahead(root)
    on_main = read_numbers(root, base)
    taken = {kind: set(numbers) for kind, numbers in on_main.items()}
    holders: dict[tuple[str, tuple[int, ...]], list[str]] = {}
    for commit, names in sorted(ahead.items(), key=lambda item: item[1]):
        for kind, numbers in read_numbers(root, commit).items():
            taken[kind] |= numbers
            # above main's highest: main holds one version, its own, and no choice under 16
            floor = max(on_main[kind], default=())
            for number in numbers:
                if number > floor:
                    holders.setdefault((kind, number), []).extend(names)
    free: dict[str, str] = {}
    for kind in NEXT_FREE_KINDS:
        if not taken[kind]:
            free[kind] = "none read" if kind == "patch" else _show(kind, (1,))
            continue
        highest = max(taken[kind])
        free[kind] = _show(kind, (*highest[:-1], highest[-1] + 1))
    above = [
        (kind, _show(kind, number), sorted(set(holders[(kind, number)])))
        for kind in NEXT_FREE_KINDS
        for number in sorted(n for k, n in holders if k == kind)
    ]
    return f"{base_ref} at {base[:7]}", free, above, len(ahead)


def task_next_free() -> int:
    """Print the next free choice, candidate, note, decision and patch (main and branches ahead)."""
    try:
        base, free, above, read = next_free(ROOT)
    except (LookupError, OSError, subprocess.CalledProcessError) as error:
        print(f"next-free: cannot read git: {error}", file=sys.stderr)
        return 1
    print(f"next-free: read on {base} and {read} branch(es) ahead of it, as last fetched")
    for kind in NEXT_FREE_KINDS:
        print(f"  {kind:10} {free[kind]}")
    print("next-free: taken above main:" + ("" if above else " none"))
    for kind, number, names in above:
        print(f"  {kind} {number}: {', '.join(names)}")
    print("next-free: nothing is reserved (choice 184); git fetch origin reads the newest state")
    return 0


# --- the version check (ROADMAP R5's race; choice 257) -------------------------------------
# Two pull requests that bump plugin.json to one version merge clean, and sdlc-tag.yml tags the
# first only: the second's change ships under a tag that does not hold it. A branch bumps when
# one of its own commits (ahead of main) holds a version none of its parents holds, so a merge
# of main into the branch brings main's version without bumping. A branch that bumps must hold
# a version above main's whose tag does not exist yet; one that bumps nothing passes, since a
# change may ship with the next release (PR #88). On main itself nothing is ahead, so nothing
# is checked.


def _version_at(root: Path, commit: str) -> tuple[int, ...] | None:
    """The plugin version at ``commit``, or None when it has no readable one."""
    try:
        text = _read_blobs(root, commit, [PLUGIN_MANIFEST]).get(PLUGIN_MANIFEST, "")
        match = VERSION_RE.match(str(json.loads(text).get("version", "")))
    except (subprocess.CalledProcessError, ValueError, AttributeError):
        return None
    return tuple(int(v) for v in match.groups()) if match else None


def version_bumped(root: Path, base: str, head: str = "HEAD") -> bool:
    """Whether a commit in ``base..head`` holds a plugin version none of its parents holds."""
    lines = _git(root, "rev-list", "--parents", f"{base}..{head}").decode().splitlines()
    for commit, *parents in (line.split() for line in lines):
        if _version_at(root, commit) not in {_version_at(root, parent) for parent in parents}:
            return True
    return False


def tag_exists(root: Path, version: str) -> bool | None:
    """Whether ``v<version>`` is tagged, locally or on ``origin``; None when neither answers."""
    try:
        _git(root, "rev-parse", "-q", "--verify", f"refs/tags/v{version}")
        return True
    except subprocess.CalledProcessError:
        pass
    try:
        return bool(_git(root, "ls-remote", "--tags", "origin", f"refs/tags/v{version}").strip())
    except (OSError, subprocess.CalledProcessError):
        return None


def version_problems(root: Path) -> tuple[list[str], list[str]]:
    """(failures, reports) for the branch at ``HEAD`` against ``main``."""
    try:
        ref, base = main_commit(root)
    except LookupError as error:
        return [], [f"not checked: {error}"]
    if not version_bumped(root, base):
        return [], []
    head, on_main = _version_at(root, "HEAD"), _version_at(root, base)
    if head is None:
        return [f"{PLUGIN_MANIFEST} holds no readable version at HEAD"], []
    shown = _show("patch", head)
    hint = "take the next free patch (python tasks.py next-free)"
    if on_main is not None and head <= on_main:
        main_shown = _show("patch", on_main)
        name = ref.split("/", 2)[2]
        return [f"the branch bumps to {shown}, not above {name}'s {main_shown}: {hint}"], []
    tagged = tag_exists(root, shown)
    if tagged:
        return [f"the branch bumps to {shown}, and v{shown} is already tagged: {hint}"], []
    if tagged is None:
        return [], [f"v{shown}'s tag not checked: no tag here and origin did not answer"]
    return [], []


def task_version_check() -> int:
    """Fail a branch that bumps plugin.json to a version main holds or a tag already has."""
    try:
        failures, reports = version_problems(ROOT)
    except (OSError, subprocess.CalledProcessError) as error:
        failures, reports = [], [f"not checked: cannot read git: {error}"]
    for line in reports:
        print(f"version-check: {line}")
    for line in failures:
        print(f"version-check: FAIL {line}")
    return 1 if failures else 0


TASKS = {
    "test": task_test,
    "lint": task_lint,
    "format": task_format,
    "check": task_check,
    "verify": task_verify,
    "notes-index": task_notes_index,
    "decisions-index": task_decisions_index,
    "choices-index": task_choices_index,
    "docs-lint": task_docs_lint,
    "next-free": task_next_free,
    "version-check": task_version_check,
}


def main(argv: list[str]) -> int:
    if len(argv) != 1 or argv[0] in {"help", "-h", "--help"}:
        print(__doc__)
        for name, fn in TASKS.items():
            print(f"  {name:8} {fn.__doc__}")
        return 0 if argv and argv[0] in {"help", "-h", "--help"} else 2
    task = TASKS.get(argv[0])
    if task is None:
        print(f"unknown task: {argv[0]}", file=sys.stderr)
        return 2
    return task()


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
