"""Which credential an unattended ``claude -p`` run uses, and whether it runs in bare mode.

One definition for the whole framework (docs/NOTES.md section 2; OPERATING_MODEL section
4.2). ``.github/scripts/substrate_smoke.py`` — the first proof of the substrate, build guide
step 3 — and ``plugin/ci/run_phase.py`` both call it, so the smoke run and the phase jobs can
never disagree about which secret wins.

The rule, from the documentation quoted in NOTES section 2:

- ``ANTHROPIC_API_KEY`` present -> ``claude -p --bare``. Bare mode "is the recommended mode
  for scripted and SDK calls" and reads only the key; the spend is billed per token, capped
  by the workspace limit and by ``--max-budget-usd``.
- otherwise ``CLAUDE_CODE_OAUTH_TOKEN`` present -> ``claude -p`` **without** ``--bare``,
  because "Bare mode does not read ``CLAUDE_CODE_OAUTH_TOKEN``"; the run draws on the
  owner's subscription window.
- neither -> no run is possible.

When both are set the key wins, as the CLI itself does in print mode ("the key is always
used when present"). No value is ever read, printed or returned here: only the variable
names are looked at.
"""

from __future__ import annotations

from collections.abc import Mapping

API_KEY_VAR = "ANTHROPIC_API_KEY"
OAUTH_TOKEN_VAR = "CLAUDE_CODE_OAUTH_TOKEN"
CREDENTIAL_VARS = (API_KEY_VAR, OAUTH_TOKEN_VAR)

# The labels the smoke script has printed since step 3; kept so its output does not change.
LABELS = {"api_key": "api-key", "oauth": "subscription-token", None: "none"}


def choose_auth(env: Mapping[str, str]) -> dict:
    """``{"auth": "api_key" | "oauth" | None, "bare": bool, "reason": str}``."""
    if env.get(API_KEY_VAR):
        return {
            "auth": "api_key",
            "bare": True,
            "reason": (
                f"{API_KEY_VAR} is set: bare mode, billed per token and capped by "
                "--max-budget-usd (NOTES section 2). The key wins when both secrets exist."
            ),
        }
    if env.get(OAUTH_TOKEN_VAR):
        return {
            "auth": "oauth",
            "bare": False,
            "reason": (
                f"{OAUTH_TOKEN_VAR} is set and {API_KEY_VAR} is not: no --bare, because bare "
                "mode does not read the token; the run draws on the subscription window."
            ),
        }
    return {
        "auth": None,
        "bare": False,
        "reason": (
            f"no credential: set the repository secret {API_KEY_VAR} or {OAUTH_TOKEN_VAR} "
            "(docs/NOTES.md section 2)"
        ),
    }


def credential_env(env: Mapping[str, str]) -> dict:
    """A copy of ``env`` carrying the chosen credential and not the other one.

    The phase jobs hand Claude Code exactly one credential (article p.40: "short-lived
    scoped tokens"), so a run can never fall back to the secret the framework did not pick.
    """
    chosen = choose_auth(env)
    out = {k: v for k, v in env.items() if k not in CREDENTIAL_VARS}
    if chosen["auth"] == "api_key":
        out[API_KEY_VAR] = env[API_KEY_VAR]
    elif chosen["auth"] == "oauth":
        out[OAUTH_TOKEN_VAR] = env[OAUTH_TOKEN_VAR]
    return out


def flags(env: Mapping[str, str]) -> list[str]:
    """The extra ``claude`` flags the chosen credential implies (``--bare`` or nothing)."""
    return ["--bare"] if choose_auth(env)["bare"] else []


def label(env: Mapping[str, str]) -> str:
    return LABELS[choose_auth(env)["auth"]]
