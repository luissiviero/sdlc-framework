"""What the change has changed: the branch's diff against its base and the commits on it.

Argument lists only (no shell). The diff is the working tree plus untracked files against
the merge base with the base ref, so a gate run right after the phase committed and a run
with uncommitted leftovers see the same thing the PR would show.
"""

from __future__ import annotations

import os
import stat
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

from state import gitops


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
    records = out.split("\0")
    i = 0
    while i < len(records):
        entry = records[i]
        i += 1
        if len(entry) <= 3:
            continue
        files.append(entry[3:].replace("\\", "/"))
        if "R" in entry[:2] or "C" in entry[:2]:
            # a rename or copy is followed by one more record, the original path, with
            # no status prefix (the review of the 0.3.4 diff, finding 6)
            if i < len(records) and records[i]:
                files.append(records[i].replace("\\", "/"))
            i += 1
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


# Claude Code's sandbox masks these paths inside the sandbox: a run that looks at the working
# directory from in there sees the project's own ``.env`` as modified and ``.idea``/``.vscode``
# as untracked, whatever the checkout really holds (observed on 2026-09-21, third live design
# run: the gate parked on ``.env, .idea, .vscode`` while the committed diff was clean). The
# mask is the sandbox's, not the run's: no phase writes these, a modification of ``.env``
# cannot come from a run at all (the CI settings deny reading it, and the guardrail and
# secrets checks cover it), so the gate looks past them wherever it happens to run. Names
# only: they are matched at the root of the checkout, so a project's own ``src/.env`` is
# untouched here — what the sandbox masks deeper down is found by its mounts instead
# (``sandbox_mounted``, 0.3.4).
SANDBOX_MASKED = frozenset(
    {
        ".env",
        ".idea",
        ".vscode",
        ".bash_profile",
        ".bashrc",
        ".gitconfig",
        ".gitmodules",
        ".mcp.json",
        ".profile",
        ".ripgreprc",
        ".zprofile",
        ".zshrc",
    }
)


def sandbox_masked(files: list[str]) -> list[str]:
    """The entries of ``files`` that sit under a root-level ``SANDBOX_MASKED`` name.

    Size and tracked state do not matter here (a tracked ``.env`` shows up as modified, an
    untracked ``.idea`` as one entry or as the files below it): the entry is the sandbox's
    view, not the change's.
    """
    return sorted({f for f in files if f.split("/", 1)[0] in SANDBOX_MASKED})


# Claude Code's sandbox enforces the settings' read denials (``Read(**/.env*)``,
# ``Read(**/secrets/**)``, …) at any depth by mounting over the paths: ``/dev/null`` bound
# over a file, a tmpfs over a directory. To git inside the session a tracked file so masked
# is modified (a character device where a regular file was) and a tracked file under a
# masked directory is deleted; neither is the session's work. Change 0001's second build
# run on 0.3.3 (2026-10-03, run 37138722554) parked gate (c) on ``clean_tree`` for this
# repository's fixture ``tests/fixtures/sample-python-project/.env`` with every other check
# green. The mount is what identifies the mask (``os.path.ismount``: the entry's device
# differs from its parent's), and the mount alone: a character device by itself is not a
# mask, because a session can make one with ``os.mknod`` (a 0:0 device needs no privilege
# on current kernels — the review of the 0.3.4 diff reproduced it as an unprivileged user —
# and ``git status`` then reads a tracked file or directory it replaced as modified or
# deleted, while pytest skips the device). ``lstat`` needs no read access, so the signal is
# readable inside the sandbox; the caller applies it inside a CI session only (``checks``),
# because on an owner's machine or in a dev container a volume over a tracked directory
# is nobody's mask.
def _mount_masked(path: Path) -> bool:
    """Whether ``path`` is what the sandbox put there: a mount point whose entry is a
    character device (``/dev/null`` bound over a file) or a directory (a tmpfs)."""
    try:
        if not os.path.ismount(path):
            return False
        mode = os.lstat(path).st_mode
        return stat.S_ISCHR(mode) or stat.S_ISDIR(mode)
    except OSError:
        return False


def sandbox_mounted(root: Path, files: list[str]) -> list[str]:
    """The entries of ``files`` that the sandbox masks by a mount: the entry itself, or a
    directory above it inside ``root`` (a tracked file under a masked directory); the root
    itself is never tested. One ``lstat`` walk per directory, cached across the entries."""
    root = Path(root)
    seen: dict[str, bool] = {}
    out = []
    for f in files:
        parts = f.rstrip("/").split("/")
        for depth in range(len(parts), 0, -1):
            key = "/".join(parts[:depth])
            if key not in seen:
                seen[key] = _mount_masked(root.joinpath(*parts[:depth]))
            if seen[key]:
                out.append(f)
                break
    return sorted(set(out))


def committed_files(root: Path, merge_base: str | None, head: str | None = None) -> list[str]:
    """The files the branch carries: ``git diff --name-only <merge_base>...HEAD``.

    This is the PR's own diff — what a reviewer sees and what merges. The working tree says
    nothing here: a checkout can be dirty for reasons that have nothing to do with the change
    (see ``SANDBOX_MASKED``), and a phase that commits its work is judged on the commits.
    """
    if not merge_base:
        return []
    ref = f"{merge_base}...{head or 'HEAD'}"
    return _z(_git(root, "diff", "--name-only", "-z", "--diff-filter=ACMRD", ref, check=False))


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
    """``refs/remotes/origin/<default branch>`` when the remote has one, else main/master
    locally. The remote-tracking ref is fully qualified (0.2.27): git resolves a tag named
    ``origin/main`` before the short remote ref, and a tag pushed by anyone with write
    access reaches every later CI checkout (``fetch-depth: 0``), where the short form then
    emptied the committed diff the checks and the runner's guard judge.

    ``SDLC_DEFAULT_BRANCH`` (refused when it names a framework branch, see
    ``gitops.explicit_default_branch``) wins when ``refs/remotes/origin/<value>`` resolves."""
    explicit = gitops.explicit_default_branch()
    if explicit:
        ref = f"refs/remotes/origin/{explicit}"
        if _git(root, "rev-parse", "--verify", "--quiet", ref, check=False).strip():
            return ref
    try:
        ref = _git(root, "symbolic-ref", "refs/remotes/origin/HEAD").strip()
        if ref.startswith("refs/remotes/"):
            return ref
    except GitUnavailable:
        pass
    for cand in ("refs/remotes/origin/main", "refs/remotes/origin/master", "main", "master"):
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
        # A base that shares no history with HEAD (an orphan branch, a shallow clone that
        # stopped short of the fork point): ``merge_base`` None, ``commits`` empty and
        # ``committed_files`` empty. The checks that judge the committed diff fail on it
        # (``checks._no_base``), never pass on the empty list (readiness review, group B).
        note = "" if mb else f"no merge base with {base}: the committed diff cannot be judged"
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
