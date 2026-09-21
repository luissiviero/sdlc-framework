"""Layer-2 integration tests: the Python halves of /sdlc-init, /sdlc-plan and /sdlc-design
against a temporary copy of the fixture project with a bare remote. The model's work
(brainstorm, writing intent.md, spec.md and plan.md) is replaced by recorded text; the PR step
is not exercised (needs GitHub), and gate (b) is reached through the gate CLI."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from state import status as status_mod
from state import yamlish

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "sample-python-project"
INIT = ROOT / "plugin" / "init" / "sdlc_init.py"
CLI = ROOT / "plugin" / "state" / "cli.py"
GATE_CLI = ROOT / "plugin" / "gate" / "cli.py"

RECORDED_INTENT = """# Intent: percent helper
Author: owner (developer). Status: proposed. Change id: 0001. Entry route: idea.

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

# what the design pass writes under the spec header the CLI renders (skill spec-template)
RECORDED_SPEC_BODY = """
## Requirements
- percent(part, whole) returns part / whole * 100 rounded to one decimal.
- whole == 0 raises ValueError with a message naming the argument.

## Design
A pure function in sample_pkg/percent.py, exported from the package; nothing else changes.

## Open questions from intent
none

## Flagged concerns
- [x] Rounding half-even vs half-up: decided half-up via round(), per the coding standards.

## Acceptance
tests/test_percent.py passes; lint and build stay green.
"""

RECORDED_PLAN = """# Plan: percent helper (from intent.md and spec.md)

## Files that change
- `sample_pkg/percent.py` — new: percent(part, whole)
- `sample_pkg/__init__.py` — export percent
- `tests/test_percent.py` — new: three cases

## Order of work
1. Add the function and its test.
2. Export it.

## Risks
Rounding only.

## Options not taken
The decimal module: overkill here.

## Proof
tests/test_percent.py::test_percent_rounds
"""


def git(cwd: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=cwd, capture_output=True, text=True, check=True
    ).stdout


def py(*args: str, cwd: Path, env: dict | None = None) -> dict:
    proc = subprocess.run(
        [sys.executable, *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        env=env or os.environ.copy(),
    )
    assert proc.returncode == 0, proc.stderr
    return json.loads(proc.stdout)


def py_raw(*args: str, cwd: Path) -> subprocess.CompletedProcess:
    """Like ``py`` but for the gate CLI, whose exit code is the answer (0/3/4)."""
    return subprocess.run(
        [sys.executable, *args], cwd=cwd, capture_output=True, text=True, env=os.environ.copy()
    )


def write_verdict(change_dir: Path, phase: str, head: str) -> None:
    """Stand in for the adversarial-reviewer agent (step 17): it writes this file."""
    data = {
        "schema_version": 1,
        "phase": phase,
        "head": head,
        "verdict": "continue",
        "reasons": [],
        "classification": "routine",
        "classification_reasons": [],
        "at": "2026-09-21T10:00:00Z",
    }
    path = change_dir / "evidence" / f"adversarial-review-{phase}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data), encoding="utf-8", newline="\n")


@pytest.fixture
def project(tmp_path):
    root = tmp_path / "proj"
    shutil.copytree(FIXTURE, root)
    bare = tmp_path / "remote.git"
    git(tmp_path, "init", "-q", "--bare", "-b", "main", str(bare))
    git(root, "init", "-q", "-b", "main")
    git(root, "config", "user.email", "owner@example.com")
    git(root, "config", "user.name", "Owner")
    git(root, "add", ".")
    git(root, "commit", "-q", "-m", "fixture")
    git(root, "remote", "add", "origin", str(bare))
    git(root, "push", "-q", "-u", "origin", "main")
    return root, bare


def test_feedback_loop_targets_exit_nonzero_on_failure(project):
    root, _ = project
    ok = subprocess.run(
        [sys.executable, "-m", "pytest", "-q"], cwd=root, capture_output=True, text=True
    )
    assert ok.returncode == 0, ok.stdout
    env = {**os.environ, "SAMPLE_FAIL": "1"}
    bad = subprocess.run(
        [sys.executable, "-m", "pytest", "-q"], cwd=root, capture_output=True, text=True, env=env
    )
    assert bad.returncode != 0 and "SAMPLE_FAIL=1" in bad.stdout


def test_sdlc_init_then_first_pr_branch(project):
    root, bare = project
    report = py(
        str(INIT), "--root", str(root), "--profile", "standard", "--deploy-action", "none", cwd=root
    )
    assert report["change"]["branch"] == "sdlc/0000/a"
    paths = ["sdlc.yaml", ".claude/settings.json", "REVIEW.md", "CLAUDE.md", "changes"]
    out = py(
        str(CLI),
        "commit-phase",
        "--root",
        str(root),
        "--id",
        "0000",
        "--phase",
        "a",
        "--message",
        "sdlc-init: connect the SDLC framework",
        "--paths",
        *paths,
        "--start-point",
        "main",
        "--push",
        cwd=root,
    )
    assert out["branch"] == "sdlc/0000/a" and out["commit"] and out["pushed"] is True
    assert out["base"] == "main"
    assert "sdlc/0000/a" in git(bare, "branch", "--list", "sdlc/0000/a")
    tracked = git(root, "ls-tree", "-r", "--name-only", "sdlc/0000/a").split()
    for rel in [
        "sdlc.yaml",
        ".claude/settings.json",
        "REVIEW.md",
        "CLAUDE.md",
        "changes/0000-sdlc-init/intent.md",
        "changes/0000-sdlc-init/status.yaml",
        "changes/README.md",
    ]:
        assert rel in tracked, rel
    assert ".env" in tracked  # the fixture proves the deny rule; it is not our job to hide it
    # main is untouched: the framework's own installation goes through gate (a)
    assert "sdlc.yaml" not in git(root, "ls-tree", "-r", "--name-only", "main").split()


def run_plan_half(root: Path) -> tuple[dict, dict]:
    """The Python half of /sdlc-init (merged) and /sdlc-plan: change 0001 with its intent
    committed on sdlc/0001/a and pushed. Returns the two CLI reports."""
    py(str(INIT), "--root", str(root), cwd=root)
    git(root, "add", ".")
    git(root, "commit", "-q", "-m", "init (simulating the merged 0000 PR)")
    git(root, "push", "-q", "origin", "main")

    alloc = py(
        str(CLI),
        "new-change",
        "--root",
        str(root),
        "--title",
        "Percent helper",
        "--type",
        "feature",
        cwd=root,
    )
    # the model would write intent.md via the intent-template skill; here the recording stands in
    (root / alloc["dir"] / "intent.md").write_text(RECORDED_INTENT, encoding="utf-8")
    out = py(
        str(CLI),
        "commit-phase",
        "--root",
        str(root),
        "--id",
        "0001",
        "--phase",
        "a",
        "--message",
        "intent(0001): Percent helper",
        "--start-point",
        "main",
        "--push",
        cwd=root,
    )
    return alloc, out


def test_sdlc_plan_python_half_produces_intent_on_phase_branch(project):
    root, bare = project
    alloc, out = run_plan_half(root)
    assert alloc["id"] == "0001" and alloc["dir"] == "changes/0001-percent-helper"
    assert out["branch"] == "sdlc/0001/a" and out["pushed"]
    assert "sdlc/0001/a" in git(bare, "branch", "--list", "sdlc/0001/a")
    assert (
        "changes/0001-percent-helper/intent.md"
        in git(root, "ls-tree", "-r", "--name-only", "sdlc/0001/a").split()
    )
    shown = py(str(CLI), "show", "--root", str(root), "--id", "0001", cwd=root)
    assert shown["status"]["phase"] == "a" and shown["status"]["change_type"] == "feature"
    # re-running the same command is a no-op commit (idempotent)
    again = py(
        str(CLI),
        "commit-phase",
        "--root",
        str(root),
        "--id",
        "0001",
        "--phase",
        "a",
        "--message",
        "intent(0001): Percent helper",
        "--push",
        cwd=root,
    )
    assert again["commit"] is None


def test_sdlc_design_python_half_produces_spec_and_plan_and_gate_b_waits(project):
    root, bare = project
    alloc, _ = run_plan_half(root)
    change = root / alloc["dir"]
    # gate (a): the owner merges the intent PR
    git(root, "checkout", "-q", "main")
    git(root, "merge", "-q", "--no-edit", "sdlc/0001/a")
    git(root, "push", "-q", "origin", "main")

    # --- the design half, exactly as /sdlc-design runs it ---------------------------------
    git(root, "checkout", "-q", "-b", "sdlc/0001/b", "main")
    py(str(GATE_CLI), "start-run", "--root", str(root), "--id", "0001", "--phase", "b", cwd=root)
    header = py(str(GATE_CLI), "spec-header", "--root", str(root), "--id", "0001", cwd=root)
    pinned = yamlish.load_file(root / "sdlc.yaml")["plugin"]["version"]
    assert header["title"] == "percent helper"  # from intent.md, not the status.yaml title
    assert header["change_id"] == "0001" and header["plugin_version"] == pinned
    assert header["prompt_version"] == "v1" and header["overrides"] == []
    assert header["header"].startswith("# Spec: percent helper\nChange id: 0001. ")
    assert f"sdlc plugin {pinned}" in header["header"]
    # the model writes the spec body under the rendered header, and the plan.md after it
    (change / "spec.md").write_text(
        header["header"] + "\n" + RECORDED_SPEC_BODY, encoding="utf-8", newline="\n"
    )
    (change / "plan.md").write_text(RECORDED_PLAN, encoding="utf-8", newline="\n")
    out = py(
        str(CLI),
        "commit-phase",
        "--root",
        str(root),
        "--id",
        "0001",
        "--phase",
        "b",
        "--message",
        "design(0001): percent helper",
        "--push",
        cwd=root,
    )
    assert out["branch"] == "sdlc/0001/b" and out["pushed"] is True

    # --- gate (b): Standard waits for the owner -------------------------------------------
    write_verdict(change, "b", git(root, "rev-parse", "HEAD").strip())
    proc = py_raw(
        str(GATE_CLI), "check", "--root", str(root), "--id", "0001", "--phase", "b", cwd=root
    )
    assert proc.returncode == 3, proc.stdout + proc.stderr
    result = json.loads(proc.stdout)
    assert result["result"] == "wait" and result["label"] == "sdlc:b-ready"
    assert (
        result["what_i_need"] == "" and [c["name"] for c in result["checks"] if not c["ok"]] == []
    )
    assert (change / "evidence" / "gate-b.json").is_file()
    assert status_mod.read_status(change).gate.result == "passed"
    py(
        str(CLI),
        "commit-phase",
        "--root",
        str(root),
        "--id",
        "0001",
        "--phase",
        "b",
        "--message",
        "evidence(0001): gate (b)",
        "--push",
        cwd=root,
    )
    assert "sdlc/0001/b" in git(bare, "branch", "--list", "sdlc/0001/b")
    tracked = git(root, "ls-tree", "-r", "--name-only", "sdlc/0001/b").split()
    for rel in ("spec.md", "plan.md", "evidence/gate-b.json"):
        assert f"{alloc['dir']}/{rel}" in tracked, rel

    # --- 23.3: Lite passes gate (b) by the confidence gate instead of asking the owner -----
    st = status_mod.read_status(change)
    st.profile_override = "lite"
    status_mod.write_status(change, st)
    py(
        str(CLI),
        "commit-phase",
        "--root",
        str(root),
        "--id",
        "0001",
        "--phase",
        "b",
        "--message",
        "profile(0001): lite",
        cwd=root,
    )
    py(str(GATE_CLI), "start-run", "--root", str(root), "--id", "0001", "--phase", "b", cwd=root)
    write_verdict(change, "b", git(root, "rev-parse", "HEAD").strip())
    proc = py_raw(
        str(GATE_CLI), "check", "--root", str(root), "--id", "0001", "--phase", "b", cwd=root
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    result = json.loads(proc.stdout)
    assert result["result"] == "continue" and result["label"] is None
    assert result["profile"] == "lite" and result["human_gate"] is False


def test_labels_are_the_documented_set():
    out = json.loads(
        subprocess.run(
            [sys.executable, str(CLI), "labels"], capture_output=True, text=True, check=True
        ).stdout
    )
    assert out == [
        "sdlc:a-ready",
        "sdlc:b-ready",
        "sdlc:c-ready",
        "sdlc:d-ready",
        "sdlc:e-ready",
        "sdlc:f-ready",
        "sdlc:c-approved",
        "sdlc:d-approved",
        "sdlc:needs-human",
    ]
