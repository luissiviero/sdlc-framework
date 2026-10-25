"""Plugin 1.0.10: the fix-round robustness of NOTES §45, gaps 2, 3 and 4, and choice 218.

- gap 2 (choices 228, 229): a build parked at the runner's preflight before any session is
  started again by a dispatch of SDLC build while its pull request is open; the restart
  merges the default branch into the work branch before the preflight;
- gap 3 (choice 230): a fix round that ends before its gate keeps the session's uncommitted
  work in one commit on the PR's head, not gated, and parks;
- gap 4 (choice 231): a fix session that exits 0 without writing this round's gate record is
  parked with its last message, never handed over on the previous record, and no unattended
  session may ask a question;
- choice 218: the un-park labels count only from the owner's account.

The GitHub calls are replaced by fakes, as ``tests/test_ci.py`` does: no network, no token.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from ci import run_phase

from state import conventions as c
from state import status as status_mod
from state import unpark
from tests import test_auto_round as auto_tests
from tests import test_ci as ci_tests
from tests.test_ci import (
    FAKE_RESULT,
    FAKE_TOKEN,
    GATE_FILE,
    KEY_ENV,
    ROOT,
    Args,
    fake_cli,
    git,
    pr_route,
    set_state,
    skip_reason,
    with_remote,
    write,
)

# the fixtures of tests/test_ci.py, used here by name
project = ci_tests.project
fake_claude = ci_tests.fake_claude

PREFLIGHT_REASON = "claude_md: CLAUDE.md does not name the lint command of sdlc.yaml"


# --- gap 2: a build parked at the runner's preflight starts again ------------------------------
def _preflight_park(root: Path, change: Path, reason: str = PREFLIGHT_REASON) -> None:
    """The change as the runner's preflight park leaves it (``park_and_publish``)."""
    st = status_mod.read_status(change)
    st.set_phase("build")
    st.park("preflight: " + reason)
    status_mod.write_status(change, st)
    run_phase.write_park_result(root, change, st, "build", "preflight", reason)


def test_an_open_pr_does_not_stop_the_restart_of_a_pre_run_preflight_park(project, monkeypatch):
    root, change = project
    _preflight_park(root, change)
    ci_tests._pr_lookup(monkeypatch, 12)
    assert run_phase.rerun_reason(root, "0001", "build", "owner/name", {}) is None
    assert run_phase.pre_run_park(root, "0001", "build") is True
    # the guard clears the park and puts back the passed gate (design) the preflight followed;
    # the run writes it only after the restart's merge (restart_record), so the guard
    # leaves the committed tree clean
    _dir, st, _cfg, reason = run_phase.guard(root, "0001", "build", "owner/name", {})
    assert reason is None
    assert st.phase == "build" and st.parked_reason is None
    assert (st.gate.phase, st.gate.result) == ("design", "passed")
    assert status_mod.read_status(change).parked_reason.startswith("preflight: ")
    st = run_phase.restart_record(change, "build")
    assert st.phase == "build" and st.parked_reason is None
    assert (st.gate.phase, st.gate.result) == ("design", "passed")
    assert status_mod.read_status(change).parked_reason is None
    # a fix round and the other phases are untouched
    assert run_phase.pre_run_park(root, "0001", "fix") is False


def test_a_preflight_park_after_a_session_is_not_a_restart(project, monkeypatch):
    root, change = project
    _preflight_park(root, change)
    write(change / "evidence" / "claude-build.json", json.dumps(FAKE_RESULT))
    ci_tests._pr_lookup(monkeypatch, 12)
    assert run_phase.pre_run_park(root, "0001", "build") is False
    reason = run_phase.rerun_reason(root, "0001", "build", "owner/name", {})
    assert reason == (
        "change 0001 is already at phase build on sdlc/0001/build; pull request #12 carries it "
        "(review comments go through /sdlc-fix, not a second run)"
    )
    # a fix round's record the branch added counts as a session too
    (change / "evidence" / "claude-build.json").unlink()
    git(root, "add", ".")
    git(root, "commit", "-q", "-m", "the branch so far")
    git(root, "checkout", "-q", "-b", "sdlc/0001/build")
    write(change / "evidence" / "claude-fix-2.json", json.dumps(FAKE_RESULT))
    assert run_phase.pre_run_park(root, "0001", "build") is False
    # one the merge base already carries (a fix round of the design) does not
    git(root, "checkout", "-q", "main")
    git(root, "add", ".")
    git(root, "commit", "-q", "-m", "a fix round at (b)")
    git(root, "checkout", "-q", "sdlc/0001/build")
    git(root, "merge", "-q", "main")
    assert run_phase.pre_run_park(root, "0001", "build") is True


def test_a_park_that_is_not_the_preflight_s_is_refused_with_its_pr_open(project, monkeypatch):
    root, change = project
    ci_tests._pr_lookup(monkeypatch, 12)
    for check, reason in (
        ("limits", "budget reached: 150.00 USD spent on the change"),
        ("guardrails", "guardrail file changed on the branch: CLAUDE.md"),
    ):
        st = status_mod.read_status(change)
        st.set_phase("build")
        st.park(f"{check}: {reason}")
        status_mod.write_status(change, st)
        run_phase.write_park_result(root, change, st, "build", check, reason)
        assert run_phase.pre_run_park(root, "0001", "build") is False
        assert "pull request #12 carries it" in skip_reason(root, "build")
    # a preflight reason over a record whose failed check is another one is refused too
    _preflight_park(root, change)
    run_phase.write_park_result(
        root, change, status_mod.read_status(change), "build", "limits", "x"
    )
    assert "pull request #12 carries it" in skip_reason(root, "build")


def _pr_upsert_only(monkeypatch, number: int | None) -> list:
    """The PR is answered by fakes; every other plugin CLI really runs (the park commits)."""
    from pr import github

    monkeypatch.setattr(github, "gh_path", lambda: None)
    monkeypatch.setattr(
        github, "find_open_pr", lambda repo, head, cwd=None: {"ok": True, "number": number}
    )
    monkeypatch.setattr(run_phase, "ensure_labels", lambda repo, env: {"ensured": 0})
    real = run_phase._cli_call
    upserts: list = []

    def cli(script, argv, timeout=600, env=None):
        if Path(script).parent.name == "pr":
            upserts.append(list(argv))
            answer = {"route": "api", "number": 7, "url": "https://github.test/o/r/pull/7"}
            return {"ok": True, "reason": "", "output": answer}
        return real(script, argv, timeout, env)

    monkeypatch.setattr(run_phase, "_cli_call", cli)
    return upserts


def _lint_command(root: Path) -> str:
    text = (root / "sdlc.yaml").read_text(encoding="utf-8")
    line = next(ln for ln in text.splitlines() if ln.strip().startswith("lint:"))
    return line.split(":", 1)[1].strip().strip('"')


def _build_parked_at_the_preflight(project, tmp_path, fake_claude, monkeypatch, capsys):
    """The first build of change 0001 parks at the preflight: CLAUDE.md on main lacks the
    lint command of sdlc.yaml (change 0005's build, NOTES §45). Returns the run's args."""
    root, change = project
    lint = _lint_command(root)
    claude_md = (root / "CLAUDE.md").read_text(encoding="utf-8")
    assert lint in claude_md
    (root / "CLAUDE.md").write_text(claude_md.replace(lint, "ruff"), encoding="utf-8")
    set_state(change, "design", gate_phase="design", gate_result="passed")
    bare = with_remote(root, tmp_path)
    _pr_upsert_only(monkeypatch, None)
    session = tmp_path / "session.py"
    write(
        session,
        "import json, pathlib\n"
        "path = pathlib.Path('changes/0001-percent-helper/evidence/gate-build.json')\n"
        f"path.write_text({json.dumps(json.dumps({**GATE_FILE, 'phase': 'build'}))})\n",
    )
    monkeypatch.setenv("FAKE_CLAUDE_RUN", str(session))
    monkeypatch.setenv("FAKE_CLAUDE_RESULT", json.dumps(FAKE_RESULT))
    args = Args(
        root=str(root), phase="build", dry_run=False, no_dispatch=True, claude=fake_cli(fake_claude)
    )
    env = dict(os.environ, **KEY_ENV, GITHUB_TOKEN=FAKE_TOKEN)
    assert run_phase.run_phase(args, env) == run_phase.EXIT_OK
    out = json.loads(capsys.readouterr().out)
    assert out["parked"] == [PREFLIGHT_REASON]
    assert not (change / "evidence" / "claude-build.json").exists()  # no session ran
    record = json.loads((change / "evidence" / "gate-build.json").read_text(encoding="utf-8"))
    [check] = record["checks"]
    assert check["need"] == (
        "Settle this on the default branch, then dispatch SDLC build (Actions → SDLC build → "
        "Run workflow) with change id 0001: the runner merges the default branch into "
        "sdlc/0001/build and runs the preflight again."
    )
    assert "sdlc/0001/build" in git(bare, "branch", "--list", "sdlc/0001/build")
    return root, change, bare, lint, args, env


def _owner_commits_on_main(root: Path, path: str, text: str, message: str) -> None:
    """The owner's reviewed PR merged on main; the dispatched runner checks out main."""
    git(root, "checkout", "-q", "main")
    (root / path).write_text(text, encoding="utf-8")
    git(root, "commit", "-q", "-am", message)
    git(root, "push", "-q", "origin", "main")


def test_a_build_parked_at_the_preflight_restarts_on_the_owner_s_fix_from_main(
    project, tmp_path, fake_claude, monkeypatch, capsys
):
    """End to end: the first build parks at the preflight and opens its PR; the owner fixes
    CLAUDE.md on main; a second dispatch with the PR open merges main into the branch (a
    merge commit, not a guardrail park: the fix is main's, not the branch's), passes the
    preflight and starts the session."""
    root, change, bare, lint, args, env = _build_parked_at_the_preflight(
        project, tmp_path, fake_claude, monkeypatch, capsys
    )
    fixed = (root / "CLAUDE.md").read_text(encoding="utf-8").replace("ruff", lint)
    git(root, "checkout", "-q", "main")
    git(root, "branch", "-q", "-D", "sdlc/0001/build")  # a fresh runner has main only
    _owner_commits_on_main(root, "CLAUDE.md", fixed, "CLAUDE.md names the lint command")
    upserts = _pr_upsert_only(monkeypatch, 7)  # the build PR is open now
    assert run_phase.run_phase(args, env) == run_phase.EXIT_OK
    out = json.loads(capsys.readouterr().out)
    assert "parked" not in out and "skipped" not in out, out
    assert (change / "evidence" / "claude-build.json").exists()  # the session ran
    assert git(root, "rev-parse", "--abbrev-ref", "HEAD").strip() == "sdlc/0001/build"
    merges = git(root, "log", "--merges", "--format=%s", "HEAD").splitlines()
    assert merges == ["run(build): origin/main merged before the restarted preflight (gap 2)"]
    assert git(root, "merge-base", "--is-ancestor", "origin/main", "HEAD") == ""
    assert lint in (root / "CLAUDE.md").read_text(encoding="utf-8")
    assert status_mod.read_status(change).parked_reason is None
    assert any(argv[0] == "upsert" for argv in upserts)
    # the merge commit reached the branch on origin with the run's own push
    assert git(bare, "merge-base", "--is-ancestor", "main", "sdlc/0001/build") == ""


def test_a_restart_whose_merge_conflicts_parks_again_and_leaves_no_merge(
    project, tmp_path, fake_claude, monkeypatch, capsys
):
    root, change, _bare, _lint, args, env = _build_parked_at_the_preflight(
        project, tmp_path, fake_claude, monkeypatch, capsys
    )
    calc = "sample_pkg/calc.py"
    original = (root / calc).read_text(encoding="utf-8")
    # the branch and main change the same lines
    (root / calc).write_text(original + "\nBRANCH = 1\n", encoding="utf-8")
    git(root, "commit", "-q", "-am", "a commit on the build branch")
    git(root, "push", "-q", "origin", "sdlc/0001/build")
    _owner_commits_on_main(root, calc, original + "\nMAIN = 2\n", "main moves on")
    _pr_upsert_only(monkeypatch, 7)
    head = git(root, "rev-parse", "sdlc/0001/build").strip()
    assert run_phase.run_phase(args, env) == run_phase.EXIT_OK
    out = json.loads(capsys.readouterr().out)
    expected = f"preflight: the default branch does not merge into sdlc/0001/build: {calc}"
    assert out["parked"] == expected and out["merged"]["conflicts"] == [calc]
    assert not (root / ".git" / "MERGE_HEAD").exists()
    assert git(root, "status", "--porcelain", "--", calc) == ""
    assert git(root, "log", "--merges", "--format=%s", "HEAD") == ""
    assert git(root, "rev-parse", "HEAD~1").strip() == head  # only the park's commit
    st = status_mod.read_status(change)
    assert st.parked_reason == expected
    record = json.loads((change / "evidence" / "gate-build.json").read_text(encoding="utf-8"))
    assert '"Update branch"' in record["checks"][0]["need"]
    # the park is a pre-run preflight park again: the next dispatch may restart it
    assert run_phase.pre_run_park(root, "0001", "build") is True


# --- gaps 3 and 4: an unfinished fix round keeps its work and parks ----------------------------
MAX_TURNS = {"is_error": True, "subtype": "error_max_turns", "total_cost_usd": 1.5, "result": ""}
# a failed session that no outer bound stopped: since R25 part 1 (plugin 1.0.26) the turn limit
# parks green, so the gap-3 tests of a failed round use this one
FAILED_RUN = {**MAX_TURNS, "subtype": "error_during_execution"}
QUESTION = {"is_error": False, "total_cost_usd": 0.4, "result": "How would you like me to proceed?"}
EDITS = (
    "import pathlib\n"
    "pathlib.Path('src/x.py').write_text('X = 2\\n', encoding='utf-8')\n"
    "pathlib.Path('src/new.py').write_text('NEW = 1\\n', encoding='utf-8')\n"
)
GUARDRAIL_EDITS = (
    "pathlib.Path('CLAUDE.md').write_text('# rewritten\\n', encoding='utf-8')\n"
    "pathlib.Path('.env.local').write_text('TOKEN=x\\n', encoding='utf-8')\n"
)


def _owner_round(project, fake_claude, monkeypatch, tmp_path, script: str, result: dict):
    """The owner's fix round on the build PR (sdlc/0001/build, #7): the session runs ``script``
    and ends with ``result``."""
    root, change = project
    calls = pr_route(monkeypatch)
    monkeypatch.setattr(run_phase, "ensure_labels", lambda repo, env: {"ensured": 0})
    monkeypatch.setattr(run_phase, "apply_owner_labels", lambda *a, **k: {"ok": True})
    monkeypatch.setattr(run_phase, "collect_fix_requests", lambda *a, **k: {"ok": True})
    monkeypatch.setattr(run_phase, "take_red_targets", lambda *a, **k: {})
    write(root / "src" / "x.py", "X = 1\n")
    set_state(
        change, "build", gate_phase="build", gate_result="parked", parked="commands: not green"
    )
    write(change / "evidence" / "gate-build.json", json.dumps({**GATE_FILE, "phase": "build"}))
    git(root, "add", ".")
    git(root, "commit", "-q", "-m", "the build so far")
    git(root, "checkout", "-q", "-b", "sdlc/0001/build")
    session = tmp_path / "session.py"
    write(session, script)
    env = dict(
        os.environ, **KEY_ENV, GITHUB_TOKEN=FAKE_TOKEN,
        FAKE_CLAUDE_RUN=str(session), FAKE_CLAUDE_RESULT=json.dumps(result),
    )  # fmt: skip
    args = Args(
        root=str(root), phase="fix", head_ref="sdlc/0001/build", pr_number="7", dry_run=False,
        no_dispatch=True, claude=fake_cli(fake_claude),
    )  # fmt: skip
    return root, change, args, env, calls


def _gate_c(change: Path) -> dict:
    return json.loads((change / "evidence" / "gate-build.json").read_text(encoding="utf-8"))


def _committed(root: Path, ref: str = "HEAD") -> list[str]:
    return git(root, "show", "--name-only", "--format=", ref).split()


def test_a_fix_session_at_the_turn_cap_keeps_its_work_on_the_pr_head_and_parks(
    project, fake_claude, monkeypatch, tmp_path, capsys
):
    root, change, args, env, calls = _owner_round(
        project, fake_claude, monkeypatch, tmp_path, EDITS, MAX_TURNS
    )
    # R25 part 1 (plugin 1.0.26): an outer bound parks green and names itself; before, a
    # red run with "claude exited 0, error_max_turns"
    assert run_phase.run_phase(args, env) == run_phase.EXIT_OK
    out = json.loads(capsys.readouterr().out)
    sha = git(root, "rev-parse", "HEAD").strip()
    message = git(root, "log", "-1", "--format=%s").strip()
    assert message == (
        "run(fix): unfinished round's work kept, not gated (gap 3): stopped at the turn limit"
    )
    files = _committed(root)
    assert "src/x.py" in files and "src/new.py" in files
    assert "changes/0001-percent-helper/evidence/claude-fix.json" in files
    assert git(root, "status", "--porcelain", "--", "src") == ""
    reason = status_mod.read_status(change).parked_reason
    assert reason == (
        "fix: the round ended before its gate (stopped at the turn limit); its work is "
        f"kept in {sha[:10]}, not gated"
    )
    assert out["parked"] == reason and out["work"]["kept"] == ["src/new.py", "src/x.py"]
    record = _gate_c(change)
    assert record["label"] == c.NEEDS_HUMAN_LABEL and [ch["name"] for ch in record["checks"]] == [
        "fix"
    ]
    assert record["checks"][0]["need"] == (
        "The round's uncommitted work is committed on the branch but no gate judged it. Review "
        "it, then start the next round (a review, an @claude comment or sdlc:reset-iterations); "
        "that round's gate judges the whole branch."
    )
    assert any(argv[:1] == ["upsert"] and "--head" in argv for _s, argv in calls)


def test_guardrail_and_env_files_stay_out_of_the_kept_work_and_are_named(
    project, fake_claude, monkeypatch, tmp_path, capsys
):
    root, change, args, env, _calls = _owner_round(
        project, fake_claude, monkeypatch, tmp_path, EDITS + GUARDRAIL_EDITS, FAILED_RUN
    )
    assert run_phase.run_phase(args, env) == run_phase.EXIT_FAILED
    out = json.loads(capsys.readouterr().out)
    files = _committed(root)
    assert "src/x.py" in files and "CLAUDE.md" not in files and ".env.local" not in files
    assert out["work"]["left_out"] == [".env.local", "CLAUDE.md"]
    assert status_mod.read_status(change).parked_reason.endswith(
        "not gated; left out of the commit: .env.local, CLAUDE.md"
    )
    left = git(root, "status", "--porcelain", "--", "CLAUDE.md", ".env.local")
    assert " M CLAUDE.md" in left and "?? .env.local" in left  # left uncommitted


def test_a_round_that_parks_on_the_owner_fields_keeps_no_work(
    project, fake_claude, monkeypatch, tmp_path, capsys
):
    """Today's behaviour stands: the owner-field park comes first, and its tree is not the
    owner's to keep (the session wrote a runner file)."""
    root, change, args, env, _calls = _owner_round(
        project, fake_claude, monkeypatch, tmp_path, EDITS + auto_tests.PLANT, FAILED_RUN
    )
    head = git(root, "rev-parse", "HEAD").strip()
    run_phase.run_phase(args, env)
    out = json.loads(capsys.readouterr().out)
    assert out["parked"].startswith(c.OWNER_FIELDS_PARK_PREFIX) and "work" not in out
    assert git(root, "rev-parse", "HEAD").strip() == head  # no work commit
    assert " M src/x.py" in git(root, "status", "--porcelain", "--", "src/x.py")


def test_an_automatic_round_that_ends_unfinished_parks_once_with_the_gap_3_reason(
    project, fake_claude, monkeypatch, tmp_path, capsys
):
    root, change, args, env, _seen = auto_tests.fix_run(project, fake_claude, monkeypatch, tmp_path)
    write(root / "src" / "x.py", "X = 1\n")
    git(root, "add", ".")
    git(root, "commit", "-q", "-m", "src/x.py")
    session = tmp_path / "session.py"
    write(session, EDITS)
    env.update(FAKE_CLAUDE_RUN=str(session), FAKE_CLAUDE_RESULT=json.dumps(FAILED_RUN))
    env.pop("FAKE_CLAUDE_GATE")  # the turn cap came before the round's gate
    auto_tests.dispatch_recorder(monkeypatch)
    assert run_phase.run_phase(args, env) == run_phase.EXIT_FAILED
    err = capsys.readouterr().err
    assert "the automatic fix round 1 did not finish" not in err
    record = _gate_c(change)
    assert record["label"] == c.NEEDS_HUMAN_LABEL
    assert [ch["name"] for ch in record["checks"] if not ch["ok"]] == ["fix"]
    reason = status_mod.read_status(change).parked_reason
    assert reason.startswith("fix: the round ended before its gate (claude exited 0")
    data = json.loads((change / "evidence" / c.AUTO_ROUND_FILE).read_text(encoding="utf-8"))
    assert data["status"] == "unfinished"
    assert "src/x.py" in _committed(root)
    # decision 29's release reads the label the park replaced: nothing to release again
    track = {"change_id": "0001", "change_dir": change, "gate_phase": "build"}
    assert run_phase.release_unfinished_round(args, env, track, 1) is None
    assert status_mod.read_status(change).parked_reason == reason


def _commands_recorder(monkeypatch) -> list:
    calls: list = []

    def fake(plugin_dir, root, change_id, phase, config, timeout=None):
        calls.append(phase)
        return {"ok": True, "output": {"ran": False}}

    monkeypatch.setattr(run_phase, "run_gate_commands", fake)
    return calls


def test_a_fix_session_that_ends_with_a_question_parks_with_it(
    project, fake_claude, monkeypatch, tmp_path, capsys
):
    """Round 5 of change 0005: the session ended "successfully" with a question and the
    runner handed the round over on the previous round's gate record."""
    root, change, args, env, _calls = _owner_round(
        project, fake_claude, monkeypatch, tmp_path, "", QUESTION
    )
    commands = _commands_recorder(monkeypatch)
    sent = auto_tests.dispatch_recorder(monkeypatch)
    assert run_phase.run_phase(args, env) == run_phase.EXIT_FAILED
    out = json.loads(capsys.readouterr().out)
    assert commands == [] and sent == [] and "dispatched" not in out
    reason = status_mod.read_status(change).parked_reason
    assert reason == "fix: the session ended without reaching its gate"
    [check] = _gate_c(change)["checks"]
    assert check["name"] == "fix" and check["need"].startswith(
        "The round left no uncommitted work to keep (what it committed and pushed, if anything, "
        "is on the branch) and no gate judged it. Review it and answer what it asks, if anything, "
        "then start the next round (a review, an @claude comment or sdlc:reset-iterations); that "
        "round's gate judges the whole branch."
    )
    assert "The session stopped with:" in check["need"]
    assert "    > How would you like me to proceed?" in check["need"]
    assert git(root, "log", "-1", "--format=%s").strip() == "run(fix): failed run record"


def test_a_fix_session_that_writes_its_gate_record_proceeds_as_before(
    project, fake_claude, monkeypatch, tmp_path, capsys
):
    root, change, args, env, _calls = _owner_round(
        project, fake_claude, monkeypatch, tmp_path, "", FAKE_RESULT
    )
    env["FAKE_CLAUDE_GATE"] = "changes/0001-percent-helper/evidence/gate-build.json"
    commands = _commands_recorder(monkeypatch)
    assert run_phase.run_phase(args, env) == run_phase.EXIT_OK
    out = json.loads(capsys.readouterr().out)
    assert "parked" not in out and commands == ["build"] and out["result"] == "continue"


def test_no_unattended_session_may_ask_a_question():
    for phase in ("fix", "design", "build", "test", "deploy"):
        argv = run_phase.compose(
            claude="claude", plugin_dir=ROOT, phase=phase, prompt="/sdlc:sdlc-fix 0001",
            permission_mode="acceptEdits", config={}, env=dict(KEY_ENV),
        )  # fmt: skip
        denied = argv[argv.index("--disallowedTools") + 1].split(",")
        assert "AskUserQuestion" in denied, phase


# --- choice 218: the un-park labels count only from the owner's account -----------------------
def test_an_un_park_label_by_a_person_who_is_not_the_owner_is_rejected(tmp_path):
    change_dir, st = status_mod.new_change(tmp_path, "Labels")
    st.iterations = 3
    owner_env = {"GITHUB_REPOSITORY_OWNER": "luissiviero"}
    present = {c.RESET_ITERATIONS_LABEL: "colleague"}
    performed, rejected = unpark.perform(
        st, present, [], [], config={}, env=owner_env, repo="luissiviero/app"
    )
    assert performed == [] and st.iterations == 3 and st.iterations_reset_by is None
    assert rejected == [
        {
            "label": c.RESET_ITERATIONS_LABEL,
            "actor": "colleague",
            "reason": "not the owner's account (decision 24, choice 218): colleague",
        }
    ]
    # the automation rule still comes first, with its own reason
    _p, rejected = unpark.perform(
        st, {c.RESET_ITERATIONS_LABEL: "sdlc-app[bot]"}, [], [], config={}, env=owner_env
    )
    assert "cannot un-park itself" in rejected[0]["reason"]
    # fail closed: no owner known, nobody counts
    _p, rejected = unpark.perform(st, {c.RESET_ITERATIONS_LABEL: "luissiviero"}, [], [], config={})
    assert rejected and st.iterations == 3
    performed, rejected = unpark.perform(
        st, {c.RESET_ITERATIONS_LABEL: "luissiviero"}, [], [], config={}, env=owner_env
    )
    assert performed == [{"label": c.RESET_ITERATIONS_LABEL, "actor": "luissiviero"}]
    assert rejected == [] and st.iterations == 0 and st.iterations_reset_by == "luissiviero"
