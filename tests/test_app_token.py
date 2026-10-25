"""The automation's GitHub token (decision 33; ROADMAP R49): ``plugin/ci/app_token.py``
switches a run to the workflow token once the App's installation token is older than 50
minutes, and hands git its credential through the environment only - no checkout persists
one in ``.git/config`` (R49 fix round 4)."""

from __future__ import annotations

import base64
import http.server
import os
import subprocess
import sys
import threading
from pathlib import Path

import pytest
from ci import app_token, checkout_check, run_phase
from pr import github

from state import gitops

APP = "app-token-placeholder"
WORKFLOW = "workflow-token-placeholder"
NOW = 1_800_000_000.0
KEY = "http.https://github.com/.extraheader"


def _basic(value: str) -> str:
    return "AUTHORIZATION: basic " + base64.b64encode(f"x-access-token:{value}".encode()).decode()


@pytest.fixture
def app_run(monkeypatch):
    """A runner job that minted the App token: both tokens are the App's, the workflow token
    waits; no command-scope git config of its own."""
    monkeypatch.setattr(app_token, "_noted", False)
    monkeypatch.setattr(app_token, "_tainted", None)
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    monkeypatch.setenv("GITHUB_TOKEN", APP)
    monkeypatch.setenv("GH_TOKEN", APP)
    monkeypatch.setenv(app_token.WORKFLOW_TOKEN_ENV, WORKFLOW)
    monkeypatch.setenv(app_token.MINTED_AT_ENV, str(int(NOW)))
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", os.devnull)
    for name in list(os.environ):
        if name.startswith("GIT_CONFIG_") and name != "GIT_CONFIG_GLOBAL":
            monkeypatch.delenv(name)


def _repo(tmp_path: Path, name: str = "project") -> Path:
    root = tmp_path / name
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    return root


def _pairs(env: dict[str, str]) -> list[tuple[str, str]]:
    count = int(env.get("GIT_CONFIG_COUNT") or 0)
    return [(env[f"GIT_CONFIG_KEY_{n}"], env[f"GIT_CONFIG_VALUE_{n}"]) for n in range(count)]


# --- the token switch ----------------------------------------------------------------------
def test_a_fresh_app_token_is_kept(app_run, capsys):
    env = {"GITHUB_TOKEN": APP}
    assert app_token.fall_back_if_stale(env, now=NOW + 49 * 60) == {"switched": False}
    assert os.environ["GITHUB_TOKEN"] == APP and env["GITHUB_TOKEN"] == APP
    assert capsys.readouterr().err == ""


def test_after_50_minutes_the_workflow_token_publishes(app_run, capsys):
    env = {"GITHUB_TOKEN": APP}
    assert app_token.fall_back_if_stale(env, now=NOW + 50 * 60 + 1) == {"switched": True}
    for mapping in (os.environ, env):
        assert mapping["GITHUB_TOKEN"] == WORKFLOW and mapping["GH_TOKEN"] == WORKFLOW
    assert capsys.readouterr().err.strip() == app_token.SWITCH_NOTE
    assert app_token.SWITCH_NOTE == (
        "the App token is older than 50 minutes: the workflow token publishes this run "
        "(decision 33); the project's CI on this head waits for the owner's approval"
    )
    assert app_token.fall_back_if_stale(env, now=NOW + 3600) == {"switched": True}
    assert capsys.readouterr().err == ""  # once per process


def test_without_the_app_nothing_changes(monkeypatch, capsys):
    """No mint time (the mint step skipped) or no workflow token (an older workflow copy):
    a no-op, however long the job has run."""
    monkeypatch.setattr(app_token, "_noted", False)
    monkeypatch.setenv("GITHUB_TOKEN", WORKFLOW)
    assert app_token.fall_back_if_stale(now=NOW + 86400) == {"switched": False}
    monkeypatch.setenv(app_token.MINTED_AT_ENV, str(int(NOW)))
    monkeypatch.setenv("GITHUB_TOKEN", APP)
    assert app_token.fall_back_if_stale(now=NOW + 86400) == {"switched": False}
    assert os.environ["GITHUB_TOKEN"] == APP and capsys.readouterr().err == ""


@pytest.mark.parametrize("minted", ["not a time", "nan", "inf", "-inf", str(int(NOW) + 301)])
def test_a_mint_time_that_is_not_a_time_counts_as_stale(app_run, capsys, minted):
    os.environ[app_token.MINTED_AT_ENV] = minted  # the fixture's setenv restores it
    assert app_token.fall_back_if_stale(now=NOW)["switched"] is True
    assert os.environ["GITHUB_TOKEN"] == WORKFLOW
    assert capsys.readouterr().err.strip() == app_token.SWITCH_NOTE


def test_a_mint_time_a_little_ahead_is_clock_skew_not_staleness(app_run):
    os.environ[app_token.MINTED_AT_ENV] = str(int(NOW) + 300)
    assert app_token.is_stale(now=NOW) is False


def test_the_api_route_checks_before_it_publishes(app_run, monkeypatch):
    monkeypatch.setattr(app_token.time, "time", lambda: NOW + 3600)
    assert github.token() == WORKFLOW


def test_the_runner_s_publishing_helpers_switch_its_env_dict(app_run, monkeypatch):
    monkeypatch.setattr(app_token.time, "time", lambda: NOW + 3600)
    env = {"GITHUB_TOKEN": APP, "GH_TOKEN": APP}
    monkeypatch.setattr(run_phase, "_RUN_ENV", env)
    assert run_phase.live_token()["switched"] is True
    assert env == {"GITHUB_TOKEN": WORKFLOW, "GH_TOKEN": WORKFLOW}


def test_gh_runs_with_the_workflow_token_once_the_app_s_is_stale(app_run, monkeypatch):
    monkeypatch.setattr(app_token.time, "time", lambda: NOW + 3600)
    monkeypatch.setattr(github, "gh_path", lambda: sys.executable)
    out = github._gh("-c", "import os; print(os.environ['GITHUB_TOKEN'], os.environ['GH_TOKEN'])")
    assert out["ok"] and out["out"].split() == [WORKFLOW, WORKFLOW]


# --- git's credential, in the environment only ---------------------------------------------
def test_git_gets_the_app_s_header_while_fresh_then_the_workflow_s(app_run, monkeypatch):
    clock = {"now": NOW + 60}
    monkeypatch.setattr(app_token.time, "time", lambda: clock["now"])
    # an empty value first: git's documented reset of the header list, then the one header
    assert _pairs(app_token.git_auth_env()) == [(KEY, ""), (KEY, _basic(APP))]
    clock["now"] = NOW + 51 * 60
    assert _pairs(app_token.git_auth_env()) == [(KEY, ""), (KEY, _basic(WORKFLOW))]


def test_without_the_app_git_gets_the_job_s_token(monkeypatch):
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    monkeypatch.setenv("GITHUB_TOKEN", WORKFLOW)
    for name in list(os.environ):
        if name.startswith("GIT_CONFIG_"):
            monkeypatch.delenv(name)
    monkeypatch.delenv("GH_TOKEN", raising=False)
    assert _pairs(app_token.git_auth_env()) == [(KEY, ""), (KEY, _basic(WORKFLOW))]
    monkeypatch.delenv("GITHUB_TOKEN")
    assert app_token.git_auth_env() == {}  # no token: nothing to hand out
    monkeypatch.setenv("GITHUB_TOKEN", WORKFLOW)
    monkeypatch.delenv("GITHUB_ACTIONS")
    assert app_token.git_auth_env() == {}  # by hand: the owner's own credentials apply


def test_the_header_is_appended_to_the_command_scope_config_already_there(app_run, monkeypatch):
    """This container (and a self-hosted runner) may already pass config through
    ``GIT_CONFIG_COUNT``: it is appended to, never overwritten."""
    monkeypatch.setattr(app_token.time, "time", lambda: NOW + 60)
    monkeypatch.setenv("GIT_CONFIG_COUNT", "2")
    monkeypatch.setenv("GIT_CONFIG_KEY_0", "url.https://mirror.invalid/.insteadOf")
    monkeypatch.setenv("GIT_CONFIG_VALUE_0", "https://github.com/")
    monkeypatch.setenv("GIT_CONFIG_KEY_1", "core.quotePath")
    monkeypatch.setenv("GIT_CONFIG_VALUE_1", "false")
    auth = app_token.git_auth_env()
    assert auth["GIT_CONFIG_COUNT"] == "4"
    assert set(auth) == {
        "GIT_CONFIG_COUNT",
        *(f"GIT_CONFIG_{w}_{n}" for w in ("KEY", "VALUE") for n in (2, 3)),
    }
    merged = {**os.environ, **auth}
    assert _pairs(merged)[:2] == [
        ("url.https://mirror.invalid/.insteadOf", "https://github.com/"),
        ("core.quotePath", "false"),
    ]
    monkeypatch.setenv("GIT_CONFIG_COUNT", "two")
    with pytest.raises(app_token.GitAuthError):
        app_token.git_auth_env()


def test_a_git_older_than_2_31_fails_loudly(app_run, monkeypatch):
    monkeypatch.setattr(app_token, "_git_version", (2, 30))
    with pytest.raises(app_token.GitAuthError, match="needs git 2.31"):
        app_token.git_auth_env()


def test_strip_git_auth_drops_only_the_credential(app_run, monkeypatch):
    monkeypatch.setenv("GIT_CONFIG_COUNT", "1")
    monkeypatch.setenv("GIT_CONFIG_KEY_0", "core.quotePath")
    monkeypatch.setenv("GIT_CONFIG_VALUE_0", "false")
    env = {**os.environ, **app_token.git_auth_env()}
    stripped = app_token.strip_git_auth(env)
    assert _pairs(stripped) == [("core.quotePath", "false")]
    assert _basic(APP) not in stripped.values()


class _Recorder(http.server.BaseHTTPRequestHandler):
    seen: list = []

    def do_GET(self):  # noqa: N802 - the http.server hook
        type(self).seen.append(self.headers.get_all("Authorization") or [])
        self.send_response(404)
        self.end_headers()

    def log_message(self, *args):  # quiet
        pass


@pytest.fixture
def server(monkeypatch):
    _Recorder.seen = []
    srv = http.server.HTTPServer(("127.0.0.1", 0), _Recorder)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    url = f"http://127.0.0.1:{srv.server_address[1]}"
    monkeypatch.setenv("GITHUB_SERVER_URL", url)
    monkeypatch.setenv("NO_PROXY", "127.0.0.1")
    monkeypatch.setenv("no_proxy", "127.0.0.1")
    yield url
    srv.shutdown()


def test_a_gitops_push_sends_the_header_from_its_environment_only(
    app_run, tmp_path, server, monkeypatch
):
    """A real git push through ``state/gitops.py``: the header arrives, once, though the
    checkout carries none - and a header a file does carry (an older persisted checkout)
    is reset, never sent beside it."""
    monkeypatch.setattr(app_token.time, "time", lambda: NOW + 60)
    root = _repo(tmp_path)
    subprocess.run(
        ["git", "-C", str(root), "-c", "user.name=t", "-c", "user.email=t@example.invalid",
         "commit", "-q", "--allow-empty", "-m", "x"],
        check=True,
    )  # fmt: skip
    subprocess.run(["git", "-C", str(root), "remote", "add", "origin", f"{server}/o/r.git"])
    gitops.run(root, "push", "origin", "HEAD", check=False)
    assert _Recorder.seen and _Recorder.seen[0] == [_basic(APP).split(": ", 1)[1]]
    assert "extraheader" not in (root / ".git" / "config").read_text(encoding="utf-8")
    _Recorder.seen = []
    subprocess.run(
        ["git", "-C", str(root), "config", f"http.{server}/.extraheader", _basic("x" * 12)]
    )
    gitops.run(root, "ls-remote", "origin", check=False)
    assert _Recorder.seen[0] == [_basic(APP).split(": ", 1)[1]]


# --- who gets it: the session, and nobody running project code -----------------------------
def test_the_session_holds_the_workflow_token_never_the_app_s(app_run, tmp_path, monkeypatch):
    monkeypatch.setattr(app_token.time, "time", lambda: NOW + 60)
    session = run_phase.session_env(dict(os.environ), tmp_path, "build")
    assert session["GITHUB_TOKEN"] == WORKFLOW and session["GH_TOKEN"] == WORKFLOW
    assert (KEY, _basic(WORKFLOW)) in _pairs(session)
    assert app_token.WORKFLOW_TOKEN_ENV not in session
    assert APP not in session.values() and _basic(APP) not in session.values()


def test_a_job_that_hands_over_no_workflow_token_leaves_the_session_none(app_run, tmp_path):
    env = {k: v for k, v in os.environ.items() if k != app_token.WORKFLOW_TOKEN_ENV}
    session = run_phase.session_env(env, tmp_path)
    assert not {"GITHUB_TOKEN", "GH_TOKEN"} & set(session) and _pairs(session) == []


def test_the_triage_session_gets_no_github_token(app_run, tmp_path, monkeypatch):
    """R18, point 5: the triage session reads logs only; neither the App's token nor the
    workflow token, nor git's credential, reaches it (the record writer runs outside it)."""
    from tests.test_ci import KEY_ENV, Args

    seen = {}

    def fake_session(argv, cwd, env, timeout):
        seen.update(env)
        return None, "it failed", "", 0

    monkeypatch.setattr(run_phase, "_run_session", fake_session)
    env = {**os.environ, **KEY_ENV}
    args = Args(root=str(tmp_path), phase="triage", log="build.log", id=None, dry_run=False)
    assert run_phase.run_triage(args, env) == run_phase.EXIT_OK
    assert not {"GITHUB_TOKEN", "GH_TOKEN", app_token.WORKFLOW_TOKEN_ENV} & set(seen)
    assert WORKFLOW not in seen.values() and APP not in seen.values()
    assert _basic(APP) not in seen.values() and _basic(WORKFLOW) not in seen.values()


def test_a_target_the_commands_step_runs_finds_no_token(app_run, tmp_path, monkeypatch):
    """S-A: code the session wrote runs outside the sandbox in the commands step; it finds
    no token in its environment and none in ``.git/config``."""
    monkeypatch.setattr(app_token.time, "time", lambda: NOW + 60)
    # as if the runner's env had the credential; the empty reset value is left out, since
    # setting an empty variable deletes it on Windows (the runner passes the pairs in a
    # subprocess env dict, where an empty value survives)
    auth = app_token.git_auth_env()
    n = int(auth[app_token.COUNT_ENV]) - 1
    monkeypatch.setenv(app_token.COUNT_ENV, "1")
    monkeypatch.setenv(app_token.KEY_ENV.format(n=0), auth[app_token.KEY_ENV.format(n=n)])
    monkeypatch.setenv(app_token.VALUE_ENV.format(n=0), auth[app_token.VALUE_ENV.format(n=n)])
    root = _repo(tmp_path)
    probe = (
        "import os, pathlib, sys; seen = ' '.join(os.environ.values()) + "
        "pathlib.Path('.git/config').read_text(); "
        "sys.exit(any(t in seen for t in sys.argv[1:]))"
    )
    secrets = [APP, WORKFLOW, _basic(APP).split()[-1], _basic(WORKFLOW).split()[-1]]
    proc = subprocess.run(
        [sys.executable, "-c", probe, *secrets], cwd=root, env=run_phase.commands_env()
    )
    assert proc.returncode == 0
    assert app_token.WORKFLOW_TOKEN_ENV not in run_phase.commands_env()


# --- every publication checks the token first ----------------------------------------------
class _Checked(Exception):
    pass


def _stop(*args, **kwargs):
    raise _Checked


@pytest.mark.parametrize(
    "call",
    [
        lambda root: run_phase.dispatch("o/r", "sdlc-test.yml", "main", "0001", "sdlc/0001/build"),
        lambda root: run_phase.commit_run_record(root, root, "0001", "build"),
        lambda root: run_phase.park_and_publish(root, root, root, None, "build", "why"),
        lambda root: run_phase.ensure_pr(root, root, "0001", "build", "o/r", {}),
        lambda root: run_phase.supersede_pr("o/r", 7, 8),
    ],
    ids=["dispatch", "commit_run_record", "park_and_publish", "ensure_pr", "supersede_pr"],
)
def test_each_publishing_helper_checks_the_token_before_anything_else(tmp_path, monkeypatch, call):
    monkeypatch.setattr(run_phase, "live_token", _stop)
    with pytest.raises(_Checked):
        call(tmp_path)


# --- checkout_check: its fetch's credential and its hardening (S-B) -------------------------
def test_the_checkout_check_fetch_takes_the_credential_in_its_environment(
    app_run, tmp_path, monkeypatch
):
    monkeypatch.setattr(app_token.time, "time", lambda: NOW + 60)
    root = _repo(tmp_path)
    calls = []
    real = checkout_check.git

    def fake(cwd, *a, env=None):
        if a[0] != "fetch":
            return real(cwd, *a, env=env)  # the config listing runs for real
        calls.append((a, env))
        return 1, "no"

    monkeypatch.setattr(checkout_check, "git", fake)
    checkout_check.default_branch_problems(root, "https://github.com/o/r", "main", "v1")
    [(args, env)] = [c for c in calls if c[0][0] == "fetch"]
    assert (KEY, _basic(APP)) in _pairs(env)
    assert env["GIT_CONFIG_GLOBAL"] == "/dev/null"  # CLEAN_ENV still applies


def test_a_hook_the_session_planted_never_runs_in_the_checkout_check(tmp_path):
    root = _repo(tmp_path)
    subprocess.run(
        ["git", "-C", str(root), "-c", "user.name=t", "-c", "user.email=t@example.invalid",
         "commit", "-q", "--allow-empty", "-m", "x"],
        check=True,
    )  # fmt: skip
    marker = tmp_path / "hook-ran"
    hook = root / ".git" / "hooks" / "reference-transaction"
    hook.write_text(f"#!/bin/sh\ntouch '{marker.as_posix()}'\n", encoding="utf-8")
    hook.chmod(0o755)
    assert checkout_check.hardening()[:2] == ["-c", checkout_check.hardening()[1]]
    assert "core.fsmonitor=false" in checkout_check.hardening()
    code, _ = checkout_check.git(root, "update-ref", "refs/heads/planted", "HEAD")
    assert code == 0 and not marker.exists()
    if os.name != "nt":  # the same command without the hardening runs the hook
        subprocess.run(["git", "-C", str(root), "update-ref", "refs/heads/other", "HEAD"])
        assert marker.exists()


# --- R49 fix round 5: the App's token goes out only through a clean git config -------------
def _committed(tmp_path: Path, server: str) -> Path:
    root = _repo(tmp_path)
    subprocess.run(
        ["git", "-C", str(root), "-c", "user.name=t", "-c", "user.email=t@example.invalid",
         "commit", "-q", "--allow-empty", "-m", "x"],
        check=True,
    )  # fmt: skip
    subprocess.run(["git", "-C", str(root), "remote", "add", "origin", f"{server}/o/r.git"])
    return root


@pytest.mark.parametrize("planted", ["url-proxy", "include-ssl", "worktree-proxy"])
def test_a_planted_redirect_makes_the_push_carry_the_workflow_header(
    app_run, tmp_path, server, monkeypatch, capsys, planted
):
    """S-1: a session can plant a URL-specific proxy, an include holding ``sslVerify=false``
    or a worktree proxy, and a command-scope value cannot reliably beat a more specific URL
    subsection; the App's token then never goes out: the push carries the workflow header,
    the API tokens follow, and the decision sticks for the process."""
    monkeypatch.setattr(app_token.time, "time", lambda: NOW + 60)
    root = _committed(tmp_path, server)
    config = ["git", "-C", str(root), "config"]
    if planted == "url-proxy":
        subprocess.run([*config, "http.https://github.com/o/r.proxy", "http://p.invalid:1"])
        expected = "http.https://github.com/o/r.proxy (local)"
    elif planted == "include-ssl":
        included = tmp_path / "included.config"
        included.write_text("[http]\n\tsslVerify = false\n", encoding="utf-8")
        subprocess.run([*config, "include.path", included.as_posix()])
        expected = "http.sslverify (local)"
    else:
        subprocess.run([*config, "extensions.worktreeConfig", "true"])
        subprocess.run(
            [*config, "--worktree", "http.https://github.com/.proxy", "http://p.invalid:1"]
        )
        expected = "http.https://github.com/.proxy (worktree)"
    gitops.run(root, "push", "origin", "HEAD", check=False)
    assert _Recorder.seen and _Recorder.seen[0] == [_basic(WORKFLOW).split(": ", 1)[1]]
    assert os.environ["GITHUB_TOKEN"] == WORKFLOW and os.environ["GH_TOKEN"] == WORKFLOW
    err = capsys.readouterr().err
    assert expected.lower() in err.lower() and "the workflow token publishes this run" in err
    # sticky: the planted key gone, the process stays on the workflow token, silently
    monkeypatch.setenv("GITHUB_TOKEN", APP)
    assert _pairs(app_token.git_auth_env(root=root))[-1][1] == _basic(WORKFLOW)
    assert capsys.readouterr().err == ""


def test_a_clean_config_is_judged_again_on_every_call(app_run, tmp_path, monkeypatch):
    """A clean result is never remembered: the session could plant a key afterwards."""
    monkeypatch.setattr(app_token.time, "time", lambda: NOW + 60)
    root = _repo(tmp_path)
    assert _pairs(app_token.git_auth_env(root=root))[-1] == (KEY, _basic(APP))
    subprocess.run(["git", "-C", str(root), "config", "http.sslVerify", "false"], check=True)
    assert _pairs(app_token.git_auth_env(root=root))[-1] == (KEY, _basic(WORKFLOW))


def test_without_the_app_the_config_is_not_judged(monkeypatch, tmp_path):
    """No App, nothing to protect beyond what the workflow token always had: no listing."""
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    monkeypatch.setenv("GITHUB_TOKEN", WORKFLOW)
    monkeypatch.setattr(app_token, "_config_finding", _stop)
    assert app_token.git_auth_env(root=tmp_path)


def test_the_release_git_runner_takes_network_env_on_its_calls(tmp_path, monkeypatch):
    """N4: ``release/approval.make_git`` (the release's fetch, ls-remote and record push)
    passes ``state/gitops.py network_env`` to every git call it starts."""
    from release import approval

    seen = []
    monkeypatch.setattr(
        gitops, "network_env", lambda args, root=None: {"MARK": f"{args[0]}@{root}"}
    )

    def fake_run(argv, **kwargs):
        seen.append((argv[1], kwargs.get("env")))
        return subprocess.CompletedProcess(argv, 0, "", "")

    monkeypatch.setattr(approval.subprocess, "run", fake_run)
    git = approval.make_git()
    for verb in ("fetch", "ls-remote", "push", "status"):
        git(tmp_path, verb)
    assert seen == [
        (verb, {"MARK": f"{verb}@{tmp_path}"}) for verb in ("fetch", "ls-remote", "push", "status")
    ]
