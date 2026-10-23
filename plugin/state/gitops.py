"""Thin git helpers used by the phase commands. Argument lists only (no shell) so the same
code runs on Windows, in a cloud session and on a Linux runner."""

from __future__ import annotations

import os
import re
import shlex
import subprocess
import sys
import tempfile
from pathlib import Path

from state import conventions

# The workflows set it from ``github.event.repository.default_branch`` on every step that
# needs the default branch (the only way to name it: no command-line flag, decisions 11, 14).
DEFAULT_BRANCH_ENV = "SDLC_DEFAULT_BRANCH"


class GitError(RuntimeError):
    pass


# --- remembered lookups (1.0.13, choice 235 item 5) ---------------------------------------------
# One phase run asked git ``rev-parse --is-inside-work-tree`` 13 times and ``rev-parse --verify
# --quiet refs/remotes/origin/main`` 11 times, from is_repo, default_branch, gate/diff.py's
# default_base and the runner's ref checks; on Windows every git process is expensive. A
# lookup is remembered only until the process starts anything but a read-only git query: a
# fetch, a checkout, a commit, a push, the model's session, a test's own ``git`` helper. The
# audit hook below sees every process start of this process (``subprocess``, ``os.system``,
# ``os.exec*``, ``os.spawn*``, ``os.posix_spawn``, and a fork, whose child may run git),
# whoever starts it, and moves the generation on; a remembered answer of an older generation
# is asked again. is_repo keeps a yes for good, re-checked by a stat that the git directory
# it found still exists.
_PROCESS_EVENTS = frozenset(
    {
        "subprocess.Popen", "os.system", "os.exec", "os.spawn", "os.posix_spawn",
        "os.startfile", "os.fork", "os.forkpty",
    }
)  # fmt: skip
# the git subcommands that never move a ref, HEAD or a remote; ``config``, ``remote``,
# ``branch`` and ``symbolic-ref`` count only in their reading forms (``_reads_only``)
_READ_ONLY_GIT = frozenset(
    {
        "rev-parse", "cat-file", "show", "diff", "diff-tree", "diff-index", "log", "rev-list",
        "merge-base", "ls-files", "ls-tree", "ls-remote", "for-each-ref", "show-ref", "status",
        "version", "check-ignore", "check-attr", "grep", "describe", "name-rev", "var",
    }
)  # fmt: skip
_generation = 0
_remembered: dict[tuple, tuple[int, object]] = {}
_repos: dict[tuple, str] = {}


def _reads_only(argv) -> bool:
    """True when ``argv`` is a git query that changes no ref, HEAD or remote. On Windows the
    audit event carries the command line ``list2cmdline`` built; it is split back on its
    double quotes. Anything not understood is not read-only."""
    if isinstance(argv, bytes):
        return False
    try:
        if isinstance(argv, str):
            split = shlex.split(argv, posix=False)
            words = [w[1:-1] if w[:1] == w[-1:] == '"' else w for w in split]
        else:
            words = [os.fsdecode(w) for w in argv]
    except (TypeError, ValueError):
        return False
    if not words:
        return False
    if os.path.splitext(re.split(r"[\\/]", words[0])[-1])[0].lower() != "git":
        return False
    i = 1
    while i < len(words) and words[i].startswith("-"):
        i += 2 if words[i] in ("-c", "-C") else 1  # global options before the subcommand
    if i >= len(words):
        return False
    verb, rest = words[i], words[i + 1 :]
    if verb in _READ_ONLY_GIT:
        return True
    if verb == "config":
        return bool({"--get", "--get-all", "--get-regexp", "--list", "-l"} & set(rest))
    if verb == "remote":
        return rest in ([], ["-v"], ["--verbose"]) or rest[:1] == ["get-url"]
    if verb == "branch":
        writes = {"-d", "-D", "-m", "-M", "-c", "-C", "-f", "-u", "--delete", "--move", "--copy"}
        reads = {"--list", "--show-current"}
        return bool(reads & set(rest)) and not writes & set(rest)
    if verb == "symbolic-ref":
        return not {"-d", "--delete"} & set(rest) and len([w for w in rest if w[:1] != "-"]) == 1
    return False


def _on_audit(event: str, args: tuple) -> None:
    global _generation
    if event in _PROCESS_EVENTS and not (event == "subprocess.Popen" and _reads_only(args[1])):
        _generation += 1


sys.addaudithook(_on_audit)


def _key(root: Path, *what: object) -> tuple:
    return (
        *what,
        os.path.realpath(root),
        os.environ.get("GIT_DIR"),
        os.environ.get("GIT_WORK_TREE"),
    )


def remembered(root: Path, what: tuple, ask):
    """``ask()``'s answer for ``what`` in ``root``, asked again once the process has started
    anything but a read-only git query since it was last asked. An exception is not
    remembered."""
    key = _key(root, *what)
    hit = _remembered.get(key)
    if hit is not None and hit[0] == _generation:
        return hit[1]
    generation = _generation
    answer = ask()
    if generation == _generation:  # nothing changed the checkout while it was asked
        _remembered[key] = (generation, answer)
    return answer


_NO_HOOKS_DIR: str | None = None


def runner_args() -> list[str]:
    """Global git options for a runner (``GITHUB_ACTIONS`` set), else []: the checkout is
    shared with the model's session, which holds ``Bash(git *)`` and could plant a hook
    (``.git/hooks/pre-commit``, ``core.hooksPath``) or an ``fsmonitor`` command that a later
    step's ``git commit`` or ``git push`` would run with that step's environment (session-8
    review). ``core.hooksPath`` points at an empty directory of this process and the
    filesystem monitor is off. R44 (the plugin security review of 2026-10-19, I4) adds the
    global attributes file off, signing off and no external diff, so a ``commit.gpgSign``
    with a ``gpg.program`` or a ``diff.external`` the session wrote runs nothing;
    ``refuse_planted_config`` refuses the keys these options cannot reach (a ``filter``
    driver named in the checkout's own ``.gitattributes``). By hand nothing changes: the
    owner's own hooks run."""
    global _NO_HOOKS_DIR
    if not os.environ.get("GITHUB_ACTIONS"):
        return []
    if _NO_HOOKS_DIR is None or not os.path.isdir(_NO_HOOKS_DIR):
        _NO_HOOKS_DIR = tempfile.mkdtemp(prefix="sdlc-no-hooks-")
    return [
        "-c", f"core.hooksPath={_NO_HOOKS_DIR}", "-c", "core.fsmonitor=false",
        "-c", f"core.attributesFile={os.devnull}", "-c", "commit.gpgSign=false",
        "-c", "tag.gpgSign=false", "-c", "diff.external=",
        # the review of 1.0.25: a replace ref the session wrote (.git/refs/replace/) made a
        # worktree of the approved commit check out another tree, and the diff readers see
        # no change; the push never carries a replacement, so the runner reads past them
        "--no-replace-objects",
    ]  # fmt: skip


# git-lfs's own filter, as ``git lfs install --local`` writes it (``actions/checkout`` with
# ``lfs: true``): judged by its value, so an LFS project keeps working (the review of 1.0.25)
LFS_FILTER = re.compile(r"^filter\.lfs\.(clean|smudge|process)$")
LFS_VALUE = re.compile(r"^git-lfs (clean|smudge|filter-process)( -- %f)?$")


def _planted(root: Path) -> tuple[str, ...]:
    """``refuse_planted_config``'s findings: the program-running keys but git-lfs's own
    filter, and a ``.git/info/grafts`` file (which rewrites history as a replace ref does)."""
    from ci import checkout_check  # noqa: PLC0415

    found: list[str] = []
    for scope, name in checkout_check.config_findings(root, checkout_check.PROGRAM_SCOPES):
        if scope == checkout_check.UNLISTED:
            found.append(name)
            continue
        if LFS_FILTER.match(name.lower()):
            code, value = checkout_check.git(root, "config", f"--{scope}", "--get", name)
            if code == 0 and LFS_VALUE.match(value.strip()):
                continue
        found.append(f"git config {scope} carries {name}")
    code, common = checkout_check.git(root, "rev-parse", "--git-common-dir")
    if code == 0 and (root / common.strip() / "info" / "grafts").exists():
        found.append(".git/info/grafts exists")
    return tuple(found)


def refuse_planted_config(root: Path | str) -> None:
    """On a runner (``GITHUB_ACTIONS`` set), raise ``GitError`` when the git config as git
    resolves it in ``root`` carries a key that makes git run a program (``ci/checkout_check.py
    RUNS_PROGRAM``: a ``filter.<x>.clean``, a ``gpg.program``, an alias, a conditional
    include...; the redirect keys stay ``ci/app_token.py``'s, which switches to the workflow
    token). The checkout is shared with the model's session, which holds ``Bash(git *)`` and
    unscoped ``Write``; the runner's own ``git add`` and ``git commit`` after the session
    would run a planted filter outside the sandbox with every credential of the job (R44,
    the plugin security review of 2026-10-19, I4). Asked once per generation (``remembered``):
    the model's session is a process start, so its end asks again. By hand nothing is
    judged: the owner's own config is theirs."""
    if not os.environ.get("GITHUB_ACTIONS"):
        return
    keep = sys.dont_write_bytecode  # checkout_check turns it off for its own fresh checkout
    from ci import checkout_check  # noqa: F401, PLC0415 - stdlib only; ci imports state

    sys.dont_write_bytecode = keep
    found = remembered(Path(root), ("planted-config",), lambda: _planted(Path(root)))
    if found:
        raise GitError(
            "the checkout's git config was changed in a way the runner refuses to run git "
            "under (R44, I4): " + "; ".join(found)
        )


# the git commands that reach the remote, and so take a credential
NETWORK_COMMANDS = ("push", "fetch", "pull", "ls-remote", "clone")


def network_env(
    args: tuple[str, ...] | list[str], root: Path | str | None = None
) -> dict[str, str] | None:
    """The environment of a git call in ``root``: for a network command on a runner, the
    process's own plus the credential in git's command-scope config (``ci/app_token.py
    git_auth_env``, which judges ``root``'s git config before handing out the App's token;
    decision 33, R49: no checkout persists one in ``.git/config``); None otherwise (the
    process's own, unchanged)."""
    if not args or args[0] not in NETWORK_COMMANDS:
        return None
    from ci import app_token  # noqa: PLC0415 - stdlib only

    auth = app_token.git_auth_env(root=root)
    return {**os.environ, **auth} if auth else None


def run(root: Path, *args: str, check: bool = True) -> str:
    refuse_planted_config(root)
    proc = subprocess.run(
        ["git", *runner_args(), *args],
        cwd=str(root),
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=network_env(args, root),
    )
    if check and proc.returncode != 0:
        raise GitError(f"git {' '.join(args)} failed: {proc.stderr.strip() or proc.stdout}")
    return proc.stdout


def is_repo(root: Path) -> bool:
    """``root`` is inside a git work tree. A yes is remembered with the git directory git
    named, and stands while that directory exists; a no is always asked again (a later
    ``git init`` makes it a yes)."""
    key = _key(root)
    git_dir = _repos.get(key)
    if git_dir and os.path.exists(git_dir):
        return True
    try:
        out = run(root, "rev-parse", "--is-inside-work-tree", "--absolute-git-dir").split("\n")
    except (GitError, FileNotFoundError):
        return False
    if out[0].strip() != "true":
        return False
    if len(out) > 1 and out[1].strip():
        _repos[key] = out[1].strip()
    return True


def current_branch(root: Path) -> str:
    return run(root, "rev-parse", "--abbrev-ref", "HEAD").strip()


def ref_exists(root: Path, ref: str) -> bool:
    """``git rev-parse --verify --quiet <ref>`` names a commit (remembered, see above)."""
    return remembered(
        root,
        ("ref_exists", ref),
        lambda: bool(run(root, "rev-parse", "--verify", "--quiet", ref, check=False).strip()),
    )


def explicit_default_branch() -> str | None:
    """``SDLC_DEFAULT_BRANCH`` when non-empty and not a framework branch name, else None.

    A value that parses as ``sdlc/<id>/<phase>`` (or starts with ``sdlc/``) is refused: the
    default branch is never one of the framework's own branches, and naming one would make
    the dispatcher judge by a PR head's bands.yaml and sdlc.yaml (decision 14)."""
    value = os.environ.get(DEFAULT_BRANCH_ENV, "").strip()
    if not value or value.startswith("sdlc/") or conventions.parse_branch(value):
        return None
    return value


def default_branch(root: Path) -> str:
    """``SDLC_DEFAULT_BRANCH`` when set to an acceptable name (``explicit_default_branch``),
    else origin/HEAD if set, else the remote-tracking origin/main or origin/master, else a
    local main or master, else the current branch.

    The remote-tracking step comes from the live run of 2026-09-25 (sdlc-sample-python,
    actions run 36165497264): ``actions/checkout`` with ``fetch-depth: 0`` on a non-default
    ref sets no ``refs/remotes/origin/HEAD`` and creates no local default branch, only the
    remote-tracking refs. Without this step the guess fell through to the current branch
    (``shakedown/detect``), and an incident branch started from it. The runbook and abandon
    workflows check out the PR head ``sdlc/<id>/a``, so the workflows name the branch
    explicitly and the explicit value wins over the guess."""
    explicit = explicit_default_branch()
    if explicit:
        return explicit
    return remembered(root, ("default_branch",), lambda: _guess_default_branch(root))


def origin_head(root: Path) -> str | None:
    """The ref ``refs/remotes/origin/HEAD`` points at, None when it is not set (remembered,
    and shared with gate/diff.py's ``default_base``)."""

    def ask() -> str | None:
        try:
            return run(root, "symbolic-ref", "refs/remotes/origin/HEAD").strip()
        except GitError:
            return None

    return remembered(root, ("origin_head",), ask)


def _guess_default_branch(root: Path) -> str:
    ref = origin_head(root)
    if ref is not None:
        prefix = "refs/remotes/origin/"
        return ref[len(prefix) :] if ref.startswith(prefix) else ref.rsplit("/", 1)[-1]
    for cand in ("main", "master"):
        if ref_exists(root, f"refs/remotes/origin/{cand}"):
            return cand
    for cand in ("main", "master"):
        if run(root, "branch", "--list", cand).strip():
            return cand
    return current_branch(root)


def checkout_branch(root: Path, branch: str, start_point: str | None = None) -> None:
    """Create the branch if missing (from start_point or HEAD), then switch to it."""
    if branch.startswith("-") or (start_point and start_point.startswith("-")):
        raise GitError("branch and start point must not look like options")
    exists = bool(run(root, "branch", "--list", "--", branch).strip())
    if exists:
        run(root, "checkout", branch)
    elif start_point:
        run(root, "checkout", "-b", branch, start_point)
    else:
        run(root, "checkout", "-b", branch)


def staged_files(root: Path) -> list[str]:
    out = run(root, "diff", "--cached", "--name-only", "--diff-filter=ACMRD")
    return [line.strip().replace("\\", "/") for line in out.splitlines() if line.strip()]


def stage_paths(root: Path, paths: list[str]) -> list[str]:
    """Stage the given paths; returns everything now staged (the whole index).

    Kept for callers that want the whole index; ``commit-phase`` goes through
    ``changed_files`` and ``commit_files`` instead, which never sweep in what was staged
    beforehand."""
    run(root, "add", "--", *paths)
    return staged_files(root)


def commit_staged(root: Path, message: str) -> str:
    """Commit the whole index (whatever was staged, by whom). Prefer ``commit_files``."""
    run(root, *identity_args(root), "commit", "-q", "-m", message)  # see commit_files
    return run(root, "rev-parse", "HEAD").strip()


def _toplevel(root: Path) -> Path:
    """The work tree's top: ``git status --porcelain`` names paths relative to it."""
    return Path(run(root, "rev-parse", "--show-toplevel").strip())


def _norm(path: str) -> str:
    return path.replace("\\", "/")


def _porcelain(root: Path, paths: list[str]) -> list[tuple[str, str, str | None]]:
    """``(XY, path, original path of a rename or copy)`` for every change under ``paths``.

    ``git status --porcelain=v1 -z`` writes one ``XY <path>`` record per NUL, and a rename
    or copy (``R`` or ``C`` in either column) is followed by one more record holding the
    original path. Paths are relative to the top of the work tree, forward slashes on every
    platform; untracked files are listed one by one (``--untracked-files=all``) and ignored
    files not at all.
    """
    out = run(
        root,
        "--literal-pathspecs",
        "status",
        "--porcelain=v1",
        "-z",
        "--untracked-files=all",
        "--",
        *[_norm(p) for p in paths],
    )
    records = out.split("\0")
    entries: list[tuple[str, str, str | None]] = []
    i = 0
    while i < len(records):
        rec = records[i]
        i += 1
        if len(rec) < 4:
            continue  # the empty tail after the last NUL
        xy, path = rec[:2], _norm(rec[3:])
        orig = None
        if "R" in xy or "C" in xy:
            orig = _norm(records[i]) if i < len(records) else None
            i += 1
        entries.append((xy, path, orig))
    return entries


def changed_files(root: Path, paths: list[str]) -> list[str]:
    """The concrete files that changed under ``paths``: modified, added, deleted, renamed
    (both sides) and untracked, relative to the top of the work tree, sorted. A path that
    matches nothing contributes nothing (no error, unlike ``git add``)."""
    if not paths:
        return []
    files: set[str] = set()
    for xy, path, orig in _porcelain(root, paths):
        files.add(path)
        if orig and "R" in xy:  # a copy leaves its source untouched; a rename removes it
            files.add(orig)
    return sorted(files)


def commit_files(root: Path, files: list[str], message: str) -> str | None:
    """Stage exactly ``files`` and commit only them. Returns the new SHA, or None when none
    of them differs from HEAD.

    ``git add -- <files>`` records modifications, new files and deletions alike (git 2.x);
    a file whose deletion or rename is already staged is gone from both the index and the
    work tree, so it is not handed to ``git add`` (which would fail on it) but still goes
    into the commit. ``git commit --only -- <files>`` then commits those paths alone: a file
    staged beforehand by a hook, an earlier partial command or the session stays staged and
    out of the commit. Literal pathspecs throughout, so a name with ``*`` or ``[`` is a name.
    """
    if not files:
        return None
    top = _toplevel(root)
    files = sorted({_norm(f) for f in files})
    addable = [f for f in files if (top / f).exists() or _in_index(top, f)]
    if addable:
        run(top, "--literal-pathspecs", "add", "--", *addable)
    out = run(
        top,
        "--literal-pathspecs",
        "diff",
        "--cached",
        "--name-only",
        "-z",
        "--no-renames",
        "--",
        *files,
    )
    to_commit = sorted({_norm(f) for f in out.split("\0") if f})
    if not to_commit:
        return None
    # every commit the plugin makes goes through here: a runner has no git identity, and the
    # detect step's ``commit-phase`` failed on one with "empty ident name" (live run of
    # 2026-09-25). identity_args names the automation identity for this one commit when none
    # is set, and writes nothing into .git/config: on an owner's machine a persisted bot
    # identity would sign every later commit of theirs.
    run(
        top,
        *identity_args(top),
        "--literal-pathspecs",
        "commit",
        "-q",
        "-m",
        message,
        "--only",
        "--",
        *to_commit,
    )
    return run(top, "rev-parse", "HEAD").strip()


def _in_index(top: Path, rel: str) -> bool:
    return bool(
        run(top, "--literal-pathspecs", "ls-files", "-z", "--cached", "--", rel).strip("\0")
    )


def commit_paths(root: Path, paths: list[str], message: str) -> str | None:
    """Commit what changed under ``paths`` and nothing else (``changed_files`` then
    ``commit_files``). Returns the new SHA, or None when nothing under them changed."""
    return commit_files(root, changed_files(root, paths), message)


# The automation identity of OPERATING_MODEL section 2 (the CI workflow token); a runner has
# no git identity of its own, and a commit needs one.
BOT_LOGIN = "github-actions[bot]"
BOT_EMAIL = "41898282+github-actions[bot]@users.noreply.github.com"


def _has_identity(root: Path) -> bool:
    have_name = run(root, "config", "--get", "user.name", check=False).strip()
    have_email = run(root, "config", "--get", "user.email", check=False).strip()
    return bool(have_name and have_email)


def identity_args(root: Path) -> list[str]:
    """``-c user.name=... -c user.email=...`` of the automation identity when the checkout
    has no user.name or user.email, else []. Passed before a ``git commit``; unlike
    ``ensure_identity`` it writes nothing into the repository's configuration."""
    if _has_identity(root):
        return []
    return ["-c", f"user.name={BOT_LOGIN}", "-c", f"user.email={BOT_EMAIL}"]


def ensure_identity(root: Path, name: str = BOT_LOGIN, email: str = BOT_EMAIL) -> str | None:
    """Give the checkout ``name``/``email`` when it has no user.name or user.email; returns
    the name when it was set, None when the checkout already had one."""
    if _has_identity(root):
        return None
    run(root, "config", "user.name", name)
    run(root, "config", "user.email", email)
    return name


def push(root: Path, branch: str, remote: str = "origin") -> None:
    run(root, "push", "-u", remote, branch)


def has_remote(root: Path, remote: str = "origin") -> bool:
    return remote in run(root, "remote").split()


def remote_url(root: Path, remote: str = "origin") -> str | None:
    try:
        return run(root, "remote", "get-url", remote).strip()
    except GitError:
        return None


def github_repo(root: Path, remote: str = "origin") -> str | None:
    """'owner/repo' from an https or ssh GitHub remote URL, else None."""
    url = remote_url(root, remote)
    if not url:
        return None
    m = re.match(
        r"^(?:https?://(?:[^@/]+@)?github\.com/|git@github\.com:|ssh://git@github\.com/)"
        r"([\w.-]+)/([\w.-]+?)(?:\.git)?/?$",
        url.strip(),
    )
    return f"{m.group(1)}/{m.group(2)}" if m else None


def remote_change_ids(root: Path, remote: str = "origin") -> list[str]:
    """Change ids that already have sdlc/<id>/* branches on the remote (best effort)."""
    try:
        out = run(root, "ls-remote", "--heads", remote, "refs/heads/sdlc/*")
    except (GitError, FileNotFoundError):
        return []
    ids = set()
    for line in out.splitlines():
        parts = line.split("refs/heads/sdlc/")
        if len(parts) == 2:
            ids.add(parts[1].split("/")[0])
    return sorted(i for i in ids if i.isdigit() and len(i) == 4)
