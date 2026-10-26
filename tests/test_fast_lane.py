"""Decision 30 (ROADMAP R46), the fast lane: the owner's own intent PR starts the design at once,
cut from the PR's head (``fast_lane.a``); a design whose plan the adversarial reviewer classes
``routine`` passes gate (design) without a merge and the build is cut from it (``fast_lane.b``);
each recorded commit is the approved copy of the phases after it (``gate/diff.py
approved_base``), and every change off the fast lane reads the merge base as before; the
earlier PR is closed as ``sdlc:superseded``, which the abandon rule skips.

Real git repositories with a bare ``origin``; every GitHub call is a fake, as in
``tests/test_ci.py``: no network, no token.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path

import pytest
from ci import run_phase
from pr import description as desc
from pr import github

from gate import checks, gate
from gate import diff as diffmod
from state import cli as state_cli
from state import conventions as c
from state import status as status_mod
from tests import fixture_repos
from tests import test_ci as ci_tests
from tests.model_records import write_reviewer_record
from tests.test_ci import (
    FAKE_RESULT,
    FAKE_TOKEN,
    KEY_ENV,
    Args,
    fake_cli,
    pr_route,
    session_gate,
)
from tests.test_gate import (
    INTENT,
    PLAN,
    SPEC,
    _initialised_fixture,
    git,
    start_run,
    write,
)

# the fixtures of tests/test_ci.py, used here by name
fake_claude = ci_tests.fake_claude
project = ci_tests.project

OWNER_ENV = {"GITHUB_REPOSITORY_OWNER": "owner", "GITHUB_REPOSITORY": "owner/name"}
REPO = "owner/name"
CHANGE_REL = "changes/0001-percent-helper"
WORKFLOWS = Path(__file__).resolve().parents[1] / "template" / ".github" / "workflows"


# --- the repository: main without the change, an intent PR head carrying it -------------------
@pytest.fixture
def lane(tmp_path):
    """Main initialised and pushed to a bare origin without change 0001; the owner's intent
    PR head ``claude/intent`` carries the change folder at phase (a) with its intent, pushed
    too. Returns (root, change folder, the intent PR's head sha)."""
    root = tmp_path / "proj"
    head = fixture_repos.copy(
        "fast-lane",
        tmp_path,
        _build_lane,
        relocate=lambda dest: git(
            dest / "proj", "remote", "set-url", "origin", str(dest / "remote.git")
        ),
    )
    return root, root / "changes" / "0001-percent-helper", head


def _build_lane(base: Path) -> str:
    root, _change = _initialised_fixture(base)
    bare = base / "remote.git"
    git(base, "init", "-q", "--bare", "-b", "main", str(bare))
    git(root, "remote", "add", "origin", str(bare))
    git(root, "stash", "-q", "-u")  # the change folder is the intent PR's, not main's
    git(root, "push", "-q", "-u", "origin", "main")
    git(root, "checkout", "-q", "-b", "claude/intent")
    git(root, "stash", "pop", "-q")
    git(root, "add", ".")
    git(root, "commit", "-q", "-m", "intent(0001): percent helper")
    git(root, "push", "-q", "-u", "origin", "claude/intent")
    git(root, "fetch", "-q", "origin")
    return git(root, "rev-parse", "HEAD").strip()


def _status(change: Path, **fields) -> None:
    st = status_mod.read_status(change)
    for name, value in fields.items():
        setattr(st, name, value)
    status_mod.write_status(change, st)


def _design_on_the_lane(root: Path, change: Path, intent_sha: str, record: bool = True) -> str:
    """``sdlc/0001/design`` cut from the intent PR's head, ``fast_lane.a`` recorded (or not), the
    spec and plan committed at phase (b); the design head's sha."""
    git(root, "checkout", "-q", "-b", "sdlc/0001/design", intent_sha)
    if record:
        _status(change, fast_lane={"intent": {"sha": intent_sha, "pr": 12}})
    write(change / "spec.md", SPEC)
    write(change / "plan.md", PLAN + "- ratchet: tests may fall, because the flag test retires\n")
    _status(change, phase="design")
    git(root, "add", ".")
    git(root, "commit", "-q", "-m", "design(0001): spec and plan")
    return git(root, "rev-parse", "HEAD").strip()


def _build_on_the_lane(
    root: Path, change: Path, design_sha: str, record: bool = True, design_pr: int | None = 13
) -> None:
    """The design head records ``fast_lane.b`` (with the design PR's number, unless
    ``design_pr`` is None) and is pushed; ``sdlc/0001/build`` is cut from it."""
    st = status_mod.read_status(change)
    if record:
        lane_record = dict(st.fast_lane or {})
        lane_record["design"] = {"sha": design_sha, "classification": "routine"}
        if design_pr is not None:
            lane_record["design"]["pr"] = design_pr
        _status(change, fast_lane=lane_record, gate=status_mod.Gate("design", "passed"))
    git(root, "commit", "-q", "-am", "run(design): gate (design) passed on the fast lane")
    git(root, "push", "-q", "-u", "origin", "sdlc/0001/design")
    git(root, "checkout", "-q", "-b", "sdlc/0001/build")
    _status(change, phase="build")
    git(root, "commit", "-q", "-am", "build(0001): start")


# --- 1. the approved base ---------------------------------------------------------------------
def test_the_recorded_commit_is_the_approved_base_while_it_stands(lane):
    root, change, intent_sha = lane
    _design_on_the_lane(root, change, intent_sha)
    merge_base = git(root, "merge-base", "origin/main", "HEAD").strip()
    assert merge_base != intent_sha
    lane_record = status_mod.read_status(change).fast_lane
    assert diffmod.fast_lane_sha(root, lane_record, "design") == intent_sha
    assert diffmod.approved_base(root, lane_record, "design", merge_base) == intent_sha
    # entry ``a`` is (b)'s only: (c) to (e) read entry ``b``, (a) and (f) the merge base
    for phase in ("intent", "build", "test", "deploy", "maintain"):
        assert diffmod.fast_lane_sha(root, lane_record, phase) is None, phase
    # no record (a change that never took the fast lane): the merge base, as before
    assert diffmod.approved_base(root, None, "design", merge_base) == merge_base
    assert diffmod.approved_base(root, lane_record, "design", None) is None  # no base: nothing
    # a sha the branch was not cut from (not an ancestor of HEAD) is not used
    stray = {"intent": {"sha": "0" * 40, "pr": 12}}
    assert diffmod.fast_lane_sha(root, stray, "design") is None


def test_a_merged_intent_pr_falls_back_to_the_merge_base(lane):
    root, change, intent_sha = lane
    _design_on_the_lane(root, change, intent_sha)
    # the owner merges the intent PR after all: its head is on the default branch now
    git(root, "push", "-q", "origin", f"{intent_sha}:refs/heads/main")
    git(root, "fetch", "-q", "origin")
    assert diffmod.fast_lane_sha(root, status_mod.read_status(change).fast_lane, "design") is None
    merge_base = git(root, "merge-base", "origin/main", "HEAD").strip()
    lane_record = status_mod.read_status(change).fast_lane
    assert diffmod.approved_base(root, lane_record, "design", merge_base) == merge_base


def test_a_build_cut_from_the_default_branch_after_a_squash_merge_reads_the_merge_base(lane):
    """A squash merge of the design PR puts its record on the default branch, but the build
    branch cut from there does not contain the recorded commit: the merge base, as before."""
    root, change, intent_sha = lane
    design = _design_on_the_lane(root, change, intent_sha)
    _status(change, fast_lane={"design": {"sha": design, "classification": "routine"}})
    git(root, "commit", "-q", "-am", "run(design): fast lane")
    snapshot = {p: p.read_bytes() for p in change.rglob("*") if p.is_file()}
    git(root, "checkout", "-q", "main")
    for path, data in snapshot.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    git(root, "add", ".")
    git(root, "commit", "-q", "-m", "design (squashed)")
    git(root, "push", "-q", "origin", "main")
    git(root, "checkout", "-q", "-b", "sdlc/0001/build")
    _status(change, phase="build")
    assert diffmod.fast_lane_sha(root, status_mod.read_status(change).fast_lane, "build") is None
    merge_base = git(root, "merge-base", "origin/main", "HEAD").strip()
    lane_record = status_mod.read_status(change).fast_lane
    assert diffmod.approved_base(root, lane_record, "build", merge_base) == merge_base


def test_a_design_branch_cut_from_the_unmerged_intent_does_not_trip_the_intent_rule(lane):
    root, change, intent_sha = lane
    _design_on_the_lane(root, change, intent_sha)
    start_run(root, "design")
    ctx = gate.build_context(root, "0001", "design")
    assert ctx.approved_base() == intent_sha
    assert ctx.approved_artifact("intent.md") == INTENT
    assert checks.check_guardrails(ctx).ok is True
    # the same branch with no record: intent.md is new on it, as an edit after gate (intent)
    _status(change, fast_lane=None)
    git(root, "commit", "-q", "-am", "the record dropped")
    ctx = gate.build_context(root, "0001", "design")
    result = checks.check_guardrails(ctx)
    assert (
        result.ok is False
        and "intent.md changed on this branch after gate (intent)" in result.reason
    )
    assert ctx.approved_artifact("intent.md") is None  # new on the branch: nobody approved it


def test_an_intent_edit_after_the_recorded_head_still_trips_the_rule(lane):
    root, change, intent_sha = lane
    _design_on_the_lane(root, change, intent_sha)
    write(change / "intent.md", INTENT + "\nOne more requirement the session invented.\n")
    git(root, "commit", "-q", "-am", "design: tweak the intent")
    ctx = gate.build_context(root, "0001", "design")
    result = checks.check_guardrails(ctx)
    assert result.ok is False and "after gate (intent)" in result.reason


def test_a_build_stacked_on_the_design_reads_the_approved_plan_for_ratchets(lane):
    root, change, intent_sha = lane
    design = _design_on_the_lane(root, change, intent_sha)
    _build_on_the_lane(root, change, design)
    git(root, "rm", "-q", "tests/test_flag.py")
    git(root, "commit", "-q", "-m", "build: retire the flag test")
    ctx = gate.build_context(root, "0001", "build")
    assert ctx.approved_base() == design
    assert "ratchet: tests may fall" in (ctx.approved_artifact("plan.md") or "")
    declared = checks.check_ratchets(ctx)
    assert declared.ok is True and declared.details["hits"] == {}
    # without the record the plan is new on the branch: no approved plan, the drop is a hit
    lane_record = dict(status_mod.read_status(change).fast_lane or {})
    lane_record.pop("design")
    _status(change, fast_lane=lane_record)
    git(root, "commit", "-q", "-am", "the record dropped")
    ctx = gate.build_context(root, "0001", "build")
    assert ctx.approved_artifact("plan.md") is None
    result = checks.check_ratchets(ctx)
    # decision 35: the undeclared drop is a hit the banner shows, never a park
    assert result.ok is True and "tests/test_flag.py" in result.reason
    assert result.details["hits"] == {"ratchet: tests": ["tests/test_flag.py"]}


def test_the_plan_s_growth_on_the_fast_lane_reads_the_design_commit(lane):
    """R26 (choice 257's port): on the fast lane the plan approved at gate (design) is the one at
    the recorded design commit, as for the ratchets; without the record there is no
    approved copy, and no growth is recorded rather than a false one."""
    root, change, intent_sha = lane
    design = _design_on_the_lane(root, change, intent_sha)
    _build_on_the_lane(root, change, design)
    plan = (change / "plan.md").read_text(encoding="utf-8")
    write(
        change / "plan.md",
        plan.replace("\n## Order of work", "- `src/new_one.py` — new\n\n## Order of work", 1),
    )
    git(root, "commit", "-q", "-am", "build: the plan gains a file")
    ctx = gate.build_context(root, "0001", "build")
    assert checks.check_plan_sync(ctx).details["plan_growth"] == {
        "added": ["src/new_one.py"],
        "removed": [],
    }
    lane_record = dict(status_mod.read_status(change).fast_lane or {})
    lane_record.pop("design")
    _status(change, fast_lane=lane_record)
    git(root, "commit", "-q", "-am", "the record dropped")
    ctx = gate.build_context(root, "0001", "build")
    assert "plan_growth" not in checks.check_plan_sync(ctx).details


def test_the_runner_reads_the_framework_change_exemption_at_the_recorded_commit(lane):
    root, change, intent_sha = lane
    git(root, "checkout", "-q", "claude/intent")
    write(
        change / "intent.md",
        INTENT.replace("\n## Problem", "\nFramework change: yes\n\n## Problem"),
    )
    git(root, "commit", "-q", "-am", "intent: a framework change")
    git(root, "push", "-q", "origin", "claude/intent")
    intent_sha = git(root, "rev-parse", "HEAD").strip()
    _design_on_the_lane(root, change, intent_sha)
    write(root / "CLAUDE.md", (root / "CLAUDE.md").read_text(encoding="utf-8") + "\n- a rule\n")
    git(root, "commit", "-q", "-am", "the owner's guardrail edit")
    config = run_phase._config(root)
    assert run_phase.guardrail_changes(root, change, config, "design") == []
    # read at the merge base (no fast lane), the intent does not exist there: refused
    assert run_phase.guardrail_changes(root, change, config) == ["CLAUDE.md"]


# --- 2. the intent PR starts the design (find-change) --------------------------------------------
def _event(tmp_path: Path, sha: str, **pull) -> Path:
    data = {
        "number": 12,
        "draft": False,
        "merged": False,
        "user": {"login": "owner"},
        "head": {"sha": sha, "ref": "claude/intent", "repo": {"full_name": REPO}},
    }
    action = pull.pop("action", "opened")
    sender = pull.pop("sender", "owner")
    data.update(pull)
    path = tmp_path / "event.json"
    payload = {"action": action, "pull_request": data, "sender": {"login": sender}}
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def _files(monkeypatch, files: list[str], open_prs: dict | None = None) -> None:
    """The intent PR's files, and the open pull requests by head (none by default)."""
    monkeypatch.setattr(
        github, "pr_files", lambda repo, number, cwd=None: {"ok": True, "files": files}
    )
    monkeypatch.setattr(
        github,
        "find_open_pr",
        lambda repo, head, cwd=None: {"ok": True, "number": (open_prs or {}).get(head)},
    )


def _find(root: Path, tmp_path: Path, event: Path, capsys) -> tuple[list[str], str]:
    output = tmp_path / "github-output"
    output.write_text("", encoding="utf-8")
    env = {
        **OWNER_ENV,
        "GITHUB_EVENT_NAME": "pull_request",
        "GITHUB_EVENT_PATH": str(event),
        "GITHUB_OUTPUT": str(output),
    }
    args = Args(root=str(root), phase="design", id=None, head_ref="claude/intent", pr_number="12")
    capsys.readouterr()
    assert run_phase.print_found_change(args, env) == run_phase.EXIT_OK  # a skip is green
    return capsys.readouterr().out.splitlines(), output.read_text(encoding="utf-8")


INTENT_FILES = [f"{CHANGE_REL}/intent.md", f"{CHANGE_REL}/status.yaml"]


def test_the_owner_s_opened_intent_pr_starts_the_design_from_its_head(
    lane, tmp_path, monkeypatch, capsys
):
    root, _change, intent_sha = lane
    _files(monkeypatch, INTENT_FILES)
    git(root, "checkout", "-q", "main")
    for action in ("opened", "reopened"):
        printed, output = _find(root, tmp_path, _event(tmp_path, intent_sha, action=action), capsys)
        assert printed == [
            "change_id=0001",
            "reason=",
            f"start_point={intent_sha}",
            "intent_pr=12",
        ], action
        assert output == f"change_id=0001\nstart_point={intent_sha}\nintent_pr=12\n"


@pytest.mark.parametrize(
    ("case", "expected"),
    [
        ("collaborator", "is by colleague, not the owner's account"),
        ("bot", "not the owner's account"),
        ("fork", "a fork's intent never starts a design"),
        ("draft", "is a draft"),
        ("no_folder", "touches 0 change folders: the fast lane starts one intent PR"),
        ("two_folders", "touches 2 change folders: the fast lane starts one intent PR"),
        ("not_phase_a", "is at phase design at the head of #12, not intent"),
        ("design_pr_open", "pull request #13 carries sdlc/0001/design"),
        ("synchronize", "without a merge starts no design"),
        # decision 30 review, B1: a reopen is the sender's act
        ("reopened_by_collaborator", "was reopened by colleague, not the owner's account"),
        ("opened_by_bot", "was opened by sdlc-app[bot], not the owner's account"),
        # decision 30 review, N1: the intent PR carries the intent alone
        ("outside_file", "changes 1 file(s) outside changes/0001-percent-helper/"),
        # second review, R2: a superseded intent PR reopened, or a change past its design
        ("superseded_label", "reopening it starts no second design"),
        (
            "design_done",
            "records gate (design) on the fast lane: the design of change 0001 is done",
        ),
        ("build_exists", "sdlc/0001/build exists: change 0001 is past its design"),
    ],
)
def test_an_intent_pr_that_is_not_the_owner_s_own_at_phase_a_keeps_gate_a(
    lane, tmp_path, monkeypatch, capsys, case, expected
):
    root, change, intent_sha = lane
    files = INTENT_FILES
    open_prs: dict = {}
    pull: dict = {}
    if case == "collaborator":
        pull["user"] = {"login": "colleague"}
    elif case == "bot":
        pull["user"] = {"login": "dependabot[bot]"}
    elif case == "fork":
        pull["head"] = {"sha": intent_sha, "repo": {"full_name": "someone/name"}}
    elif case == "draft":
        pull["draft"] = True
    elif case == "no_folder":
        files = ["README.md"]
    elif case == "two_folders":
        files = [*INTENT_FILES, "changes/0002-other/intent.md"]
    elif case == "not_phase_a":
        _status(change, phase="design")
        git(root, "commit", "-q", "-am", "a design already")
        intent_sha = git(root, "rev-parse", "HEAD").strip()
    elif case == "design_pr_open":
        git(root, "push", "-q", "origin", "HEAD:refs/heads/sdlc/0001/design")
        open_prs = {"sdlc/0001/design": 13}
    elif case == "synchronize":
        pull["action"] = "synchronize"
    elif case == "reopened_by_collaborator":
        pull.update(action="reopened", sender="colleague")
    elif case == "opened_by_bot":
        pull["sender"] = "sdlc-app[bot]"
    elif case == "outside_file":
        files = [*INTENT_FILES, "src/app.py"]
    elif case == "superseded_label":
        pull.update(action="reopened", labels=[{"name": c.SUPERSEDED_LABEL}])
    elif case in ("design_done", "build_exists"):
        design = _design_on_the_lane(root, change, intent_sha)
        if case == "design_done":
            lane_record = dict(status_mod.read_status(change).fast_lane or {})
            lane_record["design"] = {"sha": design, "classification": "routine"}
            _status(change, fast_lane=lane_record)
            git(root, "commit", "-q", "-am", "run(design): fast lane")
            git(root, "push", "-q", "origin", "sdlc/0001/design")
        else:
            git(root, "push", "-q", "origin", "HEAD:refs/heads/sdlc/0001/build")
        git(root, "checkout", "-q", "claude/intent")
    _files(monkeypatch, files, open_prs)
    git(root, "fetch", "-q", "origin")
    printed, output = _find(root, tmp_path, _event(tmp_path, intent_sha, **pull), capsys)
    assert printed[0] == "change_id=" and output == "change_id=\n", case
    assert expected in printed[1], printed[1]
    assert not any(line.startswith("start_point=") for line in printed)


def test_a_pushed_design_branch_without_a_pull_request_may_start_again(
    lane, tmp_path, monkeypatch, capsys
):
    """Decision 30 review, S5: a design branch an earlier attempt pushed but never opened a
    pull request for does not block the fast lane (the guard's ``rerun_reason`` decides)."""
    root, _change, intent_sha = lane
    git(root, "push", "-q", "origin", "HEAD:refs/heads/sdlc/0001/design")
    _files(monkeypatch, INTENT_FILES)
    printed, output = _find(root, tmp_path, _event(tmp_path, intent_sha), capsys)
    assert output == f"change_id=0001\nstart_point={intent_sha}\nintent_pr=12\n", printed


def test_an_unreadable_payload_refuses_the_design_event(lane, tmp_path, capsys):
    root, _change, _sha = lane
    printed, output = _find(root, tmp_path, tmp_path / "missing.json", capsys)
    assert output == "change_id=\n" and "payload could not be read" in printed[1]


def test_the_merged_path_is_unchanged_and_skips_a_design_already_on_the_fast_lane(
    lane, tmp_path, monkeypatch, capsys
):
    root, change, intent_sha = lane
    _files(monkeypatch, INTENT_FILES)
    merged = _event(tmp_path, intent_sha, action="closed", merged=True)
    printed, output = _find(root, tmp_path, merged, capsys)
    assert printed == ["change_id=0001", "reason="] and output == "change_id=0001\n"
    # the design already started from the open intent PR and its PR is open: the merge
    # starts no second one
    _design_on_the_lane(root, change, intent_sha)
    git(root, "push", "-q", "origin", "sdlc/0001/design")
    _files(monkeypatch, INTENT_FILES, {"sdlc/0001/design": 13})
    printed, output = _find(root, tmp_path, merged, capsys)
    assert output == "change_id=\n"
    assert "already started on the fast lane from intent PR #12" in printed[1]
    # the branch pushed with no pull request (an attempt that never reached the queue): the
    # merge may run the design again (S5)
    _files(monkeypatch, INTENT_FILES)
    printed, output = _find(root, tmp_path, merged, capsys)
    assert output == "change_id=0001\n", printed
    # second review, R2: a build branch on origin means the change is past its design
    git(root, "push", "-q", "origin", "sdlc/0001/design:refs/heads/sdlc/0001/build")
    printed, output = _find(root, tmp_path, merged, capsys)
    assert output == "change_id=\n" and "sdlc/0001/build exists" in printed[1]


# --- 3. the design run cuts its branch from the intent PR and records it --------------------------
def test_prepare_branch_cuts_the_design_from_the_intent_head_and_records_it(lane):
    root, change, intent_sha = lane
    git(root, "checkout", "-q", "--detach", "main")  # the runner's checkout of the event
    branch = run_phase.prepare_branch(root, "0001", "design", start_point=intent_sha, intent_pr=12)
    assert branch["switched"] is True and "pushed" not in branch
    assert git(root, "rev-parse", "HEAD~1").strip() == intent_sha
    st = status_mod.read_status(change)
    assert st.fast_lane == {"intent": {"sha": intent_sha, "pr": 12}} and st.phase == "intent"
    # decision 30 review, S5: nothing reaches origin before the setup and the guard
    assert git(root, "ls-remote", "--heads", "origin", "sdlc/0001/design").strip() == ""
    remote = git(root, "rev-parse", "HEAD").strip()
    # the guard of (b) reads the new branch's tree as before
    assert ci_tests.skip_reason(root, "design") is None
    # a re-run finds the branch and switches to it; nothing is recorded twice
    git(root, "checkout", "-q", "--detach", "main")
    again = run_phase.prepare_branch(root, "0001", "design", start_point=intent_sha, intent_pr=12)
    assert again["from"] == "local" and git(root, "rev-parse", "HEAD").strip() == remote


def test_a_fast_lane_record_that_cannot_be_committed_refuses_the_run(lane, monkeypatch):
    """Second review, nit 2: no session runs on a fast-lane branch without its record."""
    from state import gitops

    root, _change, intent_sha = lane
    git(root, "checkout", "-q", "--detach", "main")

    def broken(*_a, **_k):
        raise gitops.GitError("index.lock exists")

    monkeypatch.setattr(gitops, "commit_paths", broken)
    branch = run_phase.prepare_branch(root, "0001", "design", start_point=intent_sha, intent_pr=12)
    assert "the fast-lane record was not committed: index.lock exists" in branch["refused"]
    git(root, "checkout", "-q", "-f", "--detach", "main")
    git(root, "branch", "-q", "-D", "sdlc/0001/design")
    monkeypatch.setattr(gitops, "commit_paths", lambda *_a, **_k: None)
    branch = run_phase.prepare_branch(root, "0001", "design", start_point=intent_sha, intent_pr=12)
    assert "nothing to commit" in branch["refused"]


def test_a_start_point_that_is_not_a_commit_is_refused_and_the_run_skips(lane, capsys):
    root, _change, _sha = lane
    git(root, "checkout", "-q", "--detach", "main")
    branch = run_phase.prepare_branch(root, "0001", "design", start_point="f" * 40, intent_pr=12)
    assert branch["switched"] is False and "not in the checkout" in branch["refused"]
    # the workflow passes the two values in the environment, never as flags (S2)
    args = Args(root=str(root), phase="design")
    env = {**KEY_ENV, "SDLC_START_POINT": "not-a-sha", "SDLC_INTENT_PR": "12"}
    assert run_phase.run_phase(args, env) == run_phase.EXIT_OK
    assert "design branch was not created" in json.loads(capsys.readouterr().out)["skipped"]
    # by hand, the flags still say the same
    args = Args(root=str(root), phase="design", start_point="not-a-sha", intent_pr="12")
    assert run_phase.run_phase(args, dict(KEY_ENV)) == run_phase.EXIT_OK
    assert "design branch was not created" in json.loads(capsys.readouterr().out)["skipped"]


# --- 4. the verdict of gate (design) --------------------------------------------------------
def _verdict(
    root: Path, classification="routine", head: str | None = None, verdict: str = "continue"
) -> None:
    head = head or git(root, "rev-parse", "HEAD").strip()
    path = root / CHANGE_REL / "evidence" / "adversarial-review-design.json"
    write(
        path,
        json.dumps(
            {"schema_version": 1, "phase": "design", "head": head, "verdict": verdict,
             "reasons": [], "classification": classification, "classification_reasons": []}
        ),
    )  # fmt: skip
    write_reviewer_record(path, head)  # what the panel_blind hook writes beside it (R7)


@pytest.fixture
def design(tmp_path, monkeypatch):
    """The design branch of tests/test_gate.py (the intent merged), its run registered."""
    from tests.test_gate import design_project

    return design_project.__wrapped__(tmp_path)


@pytest.mark.parametrize(
    ("classification", "runner", "expected"),
    [
        ("routine", True, ("continue", None, True)),
        ("non-routine", True, ("wait", "sdlc:design-ready", False)),
        ("routine", False, ("wait", "sdlc:design-ready", False)),  # by hand
    ],
)
def test_gate_b_continues_only_on_a_routine_plan_in_ci(
    design, monkeypatch, classification, runner, expected
):
    root, change = design
    _verdict(root, classification)
    if runner:
        monkeypatch.setenv(checks.COMMANDS_RUNNER_ENV, checks.RUN_BY_RUNNER)
    result = gate.run_gate(root, "0001", "design")
    assert (result.result, result.label, result.fast_lane) == expected
    recorded = json.loads((change / "evidence" / "gate-design.json").read_text(encoding="utf-8"))
    assert recorded.get("fast_lane", False) is expected[2]
    st = status_mod.read_status(change)
    assert st.gate.result == "passed" and st.fast_lane is None  # the gate never writes it
    if expected[2]:
        assert "fast lane (decision 30)" in st.gate.reason


def test_a_missing_or_invalid_verdict_or_a_park_never_takes_the_fast_lane(design, monkeypatch):
    root, change = design
    monkeypatch.setenv(checks.COMMANDS_RUNNER_ENV, checks.RUN_BY_RUNNER)
    result = gate.run_gate(root, "0001", "design")  # no verdict file: the gate parks
    assert result.result == "park" and result.fast_lane is False
    write(
        change / "evidence" / "adversarial-review-design.json", json.dumps({"verdict": "continue"})
    )
    result = gate.run_gate(root, "0001", "design")
    assert result.result == "park" and result.fast_lane is False
    # a routine verdict for another commit is stale: a park, never the fast lane
    _verdict(root, "routine", head="0" * 40)
    result = gate.run_gate(root, "0001", "design")
    assert result.result == "park" and result.fast_lane is False


def test_a_park_verdict_the_panel_settled_never_takes_the_fast_lane():
    """Decision 30 review, S3: the panel's ``continue`` passes the gate, but the reviewer's
    own verdict was ``park``: gate (design) waits for the owner."""
    from gate.checks import CheckResult

    def results(**details):
        return [CheckResult("adversarial_review", True, "ok", details=details)]

    routine = {"classification": "routine"}
    assert gate.fast_lane_applies("design", True, results(**routine), True) is True
    settled = results(**routine, settled_by_panel=1)
    assert gate.fast_lane_applies("design", True, settled, True) is False


# --- 5. the runner confirms, records and dispatches the build -------------------------------------
def _fast_gate_file(change: Path, head: str, fast: bool = True) -> None:
    data = {**ci_tests.GATE_FILE, "phase": "design", "human_gate": True, "head": head}
    if fast:
        data["fast_lane"] = True
    write(change / "evidence" / "gate-design.json", json.dumps(data))


def _design_run(
    root: Path,
    change: Path,
    fake_claude,
    monkeypatch,
    capsys,
    expect: int = run_phase.EXIT_OK,
    no_dispatch: bool = True,
    err: list[str] | None = None,
) -> dict:
    """One design run's JSON; ``err``, when given, receives what the run wrote to stderr."""
    monkeypatch.setenv("FAKE_CLAUDE_RESULT", json.dumps(FAKE_RESULT))
    args = Args(
        root=str(root),
        phase="design",
        dry_run=False,
        no_dispatch=no_dispatch,
        claude=fake_cli(fake_claude),
    )
    env = dict(os.environ, **KEY_ENV, GITHUB_TOKEN=FAKE_TOKEN)
    assert run_phase.run_phase(args, env) == expect
    captured = capsys.readouterr()
    if err is not None:
        err.append(captured.err)
    return json.loads(captured.out)


def test_a_routine_design_records_fast_lane_b_and_dispatches_the_build(
    lane, fake_claude, monkeypatch, capsys
):
    root, change, intent_sha = lane
    LaneGitHub(monkeypatch)
    out = _lane_design_run(root, change, intent_sha, fake_claude, monkeypatch, capsys)
    assert out["result"] == "continue" and out["fast_lane"]["recorded"] is True, out
    assert out["dispatched"] == {
        "would_dispatch": "sdlc-build.yml",
        "ref": "main",
        "change_id": "0001",
        "head_ref": "sdlc/0001/build",
    }
    head = out["fast_lane"]["design"]["sha"]
    st = status_mod.read_status(change)
    assert st.fast_lane == {
        "intent": {"sha": intent_sha, "pr": 12},
        "design": {"sha": head, "classification": "routine", "pr": 7},
    }
    # the pushed design branch is the one the build stacks on (R3: checked before the hand-over)
    assert run_phase.stacked_design(root, "0001") == "refs/remotes/origin/sdlc/0001/design"


@pytest.mark.parametrize(
    "why", ["non-routine", "missing", "other-head", "park", "escalate", "after-gate"]
)
def test_a_fast_lane_record_the_runner_does_not_confirm_waits_at_b(
    project, fake_claude, monkeypatch, capsys, why
):
    root, change = project
    pr_route(monkeypatch)
    head = git(root, "rev-parse", "HEAD").strip()
    _fast_gate_file(change, head)
    if why == "non-routine":
        _verdict(root, "non-routine", head)
    elif why == "other-head":
        _verdict(root, "routine", "0" * 40)
    elif why in ("park", "escalate"):  # S3: the reviewer's own verdict must be continue
        # ``escalate``: an older plugin's word, read as ``park`` for one release (R45 row 62);
        # refused as malformed since 1.0.48 (R45's sixth PR), and the design still waits
        _verdict(root, "routine", head, verdict=why)
    elif why == "after-gate":  # S7: a plan edit committed after the commit the gate judged
        _verdict(root, "routine", head)
        write(root / "notes.md", "an edit after the gate\n")
        git(root, "add", "notes.md")
        git(root, "commit", "-q", "-m", "after the gate")
    out = _design_run(root, change, fake_claude, monkeypatch, capsys)
    assert out["fast_lane"]["recorded"] is False and out["dispatched"] is None
    expected_reason = {
        "park": "the adversarial reviewer said park, not continue",
        "escalate": "the adversarial verdict is malformed: 'verdict' must be 'continue' or 'park'",
        "after-gate": "commits after the gate's commit changed notes.md",
    }.get(why, "")
    assert expected_reason in out["fast_lane"]["reason"]
    assert out["result"] == "wait" and out["label"] == "sdlc:design-ready"
    recorded = json.loads((change / "evidence" / "gate-design.json").read_text(encoding="utf-8"))
    assert "fast_lane" not in recorded and recorded["result"] == "wait"
    assert "fast lane refused" in recorded["config_note"]
    st = status_mod.read_status(change)
    assert st.fast_lane is None and st.gate.reason == run_phase.FAST_LANE_WAIT_REASON


def test_the_design_pr_number_is_recorded_once_the_pr_exists(
    lane, fake_claude, monkeypatch, capsys
):
    """Decision 30 review, N3: the design PR the hand-over opened is named in fast_lane.b, and
    committed before the build is dispatched, so the build PR's body names it."""
    root, change, intent_sha = lane
    LaneGitHub(monkeypatch)  # no open PR before the upsert; the upsert opens #7
    out = _lane_design_run(root, change, intent_sha, fake_claude, monkeypatch, capsys)
    assert out["fast_lane"]["recorded"] is True and out["fast_lane"]["pr_recorded"]["ok"]
    assert status_mod.read_status(change).fast_lane["design"]["pr"] == 7
    message = git(root, "log", "-1", "--format=%s", "origin/sdlc/0001/design")
    assert "design pull request #7 recorded" in message
    assert out["dispatched"]["would_dispatch"] == "sdlc-build.yml"


def test_a_fix_round_at_b_never_takes_the_fast_lane(project, fake_claude, monkeypatch, capsys):
    """Decision 30 review, S4: the fast lane is the design run's; a round at (b), the owner's
    or automatic, ends waiting for the owner's merge as before."""
    root, change = project
    pr_route(monkeypatch, number=13)
    for stub in ("apply_owner_labels", "collect_fix_requests"):
        monkeypatch.setattr(run_phase, stub, lambda *a, **k: {"ok": True})
    monkeypatch.setattr(run_phase, "take_red_targets", lambda *a, **k: {})
    ci_tests.set_state(change, "design", gate_phase="design", gate_result="passed")
    git(root, "checkout", "-q", "-b", "sdlc/0001/design")  # the design PR's head, the round's
    head = git(root, "rev-parse", "HEAD").strip()
    _fast_gate_file(change, head)
    _verdict(root, "routine", head)
    session_gate(monkeypatch, "design")  # the round's own gate writes its record (gap 4)
    monkeypatch.setenv("FAKE_CLAUDE_RESULT", json.dumps(FAKE_RESULT))
    args = Args(
        root=str(root), phase="fix", dry_run=False, no_dispatch=True, claude=fake_cli(fake_claude)
    )
    env = dict(os.environ, **KEY_ENV, GITHUB_TOKEN=FAKE_TOKEN)
    assert run_phase.run_phase(args, env) == run_phase.EXIT_OK
    out = json.loads(capsys.readouterr().out)
    assert out.get("gate_phase") == "design", out
    assert out["fast_lane"]["recorded"] is False
    assert out["fast_lane"]["reason"] == run_phase.FAST_LANE_FIX_REFUSAL
    assert (
        out["result"] == "wait"
        and out["label"] == "sdlc:design-ready"
        and out["dispatched"] is None
    )
    assert status_mod.read_status(change).fast_lane is None


def test_an_unreadable_diff_after_the_gate_refuses_the_fast_lane(lane):
    """Second review, nit 1: a git error reading the commits after the gate is a refusal,
    never "nothing changed"."""
    root, _change, intent_sha = lane
    assert run_phase.fast_lane_after_gate(root, CHANGE_REL, intent_sha, "HEAD") is None
    refused = run_phase.fast_lane_after_gate(root, CHANGE_REL, "f" * 40, "HEAD")
    assert refused and refused.startswith("the commits after the gate's commit cannot be read")


def test_a_plain_continue_at_b_still_dispatches_nothing():
    args = Args(no_dispatch=True)
    assert run_phase.hand_over(args, {"result": "continue"}, "design", "0001") is None
    assert (
        run_phase.hand_over(args, {"result": "wait", "fast_lane": True}, "design", "0001") is None
    )
    handed = run_phase.hand_over(args, {"result": "continue", "fast_lane": True}, "design", "0001")
    assert handed["would_dispatch"] == "sdlc-build.yml" and handed["head_ref"] == "sdlc/0001/build"


def test_a_session_that_writes_fast_lane_parks_with_the_field_restored(
    project, fake_claude, monkeypatch, capsys, tmp_path
):
    root, change = project
    pr_route(monkeypatch)
    script = tmp_path / "forge.py"
    write(
        script,
        "import sys\n"
        f"sys.path.insert(0, {str(ci_tests.ROOT / 'plugin')!r})\n"
        "from pathlib import Path\n"
        "from state import status\n"
        f"change = Path({str(change)!r})\n"
        "st = status.read_status(change)\n"
        "st.fast_lane = {'design': {'sha': 'a' * 40, 'classification': 'routine'}}\n"
        "status.write_status(change, st)\n",
    )
    monkeypatch.setenv("FAKE_CLAUDE_RUN", str(script))
    _fast_gate_file(change, git(root, "rev-parse", "HEAD").strip())
    out = _design_run(root, change, fake_claude, monkeypatch, capsys)
    assert out["parked"].startswith("status.yaml: the session wrote owner-only field(s): ")
    assert "fast_lane: the session recorded" in out["parked"] and "dispatched" not in out
    assert status_mod.read_status(change).fast_lane is None


def test_owner_field_mismatches_accept_the_runner_s_record_and_the_default_branch_s():
    before = run_phase.owner_fields(status_mod.Status(id="0001", slug="x", title="X"))
    lane = {"intent": {"sha": "a" * 40, "pr": 3}}
    after = {**before, "fast_lane": json.dumps(lane, sort_keys=True)}
    assert run_phase.owner_field_mismatches(before, before, None) == []
    assert run_phase.owner_field_mismatches(before, after, after) == []  # a merge brought it
    (reason,) = run_phase.owner_field_mismatches(before, after, None)
    assert reason.startswith("fast_lane: the session recorded")


# --- 6. the build's start point -------------------------------------------------------------------
def _confirmed_design(root: Path, change: Path, intent_sha: str) -> tuple[str, str]:
    """The design branch as a confirmed fast-lane run leaves it, pushed: the gate's record of
    the fast lane, the reviewer's routine ``continue`` for the judged commit, then the runner's
    ``fast_lane.b``. Returns (the judged commit, the branch's tip)."""
    design = _design_on_the_lane(root, change, intent_sha)
    evidence = change / "evidence"
    gate_b = {**ci_tests.GATE_FILE, "phase": "design", "head": design, "fast_lane": True}
    write(evidence / "gate-design.json", json.dumps(gate_b))
    _verdict(root, "routine", design)
    lane_record = dict(status_mod.read_status(change).fast_lane or {})
    lane_record["design"] = {"sha": design, "classification": "routine"}
    _status(change, fast_lane=lane_record, gate=status_mod.Gate("design", "passed"))
    git(root, "add", ".")
    git(root, "commit", "-q", "-m", "run(design): gate evidence, fast lane")
    git(root, "push", "-q", "-u", "origin", "sdlc/0001/design")
    return design, git(root, "rev-parse", "HEAD").strip()


def test_the_build_is_cut_from_the_design_on_the_fast_lane_and_from_main_after_a_merge(lane):
    root, change, intent_sha = lane
    _design, design_tip = _confirmed_design(root, change, intent_sha)
    git(root, "checkout", "-q", "main")
    assert run_phase._start_point(root, "0001", "build") == "refs/remotes/origin/sdlc/0001/design"
    branch = run_phase.prepare_branch(root, "0001", "build")
    assert branch["from"] == "refs/remotes/origin/sdlc/0001/design"
    assert git(root, "rev-parse", "HEAD").strip() == design_tip
    # the (c) guard reads that tree: phase b, gate b passed
    assert ci_tests.skip_reason(root, "build") is None
    # the owner merged the design PR by hand: the default branch carries the design, and the
    # build starts from it as before
    git(root, "checkout", "-q", "main")
    git(root, "branch", "-q", "-D", "sdlc/0001/build")
    git(root, "merge", "-q", "--squash", "sdlc/0001/design")
    git(root, "commit", "-q", "-m", "design(0001) merged (squash)")
    git(root, "push", "-q", "origin", "main")
    git(root, "fetch", "-q", "origin")
    assert run_phase._start_point(root, "0001", "build") == "refs/remotes/origin/main"


@pytest.mark.parametrize("pushed", ["no-gate-record", "non-routine", "park", "plan"])
def test_a_design_branch_record_that_does_not_hold_starts_the_build_from_main(lane, pushed):
    """Decision 30 review, B2: anyone with write access could push ``fast_lane.b`` and
    ``gate b/passed``; the build is stacked only when the
    branch's gate record, verdict and later commits say the same as the runner confirmed.
    Otherwise it starts from the default branch, where the (c) guard refuses."""
    root, change, intent_sha = lane
    design, _tip = _confirmed_design(root, change, intent_sha)
    gate_file = change / "evidence" / "gate-design.json"
    if pushed == "no-gate-record":
        record = json.loads(gate_file.read_text(encoding="utf-8"))
        record.pop("fast_lane")
        write(gate_file, json.dumps({**record, "result": "wait"}))
    elif pushed == "non-routine":
        _verdict(root, "non-routine", design)
    elif pushed == "park":
        _verdict(root, "routine", design, verdict="park")
    elif pushed == "plan":
        write(change / "plan.md", PLAN + "\nOne more step, written after the gate.\n")
    git(root, "commit", "-q", "-am", f"pushed: {pushed}")
    git(root, "push", "-q", "origin", "sdlc/0001/design")
    git(root, "checkout", "-q", "main")
    git(root, "fetch", "-q", "origin")
    assert run_phase.stacked_design(root, "0001") is None
    assert run_phase._start_point(root, "0001", "build") == "refs/remotes/origin/main"


def test_a_merged_design_pr_whose_build_already_started_starts_no_second_build(
    lane, tmp_path, monkeypatch, capsys
):
    """Decision 30 review, N2: the build workflow's merge path skips with a reason when the
    design branch records the fast lane and the build branch exists."""
    root, change, intent_sha = lane
    design = _design_on_the_lane(root, change, intent_sha)
    _build_on_the_lane(root, change, design)
    _files(monkeypatch, INTENT_FILES)
    output = tmp_path / "github-output"
    output.write_text("", encoding="utf-8")
    env = {"GITHUB_EVENT_NAME": "pull_request", "GITHUB_OUTPUT": str(output)}
    args = Args(root=str(root), phase="build", id=None, head_ref="claude/x", pr_number="13")
    assert run_phase.print_found_change(args, env) == run_phase.EXIT_OK
    assert output.read_text(encoding="utf-8") == "change_id=0001\n"  # no build branch yet
    git(root, "push", "-q", "origin", "sdlc/0001/build")
    capsys.readouterr()
    assert run_phase.print_found_change(args, env) == run_phase.EXIT_OK
    printed = capsys.readouterr().out
    assert output.read_text(encoding="utf-8").endswith("change_id=0001\nchange_id=\n")
    assert "already started on the fast lane" in printed


# --- 7. superseded pull requests ------------------------------------------------------------------
class SupersedeGitHub:
    """``pr_by_number``, ``ensure_label``, ``set_labels``, ``close_pr`` and ``find_open_pr``,
    in order; no comment call exists, so a comment would fail the test."""

    def __init__(self, state="open", label_ok=True, open_prs=None, head_sha=None, labels=None):
        self.calls: list = []
        self.state = state
        self.label_ok = label_ok
        self.open_prs = open_prs or {}
        self.head_sha = head_sha
        self.labels = labels or []

    def pr_by_number(self, repo, number, cwd=None):
        self.calls.append(("pr_by_number", number))
        return {
            "ok": True,
            "number": number,
            "state": self.state,
            "head_sha": self.head_sha,
            "labels": list(self.labels),
        }

    def ensure_label(self, repo, name, color, description, cwd=None):
        self.calls.append(("ensure_label", name))
        return {"ok": True}

    def set_labels(self, repo, number, add, remove, cwd=None):
        self.calls.append(("set_labels", number, list(add), list(remove)))
        return {"ok": self.label_ok, "reason": "" if self.label_ok else "403"}

    def close_pr(self, repo, number, cwd=None):
        self.calls.append(("close_pr", number))
        return {"ok": True, "number": number}

    def find_open_pr(self, repo, head, cwd=None):
        self.calls.append(("find_open_pr", head))
        return {"ok": True, "number": self.open_prs.get(head)}

    def gh_path(self):
        return None


def test_supersede_labels_then_closes_and_never_comments(monkeypatch):
    fake = SupersedeGitHub()
    monkeypatch.setattr(run_phase, "_github", lambda: fake)
    out = run_phase.supersede_pr(REPO, 12, 13)
    assert out == {"ok": True, "number": 12, "by": 13, "labelled": True}
    assert [call[0] for call in fake.calls] == [
        "pr_by_number", "ensure_label", "set_labels", "close_pr",
    ]  # fmt: skip
    assert fake.calls[2] == ("set_labels", 12, [c.SUPERSEDED_LABEL], [])
    # a label that cannot be applied leaves the PR open: a close without it would abandon
    fake = SupersedeGitHub(label_ok=False)
    monkeypatch.setattr(run_phase, "_github", lambda: fake)
    out = run_phase.supersede_pr(REPO, 12, 13)
    assert out["ok"] is False and "left open" in out["reason"]
    assert "close_pr" not in [call[0] for call in fake.calls]
    # a PR that is not open is left as it is
    fake = SupersedeGitHub(state="closed")
    monkeypatch.setattr(run_phase, "_github", lambda: fake)
    assert run_phase.supersede_pr(REPO, 12, 13)["skipped"]
    assert [call[0] for call in fake.calls] == ["pr_by_number"]


def test_supersede_leaves_the_owner_s_later_work_and_a_reopened_pr_alone(monkeypatch, capsys):
    """Decision 30 review, S6: an intent PR whose head moved after the design started (the
    owner pushed again) stays open, and a PR that already carries the label was reopened by
    the owner: it is never closed again."""
    fake = SupersedeGitHub(head_sha="b" * 40)
    monkeypatch.setattr(run_phase, "_github", lambda: fake)
    out = run_phase.supersede_pr(REPO, 12, 13, expected_head="a" * 40)
    assert out["ok"] is False and "left open" in out["reason"]
    assert [call[0] for call in fake.calls] == ["pr_by_number"]
    assert "after the design started" in capsys.readouterr().err
    fake = SupersedeGitHub(head_sha="a" * 40, labels=[c.SUPERSEDED_LABEL])
    monkeypatch.setattr(run_phase, "_github", lambda: fake)
    out = run_phase.supersede_pr(REPO, 12, 13, expected_head="a" * 40)
    assert "reopened after it was superseded" in out["skipped"]
    assert [call[0] for call in fake.calls] == ["pr_by_number"]
    # the head the design started from: superseded
    fake = SupersedeGitHub(head_sha="a" * 40)
    monkeypatch.setattr(run_phase, "_github", lambda: fake)
    assert run_phase.supersede_pr(REPO, 12, 13, expected_head="a" * 40)["ok"] is True
    assert ("close_pr", 12) in fake.calls


def test_the_design_run_supersedes_the_intent_pr_once_its_pr_exists(lane, monkeypatch):
    root, change, intent_sha = lane
    _design_on_the_lane(root, change, intent_sha)
    fake = SupersedeGitHub(open_prs={"sdlc/0001/design": 13}, head_sha=intent_sha)
    monkeypatch.setattr(run_phase, "_github", lambda: fake)
    args = Args(root=str(root), repo=REPO)
    track = {"change_dir": change, "gate_phase": "design"}
    env = {"GITHUB_TOKEN": FAKE_TOKEN}
    out = run_phase.supersede_earlier_pr(args, env, track)
    assert out["ok"] is True and out["number"] == 12 and out["by"] == 13
    assert ("close_pr", 12) in fake.calls
    # no design PR yet: nothing is closed
    fake = SupersedeGitHub()
    monkeypatch.setattr(run_phase, "_github", lambda: fake)
    out = run_phase.supersede_earlier_pr(args, env, track)
    assert out["ok"] is False and "no open pull request on sdlc/0001/design" in out["reason"]
    assert "close_pr" not in [call[0] for call in fake.calls]
    # off the fast lane: nothing to supersede, nothing asked of GitHub
    _status(change, fast_lane=None)
    fake = SupersedeGitHub()
    monkeypatch.setattr(run_phase, "_github", lambda: fake)
    assert run_phase.supersede_earlier_pr(args, env, track) is None and fake.calls == []


def test_the_build_run_supersedes_the_design_pr(lane, monkeypatch):
    root, change, intent_sha = lane
    design = _design_on_the_lane(root, change, intent_sha)
    _build_on_the_lane(root, change, design)
    fake = SupersedeGitHub(open_prs={"sdlc/0001/build": 14})
    monkeypatch.setattr(run_phase, "_github", lambda: fake)
    args = Args(root=str(root), repo=REPO)
    out = run_phase.supersede_earlier_pr(
        args, {"GITHUB_TOKEN": FAKE_TOKEN}, {"change_dir": change, "gate_phase": "build"}
    )
    assert out["ok"] is True and out["number"] == 13 and out["by"] == 14


def test_a_failing_supersede_never_fails_the_run(project, monkeypatch, capsys):
    root, change = project

    def boom(*_a, **_k):
        raise RuntimeError("GitHub is down")

    monkeypatch.setattr(run_phase, "supersede_earlier_pr", boom)
    monkeypatch.setattr(
        run_phase, "_run_phase", lambda args, env, track: track.update(change_dir=change) or 0
    )
    args = Args(root=str(root), phase="design", dry_run=False)
    assert run_phase.run_phase(args, {}) == run_phase.EXIT_OK
    assert "was not superseded: GitHub is down" in capsys.readouterr().err


# --- 8. the abandon rule ------------------------------------------------------------------------
class LaneGitHub:
    """The GitHub calls a design run makes, answered here: the intent PR in ``intent_state``,
    no open PR before the upsert, labels created. ``create_pr`` must never be called."""

    def __init__(self, monkeypatch, intent_state="open", merged=False, labels=None, upsert=True):
        self.calls: list = []
        answers = {
            "pr_by_number": lambda repo, number, cwd=None: {
                "ok": True, "number": number, "state": intent_state, "merged": merged,
                "labels": list(labels or []), "head_sha": None,
            },
            "find_open_pr": lambda repo, head, cwd=None: {"ok": True, "number": None},
            "find_pr": lambda repo, head, state="open", cwd=None: {"ok": True, "number": None},
            "ensure_label": lambda *a, **k: {"ok": True},
            "set_labels": lambda *a, **k: {"ok": True},
            "close_pr": lambda *a, **k: {"ok": True},
            "gh_path": lambda: None,
        }  # fmt: skip
        for name, answer in answers.items():
            monkeypatch.setattr(github, name, self._record(name, answer))

        def no_create(*_a, **_k):
            raise AssertionError("no pull request may be opened")

        monkeypatch.setattr(github, "create_pr", no_create)
        real = run_phase._cli_call

        def cli_call(script, argv, timeout=600, env=None):
            if Path(script).parent.name == "pr" and argv and argv[0] == "upsert":
                self.calls.append(("upsert", list(argv)))
                if not upsert:  # GitHub refused to open the pull request
                    return {"ok": False, "reason": "HTTP 502", "output": {"route": "api"}}
                return {"ok": True, "reason": "", "output": {"route": "api", "number": 7}}
            return real(script, argv, timeout, env)

        monkeypatch.setattr(run_phase, "_cli_call", cli_call)

    def _record(self, name, answer):
        def call(*a, **k):
            self.calls.append((name, a))
            return answer(*a, **k)

        return call

    def names(self) -> list[str]:
        return [name for name, _args in self.calls]


def _lane_design_run(
    root, change, intent_sha, fake_claude, monkeypatch, capsys, session=None, **run
) -> dict:
    """A design run on the fast lane's branch (cut from the intent PR's head, the record
    committed, nothing pushed yet, S5), whose gate passed on a routine plan."""
    git(root, "checkout", "-q", "-b", "sdlc/0001/design", intent_sha)
    _status(change, fast_lane={"intent": {"sha": intent_sha, "pr": 12}})
    git(root, "commit", "-q", "-am", "run(design): fast lane from intent PR #12")
    head = git(root, "rev-parse", "HEAD").strip()
    gate_b = {**ci_tests.GATE_FILE, "phase": "design", "human_gate": True, "head": head}
    write(change / "evidence" / "gate-design.json", json.dumps({**gate_b, "fast_lane": True}))
    _verdict(root, "routine", head)
    if session:
        monkeypatch.setenv("FAKE_CLAUDE_RUN", str(session))
    return _design_run(root, change, fake_claude, monkeypatch, capsys, **run)


def test_the_owner_s_close_of_the_intent_pr_before_the_design_branch_is_pushed_abandons(
    lane, fake_claude, monkeypatch, capsys
):
    """Decision 30 review, S1, and the second review, R1: the owner closes the intent PR
    while the design runs and before its branch reaches origin, so ``sdlc-abandon.yml`` has
    no copy of it to mark; the design run records the close itself (decision 25: the close
    is the act), pushes the abandoned branch and opens no PR, dispatches nothing."""
    root, change, intent_sha = lane
    # the abandon job on the closed head: the design branch is not on origin yet
    argv = ["abandon", "--root", str(root), "--id", "0001", "--push", "--all-branches"]
    assert state_cli.main(argv) == 0
    capsys.readouterr()
    assert status_mod.read_status(change).abandoned
    assert git(root, "ls-remote", "--heads", "origin", "sdlc/0001/design").strip() == ""
    fake = LaneGitHub(monkeypatch, intent_state="closed")
    git(root, "checkout", "-q", intent_sha)  # the runner's checkout: the intent PR's head
    out = _lane_design_run(root, change, intent_sha, fake_claude, monkeypatch, capsys)
    assert out["abandoned"]["ok"] is True
    assert out["abandoned"]["reason"] == "pull request #12 closed without a merge"
    assert "dispatched" not in out and "upsert" not in fake.names()
    remote = git(root, "show", f"origin/sdlc/0001/design:{CHANGE_REL}/status.yaml")
    assert "phase: abandoned" in remote and "pull request #12 closed" in remote


@pytest.mark.parametrize(
    ("state", "merged", "labels", "phase", "abandons"),
    [
        ("closed", False, [], "build", True),
        ("closed", False, [c.SUPERSEDED_LABEL], "build", False),  # the runner's own close
        ("closed", True, [], "build", False),  # merged by the owner
        ("open", False, [], "build", False),
        ("closed", False, [], "fix", False),  # a fix round reads nothing of it
    ],
)
def test_a_stacked_build_reads_the_owner_s_close_of_the_design_pr(
    lane, monkeypatch, state, merged, labels, phase, abandons
):
    """Second review, R1, at (c): the design PR closed without a merge and without the label
    before the build's branch reached origin is the owner's abandon."""
    root, change, intent_sha = lane
    design = _design_on_the_lane(root, change, intent_sha)
    _build_on_the_lane(root, change, design)
    LaneGitHub(monkeypatch, intent_state=state, merged=merged, labels=labels)
    env = {"GITHUB_TOKEN": FAKE_TOKEN}
    found = run_phase.earlier_pr_closed(root, change, phase, REPO, env)
    assert (found == "pull request #13 closed without a merge") is abandons, found


@pytest.mark.parametrize("demotion_pushed", [True, False])
def test_a_design_the_build_s_check_would_refuse_waits_at_b_with_its_label(
    lane, fake_claude, monkeypatch, capsys, tmp_path, demotion_pushed
):
    """Second review, R3: the session leaves a plan edit uncommitted; the runner's
    confirmation reads the committed diff and passes, the run record sweeps the edit in, and
    the build's ``stacked_design`` would refuse the pushed branch. The design run checks the
    pushed branch the same way, waits at (b) with ``sdlc:design-ready`` and dispatches nothing."""
    root, change, intent_sha = lane
    fake = LaneGitHub(monkeypatch)
    session = tmp_path / "edit.py"
    write(
        session,
        "from pathlib import Path\n"
        f"plan = Path({str(change / 'plan.md')!r})\n"
        "plan.write_text(plan.read_text(encoding='utf-8') + '\\nlate edit\\n', 'utf-8')\n",
    )
    write(change / "plan.md", PLAN)
    git(root, "add", ".")
    git(root, "commit", "-q", "-m", "intent: plan seed")
    git(root, "push", "-q", "origin", "claude/intent")
    intent_sha = git(root, "rev-parse", "HEAD").strip()
    if not demotion_pushed:  # review of 1.0.11: the run ends red and names the merge
        _refuse_the_demotion(monkeypatch, "refused by the build's check")
    err: list[str] = []
    out = _lane_design_run(
        root, change, intent_sha, fake_claude, monkeypatch, capsys, session=session, err=err,
        expect=run_phase.EXIT_OK if demotion_pushed else run_phase.EXIT_FAILED,
    )  # fmt: skip
    assert out["fast_lane"]["recorded"] is False
    assert out["fast_lane"]["reason"] == (
        "the build's own check of the pushed design branch refused it"
    )
    assert out["dispatched"] is None
    assert out["result"] == "wait" and out["label"] == "sdlc:design-ready"
    assert fake.names().count("upsert") == 2  # the label is applied again after the demotion
    if not demotion_pushed:
        assert "merge the design pull request (sdlc:design-ready)" in err[0]
        return
    gate_b = json.loads(
        git(root, "show", f"origin/sdlc/0001/design:{CHANGE_REL}/evidence/gate-design.json")
    )
    assert gate_b["result"] == "wait" and "fast_lane" not in gate_b
    remote = git(root, "show", f"origin/sdlc/0001/design:{CHANGE_REL}/status.yaml")
    assert "  design:" not in remote and "  intent:" in remote


# --- 8b. a pushed fast_lane.b always has a build behind it, or waits at (b) (plugin 1.0.11) -----
def _dispatches(monkeypatch, answer: dict) -> list:
    """``run_phase.dispatch`` answering ``answer``; returns the calls it saw."""
    calls: list = []

    def fake(repo, workflow, ref, change_id, head_ref, extra_inputs=None):
        calls.append((workflow, change_id, head_ref))
        return dict(answer)

    monkeypatch.setattr(run_phase, "dispatch", fake)
    return calls


def test_a_design_pr_that_cannot_be_opened_still_dispatches_the_build(
    lane, fake_claude, monkeypatch, capsys
):
    """Before 1.0.11 a design run whose PR GitHub refused pushed ``fast_lane.b`` and dispatched
    nothing, and every later design event skipped as "design done". The build PR carries the
    design on the fast lane, so the build is dispatched; the run still ends red."""
    root, change, intent_sha = lane
    LaneGitHub(monkeypatch, upsert=False)
    calls = _dispatches(monkeypatch, {"ok": True, "status": 204, "reason": ""})
    err: list[str] = []
    out = _lane_design_run(
        root, change, intent_sha, fake_claude, monkeypatch, capsys,
        expect=run_phase.EXIT_FAILED, no_dispatch=False, err=err,
    )  # fmt: skip
    assert out["pr"]["ok"] is False and out["fast_lane"]["recorded"] is True, out
    assert "pr_recorded" not in out["fast_lane"]
    assert calls == [("sdlc-build.yml", "0001", "sdlc/0001/build")]
    assert out["dispatched"]["ok"] is True
    assert "no pull request carries this phase's result" in err[0]
    assert run_phase.FAST_LANE_BUILD_CARRIES in err[0]
    # the record the build stacks on stands on origin, without a design PR's number
    assert run_phase.stacked_design(root, "0001") == "refs/remotes/origin/sdlc/0001/design"
    remote = git(root, "show", f"origin/sdlc/0001/design:{CHANGE_REL}/status.yaml")
    assert "  design:" in remote and "pr: 7" not in remote


@pytest.mark.parametrize("demotion_pushed", [True, False])
def test_a_build_dispatch_github_refuses_puts_the_design_back_at_b(
    lane, fake_claude, monkeypatch, capsys, demotion_pushed
):
    """A refused dispatch would leave ``fast_lane.design`` pushed with no build: the design
    waits at its gate with ``sdlc:design-ready`` instead, the record dropped on origin, so the
    owner's merge starts the build and no later design event reads the change as done."""
    root, change, intent_sha = lane
    fake = LaneGitHub(monkeypatch)
    calls = _dispatches(monkeypatch, {"ok": False, "status": 403, "reason": "HTTP 403"})
    if not demotion_pushed:
        _refuse_the_demotion(monkeypatch, "not dispatched")
    err: list[str] = []
    out = _lane_design_run(
        root, change, intent_sha, fake_claude, monkeypatch, capsys, no_dispatch=False,
        expect=run_phase.EXIT_OK if demotion_pushed else run_phase.EXIT_FAILED, err=err,
    )  # fmt: skip
    assert calls == [("sdlc-build.yml", "0001", "sdlc/0001/build")]
    assert out["fast_lane"]["recorded"] is False
    assert out["fast_lane"]["reason"] == "the build was not dispatched: HTTP 403"
    assert out["result"] == "wait" and out["label"] == "sdlc:design-ready"
    assert fake.names().count("upsert") == 2  # the label is applied again after the demotion
    if not demotion_pushed:
        assert "the fast lane's demotion to gate (design) was not committed and pushed" in err[0]
        return
    assert out["fast_lane"]["demoted"]["ok"] is True
    gate_b = json.loads(
        git(root, "show", f"origin/sdlc/0001/design:{CHANGE_REL}/evidence/gate-design.json")
    )
    assert gate_b["result"] == "wait" and "fast_lane" not in gate_b
    assert "the build was not dispatched: HTTP 403" in gate_b["config_note"]
    remote = git(root, "show", f"origin/sdlc/0001/design:{CHANGE_REL}/status.yaml")
    assert "  design:" not in remote and "  intent:" in remote
    assert run_phase.carried_forward(root, "0001") is None


def _refuse_the_demotion(monkeypatch, marker: str) -> None:
    """``commit_run_record`` refuses the commit whose note carries ``marker``."""
    real = run_phase.commit_run_record

    def refuse(*a, note=None, **k):
        if note and marker in note:
            return {"ok": False, "reason": "push refused"}
        return real(*a, note=note, **k)

    monkeypatch.setattr(run_phase, "commit_run_record", refuse)


@pytest.mark.parametrize("demotion_pushed", [True, False])
def test_a_refused_dispatch_after_a_refused_design_pr_retries_the_pr_and_says_what_is_left(
    lane, fake_claude, monkeypatch, capsys, demotion_pushed
):
    """Review of 1.0.11: GitHub refuses the design PR and then the dispatch. The demotion is
    pushed and the PR tried again; a demotion that is not pushed either still names the way
    out, beside the missing PR."""
    root, change, intent_sha = lane
    fake = LaneGitHub(monkeypatch, upsert=False)
    _dispatches(monkeypatch, {"ok": False, "status": None, "reason": "connection reset"})
    if not demotion_pushed:
        _refuse_the_demotion(monkeypatch, "not dispatched")
    err: list[str] = []
    out = _lane_design_run(
        root, change, intent_sha, fake_claude, monkeypatch, capsys, no_dispatch=False,
        expect=run_phase.EXIT_FAILED, err=err,
    )  # fmt: skip
    assert out["fast_lane"]["recorded"] is False and out["result"] == "wait"
    assert fake.names().count("upsert") == 2
    assert "no pull request carries this phase's result" in err[0]
    assert run_phase.FAST_LANE_BUILD_CARRIES not in err[0]
    remote = git(root, "show", f"origin/sdlc/0001/design:{CHANGE_REL}/status.yaml")
    if demotion_pushed:
        assert "  design:" not in remote
        assert "demotion to gate (design) was not committed" not in err[0]
    else:
        assert "  design:" in remote
        assert "merge the design pull request (sdlc:design-ready)" in err[0]


def test_a_stacked_build_reads_the_owner_s_close_of_the_intent_pr_with_no_design_pr(
    lane, monkeypatch
):
    """Review of 1.0.11: with no design PR ever opened the build carries the intent PR
    forward, so the owner's close of it without the label abandons, as a design PR's would."""
    root, change, intent_sha = lane
    design = _design_on_the_lane(root, change, intent_sha)
    _build_on_the_lane(root, change, design, design_pr=None)
    env = {"GITHUB_TOKEN": FAKE_TOKEN}
    LaneGitHub(monkeypatch, intent_state="closed")
    found = run_phase.earlier_pr_closed(root, change, "build", REPO, env)
    assert found == "pull request #12 closed without a merge"
    LaneGitHub(monkeypatch, intent_state="closed", labels=[c.SUPERSEDED_LABEL])
    assert run_phase.earlier_pr_closed(root, change, "build", REPO, env) is None


def test_the_build_run_supersedes_the_intent_pr_when_no_design_pr_was_opened(lane, monkeypatch):
    root, change, intent_sha = lane
    design = _design_on_the_lane(root, change, intent_sha)
    _build_on_the_lane(root, change, design, design_pr=None)
    args = Args(root=str(root), repo=REPO)
    env = {"GITHUB_TOKEN": FAKE_TOKEN}
    track = {"change_dir": change, "gate_phase": "build"}
    fake = SupersedeGitHub(open_prs={"sdlc/0001/build": 14}, head_sha=intent_sha)
    monkeypatch.setattr(run_phase, "_github", lambda: fake)
    out = run_phase.supersede_earlier_pr(args, env, track)
    assert out["ok"] is True and out["number"] == 12 and out["by"] == 14
    assert ("close_pr", 12) in fake.calls
    # the owner pushed to the intent PR after the design started: their commits stay open
    fake = SupersedeGitHub(open_prs={"sdlc/0001/build": 14}, head_sha="b" * 40)
    monkeypatch.setattr(run_phase, "_github", lambda: fake)
    run_phase.supersede_earlier_pr(args, env, track)
    assert "close_pr" not in [call[0] for call in fake.calls]


# --- 9. the workflows and the text the owner reads ------------------------------------------------
def _yaml(name: str) -> dict:
    yaml = pytest.importorskip("yaml")
    return yaml.safe_load((WORKFLOWS / name).read_text(encoding="utf-8"))


def test_the_design_workflow_starts_on_the_owner_s_opened_intent_pr():
    data = _yaml("sdlc-design.yml")
    on = data.get("on", data.get(True))
    assert on["pull_request"]["types"] == ["opened", "reopened", "closed"]
    job = data["jobs"]["design"]
    condition = " ".join(job["if"].split())
    for part in (
        "github.event.pull_request.merged == true",
        "(github.event.action == 'opened' || github.event.action == 'reopened')",
        "github.event.pull_request.head.repo.full_name == github.repository",
        "!endsWith(github.event.pull_request.user.login, '[bot]')",
        "!endsWith(github.event.sender.login, '[bot]')",
        "github.event.pull_request.draft == false",
    ):
        assert part in condition, part
    find = next(step for step in job["steps"] if step.get("id") == "find")
    assert find["env"]["SDLC_DEFAULT_BRANCH"] == "${{ github.event.repository.default_branch }}"
    run = next(step for step in job["steps"] if step.get("id") == "phase")
    # S2: in the environment, never as flags an older pinned framework would reject
    assert run["env"]["SDLC_START_POINT"] == "${{ steps.find.outputs.start_point }}"
    assert run["env"]["SDLC_INTENT_PR"] == "${{ steps.find.outputs.intent_pr }}"
    assert "--start-point" not in run["run"] and "--intent-pr" not in run["run"]
    assert run["env"].keys() >= {"SDLC_START_POINT", "SDLC_INTENT_PR"}
    assert run_phase.START_POINT_ENV == "SDLC_START_POINT"
    assert run_phase.INTENT_PR_ENV == "SDLC_INTENT_PR"
    assert data["concurrency"]["group"] == (
        "sdlc-${{ inputs.head_ref || github.event.pull_request.head.ref }}"
    )


def test_the_abandon_workflow_skips_a_superseded_pr():
    job = _yaml("sdlc-abandon.yml")["jobs"]["abandon"]
    assert "!contains(github.event.pull_request.labels.*.name, 'sdlc:superseded')" in job["if"]
    assert c.SUPERSEDED_LABEL == "sdlc:superseded"


def test_the_pr_bodies_name_what_the_fast_lane_carries_and_superseded(lane):
    root, change, intent_sha = lane
    design = _design_on_the_lane(root, change, intent_sha)
    st = status_mod.read_status(change)
    line = desc.fast_lane_line(root, st, "design")
    assert "carries your intent too" in line and "intent PR #12" in line
    assert line in desc.build_description(root, "0001", "design")
    _build_on_the_lane(root, change, design)
    st = status_mod.read_status(change)
    line = desc.fast_lane_line(root, st, "build")
    assert "the intent, spec and plan are in this PR with the code" in line
    assert "(superseded: intent PR #12, design PR #13)" in line
    # off the fast lane, no line
    assert (
        desc.fast_lane_line(root, status_mod.Status(id="0001", slug="x", title="X"), "build") == ""
    )


def test_the_status_record_is_validated_and_absent_off_the_fast_lane():
    st = status_mod.Status(id="0001", slug="x", title="X")
    assert "fast_lane" not in st.to_dict()
    for bad in (
        {},
        {"build": {"sha": "a" * 40}},
        {"intent": {"sha": "short", "pr": 1}},
        {"intent": {"sha": "a" * 40}},
        {"design": {"sha": "a" * 40, "classification": "non-routine"}},
        {"intent": {"sha": "a" * 40, "pr": 1, "extra": 1}},
    ):
        st.fast_lane = bad
        with pytest.raises(ValueError, match="fast_lane"):
            st.validate()
    st.fast_lane = {"intent": {"sha": "1" * 40, "pr": 3}}
    again = status_mod.Status.from_dict(
        status_mod.yamlish.loads(status_mod.yamlish.dumps(st.to_dict()))
    )
    assert again.fast_lane == st.fast_lane
    assert re.search(r"(?m)^fast_lane:$", status_mod.yamlish.dumps(st.to_dict()))
