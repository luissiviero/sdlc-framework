"""The generated pull-request description (build guide steps 23, 27, 27a, 28, 42;
decision 20; OPERATING_MODEL section 7).

"Every PR the framework opens or updates starts with a <=5-bullet summary: what changed and
why, evidence status, review findings by severity, plan conformance, and - if parked - what
is needed" (OPERATING_MODEL section 7). This module renders exactly that, from files only:
``status.yaml``, ``intent.md``, ``spec.md``, ``plan.md``, ``evidence/`` and
``evidence/gate-<phase>.json``. It is pure: no network, no writes, so it is unit-testable and
re-runnable after every review comment.

Layout of the body, in order:
  1. the five bullets, one line each (a fixed order, so the owner reads the same shape every
     time); when the gate parked, the fifth bullet points at the "What I need from you" block
     and the block itself follows the list verbatim (it is multi-line, a bullet is not). At
     phase (a) the intent PR has no spec, no diff and no gate file, so the middle bullets
     describe the intent instead: entry route, affected users and systems, open questions;
  2. ``Links:`` intent, spec, plan and the gate result, as blob links on the head branch when
     the GitHub remote lets us build the URL, else as plain repository paths;
  3. ``Counters:`` the two indicators of step 42 - first-pass merge yes/no and fix iterations;
  4. the proposed ``CLAUDE.md`` lines when the review pass left them (never applied here:
     ``CLAUDE.md`` is a protected path, the owner applies the line in the PR review);
  5. at phase (e), the release note: ``evidence/release-notes.md`` (written by
     ``plugin/release/notes.py``, build guide step 32) quoted without its H1 title and with
     its headings demoted one level so they nest, else the intent's proposed outcome, in the
     owner's words.

At phase (e), when ``sdlc.yaml: deploy.production`` is true, one more line follows the
bullets (like the counters line, not a sixth bullet): the release approval, the second act
of gate (e) (decision 13).
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

PLUGIN_DIR = Path(__file__).resolve().parent.parent
if str(PLUGIN_DIR) not in sys.path:
    sys.path.insert(0, str(PLUGIN_DIR))

from gate import artifacts as art  # noqa: E402
from gate import checks  # noqa: E402
from gate.checks import CheckResult  # noqa: E402
from gate.gate import GateResult  # noqa: E402
from hooks._common import ConfigError, load_sdlc_config  # noqa: E402
from state import conventions as c  # noqa: E402
from state import gitops  # noqa: E402
from state import status as status_mod  # noqa: E402
from state.status import Status  # noqa: E402

ARTIFACTS = ("intent.md", "spec.md", "plan.md")
LOG_FILES = (art.EVIDENCE_TEST, art.EVIDENCE_BUILD, art.EVIDENCE_LINT)
SCREENSHOT_DIR = "screenshots"
CLAUDE_MD_PROPOSALS = "claude-md-proposals.md"
RELEASE_NOTES = "release-notes.md"
MAX_NITS = 5

# ``evidence/collect.py`` writes "# <command> — exit <code> — <seconds>s — <ISO-8601 UTC>"
# as the first line of each log (build guide step 28; artifacts.EVIDENCE_HEADER_RE): the exit
# code, not the agent's claim, is the evidence. ``exit timeout`` is a killed command, so it
# reads red like any other non-zero exit.
EXIT_RE = re.compile(rf"exit\s+(\d+|{art.EVIDENCE_TIMEOUT})")
SENTENCE_RE = re.compile(r"(?s)^(.*?[.!?])(?:\s|$)")
LIST_ITEM_RE = re.compile(r"^\s*(?:[-*]|\d+[.)])\s+(?P<text>.+)$")
CARRIED_FORWARD_RE = re.compile(r"(?i)carried forward")
HEADING_RE = re.compile(r"^#{2,5} ")  # an H2-H5 heading of release-notes.md, demoted once

# The PR the phase opens: (b) has its own spec+plan PR; (c), (d) and (e) share the one build
# PR the article keeps open from build to merge (p.34; OPERATING_MODEL section 4.1).
PR_BRANCH_PHASE = {"a": "a", "b": "b", "c": "c", "d": "c", "e": "c", "f": "a"}
TITLE_PREFIX = {
    "a": "intent",
    "b": "design",
    "c": "build",
    "d": "build",
    "e": "build",
    "f": "maintain",
}

# The four questions of build guide step 23, asked at gate (b) in the owner's own words.
STEP_23_CHECKLIST = (
    "Does the spec solve the problem the intent states?",
    "Are the open questions from intent.md answered or carried forward?",
    "Is every flagged concern closed with a decision?",
    "Is plan.md implementable by someone who never saw the conversation?",
)
GATE_CHECKLIST = {
    "a": "read, correct via review comments, merge = approve (gate (a))",
    "b": "; ".join(STEP_23_CHECKLIST)
    + " Merge = approve; a review comment = change request (/sdlc-fix).",
    "c": "approving review + label sdlc:c-approved starts the test phase",
    "d": "approving review + label sdlc:d-approved starts the review phase",
    "e": "merge = approve; a review comment is the change request (/sdlc-fix). Waiting for "
    "your merge: merge = gate (e) passed; the release workflow then runs `deploy.command`",
}
# Decision 13: when the project declares a real production, the merge is the first act and
# the release label, applied by a person on GitHub, the second (the only route: a run cannot
# approve itself, decision 11).
RELEASE_APPROVAL_LINE = (
    f"Release approval: apply `{c.RELEASE_APPROVED_LABEL}` on this PR after merging; the "
    "release workflow waits for it."
)
NOTHING_NEEDED = "nothing: the run continues to the next phase"


# --- small readers ----------------------------------------------------------------------
def head_branch(change_id: str, phase: str) -> str:
    """The branch the phase's PR is opened from (b has its own; c, d and e share one)."""
    return c.branch_name(change_id, PR_BRANCH_PHASE.get(phase, phase))


def load_gate(change_dir: Path, phase: str) -> dict[str, Any] | None:
    """``evidence/gate-<phase>.json`` as the gate wrote it (``GateResult.as_dict``)."""
    path = Path(change_dir) / art.EVIDENCE_DIR / art.GATE_RESULT.format(phase=phase)
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) else None


def label_for(gate_json: dict[str, Any] | None, phase: str | None = None) -> str | None:
    """The label the gate printed: ``sdlc:<phase>-ready``, ``sdlc:needs-human``, or none.
    Phase (a) has no gate file - the intent PR always waits for the owner - so a missing
    result there means ``sdlc:a-ready``."""
    if not gate_json:
        return c.ready_label("a") if phase == "a" else None
    label = gate_json.get("label")
    return label if isinstance(label, str) and label else None


def pr_title(status: Status, phase: str) -> str:
    return f"{TITLE_PREFIX.get(phase, 'sdlc')}({status.id}): {status.title}"


def _section(text: str | None, heading: str) -> str:
    return art.split_sections(text or "").get(heading, "").strip()


def _first_sentence(text: str) -> str:
    """The first sentence of a section body, list markers and blank lines removed."""
    for raw in (text or "").splitlines():
        line = raw.strip()
        if not line or line.startswith(("#", ">", "|")):
            continue
        m = LIST_ITEM_RE.match(line)
        if m:
            line = m.group("text").strip()
        m = SENTENCE_RE.match(line)
        return (m.group(1) if m else line).strip()
    return ""


def _list_items(body: str) -> list[str]:
    items = []
    for line in (body or "").splitlines():
        m = LIST_ITEM_RE.match(line)
        if m:
            items.append(m.group("text").strip())
    return items


# --- bullet 2: evidence status ------------------------------------------------------------
def log_state(path: Path) -> str:
    """green / red / missing, read from the log's first line (``... — exit <code> — ...``)."""
    if not Path(path).is_file():
        return "missing"
    try:
        with Path(path).open(encoding="utf-8", errors="replace") as fh:
            first = fh.readline().strip()
    except OSError:
        return "missing"
    m = EXIT_RE.search(first)
    if not m:
        return "unknown"
    return "green" if m.group(1) == "0" else "red"


def evidence_status(change_dir: Path, phase: str) -> str:
    """One line: the three logs, the verifier report and the screenshot count."""
    if phase in ("a", "b"):
        return "design phase, no code yet"
    evidence = Path(change_dir) / art.EVIDENCE_DIR
    parts = [f"{name.removesuffix('.log')} {log_state(evidence / name)}" for name in LOG_FILES]
    verifier = evidence / art.EVIDENCE_VERIFIER
    parts.append(f"verifier.md {'present' if verifier.is_file() else 'missing'}")
    shots = evidence / SCREENSHOT_DIR
    count = len([p for p in shots.iterdir() if p.is_file()]) if shots.is_dir() else 0
    parts.append(f"{count} screenshot(s)")
    return ", ".join(parts)


# --- bullet 3: review findings / flagged concerns -------------------------------------------
def _concern_counts(spec_text: str) -> tuple[list[str], int]:
    """(open concerns verbatim, closed count) from spec.md "## Flagged concerns"."""
    open_items = art.open_concerns(spec_text or "")
    closed = 0
    for text in _list_items(art.split_sections(spec_text or "").get("## Flagged concerns", "")):
        if art.NO_CONCERN_RE.match(text):
            continue
        if art.CLOSED_CONCERN_RE.match(text):
            closed += 1
    return open_items, closed


def _findings_line(change_dir: Path) -> str:
    path = Path(change_dir) / art.EVIDENCE_DIR / art.REVIEW_FINDINGS
    data, _error = checks.load_findings(path)
    if data is None:
        return "not yet reviewed"
    important = checks.important_findings(data)
    nits = [
        f
        for f in data["findings"]
        if isinstance(f, dict) and str(f.get("severity", "")).lower() == "nit"
    ]
    line = f"{len(important)} Important, {len(nits)} nits"
    listed = [str(f.get("summary", "")).strip() for f in nits[:MAX_NITS]]
    listed = [s for s in listed if s]
    return f"{line} ({'; '.join(listed)})" if listed else line


# --- bullet 4: plan conformance -------------------------------------------------------------
def _gate_check(gate_json: dict[str, Any] | None, name: str) -> dict[str, Any] | None:
    for ch in (gate_json or {}).get("checks") or []:
        if isinstance(ch, dict) and ch.get("name") == name:
            return ch
    return None


def _conformance_line(gate_json: dict[str, Any] | None, spec_text: str, phase: str) -> str:
    if phase in ("a", "b"):
        items = _list_items(_section(spec_text, "## Open questions from intent"))
        items = [i for i in items if not art.NO_CONCERN_RE.match(i)]
        carried = [i for i in items if CARRIED_FORWARD_RE.search(i)]
        answered = len(items) - len(carried)
        return f"open questions from intent: {answered} answered / {len(carried)} carried forward"
    check = _gate_check(gate_json, "plan_sync")
    if check is None:
        return "plan conformance not checked at this gate"
    return "diff matches plan.md" if check.get("ok") else str(check.get("reason", "")).strip()


# --- bullet 5: what needs the owner ----------------------------------------------------------
def what_i_need_block(gate_json: dict[str, Any]) -> str:
    """The parked block, verbatim from the gate result; rebuilt from the checks when the JSON
    predates it (``GateResult.what_i_need`` is the single renderer - never re-derived here)."""
    stored = gate_json.get("what_i_need")
    if isinstance(stored, str) and stored.strip():
        return stored.strip("\n")
    try:
        result = GateResult(
            change_id=str(gate_json.get("change_id", "")),
            slug=str(gate_json.get("slug", "")),
            phase=str(gate_json.get("phase", "")),
            profile=str(gate_json.get("profile", "")),
            human_gate=bool(gate_json.get("human_gate", False)),
            result=str(gate_json.get("result", "")),
            checks=[
                CheckResult(
                    name=str(ch.get("name", "")),
                    ok=bool(ch.get("ok")),
                    reason=str(ch.get("reason", "")),
                    need=str(ch.get("need", "")),
                    details=ch.get("details") or {},
                )
                for ch in gate_json.get("checks") or []
                if isinstance(ch, dict)
            ],
            label=gate_json.get("label"),
            head=gate_json.get("head"),
            at=str(gate_json.get("at", "")),
        )
    except (TypeError, ValueError):
        return ""
    return result.what_i_need().strip("\n")


def _owner_line(gate_json: dict[str, Any] | None, phase: str) -> str:
    result = (gate_json or {}).get("result")
    if result == "park":
        return (
            f'parked at gate ({phase}) - see "What I need from you" below; '
            "nobody was notified (decision 11)"
        )
    if result == "wait" or phase == "a":  # gate (a) is the owner's merge in every profile
        return GATE_CHECKLIST.get(phase, "the owner's review is the gate")
    return NOTHING_NEEDED


def _intent_bullets(intent: str, st: Status) -> list[str]:
    """Phase (a): the intent PR /sdlc-plan opens. There is no spec, no diff and no gate file
    yet, so the middle bullets describe the intent itself (build guide step 11)."""
    problem = _first_sentence(_section(intent, "## Problem"))
    affected = _first_sentence(_section(intent, "## Affected users and systems"))
    questions = [
        item
        for item in _list_items(_section(intent, "## Open questions"))
        if not art.NO_CONCERN_RE.match(item)
    ]
    body = _section(intent, "## Open questions")
    if not questions:
        open_line = "none" if body else "none recorded"
    else:
        open_line = f"{len(questions)} open: " + "; ".join(questions)
    return [
        f"- **What changed and why**: {st.title}: {problem}",
        f"- **Entry route**: {st.entry_route} route, {st.change_type} change",
        f"- **Affected users and systems**: {affected or 'not stated'}",
        f"- **Open questions**: {open_line}",
        f"- **What needs you**: {GATE_CHECKLIST['a']}",
    ]


# --- the body ---------------------------------------------------------------------------------
def _links_line(root: Path, change_dir: Path, change_id: str, phase: str) -> str:
    rel_dir = str(Path(change_dir).relative_to(root)).replace("\\", "/")
    if phase == "a":  # spec, plan and the gate result do not exist yet
        targets = ["intent.md"]
    else:
        targets = [*ARTIFACTS, f"{art.EVIDENCE_DIR}/{art.GATE_RESULT.format(phase=phase)}"]
    try:
        repo = gitops.github_repo(Path(root))
    except Exception:  # noqa: BLE001 - a missing git is not a reason to lose the summary
        repo = None
    branch = head_branch(change_id, phase)
    parts = []
    for name in targets:
        rel = f"{rel_dir}/{name}"
        parts.append(f"[{name}](https://github.com/{repo}/blob/{branch}/{rel})" if repo else rel)
    return "Links: " + " · ".join(parts)


def production_declared(root: Path) -> bool:
    """``sdlc.yaml: deploy.production`` is true. An unreadable or absent file declares
    nothing (the gate, not the PR body, is where a broken sdlc.yaml parks)."""
    try:
        config = load_sdlc_config(str(root))
    except ConfigError:
        return False
    deploy = config.get("deploy")
    return isinstance(deploy, dict) and deploy.get("production") is True


def release_note(change_dir: Path, intent: str) -> str:
    """``evidence/release-notes.md`` without its H1 title line, headings demoted one level
    (``## `` becomes ``### ``), otherwise verbatim; else the intent's
    proposed outcome on one line; "" when neither exists."""
    notes = art.read_text(Path(change_dir) / art.EVIDENCE_DIR / RELEASE_NOTES)
    if notes and notes.strip():
        lines = notes.strip("\n").splitlines()
        if lines and lines[0].startswith("# "):
            lines = lines[1:]
        # demote the file's headings one level so they nest under "## Release note"
        lines = [f"#{line}" if HEADING_RE.match(line) else line for line in lines]
        body = "\n".join(lines).strip("\n")
        if body.strip():
            return body
    outcome = _section(intent, "## Proposed outcome")
    return " ".join(outcome.split()) if outcome else ""


def _counters_line(st: Status) -> str:
    first_pass = "yes" if st.iterations == 0 else "no"
    return f"Counters: first-pass merge: {first_pass} · fix iterations: {st.iterations}"


def build_description(root: Path, change_id: str, phase: str) -> str:
    """The whole PR body for a change at a phase. Pure: reads files, contacts nothing."""
    root = Path(root).resolve()
    if phase not in c.PHASES:
        raise ValueError(f"phase must be one of {c.PHASES}, got {phase!r}")
    change_dir = c.find_change_dir(root, change_id)
    if change_dir is None:
        raise ValueError(f"no change folder for id {change_id} under {root / c.CHANGES_DIR}")
    st = status_mod.read_status(change_dir)
    intent = art.read_text(change_dir / "intent.md") or ""
    spec = art.read_text(change_dir / "spec.md") or ""
    gate_json = load_gate(change_dir, phase)

    if phase == "a":
        bullets = _intent_bullets(intent, st)
        out = [" ".join(b.split()) for b in bullets]
        out += ["", _links_line(root, change_dir, change_id, phase), "", _counters_line(st)]
        return "\n".join(out) + "\n"

    problem = _first_sentence(_section(intent, "## Problem"))
    what = f"{st.title} ({st.change_type}, {st.entry_route} route): {problem}"
    design = _first_sentence(_section(spec, "## Design"))
    if design:
        what = f"{what} Design: {design}"
    if phase == "b":
        open_items, closed = _concern_counts(spec)
        quoted = "; ".join(f'"{item}"' for item in open_items)
        findings = f"flagged concerns: {len(open_items)} open / {closed} closed"
        findings = f"{findings} ({quoted})" if quoted else findings
    else:
        findings = _findings_line(change_dir)

    bullets = [
        f"- **What changed and why**: {what}".rstrip(),
        f"- **Evidence**: {evidence_status(change_dir, phase)}",
        f"- **Review findings**: {findings}",
        f"- **Plan conformance**: {_conformance_line(gate_json, spec, phase)}",
        f"- **What needs you**: {_owner_line(gate_json, phase)}",
    ]
    out = [" ".join(b.split()) for b in bullets]

    if (gate_json or {}).get("result") == "park":
        block = what_i_need_block(gate_json)
        if block:
            out += ["", block]
    if phase == "e" and production_declared(root):
        out += ["", RELEASE_APPROVAL_LINE]
    out += ["", _links_line(root, change_dir, change_id, phase), "", _counters_line(st)]

    proposals = art.read_text(change_dir / art.EVIDENCE_DIR / CLAUDE_MD_PROPOSALS)
    if proposals and proposals.strip():
        quoted_lines = "\n".join(f"> {line}".rstrip() for line in proposals.strip().splitlines())
        out += ["", "## Proposed CLAUDE.md lines", "", quoted_lines]

    if phase == "e":
        note = release_note(change_dir, intent)
        if note:
            out += ["", "## Release note", "", note]
    return "\n".join(out) + "\n"
