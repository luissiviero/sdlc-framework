"""Layer-1 tests for the four hooks: sample tool inputs in, decisions out, plus one
end-to-end run of each script over stdin to prove the exit code and JSON contract."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from hooks import (
    _common,
    format_on_edit,
    plan_sync,
    protected_paths,
    secrets_check,
    test_file_lock,
)
from state import status

HOOKS_DIR = Path(__file__).resolve().parents[1] / "plugin" / "hooks"
PLUGIN_ROOT = HOOKS_DIR.parents[1]  # the repository root is the plugin root


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
    # a leading slash anchors a bare name to the root (gitignore); Windows spelling too
    assert m("/CLAUDE.md", "CLAUDE.md") and m("/CLAUDE.md", "claude.md")
    assert not m("/CLAUDE.md", "packages/api/CLAUDE.md")
    assert not m("/CLAUDE.md", "template\\CLAUDE.md")
    assert m("/.claude/**", ".claude/settings.json")
    assert not m("/.claude/**", "template/.claude/settings.json")
    assert m("src/gen/**", "src/gen/a/b.py")
    assert m("*.lock", "poetry.lock") and m("*.lock", "sub/poetry.lock")
    assert m("migrations/", "migrations/0001_init.py")


def test_norm_handles_windows_paths():
    assert _common.norm("C:\\project\\src\\index.ts") == "c:/project/src/index.ts"
    assert _common.rel_to("C:\\project", "C:\\project\\CLAUDE.md") == "claude.md"
    assert _common.rel_to("/home/u/proj", "/home/u/other/x") is None
    # spelling variants collapse to one comparison form
    assert _common.norm("/p/src/../.claude//settings.json ") == "/p/.claude/settings.json"
    assert _common.norm("C:\\Work\\Proj\\Claude.MD") == "c:/work/proj/claude.md"
    assert _common.norm("\\\\server\\share\\x") == "//server/share/x"


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


@pytest.mark.parametrize(
    "rel",
    [
        "template/CLAUDE.md",
        "template/REVIEW.md",
        "template/sdlc.yaml",
        "docs/x/CLAUDE.md",
        "api/CLAUDE.md",
        "packages/api/.claude/commands/x.md",
    ],
)
def test_nested_guardrail_names_are_project_content(project, rel):
    """0.2.10: the always-protected set is the project's own guardrail files, at the root.
    The framework repository builds template/CLAUDE.md, template/REVIEW.md and
    template/sdlc.yaml; a phase (c) run there must be able to edit them (NOTES section 12).
    Nested .claude/settings*.json and .claude/hooks/** stay caught by GLOBAL_PROTECTED."""
    payload = pre("Edit", file_path=str(project / rel), old_string="a", new_string="b")
    assert not protected_paths.decide(payload, [], env=_env(project)).block, rel


def test_nested_settings_and_hooks_stay_protected(project):
    for rel in ("packages/api/.claude/settings.json", "template/.claude/hooks/x.py"):
        payload = pre("Write", file_path=str(project / rel), content="")
        assert protected_paths.decide(payload, [], env=_env(project)).block, rel


@pytest.mark.parametrize(
    ("rel", "blocked"),
    [
        ("CLAUDE.md", True),
        ("REVIEW.md", True),
        ("sdlc.yaml", True),
        (".claude\\settings.json", True),
        ("template\\CLAUDE.md", False),
        ("template\\REVIEW.md", False),
        ("template\\sdlc.yaml", False),
        ("Docs\\X\\Claude.MD", False),
    ],
)
def test_root_anchoring_on_windows_paths(rel, blocked):
    """Backslash spellings, a drive letter and mixed case: the root copy is caught, the
    nested copy is free. No file exists, so both norm() and real() candidates are exercised."""
    win_root = "C:\\work\\proj"
    payload = {
        "tool_name": "Write",
        "tool_input": {"file_path": win_root + "\\" + rel, "content": ""},
        "cwd": win_root,
    }
    d = protected_paths.decide(payload, [], env={"CLAUDE_PROJECT_DIR": win_root})
    assert d.block is blocked, rel


def test_project_protected_paths_keep_gitignore_semantics(tmp_path):
    """Only the four always-protected patterns are anchored; the owner's own list still
    matches a bare name in any directory, as before 0.2.10."""
    (tmp_path / "sdlc.yaml").write_text(
        "protected_paths: [poetry.lock, /Makefile]\n", encoding="utf-8"
    )
    env = {"CLAUDE_PROJECT_DIR": str(tmp_path)}
    for rel, blocked in (
        ("poetry.lock", True),
        ("sub/poetry.lock", True),
        ("Makefile", True),
        ("sub/Makefile", False),
    ):
        payload = pre("Write", file_path=str(tmp_path / rel), content="")
        assert protected_paths.decide(payload, [], env=env).block is blocked, rel


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
    assert d.block and "SDLC plugin" in d.reason


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
    # the departure rule (article p.16 step 7): a commit whose source files are all listed
    # under "## Files that change" needs no plan.md; one that touches an unlisted file does
    planned = ["src/a.py", "tests/test_a.py"]
    assert not ok("sdlc/0001/c", ["src/a.py"], exempt, planned).block
    assert not ok("sdlc/0001/c", ["src/a.py", "tests/test_a.py"], exempt, planned).block
    d = ok("sdlc/0001/c", ["src/a.py", "src/b.py"], exempt, planned)
    assert d.block and "src/b.py" in d.reason and "src/a.py" not in d.reason
    assert not ok("sdlc/0001/c", ["src/b.py", "changes/0001-x/plan.md"], exempt, planned).block
    assert not ok("sdlc/0001/c", ["src/sub/x.py"], exempt, ["src/"]).block  # a directory entry
    assert not ok("sdlc/0001/c", ["SRC/A.py"], exempt, planned).block  # case, as the gate


def test_plan_sync_allows_a_commit_inside_the_plan_in_a_real_repo(tmp_path):
    """The first gated build run (2026-09-22): three commits, each on files plan.md lists,
    none with plan.md - the prose asks for plan.md only when the work departs from it."""
    _git(tmp_path, "init", "-q", "-b", "main")
    _git(tmp_path, "config", "user.email", "t@example.com")
    _git(tmp_path, "config", "user.name", "t")
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "a.py").write_text("x = 1\n", encoding="utf-8")
    plan = tmp_path / "changes" / "0001-x"
    plan.mkdir(parents=True)
    (plan / "plan.md").write_text(
        "# Plan\n\n## Files that change\n- `src/a.py` - bump x\n\n## Order of work\n- 1\n",
        encoding="utf-8",
    )
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
    assert proc.returncode == 0, proc.stderr  # inside the plan: nothing to sync
    (tmp_path / "src" / "b.py").write_text("y = 1\n", encoding="utf-8")
    _git(tmp_path, "add", "src/b.py")
    proc = subprocess.run(
        [sys.executable, str(HOOKS_DIR / "plan_sync.py")],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        env=env,
    )
    assert proc.returncode == 2 and "src/b.py" in proc.stderr  # a departure without plan.md


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
        assert h["args"][0].startswith("${CLAUDE_PLUGIN_ROOT}/plugin/hooks/")
        assert (HOOKS_DIR / Path(h["args"][0]).name).is_file()
        assert h["timeout"] <= 60
    events = set(data["hooks"])
    assert events == {"PreToolUse", "PostToolUse"}  # no 'ask' hooks in the build phase


# --- hardening (second review round) ------------------------------------------------------
@pytest.mark.parametrize(
    "rel",
    [
        "src/../.claude/settings.json",
        ".Claude/Settings.JSON",
        "claude.md",
        "CLAUDE.md ",
        "src//..//sdlc.yaml",
    ],
)
def test_protected_paths_spelling_variants(project, rel):
    payload = pre("Write", file_path=str(project) + "/" + rel, content="")
    assert protected_paths.decide(payload, [], env=_env(project)).block, rel


def test_protected_paths_symlink_into_project(project):
    (project / "src").mkdir()
    try:
        os.symlink(project, project / "src" / "up", target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("symlinks not available")
    payload = pre(
        "Write", file_path=str(project / "src" / "up" / ".claude" / "settings.json"), content=""
    )
    assert protected_paths.decide(payload, [], env=_env(project)).block


def test_user_level_settings_are_protected_outside_the_project(project, tmp_path):
    home = tmp_path / "home" / ".claude"
    payload = pre("Edit", file_path=str(home / "settings.json"), old_string="", new_string="")
    assert protected_paths.decide(payload, [], env=_env(project)).block
    payload = pre("Write", file_path=str(home / "hooks" / "x.py"), content="")
    assert protected_paths.decide(payload, [], env=_env(project)).block
    payload = pre("Write", file_path=str(tmp_path / "home" / "notes.md"), content="")
    assert not protected_paths.decide(payload, [], env=_env(project)).block


def test_protected_paths_fail_closed_on_unreadable_sdlc_yaml(tmp_path):
    (tmp_path / "sdlc.yaml").write_text("protected_paths: {bad: [\n", encoding="utf-8")
    payload = pre("Write", file_path=str(tmp_path / "src" / "ok.py"), content="")
    d = protected_paths.decide(payload, [], env={"CLAUDE_PROJECT_DIR": str(tmp_path)})
    assert d.block and "sdlc.yaml" in d.reason


def test_protected_paths_reads_bom_and_document_marker(tmp_path):
    (tmp_path / "sdlc.yaml").write_text("\ufeff---\nprotected_paths: [gen/**]\n", encoding="utf-8")
    payload = pre("Write", file_path=str(tmp_path / "gen" / "a.py"), content="")
    assert protected_paths.decide(payload, [], env={"CLAUDE_PROJECT_DIR": str(tmp_path)}).block


def test_project_dir_falls_back_to_nearest_root(tmp_path):
    (tmp_path / "sdlc.yaml").write_text("profile: lite\n", encoding="utf-8")
    (tmp_path / "src").mkdir()
    payload = {
        "tool_name": "Write",
        "tool_input": {"file_path": str(tmp_path / "CLAUDE.md"), "content": ""},
        "cwd": str(tmp_path / "src"),
    }
    assert protected_paths.decide(payload, [], env={}).block


def test_protected_paths_empty_stdin_fails_closed():
    proc = subprocess.run(
        [sys.executable, str(HOOKS_DIR / "protected_paths.py")],
        input="",
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 2


@pytest.mark.parametrize(
    "command",
    [
        "git add .\ngit commit -m x",
        "(git commit -m x)",
        "$(git commit -m x)",
        "GIT_EDITOR=true git commit",
        "git -c user.name=x commit -m y",
        'git -C "my dir" commit -m y',
        "git add . && git commit --amend --no-edit",
    ],
)
def test_plan_sync_detects_commit_in_any_position(command):
    assert plan_sync.COMMIT_RE.search(command), command


@pytest.mark.parametrize(
    "command",
    ["git status", "git commit-tree abc", "echo 'git commits are nice'", "git log --grep commit"],
)
def test_plan_sync_ignores_non_commit_commands(command):
    assert not plan_sync.COMMIT_RE.search(command), command


def test_plan_sync_commit_options():
    assert plan_sync.commit_options("git commit -m 'x'") == (False, [])
    assert plan_sync.commit_options("git commit -am 'x'") == (True, [])
    assert plan_sync.commit_options("git commit -qa -m x") == (True, [])
    assert plan_sync.commit_options("git commit --all -m x") == (True, [])
    assert plan_sync.commit_options("git commit -m x src/a.py") == (False, ["src/a.py"])
    assert plan_sync.commit_options("git commit -m x -- src/a.py b.py && echo hi") == (
        False,
        ["src/a.py", "b.py"],
    )
    assert plan_sync.commit_options('git commit -m "don\'t" src/a.py') == (False, ["src/a.py"])


def test_plan_sync_pathspec_commit_is_checked(tmp_path):
    _git(tmp_path, "init", "-q", "-b", "main")
    _git(tmp_path, "config", "user.email", "t@example.com")
    _git(tmp_path, "config", "user.name", "t")
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "a.py").write_text("x = 1\n", encoding="utf-8")
    _git(tmp_path, "add", ".")
    _git(tmp_path, "commit", "-q", "-m", "init")
    _git(tmp_path, "checkout", "-q", "-b", "sdlc/0002/c")
    (tmp_path / "src" / "a.py").write_text("x = 2\n", encoding="utf-8")  # unstaged
    payload = {**pre("Bash", command="git commit -m 'x' src/a.py"), "cwd": str(tmp_path)}
    env = {**os.environ, "CLAUDE_PROJECT_DIR": str(tmp_path)}
    proc = subprocess.run(
        [sys.executable, str(HOOKS_DIR / "plan_sync.py")],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        env=env,
    )
    assert proc.returncode == 2, proc.stderr


def test_plan_sync_tolerates_bad_config_and_quotes():
    def fake_git(root, *args):
        return "sdlc/0001/c\n" if args[0] == "rev-parse" else "src/a.py\0"

    assert plan_sync.exempt_patterns({"plan_sync": True}) == list(plan_sync.DEFAULT_EXEMPT)
    d = plan_sync.decide(
        pre("Bash", command="git commit -m 'don't"),
        [],
        env={"CLAUDE_PROJECT_DIR": "/p"},
        git=fake_git,
    )
    assert d.block and "plan.md is out of sync" in d.reason


@pytest.mark.parametrize(
    "text",
    [
        '{"password": "s3cretvalue123"}',
        "POSTGRES_PASSWORD=hunter2hunter2",
        "DB_PASSWORD: hunter2hunter2",
        "client_secret = 'abcdefghijkl'",
        "aws_secret_access_key = 'wJalrXUtnFEMI/K7MDENG'",
        "key = 'sk-proj-" + "c" * 40 + "'",
        "-----BEGIN ENCRYPTED PRIVATE KEY-----",
    ],
)
def test_secrets_more_shapes_denied(text):
    assert secrets_check.decide(pre("Write", file_path="/p/x", content=text), []).block


@pytest.mark.parametrize(
    "text",
    [
        "password = os.getenv('PASSWORD')",
        "PASSWORD=$SECRET_FROM_ENV",
        "password: ...",
        "token = 'sk-ant-api03-…'  # sdlc: allow-secret",
    ],
)
def test_secrets_more_shapes_allowed(text):
    assert not secrets_check.decide(pre("Write", file_path="/p/x", content=text), []).block


def test_format_on_edit_ignores_files_outside_project(tmp_path):
    outside = tmp_path / "outside.py"
    outside.write_text("x=1\n", encoding="utf-8")
    proj = tmp_path / "proj"
    proj.mkdir()
    payload = {"tool_name": "Write", "tool_input": {"file_path": str(outside)}, "cwd": str(proj)}
    assert not format_on_edit.decide(payload, [], env={"CLAUDE_PROJECT_DIR": str(proj)}).block
    assert outside.read_text(encoding="utf-8") == "x=1\n"


# --- test-file lock (build guide step 25) ---------------------------------------------------
LOCK_HOOK = HOOKS_DIR / "test_file_lock.py"
DEFAULT_TEST_PATHS_BLOCK = '  - "tests/**"\n  - "**/test_*.py"\n'


def _lock_project(
    tmp_path,
    change_type="fix",
    locked=True,
    branch="sdlc/0001/c",
    test_paths=DEFAULT_TEST_PATHS_BLOCK,
):
    """A git repo on `branch` holding change 0001 and a test file the lock can cover."""
    root = tmp_path
    body = "profile: standard\nprotected_paths: []\n"
    if test_paths is not None:
        body += "test_paths:\n" + test_paths
    (root / "sdlc.yaml").write_text(body, encoding="utf-8")
    (root / "tests").mkdir()
    (root / "tests" / "test_calc.py").write_text("def test_x():\n    pass\n", encoding="utf-8")
    (root / "sample_pkg").mkdir()
    (root / "sample_pkg" / "calc.py").write_text("x = 1\n", encoding="utf-8")
    change_dir, st = status.new_change(root, "Fix the thing", change_type=change_type)
    if locked:
        st.lock_tests()
        status.write_status(change_dir, st)
    _git(root, "init", "-q", "-b", "main")
    _git(root, "config", "user.email", "t@example.com")
    _git(root, "config", "user.name", "t")
    _git(root, "add", ".")
    _git(root, "commit", "-q", "-m", "init")
    if branch != "main":
        _git(root, "checkout", "-q", "-b", branch)
    return root, change_dir


def _run_lock_hook(root, payload):
    return subprocess.run(
        [sys.executable, str(LOCK_HOOK)],
        input=json.dumps({**payload, "cwd": str(root)}),
        capture_output=True,
        text=True,
        env={**os.environ, "CLAUDE_PROJECT_DIR": str(root)},
    )


def test_test_file_lock_denies_a_test_edit_in_a_locked_fix(tmp_path):
    root, _ = _lock_project(tmp_path)
    proc = _run_lock_hook(
        root,
        pre("Edit", file_path=str(root / "tests" / "test_calc.py"), old_string="a", new_string="b"),
    )
    assert proc.returncode == 2, proc.stderr
    out = json.loads(proc.stdout)
    assert out["hookSpecificOutput"]["permissionDecision"] == "deny"
    assert "Test-file lock" in proc.stderr and "unlock-tests" in proc.stderr
    assert "tests/test_calc.py" in out["hookSpecificOutput"]["permissionDecisionReason"]


def test_test_file_lock_allows_source_edits_in_a_locked_fix(tmp_path):
    root, _ = _lock_project(tmp_path)
    proc = _run_lock_hook(
        root,
        pre("Edit", file_path=str(root / "sample_pkg" / "calc.py"), old_string="a", new_string="b"),
    )
    assert proc.returncode == 0 and proc.stdout == "", proc.stderr


def test_test_file_lock_ignores_feature_changes(tmp_path):
    root, _ = _lock_project(tmp_path, change_type="feature")
    proc = _run_lock_hook(
        root, pre("Write", file_path=str(root / "tests" / "test_calc.py"), content="x")
    )
    assert proc.returncode == 0, proc.stderr


def test_test_file_lock_ignores_a_fix_before_the_test_is_committed(tmp_path):
    root, _ = _lock_project(tmp_path, locked=False)
    proc = _run_lock_hook(
        root, pre("Write", file_path=str(root / "tests" / "test_calc.py"), content="x")
    )
    assert proc.returncode == 0, proc.stderr


def test_test_file_lock_never_denies_outside_a_phase_branch(tmp_path):
    root, _ = _lock_project(tmp_path, branch="main")
    proc = _run_lock_hook(
        root, pre("Write", file_path=str(root / "tests" / "test_calc.py"), content="x")
    )
    assert proc.returncode == 0, proc.stderr


def test_test_file_lock_checks_every_multiedit_target(tmp_path):
    root, _ = _lock_project(tmp_path)
    payload = pre(
        "MultiEdit",
        file_path=str(root / "sample_pkg" / "calc.py"),
        edits=[
            {
                "file_path": str(root / "sample_pkg" / "calc.py"),
                "old_string": "x",
                "new_string": "y",
            },
            {
                "file_path": str(root / "tests" / "test_calc.py"),
                "old_string": "a",
                "new_string": "b",
            },
        ],
    )
    proc = _run_lock_hook(root, payload)
    assert proc.returncode == 2, proc.stderr
    assert "Test-file lock" in proc.stderr


def test_test_file_lock_fails_closed_on_an_unreadable_status_yaml(tmp_path):
    root, change_dir = _lock_project(tmp_path)
    (change_dir / "status.yaml").write_text("id: 0001\n\tbroken: [\n", encoding="utf-8")
    proc = _run_lock_hook(
        root,
        pre("Edit", file_path=str(root / "sample_pkg" / "calc.py"), old_string="a", new_string="b"),
    )
    assert proc.returncode == 2, proc.stdout
    assert "fails closed" in proc.stderr and "status.yaml" in proc.stderr


def test_test_file_lock_falls_back_to_the_built_in_globs(tmp_path):
    """A project initialised before step 25 has no `test_paths:` key: the lock still holds."""
    root, _ = _lock_project(tmp_path, test_paths=None)
    payload = {
        **pre(
            "Edit", file_path=str(root / "tests" / "test_calc.py"), old_string="a", new_string="b"
        ),
        "cwd": str(root),
    }
    d = test_file_lock.decide(payload, [], env={"CLAUDE_PROJECT_DIR": str(root)})
    assert d.block and "Test-file lock" in d.reason


def test_hooks_json_registers_the_test_file_lock_with_the_protected_path_matcher():
    data = json.loads((HOOKS_DIR / "hooks.json").read_text(encoding="utf-8"))
    entries = [
        e
        for e in data["hooks"]["PreToolUse"]
        if any("test_file_lock.py" in h["args"][0] for h in e["hooks"])
    ]
    assert len(entries) == 1
    scripts = [Path(h["args"][0]).name for h in entries[0]["hooks"]]
    assert entries[0]["matcher"] == "Edit|Write|MultiEdit|NotebookEdit"
    assert "protected_paths.py" in scripts
    assert scripts.index("test_file_lock.py") > scripts.index("protected_paths.py")
