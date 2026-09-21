"""PreToolUse hook: in a fix-type change, the reproducing test is frozen (build guide step 25;
article p.28 step 4 'write a test that reproduces the bug ... then fix the code', p.35 'stop the
agent editing test files during a fix task').

Mechanism (OPERATING_MODEL section 8, "Test-file lock"): the build run of a change whose
``status.yaml`` says ``change_type: fix`` commits the reproducing test first and then sets
``status.yaml: tests_locked: true``. From that commit on, while the run is on the change's
``sdlc/<id>/c`` branch — phases (c), (d) and (e) share it, and ``/d`` and ``/e`` are treated as
locked too should they ever exist — every ``Edit``/``Write``/``MultiEdit``/``NotebookEdit`` whose
target matches a glob in ``sdlc.yaml: test_paths`` is denied. The fix must make the committed
test pass; if the test itself is wrong, the change parks and only the owner unlocks it
(``state/cli.py unlock-tests``), in a reviewed PR.

Never denies outside a phase (c)/(d)/(e) branch: on ``main``, on an (a)/(b) branch or in a
project that is not a git repository the hook exits 0 without output. On a locked branch it
fails closed — an unreadable ``status.yaml`` or ``sdlc.yaml`` denies the edit with the error in
the reason, so a broken state file cannot quietly unlock the tests.

Usage in hooks.json (exec form): python test_file_lock.py
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import (  # noqa: E402
    FILE_TOOLS,
    ConfigError,
    Decision,
    load_sdlc_config,
    matches,
    norm,
    project_dir,
    real,
    rel_to,
    run_hook,
    target_paths,
)

from state import conventions as c  # noqa: E402
from state import status as status_mod  # noqa: E402

LOCKED_PHASES = ("c", "d", "e")
# Used only when sdlc.yaml has no `test_paths:` key (a project initialised before step 25):
# the union of the Python and Node defaults /sdlc-init writes, so the lock still holds.
DEFAULT_TEST_PATHS = (
    "tests/**",
    "test/**",
    "__tests__/**",
    "**/test_*.py",
    "**/*_test.py",
    "**/conftest.py",
    "**/*.test.js",
    "**/*.spec.js",
    "**/*.test.ts",
    "**/*.spec.ts",
)

REASON = (
    "Test-file lock: {path} is a test file and this is a fix-type change whose reproducing "
    "test is committed; the fix must make it pass without editing tests (build guide step 25). "
    "If the test itself is wrong, park the change; the owner unlocks with state/cli.py "
    "unlock-tests."
)
FAIL_CLOSED = (
    "Test-file lock cannot tell whether the tests of this change are frozen ({error}); on a "
    "phase (c)/(d)/(e) branch the hook fails closed and refuses the edit. Fix the change's "
    "status.yaml or the project's sdlc.yaml, or park the change for the owner."
)


def _git(root: str, *args: str) -> str:
    try:
        proc = subprocess.run(
            ["git", *args], cwd=root, capture_output=True, text=True, encoding="utf-8", timeout=20
        )
    except (OSError, subprocess.TimeoutExpired):
        return ""
    return proc.stdout if proc.returncode == 0 else ""


def locked_change_id(branch: str) -> str | None:
    """The change id when the branch is one the lock applies to, else None."""
    parsed = c.parse_branch(branch)
    if not parsed or parsed[1] not in LOCKED_PHASES:
        return None
    return parsed[0]


def edit_targets(tool_input: dict) -> list[str]:
    """Every path the call would write: ``file_path`` / ``notebook_path`` plus, for MultiEdit,
    the ``file_path`` of each edit (one call can touch several files)."""
    paths = list(target_paths(tool_input))
    for edit in tool_input.get("edits") or []:
        if isinstance(edit, dict) and edit.get("file_path"):
            paths.append(str(edit["file_path"]))
    return list(dict.fromkeys(paths))


def test_path_patterns(config: dict) -> list[str]:
    patterns = config.get("test_paths")
    if patterns is None:
        return list(DEFAULT_TEST_PATHS)
    if not isinstance(patterns, list):
        raise ConfigError("sdlc.yaml: test_paths must be a list of globs")
    return [str(p) for p in patterns if str(p).strip()]


def is_locked(root: str, change_id: str) -> bool:
    """True when the change is a fix whose reproducing test is committed. Raises ConfigError
    when the change folder or its status.yaml cannot be read (the caller fails closed)."""
    change_dir = c.find_change_dir(Path(root), change_id)
    if change_dir is None:
        raise ConfigError(f"no changes/{change_id}-<slug>/ folder for the current branch")
    try:
        st = status_mod.read_status(change_dir)
    except Exception as exc:  # noqa: BLE001
        raise ConfigError(f"{change_id} status.yaml could not be read: {exc}") from exc
    return st.change_type == "fix" and bool(st.tests_locked)


def decide(payload: dict, argv: list[str], env: dict[str, str] | None = None, git=_git) -> Decision:
    if payload.get("tool_name") not in FILE_TOOLS:
        return Decision.allow()
    paths = edit_targets(payload.get("tool_input") or {})
    if not paths:
        return Decision.allow()
    root = project_dir(payload, env)
    branch = git(root, "rev-parse", "--abbrev-ref", "HEAD").strip()
    change_id = locked_change_id(branch) if branch else None
    if change_id is None:
        return Decision.allow()  # not a git repo, or not a phase (c)/(d)/(e) branch
    try:
        if not is_locked(root, change_id):
            return Decision.allow()
        patterns = test_path_patterns(load_sdlc_config(root))
    except ConfigError as exc:
        return Decision.deny(FAIL_CLOSED.format(error=exc))
    for path in paths:
        for candidate in {norm(path), real(path)}:
            rel = rel_to(root, candidate)
            if rel is None:
                continue  # outside the project: not a test file of this change
            if any(matches(pattern, rel) for pattern in patterns):
                return Decision.deny(REASON.format(path=rel))
    return Decision.allow()


if __name__ == "__main__":
    sys.exit(run_hook(decide, "PreToolUse", sys.argv[1:]))
