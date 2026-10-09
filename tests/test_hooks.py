"""Layer-1 tests for the hooks: sample tool inputs in, decisions out, plus one
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
    panel_blind,
    plan_sync,
    production_gate,
    protected_paths,
    secrets_check,
    shell_guard,
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
        "def test_password_field(): ...",
    ],
)
def test_secrets_allowed(text):
    assert not secrets_check.decide(pre("Write", file_path="/p/x.py", content=text), []).block


def test_the_allow_secret_mark_counts_only_on_a_line_the_owner_committed(tmp_path):
    """0.2.28: the denial message used to suggest the mark, and a live run of eval case 0003
    saw the model add it on a retry and land the key. The mark is the owner's: a marked
    line is skipped only when HEAD already holds it byte for byte (a reviewed PR put it
    there); a new file, a changed line, another file and an Edit's new text are refused."""
    root = tmp_path / "proj"
    root.mkdir()
    run = lambda *args: subprocess.run(  # noqa: E731
        ["git", "-c", "user.name=Owner", "-c", "user.email=owner@example.com", *args],
        cwd=root, check=True, capture_output=True, text=True,
    )  # fmt: skip
    run("init", "-q", "-b", "main")
    marked = "token = 'ghp_" + "a" * 36 + "'  # sdlc: allow-secret"

    def write(content: str, name: str = "fixture.py", tool: str = "Write") -> dict:
        tool_input = {"file_path": str(root / name)}
        if tool == "Write":
            tool_input["content"] = content
        else:
            tool_input.update({"old_string": "x = 1", "new_string": content})
        return {"hook_event_name": "PreToolUse", "tool_name": tool, "cwd": str(root),
                "tool_input": tool_input}  # fmt: skip

    d = secrets_check.decide(write(marked + "\n"), [], {})  # nothing committed yet
    assert d.block and "has not committed" in d.reason and "cannot add the mark" in d.reason
    assert "put '#" not in d.reason  # the message no longer teaches the mark
    (root / "fixture.py").write_text(marked + "\nx = 1\n", encoding="utf-8", newline="\n")
    run("add", "fixture.py")
    run("commit", "-q", "-m", "the owner's fixture")
    assert not secrets_check.decide(write(marked + "\nx = 2\n"), [], {}).block
    assert not secrets_check.decide(write(marked, tool="Edit"), [], {}).block
    changed = marked.replace("'ghp_a", "'ghp_b", 1)
    assert secrets_check.decide(write(changed + "\n"), [], {}).block
    assert secrets_check.decide(write(marked + "\n", name="other.py"), [], {}).block
    assert secrets_check.decide(write(changed, tool="Edit"), [], {}).block
    assert secrets_check.decide(write(marked + "\n", name="../outside.py"), [], {}).block
    assert secrets_check.find_secrets(marked, frozenset({marked})) == []
    assert secrets_check.find_secrets(marked) == [
        (1, "GitHub token" + secrets_check.UNCOMMITTED_MARK)
    ]


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


# --- production gate (build guide step 29; decision 13; article p.35-37) -------------------
GATE_HOOK = HOOKS_DIR / "production_gate.py"


class FakeGitHub:
    """The two pr.github calls the approval makes, answered from memory."""

    def __init__(self, actor="owner-login", ok=True, reason="", labels=None, number=7):
        self.actor, self.ok, self.reason, self.number = actor, ok, reason, number
        self.labels = ["sdlc:release-approved"] if labels is None else labels
        self.calls = []

    def pr_by_number(self, repo, number, cwd=None):
        self.calls.append(("pr_by_number", repo, number))
        if not self.ok:
            return {"ok": False, "number": None, "reason": self.reason}
        return {
            "ok": True, "number": number, "state": "open", "merged": False,
            "merge_commit_sha": None, "head_ref": "sdlc/0001/c", "head_sha": "abc1234def5678",
            "labels": self.labels, "reason": "",
        }  # fmt: skip

    def label_actor(self, repo, number, label):
        self.calls.append(("label_actor", repo, number, label))
        if not self.ok:
            return {"ok": False, "actor": None, "reason": self.reason}
        return {"ok": True, "actor": self.actor, "reason": ""}


def gate_git(tags=(), verify_ok=False, branch="sdlc/0001/c", remote="https://github.com/o/r.git"):
    """A git runner answering the calls the hook and the approval make: (exit, stdout)."""

    def git(root, *args):
        if args[:2] == ("rev-parse", "--abbrev-ref"):
            return 0, branch + "\n"
        if args == ("rev-parse", "HEAD"):
            return 0, "abc1234def5678\n"
        if args[:2] == ("remote", "get-url"):
            return (0, remote + "\n") if remote else (2, "")
        if args[:2] == ("tag", "--points-at"):
            return 0, "".join(f"{t}\n" for t in tags)
        if args[0] == "verify-tag":
            return (0 if verify_ok else 1), ""
        return 1, ""

    return git


def _gate_project(tmp_path, production=True, action="publish package", guarded=None):
    body = f"deploy:\n  action: {action}\n  production: {'true' if production else 'false'}\n"
    if guarded is not None:
        body += "  guarded_commands:\n" + "".join(f'    - "{g}"\n' for g in guarded)
    (tmp_path / "sdlc.yaml").write_text(body, encoding="utf-8")
    # change 0001 with its build PR recorded (pr/cli.py upsert, 0.2.27): the approval is
    # read from that PR, never from the branch's name
    change_dir, st = status.new_change(tmp_path, "Export the claims report")
    st.build_pr = 7
    status.write_status(change_dir, st)
    log = tmp_path / "hook-log.jsonl"
    return tmp_path, {"CLAUDE_PROJECT_DIR": str(tmp_path), "SDLC_HOOK_LOG": str(log)}, log


def _log_lines(log):
    if not log.exists():
        return []
    return [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines()]


def _gate(root, env, command, **kw):
    payload = {**pre("Bash", command=command), "cwd": str(root)}
    kw.setdefault("git", gate_git())
    kw.setdefault("github", FakeGitHub(ok=False, reason="no route"))
    return production_gate.decide(payload, [], env=env, **kw)


def test_production_gate_is_inert_without_a_declared_production(tmp_path):
    root, env, log = _gate_project(tmp_path, production=False)
    d = _gate(root, env, "twine upload dist/*")
    assert not d.block
    assert not log.exists()
    assert not (root / "changes" / ".hook-log.jsonl").exists()  # no default log either
    assert not list((root / "changes").rglob("hook-log.jsonl"))


def test_production_gate_allows_and_logs_a_non_guarded_command(tmp_path):
    root, env, log = _gate_project(tmp_path)
    d = _gate(root, env, "python -m pytest -q")
    assert not d.block
    (line,) = _log_lines(log)
    assert line["verdict"] == "allow" and line["reason"] == "not a guarded command"
    assert line["hook"] == "production_gate" and line["tool"] == "Bash" and line["at"]


def test_production_gate_blocks_twine_upload_without_approval(tmp_path):
    root, env, log = _gate_project(tmp_path)
    d = _gate(root, env, "twine upload dist/*")
    assert d.block
    assert "Production gate" in d.reason and "sdlc:release-approved" in d.reason
    assert "publish package" in d.reason and "nobody has been notified" in d.reason
    (line,) = _log_lines(log)
    assert line["verdict"] == "block" and line["matched"] == "twine upload*"


def test_production_gate_allows_with_the_label_applied_by_a_person(tmp_path):
    root, env, log = _gate_project(tmp_path)
    gh = FakeGitHub(actor="luissiviero")
    d = _gate(root, env, "twine upload dist/*", github=gh)
    assert not d.block, d.reason
    assert ("pr_by_number", "o/r", 7) in gh.calls  # the recorded build PR, by number
    (line,) = _log_lines(log)
    assert line["verdict"] == "allow" and line["how"] == "label" and line["pr"] == 7


def test_production_gate_reads_the_recorded_build_pr_of_the_checked_out_change(tmp_path):
    """The readiness review's group B (0.2.27): the hook found the PR by the branch's name,
    so a checkout of another change's ``sdlc/<id>/c`` inherited its approval. Now the hook
    passes the change it resolved, the approval reads that change's recorded build PR, and
    a change with no record, or a checkout that is not the PR's head, is blocked."""
    root, env, log = _gate_project(tmp_path)
    # another change, approved, whose branch the session could check out
    change_dir, st = status.new_change(root, "Another change")
    assert st.id == "0002"
    st.build_pr = 9
    status.write_status(change_dir, st)
    gh = FakeGitHub(actor="luissiviero", number=9)
    d = _gate(root, env, "twine upload dist/*", github=gh, git=gate_git(branch="sdlc/0002/c"))
    assert d.block and "#9 (head sdlc/0001/c) is not the build PR sdlc/0002/c" in d.reason
    assert ("pr_by_number", "o/r", 9) in gh.calls and ("pr_by_number", "o/r", 7) not in gh.calls
    # no record at all: the branch name alone finds nothing
    st.build_pr = None
    status.write_status(change_dir, st)
    d = _gate(root, env, "twine upload dist/*", github=gh, git=gate_git(branch="sdlc/0002/c"))
    assert d.block and "records no build pull request" in d.reason
    # change 0001 at a commit that is not its PR's head: blocked
    gh = FakeGitHub(actor="luissiviero")
    moved = gate_git()
    git = lambda root, *a: (0, "1111111111\n") if a == ("rev-parse", "HEAD") else moved(root, *a)  # noqa: E731
    d = _gate(root, env, "twine upload dist/*", github=gh, git=git)
    assert d.block and "only the pull request's own head carries its approval" in d.reason
    assert _log_lines(log)[-1]["verdict"] == "block"


def test_production_gate_refuses_the_label_applied_by_the_automation_identity(tmp_path):
    root, env, log = _gate_project(tmp_path)
    d = _gate(root, env, "twine upload dist/*", github=FakeGitHub(actor="github-actions[bot]"))
    assert d.block
    assert "github-actions[bot]" in d.reason and "#7" in d.reason
    assert _log_lines(log)[-1]["verdict"] == "block"


def test_production_gate_refuses_a_label_that_was_removed_again(tmp_path):
    root, env, _ = _gate_project(tmp_path)
    d = _gate(root, env, "twine upload dist/*", github=FakeGitHub(actor="owner", labels=[]))
    assert d.block and "is not on #7" in d.reason


def test_production_gate_never_allows_on_a_signed_tag(tmp_path):
    """B1 (decision 5): a session allowed git can sign a tag itself, so a verified signed
    tag is no approval; only the label a person applied on GitHub is."""
    root, env, log = _gate_project(tmp_path)
    gh = FakeGitHub(actor=None)
    d = _gate(root, env, "twine upload dist/*", git=gate_git(tags=("v1.2.0",), verify_ok=True))
    assert d.block
    d = _gate(root, env, "twine upload dist/*", github=gh, git=gate_git(("v1",), True))
    assert d.block and "is not on #7" in d.reason
    line = _log_lines(log)[-1]
    assert line["verdict"] == "block" and line["how"] == "none"
    assert "signed tag" not in d.reason
    assert "from GitHub, then re-runs" in d.reason


def test_production_gate_refuses_an_unsigned_tag(tmp_path):
    root, env, _ = _gate_project(tmp_path)
    d = _gate(root, env, "twine upload dist/*", git=gate_git(tags=("v1.2.0",), verify_ok=False))
    assert d.block and "verify-tag" not in d.reason and "cannot verify the label" in d.reason


@pytest.mark.parametrize(
    "command",
    [
        "gh pr edit 7 --add-label sdlc:release-approved",
        "gh api repos/o/r/issues/7/labels -f 'labels[]=SDLC:Release-Approved'",
        'curl -X POST -H "Authorization: token $T" https://api.github.com/repos/o/r/issues/7/'
        'labels -d \'{"labels":["sdlc:release-approved"]}\'',
        "python scripts/label.py 7 sdlc:release-approved",
        "echo ok && gh issue edit 7 --add-label=sdlc:release-approved",
    ],
)
def test_production_gate_blocks_any_command_that_names_the_release_label(tmp_path, command):
    """B1 (decision 5): a run cannot apply the release label to itself, whatever the tool;
    the block holds even when an approval exists."""
    root, env, log = _gate_project(tmp_path, action="none")
    gh = FakeGitHub(actor="luissiviero")
    d = _gate(root, env, command, github=gh)
    assert d.block
    assert "a run cannot apply the label to itself (decision 5)" in d.reason
    assert "the release approval is the owner's act on GitHub" in d.reason
    assert gh.calls == []  # blocked before any approval lookup
    line = _log_lines(log)[-1]
    assert line["verdict"] == "block" and line["matched"] == "sdlc:release-approved"


def test_production_gate_lets_the_label_through_when_no_production_is_declared(tmp_path):
    root, env, log = _gate_project(tmp_path, production=False)
    assert not _gate(root, env, "gh pr edit 7 --add-label sdlc:release-approved").block
    assert not log.exists()


def test_production_gate_fails_closed_when_github_cannot_be_reached(tmp_path):
    root, env, log = _gate_project(tmp_path)
    gh = FakeGitHub(ok=False, reason="api: HTTP 502; gh: gh not found")
    d = _gate(root, env, "twine upload dist/*", github=gh)
    assert d.block and "cannot verify the label" in d.reason and "HTTP 502" in d.reason
    assert _log_lines(log)[-1]["verdict"] == "block"


def test_production_gate_catches_the_article_trigger(tmp_path):
    root, env, _ = _gate_project(tmp_path, action="none")
    assert _gate(root, env, "./scripts/deploy.sh --env production").block
    assert _gate(root, env, "make deploy ENV=production").block
    assert not _gate(root, env, "./scripts/deploy.sh --env staging").block


def test_production_gate_catches_a_chained_command(tmp_path):
    root, env, _ = _gate_project(tmp_path)
    assert _gate(root, env, "cd dist && twine upload *").block
    assert _gate(root, env, "python -m build; python -m twine upload dist/*").block
    assert not _gate(root, env, "cd dist && ls").block


@pytest.mark.parametrize(
    "command, matched",
    [
        ("/usr/local/bin/twine upload dist/*", "twine upload*"),
        ("C:\\Python312\\Scripts\\twine.exe upload dist/*", "twine upload*"),
        ("twine.exe upload dist/*", "twine upload*"),
        ("./node_modules/.bin/npm publish", "npm publish*"),
        ("npm.cmd publish --access public", "npm publish*"),
        ("C:\\tools\\npm.cmd publish", "npm publish*"),
        ("terraform -chdir=infra apply -auto-approve", "terraform apply*"),
        ("terraform -chdir infra apply", "terraform apply*"),
        ("kubectl --context prod apply -f k8s/", "kubectl apply*"),
        ("kubectl --context=prod --namespace=web rollout restart deploy/api", "kubectl rollout*"),
        ("gh -R o/r release create v1.0.0", "gh release create*"),
        ("gh --repo o/r release create v1.0.0 dist/*", "gh release create*"),
        ("helm --kube-context prod upgrade api ./chart", "helm upgrade*"),
        ("docker --context prod push o/api:1.0", "docker push*"),
        # the review of the 0.2.27 diff, M8: a quoted value with a space is one token
        ('kubectl --context "prod east" apply -f k8s/', "kubectl apply*"),
        ("terraform -chdir='infra dir' apply", "terraform apply*"),
    ],
)
def test_production_gate_reads_paths_extensions_and_options_before_the_verb(
    tmp_path, command, matched
):
    """The readiness review's group B (0.2.27): ordinary spellings of a guarded command —
    the program by its path or with a Windows extension, options between the program and
    its verb — passed the gate, which compared whole token suffixes with the pattern."""
    action = (
        "deploy service"
        if matched.split()[0] in ("terraform", "kubectl", "helm", "docker")
        or matched.startswith("gh ")
        else "publish package"
    )
    root, env, log = _gate_project(tmp_path, action=action)
    d = _gate(root, env, command)
    assert d.block, command
    assert _log_lines(log)[-1]["matched"] == matched


@pytest.mark.parametrize(
    "command",
    [
        "pip install twine",
        "python -m twine --version",
        "twine check dist/*",
        "npm --version",
        "npm install --save-dev publish-please",
        "kubectl get pods --context prod",
        "terraform -chdir=infra plan",
        "gh release list -R o/r",
        "ls /usr/local/bin/twine",
        "cat C:\\tools\\npm.cmd",
    ],
)
def test_production_gate_still_leaves_look_alikes_alone(tmp_path, command):
    """The new readings add no false positives on the ordinary commands a run needs."""
    for action in ("publish package", "deploy service"):
        project = tmp_path / action.replace(" ", "-")
        project.mkdir()
        root, env, _ = _gate_project(project, action=action)
        assert not _gate(root, env, command).block, (action, command)


@pytest.mark.parametrize(
    "command",
    [
        "true & twine upload dist/*",
        "echo $(twine upload dist/*)",
        "echo `twine upload dist/*`",
        "bash -c 'twine upload dist/*'",
        "time twine upload dist/*",
        "nohup twine upload dist/* > log",
        "python3.11 -m twine upload dist/*",
        "cmd /c twine upload dist/*",
        'pwsh -Command "twine upload dist/*"',
        "& twine upload dist/*",
        "(twine upload dist/*)",
        "sudo -E env TWINE_USERNAME=x python -m twine upload dist/*",
        "C:/Python312/python.exe -m twine upload dist/*",
    ],
)
def test_production_gate_sees_through_wrappers(tmp_path, command):
    """I3: a runner, wrapper or substitution in front of a guarded command does not hide it."""
    root, env, log = _gate_project(tmp_path)
    d = _gate(root, env, command)
    assert d.block, command
    assert _log_lines(log)[-1]["matched"] == "twine upload*"


@pytest.mark.parametrize(
    "command",
    [
        'git commit -m "promote the docs"',
        "echo twine",
        "pip install twine",
        "python -m pytest -q",
        "git log --oneline",
    ],
)
def test_production_gate_leaves_ordinary_commands_alone(tmp_path, command):
    """I3 and M7: token suffixes do not turn a mention into a match, and the paper-trading
    adapter has no default pattern that a commit message could hit."""
    for action in ("publish package", "promote to paper trading"):
        root, env, _ = _gate_project(tmp_path, action=action)
        assert not _gate(root, env, command).block, (action, command)


def test_promote_to_paper_trading_guards_only_what_the_project_lists(tmp_path):
    """M7: no default pattern; the project's own promotion command is guarded, and the
    article trigger still holds."""
    assert production_gate.DEFAULT_GUARDED["promote to paper trading"] == ()
    root, env, _ = _gate_project(
        tmp_path, action="promote to paper trading", guarded=["python scripts/promote.py"]
    )
    assert _gate(root, env, "python scripts/promote.py --live").block
    assert not _gate(root, env, 'git commit -m "promote the strategy"').block
    assert _gate(root, env, "./deploy.sh --target production").block


def test_production_gate_reads_guarded_commands_from_sdlc_yaml(tmp_path):
    root, env, log = _gate_project(tmp_path, action="regenerate report", guarded=["make ship"])
    d = _gate(root, env, "make ship --all")
    assert d.block and "regenerate report" in d.reason
    assert _log_lines(log)[-1]["matched"] == "make ship*"
    assert not _gate(root, env, "make test").block


def test_production_gate_fails_closed_on_an_unreadable_sdlc_yaml(tmp_path):
    (tmp_path / "sdlc.yaml").write_text("deploy: [\n\tbroken", encoding="utf-8")
    log = tmp_path / "log.jsonl"
    env = {"CLAUDE_PROJECT_DIR": str(tmp_path), "SDLC_HOOK_LOG": str(log)}
    with pytest.raises(_common_config_error()):
        _gate(tmp_path, env, "ls")
    assert _log_lines(log)[-1]["verdict"] == "block"


def _common_config_error():
    """The ConfigError class the hook script raises (it imports ``_common`` as a top-level
    module, the way it runs under Claude Code)."""
    return sys.modules["_common"].ConfigError


def test_production_gate_honours_sdlc_hook_log_and_writes_valid_json_lines(tmp_path):
    root, env, _ = _gate_project(tmp_path)
    custom = tmp_path / "elsewhere" / "decisions.jsonl"
    env["SDLC_HOOK_LOG"] = str(custom)
    _gate(root, env, "echo hi")
    _gate(root, env, "twine upload dist/*")
    lines = _log_lines(custom)
    assert [x["verdict"] for x in lines] == ["allow", "block"]
    for line in lines:
        assert {"at", "hook", "verdict", "reason", "event", "tool", "cwd"} <= set(line)
        assert line["at"].endswith("Z") and len(line["at"]) == len("2026-09-23T10:00:00Z")


def test_production_gate_end_to_end_blocks_with_exit_2(tmp_path):
    root, env, log = _gate_project(tmp_path)
    payload = {**pre("Bash", command="twine upload dist/*"), "cwd": str(root)}
    proc = subprocess.run(
        [sys.executable, str(GATE_HOOK)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        env={**os.environ, **env},
    )
    assert proc.returncode == 2, proc.stderr
    out = json.loads(proc.stdout)
    assert out["hookSpecificOutput"]["permissionDecision"] == "deny"
    assert "sdlc:release-approved" in out["hookSpecificOutput"]["permissionDecisionReason"]
    assert "Production gate" in proc.stderr
    assert _log_lines(log)[-1]["verdict"] == "block"


def test_production_gate_end_to_end_is_silent_when_inert(tmp_path):
    root, env, log = _gate_project(tmp_path, production=False)
    payload = {**pre("PowerShell", command="twine upload dist/*"), "cwd": str(root)}
    proc = subprocess.run(
        [sys.executable, str(GATE_HOOK)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        env={**os.environ, **env},
    )
    assert proc.returncode == 0 and proc.stdout == "", proc.stderr
    assert not log.exists()


def test_hooks_json_registers_the_production_gate_on_bash_and_powershell():
    data = json.loads((HOOKS_DIR / "hooks.json").read_text(encoding="utf-8"))
    entries = [
        e
        for e in data["hooks"]["PreToolUse"]
        if any("production_gate.py" in h["args"][0] for h in e["hooks"])
    ]
    assert len(entries) == 1 and entries[0]["matcher"] == "Bash|PowerShell"
    (handler,) = entries[0]["hooks"]
    assert "if" not in handler and handler["timeout"] == 60
    # the hook's own budget stays inside the 60 s the hook is given
    assert production_gate.APPROVAL_DEADLINE < handler["timeout"]
    assert production_gate.CALL_TIMEOUT <= production_gate.APPROVAL_DEADLINE
    # I2: a timed-out PreToolUse hook does not block, so the worst case (the log path's one
    # git call + the approval deadline) keeps a margin for the log writes
    assert production_gate.WORST_CASE == (
        production_gate.CALL_TIMEOUT + production_gate.APPROVAL_DEADLINE
    )
    assert production_gate.WORST_CASE < 50


def test_production_gate_blocks_when_the_approval_cannot_be_verified_in_time(tmp_path):
    class SlowGitHub(FakeGitHub):
        TIMEOUT, GH_TIMEOUT = 30, 120  # the pr.github constants the hook caps meanwhile

        def label_actor(self, repo, number, label):
            assert (self.TIMEOUT, self.GH_TIMEOUT) == (10, 10)
            raise TimeoutError("api: read timed out")

    root, env, log = _gate_project(tmp_path)
    gh = SlowGitHub(actor="owner")
    d = _gate(root, env, "twine upload dist/*", github=gh)
    assert d.block and "cannot verify the approval in time" in d.reason
    assert (gh.TIMEOUT, gh.GH_TIMEOUT) == (30, 120)  # restored
    assert _log_lines(log)[-1]["verdict"] == "block"


def test_production_gate_computes_the_log_path_itself_and_log_decision_runs_no_git(
    tmp_path, monkeypatch
):
    """I2: without $SDLC_HOOK_LOG the hook finds the log path with its own bounded git call
    and hands it to log_decision, which then never starts git (its own lookup had a 20 s
    timeout outside the hook's budget); a git timeout falls back to the project log."""
    common = sys.modules["_common"]  # the module the hook script imported
    started = []
    monkeypatch.setattr(common.subprocess, "run", lambda *a, **k: started.append(a))
    (tmp_path / "sdlc.yaml").write_text(
        "deploy:\n  action: publish package\n  production: true\n", encoding="utf-8"
    )
    env = {"CLAUDE_PROJECT_DIR": str(tmp_path)}

    def slow_git(root, *args):
        if args[:2] == ("rev-parse", "--abbrev-ref"):
            raise TimeoutError("git rev-parse took over 10s")
        return gate_git()(root, *args)

    assert _gate(tmp_path, env, "twine upload dist/*", git=slow_git).block
    assert not _gate(tmp_path, env, "ls", git=gate_git(branch="main")).block
    assert started == []
    log = tmp_path / "changes" / ".hook-log.jsonl"
    assert [x["verdict"] for x in _log_lines(log)] == ["block", "allow"]


def test_log_decision_with_a_default_path_never_starts_git(tmp_path, monkeypatch):
    """I2: a given default_path skips the branch lookup (a fake git that would sleep is never
    started)."""
    started = []

    def would_sleep(*args, **kwargs):
        started.append(args)
        raise AssertionError("log_decision started git although default_path was given")

    monkeypatch.setattr(_common.subprocess, "run", would_sleep)
    target = tmp_path / "given.jsonl"
    payload = {**pre("Bash", command="ls"), "cwd": str(tmp_path)}
    path = _common.log_decision("t", "allow", "r", payload, env={}, default_path=target)
    assert path == target and started == []
    assert _log_lines(target)[0]["verdict"] == "allow"


def test_project_dir_keeps_the_case_of_the_project_path(tmp_path):
    app = tmp_path / "MyApp"
    (app / "Src").mkdir(parents=True)
    (app / "sdlc.yaml").write_text("profile: lite\n", encoding="utf-8")
    root = _common.project_dir({"cwd": str(app / "Src")}, env={})
    assert root.endswith("/MyApp") and "\\" not in root
    assert _common.load_sdlc_config(root) == {"profile": "lite"}
    assert _common.project_dir({}, env={"CLAUDE_PROJECT_DIR": str(app) + "/"}).endswith("/MyApp")
    assert _common.rel_to(root, str(app / "Src" / "x.py")) == "src/x.py"  # norm() compares


# --- the hook log's default place (build guide step 29.3) ----------------------------------
def test_log_decision_defaults_to_the_change_evidence_on_a_change_branch(tmp_path):
    change_dir, _ = status.new_change(tmp_path, "Ship it")
    _git(tmp_path, "init", "-q", "-b", "main")
    _git(tmp_path, "config", "user.email", "t@example.com")
    _git(tmp_path, "config", "user.name", "t")
    _git(tmp_path, "add", ".")
    _git(tmp_path, "commit", "-q", "-m", "init")
    _git(tmp_path, "checkout", "-q", "-b", "sdlc/0001/c")
    payload = {**pre("Bash", command="ls"), "cwd": str(tmp_path)}
    path = _common.log_decision(
        "t", "allow", "why", payload, env={"CLAUDE_PROJECT_DIR": str(tmp_path)}
    )
    assert path is not None
    assert os.path.samefile(path, change_dir / "evidence" / "hook-log.jsonl")
    assert not (tmp_path / "changes" / ".hook-log.jsonl").exists()


def test_log_decision_falls_back_to_the_project_log_off_a_change_branch(tmp_path):
    status.new_change(tmp_path, "Ship it")
    _git(tmp_path, "init", "-q", "-b", "main")
    payload = {**pre("Bash", command="ls"), "cwd": str(tmp_path)}
    path = _common.log_decision(
        "t", "block", "why", payload, env={"CLAUDE_PROJECT_DIR": str(tmp_path)}, extra_key=1
    )
    assert path is not None
    assert os.path.samefile(path, tmp_path / "changes" / ".hook-log.jsonl")
    (line,) = _log_lines(Path(path))
    assert line["verdict"] == "block" and line["extra_key"] == 1


def test_log_decision_never_raises(tmp_path):
    blocker = tmp_path / "file"
    blocker.write_text("x", encoding="utf-8")
    env = {"SDLC_HOOK_LOG": str(blocker / "sub" / "log.jsonl")}  # parent is a file
    assert _common.log_decision("t", "allow", "r", pre("Bash", command="ls"), env=env) is None


# --- build guide step 41.1: every hook logs its decisions (plugin 0.2.19) --------------------
def test_every_hook_logs_its_decision_through_run_hook(tmp_path):
    """Article p.39: "Every hook decision is written ... with a timestamp and an allow or
    block verdict". run_hook appends one line per decision - the hook, the verdict, the
    reason, the tool and its target paths - to the log file; the production gate keeps its
    own line (it computes the path under its own time budget)."""
    log = tmp_path / "hook-log.jsonl"
    env = {**os.environ, "SDLC_HOOK_LOG": str(log), "CLAUDE_PROJECT_DIR": str(tmp_path)}
    denied = pre("Write", file_path=str(tmp_path / "x.py"), content="password = 'abcdefghij'")
    allowed = pre("Write", file_path=str(tmp_path / "y.py"), content="x = 1\n")
    for payload, code in ((denied, 2), (allowed, 0)):
        proc = subprocess.run(
            [sys.executable, str(HOOKS_DIR / "secrets_check.py")],
            input=json.dumps(payload),
            capture_output=True,
            text=True,
            env=env,
        )
        assert proc.returncode == code, proc.stderr
    lines = [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines()]
    assert [line["verdict"] for line in lines] == ["block", "allow"]
    assert lines[0]["hook"] == "secrets_check" and lines[0]["tool"] == "Write"
    assert lines[0]["paths"] == [str(tmp_path / "x.py")] and lines[0]["reason"]
    assert lines[0]["event"] == "PreToolUse" and lines[0]["at"].endswith("Z")
    assert lines[1]["reason"] == ""
    # a hook that crashes fails closed and logs the block too
    proc = subprocess.run(
        [sys.executable, str(HOOKS_DIR / "protected_paths.py")],
        input="not json",
        capture_output=True,
        text=True,
        env=env,
    )
    assert proc.returncode == 2
    last = json.loads(log.read_text(encoding="utf-8").splitlines()[-1])
    assert last["verdict"] == "block" and "failed closed" in last["reason"]


# --- UTF-8 in and out whatever the console encoding (plugin 0.2.25) --------------------------
def test_read_payload_decodes_bytes_as_utf8():
    """Claude Code writes the payload as UTF-8; a text-mode stdin on Windows decoded it with
    the ANSI code page, and a project path with an accented letter matched no protected
    path (1.0.0 readiness review, 2026-09-26)."""
    import io

    payload = {"tool_name": "Edit", "tool_input": {"file_path": "C:/Users/Luís/proj/CLAUDE.md"}}
    raw = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    assert _common.read_payload(io.BytesIO(raw)) == payload
    assert _common.read_payload(io.StringIO('{"a": 1}')) == {"a": 1}
    with pytest.raises(ValueError):
        _common.read_payload(io.BytesIO(b"  \n"))


@pytest.mark.parametrize("encoding", ["utf-8", "cp1252"])
def test_protected_paths_denies_under_a_non_ascii_project_path_whatever_the_console(
    tmp_path, encoding
):
    """The hook reads its input from the byte stream: under a cp1252 console (Windows'
    default for a pipe) an edit of CLAUDE.md in ``…/Luís/proj`` was allowed (exit 0)."""
    project = tmp_path / "Luís" / "proj"
    project.mkdir(parents=True)
    (project / "CLAUDE.md").write_text("# x\n", encoding="utf-8")
    subprocess.run(["git", "init", "-q"], cwd=project, check=True)
    payload = pre("Edit", file_path=str(project / "CLAUDE.md"), old_string="x", new_string="y")
    proc = subprocess.run(
        [sys.executable, str(HOOKS_DIR / "protected_paths.py"), "--plugin-root", str(PLUGIN_ROOT)],
        input=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        capture_output=True,
        env={**os.environ, "CLAUDE_PROJECT_DIR": str(project), "PYTHONIOENCODING": encoding},
    )
    assert proc.returncode == 2, (encoding, proc.stderr)
    out = json.loads(proc.stdout.decode("utf-8"))
    assert out["hookSpecificOutput"]["permissionDecision"] == "deny"


def test_utf8_stdout_makes_a_cp1252_pipe_write_utf8(monkeypatch):
    """``review/cli.py prompt``, ``panel/cli.py prompt`` and ``pr/cli.py description`` carry
    ``≠`` and ``→``; on a cp1252 pipe they raised UnicodeEncodeError."""
    import io

    buffer = io.BytesIO()
    monkeypatch.setattr(sys, "stdout", io.TextIOWrapper(buffer, encoding="cp1252"))
    monkeypatch.setattr(sys, "stderr", io.StringIO())  # no reconfigure: left alone
    _common.utf8_stdout()
    sys.stdout.write("≠ →")
    sys.stdout.flush()
    assert buffer.getvalue() == "≠ →".encode()


def test_production_gate_fails_closed_on_a_production_flag_that_is_not_a_boolean(tmp_path):
    """``production: yes`` read as "no production declared" and switched the hook off (1.0.0
    readiness review, group A); now it is a config error, which the hook blocks on."""
    root, env, log = _gate_project(tmp_path)
    path = root / "sdlc.yaml"
    path.write_text(
        path.read_text(encoding="utf-8").replace("production: true", "production: yes"),
        encoding="utf-8",
    )
    with pytest.raises(_common_config_error()) as exc:
        _gate(root, env, "twine upload dist/*")
    assert "deploy.production is 'yes', not a boolean" in str(exc.value)
    (line,) = _log_lines(log)
    assert line["verdict"] == "block" and "fail closed" in line["reason"]


# --- the review panel's blindness (0.2.30) -------------------------------------------------
PANEL_HOOK = HOOKS_DIR / "panel_blind.py"


@pytest.fixture
def panel_project(tmp_path):
    """A project mid-panel: item 1 of phase (b) has the reviewer's verdict, not the
    advocate's yet (the window)."""
    (tmp_path / "sdlc.yaml").write_text("profile: standard\n", encoding="utf-8")
    panel = tmp_path / "changes" / "0001-sample" / "evidence" / "panel"
    panel.mkdir(parents=True)
    (panel / "b-1-reviewer.md").write_text("## Verdict\nkeep half-up\n", encoding="utf-8")
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "calc.py").write_text("x = 1\n", encoding="utf-8")
    return tmp_path, panel


def _blind(root, payload):
    return panel_blind.decide({**payload, "cwd": str(root)}, [], env=_env(root))


def test_panel_blind_refuses_a_read_of_a_verdict_in_its_window(panel_project):
    root, panel = panel_project
    decision = _blind(root, pre("Read", file_path=str(panel / "b-1-reviewer.md")))
    assert decision.block
    assert "b-1-reviewer.md is the reviewer's verdict on item 1" in decision.reason
    assert "b-1-advocate.md is missing" in decision.reason
    # Windows spelling and case of the same file
    spelled = str(panel / "B-1-Reviewer.md").replace("/", "\\")
    assert _blind(root, pre("Read", file_path=spelled)).block or os.name != "nt"
    # once the advocate has written, the conciliator reads both
    (panel / "b-1-advocate.md").write_text("## Verdict\nno objection\n", encoding="utf-8")
    assert not _blind(root, pre("Read", file_path=str(panel / "b-1-reviewer.md"))).block
    assert not _blind(root, pre("Read", file_path=str(panel / "b-1-advocate.md"))).block


def test_panel_blind_is_symmetric_and_leaves_other_files_alone(panel_project):
    root, panel = panel_project
    (panel / "b-1-reviewer.md").unlink()
    (panel / "b-1-advocate.md").write_text("## Verdict\nno objection\n", encoding="utf-8")
    decision = _blind(root, pre("Read", file_path=str(panel / "b-1-advocate.md")))
    assert decision.block and "the reviewer has not written its own yet" in decision.reason
    for other in (panel / "b-1-conciliator.json", panel / "b-items.json", root / "src/calc.py"):
        assert not _blind(root, pre("Read", file_path=str(other))).block, other


def test_panel_blind_follows_a_symlink_to_a_verdict(panel_project):
    root, panel = panel_project
    link = root / "notes.md"
    try:
        link.symlink_to(panel / "b-1-reviewer.md")
    except (OSError, NotImplementedError):
        pytest.skip("symlinks are not available here")
    assert _blind(root, pre("Read", file_path=str(link))).block


@pytest.mark.parametrize(
    ("grep", "blocked"),
    [
        ({}, True),  # the whole project, no filter: would read the verdict
        ({"path": "changes"}, True),
        ({"path": "changes/0001-sample/evidence/panel/b-1-reviewer.md"}, True),
        ({"type": "markdown"}, True),
        ({"glob": "*.md"}, True),
        ({"glob": "**/*.{md,py}"}, True),  # braces: not proven to exclude it
        ({"glob": "!*.py"}, True),  # a negation: not proven to exclude it
        ({"path": "changes", "glob": "**/evidence/panel/*.md"}, True),
        ({"path": "src"}, False),  # another folder
        ({"type": "py"}, False),  # limited to code
        ({"glob": "*.py"}, False),
        ({"glob": "**/*.json"}, False),
    ],
)
def test_panel_blind_refuses_only_a_grep_that_would_read_the_verdict(panel_project, grep, blocked):
    root, _panel = panel_project
    decision = _blind(root, pre("Grep", pattern="half-up", **grep))
    assert decision.block is blocked, (grep, decision.reason)
    if blocked:
        assert "b-1-reviewer.md" in decision.reason and 'glob: "*.py"' in decision.reason


def test_panel_blind_allows_every_grep_outside_a_window(panel_project):
    root, panel = panel_project
    (panel / "b-1-advocate.md").write_text("## Verdict\nno objection\n", encoding="utf-8")
    assert not _blind(root, pre("Grep", pattern="half-up")).block
    # Glob lists names, never contents: not the hook's
    assert not _blind(root, pre("Glob", pattern="**/*.md")).block


def test_panel_blind_script_blocks_logs_and_stays_silent_otherwise(panel_project):
    root, panel = panel_project
    log = root / "hook-log.jsonl"

    def run(payload):
        return subprocess.run(
            [sys.executable, str(PANEL_HOOK)],
            input=json.dumps({**payload, "cwd": str(root)}),
            capture_output=True,
            text=True,
            encoding="utf-8",
            env={**os.environ, "CLAUDE_PROJECT_DIR": str(root), "SDLC_HOOK_LOG": str(log)},
        )

    proc = run(pre("Read", file_path=str(root / "src" / "calc.py")))
    assert proc.returncode == 0 and proc.stdout == "" and not log.exists()  # no allow lines
    proc = run(pre("Read", file_path=str(panel / "b-1-reviewer.md")))
    assert proc.returncode == 2, proc.stderr
    out = json.loads(proc.stdout)["hookSpecificOutput"]
    assert out["permissionDecision"] == "deny" and "decision 21" in out["permissionDecisionReason"]
    (line,) = [json.loads(x) for x in log.read_text(encoding="utf-8").splitlines() if x.strip()]
    assert line["hook"] == "panel_blind" and line["verdict"] == "block"
    # input that is not JSON fails closed, like every PreToolUse hook
    bad = subprocess.run(
        [sys.executable, str(PANEL_HOOK)], input="not json", capture_output=True, text=True
    )
    assert bad.returncode == 2


def test_hooks_json_registers_the_panel_blindness_on_read_and_grep():
    data = json.loads((HOOKS_DIR / "hooks.json").read_text(encoding="utf-8"))
    entries = [
        e
        for e in data["hooks"]["PreToolUse"]
        if any("panel_blind.py" in h["args"][0] for h in e["hooks"])
    ]
    assert [e["matcher"] for e in entries] == ["Read|Grep|Bash|PowerShell|Write|Edit|MultiEdit"]


@pytest.mark.parametrize(
    ("command", "blocked"),
    [
        ("cat changes/0001-sample/evidence/panel/b-1-reviewer.md", True),
        ("type changes\\0001-sample\\evidence\\panel\\B-1-Reviewer.md", True),
        ("cat changes/0001-sample/evidence/panel/*", True),
        ("git show HEAD:changes/0001-sample/evidence/panel/b-1-reviewer.md", True),
        ("python plugin/panel/cli.py prompt --member advocate --item 1", False),
        ("python -m pytest", False),
        ("git status", False),
    ],
)
def test_panel_blind_refuses_a_shell_command_that_names_a_verdict(panel_project, command, blocked):
    root, _panel = panel_project
    for tool in ("Bash", "PowerShell"):
        decision = _blind(root, pre(tool, command=command))
        assert decision.block is blocked, (tool, command, decision.reason)
        if blocked:
            assert "b-1-reviewer.md" in decision.reason


def test_panel_blind_allows_shell_commands_outside_a_window(panel_project):
    root, panel = panel_project
    (panel / "b-1-advocate.md").write_text("## Verdict\nno objection\n", encoding="utf-8")
    cmd = "cat changes/0001-sample/evidence/panel/b-1-reviewer.md"
    assert not _blind(root, pre("Bash", command=cmd)).block


def _transcripts(tmp_path, agent_id, models, nested=True):
    """A session transcript and, as Claude Code 2.1.287 keeps it, the sub-agent's own one
    beside it (NOTES section 25); ``nested=False`` puts the sub-agent's file where the hook
    input's ``transcript_path`` points."""
    session = tmp_path / "sessions" / "s1.jsonl"
    session.parent.mkdir(parents=True)
    session.write_text("{}\n", encoding="utf-8")
    sub = (session.with_suffix("") / "subagents" if nested else session.parent) / (
        f"agent-{agent_id}.jsonl"
    )
    sub.parent.mkdir(parents=True, exist_ok=True)
    lines = [{"type": "user", "message": {"role": "user", "content": "brief"}}]
    lines += [{"type": "assistant", "message": {"model": m, "content": []}} for m in models]
    sub.write_text("\n".join(json.dumps(x) for x in lines) + "\n", encoding="utf-8")
    return session if nested else sub


@pytest.mark.parametrize("nested", [True, False])
@pytest.mark.parametrize("tool", ["Write", "Edit", "MultiEdit"])
def test_panel_blind_records_the_model_that_wrote_the_advocate_verdict(
    panel_project, tmp_path, tool, nested
):
    root, panel = panel_project
    transcript = _transcripts(tmp_path, "a1b2", ["claude-opus-5"], nested=nested)
    target = str(panel / "b-1-advocate.md")
    tool_input = (
        {"edits": [{"file_path": target, "old_string": "a", "new_string": "b"}]}
        if tool == "MultiEdit"
        else {"file_path": target, "content": "## Verdict\nno objection\n"}
    )
    payload = {
        **pre(tool, **tool_input),
        "agent_id": "a1b2",
        "agent_type": "sdlc:adversarial-reviewer",
        "transcript_path": str(transcript),
    }
    assert not _blind(root, payload).block  # recording never refuses the verdict
    record = json.loads((panel / "b-1-advocate.model.json").read_text(encoding="utf-8"))
    assert record["models"] == ["claude-opus-5"] and record["reason"] is None
    assert record["agent_type"] == "sdlc:adversarial-reviewer" and record["n"] == 1


def test_panel_blind_says_why_a_model_could_not_be_recorded(panel_project, tmp_path):
    root, panel = panel_project
    target = str(panel / "b-1-advocate.md")
    path = panel / "b-1-advocate.model.json"
    # the main session wrote the advocate's file itself: no sub-agent, no advocate
    assert not _blind(root, pre("Write", file_path=target, content="x")).block
    record = json.loads(path.read_text(encoding="utf-8"))
    assert record["models"] == [] and "main session" in record["reason"]
    # a sub-agent whose transcript is nowhere to be found
    payload = {
        **pre("Write", file_path=target, content="x"),
        "agent_id": "zz",
        "agent_type": "sdlc:adversarial-reviewer",
        "transcript_path": str(tmp_path / "nowhere" / "s.jsonl"),
    }
    assert not _blind(root, payload).block
    record = json.loads(path.read_text(encoding="utf-8"))
    assert record["models"] == [] and "transcript was not found" in record["reason"]


def test_panel_blind_refuses_a_tool_write_of_a_model_record(panel_project):
    root, panel = panel_project
    for tool in ("Write", "Edit"):
        decision = _blind(root, pre(tool, file_path=str(panel / "b-1-advocate.model.json")))
        assert decision.block and "only the panel_blind hook writes it" in decision.reason
    # an ordinary edit elsewhere is left alone, and writes no record
    assert not _blind(root, pre("Write", file_path=str(root / "src" / "calc.py"))).block
    assert not (panel / "b-1-reviewer.model.json").exists()


# --- shell guard (change 0002: protected_paths.py and test_file_lock.py police Edit/Write/
# MultiEdit/NotebookEdit only; shell_guard.py closes the identical Bash/PowerShell bypass) ----
GUARD_HOOK = HOOKS_DIR / "shell_guard.py"


def _bash(command: str, cwd: str) -> dict:
    return {**pre("Bash", command=command), "cwd": cwd}


@pytest.mark.parametrize(
    "command",
    [
        "python -c \"open('CLAUDE.md','w').write('x')\"",
        "echo x > sdlc.yaml",
        "echo x >> REVIEW.md",
        "cp notes.txt CLAUDE.md",
        "Set-Content -Path CLAUDE.md -Value x",
        "Remove-Item sdlc.yaml",
        '[IO.File]::WriteAllText("CLAUDE.md","x")',
    ],
)
def test_shell_guard_denies_a_bash_write_to_a_guardrail_file(project, command):
    d = shell_guard.decide(_bash(command, str(project)), [], env=_env(project))
    assert d.block, command
    assert "Protected path" in d.reason


def test_shell_guard_covers_the_powershell_tool_too(project):
    payload = {**_bash("Remove-Item CLAUDE.md", str(project)), "tool_name": "PowerShell"}
    d = shell_guard.decide(payload, [], env=_env(project))
    assert d.block and "Protected path" in d.reason


def test_shell_guard_denies_the_plugin_root_form_only_through_plugin_root(project):
    command = "rm plugin/hooks/protected_paths.py"
    without = shell_guard.decide(_bash(command, str(project)), [], env=_env(project))
    assert not without.block
    withit = shell_guard.decide(
        _bash(command, str(project)), ["--plugin-root", str(project)], env=_env(project)
    )
    assert withit.block and "SDLC plugin" in withit.reason


def test_shell_guard_denies_a_sdlc_yaml_protected_paths_entry(project):
    d = shell_guard.decide(_bash("echo x > src/gen/model.py", str(project)), [], env=_env(project))
    assert d.block and "src/gen" in d.reason


def test_shell_guard_denies_a_bash_write_to_a_locked_test_file(tmp_path):
    root, _ = _lock_project(tmp_path)
    payload = _bash("echo x > tests/test_calc.py", str(root))
    d = shell_guard.decide(payload, [], env={"CLAUDE_PROJECT_DIR": str(root)})
    assert d.block and "Test-file lock" in d.reason and "tests/test_calc.py" in d.reason


def test_shell_guard_ignores_a_locked_test_file_outside_a_fix(tmp_path):
    root, _ = _lock_project(tmp_path, change_type="feature")
    payload = _bash("echo x > tests/test_calc.py", str(root))
    d = shell_guard.decide(payload, [], env={"CLAUDE_PROJECT_DIR": str(root)})
    assert not d.block


@pytest.mark.parametrize(
    "command",
    [
        'git commit -m "note: echo x > CLAUDE.md"',
        'echo "> CLAUDE.md"',
        "grep -n x CLAUDE.md",
        "cat sdlc.yaml",
        "python -m pytest tests/test_hooks.py -k protected",
        "cmd 2>&1",
        "cmd > /dev/null",
        "git status",
        "npm run build",
        "npx some-package",
    ],
)
def test_shell_guard_allows_ordinary_commands(project, command):
    d = shell_guard.decide(_bash(command, str(project)), [], env=_env(project))
    assert not d.block, command


def test_shell_guard_allows_a_heredoc_blockquote_mentioning_a_guardrail_path(project):
    command = (
        "gh pr comment --body \"$(cat <<'EOF'\na blockquote mentioning > CLAUDE.md here\nEOF\n)\""
    )
    d = shell_guard.decide(_bash(command, str(project)), [], env=_env(project))
    assert not d.block


def test_shell_guard_resolves_a_relative_target_against_cwd(project):
    (project / "sub").mkdir()
    d = shell_guard.decide(_bash("echo x > CLAUDE.md", str(project / "sub")), [], env=_env(project))
    assert not d.block  # sub/CLAUDE.md is project content, not the root guardrail file


def test_shell_guard_resolves_after_a_cd_in_the_same_chain(project):
    (project / "sub").mkdir()
    allowed = shell_guard.decide(
        _bash("cd sub && echo x > CLAUDE.md", str(project)), [], env=_env(project)
    )
    assert not allowed.block  # sub/CLAUDE.md, not the root guardrail file
    denied = shell_guard.decide(
        _bash(f"cd sub && cd {project} && echo x > CLAUDE.md", str(project)), [], env=_env(project)
    )
    assert denied.block


def test_shell_guard_resolves_a_git_dash_c_target(tmp_path, project):
    other = tmp_path / "other"
    other.mkdir()
    elsewhere = shell_guard.decide(
        _bash(f"git -C {other} rm CLAUDE.md", str(project)), [], env=_env(project)
    )
    assert not elsewhere.block  # CLAUDE.md under `other`, not the project root
    here = shell_guard.decide(
        _bash(f"git -C {project} rm CLAUDE.md", str(other)), [], env=_env(project)
    )
    assert here.block


def test_shell_guard_git_dash_c_does_not_leak_into_a_later_chain_part(tmp_path, project):
    """Round 4 review finding: unlike `cd`, `git -C <dir>` changes the directory of that one
    git process only — it never persists to a later part of the same chain. A command that
    only *looks* like it writes under `other/` after a `git -C other ...` actually writes to
    the real cwd's CLAUDE.md, and the hook must deny it."""
    other = tmp_path / "other"
    other.mkdir()
    leaked = shell_guard.decide(
        _bash(f"git -C {other} status && echo x > CLAUDE.md", str(project)), [], env=_env(project)
    )
    assert leaked.block  # the echo writes the real project root's CLAUDE.md, not other/CLAUDE.md


@pytest.mark.parametrize(
    "command",
    [
        "echo x > $VAR",
        "echo x > $(name)",
        "echo x > `name`",
        "echo x > ~/CLAUDE.md",
        "echo x > CLAUDE.md*",
        "cd $DIR && echo x > CLAUDE.md",
    ],
)
def test_shell_guard_fails_closed_on_a_nonliteral_write_target(project, command):
    d = shell_guard.decide(_bash(command, str(project)), [], env=_env(project))
    assert d.block and "not a literal path" in d.reason


def test_shell_guard_allows_a_cd_to_a_nonliteral_directory_with_no_write_after_it(project):
    d = shell_guard.decide(_bash("cd $DIR", str(project)), [], env=_env(project))
    assert not d.block


# --- round 4 fix-request: the escalated git/inner-shell global-option bypasses (items 1-2) ----
@pytest.mark.parametrize(
    "command",
    [
        "git -c core.fileMode=false rm CLAUDE.md",
        "git --git-dir=.git rm CLAUDE.md",
        "git --work-tree=. checkout -- CLAUDE.md",
    ],
)
def test_shell_guard_sees_the_git_verb_after_a_global_option(project, command):
    d = shell_guard.decide(_bash(command, str(project)), [], env=_env(project))
    assert d.block, command


def test_shell_guard_sees_a_dash_c_preceded_by_another_global_option(tmp_path, project):
    other = tmp_path / "other"
    other.mkdir()
    elsewhere = shell_guard.decide(
        _bash(f"git -c x=y -C {other} rm CLAUDE.md", str(project)), [], env=_env(project)
    )
    assert not elsewhere.block  # CLAUDE.md under `other`, not the project root
    here = shell_guard.decide(
        _bash(f"git -c x=y -C {project} rm CLAUDE.md", str(other)), [], env=_env(project)
    )
    assert here.block


@pytest.mark.parametrize(
    "command",
    [
        "bash --norc -c 'echo x > CLAUDE.md'",
        "sh --posix -c 'echo x > CLAUDE.md'",
        "pwsh -NoProfile -Command 'Remove-Item CLAUDE.md'",
        "cmd /d /c 'echo x > CLAUDE.md'",
    ],
)
def test_shell_write_targets_sees_through_a_flag_before_the_inner_shell_s_c_token(command):
    assert shell_guard.shell_write_targets(command) == ["CLAUDE.md"]


# --- round 4 fix-request item 3: an ancestor directory of a guardrail is protected too --------
@pytest.mark.parametrize(
    ("command", "tool_name"),
    [
        ("rm -r -q .claude", "Bash"),
        ("git rm -r -q .claude", "Bash"),
        ("python -c \"import shutil; shutil.rmtree('.claude')\"", "Bash"),
        ("Remove-Item -Recurse -Force .claude", "PowerShell"),
    ],
)
def test_shell_guard_denies_deleting_a_directory_that_contains_a_guardrail(
    project, command, tool_name
):
    payload = {**_bash(command, str(project)), "tool_name": tool_name}
    d = shell_guard.decide(payload, [], env=_env(project))
    assert d.block, command


def test_shell_guard_denies_deleting_an_ancestor_of_a_sdlc_yaml_protected_paths_entry(tmp_path):
    (tmp_path / "sdlc.yaml").write_text(
        "profile: standard\nprotected_paths:\n  - docs/policy.md\n", encoding="utf-8"
    )
    d = shell_guard.decide(
        _bash("git rm -r -q docs", str(tmp_path)), [], env={"CLAUDE_PROJECT_DIR": str(tmp_path)}
    )
    assert d.block and "docs" in d.reason


# --- round 4 fix-request item 6-7: PowerShell backslash paths and named-parameter values ------
def test_shell_write_targets_keeps_backslash_literal_on_powershell():
    assert shell_guard.shell_write_targets("Set-Content .\\CLAUDE.md x", powershell=True) == [
        ".\\CLAUDE.md"
    ]
    assert shell_guard.shell_write_targets("Set-Content .\\CLAUDE.md x") == [".CLAUDE.md"]


def test_shell_guard_reads_a_backslash_path_on_powershell(project):
    payload = {**_bash("Set-Content .\\CLAUDE.md x", str(project)), "tool_name": "PowerShell"}
    d = shell_guard.decide(payload, [], env=_env(project))
    assert d.block


@pytest.mark.parametrize(
    ("command", "expected"),
    [
        ("Set-Content -Value x CLAUDE.md", ["CLAUDE.md"]),
        ('"x" | Out-File -Encoding utf8 CLAUDE.md', ["CLAUDE.md"]),
        ("Set-Content -Path:CLAUDE.md -Value x", ["CLAUDE.md"]),
        ("New-Item -ItemType File CLAUDE.md", ["CLAUDE.md"]),
    ],
)
def test_shell_write_targets_powershell_skips_a_named_parameter_s_value(command, expected):
    assert shell_guard.shell_write_targets(command) == expected


# --- round 4 fix-request item 8: the directory-change parser ----------------------------------
def test_shell_guard_resolves_cd_with_a_flag_before_the_directory(project):
    d = shell_guard.decide(
        _bash("cd -P .claude && python -c 1 > settings.json", str(project)), [], env=_env(project)
    )
    assert d.block


def test_shell_guard_fails_closed_on_cd_dash(project):
    d = shell_guard.decide(
        _bash("cd docs && cd - && echo x > CLAUDE.md", str(project)), [], env=_env(project)
    )
    assert d.block and "not a literal path" in d.reason


def test_shell_guard_recognises_sl_alias_and_skips_set_location_flags(project):
    d = shell_guard.decide(
        _bash("Set-Location -Path .claude; Set-Content settings.json x", str(project)),
        [],
        env=_env(project),
    )
    assert d.block


def test_shell_guard_fails_closed_on_popd_and_pop_location(project):
    d = shell_guard.decide(
        _bash("pushd docs && popd && echo x > CLAUDE.md", str(project)), [], env=_env(project)
    )
    assert d.block and "not a literal path" in d.reason


# --- round 4 fix-request item 9: shell structure that hides the head word ---------------------
@pytest.mark.parametrize(
    "command",
    [
        "git status & git rm -q CLAUDE.md",
        "(git rm -q CLAUDE.md)",
        "{ git rm -q CLAUDE.md; }",
        "if true; then git rm -q CLAUDE.md; fi",
        "GIT_TRACE=0 git rm -q CLAUDE.md",
    ],
)
def test_shell_write_targets_sees_through_subshells_groups_and_assignments(command):
    assert shell_guard.shell_write_targets(command) == ["CLAUDE.md"]


def test_shell_guard_denies_a_write_inside_a_subshell_cd(project):
    d = shell_guard.decide(
        _bash("(cd .claude && python -c 1 > settings.json)", str(project)), [], env=_env(project)
    )
    assert d.block


# --- round 4 fix-request item 10: heredocs and here-strings, quote-aware ----------------------
def test_shell_write_targets_a_heredoc_word_inside_a_quote_is_not_a_heredoc():
    assert shell_guard.shell_write_targets("git log -1 --format='<<EOF'\ngit rm -q CLAUDE.md") == [
        "CLAUDE.md"
    ]


def test_shell_write_targets_a_here_string_is_not_a_heredoc():
    assert shell_guard.shell_write_targets('python -c 1 <<< "x"\ngit rm -q CLAUDE.md') == [
        "CLAUDE.md"
    ]


# --- round 4 fix-request item 11: brace expansion and git pathspec magic ----------------------
def test_shell_guard_fails_closed_on_brace_expansion(project):
    d = shell_guard.decide(
        _bash("git rm -q {CLAUDE,README}.md", str(project)), [], env=_env(project)
    )
    assert d.block and "not a literal path" in d.reason


@pytest.mark.parametrize(
    "command",
    [
        "git rm -q ':(icase)claude.md'",
        "git rm -q ':/CLAUDE.md'",
    ],
)
def test_shell_guard_fails_closed_on_git_pathspec_magic(project, command):
    d = shell_guard.decide(_bash(command, str(project)), [], env=_env(project))
    assert d.block and "not a literal path" in d.reason


# --- round 4 fix-request item 12: `>&WORD` is a file redirect, not only an fd dup -------------
def test_shell_write_targets_parses_ampersand_word_as_a_file_redirect():
    assert shell_guard.shell_write_targets("python -c 1 >&CLAUDE.md") == ["CLAUDE.md"]
    assert shell_guard.shell_write_targets("cmd 2>&1") == []
    assert shell_guard.shell_write_targets("cmd >&2") == []


# --- round 4 fix-request item 13: more programs that write a named file via their options ----
@pytest.mark.parametrize(
    ("command", "expected"),
    [
        ("git diff --output=CLAUDE.md", ["CLAUDE.md"]),
        ("git checkout main CLAUDE.md", ["CLAUDE.md"]),
        ("git config --file sdlc.yaml a.b c", ["sdlc.yaml"]),
        ("python -m json.tool x.json sdlc.yaml", ["sdlc.yaml"]),
        ("python -m pytest --basetemp=.claude", [".claude"]),
        ("gh release download 1 -O CLAUDE.md", ["CLAUDE.md"]),
    ],
)
def test_shell_write_targets_more_idioms(command, expected):
    assert shell_guard.shell_write_targets(command) == expected


def test_shell_write_targets_plain_pytest_run_is_not_a_write():
    assert shell_guard.shell_write_targets("python -m pytest") == []


def test_shell_guard_allows_the_framework_s_own_evidence_diff_command(project):
    command = "git diff --stat --patch --output=changes/0002-slug/evidence/diff-c.patch main...HEAD"
    d = shell_guard.decide(_bash(command, str(project)), [], env=_env(project))
    assert not d.block


# --- round 4 fix-request item 14: a Git Bash absolute path maps onto a drive-letter root ------
def test_resolve_maps_a_git_bash_absolute_path_onto_a_drive_letter_root():
    assert shell_guard._resolve("C:/p", "/c/p/CLAUDE.md") == "c:/p/CLAUDE.md"
    assert shell_guard._resolve("C:/p", "/c/p") == "c:/p"
    assert shell_guard._resolve("/home/u/proj", "/etc/passwd") == "/etc/passwd"


# --- round 4 fix-request item 15: scan only the interpreter's own code argument ---------------
@pytest.mark.parametrize(
    "command",
    [
        "git commit -m \"deny open('CLAUDE.md','w') via Bash\"",
        "gh pr comment 144 --body \"fs.writeFileSync('sdlc.yaml','x')\"",
        "grep -n \"open('CLAUDE.md','w')\" tests/test_hooks.py",
        "git status # then > CLAUDE.md",
    ],
)
def test_shell_guard_does_not_false_deny_text_that_merely_mentions_a_write_call(project, command):
    d = shell_guard.decide(_bash(command, str(project)), [], env=_env(project))
    assert not d.block, command


# --- round 4 fix-request item 16: PowerShell's $null is the null device ----------------------
@pytest.mark.parametrize("command", ["git fetch origin 2>$null", "python -m pytest > $null"])
def test_shell_guard_allows_null_on_powershell(project, command):
    payload = {**_bash(command, str(project)), "tool_name": "PowerShell"}
    d = shell_guard.decide(payload, [], env=_env(project))
    assert not d.block, command


# --- round 4 fix-request item 4: two-argument interpreter calls check the destination ---------
@pytest.mark.parametrize(
    ("command", "expected"),
    [
        ("python -c \"shutil.copy('README.md', 'CLAUDE.md')\"", ["CLAUDE.md"]),
        ("python -c \"os.rename('a.txt', 'CLAUDE.md')\"", ["CLAUDE.md"]),
        ("python -c \"os.replace('a.txt', 'CLAUDE.md')\"", ["CLAUDE.md"]),
        ("node -e \"fs.copyFileSync('a.txt', 'CLAUDE.md')\"", ["CLAUDE.md"]),
        ("node -e \"fs.renameSync('a.txt', 'CLAUDE.md')\"", ["CLAUDE.md"]),
        ("node -e \"fs.cpSync('a.txt', 'CLAUDE.md')\"", ["CLAUDE.md"]),
        ('[IO.File]::Copy("a.txt","CLAUDE.md")', ["CLAUDE.md"]),
        ('[IO.File]::Move("a.txt","CLAUDE.md")', ["CLAUDE.md"]),
    ],
)
def test_shell_write_targets_two_argument_calls_take_the_destination(command, expected):
    assert shell_guard.shell_write_targets(command) == expected


# --- round 4 fix-request item 5: python open() write-mode edge cases --------------------------
@pytest.mark.parametrize(
    "command",
    [
        "python -c \"open('CLAUDE.md', mode='w').write('x')\"",
        "python -c \"m='w'; open('CLAUDE.md', m).write('x')\"",
        "python -c \"open(r'CLAUDE.md','w').write('x')\"",
        "python -c \"Path('CLAUDE.md').open('w').write('x')\"",
        "python -c \"os.open('CLAUDE.md', os.O_WRONLY|os.O_TRUNC)\"",
    ],
)
def test_shell_write_targets_python_open_write_forms(command):
    assert shell_guard.shell_write_targets(command) == ["CLAUDE.md"]


@pytest.mark.parametrize(
    "command",
    [
        "python -c \"open('CLAUDE.md').read()\"",
        "python -c \"open('CLAUDE.md', encoding='utf-8').read()\"",
        "python -c \"Path('CLAUDE.md').open().read()\"",
    ],
)
def test_shell_write_targets_python_open_read_forms_are_not_writes(command):
    assert shell_guard.shell_write_targets(command) == []


@pytest.mark.parametrize(
    ("command", "expected"),
    [
        ("echo x > CLAUDE.md", ["CLAUDE.md"]),
        ("echo x >> CLAUDE.md", ["CLAUDE.md"]),
        ("echo x >| CLAUDE.md", ["CLAUDE.md"]),
        ("cmd &> CLAUDE.md", ["CLAUDE.md"]),
        ("cmd &>> CLAUDE.md", ["CLAUDE.md"]),
        ("cmd <> CLAUDE.md", ["CLAUDE.md"]),
        ("tee CLAUDE.md", ["CLAUDE.md"]),
        ("tee -a CLAUDE.md", ["CLAUDE.md"]),
        ("cp a.txt CLAUDE.md", ["CLAUDE.md"]),
        ("mv a.txt CLAUDE.md", ["CLAUDE.md"]),
        ("install a.txt CLAUDE.md", ["CLAUDE.md"]),
        ("ln -s a.txt CLAUDE.md", ["CLAUDE.md"]),
        ("rsync a.txt CLAUDE.md", ["CLAUDE.md"]),
        ("rm CLAUDE.md", ["CLAUDE.md"]),
        ("truncate -s0 CLAUDE.md", ["CLAUDE.md"]),
        ("touch CLAUDE.md", ["CLAUDE.md"]),
        ("sed -i s/a/b/ CLAUDE.md", ["CLAUDE.md"]),
        ("perl -i -pe s/a/b/ CLAUDE.md", ["CLAUDE.md"]),
        ("dd of=CLAUDE.md", ["CLAUDE.md"]),
        ("git checkout -- CLAUDE.md", ["CLAUDE.md"]),
        ("git restore CLAUDE.md", ["CLAUDE.md"]),
        ("git rm CLAUDE.md", ["CLAUDE.md"]),
        ("git mv a.txt CLAUDE.md", ["a.txt", "CLAUDE.md"]),
        ("git apply CLAUDE.md", ["CLAUDE.md"]),
        ("python -c \"open('CLAUDE.md','w').write('x')\"", ["CLAUDE.md"]),
        ("python -c \"Path('CLAUDE.md').write_text('x')\"", ["CLAUDE.md"]),
        ("python -c \"os.remove('CLAUDE.md')\"", ["CLAUDE.md"]),
        ("python -c \"shutil.move('x', 'CLAUDE.md')\"", ["CLAUDE.md"]),
        ("node -e \"fs.writeFileSync('CLAUDE.md', 'x')\"", ["CLAUDE.md"]),
        ("Set-Content -Path CLAUDE.md -Value x", ["CLAUDE.md"]),
        ("Add-Content CLAUDE.md x", ["CLAUDE.md"]),
        ("Out-File -FilePath CLAUDE.md", ["CLAUDE.md"]),
        ("New-Item CLAUDE.md", ["CLAUDE.md"]),
        ("Copy-Item a.txt -Destination CLAUDE.md", ["CLAUDE.md"]),
        ("Move-Item a.txt CLAUDE.md", ["a.txt", "CLAUDE.md"]),
        ("Remove-Item CLAUDE.md", ["CLAUDE.md"]),
        ('[IO.File]::WriteAllText("CLAUDE.md","x")', ["CLAUDE.md"]),
    ],
)
def test_shell_write_targets_idioms(command, expected):
    assert shell_guard.shell_write_targets(command) == expected


@pytest.mark.parametrize(
    "command",
    [
        'git commit -m "note: echo x > CLAUDE.md"',
        'echo "> CLAUDE.md"',
        "grep -n x CLAUDE.md",
        "cat sdlc.yaml",
        "python -m pytest tests/test_hooks.py -k protected",
        "cmd 2>&1",
        "git status",
        "npm run build",
    ],
)
def test_shell_write_targets_negative_list(command):
    assert shell_guard.shell_write_targets(command) == []


def test_shell_write_targets_sees_through_wrappers_and_inner_shells():
    for command in (
        "sudo rm CLAUDE.md",
        "nohup rm CLAUDE.md",
        "time rm CLAUDE.md",
        "env rm CLAUDE.md",
        'bash -c "echo x > CLAUDE.md"',
        "sh -c 'echo x > CLAUDE.md'",
        'cmd /c "echo x > CLAUDE.md"',
        "pwsh -Command 'Remove-Item CLAUDE.md'",
    ):
        assert shell_guard.shell_write_targets(command) == ["CLAUDE.md"], command


def test_shell_write_targets_splits_a_chain_only_on_the_documented_operators():
    assert shell_guard.shell_write_targets("rm a.txt; echo x > CLAUDE.md") == [
        "a.txt",
        "CLAUDE.md",
    ]
    assert shell_guard.shell_write_targets("rm a.txt && echo x > CLAUDE.md") == [
        "a.txt",
        "CLAUDE.md",
    ]
    assert shell_guard.shell_write_targets("rm a.txt || echo x > CLAUDE.md") == [
        "a.txt",
        "CLAUDE.md",
    ]
    assert shell_guard.shell_write_targets("rm a.txt | rm CLAUDE.md") == ["a.txt", "CLAUDE.md"]


def test_shell_guard_end_to_end_blocks_with_exit_2(project, tmp_path):
    log_path = tmp_path / "hook-log.jsonl"
    proc = subprocess.run(
        [sys.executable, str(GUARD_HOOK)],
        input=json.dumps(_bash("echo x > sdlc.yaml", str(project))),
        capture_output=True,
        text=True,
        env={**os.environ, "CLAUDE_PROJECT_DIR": str(project), "SDLC_HOOK_LOG": str(log_path)},
    )
    assert proc.returncode == 2, proc.stderr
    out = json.loads(proc.stdout)
    assert out["hookSpecificOutput"]["permissionDecision"] == "deny"
    assert "Protected path" in proc.stderr
    log_line = json.loads(log_path.read_text("utf-8").strip())
    assert log_line["hook"] == "shell_guard" and log_line["verdict"] == "block"


def test_shell_guard_end_to_end_is_silent_when_allowed(project, tmp_path):
    log_path = tmp_path / "hook-log.jsonl"
    proc = subprocess.run(
        [sys.executable, str(GUARD_HOOK)],
        input=json.dumps(_bash("echo hi", str(project))),
        capture_output=True,
        text=True,
        env={**os.environ, "CLAUDE_PROJECT_DIR": str(project), "SDLC_HOOK_LOG": str(log_path)},
    )
    assert proc.returncode == 0 and proc.stdout == "" and proc.stderr == ""
    assert not log_path.exists()


def test_hooks_json_registers_shell_guard_on_bash_and_powershell():
    data = json.loads((HOOKS_DIR / "hooks.json").read_text(encoding="utf-8"))
    entries = [
        e
        for e in data["hooks"]["PreToolUse"]
        if any("shell_guard.py" in h["args"][0] for h in e["hooks"])
    ]
    assert len(entries) == 1 and entries[0]["matcher"] == "Bash|PowerShell"
    (handler,) = entries[0]["hooks"]
    assert "if" not in handler
    assert handler["args"][1:] == ["--plugin-root", "${CLAUDE_PLUGIN_ROOT}"]
    assert handler["timeout"] == 30
