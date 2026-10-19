"""Shared test setup.

Every hook logs every decision since plugin 0.2.19 (build guide step 41.1), to
``$SDLC_HOOK_LOG`` when set and otherwise to the nearest project's ``changes/`` folder — which,
for a test that runs a hook as a subprocess from this repository, is this repository. The
fixture below points the log at the test's own temporary directory so no test leaves a
``changes/.hook-log.jsonl`` behind; a test that asserts the default location passes its own
``env`` and is unaffected.

``$SDLC_DEFAULT_BRANCH`` is removed too: ``gitops.default_branch`` prefers it over the git
guess, and a value leaking in from a runner would change every test that reads the default
branch.

The runner's own variables are removed the same way (0.2.28, the first run of the suite in
GitHub Actions, `.github/workflows/framework-checks.yml`): ``GITHUB_*`` (``GITHUB_ACTIONS``
switches the runner-only refusals on, ``GITHUB_REF_NAME`` is the pull request's ``N/merge``
and the tag script refused it as "not the default branch", ``GITHUB_REPOSITORY`` and
``GITHUB_OUTPUT`` reach every subprocess a test starts), ``RUNNER_*``, ``ACTIONS_*``, ``CI``
and ``SDLC_MODEL``. A test that needs one sets it itself, on ``os.environ`` through
``monkeypatch`` or in the ``env`` it passes, so the suite reads the same on the owner's PC, in
a cloud session and on a runner; ``tests/test_scaffold.py`` asserts the environment is clean.
"""

from __future__ import annotations

import email.message
import io
import os
import urllib.error
import urllib.parse
import urllib.request
import zlib

import pytest

from tests import fixture_repos

RUNNER_PREFIXES = ("GITHUB_", "RUNNER_", "ACTIONS_")
# ``SDLC_GATE_COMMANDS`` is the mark the runner sets in a CI session's environment (0.3.0,
# issue #91): every process of that session inherits it, this suite included when it runs as
# a project's test target, and two gate tests read the gate's answer to it; the App token's
# mint time and the workflow token the eight App workflows export (decision 33, R49) would
# switch the tokens of a test process
RUNNER_NAMES = (
    "CI",
    "SDLC_MODEL",
    "SDLC_DEFAULT_BRANCH",
    "SDLC_GATE_COMMANDS",
    "SDLC_APP_TOKEN_MINTED_AT",
    "SDLC_WORKFLOW_TOKEN",
)


def runner_variables(environ=None) -> list[str]:
    """The names in ``environ`` that a GitHub Actions runner sets and a test must not see."""
    environ = os.environ if environ is None else environ
    return sorted(
        name for name in environ if name.startswith(RUNNER_PREFIXES) or name in RUNNER_NAMES
    )


@pytest.fixture(autouse=True, scope="session")
def _fixture_repos(tmp_path_factory):
    """The fixture repositories are built once per session (``tests/fixture_repos.py``),
    under the environment every test starts from: the runner's variables removed, the hook
    log in the session's own temporary directory."""
    environ = {
        name: value
        for name, value in os.environ.items()
        if name not in runner_variables() and name != SHARD_VARIABLE
    }
    log_dir = tmp_path_factory.mktemp("fixture-repos-log")
    environ["SDLC_HOOK_LOG"] = str(log_dir / "test-hook-log.jsonl")
    fixture_repos.configure(tmp_path_factory, environ)
    yield


@pytest.fixture(autouse=True)
def _hook_log_in_tmp(tmp_path, monkeypatch):
    monkeypatch.setenv("SDLC_HOOK_LOG", str(tmp_path / "test-hook-log.jsonl"))
    for name in runner_variables():
        monkeypatch.delenv(name, raising=False)
    monkeypatch.delenv(SHARD_VARIABLE, raising=False)
    yield


# --- no real network (2026-10-19) ---------------------------------------------------------------
# A test that hands the runner a fake token and stubs nothing reached the real api.github.com:
# 40 tests sent 673 requests to `repos/owner/name` (17 labels per `run_phase` run alone), about
# a fifth of the suite's time, and every one came back 401 "Bad credentials". The fixture below
# answers that 401 at once, in-process, so every test reads the same answer as before without
# the round trip, and no token a developer exported (`GH_TOKEN`) leaves the machine. Loopback
# still goes through (`tests/test_app_token.py` runs a local server). A test that needs another
# answer patches `pr/github.py`'s `_request` or `urllib.request.urlopen` itself, after this.
# A process a test starts is not covered: one test of `tests/test_ci_end_to_end.py` still sends
# 25 requests from its subprocesses.
LOOPBACK_HOSTS = frozenset({"127.0.0.1", "localhost", "::1"})
_real_urlopen = urllib.request.urlopen


def refused_urlopen(request, *args, **kwargs):
    """``urllib.request.urlopen`` for tests: loopback as usual, anything else a 401."""
    url = request.full_url if isinstance(request, urllib.request.Request) else str(request)
    if urllib.parse.urlsplit(url).hostname in LOOPBACK_HOSTS:
        return _real_urlopen(request, *args, **kwargs)
    body = io.BytesIO(b'{"message": "Bad credentials"}')
    raise urllib.error.HTTPError(url, 401, "Unauthorized", email.message.Message(), body)


@pytest.fixture(autouse=True)
def _no_real_network(monkeypatch):
    monkeypatch.setattr(urllib.request, "urlopen", refused_urlopen)


# --- shards (2026-10-19) --------------------------------------------------------------------------
# The Windows job of framework-checks.yml runs the suite in shards on parallel runners:
# `FRAMEWORK_TEST_SHARD=<i>/<n>` keeps the tests whose node id hashes to shard i of n (crc32,
# the same on every process and platform, so xdist's workers agree on the collection). Every
# test lands in exactly one shard (`tests/test_scaffold.py`). Unset, nothing is deselected; a
# malformed value stops the run instead of quietly running nothing.
SHARD_VARIABLE = "FRAMEWORK_TEST_SHARD"


def parse_shard(value: str) -> tuple[int, int]:
    """``"i/n"`` as (i, n), 1 <= i <= n; ValueError otherwise."""
    index, _, count = value.partition("/")
    i, n = int(index), int(count)
    if not 1 <= i <= n:
        raise ValueError(f"shard {i} of {n}")
    return i, n


def in_shard(nodeid: str, index: int, count: int) -> bool:
    return zlib.crc32(nodeid.encode("utf-8")) % count == index - 1


def pytest_collection_modifyitems(config, items):
    value = os.environ.get(SHARD_VARIABLE, "").strip()
    if not value:
        return
    try:
        index, count = parse_shard(value)
    except ValueError as exc:
        raise pytest.UsageError(f"{SHARD_VARIABLE}={value!r}: want i/n, 1 <= i <= n") from exc
    kept = [item for item in items if in_shard(item.nodeid, index, count)]
    dropped = [item for item in items if not in_shard(item.nodeid, index, count)]
    if dropped:
        config.hook.pytest_deselected(items=dropped)
    items[:] = kept
