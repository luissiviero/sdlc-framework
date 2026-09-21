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


def untracked_files(root: Path) -> list[str]:
    """The paths git knows nothing about yet, honouring .gitignore and .git/info/exclude.

    Both listings: the files, and the untracked directories collapsed to one entry each
    (``--directory``), which is the only way an empty directory is named at all.
    """
    args = ("ls-files", "-z", "--others", "--exclude-standard")
    return sorted(
        set(_z(_git(root, *args, check=False)))
        | set(_z(_git(root, *args, "--directory", check=False)))
    )


def _holds_nothing(root: Path, rel: str) -> bool:
    """True when ``rel`` is a zero-byte file or an empty directory (never a symlink)."""
    path = Path(root) / rel
    try:
        if path.is_symlink():
            return False
        if path.is_file():
            return path.stat().st_size == 0
        if path.is_dir():
            return not any(path.iterdir())
    except OSError:
        return False
    return False


def sandbox_placeholders(root: Path, files: list[str]) -> list[str]:
    """The entries of ``files`` that are untracked and hold nothing.

    Claude Code's sandbox creates placeholder entries in the working directory (.bashrc,
    .gitconfig, .vscode and friends): they are empty, nobody wrote them and nothing commits
    them, but ``git status`` lists them as untracked, which parked the first live design run
    on 2026-09-21. An untracked file with content is a real stray and is still reported.
    """
    root = Path(root)
    untracked = set(untracked_files(root))
    return sorted(f for f in files if f in untracked and _holds_nothing(root, f))


def without_placeholders(root: Path, files: list[str]) -> list[str]:
    """``files`` without the sandbox placeholders; the order and the rest are untouched."""
    drop = set(sandbox_placeholders(root, files))
    return [f for f in files if f not in drop]


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
