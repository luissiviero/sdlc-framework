"""The digest's Actions-minutes meter (R25, R60's port of 2026-10-20, choice 257): on a private
repository the digest shows "Actions minutes this month: n of m" and warns at 80%; a public
repository's runs are free and get no line. No ``sdlc.yaml`` key (the owner's answer to the
port's question 1, ``docs/reviews/2026-10-20-lifecycle-axis-ports/options.md``, section 3).

The figure is an estimate read with the digest workflow's ``actions: read``: every job of
every run created since the first of the month (UTC), its time rounded up to the next minute
as GitHub bills a job, with no minute multiplier (a Windows or macOS job costs more, and the
job's own usage page leaves the multiplier out too). At most ``MAX_RUNS`` runs are read, one
request each, so a busy month is reported as "at least". The allowance ``m`` is GitHub Free's
2,000 minutes a month for a personal account; the plan's own figure is not readable with a
repository token and was not verified.
"""

from __future__ import annotations

import math
from collections.abc import Callable
from datetime import datetime
from typing import Any

INCLUDED_MINUTES = 2000  # GitHub Free, a personal account's private repositories
WARN_SHARE = 0.8
MAX_RUNS = 300
API = "https://api.github.com"
LINE = (
    "Actions minutes this month: {at_least}{used} of {included} (an estimate: each job rounded "
    "up to the minute, no multiplier; private repository)"
)
WARNING = (
    "**Actions minutes at {share}% of {included} this month**: past the allowance GitHub "
    "bills the account or stops the runs; slow the runs down or raise the account's limit."
)

Request = Callable[[str], dict[str, Any]]  # url -> {"status", "data", "error", "headers"}


def _minutes(job: dict[str, Any]) -> int:
    try:
        start = datetime.fromisoformat(str(job["started_at"]).replace("Z", "+00:00"))
        end = datetime.fromisoformat(str(job["completed_at"]).replace("Z", "+00:00"))
    except (KeyError, TypeError, ValueError):
        return 0
    seconds = (end - start).total_seconds()
    return math.ceil(seconds / 60.0) if seconds > 0 else 0


def _next(result: dict[str, Any]) -> str | None:
    from pr.github import next_page_url  # noqa: PLC0415

    return next_page_url(result)


def month_minutes(repo: str, now: datetime, get: Request) -> dict[str, Any]:
    """``{"ok", "private", "minutes", "runs", "truncated"}``, or ``ok`` false with ``reason``.
    ``get`` is a GET with the run's token (``github._request``)."""
    info = get(f"{API}/repos/{repo}")
    if info.get("error"):
        return {"ok": False, "reason": f"repository: {info['error']}"}
    if not (info.get("data") or {}).get("private"):
        return {"ok": True, "private": False}
    since = now.strftime("%Y-%m-01")
    url: str | None = f"{API}/repos/{repo}/actions/runs?created=%3E%3D{since}&per_page=100"
    runs: list[dict[str, Any]] = []
    truncated = False
    while url:
        page = get(url)
        if page.get("error"):
            return {"ok": False, "reason": f"runs: {page['error']}"}
        runs += [
            r for r in (page.get("data") or {}).get("workflow_runs") or [] if isinstance(r, dict)
        ]
        if len(runs) >= MAX_RUNS:
            truncated = len(runs) > MAX_RUNS or bool(_next(page))
            runs = runs[:MAX_RUNS]
            break
        url = _next(page)
    minutes = 0
    for run in runs:
        jobs = get(f"{API}/repos/{repo}/actions/runs/{run.get('id')}/jobs?filter=all&per_page=100")
        if jobs.get("error"):
            return {"ok": False, "reason": f"jobs of run {run.get('id')}: {jobs['error']}"}
        minutes += sum(_minutes(j) for j in (jobs.get("data") or {}).get("jobs") or [])
    return {
        "ok": True,
        "private": True,
        "minutes": minutes,
        "runs": len(runs),
        "truncated": truncated,
    }


def render(meter: dict[str, Any]) -> str:
    """The digest's lines for the meter: "" for a public repository or a failed read (the
    run's log says why), the line, and the warning first at ``WARN_SHARE`` or above."""
    if not meter.get("ok") or not meter.get("private"):
        return ""
    used = int(meter.get("minutes") or 0)
    line = LINE.format(
        used=f"{used:,}",
        at_least="at least " if meter.get("truncated") else "",
        included=f"{INCLUDED_MINUTES:,}",
    )
    if used >= WARN_SHARE * INCLUDED_MINUTES:
        share = int(used * 100 / INCLUDED_MINUTES)
        return WARNING.format(share=share, included=f"{INCLUDED_MINUTES:,}") + "\n\n" + line
    return line
