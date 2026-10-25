"""Layer-1 tests of the change-id reservation (R51, gap G2; the race analysis's checks 1 to 5;
NOTES §59): ``new-change`` reserves ``sdlc/<id>/intent`` on the remote with a commit of its own
under an empty lease before it writes the folder, takes the next id when git refuses the
ref update, keeps today's best-effort id on any other failure, and leaves a local branch at
the reservation so the id's first ``commit-phase`` pushes a fast-forward."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from state import cli as state_cli
from state import gitops


def git(cwd: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=cwd, capture_output=True, text=True, check=True, encoding="utf-8"
    ).stdout.strip()


def clone(tmp_path: Path, bare: Path, name: str) -> Path:
    work = tmp_path / name
    git(tmp_path, "clone", "-q", str(bare), str(work))
    git(work, "config", "user.email", "owner@example.com")
    git(work, "config", "user.name", "Owner")
    return work


@pytest.fixture
def remote(tmp_path):
    """A bare remote whose main holds one commit with an empty ``changes/``."""
    seed = tmp_path / "seed"
    seed.mkdir()
    git(seed, "init", "-q", "-b", "main")
    git(seed, "config", "user.email", "owner@example.com")
    git(seed, "config", "user.name", "Owner")
    (seed / "changes").mkdir()
    (seed / "changes" / ".keep").write_text("", encoding="utf-8")
    git(seed, "add", ".")
    git(seed, "commit", "-q", "-m", "seed")
    bare = tmp_path / "origin.git"
    git(tmp_path, "clone", "-q", "--bare", str(seed), str(bare))
    return bare


def new_change(capsys, root: Path, title: str = "a change") -> tuple[int, dict, str]:
    code = state_cli.main(["new-change", "--root", str(root), "--title", title])
    out, err = capsys.readouterr()
    return code, (json.loads(out) if out.strip() else {}), err


def remote_sha(bare: Path, branch: str) -> str:
    """The remote branch's sha, or "" when it does not exist."""
    return subprocess.run(
        ["git", "rev-parse", "--verify", "--quiet", f"refs/heads/{branch}"],
        cwd=bare, capture_output=True, text=True, encoding="utf-8",
    ).stdout.strip()  # fmt: skip


def test_new_change_reserves_the_id_with_a_commit_of_its_own(remote, tmp_path, capsys):
    work = clone(tmp_path, remote, "work")
    main = git(work, "rev-parse", "origin/main")
    code, out, _ = new_change(capsys, work)
    assert code == 0 and out["id"] == "0001"
    res = out["reservation"]
    assert res["outcome"] == gitops.RESERVED
    assert remote_sha(remote, "sdlc/0001/intent") == res["sha"]
    # the default branch's tree and tip as parent: an empty commit unique to the allocation
    assert git(work, "rev-parse", f"{res['sha']}^") == main
    assert git(work, "rev-parse", f"{res['sha']}^{{tree}}") == git(work, "rev-parse", "main^{tree}")
    assert res["local_branch"] == "sdlc/0001/intent"
    assert git(work, "rev-parse", "sdlc/0001/intent") == res["sha"]
    assert (work / out["dir"]).is_dir()


def test_two_allocations_from_the_same_tip_get_two_ids(remote, tmp_path, capsys, monkeypatch):
    """Row 1 of the race analysis: both read the remote before either pushed. Both start from
    the same default-branch tip, which a plain or leased push would accept twice (NOTES §59);
    each reservation's own commit makes the second a refusal, and the retry takes 0002."""
    first = clone(tmp_path, remote, "first")
    second = clone(tmp_path, remote, "second")
    reads = []
    real = gitops.remote_change_ids

    def stale_then_fresh(root, *a, **k):
        reads.append(root)
        return [] if len(reads) == 1 else real(root, *a, **k)

    assert new_change(capsys, first)[1]["id"] == "0001"
    monkeypatch.setattr(gitops, "remote_change_ids", stale_then_fresh)
    code, out, _ = new_change(capsys, second)
    assert code == 0 and out["id"] == "0002"
    assert out["reservation"]["outcome"] == gitops.RESERVED
    assert len(reads) == 2  # the retry read the remote again
    assert [p.name[:4] for p in (second / "changes").iterdir() if p.is_dir()] == ["0002"]


def test_a_second_reservation_of_a_taken_id_is_refused(remote, tmp_path):
    work = clone(tmp_path, remote, "work")
    base = gitops.reservation_base(work)
    assert gitops.reserve_change_id(work, "0007", base)[0] == gitops.RESERVED
    outcome, sha, detail = gitops.reserve_change_id(work, "0007", base)
    assert (outcome, sha) == (gitops.TAKEN, None)
    assert "stale info" in detail


def test_the_retries_skip_every_refused_id_and_are_bounded(remote, tmp_path, capsys, monkeypatch):
    work = clone(tmp_path, remote, "work")
    tried = []

    def always_taken(root, change_id, base, remote="origin"):
        tried.append(change_id)
        return gitops.TAKEN, None, "! [rejected] x -> y (stale info)"

    monkeypatch.setattr(gitops, "reserve_change_id", always_taken)
    code, out, err = new_change(capsys, work)
    assert code == 1 and out == {}
    assert tried == ["0001", "0002", "0003", "0004", "0005"]
    assert "run it again" in err
    assert not [p for p in (work / "changes").iterdir() if p.is_dir()]  # no folder written


def test_a_remote_that_cannot_be_written_keeps_the_best_effort_id(tmp_path, remote, capsys):
    """Check 3: a failure other than git's refusal (here an unreachable remote) is not
    "taken": the id is today's best effort, said so, and the folder is written."""
    work = clone(tmp_path, remote, "work")
    git(work, "remote", "set-url", "origin", str(tmp_path / "gone.git"))
    code, out, err = new_change(capsys, work)
    assert code == 0 and out["id"] == "0001"
    assert out["reservation"]["outcome"] == gitops.UNRESERVED
    assert "not reserved" in err
    assert (work / out["dir"]).is_dir()
    assert "sha" not in out["reservation"]


def test_an_explicit_id_reserves_nothing(remote, tmp_path, capsys):
    work = clone(tmp_path, remote, "work")
    code = state_cli.main(["new-change", "--root", str(work), "--title", "t", "--id", "0042"])
    out = json.loads(capsys.readouterr().out)
    assert code == 0 and out["id"] == "0042" and "reservation" not in out
    assert not remote_sha(remote, "sdlc/0042/intent")


def test_the_first_commit_phase_starts_from_the_reservation(remote, tmp_path, capsys):
    """Check 5: a local default branch behind the reservation's parent would push
    non-fast-forward against it; the local branch made at allocation is what the first
    ``commit-phase`` checks out, so its push fast-forwards the reserved ref."""
    work = clone(tmp_path, remote, "work")
    other = clone(tmp_path, remote, "other")
    (other / "x.txt").write_text("x\n", encoding="utf-8")
    git(other, "add", "x.txt")
    git(other, "commit", "-q", "-m", "moves main")
    git(other, "push", "-q", "origin", "main")
    git(work, "fetch", "-q", "origin")  # origin/main moved; the local main stays behind
    _, out, _ = new_change(capsys, work)
    reserved = out["reservation"]["sha"]
    (work / out["dir"] / "intent.md").write_text("# intent\n", encoding="utf-8")
    code = state_cli.main(
        ["commit-phase", "--root", str(work), "--id", out["id"], "--phase", "intent",
         "--message", "intent", "--start-point", "main", "--push"]
    )  # fmt: skip
    capsys.readouterr()
    assert code == 0
    pushed = remote_sha(remote, "sdlc/0001/intent")
    assert git(work, "rev-parse", f"{pushed}^") == reserved


def test_the_reservation_sits_on_the_remote_tip_without_a_fetch_by_hand(remote, tmp_path, capsys):
    """The independent review of the R51 PR, finding 9: a clone whose remote-tracking default
    branch is stale still reserves on the remote's tip, since new-change fetches it first."""
    work = clone(tmp_path, remote, "work")
    other = clone(tmp_path, remote, "other")
    (other / "x.txt").write_text("x\n", encoding="utf-8")
    git(other, "add", "x.txt")
    git(other, "commit", "-q", "-m", "moves main")
    git(other, "push", "-q", "origin", "main")
    tip = git(other, "rev-parse", "HEAD")
    _, out, _ = new_change(capsys, work)
    assert git(work, "rev-parse", f"{out['reservation']['sha']}^") == tip


def test_a_push_reports_in_english_and_a_network_read_has_no_bound(remote, tmp_path, monkeypatch):
    """Findings 7 and 8 of the review: git translates its refusal reasons, which the
    reservation and the push read; a network read keeps no 60 s bound."""
    work = clone(tmp_path, remote, "work")
    seen = []
    real = subprocess.run

    def spy(argv, **kwargs):
        seen.append((argv, kwargs.get("env"), kwargs.get("timeout")))
        return real(argv, **kwargs)

    monkeypatch.setattr(gitops.subprocess, "run", spy)
    gitops.run_proc(work, "push", "origin", "main")
    gitops.run_proc(work, "ls-remote", "origin")
    gitops.run_proc(work, "rev-parse", "HEAD")
    push, ls_remote, rev_parse = seen
    assert push[1]["LC_ALL"] == "C" and push[1]["LANGUAGE"] == "C" and push[2] is None
    assert ls_remote[2] is None
    assert rev_parse[2] == gitops.READ_TIMEOUT_SECONDS
