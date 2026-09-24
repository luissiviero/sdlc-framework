"""Thin git helpers used by the phase commands. Argument lists only (no shell) so the same
code runs on Windows, in a cloud session and on a Linux runner."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path


class GitError(RuntimeError):
    pass


def run(root: Path, *args: str, check: bool = True) -> str:
    proc = subprocess.run(
        ["git", *args], cwd=str(root), capture_output=True, text=True, encoding="utf-8"
    )
    if check and proc.returncode != 0:
        raise GitError(f"git {' '.join(args)} failed: {proc.stderr.strip() or proc.stdout}")
    return proc.stdout


def is_repo(root: Path) -> bool:
    try:
        return run(root, "rev-parse", "--is-inside-work-tree").strip() == "true"
    except (GitError, FileNotFoundError):
        return False


def current_branch(root: Path) -> str:
    return run(root, "rev-parse", "--abbrev-ref", "HEAD").strip()


def default_branch(root: Path) -> str:
    """origin/HEAD if set, else main/master if they exist, else the current branch."""
    try:
        ref = run(root, "symbolic-ref", "refs/remotes/origin/HEAD").strip()
        prefix = "refs/remotes/origin/"
        return ref[len(prefix) :] if ref.startswith(prefix) else ref.rsplit("/", 1)[-1]
    except GitError:
        pass
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
    run(root, "commit", "-q", "-m", message)
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
    run(top, "--literal-pathspecs", "commit", "-q", "-m", message, "--only", "--", *to_commit)
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


def ensure_identity(root: Path, name: str = BOT_LOGIN, email: str = BOT_EMAIL) -> str | None:
    """Give the checkout ``name``/``email`` when it has no user.name or user.email; returns
    the name when it was set, None when the checkout already had one."""
    have_name = run(root, "config", "--get", "user.name", check=False).strip()
    have_email = run(root, "config", "--get", "user.email", check=False).strip()
    if have_name and have_email:
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
