"""Control-band statistics of phase (f) maintain (build guide step 37.1; article p.43-45).

The article asks for the "mean and standard deviation over a rolling window with rules
(Western Electric or similar) so the bands catch slow drift as well as spikes" (p.43), and
for detection that "stays entirely deterministic, with no model involved" (p.43). The response
tiers are 1 sigma log, 2 sigma diagnose, 3 sigma propose (p.43 step 3). Everything below is
the framework's reading of "Western Electric or similar"; the article says nothing more.

Pure functions: no I/O, no clock, no randomness, no model. The latest point's ``at`` is "now".

1. Series: a list of ``Point`` sorted ascending by ``at`` (``sort_points``). ``at`` is an
   ISO-8601 date or datetime; a trailing ``Z`` means UTC, a bare date is midnight UTC and a
   datetime without an offset is read as UTC. Duplicate instants: the last one given wins.
2. Window: ``baseline: rolling_<N>d`` gives ``window_days = N`` (``parse_baseline``). Only
   the points with ``latest.at - N days <= at <= latest.at`` count (``window``).
3. Tail and baseline: the baseline never contains the points it judges. The tail is the last
   ``TAIL = 8`` points of the window (the span of the longest rule); the baseline is every
   older point of the window. ``mean`` is the arithmetic mean of the baseline values and
   ``sigma`` their sample standard deviation (n - 1), floored at ``min_sigma``. Fewer than
   ``MIN_BASELINE = 8`` baseline points: tier 0, "insufficient baseline", no rule evaluated.
4. Direction: ``above`` (the default: higher is worse, such as a failure rate), ``below`` or
   ``both``. A point is "beyond k sigma" when ``(value - mean) / sigma >= k`` for ``above``,
   ``<= -k`` for ``below`` and ``abs(...) >= k`` for ``both``. The "same side" rules use the
   side the direction names (for ``both``: either side, all points on the same one). With
   ``sigma == 0`` a value equal to the mean is 0 sigmas away and any other value is
   ``math.inf`` sigmas away on its side, so a perfectly flat baseline followed by one failure
   is a 3 sigma breach (the article's own example, p.45). ``min_sigma`` (bands.yaml, default
   0.0) floors sigma before the division when a flat baseline makes the loop too loud.
5. Rules: the four classic Western Electric rules over the tail, most recent point last. Each
   rule needs a run of consecutive points that ends at the latest point (an older breach
   inside the tail was reported by an earlier run); a rule whose span exceeds the tail does
   not fire.

   - ``we1``: the latest point beyond 3 sigma.
   - ``we2``: two of the last three points beyond 2 sigma on the same side, the latest one
     of them.
   - ``we3``: four of the last five points beyond 1 sigma on the same side, the latest one
     of them.
   - ``we4``: the last eight points all strictly on the same side of the mean.
6. Tiers (``RULE_TIER``): ``we1`` 3; ``we2`` 2; ``we4`` 2 (eight points on one side is a
   shift of the mean: the slow drift p.43 wants diagnosed); ``we3`` 1 (the early warning that
   only logs). ``tier`` is the maximum over the rules hit and ``rule`` the rule that gives it
   (ties in the order ``we1``, ``we2``, ``we4``, ``we3``). ``breach_start`` is the ``at`` of
   the earliest point the deciding rule counted.
"""

from __future__ import annotations

import math
import re
from collections.abc import Iterable, Sequence
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any

TAIL = 8
MIN_BASELINE = 8
DIRECTIONS = ("above", "below", "both")
RULES = ("we1", "we2", "we3", "we4")  # rule order: the order of Verdict.rules_hit
RULE_TIER = {"we1": 3, "we2": 2, "we3": 1, "we4": 2}
TIER_ORDER = ("we1", "we2", "we4", "we3")  # which rule decides when two give the same tier
RULE_SPAN = {"we1": 1, "we2": 3, "we3": 5, "we4": 8}
BASELINE_RE = re.compile(r"^rolling_(?P<days>[0-9]+)d$")
_SIDES = {"above": (1,), "below": (-1,), "both": (1, -1)}


@dataclass(frozen=True)
class Point:
    """One observation: ``at`` (ISO-8601, UTC), the value, and free metadata."""

    at: str
    value: float
    meta: dict[str, Any] = field(default_factory=dict)


@dataclass
class Verdict:
    """What ``evaluate`` concluded about the latest point. ``sigma`` is the standard deviation
    the rules used (the sample one floored at ``min_sigma``)."""

    tier: int
    rules_hit: list[str]
    rule: str | None
    latest: Point | None
    mean: float | None
    sigma: float | None
    sigmas: float | None
    n_baseline: int
    n_tail: int
    window_days: int
    direction: str
    reason: str
    breach_start: str | None

    def as_dict(self) -> dict[str, Any]:
        """A JSON-safe dict: a non-finite float becomes the string ``"inf"``, ``"-inf"`` or
        ``"nan"`` (strict JSON has no infinity)."""
        return _json_safe(asdict(self))


def _json_safe(value: Any) -> Any:
    if isinstance(value, float) and not math.isfinite(value):
        return str(value)
    if isinstance(value, dict):
        return {k: _json_safe(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_json_safe(v) for v in value]
    return value


def parse_baseline(baseline: str) -> int:
    """``rolling_<N>d`` -> N (N >= 1); anything else raises ``ValueError``."""
    m = BASELINE_RE.match(baseline.strip()) if isinstance(baseline, str) else None
    if not m or int(m.group("days")) < 1:
        raise ValueError(f"unknown baseline {baseline!r}: expected rolling_<N>d with N >= 1")
    return int(m.group("days"))


def parse_at(at: str) -> datetime:
    """An aware UTC datetime for an ISO-8601 date or datetime (``Z`` allowed)."""
    text = at.strip()
    if text.endswith(("Z", "z")):
        text = text[:-1] + "+00:00"
    dt = datetime.fromisoformat(text)
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def sort_points(points: Iterable[Point]) -> list[Point]:
    """The points ascending by ``at``; of two points at the same instant the last one wins."""
    by_instant: dict[datetime, Point] = {}
    for p in points:
        by_instant[parse_at(p.at)] = p
    return [by_instant[k] for k in sorted(by_instant)]


def window(points: list[Point], window_days: int) -> list[Point]:
    """The points of a sorted series with ``latest.at - window_days <= at <= latest.at``."""
    if not points:
        return []
    latest = parse_at(points[-1].at)
    start = latest - timedelta(days=window_days)
    return [p for p in points if start <= parse_at(p.at) <= latest]


def mean_std(values: Sequence[float]) -> tuple[float, float]:
    """The mean and the sample standard deviation (n - 1); ``(v, 0.0)`` for one value."""
    n = len(values)
    if n == 0:
        raise ValueError("mean_std of an empty sequence")
    mean = math.fsum(values) / n
    if n == 1:
        return mean, 0.0
    var = math.fsum((v - mean) ** 2 for v in values) / (n - 1)
    return mean, math.sqrt(var)


def sigmas_of(value: float, mean: float, sigma: float) -> float:
    """How many sigmas ``value`` is from ``mean`` (signed); with ``sigma == 0`` it is 0 for the
    mean itself and ``inf`` on the value's side for anything else."""
    if sigma == 0:
        if value == mean:
            return 0.0
        return math.inf if value > mean else -math.inf
    return (value - mean) / sigma


def _we1(zs: list[float], sides: tuple[int, ...]) -> int | None:
    """Index (into ``zs``) of the earliest point counted, or None when the rule is not met."""
    last = len(zs) - 1
    return last if any(side * zs[last] >= 3 for side in sides) else None


def _k_of_last(
    zs: list[float], sides: tuple[int, ...], k: int, of: int, beyond: float
) -> int | None:
    last = len(zs) - 1
    for side in sides:
        if side * zs[last] < beyond:
            continue
        counted = [i for i in range(len(zs) - of, len(zs)) if side * zs[i] >= beyond]
        if len(counted) >= k:
            return counted[0]
    return None


def _we4(zs: list[float], sides: tuple[int, ...]) -> int | None:
    span = RULE_SPAN["we4"]
    first = len(zs) - span
    for side in sides:
        if all(side * z > 0 for z in zs[first:]):
            return first
    return None


def _fmt(x: float) -> str:
    if math.isinf(x):
        return "inf" if x > 0 else "-inf"
    return f"{x:.4g}"


def evaluate(
    points: Iterable[Point],
    *,
    window_days: int = 30,
    direction: str = "above",
    min_sigma: float = 0.0,
    tail: int = TAIL,
    min_baseline: int = MIN_BASELINE,
) -> Verdict:
    """The verdict on the latest point of ``points`` (see the module docstring)."""
    if direction not in DIRECTIONS:
        raise ValueError(f"unknown direction {direction!r}: expected one of {DIRECTIONS}")
    if not isinstance(window_days, int) or window_days <= 0:
        raise ValueError(f"window_days must be a positive integer, got {window_days!r}")
    if tail < 1 or min_baseline < 1:
        raise ValueError("tail and min_baseline must be at least 1")
    if min_sigma < 0:
        raise ValueError(f"min_sigma must not be negative, got {min_sigma!r}")

    def verdict(**kw: Any) -> Verdict:
        base = {
            "tier": 0,
            "rules_hit": [],
            "rule": None,
            "latest": None,
            "mean": None,
            "sigma": None,
            "sigmas": None,
            "n_baseline": 0,
            "n_tail": 0,
            "window_days": window_days,
            "direction": direction,
            "reason": "",
            "breach_start": None,
        }
        base.update(kw)
        return Verdict(**base)

    series = window(sort_points(points), window_days)
    if not series:
        return verdict(reason="no observations")
    latest = series[-1]
    tail_points = series[-tail:]
    baseline = series[: len(series) - len(tail_points)]
    counts = {"latest": latest, "n_baseline": len(baseline), "n_tail": len(tail_points)}
    if len(baseline) < min_baseline:
        return verdict(
            reason=(f"insufficient baseline: {len(baseline)} point(s), {min_baseline} needed"),
            **counts,
        )

    mean, sample_sigma = mean_std([p.value for p in baseline])
    sigma = max(sample_sigma, min_sigma)
    zs = [sigmas_of(p.value, mean, sigma) for p in tail_points]
    sides = _SIDES[direction]

    starts: dict[str, int | None] = {}
    for rule in RULES:
        if RULE_SPAN[rule] > len(zs):
            starts[rule] = None
        elif rule == "we1":
            starts[rule] = _we1(zs, sides)
        elif rule == "we2":
            starts[rule] = _k_of_last(zs, sides, 2, 3, 2)
        elif rule == "we3":
            starts[rule] = _k_of_last(zs, sides, 4, 5, 1)
        else:
            starts[rule] = _we4(zs, sides)
    hit = [rule for rule in RULES if starts[rule] is not None]

    latest_sigmas = zs[-1]
    stats = (
        f"latest value {_fmt(latest.value)} is {_fmt(latest_sigmas)} sigma from the mean "
        f"{_fmt(mean)} (sigma {_fmt(sigma)}, {len(baseline)} baseline point(s) over "
        f"{window_days}d, {direction})"
    )
    common = dict(counts, mean=mean, sigma=sigma, sigmas=latest_sigmas, rules_hit=hit)
    if not hit:
        return verdict(reason=f"within bands: {stats}; no rule fired", **common)
    tier = max(RULE_TIER[r] for r in hit)
    rule = next(r for r in TIER_ORDER if r in hit and RULE_TIER[r] == tier)
    start = tail_points[starts[rule]].at
    return verdict(
        tier=tier,
        rule=rule,
        breach_start=start,
        reason=(
            f"tier {tier} by {rule} (rules hit: {', '.join(hit)}): {stats}; breach since {start}"
        ),
        **common,
    )
