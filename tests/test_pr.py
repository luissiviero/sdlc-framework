"""Layer-1 tests for plugin/pr: the generated PR description (the five bullets in their
fixed order for phases b, c, d and e, the parked block, the counters and the links), the
`upsert --dry-run` contract the phase commands call, the three routes of the GitHub client
(with `gh` off PATH and `_request` monkeypatched, so nothing leaves the process) and the
daily digest (build guide step 27a, decision 20)."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
from pr import cli as pr_cli
from pr import description as desc
from pr import digest as digest_mod
from pr import github

from gate import artifacts as art
from gate import preflight
from state import conventions as c
from state import status as status_mod
from tests import fixture_repos

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "sample-python-project"
INIT = ROOT / "plugin" / "init" / "sdlc_init.py"
STATE_CLI = ROOT / "plugin" / "state" / "cli.py"
PLUGIN_VERSION = json.loads((ROOT / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))[
    "version"
]
CHANGE_DIR_NAME = "0001-percent-helper"

INTENT = """# Intent: percent helper
Author: owner (developer). Status: accepted. Change id: 0001. Entry route: idea.

## Problem
Callers compute percentages by hand and get rounding wrong. It shows up in invoices.

## Proposed outcome
`sample_pkg.percent(part, whole)` returns a rounded percentage; covered by tests.

## Affected users and systems
sample_pkg users.

## Constraints
No new dependencies.

## Open questions
none
"""

SPEC_HEADER = art.render_spec_header(
    "percent helper", "0001", PLUGIN_VERSION, list(preflight.POLICY_SKILLS), []
)
SPEC_BODY = """
## Requirements
- percent(part, whole) returns part / whole * 100 rounded to one decimal.

## Design
A pure function in sample_pkg/percent.py exported from the package. Nothing else moves.

## Open questions from intent
- Rounding mode: answered, half-up.
- Locale-aware formatting: carried forward to a later change.

## Flagged concerns
- [x] Rounding half-even vs half-up: decided half-up via round() (documented).
- Invoices may depend on the old behaviour; nobody has checked.

## Acceptance
Tests in tests/test_percent.py pass; lint clean.
"""
SPEC = SPEC_HEADER + "\n" + SPEC_BODY

PLAN = """# Plan: percent helper

## Files that change
- `sample_pkg/percent.py` — new: percent(part, whole)

## Order of work
1. Add the function and its test.

## Risks
Rounding; nothing else.

## Options not taken
Decimal module: overkill.

## Proof
tests/test_percent.py::test_percent_rounds
"""


# --- helpers ------------------------------------------------------------------------------
def git(cwd: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=cwd, capture_output=True, text=True, check=True, encoding="utf-8"
    ).stdout


def run_py(*args: str, cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        env=os.environ.copy(),
        encoding="utf-8",
    )


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def bullets(body: str) -> list[str]:
    """The leading bullet block of the body: every line until the first non-bullet line."""
    out = []
    for line in body.splitlines():
        if line.startswith("- "):
            out.append(line)
        elif out:
            break
    return out


def gate_json(
    change_dir: Path,
    phase: str,
    result: str,
    label: str | None,
    plan_sync_ok: bool = True,
    with_block: bool = True,
) -> dict:
    """``evidence/gate-<phase>.json`` in the shape ``GateResult.as_dict()`` writes."""
    checks = [
        {
            "name": "artifacts",
            "ok": True,
            "reason": "every artifact matches",
            "need": "",
            "details": {},
        },
        {
            "name": "plan_sync",
            "ok": plan_sync_ok,
            "reason": (
                "every changed source file is in plan.md"
                if plan_sync_ok
                else "2 changed file(s) not listed in plan.md"
            ),
            "need": (
                ""
                if plan_sync_ok
                else "Update '## Files that change' in plan.md to match the diff."
            ),
            "details": {},
        },
    ]
    if result == "park":
        checks.append(
            {
                "name": "risk_list",
                "ok": False,
                "reason": "the diff touches the risk-list item 'auth'",
                "need": "Accept the risk with state/cli.py accept-risk, or split the change.",
                "details": {},
            }
        )
    data = {
        "schema_version": 1,
        "change_id": "0001",
        "slug": "percent-helper",
        "phase": phase,
        "profile": "standard",
        "human_gate": result == "wait",
        "result": result,
        "label": label,
        "head": "0123456789abcdef0123456789abcdef01234567",
        "at": "2026-09-21T10:00:00Z",
        "dry_run": False,
        "reason": "; ".join(f"{ch['name']}: {ch['reason']}" for ch in checks if not ch["ok"]),
        "config_note": "",
        "checks": checks,
    }
    if with_block:
        failed = [ch for ch in checks if not ch["ok"]]
        lines = [
            "## What I need from you",
            f"Gate ({phase}) parked change 0001 (percent-helper) on 2026-09-21T10:00:00Z.",
        ]
        for ch in failed:
            lines.append(f"- **{ch['name']}**: {ch['reason']}")
            if ch["need"]:
                lines.append(f"  - what I need: {ch['need']}")
        data["what_i_need"] = "\n".join(lines) + "\n" if result == "park" else ""
    write(
        change_dir / art.EVIDENCE_DIR / art.GATE_RESULT.format(phase=phase),
        json.dumps(data, indent=2),
    )
    return data


def logs(change_dir: Path, exit_code: int | None = 0) -> None:
    """The three command logs with the header plugin/evidence/collect.py writes."""
    for name, command in (
        (art.EVIDENCE_TEST, "python -m pytest"),
        (art.EVIDENCE_BUILD, "python -m build"),
        (art.EVIDENCE_LINT, "ruff check ."),
    ):
        header = art.render_evidence_header(command, exit_code, 1.2, "2026-09-21T10:00:00Z")
        write(change_dir / art.EVIDENCE_DIR / name, header + "\nall good\n")


def findings(change_dir: Path, important: int = 0, nits: int = 0) -> None:
    items = [
        {"pass": "bugs", "severity": "important", "file": "a.py", "line": i, "summary": f"bug {i}"}
        for i in range(important)
    ]
    items += [
        {"pass": "bugs", "severity": "nit", "file": "a.py", "line": i, "summary": f"nit {i}"}
        for i in range(nits)
    ]
    write(
        change_dir / art.EVIDENCE_DIR / art.REVIEW_FINDINGS,
        json.dumps(
            {
                "schema_version": 1,
                "head": "0123456789abcdef",
                "findings": items,
                "tally": {"important": important, "nit": nits},
            }
        ),
    )


@pytest.fixture
def project(tmp_path):
    """A fixture copy, initialised, with change 0001 and its three artifacts written by hand."""
    fixture_repos.copy("pr-project", tmp_path, _build_project)
    root = tmp_path / "proj"
    return root, root / "changes" / CHANGE_DIR_NAME


def _build_project(base: Path) -> None:
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
    git(root, "commit", "-q", "-m", "sdlc-init")
    proc = run_py(
        str(STATE_CLI), "new-change", "--root", str(root), "--title", "Percent helper", cwd=root
    )
    assert proc.returncode == 0, proc.stderr
    change = root / "changes" / CHANGE_DIR_NAME
    write(change / "intent.md", INTENT)
    write(change / "spec.md", SPEC)
    write(change / "plan.md", PLAN)
    git(root, "add", ".")
    git(root, "commit", "-q", "-m", "intent, spec and plan")


# --- the five bullets ----------------------------------------------------------------------
def test_five_bullets_at_phase_a_describe_the_intent(project):
    root, change = project
    write(
        change / "intent.md",
        INTENT.replace("## Open questions\nnone", "## Open questions\n- Which rounding mode?\n"),
    )
    body = desc.build_description(root, "0001", "intent")  # no gate file exists at (a)
    lines = bullets(body)
    assert len(lines) == 5
    heads = [line.split("**")[1] for line in lines]
    assert heads == [
        "What changed and why",
        "Entry route",
        "Affected users and systems",
        "Open questions",
        "What needs you",
    ]
    assert lines[0] == (
        "- **What changed and why**: Percent helper: Callers compute percentages by hand "
        "and get rounding wrong."
    )
    assert lines[1].endswith("idea route, feature change")
    assert lines[2].endswith("sample_pkg users.")
    assert lines[3].endswith("1 open: Which rounding mode?")
    assert lines[4].endswith("read, correct via review comments, merge = approve (gate (intent))")
    # phase (a) links only the artifact that exists, and carries the counters
    assert f"Links: changes/{CHANGE_DIR_NAME}/intent.md" in body
    assert "spec.md" not in body and "gate-intent.json" not in body
    assert "Counters: no fix round so far · fix iterations: 0" in body


def test_intent_pr_names_the_fast_lane_unless_opened_as_a_draft(project):
    """Choice 239 (R54): the sample's #77 read "merge = approve (gate (intent))" while its opening
    had already accepted the intent and started the design (NOTES §50). A PR not opened as a
    draft names both cases; a draft, which never takes the fast lane, keeps gate (intent) alone."""
    root, _change = project
    needs = bullets(desc.build_description(root, "0001", "intent"))[4]
    assert (
        "opened from your own account, not as a draft, and changing nothing outside its change "
        "folder, nothing"
    ) in needs
    assert "the fast lane, decision 30" in needs and "`sdlc:superseded`" in needs
    assert needs.endswith("or changing other files: " + desc.GATE_CHECKLIST["intent"])
    draft = bullets(desc.build_description(root, "0001", "intent", draft=True))[4]
    assert draft == "- **What needs you**: " + desc.GATE_CHECKLIST["intent"]


def test_upsert_passes_the_draft_flag_to_the_description(project, capsys):
    root, _change = project
    for flags, fast in (([], True), (["--draft"], False)):
        argv = ["upsert", "--root", str(root), "--id", "0001", "--phase", "intent", "--dry-run"]
        assert pr_cli.main(argv + flags) == 0
        body = json.loads(capsys.readouterr().out)["body"]
        assert ("the fast lane, decision 30" in body) is fast


def test_the_install_pr_of_change_0000_keeps_gate_a(project):
    """The review of 5248e29: /sdlc-init opens change 0000's PR without --draft, and it changes
    files outside its folder, so the fast lane never takes it (run_phase.intent_pr_start)."""
    root, change = project
    st = status_mod.read_status(change)
    needs = desc._intent_bullets(INTENT, status_mod.Status(**{**st.__dict__, "id": "0000"}))[4]
    assert needs == "- **What needs you**: " + desc.GATE_CHECKLIST["intent"]


def test_upsert_on_an_open_pr_reads_its_live_draft_state(project, capsys, monkeypatch):
    """A fix round's upsert passes no --draft: the body follows the PR's own draft flag."""
    root, _change = project
    git(root, "remote", "add", "origin", "https://github.com/o/r.git")
    bodies: list[str] = []
    for live_draft, fast in ((True, False), (False, True)):
        found = {"ok": True, "number": 7, "labels": [], "draft": live_draft, "route": "api"}
        monkeypatch.setattr(github, "find_open_pr", lambda *a, _f=found, **k: _f)
        monkeypatch.setattr(
            github,
            "update_pr",
            lambda repo, number, body, title, cwd=None: (
                bodies.append(body) or {"ok": True, "route": "api", "number": number}
            ),
        )
        monkeypatch.setattr(github, "ensure_label", lambda *a, **k: {"ok": True})
        monkeypatch.setattr(github, "set_labels", lambda *a, **k: {"ok": True})
        monkeypatch.setattr(pr_cli, "not_build_check", lambda *a, **k: {"ok": True})
        assert (
            pr_cli.main(["upsert", "--root", str(root), "--id", "0001", "--phase", "intent"]) == 0
        )
        capsys.readouterr()
        assert ("the fast lane, decision 30" in bodies[-1]) is fast


def test_upsert_keeps_the_triage_queue_s_labels_and_moves_an_older_incident_label(
    project, capsys, monkeypatch
):
    """R45 (rows 37 and 38): `sdlc:triage` and `sdlc:schedule` carry the gate labels' prefix,
    so the gate-label sweep keeps them (`OWNER_LABELS`); an upsert at maintain labels the PR
    `sdlc:triage` and takes off the `incident` an older plugin applied."""
    root, _change = project
    git(root, "remote", "add", "origin", "https://github.com/o/r.git")
    calls: list[tuple] = []
    for phase, labels in (
        ("intent", ["sdlc:schedule", "sdlc:triage", "sdlc:needs-human"]),
        ("maintain", ["incident", "sdlc:schedule"]),
    ):
        found = {"ok": True, "number": 7, "labels": labels, "draft": False, "route": "api"}
        monkeypatch.setattr(github, "find_open_pr", lambda *a, _f=found, **k: _f)
        monkeypatch.setattr(
            github, "update_pr", lambda *a, **k: {"ok": True, "route": "api", "number": 7}
        )
        monkeypatch.setattr(github, "ensure_label", lambda *a, **k: {"ok": True})
        monkeypatch.setattr(
            github, "set_labels", lambda repo, n, add, remove, **k: calls.append((add, remove))
        )
        monkeypatch.setattr(pr_cli, "not_build_check", lambda *a, **k: {"ok": True})
        argv = ["upsert", "--root", str(root), "--id", "0001", "--phase", phase]
        assert pr_cli.main(argv) == 0
        capsys.readouterr()
    (add_a, remove_a), (add_f, remove_f) = calls
    assert "sdlc:needs-human" in remove_a
    assert "sdlc:schedule" not in remove_a and "sdlc:triage" not in remove_a
    assert "sdlc:triage" in add_f and "incident" in remove_f
    assert "sdlc:schedule" not in remove_f


QUICK_INTENT = """# Intent: percent helper
Author: owner (developer). Status: proposed. Change id: 0001. Entry route: idea.
Quick intent: yes

## Problem
Callers compute percentages by hand and get rounding wrong. Give them a helper.

## Proposed outcome
Left to the design run (quick intent).

## Affected users and systems
Left to the design run (quick intent).

## Constraints
Left to the design run (quick intent).

## Open questions
Left to the design run (quick intent).

## Examples/References
none
"""
ASSUMED = """
## Assumed from the quick intent
- Proposed outcome: `sample_pkg.percent(part, whole)` returns a rounded
  percentage.
- Change type: feature.
"""


def test_quick_intent_at_a_says_what_is_left_to_the_design(project):
    root, change = project
    write(change / "intent.md", QUICK_INTENT)
    lines = bullets(desc.build_description(root, "0001", "intent"))
    assert len(lines) == 5
    assert lines[0].endswith("Callers compute percentages by hand and get rounding wrong.")
    assert lines[1].endswith("idea route, feature change, quick intent")
    for line in lines[2:4]:
        assert "left to the design run (quick intent)" in line
        assert "Left to the design run" not in line  # never quoted as an open question


def test_what_i_assumed_heads_the_design_and_build_prs(project):
    root, change = project
    write(change / "intent.md", QUICK_INTENT)
    write(change / "spec.md", SPEC_HEADER + ASSUMED + SPEC_BODY)
    gate_json(change, "design", "wait", c.ready_label("design"))
    gate_json(change, "deploy", "wait", c.ready_label("deploy"))
    for phase in ("design", "deploy"):
        body = desc.build_description(root, "0001", phase)
        assert len(bullets(body)) == 5
        assert body.startswith("**What I assumed (2)** from your one-paragraph intent (R54)")
        # choice 263: a fix round edits the spec at (b) only; from (c) on it changes the code
        head = body.splitlines()[0]
        assert ("corrects it (/sdlc-fix)" in head) is (phase == "design")
        assert ("the line itself stays as the design wrote it" in head) is (phase == "deploy")
        assert (
            "1. Proposed outcome: `sample_pkg.percent(part, whole)` returns a rounded "
            "percentage.\n2. Change type: feature.\n"
        ) in body
    # the marker is not a release note: with no notes file, the section is left out
    assert "## Release note" not in desc.build_description(root, "0001", "deploy")
    write(change / "intent.md", INTENT)
    write(change / "spec.md", SPEC)
    assert "What I assumed" not in desc.build_description(root, "0001", "design")


def test_phase_a_open_questions_none_and_default_label(project):
    root, change = project
    assert bullets(desc.build_description(root, "0001", "intent"))[3].endswith("none")
    st = status_mod.read_status(change)
    assert desc.pr_title(st, "intent") == "intent(0001): Percent helper"
    assert desc.head_branch("0001", "intent") == "sdlc/0001/intent"
    assert desc.label_for(None, "intent") == "sdlc:intent-ready"  # no gate file at (a)
    assert desc.label_for(None, "build") is None


def test_five_bullets_in_order_at_phase_b(project):
    root, change = project
    gate_json(change, "design", "wait", c.ready_label("design"))
    body = desc.build_description(root, "0001", "design")
    lines = bullets(body)
    assert len(lines) == 5
    heads = [line.split("**")[1] for line in lines]
    assert heads == [
        "What changed and why",
        "Evidence",
        "Review findings",
        "Plan conformance",
        "What needs you",
    ]
    assert "Percent helper (feature, idea route)" in lines[0]
    assert "Callers compute percentages by hand and get rounding wrong." in lines[0]
    assert "Design: A pure function in sample_pkg/percent.py exported from the package." in lines[0]
    assert lines[1].endswith("design phase, no code yet")
    # phase (b): the flagged concerns, with the open one quoted verbatim
    assert "1 open / 1 closed" in lines[2]
    assert "Invoices may depend on the old behaviour; nobody has checked." in lines[2]
    assert "open questions from intent: 1 answered / 1 carried forward" in lines[3]
    # the four questions of build guide step 23
    assert "Does the spec solve the problem the intent states?" in lines[4]
    assert "Merge = approve; a review comment = change request (/sdlc-fix)." in lines[4]


def test_phase_c_evidence_missing_and_not_yet_reviewed(project):
    root, change = project
    gate_json(change, "build", "continue", None)
    body = desc.build_description(root, "0001", "build")
    lines = bullets(body)
    assert len(lines) == 5
    assert "test missing, build missing, lint missing" in lines[1]
    assert "verifier.md missing" in lines[1] and "0 screenshot(s)" in lines[1]
    assert lines[2].endswith("not yet reviewed")
    assert "diff matches plan.md" in lines[3]
    assert "nothing: the run continues to the next phase" in lines[4]


def test_phase_d_green_logs_and_nothing_to_do_at_d(project):
    root, change = project
    logs(change, exit_code=0)
    write(change / art.EVIDENCE_DIR / art.EVIDENCE_VERIFIER, "# Verifier\nRan it.\n")
    write(change / art.EVIDENCE_DIR / desc.SCREENSHOT_DIR / "home.png", "png")
    findings(change, important=0, nits=2)
    gate_json(change, "test", "continue", None)
    lines = bullets(desc.build_description(root, "0001", "test"))
    assert "test green, build green, lint green" in lines[1]
    assert "verifier.md present" in lines[1] and "1 screenshot(s)" in lines[1]
    assert "0 Important, 2 nits (nit 0; nit 1)" in lines[2]
    # decision 37 (1.0.21): gate (test) is the confidence gate's; no approval label is asked for
    assert desc.NOTHING_NEEDED in lines[4] and "approved" not in lines[4]


def test_red_log_is_red(project):
    root, change = project
    logs(change, exit_code=1)
    gate_json(change, "test", "park", c.NEEDS_HUMAN_LABEL)
    lines = bullets(desc.build_description(root, "0001", "test"))
    assert "test red, build red, lint red" in lines[1]


# --- change 0004: the drive's proof in the evidence line ------------------------------------
def _with_drive(root: Path) -> None:
    text = (root / "sdlc.yaml").read_text(encoding="utf-8")
    write(root / "sdlc.yaml", text.replace('  drive: ""\n', '  drive: "npx x"\n', 1))
    git(root, "add", "sdlc.yaml")
    git(root, "commit", "-q", "-m", "owner: commands.drive")


def _proof_record(change: Path, details: dict) -> None:
    record = gate_json(change, "test", "continue", None)
    record["checks"].append(
        {"name": "proof", "ok": True, "reason": "x", "need": "", "details": details}
    )
    write(change / art.EVIDENCE_DIR / "gate-test.json", json.dumps(record))


def _manifest(change: Path, commit: str) -> None:
    files = [{"path": "home.png", "bytes": 10}, {"path": "status.json", "bytes": 20}]
    write(
        change / art.EVIDENCE_DIR / "proof" / "manifest.json",
        json.dumps({"schema_version": 1, "commit": commit, "files": files, "dropped": []}),
    )


STATE_ITEMS = [
    {"item": "a", "kind": "state", "approved": True, "outcome": "matches"},
    {"item": "b", "kind": "state", "approved": True, "outcome": "differs"},
    {"item": "c", "kind": "screenshot", "approved": True, "outcome": "matches"},
    {"item": "d", "kind": "state", "approved": False, "outcome": "matches"},
]


def test_the_evidence_line_shows_the_drive_and_its_proof(project):
    root, change = project
    _with_drive(root)
    logs(change, exit_code=0)
    write(change / art.EVIDENCE_DIR / desc.SCREENSHOT_DIR / ".gitkeep", "")
    head = git(root, "rev-parse", "HEAD").strip()
    _manifest(change, head)
    _proof_record(change, {"items": STATE_ITEMS})
    status = desc.evidence_status(change, "test", root)
    assert "test green, build green, lint green, drive missing" in status
    assert "proof 2, state items 1 of 2 matching" in status
    assert "0 screenshot(s)" in status  # the .gitkeep is not a screenshot
    assert "not the final head" not in status
    # the runner's record commit moves the change folder only: still the final head
    git(root, "add", ".")
    git(root, "commit", "-q", "-m", "run(c): gate record")
    assert "not the final head" not in desc.evidence_status(change, "test", root)
    # a source file changed after the manifest: the proof is of an older tree
    write(root / "sample_pkg" / "later.py", "x = 1\n")
    git(root, "add", ".")
    git(root, "commit", "-q", "-m", "a later source commit")
    assert f"proof of {head[:7]}, not the final head" in desc.evidence_status(change, "test", root)
    # the check run's summary carries the same line
    summary = pr_cli.check_run_result(root, change, "test")["summary"]
    assert "drive missing" in summary and "proof 2, state items 1 of 2 matching" in summary
    # by hand: not checked; and the bullet passes the root
    _proof_record(change, {"checked": False})
    assert "proof not checked" in desc.evidence_status(change, "test", root)
    lines = bullets(desc.build_description(root, "0001", "test"))
    assert "drive missing" in lines[1] and "proof not checked" in lines[1]


def test_no_drive_keeps_the_evidence_line_of_today(project):
    root, change = project
    logs(change, exit_code=0)
    _proof_record(change, {})
    status = desc.evidence_status(change, "test", root)
    assert "drive" not in status and "proof" not in status
    assert status.startswith("test green, build green, lint green, verifier.md missing")


def test_a_proof_round_reads_its_item_count():
    auto = {"round": 1, "cap": 2, "targets": [{"target": "proof", "items": [{}, {}]}]}
    assert "a red target (proof (2 items))" in desc._auto_round_line(auto)
    auto["targets"] = [{"target": "test", "exit_code": 1}, {"target": "proof", "items": [{}]}]
    assert "(test (exit 1), proof (1 item))" in desc._auto_round_line(auto)


def test_phase_e_release_note_and_counters(project):
    root, change = project
    logs(change)
    write(change / art.EVIDENCE_DIR / art.EVIDENCE_VERIFIER, "# Verifier\n")
    findings(change, important=0, nits=1)
    gate_json(change, "deploy", "wait", c.ready_label("deploy"))
    body = desc.build_description(root, "0001", "deploy")
    assert len(bullets(body)) == 5
    assert "an approving review = approve (gate (deploy), decision 36)" in body
    assert "## Release note" in body
    assert "returns a rounded percentage" in body.split("## Release note")[1]
    assert "Counters: no fix round so far · fix iterations: 0" in body
    # relative repository paths when the fixture has no GitHub remote
    assert f"changes/{CHANGE_DIR_NAME}/intent.md" in body
    assert f"changes/{CHANGE_DIR_NAME}/evidence/gate-deploy.json" in body
    # waiting for the owner's approval; the merge App merges, then the release workflow runs
    # (build guide step 32; decision 36)
    assert "Waiting for your approval: the merge App then merges this PR" in body
    assert "the release workflow runs `deploy.command`" in body
    # the fixture declares no production: merge is the whole gate (decision 13)
    assert "Release approval" not in body and "sdlc:release-approved" not in body


RELEASE_NOTES = """# Release notes — change 0001: Percent helper

## What changed

- `sample_pkg.percent(part, whole)` added.

## Evidence

test green, build green, lint green
"""


def test_phase_e_release_note_quotes_the_release_notes_file(project):
    """32.2: at (e) the "## Release note" section is evidence/release-notes.md verbatim,
    without its H1 title; the intent's proposed outcome is only the fallback."""
    root, change = project
    logs(change)
    gate_json(change, "deploy", "wait", c.ready_label("deploy"))
    write(change / art.EVIDENCE_DIR / desc.RELEASE_NOTES, RELEASE_NOTES)
    body = desc.build_description(root, "0001", "deploy")
    assert len(bullets(body)) == 5
    note = body.split("## Release note\n")[1]
    assert note.startswith("\n### What changed\n\n- `sample_pkg.percent(part, whole)` added.\n")
    assert "### Evidence\n\ntest green, build green, lint green" in note
    # the file's headings are demoted one level so they nest under "## Release note"
    assert "\n## What changed" not in body and "\n## Evidence" not in body
    assert "# Release notes — change 0001" not in body
    assert "returns a rounded percentage" not in note  # the fallback is not used


def test_phase_e_release_note_falls_back_to_the_intent_outcome(project):
    root, change = project
    gate_json(change, "deploy", "wait", c.ready_label("deploy"))
    write(change / art.EVIDENCE_DIR / desc.RELEASE_NOTES, "# Release notes — change 0001\n\n")
    body = desc.build_description(root, "0001", "deploy")
    assert "returns a rounded percentage" in body.split("## Release note")[1]


def test_phase_f_proposed_outcome_keeps_a_sentence_wrapped_over_lines(project):
    # item 11's read: the sample's PR #60 showed "... the commit that caused the breach was
    # already" because only the first line of a hard-wrapped paragraph was read
    root, change = project
    st = status_mod.read_status(change)
    st.entry_route, st.change_type = "incident", "fix"
    st.set_phase("maintain")
    status_mod.write_status(change, st)
    outcome = (
        "No design-phase code change is required: the commit that caused the breach was already\n"
        "reverted on `main`, before this diagnosis ran (see Evidence).\n"
        "`main` is green.\n"
    )
    write(
        change / "intent.md",
        INTENT.replace("Entry route: idea", "Entry route: incident abc").replace(
            "`sample_pkg.percent(part, whole)` returns a rounded percentage; covered by tests.\n",
            outcome,
        ),
    )
    lines = bullets(desc.build_description(root, "0001", "maintain"))
    assert lines[1] == (
        "- **Proposed outcome**: Percent helper: No design-phase code change is required: the "
        "commit that caused the breach was already reverted on `main`, before this diagnosis "
        "ran (see Evidence)."
    )


@pytest.mark.parametrize(
    "body, sentence",
    [
        ("One line. Two.\n", "One line."),
        ("Wrapped over\ntwo lines. Then more.\n", "Wrapped over two lines."),
        ("No end mark\non two lines\n\nNext paragraph.\n", "No end mark on two lines"),
        ("- An item\n  that wraps. Rest.\n- Another item.\n", "An item that wraps."),
        ("- An item with no end mark\n- Another item.\n", "An item with no end mark"),
        ("Stops at a list\n- item.\n", "Stops at a list"),
        ("> a quote\n\nThe text\nafter it.\n", "The text after it."),
        ("A signature:\n```python\ndef f(x):\n    return x\n```\n", "A signature:"),
        ("```\ncode line\n```\nThe text\nafter it.\n", "The text after it."),
    ],
)
@pytest.mark.parametrize("helper", ["pr", "release"])
def test_first_sentence_reads_the_whole_first_paragraph(helper, body, sentence):
    # the PR body's helper and the release note's copy read a section the same way
    from release import notes

    first_sentence = desc._first_sentence if helper == "pr" else notes._first_sentence
    assert first_sentence(body) == sentence


def _declare_production(root: Path, value: str, key: str = "production_gate") -> None:
    """The one ``deploy.production_gate:`` (or old ``production:``) line set to ``key: value``."""
    config = root / "sdlc.yaml"
    text = config.read_text(encoding="utf-8")
    keys = ("production_gate:", "production:")
    lines = [
        f"  {key}: {value}" if line.strip().startswith(keys) else line for line in text.splitlines()
    ]
    assert sum(line.strip().startswith(keys) for line in text.splitlines()) == 1
    write(config, "\n".join(lines) + "\n")


def test_release_approval_line_only_when_production_is_declared(project):
    """Decision 13: with `deploy.production_gate: true` the release label is the second act; the
    line sits below the five bullets (not a sixth bullet) and only at phase (e)."""
    root, change = project
    logs(change)
    gate_json(change, "deploy", "wait", c.ready_label("deploy"))
    gate_json(change, "test", "continue", None)
    _declare_production(root, "true")
    body = desc.build_description(root, "0001", "deploy")
    assert len(bullets(body)) == 5
    line = (
        "Release approval: apply `sdlc:release-approved` on this PR with your approval; the "
        "release workflow waits for it after the merge."
    )
    assert line in body.splitlines()
    assert "signed tag" not in body  # decision 5: the label is the only route
    assert body.index(line) > body.index(bullets(body)[-1]) and body.index(line) < body.index(
        "Links:"
    )
    assert line not in desc.build_description(root, "0001", "test")
    _declare_production(root, "false")
    assert line not in desc.build_description(root, "0001", "deploy")
    # R45 (decision 39, row 55): the old key `deploy.production` is read for one release
    _declare_production(root, "true", key="production")
    assert "  production: true" in (root / "sdlc.yaml").read_text(encoding="utf-8")
    assert line in desc.build_description(root, "0001", "deploy").splitlines()
    _declare_production(root, "false", key="production")
    assert line not in desc.build_description(root, "0001", "deploy")


def test_counters_after_a_fix_round(project):
    root, change = project
    st = status_mod.read_status(change)
    st.iterations = 3
    status_mod.write_status(change, st)
    gate_json(change, "build", "continue", None)
    body = desc.build_description(root, "0001", "build")
    assert "Counters: first-pass: no · fix iterations: 3" in body


def test_claude_md_proposals_block(project):
    root, change = project
    gate_json(change, "deploy", "wait", c.ready_label("deploy"))
    write(
        change / art.EVIDENCE_DIR / desc.CLAUDE_MD_PROPOSALS,
        "- Always pass encoding='utf-8' to open().\n",
    )
    body = desc.build_description(root, "0001", "deploy")
    assert "## Proposed CLAUDE.md lines" in body
    assert "> - Always pass encoding='utf-8' to open()." in body


# --- parked --------------------------------------------------------------------------------
def test_parked_body_carries_what_i_need_from_you(project):
    root, change = project
    data = gate_json(change, "build", "park", c.NEEDS_HUMAN_LABEL)
    body = desc.build_description(root, "0001", "build")
    lines = bullets(body)
    assert len(lines) == 5
    assert lines[4].endswith('parked at gate (build) - see "What I need from you" below')
    assert data["what_i_need"].strip() in body
    assert "the diff touches the risk-list item 'auth'" in body
    assert "what I need: Accept the risk with state/cli.py accept-risk" in body


def test_parked_block_rebuilt_when_the_json_does_not_carry_it(project):
    root, change = project
    gate_json(change, "build", "park", c.NEEDS_HUMAN_LABEL, with_block=False)
    body = desc.build_description(root, "0001", "build")
    assert "## What I need from you" in body
    assert "Gate (build) parked change 0001 (percent-helper)" in body
    assert "- **risk_list**: the diff touches the risk-list item 'auth'" in body
    assert "re-run the gate" in body


def test_plan_conformance_reports_the_failed_check(project):
    root, change = project
    gate_json(change, "build", "park", c.NEEDS_HUMAN_LABEL, plan_sync_ok=False)
    lines = bullets(desc.build_description(root, "0001", "build"))
    assert "2 changed file(s) not listed in plan.md" in lines[3]


def test_conformance_line_declared_drops_clause_present():
    gate_json_data = {
        "checks": [
            {
                "name": "plan_sync",
                "ok": True,
                "reason": "every committed source file is in plan.md",
            },
            {"name": "ratchets", "ok": True, "details": {"declared": ["tests/x.py (plan)"]}},
        ]
    }
    line = desc._conformance_line(gate_json_data, "", "build")
    assert line == "diff matches plan.md; declared drops: tests/x.py (plan)"


def test_conformance_line_declared_drops_clause_absent():
    gate_json_data = {
        "checks": [
            {
                "name": "plan_sync",
                "ok": True,
                "reason": "every committed source file is in plan.md",
            },
            {"name": "ratchets", "ok": True, "details": {"declared": []}},
        ]
    }
    assert desc._conformance_line(gate_json_data, "", "build") == "diff matches plan.md"
    # unchanged at (a)/(b): no `ratchets` check runs there
    assert desc._conformance_line(None, "", "design").startswith("open questions from intent")


def test_no_gate_file_means_nothing_needed(project):
    root, _change = project
    lines = bullets(desc.build_description(root, "0001", "build"))
    assert "nothing: the run continues to the next phase" in lines[4]


# --- titles, labels, branches -----------------------------------------------------------------
def test_pr_title_and_label_and_branch(project):
    _root, change = project
    st = status_mod.read_status(change)
    assert desc.pr_title(st, "design") == "design(0001): Percent helper"
    for phase in ("build", "test", "deploy"):
        assert desc.pr_title(st, phase) == "build(0001): Percent helper"
    assert desc.head_branch("0001", "design") == "sdlc/0001/design"
    assert all(
        desc.head_branch("0001", p) == "sdlc/0001/build" for p in ("build", "test", "deploy")
    )
    assert desc.label_for({"label": "sdlc:deploy-ready"}) == "sdlc:deploy-ready"
    assert desc.label_for({"label": None}) is None
    assert desc.label_for(None) is None


def test_a_change_in_flight_keeps_its_letter_branch_gate_file_and_phase(project, capsys):
    """R45, for one release: ``--phase c`` is read as build, the gate record an older plugin
    wrote (``gate-c.json``) is read and linked, and the build PR's head is the letter branch
    ``sdlc/0001/c`` while only that one exists."""
    root, change = project
    gate_json(change, "build", "park", c.NEEDS_HUMAN_LABEL)
    evidence = change / art.EVIDENCE_DIR
    (evidence / "gate-build.json").rename(evidence / "gate-c.json")
    assert desc.load_gate(change, "c")["result"] == "park"
    assert desc.load_gate(change, "build")["result"] == "park"
    assert desc.head_branch("0001", "deploy", root) == "sdlc/0001/build"
    git(root, "branch", "sdlc/0001/c")
    assert desc.head_branch("0001", "deploy", root) == "sdlc/0001/c"
    body = desc.build_description(root, "0001", "c")
    assert "evidence/gate-c.json" in body and "parked at gate (build)" in body
    assert pr_cli.main(["upsert", "--root", str(root), "--id", "0001", "--phase", "c",
                        "--dry-run"]) == 0  # fmt: skip
    out = json.loads(capsys.readouterr().out)
    assert out["head"] == "sdlc/0001/c" and out["title"] == "build(0001): Percent helper"


# --- the CLI ------------------------------------------------------------------------------
def test_upsert_dry_run_contacts_nothing(project, capsys, monkeypatch):
    root, change = project
    gate_json(change, "build", "park", c.NEEDS_HUMAN_LABEL)

    def boom(*_args, **_kwargs):  # any HTTP call in a dry run is a bug
        raise AssertionError("--dry-run must contact nothing")

    monkeypatch.setattr(github, "_request", boom)
    monkeypatch.setattr(github.shutil, "which", lambda *_a, **_k: None)
    code = pr_cli.main(
        ["upsert", "--root", str(root), "--id", "0001", "--phase", "build", "--draft", "--dry-run"]
    )
    assert code == 0
    out = json.loads(capsys.readouterr().out)
    assert out["route"] == "dry-run"
    assert out["head"] == "sdlc/0001/build" and out["base"] == "main"
    assert out["label"] == c.NEEDS_HUMAN_LABEL
    assert out["title"] == "build(0001): Percent helper"
    assert out["created"] is False and out["number"] is None
    assert "## What I need from you" in out["body"]


def test_description_subcommand_prints_the_body_only(project, capsys):
    root, change = project
    gate_json(change, "design", "wait", c.ready_label("design"))
    assert (
        pr_cli.main(["description", "--root", str(root), "--id", "0001", "--phase", "design"]) == 0
    )
    out = capsys.readouterr().out
    assert out.startswith("- **What changed and why**:")
    assert len(bullets(out)) == 5


def test_cli_unknown_change_exits_2(project, capsys):
    root, _change = project
    assert (
        pr_cli.main(["description", "--root", str(root), "--id", "0099", "--phase", "build"]) == 2
    )
    assert "no change folder" in capsys.readouterr().err


def test_check_run_without_remote_reports_route_none(project, capsys):
    root, change = project
    gate_json(change, "test", "park", c.NEEDS_HUMAN_LABEL)
    logs(change, exit_code=1)
    assert pr_cli.main(["check-run", "--root", str(root), "--id", "0001", "--phase", "test"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["route"] == "none" and out["conclusion"] == "failure"
    assert out["name"] == "sdlc/test" and "test red" in out["summary"]


def test_upsert_records_the_build_pr_in_status_yaml(project, capsys, recorder):
    """The readiness review's group B (0.2.27): the release approval reads the change's own
    build PR by the number ``status.yaml`` records; ``upsert`` writes it when the PR of the
    work branch ``sdlc/<id>/build`` is opened or found, and leaves the other phases' PRs alone."""
    root, change = project
    calls, answers = recorder
    gate_json(change, "design", "pass", c.ready_label("design"))
    gate_json(change, "build", "park", c.NEEDS_HUMAN_LABEL)
    answers[("GET", "/pulls?")] = {"status": 200, "data": [], "error": ""}
    answers[("POST", "/repos/o/r/pulls")] = {
        "status": 201,
        "data": {"number": 41, "html_url": "https://github.com/o/r/pull/41", "node_id": "PR_41"},
        "error": "",
    }
    git(root, "remote", "add", "origin", "https://github.com/o/r.git")
    assert pr_cli.main(["upsert", "--root", str(root), "--id", "0001", "--phase", "design"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["number"] == 41 and "build_pr_recorded" not in out
    assert status_mod.read_status(change).build_pr is None  # the spec PR is not the build PR
    assert (
        pr_cli.main(["upsert", "--root", str(root), "--id", "0001", "--phase", "build", "--draft"])
        == 0
    )
    out = json.loads(capsys.readouterr().out)
    assert out["number"] == 41 and out["build_pr_recorded"] == 41
    assert status_mod.read_status(change).build_pr == 41
    assert "build_pr: 41" in (change / "status.yaml").read_text(encoding="utf-8")
    # a second upsert of the same PR changes nothing
    answers[("GET", "/pulls?")] = {
        "status": 200,
        "data": [{"number": 41, "html_url": "https://github.com/o/r/pull/41", "labels": []}],
        "error": "",
    }
    answers[("PATCH", "/repos/o/r/pulls/41")] = {"status": 200, "data": {"number": 41}, "error": ""}
    assert pr_cli.main(["upsert", "--root", str(root), "--id", "0001", "--phase", "test"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["number"] == 41 and "build_pr_recorded" not in out


def test_upsert_posts_not_a_build_pr_on_every_other_pull_request(project, capsys, recorder):
    """R22 (decision 36, point 5): ruleset 2 requires sdlc/review; the workflow token's pull
    requests start no run of sdlc-merge.yml, so the upsert posts the passing "not a build
    PR" on the head of every pull request that is not the build PR."""
    root, change = project
    calls, answers = recorder
    gate_json(change, "design", "wait", c.ready_label("design"))
    gate_json(change, "build", "park", c.NEEDS_HUMAN_LABEL)
    answers[("GET", "/pulls?")] = {"status": 200, "data": [], "error": ""}
    answers[("POST", "/repos/o/r/pulls")] = {
        "status": 201,
        "data": {"number": 41, "html_url": "https://github.com/o/r/pull/41", "node_id": "PR_41"},
        "error": "",
    }
    answers[("GET", "/repos/o/r/pulls/41")] = {
        "status": 200,
        "data": {"number": 41, "head": {"ref": "sdlc/0001/design", "sha": "f" * 40}},
        "error": "",
    }
    answers[("POST", "/check-runs")] = {"status": 201, "data": {"id": 3}, "error": ""}
    git(root, "remote", "add", "origin", "https://github.com/o/r.git")
    assert pr_cli.main(["upsert", "--root", str(root), "--id", "0001", "--phase", "design"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["review_check"]["ok"] is True
    [posted] = [p for m, u, p in calls if m == "POST" and u.endswith("/check-runs")]
    assert posted["name"] == "sdlc/review" and posted["head_sha"] == "f" * 40
    assert posted["conclusion"] == "success" and posted["output"]["title"] == "not a build PR"
    # the build PR gets none: its sdlc/review is the review pass's, posted by the (e) run
    calls.clear()
    assert (
        pr_cli.main(["upsert", "--root", str(root), "--id", "0001", "--phase", "build", "--draft"])
        == 0
    )
    out = json.loads(capsys.readouterr().out)
    assert "review_check" not in out
    assert not [u for m, u, _p in calls if u.endswith("/check-runs")]


def test_upsert_posts_the_phase_check_run_when_asked(project, capsys, monkeypatch):
    """The phase (d) runbook line is one command: upsert --check-run (build guide step 28)."""
    root, change = project
    gate_json(change, "test", "park", c.NEEDS_HUMAN_LABEL)
    logs(change, exit_code=1)
    monkeypatch.setattr(github.shutil, "which", lambda *_a, **_k: None)
    posted: list[tuple] = []
    monkeypatch.setattr(
        github,
        "create_check_run",
        lambda *args: posted.append(args) or {"route": "api", "ok": True, "id": 3},
    )
    code = pr_cli.main(
        ["upsert", "--root", str(root), "--id", "0001", "--phase", "test", "--check-run"]
    )
    assert code == 0
    out = json.loads(capsys.readouterr().out)
    assert out["check_run"]["name"] == "sdlc/test"
    assert out["check_run"]["conclusion"] == "failure"  # the gate parked
    assert "test red" in out["check_run"]["summary"]  # the evidence summary, as posted
    # without the flag nothing is posted at all
    assert pr_cli.main(["upsert", "--root", str(root), "--id", "0001", "--phase", "test"]) == 0
    assert "check_run" not in json.loads(capsys.readouterr().out)


def test_label_colours(project):
    assert pr_cli.label_color(c.NEEDS_HUMAN_LABEL) == "D93F0B"
    assert pr_cli.label_color(c.ready_label("build")) == "0E8A16"


# --- the GitHub client ------------------------------------------------------------------------
@pytest.fixture(autouse=True)
def no_minutes_meter(monkeypatch):
    """The digest's Actions-minutes meter (R25) reads GitHub; these tests never do. Its own
    tests are in test_actions_minutes.py."""
    monkeypatch.setattr(digest_mod, "minutes_meter", lambda repo: "")


@pytest.fixture
def no_gh(monkeypatch):
    """No `gh` on PATH: every route decision falls to the token."""
    monkeypatch.setattr(github.shutil, "which", lambda *_a, **_k: None)
    for var in github.TOKEN_VARS:
        monkeypatch.delenv(var, raising=False)


@pytest.fixture
def fake_gh(monkeypatch):
    """A ``gh`` on PATH that runs nothing: it records (args, stdin, cwd) and answers from a
    queue of ``_gh`` results (an empty queue means success with no output)."""
    calls: list[dict] = []
    answers: list[dict] = []

    def run(*args, stdin=None, cwd=None):
        calls.append({"args": list(args), "stdin": stdin, "cwd": cwd})
        return answers.pop(0) if answers else {"ok": True, "code": 0, "out": "", "err": ""}

    monkeypatch.setattr(github, "gh_path", lambda: "/usr/bin/gh")
    monkeypatch.setattr(github, "_gh", run)
    return calls, answers


@pytest.fixture
def gh_only(monkeypatch, fake_gh):
    """``gh`` and no token: the fallback route on its own."""
    for var in github.TOKEN_VARS:
        monkeypatch.delenv(var, raising=False)
    return fake_gh


@pytest.fixture
def recorder(monkeypatch, no_gh):
    """Record every call to the single HTTP entry point and answer from a canned table."""
    calls: list[tuple] = []
    answers: dict[tuple[str, str], dict] = {}

    def fake(method, url, tok, payload=None):
        assert tok == "secret-token"
        calls.append((method, url, payload))
        for (m, fragment), answer in answers.items():
            if m == method and fragment in url:
                return answer
        return {"status": 200, "data": {}, "error": ""}

    monkeypatch.setenv("GITHUB_TOKEN", "secret-token")
    monkeypatch.setattr(github, "_request", fake)
    return calls, answers


def test_no_route_without_gh_or_token_returns_the_compare_url(no_gh):
    result = github.create_pr("o/r", "main", "sdlc/0001/build", "t", "b", draft=True)
    assert result["route"] == "none"
    assert result["compare_url"] == "https://github.com/o/r/compare/main...sdlc/0001/build?expand=1"
    assert github.find_open_pr("o/r", "sdlc/0001/build")["number"] is None
    assert (
        github.create_check_run("o/r", "abc", "sdlc/test", "success", "t", "s")["route"] == "none"
    )


def test_find_open_pr_and_create_and_update(recorder):
    calls, answers = recorder
    answers[("GET", "/pulls?")] = {"status": 200, "data": [], "error": ""}
    assert github.find_open_pr("o/r", "sdlc/0001/build")["number"] is None
    assert "head=o%3Asdlc%2F0001%2Fbuild" in calls[0][1]

    answers[("POST", "/repos/o/r/pulls")] = {
        "status": 201,
        "data": {"number": 7, "html_url": "https://github.com/o/r/pull/7", "node_id": "PR_7"},
        "error": "",
    }
    created = github.create_pr(
        "o/r", "main", "sdlc/0001/build", "build(0001): x", "body", draft=True
    )
    assert created["route"] == "api" and created["number"] == 7 and created["created"] is True
    assert calls[-1][2]["draft"] is True and calls[-1][2]["base"] == "main"

    answers[("PATCH", "/repos/o/r/pulls/7")] = {
        "status": 200,
        "data": {"number": 7, "html_url": "https://github.com/o/r/pull/7"},
        "error": "",
    }
    updated = github.update_pr("o/r", 7, "new body", "new title")
    assert updated["ok"] and updated["created"] is False
    assert calls[-1][2] == {"body": "new body", "title": "new title"}


def test_set_labels_removes_then_adds(recorder):
    calls, _answers = recorder
    result = github.set_labels(
        "o/r", 7, ["sdlc:deploy-ready"], ["sdlc:test-ready", "sdlc:needs-human"]
    )
    assert result["ok"] is True
    methods = [call[0] for call in calls]
    assert methods == ["DELETE", "DELETE", "POST"]  # remove first, then add
    assert calls[0][1].endswith("/issues/7/labels/sdlc%3Atest-ready")
    assert calls[-1][2] == {"labels": ["sdlc:deploy-ready"]}


def test_set_labels_ignores_404_on_remove(recorder):
    _calls, answers = recorder
    answers[("DELETE", "/labels/")] = {
        "status": 404,
        "data": {"message": "Not Found"},
        "error": "Not Found",
    }
    result = github.set_labels("o/r", 7, [], ["sdlc:build-ready"])
    assert result["ok"] is True and result["removed"] == []


def test_ensure_label_never_forces_and_accepts_an_existing_label(monkeypatch, gh_only):
    """--force would rewrite the colour and description of a label the owner edited."""
    calls, answers = gh_only
    answers.append({"ok": False, "code": 1, "out": "", "err": "label already exists; ..."})
    result = github.ensure_label("o/r", "sdlc:build-ready", "0E8A16", "SDLC gate (build)")
    assert result["ok"] is True and result["created"] is False
    assert "--force" not in calls[0]["args"]


def test_ensure_label_treats_already_exists_as_success(recorder):
    _calls, answers = recorder
    answers[("POST", "/labels")] = {
        "status": 422,
        "data": {"message": "Validation Failed", "errors": [{"code": "already_exists"}]},
        "error": "Validation Failed",
    }
    result = github.ensure_label("o/r", "sdlc:build-ready", "0E8A16", "SDLC gate (build)")
    assert result["ok"] is True and result["created"] is False


def test_set_ready_uses_the_graphql_mutation(recorder):
    calls, answers = recorder
    answers[("GET", "/pulls/7")] = {"status": 200, "data": {"node_id": "PR_7"}, "error": ""}
    answers[("POST", "/graphql")] = {"status": 200, "data": {"data": {}}, "error": ""}
    assert github.set_ready("o/r", 7)["ok"] is True
    assert "markPullRequestReadyForReview" in calls[-1][2]["query"]
    assert calls[-1][2]["variables"] == {"id": "PR_7"}


def test_check_run_and_issue_helpers(recorder):
    calls, answers = recorder
    answers[("POST", "/check-runs")] = {"status": 201, "data": {"id": 3}, "error": ""}
    assert github.create_check_run("o/r", "sha", "sdlc/test", "success", "t", "s")["id"] == 3
    assert calls[-1][2]["conclusion"] == "success"

    answers[("GET", "/issues?")] = {
        "status": 200,
        "data": [{"number": 9, "title": digest_mod.ISSUE_TITLE, "node_id": "I_9"}],
        "error": "",
    }
    found = github.pinned_issue("o/r", digest_mod.ISSUE_TITLE)
    assert found["number"] == 9 and found["node_id"] == "I_9"
    answers[("PATCH", "/issues/9")] = {"status": 200, "data": {"number": 9}, "error": ""}
    assert github.update_issue_body("o/r", 9, "# queue")["ok"] is True


# --- the order of the routes (third live design run, 2026-09-21) ------------------------------
def test_the_token_route_goes_first_and_gh_is_never_called(recorder, fake_gh):
    """A CI runner has both. The token is the identity the workflow acts as and the REST call
    behaves the same everywhere, so it goes first; ``gh`` is the fallback."""
    calls, answers = recorder
    gh_calls, _gh_answers = fake_gh
    answers[("POST", "/repos/o/r/pulls")] = {
        "status": 201,
        "data": {"number": 7, "html_url": "https://github.com/o/r/pull/7"},
        "error": "",
    }
    created = github.create_pr("o/r", "main", "sdlc/0001/build", "t", "body", cwd="/tmp/project")
    assert created["route"] == "api" and created["number"] == 7
    assert gh_calls == [] and calls[-1][0] == "POST"


def test_gh_takes_over_when_the_token_route_fails(recorder, fake_gh):
    _calls, answers = recorder
    gh_calls, gh_answers = fake_gh
    answers[("POST", "/repos/o/r/pulls")] = {
        "status": 403,
        "data": {"message": "Resource not accessible by integration"},
        "error": "Resource not accessible by integration",
    }
    gh_answers.append({"ok": True, "code": 0, "out": "https://github.com/o/r/pull/9\n", "err": ""})
    created = github.create_pr("o/r", "main", "sdlc/0001/build", "t", "body", cwd="/tmp/project")
    assert created["route"] == "gh" and created["number"] == 9 and created["created"] is True
    assert gh_calls[0]["args"][:2] == ["pr", "create"]
    assert gh_calls[0]["cwd"] == "/tmp/project"  # gh reads the repo from its directory
    assert gh_calls[0]["stdin"] == "body"


def test_when_both_routes_fail_the_reason_names_both(recorder, fake_gh):
    _calls, answers = recorder
    _gh_calls, gh_answers = fake_gh
    answers[("PATCH", "/repos/o/r/pulls/7")] = {
        "status": 404,
        "data": {"message": "Not Found"},
        "error": "Not Found",
    }
    gh_answers.append(
        {"ok": False, "code": 1, "out": "", "err": "could not determine base repository"}
    )
    result = github.update_pr("o/r", 7, "body", "title", cwd="/tmp/project")
    assert result["ok"] is False and result["route"] == "none" and result["number"] == 7
    assert "api: Not Found" in result["reason"]
    assert "gh: gh pr edit exited 1: could not determine base repository" in result["reason"]


def test_gh_alone_still_opens_the_pull_request(gh_only):
    calls, answers = gh_only
    answers.append({"ok": True, "code": 0, "out": "https://github.com/o/r/pull/4\n", "err": ""})
    result = github.create_pr("o/r", "main", "sdlc/0001/design", "t", "body", cwd="/tmp/project")
    assert result["route"] == "gh" and result["number"] == 4
    assert calls[0]["cwd"] == "/tmp/project"

    answers.append({"ok": True, "code": 0, "out": "[]", "err": ""})
    assert github.find_open_pr("o/r", "sdlc/0001/design", cwd="/tmp/project")["number"] is None
    assert calls[-1]["cwd"] == "/tmp/project"


# --- the daily digest ---------------------------------------------------------------------
QUEUE = [
    {
        "number": 4,
        "title": "build(0002): invoice totals",
        "html_url": "https://github.com/o/r/pull/4",
        "updated_at": "2026-09-20T08:00:00Z",
        "labels": [{"name": "sdlc:needs-human"}],
        "body": "- **What changed and why**: invoice totals (fix, ticket route)\n- more\n",
    },
    {
        "number": 2,
        "title": "design(0001): percent helper",
        "html_url": "https://github.com/o/r/pull/2",
        "updated_at": "2026-09-21T09:00:00Z",
        "labels": [{"name": "sdlc:design-ready"}],
        "body": "- **What changed and why**: percent helper (feature, idea route)\n",
    },
    {
        "number": 5,
        "title": "chore: unrelated",
        "html_url": "https://github.com/o/r/pull/5",
        "updated_at": "2026-09-21T09:30:00Z",
        "labels": [{"name": "dependencies"}],
        "body": "- nothing to do with the framework\n",
    },
]


def test_render_digest_puts_parked_first_and_skips_unlabelled_prs():
    markdown = digest_mod.render_digest(QUEUE, "2026-09-21T10:00:00Z")
    assert markdown.startswith("# SDLC review queue — 2026-09-21")
    assert "1 parked, 1 waiting at a gate." in markdown
    parked_at = markdown.index("## Parked")
    ready_at = markdown.index("## Waiting at a human gate")
    assert parked_at < ready_at
    assert markdown.index("#4") < ready_at < markdown.index("#2")
    assert "invoice totals (fix, ticket route)" in markdown  # the first bullet of the body
    assert "unrelated" not in markdown


def test_render_digest_empty_queue():
    markdown = digest_mod.render_digest([], "2026-09-21T10:00:00Z")
    assert digest_mod.NOTHING_WAITING in markdown
    assert "## Parked" not in markdown


def test_digest_shows_the_owner_labels_beside_the_gate_label():
    """D11 (live run of 2026-09-25): the `schedule` label the owner applied at gate (maintain) was
    invisible, so a scheduled incident looked like a waiting one."""
    labels = [{"name": "sdlc:maintain-ready"}, {"name": "incident"}, {"name": "schedule"}]
    intent = {"number": 7, "title": "intent(0009): incident", "html_url": "https://x/7"}
    intent["labels"] = labels
    md = digest_mod.render_digest([intent], "2026-09-25T06:00:00Z")
    section = md[md.index("## Waiting at a human gate") :]
    line = next(ln for ln in section.splitlines() if "#7" in ln)
    assert "— `sdlc:maintain-ready`, `incident`, `schedule` —" in line
    assert "## Phase (f)" not in md  # it carries its gate label: a queue item
    reordered = {**intent, "labels": [{"name": "schedule"}, {"name": "sdlc:maintain-ready"}]}
    line = digest_mod._line(reordered)
    assert "— `sdlc:maintain-ready`, `schedule` —" in line


def test_digest_main_dry_run_reads_the_input_file(tmp_path, capsys, no_gh):
    path = tmp_path / "prs.json"
    write(path, json.dumps(QUEUE))
    assert digest_mod.main(["--repo", "o/r", "--dry-run", "--input", str(path)]) == 0
    out = capsys.readouterr().out
    assert "## Parked" in out and "design(0001): percent helper" in out


def test_digest_main_without_a_token_still_renders(capsys, no_gh):
    assert digest_mod.main(["--repo", "o/r"]) == 0
    out = capsys.readouterr().out
    assert "no GITHUB_TOKEN/GH_TOKEN" in out
    assert digest_mod.NOTHING_WAITING in out


def test_digest_publish_updates_the_issue_body(recorder):
    calls, answers = recorder
    answers[("GET", "/issues?")] = {
        "status": 200,
        "data": [{"number": 9, "title": digest_mod.ISSUE_TITLE, "node_id": "I_9"}],
        "error": "",
    }
    answers[("PATCH", "/issues/9")] = {"status": 200, "data": {"number": 9}, "error": ""}
    result = digest_mod.publish("o/r", "# queue\n")
    assert result["ok"] is True and result["number"] == 9
    assert calls[-1][0] == "PATCH" and calls[-1][2] == {"body": "# queue\n"}


# --- phase (f): the incident intent PR (build guide steps 37 and 39; plugin 0.2.19) -----------
def test_phase_f_bullets_describe_the_finding_the_route_and_the_triage(project):
    from detect import finding

    root, change = project
    st = status_mod.read_status(change)
    st.entry_route, st.change_type = "incident", "fix"
    st.set_phase("maintain")
    status_mod.write_status(change, st)
    write(
        change / "intent.md",
        INTENT.replace("Entry route: idea", "Entry route: incident abc")
        + "\n## Evidence\nwe1 at 3sigma; run https://x/runs/1.\n",
    )
    verdict = {
        "tier": 3,
        "rules_hit": ["we1"],
        "rule": "we1",
        "mean": 0.05,
        "sigma": 0.02,
        "sigmas": 47.5,
        "latest": {"at": "2026-09-24", "value": 1.0, "meta": {}},
        "breach_start": "2026-09-24",
        "window_days": 30,
        "n_baseline": 20,
        "n_tail": 8,
        "direction": "above",
        "reason": "one point beyond 3 sigma",
    }
    finding.write(
        change / "evidence" / finding.DETECTION_FILE,
        finding.build_record(
            metric="ci_test_failure_rate",
            source="github-actions",
            verdict=verdict,
            observations=[],
            action="propose",
            failed_run_urls=[],
            commits=[],
        ),
    )
    write(
        change / "evidence" / finding.PROPOSAL_FILE,
        json.dumps(
            {
                "schema_version": 1,
                "tier": 3,
                "route": "runbook:revert-pr",
                "args": {"sha": "0" * 40},
                "rationale": "x",
            }
        ),
    )
    write(
        change / "evidence" / "runbook-revert-pr.json",
        json.dumps({"runbook": "revert-pr", "status": "go-requested"}),
    )
    body = desc.build_description(root, "0001", "maintain")
    lines = bullets(body)
    heads = [line.split("**")[1] for line in lines]
    assert heads == ["Finding", "Proposed outcome", "Route", "Entry route", "What needs you"]
    assert lines[0] == (
        "- **Finding**: ci_test_failure_rate at tier 3 (we1): 1.000 on 2026-09-24 "
        "(mean 0.050, sigma 0.020)"
    )
    assert lines[2] == "- **Route**: runbook:revert-pr (go-requested)"
    assert lines[3].endswith("incident route, fix change")
    assert "merge = fix now" in lines[4] and "close with a comment = dismiss" in lines[4]
    assert f"changes/{CHANGE_DIR_NAME}/evidence/detection.json" in body
    assert "Counters: no fix round so far" in body
    # a parked gate (Go requested) shows "What I need from you"
    write(
        change / "evidence" / "gate-maintain.json",
        json.dumps(
            {
                "result": "park",
                "label": "sdlc:needs-human",
                "reason": "route: Go",
                "checks": [
                    {
                        "name": "route",
                        "ok": False,
                        "reason": "Go requested",
                        "need": "Apply `sdlc:go` on this PR",
                        "details": {},
                    }
                ],
            }
        ),
    )
    body = desc.build_description(root, "0001", "maintain")
    assert "What I need from you" in body and "Apply `sdlc:go`" in body
    assert desc.pr_title(status_mod.read_status(change), "maintain").startswith("maintain(0001): ")
    assert desc.head_branch("0001", "maintain") == "sdlc/0001/intent"


def test_phase_f_finding_of_a_rehearsal_on_an_empty_series_says_no_observation(project):
    """A forced rehearsal whose source returned nothing (live run of 2026-09-25): the finding
    names the record's day with "no observation", never "None", and has no band."""
    from detect import finding

    root, change = project
    st = status_mod.read_status(change)
    st.entry_route, st.change_type = "incident", "fix"
    st.set_phase("maintain")
    status_mod.write_status(change, st)
    write(change / "intent.md", INTENT.replace("Entry route: idea", "Entry route: incident abc"))
    verdict = {
        "tier": 2,
        "rules_hit": ["forced"],
        "rule": "forced",
        "mean": None,
        "sigma": None,
        "sigmas": None,
        "latest": None,
        "breach_start": None,
        "window_days": 30,
        "n_baseline": 0,
        "n_tail": 0,
        "direction": "above",
        "reason": "tier 2 forced by workflow_dispatch (a rehearsal)",
    }
    finding.write(
        change / "evidence" / finding.DETECTION_FILE,
        finding.build_record(
            metric="ci_test_failure_rate",
            source="github-actions",
            verdict=verdict,
            observations=[],
            action="diagnose",
            failed_run_urls=[],
            commits=[],
            forced=True,
            at="2026-09-25T05:41:00Z",
        ),
    )
    lines = bullets(desc.build_description(root, "0001", "maintain"))
    assert lines[0] == (
        "- **Finding**: ci_test_failure_rate at tier 2 (forced): no observation in the window "
        "(run of 2026-09-25), forced by a rehearsal"
    )
    assert "None" not in lines[0]


# --- build guide step 42.2: the counters over changes/*/ (plugin 0.2.19) ---------------------
def test_counters_over_the_change_folders_and_the_digest_section(project, tmp_path):
    from detect import dismissals
    from pr import counters

    root, change = project
    base = counters.collect(root)  # the fixture's own changes (0000-sdlc-init, 0001)
    st = status_mod.read_status(change)
    st.set_phase("deploy")  # shipped, first pass
    status_mod.write_status(change, st)
    second, st2 = status_mod.new_change(root, "Second", entry_route="incident", change_type="fix")
    st2.set_phase("deploy")
    st2.bump_iteration()
    st2.bump_iteration()
    status_mod.write_status(second, st2)
    third, st3 = status_mod.new_change(root, "Third", entry_route="incident", change_type="fix")
    st3.abandon("closed")  # 0.2.26: an abandoned folder is not an incident merged
    status_mod.write_status(third, st3)
    path = dismissals.path_for(root)
    dismissals.save(
        path,
        dismissals.add(
            dismissals.load(path), "a" * 16, kind="detect", reason="noise", by="o", change_id="0003"
        ),
    )
    counts = counters.collect(root)
    assert counts["changes"] == base["changes"] + 1 and counts["abandoned"] == 1
    assert counts["shipped"] == base["shipped"] + 2
    assert counts["first_pass_merges"] == base["first_pass_merges"] + 1
    assert counts["fix_iterations_total"] == base["fix_iterations_total"] + 2
    assert counts["incidents_merged"] == 1 and counts["incidents_shipped"] == 1
    assert counts["dismissals"] == 1 and counts["dismissals_by_kind"] == {"detect": 1, "scan": 0}
    md = counters.render(counts)
    assert md.startswith("## Counters") and "| First-pass merge share | " in md
    assert (
        "| Incidents merged (fix now) / shipped | 1 / 1 | Closing the loop (p.45), lagging |" in md
    )
    assert "never reach the default branch" in md
    assert "1 change folder(s) abandoned after a merge, left out." in md
    digest = digest_mod.render_digest([], "2026-09-25T06:00:00Z", md)
    assert digest_mod.NOTHING_WAITING in digest and "## Counters" in digest
    digest = digest_mod.render_digest(QUEUE, "2026-09-25T06:00:00Z", md)
    assert digest.index("## Waiting at a human gate") < digest.index("## Counters")
    assert digest.rstrip().endswith("Generated 2026-09-25T06:00:00Z.")
    assert counters.main(["--root", str(root), "--json"]) == 0


def _ship(change_dir, st, classification=None, growth=None):
    """Mark a change shipped (phase e), with the plan's class in an adversarial verdict and
    the plan's growth in the gate-e record when given."""
    st.set_phase("deploy")
    status_mod.write_status(change_dir, st)
    evidence = change_dir / art.EVIDENCE_DIR
    evidence.mkdir(parents=True, exist_ok=True)
    if classification:
        verdict = {"schema_version": 1, "phase": "deploy", "head": "f" * 40, "verdict": "continue",
                   "reasons": [], "classification": classification,
                   "classification_reasons": []}  # fmt: skip
        (evidence / art.ADVERSARIAL_VERDICT.format(phase="deploy")).write_text(
            json.dumps(verdict), encoding="utf-8"
        )
    if growth is not None:
        growth_record = {"plan_growth": {"added": growth, "removed": []}}
        record = {"checks": [{"name": "plan_sync", "ok": True, "details": growth_record}]}
        (evidence / art.GATE_RESULT.format(phase="deploy")).write_text(
            json.dumps(record), encoding="utf-8"
        )


def test_counters_true_definitions_class_split_and_plan_growth(project):
    """R26 parts 1 and 2 and choice 257's ports: a reset change by any of the three routes is
    never first-pass and is named under the table; an expired dismissal is not in force; the
    first-pass share and the fix iterations are split by the plan's class with their "n of
    m"; the plan's growth since gate (design) is counted; every row names its play."""
    from detect import dismissals
    from pr import counters

    root, change = project
    st = status_mod.read_status(change)
    _ship(change, st, "routine", growth=["src/a.py", "src/b.py"])  # 0001: first pass
    by_label, st2 = status_mod.new_change(root, "Label reset")
    st2.bump_iteration()
    st2.record_owner_label(c.RESET_ITERATIONS_LABEL, "owner")
    _ship(by_label, st2, "non-routine")
    by_hand, st3 = status_mod.new_change(root, "Hand reset")
    st3.bump_iteration()
    st3.set_iterations(0)
    _ship(by_hand, st3, "non-routine", growth=[])
    by_runner, st4 = status_mod.new_change(root, "Runner reset")
    st4.iterations_reset_by, st4.iterations_reset_at = "sdlc-runner:1/1", "2026-10-23T00:00:00Z"
    _ship(by_runner, st4)  # no verdict: unclassified
    path = dismissals.path_for(root)
    record = dismissals.add(
        dismissals.load(path), "a" * 16, kind="detect", reason="noise", by="o", change_id="0003"
    )
    record = dismissals.add(
        record, "b" * 16, kind="scan", reason="old", by="o", change_id="0003", until="2020-01-01"
    )
    dismissals.save(path, record)

    counts = counters.collect(root)
    ids = {st.id: name for st, name in ((st2, "label"), (st3, "hand"), (st4, "runner"))}
    assert counts["reset_shipped"] == sorted(ids)
    assert counts["first_pass_merges"] == 1  # 0001 only (0000-sdlc-init is not shipped)
    assert counts["by_class"]["routine"]["first_pass_merges"] == 1
    assert counts["by_class"]["routine"]["shipped"] == 1
    assert counts["by_class"]["non-routine"] == {
        "shipped": 2, "first_pass_merges": 0, "first_pass_share": 0.0,
        "fix_iterations_mean": 0.0,
    }  # fmt: skip
    assert counts["by_class"]["unclassified"]["shipped"] == 1
    assert counts["plan_grown"] == {"0001": 2} and counts["plan_growth_recorded"] == 2
    assert counts["dismissals"] == 1 and counts["dismissals_expired"] == 1
    assert counts["dismissals_by_kind"] == {"detect": 1, "scan": 0}

    md = counters.render(counts)
    assert (
        "| First-pass merge share, routine plans | 100% (1 of 1) | Plan mode (p.17), leading |"
        in md
    )
    assert "| First-pass merge share, non-routine plans | 0% (0 of 2) |" in md
    assert "| Fix iterations per shipped change, non-routine plans | 0.0 (2 of 4 shipped) |" in md
    assert (
        "| Plan grown since gate (design) (shipped changes with the record) | 1 of 2 (2 files) |"
        in md
    )
    assert "2 shipped change(s) have no record of the plan's growth" in md
    assert "| Panel calls, all changes (decision 21) | 0 | — |" in md
    assert f"Reset, never first-pass: {', '.join(sorted(ids))}." in md
    assert "1 shipped change(s) carry no class" in md
    assert "1 expired dismissal(s), not in force." in md
    assert "DORA, built in a change of its own" in md


def test_the_build_pr_body_shows_the_plan_s_growth(project):
    """Choice 257 (R60's port): the build PR's banner, from the gate records it covers."""
    root, change = project
    gate_json(change, "deploy", "wait", c.ready_label("deploy"))
    record = json.loads(
        (change / art.EVIDENCE_DIR / "gate-deploy.json").read_text(encoding="utf-8")
    )
    growth = {"plan_growth": {"added": ["src/x.py", "src/y.py"], "removed": []}}
    for check in record["checks"]:  # the fixture's own plan_sync check gains the record
        if check["name"] == "plan_sync":
            check["details"].update(growth)
    (change / art.EVIDENCE_DIR / "gate-deploy.json").write_text(
        json.dumps(record), encoding="utf-8"
    )
    body = desc.build_description(root, "0001", "deploy")
    assert "- The plan grew by 2 files since gate (design): `src/x.py`, `src/y.py`." in body
    assert body.index("**Needs your close look**") < body.index("- **What changed and why**")


def test_counters_name_a_class_with_no_shipped_change(project):
    """The settle table: a class with no shipped change reads "0 of 0", never a rate."""
    from pr import counters

    md = counters.render(counters.collect(project[0]))
    assert "| First-pass merge share, routine plans | 0 of 0, no routine plan shipped yet |" in md
    assert "| First-pass merge share, non-routine plans | 0 of 0, no non-routine plan " in md


def test_counters_line_of_an_open_pr_after_a_reset(project):
    """R26 part 1: a reset count never reads as first-pass on the PR either."""
    root, change = project
    st = status_mod.read_status(change)
    st.bump_iteration()
    st.record_owner_label(c.RESET_ITERATIONS_LABEL, "owner")
    status_mod.write_status(change, st)
    gate_json(change, "build", "continue", None)
    body = desc.build_description(root, "0001", "build")
    assert (
        f"Counters: first-pass: no (count reset {st.iterations_reset_at}) · fix iterations: 0"
        in body
    )


def test_digest_lists_the_runbook_and_dismissal_prs_under_the_triage_label():
    """Session-5 review: a revert, a quarantine or a dismissal PR carries `sdlc:triage` (R45,
    row 37; `incident` until 1.0.43) and no gate label; decision 20 makes the digest the
    only place the owner meets them. Since the label carries the `sdlc:` prefix, the filter
    is "no gate label", not "no sdlc: label", and the PR is not a queue item."""
    revert = {
        "number": 31,
        "title": "revert(0007): fix x",
        "body": "- **Runbook**: revert-pr",
        "html_url": "https://x/31",
        "labels": [{"name": "sdlc:triage"}],
    }
    md = digest_mod.render_digest([*QUEUE, revert], "2026-09-25T06:00:00Z")
    assert "1 runbook or dismissal PR(s) of maintain" in md
    assert "## Maintain: runbook and dismissal PRs — `sdlc:triage`" in md and "#31" in md
    assert md.index("## Waiting at a human gate") < md.index("## Maintain:")
    waiting = md[md.index("## Waiting at a human gate") : md.index("## Maintain:")]
    assert "#31" not in waiting  # a runbook PR waits at no gate
    md = digest_mod.render_digest([revert], "2026-09-25T06:00:00Z")
    assert digest_mod.NOTHING_WAITING not in md and "#31" in md
    assert "0 parked, 0 waiting at a gate" in md
    assert digest_mod.incident_prs(QUEUE) == []  # an intent PR has its gate label: a queue item
    # an incident intent PR at its gate is a queue item, listed once, never as a runbook PR
    intent = {
        **revert,
        "number": 33,
        "labels": [{"name": "sdlc:triage"}, {"name": "sdlc:maintain-ready"}],
    }
    md = digest_mod.render_digest([intent], "2026-09-25T06:00:00Z")
    assert "0 parked, 1 waiting at a gate" in md and md.count("#33") == 1
    assert "## Maintain:" not in md and digest_mod.incident_prs([intent]) == []
    # a scheduled one stays a runbook PR, and an older plugin's `incident` is still read
    scheduled = {**revert, "labels": [{"name": "sdlc:triage"}, {"name": "sdlc:schedule"}]}
    older = {**revert, "number": 32, "labels": [{"name": "incident"}]}
    assert digest_mod.incident_prs([scheduled, older]) == [scheduled, older]


def test_the_queue_listing_keeps_an_older_plugin_s_incident_pr(monkeypatch):
    """R45 (row 37): the pulls listing keeps every PR with an ``sdlc:`` label, and for one
    release a PR an older plugin labelled ``incident`` with no ``sdlc:`` label at all."""
    pulls = [
        {"number": 1, "labels": [{"name": "sdlc:triage"}]},
        {"number": 2, "labels": [{"name": "incident"}]},
        {"number": 3, "labels": [{"name": "bug"}]},
    ]
    monkeypatch.setattr(github, "token", lambda: "t")
    monkeypatch.setattr(github, "_request", lambda *a, **k: {"error": None, "data": pulls})
    prs, error = digest_mod.list_queue_prs("o/r")
    assert error == "" and [pr["number"] for pr in prs] == [1, 2]


def test_digest_and_review_requests_read_the_letter_labels_of_an_older_plugin(monkeypatch):
    """R45, for one release: a PR an older plugin labelled ``sdlc:c-ready`` waits at a gate in
    the digest, sorted in phase order beside the names, and still requests the owner's
    review; an approved build PR at ``sdlc:e-ready`` gets the approval line."""
    from pr import review_request

    def pr(number, label):
        return {"number": number, "title": f"t{number}", "labels": [{"name": label}]}

    queue = [pr(1, "sdlc:deploy-ready"), pr(2, "sdlc:c-ready"), pr(3, "sdlc:intent-ready")]
    md = digest_mod.render_digest(queue, "2026-09-25T06:00:00Z")
    assert "0 parked, 3 waiting at a gate" in md
    assert md.index("#3 t3") < md.index("#2 t2") < md.index("#1 t1")  # intent, build, deploy
    assert review_request.is_waiting_label("sdlc:c-ready")
    assert review_request.is_waiting_label("sdlc:build-ready")
    seen = []
    monkeypatch.setattr(github, "pr_reviews", lambda repo, n: seen.append(n) or {"ok": False})
    for label in ("sdlc:e-ready", "sdlc:deploy-ready", "sdlc:build-ready"):
        digest_mod.approval_of("o/r", pr(7, label))
    assert seen == [7, 7]


# --- the default branch's protection (decision 4; plugin 0.2.25) ------------------------------
def test_default_branch_protection_counts_a_restrict_updates_rule_only(recorder):
    """The framework's own default branch was unprotected at the 1.0.0 readiness review
    (2026-09-26). Only a ruleset's ``update`` rule (Restrict updates, the owner as bypass)
    keeps the workflow token from merging: a classic flag or a pull-request rule without
    it does not count (the review of the 0.2.25 diff, finding H1)."""
    calls, answers = recorder
    # the more specific fragments first: the recorder returns the first match
    answers[("GET", "/rules/branches/main")] = {"status": 200, "data": [], "error": ""}
    answers[("GET", "/branches/main")] = {"status": 200, "data": {"protected": False}, "error": ""}
    answers[("GET", "/repos/o/r")] = {
        "status": 200,
        "data": {"default_branch": "main"},
        "error": "",
    }
    result = github.default_branch_protection("o/r")
    assert result == {
        "route": "api", "ok": True, "branch": "main", "protected": False,
        "classic": False, "rules": [], "by": "nothing",
    }  # fmt: skip
    assert [url.split("api.github.com")[1] for _m, url, _p in calls] == [
        "/repos/o/r", "/repos/o/r/branches/main", "/repos/o/r/rules/branches/main"
    ]  # fmt: skip
    # a pull-request rule and a classic flag: still not enforcing
    answers[("GET", "/rules/branches/main")]["data"] = [
        {"type": "pull_request"},
        {"type": "deletion"},
    ]
    answers[("GET", "/branches/main")]["data"]["protected"] = True
    result = github.default_branch_protection("o/r")
    assert result["protected"] is False and result["classic"] is True
    assert result["rules"] == ["deletion", "pull_request"]
    assert result["by"] == "classic branch protection; rules deletion, pull_request"
    # the update rule: enforcing
    answers[("GET", "/rules/branches/main")]["data"].append({"type": "update"})
    result = github.default_branch_protection("o/r")
    assert result["protected"] is True and result["by"] == "ruleset: restrict updates"
    answers[("GET", "/repos/o/r")] = {"status": 404, "data": {}, "error": "Not Found"}
    assert github.default_branch_protection("o/r")["ok"] is False


def test_merge_environment_is_safe_only_for_the_default_branch_alone(recorder):
    """Choice 250 (the R22 double check, F8): the sdlc-merge environment keeps the merge
    App's key to the default branch only with selected branches whose one rule is it."""
    calls, answers = recorder
    env_url = "/environments/sdlc-merge"
    answers[("GET", env_url + "/deployment-branch-policies")] = {
        "status": 200, "data": {"branch_policies": [{"name": "main", "type": "branch"}]},
        "error": "",
    }  # fmt: skip
    custom = {"protected_branches": False, "custom_branch_policies": True}
    answers[("GET", env_url)] = {
        "status": 200, "data": {"deployment_branch_policy": custom}, "error": ""
    }  # fmt: skip
    got = github.merge_environment("o/r", "main")
    assert (got["ok"], got["exists"], got["safe"]) == (True, True, True)
    # a second rule, a tag rule, every protected branch, no policy: each is unsafe
    policies = answers[("GET", env_url + "/deployment-branch-policies")]["data"]
    policies["branch_policies"].append({"name": "dev", "type": "branch"})
    got = github.merge_environment("o/r", "main")
    assert got["safe"] is False and "branch main, branch dev" in got["found"]
    policies["branch_policies"] = [{"name": "main", "type": "tag"}]
    assert github.merge_environment("o/r", "main")["safe"] is False
    answers[("GET", env_url)]["data"]["deployment_branch_policy"] = {
        "protected_branches": True, "custom_branch_policies": False,
    }  # fmt: skip
    assert "every protected branch" in github.merge_environment("o/r", "main")["found"]
    answers[("GET", env_url)]["data"]["deployment_branch_policy"] = None
    got = github.merge_environment("o/r", "main")
    assert got["safe"] is False and got["found"] == "every branch and tag may use it"
    # no environment: the merge stays the owner's (fallback C1), nothing to warn about
    answers[("GET", env_url)] = {"status": 404, "data": {}, "error": "Not Found"}
    got = github.merge_environment("o/r", "main")
    assert (got["ok"], got["exists"], got["safe"]) == (True, False, True)
    # a lookup that fails is not an answer
    answers[("GET", env_url)] = {"status": 403, "data": {}, "error": "Forbidden"}
    assert github.merge_environment("o/r", "main")["ok"] is False


def test_digest_warns_when_the_merge_key_reaches_beyond_the_default_branch(monkeypatch, capsys):
    """Choice 250 (F8): the digest says so when the environment lets another ref read the
    key, or when the key is a repository secret; a failed lookup says nothing."""
    unsafe = {"ok": True, "safe": False, "found": "every branch and tag may use it",
              "branch": "main"}  # fmt: skip
    notice = digest_mod.merge_key_notice(unsafe, False)
    assert "merge App's key is not kept to `main`** (every branch and tag" in notice
    both = digest_mod.merge_key_notice({**unsafe, "safe": True}, True)
    assert digest_mod.KEY_IN_REPOSITORY in both
    assert digest_mod.merge_key_notice({**unsafe, "safe": True}, False) == ""
    assert digest_mod.merge_key_notice({"ok": False, "reason": "403"}, False) == ""
    md = digest_mod.render_digest(QUEUE, "2026-10-22T06:00:00Z", merge_key=notice)
    assert md.index("merge App's key") < md.index("## Waiting")
    # main reads the environment for the default branch and the job's own flag
    monkeypatch.setattr(digest_mod, "list_queue_prs", lambda repo: (list(QUEUE), ""))
    monkeypatch.setattr(
        digest_mod.github, "default_branch_protection",
        lambda repo, cwd=None: {"ok": True, "branch": "main", "protected": True},
    )  # fmt: skip
    asked = []

    def environment(repo, branch):
        asked.append((repo, branch))
        return {"ok": True, "exists": True, "safe": True, "found": "only main may use it"}

    monkeypatch.setattr(digest_mod.github, "merge_environment", environment)
    monkeypatch.setenv(digest_mod.KEY_IN_REPOSITORY_ENV, "true")
    assert digest_mod.main(["--repo", "o/r", "--dry-run"]) == 0
    out = capsys.readouterr().out
    assert asked == [("o/r", "main")]
    assert digest_mod.KEY_IN_REPOSITORY in out and "not kept to `main`" in out
    monkeypatch.setenv(digest_mod.KEY_IN_REPOSITORY_ENV, "false")
    assert digest_mod.main(["--repo", "o/r", "--dry-run"]) == 0
    assert "merge App's key" not in capsys.readouterr().out


def test_digest_main_reads_the_protection_and_renders_the_notice(monkeypatch, capsys):
    """``main`` asks GitHub once (never with ``--input``) and hands the answer to the
    renderer; ``--dry-run`` prints the notice at the top."""
    monkeypatch.setattr(digest_mod, "list_queue_prs", lambda repo: (list(QUEUE), ""))
    asked = []

    def protection(repo, cwd=None):
        asked.append(repo)
        return {"route": "api", "ok": True, "branch": "main", "protected": False,
                "classic": True, "rules": ["pull_request"],
                "by": "classic branch protection; rules pull_request"}  # fmt: skip

    monkeypatch.setattr(digest_mod.github, "default_branch_protection", protection)
    assert digest_mod.main(["--repo", "o/r", "--dry-run"]) == 0
    out = capsys.readouterr().out
    assert asked == ["o/r"]
    assert (
        "does not restrict who merges** (found: classic branch protection; rules pull_request)"
        in out
    )
    assert out.index("does not restrict who merges") < out.index("## Waiting")
    # R21: a ruleset is desktop-only, and the notice links the project's own rulesets page
    assert "Desktop-only: the GitHub mobile app cannot change a ruleset" in out
    assert "open https://github.com/o/r/settings/rules in a desktop browser" in out


def test_digest_says_so_while_the_default_branch_is_unprotected():
    unprotected = {"ok": True, "branch": "main", "protected": False, "by": "nothing"}
    md = digest_mod.render_digest(QUEUE, "2026-09-25T06:00:00Z", protection=unprotected)
    assert md.index(
        "**The default branch `main` does not restrict who merges** (found: nothing)"
    ) < md.index("## Waiting")
    assert "Settings → Rules → Rulesets" in md and "decision 4" in md.lower()
    assert "Restrict updates" in md and "bypass: repository admin" in md
    # R21: without the repository the notice still says desktop-only, with no broken link
    assert "Desktop-only" in md and digest_mod.NO_LINK in md and "{" not in md
    md = digest_mod.render_digest([], "2026-09-25T06:00:00Z", protection=unprotected)
    assert "does not restrict who merges" in md and digest_mod.NOTHING_WAITING in md
    protected = {"ok": True, "branch": "main", "protected": True, "by": "ruleset: restrict updates"}
    assert "restrict who merges" not in digest_mod.render_digest(
        QUEUE, "2026-09-25T06:00:00Z", protection=protected
    )
    # a lookup that failed says nothing rather than something wrong
    failed = {"route": "none", "ok": False, "reason": "no route"}
    assert "restrict who merges" not in digest_mod.render_digest(
        QUEUE, "2026-09-25T06:00:00Z", protection=failed
    )
    assert digest_mod.unprotected_notice(None) == ""


def test_counters_leave_out_a_change_abandoned_on_its_remote_branches(project, tmp_path):
    """The sample's rehearsal 0005: the incident PR merged (the folder on main at phase f),
    then its design PR closed; abandon wrote the marker on ``sdlc/0005/design`` only (decision 25),
    and the digest counted it as an incident merged until 0.2.26 (1.0.0 readiness review,
    group A; ``detect/cli.py open_incidents`` already read the markers)."""
    from pr import counters

    root, _change = project
    second, st2 = status_mod.new_change(root, "Second", entry_route="incident", change_type="fix")
    st2.set_phase("maintain")
    status_mod.write_status(second, st2)
    git(root, "add", "-A")
    git(root, "commit", "-q", "-m", "the incident PR merged")
    bare = tmp_path / "remote.git"
    git(tmp_path, "init", "-q", "--bare", "-b", "main", str(bare))
    git(root, "remote", "add", "origin", str(bare))
    git(root, "push", "-q", "-u", "origin", "main")
    assert counters.collect(root)["incidents_merged"] == 1
    git(root, "checkout", "-q", "-b", "sdlc/0002/design")
    st2 = status_mod.read_status(second)
    st2.abandon("closed: the design PR")
    status_mod.write_status(second, st2)
    git(root, "commit", "-q", "-am", "abandon(0002)")
    git(root, "push", "-q", "-u", "origin", "sdlc/0002/design")
    git(root, "checkout", "-q", "main")
    assert not status_mod.read_status(second).abandoned  # main never learns of it
    counts = counters.collect(root)
    assert counts["incidents_merged"] == 0 and counts["abandoned"] == 1
    assert "| Incidents merged (fix now) / shipped | 0 / 0 |" in counters.render(counts)


def test_log_state_names_a_log_the_session_left_to_the_runner(tmp_path):
    """Item 3b (0.3.2): a marked log reads "deferred to the runner" in the PR body during the
    window before the runner's step, even when the command's own text says "exit 0" (the
    review of the 0.3.2 diff, finding 5)."""
    from gate import artifacts as art

    path = tmp_path / "test.log"
    art.write_evidence_log(
        path,
        art.render_deferred_header("pytest -x || exit 0", "2026-10-03T12:00:00Z"),
        art.EVIDENCE_DEFERRED_BODY,
    )
    assert desc.log_state(path) == "deferred to the runner"
    art.write_evidence_log(
        path, art.render_evidence_header("pytest -x || exit 0", 0, 1.0, "2026-10-03T12:00:00Z"), ""
    )
    assert desc.log_state(path) == "green"


def test_a_linked_evidence_file_is_never_quoted_in_the_body(project, tmp_path):
    """R59, the plugin security review of 2026-10-19, I2: a session links
    ``evidence/claude-md-proposals.md`` to a file it may not read (``.env``); the runner,
    which builds the body outside the sandbox, must not quote the target."""
    root, change = project
    gate_json(change, "deploy", "wait", c.ready_label("deploy"))
    secret = root / ".env"
    secret.write_text("FAKE_SECRET=marker-r59-i2\n", encoding="utf-8")
    link = change / art.EVIDENCE_DIR / desc.CLAUDE_MD_PROPOSALS
    link.parent.mkdir(parents=True, exist_ok=True)
    try:
        os.symlink(secret, link)
    except (OSError, NotImplementedError):
        pytest.skip("symbolic links are not permitted here")
    body = desc.build_description(root, "0001", "deploy")
    assert "marker-r59-i2" not in body
    assert "## Proposed CLAUDE.md lines" not in body
