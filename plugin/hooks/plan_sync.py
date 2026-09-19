"""PreToolUse hook on ``git commit``: plan.md must change whenever source changes in phase (c)
(build guide step 15 (4) and step 12; article p.16 step 7 'When implementation departs from
the plan, update plan.md in the same commit. Consider using a hook to enforce
synchronization between the two.').

Mechanism (the article suggests the hook but not its mechanism): registered with
``"if": "Bash(git commit *)"`` (and the PowerShell twin). It reads the current branch; only
``sdlc/<id>/c`` branches are checked (OPERATING_MODEL section 8: 'In (c) a pre-commit check
enforces that plan.md changes whenever source changes'). If any staged path is source — not
under ``changes/`` and not matched by ``plan_sync.exempt`` in sdlc.yaml — then
``changes/<id>-*/plan.md`` must be staged too, or the commit is denied.
"""

from __future__ import annotations

import re
import shlex
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import Decision, load_sdlc_config, matches, project_dir, run_hook  # noqa: E402

from state import conventions as c  # noqa: E402

DEFAULT_EXEMPT = ("changes/**",)
COMMIT_RE = re.compile(r"(^|[;&|]\s*)git\s+(?:-C\s+\S+\s+)?commit\b")


def _git(root: str, *args: str) -> str:
    proc = subprocess.run(
        ["git", *args], cwd=root, capture_output=True, text=True, encoding="utf-8"
    )
    return proc.stdout if proc.returncode == 0 else ""


def staged_and_auto(root: str, command: str, git=_git) -> list[str]:
    files = git(root, "diff", "--cached", "--name-only", "--diff-filter=ACMRD").split()
    tokens = shlex.split(command, posix=True) if command else []
    if (
        "-a" in tokens
        or "--all" in tokens
        or any(t.startswith("-a") and t[1:].isalpha() for t in tokens)
    ):
        files += git(root, "diff", "--name-only", "--diff-filter=ACMRD").split()
    return sorted({f.replace("\\", "/") for f in files})


def check(branch: str, files: list[str], exempt: list[str]) -> Decision:
    parsed = c.parse_branch(branch)
    if not parsed or parsed[1] != "c":
        return Decision.allow()
    change_id = parsed[0]
    plan_rx = re.compile(rf"^changes/{change_id}-[^/]+/plan\.md$")
    plan_staged = any(plan_rx.match(f) for f in files)
    source = [f for f in files if not any(matches(p, f) for p in exempt)]
    if source and not plan_staged:
        listed = "\n".join(f"  - {f}" for f in source[:20])
        return Decision.deny(
            "plan.md is out of sync: this commit changes source files but not "
            f"changes/{change_id}-<slug>/plan.md. When implementation departs from the plan, "
            "update plan.md in the same commit (article p.16, step 7). Source files staged:\n"
            f"{listed}"
        )
    return Decision.allow()


def decide(payload: dict, argv: list[str], env: dict[str, str] | None = None, git=_git) -> Decision:
    if payload.get("tool_name") not in ("Bash", "PowerShell"):
        return Decision.allow()
    command = str((payload.get("tool_input") or {}).get("command") or "")
    if not COMMIT_RE.search(command):
        return Decision.allow()
    root = project_dir(payload, env)
    branch = git(root, "rev-parse", "--abbrev-ref", "HEAD").strip()
    if not branch:
        return Decision.allow()  # not a git repo: nothing to enforce
    cfg = load_sdlc_config(root).get("plan_sync") or {}
    exempt = list(DEFAULT_EXEMPT) + [
        str(p) for p in (cfg.get("exempt") or []) if isinstance(cfg, dict)
    ]
    return check(branch, staged_and_auto(root, command, git), exempt)


if __name__ == "__main__":
    sys.exit(run_hook(decide, "PreToolUse", sys.argv[1:]))
