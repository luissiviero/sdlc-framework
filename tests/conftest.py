"""Shared test setup.

Every hook logs every decision since plugin 0.2.19 (build guide step 41.1), to
``$SDLC_HOOK_LOG`` when set and otherwise to the nearest project's ``changes/`` folder — which,
for a test that runs a hook as a subprocess from this repository, is this repository. The
fixture below points the log at the test's own temporary directory so no test leaves a
``changes/.hook-log.jsonl`` behind; a test that asserts the default location passes its own
``env`` and is unaffected.
"""

from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _hook_log_in_tmp(tmp_path, monkeypatch):
    monkeypatch.setenv("SDLC_HOOK_LOG", str(tmp_path / "test-hook-log.jsonl"))
    yield
