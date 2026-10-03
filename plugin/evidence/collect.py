"""Collect the phase (d) evidence: run the three ``sdlc.yaml`` commands and store what they
printed (build guide step 28; article p.27-29 — the evidence is the toolchain's own output,
not a summary of it).

    python "${CLAUDE_PLUGIN_ROOT}/plugin/evidence/collect.py" --root . --id 0001 \
        [--only test lint] [--timeout 900]

For each target it writes ``changes/<id>-<slug>/evidence/<target>.log`` whose first line is

    # <command> — exit <code> — <seconds>s — <ISO-8601 UTC>

(``exit timeout`` when the command was killed at the timeout) followed by the literal
combined stdout+stderr. ``gate/checks.py: check_evidence`` reads that header back, so a red
log parks the change. It also creates ``evidence/screenshots/`` (with a ``.gitkeep``) for the
UI proof of a change whose plan names one, and prints

    {"all_green": bool, "results": {"test": {"exit", "seconds", "log", "timed_out"}, ...}}

Exit codes: 0 every collected target exited 0 · 1 a target failed or timed out · 2 a usage
error — no change folder, no ``sdlc.yaml``, or a target ``sdlc.yaml`` does not define (that
one is reported as ``"exit": "none"`` and ``all_green`` is false; the gate refuses a project
without the three commands anyway, build guide step 14).

The commands run through ``gate/checks.py: run_command``: the platform shell, the timeout of
``sdlc.yaml: gate.command_timeout`` (or ``--timeout``) and a process-group kill on a hang, so
a wedged test suite cannot hold the run open on Windows or Linux.

Inside a CI session (item 3b, 0.3.2; issue #91) nothing runs here: the runner marks the
session's environment (``SDLC_GATE_COMMANDS=runner``, the mark the gate's ``commands`` check
reads too), and each selected log gets the first line

    # <command> — deferred to the runner — <ISO-8601 UTC>

and a sentence saying so. The runner's commands step after the session runs the three
targets once, outside the sandbox, writes their output into these logs and re-judges the
gate; the gate accepts the mark only while that step is still to come. The summary then reads
``{"all_green": null, "deferred": true, "results": {"test": {"exit": "deferred", ...}}}``,
exit 0: the session has nothing to fix or to read until the runner has run the targets.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

PLUGIN_DIR = Path(__file__).resolve().parent.parent
if str(PLUGIN_DIR) not in sys.path:
    sys.path.insert(0, str(PLUGIN_DIR))

from gate import artifacts as art  # noqa: E402
from gate import checks  # noqa: E402
from hooks._common import ConfigError, load_sdlc_config  # noqa: E402
from state import conventions as c  # noqa: E402

TARGETS = ("test", "build", "lint")  # the order the logs are produced in
MISSING = "none"  # the exit field of a target sdlc.yaml does not define
DEFERRED = "deferred"  # the exit field inside a CI session: the runner runs the target later


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def deferred_to_runner() -> bool:
    """Whether this process runs inside a CI session whose targets the runner runs after it
    (``gate.checks.COMMANDS_RUNNER_ENV``; item 3b)."""
    return os.environ.get(checks.COMMANDS_RUNNER_ENV) == checks.RUN_BY_RUNNER


def ensure_screenshots_dir(evidence_dir: Path) -> Path:
    """``evidence/screenshots/`` for the UI proof of step 28; git keeps an empty dir only
    with a file in it, so a ``.gitkeep`` goes with it."""
    shots = evidence_dir / art.EVIDENCE_SCREENSHOTS
    shots.mkdir(parents=True, exist_ok=True)
    keep = shots / ".gitkeep"
    if not keep.exists():
        keep.write_text("", encoding="utf-8")
    return shots


def collect(
    root: Path,
    change_id: str,
    only: list[str] | None = None,
    timeout: int | None = None,
) -> tuple[dict, int]:
    """(report, exit code). Runs the selected targets and writes their logs."""
    root = Path(root).resolve()
    change_dir = c.find_change_dir(root, change_id)
    if change_dir is None:
        return {"error": f"no change folder for id {change_id}"}, 2
    try:
        config = load_sdlc_config(str(root))
    except ConfigError as exc:
        return {"error": str(exc)}, 2
    if not config:
        return {"error": "sdlc.yaml not found: run /sdlc-init first"}, 2
    commands = checks.commands_from_config(config)
    if timeout is None:
        gate_cfg = config.get("gate") if isinstance(config.get("gate"), dict) else {}
        try:
            timeout = int(gate_cfg.get("command_timeout", checks.DEFAULT_COMMAND_TIMEOUT))
        except (TypeError, ValueError):
            timeout = checks.DEFAULT_COMMAND_TIMEOUT
    selected = [t for t in TARGETS if not only or t in only]
    evidence_dir = change_dir / art.EVIDENCE_DIR
    ensure_screenshots_dir(evidence_dir)
    results: dict[str, dict] = {}
    all_green, usage_error = True, False
    deferred = deferred_to_runner()
    for target in selected:
        log = evidence_dir / art.EVIDENCE_TARGETS[target]
        rel = str(log.relative_to(root)).replace("\\", "/")
        command = commands.get(target)
        if not command:
            all_green, usage_error = False, True
            results[target] = {"exit": MISSING, "seconds": 0.0, "log": None, "timed_out": False}
            continue
        if deferred:
            # a CI session: the mark, never the target (the runner writes the real log)
            art.write_evidence_log(
                log, art.render_deferred_header(command, _now()), art.EVIDENCE_DEFERRED_BODY
            )
            results[target] = {"exit": DEFERRED, "seconds": 0.0, "log": rel, "timed_out": False}
            continue
        started = time.monotonic()
        run = checks.run_command(command, root, timeout, tail=None)
        seconds = round(time.monotonic() - started, 1)
        exit_code = run["exit_code"]
        timed_out = "timeout" in run
        art.write_evidence_log(
            log,
            art.render_evidence_header(command, exit_code, seconds, _now()),
            run["output"] or "",
        )
        if exit_code != 0:
            all_green = False
        results[target] = {
            "exit": exit_code,
            "seconds": seconds,
            "log": rel,
            "timed_out": timed_out,
        }
    report: dict = {"all_green": all_green, "results": results}
    if deferred:
        # nothing ran: the verdict is the runner's, and the summary says so
        report["all_green"] = None if not usage_error else False
        report["deferred"] = True
    if usage_error:
        report["error"] = (
            "sdlc.yaml defines no "
            + ", ".join(t for t, r in results.items() if r["exit"] == MISSING)
            + " command"
        )
        return report, 2
    return report, 0 if all_green else 1


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="sdlc-evidence",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--root", default=".")
    p.add_argument("--id", required=True, help="change id, e.g. 0001")
    p.add_argument(
        "--only", nargs="*", default=None, choices=TARGETS, help="collect these targets only"
    )
    p.add_argument("--timeout", type=int, default=None, help="seconds per command")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        report, code = collect(Path(args.root), args.id, args.only, args.timeout)
    except ValueError as exc:  # a malformed change id
        print(f"evidence: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(report, indent=2, sort_keys=True))
    if "error" in report:
        print(f"evidence: {report['error']}", file=sys.stderr)
    return code


if __name__ == "__main__":
    sys.exit(main())
