"""Layer-1 tests of the digest's Actions-minutes meter (R25, R60's port; ``pr/actions_minutes.py``):
a private repository's minutes this month, each job rounded up to the minute, warned at 80%
of the allowance; a public repository gets no line."""

from __future__ import annotations

from datetime import datetime, timezone

from pr import actions_minutes as am
from pr import digest as digest_mod

NOW = datetime(2026, 10, 23, 12, 0, tzinfo=timezone.utc)


def job(start: str, end: str) -> dict:
    return {"started_at": f"2026-10-{start}Z", "completed_at": f"2026-10-{end}Z"}


def fake_get(private: bool, runs: list[dict], jobs: dict, pages: int = 1):
    seen: list[str] = []

    def get(url: str) -> dict:
        seen.append(url)
        if url.endswith("/repos/o/r"):
            return {"status": 200, "data": {"private": private}, "error": ""}
        if "/actions/runs?" in url:
            assert "created=%3E%3D2026-10-01" in url  # since the first of the month (UTC)
            return {"status": 200, "data": {"workflow_runs": runs}, "error": "", "headers": {}}
        run_id = int(url.split("/runs/")[1].split("/")[0])
        return {"status": 200, "data": {"jobs": jobs.get(run_id, [])}, "error": ""}

    return get, seen


def test_a_public_repository_reads_no_runs_and_gets_no_line():
    get, seen = fake_get(False, [{"id": 1}], {})
    meter = am.month_minutes("o/r", NOW, get)
    assert meter == {"ok": True, "private": False}
    assert len(seen) == 1 and am.render(meter) == ""


def test_each_job_is_rounded_up_to_the_minute():
    jobs = {
        1: [job("23T10:00:00", "23T10:00:01"), job("23T10:00:00", "23T10:02:00")],  # 1 + 2
        2: [job("23T11:00:00", "23T11:10:30"), {"started_at": None}],  # 11 + 0 (not finished)
    }
    meter = am.month_minutes("o/r", NOW, fake_get(True, [{"id": 1}, {"id": 2}], jobs)[0])
    assert meter == {"ok": True, "private": True, "minutes": 14, "runs": 2, "truncated": False}
    assert am.render(meter) == (
        "Actions minutes this month: 14 of 2,000 (an estimate: each job rounded up to the "
        "minute, no multiplier; private repository)"
    )


def test_the_warning_comes_first_at_eighty_percent():
    line = am.render({"ok": True, "private": True, "minutes": 1600, "runs": 9})
    warning, meter = line.split("\n\n")
    assert warning.startswith("**Actions minutes at 80% of 2,000 this month**")
    assert meter.startswith("Actions minutes this month: 1,600 of 2,000")
    assert "**" not in am.render({"ok": True, "private": True, "minutes": 1599, "runs": 9})


def test_a_busy_month_reads_at_most_max_runs_and_says_at_least(monkeypatch):
    monkeypatch.setattr(am, "MAX_RUNS", 2)
    runs = [{"id": i} for i in range(1, 4)]
    jobs = {i: [job("23T10:00:00", "23T10:01:00")] for i in range(1, 4)}
    meter = am.month_minutes("o/r", NOW, fake_get(True, runs, jobs)[0])
    assert (meter["runs"], meter["minutes"], meter["truncated"]) == (2, 2, True)
    assert am.render(meter).startswith("Actions minutes this month: at least 2 of 2,000")


def test_a_failed_read_says_why_and_renders_nothing():
    def get(url: str) -> dict:
        return {"status": 403, "data": {}, "error": "Resource not accessible by integration"}

    meter = am.month_minutes("o/r", NOW, get)
    assert not meter["ok"] and "Resource not accessible" in meter["reason"]
    assert am.render(meter) == ""


def test_the_digest_shows_the_meter_near_the_top():
    md = digest_mod.render_digest([], "2026-10-23T12:00:00Z", meter="Actions minutes this month")
    assert md.index("Actions minutes this month") < md.index(digest_mod.NOTHING_WAITING)


def test_the_meter_asks_nothing_without_a_token(monkeypatch):
    monkeypatch.setattr(digest_mod.github, "token", lambda: None)
    monkeypatch.setattr(
        digest_mod.github, "_request", lambda *a, **k: (_ for _ in ()).throw(AssertionError)
    )
    assert digest_mod.minutes_meter("o/r") == ""
