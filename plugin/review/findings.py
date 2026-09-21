"""The review findings file: signatures, validation, the tally, the framework rules and the
record of what has been seen before (build guide step 26; article p.33-35).

The reviewer writes ``changes/<id>-<slug>/evidence/review-findings.json`` in the shape
``plugin/gate/checks.py: load_findings`` reads (PROGRESS choice 7)::

    {"schema_version": 1, "head": "<sha>", "at": "<ISO-8601 UTC>",
     "findings": [{"pass": "bugs|security|compliance", "severity": "important|nit",
                   "file": "...", "line": N, "summary": "...", "rule": "...",
                   "signature": "<16 hex>"}],
     "tally": {"important": N, "nit": M, "nits_omitted": K}}

Nothing here judges a diff. It checks the file the reviewer wrote, adds the findings a rule
can decide on its own (article p.35 / REVIEW.md: no pre-existing test may be edited in a
fix-type change), computes the machine-readable tally the gate and the check run read
(article p.33 step 3) and answers the second-occurrence question of article p.34 step 5:
"when a review flags a mistake for the second time, the correction goes into CLAUDE.md".
"""

from __future__ import annotations

import hashlib
import re
import sys
from collections.abc import Callable, Iterable
from pathlib import Path
from typing import Any

PLUGIN_DIR = Path(__file__).resolve().parent.parent
if str(PLUGIN_DIR) not in sys.path:
    sys.path.insert(0, str(PLUGIN_DIR))

from hooks._common import ConfigError, load_sdlc_config, matches  # noqa: E402
from state import conventions as c  # noqa: E402

SCHEMA_VERSION = 1
SEVERITIES = ("important", "nit")
PASSES = ("bugs", "security", "compliance")
REQUIRED_FIELDS = ("pass", "severity", "file", "summary")

SEEN_FILE = ".review-seen.json"  # changes/.review-seen.json: the project's record of findings
PROPOSALS_FILE = "claude-md-proposals.md"  # evidence/: the lines the PR description quotes
CHECK_RUN_NAME = "sdlc/review"

SUMMARY_MAX = 80  # characters of the normalised summary that go into a signature
SIGNATURE_LEN = 16  # hex characters of the sha1 kept

# The fallback when sdlc.yaml carries no ``test_paths`` (the defaults /sdlc-init writes for an
# unknown language plus the two conventional JS spellings; build guide step 25).
DEFAULT_TEST_PATHS = [
    "tests/**",
    "test/**",
    "**/test_*.py",
    "**/*_test.py",
    "**/*.test.js",
    "**/*.spec.js",
]
TEST_EDIT_SUMMARY = (
    "pre-existing test file modified in a fix-type change "
    "(REVIEW.md framework rule; build guide step 25)"
)
TEST_EDIT_RULE = "REVIEW.md: no test edits in a fix task"

_PUNCT_RE = re.compile(r"[^0-9a-z\s]+")
_DIGIT_RE = re.compile(r"\d+")
_SPACE_RE = re.compile(r"\s+")


# --- signatures ----------------------------------------------------------------------------
def normalise_summary(summary: str) -> str:
    """The comparison form of a finding's sentence: lower-cased, punctuation replaced by a
    space, every run of digits replaced by ``#``, whitespace collapsed, cut to 80 characters."""
    text = _PUNCT_RE.sub(" ", str(summary).lower())
    text = _DIGIT_RE.sub("#", text)
    return _SPACE_RE.sub(" ", text).strip()[:SUMMARY_MAX]


def strip_dot_slash(path: str) -> str:
    """Drop every leading ``./`` — and nothing else. ``lstrip("./")`` would eat the dot of
    ``.github/workflows/ci.yml`` and turn it into ``github/workflows/ci.yml``."""
    while path.startswith("./"):
        path = path.removeprefix("./")
    return path


def normalise_file(path: str) -> str:
    return strip_dot_slash(str(path).strip().replace("\\", "/")).lower()


def signature(finding: dict[str, Any]) -> str:
    """A stable id for "the same finding", so a second occurrence is computable (article p.34
    step 5).

    It is the first 16 hex characters of the sha1 of ``pass|file|summary``, where the file is
    lower-cased with forward slashes and the summary goes through ``normalise_summary``. The
    line number is deliberately not part of it: the same mistake moves up and down a file
    between reviews, and a signature that changed with it would never match twice. Two
    findings of the same pass, in the same file, saying the same thing in the same words are
    the same finding; the same sentence about another file is not.
    """
    key = "|".join(
        (
            str(finding.get("pass", "")).strip().lower(),
            normalise_file(finding.get("file", "")),
            normalise_summary(finding.get("summary", "")),
        )
    )
    return hashlib.sha1(key.encode("utf-8")).hexdigest()[:SIGNATURE_LEN]  # noqa: S324


# --- validation ----------------------------------------------------------------------------
def validate(data: dict[str, Any], head: str | None) -> list[str]:
    """Everything wrong with the file the reviewer wrote, in the order it was found; an empty
    list means the gate can read it. ``head`` is the commit reviewed (``git rev-parse HEAD``);
    the recorded head must be a prefix of it, exactly as ``gate/checks.py`` compares them, so
    an abbreviated sha is accepted and a stale review is not."""
    problems: list[str] = []
    if not isinstance(data, dict):
        return ["the findings file is not a JSON object"]
    if data.get("schema_version") != SCHEMA_VERSION:
        problems.append(
            f"schema_version must be {SCHEMA_VERSION}, got {data.get('schema_version')!r}"
        )
    recorded = data.get("head")
    if not recorded or not isinstance(recorded, str):
        problems.append("no 'head' commit recorded: the review must say which commit it read")
    elif head and not str(head).startswith(recorded):
        problems.append(
            f"findings are for commit {recorded[:10]}, HEAD is {str(head)[:10]}: re-run the review"
        )
    items = data.get("findings")
    if not isinstance(items, list):
        problems.append("'findings' must be a list")
        return problems
    for i, finding in enumerate(items):
        if not isinstance(finding, dict):
            problems.append(f"findings[{i}] is not an object")
            continue
        for field in REQUIRED_FIELDS:
            value = finding.get(field)
            if not isinstance(value, str) or not value.strip():
                problems.append(f"findings[{i}] has no '{field}'")
        severity = str(finding.get("severity", "")).strip().lower()
        if severity and severity not in SEVERITIES:
            problems.append(f"findings[{i}].severity must be one of {SEVERITIES}, got {severity!r}")
        pass_name = str(finding.get("pass", "")).strip().lower()
        if pass_name and pass_name not in PASSES:
            problems.append(f"findings[{i}].pass must be one of {PASSES}, got {pass_name!r}")
    return problems


# --- normalisation -------------------------------------------------------------------------
def _line_of(finding: dict[str, Any]) -> int:
    line = finding.get("line")
    if isinstance(line, bool) or not isinstance(line, int):
        return 0
    return max(line, 0)


def _severity(finding: dict[str, Any]) -> str:
    return str(finding.get("severity", "")).strip().lower()


def _sort_key(finding: dict[str, Any]) -> tuple:
    return (
        0 if _severity(finding) == "important" else 1,
        normalise_file(finding.get("file", "")),
        _line_of(finding),
        str(finding.get("summary", "")),
    )


def normalise(data: dict[str, Any]) -> dict[str, Any]:
    """A copy of the findings file with every signature filled, the tally recomputed from the
    findings themselves and the findings sorted Important first, then by file and line. The
    reviewer's ``nits_omitted`` is kept (only it knows how many nits it left out, article p.34
    "at most five nits"); the two counted numbers are never taken on trust."""
    out = dict(data)
    items = [dict(f) for f in data.get("findings", []) if isinstance(f, dict)]
    for finding in items:
        finding["signature"] = signature(finding)
    items.sort(key=_sort_key)
    omitted = (
        (data.get("tally") or {}).get("nits_omitted")
        if isinstance(data.get("tally"), dict)
        else None
    )
    if isinstance(omitted, bool) or not isinstance(omitted, int) or omitted < 0:
        omitted = 0
    out["schema_version"] = SCHEMA_VERSION
    out["findings"] = items
    out["tally"] = {
        "important": sum(1 for f in items if _severity(f) == "important"),
        "nit": sum(1 for f in items if _severity(f) == "nit"),
        "nits_omitted": omitted,
    }
    return out


def important(data: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        f for f in data.get("findings", []) if isinstance(f, dict) and _severity(f) == "important"
    ]


# --- the framework rules a script can decide (build guide step 25; REVIEW.md) ----------------
def test_path_globs(root: Path) -> list[str]:
    """``sdlc.yaml: test_paths``, or the defaults when the project has not set them."""
    try:
        config = load_sdlc_config(str(root))
    except ConfigError:
        config = {}
    globs = config.get("test_paths")
    if not isinstance(globs, list):
        return list(DEFAULT_TEST_PATHS)
    kept = [str(g).strip() for g in globs if str(g).strip()]
    return kept or list(DEFAULT_TEST_PATHS)


def framework_findings(
    root: Path,
    change_dir: Path,
    status: Any,
    diff_files: Iterable[str],
    base_files_exist: Callable[[str], bool],
) -> list[dict[str, Any]]:
    """The deterministic backing of the REVIEW.md rule "in a fix-type change the diff must not
    modify test files that existed before the fix" (build guide step 25; article p.35: hooks
    "stop the agent editing test files during a fix task" — this is the review-side check of
    the same rule, for the paths a hook cannot see, e.g. an edit made in CI or before the lock).

    A file is flagged when the change is a fix, the path matches ``sdlc.yaml: test_paths`` and
    the file existed on the base branch (``base_files_exist`` answers that; the caller passes
    ``lambda p: diff.file_at(root, base, p) is not None``). A new test file is fine — the
    reproducing test is the proof of the fix. The change folder itself is never flagged.
    """
    if getattr(status, "change_type", "") != "fix":
        return []
    globs = test_path_globs(Path(root))
    try:
        change_rel = Path(change_dir).resolve().relative_to(Path(root).resolve()).as_posix()
    except ValueError:
        change_rel = ""
    out: list[dict[str, Any]] = []
    for raw in sorted({str(f).replace("\\", "/") for f in diff_files}):
        rel = strip_dot_slash(raw)
        if change_rel and (rel == change_rel or rel.startswith(change_rel + "/")):
            continue
        if not any(matches(g, rel) for g in globs):
            continue
        if not base_files_exist(rel):
            continue
        out.append(
            {
                "pass": "compliance",
                "severity": "important",
                "file": rel,
                "line": 0,
                "summary": TEST_EDIT_SUMMARY,
                "rule": TEST_EDIT_RULE,
                "source": "framework",
            }
        )
    return out


# --- the record of findings already seen (article p.34 step 5) -------------------------------
def seen_record_path(root: Path) -> Path:
    """``changes/.review-seen.json``: one file per project, committed with the change."""
    return Path(root) / c.CHANGES_DIR / SEEN_FILE


def update_seen(
    record: dict[str, Any],
    findings: Iterable[dict[str, Any]],
    change_id: str,
    at: str,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Fold this review's findings into the project's record and say which of them are the
    second occurrence of a finding from an *earlier* change.

    The record maps signature -> ``{"count", "first_change", "last_change", "summary", "file",
    "last_seen"}``. A finding is repeated when its signature was already recorded (count >= 1)
    by another change id; two occurrences inside one change are one mistake being reviewed
    twice, not the pattern the CLAUDE.md line is for.
    """
    updated = {k: dict(v) for k, v in record.items() if isinstance(v, dict)}
    repeated: list[dict[str, Any]] = []
    handled: set[str] = set()
    for finding in findings:
        if not isinstance(finding, dict):
            continue
        sig = finding.get("signature") or signature(finding)
        if sig in handled:
            continue
        handled.add(sig)
        entry = updated.get(sig, {})
        count = entry.get("count", 0)
        count = count if isinstance(count, int) and not isinstance(count, bool) else 0
        first = entry.get("first_change") or change_id
        if count >= 1 and first != change_id:
            item = dict(finding)
            item["signature"] = sig
            item["first_change"] = first
            item["change_id"] = change_id
            repeated.append(item)
        updated[sig] = {
            "count": count + 1,
            "first_change": first,
            "last_change": change_id,
            "summary": str(finding.get("summary", "")),
            "file": str(finding.get("file", "")),
            "last_seen": at,
        }
    return updated, repeated


def claude_md_lines(repeated: list[dict[str, Any]]) -> list[str]:
    """One line per repeated finding, to propose under "Things Claude gets wrong" in CLAUDE.md
    (article p.34 step 5). The review proposes; the owner applies it — CLAUDE.md is a protected
    path and the hook denies the edit (REVIEW.md framework rules)."""
    lines: list[str] = []
    for finding in repeated:
        summary = str(finding.get("summary", "")).strip().rstrip(".")
        first = finding.get("first_change", "?")
        this = finding.get("change_id", "?")
        pass_name = str(finding.get("pass", "")).strip() or "review"
        line = f"- {summary} (seen in changes {first} and {this}; {pass_name})"
        if line not in lines:
            lines.append(line)
    return lines


# --- the markdown the check run and the PR description show ----------------------------------
def _finding_line(finding: dict[str, Any]) -> str:
    where = normalise_file(finding.get("file", "")) or "(no file)"
    line = _line_of(finding)
    where = f"{where}:{line}" if line else where
    summary = str(finding.get("summary", "")).strip()
    rule = str(finding.get("rule", "") or "").strip()
    return f"- `{where}` — {summary}" + (f" [{rule}]" if rule else "")


def render_summary(data: dict[str, Any]) -> str:
    """The markdown body of the ``sdlc/review`` check run, quoted in the PR description: the
    machine-readable tally in words (article p.33 step 3), every Important finding on one line
    and the nits the reviewer kept (at most five, article p.34)."""
    tally = data.get("tally") if isinstance(data.get("tally"), dict) else {}
    counts = {k: int(tally.get(k, 0) or 0) for k in ("important", "nit", "nits_omitted")}
    items = [f for f in data.get("findings", []) if isinstance(f, dict)]
    importants = [f for f in items if _severity(f) == "important"]
    nits = [f for f in items if _severity(f) == "nit"]
    head = str(data.get("head", "") or "")
    lines = ["## Review findings (bugs · security · compliance)"]
    tally_line = f"**{counts['important']} Important, {counts['nit']} nits**"
    if counts["nits_omitted"]:
        tally_line += f", {counts['nits_omitted']} further nits omitted"
    if head:
        tally_line += f" — commit `{head[:10]}`"
    lines.append(tally_line + ".")
    if importants:
        lines += ["", "### Important", *[_finding_line(f) for f in importants]]
    if nits:
        lines += ["", "### Nits", *[_finding_line(f) for f in nits]]
    if not items:
        lines += ["", "No findings: the three passes found nothing to report."]
    return "\n".join(lines) + "\n"
