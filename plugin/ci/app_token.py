"""The automation's GitHub token (decision 33; ROADMAP R49): which token publishes, and how git
gets it - through the environment only, never from a file.

The eight workflows that push or open pull requests mint the project's GitHub App token in
their first step (``actions/create-github-app-token``), and the job then pushes, opens pull
requests and dispatches with it. An installation token expires one hour after it is minted
(the action's README: "An installation access token expires after 1 hour"), while a phase
job may run for more than three hours, and the runner publishes at the end of the session.
So the workflow records when it minted the token (``SDLC_APP_TOKEN_MINTED_AT``, epoch
seconds, through ``$GITHUB_ENV``) and hands every publishing step the workflow token too
(``SDLC_WORKFLOW_TOKEN``). Once the App token is older than ``MAX_AGE_SECONDS``,
``fall_back_if_stale`` switches ``GITHUB_TOKEN`` and ``GH_TOKEN`` to the workflow token, in
``os.environ`` (what ``pr/github.py``, ``gh`` and every plugin CLI the runner starts read)
and in the env dict the caller passes. The cost is the one decision 33 removed: the
project's CI on a head the workflow token pushed waits for the owner's approval
(``docs/notes/23.md``).

**No credential on disk.** Every project checkout runs with ``persist-credentials: false``,
so ``.git/config`` holds no token that project code (the session's tests the commands step
runs, a ``setup.py`` the toolchain install runs), a planted hook or a planted config key
could reach. Each git network call of the runner gets the credential in its own environment
instead (``git_auth_env``): git's command-scope config (``GIT_CONFIG_COUNT``,
``GIT_CONFIG_KEY_<n>``, ``GIT_CONFIG_VALUE_<n>``, git 2.31+), appended to any such entries
already there, setting ``http.<server>/.extraheader`` to ``AUTHORIZATION: basic
base64(x-access-token:<token>)`` - the header ``actions/checkout@v5`` would have persisted
(``src/git-auth-helper.ts``, ``configureToken``). An empty value first resets the header list
(git's documented reset for ``http.extraHeader``), so a header a file carries is never sent
beside it. The model's session gets the workflow token's header (``session_env``), never the
App's; the commands step, the toolchain install and the judge get none (``strip_git_auth``).
Only on a runner (``GITHUB_ACTIONS``): by hand the owner's own git credentials apply.
``actions/checkout@v6`` persists its credential in a separate included file; with
``persist-credentials: false`` that difference does not arise.

Standard library only: this module imports nothing of the plugin.
"""

from __future__ import annotations

import base64
import math
import os
import re
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
FUTURE_SKEW_SECONDS = 5 * 60  # a mint time further ahead than this is not a time
SWITCH_NOTE = (
    "the App token is older than 50 minutes: the workflow token publishes this run "
    "(decision 33); the project's CI on this head waits for the owner's approval"
)
DEFAULT_SERVER_URL = "https://github.com"
COUNT_ENV = "GIT_CONFIG_COUNT"
KEY_ENV = "GIT_CONFIG_KEY_{n}"
VALUE_ENV = "GIT_CONFIG_VALUE_{n}"
MIN_GIT = (2, 31)  # GIT_CONFIG_COUNT and its pairs (git 2.31.0 release notes)
# GitAuthError is deliberately not a ``state/gitops.py GitError``: callers that catch a
# failed git command and carry on (``check=False``, a park) must not swallow it - a git that
# cannot take its credential fails the run loudly, closed, before anything is pushed.
EXTRAHEADER_RE = re.compile(r"^https?\..*extraheader$", re.IGNORECASE)

_noted = False
_git_version: tuple[int, int] | None = None
# the git config finding that took this process off the App's token (never a clean result:
# the session could plant a key later)
_tainted: str | None = None


class GitAuthError(RuntimeError):
    """git cannot take its credential through the environment (older than 2.31, or a
    ``GIT_CONFIG_COUNT`` that is not a number): the run fails loudly rather than push with
    no credential or with a wrong one."""


def _lookup(name: str, env: Mapping[str, str] | None) -> str:
    return str((env or {}).get(name) or os.environ.get(name) or "").strip()


def is_stale(env: Mapping[str, str] | None = None, now: float | None = None) -> bool:
    """True when the App's token was minted more than ``MAX_AGE_SECONDS`` ago and the
    workflow token is there to take over; False without the App or without that token. A
    mint time that does not parse, is not finite or lies more than ``FUTURE_SKEW_SECONDS``
    ahead counts as stale: the App's token is of unknown age, and the workflow token is
    the one that surely works (fail towards the token that publishes)."""
    minted, workflow = _lookup(MINTED_AT_ENV, env), _lookup(WORKFLOW_TOKEN_ENV, env)
    if not minted or not workflow:
        return False
    try:
        minted_at = float(minted)
    except ValueError:
        return True
    if not math.isfinite(minted_at):
        return True
    current = time.time() if now is None else now
    if minted_at - current > FUTURE_SKEW_SECONDS:
        return True
    return current - minted_at > MAX_AGE_SECONDS


def fall_back_if_stale(
    env: MutableMapping[str, str] | None = None, now: float | None = None
) -> dict[str, Any]:
    """Switch the run to the workflow token once the App's is older than 50 minutes:
    ``os.environ`` and ``env`` (when given) get it as ``GITHUB_TOKEN`` and ``GH_TOKEN``, and
    every later ``git_auth_env`` hands it to git. Prints ``SWITCH_NOTE`` to stderr once per
    process. Idempotent and cheap; ``{"switched": False}`` before the deadline and without
    the App."""
    global _noted
    if not is_stale(env, now):
        return {"switched": False}
    _switch_env(_lookup(WORKFLOW_TOKEN_ENV, env), env)
    if not _noted:
        print(SWITCH_NOTE, file=sys.stderr)
        _noted = True
    return {"switched": True}


def _switch_env(workflow: str, env: MutableMapping[str, str] | None) -> None:
    """``GITHUB_TOKEN`` and ``GH_TOKEN`` become the workflow token in ``os.environ`` and in
    ``env`` (when given)."""
    targets: list[MutableMapping[str, str]] = [os.environ]
    if env is not None and env is not os.environ:
        targets.append(env)
    for mapping in targets:
        for var in TOKEN_VARS:
            if mapping.get(var) != workflow:
                mapping[var] = workflow


def _config_finding(root: Path) -> str:
    """ "the git config carries <key> (<scope>), ..." for the keys of the git config, as git
    resolves it in ``root`` (worktree, local and global scopes; ``ci/checkout_check.py
    config_findings``), that would send a push elsewhere or unprotected - a proxy, TLS
    verification off or another CA, a URL rewrite, an include, a credential helper - or what
    git said when it refused the listing; "" when there is none."""
    from ci import checkout_check  # noqa: PLC0415 - checkout_check imports this module

    found = checkout_check.config_findings(root)
    if not found:
        return ""
    if found[0][0] == checkout_check.UNLISTED:
        return found[0][1]
    return "the git config carries " + ", ".join(f"{name} ({scope})" for scope, name in found)


def credential_key(server_url: str | None = None) -> str:
    """The config key ``actions/checkout`` uses for the token:
    ``http.<scheme>://<host>/.extraheader``."""
    parts = urllib.parse.urlsplit(
        server_url or os.environ.get("GITHUB_SERVER_URL") or DEFAULT_SERVER_URL
    )
    return f"http.{parts.scheme}://{parts.netloc}/.extraheader"


def credential_value(token: str) -> str:
    basic = base64.b64encode(f"x-access-token:{token}".encode()).decode("ascii")
    return f"AUTHORIZATION: basic {basic}"


def _require_git_config_env() -> None:
    global _git_version
    if _git_version is None:
        try:
            out = subprocess.run(
                ["git", "version"], capture_output=True, text=True, encoding="utf-8", check=False
            ).stdout
        except OSError as exc:
            raise GitAuthError(f"git cannot be started: {exc}") from exc
        found = re.search(r"(\d+)\.(\d+)", out or "")
        _git_version = (int(found.group(1)), int(found.group(2))) if found else (0, 0)
    if _git_version < MIN_GIT:
        have = ".".join(map(str, _git_version))
        raise GitAuthError(
            f"git {have} cannot take its credential through the environment "
            f"(GIT_CONFIG_COUNT needs git {'.'.join(map(str, MIN_GIT))}+): no credential is "
            "persisted in .git/config, so the runner's push or fetch cannot authenticate"
        )


def git_auth_env(
    env: Mapping[str, str] | None = None,
    token: str | None = None,
    root: Path | str | None = None,
) -> dict[str, str]:
    """The environment entries that hand git its credential for one call in ``root`` (the
    working directory when None), to merge into ``env`` (``os.environ`` when None) - never
    written to a file. ``token`` is the token to hand out; without it, the App's while fresh
    and while the git config is clean, else the workflow token (``fall_back_if_stale``),
    else ``GITHUB_TOKEN``/``GH_TOKEN`` as the job set them.

    The App's token goes out only through a clean git config (the R49 review, fix round 5):
    a session can plant ``http.<url>.proxy`` or ``sslVerify=false`` in ``.git/config``, an
    include or the worktree file, and a command-scope value cannot reliably beat a more
    specific URL subsection. So before handing out the App's token the config is judged as
    git resolves it (one ``git config --list --show-scope``, every call: the session could
    plant a key later); a finding, or a listing git refused, hands out the workflow token
    instead, switches ``GITHUB_TOKEN`` and ``GH_TOKEN`` with it (the API calls follow) and
    sticks for the process, with one stderr line naming the key and its scope.

    Appends to the ``GIT_CONFIG_COUNT`` entries ``env`` already carries. {} by hand (no
    ``GITHUB_ACTIONS``) and without a token. Raises ``GitAuthError`` when git is older than
    2.31."""
    global _tainted
    base = os.environ if env is None else env
    if not str(base.get("GITHUB_ACTIONS") or "").strip():
        return {}
    mutable = env if isinstance(env, MutableMapping) else None
    if token is None:
        fall_back_if_stale(mutable)
        workflow = _lookup(WORKFLOW_TOKEN_ENV, env)
        token = _lookup("GITHUB_TOKEN", env) or _lookup("GH_TOKEN", env)
        app_in_use = bool(_lookup(MINTED_AT_ENV, env) and workflow and token != workflow)
        if app_in_use:
            finding = _tainted or _config_finding(Path(root) if root is not None else Path.cwd())
            if finding:
                if _tainted is None:
                    print(
                        f"{finding}: the workflow token publishes this run (decision 33); the "
                        "project's CI on this head waits for the owner's approval",
                        file=sys.stderr,
                    )
                _tainted = finding
                _switch_env(workflow, mutable)
                token = workflow
    if not token:
        return {}
    _require_git_config_env()
    raw = str(base.get(COUNT_ENV) or "0").strip()
    try:
        count = int(raw)
    except ValueError as exc:
        raise GitAuthError(f"{COUNT_ENV}={raw!r} is not a number") from exc
    key = credential_key(base.get("GITHUB_SERVER_URL"))
    # the empty value resets the header list (a header a file carries is never sent beside)
    return {
        COUNT_ENV: str(count + 2),
        KEY_ENV.format(n=count): key,
        VALUE_ENV.format(n=count): "",
        KEY_ENV.format(n=count + 1): key,
        VALUE_ENV.format(n=count + 1): credential_value(token),
    }


def strip_git_auth(env: Mapping[str, str]) -> dict[str, str]:
    """``env`` without any git credential handed through the environment: every
    ``GIT_CONFIG_KEY_<n>`` that sets an ``extraheader`` is dropped with its value, and the
    other pairs are renumbered so the rest of the command-scope config still applies."""
    out = {
        k: v
        for k, v in env.items()
        if k != COUNT_ENV and not k.startswith(("GIT_CONFIG_KEY_", "GIT_CONFIG_VALUE_"))
    }
    try:
        count = int(str(env.get(COUNT_ENV) or "0").strip())
    except ValueError:
        return out  # not git's to read either: no pair applies
    kept = 0
    for n in range(count):
        key = env.get(KEY_ENV.format(n=n))
        if key is None or EXTRAHEADER_RE.match(key):
            continue
        out[KEY_ENV.format(n=kept)] = key
        out[VALUE_ENV.format(n=kept)] = env.get(VALUE_ENV.format(n=n), "")
        kept += 1
    if kept:
        out[COUNT_ENV] = str(kept)
    return out


def session_tokens(env: Mapping[str, str]) -> dict[str, str]:
    """The GitHub tokens a model session gets: the workflow token as ``GITHUB_TOKEN`` and
    ``GH_TOKEN`` when the workflow handed it over (``SDLC_WORKFLOW_TOKEN``), else {} (the
    session keeps what it had, the workflow token in the workflows that mint no App token);
    ``run_phase.session_env`` adds its git header (``git_auth_env``)."""
    workflow = str(env.get(WORKFLOW_TOKEN_ENV) or "").strip()
    return {var: workflow for var in TOKEN_VARS} if workflow else {}
