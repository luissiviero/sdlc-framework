"""The App token's lifetime (decision 33; ROADMAP R49): ``plugin/ci/app_token.py`` switches a
run to the workflow token once the App's installation token is older than 50 minutes, in the
environment and in the credential ``actions/checkout@v5`` persisted in ``.git/config``."""

from __future__ import annotations

import base64
import os
import subprocess
import sys
from pathlib import Path

import pytest
from ci import app_token, run_phase
from pr import github

from state import gitops

APP = "app-token-placeholder"
WORKFLOW = "workflow-token-placeholder"
KEY = "http.https://github.com/.extraheader"
NOW = 1_800_000_000.0


def _basic(value: str) -> str:
    return "AUTHORIZATION: basic " + base64.b64encode(f"x-access-token:{value}".encode()).decode()


@pytest.fixture
def app_run(monkeypatch):
    """A job that minted the App token: both tokens are the App's, the workflow token waits."""
    monkeypatch.setattr(app_token, "_noted", False)
    monkeypatch.setattr(app_token, "_replaced", set())
    monkeypatch.setenv("GITHUB_TOKEN", APP)
    monkeypatch.setenv("GH_TOKEN", APP)
    monkeypatch.setenv(app_token.WORKFLOW_TOKEN_ENV, WORKFLOW)
    monkeypatch.setenv(app_token.MINTED_AT_ENV, str(int(NOW)))
    # the machine's own ~/.gitconfig is not the test's: an empty global config
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", os.devnull)


def _checkout(tmp_path: Path, credential: str | None) -> Path:
    """A scratch repository whose local config carries the header as actions/checkout@v5
    writes it (``git config --local http.https://github.com/.extraheader <value>``)."""
    root = tmp_path / "project"
    root.mkdir()
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    if credential is not None:
        subprocess.run(["git", "-C", str(root), "config", "--local", KEY, credential], check=True)
    return root


def _headers(root: Path) -> list[str]:
    out = subprocess.run(
        ["git", "-C", str(root), "config", "--local", "--get-all", KEY],
        capture_output=True, text=True, check=False,
    )  # fmt: skip
    return out.stdout.splitlines()


def test_a_fresh_app_token_is_kept(app_run, tmp_path, capsys):
    root = _checkout(tmp_path, _basic(APP))
    env = {"GITHUB_TOKEN": APP}
    assert app_token.fall_back_if_stale(root, env, now=NOW + 49 * 60) == {"switched": False}
    assert os.environ["GITHUB_TOKEN"] == APP and env["GITHUB_TOKEN"] == APP
    assert _headers(root) == [_basic(APP)]
    assert capsys.readouterr().err == ""


def test_after_50_minutes_the_workflow_token_publishes(app_run, tmp_path, capsys):
    root = _checkout(tmp_path, _basic(APP))
    env = {"GITHUB_TOKEN": APP}
    out = app_token.fall_back_if_stale(root, env, now=NOW + 50 * 60 + 1)
    assert out == {"switched": True, "git_credential": "replaced"}
    for mapping in (os.environ, env):
        assert mapping["GITHUB_TOKEN"] == WORKFLOW and mapping["GH_TOKEN"] == WORKFLOW
    # the credential is replaced, never a second Authorization header beside it
    assert _headers(root) == [_basic(WORKFLOW)]
    assert APP not in (root / ".git" / "config").read_text(encoding="utf-8")
    assert capsys.readouterr().err.strip() == app_token.SWITCH_NOTE
    assert app_token.SWITCH_NOTE == (
        "the App token is older than 50 minutes: the workflow token publishes this run "
        "(decision 33); the project's CI on this head waits for the owner's approval"
    )
    # idempotent: a second call changes nothing and says nothing
    again = app_token.fall_back_if_stale(root, env, now=NOW + 3600)
    assert again == {"switched": True, "git_credential": "already"}
    assert _headers(root) == [_basic(WORKFLOW)] and capsys.readouterr().err == ""


def test_two_persisted_headers_become_one(app_run, tmp_path):
    root = _checkout(tmp_path, _basic(APP))
    subprocess.run(["git", "-C", str(root), "config", "--local", "--add", KEY, _basic("x" * 12)])
    app_token.fall_back_if_stale(root, now=NOW + 3600)
    assert _headers(root) == [_basic(WORKFLOW)]


def test_a_checkout_without_a_persisted_credential_is_left_alone(app_run, tmp_path):
    root = _checkout(tmp_path, None)
    out = app_token.fall_back_if_stale(root, now=NOW + 3600)
    assert out["git_credential"] == "none" and _headers(root) == []


def test_without_the_app_nothing_changes(monkeypatch, tmp_path, capsys):
    """No mint time (the variable is unset, the mint step skipped) or no workflow token (an
    older workflow copy): a no-op, however long the job has run."""
    monkeypatch.setattr(app_token, "_noted", False)
    monkeypatch.setenv("GITHUB_TOKEN", WORKFLOW)
    root = _checkout(tmp_path, _basic(WORKFLOW))
    assert app_token.fall_back_if_stale(root, now=NOW + 86400) == {"switched": False}
    monkeypatch.setenv(app_token.MINTED_AT_ENV, str(int(NOW)))
    monkeypatch.setenv("GITHUB_TOKEN", APP)
    assert app_token.fall_back_if_stale(root, now=NOW + 86400) == {"switched": False}
    assert os.environ["GITHUB_TOKEN"] == APP and _headers(root) == [_basic(WORKFLOW)]
    assert capsys.readouterr().err == ""


@pytest.mark.parametrize("minted", ["not a time", "nan", "inf", "-inf", str(int(NOW) + 301)])
def test_a_mint_time_that_is_not_a_time_counts_as_stale(app_run, tmp_path, capsys, minted):
    """R49 review, N1: a mint time that does not parse, is not finite or lies more than five
    minutes ahead gives a token of unknown age: the workflow token publishes."""
    os.environ[app_token.MINTED_AT_ENV] = minted  # the fixture's setenv restores it
    root = _checkout(tmp_path, _basic(APP))
    assert app_token.fall_back_if_stale(root, now=NOW)["switched"] is True
    assert os.environ["GITHUB_TOKEN"] == WORKFLOW and _headers(root) == [_basic(WORKFLOW)]
    assert capsys.readouterr().err.strip() == app_token.SWITCH_NOTE


def test_a_mint_time_a_little_ahead_is_clock_skew_not_staleness(app_run):
    os.environ[app_token.MINTED_AT_ENV] = str(int(NOW) + 300)
    assert app_token.is_stale(now=NOW) is False


def test_the_config_file_keeps_its_line_endings(app_run, tmp_path):
    """R49 review, N3: a Windows checkout's ``.git/config`` may use CRLF; the file edit keeps
    every line ending it found (only the header line ``git config`` itself rewrote is git's)."""
    root = _checkout(tmp_path, _basic(APP))
    config = root / ".git" / "config"
    text = config.read_text(encoding="utf-8").replace("\n", "\r\n")
    config.write_bytes(text.encode("utf-8"))
    app_token.replace_git_credential(root, WORKFLOW)
    lines = config.read_bytes().split(b"\n")[:-1]
    kept = [line for line in lines if b"extraheader" not in line]
    assert kept and all(line.endswith(b"\r") for line in kept)
    assert _headers(root) == [_basic(WORKFLOW)]


def test_the_api_and_git_routes_check_before_they_publish(app_run, tmp_path, monkeypatch):
    """``pr/github.py token()`` (every API request and dispatch) and ``state/gitops.py run``
    (every push, fetch and ls-remote) make the check themselves, so the detect, scan and
    runbook CLIs and the runner's subprocesses need no call of their own."""
    monkeypatch.setattr(app_token.time, "time", lambda: NOW + 3600)
    assert github.token() == WORKFLOW
    root = _checkout(tmp_path, _basic(APP))
    gitops.run(root, "fetch", "--quiet", str(tmp_path / "nowhere"), check=False)
    assert _headers(root) == [_basic(WORKFLOW)]


def test_the_runner_s_publishing_helpers_switch_its_env_dict(app_run, monkeypatch):
    monkeypatch.setattr(app_token.time, "time", lambda: NOW + 3600)
    env = {"GITHUB_TOKEN": APP, "GH_TOKEN": APP}
    monkeypatch.setattr(run_phase, "_RUN_ENV", env)
    assert run_phase.live_token()["switched"] is True
    assert env == {"GITHUB_TOKEN": WORKFLOW, "GH_TOKEN": WORKFLOW}


def test_the_session_holds_the_workflow_token_never_the_app_s(tmp_path):
    env = {"GITHUB_TOKEN": APP, "GH_TOKEN": APP, app_token.WORKFLOW_TOKEN_ENV: WORKFLOW}
    session = run_phase.session_env(env, tmp_path, "c")
    assert session["GITHUB_TOKEN"] == WORKFLOW and session["GH_TOKEN"] == WORKFLOW
    assert app_token.WORKFLOW_TOKEN_ENV not in session
    assert APP not in session.values()
    # without the App's workflows (no SDLC_WORKFLOW_TOKEN) the session keeps what it had
    assert run_phase.session_env({"GITHUB_TOKEN": WORKFLOW}, tmp_path)["GITHUB_TOKEN"] == WORKFLOW


def test_the_workflow_token_never_reaches_the_commands_step(monkeypatch):
    monkeypatch.setenv(app_token.WORKFLOW_TOKEN_ENV, WORKFLOW)
    assert app_token.WORKFLOW_TOKEN_ENV not in run_phase.commands_env()


# --- R49 review, B1 and S1: the session never holds the App's token -----------------------
def _session_seen(root: Path, monkeypatch, crash: bool = False) -> dict:
    """Run ``run_phase.invoke`` with a fake session that records what it held."""
    seen: dict = {}

    def fake_session(argv, cwd, env, timeout):
        seen["headers"] = _headers(root)
        seen["config"] = (root / ".git" / "config").read_text(encoding="utf-8")
        seen["env"] = dict(env)
        if crash:
            raise RuntimeError("the session crashed")
        return None, "", "", 0

    monkeypatch.setattr(run_phase, "_run_session", fake_session)
    session = run_phase.session_env(dict(os.environ), root, "c")
    if crash:
        with pytest.raises(RuntimeError):
            run_phase.invoke(["claude"], root, session, 60)
    else:
        run_phase.invoke(["claude"], root, session, 60)
    return seen


@pytest.mark.parametrize("crash", [False, True])
def test_the_session_pushes_on_the_workflow_token_and_the_app_s_comes_back(
    app_run, tmp_path, monkeypatch, crash
):
    """While the session runs, ``.git/config`` carries the workflow token's header and no
    trace of the App's, and the session's env neither: its pushes (a branch, a tag) cannot
    go out as the App and start the project's push- or tag-triggered workflows. After it, a
    fresh App token's header comes back, also when the session crashed."""
    monkeypatch.setattr(app_token.time, "time", lambda: NOW + 60)
    root = _checkout(tmp_path, _basic(APP))
    seen = _session_seen(root, monkeypatch, crash)
    assert seen["headers"] == [_basic(WORKFLOW)]
    assert _basic(APP) not in seen["config"]
    assert seen["env"]["GITHUB_TOKEN"] == WORKFLOW and seen["env"]["GH_TOKEN"] == WORKFLOW
    assert app_token.WORKFLOW_TOKEN_ENV not in seen["env"] and APP not in seen["env"].values()
    assert _headers(root) == [_basic(APP)]  # restored: the runner publishes as the App
    assert os.environ["GITHUB_TOKEN"] == APP


def test_after_a_session_past_50_minutes_the_run_stays_on_the_workflow_token(
    app_run, tmp_path, monkeypatch, capsys
):
    clock = {"now": NOW + 60}
    monkeypatch.setattr(app_token.time, "time", lambda: clock["now"])
    root = _checkout(tmp_path, _basic(APP))

    def long_session(argv, cwd, env, timeout):
        clock["now"] = NOW + 51 * 60  # the session outlived the App token's 50 minutes
        assert _headers(root) == [_basic(WORKFLOW)]
        return None, "", "", 0

    monkeypatch.setattr(run_phase, "_run_session", long_session)
    run_phase.invoke(["claude"], root, run_phase.session_env(dict(os.environ), root), 60)
    assert _headers(root) == [_basic(WORKFLOW)]
    assert os.environ["GITHUB_TOKEN"] == WORKFLOW
    assert capsys.readouterr().err.strip() == app_token.SWITCH_NOTE


def test_without_the_workflow_token_the_session_s_credential_is_untouched(tmp_path, monkeypatch):
    root = _checkout(tmp_path, _basic(APP))
    seen = _session_seen(root, monkeypatch)
    assert seen["headers"] == [_basic(APP)] and _headers(root) == [_basic(APP)]


# --- R49 review, N7 and N2: every publication checks the token first ----------------------
class _Checked(Exception):
    pass


def _stop(*args, **kwargs):
    raise _Checked


@pytest.mark.parametrize(
    "call",
    [
        lambda root: run_phase.dispatch("o/r", "sdlc-test.yml", "main", "0001", "sdlc/0001/c"),
        lambda root: run_phase.commit_run_record(root, root, "0001", "c"),
        lambda root: run_phase.park_and_publish(root, root, root, None, "c", "why"),
        lambda root: run_phase.ensure_pr(root, root, "0001", "c", "o/r", {}),
        lambda root: run_phase.supersede_pr("o/r", 7, 8),
    ],
    ids=["dispatch", "commit_run_record", "park_and_publish", "ensure_pr", "supersede_pr"],
)
def test_each_publishing_helper_checks_the_token_before_anything_else(tmp_path, monkeypatch, call):
    monkeypatch.setattr(run_phase, "live_token", _stop)
    with pytest.raises(_Checked):
        call(tmp_path)


def test_gh_runs_with_the_workflow_token_once_the_app_s_is_stale(app_run, monkeypatch):
    monkeypatch.setattr(app_token.time, "time", lambda: NOW + 3600)
    monkeypatch.setattr(github, "gh_path", lambda: sys.executable)
    out = github._gh("-c", "import os; print(os.environ['GITHUB_TOKEN'], os.environ['GH_TOKEN'])")
    assert out["ok"] and out["out"].split() == [WORKFLOW, WORKFLOW]


def test_the_checkout_check_fetch_checks_the_token_first(tmp_path, monkeypatch):
    from ci import checkout_check

    monkeypatch.setattr(app_token, "fall_back_if_stale", _stop)
    with pytest.raises(_Checked):
        checkout_check.default_branch_problems(tmp_path, "https://github.com/o/r", "main", "v1")


# --- R49 fix round 2: a git config the session altered keeps the workflow token -------------
@pytest.mark.parametrize(
    "key, value",
    [
        ("http.proxy", "http://proxy.invalid:3128"),
        ("http.sslVerify", "false"),
        ("http.https://github.com/.sslCAInfo", "/tmp/other-ca.pem"),
    ],
)
def test_a_session_that_redirects_the_next_push_leaves_the_workflow_header(
    app_run, tmp_path, monkeypatch, capsys, key, value
):
    """The App's header never goes back into a config that would send the next push
    through a proxy or without TLS verification; the run carries on with the workflow token."""
    monkeypatch.setattr(app_token.time, "time", lambda: NOW + 60)
    root = _checkout(tmp_path, _basic(APP))

    def meddling_session(argv, cwd, env, timeout):
        subprocess.run(["git", "-C", str(root), "config", "--local", key, value], check=True)
        return None, "", "", 0

    monkeypatch.setattr(run_phase, "_run_session", meddling_session)
    run_phase.invoke(["claude"], root, run_phase.session_env(dict(os.environ), root), 60)
    assert _headers(root) == [_basic(WORKFLOW)]
    assert os.environ["GITHUB_TOKEN"] == WORKFLOW and os.environ["GH_TOKEN"] == WORKFLOW
    err = capsys.readouterr().err
    assert f"carries {key.lower()}" in err.lower() and "the workflow token publishes" in err


def test_a_legitimate_push_u_still_gets_the_app_header_back(app_run, tmp_path, monkeypatch):
    """The check reads keys, not bytes: a session's ``git push -u`` writes branch keys."""
    monkeypatch.setattr(app_token.time, "time", lambda: NOW + 60)
    root = _checkout(tmp_path, _basic(APP))

    def pushing_session(argv, cwd, env, timeout):
        for k, v in (("branch.sdlc/0001/c.remote", "origin"), ("branch.sdlc/0001/c.merge", "x")):
            subprocess.run(["git", "-C", str(root), "config", "--local", k, v], check=True)
        return None, "", "", 0

    monkeypatch.setattr(run_phase, "_run_session", pushing_session)
    run_phase.invoke(["claude"], root, run_phase.session_env(dict(os.environ), root), 60)
    assert _headers(root) == [_basic(APP)]


def test_a_failed_switch_starts_the_session_with_no_credential(app_run, tmp_path, monkeypatch):
    """Fail closed: when the workflow header cannot be written, the key is removed before
    the session (it cannot push; the runner publishes after it) and comes back after."""
    monkeypatch.setattr(app_token.time, "time", lambda: NOW + 60)
    root = _checkout(tmp_path, _basic(APP))
    real = app_token._set_credential
    calls = {"n": 0}

    def failing_first(root_, value, create=False):
        calls["n"] += 1
        return "failed: test" if calls["n"] == 1 else real(root_, value, create)

    monkeypatch.setattr(app_token, "_set_credential", failing_first)
    seen = _session_seen(root, monkeypatch)
    assert seen["headers"] == [] and _basic(APP) not in seen["config"]
    assert _headers(root) == [_basic(APP)]


def test_a_credential_that_can_be_neither_switched_nor_removed_starts_no_session(
    app_run, tmp_path, monkeypatch
):
    root = _checkout(tmp_path, _basic(APP))
    monkeypatch.setattr(app_token, "_set_credential", lambda *a, **k: "failed: test")
    real_git = app_token._git
    monkeypatch.setattr(
        app_token,
        "_git",
        lambda r, *args: (5, "locked") if "--unset-all" in args else real_git(r, *args),
    )
    ran = []
    monkeypatch.setattr(run_phase, "_run_session", lambda *a: ran.append(1))
    data, _raw, err, code = run_phase.invoke(["claude"], root, {}, 60)
    assert ran == [] and code == 1 and "does not start" in err


def test_the_triage_session_gets_the_session_environment(app_run, tmp_path, monkeypatch):
    from tests.test_ci import KEY_ENV, Args

    seen = {}

    def fake_session(argv, cwd, env, timeout):
        seen.update(env)
        return None, "it failed", "", 0

    monkeypatch.setattr(run_phase, "_run_session", fake_session)
    env = {**KEY_ENV, "GITHUB_TOKEN": APP, "GH_TOKEN": APP, app_token.WORKFLOW_TOKEN_ENV: WORKFLOW}
    args = Args(root=str(tmp_path), phase="triage", log="build.log", id=None, dry_run=False)
    assert run_phase.run_triage(args, env) == run_phase.EXIT_OK
    assert seen["GITHUB_TOKEN"] == WORKFLOW and seen["GH_TOKEN"] == WORKFLOW
    assert app_token.WORKFLOW_TOKEN_ENV not in seen
