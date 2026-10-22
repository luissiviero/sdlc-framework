"""``python tasks.py verify`` and docs-lint check 13 (ROADMAP R65, part 4; choice 253).

Layer 1 (temporary files): the commands read from ``sdlc.yaml``, split at ``&&`` and run with
this interpreter; every step run and its verdict printed, a red one failing the task; check
13, CLAUDE.md's verifying lines against ``sdlc.yaml: commands``.
Layer 2 (this repository): CLAUDE.md quotes this repository's ``sdlc.yaml`` word for word.
"""

from __future__ import annotations

import sys
from pathlib import Path

import tasks

SDLC = (
    "profile: standard\n"
    "commands:\n"
    '  build: "python -m compileall -q plugin tests tasks.py"\n'
    '  test: "python -m pytest"\n'
    '  lint: "python -m ruff check . && python -m ruff format --check ."\n'
)
CLAUDE = (
    "# Repo\n\n## Commands\n- Test: `python -m pytest -x` (not the section check 13 reads)\n\n"
    "## Verifying your work\n"
    "- Build: `python -m compileall -q plugin tests tasks.py` (no output)\n"
    "- Test: `python -m pytest` (all green)\n"
    "- Lint: `python -m ruff check . && python -m ruff format --check .` (zero warnings)\n"
    "Run all three.\n\n## Next\n- Build: `ignored`\n"
)


def _write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")
    return path


def test_the_commands_are_read_from_sdlc_yaml(tmp_path):
    assert tasks.read_commands(_write(tmp_path / "sdlc.yaml", SDLC)) == {
        "build": "python -m compileall -q plugin tests tasks.py",
        "test": "python -m pytest",
        "lint": "python -m ruff check . && python -m ruff format --check .",
    }
    assert tasks.read_commands(_write(tmp_path / "empty.yaml", "commands:\n  test: ''\n")) == {
        "build": "",
        "test": "",
        "lint": "",
    }


def test_a_command_runs_as_argument_lists_with_this_interpreter():
    assert tasks.command_steps("python -m ruff check . && python -m ruff format --check .") == [
        [sys.executable, "-m", "ruff", "check", "."],
        [sys.executable, "-m", "ruff", "format", "--check", "."],
    ]
    assert tasks.command_steps("make 'a b' && ") == [["make", "a b"]]


def test_verify_runs_every_step_and_fails_on_a_red_one(monkeypatch, capsys):
    ran: list[str] = []
    monkeypatch.setattr(
        tasks,
        "read_commands",
        lambda path=None: {
            "build": "python -c pass",
            "test": "python -m pytest",
            "lint": 'python -c "import sys; sys.exit(3)"',
        },
    )
    monkeypatch.setattr(tasks, "task_docs_lint", lambda: ran.append("docs-lint") or 0)
    monkeypatch.setattr(tasks, "task_test", lambda: ran.append("test") or 0)
    monkeypatch.setattr(tasks.shutil, "which", lambda name: None)
    assert tasks.main(["verify"]) == 1
    assert ran == ["docs-lint", "test"]
    out = capsys.readouterr().out.splitlines()
    assert out[-5:] == [
        "verify: build: ok",
        "verify: lint: FAIL",
        "verify: docs-lint: ok",
        "verify: test: ok",
        "verify: plugin validate: not run (no command or no claude CLI)",
    ]


def test_verify_runs_another_test_command_as_written_and_validates_with_the_cli(
    monkeypatch, capsys
):
    calls: list[list[str]] = []
    monkeypatch.setattr(
        tasks,
        "read_commands",
        lambda path=None: {"build": "", "test": "python -m unittest", "lint": ""},
    )
    monkeypatch.setattr(tasks, "task_docs_lint", lambda: 0)
    monkeypatch.setattr(tasks, "task_test", lambda: 1)
    monkeypatch.setattr(tasks.shutil, "which", lambda name: "/bin/claude")
    monkeypatch.setattr(tasks.subprocess, "call", lambda args, cwd=None: calls.append(args) or 0)
    assert tasks.task_verify() == 0
    assert calls == [[sys.executable, "-m", "unittest"], ["/bin/claude", "plugin", "validate", "."]]
    assert "verify: build: not run (no command or no claude CLI)" in capsys.readouterr().out


def test_check_13_compares_the_verifying_lines_with_sdlc_yaml(tmp_path):
    _write(tmp_path / "sdlc.yaml", SDLC)
    _write(tmp_path / "CLAUDE.md", CLAUDE)
    assert tasks.verify_line_problems(tmp_path) == []
    _write(
        tmp_path / "CLAUDE.md",
        CLAUDE.replace("tests tasks.py` (no", "tests tasks.py .github/scripts` (no").replace(
            "- Test: `python -m pytest` (all green)\n", ""
        ),
    )
    assert tasks.verify_line_problems(tmp_path) == [
        "commands: CLAUDE.md:7: `python -m compileall -q plugin tests tasks.py .github/scripts` "
        "differs from sdlc.yaml commands.build `python -m compileall -q plugin tests tasks.py`",
        'commands: CLAUDE.md has no "- Test:" line under "## Verifying your work"',
    ]
    failures, _ = tasks.lint_docs(tmp_path / "docs", tmp_path, pin="2.1.304")
    assert 'commands: CLAUDE.md has no "- Test:" line under "## Verifying your work"' in failures


def test_check_13_reads_nothing_without_both_files(tmp_path):
    _write(tmp_path / "CLAUDE.md", CLAUDE)
    assert tasks.verify_line_problems(tmp_path) == []


# --- layer 2: this repository -------------------------------------------------------------------


def test_claude_md_quotes_this_repositorys_commands():
    assert tasks.verify_line_problems(tasks.ROOT) == []
