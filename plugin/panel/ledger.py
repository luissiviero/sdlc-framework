"""The decisions ledger of deferred review (decision 21; build guide step 16a; OPERATING_MODEL
sections 3 and 6): what the review panel decided inside a phase, one entry per decision,
kept as evidence with the change and read by the gate and by the PR summary.

Files, under ``changes/<id>-<slug>/evidence/``:

- ``decisions-<phase>.json`` — the record the gate, ``pr/description.py`` and ``/sdlc-fix``
  read: ``{"schema_version": 1, "phase": "b", "decisions": [<entry>, ...]}``;
- ``decisions-<phase>.md`` — the same ledger rendered for a person, one line per decision
  (item, the two verdicts in one clause each, the decision, the rationale, the cost);
- ``panel/<phase>-items.json`` — the items ``panel/cli.py items`` found for the phase;
- ``panel/<phase>-<n>-reviewer.md``, ``-advocate.md``, ``-conciliator.json`` — what the
  three members wrote for item ``n``. ``record`` reads the conciliator's decision and takes
  the two verdicts from the members' own files (``## Verdict``), never from the
  conciliator's restatement; it refuses an item whose two blind verdicts are not both there
  (0.2.30), and the gate's ``panel`` check re-checks that for every ledger line.

An entry::

    {"n": 1, "phase": "b", "kind": "concern", "key": "<stable key of the item>",
     "item": "<the item as the owner would read it>",
     "reviewer": "<the reviewer's verdict, one clause>",
     "advocate": "<the devil's advocate's verdict, one clause>",
     "decision": "<one line>", "rationale": ["<at most five lines>"],
     "cost_usd": null, "head": "<sha>", "at": "<ISO-8601 UTC>",
     "overturned": null | {"comment": "<the owner's words>", "at": "<ISO-8601 UTC>"},
     "item_n": 1}

``item_n`` (since 0.2.30) is the item's number, which names the members' files; a line
written before 0.2.30 has none.

Kinds — the fixed list of what may go to the panel (nothing else ever does):

- ``concern``: an open flagged concern in ``spec.md`` (the decision closes it: the item is
  rewritten to start with ``decided (by panel #<n>): <decision> — <original>``, ``n`` the
  ledger line, which is what the gate matches — the wording after it may be tidied);
- ``policy``: a concern that names contradicting policy skills (closed the same way);
- ``escalate``: an ``escalate`` verdict of the adversarial reviewer (keyed by its reasons;
  the gate's ``adversarial_review`` check reads the entry);
- ``finding``: an Important review finding whose fix the run cannot determine (keyed by
  the finding's signature; the gate's ``findings`` check reads the entry);
- ``verifier``: the verifier's "does not match the plan" (a record; the run acts on it).

What never goes to the panel and still parks (``NEVER_TO_PANEL``): a risk-list hit, a
guardrail file change, a run limit, an infrastructure failure, any merge to ``main``, any
deploy. The gate's ``panel`` check refuses a ledger that names one.

Pure module: no network, no git; ``apply_decision`` edits ``spec.md`` and nothing else.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PLUGIN_DIR = Path(__file__).resolve().parent.parent
if str(PLUGIN_DIR) not in sys.path:
    sys.path.insert(0, str(PLUGIN_DIR))

from gate import artifacts as art  # noqa: E402

SCHEMA_VERSION = 1
LEDGER_JSON = "decisions-{phase}.json"
LEDGER_MD = "decisions-{phase}.md"
PANEL_DIR = "panel"
ITEMS_FILE = "{phase}-items.json"
MEMBER_FILE = "{phase}-{n}-{member}.{ext}"
MEMBERS = ("reviewer", "advocate", "conciliator")

PANEL_KINDS = ("concern", "policy", "escalate", "finding", "verifier")
# the gate checks whose failure is never the panel's to settle (OPERATING_MODEL section 6)
NEVER_TO_PANEL = (
    "risk_list",
    "guardrails",
    "limits",
    "commands",
    "evidence",
    "clean_tree",
    "artifacts",
    "plan_sync",
    "design_scope",
    "owner_actions",
    "panel",
)
RATIONALE_MAX_LINES = 5
# The closing word first: the gate's ``open_concerns`` check reads "decided". ``#<n>`` names
# the ledger line (0.2.15); the form without it is what 0.2.14 wrote and is still read.
PANEL_CLOSING = "decided (by panel):"
PANEL_CLOSING_RE = re.compile(r"(?i)^decided \(by panel(?: #(?P<n>\d+))?\):\s*")
POLICY_RE = re.compile(
    r"(?i)\b(contradict\w*|conflict\w*)\b.*\b(polic\w*|skill\w*)\b|\bpolic\w*.*\b(contradict\w*|conflict\w*)\b"
)
VERIFIER_MISMATCH_RE = re.compile(
    r"(?im)^\s*[-*]?\s*\**verdict\**\s*[:—-]\s*`?does not match the plan`?"
)


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _key(*parts: str) -> str:
    return hashlib.sha1("|".join(parts).encode("utf-8")).hexdigest()[:16]  # noqa: S324


def concern_key(text: str) -> str:
    """A concern's stable key: its text without the list marker, whitespace collapsed."""
    text = re.sub(r"^\s*(?:[-*]|\d+[.)])\s+", "", text.strip())
    return "concern:" + _key(" ".join(text.split()).lower())


def escalate_key(reasons: list[str]) -> str:
    """An escalate verdict's key: its reasons, order-independent. A later verdict with new
    reasons is a new item; the same reasons again are the item already decided."""
    return "escalate:" + _key(*sorted(" ".join(str(r).split()).lower() for r in reasons))


def finding_key(signature: str) -> str:
    return f"finding:{signature}"


VERIFIER_KEY = "verifier:mismatch"


def kind_of_concern(text: str) -> str:
    return "policy" if POLICY_RE.search(text) else "concern"


def closing_marker(n: int) -> str:
    return f"decided (by panel #{int(n)}):"


def _norm(text: str) -> str:
    """Words only, for the item-text match: the conciliator restates the item without its
    backticks or quotes."""
    return " ".join(re.sub(r"[`*_\"']", "", str(text or "")).split()).lower()


def clean_decision(decision: str, item: str) -> str:
    """The conciliator's decision line as the run applies it: one line, without a closing
    prefix it copied from the brief and without the item's text appended after an em dash
    (the first deferred run, sample change 0002, wrote ``decided (by panel): X — <the
    concern>`` into ``decision`` and the spec read ``decided (by panel): decided (by panel):
    X — ... — ...``). The item's text is recognised by its first forty characters."""
    text = " ".join(str(decision or "").split())
    while True:
        m = PANEL_CLOSING_RE.match(text)
        if not m:
            break
        text = text[m.end() :].strip()
    item_head = _norm(item)[:40]
    while " — " in text:
        head, _sep, tail = text.rpartition(" — ")
        tail_norm = _norm(tail)
        if item_head and (
            tail_norm.startswith(item_head)
            or (len(tail_norm) >= 20 and item_head.startswith(tail_norm))
        ):
            text = head.strip()
            continue
        break
    return text


LEDGER_PHASES = ("b", "c", "d", "e")


def phases_up_to(phase: str) -> tuple[str, ...]:
    """The phases whose ledgers a gate at ``phase`` reads for the closings in ``spec.md``:
    a concern closed by the panel at (b) stays closed through (c), (d) and (e), and its
    ledger line lives in ``decisions-b.json`` (the first build under deferred review, sample
    change 0002, 2026-09-24, parked at gate (c) on "closed with no ledger line" because the
    check read the phase's own ledger only)."""
    if phase not in LEDGER_PHASES:
        return ()
    return LEDGER_PHASES[: LEDGER_PHASES.index(phase) + 1]


# --- paths --------------------------------------------------------------------------------------
def ledger_path(change_dir: Path, phase: str) -> Path:
    return Path(change_dir) / art.EVIDENCE_DIR / LEDGER_JSON.format(phase=phase)


def ledger_md_path(change_dir: Path, phase: str) -> Path:
    return Path(change_dir) / art.EVIDENCE_DIR / LEDGER_MD.format(phase=phase)


def items_path(change_dir: Path, phase: str) -> Path:
    return Path(change_dir) / art.EVIDENCE_DIR / PANEL_DIR / ITEMS_FILE.format(phase=phase)


def member_path(change_dir: Path, phase: str, n: int, member: str) -> Path:
    ext = "json" if member == "conciliator" else "md"
    name = MEMBER_FILE.format(phase=phase, n=n, member=member, ext=ext)
    return Path(change_dir) / art.EVIDENCE_DIR / PANEL_DIR / name


BLIND_MEMBERS = ("reviewer", "advocate")
VERDICT_HEADING_RE = re.compile(r"^##\s+Verdict\s*$", re.IGNORECASE)


def verdict_clause(text: str | None) -> str | None:
    """The verdict a member wrote: the first paragraph under ``## Verdict``, on one line.
    None when there is no such heading, the paragraph is empty, or it is still the brief's
    ``<placeholder>``."""
    if not text:
        return None
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if not VERDICT_HEADING_RE.match(line.strip()):
            continue
        paragraph: list[str] = []
        for following in lines[i + 1 :]:
            stripped = following.strip()
            if stripped.startswith("#") or (not stripped and paragraph):
                break
            if stripped:
                paragraph.append(stripped)
        clause = " ".join(" ".join(paragraph).split())
        if not clause or (clause.startswith("<") and clause.endswith(">")):
            return None
        return clause
    return None


def member_verdicts(
    texts: dict[str, str | None], phase: str, n: int
) -> tuple[dict[str, str], list[str]]:
    """The two blind verdicts of item ``n`` from the members' file texts (``texts[member]``
    is None when the file is missing), and what is wrong when one is absent."""
    verdicts: dict[str, str] = {}
    problems: list[str] = []
    for member in BLIND_MEMBERS:
        name = MEMBER_FILE.format(phase=phase, n=n, member=member, ext="md")
        text = texts.get(member)
        if text is None:
            problems.append(f"panel/{name} is missing: the {member} has not written its verdict")
            continue
        clause = verdict_clause(text)
        if clause is None:
            problems.append(f"panel/{name} has no '## Verdict' clause")
        else:
            verdicts[member] = clause
    return verdicts, problems


ADVOCATE_MODEL_FILE = "{phase}-{n}-advocate.model.json"
ADVOCATE_AGENT = "adversarial-reviewer"  # the plugin agent ``sdlc:adversarial-reviewer``


def advocate_model_path(change_dir: Path, phase: str, n: int) -> Path:
    name = ADVOCATE_MODEL_FILE.format(phase=phase, n=n)
    return Path(change_dir) / art.EVIDENCE_DIR / PANEL_DIR / name


def advocate_model_problems(text: str | None, wanted: str | None, phase: str, n: int) -> list[str]:
    """What is wrong with the record of which model wrote the advocate's verdict (written by
    the ``panel_blind`` hook, 0.2.30): it must exist, name the devil's advocate as the writer
    and, when ``sdlc.yaml: panel_advocate_model`` is set, a model that satisfies it."""
    name = f"panel/{ADVOCATE_MODEL_FILE.format(phase=phase, n=n)}"
    if text is None:
        return [
            f"{name} is missing: nothing shows which model wrote the devil's advocate's "
            "verdict (the panel_blind hook writes it when the advocate writes its file)"
        ]
    try:
        record = json.loads(text)
    except ValueError:
        return [f"{name} is unreadable"]
    if not isinstance(record, dict):
        return [f"{name} is not a JSON object"]
    agent = str(record.get("agent_type") or "")
    if agent.rsplit(":", 1)[-1] != ADVOCATE_AGENT:
        writer = agent or "the main session"
        return [f"{name}: the advocate's verdict was written by {writer}, not by the devil's "
                f"advocate (sdlc:{ADVOCATE_AGENT})"]  # fmt: skip
    models = [str(m) for m in record.get("models") or [] if str(m).strip()]
    if not models:
        why = record.get("reason") or "no model recorded"
        return [f"{name}: the advocate's model is unproved ({why})"]
    alias = str(wanted or "").strip()
    if alias and not any(model_matches(alias, m) for m in models):
        return [f"{name}: the devil's advocate ran on {', '.join(models)}, not on {alias} "
                "(sdlc.yaml: panel_advocate_model)"]  # fmt: skip
    return []


def read_member_verdicts(change_dir: Path, phase: str, n: int) -> tuple[dict[str, str], list[str]]:
    """``member_verdicts`` over the files in the working tree."""
    texts = {
        member: art.read_text(member_path(change_dir, phase, n, member)) for member in BLIND_MEMBERS
    }
    return member_verdicts(texts, phase, n)


# --- the ledger ---------------------------------------------------------------------------------
def load_ledger(change_dir: Path, phase: str) -> list[dict[str, Any]]:
    """The entries of the phase's ledger, [] when there is none or it is unreadable (the gate's
    ``panel`` check reports an unreadable one; a reader that only lists is not the judge)."""
    path = ledger_path(change_dir, phase)
    if not path.is_file():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    entries = data.get("decisions") if isinstance(data, dict) else None
    return [e for e in entries if isinstance(e, dict)] if isinstance(entries, list) else []


def load_ledgers(change_dir: Path, phase: str) -> list[tuple[str, list[dict[str, Any]]]]:
    """``(phase, entries)`` for every phase up to and including ``phase`` (``phases_up_to``)."""
    return [(ph, load_ledger(change_dir, ph)) for ph in phases_up_to(phase)]


def ledger_error(change_dir: Path, phase: str) -> str | None:
    """Why the ledger file cannot be read, or None (also None when there is no file)."""
    path = ledger_path(change_dir, phase)
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return f"evidence/{path.name} is unreadable: {exc}"
    if not isinstance(data, dict) or not isinstance(data.get("decisions"), list):
        return f"evidence/{path.name} is not a ledger (no 'decisions' list)"
    return None


def save_ledger(change_dir: Path, phase: str, entries: list[dict[str, Any]]) -> Path:
    path = ledger_path(change_dir, phase)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {"schema_version": SCHEMA_VERSION, "phase": phase, "decisions": entries}
    path.write_text(
        json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n"
    )
    ledger_md_path(change_dir, phase).write_text(
        render_md(phase, entries), encoding="utf-8", newline="\n"
    )
    return path


def active(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """The decisions that still stand (not overturned by a review comment)."""
    return [e for e in entries if not e.get("overturned")]


def decided_keys(entries: list[dict[str, Any]]) -> set[str]:
    return {str(e.get("key", "")) for e in active(entries)}


def total_cost(entries: list[dict[str, Any]]) -> float:
    total = 0.0
    for e in entries:
        cost = e.get("cost_usd")
        if isinstance(cost, (int, float)) and not isinstance(cost, bool):
            total += float(cost)
    return round(total, 4)


def validate_entry(entry: dict[str, Any]) -> list[str]:
    """Everything wrong with one ledger entry (the gate's ``panel`` check reports them)."""
    problems: list[str] = []
    n = entry.get("n")
    if isinstance(n, bool) or not isinstance(n, int) or n < 1:
        problems.append("n must be a positive integer")
    kind = entry.get("kind")
    if kind not in PANEL_KINDS:
        problems.append(f"kind {kind!r} is not one of the panel's ({', '.join(PANEL_KINDS)})")
    for field in ("key", "item", "reviewer", "advocate", "decision", "head", "at"):
        value = entry.get(field)
        if not isinstance(value, str) or not value.strip():
            problems.append(f"'{field}' is missing")
    rationale = entry.get("rationale")
    if not isinstance(rationale, list) or not rationale:
        problems.append("'rationale' must be a non-empty list of lines")
    elif len(rationale) > RATIONALE_MAX_LINES:
        problems.append(f"'rationale' has {len(rationale)} lines; at most {RATIONALE_MAX_LINES}")
    elif not all(isinstance(line, str) and line.strip() for line in rationale):
        problems.append("'rationale' must be non-empty strings")
    decision = str(entry.get("decision") or "")
    if "\n" in decision.strip():
        problems.append("'decision' must be one line")
    cost = entry.get("cost_usd")
    if cost is not None and (isinstance(cost, bool) or not isinstance(cost, (int, float))):
        problems.append("'cost_usd' must be a number or null")
    overturned = entry.get("overturned")
    if overturned is not None and not isinstance(overturned, dict):
        problems.append("'overturned' must be null or an object")
    return [f"decision {n}: {p}" if isinstance(n, int) else p for p in problems]


def validate_decision_file(data: Any) -> list[str]:
    """What the conciliator must have written: decision, rationale (<= 5 lines), the two
    verdicts in one clause each."""
    if not isinstance(data, dict):
        return ["the decision file is not a JSON object"]
    problems: list[str] = []
    for field in ("reviewer", "advocate", "decision"):
        value = data.get(field)
        if not isinstance(value, str) or not value.strip():
            problems.append(f"'{field}' is missing")
    if "\n" in str(data.get("decision") or "").strip():
        problems.append("'decision' must be one line")
    rationale = data.get("rationale")
    if isinstance(rationale, str):
        rationale = [line for line in rationale.splitlines() if line.strip()]
    if not isinstance(rationale, list) or not rationale:
        problems.append("'rationale' must be a non-empty list of lines")
    elif len(rationale) > RATIONALE_MAX_LINES:
        problems.append(f"'rationale' has {len(rationale)} lines; at most {RATIONALE_MAX_LINES}")
    return problems


def render_md(phase: str, entries: list[dict[str, Any]]) -> str:
    """The ledger for a person: one line per decision, in the order they were taken."""
    lines = [
        f"# Decisions taken for you — phase ({phase})",
        "",
        "One line per panel decision (decision 21): the item, the reviewer's and the devil's "
        "advocate's verdicts, the conciliator's decision and rationale, the cost. A review "
        "comment on any of them overturns it (/sdlc-fix); an overturned line says so.",
        "",
    ]
    if not entries:
        lines.append("- none")
    for e in entries:
        rationale = " ".join(str(line).strip() for line in e.get("rationale") or [])
        cost = e.get("cost_usd")
        cost_text = f"${float(cost):.2f}" if isinstance(cost, (int, float)) else "n/a"
        line = (
            f"- {e.get('n')}. [{e.get('kind')}] {e.get('item')} — reviewer: {e.get('reviewer')}; "
            f"devil's advocate: {e.get('advocate')}; decision: {e.get('decision')}; "
            f"rationale: {rationale}; cost: {cost_text}"
        )
        overturned = e.get("overturned")
        if isinstance(overturned, dict):
            line += f" — OVERTURNED by the owner's review comment: {overturned.get('comment', '')}"
        lines.append(" ".join(line.split()))
    lines += ["", f"Total panel cost: ${total_cost(entries):.2f}"]
    return "\n".join(lines) + "\n"


# --- applying a decision to spec.md ---------------------------------------------------------
def panel_closings(spec_text: str) -> list[tuple[int | None, str]]:
    """The concern items ``apply_decision`` closed: ``(n, text)`` per item, ``n`` the ledger
    line the closing names (``decided (by panel #n):``) or None for the 0.2.14 form."""
    body = art.split_sections(spec_text or "").get(art.CONCERNS_SECTION, "")
    out: list[tuple[int | None, str]] = []
    for line in body.splitlines():
        m = art.CONCERN_ITEM_RE.match(line)
        if not m:
            continue
        text = m.group("text").strip()
        closing = PANEL_CLOSING_RE.match(text)
        if closing:
            n = closing.group("n")
            out.append((int(n) if n else None, text))
    return out


def panel_closed_concerns(spec_text: str) -> list[str]:
    """The concern items ``apply_decision`` closed, as text."""
    return [text for _n, text in panel_closings(spec_text)]


def apply_decision(change_dir: Path, entry: dict[str, Any]) -> bool:
    """Close the concern the entry decides in ``spec.md``: the item is rewritten to
    ``decided (by panel #<n>): <decision> — <original text>`` so the gate's ``open_concerns``
    check reads it as closed, the ``panel`` check finds the ledger line by ``n`` however the
    words are tidied later, and the owner sees what was decided and what the concern was.
    True when an open item with the entry's key was found and rewritten; False otherwise
    (the entry is for another kind, or the concern is already closed)."""
    if entry.get("kind") not in ("concern", "policy"):
        return False
    spec_path = Path(change_dir) / "spec.md"
    text = art.read_text(spec_path)
    if text is None:
        return False
    sections = art.split_sections(text)
    if art.CONCERNS_SECTION not in sections:
        return False
    out: list[str] = []
    done = False
    in_section = False
    for line in text.splitlines():
        if line.startswith("## "):
            in_section = line.strip() == art.CONCERNS_SECTION
        m = art.CONCERN_ITEM_RE.match(line) if in_section and not done else None
        if m:
            item = m.group("text").strip()
            is_open = not art.NO_CONCERN_RE.match(item) and not art.CLOSED_CONCERN_RE.match(item)
            if is_open and concern_key(item) == entry.get("key"):
                marker = line[: line.index(m.group("text"))]
                decision = " ".join(str(entry.get("decision", "")).split())
                line = f"{marker}{closing_marker(int(entry.get('n', 0)))} {decision} — {item}"
                done = True
        out.append(line)
    if done:
        body = "\n".join(out) + ("\n" if text.endswith("\n") else "")
        spec_path.write_text(body, encoding="utf-8", newline="\n")
    return done


def verifier_disagrees(verifier_text: str | None) -> bool:
    """``evidence/verifier.md`` ends its report with ``Verdict — does not match the plan``."""
    return bool(verifier_text) and VERIFIER_MISMATCH_RE.search(verifier_text) is not None


def new_entry(
    n: int,
    phase: str,
    item: dict[str, Any],
    decision: dict[str, Any],
    head: str,
    cost_usd: float | None,
    verdicts: dict[str, str] | None = None,
) -> dict[str, Any]:
    """One ledger line. ``verdicts`` are the two blind verdicts read from the members' own
    files (``read_member_verdicts``); without them the conciliator's restatement is used, as
    before 0.2.30. ``item_n`` is the item's number, which names the members' files: the
    gate's ``panel`` check finds them by it (a line written before 0.2.30 has none)."""
    rationale = decision.get("rationale")
    if isinstance(rationale, str):
        rationale = [line for line in rationale.splitlines() if line.strip()]
    verdicts = verdicts or {}
    entry: dict[str, Any] = {
        "n": n,
        "phase": phase,
        "kind": str(item.get("kind")),
        "key": str(item.get("key")),
        "item": " ".join(str(item.get("item", "")).split()),
        "reviewer": " ".join(str(verdicts.get("reviewer") or decision.get("reviewer", "")).split()),
        "advocate": " ".join(str(verdicts.get("advocate") or decision.get("advocate", "")).split()),
        "decision": clean_decision(str(decision.get("decision", "")), str(item.get("item", ""))),
        "rationale": [" ".join(str(line).split()) for line in rationale],
        "cost_usd": cost_usd,
        "head": head,
        "at": _now(),
        "overturned": None,
    }
    item_n = item.get("n")
    if isinstance(item_n, int) and not isinstance(item_n, bool):
        entry["item_n"] = item_n
    return entry


# --- the models a run's panel ran on (0.2.30) ---------------------------------------------------
# The devil's advocate runs on ``sdlc.yaml: panel_advocate_model`` (decision 21: a panel on one
# model shares its blind spots). A phase run in CI ends with ``claude -p --output-format json``,
# whose ``modelUsage`` names every model the session and its sub-agents used (the sample's
# change 0002: the phases with panel decisions list ``claude-opus-5`` beside the session's
# ``claude-sonnet-5``, the others the session's model only). ``run_phase.py`` checks it after a
# run that added panel decisions and keeps the result here; the PR summary shows it.
MODELS_FILE = "panel-models-{phase}.json"
MODEL_FAMILIES = ("opus", "sonnet", "haiku", "fable")


def models_path(change_dir: Path, phase: str) -> Path:
    return Path(change_dir) / art.EVIDENCE_DIR / MODELS_FILE.format(phase=phase)


def model_matches(wanted: str, model: str) -> bool:
    """Does ``model`` (an id from ``modelUsage``, e.g. ``claude-opus-5``) satisfy ``wanted``
    (an alias, ``opus``, or a full id)? A context suffix (``opus[1m]``) is ignored."""
    want = str(wanted).strip().lower().split("[", 1)[0]
    have = str(model).strip().lower().split("[", 1)[0]
    if not want or not have:
        return False
    if want in MODEL_FAMILIES:
        return want in have.replace("_", "-").split("-")
    return have == want or have.startswith(want) or want.startswith(have)


def session_model(model_usage: dict[str, Any], env_model: str | None) -> tuple[str | None, str]:
    """The session's own model: ``SDLC_MODEL`` when the workflow set it (it is passed as
    ``--model``), else the model with the largest output, which is the session's in every
    run read so far (the panel's members write a few files; the session writes the rest)."""
    if env_model:
        return env_model, "SDLC_MODEL"
    best, most = None, -1
    for model, usage in model_usage.items():
        out = usage.get("outputTokens") if isinstance(usage, dict) else None
        count = out if isinstance(out, int) and not isinstance(out, bool) else 0
        if count > most:
            best, most = model, count
    return best, "the largest output in modelUsage"


def check_models(
    new_decisions: int, result: Any, advocate_model: str | None, env_model: str | None
) -> dict[str, Any] | None:
    """The record of which models a run's panel ran on, or None when the run added no
    panel decision. ``ok`` is False when no model of the run satisfies the advocate's
    model: the advocate did not run where decision 21 puts it. ``warning`` says when the
    session already runs on that model, so the panel had no second model (advice only)."""
    if new_decisions <= 0:
        return None
    usage = result.get("modelUsage") if isinstance(result, dict) else None
    usage = usage if isinstance(usage, dict) else {}
    models = sorted(str(m) for m in usage)
    session, source = session_model(usage, env_model)
    alias = str(advocate_model or "").strip()
    record: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "new_decisions": new_decisions,
        "advocate_model": alias or None,
        "models": models,
        "session_model": session,
        "session_model_source": source,
        "ok": True,
        "reason": None,
        "warning": None,
    }
    if not alias:
        record["warning"] = (
            "sdlc.yaml names no panel_advocate_model, so the devil's advocate ran on the "
            "session's model"
        )
        return record
    if not models:
        record.update(ok=False, reason="the run reported no models (no modelUsage)")
    elif not any(model_matches(alias, m) for m in models):
        record.update(
            ok=False,
            reason=(
                f"no model of this run is {alias} (it used {', '.join(models)}): the devil's "
                "advocate did not run on sdlc.yaml's panel_advocate_model"
            ),
        )
    elif session and model_matches(alias, session):
        record["warning"] = (
            f"the session itself runs on {session}, the advocate's model ({alias}), so the "
            "panel had no second model"
        )
    return record


def save_models(change_dir: Path, phase: str, record: dict[str, Any]) -> Path:
    path = models_path(change_dir, phase)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n"
    )
    return path


def load_models(change_dir: Path, phase: str) -> dict[str, Any] | None:
    try:
        data = json.loads(models_path(change_dir, phase).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) else None
