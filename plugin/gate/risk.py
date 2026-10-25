"""The risk list after decision 35 (ROADMAP R24): a hit is a line in the close-look banner.

A risk-list hit no longer parks the change. The gate's ``risk_list`` check (and ``ratchets``,
whose undeclared drop is a hit named after the ratchet, R15) reports the hits in its record;
the gate's reviewer writes a short brief per hit item; the PR the owner merges anyway shows
both in its "Needs your close look" banner; the owner's merge is the acceptance (at (deploy), the
owner's approving review, decision 36), which the runner records in
``status.yaml: risk_acceptances``. What still parks is the reviewer's
escalation on a risk item: it never goes to the review panel (decisions 11 and 21 as 35
amends them).

This module holds the parts the gate, the PR description, the runner and the release share:

- **the items** (``parse_items``): an item of ``sdlc.yaml: risk_list`` is a plain string,
  matched by its words in the committed diff's paths and in spec.md's "Flagged concerns"
  as before, or a mapping ``{item: <words>, paths: [<glob>, ...]}``, whose globs are matched
  on the committed diff and whose words are matched in "Flagged concerns" only. A glob never
  matches under ``changes/``, and neither do a plain item's words: a change's own folder is
  not a risk (a slug such as ``0007-auth-login`` hit the word match before 1.0.15);
- **the brief** (``brief_path``, ``parse_brief``): ``evidence/roles/security-policy-<phase>.md``,
  the file the Security & policy role owns once R28 builds it, written until then by the
  adversarial reviewer at design to test and by the REVIEW.md pass at (deploy): one ``## <item>``
  section per hit item, with the reviewer's word on it and what the change does to it, what
  could break and how to undo it;
- **the escalation** (``escalated_items``): the brief's word ``escalate`` on a hit item, or an
  ``escalate`` verdict whose reasons name a hit item;
- **the banner** (``banner_entries``, ``banner_lines``, ``banner_shown``) and **the
  acceptance record** (``accepted``, ``acceptance_line``, ``record_acceptance``).

Pure but for reading files: no git, no network.
"""

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

PLUGIN_DIR = Path(__file__).resolve().parent.parent
if str(PLUGIN_DIR) not in sys.path:
    sys.path.insert(0, str(PLUGIN_DIR))

from gate import artifacts as art  # noqa: E402
from hooks._common import matches  # noqa: E402
from state import conventions as c  # noqa: E402

# the gate checks whose ``details.hits`` are risk-list hits (R15: a dropped test file or eval
# case is one, named after its ratchet)
RISK_HIT_CHECKS = ("risk_list", "ratchets")
CHANGES_PREFIX = "changes/"
BRIEF_DIR = "roles"
BRIEF_FILE = "security-policy-{phase}.md"
BRIEF_FIELDS = ("What the change does to it", "What could break", "How to undo it")
WORDS = ("continue", "escalate")
BANNER_HEADING = "**Needs your close look**"
ACCEPT_ACT = "risk accepted"
ACCEPT_VIA = "merge"
# R22 (choice 242, point 2): at (deploy) the owner's approving review accepts, the merge App never
ACCEPT_VIA_APPROVAL = "approval"
ACCEPT_VIAS = (ACCEPT_VIA, ACCEPT_VIA_APPROVAL)
# the gates whose PR shows the banner, and the earlier gates whose records it reads: the
# design PR at design; the build PR at build, test and deploy, one PR from build to merge; the
# install PR of change 0000 at (intent), whose merge also confirms the globs
BANNER_PHASES = {
    c.INTENT: (c.INTENT,),
    c.DESIGN: (c.DESIGN,),
    c.BUILD: (c.BUILD,),
    c.TEST: (c.BUILD, c.TEST),
    c.DEPLOY: (c.BUILD, c.TEST, c.DEPLOY),
}
BANNER_ASK = {
    c.INTENT: "Merging this PR accepts them for this change and confirms the risk list's globs "
    "(decision 35).",
    c.DESIGN: "Merging this PR accepts them for this change, recorded in status.yaml with your "
    "name (decision 35); a review comment or Request changes stops it here.",
    c.BUILD: "Only your approval at gate (deploy) accepts them (R12's third point); Request "
    "changes stops the change here.",
    c.TEST: "Only your approval at gate (deploy) accepts them (R12's third point); Request "
    "changes stops the change here.",
    c.DEPLOY: "Your approving review accepts them for this change (your merge, when you merge it "
    "yourself), recorded in status.yaml with your name (decisions 35 and 36).",
}


@dataclass(frozen=True)
class RiskItem:
    name: str
    paths: tuple[str, ...] = ()  # empty: a plain-string item, its words matched on paths


def parse_items(value: Any) -> tuple[list[RiskItem], str]:
    """``sdlc.yaml: risk_list`` as items, or ([], why) when it is not a list of strings and
    ``{item, paths}`` mappings. A mapping without ``paths`` (or with an empty list) is read as
    the plain string it names."""
    if value is None:
        return [], ""
    if not isinstance(value, list):
        return [], "sdlc.yaml: risk_list must be a list"
    items: list[RiskItem] = []
    for entry in value:
        if isinstance(entry, dict):
            name = str(entry.get("item") or "").strip()
            paths = entry.get("paths") or []
            unknown = sorted(set(entry) - {"item", "paths"})
            if not name or unknown or not isinstance(paths, list):
                return [], (
                    "sdlc.yaml: a risk_list mapping is {item: <words>, paths: [<glob>, ...]}"
                    + (f"; unknown key(s): {', '.join(unknown)}" if unknown else "")
                )
            globs = tuple(str(p).strip() for p in paths if str(p).strip())
            items.append(RiskItem(name, globs))
        elif str(entry).strip():
            items.append(RiskItem(str(entry).strip()))
    return items, ""


# --- matching -----------------------------------------------------------------------------------
def _tokens(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


def _tok_eq(a: str, b: str) -> bool:
    return a == b or a == b + "s" or b == a + "s"


def phrase_in(text: str, words: str) -> bool:
    """Whether ``words`` occur in ``text`` as whole tokens, plural-tolerant: 'auth' matches
    'auth/' and 'auth_token' but not 'author'."""
    tokens, phrase = _tokens(text), _tokens(words)
    n = len(phrase)
    if not n:
        return False
    return any(
        all(_tok_eq(tokens[i + j], phrase[j]) for j in range(n)) for i in range(len(tokens) - n + 1)
    )


def hits(
    items: list[RiskItem | str | dict[str, Any]], paths: list[str], texts: dict[str, str]
) -> dict[str, list[str]]:
    """``{item: [where it matched]}``. A plain item's words are matched on ``paths`` and in
    ``texts``; an item with globs has them matched on ``paths`` and its words in ``texts``
    only. No path under ``changes/`` is matched: the change's own folder is not a risk, and
    its spec's "Flagged concerns" come in through ``texts``."""
    found: dict[str, list[str]] = {}
    outside = [p for p in paths if not p.startswith(CHANGES_PREFIX)]
    for raw in items:
        item = _as_item(raw)
        if item is None:
            continue
        if item.paths:
            where = [p for p in outside if any(matches(g, p) for g in item.paths)]
        else:
            where = [p for p in outside if phrase_in(p, item.name)]
        where += [f"{name}: text" for name, text in texts.items() if phrase_in(text, item.name)]
        if where:
            found[item.name] = where
    return found


def _as_item(raw: RiskItem | str | dict[str, Any]) -> RiskItem | None:
    if isinstance(raw, RiskItem):
        return raw
    parsed, _why = parse_items([raw])
    return parsed[0] if parsed else None


# --- the brief per hit item ---------------------------------------------------------------------
def brief_path(change_dir: Path, phase: str) -> Path:
    """The brief of ``phase``'s gate to read: ``security-policy-<name>.md``, or the letter's
    an older plugin's reviewer wrote (``security-policy-c.md``) when only that exists (R45)."""
    return c.phase_file(Path(change_dir) / art.EVIDENCE_DIR / BRIEF_DIR, BRIEF_FILE, phase)


def brief_rel(phase: str) -> str:
    """Where the reviewer writes the brief: always under the phase's name (R45)."""
    name = BRIEF_FILE.format(phase=c.phase_name(phase))
    return f"{art.EVIDENCE_DIR}/{BRIEF_DIR}/{name}"


_FIELD_RE = re.compile(r"^\s*[-*]\s*\**(?P<key>[^:*]+?)\**\s*:\s*(?P<value>.*)$")


def parse_brief(text: str | None) -> dict[str, dict[str, str]]:
    """``{item lowercased: {"item", "word", <field>: <text>}}`` from a brief file: one ``## ``
    section per item, its lines ``- Word: continue|escalate`` and ``- <field>: <text>``
    (``BRIEF_FIELDS``). A section without a valid word reads as ``continue``; a missing
    field is absent. Unreadable or empty text gives {}."""
    out: dict[str, dict[str, str]] = {}
    for heading, body in art.split_sections(text or "").items():
        if not heading.startswith("## "):
            continue
        name = heading[3:].strip().strip("`").strip()
        if not name:
            continue
        entry: dict[str, str] = {"item": name, "word": "continue"}
        for line in body.splitlines():
            m = _FIELD_RE.match(line)
            if not m:
                continue
            key, value = m.group("key").strip(), m.group("value").strip()
            if key.lower() == "word":
                word = value.strip("`*").strip().lower()
                entry["word"] = word if word in WORDS else "continue"
            else:
                for field_name in BRIEF_FIELDS:
                    if key.lower() == field_name.lower() and value:
                        entry[field_name] = value
        out[name.lower()] = entry
    return out


def read_brief(change_dir: Path, phase: str) -> dict[str, dict[str, str]]:
    return parse_brief(art.read_text(brief_path(change_dir, phase)))


def escalated_items(
    hit_items: list[str], brief: dict[str, dict[str, str]], verdict: dict[str, Any] | None
) -> list[str]:
    """The hit items the gate's reviewer escalates on: the brief's word ``escalate`` on the
    item, or an ``escalate`` verdict of the adversarial reviewer whose reasons name it (its
    words, as the item match reads them)."""
    reasons: list[str] = []
    if isinstance(verdict, dict) and verdict.get("verdict") == "escalate":
        reasons = [str(r) for r in verdict.get("reasons") or []]
    out = []
    for item in hit_items:
        entry = brief.get(item.lower())
        if (entry and entry.get("word") == "escalate") or any(phrase_in(r, item) for r in reasons):
            out.append(item)
    return out


# --- what was accepted --------------------------------------------------------------------------
def accepted(st: Any) -> dict[str, str]:
    """``{item lowercased: how it was accepted}``: the items accepted by hand
    (``state/cli.py accept-risk``, or an ``sdlc:accept-risk`` label before 1.0.15) and the
    items of a ``risk_acceptances`` line whose banner was shown (an acceptance the owner
    could not have read is no acceptance)."""
    out: dict[str, str] = {}
    by_label = {
        str(e.get("item", "")).strip().lower(): str(e.get("actor", "")).strip()
        for e in getattr(st, "risk_accepted_by", None) or []
        if isinstance(e, dict)
    }
    for item in getattr(st, "risk_accepted", None) or []:
        key = str(item).strip().lower()
        if key:
            actor = by_label.get(key)
            out[key] = f"accepted by @{actor}" if actor else "accepted by hand"
    for line in getattr(st, "risk_acceptances", None) or []:
        details = line.get("details") if isinstance(line, dict) else None
        if not isinstance(details, dict) or details.get("banner_shown") is not True:
            continue
        when = str(line.get("at") or "")[:10]
        how = f"accepted at gate ({c.phase_name(details.get('phase'))}) by @{line.get('by')}"
        how += f" on {when}" if when else ""
        for item in details.get("items") or []:
            out.setdefault(str(item).strip().lower(), how)
    return out


def acceptance_line(
    phase: str,
    items: list[str],
    by: str,
    at: str,
    pr: int,
    head: str | None,
    banner_shown: bool,
    via: str = ACCEPT_VIA,
) -> dict[str, Any]:
    """One ``status.yaml: risk_acceptances`` line, in the shape of R11's approvals list
    (``act``, ``by``, ``at``, ``via``, ``pr``, ``head``, ``details``), so R11 can take it in.
    ``via`` is ``merge`` (the owner's merge) or, at (deploy) since R22, ``approval`` (the owner's
    approving review, on which the merge App merged; ``head`` is then the approved commit)."""
    if via not in ACCEPT_VIAS:
        raise ValueError(f"via must be one of {', '.join(ACCEPT_VIAS)}")
    return {
        "act": ACCEPT_ACT,
        "by": by,
        "at": at,
        "via": via,
        "pr": int(pr),
        "head": head or None,
        "details": {
            "phase": c.phase_name(phase),
            "items": list(items),
            "banner_shown": bool(banner_shown),
        },
    }


def validate_acceptances(lines: Any) -> None:
    """Raise ValueError unless ``lines`` is a list of acceptance lines."""
    if not isinstance(lines, list):
        raise ValueError("risk_acceptances must be a list")
    for line in lines:
        ok = (
            isinstance(line, dict)
            and set(line) == {"act", "by", "at", "via", "pr", "head", "details"}
            and line.get("act") == ACCEPT_ACT
            and line.get("via") in ACCEPT_VIAS
            and (
                line.get("via") == ACCEPT_VIA
                or (
                    isinstance(line.get("details"), dict)
                    and c.phase_name(line["details"].get("phase")) == c.DEPLOY
                )
            )
            and all(isinstance(line.get(k), str) and line[k].strip() for k in ("by", "at"))
            and isinstance(line.get("pr"), int)
            and not isinstance(line.get("pr"), bool)
            and line["pr"] > 0
            and (line.get("head") is None or isinstance(line.get("head"), str))
            and isinstance(line.get("details"), dict)
            and c.phase_name(line["details"].get("phase")) in (c.INTENT, c.DESIGN, c.DEPLOY)
            and isinstance(line["details"].get("items"), list)
            and all(isinstance(i, str) and i.strip() for i in line["details"]["items"])
            and isinstance(line["details"].get("banner_shown"), bool)
        )
        if not ok:
            raise ValueError(
                "risk_acceptances: each line is {act: 'risk accepted', by, at, via: 'merge' "
                "(or 'approval' at deploy), pr, head, details: {phase: intent|design|deploy, "
                "items, banner_shown}}"
            )


def record_acceptance(st: Any, line: dict[str, Any]) -> bool:
    """Append ``line`` unless a line for the same pull request and phase is already there;
    True when it was added. One merge is one act."""
    for old in st.risk_acceptances:
        if old.get("pr") == line["pr"] and c.phase_name(
            (old.get("details") or {}).get("phase")
        ) == c.phase_name(line["details"]["phase"]):
            return False
    st.risk_acceptances.append(line)
    return True


# --- the banner ---------------------------------------------------------------------------------
def _gate_record(change_dir: Path, phase: str) -> dict[str, Any] | None:
    # R45: ``gate-build.json``, or ``gate-c.json`` from an older plugin
    path = c.phase_file(Path(change_dir) / art.EVIDENCE_DIR, art.GATE_RESULT, phase)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) else None


def recorded_hits(record: dict[str, Any] | None) -> dict[str, list[str]]:
    """``{item: [where]}`` the risk-hit checks of a gate record reported, accepted or not."""
    out: dict[str, list[str]] = {}
    for check in (record or {}).get("checks") or []:
        if not isinstance(check, dict) or check.get("name") not in RISK_HIT_CHECKS:
            continue
        found = (check.get("details") or {}).get("hits")
        if isinstance(found, dict):
            for item, where in found.items():
                if str(item).strip():
                    listed = out.setdefault(str(item), [])
                    listed += [str(w) for w in where or [] if str(w) not in listed]
    return out


def declared_drops(record: dict[str, Any] | None) -> list[str]:
    """The drops the approved plan declares (the ``ratchets`` check's ``details.declared``):
    a banner line too (decision 35, point 6), never one to accept."""
    for check in (record or {}).get("checks") or []:
        if isinstance(check, dict) and check.get("name") == "ratchets":
            listed = (check.get("details") or {}).get("declared")
            return [str(d) for d in listed or []] if isinstance(listed, list) else []
    return []


def banner_entries(change_dir: Path, phase: str, st: Any) -> list[dict[str, Any]]:
    """One entry per item hit at the gates the phase's PR covers (``BANNER_PHASES``), in the
    order first found: ``{item, first, where, accepted, brief, brief_phase}``. ``accepted`` is
    how an earlier act accepted it, or None when the PR's merge is asked to; ``brief`` is the
    newest brief on it among those gates (None when no reviewer wrote one)."""
    phase = c.phase_name(phase)
    phases = BANNER_PHASES.get(phase, ())
    if phase == c.INTENT and str(getattr(st, "id", "")) != c.INIT_CHANGE_ID:
        return []  # a change's own folder never hits; (intent) asks only on the install PR
    done = accepted(st)
    entries: dict[str, dict[str, Any]] = {}
    for gate_phase in phases:
        for item, where in recorded_hits(_gate_record(change_dir, gate_phase)).items():
            entry = entries.setdefault(
                item.lower(),
                {"item": item, "first": gate_phase, "where": [], "brief": None,
                 "brief_phase": None, "accepted": done.get(item.lower())},
            )  # fmt: skip
            entry["where"] += [w for w in where if w not in entry["where"]]
        briefs = read_brief(change_dir, gate_phase)
        for key, entry in entries.items():
            if key in briefs:
                entry["brief"], entry["brief_phase"] = briefs[key], gate_phase
    return list(entries.values())


def new_items(entries: list[dict[str, Any]]) -> list[str]:
    """The banner's items no earlier act accepted: what the PR's merge accepts."""
    return [e["item"] for e in entries if not e.get("accepted")]


def _brief_text(entry: dict[str, Any]) -> str:
    brief = entry.get("brief")
    if not brief:
        return "the reviewer wrote no brief on it"
    parts = [f"{name.lower()}: {brief[name]}" for name in BRIEF_FIELDS if brief.get(name)]
    word = " The reviewer escalates on it." if brief.get("word") == "escalate" else ""
    return (
        f"brief ({brief_rel(entry['brief_phase'])}): " + ("; ".join(parts) or "empty") + "." + word
    )


def plan_grown(change_dir: Path, phase: str) -> list[str] | None:
    """The files the plan gained since gate (design), as the newest gate record the phase's PR
    covers holds them (``plan_sync``'s ``details.plan_growth.added``; R26, choice 257: R60's
    port, no park and no cap change). The newest record with a ``plan_sync`` check decides,
    never an older one behind it; None when it holds no growth (a record written before
    1.0.39, or no approved copy), at intent and design, and before any such record."""
    for gate_phase in reversed(BANNER_PHASES.get(c.phase_name(phase), ())):
        if gate_phase not in (c.BUILD, c.TEST, c.DEPLOY):
            continue
        for check in (_gate_record(change_dir, gate_phase) or {}).get("checks") or []:
            if isinstance(check, dict) and check.get("name") == "plan_sync":
                growth = (check.get("details") or {}).get("plan_growth")
                added = growth.get("added") if isinstance(growth, dict) else None
                if not isinstance(added, list):
                    return None
                return [str(p) for p in added if str(p).strip()]
    return None


def banner_lines(change_dir: Path, phase: str, st: Any) -> list[str]:
    """The banner's risk lines for the phase's PR, or [] when nothing hit. The first line
    carries ``BANNER_HEADING``; each item's line starts with ``- `<item>```, which
    ``banner_shown`` looks for."""
    phase = c.phase_name(phase)
    entries = banner_entries(change_dir, phase, st)
    declared: list[str] = []
    for gate_phase in BANNER_PHASES.get(phase, ()):
        for drop in declared_drops(_gate_record(change_dir, gate_phase)):
            if drop not in declared:
                declared.append(drop)
    grown = plan_grown(change_dir, phase)
    if not entries and not declared and not grown:
        return []
    if entries or declared:
        head = f"{BANNER_HEADING}: this change touches risk-list items."
    else:
        head = f"{BANNER_HEADING}: the plan changed after you approved it at gate (design)."
    if new_items(entries):
        head += " " + BANNER_ASK.get(phase, BANNER_ASK[c.DEPLOY])
    lines = [head]
    if grown:
        n = len(grown)
        listed = ", ".join(f"`{p}`" for p in grown[:5]) + (" …" if n > 5 else "")
        lines.append(
            f"- The plan grew by {n} file{'s' if n != 1 else ''} since gate (design): {listed}."
        )
    for entry in entries:
        where = ", ".join(entry["where"][:5]) + (" …" if len(entry["where"]) > 5 else "")
        if entry.get("accepted"):
            state = f"{entry['accepted']}; touched at gate ({entry['first']}) or later"
        else:
            state = f"first found at gate ({entry['first']})"
        lines.append(f"- `{entry['item']}` — {state}: {where}. {_brief_text(entry)}")
    for drop in declared:
        lines.append(f"- dropped, declared by the approved plan: {drop}")
    return lines


def banner_shown(body: str | None, items: list[str]) -> bool:
    """Whether a PR body carried the banner with a line for every item in ``items``."""
    text = body or ""
    at = text.find(BANNER_HEADING)
    if at < 0:
        return not items
    rest = text[at:]
    return all(f"- `{item}`" in rest for item in items)
