"""``run_gate``: the one gate function every autonomous phase calls (build guide step 16).

Order: run limits (step 19) → deterministic checks → the adversarial reviewer's verdict.
Result:
  - ``continue``  every check passed and the gate is automated for this profile;
  - ``wait``      every check passed but the gate is human (Standard: a, b, e; Full: all):
                  the run stops with the ``sdlc:<phase>-ready`` label;
  - ``park``      a check failed: ``Status.park(reason)``, the ``sdlc:needs-human`` label and
                  the "What I need from you" block for the PR description. Nobody is notified
                  (decision 11).
The result is also written to ``changes/<id>-<slug>/evidence/gate-<phase>.json`` so the
PR summary (step 27a, B3) can show it.
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PLUGIN_DIR = Path(__file__).resolve().parent.parent
if str(PLUGIN_DIR) not in sys.path:
    sys.path.insert(0, str(PLUGIN_DIR))

from gate import artifacts as art  # noqa: E402
from gate import checks, limits  # noqa: E402
from gate import diff as diffmod  # noqa: E402
from gate.checks import CheckResult, GateContext  # noqa: E402
from hooks._common import ConfigError, load_sdlc_config  # noqa: E402
from state import conventions as c  # noqa: E402
from state import status as status_mod  # noqa: E402

RESULTS = ("continue", "wait", "park")


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


@dataclass
class GateResult:
    change_id: str
    slug: str
    phase: str
    profile: str
    human_gate: bool
    result: str
    checks: list[CheckResult]
    label: str | None
    head: str | None
    at: str = field(default_factory=_now)
    dry_run: bool = False

    @property
    def failed(self) -> list[CheckResult]:
        return [ch for ch in self.checks if not ch.ok]

    @property
    def reason(self) -> str:
        return "; ".join(f"{ch.name}: {ch.reason}" for ch in self.failed)

    def what_i_need(self) -> str:
        """The block the PR description carries when the change is parked (decision 11)."""
        if self.result != "park":
            return ""
        lines = [
            "## What I need from you",
            f"Gate ({self.phase}) parked change {self.change_id} ({self.slug}) on {self.at}.",
        ]
        for ch in self.failed:
            lines.append(f"- **{ch.name}**: {ch.reason}")
            if ch.need:
                lines.append(f"  - what I need: {ch.need}")
        lines.append(
            "When the item is settled, re-run the gate: "
            f'`python "${{CLAUDE_PLUGIN_ROOT}}/plugin/gate/cli.py" check --root . '
            f"--id {self.change_id} --phase {self.phase}` (review comments are the change "
            "request; /sdlc-fix from B3 re-runs the phase with them)."
        )
        return "\n".join(lines) + "\n"

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "change_id": self.change_id,
            "slug": self.slug,
            "phase": self.phase,
            "profile": self.profile,
            "human_gate": self.human_gate,
            "result": self.result,
            "label": self.label,
            "head": self.head,
            "at": self.at,
            "dry_run": self.dry_run,
            "reason": self.reason,
            "checks": [ch.as_dict() for ch in self.checks],
            "what_i_need": self.what_i_need(),
        }


class GateError(RuntimeError):
    pass


def build_context(root: Path, change_id: str, phase: str, base: str | None = None) -> GateContext:
    root = Path(root).resolve()
    if phase not in c.PHASES:
        raise GateError(f"phase must be one of {c.PHASES}")
    change_dir = c.find_change_dir(root, change_id)
    if change_dir is None:
        raise GateError(f"no change folder for id {change_id} under {root / c.CHANGES_DIR}")
    st = status_mod.read_status(change_dir)
    try:
        config = load_sdlc_config(str(root))
    except ConfigError as exc:
        raise GateError(str(exc)) from exc
    if not config:
        raise GateError("sdlc.yaml not found: run /sdlc-init first")
    profile = c.effective_profile(config.get("profile"), st.profile_override)
    human = c.is_human_gate(profile, phase)
    diff_error = ""
    try:
        d = diffmod.collect(root, base)
    except diffmod.GitUnavailable as exc:
        d, diff_error = None, str(exc)
    ctx = GateContext(root, change_dir, phase, st, config, d, human, diff_error)
    ctx.profile = profile  # type: ignore[attr-defined]
    return ctx


def evaluate(ctx: GateContext) -> GateResult:
    """Run every check for the phase; no side effects."""
    results: list[CheckResult] = [limits.check_limits(ctx)]
    stop_early = not results[0].ok and results[0].details.get("stop", False)
    if not stop_early:
        for check in checks.CHECKS_BY_PHASE.get(ctx.phase, ()):
            try:
                results.append(check(ctx))
            except Exception as exc:  # noqa: BLE001 — a crashing check parks, never passes
                results.append(
                    CheckResult(
                        check.__name__.removeprefix("check_"),
                        False,
                        f"check crashed: {exc!r}",
                        "Report this to the framework owner; the gate failed closed.",
                    )
                )
    failed = [r for r in results if not r.ok]
    profile = getattr(ctx, "profile", c.DEFAULT_PROFILE)
    if failed:
        result, label = "park", c.NEEDS_HUMAN_LABEL
    elif ctx.human_gate:
        result, label = "wait", c.ready_label(ctx.phase)
    else:
        result, label = "continue", None
    return GateResult(
        change_id=ctx.status.id,
        slug=ctx.status.slug,
        phase=ctx.phase,
        profile=profile,
        human_gate=ctx.human_gate,
        result=result,
        checks=results,
        label=label,
        head=ctx.diff.head if ctx.diff else None,
    )


def apply(ctx: GateContext, result: GateResult) -> None:
    """Record the verdict: status.yaml (park or passed) and evidence/gate-<phase>.json."""
    st = ctx.status
    if result.result == "park":
        st.park(result.reason)
    elif result.result == "continue":
        st.record_gate(ctx.phase, "passed")
    else:
        st.record_gate(ctx.phase, "passed", f"waiting for the owner at gate ({ctx.phase})")
    status_mod.write_status(ctx.change_dir, st)
    ctx.evidence_dir.mkdir(parents=True, exist_ok=True)
    out = ctx.evidence_dir / art.GATE_RESULT.format(phase=ctx.phase)
    out.write_text(json.dumps(result.as_dict(), indent=2), encoding="utf-8", newline="\n")


def run_gate(
    root: Path, change_id: str, phase: str, base: str | None = None, dry_run: bool = False
) -> GateResult:
    ctx = build_context(root, change_id, phase, base)
    result = evaluate(ctx)
    result.dry_run = dry_run
    if not dry_run:
        apply(ctx, result)
    return result
