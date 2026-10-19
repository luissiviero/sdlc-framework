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

from ci import run_phase

from state import conventions as c
from state import status as status_mod
from tests import test_ci as ci_tests
from tests import test_fix_round_gaps as gaps
from tests.test_ci import DEFERRED_GATE_FILE, git

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
