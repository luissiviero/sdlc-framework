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
from tests.test_ci import Args, fake_cli, git, pr_route, set_state, write

project = ci_tests.project
fake_claude = ci_tests.fake_claude

JOB_ENV = {"SDLC_JOB_TIMEOUT_MINUTES": "260"}
AT_TIMEOUT = "the job was cancelled at its timeout-minutes (260) while the session ran"


# GitHub's cancel interrupts the step's process (SIGINT, then SIGTERM): the runner's step ends
# wherever it was, and its ``finally`` parks nothing (``run_phase``)
Cancelled = KeyboardInterrupt


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


def _set_stage(args, stage: str) -> None:
    path = run_phase.cancel_state_path(args.out)
    data = json.loads(path.read_text(encoding="utf-8"))
    path.write_text(json.dumps({**data, "stage": stage}), encoding="utf-8")


def test_a_park_the_run_wrote_before_the_cancel_is_published_again_not_replaced(
    project, fake_claude, monkeypatch, tmp_path, capsys
):
    """The review of this PR, finding 1: a park written to status.yaml (the commands step's
    red target) before the cancel stopped its publication is published again with the
    review request; its reason stands."""
    root, change, args, env, calls = _cancelled_round(project, fake_claude, monkeypatch, tmp_path)
    _set_stage(args, "after")
    st = status_mod.read_status(change)
    st.park("commands: not green: test (exit 1)")
    status_mod.write_status(change, st)
    _elapsed(monkeypatch, 261.0)
    out = _park(args, env, capsys)
    assert out["republished"] == "commands: not green: test (exit 1)"
    assert status_mod.read_status(change).parked_reason == "commands: not green: test (exit 1)"
    assert any(argv[:1] == ["upsert"] and "--request-review" in argv for _s, argv in calls)
    # the session's uncommitted work is not the park's to keep at "after"
    assert " M src/x.py" in git(root, "status", "--porcelain", "--", "src/x.py")


def test_at_session_a_park_the_session_wrote_is_replaced_by_the_cancel_s(
    project, fake_claude, monkeypatch, tmp_path, capsys
):
    """parked_reason is not an owner field: a session's park never skips the replay."""
    _root, change, args, env, _calls = _cancelled_round(project, fake_claude, monkeypatch, tmp_path)
    st = status_mod.read_status(change)
    st.park("limits: the session says so")
    status_mod.write_status(change, st)
    _elapsed(monkeypatch, 261.0)
    _park(args, env, capsys)
    assert AT_TIMEOUT in status_mod.read_status(change).parked_reason


def test_a_fix_round_cancelled_after_its_checks_keeps_nothing_uncommitted(
    project, fake_claude, monkeypatch, tmp_path, capsys
):
    """Finding 4: at "after" the commands step had run in the tree, so its output is not
    committed as the session's work."""
    root, change, args, env, _calls = _cancelled_round(project, fake_claude, monkeypatch, tmp_path)
    _set_stage(args, "after")
    _elapsed(monkeypatch, 261.0)
    head = git(root, "rev-parse", "HEAD").strip()
    out = _park(args, env, capsys)
    what = "the job was cancelled at its timeout-minutes (260) after the session ended"
    assert out["parked"] == f"cancelled: {what}; no gate judged the run" and "work" not in out
    assert "src/x.py" not in git(root, "diff", "--name-only", head, "HEAD")
    check = next(ch for ch in gaps._gate_c(change)["checks"] if not ch["ok"])
    assert check["name"] == "cancelled" and check["need"] == run_phase.CANCEL_FIX_NEED


def test_a_run_that_updated_its_pr_parks_nothing(
    project, fake_claude, monkeypatch, tmp_path, capsys
):
    _root, change, args, env, _calls = _cancelled_round(project, fake_claude, monkeypatch, tmp_path)
    _set_stage(args, "done")
    out = _park(args, env, capsys)
    assert out["skipped"] == run_phase.CANCEL_DONE
    assert status_mod.read_status(change).parked_reason == "commands: not green"


@pytest.mark.parametrize(
    ("field", "value", "why"),
    [
        ("change_dir", "../elsewhere", "its change folder '../elsewhere' is not change '0001'"),
        ("change_dir", "changes/0002-other", "is not change '0001'"),
        ("fix_branch", "main", "its fix round's head 'main' is not the workflow's"),
        ("phase", "explain", "its phase 'explain' is not a phase run"),
    ],
)
def test_a_state_that_is_not_this_run_s_parks_nothing(
    project, fake_claude, monkeypatch, tmp_path, capsys, field, value, why
):
    """Finding 5: the project's commands run outside the sandbox in the same job and could
    rewrite the file; a state that is not this run's change, phase or head parks nothing."""
    _root, change, args, env, _calls = _cancelled_round(project, fake_claude, monkeypatch, tmp_path)
    path = run_phase.cancel_state_path(args.out)
    data = json.loads(path.read_text(encoding="utf-8"))
    path.write_text(json.dumps({**data, field: value}), encoding="utf-8")
    env["HEAD_REF"] = "sdlc/0001/build"
    out = _park(args, env, capsys)
    assert out["skipped"].startswith("nothing to park: the saved state is not this run's (")
    assert why in out["skipped"]
    assert status_mod.read_status(change).parked_reason == "commands: not green"
    written = json.loads(Path(args.out).read_text(encoding="utf-8"))
    assert written["explain"] is None  # no model call in the minutes left


def test_a_kill_after_the_result_was_stored_does_not_flag_the_runner_s_own_file(
    project, fake_claude, monkeypatch, tmp_path, capsys
):
    """Finding 8: the session's result, stored by the runner, is not "created by the session"."""
    root, change, args, env, _calls = gaps._owner_round(
        project, fake_claude, monkeypatch, tmp_path, gaps.EDITS, gaps.FAILED_RUN
    )
    args.out = str(tmp_path / "temp" / "sdlc-run.json")
    env.update(JOB_ENV)

    def stopped(*a, **k):
        raise Cancelled

    monkeypatch.setattr(run_phase, "store_stderr", stopped)
    with pytest.raises(Cancelled):
        run_phase.run_phase(args, env)
    assert (change / "evidence" / "claude-fix.json").is_file()
    _elapsed(monkeypatch, 261.0)
    _park(args, env, capsys)
    reason = status_mod.read_status(change).parked_reason
    assert reason.startswith(f"fix: the round ended before its gate ({AT_TIMEOUT})"), reason


def test_an_interrupted_runner_parks_and_writes_nothing_on_its_way_out(
    project, fake_claude, monkeypatch, tmp_path, capsys
):
    """Finding 2: on the interrupt the runner's ``finally`` makes no half park (decision 29's
    release) and writes no result file the explain step would spend a model call on."""
    root, change, args, env, _seen = auto_tests.fix_run(project, fake_claude, monkeypatch, tmp_path)
    args.out = str(tmp_path / "temp" / "sdlc-run.json")
    _cancel_in_session(monkeypatch)
    released: list = []
    monkeypatch.setattr(run_phase, "release_unfinished_round", lambda *a: released.append(a))
    with pytest.raises(Cancelled):
        run_phase.run_phase(args, env)
    assert released == [] and not Path(args.out).exists()
    assert run_phase.cancel_state_path(args.out).is_file()


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
    with pytest.raises(Cancelled):
        run_phase.run_phase(args, env)
    assert gaps._gate_c(change)["label"] == c.FIXING_LABEL  # the runner parked nothing
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


def test_the_record_is_marked_parked_and_the_digest_says_the_cancelled_run_parked(
    project, monkeypatch, tmp_path
):
    root, _change = project
    seen: list = []
    monkeypatch.setattr(
        run_phase.explain_mod, "write_record_ref", lambda r, rec, env: seen.append(rec) or {}
    )
    state = {"phase": "fix", "change_id": "0001"}
    env = {"GITHUB_RUN_ID": "9", "GITHUB_RUN_ATTEMPT": "1", "GITHUB_REPOSITORY": "o/r"}
    run_phase.write_cancelled_record(env, root, state, AT_TIMEOUT)
    assert seen[0]["parked"] is True and seen[0]["reason"] == AT_TIMEOUT
    assert seen[0]["explanation"] == []
    run_phase.write_cancelled_record(env, root, state, AT_TIMEOUT, parked=False)
    assert seen[1]["parked"] is False
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
    # the cancelled run decision 41 parked says so (a forged record hides no run); a red
    # park keeps its bare line
    assert [e["run"]["id"] for e in got["runs"]] == [1, 2]
    lines = failed_runs.render(got).splitlines()
    assert lines[2].endswith(failed_runs.PARKED_ON_CANCEL) and "no failed-run record" in lines[3]


def test_a_stale_lock_and_a_stopped_merge_are_cleared_when_no_git_runs(
    tmp_path, monkeypatch, capsys
):
    repo = tmp_path / "r"
    repo.mkdir()
    git(repo, "init", "-q", "-b", "main")
    git(repo, "config", "user.email", "t@t")
    git(repo, "config", "user.name", "t")
    write(repo / "a.txt", "one\n")
    git(repo, "add", ".")
    git(repo, "commit", "-q", "-m", "one")
    git(repo, "checkout", "-q", "-b", "side")
    write(repo / "a.txt", "side\n")
    git(repo, "commit", "-qam", "side")
    git(repo, "checkout", "-q", "main")
    write(repo / "a.txt", "main\n")
    git(repo, "commit", "-qam", "main")
    import subprocess

    subprocess.run(["git", "merge", "side"], cwd=repo, capture_output=True, check=False)
    assert (repo / ".git" / "MERGE_HEAD").is_file()
    (repo / ".git" / "index.lock").write_text("", encoding="utf-8")
    monkeypatch.setattr(run_phase, "git_process_running", lambda: True)
    assert run_phase.clear_stopped_git(repo) == []  # a live git may hold them
    monkeypatch.setattr(run_phase, "git_process_running", lambda: False)
    done = run_phase.clear_stopped_git(repo)
    assert done == [run_phase.INDEX_LOCK_REMOVED, run_phase.MERGE_ABORTED]
    assert not (repo / ".git" / "MERGE_HEAD").exists()
    assert git(repo, "status", "--porcelain") == ""
    assert run_phase.clear_stopped_git(repo) == []
    capsys.readouterr()


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
