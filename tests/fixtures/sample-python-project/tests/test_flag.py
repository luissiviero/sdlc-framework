"""Fails on purpose when SAMPLE_FAIL=1, so integration tests can prove that the one-command
test target exits non-zero on failure (article p.27 step 1)."""

import os


def test_intentional_failure_behind_flag():
    assert os.environ.get("SAMPLE_FAIL") != "1", "SAMPLE_FAIL=1 makes this test fail on purpose"
