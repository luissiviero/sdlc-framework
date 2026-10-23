"""The digest's "Failed runs" line (ROADMAP R18; ``docs/proposals/failed-run-explains-itself.md``,
point 4).

One line per red run of a framework workflow (``.github/workflows/sdlc-*.yml``) in the last
seven days, oldest first, that did not park: a run that parked is in the queue already, and
the triage step writes no record for it. Two sources, no model call:

- the Actions API (``GET /repos/{repo}/actions/runs``, the digest's ``actions: read``) says
  which runs failed, were cancelled or timed out; its run object is the latest attempt, so a
  run whose re-run succeeded drops out. It is the only source for a lost runner, a cancelled
  job, a failed checkout and a failed digest, which show as the bare line;
- the failed-run records on ``refs/sdlc/failed-runs/<run>-<attempt>`` (``ci/triage.py``) add
  the runner's reason and the triage lines, labelled model-written. A record is data: the
  phase session holds ``Bash(git *)`` and could push such a ref, so a record shows only for
  a run the API lists as red, on one line, cut to ``TEXT_MAX`` characters, with its
  mentions and links made inert (the issue body would otherwise notify, against decision 31).

Where the line sits in the digest is R20's to place; until then it follows the queue.
"""

from __future__ import annotations

import base64
import json
import urllib.parse
from collections.abc import Callable
from datetime import datetime, timedelta
from typing import Any

if __package__ in (None, ""):
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pr.github import next_page_url  # noqa: E402

WINDOW_DAYS = 7
FAILED_CONCLUSIONS = ("failure", "cancelled", "timed_out")
WORKFLOW_PREFIX = ".github/workflows/sdlc-"
REF_PREFIX = "sdlc/failed-runs/"  # under refs/, as ``ci/triage.py FAILED_RUN_PREFIX``
RECORD_FILE = "failed-run.json"
MAX_RECORDS = 50  # records read per digest; older ones show as bare lines
MAX_PAGES = 5  # pages of 100 runs: a busy repository's week, the project's own CI included
TEXT_MAX = 400
HEADING = "## Failed runs — the last {days} days, no park"
UNREADABLE = "The failed runs could not be read: {reason}."
NO_RECORD = "{conclusion}; no triage record (the job ended before its triage step, or no step ran)"
TRIAGE_LABEL = "triage (model-written)"

Get = Callable[[str], dict[str, Any]]


def _one_line(value: Any) -> str:
    text = " ".join(str(value or "").split())
    return text if len(text) <= TEXT_MAX else text[: TEXT_MAX - 1] + "…"


def _inert(value: Any) -> str:
    """A record's text on one line, with ``@`` mentions and markdown links or HTML made
    inert: a record is data a session could have written."""
    text = _one_line(value).replace("@", "@\u200b").replace("](", "] (")
    return text.replace("<", "&lt;")


def _red_runs(api_root: str, repo: str, since: str, get: Get) -> tuple[list[Any], str]:
    query = urllib.parse.urlencode({"created": f">={since}", "per_page": 100})
    url: str | None = f"{api_root}/repos/{repo}/actions/runs?{query}"
    runs: list[Any] = []
    for _page in range(MAX_PAGES):
        if not url:
            break
        listed = get(url)
        if listed.get("error"):
            return runs, str(listed["error"])
        data = listed.get("data") if isinstance(listed.get("data"), dict) else {}
        runs += data.get("workflow_runs") or []
        url = next_page_url(listed)
    return runs, ""


def _record(api_root: str, repo: str, ref: dict[str, Any], get: Get) -> dict[str, Any] | None:
    sha = str((ref.get("object") or {}).get("sha") or "")
    if not sha:
        return None
    url = f"{api_root}/repos/{repo}/contents/{RECORD_FILE}?ref={urllib.parse.quote(sha)}"
    result = get(url)
    data = result.get("data") if not result.get("error") else None
    if not isinstance(data, dict):
        return None
    try:
        record = json.loads(base64.b64decode(str(data.get("content") or "")).decode("utf-8"))
    except (ValueError, UnicodeDecodeError):
        return None
    return record if isinstance(record, dict) else None


def collect(repo: str, now: datetime, get: Get, api_root: str) -> dict[str, Any]:
    """{'ok', 'runs', 'reason'}: the red runs of the window, oldest first, each with its
    record when one names it. ``get(url)`` is ``github._request("GET", url, token)``."""
    since = (now - timedelta(days=WINDOW_DAYS)).date().isoformat()
    listed, error = _red_runs(api_root, repo, since, get)
    if error:
        return {"ok": False, "runs": [], "reason": error}
    red = [
        run
        for run in listed
        if isinstance(run, dict)
        and str(run.get("path") or "").startswith(WORKFLOW_PREFIX)
        and run.get("conclusion") in FAILED_CONCLUSIONS
    ]
    records: dict[str, dict[str, Any]] = {}
    refs = get(f"{api_root}/repos/{repo}/git/matching-refs/{REF_PREFIX}")
    ref_list = refs.get("data") if not refs.get("error") else []
    ref_list = ref_list if isinstance(ref_list, list) else []
    red_ids = {str(run.get("id")) for run in red}
    wanted = [
        ref
        for ref in ref_list
        if isinstance(ref, dict)
        and str(ref.get("ref") or "").rpartition("/")[2].rpartition("-")[0] in red_ids
    ]
    for ref in sorted(wanted, key=lambda r: str(r.get("ref")))[-MAX_RECORDS:]:
        record = _record(api_root, repo, ref, get)
        name = str(ref.get("ref")).rpartition("/")[2]
        if record is not None and not record.get("parked"):
            records[name] = record
    runs = []
    for run in sorted(red, key=lambda r: str(r.get("created_at") or "")):
        attempt = str(run.get("run_attempt") or 1)
        record = records.get(f"{run.get('id')}-{attempt}")
        runs.append({"run": run, "record": record})
    return {"ok": True, "runs": runs, "reason": ""}


def line(entry: dict[str, Any]) -> str:
    run, record = entry["run"], entry.get("record")
    attempt = run.get("run_attempt") or 1
    name = _one_line(run.get("name") or run.get("path"))
    head = f"[{name}, run {run.get('id')} attempt {attempt}]({run.get('html_url')})"
    parts = [f"- {head} — {str(run.get('created_at') or '')[:16].replace('T', ' ')} UTC"]
    if record is None:
        parts.append(NO_RECORD.format(conclusion=run.get("conclusion")))
        return " — ".join(parts)
    if record.get("change_id"):
        parts.append(f"change {_inert(record['change_id'])}")
    parts.append(_inert(record.get("reason")))
    triage = record.get("triage")
    if isinstance(triage, list) and triage:
        parts.append(f"{TRIAGE_LABEL}: " + _inert("; ".join(str(t) for t in triage)))
    return " — ".join(parts)


def render(collected: dict[str, Any] | None) -> str:
    """The section, or "" when no framework run failed in the window."""
    if collected is None:
        return ""
    if not collected.get("ok"):
        return UNREADABLE.format(reason=_one_line(collected.get("reason")))
    runs = collected.get("runs") or []
    if not runs:
        return ""
    return "\n".join([HEADING.format(days=WINDOW_DAYS), "", *[line(e) for e in runs]])
