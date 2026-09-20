"""Layer-2 integration tests: the Python halves of /sdlc-init and /sdlc-plan against a temporary
copy of the fixture project with a bare remote. The model's work (brainstorm, writing
intent.md) is replaced by recorded text; the PR step is not exercised (needs GitHub)."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "sample-python-project"
INIT = ROOT / "plugin" / "init" / "sdlc_init.py"
CLI = ROOT / "plugin" / "state" / "cli.py"

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


def test_sdlc_plan_python_half_produces_intent_on_phase_branch(project):
    root, bare = project
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
    assert alloc["id"] == "0001" and alloc["dir"] == "changes/0001-percent-helper"
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
