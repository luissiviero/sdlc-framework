"""Install the project's own toolchain before a phase runs (build guide step 30).

    python framework/plugin/ci/project_setup.py --root .

A GitHub-hosted runner carries neither the project nor the tools its targets call: the first
live design run (2026-09-21) parked at gate (b) because ``python -m pytest`` answered
``/usr/bin/python: No module named pytest``. The phase job therefore runs this step between
the runner setup and ``run_phase.py``.

It reads one line of configuration, ``sdlc.yaml: commands.setup`` — the one-command install
/sdlc-init detects (``python -m pip install -e ".[dev]"``, ``npm ci``, ...). An empty value
means the project has nothing to install and is not an error. The command runs through the
platform shell, like the gate's own targets, so the same line works on Windows and on a
Linux runner.

Prints JSON. Exit 0 when the command exited 0 or there was nothing to run, 1 when it failed
or timed out, 2 on a usage error.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

PLUGIN_DIR = Path(__file__).resolve().parent.parent  # <framework root>/plugin
if str(PLUGIN_DIR) not in sys.path:
    sys.path.insert(0, str(PLUGIN_DIR))

from gate.checks import run_command  # noqa: E402
from hooks._common import ConfigError, load_sdlc_config  # noqa: E402

EXIT_OK, EXIT_FAILED, EXIT_USAGE = 0, 1, 2
TIMEOUT_SECONDS = 15 * 60  # an install, not a build: fifteen minutes is generous
OUTPUT_TAIL = 4000  # characters of output kept in the JSON result
NOTHING_TO_RUN = "no setup command"


def setup_command(config: dict[str, Any]) -> str:
    """``sdlc.yaml: commands.setup``, or "" when the project declares none."""
    cmds = config.get("commands")
    value = cmds.get("setup") if isinstance(cmds, dict) else None
    return value.strip() if isinstance(value, str) else ""


def run_setup(root: Path, timeout: int = TIMEOUT_SECONDS) -> tuple[dict[str, Any], int]:
    """(result, exit code). A project with no setup command is skipped, not failed."""
    root = Path(root).resolve()
    try:
        config = load_sdlc_config(str(root)) or {}
    except ConfigError as exc:
        return {"error": f"sdlc.yaml is unreadable: {exc}"}, EXIT_FAILED
    command = setup_command(config)
    if not command:
        return {"skipped": NOTHING_TO_RUN}, EXIT_OK
    run = run_command(command, root, timeout, tail=OUTPUT_TAIL)
    exit_code = run.get("exit_code")
    result = {
        "command": command,
        "exit_code": exit_code,
        "output": run.get("output", ""),
        "ok": exit_code == 0,
        "timeout": timeout if exit_code is None else None,
    }
    return result, EXIT_OK if exit_code == 0 else EXIT_FAILED


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="sdlc-project-setup",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--root", default=".", help="the project checkout")
    p.add_argument(
        "--timeout",
        type=int,
        default=TIMEOUT_SECONDS,
        help=f"seconds the install may take (default {TIMEOUT_SECONDS})",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.timeout <= 0:
        print("--timeout must be a positive number of seconds", file=sys.stderr)
        return EXIT_USAGE
    result, code = run_setup(Path(args.root), args.timeout)
    print(json.dumps(result, indent=2, sort_keys=True))
    return code


if __name__ == "__main__":
    sys.exit(main())
