"""The App token's lifetime (decision 33; ROADMAP R49): ``plugin/ci/app_token.py`` switches a
run to the workflow token once the App's installation token is older than 50 minutes, in the
environment and in the credential ``actions/checkout@v5`` persisted in ``.git/config``."""

from __future__ import annotations

import base64
import os
import subprocess
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
    monkeypatch.setenv(app_token.MINTED_AT_ENV, "not a time")
    monkeypatch.setenv(app_token.WORKFLOW_TOKEN_ENV, WORKFLOW)
    assert app_token.fall_back_if_stale(root, now=NOW + 86400) == {"switched": False}
    assert os.environ["GITHUB_TOKEN"] == APP and _headers(root) == [_basic(WORKFLOW)]
    assert capsys.readouterr().err == ""


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
