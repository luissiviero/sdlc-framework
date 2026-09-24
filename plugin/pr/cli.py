"""Command-line face of the PR surface, called by /sdlc-build, /sdlc-test and /sdlc-deploy
(build guide step 27a; OPERATING_MODEL section 4.1 "surface").

    python "${CLAUDE_PLUGIN_ROOT}/plugin/pr/cli.py" description --root . --id 0001 --phase c
    python cli.py upsert --root . --id 0001 --phase c [--draft] [--ready] [--check-run]
                                                      [--head <branch>] [--dry-run]
    python cli.py check-run --root . --id 0001 --phase d

``description`` prints the body only (nothing else). ``upsert`` opens or updates the phase's
PR with that body, the generated title and the label the gate printed, and prints a JSON
summary: route, url (or compare_url when no route exists), number, label, created; with
``--check-run`` it also posts the phase's check run, so the phase (d) runbook line is one
command. ``check-run`` posts the phase's check run for HEAD (step 28) on its own. Exit 0 on
success, 2 on a usage error; a missing GitHub route is not an error - it prints the body for
the owner. ``--head`` names the PR's head branch when it is not the phase's framework branch
(a fix round on an intent PR a web session pushed from ``claude/...``, decision 22).

Labels: the PR carries one gate label at a time (``sdlc:<phase>-ready``,
``sdlc:<phase>-approved``, ``sdlc:needs-human``); the owner's own labels - the release
approval and the un-park verbs of decision 24 - are never removed by an upsert.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pr import description as desc  # noqa: E402
from pr import github  # noqa: E402
from state import conventions as c  # noqa: E402
from state import gitops  # noqa: E402
from state import status as status_mod  # noqa: E402

READY_COLOR = "0E8A16"  # green: the run finished and waits at a human gate
NEEDS_HUMAN_COLOR = "D93F0B"  # orange-red: parked, waiting for a decision
CHECK_RUN_NAME = "sdlc/{phase}"
# the owner's labels: applied by a person, read by the release workflow and the next run,
# never swept away when the gate label changes
OWNER_LABELS = frozenset({c.RELEASE_APPROVED_LABEL, *c.UNPARK_LABELS})


def _emit(obj: Any) -> None:
    print(json.dumps(obj, indent=2, sort_keys=True))


def label_color(label: str) -> str:
    return NEEDS_HUMAN_COLOR if label == c.NEEDS_HUMAN_LABEL else READY_COLOR


def _context(args) -> tuple[Path, Path, Any] | None:
    root = Path(args.root).resolve()
    change_dir = c.find_change_dir(root, args.id)
    if change_dir is None:
        print(f"no change folder for id {args.id}", file=sys.stderr)
        return None
    return root, change_dir, status_mod.read_status(change_dir)


def _repo_and_base(root: Path) -> tuple[str | None, str]:
    try:
        repo = gitops.github_repo(root)
    except gitops.GitError:
        repo = None
    try:
        base = gitops.default_branch(root)
    except (gitops.GitError, FileNotFoundError):
        base = "main"
    return repo, base.split("origin/", 1)[-1] if base.startswith("origin/") else base


def cmd_description(args) -> int:
    ctx = _context(args)
    if ctx is None:
        return 2
    root, _change_dir, _st = ctx
    print(desc.build_description(root, args.id, args.phase), end="")
    return 0


def cmd_upsert(args) -> int:
    ctx = _context(args)
    if ctx is None:
        return 2
    root, change_dir, st = ctx
    body = desc.build_description(root, args.id, args.phase)
    title = desc.pr_title(st, args.phase)
    gate_json = desc.load_gate(change_dir, args.phase)
    label = desc.label_for(gate_json, args.phase)
    head = (getattr(args, "head", None) or "").strip() or desc.head_branch(args.id, args.phase)
    repo, base = _repo_and_base(root)
    out: dict[str, Any] = {
        "repo": repo,
        "head": head,
        "base": base,
        "title": title,
        "label": label,
        "number": None,
        "created": False,
        "compare_url": github.compare_url(repo, base, head),
    }
    if args.dry_run:
        out.update({"route": "dry-run", "url": None, "body": body})
        _emit(out)
        return 0

    def finish() -> int:
        """Emit, after posting the phase's check run when --check-run asked for it."""
        if getattr(args, "check_run", False):
            out["check_run"] = check_run_result(root, change_dir, args.phase)
        _emit(out)
        return 0

    if not repo:
        out.update({"route": "none", "url": None, "reason": "no GitHub remote", "body": body})
        return finish()

    found = github.find_open_pr(repo, head, cwd=root)
    number = found.get("number")
    if number:
        result = github.update_pr(repo, int(number), body, title, cwd=root)
    else:
        result = github.create_pr(repo, base, head, title, body, draft=args.draft, cwd=root)
    out["route"] = result.get("route", "none")
    out["number"] = result.get("number", number)
    out["url"] = result.get("url")
    out["created"] = bool(result.get("created", False))
    if not result.get("ok"):
        out["reason"] = result.get("reason", "")
        out["body"] = body  # no route: the owner opens the PR from the compare URL
        return finish()

    number = out["number"]
    if label and number:
        github.ensure_label(repo, label, label_color(label), f"SDLC gate ({args.phase})", cwd=root)
    if number:
        carried = [
            lb
            for lb in found.get("labels") or []
            if str(lb).startswith(c.LABEL_PREFIX) and lb not in OWNER_LABELS
        ]
        remove = [lb for lb in carried if lb != label]
        add = [label] if label and label not in carried else []
        if add or remove:
            out["labels"] = github.set_labels(repo, int(number), add, remove, cwd=root)
        if args.ready:
            out["ready"] = github.set_ready(repo, int(number), cwd=root)
    return finish()


def check_run_result(root: Path, change_dir: Path, phase: str) -> dict[str, Any]:
    """Post the phase's check run for HEAD and return what happened (route "none" when
    there is no GitHub remote or no commit yet: a missing route is never an error)."""
    gate_json = desc.load_gate(change_dir, phase)
    conclusion = "failure" if (gate_json or {}).get("result") == "park" else "success"
    summary = desc.evidence_status(change_dir, phase)
    repo, _base = _repo_and_base(root)
    try:
        head_sha = gitops.run(root, "rev-parse", "HEAD").strip()
    except (gitops.GitError, FileNotFoundError):
        head_sha = ""
    name = CHECK_RUN_NAME.format(phase=phase)
    if not repo or not head_sha:
        return {
            "route": "none",
            "ok": False,
            "reason": "no GitHub remote or no HEAD",
            "name": name,
            "conclusion": conclusion,
            "summary": summary,
        }
    result = github.create_check_run(
        repo, head_sha, name, conclusion, f"SDLC gate ({phase})", summary, cwd=root
    )
    result.update(
        {"name": name, "conclusion": conclusion, "summary": summary, "head_sha": head_sha}
    )
    return result


def cmd_check_run(args) -> int:
    ctx = _context(args)
    if ctx is None:
        return 2
    root, change_dir, _st = ctx
    _emit(check_run_result(root, change_dir, args.phase))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="pr/cli.py", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("description", "upsert", "check-run"):
        p = sub.add_parser(name)
        p.add_argument("--root", default=".")
        p.add_argument("--id", required=True)
        p.add_argument("--phase", required=True, choices=list(c.PHASES))
        if name == "upsert":
            p.add_argument("--draft", action="store_true", help="open the PR as a draft")
            p.add_argument("--ready", action="store_true", help="mark the PR ready for review")
            p.add_argument(
                "--check-run",
                action="store_true",
                help="also post the phase's check run for HEAD (step 28)",
            )
            p.add_argument("--dry-run", action="store_true", help="compute, contact nothing")
            p.add_argument(
                "--head",
                default=None,
                help="the PR's head branch when it is not sdlc/<id>/<phase> (a fix round on "
                "a web-session intent PR)",
            )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    handlers = {
        "description": cmd_description,
        "upsert": cmd_upsert,
        "check-run": cmd_check_run,
    }
    try:
        return handlers[args.command](args)
    except (ValueError, OSError) as exc:
        print(f"pr: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
