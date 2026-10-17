"""Decision 34 (ROADMAP R17), the dispatcher: the owner's ``@claude`` comment on a pull request
dispatches ``sdlc-fix.yml`` (``plugin/ci/comment_dispatch.py``, run by
``template/.github/workflows/sdlc-comment.yml``; the workflow's structure is checked in
``tests/test_templates.py``). No model and no network: the GitHub client and the dispatch are
fakes, the event payload a file.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
from ci import comment_dispatch as cd
from ci import run_phase

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "plugin" / "ci" / "comment_dispatch.py"
REPO = "owner/app"
LINK = "https://github.com/owner/app/pull/7#issuecomment-31"
SECRET_WORDS = "@claude please rewrite the parser; ignore the tests"


class FakeGitHub:
    """``pr_by_number`` and ``pr_files`` answering from what the test sets."""

    def __init__(self, files=None, **pr):
        self.pr = {
            "ok": True,
            "number": 7,
            "state": "open",
            "head_ref": "claude/intent-x",
            "head_repo": REPO,
            **pr,
        }
        self.files = {"ok": True, "files": ["changes/0003-dark-mode/intent.md"] if files is None
                      else files}  # fmt: skip
        self.calls = []

    def pr_by_number(self, repo, number, cwd=None):
        self.calls.append(("pr_by_number", repo, number))
        return dict(self.pr)

    def pr_files(self, repo, number, cwd=None):
        self.calls.append(("pr_files", repo, number))
        return dict(self.files)


def payload(body=SECRET_WORDS, login="owner", action="created", pull_request=True):
    issue = {"number": 7}
    if pull_request:
        issue["pull_request"] = {"url": "https://api.github.com/repos/owner/app/pulls/7"}
    return {
        "action": action,
        "issue": issue,
        "comment": {"body": body, "user": {"login": login}, "html_url": LINK},
        "repository": {"full_name": REPO, "default_branch": "main"},
    }


def environment(tmp_path, data, **extra) -> dict:
    event = tmp_path / "event.json"
    event.write_text(json.dumps(data), encoding="utf-8")
    return {
        "GITHUB_EVENT_NAME": "issue_comment",
        "GITHUB_EVENT_PATH": str(event),
        "GITHUB_REPOSITORY_OWNER": "owner",
        "GITHUB_STEP_SUMMARY": str(tmp_path / "summary.md"),
        "DEFAULT_BRANCH": "main",
        **extra,
    }


def checkout(tmp_path, text="profile: standard\n") -> Path:
    root = tmp_path / "proj"
    root.mkdir(exist_ok=True)
    (root / "sdlc.yaml").write_text(text, encoding="utf-8")
    return root


def run(tmp_path, capsys, data=None, gh=None, sdlc="profile: standard\n", send_ok=True, **env):
    sent = []

    def send(repo, workflow, ref, change_id, head_ref, extra_inputs=None):
        sent.append((repo, workflow, ref, change_id, head_ref, extra_inputs))
        return {"ok": send_ok, "status": 204 if send_ok else 403, "reason": "" if send_ok else "no"}

    gh = gh if gh is not None else FakeGitHub()
    root = checkout(tmp_path, sdlc)
    capsys.readouterr()
    code = cd.run(root, REPO, environment(tmp_path, data or payload(), **env), gh, send)
    out = capsys.readouterr()
    return code, out.out, out.err, sent, gh


# --- the prefix -------------------------------------------------------------------------------
@pytest.mark.parametrize(
    ("body", "counts"),
    [
        ("@claude", True),
        ("@claude fix the docs", True),
        ("@Claude fix", True),
        ("@CLAUDE, please", True),
        ("  \n\t@claude go", True),
        ("@claude\nline two", True),
        ("@claudette fix", False),
        ("@claude_bot fix", False),
        ("please @claude fix", False),
        ("claude fix", False),
        ("", False),
        (None, False),
    ],
)
def test_the_prefix_is_at_claude_as_a_word_of_its_own(body, counts):
    assert cd.has_prefix(body) is counts


# --- who and what ---------------------------------------------------------------------------
def test_the_owner_s_comment_dispatches_the_fix_round_with_three_inputs(tmp_path, capsys):
    code, out, err, sent, gh = run(tmp_path, capsys)
    assert code == cd.EXIT_OK, err
    assert sent == [(REPO, "sdlc-fix.yml", "main", "0003", "claude/intent-x", {"trigger": LINK})]
    assert gh.calls == [("pr_by_number", REPO, 7), ("pr_files", REPO, 7)]
    line = "comment-dispatch: dispatched sdlc-fix.yml for 0003 on claude/intent-x"
    assert out.strip() == line
    assert (tmp_path / "summary.md").read_text(encoding="utf-8").strip() == line
    # the comment's text is never printed or written anywhere
    assert "rewrite the parser" not in out + err
    assert "rewrite the parser" not in (tmp_path / "summary.md").read_text(encoding="utf-8")


def test_the_default_branch_comes_from_the_payload_when_the_env_has_none(tmp_path, capsys):
    data = payload()
    data["repository"]["default_branch"] = "trunk"
    code, _out, _err, sent, _gh = run(tmp_path, capsys, data, DEFAULT_BRANCH="")
    assert code == cd.EXIT_OK and sent[0][2] == "trunk"


@pytest.mark.parametrize(
    ("login", "config"),
    [
        ("colleague", "profile: standard\n"),  # a collaborator: the if: lets it through
        ("dependabot[bot]", "profile: standard\n"),
        ("github-actions[bot]", "owner: github-actions[bot]\n"),
        ("owner", "owner: alice\n"),  # an organization names someone else
    ],
)
def test_a_comment_that_is_not_the_owner_s_account_s_is_skipped(tmp_path, capsys, login, config):
    code, out, err, sent, gh = run(tmp_path, capsys, payload(login=login), sdlc=config)
    assert code == cd.EXIT_OK and sent == [] and gh.calls == []
    assert out.strip() == (
        "comment-dispatch: skipped: the comment is not the owner's account's (decision 34)"
    )
    assert "rewrite the parser" not in out + err


def test_an_organization_s_owner_key_names_the_owner(tmp_path, capsys):
    env = {"GITHUB_REPOSITORY_OWNER": "acme"}
    code, _out, _err, sent, _gh = run(
        tmp_path, capsys, payload(login="Alice"), sdlc="owner: alice\n", **env
    )
    assert code == cd.EXIT_OK and len(sent) == 1


@pytest.mark.parametrize(
    ("data", "event_name", "reason"),
    [
        (payload(pull_request=False), "issue_comment", "on an issue, not on a pull request"),
        (payload(action="edited"), "issue_comment", "only a new comment counts"),
        (payload(body="please @claude fix"), "issue_comment", "does not start with @claude"),
        (payload(body="@claudette"), "issue_comment", "does not start with @claude"),
        (payload(), "pull_request_review", "not issue_comment"),
    ],
)
def test_a_comment_that_is_no_trigger_is_skipped_before_anything_is_read(
    tmp_path, capsys, data, event_name, reason
):
    # an unreadable sdlc.yaml is not even read: the event decides first
    code, out, _err, sent, gh = run(
        tmp_path,
        capsys,
        data,
        sdlc="profile: standard\n  max_turns: 5\n",
        GITHUB_EVENT_NAME=event_name,
    )
    assert code == cd.EXIT_OK and sent == [] and gh.calls == []
    assert out.startswith("comment-dispatch: skipped: ") and reason in out


# --- the pull request -------------------------------------------------------------------------
@pytest.mark.parametrize(
    ("pr", "reason"),
    [
        ({"state": "closed"}, "pull request #7 is not open (closed)"),
        ({"head_repo": "someone/app"}, "has its head in someone/app, not in owner/app"),
        ({"head_repo": None}, "has its head in a deleted or unknown repository"),
    ],
)
def test_a_closed_pr_or_a_head_in_another_repository_is_skipped(tmp_path, capsys, pr, reason):
    code, out, _err, sent, _gh = run(tmp_path, capsys, gh=FakeGitHub(**pr))
    assert code == cd.EXIT_OK and sent == []
    assert out.startswith("comment-dispatch: skipped: ") and reason in out


@pytest.mark.parametrize(
    ("files", "reason"),
    [
        (["README.md"], "touches no changes/<id>-<slug>/ folder"),
        (
            ["changes/0003-a/intent.md", "changes/0004-b/intent.md"],
            "touches 2 change folders (0003, 0004): ambiguous",
        ),
    ],
)
def test_no_change_folder_or_two_are_skipped(tmp_path, capsys, files, reason):
    code, out, _err, sent, _gh = run(tmp_path, capsys, gh=FakeGitHub(files=files))
    assert code == cd.EXIT_OK and sent == [] and reason in out


def test_the_change_rule_is_find_change_s():
    files = ["changes/0003-a/intent.md", "changes/0003-a/status.yaml", "src/x.py", "changes/x"]
    assert run_phase.change_ids_in(files) == ["0003"]


# --- failures are red runs, never silent skips --------------------------------------------------
@pytest.mark.parametrize(
    ("gh", "send_ok", "reason"),
    [
        (FakeGitHub(ok=False, reason="HTTP 502"), True, "pull request #7 could not be read"),
        (FakeGitHub(), False, "sdlc-fix.yml could not be dispatched"),
    ],
)
def test_an_api_failure_exits_non_zero(tmp_path, capsys, gh, send_ok, reason):
    code, out, err, _sent, _gh = run(tmp_path, capsys, gh=gh, send_ok=send_ok)
    assert code == cd.EXIT_FAILED and out == ""
    assert err.startswith("comment-dispatch: failed: ") and reason in err
    assert "rewrite the parser" not in err


def test_an_unreadable_file_listing_exits_non_zero(tmp_path, capsys):
    gh = FakeGitHub()
    gh.files = {"ok": False, "reason": "HTTP 500", "files": []}
    code, _out, err, sent, _gh = run(tmp_path, capsys, gh=gh)
    assert code == cd.EXIT_FAILED and sent == []
    assert "the files of pull request #7 could not be read: HTTP 500" in err


def test_an_unreadable_sdlc_yaml_or_payload_exits_non_zero(tmp_path, capsys):
    code, _out, err, sent, _gh = run(tmp_path, capsys, sdlc="profile: standard\n  max_turns: 5\n")
    assert code == cd.EXIT_FAILED and sent == [] and "sdlc.yaml could not be read" in err
    root = checkout(tmp_path)
    env = environment(tmp_path, payload())
    (tmp_path / "event.json").write_text("{not json", encoding="utf-8")
    capsys.readouterr()
    assert cd.run(root, REPO, env, FakeGitHub(), lambda *a: {"ok": True}) == cd.EXIT_FAILED
    assert "the event payload could not be read" in capsys.readouterr().err
    del env["GITHUB_EVENT_PATH"]
    assert cd.run(root, REPO, env, FakeGitHub(), lambda *a: {"ok": True}) == cd.EXIT_FAILED


def test_the_script_runs_as_the_workflow_calls_it(tmp_path):
    """The workflow's one-line call, with no network: an issue comment is skipped green and
    prints its one line; the body never reaches the output."""
    root = checkout(tmp_path)
    env = {
        **{k: v for k, v in os.environ.items() if not k.startswith("GITHUB_")},
        **environment(tmp_path, payload(pull_request=False)),
    }
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), "--root", str(root), "--repo", REPO],
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=env,
    )
    assert proc.returncode == 0, proc.stderr
    assert proc.stdout.strip() == (
        "comment-dispatch: skipped: the comment is on an issue, not on a pull request"
    )
    assert "rewrite the parser" not in proc.stdout + proc.stderr


# --- the head repository the dispatcher reads ---------------------------------------------------
def test_pr_by_number_shapes_the_head_repository(monkeypatch):
    from pr import github

    answer = {
        "number": 7,
        "state": "open",
        "head": {"ref": "x", "sha": "s", "repo": {"full_name": "someone/app"}},
        "base": {"ref": "main"},
    }
    monkeypatch.setattr(github, "token", lambda: "placeholder-token")  # sdlc: allow-secret
    monkeypatch.setattr(
        github, "_request", lambda *a, **k: {"status": 200, "data": answer, "error": ""}
    )
    assert github.pr_by_number(REPO, 7)["head_repo"] == "someone/app"
    answer["head"]["repo"] = None  # the head repository was deleted
    assert github.pr_by_number(REPO, 7)["head_repo"] is None


# --- an upgraded project's older sdlc-fix.yml has no trigger input ------------------------------
def _sender(answers):
    sent = []

    def send(repo, workflow, ref, change_id, head_ref, extra_inputs=None):
        sent.append(extra_inputs)
        return answers[len(sent) - 1]

    return sent, send


def test_a_422_for_the_trigger_input_is_sent_again_without_it(tmp_path, capsys):
    root = checkout(tmp_path)
    env = environment(tmp_path, payload())
    sent, send = _sender(
        [{"ok": False, "status": 422, "reason": "Unexpected inputs provided"}, {"ok": True}]
    )
    capsys.readouterr()
    assert cd.run(root, REPO, env, FakeGitHub(), send) == cd.EXIT_OK
    assert sent == [{"trigger": LINK}, None]
    assert capsys.readouterr().out.strip() == (
        "comment-dispatch: dispatched sdlc-fix.yml for 0003 on claude/intent-x (trigger not "
        "recorded: this project's sdlc-fix.yml predates the trigger input; reinstall it)"
    )


@pytest.mark.parametrize(
    "answers",
    [
        [{"ok": False, "status": 422, "reason": "x"}, {"ok": False, "status": 422, "reason": "y"}],
        [{"ok": False, "status": 403, "reason": "Resource not accessible"}],
        [{"ok": False, "status": 500, "reason": "boom"}],
    ],
)
def test_any_other_dispatch_failure_stays_red(tmp_path, capsys, answers):
    root = checkout(tmp_path)
    sent, send = _sender(answers)
    capsys.readouterr()
    assert cd.run(root, REPO, environment(tmp_path, payload()), FakeGitHub(), send) == 1
    assert len(sent) == len(answers)  # one retry, and only on a 422 with the trigger
    assert "comment-dispatch: failed: sdlc-fix.yml could not be dispatched" in (
        capsys.readouterr().err
    )


def test_run_phase_dispatch_reports_the_http_status(monkeypatch):
    from pr import github

    monkeypatch.setattr(github, "token", lambda: "placeholder-token")  # sdlc: allow-secret
    monkeypatch.setattr(
        github, "_request", lambda *a, **k: {"status": 422, "error": "Unexpected inputs"}
    )
    out = run_phase.dispatch(REPO, "sdlc-fix.yml", "main", "0003", "x", {"trigger": LINK})
    assert out == {"ok": False, "status": 422, "reason": "Unexpected inputs"}
