"""Artifact contracts the gate checks against (build guide step 16: "artifact exists and
matches its template").

The section names are the single definition for intent.md (skill ``intent-template``),
plan.md (skill ``plan-template``), spec.md (written by ``/sdlc-design`` in B3; the article
p.13–14 prescribes the prompt, not the sections, so they are defined here: requirements and
design, the intent's open questions answered or carried forward (p.14 step 3), flagged
concerns (p.14 step 4, mandatory — "the points an analyst would have escalated"), and the
acceptance target the test phase measures (p.27 step 3)), the evidence files phase (d)
leaves behind (step 28) and the two JSON files the review passes and the adversarial
reviewer write into ``evidence/``.
"""

from __future__ import annotations

import re
from pathlib import Path

INTENT_SECTIONS = (
    "## Problem",
    "## Proposed outcome",
    "## Affected users and systems",
    "## Constraints",
    "## Open questions",
)
INTENT_HEADER_FIELDS = ("Author:", "Status:", "Change id:", "Entry route:")
# The first heading of intent.md: "# Intent: <title>" (skill ``intent-template``).
INTENT_TITLE_RE = re.compile(r"(?i)^#\s*Intent:\s*(?P<title>.*)$")

SPEC_SECTIONS = (
    "## Requirements",
    "## Design",
    "## Open questions from intent",
    "## Flagged concerns",
    "## Acceptance",
)
# The spec header logs the change, the prompt and the versions in force (article p.14:
# "the spec, the prompt that produced it, and the skill versions in force are all logged").
SPEC_HEADER_FIELDS = ("Change id:", "Produced by:")
# The prompt text itself lives in plugin/commands/sdlc-design.md and is logged through the
# plugin pin (article p.14): the pinned plugin version identifies the prompt that ran, so the
# header carries this version number, not a copy of the prompt.
DESIGN_PROMPT_VERSION = "v1"

PLAN_SECTIONS = (
    "## Files that change",
    "## Order of work",
    "## Risks",
    "## Options not taken",
    "## Proof",
)

ARTIFACT_SECTIONS = {
    "intent.md": INTENT_SECTIONS,
    "spec.md": SPEC_SECTIONS,
    "plan.md": PLAN_SECTIONS,
}

# Files under changes/<id>-<slug>/evidence/ (OPERATING_MODEL section 1, step 28: "the literal
# output of the test command, the build log, the lint output ... the verifier report").
EVIDENCE_DIR = "evidence"
EVIDENCE_TEST = "test.log"
EVIDENCE_BUILD = "build.log"
EVIDENCE_LINT = "lint.log"
EVIDENCE_VERIFIER = "verifier.md"
EVIDENCE_SCREENSHOTS = "screenshots"  # UI proof of phase (d); created empty with a .gitkeep
EVIDENCE_TARGETS = {"test": EVIDENCE_TEST, "build": EVIDENCE_BUILD, "lint": EVIDENCE_LINT}
REVIEW_FINDINGS = "review-findings.json"  # the review passes' machine-readable tally (p.33)
ADVERSARIAL_VERDICT = "adversarial-review-{phase}.json"  # the agent of step 17, per gate
GATE_RESULT = "gate-{phase}.json"  # written by the gate itself, read by the PR summary (B3)

# Which artifacts and evidence each gate requires. The key is the phase that just finished.
REQUIRED_ARTIFACTS = {
    "a": ("intent.md",),
    "b": ("intent.md", "spec.md", "plan.md"),
    "c": ("intent.md", "spec.md", "plan.md"),
    "d": ("intent.md", "spec.md", "plan.md"),
    "e": ("intent.md", "spec.md", "plan.md"),
    "f": (),
}
REQUIRED_EVIDENCE = {
    "c": (EVIDENCE_VERIFIER,),
    "d": (EVIDENCE_TEST, EVIDENCE_BUILD, EVIDENCE_LINT, EVIDENCE_VERIFIER),
    "e": (EVIDENCE_TEST, EVIDENCE_BUILD, EVIDENCE_LINT, EVIDENCE_VERIFIER),
}
# The review passes (step 26, phase e) publish review-findings.json; the gate refuses to pass
# gate (e) without it, and reads it at (c)/(d) whenever it is present.
FINDINGS_REQUIRED_AT = ("e",)

# The first line of each command log written by plugin/evidence/collect.py (step 28):
#   # <command> — exit <code> — <seconds>s — <ISO-8601 UTC>
# followed by the literal combined output of the command (article p.27-29: the evidence is
# the toolchain's own output, not a summary of it). The gate reads the header back, so a log
# whose header records a failure parks the change even when the gate's own re-run is green.
EVIDENCE_TIMEOUT = "timeout"  # the exit field when the command was killed at the timeout
EVIDENCE_HEADER_RE = re.compile(
    r"^#\s+(?P<command>.+?)\s+—\s+exit\s+(?P<exit>-?\d+|timeout)\s+—\s+"
    r"(?P<seconds>[0-9.]+)s\s+—\s+(?P<at>\S+)\s*$"
)


def render_evidence_header(command: str, exit_code: int | None, seconds: float, at: str) -> str:
    """The first line of test.log / build.log / lint.log."""
    code = EVIDENCE_TIMEOUT if exit_code is None else int(exit_code)
    return f"# {command} — exit {code} — {seconds:.1f}s — {at}"


def parse_evidence_header(text: str) -> dict[str, str] | None:
    """{'command', 'exit', 'seconds', 'at'} from a log's first line, or None when the log was
    not written by collect.py (a hand-written log is accepted as it is)."""
    first = (text or "").splitlines()[:1]
    if not first:
        return None
    m = EVIDENCE_HEADER_RE.match(first[0])
    return m.groupdict() if m else None


MISSING_HEADER = "evidence log without the collector header: re-run evidence/collect.py"


def evidence_failure(text: str, *, require_header: bool = False) -> str | None:
    """The header's failure, or None when the log records exit 0.

    ``require_header`` is what gates (d) and (e) pass for the three command logs: a log
    nobody can date back to a command and an exit code is not evidence, and accepting it
    would let a hand-written "all good" stand in for the toolchain's own output (p.27-29).
    """
    header = parse_evidence_header(text)
    if header is None:
        return MISSING_HEADER if require_header else None
    if header["exit"] == EVIDENCE_TIMEOUT:
        return f"`{header['command']}` timed out after {header['seconds']}s"
    if header["exit"] != "0":
        return f"`{header['command']}` exited {header['exit']}"
    return None


# A line in intent.md's header that marks the change as the framework itself, which is the
# only case where the diff may touch the guardrail files (OPERATING_MODEL section 3).
FRAMEWORK_CHANGE_RE = re.compile(r"(?im)^\s*Framework change:\s*yes\b")

# Flagged concerns in spec.md: every list item is a concern; it is closed only when it says
# so (a decision recorded, article p.14 step 4). Anything else is open — fail closed. The
# gate's risk-list check reads this section too, and only this section of the spec.
CONCERNS_SECTION = "## Flagged concerns"
CONCERN_ITEM_RE = re.compile(r"^\s*(?:[-*]|\d+[.)])\s+(?P<text>.+)$")
CLOSED_CONCERN_RE = re.compile(r"(?i)^(?:\[x\]|closed\b|resolved\b|decided\b)")
NO_CONCERN_RE = re.compile(r"(?i)^(?:none|n/a|no concerns?)\.?$")


def split_sections(text: str) -> dict[str, str]:
    """{'## Heading': body} for every level-2 heading; '' for text before the first."""
    out: dict[str, str] = {}
    heading, buf = "", []
    for line in text.splitlines():
        if line.startswith("## "):
            out[heading] = "\n".join(buf)
            heading, buf = line.strip(), []
        else:
            buf.append(line)
    out[heading] = "\n".join(buf)
    return out


def missing_sections(text: str, required: tuple[str, ...]) -> list[str]:
    present = set(split_sections(text))
    return [h for h in required if h not in present]


def empty_sections(text: str, required: tuple[str, ...]) -> list[str]:
    sections = split_sections(text)
    return [h for h in required if h in sections and not sections[h].strip()]


def render_spec_header(
    title: str,
    change_id: str,
    plugin_version: str,
    skills: list[str],
    overrides: list[str],
) -> str:
    """The two header lines of spec.md, exactly as the ``spec-template`` skill shows them
    (article p.14: the spec, the prompt that produced it and the skill versions in force are
    logged together). ``gate/cli.py spec-header`` renders it; the design pass pastes it."""
    applied = ", ".join(skills)
    overridden = ", ".join(overrides) if overrides else "none"
    return (
        f"# Spec: {title}\n"
        f"Change id: {change_id}. Status: proposed. Produced by: sdlc plugin "
        f"{plugin_version}, /sdlc-design prompt {DESIGN_PROMPT_VERSION} (article p.14). "
        f"Skills: {applied} (plugin {plugin_version}); overrides: {overridden}"
    )


def intent_title(intent_text: str) -> str | None:
    """The title of intent.md: the text after ``# Intent:`` on its first heading line."""
    for line in intent_text.splitlines():
        if not line.startswith("#"):
            continue
        m = INTENT_TITLE_RE.match(line)
        if not m:
            return None
        return m.group("title").strip() or None
    return None


def is_framework_change(intent_text: str) -> bool:
    return FRAMEWORK_CHANGE_RE.search(intent_text) is not None


def open_concerns(spec_text: str) -> list[str]:
    body = split_sections(spec_text).get(CONCERNS_SECTION, "")
    out = []
    for line in body.splitlines():
        m = CONCERN_ITEM_RE.match(line)
        if not m:
            continue
        text = m.group("text").strip()
        if NO_CONCERN_RE.match(text) or CLOSED_CONCERN_RE.match(text):
            continue
        out.append(line.strip())
    return out


def planned_files(plan_text: str) -> list[str]:
    """Paths listed under "## Files that change": the first backtick span or the first word
    of each list item (a plan says `path/to/file.py — what changes`)."""
    body = split_sections(plan_text).get("## Files that change", "")
    files: list[str] = []
    for line in body.splitlines():
        s = line.strip()
        if not s or s[0] not in "-*0123456789":
            continue
        s = re.sub(r"^(?:[-*]|\d+[.)])\s*", "", s)
        m = re.search(r"`([^`]+)`", s)  # the first backtick span anywhere in the item
        token = m.group(1) if m else re.split(r"[\s—:]", s, maxsplit=1)[0]
        token = token.strip().strip("`'\"").replace("\\", "/")
        token = re.sub(r"^(?:\./)+", "", token)  # keep dotfiles: .github/..., .gitignore
        if token and token.lower() not in ("none", "n/a"):
            files.append(token)
    return files


def read_text(path: Path) -> str | None:
    try:
        return Path(path).read_text(encoding="utf-8")
    except OSError:
        return None
