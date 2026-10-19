"""Prepares a runner of ``Framework checks`` before the suite runs (choice 235, 2026-10-19).

Run by every test job of ``.github/workflows/framework-checks.yml`` before it installs the dev
tools (and by hand: ``python .github/scripts/framework_checks_runner.py --dry-run``). The suite
starts about 44,000 git processes, and on Windows each one costs several times what it costs
on Linux. Two settings make them cheaper, on the runner only:

- **git's automatic maintenance off** (``maintenance.auto false``, ``gc.auto 0`` in the
  runner's global config): after a commit or a fetch, git starts ``git maintenance run
  --auto`` in the background, an extra process per command for repositories that live a few
  seconds. ``plugin/evals/run.py`` already turns it off in its fixture for the lock it leaves.
- **Defender's real-time scan off** on Windows (``Set-MpPreference
  -DisableRealtimeMonitoring``): every process start and every file a test writes is scanned.

Both are speed only: the runner is thrown away after the job and runs nothing but this
repository's checks, and no test reads either setting (a test that needs its own git config
sets ``GIT_CONFIG_GLOBAL``). So a setting that cannot be applied is reported and the job goes
on, slower, never red: exit 0 always. Nothing is changed on the owner's PC unless this script
is run there by hand.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from collections.abc import Callable

GIT_SETTINGS = (("maintenance.auto", "false"), ("gc.auto", "0"))
DEFENDER_OFF = (
    "Set-MpPreference -DisableRealtimeMonitoring $true; "
    "(Get-MpPreference).DisableRealtimeMonitoring"
)


def plan(windows: bool) -> list[tuple[str, list[str]]]:
    """(what, command) for every setting this runner takes, in order."""
    steps = [
        (f"git {key}={value}", ["git", "config", "--global", key, value])
        for key, value in GIT_SETTINGS
    ]
    if windows:
        command = ["powershell", "-NoProfile", "-NonInteractive", "-Command", DEFENDER_OFF]
        steps.append(("Defender real-time scan off", command))
    return steps


def apply(
    steps: list[tuple[str, list[str]]],
    run: Callable[..., subprocess.CompletedProcess] = subprocess.run,
) -> list[str]:
    """One line per step: ``applied`` or ``not applied`` with the reason."""
    lines = []
    for what, command in steps:
        try:
            proc = run(command, capture_output=True, text=True, timeout=120)
        except (OSError, subprocess.SubprocessError) as exc:
            lines.append(f"{what}: not applied ({type(exc).__name__}: {exc})")
            continue
        out = " ".join((proc.stdout or "").split())
        if proc.returncode != 0:
            err = " ".join((proc.stderr or "").split())[:300]
            lines.append(f"{what}: not applied (exit {proc.returncode}: {err})")
        else:
            lines.append(f"{what}: applied" + (f" ({out})" if out else ""))
    return lines


def main(
    argv: list[str] | None = None,
    run: Callable[..., subprocess.CompletedProcess] = subprocess.run,
) -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0])
    p.add_argument("--dry-run", action="store_true", help="print the plan, change nothing")
    p.add_argument("--windows", choices=("auto", "yes", "no"), default="auto")
    args = p.parse_args(argv)
    windows = os.name == "nt" if args.windows == "auto" else args.windows == "yes"
    steps = plan(windows)
    if args.dry_run:
        lines = [f"{what}: {' '.join(command)}" for what, command in steps]
    else:
        lines = apply(steps, run)
    print("\n".join(lines), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
