"""Whether the Windows job of ``Framework checks`` runs on this event (the batch ci revision, 10.2).

Run by ``.github/workflows/framework-checks.yml`` in its ``platforms`` job, before the
Windows job (and by hand: ``python .github/scripts/framework_checks_windows.py``). Windows is
the whole wait of a pull request (about 12 to 16 minutes against 2 on Linux), and half the
merges to ``main`` touch only documentation, which no Windows-only code reads. So the
Windows job is skipped on a pull request when **every** changed path is documentation:
under ``docs/``, or ``HANDOFF.md`` or ``README.md`` at the root. Any other path runs it, so
a list of platform-sensitive paths cannot go stale: the Windows-specific code sits in eight
``plugin/`` folders, and the one Windows-only failure on record was in ``tests/``.

Every other event (a push to ``main``, a dispatch) runs Windows, and so does every doubt:
no ``HEAD^2``, a failed ``git diff``, no changed path read. On a ``pull_request`` event the
checkout is GitHub's merge commit, so ``HEAD^1`` is the base and the diff ``HEAD^1 HEAD``
is what the merge would change; ``--no-renames`` lists a moved file under both of its
names, so moving code into ``docs/`` still runs Windows.

The event is ``GITHUB_EVENT_NAME`` (set by the runner), or ``--event``. Outputs
(``$GITHUB_OUTPUT`` and stdout): ``windows=true|false`` and ``reason=<why>``. Exit 0 always:
a failure to decide is a ``windows=true``, never a red job.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

DOCUMENTATION_DIR = "docs/"
DOCUMENTATION_FILES = frozenset({"HANDOFF.md", "README.md"})


def is_documentation(path: str) -> bool:
    return path.startswith(DOCUMENTATION_DIR) or path in DOCUMENTATION_FILES


def decide(event: str, paths: list[str] | None) -> tuple[bool, str]:
    """(whether Windows runs, why)."""
    if event != "pull_request":
        return True, f"a {event or 'unnamed'} event runs every platform"
    if paths is None:
        return True, "the changed paths could not be read"
    if not paths:
        return True, "no changed path was read"
    other = [p for p in paths if not is_documentation(p)]
    if other:
        return True, f"{len(other)} changed path(s) are not documentation, first {other[0]}"
    return False, f"all {len(paths)} changed path(s) are documentation"


def changed_paths(root: Path) -> list[str] | None:
    """The paths the merge commit at HEAD changes against its base, or None."""

    def git(*args: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            ["git", *args], cwd=root, capture_output=True, text=True, encoding="utf-8"
        )

    if git("rev-parse", "--verify", "--quiet", "HEAD^2").returncode != 0:
        return None  # not a merge commit: not GitHub's checkout of a pull request
    proc = git("diff", "--name-only", "--no-renames", "-z", "HEAD^1", "HEAD")
    if proc.returncode != 0:
        return None
    return [p for p in proc.stdout.split("\0") if p]


def write_outputs(values: dict[str, str]) -> None:
    lines = [f"{k}={v}" for k, v in values.items()]
    print("\n".join(lines))
    path = os.environ.get("GITHUB_OUTPUT")
    if path:
        with open(path, "a", encoding="utf-8") as fh:
            fh.write("\n".join(lines) + "\n")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0])
    p.add_argument("--root", default=".")
    p.add_argument("--event", default=os.environ.get("GITHUB_EVENT_NAME", ""))
    args = p.parse_args(argv)
    paths = changed_paths(Path(args.root)) if args.event == "pull_request" else None
    windows, reason = decide(args.event, paths)
    write_outputs({"windows": str(windows).lower(), "reason": reason})
    return 0


if __name__ == "__main__":
    sys.exit(main())
