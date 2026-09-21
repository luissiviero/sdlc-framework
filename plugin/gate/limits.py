"""Run limits for unattended phases (build guide step 19): every limit parks through the gate
with the partial evidence attached; never a silent stop, never a notification.

Limits (sdlc.yaml ``gate:`` block, all optional; defaults here):
  - ``max_iterations``: fix iterations per phase (default 3, "two or three rounds", article
    p.28); the non-routine classification of the adversarial reviewer lowers it to
    ``max_iterations_non_routine`` (default 2), never below 1;
  - ``max_wall_clock_minutes``: elapsed time since the phase run started (default 120);
    the run records its start with ``cli.py start-run``;
  - ``max_budget_usd``: per-change spend where the substrate exposes one; the run writes the
    figure it observes with ``cli.py record-spend`` (a headless `claude -p` prints
    ``total_cost_usd`` in its JSON result); absent figure = not enforced;
  - pause flag: ``sdlc.yaml: paused: true`` (chosen over a PAUSE file: sdlc.yaml is already a
    protected path, so a run cannot un-pause itself).
The outer bound for headless runs is the CLI's own ``--max-turns`` (docs/NOTES.md section 10).
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PLUGIN_DIR = Path(__file__).resolve().parent.parent
if str(PLUGIN_DIR) not in sys.path:
    sys.path.insert(0, str(PLUGIN_DIR))

from gate import artifacts as art  # noqa: E402
from gate.checks import CheckResult, GateContext  # noqa: E402

DEFAULT_MAX_ITERATIONS = 3
DEFAULT_MAX_ITERATIONS_NON_ROUTINE = 2
DEFAULT_MAX_WALL_CLOCK_MINUTES = 120
RUN_FILE = "run-{phase}.json"  # evidence/run-<phase>.json: started_at, spend_usd


def _int(value: Any, default: int) -> int:
    try:
        n = int(value)
    except (TypeError, ValueError):
        return default
    return n if n > 0 else default


def _float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def iteration_cap(ctx: GateContext, classification: str | None) -> int:
    cap = _int(ctx.gate_setting("max_iterations", None), DEFAULT_MAX_ITERATIONS)
    if classification == "non-routine":
        tight = _int(
            ctx.gate_setting("max_iterations_non_routine", None),
            DEFAULT_MAX_ITERATIONS_NON_ROUTINE,
        )
        cap = max(1, min(cap, tight))
    return cap


def classification_for(ctx: GateContext) -> str | None:
    """The adversarial reviewer's routine/non-routine call for this phase, or the latest one
    from an earlier gate (a classification made at (b) tightens (c) and (d))."""
    from gate.checks import load_verdict

    for phase in (ctx.phase, "d", "c", "b"):
        data, _ = load_verdict(ctx.evidence_dir / art.ADVERSARIAL_VERDICT.format(phase=phase))
        if data is not None:
            return data.get("classification")
    return None


def read_run(ctx: GateContext) -> dict[str, Any]:
    import json

    path = ctx.evidence_dir / RUN_FILE.format(phase=ctx.phase)
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def _elapsed_minutes(started_at: str | None, now: datetime | None = None) -> float | None:
    if not started_at:
        return None
    try:
        start = datetime.fromisoformat(str(started_at).replace("Z", "+00:00"))
    except ValueError:
        return None
    if start.tzinfo is None:
        start = start.replace(tzinfo=timezone.utc)
    now = now or datetime.now(timezone.utc)
    return (now - start).total_seconds() / 60.0


def check_limits(ctx: GateContext, now: datetime | None = None) -> CheckResult:
    details: dict[str, Any] = {}
    # pause flag first: a paused repo runs nothing
    if ctx.config.get("paused") is True:
        return CheckResult(
            "limits",
            False,
            "the repository is paused (sdlc.yaml: paused: true)",
            "Set `paused: false` in sdlc.yaml (a reviewed PR) when runs may resume.",
            {"stop": True, "paused": True},
        )
    classification = classification_for(ctx)
    cap = iteration_cap(ctx, classification)
    details.update(
        {"iterations": ctx.status.iterations, "cap": cap, "classification": classification}
    )
    if ctx.status.iterations > cap:
        return CheckResult(
            "limits",
            False,
            f"iteration cap reached: {ctx.status.iterations} fix iterations, cap {cap}"
            + (" (non-routine)" if classification == "non-routine" else ""),
            "Look at the partial evidence, then either fix by hand, or reset the count with "
            f"`cli.py set-iterations --root . --id {ctx.status.id} --count 0` to allow another "
            "round.",
            {**details, "stop": True},
        )
    run = read_run(ctx)
    if not run and not ctx.human_gate and ctx.phase in ("b", "c", "d"):
        return CheckResult(
            "limits",
            False,
            f"the run did not register its start (evidence/{RUN_FILE.format(phase=ctx.phase)} "
            "missing), so the wall clock and budget cannot be enforced",
            f"Start phase runs with `gate/cli.py start-run --id {ctx.status.id} --phase "
            f"{ctx.phase}` before the work, and record spend with `record-spend`.",
            {**details, "stop": False},
        )
    max_minutes = _int(
        ctx.gate_setting("max_wall_clock_minutes", None), DEFAULT_MAX_WALL_CLOCK_MINUTES
    )
    elapsed = _elapsed_minutes(run.get("started_at"), now)
    details.update({"elapsed_minutes": round(elapsed, 1) if elapsed is not None else None})
    if elapsed is not None and elapsed > max_minutes:
        return CheckResult(
            "limits",
            False,
            f"wall-clock limit exceeded: {elapsed:.0f} min elapsed, limit {max_minutes} min",
            "The phase ran too long: inspect the partial evidence and start a fresh run "
            "(`cli.py start-run` resets the clock).",
            {**details, "stop": True, "max_wall_clock_minutes": max_minutes},
        )
    budget = _float(ctx.gate_setting("max_budget_usd", None))
    spend = _float(run.get("spend_usd"))
    details.update({"spend_usd": spend, "max_budget_usd": budget})
    if budget is not None and spend is not None and spend > budget:
        return CheckResult(
            "limits",
            False,
            f"budget exceeded: {spend:.2f} USD spent, budget {budget:.2f} USD",
            "Raise `gate.max_budget_usd` in sdlc.yaml (a reviewed PR) or finish by hand.",
            {**details, "stop": True},
        )
    return CheckResult("limits", True, "within the run limits", details=details)
