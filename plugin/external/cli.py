"""The second opinion (ROADMAP R8, plugin 1.0.19): a model of another vendor reads a change at
gate (b) or (e) and answers; it edits nothing, never parks and never fails its job.

    python plugin/external/cli.py review --root . --id 0001 --phase b [--repo owner/name]
        [--ref main] [--head <rev>] [--model <id>] [--out record.json] [--post] [--dry-run]
    python plugin/external/cli.py models

In CI it runs in a job of its own after the phase job (``sdlc-design.yml``, ``sdlc-deploy.yml``),
on a fresh runner that never held a Claude session, with ``GEMINI_API_KEY`` in that one
step's environment; the Claude session never sees the key (``ci/run_phase.session_env``
strips it) and its sandbox does not reach the Gemini host. By hand it runs the same way from
a terminal where the owner set the key for that window only.

On: ``sdlc.yaml: external_review: {model: <id>, phases: [b, e]}`` on the default branch
(``--ref``), as the pin is read; absent means off and the command says so and stops.
``--model`` runs it by hand whatever ``sdlc.yaml`` says. With ``--repo`` it reviews the head
of the change's open pull request (``sdlc/<id>/b`` at (b), ``sdlc/<id>/c`` at (e)) and
``--post`` puts the record on that pull request as one comment. Every failure is the
record's "not run: <reason>"; the exit code is 0 whenever the arguments parse.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

PLUGIN_DIR = Path(__file__).resolve().parent.parent
if str(PLUGIN_DIR) not in sys.path:
    sys.path.insert(0, str(PLUGIN_DIR))

from external import bundle, gemini  # noqa: E402
from external import review as review_mod  # noqa: E402
from state import yamlish  # noqa: E402

PHASES = ("b", "e")
BRANCH = {"b": "sdlc/{id}/b", "e": "sdlc/{id}/c"}
CONFIG_KEY = "external_review"
WORK_BRANCH_RE = re.compile(r"^sdlc/(\d{4})/[a-f]$")


def _github():
    from pr import github  # noqa: PLC0415

    return github


def read_config(root: Path, ref: str | None) -> dict[str, Any]:
    """``sdlc.yaml`` from the default branch ``ref`` (the remote-tracking ref first, as the
    pin is read), else the working tree's; {} when unreadable."""
    for rev in (f"refs/remotes/origin/{ref}", f"refs/heads/{ref}") if ref else ():
        ok, text = bundle.run_git(root, "show", f"{rev}:sdlc.yaml")
        if ok:
            break
    else:
        path = Path(root) / "sdlc.yaml"
        text = path.read_text(encoding="utf-8") if path.is_file() else ""
    try:
        data = yamlish.loads(text) if text.strip() else {}
    except Exception:  # noqa: BLE001 - an unreadable file is "off", never a crash
        return {}
    return data if isinstance(data, dict) else {}


def settings(config: dict[str, Any]) -> dict[str, Any]:
    value = config.get(CONFIG_KEY)
    return value if isinstance(value, dict) else {}


def turned_on(config: dict[str, Any], phase: str) -> bool:
    phases = settings(config).get("phases")
    return isinstance(phases, list) and phase in [str(p) for p in phases]


def max_chars(config: dict[str, Any]) -> int:
    value = settings(config).get("max_chars")
    return value if isinstance(value, int) and value > 0 else bundle.DEFAULT_MAX_CHARS


def given_on_head(repo: str, pr: int, head: str, root: Path) -> str | None:
    """The URL of a bot's comment that already carries a second opinion (a verdict, not a
    "not run") on ``head``: a re-run of the phase job on an unchanged head pays nothing."""
    found = _github().issue_comments(repo, pr, cwd=root)
    for c in found.get("comments") or [] if found.get("ok") else []:
        body = c.get("body") or ""
        if c.get("type") != "Bot" or not body.startswith(review_mod.MARKER):
            continue
        if f"commit `{head[:12]}`" in body and "\nVerdict: **" in body:
            return c.get("url") or "a comment on the pull request"
    return None


def run_review(args: argparse.Namespace, env: dict[str, str]) -> dict[str, Any]:
    root = Path(args.root).resolve()
    config = read_config(root, args.ref)
    if not args.id:
        found_id = WORK_BRANCH_RE.match(args.head_ref or "")
        args.id = found_id.group(1) if found_id else ""
    record: dict[str, Any] = {
        "provider": review_mod.PROVIDER,
        "phase": args.phase,
        "change_id": args.id,
        "ran": False,
        "reason": "",
        "model": args.model or settings(config).get("model"),
        "pr": None,
    }
    if not args.model and not turned_on(config, args.phase):
        record["off"] = True
        record["reason"] = (
            f"off: sdlc.yaml {CONFIG_KEY}.phases does not list ({args.phase}) on "
            f"{args.ref or 'the working tree'}"
        )
        return record
    if not args.id:
        record["reason"] = (
            f"no change id (--id, or a --head-ref sdlc/<id>/<phase>; got {args.head_ref!r})"
        )
        return record
    if not record["model"]:
        record["reason"] = f"no model: set sdlc.yaml {CONFIG_KEY}.model or pass --model"
        return record
    head_rev = args.head
    if args.repo and not head_rev:
        branch = BRANCH[args.phase].format(id=args.id)
        found = _github().find_open_pr(args.repo, branch, cwd=root)
        if not found.get("number"):
            record["reason"] = (
                f"no open pull request from {branch} ({found.get('reason') or 'none'})"
            )
            return record
        record["pr"] = found["number"]
        head_rev = found.get("head_sha")
    head = bundle.resolve(root, head_rev or "HEAD")
    if head is None:
        record["reason"] = f"the head {head_rev or 'HEAD'} is not in this checkout"
        return record
    record["head"] = head
    earlier = given_on_head(args.repo, record["pr"], head, root) if record["pr"] else None
    if earlier:
        record["duplicate"] = True
        record["reason"] = f"already given on this head: {earlier}"
        return record
    base = None
    if args.phase == "e":
        ref = args.ref or "main"
        target = bundle.resolve(root, f"refs/remotes/origin/{ref}") or bundle.resolve(root, ref)
        ok, out = bundle.run_git(root, "merge-base", target or "", head) if target else (False, "")
        base = out.strip() if ok and out.strip() else None
        if base is None:
            record["reason"] = f"no merge base between {ref} and {head[:12]}"
            return record
        record["base"] = base
    bundled = bundle.build(root, args.id, args.phase, head, base, max_chars(config))
    for name in ("change_dir", "sent", "left_out", "withheld_lines", "chars"):
        record[name] = bundled[name]
    if not bundled["ok"]:
        record["reason"] = bundled["reason"]
        return record
    text = review_mod.prompt(args.phase, args.id, bundled["pieces"], bundled["left_out"])
    if args.dry_run:
        record["reason"] = "dry run: nothing sent"
        record["prompt_chars"] = len(text)
        return record
    credential = gemini.key(env)
    if credential is None:
        record["reason"] = f"no {gemini.KEY_ENV} in this step's environment"
        return record
    result = gemini.generate(record["model"], text, review_mod.SCHEMA, credential)
    record.update(
        model_reported=result["model"],
        model_status=result.get("model_status"),
        tokens=result["tokens"],
        seconds=result["seconds"],
    )
    if not result["ok"]:
        record["reason"] = result["reason"]
        return record
    answer, why = review_mod.check_answer(result["answer"])
    if answer is None:
        record["reason"] = why
        return record
    record["ran"] = True
    record["answer"] = answer
    return record


def publish(args: argparse.Namespace, record: dict[str, Any], env: dict[str, str]) -> None:
    """The record where the owner reads it: the job summary in CI, one PR comment with
    ``--post``, the JSON with ``--out``. An "off" record is not posted, nor a repeat on a head
    that already has a verdict."""
    if args.out:
        Path(args.out).write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    if record.get("off"):
        return
    text = review_mod.comment(record)
    summary = env.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as fh:
            fh.write(text + "\n")
    if (
        args.post
        and args.repo
        and record.get("pr")
        and not args.dry_run
        and not record.get("duplicate")
    ):
        posted = _github().add_comment(args.repo, record["pr"], text, cwd=args.root)
        record["comment"] = posted.get("url") if posted.get("ok") else None
        if not posted.get("ok"):
            record["comment_error"] = posted.get("reason")


def cmd_review(args: argparse.Namespace) -> int:
    env = dict(os.environ)
    record = run_review(args, env)
    publish(args, record, env)
    print(json.dumps(record, indent=2))
    return 0


def cmd_models(args: argparse.Namespace) -> int:
    credential = gemini.key()
    if credential is None:
        print(json.dumps({"ok": False, "reason": f"no {gemini.KEY_ENV} in the environment"}))
        return 0
    print(json.dumps(gemini.list_models(credential), indent=2))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0])
    sub = parser.add_subparsers(dest="command", required=True)
    rv = sub.add_parser("review", help="ask for a second opinion on a change at (b) or (e)")
    rv.add_argument("--root", default=".")
    rv.add_argument("--id", default="", help="the change id (else read from --head-ref)")
    rv.add_argument("--head-ref", default="", help="the work branch sdlc/<id>/<phase>")
    rv.add_argument("--phase", required=True, choices=PHASES)
    rv.add_argument("--repo", help="owner/name: review the head of the change's open PR")
    rv.add_argument("--ref", help="the default branch: sdlc.yaml and the (e) merge base")
    rv.add_argument("--head", help="the commit to review (default: the PR's head, else HEAD)")
    rv.add_argument("--model", help="by hand: this model id, whatever sdlc.yaml says")
    rv.add_argument("--out", help="write the record (JSON) to this file")
    rv.add_argument("--post", action="store_true", help="post the record on the PR")
    rv.add_argument("--dry-run", action="store_true", help="build the input, send nothing")
    rv.set_defaults(func=cmd_review)
    md = sub.add_parser("models", help="the model ids GEMINI_API_KEY can call")
    md.set_defaults(func=cmd_models)
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
