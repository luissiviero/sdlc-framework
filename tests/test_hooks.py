"""Layer-1 tests for the four hooks: sample tool inputs in, decisions out, plus one
end-to-end run of each script over stdin to prove the exit code and JSON contract."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from hooks import _common, format_on_edit, plan_sync, protected_paths, secrets_check

HOOKS_DIR = Path(__file__).resolve().parents[1] / "plugin" / "hooks"
PLUGIN_ROOT = HOOKS_DIR.parent


def pre(tool: str, **tool_input):
    return {"hook_event_name": "PreToolUse", "tool_name": tool, "tool_input": tool_input}


# --- _common ------------------------------------------------------------------------------
def test_glob_matching_gitignore_style():
    m = _common.matches
    assert m(".claude/**", ".claude/settings.json")
    assert m(".claude/**", ".claude/hooks/x.py")
    assert not m(".claude/**", "src/.claude-ish/x")
    assert m("CLAUDE.md", "CLAUDE.md")
    assert m("CLAUDE.md", "packages/api/CLAUDE.md")  # unanchored: any directory
    assert not m("CLAUDE.md", "CLAUDE.md.bak")
    assert m("src/gen/**", "src/gen/a/b.py")
    assert m("*.lock", "poetry.lock") and m("*.lock", "sub/poetry.lock")
    assert m("migrations/", "migrations/0001_init.py")


def test_norm_handles_windows_paths():
    assert _common.norm("C:\\project\\src\\index.ts") == "c:/project/src/index.ts"
    assert _common.rel_to("C:\\project", "C:\\project\\CLAUDE.md") == "CLAUDE.md"
    assert _common.rel_to("/home/u/proj", "/home/u/other/x") is None


# --- protected paths -----------------------------------------------------------------------
@pytest.fixture
def project(tmp_path):
    (tmp_path / "sdlc.yaml").write_text(
        "profile: standard\nprotected_paths:\n  - src/gen/**\n  - migrations/\n", encoding="utf-8"
    )
    return tmp_path


def _env(project):
    return {"CLAUDE_PROJECT_DIR": str(project)}


@pytest.mark.parametrize(
    "rel",
    [
        ".claude/settings.json",
        ".claude/hooks/x.py",
        "CLAUDE.md",
        "REVIEW.md",
        "sdlc.yaml",
        "src/gen/model.py",
        "migrations/0002.py",
        "api/CLAUDE.md",
    ],
)
def test_protected_paths_denied(project, rel):
    payload = pre("Edit", file_path=str(project / rel), old_string="a", new_string="b")
    d = protected_paths.decide(payload, [], env=_env(project))
    assert d.block, rel
    assert "Protected path" in d.reason


@pytest.mark.parametrize(
    "rel", ["src/app.py", "README.md", "changes/0001-x/plan.md", "tests/test_x.py"]
)
def test_unprotected_paths_allowed(project, rel):
    payload = pre("Write", file_path=str(project / rel), content="x")
    assert not protected_paths.decide(payload, [], env=_env(project)).block


def test_windows_style_path_is_still_caught(project):
    win_root = "C:\\work\\proj"
    payload = {
        "tool_name": "Write",
        "tool_input": {"file_path": "C:\\work\\proj\\.claude\\settings.json", "content": ""},
        "cwd": win_root,
    }
    d = protected_paths.decide(payload, [], env={"CLAUDE_PROJECT_DIR": win_root})
    assert d.block


def test_plugin_root_is_self_protected(project):
    hook_file = PLUGIN_ROOT / "hooks" / "protected_paths.py"
    payload = pre("Edit", file_path=str(hook_file), old_string="a", new_string="b")
    d = protected_paths.decide(payload, ["--plugin-root", str(PLUGIN_ROOT)], env=_env(project))
    assert d.block and "plugin" in d.reason


def test_non_file_tools_ignored(project):
    assert not protected_paths.decide(pre("Bash", command="ls"), [], env=_env(project)).block


def test_protected_paths_end_to_end_blocks_settings_json(project):
    """Definition of done: the hook demonstrably blocks an edit to .claude/settings.json."""
    payload = pre(
        "Edit",
        file_path=str(project / ".claude" / "settings.json"),
        old_string="{",
        new_string="{ }",
    )
    proc = subprocess.run(
        [sys.executable, str(HOOKS_DIR / "protected_paths.py"), "--plugin-root", str(PLUGIN_ROOT)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        env={**os.environ, "CLAUDE_PROJECT_DIR": str(project)},
    )
    assert proc.returncode == 2
    out = json.loads(proc.stdout)
    assert out["hookSpecificOutput"]["permissionDecision"] == "deny"
    assert ".claude/settings.json" in out["hookSpecificOutput"]["permissionDecisionReason"]
    assert "Protected path" in proc.stderr


def test_protected_paths_fails_closed_on_garbage_input():
    proc = subprocess.run(
        [sys.executable, str(HOOKS_DIR / "protected_paths.py")],
        input="not json",
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 2
    assert "failed closed" in proc.stderr


# --- secrets -------------------------------------------------------------------------------
@pytest.mark.parametrize(
    "text",
    [
        "AWS_KEY = 'AKIAIOSFODNN7EXAMPLE'".replace("EXAMPLE", "REALKEY"),
        "-----BEGIN RSA PRIVATE KEY-----\nMIIE...",
        "token = 'ghp_" + "a" * 36 + "'",
        "key = 'sk-ant-" + "b" * 24 + "'",
        'password = "hunter2hunter2"',
        "api_key: 'Zm9vYmFyYmF6cXV4'",
    ],
)
def test_secrets_denied(text):
    d = secrets_check.decide(pre("Write", file_path="/p/config.py", content=text), [])
    assert d.block and "Possible secret" in d.reason


@pytest.mark.parametrize(
    "text",
    [
        "password = os.environ['PASSWORD']",
        'api_key = "<your-api-key>"',
        'secret = "${SECRET}"',
        'password = "example-password"',
        "token = 'ghp_" + "a" * 36 + "'  # sdlc: allow-secret",
        "def test_password_field(): ...",
    ],
)
def test_secrets_allowed(text):
    assert not secrets_check.decide(pre("Write", file_path="/p/x.py", content=text), []).block


def test_secrets_in_edit_new_string_and_multiedit():
    d = secrets_check.decide(
        pre("Edit", file_path="/p/x", old_string="", new_string="password = 'abcdefghij'"), []
    )
    assert d.block
    d = secrets_check.decide(
        pre(
            "MultiEdit",
            file_path="/p/x",
            edits=[
                {"old_string": "", "new_string": "ok"},
                {"old_string": "", "new_string": "AKIA" + "Q" * 16},
            ],
        ),
        [],
    )
    assert d.block


def test_secrets_end_to_end():
    payload = pre("Write", file_path="/p/x.py", content="password = 'abcdefghij'")
    proc = subprocess.run(
        [sys.executable, str(HOOKS_DIR / "secrets_check.py")],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
    )
    assert (
        proc.returncode == 2
        and json.loads(proc.stdout)["hookSpecificOutput"]["permissionDecision"] == "deny"
    )


# --- formatter -----------------------------------------------------------------------------
def test_format_on_edit_formats_and_fixes(tmp_path):
    pytest.importorskip("ruff")
    f = tmp_path / "m.py"
    f.write_text("import os\nx=1\n", encoding="utf-8")  # unused import (fixable), spacing
    payload = {
        "hook_event_name": "PostToolUse",
        "tool_name": "Write",
        "tool_input": {"file_path": str(f), "content": ""},
        "cwd": str(tmp_path),
    }
    d = format_on_edit.decide(payload, [], env={"CLAUDE_PROJECT_DIR": str(tmp_path)})
    assert not d.block
    assert f.read_text(encoding="utf-8") == "x = 1\n"


def test_format_on_edit_reports_unfixable(tmp_path):
    pytest.importorskip("ruff")
    f = tmp_path / "m.py"
    f.write_text("def f():\n    return undefined_name\n", encoding="utf-8")  # F821, not fixable
    payload = {
        "hook_event_name": "PostToolUse",
        "tool_name": "Edit",
        "tool_input": {"file_path": str(f)},
        "cwd": str(tmp_path),
    }
    d = format_on_edit.decide(payload, [], env={"CLAUDE_PROJECT_DIR": str(tmp_path)})
    assert d.block and "F821" in d.reason


def test_format_on_edit_ignores_non_python_and_can_be_disabled(tmp_path):
    (tmp_path / "sdlc.yaml").write_text("hooks:\n  format_on_edit: false\n", encoding="utf-8")
    f = tmp_path / "m.py"
    f.write_text("x=1\n", encoding="utf-8")
    payload = {"tool_name": "Write", "tool_input": {"file_path": str(f)}, "cwd": str(tmp_path)}
    assert not format_on_edit.decide(payload, [], env={"CLAUDE_PROJECT_DIR": str(tmp_path)}).block
    assert f.read_text(encoding="utf-8") == "x=1\n"
    md = tmp_path / "n.md"
    md.write_text("x", encoding="utf-8")
    assert not format_on_edit.decide(
        {"tool_name": "Write", "tool_input": {"file_path": str(md)}, "cwd": str(tmp_path)},
        [],
        env={},
    ).block


def test_format_on_edit_end_to_end_emits_block_json(tmp_path):
    pytest.importorskip("ruff")
    f = tmp_path / "m.py"
    f.write_text("def f():\n    return undefined_name\n", encoding="utf-8")
    payload = {
        "hook_event_name": "PostToolUse",
        "tool_name": "Edit",
        "tool_input": {"file_path": str(f)},
        "cwd": str(tmp_path),
    }
    proc = subprocess.run(
        [sys.executable, str(HOOKS_DIR / "format_on_edit.py")],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        env={**os.environ, "CLAUDE_PROJECT_DIR": str(tmp_path)},
    )
    assert proc.returncode == 0  # PostToolUse: feedback, never a hard block
    assert json.loads(proc.stdout)["decision"] == "block"


# --- plan sync -----------------------------------------------------------------------------
def test_plan_sync_rules():
    exempt = list(plan_sync.DEFAULT_EXEMPT)
    ok = plan_sync.check
    assert not ok("main", ["src/a.py"], exempt).block  # not an sdlc branch
    assert not ok("sdlc/0001/a", ["src/a.py"], exempt).block  # only phase c is enforced
    assert not ok("sdlc/0001/c", ["changes/0001-x/status.yaml"], exempt).block  # no source
    assert ok("sdlc/0001/c", ["src/a.py"], exempt).block
    assert not ok("sdlc/0001/c", ["src/a.py", "changes/0001-x/plan.md"], exempt).block
    assert ok("sdlc/0001/c", ["src/a.py", "changes/0002-y/plan.md"], exempt).block  # wrong change
    assert not ok("sdlc/0001/c", ["docs/x.md"], exempt + ["docs/**"]).block


def test_plan_sync_only_on_commit_commands():
    calls = []

    def fake_git(root, *args):
        calls.append(args)
        return "sdlc/0001/c\n" if args[0] == "rev-parse" else "src/a.py\n"

    assert not plan_sync.decide(
        pre("Bash", command="git status"), [], env={"CLAUDE_PROJECT_DIR": "/p"}, git=fake_git
    ).block
    assert calls == []
    d = plan_sync.decide(
        pre("Bash", command="git commit -m 'x'"), [], env={"CLAUDE_PROJECT_DIR": "/p"}, git=fake_git
    )
    assert d.block and "plan.md is out of sync" in d.reason
    d = plan_sync.decide(
        pre("PowerShell", command="git commit -am 'x'"),
        [],
        env={"CLAUDE_PROJECT_DIR": "/p"},
        git=fake_git,
    )
    assert d.block


def _git(root: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=root, capture_output=True, text=True, check=True
    ).stdout


def test_plan_sync_end_to_end_in_a_real_repo(tmp_path):
    _git(tmp_path, "init", "-q", "-b", "main")
    _git(tmp_path, "config", "user.email", "t@example.com")
    _git(tmp_path, "config", "user.name", "t")
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "a.py").write_text("x = 1\n", encoding="utf-8")
    plan = tmp_path / "changes" / "0001-x"
    plan.mkdir(parents=True)
    (plan / "plan.md").write_text("# Plan\n", encoding="utf-8")
    _git(tmp_path, "add", ".")
    _git(tmp_path, "commit", "-q", "-m", "init")
    _git(tmp_path, "checkout", "-q", "-b", "sdlc/0001/c")
    (tmp_path / "src" / "a.py").write_text("x = 2\n", encoding="utf-8")
    _git(tmp_path, "add", "src/a.py")
    payload = {**pre("Bash", command="git commit -m 'change'"), "cwd": str(tmp_path)}
    env = {**os.environ, "CLAUDE_PROJECT_DIR": str(tmp_path)}
    proc = subprocess.run(
        [sys.executable, str(HOOKS_DIR / "plan_sync.py")],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        env=env,
    )
    assert proc.returncode == 2, proc.stderr
    (plan / "plan.md").write_text("# Plan\n- updated\n", encoding="utf-8")
    _git(tmp_path, "add", "changes/0001-x/plan.md")
    proc = subprocess.run(
        [sys.executable, str(HOOKS_DIR / "plan_sync.py")],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        env=env,
    )
    assert proc.returncode == 0, proc.stderr


# --- hooks.json contract -------------------------------------------------------------------
def test_hooks_json_uses_exec_form_with_python():
    data = json.loads((HOOKS_DIR / "hooks.json").read_text(encoding="utf-8"))
    handlers = [h for group in data["hooks"].values() for entry in group for h in entry["hooks"]]
    assert handlers
    for h in handlers:
        assert h["type"] == "command" and h["command"] == "python"
        assert h["args"][0].startswith("${CLAUDE_PLUGIN_ROOT}/hooks/")
        assert (HOOKS_DIR / Path(h["args"][0]).name).is_file()
        assert h["timeout"] <= 60
    events = set(data["hooks"])
    assert events == {"PreToolUse", "PostToolUse"}  # no 'ask' hooks in the build phase
