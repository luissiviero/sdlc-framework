"""Command-line face of plugin/state, called by the slash commands.

The commands (markdown prompts) do the model's work; everything deterministic — ids, folders,
status.yaml, branches, commits — goes through here so it is unit-testable without a model
and identical on Windows, in a cloud session and in CI.

    python "${CLAUDE_PLUGIN_ROOT}/state/cli.py" new-change --root . --title "..." \
        [--route idea|ticket|incident] [--type feature|fix] [--profile-override lite] \
        [--external-ref 42]
    python cli.py commit-phase --root . --id 0001 --phase a --message "..."
    python cli.py set-phase --root . --id 0001 --phase b
    python cli.py park --root . --id 0001 --reason "..."
    python cli.py show --root . --id 0001
    python cli.py labels
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from state import conventions as c  # noqa: E402
from state import gitops, status  # noqa: E402


def _emit(obj) -> None:
    print(json.dumps(obj, indent=2, sort_keys=True))


def cmd_new_change(args) -> int:
    root = Path(args.root).resolve()
    change_dir, st = status.new_change(
        root,
        title=args.title,
        entry_route=args.route,
        change_type=args.type,
        profile_override=args.profile_override,
        external_ref=args.external_ref,
        change_id=args.id,
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


def cmd_commit_phase(args) -> int:
    """Switch to sdlc/<id>/<phase>, stage the change folder (+ extra paths) and commit."""
    root = Path(args.root).resolve()
    change_dir = c.find_change_dir(root, args.id)
    if change_dir is None:
        print(f"no change folder for id {args.id}", file=sys.stderr)
        return 2
    st = status.read_status(change_dir)
    if st.phase != args.phase:  # idempotent: an unchanged phase leaves status.yaml untouched
        st.set_phase(args.phase)
        status.write_status(change_dir, st)
    branch = c.branch_name(args.id, args.phase)
    if not gitops.is_repo(root):
        print(f"{root} is not a git repository", file=sys.stderr)
        return 2
    start = args.start_point or None
    gitops.checkout_branch(root, branch, start)
    rel = str(change_dir.relative_to(root)).replace("\\", "/")
    sha = gitops.commit_paths(root, [rel, *args.paths], args.message)
    pushed = False
    if args.push and gitops.has_remote(root):
        gitops.push(root, branch)
        pushed = True
    _emit(
        {
            "id": st.id,
            "branch": branch,
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


def cmd_show(args) -> int:
    loaded = _load(args)
    if not loaded:
        return 2
    change_dir, st = loaded
    _emit({"dir": str(change_dir), "status": st.to_dict()})
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

    for name, fn in (("set-phase", cmd_set_phase), ("park", cmd_park), ("show", cmd_show)):
        s = sub.add_parser(name)
        s.add_argument("--root", default=".")
        s.add_argument("--id", required=True)
        if name == "set-phase":
            s.add_argument("--phase", required=True, choices=c.PHASES)
        if name == "park":
            s.add_argument("--reason", required=True)
        s.set_defaults(fn=fn)

    lab = sub.add_parser("labels")
    lab.set_defaults(fn=cmd_labels)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
