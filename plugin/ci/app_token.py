"""The App token's lifetime (decision 33; ROADMAP R49): fall back to the workflow token after
50 minutes.

The eight workflows that push or open pull requests mint the project's GitHub App token in
their first step (``actions/create-github-app-token``), and the job then pushes, opens pull
requests and dispatches with it. An installation token expires one hour after it is minted
(the action's README: "An installation access token expires after 1 hour"), while a phase
job may run for more than three hours, and the runner publishes at the end of the session.
So the workflow records when it minted the token (``SDLC_APP_TOKEN_MINTED_AT``, epoch
seconds, through ``$GITHUB_ENV``) and hands every publishing step the workflow token too
(``SDLC_WORKFLOW_TOKEN``). Once the App token is older than ``MAX_AGE_SECONDS``,
``fall_back_if_stale`` switches the run to the workflow token:

- ``GITHUB_TOKEN`` and ``GH_TOKEN`` in ``os.environ`` (what ``pr/github.py``, ``gh`` and
  every plugin CLI the runner starts read) and in the env dict the caller passes;
- the git credential ``actions/checkout@v5`` persisted in the checkout's local
  ``.git/config``: ``http.<server>/.extraheader`` = ``AUTHORIZATION: basic
  base64(x-access-token:<token>)`` (``src/git-auth-helper.ts``, ``configureToken``). The
  value is replaced, never added beside (two Authorization headers would be sent), and as
  the action writes it: a placeholder through ``git config``, then the file edited, so the
  token never appears on a command line.

The cost is the one decision 33 removed: the project's CI on a head the workflow token
pushed waits for the owner's approval (``docs/notes/23.md``). Without the App (no
``SDLC_APP_TOKEN_MINTED_AT``) or without ``SDLC_WORKFLOW_TOKEN`` nothing changes. The check
is idempotent and cheap (two environment reads before the deadline; one ``git config`` read
per checkout after it), so ``pr/github.py`` and ``state/gitops.py`` call it before every
request and every network git command. Standard library only: this module imports nothing
of the plugin.
"""

from __future__ import annotations

import base64
import os
import subprocess
import sys
import time
import urllib.parse
from collections.abc import Mapping, MutableMapping
from pathlib import Path
from typing import Any

MINTED_AT_ENV = "SDLC_APP_TOKEN_MINTED_AT"
WORKFLOW_TOKEN_ENV = "SDLC_WORKFLOW_TOKEN"
TOKEN_VARS = ("GITHUB_TOKEN", "GH_TOKEN")
MAX_AGE_SECONDS = 50 * 60  # ten minutes before the hour GitHub gives an installation token
SWITCH_NOTE = (
    "the App token is older than 50 minutes: the workflow token publishes this run "
    "(decision 33); the project's CI on this head waits for the owner's approval"
)
# actions/checkout's own placeholder (configureToken): the value goes in through the file
PLACEHOLDER = "AUTHORIZATION: basic ***"
DEFAULT_SERVER_URL = "https://github.com"

_noted = False
_replaced: set[tuple[str, str]] = set()  # (checkout, credential key) already switched


def _lookup(name: str, env: Mapping[str, str] | None) -> str:
    return str((env or {}).get(name) or os.environ.get(name) or "").strip()


def is_stale(env: Mapping[str, str] | None = None, now: float | None = None) -> bool:
    """True when the App's token was minted more than ``MAX_AGE_SECONDS`` ago and the
    workflow token is there to take over; False without the App or without that token."""
    minted, workflow = _lookup(MINTED_AT_ENV, env), _lookup(WORKFLOW_TOKEN_ENV, env)
    if not minted or not workflow:
        return False
    try:
        minted_at = float(minted)
    except ValueError:
        return False
    return (time.time() if now is None else now) - minted_at > MAX_AGE_SECONDS


def credential_key(server_url: str | None = None) -> str:
    """The config key ``actions/checkout`` persists the token under:
    ``http.<scheme>://<host>/.extraheader``."""
    parts = urllib.parse.urlsplit(
        server_url or os.environ.get("GITHUB_SERVER_URL") or DEFAULT_SERVER_URL
    )
    return f"http.{parts.scheme}://{parts.netloc}/.extraheader"


def credential_value(token: str) -> str:
    basic = base64.b64encode(f"x-access-token:{token}".encode()).decode("ascii")
    return f"AUTHORIZATION: basic {basic}"


def _git(root: Path, *args: str) -> tuple[int, str]:
    try:
        proc = subprocess.run(
            ["git", *args], cwd=str(root), capture_output=True, text=True, encoding="utf-8",
            check=False,
        )  # fmt: skip
    except OSError as exc:
        return 127, str(exc)
    return proc.returncode, proc.stdout if proc.returncode == 0 else proc.stderr


def replace_git_credential(root: Path, token: str) -> str:
    """Point the checkout's persisted credential at ``token``: "replaced", "already" (it
    carries that token), "none" (no persisted credential: ``persist-credentials: false`` or
    not a checkout) or "failed: <why>". Every value of the key is replaced by one."""
    root = Path(root)
    key = credential_key()
    memo = (str(root.resolve()), key)
    if memo in _replaced:
        return "already"
    value = credential_value(token)
    code, out = _git(root, "config", "--local", "--get-all", key)
    if code != 0:
        return "none"  # exit 1: the key is not set (git config's documented code)
    if out.splitlines() == [value]:
        _replaced.add(memo)
        return "already"
    code, path = _git(root, "rev-parse", "--git-path", "config")
    if code != 0 or not path.strip():
        return f"failed: the checkout's config file was not found ({path.strip()})"
    config = (root / path.strip()).resolve()
    code, why = _git(root, "config", "--local", "--replace-all", key, PLACEHOLDER)
    if code != 0:
        return f"failed: git config exited {code}: {why.strip()}"
    try:
        text = config.read_text(encoding="utf-8")
        if text.count(PLACEHOLDER) != 1:
            return f"failed: the placeholder is not in {config} exactly once"
        config.write_text(text.replace(PLACEHOLDER, value), encoding="utf-8")
    except OSError as exc:
        return f"failed: {exc}"
    _replaced.add(memo)
    return "replaced"


def fall_back_if_stale(
    root: Path | str | None = None,
    env: MutableMapping[str, str] | None = None,
    now: float | None = None,
) -> dict[str, Any]:
    """Switch the run to the workflow token once the App's is older than 50 minutes (the
    module docstring): ``os.environ`` and ``env`` (when given) get it as ``GITHUB_TOKEN``
    and ``GH_TOKEN``, and ``root``'s persisted git credential (when given) points at it.
    Prints ``SWITCH_NOTE`` to stderr once per process. ``{"switched": False}`` before the
    deadline and without the App."""
    global _noted
    if not is_stale(env, now):
        return {"switched": False}
    workflow = _lookup(WORKFLOW_TOKEN_ENV, env)
    targets: list[MutableMapping[str, str]] = [os.environ]
    if env is not None and env is not os.environ:
        targets.append(env)
    for mapping in targets:
        for var in TOKEN_VARS:
            if mapping.get(var) != workflow:
                mapping[var] = workflow
    out: dict[str, Any] = {"switched": True}
    if root is not None:
        out["git_credential"] = replace_git_credential(Path(root), workflow)
    if not _noted:
        print(SWITCH_NOTE, file=sys.stderr)
        _noted = True
    return out


def session_tokens(env: Mapping[str, str]) -> dict[str, str]:
    """The GitHub tokens a model session gets: the workflow token as ``GITHUB_TOKEN`` and
    ``GH_TOKEN`` when the workflow handed it over (``SDLC_WORKFLOW_TOKEN``), else {} (the
    session keeps what it had). The session then never holds the App token through its
    environment, and nothing it does depends on the App token's lifetime; the credential
    ``actions/checkout`` persisted in ``.git/config`` stays readable to it."""
    workflow = str(env.get(WORKFLOW_TOKEN_ENV) or "").strip()
    return {var: workflow for var in TOKEN_VARS} if workflow else {}
