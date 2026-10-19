"""The runner preparation of this repository's own checks (workflow framework-checks.yml;
.github/scripts/framework_checks_runner.py, choice 235): git's automatic maintenance off on
every runner, Defender's real-time scan off on Windows, and a setting that cannot be applied
never turns the job red. The commands are recorded, never run: a test must not change the
machine's global git config or its antivirus."""

from __future__ import annotations

import importlib.util
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / ".github" / "scripts" / "framework_checks_runner.py"
spec = importlib.util.spec_from_file_location("framework_checks_runner", SCRIPT)
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


def recorder(returncode: int = 0, stdout: str = "", stderr: str = "", raises=None):
    calls: list[list[str]] = []

    def run(command, **kwargs):
        calls.append(list(command))
        if raises is not None:
            raise raises
        return subprocess.CompletedProcess(command, returncode, stdout, stderr)

    return calls, run


def test_every_runner_turns_git_s_automatic_maintenance_off_and_only_windows_defender():
    linux = runner.plan(windows=False)
    windows = runner.plan(windows=True)
    git_steps = [
        ["git", "config", "--global", "maintenance.auto", "false"],
        ["git", "config", "--global", "gc.auto", "0"],
    ]
    assert [command for _what, command in linux] == git_steps
    assert [command for _what, command in windows][:2] == git_steps
    (defender,) = [command for _what, command in windows][2:]
    assert defender[:4] == ["powershell", "-NoProfile", "-NonInteractive", "-Command"]
    assert "Set-MpPreference -DisableRealtimeMonitoring $true" in defender[4]


def test_the_script_applies_its_plan_and_says_so(capsys):
    calls, run = recorder(stdout="True\n")
    assert runner.main(["--windows", "yes"], run=run) == 0
    assert calls == [command for _what, command in runner.plan(windows=True)]
    out = capsys.readouterr().out
    assert "git maintenance.auto=false: applied" in out
    assert "Defender real-time scan off: applied (True)" in out


def test_a_setting_that_cannot_be_applied_is_reported_and_the_step_stays_green(capsys):
    _calls, refused = recorder(returncode=1, stderr="Access denied.\r\n")
    assert runner.main(["--windows", "yes"], run=refused) == 0
    assert "Defender real-time scan off: not applied (exit 1: Access denied.)" in (
        capsys.readouterr().out
    )
    _calls, missing = recorder(raises=FileNotFoundError("powershell"))
    assert runner.main(["--windows", "no"], run=missing) == 0
    assert "gc.auto=0: not applied (FileNotFoundError: powershell)" in capsys.readouterr().out


def test_a_dry_run_changes_nothing(capsys):
    calls, run = recorder()
    assert runner.main(["--dry-run", "--windows", "yes"], run=run) == 0
    assert calls == []
    out = capsys.readouterr().out
    assert "git config --global maintenance.auto false" in out and "Set-MpPreference" in out
