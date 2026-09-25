"""Detection statistics of phase (f) (build guide step 37.1; article p.43-45): the rolling
window, the tail/baseline split, the four Western Electric rules and their tiers, and the
bands.yaml reader, against synthetic series and a tmp bands.yaml."""

from __future__ import annotations

import json
import math
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from detect import bands, stats
from detect.stats import Point

TEMPLATE_BANDS = Path(__file__).resolve().parents[1] / "template" / "bands.yaml"
DAY0 = datetime(2026, 9, 1, tzinfo=timezone.utc)
# nine baseline values with mean exactly 10 and sample standard deviation exactly 1
BASE9 = [9.0, 11.0, 9.0, 11.0, 9.0, 11.0, 9.0, 11.0, 10.0]


def series(values: list[float], start: datetime = DAY0) -> list[Point]:
    """One point a day from ``start``."""
    return [
        Point(at=(start + timedelta(days=i)).strftime("%Y-%m-%dT%H:%M:%SZ"), value=v)
        for i, v in enumerate(values)
    ]


def judge(tail: list[float], **kw) -> stats.Verdict:
    """The verdict on BASE9 followed by an eight-point tail."""
    assert len(tail) == stats.TAIL
    return stats.evaluate(series(BASE9 + tail), **kw)


def mirror(values: list[float]) -> list[float]:
    return [20.0 - v for v in values]


# --- parsing, sorting, window ---------------------------------------------------------------


def test_parse_baseline_good_and_bad():
    assert stats.parse_baseline("rolling_30d") == 30
    assert stats.parse_baseline("rolling_7d") == 7
    for bad in ("rolling_0d", "rolling_30", "30d", "rolling_-1d", "fixed_30d", "", None):
        with pytest.raises(ValueError):
            stats.parse_baseline(bad)


def test_parse_at_forms_are_utc():
    assert stats.parse_at("2026-09-24") == datetime(2026, 9, 24, tzinfo=timezone.utc)
    assert stats.parse_at("2026-09-24T06:00:00Z") == datetime(2026, 9, 24, 6, tzinfo=timezone.utc)
    assert stats.parse_at("2026-09-24T08:00:00+02:00") == stats.parse_at("2026-09-24T06:00:00Z")
    assert stats.parse_at("2026-09-24T06:00:00") == stats.parse_at("2026-09-24T06:00:00Z")


def test_sort_points_orders_and_keeps_the_last_duplicate():
    pts = [
        Point("2026-09-03", 3.0),
        Point("2026-09-01", 1.0),
        Point("2026-09-02T00:00:00Z", 2.0),
        Point("2026-09-02", 22.0),
    ]
    out = stats.sort_points(pts)
    assert [p.value for p in out] == [1.0, 22.0, 3.0]


def test_window_boundaries():
    latest = Point("2026-09-30T12:00:00Z", 1.0)
    exactly = Point("2026-08-31T12:00:00Z", 2.0)  # exactly 30 days old: in
    too_old = Point("2026-08-31T11:59:59Z", 3.0)  # 30 days and 1 second: out
    out = stats.window([too_old, exactly, latest], 30)
    assert out == [exactly, latest]
    assert stats.window([], 30) == []


def test_mean_std():
    assert stats.mean_std(BASE9) == (10.0, 1.0)
    assert stats.mean_std([4.0]) == (4.0, 0.0)
    with pytest.raises(ValueError):
        stats.mean_std([])


def test_sigmas_of_zero_sigma():
    assert stats.sigmas_of(0.0, 0.0, 0.0) == 0.0
    assert stats.sigmas_of(1.0, 0.0, 0.0) == math.inf
    assert stats.sigmas_of(-1.0, 0.0, 0.0) == -math.inf
    assert stats.sigmas_of(13.0, 10.0, 1.0) == 3.0


# --- evaluate: guards -----------------------------------------------------------------------


def test_empty_series_is_tier_zero():
    v = stats.evaluate([])
    assert v.tier == 0 and v.reason == "no observations" and v.latest is None
    assert v.n_baseline == 0 and v.n_tail == 0


def test_bad_direction_and_window_raise():
    with pytest.raises(ValueError):
        stats.evaluate(series([1.0]), direction="up")
    with pytest.raises(ValueError):
        stats.evaluate(series([1.0]), window_days=0)
    with pytest.raises(ValueError):
        stats.evaluate(series([1.0]), window_days=-3)


def test_insufficient_baseline():
    v = stats.evaluate(series([0.0] * 14 + [1.0]))
    assert v.tier == 0 and v.rules_hit == [] and v.rule is None
    assert v.n_baseline == 7 and v.n_tail == 8
    assert v.reason == "insufficient baseline: 7 point(s), 8 needed"
    assert v.mean is None and v.sigma is None and v.sigmas is None


def test_window_drops_old_points_from_the_baseline():
    # 8 flat points 40 days before the rest: outside a 30-day window, so the baseline is short
    old = series([0.0] * 8, start=DAY0 - timedelta(days=40))
    recent = series([0.0] * 8 + [1.0])
    v = stats.evaluate(old + recent)
    assert v.tier == 0 and v.n_baseline == 1
    assert stats.evaluate(old + recent, window_days=60).tier == 3


# --- evaluate: rules ------------------------------------------------------------------------


def test_flat_baseline_then_one_failure_is_we1_tier_3():
    pts = series([0.0] * 15 + [1.0])
    v = stats.evaluate(pts)
    assert v.tier == 3 and v.rule == "we1" and v.rules_hit == ["we1"]
    assert v.sigma == 0.0 and v.sigmas == math.inf
    assert v.breach_start == pts[-1].at
    assert v.latest == pts[-1]
    assert json.loads(json.dumps(v.as_dict()))["sigmas"] == "inf"


def test_spike_at_exactly_three_sigma_fires():
    v = judge([10.0] * 7 + [13.0])
    assert v.mean == 10.0 and v.sigma == 1.0 and v.sigmas == 3.0
    assert v.tier == 3 and v.rule == "we1"
    assert judge([10.0] * 7 + [12.99]).tier == 0


def test_two_of_three_beyond_two_sigma():
    v = judge([10.0] * 5 + [12.0, 10.0, 12.5])
    assert v.rules_hit == ["we2"] and v.tier == 2
    assert v.breach_start == series(BASE9 + [0.0] * 8)[-3].at


def test_two_of_three_with_the_older_two_only_does_not_fire():
    v = judge([10.0] * 5 + [12.0, 12.0, 10.0])
    assert v.tier == 0 and v.rules_hit == []


def test_four_of_five_beyond_one_sigma_is_tier_1():
    pts = series(BASE9 + [10.0] * 3 + [11.0, 10.0, 11.5, 11.2, 11.0])
    v = stats.evaluate(pts)
    assert v.rules_hit == ["we3"] and v.tier == 1 and v.rule == "we3"
    assert v.breach_start == pts[-5].at


def test_eight_on_one_side_is_tier_2_from_eight_points_back():
    pts = series(BASE9 + [10.5] * 8)
    v = stats.evaluate(pts)
    assert v.rules_hit == ["we4"] and v.tier == 2 and v.rule == "we4"
    assert v.breach_start == pts[-8].at


def test_below_mirrors_above():
    tail = [10.0] * 5 + [12.0, 10.0, 12.5]
    above = judge(tail)
    below = judge(mirror(tail), direction="below")
    assert (below.tier, below.rules_hit, below.breach_start) == (
        above.tier,
        above.rules_hit,
        above.breach_start,
    )
    # the wrong direction sees nothing
    assert judge(mirror(tail), direction="above").tier == 0
    assert judge(tail, direction="below").tier == 0
    assert judge([9.5] * 8, direction="below").rules_hit == ["we4"]


def test_both_catches_either_side():
    assert judge([10.0] * 7 + [13.0], direction="both").rule == "we1"
    assert judge([10.0] * 7 + [7.0], direction="both").rule == "we1"
    assert judge([9.5] * 8, direction="both").rules_hit == ["we4"]
    # two points beyond 2 sigma but on opposite sides: no two-of-three
    assert judge([10.0] * 5 + [7.9, 10.0, 12.1], direction="both").rules_hit == []


def test_min_sigma_floors_the_standard_deviation():
    pts = series([0.0] * 15 + [1.0])
    v = stats.evaluate(pts, min_sigma=0.5)
    assert v.sigma == 0.5 and v.sigmas == 2.0 and v.tier == 0
    assert stats.evaluate(pts, min_sigma=0.25).tier == 3
    with pytest.raises(ValueError):
        stats.evaluate(pts, min_sigma=-1.0)


def test_several_rules_take_the_max_tier_and_rule_order():
    # all eight above the mean, the last five beyond 1 sigma, the last three beyond 2 sigma,
    # the latest beyond 3 sigma: every rule fires, we1 decides
    pts = series(BASE9 + [10.5, 10.5, 10.5, 11.5, 11.5, 12.5, 12.5, 13.5])
    v = stats.evaluate(pts)
    assert v.rules_hit == ["we1", "we2", "we3", "we4"]
    assert v.tier == 3 and v.rule == "we1" and v.breach_start == pts[-1].at
    # we2 and we4 tie at tier 2: we2 decides
    pts = series(BASE9 + [10.5] * 6 + [12.5, 12.5])
    v = stats.evaluate(pts)
    assert v.rules_hit == ["we2", "we4"] and v.tier == 2 and v.rule == "we2"
    assert v.breach_start == pts[-2].at
    # we3 and we4: tier 2 by we4
    v = stats.evaluate(series(BASE9 + [10.5] * 4 + [11.5] * 4))
    assert v.rules_hit == ["we3", "we4"] and v.rule == "we4"


def test_a_run_that_ended_before_the_latest_point_does_not_fire():
    assert judge([10.0] * 6 + [14.0, 10.0]).tier == 0  # an older spike
    assert judge([10.0] * 3 + [11.5] * 4 + [10.0]).tier == 0  # four of five, then back
    assert judge([10.5] * 7 + [9.5]).tier == 0  # seven above, then below


def test_short_tail_rules_do_not_fire():
    v = stats.evaluate(series([0.0] * 10 + [1.0] * 2), tail=2, min_baseline=8)
    assert v.n_tail == 2 and v.rules_hit == ["we1"]


def test_evaluate_is_order_independent_and_deterministic():
    pts = series(BASE9 + [10.0] * 7 + [13.0])
    assert stats.evaluate(list(reversed(pts))) == stats.evaluate(pts)
    assert stats.evaluate(pts).as_dict() == stats.evaluate(pts).as_dict()


# --- bands.yaml -----------------------------------------------------------------------------


def _write_bands(tmp_path: Path, text: str) -> Path:
    path = tmp_path / bands.BANDS_FILE
    path.write_text(text, encoding="utf-8")
    return path


def _rendered_template() -> str:
    text = TEMPLATE_BANDS.read_text(encoding="utf-8")
    return text.replace("{{MAINTAIN_METRIC}}", "ci_failure_rate").replace(
        "{{MAINTAIN_SOURCE}}", "github_actions"
    )


def test_load_rendered_template(tmp_path):
    _write_bands(tmp_path, _rendered_template())
    b = bands.load_project(tmp_path)
    assert (b.metric, b.source, b.baseline, b.rules) == (
        "ci_failure_rate",
        "github_actions",
        "rolling_30d",
        "western_electric",
    )
    assert b.window_days == 30 and b.direction == "above" and b.min_sigma == 0.0
    assert [b.action(t) for t in (0, 1, 2, 3)] == [None, "log", "diagnose", "propose"]
    assert b.diagnose_tools() == "Read,Grep,Bash(gh run view *)"
    assert [(r.name, r.authorization) for r in b.routes()] == [
        ("pull_request", "preapproved"),
        ("runbook:quarantine-flaky-test", "preapproved"),
        ("runbook:revert-pr", "preapproved"),
        ("runbook:rollback-deploy", "go"),
    ]
    assert b.route("runbook:rollback-deploy") == bands.Route("runbook:rollback-deploy", "go")
    assert b.route("runbook:unknown") is None


def test_load_optional_direction_and_min_sigma(tmp_path):
    text = _rendered_template().replace(
        "rules: western_electric", "rules: western_electric\ndirection: below\nmin_sigma: 0.05"
    )
    b = bands.load(_write_bands(tmp_path, text))
    assert b.direction == "below" and b.min_sigma == 0.05


def test_load_missing_file(tmp_path):
    with pytest.raises(bands.BandsError, match="not found"):
        bands.load_project(tmp_path)


def test_load_unrendered_template_is_a_one_line_error(tmp_path):
    path = _write_bands(tmp_path, TEMPLATE_BANDS.read_text(encoding="utf-8"))
    with pytest.raises(bands.BandsError) as exc:
        bands.load(path)
    assert "\n" not in str(exc.value)


def test_load_invalid_raises_bands_error_one_line(tmp_path):
    path = _write_bands(tmp_path, _rendered_template().replace("rules: western_electric", ""))
    assert bands.load(path).rules == "western_electric"  # absent: the default
    path = _write_bands(tmp_path, "source: x\nrules: nelson\n")
    with pytest.raises(bands.BandsError) as exc:
        bands.load(path)
    assert isinstance(exc.value, ValueError) and "\n" not in str(exc.value)
    assert "missing metric" in str(exc.value) and "unknown rules value" in str(exc.value)


VALID = {
    "metric": "ci_failure_rate",
    "source": "github_actions",
    "baseline": "rolling_30d",
    "rules": "western_electric",
    "tiers": {
        "1sigma": {"action": "log"},
        "2sigma": {"action": "diagnose", "tools": "Read"},
        "3sigma": {
            "action": "propose",
            "routes": [{"name": "pull_request", "authorization": "preapproved"}],
        },
    },
}


def _with(**changes) -> dict:
    data = json.loads(json.dumps(VALID))
    data.update(changes)
    return data


def _tier3(**route) -> dict:
    return _with(tiers={"3sigma": {"action": "propose", "routes": [route]}})


@pytest.mark.parametrize(
    ("data", "reason"),
    [
        ("not a mapping", "bands.yaml is not a mapping"),
        (_with(metric=""), "missing metric"),
        ({k: v for k, v in VALID.items() if k != "metric"}, "missing metric"),
        (_with(rules="nelson"), "unknown rules value 'nelson'"),
        (_with(baseline="weekly"), "unknown baseline 'weekly'"),
        (_with(direction="up"), "unknown direction 'up'"),
        (_with(min_sigma=-0.1), "min_sigma must be a number >= 0"),
        (_with(min_sigma="low"), "min_sigma must be a number >= 0"),
        (_with(tiers=["log"]), "tiers is not a mapping"),
        (_with(tiers={"4sigma": {"action": "page"}}), "unknown tier '4sigma'"),
        (_with(tiers={"1sigma": {"tools": "Read"}}), "tier 1sigma has no action"),
        (_with(tiers={"1sigma": None}), "tier 1sigma has no action"),
        (_with(tiers={"3sigma": {"action": "propose", "routes": "x"}}), "routes is not a list"),
        (_tier3(authorization="go"), "tier 3sigma: route 1 has no name"),
        (_tier3(name="runbook:x", authorization="auto"), "has authorization 'auto'"),
        (_tier3(name="runbook:x"), "has authorization None"),
    ],
)
def test_validate_failure_reasons(data, reason):
    reasons = bands.validate(data)
    assert len(reasons) == 1
    assert reasons[0].startswith(reason) or reason in reasons[0]


def test_validate_valid():
    assert bands.validate(VALID) == []
