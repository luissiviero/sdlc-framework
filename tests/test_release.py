"""Release tooling of gate (e) (build guide steps 29 and 32; decision 13): the approval
function, the release notes and the release workflow's step, against tmp git repositories and
an in-memory GitHub."""

from __future__ import annotations

import inspect
import json
import subprocess
import sys
from pathlib import Path

import pytest
from release import approval, cli, notes

from state import status

RELEASE = Path(__file__).resolve().parents[1] / "plugin" / "release"


def _git(root: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=root, capture_output=True, text=True, check=True
    ).stdout


INTENT = """# Intent: Export the claims report

Author: owner
Status: approved
Change id: 0001
Entry route: idea

## Problem
Nobody can export the report.

## Proposed outcome
Owners download the claims report as CSV. Later we add more formats.

## Affected users and systems
Owners.

## Constraints
None.

## Open questions
None.
"""


def gate_record(deferred: bool) -> dict:
    """A gate (e) record as the deploy run leaves it: the commands check run by the runner
    after the session (0.3.0), or still deferred (the job died before the runner's step)."""
    details = {"deferred": True} if deferred else {"ran_by": "runner", "deferred": False}
    return {
        "phase": "e",
        "result": "wait",
        "checks": [{"name": "commands", "ok": True, "reason": "x", "details": details}],
    }


def _repo_with_change(
    tmp_path: Path,
    phase: str = "e",
    sdlc_yaml: str | None = None,
    gate_result: str | None = "passed",
    parked: str | None = None,
):
    """A git repo: main holds change 0001; sdlc/0001/c carries two more commits. At phase e
    the merged copy carries gate (e)'s result as the deploy run leaves it (``gate_result``
    None leaves the gate as a merge before the run's gate does; ``parked`` is the reason a
    parked gate (e) recorded)."""
    root = tmp_path
    change_dir, st = status.new_change(root, "Export the claims report")
    (change_dir / "intent.md").write_text(INTENT, encoding="utf-8")
    (change_dir / "plan.md").write_text("# Plan\n", encoding="utf-8")
    if phase != "a":
        st.set_phase(phase)
        if phase == "e" and parked:
            st.park(parked)
        elif phase == "e" and gate_result:
            st.record_gate("e", gate_result, "waiting for the owner at gate (e)")
        if phase == "e" and (parked or gate_result):
            (change_dir / "evidence" / "gate-e.json").write_text(
                json.dumps(gate_record(deferred=False)) + "\n", encoding="utf-8"
            )
        status.write_status(change_dir, st)
    (root / "sdlc.yaml").write_text(
        sdlc_yaml or "deploy:\n  action: none\n  production: false\n", encoding="utf-8"
    )
    _git(root, "init", "-q", "-b", "main")
    _git(root, "config", "user.email", "t@example.com")
    _git(root, "config", "user.name", "t")
    _git(root, "config", "commit.gpgsign", "false")
    _git(root, "add", ".")
    _git(root, "commit", "-q", "-m", "init")
    _git(root, "checkout", "-q", "-b", "sdlc/0001/c")
    (root / "report.py").write_text("x = 1\n", encoding="utf-8")
    _git(root, "add", "report.py")
    _git(root, "commit", "-q", "-m", "Add the CSV export")
    (root / "report.py").write_text("x = 2\n", encoding="utf-8")
    _git(root, "add", "report.py")
    _git(root, "commit", "-q", "-m", "Handle empty reports")
    return root, change_dir


# --- release notes (32.2) --------------------------------------------------------------------
def test_notes_are_deterministic_and_list_commits_and_links(tmp_path):
    root, change_dir = _repo_with_change(tmp_path)
    first = notes.build_notes(root, "0001", base="main")
    assert first == notes.build_notes(root, "0001", base="main")
    assert first.startswith("# Release notes — change 0001: Export the claims report\n")
    assert "## What changed\n\nOwners download the claims report as CSV.\n" in first
    body = first.split("## Commits", 1)[1].split("## Evidence", 1)[0]
    subjects = [line.split(" ", 2)[2] for line in body.splitlines() if line.startswith("- ")]
    assert subjects == ["Add the CSV export", "Handle empty reports"]
    assert "[intent.md](../intent.md)" in first and "[plan.md](../plan.md)" in first
    assert "spec.md" not in first.split("## Links", 1)[1]  # no spec.md in the folder
    assert "no review-findings.json" in first
    assert "test missing" in first  # the evidence status line of the PR summary


def test_notes_leave_out_evidence_only_commits(tmp_path):
    """M1: the commit that stores the notes (or any other evidence-only commit) is not listed,
    so writing the notes does not change them; a commit that also touches code still is."""
    root, change_dir = _repo_with_change(tmp_path)
    notes.write_notes(root, "0001", base="main")
    _git(root, "add", "changes")
    _git(root, "commit", "-q", "-m", "Store the release notes")
    (change_dir / "evidence" / "gate-e.json").write_text("{}\n", encoding="utf-8")
    (root / "report.py").write_text("x = 3\n", encoding="utf-8")
    _git(root, "add", ".")
    _git(root, "commit", "-q", "-m", "Code and evidence together")
    text = notes.build_notes(root, "0001", base="main")
    assert "Store the release notes" not in text
    body = text.split("## Commits", 1)[1].split("## Evidence", 1)[0]
    subjects = [line.split(" ", 2)[2] for line in body.splitlines() if line.startswith("- ")]
    assert subjects == ["Add the CSV export", "Handle empty reports", "Code and evidence together"]


def test_notes_tally_the_review_findings(tmp_path):
    root, change_dir = _repo_with_change(tmp_path)
    findings = {
        "findings": [
            {"severity": "important", "summary": "a"},
            {"severity": "nit", "summary": "b"},
            {"severity": "nit", "summary": "c"},
        ]
    }
    (change_dir / "evidence" / "review-findings.json").write_text(
        json.dumps(findings), encoding="utf-8"
    )
    assert "1 Important, 2 nits" in notes.build_notes(root, "0001", base="main")


def test_notes_without_git_history(tmp_path):
    change_dir, _ = status.new_change(tmp_path, "No repo here")
    text = notes.build_notes(tmp_path, "0001")
    assert notes.NO_HISTORY in text and "# Release notes — change 0001: No repo here" in text


def test_notes_write_stores_the_file_in_the_evidence(tmp_path, capsys):
    root, change_dir = _repo_with_change(tmp_path)
    code = notes.main(["--root", str(root), "--id", "0001", "--base", "main", "--write"])
    assert code == 0
    path = change_dir / "evidence" / "release-notes.md"
    assert Path(capsys.readouterr().out.strip()) == path
    raw = path.read_bytes()
    assert b"\r\n" not in raw
    assert raw.decode("utf-8") == notes.build_notes(root, "0001", base="main")


def test_notes_cli_prints_and_refuses_an_unknown_change(tmp_path):
    root, _ = _repo_with_change(tmp_path)
    proc = subprocess.run(
        [sys.executable, str(RELEASE / "notes.py"), "--root", str(root), "--id", "0001"],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert proc.returncode == 0 and proc.stdout.startswith("# Release notes — change 0001")
    assert notes.main(["--root", str(root), "--id", "0009"]) == 2


# --- approval (29.1) -------------------------------------------------------------------------
class FakeGitHub:
    def __init__(
        self,
        actor="owner-login",
        ok=True,
        merged=True,
        files=("changes/0001-export-the-claims-report/status.yaml", "report.py"),
        labels=("sdlc:release-approved",),
        head_ref="sdlc/0001/c",
    ):
        self.actor, self.ok, self.merged = actor, ok, merged
        self.files, self.labels, self.head_ref = list(files), list(labels), head_ref

    def find_pr(self, repo, head, state="open", cwd=None):
        return {"ok": self.ok, "number": 7, "labels": self.labels, "reason": "down"}

    def label_actor(self, repo, number, label):
        if not self.ok:
            return {"ok": False, "actor": None, "reason": "api: HTTP 502"}
        return {"ok": True, "actor": self.actor, "reason": ""}

    def pr_files(self, repo, number, cwd=None):
        return {"ok": True, "files": self.files, "route": "api", "reason": ""}

    def pr_by_number(self, repo, number, cwd=None):
        if not self.ok:
            return {"ok": False, "number": None, "reason": "down"}
        return {
            "ok": True,
            "number": number,
            "merged": self.merged,
            "state": "closed" if self.merged else "open",
            "merge_commit_sha": "abc1234def" if self.merged else None,
            "head_sha": "abc1234def",
            "labels": self.labels,
            "head_ref": self.head_ref,
            "base_ref": "main",
            "reason": "",
        }


def _recorded(root: Path, number: int | None = 7) -> Path:
    """Change 0001 whose status.yaml records ``number`` as its build PR (``pr/cli.py
    upsert`` writes it, 0.2.27): the approval is read from that PR and no other."""
    change_dir, st = status.new_change(root, "Export the claims report")
    st.build_pr = number
    status.write_status(change_dir, st)
    return change_dir


def fake_git(tags=(), verify_ok=False):
    def git(root, *args):
        if args[:2] == ("rev-parse", "--abbrev-ref"):
            return 0, "sdlc/0001/c\n"
        if args == ("rev-parse", "HEAD"):
            return 0, "abc1234def\n"
        if args[:2] == ("remote", "get-url"):
            return 0, "git@github.com:o/r.git\n"
        if args[:2] == ("tag", "--points-at"):
            return 0, "".join(f"{t}\n" for t in tags)
        if args[0] == "verify-tag":
            return (0 if verify_ok else 1), ""
        return 1, ""

    return git


def test_approval_by_the_label_of_a_person(tmp_path):
    _recorded(tmp_path)
    a = approval.release_approval(tmp_path, {}, {}, git=fake_git(), github=FakeGitHub())
    assert a.approved and a.how == "label" and a.pr_number == 7
    assert a.detail == "label applied by owner-login"


@pytest.mark.parametrize("actor", ["github-actions[bot]", "dependabot[bot]", "ci-user"])
def test_approval_refuses_the_label_of_the_automation_identity(tmp_path, actor):
    config = {"automation_identity": ["ci-user"]} if actor == "ci-user" else {}
    _recorded(tmp_path)
    a = approval.release_approval(
        tmp_path, config, {}, git=fake_git(), github=FakeGitHub(actor=actor)
    )
    assert not a.approved and actor in a.detail


def test_a_signed_tag_is_never_an_approval(tmp_path):
    """B1 (decision 5): a session allowed git can sign a tag itself, so a verified signed
    tag on the merge commit no longer approves; the label is the only route."""
    calls = []
    _recorded(tmp_path)
    base = fake_git(tags=("v1.0.0",), verify_ok=True)

    def git(root, *args):
        calls.append(args)
        return base(root, *args)

    a = approval.release_approval(tmp_path, {}, {}, git=git, github=FakeGitHub(actor=None))
    assert not a.approved and a.how == "none"
    assert a.detail == "label sdlc:release-approved is not on #7"
    assert not any(c[0] in ("tag", "verify-tag") for c in calls)  # no tag is even looked at
    assert "merge_sha" not in inspect.signature(approval.release_approval).parameters
    assert not hasattr(approval, "tag_approval")


def test_no_approval_explains_the_label_route(tmp_path):
    _recorded(tmp_path)
    a = approval.release_approval(
        tmp_path, {}, {}, git=fake_git(tags=("v1",)), github=FakeGitHub(ok=False)
    )
    assert not a.approved and a.how == "none"
    assert a.detail.startswith("cannot verify the label")
    assert "tag" not in a.detail


def test_approval_never_reads_an_environment_variable(tmp_path):
    env = {"RELEASE_APPROVAL": "yes", "SDLC_RELEASE_APPROVED": "1"}
    _recorded(tmp_path)
    a = approval.release_approval(tmp_path, {}, env, git=fake_git(), github=FakeGitHub(actor=None))
    assert not a.approved


def test_the_approval_is_the_recorded_build_pr_not_the_branch_name(tmp_path):
    """The readiness review's group B (0.2.27): the PR used to be "the most recent one from
    the current branch's name", merged or not, so a checkout of any ``sdlc/<id>/c`` — a
    local branch with any content — inherited that change's label. Now the PR is the one
    ``status.yaml`` records, it must be the change's own build PR, and the checkout must be
    its head (open) or its merge commit (merged)."""
    git = fake_git()
    # no record: a branch name alone finds nothing
    _recorded(tmp_path, number=None)
    a = approval.release_approval(tmp_path, {}, {}, git=git, github=FakeGitHub())
    assert not a.approved and "records no build pull request" in a.detail
    change_dir = tmp_path / "changes" / "0001-export-the-claims-report"
    st = status.read_status(change_dir)
    st.build_pr = 7
    status.write_status(change_dir, st)
    # the recorded PR is read by number, and its head must be this change's build branch
    other = FakeGitHub(head_ref="sdlc/0002/c")
    a = approval.release_approval(tmp_path, {}, {}, git=git, github=other)
    assert not a.approved and "#7 (head sdlc/0002/c) is not the build PR sdlc/0001/c" in a.detail
    # closed without a merge: void
    gone = FakeGitHub(merged=False)
    gone.pr_by_number = lambda repo, number, cwd=None: {
        "ok": True, "number": number, "merged": False, "state": "closed", "head_sha": "abc1234def",
        "merge_commit_sha": None, "labels": ["sdlc:release-approved"], "head_ref": "sdlc/0001/c",
    }  # fmt: skip
    a = approval.release_approval(tmp_path, {}, {}, git=git, github=gone)
    assert not a.approved and "closed without a merge" in a.detail
    # open, but the checkout is not the PR's head (a local commit on top): refused
    moved = FakeGitHub(merged=False)
    base = moved.pr_by_number
    moved.pr_by_number = lambda *a, **k: {**base(*a, **k), "head_sha": "fedcba9876"}
    a = approval.release_approval(tmp_path, {}, {}, git=git, github=moved)
    assert not a.approved and "only the pull request's own head carries its approval" in a.detail
    # open at the PR's head: approved; merged with the checkout at the merge commit: approved
    a = approval.release_approval(tmp_path, {}, {}, git=git, github=FakeGitHub(merged=False))
    assert a.approved and a.pr_number == 7
    a = approval.release_approval(tmp_path, {}, {}, git=git, github=FakeGitHub(merged=True))
    assert a.approved and a.pr_number == 7
    # merged, with the checkout on the PR's own head (the by-hand deploy on sdlc/<id>/c
    # after the owner's merge; the review of the 0.2.27 diff, M3): approved
    at_head = FakeGitHub(merged=True)
    base_pr = at_head.pr_by_number
    at_head.pr_by_number = lambda *a, **k: {**base_pr(*a, **k), "merge_commit_sha": "9999999999"}
    a = approval.release_approval(tmp_path, {}, {}, git=git, github=at_head)
    assert a.approved and a.pr_number == 7
    # merged, but the checkout is elsewhere (a rebuilt local branch): refused
    elsewhere = fake_git()

    def moved(root, *args):
        return (0, "0000000000\n") if args == ("rev-parse", "HEAD") else elsewhere(root, *args)

    a = approval.release_approval(tmp_path, {}, {}, git=moved, github=FakeGitHub())
    assert not a.approved and "only the merged commit and the pull request's own head" in a.detail
    # the change id the caller resolved wins over the branch name
    _recorded_2 = status.new_change(tmp_path, "Another change")
    a = approval.release_approval(tmp_path, {}, {}, git=git, github=FakeGitHub(), change_id="0002")
    assert not a.approved and "change 0002 records no build pull request" in a.detail
    assert not hasattr(approval, "_find_pr")


def test_approval_on_a_real_repo_with_a_tag_but_no_label(tmp_path):
    root, _ = _repo_with_change(tmp_path)
    _git(root, "tag", "v1.0.0")  # a tag on HEAD changes nothing
    a = approval.release_approval(root, {}, {}, repo="o/r", pr_number=3, github=FakeGitHub(None))
    assert not a.approved and a.detail == "label sdlc:release-approved is not on #3"


# --- the release workflow's step (32.3) --------------------------------------------------------
def _run(root, github, *extra, env=None, git=None, record_git=None):
    """The ``run`` verb. The approval's git is the fake unless given; the remote record is
    read with the real git (the test repositories without a remote read as "no origin")."""
    lines: list[str] = []
    argv = ["run", "--root", str(root), "--repo", "o/r", "--pr", "7", *extra]
    args = cli.build_parser().parse_args(argv)
    code = cli.release(
        args,
        env=env or {},
        github=github,
        git=git or fake_git(),
        record_git=record_git or approval.make_git(),
        out=lines.append,
    )
    return code, lines


def _record(root, *extra, git=None, env=None):
    """The ``record`` verb (the workflow's second job)."""
    lines: list[str] = []
    argv = ["record", "--root", str(root), "--id", "0001", "--pr", "7", *extra]
    args = cli.build_parser().parse_args(argv)
    code = cli.record(args, env=env or {}, git=git or approval.make_git(), out=lines.append)
    return code, lines


def _yaml(action="publish package", production=False, command=""):
    return (
        f"deploy:\n  action: {action}\n  production: {'true' if production else 'false'}\n"
        f"  command: '{command}'\n"
    )


def test_cli_skips_an_unmerged_pull_request(tmp_path):
    root, _ = _repo_with_change(tmp_path, sdlc_yaml=_yaml())
    code, lines = _run(root, FakeGitHub(merged=False))
    assert code == 0 and "release: skip: pull request #7 is not merged" in lines


def test_cli_skips_a_merged_pull_request_that_is_not_the_build_pr(tmp_path):
    """I1: an owner's PR that touches changes/0001-*/status.yaml after the merge must not run
    deploy.command again."""
    root, _ = _repo_with_change(tmp_path, sdlc_yaml=_yaml(command="python fail.py"))
    code, lines = _run(root, FakeGitHub(head_ref="owner/tidy-status"))
    assert code == 0
    assert lines[-1] == (
        "release: skip: pull request #7 (head owner/tidy-status) is not the build PR "
        "sdlc/0001/c of change 0001"
    )
    assert not any(line.startswith(("release: run:", "release: pr:")) for line in lines)


def test_cli_passes_production_to_read_status_when_it_takes_it(tmp_path, monkeypatch):
    root, change_dir = _repo_with_change(tmp_path, sdlc_yaml=_yaml(production=True))
    seen = {}
    real = status.read_status

    def reader(change_dir, on_default_branch=False, production=False):
        seen.update(on_default_branch=on_default_branch, production=production)
        return real(change_dir)

    monkeypatch.setattr(status, "read_status", reader)
    st, note = cli._read_status(change_dir, True)
    assert note == "" and st.phase == "e"
    assert seen == {"on_default_branch": True, "production": True}


def test_cli_skips_a_pull_request_without_one_change(tmp_path):
    root, _ = _repo_with_change(tmp_path, sdlc_yaml=_yaml())
    code, lines = _run(root, FakeGitHub(files=("README.md",)))
    assert code == 0 and any(line.startswith("release: skip:") for line in lines)


def test_cli_skips_a_change_not_at_phase_e(tmp_path):
    root, _ = _repo_with_change(tmp_path, phase="d", sdlc_yaml=_yaml())
    code, lines = _run(root, FakeGitHub())
    assert code == 0 and "release: skip: change 0001 is at phase d, not e" in lines


def test_cli_waits_for_the_release_label_when_production(tmp_path):
    root, _ = _repo_with_change(tmp_path, sdlc_yaml=_yaml(production=True, command="x"))
    code, lines = _run(root, FakeGitHub(actor=None, labels=()))
    assert code == 0
    assert any(line.startswith("release: waiting: ") for line in lines)
    assert "release: route: apply sdlc:release-approved on #7" in lines
    assert not any(line.startswith("release: run:") for line in lines)


def test_cli_done_for_action_none(tmp_path):
    root, _ = _repo_with_change(tmp_path, sdlc_yaml=_yaml(action="none", command="x"))
    code, lines = _run(root, FakeGitHub(), "--change-id", "0001")
    assert code == 0 and lines[-1] == "release: done: nothing to release (deploy.action none)"


def test_cli_done_prepared_for_an_empty_command(tmp_path):
    root, _ = _repo_with_change(tmp_path, sdlc_yaml=_yaml())
    code, lines = _run(root, FakeGitHub())
    assert code == 0
    assert lines[-1] == (
        "release: done: release prepared in the PR; deploy.command is empty, nothing runs"
    )
    assert "release: change: 0001" in lines


def test_cli_runs_the_release_command_after_the_label(tmp_path, capfd):
    command = """python -c "print(''released'')\""""
    root, _ = _repo_with_change(tmp_path, sdlc_yaml=_yaml(production=True, command=command))
    code, lines = _run(root, FakeGitHub())
    assert code == 0, lines
    assert "release: approval: label (label applied by owner-login)" in lines
    assert "release: exit: 0" in lines
    assert "released" in capfd.readouterr().out
    assert lines[-1].startswith("release: record: pending: the record job stores it on")


def test_cli_skips_an_event_pr_that_is_not_the_recorded_build_pr(tmp_path):
    """0.2.27: status.yaml records the build PR; a ``labeled`` event on another PR from the
    same head (a re-opened one) is not the change's approval."""
    root, change_dir = _repo_with_change(tmp_path, sdlc_yaml=_yaml(production=True))
    st = status.read_status(change_dir)
    st.build_pr = 3
    status.write_status(change_dir, st)
    code, lines = _run(root, FakeGitHub())
    assert code == 0
    assert "release: skip: pull request #7 is not the build PR #3 status.yaml records" in lines
    st.build_pr = 7
    status.write_status(change_dir, st)
    code, lines = _run(root, FakeGitHub())
    assert code == 0 and "release: approval: label (label applied by owner-login)" in lines


def test_cli_fails_red_when_the_release_command_fails(tmp_path):
    (tmp_path / "fail.py").write_text("import sys\nsys.exit(3)\n", encoding="utf-8")
    root, _ = _repo_with_change(tmp_path, sdlc_yaml=_yaml(command="python fail.py"))
    code, lines = _run(root, FakeGitHub())
    assert code == 1 and "release: exit: 3" in lines


def test_cli_refuses_shell_operators_in_the_command(tmp_path):
    root, _ = _repo_with_change(tmp_path, sdlc_yaml=_yaml(command="make dist | tee log"))
    code, lines = _run(root, FakeGitHub())
    assert code == 2 and any("without a shell" in line for line in lines)


def test_cli_writes_the_step_summary(tmp_path):
    root, _ = _repo_with_change(tmp_path, sdlc_yaml=_yaml())
    summary = tmp_path / "summary.md"
    code, lines = _run(root, FakeGitHub(), env={"GITHUB_STEP_SUMMARY": str(summary)})
    assert code == 0
    text = summary.read_text(encoding="utf-8")
    assert text.startswith("## sdlc release") and "release: done:" in text


def test_cli_usage_error_without_sdlc_yaml(tmp_path):
    code, lines = _run(tmp_path, FakeGitHub())
    assert code == 2 and lines[0].startswith("release: error:")


def test_command_chain_splits_on_and_and_expands_globs(tmp_path):
    (tmp_path / "dist").mkdir()
    (tmp_path / "dist" / "a-1.0.whl").write_text("", encoding="utf-8")
    chain = cli.command_chain("python -m build && twine upload dist/*", tmp_path)
    assert chain[0] == ["python", "-m", "build"]
    assert [p.replace("\\", "/") for p in chain[1]] == ["twine", "upload", "dist/a-1.0.whl"]


def test_cli_fails_closed_on_a_production_flag_that_is_not_a_boolean(tmp_path):
    """``production: yes`` read as "not production" and skipped the release approval (1.0.0
    readiness review, group A)."""
    root, _ = _repo_with_change(
        tmp_path, sdlc_yaml="deploy:\n  action: publish package\n  production: yes\n"
    )
    code, lines = _run(root, FakeGitHub())
    assert code == 2
    assert any("deploy.production is 'yes', not a boolean" in line for line in lines)
    assert any("fails closed" in line for line in lines)


# --- issue #66: one release per change, and only once gate (e) has a result (0.3.1) ---------
def test_cli_skips_a_build_pr_merged_before_gate_e_has_a_result(tmp_path):
    """Issue #66: the deploy run sets phase e at its start, before the REVIEW.md pass; a build
    PR merged while it runs carries phase e and no gate (e) result. The release used to run
    deploy.command on that merge (sample change 0002, PR #17); now it skips."""
    (tmp_path / "fail.py").write_text("import sys\nsys.exit(3)\n", encoding="utf-8")
    root, change_dir = _repo_with_change(
        tmp_path, sdlc_yaml=_yaml(command="python fail.py"), gate_result=None
    )
    assert status.read_status(change_dir).gate.result is None  # as the merge left it
    code, lines = _run(root, FakeGitHub())
    assert code == 0
    assert lines[-1].startswith(
        "release: skip: change 0001 has no gate (e) result on the merged copy (gate: -/-)"
    )
    assert "before its REVIEW.md pass" in lines[-1]
    assert not any(line.startswith(("release: run:", "release: gate:")) for line in lines)
    # the pull request the run opens afterwards carries the result: released on its merge
    st = status.read_status(change_dir)
    st.record_gate("e", "passed", "waiting for the owner at gate (e)")
    status.write_status(change_dir, st)
    (change_dir / "evidence" / "gate-e.json").write_text(
        json.dumps(gate_record(deferred=False)), encoding="utf-8"
    )
    code, lines = _run(root, FakeGitHub())
    assert "release: gate: e/passed" in lines and "release: run: python fail.py" in lines


def test_cli_skips_a_gate_e_record_whose_commands_never_ran(tmp_path):
    """The review of the 0.3.1 diff, finding 1: since 0.3.0 the (e) session's gate records
    ``passed`` with its commands check deferred to the runner, and a job that died before the
    runner's step (or a merge in that window) leaves that record on the merged copy; the
    runner's guard refuses it for the next phase (issue #91) and the release must too."""
    root, change_dir = _repo_with_change(tmp_path, sdlc_yaml=_yaml(command="python x.py"))
    gate_file = change_dir / "evidence" / "gate-e.json"
    gate_file.write_text(json.dumps(gate_record(deferred=True)), encoding="utf-8")
    code, lines = _run(root, FakeGitHub())
    assert code == 0, lines
    assert lines[-1].startswith("release: skip: gate (e) of change 0001 recorded its commands")
    assert "the runner never ran it (issue #91)" in lines[-1]
    assert not any(line.startswith(("release: run:", "release: gate:")) for line in lines)
    # no record at all: nothing to judge, the same skip family
    gate_file.unlink()
    code, lines = _run(root, FakeGitHub())
    assert code == 0 and "no readable evidence/gate-e.json" in lines[-1]
    assert not any(line.startswith("release: run:") for line in lines)


def _with_remote(root: Path) -> Path:
    """A bare remote holding main and sdlc/0001/c, as GitHub does after the merge."""
    remote = root.parent / f"{root.name}-remote.git"  # beside the project, unique per test
    _git(root, "init", "-q", "--bare", str(remote))
    _git(root, "remote", "add", "origin", str(remote))
    _git(root, "push", "-q", "origin", "main", "sdlc/0001/c")
    _git(root, "checkout", "-q", "main")  # the release checks out the merge commit
    return remote


def _remote_status(root: Path, ref: str = "refs/remotes/origin/sdlc/0001/c") -> dict:
    from state import yamlish

    text = _git(root, "show", f"{ref}:changes/0001-export-the-claims-report/status.yaml")
    return yamlish.loads(text)


RELEASED = """python -c "print(''released'')\""""


def test_run_hands_the_record_to_the_record_job_and_never_releases_twice(tmp_path, capfd):
    """Issue #66: the second merge of the same change (the (e) run's second build PR from the
    same head, a label applied after the release, a dispatch) released again. ``run`` now
    writes ``released=true`` for the record job, ``record`` stores the record on the work
    branch and on refs/sdlc/released/<id>, and ``run`` skips on the record read from the
    merged copy, the ref or the branch."""
    root, change_dir = _repo_with_change(tmp_path, sdlc_yaml=_yaml(command=RELEASED))
    _with_remote(root)
    outputs = tmp_path.parent / f"{tmp_path.name}-github-output"
    outputs.write_text("ref=v0.3.1\n", encoding="utf-8")
    code, lines = _run(root, FakeGitHub(), env={"GITHUB_OUTPUT": str(outputs)})
    assert code == 0, lines
    assert "release: note: no release record: no release record on sdlc/0001/c" in lines
    assert "release: done: deploy.command exited 0 (deploy.action publish package)" in lines
    assert lines[-1] == (
        "release: record: pending: the record job stores it on sdlc/0001/c and "
        "refs/sdlc/released/0001"
    )
    assert outputs.read_text(encoding="utf-8") == "ref=v0.3.1\nreleased=true\nchange_id=0001\n"
    assert capfd.readouterr().out.count("released") == 1
    # the record job
    code, lines = _record(root, "--merge-sha", "abc1234def")
    assert code == 0, lines
    assert lines == [
        "release: record: stored on refs/sdlc/released/0001 and sdlc/0001/c ("
        + _git(root, "rev-parse", "--short", "origin/sdlc/0001/c").strip()
        + ")"
    ] or lines[0].startswith("release: record: stored on refs/sdlc/released/0001 and sdlc/0001/c (")
    _git(root, "fetch", "-q", "origin", "+refs/sdlc/*:refs/sdlc/*")
    for ref in ("refs/remotes/origin/sdlc/0001/c", "refs/sdlc/released/0001"):
        recorded = _remote_status(root, ref)
        assert recorded["released_pr"] == 7 and recorded["released_sha"] == "abc1234def", ref
        assert recorded["released_at"].endswith("Z"), ref
    assert _git(root, "log", "-1", "--format=%s", "origin/sdlc/0001/c").strip() == (
        "release(0001): record the release of pull request #7"
    )
    assert _git(root, "rev-parse", "refs/sdlc/released/0001") == _git(
        root, "rev-parse", "origin/sdlc/0001/c"
    )
    assert _git(root, "status", "--porcelain").strip() == ""  # the checkout is untouched
    # a second record (the job re-run) changes nothing
    code, lines = _record(root)
    assert code == 0 and lines[0].startswith(
        "release: record: refs/sdlc/released/0001 already records it: released as abc1234def"
    )
    # the labeled event, a dispatch or the second build PR's merge: the remote says released
    outputs.write_text("", encoding="utf-8")
    code, lines = _run(
        root, FakeGitHub(), "--event", "labeled", env={"GITHUB_OUTPUT": str(outputs)}
    )
    assert code == 0, lines
    assert lines[-1].startswith("release: skip: change 0001 was already released as abc1234def at")
    assert lines[-1].endswith("(pull request #7) (refs/sdlc/released/0001)")
    assert not any(line.startswith("release: run:") for line in lines)
    assert outputs.read_text(encoding="utf-8") == "" and "released" not in capfd.readouterr().out
    # a merged copy that carries the record (the second PR merged from the branch): the same
    _git(root, "merge", "-q", "--no-ff", "-m", "second merge", "origin/sdlc/0001/c")
    code, lines = _run(root, FakeGitHub())
    assert code == 0 and lines[-1].startswith("release: skip: change 0001 was already released")
    assert "released" not in capfd.readouterr().out


def test_the_record_survives_a_deleted_work_branch(tmp_path, capfd):
    """The review of the 0.3.1 diff, finding 2: with GitHub's "automatically delete head
    branches" the work branch is gone before the release job starts, so a record kept only
    there would never exist and the label or a dispatch would release again. The ref
    refs/sdlc/released/<id> is no branch: the record goes there, on the merge commit."""
    root, _ = _repo_with_change(tmp_path, sdlc_yaml=_yaml(command=RELEASED))
    _with_remote(root)
    _git(root, "push", "-q", "origin", "--delete", "sdlc/0001/c")
    code, lines = _run(root, FakeGitHub())
    assert code == 0 and lines[-1].startswith("release: record: pending")
    assert "released" in capfd.readouterr().out
    code, lines = _record(root, "--merge-sha", "abc1234def")
    assert code == 0, lines
    assert lines[0].startswith(
        "release: record: stored on refs/sdlc/released/0001 (sdlc/0001/c is gone)"
    )
    _git(root, "fetch", "-q", "origin", "+refs/sdlc/*:refs/sdlc/*")
    assert _remote_status(root, "refs/sdlc/released/0001")["released_pr"] == 7
    assert (
        _git(root, "rev-parse", "refs/sdlc/released/0001^").strip()
        == _git(root, "rev-parse", "main").strip()
    )  # on top of the merge commit
    assert "sdlc/0001/c" not in _git(root, "ls-remote", "--heads", "origin")
    code, lines = _run(root, FakeGitHub(), "--event", "labeled")
    assert code == 0 and lines[-1].startswith("release: skip: change 0001 was already released")
    assert "released" not in capfd.readouterr().out


def test_run_fails_closed_when_the_remote_record_cannot_be_read(tmp_path, capfd):
    """The review of the 0.3.1 diff, finding 3: a failed ls-remote or fetch let the release
    go on with a note, so a network blip on a branch that already records a release released
    it again. A read that did not happen is exit 2, never a release."""
    root, _ = _repo_with_change(tmp_path, sdlc_yaml=_yaml(command=RELEASED))
    _with_remote(root)
    real = approval.make_git()
    _run(root, FakeGitHub())
    _record(root)
    for failing in ("ls-remote", "fetch"):

        def flaky(r, *a, failing=failing):
            if a[0] == failing:
                return 128, ""
            return real(r, *a)

        code, lines = _run(root, FakeGitHub(), "--event", "labeled", record_git=flaky)
        assert code == 2, (failing, lines)
        assert lines[-1].startswith("release: error: the remote's release record could not be read")
        assert "the release fails closed" in lines[-1]
        assert not any(line.startswith("release: run:") for line in lines)
    assert capfd.readouterr().out.count("released") == 1  # the first run only

    # a timeout is the same
    def slow(r, *a):
        raise TimeoutError("git ls-remote took over 120s")

    code, lines = _run(root, FakeGitHub(), record_git=slow)
    assert code == 2 and "took over" in lines[-1]
    # the ref there without a record is not "no record" either
    (root / "x").write_text("", encoding="utf-8")
    _git(root, "update-ref", "refs/sdlc/released/0001", "main")
    _git(root, "push", "-q", "origin", "+refs/sdlc/released/0001:refs/sdlc/released/0001")
    code, lines = _run(root, FakeGitHub())
    assert code == 2 and "carries no release record" in lines[-1]


def test_the_record_lands_after_a_competing_push(tmp_path):
    """The review of the 0.3.1 diff, finding 8: a session pushing to sdlc/<id>/c at the same
    moment (a fix round the owner started before merging) rejects the record's first push;
    the record is re-applied on the new tip and the competing commit is kept."""
    root, _ = _repo_with_change(tmp_path, sdlc_yaml=_yaml(command=RELEASED))
    remote = _with_remote(root)
    real = approval.make_git()
    other = tmp_path.parent / f"{tmp_path.name}-other"
    _git(root, "clone", "-q", "--branch", "sdlc/0001/c", str(remote), str(other))
    _git(other, "config", "user.email", "s@example.com")
    _git(other, "config", "user.name", "session")
    pushes = {"n": 0}

    def racing(r, *a):
        if a[0] == "push" and pushes["n"] == 0:
            pushes["n"] += 1
            (other / "report.py").write_text("x = 3\n", encoding="utf-8")
            _git(other, "commit", "-q", "-am", "fix round: a concurrent push")
            _git(other, "push", "-q", "origin", "sdlc/0001/c")
        return real(r, *a)

    _run(root, FakeGitHub())
    code, lines = _record(root, git=racing)
    assert code == 0, lines
    assert lines[0].startswith("release: record: stored on refs/sdlc/released/0001 and sdlc/0001/c")
    subjects = _git(root, "log", "--format=%s", "-2", "origin/sdlc/0001/c").splitlines()
    _git(root, "fetch", "-q", "origin")
    subjects = _git(root, "log", "--format=%s", "-2", "origin/sdlc/0001/c").splitlines()
    assert subjects == [
        "release(0001): record the release of pull request #7",
        "fix round: a concurrent push",
    ]
    assert _remote_status(root)["released_pr"] == 7


def test_record_is_red_when_the_push_fails(tmp_path):
    """A release that ran without its record would release again on the next event: the
    record job is red and says so (every push rejected)."""
    root, _ = _repo_with_change(tmp_path, sdlc_yaml=_yaml(command=RELEASED))
    _with_remote(root)
    real = approval.make_git()
    pushes = []

    def rejecting(r, *a):
        if a[0] == "push":
            pushes.append(a)
            return 1, ""
        return real(r, *a)

    code, lines = _record(root, git=rejecting)
    assert code == 1, lines
    assert lines[-1].startswith("release: record: not stored: the push to refs/sdlc/released/0001")
    assert lines[-1].endswith("; the release ran without its record")
    assert len(pushes) == cli.RECORD_PUSH_ATTEMPTS
    assert _git(root, "status", "--porcelain").strip() == ""  # the worktrees are gone
    assert _git(root, "worktree", "list").count("\n") == 1

    # a remote that cannot be read is red too, without a push
    def down(r, *a):
        return (128, "") if a[0] == "ls-remote" else real(r, *a)

    code, lines = _record(root, git=down)
    assert code == 1 and "origin could not be read" in lines[-1]


def test_cli_releases_nothing_twice_with_an_empty_command_either(tmp_path):
    """Nothing ran, so nothing is handed to the record job: a merged copy at phase e with an
    empty command stays "prepared" on every event (no record for a release that did not
    happen, and no released=true output)."""
    root, _ = _repo_with_change(tmp_path, sdlc_yaml=_yaml())
    _with_remote(root)
    outputs = tmp_path.parent / f"{tmp_path.name}-github-output"
    outputs.write_text("", encoding="utf-8")
    code, lines = _run(root, FakeGitHub(), env={"GITHUB_OUTPUT": str(outputs)})
    assert code == 0 and lines[-1].startswith("release: done: release prepared in the PR")
    assert outputs.read_text(encoding="utf-8") == ""
    assert "refs/sdlc/released/0001" not in _git(root, "ls-remote", "origin")


# --- issue #68: a parked change merged at (e) waits for the label, with its reason shown ----
def test_cli_waits_for_the_label_on_a_parked_merge_whatever_production_says(tmp_path, capfd):
    """Issue #68: gate (e) parked (a risk-list hit, a guardrail change, the iteration cap) and
    the owner merged anyway; without a declared production the release ran deploy.command
    with no second look and no mention of the park. Now the park reason is printed and the
    release waits for sdlc:release-approved, production or not."""
    reason = "risk-list hit: touches auth/"
    root, change_dir = _repo_with_change(
        tmp_path, sdlc_yaml=_yaml(production=False, command=RELEASED), parked=reason
    )
    assert status.read_status(change_dir, on_default_branch=True).parked_reason is None
    code, lines = _run(root, FakeGitHub(actor=None, labels=()))
    assert code == 0, lines
    assert "release: gate: e/parked" in lines
    assert f"release: parked: gate (e) parked change 0001: {reason}" in lines
    waiting = [line for line in lines if line.startswith("release: waiting: ")]
    assert waiting and f"merged while parked ({reason})" in waiting[0]
    assert "whatever deploy.production says" in waiting[0]
    assert "release: route: apply sdlc:release-approved on #7" in lines
    assert not any(line.startswith("release: run:") for line in lines)
    assert "released" not in capfd.readouterr().out
    # the owner's label (a person's act on GitHub) releases it, with the reason in the log
    code, lines = _run(root, FakeGitHub(), "--event", "labeled")
    assert code == 0, lines
    assert f"release: parked: gate (e) parked change 0001: {reason}" in lines
    assert "release: approval: label (label applied by owner-login)" in lines
    assert "release: exit: 0" in lines and "released" in capfd.readouterr().out


def test_cli_refuses_the_automation_identity_s_label_on_a_parked_merge(tmp_path):
    root, _ = _repo_with_change(tmp_path, sdlc_yaml=_yaml(command="x"), parked="cap reached")
    code, lines = _run(root, FakeGitHub(actor="github-actions[bot]"))
    assert code == 0
    assert any(line.startswith("release: waiting: ") for line in lines)
    assert not any(line.startswith("release: run:") for line in lines)
