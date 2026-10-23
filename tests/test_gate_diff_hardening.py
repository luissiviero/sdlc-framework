"""R59 and the git half of R44 (the plugin security review of 2026-10-19, I2, I3, I4, M3, M9
and M12): the gate and the runner read what the branch really changed, no evidence file is
read through a link, and the runner's git calls run no program the session configured."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import pytest
from ci import run_phase

from gate import artifacts as art
from gate import checks
from gate import diff as diffmod
from hooks import _common, test_file_lock
from state import gitops


def git(cwd: Path, *args: str, stdin: str | None = None) -> str:
    return subprocess.run(
        ["git", *args], cwd=cwd, capture_output=True, text=True, check=True,
        encoding="utf-8", input=stdin,
    ).stdout  # fmt: skip


def repo(tmp_path: Path, files: dict[str, str]) -> Path:
    root = tmp_path / "proj"
    root.mkdir()
    git(root, "init", "-q", "-b", "main")
    git(root, "config", "user.email", "owner@example.com")
    git(root, "config", "user.name", "Owner")
    for rel, text in files.items():
        (root / rel).parent.mkdir(parents=True, exist_ok=True)
        (root / rel).write_text(text, encoding="utf-8")
    git(root, "add", ".")
    git(root, "commit", "-q", "-m", "base")
    git(root, "checkout", "-q", "-b", "sdlc/0001/c")
    return root


def link_in_commit(root: Path, rel: str, target: str) -> None:
    """Turn ``rel`` into a symbolic link in the index and commit it: plumbing only, the way a
    session with ``Bash(git *)`` can, with no link on disk (works on Windows too)."""
    blob = git(root, "hash-object", "-w", "--stdin", stdin=target).strip()
    git(root, "update-index", "--add", "--cacheinfo", f"120000,{blob},{rel}")
    git(root, "commit", "-q", "-m", f"{rel} becomes a link")


GUARDED = {"CLAUDE.md": "# rules\n", "sdlc.yaml": "commands: {}\n", "app.py": "x = 1\n"}


# --- I3 and M9: one diff reader for every gate check and the runner's guard ----------------------
def test_a_rename_s_source_and_a_type_change_are_committed_changes(tmp_path):
    root = repo(tmp_path, GUARDED)
    base = git(root, "rev-parse", "HEAD").strip()
    git(root, "mv", "CLAUDE.md", "docs_CLAUDE.md")
    git(root, "commit", "-q", "-m", "rename")
    link_in_commit(root, "sdlc.yaml", "elsewhere.yaml")
    # the review's reproduction gave ['docs_CLAUDE.md'] only
    assert diffmod.committed_files(root, base) == ["CLAUDE.md", "docs_CLAUDE.md", "sdlc.yaml"]
    collected = diffmod.collect(root, "main")
    assert {"CLAUDE.md", "sdlc.yaml"} <= set(collected.files)
    assert {"CLAUDE.md", "docs_CLAUDE.md"} <= set(collected.commits[0].files)


def test_the_runner_s_guard_sees_a_renamed_guardrail_and_a_non_ascii_path(tmp_path):
    root = repo(tmp_path, {**GUARDED, ".claude/settings.json": "{}\n"})
    git(root, "mv", "CLAUDE.md", "notes.md")
    (root / ".claude" / "régua.json").write_text("{}\n", encoding="utf-8")
    git(root, "add", ".")
    git(root, "commit", "-q", "-m", "rename and add")
    files, merge_base = run_phase._committed_diff(root)
    assert merge_base
    assert ".claude/régua.json" in files  # unquoted: --name-only without -z quoted it (M9)
    hits = run_phase.guardrail_hits(files, {})
    assert "CLAUDE.md" in hits and ".claude/régua.json" in hits


def test_a_locked_test_turned_into_a_link_is_a_changed_test_file(tmp_path):
    root = repo(tmp_path, {"tests/test_x.py": "def test_x():\n    assert False\n"})
    lock = git(root, "rev-parse", "HEAD").strip()
    link_in_commit(root, "tests/test_x.py", "../weaker.py")
    assert diffmod.changed_paths(root, f"{lock}..HEAD") == ["tests/test_x.py"]


def test_the_fast_lane_guard_sees_a_rename_out_of_the_change_folder(tmp_path):
    root = repo(tmp_path, {"changes/0001-x/evidence/a.md": "a\n", "spec.md": "s\n"})
    sha = git(root, "rev-parse", "HEAD").strip()
    git(root, "mv", "spec.md", "changes/0001-x/evidence/spec.md")
    git(root, "commit", "-q", "-m", "move the spec into evidence")
    why = run_phase.fast_lane_after_gate(root, "changes/0001-x", sha, "HEAD")
    assert why and "spec.md" in why


# --- I2: no evidence file read through a link ---------------------------------------------------
def _symlink(target: Path, link: Path, *, directory: bool = False) -> None:
    try:
        os.symlink(target, link, target_is_directory=directory)
    except (OSError, NotImplementedError):
        pytest.skip("symbolic links are not permitted here")


def test_read_text_refuses_a_link_and_a_linked_folder(tmp_path):
    root = repo(tmp_path, {"changes/0001-x/intent.md": "i\n", ".env": "SECRET=1\n"})
    evidence = root / "changes" / "0001-x" / "evidence"
    evidence.mkdir()
    _symlink(root / ".env", evidence / "claude-md-proposals.md")
    assert art.read_text(evidence / "claude-md-proposals.md") is None
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    (elsewhere / "release-notes.md").write_text("SECRET=1\n", encoding="utf-8")
    other = root / "changes" / "0002-y"
    other.mkdir()
    _symlink(elsewhere, other / "evidence", directory=True)
    assert art.read_text(other / "evidence" / "release-notes.md") is None
    assert art.read_text(root / "changes" / "0001-x" / "intent.md") == "i\n"


def test_a_link_under_the_change_folder_is_a_gate_finding(tmp_path):
    root = repo(tmp_path, {"changes/0001-x/intent.md": "i\n"})
    assert checks.change_folder_links(root, "changes/0001-x", "HEAD") == []
    link_in_commit(root, "changes/0001-x/evidence/notes.md", "../../../.env")
    assert checks.change_folder_links(root, "changes/0001-x", "HEAD") == [
        "changes/0001-x/evidence/notes.md"
    ]


# --- I4: the runner's git calls run no program the session configured ---------------------------
def _plant_filter(root: Path, marker: Path) -> None:
    program = f"python -c \"open(r'{marker}', 'w').write('ran')\" && cat"
    git(root, "config", "filter.x.clean", program)
    (root / ".gitattributes").write_text("*.txt filter=x\n", encoding="utf-8")


def test_a_planted_filter_stops_the_runner_s_git_before_it_runs(tmp_path, monkeypatch):
    root = repo(tmp_path, GUARDED)
    marker = tmp_path / "ran"
    _plant_filter(root, marker)
    (root / "a.txt").write_text("text\n", encoding="utf-8")
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    with pytest.raises(gitops.GitError, match="filter.x.clean"):
        gitops.commit_files(root, ["a.txt"], "record")
    with pytest.raises(diffmod.GitUnavailable, match="filter.x.clean"):
        diffmod.changed_paths(root, "HEAD")
    assert not marker.exists()


def test_by_hand_the_owner_s_own_config_is_not_judged(tmp_path, monkeypatch):
    root = repo(tmp_path, GUARDED)
    git(root, "config", "alias.st", "status")
    monkeypatch.delenv("GITHUB_ACTIONS", raising=False)
    assert gitops.run(root, "rev-parse", "HEAD").strip()


def test_a_redirect_key_stays_app_token_s_to_judge(tmp_path, monkeypatch):
    """A proxy is not a program: R49's fallback to the workflow token stays in charge."""
    root = repo(tmp_path, GUARDED)
    git(root, "config", "http.https://github.com/o/r.proxy", "http://127.0.0.1:9")
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    assert gitops.run(root, "rev-parse", "HEAD").strip()


def test_the_runner_args_turn_off_signing_and_the_external_diff(monkeypatch):
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    args = gitops.runner_args()
    for option in ("commit.gpgSign=false", "tag.gpgSign=false", "diff.external="):
        assert option in args
    assert f"core.attributesFile={os.devnull}" in args


# --- M3: the test-file lock survives a branch switch and an edited status.yaml ------------------
LOCKED = "change_type: fix\ntests_locked: true\nphase: c\n"


def _locked_repo(tmp_path: Path) -> Path:
    root = repo(
        tmp_path,
        {
            "sdlc.yaml": "test_paths:\n  - tests/**\n",
            "changes/0001-fix/status.yaml": LOCKED,
            "tests/test_x.py": "def test_x():\n    pass\n",
        },
    )
    return root


def _edit(root: Path, rel: str) -> dict:
    return {
        "tool_name": "Edit",
        "tool_input": {"file_path": str(root / rel)},
        "cwd": str(root),
    }


def test_the_lock_holds_on_a_detached_head_and_a_branch_of_the_session_s_own(tmp_path):
    root = _locked_repo(tmp_path)
    env = {"CLAUDE_PROJECT_DIR": str(root)}
    assert test_file_lock.decide(_edit(root, "tests/test_x.py"), [], env).block
    git(root, "checkout", "-q", "--detach")
    assert test_file_lock.decide(_edit(root, "tests/test_x.py"), [], env).block
    git(root, "checkout", "-q", "-b", "elsewhere")
    assert test_file_lock.decide(_edit(root, "tests/test_x.py"), [], env).block


def test_an_edited_working_copy_of_status_yaml_does_not_lift_the_lock(tmp_path):
    root = _locked_repo(tmp_path)
    (root / "changes/0001-fix/status.yaml").write_text(
        LOCKED.replace("tests_locked: true", "tests_locked: false"), encoding="utf-8"
    )
    env = {"CLAUDE_PROJECT_DIR": str(root)}
    assert test_file_lock.decide(_edit(root, "tests/test_x.py"), [], env).block


# --- M12: a committed hook log keeps no literal secret ------------------------------------------
def test_the_hook_log_redacts_a_secret_in_the_command(tmp_path):
    log = tmp_path / "log.jsonl"
    key = "sk-ant-" + "a1" * 20
    _common.log_decision(
        "production_gate", "block", "fail closed", {"tool_name": "Bash"},
        {"SDLC_HOOK_LOG": str(log)}, command=f"deploy --key {key}",
    )  # fmt: skip
    record = json.loads(log.read_text(encoding="utf-8"))
    assert key not in record["command"] and "[redacted]" in record["command"]


# --- the fresh-context review of 1.0.26 ----------------------------------------------------------
def test_a_replace_ref_does_not_hide_a_commit_from_the_runner_s_diff(tmp_path, monkeypatch):
    """A session writes ``refs/replace/<head>`` pointing at a commit with the base's tree:
    without ``--no-replace-objects`` the diff printed nothing."""
    root = repo(tmp_path, GUARDED)
    base = git(root, "rev-parse", "HEAD").strip()
    (root / "CLAUDE.md").write_text("# changed\n", encoding="utf-8")
    git(root, "commit", "-q", "-am", "edit a guardrail")
    head = git(root, "rev-parse", "HEAD").strip()
    tree = git(root, "rev-parse", f"{base}^{{tree}}").strip()
    fake = git(root, "commit-tree", tree, "-p", base, "-m", "looks clean").strip()
    git(root, "replace", head, fake)
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    assert diffmod.committed_files(root, base) == ["CLAUDE.md"]


def test_git_lfs_s_own_filter_is_not_refused_but_another_is(tmp_path, monkeypatch):
    root = repo(tmp_path, GUARDED)
    git(root, "config", "filter.lfs.clean", "git-lfs clean -- %f")
    git(root, "config", "filter.lfs.smudge", "git-lfs smudge -- %f")
    git(root, "config", "filter.lfs.process", "git-lfs filter-process")
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    assert gitops.run(root, "rev-parse", "HEAD").strip()
    git(root, "config", "filter.lfs.clean", "sh -c planted")
    with pytest.raises(gitops.GitError, match="filter.lfs.clean"):
        gitops.run(root, "status")


def test_grafts_and_the_ext_transport_are_refused(tmp_path, monkeypatch):
    root = repo(tmp_path, GUARDED)
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    git(root, "config", "protocol.ext.allow", "always")
    with pytest.raises(gitops.GitError, match="protocol.ext.allow"):
        gitops.run(root, "status")
    git(root, "config", "--unset", "protocol.ext.allow")
    (root / ".git" / "info").mkdir(exist_ok=True)
    (root / ".git" / "info" / "grafts").write_text("", encoding="utf-8")
    with pytest.raises(gitops.GitError, match="grafts"):
        gitops.run(root, "status")


def test_the_lock_holds_after_a_commit_on_the_session_s_own_branch(tmp_path, monkeypatch):
    """``branch --contains HEAD`` stops naming the locked branch once the session commits
    elsewhere; on a runner ``for-each-ref --merged HEAD`` still finds it."""
    root = _locked_repo(tmp_path)
    git(root, "checkout", "-q", "-b", "mine")
    (root / "changes/0001-fix/status.yaml").write_text(
        LOCKED.replace("tests_locked: true", "tests_locked: false"), encoding="utf-8"
    )
    git(root, "commit", "-q", "-am", "unlock it myself")
    env = {"CLAUDE_PROJECT_DIR": str(root)}
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    assert test_file_lock.decide(_edit(root, "tests/test_x.py"), [], env).block


def test_the_runner_s_restore_sees_a_locked_test_moved_away(tmp_path):
    root = repo(tmp_path, {"sdlc.yaml": "test_paths:\n  - tests/**\n", "tests/test_x.py": "x\n"})
    pre_head = git(root, "rev-parse", "HEAD").strip()
    (root / "src").mkdir()
    git(root, "mv", "tests/test_x.py", "src/x.py")
    git(root, "commit", "-q", "-m", "move the test")
    config = {"test_paths": ["tests/**"]}
    assert run_phase._test_files_changed_since(root, pre_head, config) == ["tests/test_x.py"]
