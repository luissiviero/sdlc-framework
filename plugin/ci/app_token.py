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

The model's session never holds the App's token: its environment carries the workflow token
(``session_tokens``) and, while it runs, so does the persisted credential
(``session_credential``); the session's own pushes start no workflow run without the owner's
approval, as before decision 33, and only the runner's publications after the session carry
the App's identity.

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
import contextlib
import math
import os
import subprocess
import sys
import time
import urllib.parse
from collections.abc import Iterator, Mapping, MutableMapping
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
# actions/checkout's own placeholder (configureToken): the value goes in through the file
PLACEHOLDER = "AUTHORIZATION: basic ***"
DEFAULT_SERVER_URL = "https://github.com"

_noted = False
_replaced: set[tuple[str, str]] = set()  # (checkout, credential key) already switched


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
    memo = (str(root.resolve()), credential_key())
    if memo in _replaced:
        return "already"
    done = _set_credential(root, credential_value(token))
    if done in ("replaced", "already"):
        _replaced.add(memo)
    return done


def _persisted(root: Path) -> list[str] | None:
    """The persisted header values, in order, or None when the key is not set."""
    code, out = _git(root, "config", "--local", "--get-all", credential_key())
    return out.splitlines() if code == 0 else None  # exit 1: the key is not set


def _set_credential(root: Path, value: str, create: bool = False) -> str:
    """Make ``value`` the key's one value, as actions/checkout writes it (a placeholder
    through ``git config``, then the file edited: the token never on a command line). A key
    that is not set is left unset ("none") unless ``create``."""
    key = credential_key()
    values = _persisted(root)
    if values is None and not create:
        return "none"
    if values == [value]:
        return "already"
    code, path = _git(root, "rev-parse", "--git-path", "config")
    if code != 0 or not path.strip():
        return f"failed: the checkout's config file was not found ({path.strip()})"
    config = (root / path.strip()).resolve()
    code, why = _git(root, "config", "--local", "--replace-all", key, PLACEHOLDER)
    if code != 0:
        return f"failed: git config exited {code}: {why.strip()}"
    try:
        # newline="": the file keeps its own line endings (CRLF on a Windows checkout)
        with config.open(encoding="utf-8", newline="") as handle:
            text = handle.read()
        if text.count(PLACEHOLDER) != 1:
            return f"failed: the placeholder is not in {config} exactly once"
        with config.open("w", encoding="utf-8", newline="") as handle:
            handle.write(text.replace(PLACEHOLDER, value))
    except OSError as exc:
        return f"failed: {exc}"
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
    _switch_env(workflow, env)
    out: dict[str, Any] = {"switched": True}
    if root is not None:
        out["git_credential"] = replace_git_credential(Path(root), workflow)
    if not _noted:
        print(SWITCH_NOTE, file=sys.stderr)
        _noted = True
    return out


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


class CredentialError(RuntimeError):
    """The checkout's credential could neither be pointed at the workflow token nor removed
    before a session: the session does not start (it would hold the App's token)."""


def _credential_config_problem(root: Path) -> str:
    """ "the git config carries <key> (<scope>), ..." for the keys of the git config, as git
    resolves it in ``root`` (worktree, local and global scopes), that would redirect or
    unprotect the runner's next push, or what git said when it refused the listing; "" when
    there is none
    (``ci/checkout_check.py config_findings``: a proxy, TLS verification switched off or
    another CA, a URL rewrite, an include, a credential helper, a worktree config...). The
    runner image's own global proxy, if it has one, reads the same: the run then stays on
    the workflow token, which is why the line names the key and its scope, not the session."""
    from ci import checkout_check  # noqa: PLC0415 - checkout_check imports this module

    found = checkout_check.config_findings(root, checkout_check.CREDENTIAL_SCOPES)
    if not found:
        return ""
    if found[0][0] == checkout_check.UNLISTED:
        return found[0][1]
    return "the git config carries " + ", ".join(f"{name} ({scope})" for scope, name in found)


def _settle(checkout: Path, value: str) -> str:
    """Write the credential after a session; a write that fails (a planted placeholder, a
    locked file) removes the key rather than leave a bare placeholder, and says so: the
    runner's pushes from this checkout then fail visibly instead of going out wrong."""
    result = _set_credential(checkout, value, create=True)
    if result in ("replaced", "already", "none"):
        return result
    code, why = _git(checkout, "config", "--local", "--unset-all", credential_key())
    left = "removed" if code == 0 else f"left as it is (git config exited {code}: {why.strip()})"
    print(
        f"the checkout's git credential could not be written after the session ({result}): "
        f"the key is {left}; the runner's pushes from this checkout have no credential",
        file=sys.stderr,
    )
    return result


@contextlib.contextmanager
def session_credential(
    root: Path | str | None, env: MutableMapping[str, str] | None = None
) -> Iterator[dict[str, Any]]:
    """Around a model session: the checkout's persisted credential carries the workflow
    token while the session runs, so the session never holds the App's token, in its
    environment (``session_tokens``) or in ``.git/config``, and its own pushes go out on the
    workflow token, which starts no run without the owner's approval (as before decision 33)
    and does not expire with the App's. Afterwards the App's header comes back while that
    token is fresh; once it is stale the run stays on the workflow token
    (``fall_back_if_stale``). Restored in a ``finally``, so a session that crashed or timed
    out restores too. The App's header comes back only into a clean git config, judged as
    git resolves it (``_credential_config_problem``: worktree, local and global scopes): a
    proxy, TLS verification off or another CA, wherever it was written (by the session, or
    the runner image's own global config), keeps the run on the workflow token, with one
    stderr line naming the key and its scope, and the project's CI on that head waits for
    the owner's approval, as in the fallback. A write that fails after the session removes
    the key and says so (``_settle``). A no-op without ``SDLC_WORKFLOW_TOKEN`` or without a
    persisted credential. Raises ``CredentialError`` before the session when the credential
    can neither be switched nor removed."""
    workflow = _lookup(WORKFLOW_TOKEN_ENV, env)
    checkout = Path(root) if root is not None else None
    before = _persisted(checkout) if workflow and checkout is not None else None
    if checkout is None or not before:
        yield {"session_credential": "unchanged"}
        return
    during = _set_credential(checkout, credential_value(workflow))
    if during not in ("replaced", "already"):
        # fail closed: the session starts with no persisted credential at all and cannot
        # push; the runner publishes after it, so nothing is lost but the session's own pushes
        code, why = _git(checkout, "config", "--local", "--unset-all", credential_key())
        if code != 0:
            raise CredentialError(
                f"the session's git credential could not be switched ({during}) nor removed "
                f"(git config exited {code}: {why.strip()}): the session does not start"
            )
        during = "removed"
    try:
        yield {"session_credential": during}
    finally:
        _replaced.discard((str(checkout.resolve()), credential_key()))
        problem = _credential_config_problem(checkout)
        if problem:
            print(
                f"{problem}: the workflow token publishes this run (decision 33); the "
                "project's CI on this head waits for the owner's approval",
                file=sys.stderr,
            )
            _switch_env(workflow, env)
            _settle(checkout, credential_value(workflow))
        elif is_stale(env):
            if _settle(checkout, credential_value(workflow)) in ("replaced", "already"):
                fall_back_if_stale(checkout, env)
            else:
                _switch_env(workflow, env)
        else:
            _settle(checkout, before[-1])  # the App's header, still fresh


def session_tokens(env: Mapping[str, str]) -> dict[str, str]:
    """The GitHub tokens a model session gets: the workflow token as ``GITHUB_TOKEN`` and
    ``GH_TOKEN`` when the workflow handed it over (``SDLC_WORKFLOW_TOKEN``), else {} (the
    session keeps what it had); ``session_credential`` does the same for ``.git/config``."""
    workflow = str(env.get(WORKFLOW_TOKEN_ENV) or "").strip()
    return {var: workflow for var in TOKEN_VARS} if workflow else {}
