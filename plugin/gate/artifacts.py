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

SPEC_SECTIONS = (
    "## Requirements",
    "## Design",
    "## Open questions from intent",
    "## Flagged concerns",
    "## Acceptance",
)

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

# A line in intent.md's header that marks the change as the framework itself, which is the
# only case where the diff may touch the guardrail files (OPERATING_MODEL section 3).
FRAMEWORK_CHANGE_RE = re.compile(r"(?im)^\s*Framework change:\s*yes\b")

# Open concern in spec.md's "Flagged concerns" list: an item not closed with a decision.
OPEN_CONCERN_RE = re.compile(r"(?im)^\s*[-*]\s+(?:\[ \]|open\b|OPEN\b)")
CLOSED_CONCERN_RE = re.compile(r"(?im)^\s*[-*]\s+(?:\[x\]|closed\b|resolved\b|decided\b)")


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


def is_framework_change(intent_text: str) -> bool:
    return FRAMEWORK_CHANGE_RE.search(intent_text) is not None


def open_concerns(spec_text: str) -> list[str]:
    body = split_sections(spec_text).get("## Flagged concerns", "")
    return [line.strip() for line in body.splitlines() if OPEN_CONCERN_RE.match(line)]


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
        m = re.match(r"`([^`]+)`", s)
        token = m.group(1) if m else re.split(r"[\s—:]", s, maxsplit=1)[0]
        token = token.strip().strip("`'\"").replace("\\", "/")
        if token and token.lower() not in ("none", "n/a"):
            files.append(token.lstrip("./"))
    return files


def read_text(path: Path) -> str | None:
    try:
        return Path(path).read_text(encoding="utf-8")
    except OSError:
        return None
