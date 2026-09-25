"""The bands.yaml reader of phase (f) maintain (build guide step 37.1; article p.43-44).

``bands.yaml`` sits at the project root (written by ``/sdlc-init`` from
``template/bands.yaml``; project content the owner tunes). Keys:

- ``metric`` (required): what the detection script watches, e.g. ``ci_failure_rate``.
- ``source``: where the series comes from, e.g. ``github_actions``.
- ``baseline`` (default ``rolling_30d``): the rolling window, ``rolling_<N>d``.
- ``rules`` (default ``western_electric``, the only value this version knows).
- ``direction`` (optional, default ``above``): ``above`` when higher is worse (a failure
  rate), ``below`` when lower is worse (a pass rate, throughput), ``both`` for either side.
- ``min_sigma`` (optional, default ``0.0``): a floor under the standard deviation, for when
  a perfectly flat baseline makes every single failure a 3 sigma breach and the loop too loud.
- ``tiers``: ``1sigma``, ``2sigma``, ``3sigma``, each with an ``action`` (p.43 step 3: log,
  diagnose, propose); ``2sigma`` may name the read-only ``tools`` of the diagnosis and
  ``3sigma`` lists the ``routes`` (``name`` plus ``authorization``: ``preapproved`` or
  ``go``, decision 14). A route not listed is never taken.

Read with ``state.yamlish`` (no PyYAML at runtime). ``load`` raises ``BandsError`` (a
``ValueError``) with a one-line reason; ``validate`` returns the reasons.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

PLUGIN_DIR = Path(__file__).resolve().parent.parent
if str(PLUGIN_DIR) not in sys.path:
    sys.path.insert(0, str(PLUGIN_DIR))

from detect import stats  # noqa: E402
from state import yamlish  # noqa: E402

BANDS_FILE = "bands.yaml"
DEFAULT_BASELINE = "rolling_30d"
KNOWN_RULES = ("western_electric",)
TIER_KEYS = {"1sigma": 1, "2sigma": 2, "3sigma": 3}
AUTHORIZATIONS = ("preapproved", "go")


class BandsError(ValueError):
    """bands.yaml is missing or invalid; the message is one line."""


@dataclass
class Route:
    name: str  # "pull_request" | "runbook:<name>"
    authorization: str  # "preapproved" | "go"


@dataclass
class Bands:
    metric: str
    source: str
    baseline: str = DEFAULT_BASELINE
    rules: str = "western_electric"
    direction: str = "above"
    min_sigma: float = 0.0
    # 1: {"action": "log"}, 2: {"action": "diagnose", "tools": "..."},
    # 3: {"action": "propose", "routes": [Route, ...]}
    tiers: dict[int, dict[str, Any]] = field(default_factory=dict)

    @property
    def window_days(self) -> int:
        return stats.parse_baseline(self.baseline)

    def action(self, tier: int) -> str | None:
        """The action of a tier; None for tier 0 or a tier the file does not list."""
        return self.tiers.get(tier, {}).get("action") if tier else None

    def routes(self) -> list[Route]:
        """Tier 3's routes, in file order; [] when none."""
        return list(self.tiers.get(3, {}).get("routes") or [])

    def route(self, name: str) -> Route | None:
        return next((r for r in self.routes() if r.name == name), None)

    def diagnose_tools(self) -> str | None:
        return self.tiers.get(2, {}).get("tools")


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _nonempty_str(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def validate(data: Any) -> list[str]:
    """Every reason ``data`` is not a valid bands.yaml; [] when it is."""
    if not isinstance(data, dict):
        return ["bands.yaml is not a mapping"]
    reasons: list[str] = []
    if not _nonempty_str(data.get("metric")):
        reasons.append("missing metric")
    source = data.get("source")
    if source is not None and not isinstance(source, str):
        reasons.append("source is not a string")
    baseline = data.get("baseline", DEFAULT_BASELINE)
    try:
        stats.parse_baseline(baseline)
    except ValueError:
        reasons.append(f"unknown baseline {baseline!r}: expected rolling_<N>d")
    rules = data.get("rules", KNOWN_RULES[0])
    if rules not in KNOWN_RULES:
        reasons.append(f"unknown rules value {rules!r}: expected one of {', '.join(KNOWN_RULES)}")
    direction = data.get("direction", "above")
    if direction not in stats.DIRECTIONS:
        reasons.append(
            f"unknown direction {direction!r}: expected one of {', '.join(stats.DIRECTIONS)}"
        )
    min_sigma = data.get("min_sigma", 0.0)
    if not _is_number(min_sigma) or min_sigma < 0:
        reasons.append(f"min_sigma must be a number >= 0, got {min_sigma!r}")
    tiers = data.get("tiers")
    if tiers is None:
        return reasons
    if not isinstance(tiers, dict):
        return [*reasons, "tiers is not a mapping"]
    for key, tier in tiers.items():
        if key not in TIER_KEYS:
            reasons.append(f"unknown tier {key!r}: expected one of {', '.join(TIER_KEYS)}")
            continue
        if not isinstance(tier, dict) or not _nonempty_str(tier.get("action")):
            reasons.append(f"tier {key} has no action")
            continue
        tools = tier.get("tools")
        if tools is not None and not isinstance(tools, str):
            reasons.append(f"tier {key}: tools is not a string")
        routes = tier.get("routes")
        if routes is None:
            continue
        if not isinstance(routes, list):
            reasons.append(f"tier {key}: routes is not a list")
            continue
        for i, route in enumerate(routes, 1):
            if not isinstance(route, dict) or not _nonempty_str(route.get("name")):
                reasons.append(f"tier {key}: route {i} has no name")
                continue
            auth = route.get("authorization")
            if auth not in AUTHORIZATIONS:
                reasons.append(
                    f"tier {key}: route {route['name']} has authorization {auth!r}, "
                    f"expected one of {', '.join(AUTHORIZATIONS)}"
                )
    return reasons


def _tiers(raw: dict[str, Any]) -> dict[int, dict[str, Any]]:
    out: dict[int, dict[str, Any]] = {}
    for key, tier in raw.items():
        entry = dict(tier)
        if "routes" in entry:
            entry["routes"] = [
                Route(name=r["name"], authorization=r["authorization"])
                for r in entry["routes"] or []
            ]
        out[TIER_KEYS[key]] = entry
    return out


def load(path: Path) -> Bands:
    """The bands of ``path``; ``BandsError`` with a one-line reason when missing or invalid."""
    path = Path(path)
    if not path.is_file():
        raise BandsError(f"{path.name} not found: {path}")
    try:
        data = yamlish.load_file(path)
    except (OSError, UnicodeDecodeError, yamlish.YamlishError) as exc:
        detail = str(exc).splitlines()[0] if str(exc) else type(exc).__name__
        raise BandsError(f"cannot read {path.name}: {detail}") from exc
    reasons = validate(data)
    if reasons:
        raise BandsError(f"invalid {path.name}: {'; '.join(reasons)}")
    return Bands(
        metric=data["metric"].strip(),
        source=(data.get("source") or "").strip(),
        baseline=data.get("baseline", DEFAULT_BASELINE),
        rules=data.get("rules", KNOWN_RULES[0]),
        direction=data.get("direction", "above"),
        min_sigma=float(data.get("min_sigma", 0.0)),
        tiers=_tiers(data.get("tiers") or {}),
    )


def load_project(root: Path) -> Bands:
    """The project's bands: ``root / bands.yaml``."""
    return load(Path(root) / BANDS_FILE)
