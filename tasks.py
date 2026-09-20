"""Task runner for the SDLC framework repo (decision 7: one runner, Windows and Linux).

Usage: python tasks.py <task>
Tasks: test | lint | format | check | help

Everything runs through ``sys.executable -m ...`` with argument lists (no shell), so the
same file works in cmd.exe, PowerShell, Git Bash and a Linux runner.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def _run(*args: str) -> int:
    cmd = [sys.executable, "-m", *args]
    print("$", " ".join(cmd), flush=True)
    return subprocess.call(cmd, cwd=ROOT)


def task_test() -> int:
    """Run the self-tests (layer 1) and the fixture integration tests (layer 2)."""
    return _run("pytest")


def task_lint() -> int:
    """ruff check + ruff format --check; zero warnings is the bar (CLAUDE.md)."""
    rc = _run("ruff", "check", ".")
    rc2 = _run("ruff", "format", "--check", ".")
    return rc or rc2


def task_format() -> int:
    """Apply ruff formatting and safe fixes."""
    rc = _run("ruff", "format", ".")
    rc2 = _run("ruff", "check", "--fix", ".")
    return rc or rc2


def task_check() -> int:
    """lint then test; the pre-commit bar for this repo."""
    rc = task_lint()
    return rc or task_test()


TASKS = {
    "test": task_test,
    "lint": task_lint,
    "format": task_format,
    "check": task_check,
}


def main(argv: list[str]) -> int:
    if len(argv) != 1 or argv[0] in {"help", "-h", "--help"}:
        print(__doc__)
        for name, fn in TASKS.items():
            print(f"  {name:8} {fn.__doc__}")
        return 0 if argv and argv[0] in {"help", "-h", "--help"} else 2
    task = TASKS.get(argv[0])
    if task is None:
        print(f"unknown task: {argv[0]}", file=sys.stderr)
        return 2
    return task()


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
