"""Command-line face of plugin/state, called by the slash commands.

The commands (markdown prompts) do the model's work; everything deterministic — ids, folders,
status.yaml, branches, commits — goes through here so it is unit-testable without a model
and identical on Windows, in a cloud session and in CI.

    python "${CLAUDE_PLUGIN_ROOT}/state/cli.py" new-change --root . --title "..." \
        [--route idea|ticket|incident] [--type feature|fix] [--profile-override lite] \
        [--external-ref 42]
    python cli.py commit-phase --root . --id 0001 --phase a --message "..."
        # phases d and e commit on the (c) branch: the build PR stays open through them
    python cli.py set-phase --root . --id 0001 --phase b
    python cli.py park --root . --id 0001 --reason "..."
    python cli.py accept-risk --root . --id 0001 --item "auth"   # owner accepts a risk hit
    python cli.py lock-tests --root . --id 0001     # fix change: reproducing test committed
    python cli.py unlock-tests --root . --id 0001   # owner only: the test itself was wrong
    python cli.py apply-labels --root . --id 0001 --repo owner/name --pr 12
        # the owner's un-park labels on the PR (decision 24): performed, recorded with the
        # label's actor, removed from the PR; nothing is committed
    python cli.py abandon --root . --id 0001 --reason "..." [--push]
        # decision 25: the PR was closed without a merge; phase: abandoned on the current
        # branch and on every other sdlc/<id>/* branch of the change on the remote
    python cli.py show --root . --id 0001   # on the default branch: gate (e) of a merged
    python cli.py list --root .             # phase-e change is derived as passed
    python cli.py labels
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hooks import plan_sync  # noqa: E402
from hooks._common import ConfigError, load_sdlc_config  # noqa: E402
from state import conventions as c  # noqa: E402
from state import gitops, status, unpark  # noqa: E402


def _emit(obj) -> None:
    print(json.dumps(obj, indent=2, sort_keys=True))


def cmd_new_change(args) -> int:
    root = Path(args.root).resolve()
    change_id = args.id
    if change_id is None and gitops.is_repo(root) and gitops.has_remote(root):
        change_id = c.next_change_id(root, gitops.remote_change_ids(root))
    change_dir, st = status.new_change(
        root,
        title=args.title,
        entry_route=args.route,
        change_type=args.type,
        profile_override=args.profile_override,
        external_ref=args.external_ref,
        change_id=change_id,
    )
    _emit(
        {
            "id": st.id,
            "slug": st.slug,
            "dir": str(change_dir.relative_to(root)).replace("\\", "/"),
            "branch": c.branch_name(st.id, "a"),
            "status": st.to_dict(),
        }
    )
    return 0


def _branch_exists(root: Path, branch: str) -> bool:
    return bool(gitops.run(root, "branch", "--list", "--", branch).strip())


def cmd_commit_phase(args) -> int:
    """Switch to the phase's work branch and commit what changed under the change folder (+
    extra paths), and only that: anything staged beforehand elsewhere stays out.

    The work branch is ``conventions.work_branch``, not the literal ``sdlc/<id>/<phase>``:
    phases (d) and (e) commit on ``sdlc/<id>/c``, the build PR that stays open through them
    (OPERATING_MODEL section 8). A (d)/(e) run therefore never creates a branch: a missing
    ``sdlc/<id>/c`` means the build phase never ran, which is an error, not a fresh start.

    ``--branch`` names the branch instead (decision 22): a fix round on an intent PR that a
    web session pushed from a branch of its own (``claude/...``) commits on that PR's head,
    never on ``sdlc/<id>/a``, or the PR would not carry it. The branch must exist."""
    root = Path(args.root).resolve()
    change_dir = c.find_change_dir(root, args.id)
    if change_dir is None:
        print(f"no change folder for id {args.id}", file=sys.stderr)
        return 2
    if not gitops.is_repo(root):
        print(f"{root} is not a git repository", file=sys.stderr)
        return 2
    branch = c.work_branch(args.id, args.phase)
    start = args.start_point or None
    explicit = (getattr(args, "branch", None) or "").strip()
    if explicit:
        if explicit.startswith("-"):
            print("--branch must not look like an option", file=sys.stderr)
            return 2
        if not _branch_exists(root, explicit):
            print(
                f"--branch {explicit} does not exist locally: a fix round commits on the "
                "pull request's own head, which the run checks out first",
                file=sys.stderr,
            )
            return 2
        branch, start = explicit, None
    elif args.phase in ("d", "e"):
        if not _branch_exists(root, branch):
            print(
                f"phase ({args.phase}) commits on {branch}, which does not exist: run "
                f"/sdlc-build for change {args.id} first (the build PR stays open through "
                "(d) and (e))",
                file=sys.stderr,
            )
            return 2
        start = None  # switch to the existing build branch; never branch off somewhere else
    st = status.read_status(change_dir)
    if st.abandoned:  # decision 25: read before any branch is created for the phase
        print(
            f"change {args.id} is abandoned ({st.abandoned_reason}); nothing runs on it",
            file=sys.stderr,
        )
        return 2
    gitops.checkout_branch(root, branch, start)
    st = status.read_status(change_dir)
    if st.phase != args.phase:  # idempotent: an unchanged phase leaves status.yaml untouched
        st.set_phase(args.phase)
        status.write_status(change_dir, st)
    rel = str(change_dir.relative_to(root)).replace("\\", "/")
    # Only what changed under the change folder and --paths goes into the commit: the
    # concrete files (modified, added, deleted, renamed, untracked), staged and committed
    # alone with ``git commit --only``, so a file staged beforehand by a hook, an earlier
    # partial command or the session stays out of it. A --paths entry that matches nothing
    # (e.g. ruff.toml when it was not created) contributes nothing; a deleted one is recorded.
    files = gitops.changed_files(root, [rel, *args.paths])
    # The plan-sync rule, applied here because this command is how the phase commands
    # commit and the hook only sees ``git *`` shell commands (NOTES section 9): a commit on
    # sdlc/<id>/c that departs from plan.md without updating it is refused now, not found
    # by gate (c) twenty turns later (the first gated build run, 2026-09-22).
    denial = plan_sync.check(
        branch,
        files,
        plan_sync.exempt_patterns(load_sdlc_config(str(root))),
        plan_sync.planned_files(str(root), args.id),
    )
    if denial.block:
        print(denial.reason, file=sys.stderr)
        return 2
    sha = gitops.commit_files(root, files, args.message)
    pushed = False
    if args.push and gitops.has_remote(root):
        gitops.push(root, branch)
        pushed = True
    _emit(
        {
            "id": st.id,
            "branch": branch,
            "work_branch": branch,
            "commit": sha,
            "pushed": pushed,
            "github_repo": gitops.github_repo(root),
            "base": gitops.default_branch(root) if sha else None,
        }
    )
    return 0


def _load(args) -> tuple[Path, status.Status] | None:
    root = Path(args.root).resolve()
    change_dir = c.find_change_dir(root, args.id)
    if change_dir is None:
        print(f"no change folder for id {args.id}", file=sys.stderr)
        return None
    return change_dir, status.read_status(change_dir)


def cmd_set_phase(args) -> int:
    loaded = _load(args)
    if not loaded:
        return 2
    change_dir, st = loaded
    st.set_phase(args.phase)
    status.write_status(change_dir, st)
    _emit(st.to_dict())
    return 0


def cmd_park(args) -> int:
    loaded = _load(args)
    if not loaded:
        return 2
    change_dir, st = loaded
    st.park(args.reason)
    status.write_status(change_dir, st)
    _emit({"label": c.NEEDS_HUMAN_LABEL, "status": st.to_dict()})
    return 0


def cmd_accept_risk(args) -> int:
    """The owner accepts a risk-list hit for this change (gate check risk_list, step 16)."""
    loaded = _load(args)
    if not loaded:
        return 2
    change_dir, st = loaded
    st.accept_risk(args.item)
    status.write_status(change_dir, st)
    _emit({"risk_accepted": st.risk_accepted, "status": st.to_dict()})
    return 0


def cmd_lock_tests(args) -> int:
    """Fix-type change: the reproducing test is committed, so the test paths freeze for the
    rest of the change (build guide step 25; hooks/test_file_lock.py enforces it)."""
    loaded = _load(args)
    if not loaded:
        return 2
    change_dir, st = loaded
    st.lock_tests()
    status.write_status(change_dir, st)
    _emit(st.to_dict())
    return 0


def cmd_unlock_tests(args) -> int:
    """Owner only, in a reviewed PR, when the reproducing test itself was wrong."""
    loaded = _load(args)
    if not loaded:
        return 2
    change_dir, st = loaded
    st.unlock_tests()
    status.write_status(change_dir, st)
    _emit(st.to_dict())
    return 0


def cmd_apply_labels(args) -> int:
    """The owner's un-park labels on the change's PR (decision 24): performed on status.yaml,
    recorded with the label's actor, removed from the PR. Exit 0 with the report; 2 when the
    PR cannot be read (the labels are then not consumed)."""
    loaded = _load(args)
    if not loaded:
        return 2
    change_dir, _st = loaded
    root = Path(args.root).resolve()
    try:
        config = load_sdlc_config(str(root))
    except ConfigError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    repo = args.repo or gitops.github_repo(root) or ""
    result = unpark.apply_from_pr(root, change_dir, config, repo, int(args.pr))
    _emit(result)
    return 0 if result.get("ok") else 2


def _remote_change_branches(root: Path, change_id: str) -> list[str]:
    """The change's ``sdlc/<id>/*`` branches on the remote: the remote-tracking refs the
    checkout already has (``actions/checkout`` with ``fetch-depth: 0`` fetches every branch)
    plus what ``ls-remote`` answers (best effort: nothing when the remote is unreachable)."""
    names: set[str] = set()
    prefix = f"refs/remotes/origin/sdlc/{change_id}/"
    out = gitops.run(root, "for-each-ref", "--format=%(refname)", prefix, check=False)
    for line in out.splitlines():
        name = line.strip()[len("refs/remotes/origin/") :]
        if line.strip().startswith(prefix) and c.parse_branch(name):
            names.add(name)
    try:
        out = gitops.run(root, "ls-remote", "--heads", "origin", f"refs/heads/sdlc/{change_id}/*")
    except (gitops.GitError, FileNotFoundError):
        out = ""
    for line in out.splitlines():
        parts = line.split("refs/heads/")
        if len(parts) == 2 and c.parse_branch(parts[1]):
            names.add(parts[1].strip())
    return sorted(names)


def cmd_abandon(args) -> int:
    """Decision 25: the owner closed the change's PR without merging. ``status.yaml`` says
    ``phase: abandoned`` on the current branch (the closed PR's head, which the abandon
    workflow checks out) and, with ``--all-branches``, on every other ``sdlc/<id>/*`` branch
    of the change on the remote, so a later dispatch of any phase finds the end state on the
    branch it switches to. Branches are kept: nothing is deleted. Idempotent."""
    loaded = _load(args)
    if not loaded:
        return 2
    change_dir, st = loaded
    root = Path(args.root).resolve()
    reason = args.reason or "pull request closed without a merge"
    rel = str(change_dir.relative_to(root)).replace("\\", "/")
    done: list[dict] = []

    def mark(branch: str) -> None:
        current = status.read_status(change_dir)
        already = current.abandoned
        current.abandon(reason)
        status.write_status(change_dir, current)
        sha = None
        pushed = False
        if gitops.is_repo(root):
            sha = gitops.commit_paths(root, [rel], f"abandon({st.id}): {reason}"[:200])
            if sha and args.push and gitops.has_remote(root):
                gitops.push(root, branch)
                pushed = True
        done.append({"branch": branch, "commit": sha, "pushed": pushed, "already": already})

    if not gitops.is_repo(root):
        mark("(no git repository)")
        _emit({"id": st.id, "phase": c.ABANDONED, "reason": reason, "branches": done})
        return 0
    gitops.ensure_identity(root)  # a CI runner commits under the automation identity
    head = gitops.current_branch(root)
    mark(head)
    if args.all_branches and gitops.has_remote(root):
        gitops.run(root, "fetch", "origin", check=False)
        for branch in _remote_change_branches(root, st.id):
            if branch == head:
                continue
            gitops.run(root, "checkout", "-q", "-B", branch, f"origin/{branch}")
            mark(branch)
        gitops.run(root, "checkout", "-q", head)
    _emit({"id": st.id, "phase": c.ABANDONED, "reason": reason, "branches": done})
    return 0


def _default_branch_checkout(root: Path) -> str | None:
    """The default branch's name when ``root`` is a checkout of it, else None (also for a
    folder that is not a git repository, or a detached HEAD). A ``sdlc/<id>/<phase>`` work
    branch is never the default one, even when ``gitops.default_branch`` falls back to the
    current branch (a CI checkout with neither ``origin/HEAD`` nor a local main)."""
    try:
        if not gitops.is_repo(root):
            return None
        current = gitops.current_branch(root)
        if current == "HEAD" or c.parse_branch(current):
            return None
        default = gitops.default_branch(root)
        return default if current == default else None
    except (gitops.GitError, OSError):
        return None


def _production(root: Path) -> bool:
    """``sdlc.yaml: deploy.production`` of the project; False when the file or the key is
    missing or unreadable. It only words the derived gate (e) reason (decision 13): the
    release approval itself is the release workflow's to check."""
    try:
        deploy = load_sdlc_config(str(root)).get("deploy")
    except (ConfigError, OSError):
        return False
    return isinstance(deploy, dict) and deploy.get("production") is True


def _derived_gate(raw: status.Status, st: status.Status, default: str | None) -> str | None:
    """The marker ``show`` and ``list`` print when the gate was derived, not read."""
    if default is None or st.gate == raw.gate:
        return None
    return f"gate: {st.gate.phase}/{st.gate.result} (derived: merged on {default})"


def cmd_show(args) -> int:
    """``status.yaml`` of one change. On a checkout of the default branch a change at phase e
    was merged by the owner, which is gate (e) passed (decision 13): the output shows the
    derived gate and says so under ``derived``; the file itself is left as it is."""
    loaded = _load(args)
    if not loaded:
        return 2
    change_dir, raw = loaded
    root = Path(args.root).resolve()
    default = _default_branch_checkout(root)
    st = status.merged_at_gate_e(raw, production=_production(root)) if default else raw
    out = {"dir": str(change_dir), "status": st.to_dict()}
    marker = _derived_gate(raw, st, default)
    if marker:
        out["derived"] = marker
    _emit(out)
    return 0


def cmd_list(args) -> int:
    """Every change folder with its phase, so a re-run of /sdlc-plan can find an existing one.
    On the default branch the gate of a merged phase-e change is derived as in ``show``."""
    root = Path(args.root).resolve()
    default = _default_branch_checkout(root)
    production = _production(root) if default else False
    rows = []
    for change_dir in c.list_change_dirs(root):
        try:
            raw = status.read_status(change_dir)
            st = status.merged_at_gate_e(raw, production=production) if default else raw
            row = {
                "id": st.id,
                "slug": st.slug,
                "title": st.title,
                "phase": st.phase,
                "change_type": st.change_type,
                "parked_reason": st.parked_reason,
                "abandoned_reason": st.abandoned_reason,
                "dir": str(change_dir.relative_to(root)).replace("\\", "/"),
            }
            marker = _derived_gate(raw, st, default)
            if marker:
                row["derived"] = marker
            rows.append(row)
        except Exception as exc:  # noqa: BLE001
            rows.append({"dir": change_dir.name, "error": repr(exc)})
    _emit(rows)
    return 0


def cmd_labels(_args) -> int:
    _emit(c.all_labels())
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="sdlc-state", description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)

    n = sub.add_parser("new-change")
    n.add_argument("--root", default=".")
    n.add_argument("--title", required=True)
    n.add_argument("--route", default="idea", choices=c.ENTRY_ROUTES)
    n.add_argument("--type", default="feature", choices=c.CHANGE_TYPES)
    n.add_argument("--profile-override", default=None, choices=c.PROFILES)
    n.add_argument("--external-ref", default=None)
    n.add_argument("--id", default=None, help="force an id (e.g. 0000 for /sdlc-init)")
    n.set_defaults(fn=cmd_new_change)

    cp = sub.add_parser("commit-phase")
    cp.add_argument("--root", default=".")
    cp.add_argument("--id", required=True)
    cp.add_argument("--phase", required=True, choices=c.PHASES)
    cp.add_argument("--message", required=True)
    cp.add_argument("--paths", nargs="*", default=[], help="extra paths to commit")
    cp.add_argument("--start-point", default=None)
    cp.add_argument(
        "--branch",
        default=None,
        help="commit on this existing branch instead of sdlc/<id>/<phase> (a fix round on "
        "a pull request whose head is not a framework branch)",
    )
    cp.add_argument("--push", action="store_true")
    cp.set_defaults(fn=cmd_commit_phase)

    al = sub.add_parser("apply-labels")
    al.add_argument("--root", default=".")
    al.add_argument("--id", required=True)
    al.add_argument("--repo", default=None, help="owner/repo (default: the origin remote)")
    al.add_argument("--pr", required=True, type=int, help="the change's pull request")
    al.set_defaults(fn=cmd_apply_labels)

    ab = sub.add_parser("abandon")
    ab.add_argument("--root", default=".")
    ab.add_argument("--id", required=True)
    ab.add_argument("--reason", default=None)
    ab.add_argument("--push", action="store_true")
    ab.add_argument(
        "--all-branches",
        action="store_true",
        help="also mark every other sdlc/<id>/* branch of the change on the remote",
    )
    ab.set_defaults(fn=cmd_abandon)

    for name, fn in (
        ("set-phase", cmd_set_phase),
        ("park", cmd_park),
        ("show", cmd_show),
        ("accept-risk", cmd_accept_risk),
        ("lock-tests", cmd_lock_tests),
        ("unlock-tests", cmd_unlock_tests),
    ):
        s = sub.add_parser(name)
        s.add_argument("--root", default=".")
        s.add_argument("--id", required=True)
        if name == "set-phase":
            s.add_argument("--phase", required=True, choices=c.PHASES)
        if name == "park":
            s.add_argument("--reason", required=True)
        if name == "accept-risk":
            s.add_argument("--item", required=True)
        s.set_defaults(fn=fn)

    ls = sub.add_parser("list")
    ls.add_argument("--root", default=".")
    ls.set_defaults(fn=cmd_list)

    lab = sub.add_parser("labels")
    lab.set_defaults(fn=cmd_labels)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
