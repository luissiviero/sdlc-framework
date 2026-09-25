"""Layer-1 tests for plugin/detect/source.py: the CI test failure rate per UTC day read from
the GitHub Actions runs API (build guide step 37, decision 15, p.43). The HTTP layer is
always a fake (a ``get_pages`` callable, or ``_http_get``/``urlopen`` monkeypatched), so
nothing leaves the process."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from detect import source


def run(
    run_id: int,
    created_at: str,
    conclusion: str | None = "success",
    *,
    event: str = "push",
    name: str = "CI",
    status: str = "completed",
) -> dict[str, Any]:
    return {
        "id": run_id,
        "created_at": created_at,
        "conclusion": conclusion,
        "status": status,
        "event": event,
        "name": name,
        "html_url": f"https://github.com/o/r/actions/runs/{run_id}",
        "head_sha": "abc",  # an API field the cache does not keep
    }


class FakePages:
    """A ``get_pages`` stand-in: records every URL and returns a fixed list of runs."""

    def __init__(self, runs: list[dict[str, Any]]):
        self.runs = runs
        self.urls: list[str] = []

    def __call__(self, url: str) -> list[dict[str, Any]]:
        self.urls.append(url)
        return list(self.runs)


def write_cache(path: Path, repo: str, runs: dict[str, dict[str, Any]], version: int = 1):
    path.write_text(
        json.dumps({"schema_version": version, "repo": repo, "runs": runs, "fetched_at": "x"}),
        encoding="utf-8",
    )


def cached(created_at: str, conclusion: str = "success", **extra: Any) -> dict[str, Any]:
    record = {k: v for k, v in run(0, created_at, conclusion, **extra).items() if k != "id"}
    return {k: record[k] for k in source.CACHED_FIELDS}


# --- parse_source -----------------------------------------------------------------------------
def test_parse_source_accepts_the_bare_kind_and_a_named_workflow():
    assert source.parse_source("github-actions") == ("github-actions", None)
    assert source.parse_source("github-actions:CI") == ("github-actions", "CI")
    assert source.parse_source(" github-actions:Unit tests ") == ("github-actions", "Unit tests")


@pytest.mark.parametrize("bad", ["prometheus", "", "github-actions:", "gitlab-ci:CI", "GitHub"])
def test_parse_source_rejects_anything_else(bad):
    with pytest.raises(source.SourceError):
        source.parse_source(bad)


# --- counts -----------------------------------------------------------------------------------
@pytest.mark.parametrize(
    ("conclusion", "expected"),
    [
        ("success", True),
        ("failure", True),
        ("cancelled", False),
        ("skipped", False),
        ("timed_out", False),
        ("action_required", False),
        ("neutral", False),
        ("stale", False),
        (None, False),
    ],
)
def test_counts_by_conclusion(conclusion, expected):
    assert source.counts(run(1, "2026-09-01T10:00:00Z", conclusion), None) is expected


@pytest.mark.parametrize(
    ("event", "expected"),
    [
        ("push", True),
        ("pull_request", True),
        ("schedule", True),
        ("workflow_dispatch", True),
        ("repository_dispatch", False),
        ("pull_request_target", False),
        ("release", False),
    ],
)
def test_counts_by_event(event, expected):
    assert source.counts(run(1, "2026-09-01T10:00:00Z", event=event), None) is expected


def test_counts_ignores_runs_not_completed():
    assert not source.counts(run(1, "2026-09-01T10:00:00Z", status="in_progress"), None)


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("SDLC phase transition", False),
        ("SDLC daily digest", False),
        ("SDLCish", True),
        ("CI", True),
    ],
)
def test_counts_skips_the_framework_workflows(name, expected):
    assert source.counts(run(1, "2026-09-01T10:00:00Z", name=name), None) is expected


def test_counts_workflow_filter_is_case_insensitive_and_exact():
    r = run(1, "2026-09-01T10:00:00Z", name="Unit Tests")
    assert source.counts(r, "unit tests")
    assert source.counts(r, "UNIT TESTS")
    assert not source.counts(r, "unit")
    assert not source.counts(run(2, "2026-09-01T10:00:00Z", name="Lint"), "unit tests")


def test_counts_workflow_filter_never_admits_a_framework_workflow():
    assert not source.counts(run(1, "2026-09-01T10:00:00Z", name="SDLC build"), "SDLC build")


# --- daily_series -----------------------------------------------------------------------------
FIXTURE_RUNS = [
    # before the window: dropped
    run(1, "2026-08-31T23:59:59Z", "failure"),
    # day 1: 1 of 4 counted runs failed (cancelled, SDLC and release event ignored)
    run(10, "2026-09-01T08:00:00Z", "success"),
    run(11, "2026-09-01T09:00:00Z", "failure"),
    run(12, "2026-09-01T10:00:00Z", "success", event="pull_request"),
    run(13, "2026-09-01T11:00:00Z", "success", event="schedule"),
    run(14, "2026-09-01T12:00:00Z", "cancelled"),
    run(15, "2026-09-01T13:00:00Z", "failure", name="SDLC phase transition"),
    run(16, "2026-09-01T14:00:00Z", "failure", event="release"),
    # day 2 (2026-09-02): no counted run at all -> absent
    run(20, "2026-09-02T10:00:00Z", "skipped"),
    # day 3: 12 failed of 13, newest-first links capped at 10
    *[run(300 + i, f"2026-09-03T{i:02d}:00:00Z", "failure") for i in range(12)],
    run(399, "2026-09-03T23:00:00Z", "success"),
]


def test_daily_series_rates_meta_and_order():
    series = source.daily_series(reversed(FIXTURE_RUNS), None, "2026-09-01")
    assert [o["at"] for o in series] == ["2026-09-01", "2026-09-03"]

    day1 = series[0]
    assert day1["value"] == pytest.approx(0.25)
    assert day1["meta"] == {
        "runs": 4,
        "failed": 1,
        "failed_run_ids": [11],
        "failed_run_urls": ["https://github.com/o/r/actions/runs/11"],
    }

    day3 = series[1]
    assert day3["meta"]["runs"] == 13
    assert day3["meta"]["failed"] == 12
    assert day3["value"] == pytest.approx(12 / 13)
    assert day3["meta"]["failed_run_ids"] == [311 - i for i in range(10)]
    assert len(day3["meta"]["failed_run_urls"]) == source.MAX_FAILED_LINKS
    assert day3["meta"]["failed_run_urls"][0] == "https://github.com/o/r/actions/runs/311"


def test_daily_series_drops_runs_before_since():
    series = source.daily_series(FIXTURE_RUNS, None, "2026-09-02")
    assert [o["at"] for o in series] == ["2026-09-03"]
    earlier = source.daily_series(FIXTURE_RUNS, None, "2026-08-31")
    assert earlier[0] == {
        "at": "2026-08-31",
        "value": 1.0,
        "meta": {
            "runs": 1,
            "failed": 1,
            "failed_run_ids": [1],
            "failed_run_urls": ["https://github.com/o/r/actions/runs/1"],
        },
    }


def test_daily_series_with_a_workflow_filter():
    runs = [
        run(1, "2026-09-01T08:00:00Z", "failure", name="CI"),
        run(2, "2026-09-01T09:00:00Z", "success", name="Lint"),
        run(3, "2026-09-01T10:00:00Z", "success", name="ci"),
    ]
    series = source.daily_series(runs, "CI", "2026-09-01")
    assert series[0]["meta"]["runs"] == 2
    assert series[0]["value"] == pytest.approx(0.5)


def test_daily_series_all_green_day_has_rate_zero():
    series = source.daily_series([run(1, "2026-09-01T08:00:00Z")], None, "2026-09-01")
    assert series[0]["value"] == 0.0
    assert series[0]["meta"]["failed_run_ids"] == []


# --- fetch ------------------------------------------------------------------------------------
REPO = "owner/name"


def test_fetch_with_an_empty_cache_requests_from_the_window_start(tmp_path):
    cache = tmp_path / "nested" / "dir" / "runs.json"
    fake = FakePages(
        [
            run(1, "2026-09-10T08:00:00Z", "failure"),
            run(2, "2026-09-10T09:00:00Z", "success"),
            run(3, "2026-09-11T09:00:00Z", "success"),
        ]
    )
    result = source.fetch(REPO, since="2026-09-10", cache=cache, get_pages=fake)

    assert len(fake.urls) == 1
    url = fake.urls[0]
    assert url.startswith(f"{source.github.API_ROOT}/repos/owner/name/actions/runs?")
    assert "created=>=2026-09-10" in url
    assert "per_page=100" in url
    assert "status=completed" in url

    assert [o["at"] for o in result.observations] == ["2026-09-10", "2026-09-11"]
    assert result.observations[0]["value"] == pytest.approx(0.5)
    assert result.runs_total == 3
    assert result.fetched == 3
    assert result.since == "2026-09-10"
    assert result.cache_note == "written"
    assert result.cache_path == str(cache)

    data = json.loads(cache.read_text(encoding="utf-8"))
    assert data["schema_version"] == 1
    assert data["repo"] == REPO
    assert set(data["runs"]) == {"1", "2", "3"}
    assert set(data["runs"]["1"]) == set(source.CACHED_FIELDS)  # head_sha not kept
    assert data["fetched_at"].endswith("Z")


def test_fetch_with_a_warm_cache_refetches_the_last_days_merges_and_drops_old(tmp_path):
    cache = tmp_path / "runs.json"
    write_cache(
        cache,
        REPO,
        {
            "5": cached("2026-09-01T10:00:00Z"),  # older than since - 1 day: dropped
            "6": cached("2026-09-09T10:00:00Z", "failure"),  # since - 1 day: kept, not counted
            "7": cached("2026-09-12T10:00:00Z"),
            "8": cached("2026-09-20T10:00:00Z", "success", status="in_progress"),
        },
    )
    in_progress_then = run(8, "2026-09-20T10:00:00Z", "failure")  # completed since: fresh wins
    fake = FakePages([in_progress_then, run(9, "2026-09-21T07:00:00Z", "success")])

    result = source.fetch(REPO, since="2026-09-10", cache=cache, get_pages=fake)

    assert "created=>=2026-09-18" in fake.urls[0]  # newest cached day minus REFETCH_DAYS
    assert result.fetched == 2
    assert [o["at"] for o in result.observations] == ["2026-09-12", "2026-09-20", "2026-09-21"]
    assert result.observations[1]["value"] == 1.0
    assert result.observations[1]["meta"]["failed_run_ids"] == [8]
    assert result.runs_total == 3
    assert result.cache_note == "written"

    data = json.loads(cache.read_text(encoding="utf-8"))
    assert set(data["runs"]) == {"6", "7", "8", "9"}
    assert data["runs"]["8"]["conclusion"] == "failure"
    assert data["runs"]["8"]["status"] == "completed"

    # re-read: the next fetch starts from the new newest run and sees the same series
    again = FakePages([])
    second = source.fetch(REPO, since="2026-09-10", cache=cache, get_pages=again)
    assert "created=>=2026-09-19" in again.urls[0]
    assert second.observations == result.observations
    assert second.fetched == 0


def test_fetch_never_requests_before_the_window_start_from_a_stale_cache(tmp_path):
    cache = tmp_path / "runs.json"
    write_cache(cache, REPO, {"1": cached("2026-01-05T10:00:00Z")})
    fake = FakePages([])
    result = source.fetch(REPO, since="2026-09-10", cache=cache, get_pages=fake)
    assert "created=>=2026-09-10" in fake.urls[0]
    assert result.observations == []
    assert json.loads(cache.read_text(encoding="utf-8"))["runs"] == {}


def test_fetch_ignores_a_foreign_repo_cache(tmp_path):
    cache = tmp_path / "runs.json"
    write_cache(cache, "someone/else", {"7": cached("2026-09-12T10:00:00Z", "failure")})
    fake = FakePages([run(1, "2026-09-11T08:00:00Z")])
    result = source.fetch(REPO, since="2026-09-10", cache=cache, get_pages=fake)
    assert "created=>=2026-09-10" in fake.urls[0]
    assert [o["at"] for o in result.observations] == ["2026-09-11"]
    data = json.loads(cache.read_text(encoding="utf-8"))
    assert data["repo"] == REPO
    assert set(data["runs"]) == {"1"}


@pytest.mark.parametrize(
    "content", ["not json", "[]", '{"schema_version": 2, "repo": "owner/name"}']
)
def test_fetch_treats_an_unreadable_cache_as_empty(tmp_path, content):
    cache = tmp_path / "runs.json"
    cache.write_text(content, encoding="utf-8")
    fake = FakePages([])
    source.fetch(REPO, since="2026-09-10", cache=cache, get_pages=fake)
    assert "created=>=2026-09-10" in fake.urls[0]


def test_fetch_reports_an_unwritable_cache_and_still_returns(tmp_path):
    cache = tmp_path / "runs.json"
    cache.mkdir()  # a directory where the file should be
    fake = FakePages([run(1, "2026-09-11T08:00:00Z", "failure")])
    result = source.fetch(REPO, since="2026-09-10", cache=cache, get_pages=fake)
    assert result.cache_note.startswith("not written: ")
    assert len(result.cache_note) > len("not written: ")
    assert result.observations[0]["value"] == 1.0
    assert cache.is_dir()
    assert [p.name for p in tmp_path.iterdir()] == ["runs.json"]  # no temp file left behind


def test_fetch_without_a_cache(tmp_path):
    result = source.fetch(REPO, since="2026-09-10", get_pages=FakePages([]))
    assert result.cache_note == "no cache"
    assert result.cache_path is None
    assert result.observations == []
    assert result.runs_total == 0


@pytest.mark.parametrize("repo", ["owner", "owner/", "/name", "a/b/c", ""])
def test_fetch_rejects_a_bad_repo(repo):
    with pytest.raises(source.SourceError):
        source.fetch(repo, since="2026-09-10", get_pages=FakePages([]))


def test_fetch_rejects_a_bad_since():
    with pytest.raises(source.SourceError):
        source.fetch(REPO, since="10/09/2026", get_pages=FakePages([]))


def test_fetch_passes_the_workflow_filter(tmp_path):
    fake = FakePages(
        [run(1, "2026-09-11T08:00:00Z", "failure", name="Lint"), run(2, "2026-09-11T09:00:00Z")]
    )
    result = source.fetch(REPO, since="2026-09-10", workflow="ci", get_pages=fake)
    assert result.runs_total == 1
    assert result.observations[0]["value"] == 0.0


# --- the default HTTP pager -------------------------------------------------------------------
def page(runs: list[dict[str, Any]], next_url: str | None = None):
    headers = {"Link": f'<{next_url}>; rel="next"'} if next_url else {}
    return 200, json.dumps({"total_count": 99, "workflow_runs": runs}), headers


def test_default_pager_follows_link_headers_and_uses_the_token(monkeypatch):
    pages = {
        "first": page([run(1, "2026-09-11T08:00:00Z")], "https://api.github.com/p2"),
        "https://api.github.com/p2": page([run(2, "2026-09-11T09:00:00Z", "failure")]),
    }
    calls: list[tuple[str, str | None]] = []

    def fake_get(url, tok):
        calls.append((url, tok))
        return pages["first" if "actions/runs" in url else url]

    monkeypatch.setattr(source, "_http_get", fake_get)
    result = source.fetch(REPO, since="2026-09-10", token="t0k")
    assert [tok for _, tok in calls] == ["t0k", "t0k"]
    assert calls[1][0] == "https://api.github.com/p2"
    assert result.fetched == 2
    assert result.observations[0]["value"] == pytest.approx(0.5)


def test_default_pager_stops_after_max_pages(monkeypatch):
    calls: list[str] = []

    def endless(url, tok):
        calls.append(url)
        return page(
            [run(len(calls), "2026-09-11T08:00:00Z")], f"https://api.github.com/p{len(calls)}"
        )

    monkeypatch.setattr(source, "_http_get", endless)
    result = source.fetch(REPO, since="2026-09-10", token="t")
    assert len(calls) == source.MAX_PAGES
    assert result.fetched == source.MAX_PAGES


def test_default_pager_turns_a_non_200_into_a_readable_source_error(monkeypatch):
    body = json.dumps({"message": "Not Found", "documentation_url": "x" * 400})
    monkeypatch.setattr(source, "_http_get", lambda url, tok: (404, body, {}))
    with pytest.raises(source.SourceError) as info:
        source.fetch(REPO, since="2026-09-10", token="secret-token")
    message = str(info.value)
    assert message.startswith("GitHub 404 on https://api.github.com/repos/owner/name/")
    assert message.endswith(body[:200])
    assert "secret-token" not in message


def test_default_pager_rejects_a_response_without_runs(monkeypatch):
    monkeypatch.setattr(source, "_http_get", lambda url, tok: (200, "[]", {}))
    with pytest.raises(source.SourceError):
        source.fetch(REPO, since="2026-09-10", token="t")


def test_default_pager_falls_back_to_the_environment_token(monkeypatch):
    seen: list[str | None] = []
    monkeypatch.setattr(source.github, "token", lambda: "env-token")
    monkeypatch.setattr(source, "_http_get", lambda url, tok: seen.append(tok) or page([]))
    source.fetch(REPO, since="2026-09-10")
    assert seen == ["env-token"]


class FakeResponse:
    status = 200
    headers = {"Content-Type": "application/json"}

    def __init__(self, body: str):
        self.body = body

    def read(self):
        return self.body.encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


@pytest.mark.parametrize("tok", [None, ""])
def test_http_get_without_a_token_sends_no_authorization(monkeypatch, tok):
    sent = []

    def fake_urlopen(request, timeout):
        sent.append((request, timeout))
        return FakeResponse('{"workflow_runs": []}')

    monkeypatch.setattr(source.urllib.request, "urlopen", fake_urlopen)
    status, body, _headers = source._http_get("https://api.github.com/x", tok)
    assert status == 200 and "workflow_runs" in body
    request, timeout = sent[0]
    assert request.get_header("Authorization") is None
    assert request.get_header("X-github-api-version") == source.github.API_VERSION
    assert timeout == source.github.TIMEOUT


def test_http_get_with_a_token_sends_a_bearer_header(monkeypatch):
    sent = []
    monkeypatch.setattr(
        source.urllib.request,
        "urlopen",
        lambda request, timeout: sent.append(request) or FakeResponse("{}"),
    )
    source._http_get("https://api.github.com/x", "abc")
    assert sent[0].get_header("Authorization") == "Bearer abc"


def test_http_get_network_failure_is_a_source_error(monkeypatch):
    def refuse(request, timeout):
        raise source.urllib.error.URLError("connection refused")

    monkeypatch.setattr(source.urllib.request, "urlopen", refuse)
    with pytest.raises(source.SourceError, match="unreachable"):
        source._http_get("https://api.github.com/x", None)
