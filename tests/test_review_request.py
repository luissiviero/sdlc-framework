"""Decision 31: the owner's review request on a pull request that waits (ROADMAP R47).

``pr/review_request.py sync_owner_review`` with a fake GitHub module; ``pr/cli.py upsert
--request-review`` with the client's functions monkeypatched (nothing leaves the process),
including the runner's rule that only the default branch's ``sdlc.yaml`` names the owner;
the callers that pass the flag (the runner's two publishers, the detect workflow's three
upserts); and the client's new fields and routes."""

from __future__ import annotations

import inspect
import json
from pathlib import Path

import pytest
from ci import run_phase
from detect import cli as detect_cli
from pr import cli as pr_cli
from pr import github
from pr import review_request as rr

from state import conventions as c
from tests import test_pr as pr_tests
from tests.test_pr import gate_json, git

# the fixture of tests/test_pr.py, used here by name
project = pr_tests.project

REPO = "o/r"
OWNER = "owner"
ENV = {"GITHUB_REPOSITORY_OWNER": OWNER, "GITHUB_REPOSITORY": "owner/r"}


class FakeGitHub:
    """Records ``request_reviewers`` and ``remove_reviewers`` in order; each answers ``ok``
    unless ``fail`` names it."""

    def __init__(self, fail: str | None = None) -> None:
        self.calls: list[tuple[str, int, list[str]]] = []
        self.fail = fail

    def _answer(self, name: str, number: int, logins: list[str]) -> dict:
        self.calls.append((name, number, list(logins)))
        if self.fail == name:
            return {"route": "api", "ok": False, "reason": "Validation Failed"}
        return {"route": "api", "ok": True}

    def request_reviewers(self, repo, number, logins, cwd=None):
        return self._answer("request", number, logins)

    def remove_reviewers(self, repo, number, logins, cwd=None):
        return self._answer("remove", number, logins)


def pr(pending: bool = False, author: str = "github-actions[bot]", state: str = "open") -> dict:
    return {
        "ok": True,
        "number": 5,
        "state": state,
        "author": author,
        "draft": False,
        "requested_reviewers": [OWNER.upper()] if pending else [],
    }


# --- 1. the decision --------------------------------------------------------------------------
@pytest.mark.parametrize(
    "label", [c.NEEDS_HUMAN_LABEL, c.ready_label("design"), c.ready_label("deploy")]
)
def test_a_waiting_label_requests_the_owner_s_review(label):
    gh = FakeGitHub()
    out = rr.sync_owner_review(gh, REPO, 5, label, {}, ENV, pr())
    assert out["ok"] and out["action"] == "requested" and out["owner"] == OWNER
    assert gh.calls == [("request", 5, [OWNER])]


@pytest.mark.parametrize("label", [c.NEEDS_HUMAN_LABEL, c.ready_label("build")])
def test_a_pending_request_is_removed_and_requested_again(label):
    """The owner's ``@claude`` comment or approval label leaves the request pending: every new
    wait gives one fresh push."""
    gh = FakeGitHub()
    out = rr.sync_owner_review(gh, REPO, 5, label, {}, ENV, pr(pending=True))
    assert out["ok"] and out["action"] == "re-requested"
    assert gh.calls == [("remove", 5, [OWNER]), ("request", 5, [OWNER])]


@pytest.mark.parametrize("label", [c.FIXING_LABEL, None, "sdlc:c-approved"])
def test_a_label_that_does_not_wait_withdraws_a_pending_request(label):
    gh = FakeGitHub()
    out = rr.sync_owner_review(gh, REPO, 5, label, {}, ENV, pr(pending=True))
    assert out["ok"] and out["action"] == "withdrawn"
    assert gh.calls == [("remove", 5, [OWNER])]
    gh = FakeGitHub()
    out = rr.sync_owner_review(gh, REPO, 5, label, {}, ENV, pr())
    assert out["ok"] and out["action"] == "none" and gh.calls == []


def test_is_waiting_label():
    assert all(rr.is_waiting_label(c.ready_label(p)) for p in c.PHASES)
    assert rr.is_waiting_label(c.NEEDS_HUMAN_LABEL)
    for label in (None, "", c.FIXING_LABEL, "sdlc:d-approved", c.GO_LABEL, "sdlc:x-ready"):
        assert not rr.is_waiting_label(label)


# --- 2. the skips -----------------------------------------------------------------------------
def test_the_owner_s_own_pr_is_skipped():
    """GitHub refuses a review request to a PR's author: the owner's own intent PR."""
    gh = FakeGitHub()
    out = rr.sync_owner_review(gh, REPO, 5, c.ready_label("intent"), {}, ENV, pr(author="OWNER"))
    assert out["ok"] and "author" in out["skipped"] and gh.calls == []


def test_a_closed_pr_is_skipped():
    gh = FakeGitHub()
    out = rr.sync_owner_review(gh, REPO, 5, c.NEEDS_HUMAN_LABEL, {}, ENV, pr(state="closed"))
    assert out["ok"] and "not open" in out["skipped"] and gh.calls == []


def test_no_owner_is_skipped():
    gh = FakeGitHub()
    out = rr.sync_owner_review(gh, "", 5, c.NEEDS_HUMAN_LABEL, {}, {}, pr())
    assert out["ok"] and "no owner" in out["skipped"] and gh.calls == []


@pytest.mark.parametrize(
    "config",
    [
        {"owner": "github-actions[bot]"},
        {"owner": "sdlc-bot", "automation_identity": ["sdlc-bot"]},
    ],
)
def test_an_owner_key_naming_the_automation_fails_closed(config):
    gh = FakeGitHub()
    out = rr.sync_owner_review(gh, REPO, 5, c.NEEDS_HUMAN_LABEL, config, ENV, pr())
    assert out["ok"] and "fail closed" in out["skipped"] and gh.calls == []


# --- 3. a GitHub failure ----------------------------------------------------------------------
@pytest.mark.parametrize(
    ("fail", "pending", "label"),
    [
        ("request", False, c.NEEDS_HUMAN_LABEL),
        ("remove", True, c.NEEDS_HUMAN_LABEL),
        ("remove", True, c.FIXING_LABEL),
    ],
)
def test_a_github_failure_is_a_reason_never_an_exception(fail, pending, label):
    out = rr.sync_owner_review(FakeGitHub(fail), REPO, 5, label, {}, ENV, pr(pending=pending))
    assert out["ok"] is False and "Validation Failed" in out["reason"]


# --- 4. pr/cli.py upsert --request-review ----------------------------------------------------
@pytest.fixture
def fake_routes(monkeypatch):
    """Every client function ``upsert`` calls, answered offline; review calls recorded."""
    state = {"existing": None, "calls": [], "reviewers": []}

    def find_open_pr(repo, head, cwd=None, reviewers=False):
        state["reviewers"].append(("find", reviewers))
        existing = state["existing"]
        return {"route": "api", "ok": True, **(existing or {"number": None, "labels": []})}

    def pr_by_number(repo, number, cwd=None, reviewers=False):
        state["reviewers"].append(("by_number", reviewers))
        return {"route": "api", "ok": True, **pr(), "number": 9}

    def record(name):
        def call(repo, number, logins, cwd=None):
            state["calls"].append((name, number, list(logins)))
            return {"route": "api", "ok": True}

        return call

    monkeypatch.setattr(github, "find_open_pr", find_open_pr)
    monkeypatch.setattr(
        github,
        "create_pr",
        lambda *a, **k: {"route": "api", "ok": True, "number": 9, "url": "u", "created": True},
    )
    monkeypatch.setattr(
        github,
        "update_pr",
        lambda *a, **k: {"route": "api", "ok": True, "number": 9, "url": "u", "created": False},
    )
    monkeypatch.setattr(
        github,
        "pr_by_number",
        pr_by_number,
    )
    monkeypatch.setattr(github, "ensure_label", lambda *a, **k: {"ok": True})
    monkeypatch.setattr(github, "set_labels", lambda *a, **k: {"ok": True})
    monkeypatch.setattr(github, "request_reviewers", record("request"))
    monkeypatch.setattr(github, "remove_reviewers", record("remove"))
    monkeypatch.setenv("GITHUB_REPOSITORY_OWNER", OWNER)
    return state


def upsert(capsys, root: Path, *extra: str) -> dict:
    code = pr_cli.main(["upsert", "--root", str(root), "--id", "0001", "--phase", "design", *extra])
    assert code == 0
    return json.loads(capsys.readouterr().out)


def test_upsert_requests_the_review_only_with_the_flag(project, capsys, fake_routes):
    root, change = project
    git(root, "remote", "add", "origin", "https://github.com/o/r.git")
    gate_json(change, "b", "wait", c.ready_label("design"))
    out = upsert(capsys, root)
    assert out["created"] is True and "review_request" not in out
    assert fake_routes["calls"] == []  # the model's in-session upserts request nothing
    # the plain lookup, as before, and (R22) the head read back for the "not a build PR"
    # check this design PR carries
    assert fake_routes["reviewers"] == [("find", False), ("by_number", False)]
    out = upsert(capsys, root, "--request-review")
    assert out["review_request"]["action"] == "requested"
    assert fake_routes["calls"] == [("request", 9, [OWNER])]
    # the sync's lookups ask for the author and the pending reviewers
    assert fake_routes["reviewers"][2:] == [
        ("find", True),
        ("by_number", False),
        ("by_number", True),
    ]
    # a later publication on the same PR, now carrying sdlc:fixing: the request is withdrawn
    fake_routes["calls"].clear()
    fake_routes["existing"] = {**pr(pending=True), "number": 9, "labels": [c.ready_label("design")]}
    gate_json(change, "b", "wait", c.FIXING_LABEL)
    out = upsert(capsys, root, "--request-review")
    assert out["review_request"]["action"] == "withdrawn" and out["label"] == c.FIXING_LABEL
    assert fake_routes["calls"] == [("remove", 9, [OWNER])]


def test_a_failed_request_does_not_change_the_upsert(project, capsys, fake_routes, monkeypatch):
    root, change = project
    git(root, "remote", "add", "origin", "https://github.com/o/r.git")
    gate_json(change, "b", "park", c.NEEDS_HUMAN_LABEL)
    monkeypatch.setattr(
        github, "request_reviewers", lambda *a, **k: {"ok": False, "reason": "HTTP 422"}
    )
    out = upsert(capsys, root, "--request-review")
    assert out["route"] == "api" and out["number"] == 9
    assert out["review_request"] == {
        "ok": False,
        "owner": OWNER,
        "label": c.NEEDS_HUMAN_LABEL,
        "reason": "request: HTTP 422",
    }
    assert run_phase.upsert_outcome({"ok": True, "output": out})["ok"] is True


def _runner_project(root: Path, monkeypatch, default_owner: str | None) -> None:
    """The default branch's copy names ``default_owner`` (none: no copy is located); the PR's
    head writes ``owner: intruder``."""
    git(root, "remote", "add", "origin", "https://github.com/o/r.git")
    sdlc = root / "sdlc.yaml"
    if default_owner:
        sdlc.write_text(sdlc.read_text(encoding="utf-8") + f"owner: {default_owner}\n", "utf-8")
        git(root, "commit", "-q", "-am", "owner on the default branch")
        git(root, "update-ref", "refs/remotes/origin/main", "HEAD")
    git(root, "checkout", "-q", "-b", "sdlc/0001/design")
    text = sdlc.read_text(encoding="utf-8").replace(f"owner: {default_owner}\n", "")
    sdlc.write_text(text + "owner: intruder\n", encoding="utf-8")
    git(root, "commit", "-q", "-am", "the head names its own owner")
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    monkeypatch.setenv("SDLC_DEFAULT_BRANCH", "main")


def test_on_a_runner_the_default_branch_names_the_owner(project, capsys, fake_routes, monkeypatch):
    root, change = project
    _runner_project(root, monkeypatch, "realowner")
    gate_json(change, "b", "park", c.NEEDS_HUMAN_LABEL)
    out = upsert(capsys, root, "--request-review")
    assert out["review_request"]["owner"] == "realowner"
    assert fake_routes["calls"] == [("request", 9, ["realowner"])]


def test_on_a_runner_a_default_copy_without_owner_falls_to_the_repository_owner(
    project, capsys, fake_routes, monkeypatch
):
    """The default branch's copy names no owner while the head writes ``owner: intruder``:
    the owner is the repository owner from the runner's environment, never the head's."""
    root, change = project
    git(root, "remote", "add", "origin", "https://github.com/o/r.git")
    git(root, "update-ref", "refs/remotes/origin/main", "HEAD")
    git(root, "checkout", "-q", "-b", "sdlc/0001/design")
    sdlc = root / "sdlc.yaml"
    sdlc.write_text(sdlc.read_text(encoding="utf-8") + "owner: intruder\n", encoding="utf-8")
    git(root, "commit", "-q", "-am", "the head names its own owner")
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    monkeypatch.setenv("SDLC_DEFAULT_BRANCH", "main")
    gate_json(change, "b", "park", c.NEEDS_HUMAN_LABEL)
    out = upsert(capsys, root, "--request-review")
    assert out["review_request"]["owner"] == OWNER
    assert fake_routes["calls"] == [("request", 9, [OWNER])]


def test_a_new_pr_that_cannot_be_read_back_is_requested_as_nobody_s(
    project, capsys, fake_routes, monkeypatch
):
    """The re-read of a just-created PR failed: it is open and nobody is requested yet."""
    root, change = project
    git(root, "remote", "add", "origin", "https://github.com/o/r.git")
    gate_json(change, "b", "wait", c.ready_label("design"))
    monkeypatch.setattr(github, "pr_by_number", lambda *a, **k: {"ok": False, "reason": "HTTP 502"})
    out = upsert(capsys, root, "--request-review")
    assert out["created"] is True and out["review_request"]["action"] == "requested"
    assert fake_routes["calls"] == [("request", 9, [OWNER])]


def test_an_error_in_the_sync_never_changes_the_upsert(project, capsys, fake_routes, monkeypatch):
    root, change = project
    git(root, "remote", "add", "origin", "https://github.com/o/r.git")
    gate_json(change, "b", "park", c.NEEDS_HUMAN_LABEL)

    def boom(*_a, **_k):
        raise RuntimeError("unexpected")

    monkeypatch.setattr(pr_cli.review_request, "sync_owner_review", boom)
    out = upsert(capsys, root, "--request-review")
    assert out["route"] == "api" and out["number"] == 9
    assert out["review_request"] == {
        "ok": False,
        "reason": "review request: RuntimeError: unexpected",
    }


def test_on_a_runner_without_the_default_branch_copy_nobody_is_requested(
    project, capsys, fake_routes, monkeypatch
):
    root, change = project
    _runner_project(root, monkeypatch, None)
    gate_json(change, "b", "park", c.NEEDS_HUMAN_LABEL)
    out = upsert(capsys, root, "--request-review")
    assert out["route"] == "api" and "decision 34" in out["review_request"]["skipped"]
    assert fake_routes["calls"] == []


# --- 5. the callers pass the flag -------------------------------------------------------------
def test_the_runner_s_publishers_pass_request_review(tmp_path, monkeypatch):
    seen: list[list[str]] = []

    def fake_cli_call(script, argv, timeout=600, env=None):
        seen.append(list(argv))
        return {"ok": True, "output": {"route": "api", "number": 3, "url": "u"}}

    class Client:
        @staticmethod
        def gh_path():
            return None

        @staticmethod
        def find_open_pr(repo, head, cwd=None):
            return {"ok": True, "number": 3}

    monkeypatch.setattr(run_phase, "_cli_call", fake_cli_call)
    monkeypatch.setattr(run_phase, "_github", lambda: Client)
    monkeypatch.setattr(run_phase, "park", lambda *a, **k: {"ok": True})
    monkeypatch.setattr(run_phase, "write_park_result", lambda *a, **k: None)
    out = run_phase.ensure_pr(tmp_path, tmp_path, "0001", "c", REPO, {"GITHUB_TOKEN": "t"})
    assert out["ok"] and seen[-1][0] == "upsert" and seen[-1][-1] == "--request-review"
    st = type("St", (), {"phase": "build", "id": "0001"})()
    run_phase.park_and_publish(tmp_path, tmp_path, tmp_path, st, "c", "gate: red")
    upserts = [argv for argv in seen if argv[0] == "upsert"]
    assert len(upserts) == 2 and "--request-review" in upserts[-1]


def test_the_detect_publications_pass_request_review(tmp_path, monkeypatch):
    seen: list[list[str]] = []

    def fake_cli(script, argv, cwd):
        seen.append(list(argv))
        return {}, 0, ""

    monkeypatch.setattr(detect_cli, "_cli", fake_cli)
    monkeypatch.setattr(detect_cli, "_commit_change", lambda *a, **k: {"ok": True})
    detect_cli._gate_and_pr(tmp_path, "0001", False, {})
    assert seen[-1] == detect_cli._upsert_argv(tmp_path, "0001")
    assert seen[-1][0] == "upsert" and seen[-1][-1] == "--request-review"
    # cmd_finish's park and cmd_park build the same argv: no other upsert in the module
    source = inspect.getsource(detect_cli)
    assert source.count('"upsert"') == 1 and source.count("_upsert_argv(root, ") == 3


# --- 6. the GitHub client ---------------------------------------------------------------------
def test_the_pr_shape_carries_author_and_requested_reviewers():
    api = github._pr_from_api(
        {
            "number": 1,
            "state": "open",
            "user": {"login": "github-actions[bot]"},
            "requested_reviewers": [{"login": OWNER}, {"login": "other"}],
        }
    )
    assert api["author"] == "github-actions[bot]" and api["requested_reviewers"] == [OWNER, "other"]
    gh = github._pr_from_gh(
        {
            "number": 1,
            "state": "OPEN",
            "author": {"login": "app/github-actions"},
            "reviewRequests": [{"__typename": "User", "login": OWNER}, {"slug": "team"}],
        }
    )
    assert gh["author"] == "app/github-actions" and gh["requested_reviewers"] == [OWNER]
    assert github._EMPTY_PR["requested_reviewers"] == [] and github._EMPTY_PR["author"] is None


def test_request_and_remove_reviewers_use_the_rest_route(monkeypatch):
    calls: list[tuple] = []

    def fake(method, url, tok, payload=None):
        calls.append((method, url, payload))
        if method == "DELETE":
            return {"status": 422, "data": {}, "error": "Reviews may only be requested..."}
        return {"status": 201, "data": {}, "error": ""}

    monkeypatch.setattr(github.shutil, "which", lambda *_a, **_k: None)
    monkeypatch.setenv("GITHUB_TOKEN", "t")
    monkeypatch.setattr(github, "_request", fake)
    path = "https://api.github.com/repos/o/r/pulls/5/requested_reviewers"
    assert github.request_reviewers(REPO, 5, [OWNER])["ok"] is True
    removed = github.remove_reviewers(REPO, 5, [OWNER])
    assert removed["ok"] is False and "Reviews may only" in removed["reason"]
    assert calls == [
        ("POST", path, {"reviewers": [OWNER]}),
        ("DELETE", path, {"reviewers": [OWNER]}),
    ]


def test_remove_reviewers_gh_route(monkeypatch):
    seen: list[tuple] = []

    def fake_gh(*args, stdin=None, cwd=None):
        seen.append(args)
        return {"ok": True, "code": 0, "out": "", "err": ""}

    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    monkeypatch.delenv("GH_TOKEN", raising=False)
    monkeypatch.setattr(github, "gh_path", lambda: "/usr/bin/gh")
    monkeypatch.setattr(github, "_gh", fake_gh)
    assert github.remove_reviewers(REPO, 5, [OWNER])["route"] == "gh"
    assert github.request_reviewers(REPO, 5, [OWNER])["ok"] is True
    assert seen == [
        ("pr", "edit", "5", "--repo", REPO, "--remove-reviewer", OWNER),
        ("pr", "edit", "5", "--repo", REPO, "--add-reviewer", OWNER),
    ]


def test_only_the_sync_s_lookups_ask_gh_for_review_requests(monkeypatch):
    """A team's review request can fail ``reviewRequests`` under a workflow token: every
    other lookup keeps the narrow field set."""
    seen: list[str] = []

    def fake_gh_json(*args, cwd=None):
        seen.append(args[args.index("--json") + 1])
        return ({"number": 1, "state": "OPEN"} if args[1] == "view" else []), ""

    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    monkeypatch.delenv("GH_TOKEN", raising=False)
    monkeypatch.setattr(github, "gh_path", lambda: "/usr/bin/gh")
    monkeypatch.setattr(github, "_gh_json", fake_gh_json)
    github.find_open_pr(REPO, "sdlc/0001/design")
    github.pr_by_number(REPO, 1)
    github.find_pr(REPO, "sdlc/0001/design", "all")
    assert seen == [github.GH_PR_FIELDS] * 3 and "reviewRequests" not in github.GH_PR_FIELDS
    seen.clear()
    github.find_open_pr(REPO, "sdlc/0001/design", reviewers=True)
    github.pr_by_number(REPO, 1, reviewers=True)
    assert seen == [github.GH_REVIEW_FIELDS] * 2
    assert "author" in github.GH_REVIEW_FIELDS and "reviewRequests" in github.GH_REVIEW_FIELDS
