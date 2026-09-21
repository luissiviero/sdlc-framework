"""What the change has changed: the branch's diff against its base and the commits on it.

Argument lists only (no shell). The diff is the working tree plus untracked files against
the merge base with the base ref, so a gate run right after the phase committed and a run
with uncommitted leftovers see the same thing the PR would show.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from pathlib import Path


class GitUnavailable(RuntimeError):
    pass


def _git(root: Path, *args: str, check: bool = True) -> str:
    try:
        proc = subprocess.run(
            ["git", *args],
            cwd=str(root),
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=60,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise GitUnavailable(f"git {' '.join(args)}: {exc!r}") from exc
    if check and proc.returncode != 0:
        raise GitUnavailable(f"git {' '.join(args)} failed: {proc.stderr.strip() or proc.stdout}")
    return proc.stdout


def _z(out: str) -> list[str]:
    return sorted({f.replace("\\", "/") for f in out.split("\0") if f})


@dataclass
class Commit:
    sha: str
    files: list[str] = field(default_factory=list)


@dataclass
class Diff:
    base: str
    merge_base: str | None
    head: str | None
    files: list[str] = field(default_factory=list)
    commits: list[Commit] = field(default_factory=list)
    branch: str = ""
    note: str = ""

    def as_dict(self) -> dict:
        return {
            "base": self.base,
            "merge_base": self.merge_base,
            "head": self.head,
            "branch": self.branch,
            "files": self.files,
            "commits": [{"sha": c.sha, "files": c.files} for c in self.commits],
            "note": self.note,
        }


def file_at(root: Path, ref: str | None, rel: str) -> str | None:
    """The committed content of ``rel`` at ``ref`` (None when absent there or no ref)."""
    if not ref or not _cat_ok(root, ref, rel):
        return None
    return _git(root, "show", f"{ref}:{rel}", check=False)


def _cat_ok(root: Path, ref: str, rel: str) -> bool:
    try:
        proc = subprocess.run(
            ["git", "cat-file", "-e", f"{ref}:{rel}"],
            cwd=str(root),
            capture_output=True,
            text=True,
            timeout=60,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    return proc.returncode == 0


def dirty_files(root: Path) -> list[str]:
    """Paths with uncommitted changes (modified, staged or untracked), forward slashes."""
    out = _git(root, "status", "--porcelain", "-z", "--untracked-files=all", check=False)
    files = []
    for entry in out.split("\0"):
        if len(entry) > 3:
            files.append(entry[3:].replace("\\", "/"))
    return sorted(set(files))


def is_repo(root: Path) -> bool:
    try:
        return _git(root, "rev-parse", "--is-inside-work-tree").strip() == "true"
    except GitUnavailable:
        return False


def head_sha(root: Path) -> str | None:
    try:
        return _git(root, "rev-parse", "HEAD").strip()
    except GitUnavailable:
        return None


def default_base(root: Path) -> str:
    """origin/<default branch> when the remote has one, else main/master locally."""
    try:
        ref = _git(root, "symbolic-ref", "refs/remotes/origin/HEAD").strip()
        if ref.startswith("refs/remotes/"):
            return ref[len("refs/remotes/") :]
    except GitUnavailable:
        pass
    for cand in ("origin/main", "origin/master", "main", "master"):
        if _git(root, "rev-parse", "--verify", "--quiet", cand, check=False).strip():
            return cand
    return "HEAD"


def collect(root: Path, base: str | None = None) -> Diff:
    root = Path(root)
    if not is_repo(root):
        raise GitUnavailable(f"{root} is not a git repository")
    base = base or default_base(root)
    head = head_sha(root)
    branch = _git(root, "rev-parse", "--abbrev-ref", "HEAD", check=False).strip()
    if base == "HEAD" or head is None:
        merge_base = head
        note = "no base branch found: only uncommitted changes are in the diff"
    else:
        mb = _git(root, "merge-base", base, "HEAD", check=False).strip()
        merge_base = mb or None
        note = "" if mb else f"no merge base with {base}: comparing against HEAD"
    ref = merge_base or "HEAD"
    files = _z(_git(root, "diff", "--name-only", "-z", "--diff-filter=ACMRD", ref, check=False))
    files = sorted(
        set(files) | set(_z(_git(root, "ls-files", "-z", "--others", "--exclude-standard")))
    )
    commits: list[Commit] = []
    if merge_base and head and merge_base != head:
        for sha in _git(root, "rev-list", "--reverse", f"{merge_base}..HEAD").split():
            changed = _z(_git(root, "diff-tree", "--no-commit-id", "--name-only", "-r", "-z", sha))
            commits.append(Commit(sha, changed))
    return Diff(base, merge_base, head, files, commits, branch, note)
