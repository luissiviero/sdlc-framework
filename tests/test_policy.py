"""gate/policy.py's identity helpers on their own (the plugin test coverage map of 2026-10-19,
`docs/reviews/2026-10-19-plugin-test-coverage.md`, gap 1): `is_automation` decides owner versus
automation for the gate's `owner_actions` check, and until now only the default GitHub Actions
identity was exercised, through that check. The trial pushes as the project's own GitHub App
(decision 33), whose commits carry `<app>[bot]@users.noreply.github.com`, so the suffix branch
is the one that matters there."""

from __future__ import annotations

import pytest

from gate import policy

DEFAULT = policy.DEFAULT_AUTOMATION_IDENTITY


@pytest.mark.parametrize(
    ("name", "email"),
    [
        ("github-actions[bot]", "41898282+github-actions[bot]@users.noreply.github.com"),
        ("github-actions[bot]", ""),  # the name alone is enough
        ("", "41898282+github-actions[bot]@users.noreply.github.com"),  # the email alone too
        ("GitHub-Actions[BOT]", ""),  # case does not matter
        ("  github-actions[bot]  ", ""),  # nor surrounding whitespace
        # an App the project did not list: the suffix makes it automation whatever the list
        ("sdlc-automation-x[bot]", "sdlc-automation-x[bot]@users.noreply.github.com"),
        ("", "12345+Some-App[bot]@users.noreply.github.com"),
        ("Some App", "  SOME-APP[BOT]@USERS.NOREPLY.GITHUB.COM  "),
    ],
)  # fmt: skip
def test_is_automation_matches_the_default_identity_and_every_app_bot_email(name, email):
    assert policy.is_automation(name, email, DEFAULT)


@pytest.mark.parametrize(
    ("name", "email"),
    [
        ("Luis", "luissiviero@users.noreply.github.com"),  # a person's noreply address
        ("github-actions", "ci@example.com"),  # the bot's name without "[bot]"
        ("github-actions[bot]@users.noreply.github.com", ""),  # the address in the name field
        ("", "github-actions[bot]@example.com"),  # the suffix must be GitHub's noreply domain
        ("", "[bot]@users.noreply.github.com.evil.example"),  # a longer host is not the suffix
        ("", ""),
        (None, None),
    ],
)
def test_is_automation_never_takes_the_owner_for_the_automation(name, email):
    assert not policy.is_automation(name, email, DEFAULT)


def test_is_automation_honours_a_custom_list_and_still_the_suffix():
    custom = ["release-robot", "robot@example.com"]
    assert policy.is_automation("release-robot", "someone@example.com", custom)
    assert policy.is_automation("Someone", "ROBOT@example.com", custom)
    # the default identity is not in the custom list, but its email carries the suffix
    assert policy.is_automation(
        "github-actions[bot]", "41898282+github-actions[bot]@users.noreply.github.com", custom
    )
    assert not policy.is_automation("github-actions[bot]", "", custom)  # the name alone is not
    assert not policy.is_automation("Luis", "luis@example.com", custom)
    assert not policy.is_automation("", "", [])  # an empty list matches nobody by name


@pytest.mark.parametrize(
    "config",
    [
        {},
        {"automation_identity": None},
        {"automation_identity": []},
        {"automation_identity": ["", "   "]},  # blanks only: as if unset
        {"automation_identity": "release-robot"},  # not a list: ignored, never split
    ],
)
def test_automation_identity_falls_back_to_the_default_list(config):
    assert policy.automation_identity(config) == DEFAULT
    assert policy.automation_identity(config) is not DEFAULT  # a copy the caller may edit


def test_automation_identity_reads_the_owner_s_list_trimmed():
    config = {"automation_identity": [" release-robot ", 42, "", "robot@example.com"]}
    assert policy.automation_identity(config) == ["release-robot", "42", "robot@example.com"]
