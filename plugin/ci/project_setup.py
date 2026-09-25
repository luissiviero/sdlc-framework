"""Install the project's own toolchain before a phase runs (build guide step 30).

    python framework/plugin/ci/project_setup.py --root . [--ref <git ref>]

A GitHub-hosted runner carries neither the project nor the tools its targets call: the first
live design run (2026-09-21) parked at gate (b) because ``python -m pytest`` answered
``/usr/bin/python: No module named pytest``. The phase job therefore runs this step between
the runner setup and ``run_phase.py``.

It reads one line of configuration, ``sdlc.yaml: commands.setup`` — the one-command install
/sdlc-init detects (``python -m pip install -e ".[dev]"``, ``npm ci``, ...). An empty value
means the project has nothing to install and is not an error. The command runs through the
platform shell, like the gate's own targets, so the same line works on Windows and on a
Linux runner.

``--ref`` reads ``sdlc.yaml`` from that git ref (``git show <ref>:sdlc.yaml`` in ``--root``)
instead of the working tree. The runbook workflow passes
``refs/remotes/origin/<default branch>``: it checks out the incident PR's head, and its Go
step holds the project's runbook secrets, so the head's copy of ``commands.setup`` is not the
owner's approved one and could plant a command that runs before that step (choice 80's
pattern: ``detect/cli.py`` reads ``sdlc.yaml`` and ``bands.yaml`` from ``origin/<default>``
the same way). Any ref is accepted, but the workflow passes the fully qualified one because
git resolves ``refs/tags/<name>`` before ``refs/remotes/<name>``: a tag named
``origin/main``, fetched by ``actions/checkout`` with ``fetch-depth: 0``, would otherwise
shadow the remote-tracking ref. An unreadable ref or unparsable text is an error, never a
fallback to the checkout's copy.

Pinning the command string is not enough: the approved command (``pip install -e ".[dev]"``,
``npm ci``, ...) still runs in the head's tree, so the head's ``pyproject.toml``,
``requirements.txt`` or ``package.json`` lifecycle scripts would run before the Go step
(review of 2026-09-25). The incident PR head ``sdlc/<id>/a`` is created by the framework
from the default branch and only the maintain session writes into it, under
``changes/<id>-<slug>/`` (gate (f)'s ``design_scope`` check refuses a source file there). So
with ``--ref`` the step first lists ``git diff --name-only <ref>...HEAD`` in ``--root`` and
refuses, running nothing, when any path lies outside ``changes/``; a ``git diff`` that fails
is refused too (fail closed). The check compares commits: the working tree's uncommitted
state is not its concern, the committed head is.

Prints JSON. Exit 0 when the command exited 0 or there was nothing to run, 1 when it failed
or timed out, 2 on a usage error.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

PLUGIN_DIR = Path(__file__).resolve().parent.parent  # <framework root>/plugin
if str(PLUGIN_DIR) not in sys.path:
    sys.path.insert(0, str(PLUGIN_DIR))

from gate.checks import run_command  # noqa: E402
from hooks._common import SDLC_FILE, ConfigError, load_sdlc_config  # noqa: E402
from state import status as status_mod  # noqa: E402
from state.conventions import CHANGES_DIR  # noqa: E402

EXIT_OK, EXIT_FAILED, EXIT_USAGE = 0, 1, 2
TIMEOUT_SECONDS = 15 * 60  # an install, not a build: fifteen minutes is generous
OUTPUT_TAIL = 4000  # characters of output kept in the JSON result
NOTHING_TO_RUN = "no setup command"
PATHS_SHOWN = 5  # paths named in the refusal's error line (the JSON lists them all)


def setup_command(config: dict[str, Any]) -> str:
    """``sdlc.yaml: commands.setup``, or "" when the project declares none."""
    cmds = config.get("commands")
    value = cmds.get("setup") if isinstance(cmds, dict) else None
    return value.strip() if isinstance(value, str) else ""


def config_at_ref(root: Path, ref: str) -> dict[str, Any]:
    """``sdlc.yaml`` as committed at ``ref`` (``git show <ref>:sdlc.yaml`` in ``root``),
    parsed with the same reader as ``detect/cli.py approved_files``. Raises ``ValueError``
    with the reason when the ref or the file cannot be read or parsed: the caller fails
    closed and never falls back to the checkout's copy."""
    if not ref or ref.startswith("-"):
        raise ValueError("not a git ref")  # never let the value read as a git option
    try:
        proc = subprocess.run(
            ["git", "show", f"{ref}:{SDLC_FILE}"],
            cwd=str(root),
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
    except OSError as exc:
        raise ValueError(f"git could not run: {exc}") from exc
    if proc.returncode != 0:
        lines = [ln.strip() for ln in (proc.stderr or "").splitlines() if ln.strip()]
        raise ValueError(lines[-1] if lines else f"git show exited {proc.returncode}")
    try:
        data = status_mod.yamlish.loads(proc.stdout)
    except status_mod.yamlish.YamlishError as exc:
        raise ValueError(str(exc)) from exc
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ValueError("the top level is not a mapping")
    return data


def paths_changed_outside_changes(root: Path, ref: str) -> list[str]:
    """The paths the committed ``HEAD`` changed relative to ``ref`` (``git diff --name-only
    <ref>...HEAD``, from their merge base) that lie outside ``changes/``, sorted. Renames are
    listed as a deletion and an addition, so a file moved into ``changes/`` still names its
    old path. Uncommitted working-tree edits are not listed. Raises ``ValueError`` when git
    cannot answer: the caller fails closed."""
    if not ref or ref.startswith("-"):
        raise ValueError("not a git ref")  # never let the value read as a git option
    try:
        proc = subprocess.run(
            ["git", "diff", "--name-only", "--no-renames", "-z", f"{ref}...HEAD", "--"],
            cwd=str(root),
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
    except OSError as exc:
        raise ValueError(f"git could not run: {exc}") from exc
    if proc.returncode != 0:
        lines = [ln.strip() for ln in (proc.stderr or "").splitlines() if ln.strip()]
        raise ValueError(lines[-1] if lines else f"git diff exited {proc.returncode}")
    prefix = f"{CHANGES_DIR}/"
    paths = {p for p in (proc.stdout or "").split("\0") if p}
    return sorted(p for p in paths if not p.startswith(prefix))


def run_setup(
    root: Path, timeout: int = TIMEOUT_SECONDS, ref: str | None = None
) -> tuple[dict[str, Any], int]:
    """(result, exit code). A project with no setup command is skipped, not failed. With
    ``ref``, the command comes from that ref's ``sdlc.yaml``, a head that changed files outside
    ``changes/`` relative to it runs nothing, and the result names the ref."""
    root = Path(root).resolve()
    extra: dict[str, Any] = {"ref": ref} if ref else {}
    if ref:
        try:
            config = config_at_ref(root, ref)
        except ValueError as exc:
            return {"error": f"{SDLC_FILE} at {ref} could not be read: {exc}"}, EXIT_FAILED
        try:
            outside = paths_changed_outside_changes(root, ref)
        except ValueError as exc:
            error = f"could not list the files the checkout changed relative to {ref}: {exc}"
            return {"error": error, "ref": ref}, EXIT_FAILED
        if outside:
            where = f"outside {CHANGES_DIR}/ relative to {ref}"
            error = f"the checkout changed files {where}: {', '.join(outside[:PATHS_SHOWN])}"
            return {"error": error, "ref": ref, "paths": outside}, EXIT_FAILED
    else:
        try:
            config = load_sdlc_config(str(root)) or {}
        except ConfigError as exc:
            return {"error": f"sdlc.yaml is unreadable: {exc}"}, EXIT_FAILED
    command = setup_command(config)
    if not command:
        return {"skipped": NOTHING_TO_RUN, **extra}, EXIT_OK
    run = run_command(command, root, timeout, tail=OUTPUT_TAIL)
    exit_code = run.get("exit_code")
    result = {
        "command": command,
        "exit_code": exit_code,
        "output": run.get("output", ""),
        "ok": exit_code == 0,
        "timeout": timeout if exit_code is None else None,
        **extra,
    }
    return result, EXIT_OK if exit_code == 0 else EXIT_FAILED


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="sdlc-project-setup",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--root", default=".", help="the project checkout")
    p.add_argument(
        "--timeout",
        type=int,
        default=TIMEOUT_SECONDS,
        help=f"seconds the install may take (default {TIMEOUT_SECONDS})",
    )
    p.add_argument(
        "--ref",
        default=None,
        help=(
            "read sdlc.yaml from this git ref (e.g. refs/remotes/origin/main), never the "
            "working tree, and refuse a head that changed files outside changes/"
        ),
    )
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.timeout <= 0:
        print("--timeout must be a positive number of seconds", file=sys.stderr)
        return EXIT_USAGE
    result, code = run_setup(Path(args.root), args.timeout, ref=args.ref or None)
    print(json.dumps(result, indent=2, sort_keys=True))
    return code


if __name__ == "__main__":
    sys.exit(main())
