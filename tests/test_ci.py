"""Layer-1 tests for plugin/ci: the credential selection, the composed ``claude -p`` command
line for every phase, the guards that make a duplicate trigger harmless, one full run against
a fake ``claude`` executable, and the installed workflow templates against the trigger and
dispatch table of docs/OPERATING_MODEL.md section 4.2 (build guide step 30).

No model, no network and no GitHub token is involved: the CLI is a Python script on PATH and
every GitHub call is monkeypatched. The credential values below are placeholders.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
from ci import auth, run_phase

from state import status as status_mod

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "sample-python-project"
INIT = ROOT / "plugin" / "init" / "sdlc_init.py"
STATE_CLI = ROOT / "plugin" / "state" / "cli.py"
WORKFLOW_DIR = ROOT / "template" / ".github" / "workflows"
PHASE_WORKFLOWS = ("sdlc-design.yml", "sdlc-build.yml", "sdlc-test.yml", "sdlc-deploy.yml")
ALL_WORKFLOWS = (*PHASE_WORKFLOWS, "sdlc-digest.yml")

KEY_VAR, TOKEN_VAR = auth.API_KEY_VAR, auth.OAUTH_TOKEN_VAR
FAKE_KEY = "placeholder-key"  # sdlc: allow-secret
FAKE_TOKEN = "placeholder-token"  # sdlc: allow-secret
KEY_ENV = {KEY_VAR: FAKE_KEY}
TOKEN_ENV = {TOKEN_VAR: FAKE_TOKEN}
BOTH_ENV = {KEY_VAR: FAKE_KEY, TOKEN_VAR: FAKE_TOKEN}


# --- helpers ------------------------------------------------------------------------------------
def git(cwd: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=cwd, capture_output=True, text=True, check=True, encoding="utf-8"
    ).stdout


def run_py(*args: str, cwd: Path, env: dict | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        env=env or os.environ.copy(),
        encoding="utf-8",
    )


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


class Args:
    """The namespace ``run_phase.main`` builds, for calling its functions directly."""

    def __init__(self, **kw):
        self.root = "."
        self.plugin_dir = str(ROOT)
        self.phase = "b"
        self.id = "0001"
        self.head_ref = None
        self.repo = "owner/name"
        self.ref = "main"
        self.log = None
        self.claude = "claude"
        self.dry_run = True
        self.no_dispatch = False
        self.__dict__.update(kw)


def dry_run_argv(capsys, root: Path, phase: str = "b", env=None) -> list[str]:
    """Put the change at the phase this run follows, then compose the command and stop."""
    change = root / "changes" / "0001-percent-helper"
    previous = run_phase.PREVIOUS_PHASE[phase]
    set_state(
        change,
        previous,
        gate_phase=previous if phase in run_phase.GATE_MUST_HAVE_PASSED else None,
        gate_result="passed",
    )
    args = Args(root=str(root), phase=phase)
    assert run_phase.run_phase(args, env or dict(KEY_ENV)) == run_phase.EXIT_OK
    return json.loads(capsys.readouterr().out)["argv"]


# --- 1. the credential selection (task 30.3; docs/NOTES.md section 2) -----------------------------
def test_choose_auth_key_only():
    chosen = auth.choose_auth(KEY_ENV)
    assert chosen["auth"] == "api_key" and chosen["bare"] is True and chosen["reason"]


def test_choose_auth_token_only():
    chosen = auth.choose_auth(TOKEN_ENV)
    assert chosen["auth"] == "oauth" and chosen["bare"] is False


def test_choose_auth_key_wins_when_both_are_set():
    chosen = auth.choose_auth(BOTH_ENV)
    assert chosen["auth"] == "api_key" and chosen["bare"] is True


def test_choose_auth_none():
    chosen = auth.choose_auth({})
    assert chosen["auth"] is None and chosen["bare"] is False
    assert KEY_VAR in chosen["reason"] and TOKEN_VAR in chosen["reason"]


def test_credential_env_carries_exactly_one_secret():
    out = auth.credential_env({"PATH": "/usr/bin", **BOTH_ENV})
    assert out[KEY_VAR] == FAKE_KEY
    assert TOKEN_VAR not in out and out["PATH"] == "/usr/bin"
    assert auth.credential_env(TOKEN_ENV) == TOKEN_ENV


def test_substrate_smoke_agrees_with_the_shared_selection():
    """The smoke script of step 3 and the phase jobs must never disagree (NOTES section 2)."""
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "substrate_smoke", ROOT / ".github" / "scripts" / "substrate_smoke.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    for env in (KEY_ENV, TOKEN_ENV, BOTH_ENV, {}):
        chosen = auth.choose_auth(env)
        smoke = module.choose_auth(env)
        if chosen["auth"] is None:
            assert smoke is None
        else:
            assert smoke == (auth.LABELS[chosen["auth"]], ["--bare"] if chosen["bare"] else [])


# --- 2. the composed command line (task 30.3; docs/NOTES.md section 10b) --------------------------
@pytest.mark.parametrize(
    ("phase", "command", "mode"),
    [("b", "sdlc-design", "default"), ("d", "sdlc-test", "acceptEdits"),
     ("e", "sdlc-deploy", "acceptEdits")],
)  # fmt: skip
def test_dry_run_argv_per_phase(capsys, project, phase, command, mode):
    root, _change = project
    argv = dry_run_argv(capsys, root, phase)
    assert argv[:3] == ["claude", "-p", "--bare"]  # the key path is bare mode
    assert argv[-1] == f"/sdlc:{command} 0001"
    assert argv[argv.index("--permission-mode") + 1] == mode
    assert "--permission-prompts" in argv and argv[argv.index("--permission-prompts") + 1] == "none"
    assert argv[argv.index("--plugin-dir") + 1] == str(ROOT)
    settings = Path(argv[argv.index("--settings") + 1])
    assert settings == ROOT / "plugin" / "ci" / "settings.ci.json" and settings.is_file()
    assert argv[argv.index("--output-format") + 1] == "json"
    assert int(argv[argv.index("--max-turns") + 1]) == run_phase.DEFAULT_MAX_TURNS


def test_design_phase_argv_cannot_edit_a_file(capsys, project):
    """Phase (b) writes spec.md and plan.md; it never edits code (decision 6, layer iii)."""
    root, _change = project
    argv = dry_run_argv(capsys, root, "b")
    assert argv[argv.index("--allowedTools") + 1] == run_phase.DESIGN_ALLOWED_TOOLS
    assert argv[argv.index("--disallowedTools") + 1] == run_phase.DESIGN_DISALLOWED_TOOLS
    assert "Edit" in argv[argv.index("--disallowedTools") + 1]


def test_dry_run_argv_on_the_token_path_is_not_bare(capsys, project):
    root, _change = project
    argv = dry_run_argv(capsys, root, env=dict(TOKEN_ENV))
    assert argv[:2] == ["claude", "-p"] and "--bare" not in argv


def test_dry_run_argv_passes_sdlc_model_when_set(capsys, project):
    root, _change = project
    argv = dry_run_argv(capsys, root, env={**KEY_ENV, "SDLC_MODEL": "opus"})
    assert argv[argv.index("--model") + 1] == "opus"
    assert "--model" not in dry_run_argv(capsys, root)


def test_phase_c_takes_its_permission_mode_from_the_preflight(capsys, project, monkeypatch):
    """Auto-accept only when plugin/gate/preflight.py allows it; never bypass (step 18)."""
    root, change = project
    set_state(change, "b", gate_phase="b", gate_result="passed")
    monkeypatch.setattr(
        run_phase, "preflight", lambda *a: {"allow": True, "permission_mode": "acceptEdits"}
    )
    args = Args(root=str(root), phase="c")
    assert run_phase.run_phase(args, dict(KEY_ENV)) == run_phase.EXIT_OK
    argv = json.loads(capsys.readouterr().out)["argv"]
    assert argv[argv.index("--permission-mode") + 1] == "acceptEdits"
    assert argv[-1] == "/sdlc:sdlc-build 0001"
    assert "bypassPermissions" not in argv


def test_phase_c_parks_when_the_preflight_refuses(capsys, project, monkeypatch):
    root, change = project
    set_state(change, "b", gate_phase="b", gate_result="passed")
    monkeypatch.setattr(
        run_phase,
        "preflight",
        lambda *a: {"allow": False, "reasons": ["test_target: the test target is not green"]},
    )
    args = Args(root=str(root), phase="c", dry_run=False)
    assert run_phase.run_phase(args, dict(KEY_ENV)) == run_phase.EXIT_OK  # a park is not a failure
    assert "not green" in json.loads(capsys.readouterr().out)["parked"][0]
    assert "preflight:" in status_mod.read_status(change).parked_reason


def test_triage_phase_is_read_only(capsys):
    """The article's p.41 pipeline step: read the log, say what failed, fix nothing."""
    args = Args(phase="triage", log="out/build.log", id=None)
    assert run_phase.run_triage(args, dict(KEY_ENV)) == run_phase.EXIT_OK
    argv = json.loads(capsys.readouterr().out)["argv"]
    assert argv[argv.index("--allowedTools") + 1] == "Read"
    assert argv[argv.index("--disallowedTools") + 1] == "Edit,Write,Bash"
    assert argv[-1].startswith("Read the CI log at out/build.log.")
    assert "Do not fix anything." in argv[-1]


def test_triage_without_a_log_is_a_usage_error():
    assert run_phase.run_triage(Args(phase="triage"), {}) == run_phase.EXIT_USAGE


# --- 3. the guard (OPERATING_MODEL section 4.2, "Guard" column) -----------------------------------
@pytest.fixture
def project(tmp_path):
    """A fixture copy with /sdlc-init run and change 0001 created, sitting at phase (a)."""
    root = tmp_path / "proj"
    shutil.copytree(FIXTURE, root)
    git(root, "init", "-q", "-b", "main")
    git(root, "config", "user.email", "owner@example.com")
    git(root, "config", "user.name", "Owner")
    git(root, "add", ".")
    git(root, "commit", "-q", "-m", "fixture")
    proc = run_py(str(INIT), "--root", str(root), "--profile", "standard", cwd=root)
    assert proc.returncode == 0, proc.stderr
    proc = run_py(
        str(STATE_CLI), "new-change", "--root", str(root), "--title", "Percent helper", cwd=root
    )
    assert proc.returncode == 0, proc.stderr
    return root, root / "changes" / "0001-percent-helper"


def set_state(change: Path, phase: str, gate_phase=None, gate_result=None, parked=None) -> None:
    st = status_mod.read_status(change)
    st.phase = phase
    if gate_phase:
        st.record_gate(gate_phase, gate_result)
    st.parked_reason = parked
    status_mod.write_status(change, st)


def skip_reason(root: Path, phase: str, env=None) -> str | None:
    _dir, _st, _cfg, reason = run_phase.guard(root, "0001", phase, "owner/name", env or {})
    return reason


def test_guard_passes_at_the_expected_phase(project):
    root, _change = project
    assert skip_reason(root, "b") is None


def test_guard_skips_at_the_wrong_phase(project):
    root, change = project
    set_state(change, "c")
    assert "not a" in skip_reason(root, "b")


def test_guard_skips_a_parked_change(project):
    root, change = project
    set_state(change, "a", parked="waiting for the owner's decision on rounding")
    assert "parked" in skip_reason(root, "b")


def test_guard_skips_when_the_repository_is_paused(project):
    root, _change = project
    text = (root / "sdlc.yaml").read_text(encoding="utf-8").replace("paused: false", "paused: true")
    (root / "sdlc.yaml").write_text(text, encoding="utf-8")
    assert "paused" in skip_reason(root, "b")


def test_guard_skips_when_the_previous_gate_did_not_pass(project):
    root, change = project
    set_state(change, "b")
    assert "gate (b) has not passed" in skip_reason(root, "c")
    set_state(change, "b", gate_phase="b", gate_result="passed")
    assert skip_reason(root, "c") is None


def test_guard_skips_an_unknown_change(project):
    root, _change = project
    _d, _s, _c, reason = run_phase.guard(root, "0099", "b", "owner/name", {})
    assert "no change folder" in reason


def test_full_profile_needs_a_human_applied_approval_label(project, monkeypatch):
    root, change = project
    text = (root / "sdlc.yaml").read_text(encoding="utf-8")
    (root / "sdlc.yaml").write_text(text.replace("profile: standard", "profile: full"), "utf-8")
    set_state(change, "c", gate_phase="c", gate_result="passed")
    env = {"GITHUB_TOKEN": FAKE_TOKEN}
    from pr import github

    monkeypatch.setattr(github, "gh_path", lambda: None)
    monkeypatch.setattr(github, "token", lambda: FAKE_TOKEN)
    monkeypatch.setattr(github, "find_open_pr", lambda repo, head: {"number": 7, "labels": []})
    assert "does not carry sdlc:c-approved" in skip_reason(root, "d", env)

    monkeypatch.setattr(
        github, "find_open_pr", lambda repo, head: {"number": 7, "labels": ["sdlc:c-approved"]}
    )
    events = [{"event": "labeled", "label": {"name": "sdlc:c-approved"}, "actor": {"login": "x"}}]

    def fake_request(method, url, tok, payload=None):
        assert "/issues/7/events" in url
        return {"status": 200, "data": events, "error": ""}

    monkeypatch.setattr(github, "_request", fake_request)
    events[0]["actor"]["login"] = run_phase.BOT_LOGIN
    assert "not by a human" in skip_reason(root, "d", env)
    events[0]["actor"]["login"] = "luissiviero"
    assert skip_reason(root, "d", env) is None
    # the Standard profile never reads the label at all
    (root / "sdlc.yaml").write_text(text, "utf-8")
    monkeypatch.setattr(github, "find_open_pr", lambda repo, head: {"number": None})
    assert skip_reason(root, "d", env) is None


def with_remote(root: Path, tmp_path: Path) -> Path:
    """A bare origin with the project's main branch pushed to it."""
    bare = tmp_path / "remote.git"
    git(tmp_path, "init", "-q", "--bare", "-b", "main", str(bare))
    git(root, "remote", "add", "origin", str(bare))
    git(root, "add", "-A")
    git(root, "commit", "-q", "-m", "sdlc-init")
    git(root, "push", "-q", "-u", "origin", "main")
    return bare


def test_a_dispatched_run_switches_to_the_work_branch_before_the_guard(project, tmp_path, capsys):
    """A workflow_dispatch run checks out the default branch, where status.yaml is still at
    the phase main knows; without the switch every dispatched (d)/(e) run would skip."""
    root, change = project
    set_state(change, "b")
    with_remote(root, tmp_path)
    # the build branch carries phase (c) with a passing gate; main stays at (b)
    git(root, "checkout", "-q", "-b", "sdlc/0001/c")
    set_state(change, "c", gate_phase="c", gate_result="passed")
    git(root, "add", "-A")
    git(root, "commit", "-q", "-m", "build(0001): the work")
    git(root, "push", "-q", "-u", "origin", "sdlc/0001/c")
    git(root, "checkout", "-q", "main")
    git(root, "branch", "-q", "-D", "sdlc/0001/c")  # the dispatched runner has main only
    assert status_mod.read_status(change).phase == "b"

    args = Args(root=str(root), phase="d")
    assert run_phase.run_phase(args, dict(KEY_ENV)) == run_phase.EXIT_OK
    out = json.loads(capsys.readouterr().out)
    assert out["branch"]["branch"] == "sdlc/0001/c" and out["branch"]["switched"] is True
    assert out["branch"]["from"] == "origin/sdlc/0001/c"
    assert out["argv"][-1] == "/sdlc:sdlc-test 0001"  # the guard saw phase (c), not (b)
    assert status_mod.read_status(change).phase == "c"
    assert git(root, "rev-parse", "--abbrev-ref", "HEAD").strip() == "sdlc/0001/c"


def test_the_build_run_creates_its_branch_off_the_design_branch(project, tmp_path, capsys):
    """Lite: the spec+plan PR is not merged before the build, so sdlc/<id>/c starts there."""
    root, change = project
    set_state(change, "b", gate_phase="b", gate_result="passed")
    with_remote(root, tmp_path)
    git(root, "checkout", "-q", "-b", "sdlc/0001/b")
    git(root, "commit", "-q", "--allow-empty", "-m", "design(0001): spec and plan")
    git(root, "push", "-q", "-u", "origin", "sdlc/0001/b")
    git(root, "checkout", "-q", "main")
    design_head = git(root, "rev-parse", "origin/sdlc/0001/b").strip()

    branch = run_phase.prepare_branch(root, "0001", "c")
    assert branch["branch"] == "sdlc/0001/c" and branch["switched"] is True
    assert branch["from"] == "origin/sdlc/0001/b"
    assert git(root, "rev-parse", "HEAD").strip() == design_head


def test_a_missing_build_branch_leaves_the_checkout_alone(project):
    root, _change = project
    branch = run_phase.prepare_branch(root, "0001", "e")
    assert branch["switched"] is False and "does not exist" in branch["note"]


def test_a_ci_park_commits_the_change_and_updates_the_pr(project, tmp_path, capsys, monkeypatch):
    """A park is a queue item: it has to reach the branch and the PR, not just status.yaml
    on a runner that is about to be deleted (OPERATING_MODEL section 5)."""
    root, change = project
    set_state(change, "b", gate_phase="b", gate_result="passed")
    bare = with_remote(root, tmp_path)
    monkeypatch.setattr(
        run_phase, "preflight", lambda *a: {"allow": False, "reasons": ["test_target: red"]}
    )
    args = Args(root=str(root), phase="c", dry_run=False)
    assert run_phase.run_phase(args, dict(KEY_ENV)) == run_phase.EXIT_OK
    out = json.loads(capsys.readouterr().out)
    assert out["parked"] == ["test_target: red"] and out["commit"]["ok"] is True
    st = status_mod.read_status(change)
    assert "preflight:" in st.parked_reason  # the park survives the commit
    assert "sdlc/0001/c" in git(bare, "branch", "--list", "sdlc/0001/c")
    tracked = git(root, "ls-tree", "-r", "--name-only", "sdlc/0001/c")
    assert "changes/0001-percent-helper/evidence/gate-c.json" in tracked
    gate_file = json.loads((change / "evidence" / "gate-c.json").read_text(encoding="utf-8"))
    assert gate_file["result"] == "park" and gate_file["label"] == "sdlc:needs-human"
    assert "What I need from you" in gate_file["what_i_need"]


def test_a_branch_that_changed_a_guardrail_file_never_runs(project, tmp_path, capsys):
    """Decision 6 layer iii: prevention. The hook denies the edit inside a run; a branch that
    arrives with one is parked before the model is called."""
    root, change = project
    set_state(change, "c", gate_phase="c", gate_result="passed")
    with_remote(root, tmp_path)
    git(root, "checkout", "-q", "-b", "sdlc/0001/c")
    (root / "CLAUDE.md").write_text("# rewritten by the run\n", encoding="utf-8")
    git(root, "add", "-A")
    git(root, "commit", "-q", "-m", "build(0001): the work")
    git(root, "push", "-q", "-u", "origin", "sdlc/0001/c")

    args = Args(root=str(root), phase="d", dry_run=False)
    assert run_phase.run_phase(args, dict(KEY_ENV)) == run_phase.EXIT_OK
    out = json.loads(capsys.readouterr().out)
    assert "CLAUDE.md" in out["parked"] and "refuses to run" in out["parked"]
    assert "guardrail" in status_mod.read_status(change).parked_reason


def test_a_framework_change_may_touch_the_guardrails(project, tmp_path):
    """The one exception of OPERATING_MODEL section 3, read from the base copy of intent.md
    so a branch cannot declare itself a framework change."""
    root, change = project
    write(change / "intent.md", "# Intent: the framework\nFramework change: yes\n")
    with_remote(root, tmp_path)  # the marker is on the base branch
    git(root, "checkout", "-q", "-b", "sdlc/0001/c")
    (root / "CLAUDE.md").write_text("# a reviewed framework change\n", encoding="utf-8")
    git(root, "add", "-A")
    git(root, "commit", "-q", "-m", "build(0001): the framework change")
    assert run_phase.guardrail_changes(root, change, {}) == []


def test_full_profile_fails_closed_when_the_label_cannot_be_read(project, monkeypatch):
    """No gh and no token is no route to the label: an unverifiable human gate is not a
    passed human gate, so the run skips instead of proceeding (OPERATING_MODEL 4.2)."""
    root, change = project
    text = (root / "sdlc.yaml").read_text(encoding="utf-8")
    (root / "sdlc.yaml").write_text(text.replace("profile: standard", "profile: full"), "utf-8")
    set_state(change, "c", gate_phase="c", gate_result="passed")
    from pr import github

    monkeypatch.setattr(github, "gh_path", lambda: None)
    monkeypatch.setattr(github, "token", lambda: None)
    assert "cannot be verified" in skip_reason(root, "d", {})

    # gh alone still reads the label; only the actor check degrades, with a note
    monkeypatch.setattr(github, "gh_path", lambda: "/usr/bin/gh")
    monkeypatch.setattr(
        github, "find_open_pr", lambda repo, head: {"number": 7, "labels": ["sdlc:c-approved"]}
    )
    assert skip_reason(root, "d", {}) is None


def test_label_events_are_read_page_by_page(monkeypatch):
    """A long PR thread pushes the `labeled` event past the first page of the timeline."""
    from pr import github

    pages = {
        "https://api.github.com/repos/o/r/issues/7/events?per_page=100": {
            "status": 200,
            "data": [{"event": "commented"}],
            "error": "",
            "headers": {"Link": '<https://api.github.com/x?page=2>; rel="next"'},
        },
        "https://api.github.com/x?page=2": {
            "status": 200,
            "data": [
                {
                    "event": "labeled",
                    "label": {"name": "sdlc:c-approved"},
                    "actor": {"login": "luissiviero"},
                }
            ],
            "error": "",
            "headers": {"Link": '<https://api.github.com/x?page=1>; rel="prev"'},
        },
    }
    seen = []

    def fake_request(method, url, tok, payload=None):
        seen.append(url)
        return pages[url]

    monkeypatch.setattr(github, "token", lambda: FAKE_TOKEN)
    monkeypatch.setattr(github, "_request", fake_request)
    assert run_phase.label_applied_by_a_human("o/r", 7, "sdlc:c-approved") == (True, "luissiviero")
    assert len(seen) == 2 and seen[0].endswith("per_page=100")


def test_change_id_comes_from_the_head_ref_when_no_input_is_given():
    assert run_phase.resolve_change_id(None, "sdlc/0042/a", "b") == ("0042", None)
    assert run_phase.resolve_change_id(None, "sdlc/0042/b", "b")[0] is None
    assert run_phase.resolve_change_id(None, "feature/x", "b")[0] is None
    assert run_phase.resolve_change_id("0007", None, "b") == ("0007", None)
    assert run_phase.resolve_change_id("7", None, "b")[0] is None


# --- 4. a full run with a fake `claude` on PATH --------------------------------------------------
FAKE_RESULT = {"total_cost_usd": 0.42, "is_error": False, "result": "ok", "session_id": "s"}
GATE_FILE = {
    "schema_version": 1,
    "change_id": "0001",
    "slug": "percent-helper",
    "phase": "b",
    "profile": "lite",
    "human_gate": False,
    "result": "continue",
    "label": None,
    "head": "abc123",
    "at": "2026-09-21T10:00:00Z",
    "dry_run": False,
    "reason": "",
    "config_note": "",
    "checks": [],
    "what_i_need": "",
}


@pytest.fixture
def fake_claude(tmp_path):
    """A stand-in CLI: it ignores its arguments and prints the JSON result it is given."""
    bindir = tmp_path / "bin"
    bindir.mkdir()
    script = bindir / "claude.py"
    write(script, "import os\nprint(os.environ['FAKE_CLAUDE_RESULT'])\n")
    launcher = bindir / "claude"
    write(launcher, f'#!/bin/sh\nexec "{sys.executable}" "{script}" "$@"\n')
    launcher.chmod(0o755)
    write(bindir / "claude.cmd", f'@echo off\r\n"{sys.executable}" "{script}" %*\r\n')
    return bindir


def fake_cli(bindir: Path) -> str:
    return str(bindir / ("claude.cmd" if os.name == "nt" else "claude"))


def test_full_run_stores_the_transcript_records_spend_and_hands_over(
    project, fake_claude, monkeypatch, capsys
):
    root, change = project
    write(change / "evidence" / "gate-b.json", json.dumps(GATE_FILE))
    monkeypatch.setenv("FAKE_CLAUDE_RESULT", json.dumps(FAKE_RESULT))
    env = dict(os.environ, **KEY_ENV)
    args = Args(
        root=str(root), phase="b", dry_run=False, no_dispatch=True, claude=fake_cli(fake_claude)
    )
    assert run_phase.run_phase(args, env) == run_phase.EXIT_OK
    out = json.loads(capsys.readouterr().out)
    assert out["result"] == "continue" and out["cost_usd"] == 0.42
    assert out["dispatched"]["would_dispatch"] == "sdlc-build.yml"
    assert out["dispatched"]["change_id"] == "0001"
    assert out["dispatched"]["head_ref"] == "sdlc/0001/c"  # keys the next run's group

    stored = json.loads((change / "evidence" / "claude-b.json").read_text(encoding="utf-8"))
    assert stored == FAKE_RESULT
    run_file = json.loads((change / "evidence" / "run-b.json").read_text(encoding="utf-8"))
    assert run_file["spend_usd"] == 0.42 and run_file["phase"] == "b"


def test_a_run_that_leaves_no_gate_file_is_an_infrastructure_failure(
    project, fake_claude, monkeypatch, capsys
):
    root, _change = project
    monkeypatch.setenv("FAKE_CLAUDE_RESULT", json.dumps(FAKE_RESULT))
    args = Args(
        root=str(root), phase="b", dry_run=False, no_dispatch=True, claude=fake_cli(fake_claude)
    )
    assert run_phase.run_phase(args, dict(os.environ, **KEY_ENV)) == run_phase.EXIT_FAILED
    assert "gate-b.json" in capsys.readouterr().err


def test_a_failing_claude_run_exits_1_with_its_text_on_stderr(
    project, fake_claude, monkeypatch, capsys
):
    root, _change = project
    monkeypatch.setenv(
        "FAKE_CLAUDE_RESULT", json.dumps({"is_error": True, "result": "Authentication error"})
    )
    args = Args(
        root=str(root), phase="b", dry_run=False, no_dispatch=True, claude=fake_cli(fake_claude)
    )
    assert run_phase.run_phase(args, dict(os.environ, **KEY_ENV)) == run_phase.EXIT_FAILED
    assert "Authentication error" in capsys.readouterr().err


def test_no_credential_skips_instead_of_failing(project, capsys):
    root, _change = project
    args = Args(root=str(root), phase="b", dry_run=False)
    assert run_phase.run_phase(args, {}) == run_phase.EXIT_OK
    assert "no credential" in json.loads(capsys.readouterr().out)["skipped"]


def test_hand_over_table_matches_operating_model_4_2():
    assert run_phase.NEXT_WORKFLOW == {
        "b": "sdlc-build.yml",
        "c": "sdlc-test.yml",
        "d": "sdlc-deploy.yml",
    }
    args = Args(no_dispatch=True)
    assert run_phase.hand_over(args, {"result": "wait"}, "b", "0001") is None
    assert run_phase.hand_over(args, {"result": "park"}, "c", "0001") is None
    assert run_phase.hand_over(args, {"result": "continue"}, "e", "0001") is None  # (e) ends here


def test_review_phase_argv_is_read_only(project, monkeypatch, capsys):
    root, change = project
    monkeypatch.setattr(run_phase, "review_prompt", lambda *a: ("REVIEW the diff.", ""))
    set_state(change, "d", gate_phase="d", gate_result="passed")
    args = Args(root=str(root), phase="review")
    assert run_phase.run_phase(args, dict(KEY_ENV)) == run_phase.EXIT_OK
    argv = json.loads(capsys.readouterr().out)["argv"]
    assert argv[argv.index("--allowedTools") + 1] == "Read,Grep,Glob,Bash(git *),Write"
    assert argv[argv.index("--disallowedTools") + 1] == "Edit,WebFetch,WebSearch"
    assert argv[argv.index("--permission-mode") + 1] == "default"
    assert argv[-1] == "REVIEW the diff."


# --- 5. the workflow templates against the trigger and dispatch table ----------------------------
def workflow(name: str) -> str:
    return (WORKFLOW_DIR / name).read_text(encoding="utf-8")


@pytest.mark.parametrize("name", ALL_WORKFLOWS)
def test_workflow_header_cites_the_contract(name):
    text = workflow(name)
    assert re.search(r"OPERATING_MODEL\.md sections? 4\.2", text)
    assert "step 30" in text and "p.39-41" in text
    assert "never start another workflow run" in text  # the token rule


@pytest.mark.parametrize("name", PHASE_WORKFLOWS)
def test_phase_workflow_triggers(name):
    text = workflow(name)
    assert re.search(r"(?m)^  workflow_dispatch:\n    inputs:\n      change_id:", text)
    assert "required: true" in text
    if name in ("sdlc-design.yml", "sdlc-build.yml"):
        assert re.search(r"(?m)^    types: \[closed\]$", text)
        assert re.search(r"(?m)^    branches: \[main\]$", text)
        assert "github.event.pull_request.merged == true" in text
    else:
        assert re.search(r"(?m)^    types: \[labeled\]$", text)
        label = "sdlc:c-approved" if name == "sdlc-test.yml" else "sdlc:d-approved"
        assert f"github.event.label.name == '{label}'" in text


@pytest.mark.parametrize("name", PHASE_WORKFLOWS)
def test_phase_workflow_permissions_and_concurrency(name):
    text = workflow(name)
    block = text.split("permissions:\n", 1)[1].split("\n\n", 1)[0]
    assert [line.strip() for line in block.splitlines()] == [
        "contents: write",
        "pull-requests: write",
        "issues: write",
        "checks: write",
        "actions: write",
    ]
    assert 'group: "sdlc-${{ inputs.head_ref || github.event.pull_request.head.ref }}"' in text
    assert "cancel-in-progress: false" in text
    assert "timeout-minutes: 150" in text


@pytest.mark.parametrize("name", PHASE_WORKFLOWS)
def test_phase_workflow_dispatch_takes_the_head_ref_that_keys_the_group(name):
    """run_phase.py's dispatch passes it, so an automated hop shares the PR-fired run's
    concurrency group (OPERATING_MODEL section 4.2)."""
    text = workflow(name)
    block = re.search(r"(?m)^      head_ref:\n(?:        .*\n)+", text)
    assert block and "required: false" in block.group(0)
    assert "type: string" in text


@pytest.mark.parametrize("name", ALL_WORKFLOWS)
def test_no_workflow_run_line_interpolates_an_expression(name):
    """Script injection: a `${{ }}` in a run: line is pasted into the shell before it runs.
    Every value reaches the script through a step-level env var instead."""
    for line in workflow(name).splitlines():
        if line.strip().startswith("run: "):
            assert "${{" not in line, line


@pytest.mark.parametrize("name", ("sdlc-design.yml", "sdlc-build.yml"))
def test_merge_fired_workflows_only_look_at_sdlc_branches(name):
    """A closed PR on any other branch is not this framework's business."""
    text = workflow(name)
    assert "startsWith(github.event.pull_request.head.ref, 'sdlc/')" in text
    assert "github.event_name != 'pull_request'" in text  # the dispatch path still runs


def test_digest_workflow_is_scheduled_and_needs_no_model_credential():
    text = workflow("sdlc-digest.yml")
    assert re.search(r'(?m)^    - cron: "17 6 \* \* \*"$', text)
    assert re.search(r"(?m)^  workflow_dispatch:$", text)
    block = text.split("permissions:\n", 1)[1].split("\n\n", 1)[0]
    assert [line.strip() for line in block.splitlines()] == [
        "contents: read",  # actions/checkout fails without it
        "issues: write",
        "pull-requests: read",
    ]
    assert "plugin/pr/digest.py --repo" in text
    assert KEY_VAR not in text and TOKEN_VAR not in text


@pytest.mark.parametrize("name", ALL_WORKFLOWS)
def test_workflow_steps_are_python_or_the_pinned_cli(name):
    for line in workflow(name).splitlines():
        stripped = line.strip()
        if stripped.startswith("run: "):
            body = stripped[len("run: ") :]
            assert body.startswith("python ") or body.startswith(
                "npm install -g @anthropic-ai/claude-code@"
            ), body


@pytest.mark.parametrize("name", ALL_WORKFLOWS)
def test_workflow_uses_no_other_secret(name):
    text = workflow(name)
    assert set(re.findall(r"secrets\.([A-Za-z_][A-Za-z0-9_]*)", text)) <= {KEY_VAR, TOKEN_VAR}
    assert "github.token" in text or "sdlc-digest" not in text
    assert "${{ secrets.GITHUB_TOKEN }}" not in text  # github.token is the documented form


@pytest.mark.parametrize("name", ALL_WORKFLOWS)
def test_workflow_checks_out_the_pinned_framework_beside_the_project(name):
    text = workflow(name)
    assert 'repository: "{{FRAMEWORK_REPO}}"' in text
    assert "ref: ${{ steps.pin.outputs.ref }}" in text
    assert "path: framework" in text
    assert "run: python .github/scripts/sdlc_pin.py" in text
    assert "fetch-depth: 0" in text


def test_permission_prompts_none_lives_in_run_phase_not_in_yaml():
    """The flag is composed in Python (task 30.3), so the YAML never carries a CLI flag."""
    source = (ROOT / "plugin" / "ci" / "run_phase.py").read_text(encoding="utf-8")
    assert "--permission-prompts" in source
    for name in ALL_WORKFLOWS:
        assert "--permission-prompts" not in workflow(name)


def test_deploy_workflow_runs_the_review_pass_before_phase_e():
    text = workflow("sdlc-deploy.yml")
    assert text.index("--phase review") < text.index("--phase e")
    assert text.count("jobs:") == 1  # both steps are in one job


# --- 6. the runner setup (task 30.7) -------------------------------------------------------------
def test_runner_setup_check_reports_without_changing_anything():
    report = json.loads(
        run_py(str(ROOT / "plugin" / "ci" / "runner_setup.py"), "--check", cwd=ROOT).stdout
    )
    assert report["check_only"] is True and report["steps"] == []
    assert report["sandbox_applies"] is sys.platform.startswith("linux")
