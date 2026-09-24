"""Layer-1 tests of deferred review (decision 21; build guide step 16a): the ledger, the
items a phase would park on, the three briefs, the record that applies a decision and counts
an iteration, the overturn, and the gate checks that read the ledger. The panel's
model-driven half (the three members) is a prompt: here their files are written by hand.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest
from panel import cli as panel_cli
from panel import ledger, prompts
from pr import description as desc

from gate import artifacts as art
from gate import gate
from state import status as status_mod
from tests.test_gate import (
    SPEC,
    _names,
    design_project,  # noqa: F401 - the fixture
    git,
    project,  # noqa: F401 - the fixture
    verdict,
    write,
)

ROOT = Path(__file__).resolve().parents[1]
PANEL_CLI = ROOT / "plugin" / "panel" / "cli.py"
OPEN_CONCERN = "Invoices may depend on the old rounding; nobody has checked."
DECISION = {
    "reviewer": "keep half-up; no caller reads the old rounding",
    "advocate": "no objection: the invoices module does not import percent()",
    "decision": "keep half-up rounding; the invoices module never calls percent()",
    "rationale": ["grep finds no caller in invoices/", "the coding standard names round()"],
}


def set_review(change: Path, mode: str) -> None:
    """The per-change override (status.yaml: review_override): the project's sdlc.yaml is a
    guardrail file, and a change on the branch would make the gate read the base's copy."""
    st = status_mod.read_status(change)
    st.review_override = mode
    status_mod.write_status(change, st)


def open_the_concern(change: Path) -> None:
    spec = SPEC.replace(
        "- [x] Rounding half-even vs half-up: decided half-up via round() (documented).",
        "- [x] Rounding half-even vs half-up: decided half-up via round() (documented).\n"
        f"- {OPEN_CONCERN}",
    )
    write(change / "spec.md", spec)


def run(argv: list[str]) -> tuple[int, dict]:
    proc = subprocess.run(
        [sys.executable, str(PANEL_CLI), *argv], capture_output=True, text=True, encoding="utf-8"
    )
    out = proc.stdout
    data = json.loads(out[out.index("{") :]) if "{" in out else {}
    return proc.returncode, data


# --- the ledger module ----------------------------------------------------------------------
def test_keys_are_stable_and_kinds_are_the_fixed_list():
    assert ledger.concern_key("- Foo  bar.") == ledger.concern_key("Foo bar.")
    assert ledger.concern_key("a") != ledger.concern_key("b")
    assert ledger.escalate_key(["b", "a"]) == ledger.escalate_key(["a ", " b"])
    assert ledger.finding_key("abc") == "finding:abc"
    assert ledger.kind_of_concern("The security baseline contradicts the UX policy") == "policy"
    assert ledger.kind_of_concern("Rounding is unclear") == "concern"
    assert set(ledger.PANEL_KINDS) == {"concern", "policy", "escalate", "finding", "verifier"}
    assert not set(ledger.PANEL_KINDS) & set(ledger.NEVER_TO_PANEL)
    for name in ("risk_list", "guardrails", "limits"):
        assert name in ledger.NEVER_TO_PANEL


def test_validate_entry_and_decision_file():
    item = {"kind": "concern", "key": "concern:x", "item": OPEN_CONCERN}
    entry = ledger.new_entry(1, "b", item, DECISION, "abc123", 0.3)
    assert ledger.validate_entry(entry) == []
    assert entry["rationale"] == DECISION["rationale"] and entry["overturned"] is None
    bad = dict(entry, kind="risk_list", rationale=["1", "2", "3", "4", "5", "6"], decision="a\nb")
    problems = ledger.validate_entry(bad)
    assert any("not one of the panel's" in p for p in problems)
    assert any("at most 5" in p for p in problems)
    assert any("one line" in p for p in problems)
    assert ledger.validate_decision_file({"decision": "x"}) != []
    assert ledger.validate_decision_file(dict(DECISION, rationale="one\ntwo")) == []
    assert ledger.validate_decision_file("text") == ["the decision file is not a JSON object"]


def test_ledger_round_trip_render_and_cost(tmp_path):
    change = tmp_path / "changes" / "0001-x"
    item = {"kind": "concern", "key": "concern:x", "item": OPEN_CONCERN}
    entries = [ledger.new_entry(1, "b", item, DECISION, "abc123", 0.3)]
    entries.append(ledger.new_entry(2, "b", dict(item, key="concern:y"), DECISION, "abc123", None))
    entries[1]["overturned"] = {"comment": "use half-even", "at": "2026-09-24T10:00:00Z"}
    ledger.save_ledger(change, "b", entries)
    assert ledger.load_ledger(change, "b") == entries
    assert ledger.ledger_error(change, "b") is None
    assert [e["n"] for e in ledger.active(entries)] == [1]
    assert ledger.decided_keys(entries) == {"concern:x"}
    assert ledger.total_cost(entries) == 0.3
    text = ledger.ledger_md_path(change, "b").read_text(encoding="utf-8")
    assert "Decisions taken for you — phase (b)" in text
    assert "1. [concern] " + OPEN_CONCERN in text and "cost: $0.30" in text
    assert "OVERTURNED by the owner's review comment: use half-even" in text
    assert "Total panel cost: $0.30" in text
    ledger.ledger_path(change, "b").write_text("{not json", encoding="utf-8")
    assert "unreadable" in ledger.ledger_error(change, "b")
    assert ledger.load_ledger(change, "b") == []
    assert ledger.load_ledger(change, "c") == [] and ledger.ledger_error(change, "c") is None


def test_apply_decision_closes_the_concern_in_spec_md(tmp_path):
    change = tmp_path / "changes" / "0001-x"
    open_the_concern(change)
    item = {"kind": "concern", "key": ledger.concern_key(OPEN_CONCERN), "item": OPEN_CONCERN}
    entry = ledger.new_entry(1, "b", item, DECISION, "abc123", None)
    assert ledger.apply_decision(change, entry) is True
    spec = (change / "spec.md").read_text(encoding="utf-8")
    assert art.open_concerns(spec) == []
    closed = ledger.panel_closed_concerns(spec)
    assert closed == [f"decided (by panel #1): {DECISION['decision']} — {OPEN_CONCERN}"]
    assert ledger.panel_closings(spec) == [(1, closed[0])]
    assert "- [x] Rounding half-even" in spec  # the other item is untouched
    assert ledger.apply_decision(change, entry) is False  # already closed
    assert ledger.apply_decision(change, dict(entry, kind="escalate")) is False


def test_clean_decision_strips_the_copied_closing_and_the_restated_item():
    """The first deferred run (sample change 0002): the conciliator copied the closing
    format from its brief and the spec read ``decided (by panel): decided (by panel): X —
    <concern> — <concern>``."""
    item = "`mean`'s parameter type is undecided: a materialised `Sequence[float]` (simpler,"
    raw = (
        "decided (by panel): `Sequence[float]` — mean's parameter type is undecided: a "
        'materialised `Sequence[float]` (simpler, matches intent\'s "keep it minimal") or a '
        "general `Iterable[float]`."
    )
    assert ledger.clean_decision(raw, item) == "`Sequence[float]`"
    assert (
        ledger.clean_decision("Decided (by panel #3): keep it — keep it", item)
        == "keep it — keep it"
    )
    assert ledger.clean_decision("  keep   half-up  ", item) == "keep half-up"
    assert ledger.clean_decision("a — b", "unrelated concern text here") == "a — b"
    entry = ledger.new_entry(2, "b", {"kind": "concern", "key": "k", "item": item},
                             dict(DECISION, decision=raw), "abc", None)  # fmt: skip
    assert entry["decision"] == "`Sequence[float]`"
    # the 0.2.14 form (no number) is still a closing; the number is read when present
    spec = SPEC.replace(
        "- [x] Rounding half-even vs half-up: decided half-up via round() (documented).",
        "- decided (by panel): keep half-up — Rounding\n- decided (by panel #7): x — y",
    )
    assert ledger.panel_closings(spec) == [
        (None, "decided (by panel): keep half-up — Rounding"),
        (7, "decided (by panel #7): x — y"),
    ]


def test_verifier_disagreement_is_read_from_the_report():
    assert ledger.verifier_disagrees("...\n- **Verdict** — `does not match the plan`\n")
    assert ledger.verifier_disagrees("Verdict: does not match the plan")
    assert not ledger.verifier_disagrees("- **Verdict** — `matches the plan`\n")
    assert not ledger.verifier_disagrees(None)


# --- the CLI against the fixture ---------------------------------------------------------------
def test_items_lists_the_fixed_list_and_the_parks(design_project):  # noqa: F811
    root, change = design_project
    open_the_concern(change)
    git(root, "add", ".")
    git(root, "commit", "-q", "-m", "design(0001): an open concern")
    verdict(root, "b", verdict="escalate")
    rc, out = run(["items", "--root", str(root), "--id", "0001", "--phase", "b"])
    assert rc == 0 and out["mode"] == "parked" and out["gate"] == "park"
    kinds = [(i["kind"], i["decided"]) for i in out["items"]]
    assert kinds == [("concern", False), ("escalate", False)]
    assert out["items"][0]["item"] == OPEN_CONCERN and out["items"][0]["n"] == 1
    assert out["items"][1]["key"].startswith("escalate:")
    assert out["parks"] == [] and out["pending"] == [1, 2]
    assert out["iterations"] == {"used": 0, "cap": 3, "left": 3}
    assert ledger.items_path(change, "b").is_file()
    # a never-to-panel failure is a park, not an item
    write(root / "sample_pkg" / "stray.py", "x = 1\n")
    git(root, "add", ".")
    git(root, "commit", "-q", "-m", "a source file at (b)")
    verdict(root, "b", verdict="escalate")
    rc, out = run(["items", "--root", str(root), "--id", "0001", "--phase", "b"])
    assert [p["check"] for p in out["parks"]] == ["design_scope"]
    assert len(out["items"]) == 2


def test_record_refuses_under_parked_and_decides_under_deferred(design_project):  # noqa: F811
    root, change = design_project
    open_the_concern(change)
    git(root, "add", ".")
    git(root, "commit", "-q", "-m", "design(0001): an open concern")
    verdict(root, "b")
    assert run(["items", "--root", str(root), "--id", "0001", "--phase", "b"])[0] == 0
    decision = ledger.member_path(change, "b", 1, "conciliator")
    decision.parent.mkdir(parents=True, exist_ok=True)
    decision.write_text(json.dumps(DECISION), encoding="utf-8")
    rc, _out = run(["record", "--root", str(root), "--id", "0001", "--phase", "b", "--item", "1"])
    assert rc == panel_cli.EXIT_PARKED_MODE  # review: parked - the owner decides
    assert ledger.load_ledger(change, "b") == []

    set_review(change, "deferred")
    rc, out = run(["mode", "--root", str(root), "--id", "0001"])
    assert rc == 0 and out["mode"] == "deferred"
    rc, out = run(
        ["record", "--root", str(root), "--id", "0001", "--phase", "b", "--item", "1",
         "--cost-usd", "0.42"]
    )  # fmt: skip
    assert rc == 0, out
    assert out["recorded"] and out["applied_to_spec"] and out["panel_calls"] == 1
    assert out["iterations"] == 0  # a panel call is not a fix iteration (0.2.15)
    entry = out["entry"]
    assert entry["kind"] == "concern" and entry["decision"] == DECISION["decision"]
    before = entry["head"]
    assert entry["cost_usd"] == 0.42
    st = status_mod.read_status(change)
    assert st.panel_calls == 1 and st.iterations == 0
    spec = (change / "spec.md").read_text(encoding="utf-8")
    assert art.open_concerns(spec) == [] and ledger.panel_closings(spec)[0][0] == 1
    assert (change / "evidence" / "decisions-b.md").is_file()
    # record committed the decision itself: spec, status and ledger are in HEAD
    head = git(root, "rev-parse", "HEAD").strip()
    assert out["commit"] == head and head != before
    assert git(root, "log", "-1", "--format=%s").strip() == "design(0001): panel decision 1"
    assert git(root, "status", "--porcelain", "--", "changes").strip() == ""
    # idempotent: the same item again is not recorded twice
    rc, out = run(["record", "--root", str(root), "--id", "0001", "--phase", "b", "--item", "1"])
    assert rc == 0 and out["recorded"] is False and out["reason"] == "already decided"
    # the gate now continues past the concern and reads the ledger; a tidied closing line
    # still matches its ledger line by number
    spec = (
        (change / "spec.md")
        .read_text(encoding="utf-8")
        .replace(
            f"decided (by panel #1): {DECISION['decision']} — {OPEN_CONCERN}",
            "decided (by panel #1): keep `half-up`: the invoices module never calls it.",
        )
    )
    write(change / "spec.md", spec)
    git(root, "add", ".")
    git(root, "commit", "-q", "-m", "design(0001): tidy")
    verdict(root, "b")
    result = gate.run_gate(root, "0001", "b", dry_run=True)
    assert result.result == "wait", result.reason
    panel = next(ch for ch in result.checks if ch.name == "panel")
    assert panel.ok and panel.details["decisions"][0]["kind"] == "concern"
    assert panel.details["cost_usd"] == 0.42
    # the PR summary opens with the decision
    body = desc.build_description(root, "0001", "b")
    first = body.splitlines()[0]
    assert first.startswith("**Decisions taken for you (1)**")
    assert f"1. (b) [concern] {OPEN_CONCERN} → **{DECISION['decision']}**" in body
    assert "evidence/decisions-b.md, line 1" in body
    # the owner overturns it with a review comment
    rc, out = run(
        ["overturn", "--root", str(root), "--id", "0001", "--phase", "b", "--item", "1",
         "--comment", "use half-even after all"]
    )  # fmt: skip
    assert rc == 0 and out["entry"]["overturned"]["comment"] == "use half-even after all"
    body = desc.build_description(root, "0001", "b")
    assert body.splitlines()[0].startswith("**Decisions taken for you (0)** — 1 overturned")


def test_record_stops_at_the_iteration_cap_and_validates_the_decision(design_project):  # noqa: F811
    root, change = design_project
    set_review(change, "deferred")
    open_the_concern(change)
    git(root, "add", ".")
    git(root, "commit", "-q", "-m", "design(0001): an open concern")
    verdict(root, "b")
    assert run(["items", "--root", str(root), "--id", "0001", "--phase", "b"])[0] == 0
    decision = ledger.member_path(change, "b", 1, "conciliator")
    decision.parent.mkdir(parents=True, exist_ok=True)
    decision.write_text(json.dumps({"decision": "x"}), encoding="utf-8")
    rc, _out = run(["record", "--root", str(root), "--id", "0001", "--phase", "b", "--item", "1"])
    assert rc == panel_cli.EXIT_USAGE  # no reviewer clause, no rationale
    decision.write_text(json.dumps(DECISION), encoding="utf-8")
    st = status_mod.read_status(change)
    st.iterations = 3  # the fix-iteration cap: not the panel's
    st.panel_calls = 4  # gate.max_panel_calls (default 4)
    status_mod.write_status(change, st)
    rc, out = run(["record", "--root", str(root), "--id", "0001", "--phase", "b", "--item", "1"])
    assert rc == panel_cli.EXIT_CAP and out["reason"] == "panel-call cap reached"
    assert out["panel_calls"] == 4 and out["cap"] == 4
    assert ledger.load_ledger(change, "b") == [] and art.open_concerns(
        (change / "spec.md").read_text(encoding="utf-8")
    )
    rc, out = run(["items", "--root", str(root), "--id", "0001", "--phase", "b"])
    assert rc == 0 and out["panel_calls"] == {"used": 4, "cap": 4, "left": 0}
    # the gate parks on the count once it is past the cap, and says how to lift it
    st.panel_calls = 5
    status_mod.write_status(change, st)
    result = gate.run_gate(root, "0001", "b", dry_run=True)
    limits_check = next(ch for ch in result.checks if ch.name == "limits")
    assert (
        not limits_check.ok
        and "panel-call cap reached: 5 panel calls, cap 4" in limits_check.reason
    )
    assert "sdlc:reset-iterations" in limits_check.need
    # --no-commit leaves the commit to the caller
    st.panel_calls = 0
    status_mod.write_status(change, st)
    rc, out = run(["record", "--root", str(root), "--id", "0001", "--phase", "b", "--item", "1",
                   "--no-commit"])  # fmt: skip
    assert rc == 0 and out["commit"] is None
    assert git(root, "status", "--porcelain", "--", "changes").strip() != ""
    rc, _out = run(["record", "--root", str(root), "--id", "0001", "--phase", "b", "--item", "9"])
    assert rc == panel_cli.EXIT_USAGE


def test_prompts_name_the_item_the_files_and_the_blindness(design_project):  # noqa: F811
    root, change = design_project
    open_the_concern(change)
    git(root, "add", ".")
    git(root, "commit", "-q", "-m", "design(0001): an open concern")
    verdict(root, "b")
    assert run(["items", "--root", str(root), "--id", "0001", "--phase", "b"])[0] == 0
    texts = {}
    for member in ledger.MEMBERS:
        proc = subprocess.run(
            [sys.executable, str(PANEL_CLI), "prompt", "--root", str(root), "--id", "0001",
             "--phase", "b", "--item", "1", "--member", member],
            capture_output=True, text=True, encoding="utf-8",
        )  # fmt: skip
        assert proc.returncode == 0, proc.stderr
        texts[member] = proc.stdout
        assert OPEN_CONCERN in proc.stdout and "Kind: concern" in proc.stdout
        assert "{" not in proc.stdout.replace("{{", "").replace("}}", "").split("```")[0]
    assert "evidence/panel/b-1-reviewer.md" in texts["reviewer"].replace("\\", "/")
    assert "must not look for" in texts["advocate"] and "b-1-advocate.md" in texts["advocate"]
    assert "b-1-conciliator.json" in texts["conciliator"]
    assert '"rationale"' in texts["conciliator"] and "at most five lines" in texts["conciliator"]
    assert prompts.APPLY_HINT["concern"].split(" ")[0] in texts["conciliator"]
    # the advocate runs on another model: the design command says which key names it
    text = (ROOT / "plugin" / "commands" / "sdlc-design.md").read_text(encoding="utf-8")
    assert "panel_advocate_model" in text and "sdlc:adversarial-reviewer" in text


# --- the gate reads the ledger --------------------------------------------------------------------
def _ledger_entry(change: Path, phase: str, item: dict, decision: str, head: str) -> dict:
    entries = ledger.load_ledger(change, phase)
    entry = ledger.new_entry(
        len(entries) + 1, phase, item, dict(DECISION, decision=decision), head, None
    )
    entries.append(entry)
    ledger.save_ledger(change, phase, entries)
    return entry


def test_gate_accepts_an_escalate_the_panel_decided_to_continue(project):  # noqa: F811
    root, change = project
    set_review(change, "deferred")
    verdict(root, "c", verdict="escalate")
    result = gate.run_gate(root, "0001", "c", dry_run=True)
    assert "adversarial_review" in _names(result, False)
    head = git(root, "rev-parse", "HEAD").strip()
    reasons = ["blast radius larger than the plan says"]
    item = {"kind": "escalate", "key": ledger.escalate_key(reasons), "item": "escalate"}
    _ledger_entry(change, "c", item, "continue: the plan lists every file the diff touches", head)
    git(root, "add", ".")
    git(root, "commit", "-q", "-m", "build(0001): panel decisions")
    verdict(root, "c", verdict="escalate")
    result = gate.run_gate(root, "0001", "c", dry_run=True)
    assert result.result == "continue", result.reason
    adv = next(ch for ch in result.checks if ch.name == "adversarial_review")
    assert adv.ok and "the review panel decided to continue" in adv.reason
    assert adv.details["settled_by_panel"] == 1
    # a decision that does not say continue keeps the park, and says what the panel said
    entries = ledger.load_ledger(change, "c")
    entries[0]["decision"] = "park: the owner must see the blast radius"
    ledger.save_ledger(change, "c", entries)
    result = gate.run_gate(root, "0001", "c", dry_run=True)
    adv = next(ch for ch in result.failed if ch.name == "adversarial_review")
    assert "the panel decided: park" in adv.need
    # under review: parked the ledger decides nothing and the panel check says so
    set_review(change, "parked")
    result = gate.run_gate(root, "0001", "c", dry_run=True)
    assert {"adversarial_review", "panel"} <= set(_names(result, False))
    panel = next(ch for ch in result.failed if ch.name == "panel")
    assert "review mode is parked" in panel.reason


def test_gate_accepts_an_important_finding_the_panel_settled(project):  # noqa: F811
    from review import findings as fmod

    root, change = project
    set_review(change, "deferred")
    verdict(root, "c")
    head = git(root, "rev-parse", "HEAD").strip()
    finding = {
        "pass": "compliance",
        "severity": "important",
        "file": "CLAUDE.md",
        "line": 0,
        "summary": "CLAUDE.md is outdated: the new percent() helper is not in the commands",
        "rule": "REVIEW.md: flag when the change has made CLAUDE.md outdated",
    }
    data = {"schema_version": 1, "head": head, "findings": [finding], "tally": {}}
    write(change / art.EVIDENCE_DIR / art.REVIEW_FINDINGS, json.dumps(data))
    result = gate.run_gate(root, "0001", "c", dry_run=True)
    assert "findings" in _names(result, False)
    item = {
        "kind": "finding",
        "key": ledger.finding_key(fmod.signature(finding)),
        "item": finding["summary"],
    }
    _ledger_entry(change, "c", item, "settled: the CLAUDE.md line is proposed in the PR body", head)
    result = gate.run_gate(root, "0001", "c", dry_run=True)
    assert "findings" not in _names(result, False), result.reason
    check = next(ch for ch in result.checks if ch.name == "findings")
    assert "settled by the review panel" in check.reason
    assert check.details["settled_by_panel"] == [finding["summary"]]


def test_gate_panel_check_refuses_a_bad_ledger_and_an_unrecorded_closing(project):  # noqa: F811
    root, change = project
    set_review(change, "deferred")
    verdict(root, "c")
    head = git(root, "rev-parse", "HEAD").strip()
    entry = _ledger_entry(
        change, "c", {"kind": "risk_list", "key": "x", "item": "auth"}, "accept it", head
    )
    result = gate.run_gate(root, "0001", "c", dry_run=True)
    panel = next(ch for ch in result.failed if ch.name == "panel")
    assert "never goes to the panel" in panel.reason or "not one of the panel's" in panel.reason
    assert entry["n"] == 1
    ledger.save_ledger(change, "c", [])
    spec = (
        (change / "spec.md")
        .read_text(encoding="utf-8")
        .replace(
            "- [x] Rounding half-even vs half-up: decided half-up via round() (documented).",
            "- decided (by panel): keep half-up — Rounding half-even vs half-up",
        )
    )
    write(change / "spec.md", spec)
    result = gate.run_gate(root, "0001", "c", dry_run=True)
    panel = next(ch for ch in result.failed if ch.name == "panel")
    assert "no ledger line" in panel.reason
    spec = spec.replace(
        "- decided (by panel): keep half-up", "- decided (by panel #4): keep half-up"
    )
    write(change / "spec.md", spec)
    result = gate.run_gate(root, "0001", "c", dry_run=True)
    panel = next(ch for ch in result.failed if ch.name == "panel")
    assert "panel decision 4, which the ledger lacks" in panel.reason


def test_a_change_may_override_the_review_mode(tmp_path):
    change_dir, st = status_mod.new_change(tmp_path, "Deferred one", review_override="deferred")
    assert status_mod.read_status(change_dir).review_override == "deferred"
    with pytest.raises(ValueError):
        st.review_override = "panel"
        st.validate()
