"""PostToolUse hook: run the formatter and linter on the file that changed (build guide
step 15 (2); article p.23 'Run the formatter and linter after file edits so drift never
accumulates' and 'build-phase hooks should be fast and scoped to the file that changed').

Python files: ``ruff format`` then ``ruff check --fix``; anything ruff cannot fix is fed back
to Claude as a PostToolUse ``decision: block`` reason. Other file types are ignored in this
version; ``sdlc.yaml`` can turn the hook off with ``hooks: {format_on_edit: false}``.
This hook fails open: a missing ruff is reported on stderr and never blocks.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import (  # noqa: E402
    FILE_TOOLS,
    Decision,
    load_sdlc_config,
    project_dir,
    run_hook,
    target_paths,
)

PY_SUFFIXES = {".py", ".pyi"}


def ruff_command(runner: str | None = None) -> list[str] | None:
    """Prefer `python -m ruff` (same interpreter as the hook), else `ruff` on PATH."""
    probe = subprocess.run(
        [sys.executable, "-m", "ruff", "--version"], capture_output=True, text=True
    )
    if probe.returncode == 0:
        return [sys.executable, "-m", "ruff"]
    exe = shutil.which("ruff")
    return [exe] if exe else None


def format_file(path: Path, root: Path, run=subprocess.run) -> tuple[bool, str]:
    """Returns (clean, message). clean=False means unfixable lint findings remain.
    Order matters: fix first (may delete lines), then format, then report what is left."""
    cmd = ruff_command()
    if cmd is None:
        return True, "ruff not installed; skipped formatter/lint"
    common = dict(cwd=str(root), capture_output=True, text=True)
    run([*cmd, "check", "--fix", "--quiet", str(path)], **common)
    run([*cmd, "format", str(path)], **common)
    proc = run([*cmd, "check", "--output-format", "concise", str(path)], **common)
    if proc.returncode == 0:
        return True, ""
    return False, (proc.stdout or proc.stderr).strip()


def decide(payload: dict, argv: list[str], env: dict[str, str] | None = None) -> Decision:
    if payload.get("tool_name") not in FILE_TOOLS:
        return Decision.allow()
    root = Path(project_dir(payload, env))
    config = load_sdlc_config(str(root))
    hooks_cfg = config.get("hooks") or {}
    if isinstance(hooks_cfg, dict) and hooks_cfg.get("format_on_edit") is False:
        return Decision.allow()
    for path_s in target_paths(payload.get("tool_input") or {}):
        path = Path(path_s)
        if path.suffix.lower() not in PY_SUFFIXES or not path.is_file():
            continue
        clean, message = format_file(path, root)
        if not clean:
            return Decision(
                block=True,
                reason=(
                    f"ruff reports remaining problems in {path.name} after auto-fix; fix them "
                    f"before moving on:\n{message}"
                ),
            )
        if message:
            sys.stderr.write(message)
    return Decision.allow()


if __name__ == "__main__":
    sys.exit(run_hook(decide, "PostToolUse", sys.argv[1:]))
