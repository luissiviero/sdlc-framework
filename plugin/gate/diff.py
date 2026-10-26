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

from state import conventions as c
from state import gitops


class GitUnavailable(RuntimeError):
    pass


def _git(root: Path, *args: str, check: bool = True) -> str:
    try:
        gitops.refuse_planted_config(root)
    except gitops.GitError as exc:
        raise GitUnavailable(str(exc)) from exc
    try:
        proc = subprocess.run(
            ["git", *gitops.runner_args(), *args],
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
# run on 0.3.3 (2026-10-03, run 37138722554) parked gate (build) on ``clean_tree`` for this
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


@dataclass
class NameStatusRecord:
    """One record of ``git diff --name-status -M -z``: a status letter (``D``, ``M``, ``A``,
    or ``R``/``C`` with the percentage stripped), ``path`` (the source path, or the only path
    when it is not a rename/copy) and ``new_path`` (the destination, ``R``/``C`` only)."""

    status: str
    path: str
    new_path: str | None = None


def parse_name_status(out: str) -> list[NameStatusRecord]:
    """``git diff --name-status -M -z`` output (NUL-separated) into typed records: a rename
    or copy record is three fields (status, old path, new path), every other status is two
    (status, path) — the gate's existing ``_z`` only flattens a ``--name-only`` list and
    cannot carry a rename's two paths (spec.md Design; ``check_ratchets``'s rename rule)."""
    records: list[NameStatusRecord] = []
    fields = [f for f in out.split("\0") if f != ""]
    i = 0
    while i < len(fields):
        status = fields[i]
        i += 1
        letter = status[0] if status else ""
        if letter in ("R", "C"):
            if i + 1 >= len(fields):
                break
            old, new = fields[i], fields[i + 1]
            i += 2
            records.append(NameStatusRecord(letter, old.replace("\\", "/"), new.replace("\\", "/")))
        else:
            if i >= len(fields):
                break
            path = fields[i]
            i += 1
            records.append(NameStatusRecord(letter, path.replace("\\", "/")))
    return records


def name_status(
    root: Path, merge_base: str | None, head: str | None = None
) -> list[NameStatusRecord]:
    """``git diff --name-status -M -z <merge_base>...<head>`` parsed into records; ``-M``
    named explicitly (spec.md Requirements), so rename detection does not depend on the
    running machine's git configuration. ``[]`` with no merge base, as ``committed_files``."""
    if not merge_base:
        return []
    ref = f"{merge_base}...{head or 'HEAD'}"
    out = _git(root, "diff", "--name-status", "-M", "-z", ref, check=False)
    return parse_name_status(out)


# Every reader of what a branch changed (R59, the plugin security review of 2026-10-19, I3):
# ``--name-status`` with no diff filter and no rename detection, so a rename lists its source
# as a deletion beside its destination, and a type change (``T``: a file turned into a
# symlink, or the reverse) and a submodule are listed with the rest. ``--name-only`` with the
# default rename detection printed only a rename's destination, and ``--diff-filter=ACMRD``
# dropped ``T``: ``git mv CLAUDE.md x`` and ``sdlc.yaml`` turned into a link passed the gate.
CHANGED = ("--name-status", "--no-renames", "-z")


def paths_of(out: str) -> list[str]:
    """The paths of ``git diff --name-status --no-renames -z`` output, sorted, once each."""
    return sorted({record.path for record in parse_name_status(out)})


def changed_paths(root: Path, *revs: str) -> list[str]:
    """The paths ``git diff`` lists between ``revs`` (a range, or one ref against the working
    tree), every status counted (``CHANGED``)."""
    return paths_of(_git(root, "diff", *CHANGED, *revs, check=False))


def tree_files(root: Path, ref: str | None, prefix: str) -> list[str]:
    """Every path ``ref``'s committed tree holds under ``prefix`` (``git ls-tree -r
    --name-only -z <ref> -- <prefix>``). Used to tell an eval case's survivor from its drop:
    a file under a case folder the diff never touches carries no ``--name-status`` record at
    all (panel decision #2, phase b)."""
    if not ref:
        return []
    out = _git(root, "ls-tree", "-r", "--name-only", "-z", ref, "--", prefix, check=False)
    return _z(out)


def committed_files(root: Path, merge_base: str | None, head: str | None = None) -> list[str]:
    """The files the branch carries: ``git diff <merge_base>...HEAD``, every status and a
    rename's two paths counted (``CHANGED``).

    This is the PR's own diff — what a reviewer sees and what merges. The working tree says
    nothing here: a checkout can be dirty for reasons that have nothing to do with the change
    (see ``SANDBOX_MASKED``), and a phase that commits its work is judged on the commits.
    """
    if not merge_base:
        return []
    ref = f"{merge_base}...{head or 'HEAD'}"
    return changed_paths(root, ref)


def is_repo(root: Path) -> bool:
    """``gitops.is_repo``, whose yes is remembered (1.0.13); no git at all is a no."""
    try:
        return gitops.is_repo(root)
    except OSError:
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
    ``gitops.explicit_default_branch``) wins when ``refs/remotes/origin/<value>`` resolves.
    Its lookups are gitops' remembered ones (``origin_head``, ``ref_exists``, 1.0.13), shared
    with ``gitops.default_branch`` and the runner's ref checks."""
    explicit = gitops.explicit_default_branch()
    try:
        if explicit:
            ref = f"refs/remotes/origin/{explicit}"
            if gitops.ref_exists(root, ref):
                return ref
        ref = gitops.origin_head(root)
        if ref and ref.startswith("refs/remotes/"):
            return ref
        for cand in ("refs/remotes/origin/main", "refs/remotes/origin/master", "main", "master"):
            if gitops.ref_exists(root, cand):
                return cand
    except (OSError, gitops.GitError) as exc:  # a read that timed out included (choice 239)
        raise GitUnavailable(f"git: {exc!r}") from exc
    return "HEAD"


def is_ancestor(root: Path, commit: str, ref: str) -> bool:
    """``git merge-base --is-ancestor <commit> <ref>``: False on any error (an unknown sha)."""
    try:
        proc = subprocess.run(
            ["git", "merge-base", "--is-ancestor", commit, ref],
            cwd=str(root),
            capture_output=True,
            text=True,
            timeout=60,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    return proc.returncode == 0


# Decision 30 (the fast lane, ROADMAP R46): the ``status.yaml: fast_lane`` entry whose commit
# is the approved copy of a phase. The design phase was cut from the owner's unmerged intent PR
# (entry ``intent``); the build branch, and the test, deploy and review runs and the fix rounds on
# it, from the design commit whose gate passed on a routine plan (entry ``design``). Every other
# phase (the intent PR's own rounds at (intent), the maintain phase) reads the merge base as before.
FAST_LANE_ENTRY = {
    c.DESIGN: c.INTENT,
    c.BUILD: c.DESIGN,
    c.TEST: c.DESIGN,
    c.DEPLOY: c.DESIGN,
    "review": c.DESIGN,
}


def fast_lane_sha(
    root: Path,
    fast_lane: dict | None,
    phase: str,
    base: str | None = None,
    head: str = "HEAD",
) -> str | None:
    """The commit ``fast_lane`` records for ``phase`` while it stands, else None: it must be
    an ancestor of ``head`` (the branch was cut from it) and not of the default branch
    ``base`` (its pull request was not merged). A merge of that PR (its commit then on the
    default branch), a squash merge (the next branch then cut from the default branch, the
    commit not in it) and a change that never took the fast lane all give None, and the
    caller reads the merge base exactly as before."""
    key = FAST_LANE_ENTRY.get(phase)
    lane = fast_lane if isinstance(fast_lane, dict) else {}
    entry = lane.get(key) if key else None
    sha = entry.get("sha") if isinstance(entry, dict) else None
    if not isinstance(sha, str) or not sha:
        return None
    base = base or default_base(root)
    if base == "HEAD" or not is_ancestor(root, sha, head) or is_ancestor(root, sha, base):
        return None
    return sha


def approved_base(
    root: Path,
    fast_lane: dict | None,
    phase: str,
    merge_base: str | None,
    base: str | None = None,
    head: str = "HEAD",
) -> str | None:
    """The one rule for the commit a phase's "approved copies" (``intent.md``, ``plan.md``)
    and its "changed since the last gate" diff are read at: the fast lane's recorded commit
    for the phase (``fast_lane_sha``) while it stands, else ``merge_base`` (the merge base
    of HEAD with the default branch, None when there is none), as before decision 30. The
    gate (``GateContext.approved_base``) and the runner (``guardrail_changes``) both call it.
    The PR's own diff (``committed_files`` from the merge base) is unchanged: the owner sees
    intent, spec, plan and code together at (deploy)."""
    if not merge_base:
        return None
    return fast_lane_sha(Path(root), fast_lane, phase, base, head) or merge_base


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
    files = set(changed_paths(root, ref))
    if merge_base and head and merge_base != head:
        # the commits too: a commit made with plumbing (``update-index --cacheinfo``) can
        # leave the working tree as the base had it, and the working-tree diff alone misses
        # it (R59, I3)
        files |= set(changed_paths(root, f"{merge_base}...HEAD"))
    files = sorted(files | set(_z(_git(root, "ls-files", "-z", "--others", "--exclude-standard"))))
    commits: list[Commit] = []
    if merge_base and head and merge_base != head:
        for sha in _git(root, "rev-list", "--reverse", f"{merge_base}..HEAD").split():
            changed = paths_of(_git(root, "diff-tree", "--no-commit-id", "-r", *CHANGED, sha))
            commits.append(Commit(sha, changed))
    return Diff(base, merge_base, head, files, commits, branch, note)
