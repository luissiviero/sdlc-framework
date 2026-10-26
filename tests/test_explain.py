"""ROADMAP R18: a failed CI run explains itself (``plugin/ci/explain.py``, ``run_phase.py
--phase explain``, ``pr/failed_runs.py``; ``docs/proposals/failed-run-explains-itself.md``)."""

from __future__ import annotations

import json
import os
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import pytest
from ci import explain, project_setup, run_phase
from pr import digest, failed_runs

from gate import gate as gate_mod
from state import status as status_mod
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
EXPLAINED = ("design", "build", "test", "deploy", "fix", "detect")
AWS_KEY = "AKIA" + "ABCDEFGHIJKLMNOP"  # split so the secrets hook does not flag this file


def _git(root: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=root, capture_output=True, text=True, check=True
    ).stdout.strip()


# --- the case the runner leaves for the explain step ----------------------------------------------
PARK = {"result": "park", "checks": [{"name": "commands", "ok": False, "reason": "red"}]}
GUARDRAIL_PARK = {"result": "park", "checks": [{"name": "guardrails", "ok": False}]}


def test_the_case_follows_the_park_this_run_wrote():
    assert explain.run_case(1, PARK, fresh=True) == "park"
    assert explain.run_case(0, PARK, fresh=True) == "park"  # a park ends the job green
    # a park that already says why costs no model call, and is in the queue already
    assert explain.run_case(0, GUARDRAIL_PARK, fresh=True) is None
    assert explain.run_case(1, GUARDRAIL_PARK, fresh=True) is None
    # an older park the run did not write is not this run's
    assert explain.run_case(0, PARK, fresh=False) is None
    assert explain.run_case(1, PARK, fresh=False) == "red"
    assert explain.run_case(0, None, fresh=False) is None


def test_the_logs_for_a_park_include_the_drive_s_files(tmp_path):
    """Change 0004 (R13): a red ``commands`` entry adds ``drive.log`` when it exists; a failed
    ``proof`` entry adds ``drive.log`` and ``proof/manifest.json``."""
    change = "changes/0001-x"
    evidence = tmp_path / change / "evidence"
    for name in ("test.log", "build.log", "lint.log", "drive.log", "proof/manifest.json"):
        (evidence / name).parent.mkdir(parents=True, exist_ok=True)
        (evidence / name).write_text("x\n", encoding="utf-8")

    def logs(failed: list[str]) -> list[str]:
        record = {"result": "park", "checks": [{"name": n, "ok": False} for n in failed]}
        (evidence / "gate-build.json").write_text(json.dumps(record), encoding="utf-8")
        out = {"change_dir": change, "gate_record": f"{change}/evidence/gate-build.json"}
        return [
            p.removeprefix(f"{change}/evidence/")
            for p in explain.logs_for(tmp_path, "park", out, [])
        ]

    assert logs(["commands"]) == [
        "gate-build.json",
        "test.log",
        "build.log",
        "lint.log",
        "drive.log",
    ]
    assert logs(["proof"]) == ["gate-build.json", "drive.log", "proof/manifest.json"]
    assert logs(["commands", "proof"])[-2:] == ["drive.log", "proof/manifest.json"]
    (evidence / "drive.log").unlink()
    assert logs(["commands"]) == ["gate-build.json", "test.log", "build.log", "lint.log"]


def test_a_failed_setup_comes_first_and_a_missing_result_reads_as_red():
    assert explain.case_of(None, {"error": "sdlc.yaml is unreadable"}) == "setup"
    assert explain.case_of({"explain": "park"}, {"ok": False, "exit_code": 1}) == "setup"
    assert explain.case_of(None, None) == "red"
    assert explain.case_of({"explain": None}, {"ok": True}) is None
    assert explain.case_of({"explain": "park"}, None) == "park"


def test_the_lines_are_capped_and_a_line_carrying_a_secret_is_dropped():
    text = "\n".join(
        ["- the test target failed", f"* key {AWS_KEY} in the log", "", "3", "4", "5", "6"]
    )
    kept, dropped = explain.lines_of(text)
    assert dropped == 1 and AWS_KEY not in " ".join(kept)
    assert kept == ["the test target failed", "3", "4", "5"]
    assert explain.lines_of("x" * 1000)[0] == ["x" * explain.LINE_MAX]


# --- the park block ------------------------------------------------------------------------------
def test_the_park_block_prints_the_explain_lines_under_their_label():
    result = gate_mod.GateResult.from_dict(
        {**PARK, "change_id": "0001", "slug": "s", "phase": "build", "explanation": ["a", "b"]}
    )
    block = result.what_i_need()
    assert gate_mod.EXPLANATION_HEADING in block and "  - a\n  - b" in block
    assert block.index("**commands**") < block.index("Explanation (model-written)")
    data = result.as_dict()
    assert data["explanation"] == ["a", "b"] and gate_mod.EXPLANATION_HEADING in data["what_i_need"]
    # a record without an explanation keeps its shape
    assert "explanation" not in gate_mod.GateResult.from_dict(PARK).as_dict()


# --- the runner's --out file ---------------------------------------------------------------------
def test_a_parked_run_writes_its_out_file_and_the_explain_output(
    project, fake_claude, monkeypatch, capsys, tmp_path
):
    """The commands step could not run: the run parks and exits 1; its --out file names the
    park's record and the session's files, and the step output says ``explain=park``."""
    root, change = project
    pr_route(monkeypatch)
    set_state(change, "design", gate_phase="design", gate_result="passed")
    write(change / "evidence" / "gate-build.json", json.dumps(DEFERRED_GATE_FILE))
    monkeypatch.setenv("FAKE_CLAUDE_RESULT", json.dumps(FAKE_RESULT))
    monkeypatch.setattr(
        run_phase, "run_gate_commands", lambda *a, **k: {"ok": False, "reason": "gate: boom"}
    )
    output, out = tmp_path / "github-output", tmp_path / "run.json"
    out.write_text("{}", encoding="utf-8")  # a stale file is removed first
    env = dict(os.environ, **KEY_ENV, GITHUB_TOKEN=FAKE_TOKEN, GITHUB_OUTPUT=str(output))
    args = Args(
        root=str(root),
        phase="build",
        dry_run=False,
        no_dispatch=True,
        claude=fake_cli(fake_claude),
        out=str(out),
    )
    assert run_phase.run_phase(args, env) == run_phase.EXIT_FAILED
    capsys.readouterr()
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["explain"] == "park" and data["exit_code"] == run_phase.EXIT_FAILED
    assert data["change_id"] == "0001" and data["gate_phase"] == "build"
    assert data["gate_record"] == "changes/0001-percent-helper/evidence/gate-build.json"
    assert data["result_file"].endswith("evidence/claude-build.json")
    assert data["emitted"]["parked"].startswith("commands: deferred")
    assert "explain=park\n" in output.read_text(encoding="utf-8")
    assert "triage=" not in output.read_text(encoding="utf-8")  # not written since 1.0.48


def test_a_red_run_with_no_park_says_red(project, fake_claude, monkeypatch, capsys, tmp_path):
    root, change = project
    pr_route(monkeypatch)
    set_state(change, "design", gate_phase="design", gate_result="passed")
    monkeypatch.setenv("FAKE_CLAUDE_RESULT", json.dumps({**FAKE_RESULT, "is_error": True}))
    out = tmp_path / "run.json"
    env = dict(os.environ, **KEY_ENV, GITHUB_TOKEN=FAKE_TOKEN)
    args = Args(
        root=str(root),
        phase="build",
        dry_run=False,
        no_dispatch=True,
        claude=fake_cli(fake_claude),
        out=str(out),
    )
    assert run_phase.run_phase(args, env) == run_phase.EXIT_FAILED
    capsys.readouterr()
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["explain"] == "red" and "claude exited 0" in data["why"]


def test_a_run_refused_before_it_starts_still_writes_its_out_file(tmp_path, monkeypatch):
    """No App configured: ``main`` refuses before the phase run, and says so in the file."""
    out = tmp_path / "run.json"
    monkeypatch.delenv("SDLC_APP_TOKEN_MINTED_AT", raising=False)
    monkeypatch.setattr(run_phase.app_token, "app_missing", lambda env: "no App")
    argv = ["--root", str(tmp_path), "--phase", "build", "--id", "0001", "--out", str(out)]
    assert run_phase.main(argv) == run_phase.EXIT_FAILED
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["explain"] == "red" and data["why"] == "no App"


def test_project_setup_writes_its_out_file(tmp_path):
    (tmp_path / "sdlc.yaml").write_text(
        'commands:\n  setup: python -c "import sys; sys.exit(3)"\n', encoding="utf-8"
    )
    out = tmp_path / "setup.json"
    assert project_setup.main(["--root", str(tmp_path), "--out", str(out)]) == 1
    data = json.loads(out.read_text(encoding="utf-8"))
    assert explain.setup_failed(data) and data["exit_code"] == 3


# --- the explain step -----------------------------------------------------------------------------
class Session:
    """A fake ``_run_session``: records the argv and environment, answers ``text``."""

    def __init__(self, text: str, cost: float = 0.02):
        self.text, self.cost, self.calls = text, cost, []

    def __call__(self, argv, cwd, env, timeout):
        self.calls.append({"argv": argv, "env": dict(env), "timeout": timeout})
        data = {"result": self.text, "total_cost_usd": self.cost, "is_error": False}
        return data, json.dumps(data), "", 0


def _explain_args(root: Path, out: Path | None, setup: Path | None = None, **kw) -> Args:
    return Args(
        root=str(root),
        phase="explain",
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
    out.write_text(json.dumps({"explain": None, "exit_code": 0}), encoding="utf-8")
    assert run_phase.run_explain(_explain_args(tmp_path, out), dict(KEY_ENV)) == 0
    assert "nothing to explain" in json.loads(capsys.readouterr().out)["skipped"]
    assert session.calls == []


def test_a_parked_run_gets_its_lines_in_the_park_block(project, monkeypatch, capsys, tmp_path):
    """The park's record gains the explain step's lines, the block is re-rendered, the session's
    result is stored where the budget reads it, and the park is committed and the PR body
    brought up to date; the session held no GitHub token and read the target logs."""
    root, change = project
    evidence = change / "evidence"
    record = {
        **PARK,
        "change_id": "0001",
        "slug": "percent-helper",
        "phase": "build",
        "label": "sdlc:needs-human",
    }
    record["what_i_need"] = gate_mod.GateResult.from_dict(record).what_i_need()
    write(evidence / "gate-build.json", json.dumps(record))
    write(evidence / "test.log", "FAILED test_percent\n")
    out = tmp_path / "run.json"
    out.write_text(
        json.dumps(
            {
                "explain": "park",
                "change_id": "0001",
                "gate_phase": "build",
                "branch_phase": "build",
                "change_dir": "changes/0001-percent-helper",
                "gate_record": "changes/0001-percent-helper/evidence/gate-build.json",
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
    assert run_phase.run_explain(_explain_args(root, out), env) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["case"] == "park" and report["added"] is True
    stored = json.loads((evidence / "gate-build.json").read_text(encoding="utf-8"))
    assert stored["explanation"] == ["test_percent fails", "looks real"]
    assert "Explanation (model-written)" in stored["what_i_need"]
    assert AWS_KEY not in json.dumps(stored)
    seen = session.calls[0]
    assert not {"GITHUB_TOKEN", "GH_TOKEN", "SDLC_WORKFLOW_TOKEN"} & set(seen["env"])
    assert seen["timeout"] == run_phase.EXPLAIN_TIMEOUT_SECONDS
    prompt = seen["argv"][2]
    assert "changes/0001-percent-helper/evidence/test.log" in prompt
    assert ".sdlc-cache/explain/run.json" in prompt
    assert (evidence / "claude-explain.json").is_file()  # the budget's own record
    # committed on the branch without moving the change's phase (the review, finding B1),
    # then the PR body refreshed with no review request
    assert _git(root, "log", "-1", "--format=%s") == "explain(0001): the run's logs read"
    names = [argv[0] for _name, argv in calls]
    assert names == ["upsert"] and "--request-review" not in calls[0][1]
    # the park ended the job red: a record marked parked, which the digest leaves to the queue
    assert report["record"]["reason"] == explain.NO_RUN_ID  # no GITHUB_RUN_ID here


def test_a_red_run_writes_its_failed_run_record_on_its_own_ref(tmp_path, monkeypatch, capsys):
    root = tmp_path / "proj"
    root.mkdir()
    _git(root, "init", "-q", "-b", "main")
    bare = _origin(root, tmp_path)
    # a session that knew the run id pushed its own record first: the runner's replaces it
    _git(root, "-c", "user.name=s", "-c", "user.email=s@x", "commit", "-q", "--allow-empty",
         "-m", "forged")  # fmt: skip
    _git(root, "push", "-q", "origin", "HEAD:refs/sdlc/failed-runs/4242-2")
    write(root / "stderr.txt", "Error: the gate CLI crashed\n")
    out = tmp_path / "run.json"
    out.write_text(
        json.dumps(
            {
                "explain": "red",
                "exit_code": 1,
                "why": "the run left no gate record",
                "stderr_file": "stderr.txt",
            }
        ),
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
    assert run_phase.run_explain(_explain_args(root, out), env) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["record"]["ok"] is True, report
    ref = "refs/sdlc/failed-runs/4242-2"
    record = json.loads(subprocess.run(
        ["git", "--git-dir", str(bare), "show", f"{ref}:{explain.RECORD_FILE}"],
        capture_output=True, text=True, check=True,
    ).stdout)  # fmt: skip
    assert record["reason"] == "the run left no gate record" and record["parked"] is False
    assert record["explanation"] == ["it never reached its gate", "looks real"]
    assert record["run"]["url"].endswith("/o/r/actions/runs/4242/attempts/2")


def test_a_failed_setup_is_read_from_its_file(tmp_path, monkeypatch, capsys):
    setup = tmp_path / "setup.json"
    setup.write_text(json.dumps({"command": "pip install x", "exit_code": 1}), encoding="utf-8")
    session = Session("pip could not reach the index\nlooks flaky")
    monkeypatch.setattr(run_phase, "_run_session", session)
    root = tmp_path / "proj"
    root.mkdir()
    args = _explain_args(root, tmp_path / "missing.json", setup, dry_run=True)
    assert run_phase.run_explain(args, dict(KEY_ENV)) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["case"] == "setup" and report["logs"] == [".sdlc-cache/explain/setup.json"]
    record = explain.failed_run_record("setup", None, json.loads(setup.read_text()), [], {})
    assert record["step"] == "setup" and record["reason"].startswith("the project's setup failed")


def test_a_run_with_no_file_to_read_is_recorded_without_a_session(tmp_path, monkeypatch):
    record = explain.failed_run_record("red", None, None, [], {"GITHUB_RUN_ID": "1"})
    assert record["reason"] == explain.RUNNER_DID_NOT_FINISH and record["explanation"] == []


def test_a_red_review_pass_keeps_the_change_at_its_phase(project, monkeypatch, capsys):
    """The review, finding B1: the explain step on a red review pass stores its result and commits
    it on the build branch without moving the change to (e), so the next deploy run's guard
    still finds it at (d)."""
    root, change = project
    set_state(change, "test", gate_phase="test", gate_result="passed")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "at d")
    write(change / "evidence" / "claude-review.stderr.txt", "Traceback: review/cli.py\n")
    out = root.parent / "run.json"
    out.write_text(
        json.dumps(
            {
                "explain": "red",
                "exit_code": 1,
                "change_id": "0001",
                "gate_phase": "review",
                "branch_phase": "deploy",
                "change_dir": "changes/0001-percent-helper",
                "stderr_file": "changes/0001-percent-helper/evidence/claude-review.stderr.txt",
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(run_phase, "_run_session", Session("the review CLI crashed\nreal"))
    monkeypatch.setattr(run_phase, "record_spend", lambda *a, **k: True)
    assert run_phase.run_explain(_explain_args(root, out), dict(KEY_ENV)) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["commit"]["ok"] is True and report["session"]["result_file"] == (
        "claude-explain.json"
    )
    assert status_mod.read_status(change).phase == "test"
    committed = _git(root, "show", "HEAD:changes/0001-percent-helper/status.yaml")
    assert "phase: test" in committed


def test_a_red_run_the_runner_already_explained_costs_no_session(tmp_path, monkeypatch, capsys):
    """The review, nit N1: the only file is the runner's own JSON (a missing App, a crash
    before the guard): the reason is deterministic and no model is called."""
    session = Session("x")
    monkeypatch.setattr(run_phase, "_run_session", session)
    out = tmp_path / "run.json"
    out.write_text(json.dumps({"explain": "red", "exit_code": 1, "why": "no App"}), "utf-8")
    args = _explain_args(tmp_path, out, dry_run=True)
    assert run_phase.run_explain(args, dict(KEY_ENV)) == 0
    assert json.loads(capsys.readouterr().out)["logs"] == [] and session.calls == []


def test_the_two_halves_run_in_two_steps(project, monkeypatch, capsys, tmp_path):
    """The review, finding S4: the read-only half writes its lines to a file with no GitHub
    token in its environment; the writing half reads that file and calls no model."""
    root, change = project
    write(change / "evidence" / "claude-build.stderr.txt", "boom\n")
    out = tmp_path / "run.json"
    out.write_text(
        json.dumps(
            {
                "explain": "red",
                "exit_code": 1,
                "change_id": "0001",
                "gate_phase": "build",
                "change_dir": "changes/0001-percent-helper",
                "stderr_file": "changes/0001-percent-helper/evidence/claude-build.stderr.txt",
            }
        ),
        encoding="utf-8",
    )
    session = Session("the session crashed\nlooks real")
    monkeypatch.setattr(run_phase, "_run_session", session)
    monkeypatch.setattr(run_phase, "record_spend", lambda *a, **k: True)
    lines = tmp_path / "explain.json"
    assert run_phase.run_explain(_explain_args(root, out, lines=str(lines)), dict(KEY_ENV)) == 0
    capsys.readouterr()
    assert json.loads(lines.read_text(encoding="utf-8"))["lines"] == [
        "the session crashed",
        "looks real",
    ]
    assert not (change / "evidence" / "claude-explain.json").exists()  # nothing written yet
    monkeypatch.setattr(run_phase, "_run_session", None)  # the writing half calls no model
    args = _explain_args(root, out, publish=str(lines))
    assert run_phase.run_explain(args, {"GITHUB_TOKEN": FAKE_TOKEN}) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["case"] == "red" and (change / "evidence" / "claude-explain.json").is_file()
    assert report["record"]["reason"] == explain.NO_RUN_ID
    # a missing lines file (the read-only step failed): a record with no lines
    args = _explain_args(root, out, publish=str(tmp_path / "none.json"))
    assert run_phase.run_explain(args, {}) == 0
    assert json.loads(capsys.readouterr().out)["lines"] == []


def test_a_reason_carrying_a_secret_is_withheld():
    """The review, finding S2: a setup's last output line can carry a token."""
    token = "ghp_" + "a" * 36
    setup = {"command": "pip install", "exit_code": 1, "output": f"401 https://x:{token}@idx"}
    record = explain.failed_run_record("setup", None, setup, [], {})
    assert record["reason"] == explain.REASON_WITHHELD and token not in json.dumps(record)


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
        "a": {"change_id": "0004", "reason": "claude exited 1", "explanation": ["x", "y"]},
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
    assert "cancelled; no failed-run record" in lines[2]
    assert "attempt 2" in lines[3] and "no failed-run record" in lines[3]  # its record parked
    assert "change 0004 — claude exited 1 — explanation (model-written): x; y" in lines[4]
    assert "parked one" not in text and "forged" not in text and "old" not in text


def test_a_record_s_mentions_and_links_are_inert_and_the_runs_are_paged():
    """The review, findings S1 and S6: a record is data a session could write, so a mention
    or a link in it never notifies; a busy repository's runs span several pages."""
    pages = {
        "first": {"error": "", "data": {"workflow_runs": [_run(1, "success")]},
                  "headers": {"Link": '<https://api/next>; rel="next"'}},
        "next": {"error": "", "data": {"workflow_runs": [_run(7, "failure")]}},
    }  # fmt: skip
    record = {"reason": "ping @owner [x](https://evil) <img>", "explanation": ["@team"]}

    def get(url):
        if url == "https://api/next":
            return pages["next"]
        if "/actions/runs?" in url:
            return pages["first"]
        if "/git/matching-refs/" in url:
            return {
                "error": "",
                "data": [{"ref": "refs/sdlc/failed-runs/7-1", "object": {"sha": "s"}}],
            }
        import base64

        return {
            "error": "",
            "data": {"content": base64.b64encode(json.dumps(record).encode()).decode()},
        }

    now = datetime(2026, 10, 23, tzinfo=timezone.utc)
    text = failed_runs.render(failed_runs.collect("o/r", now, get, "https://api"))
    assert "run 7" in text and "@owner" not in text and "@team" not in text
    assert "](https://evil)" not in text and "<img>" not in text


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
PARKED_ON_CANCEL = ("design", "build", "test", "deploy", "fix")  # decision 41, point 2


@pytest.mark.parametrize("name", EXPLAINED)
def test_each_phase_workflow_explains_after_a_fresh_framework_checkout(name):
    text = (WORKFLOWS / f"sdlc-{name}.yml").read_text(encoding="utf-8")
    steps = text.split("\n      - ")
    explain_at = next(i for i, s in enumerate(steps) if "--phase explain" in s)
    if name in PARKED_ON_CANCEL:
        # decision 41 (R67): the park after a cancelled run sits between the checkout's check
        # and the explain steps, so it runs first in the minutes GitHub leaves after the cancel
        park = steps[explain_at - 1]
        assert park.startswith("name: Park the change after a cancelled run")
        assert f"--phase {name} --cancelled " in park
        assert '--out "$RUNNER_TEMP/sdlc-run.json"' in park
        assert "steps.explain_checkout.outcome == 'success'" in park
        assert "(steps.setup.outcome == 'cancelled' || steps.phase.outcome == 'cancelled')" in park
        assert "steps.review.outcome" not in park  # a cancelled review pass does not park
        assert "ANTHROPIC_API_KEY" not in park and "CLAUDE_CODE_OAUTH_TOKEN" not in park
        assert "continue-on-error: true" in park and "# sdlc:commands.env" not in park
        assert "SDLC_JOB_TIMEOUT_MINUTES" in text  # the park tells GitHub's cancel from a hand's
        steps = steps[: explain_at - 1] + steps[explain_at:]
        explain_at -= 1
    names = [re.match(r"(?:name: )?(.*)", s).group(1) for s in steps]
    assert names[explain_at - 3].startswith("Remove the framework checkout before the explain")
    assert (
        "path: framework" in steps[explain_at - 2]
        and "persist-credentials: false" in (steps[explain_at - 2])
    )
    assert "checkout_check.py" in steps[explain_at - 1]
    read_half, publish = steps[explain_at], steps[explain_at + 1]
    for step in (read_half, publish):
        assert "continue-on-error: true" in step
        assert "if: always() && steps.explain_checkout.outcome == 'success'" in step
        assert "# sdlc:commands.env" not in step  # the project's secrets never reach it
    # the read-only half holds the model credential and no GitHub token; the writing half
    # the token and no model credential (the review, finding S4)
    assert "--lines " in read_half and "ANTHROPIC_API_KEY" in read_half
    assert "GITHUB_TOKEN" not in read_half and "SDLC_WORKFLOW_TOKEN" not in read_half
    assert "--publish " in publish and "GITHUB_TOKEN" in publish
    assert "ANTHROPIC_API_KEY" not in publish and "CLAUDE_CODE_OAUTH_TOKEN" not in publish
    failed = ("review", "phase") if name == "deploy" else ("phase",)
    for before in steps[explain_at - 3 : explain_at]:
        assert "steps.phase.outputs.explain == 'park'" in before
        assert "steps.setup.outcome == 'failure'" in before
        if name in PARKED_ON_CANCEL:
            cancelled = "steps.setup.outcome == 'cancelled' || steps.phase.outcome == 'cancelled'"
            assert cancelled in before
        for step_id in failed:
            assert f"steps.{step_id}.outcome == 'failure'" in before
    # every phase run and the setup write the files the explain step reads
    for line in [ln for ln in text.splitlines() if ln.strip().startswith("run: python")]:
        if "run_phase.py" in line and "--find-change" not in line and "--phase explain" not in line:
            assert '--out "$RUNNER_TEMP/sdlc-run.json"' in line, line
        if "project_setup.py" in line:
            assert '--out "$RUNNER_TEMP/sdlc-setup.json"' in line, line
    assert "        id: setup\n" in text


def test_a_letter_phase_in_a_run_file_is_not_read_as_its_name_since_1_0_48(tmp_path):
    """R45: ``phase: c`` in a run's out file was read as the build for one release; since
    1.0.48 (R45's sixth PR) the failed-run record keeps the phase as written."""
    record = explain.failed_run_record("red", {"phase": "c", "exit_code": 1}, None, [], {})
    assert record["phase"] == "c"
    record = explain.failed_run_record("red", {"phase": "build", "exit_code": 1}, None, [], {})
    assert record["phase"] == "build"
    record = explain.failed_run_record("red", {"phase": "review", "exit_code": 1}, None, [], {})
    assert record["phase"] == "review"


# --- R45's PR 2: the step's older name, refused since 1.0.48 (R45's sixth PR) -------------------
def test_the_older_phase_name_triage_is_refused_since_1_0_48(tmp_path, monkeypatch, capsys):
    """A workflow copy from before R45's PR 2 passed ``--phase triage``; since 1.0.48 (R45's
    sixth PR) the runner refuses it (exit 2) and ``--phase explain`` runs the read-only step."""
    for var, value in KEY_ENV.items():
        monkeypatch.setenv(var, value)
    argv = ["--root", str(tmp_path), "--phase", "triage", "--log", "build.log", "--dry-run"]
    with pytest.raises(SystemExit) as exited:
        run_phase.main(argv)
    assert exited.value.code == 2
    assert "invalid choice: 'triage'" in capsys.readouterr().err
    argv[argv.index("triage")] = "explain"
    assert run_phase.main(argv) == run_phase.EXIT_OK
    report = json.loads(capsys.readouterr().out)
    assert report["phase"] == "explain"
    assert report["argv"][report["argv"].index("--allowedTools") + 1] == "Read"


def test_the_runner_no_longer_writes_the_older_step_output_since_1_0_48(tmp_path):
    """A workflow copy from before R45's PR 2 tested ``steps.phase.outputs.triage``; since
    1.0.48 (R45's sixth PR) the runner writes only ``explain=``."""
    out, output = tmp_path / "run.json", tmp_path / "github-output"
    args = Args(root=str(tmp_path), phase="build", out=str(out))
    run_phase.write_run_out(args, {"GITHUB_OUTPUT": str(output)}, {"why": "no App"}, 1)
    assert output.read_text(encoding="utf-8").splitlines() == ["explain=red"]
    assert json.loads(out.read_text(encoding="utf-8"))["explain"] == "red"


def test_a_run_file_s_older_triage_case_is_not_read_since_1_0_48():
    """The out file's case was ``triage`` before R45's PR 2; since 1.0.48 (R45's sixth PR)
    only ``explain`` is read."""
    assert explain.case_of({"triage": "park"}, None) is None
    assert explain.case_of({"triage": "red"}, {"ok": True}) is None
    assert explain.case_of({"explain": None, "triage": "park"}, None) is None
    assert explain.case_of({"explain": "park"}, None) == "park"


def test_a_gate_record_s_older_triage_key_is_not_read_since_1_0_48():
    """A park written before R45's PR 2 kept the lines under ``triage``; since 1.0.48 (R45's
    sixth PR) that key is not read, and ``explanation`` is."""
    result = gate_mod.GateResult.from_dict({**PARK, "change_id": "0001", "triage": ["a", "b"]})
    assert result.explanation == []
    assert "Explanation (model-written)" not in result.what_i_need()
    assert "triage" not in result.as_dict()
    result = gate_mod.GateResult.from_dict({**PARK, "change_id": "0001", "explanation": ["a", "b"]})
    assert result.explanation == ["a", "b"]
    assert "Explanation (model-written)" in result.what_i_need()
    data = result.as_dict()
    assert data["explanation"] == ["a", "b"] and "triage" not in data


def test_a_failed_run_record_s_older_triage_key_is_not_read_since_1_0_48():
    """A record written before R45's PR 2 kept its lines under ``triage``; since 1.0.48
    (R45's sixth PR) the digest's line shows only ``explanation``."""
    text = failed_runs.line(
        {"run": _run(8, "failure"), "record": {"reason": "claude exited 1", "triage": ["x"]}}
    )
    assert "claude exited 1" in text and "explanation (model-written)" not in text
    text = failed_runs.line(
        {"run": _run(8, "failure"), "record": {"reason": "claude exited 1", "explanation": ["x"]}}
    )
    assert "claude exited 1 — explanation (model-written): x" in text


def test_the_older_result_file_keeps_its_own_run_name_since_1_0_48(tmp_path):
    """``evidence/claude-triage.json`` (before R45's PR 2) was read as the explain step's
    run for one release; since 1.0.48 (R45's sixth PR) its run is not mapped: it still counts
    toward the spend the budget reads, under its own name ``triage``."""
    from gate import limits

    for name, usd in (("claude-triage.json", 0.1), ("claude-explain.json", 0.2)):
        write(tmp_path / name, json.dumps({"total_cost_usd": usd}))
    spend = limits.spend_from_runs(tmp_path)
    assert spend["total_usd"] == pytest.approx(0.3)
    assert sorted((e["source"], e["run"]) for e in spend["entries"]) == [
        ("claude-explain.json", "explain"),
        ("claude-triage.json", "triage"),
    ]
