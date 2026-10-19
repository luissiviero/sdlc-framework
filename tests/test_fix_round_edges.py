"""Plugin 1.0.10, the first review round of the fix-round robustness PR (NOTES §45 gaps 2-4,
choice 218):

- an unfinished fix round always parks, with or without work to keep, and a session that
  failed after its own gate says so;
- the fix round with nothing to do is skipped before the session, and a label another
  account applied is refused by the find step (choice 218);
- the restart of a build parked at the preflight merges a default branch that changed the
  change's ``status.yaml`` (a stacked fast-lane build included), and a dry run merges nothing;
- the kept work leaves out the settings and hooks of a nested ``.claude/``;
- ``/sdlc-fix`` tells an undecided session to end its turn with the question, never to park.

The GitHub calls are replaced by fakes, as ``tests/test_ci.py`` does: no network, no token.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest
from ci import run_phase

from state import conventions as c
from state import status as status_mod
from tests import test_ci as ci_tests
from tests import test_fix_round_gaps as gaps
from tests import test_owner_rounds as owner_rounds
from tests.test_ci import (
    DEFERRED_GATE_FILE,
    FAKE_RESULT,
    FAKE_TOKEN,
    GATE_FILE,
    KEY_ENV,
    Args,
    fake_cli,
    git,
    set_state,
    write,
)

# the fixtures of tests/test_ci.py, used here by name
project = ci_tests.project
fake_claude = ci_tests.fake_claude

NO_WORK_NEED = (
    "The round left no uncommitted work to keep (what it committed and pushed, if anything, "
    "is on the branch) and no gate judged it. Review it and answer what it asks, if anything, "
    "then start the next round (a review, an @claude comment or sdlc:reset-iterations); that "
    "round's gate judges the whole branch."
)
COMMIT_EDITS = (
    gaps.EDITS
    + "import subprocess\n"
    + "subprocess.run(['git', 'add', 'src'], check=True)\n"
    + 'message = "fix: the session\'s own commit"\n'
    + "subprocess.run(['git', 'commit', '-q', '-m', message], check=True)\n"
)
WRITE_DEFERRED = (
    "import json, pathlib\n"
    "path = pathlib.Path('changes/0001-percent-helper/evidence/gate-c.json')\n"
    f"path.write_text({json.dumps(json.dumps(DEFERRED_GATE_FILE))}, encoding='utf-8')\n"
)


# --- item 2: an unfinished round parks even when nothing is left uncommitted ------------------
def test_a_failed_session_that_committed_its_work_itself_still_parks(
    project, fake_claude, monkeypatch, tmp_path, capsys
):
    """Round 3 of change 0005: the session committed its code, then hit the turn cap; the PR
    kept its old label over commits no gate judged."""
    root, change, args, env, calls = gaps._owner_round(
        project, fake_claude, monkeypatch, tmp_path, COMMIT_EDITS, gaps.MAX_TURNS
    )
    assert run_phase.run_phase(args, env) == run_phase.EXIT_FAILED
    out = json.loads(capsys.readouterr().out)
    reason = "fix: the round ended before its gate (claude exited 0, error_max_turns)"
    assert status_mod.read_status(change).parked_reason == reason
    assert out["parked"] == reason and out["work"]["kept"] == []
    [check] = gaps._gate_c(change)["checks"]
    assert check["name"] == "fix" and check["need"] == NO_WORK_NEED
    assert gaps._gate_c(change)["label"] == c.NEEDS_HUMAN_LABEL
    assert git(root, "log", "-2", "--format=%s").splitlines() == [
        "run(fix): failed run record",
        "fix: the session's own commit",
    ]
    assert any(argv[:1] == ["upsert"] and "--head" in argv for _s, argv in calls)


def test_a_deferred_record_the_failed_session_pushed_folds_into_the_one_park(
    project, fake_claude, monkeypatch, tmp_path, capsys
):
    """The session's gate wrote a deferred record, then the session failed with nothing
    uncommitted: one park, the gap-3 one, never the deferred-record park."""
    root, change, args, env, _calls = gaps._owner_round(
        project, fake_claude, monkeypatch, tmp_path, WRITE_DEFERRED, gaps.MAX_TURNS
    )
    assert run_phase.run_phase(args, env) == run_phase.EXIT_FAILED
    out = json.loads(capsys.readouterr().out)
    reason = "fix: the session failed after its gate (claude exited 0, error_max_turns)"
    assert out["parked"] == reason
    assert status_mod.read_status(change).parked_reason == reason
    record = gaps._gate_c(change)
    assert [ch["name"] for ch in record["checks"] if not ch["ok"]] == ["fix"]
    assert record["result"] == "park" and record["label"] == c.NEEDS_HUMAN_LABEL


# --- item 8: a session that failed after its gate says so --------------------------------------
def test_a_session_that_failed_after_its_gate_keeps_its_work_under_that_reason(
    project, fake_claude, monkeypatch, tmp_path, capsys
):
    root, change, args, env, _calls = gaps._owner_round(
        project, fake_claude, monkeypatch, tmp_path, gaps.EDITS, gaps.MAX_TURNS
    )
    env["FAKE_CLAUDE_GATE"] = "changes/0001-percent-helper/evidence/gate-c.json"
    assert run_phase.run_phase(args, env) == run_phase.EXIT_FAILED
    capsys.readouterr()
    sha = git(root, "rev-parse", "HEAD").strip()
    assert status_mod.read_status(change).parked_reason == (
        "fix: the session failed after its gate (claude exited 0, error_max_turns); its work "
        f"is kept in {sha[:10]}, not gated"
    )


# --- item 5: the restart's merge runs on the branch's committed tree ---------------------------
def _restart_after_main_fixes_claude_md(project, tmp_path, fake_claude, monkeypatch, capsys):
    """The build parked at the preflight; the owner fixes CLAUDE.md on main; a fresh runner
    has main only. Returns what ``_build_parked_at_the_preflight`` returns."""
    parked = gaps._build_parked_at_the_preflight(
        project, tmp_path, fake_claude, monkeypatch, capsys
    )
    root, _change, _bare, lint, _args, _env = parked
    fixed = (root / "CLAUDE.md").read_text(encoding="utf-8").replace("ruff", lint)
    git(root, "checkout", "-q", "main")
    git(root, "branch", "-q", "-D", "sdlc/0001/c")
    gaps._owner_commits_on_main(root, "CLAUDE.md", fixed, "CLAUDE.md names the lint command")
    return parked


def test_a_restart_merges_a_default_branch_that_changed_the_change_s_status(
    project, tmp_path, fake_claude, monkeypatch, capsys
):
    """The owner set an override in the change's status.yaml on main: the guard's write (the
    park cleared) used to make git refuse the merge ("local changes would be overwritten"),
    and the change parked again with the reason "Aborting"."""
    root, change, _bare, _lint, args, env = _restart_after_main_fixes_claude_md(
        project, tmp_path, fake_claude, monkeypatch, capsys
    )
    st = status_mod.read_status(change)
    st.review_override = "deferred"
    status_mod.write_status(change, st)
    git(root, "commit", "-q", "-am", "owner: review deferred for change 0001")
    git(root, "push", "-q", "origin", "main")
    gaps._pr_upsert_only(monkeypatch, 7)
    assert run_phase.run_phase(args, env) == run_phase.EXIT_OK
    out = json.loads(capsys.readouterr().out)
    assert "parked" not in out and "skipped" not in out, out
    assert (change / "evidence" / "claude-c.json").exists()  # the session ran
    merges = git(root, "log", "--merges", "--format=%s", "HEAD").splitlines()
    assert merges == ["run(c): origin/main merged before the restarted preflight (gap 2)"]
    st = status_mod.read_status(change)
    assert st.phase == "c" and st.parked_reason is None
    assert st.review_override == "deferred"  # the owner's override is kept


def test_a_stacked_build_restarts_after_its_design_was_squash_merged(
    project, tmp_path, fake_claude, monkeypatch, capsys
):
    """A build branch cut from the design branch, not from main (a fast-lane build, decision
    30), parked at the preflight; the owner then squash-merged the design PR and fixed
    CLAUDE.md on main. Both sides added the change's status.yaml (main's copy says phase b):
    the conflict in that one file is settled with the branch's record, and the restart
    runs."""
    root, change = project
    rel = "changes/0001-percent-helper"
    lint = gaps._lint_command(root)
    claude_md = (root / "CLAUDE.md").read_text(encoding="utf-8")
    (root / "CLAUDE.md").write_text(claude_md.replace(lint, "ruff"), encoding="utf-8")
    set_state(change, "b", gate_phase="b", gate_result="passed")
    bare = tmp_path / "remote.git"
    git(tmp_path, "init", "-q", "--bare", "-b", "main", str(bare))
    git(root, "remote", "add", "origin", str(bare))
    git(root, "add", "-A")
    git(root, "reset", "-q", "--", rel)  # main before the design: no change folder yet
    git(root, "commit", "-q", "-m", "sdlc-init")
    git(root, "push", "-q", "-u", "origin", "main")
    git(root, "checkout", "-q", "-b", "sdlc/0001/b")
    git(root, "add", rel)
    git(root, "commit", "-q", "-m", "design(0001): spec and plan")
    git(root, "checkout", "-q", "-b", "sdlc/0001/c")  # stacked on the design
    gaps._preflight_park(root, change)
    git(root, "add", rel)
    git(root, "commit", "-q", "-m", "run(c): parked at the preflight")
    git(root, "push", "-q", "-u", "origin", "sdlc/0001/c")
    git(root, "checkout", "-q", "main")
    git(root, "merge", "-q", "--squash", "sdlc/0001/b")
    git(root, "commit", "-q", "-m", "design(0001) (squash merge)")
    gaps._owner_commits_on_main(root, "CLAUDE.md", claude_md, "CLAUDE.md names the lint command")
    git(root, "branch", "-q", "-D", "sdlc/0001/c", "sdlc/0001/b")  # a fresh runner has main
    gaps._pr_upsert_only(monkeypatch, 7)
    session = tmp_path / "session.py"
    write(
        session,
        "import json, pathlib\n"
        "path = pathlib.Path('changes/0001-percent-helper/evidence/gate-c.json')\n"
        f"path.write_text({json.dumps(json.dumps({**GATE_FILE, 'phase': 'c'}))})\n",
    )
    monkeypatch.setenv("FAKE_CLAUDE_RUN", str(session))
    monkeypatch.setenv("FAKE_CLAUDE_RESULT", json.dumps(FAKE_RESULT))
    args = Args(
        root=str(root), phase="c", dry_run=False, no_dispatch=True, claude=fake_cli(fake_claude)
    )
    env = dict(os.environ, **KEY_ENV, GITHUB_TOKEN=FAKE_TOKEN)
    assert run_phase.run_phase(args, env) == run_phase.EXIT_OK
    out = json.loads(capsys.readouterr().out)
    assert "parked" not in out and "skipped" not in out, out
    assert (change / "evidence" / "claude-c.json").exists()  # the session ran
    merges = git(root, "log", "--merges", "--format=%s", "HEAD").splitlines()
    assert merges == ["run(c): origin/main merged before the restarted preflight (gap 2)"]
    assert git(root, "merge-base", "--is-ancestor", "origin/main", "HEAD") == ""
    assert not (root / ".git" / "MERGE_HEAD").exists()
    st = status_mod.read_status(change)
    assert st.phase == "c" and st.parked_reason is None


def test_a_file_the_merge_would_overwrite_is_named_as_the_conflict(
    project, tmp_path, fake_claude, monkeypatch, capsys
):
    root, change, _bare, _lint, args, env = _restart_after_main_fixes_claude_md(
        project, tmp_path, fake_claude, monkeypatch, capsys
    )
    write(root / "notes.txt", "main's notes\n")
    git(root, "add", "notes.txt")
    git(root, "commit", "-q", "-m", "main adds notes.txt")
    git(root, "push", "-q", "origin", "main")
    real = run_phase.install_toolchain

    def setup(where, dry_run):  # the setup step leaves a file main tracks, untracked here
        write(Path(where) / "notes.txt", "left by the setup step\n")
        return real(where, dry_run)

    monkeypatch.setattr(run_phase, "install_toolchain", setup)
    gaps._pr_upsert_only(monkeypatch, 7)
    assert run_phase.run_phase(args, env) == run_phase.EXIT_OK
    out = json.loads(capsys.readouterr().out)
    assert out["parked"] == (
        "preflight: the default branch does not merge into sdlc/0001/c: notes.txt"
    )
    assert not (root / ".git" / "MERGE_HEAD").exists()


# --- item 7: a dry run merges nothing ---------------------------------------------------------
def test_a_dry_run_of_a_restart_merges_nothing(project, tmp_path, fake_claude, monkeypatch, capsys):
    root, _change, bare, _lint, args, env = _restart_after_main_fixes_claude_md(
        project, tmp_path, fake_claude, monkeypatch, capsys
    )
    gaps._pr_upsert_only(monkeypatch, 7)
    args.dry_run = True
    assert run_phase.run_phase(args, env) == run_phase.EXIT_OK
    out = json.loads(capsys.readouterr().out)
    assert out["merged"] is None  # the restart's merge is skipped
    assert git(root, "log", "--merges", "--format=%s", "HEAD") == ""
    assert git(root, "rev-parse", "HEAD") == git(bare, "rev-parse", "sdlc/0001/c")


# --- item 3: a round with nothing to do never starts a session --------------------------------
NOTHING_TO_DO = (
    "the fix round has nothing to do: no owner label performed, no request to apply in "
    "evidence/fix-requests.json, and the change is not parked"
)


def _ready_round(project, fake_claude, monkeypatch, tmp_path, requests: list):
    """An owner round on a build PR whose gate passed (not parked): the requests file holds
    ``requests``."""
    root, change, args, env, calls = gaps._owner_round(
        project, fake_claude, monkeypatch, tmp_path, gaps.EDITS, gaps.QUESTION
    )
    set_state(change, "c", gate_phase="c", gate_result="passed")
    git(root, "commit", "-q", "-am", "gate (c) passed")

    def collect(root, change_dir, *a, **k):
        from ci import fix_requests

        fix_requests.write(
            change_dir,
            {"schema_version": 1, "ok": True, "requests": requests, "not_applied": []},
        )
        return {"ok": True, "requests": len(requests)}

    monkeypatch.setattr(run_phase, "collect_fix_requests", collect)
    return root, change, args, env, calls


@pytest.mark.parametrize("applied", [False, True], ids=["no-request", "all-applied"])
def test_a_fix_round_with_nothing_to_do_is_skipped_before_the_session(
    project, fake_claude, monkeypatch, tmp_path, capsys, applied
):
    """A queued second run of a round, or an @claude comment already applied: the session
    used to end without a gate record and park a ready PR."""
    done = {"kind": "comment", "id": 5, "author": "luissiviero", "applied": True}
    root, change, args, env, calls = _ready_round(
        project, fake_claude, monkeypatch, tmp_path, [done] if applied else []
    )
    head = git(root, "rev-parse", "HEAD").strip()
    record = (change / "evidence" / "gate-c.json").read_bytes()
    assert run_phase.run_phase(args, env) == run_phase.EXIT_OK
    assert json.loads(capsys.readouterr().out) == {"skipped": NOTHING_TO_DO}
    assert not (change / "evidence" / "claude-fix.json").exists()  # no session
    assert (change / "evidence" / "gate-c.json").read_bytes() == record
    assert status_mod.read_status(change).parked_reason is None
    assert git(root, "rev-parse", "HEAD").strip() == head and calls == []


def test_a_fix_round_with_a_request_left_to_apply_runs(
    project, fake_claude, monkeypatch, tmp_path, capsys
):
    pending = {"kind": "comment", "id": 6, "author": "luissiviero", "body": "rename x"}
    _root, change, args, env, _calls = _ready_round(
        project, fake_claude, monkeypatch, tmp_path, [pending]
    )
    run_phase.run_phase(args, env)
    assert "skipped" not in json.loads(capsys.readouterr().out)
    assert (change / "evidence" / "claude-fix.json").exists()  # the session ran


def _label_event(tmp_path, sender: str):
    payload = {
        "action": "labeled",
        "label": {"name": c.RESET_ITERATIONS_LABEL},
        "sender": {"login": sender},
        "pull_request": {"number": 7, "head": {"ref": "sdlc/0001/b"}},
    }
    path = tmp_path / f"label-{sender}.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_the_find_step_refuses_a_label_another_account_applied(project, tmp_path, capsys):
    """Choice 218: a label nobody but the owner may apply never starts a paid round."""
    root, _change = project
    for sender, found in (("colleague", ""), ("LuisSiviero", "0001")):
        env = {
            **owner_rounds.OWNER_ENV,
            "GITHUB_EVENT_NAME": "pull_request",
            "GITHUB_EVENT_PATH": str(_label_event(tmp_path, sender)),
        }
        code, printed, output = owner_rounds._find(root, tmp_path, env, capsys)
        assert code == run_phase.EXIT_OK and output == f"change_id={found}\n", sender
    assert (
        "the label was applied by colleague, not the owner's account (choice 218)"
        in (
            owner_rounds._find(
                root,
                tmp_path,
                {**env, "GITHUB_EVENT_PATH": str(_label_event(tmp_path, "colleague"))},
                capsys,
            )[1]
        )
    )
    # on a runner a payload that cannot be read refuses (fail closed)
    env = {**owner_rounds.OWNER_ENV, "GITHUB_ACTIONS": "true", "GITHUB_EVENT_NAME": "pull_request"}
    code, printed, output = owner_rounds._find(root, tmp_path, env, capsys)
    assert output == "change_id=\n" and "the label event's payload could not be read" in printed


# --- item 4: an undecided session ends its turn with the question, it never parks -------------
def test_sdlc_fix_tells_an_undecided_session_to_end_with_its_question():
    text = " ".join((ci_tests.ROOT / "plugin" / "commands" / "sdlc-fix.md").read_text().split())
    start = text.index("Unattended: never ask the owner a question.")
    unattended = text[start : text.index("One shell command per Bash call", start)]
    assert "state/cli.py park" not in unattended
    assert (
        'When you cannot decide, write the question under "What I need from you" in '
        "`evidence/fix-response.md`, commit and push your work, and end the turn without "
        "running the gate, the question as your last message."
    ) in unattended
    assert "it never waits for an answer" in unattended
    assert (
        "In CI such a round never starts: the runner skips it before the session when it "
        "performed no owner label, `evidence/fix-requests.json` holds no request left to apply"
    ) in text


# --- item 6: the kept work leaves out a nested .claude/'s settings and hooks -------------------
def test_a_nested_claude_settings_file_is_a_guardrail_path():
    files = ["pkg/.claude/settings.json", "pkg/.claude/hooks/x.py", "pkg/.claude/notes.md"]
    assert run_phase.guardrail_hits(files, {}) == [
        "pkg/.claude/hooks/x.py",
        "pkg/.claude/settings.json",
    ]


def test_a_nested_claude_settings_file_stays_out_of_the_kept_work(
    project, fake_claude, monkeypatch, tmp_path, capsys
):
    nested = (
        "pathlib.Path('pkg/.claude').mkdir(parents=True)\n"
        "pathlib.Path('pkg/.claude/settings.json').write_text('{}\\n', encoding='utf-8')\n"
    )
    root, _change, args, env, _calls = gaps._owner_round(
        project, fake_claude, monkeypatch, tmp_path, gaps.EDITS + nested, gaps.MAX_TURNS
    )
    assert run_phase.run_phase(args, env) == run_phase.EXIT_FAILED
    out = json.loads(capsys.readouterr().out)
    assert out["work"]["left_out"] == ["pkg/.claude/settings.json"]
    assert "pkg/.claude/settings.json" not in gaps._committed(root)
