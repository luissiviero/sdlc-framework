"""Decision 41, point 2 (ROADMAP R67, plugin 1.0.50): a job GitHub cancels parks the change.

GitHub's cancel stops the runner's step with the runner in it, so the runner saves what a park
needs beside ``--out`` as the run goes, and the workflow's step on ``always()`` that reads
``cancelled`` runs the fresh runner with ``--cancelled``. The cancel is simulated by an
exception the session's ``invoke`` raises after the fake session wrote its files, as GitHub's
interrupt would end the runner; ``--cancelled`` then runs as the next step does.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest
from ci import run_phase
from pr import failed_runs

from state import conventions as c
from state import status as status_mod
from tests import test_auto_round as auto_tests
from tests import test_ci as ci_tests
from tests import test_explain as explain_tests
from tests import test_fix_round_gaps as gaps
from tests.test_ci import Args, fake_cli, git, pr_route, set_state

project = ci_tests.project
fake_claude = ci_tests.fake_claude

JOB_ENV = {"SDLC_JOB_TIMEOUT_MINUTES": "260"}
AT_TIMEOUT = "the job was cancelled at its timeout-minutes (260) while the session ran"


class Cancelled(BaseException):
    """GitHub's cancel: the runner's step ends here, whatever it was doing."""


def _cancel_in_session(monkeypatch) -> None:
    """The fake session runs (its files are written), then the job is cancelled."""
    real = run_phase.invoke

    def invoke(argv, root, env, timeout):
        real(argv, root, env, timeout)
        raise Cancelled

    monkeypatch.setattr(run_phase, "invoke", invoke)


def _elapsed(monkeypatch, minutes: float | None, why: str = "") -> None:
    monkeypatch.setattr(run_phase, "job_elapsed_minutes", lambda env: (minutes, why))


def _cancelled_round(project, fake_claude, monkeypatch, tmp_path, script=gaps.EDITS):
    """The owner's fix round on the build PR, cancelled while its session ran."""
    root, change, args, env, calls = gaps._owner_round(
        project, fake_claude, monkeypatch, tmp_path, script, gaps.FAILED_RUN
    )
    out = tmp_path / "temp" / "sdlc-run.json"
    args.out = str(out)
    env.update(JOB_ENV)
    _cancel_in_session(monkeypatch)
    with pytest.raises(Cancelled):
        run_phase.run_phase(args, env)
    state = json.loads((tmp_path / "temp" / "sdlc-run.state.json").read_text("utf-8"))
    assert state["stage"] == "session" and state["phase"] == "fix"
    return root, change, args, env, calls


def _park(args, env, capsys) -> dict:
    capsys.readouterr()
    args.cancelled = True
    assert run_phase.run_cancelled(args, env) == run_phase.EXIT_OK
    return json.loads(capsys.readouterr().out)


def test_a_fix_round_cancelled_at_its_timeout_keeps_its_work_and_parks(
    project, fake_claude, monkeypatch, tmp_path, capsys
):
    root, change, args, env, calls = _cancelled_round(project, fake_claude, monkeypatch, tmp_path)
    _elapsed(monkeypatch, 261.0)
    assert " M src/x.py" in git(root, "status", "--porcelain", "--", "src")
    out = _park(args, env, capsys)
    sha = git(root, "rev-parse", "HEAD").strip()
    assert git(root, "log", "-1", "--format=%s").strip() == (
        f"run(fix): unfinished round's work kept, not gated (gap 3): {AT_TIMEOUT}"
    )
    files = gaps._committed(root)
    assert "src/x.py" in files and "src/new.py" in files
    reason = (
        f"fix: the round ended before its gate ({AT_TIMEOUT}); its work is kept in "
        f"{sha[:10]}, not gated"
    )
    assert status_mod.read_status(change).parked_reason == reason
    assert out["cancelled"] == AT_TIMEOUT and out["stage"] == "session"
    assert out["work"]["kept"] == ["src/new.py", "src/x.py"]
    record = gaps._gate_c(change)
    assert record["label"] == c.NEEDS_HUMAN_LABEL
    assert [ch["name"] for ch in record["checks"] if not ch["ok"]] == ["fix"]
    # the review request, the only notification (decision 31), on the PR's head
    assert any(
        argv[:1] == ["upsert"] and "--request-review" in argv and "--head" in argv
        for _s, argv in calls
    )
    # the explain steps after it find no case, so their red record never replaces the park's
    written = json.loads(Path(args.out).read_text(encoding="utf-8"))
    assert written["explain"] is None and written["cancelled"] is True


def test_a_cancel_by_hand_says_so(project, fake_claude, monkeypatch, tmp_path, capsys):
    root, change, args, env, _calls = _cancelled_round(project, fake_claude, monkeypatch, tmp_path)
    _elapsed(monkeypatch, 30.4)
    _park(args, env, capsys)
    assert status_mod.read_status(change).parked_reason.startswith(
        "fix: the round ended before its gate (the job was cancelled by hand after 30 of its "
        "260 minutes while the session ran)"
    )


def test_a_cancel_the_runner_cannot_place_says_both(
    project, fake_claude, monkeypatch, tmp_path, capsys
):
    _root, change, args, env, _calls = _cancelled_round(project, fake_claude, monkeypatch, tmp_path)
    _elapsed(monkeypatch, None, "HTTP 403")
    _park(args, env, capsys)
    assert (
        "(the job was cancelled while the session ran (at its timeout-minutes or by hand: "
        "HTTP 403))" in status_mod.read_status(change).parked_reason
    )
    env.pop("SDLC_JOB_TIMEOUT_MINUTES")
    assert run_phase.cancel_what(env, "session") == (
        "the job was cancelled while the session ran (at its timeout-minutes or by hand: "
        "no SDLC_JOB_TIMEOUT_MINUTES)"
    )


def test_a_cancelled_session_that_wrote_a_runner_file_parks_on_it_and_keeps_no_work(
    project, fake_claude, monkeypatch, tmp_path, capsys
):
    """The checks the runner makes after the session are made from the saved snapshots: the
    planted file is put back, the park names it, and the tree is not the owner's to keep."""
    root, change, args, env, _calls = _cancelled_round(
        project, fake_claude, monkeypatch, tmp_path, gaps.EDITS + auto_tests.PLANT
    )
    _elapsed(monkeypatch, 261.0)
    head = git(root, "rev-parse", "HEAD").strip()
    out = _park(args, env, capsys)
    assert out["parked"].startswith(c.OWNER_FIELDS_PARK_PREFIX)
    assert "evidence/auto-round.json: the session created it" in out["parked"]
    assert out["parked"].endswith(f"({AT_TIMEOUT})") and "work" not in out
    assert not (change / "evidence" / c.AUTO_ROUND_FILE).exists()
    assert " M src/x.py" in git(root, "status", "--porcelain", "--", "src/x.py")
    assert "src/x.py" not in git(root, "diff", "--name-only", head, "HEAD")


def test_no_saved_state_parks_nothing(project, monkeypatch, tmp_path, capsys):
    root, change = project
    args = Args(root=str(root), phase="build", out=str(tmp_path / "sdlc-run.json"))
    args.cancelled = True
    assert run_phase.run_cancelled(args, {}) == run_phase.EXIT_OK
    out = json.loads(capsys.readouterr().out)
    assert out["skipped"] == run_phase.CANCEL_NO_STATE
    assert status_mod.read_status(change).parked_reason is None
    assert run_phase.cancel_state_path(None) is None


def test_a_run_that_parked_before_the_cancel_is_not_parked_twice(
    project, fake_claude, monkeypatch, tmp_path, capsys
):
    _root, change, args, env, _calls = _cancelled_round(project, fake_claude, monkeypatch, tmp_path)
    st = status_mod.read_status(change)
    st.park("limits: the runner parked it")  # the round had begun parking when cancelled
    status_mod.write_status(change, st)
    out = _park(args, env, capsys)
    assert out["skipped"] == run_phase.CANCEL_ALREADY_PARKED.format(
        reason="limits: the runner parked it"
    )


def test_a_build_cancelled_before_its_session_parks_with_the_cancel_reason(
    project, fake_claude, monkeypatch, tmp_path, capsys
):
    """The other phases park as the runner's own timeout park does: the change folder
    committed with the reason, the check ``cancelled`` and its "what I need from you"."""
    root, change = project
    calls = pr_route(monkeypatch)
    monkeypatch.setattr(
        run_phase, "preflight", lambda *a: {"allow": True, "permission_mode": "acceptEdits"}
    )
    set_state(change, "design", gate_phase="design", gate_result="passed")

    def cancelled(repo, env):  # the job is cancelled after the preflight, before the session
        raise Cancelled

    monkeypatch.setattr(run_phase, "ensure_labels", cancelled)
    args = Args(
        root=str(root), phase="build", dry_run=False, no_dispatch=True,
        claude=fake_cli(fake_claude), out=str(tmp_path / "temp" / "sdlc-run.json"),
    )  # fmt: skip
    env = {**ci_tests.KEY_ENV, "GITHUB_TOKEN": ci_tests.FAKE_TOKEN, **JOB_ENV}
    with pytest.raises(Cancelled):
        run_phase.run_phase(args, env)
    _elapsed(monkeypatch, 262.0)
    out = _park(args, env, capsys)
    what = "the job was cancelled at its timeout-minutes (260) before the session started"
    assert out["stage"] == "prepared" and out["cancelled"] == what
    reason = f"cancelled: {what}; no gate judged the run"
    st = status_mod.read_status(change)
    assert st.parked_reason == reason
    # the park's own set-phase and commit (the plugin CLIs are fakes here, ``pr_route``)
    assert any(argv[:1] == ["set-phase"] and argv[-1] == "build" for _s, argv in calls)
    assert any(argv[:1] == ["commit-phase"] and "--push" in argv for _s, argv in calls)
    assert git(root, "rev-parse", "--abbrev-ref", "HEAD").strip() == "sdlc/0001/build"
    record = json.loads((change / "evidence" / "gate-build.json").read_text(encoding="utf-8"))
    assert record["label"] == c.NEEDS_HUMAN_LABEL
    check = next(ch for ch in record["checks"] if not ch["ok"])
    assert check["name"] == "cancelled"
    assert check["need"] == run_phase.CANCEL_NEED.format(phase="build", id="0001")
    assert any(argv[:1] == ["upsert"] and "--request-review" in argv for _s, argv in calls)


def test_an_automatic_round_cancelled_with_nothing_to_keep_parks_as_decision_29_does(
    project, fake_claude, monkeypatch, tmp_path, capsys
):
    """``park_unfinished_round`` leaves such a round to decision 29's own park, which the
    stopped runner would have made on its way out: the cancel step makes it."""
    root, change, args, env, _seen = auto_tests.fix_run(project, fake_claude, monkeypatch, tmp_path)
    env.pop("FAKE_CLAUDE_GATE", None)
    env.update(JOB_ENV)
    args.out = str(tmp_path / "temp" / "sdlc-run.json")
    auto_tests.dispatch_recorder(monkeypatch)
    real = run_phase.invoke

    def invoke(argv, root, env, timeout):
        real(argv, root, env, timeout)
        raise Cancelled

    monkeypatch.setattr(run_phase, "invoke", invoke)
    # the runner killed before its ``finally`` parks the round: only the cancel step does
    monkeypatch.setattr(run_phase, "release_unfinished_round", _release_after_the_kill)
    with pytest.raises(Cancelled):
        run_phase.run_phase(args, env)
    _elapsed(monkeypatch, 261.0)
    _park(args, env, capsys)
    record = gaps._gate_c(change)
    assert record["label"] == c.NEEDS_HUMAN_LABEL
    reason = status_mod.read_status(change).parked_reason
    assert reason.startswith("fix_rounds: the automatic fix round 1 did not finish: ")
    assert AT_TIMEOUT in reason
    data = json.loads((change / "evidence" / c.AUTO_ROUND_FILE).read_text(encoding="utf-8"))
    assert data["status"] == "unfinished"
    assert git(root, "status", "--porcelain", "--", "src") == ""


_REAL_RELEASE = run_phase.release_unfinished_round


def _release_after_the_kill(args, env, track, code):
    """The runner's own release, skipped while the runner is being killed; the cancel step
    calls the real one."""
    if getattr(args, "cancelled", False):
        return _REAL_RELEASE(args, env, track, code)
    return None


def test_the_cancelled_entry_refuses_the_review_pass(capsys):
    """Decision 11's note keeps a cancelled review pass red, never parked."""
    code = run_phase.main(["--phase", "review", "--cancelled", "--out", "x.json"])
    assert code == run_phase.EXIT_USAGE
    assert "--cancelled does not apply to --phase review" in capsys.readouterr().err


def test_the_review_pass_saves_no_state_and_a_run_starts_without_a_stale_one(tmp_path):
    out = tmp_path / "sdlc-run.json"
    state = run_phase.cancel_state_path(str(out))
    assert state == tmp_path / "sdlc-run.state.json"
    args = Args(out=str(out), dry_run=False)
    run_phase.save_cancel_state(args, "prepared", change_dir="changes/x", phase="build")
    run_phase.save_cancel_state(args, "session", pre_head="abc")
    data = run_phase.read_cancel_state(state)
    assert data["stage"] == "session" and data["phase"] == "build" and data["pre_head"] == "abc"
    # a dry run and a run without --out save nothing
    state.unlink()
    run_phase.save_cancel_state(Args(out=str(out), dry_run=True), "prepared", change_dir="x")
    run_phase.save_cancel_state(Args(out=None, dry_run=False), "prepared", change_dir="x")
    assert not state.exists()
    # an unknown stage or schema is no state
    state.write_text(json.dumps({"schema_version": 1, "stage": "x", "change_dir": "y"}), "utf-8")
    assert run_phase.read_cancel_state(state) is None
    assert run_phase._unb64("not base64!") is None and run_phase._unb64(None) is None
    assert run_phase._unb64(run_phase._b64(b"\x00x")) == b"\x00x"


def test_the_record_is_marked_parked_and_the_digest_leaves_the_cancelled_run_out(
    project, monkeypatch, tmp_path
):
    root, _change = project
    seen: list = []
    monkeypatch.setattr(
        run_phase.explain_mod, "write_record_ref", lambda r, rec, env: seen.append(rec) or {}
    )
    state = {"phase": "fix", "change_id": "0001"}
    env = {"GITHUB_RUN_ID": "9", "GITHUB_RUN_ATTEMPT": "1", "GITHUB_REPOSITORY": "o/r"}
    run_phase.write_cancelled_record(Args(root=str(root)), env, root, state, AT_TIMEOUT)
    assert seen[0]["parked"] is True and seen[0]["reason"] == AT_TIMEOUT
    assert seen[0]["explanation"] == []
    runs = [
        explain_tests._run(1, "cancelled", at="2026-10-21T08:00:00Z"),
        explain_tests._run(2, "failure", at="2026-10-22T08:00:00Z"),
    ]
    refs = [
        {"ref": "refs/sdlc/failed-runs/1-1", "object": {"sha": "a"}},
        {"ref": "refs/sdlc/failed-runs/2-1", "object": {"sha": "b"}},
    ]
    records = {"a": {"reason": "cancelled", "parked": True}, "b": {"reason": "x", "parked": True}}
    now = datetime(2026, 10, 23, tzinfo=timezone.utc)
    got = failed_runs.collect("o/r", now, explain_tests._api(runs, refs, records), "https://api")
    # the cancelled run decision 41 parked is in the queue; a red park keeps its bare line
    assert [e["run"]["id"] for e in got["runs"]] == [2]


def test_a_stale_index_lock_is_removed(tmp_path, capsys):
    (tmp_path / ".git").mkdir()
    (tmp_path / ".git" / "index.lock").write_text("", encoding="utf-8")
    assert run_phase.remove_index_lock(tmp_path) is True
    assert not (tmp_path / ".git" / "index.lock").exists()
    assert run_phase.remove_index_lock(tmp_path) is False
    assert run_phase.INDEX_LOCK_REMOVED in capsys.readouterr().err


def test_the_job_s_elapsed_minutes_come_from_its_runner(monkeypatch):
    from pr import github

    started = datetime.now(timezone.utc).replace(microsecond=0)
    jobs = {
        "jobs": [
            {"runner_name": "other", "started_at": "2026-01-01T00:00:00Z"},
            {"runner_name": "GitHub Actions 7", "started_at": started.isoformat()},
        ]
    }
    asked: list = []
    monkeypatch.setattr(github, "token", lambda: "t")
    monkeypatch.setattr(
        github, "_request", lambda m, url, tok, body=None: asked.append(url) or {"data": jobs}
    )
    env = {
        "GITHUB_REPOSITORY": "o/r",
        "GITHUB_RUN_ID": "5",
        "GITHUB_RUN_ATTEMPT": "2",
        "RUNNER_NAME": "GitHub Actions 7",
    }
    elapsed, why = run_phase.job_elapsed_minutes(env)
    assert elapsed is not None and 0 <= elapsed < 1 and why == ""
    assert asked == [f"{github.API_ROOT}/repos/o/r/actions/runs/5/attempts/2/jobs"]
    assert run_phase.job_elapsed_minutes({}) == (None, "not a workflow run")
    monkeypatch.setattr(github, "_request", lambda *a, **k: {"error": "HTTP 403"})
    assert run_phase.job_elapsed_minutes(env) == (None, "HTTP 403")
