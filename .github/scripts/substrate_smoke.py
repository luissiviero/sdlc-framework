"""First proof of the execution substrate (build guide step 3, decision 1; step 30 says to
start with a read-only step, article p.41).

Runs one headless `claude -p` turn under a per-run budget with whichever credential the
workflow was given, and prints what the CLI reports. Either repository secret works
(docs/NOTES.md section 2):

- ``ANTHROPIC_API_KEY``      -> ``claude -p --bare ...`` (bare mode reads only the key;
                               billed per token, not against a plan window)
- ``CLAUDE_CODE_OAUTH_TOKEN`` -> ``claude -p ...`` (no ``--bare``: bare mode does not read
                               the token; the run draws on the owner's subscription window)

When both are present the key wins, as the CLI itself does in print mode ("the key is
always used when present"). Exit codes: 0 the turn succeeded; 1 the CLI reported an error
or returned no JSON; 2 no credential was given.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from collections.abc import Mapping, Sequence

PROMPT = "Reply with the single word OK. Do not use any tool."
# The outer bounds every phase job will carry (docs/NOTES.md section 10b).
BOUNDS = ["--model", "opus", "--max-turns", "2", "--max-budget-usd", "0.25"]


def choose_auth(env: Mapping[str, str]) -> tuple[str, list[str]] | None:
    """Return (label, extra CLI flags) for the credential present in ``env``, or None."""
    if env.get("ANTHROPIC_API_KEY"):
        return "api-key", ["--bare"]
    if env.get("CLAUDE_CODE_OAUTH_TOKEN"):
        return "subscription-token", []
    return None


def run(
    claude: Sequence[str] = ("claude",),
    env: Mapping[str, str] | None = None,
    out=sys.stdout,
) -> int:
    env = dict(os.environ if env is None else env)
    auth = choose_auth(env)
    if auth is None:
        print(
            "no credential: set the repository secret ANTHROPIC_API_KEY or "
            "CLAUDE_CODE_OAUTH_TOKEN (docs/NOTES.md section 2)",
            file=out,
        )
        return 2
    label, flags = auth
    argv = [*claude, "-p", *flags, *BOUNDS, "--output-format", "json", PROMPT]
    print("auth:", label, file=out)
    print("command:", " ".join(argv[len(claude) :]), file=out)
    proc = subprocess.run(argv, capture_output=True, text=True, env=env)
    try:
        data = json.loads(proc.stdout)
    except ValueError:
        print(f"no JSON result (exit {proc.returncode})", file=out)
        print(proc.stdout[-2000:], file=out)
        print(proc.stderr[-2000:], file=out)
        return 1
    print("total_cost_usd:", data.get("total_cost_usd"), file=out)
    print("models:", ", ".join(sorted(data.get("modelUsage", {}))) or "none", file=out)
    print("result:", data.get("result"), file=out)
    if data.get("is_error") or proc.returncode != 0:
        print(f"the turn failed (exit {proc.returncode})", file=out)
        return 1
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--claude", default="claude", help="the CLI executable (default: claude on PATH)"
    )
    args = parser.parse_args(argv)
    return run(claude=[args.claude])


if __name__ == "__main__":
    sys.exit(main())
