"""Layer-1 tests for plugin/gate: artifact contracts, risk matching, findings and verdict
readers, run limits — and, against a temporary copy of the fixture project, the gate itself:
`continue` on a clean change, `wait` at a human gate, `park` with the right reason for each
prepared failure (missing plan.md, failing test behind SAMPLE_FAIL=1, a diff touching
.claude/settings.json, a risk-list word, an escalating or stale adversarial verdict, an open
flagged concern, a limit hit), and gate (b): a spec.md without its rendered header or a design
branch that touches source parks, while a clean one waits (Standard) or continues (Lite)."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from gate import artifacts as art
from gate import checks, gate, limits, policy, preflight
from gate import cli as gate_cli
from state import status as status_mod
from state import yamlish

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "sample-python-project"
INIT = ROOT / "plugin" / "init" / "sdlc_init.py"
GATE_CLI = ROOT / "plugin" / "gate" / "cli.py"
STATE_CLI = ROOT / "plugin" / "state" / "cli.py"
PLUGIN_VERSION = json.loads((ROOT / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))[
    "version"
]

INTENT = """# Intent: percent helper
Author: owner (developer). Status: accepted. Change id: 0001. Entry route: idea.

## Problem
Callers compute percentages by hand and get rounding wrong.

## Proposed outcome
`sample_pkg.percent(part, whole)` returns a rounded percentage; covered by tests.

## Affected users and systems
sample_pkg users.

## Constraints
No new dependencies.

## Open questions
none
"""

# The header is what `gate/cli.py spec-header` renders and the design pass pastes (step 22);
# the gate parks a spec.md whose header lacks one of art.SPEC_HEADER_FIELDS.
SPEC_HEADER = art.render_spec_header(
    "percent helper", "0001", PLUGIN_VERSION, list(preflight.POLICY_SKILLS), []
)
SPEC_BODY = """
## Requirements
- percent(part, whole) returns part / whole * 100 rounded to one decimal.
- whole == 0 raises ValueError.

## Design
A pure function in sample_pkg/percent.py exported from the package.

## Open questions from intent
none

## Flagged concerns
- [x] Rounding half-even vs half-up: decided half-up via round() (documented).

## Acceptance
Tests in tests/test_percent.py pass; lint clean.
"""
SPEC = SPEC_HEADER + "\n" + SPEC_BODY

PLAN = """# Plan: percent helper (from intent.md 2026-09-21, spec.md 2026-09-21)

## Files that change
- `sample_pkg/percent.py` — new: percent(part, whole)
- `sample_pkg/__init__.py` — export percent
- `tests/test_percent.py` — new: three cases

## Order of work
1. Add the function and its test.
2. Export it.

## Risks
Rounding; nothing else.

## Options not taken
Decimal module: overkill.

## Proof
tests/test_percent.py::test_percent_rounds
"""

PERCENT = '''"""Percent helper."""


def percent(part: float, whole: float) -> float:
    if whole == 0:
        raise ValueError("whole must not be zero")
    return round(part / whole * 100, 1)
'''

TEST_PERCENT = """from sample_pkg.percent import percent


def test_percent_rounds():
    assert percent(1, 3) == 33.3
"""


# --- helpers ----------------------------------------------------------------------------------
def git(cwd: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=cwd, capture_output=True, text=True, check=True, encoding="utf-8"
    ).stdout


def run_py(*args: str, cwd: Path, env: dict | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        env=env or os.environ.copy(),
        encoding="utf-8",
    )


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def verdict(root: Path, phase: str, verdict: str = "continue", classification="routine", head=None):
    head = head or git(root, "rev-parse", "HEAD").strip()
    data = {
        "schema_version": 1,
        "phase": phase,
        "head": head,
        "verdict": verdict,
        "reasons": [] if verdict == "continue" else ["blast radius larger than the plan says"],
        "classification": classification,
        "classification_reasons": [],
        "at": "2026-09-21T10:00:00Z",
    }
    path = (
        root / "changes" / "0001-percent-helper" / "evidence" / f"adversarial-review-{phase}.json"
    )
    write(path, json.dumps(data))
    return path


def on_base(root: Path, edit, message: str = "owner change on main") -> None:
    """Apply ``edit(root)`` as a commit on main and merge it into the current phase branch,
    so the gate sees it as approved (part of the merge base), not as part of the diff."""
    branch = git(root, "rev-parse", "--abbrev-ref", "HEAD").strip()
    git(root, "checkout", "-q", "main")
    edit(root)
    git(root, "add", ".")
    git(root, "commit", "-q", "-m", message)
    git(root, "checkout", "-q", branch)
    git(root, "merge", "-q", "--no-edit", "main")


def start_run(root: Path, phase: str) -> None:
    proc = run_py(
        str(GATE_CLI), "start-run", "--root", str(root), "--id", "0001", "--phase", phase, cwd=root
    )
    assert proc.returncode == 0, proc.stderr


def _initialised_fixture(tmp_path) -> tuple[Path, Path]:
    """A fixture copy on main with /sdlc-init merged and change 0001 created with its intent
    (uncommitted): the common ground of the phase-(b) and phase-(c) states below."""
    root = tmp_path / "proj"
    shutil.copytree(FIXTURE, root)
    git(root, "init", "-q", "-b", "main")
    git(root, "config", "user.email", "owner@example.com")
    git(root, "config", "user.name", "Owner")
    git(root, "add", ".")
    git(root, "commit", "-q", "-m", "fixture")
    proc = run_py(str(INIT), "--root", str(root), "--profile", "standard", cwd=root)
    assert proc.returncode == 0, proc.stderr
    git(root, "add", ".")
    git(root, "commit", "-q", "-m", "sdlc-init (as if the 0000 PR merged)")
    proc = run_py(
        str(STATE_CLI), "new-change", "--root", str(root), "--title", "Percent helper", cwd=root
    )
    assert proc.returncode == 0, proc.stderr
    change = root / "changes" / "0001-percent-helper"
    write(change / "intent.md", INTENT)
    return root, change


@pytest.fixture
def project(tmp_path):
    """Fixture copy initialised (standard profile), change 0001 through (b), and a phase-(c)
    branch with the implementation committed together with plan.md."""
    root, change = _initialised_fixture(tmp_path)
    write(change / "spec.md", SPEC)
    write(change / "plan.md", PLAN)
    st = status_mod.read_status(change)
    st.set_phase("c")
    status_mod.write_status(change, st)
    git(root, "add", ".")
    git(root, "commit", "-q", "-m", "intent, spec and plan (as if the a and b PRs merged)")
    git(root, "checkout", "-q", "-b", "sdlc/0001/c")
    write(root / "sample_pkg" / "percent.py", PERCENT)
    write(root / "tests" / "test_percent.py", TEST_PERCENT)
    init_py = root / "sample_pkg" / "__init__.py"
    write(init_py, init_py.read_text(encoding="utf-8") + "from .percent import percent  # noqa\n")
    write(change / "evidence" / "verifier.md", "# Verifier\nRan the tests; percent(1,3)=33.3.\n")
    # the plan-sync hook requires plan.md in every commit that changes source (p.16 step 7)
    write(change / "plan.md", PLAN + "\nProgress: step 1 and 2 done.\n")
    git(root, "add", ".")
    git(root, "commit", "-q", "-m", "build: percent helper")
    start_run(root, "c")  # the runbook registers the run before the work (step 19)
    return root, change


@pytest.fixture
def design_project(tmp_path):
    """Fixture copy initialised, the intent merged on main (as if the (a) PR did), and the
    phase-(b) branch carrying only spec.md and plan.md — the state gate (b) judges."""
    root, change = _initialised_fixture(tmp_path)
    git(root, "add", ".")
    git(root, "commit", "-q", "-m", "intent(0001): percent helper (as if the a PR merged)")
    git(root, "checkout", "-q", "-b", "sdlc/0001/b")
    write(change / "spec.md", SPEC)
    write(change / "plan.md", PLAN)
    st = status_mod.read_status(change)
    st.set_phase("b")
    status_mod.write_status(change, st)
    git(root, "add", ".")
    git(root, "commit", "-q", "-m", "design(0001): spec and plan")
    start_run(root, "b")
    return root, change


# --- artifact contracts -----------------------------------------------------------------------
def test_artifact_section_helpers():
    assert art.missing_sections(INTENT, art.INTENT_SECTIONS) == []
    assert art.missing_sections("# x\n## Problem\nfoo\n", art.INTENT_SECTIONS) == list(
        art.INTENT_SECTIONS[1:]
    )
    assert art.empty_sections(
        "## Problem\n\n## Proposed outcome\nok\n", art.INTENT_SECTIONS[:2]
    ) == ["## Problem"]
    assert art.planned_files(PLAN) == [
        "sample_pkg/percent.py",
        "sample_pkg/__init__.py",
        "tests/test_percent.py",
    ]
    assert art.planned_files("## Files that change\n- src/a.py: add x\n1. lib\\b.py — y\n") == [
        "src/a.py",
        "lib/b.py",
    ]
    assert art.open_concerns(SPEC) == []
    assert art.open_concerns(SPEC.replace("- [x] Rounding", "- [ ] Rounding")) == [
        "- [ ] Rounding half-even vs half-up: decided half-up via round() (documented)."
    ]
    # fail closed: an item that does not say it is closed is open; "none" is no concern
    assert art.open_concerns("## Flagged concerns\n- Rounding: undecided, needs owner\n") == [
        "- Rounding: undecided, needs owner"
    ]
    assert art.open_concerns("## Flagged concerns\n- none\n- Closed: fine\n1. resolved\n") == []
    # dot paths and a backtick span anywhere in the item
    plan = "## Files that change\n- `.github/workflows/ci.yml` — new\n- new file `src/x.py`\n"
    assert art.planned_files(plan + "- ./.gitignore\n") == [
        ".github/workflows/ci.yml",
        "src/x.py",
        ".gitignore",
    ]
    assert art.is_framework_change("Author: o. Status: draft.\nFramework change: yes\n")
    assert not art.is_framework_change(INTENT)


def test_spec_header_render_and_intent_title():
    header = art.render_spec_header(
        "percent helper", "0001", "0.1.0", ["coding-standards", "security-baseline"], []
    )
    title_line, fields = header.splitlines()
    assert title_line == "# Spec: percent helper"
    assert fields == (
        "Change id: 0001. Status: proposed. Produced by: sdlc plugin 0.1.0, /sdlc-design "
        "prompt v1 (article p.14). Skills: coding-standards, security-baseline "
        "(plugin 0.1.0); overrides: none"
    )
    assert all(f in fields for f in art.SPEC_HEADER_FIELDS)
    assert art.DESIGN_PROMPT_VERSION == "v1"
    overridden = art.render_spec_header("x", "0002", "1.2.3", ["a", "b"], ["b"])
    assert overridden.endswith("Skills: a, b (plugin 1.2.3); overrides: b")
    # the header a spec carries is the one the gate accepts
    assert art.missing_sections(SPEC, art.SPEC_SECTIONS) == []
    assert all(f in SPEC.split("## ", 1)[0] for f in art.SPEC_HEADER_FIELDS)
    assert art.intent_title(INTENT) == "percent helper"
    assert art.intent_title("#  Intent:   spaced title  \n## Problem\n") == "spaced title"
    assert art.intent_title("# Spec: percent helper\n") is None
    assert art.intent_title("# Intent:\n") is None
    assert art.intent_title("") is None


def test_risk_hits_match_whole_tokens_only():
    items = ["auth", "data migrations", "money movement", "production config"]
    hits = checks.risk_hits(items, ["src/auth/login.py", "db/data_migration/001.sql"], {})
    assert hits == {
        "auth": ["src/auth/login.py"],
        "data migrations": ["db/data_migration/001.sql"],
    }
    assert checks.risk_hits(["auth"], ["docs/author.md"], {"spec.md": "the author writes"}) == {}
    assert checks.risk_hits(["money movement"], [], {"spec.md": "No money-movement here"}) == {
        "money movement": ["spec.md: text"]
    }


def test_findings_and_verdict_readers(tmp_path):
    p = tmp_path / "review-findings.json"
    assert checks.load_findings(p) == (None, "missing")
    p.write_text("{", encoding="utf-8")
    assert checks.load_findings(p)[1].startswith("unreadable")
    p.write_text(json.dumps({"findings": [{"severity": "Important", "summary": "x"}]}))
    data, err = checks.load_findings(p)
    assert err == "" and len(checks.important_findings(data)) == 1
    v = tmp_path / "adversarial-review-c.json"
    v.write_text(json.dumps({"verdict": "maybe"}), encoding="utf-8")
    assert checks.load_verdict(v)[1].startswith("malformed")
    v.write_text(json.dumps({"verdict": "continue", "classification": "routine"}))
    assert "head" in checks.load_verdict(v)[1]  # a verdict without a commit is malformed
    v.write_text(
        json.dumps({"verdict": "continue", "classification": "routine", "head": "abc1234"})
    )
    assert checks.load_verdict(v)[0]["verdict"] == "continue"


# --- run limits (step 19) with a bare context -------------------------------------------------
def _ctx(tmp_path, config=None, iterations=0, phase="c"):
    change_dir = tmp_path / "changes" / "0001-x"
    (change_dir / "evidence").mkdir(parents=True, exist_ok=True)
    st = status_mod.Status(id="0001", slug="x", title="x", phase=phase, iterations=iterations)
    # human_gate=True: these unit tests isolate the caps; run registration is tested on the fixture
    return checks.GateContext(tmp_path, change_dir, phase, st, config or {}, None, True, "no git")


def test_limits_pause_flag_stops_everything(tmp_path):
    res = limits.check_limits(_ctx(tmp_path, {"paused": True}))
    assert not res.ok and res.details["stop"] and "paused" in res.reason


def test_limits_iteration_cap_default_and_non_routine(tmp_path):
    assert limits.check_limits(_ctx(tmp_path, iterations=3)).ok
    res = limits.check_limits(_ctx(tmp_path, iterations=4))
    assert not res.ok and "cap 3" in res.reason
    ctx = _ctx(tmp_path, iterations=3)
    write(
        ctx.evidence_dir / "adversarial-review-b.json",
        json.dumps({"verdict": "continue", "classification": "non-routine", "head": "abc1234"}),
    )
    res = limits.check_limits(ctx)
    assert not res.ok and "cap 2" in res.reason and "non-routine" in res.reason
    ctx = _ctx(tmp_path / "fresh", {"gate": {"max_iterations": 5}}, iterations=5)
    assert limits.check_limits(ctx).ok


def test_limits_wall_clock_and_budget(tmp_path):
    ctx = _ctx(tmp_path, {"gate": {"max_wall_clock_minutes": 30, "max_budget_usd": 2}})
    started = datetime.now(timezone.utc) - timedelta(minutes=45)
    write(
        ctx.evidence_dir / "run-c.json",
        json.dumps({"started_at": started.isoformat().replace("+00:00", "Z")}),
    )
    res = limits.check_limits(ctx)
    assert not res.ok and "wall-clock" in res.reason
    write(
        ctx.evidence_dir / "run-c.json",
        json.dumps({"started_at": datetime.now(timezone.utc).isoformat(), "spend_usd": 2.5}),
    )
    res = limits.check_limits(ctx)
    assert not res.ok and "budget" in res.reason
    write(ctx.evidence_dir / "run-c.json", json.dumps({"spend_usd": 2.5}))
    assert not limits.check_limits(ctx).ok
    write(ctx.evidence_dir / "run-c.json", json.dumps({"spend_usd": 1.0}))
    assert limits.check_limits(ctx).ok


# --- the gate against the fixture --------------------------------------------------------------
def _names(result, ok):
    return sorted(ch.name for ch in result.checks if ch.ok is ok)


def test_gate_continues_on_a_clean_change(project):
    root, change = project
    verdict(root, "c")
    result = gate.run_gate(root, "0001", "c")
    assert result.result == "continue", result.reason
    assert result.label is None and result.human_gate is False and result.profile == "standard"
    assert _names(result, False) == []
    assert set(_names(result, True)) == {
        "limits",
        "clean_tree",
        "artifacts",
        "open_concerns",
        "commands",
        "evidence",
        "findings",
        "plan_sync",
        "guardrails",
        "risk_list",
        "owner_actions",
        "adversarial_review",
    }
    st = status_mod.read_status(change)
    assert st.gate.phase == "c" and st.gate.result == "passed" and st.parked_reason is None
    recorded = json.loads((change / "evidence" / "gate-c.json").read_text(encoding="utf-8"))
    assert recorded["result"] == "continue" and recorded["head"] == result.head
    assert result.what_i_need() == ""


def test_gate_waits_at_a_human_gate_and_dry_run_writes_nothing(project):
    root, change = project
    st = status_mod.read_status(change)
    st.profile_override = "full"
    status_mod.write_status(change, st)
    before = (change / "status.yaml").read_text(encoding="utf-8")
    result = gate.run_gate(root, "0001", "c", dry_run=True)
    assert result.result == "park"  # Full profile still needs the adversarial verdict at (c)
    assert "adversarial_review" in _names(result, False)
    verdict(root, "c")
    result = gate.run_gate(root, "0001", "c", dry_run=True)
    assert result.result == "wait" and result.label == "sdlc:c-ready"
    assert (change / "status.yaml").read_text(encoding="utf-8") == before
    assert not (change / "evidence" / "gate-c.json").exists()
    # a failed check parks even at a human gate
    (root / "sample_pkg" / "percent.py").unlink()
    write(root / "sample_pkg" / "extra.py", "x = 1\n")
    result = gate.run_gate(root, "0001", "c")
    assert result.result == "park" and "plan_sync" in _names(result, False)


def test_gate_parks_without_plan_md(project):
    root, change = project
    verdict(root, "c")
    (change / "plan.md").unlink()
    result = gate.run_gate(root, "0001", "c")
    assert result.result == "park"
    failed = {ch.name: ch for ch in result.failed}
    assert "artifacts" in failed and "plan.md is missing" in failed["artifacts"].reason
    st = status_mod.read_status(change)
    assert st.gate.result == "parked" and "plan.md is missing" in st.parked_reason
    block = result.what_i_need()
    assert block.startswith("## What I need from you") and "**artifacts**" in block
    assert "--id 0001 --phase c" in block


def test_gate_parks_on_a_failing_test(project, monkeypatch):
    root, _ = project
    verdict(root, "c")
    monkeypatch.setenv("SAMPLE_FAIL", "1")
    result = gate.run_gate(root, "0001", "c")
    assert result.result == "park"
    cmd = next(ch for ch in result.failed if ch.name == "commands")
    assert "test (exit 1)" in cmd.reason
    assert "SAMPLE_FAIL=1" in cmd.details["runs"]["test"]["output"]
    assert cmd.details["runs"]["build"]["exit_code"] == 0


def test_gate_parks_when_the_diff_touches_settings_json(project):
    root, change = project
    verdict(root, "c")
    settings = root / ".claude" / "settings.json"
    data = json.loads(settings.read_text(encoding="utf-8"))
    data["permissions"]["allow"].append("Bash(rm *)")
    write(settings, json.dumps(data, indent=2))
    result = gate.run_gate(root, "0001", "c")
    assert result.result == "park"
    g = next(ch for ch in result.failed if ch.name == "guardrails")
    assert ".claude/settings.json" in g.reason
    assert "clean_tree" in _names(result, False)  # and it is uncommitted
    # the run cannot grant itself the exemption by editing intent.md on the branch
    write(
        change / "intent.md",
        INTENT.replace("Entry route: idea.", "Entry route: idea.\nFramework change: yes"),
    )
    git(root, "add", ".")
    git(root, "commit", "-q", "-m", "self-declared framework change")
    verdict(root, "c")
    result = gate.run_gate(root, "0001", "c")
    g = next(ch for ch in result.failed if ch.name == "guardrails")
    assert "intent.md changed on this branch" in g.reason
    git(root, "reset", "-q", "--hard", "HEAD~1")
    # only the intent the owner merged at gate (a) can declare a framework change
    on_base(
        root,
        lambda r: write(
            r / "changes" / "0001-percent-helper" / "intent.md",
            INTENT.replace("Entry route: idea.", "Entry route: idea.\nFramework change: yes"),
        ),
        "intent: framework change (merged at gate a)",
    )
    verdict(root, "c")
    result = gate.run_gate(root, "0001", "c")
    assert "guardrails" not in _names(result, False)
    assert "clean_tree" not in _names(result, False)


def test_gate_parks_on_a_risk_list_word_until_the_owner_accepts_it(project):
    root, change = project
    write(root / "sample_pkg" / "auth.py", "TOKEN_TTL = 60\n")
    write(
        change / "plan.md",
        PLAN.replace("## Order of work", "- `sample_pkg/auth.py` — ttl\n\n## Order of work"),
    )
    git(root, "add", ".")
    git(root, "commit", "-q", "-m", "auth ttl")
    verdict(root, "c")
    result = gate.run_gate(root, "0001", "c")
    assert result.result == "park"
    r = next(ch for ch in result.failed if ch.name == "risk_list")
    assert r.details["hits"] == {"auth": ["sample_pkg/auth.py"]} and "accept-risk" in r.need
    proc = run_py(
        str(STATE_CLI),
        "accept-risk",
        "--root",
        str(root),
        "--id",
        "0001",
        "--item",
        "auth",
        cwd=root,
    )
    assert proc.returncode == 0 and json.loads(proc.stdout)["risk_accepted"] == ["auth"]
    # the acceptance is the owner's and counts only once they committed it (step 24.5)
    result = gate.run_gate(root, "0001", "c")
    assert result.result == "park" and "owner_actions" in _names(result, False)
    git(root, "add", ".")
    git(root, "commit", "-q", "-m", "owner: accept the auth risk for change 0001")
    verdict(root, "c")
    assert gate.run_gate(root, "0001", "c").result == "continue"


def test_gate_parks_on_escalate_missing_or_stale_verdict(project):
    root, change = project
    result = gate.run_gate(root, "0001", "c")
    assert result.result == "park"
    assert "missing" in next(ch for ch in result.failed if ch.name == "adversarial_review").reason
    verdict(root, "c", "escalate", "non-routine")
    result = gate.run_gate(root, "0001", "c")
    a = next(ch for ch in result.failed if ch.name == "adversarial_review")
    assert "escalate" in a.reason and "blast radius" in a.reason
    verdict(root, "c", head="0000000000deadbeef")
    a = next(
        ch for ch in gate.run_gate(root, "0001", "c").failed if ch.name == "adversarial_review"
    )
    assert a.details.get("stale") is True


def test_gate_parks_on_open_concern_and_unsynced_commit(project):
    root, change = project
    write(change / "spec.md", SPEC.replace("- [x] Rounding", "- [ ] Rounding"))
    write(root / "sample_pkg" / "helper.py", "y = 2\n")
    git(root, "add", ".")
    git(root, "commit", "-q", "-m", "departure without plan.md")
    verdict(root, "c")
    result = gate.run_gate(root, "0001", "c")
    names = _names(result, False)
    assert "open_concerns" in names and "plan_sync" in names
    p = next(ch for ch in result.failed if ch.name == "plan_sync")
    assert (
        p.details["unplanned"] == ["sample_pkg/helper.py"]
        and len(p.details["unsynced_commits"]) == 1
    )


def test_gate_phase_d_requires_evidence_and_findings_at_e(project):
    root, change = project
    with pytest.raises(gate.GateError, match="in phase \\(c\\); gate \\(d\\)"):
        gate.run_gate(root, "0001", "d")  # the phase must be set before its gate runs
    st = status_mod.read_status(change)
    st.set_phase("d")
    status_mod.write_status(change, st)
    verdict(root, "d")
    result = gate.run_gate(root, "0001", "d")
    limits_check = result.checks[0]
    assert not limits_check.ok and "did not register its start" in limits_check.reason
    start_run(root, "d")
    result = gate.run_gate(root, "0001", "d")
    ev = next(ch for ch in result.failed if ch.name == "evidence")
    assert ev.details["missing"] == ["test.log", "build.log", "lint.log"]
    for name in ("test.log", "build.log", "lint.log"):
        write(change / "evidence" / name, "ok\n")  # no collector header: not evidence
    ev = next(ch for ch in gate.run_gate(root, "0001", "d").failed if ch.name == "evidence")
    assert "collector header" in ev.reason
    write_logs(change)
    assert gate.run_gate(root, "0001", "d").result == "continue"
    # gate (e) is human; the findings JSON is mandatory there, tied to HEAD, and Important
    # findings park
    st = status_mod.read_status(change)
    st.set_phase("e")
    status_mod.write_status(change, st)
    result = gate.run_gate(root, "0001", "e")
    assert result.result == "park" and "findings" in _names(result, False)
    head = git(root, "rev-parse", "HEAD").strip()
    findings = change / "evidence" / "review-findings.json"
    write(findings, json.dumps({"findings": [{"severity": "nit", "summary": "naming"}]}))
    f = next(ch for ch in gate.run_gate(root, "0001", "e").failed if ch.name == "findings")
    assert "no 'head'" in f.reason
    write(findings, json.dumps({"findings": [], "head": "0000000000deadbeef"}))
    f = next(ch for ch in gate.run_gate(root, "0001", "e").failed if ch.name == "findings")
    assert f.details.get("stale") is True
    write(
        findings,
        json.dumps({"findings": [{"severity": "nit", "summary": "naming"}], "head": head}),
    )
    result = gate.run_gate(root, "0001", "e")
    assert result.result == "wait" and result.label == "sdlc:e-ready", result.reason
    write(
        findings,
        json.dumps({"findings": [{"severity": "important", "summary": "leaks PII"}], "head": head}),
    )
    assert "findings" in _names(gate.run_gate(root, "0001", "e"), False)


def test_gate_parks_on_iteration_cap_and_pause_flag(project):
    root, change = project
    verdict(root, "c")
    st = status_mod.read_status(change)
    st.iterations = 4
    status_mod.write_status(change, st)
    result = gate.run_gate(root, "0001", "c")
    assert result.result == "park" and [ch.name for ch in result.checks] == ["limits"]
    proc = run_py(
        str(GATE_CLI),
        "set-iterations",
        "--root",
        str(root),
        "--id",
        "0001",
        "--count",
        "0",
        cwd=root,
    )
    assert proc.returncode == 0
    text = (root / "sdlc.yaml").read_text(encoding="utf-8")
    assert "paused: false" in text  # written by /sdlc-init from the template
    write(root / "sdlc.yaml", text.replace("paused: false", "paused: true"))
    result = gate.run_gate(root, "0001", "c")
    # an sdlc.yaml edited on the branch is ignored for limits (the base copy rules) and is
    # itself a guardrail hit; the pause flag counts once the owner merged it
    assert result.config_note.startswith("sdlc.yaml changed on the branch")
    assert "paused" not in result.reason and "guardrails" in _names(result, False)
    git(root, "checkout", "-q", "--", "sdlc.yaml")
    on_base(
        root,
        lambda r: write(
            r / "sdlc.yaml",
            (r / "sdlc.yaml").read_text(encoding="utf-8").replace("paused: false", "paused: true"),
        ),
        "pause",
    )
    verdict(root, "c")
    result = gate.run_gate(root, "0001", "c")
    assert result.result == "park" and "paused" in result.reason


def test_gate_cli_exit_codes_and_run_files(project):
    root, change = project
    proc = run_py(
        str(GATE_CLI), "check", "--root", str(root), "--id", "0001", "--phase", "c", cwd=root
    )
    assert proc.returncode == 4, proc.stderr
    out = json.loads(proc.stdout)
    assert out["result"] == "park" and "What I need from you" in proc.stderr
    verdict(root, "c")
    proc = run_py(
        str(GATE_CLI), "start-run", "--root", str(root), "--id", "0001", "--phase", "c", cwd=root
    )
    assert proc.returncode == 0 and (change / "evidence" / "run-c.json").exists()
    proc = run_py(
        str(GATE_CLI),
        "record-spend",
        "--root",
        str(root),
        "--id",
        "0001",
        "--phase",
        "c",
        "--usd",
        "0.4",
        cwd=root,
    )
    assert proc.returncode == 0 and json.loads(proc.stdout)["spend_usd"] == 0.4
    proc = run_py(
        str(GATE_CLI), "check", "--root", str(root), "--id", "0001", "--phase", "c", cwd=root
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert json.loads(proc.stdout)["result"] == "continue"
    proc = run_py(
        str(GATE_CLI), "check", "--root", str(root), "--id", "0009", "--phase", "c", cwd=root
    )
    assert proc.returncode == 2


def test_gate_refuses_without_sdlc_yaml(tmp_path):
    change_dir, _ = status_mod.new_change(tmp_path, "x")
    with pytest.raises(gate.GateError):
        gate.run_gate(tmp_path, "0001", "a")


def test_gate_cli_main_dry_run(project, capsys):
    root, _ = project
    verdict(root, "c")
    rc = gate_cli.main(["check", "--root", str(root), "--id", "0001", "--phase", "c", "--dry-run"])
    assert rc == 0 and json.loads(capsys.readouterr().out)["dry_run"] is True


def test_sdlc_yaml_gate_block_is_read_from_the_base(project):
    root, change = project
    text = (root / "sdlc.yaml").read_text(encoding="utf-8")
    cfg = yamlish.load_file(root / "sdlc.yaml")["gate"]
    assert cfg["max_iterations"] == 3 and cfg["max_budget_usd"] is None
    st = status_mod.read_status(change)
    st.iterations = 5
    status_mod.write_status(change, st)
    verdict(root, "c")
    # relaxing the cap in the working tree changes nothing: the base copy rules
    write(root / "sdlc.yaml", text.replace("max_iterations: 3", "max_iterations: 5"))
    result = gate.run_gate(root, "0001", "c", dry_run=True)
    assert result.checks[0].name == "limits" and not result.checks[0].ok
    assert result.checks[0].details["cap"] == 3 and result.config_note
    git(root, "checkout", "-q", "--", "sdlc.yaml")
    # the owner raising it on main (merged into the branch) does
    on_base(
        root,
        lambda r: write(
            r / "sdlc.yaml",
            (r / "sdlc.yaml")
            .read_text(encoding="utf-8")
            .replace("max_iterations: 3", "max_iterations: 5"),
        ),
        "raise the cap",
    )
    verdict(root, "c")
    result = gate.run_gate(root, "0001", "c", dry_run=True)
    assert result.checks[0].ok and result.checks[0].details["cap"] == 5 and not result.config_note
    assert result.result == "continue", result.reason


def test_gate_parks_on_uncommitted_work_outside_the_change_folder(project):
    root, change = project
    verdict(root, "c")
    write(root / "sample_pkg" / "scratch.py", "x = 1\n")
    result = gate.run_gate(root, "0001", "c", dry_run=True)
    ct = next(ch for ch in result.failed if ch.name == "clean_tree")
    assert ct.details["dirty"] == ["sample_pkg/scratch.py"]
    (root / "sample_pkg" / "scratch.py").unlink()
    write(change / "evidence" / "note.md", "inside the change folder: fine\n")
    assert "clean_tree" not in _names(gate.run_gate(root, "0001", "c", dry_run=True), False)


def test_run_command_timeout_kills_the_whole_tree(tmp_path):
    started = datetime.now(timezone.utc)
    run = checks.run_command(f'"{sys.executable}" -c "import time; time.sleep(30)"', tmp_path, 1)
    assert run["exit_code"] is None and run["timeout"] == 1
    assert (datetime.now(timezone.utc) - started).total_seconds() < 20
    run = checks.run_command(f'"{sys.executable}" -c "print(42)"', tmp_path, 10)
    assert run["exit_code"] == 0 and "42" in run["output"]


def test_gate_cli_rejects_a_malformed_id(project):
    root, _ = project
    proc = run_py(
        str(GATE_CLI), "check", "--root", str(root), "--id", "x", "--phase", "c", cwd=root
    )
    assert proc.returncode == 2 and "four digits" in proc.stderr


# --- gate (b): the design gate (steps 22-23) ---------------------------------------------------
def test_gate_b_waits_for_the_owner_and_lite_continues(design_project):
    root, change = design_project
    verdict(root, "b")
    result = gate.run_gate(root, "0001", "b", dry_run=True)
    assert result.result == "wait", result.reason
    assert result.label == "sdlc:b-ready" and result.profile == "standard"
    assert _names(result, False) == []
    assert set(_names(result, True)) == {
        "limits",
        "artifacts",
        "design_scope",
        "open_concerns",
        "commands",
        "guardrails",
        "risk_list",
        "owner_actions",
        "adversarial_review",
    }
    # Lite gate-checks (b) instead of asking the owner (23.3; conventions.HUMAN_GATES)
    st = status_mod.read_status(change)
    st.profile_override = "lite"
    status_mod.write_status(change, st)
    result = gate.run_gate(root, "0001", "b", dry_run=True)
    assert result.result == "continue", result.reason
    assert result.label is None and result.profile == "lite" and result.human_gate is False


def test_gate_b_parks_on_a_spec_without_the_header(design_project):
    root, change = design_project
    verdict(root, "b")
    write(change / "spec.md", SPEC_BODY)  # the five sections, no header line
    result = gate.run_gate(root, "0001", "b", dry_run=True)
    assert result.result == "park"
    a = next(ch for ch in result.failed if ch.name == "artifacts")
    assert "spec.md header lacks Change id:, Produced by:" in a.reason
    assert any("header" in p for p in a.details["problems"])


def test_gate_b_parks_when_the_branch_touches_source(design_project):
    root, _change = design_project
    verdict(root, "b")
    assert "design_scope" not in _names(gate.run_gate(root, "0001", "b", dry_run=True), False)
    # the plan run of phase (b) is read-only on source (decision 2; OPERATING_MODEL section 8)
    write(root / "sample_pkg" / "percent.py", PERCENT)
    git(root, "add", "sample_pkg/percent.py")
    git(root, "commit", "-q", "-m", "implementation written in the design phase")
    verdict(root, "b")
    result = gate.run_gate(root, "0001", "b", dry_run=True)
    assert result.result == "park"
    ds = next(ch for ch in result.failed if ch.name == "design_scope")
    assert ds.details["outside"] == ["sample_pkg/percent.py"]
    assert "phase (c)" in ds.need and "changes/0001-percent-helper/" in ds.need
    # the same tree with only changes/** in the diff passes
    git(root, "reset", "-q", "--hard", "HEAD~1")
    verdict(root, "b")
    result = gate.run_gate(root, "0001", "b", dry_run=True)
    assert "design_scope" not in _names(result, False) and result.result == "wait", result.reason


def test_gate_b_ignores_the_sandbox_placeholders_but_not_a_stray_file(design_project):
    """Claude Code's sandbox leaves empty placeholder entries (.bashrc, .vscode/) in the
    working directory; the first live design run (2026-09-21) parked on them. They are
    untracked and empty, so design_scope looks past them - an untracked file with content
    outside the change folder is still a departure from phase (b)."""
    root, _change = design_project
    (root / ".bashrc").write_text("", encoding="utf-8")  # zero bytes: a placeholder
    (root / ".vscode").mkdir()  # empty directory: a placeholder
    verdict(root, "b")
    result = gate.run_gate(root, "0001", "b", dry_run=True)
    assert "design_scope" not in _names(result, False), result.reason
    ds = next(ch for ch in result.checks if ch.name == "design_scope")
    assert ".bashrc" in ds.details["ignored"]
    assert result.result == "wait"

    write(root / "stray.py", "x = 1\n")  # untracked but not empty: a real stray
    verdict(root, "b")
    result = gate.run_gate(root, "0001", "b", dry_run=True)
    assert result.result == "park"
    ds = next(ch for ch in result.failed if ch.name == "design_scope")
    assert ds.details["outside"] == ["stray.py"] and ".bashrc" in ds.details["ignored"]


def test_clean_tree_ignores_the_sandbox_placeholders_but_not_a_stray_file(project):
    """The same placeholders would fail clean_tree at gates (c), (d) and (e)."""
    root, _change = project
    (root / ".bashrc").write_text("", encoding="utf-8")
    (root / ".idea").mkdir()
    verdict(root, "c")
    result = gate.run_gate(root, "0001", "c", dry_run=True)
    assert "clean_tree" not in _names(result, False), result.reason
    ct = next(ch for ch in result.checks if ch.name == "clean_tree")
    assert ct.details["ignored"] == [".bashrc"]  # `git status -uall` never names an empty dir
    assert checks.diffmod.sandbox_placeholders(root, [".idea/"]) == [".idea/"]

    write(root / "stray.py", "x = 1\n")
    result = gate.run_gate(root, "0001", "c", dry_run=True)
    ct = next(ch for ch in result.failed if ch.name == "clean_tree")
    assert ct.details["dirty"] == ["stray.py"]


def test_a_committed_empty_file_is_still_part_of_the_diff(design_project):
    """Only untracked entries are treated as placeholders: an empty file the phase committed
    is a change like any other (ctx.diff.files keeps its meaning for committed work)."""
    root, _change = design_project
    write(root / "sample_pkg" / "marker.py", "")
    git(root, "add", "sample_pkg/marker.py")
    git(root, "commit", "-q", "-m", "an empty module, committed")
    verdict(root, "b")
    result = gate.run_gate(root, "0001", "b", dry_run=True)
    ds = next(ch for ch in result.failed if ch.name == "design_scope")
    assert ds.details["outside"] == ["sample_pkg/marker.py"]


def test_gate_cli_spec_header(project, capsys, tmp_path):
    root, change = project
    rc = gate_cli.main(["spec-header", "--root", str(root), "--id", "0001"])
    assert rc == 0
    out = json.loads(capsys.readouterr().out)
    assert out["title"] == "percent helper"  # from intent.md, not the status.yaml title
    assert out["change_id"] == "0001" and out["prompt_version"] == "v1"
    assert out["plugin_version"] == yamlish.load_file(root / "sdlc.yaml")["plugin"]["version"]
    assert out["skills"] == list(preflight.POLICY_SKILLS) and out["overrides"] == []
    assert out["header"] == SPEC_HEADER
    # a project skill under .claude/skills/ overrides the plugin's policy skill (step 20)
    write(root / ".claude" / "skills" / "coding-standards" / "SKILL.md", "# ours\n")
    rc = gate_cli.main(["spec-header", "--root", str(root), "--id", "0001"])
    out = json.loads(capsys.readouterr().out)
    assert rc == 0 and out["overrides"] == ["coding-standards"]
    assert out["header"].endswith("overrides: coding-standards")
    # no intent.md: the title falls back to status.yaml
    (change / "intent.md").unlink()
    gate_cli.main(["spec-header", "--root", str(root), "--id", "0001"])
    assert json.loads(capsys.readouterr().out)["title"] == "Percent helper"
    assert gate_cli.main(["spec-header", "--root", str(root), "--id", "0009"]) == 2
    # a project without the sdlc.yaml pin: the installed plugin's manifest answers
    bare = tmp_path / "bare"
    status_mod.new_change(bare, "Other change")
    rc = gate_cli.main(
        ["spec-header", "--root", str(bare), "--id", "0001", "--plugin-root", str(ROOT)]
    )
    assert rc == 0 and json.loads(capsys.readouterr().out)["plugin_version"] == PLUGIN_VERSION


# --- step 24.3: bump-iteration ------------------------------------------------------------
def bump(root: Path) -> tuple[int, dict]:
    proc = run_py(str(GATE_CLI), "bump-iteration", "--root", str(root), "--id", "0001", cwd=root)
    return proc.returncode, (json.loads(proc.stdout) if proc.stdout.strip() else {})


def test_gate_cli_bump_iteration_counts_rounds_and_reports_the_cap(project):
    """Every fix round of a phase run counts (OPERATING_MODEL section 4.1); the command exits
    3 once the count is past the cap the gate would park on."""
    root, change = project
    for expected in (1, 2, 3):
        rc, out = bump(root)
        assert rc == 0, out
        assert out == {
            "iterations": expected,
            "cap": 3,
            "cap_reached": False,
            "classification": None,
        }
        assert status_mod.read_status(change).iterations == expected
    rc, out = bump(root)
    assert rc == 3 and out["iterations"] == 4 and out["cap_reached"] is True
    # and the gate agrees: the same count parks the change
    verdict(root, "c")
    assert gate.run_gate(root, "0001", "c", dry_run=True).result == "park"
    # a non-routine plan tightens the cap (step 19)
    assert (
        gate_cli.main(["set-iterations", "--root", str(root), "--id", "0001", "--count", "1"]) == 0
    )
    verdict(root, "c", classification="non-routine")
    rc, out = bump(root)
    assert rc == 0 and out == {
        "iterations": 2,
        "cap": 2,
        "cap_reached": False,
        "classification": "non-routine",
    }
    rc, out = bump(root)
    assert rc == 3 and out["cap"] == 2 and out["cap_reached"] is True
    proc = run_py(str(GATE_CLI), "bump-iteration", "--root", str(root), "--id", "0009", cwd=root)
    assert proc.returncode == 2


# --- step 24.5: accept-risk and set-iterations are the owner's ------------------------------
BOT_AUTHOR = "github-actions[bot] <41898282+github-actions[bot]@users.noreply.github.com>"


def commit_all(root: Path, message: str, author: str | None = None) -> str:
    git(root, "add", ".")
    args = ["commit", "-q", "-m", message] + (["--author", author] if author else [])
    git(root, *args)
    return git(root, "rev-parse", "HEAD").strip()


def accept_risk(root: Path, change: Path, item: str = "auth") -> None:
    st = status_mod.read_status(change)
    st.accept_risk(item)
    status_mod.write_status(change, st)


def test_owner_actions_ties_a_risk_acceptance_to_the_owner(project):
    root, change = project
    verdict(root, "c")
    assert "owner_actions" not in _names(gate.run_gate(root, "0001", "c", dry_run=True), False)
    # an acceptance sitting in the working tree was committed by nobody
    accept_risk(root, change)
    result = gate.run_gate(root, "0001", "c", dry_run=True)
    oa = next(ch for ch in result.failed if ch.name == "owner_actions")
    assert "risk_accepted gained auth" in oa.reason and "in no commit" in oa.reason
    assert "a run cannot approve itself" in oa.need and "accept-risk" in oa.need
    # the owner commits it: it counts
    commit_all(root, "owner: accept the auth risk")
    verdict(root, "c")
    assert "owner_actions" not in _names(gate.run_gate(root, "0001", "c", dry_run=True), False)
    # the very same acceptance made by the automation identity does not
    git(root, "reset", "-q", "--hard", "HEAD~1")
    accept_risk(root, change)
    sha = commit_all(root, "accept the auth risk", author=BOT_AUTHOR)
    verdict(root, "c")
    result = gate.run_gate(root, "0001", "c", dry_run=True)
    assert result.result == "park" and result.label == "sdlc:needs-human"
    oa = next(ch for ch in result.failed if ch.name == "owner_actions")
    assert f"commit {sha[:10]}" in oa.reason and "github-actions[bot]" in oa.reason
    assert "risk_accepted" in oa.reason
    assert oa.details["automation_identity"] == policy.DEFAULT_AUTOMATION_IDENTITY


def test_owner_actions_parks_on_an_iteration_reset_by_the_automation_identity(project):
    root, change = project
    st = status_mod.read_status(change)
    st.iterations = 2  # two fix rounds, counted by the run itself: that is not owner state
    status_mod.write_status(change, st)
    commit_all(root, "build(0001): two fix rounds")
    verdict(root, "c")
    assert "owner_actions" not in _names(gate.run_gate(root, "0001", "c", dry_run=True), False)
    # the reset itself is the owner's act: uncommitted it belongs to nobody
    assert (
        gate_cli.main(["set-iterations", "--root", str(root), "--id", "0001", "--count", "0"]) == 0
    )
    result = gate.run_gate(root, "0001", "c", dry_run=True)
    oa = next(ch for ch in result.failed if ch.name == "owner_actions")
    assert "iterations dropped from 2 to 0" in oa.reason and "in no commit" in oa.reason
    # committed by the automation identity it is still not the owner's
    sha = commit_all(root, "reset the iteration count", author=BOT_AUTHOR)
    verdict(root, "c")
    result = gate.run_gate(root, "0001", "c", dry_run=True)
    assert result.result == "park"
    oa = next(ch for ch in result.failed if ch.name == "owner_actions")
    assert f"iterations dropped from 2 to 0 in commit {sha[:10]}" in oa.reason
    # the owner's own commit passes
    git(root, "reset", "-q", "--hard", "HEAD~1")
    assert (
        gate_cli.main(["set-iterations", "--root", str(root), "--id", "0001", "--count", "0"]) == 0
    )
    commit_all(root, "owner: allow another round")
    verdict(root, "c")
    assert gate.run_gate(root, "0001", "c", dry_run=True).result == "continue"


# --- step 24.4: the fixture states of gates (c), (d) and (e) --------------------------------
def write_logs(change: Path, red: str | None = None) -> None:
    """The three command logs exactly as plugin/evidence/collect.py writes them."""
    for target, name in art.EVIDENCE_TARGETS.items():
        code = 1 if target == red else 0
        header = art.render_evidence_header(
            f"python -m {target}", code, 1.2, "2026-09-21T10:00:00Z"
        )
        body = "42 passed\n" if code == 0 else "E   assert percent(1, 3) == 33.3\n1 failed\n"
        write(change / "evidence" / name, header + "\n" + body)


def set_phase(change: Path, phase: str) -> None:
    st = status_mod.read_status(change)
    st.set_phase(phase)
    status_mod.write_status(change, st)


def test_gate_c_parks_without_the_verifier_report(project):
    """The continue case is test_gate_continues_on_a_clean_change; this is its mirror: the
    only evidence gate (c) requires is the verifier report (artifacts.REQUIRED_EVIDENCE)."""
    root, change = project
    verdict(root, "c")
    (change / "evidence" / art.EVIDENCE_VERIFIER).unlink()
    result = gate.run_gate(root, "0001", "c")
    assert result.result == "park" and result.label == "sdlc:needs-human"
    ev = next(ch for ch in result.failed if ch.name == "evidence")
    assert ev.details["missing"] == ["verifier.md"]
    assert "changes/0001-percent-helper/evidence/verifier.md" in ev.need
    assert "verifier.md" in result.what_i_need()
    assert status_mod.read_status(change).gate.result == "parked"


def test_gate_d_continues_on_green_logs_and_parks_on_a_red_test_log(project):
    root, change = project
    set_phase(change, "d")
    start_run(root, "d")
    write_logs(change)
    verdict(root, "d")
    result = gate.run_gate(root, "0001", "d", dry_run=True)
    assert result.result == "continue", result.reason
    assert result.label is None and result.human_gate is False
    assert "evidence" in _names(result, True)
    # a red log parks the change even though the gate's own re-run of the suite is green
    write_logs(change, red="test")
    result = gate.run_gate(root, "0001", "d")
    assert result.result == "park" and result.label == "sdlc:needs-human"
    ev = next(ch for ch in result.failed if ch.name == "evidence")
    assert "evidence/test.log" in ev.reason and "exited 1" in ev.reason
    assert ev.details["red_files"] == ["test.log"]
    assert "changes/0001-percent-helper/evidence/test.log" in ev.need
    assert "commands" not in _names(result, False)  # the project's own targets are green
    assert "test.log" in result.what_i_need()


def test_gate_e_waits_for_the_owner_and_parks_on_an_important_finding(project):
    root, change = project
    set_phase(change, "e")
    start_run(root, "e")
    write_logs(change)
    head = git(root, "rev-parse", "HEAD").strip()
    findings = change / "evidence" / art.REVIEW_FINDINGS
    write(
        findings,
        json.dumps(
            {"head": head, "findings": [{"severity": "nit", "summary": "naming"}], "tally": {}}
        ),
    )
    result = gate.run_gate(root, "0001", "e", dry_run=True)
    assert result.result == "wait", result.reason
    assert result.label == "sdlc:e-ready" and result.human_gate is True
    assert _names(result, False) == []
    write(
        findings,
        json.dumps(
            {
                "head": head,
                "findings": [{"severity": "important", "summary": "leaks PII", "file": "x.py"}],
            }
        ),
    )
    result = gate.run_gate(root, "0001", "e")
    assert result.result == "park" and result.label == "sdlc:needs-human"
    f = next(ch for ch in result.failed if ch.name == "findings")
    assert "1 Important review finding(s) open" in f.reason
    assert "changes/0001-percent-helper/evidence/review-findings.json" in f.need
    assert "review-findings.json" in result.what_i_need()
