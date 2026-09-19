"""Thin git helpers used by the phase commands. Argument lists only (no shell) so the same
code runs on Windows, in a cloud session and on a Linux runner."""

from __future__ import annotations

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
        return ref.rsplit("/", 1)[-1]
    except GitError:
        pass
    for cand in ("main", "master"):
        if run(root, "branch", "--list", cand).strip():
            return cand
    return current_branch(root)


def checkout_branch(root: Path, branch: str, start_point: str | None = None) -> None:
    """Create the branch if missing (from start_point or HEAD), then switch to it."""
    exists = bool(run(root, "branch", "--list", branch).strip())
    if exists:
        run(root, "checkout", branch)
    elif start_point:
        run(root, "checkout", "-b", branch, start_point)
    else:
        run(root, "checkout", "-b", branch)


def staged_files(root: Path) -> list[str]:
    out = run(root, "diff", "--cached", "--name-only", "--diff-filter=ACMRD")
    return [line.strip().replace("\\", "/") for line in out.splitlines() if line.strip()]


def commit_paths(root: Path, paths: list[str], message: str) -> str | None:
    """Stage the given paths and commit. Returns the new SHA, or None when nothing changed."""
    run(root, "add", "--", *paths)
    if not staged_files(root):
        return None
    run(root, "commit", "-q", "-m", message)
    return run(root, "rev-parse", "HEAD").strip()


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
    if not url or "github.com" not in url:
        return None
    tail = url.split("github.com", 1)[1].lstrip(":/")
    if tail.endswith(".git"):
        tail = tail[:-4]
    parts = tail.strip("/").split("/")
    return "/".join(parts[:2]) if len(parts) >= 2 else None
