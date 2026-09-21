"""Layer-1 tests for plugin/evidence/collect.py (build guide step 28): the three sdlc.yaml
commands are run against a temporary copy of the fixture project and their literal output is
stored under changes/<id>-<slug>/evidence/ with the header line the gate reads back."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest
from evidence import collect as collect_mod

from gate import artifacts as art
from tests.test_gate import _initialised_fixture, git, run_py, write

COLLECT = Path(__file__).resolve().parents[1] / "plugin" / "evidence" / "collect.py"


@pytest.fixture
def project(tmp_path):
    """The fixture project with /sdlc-init applied and change 0001 in place (phase (d) would
    be reached with the build committed; the evidence writer needs neither)."""
    root, change = _initialised_fixture(tmp_path)
    git(root, "add", ".")
    git(root, "commit", "-q", "-m", "change 0001")
    return root, change


def run_collect(root: Path, *args: str, env: dict | None = None):
    proc = run_py(str(COLLECT), "--root", str(root), "--id", "0001", *args, cwd=root, env=env)
    return proc, json.loads(proc.stdout) if proc.stdout.strip() else {}


def set_command(root: Path, target: str, command: str) -> None:
    """Rewrite one `commands:` target in the project's sdlc.yaml."""
    text = (root / "sdlc.yaml").read_text(encoding="utf-8")
    lines = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith(f"{target}:") and line.startswith("  "):
            lines.append(f'  {target}: "{command}"')
        else:
            lines.append(line)
    write(root / "sdlc.yaml", "\n".join(lines) + "\n")


def header_of(path: Path) -> dict[str, str]:
    parsed = art.parse_evidence_header(path.read_text(encoding="utf-8"))
    assert parsed is not None, path.read_text(encoding="utf-8")[:200]
    return parsed


def test_collect_writes_the_three_logs_with_their_header_and_exits_zero(project):
    root, change = project
    proc, out = run_collect(root)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert out["all_green"] is True
    assert sorted(out["results"]) == ["build", "lint", "test"]
    for target in ("test", "build", "lint"):
        result = out["results"][target]
        assert result["exit"] == 0 and result["timed_out"] is False
        assert result["seconds"] >= 0
        log = change / "evidence" / art.EVIDENCE_TARGETS[target]
        assert result["log"] == f"changes/0001-percent-helper/evidence/{log.name}"
        head = header_of(log)
        assert head["exit"] == "0" and head["at"].endswith("Z")
        assert head["command"]  # the sdlc.yaml one-liner, verbatim
    # the literal toolchain output follows the header (article p.27-29), not a summary
    body = (change / "evidence" / "test.log").read_text(encoding="utf-8").splitlines()[1:]
    assert any("passed" in line for line in body), body
    shots = change / "evidence" / "screenshots"
    assert shots.is_dir() and (shots / ".gitkeep").is_file()


def test_collect_reports_a_failing_target_and_keeps_its_output(project):
    root, change = project
    env = {**os.environ, "SAMPLE_FAIL": "1"}
    proc, out = run_collect(root, env=env)
    assert proc.returncode == 1, proc.stdout + proc.stderr
    assert out["all_green"] is False
    assert out["results"]["test"]["exit"] == 1 and out["results"]["build"]["exit"] == 0
    log = change / "evidence" / "test.log"
    assert header_of(log)["exit"] == "1"
    assert "SAMPLE_FAIL=1" in log.read_text(encoding="utf-8")  # the failure itself is the record
    # and the gate reads that header back: a red log parks the change at (d)
    assert art.evidence_failure(log.read_text(encoding="utf-8")).endswith("exited 1")


def test_collect_only_runs_the_named_target(project):
    root, change = project
    proc, out = run_collect(root, "--only", "lint")
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert list(out["results"]) == ["lint"] and out["all_green"] is True
    assert (change / "evidence" / "lint.log").is_file()
    assert not (change / "evidence" / "test.log").exists()
    assert not (change / "evidence" / "build.log").exists()


def test_collect_times_out_and_says_so(project):
    root, change = project
    write(root / "sleeper.py", "import time\n\ntime.sleep(30)\n")
    set_command(root, "test", "python sleeper.py")
    proc, out = run_collect(root, "--only", "test", "--timeout", "1")
    assert proc.returncode == 1, proc.stdout + proc.stderr
    result = out["results"]["test"]
    assert result["exit"] is None and result["timed_out"] is True and out["all_green"] is False
    log = change / "evidence" / "test.log"
    assert header_of(log)["exit"] == art.EVIDENCE_TIMEOUT
    assert "timed out" in art.evidence_failure(log.read_text(encoding="utf-8"))


def test_collect_reports_a_missing_command_as_none(project):
    root, _change = project
    set_command(root, "lint", "echo no lint target")  # the placeholder /sdlc-init writes
    proc, out = run_collect(root, "--only", "lint")
    assert proc.returncode == 2, proc.stdout + proc.stderr
    assert out["results"]["lint"]["exit"] == "none" and out["results"]["lint"]["log"] is None
    assert out["all_green"] is False and "lint" in out["error"]


def test_collect_usage_errors(project, tmp_path):
    root, _change = project
    proc = run_py(str(COLLECT), "--root", str(root), "--id", "0009", cwd=root)
    assert proc.returncode == 2 and "no change folder" in proc.stderr
    bare = tmp_path / "bare"
    (bare / "changes" / "0001-x").mkdir(parents=True)
    write(bare / "changes" / "0001-x" / "status.yaml", "id: '0001'\n")
    proc = run_py(str(COLLECT), "--root", str(bare), "--id", "0001", cwd=tmp_path)
    assert proc.returncode == 2 and "sdlc.yaml" in proc.stderr
    assert collect_mod.main(["--root", str(root), "--id", "abc"]) == 2


def test_evidence_header_round_trip():
    line = art.render_evidence_header("python -m pytest", 0, 12.34, "2026-09-21T10:00:00Z")
    assert line == "# python -m pytest — exit 0 — 12.3s — 2026-09-21T10:00:00Z"
    assert art.parse_evidence_header(line)["command"] == "python -m pytest"
    assert art.evidence_failure(line) is None
    assert art.evidence_failure(line + "\n42 passed\n") is None
    assert "exited 2" in art.evidence_failure(art.render_evidence_header("x", 2, 1.0, "t"))
    assert "timed out" in art.evidence_failure(art.render_evidence_header("x", None, 1.0, "t"))
    # a hand-written log has no header and is accepted as it is (the gate only checks it exists)
    assert art.parse_evidence_header("ok\n") is None and art.evidence_failure("ok\n") is None
