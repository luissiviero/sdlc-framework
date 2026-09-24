"""The release workflow's step (build guide step 32.3; decision 13; OPERATING_MODEL section 4,
gate (e): "merge of the build PR; plus a release label only when sdlc.yaml declares a real
production").

    python cli.py run --root <project> --repo <owner/repo> --pr <number>
                      [--event closed|labeled] [--merge-sha <sha>] [--change-id <id>]

``.github/workflows/sdlc-release.yml`` calls it on the owner's merge of a build PR and, when
production is declared, on the release label. It is **not** a phase run: no ``claude``
starts and no hook fires here, so it checks the approval itself with the production-gate
hook's own function (``release/approval.py``; article p.36-37). Every step prints one line
``release: <key>: <value>``:

1. ``config``: ``sdlc.yaml: deploy`` (action, production, command);
2. ``change``: ``--change-id``, else the one ``changes/<id>-<slug>/`` the PR touches (zero or
   several -> ``skip``);
3. ``pr``: the PR must be merged and be the change's build PR, head ``sdlc/<id>/c`` (else
   ``skip``: an owner's PR that touches ``changes/<id>-*/`` after the merge never releases
   again);
4. ``phase``: ``status.yaml`` read as on the default branch must be at phase (e) (else
   ``skip``);
5. ``approval``: with production declared, the release label applied by a person (the only
   route: decision 11, a run cannot approve itself); without it ``waiting`` + ``route`` and a
   green exit (the ``labeled`` event re-runs the workflow);
6. ``done`` / ``exit``: ``deploy.action none`` or an empty ``deploy.command`` release nothing;
   otherwise the command runs on the runner and its output streams to the log.

``$GITHUB_STEP_SUMMARY`` gets the same lines when it is set. Nothing is written into the
repository (the automation identity cannot write to the default branch).

The command runs without a shell (argument lists only): one command, or several joined by
``&&`` that run in order and stop at the first failure; a word with ``*``, ``?`` or ``[`` is
expanded against the project root like a shell glob (kept literal when nothing matches);
other shell operators (``|``, ``;``, ``||``, redirections) are refused as a configuration
error. The executable is resolved on PATH (``.cmd``/``.exe`` shims on Windows).

Exit codes: 0 done, skip or waiting · 1 the release command failed (a failed release is red:
infrastructure, not a park) · 2 usage or configuration error.
"""

from __future__ import annotations

import argparse
import glob
import inspect
import os
import re
import shlex
import shutil
import subprocess
import sys
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

PLUGIN_DIR = Path(__file__).resolve().parent.parent
if str(PLUGIN_DIR) not in sys.path:
    sys.path.insert(0, str(PLUGIN_DIR))

from hooks._common import ConfigError, load_sdlc_config  # noqa: E402
from release import approval as approval_mod  # noqa: E402
from state import conventions as c  # noqa: E402

CHANGE_FILE_RE = re.compile(r"^changes/(\d{4})-[^/]+/")
UNSUPPORTED = ("||", "|", ";", ">", ">>", "<", "&", "2>", "2>&1", "(", ")")
DEFAULT_TIMEOUT = 900  # seconds, when sdlc.yaml has no gate.command_timeout


class UsageError(RuntimeError):
    pass


def _github() -> tuple[Any, str]:
    return approval_mod.load_github()


def _call(github: Any, name: str, *args: Any, **kwargs: Any) -> dict[str, Any]:
    return approval_mod._call(github, name, *args, **kwargs)


def _read_status(change_dir: Path, production: bool = False) -> tuple[Any, str]:
    """(Status, note). ``read_status(change_dir, on_default_branch=True)`` when the state
    module has the parameter (plus ``production=production`` when it has that one too);
    otherwise the plain read and a note saying so."""
    from state import status as status_mod

    reader = status_mod.read_status
    try:
        params = inspect.signature(reader).parameters
    except (TypeError, ValueError):
        params = {}
    if "on_default_branch" in params:
        kwargs: dict[str, Any] = {"on_default_branch": True}
        if "production" in params:
            kwargs["production"] = production
        return reader(change_dir, **kwargs), ""
    note = "state/status.py read_status has no on_default_branch: plain read"
    return reader(change_dir), note


def command_chain(command: str, root: Path, posix: bool | None = None) -> list[list[str]]:
    """The argument lists of ``deploy.command``: one per ``&&``-joined step."""
    posix = (os.name != "nt") if posix is None else posix
    lexer = shlex.shlex(command, posix=posix, punctuation_chars=True)
    lexer.whitespace_split = True
    try:
        tokens = list(lexer)
    except ValueError as exc:
        raise UsageError(f"deploy.command cannot be parsed: {exc}") from exc
    chain: list[list[str]] = [[]]
    for token in tokens:
        if token == "&&":
            chain.append([])
            continue
        if token in UNSUPPORTED or token.startswith((">", "<", "|", ";")):
            raise UsageError(
                f"deploy.command uses the shell operator {token!r}; the release command runs "
                "without a shell: give one command, or steps joined by &&"
            )
        if not posix and len(token) >= 2 and token[0] == token[-1] and token[0] in "\"'":
            token = token[1:-1]
        chain[-1].append(token)
    if any(not step for step in chain):
        raise UsageError("deploy.command has an empty step")
    return [_expand(step, root) for step in chain]


def _expand(step: list[str], root: Path) -> list[str]:
    out = [step[0]]
    for word in step[1:]:
        if any(ch in word for ch in "*?["):
            found = sorted(glob.glob(word, root_dir=str(root)))
            out += found or [word]
        else:
            out.append(word)
    return out


def _timeout(config: Mapping[str, Any]) -> int:
    gate_cfg = config.get("gate") if isinstance(config.get("gate"), dict) else {}
    try:
        return int(gate_cfg.get("command_timeout", DEFAULT_TIMEOUT))
    except (TypeError, ValueError):
        return DEFAULT_TIMEOUT


def run_command(command: str, root: Path, timeout: int) -> tuple[int, str]:
    """Run the chain; (exit code of the first failing step or 0, what happened)."""
    for argv in command_chain(command, root):
        exe = shutil.which(argv[0], path=os.environ.get("PATH")) or argv[0]
        sys.stdout.flush()
        try:
            proc = subprocess.run([exe, *argv[1:]], cwd=str(root), timeout=timeout)
        except FileNotFoundError:
            return 127, f"{argv[0]}: not found"
        except subprocess.TimeoutExpired:
            return 124, f"{argv[0]}: timed out after {timeout}s"
        except OSError as exc:
            return 126, f"{argv[0]}: {exc}"
        if proc.returncode != 0:
            return proc.returncode, f"{argv[0]} exited {proc.returncode}"
    return 0, "ok"


def _summary(lines: list[str], env: Mapping[str, str]) -> None:
    target = env.get("GITHUB_STEP_SUMMARY")
    if not target:
        return
    try:
        with open(target, "a", encoding="utf-8", newline="\n") as fh:
            fh.write("## sdlc release\n\n")
            fh.write("".join(f"- `{line}`\n" for line in lines))
            fh.write("\n")
    except OSError:
        pass  # the summary is a convenience; the log has the same lines


def release(
    args: argparse.Namespace,
    *,
    env: Mapping[str, str] | None = None,
    github: Any = None,
    git: Callable[..., tuple[int, str]] | None = None,
    out: Callable[[str], None] = print,
) -> int:
    env = os.environ if env is None else env
    lines: list[str] = []

    def say(key: str, value: str) -> None:
        line = f"release: {key}: {value}"
        lines.append(line)
        out(line)

    code = _release(args, env, github, git, say)
    _summary(lines, env)
    return code


def _release(args, env, github, git, say) -> int:
    root = Path(args.root).resolve()
    # (1) configuration
    try:
        config = load_sdlc_config(str(root))
    except ConfigError as exc:
        say("error", str(exc))
        return 2
    if not config:
        say("error", f"no sdlc.yaml at {root}")
        return 2
    deploy = config.get("deploy") or {}
    if not isinstance(deploy, dict):
        say("error", "sdlc.yaml: deploy must be a mapping")
        return 2
    action = str(deploy.get("action") or "none").strip().lower()
    production = deploy.get("production") is True
    command = str(deploy.get("command") or "").strip()
    say(
        "config",
        f"action={action} production={str(production).lower()} "
        f"command={'set' if command else 'empty'} event={args.event}",
    )
    if github is None:
        github, why = _github()
        if github is None:
            say("error", why)
            return 2
    # (2) the change
    change_id = args.change_id
    if change_id:
        if not c.ID_RE.match(change_id):
            say("error", f"--change-id must be four digits, got {change_id!r}")
            return 2
    else:
        files = _call(github, "pr_files", args.repo, args.pr, cwd=str(root))
        if not files.get("ok"):
            say("error", f"cannot list the files of #{args.pr}: {files.get('reason')}")
            return 2
        ids = sorted(
            {m.group(1) for f in files.get("files") or [] if (m := CHANGE_FILE_RE.match(f))}
        )
        if len(ids) != 1:
            why = "no change folder" if not ids else f"several change folders ({', '.join(ids)})"
            say("skip", f"pull request #{args.pr} touches {why}")
            return 0
        change_id = ids[0]
    say("change", change_id)
    # (3) the pull request must be merged
    pr = _call(github, "pr_by_number", args.repo, args.pr, cwd=str(root))
    if not pr.get("ok"):
        say("error", f"cannot read #{args.pr}: {pr.get('reason')}")
        return 2
    if not pr.get("merged"):
        say("skip", f"pull request #{args.pr} is not merged")
        return 0
    build_head = c.work_branch(change_id, "c")
    if pr.get("head_ref") != build_head:
        say(
            "skip",
            f"pull request #{args.pr} (head {pr.get('head_ref') or '?'}) is not the build PR "
            f"{build_head} of change {change_id}",
        )
        return 0
    merge_sha = args.merge_sha or pr.get("merge_commit_sha")
    say("pr", f"#{args.pr} merged{f' as {merge_sha}' if merge_sha else ''}")
    # (4) the change is at phase (e), read as on the default branch
    change_dir = c.find_change_dir(root, change_id)
    if change_dir is None:
        say("skip", f"no changes/{change_id}-<slug>/ folder at {root}")
        return 0
    try:
        st, note = _read_status(change_dir, production)
    except Exception as exc:  # noqa: BLE001 - a broken status.yaml is a configuration error
        say("error", f"{change_id} status.yaml could not be read: {exc}")
        return 2
    if note:
        say("note", note)
    if st.phase != "e":
        say("skip", f"change {change_id} is at phase {st.phase}, not e")
        return 0
    say("phase", "e")
    # (5) the release approval (decision 13)
    if production:
        labels = pr.get("labels")
        result = approval_mod.release_approval(
            root,
            config,
            env,
            pr_number=args.pr,
            repo=args.repo,
            git=git,
            github=github,
            pr_labels=list(labels) if isinstance(labels, list) else None,
        )
        if not result.approved:
            say("waiting", result.detail)
            say("route", f"apply {approval_mod.RELEASE_LABEL} on #{args.pr}")
            return 0
        say("approval", f"{result.how} ({result.detail})")
    # (6) the adapter's action
    if action == "none":
        say("done", "nothing to release (deploy.action none)")
        return 0
    if not command:
        say("done", "release prepared in the PR; deploy.command is empty, nothing runs")
        return 0
    say("run", command)
    try:
        code, what = run_command(command, root, _timeout(config))
    except UsageError as exc:
        say("error", str(exc))
        return 2
    say("exit", str(code))
    if code != 0:
        say("failed", what)
        return 1
    say("done", f"deploy.command exited 0 (deploy.action {action})")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="sdlc-release",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = p.add_subparsers(dest="verb", required=True)
    run = sub.add_parser("run", help="the release workflow's step")
    run.add_argument("--root", default=".")
    run.add_argument("--repo", required=True, help="owner/repo")
    run.add_argument("--pr", required=True, type=int, help="the build PR's number")
    run.add_argument("--event", choices=("closed", "labeled"), default="closed")
    run.add_argument(
        "--merge-sha", default=None, help="shown on the pr line only; never an approval"
    )
    run.add_argument("--change-id", default=None)
    return p


def main(argv: list[str] | None = None, **inject: Any) -> int:
    try:
        args = build_parser().parse_args(argv)
    except SystemExit as exc:  # argparse: usage error
        return 2 if exc.code else 0
    reconfigure = getattr(sys.stdout, "reconfigure", None)
    if callable(reconfigure):
        try:
            reconfigure(encoding="utf-8", errors="replace")
        except (OSError, ValueError):
            pass
    return release(args, **inject)


if __name__ == "__main__":
    sys.exit(main())
