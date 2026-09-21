"""A thin GitHub client with three routes, tried in that order (the fallback chain
``/sdlc-plan`` step 6 already uses by hand, made deterministic here):

1. **gh** - the ``gh`` CLI when it is on PATH and authenticated (the owner's PC, most CI);
2. **api** - the REST API over ``urllib`` with ``GITHUB_TOKEN`` or ``GH_TOKEN`` (the
   automation identity in a workflow);
3. **none** - nothing is contacted: the caller gets the compare URL and prints it with the
   body so the owner opens the PR by hand. A missing route is never an error.

No third-party dependency (decision 7), a 30 s timeout on every request, and the token is
never printed: it only ever reaches an ``Authorization`` header inside ``_request``, which is
the single HTTP entry point (so tests monkeypatch one function).
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

API_ROOT = "https://api.github.com"
GRAPHQL_URL = f"{API_ROOT}/graphql"
API_VERSION = "2022-11-28"
TIMEOUT = 30  # seconds, every request
TOKEN_VARS = ("GITHUB_TOKEN", "GH_TOKEN")
GH_TIMEOUT = 120  # seconds for one gh invocation


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


# --- the one HTTP entry point -----------------------------------------------------------------
def _request(
    method: str, url: str, tok: str, payload: dict[str, Any] | None = None
) -> dict[str, Any]:
    """{'status', 'data', 'error'}. The only place a token touches the network."""
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
    except urllib.error.HTTPError as exc:  # 4xx/5xx carry a body worth reading
        raw = exc.read().decode("utf-8", errors="replace")
        status = exc.code
    except (urllib.error.URLError, OSError, ValueError) as exc:
        return {"status": 0, "data": {}, "error": f"{type(exc).__name__}: {exc}"}
    try:
        data = json.loads(raw) if raw.strip() else {}
    except ValueError:
        data = {"raw": raw}
    error = "" if 200 <= status < 300 else str(data.get("message", f"HTTP {status}"))
    return {"status": status, "data": data, "error": error}


def _gh(*args: str, stdin: str | None = None) -> dict[str, Any]:
    """Run ``gh`` with an argument list (no shell, so the same call works on Windows)."""
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


def _gh_json(*args: str) -> tuple[Any, str]:
    result = _gh(*args)
    if not result["ok"]:
        return None, result["err"] or f"gh exited {result['code']}"
    try:
        return json.loads(result["out"] or "null"), ""
    except ValueError as exc:
        return None, f"gh output is not JSON: {exc}"


# --- pull requests -----------------------------------------------------------------------------
def find_open_pr(repo: str, head_branch: str) -> dict[str, Any]:
    """{'route', 'number', 'url', 'labels', 'draft'} - number None when there is none."""
    if gh_path():
        data, error = _gh_json(
            "pr",
            "list",
            "--repo",
            repo,
            "--head",
            head_branch,
            "--state",
            "open",
            "--json",
            "number,url,labels,isDraft",
        )
        if error:
            return _no_route(error, number=None)
        first = (data or [None])[0] if isinstance(data, list) else None
        if not first:
            return {"route": "gh", "ok": True, "number": None, "url": None, "labels": []}
        return {
            "route": "gh",
            "ok": True,
            "number": first.get("number"),
            "url": first.get("url"),
            "labels": [lb.get("name") for lb in first.get("labels") or []],
            "draft": bool(first.get("isDraft")),
        }
    tok = token()
    if not tok:
        return _no_route("no gh on PATH and no GITHUB_TOKEN/GH_TOKEN", number=None)
    owner = repo.split("/")[0]
    query = urllib.parse.urlencode({"state": "open", "head": f"{owner}:{head_branch}"})
    result = _request("GET", f"{API_ROOT}/repos/{repo}/pulls?{query}", tok)
    if result["error"]:
        return {"route": "api", "ok": False, "reason": result["error"], "number": None}
    items = result["data"] if isinstance(result["data"], list) else []
    if not items:
        return {"route": "api", "ok": True, "number": None, "url": None, "labels": []}
    first = items[0]
    return {
        "route": "api",
        "ok": True,
        "number": first.get("number"),
        "url": first.get("html_url"),
        "labels": [lb.get("name") for lb in first.get("labels") or []],
        "draft": bool(first.get("draft")),
        "node_id": first.get("node_id"),
    }


def create_pr(
    repo: str, base: str, head: str, title: str, body: str, draft: bool = False
) -> dict[str, Any]:
    if gh_path():
        args = [
            "pr",
            "create",
            "--repo",
            repo,
            "--base",
            base,
            "--head",
            head,
            "--title",
            title,
            "--body-file",
            "-",
        ]
        if draft:
            args.append("--draft")
        result = _gh(*args, stdin=body)
        if not result["ok"]:
            return _no_route(result["err"] or "gh pr create failed")
        url = (result["out"] or "").strip().splitlines()[-1] if result["out"].strip() else None
        number = None
        if url and url.rsplit("/", 1)[-1].isdigit():
            number = int(url.rsplit("/", 1)[-1])
        return {"route": "gh", "ok": True, "number": number, "url": url, "created": True}
    tok = token()
    if not tok:
        return _no_route(
            "no gh on PATH and no GITHUB_TOKEN/GH_TOKEN",
            compare_url=compare_url(repo, base, head),
        )
    payload = {"title": title, "head": head, "base": base, "body": body, "draft": bool(draft)}
    result = _request("POST", f"{API_ROOT}/repos/{repo}/pulls", tok, payload)
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


def update_pr(repo: str, number: int, body: str, title: str | None = None) -> dict[str, Any]:
    if gh_path():
        args = ["pr", "edit", str(number), "--repo", repo, "--body-file", "-"]
        if title:
            args += ["--title", title]
        result = _gh(*args, stdin=body)
        if not result["ok"]:
            return _no_route(result["err"] or "gh pr edit failed", number=number)
        url = (result["out"] or "").strip().splitlines()[-1] if result["out"].strip() else None
        return {"route": "gh", "ok": True, "number": number, "url": url, "created": False}
    tok = token()
    if not tok:
        return _no_route("no gh on PATH and no GITHUB_TOKEN/GH_TOKEN", number=number)
    payload: dict[str, Any] = {"body": body}
    if title:
        payload["title"] = title
    result = _request("PATCH", f"{API_ROOT}/repos/{repo}/pulls/{number}", tok, payload)
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


def set_ready(repo: str, number: int) -> dict[str, Any]:
    """Mark a draft PR ready for review (phase (e)). REST has no such field: the GraphQL
    mutation ``markPullRequestReadyForReview`` takes the PR's node id."""
    if gh_path():
        result = _gh("pr", "ready", str(number), "--repo", repo)
        if not result["ok"]:
            return _no_route(result["err"] or "gh pr ready failed", number=number)
        return {"route": "gh", "ok": True, "number": number}
    tok = token()
    if not tok:
        return _no_route("no gh on PATH and no GITHUB_TOKEN/GH_TOKEN", number=number)
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


# --- labels ---------------------------------------------------------------------------------
def ensure_label(repo: str, name: str, color: str, description: str) -> dict[str, Any]:
    """Create the label if the repository does not have it; an existing one is success."""
    if gh_path():
        result = _gh(
            "label",
            "create",
            name,
            "--repo",
            repo,
            "--force",
            "--color",
            color,
            "--description",
            description,
        )
        if not result["ok"]:
            return _no_route(result["err"] or "gh label create failed", label=name)
        return {"route": "gh", "ok": True, "label": name, "created": True}
    tok = token()
    if not tok:
        return _no_route("no gh on PATH and no GITHUB_TOKEN/GH_TOKEN", label=name)
    payload = {"name": name, "color": color, "description": description}
    result = _request("POST", f"{API_ROOT}/repos/{repo}/labels", tok, payload)
    if result["status"] == 422 and "already_exists" in json.dumps(result["data"]):
        return {"route": "api", "ok": True, "label": name, "created": False}
    if result["error"]:
        return {"route": "api", "ok": False, "reason": result["error"], "label": name}
    return {"route": "api", "ok": True, "label": name, "created": True}


def set_labels(repo: str, number: int, add: list[str], remove: list[str]) -> dict[str, Any]:
    """Remove first, then add: the PR carries exactly one ``sdlc:`` label at a time."""
    if gh_path():
        args = ["pr", "edit", str(number), "--repo", repo]
        for name in remove:
            args += ["--remove-label", name]
        for name in add:
            args += ["--add-label", name]
        if not remove and not add:
            return {"route": "gh", "ok": True, "added": [], "removed": []}
        result = _gh(*args)
        if not result["ok"]:
            return _no_route(result["err"] or "gh pr edit failed", number=number)
        return {"route": "gh", "ok": True, "added": list(add), "removed": list(remove)}
    tok = token()
    if not tok:
        return _no_route("no gh on PATH and no GITHUB_TOKEN/GH_TOKEN", number=number)
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


# --- check runs -------------------------------------------------------------------------------
def create_check_run(
    repo: str, head_sha: str, name: str, conclusion: str, title: str, summary: str
) -> dict[str, Any]:
    """The phase (d) check run (build guide step 28). Check runs need an app/installation
    token, which ``gh``'s user token usually is not - we try ``gh api`` anyway and report the
    failure rather than inventing a route."""
    payload = {
        "name": name,
        "head_sha": head_sha,
        "status": "completed",
        "conclusion": conclusion,
        "output": {"title": title, "summary": summary},
    }
    if gh_path():
        result = _gh(
            "api",
            "--method",
            "POST",
            f"repos/{repo}/check-runs",
            "--input",
            "-",
            stdin=json.dumps(payload),
        )
        if result["ok"]:
            try:
                data = json.loads(result["out"] or "{}")
            except ValueError:
                data = {}
            return {"route": "gh", "ok": True, "id": data.get("id"), "url": data.get("html_url")}
        # fall through to the token route: a user token cannot create check runs
        if not token():
            return _no_route(result["err"] or "gh api check-runs failed")
    tok = token()
    if not tok:
        return _no_route("no token: a check run needs an app or installation token")
    result = _request("POST", f"{API_ROOT}/repos/{repo}/check-runs", tok, payload)
    if result["error"]:
        return {"route": "api", "ok": False, "reason": result["error"]}
    return {
        "route": "api",
        "ok": True,
        "id": result["data"].get("id"),
        "url": result["data"].get("html_url"),
    }


# --- issues (the daily digest lives in one) ----------------------------------------------------
def pinned_issue(repo: str, title: str) -> dict[str, Any]:
    """The open issue with this exact title, if any: {'number', 'node_id'}."""
    if gh_path():
        data, error = _gh_json(
            "issue",
            "list",
            "--repo",
            repo,
            "--state",
            "open",
            "--limit",
            "100",
            "--json",
            "number,title,id",
        )
        if error:
            return _no_route(error, number=None)
        for item in data or []:
            if str(item.get("title", "")).strip() == title:
                return {
                    "route": "gh",
                    "ok": True,
                    "number": item.get("number"),
                    "node_id": item.get("id"),
                }
        return {"route": "gh", "ok": True, "number": None}
    tok = token()
    if not tok:
        return _no_route("no gh on PATH and no GITHUB_TOKEN/GH_TOKEN", number=None)
    query = urllib.parse.urlencode({"state": "open", "per_page": 100})
    result = _request("GET", f"{API_ROOT}/repos/{repo}/issues?{query}", tok)
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


def create_issue(repo: str, title: str, body: str) -> dict[str, Any]:
    if gh_path():
        result = _gh(
            "issue", "create", "--repo", repo, "--title", title, "--body-file", "-", stdin=body
        )
        if not result["ok"]:
            return _no_route(result["err"] or "gh issue create failed")
        url = (result["out"] or "").strip().splitlines()[-1] if result["out"].strip() else None
        number = int(url.rsplit("/", 1)[-1]) if url and url.rsplit("/", 1)[-1].isdigit() else None
        return {"route": "gh", "ok": True, "number": number, "url": url, "created": True}
    tok = token()
    if not tok:
        return _no_route("no gh on PATH and no GITHUB_TOKEN/GH_TOKEN")
    result = _request(
        "POST", f"{API_ROOT}/repos/{repo}/issues", tok, {"title": title, "body": body}
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


def update_issue_body(repo: str, number: int, body: str) -> dict[str, Any]:
    if gh_path():
        result = _gh("issue", "edit", str(number), "--repo", repo, "--body-file", "-", stdin=body)
        if not result["ok"]:
            return _no_route(result["err"] or "gh issue edit failed", number=number)
        return {"route": "gh", "ok": True, "number": number, "created": False}
    tok = token()
    if not tok:
        return _no_route("no gh on PATH and no GITHUB_TOKEN/GH_TOKEN", number=number)
    result = _request("PATCH", f"{API_ROOT}/repos/{repo}/issues/{number}", tok, {"body": body})
    if result["error"]:
        return {"route": "api", "ok": False, "reason": result["error"], "number": number}
    return {
        "route": "api",
        "ok": True,
        "number": number,
        "url": result["data"].get("html_url"),
        "created": False,
    }


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
