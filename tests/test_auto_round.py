"""Decision 29 (plugin 1.0.3, ROADMAP R10): a red target the CI runner finds after the session
starts the next fix round by itself, the change parks only at the iteration cap after one
judged reset, and the owner-field guards accept that marked reset and nothing else.

The runner's commands step, the GitHub calls and the judge's ``claude -p`` are replaced by
fakes, as ``tests/test_ci.py`` does: no model, no network, no token.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest
from ci import auto_round, run_phase
from pr import description as desc
from pr import digest

from state import conventions as c
from state import status as status_mod
from tests import test_ci as ci_tests
from tests.test_ci import (
    DEFERRED_GATE_FILE,
    FAKE_RESULT,
    FAKE_TOKEN,
    GATE_FILE,
    KEY_ENV,
    ROOT,
    Args,
    fake_cli,
    git,
    pr_route,
    session_gate,
    set_state,
    write,
)

# the fixtures of tests/test_ci.py, used here by name
project = ci_tests.project
fake_claude = ci_tests.fake_claude

RUN_ENV = {
    "GITHUB_RUN_ID": "777",
    "GITHUB_SERVER_URL": "https://github.com",
    "GITHUB_REPOSITORY": "owner/name",
    "GITHUB_RUN_ATTEMPT": "1",
}


def runs(test_exit=1, **extra) -> dict:
    out = {
        "build": {"command": "python -m compileall -q .", "exit_code": 0, "output": ""},
        "test": {"command": "python -m pytest", "exit_code": test_exit, "output": "FAILED x"},
        "lint": {"command": "python -m ruff check .", "exit_code": 0, "output": ""},
    }
    out.update(extra)
    return out


def red_record(phase: str = "build", run_map=None, extra_checks=(), commands_details=None) -> dict:
    details = commands_details or {"ran_by": "runner", "runs": run_map or runs()}
    checks = [
        {"name": "artifacts", "ok": True, "reason": "ok", "need": "", "details": {}},
        {
            "name": "commands",
            "ok": False,
            "reason": "not green: test (exit 1)",
            "need": "Make the failing target pass (fix the code, not the test).",
            "details": details,
        },
        *extra_checks,
    ]
    return {
        **GATE_FILE,
        "phase": phase,
        "result": "park",
        "label": c.NEEDS_HUMAN_LABEL,
        "reason": "commands: not green: test (exit 1)",
        "checks": checks,
        "what_i_need": "## What I need from you\n- **commands**: not green\n",
    }


# --- 1. what is a red target ----------------------------------------------------------------
def test_a_park_on_red_targets_only_is_a_red_target_and_a_timeout_is_one():
    targets = auto_round.red_targets(red_record())
    assert [t["target"] for t in targets] == ["test"]
    assert targets[0]["exit_code"] == 1 and targets[0]["timed_out"] is False
    assert targets[0]["output_tail"] == "FAILED x" and targets[0]["command"] == "python -m pytest"
    hung = runs(test_exit=None)
    hung["test"]["timeout"] = 900
    targets = auto_round.red_targets(red_record(run_map=hung))
    assert targets[0]["timed_out"] is True and targets[0]["exit_code"] is None
    assert targets[0]["timeout"] == 900
    assert auto_round.targets_summary(targets) == "test (timed out)"
    # the evidence check failing on the logs of the same red run is part of it
    same_logs = {
        "name": "evidence",
        "ok": False,
        "reason": "evidence/test.log: exited 1",
        "need": "",
        "details": {"red": ["evidence/test.log: exit 1"], "red_files": ["test.log"]},
    }
    assert auto_round.red_targets(red_record(extra_checks=[same_logs])) is not None


def test_anything_else_is_not_a_red_target():
    other_log = {
        "name": "evidence",
        "ok": False,
        "reason": "x",
        "need": "",
        "details": {"red_files": ["lint.log"]},
    }
    missing_log = {"name": "evidence", "ok": False, "reason": "x", "details": {"missing": ["a"]}}
    plan = {"name": "plan_sync", "ok": False, "reason": "plan.md out of sync", "details": {}}
    did_not_start = runs(test_exit=None)  # no exit code and no timeout: the shell never ran
    cases = [
        red_record(extra_checks=[plan]),  # another check failed too
        red_record(extra_checks=[other_log]),  # a red log of a green target
        red_record(extra_checks=[missing_log]),  # a missing log
        red_record(commands_details={"missing": ["lint"]}),  # an sdlc.yaml gap
        red_record(commands_details={"ran_by": "runner"}),  # the step crashed: no runs
        red_record(run_map=did_not_start),
        red_record(run_map=runs(test_exit=127)),  # a tool missing on the runner
        red_record(run_map=runs(test_exit=126)),
        red_record(commands_details={"ran_by": "runner", "runs": runs(), "not_started": ["x"]}),
        {**red_record(), "result": "continue"},
        None,
    ]
    for record in cases:
        assert auto_round.red_targets(record) is None, record


def proof_check(items=None, **details) -> dict:
    items = (
        [
            {
                "item": "- state: evidence/proof/status.json status.code == 200",
                "kind": "state",
                "file": "evidence/proof/status.json",
                "approved": True,
                "outcome": "differs",
                "seen": 500,
            },
            {
                "item": "- screenshot: evidence/proof/home.png",
                "kind": "screenshot",
                "file": "evidence/proof/home.png",
                "approved": True,
                "outcome": "matches",
            },
            {
                "item": "- state: evidence/proof/status.json change == 9",
                "kind": "state",
                "file": "evidence/proof/status.json",
                "approved": False,
                "outcome": "differs",
                "seen": "0004",
            },
        ]
        if items is None
        else items
    )
    return {
        "name": "proof",
        "ok": False,
        "reason": "1 approved proof item(s) not met",
        "need": "",
        "details": {"items": items, **details} if items != "none" else details,
    }


def green_record_with(*extra_checks) -> dict:
    record = red_record(extra_checks=extra_checks)
    record["checks"][1] = {
        "name": "commands",
        "ok": True,
        "reason": "build, test, lint and drive exit 0",
        "need": "",
        "details": {"ran_by": "runner", "runs": runs(test_exit=0)},
    }
    return record


def test_a_failed_proof_entry_is_a_round_also_when_the_targets_are_green():
    targets = auto_round.red_targets(green_record_with(proof_check()))
    assert targets == [
        {
            "target": "proof",
            "items": [
                {
                    "item": "- state: evidence/proof/status.json status.code == 200",
                    "outcome": "differs",
                    "expected": "status.code == 200",
                    "seen": 500,
                }
            ],
        }
    ]
    assert auto_round.targets_summary(targets) == "proof (1 item)"
    # a red drive whose items were not produced is one round, its log among the constraint's
    drive_red = runs(test_exit=0, drive={"command": "npx playwright test", "exit_code": 1})
    drive_log = {
        "name": "evidence",
        "ok": False,
        "reason": "evidence/drive.log: exited 1",
        "need": "",
        "details": {"red_files": ["drive.log"]},
    }
    record = red_record(run_map=drive_red, extra_checks=[proof_check(), drive_log])
    targets = auto_round.red_targets(record)
    assert [t["target"] for t in targets] == ["drive", "proof"]
    assert auto_round.targets_summary(targets) == "drive (exit 1), proof (1 item)"


def test_a_failed_proof_entry_without_items_or_with_the_drive_removed_parks():
    assert auto_round.red_targets(green_record_with(proof_check(items="none"))) is None
    removed = proof_check(drive_removed=True)
    assert auto_round.red_targets(green_record_with(removed)) is None
    assert auto_round.red_targets(red_record(extra_checks=[removed])) is None
    # only items added in (c) failed: nothing approved to fix, a park
    added_only = proof_check(items=[proof_check()["details"]["items"][2]])
    assert auto_round.red_targets(green_record_with(added_only)) is None


def test_the_round_s_request_names_each_item_with_expected_and_seen():
    targets = auto_round.red_targets(green_record_with(proof_check()))
    request = auto_round.red_targets_request(
        {"round": 1, "cap": 2, "targets": targets, "head": "abc", "at": "now"}
    )
    body = request["body"]
    assert "found a red target or proof item: proof (1 item)" in body
    assert (
        "- `- state: evidence/proof/status.json status.code == 200` (differs): expected "
        "status.code == 200, seen 500"
    ) in body
    assert request["targets"][0]["items"][0]["seen"] == 500
    prompt = auto_round.judge_prompt("0004", "changes/0004-x", "c", 2, 2, targets)
    assert "drive.log" in prompt and "the record's `proof` entry" in prompt


def test_parse_verdict_reads_the_judge_s_json_and_nothing_else():
    assert auto_round.parse_verdict('{"reset": true, "reasons": "progress"}') == {
        "reset": True,
        "reasons": "progress",
    }
    fenced = 'Here it is:\n```json\n{"reset": false, "reasons": "same\\n failure"}\n```'
    assert auto_round.parse_verdict(fenced) == {"reset": False, "reasons": "same failure"}
    for text in ("", "yes, reset", '{"reset": "yes"}', None, '{"reasons": "x"}'):
        assert auto_round.parse_verdict(text) is None, text
    # the reasons reach status.yaml, the gate record and the PR body: capped
    long = auto_round.parse_verdict(json.dumps({"reset": False, "reasons": "x " * 5000}))
    assert len(long["reasons"]) == auto_round.REASONS_CHARS and long["reasons"].endswith("…")


def test_the_run_is_named_from_the_runner_s_variables():
    assert auto_round.github_run({}) is None and auto_round.run_label({}) == "local"
    assert auto_round.github_run(RUN_ENV) == {
        "id": "777",
        "url": "https://github.com/owner/name/actions/runs/777",
        "attempt": "1",
    }
    assert auto_round.run_label(RUN_ENV) == "777"


def test_the_fixing_label_is_created_with_the_others(monkeypatch):
    assert c.FIXING_LABEL == "sdlc:fixing" and c.runner_labels() == [c.FIXING_LABEL]
    from pr import cli as pr_cli
    from pr import github

    assert pr_cli.label_color(c.FIXING_LABEL) != pr_cli.label_color(c.NEEDS_HUMAN_LABEL)
    seen = {}
    monkeypatch.setattr(
        github,
        "ensure_label",
        lambda repo, name, color, text, cwd=None: seen.update({name: color}) or {"ok": True},
    )
    run_phase.ensure_labels("owner/name", {"GITHUB_TOKEN": FAKE_TOKEN})
    assert seen[c.FIXING_LABEL] == run_phase.LABEL_COLOR_FIXING
    assert seen[c.NEEDS_HUMAN_LABEL] == run_phase.LABEL_COLOR_HUMAN


# --- 2. the runner's side: a full phase run with a red commands step ------------------------------
def red_commands_step(monkeypatch, record=None, calls=None):
    """Replace the runner's commands step with one that rewrites the record as the gate's
    ``run_deferred_commands`` does on a red target (the record, then status.yaml parked)."""
    record = record or red_record()

    def fake(plugin_dir, root, change_id, phase, config):
        change = c.find_change_dir(Path(root), change_id)
        write(change / "evidence" / f"gate-{phase}.json", json.dumps(record))
        st = status_mod.read_status(change)
        st.park(record["reason"], phase=phase)
        status_mod.write_status(change, st)
        if calls is not None:
            calls.append(phase)
        return {"ok": True, "output": {"ran": True, **record}}

    monkeypatch.setattr(run_phase, "run_gate_commands", fake)


def dispatch_recorder(monkeypatch, answer=None) -> list:
    sent: list = []

    def fake(repo, workflow, ref, change_id, head_ref):
        sent.append((repo, workflow, ref, change_id, head_ref))
        return dict(answer or {"ok": True, "status": 204, "reason": ""})

    monkeypatch.setattr(run_phase, "dispatch", fake)
    return sent


PAST = "2026-10-01T00:00:00Z"


def taken_round(change: Path, k: int, phase: str = "build", at: str = PAST) -> None:
    """``auto-round.json`` as a fix run that took automatic round ``k`` leaves it."""
    write(
        change / "evidence" / c.AUTO_ROUND_FILE,
        json.dumps({"round": k, "cap": 3, "phase": phase, "head": "abc", "at": at,
                    "status": "taken", "targets": [], "history": []}),
    )  # fmt: skip


def build_run(
    project, fake_claude, monkeypatch, iterations=0, extra_env=None, taken=None, **args_kw
):
    root, change = project
    if taken is not None:
        taken_round(change, taken)
    calls = pr_route(monkeypatch)
    # nothing leaves the machine: the labels the run would create are not created
    monkeypatch.setattr(run_phase, "ensure_labels", lambda repo, env: {"ensured": 0})
    set_state(change, "design", gate_phase="design", gate_result="passed")
    if iterations:
        st = status_mod.read_status(change)
        st.iterations = iterations
        status_mod.write_status(change, st)
    write(change / "evidence" / "gate-build.json", json.dumps({**GATE_FILE, "phase": "build"}))
    monkeypatch.setenv("FAKE_CLAUDE_RESULT", json.dumps(FAKE_RESULT))
    env = dict(os.environ, **KEY_ENV, GITHUB_TOKEN=FAKE_TOKEN, **(extra_env or {}))
    kw = {"root": str(root), "phase": "build", "dry_run": False, "claude": fake_cli(fake_claude)}
    kw.update(args_kw)
    return Args(**kw), env, calls


def gate_c(change: Path) -> dict:
    return json.loads((change / "evidence" / "gate-build.json").read_text(encoding="utf-8"))


def test_a_red_target_below_the_cap_dispatches_the_next_fix_round(
    project, fake_claude, monkeypatch, capsys
):
    root, change = project
    args, env, calls = build_run(project, fake_claude, monkeypatch, extra_env=RUN_ENV)
    red_commands_step(monkeypatch)
    sent = dispatch_recorder(monkeypatch)
    assert run_phase.run_phase(args, env) == run_phase.EXIT_OK
    out = json.loads(capsys.readouterr().out)
    assert out["auto_round"]["action"] == "round" and out["auto_round"]["round"] == 1
    assert out["auto_round"]["cap"] == 3 and out["dispatched"] is None  # no next phase
    assert out["auto_round"]["dispatched"]["ok"] is True
    # the round goes through the only start the workflow token's events allow
    assert sent == [("owner/name", "sdlc-fix.yml", "main", "0001", "sdlc/0001/build")]
    data = json.loads((change / "evidence" / c.AUTO_ROUND_FILE).read_text(encoding="utf-8"))
    assert data["round"] == 1 and data["cap"] == 3 and data["phase"] == "c"
    assert data["status"] == "dispatched" and data["after_reset"] is False
    assert data["head"] == git(root, "rev-parse", "HEAD").strip()
    assert data["run"]["url"] == "https://github.com/owner/name/actions/runs/777"
    assert data["targets"] == [
        {
            "target": "test",
            "command": "python -m pytest",
            "exit_code": 1,
            "timed_out": False,
            "timeout": None,
            "output_tail": "FAILED x",
        }
    ]
    assert data["at"]
    # the record keeps its failing check and its park (the check run stays red) and carries
    # the fixing label; status.yaml says a round runs, not that the owner is needed
    record = gate_c(change)
    assert record["result"] == "park" and record["label"] == c.FIXING_LABEL
    assert next(ch for ch in record["checks"] if ch["name"] == "commands")["ok"] is False
    st = status_mod.read_status(change)
    assert st.gate.result == "parked"
    assert st.parked_reason.startswith("automatic fix round 1 of 3 dispatched by the runner")
    # committed with the run record, the message says so, and the PR is refreshed
    commit = next(argv for name, argv in calls if argv and argv[0] == "commit-phase")
    message = commit[commit.index("--message") + 1]
    assert "automatic fix round 1 of 3 (decision 29)" in message
    assert any(argv and argv[0] == "upsert" for _name, argv in calls)
    # decision 29's third answer: the run record names this workflow run
    run_file = json.loads((change / "evidence" / "run-build.json").read_text(encoding="utf-8"))
    assert run_file["github_run"]["id"] == "777"


def test_no_dispatch_sends_nothing_says_what_it_would_send_and_parks(
    project, fake_claude, monkeypatch, capsys
):
    """Under --no-dispatch no round runs, so the change is not left saying one does."""
    root, change = project
    args, env, _calls = build_run(project, fake_claude, monkeypatch, no_dispatch=True)
    red_commands_step(monkeypatch)
    sent = dispatch_recorder(monkeypatch)
    assert run_phase.run_phase(args, env) == run_phase.EXIT_OK
    out = json.loads(capsys.readouterr().out)
    assert sent == []
    dispatched = out["auto_round"]["dispatched"]
    assert {k: dispatched[k] for k in ("would_dispatch", "ref", "change_id", "head_ref")} == {
        "would_dispatch": "sdlc-fix.yml",
        "ref": "main",
        "change_id": "0001",
        "head_ref": "sdlc/0001/build",
    }
    assert gate_c(change)["label"] == c.NEEDS_HUMAN_LABEL
    data = json.loads((change / "evidence" / c.AUTO_ROUND_FILE).read_text(encoding="utf-8"))
    assert data["status"] == "not-dispatched" and "--no-dispatch" in data["reason"]


def test_a_dry_run_dispatches_no_fix_round(monkeypatch):
    sent = dispatch_recorder(monkeypatch)
    args = Args(root=str(ROOT), dry_run=True, no_dispatch=False)
    got = run_phase.dispatch_fix_round(args, "0001", "sdlc/0001/build")
    assert got["would_dispatch"] == "sdlc-fix.yml" and sent == []
    args = Args(root=str(ROOT), dry_run=False, no_dispatch=False)
    assert (
        run_phase.dispatch_fix_round(args, "0001", "sdlc/0001/build")["workflow"] == "sdlc-fix.yml"
    )
    assert sent == [("owner/name", "sdlc-fix.yml", "main", "0001", "sdlc/0001/build")]


def test_a_red_target_with_another_failed_check_parks_as_before(
    project, fake_claude, monkeypatch, capsys
):
    root, change = project
    args, env, _calls = build_run(project, fake_claude, monkeypatch)
    plan = {"name": "plan_sync", "ok": False, "reason": "out of sync", "need": "", "details": {}}
    red_commands_step(monkeypatch, red_record(extra_checks=[plan]))
    sent = dispatch_recorder(monkeypatch)
    assert run_phase.run_phase(args, env) == run_phase.EXIT_OK
    out = json.loads(capsys.readouterr().out)
    assert out["auto_round"] is None and sent == []
    assert gate_c(change)["label"] == c.NEEDS_HUMAN_LABEL
    assert not (change / "evidence" / c.AUTO_ROUND_FILE).exists()


def test_a_missing_target_parks_at_once(project, fake_claude, monkeypatch, capsys):
    root, change = project
    args, env, _calls = build_run(project, fake_claude, monkeypatch)
    red_commands_step(monkeypatch, red_record(commands_details={"missing": ["lint"]}))
    sent = dispatch_recorder(monkeypatch)
    assert run_phase.run_phase(args, env) == run_phase.EXIT_OK
    assert json.loads(capsys.readouterr().out)["auto_round"] is None and sent == []
    assert gate_c(change)["label"] == c.NEEDS_HUMAN_LABEL


def test_a_round_that_could_not_be_dispatched_parks_for_the_owner(
    project, fake_claude, monkeypatch, capsys
):
    root, change = project
    args, env, _calls = build_run(project, fake_claude, monkeypatch)
    red_commands_step(monkeypatch)
    dispatch_recorder(monkeypatch, {"ok": False, "status": 403, "reason": "forbidden"})
    assert run_phase.run_phase(args, env) == run_phase.EXIT_OK
    out, err = capsys.readouterr()
    assert "could not be dispatched: forbidden" in err
    assert json.loads(out)["auto_round"]["parked"]["reason"].startswith(
        "the automatic fix round 1 could not be dispatched"
    )
    record = gate_c(change)
    assert record["label"] == c.NEEDS_HUMAN_LABEL and record["result"] == "park"
    rounds = next(ch for ch in record["checks"] if ch["name"] == "fix_rounds")
    assert "workflow_dispatch of sdlc-fix.yml" in rounds["need"]
    data = json.loads((change / "evidence" / c.AUTO_ROUND_FILE).read_text(encoding="utf-8"))
    assert data["status"] == "not-dispatched"
    assert "could not be dispatched" in status_mod.read_status(change).parked_reason


# --- 3. at the cap: the one judged reset ----------------------------------------------------------
def judge(monkeypatch, answer=None, calls=None):
    def fake(*args, **kwargs):
        if calls is not None:
            calls.append(args)
        if answer is None:
            raise AssertionError("the judge must not run")
        return dict(answer)

    monkeypatch.setattr(run_phase, "run_reset_judge", fake)


def test_at_the_cap_a_judged_reset_restarts_the_rounds_once(
    project, fake_claude, monkeypatch, tmp_path, capsys
):
    """The fix run that took round 3 (from a count of 2) is red again and its session did not
    bump: the runner counts the round, the automatic rounds reach the cap, the judge resets."""
    root, change, args, env, _seen = fix_run(project, fake_claude, monkeypatch, tmp_path, 2)
    st = status_mod.read_status(change)
    st.panel_calls = 2
    status_mod.write_status(change, st)
    red_commands_step(monkeypatch)
    sent = dispatch_recorder(monkeypatch)
    asked: list = []
    verdict = {"ok": True, "reset": True, "reasons": "fewer failures each round", "source": "j"}
    judge(monkeypatch, verdict, asked)
    assert run_phase.run_phase(args, env) == run_phase.EXIT_OK
    out = json.loads(capsys.readouterr().out)
    assert len(asked) == 1 and out["auto_round"]["action"] == "round"
    assert out["auto_round"]["count_enforced"] == {"from": 2, "to": 3}
    assert out["auto_round"]["reset"]["actor"] == "sdlc-runner:777"
    st = status_mod.read_status(change)
    assert st.iterations == 0 and st.panel_calls == 0  # as sdlc:reset-iterations does
    assert st.iterations_reset_by == "sdlc-runner:777" and st.iterations_reset_at
    reset = json.loads((change / "evidence" / c.AUTO_RESET_FILE).read_text(encoding="utf-8"))
    assert reset["reset"] is True and reset["reasons"] == "fewer failures each round"
    assert reset["actor"] == st.iterations_reset_by and reset["at"] == st.iterations_reset_at
    assert reset["iterations_before"] == 3 and reset["panel_calls_before"] == 2
    assert reset["run"]["id"] == "777" and reset["cap"] == 3
    data = json.loads((change / "evidence" / c.AUTO_ROUND_FILE).read_text(encoding="utf-8"))
    assert data["round"] == 1 and data["after_reset"] is True
    assert sent and sent[0][1] == "sdlc-fix.yml"
    assert gate_c(change)["label"] == c.FIXING_LABEL


@pytest.mark.parametrize(
    ("answer", "expected"),
    [
        ({"ok": True, "reset": False, "reasons": "the same failure three times"},
         "the judge declined a reset: the same failure three times"),
        ({"ok": False, "reason": "the judge did not finish (claude exited 1)"},
         "the judge could not decide on a reset: the judge did not finish"),
    ],
)  # fmt: skip
def test_at_the_cap_a_declined_or_failed_judge_parks_for_the_owner(
    project, fake_claude, monkeypatch, tmp_path, capsys, answer, expected
):
    root, change, args, env, _seen = fix_run(project, fake_claude, monkeypatch, tmp_path, 2)
    red_commands_step(monkeypatch)
    sent = dispatch_recorder(monkeypatch)
    judge(monkeypatch, answer)
    assert run_phase.run_phase(args, env) == run_phase.EXIT_OK
    out = json.loads(capsys.readouterr().out)
    assert out["auto_round"]["action"] == "park" and sent == []
    record = gate_c(change)
    assert record["label"] == c.NEEDS_HUMAN_LABEL and record["result"] == "park"
    rounds = next(ch for ch in record["checks"] if ch["name"] == "fix_rounds")
    assert rounds["reason"].startswith(
        "iteration cap reached after the automatic fix rounds: 3 of 3"
    )
    assert expected in rounds["reason"] and "sdlc:reset-iterations" in rounds["need"]
    assert "**fix_rounds**" in record["what_i_need"]
    st = status_mod.read_status(change)
    assert st.iterations == 3 and st.iterations_reset_by is None
    assert expected in st.parked_reason
    assert not (change / "evidence" / c.AUTO_RESET_FILE).exists()


def test_the_second_cap_parks_without_asking_the_judge(
    project, fake_claude, monkeypatch, tmp_path, capsys
):
    root, change = project
    write(
        change / "evidence" / c.AUTO_RESET_FILE,
        json.dumps({"reset": True, "actor": "sdlc-runner:1", "at": "2026-10-17T10:00:00Z"}),
    )
    root, change, args, env, _seen = fix_run(project, fake_claude, monkeypatch, tmp_path, 2)
    red_commands_step(monkeypatch)
    sent = dispatch_recorder(monkeypatch)
    judge(monkeypatch, None)  # raises if called
    assert run_phase.run_phase(args, env) == run_phase.EXIT_OK
    out = json.loads(capsys.readouterr().out)
    assert out["auto_round"]["action"] == "park" and sent == []
    assert "the one automatic reset of this change is spent" in out["auto_round"]["reason"]
    assert gate_c(change)["label"] == c.NEEDS_HUMAN_LABEL


@pytest.mark.parametrize("taken", [None, 2])
def test_a_cap_the_automatic_rounds_did_not_reach_parks_without_the_judge(
    project, fake_claude, monkeypatch, capsys, taken
):
    """Decision 29: the judge reads the automatic rounds when they reach the cap; a count the
    owner's rounds (or another phase's) used up parks as before."""
    root, change = project
    args, env, _calls = build_run(project, fake_claude, monkeypatch, 3, taken=taken)
    red_commands_step(monkeypatch)
    sent = dispatch_recorder(monkeypatch)
    judge(monkeypatch, None)  # raises if called
    assert run_phase.run_phase(args, env) == run_phase.EXIT_OK
    out = json.loads(capsys.readouterr().out)
    assert out["auto_round"]["action"] == "park" and sent == []
    assert "not reached by the runner's automatic rounds" in out["auto_round"]["reason"]
    assert gate_c(change)["label"] == c.NEEDS_HUMAN_LABEL


def test_the_runner_enforces_the_count_a_session_did_not_bump(project, monkeypatch):
    """A fix session that skipped bump-iteration does not get the same round number again:
    the round this run took counts one from the count it started from (raised, never
    lowered); at the cap reached that way the judge is asked."""
    root, change = project
    write(change / "evidence" / "gate-build.json", json.dumps(red_record("c")))
    set_state(change, "build", gate_phase="build", gate_result="parked", parked="red")
    args = Args(root=str(root), dry_run=False)
    took = {"round": 2, "iterations_at_take": 1}
    st = status_mod.read_status(change)
    st.iterations = 1
    status_mod.write_status(change, st)
    got = run_phase.auto_fix_round(args, ROOT, root, change, "0001", "c", {}, {}, took=took)
    assert got["count_enforced"] == {"from": 1, "to": 2} and got["round"] == 3
    assert status_mod.read_status(change).iterations == 2
    # a session that did bump is not counted twice
    got = run_phase.auto_fix_round(
        args, ROOT, root, change, "0001", "c", {}, {}, took={"round": 3, "iterations_at_take": 1}
    )
    assert "count_enforced" not in got and status_mod.read_status(change).iterations == 2
    # round 3 from a count of 2, not bumped: the automatic rounds reach the cap -> the judge
    judge_calls: list = []
    judge(monkeypatch, {"ok": True, "reset": False, "reasons": "no progress"}, judge_calls)
    got = run_phase.auto_fix_round(
        args, ROOT, root, change, "0001", "c", {}, {}, took={"round": 3, "iterations_at_take": 2}
    )
    assert got["action"] == "park" and len(judge_calls) == 1
    assert status_mod.read_status(change).iterations == 3


def test_an_owner_s_reset_by_hand_is_not_undone(project, monkeypatch):
    """The re-review of 443f818: three automatic rounds, a park at the cap, the owner's
    ``gate/cli.py set-iterations --count 0`` by hand (no label: no actor; R26 stamps the time),
    and a red target on the next run: the stale taken round 3 must not raise the count."""
    root, change = project
    set_state(change, "build", gate_phase="build", gate_result="parked", parked="red")
    auto_round.start_round(change, "build", 2, 3, auto_round.red_targets(red_record()), "abc", {})
    auto_round.set_round_status(change, auto_round.TAKEN, iterations_at_take=2)
    from gate import cli as gate_cli

    assert (
        gate_cli.main(["set-iterations", "--root", str(root), "--id", "0001", "--count", "0"]) == 0
    )
    write(change / "evidence" / "gate-build.json", json.dumps(red_record("c")))
    judge(monkeypatch, None)  # raises if called
    args = Args(root=str(root), dry_run=False)
    got = run_phase.auto_fix_round(args, ROOT, root, change, "0001", "c", {}, RUN_ENV)
    assert "count_enforced" not in got and got["action"] == "round" and got["round"] == 1
    assert status_mod.read_status(change).iterations == 0
    # the owner's round that took a pending round after the reset counts from 0
    got = run_phase.auto_fix_round(
        args, ROOT, root, change, "0001", "c", {}, RUN_ENV,
        took={"round": 1, "iterations_at_take": 0},
    )  # fmt: skip
    assert got["count_enforced"] == {"from": 0, "to": 1} and got["round"] == 2


def test_a_reset_deleted_from_the_branch_is_still_spent(project):
    """A session that deletes evidence/auto-reset.json does not earn a second reset: the
    branch's history still carries the file."""
    root, change = project
    st = status_mod.read_status(change)
    assert auto_round.reset_used(root, change, st) == ""
    write(change / "evidence" / c.AUTO_RESET_FILE, "{}")
    assert "records it" in auto_round.reset_used(root, change, st)
    git(root, "add", ".")
    git(root, "commit", "-q", "-m", "runner reset")
    (change / "evidence" / c.AUTO_RESET_FILE).unlink()
    git(root, "commit", "-q", "-am", "session deletes it")
    assert "history" in auto_round.reset_used(root, change, st)
    st.iterations_reset_by = "sdlc-runner:5"
    assert "status.yaml names it" in auto_round.reset_used(root, change, st)


def test_the_judge_is_read_only_on_the_advocate_s_model(project, monkeypatch):
    root, change = project
    seen = {}

    def fake_invoke(argv, cwd, env, timeout):
        seen.update(argv=argv, timeout=timeout, model=env.get("SDLC_MODEL"), env=env)
        return {"result": '{"reset": true, "reasons": "r"}', "total_cost_usd": 0.1}, "", "", 0

    monkeypatch.setattr(run_phase, "invoke", fake_invoke)
    targets = auto_round.red_targets(red_record())
    got = run_phase.run_reset_judge(
        Args(root=str(root)), ROOT, root, change, "0001", "c",
        {"panel_advocate_model": "opus"}, {**KEY_ENV, "GITHUB_TOKEN": FAKE_TOKEN,
        "GH_TOKEN": FAKE_TOKEN}, 3, 3, targets,
    )  # fmt: skip
    assert got["ok"] is True and got["reset"] is True and got["reasons"] == "r"
    assert not {"GITHUB_TOKEN", "GH_TOKEN"} & set(seen["env"])  # no GitHub token
    assert seen["timeout"] == 600  # within the job's budget
    argv = seen["argv"]
    assert argv[argv.index("--allowedTools") + 1] == "Read,Grep,Glob"
    denied = argv[argv.index("--disallowedTools") + 1].split(",")
    assert {"Edit", "Write", "Bash", "MultiEdit", "Agent", "Task", "Skill"} <= set(denied)
    assert {"SlashCommand", "TodoWrite"} <= set(denied)
    assert argv[argv.index("--model") + 1] == "opus" and seen["model"] == "opus"
    prompt = argv[argv.index("-p") + 1]
    assert "changes/0001-percent-helper/evidence/gate-build.json" in prompt
    assert "auto-round.json" in prompt and "fix-response.md" in prompt
    assert "Change nothing" in prompt and '"reset"' in prompt
    assert (change / "evidence" / "claude-judge.json").is_file()
    ledger = json.loads((change / "evidence" / "spend.json").read_text(encoding="utf-8"))
    assert [(e["run"], e["source"]) for e in ledger["entries"]] == [("judge", "claude-judge.json")]
    # a failed or unreadable judge never resets
    monkeypatch.setattr(run_phase, "invoke", lambda *a, **k: ({"result": "maybe"}, "", "", 0))
    assert (
        run_phase.run_reset_judge(
            Args(root=str(root)), ROOT, root, change, "0001", "c", {}, dict(KEY_ENV), 3, 3, targets
        )["ok"]
        is False
    )
    # R7: the judge runs on the adversarial reviewer's model when sdlc.yaml names one
    monkeypatch.setattr(run_phase, "invoke", fake_invoke)
    run_phase.run_reset_judge(
        Args(root=str(root)), ROOT, root, change, "0001", "c",
        {"adversarial_model": "claude-opus-5-5", "panel_advocate_model": "claude-fable-5-1"},
        dict(KEY_ENV), 3, 3, targets,
    )  # fmt: skip
    assert seen["model"] == "claude-opus-5-5"
    monkeypatch.setattr(run_phase, "invoke", lambda *a, **k: (None, "", "boom", 1))
    assert (
        "claude exited 1"
        in run_phase.run_reset_judge(
            Args(root=str(root)), ROOT, root, change, "0001", "c", {}, dict(KEY_ENV), 3, 3, targets
        )["reason"]
    )


# --- 4. the dispatched round takes its constraint once --------------------------------------------
def pending_round(root: Path, change: Path, iterations: int = 0) -> dict:
    git(root, "add", ".")
    git(root, "commit", "-q", "--allow-empty", "-m", "the tree the runner found red")
    head = git(root, "rev-parse", "HEAD").strip()
    targets = auto_round.red_targets(red_record())
    data = auto_round.start_round(change, "build", iterations, 3, targets, head, {})
    git(root, "add", ".")
    git(root, "commit", "-q", "-m", "run(c): spend recorded; automatic fix round 1 of 3")
    return data


def test_the_fix_round_turns_a_pending_auto_round_into_one_red_targets_request(project):
    root, change = project
    pending_round(root, change)
    write(
        change / "evidence" / "fix-requests.json",
        json.dumps({"schema_version": 1, "ok": True, "requests": [], "not_applied": []}),
    )
    got = run_phase.take_red_targets(root, change, RUN_ENV)
    assert got["red_targets"] is not None, got
    assert got["red_targets"]["kind"] == "red-targets" and got["red_targets"]["requests"] == 1
    data = json.loads((change / "evidence" / "fix-requests.json").read_text(encoding="utf-8"))
    (request,) = data["requests"]
    assert request["kind"] == "red-targets" and request["author"] == "sdlc-runner"
    assert request["round"] == 1 and request["cap"] == 3
    assert "fix the code, not the test; the test-file lock still applies" in request["body"]
    assert "`python -m pytest` exited 1" in request["body"] and "FAILED x" in request["body"]
    taken = json.loads((change / "evidence" / c.AUTO_ROUND_FILE).read_text(encoding="utf-8"))
    assert taken["status"] == "taken" and taken["taken_by"]["run"]["id"] == "777"
    # a later round (the owner's) does not apply it again
    again = run_phase.take_red_targets(root, change, {})
    assert again["red_targets"] is None and "is taken" in again["red_targets_note"]
    data = json.loads((change / "evidence" / "fix-requests.json").read_text(encoding="utf-8"))
    assert len(data["requests"]) == 1


def test_a_pending_round_whose_tree_moved_is_not_applied(project):
    root, change = project
    pending_round(root, change)
    # the owner's labels committed by the round touch the change folder only: still current
    write(change / "evidence" / "note.txt", "labels")
    git(root, "add", ".")
    git(root, "commit", "-q", "-m", "owner labels applied")
    assert auto_round.head_matches(root, change, auto_round.read_round(change)["head"])
    # code changed since the runner found the target red: the request is stale
    write(root / "sample_pkg" / "extra.py", "X = 1\n")
    git(root, "add", ".")
    git(root, "commit", "-q", "-m", "someone pushed code")
    got = run_phase.take_red_targets(root, change, {})
    assert (
        got["red_targets"] is None and "not what this round starts from" in got["red_targets_note"]
    )
    assert auto_round.read_round(change)["status"] == "dispatched"


# --- 5. the owner-field guards accept the marked reset and nothing else -----------------------
AT = "2026-10-17T10:00:00Z"


def fields(reset_by=None, reset_at=None) -> dict:
    return {
        "risk_accepted": [],
        "risk_accepted_by": [],
        "iterations_reset": (reset_by, reset_at),
        "tests_unlocked_by": None,
        "locked": False,
        "iterations": 0,
        "panel_calls": 0,
    }


def test_the_baseline_accepts_the_runner_s_reset_with_its_record_only(project, monkeypatch):
    root, change = project

    class NoGitHub:
        def label_actor(self, *a, **k):
            raise AssertionError("a runner reset has no label event to read")

    monkeypatch.setattr(run_phase, "_github", lambda: NoGitHub())
    ci_env = {"GITHUB_ACTIONS": "true"}
    before = fields("sdlc-runner:777", AT)
    # no record: a forgery, on a runner and by hand
    for env in (ci_env, {}):
        reasons = run_phase.baseline_mismatches(before, None, "o/r", 5, env, change_dir=change)
        assert len(reasons) == 1 and "records no such reset" in reasons[0]
    write(
        change / "evidence" / c.AUTO_RESET_FILE,
        json.dumps({"reset": True, "actor": "sdlc-runner:777", "at": AT}),
    )
    assert run_phase.baseline_mismatches(before, None, "o/r", 5, ci_env, change_dir=change) == []
    # the same actor at another stamp, or another runner actor, is not that reset
    for forged in (fields("sdlc-runner:777", "2026-10-18T00:00:00Z"), fields("sdlc-runner:8", AT)):
        assert run_phase.baseline_mismatches(forged, None, "o/r", 5, ci_env, change_dir=change)
    # a record that says the judge declined is no reset either
    write(
        change / "evidence" / c.AUTO_RESET_FILE,
        json.dumps({"reset": False, "actor": "sdlc-runner:777", "at": AT}),
    )
    assert run_phase.baseline_mismatches(before, None, "o/r", 5, ci_env, change_dir=change)


def test_a_session_still_cannot_write_a_runner_reset_itself():
    after = {**fields("sdlc-runner:777", AT)}
    reasons = run_phase.owner_field_mismatches(fields(), after, None)
    assert reasons and reasons[0].startswith("iterations_reset_by: the session recorded")


def test_a_runner_reset_is_never_a_label_actor():
    from state import unpark

    assert unpark.is_runner_reset("sdlc-runner:1") and not unpark.is_runner_reset("owner")
    # the label rule is unchanged: a person's login passes, a bot never does
    assert unpark.is_automation_actor("github-actions[bot]", []) is True
    assert unpark.is_automation_actor("luissiviero", []) is False


# --- 6. what the owner reads ----------------------------------------------------------------------
def fixing_change(project, label=c.FIXING_LABEL):
    root, change = project
    set_state(change, "build", gate_phase="build", gate_result="parked", parked="red")
    record = red_record()
    if label == c.FIXING_LABEL:
        record = {**record, "label": label, "auto_round": {"round": 2, "cap": 3}}
        auto_round.start_round(
            change, "build", 1, 3, auto_round.red_targets(red_record()), "abc", {}
        )
    write(change / "evidence" / "gate-build.json", json.dumps(record))
    return root, change


def test_the_pr_says_an_automatic_round_runs_and_asks_nothing(project):
    root, change = fixing_change(project)
    body = desc.build_description(root, "0001", "build")
    line = next(x for x in body.splitlines() if x.startswith("- **What needs you**"))
    assert "automatic fix round 2 of 3 is running (decision 29)" in line
    assert "test (exit 1)" in line and line.startswith("- **What needs you**: nothing")
    assert "## What I need from you" not in body


def test_a_park_still_shows_what_the_owner_must_do(project):
    root, change = fixing_change(project, label=c.NEEDS_HUMAN_LABEL)
    body = desc.build_description(root, "0001", "build")
    assert "## What I need from you" in body and "automatic fix round" not in body


def test_the_pr_summary_names_the_run_its_evidence_came_from(project):
    root, change = project
    set_state(change, "build", gate_phase="build", gate_result="passed")
    write(change / "evidence" / "gate-build.json", json.dumps({**GATE_FILE, "phase": "build"}))
    assert "Run:" not in desc.build_description(root, "0001", "build")  # by hand: no line
    assert run_phase.stamp_run_record(change, "c", RUN_ENV) is None  # no record to stamp
    assert not (change / "evidence" / "run-build.json").exists()
    write(change / "evidence" / "run-build.json", json.dumps({"phase": "build", "spend_usd": 1.0}))
    run_phase.stamp_run_record(change, "c", {})
    assert "Run:" not in desc.build_description(root, "0001", "build")
    assert run_phase.stamp_run_record(change, "c", RUN_ENV)["id"] == "777"
    run_file = json.loads((change / "evidence" / "run-build.json").read_text(encoding="utf-8"))
    assert run_file["spend_usd"] == 1.0  # the run record keeps what it carried
    body = desc.build_description(root, "0001", "build")
    assert (
        "Run: the evidence and the gate record of phase (c) come from "
        "[workflow run 777](https://github.com/owner/name/actions/runs/777)."
    ) in body


def test_the_digest_lists_a_fixing_pr_apart_from_the_owner_s_queue():
    prs = [
        {"number": 1, "title": "build(0001): x", "labels": [c.FIXING_LABEL], "body": "- a"},
        {"number": 2, "title": "build(0002): y", "labels": [c.NEEDS_HUMAN_LABEL], "body": "- b"},
    ]
    text = digest.render_digest(prs, "2026-10-17T00:00:00Z")
    assert "1 parked, 0 waiting at a gate, 1 in an automatic fix round" in text
    fixing = text.index("## Automatic fix round running")
    assert text.index("#1") > fixing and text.index("#2") < fixing
    assert "## Waiting at a human gate" not in text


def test_the_verifier_names_the_tree_it_read_and_what_it_did_not_exercise():
    body = " ".join((ROOT / "plugin" / "agents" / "verifier.md").read_text("utf-8").split())
    assert "**Say which tree you read** (decision 29)" in body
    assert "name the record you quoted by its phase and its commit" in body
    assert "the final tree's result is the runner's" in body and "check run `sdlc/d`" in body
    assert "**Not exercised**" in body
    assert "the paths, platforms and inputs this verdict says nothing about" in body


def test_the_fix_command_applies_a_red_targets_request():
    text = " ".join((ROOT / "plugin" / "commands" / "sdlc-fix.md").read_text("utf-8").split())
    assert "A request of kind `red-targets`" in text
    assert (
        "make the failing targets pass: fix the code, not the test; the test-file lock still "
        "applies"
    ) in text
    assert "the runner runs the targets again after this round" in text


@pytest.mark.parametrize("phase", ["intent", "design", "maintain"])
def test_a_red_target_at_a_gate_whose_round_cannot_change_the_code_parks(project, phase):
    """At (a), (b) and (f) the gate's design_scope check refuses a source file, so a fix round
    could not fix a red target there: the change parks for the owner as before."""
    root, change = project
    write(change / "evidence" / f"gate-{phase}.json", json.dumps(red_record(phase)))
    args = Args(root=str(root), dry_run=False)
    assert run_phase.auto_fix_round(args, ROOT, root, change, "0001", phase, {}, {}) is None
    assert not (change / "evidence" / c.AUTO_ROUND_FILE).exists()
    write(change / "evidence" / "gate-build.json", json.dumps(red_record("c")))
    set_state(change, "build", gate_phase="build", gate_result="parked", parked="red")
    got = run_phase.auto_fix_round(args, ROOT, root, change, "0001", "c", {}, {})
    assert got["action"] == "round" and got["round"] == 1


# --- 7. the review of 0ac8c9f: the fix round end to end, the runner's files, the re-run ----------
PLANT = """
import json, pathlib
path = pathlib.Path("changes/0001-percent-helper/evidence/auto-round.json")
path.write_text(json.dumps({"round": 1, "status": "dispatched", "head": "x"}), encoding="utf-8")
"""


def test_a_session_that_writes_the_runner_s_files_parks_and_they_are_put_back(
    project, fake_claude, tmp_path, monkeypatch, capsys
):
    root, change = project
    script = tmp_path / "plant.py"
    write(script, PLANT)
    monkeypatch.setenv("FAKE_CLAUDE_RUN", str(script))  # before the run's environment is built
    args, env, _calls = build_run(project, fake_claude, monkeypatch, extra_env=RUN_ENV)
    red_commands_step(monkeypatch)
    sent = dispatch_recorder(monkeypatch)
    assert run_phase.run_phase(args, env) == run_phase.EXIT_OK
    out = json.loads(capsys.readouterr().out)
    assert out["parked"].startswith(c.OWNER_FIELDS_PARK_PREFIX) and sent == []
    assert "evidence/auto-round.json: the session created it" in out["parked"]
    assert not (change / "evidence" / c.AUTO_ROUND_FILE).exists()
    # the park commits a run record that names the workflow run (stamped on every path)
    run_file = json.loads((change / "evidence" / "run-build.json").read_text(encoding="utf-8"))
    assert run_file["github_run"]["id"] == "777"


def fix_run(project, fake_claude, monkeypatch, tmp_path, iterations=0):
    """A dispatched fix round on the build branch: the gate record says sdlc:fixing and
    auto-round.json holds the pending round 1, as the runner left them."""
    root, change = project
    pr_route(monkeypatch)
    monkeypatch.setattr(run_phase, "ensure_labels", lambda repo, env: {"ensured": 0})
    monkeypatch.setattr(run_phase, "apply_owner_labels", lambda *a, **k: {"ok": True})

    def collect(root, change_dir, *a, **k):
        from ci import fix_requests

        fix_requests.write(change_dir, {"schema_version": 1, "ok": True, "requests": [],
                                        "not_applied": []})  # fmt: skip
        return {"ok": True, "requests": 0}

    monkeypatch.setattr(run_phase, "collect_fix_requests", collect)
    set_state(change, "build", gate_phase="build", gate_result="parked", parked="red")
    st = status_mod.read_status(change)
    st.iterations = iterations
    status_mod.write_status(change, st)
    git(root, "add", ".")  # the installation and the change, as merged on the default branch
    git(root, "commit", "-q", "-m", "sdlc-init and change 0001")
    git(root, "checkout", "-q", "-b", "sdlc/0001/build")
    data = pending_round(root, change, iterations)
    auto_round.mark_fixing(change, "build", data)
    git(root, "add", ".")
    git(root, "commit", "-q", "-m", "run(c): automatic fix round 1 of 3")
    seen = tmp_path / "seen-requests.json"
    monkeypatch.setenv(
        "FAKE_CLAUDE_WATCH", "changes/0001-percent-helper/evidence/fix-requests.json"
    )
    monkeypatch.setenv("FAKE_CLAUDE_RECORD", str(seen))
    session_gate(monkeypatch, "c")  # the round's own gate writes its record (gap 4)
    monkeypatch.setenv("FAKE_CLAUDE_RESULT", json.dumps(FAKE_RESULT))
    env = dict(os.environ, **KEY_ENV, GITHUB_TOKEN=FAKE_TOKEN, **RUN_ENV)
    args = Args(root=str(root), phase="fix", head_ref="sdlc/0001/build", dry_run=False,
                claude=fake_cli(fake_claude))  # fmt: skip
    return root, change, args, env, seen


def test_a_dispatched_fix_round_takes_its_request_and_the_runner_counts_the_round(
    project, fake_claude, monkeypatch, tmp_path, capsys
):
    """End to end on ``--phase fix``: the session reads the red-targets request, does not run
    bump-iteration, the targets are red again, and the runner counts round 1 itself, so the
    next round is round 2 (the review of 0ac8c9f: "round 1" again forever)."""
    root, change, args, env, seen = fix_run(project, fake_claude, monkeypatch, tmp_path)
    red_commands_step(monkeypatch)
    sent = dispatch_recorder(monkeypatch)
    assert run_phase.run_phase(args, env) == run_phase.EXIT_OK
    out = json.loads(capsys.readouterr().out)
    requests = json.loads(seen.read_text(encoding="utf-8"))["requests"]
    assert [r["kind"] for r in requests] == ["red-targets"] and requests[0]["round"] == 1
    assert out["fix_requests"]["red_targets"]["kind"] == "red-targets"
    assert out["auto_round"]["count_enforced"] == {"from": 0, "to": 1}
    assert out["auto_round"]["round"] == 2
    assert status_mod.read_status(change).iterations == 1
    assert sent == [("owner/name", "sdlc-fix.yml", "main", "0001", "sdlc/0001/build")]
    assert gate_c(change)["label"] == c.FIXING_LABEL


@pytest.mark.parametrize("how", ["exit", "timeout"])
def test_a_fix_round_that_does_not_finish_parks_for_the_owner(
    project, fake_claude, monkeypatch, tmp_path, capsys, how
):
    root, change, args, env, _seen = fix_run(project, fake_claude, monkeypatch, tmp_path)
    if how == "exit":
        script = tmp_path / "die.py"
        write(script, "import sys\nsys.exit(1)\n")
        env["FAKE_CLAUDE_RUN"] = str(script)  # the session's own environment
        expected, code = "claude exited 1", run_phase.EXIT_FAILED
    else:
        monkeypatch.setattr(
            run_phase, "invoke", lambda *a, **k: (None, "", "claude did not finish", 124)
        )
        # R25 part 1 (1.0.26): the runner's timeout is an outer bound; decision 29's park
        # names it, and the run is green (before: "claude exited 124", a red run)
        expected, code = "stopped by the runner's timeout", run_phase.EXIT_OK
    sent = dispatch_recorder(monkeypatch)
    assert run_phase.run_phase(args, env) == code
    err = capsys.readouterr().err
    assert "the automatic fix round 1 did not finish" in err and sent == []
    record = gate_c(change)
    assert record["label"] == c.NEEDS_HUMAN_LABEL and record["result"] == "park"
    rounds = next(ch for ch in record["checks"] if ch["name"] == "fix_rounds")
    assert expected in rounds["reason"] and "workflow_dispatch of sdlc-fix.yml" in rounds["need"]
    data = json.loads((change / "evidence" / c.AUTO_ROUND_FILE).read_text(encoding="utf-8"))
    assert data["status"] == "unfinished"
    assert "did not finish" in status_mod.read_status(change).parked_reason


def test_a_fix_round_that_is_skipped_parks_for_the_owner(
    project, fake_claude, monkeypatch, tmp_path, capsys
):
    root, change, args, env, _seen = fix_run(project, fake_claude, monkeypatch, tmp_path)
    skip = "status.yaml is unreadable: bad"
    monkeypatch.setattr(run_phase, "guard", lambda *a, **k: (None, None, {}, skip))
    assert run_phase.run_phase(args, env) == run_phase.EXIT_OK
    assert "the fix run was skipped: status.yaml is unreadable" in capsys.readouterr().err
    assert gate_c(change)["label"] == c.NEEDS_HUMAN_LABEL


def test_a_paused_repository_writes_nothing_when_a_round_is_skipped(
    project, fake_claude, monkeypatch, tmp_path, capsys
):
    """A paused repository runs and writes nothing: the skipped round leaves the record as
    it was (the re-review of 443f818)."""
    root, change, args, env, _seen = fix_run(project, fake_claude, monkeypatch, tmp_path)
    head = git(root, "rev-parse", "HEAD").strip()
    monkeypatch.setattr(run_phase, "guard", lambda *a, **k: (None, None, {}, run_phase.PAUSED_SKIP))
    calls = pr_route(monkeypatch)
    assert run_phase.run_phase(args, env) == run_phase.EXIT_OK
    assert "did not finish" not in capsys.readouterr().err
    assert gate_c(change)["label"] == c.FIXING_LABEL
    assert git(root, "rev-parse", "HEAD").strip() == head and calls == []


def test_the_runner_re_runs_a_commands_step_that_failed_once(
    project, fake_claude, monkeypatch, capsys
):
    root, change = project
    args, env, _calls = build_run(project, fake_claude, monkeypatch)
    write(change / "evidence" / "gate-build.json", json.dumps(DEFERRED_GATE_FILE))
    calls: list = []
    timeouts: list = []
    answers = [{"ok": False, "reason": "gate: boom"}]

    def step(plugin_dir, root, change_id, phase, config, timeout=None):
        calls.append(phase)
        timeouts.append(timeout)
        if answers:
            return answers.pop(0)
        return {"ok": True, "output": {"ran": False}}

    monkeypatch.setattr(run_phase, "run_gate_commands", step)
    assert run_phase.run_phase(args, env) == run_phase.EXIT_OK
    capsys.readouterr()
    assert calls == ["build", "build"]
    # the re-run gets what is left of the step's budget, so both fit in the job
    budget = run_phase.commands_timeout_seconds({})
    assert timeouts[0] is None and 0 < timeouts[1] <= budget
    # failed twice: parked, the reason says it was re-run
    calls.clear()
    answers[:] = [{"ok": False, "reason": "gate: boom"}, {"ok": False, "reason": "gate: bang"}]
    write(change / "evidence" / "gate-build.json", json.dumps(DEFERRED_GATE_FILE))
    set_state(change, "design", gate_phase="design", gate_result="passed")
    assert run_phase.run_phase(args, env) == run_phase.EXIT_FAILED
    err = capsys.readouterr().err
    assert calls == ["build", "build"] and "after one automatic re-run of the step" in err
    # a step that timed out is not re-run: a second one would outlast the job
    calls.clear()
    answers[:] = [{"ok": False, "reason": "Command '...' timed out after 3000 seconds"}]
    write(change / "evidence" / "gate-build.json", json.dumps(DEFERRED_GATE_FILE))
    set_state(change, "design", gate_phase="design", gate_result="passed")
    assert run_phase.run_phase(args, env) == run_phase.EXIT_FAILED
    capsys.readouterr()
    assert calls == ["c"]


def test_a_re_run_of_the_commands_step_needs_half_its_budget_left(project):
    """The re-review of 443f818: a first attempt that used more than half of the step's
    budget is not re-run (125 + 50 + 50 + 10 would outlast the job's 200 minutes)."""
    root, change = project
    write(change / "evidence" / "gate-build.json", json.dumps(DEFERRED_GATE_FILE))
    failed = {"ok": False, "reason": "gate: boom"}
    assert run_phase.commands_retryable(failed, change, "c", 2000, 3000) is True
    assert run_phase.commands_retryable(failed, change, "c", 1400, 3000) is False
    assert run_phase.commands_retryable({"ok": False, "reason": "timed out"}, change, "c") is False
    write(change / "evidence" / "gate-build.json", json.dumps({**GATE_FILE, "phase": "build"}))
    assert run_phase.commands_retryable(failed, change, "c", 2000, 3000) is False  # rewritten
