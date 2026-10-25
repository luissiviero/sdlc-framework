"""R51, gap G1 (``docs/proposals/concurrent-changes.md``; the race analysis's checks 6, 7 and
12, ``docs/reviews/2026-10-20-r51-race-analysis.md``): a build PR behind the default branch
is brought up to date and re-checked before gate (deploy) is offered, and a run whose push found
its branch moved re-checks the merged tree before it hands anything over.

- ``update_before_offer``: before the REVIEW.md pass, the deploy run and a fix round at deploy, the
  default branch is merged into the work branch with a merge commit (``merge_default_branch``
  of the runner, 1.0.10's merge); a conflict parks, and a merge that went in is re-checked.
- ``recheck``: the three targets run once more by the runner itself on the merged tree, never
  read from the PR's check runs (a push by the workflow token starts none, NOTES §11); red
  parks with the targets named.
- ``remote_merged``: ``commit-phase --push`` reports the merge commit ``gitops.push`` made
  when the remote branch had moved (check 12); the runner then re-checks that tree.

The merge commit of ``update_before_offer`` is pushed by the run's next push (the review
pass's run record, the park, or the deploy run's own commits), as 1.0.10's merge is.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

from gate import checks as gate_checks

CHECK = "base_update"
MERGE_MESSAGE = "run({phase}): {base} merged before gate (deploy) is offered (R51)"
CONFLICT_PARK = CHECK + ": the default branch does not merge into {branch}: {files}"
CONFLICT_NEED = (
    "The default branch moved since this change's gates ran, and it does not merge into "
    "{branch}; the runner aborted the merge. Merge it by hand (the pull request's \"Update "
    'branch", or a merge commit), then dispatch SDLC deploy (Actions → SDLC deploy → Run '
    "workflow) with change id {id} and head_ref {branch}."
)
RED_PARK = CHECK + ": {what} is not green: {red}"
RED_NEED = (
    "No gate judged this tree: {what}. Fix the red target on {branch} (a review comment or an "
    "@claude comment starts a fix round), then gate (deploy) is offered on the fixed head."
)
UPDATED = "the default branch merged into {branch} as {sha}"
MOVED = "the remote {branch} moved during the run and was merged in as {sha}"


def recheck(root: Path, config: dict[str, Any], env: dict[str, str]) -> list[str] | None:
    """The targets that are not green on the checkout, ``[]`` when all are, None when
    sdlc.yaml has none. ``env`` is the runner's commands environment (no token, no model
    credential); each target gets the gate's own per-command timeout."""
    commands = gate_checks.commands_from_config(config)
    if not commands:
        return None
    gate_cfg = config.get("gate") if isinstance(config.get("gate"), dict) else {}
    try:
        timeout = int(gate_cfg.get("command_timeout", gate_checks.DEFAULT_COMMAND_TIMEOUT))
    except (TypeError, ValueError):
        timeout = gate_checks.DEFAULT_COMMAND_TIMEOUT
    red = []
    for name, command in commands.items():
        run = gate_checks.run_command(command, root, timeout, env=env)
        if run["exit_code"] != 0:
            how = "timed out" if run["exit_code"] is None else f"exit {run['exit_code']}"
            red.append(f"{name} ({how})")
    return red


def update_before_offer(
    root: Path,
    config: dict[str, Any],
    env: dict[str, str],
    merge: Callable[..., dict[str, Any]],
    branch: str,
    change_id: str,
    phase: str,
) -> dict[str, Any]:
    """Merge the default branch into ``branch`` and re-check the merged tree.
    ``{"ok": True, "merged": sha | None}``, or ``{"ok": False, "reason", "need"}`` for the
    park. ``merge`` is the runner's ``merge_default_branch``."""
    merged = merge(root, message=MERGE_MESSAGE.format(phase=phase, base="{base}"))
    if not merged.get("ok"):
        files = ", ".join(merged.get("conflicts") or [])
        return {
            **merged,
            "reason": CONFLICT_PARK.format(branch=branch, files=files),
            "need": CONFLICT_NEED.format(branch=branch, id=change_id),
        }
    if not merged.get("merged"):
        return merged
    what = UPDATED.format(branch=branch, sha=merged["merged"][:10])
    return {**merged, **judged(root, config, env, what, branch)}


def remote_merged(record: dict[str, Any] | None) -> str | None:
    """The merge commit ``commit-phase --push`` made over a moved remote branch, else None."""
    output = (record or {}).get("output")
    sha = output.get("remote_merged") if isinstance(output, dict) else None
    return sha if isinstance(sha, str) and sha else None


def judged(
    root: Path, config: dict[str, Any], env: dict[str, str], what: str, branch: str
) -> dict[str, Any]:
    """``{"ok": True, "recheck": ...}`` when the targets are green (or there are none), else
    the park's ``reason`` and ``need`` naming ``what`` happened and the red targets."""
    red = recheck(root, config, env)
    if not red:
        return {"ok": True, "recheck": "no targets" if red is None else "green"}
    return {
        "ok": False,
        "recheck": red,
        "reason": RED_PARK.format(what=what, red="; ".join(red)),
        "need": RED_NEED.format(what=what, branch=branch),
    }
