"""The decisions ledger of deferred review (decision 21; build guide step 16a; OPERATING_MODEL
sections 3 and 6): what the review panel decided inside a phase, one entry per decision,
kept as evidence with the change and read by the gate and by the PR summary.

Files, under ``changes/<id>-<slug>/evidence/``:

- ``decisions-<phase>.json`` — the record the gate, ``pr/description.py`` and ``/sdlc-fix``
  read: ``{"schema_version": 1, "phase": "b", "decisions": [<entry>, ...]}``;
- ``decisions-<phase>.md`` — the same ledger rendered for a person, one line per decision
  (item, the two verdicts in one clause each, the decision, the rationale, the cost);
- ``panel/<phase>-items.json`` — the items ``panel/cli.py items`` found for the phase;
- ``panel/<phase>-<n>-reviewer.md``, ``-advocate.md``, ``-decision.json`` — what the three
  members wrote for item ``n`` (the conciliator's file is what ``record`` reads).

An entry::

    {"n": 1, "phase": "b", "kind": "concern", "key": "<stable key of the item>",
     "item": "<the item as the owner would read it>",
     "reviewer": "<the reviewer's verdict, one clause>",
     "advocate": "<the devil's advocate's verdict, one clause>",
     "decision": "<one line>", "rationale": ["<at most five lines>"],
     "cost_usd": null, "head": "<sha>", "at": "<ISO-8601 UTC>",
     "overturned": null | {"comment": "<the owner's words>", "at": "<ISO-8601 UTC>"}}

Kinds — the fixed list of what may go to the panel (nothing else ever does):

- ``concern``: an open flagged concern in ``spec.md`` (the decision closes it: the item is
  rewritten to start with ``decided (by panel): <decision> — <original>``);
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
PANEL_CLOSING = "decided (by panel):"  # the closing word first: the gate reads "decided"
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
def panel_closed_concerns(spec_text: str) -> list[str]:
    """The concern items ``apply_decision`` closed (they start with ``decided (by panel):``)."""
    body = art.split_sections(spec_text or "").get(art.CONCERNS_SECTION, "")
    out: list[str] = []
    for line in body.splitlines():
        m = art.CONCERN_ITEM_RE.match(line)
        if m and m.group("text").strip().lower().startswith(PANEL_CLOSING):
            out.append(m.group("text").strip())
    return out


def apply_decision(change_dir: Path, entry: dict[str, Any]) -> bool:
    """Close the concern the entry decides in ``spec.md``: the item is rewritten to
    ``decided (by panel): <decision> — <original text>`` so the gate's ``open_concerns``
    check reads it as closed and the owner sees what was decided and what the concern was.
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
                line = f"{marker}{PANEL_CLOSING} {decision} — {item}"
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
) -> dict[str, Any]:
    rationale = decision.get("rationale")
    if isinstance(rationale, str):
        rationale = [line for line in rationale.splitlines() if line.strip()]
    return {
        "n": n,
        "phase": phase,
        "kind": str(item.get("kind")),
        "key": str(item.get("key")),
        "item": " ".join(str(item.get("item", "")).split()),
        "reviewer": " ".join(str(decision.get("reviewer", "")).split()),
        "advocate": " ".join(str(decision.get("advocate", "")).split()),
        "decision": " ".join(str(decision.get("decision", "")).split()),
        "rationale": [" ".join(str(line).split()) for line in rationale],
        "cost_usd": cost_usd,
        "head": head,
        "at": _now(),
        "overturned": None,
    }
