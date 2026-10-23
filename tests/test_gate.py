"""Layer-1 tests for plugin/gate: artifact contracts, risk matching, findings and verdict
readers, run limits — and, against a temporary copy of the fixture project, the gate itself:
`continue` on a clean change, `wait` at a human gate, `park` with the right reason for each
prepared failure (missing plan.md, failing test behind SAMPLE_FAIL=1, a diff touching
.claude/settings.json, a risk-list word, an escalating or stale adversarial verdict, an open
flagged concern, a limit hit), and gate (b): a spec.md without its rendered header or a design
branch that touches source parks, while a clean one waits for the owner."""

from __future__ import annotations

import json
import os
import shutil
import stat
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
from tests import fixture_repos
from tests.model_records import write_reviewer_record

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
    }
    path = (
        root / "changes" / "0001-percent-helper" / "evidence" / f"adversarial-review-{phase}.json"
    )
    write(path, json.dumps(data))
    write_reviewer_record(path, head)  # what the panel_blind hook writes beside it (R7)
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


def set_on_base(root: Path, change: Path, **fields) -> None:
    """Set ``status.yaml`` fields the way the owner does — a commit on main merged into the
    current branch — so the gate reads them from the copy the owner approved (0.2.26: the
    overrides on the branch are ignored). The working tree's other changes are kept aside."""
    branch = git(root, "rev-parse", "--abbrev-ref", "HEAD").strip()
    dirty = bool(git(root, "status", "--porcelain").strip())
    if dirty:
        git(root, "stash", "push", "-q", "-u")
    git(root, "checkout", "-q", "main")
    st = status_mod.read_status(change)
    for name, value in fields.items():
        setattr(st, name, value)
    status_mod.write_status(change, st)
    git(root, "add", "--", str(change.relative_to(root) / "status.yaml"))
    git(root, "commit", "-q", "-m", f"owner: {', '.join(f'{k}={v}' for k, v in fields.items())}")
    git(root, "checkout", "-q", branch)
    git(root, "merge", "-q", "--no-edit", "main")
    if dirty:
        git(root, "stash", "pop", "-q")


def start_run(root: Path, phase: str) -> None:
    proc = run_py(
        str(GATE_CLI), "start-run", "--root", str(root), "--id", "0001", "--phase", phase, cwd=root
    )
    assert proc.returncode == 0, proc.stderr


def _initialised_fixture(tmp_path) -> tuple[Path, Path]:
    """A fixture copy on main with /sdlc-init merged and change 0001 created with its intent
    (uncommitted): the common ground of the phase-(b) and phase-(c) states below."""
    fixture_repos.copy("gate-initialised", tmp_path, _build_initialised)
    root = tmp_path / "proj"
    return root, root / "changes" / "0001-percent-helper"


def _build_initialised(base: Path) -> None:
    root = base / "proj"
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


@pytest.fixture
def project(tmp_path):
    """Fixture copy initialised (standard profile), change 0001 through (b), and a phase-(c)
    branch with the implementation committed together with plan.md."""
    fixture_repos.copy("gate-project", tmp_path, _build_project)
    root = tmp_path / "proj"
    start_run(root, "c")  # the runbook registers the run before the work (step 19)
    return root, root / "changes" / "0001-percent-helper"


def _build_project(base: Path) -> None:
    root, change = _initialised_fixture(base)
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


@pytest.fixture
def design_project(tmp_path):
    """Fixture copy initialised, the intent merged on main (as if the (a) PR did), and the
    phase-(b) branch carrying only spec.md and plan.md — the state gate (b) judges."""
    fixture_repos.copy("gate-design-project", tmp_path, _build_design_project)
    root = tmp_path / "proj"
    start_run(root, "b")
    return root, root / "changes" / "0001-percent-helper"


def _build_design_project(base: Path) -> None:
    root, change = _initialised_fixture(base)
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
def _ctx(tmp_path, config=None, iterations=0, phase="c", entry_route="idea"):
    change_dir = tmp_path / "changes" / "0001-x"
    (change_dir / "evidence").mkdir(parents=True, exist_ok=True)
    st = status_mod.Status(
        id="0001", slug="x", title="x", phase=phase, iterations=iterations, entry_route=entry_route
    )
    # human_gate=True: these unit tests isolate the caps; run registration is tested on the fixture
    return checks.GateContext(tmp_path, change_dir, phase, st, config or {}, None, True, "no git")


def test_limits_pause_flag_stops_everything(tmp_path):
    res = limits.check_limits(_ctx(tmp_path, {"paused": True}))
    assert not res.ok and res.details["stop"] and "paused" in res.reason


def test_limits_fail_closed_on_a_pause_flag_that_is_not_a_boolean(tmp_path):
    """``paused: yes`` is the string "yes" to YAML 1.2 and every reader tested ``is True``:
    the flag paused nothing (1.0.0 readiness review, group A)."""
    for value in ("yes", "on", "true", 1):
        res = limits.check_limits(_ctx(tmp_path, {"paused": value}))
        assert not res.ok and res.details["stop"], value
        assert f"sdlc.yaml: paused is {value!r}, not a boolean" in res.reason
    assert limits.check_limits(_ctx(tmp_path, {"paused": None})).ok
    assert limits.check_limits(_ctx(tmp_path, {"paused": False})).ok


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


def test_the_cap_is_described_as_per_change_everywhere():
    """sdlc.yaml's comment said "per phase" while the contract (OPERATING_MODEL section 4.1)
    and the code count per change; a session took the comment at its word (2026-09-23)."""
    for rel in ("template/sdlc.yaml", "plugin/gate/limits.py", "docs/BUILD_GUIDE.md"):
        text = (ROOT / rel).read_text(encoding="utf-8")
        assert "fix iterations per change" in text, rel
        assert "iterations per phase" not in text, rel


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


def test_the_build_caps_and_their_fallback_rule():
    """Decision 32 (1.0.8): the build run and every fix round get ``build_max_turns`` (400)
    and ``build_max_wall_clock_minutes`` (180); an unset or invalid build key is the larger
    of the general setting and the build default, so no project's cap goes down."""
    caps = limits.run_caps
    # unset
    assert caps({}, False) == (200, 120) and caps({}, True) == (400, 180)
    assert caps(None, True) == (400, 180) and caps("not a block", False) == (200, 120)
    # general only, below and above the build default (this repository's root: 400)
    assert caps({"max_turns": 300, "max_wall_clock_minutes": 90}, True) == (400, 180)
    assert (
        caps({"max_turns": 400}, False) == (400, 120) and caps({"max_turns": 400}, True)[0] == 400
    )
    general = {"max_turns": 500, "max_wall_clock_minutes": 240}
    assert caps(general, False) == (500, 240) and caps(general, True) == (500, 240)
    # build only: the general caps are untouched
    build = {"build_max_turns": 250, "build_max_wall_clock_minutes": 150}
    assert caps(build, True) == (250, 150) and caps(build, False) == (200, 120)
    # both: the build key wins for the build, even below the general setting
    both = {**general, **build}
    assert caps(both, True) == (250, 150) and caps(both, False) == (500, 240)
    # invalid values fall back as if unset
    for bad in ("x", 0, -5, None, [1]):
        assert caps({"max_turns": bad, "max_wall_clock_minutes": bad}, False) == (200, 120)
        assert caps({"build_max_turns": bad, "build_max_wall_clock_minutes": bad}, True) == (
            400,
            180,
        )
        assert caps({"max_turns": 450, "build_max_turns": bad}, True)[0] == 450


def test_the_build_run_and_a_fix_round_get_the_build_wall_clock(tmp_path):
    """Decision 32: ``start-run`` records ``"run": "build"`` for the build and a fix round,
    and the wall-clock check gives that run ``build_max_wall_clock_minutes``; a record without
    the field (any other run, or one written before 1.0.8) keeps the general cap."""
    started = (datetime.now(timezone.utc) - timedelta(minutes=150)).isoformat()
    ctx = _ctx(tmp_path, phase="c")
    write(ctx.evidence_dir / "run-c.json", json.dumps({"started_at": started, "run": "build"}))
    res = limits.check_limits(ctx)
    assert res.ok, res.reason
    ctx = _ctx(tmp_path / "b", phase="b")
    write(ctx.evidence_dir / "run-b.json", json.dumps({"started_at": started}))
    res = limits.check_limits(ctx)
    assert not res.ok and res.details["max_wall_clock_minutes"] == 120
    assert "150 min elapsed, limit 120 min" in res.reason
    # a fix round at (b) carries the field: the build cap, with the owner's own setting
    write(ctx.evidence_dir / "run-b.json", json.dumps({"started_at": started, "run": "build"}))
    assert limits.check_limits(ctx).ok
    ctx.config["gate"] = {"build_max_wall_clock_minutes": 140}
    res = limits.check_limits(ctx)
    assert not res.ok and "limit 140 min" in res.reason


def test_start_run_records_the_build_run_and_a_fix_round(tmp_path, monkeypatch, capsys):
    """``"run": "build"`` for ``--phase c``, for any phase under ``SDLC_RUN=fix`` (the runner
    marks the fix session) and for ``--run fix|build`` (a by-hand run); none otherwise."""
    change_dir, _st = status_mod.new_change(tmp_path, "x")
    monkeypatch.delenv(limits.RUN_KIND_ENV, raising=False)

    def started(phase: str, *flags: str) -> dict:
        argv = ["start-run", "--root", str(tmp_path), "--id", "0001", "--phase", phase, *flags]
        assert gate_cli.main(argv) == 0
        capsys.readouterr()
        path = change_dir / "evidence" / f"run-{phase}.json"
        return json.loads(path.read_text(encoding="utf-8"))

    assert started("c")["run"] == "build"
    for phase in ("b", "d", "e"):
        assert "run" not in started(phase), phase
    assert started("d", "--run", "fix")["run"] == "build"
    assert started("e", "--run", "build")["run"] == "build"
    monkeypatch.setenv(limits.RUN_KIND_ENV, "fix")
    for phase in ("a", "b", "c", "d", "e"):
        assert started(phase)["run"] == "build", phase
    monkeypatch.setenv(limits.RUN_KIND_ENV, "something else")
    assert "run" not in started("b")


def _stored(evidence: Path, source: str, usd) -> None:
    """The runner's stored result of one session: M8 (R25, 1.0.26) rebuilds the change's
    spend from these, never from ``evidence/spend.json``, which the session can write."""
    write(evidence / source, json.dumps({"total_cost_usd": usd}))


def test_the_budget_binds_the_change_s_running_total_not_the_last_session(tmp_path):
    """Issue #71 (0.3.1): ``max_budget_usd`` is documented per change, but the cap was compared
    with the last session's figure, which ``start-run`` reset and ``record-spend`` overwrote:
    sample change 0002 cost almost four times a cap of 5 with no park. Two sessions below the
    cap whose sum exceeds it now park."""
    ctx = _ctx(tmp_path, {"gate": {"max_budget_usd": 2}})
    write(ctx.evidence_dir / "run-c.json", json.dumps({"spend_usd": 1.5}))
    ledger = limits.record_spend_entry(ctx.evidence_dir, "c", "claude-c.json", 1.5)
    _stored(ctx.evidence_dir, "claude-c.json", 1.5)
    assert ledger["total_usd"] == 1.5 and limits.check_limits(ctx).ok
    ledger = limits.record_spend_entry(ctx.evidence_dir, "c", "claude-c-2.json", 1.5)
    _stored(ctx.evidence_dir, "claude-c-2.json", 1.5)
    assert ledger["total_usd"] == 3.0
    res = limits.check_limits(ctx)
    assert not res.ok and res.details["stop"]
    assert res.reason == (
        "budget exceeded: 3.00 USD spent on the change (this run 1.50), budget 2.00 USD"
    )
    assert res.details["spend_usd"] == 1.5 and res.details["spend_usd_total"] == 3.0
    assert res.details["spend_entries"] == 2
    # the cap is the change's, not the phase's: a (b) session's spend counts at (c)
    assert limits.read_spend_ledger(_ctx(tmp_path, phase="b").evidence_dir)["total_usd"] == 3.0
    # M8: an emptied ledger changes nothing, the stored results still count
    (ctx.evidence_dir / limits.SPEND_FILE).unlink()
    assert not limits.check_limits(ctx).ok
    # without stored results (a by-hand run) the run record's figure still binds
    for name in ("claude-c.json", "claude-c-2.json"):
        (ctx.evidence_dir / name).unlink()
    assert limits.check_limits(ctx).ok
    write(ctx.evidence_dir / "run-c.json", json.dumps({"spend_usd": 2.5}))
    res = limits.check_limits(ctx)
    assert not res.ok and res.details["spend_usd_total"] == 2.5
    assert res.details["spend_entries"] == 0


def test_the_review_pass_and_each_fix_round_are_their_own_spend_entries(tmp_path):
    """Issue #71: the review pass's cost went to run-e.json and the (e) session's start-run
    wiped it; a fix round's cost replaced the phase's. Each is an entry now, keyed by the
    stored result, so a repeated record of one session replaces its entry, never doubles it."""
    ctx = _ctx(tmp_path, {"gate": {"max_budget_usd": 5}}, phase="e")
    evidence = ctx.evidence_dir
    limits.record_spend_entry(evidence, "d", "claude-d.json", 1.0, at="2026-10-02T10:00:00Z")
    limits.record_spend_entry(evidence, "review", "claude-review.json", 0.65)
    limits.record_spend_entry(evidence, "e", "claude-e.json", 2.04)
    limits.record_spend_entry(evidence, "fix", "claude-fix.json", 0.9)
    limits.record_spend_entry(evidence, "fix", "claude-fix-2.json", 0.5)
    for source, usd in (("claude-d.json", 1.0), ("claude-review.json", 0.65),
                        ("claude-e.json", 2.04), ("claude-fix.json", 0.9),
                        ("claude-fix-2.json", 0.5)):  # fmt: skip
        _stored(evidence, source, usd)
    ledger = limits.read_spend_ledger(evidence)
    assert [(e["run"], e["source"]) for e in ledger["entries"]] == [
        ("d", "claude-d.json"),
        ("review", "claude-review.json"),
        ("e", "claude-e.json"),
        ("fix", "claude-fix.json"),
        ("fix", "claude-fix-2.json"),
    ]
    assert ledger["total_usd"] == 5.09 and ledger["entries"][0]["at"] == "2026-10-02T10:00:00Z"
    assert not limits.check_limits(ctx).ok
    # the same session recorded again (a repeated step): its entry is replaced
    ledger = limits.record_spend_entry(evidence, "fix", "claude-fix-2.json", 0.4)
    _stored(evidence, "claude-fix-2.json", 0.4)
    assert len(ledger["entries"]) == 5 and ledger["total_usd"] == 4.99
    assert limits.check_limits(ctx).ok
    stored = json.loads((evidence / "spend.json").read_text(encoding="utf-8"))
    assert stored["total_usd"] == 4.99 and len(stored["entries"]) == 5
    # a ledger that is not a ledger counts nothing (the run record still does)
    write(evidence / "spend.json", "{not json")
    assert limits.read_spend_ledger(evidence) == {"total_usd": 0.0, "entries": []}


def test_a_spend_figure_is_finite_and_non_negative_and_zero_counts(tmp_path):
    """The review of the 0.3.1 diff, finding 5: Python's json reads ``NaN``, and one NaN
    entry made the total NaN, which no cap ever exceeds; a negative entry lowered it; a
    ``0.0`` entry was dropped. The ledger refuses the first two and keeps the third."""
    ctx = _ctx(tmp_path, {"gate": {"max_budget_usd": 0.01}})
    evidence = ctx.evidence_dir
    for bad in (float("nan"), float("inf"), -1.0, "x"):
        with pytest.raises(ValueError, match="finite, non-negative"):
            limits.record_spend_entry(evidence, "c", "bad.json", bad)
    assert limits.record_spend_entry(evidence, "c", "zero.json", 0.0)["entries"][0]["usd"] == 0.0
    limits.record_spend_entry(evidence, "c", "real.json", 0.02)
    # entries written behind the ledger's back are judged the same way on the read
    stored = json.loads((evidence / "spend.json").read_text(encoding="utf-8"))
    stored["entries"] += [
        {"run": "c", "source": "nan.json", "usd": float("nan")},
        {"run": "c", "source": "neg.json", "usd": -5},
        {"run": "c", "source": "inf.json", "usd": float("inf")},
    ]
    write(evidence / "spend.json", json.dumps(stored))  # json writes NaN and Infinity
    ledger = limits.read_spend_ledger(evidence)
    assert [e["source"] for e in ledger["entries"]] == ["zero.json", "real.json"]
    assert ledger["total_usd"] == 0.02
    # the stored results are judged the same way: no figure is counted as no figure (M8)
    for source, usd in (("claude-c.json", 0.0), ("claude-c-2.json", 0.02),
                        ("claude-c-3.json", float("nan")), ("claude-c-4.json", -5),
                        ("claude-c-5.json", float("inf"))):  # fmt: skip
        _stored(evidence, source, usd)
    assert limits.spend_from_runs(evidence)["total_usd"] == 0.02
    assert limits.spend_from_runs(evidence)["unknown"] == 3
    res = limits.check_limits(ctx)
    assert not res.ok and "budget exceeded: 0.02 USD" in res.reason
    status_mod.write_status(ctx.change_dir, ctx.status)  # the CLI reads the change's status
    proc = run_py(
        str(GATE_CLI), "record-spend", "--root", str(tmp_path), "--id", "0001", "--phase", "c",
        "--usd", "nan", cwd=tmp_path,
    )  # fmt: skip
    assert proc.returncode == 2 and "finite, non-negative" in proc.stderr


# --- the gate against the fixture --------------------------------------------------------------
def _names(result, ok):
    return sorted(ch.name for ch in result.checks if ch.ok is ok)


def test_gate_continues_on_a_clean_change(project):
    root, change = project
    verdict(root, "c")
    result = gate.run_gate(root, "0001", "c")
    assert result.result == "continue", result.reason
    assert result.label is None and result.human_gate is False
    assert _names(result, False) == []
    assert set(_names(result, True)) == {
        "limits",
        "clean_tree",
        "artifacts",
        "evidence_links",
        "open_concerns",
        "panel",
        "commands",
        "evidence",
        "findings",
        "plan_sync",
        "guardrails",
        "risk_list",
        "owner_actions",
        "test_lock",
        "adversarial_review",
        "reviewer_model",
        "ratchets",
    }
    st = status_mod.read_status(change)
    assert st.gate.phase == "c" and st.gate.result == "passed" and st.parked_reason is None
    recorded = json.loads((change / "evidence" / "gate-c.json").read_text(encoding="utf-8"))
    assert recorded["result"] == "continue" and recorded["head"] == result.head
    assert result.what_i_need() == ""


def test_gate_dry_run_writes_nothing_and_a_failed_check_parks(project):
    """Gate (c) is the confidence gate's alone (decision 37, 1.0.21): it continues with no
    label; a dry run writes nothing, and a failed check parks."""
    root, change = project
    before = (change / "status.yaml").read_text(encoding="utf-8")
    result = gate.run_gate(root, "0001", "c", dry_run=True)
    assert result.result == "park"  # the adversarial verdict is still needed at (c)
    assert "adversarial_review" in _names(result, False)
    verdict(root, "c")
    result = gate.run_gate(root, "0001", "c", dry_run=True)
    assert result.result == "continue" and result.label is None and not result.human_gate
    assert (change / "status.yaml").read_text(encoding="utf-8") == before
    assert not (change / "evidence" / "gate-c.json").exists()
    # a failed check parks (uncommitted work is clean_tree's, not
    # plan_sync's: the plan is judged on the commits since 0.2.9)
    (root / "sample_pkg" / "percent.py").unlink()
    write(root / "sample_pkg" / "extra.py", "x = 1\n")
    result = gate.run_gate(root, "0001", "c")
    assert result.result == "park" and "clean_tree" in _names(result, False)
    assert "plan_sync" in _names(result, True)


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


# --- issue #91 (0.3.0): the commands check deferred to the runner ------------------------------
def _commands_check(result):
    return next(ch for ch in result.checks if ch.name == "commands")


def test_a_ci_session_s_gate_defers_the_commands_and_runs_no_target(project, monkeypatch):
    """With the runner's mark in the environment the gate records the ``commands`` check as
    deferred and runs nothing: a target that would fail (``SAMPLE_FAIL=1``) leaves the gate at
    ``continue``, and the record says the check is waiting for the runner."""
    root, change = project
    verdict(root, "c")
    monkeypatch.setenv("SAMPLE_FAIL", "1")
    monkeypatch.setenv(checks.COMMANDS_RUNNER_ENV, checks.RUN_BY_RUNNER)
    result = gate.run_gate(root, "0001", "c")
    assert result.result == "continue", result.reason
    cmd = _commands_check(result)
    assert cmd.ok is True and cmd.details == {"deferred": True}
    assert cmd.reason == checks.COMMANDS_DEFERRED_REASON and "not yet run" in cmd.reason
    recorded = json.loads((change / "evidence" / "gate-c.json").read_text(encoding="utf-8"))
    assert gate.deferred_commands(recorded) is True
    # any other value of the variable, or none, runs the targets as before
    monkeypatch.setenv(checks.COMMANDS_RUNNER_ENV, "session")
    result = gate.run_gate(root, "0001", "c", dry_run=True)
    assert result.result == "park" and "test (exit 1)" in _commands_check(result).reason


def test_the_runner_s_commands_step_parks_a_red_target_and_keeps_the_record_s_shape(
    project, monkeypatch
):
    root, change = project
    verdict(root, "c")
    monkeypatch.setenv(checks.COMMANDS_RUNNER_ENV, checks.RUN_BY_RUNNER)
    deferred = gate.run_gate(root, "0001", "c")
    before = json.loads((change / "evidence" / "gate-c.json").read_text(encoding="utf-8"))
    monkeypatch.setenv("SAMPLE_FAIL", "1")
    # the runner's own environment may carry the mark too: the step runs the targets anyway
    result = gate.run_deferred_commands(root, "0001", "c")
    assert result is not None and result.result == "park" and result.label == "sdlc:needs-human"
    cmd = _commands_check(result)
    assert cmd.ok is False and "test (exit 1)" in cmd.reason
    assert cmd.details["ran_by"] == "runner" and "deferred" not in cmd.details
    assert "SAMPLE_FAIL=1" in cmd.details["runs"]["test"]["output"]
    assert cmd.details["runs"]["build"]["exit_code"] == 0
    assert cmd.need.startswith("Make the failing target pass")
    # the shape: the same checks in the same order, the session's head and time
    assert [ch.name for ch in result.checks] == [ch.name for ch in deferred.checks]
    assert result.head == before["head"] and result.at == before["at"]
    after = json.loads((change / "evidence" / "gate-c.json").read_text(encoding="utf-8"))
    assert after["result"] == "park" and after["reason"].startswith("commands: not green")
    assert "**commands**" in after["what_i_need"] and "--id 0001 --phase c" in after["what_i_need"]
    assert [ch["name"] for ch in after["checks"]] == [ch["name"] for ch in before["checks"]]
    st = status_mod.read_status(change)
    assert st.gate.result == "parked" and st.parked_reason.startswith("commands: not green")


@pytest.mark.parametrize(
    ("fixture", "phase", "expected", "label", "classification"),
    [
        ("project", "c", "continue", None, "routine"),
        ("design_project", "b", "wait", "sdlc:b-ready", "non-routine"),
        # decision 30: a routine plan in a CI session passes gate (b) on the fast lane
        ("design_project", "b", "continue", None, "routine"),
    ],
)
def test_a_green_target_after_the_session_leaves_the_session_s_verdict_standing(
    request, monkeypatch, fixture, phase, expected, label, classification
):
    root, change = request.getfixturevalue(fixture)
    verdict(root, phase, classification=classification)
    monkeypatch.setenv(checks.COMMANDS_RUNNER_ENV, checks.RUN_BY_RUNNER)
    assert gate.run_gate(root, "0001", phase).result == expected
    result = gate.run_deferred_commands(root, "0001", phase)
    assert result is not None and result.result == expected and result.label == label
    cmd = _commands_check(result)
    assert cmd.ok is True and cmd.reason == "build, test and lint exit 0"
    assert cmd.details["ran_by"] == "runner" and "deferred" not in cmd.details
    assert {n: r["exit_code"] for n, r in cmd.details["runs"].items()} == {
        "build": 0,
        "test": 0,
        "lint": 0,
    }
    recorded = json.loads((change / "evidence" / f"gate-{phase}.json").read_text(encoding="utf-8"))
    assert recorded["result"] == expected and gate.deferred_commands(recorded) is False
    st = status_mod.read_status(change)
    assert st.gate.phase == phase and st.gate.result == "passed" and st.parked_reason is None


def test_a_crashing_check_in_the_runner_s_step_parks_as_the_gate_does(project, monkeypatch):
    """``evaluate`` turns a crashing check into a park; the runner's step does the same (a
    ``gate.command_timeout`` that is not a number crashed the step and left the deferred record
    reading as passed: the fourth finding of the 0.3.0 review)."""
    root, change = project
    verdict(root, "c")
    monkeypatch.setenv(checks.COMMANDS_RUNNER_ENV, checks.RUN_BY_RUNNER)
    assert gate.run_gate(root, "0001", "c").result == "continue"
    original = checks.GateContext.gate_setting
    monkeypatch.setattr(
        checks.GateContext,
        "gate_setting",
        lambda self, key, default: (
            "abc" if key == "command_timeout" else original(self, key, default)
        ),
    )
    result = gate.run_deferred_commands(root, "0001", "c")
    assert result is not None and result.result == "park"
    cmd = _commands_check(result)
    assert cmd.ok is False and cmd.reason.startswith("check crashed: ValueError")
    assert cmd.details == {"ran_by": "runner"}
    recorded = json.loads((change / "evidence" / "gate-c.json").read_text(encoding="utf-8"))
    assert recorded["result"] == "park" and gate.deferred_commands(recorded) is False
    assert status_mod.read_status(change).gate.result == "parked"


def test_an_infrastructure_failure_of_the_runner_s_step_is_re_run_once(project, monkeypatch):
    """Decision 29 (1.0.3): a crash of the targets' run is an infrastructure failure, not a
    red target: the step re-runs the targets once, not counted as a fix round, and parks
    with the reason saying it retried only when the second run crashes too."""
    root, change = project
    verdict(root, "c")
    monkeypatch.setenv(checks.COMMANDS_RUNNER_ENV, checks.RUN_BY_RUNNER)
    assert gate.run_gate(root, "0001", "c").result == "continue"
    deferred = (change / "evidence" / "gate-c.json").read_text(encoding="utf-8")
    original = checks.run_targets
    calls: list[int] = []

    def flaky(ctx, fail_times, only=None):
        calls.append(only)
        if len(calls) <= fail_times:
            raise OSError("runner lost its disk")
        return original(ctx, only=only)

    monkeypatch.setattr(checks, "run_targets", lambda ctx, only=None: flaky(ctx, 1, only))
    result = gate.run_deferred_commands(root, "0001", "c")
    assert calls == [None, None] and result.result == "continue", result.reason
    cmd = _commands_check(result)
    assert cmd.ok is True and cmd.details["retried"] == 1
    # twice: parked, the reason says the step was re-run once, the iteration count untouched
    (change / "evidence" / "gate-c.json").write_text(deferred, encoding="utf-8")
    calls.clear()
    monkeypatch.setattr(checks, "run_targets", lambda ctx, only=None: flaky(ctx, 5, only))
    result = gate.run_deferred_commands(root, "0001", "c")
    assert len(calls) == 2 and result.result == "park"
    cmd = _commands_check(result)
    assert cmd.reason.startswith("check crashed: OSError")
    assert "after one automatic re-run of the commands step, decision 29" in cmd.reason
    assert "failed twice" in cmd.need and "runs" not in cmd.details
    assert status_mod.read_status(change).iterations == 0


@pytest.mark.parametrize("code", [None, 126, 127])
def test_a_target_that_did_not_start_is_re_run_once_and_never_read_as_red(
    project, monkeypatch, code
):
    """No shell (no exit code, no timeout) or the shell's 126/127 (a tool missing on the
    runner) is an infrastructure failure (decision 29): only that target runs again, once."""
    root, change = project
    verdict(root, "c")
    monkeypatch.setenv(checks.COMMANDS_RUNNER_ENV, checks.RUN_BY_RUNNER)
    assert gate.run_gate(root, "0001", "c").result == "continue"
    calls: list = []

    def no_tool(ctx, only=None):
        calls.append(only)
        runs = {
            "build": {"command": "b", "exit_code": 0, "output": "", "seconds": 0.0},
            "test": {"command": "t", "exit_code": code, "output": "t: not found", "seconds": 0.0},
            "lint": {"command": "l", "exit_code": 0, "output": "", "seconds": 0.0},
        }
        return {n: r for n, r in runs.items() if only is None or n in only}

    monkeypatch.setattr(checks, "run_targets", no_tool)
    result = gate.run_deferred_commands(root, "0001", "c")
    assert calls == [None, ["test"]] and result.result == "park"
    cmd = _commands_check(result)
    assert cmd.details["not_started"] == ["test"]
    assert cmd.details["runs"]["build"]["exit_code"] == 0
    assert "did not start (after one automatic re-run, decision 29)" in cmd.reason


def test_the_runner_s_commands_step_leaves_a_record_without_the_deferred_mark_alone(project):
    """A gate run by hand (no mark) ran the targets itself: the step has nothing to do, and
    the record and status.yaml are byte-for-byte what the gate wrote."""
    root, change = project
    verdict(root, "c")
    gate.run_gate(root, "0001", "c")
    record = change / "evidence" / "gate-c.json"
    before = record.read_bytes(), (change / "status.yaml").read_bytes()
    assert gate.run_deferred_commands(root, "0001", "c") is None
    assert (record.read_bytes(), (change / "status.yaml").read_bytes()) == before
    record.unlink()
    assert gate.run_deferred_commands(root, "0001", "c") is None  # no record: nothing to run
    assert not record.exists()
    with pytest.raises(gate.GateError, match="no change folder"):
        gate.run_deferred_commands(root, "0009", "c")


# --- item 3b (0.3.2): the evidence logs deferred to the runner's same step -------------------
def _at_phase_d(root: Path, change: Path) -> None:
    """The project fixture moved to phase (d) with its run registered and its verdict written:
    the state gate (d) judges, before the evidence writer has run."""
    set_phase(change, "d")
    start_run(root, "d")
    verdict(root, "d")


def _check(result, name):
    return next(ch for ch in result.checks if ch.name == name)


def write_marked_logs(root: Path, change: Path) -> None:
    """The three logs as ``evidence/collect.py`` leaves them inside a CI session."""
    from evidence import collect as collect_mod

    report, code = collect_mod.collect(root, "0001")
    assert code == 0 and report["deferred"] is True, report


def test_a_ci_session_s_gate_at_d_accepts_the_marked_logs_only_while_the_deferral_holds(
    project, monkeypatch
):
    """Item 3b: with the runner's mark in the environment the evidence writer leaves a mark in
    each log and the gate's ``evidence`` check accepts it (``ok`` with ``details.deferred``),
    beside the deferred ``commands`` check; the same record read without the deferral - a
    gate run by hand on a tree whose logs were never replaced - fails the evidence check."""
    root, change = project
    _at_phase_d(root, change)
    write(change / "evidence" / "verifier.md", "# Verifier\nread, not run\n")
    monkeypatch.setenv("SAMPLE_FAIL", "1")  # a target that would fail: nothing runs it here
    monkeypatch.setenv(checks.COMMANDS_RUNNER_ENV, checks.RUN_BY_RUNNER)
    write_marked_logs(root, change)
    result = gate.run_gate(root, "0001", "d")
    assert result.result == "continue", result.reason
    ev = _check(result, "evidence")
    assert ev.ok is True and ev.details == {
        "deferred": True,
        "deferred_logs": ["test.log", "build.log", "lint.log"],
    }
    assert ev.reason.startswith("deferred to the runner") and "not yet written" in ev.reason
    assert _check(result, "commands").details == {"deferred": True}
    recorded = json.loads((change / "evidence" / "gate-d.json").read_text(encoding="utf-8"))
    assert gate.deferred_checks(recorded) == ["commands", "evidence"]
    assert gate.deferred_commands(recorded) is True
    # the mark is no evidence once the deferral is off: 0.3.1's gate parked on it as a log
    # without the collector header; 0.3.2's names the mark the runner never replaced
    monkeypatch.delenv(checks.COMMANDS_RUNNER_ENV)
    by_hand = gate.run_gate(root, "0001", "d", dry_run=True)
    assert by_hand.result == "park"
    ev = _check(by_hand, "evidence")
    assert ev.ok is False and ev.details["red_files"] == ["test.log", "build.log", "lint.log"]
    assert "the runner never replaced it" in ev.reason


def test_the_runner_s_step_writes_the_three_logs_from_its_one_run_and_re_judges_the_gate(
    project, monkeypatch
):
    """After the session the runner's ``run-commands`` step runs the targets once: the
    ``commands`` entry and the three logs come from that run (they agree by construction),
    and the ``evidence`` check is judged again without the deferral; a green run leaves the
    session's verdict standing, a red target parks on both checks with the red log named."""
    root, change = project
    _at_phase_d(root, change)
    write(change / "evidence" / "verifier.md", "# Verifier\nread, not run\n")
    monkeypatch.setenv(checks.COMMANDS_RUNNER_ENV, checks.RUN_BY_RUNNER)
    write_marked_logs(root, change)
    deferred = gate.run_gate(root, "0001", "d")
    before = json.loads((change / "evidence" / "gate-d.json").read_text(encoding="utf-8"))
    result = gate.run_deferred_commands(root, "0001", "d")
    assert result is not None and result.result == "continue" and result.label is None
    cmd, ev = _check(result, "commands"), _check(result, "evidence")
    assert cmd.ok and cmd.details["ran_by"] == "runner" and "deferred" not in cmd.details
    assert (
        ev.ok
        and ev.details == {}
        and ev.reason == ("evidence present: test.log, build.log, lint.log, verifier.md")
    )
    assert [ch.name for ch in result.checks] == [ch.name for ch in deferred.checks]
    assert result.head == before["head"] and result.at == before["at"]
    for target, name in art.EVIDENCE_TARGETS.items():
        text = (change / "evidence" / name).read_text(encoding="utf-8")
        header = art.parse_evidence_header(text)
        assert header is not None and header["exit"] == "0", text[:200]
        assert header["command"] == cmd.details["runs"][target]["command"]
        assert float(header["seconds"]) >= 0 and header["at"].endswith("Z")
        assert art.parse_deferred_header(text) is None
    assert "passed" in (change / "evidence" / "test.log").read_text(encoding="utf-8")
    recorded = json.loads((change / "evidence" / "gate-d.json").read_text(encoding="utf-8"))
    assert gate.deferred_checks(recorded) == [] and recorded["result"] == "continue"
    assert status_mod.read_status(change).gate.result == "passed"
    # the record's runs keep the tail of the output; the log keeps it whole
    assert "seconds" not in cmd.details["runs"]["test"]
    # a second step finds nothing deferred
    assert gate.run_deferred_commands(root, "0001", "d") is None

    # the red case: the mark again, the target fails after the session
    write_marked_logs(root, change)
    gate.run_gate(root, "0001", "d")
    monkeypatch.setenv("SAMPLE_FAIL", "1")
    result = gate.run_deferred_commands(root, "0001", "d")
    assert result is not None and result.result == "park" and result.label == "sdlc:needs-human"
    cmd, ev = _check(result, "commands"), _check(result, "evidence")
    assert cmd.ok is False and "test (exit 1)" in cmd.reason
    assert ev.ok is False and ev.details["red_files"] == ["test.log"]
    assert "exited 1" in ev.reason and "deferred" not in ev.details
    test_log = (change / "evidence" / "test.log").read_text(encoding="utf-8")
    assert art.parse_evidence_header(test_log)["exit"] == "1" and "SAMPLE_FAIL=1" in test_log
    assert (
        art.parse_evidence_header((change / "evidence" / "build.log").read_text("utf-8"))["exit"]
        == "0"
    )
    st = status_mod.read_status(change)
    assert st.gate.result == "parked" and st.parked_reason.startswith("commands: not green")
    assert "evidence/test.log" in st.parked_reason


def test_a_marked_log_the_step_could_not_replace_fails_the_record(project, monkeypatch):
    """A crashing targets run (``gate.command_timeout`` not a number) leaves the marks in
    place: the ``commands`` entry parks on the crash and the ``evidence`` entry, judged without
    the deferral, refuses the marks the runner never replaced - never a pass on them."""
    root, change = project
    _at_phase_d(root, change)
    write(change / "evidence" / "verifier.md", "# Verifier\nread, not run\n")
    monkeypatch.setenv(checks.COMMANDS_RUNNER_ENV, checks.RUN_BY_RUNNER)
    write_marked_logs(root, change)
    assert gate.run_gate(root, "0001", "d").result == "continue"
    original = checks.GateContext.gate_setting
    monkeypatch.setattr(
        checks.GateContext,
        "gate_setting",
        lambda self, key, default: (
            "abc" if key == "command_timeout" else original(self, key, default)
        ),
    )
    result = gate.run_deferred_commands(root, "0001", "d")
    assert result is not None and result.result == "park"
    assert _check(result, "commands").reason.startswith("check crashed: ValueError")
    ev = _check(result, "evidence")
    assert ev.ok is False and ev.details["red_files"] == ["test.log", "build.log", "lint.log"]
    assert "the runner never replaced it" in ev.reason
    assert art.parse_deferred_header((change / "evidence" / "test.log").read_text("utf-8"))
    recorded = json.loads((change / "evidence" / "gate-d.json").read_text(encoding="utf-8"))
    assert gate.deferred_checks(recorded) == [] and recorded["result"] == "park"


def test_the_runner_s_step_at_c_writes_the_marked_logs_it_finds_and_leaves_the_rest(
    project, monkeypatch
):
    """At (c) no log is required, so only ``commands`` is deferred; a log the build session
    marked all the same (``collect.py --only test``) is written from the step's run, a log
    it did not mark is left as it is (the review of the 0.3.2 diff, finding 9)."""
    from evidence import collect as collect_mod

    root, change = project
    verdict(root, "c")
    write_logs(change, red="build")  # an older tree's logs, the build one red
    monkeypatch.setenv(checks.COMMANDS_RUNNER_ENV, checks.RUN_BY_RUNNER)
    report, code = collect_mod.collect(root, "0001", only=["test"])
    assert code == 0 and report["deferred"] is True
    assert gate.run_gate(root, "0001", "c").result == "continue"
    recorded = json.loads((change / "evidence" / "gate-c.json").read_text(encoding="utf-8"))
    assert gate.deferred_checks(recorded) == ["commands"]
    result = gate.run_deferred_commands(root, "0001", "c")
    assert result is not None and result.result == "continue"
    test_log = (change / "evidence" / "test.log").read_text(encoding="utf-8")
    assert art.parse_evidence_header(test_log)["exit"] == "0" and "passed" in test_log
    build_log = (change / "evidence" / "build.log").read_text(encoding="utf-8")
    assert art.parse_evidence_header(build_log)["exit"] == "1"  # untouched at (c)
    assert (
        _check(result, "evidence").ok and _check(result, "commands").details["ran_by"] == "runner"
    )


def test_the_runner_s_step_at_d_writes_all_three_logs_and_lifts_a_park_on_a_stale_one(
    project, monkeypatch
):
    """At (d) the gate reads the three logs, so the step writes all three from its run,
    marked or not: a red log of an older tree no longer stands beside the runner's green
    run, and a session that parked on it is re-judged on the logs of this run (the review
    of the 0.3.2 diff, finding 8)."""
    from evidence import collect as collect_mod

    root, change = project
    _at_phase_d(root, change)
    write(change / "evidence" / "verifier.md", "# Verifier\nread, not run\n")
    write_logs(change, red="build")  # an older tree's logs, the build one red
    monkeypatch.setenv(checks.COMMANDS_RUNNER_ENV, checks.RUN_BY_RUNNER)
    report, code = collect_mod.collect(root, "0001", only=["test"])
    assert code == 0 and report["deferred"] is True
    session = gate.run_gate(root, "0001", "d")
    assert session.result == "park" and _check(session, "evidence").details["red_files"] == [
        "build.log"
    ]
    recorded = json.loads((change / "evidence" / "gate-d.json").read_text(encoding="utf-8"))
    assert gate.deferred_checks(recorded) == ["commands"]
    result = gate.run_deferred_commands(root, "0001", "d")
    assert result is not None and result.result == "continue" and result.label is None
    for name in art.EVIDENCE_TARGETS.values():
        text = (change / "evidence" / name).read_text(encoding="utf-8")
        assert art.parse_evidence_header(text)["exit"] == "0", (name, text[:120])
    ev = _check(result, "evidence")
    assert ev.ok and ev.reason.startswith("evidence present")
    st = status_mod.read_status(change)
    assert st.gate.result == "passed" and st.parked_reason is None


def test_a_record_whose_evidence_alone_is_deferred_keeps_the_session_s_commands_entry(
    project, monkeypatch
):
    """Only the entries the session left to the runner are replaced: a ``commands`` entry the
    session ran itself stays, while the marked logs are written and the ``evidence`` entry
    judged again (the ``pending`` guard; the review of the 0.3.2 diff, finding 9)."""
    root, change = project
    _at_phase_d(root, change)
    write(change / "evidence" / "verifier.md", "# Verifier\nread, not run\n")
    monkeypatch.setenv(checks.COMMANDS_RUNNER_ENV, checks.RUN_BY_RUNNER)
    write_marked_logs(root, change)
    gate.run_gate(root, "0001", "d")
    path = change / "evidence" / "gate-d.json"
    recorded = json.loads(path.read_text(encoding="utf-8"))
    for ch in recorded["checks"]:
        if ch["name"] == "commands":
            ch["reason"], ch["details"] = "build, test and lint exit 0", {"runs": {"test": {}}}
    path.write_text(json.dumps(recorded), encoding="utf-8")
    assert gate.deferred_checks(recorded) == ["evidence"]
    result = gate.run_deferred_commands(root, "0001", "d")
    assert result is not None and result.result == "continue"
    cmd = _check(result, "commands")
    assert cmd.details == {"runs": {"test": {}}} and "ran_by" not in cmd.details
    ev = _check(result, "evidence")
    assert ev.ok and ev.details == {} and gate.deferred_checks(result.as_dict()) == []
    text = (change / "evidence" / "test.log").read_text(encoding="utf-8")
    assert art.parse_evidence_header(text)["exit"] == "0"


def test_the_deferred_mark_readers_cover_the_evidence_entry_too():
    record = {"checks": [{"name": "evidence", "ok": True, "details": {"deferred": True}}]}
    assert gate.deferred_checks(record) == ["evidence"] and gate.deferred_commands(record)
    record = {"checks": [{"name": "evidence", "ok": True, "details": {"deferred_logs": []}}]}
    assert gate.deferred_checks(record) == [] and not gate.deferred_commands(record)
    assert gate.deferred_checks({"checks": "x"}) == [] and not gate.deferred_commands({})


def test_a_by_hand_gate_at_d_with_real_logs_is_untouched_by_3b(project, monkeypatch):
    """Without the runner's mark the writer runs the targets and the gate reads the headers
    as it always did; a step after it has nothing to do."""
    root, change = project
    _at_phase_d(root, change)
    write(change / "evidence" / "verifier.md", "# Verifier\nran\n")
    monkeypatch.delenv(checks.COMMANDS_RUNNER_ENV, raising=False)
    from evidence import collect as collect_mod

    report, code = collect_mod.collect(root, "0001")
    assert code == 0 and report["all_green"] is True and "deferred" not in report
    result = gate.run_gate(root, "0001", "d")
    assert result.result == "continue" and _check(result, "evidence").details == {}
    assert gate.run_deferred_commands(root, "0001", "d") is None


def test_the_run_commands_cli_reports_the_step_and_exits_0_either_way(project, monkeypatch):
    root, change = project
    verdict(root, "c")
    monkeypatch.setenv(checks.COMMANDS_RUNNER_ENV, checks.RUN_BY_RUNNER)
    run_py(str(GATE_CLI), "check", "--root", str(root), "--id", "0001", "--phase", "c", cwd=root)
    env = {k: v for k, v in os.environ.items() if k != checks.COMMANDS_RUNNER_ENV}
    proc = run_py(
        str(GATE_CLI), "run-commands", "--root", str(root), "--id", "0001", "--phase", "c",
        cwd=root, env={**env, "SAMPLE_FAIL": "1"},
    )  # fmt: skip
    assert proc.returncode == 0, proc.stderr
    out = json.loads(proc.stdout)
    assert out["ran"] is True and out["result"] == "park" and out["schema_version"] == 1
    assert "## What I need from you" in proc.stderr and "**commands**" in proc.stderr
    # a second call finds the targets already run
    proc = run_py(
        str(GATE_CLI), "run-commands", "--root", str(root), "--id", "0001", "--phase", "c",
        cwd=root, env=env,
    )  # fmt: skip
    assert proc.returncode == 0 and json.loads(proc.stdout) == {
        "ran": False,
        "reason": "the gate record carries no check deferred to the runner",
    }
    proc = run_py(
        str(GATE_CLI), "run-commands", "--root", str(root), "--id", "0001", "--phase", "b",
        cwd=root, env=env,
    )  # fmt: skip
    assert proc.returncode == 0 and json.loads(proc.stdout)["ran"] is False  # no gate-b.json
    (change / "evidence" / "gate-c.json").write_text("not json", encoding="utf-8")
    proc = run_py(
        str(GATE_CLI), "run-commands", "--root", str(root), "--id", "0001", "--phase", "c",
        cwd=root, env=env,
    )  # fmt: skip
    assert proc.returncode == 2 and "gate-c.json unreadable" in proc.stderr


def test_a_gate_record_round_trips_through_from_dict(project):
    root, change = project
    verdict(root, "c")
    result = gate.run_gate(root, "0001", "c")
    data = json.loads((change / "evidence" / "gate-c.json").read_text(encoding="utf-8"))
    again = gate.GateResult.from_dict(data)
    assert again.as_dict() == data == result.as_dict()
    assert gate.GateResult.from_dict({}).result == "park"  # an empty record fails closed


def test_gate_parks_when_the_diff_touches_settings_json(project):
    root, change = project
    verdict(root, "c")
    settings = root / ".claude" / "settings.json"
    data = json.loads(settings.read_text(encoding="utf-8"))
    data["permissions"]["allow"].append("Bash(rm *)")
    write(settings, json.dumps(data, indent=2))
    # uncommitted, the edit is clean_tree's: the gate judges HEAD (deliverable 6(d))
    result = gate.run_gate(root, "0001", "c")
    assert result.result == "park"
    assert "clean_tree" in _names(result, False)
    assert "guardrails" in _names(result, True)
    # committed, it is on the branch the PR would merge, and guardrails parks
    git(root, "add", ".claude/settings.json")
    git(root, "commit", "-q", "-m", "widen the permissions")
    verdict(root, "c")
    result = gate.run_gate(root, "0001", "c")
    assert result.result == "park"
    g = next(ch for ch in result.failed if ch.name == "guardrails")
    assert ".claude/settings.json" in g.reason
    assert "clean_tree" in _names(result, True)
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
    g = next(ch for ch in result.checks if ch.name == "guardrails")
    assert g.details["touched"] == [".claude/settings.json"]  # still on the branch, exempted


def test_a_risk_list_word_is_reported_never_parked_and_accepted_by_hand(project):
    """Decision 35 (1.0.15): a risk-list hit no longer parks. The check passes and reports
    the hit for the close-look banner; the by-hand ``accept-risk`` stays, counts once the
    owner committed it, and the check then names the item accepted."""
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
    assert result.result == "continue", result.reason
    r = next(ch for ch in result.checks if ch.name == "risk_list")
    assert r.ok and r.details["hits"] == {"auth": ["sample_pkg/auth.py"]}
    assert r.details["accepted"] == [] and "close-look banner" in r.reason
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
    result = gate.run_gate(root, "0001", "c")
    assert result.result == "continue", result.reason
    r = next(ch for ch in result.checks if ch.name == "risk_list")
    assert r.details["accepted"] == ["auth"]
    assert r.details["hits"] == {"auth": ["sample_pkg/auth.py"]}


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


def test_plan_sync_judges_the_committed_diff_only(project):
    """The first gated build run on the sample repository (2026-09-22, plugin 0.2.8): the
    gate ran inside Claude Code's sandbox, where the masked ``.env`` shows as modified, and
    plan_sync parked on ".env not listed in plan.md". The working tree says nothing about
    the plan; the commits do, as design_scope has judged since 0.2.3."""
    root, change = project
    verdict(root, "c")
    write(root / ".env", "SAMPLE_FLAG=masked-by-the-sandbox\n")  # tracked, dirty, uncommitted
    result = gate.run_gate(root, "0001", "c", dry_run=True)
    p = next(ch for ch in result.checks if ch.name == "plan_sync")
    assert p.ok, p.reason
    assert "clean_tree" in _names(result, True)  # .env is a sandbox-masked name


def test_guardrails_and_risk_list_judge_the_committed_diff_only(project):
    """Deliverable 6(d): guardrails and risk_list read merge base...HEAD, like plan_sync and
    design_scope (OPERATING_MODEL section 3: the gate judges HEAD, not the working tree).
    Uncommitted work is clean_tree's to report; once committed, the same change parks on the
    guardrail file and reports the risk-list hit (decision 35: a hit never parks)."""
    root, _change = project
    settings = root / ".claude" / "settings.json"
    data = json.loads(settings.read_text(encoding="utf-8"))
    data["permissions"]["allow"].append("Bash(rm *)")
    write(settings, json.dumps(data, indent=2))  # tracked, modified
    write(root / "CLAUDE.md", "# Project\nA line the run wrote.\n")  # a guardrail file
    write(root / "sample_pkg" / "auth.py", "TOKEN_TTL = 60\n")  # untracked risk-list hit
    verdict(root, "c")
    result = gate.run_gate(root, "0001", "c", dry_run=True)
    assert {"guardrails", "risk_list"} <= set(_names(result, True)), result.reason
    assert next(ch for ch in result.checks if ch.name == "risk_list").details["hits"] == {}
    ct = next(ch for ch in result.failed if ch.name == "clean_tree")
    assert {".claude/settings.json", "CLAUDE.md", "sample_pkg/auth.py"} <= set(ct.details["dirty"])

    git(root, "add", ".claude/settings.json", "CLAUDE.md", "sample_pkg/auth.py")
    git(root, "commit", "-q", "-m", "the same change, committed")
    verdict(root, "c")
    result = gate.run_gate(root, "0001", "c", dry_run=True)
    assert result.result == "park"
    g = next(ch for ch in result.failed if ch.name == "guardrails")
    assert g.details["touched"] == [".claude/settings.json", "CLAUDE.md"]
    r = next(ch for ch in result.checks if ch.name == "risk_list")
    assert r.ok and r.details["hits"] == {"auth": ["sample_pkg/auth.py"]}
    assert "clean_tree" in _names(result, True)


def test_a_sandbox_masked_env_no_longer_trips_guardrails_or_risk_list(project):
    """Inside Claude Code's sandbox the project's ``.env`` shows as modified however clean the
    checkout is (the false positive that parked plan_sync in the eleventh live run,
    2026-09-22). A project that protects ``.env`` or lists it on its risk list would have
    parked on it in guardrails and risk_list too, which read the working tree until 0.2.12."""
    root, _change = project

    def protect_env(r: Path) -> None:
        text = (r / "sdlc.yaml").read_text(encoding="utf-8")
        edited = text.replace("protected_paths: []", 'protected_paths:\n  - ".env"').replace(
            '  - "production config"\n', '  - "production config"\n  - env\n'
        )
        assert edited.count('- ".env"') == 1 and "  - env\n" in edited
        write(r / "sdlc.yaml", edited)

    on_base(root, protect_env, "owner: protect .env and put it on the risk list")
    write(root / ".env", "SANDBOX=1\n")  # tracked: shows as modified, nobody's work
    assert ".env" in checks.diffmod.collect(root).files  # what the two checks used to read
    verdict(root, "c")
    result = gate.run_gate(root, "0001", "c", dry_run=True)
    assert {"guardrails", "risk_list", "clean_tree"} <= set(_names(result, True)), result.reason
    assert result.result == "continue", result.reason


DIFF_CHECKS = (
    checks.check_plan_sync,
    checks.check_design_scope,
    checks.check_guardrails,
    checks.check_risk_list,
    checks.check_ratchets,
)


def _single_branch_repo(tmp_path: Path, branch: str) -> Path:
    """One branch, no remote: a change 0001 at phase (c) and a committed guardrail edit."""
    root = tmp_path / branch
    write(root / "sdlc.yaml", "protected_paths: []\nrisk_list:\n  - auth\n")
    git(root, "init", "-q", "-b", branch)
    git(root, "config", "user.email", "owner@example.com")
    git(root, "config", "user.name", "Owner")
    change_dir, st = status_mod.new_change(root, "Percent helper")
    st.set_phase("c")
    status_mod.write_status(change_dir, st)
    write(root / "CLAUDE.md", "# Project\n")
    write(root / "sample_pkg" / "auth.py", "TOKEN_TTL = 60\n")
    git(root, "add", ".")
    git(root, "commit", "-q", "-m", "everything on the one branch")
    return root


def test_the_diff_checks_fail_when_no_default_branch_exists(tmp_path):
    """Review finding M2 (0.2.12): with no origin/HEAD, main or master, ``diff.collect``
    compares HEAD with itself and the committed diff is empty whatever the branch carries;
    the four checks that judge it used to pass silently on that empty list."""
    root = _single_branch_repo(tmp_path, "trunk")
    ctx = gate.build_context(root, "0001", "c")
    assert ctx.diff is not None and ctx.diff.base == "HEAD" and "no base" in ctx.diff.note
    for check in DIFF_CHECKS:
        res = check(ctx)
        assert not res.ok, check.__name__
        assert res.reason == "no base branch: the committed diff cannot be judged"
        assert res.need == (
            "Run the gate in a checkout whose default branch exists (origin/HEAD, main or master)"
        )


def test_the_diff_checks_fail_when_the_branch_shares_no_history_with_the_base(tmp_path):
    """The readiness review's group B (0.2.27): with a base that exists but has no merge
    base with HEAD (an orphan branch, a shallow clone), ``diff.collect`` returned an empty
    committed diff and the four checks passed on it — the silent pass M2 fixed for the
    no-base case. Now ``merge_base`` None fails them, naming the base."""
    root = _single_branch_repo(tmp_path, "main")
    git(root, "checkout", "-q", "--orphan", "sdlc/0001/c")
    git(root, "commit", "-q", "-m", "an unrelated history with the same files")
    ctx = gate.build_context(root, "0001", "c")
    assert ctx.diff is not None and ctx.diff.base == "main" and ctx.diff.merge_base is None
    assert ctx.diff.commits == [] and "cannot be judged" in ctx.diff.note
    assert checks.diffmod.committed_files(root, ctx.diff.merge_base, ctx.diff.head) == []
    for check in DIFF_CHECKS:
        res = check(ctx)
        assert not res.ok, check.__name__
        assert res.reason == "no merge base with main: the committed diff cannot be judged"
        assert "fetch-depth: 0" in res.need and "main" in res.need


def test_the_diff_checks_judge_a_checkout_of_the_default_branch_itself(tmp_path):
    """A single-branch repository on its default branch is not "no base": the merge base is
    HEAD because nothing was committed on top of the base yet, and the empty diff passes."""
    root = _single_branch_repo(tmp_path, "main")
    ctx = gate.build_context(root, "0001", "c")
    assert ctx.diff is not None and ctx.diff.base == "main"
    assert ctx.diff.merge_base == ctx.diff.head
    for check in DIFF_CHECKS:
        res = check(ctx)
        assert res.ok, (check.__name__, res.reason)
        assert res.reason != checks.NO_BASE_REASON


def test_default_base_prefers_the_environment_value_when_its_remote_branch_exists(
    tmp_path, monkeypatch
):
    """``SDLC_DEFAULT_BRANCH`` names the base when ``origin/<value>`` resolves, before
    origin/HEAD; a framework branch name or a branch the remote lacks falls through."""
    from gate import diff

    root = _single_branch_repo(tmp_path, "main")
    origin = tmp_path / "origin.git"
    git(tmp_path, "init", "-q", "--bare", "-b", "main", str(origin))
    git(root, "remote", "add", "origin", str(origin))
    git(root, "push", "-q", "origin", "main", "main:trunk", "main:sdlc/0001/a")
    git(root, "fetch", "-q", "origin")
    git(root, "symbolic-ref", "refs/remotes/origin/HEAD", "refs/remotes/origin/main")
    assert diff.default_base(root) == "refs/remotes/origin/main"  # qualified since 0.2.27
    monkeypatch.setenv("SDLC_DEFAULT_BRANCH", "trunk")
    assert diff.default_base(root) == "refs/remotes/origin/trunk"
    for fallthrough in ("sdlc/0001/a", "nonexistent"):
        monkeypatch.setenv("SDLC_DEFAULT_BRANCH", fallthrough)
        assert diff.default_base(root) == "refs/remotes/origin/main", fallthrough
    # the review of the 0.2.27 diff, M2: a tag named origin/main (anyone with write access
    # can push one; a CI checkout fetches tags) used to shadow the short ref and empty the
    # committed diff every check judges
    monkeypatch.delenv("SDLC_DEFAULT_BRANCH")
    git(root, "tag", "origin/main", "HEAD~0")
    assert diff.default_base(root) == "refs/remotes/origin/main"


# --- ratchets: a dropped test file or eval case (intent.md change 1; spec.md change 5) --------
NS = checks.diffmod.NameStatusRecord


def _plain_repo(tmp_path: Path) -> Path:
    root = tmp_path / "plain"
    root.mkdir()
    git(root, "init", "-q", "-b", "main")
    git(root, "config", "user.email", "owner@example.com")
    git(root, "config", "user.name", "Owner")
    return root


def test_diff_name_status_rename_detection_parses_rename(tmp_path):
    root = _plain_repo(tmp_path)
    write(root / "tests" / "test_a.py", "def test_a(): pass\n")
    git(root, "add", ".")
    git(root, "commit", "-q", "-m", "base")
    base = git(root, "rev-parse", "HEAD").strip()
    git(root, "mv", "tests/test_a.py", "tests/test_b.py")
    git(root, "commit", "-q", "-m", "rename")
    records = checks.diffmod.name_status(root, base, "HEAD")
    assert records == [NS("R", "tests/test_a.py", "tests/test_b.py")]


def test_diff_name_status_delete_parses_as_d(tmp_path):
    root = _plain_repo(tmp_path)
    write(root / "tests" / "test_a.py", "def test_a(): pass\n")
    git(root, "add", ".")
    git(root, "commit", "-q", "-m", "base")
    base = git(root, "rev-parse", "HEAD").strip()
    (root / "tests" / "test_a.py").unlink()
    git(root, "add", ".")
    git(root, "commit", "-q", "-m", "drop")
    records = checks.diffmod.name_status(root, base, "HEAD")
    assert records == [NS("D", "tests/test_a.py")]


def test_diff_tree_files_lists_committed_paths_under_prefix(tmp_path):
    root = _plain_repo(tmp_path)
    write(root / "evals" / "cases" / "foo" / "a.yaml", "a: 1\n")
    write(root / "evals" / "cases" / "foo" / "b.yaml", "b: 1\n")
    write(root / "evals" / "cases" / "bar" / "c.yaml", "c: 1\n")
    write(root / "README.md", "x\n")
    git(root, "add", ".")
    git(root, "commit", "-q", "-m", "base")
    head = git(root, "rev-parse", "HEAD").strip()
    assert checks.diffmod.tree_files(root, head, "evals/cases") == [
        "evals/cases/bar/c.yaml",
        "evals/cases/foo/a.yaml",
        "evals/cases/foo/b.yaml",
    ]
    assert checks.diffmod.tree_files(root, None, "evals/cases") == []


def test_dropped_test_files_and_eval_cases_pure():
    """The two drop-rule functions over the parsed records alone (plus a plain survivor
    list for the eval-case rule), not live git (plan.md step 2)."""
    patterns = ["tests/**"]
    records = [
        NS("D", "tests/test_a.py"),
        NS("D", "sample_pkg/util.py"),  # not under test_paths: not reported
        NS("R", "tests/test_b.py", "tests/test_c.py"),  # rename within the globs: not a drop
        NS("R", "tests/test_d.py", "sample_pkg/test_d.py"),  # out of scope: a drop
        NS("R", "sample_pkg/x.py", "tests/test_e.py"),  # into scope: a new test, not a drop
    ]
    assert checks.dropped_test_files(records, patterns) == ["tests/test_a.py", "tests/test_d.py"]

    case_records = [
        NS("D", "evals/cases/bar/only.yaml"),  # the whole case: dropped
        NS("D", "evals/cases/foo/a.yaml"),  # one of two: a survivor remains
        NS("R", "evals/cases/baz/x.yaml", "evals/cases/.baz/x.yaml"),  # hidden rename: dropped
        NS("R", "evals/cases/qux/a.yaml", "evals/cases/qux/a2.yaml"),  # internal move: kept
    ]
    survivors = ["evals/cases/foo/b.yaml", "evals/cases/qux/a2.yaml"]
    assert checks.dropped_eval_cases(case_records, survivors) == [
        "evals/cases/bar/",
        "evals/cases/baz/",
    ]


RATCHET_SDLC_YAML = "risk_list:\n  - auth\n"
BASE_PLAN = "# Plan: x\n\n## Files that change\n- none\n\n## Proof\nnone\n"
PLAN_FILES_DECLARES_TEST = (
    "# Plan: x\n\n## Files that change\n- `tests/test_keep.py` — removed\n\n## Proof\nnone\n"
)
PLAN_PROOF_DECLARES_TESTS = (
    "# Plan: x\n\n## Files that change\n- none\n\n## Proof\n"
    "- ratchet: tests may fall, because the helper is retired\n"
)
PLAN_FILES_DECLARES_BAR = (
    "# Plan: x\n\n## Files that change\n- `evals/cases/bar/` — retired\n\n## Proof\nnone\n"
)
PLAN_PROOF_DECLARES_EVALS = (
    "# Plan: x\n\n## Files that change\n- none\n\n## Proof\n"
    "- ratchet: evals may fall, because the case is obsolete\n"
)
PLAN_PROOF_UNKNOWN_RATCHET = (
    "# Plan: x\n\n## Files that change\n- none\n\n## Proof\n"
    "- ratchet: docs may fall, because nothing\n"
)


def _ratchet_repo(tmp_path: Path, plan_body: str, sdlc_yaml: str = RATCHET_SDLC_YAML):
    """A one-branch repo ('main') with the given plan.md committed as approved, a
    tests/test_keep.py file, a two-file eval case ('foo') and a one-file eval case ('bar');
    checked out on 'sdlc/0001/c' for the test's own commit."""
    root = tmp_path / "repo"
    write(root / "sdlc.yaml", sdlc_yaml)
    write(root / "tests" / "test_keep.py", "def test_keep():\n    assert True\n")
    write(root / "evals" / "cases" / "foo" / "a.yaml", "a: 1\n")
    write(root / "evals" / "cases" / "foo" / "b.yaml", "b: 1\n")
    write(root / "evals" / "cases" / "bar" / "only.yaml", "c: 1\n")
    git(root, "init", "-q", "-b", "main")
    git(root, "config", "user.email", "owner@example.com")
    git(root, "config", "user.name", "Owner")
    change_dir, st = status_mod.new_change(root, "x", change_id="0001")
    write(change_dir / "plan.md", plan_body)
    st.set_phase("c")
    status_mod.write_status(change_dir, st)
    git(root, "add", ".")
    git(root, "commit", "-q", "-m", "base (as if the a and b PRs merged)")
    git(root, "checkout", "-q", "-b", "sdlc/0001/c")
    return root, change_dir


def test_ratchets_drop_test_file_undeclared_is_a_hit(tmp_path):
    root, _change = _ratchet_repo(tmp_path, BASE_PLAN)
    (root / "tests" / "test_keep.py").unlink()
    git(root, "add", ".")
    git(root, "commit", "-q", "-m", "drop a test")
    res = checks.check_ratchets(gate.build_context(root, "0001", "c"))
    assert res.ok and "close-look banner" in res.reason  # decision 35: a hit, never a park
    assert res.details["hits"]["ratchet: tests"] == ["tests/test_keep.py"]


def test_ratchets_drop_test_file_declared_in_files_that_change_ok(tmp_path):
    root, _change = _ratchet_repo(tmp_path, PLAN_FILES_DECLARES_TEST)
    (root / "tests" / "test_keep.py").unlink()
    git(root, "add", ".")
    git(root, "commit", "-q", "-m", "drop a test, declared")
    res = checks.check_ratchets(gate.build_context(root, "0001", "c"))
    assert res.ok, res.reason
    assert "tests/test_keep.py (plan)" in res.details["declared"]


def test_ratchets_drop_test_file_declared_in_proof_ok(tmp_path):
    root, _change = _ratchet_repo(tmp_path, PLAN_PROOF_DECLARES_TESTS)
    (root / "tests" / "test_keep.py").unlink()
    git(root, "add", ".")
    git(root, "commit", "-q", "-m", "drop a test, declared via proof")
    res = checks.check_ratchets(gate.build_context(root, "0001", "c"))
    assert res.ok, res.reason


def test_ratchets_plan_edited_after_merge_base_does_not_excuse_drop(tmp_path):
    root, change_dir = _ratchet_repo(tmp_path, BASE_PLAN)
    (root / "tests" / "test_keep.py").unlink()
    write(change_dir / "plan.md", PLAN_FILES_DECLARES_TEST)  # edited only on this branch
    git(root, "add", ".")
    git(root, "commit", "-q", "-m", "drop a test and edit plan.md in the same commit")
    res = checks.check_ratchets(gate.build_context(root, "0001", "c"))
    assert res.ok and "close-look banner" in res.reason  # decision 35: a hit, never a park
    assert res.details["hits"]["ratchet: tests"] == ["tests/test_keep.py"]


def test_ratchets_rename_within_test_paths_is_not_a_drop(tmp_path):
    root, _change = _ratchet_repo(tmp_path, BASE_PLAN)
    git(root, "mv", "tests/test_keep.py", "tests/test_renamed.py")
    git(root, "commit", "-q", "-m", "rename within test_paths")
    res = checks.check_ratchets(gate.build_context(root, "0001", "c"))
    assert res.ok, res.reason


def test_ratchets_rename_out_of_test_paths_is_a_drop(tmp_path):
    root, _change = _ratchet_repo(tmp_path, BASE_PLAN)
    git(root, "mv", "tests/test_keep.py", "renamed_out_of_scope.py")
    git(root, "commit", "-q", "-m", "rename out of test_paths")
    res = checks.check_ratchets(gate.build_context(root, "0001", "c"))
    assert res.ok and "close-look banner" in res.reason  # decision 35: a hit, never a park
    assert res.details["hits"]["ratchet: tests"] == ["tests/test_keep.py"]


def test_ratchets_drop_eval_case_folder_emptied_is_a_hit(tmp_path):
    root, _change = _ratchet_repo(tmp_path, BASE_PLAN)
    (root / "evals" / "cases" / "bar" / "only.yaml").unlink()
    git(root, "add", ".")
    git(root, "commit", "-q", "-m", "empty the bar case")
    res = checks.check_ratchets(gate.build_context(root, "0001", "c"))
    assert res.ok and "close-look banner" in res.reason  # decision 35: a hit, never a park
    assert res.details["hits"]["ratchet: evals"] == ["evals/cases/bar/"]


def test_ratchets_drop_eval_case_dot_rename_is_a_hit(tmp_path):
    root, _change = _ratchet_repo(tmp_path, BASE_PLAN)
    # git mv needs the destination directory to pre-exist; move by hand so git still sees it
    # as a rename (-M) once the content is unchanged
    dest = root / "evals" / "cases" / ".bar" / "only.yaml"
    dest.parent.mkdir(parents=True, exist_ok=True)
    (root / "evals" / "cases" / "bar" / "only.yaml").rename(dest)
    git(root, "add", "-A")
    git(root, "commit", "-q", "-m", "hide the bar case")
    res = checks.check_ratchets(gate.build_context(root, "0001", "c"))
    assert res.ok and "close-look banner" in res.reason  # decision 35: a hit, never a park
    assert res.details["hits"]["ratchet: evals"] == ["evals/cases/bar/"]


def test_ratchets_eval_case_dot_rename_wins_over_a_surviving_sibling(tmp_path):
    """Pins panel decision #1 (phase c fix round): the dot-prefixed-rename rule is
    evaluated independently of the survivor-emptiness rule, so a sibling left in place
    under the same case folder does not excuse the rename (spec.md Design)."""
    root, _change = _ratchet_repo(tmp_path, BASE_PLAN)
    dest = root / "evals" / "cases" / ".foo" / "a.yaml"
    dest.parent.mkdir(parents=True, exist_ok=True)
    (root / "evals" / "cases" / "foo" / "a.yaml").rename(dest)
    git(root, "add", "-A")
    git(root, "commit", "-q", "-m", "hide one file of the foo case, b.yaml survives")
    res = checks.check_ratchets(gate.build_context(root, "0001", "c"))
    assert res.ok and "close-look banner" in res.reason  # decision 35: a hit, never a park
    assert res.details["hits"]["ratchet: evals"] == ["evals/cases/foo/"]


def test_ratchets_drop_eval_case_declared_in_files_that_change_ok(tmp_path):
    root, _change = _ratchet_repo(tmp_path, PLAN_FILES_DECLARES_BAR)
    (root / "evals" / "cases" / "bar" / "only.yaml").unlink()
    git(root, "add", ".")
    git(root, "commit", "-q", "-m", "empty the bar case, declared")
    res = checks.check_ratchets(gate.build_context(root, "0001", "c"))
    assert res.ok, res.reason
    assert "evals/cases/bar/ (plan)" in res.details["declared"]


def test_ratchets_drop_eval_case_declared_in_proof_ok(tmp_path):
    root, _change = _ratchet_repo(tmp_path, PLAN_PROOF_DECLARES_EVALS)
    (root / "evals" / "cases" / "bar" / "only.yaml").unlink()
    git(root, "add", ".")
    git(root, "commit", "-q", "-m", "empty the bar case, declared via proof")
    res = checks.check_ratchets(gate.build_context(root, "0001", "c"))
    assert res.ok, res.reason


def test_ratchets_eval_case_partial_delete_is_not_a_drop(tmp_path):
    root, _change = _ratchet_repo(tmp_path, BASE_PLAN)
    (root / "evals" / "cases" / "foo" / "a.yaml").unlink()
    git(root, "add", ".")
    git(root, "commit", "-q", "-m", "drop one file of a multi-file case")
    res = checks.check_ratchets(gate.build_context(root, "0001", "c"))
    assert res.ok, res.reason


def test_ratchets_eval_case_internal_move_is_not_a_drop(tmp_path):
    root, _change = _ratchet_repo(tmp_path, BASE_PLAN)
    git(root, "mv", "evals/cases/foo/a.yaml", "evals/cases/foo/a2.yaml")
    git(root, "commit", "-q", "-m", "move within the same case")
    res = checks.check_ratchets(gate.build_context(root, "0001", "c"))
    assert res.ok, res.reason


def test_ratchets_accepted_hit_passes_on_later_run(tmp_path):
    root, change_dir = _ratchet_repo(tmp_path, BASE_PLAN)
    (root / "tests" / "test_keep.py").unlink()
    git(root, "add", ".")
    git(root, "commit", "-q", "-m", "drop a test")
    st = status_mod.read_status(change_dir)
    st.accept_risk("ratchet: tests")
    status_mod.write_status(change_dir, st)
    git(root, "add", ".")
    git(root, "commit", "-q", "-m", "accept the risk")
    res = checks.check_ratchets(gate.build_context(root, "0001", "c"))
    assert res.ok, res.reason
    assert res.details["accepted"] == ["ratchet: tests"]
    assert res.details["hits"] == {"ratchet: tests": ["tests/test_keep.py"]}  # still shown


def test_ratchets_risk_list_tests_configured_does_not_satisfy_ratchet_hit(tmp_path):
    root, change_dir = _ratchet_repo(
        tmp_path, BASE_PLAN, sdlc_yaml="risk_list:\n  - auth\n  - tests\n"
    )
    (root / "tests" / "test_keep.py").unlink()
    git(root, "add", ".")
    git(root, "commit", "-q", "-m", "drop a test")
    st = status_mod.read_status(change_dir)
    st.accept_risk("tests")  # accepts risk_list's bare item, not the ratchet
    status_mod.write_status(change_dir, st)
    git(root, "add", ".")
    git(root, "commit", "-q", "-m", "accept the bare risk-list item")
    ctx = gate.build_context(root, "0001", "c")
    ratchets_res = checks.check_ratchets(ctx)
    risk_res = checks.check_risk_list(ctx)
    assert ratchets_res.ok and ratchets_res.details["accepted"] == []  # reported, decision 35
    assert ratchets_res.details["hits"]["ratchet: tests"] == ["tests/test_keep.py"]
    assert risk_res.ok, risk_res.reason


def test_ratchets_skip_markers_listed_never_fail(tmp_path):
    """Skip markers are listed, never parked on (open question 2). The ``--deselect`` lines
    are this repository's own runbook test file, not a synthetic one — nine of them, the
    count the Risks section names; a small supplement covers the remaining fixed tokens."""
    runbook_test_text = (ROOT / "tests" / "test_detect_runbooks.py").read_text(encoding="utf-8")
    assert runbook_test_text.count("--deselect") == 9
    supplement = (
        "@pytest.mark.skip\n"
        "@pytest.mark.xfail\n"
        'pytest.skip("reason")\n'
        "--ignore=tests/slow\n"
        "-k not slow\n"
        "norecursedirs = build\n"
        'collect_ignore = ["setup.py"]\n'
        'it.skip("x", () => {})\n'
        'describe.skip("y", () => {})\n'
        '.only("z")\n'
        'test.todo("w")\n'
        "#[ignore]\n"
    )
    root, _change = _ratchet_repo(tmp_path, BASE_PLAN)
    write(root / "tests" / "test_detect_runbooks.py", "")
    write(root / "tests" / "test_skip_marker_supplement.py", "")
    git(root, "add", ".")
    git(root, "commit", "-q", "-m", "empty placeholders")
    write(root / "tests" / "test_detect_runbooks.py", runbook_test_text)
    write(root / "tests" / "test_skip_marker_supplement.py", supplement)
    git(root, "add", ".")
    git(root, "commit", "-q", "-m", "the real runbook test file and the token supplement")
    res = checks.check_ratchets(gate.build_context(root, "0001", "c"))
    assert res.ok, res.reason
    hit_tokens = {h["token"] for h in res.details["skip_markers"]}
    assert hit_tokens == set(checks.SKIP_MARKER_TOKENS)
    deselect_hits = [h for h in res.details["skip_markers"] if h["token"] == "--deselect"]
    assert len(deselect_hits) == 9
    assert all(h["file"] == "tests/test_detect_runbooks.py" for h in deselect_hits)


def test_ratchets_declaring_unknown_ratchet_name_is_inert(tmp_path):
    root, _change = _ratchet_repo(tmp_path, PLAN_PROOF_UNKNOWN_RATCHET)
    (root / "tests" / "test_keep.py").unlink()
    git(root, "add", ".")
    git(root, "commit", "-q", "-m", "drop a test, unrelated proof line present")
    res = checks.check_ratchets(gate.build_context(root, "0001", "c"))
    assert res.ok and "close-look banner" in res.reason  # decision 35: a hit, never a park
    assert res.details["hits"]["ratchet: tests"] == ["tests/test_keep.py"]


def test_checks_by_phase_ratchets_membership():
    assert checks.check_ratchets in checks.CHECKS_BY_PHASE["c"]
    assert checks.check_ratchets in checks.CHECKS_BY_PHASE["d"]
    assert checks.check_ratchets in checks.CHECKS_BY_PHASE["e"]
    for phase in ("a", "b", "f"):
        assert checks.check_ratchets not in checks.CHECKS_BY_PHASE[phase]


def test_risk_list_reads_the_committed_spec(design_project):
    """The spec's "Flagged concerns" are read at HEAD: clean_tree skips the change folder and
    does not run at (b), so an uncommitted edit of spec.md is not what the PR carries."""
    root, change = design_project
    concern = "- auth: the helper reads the caller's session token; the owner decides.\n"
    write(change / "spec.md", SPEC.replace("## Acceptance", concern + "\n## Acceptance"))
    verdict(root, "b")
    result = gate.run_gate(root, "0001", "b", dry_run=True)
    assert "risk_list" in _names(result, True), result.reason
    assert next(ch for ch in result.checks if ch.name == "risk_list").details["hits"] == {}
    git(root, "add", ".")
    git(root, "commit", "-q", "-m", "design(0001): a risk item flagged")
    verdict(root, "b")
    result = gate.run_gate(root, "0001", "b", dry_run=True)
    hit = next(ch for ch in result.checks if ch.name == "risk_list")
    assert hit.details["hits"] == {"auth": ["spec.md Flagged concerns: text"]}


def test_plan_sync_wants_plan_md_only_in_a_commit_that_departs_from_the_plan(project):
    """Article p.16 step 7: "When implementation departs from the plan, update plan.md in
    the same commit". The same run committed exactly the three files plan.md lists, one plan
    step per commit as /sdlc-build asks, and was parked because no commit carried plan.md.
    A commit whose source files are all planned needs no plan.md; a commit that touches a
    file the plan does not list still does."""
    root, change = project
    write(root / "sample_pkg" / "percent.py", PERCENT.replace("Percent helper", "Step 2"))
    git(root, "add", "sample_pkg/percent.py")
    git(root, "commit", "-q", "-m", "build: step 2 on a planned file, no plan.md")
    verdict(root, "c")
    result = gate.run_gate(root, "0001", "c", dry_run=True)
    assert "plan_sync" in _names(result, True), result.reason
    write(root / "sample_pkg" / "helper.py", "y = 2\n")
    git(root, "add", "sample_pkg/helper.py")
    git(root, "commit", "-q", "-m", "departure without plan.md")
    verdict(root, "c")
    result = gate.run_gate(root, "0001", "c", dry_run=True)
    p = next(ch for ch in result.failed if ch.name == "plan_sync")
    assert p.details["unplanned"] == ["sample_pkg/helper.py"]
    assert len(p.details["unsynced_commits"]) == 1  # the step-2 commit is inside the plan


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
    # an sdlc.yaml edited on the branch is ignored for limits (the base copy rules); while
    # uncommitted it is clean_tree's, and committed it is a guardrail hit (the gate judges
    # HEAD, deliverable 6(d)); the pause flag counts once the owner merged it
    assert result.config_note.startswith("sdlc.yaml changed on the branch")
    assert "paused" not in result.reason and "clean_tree" in _names(result, False)
    assert "guardrails" in _names(result, True)
    git(root, "add", "sdlc.yaml")
    git(root, "commit", "-q", "-m", "pause from the branch")
    verdict(root, "c")
    result = gate.run_gate(root, "0001", "c")
    assert result.config_note.startswith("sdlc.yaml changed on the branch")
    assert "paused" not in result.reason and "guardrails" in _names(result, False)
    git(root, "reset", "-q", "--soft", "HEAD~1")  # keeps the uncommitted iteration reset
    git(root, "reset", "-q", "--", "sdlc.yaml")
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
    recorded = json.loads(proc.stdout)
    assert proc.returncode == 0 and recorded["spend_usd"] == 0.4
    assert recorded["spend_usd_total"] == 0.4 and recorded["spend_entries"] == 1  # issue #71
    proc = run_py(
        str(GATE_CLI), "record-spend", "--root", str(root), "--id", "0001", "--phase", "e",
        "--usd", "0.65", "--run", "review", "--source", "claude-review.json", cwd=root,
    )  # fmt: skip
    assert proc.returncode == 0 and json.loads(proc.stdout)["spend_usd_total"] == 1.05
    ledger = json.loads((change / "evidence" / "spend.json").read_text(encoding="utf-8"))
    assert [(e["run"], e["source"], e["usd"]) for e in ledger["entries"]] == [
        ("c", None, 0.4),
        ("review", "claude-review.json", 0.65),
    ]
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
    assert cfg["max_iterations"] == 3 and cfg["max_budget_usd"] == 150  # decision 32
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
def test_gate_b_waits_for_the_owner(design_project, monkeypatch):
    root, change = design_project
    verdict(root, "b")
    result = gate.run_gate(root, "0001", "b", dry_run=True)
    assert result.result == "wait", result.reason
    assert result.label == "sdlc:b-ready"
    assert _names(result, False) == []
    assert set(_names(result, True)) == {
        "limits",
        "artifacts",
        "evidence_links",
        "design_scope",
        "open_concerns",
        "panel",
        "commands",
        "guardrails",
        "risk_list",
        "owner_actions",
        "adversarial_review",
        "reviewer_model",
    }
    # decision 37 (1.0.21): a project file that still says ``profile: full`` or
    # ``review: parked`` waits the same; the keys are not read, and the result names them
    loaded = gate.load_sdlc_config
    monkeypatch.setattr(
        gate, "load_sdlc_config", lambda r: {**loaded(r), "profile": "full", "review": "parked"}
    )
    result = gate.run_gate(root, "0001", "b", dry_run=True)
    assert result.result == "wait", result.reason
    assert result.label == "sdlc:b-ready" and result.human_gate is True
    assert "profile: full" in result.config_note and "decision 37" in result.config_note


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


def test_gate_b_judges_the_committed_diff_not_the_working_tree(design_project):
    """The gate at (b) may run inside Claude Code's sandbox, which masks .env, .idea and
    .vscode: the third live design run (2026-09-21) parked on them although the committed
    diff held only the change folder. The working tree is reported, never a park."""
    root, _change = design_project
    (root / ".env").write_text("SANDBOX=1\n", encoding="utf-8")  # tracked and "modified"
    (root / ".idea").mkdir()
    write(root / ".idea" / "workspace.xml", "<project/>\n")  # untracked, not empty
    (root / ".bashrc").write_text("", encoding="utf-8")  # zero bytes: a placeholder
    verdict(root, "b")
    result = gate.run_gate(root, "0001", "b", dry_run=True)
    assert "design_scope" not in _names(result, False), result.reason
    ds = next(ch for ch in result.checks if ch.name == "design_scope")
    assert ".env" in ds.details["dirty"] and ".idea/workspace.xml" in ds.details["dirty"]
    assert ".bashrc" not in ds.details["dirty"]  # an empty placeholder is not even reported
    assert result.result == "wait"

    # an uncommitted stray is reported and still does not park: only the PR's diff counts
    write(root / "stray.py", "x = 1\n")
    verdict(root, "b")
    result = gate.run_gate(root, "0001", "b", dry_run=True)
    assert "design_scope" not in _names(result, False), result.reason
    ds = next(ch for ch in result.checks if ch.name == "design_scope")
    assert "stray.py" in ds.details["dirty"]


def test_the_sandbox_s_mask_is_read_from_its_mounts(tmp_path):
    """A file the sandbox masks is /dev/null bound over it, a mount point whose entry is a
    character device; a directory it masks is a tmpfs mount (reproduced with ``mount
    --bind`` in the container, 2026-10-03). A character device that is no mount point is
    not a mask: a session can make one with ``os.mknod`` (a 0:0 device, no privilege needed
    on current kernels) over a tracked file or directory, and the review of the 0.3.4 diff
    showed pytest then skips it while git reads it as modified or deleted — it stays
    reported. A plain file, a plain directory and a missing path are not masked."""
    plain = tmp_path / "plain.txt"
    plain.write_text("x", encoding="utf-8")
    assert checks.diffmod._mount_masked(plain) is False
    assert checks.diffmod._mount_masked(tmp_path) is False
    assert checks.diffmod._mount_masked(tmp_path / "missing") is False
    if os.name != "nt":
        assert checks.diffmod._mount_masked(Path("/dev/null")) is False  # a device, no mount
        assert checks.diffmod._mount_masked(Path("/")) is True  # a mount point, a directory
        forged = tmp_path / "forged.env"
        try:
            os.mknod(forged, stat.S_IFCHR | 0o644, 0)  # a 0:0 character device
        except (PermissionError, OSError):
            pytest.skip("mknod of a 0:0 character device not allowed here")
        assert checks.diffmod._mount_masked(forged) is False


def test_clean_tree_ignores_a_nested_env_the_sandbox_mounted_over(project, monkeypatch):
    """Change 0001's second build run on 0.3.3 (2026-10-03, run 37138722554): inside the
    session the sandbox mounts /dev/null over every ``.env*`` the deny rule names, at any
    depth, so this repository's tracked ``tests/fixtures/sample-python-project/.env`` read
    as modified and gate (c) parked on ``clean_tree`` with every other check green. What the
    sandbox mounted over is its view, not the change's (0.3.4), inside a CI session only; a
    nested ``.env.local`` the session wrote, with no mount over it, is still the session's
    uncommitted work, and the checkout's root is never a mask."""
    root, _change = project
    nested = root / "tests" / "fixtures" / "inner" / ".env"
    nested.parent.mkdir(parents=True)
    nested.write_text("FIXTURE=1\n", encoding="utf-8")
    secret = root / "config" / "secrets" / "README.md"
    secret.parent.mkdir(parents=True)
    secret.write_text("kept\n", encoding="utf-8")
    git(root, "add", "tests/fixtures/inner/.env", "config/secrets/README.md")
    git(root, "commit", "-q", "-m", "a nested fixture .env and a secrets folder, tracked")
    nested.write_text("", encoding="utf-8")  # what the mask looks like to git: modified
    secret.unlink()  # under a tmpfs-masked directory: deleted
    masked = {root / "tests" / "fixtures" / "inner" / ".env", root / "config" / "secrets", root}
    monkeypatch.setattr(checks.diffmod, "_mount_masked", lambda path: Path(path) in masked)
    monkeypatch.setenv(checks.COMMANDS_RUNNER_ENV, checks.RUN_BY_RUNNER)  # a CI session
    verdict(root, "c")
    result = gate.run_gate(root, "0001", "c", dry_run=True)
    assert "clean_tree" not in _names(result, False), result.reason
    ct = next(ch for ch in result.checks if ch.name == "clean_tree")
    assert ct.details["ignored"] == ["config/secrets/README.md", "tests/fixtures/inner/.env"]
    # an untracked nested .env.local with content, not mounted over: the session's work
    # (the root being a mount point, as in a container, masks nothing below it)
    write(root / "tests" / "fixtures" / "inner" / ".env.local", "X=1\n")
    result = gate.run_gate(root, "0001", "c", dry_run=True)
    ct = next(ch for ch in result.failed if ch.name == "clean_tree")
    assert ct.details["dirty"] == ["tests/fixtures/inner/.env.local"]
    (root / "tests" / "fixtures" / "inner" / ".env.local").unlink()
    # by hand (no mark) a mount over a tracked path is nobody's mask: everything is reported
    monkeypatch.delenv(checks.COMMANDS_RUNNER_ENV)
    result = gate.run_gate(root, "0001", "c", dry_run=True)
    ct = next(ch for ch in result.failed if ch.name == "clean_tree")
    assert ct.details["dirty"] == ["config/secrets/README.md", "tests/fixtures/inner/.env"]
    # and inside a CI session with nothing mounted over, the same
    monkeypatch.setenv(checks.COMMANDS_RUNNER_ENV, checks.RUN_BY_RUNNER)
    monkeypatch.setattr(checks.diffmod, "_mount_masked", lambda path: False)
    result = gate.run_gate(root, "0001", "c", dry_run=True)
    ct = next(ch for ch in result.failed if ch.name == "clean_tree")
    assert ct.details["dirty"] == ["config/secrets/README.md", "tests/fixtures/inner/.env"]


def test_dirty_files_reads_a_staged_rename_as_two_paths(project):
    """``git status --porcelain -z`` writes a rename as two records, the second without a
    status prefix (the review of the 0.3.4 diff, finding 6)."""
    root, _change = project
    git(root, "mv", "sample_pkg/calc.py", "sample_pkg/calc_renamed.py")
    dirty = checks.diffmod.dirty_files(root)
    assert "sample_pkg/calc.py" in dirty and "sample_pkg/calc_renamed.py" in dirty
    assert not any(f.startswith("mple_pkg") for f in dirty)


def test_gate_b_parks_on_a_stray_file_the_branch_committed(design_project):
    """What the branch carries is the verdict: a source file committed outside the change
    folder is the departure from phase (b) design_scope exists to catch."""
    root, _change = design_project
    write(root / "stray.py", "x = 1\n")
    git(root, "add", "stray.py")
    git(root, "commit", "-q", "-m", "a file phase (b) had no business writing")
    verdict(root, "b")
    result = gate.run_gate(root, "0001", "b", dry_run=True)
    assert result.result == "park"
    ds = next(ch for ch in result.failed if ch.name == "design_scope")
    assert ds.details["outside"] == ["stray.py"]
    assert "phase (c)" in ds.need


def test_clean_tree_ignores_the_placeholders_and_the_masked_paths(project):
    """At (c), (d) and (e) the working tree is still the verdict - but neither the sandbox's
    empty placeholders nor the paths it masks (diff.SANDBOX_MASKED) are anyone's work."""
    root, _change = project
    (root / ".bashrc").write_text("", encoding="utf-8")
    (root / ".env").write_text("SANDBOX=1\n", encoding="utf-8")  # tracked: shows as modified
    write(root / ".vscode" / "settings.json", "{}\n")  # untracked, not empty
    (root / ".idea").mkdir()
    verdict(root, "c")
    result = gate.run_gate(root, "0001", "c", dry_run=True)
    assert "clean_tree" not in _names(result, False), result.reason
    ct = next(ch for ch in result.checks if ch.name == "clean_tree")
    assert ct.details["ignored"] == [".bashrc", ".env", ".vscode/settings.json"]
    assert checks.diffmod.sandbox_placeholders(root, [".idea/"]) == [".idea/"]
    assert checks.diffmod.sandbox_masked([".env", "src/.env", ".idea/x"]) == [".env", ".idea/x"]

    write(root / "sample_pkg" / "calc.py", "x = 1\n")  # real work, uncommitted
    result = gate.run_gate(root, "0001", "c", dry_run=True)
    ct = next(ch for ch in result.failed if ch.name == "clean_tree")
    assert ct.details["dirty"] == ["sample_pkg/calc.py"]


def test_clean_tree_sets_aside_the_review_pass_s_record(project):
    """``changes/.review-seen.json`` is written by ``review/cli.py validate`` right before the
    gate reads the findings beside it, and lives outside the change folder (one file per
    project): until 0.3.5 the gate read it as uncommitted work, and every fix round of change
    0001 at gate (e) parked on it (2026-10-03, PROGRESS "Session 19"). At (d) and (e),
    untracked or modified, it is set aside and listed under ``ignored``; a sibling under
    changes/ is still work, and so is anything at that path that is not the record's shape."""
    root, change = project

    def clean_tree_at(phase: str):
        st = status_mod.read_status(change)
        st.set_phase(phase)  # the gate refuses a phase status.yaml does not carry
        status_mod.write_status(change, st)
        result = gate.run_gate(root, "0001", phase, dry_run=True)
        return next(ch for ch in result.checks if ch.name == "clean_tree")

    seen = root / "changes" / ".review-seen.json"
    write(seen, '{"27da52344010278e": {"count": 1, "first_change": "0001"}}\n')  # untracked
    verdict(root, "c")
    ct = clean_tree_at("c")  # (c): the review pass never runs there
    assert not ct.ok and ct.details["dirty"] == ["changes/.review-seen.json"]
    for phase in ("d", "e"):
        ct = clean_tree_at(phase)
        assert ct.ok, ct.reason
        assert ct.details["ignored"] == ["changes/.review-seen.json"]

    git(root, "add", "changes/.review-seen.json")
    git(root, "commit", "-q", "-m", "review record")
    write(seen, '{"27da52344010278e": {"count": 2, "first_change": "0001"}}\n')  # modified
    ct = clean_tree_at("e")
    assert ct.ok, ct.reason
    assert ct.details["ignored"] == ["changes/.review-seen.json"]

    write(root / "changes" / "scratch.json", "{}\n")  # any other file under changes/ is work
    ct = clean_tree_at("e")
    assert not ct.ok
    assert ct.details["dirty"] == ["changes/scratch.json"]
    assert ct.details["ignored"] == ["changes/.review-seen.json"]
    (root / "changes" / "scratch.json").unlink()

    # the review of the 0.3.5 diff: only the record's own shape is set aside — a deleted
    # record, a non-JSON payload or a symlink at that path is work the gate reports
    seen.write_text("not json\n", encoding="utf-8")
    ct = clean_tree_at("e")
    assert not ct.ok
    assert ct.details["dirty"] == ["changes/.review-seen.json"] and ct.details["ignored"] == []
    seen.unlink()
    ct = clean_tree_at("e")
    assert not ct.ok
    assert ct.details["dirty"] == ["changes/.review-seen.json"]
    if os.name != "nt":
        seen.symlink_to(root / "sample_pkg" / "calc.py")
        ct = clean_tree_at("e")
        assert not ct.ok
        assert ct.details["dirty"] == ["changes/.review-seen.json"]


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
    result = gate.run_gate(root, "0001", "c", dry_run=True)
    assert result.result == "continue", result.reason


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


# --- the risk-list check reads the diff and the "Flagged concerns" section, never the prose --
RISK_PROSE = (
    "Checked sdlc.yaml risk_list: auth, data migrations, money movement and production "
    "config are not touched by this design.\n"
)


def test_gate_b_ignores_risk_list_words_in_the_spec_s_prose(design_project):
    """Security-baseline rule 8 makes every spec name the risk items it checked; the fifth
    live design run (2026-09-21) parked on exactly that sentence."""
    root, change = design_project
    write(change / "spec.md", SPEC.replace("## Design\n", "## Design\n" + RISK_PROSE))
    git(root, "add", ".")
    git(root, "commit", "-q", "-m", "design(0001): the spec names the risk items it checked")
    verdict(root, "b")
    result = gate.run_gate(root, "0001", "b", dry_run=True)
    assert result.result == "wait", result.reason
    assert "risk_list" not in _names(result, False)


def test_gate_b_reports_a_risk_list_item_declared_under_flagged_concerns(design_project):
    """Decision 35: the item named under "Flagged concerns" is a hit the design PR's banner
    shows; the open concern parks on its own check, never on risk_list."""
    root, change = design_project
    concern = "- auth: the helper reads the caller's session token; the owner decides.\n"
    write(change / "spec.md", SPEC.replace("## Acceptance", concern + "\n## Acceptance"))
    git(root, "add", ".")
    git(root, "commit", "-q", "-m", "design(0001): a risk item flagged")
    verdict(root, "b")
    result = gate.run_gate(root, "0001", "b", dry_run=True)
    assert result.result == "park" and "open_concerns" in _names(result, False)
    assert "risk_list" not in _names(result, False)
    hit = next(ch for ch in result.checks if ch.name == "risk_list")
    assert hit.details["hits"] == {"auth": ["spec.md Flagged concerns: text"]}
    # the declaration the spec-template skill asks for is closed: the design waits for the
    # owner's merge, which accepts the item, and parks on nothing
    declared = (
        "- decided (decision 35): risk item 'auth': the helper reads the caller's session "
        "token; the close-look banner shows it and the owner's merge accepts it.\n"
    )
    write(change / "spec.md", SPEC.replace("## Acceptance", declared + "\n## Acceptance"))
    git(root, "commit", "-q", "-am", "design(0001): the risk item declared")
    verdict(root, "b", classification="non-routine")
    result = gate.run_gate(root, "0001", "b", dry_run=True)
    assert result.result == "wait", result.reason
    hit = next(ch for ch in result.checks if ch.name == "risk_list")
    assert hit.details["hits"] == {"auth": ["spec.md Flagged concerns: text"]}


# --- decision 24: the owner's label, performed and committed by the CI run ---------------------
def _label_act(change: Path, label: str, actor: str, items=("auth",)) -> None:
    from state import conventions as c

    st = status_mod.read_status(change)
    if label == c.ACCEPT_RISK_LABEL:
        # the label retired with decision 35 (1.0.15); a status.yaml its fix round wrote
        # before then carries the item and the label's actor, which owner_actions honours
        for item in items:
            st.accept_risk(item)
            st.risk_accepted_by = [e for e in st.risk_accepted_by if e["item"] != item] + [
                {"item": item, "actor": actor}
            ]
    else:
        st.record_owner_label(label, actor)
    status_mod.write_status(change, st)


def test_owner_actions_honours_a_label_the_owner_applied_and_the_run_committed(project):
    """The CI run performs sdlc:accept-risk and commits status.yaml under the automation
    identity; the recorded actor is what the check reads (a person: passes)."""
    from state import conventions as c

    root, change = project
    _label_act(change, c.ACCEPT_RISK_LABEL, "luissiviero")
    commit_all(root, "owner labels applied: sdlc:accept-risk", author=BOT_AUTHOR)
    verdict(root, "c")
    result = gate.run_gate(root, "0001", "c", dry_run=True)
    assert "owner_actions" not in _names(result, False)
    oa = next(ch for ch in result.checks if ch.name == "owner_actions")
    assert oa.details["label_actors"] == {"risk_accepted": {"auth": "luissiviero"}}
    assert "applied by the owner's label" in oa.reason


def test_owner_actions_honours_a_second_reset_by_the_same_person(project):
    """The second sdlc:reset-iterations on sample change 0002 (2026-09-24) parked: the actor
    field already said luissiviero, so the commit that lowered the count changed no actor.
    Since 0.2.17 the act is recorded by its stamp (``iterations_reset_at``) as well."""
    from state import conventions as c

    root, change = project
    st = status_mod.read_status(change)
    st.iterations = 2
    status_mod.write_status(change, st)
    commit_all(root, "build(0001): two fix rounds")
    _label_act(change, c.RESET_ITERATIONS_LABEL, "luissiviero")
    commit_all(root, "owner labels applied: sdlc:reset-iterations", author=BOT_AUTHOR)
    st = status_mod.read_status(change)
    assert st.iterations == 0 and st.panel_calls == 0 and st.iterations_reset_at
    first_stamp = st.iterations_reset_at
    st.iterations = 1
    status_mod.write_status(change, st)
    commit_all(root, "fix(0001): one round")
    import time

    time.sleep(1.1)  # the stamp has second resolution; the second act must differ
    _label_act(change, c.RESET_ITERATIONS_LABEL, "luissiviero")  # the same person again
    commit_all(root, "owner labels applied: sdlc:reset-iterations", author=BOT_AUTHOR)
    st = status_mod.read_status(change)
    assert st.iterations_reset_by == "luissiviero" and st.iterations_reset_at != first_stamp
    verdict(root, "c")
    result = gate.run_gate(root, "0001", "c", dry_run=True)
    assert "owner_actions" not in _names(result, False), result.reason
    oa = next(ch for ch in result.checks if ch.name == "owner_actions")
    assert oa.details["label_actors"] == {"iterations_reset": "luissiviero"}
    # a drop with neither a new actor nor a new stamp is still the run's own act: rejected
    st = status_mod.read_status(change)
    st.iterations = 1
    status_mod.write_status(change, st)
    commit_all(root, "fix(0001): another round")
    st = status_mod.read_status(change)
    st.iterations = 0  # no label: actor and stamp unchanged
    status_mod.write_status(change, st)
    commit_all(root, "owner labels applied: sdlc:reset-iterations", author=BOT_AUTHOR)
    verdict(root, "c")
    result = gate.run_gate(root, "0001", "c", dry_run=True)
    assert "owner_actions" in _names(result, False)


def test_owner_actions_accepts_the_runner_s_marked_reset_only_with_its_record(project):
    """Decision 29 (1.0.3): the runner's one judged reset at the cap is marked
    ``sdlc-runner:<run>`` and recorded in evidence/auto-reset.json; the check accepts that
    drop on the record's word, lists it apart from the owner's label acts, and refuses the
    same marking without the record (before 1.0.3 any non-bot string passed as a person)."""
    from state import conventions as c

    root, change = project
    st = status_mod.read_status(change)
    st.iterations = 3
    status_mod.write_status(change, st)
    commit_all(root, "build(0001): three automatic rounds")
    st = status_mod.read_status(change)
    st.iterations = 0
    st.panel_calls = 0
    st.iterations_reset_by = "sdlc-runner:777"
    st.iterations_reset_at = "2026-10-17T10:00:00Z"
    status_mod.write_status(change, st)
    sha = commit_all(root, "run(c): judged reset (decision 29)", author=BOT_AUTHOR)
    verdict(root, "c")
    result = gate.run_gate(root, "0001", "c", dry_run=True)
    oa = next(ch for ch in result.failed if ch.name == "owner_actions")
    assert f"iterations dropped from 3 to 0 in commit {sha[:10]}" in oa.reason
    assert "'sdlc-runner:777' is not a person" in oa.reason
    record = {"reset": True, "actor": "sdlc-runner:777", "at": "2026-10-17T10:00:00Z"}
    write(change / "evidence" / c.AUTO_RESET_FILE, json.dumps(record))
    result = gate.run_gate(root, "0001", "c", dry_run=True)
    assert "owner_actions" not in _names(result, False), result.reason
    oa = next(ch for ch in result.checks if ch.name == "owner_actions")
    assert oa.details["runner_resets"] == {"iterations_reset": "sdlc-runner:777"}
    assert oa.details["label_actors"] == {}  # not a person's act
    # a record of another stamp is not this reset
    write(change / "evidence" / c.AUTO_RESET_FILE, json.dumps({**record, "at": "2026-10-18"}))
    assert "owner_actions" in _names(gate.run_gate(root, "0001", "c", dry_run=True), False)


def test_owner_actions_rejects_a_label_actor_that_is_the_automation_identity(project):
    """A recorded actor that is a bot never passes, whoever wrote the commit: a run cannot
    un-park itself (decision 11)."""
    from state import conventions as c

    root, change = project
    st = status_mod.read_status(change)
    st.iterations = 2
    status_mod.write_status(change, st)
    commit_all(root, "build(0001): two fix rounds")
    st = status_mod.read_status(change)
    st.iterations = 0
    st.iterations_reset_by = "github-actions[bot]"
    status_mod.write_status(change, st)
    sha = commit_all(root, "owner labels applied: sdlc:reset-iterations", author=BOT_AUTHOR)
    verdict(root, "c")
    result = gate.run_gate(root, "0001", "c", dry_run=True)
    oa = next(ch for ch in result.failed if ch.name == "owner_actions")
    assert f"iterations dropped from 2 to 0 in commit {sha[:10]}" in oa.reason
    assert "'github-actions[bot]' is not a person" in oa.reason
    assert "sdlc:reset-iterations" in oa.need
    # the same drop recorded with the owner's login passes
    git(root, "reset", "-q", "--hard", "HEAD~1")
    _label_act(change, c.RESET_ITERATIONS_LABEL, "luissiviero")
    commit_all(root, "owner labels applied: sdlc:reset-iterations", author=BOT_AUTHOR)
    verdict(root, "c")
    result = gate.run_gate(root, "0001", "c", dry_run=True)
    assert result.result == "continue", result.reason
    oa = next(ch for ch in result.checks if ch.name == "owner_actions")
    assert oa.details["label_actors"] == {"iterations_reset": "luissiviero"}
    # a bot-authored acceptance with no actor recorded is the CLI case: still refused
    git(root, "reset", "-q", "--hard", "HEAD~1")
    accept_risk(root, change)
    commit_all(root, "accept the auth risk", author=BOT_AUTHOR)
    verdict(root, "c")
    oa = next(
        ch for ch in gate.run_gate(root, "0001", "c", dry_run=True).failed
        if ch.name == "owner_actions"
    )  # fmt: skip
    assert "no owner label actor is recorded" in oa.reason


# --- gate (f): the incident intent, the finding and its route (build guide steps 37 and 39;
# --- decisions 14, 25, 26; plugin 0.2.19) ---------------------------------------------------------
INCIDENT_INTENT = """# Intent: ci_test_failure_rate breached 3sigma (we1) on 2026-09-24
Author: maintain run (phase f). Status: proposed. Change id: 0002. Entry route: incident abc.

## Problem
The CI test failure rate went from 0 to 1.0 on 2026-09-24.

## Proposed outcome
The flaky test is quarantined until its cause is fixed.

## Affected users and systems
CI of sample_pkg.

## Constraints
No test is edited.

## Open questions
none

## Evidence
we1 at 3sigma: mean 0.0, sigma 0.0, latest 1.0 on 2026-09-24; run https://x/runs/1.
"""


def _detection_record(tier: int = 3, rule: str = "we1") -> dict:
    from detect import finding

    verdict = {
        "tier": tier,
        "rules_hit": [rule],
        "rule": rule,
        "latest": {"at": "2026-09-24", "value": 1.0, "meta": {}},
        "mean": 0.0,
        "sigma": 0.0,
        "sigmas": "inf",
        "n_baseline": 20,
        "n_tail": 8,
        "window_days": 30,
        "direction": "above",
        "reason": "one point beyond 3 sigma",
        "breach_start": "2026-09-24",
    }
    return finding.build_record(
        metric="ci_test_failure_rate",
        source="github-actions",
        verdict=verdict,
        observations=[],
        action="propose",
        failed_run_urls=["https://x/runs/1"],
        commits=[],
    )


@pytest.fixture
def maintain_project(tmp_path):
    """Fixture copy initialised, and an incident change 0002 filed at phase (f) on its
    sdlc/0002/a branch: the detection record, the intent and a pull_request proposal."""
    from detect import finding

    root, _change = _initialised_fixture(tmp_path)
    git(root, "add", ".")
    git(root, "commit", "-q", "-m", "change 0001 (as if merged)")
    proc = run_py(
        str(STATE_CLI), "new-change", "--root", str(root), "--title", "CI failure rate breach",
        "--route", "incident", "--type", "fix", cwd=root,
    )  # fmt: skip
    assert proc.returncode == 0, proc.stderr
    change = root / "changes" / "0002-ci-failure-rate-breach"
    git(root, "checkout", "-q", "-b", "sdlc/0002/a")
    st = status_mod.read_status(change)
    st.set_phase("f")
    status_mod.write_status(change, st)
    finding.write(change / "evidence" / finding.DETECTION_FILE, _detection_record())
    write(change / "intent.md", INCIDENT_INTENT)
    write(
        change / "evidence" / finding.PROPOSAL_FILE,
        json.dumps({"schema_version": 1, "tier": 3, "route": "pull_request", "args": {},
                    "rationale": "no runbook fits"}),
    )  # fmt: skip
    git(root, "add", ".")
    git(root, "commit", "-q", "-m", "maintain(0002): diagnosis")
    proc = run_py(
        str(GATE_CLI), "start-run", "--root", str(root), "--id", "0002", "--phase", "f", cwd=root
    )
    assert proc.returncode == 0, proc.stderr
    return root, change


def test_gate_f_waits_for_the_owner_s_triage_with_the_finding_and_its_route(maintain_project):
    root, change = maintain_project
    result = gate.run_gate(root, "0002", "f")
    assert result.result == "wait" and result.label == "sdlc:f-ready", result.reason
    names = [ch.name for ch in result.checks]
    assert names == ["limits", "artifacts", "evidence_links", "design_scope", "guardrails",
                     "risk_list", "detection", "route"]  # fmt: skip
    detection = next(ch for ch in result.checks if ch.name == "detection")
    assert detection.details["tier"] == 3 and detection.details["rule"] == "we1"
    route = next(ch for ch in result.checks if ch.name == "route")
    assert "this intent PR is the route" in route.reason
    assert (change / "evidence" / "gate-f.json").is_file()
    # the change stays at phase f: the owner's merge is gate (a) of this intent (decision 25)
    assert status_mod.read_status(change).phase == "f"


def test_gate_f_parks_on_an_intent_without_its_evidence_section(maintain_project):
    root, change = maintain_project
    write(change / "intent.md", INCIDENT_INTENT.split("## Evidence")[0])
    git(root, "commit", "-q", "-am", "drop the evidence")
    result = gate.run_gate(root, "0002", "f")
    assert result.result == "park"
    artifacts = next(ch for ch in result.checks if ch.name == "artifacts")
    assert not artifacts.ok and "## Evidence" in artifacts.reason


def test_gate_f_parks_on_a_dismissed_finding_and_on_a_logged_tier(maintain_project):
    from detect import dismissals, finding

    root, change = maintain_project
    record = _detection_record()
    path = dismissals.path_for(root)
    dismissals.save(
        path,
        dismissals.add(dismissals.load(path), record["signature"], kind="detect",
                       reason="known flaky suite", by="owner", change_id="0001"),
    )  # fmt: skip
    result = gate.run_gate(root, "0002", "f")
    detection = next(ch for ch in result.checks if ch.name == "detection")
    assert result.result == "park" and not detection.ok
    assert "dismissed by owner" in detection.reason and "known flaky suite" in detection.reason
    path.unlink()
    finding.write(change / "evidence" / finding.DETECTION_FILE, _detection_record(1, "we3"))
    git(root, "commit", "-q", "-am", "a 1 sigma record")
    result = gate.run_gate(root, "0002", "f")
    detection = next(ch for ch in result.checks if ch.name == "detection")
    assert not detection.ok and "only logs" in detection.reason


def test_gate_f_route_go_requested_parks_and_a_ran_runbook_passes(maintain_project):
    root, change = maintain_project
    proposal = change / "evidence" / "proposal.json"
    write(
        proposal,
        json.dumps({"schema_version": 1, "tier": 3, "route": "runbook:rollback-deploy",
                    "args": {}, "rationale": "a deploy in the window"}),
    )  # fmt: skip
    # the template lists rollback-deploy with authorization go and the fixture declares no
    # runbook command: unsupported, so the proposal is refused with that reason
    result = gate.run_gate(root, "0002", "f")
    route = next(ch for ch in result.checks if ch.name == "route")
    assert result.result == "park" and "no runbook named 'rollback-deploy'" in route.reason
    write(
        proposal,
        json.dumps({"schema_version": 1, "tier": 3, "route": "runbook:revert-pr",
                    "args": {"sha": "0" * 40}, "rationale": "commit x broke it"}),
    )  # fmt: skip
    result = gate.run_gate(root, "0002", "f")
    route = next(ch for ch in result.checks if ch.name == "route")
    assert not route.ok and "no evidence/runbook-revert-pr.json" in route.reason
    record = change / "evidence" / "runbook-revert-pr.json"
    write(record, json.dumps({"runbook": "revert-pr", "status": "go-requested"}))
    result = gate.run_gate(root, "0002", "f")
    route = next(ch for ch in result.checks if ch.name == "route")
    assert not route.ok and "Go requested" in route.reason and "`sdlc:go`" in route.need
    write(record, json.dumps({"runbook": "revert-pr", "status": "failed", "reason": "conflicts"}))
    result = gate.run_gate(root, "0002", "f")
    route = next(ch for ch in result.checks if ch.name == "route")
    assert not route.ok and "conflicts" in route.reason
    write(record, json.dumps({"runbook": "revert-pr", "status": "ran", "pr_url": "https://x/9"}))
    git(root, "add", ".")
    git(root, "commit", "-q", "-m", "route recorded")
    result = gate.run_gate(root, "0002", "f")
    route = next(ch for ch in result.checks if ch.name == "route")
    assert route.ok and "https://x/9" in route.reason and result.result == "wait"


def test_gate_f_parks_when_the_diagnosis_committed_source(maintain_project):
    root, change = maintain_project
    write(root / "sample_pkg" / "hotfix.py", "x = 1\n")
    git(root, "add", ".")
    git(root, "commit", "-q", "-m", "a fix the diagnosis must not make")
    result = gate.run_gate(root, "0002", "f")
    scope = next(ch for ch in result.checks if ch.name == "design_scope")
    assert result.result == "park" and not scope.ok and "phase (f)" in scope.need


# --- lesson and eval, gate (e) only (change 0003) ---------------------------------------------
from lessons import index as lessons_index  # noqa: E402
from tests.test_lessons import write_lesson  # noqa: E402

LESSON_SLUG = "x"  # matches _ctx's Status(slug="x")


def _lesson_setup(
    tmp_path,
    lesson_overrides=None,
    write_lesson_file=True,
    write_index=True,
    write_eval=True,
    missing_eval_file=None,
    extra_lesson_name=None,
):
    """Everything ``lesson_and_eval`` reads for change 0001-x, each piece switchable so a
    fail case can drop exactly one thing."""
    if write_lesson_file:
        write_lesson(tmp_path / "lessons" / f"2026-10-{LESSON_SLUG}.md", **(lesson_overrides or {}))
    if extra_lesson_name:
        write_lesson(tmp_path / "lessons" / extra_lesson_name)
    if write_index:
        text, _notes = lessons_index.build(tmp_path, today="2026-10-08")
        write(tmp_path / "lessons" / "index.md", text)
    if write_eval:
        eval_dir = tmp_path / "evals" / "cases" / f"0001-{LESSON_SLUG}"
        if missing_eval_file != "prompt.md":
            write(eval_dir / "prompt.md", "Incident 0001: x.\n")
        if missing_eval_file != "checks.yaml":
            write(eval_dir / "checks.yaml", "checks:\n  - command: pytest\n    exit: 0\n")
    return tmp_path


def _e_ctx(tmp_path):
    return _ctx(tmp_path, phase="e", entry_route="incident")


def test_lesson_and_eval_passes_when_everything_is_present(tmp_path):
    _lesson_setup(tmp_path)
    res = checks.lesson_and_eval(_e_ctx(tmp_path))
    assert res.ok, res.reason


def test_lesson_and_eval_does_not_run_outside_an_incident_change_at_gate_e(tmp_path):
    assert checks.lesson_and_eval(_ctx(tmp_path, phase="e", entry_route="idea")).ok
    assert checks.lesson_and_eval(_ctx(tmp_path, phase="c", entry_route="incident")).ok


def test_lesson_and_eval_guard_holds_even_called_directly_at_phase_f(tmp_path):
    """The guard itself, not only its absence from CHECKS_BY_PHASE['f']: an incident change
    at phase (f) has neither the lesson nor the eval yet, and the check must still pass."""
    res = checks.lesson_and_eval(_ctx(tmp_path, phase="f", entry_route="incident"))
    assert res.ok, res.reason
    assert "lesson_and_eval" not in [fn.__name__ for fn in checks.CHECKS_BY_PHASE["f"]]


def test_lesson_and_eval_fails_on_a_missing_lesson_file(tmp_path):
    _lesson_setup(tmp_path, write_lesson_file=False, write_index=False)
    res = checks.lesson_and_eval(_e_ctx(tmp_path))
    assert not res.ok
    assert any("no lesson file matches" in p for p in res.need.split("\n    "))


def test_lesson_and_eval_fails_on_two_lesson_files_matching_the_glob(tmp_path):
    _lesson_setup(tmp_path, extra_lesson_name=f"2026-11-{LESSON_SLUG}.md")
    res = checks.lesson_and_eval(_e_ctx(tmp_path))
    assert not res.ok
    assert any("2 lesson files match" in p for p in res.need.split("\n    "))


def test_lesson_and_eval_fails_on_a_missing_required_frontmatter_field(tmp_path):
    _lesson_setup(tmp_path, lesson_overrides={"change": None}, write_index=False)
    res = checks.lesson_and_eval(_e_ctx(tmp_path))
    assert not res.ok
    assert any("'change' missing or not a scalar" in p for p in res.need.split("\n    "))


def test_lesson_and_eval_fails_on_a_wrong_type_frontmatter_field(tmp_path):
    """A field that is present but the wrong shape (here a scalar where ``tags`` wants a
    list) is reported with the same wording as an absent one, not as "missing"."""
    _lesson_setup(tmp_path, lesson_overrides={"tags": "flaky-test"}, write_index=False)
    res = checks.lesson_and_eval(_e_ctx(tmp_path))
    assert not res.ok
    assert any("'tags' missing or not a list" in p for p in res.need.split("\n    "))


def test_lesson_and_eval_fails_when_prompt_or_checks_yaml_is_missing(tmp_path):
    _lesson_setup(tmp_path, missing_eval_file="prompt.md")
    res = checks.lesson_and_eval(_e_ctx(tmp_path))
    assert not res.ok
    assert any("prompt.md is missing" in p for p in res.need.split("\n    "))

    (tmp_path / "evals" / "cases" / f"0001-{LESSON_SLUG}" / "checks.yaml").unlink()
    write(tmp_path / "evals" / "cases" / f"0001-{LESSON_SLUG}" / "prompt.md", "Incident 0001: x.\n")
    res = checks.lesson_and_eval(_e_ctx(tmp_path))
    assert not res.ok
    assert any("checks.yaml is missing" in p for p in res.need.split("\n    "))


def test_lesson_and_eval_fails_on_a_failing_index_check(tmp_path):
    _lesson_setup(tmp_path, write_index=False)
    write(tmp_path / "lessons" / "index.md", "# Lessons\n\nhand-edited, wrong\n")
    res = checks.lesson_and_eval(_e_ctx(tmp_path))
    assert not res.ok
    assert any("lessons/index.md is not what" in p for p in res.need.split("\n    "))


def test_lesson_and_eval_fails_on_a_dangling_supersedes(tmp_path):
    _lesson_setup(tmp_path, lesson_overrides={"supersedes": "2099-01-ghost.md"}, write_index=False)
    res = checks.lesson_and_eval(_e_ctx(tmp_path))
    assert not res.ok
    assert any(
        "supersedes target '2099-01-ghost.md' does not exist" in p for p in res.need.split("\n    ")
    )


def test_lesson_and_eval_fails_on_a_supersedes_path_outside_lessons(tmp_path):
    _lesson_setup(tmp_path, lesson_overrides={"supersedes": "../secret.txt"}, write_index=False)
    res = checks.lesson_and_eval(_e_ctx(tmp_path))
    assert not res.ok
    assert any(
        "supersedes must name a lesson file in lessons/" in p for p in res.need.split("\n    ")
    )


def test_lesson_and_eval_fails_on_an_absolute_supersedes_path(tmp_path):
    target = tmp_path / "lessons" / f"2026-09-earlier-{LESSON_SLUG}.md"
    write_lesson(target, status="retired")
    _lesson_setup(tmp_path, lesson_overrides={"supersedes": str(target)}, write_index=False)
    res = checks.lesson_and_eval(_e_ctx(tmp_path))
    assert not res.ok
    assert any(
        "supersedes must name a lesson file in lessons/" in p for p in res.need.split("\n    ")
    )


def test_lesson_and_eval_fails_on_a_lesson_that_supersedes_itself(tmp_path):
    _lesson_setup(
        tmp_path, lesson_overrides={"supersedes": f"2026-10-{LESSON_SLUG}.md"}, write_index=False
    )
    res = checks.lesson_and_eval(_e_ctx(tmp_path))
    assert not res.ok
    assert any(
        "supersedes must name a lesson file in lessons/" in p for p in res.need.split("\n    ")
    )


def test_lesson_and_eval_fails_when_the_supersedes_target_was_never_retired(tmp_path):
    write_lesson(tmp_path / "lessons" / f"2026-09-earlier-{LESSON_SLUG}.md")  # status: stable
    _lesson_setup(
        tmp_path,
        lesson_overrides={"supersedes": f"2026-09-earlier-{LESSON_SLUG}.md"},
        write_index=False,
    )
    res = checks.lesson_and_eval(_e_ctx(tmp_path))
    assert not res.ok
    assert any(
        f"supersedes target '2026-09-earlier-{LESSON_SLUG}.md' has not been retired" in p
        for p in res.need.split("\n    ")
    )


def test_lesson_and_eval_fails_on_an_out_of_enum_status(tmp_path):
    _lesson_setup(tmp_path, lesson_overrides={"status": "archived"}, write_index=False)
    res = checks.lesson_and_eval(_e_ctx(tmp_path))
    assert not res.ok
    assert any("status 'archived' is not one of" in p for p in res.need.split("\n    "))


def test_lesson_and_eval_renders_every_problem_on_its_own_indented_line(tmp_path):
    """The whole "what I need from you" block, not just substrings: ``gate.GateResult`` is
    what the PR description actually shows the owner."""
    _lesson_setup(tmp_path, write_lesson_file=False, write_index=False, write_eval=False)
    res = checks.lesson_and_eval(_e_ctx(tmp_path))
    assert not res.ok and len(res.need.split("\n    ")) >= 3
    result = gate.GateResult("0001", "x", "e", True, "park", [res], "sdlc:needs-human", "a" * 40)
    block = result.what_i_need()
    bullet = f"- **lesson_and_eval**: {res.reason}"
    problems = res.need.split("\n    ")
    need_lines = [f"  - what I need: {problems[0]}"] + [f"    {p}" for p in problems[1:]]
    assert bullet in block
    for line in need_lines:
        assert line in block.splitlines()


def _set_lock(change: Path, locked: bool, unlocked_by=None, change_type="fix") -> None:
    st = status_mod.read_status(change)
    st.change_type = change_type
    st.tests_locked = locked
    st.tests_unlocked_by = unlocked_by
    status_mod.write_status(change, st)


def test_owner_actions_ties_a_test_lock_lift_to_the_owner(project):
    """0.2.25: the test-file lock is the third owner action (OPERATING_MODEL sections 6
    and 8, "only the owner unlocks"). Until then only the hook read ``tests_locked``, so a
    run that set it to false, turned the change into a feature, or ran ``unlock-tests``
    itself edited the frozen tests unnoticed (1.0.0 readiness review, 2026-09-26)."""
    root, change = project
    _set_lock(change, True)
    commit_all(root, "build: the reproducing test; tests locked")
    verdict(root, "c")
    assert "owner_actions" not in _names(gate.run_gate(root, "0001", "c", dry_run=True), False)
    # lifted in the working tree: nobody's
    _set_lock(change, False)
    result = gate.run_gate(root, "0001", "c", dry_run=True)
    oa = next(ch for ch in result.failed if ch.name == "owner_actions")
    assert "test-file lock was lifted in the working tree" in oa.reason
    assert "unlock-tests" in oa.need and "sdlc:unlock-tests" in oa.need
    # lifted by the automation identity with no actor recorded: parks
    sha = commit_all(root, "unlock the tests", author=BOT_AUTHOR)
    verdict(root, "c")
    result = gate.run_gate(root, "0001", "c", dry_run=True)
    assert result.result == "park" and result.label == "sdlc:needs-human"
    oa = next(ch for ch in result.failed if ch.name == "owner_actions")
    assert f"test-file lock was lifted in commit {sha[:10]}" in oa.reason
    assert "github-actions[bot]" in oa.reason and "no owner label actor" in oa.reason
    # the run turning the fix into a feature lifts the lock the same way
    git(root, "reset", "-q", "--hard", "HEAD~1")
    _set_lock(change, True, change_type="feature")
    commit_all(root, "it is a feature now", author=BOT_AUTHOR)
    verdict(root, "c")
    result = gate.run_gate(root, "0001", "c", dry_run=True)
    assert "owner_actions" in _names(result, False)
    assert (
        "test-file lock was lifted"
        in next(ch for ch in result.failed if ch.name == "owner_actions").reason
    )
    # the owner's sdlc:unlock-tests label, performed by the run and recorded: passes
    git(root, "reset", "-q", "--hard", "HEAD~1")
    _set_lock(change, False, unlocked_by="luissiviero")
    commit_all(root, "apply sdlc:unlock-tests", author=BOT_AUTHOR)
    verdict(root, "c")
    result = gate.run_gate(root, "0001", "c", dry_run=True)
    assert "owner_actions" not in _names(result, False), result.reason
    oa = next(ch for ch in result.checks if ch.name == "owner_actions")
    assert oa.details["label_actors"] == {"tests_unlocked": "luissiviero"}
    # a recorded actor that is a bot is not a person
    git(root, "reset", "-q", "--hard", "HEAD~1")
    _set_lock(change, False, unlocked_by="github-actions[bot]")
    commit_all(root, "apply sdlc:unlock-tests", author=BOT_AUTHOR)
    verdict(root, "c")
    result = gate.run_gate(root, "0001", "c", dry_run=True)
    oa = next(ch for ch in result.failed if ch.name == "owner_actions")
    assert "is not a person" in oa.reason
    # the owner's own commit: counts
    git(root, "reset", "-q", "--hard", "HEAD~1")
    _set_lock(change, False)
    commit_all(root, "owner: the test itself was wrong, unlock")
    verdict(root, "c")
    assert "owner_actions" not in _names(gate.run_gate(root, "0001", "c", dry_run=True), False)


def test_test_lock_refuses_a_test_changed_while_the_lock_stands(project):
    """The hook denies the edit tools and reads the working tree: a run that lifts the lock
    in the file, edits a test and sets it back — or edits through a shell command — leaves
    HEAD locked and the test changed, and ``owner_actions`` sees no lift (the review of the
    0.2.25 diff, M1). The committed diff from the lock commit to HEAD under ``test_paths``
    is the record the hook cannot fake."""
    root, change = project
    _set_lock(change, True)
    lock_sha = commit_all(root, "build: the reproducing test; tests locked")
    verdict(root, "c")
    result = gate.run_gate(root, "0001", "c", dry_run=True)
    tl = next(ch for ch in result.checks if ch.name == "test_lock")
    assert tl.ok and tl.details["lock_commit"] == lock_sha
    # a test edited after the lock, the lock untouched in HEAD: parks
    test_file = root / "tests" / "test_percent.py"
    write(test_file, test_file.read_text(encoding="utf-8") + "\n# weakened\n")
    write(change / "plan.md", (change / "plan.md").read_text(encoding="utf-8") + "\nmore\n")
    commit_all(root, "weaken the test", author=BOT_AUTHOR)
    verdict(root, "c")
    result = gate.run_gate(root, "0001", "c", dry_run=True)
    assert result.result == "park"
    tl = next(ch for ch in result.failed if ch.name == "test_lock")
    assert "tests/test_percent.py" in tl.reason and f"lock commit {lock_sha[:10]}" in tl.reason
    assert "sdlc:unlock-tests" in tl.need
    # the owner's unlock lifts it: owner_actions judges the lift, test_lock stands down
    _set_lock(change, False)
    commit_all(root, "owner: the test was wrong, unlock")
    verdict(root, "c")
    result = gate.run_gate(root, "0001", "c", dry_run=True)
    names = _names(result, False)
    assert "test_lock" not in names and "owner_actions" not in names
    # a feature-type change has no lock
    _set_lock(change, True, change_type="feature")
    commit_all(root, "a feature")
    verdict(root, "c")
    tl = next(
        ch for ch in gate.run_gate(root, "0001", "c", dry_run=True).checks if ch.name == "test_lock"
    )
    assert tl.ok and "not a fix-type" in tl.reason


def test_lock_tests_clears_the_recorded_unlock_actor():
    """A re-lock after the owner's unlock clears ``tests_unlocked_by``, so a second unlock by
    the same person changes the field and ``owner_actions`` credits it (the review of the
    0.2.25 diff, L1)."""
    st = status_mod.Status(id="0001", slug="x", title="x", change_type="fix")
    st.record_owner_label("sdlc:unlock-tests", "luissiviero")
    assert st.tests_locked is False and st.tests_unlocked_by == "luissiviero"
    st.lock_tests()
    assert st.tests_locked is True and st.tests_unlocked_by is None
    st.record_owner_label("sdlc:unlock-tests", "luissiviero")
    assert st.tests_unlocked_by == "luissiviero"


# --- 0.2.26: group A of the 1.0.0 readiness review (docs/reviews/2026-09-26-readiness-review.md) --
def test_a_leftover_profile_override_changes_nothing(project):
    """Decision 37 (1.0.21): no per-change override any more. A ``status.yaml`` an older plugin
    wrote with ``profile_override: full`` and ``review_override: parked``, on the copy the
    owner approved, still loads, and gate (c) is still the confidence gate's alone."""
    root, change = project

    def leftover(r: Path) -> None:
        raw = yamlish.load_file(change / "status.yaml")
        raw.update({"profile_override": "full", "review_override": "parked"})
        yamlish.dump_file(change / "status.yaml", raw)

    on_base(root, leftover, "an older plugin's status.yaml")
    verdict(root, "c")
    result = gate.run_gate(root, "0001", "c", dry_run=True)
    assert result.result == "continue" and result.label is None, result.reason


def test_design_scope_exempts_change_0000_by_its_folder_and_at_gate_a_only(project):
    """The review of the 0.2.26 diff, L2: keyed on ``status.id``, which the session writes, a
    ``0001-x/status.yaml`` saying ``id: '0000'`` skipped the check at every phase."""
    from gate import diff as diffmod

    root, change = project
    write(root / "sample_pkg" / "extra.py", "x = 1\n")
    git(root, "add", "sample_pkg/extra.py")
    git(root, "commit", "-q", "-m", "a source file")
    st = status_mod.read_status(change)
    st.id = "0000"  # the session's forgery; the folder is still 0001's
    d = diffmod.collect(root, None)
    for phase in ("a", "b", "c", "f"):
        ctx = checks.GateContext(root, change, phase, st, {"profile": "standard"}, d, True, "")
        assert not checks.check_design_scope(ctx).ok, phase


def test_owner_actions_judges_every_risk_gaining_commit(project):
    """An older self-acceptance was laundered by the owner's later acceptance of another
    item: the walk kept the newest risk-gaining commit only."""
    root, change = project
    accept_risk(root, change, "auth")
    sha = commit_all(root, "accept the auth risk", author=BOT_AUTHOR)  # the run's own act
    accept_risk(root, change, "payments")
    commit_all(root, "owner: accept the payments risk")  # the owner's, newer
    verdict(root, "c")
    result = gate.run_gate(root, "0001", "c", dry_run=True)
    oa = next(ch for ch in result.failed if ch.name == "owner_actions")
    assert f"risk_accepted gained auth in commit {sha[:10]}" in oa.reason
    assert "payments" not in oa.reason
    # the way out (the review of the 0.2.26 diff, L5): the owner's sdlc:accept-risk after the
    # park records a person for the item in a later commit, which ratifies the old gain
    from state import conventions as c

    _label_act(change, c.ACCEPT_RISK_LABEL, "luissiviero", items=("auth",))
    commit_all(root, "owner labels applied: sdlc:accept-risk", author=BOT_AUTHOR)
    verdict(root, "c")
    result = gate.run_gate(root, "0001", "c", dry_run=True)
    assert "owner_actions" not in _names(result, False), result.reason
    oa = next(ch for ch in result.checks if ch.name == "owner_actions")
    assert oa.details["label_actors"] == {"risk_accepted": {"auth": "luissiviero"}}


def test_owner_actions_judges_every_drop_and_every_lift(project):
    """The review of the 0.2.26 diff, L6: a drop or a lift was judged on its newest commit
    only, the laundering pattern item 7 closed for the risk items."""
    from state import conventions as c

    root, change = project
    st = status_mod.read_status(change)
    st.iterations = 2
    status_mod.write_status(change, st)
    commit_all(root, "build(0001): two fix rounds")
    st = status_mod.read_status(change)
    st.iterations = 0  # the run's own reset, no actor
    status_mod.write_status(change, st)
    sha = commit_all(root, "back to zero", author=BOT_AUTHOR)
    st = status_mod.read_status(change)
    st.iterations = 1
    status_mod.write_status(change, st)
    commit_all(root, "fix(0001): one round")
    _label_act(change, c.RESET_ITERATIONS_LABEL, "luissiviero")  # the owner's, newer
    commit_all(root, "owner labels applied: sdlc:reset-iterations", author=BOT_AUTHOR)
    verdict(root, "c")
    result = gate.run_gate(root, "0001", "c", dry_run=True)
    oa = next(ch for ch in result.failed if ch.name == "owner_actions")
    assert f"iterations dropped from 2 to 0 in commit {sha[:10]}" in oa.reason


def test_owner_actions_judges_a_panel_calls_drop_like_an_iterations_drop(project):
    """OPERATING_MODEL section 6: sdlc:reset-iterations resets "the fix-iteration and
    panel-call counts"; the check judged the iteration count only."""
    from state import conventions as c

    root, change = project
    st = status_mod.read_status(change)
    st.iterations = 2
    st.panel_calls = 3
    status_mod.write_status(change, st)
    commit_all(root, "build(0001): two fix rounds, three panel calls")
    # in the working tree, in no commit
    st = status_mod.read_status(change)
    st.panel_calls = 0
    status_mod.write_status(change, st)
    verdict(root, "c")
    result = gate.run_gate(root, "0001", "c", dry_run=True)
    oa = next(ch for ch in result.failed if ch.name == "owner_actions")
    assert "panel_calls dropped from 3 to 0 in the working tree, in no commit" in oa.reason
    # in the run's own commit with no actor recorded
    sha = commit_all(root, "panel calls back to zero", author=BOT_AUTHOR)
    verdict(root, "c")
    result = gate.run_gate(root, "0001", "c", dry_run=True)
    oa = next(ch for ch in result.failed if ch.name == "owner_actions")
    assert f"panel_calls dropped from 3 to 0 in commit {sha[:10]}" in oa.reason
    assert "no owner label actor is recorded" in oa.reason
    # the owner's label, performed by the run, resets both and is credited for both
    git(root, "reset", "-q", "--hard", "HEAD~1")
    _label_act(change, c.RESET_ITERATIONS_LABEL, "luissiviero")
    commit_all(root, "owner labels applied: sdlc:reset-iterations", author=BOT_AUTHOR)
    st = status_mod.read_status(change)
    assert st.iterations == 0 and st.panel_calls == 0
    verdict(root, "c")
    result = gate.run_gate(root, "0001", "c", dry_run=True)
    assert "owner_actions" not in _names(result, False), result.reason
    oa = next(ch for ch in result.checks if ch.name == "owner_actions")
    assert oa.details["label_actors"] == {
        "iterations_reset": "luissiviero",
        "panel_calls_reset": "luissiviero",
    }


def test_important_findings_strips_the_severity():
    data = {"findings": [{"severity": "Important ", "summary": "x"}, {"severity": " nit"}]}
    assert len(checks.important_findings(data)) == 1


def _intent_branch(tmp_path) -> tuple[Path, Path]:
    """Change 0001 at gate (a): the intent committed on ``sdlc/0001/a`` and nothing else."""
    root, change = _initialised_fixture(tmp_path)
    git(root, "stash", "push", "-q", "-u")  # the intent, not yet committed
    git(root, "checkout", "-q", "-b", "sdlc/0001/a")
    git(root, "stash", "pop", "-q")
    git(root, "add", ".")
    git(root, "commit", "-q", "-m", "intent(0001): percent helper")
    return root, change


def test_gate_a_refuses_a_source_file_on_the_intent_branch(tmp_path):
    """OPERATING_MODEL section 4.2: the fix round at (a) is refused a source file by
    ``design_scope``; gate (a) never ran the check (1.0.0 readiness review, group A)."""
    root, _change = _intent_branch(tmp_path)
    assert checks.check_design_scope in checks.CHECKS_BY_PHASE["a"]
    result = gate.run_gate(root, "0001", "a", dry_run=True)
    assert result.result == "wait", result.reason
    write(root / "sample_pkg" / "percent.py", PERCENT)
    git(root, "add", "sample_pkg/percent.py")
    git(root, "commit", "-q", "-m", "implementation written at the intent stage")
    result = gate.run_gate(root, "0001", "a", dry_run=True)
    assert result.result == "park"
    ds = next(ch for ch in result.failed if ch.name == "design_scope")
    assert ds.details["outside"] == ["sample_pkg/percent.py"]
    assert "phase (a) commits only changes/0001-percent-helper/" in ds.need
    assert "the intent PR carries the intent alone" in ds.need


def test_gate_a_exempts_change_0000_from_design_scope(tmp_path):
    """The installation PR of /sdlc-init carries the guardrails, the workflows and the pin
    script: outside its folder by design (section 8, layer i), as ``guardrails`` knows."""
    root = tmp_path / "proj"
    shutil.copytree(FIXTURE, root)
    git(root, "init", "-q", "-b", "main")
    git(root, "config", "user.email", "owner@example.com")
    git(root, "config", "user.name", "Owner")
    git(root, "add", ".")
    git(root, "commit", "-q", "-m", "fixture")
    git(root, "checkout", "-q", "-b", "sdlc/0000/a")
    proc = run_py(str(INIT), "--root", str(root), "--profile", "standard", cwd=root)
    assert proc.returncode == 0, proc.stderr
    git(root, "add", ".")
    git(root, "commit", "-q", "-m", "sdlc-init")
    result = gate.run_gate(root, "0000", "a", dry_run=True)
    ds = next(ch for ch in result.checks if ch.name == "design_scope")
    assert ds.ok and "change 0000 installs the framework" in ds.reason
    assert "design_scope" not in _names(result, False)
