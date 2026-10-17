"""Decision 34 (ROADMAP R17), the runner's half: only the owner's account starts a fix round
or approves gates (c) and (d) (``state/unpark.py is_owner_actor``, fail closed); the "Request
changes" path is refused in the find step for anyone else and for a fork's head; the round
records the ``@claude`` comment that started it; and a request an earlier round applied is
never applied twice.

The GitHub calls are replaced by fakes, as ``tests/test_ci.py`` does: no network, no token.
"""

from __future__ import annotations

import json

from ci import fix_requests, run_phase

from state import unpark
from tests import test_ci as ci_tests
from tests.test_ci import FAKE_TOKEN, Args, FixGitHub, set_state, skip_reason

# the fixture of tests/test_ci.py, used here by name
project = ci_tests.project

REVIEW_2, COMMENT_31 = {"kind": "review", "id": 2}, {"kind": "comment", "id": 31}
OWNER_ENV = {"GITHUB_REPOSITORY_OWNER": "luissiviero", "GITHUB_REPOSITORY": "luissiviero/app"}


# --- is_owner_actor -------------------------------------------------------------------------
def test_the_owner_is_the_repository_owner_on_a_personal_repository():
    assert unpark.owner_login({}, OWNER_ENV) == "luissiviero"
    assert unpark.is_owner_actor("luissiviero", {}, OWNER_ENV) is True
    assert unpark.is_owner_actor("colleague", {}, OWNER_ENV) is False
    # GITHUB_REPOSITORY alone names the owner too
    assert unpark.owner_login({}, {"GITHUB_REPOSITORY": "someone/app"}) == "someone"
    assert unpark.is_owner_actor("someone", {}, {"GITHUB_REPOSITORY": "someone/app"}) is True


def test_sdlc_yaml_owner_names_the_owner_and_wins_over_the_environment():
    """An organization repository names its owner in ``sdlc.yaml: owner``: the organization
    itself never comments, so without it nobody counts."""
    org = {"GITHUB_REPOSITORY_OWNER": "acme", "GITHUB_REPOSITORY": "acme/app"}
    assert unpark.is_owner_actor("alice", {}, org) is False
    assert unpark.owner_login({"owner": "alice"}, org) == "alice"
    assert unpark.is_owner_actor("alice", {"owner": "alice"}, org) is True
    assert unpark.is_owner_actor("acme", {"owner": "alice"}, org) is False
    # an empty or non-string owner key falls back to the environment
    assert unpark.owner_login({"owner": "  "}, org) == "acme"
    assert unpark.owner_login({"owner": ["alice"]}, org) == "acme"


def test_the_owner_comparison_ignores_case_and_surrounding_spaces():
    assert unpark.is_owner_actor(" LuisSiviero ", {}, OWNER_ENV) is True
    assert unpark.is_owner_actor("ALICE", {"owner": " alice "}, {}) is True


def test_a_bot_or_the_automation_identity_is_never_the_owner_even_when_named():
    assert unpark.is_owner_actor("github-actions[bot]", {"owner": "github-actions[bot]"}, {}) is (
        False
    )
    named = {"owner": "sdlc-bot", "automation_identity": ["sdlc-bot"]}
    assert unpark.is_owner_actor("sdlc-bot", named, {}) is False
    assert unpark.is_owner_actor("renovate[bot]", {}, {"GITHUB_REPOSITORY_OWNER": "x"}) is False


def test_an_empty_actor_or_an_unknown_owner_is_refused():
    assert unpark.is_owner_actor("", {}, OWNER_ENV) is False
    assert unpark.is_owner_actor(None, {}, OWNER_ENV) is False
    assert unpark.owner_login({}, {}) is None
    assert unpark.owner_login({}, {"GITHUB_REPOSITORY": "no-slash"}) is None
    assert unpark.is_owner_actor("luissiviero", {}, {}) is False


def test_the_owner_is_read_from_os_environ_by_default(monkeypatch):
    monkeypatch.setenv("GITHUB_REPOSITORY_OWNER", "luissiviero")
    assert unpark.is_owner_actor("luissiviero", {}) is True


# --- gates (c) and (d): the label counts only from the owner's account -----------------------
def _full_profile_with_label(root, change, monkeypatch, actor: str):
    from pr import github

    text = (root / "sdlc.yaml").read_text(encoding="utf-8")
    (root / "sdlc.yaml").write_text(text.replace("profile: standard", "profile: full"), "utf-8")
    set_state(change, "c", gate_phase="c", gate_result="passed")
    monkeypatch.setattr(github, "gh_path", lambda: None)
    monkeypatch.setattr(github, "token", lambda: FAKE_TOKEN)
    monkeypatch.setattr(
        github, "find_open_pr", lambda repo, head: {"number": 7, "labels": ["sdlc:c-approved"]}
    )
    events = [{"event": "labeled", "label": {"name": "sdlc:c-approved"}, "actor": {"login": actor}}]
    monkeypatch.setattr(
        github, "_request", lambda method, url, tok, payload=None: {
            "status": 200, "data": events, "error": ""
        },
    )  # fmt: skip
    return events


def test_an_approval_label_applied_by_a_collaborator_does_not_start_the_next_phase(
    project, monkeypatch
):
    """Decision 34 amends 27: a person who is not the owner's account no longer approves
    gate (c) or (d); the run skips with the label, the PR and the actor in its reason."""
    root, change = project
    events = _full_profile_with_label(root, change, monkeypatch, "colleague")
    env = {"GITHUB_TOKEN": FAKE_TOKEN, **OWNER_ENV}
    assert skip_reason(root, "d", env) == (
        "sdlc:c-approved on PR #7 was applied by colleague, not by the owner's account "
        "(decision 34)"
    )
    events[0]["actor"]["login"] = "luissiviero"
    assert skip_reason(root, "d", env) is None
    # with no owner known at all, nobody approves (fail closed)
    assert "not by the owner's account" in skip_reason(root, "d", {"GITHUB_TOKEN": FAKE_TOKEN})


def test_an_organization_repository_s_owner_key_names_the_approver(project, monkeypatch):
    root, change = project
    _full_profile_with_label(root, change, monkeypatch, "alice")
    org = {"GITHUB_TOKEN": FAKE_TOKEN, "GITHUB_REPOSITORY_OWNER": "acme"}
    assert "applied by alice, not by the owner's account" in skip_reason(root, "d", org)
    text = (root / "sdlc.yaml").read_text(encoding="utf-8")
    (root / "sdlc.yaml").write_text(text + "\nowner: alice\n", "utf-8")
    assert skip_reason(root, "d", org) is None
    set_state(change, "d", gate_phase="d", gate_result="passed")
    # gate (d)'s label is read for the deploy run: the same rule
    from pr import github

    monkeypatch.setattr(
        github, "find_open_pr", lambda repo, head: {"number": 7, "labels": ["sdlc:d-approved"]}
    )
    events = [{"event": "labeled", "label": {"name": "sdlc:d-approved"}, "actor": {"login": "x"}}]
    monkeypatch.setattr(
        github, "_request", lambda method, url, tok, payload=None: {
            "status": 200, "data": events, "error": ""
        },
    )  # fmt: skip
    assert "applied by x, not by the owner's account" in skip_reason(root, "e", org)
    events[0]["actor"]["login"] = "Alice"
    assert skip_reason(root, "e", org) is None


# --- the "Request changes" path: the find step refuses all but the owner's own head -----------
def _review_event(tmp_path, login: str, head_repo: str | None, name="event.json"):
    head = {"ref": "sdlc/0001/b", "repo": {"full_name": head_repo} if head_repo else None}
    payload = {
        "action": "submitted",
        "review": {"state": "changes_requested", "user": {"login": login}},
        "pull_request": {"number": 7, "head": head},
    }
    path = tmp_path / name
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def _find(root, tmp_path, env, capsys, **kw):
    output = tmp_path / "github-output"
    output.write_text("", encoding="utf-8")
    args = Args(root=str(root), phase="fix", head_ref="sdlc/0001/b", pr_number="7", **kw)
    args.id = kw.get("id")
    args.find_change = True
    capsys.readouterr()
    code = run_phase.print_found_change(args, {**env, "GITHUB_OUTPUT": str(output)})
    printed = capsys.readouterr().out
    return code, printed, output.read_text(encoding="utf-8")


def test_a_collaborator_s_request_changes_review_starts_no_round(project, tmp_path, capsys):
    root, _change = project
    event = _review_event(tmp_path, "colleague", "owner/name")
    env = {**OWNER_ENV, "GITHUB_EVENT_NAME": "pull_request_review", "GITHUB_EVENT_PATH": str(event)}
    code, printed, output = _find(root, tmp_path, env, capsys)
    assert code == run_phase.EXIT_OK  # a skip, not a park: the run ends green
    assert output == "change_id=\n"
    assert "change_id=\n" in printed
    assert "the review is by colleague, not the owner's account (decision 34)" in printed


def test_the_owner_s_review_on_the_repository_s_own_head_finds_the_change(
    project, tmp_path, capsys
):
    root, _change = project
    event = _review_event(tmp_path, "LuisSiviero", "owner/name")
    env = {**OWNER_ENV, "GITHUB_EVENT_NAME": "pull_request_review", "GITHUB_EVENT_PATH": str(event)}
    code, printed, output = _find(root, tmp_path, env, capsys)
    assert code == run_phase.EXIT_OK and output == "change_id=0001\n"


def test_a_review_on_a_fork_s_head_is_refused_even_from_the_owner(project, tmp_path, capsys):
    root, _change = project
    for head_repo in ("someone/name", None):
        event = _review_event(tmp_path, "luissiviero", head_repo)
        env = {
            **OWNER_ENV,
            "GITHUB_EVENT_NAME": "pull_request_review",
            "GITHUB_EVENT_PATH": str(event),
        }
        code, printed, output = _find(root, tmp_path, env, capsys)
        assert code == run_phase.EXIT_OK and output == "change_id=\n", head_repo
        assert "a fork's head never starts a round" in printed


def test_a_review_event_without_a_readable_payload_is_refused(project, tmp_path, capsys):
    root, _change = project
    base = {**OWNER_ENV, "GITHUB_EVENT_NAME": "pull_request_review"}
    for env in (
        base,
        {**base, "GITHUB_EVENT_PATH": str(tmp_path / "missing.json")},
    ):
        code, printed, output = _find(root, tmp_path, env, capsys)
        assert code == run_phase.EXIT_OK and output == "change_id=\n"
        assert "payload could not be read" in printed
    broken = tmp_path / "broken.json"
    broken.write_text("{not json", encoding="utf-8")
    code, printed, output = _find(
        root, tmp_path, {**base, "GITHUB_EVENT_PATH": str(broken)}, capsys
    )
    assert output == "change_id=\n" and "payload could not be read" in printed


def test_a_dispatch_and_a_label_event_are_not_judged_by_the_review_rule(project, tmp_path, capsys):
    """The owner's dispatch, the runner's own round (decision 29), the comment dispatcher's
    dispatch (actor github-actions[bot]) and the un-park labels keep their path."""
    root, _change = project
    for event_name in ("workflow_dispatch", "pull_request"):
        env = {"GITHUB_EVENT_NAME": event_name}  # no payload, no owner known: not read
        code, _printed, output = _find(root, tmp_path, env, capsys, id="0001")
        assert code == run_phase.EXIT_OK and output == "change_id=0001\n", event_name
    assert run_phase.review_refusal(root, "owner/name", {}) is None


# --- the round's trigger and the requests no round applies twice ----------------------------
def _gh_with_requests() -> FixGitHub:
    gh = FixGitHub()
    gh.reviews["reviews"] = [
        {"id": 2, "author": "luissiviero", "type": "User", "association": "OWNER",
         "state": "COMMENTED", "body": "the comment review", "at": "t", "url": "u2"},
    ]  # fmt: skip
    gh.threads["threads"] = [
        {"id": "T1", "resolved": False, "outdated": False, "path": "src/a.py", "line": 7,
         "comments": [
             {"id": 11, "author": "luissiviero", "type": "User", "association": "OWNER",
              "body": "rename this", "at": "t", "url": "u11"},
             {"id": 31, "author": "luissiviero", "type": "User", "association": "OWNER",
              "body": "same id as the PR comment", "at": "t", "url": "u31t"}]},
    ]  # fmt: skip
    gh.comments["comments"] = [
        {"id": 31, "author": "luissiviero", "type": "User", "association": "OWNER",
         "body": "@claude fix the docs", "at": "t", "url": "u31"},
        {"id": 32, "author": "luissiviero", "type": "User", "association": "OWNER",
         "body": "and the changelog", "at": "t", "url": "u32"},
    ]  # fmt: skip
    return gh


def _round(change, gh, trigger=None) -> dict:
    fix_requests.collect_and_write(change, "o/r", 7, gh, {}, "abc", trigger=trigger)
    return json.loads((change / "evidence" / "fix-requests.json").read_text(encoding="utf-8"))


def _mark_applied(change, wanted: set) -> None:
    """What /sdlc-fix step 6 does: ``"applied": true`` on each request it applied."""
    path = change / "evidence" / "fix-requests.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    for entry in data["requests"]:
        if (entry["kind"], entry["id"]) in wanted:
            entry["applied"] = True
    path.write_text(json.dumps(data), encoding="utf-8")


def test_a_request_an_earlier_round_applied_is_not_applied_again(project):
    """Decision 34, point 6: a PR comment cannot be resolved and a comment review cannot be
    dismissed; the marked ids are carried from round to round, threads keep their own rule."""
    _root, change = project
    gh = _gh_with_requests()
    first = _round(change, gh)
    assert first["applied_earlier"] == []  # the first round reads everything
    assert [(r["kind"], r["id"]) for r in first["requests"]] == [
        ("review", 2), ("review_comment", 11), ("review_comment", 31), ("comment", 31),
        ("comment", 32),
    ]  # fmt: skip
    # round 1 applied the review, the PR comment 31 and the thread comment 11; not 32
    _mark_applied(change, {("review", 2), ("comment", 31), ("review_comment", 11)})
    second = _round(change, gh)
    assert second["applied_earlier"] == [COMMENT_31, REVIEW_2]
    assert [(r["kind"], r["id"]) for r in second["requests"]] == [
        ("review_comment", 11),  # an unresolved thread stays a request: threads are not carried
        ("review_comment", 31),  # a thread comment is never carried, whatever its id
        ("comment", 32),  # an earlier round did not mark it: still a request
    ]
    skipped = [(r["kind"], r["id"], r["why"], r["body"]) for r in second["not_applied"]]
    assert skipped == [
        ("review", 2, fix_requests.APPLIED_EARLIER, None),
        ("comment", 31, fix_requests.APPLIED_EARLIER, None),
    ]
    assert "@claude fix the docs" not in json.dumps(second)  # listed without its text
    assert second["not_applied"][1]["chars"] == len("@claude fix the docs")
    # round 2 marks nothing; round 3 still skips 2 and 31 through applied_earlier
    third = _round(change, gh)
    assert third["applied_earlier"] == [COMMENT_31, REVIEW_2]
    assert [r["id"] for r in third["not_applied"]] == [2, 31]
    assert fix_requests.APPLIED_EARLIER == "not applied: applied by an earlier round"


def test_a_corrupt_earlier_requests_file_carries_nothing(project):
    _root, change = project
    path = change / "evidence" / "fix-requests.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    for text in ("{not json", "[1, 2]", '{"applied_earlier": "31", "requests": "x"}'):
        path.write_text(text, encoding="utf-8")
        data = _round(change, _gh_with_requests())
        assert data["applied_earlier"] == [] and len(data["requests"]) == 5, text
    assert fix_requests.applied_earlier(change / "nowhere") == []


def test_the_round_records_the_comment_that_started_it(project, monkeypatch, capsys):
    """Part 5: the dispatcher's ``trigger`` input reaches the runner as ``SDLC_TRIGGER`` and is
    written into the file once; a round started any other way says null. An unavailable
    collection keeps the carried ids too."""
    _root, change = project
    root = _root
    gh = _gh_with_requests()
    monkeypatch.setattr(run_phase, "_github", lambda: gh)
    link = "https://github.com/owner/name/pull/7#issuecomment-31"
    env = {"GITHUB_TOKEN": FAKE_TOKEN, "SDLC_TRIGGER": link}
    capsys.readouterr()
    out = run_phase.collect_fix_requests(root, change, {}, "owner/name", "7", env)
    assert out["ok"] is True
    assert capsys.readouterr().err.count(link) == 1
    path = change / "evidence" / "fix-requests.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["trigger"] == link
    _mark_applied(change, {("comment", 31)})
    run_phase.collect_fix_requests(root, change, {}, "owner/name", "7", {"GITHUB_TOKEN": "t"})
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["trigger"] is None and data["applied_earlier"] == [COMMENT_31]
    # no route: the file says unavailable and still carries what earlier rounds applied
    out = run_phase.collect_fix_requests(
        root, change, {}, "owner/name", "7", {"SDLC_TRIGGER": link}
    )
    data = json.loads(path.read_text(encoding="utf-8"))
    assert out["ok"] is False and data["unavailable"] == out["unavailable"]
    assert data["applied_earlier"] == [COMMENT_31] and data["trigger"] == link


# --- the dispatch carries extra inputs without changing the existing call ----------------------
def test_dispatch_adds_extra_inputs_and_keeps_the_two_it_always_sends(monkeypatch):
    from pr import github

    sent = []
    monkeypatch.setattr(github, "token", lambda: FAKE_TOKEN)
    monkeypatch.setattr(
        github,
        "_request",
        lambda method, url, tok, payload=None: sent.append((url, payload)) or {"status": 204},
    )
    assert run_phase.dispatch("o/r", "sdlc-fix.yml", "main", "0001", "sdlc/0001/c")["ok"]
    assert sent[-1][1] == {
        "ref": "main",
        "inputs": {"change_id": "0001", "head_ref": "sdlc/0001/c"},
    }
    extra = {"trigger": "https://x/1", "change_id": "9999"}
    assert run_phase.dispatch("o/r", "sdlc-fix.yml", "main", "0001", "sdlc/0001/c", extra)["ok"]
    assert sent[-1][0].endswith("/repos/o/r/actions/workflows/sdlc-fix.yml/dispatches")
    assert sent[-1][1]["inputs"] == {
        "change_id": "0001",  # never overridden by an extra input
        "head_ref": "sdlc/0001/c",
        "trigger": "https://x/1",
    }


# --- the review round's fix: a request is carried by its kind and id ------------------------
def test_a_carried_comment_id_does_not_skip_a_review_with_the_same_id(project):
    """Review ids and comment ids come from separate sequences: a PR comment applied earlier
    never hides a review that happens to share its number."""
    _root, change = project
    gh = _gh_with_requests()
    _round(change, gh)
    _mark_applied(change, {("comment", 31)})
    gh.reviews["reviews"].append(
        {"id": 31, "author": "luissiviero", "type": "User", "association": "OWNER",
         "state": "COMMENTED", "body": "a review numbered 31", "at": "t", "url": "u-r31"}
    )  # fmt: skip
    data = _round(change, gh)
    assert data["applied_earlier"] == [COMMENT_31]
    assert ("review", 31) in [(r["kind"], r["id"]) for r in data["requests"]]
    assert [(r["kind"], r["id"]) for r in data["not_applied"]] == [("comment", 31)]
    # an earlier file in the first round's id-only shape carries nothing
    path = change / "evidence" / "fix-requests.json"
    path.write_text(json.dumps({"applied_earlier": [31, "2"], "requests": []}), "utf-8")
    assert fix_requests.applied_earlier(change) == []


# --- the trigger is a comment link of this repository, or nothing ---------------------------
def test_a_trigger_that_is_not_this_repository_s_comment_link_is_dropped_unprinted(
    project, monkeypatch, capsys
):
    _root, change = project
    monkeypatch.setattr(run_phase, "_github", lambda: _gh_with_requests())
    path = change / "evidence" / "fix-requests.json"
    for bad in (
        "https://github.com/other/repo/pull/7#issuecomment-31",
        "https://github.com/owner/name/pull/7",
        "::warning::forged https://github.com/owner/name/pull/7#issuecomment-31",
        "https://github.com/owner/name/pull/7#issuecomment-31\n::set-output name=x::y",
        "javascript:alert(1)",
    ):
        env = {"GITHUB_TOKEN": FAKE_TOKEN, "SDLC_TRIGGER": bad}
        capsys.readouterr()
        run_phase.collect_fix_requests(_root, change, {}, "owner/name", "7", env)
        err = capsys.readouterr().err
        assert bad not in err and "::" not in err and "other/repo" not in err, bad
        assert "the trigger input is not a comment link" in err
        assert json.loads(path.read_text(encoding="utf-8"))["trigger"] is None
    good = "https://github.com/Owner/Name/pull/7#issuecomment-31"
    assert fix_requests.trigger_link(good, "owner/name") == good
    assert fix_requests.trigger_link(good, "") is None


# --- the session may only mark what it applied ------------------------------------------------
def _session_edit(change, edit) -> None:
    path = change / "evidence" / "fix-requests.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    edit(data)
    path.write_text(json.dumps(data, indent=4), encoding="utf-8")


def test_the_session_s_applied_marks_are_kept_and_nothing_else(project):
    _root, change = project
    gh = _gh_with_requests()
    before = _round(change, gh)
    snap = fix_requests.snapshot(change)
    assert snap == before

    def legit(data):  # step 6: marks on a review and a PR comment, reformatted
        for entry in data["requests"]:
            if (entry["kind"], entry["id"]) in {("review", 2), ("comment", 32)}:
                entry["applied"] = True

    _session_edit(change, legit)
    assert fix_requests.keep_marks_only(change, snap) is None
    marked = json.loads((change / "evidence" / "fix-requests.json").read_text("utf-8"))
    assert [(r["kind"], r["id"]) for r in marked["requests"] if r.get("applied")] == [
        ("review", 2),
        ("comment", 32),
    ]

    def forged(data):
        legit(data)
        data["applied_earlier"] = [{"kind": "comment", "id": 31}]  # hides the @claude ask
        data["requests"] = [r for r in data["requests"] if r["id"] != 11]  # drops a thread
        data["requests"][0]["body"] = "rewritten"
        for entry in data["requests"]:
            if entry["kind"] == "review_comment":
                entry["applied"] = True  # a thread is never marked
        data["requests"].append({"kind": "comment", "id": 99, "applied": True})

    _session_edit(change, forged)
    line = fix_requests.keep_marks_only(change, snap)
    assert line == (
        "evidence/fix-requests.json: the session changed more than the applied marks; the "
        "runner's copy is restored with 2 mark(s) kept (decision 34)"
    )
    restored = json.loads((change / "evidence" / "fix-requests.json").read_text("utf-8"))
    expected = json.loads(json.dumps(snap))
    for entry in expected["requests"]:
        if (entry["kind"], entry["id"]) in {("review", 2), ("comment", 32)}:
            entry["applied"] = True
    assert restored == expected
    # a deleted or broken file comes back too
    (change / "evidence" / "fix-requests.json").write_text("{broken", encoding="utf-8")
    assert fix_requests.keep_marks_only(change, snap)
    assert fix_requests.snapshot(change) == snap
    assert fix_requests.keep_marks_only(change, None) is None  # nothing written before


def test_the_fix_round_restores_a_forged_requests_file_after_the_session(
    project, tmp_path, monkeypatch, capsys
):
    """The runner snapshots the file it wrote before the session and, after the session and
    before anything is committed, keeps only the session's legitimate marks."""
    import os

    root, change = project
    order = ci_tests._fix_round(root, change, tmp_path, monkeypatch)
    gh = _gh_with_requests()
    monkeypatch.setattr(run_phase, "_github", lambda: gh)
    path = change / "evidence" / "fix-requests.json"

    def session(argv, root_, env, timeout):
        order.append("invoke")
        data = json.loads(path.read_text(encoding="utf-8"))
        for entry in data["requests"]:
            if (entry["kind"], entry["id"]) == ("comment", 32):
                entry["applied"] = True
        data["applied_earlier"] = [{"kind": "comment", "id": 31}]
        path.write_text(json.dumps(data), encoding="utf-8")
        return (None, "", "boom", 1)

    monkeypatch.setattr(run_phase, "invoke", session)
    args = Args(root=str(root), phase="fix", head_ref="sdlc/0001/b", pr_number="7", dry_run=False)
    env = dict(os.environ, **ci_tests.KEY_ENV, GITHUB_TOKEN=FAKE_TOKEN)
    env.pop("GITHUB_ACTIONS", None)
    capsys.readouterr()
    assert run_phase.run_phase(args, env) == run_phase.EXIT_FAILED  # the fake session failed
    assert "invoke" in order
    assert "the session changed more than the applied marks" in capsys.readouterr().err
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["applied_earlier"] == []
    assert [(r["kind"], r["id"]) for r in data["requests"] if r.get("applied")] == [("comment", 32)]


# --- the owner check reads the default branch's sdlc.yaml, never the head's --------------------
def _head_names_its_own_owner(root, tmp_path):
    ci_tests.with_remote(root, tmp_path)  # main carries sdlc.yaml without an owner key
    ci_tests.git(root, "checkout", "-q", "-b", "sdlc/0001/b")
    text = (root / "sdlc.yaml").read_text(encoding="utf-8")
    (root / "sdlc.yaml").write_text(text + "\nowner: colleague\n", "utf-8")
    ci_tests.git(root, "commit", "-q", "-am", "the head names its own owner")


def test_a_head_s_owner_key_is_ignored_by_the_review_check(project, tmp_path, capsys):
    root, _change = project
    _head_names_its_own_owner(root, tmp_path)
    event = _review_event(tmp_path, "colleague", "owner/name")
    env = {
        **OWNER_ENV,
        "GITHUB_ACTIONS": "true",
        "GITHUB_EVENT_NAME": "pull_request_review",
        "GITHUB_EVENT_PATH": str(event),
    }
    _code, printed, output = _find(root, tmp_path, env, capsys)
    assert output == "change_id=\n"
    assert "the review is by colleague, not the owner's account" in printed


def test_on_a_runner_without_the_default_branch_s_copy_the_owner_is_not_judged(
    project, tmp_path, capsys, monkeypatch
):
    """No remote-tracking ref: ``_approved_config`` would read the checkout's copy, the PR
    head's on a review run. On a runner the owner check refuses instead; by hand it reads
    the checkout as before."""
    root, change = project
    text = (root / "sdlc.yaml").read_text(encoding="utf-8")
    (root / "sdlc.yaml").write_text(text + "\nowner: colleague\n", "utf-8")
    event = _review_event(tmp_path, "colleague", "owner/name")
    review = {"GITHUB_EVENT_NAME": "pull_request_review", "GITHUB_EVENT_PATH": str(event)}
    _code, printed, output = _find(root, tmp_path, {**review, "GITHUB_ACTIONS": "true"}, capsys)
    assert output == "change_id=\n"
    assert "the review cannot be judged: " + run_phase.OWNER_COPY_MISSING in printed
    _code, _printed, output = _find(root, tmp_path, review, capsys)
    assert output == "change_id=0001\n"  # by hand: the checkout's copy is the owner's
    # the (c)/(d) label is judged the same way
    (root / "sdlc.yaml").write_text(text, "utf-8")
    _full_profile_with_label(root, change, monkeypatch, "luissiviero")
    env = {"GITHUB_TOKEN": FAKE_TOKEN, "GITHUB_ACTIONS": "true", **OWNER_ENV}
    reason = run_phase.check_approval(root, "owner/name", "0001", "d", env)
    assert reason == f"sdlc:c-approved on PR #7 cannot be judged: {run_phase.OWNER_COPY_MISSING}"


def test_an_unreadable_sdlc_yaml_refuses_the_review_and_the_label(
    project, tmp_path, capsys, monkeypatch
):
    root, change = project
    _full_profile_with_label(root, change, monkeypatch, "luissiviero")
    (root / "sdlc.yaml").write_text("profile: full\n  max_turns: 5\n", "utf-8")
    env = {"GITHUB_TOKEN": FAKE_TOKEN, **OWNER_ENV}
    reason = run_phase.check_approval(root, "owner/name", "0001", "d", env)
    assert reason.startswith("sdlc:c-approved on PR #7 cannot be judged: sdlc.yaml")
    event = _review_event(tmp_path, "luissiviero", "owner/name")
    review = {**OWNER_ENV, "GITHUB_EVENT_NAME": "pull_request_review"}
    _code, printed, output = _find(
        root, tmp_path, {**review, "GITHUB_EVENT_PATH": str(event)}, capsys
    )
    assert output == "change_id=\n" and "the review cannot be judged: sdlc.yaml" in printed


def test_the_owner_falls_back_to_the_repository_the_caller_names():
    assert unpark.owner_login({}, {}, "luissiviero/app") == "luissiviero"
    assert unpark.owner_login({}, {"GITHUB_REPOSITORY_OWNER": "x"}, "luissiviero/app") == "x"
    assert unpark.owner_login({"owner": "alice"}, {}, "luissiviero/app") == "alice"
    assert unpark.is_owner_actor("luissiviero", {}, {}, "luissiviero/app") is True
    assert unpark.is_owner_actor("luissiviero", {}, {}, "no-slash") is False
