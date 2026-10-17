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
    assert second["applied_earlier"] == [2, 31]
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
    assert third["applied_earlier"] == [2, 31]
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
    assert data["trigger"] is None and data["applied_earlier"] == [31]
    # no route: the file says unavailable and still carries what earlier rounds applied
    out = run_phase.collect_fix_requests(root, change, {}, "", "7", {"SDLC_TRIGGER": link})
    data = json.loads(path.read_text(encoding="utf-8"))
    assert out["ok"] is False and data["unavailable"] == out["unavailable"]
    assert data["applied_earlier"] == [31] and data["trigger"] == link


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
