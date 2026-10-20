"""Decision 36 (ROADMAP R22): gate (e) is the owner's approving review, and the merge App
merges on it (``plugin/ci/merge_step.py``, run by ``template/.github/workflows/sdlc-merge.yml``,
whose structure ``tests/test_templates.py`` checks). No model and no network: the GitHub
client and the dispatch are fakes, the event payload a file.
"""

from __future__ import annotations

import json
from pathlib import Path

from ci import app_token, merge_step

from state import status as status_mod
from state import yamlish

REPO = "owner/app"
HEAD = "c" * 40
REVIEWED = "b" * 40
DIR = "changes/0007-dark-mode"


def status_text(**over) -> str:
    st = status_mod.Status.from_dict(
        {"id": "0007", "slug": "dark-mode", "title": "Dark mode", "phase": "e"}
    )
    st.record_gate("e", "passed", "waiting for the owner at gate (e)")
    st.build_pr = 12
    data = {**st.to_dict(), **over}
    return yamlish.dumps(data)


class FakeGitHub:
    """Answers the merge step's reads from what the test sets; records the merge call."""

    NOT_BUILD_TITLE = "not a build PR"

    def __init__(self, **over):
        self.pr = {
            "ok": True,
            "number": 12,
            "state": "open",
            "draft": False,
            "head_ref": "sdlc/0007/c",
            "head_sha": HEAD,
            "head_repo": REPO,
            "base_ref": "main",
            "labels": ["sdlc:e-ready"],
        }
        self.pr.update(over.pop("pr", {}))
        self.files = {
            f"{DIR}/status.yaml": status_text(),
            f"{DIR}/evidence/gate-e.json": json.dumps({"phase": "e", "result": "wait"}),
            f"{DIR}/evidence/review-findings.json": json.dumps(
                {"head": REVIEWED, "findings": [], "summary": "clean"}
            ),
        }
        self.files.update(over.pop("files", {}))
        self.compare = over.pop(
            "compare", {"ok": True, "status": "ahead", "files": [f"{DIR}/evidence/x.json"]}
        )
        self.checks = over.pop("checks", {"ok": True, "runs": [{"conclusion": "success"}]})
        self.reviews = over.pop(
            "reviews",
            {
                "ok": True,
                "reviews": [
                    {"author": "owner", "state": "APPROVED", "commit": HEAD, "at": "2026-10-20"}
                ],
            },
        )
        self.merged = over.pop("merged", {"ok": True, "sha": "d" * 40, "status": 200})
        self.calls = []

    def pr_by_number(self, repo, number, cwd=None):
        return dict(self.pr)

    def dir_at(self, repo, path, ref):
        return {"ok": True, "names": [DIR.split("/")[1], "0008-other"]}

    def file_at(self, repo, path, ref):
        if path in self.files and self.files[path] is not None:
            return {"ok": True, "text": self.files[path], "missing": False}
        return {"ok": False, "text": None, "missing": True, "reason": "404"}

    def compare_commits(self, repo, base, head):
        self.calls.append(("compare", base, head))
        return dict(self.compare)

    def check_runs_on(self, repo, sha, name):
        return dict(self.checks)

    def pr_reviews(self, repo, number, cwd=None):
        return dict(self.reviews)

    def merge_pr(self, repo, number, sha, tok):
        self.calls.append(("merge", number, sha, tok))
        return dict(self.merged)

    def post_not_build_check(self, repo, sha, cwd=None):
        self.calls.append(("not-build", sha))
        return {"ok": True}


def env(tmp_path, data=None, name="workflow_dispatch", **extra) -> dict:
    event = tmp_path / "event.json"
    event.write_text(json.dumps(data or {}), encoding="utf-8")
    return {
        "GITHUB_EVENT_NAME": name,
        "GITHUB_EVENT_PATH": str(event),
        "GITHUB_REPOSITORY_OWNER": "owner",
        "DEFAULT_BRANCH": "main",
        "GITHUB_STEP_SUMMARY": str(tmp_path / "summary.md"),
        "SDLC_MERGE_TOKEN": "merge-app-token",
        **extra,
    }


def checkout(tmp_path) -> Path:
    root = tmp_path / "proj"
    root.mkdir(exist_ok=True)
    (root / "sdlc.yaml").write_text("profile: standard\n", encoding="utf-8")
    return root


# --- merge ------------------------------------------------------------------------------------
def test_the_owner_s_approval_merges_at_the_head_through_the_merge_app(tmp_path, capsys):
    gh = FakeGitHub()
    assert merge_step.merge(checkout(tmp_path), REPO, 12, env(tmp_path), gh) == 0
    assert ("merge", 12, HEAD, "merge-app-token") in gh.calls
    # the head rule: from the reviewed commit, and from the approved one (here the head)
    assert ("compare", REVIEWED, HEAD) in gh.calls
    out = capsys.readouterr().out
    assert "merge: approval: owner approved #12" in out
    assert "merge: merged #12 (0007)" in out and "0 Important" in out
    assert "merge: merged #12" in (tmp_path / "summary.md").read_text(encoding="utf-8")


def _waits(tmp_path, capsys, gh, why):
    assert merge_step.merge(checkout(tmp_path), REPO, 12, env(tmp_path), gh) == 0
    out = capsys.readouterr().out
    assert "merge: wait:" in out and why in out, out
    assert not [c for c in gh.calls if c[0] == "merge"]


def test_no_approval_by_the_owner_waits(tmp_path, capsys):
    reviews = {"ok": True, "reviews": [{"author": "someone", "state": "APPROVED", "commit": HEAD}]}
    _waits(tmp_path, capsys, FakeGitHub(reviews=reviews), "no approving review by the owner")
    # a later "Request changes" by the owner takes the approval back
    later = {
        "ok": True,
        "reviews": [
            {"author": "owner", "state": "APPROVED", "commit": HEAD},
            {"author": "owner", "state": "COMMENTED", "commit": HEAD},
            {"author": "owner", "state": "CHANGES_REQUESTED", "commit": HEAD},
        ],
    }
    _waits(tmp_path, capsys, FakeGitHub(reviews=later), "no approving review by the owner")
    # a [bot]'s approval never counts, even under the owner's name rule
    bot = {"ok": True, "reviews": [{"author": "owner[bot]", "state": "APPROVED", "commit": HEAD}]}
    _waits(tmp_path, capsys, FakeGitHub(reviews=bot), "no approving review by the owner")


def test_a_pr_that_is_not_a_ready_build_pr_waits(tmp_path, capsys):
    cases = [
        ({"state": "closed"}, "is not open"),
        ({"draft": True}, "is a draft"),
        ({"head_ref": "sdlc/0007/b"}, "is not a build PR"),
        ({"head_repo": "fork/app"}, "outside"),
        ({"base_ref": "dev"}, "is not into main"),
        ({"labels": ["sdlc:e-ready", "sdlc:needs-human"]}, "is parked"),
        ({"labels": ["sdlc:d-ready"]}, "does not carry sdlc:e-ready"),
    ]
    for pr, why in cases:
        _waits(tmp_path, capsys, FakeGitHub(pr=pr), why)


def test_gate_e_s_record_and_the_findings_must_say_green(tmp_path, capsys):
    findings = f"{DIR}/evidence/review-findings.json"
    gate = f"{DIR}/evidence/gate-e.json"
    status = f"{DIR}/status.yaml"
    cases = [
        ({status: status_text(phase="d")}, "not (e) passed"),
        (
            {status: status_text(
                parked_reason="the owner must decide",
                gate={"phase": "e", "result": "parked", "reason": "the owner must decide"},
            )},
            "gate e/parked",
        ),
        ({status: status_text(build_pr=13)}, "names build PR #13"),
        ({gate: None}, "gate-e.json is missing"),
        ({gate: json.dumps({"result": "park"})}, "recorded 'park'"),
        (
            {gate: json.dumps({"result": "wait", "checks": [
                {"name": "commands", "ok": True, "details": {"deferred": True}}]})},
            "still deferred",
        ),
        ({findings: None}, "review-findings.json is missing"),
        (
            {findings: json.dumps({"head": REVIEWED, "findings": [
                {"severity": "Important", "file": "a.py", "summary": "x"}]})},
            "Important finding",
        ),
    ]  # fmt: skip
    for files, why in cases:
        gh = FakeGitHub(files=files)
        assert merge_step.merge(checkout(tmp_path), REPO, 12, env(tmp_path), gh) == 0
        out = capsys.readouterr().out
        assert "merge: wait:" in out and why in out, (files, out)


def test_a_commit_after_the_review_that_is_not_evidence_waits(tmp_path, capsys):
    compare = {"ok": True, "status": "ahead", "files": [f"{DIR}/evidence/a.md", "src/app.py"]}
    _waits(tmp_path, capsys, FakeGitHub(compare=compare), "src/app.py")
    # an "Update branch" merge commit brings the default branch's files: refused (R51 row 6)
    compare = {"ok": True, "status": "diverged", "files": []}
    _waits(tmp_path, capsys, FakeGitHub(compare=compare), "does not follow")


def test_the_check_must_be_green_on_the_head(tmp_path, capsys):
    _waits(tmp_path, capsys, FakeGitHub(checks={"ok": True, "runs": []}), "no sdlc/review")
    red = {"ok": True, "runs": [{"conclusion": "failure"}]}
    _waits(tmp_path, capsys, FakeGitHub(checks=red), "not green")


def test_an_approval_on_an_older_head_counts_only_across_evidence(tmp_path, capsys):
    older = {"ok": True, "reviews": [{"author": "owner", "state": "APPROVED", "commit": "a" * 40}]}
    gh = FakeGitHub(reviews=older)
    assert merge_step.merge(checkout(tmp_path), REPO, 12, env(tmp_path), gh) == 0
    assert ("compare", "a" * 40, HEAD) in gh.calls and ("merge", 12, HEAD, "merge-app-token") in (
        gh.calls
    )
    capsys.readouterr()
    compare = {"ok": True, "status": "ahead", "files": ["src/app.py"]}
    gh = FakeGitHub(reviews=older, compare=compare)
    _waits(tmp_path, capsys, gh, "src/app.py")


def test_a_refused_merge_or_a_failed_read_is_red(tmp_path, capsys):
    gh = FakeGitHub(merged={"ok": False, "status": 405, "reason": "Repository rule violations"})
    assert merge_step.merge(checkout(tmp_path), REPO, 12, env(tmp_path), gh) == 1
    assert "refused (HTTP 405)" in capsys.readouterr().err
    gh = FakeGitHub(checks={"ok": False, "reason": "HTTP 403"})
    assert merge_step.merge(checkout(tmp_path), REPO, 12, env(tmp_path), gh) == 1
    # without the merge App's token nothing is merged, and the run says why
    gh = FakeGitHub()
    assert merge_step.merge(checkout(tmp_path), REPO, 12, env(tmp_path, SDLC_MERGE_TOKEN=""), gh)
    assert "SDLC_MERGE_TOKEN is empty" in capsys.readouterr().err
    assert not [c for c in gh.calls if c[0] == "merge"]


def test_allowed_after_review_is_evidence_status_and_the_seen_record():
    from review import findings as fmod

    for path in (f"{DIR}/evidence/run-e.json", f"{DIR}/status.yaml", "changes/.review-seen.json"):
        assert fmod.allowed_after_review(path, DIR)
    for path in (f"{DIR}/plan.md", f"{DIR}/spec.md", "src/app.py", "changes/0008-x/status.yaml"):
        assert not fmod.allowed_after_review(path, DIR)


# --- doorbell ---------------------------------------------------------------------------------
def review_payload(state="approved", login="owner", ref="sdlc/0007/c", head_repo=REPO):
    return {
        "action": "submitted",
        "review": {"state": state, "user": {"login": login}},
        "pull_request": {"number": 12, "head": {"ref": ref, "repo": {"full_name": head_repo}}},
        "repository": {"default_branch": "main"},
    }


def test_the_owner_s_approval_rings_the_merge(tmp_path, capsys):
    sent = []

    def send(*args):
        sent.append(args)
        return {"ok": True}

    e = env(tmp_path, review_payload(), name="pull_request_review")
    assert merge_step.doorbell(checkout(tmp_path), REPO, e, FakeGitHub(), send) == 0
    assert sent == [(REPO, "sdlc-merge.yml", "main", "0007", "sdlc/0007/c", {"pr": "12"})]
    assert "dispatched sdlc-merge.yml for #12" in capsys.readouterr().out


def test_any_other_review_rings_nothing(tmp_path, capsys):
    for data, why in (
        (review_payload(state="changes_requested"), "does not approve"),
        (review_payload(login="someone"), "not the owner's"),
        (review_payload(login="owner[bot]"), "not the owner's"),
        (review_payload(ref="sdlc/0007/b"), "not a build PR"),
        (review_payload(head_repo="fork/app"), "fork/app"),
    ):
        sent = []
        e = env(tmp_path, data, name="pull_request_review")
        code = merge_step.doorbell(checkout(tmp_path), REPO, e, FakeGitHub(), sent.append)
        assert code == 0 and sent == []
        assert why in capsys.readouterr().out
    failed = env(tmp_path, review_payload(), name="pull_request_review")
    code = merge_step.doorbell(
        checkout(tmp_path), REPO, failed, FakeGitHub(), lambda *a: {"ok": False, "status": 404}
    )
    assert code == 1


# --- not-build --------------------------------------------------------------------------------
def pull_payload(ref="feature/x", sha=HEAD, head_repo=REPO):
    return {"pull_request": {"head": {"ref": ref, "sha": sha, "repo": {"full_name": head_repo}}}}


def test_every_other_pull_request_gets_a_passing_check(tmp_path, capsys):
    gh = FakeGitHub()
    e = env(tmp_path, pull_payload(), name="pull_request")
    assert merge_step.not_build(checkout(tmp_path), REPO, e, gh) == 0
    assert gh.calls == [("not-build", HEAD)]
    for data in (pull_payload(ref="sdlc/0007/c"), pull_payload(head_repo="fork/app")):
        gh = FakeGitHub()
        e = env(tmp_path, data, name="pull_request")
        assert merge_step.not_build(checkout(tmp_path), REPO, e, gh) == 0
        assert gh.calls == []
    capsys.readouterr()


def test_the_check_is_posted_with_the_review_check_s_name(monkeypatch):
    from pr import github

    seen = []
    monkeypatch.setattr(github, "create_check_run", lambda *a, **k: seen.append(a) or {"ok": True})
    github.post_not_build_check(REPO, HEAD)
    assert seen == [
        (REPO, HEAD, "sdlc/review", "success", "not a build PR", github.NOT_BUILD_SUMMARY)
    ]
    from review import findings as fmod

    assert github.REVIEW_CHECK == fmod.CHECK_RUN_NAME


# --- the App is required (R60's answer, R22) ------------------------------------------------
def test_a_workflow_that_minted_no_app_token_stops_the_run():
    base = {"GITHUB_ACTIONS": "true", "SDLC_WORKFLOW_TOKEN": "wf", "GITHUB_REPOSITORY": REPO}
    why = app_token.app_missing(base)
    assert why and "SDLC_APP_ID" in why and f"github.com/{REPO}/settings" in why
    assert app_token.app_missing({**base, "SDLC_APP_TOKEN_MINTED_AT": "1792415878"}) is None
    # by hand, and in the workflows that mint no App token, nothing is judged
    assert app_token.app_missing({"SDLC_WORKFLOW_TOKEN": "wf"}) is None
    assert app_token.app_missing({"GITHUB_ACTIONS": "true"}) is None


def test_the_runner_refuses_a_phase_run_without_the_app(monkeypatch, capsys):
    from ci import run_phase

    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    monkeypatch.setenv("SDLC_WORKFLOW_TOKEN", "wf")
    monkeypatch.delenv("SDLC_APP_TOKEN_MINTED_AT", raising=False)
    monkeypatch.setattr(run_phase, "run_phase", lambda *a: (_ for _ in ()).throw(AssertionError))
    assert run_phase.main(["--phase", "c", "--id", "0007"]) == run_phase.EXIT_FAILED
    assert "GitHub App is required" in capsys.readouterr().err


# --- the (e) run: the check on the final head, and the merge offered ------------------------
def _offer_project(tmp_path):
    root = tmp_path / "proj"
    change = root / "changes" / "0007-dark-mode" / "evidence"
    change.mkdir(parents=True)
    (change / "review-findings.json").write_text("{}", encoding="utf-8")
    return root


class _Args:
    repo, ref, no_dispatch = REPO, "main", False


def test_the_e_run_posts_on_the_final_head_and_offers_the_merge(tmp_path, monkeypatch):
    from ci import run_phase

    root = _offer_project(tmp_path)
    calls, sent = [], []
    posted = {"route": "check-run", "conclusion": "success", "head": HEAD}
    monkeypatch.setattr(
        run_phase, "_cli_call", lambda script, argv, **k: calls.append(argv) or {"output": posted}
    )
    monkeypatch.setattr(run_phase, "dispatch", lambda *a: sent.append(a) or {"ok": True})
    out = run_phase.offer_merge(_Args(), tmp_path, root, "0007", {"result": "wait"}, {"number": 12})
    assert calls == [
        ["check-run", "--root", str(root), "--id", "0007", "--phase", "e", "--final-head"]
    ]
    assert sent == [(REPO, "sdlc-merge.yml", "main", "0007", "sdlc/0007/c", {"pr": "12"})]
    assert out["dispatched"] == {"ok": True}
    # a red check, or a gate (e) that does not wait for the owner, offers nothing
    for check, result in (({**posted, "conclusion": "failure"}, "wait"), (posted, "park")):
        sent.clear()
        monkeypatch.setattr(run_phase, "_cli_call", lambda *a, check=check, **k: {"output": check})
        out = run_phase.offer_merge(
            _Args(), tmp_path, root, "0007", {"result": result}, {"number": 12}
        )
        assert sent == [] and out["dispatched"] is None


def test_the_offer_needs_the_findings_file(tmp_path, monkeypatch):
    from ci import run_phase

    root = tmp_path / "proj"
    (root / "changes" / "0007-dark-mode").mkdir(parents=True)
    monkeypatch.setattr(
        run_phase, "_cli_call", lambda *a, **k: (_ for _ in ()).throw(AssertionError)
    )
    out = run_phase.offer_merge(_Args(), tmp_path, root, "0007", {"result": "wait"}, {"number": 12})
    assert out["posted"] is None


# --- the digest: an approved build PR the App has not merged --------------------------------
def test_the_digest_says_an_approved_build_pr_is_not_merged_and_why(monkeypatch):
    from pr import digest
    from pr import github as gh

    pr = {"number": 12, "labels": [{"name": "sdlc:e-ready"}], "head": {"sha": HEAD}, "title": "t"}
    reviews = {
        "ok": True,
        "reviews": [{"author": "owner", "state": "APPROVED", "at": "2026-10-21T"}],
    }
    monkeypatch.setattr(gh, "pr_reviews", lambda *a, **k: reviews)
    monkeypatch.setattr(gh, "check_runs_on", lambda *a, **k: {"ok": True, "runs": []})
    got = digest.approval_of("o/r", pr)
    assert got == {"at": "2026-10-21T", "reason": digest.NO_CHECK}
    assert "approved 2026-10-21, not merged: waiting for the sdlc/review" in digest._line(
        {**pr, "approval": got}
    )
    red = {"ok": True, "runs": [{"conclusion": "failure"}]}
    monkeypatch.setattr(gh, "check_runs_on", lambda *a, **k: red)
    assert digest.approval_of("o/r", pr)["reason"] == digest.RED_CHECK
    green = {"ok": True, "runs": [{"conclusion": "success"}]}
    monkeypatch.setattr(gh, "check_runs_on", lambda *a, **k: green)
    monkeypatch.setattr(gh, "token", lambda: "t")
    monkeypatch.setattr(
        gh, "_request", lambda *a, **k: {"data": {"mergeable_state": "dirty"}, "error": ""}
    )
    assert digest.approval_of("o/r", pr)["reason"] == digest.CONFLICT
    # not approved, or not at (e): no line
    monkeypatch.setattr(gh, "pr_reviews", lambda *a, **k: {"ok": True, "reviews": []})
    assert digest.approval_of("o/r", pr) is None
    assert digest.approval_of("o/r", {**pr, "labels": [{"name": "sdlc:b-ready"}]}) is None


# --- detect and scan file nothing without the App -------------------------------------------
def test_scan_files_nothing_without_the_app(tmp_path, monkeypatch, capsys):
    from scan import cli as scan_cli
    from scan import route as route_mod

    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    monkeypatch.setenv("SDLC_WORKFLOW_TOKEN", "wf")
    monkeypatch.delenv("SDLC_APP_TOKEN_MINTED_AT", raising=False)
    monkeypatch.setattr(scan_cli, "_head", lambda *a: HEAD)
    monkeypatch.setattr(
        route_mod, "load_findings", lambda *a: ({"findings": [{"x": 1}], "head": HEAD}, [])
    )
    monkeypatch.setattr(route_mod, "filed_signatures", lambda *a: set())
    monkeypatch.setattr(route_mod, "select", lambda *a, **k: ([{"x": 1}], []))
    monkeypatch.setattr(
        route_mod, "file_findings", lambda *a, **k: (_ for _ in ()).throw(AssertionError)
    )
    (tmp_path / "changes").mkdir()
    argv = ["route", "--root", str(tmp_path), "--findings", "f.json", "--repo", REPO]
    assert scan_cli.main(argv) == scan_cli.EXIT_FAILED
    out = json.loads(capsys.readouterr().out)
    assert any("GitHub App is required" in p for p in out["problems"])


def test_compare_lists_a_rename_s_old_path_too(monkeypatch):
    from pr import github

    monkeypatch.setattr(github, "token", lambda: "t")
    data = {
        "status": "ahead",
        "files": [
            {"filename": f"{DIR}/evidence/app.py", "previous_filename": "src/app.py"},
            {"filename": f"{DIR}/evidence/run-e.json"},
        ],
    }
    monkeypatch.setattr(github, "_request", lambda *a, **k: {"data": data, "error": ""})
    got = github.compare_commits(REPO, REVIEWED, HEAD)
    assert got["files"] == [f"{DIR}/evidence/app.py", "src/app.py", f"{DIR}/evidence/run-e.json"]
