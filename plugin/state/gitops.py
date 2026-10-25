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
# audit hook below sees the process starts made through ``subprocess``, ``os.system``,
# ``os.exec*``, ``os.spawn*``, ``os.posix_spawn``, ``os.startfile`` and ``os.fork*`` (a
# fork's child may run git), whoever makes them, and moves the generation on, counted at the
# start only; a remembered answer of an older generation is asked again. Code that starts
# processes another way (``multiprocessing`` with ``spawn`` or ``forkserver`` raises none of
# these events), or reads while a child it started still runs, must not rely on the
# remembered answers (choice 239). A remote's answer (``ls-remote``) is never remembered:
# the id reservation reads it fresh each time (R51). is_repo keeps a yes for good,
# re-checked by a stat that the git directory it found still exists.
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
# the long global options that also take their value as the next word (``--git-dir x``)
_SEPARATE_VALUE_OPTIONS = frozenset(
    {"--git-dir", "--work-tree", "--namespace", "--super-prefix", "--config-env", "--attr-source"}
)
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
        if words[i] in _SEPARATE_VALUE_OPTIONS:
            return False  # its value may be a read verb: not understood (choice 239)
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
        # the review of 1.0.27: a replace ref the session wrote (.git/refs/replace/) made a
        # worktree of the approved commit check out another tree, and the diff readers see
        # no change; the push never carries a replacement, so the runner reads past them
        "--no-replace-objects",
    ]  # fmt: skip


# git-lfs's own filter, as ``git lfs install --local`` writes it (``actions/checkout`` with
# ``lfs: true``): judged by its value, so an LFS project keeps working (the review of 1.0.27)
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


def run_proc(root: Path, *args: str) -> subprocess.CompletedProcess:
    """``git <args>`` in ``root``, its exit code and both streams; ``run`` raises on a
    non-zero exit instead. A local read-only query is bounded by ``READ_TIMEOUT_SECONDS``;
    a network command is not (a sign-in by Git Credential Manager can take longer, and the
    bound kills git, not its remote helper). A push reports in English (``LC_ALL=C``):
    ``reserve_change_id`` and ``push`` read git's refusal reasons, which git translates
    (the independent review of the R51 PR, findings 7 and 8)."""
    refuse_planted_config(root)  # R44, I4: no runner git call under a planted program
    env = network_env(args, root)
    if args and args[0] == "push":
        env = {**(env if env is not None else os.environ), "LC_ALL": "C", "LANGUAGE": "C"}
    local_read = _reads_only(["git", *args]) and not (args and args[0] in NETWORK_COMMANDS)
    try:
        return subprocess.run(
            ["git", *runner_args(), *args],
            cwd=str(root),
            capture_output=True,
            text=True,
            encoding="utf-8",
            env=env,
            timeout=READ_TIMEOUT_SECONDS if local_read else None,
        )
    except subprocess.TimeoutExpired as exc:
        raise GitError(f"git {' '.join(args)} timed out after {exc.timeout:g} s") from exc


# a local read-only query that hangs (a slow network filesystem, an ``fsmonitor`` command by
# hand) fails closed after this long, as gate/diff.py's own calls did before 1.0.13 (choice
# 239); a network command, a push or a commit keeps the job's own bound
READ_TIMEOUT_SECONDS = 60


def run(root: Path, *args: str, check: bool = True) -> str:
    proc = run_proc(root, *args)
    if check and proc.returncode != 0:
        raise GitError(f"git {' '.join(args)} failed: {proc.stderr.strip() or proc.stdout}")
    return proc.stdout


def is_repo(root: Path) -> bool:
    """``root`` is inside a git work tree. A yes is remembered with the git directory git
    named and the work tree's ``.git`` entry, and stands while both exist; a no is always
    asked again (a later ``git init`` makes it a yes). The ``.git`` entry is what a linked
    worktree removed without ``git worktree remove`` loses while its git directory, under the
    main checkout's, stays (choice 239); a ``GIT_DIR`` checkout has none and keeps the git
    directory's stat alone."""
    key = _key(root)
    known = _repos.get(key)
    if known and all(os.path.exists(p) for p in known):
        return True
    try:
        out = run(
            root, "rev-parse", "--is-inside-work-tree", "--absolute-git-dir", "--show-toplevel"
        ).split("\n")
    except (GitError, FileNotFoundError):
        return False
    if out[0].strip() != "true":
        return False
    if len(out) > 1 and out[1].strip():
        paths = [out[1].strip()]
        top = out[2].strip() if len(out) > 2 else ""
        if top and not os.environ.get("GIT_DIR"):
            paths.append(os.path.join(top, ".git"))
        _repos[key] = tuple(paths)
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


def existing_branch(root: Path, candidates: tuple[str, ...] | list[str]) -> str:
    """The first of ``candidates`` (``conventions.branch_names``: the phase name's branch,
    then the letter's) that exists locally or on ``origin``, else the first. R45: a change in
    flight when its project moved past plugin 1.0.42 finishes on its letter branch, so a run
    of it checks out ``sdlc/<id>/c`` while a new change gets ``sdlc/<id>/build``."""
    for name in candidates:
        for ref in (f"refs/heads/{name}", f"refs/remotes/origin/{name}"):
            if ref_exists(root, ref):
                return name
    return candidates[0]


def only_change_folder_moved(root: Path, change_dir: Path, sha: str | None) -> bool:
    """Whether ``sha`` is HEAD, or an ancestor of HEAD from which only ``change_dir`` moved:
    the rule a fix round's head check (``ci/auto_round.head_matches``) and the PR body's
    stale-proof line (change 0004, R12) read. A rename's source counts as outside the folder
    (the review of 1.0.27: a file moved into the change folder is a change outside it); an
    unknown sha or an unreadable diff reads as moved."""
    if not sha or not is_repo(root):
        return False
    try:
        if run(root, "rev-parse", "HEAD").strip() == sha:
            return True
        run(root, "merge-base", "--is-ancestor", sha, "HEAD")
        changed = run(root, "diff", "--name-status", "--no-renames", sha, "HEAD")
    except (GitError, OSError):
        return False
    try:
        rel = Path(change_dir).resolve().relative_to(Path(root).resolve()).as_posix() + "/"
    except ValueError:
        return False
    paths = [line.split("\t", 1)[-1].strip() for line in changed.splitlines() if line.strip()]
    return all(path.startswith(rel) for path in paths)


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


PUSH_MERGE_MESSAGE = "merge {remote}/{branch}: the branch moved while this run worked (R51)"
_MOVED_RE = re.compile(r"\[rejected\].*\((?:non-fast-forward|fetch first)\)")


def push(root: Path, branch: str, remote: str = "origin") -> str | None:
    """Push ``branch``. A push git rejects because the remote branch moved (the owner's
    "Update branch", a by-hand commit, another run) fetches it, merges it with a merge commit
    (never a rebase or a force) and pushes once more (R51, check 12 of the race analysis).
    Returns that merge commit, None when the first push went through; a merge that conflicts
    (aborted), a second rejection or any other failure raises ``GitError``. The caller that
    judged the tree before the push re-checks the merged one."""
    proc = run_proc(root, "push", "-u", remote, branch)
    if proc.returncode == 0:
        return None
    said = f"{proc.stderr}\n{proc.stdout}".strip()
    if not _MOVED_RE.search(said):
        raise GitError(f"git push -u {remote} {branch} failed: {said}")
    tracking = f"refs/remotes/{remote}/{branch}"
    run(root, "fetch", remote, f"+refs/heads/{branch}:{tracking}")
    message = PUSH_MERGE_MESSAGE.format(remote=remote, branch=branch)
    merge = run_proc(
        root, *identity_args(root), "merge", "--no-ff", "--no-edit", "-m", message, tracking
    )
    if merge.returncode != 0:
        run(root, "merge", "--abort", check=False)
        raise GitError(
            f"git push -u {remote} {branch} was rejected (the remote branch moved) and "
            f"{tracking} does not merge: {(merge.stdout or merge.stderr).strip()[-500:]}"
        )
    run(root, "push", "-u", remote, branch)
    return run(root, "rev-parse", "HEAD").strip()


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


# --- the id reservation (R51, gap G2; NOTES §59) -------------------------------------------------
# A new id is reserved on the remote before its folder is written: ``sdlc/<id>/intent`` is
# created with a commit unique to this allocation (the default branch's tree, the default
# branch's tip as parent, a message with a random nonce), pushed with an empty lease. NOTES
# §59 shows why both halves: a push of the object a ref already holds answers "up to date"
# with exit 0 even under the lease, and a plain push of a child commit fast-forwards over a
# reservation of the tip. Only git's own rejection of the ref update counts as "taken"; any
# other failure (no write access to ``sdlc/*``, the network) leaves the id unreserved and
# says so.
RESERVED, TAKEN, UNRESERVED = "reserved", "taken", "unreserved"
RESERVE_MESSAGE = "sdlc: reserve change id {id} ({nonce}; R51)"
_TAKEN_RE = re.compile(
    r"\[rejected\].*\((?:stale info|non-fast-forward|fetch first|already exists)\)"
)


def reservation_base(root: Path, remote: str = "origin") -> str | None:
    """The commit a reservation starts from: the default branch's remote-tracking tip, else
    HEAD; None in a repository without a commit."""
    for ref in (f"refs/remotes/{remote}/{default_branch(root)}", "HEAD"):
        sha = run(root, "rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}", check=False)
        if sha.strip():
            return sha.strip()
    return None


def reserve_change_id(
    root: Path, change_id: str, base: str, remote: str = "origin"
) -> tuple[str, str | None, str]:
    """``(outcome, sha, detail)`` of reserving ``sdlc/<change_id>/a`` on ``remote``:
    ``RESERVED`` with the reservation commit, ``TAKEN`` when git refused the ref update
    because the ref exists, ``UNRESERVED`` with git's message for any other failure."""
    import secrets  # noqa: PLC0415

    nonce = secrets.token_hex(8)
    message = RESERVE_MESSAGE.format(id=change_id, nonce=nonce)
    try:
        sha = run(
            root, *identity_args(root), "commit-tree", f"{base}^{{tree}}", "-p", base,
            "-m", message,
        ).strip()  # fmt: skip
    except GitError as exc:
        return UNRESERVED, None, str(exc)
    ref = f"refs/heads/{conventions.branch_name(change_id, conventions.INTENT)}"
    try:
        proc = run_proc(root, "push", f"--force-with-lease={ref}:", remote, f"{sha}:{ref}")
    except (GitError, FileNotFoundError) as exc:
        return UNRESERVED, None, str(exc)
    text = f"{proc.stderr}\n{proc.stdout}".strip()
    if proc.returncode == 0:
        return RESERVED, sha, text
    if _TAKEN_RE.search(text):
        return TAKEN, None, text
    return UNRESERVED, None, text.splitlines()[-1] if text else f"exit {proc.returncode}"
