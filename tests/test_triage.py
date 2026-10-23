"""ROADMAP R18: a failed CI run explains itself (``plugin/ci/triage.py``, ``run_phase.py
--phase triage``, ``pr/failed_runs.py``; ``docs/proposals/failed-run-explains-itself.md``)."""

from __future__ import annotations

import json
import os
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import pytest
from ci import project_setup, run_phase, triage
from pr import digest, failed_runs

from gate import gate as gate_mod
from tests import test_ci as ci_tests  # noqa: E402
from tests.test_ci import (
    DEFERRED_GATE_FILE,
    FAKE_RESULT,
    FAKE_TOKEN,
    KEY_ENV,
    Args,
    fake_cli,
    pr_route,
    set_state,
    write,
)

# the fixtures of the phase runner's tests, used here by name
project = ci_tests.project
fake_claude = ci_tests.fake_claude

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / "template" / ".github" / "workflows"
TRIAGED = ("design", "build", "test", "deploy", "fix", "detect")
AWS_KEY = "AKIA" + "ABCDEFGHIJKLMNOP"  # split so the secrets hook does not flag this file


def _git(root: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=root, capture_output=True, text=True, check=True
    ).stdout.strip()


# --- the case the runner leaves for the triage step ----------------------------------------------
PARK = {"result": "park", "checks": [{"name": "commands", "ok": False, "reason": "red"}]}
GUARDRAIL_PARK = {"result": "park", "checks": [{"name": "guardrails", "ok": False}]}


def test_the_case_follows_the_park_this_run_wrote():
    assert triage.run_case(1, PARK, fresh=True) == "park"
    assert triage.run_case(0, PARK, fresh=True) == "park"  # a park ends the job green
    # a park that already says why costs no model call, and is in the queue already
    assert triage.run_case(0, GUARDRAIL_PARK, fresh=True) is None
    assert triage.run_case(1, GUARDRAIL_PARK, fresh=True) is None
    # an older park the run did not write is not this run's
    assert triage.run_case(0, PARK, fresh=False) is None
    assert triage.run_case(1, PARK, fresh=False) == "red"
    assert triage.run_case(0, None, fresh=False) is None


def test_a_failed_setup_comes_first_and_a_missing_result_reads_as_red():
    assert triage.case_of(None, {"error": "sdlc.yaml is unreadable"}) == "setup"
    assert triage.case_of({"triage": "park"}, {"ok": False, "exit_code": 1}) == "setup"
    assert triage.case_of(None, None) == "red"
    assert triage.case_of({"triage": None}, {"ok": True}) is None
    assert triage.case_of({"triage": "park"}, None) == "park"


def test_the_lines_are_capped_and_a_line_carrying_a_secret_is_dropped():
    text = "\n".join(
        ["- the test target failed", f"* key {AWS_KEY} in the log", "", "3", "4", "5", "6"]
    )
    kept, dropped = triage.lines_of(text)
    assert dropped == 1 and AWS_KEY not in " ".join(kept)
    assert kept == ["the test target failed", "3", "4", "5"]
    assert triage.lines_of("x" * 1000)[0] == ["x" * triage.LINE_MAX]


# --- the park block ------------------------------------------------------------------------------
def test_the_park_block_prints_the_triage_lines_under_their_label():
    result = gate_mod.GateResult.from_dict(
        {**PARK, "change_id": "0001", "slug": "s", "phase": "c", "triage": ["a", "b"]}
    )
    block = result.what_i_need()
    assert gate_mod.TRIAGE_HEADING in block and "  - a\n  - b" in block
    assert block.index("**commands**") < block.index("Triage (model-written)")
    data = result.as_dict()
    assert data["triage"] == ["a", "b"] and gate_mod.TRIAGE_HEADING in data["what_i_need"]
    # a record without triage keeps its shape
    assert "triage" not in gate_mod.GateResult.from_dict(PARK).as_dict()


# --- the runner's --out file ---------------------------------------------------------------------
def test_a_parked_run_writes_its_out_file_and_the_triage_output(
    project, fake_claude, monkeypatch, capsys, tmp_path
):
    """The commands step could not run: the run parks and exits 1; its --out file names the
    park's record and the session's files, and the step output says ``triage=park``."""
    root, change = project
    pr_route(monkeypatch)
    set_state(change, "b", gate_phase="b", gate_result="passed")
    write(change / "evidence" / "gate-c.json", json.dumps(DEFERRED_GATE_FILE))
    monkeypatch.setenv("FAKE_CLAUDE_RESULT", json.dumps(FAKE_RESULT))
    monkeypatch.setattr(
        run_phase, "run_gate_commands", lambda *a, **k: {"ok": False, "reason": "gate: boom"}
    )
    output, out = tmp_path / "github-output", tmp_path / "run.json"
    out.write_text("{}", encoding="utf-8")  # a stale file is removed first
    env = dict(os.environ, **KEY_ENV, GITHUB_TOKEN=FAKE_TOKEN, GITHUB_OUTPUT=str(output))
    args = Args(
        root=str(root),
        phase="c",
        dry_run=False,
        no_dispatch=True,
        claude=fake_cli(fake_claude),
        out=str(out),
    )
    assert run_phase.run_phase(args, env) == run_phase.EXIT_FAILED
    capsys.readouterr()
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["triage"] == "park" and data["exit_code"] == run_phase.EXIT_FAILED
    assert data["change_id"] == "0001" and data["gate_phase"] == "c"
    assert data["gate_record"] == "changes/0001-percent-helper/evidence/gate-c.json"
    assert data["result_file"].endswith("evidence/claude-c.json")
    assert data["emitted"]["parked"].startswith("commands: deferred")
    assert "triage=park\n" in output.read_text(encoding="utf-8")


def test_a_red_run_with_no_park_says_red(project, fake_claude, monkeypatch, capsys, tmp_path):
    root, change = project
    pr_route(monkeypatch)
    set_state(change, "b", gate_phase="b", gate_result="passed")
    monkeypatch.setenv("FAKE_CLAUDE_RESULT", json.dumps({**FAKE_RESULT, "is_error": True}))
    out = tmp_path / "run.json"
    env = dict(os.environ, **KEY_ENV, GITHUB_TOKEN=FAKE_TOKEN)
    args = Args(
        root=str(root),
        phase="c",
        dry_run=False,
        no_dispatch=True,
        claude=fake_cli(fake_claude),
        out=str(out),
    )
    assert run_phase.run_phase(args, env) == run_phase.EXIT_FAILED
    capsys.readouterr()
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["triage"] == "red" and "claude exited 0" in data["why"]


def test_a_run_refused_before_it_starts_still_writes_its_out_file(tmp_path, monkeypatch):
    """No App configured: ``main`` refuses before the phase run, and says so in the file."""
    out = tmp_path / "run.json"
    monkeypatch.delenv("SDLC_APP_TOKEN_MINTED_AT", raising=False)
    monkeypatch.setattr(run_phase.app_token, "app_missing", lambda env: "no App")
    argv = ["--root", str(tmp_path), "--phase", "c", "--id", "0001", "--out", str(out)]
    assert run_phase.main(argv) == run_phase.EXIT_FAILED
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["triage"] == "red" and data["why"] == "no App"


def test_project_setup_writes_its_out_file(tmp_path):
    (tmp_path / "sdlc.yaml").write_text(
        'commands:\n  setup: python -c "import sys; sys.exit(3)"\n', encoding="utf-8"
    )
    out = tmp_path / "setup.json"
    assert project_setup.main(["--root", str(tmp_path), "--out", str(out)]) == 1
    data = json.loads(out.read_text(encoding="utf-8"))
    assert triage.setup_failed(data) and data["exit_code"] == 3


# --- the triage step -----------------------------------------------------------------------------
class Session:
    """A fake ``_run_session``: records the argv and environment, answers ``text``."""

    def __init__(self, text: str, cost: float = 0.02):
        self.text, self.cost, self.calls = text, cost, []

    def __call__(self, argv, cwd, env, timeout):
        self.calls.append({"argv": argv, "env": dict(env), "timeout": timeout})
        data = {"result": self.text, "total_cost_usd": self.cost, "is_error": False}
        return data, json.dumps(data), "", 0


def _triage_args(root: Path, out: Path | None, setup: Path | None = None, **kw) -> Args:
    return Args(
        root=str(root),
        phase="triage",
        id=None,
        out=str(out) if out else None,
        setup=str(setup) if setup else None,
        **{"dry_run": False, **kw},
    )


def _origin(root: Path, tmp_path: Path) -> Path:
    bare = tmp_path / "origin.git"
    subprocess.run(["git", "init", "-q", "--bare", str(bare)], check=True)
    _git(root, "remote", "add", "origin", str(bare))
    return bare


def test_nothing_to_explain_runs_no_session(tmp_path, monkeypatch, capsys):
    session = Session("x")
    monkeypatch.setattr(run_phase, "_run_session", session)
    out = tmp_path / "run.json"
    out.write_text(json.dumps({"triage": None, "exit_code": 0}), encoding="utf-8")
    assert run_phase.run_triage(_triage_args(tmp_path, out), dict(KEY_ENV)) == 0
    assert "nothing to explain" in json.loads(capsys.readouterr().out)["skipped"]
    assert session.calls == []


def test_a_parked_run_gets_its_lines_in_the_park_block(project, monkeypatch, capsys, tmp_path):
    """The park's record gains the triage lines, the block is re-rendered, the session's
    result is stored where the budget reads it, and the park is committed and the PR body
    brought up to date; the session held no GitHub token and read the target logs."""
    root, change = project
    evidence = change / "evidence"
    record = {
        **PARK,
        "change_id": "0001",
        "slug": "percent-helper",
        "phase": "c",
        "label": "sdlc:needs-human",
    }
    record["what_i_need"] = gate_mod.GateResult.from_dict(record).what_i_need()
    write(evidence / "gate-c.json", json.dumps(record))
    write(evidence / "test.log", "FAILED test_percent\n")
    out = tmp_path / "run.json"
    out.write_text(
        json.dumps(
            {
                "triage": "park",
                "change_id": "0001",
                "gate_phase": "c",
                "branch_phase": "c",
                "change_dir": "changes/0001-percent-helper",
                "gate_record": "changes/0001-percent-helper/evidence/gate-c.json",
                "exit_code": 1,
            }
        ),
        encoding="utf-8",
    )
    session = Session(f"- test_percent fails\n- looks real\n- token {AWS_KEY}", cost=0.05)
    monkeypatch.setattr(run_phase, "_run_session", session)
    calls = []

    def cli_call(script, argv, timeout=600, env=None):
        calls.append((Path(script).name, argv))
        return {"ok": True, "output": {"route": "api", "number": 7, "url": "u"}}

    monkeypatch.setattr(run_phase, "_cli_call", cli_call)
    monkeypatch.setattr(run_phase, "record_spend", lambda *a, **k: True)
    env = dict(os.environ, **KEY_ENV, GITHUB_TOKEN=FAKE_TOKEN, SDLC_WORKFLOW_TOKEN="wf")
    assert run_phase.run_triage(_triage_args(root, out), env) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["case"] == "park" and report["added"] is True
    stored = json.loads((evidence / "gate-c.json").read_text(encoding="utf-8"))
    assert stored["triage"] == ["test_percent fails", "looks real"]
    assert "Triage (model-written)" in stored["what_i_need"]
    assert AWS_KEY not in json.dumps(stored)
    seen = session.calls[0]
    assert not {"GITHUB_TOKEN", "GH_TOKEN", "SDLC_WORKFLOW_TOKEN"} & set(seen["env"])
    assert seen["timeout"] == run_phase.TRIAGE_TIMEOUT_SECONDS
    prompt = seen["argv"][2]
    assert "changes/0001-percent-helper/evidence/test.log" in prompt
    assert ".sdlc-cache/triage/run.json" in prompt
    assert (evidence / "claude-triage.json").is_file()  # the budget's own record
    names = [argv[0] for _name, argv in calls]
    assert names == ["commit-phase", "upsert"]


def test_a_red_run_writes_its_failed_run_record_on_its_own_ref(tmp_path, monkeypatch, capsys):
    root = tmp_path / "proj"
    root.mkdir()
    _git(root, "init", "-q", "-b", "main")
    bare = _origin(root, tmp_path)
    out = tmp_path / "run.json"
    out.write_text(
        json.dumps({"triage": "red", "exit_code": 1, "why": "the run left no gate record"}),
        encoding="utf-8",
    )
    session = Session("it never reached its gate\nlooks real")
    monkeypatch.setattr(run_phase, "_run_session", session)
    env = dict(
        os.environ,
        **KEY_ENV,
        GITHUB_RUN_ID="4242",
        GITHUB_RUN_ATTEMPT="2",
        GITHUB_REPOSITORY="o/r",
        GITHUB_WORKFLOW="SDLC build (c)",
    )
    for var in ("GITHUB_TOKEN", "GH_TOKEN", "GITHUB_ACTIONS"):
        env.pop(var, None)
        monkeypatch.delenv(var, raising=False)
    assert run_phase.run_triage(_triage_args(root, out), env) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["record"]["ok"] is True, report
    ref = "refs/sdlc/failed-runs/4242-2"
    record = json.loads(subprocess.run(
        ["git", "--git-dir", str(bare), "show", f"{ref}:{triage.RECORD_FILE}"],
        capture_output=True, text=True, check=True,
    ).stdout)  # fmt: skip
    assert record["reason"] == "the run left no gate record" and record["parked"] is False
    assert record["triage"] == ["it never reached its gate", "looks real"]
    assert record["run"]["url"].endswith("/o/r/actions/runs/4242/attempts/2")


def test_a_failed_setup_is_read_from_its_file(tmp_path, monkeypatch, capsys):
    setup = tmp_path / "setup.json"
    setup.write_text(json.dumps({"command": "pip install x", "exit_code": 1}), encoding="utf-8")
    session = Session("pip could not reach the index\nlooks flaky")
    monkeypatch.setattr(run_phase, "_run_session", session)
    root = tmp_path / "proj"
    root.mkdir()
    args = _triage_args(root, tmp_path / "missing.json", setup, dry_run=True)
    assert run_phase.run_triage(args, dict(KEY_ENV)) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["case"] == "setup" and report["logs"] == [".sdlc-cache/triage/setup.json"]
    record = triage.failed_run_record("setup", None, json.loads(setup.read_text()), [], {})
    assert record["step"] == "setup" and record["reason"].startswith("the project's setup failed")


def test_a_run_with_no_file_to_read_is_recorded_without_a_session(tmp_path, monkeypatch):
    record = triage.failed_run_record("red", None, None, [], {"GITHUB_RUN_ID": "1"})
    assert record["reason"] == triage.RUNNER_DID_NOT_FINISH and record["triage"] == []


# --- the digest's "Failed runs" line -------------------------------------------------------------
def _api(runs, refs, records):
    def get(url):
        if "/actions/runs?" in url:
            return {"error": "", "data": {"workflow_runs": runs}}
        if "/git/matching-refs/" in url:
            return {"error": "", "data": refs}
        sha = url.rpartition("ref=")[2]
        import base64

        body = base64.b64encode(json.dumps(records[sha]).encode()).decode()
        return {"error": "", "data": {"content": body}}

    return get


def _run(run_id, conclusion, path="sdlc-build.yml", attempt=1, at="2026-10-22T10:00:00Z"):
    return {
        "id": run_id,
        "run_attempt": attempt,
        "name": "SDLC build (c)",
        "path": f".github/workflows/{path}",
        "conclusion": conclusion,
        "created_at": at,
        "html_url": f"https://github.com/o/r/actions/runs/{run_id}",
    }


def test_the_failed_runs_line_lists_red_runs_with_their_records():
    runs = [
        _run(2, "failure", at="2026-10-22T12:00:00Z"),
        _run(1, "cancelled", at="2026-10-21T08:00:00Z"),
        _run(3, "success"),  # a later attempt succeeded: the run object says success
        _run(4, "failure", path="ci.yml"),  # not a framework workflow
        _run(5, "failure", attempt=2),
    ]
    refs = [
        {"ref": "refs/sdlc/failed-runs/2-1", "object": {"sha": "a"}},
        {"ref": "refs/sdlc/failed-runs/3-1", "object": {"sha": "b"}},  # its run is green now
        {"ref": "refs/sdlc/failed-runs/5-2", "object": {"sha": "c"}},
        {"ref": "refs/sdlc/failed-runs/9-1", "object": {"sha": "d"}},  # no such red run
    ]
    records = {
        "a": {"change_id": "0004", "reason": "claude exited 1", "triage": ["x", "y"]},
        "b": {"reason": "old"},
        "c": {"reason": "parked one", "parked": True},
        "d": {"reason": "forged"},
    }
    now = datetime(2026, 10, 23, tzinfo=timezone.utc)
    got = failed_runs.collect("o/r", now, _api(runs, refs, records), "https://api")
    assert [e["run"]["id"] for e in got["runs"]] == [1, 5, 2]  # oldest first
    text = failed_runs.render(got)
    lines = text.splitlines()
    assert lines[0] == failed_runs.HEADING.format(days=7)
    assert "cancelled; no triage record" in lines[2]
    assert "attempt 2" in lines[3] and "no triage record" in lines[3]  # its record parked
    assert "change 0004 — claude exited 1 — triage (model-written): x; y" in lines[4]
    assert "parked one" not in text and "forged" not in text and "old" not in text


def test_the_digest_places_the_failed_runs_after_the_queue():
    section = "## Failed runs — the last 7 days, no park\n\n- a run"
    text = digest.render_digest([], "2026-10-23T06:00:00Z", "## Counters", failed_runs=section)
    assert (
        text.index(digest.NOTHING_WAITING)
        < text.index("## Failed runs")
        < text.index("## Counters")
    )
    assert failed_runs.render({"ok": True, "runs": []}) == ""
    assert failed_runs.render({"ok": False, "reason": "403"}).startswith("The failed runs")


# --- the workflow templates ----------------------------------------------------------------------
@pytest.mark.parametrize("name", TRIAGED)
def test_each_phase_workflow_triages_after_a_fresh_framework_checkout(name):
    text = (WORKFLOWS / f"sdlc-{name}.yml").read_text(encoding="utf-8")
    steps = text.split("\n      - ")
    triage_at = next(i for i, s in enumerate(steps) if "--phase triage" in s)
    names = [re.match(r"(?:name: )?(.*)", s).group(1) for s in steps]
    assert names[triage_at - 3].startswith("Remove the framework checkout before the triage")
    assert (
        "path: framework" in steps[triage_at - 2]
        and "persist-credentials: false" in (steps[triage_at - 2])
    )
    assert "checkout_check.py" in steps[triage_at - 1]
    step = steps[triage_at]
    assert "continue-on-error: true" in step
    assert "steps.triage_checkout.outcome == 'success'" in step
    assert "# sdlc:commands.env" not in step  # the project's secrets never reach it
    for before in steps[triage_at - 3 : triage_at]:
        assert "steps.phase.outputs.triage == 'park'" in before
        assert "steps.setup.outcome == 'failure'" in before
    # every phase run and the setup write the files the triage step reads
    for line in [ln for ln in text.splitlines() if ln.strip().startswith("run: python")]:
        if "run_phase.py" in line and "--find-change" not in line and "--phase triage" not in line:
            assert '--out "$RUNNER_TEMP/sdlc-run.json"' in line, line
        if "project_setup.py" in line:
            assert '--out "$RUNNER_TEMP/sdlc-setup.json"' in line, line
    assert "        id: setup\n        # sdlc:commands.env setup" in text or (
        "        id: setup\n" in text
    )
