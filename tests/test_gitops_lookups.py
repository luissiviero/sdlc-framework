"""Layer-1 tests of the remembered git lookups (plugin 1.0.13, choice 235 item 5): ``is_repo``,
``default_branch``, ``ref_exists`` and gate/diff.py's ``default_base`` ask git once while
nothing can have changed the answer, and a lookup after any git call that can change it
(init, fetch, checkout, commit, branch, remote, push, merge, a test's own ``git``, a process
that is not git at all) returns the new truth."""

from __future__ import annotations

import os
import shutil
import stat
import subprocess
import sys
from pathlib import Path

import pytest

from gate import diff as gate_diff
from state import gitops


def git(cwd: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=cwd, capture_output=True, text=True, check=True, encoding="utf-8"
    ).stdout


def remove_tree(path: Path) -> None:
    """``shutil.rmtree`` that clears the read-only bit git sets on its objects (Windows)."""

    def force(func, target, _exc):
        os.chmod(target, stat.S_IWRITE)
        func(target)

    if sys.version_info >= (3, 12):
        shutil.rmtree(path, onexc=force)
    else:
        shutil.rmtree(path, onerror=force)


def commit(root: Path, name: str) -> None:
    (root / name).write_text(name + "\n", encoding="utf-8")
    git(root, "add", name)
    git(root, "commit", "-q", "-m", name)


@pytest.fixture
def repo(tmp_path):
    """A repository on ``trunk`` (no main, no master, no remote) with one commit."""
    root = tmp_path / "proj"
    root.mkdir()
    git(root, "init", "-q", "-b", "trunk")
    git(root, "config", "user.email", "owner@example.com")
    git(root, "config", "user.name", "Owner")
    commit(root, "a.txt")
    return root


@pytest.fixture
def counted(monkeypatch):
    """The git calls gitops makes, by argument list."""
    calls: list[tuple[str, ...]] = []
    real = gitops.run

    def run(root, *args, check=True):
        calls.append(args)
        return real(root, *args, check=check)

    monkeypatch.setattr(gitops, "run", run)
    return calls


def test_a_repeated_lookup_with_nothing_in_between_asks_git_once(repo, counted):
    assert gitops.is_repo(repo) and gitops.is_repo(repo)
    assert gitops.default_branch(repo) == gitops.default_branch(repo) == "trunk"
    assert gitops.ref_exists(repo, "refs/heads/trunk") and gitops.ref_exists(
        repo, "refs/heads/trunk"
    )
    assert gate_diff.default_base(repo) == gate_diff.default_base(repo) == "HEAD"
    asked = [args[:2] for args in counted]
    assert asked.count(("rev-parse", "--is-inside-work-tree")) == 1
    # origin/HEAD and origin/main are asked once for default_branch and default_base together
    assert asked.count(("symbolic-ref", "refs/remotes/origin/HEAD")) == 1
    verified = [args[3] for args in counted if args[:2] == ("rev-parse", "--verify")]
    assert sorted(verified) == sorted(
        ["refs/remotes/origin/main", "refs/remotes/origin/master", "refs/heads/trunk", "main"]
        + ["master"]
    )
    # read-only queries in between (the gate's own) keep the answers
    git(repo, "status", "--porcelain")
    git(repo, "rev-parse", "HEAD")
    before = len(counted)
    assert gitops.default_branch(repo) == "trunk" and gitops.ref_exists(repo, "refs/heads/trunk")
    assert gate_diff.default_base(repo) == "HEAD"
    assert len(counted) == before


def test_is_repo_follows_init_and_a_removed_git_directory(tmp_path):
    root = tmp_path / "proj"
    root.mkdir()
    assert gitops.is_repo(root) is False and gate_diff.is_repo(root) is False
    git(root, "init", "-q")
    assert gitops.is_repo(root) is True and gate_diff.is_repo(root) is True
    remove_tree(root / ".git")  # no process at all: the stat of the git directory sees it
    assert gitops.is_repo(root) is False and gate_diff.is_repo(root) is False
    gitops.run(root, "init", "-q")
    assert gitops.is_repo(root) is True


def test_default_branch_follows_branch_remote_push_set_head_and_checkout(repo, tmp_path):
    assert gitops.default_branch(repo) == "trunk"  # the current branch, the last resort
    git(repo, "checkout", "-q", "-b", "feature")
    assert gitops.default_branch(repo) == "feature"
    gitops.run(repo, "branch", "master", "trunk")
    assert gitops.default_branch(repo) == "master"  # a local master, by gitops' own call
    git(repo, "branch", "main", "trunk")
    assert gitops.default_branch(repo) == "main"  # a local main, by a test's own git
    bare = tmp_path / "remote.git"
    git(tmp_path, "init", "-q", "--bare", "-b", "trunk", str(bare))
    gitops.run(repo, "remote", "add", "origin", str(bare))
    gitops.run(repo, "push", "-q", "origin", "feature:release")
    assert gitops.ref_exists(repo, "refs/remotes/origin/release")
    git(bare, "symbolic-ref", "HEAD", "refs/heads/release")
    gitops.run(repo, "remote", "set-head", "origin", "--auto")  # origin/HEAD by a fetch of it
    assert gitops.default_branch(repo) == "release"
    assert gate_diff.default_base(repo) == "refs/remotes/origin/release"
    git(repo, "remote", "set-head", "origin", "--delete")
    assert gitops.default_branch(repo) == "main"
    assert gate_diff.default_base(repo) == "main"


def test_ref_exists_follows_push_fetch_merge_and_deletion(repo, tmp_path):
    bare = tmp_path / "remote.git"
    git(tmp_path, "init", "-q", "--bare", "-b", "trunk", str(bare))
    git(repo, "remote", "add", "origin", str(bare))
    assert gitops.ref_exists(repo, "refs/remotes/origin/trunk") is False
    gitops.push(repo, "trunk")
    assert gitops.ref_exists(repo, "refs/remotes/origin/trunk") is True
    other = tmp_path / "other"
    git(tmp_path, "clone", "-q", str(bare), str(other))
    git(other, "config", "user.email", "o@example.com")
    git(other, "config", "user.name", "O")
    git(other, "checkout", "-q", "-b", "topic")
    commit(other, "b.txt")
    git(other, "push", "-q", "origin", "topic")
    assert gitops.ref_exists(repo, "refs/remotes/origin/topic") is False
    gitops.run(repo, "fetch", "-q", "origin")
    assert gitops.ref_exists(repo, "refs/remotes/origin/topic") is True
    assert gitops.ref_exists(repo, "topic-merged") is False
    git(repo, "merge", "-q", "--no-edit", "origin/topic")
    git(repo, "branch", "topic-merged")
    assert gitops.ref_exists(repo, "topic-merged") is True
    git(repo, "update-ref", "-d", "refs/remotes/origin/topic")
    assert gitops.ref_exists(repo, "refs/remotes/origin/topic") is False
    assert gitops.ref_exists(repo, "HEAD~2") is False  # a.txt and b.txt only
    (repo / "c.txt").write_text("c\n", encoding="utf-8")
    assert gitops.commit_paths(repo, ["c.txt"], "c") is not None  # gitops' own commit
    assert gitops.ref_exists(repo, "HEAD~2") is True


def test_a_process_that_is_not_git_forgets_every_answer(repo):
    """The model's session or a script may run git itself: any process start counts."""
    assert gitops.default_branch(repo) == "trunk"
    script = "import subprocess; subprocess.run(['git', 'branch', 'main'], check=True)"
    subprocess.run([sys.executable, "-c", script], cwd=repo, check=True)
    assert gitops.default_branch(repo) == "main"


def test_the_explicit_default_branch_is_never_remembered(repo, monkeypatch):
    assert gitops.default_branch(repo) == "trunk"
    monkeypatch.setenv(gitops.DEFAULT_BRANCH_ENV, "develop")
    assert gitops.default_branch(repo) == "develop"
    monkeypatch.delenv(gitops.DEFAULT_BRANCH_ENV)
    assert gitops.default_branch(repo) == "trunk"


@pytest.mark.parametrize(
    "argv, reads",
    [
        (["git", "rev-parse", "--is-inside-work-tree"], True),
        (["git", "-c", "core.hooksPath=/x", "-c", "core.fsmonitor=false", "status"], True),
        (["/usr/bin/git", "--literal-pathspecs", "diff", "--cached"], True),
        (["git", "config", "--get", "user.name"], True),
        (["git", "config", "user.name", "Bot"], False),
        (["git", "remote"], True),
        (["git", "remote", "get-url", "origin"], True),
        (["git", "remote", "add", "origin", "/x"], False),
        (["git", "remote", "set-url", "origin", "/x"], False),
        (["git", "branch", "--list", "main"], True),
        (["git", "branch", "--list", "-D", "main"], False),
        (["git", "branch", "main"], False),
        (["git", "symbolic-ref", "refs/remotes/origin/HEAD"], True),
        (["git", "symbolic-ref", "HEAD", "refs/heads/x"], False),
        (["git", "symbolic-ref", "--delete", "refs/remotes/origin/HEAD"], False),
        (["git", "fetch", "origin"], False),
        (["git", "checkout", "-b", "x"], False),
        (["git", "commit", "-m", "x"], False),
        (["git", "push", "origin", "x"], False),
        (["git", "merge", "main"], False),
        (["git", "init"], False),
        (["git"], False),
        ([sys.executable, "-c", "pass"], False),
        # Windows: the audit event carries the command line list2cmdline built
        ('git -c "core.hooksPath=C:\\Users\\RUNNER~1\\a b" rev-parse HEAD', True),
        ("C:\\Program Files\\Git\\cmd\\git.exe status", False),  # unquoted: not understood
        ('"C:\\Program Files\\Git\\cmd\\git.exe" status', True),
        ("git.exe checkout -q main", False),
        ('git config "--get" user.name', True),
        (b"git status", False),
        # a long global option whose value is the next word: not understood (choice 239)
        (["git", "--git-dir", "log", "commit", "-m", "x"], False),
        (["git", "--work-tree", "status", "checkout", "x"], False),
        (["git", "--git-dir=.git", "log"], True),
    ],
)
def test_only_read_only_git_queries_keep_the_answers(argv, reads):
    assert gitops._reads_only(argv) is reads


def test_every_process_start_but_a_read_only_git_query_moves_the_generation():
    """The audit events the hook counts: a fork too, whose child may run git."""
    for event, args in (
        ("os.fork", ()),
        ("os.system", (b"git branch main",)),
        ("subprocess.Popen", ("git", ["git", "fetch"], None, None)),
    ):
        before = gitops._generation
        gitops._on_audit(event, args)
        assert gitops._generation == before + 1, event
    before = gitops._generation
    gitops._on_audit("subprocess.Popen", ("git", ["git", "rev-parse", "HEAD"], None, None))
    gitops._on_audit("open", ("/x", "r", 0))
    assert gitops._generation == before


def _start_with(how: str) -> None:
    """Start one trivial real process through ``how`` and wait for it."""
    exe = sys.executable
    if how == "os.system":
        assert os.system(f'"{exe}" -c pass') == 0
    elif how == "os.spawnv":
        assert os.spawnv(os.P_WAIT, exe, [exe, "-c", "pass"]) == 0
    elif how == "os.posix_spawn":
        pid = os.posix_spawn(exe, [exe, "-c", "pass"], dict(os.environ))
        os.waitpid(pid, 0)
    elif how == "os.fork":
        pid = os.fork()
        if pid == 0:  # the child leaves at once, running nothing of the test
            os._exit(0)
        os.waitpid(pid, 0)
    elif how == "subprocess":
        subprocess.run([exe, "-c", "pass"], check=True)


# the ways a process can start on this platform, each raising its own audit event in CPython;
# os.exec* replaces the process and os.startfile opens a file with its application, so neither
# is started here (their names are only the hook's spelling of CPython's events)
STARTS = ["os.system", "os.spawnv", "subprocess"] + (
    ["os.posix_spawn", "os.fork"] if os.name == "posix" else []
)


@pytest.mark.parametrize("how", STARTS)
def test_a_real_process_start_moves_the_generation(how):
    """Choice 239: the events CPython raises are the names the hook counts, shown by starting
    a real process each way rather than by calling the hook with hand-made events."""
    before = gitops._generation
    _start_with(how)
    assert gitops._generation > before, how


def test_a_hanging_read_only_query_fails_closed(repo, monkeypatch):
    """Choice 239: a read-only query is bounded again (gate/diff.py lost its 60 s in 1.0.13);
    the timeout is a GitError, which the gate reads as git unavailable."""

    def hang(*_args, **kwargs):
        assert kwargs.get("timeout") == gitops.READ_TIMEOUT_SECONDS
        raise subprocess.TimeoutExpired(["git"], kwargs["timeout"])

    monkeypatch.setattr(gitops.subprocess, "run", hang)
    with pytest.raises(gitops.GitError, match="timed out"):
        gitops.run(repo, "rev-parse", "HEAD")
    assert gate_diff.is_repo(repo / "elsewhere") is False


def test_a_write_has_no_read_timeout(repo, monkeypatch):
    seen = {}
    real = subprocess.run

    def spy(*args, **kwargs):
        seen["timeout"] = kwargs.get("timeout")
        return real(*args, **kwargs)

    monkeypatch.setattr(gitops.subprocess, "run", spy)
    gitops.run(repo, "branch", "other")
    assert seen["timeout"] is None


def test_is_repo_drops_a_linked_worktree_removed_by_hand(repo, tmp_path):
    """Choice 239: the worktree's git directory outlives a removal by hand; its ``.git`` file
    does not, and is_repo now stats both."""
    wt = tmp_path / "wt"
    git(repo, "worktree", "add", "-q", str(wt), "-b", "side")
    assert gitops.is_repo(wt) is True
    remove_tree(wt)
    wt.mkdir()  # the same path, empty: git rev-parse exits 128 here
    assert gitops.is_repo(wt) is False


def test_a_hanging_default_base_lookup_is_git_unavailable(repo, monkeypatch):
    def hang(*_args, **kwargs):
        raise subprocess.TimeoutExpired(["git"], kwargs.get("timeout") or 0)

    gitops._remembered.clear()
    monkeypatch.setattr(gitops.subprocess, "run", hang)
    with pytest.raises(gate_diff.GitUnavailable):
        gate_diff.default_base(repo)


def test_only_change_folder_moved(repo):
    """Change 0004 (R12): the rule a fix round's head check and the PR body's stale-proof line
    share: HEAD itself, or an ancestor from which only the change folder moved."""
    change = repo / "changes" / "0001-x"
    change.mkdir(parents=True)
    commit(repo, "changes/0001-x/manifest.json")
    first = git(repo, "rev-parse", "HEAD").strip()
    assert gitops.only_change_folder_moved(repo, change, first)  # HEAD itself
    commit(repo, "changes/0001-x/gate-c.json")  # the runner's record commit
    assert gitops.only_change_folder_moved(repo, change, first)
    folder_only = git(repo, "rev-parse", "HEAD").strip()
    commit(repo, "src.py")  # a source file moved after it
    assert not gitops.only_change_folder_moved(repo, change, first)
    assert not gitops.only_change_folder_moved(repo, change, folder_only)
    after_source = git(repo, "rev-parse", "HEAD").strip()
    # a file renamed into the change folder is a change outside it
    git(repo, "mv", "src.py", "changes/0001-x/src.py")
    git(repo, "commit", "-q", "-m", "move")
    assert not gitops.only_change_folder_moved(repo, change, after_source)
    # an unknown sha, no sha, not a repository
    assert not gitops.only_change_folder_moved(repo, change, "0" * 40)
    assert not gitops.only_change_folder_moved(repo, change, None)
    assert not gitops.only_change_folder_moved(repo.parent, change, first)
