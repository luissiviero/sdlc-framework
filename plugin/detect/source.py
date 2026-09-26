"""The metric source of the detection script: CI test failure rate per UTC day (build guide
step 37, decision 15).

The article asks for "a metrics store the detection script can query (Prometheus, the CI
system's API, or equivalents)" (p.43); decision 15 makes the first metric the CI test failure
rate because it "needs only the CI API". This module reads the GitHub Actions runs API and
turns it into one observation per UTC day::

    {"at": "YYYY-MM-DD", "value": failed / total,
     "meta": {"runs": total, "failed": failed, "failed_run_ids": [...],
              "failed_run_urls": [...]}}

Observations are plain dicts (``Observation``) so this module does not depend on
``detect.stats``; the caller converts them.

A run counts when it completed with ``success`` or ``failure``, was started by a counted
event, is not one of the framework's own ``SDLC ...`` workflows (they end green by design
and are not the project's test suite), and was not started by an excluded actor (default
``DEFAULT_EXCLUDED_ACTORS``, the framework's automation identity). The last rule exists
because a ``pull_request`` event caused by the workflow token starts no run, yet GitHub still
records one that ends ``completed`` / ``failure`` with zero jobs: on 2026-09-25 the sample
repository's ``CI`` listing held nine such runs among 23, so the day's rate would have read
0.39 on a day when no test failed. Only the automation identity is excluded, not every
``[bot]`` actor: Dependabot's ``pull_request`` runs are real test runs. A local JSON cache
keeps the runs already seen, so a daily fetch only asks for the last few days.

No third-party dependency (decision 7), a 30 s timeout on every request (``TIMEOUT`` of
``pr.github``), and the token only ever reaches an ``Authorization`` header inside
``_http_get``, the single HTTP entry point (so tests monkeypatch one function or pass a fake
``get_pages``).
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
import urllib.error
import urllib.request
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pr import github  # noqa: E402

Observation = dict[str, Any]
GetPages = Callable[[str], list[dict[str, Any]]]

SOURCE_KIND = "github-actions"
MAX_PAGES = 10  # 1000 runs per fetch; the API returns newest first
REFETCH_DAYS = 2  # a run in progress at the last fetch completes later
# 2 since 0.2.23: entries carry the actor; an older cache is discarded and refetched once,
# so its zero-job token runs (D12) do not sit in the baseline for a whole window
CACHE_SCHEMA_VERSION = 2
MAX_FAILED_LINKS = 10  # failed run ids/urls kept per day, newest first
COUNTED_CONCLUSIONS = ("success", "failure")
FAILED_CONCLUSION = "failure"
COUNTED_EVENTS = ("push", "pull_request", "schedule", "workflow_dispatch")
FRAMEWORK_WORKFLOW_PREFIX = "SDLC "
CACHED_FIELDS = ("created_at", "conclusion", "status", "event", "name", "html_url", "actor")
# The framework's default automation identity (the same value as gate/policy.py
# DEFAULT_AUTOMATION_IDENTITY, named here rather than imported to keep this module free of gate
# imports); the caller passes the project's sdlc.yaml automation_identity list instead.
DEFAULT_EXCLUDED_ACTORS: tuple[str, ...] = ("github-actions[bot]",)
ERROR_BODY_CHARS = 200


class SourceError(RuntimeError):
    """The metric source cannot be read (bad source value, bad input, API error)."""


@dataclass
class FetchResult:
    observations: list[Observation] = field(default_factory=list)
    runs_total: int = 0  # counted runs in the window
    fetched: int = 0  # runs the API returned this call
    cache_path: str | None = None
    cache_note: str = "no cache"  # "written" | "not written: <reason>" | "no cache"
    since: str = ""


# --- source value -----------------------------------------------------------------------------
def parse_source(source: str) -> tuple[str, str | None]:
    """``github-actions`` -> (kind, None); ``github-actions:<workflow>`` -> (kind, workflow)."""
    text = (source or "").strip()
    kind, sep, workflow = text.partition(":")
    kind = kind.strip()
    if kind != SOURCE_KIND:
        raise SourceError(
            f"unknown metric source {source!r}: expected {SOURCE_KIND!r} or "
            f"'{SOURCE_KIND}:<workflow name>'"
        )
    if not sep:
        return kind, None
    workflow = workflow.strip()
    if not workflow:
        raise SourceError(f"metric source {source!r} names no workflow after ':'")
    return kind, workflow


# --- counting ---------------------------------------------------------------------------------
def _actor_login(value: Any) -> str | None:
    """The actor's login: ``value["login"]`` for the API shape (a dict), the value itself for
    an already-flattened cached string, else None."""
    if isinstance(value, dict):
        login = value.get("login")
        return login if isinstance(login, str) else None
    return value if isinstance(value, str) else None


def _normalized_actors(excluded_actors: Iterable[str] | None) -> frozenset[str]:
    actors = DEFAULT_EXCLUDED_ACTORS if excluded_actors is None else excluded_actors
    if isinstance(actors, str):  # one login passed on its own, not a list of characters
        actors = (actors,)
    return frozenset(str(a).strip().casefold() for a in actors if str(a).strip())


def counts(
    run: dict[str, Any],
    workflow: str | None,
    excluded_actors: Iterable[str] | None = None,
) -> bool:
    """Whether a run enters the failure rate (see the module docstring). ``excluded_actors``
    defaults to ``DEFAULT_EXCLUDED_ACTORS``; pass ``()`` to exclude no actor. A run with no
    actor (a cache written before the actor was kept) counts."""
    if run.get("status") != "completed":
        return False
    if run.get("conclusion") not in COUNTED_CONCLUSIONS:
        return False
    if run.get("event") not in COUNTED_EVENTS:
        return False
    name = str(run.get("name") or "")
    if name.startswith(FRAMEWORK_WORKFLOW_PREFIX):
        return False
    if workflow is not None and name.casefold() != workflow.casefold():
        return False
    login = _actor_login(run.get("actor"))
    if login is not None and login.strip().casefold() in _normalized_actors(excluded_actors):
        return False
    return True


def _day(run: dict[str, Any]) -> str:
    return str(run.get("created_at") or "")[:10]


def daily_series(
    runs: Iterable[dict[str, Any]],
    workflow: str | None,
    since: str,
    excluded_actors: Iterable[str] | None = None,
) -> list[Observation]:
    """One observation per UTC day on or after ``since`` with at least one counted run,
    sorted by day."""
    excluded = _normalized_actors(excluded_actors)
    by_day: dict[str, list[dict[str, Any]]] = {}
    for run in runs:
        day = _day(run)
        if len(day) < 10 or day < since or not counts(run, workflow, excluded):
            continue
        by_day.setdefault(day, []).append(run)
    series: list[Observation] = []
    for day in sorted(by_day):
        day_runs = by_day[day]
        failed = [r for r in day_runs if r.get("conclusion") == FAILED_CONCLUSION]
        failed.sort(key=lambda r: (str(r.get("created_at") or ""), _id_key(r.get("id"))))
        newest = list(reversed(failed))[:MAX_FAILED_LINKS]
        series.append(
            {
                "at": day,
                "value": len(failed) / len(day_runs),
                "meta": {
                    "runs": len(day_runs),
                    "failed": len(failed),
                    "failed_run_ids": [r.get("id") for r in newest],
                    "failed_run_urls": [r.get("html_url") for r in newest],
                },
            }
        )
    return series


def _id_key(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


# --- HTTP -------------------------------------------------------------------------------------
def _http_get(url: str, tok: str | None) -> tuple[int, str, dict[str, str]]:
    """(status, body, headers). The only place a token touches the network; without a token
    the request goes out unauthenticated (enough for a public repository)."""
    request = urllib.request.Request(url, method="GET")
    if tok:
        request.add_header("Authorization", f"Bearer {tok}")
    request.add_header("Accept", "application/vnd.github+json")
    request.add_header("X-GitHub-Api-Version", github.API_VERSION)
    request.add_header("User-Agent", "sdlc-framework")
    try:
        with urllib.request.urlopen(request, timeout=github.TIMEOUT) as response:
            return (
                response.status,
                response.read().decode("utf-8", errors="replace"),
                dict(response.headers.items()),
            )
    except urllib.error.HTTPError as exc:  # 4xx/5xx carry a body worth reading
        raw = exc.read().decode("utf-8", errors="replace")
        headers = dict(exc.headers.items()) if exc.headers else {}
        return exc.code, raw, headers
    except (urllib.error.URLError, OSError, ValueError) as exc:
        raise SourceError(f"GitHub unreachable on {url}: {type(exc).__name__}: {exc}") from exc


def _api_get_pages(url: str, tok: str | None) -> list[dict[str, Any]]:
    """Every workflow run of a paged runs listing, following ``Link: rel="next"`` for at most
    ``MAX_PAGES`` pages (newest first, so a cut drops only the oldest runs)."""
    runs: list[dict[str, Any]] = []
    for _page in range(MAX_PAGES):
        status, raw, headers = _http_get(url, tok)
        if status != 200:
            raise SourceError(f"GitHub {status} on {url}: {raw[:ERROR_BODY_CHARS]}")
        try:
            data = json.loads(raw) if raw.strip() else {}
        except ValueError as exc:
            raise SourceError(
                f"GitHub {status} on {url}: not JSON: {raw[:ERROR_BODY_CHARS]}"
            ) from exc
        items = data.get("workflow_runs") if isinstance(data, dict) else None
        if not isinstance(items, list):
            raise SourceError(f"GitHub {status} on {url}: no workflow_runs in the response")
        runs += [item for item in items if isinstance(item, dict)]
        next_url = github.next_page_url({"headers": headers})
        if not next_url:
            break
        url = next_url
    return runs


def runs_url(repo: str, since: str) -> str:
    return (
        f"{github.API_ROOT}/repos/{repo}/actions/runs"
        f"?per_page={github.PER_PAGE}&created=>={since}&status=completed"
    )


# --- cache ------------------------------------------------------------------------------------
def _load_cache(cache: Path | None, repo: str) -> dict[str, dict[str, Any]]:
    """The cached runs by id; a missing, unreadable, foreign-repo or other-schema cache is
    empty."""
    if cache is None:
        return {}
    try:
        data = json.loads(Path(cache).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    if not isinstance(data, dict) or data.get("schema_version") != CACHE_SCHEMA_VERSION:
        return {}
    if str(data.get("repo") or "").casefold() != repo.casefold():
        return {}
    runs = data.get("runs")
    if not isinstance(runs, dict):
        return {}
    return {str(k): v for k, v in runs.items() if isinstance(v, dict) and v.get("created_at")}


def _write_cache(cache: Path, repo: str, runs: dict[str, dict[str, Any]]) -> str:
    """Write the cache atomically; return the note for ``FetchResult.cache_note``."""
    payload = {
        "schema_version": CACHE_SCHEMA_VERSION,
        "repo": repo,
        "runs": runs,
        "fetched_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    tmp_name = ""
    try:
        cache.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp_name = tempfile.mkstemp(prefix=".source-cache-", dir=str(cache.parent))
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(payload, handle, indent=1, sort_keys=True)
            handle.write("\n")
        os.replace(tmp_name, cache)
        tmp_name = ""
    except OSError as exc:
        return f"not written: {type(exc).__name__}: {exc}"
    finally:
        if tmp_name:
            try:
                os.unlink(tmp_name)
            except OSError:
                pass
    return "written"


def _record(run: dict[str, Any]) -> dict[str, Any]:
    """The cached fields of a run, with ``actor`` flattened to its login (a string or None).
    A cache written before ``actor`` was kept has no such key and its runs count as before;
    the cache only refetches the last ``REFETCH_DAYS``, so those entries age out of the window
    on their own."""
    record = {key: run.get(key) for key in CACHED_FIELDS}
    record["actor"] = _actor_login(run.get("actor"))
    return record


# --- fetch ------------------------------------------------------------------------------------
def _parse_day(value: str, what: str) -> date:
    try:
        return date.fromisoformat(str(value)[:10])
    except ValueError as exc:
        raise SourceError(f"{what} {value!r} is not an ISO date (YYYY-MM-DD)") from exc


def fetch(
    repo: str,
    *,
    since: str,
    cache: Path | None = None,
    workflow: str | None = None,
    get_pages: GetPages | None = None,
    token: str | None = None,
    excluded_actors: Iterable[str] | None = None,
) -> FetchResult:
    """The daily failure-rate series of ``repo`` (``owner/name``) from ``since`` (ISO date).

    With a warm cache only runs created since the newest cached run minus ``REFETCH_DAYS``
    are requested (never earlier than ``since``); fresh runs replace cached ones by id, runs
    older than ``since`` - 1 day are dropped, and the cache is written back. A cache that
    cannot be written is reported in ``cache_note``, never raised. ``token`` defaults to
    ``GITHUB_TOKEN``/``GH_TOKEN``; with none the request is unauthenticated.
    ``excluded_actors`` (default ``DEFAULT_EXCLUDED_ACTORS``) is passed to ``counts``.
    """
    owner, sep, name = (repo or "").partition("/")
    if not (owner and sep and name) or "/" in name:
        raise SourceError(f"repository {repo!r} is not 'owner/name'")
    window_start = _parse_day(since, "since")
    since_iso = window_start.isoformat()
    keep_from = (window_start - timedelta(days=1)).isoformat()

    cached = _load_cache(cache, repo)
    if cached:
        newest = max(_parse_day(r["created_at"], "cached created_at") for r in cached.values())
        request_since = max(newest - timedelta(days=REFETCH_DAYS), window_start)
    else:
        request_since = window_start

    if get_pages is None:
        tok = token if token is not None else github.token()

        def _from_api(url: str) -> list[dict[str, Any]]:
            return _api_get_pages(url, tok)

        get_pages = _from_api
    fresh = get_pages(runs_url(repo, request_since.isoformat()))

    merged = dict(cached)
    for run in fresh:
        if run.get("id") is None:
            continue
        merged[str(run["id"])] = _record(run)
    merged = {k: v for k, v in merged.items() if _day(v) >= keep_from}

    cache_note = "no cache"
    if cache is not None:
        cache_note = _write_cache(Path(cache), repo, merged)

    runs = [{"id": _id_key(k), **v} for k, v in merged.items()]
    observations = daily_series(runs, workflow, since_iso, excluded_actors)
    return FetchResult(
        observations=observations,
        runs_total=sum(o["meta"]["runs"] for o in observations),
        fetched=len(fresh),
        cache_path=str(cache) if cache is not None else None,
        cache_note=cache_note,
        since=since_iso,
    )
