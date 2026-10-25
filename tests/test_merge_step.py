"""Decision 36 (ROADMAP R22): gate (deploy) is the owner's approving review, and the merge App
merges on it (``plugin/ci/merge_step.py``, run by ``template/.github/workflows/sdlc-merge.yml``,
whose structure ``tests/test_templates.py`` checks). No model and no network: the GitHub
client and the dispatch are fakes, the event payload a file.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from ci import app_token, merge_step

from state import status as status_mod
from state import yamlish

REPO = "owner/app"
HEAD = "c" * 40
REVIEWED = "b" * 40
DIR = "changes/0007-dark-mode"


def status_text(**over) -> str:
    st = status_mod.Status.from_dict(
        {"id": "0007", "slug": "dark-mode", "title": "Dark mode", "phase": "deploy"}
    )
    st.record_gate("deploy", "passed", "waiting for the owner at gate (deploy)")
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
            "head_ref": "sdlc/0007/build",
            "head_sha": HEAD,
            "head_repo": REPO,
            "base_ref": "main",
            "labels": ["sdlc:deploy-ready"],
        }
        self.pr.update(over.pop("pr", {}))
        self.files = {
            f"{DIR}/status.yaml": status_text(),
            f"{DIR}/evidence/gate-deploy.json": json.dumps({"phase": "deploy", "result": "wait"}),
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


def test_a_change_in_flight_before_r45_merges_with_its_letters(tmp_path, capsys):
    """R45, for one release: a build PR an older plugin opened has the head ``sdlc/0007/c``,
    the label ``sdlc:e-ready``, ``phase: e`` in status.yaml and ``evidence/gate-e.json``;
    the merge step reads every one of them as deploy and merges."""
    letter = "e"
    letters = yamlish.dumps(
        {
            **yamlish.loads(status_text()),
            "phase": letter,
            "gate": {"phase": letter, "result": "passed", "reason": None, "at": None},
        }
    )
    gh = FakeGitHub(
        pr={"head_ref": "sdlc/0007/" + "c", "labels": ["sdlc:" + letter + "-ready"]},
        files={
            f"{DIR}/status.yaml": letters,
            f"{DIR}/evidence/gate-deploy.json": None,
            f"{DIR}/evidence/gate-{letter}.json": json.dumps({"result": "wait"}),
        },
    )
    assert merge_step.merge(checkout(tmp_path), REPO, 12, env(tmp_path), gh) == 0
    assert ("merge", 12, HEAD, "merge-app-token") in gh.calls, capsys.readouterr().out
    assert merge_step.build_change_id("sdlc/0007/" + "c") == "0007"
    assert merge_step.build_change_id("sdlc/0007/build") == "0007"
    assert merge_step.build_change_id("sdlc/0007/design") is None


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


def test_a_dismissed_approval_waits(tmp_path, capsys):
    """The R22 double check, F13: a dismissed review is the owner's latest decisive one, and
    it takes the approval back."""
    dismissed = {
        "ok": True,
        "reviews": [
            {"author": "owner", "state": "APPROVED", "commit": HEAD},
            {"author": "owner", "state": "DISMISSED", "commit": HEAD},
        ],
    }
    _waits(tmp_path, capsys, FakeGitHub(reviews=dismissed), "no approving review by the owner")


@pytest.mark.parametrize("status", ["diverged", "behind"])
def test_a_head_that_does_not_follow_the_approved_commit_waits(tmp_path, capsys, status):
    """The R22 double check, F13: a force-push or an "Update branch" after the approval
    leaves a head that does not follow the approved commit."""
    approved = "e" * 40

    class Moved(FakeGitHub):
        def compare_commits(self, repo, base, head):
            if base == approved:
                return {"ok": True, "status": status, "files": []}
            return super().compare_commits(repo, base, head)

    reviews = {
        "ok": True,
        "reviews": [{"author": "owner", "state": "APPROVED", "commit": approved}],
    }
    files = {f"{DIR}/evidence/gate-deploy.json": json.dumps({"phase": "deploy", "result": "wait"})}
    _waits(tmp_path, capsys, Moved(reviews=reviews, files=files), f"({status})")


@pytest.mark.parametrize("names", [["0008-other"], ["0007-a", "0007-b", "0008-other"]])
def test_no_single_change_folder_at_the_head_waits(tmp_path, capsys, names):
    """The R22 double check, F13: the change id must name exactly one folder at the head."""

    class Folders(FakeGitHub):
        def dir_at(self, repo, path, ref):
            return {"ok": True, "names": list(names)}

    found = len([n for n in names if n.startswith("0007-")])
    _waits(tmp_path, capsys, Folders(), f"has {found} folders for 0007")


def test_a_pr_that_is_not_a_ready_build_pr_waits(tmp_path, capsys):
    cases = [
        ({"state": "closed"}, "is not open"),
        ({"draft": True}, "is a draft"),
        ({"head_ref": "sdlc/0007/design"}, "is not a build PR"),
        ({"head_repo": "fork/app"}, "outside"),
        ({"base_ref": "dev"}, "is not into main"),
        ({"labels": ["sdlc:deploy-ready", "sdlc:needs-human"]}, "is parked"),
        ({"labels": ["sdlc:test-ready"]}, "does not carry sdlc:deploy-ready"),
    ]
    for pr, why in cases:
        _waits(tmp_path, capsys, FakeGitHub(pr=pr), why)


def test_gate_e_s_record_and_the_findings_must_say_green(tmp_path, capsys):
    findings = f"{DIR}/evidence/review-findings.json"
    gate = f"{DIR}/evidence/gate-deploy.json"
    status = f"{DIR}/status.yaml"
    cases = [
        ({status: status_text(phase="test")}, "not deploy passed"),
        (
            {status: status_text(
                parked_reason="the owner must decide",
                gate={"phase": "deploy", "result": "parked", "reason": "the owner must decide"},
            )},
            "gate deploy/parked",
        ),
        ({status: status_text(build_pr=13)}, "names build PR #13"),
        ({gate: None}, "gate-deploy.json is missing"),
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

    for path in (
        f"{DIR}/evidence/run-deploy.json",
        f"{DIR}/status.yaml",
        "changes/.review-seen.json",
    ):
        assert fmod.allowed_after_review(path, DIR)
    for path in (f"{DIR}/plan.md", f"{DIR}/spec.md", "src/app.py", "changes/0008-x/status.yaml"):
        assert not fmod.allowed_after_review(path, DIR)


# --- on-approval (doorbell before plugin 1.0.46, R45 row N5) ---------------------------------
def review_payload(state="approved", login="owner", ref="sdlc/0007/build", head_repo=REPO):
    return {
        "action": "submitted",
        "review": {"state": state, "user": {"login": login}},
        "pull_request": {"number": 12, "head": {"ref": ref, "repo": {"full_name": head_repo}}},
        "repository": {"default_branch": "main"},
    }


def test_the_owner_s_approval_dispatches_the_merge(tmp_path, capsys):
    sent = []

    def send(*args):
        sent.append(args)
        return {"ok": True}

    e = env(tmp_path, review_payload(), name="pull_request_review")
    assert merge_step.on_approval(checkout(tmp_path), REPO, e, FakeGitHub(), send) == 0
    assert sent == [(REPO, "sdlc-merge.yml", "main", "0007", "sdlc/0007/build", {"pr": "12"})]
    assert "on-approval: dispatched sdlc-merge.yml for #12" in capsys.readouterr().out


def test_any_other_review_dispatches_nothing(tmp_path, capsys):
    for data, why in (
        (review_payload(state="changes_requested"), "does not approve"),
        (review_payload(login="someone"), "not the owner's"),
        (review_payload(login="owner[bot]"), "not the owner's"),
        (review_payload(ref="sdlc/0007/design"), "not a build PR"),
        (review_payload(head_repo="fork/app"), "fork/app"),
    ):
        sent = []
        e = env(tmp_path, data, name="pull_request_review")
        code = merge_step.on_approval(checkout(tmp_path), REPO, e, FakeGitHub(), sent.append)
        assert code == 0 and sent == []
        assert why in capsys.readouterr().out
    failed = env(tmp_path, review_payload(), name="pull_request_review")
    code = merge_step.on_approval(
        checkout(tmp_path), REPO, failed, FakeGitHub(), lambda *a: {"ok": False, "status": 404}
    )
    assert code == 1


def test_the_old_doorbell_subcommand_still_runs_for_one_release(tmp_path, monkeypatch, capsys):
    """R45 row N5: an sdlc-merge.yml copy from before plugin 1.0.46 calls ``merge_step.py
    doorbell``; it runs on-approval, under the new log prefix."""
    from ci import run_phase  # noqa: PLC0415

    sent = []
    monkeypatch.setattr(run_phase, "dispatch", lambda *a: sent.append(a) or {"ok": True})
    for key, value in env(tmp_path, review_payload(), name="pull_request_review").items():
        monkeypatch.setenv(key, value)
    root = checkout(tmp_path)
    for cmd in ("doorbell", "on-approval"):
        assert merge_step.main([cmd, "--root", str(root), "--repo", REPO]) == 0
        out = capsys.readouterr().out
        assert "on-approval: dispatched sdlc-merge.yml for #12" in out
        assert "doorbell" not in out
    assert len(sent) == 2 and sent[0] == sent[1]
    assert merge_step.LINES[merge_step.ON_APPROVAL] == "on-approval"


# --- not-build --------------------------------------------------------------------------------
def pull_payload(ref="feature/x", sha=HEAD, head_repo=REPO):
    return {"pull_request": {"head": {"ref": ref, "sha": sha, "repo": {"full_name": head_repo}}}}


def test_every_other_pull_request_gets_a_passing_check(tmp_path, capsys):
    gh = FakeGitHub()
    e = env(tmp_path, pull_payload(), name="pull_request")
    assert merge_step.not_build(checkout(tmp_path), REPO, e, gh) == 0
    assert gh.calls == [("not-build", HEAD)]
    for data in (pull_payload(ref="sdlc/0007/build"), pull_payload(head_repo="fork/app")):
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
    assert run_phase.main(["--phase", "build", "--id", "0007"]) == run_phase.EXIT_FAILED
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
        ["check-run", "--root", str(root), "--id", "0007", "--phase", "deploy", "--final-head"]
    ]
    assert sent == [(REPO, "sdlc-merge.yml", "main", "0007", "sdlc/0007/build", {"pr": "12"})]
    assert out["dispatched"] == {"ok": True}
    # a red check, or a gate (deploy) that does not wait for the owner, offers nothing
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

    pr = {
        "number": 12,
        "labels": [{"name": "sdlc:deploy-ready"}],
        "head": {"sha": HEAD},
        "title": "t",
    }
    reviews = {
        "ok": True,
        "reviews": [{"author": "owner", "state": "APPROVED", "at": "2026-10-21T"}],
    }
    monkeypatch.setattr(gh, "pr_reviews", lambda *a, **k: reviews)
    monkeypatch.setattr(gh, "check_runs_on", lambda *a, **k: {"ok": True, "runs": []})
    monkeypatch.delenv("GITHUB_REPOSITORY_OWNER", raising=False)
    monkeypatch.delenv("GITHUB_REPOSITORY", raising=False)
    got = digest.approval_of("owner/r", pr)
    assert got == {"at": "2026-10-21T", "reason": digest.NO_CHECK}
    # a collaborator's approval is not the owner's: no line (decision 34)
    assert digest.approval_of("someone/r", pr) is None
    assert "approved 2026-10-21, not merged: waiting for the sdlc/review" in digest._line(
        {**pr, "approval": got}
    )
    red = {"ok": True, "runs": [{"conclusion": "failure"}]}
    monkeypatch.setattr(gh, "check_runs_on", lambda *a, **k: red)
    assert digest.approval_of("owner/r", pr)["reason"] == digest.RED_CHECK
    green = {"ok": True, "runs": [{"conclusion": "success"}]}
    monkeypatch.setattr(gh, "check_runs_on", lambda *a, **k: green)
    monkeypatch.setattr(gh, "token", lambda: "t")
    monkeypatch.setattr(
        gh, "_request", lambda *a, **k: {"data": {"mergeable_state": "dirty"}, "error": ""}
    )
    assert digest.approval_of("owner/r", pr)["reason"] == digest.CONFLICT
    monkeypatch.setattr(
        gh, "_request", lambda *a, **k: {"data": {"mergeable_state": "clean"}, "error": ""}
    )
    # R45 row N7: the mode without a merge App says what it is, not an option's label
    assert digest.approval_of("owner/r", pr)["reason"] == digest.NOT_YET
    assert "no merge App: merge it yourself" in digest.NOT_YET and "C1" not in digest.NOT_YET
    # not approved, or not at (e): no line
    monkeypatch.setattr(gh, "pr_reviews", lambda *a, **k: {"ok": True, "reviews": []})
    assert digest.approval_of("owner/r", pr) is None
    assert digest.approval_of("owner/r", {**pr, "labels": [{"name": "sdlc:design-ready"}]}) is None


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
            {"filename": f"{DIR}/evidence/run-deploy.json"},
        ],
    }
    monkeypatch.setattr(github, "_request", lambda *a, **k: {"data": data, "error": ""})
    got = github.compare_commits(REPO, REVIEWED, HEAD)
    assert got["files"] == [
        f"{DIR}/evidence/app.py",
        "src/app.py",
        f"{DIR}/evidence/run-deploy.json",
    ]


def test_an_approval_before_gate_e_waits_and_a_leftover_full_profile_is_not_read(tmp_path, capsys):
    """Choice 250 (the R22 double check, F3): an approval on a commit without gate (deploy)'s
    record was given before the owner could read the (e) banner and findings, so it is no
    gate (deploy) on any profile; the owner approves again. Decision 37 (1.0.21): a leftover
    ``profile: full`` changes nothing."""
    early = "a" * 40

    class Early(FakeGitHub):
        def file_at(self, repo, path, ref):
            if ref == early and path.endswith("gate-deploy.json"):
                return {"ok": False, "text": None, "missing": True, "reason": "404"}
            return super().file_at(repo, path, ref)

    approval = {
        "ok": True,
        "reviews": [{"author": "owner", "state": "APPROVED", "commit": early}],
    }
    _waits(tmp_path, capsys, Early(reviews=approval), "approval predates gate (deploy)")
    root = checkout(tmp_path)
    (root / "sdlc.yaml").write_text("profile: full\n", encoding="utf-8")
    gh = Early(reviews=approval)
    assert merge_step.merge(root, REPO, 12, env(tmp_path), gh) == 0
    assert not [c for c in gh.calls if c[0] == "merge"]
    # the same approval given again once (e) ran (its commit carries gate-deploy.json) merges
    again = {
        "ok": True,
        "reviews": [
            {"author": "owner", "state": "APPROVED", "commit": early},
            {"author": "owner", "state": "APPROVED", "commit": REVIEWED},
        ],
    }
    gh = Early(reviews=again)
    assert merge_step.merge(checkout(tmp_path), REPO, 12, env(tmp_path), gh) == 0
    assert [c for c in gh.calls if c[0] == "merge"]


def test_an_approval_on_an_escalated_gate_e_record_waits(tmp_path, capsys):
    """The review of the 1.0.22 diff (finding 6): a gate (deploy) record that did not offer the
    PR (an escalation, a park) is no offer, so an approval given on it does not count."""
    early = "a" * 40

    class Escalated(FakeGitHub):
        def file_at(self, repo, path, ref):
            if ref == early and path.endswith("gate-deploy.json"):
                text = json.dumps({"phase": "deploy", "result": "escalate"})
                return {"ok": True, "text": text, "missing": False}
            return super().file_at(repo, path, ref)

    approval = {"ok": True, "reviews": [{"author": "owner", "state": "APPROVED", "commit": early}]}
    _waits(tmp_path, capsys, Escalated(reviews=approval), "approval predates gate (deploy)")


def test_the_digest_asks_for_a_new_approval_when_it_predates_gate_e(monkeypatch):
    """The review of the 1.0.22 diff (finding 1): GitHub still shows the PR approved, so
    the digest's line says why the merge waits and what the owner does."""
    from pr import digest
    from pr import github as gh

    early = "a" * 40
    pr = {
        "number": 12, "labels": [{"name": "sdlc:deploy-ready"}], "title": "t",
        "head": {"sha": HEAD, "ref": "sdlc/0007/build"},
    }  # fmt: skip
    reviews = {"ok": True, "reviews": [{"author": "owner", "state": "APPROVED", "commit": early}]}
    gate = {"text": None}
    monkeypatch.setattr(gh, "pr_reviews", lambda *a, **k: reviews)
    monkeypatch.setattr(gh, "check_runs_on", lambda *a, **k: {"ok": True, "runs": []})
    monkeypatch.setattr(gh, "dir_at", lambda *a, **k: {"ok": True, "names": [DIR.split("/")[1]]})

    def file_at(repo, path, ref):
        # R45: the name's record first, then the letter's an older plugin wrote
        letter = f"{DIR}/evidence/gate-" + "e.json"
        assert path in (f"{DIR}/evidence/gate-deploy.json", letter)
        assert ref == early
        if gate["text"] is None or path == letter:
            return {"ok": False, "text": None, "missing": True, "reason": "404"}
        return {"ok": True, "text": gate["text"], "missing": False}

    monkeypatch.setattr(gh, "file_at", file_at)
    monkeypatch.delenv("GITHUB_REPOSITORY_OWNER", raising=False)
    monkeypatch.delenv("GITHUB_REPOSITORY", raising=False)
    assert digest.approval_of("owner/r", pr)["reason"] == digest.PREDATES_GATE_E
    gate["text"] = json.dumps({"result": "escalate"})
    assert digest.approval_of("owner/r", pr)["reason"] == digest.PREDATES_GATE_E
    gate["text"] = json.dumps({"result": "wait"})  # given once (e) offered the PR
    assert digest.approval_of("owner/r", pr)["reason"] == digest.NO_CHECK
    # a read that fails says nothing wrong: the line falls back to the check's state
    monkeypatch.setattr(gh, "dir_at", lambda *a, **k: {"ok": False, "names": [], "reason": "x"})
    gate["text"] = None
    assert digest.approval_of("owner/r", pr)["reason"] == digest.NO_CHECK


def test_findings_that_do_not_normalise_wait(tmp_path, capsys):
    bad = {f"{DIR}/evidence/review-findings.json": json.dumps({"head": REVIEWED, "findings": 3})}
    _waits(tmp_path, capsys, FakeGitHub(files=bad), "")


# --- the GitHub helpers ------------------------------------------------------------------------
def test_the_merge_step_s_github_helpers_shape_the_api(monkeypatch):
    import base64

    from pr import github

    monkeypatch.setattr(github, "token", lambda: "t")
    answers = {}

    def fake(method, url, tok, payload=None):
        answers.setdefault("calls", []).append((method, url, payload))
        for fragment, answer in answers.items():
            if fragment != "calls" and fragment in url:
                return answer
        return {"status": 404, "data": {"message": "Not Found"}, "error": "Not Found"}

    monkeypatch.setattr(github, "_request", fake)
    text = base64.b64encode(b"phase: deploy\n").decode()
    answers["/contents/a.yaml"] = {"status": 200, "data": {"type": "file", "content": text},
                                   "error": ""}  # fmt: skip
    assert github.file_at(REPO, "a.yaml", HEAD)["text"] == "phase: deploy\n"
    assert github.file_at(REPO, "b.yaml", HEAD)["missing"] is True
    answers["/contents/changes"] = {
        "status": 200,
        "error": "",
        "data": [{"name": "0007-dark-mode", "type": "dir"}, {"name": "README.md", "type": "file"}],
    }
    assert github.dir_at(REPO, "changes", HEAD)["names"] == ["0007-dark-mode"]
    answers["/check-runs?"] = {
        "status": 200,
        "error": "",
        "data": {
            "check_runs": [
                {"id": 1, "status": "completed", "conclusion": "success", "app": {"slug": "x"}}
            ]
        },
    }
    runs = github.check_runs_on(REPO, HEAD, "sdlc/review")
    assert runs["runs"] == [{"id": 1, "status": "completed", "conclusion": "success", "app": "x"}]
    assert "check_name=sdlc%2Freview" in answers["calls"][-1][1]
    answers["/compare/"] = {
        "status": 200,
        "error": "",
        "data": {"status": "ahead", "files": [{"filename": f"f{n}"} for n in range(300)]},
    }
    assert github.compare_commits(REPO, REVIEWED, HEAD)["ok"] is False
    answers["/pulls/12/merge"] = {"status": 405, "error": "Repository rule violations", "data": {}}
    assert github.merge_pr(REPO, 12, HEAD, "m") == {
        "ok": False,
        "sha": None,
        "status": 405,
        "reason": "Repository rule violations",
    }
    method, url, payload = answers["calls"][-1]
    assert method == "PUT" and payload == {"sha": HEAD, "merge_method": "merge"}
    assert github.merge_pr(REPO, 12, HEAD, "")["reason"] == "no merge token"
