"""Artifact contracts the gate checks against (build guide step 16: "artifact exists and
matches its template").

The section names are the single definition for intent.md (skill ``intent-template``),
plan.md (skill ``plan-template``), spec.md (written by ``/sdlc-design`` in B3; the article
p.13–14 prescribes the prompt, not the sections, so they are defined here: requirements and
design, the intent's open questions answered or carried forward (p.14 step 3), flagged
concerns (p.14 step 4, mandatory — "the points an analyst would have escalated"), and the
acceptance target the test phase measures (p.27 step 3)), the evidence files the test phase
leaves behind (step 28) and the two JSON files the review passes and the adversarial
reviewer write into ``evidence/``.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from state import conventions as c

INTENT_SECTIONS = (
    "## Problem",
    "## Proposed outcome",
    "## Affected users and systems",
    "## Constraints",
    "## Open questions",
)
# Incidents only (article p.44 step 5: "the anomaly and its evidence"): required by gate (maintain)
# when ``status.yaml: entry_route`` is ``incident``.
INTENT_EVIDENCE_SECTION = "## Evidence"
# R45 row 77: the header no longer carries ``Status:`` (``status.yaml`` holds the phase, and a
# frozen header line disagreed with it); an intent written before plugin 1.0.46 keeps its
# ``Status:`` line as history, and the gate neither requires nor refuses it.
INTENT_HEADER_FIELDS = ("Author:", "Change id:", "Entry route:")
# R29 part 1: the section for the owner's examples and references (skill ``intent-template``).
# Not in INTENT_SECTIONS: the gate does not require it, so changes in flight and the
# detection's incident intents never park on it (docs/proposals/intent-home.md).
INTENT_EXAMPLES_SECTION = "## Examples/References"
# R54, the quick intent: the owner writes the Problem paragraph only; each other article
# section holds this one line, and the design pass states what it assumed in spec.md's
# SPEC_ASSUMED_SECTION, which the design PR and the build PR show above their bullets.
QUICK_INTENT_RE = re.compile(r"(?im)^\s*Quick intent:\s*yes\b")
QUICK_INTENT_MARKER = "Left to the design run (quick intent)."
SPEC_ASSUMED_SECTION = "## Assumed from the quick intent"
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
EVIDENCE_SCREENSHOTS = "screenshots"  # UI proof of the test phase; created empty with a .gitkeep
EVIDENCE_TARGETS = {"test": EVIDENCE_TEST, "build": EVIDENCE_BUILD, "lint": EVIDENCE_LINT}
# Change 0004 (ROADMAP R14): the optional fourth target ``commands.drive`` exercises the product
# and writes its proof under ``evidence/proof/``; the runner's step writes ``drive.log``
EVIDENCE_DRIVE = "drive.log"
EVIDENCE_PROOF = "proof"
PROOF_MANIFEST = "manifest.json"  # written by the step after every drive run, never an item
PROOF_MAX_IMAGES = 10
PROOF_IMAGE_SUFFIXES = (".png", ".jpg", ".jpeg", ".webp", ".gif")
STATE_FILE_MAX_BYTES = 1024 * 1024  # a state file over 1 MiB is ``not produced``
REVIEW_FINDINGS = "review-findings.json"  # the review passes' machine-readable tally (p.33)
ADVERSARIAL_VERDICT = "adversarial-review-{phase}.json"  # the agent of step 17, per gate
# The adversarial reviewer's verdict, and its verdict on each risk-list item in the brief (R45
# row 62, N17): ``continue`` or ``park``, the word the gate's result and the state use for the
# same event (decision 11: nobody is paged). An older plugin wrote ``escalate``; a verdict file,
# a ledger line or a brief that says it is read as ``park`` for one release (``verdict_word``).
VERDICT_CONTINUE = "continue"
VERDICT_PARK = "park"
VERDICTS = (VERDICT_CONTINUE, VERDICT_PARK)
VERDICT_ALIASES = {"escalate": VERDICT_PARK}
GATE_RESULT = "gate-{phase}.json"  # written by the gate itself, read by the PR summary (B3)

# Which artifacts and evidence each gate requires. The key is the phase that just finished.
REQUIRED_ARTIFACTS = {
    c.INTENT: ("intent.md",),
    c.DESIGN: ("intent.md", "spec.md", "plan.md"),
    c.BUILD: ("intent.md", "spec.md", "plan.md"),
    c.TEST: ("intent.md", "spec.md", "plan.md"),
    c.DEPLOY: ("intent.md", "spec.md", "plan.md"),
    c.MAINTAIN: ("intent.md",),  # the incident intent (p.44 step 5); Evidence checked by the gate
}
REQUIRED_EVIDENCE = {
    c.BUILD: (EVIDENCE_VERIFIER,),
    c.TEST: (EVIDENCE_TEST, EVIDENCE_BUILD, EVIDENCE_LINT, EVIDENCE_VERIFIER),
    c.DEPLOY: (EVIDENCE_TEST, EVIDENCE_BUILD, EVIDENCE_LINT, EVIDENCE_VERIFIER),
}
# The incident's lesson and eval (change 0003; docs/proposals/okf-adoption.md R1), checked
# only at gate (deploy) by gate/checks.py:lesson_and_eval. The field names and order are spec.md
# Requirements' first bullet, minus the three optional fields (runbook, supersedes,
# retired_by); the value names what a present field must not be to count as missing.
LESSON_REQUIRED_FIELDS = {
    "type": "scalar",
    "title": "scalar",
    "description": "scalar",
    "tags": "list",
    "change": "scalar",
    "detected": "mapping",
    "fixed": "mapping",
    "generated": "mapping",
    "status": "scalar",
    "stale_after": "scalar",
    "sources": "list",
}
LESSON_STATUSES = ("stable", "retired")
# The eval case's two files: plugin/evals/case.py:178 is the only writer and must agree.
EVAL_PROMPT = "prompt.md"
EVAL_CHECKS = "checks.yaml"


def verdict_word(value: Any) -> str | None:
    """The reviewer's verdict ``value`` as this plugin names it: ``continue`` or ``park``
    (``escalate``, an older plugin's word, reads as ``park``: R45, for one release), or None
    when it is neither. The match is exact: a reader that tolerates case or markup (the
    brief's ``- Verdict:`` line) tidies the value first."""
    if not isinstance(value, str):
        return None
    word = VERDICT_ALIASES.get(value, value)
    return word if word in VERDICTS else None


def target_logs(drive_set: bool) -> dict[str, str]:
    """The command logs by target name: the three of ``EVIDENCE_TARGETS``, plus ``drive.log``
    when ``commands.drive`` is set (change 0004)."""
    logs = dict(EVIDENCE_TARGETS)
    if drive_set:
        logs["drive"] = EVIDENCE_DRIVE
    return logs


def required_evidence(phase: str, drive_set: bool) -> tuple[str, ...]:
    """``REQUIRED_EVIDENCE`` of ``phase``, with ``drive.log`` at test and deploy when the drive is
    set (change 0004, R7)."""
    required = REQUIRED_EVIDENCE.get(c.phase_name(phase), ())
    if drive_set and EVIDENCE_TEST in required:
        return (*required, EVIDENCE_DRIVE)
    return required


def lesson_glob(slug: str) -> str:
    """The glob a change's lesson file must match, year and month free, slug fixed (a looser
    ``lessons/*-<slug>.md`` would also match a file whose name merely ends in another
    change's slug)."""
    return f"lessons/[0-9][0-9][0-9][0-9]-[0-9][0-9]-{slug}.md"


# The review passes (step 26, the deploy phase) publish review-findings.json; the gate refuses to
# pass gate (deploy) without it, and reads it at build/test whenever it is present.
FINDINGS_REQUIRED_AT = (c.DEPLOY,)

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


# Item 3b (0.3.2): inside a CI session the evidence writer runs no target (the sandbox denies
# a nested ``.env*``, issue #91) and leaves this first line instead:
#   # <command> — deferred to the runner — <ISO-8601 UTC>
# The runner's commands step replaces the whole file with the target's own output after the
# session (``gate.run_deferred_commands``); the gate accepts the mark only while that step
# is still to come (``checks.check_evidence`` with the runner's mark in the environment).
EVIDENCE_DEFERRED = "deferred to the runner"
EVIDENCE_DEFERRED_RE = re.compile(
    rf"^#\s+(?P<command>.+?)\s+—\s+{EVIDENCE_DEFERRED}\s+—\s+(?P<at>\S+)\s*$"
)
EVIDENCE_DEFERRED_BODY = (
    "The target did not run inside the model's session: build, test and lint run after the "
    "session, outside its sandbox (issue #91), and the runner replaces this file with the "
    "target's own output. A file still reading this line was never replaced: the targets "
    "did not run, and the gate does not pass on it.\n"
)


def render_evidence_header(command: str, exit_code: int | None, seconds: float, at: str) -> str:
    """The first line of test.log / build.log / lint.log."""
    code = EVIDENCE_TIMEOUT if exit_code is None else int(exit_code)
    return f"# {command} — exit {code} — {seconds:.1f}s — {at}"


def render_deferred_header(command: str, at: str) -> str:
    """The first line of a log the session left to the runner (item 3b)."""
    return f"# {command} — {EVIDENCE_DEFERRED} — {at}"


def parse_deferred_header(text: str) -> dict[str, str] | None:
    """{'command', 'at'} when the log's first line is the deferred mark, else None."""
    first = (text or "").splitlines()[:1]
    if not first:
        return None
    m = EVIDENCE_DEFERRED_RE.match(first[0])
    return m.groupdict() if m else None


def write_evidence_log(path: Path, header: str, output: str) -> None:
    """A command log: the header line, then the literal output (``evidence/collect.py`` in
    the session, ``gate.run_deferred_commands`` on the runner)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    body = output if output.endswith("\n") or not output else output + "\n"
    path.write_text(f"{header}\n{body}", encoding="utf-8", newline="\n")


def parse_evidence_header(text: str) -> dict[str, str] | None:
    """{'command', 'exit', 'seconds', 'at'} from a log's first line, or None when the log was
    not written by collect.py (a hand-written log is accepted as it is)."""
    first = (text or "").splitlines()[:1]
    if not first:
        return None
    m = EVIDENCE_HEADER_RE.match(first[0])
    return m.groupdict() if m else None


MISSING_HEADER = "evidence log without the collector header: re-run evidence/collect.py"
DEFERRED_NEVER_REPLACED = (
    "evidence log still carries the session's deferred mark: the runner never replaced it "
    "with the target's output (issue #91); re-run evidence/collect.py"
)


def evidence_failure(text: str, *, require_header: bool = False) -> str | None:
    """The header's failure, or None when the log records exit 0.

    ``require_header`` is what gates (test) and (deploy) pass for the three command logs: a log
    nobody can date back to a command and an exit code is not evidence, and accepting it
    would let a hand-written "all good" stand in for the toolchain's own output (p.27-29).
    """
    header = parse_evidence_header(text)
    if header is None:
        if parse_deferred_header(text) is not None:
            # a mark the runner never replaced is no evidence at any gate (item 3b)
            return DEFERRED_NEVER_REPLACED
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
    sources: list[tuple[str, str]] | None = None,
) -> str:
    """The two header lines of spec.md, exactly as the ``spec-template`` skill shows them
    (article p.14: the spec, the prompt that produced it and the skill versions in force are
    logged together). ``gate/cli.py spec-header`` renders it; the design pass pastes it.
    ``sources`` are the owner's policy sources in force, ``(path, commit)`` each (R27): the
    record of which policy text judged the change, beside the plugin version."""
    applied = ", ".join(skills)
    overridden = ", ".join(overrides) if overrides else "none"
    in_force = ", ".join(f"{path}@{commit}" for path, commit in sources or []) or "none"
    return (
        f"# Spec: {title}\n"
        f"Change id: {change_id}. Status: proposed. Produced by: sdlc plugin "
        f"{plugin_version}, /sdlc-design prompt {DESIGN_PROMPT_VERSION} (article p.14). "
        f"Skills: {applied} (plugin {plugin_version}); overrides: {overridden}; "
        f"policy sources: {in_force}"
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


def is_quick_intent(intent_text: str) -> bool:
    """The header line ``Quick intent: yes`` (R54), read before the first section."""
    return QUICK_INTENT_RE.search(intent_text.split("## ", 1)[0]) is not None


def left_to_design(body: str) -> bool:
    """True when an intent section holds only the quick intent's marker (R54)."""
    text = re.sub(r"^\s*[-*]\s+", "", " ".join(body.split())).rstrip(".").lower()
    return text == QUICK_INTENT_MARKER.rstrip(".").lower()


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


def linked_part(path: Path) -> Path | None:
    """The first part of ``path`` that is a symbolic link, from the file itself up to the
    ``changes`` folder or the folder that holds ``.git`` (the project root, not judged), or
    None. R59 (the plugin security review of 2026-10-19, I2): a session can link
    ``evidence/claude-md-proposals.md`` to ``.env`` without reading it, and the runner, which
    builds the PR body outside the sandbox, would quote the target."""
    part = Path(path).absolute()
    while True:
        if part.is_symlink():
            return part
        parent = part.parent
        if part.name == "changes" or parent == part or (parent / ".git").exists():
            return None
        part = parent


def read_text(path: Path) -> str | None:
    """The file's text, or None when it is missing, unreadable or reached through a link
    (``linked_part``)."""
    try:
        if linked_part(path) is not None:
            return None
        return Path(path).read_text(encoding="utf-8")
    except OSError:
        return None


# --- change 0004: the proof items of plan.md's ``## Proof`` (skill ``plan-template``, R5) -----
# Only a list item whose text starts with ``test:``, ``screenshot:`` or ``state:`` is an item;
# prose, the ``ratchet:`` line and any other list item stay allowed beside them.
PROOF_SECTION = "## Proof"
PROOF_PREFIX = f"{EVIDENCE_DIR}/{EVIDENCE_PROOF}/"
PROOF_ITEM_RE = re.compile(
    r"^\s*(?:[-*]|\d+[.)])\s+(?P<kind>test|screenshot|state):[ \t]*(?P<rest>.*?)\s*$"
)
PROOF_SCREENSHOT_RE = re.compile(r"^(?P<file>\S+)(?:\s+vs\s+(?P<mock>mock/\S+))?$")
PROOF_STATE_RE = re.compile(r"^(?P<file>\S+)\s+(?P<path>\S+)\s+(?P<verb>\S+)(?:\s+(?P<value>.*))?$")
PROOF_VERBS = ("==", "contains", "matches")
PROOF_LINE_PATH = "line"
OUTCOME_MATCHES = "matches"
OUTCOME_DIFFERS = "differs"
OUTCOME_NOT_PRODUCED = "not produced"


@dataclass
class ProofItem:
    kind: str  # test | screenshot | state
    line: str  # the plan's line, stripped
    number: int  # its line number in plan.md
    file: str = ""  # evidence/proof/<file> for screenshot and state items
    path: str = ""  # state: a dotted JSON key, or ``line``
    verb: str = ""  # state: ``==``, ``contains`` or ``matches``
    value: str = ""  # state: the rest of the line; test: the test's name
    mock: str = ""  # screenshot: ``mock/<file>`` after ``vs``
    problem: str = ""  # why the item is malformed, empty when it is not


def _proof_file_problem(file: str) -> str:
    if not file.startswith(PROOF_PREFIX) or len(file) == len(PROOF_PREFIX):
        return f"the file must sit under {PROOF_PREFIX}"
    if file == PROOF_PREFIX + PROOF_MANIFEST:
        return f"{PROOF_MANIFEST} is the step's own file, never a proof file"
    return ""


def _parse_proof_item(kind: str, rest: str, line: str, number: int) -> ProofItem:
    item = ProofItem(kind, line, number)
    if kind == "test":
        item.value = rest
        item.problem = "" if rest else "a test item names the test"
        return item
    if kind == "screenshot":
        m = PROOF_SCREENSHOT_RE.match(rest)
        if not m:
            item.problem = "expected `screenshot: evidence/proof/<file>.png [vs mock/<file>]`"
            return item
        item.file, item.mock = m.group("file"), m.group("mock") or ""
        item.problem = _proof_file_problem(item.file) or (
            "" if item.file.lower().endswith(".png") else "a screenshot item names a .png file"
        )
        return item
    m = PROOF_STATE_RE.match(rest)
    if not m:
        item.problem = "expected `state: evidence/proof/<file> <path> ==|contains|matches <value>`"
        return item
    item.file, item.path, item.verb = m.group("file"), m.group("path"), m.group("verb")
    item.value = (m.group("value") or "").strip()
    item.problem = _proof_file_problem(item.file)
    if not item.problem and item.verb not in PROOF_VERBS:
        item.problem = f"the verb must be one of {', '.join(PROOF_VERBS)}, not {item.verb!r}"
    if not item.problem and item.verb == "matches":
        try:
            re.compile(item.value)
        except re.error as exc:
            item.problem = f"the pattern does not compile: {exc}"
    return item


def _all_proof_items(plan_text: str) -> list[ProofItem]:
    items: list[ProofItem] = []
    in_proof = False
    for number, line in enumerate((plan_text or "").splitlines(), start=1):
        if line.startswith("## "):
            in_proof = line.strip() == PROOF_SECTION
            continue
        m = PROOF_ITEM_RE.match(line) if in_proof else None
        if m:
            items.append(_parse_proof_item(m.group("kind"), m.group("rest"), line.strip(), number))
    return items


def proof_items(plan_text: str) -> list[ProofItem]:
    """The well-formed items of ``## Proof``, in plan order (R5)."""
    return [item for item in _all_proof_items(plan_text) if not item.problem]


def malformed_proof_items(plan_text: str) -> list[ProofItem]:
    """The items of ``## Proof`` that do not follow the grammar, each with its ``problem``."""
    return [item for item in _all_proof_items(plan_text) if item.problem]


def parse_value(text: str) -> Any:
    """The one parse of R5, for the expected value and for each line of a text file: JSON when
    it parses (``200``, ``true``, ``"x"``, ``null``), else the string itself."""
    try:
        return json.loads(text)
    except ValueError:
        return text


def string_form(value: Any) -> str:
    """The form ``contains`` and ``matches`` read: a string itself, else its JSON."""
    return value if isinstance(value, str) else json.dumps(value, sort_keys=True)


def strict_equal(a: Any, b: Any) -> bool:
    """``==`` of R5: the same type and value at every depth (``True`` is not ``1``, ``1`` is
    not ``1.0``); lists element by element, dicts key by key."""
    if type(a) is not type(b):
        return False
    if isinstance(a, list):
        return len(a) == len(b) and all(strict_equal(x, y) for x, y in zip(a, b, strict=True))
    if isinstance(a, dict):
        return a.keys() == b.keys() and all(strict_equal(a[k], b[k]) for k in a)
    return a == b


def _holds(verb: str, seen: Any, value: str) -> bool:
    if verb == "matches":
        return re.search(value, string_form(seen)) is not None
    expected = parse_value(value)
    if verb == "==":
        return strict_equal(seen, expected)
    if isinstance(seen, list):
        return any(strict_equal(x, expected) for x in seen)
    return string_form(expected) in string_form(seen)


def _proof_target(item: ProofItem, proof_dir: Path) -> tuple[Path | None, str]:
    """The file an item names, kept inside ``proof_dir``, or (None, why)."""
    rel = item.file[len(PROOF_PREFIX) :]
    if ".." in Path(rel).parts:
        return None, f"{item.file} leaves {PROOF_PREFIX}"
    target = Path(proof_dir) / rel
    if linked_part(target) is not None:
        return None, f"{item.file} is reached through a link"
    try:
        target.resolve().relative_to(Path(proof_dir).resolve())
    except ValueError:
        return None, f"{item.file} leaves {PROOF_PREFIX}"
    if not target.is_file():
        return None, f"{item.file} missing"
    return target, ""


def screenshot_outcome(item: ProofItem, proof_dir: Path) -> tuple[str, Any]:
    """(outcome, seen) of a ``screenshot`` item: the file exists under ``proof/`` or not."""
    target, why = _proof_target(item, proof_dir)
    return (OUTCOME_MATCHES, None) if target is not None else (OUTCOME_NOT_PRODUCED, why)


def _json_at(data: Any, dotted: str) -> tuple[bool, Any]:
    for key in dotted.split("."):
        if isinstance(data, dict) and key in data:
            data = data[key]
        elif isinstance(data, list) and key.isdigit() and int(key) < len(data):
            data = data[int(key)]
        else:
            return False, None
    return True, data


def compare_state(item: ProofItem, proof_dir: Path) -> tuple[str, Any]:
    """(outcome, seen) of a ``state`` item against the file it names under ``proof_dir`` (R5):
    ``matches``, ``differs`` with the value seen (the first line for ``line``), or ``not
    produced`` with what was wrong (missing, over 1 MiB, unreadable, empty, not JSON, no such
    key)."""
    target, why = _proof_target(item, proof_dir)
    if target is None:
        return OUTCOME_NOT_PRODUCED, why
    try:
        if target.stat().st_size > STATE_FILE_MAX_BYTES:
            return OUTCOME_NOT_PRODUCED, f"{item.file} is over 1 MiB"
        text = target.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return OUTCOME_NOT_PRODUCED, f"{item.file} unreadable"
    if not text.strip():
        return OUTCOME_NOT_PRODUCED, f"{item.file} is empty"
    try:
        if item.path == PROOF_LINE_PATH:
            lines = text.splitlines()
            if any(_holds(item.verb, parse_value(line.strip()), item.value) for line in lines):
                return OUTCOME_MATCHES, None
            return OUTCOME_DIFFERS, lines[0]
        try:
            data = json.loads(text)
        except ValueError:
            return OUTCOME_NOT_PRODUCED, f"{item.file} is not valid JSON"
        found, seen = _json_at(data, item.path)
        if not found:
            return OUTCOME_NOT_PRODUCED, f"{item.file} has no {item.path}"
        if _holds(item.verb, seen, item.value):
            return OUTCOME_MATCHES, None
        return OUTCOME_DIFFERS, seen
    except re.error as exc:
        return OUTCOME_DIFFERS, f"the pattern does not compile: {exc}"
