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
    python cli.py show --root . --id 0001
    python cli.py list --root .
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
from hooks._common import load_sdlc_config  # noqa: E402
from state import conventions as c  # noqa: E402
from state import gitops, status  # noqa: E402


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
    """Switch to the phase's work branch, stage the change folder (+ extra paths) and commit.

    The work branch is ``conventions.work_branch``, not the literal ``sdlc/<id>/<phase>``:
    phases (d) and (e) commit on ``sdlc/<id>/c``, the build PR that stays open through them
    (OPERATING_MODEL section 8). A (d)/(e) run therefore never creates a branch: a missing
    ``sdlc/<id>/c`` means the build phase never ran, which is an error, not a fresh start."""
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
    if args.phase in ("d", "e"):
        if not _branch_exists(root, branch):
            print(
                f"phase ({args.phase}) commits on {branch}, which does not exist: run "
                f"/sdlc-build for change {args.id} first (the build PR stays open through "
                "(d) and (e))",
                file=sys.stderr,
            )
            return 2
        start = None  # switch to the existing build branch; never branch off somewhere else
    gitops.checkout_branch(root, branch, start)
    st = status.read_status(change_dir)
    if st.phase != args.phase:  # idempotent: an unchanged phase leaves status.yaml untouched
        st.set_phase(args.phase)
        status.write_status(change_dir, st)
    rel = str(change_dir.relative_to(root)).replace("\\", "/")
    extra = [p for p in args.paths if (root / p).exists()]  # e.g. ruff.toml only when created
    staged = gitops.stage_paths(root, [rel, *extra])
    # The plan-sync rule, applied here because this command is how the phase commands
    # commit and the hook only sees ``git *`` shell commands (NOTES section 9): a commit on
    # sdlc/<id>/c that departs from plan.md without updating it is refused now, not found
    # by gate (c) twenty turns later (the first gated build run, 2026-09-22).
    denial = plan_sync.check(
        branch,
        staged,
        plan_sync.exempt_patterns(load_sdlc_config(str(root))),
        plan_sync.planned_files(str(root), args.id),
    )
    if denial.block:
        print(denial.reason, file=sys.stderr)
        return 2
    sha = gitops.commit_staged(root, args.message) if staged else None
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


def cmd_show(args) -> int:
    loaded = _load(args)
    if not loaded:
        return 2
    change_dir, st = loaded
    _emit({"dir": str(change_dir), "status": st.to_dict()})
    return 0


def cmd_list(args) -> int:
    """Every change folder with its phase, so a re-run of /sdlc-plan can find an existing one."""
    root = Path(args.root).resolve()
    rows = []
    for change_dir in c.list_change_dirs(root):
        try:
            st = status.read_status(change_dir)
            rows.append(
                {
                    "id": st.id,
                    "slug": st.slug,
                    "title": st.title,
                    "phase": st.phase,
                    "change_type": st.change_type,
                    "parked_reason": st.parked_reason,
                    "dir": str(change_dir.relative_to(root)).replace("\\", "/"),
                }
            )
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
    cp.add_argument("--paths", nargs="*", default=[], help="extra paths to stage")
    cp.add_argument("--start-point", default=None)
    cp.add_argument("--push", action="store_true")
    cp.set_defaults(fn=cmd_commit_phase)

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
