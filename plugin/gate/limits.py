"""Run limits for unattended phases (build guide step 19): every limit parks through the gate
with the partial evidence attached; never a silent stop, and no notification but the runner's
review request on the parked PR (decision 31).

Limits (sdlc.yaml ``gate:`` block, all optional; defaults here):
  - ``max_iterations``: fix iterations per change, one counter across the phases
    (OPERATING_MODEL section 4.1; default 3, after the article's "two or three rounds" of
    the visual check, p.28; one change spends rounds at several gates); the non-routine
    classification of the adversarial reviewer lowers it to
    ``max_iterations_non_routine`` (default 2), never below 1;
  - ``max_panel_calls``: review-panel calls per change under deferred review (decision 21,
    amended in 0.2.15: a panel call is not a fix iteration; default 4; the same
    ``sdlc:reset-iterations`` label resets both counts);
  - ``max_wall_clock_minutes``: elapsed time since the phase run started (default 120);
    the run records its start with ``cli.py start-run``;
  - ``build_max_turns`` and ``build_max_wall_clock_minutes``: the turn and wall-clock caps of
    the build run (``--phase c``) and of every fix round (decision 32, 1.0.8; defaults 400 and
    180); every other run keeps ``max_turns`` (the runner's, default 200) and
    ``max_wall_clock_minutes``. An unset build key is the larger of the general setting and
    the build default, so no project's cap goes down (``run_caps``); ``start-run`` records
    ``"run": "build"`` for such a run, and a record without it gets the general cap;
  - ``max_budget_usd``: per-change spend where the substrate exposes one; the run writes the
    figure it observes with ``cli.py record-spend`` (a headless `claude -p` prints
    ``total_cost_usd`` in its JSON result); absent figure = not enforced, so the cap binds CI
    runs only (a by-hand or cloud-session run has no figure; OPERATING_MODEL section 4.1).
    The cap is compared with the change's running total (issue #71, 0.3.1): every recorded
    session is one entry of ``evidence/spend.json`` (the review pass and each fix round are
    their own entries, named by the run and its stored result), and ``total_usd`` is their
    sum; ``run-<phase>.json`` keeps the last session's figure for the run record. Before
    0.3.1 the cap saw that one figure only, which ``start-run`` reset and ``record-spend``
    overwrote, so a change spent several times the cap unless one session did;
  - pause flag: ``sdlc.yaml: paused: true`` (chosen over a PAUSE file: sdlc.yaml is already a
    protected path, so a run cannot un-pause itself).
The outer bound for headless runs is the CLI's own ``--max-turns`` (docs/notes/10.md, 10b).
"""

from __future__ import annotations

import json
import math
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PLUGIN_DIR = Path(__file__).resolve().parent.parent
if str(PLUGIN_DIR) not in sys.path:
    sys.path.insert(0, str(PLUGIN_DIR))

from gate import artifacts as art  # noqa: E402
from gate import checks  # noqa: E402
from gate.checks import CheckResult, GateContext  # noqa: E402
from hooks._common import ConfigError, config_flag  # noqa: E402

DEFAULT_MAX_ITERATIONS = 3
DEFAULT_MAX_ITERATIONS_NON_ROUTINE = 2
DEFAULT_MAX_PANEL_CALLS = 4
DEFAULT_MAX_WALL_CLOCK_MINUTES = 120
DEFAULT_MAX_TURNS = 200  # the runner's ``--max-turns`` (docs/notes/10.md, 10b)
DEFAULT_BUILD_MAX_TURNS = 400  # decision 32: the build run and every fix round
DEFAULT_BUILD_MAX_WALL_CLOCK_MINUTES = 180
BUILD_RUN = "build"  # run-<phase>.json: "run" for the build run or a fix round
RUN_KIND_ENV = "SDLC_RUN"  # the runner sets it to FIX_RUN in a fix session's environment
FIX_RUN = "fix"
RUN_FILE = "run-{phase}.json"  # evidence/run-<phase>.json: started_at, spend_usd
SPEND_FILE = "spend.json"  # evidence/spend.json: the change's spend ledger (issue #71)


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


def run_caps(gate_settings: Any, build: bool, less_minutes: int = 0) -> tuple[int, int]:
    """(turns, wall-clock minutes) of one run, from the ``sdlc.yaml`` ``gate:`` block
    (decision 32): the general ``max_turns`` and ``max_wall_clock_minutes``, or for the build
    run and a fix round (``build``) ``build_max_turns`` and ``build_max_wall_clock_minutes``,
    each of which, when unset or invalid, is the larger of the general setting and the build
    default. The one copy of the rule: the runner's ``--max-turns`` and subprocess timeout and
    the gate's wall-clock check all read it. ``less_minutes`` comes off the wall clock (the
    drive's minutes at (e), change 0004), never below ``RUN_CAP_FLOOR_MINUTES``."""
    cfg = gate_settings if isinstance(gate_settings, dict) else {}
    turns = _int(cfg.get("max_turns"), DEFAULT_MAX_TURNS)
    minutes = _int(cfg.get("max_wall_clock_minutes"), DEFAULT_MAX_WALL_CLOCK_MINUTES)
    if build:
        turns = _int(cfg.get("build_max_turns"), max(turns, DEFAULT_BUILD_MAX_TURNS))
        minutes = _int(
            cfg.get("build_max_wall_clock_minutes"),
            max(minutes, DEFAULT_BUILD_MAX_WALL_CLOCK_MINUTES),
        )
    if less_minutes > 0:
        minutes = max(minutes - less_minutes, min(minutes, RUN_CAP_FLOOR_MINUTES))
    return turns, minutes


# Change 0004 (spec R4): the largest ``gate.drive_timeout`` the test and build jobs hold. With
# the R18 triage step's 5 minutes the test job is 190 + d <= 200 and the build and fix jobs
# 250 + d <= 260, so the drive adds at most 10 minutes over its default 300 s. A larger value
# is capped at (c) and (d); at (e) the drive's minutes come off the session's wall clock
# instead (``run_caps``' ``less_minutes``), never below the floor.
DRIVE_TIMEOUT_MAX_SECONDS = 600
DRIVE_CAPPED_PHASES = ("c", "d")
RUN_CAP_FLOOR_MINUTES = 30
DRIVE_PHASE = "e"  # the gate whose session gives up the drive's minutes
DRIVE_TIMEOUT_REFUSAL = (
    "gate.drive_timeout={n} exceeds the 600 s the test and build jobs hold: 600 applied; "
    "lower it, or raise timeout-minutes and SDLC_JOB_TIMEOUT_MINUTES together in a reviewed PR"
)


def drive_timeout_seconds(config: Any, gate_phase: str | None) -> int | None:
    """The drive's timeout at gate ``gate_phase``: ``gate.drive_timeout``, capped at
    ``DRIVE_TIMEOUT_MAX_SECONDS`` unless the gate is (e); None when no drive is set."""
    config = config if isinstance(config, dict) else {}
    if checks.drive_from_config(config) is None:
        return None
    seconds = checks.configured_drive_timeout(config)
    if gate_phase != DRIVE_PHASE:
        seconds = min(seconds, DRIVE_TIMEOUT_MAX_SECONDS)
    return seconds


def drive_timeout_refusal(config: Any) -> str | None:
    """Why the configured ``gate.drive_timeout`` is not the one applied at (c) and (d), or None
    when it is (or no drive is set)."""
    config = config if isinstance(config, dict) else {}
    if checks.drive_from_config(config) is None:
        return None
    seconds = checks.configured_drive_timeout(config)
    return DRIVE_TIMEOUT_REFUSAL.format(n=seconds) if seconds > DRIVE_TIMEOUT_MAX_SECONDS else None


def drive_minutes(config: Any) -> int:
    """The minutes the drive takes off the (e) session's wall clock: ``ceil(drive_timeout /
    60)`` when a drive is set, else 0."""
    seconds = drive_timeout_seconds(config, DRIVE_PHASE)
    return math.ceil(seconds / 60) if seconds else 0


def iteration_cap(ctx: GateContext, classification: str | None) -> int:
    cap = _int(ctx.gate_setting("max_iterations", None), DEFAULT_MAX_ITERATIONS)
    if classification == "non-routine":
        tight = _int(
            ctx.gate_setting("max_iterations_non_routine", None),
            DEFAULT_MAX_ITERATIONS_NON_ROUTINE,
        )
        cap = max(1, min(cap, tight))
    return cap


def panel_cap(ctx: GateContext) -> int:
    """Panel calls per change (decision 21): ``gate.max_panel_calls``, default 4, whatever
    the classification (the panel is bounded by the budget and this count, not by the fix
    rounds)."""
    return _int(ctx.gate_setting("max_panel_calls", None), DEFAULT_MAX_PANEL_CALLS)


def classification_for(ctx: GateContext) -> str | None:
    """The adversarial reviewer's routine/non-routine call for this phase, or the latest one
    from an earlier gate (a classification made at (b) tightens (c) and (d))."""
    return classification_in(ctx.evidence_dir, ctx.phase)


def classification_in(evidence_dir: Path, phase: str) -> str | None:
    """``classification_for`` over an evidence folder: the counters read a shipped change's
    class the way the cap does (R26 part 2)."""
    from gate.checks import load_verdict

    for at in (phase, "d", "c", "b"):
        data, _ = load_verdict(Path(evidence_dir) / art.ADVERSARIAL_VERDICT.format(phase=at))
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


def _spend(value: Any) -> float | None:
    """A spend figure: a finite, non-negative number (``0.0`` counts); anything else - a
    NaN, which would make the total NaN and the cap never bind, an infinity, a negative
    figure, a string - is None."""
    n = _float(value)
    if n is None or not math.isfinite(n) or n < 0:
        return None
    return n


def read_spend_ledger(evidence_dir: Path) -> dict[str, Any]:
    """``evidence/spend.json``: ``{"total_usd": <sum>, "entries": [...]}``, each entry
    ``{"run", "source", "usd", "at"}``; an absent or unreadable file is an empty ledger,
    and an entry whose ``usd`` is not a finite, non-negative number is left out."""
    import json

    path = Path(evidence_dir) / SPEND_FILE
    empty = {"total_usd": 0.0, "entries": []}
    if not path.is_file():
        return empty
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return empty
    if not isinstance(data, dict) or not isinstance(data.get("entries"), list):
        return empty
    entries = [
        e for e in data["entries"] if isinstance(e, dict) and _spend(e.get("usd")) is not None
    ]
    return {"total_usd": round(sum(float(e["usd"]) for e in entries), 6), "entries": entries}


def record_spend_entry(
    evidence_dir: Path, run: str, source: str | None, usd: float, at: str | None = None
) -> dict[str, Any]:
    """Add one session's cost to the change's ledger and return the ledger. ``run`` names
    the run that spent it (``c``, ``review``, ``fix``); ``source`` the stored result it was
    read from (``claude-fix-2.json``), which makes the entry unique: a second record of the
    same source (a repeated step) replaces its entry instead of counting it twice."""
    import json

    if _spend(usd) is None:
        raise ValueError(f"a spend figure must be a finite, non-negative number, not {usd!r}")
    ledger = read_spend_ledger(evidence_dir)
    at = at or datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    entry = {"run": run, "source": source, "usd": float(usd), "at": at}
    entries = [e for e in ledger["entries"] if not (source and e.get("source") == source)] + [entry]
    ledger = {"total_usd": round(sum(float(e["usd"]) for e in entries), 6), "entries": entries}
    path = Path(evidence_dir) / SPEND_FILE
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(ledger, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n"
    )
    return ledger


# --- the run lines (R25 parts 1-2, M8 of the plugin security review; choice 257) ---------------
# The spend the budget and the PR read is rebuilt from the runner's own stored results, one
# ``evidence/claude-<run>[-<n>].json`` per session (``run_phase.store_result``), never from
# ``evidence/spend.json``: the session can write that ledger, and emptying it gave the next
# session the whole ``max_budget_usd`` again. The runner guards the stored results like its
# other files (``snapshot_run_records``, ``run_record_mismatches``). Each result carries the
# runner's ``sdlc_run`` fields: the credential that paid (``oauth`` the subscription token,
# ``api_key`` the key), the session's wall time and whether the runner's timeout stopped it.
# On the subscription token a run cannot be capped in dollars (NOTES §2), so its lines are
# counted in runs and time.
RUN_RECORD_RE = re.compile(r"^claude-(?P<run>[a-z]+)(?:-(?P<n>\d+))?\.json$")
RUN_META = "sdlc_run"
CREDENTIAL_WORDS = {"oauth": "subscription token", "api_key": "API key"}


def _record_order(path: Path) -> tuple[str, int]:
    m = RUN_RECORD_RE.match(path.name)
    return (m.group("run"), int(m.group("n") or 1)) if m else ("", 0)


def run_record_paths(evidence_dir: Path) -> list[Path]:
    """The stored session results in ``evidence_dir``, ordered by run and number."""
    found = [p for p in Path(evidence_dir).glob("claude-*.json") if RUN_RECORD_RE.match(p.name)]
    return sorted(found, key=_record_order)


def run_lines(evidence_dir: Path) -> list[dict[str, Any]]:
    """One line per stored session result: ``source``, ``run``, ``usd`` (None when the
    session reported no figure: a timeout, a crash), ``credential``, ``seconds``, ``turns``
    and ``stop`` (the CLI's error subtype, or ``timeout``)."""
    lines = []
    for path in run_record_paths(evidence_dir):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            data = None
        data = data if isinstance(data, dict) else {}
        meta = data.get(RUN_META) if isinstance(data.get(RUN_META), dict) else {}
        seconds = _spend(meta.get("seconds"))
        if seconds is None and _spend(data.get("duration_ms")) is not None:
            seconds = float(data["duration_ms"]) / 1000.0
        subtype = data.get("subtype")
        stop = (
            "timeout"
            if meta.get("timed_out")
            else (subtype if isinstance(subtype, str) and subtype.startswith("error") else None)
        )
        lines.append(
            {
                "source": path.name,
                "run": RUN_RECORD_RE.match(path.name).group("run"),
                "usd": _spend(data.get("total_cost_usd")),
                "credential": meta.get("credential"),
                "seconds": round(seconds, 1) if seconds is not None else None,
                "turns": data.get("num_turns") if isinstance(data.get("num_turns"), int) else None,
                "stop": stop,
                "at": meta.get("at"),
            }
        )
    return lines


def spend_from_runs(evidence_dir: Path) -> dict[str, Any]:
    """The change's spend rebuilt from its run lines: ``total_usd`` (the figures that exist),
    ``entries`` (the lines with a figure, ``read_spend_ledger``'s shape), ``lines`` (all),
    ``unknown`` (sessions without a figure) and, per credential, the runs, seconds and USD."""
    lines = run_lines(evidence_dir)
    priced = [ln for ln in lines if ln["usd"] is not None]
    by: dict[str, dict[str, Any]] = {}
    for ln in lines:
        b = by.setdefault(
            str(ln["credential"] or "unknown"), {"runs": 0, "seconds": 0.0, "usd": 0.0}
        )
        b["runs"] += 1
        b["seconds"] = round(b["seconds"] + (ln["seconds"] or 0.0), 1)
        b["usd"] = round(b["usd"] + (ln["usd"] or 0.0), 6)
    return {
        "total_usd": round(sum(ln["usd"] for ln in priced), 6),
        "entries": [
            {"run": ln["run"], "source": ln["source"], "usd": ln["usd"], "at": ln["at"]}
            for ln in priced
        ],
        "lines": lines,
        "unknown": len(lines) - len(priced),
        "by_credential": by,
    }


def snapshot_run_records(evidence_dir: Path) -> dict[str, bytes]:
    """The stored session results as they stand right before a session (M8)."""
    out = {}
    for path in run_record_paths(evidence_dir):
        try:
            out[path.name] = path.read_bytes()
        except OSError:
            continue
    return out


def run_record_mismatches(
    evidence_dir: Path, before: dict[str, bytes], own: set[str] | frozenset[str] = frozenset()
) -> list[str]:
    """After a session: every stored result it created (``own``, the runner's own result of
    this session, aside), changed or deleted is put back as it was and named; the caller
    parks, as for the owner-only fields. Only the runner writes them (M8)."""
    reasons = []
    now = {p.name for p in run_record_paths(evidence_dir)}
    for name in sorted((now | set(before)) - set(own)):
        path = Path(evidence_dir) / name
        try:
            current = path.read_bytes() if path.is_file() else None
        except OSError:
            current = None
        was = before.get(name)
        if current == was:
            continue
        what = "created" if was is None else ("deleted" if current is None else "changed")
        reasons.append(f"evidence/{name}: the session {what} it; only the runner writes it")
        if was is None:
            path.unlink(missing_ok=True)
        else:
            path.write_bytes(was)
    return reasons


def _duration(seconds: float) -> str:
    minutes = int(round(seconds / 60.0))
    return f"{minutes // 60} h {minutes % 60:02d} min" if minutes >= 60 else f"{minutes} min"


def spend_line(evidence_dir: Path) -> str:
    """The PR's spend line (R25 part 2): the total in USD and, per credential, the runs and
    their time; "" when no session ran. The subscription token's runs are shown in runs and
    time first: they cannot be capped in dollars (NOTES §2)."""
    spent = spend_from_runs(evidence_dir)
    if not spent["lines"]:
        return ""
    n = len(spent["lines"])
    parts = []
    for key in ("oauth", "api_key", "unknown"):
        b = spent["by_credential"].get(key)
        if not b:
            continue
        word = CREDENTIAL_WORDS.get(key, "credential not recorded")
        runs = f"{b['runs']} run{'s' if b['runs'] != 1 else ''}"
        parts.append(f"{word}: {runs}, {_duration(b['seconds'])}, {b['usd']:.2f} USD")
    line = (
        f"Spend: {spent['total_usd']:.2f} USD over {n} session{'s' if n != 1 else ''} "
        f"({'; '.join(parts)})"
    )
    if spent["unknown"]:
        line += f"; {spent['unknown']} without a figure (a timeout or a crash), not counted"
    return line + "."


# --- the outer bounds park (R25 part 1) -----------------------------------------------------------
OUTER_BOUND_NEED = (
    "The session stopped at an outer bound before its gate; its partial evidence and its "
    "result record are committed on the branch. Read them, then either raise the bound in "
    "sdlc.yaml (gate.max_turns or gate.build_max_turns, gate.max_wall_clock_minutes or "
    "gate.build_max_wall_clock_minutes, gate.max_budget_usd; a reviewed PR) and re-run the "
    "phase, or finish by hand."
)
TIMEOUT_EXIT = 124  # run_phase.invoke's exit when the runner's timeout stopped the session


def outer_bound(data: Any, code: int, err: str = "") -> str | None:
    """The park reason of a session an outer bound stopped, else None: the CLI's turn limit
    (``error_max_turns``), its budget stop (``error_max_budget_usd``), or the runner's
    timeout (no result, exit 124)."""
    if isinstance(data, dict):
        subtype = data.get("subtype")
        if subtype == "error_max_turns":
            turns = data.get("num_turns")
            return (
                f"stopped at the turn limit ({turns} turns)"
                if turns
                else ("stopped at the turn limit")
            )
        if subtype == "error_max_budget_usd":
            cost = _spend(data.get("total_cost_usd"))
            return "stopped at the session's budget" + (
                f" ({cost:.2f} USD)" if cost is not None else ""
            )
        return None
    if code == TIMEOUT_EXIT:
        said = (err or "").strip().splitlines()
        return "stopped by the runner's timeout" + (f" ({said[-1]})" if said else "")
    return None


BUDGET_NEED = "Raise `gate.max_budget_usd` in sdlc.yaml (a reviewed PR) or finish by hand."


def budget_reason(total: float, budget: float, this_run: float | None = None) -> str:
    """The park reason of a spent per-change budget: the gate's ``limits`` check (``total``
    above ``budget``: exceeded), and the runner when nothing is left before a session starts
    (1.0.8; ``total`` equal to ``budget``: reached)."""
    run = f" (this run {this_run:.2f})" if this_run is not None else ""
    word = "exceeded" if total > budget else "reached"
    return f"budget {word}: {total:.2f} USD spent on the change{run}, budget {budget:.2f} USD"


def budget_left(gate_settings: Any, evidence_dir: Path) -> tuple[float, float, float] | None:
    """(cap, spent, left) of the change's budget (``gate.max_budget_usd``, the total rebuilt
    from the stored session results, ``spend_from_runs``; M8), or None when no cap is set.
    The runner passes ``left`` as the session's ``--max-budget-usd``: the cap is per change,
    so a session gets what the change has not spent yet, never the whole cap again (1.0.8)."""
    cfg = gate_settings if isinstance(gate_settings, dict) else {}
    cap = _spend(cfg.get("max_budget_usd"))
    if cap is None:
        return None
    spent = spend_from_runs(evidence_dir)["total_usd"]
    return cap, spent, round(max(cap - spent, 0.0), 6)


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
    # pause flag first: a paused repo runs nothing; a flag that is not a boolean stops it too
    try:
        paused = config_flag(ctx.config, "paused")
    except ConfigError as exc:
        return CheckResult(
            "limits",
            False,
            str(exc),
            "Fix sdlc.yaml: paused (a reviewed PR); the gate fails closed on a value it cannot "
            "read as a boolean.",
            {"stop": True, "paused": None},
        )
    if paused:
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
    calls_cap = panel_cap(ctx)
    details.update({"panel_calls": ctx.status.panel_calls, "panel_cap": calls_cap})
    if ctx.status.panel_calls > calls_cap:
        return CheckResult(
            "limits",
            False,
            f"panel-call cap reached: {ctx.status.panel_calls} panel calls, cap {calls_cap}",
            "Read the decisions ledger, then either settle the rest by hand, or apply "
            "`sdlc:reset-iterations` (it resets both counts) or raise `gate.max_panel_calls` "
            "in sdlc.yaml (a reviewed PR) to allow more.",
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
    # the build run and a fix round carry ``"run": "build"`` (``start-run``); an older record
    # has no field and gets the general cap, as before 1.0.8
    build = run.get("run") == BUILD_RUN
    # change 0004: at (e) the drive's minutes came off the session's cap; the runner
    # subtracted the same figure (``run_phase.run_caps`` with the gate phase)
    less = drive_minutes(ctx.config) if ctx.phase == DRIVE_PHASE else 0
    _turns, max_minutes = run_caps(ctx.config.get("gate"), build, less)
    _turns, whole = run_caps(ctx.config.get("gate"), build)
    if less and whole - less < RUN_CAP_FLOOR_MINUTES:
        return CheckResult(
            "limits",
            False,
            f"gate.drive_timeout takes {less} min off the (e) session's {whole} min, below the "
            f"floor of {RUN_CAP_FLOOR_MINUTES} min",
            "Lower gate.drive_timeout or raise the wall-clock cap in sdlc.yaml (a reviewed PR), "
            "then re-run the phase.",
            {**details, "stop": False, "drive_minutes": less, "max_wall_clock_minutes": whole},
        )
    if less:
        details["drive_minutes"] = less
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
    spend = _float(run.get("spend_usd"))  # the last session of this phase (the run record)
    ledger = spend_from_runs(ctx.evidence_dir)
    # the change's running total (issue #71), rebuilt from the stored session results (M8);
    # a change with none (a by-hand run) has only the run record's figure
    total = ledger["total_usd"] if ledger["entries"] else spend
    details.update(
        {
            "spend_usd": spend,
            "spend_usd_total": total,
            "spend_entries": len(ledger["entries"]),
            "max_budget_usd": budget,
        }
    )
    if budget is not None and total is not None and total > budget:
        return CheckResult(
            "limits",
            False,
            budget_reason(total, budget, spend),
            BUDGET_NEED,
            {**details, "stop": True},
        )
    return CheckResult("limits", True, "within the run limits", details=details)
