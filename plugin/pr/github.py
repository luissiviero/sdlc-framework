"""A thin GitHub client with three routes (the fallback chain ``/sdlc-plan`` step 6 already
uses by hand, made deterministic here):

1. **api** - the REST API over ``urllib`` with ``GITHUB_TOKEN`` or ``GH_TOKEN``. It is tried
   **first** whenever a token exists: it behaves the same on every machine, while ``gh``
   depends on its own login, its version and the directory it runs in (a CI runner has both,
   and the token is the identity the workflow is supposed to act as);
2. **gh** - the ``gh`` CLI when it is on PATH and authenticated: the fallback, and the only
   route on the owner's PC when no token is exported. Every ``gh`` call takes the project
   root as its working directory, because ``gh pr create|edit|view`` resolve the repository
   from the directory they run in;
3. **none** - nothing is contacted: the caller gets the compare URL and prints it with the
   body so the owner opens the PR by hand.

When both routes are available and both fail, the reason names what each one said (the third
live design run, 2026-09-21, could not tell which route had failed).

No third-party dependency (decision 7), a 30 s timeout on every request, and the token is
never printed: it only ever reaches an ``Authorization`` header inside ``_request``, which is
the single HTTP entry point (so tests monkeypatch one function).
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable
from pathlib import Path
from typing import Any

API_ROOT = "https://api.github.com"
GRAPHQL_URL = f"{API_ROOT}/graphql"
API_VERSION = "2022-11-28"
TIMEOUT = 30  # seconds, every request
TOKEN_VARS = ("GITHUB_TOKEN", "GH_TOKEN")
GH_TIMEOUT = 120  # seconds for one gh invocation
NO_ROUTE = "no GITHUB_TOKEN/GH_TOKEN and no gh on PATH"


# --- routes ---------------------------------------------------------------------------------
def gh_path() -> str | None:
    return shutil.which("gh")


def token() -> str | None:
    for var in TOKEN_VARS:
        value = os.environ.get(var)
        if value:
            return value
    return None


def compare_url(repo: str | None, base: str, head: str) -> str | None:
    if not repo:
        return None
    return f"https://github.com/{repo}/compare/{base}...{head}?expand=1"


def _no_route(reason: str, **extra: Any) -> dict[str, Any]:
    out: dict[str, Any] = {"route": "none", "ok": False, "reason": reason}
    out.update(extra)
    return out


def _attempt(
    api_call: Callable[[], dict[str, Any]],
    gh_call: Callable[[], dict[str, Any]] | None = None,
    **extra: Any,
) -> dict[str, Any]:
    """The first route that works: the token route, then ``gh``.

    Both routes return the usual result dict; a failure carries ``reason``. With no route at
    all the caller gets ``route: none`` and ``extra`` (the compare URL, a number), and when
    every available route failed the reason names each one.
    """
    problems: list[str] = []
    for name, call in (
        ("api", api_call if token() else None),
        ("gh", gh_call if gh_path() else None),
    ):
        if call is None:
            continue
        result = call()
        if result.get("ok"):
            return result
        problems.append(f"{name}: {result.get('reason') or 'failed'}")
    if not problems:
        return _no_route(NO_ROUTE, **extra)
    return {"route": "none", "ok": False, "reason": "; ".join(problems), **extra}


# --- the one HTTP entry point -----------------------------------------------------------------
def _request(
    method: str, url: str, tok: str, payload: dict[str, Any] | None = None
) -> dict[str, Any]:
    """{'status', 'data', 'error', 'headers'}. The only place a token touches the network.

    ``headers`` carries the response headers as they arrived; callers that page read
    ``Link`` from it (a monkeypatched ``_request`` may leave it out: treat it as empty).
    """
    body = json.dumps(payload).encode("utf-8") if payload is not None else None
    request = urllib.request.Request(url, data=body, method=method)
    request.add_header("Authorization", f"Bearer {tok}")
    request.add_header("Accept", "application/vnd.github+json")
    request.add_header("X-GitHub-Api-Version", API_VERSION)
    request.add_header("User-Agent", "sdlc-framework")
    if body is not None:
        request.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
            raw = response.read().decode("utf-8")
            status = response.status
            headers = dict(response.headers.items())
    except urllib.error.HTTPError as exc:  # 4xx/5xx carry a body worth reading
        raw = exc.read().decode("utf-8", errors="replace")
        status = exc.code
        headers = dict(exc.headers.items()) if exc.headers else {}
    except (urllib.error.URLError, OSError, ValueError) as exc:
        return {"status": 0, "data": {}, "error": f"{type(exc).__name__}: {exc}", "headers": {}}
    try:
        data = json.loads(raw) if raw.strip() else {}
    except ValueError:
        data = {"raw": raw}
    error = "" if 200 <= status < 300 else str(data.get("message", f"HTTP {status}"))
    return {"status": status, "data": data, "error": error, "headers": headers}


def _gh(*args: str, stdin: str | None = None, cwd: str | Path | None = None) -> dict[str, Any]:
    """Run ``gh`` with an argument list (no shell, so the same call works on Windows).

    ``cwd`` is the project root: ``gh pr create|edit|view`` read the repository from the
    directory they run in, and a run whose process started somewhere else (the runner's
    home, the framework checkout) finds no repository there.
    """
    exe = gh_path()
    if not exe:
        return {"ok": False, "code": 127, "out": "", "err": "gh not found"}
    try:
        proc = subprocess.run(
            [exe, *args],
            capture_output=True,
            text=True,
            encoding="utf-8",
            input=stdin,
            cwd=str(cwd) if cwd else None,
            timeout=GH_TIMEOUT,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return {"ok": False, "code": 1, "out": "", "err": str(exc)}
    return {
        "ok": proc.returncode == 0,
        "code": proc.returncode,
        "out": proc.stdout or "",
        "err": (proc.stderr or "").strip(),
    }


def _gh_error(result: dict[str, Any], what: str) -> str:
    """One line naming what failed and what ``gh`` printed on stderr."""
    err = (result.get("err") or "").strip().replace("\n", " ")
    return (
        f"{what} exited {result.get('code')}: {err}"
        if err
        else f"{what} exited {result.get('code')}"
    )


def _gh_json(*args: str, cwd: str | Path | None = None) -> tuple[Any, str]:
    result = _gh(*args, cwd=cwd)
    if not result["ok"]:
        return None, _gh_error(result, "gh " + " ".join(args[:2]))
    try:
        return json.loads(result["out"] or "null"), ""
    except ValueError as exc:
        return None, f"gh output is not JSON: {exc}"


def _gh_url(result: dict[str, Any]) -> str | None:
    """The URL ``gh`` prints as the last line of a create/edit."""
    out = (result.get("out") or "").strip()
    return out.splitlines()[-1] if out else None


def _number_in(url: str | None) -> int | None:
    tail = url.rsplit("/", 1)[-1] if url else ""
    return int(tail) if tail.isdigit() else None


# --- paging ------------------------------------------------------------------------------------
LINK_NEXT_RE = re.compile(r'<([^>]+)>\s*;\s*rel="next"')
PER_PAGE = 100
MAX_EVENT_PAGES = 10  # 1000 timeline events is far past any real review thread
MAX_FILE_PAGES = 30  # GitHub lists at most 3000 files of a pull request
EVENTS_OVERFLOW = (
    f"label events exceed {PER_PAGE * MAX_EVENT_PAGES}: cannot determine the last actor"
)


def next_page_url(result: dict[str, Any]) -> str | None:
    """The ``rel="next"`` target of a REST ``Link`` header, or None on the last page."""
    headers = result.get("headers") or {}
    link = ""
    for key, value in headers.items():
        if str(key).lower() == "link":
            link = str(value)
            break
    match = LINK_NEXT_RE.search(link)
    return match.group(1) if match else None


def _get_pages(url: str, max_pages: int, overflow: str = "") -> tuple[list[Any], str]:
    """Every item of a paged REST list, following ``Link: rel="next"``: (items, error).

    When a next page still exists after ``max_pages`` pages, ``overflow`` (if given) is
    returned as the error, so a caller that needs the whole list fails closed."""
    items: list[Any] = []
    tok = token() or ""
    for _page in range(max_pages):
        result = _request("GET", url, tok)
        if result.get("error"):
            return items, str(result["error"])
        data = result.get("data")
        items += data if isinstance(data, list) else []
        next_url = next_page_url(result)
        if not next_url:
            return items, ""
        url = next_url
    return items, overflow


# --- pull requests -----------------------------------------------------------------------------
PR_STATES = ("open", "closed", "all")
_EMPTY_PR: dict[str, Any] = {
    "number": None,
    "state": None,
    "merged": False,
    "merge_commit_sha": None,
    "head_ref": None,
    "base_ref": None,
    "labels": [],
    "html_url": None,
    "url": None,
    "draft": False,
}


def _pr_from_api(item: dict[str, Any]) -> dict[str, Any]:
    """One REST pull request (single or listed) in the shape every lookup returns. A listed
    item has no ``merged`` field, only ``merged_at``."""
    merged = item.get("merged")
    if merged is None:
        merged = bool(item.get("merged_at"))
    return {
        "number": item.get("number"),
        "state": item.get("state"),
        "merged": bool(merged),
        "merge_commit_sha": item.get("merge_commit_sha"),
        "head_ref": (item.get("head") or {}).get("ref"),
        "base_ref": (item.get("base") or {}).get("ref"),
        "labels": [lb.get("name") for lb in item.get("labels") or []],
        "html_url": item.get("html_url"),
        "url": item.get("html_url"),
        "draft": bool(item.get("draft")),
        "node_id": item.get("node_id"),
    }


GH_PR_FIELDS = "number,url,labels,isDraft,state,mergeCommit,headRefName,baseRefName"


def _pr_from_gh(item: dict[str, Any]) -> dict[str, Any]:
    """One ``gh pr list|view --json`` item: ``state`` is OPEN, CLOSED or MERGED there."""
    state = str(item.get("state") or "").lower()
    return {
        "number": item.get("number"),
        "state": "closed" if state == "merged" else (state or None),
        "merged": state == "merged",
        "merge_commit_sha": (item.get("mergeCommit") or {}).get("oid"),
        "head_ref": item.get("headRefName"),
        "base_ref": item.get("baseRefName"),
        "labels": [lb.get("name") for lb in item.get("labels") or []],
        "html_url": item.get("url"),
        "url": item.get("url"),
        "draft": bool(item.get("isDraft")),
    }


def _find_pr_api(repo: str, head_branch: str, state: str) -> dict[str, Any]:
    owner = repo.split("/")[0]
    query = urllib.parse.urlencode({"state": state, "head": f"{owner}:{head_branch}"})
    result = _request("GET", f"{API_ROOT}/repos/{repo}/pulls?{query}", token() or "")
    if result["error"]:
        return {"route": "api", "ok": False, "reason": result["error"], "number": None}
    items = result["data"] if isinstance(result["data"], list) else []
    if not items:
        return {"route": "api", "ok": True, "reason": "", **_EMPTY_PR}
    return {"route": "api", "ok": True, "reason": "", **_pr_from_api(items[0])}


def _find_pr_gh(repo: str, head_branch: str, state: str, cwd: str | Path | None) -> dict[str, Any]:
    data, error = _gh_json(
        "pr", "list", "--repo", repo, "--head", head_branch, "--state", state,
        "--json", GH_PR_FIELDS, cwd=cwd,
    )  # fmt: skip
    if error:
        return {"route": "gh", "ok": False, "reason": error, "number": None}
    first = (data or [None])[0] if isinstance(data, list) else None
    if not first:
        return {"route": "gh", "ok": True, "reason": "", **_EMPTY_PR}
    return {"route": "gh", "ok": True, "reason": "", **_pr_from_gh(first)}


def find_pr(
    repo: str, head_branch: str, state: str = "open", cwd: str | Path | None = None
) -> dict[str, Any]:
    """The most recent pull request from ``head_branch`` in ``state`` (open, closed or all):
    {'route', 'ok', 'number', 'state', 'merged', 'merge_commit_sha', 'head_ref', 'base_ref',
    'labels', 'html_url', 'url', 'draft', 'reason'} - number None when there is none."""
    if state not in PR_STATES:
        raise ValueError(f"state must be one of {PR_STATES}, not {state!r}")
    return _attempt(
        lambda: _find_pr_api(repo, head_branch, state),
        lambda: _find_pr_gh(repo, head_branch, state, cwd),
        number=None,
    )


def find_open_pr(repo: str, head_branch: str, cwd: str | Path | None = None) -> dict[str, Any]:
    """{'route', 'number', 'url', 'labels', 'draft'} - number None when there is none."""
    return find_pr(repo, head_branch, "open", cwd=cwd)


def pr_by_number(repo: str, number: int, cwd: str | Path | None = None) -> dict[str, Any]:
    """One pull request by number, in ``find_pr``'s shape; ``ok`` False with a reason when it
    cannot be read (no route, not found)."""

    def via_api() -> dict[str, Any]:
        result = _request("GET", f"{API_ROOT}/repos/{repo}/pulls/{number}", token() or "")
        if result["error"] or not isinstance(result["data"], dict):
            reason = result["error"] or "the answer is not a pull request"
            return {"route": "api", "ok": False, "reason": reason, "number": None}
        return {"route": "api", "ok": True, "reason": "", **_pr_from_api(result["data"])}

    def via_gh() -> dict[str, Any]:
        data, error = _gh_json(
            "pr", "view", str(number), "--repo", repo, "--json", GH_PR_FIELDS, cwd=cwd
        )
        if error or not isinstance(data, dict):
            reason = error or "gh pr view printed no pull request"
            return {"route": "gh", "ok": False, "reason": reason, "number": None}
        return {"route": "gh", "ok": True, "reason": "", **_pr_from_gh(data)}

    return _attempt(via_api, via_gh, **_EMPTY_PR)


def pr_files(repo: str, number: int, cwd: str | Path | None = None) -> dict[str, Any]:
    """The paths a pull request touches: {'ok', 'files', 'route', 'reason'}.

    The REST route follows ``Link: rel="next"`` (100 per page, GitHub's own cap is 3000
    files); ``gh pr view --json files`` is the fallback."""

    def via_api() -> dict[str, Any]:
        url = f"{API_ROOT}/repos/{repo}/pulls/{number}/files?per_page={PER_PAGE}"
        items, error = _get_pages(url, MAX_FILE_PAGES)
        if error:
            return {"route": "api", "ok": False, "reason": error, "files": []}
        files = [str(i.get("filename")) for i in items if isinstance(i, dict) and i.get("filename")]
        return {"route": "api", "ok": True, "reason": "", "files": files}

    def via_gh() -> dict[str, Any]:
        data, error = _gh_json(
            "pr", "view", str(number), "--repo", repo, "--json", "files", cwd=cwd
        )
        if error:
            return {"route": "gh", "ok": False, "reason": error, "files": []}
        listed = data.get("files") if isinstance(data, dict) else None
        files = [str(i.get("path")) for i in listed or [] if isinstance(i, dict) and i.get("path")]
        return {"route": "gh", "ok": True, "reason": "", "files": files}

    return _attempt(via_api, via_gh, files=[])


def _last_label_actor(events: list[Any], label: str) -> str | None:
    """The login of the last ``labeled`` event for ``label``; a missing actor (a deleted
    account) reads ``unknown``."""
    actors = [
        ((event.get("actor") or {}).get("login") or "unknown")
        for event in events
        if isinstance(event, dict)
        and event.get("event") == "labeled"
        and (event.get("label") or {}).get("name") == label
    ]
    return actors[-1] if actors else None


def label_actor(repo: str, number: int, label: str) -> dict[str, Any]:
    """Who applied ``label`` last on issue or pull request ``number``: {'ok', 'actor',
    'reason'}; ``actor`` None when the label was never applied.

    GitHub records one ``labeled`` event per application, with the actor that caused it
    (``GET /repos/{repo}/issues/{number}/events``, oldest first, up to 10 pages). The ``gh``
    route reads the same path with ``gh api``, page by page. More events than that fail
    closed (``ok`` False, ``EVENTS_OVERFLOW``): the last actor would be a guess."""

    path = f"repos/{repo}/issues/{number}/events"

    def via_api() -> dict[str, Any]:
        events, error = _get_pages(
            f"{API_ROOT}/{path}?per_page={PER_PAGE}", MAX_EVENT_PAGES, overflow=EVENTS_OVERFLOW
        )
        if error:
            return {"route": "api", "ok": False, "reason": error, "actor": None}
        return {"route": "api", "ok": True, "reason": "", "actor": _last_label_actor(events, label)}

    def via_gh() -> dict[str, Any]:
        events: list[Any] = []
        for page in range(1, MAX_EVENT_PAGES + 2):
            data, error = _gh_json("api", f"{path}?per_page={PER_PAGE}&page={page}")
            if error:
                return {"route": "gh", "ok": False, "reason": error, "actor": None}
            batch = data if isinstance(data, list) else []
            if page > MAX_EVENT_PAGES:  # one page past the cap, read only to see if it exists
                if batch:
                    return {"route": "gh", "ok": False, "reason": EVENTS_OVERFLOW, "actor": None}
                break
            events += batch
            if len(batch) < PER_PAGE:
                break
        return {"route": "gh", "ok": True, "reason": "", "actor": _last_label_actor(events, label)}

    return _attempt(via_api, via_gh, actor=None)


def _create_pr_api(
    repo: str, base: str, head: str, title: str, body: str, draft: bool
) -> dict[str, Any]:
    payload = {"title": title, "head": head, "base": base, "body": body, "draft": bool(draft)}
    result = _request("POST", f"{API_ROOT}/repos/{repo}/pulls", token() or "", payload)
    if result["error"]:
        return {
            "route": "api",
            "ok": False,
            "reason": result["error"],
            "compare_url": compare_url(repo, base, head),
        }
    data = result["data"]
    return {
        "route": "api",
        "ok": True,
        "number": data.get("number"),
        "url": data.get("html_url"),
        "node_id": data.get("node_id"),
        "created": True,
    }


def _create_pr_gh(
    repo: str, base: str, head: str, title: str, body: str, draft: bool, cwd: str | Path | None
) -> dict[str, Any]:
    args = [
        "pr", "create", "--repo", repo, "--base", base, "--head", head,
        "--title", title, "--body-file", "-",
    ]  # fmt: skip
    if draft:
        args.append("--draft")
    result = _gh(*args, stdin=body, cwd=cwd)
    if not result["ok"]:
        return {
            "route": "gh",
            "ok": False,
            "reason": _gh_error(result, "gh pr create"),
            "compare_url": compare_url(repo, base, head),
        }
    url = _gh_url(result)
    return {"route": "gh", "ok": True, "number": _number_in(url), "url": url, "created": True}


def create_pr(
    repo: str,
    base: str,
    head: str,
    title: str,
    body: str,
    draft: bool = False,
    cwd: str | Path | None = None,
) -> dict[str, Any]:
    return _attempt(
        lambda: _create_pr_api(repo, base, head, title, body, draft),
        lambda: _create_pr_gh(repo, base, head, title, body, draft, cwd),
        compare_url=compare_url(repo, base, head),
    )


def _update_pr_api(repo: str, number: int, body: str, title: str | None) -> dict[str, Any]:
    payload: dict[str, Any] = {"body": body}
    if title:
        payload["title"] = title
    result = _request("PATCH", f"{API_ROOT}/repos/{repo}/pulls/{number}", token() or "", payload)
    if result["error"]:
        return {"route": "api", "ok": False, "reason": result["error"], "number": number}
    return {
        "route": "api",
        "ok": True,
        "number": number,
        "url": result["data"].get("html_url"),
        "node_id": result["data"].get("node_id"),
        "created": False,
    }


def _update_pr_gh(
    repo: str, number: int, body: str, title: str | None, cwd: str | Path | None
) -> dict[str, Any]:
    args = ["pr", "edit", str(number), "--repo", repo, "--body-file", "-"]
    if title:
        args += ["--title", title]
    result = _gh(*args, stdin=body, cwd=cwd)
    if not result["ok"]:
        return {
            "route": "gh",
            "ok": False,
            "reason": _gh_error(result, "gh pr edit"),
            "number": number,
        }
    return {
        "route": "gh",
        "ok": True,
        "number": number,
        "url": _gh_url(result),
        "created": False,
    }


def update_pr(
    repo: str, number: int, body: str, title: str | None = None, cwd: str | Path | None = None
) -> dict[str, Any]:
    return _attempt(
        lambda: _update_pr_api(repo, number, body, title),
        lambda: _update_pr_gh(repo, number, body, title, cwd),
        number=number,
    )


def _set_ready_api(repo: str, number: int) -> dict[str, Any]:
    tok = token() or ""
    got = _request("GET", f"{API_ROOT}/repos/{repo}/pulls/{number}", tok)
    node_id = got["data"].get("node_id") if isinstance(got["data"], dict) else None
    if got["error"] or not node_id:
        return {"route": "api", "ok": False, "reason": got["error"] or "no node id"}
    mutation = (
        "mutation($id:ID!){markPullRequestReadyForReview(input:{pullRequestId:$id})"
        "{pullRequest{number isDraft}}}"
    )
    result = _request("POST", GRAPHQL_URL, tok, {"query": mutation, "variables": {"id": node_id}})
    errors = result["data"].get("errors") if isinstance(result["data"], dict) else None
    if result["error"] or errors:
        reason = result["error"] or json.dumps(errors)
        return {"route": "api", "ok": False, "reason": reason, "number": number}
    return {"route": "api", "ok": True, "number": number}


def set_ready(repo: str, number: int, cwd: str | Path | None = None) -> dict[str, Any]:
    """Mark a draft PR ready for review (phase (e)). REST has no such field: the GraphQL
    mutation ``markPullRequestReadyForReview`` takes the PR's node id."""

    def via_gh() -> dict[str, Any]:
        result = _gh("pr", "ready", str(number), "--repo", repo, cwd=cwd)
        if not result["ok"]:
            return {
                "route": "gh",
                "ok": False,
                "reason": _gh_error(result, "gh pr ready"),
                "number": number,
            }
        return {"route": "gh", "ok": True, "number": number}

    return _attempt(lambda: _set_ready_api(repo, number), via_gh, number=number)


# --- labels ---------------------------------------------------------------------------------
def ensure_label(
    repo: str, name: str, color: str, description: str, cwd: str | Path | None = None
) -> dict[str, Any]:
    """Create the label if the repository does not have it; an existing one is success.

    Never ``--force``: that would rewrite the colour and description of a label the owner
    edited. ``gh`` says "already exists" instead, which is the success we want.
    """

    def via_api() -> dict[str, Any]:
        payload = {"name": name, "color": color, "description": description}
        result = _request("POST", f"{API_ROOT}/repos/{repo}/labels", token() or "", payload)
        if result["status"] == 422 and "already_exists" in json.dumps(result["data"]):
            return {"route": "api", "ok": True, "label": name, "created": False}
        if result["error"]:
            return {"route": "api", "ok": False, "reason": result["error"], "label": name}
        return {"route": "api", "ok": True, "label": name, "created": True}

    def via_gh() -> dict[str, Any]:
        result = _gh(
            "label", "create", name, "--repo", repo,
            "--color", color, "--description", description, cwd=cwd,
        )  # fmt: skip
        if not result["ok"]:
            if "already exists" in (result["err"] or "").lower():
                return {"route": "gh", "ok": True, "label": name, "created": False}
            return {
                "route": "gh",
                "ok": False,
                "reason": _gh_error(result, "gh label create"),
                "label": name,
            }
        return {"route": "gh", "ok": True, "label": name, "created": True}

    return _attempt(via_api, via_gh, label=name)


def set_labels(
    repo: str,
    number: int,
    add: list[str],
    remove: list[str],
    cwd: str | Path | None = None,
) -> dict[str, Any]:
    """Remove first, then add: the PR carries exactly one ``sdlc:`` label at a time."""

    def via_api() -> dict[str, Any]:
        tok = token() or ""
        base = f"{API_ROOT}/repos/{repo}/issues/{number}/labels"
        removed, added, problems = [], [], []
        for name in remove:
            result = _request("DELETE", f"{base}/{urllib.parse.quote(name)}", tok)
            if result["status"] == 404:  # the PR does not carry it: nothing to do
                continue
            if result["error"]:
                problems.append(f"remove {name}: {result['error']}")
            else:
                removed.append(name)
        if add:
            result = _request("POST", base, tok, {"labels": list(add)})
            if result["error"]:
                problems.append(f"add {', '.join(add)}: {result['error']}")
            else:
                added = list(add)
        return {
            "route": "api",
            "ok": not problems,
            "added": added,
            "removed": removed,
            "reason": "; ".join(problems),
        }

    def via_gh() -> dict[str, Any]:
        args = ["pr", "edit", str(number), "--repo", repo]
        for name in remove:
            args += ["--remove-label", name]
        for name in add:
            args += ["--add-label", name]
        result = _gh(*args, cwd=cwd)
        if not result["ok"]:
            return {
                "route": "gh",
                "ok": False,
                "reason": _gh_error(result, "gh pr edit"),
                "number": number,
            }
        return {"route": "gh", "ok": True, "added": list(add), "removed": list(remove)}

    if not remove and not add:
        return {"route": "none", "ok": True, "added": [], "removed": []}
    return _attempt(via_api, via_gh, number=number)


# --- check runs -------------------------------------------------------------------------------
def create_check_run(
    repo: str,
    head_sha: str,
    name: str,
    conclusion: str,
    title: str,
    summary: str,
    cwd: str | Path | None = None,
) -> dict[str, Any]:
    """The phase (d) check run (build guide step 28). Check runs need an app/installation
    token, which neither ``gh``'s user token nor every workflow token is - both routes are
    tried and the failure is reported rather than a route invented."""
    payload = {
        "name": name,
        "head_sha": head_sha,
        "status": "completed",
        "conclusion": conclusion,
        "output": {"title": title, "summary": summary},
    }

    def via_api() -> dict[str, Any]:
        result = _request("POST", f"{API_ROOT}/repos/{repo}/check-runs", token() or "", payload)
        if result["error"]:
            return {"route": "api", "ok": False, "reason": result["error"]}
        return {
            "route": "api",
            "ok": True,
            "id": result["data"].get("id"),
            "url": result["data"].get("html_url"),
        }

    def via_gh() -> dict[str, Any]:
        result = _gh(
            "api", "--method", "POST", f"repos/{repo}/check-runs", "--input", "-",
            stdin=json.dumps(payload), cwd=cwd,
        )  # fmt: skip
        if not result["ok"]:
            return {"route": "gh", "ok": False, "reason": _gh_error(result, "gh api check-runs")}
        try:
            data = json.loads(result["out"] or "{}")
        except ValueError:
            data = {}
        return {"route": "gh", "ok": True, "id": data.get("id"), "url": data.get("html_url")}

    return _attempt(via_api, via_gh)


# --- issues (the daily digest lives in one) ----------------------------------------------------
def pinned_issue(repo: str, title: str, cwd: str | Path | None = None) -> dict[str, Any]:
    """The open issue with this exact title, if any: {'number', 'node_id'}."""

    def via_api() -> dict[str, Any]:
        query = urllib.parse.urlencode({"state": "open", "per_page": 100})
        result = _request("GET", f"{API_ROOT}/repos/{repo}/issues?{query}", token() or "")
        if result["error"]:
            return {"route": "api", "ok": False, "reason": result["error"], "number": None}
        items = result["data"] if isinstance(result["data"], list) else []
        for item in items:
            if "pull_request" in item:
                continue
            if str(item.get("title", "")).strip() == title:
                return {
                    "route": "api",
                    "ok": True,
                    "number": item.get("number"),
                    "node_id": item.get("node_id"),
                }
        return {"route": "api", "ok": True, "number": None}

    def via_gh() -> dict[str, Any]:
        data, error = _gh_json(
            "issue", "list", "--repo", repo, "--state", "open",
            "--limit", "100", "--json", "number,title,id", cwd=cwd,
        )  # fmt: skip
        if error:
            return {"route": "gh", "ok": False, "reason": error, "number": None}
        for item in data or []:
            if str(item.get("title", "")).strip() == title:
                return {
                    "route": "gh",
                    "ok": True,
                    "number": item.get("number"),
                    "node_id": item.get("id"),
                }
        return {"route": "gh", "ok": True, "number": None}

    return _attempt(via_api, via_gh, number=None)


def create_issue(repo: str, title: str, body: str, cwd: str | Path | None = None) -> dict[str, Any]:
    def via_api() -> dict[str, Any]:
        result = _request(
            "POST", f"{API_ROOT}/repos/{repo}/issues", token() or "", {"title": title, "body": body}
        )
        if result["error"]:
            return {"route": "api", "ok": False, "reason": result["error"]}
        return {
            "route": "api",
            "ok": True,
            "number": result["data"].get("number"),
            "url": result["data"].get("html_url"),
            "node_id": result["data"].get("node_id"),
            "created": True,
        }

    def via_gh() -> dict[str, Any]:
        result = _gh(
            "issue", "create", "--repo", repo, "--title", title, "--body-file", "-",
            stdin=body, cwd=cwd,
        )  # fmt: skip
        if not result["ok"]:
            return {"route": "gh", "ok": False, "reason": _gh_error(result, "gh issue create")}
        url = _gh_url(result)
        return {
            "route": "gh",
            "ok": True,
            "number": _number_in(url),
            "url": url,
            "created": True,
        }

    return _attempt(via_api, via_gh)


def update_issue_body(
    repo: str, number: int, body: str, cwd: str | Path | None = None
) -> dict[str, Any]:
    def via_api() -> dict[str, Any]:
        result = _request(
            "PATCH", f"{API_ROOT}/repos/{repo}/issues/{number}", token() or "", {"body": body}
        )
        if result["error"]:
            return {"route": "api", "ok": False, "reason": result["error"], "number": number}
        return {
            "route": "api",
            "ok": True,
            "number": number,
            "url": result["data"].get("html_url"),
            "created": False,
        }

    def via_gh() -> dict[str, Any]:
        result = _gh(
            "issue", "edit", str(number), "--repo", repo, "--body-file", "-", stdin=body, cwd=cwd
        )
        if not result["ok"]:
            return {
                "route": "gh",
                "ok": False,
                "reason": _gh_error(result, "gh issue edit"),
                "number": number,
            }
        return {"route": "gh", "ok": True, "number": number, "created": False}

    return _attempt(via_api, via_gh, number=number)


def pin_issue(repo: str, node_id: str | None) -> dict[str, Any]:
    """Best effort: a pinned issue is convenience, never a precondition."""
    if not node_id:
        return _no_route("no issue node id to pin")
    tok = token()
    if not tok:
        return _no_route("pinning needs a token (GraphQL)")
    mutation = "mutation($id:ID!){pinIssue(input:{issueId:$id}){issue{number}}}"
    result = _request("POST", GRAPHQL_URL, tok, {"query": mutation, "variables": {"id": node_id}})
    errors = result["data"].get("errors") if isinstance(result["data"], dict) else None
    if result["error"] or errors:
        return {"route": "api", "ok": False, "reason": result["error"] or json.dumps(errors)}
    return {"route": "api", "ok": True}
