"""Layer-1 tests for plugin/gate/preflight.py (build guide step 18): refuses auto-accept when
any precondition is missing, allows it on the initialised fixture, never names bypass mode."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from gate import preflight
from state import status

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "sample-python-project"
INIT = ROOT / "plugin" / "init" / "sdlc_init.py"
PREFLIGHT = ROOT / "plugin" / "gate" / "preflight.py"


def _init(root: Path) -> None:
    subprocess.run(
        [sys.executable, str(INIT), "--root", str(root), "--profile", "standard"],
        check=True,
        capture_output=True,
        text=True,
    )


def _project_skills(root: Path, names=preflight.POLICY_SKILLS) -> None:
    """Project overrides under .claude/skills/ (the plugin ships its own; both paths count)."""
    for name in names:
        path = root / ".claude" / "skills" / name / "SKILL.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"---\nname: {name}\ndescription: test\n---\n# {name}\n", encoding="utf-8")


@pytest.fixture
def project(tmp_path):
    root = tmp_path / "proj"
    shutil.copytree(FIXTURE, root)
    _init(root)
    _project_skills(root)
    return root


def _names(report, ok):
    return sorted(ch["name"] for ch in report["checks"] if ch["ok"] is ok)


def test_refuses_on_the_raw_fixture(tmp_path):
    root = tmp_path / "raw"
    shutil.copytree(FIXTURE, root)
    report = preflight.run_preflight(root, ROOT)
    assert report["allow"] is False and report["permission_mode"] == "default"
    assert {"sdlc_yaml", "settings"} <= set(_names(report, False))
    assert "test_target" not in [ch["name"] for ch in report["checks"]]  # never runs blind


def test_allows_on_the_initialised_fixture(project):
    report = preflight.run_preflight(project, ROOT)
    assert report["allow"] is True, report["reasons"]
    assert report["permission_mode"] == "acceptEdits" and report["never"] == "bypassPermissions"
    assert _names(report, True) == sorted(
        ["sdlc_yaml", "claude_md", "policy_skills", "hooks", "settings", "paused", "test_target"]
    )
    assert report["checks"][-1]["details"]["run"]["exit_code"] == 0


@pytest.mark.parametrize(
    "break_it, name, fragment",
    [
        (lambda r: (r / "CLAUDE.md").unlink(), "claude_md", "CLAUDE.md is missing"),
        (
            lambda r: (r / "CLAUDE.md").write_text("# p\n## Commands\n- none\n", encoding="utf-8"),
            "claude_md",
            "does not name the build, test, lint command",
        ),
        (
            lambda r: (r / "sdlc.yaml").write_text(
                (r / "sdlc.yaml")
                .read_text(encoding="utf-8")
                .replace("paused: false", "paused: true"),
                encoding="utf-8",
            ),
            "paused",
            "paused",
        ),
    ],
)
def test_refuses_when_a_precondition_is_missing(project, break_it, name, fragment):
    break_it(project)
    report = preflight.run_preflight(project, ROOT)
    assert report["allow"] is False and name in _names(report, False)
    failed = next(ch for ch in report["checks"] if ch["name"] == name)
    assert fragment in failed["reason"] and failed["need"]


def test_refuses_when_a_policy_skill_is_missing_everywhere(project, tmp_path):
    shutil.rmtree(project / ".claude" / "skills" / "security-baseline")
    assert preflight.run_preflight(project, ROOT)["allow"] is True  # the plugin ships it
    bare_plugin = tmp_path / "plugin-without-skills"
    (bare_plugin / "plugin").mkdir(parents=True)
    shutil.copytree(ROOT / "plugin" / "hooks", bare_plugin / "plugin" / "hooks")
    report = preflight.run_preflight(project, bare_plugin)
    failed = next(ch for ch in report["checks"] if ch["name"] == "policy_skills")
    assert report["allow"] is False and failed["details"]["missing"] == ["security-baseline"]
    assert failed["details"]["found"]["coding-standards"] == "project override"


def test_refuses_when_settings_allow_bypass_or_lack_a_deny_rule(project):
    path = project / ".claude" / "settings.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    data["permissions"]["disableBypassPermissionsMode"] = "enable"
    data["permissions"]["deny"].remove("Edit(CLAUDE.md)")
    del data["enabledPlugins"]
    path.write_text(json.dumps(data), encoding="utf-8")
    report = preflight.run_preflight(project, ROOT)
    failed = next(ch for ch in report["checks"] if ch["name"] == "settings")
    assert failed["details"]["problems"] == [
        "permissions.disableBypassPermissionsMode is not 'disable'",
        "deny rule Edit(CLAUDE.md) missing",
        "enabledPlugins does not enable sdlc@sdlc-framework",
    ]


def test_refuses_when_the_test_target_is_red(project, monkeypatch):
    monkeypatch.setenv("SAMPLE_FAIL", "1")
    report = preflight.run_preflight(project, ROOT)
    assert report["allow"] is False and _names(report, False) == ["test_target"]
    assert "SAMPLE_FAIL" in report["checks"][-1]["details"]["run"]["output"]


def test_refuses_without_python_on_path_or_hooks(project, monkeypatch, tmp_path):
    monkeypatch.setattr(preflight.shutil, "which", lambda name: None)
    report = preflight.run_preflight(project, ROOT)
    hooks = next(ch for ch in report["checks"] if ch["name"] == "hooks")
    assert not hooks["ok"] and "PATH" in hooks["reason"]
    monkeypatch.undo()
    fake_plugin = tmp_path / "plugin-copy"
    shutil.copytree(ROOT / "plugin", fake_plugin / "plugin")
    (fake_plugin / "plugin" / "hooks" / "secrets_check.py").unlink()
    report = preflight.run_preflight(project, fake_plugin)
    hooks = next(ch for ch in report["checks"] if ch["name"] == "hooks")
    assert not hooks["ok"] and "secrets_check.py" in hooks["reason"]
    (fake_plugin / "plugin" / "hooks" / "hooks.json").unlink()
    report = preflight.run_preflight(project, fake_plugin)
    assert "not found" in next(ch for ch in report["checks"] if ch["name"] == "hooks")["reason"]


def test_classification_reported_for_a_change(project):
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "plugin/state/cli.py"),
            "new-change",
            "--root",
            str(project),
            "--title",
            "X",
        ],
        check=True,
        capture_output=True,
    )
    report = preflight.run_preflight(project, ROOT, "0001")
    assert report["change"] == {
        "change_id": "0001",
        "classification": None,
        "iteration_cap": 3,
        "iterations_so_far": 0,
        "verdict_file": "adversarial-review-b.json",
    }
    verdict = project / "changes" / "0001-x" / "evidence" / "adversarial-review-b.json"
    verdict.write_text(
        json.dumps({"verdict": "continue", "classification": "non-routine", "head": "abc1234"})
    )
    report = preflight.run_preflight(project, ROOT, "0001")
    assert report["change"]["classification"] == "non-routine"
    assert report["change"]["iteration_cap"] == 2 and report["allow"] is True  # tightens only


def _new_change(project: Path) -> Path:
    subprocess.run(
        [sys.executable, str(ROOT / "plugin/state/cli.py"), "new-change", "--root", str(project),
         "--title", "X"],
        check=True,
        capture_output=True,
    )  # fmt: skip
    return project / "changes" / "0001-x"


def test_refuses_a_parked_change(project):
    """The park is the owner's item and the run must not start under it. The check lives
    here, not in the command's prose: the ninth live run (2026-09-22, phase (c)) had the CI
    guard let a change through and the session refuse it on its own reading of status.yaml.
    Nothing is run under a park, the test target included."""
    change = _new_change(project)
    st = status.read_status(change)
    st.set_phase("b")
    st.park("open_concerns: 1 open")
    status.write_status(change, st)
    report = preflight.run_preflight(project, ROOT, "0001")
    assert report["allow"] is False and report["permission_mode"] == "default"
    assert report["reasons"] == ["parked: open_concerns: 1 open"]
    parked = next(ch for ch in report["checks"] if ch["name"] == "parked")
    assert "/sdlc-fix 0001" in parked["need"]
    assert "test_target" not in [ch["name"] for ch in report["checks"]]


def test_a_park_that_a_later_gate_result_lifted_does_not_refuse(project):
    """status.yaml as plugins before 0.2.6 wrote it: gate (b) passed, the reason kept."""
    change = _new_change(project)
    st = status.read_status(change)
    st.set_phase("b")
    st.park("open_concerns: stale")
    st.gate.result = "passed"
    status.write_status(change, st)
    report = preflight.run_preflight(project, ROOT, "0001")
    assert report["allow"] is True
    assert next(ch for ch in report["checks"] if ch["name"] == "parked")["ok"] is True


def test_a_missing_change_refuses(project):
    report = preflight.run_preflight(project, ROOT, "0042")
    assert report["allow"] is False
    assert report["reasons"] == ["parked: no change folder for id 0042"]


def test_phases_d_and_e_skip_the_test_target(project, monkeypatch):
    """(d) judges the suite itself and (e) ships what (d) judged: their preflight checks the
    guardrails and the park, never the tests. (c) still needs the suite green to lean on."""
    monkeypatch.setenv("SAMPLE_FAIL", "1")
    for phase in ("d", "e"):
        report = preflight.run_preflight(project, ROOT, phase=phase)
        assert report["allow"] is True and report["phase"] == phase
        assert "test_target" not in [ch["name"] for ch in report["checks"]]
    report = preflight.run_preflight(project, ROOT, phase="c")
    assert report["allow"] is False and _names(report, False) == ["test_target"]


def test_preflight_cli_exit_codes(project):
    proc = subprocess.run(
        [sys.executable, str(PREFLIGHT), "--root", str(project)], capture_output=True, text=True
    )
    assert proc.returncode == 0, proc.stderr
    assert json.loads(proc.stdout)["permission_mode"] == "acceptEdits"
    (project / "CLAUDE.md").unlink()
    proc = subprocess.run(
        [sys.executable, str(PREFLIGHT), "--root", str(project)], capture_output=True, text=True
    )
    assert proc.returncode == 4 and json.loads(proc.stdout)["allow"] is False


def test_no_agent_command_or_skill_mentions_bypass_as_an_option():
    text = PREFLIGHT.read_text(encoding="utf-8")
    assert "bypassPermissions" in text and "--dangerously-skip-permissions" not in text
