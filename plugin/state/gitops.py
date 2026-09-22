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
    """Stage the given paths; returns everything now staged."""
    run(root, "add", "--", *paths)
    return staged_files(root)


def commit_staged(root: Path, message: str) -> str:
    run(root, "commit", "-q", "-m", message)
    return run(root, "rev-parse", "HEAD").strip()


def commit_paths(root: Path, paths: list[str], message: str) -> str | None:
    """Stage the given paths and commit. Returns the new SHA, or None when nothing changed."""
    if not stage_paths(root, paths):
        return None
    return commit_staged(root, message)


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
