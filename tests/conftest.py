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

import os

import pytest

RUNNER_PREFIXES = ("GITHUB_", "RUNNER_", "ACTIONS_")
RUNNER_NAMES = ("CI", "SDLC_MODEL", "SDLC_DEFAULT_BRANCH")


def runner_variables(environ=None) -> list[str]:
    """The names in ``environ`` that a GitHub Actions runner sets and a test must not see."""
    environ = os.environ if environ is None else environ
    return sorted(
        name for name in environ if name.startswith(RUNNER_PREFIXES) or name in RUNNER_NAMES
    )


@pytest.fixture(autouse=True)
def _hook_log_in_tmp(tmp_path, monkeypatch):
    monkeypatch.setenv("SDLC_HOOK_LOG", str(tmp_path / "test-hook-log.jsonl"))
    for name in runner_variables():
        monkeypatch.delenv(name, raising=False)
    yield
