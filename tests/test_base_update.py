"""Layer-1 tests of R51's gap G1 (``ci/base_update.py``) and check 12 (``gitops.push``): a build
branch behind the default branch is merged up to date and re-checked by the runner before
gate (e) is offered, and a push that found its branch moved merges the remote head (never a
rebase or a force) and pushes once more."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest
from ci import base_update
from ci import run_phase as rp

from state import gitops

PY = sys.executable.replace("\\", "/")


def git(cwd: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=cwd, capture_output=True, text=True, check=True, encoding="utf-8"
    ).stdout.strip()


def write(root: Path, name: str, text: str, message: str) -> str:
    (root / name).write_text(text, encoding="utf-8")
    git(root, "add", name)
    git(root, "commit", "-q", "-m", message)
    return git(root, "rev-parse", "HEAD")


def clone(tmp_path: Path, bare: Path, name: str, branch: str = "main") -> Path:
    work = tmp_path / name
    git(tmp_path, "clone", "-q", "-b", branch, str(bare), str(work))
    git(work, "config", "user.email", "owner@example.com")
    git(work, "config", "user.name", "Owner")
    return work


@pytest.fixture
def remote(tmp_path):
    """A bare remote: main with app.txt, and sdlc/0001/c one commit ahead of it."""
    seed = tmp_path / "seed"
    seed.mkdir()
    git(seed, "init", "-q", "-b", "main")
    git(seed, "config", "user.email", "owner@example.com")
    git(seed, "config", "user.name", "Owner")
    write(seed, "app.txt", "one\n", "seed")
    git(seed, "checkout", "-q", "-b", "sdlc/0001/c")
    write(seed, "feature.txt", "feature\n", "build")
    git(seed, "checkout", "-q", "main")  # the remote's HEAD is its default branch
    bare = tmp_path / "origin.git"
    git(tmp_path, "clone", "-q", "--bare", str(seed), str(bare))
    return bare


# --- check 12: a rejected push -----------------------------------------------------------------
def test_a_push_onto_a_moved_branch_merges_the_remote_head_and_pushes_again(remote, tmp_path):
    run = clone(tmp_path, remote, "run", "sdlc/0001/c")
    owner = clone(tmp_path, remote, "owner", "sdlc/0001/c")
    theirs = write(owner, "owner.txt", "by hand\n", "the owner's commit")
    git(owner, "push", "-q", "origin", "sdlc/0001/c")
    ours = write(run, "record.txt", "run record\n", "run record")
    merged = gitops.push(run, "sdlc/0001/c")
    assert merged == git(run, "rev-parse", "HEAD")
    assert git(run, "rev-parse", f"{merged}^1") == ours  # a merge commit: both kept
    assert git(run, "rev-parse", f"{merged}^2") == theirs
    assert git(remote, "rev-parse", "refs/heads/sdlc/0001/c") == merged
    assert "the branch moved while this run worked" in git(run, "log", "-1", "--format=%s")


def test_a_push_that_goes_through_reports_no_merge(remote, tmp_path):
    run = clone(tmp_path, remote, "run", "sdlc/0001/c")
    write(run, "record.txt", "run record\n", "run record")
    assert gitops.push(run, "sdlc/0001/c") is None


def test_a_moved_branch_that_does_not_merge_is_an_error_and_the_merge_is_aborted(remote, tmp_path):
    run = clone(tmp_path, remote, "run", "sdlc/0001/c")
    owner = clone(tmp_path, remote, "owner", "sdlc/0001/c")
    write(owner, "feature.txt", "the owner's line\n", "conflicting edit")
    git(owner, "push", "-q", "origin", "sdlc/0001/c")
    ours = write(run, "feature.txt", "the run's line\n", "run edit")
    with pytest.raises(gitops.GitError, match="does not merge"):
        gitops.push(run, "sdlc/0001/c")
    assert git(run, "rev-parse", "HEAD") == ours
    assert git(run, "status", "--porcelain") == ""


def test_a_push_refused_for_another_reason_is_not_merged(remote, tmp_path):
    run = clone(tmp_path, remote, "run", "sdlc/0001/c")
    git(run, "remote", "set-url", "origin", str(tmp_path / "gone.git"))
    with pytest.raises(gitops.GitError, match="failed"):
        gitops.push(run, "sdlc/0001/c")


def test_remote_merged_reads_the_commit_phase_output():
    assert base_update.remote_merged({"output": {"remote_merged": "abc"}}) == "abc"
    assert base_update.remote_merged({"output": {"remote_merged": None}}) is None
    assert base_update.remote_merged({"ok": False}) is None
    assert base_update.remote_merged(None) is None


# --- gap G1: the default branch merged in before gate (e) is offered -----------------------------
def targets(test_exit: int = 0) -> dict:
    ok = f'"{PY}" -c "pass"'
    test = f'"{PY}" -c "import sys; sys.exit({test_exit})"'
    return {"commands": {"build": ok, "test": test, "lint": ok}}


def moved_main(remote: Path, tmp_path: Path, name: str = "app.txt", text: str = "two\n") -> str:
    other = clone(tmp_path, remote, "other")
    sha = write(other, name, text, "another change merged")
    git(other, "push", "-q", "origin", "main")
    return sha


def update(run: Path, config: dict) -> dict:
    return base_update.update_before_offer(
        run, config, {}, rp.merge_default_branch, "sdlc/0001/c", "0001", "review"
    )


def test_a_branch_behind_the_default_branch_is_merged_and_rechecked_green(remote, tmp_path):
    run = clone(tmp_path, remote, "run", "sdlc/0001/c")
    tip = moved_main(remote, tmp_path)
    git(run, "fetch", "-q", "origin")
    out = update(run, targets())
    assert out["ok"] and out["recheck"] == "green"
    assert git(run, "rev-parse", "HEAD") == out["merged"]
    assert git(run, "merge-base", "--is-ancestor", tip, "HEAD") == ""
    assert "merged before gate (e) is offered (R51)" in git(run, "log", "-1", "--format=%s")


def test_a_branch_already_up_to_date_is_left_alone(remote, tmp_path):
    run = clone(tmp_path, remote, "run", "sdlc/0001/c")
    head = git(run, "rev-parse", "HEAD")
    out = update(run, targets(1))  # red targets are not run: nothing changed
    assert out["ok"] and out["merged"] is None and "recheck" not in out
    assert git(run, "rev-parse", "HEAD") == head


def test_a_red_merged_tree_parks_with_the_targets_named(remote, tmp_path):
    run = clone(tmp_path, remote, "run", "sdlc/0001/c")
    moved_main(remote, tmp_path)
    git(run, "fetch", "-q", "origin")
    out = update(run, targets(1))
    assert not out["ok"] and out["recheck"] == ["test (exit 1)"]
    assert out["reason"].startswith("base_update: the default branch merged into sdlc/0001/c")
    assert "test (exit 1)" in out["reason"]
    assert "Fix the red target on sdlc/0001/c" in out["need"]


def test_a_default_branch_that_does_not_merge_parks_with_the_files(remote, tmp_path):
    run = clone(tmp_path, remote, "run", "sdlc/0001/c")
    write(run, "app.txt", "the build's line\n", "build edits app")
    moved_main(remote, tmp_path, text="main's line\n")
    git(run, "fetch", "-q", "origin")
    head = git(run, "rev-parse", "HEAD")
    out = update(run, targets())
    assert not out["ok"] and out["conflicts"] == ["app.txt"]
    assert out["reason"] == (
        "base_update: the default branch does not merge into sdlc/0001/c: app.txt"
    )
    assert "dispatch SDLC deploy" in out["need"] and "change id 0001" in out["need"]
    assert git(run, "rev-parse", "HEAD") == head and git(run, "status", "--porcelain") == ""


def test_the_recheck_has_no_targets_to_run_without_commands(tmp_path):
    assert base_update.recheck(tmp_path, {}, {}) is None
    assert base_update.judged(tmp_path, {}, {}, "x", "b") == {"ok": True, "recheck": "no targets"}


def test_the_merge_after_a_session_runs_no_planted_hook_and_holds_no_credential(
    remote, tmp_path, monkeypatch
):
    """The independent review of the R51 PR, finding 3: on a runner the (e) step's merge
    follows the REVIEW.md session in the same checkout; a hook planted in ``.git/hooks``
    must not run, and the merge's environment carries none of the job's credentials."""
    run = clone(tmp_path, remote, "run", "sdlc/0001/c")
    moved_main(remote, tmp_path)
    git(run, "fetch", "-q", "origin")
    witness = tmp_path / "hook-ran"
    hook = run / ".git" / "hooks" / "post-merge"
    hook.write_text(f'#!/bin/sh\necho "$ANTHROPIC_API_KEY" > "{witness.as_posix()}"\n', "utf-8")
    hook.chmod(0o755)
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-secret")
    out = rp.merge_default_branch(run)
    assert out["ok"] and out["merged"]
    assert not witness.exists()
    # by hand (no GITHUB_ACTIONS) the owner's own hooks run as before, still without the key
    monkeypatch.delenv("GITHUB_ACTIONS")
    git(run, "reset", "-q", "--hard", "HEAD~1")
    rp.merge_default_branch(run)
    if os.name == "posix":
        assert witness.read_text(encoding="utf-8").strip() == ""
