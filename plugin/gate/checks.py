"""The deterministic checks of the confidence gate (build guide step 16; OPERATING_MODEL
section 3). Each check is a function ``(GateContext) -> CheckResult``; ``CHECKS_BY_PHASE``
says which run at the gate of which phase. A failed check carries ``need``: the sentence the
"What I need from you" block shows the owner (decision 11).

The gate judges HEAD, not the working tree (OPERATING_MODEL section 3: "HEAD rather than the
working tree"): ``plan_sync``, ``design_scope``, ``guardrails`` and ``risk_list`` read the
committed diff (``diff.committed_files``: merge base...HEAD, the PR's own diff), and
``clean_tree`` is the only check that looks at the working tree — its job is to say that
the work was committed at all. Those four fail (``_no_base``) when no default branch exists
to take the merge base from: an empty committed diff would otherwise pass them silently.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import signal
import stat
import subprocess
import sys
import time
from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PLUGIN_DIR = Path(__file__).resolve().parent.parent
if str(PLUGIN_DIR) not in sys.path:
    sys.path.insert(0, str(PLUGIN_DIR))

from gate import artifacts as art  # noqa: E402
from gate import diff as diffmod  # noqa: E402
from gate import risk as risk_mod  # noqa: E402
from gate.diff import Diff  # noqa: E402
from gate.policy import automation_identity, is_automation  # noqa: E402
from hooks import plan_sync, protected_paths  # noqa: E402
from hooks._common import matches  # noqa: E402
from lessons import index as lessons_mod  # noqa: E402
from state import conventions as c  # noqa: E402
from state import yamlish  # noqa: E402
from state.status import STATUS_FILE, Status  # noqa: E402

PLACEHOLDER_COMMAND_RE = re.compile(r"^\s*echo\s+no\s+\w+\s+target\s*$", re.IGNORECASE)
DEFAULT_COMMAND_TIMEOUT = 900  # seconds per command; sdlc.yaml: gate.command_timeout
OUTPUT_TAIL = 4000  # characters of command output kept in the gate result
DEFAULT_DRIVE_TIMEOUT = 300  # seconds; sdlc.yaml: gate.drive_timeout (change 0004)
DEFAULT_PROOF_IMAGE_KB = 50  # sdlc.yaml: gate.proof_image_kb, after filmcraft's golden cap
PROOF_DIR_ENV = "SDLC_PROOF_DIR"  # the absolute evidence/proof/ the drive writes into
CHANGE_ID_ENV = "SDLC_CHANGE_ID"
DRIVE_PHASES = (
    c.BUILD,
    c.TEST,
    c.DEPLOY,
)  # the gates whose runner step runs the drive, never (design)
# Issue #91 (0.3.0): the runner sets this in the model's session's environment, and the gate
# run inside the session then records its ``commands`` check as deferred instead of running
# the project's targets inside Claude Code's sandbox, where ``Read(**/.env*)`` makes a nested
# ``.env*`` unreadable (change 0001's design run of 2026-10-02: ``python -m pytest`` failed on
# this repository's own fixture ``.env``). The runner runs the check after the session,
# outside the sandbox (``gate.run_deferred_commands``, ``cli.py run-commands``).
COMMANDS_RUNNER_ENV = "SDLC_GATE_COMMANDS"
RUN_BY_RUNNER = "runner"
COMMANDS_DEFERRED_REASON = (
    "deferred to the runner: build, test and lint run after the model's session, outside its "
    "sandbox (issue #91); not yet run"
)


@dataclass
class CheckResult:
    name: str
    ok: bool
    reason: str
    need: str = ""  # what the owner must do when the check fails
    details: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "ok": self.ok,
            "reason": self.reason,
            "need": self.need,
            "details": self.details,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CheckResult:
        """A check read back from ``evidence/gate-<phase>.json`` (``as_dict`` inverted)."""
        details = data.get("details")
        return cls(
            str(data.get("name") or ""),
            bool(data.get("ok")),
            str(data.get("reason") or ""),
            str(data.get("need") or ""),
            dict(details) if isinstance(details, dict) else {},
        )


@dataclass
class GateContext:
    root: Path
    change_dir: Path
    phase: str
    status: Status
    config: dict[str, Any]  # sdlc.yaml as committed on the base when the diff changes it
    diff: Diff | None  # None when the project is not a git repository
    human_gate: bool
    diff_error: str = ""
    config_note: str = ""  # set when the config was taken from the merge base
    # issue #91 (0.3.0): the runner runs the ``commands`` check after the session (set from
    # ``COMMANDS_RUNNER_ENV`` by ``gate.build_context``; a by-hand gate runs them itself)
    commands_deferred: bool = False

    def __post_init__(self) -> None:
        self.phase = c.phase_name(self.phase)  # R45: a letter an older caller passes

    @property
    def evidence_dir(self) -> Path:
        return self.change_dir / art.EVIDENCE_DIR

    @property
    def change_rel(self) -> str:
        return str(self.change_dir.relative_to(self.root)).replace("\\", "/")

    def artifact(self, name: str) -> str | None:
        return art.read_text(self.change_dir / name)

    def approved_base(self) -> str | None:
        """The commit the approved copies are read at: the merge base with the default
        branch, or, on the fast lane (decision 30), the commit ``status.yaml: fast_lane``
        records for this phase while it stands (``diff.fast_lane_sha``: the owner's unmerged
        intent PR head for (design), the design commit gate (design) passed on for build to deploy).
        None when there is no base to compare with."""
        if self.diff is None:
            return None
        return diffmod.approved_base(
            self.root,
            self.status.fast_lane,
            self.phase,
            self.diff.merge_base,
            self.diff.base,
            self.diff.head or "HEAD",
        )

    def approved_artifact(self, name: str) -> str | None:
        """The artifact as committed on the base branch (what the owner approved; on the
        fast lane, at the commit ``approved_base`` names), falling back to the working tree
        only when there is no base to compare with."""
        base = self.approved_base()
        if self.diff is not None and base:
            committed = diffmod.file_at(self.root, base, f"{self.change_rel}/{name}")
            if committed is not None:
                return committed
            if f"{self.change_rel}/{name}" in self.diff.files:
                return None  # new on this branch: not approved by anyone yet
        return self.artifact(name)

    def gate_setting(self, key: str, default):
        gate_cfg = self.config.get("gate")
        if isinstance(gate_cfg, dict) and key in gate_cfg:
            return gate_cfg[key]
        return default


def _ok(name: str, reason: str, **details) -> CheckResult:
    return CheckResult(name, True, reason, details=details)


def _fail(name: str, reason: str, need: str, **details) -> CheckResult:
    return CheckResult(name, False, reason, need, details)


NO_BASE_REASON = "no base branch: the committed diff cannot be judged"
NO_BASE_NEED = (
    "Run the gate in a checkout whose default branch exists (origin/HEAD, main or master)"
)
NO_MERGE_BASE_REASON = "no merge base with {base}: the committed diff cannot be judged"
NO_MERGE_BASE_NEED = (
    "Start the branch from the default branch, or fetch its whole history (fetch-depth: 0): "
    "a branch that shares no commit with {base} has no committed diff to judge"
)


def _no_base(ctx: GateContext, name: str) -> CheckResult | None:
    """The failure of a check that judges the committed diff when there is nothing to judge
    it against: ``diff.default_base`` found no default branch at all (``diff.collect`` then
    compares HEAD with itself, ``base`` "HEAD", and the committed diff is empty whatever the
    branch carries), or the base exists and shares no history with HEAD (an orphan branch,
    a shallow clone: ``merge_base`` None, and the committed diff is empty the same way —
    the readiness review's group B, 0.2.27). A checkout of the default branch itself is
    neither case: its merge base is HEAD because nothing was committed on top of the base
    yet."""
    if ctx.diff is None:
        return None
    if ctx.diff.base == "HEAD":
        return _fail(name, NO_BASE_REASON, NO_BASE_NEED, note=ctx.diff.note)
    if ctx.diff.merge_base is None:
        return _fail(
            name,
            NO_MERGE_BASE_REASON.format(base=ctx.diff.base),
            NO_MERGE_BASE_NEED.format(base=ctx.diff.base),
            note=ctx.diff.note,
        )
    return None


# --- 1. artifact exists and matches its template ---------------------------------------------
def check_artifacts(ctx: GateContext) -> CheckResult:
    problems: list[str] = []
    for name in art.REQUIRED_ARTIFACTS.get(ctx.phase, ()):
        text = ctx.artifact(name)
        if text is None or not text.strip():
            problems.append(f"{name} is missing or empty")
            continue
        required = art.ARTIFACT_SECTIONS[name]
        missing = art.missing_sections(text, required)
        if missing:
            problems.append(f"{name} lacks sections: {', '.join(missing)}")
        empty = art.empty_sections(text, required)
        if empty:
            problems.append(f"{name} has empty sections: {', '.join(empty)}")
        if name == "intent.md":
            head = text.split("## ", 1)[0]
            lacking = [f for f in art.INTENT_HEADER_FIELDS if f not in head]
            if lacking:
                problems.append(f"intent.md header lacks {', '.join(lacking)}")
            if ctx.status.entry_route == "incident":
                # p.44 step 5: "the anomaly and its evidence"; the intent-template skill adds
                # the section for incidents only
                if art.missing_sections(text, (art.INTENT_EVIDENCE_SECTION,)):
                    problems.append(f"intent.md lacks section {art.INTENT_EVIDENCE_SECTION}")
                elif art.empty_sections(text, (art.INTENT_EVIDENCE_SECTION,)):
                    problems.append(f"intent.md has an empty {art.INTENT_EVIDENCE_SECTION}")
        if name == "spec.md":
            # the header logs the prompt, the plugin pin and the skills in force (p.14)
            head = text.split("## ", 1)[0]
            lacking = [f for f in art.SPEC_HEADER_FIELDS if f not in head]
            if lacking:
                problems.append(f"spec.md header lacks {', '.join(lacking)}")
            # R54: a quick intent's assumptions are what the owner corrects on the PR
            if art.is_quick_intent(ctx.artifact("intent.md") or ""):
                body = art.split_sections(text).get(art.SPEC_ASSUMED_SECTION, "")
                if not re.search(r"(?m)^\s*(?:[-*]|\d+[.)])\s+\S", body):
                    problems.append(
                        f"spec.md of a quick intent lists nothing under {art.SPEC_ASSUMED_SECTION}"
                    )
    if problems:
        return _fail(
            "artifacts",
            "; ".join(problems),
            "Complete the phase artifact so it matches its template (intent-template, "
            "spec-template and plan-template skills; the sections and header fields are "
            "defined in plugin/gate/artifacts.py).",
            problems=problems,
        )
    return _ok("artifacts", "every required artifact exists and has its template sections")


# --- 2. no open flagged concern in spec.md (step 23: the deterministic gate check) ------------
def check_open_concerns(ctx: GateContext) -> CheckResult:
    spec = ctx.artifact("spec.md")
    if spec is None:
        return _ok("open_concerns", "no spec.md at this gate")
    concerns = art.open_concerns(spec)
    if concerns:
        return _fail(
            "open_concerns",
            f"{len(concerns)} flagged concern(s) still open in spec.md",
            "Close each open item under '## Flagged concerns' with a decision "
            "(article p.14 step 4), or leave a review comment for /sdlc-fix.",
            open=concerns,
        )
    return _ok("open_concerns", "no open flagged concern")


# --- 3. tests/build/lint green via the sdlc.yaml commands (step 14: refuse to enter (build)) -----
def commands_from_config(config: dict[str, Any]) -> dict[str, str]:
    """The usable ``sdlc.yaml: commands`` targets ("echo no lint target" is not one). Shared
    with plugin/evidence/collect.py so the gate and the evidence writer run the same lines."""
    cmds = config.get("commands")
    out: dict[str, str] = {}
    if isinstance(cmds, dict):
        for key in ("build", "test", "lint"):
            value = _usable(cmds.get(key))
            if value:
                out[key] = value
    return out


def _usable(value: Any) -> str | None:
    """A command line as ``sdlc.yaml`` gives it, stripped, or None when it is not one (not a
    string, empty, or the "echo no <x> target" placeholder)."""
    if isinstance(value, str) and value.strip() and not PLACEHOLDER_COMMAND_RE.match(value):
        return value.strip()
    return None


def drive_from_config(config: dict[str, Any]) -> str | None:
    """``sdlc.yaml: commands.drive``, the optional fourth target (change 0004, spec R3), or
    None when it is missing, empty or a placeholder. Read apart from ``commands_from_config``
    so the three-target readers (the re-checks of R51 and the release) never run it."""
    cmds = config.get("commands") if isinstance(config, dict) else None
    return _usable(cmds.get("drive")) if isinstance(cmds, dict) else None


def configured_drive_timeout(config: dict[str, Any]) -> int:
    """``sdlc.yaml: gate.drive_timeout`` in seconds, ``DEFAULT_DRIVE_TIMEOUT`` when unset or
    not a positive number."""
    gate_cfg = config.get("gate") if isinstance(config, dict) else None
    value = gate_cfg.get("drive_timeout") if isinstance(gate_cfg, dict) else None
    try:
        seconds = int(value)
    except (TypeError, ValueError):
        return DEFAULT_DRIVE_TIMEOUT
    return seconds if seconds > 0 else DEFAULT_DRIVE_TIMEOUT


def configured_proof_image_kb(config: dict[str, Any]) -> int:
    """``sdlc.yaml: gate.proof_image_kb``, ``DEFAULT_PROOF_IMAGE_KB`` when unset or not a
    positive number, as ``configured_drive_timeout`` reads its setting."""
    gate_cfg = config.get("gate") if isinstance(config, dict) else None
    value = gate_cfg.get("proof_image_kb") if isinstance(gate_cfg, dict) else None
    try:
        kb = int(value)
    except (TypeError, ValueError):
        return DEFAULT_PROOF_IMAGE_KB
    return kb if kb > 0 else DEFAULT_PROOF_IMAGE_KB


def drive_timeout(ctx: GateContext, phase: str) -> int:
    """The drive's timeout at gate ``phase``: capped at 600 s at build and test, whole at (deploy)
    (``limits.drive_timeout_seconds``, spec R4)."""
    from gate import limits  # noqa: PLC0415 - limits imports this module

    return limits.drive_timeout_seconds(ctx.config, phase) or configured_drive_timeout(ctx.config)


def _commands(ctx: GateContext) -> dict[str, str]:
    return commands_from_config(ctx.config)


def _tail(output: str | None, tail: int | None) -> str:
    text = output or ""
    return text if tail is None else text[-tail:]


def _kill_tree(proc: subprocess.Popen) -> None:
    """Kill the shell and everything it started (a hung pytest/npm would otherwise keep the
    pipes open and block the timeout on Windows)."""
    try:
        if os.name == "nt":
            subprocess.run(
                ["taskkill", "/T", "/F", "/PID", str(proc.pid)], capture_output=True, timeout=30
            )
        else:
            os.killpg(proc.pid, signal.SIGKILL)
    except (OSError, subprocess.SubprocessError):
        try:
            proc.kill()
        except OSError:
            pass


def run_command(
    command: str,
    root: Path,
    timeout: int,
    tail: int | None = OUTPUT_TAIL,
    env: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Run one project target through the platform shell (the targets are the owner's own
    one-liners: `npm test`, `python -m pytest`; on Windows the .cmd shims need cmd.exe). The
    command runs in its own process group so a timeout kills the whole tree. ``tail`` caps
    the kept output (the gate result keeps the tail; ``None`` keeps the literal output, which
    is what the evidence writer of step 28 stores). ``env`` replaces the process's own
    environment when given (the runner's toolchain install: no token, no model credential)."""
    group: dict[str, Any] = (
        {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP}  # type: ignore[attr-defined]
        if os.name == "nt"
        else {"start_new_session": True}
    )
    try:
        proc = subprocess.Popen(
            command,
            cwd=str(root),
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            stdin=subprocess.DEVNULL,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=env,
            **group,
        )
    except OSError as exc:
        return {"command": command, "exit_code": None, "output": repr(exc)}
    try:
        output, _ = proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        _kill_tree(proc)
        try:
            output, _ = proc.communicate(timeout=30)
        except subprocess.TimeoutExpired:
            output = ""
        return {
            "command": command,
            "exit_code": None,
            "output": _tail(output, tail),
            "timeout": timeout,
        }
    return {
        "command": command,
        "exit_code": proc.returncode,
        "output": _tail(output, tail),
    }


def check_commands(ctx: GateContext) -> CheckResult:
    """Build, test and lint green. Since 0.3.0 (issue #91) a gate run inside a CI session
    records the check as deferred (``ok`` with ``details.deferred``) when the runner asked for
    it through ``COMMANDS_RUNNER_ENV``: the targets run in the runner's own process after the
    session, outside Claude Code's sandbox, through ``run_commands_check``, and the record is
    rewritten with the result (``gate.run_deferred_commands``). A gate run by hand, or by a
    runner that did not set the variable, runs them here as before."""
    if ctx.commands_deferred:
        return _ok("commands", COMMANDS_DEFERRED_REASON, deferred=True)
    return run_commands_check(ctx)


def missing_targets(ctx: GateContext) -> CheckResult | None:
    cmds = _commands(ctx)
    missing = [k for k in ("build", "test", "lint") if k not in cmds]
    if not missing:
        return None
    return _fail(
        "commands",
        f"sdlc.yaml has no usable {', '.join(missing)} target",
        "Give the project one-command build/test/lint targets in sdlc.yaml "
        "(re-run /sdlc-init or edit sdlc.yaml in a reviewed PR); the framework does not "
        "enter the build phase without them (article p.27 step 1).",
        missing=missing,
    )


def run_targets(ctx: GateContext, only: list[str] | None = None) -> dict[str, dict[str, Any]]:
    """Run the three targets once, keeping the literal output and the seconds each took:
    ``{name: {"command", "exit_code", "output", "seconds"[, "timeout"]}}``. The gate's record
    keeps the tail of the output (``judge_targets``); the evidence logs keep it whole (item
    3b: the runner writes ``test.log``, ``build.log`` and ``lint.log`` from this same run).
    ``only`` names the targets to run (decision 29: the re-run of the targets that did not
    start), all three when None."""
    timeout = int(ctx.gate_setting("command_timeout", DEFAULT_COMMAND_TIMEOUT))
    runs: dict[str, dict[str, Any]] = {}
    for name, cmd in _commands(ctx).items():
        if only is not None and name not in only:
            continue
        started = time.monotonic()
        run = run_command(cmd, ctx.root, timeout, tail=None)
        run["seconds"] = round(time.monotonic() - started, 1)
        runs[name] = run
    return runs


def judge_targets(runs: dict[str, dict[str, Any]], ran_by: str | None = None) -> CheckResult:
    """The ``commands`` check from the targets' runs; ``ran_by`` names who ran them when it
    was not the gate's own process (``RUN_BY_RUNNER``), kept in the check's details."""
    runs = {
        name: {
            k: (_tail(v, OUTPUT_TAIL) if k == "output" else v)
            for k, v in run.items()
            if k != "seconds"
        }
        for name, run in runs.items()
    }
    who = {"ran_by": ran_by} if ran_by else {}
    red = {n: r for n, r in runs.items() if r["exit_code"] != 0}
    if red:
        summary = ", ".join(
            f"{n} ({'timed out' if r['exit_code'] is None else 'exit ' + str(r['exit_code'])})"
            for n, r in red.items()
        )
        return _fail(
            "commands",
            f"not green: {summary}",
            "Make the failing target pass (fix the code, not the test) and re-run the gate. "
            "The tail of each output is in the gate result.",
            runs=runs,
            **who,
        )
    green = (
        "build, test, lint and drive exit 0" if "drive" in runs else "build, test and lint exit 0"
    )
    return _ok("commands", green, runs=runs, **who)


def run_commands_check(ctx: GateContext, ran_by: str | None = None) -> CheckResult:
    """Run the three targets and judge them (``run_targets`` then ``judge_targets``)."""
    missing = missing_targets(ctx)
    if missing is not None:
        return missing
    return judge_targets(run_targets(ctx), ran_by)


# --- 4. evidence present (step 28) --------------------------------------------------------
HEADER_REQUIRED_AT = (c.TEST, c.DEPLOY)  # the gates that read the toolchain's own output
EVIDENCE_DEFERRED_REASON = (
    "deferred to the runner: the session wrote no command log, the runner writes {logs} "
    "from its {targets} after the model's session (issue #91); not yet written"
)


def check_evidence(ctx: GateContext) -> CheckResult:
    drive_set = drive_from_config(ctx.config) is not None
    required = art.required_evidence(ctx.phase, drive_set)
    if not required:
        return _ok("evidence", "no evidence required at this gate")
    command_logs = tuple(art.target_logs(drive_set).values())
    missing = []
    red: list[str] = []
    red_names: list[str] = []
    deferred: list[str] = []
    for name in required:
        path = ctx.evidence_dir / name
        text = path.read_text(encoding="utf-8", errors="replace") if path.is_file() else ""
        if ctx.commands_deferred and name == art.EVIDENCE_DRIVE:
            # change 0004 (R7): the session never runs the drive and leaves no mark for it,
            # so a drive.log already on the tree (a red one a fix round inherits) is not the
            # session's to rewrite; the runner's step writes drive.log and judges this again
            deferred.append(name)
            continue
        if not text.strip():
            missing.append(name)
            continue
        if (
            ctx.commands_deferred
            and name in command_logs
            and art.parse_deferred_header(text) is not None
        ):
            # item 3b: inside a CI session the writer left the mark and the runner writes
            # the real log after the session; the mark is accepted only while that step is
            # still to come (``run_deferred_commands`` re-judges this check without it)
            deferred.append(name)
            continue
        # logs written by evidence/collect.py carry their exit code on the first line; a log
        # that records a failure is evidence of a red run, whatever a later re-run says, and
        # at test and deploy a command log without that header is not evidence at all
        failure = art.evidence_failure(
            text, require_header=ctx.phase in HEADER_REQUIRED_AT and name in command_logs
        )
        if failure:
            red.append(f"evidence/{name}: {failure}")
            red_names.append(name)
    if missing:
        return _fail(
            "evidence",
            f"evidence/ lacks {', '.join(missing)}",
            "The test phase must leave the literal toolchain output and the verifier report in "
            f"{ctx.change_rel}/evidence/ (article p.28–29): write "
            + ", ".join(f"{ctx.change_rel}/evidence/{n}" for n in missing)
            + ' by running `python "${CLAUDE_PLUGIN_ROOT}/plugin/evidence/collect.py" --root . '
            f"--id {ctx.status.id}` (the verifier agent writes verifier.md).",
            missing=missing,
        )
    if red:
        files = ", ".join(f"{ctx.change_rel}/evidence/{n}" for n in red_names)
        return _fail(
            "evidence",
            "; ".join(red),
            "Fix the failing target (fix the code, not the test), then re-run "
            f'`python "${{CLAUDE_PLUGIN_ROOT}}/plugin/evidence/collect.py" --root . --id '
            f"{ctx.status.id}` so {files} records a green run.",
            red=red,
            red_files=red_names,
        )
    if deferred:
        return _ok(
            "evidence",
            EVIDENCE_DEFERRED_REASON.format(
                logs=", ".join(deferred),
                targets="build, test, lint and drive" if drive_set else "build, test and lint",
            ),
            deferred=True,
            deferred_logs=deferred,
        )
    return _ok("evidence", f"evidence present: {', '.join(required)}")


# --- 4b. the drive and its proof (change 0004, ROADMAP R14; spec R2 to R9) -------------------
PROOF_DEFERRED_REASON = (
    "deferred to the runner: the drive runs after the model's session, beside build, test and "
    "lint; not yet run"
)
PROOF_NOT_CHECKED_REASON = (
    "not checked: a gate run by hand runs no drive; `python plugin/evidence/collect.py --root . "
    "--id {id}` runs it and prints the items"
)
PROOF_NO_DRIVE_REASON = "no drive target: nothing to compare"
PROOF_DRIVE_REMOVED_REASON = (
    "drive removed after gate (design): the approved plan names {n} state/screenshot item(s) and "
    "commands.drive is empty"
)
PROOF_DRIVE_REMOVED_NEED = (
    "Restore `commands.drive` in sdlc.yaml in a reviewed PR, then re-run the phase: the plan "
    "the owner approved at gate (design) names proof items only a drive produces, and no run can "
    "change sdlc.yaml or the approved plan."
)
PROOF_NO_MANIFEST_REASON = "the drive ran but wrote no manifest"
PROOF_NO_PLAN_REASON = "the approved plan.md cannot be read, so its proof items cannot be judged"
PROOF_FAILED_NEED = (
    "Make the product produce what the approved plan's proof items say (fix the code, not the "
    "plan); each item, the expected value and the value seen are in the gate result."
)
PROOF_STEP_NEED = (
    "The runner's step could not judge the proof; read the job log and evidence/drive.log, "
    "then re-run the phase."
)
PROOF_ITEMS_NEED = (
    "Fix each item in plan.md's ## Proof to the grammar of the plan-template skill, or, for a "
    "state or screenshot item while commands.drive is empty, set the drive in sdlc.yaml in a "
    "reviewed PR or drop the item; then re-run the design."
)
GITHUB_RUN_VARS = ("GITHUB_RUN_ID", "GITHUB_SERVER_URL", "GITHUB_REPOSITORY", "GITHUB_EVENT_NAME")
PROOF_KINDS = ("state", "screenshot")  # the kinds the drive produces; ``test`` is the suite's


def proof_dir(ctx: GateContext) -> Path:
    return ctx.evidence_dir / art.EVIDENCE_PROOF


def drive_env(ctx: GateContext, base: dict[str, str] | None = None) -> dict[str, str]:
    """The drive's environment: ``base`` (the process's own, which the runner already stripped
    of every credential, ``run_phase.commands_env``) plus ``SDLC_PROOF_DIR`` and
    ``SDLC_CHANGE_ID``; nothing else is added (spec R1)."""
    env = dict(os.environ if base is None else base)
    env[PROOF_DIR_ENV] = str(proof_dir(ctx).resolve())
    env[CHANGE_ID_ENV] = ctx.status.id
    return env


def _clear_read_only(func, path, _exc) -> None:
    """rmtree's error handler: Windows refuses to delete a read-only file."""
    os.chmod(path, stat.S_IWRITE)
    func(path)


def clear_proof_dir(folder: Path) -> None:
    """Empty ``evidence/proof/`` and recreate it, read-only files (Windows) included: a stale
    file never counts (spec R2)."""
    folder = Path(folder)
    if folder.is_symlink() or folder.is_file():
        folder.unlink()
    elif folder.exists() and sys.version_info >= (3, 12):
        shutil.rmtree(folder, onexc=_clear_read_only)
    elif folder.exists():
        shutil.rmtree(folder, onerror=_clear_read_only)
    folder.mkdir(parents=True, exist_ok=True)


def _proof_files(folder: Path) -> list[Path]:
    return sorted(
        (p for p in Path(folder).rglob("*") if p.is_file() and p.name != art.PROOF_MANIFEST),
        key=lambda p: p.relative_to(folder).as_posix(),
    )


def apply_image_caps(folder: Path, max_kb: int) -> list[dict[str, Any]]:
    """Delete the images over ``max_kb`` and, of the rest, those past the tenth by sorted
    relative path (spec R8). Returns the manifest's ``dropped`` entries."""
    dropped: list[dict[str, Any]] = []
    kept = 0
    for path in _proof_files(folder):
        if path.suffix.lower() not in art.PROOF_IMAGE_SUFFIXES:
            continue
        size = path.stat().st_size
        why = ""
        if size > max_kb * 1024:
            why = f"over gate.proof_image_kb ({max_kb} KB)"
        elif kept >= art.PROOF_MAX_IMAGES:
            why = f"past the {art.PROOF_MAX_IMAGES} images a run keeps"
        if why:
            path.unlink()
            dropped.append({"path": path.relative_to(folder).as_posix(), "bytes": size, "why": why})
        else:
            kept += 1
    return dropped


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def manifest_run(env: dict[str, str] | None = None) -> dict[str, Any] | None:
    """The workflow run that produced the proof, from the GitHub variables, or None by hand."""
    env = os.environ if env is None else env
    run_id, server, repo, event = (env.get(name) or None for name in GITHUB_RUN_VARS)
    if run_id is None:
        return None
    url = f"{server}/{repo}/actions/runs/{run_id}" if server and repo else None
    return {"id": run_id, "url": url, "event": event}


def write_manifest(
    folder: Path, head: str | None, phase: str, dropped: list[dict[str, Any]]
) -> dict[str, Any]:
    """``evidence/proof/manifest.json`` (spec R6): which commit and run produced the proof,
    every file with its size, the images dropped by the caps."""
    folder = Path(folder)
    manifest = {
        "schema_version": 1,
        "commit": head,
        "run": manifest_run(),
        "phase": phase,
        "at": _now_iso(),
        "files": [
            {"path": p.relative_to(folder).as_posix(), "bytes": p.stat().st_size}
            for p in _proof_files(folder)
        ],
        "dropped": sorted(dropped, key=lambda d: d["path"]),
    }
    (folder / art.PROOF_MANIFEST).write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n"
    )
    return manifest


def read_manifest(ctx: GateContext) -> dict[str, Any] | None:
    """``evidence/proof/manifest.json``, or None when it is missing or not a JSON object."""
    text = art.read_text(proof_dir(ctx) / art.PROOF_MANIFEST)
    try:
        data = json.loads(text) if text else None
    except ValueError:
        return None
    return data if isinstance(data, dict) else None


def run_drive(
    ctx: GateContext, head: str | None, phase: str, env: dict[str, str] | None = None
) -> dict[str, Any]:
    """Run ``commands.drive`` once (spec R2): clear ``proof/``, run the line through the
    platform shell with ``drive_env`` and the drive's timeout, apply the image caps and write
    the manifest. Returns the run as ``run_targets`` gives one (the literal output, which the
    caller writes to ``drive.log``), ``refused`` naming a capped ``drive_timeout``."""
    from gate import limits  # noqa: PLC0415 - limits imports this module

    command = drive_from_config(ctx.config)
    if command is None:
        raise ValueError("commands.drive is empty: there is no drive to run")
    folder = proof_dir(ctx)
    clear_proof_dir(folder)
    started = time.monotonic()
    run = run_command(
        command,
        ctx.root,
        drive_timeout(ctx, phase),
        tail=None,
        env=drive_env(ctx, env),
    )
    run["seconds"] = round(time.monotonic() - started, 1)
    dropped = apply_image_caps(folder, configured_proof_image_kb(ctx.config))
    write_manifest(folder, head, phase, dropped)
    refused = (
        limits.drive_timeout_refusal(ctx.config) if phase in limits.DRIVE_CAPPED_PHASES else None
    )
    if refused:
        run["refused"] = refused
    return run


def _drive_items(plan_text: str | None) -> list[art.ProofItem]:
    return [i for i in art.proof_items(plan_text or "") if i.kind in PROOF_KINDS]


def item_outcome(item: art.ProofItem, folder: Path, dropped: list[Any]) -> tuple[str, Any]:
    """(outcome, seen) of one ``state`` or ``screenshot`` item against ``proof/``; an image the
    caps dropped says why."""
    rel = item.file[len(art.PROOF_PREFIX) :]
    why = next(
        (d.get("why") for d in dropped if isinstance(d, dict) and d.get("path") == rel), None
    )
    if why:
        return art.OUTCOME_NOT_PRODUCED, f"{item.file} dropped: {why}"
    if item.kind == "screenshot":
        return art.screenshot_outcome(item, folder)
    return art.compare_state(item, folder)


def proof_entries(ctx: GateContext, dropped: list[Any] | None = None) -> list[dict[str, Any]]:
    """The approved plan's items judged against ``proof/``, then the items the working-tree
    plan added (``approved: false``, reported and never the bar; spec R7)."""
    approved = _drive_items(ctx.approved_artifact("plan.md"))
    lines = {i.line for i in approved}
    added = [i for i in _drive_items(ctx.artifact("plan.md")) if i.line not in lines]
    return [
        _entry(item, is_approved, *item_outcome(item, proof_dir(ctx), dropped or []))
        for item, is_approved in [(i, True) for i in approved] + [(i, False) for i in added]
    ]


def _entry(item: art.ProofItem, approved: bool, outcome: str, seen: Any) -> dict[str, Any]:
    """One item of the ``proof`` entry (spec R7); ``seen`` only when it did not match."""
    entry = {
        "item": item.line,
        "kind": item.kind,
        "file": item.file,
        "approved": approved,
        "outcome": outcome,
    }
    if outcome != art.OUTCOME_MATCHES:
        entry["seen"] = seen
    return entry


def judge_proof(ctx: GateContext, manifest: dict[str, Any] | None) -> CheckResult:
    """The ``proof`` entry after a drive run (spec R7): ``ok`` only when every approved item
    matches. A missing manifest or an unreadable approved plan is the step's own failure (no
    ``items``, so never a round)."""
    if manifest is None:
        return _fail("proof", PROOF_NO_MANIFEST_REASON, PROOF_STEP_NEED)
    if ctx.approved_artifact("plan.md") is None:
        return _fail("proof", PROOF_NO_PLAN_REASON, PROOF_STEP_NEED)
    dropped = manifest.get("dropped") if isinstance(manifest.get("dropped"), list) else []
    items = proof_entries(ctx, dropped)
    details = {
        "manifest": f"{art.EVIDENCE_DIR}/{art.EVIDENCE_PROOF}/{art.PROOF_MANIFEST}",
        "run": manifest.get("run"),
        "commit": manifest.get("commit"),
        "items": items,
        "dropped": dropped,
    }
    failed = [i for i in items if i["approved"] and i["outcome"] != art.OUTCOME_MATCHES]
    if failed:
        return _fail(
            "proof",
            f"{len(failed)} approved proof item(s) not met: "
            + "; ".join(f"{i['item']} ({i['outcome']})" for i in failed),
            PROOF_FAILED_NEED,
            **details,
        )
    approved = sum(1 for i in items if i["approved"])
    return _ok("proof", f"{approved} approved proof item(s) matching", **details)


def check_proof(ctx: GateContext) -> CheckResult:
    """The ``proof`` entry of every build, test and deploy record (spec R7). With a drive: deferred
    in a CI session (the runner's step judges it after the drive), ``checked: false`` by hand.
    Without one: judged at once from the approved plan, in CI too."""
    if drive_from_config(ctx.config) is not None:
        if ctx.commands_deferred:
            return _ok("proof", PROOF_DEFERRED_REASON, deferred=True)
        return _ok("proof", PROOF_NOT_CHECKED_REASON.format(id=ctx.status.id), checked=False)
    items = _drive_items(ctx.approved_artifact("plan.md"))
    if not items:
        return _ok("proof", PROOF_NO_DRIVE_REASON)
    return _fail(
        "proof",
        PROOF_DRIVE_REMOVED_REASON.format(n=len(items)),
        PROOF_DRIVE_REMOVED_NEED,
        items=[
            _entry(i, True, art.OUTCOME_NOT_PRODUCED, "no drive ran: commands.drive is empty")
            for i in items
        ],
        drive_removed=True,
    )


def check_proof_items(ctx: GateContext) -> CheckResult:
    """Gate (design) (spec R9): every item of the working-tree plan's ``## Proof`` follows the
    grammar, and a ``state`` or ``screenshot`` item has a drive to produce it."""
    plan = ctx.artifact("plan.md")
    problems = [
        f"plan.md line {i.number}: `{i.line}`: {i.problem}" for i in art.malformed_proof_items(plan)
    ]
    if drive_from_config(ctx.config) is None:
        problems += [
            f"plan.md line {i.number}: `{i.line}` needs commands.drive, which sdlc.yaml "
            "leaves empty"
            for i in _drive_items(plan)
        ]
    if problems:
        return _fail("proof_items", "; ".join(problems), PROOF_ITEMS_NEED, problems=problems)
    return _ok("proof_items", "the Proof items follow the grammar")


# --- 5. no Important review finding (step 26; the tally of p.33) ---------------------------
def load_findings(path: Path) -> tuple[dict[str, Any] | None, str]:
    """(data, error). Format (defined here, produced by the review pass in B3):
    {"schema_version": 1, "head": "<sha>", "findings": [{"pass": "bugs|security|compliance",
     "severity": "important|nit", "file": "...", "line": N, "summary": "..."}],
     "tally": {"important": N, "nit": M}}"""
    if not path.is_file():
        return None, "missing"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return None, f"unreadable: {exc}"
    if not isinstance(data, dict) or not isinstance(data.get("findings"), list):
        return None, "malformed: expected an object with a 'findings' list"
    return data, ""


def important_findings(data: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        f
        for f in data["findings"]
        if isinstance(f, dict) and str(f.get("severity", "")).strip().lower() == "important"
    ]


def check_findings(ctx: GateContext) -> CheckResult:
    path = ctx.evidence_dir / art.REVIEW_FINDINGS
    data, error = load_findings(path)
    if data is None:
        if error == "missing" and ctx.phase not in art.FINDINGS_REQUIRED_AT:
            return _ok(
                "findings", "no review findings yet (the review pass runs in the deploy phase)"
            )
        return _fail(
            "findings",
            f"evidence/{art.REVIEW_FINDINGS} {error}",
            "Run the review passes (REVIEW.md) so they publish their findings JSON.",
        )
    head = ctx.diff.head if ctx.diff else None
    if ctx.phase in art.FINDINGS_REQUIRED_AT:
        if not data.get("head"):
            return _fail(
                "findings",
                f"evidence/{art.REVIEW_FINDINGS} carries no 'head' commit",
                "The review pass must record the commit it reviewed; re-run it.",
            )
        if head and not str(head).startswith(str(data["head"])):
            return _fail(
                "findings",
                f"findings are for commit {str(data['head'])[:10]}, HEAD is {head[:10]}",
                "Re-run the review pass on the current HEAD.",
                stale=True,
            )
    important = important_findings(data)
    settled = _panel_settled_findings(ctx, important)
    blocking = [f for f in important if f not in settled]
    if blocking:
        return _fail(
            "findings",
            f"{len(blocking)} Important review finding(s) open",
            "Fix every Important finding (or have the owner waive it in a review comment; "
            "the review panel may settle one the run cannot fix), then re-run "
            f"the review pass so {ctx.change_rel}/evidence/{art.REVIEW_FINDINGS} shows none.",
            important=blocking[:20],
            settled_by_panel=[str(f.get("summary", "")) for f in settled],
        )
    tally = data.get("tally") if isinstance(data.get("tally"), dict) else {}
    if settled:
        return _ok(
            "findings",
            f"{len(settled)} Important finding(s) settled by the review panel, none open",
            tally=tally,
            settled_by_panel=[str(f.get("summary", "")) for f in settled],
        )
    return _ok("findings", "no Important review finding", tally=tally)


def _panel_entries(ctx: GateContext, kind: str) -> list[dict[str, Any]]:
    """The standing ledger entries of ``kind`` for this phase (decision 21)."""
    from panel import ledger  # noqa: PLC0415

    return [
        e
        for e in ledger.active(ledger.load_ledger(ctx.change_dir, ctx.phase))
        if e.get("kind") == kind
    ]


def _owner_continues(ctx: GateContext) -> list[dict[str, Any]]:
    """The ``park`` lines of this phase's ledger that the owner overturned and whose
    decision upheld the verdict (not ``continue``): the owner's word replaces the panel's
    (``sdlc-fix.md``), so a ``park`` verdict with the same reasons is settled for the
    phase to continue; one with other reasons is a new item (1.0.8, NOTES 45 gap 1)."""
    from panel import ledger  # noqa: PLC0415

    return [
        e
        for e in ledger.load_ledger(ctx.change_dir, ctx.phase)
        if e.get("kind") == "park" and e.get("overturned") and not ledger.decides_continue(e)
    ]


def _panel_settled_findings(
    ctx: GateContext, important: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    from panel import ledger  # noqa: PLC0415
    from review import findings as fmod  # noqa: PLC0415

    keys = {str(e.get("key")) for e in _panel_entries(ctx, "finding")}
    if not keys:
        return []
    return [
        f
        for f in important
        if ledger.finding_key(str(f.get("signature") or fmod.signature(f))) in keys
    ]


# --- 6. plan.md <-> diff (step 12/16; article p.17 'the merged diff still matches plan.md') -----
def _source_files(ctx: GateContext, files: list[str]) -> list[str]:
    exempt = plan_sync.exempt_patterns(ctx.config)
    return [f for f in files if not any(matches(p, f) for p in exempt)]


def check_plan_sync(ctx: GateContext) -> CheckResult:
    """The plan against the **committed** diff (as ``check_design_scope``): the working tree
    is ``check_clean_tree``'s, and inside Claude Code's sandbox the masked ``.env`` shows as
    modified however clean the checkout is - it parked the first gated build run
    (2026-09-22) as "not listed in plan.md". The per-commit rule is the hook's: plan.md in
    the same commit only when the commit departs from the plan (article p.16 step 7)."""
    if ctx.diff is None:
        return _fail("plan_sync", ctx.diff_error, "Run the gate inside the project's git repo.")
    no_base = _no_base(ctx, "plan_sync")
    if no_base:
        return no_base
    plan = ctx.artifact("plan.md") or ""
    planned = art.planned_files(plan)
    committed = diffmod.committed_files(ctx.root, ctx.diff.merge_base, ctx.diff.head)
    source = _source_files(ctx, committed)
    change_id = ctx.status.id
    unplanned = [f for f in source if not any(plan_sync.is_planned(f, p) for p in planned)]
    # the per-commit rule of the plan-sync hook, re-applied to every commit on the branch
    # (catches commits driven from scripts the hook could not parse, NOTES section 9)
    branch = c.branch_name(change_id, c.BUILD)
    exempt = plan_sync.exempt_patterns(ctx.config)
    unsynced = [
        commit.sha[:10]
        for commit in ctx.diff.commits
        if plan_sync.check(branch, commit.files, exempt, planned).block
    ]
    growth = _plan_growth(ctx, planned)
    grown = {"plan_growth": growth} if growth is not None else {}
    problems = []
    if unplanned:
        problems.append(f"{len(unplanned)} changed file(s) not listed in plan.md")
    if unsynced:
        problems.append(f"{len(unsynced)} commit(s) changed source without plan.md")
    if problems:
        return _fail(
            "plan_sync",
            "; ".join(problems),
            "Update '## Files that change' in plan.md to match the diff (article p.16 step 7) "
            "in the same commit as the departure, or revert the unplanned change.",
            unplanned=unplanned[:50],
            unsynced_commits=unsynced,
            **grown,
        )
    unrealised = [p for p in planned if not any(plan_sync.is_planned(f, p) for f in committed)]
    return _ok(
        "plan_sync",
        "every committed source file is in plan.md",
        planned_but_unchanged=unrealised,
        **grown,
    )


def _plan_growth(ctx: GateContext, planned: list[str]) -> dict[str, list[str]] | None:
    """The files plan.md lists now and the copy the owner approved at gate (design) did not, and
    the reverse (R26, choice 257: R60's port): the build PR's banner shows the first, the
    digest counts it. None at (design), where the plan is being written, and when there is no
    approved copy to compare with."""
    if ctx.phase not in (c.BUILD, c.TEST, c.DEPLOY):
        return None
    approved = ctx.approved_artifact("plan.md")  # the caller returned already with no base
    if approved is None:
        return None
    now, before = dict.fromkeys(planned), dict.fromkeys(art.planned_files(approved))
    return {
        "added": [p for p in now if p not in before],
        "removed": [p for p in before if p not in now],
    }


# --- 7. no diff touching the guardrail files (OPERATING_MODEL section 3) ------------------------
def check_guardrails(ctx: GateContext) -> CheckResult:
    """No guardrail file and no accepted ``intent.md`` in the **committed** diff (as
    ``check_plan_sync`` and ``check_design_scope``; OPERATING_MODEL section 3: the gate
    judges HEAD). An uncommitted edit is ``check_clean_tree``'s. Read from the working tree,
    the ``.env`` that Claude Code's sandbox shows as modified is part of the "diff" however
    clean the branch is - the false positive that parked ``plan_sync`` in the eleventh live
    run (2026-09-22) - and a project that protects ``.env`` or lists it on its risk list
    would park here on it the same way."""
    if ctx.diff is None:
        return _fail("guardrails", ctx.diff_error, "Run the gate inside the project's git repo.")
    no_base = _no_base(ctx, "guardrails")
    if no_base:
        return no_base
    committed = diffmod.committed_files(ctx.root, ctx.diff.merge_base, ctx.diff.head)
    patterns = protected_paths.protected_patterns(ctx.config)
    touched = [f for f in committed if any(matches(p, f) for p in patterns)]
    intent_rel = f"{ctx.change_rel}/intent.md"
    # decision 30: on the fast lane the intent was accepted at the owner's unmerged intent PR
    # head, which the branch was cut from; "changed after gate (intent)" is read since that commit
    approved = ctx.approved_base()
    since_gate = (
        committed
        if approved == ctx.diff.merge_base
        else diffmod.committed_files(ctx.root, approved, ctx.diff.head)
    )
    if ctx.phase not in (c.INTENT, c.MAINTAIN) and intent_rel in since_gate:
        # the intent was accepted at gate (intent): a later phase may not rewrite it (it is what
        # the guardrail exemption and the risk acceptance are judged against). The maintain phase
        # writes the incident intent itself (p.44 step 5): its PR is the intent PR of that
        # change, and the owner's merge is its gate (intent) (decision 25)
        return _fail(
            "guardrails",
            "intent.md changed on this branch after gate (intent)",
            "Revert the intent.md change; an accepted intent changes only through a new "
            "intent PR (the intent phase).",
            touched=touched,
        )
    if not touched:
        return _ok("guardrails", "the diff does not touch a guardrail file")
    intent = ctx.approved_artifact("intent.md") or ""
    if ctx.status.id == c.INIT_CHANGE_ID or art.is_framework_change(intent):
        return _ok(
            "guardrails",
            "guardrail files changed by a declared framework change",
            touched=touched,
        )
    return _fail(
        "guardrails",
        f"the diff touches guardrail file(s): {', '.join(touched[:10])}",
        "Guardrail files (.claude/**, CLAUDE.md, REVIEW.md, sdlc.yaml, policies/**, "
        "protected_paths) are changed by the owner in a reviewed PR. Revert them here; a "
        "framework change says 'Framework change: yes' in the intent the owner merged at "
        "gate (intent).",
        touched=touched,
    )


# --- 8. risk list (step 5; OPERATING_MODEL section 9; decision 35) ----------------------------
def risk_hits(items: list[Any], paths: list[str], texts: dict[str, str]) -> dict[str, list[str]]:
    """{risk item: [where it matched]} (``risk.hits``): a plain item's words whole-token and
    plural-tolerant, so 'auth' matches 'auth/' and 'auth_token' but not 'author'; an item
    with ``paths`` by its globs, never under ``changes/``."""
    return risk_mod.hits(items, paths, texts)


RISK_PARK_NEED = (
    "The gate's reviewer says park on the risk-list item(s) named above. Under decision 35 a "
    "hit is only a line of the close-look banner, but the reviewer's park on a risk item is "
    "yours and never goes to the review panel (decisions 11 and 21 as 35 amends them). Read "
    "the brief ({brief}) and the verdict's reasons, then answer as for any park: a review "
    "comment or Request changes starts a fix round, and the reviewer judges the new HEAD."
)


def check_risk_list(ctx: GateContext) -> CheckResult:
    """Risk-list items in the **committed** diff's paths and in the committed spec's
    "Flagged concerns" (OPERATING_MODEL section 3: the gate judges HEAD; see
    ``check_guardrails`` for the sandbox-masked ``.env`` this keeps out).

    Decision 35 (1.0.15): a hit no longer parks. The check passes and reports every hit in
    ``details.hits`` (accepted or not; ``details.accepted`` names the accepted ones), which the
    close-look banner of the PR the owner merges reads (``risk.banner_lines``). It fails, and
    parks, only when the gate's reviewer says park on a hit item (``risk.parked_items``:
    the brief's verdict on it, or a ``park`` verdict that names the item); ``risk_list`` is on
    the panel's never list, so that park stays the owner's."""
    items, why = risk_mod.parse_items(ctx.config.get("risk_list"))
    if why:
        return _fail("risk_list", why, "Fix sdlc.yaml (decision 35: a string or {item, paths}).")
    no_base = _no_base(ctx, "risk_list")
    if no_base:
        return no_base
    accepted = risk_mod.accepted(ctx.status)
    head = ctx.diff.head if ctx.diff else None
    paths = (
        diffmod.committed_files(ctx.root, ctx.diff.merge_base, ctx.diff.head) if ctx.diff else []
    )
    # Only the "Flagged concerns" section of spec.md is read, never its prose: the design
    # prompt and security-baseline rule 8 make every spec name the risk-list items it checked
    # ("none of auth, data migrations, ... is touched"), and a whole-text scan fired on that
    # sentence in every live design run of 2026-09-21. A risk item the design touches is a
    # flagged concern (skill spec-template), so that section is where it is declared.
    # The spec is read at HEAD: ``check_clean_tree`` skips the change folder (the evidence is
    # committed after the gate) and does not run at intent or design, so the working-tree spec is
    # not guaranteed to be the committed one. The working tree is the fallback only when there
    # is no commit to read (not a repository, or an unborn branch).
    texts = {}
    spec = (
        diffmod.file_at(ctx.root, head, f"{ctx.change_rel}/spec.md")
        if head
        else ctx.artifact("spec.md")
    )
    if spec:
        concerns = art.split_sections(spec).get(art.CONCERNS_SECTION, "")
        if concerns.strip():
            texts[f"spec.md {art.CONCERNS_SECTION[3:]}"] = concerns
    hits = risk_hits(items, paths, texts)
    accepted_hit = sorted(k for k in hits if k.lower() in accepted)
    if not hits:
        return _ok("risk_list", "no risk-list item touched", hits={}, accepted=accepted_hit)
    parked = risk_mod.parked_items(sorted(hits), _phase_brief(ctx), _phase_verdict(ctx))
    shown = "; ".join(f"'{k}' in {', '.join(v[:3])}" for k, v in hits.items())
    if parked:
        return _fail(
            "risk_list",
            "the reviewer says park on risk-list item(s) "
            + ", ".join(f"'{i}'" for i in parked)
            + f" (hits: {shown})",
            RISK_PARK_NEED.format(brief=risk_mod.brief_rel(ctx.phase)),
            hits=hits,
            accepted=accepted_hit,
            parked_on=parked,
        )
    return _ok(
        "risk_list",
        f"risk-list hit, shown in the close-look banner (decision 35): {shown}",
        hits=hits,
        accepted=accepted_hit,
    )


def _phase_brief(ctx: GateContext) -> dict[str, dict[str, str]]:
    """The gate's reviewer's brief per hit item, read from the working tree as the verdict
    is (``load_verdict``): both are evidence the reviewer wrote for this round, committed
    after the gate, so HEAD still holds the previous round's brief."""
    return risk_mod.read_brief(ctx.change_dir, ctx.phase)


def _phase_verdict(ctx: GateContext) -> dict[str, Any] | None:
    data, _error = load_verdict(c.phase_file(ctx.evidence_dir, art.ADVERSARIAL_VERDICT, ctx.phase))
    return data


# --- 9. the adversarial reviewer's verdict (step 17; an input, never run by the gate) ---------
def load_verdict(path: Path) -> tuple[dict[str, Any] | None, str]:
    """Format written by the adversarial-reviewer agent:
    {"schema_version": 1, "phase": "build", "head": "<sha>", "verdict": "continue|park",
     "reasons": [...], "classification": "routine|non-routine",
     "classification_reasons": [...], "at": "<iso>"}

    A verdict an older plugin wrote says ``escalate``: it reads as ``park`` (R45 row 62, for
    one release; ``art.verdict_word``), and the data returned always holds the new word."""
    if not path.is_file():
        return None, "missing"
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        return None, f"unreadable: {exc}"
    return parse_verdict(text)


def parse_verdict(text: str | None) -> tuple[dict[str, Any] | None, str]:
    """``load_verdict``'s validation of the verdict file's text (the runner reads the file
    at a commit of the design branch too, decision 30): (data, "") or (None, why). Every
    reader of the verdict goes through here, so ``data["verdict"]`` is ``continue`` or
    ``park`` whatever word the file holds."""
    if text is None:
        return None, "missing"
    try:
        data = json.loads(text)
    except ValueError as exc:
        return None, f"unreadable: {exc}"
    word = art.verdict_word(data.get("verdict")) if isinstance(data, dict) else None
    if word is None:
        return None, "malformed: 'verdict' must be 'continue' or 'park'"
    data["verdict"] = word
    if data.get("classification") not in ("routine", "non-routine"):
        return None, "malformed: 'classification' must be 'routine' or 'non-routine'"
    if not isinstance(data.get("head"), str) or len(data["head"]) < 7:
        return None, "malformed: 'head' must be the commit sha the verdict judged"
    return data, ""


VERDICT_REQUIRED_AT = (c.DESIGN, c.BUILD, c.TEST)  # the reviewer runs before each of these


def check_adversarial_verdict(ctx: GateContext) -> CheckResult:
    path = c.phase_file(ctx.evidence_dir, art.ADVERSARIAL_VERDICT, ctx.phase)
    data, error = load_verdict(path)
    if data is None:
        if error == "missing" and ctx.phase not in VERDICT_REQUIRED_AT:
            return _ok(
                "adversarial_review", f"no adversarial verdict required at gate ({ctx.phase})"
            )
        return _fail(
            "adversarial_review",
            f"evidence/{path.name} {error}",
            "Run the adversarial-reviewer agent in a fresh context for this phase; it writes "
            "the verdict JSON.",
        )
    head = ctx.diff.head if ctx.diff else None
    if head and not str(head).startswith(str(data["head"])):
        return _fail(
            "adversarial_review",
            f"verdict is for commit {str(data['head'])[:10]}, HEAD is {head[:10]}",
            "Re-run the adversarial-reviewer on the current HEAD (a verdict never outlives "
            "the diff it judged).",
            stale=True,
        )
    reasons = [str(r) for r in (data.get("reasons") or [])]
    if data["verdict"] == art.VERDICT_PARK:
        from panel import ledger  # noqa: PLC0415

        key = ledger.park_key(reasons)
        settled = next((e for e in _panel_entries(ctx, "park") if e.get("key") == key), None)
        owner = next((e for e in _owner_continues(ctx) if e.get("key") == key), None)
        if settled is None and owner is not None:
            return _ok(
                "adversarial_review",
                "adversarial reviewer said park; the owner overturned the panel's "
                f"decision {owner.get('n')} on it, so the phase continues: "
                + str((owner.get("overturned") or {}).get("comment", "")),
                classification=data["classification"],
                reasons=reasons,
                settled_by_owner=owner.get("n"),
            )
        if settled is not None and ledger.decides_continue(settled):
            return _ok(
                "adversarial_review",
                "adversarial reviewer said park; the review panel decided to continue: "
                + str(settled.get("decision", "")),
                classification=data["classification"],
                reasons=reasons,
                settled_by_panel=settled.get("n"),
            )
        return _fail(
            "adversarial_review",
            "adversarial reviewer says park: " + ("; ".join(reasons) or "no reason given"),
            "Read the reviewer's reasons and decide: fix and re-run, or accept in review"
            + (
                " (the panel decided: " + str(settled.get("decision", "")) + ")"
                if settled is not None
                else ""
            )
            + ".",
            reasons=reasons,
            classification=data["classification"],
            verdict=art.VERDICT_PARK,
        )
    return _ok(
        "adversarial_review",
        "adversarial reviewer says continue",
        classification=data["classification"],
        reasons=reasons,
    )


REVIEWER_MODEL_NEED = (
    "The adversarial reviewer must run on the model sdlc.yaml's adversarial_model names (ROADMAP "
    "R7), and nothing shows that this verdict did. `panel/cli.py models` prints the alias the "
    "phase command passes, the pins that make it resolve to that model (the runner sets them; "
    "a run by hand exports them before the session starts) and any conflict in the "
    "configuration; fix that, then re-run the reviewer on the current HEAD."
)


def check_reviewer_model(ctx: GateContext) -> CheckResult:
    """ROADMAP R7: when ``sdlc.yaml: adversarial_model`` is set, the record the
    ``panel_blind`` hook wrote beside the phase's verdict names the adversarial reviewer as
    the writer, the verdict's ``head`` and a model that satisfies the pin. A hard park, never
    the panel's to settle (``ledger.NEVER_TO_PANEL``). Unset: nothing is checked."""
    from panel import ledger, models  # noqa: PLC0415

    wanted = models.reviewer_model(ctx.config)
    if not wanted:
        return _ok("reviewer_model", "sdlc.yaml names no adversarial_model: not checked")
    data, _error = load_verdict(c.phase_file(ctx.evidence_dir, art.ADVERSARIAL_VERDICT, ctx.phase))
    if data is None:
        # the adversarial_review check reports a missing or unreadable verdict
        return _ok("reviewer_model", "no readable verdict to check", wanted=wanted)
    path = ledger.reviewer_model_path(ctx.change_dir, ctx.phase)
    problems = ledger.reviewer_model_problems(
        art.read_text(path), wanted, ctx.phase, str(data["head"])
    )
    if problems:
        # a configuration no alias can satisfy is named, so the park says what to change
        problems += [
            f"the configuration: {why}"
            for why in models.conflicts(ctx.config, ctx.phase, dict(os.environ))
        ]
        return _fail("reviewer_model", "; ".join(problems), REVIEWER_MODEL_NEED, wanted=wanted)
    return _ok("reviewer_model", f"the adversarial reviewer ran on {wanted}", wanted=wanted)


# --- 10. committed work only: the verdict and the PR cover HEAD, not the working tree -----------
def _is_review_record(path: Path) -> bool:
    """A regular file (no symlink) whose text is a JSON object of objects: the shape
    ``review/findings.py update_seen`` writes. Anything else at that path is work."""
    if path.is_symlink() or not path.is_file():
        return False
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, ValueError):
        return False
    return isinstance(data, dict) and all(isinstance(v, dict) for v in data.values())


def check_clean_tree(ctx: GateContext) -> CheckResult:
    if ctx.diff is None:
        return _fail("clean_tree", ctx.diff_error, "Run the gate inside the project's git repo.")
    prefix = ctx.change_rel + "/"
    tree = diffmod.dirty_files(ctx.root)
    # four kinds of entry are nobody's work: the sandbox's empty placeholders, the root
    # names it masks (.env, .idea, .vscode and friends — diffmod.SANDBOX_MASKED), the review
    # pass's own record at test and deploy (changes/.review-seen.json, written by ``review/cli.py
    # validate`` right before this gate reads the findings file in the change's evidence/,
    # and committed with the evidence after it by ``commit-phase``, 0.3.5: change 0001's fix
    # rounds at gate (deploy) parked on it — a regular file holding a JSON object, so a deleted,
    # replaced or malformed record is still reported) and, inside a CI session only, what the
    # sandbox has mounted over at any depth (diffmod.sandbox_mounted, 0.3.4; the mark the
    # runner sets says the gate runs inside the sandbox, and by hand a mount over a tracked
    # path is nobody's mask)
    ignored = set(diffmod.sandbox_placeholders(ctx.root, tree)) | set(diffmod.sandbox_masked(tree))
    seen = c.review_seen_rel()
    if ctx.phase in (c.TEST, c.DEPLOY) and seen in tree and _is_review_record(ctx.root / seen):
        ignored.add(seen)
    dirty = [f for f in tree if f not in ignored and not f.startswith(prefix)]
    if dirty and ctx.commands_deferred:
        mounted = set(diffmod.sandbox_mounted(ctx.root, dirty))
        ignored |= mounted
        dirty = [f for f in dirty if f not in mounted]
    ignored = sorted(ignored)
    if dirty:
        return _fail(
            "clean_tree",
            f"{len(dirty)} uncommitted file(s) outside the change folder: " + ", ".join(dirty[:10]),
            "Commit (or discard) the work first: the adversarial verdict and the PR judge "
            "HEAD, not the working tree.",
            dirty=dirty[:50],
            ignored=ignored[:50],
        )
    return _ok(
        "clean_tree", "no uncommitted change outside the change folder", ignored=ignored[:50]
    )


# --- 10b. no link under the change folder (R59, the plugin security review of 2026-10-19, I2) --
EVIDENCE_LINKS_NEED = (
    "Replace each link with the file's own content, or remove it: the runner reads the change "
    "folder outside the sandbox to build the PR body, and a link there could quote any file "
    "it can read (.env included)."
)


def change_folder_links(root: Path, change_rel: str, head: str | None) -> list[str]:
    """Every symbolic link under ``change_rel``: in the working tree (tracked or not, the
    folder itself and its parents up to ``changes/`` included) and, at ``head``, every entry
    committed with the link mode ``120000``."""
    folder = Path(root) / change_rel
    found: set[str] = set()
    linked = art.linked_part(folder)
    if linked is not None:
        found.add(Path(os.path.relpath(linked, root)).as_posix())
    elif folder.is_dir():
        for top, dirs, files in os.walk(folder):
            for name in dirs + files:
                entry = Path(top) / name
                if entry.is_symlink():
                    found.add(entry.relative_to(root).as_posix())
    if head:
        out = diffmod._git(root, "ls-tree", "-r", "-z", head, "--", change_rel + "/", check=False)
        for record in out.split("\0"):
            meta, _, path = record.partition("\t")
            if path and meta.split(" ")[0] == "120000":
                found.add(path.replace("\\", "/"))
    return sorted(found)


def check_evidence_links(ctx: GateContext) -> CheckResult:
    if ctx.diff is None:
        return _fail(
            "evidence_links", ctx.diff_error, "Run the gate inside the project's git repo."
        )
    links = change_folder_links(ctx.root, ctx.change_rel, ctx.diff.head)
    if links:
        return _fail(
            "evidence_links",
            f"{len(links)} symbolic link(s) under the change folder: " + ", ".join(links[:10]),
            EVIDENCE_LINKS_NEED,
            links=links[:50],
        )
    return _ok("evidence_links", "no symbolic link under the change folder")


# --- 11. the design phase touches no source (decision 2; OPERATING_MODEL section 8) ---------------
def check_design_scope(ctx: GateContext) -> CheckResult:
    """The spec-and-plan run of the design phase is read-only on source: the only files it writes
    are the change folder's own artifacts. The first run with edit tools on source is the build
    phase.

    The verdict is the **committed** diff only: the files between the merge base and HEAD,
    which is what the PR carries and what would merge. The working tree is reported under
    ``details.dirty`` and never parks the run — the gate may be executed inside Claude Code's
    sandbox, whose masked paths (``diff.SANDBOX_MASKED``) show up as modified or untracked
    however clean the checkout is, and that parked the third live design run (2026-09-21).
    """
    if ctx.diff is None:
        return _fail("design_scope", ctx.diff_error, "Run the gate inside the project's git repo.")
    if ctx.phase == c.INTENT and ctx.change_dir.name.startswith(c.INIT_CHANGE_ID + "-"):
        # the installation PR of /sdlc-init (change 0000) is the one intent PR that carries
        # files outside its folder: the guardrails, the workflows and the pin script it writes
        # (OPERATING_MODEL section 8, layer i). Keyed on the folder name and gate (intent) only:
        # ``status.id`` is the session's to write (the review of the 0.2.26 diff, L2)
        return _ok("design_scope", "change 0000 installs the framework: not judged")
    no_base = _no_base(ctx, "design_scope")
    if no_base:
        return no_base
    prefix = ctx.change_rel + "/"
    committed = diffmod.committed_files(ctx.root, ctx.diff.merge_base, ctx.diff.head)
    outside = [f for f in committed if not f.startswith(prefix)]
    dirty = diffmod.without_placeholders(ctx.root, diffmod.dirty_files(ctx.root))
    if outside:
        if ctx.phase == c.INTENT:
            why = (
                " (the intent PR carries the intent alone; a fix round at gate (intent) applies "
                "the owner's review comments to intent.md and nothing else, decision 22)."
            )
        elif ctx.phase == c.MAINTAIN:
            why = (
                " (the diagnosis of the maintain phase is read-only, p.43 step 3; a runbook works "
                "on a branch of its own)."
            )
        else:
            why = "."
        return _fail(
            "design_scope",
            f"{len(outside)} committed file(s) outside {prefix}: " + ", ".join(outside[:10]),
            f"Revert them on the branch: the {ctx.phase} phase commits only {prefix}; the "
            "first run with edit tools on source is the build phase" + why,
            outside=outside[:50],
            dirty=dirty[:50],
        )
    return _ok("design_scope", f"the committed diff stays inside {prefix}", dirty=dirty[:50])


# --- 12. owner-only state: accept-risk and set-iterations (build guide step 24.5) -------------
OWNER_ACTIONS_NEED = (
    "accept-risk, set-iterations and unlock-tests are the owner's: apply "
    "sdlc:reset-iterations or sdlc:unlock-tests on the pull request, or run the command on "
    "your machine or in your own session and commit (a risk item is accepted by your merge "
    "since decision 35, or by accept-risk run by hand); a run cannot approve itself "
    "(decision 5)."
)
STATUS_HISTORY_LIMIT = "200"  # commits of status.yaml history the check walks back through


_STATUS_CACHE: dict[tuple[str, str, str], dict[str, Any] | None] = {}
_SHA_RE = re.compile(r"^[0-9a-f]{40}\^?$")


def _status_fields(ctx: GateContext, ref: str) -> dict[str, Any] | None:
    """``risk_accepted`` and ``iterations`` of the change's status.yaml at ``ref``. A commit's
    copy never changes, so a full sha (or its parent) is cached for the process: the history
    walks of ``owner_actions`` and ``test_lock`` read the same commits (the review of the
    0.2.26 diff, L9)."""
    key = (str(ctx.root), ctx.change_rel, ref)
    cacheable = bool(_SHA_RE.match(ref))
    if cacheable and key in _STATUS_CACHE:
        return _STATUS_CACHE[key]
    fields = _status_fields_uncached(ctx, ref)
    if cacheable:
        if len(_STATUS_CACHE) > 4000:
            _STATUS_CACHE.clear()
        _STATUS_CACHE[key] = fields
    return fields


def _status_fields_uncached(ctx: GateContext, ref: str) -> dict[str, Any] | None:
    text = diffmod.file_at(ctx.root, ref, f"{ctx.change_rel}/{STATUS_FILE}")
    if text is None:
        return None
    try:
        data = yamlish.loads(text)
    except Exception:  # noqa: BLE001 — an unreadable old copy is treated as absent
        return None
    if not isinstance(data, dict):
        return None
    risk = {str(r).strip().lower() for r in (data.get("risk_accepted") or []) if str(r).strip()}
    iterations = data.get("iterations")
    if isinstance(iterations, bool) or not isinstance(iterations, int):
        iterations = 0
    panel_calls = data.get("panel_calls")
    if isinstance(panel_calls, bool) or not isinstance(panel_calls, int):
        panel_calls = 0
    # decision 24: the actor of the owner label that made the change, when a label did
    by = data.get("risk_accepted_by")
    risk_by = {
        str(e.get("item", "")).strip().lower(): str(e.get("actor", "")).strip()
        for e in (by if isinstance(by, list) else [])
        if isinstance(e, dict) and str(e.get("item", "")).strip()
    }
    reset_by = data.get("iterations_reset_by")
    reset_at = data.get("iterations_reset_at")
    # the test-file lock as the hook reads it (``hooks/test_file_lock.py: is_locked``): a
    # fix-type change whose reproducing test is committed; either field lifts it
    locked = str(data.get("change_type", "")).strip().lower() == "fix" and (
        data.get("tests_locked") is True
    )
    unlocked_by = data.get("tests_unlocked_by")
    return {
        "risk": risk,
        "iterations": iterations,
        "panel_calls": panel_calls,
        "risk_by": risk_by,
        "reset_by": str(reset_by).strip() if isinstance(reset_by, str) else None,
        "reset_at": str(reset_at).strip() if isinstance(reset_at, str) else None,
        "locked": locked,
        "unlocked_by": str(unlocked_by).strip() if isinstance(unlocked_by, str) else None,
    }


def _label_actor_ok(actor: str | None, identities: list[str]) -> bool:
    """A recorded label actor that is a person: not empty, not the automation identity, not
    a ``[bot]`` account (``state/unpark.py`` applies the same rule before recording)."""
    from state.unpark import is_automation_actor, is_runner_reset  # noqa: PLC0415

    # decision 29: the runner's marked reset is not a person's act; it counts only through
    # ``runner_reset_recorded`` (``check_owner_actions``), never as a label actor
    return (
        bool(actor)
        and not is_runner_reset(actor)
        and not is_automation_actor(str(actor), identities)
    )


def _status_history(ctx: GateContext) -> list[tuple[str, str, str]]:
    """(sha, author email, author name) for the commits that touched status.yaml, newest
    first — the author is who introduced the change of state, which is the point here."""
    out = diffmod._git(
        ctx.root,
        "log",
        "-n",
        STATUS_HISTORY_LIMIT,
        "--format=%H%x1f%ae%x1f%an",
        "--",
        f"{ctx.change_rel}/{STATUS_FILE}",
        check=False,
    )
    rows = []
    for line in out.splitlines():
        parts = line.strip().split("\x1f")
        if len(parts) == 3 and parts[0]:
            rows.append((parts[0], parts[1], parts[2]))
    return rows


def check_owner_actions(ctx: GateContext) -> CheckResult:
    """A risk acceptance or an iteration reset counts only when the owner made it.

    ``status.yaml: risk_accepted`` and ``iterations`` were owner actions by convention only
    (PROGRESS known gap); this ties them to the commit author. Every commit that gained a
    risk item (since 0.2.26; before, the newest only, so an earlier self-acceptance hid
    behind the owner's later one) and the newest that lowered the iteration or the panel-call
    count (the panel count since 0.2.26: one label resets both, decision 21) must not be the
    automation identity, and an acceptance that sits uncommitted in the working tree belongs
    to nobody: the owner commits theirs.

    Decision 24: the owner's label on the PR is the other form of the act. A CI run performs
    it and commits ``status.yaml`` under the automation identity, so a commit by that
    identity passes when the same commit recorded the label's actor
    (``risk_accepted_by[item]``, ``iterations_reset_by``) and that actor is a person. An
    actor that is the automation identity or a ``[bot]`` account is rejected as before: a
    run cannot un-park itself (decision 11).

    The test-file lock is the third owner action (OPERATING_MODEL sections 6 and 8: "only
    the owner unlocks"). Until 0.2.25 nothing but the hook read ``tests_locked``, so a run
    that set it to false, or turned the change into a feature, or ran ``unlock-tests``
    itself, edited the frozen tests unnoticed (1.0.0 readiness review, 2026-09-26). The
    newest commit that lifted the lock is judged like a reset: a person's commit, or the
    automation identity's with ``tests_unlocked_by`` recorded as a person in that commit."""
    if ctx.diff is None:
        return _fail("owner_actions", ctx.diff_error, "Run the gate inside the project's git repo.")
    identities = automation_identity(ctx.config)
    empty = {
        "risk": set(),
        "iterations": 0,
        "panel_calls": 0,
        "risk_by": {},
        "reset_by": None,
        "reset_at": None,
        "locked": False,
        "unlocked_by": None,
    }
    head = _status_fields(ctx, "HEAD") or empty
    tree_risk = {str(r).strip().lower() for r in ctx.status.risk_accepted if str(r).strip()}
    tree_locked = ctx.status.change_type == "fix" and bool(ctx.status.tests_locked)
    problems: list[str] = []
    gained = sorted(tree_risk - head["risk"])
    if gained:
        problems.append(
            f"risk_accepted gained {', '.join(gained)} in the working tree, in no commit"
        )
    # decision 21: one label resets the fix-iteration and the panel-call counts, so a drop of
    # either is the same owner act (the panel count was not judged before 0.2.26)
    tree_counts = {"iterations": ctx.status.iterations, "panel_calls": ctx.status.panel_calls}
    for counter, tree_value in tree_counts.items():
        if tree_value < head[counter]:
            problems.append(
                f"{counter} dropped from {head[counter]} to {tree_value} in the working tree, "
                "in no commit"
            )
    if head["locked"] and not tree_locked:
        problems.append("the test-file lock was lifted in the working tree, in no commit")
    # every commit that gained a risk item, lowered a counter or lifted the lock is judged,
    # not the newest only: an earlier self-acceptance was laundered by the owner's later
    # acceptance of another item (1.0.0 readiness review, group A; the review of the 0.2.26
    # diff, L6, for the drops and the lifts). An unlabelled gain is ratified when a later
    # commit recorded a person's actor for the item (the owner's sdlc:accept-risk after the
    # park, before decision 35 retired the label; L5: without it the park could never be
    # cleared).
    risk_events: list[tuple[str, str, str, list[str], dict[str, str], int]] = []
    drop_events: list[tuple[str, str, str, str, int, int, str | None, str | None]] = []
    unlock_events: list[tuple[str, str, str, str | None]] = []
    ratified: dict[str, tuple[int, str]] = {}  # item -> (walk index, the actor recorded)
    for index, (sha, email, name) in enumerate(_status_history(ctx)):
        now = _status_fields(ctx, sha)
        if now is None:
            continue
        before = _status_fields(ctx, f"{sha}^") or empty
        for item, actor in now["risk_by"].items():
            if actor != before["risk_by"].get(item) and item not in ratified:
                ratified[item] = (index, actor)
        if before["locked"] and not now["locked"]:
            # the act is recorded in this very commit when the actor changed
            recorded = now["unlocked_by"] if now["unlocked_by"] != before["unlocked_by"] else None
            unlock_events.append((sha, email, name, recorded))
        added = sorted(now["risk"] - before["risk"])
        if added:
            # the label actors this very commit recorded for the items it added
            by = {
                i: a
                for i, a in now["risk_by"].items()
                if i in added and a != before["risk_by"].get(i)
            }
            risk_events.append((sha, email, name, added, by, index))
        for counter in tree_counts:
            if now[counter] < before[counter]:
                # the act is recorded in this very commit when the actor or the stamp changed:
                # a second reset by the same person changes the stamp only (0.2.17)
                recorded = now["reset_by"] != before["reset_by"] or (
                    now["reset_at"] is not None and now["reset_at"] != before["reset_at"]
                )
                reset_by = now["reset_by"] if recorded else None
                reset_at = now["reset_at"] if recorded else None
                drop_events.append(
                    (counter, sha, email, name, before[counter], now[counter], reset_by, reset_at)
                )
    from state.unpark import runner_reset_recorded  # noqa: PLC0415

    labels: dict[str, Any] = {}
    runner_resets: dict[str, Any] = {}
    for sha, email, name, added, by, index in risk_events:
        if not is_automation(name, email, identities):
            continue
        unlabelled = [
            i
            for i in added
            if not _label_actor_ok(by.get(i), identities)
            and not (
                i in ratified
                and ratified[i][0] < index
                and _label_actor_ok(ratified[i][1], identities)
            )
        ]
        if unlabelled:
            problems.append(
                f"risk_accepted gained {', '.join(unlabelled)} in commit {sha[:10]}, "
                f"authored by the automation identity ({name} <{email}>)"
                + (
                    f"; the recorded label actor {by[unlabelled[0]]!r} is not a person"
                    if by.get(unlabelled[0])
                    else " and no owner label actor is recorded for it"
                )
            )
        else:
            labels.setdefault("risk_accepted", {}).update(
                {i: by.get(i) or ratified[i][1] for i in added}
            )
    for counter, sha, email, name, was, now_count, reset_by, reset_at in drop_events:
        if not is_automation(name, email, identities):
            continue
        if _label_actor_ok(reset_by, identities):
            labels.setdefault(f"{counter}_reset", reset_by)
        elif runner_reset_recorded(ctx.change_dir, reset_by, reset_at):
            # decision 29: the runner's one judged reset at the cap, marked as the label's is
            # and recorded in evidence/auto-reset.json; on the fix-round line, not a person's
            runner_resets.setdefault(f"{counter}_reset", reset_by)
        else:
            problems.append(
                f"{counter} dropped from {was} to {now_count} in commit {sha[:10]}, "
                f"authored by the automation identity ({name} <{email}>)"
                + (
                    f"; the recorded label actor {reset_by!r} is not a person"
                    if reset_by
                    else " and no owner label actor is recorded for it"
                )
            )
    for sha, email, name, unlocked_by in unlock_events:
        if not is_automation(name, email, identities):
            continue
        if _label_actor_ok(unlocked_by, identities):
            labels.setdefault("tests_unlocked", unlocked_by)
        else:
            problems.append(
                f"the test-file lock was lifted in commit {sha[:10]}, authored by the "
                f"automation identity ({name} <{email}>)"
                + (
                    f"; the recorded label actor {unlocked_by!r} is not a person"
                    if unlocked_by
                    else " and no owner label actor is recorded for it"
                )
            )
    if problems:
        return _fail(
            "owner_actions",
            "; ".join(problems),
            OWNER_ACTIONS_NEED,
            problems=problems,
            automation_identity=identities,
        )
    return _ok(
        "owner_actions",
        "risk acceptances, iteration and panel-call resets and test-lock lifts, if any, were "
        "committed by the owner or applied by the owner's label",
        risk_accepted=sorted(tree_risk),
        label_actors=labels,
        **({"runner_resets": runner_resets} if runner_resets else {}),
    )


# --- 12a. the test-file lock holds from its commit to HEAD (plugin 0.2.25) ------------------
TEST_LOCK_NEED = (
    "a fix-type change edits no test under sdlc.yaml: test_paths once its reproducing test is "
    "committed (OPERATING_MODEL section 8): revert the test edits, or the owner unlocks "
    "(sdlc:unlock-tests on the pull request, or unlock-tests on their machine and a commit) "
    "when the test itself was wrong."
)


def _lock_commit(ctx: GateContext) -> str | None:
    """The newest commit that set the lock: ``status.yaml`` gained ``tests_locked: true`` on a
    fix-type change (or the oldest commit in the walked history, when it was locked already)."""
    oldest_locked = None
    for sha, _email, _name in _status_history(ctx):
        now = _status_fields(ctx, sha)
        if now is None or not now["locked"]:
            continue
        before = _status_fields(ctx, f"{sha}^")
        if before is None or not before["locked"]:
            return sha
        oldest_locked = sha
    return oldest_locked


def check_test_lock(ctx: GateContext) -> CheckResult:
    """No test file changed between the lock commit and HEAD while the lock stands.

    The hook (``hooks/test_file_lock.py``) denies the edit tools and reads the working tree,
    so a run that sets ``tests_locked: false`` in the file, edits a test and sets it back, or
    edits through a shell command, leaves HEAD locked and the test changed, and
    ``owner_actions`` sees no lift (the 0.2.25 review of the readiness fixes, finding M1).
    The committed diff from the lock commit to HEAD under ``test_paths`` is the record the
    hook cannot fake; when HEAD is unlocked, ``owner_actions`` judges who lifted it."""
    from hooks._common import ConfigError  # noqa: PLC0415
    from hooks.test_file_lock import test_path_patterns  # noqa: PLC0415

    if ctx.diff is None:
        return _fail("test_lock", ctx.diff_error, "Run the gate inside the project's git repo.")
    if ctx.status.change_type != "fix":
        return _ok("test_lock", "not a fix-type change: no test-file lock")
    head = _status_fields(ctx, "HEAD")
    if not head or not head["locked"]:
        return _ok("test_lock", "the lock is not set at HEAD (owner_actions judges a lift)")
    sha = _lock_commit(ctx)
    if sha is None:
        return _ok("test_lock", "no commit in the walked history set the lock")
    try:
        patterns = test_path_patterns(ctx.config)
    except ConfigError as exc:
        return _fail("test_lock", str(exc), "Fix sdlc.yaml: test_paths (a list of globs).")
    # every status, a rename's source and a type change counted (R59, I3): a locked test
    # renamed away or turned into a symlink is a changed test file
    changed = diffmod.changed_paths(ctx.root, f"{sha}..HEAD")
    hits = sorted(f for f in changed if any(matches(p, f) for p in patterns))
    if hits:
        return _fail(
            "test_lock",
            f"{len(hits)} test file(s) changed after the lock commit {sha[:10]}: "
            + ", ".join(hits[:10]),
            TEST_LOCK_NEED,
            files=hits[:50],
            lock_commit=sha,
        )
    return _ok(
        "test_lock", f"no test file changed since the lock commit {sha[:10]}", lock_commit=sha
    )


# --- 12b. dropped test files and eval cases are a gate finding (intent.md change 1) -----------
EVAL_CASES_PREFIX = "evals/cases/"
RATCHET_KEYS = {"tests": "ratchet: tests", "evals": "ratchet: evals"}
RATCHET_PROOF_RE = re.compile(r"(?im)^[ \t]*[-*][ \t]*ratchet:[ \t]*(tests|evals)\b")

# intent.md's own fixed token list (open question 2): never anchored beyond the plain
# substring itself, so a test that only mentions a token in a string is listed, never parked
# on (the measured ratchets, ROADMAP R15, is what would tell the two apart).
SKIP_MARKER_TOKENS = (
    "@pytest.mark.skip",
    "@pytest.mark.xfail",
    "pytest.skip(",
    "--deselect",
    "--ignore",
    "-k",
    "testpaths",
    "norecursedirs",
    "collect_ignore",
    "it.skip(",
    "describe.skip(",
    "xit(",
    ".only(",
    "test.todo(",
    "#[ignore]",
)
# The test runner's own configuration files (Requirements), read the same way ``matches``
# reads every other glob in this module - no new ``sdlc.yaml`` key.
SKIP_MARKER_CONFIG_GLOBS = (
    "**/pytest.ini",
    "**/pyproject.toml",
    "**/setup.cfg",
    "**/tox.ini",
    "**/conftest.py",
    "**/package.json",
    "**/jest.config.*",
)


def dropped_test_files(records: list[diffmod.NameStatusRecord], patterns: list[str]) -> list[str]:
    """A ``D`` under a ``test_paths`` glob, or an ``R``/``C`` whose source matches a glob and
    destination matches none (a rename within the globs is not a drop; panel decision #3,
    phase b). Pure: takes the parsed ``--name-status`` records, no live git."""
    dropped: set[str] = set()
    for rec in records:
        if rec.status == "D":
            if any(matches(p, rec.path) for p in patterns):
                dropped.add(rec.path)
        elif rec.status in ("R", "C") and rec.new_path is not None:
            if any(matches(p, rec.path) for p in patterns) and not any(
                matches(p, rec.new_path) for p in patterns
            ):
                dropped.add(rec.path)
    return sorted(dropped)


def dropped_eval_cases(
    records: list[diffmod.NameStatusRecord],
    survivors: list[str],
    prefix: str = EVAL_CASES_PREFIX,
) -> list[str]:
    """Case folders under ``prefix`` with no survivor left in ``survivors`` (``tree_files`` at
    ``ctx.diff.head``), plus every case renamed to a dot-prefixed destination folder (``discover``
    excludes a hidden folder with no deletion in the diff). A case is decided from what the
    committed tree still holds, not from the diff's records alone, so a partial multi-file
    deletion with a surviving sibling is never mistaken for the whole case's drop (panel
    decision #2, phase b) — but the dot-prefixed-rename rule is evaluated independently of
    that survivor check, deliberately: a surviving sibling never excuses a dot-prefixed
    rename, since the rename is itself how a case would be hidden from discovery (panel
    decision #1, phase c fix round). Pure but for its two list arguments."""

    def case_of(path: str) -> str | None:
        if not path.startswith(prefix):
            return None
        rest = path[len(prefix) :]
        return rest.split("/", 1)[0] if "/" in rest else None

    touched: set[str] = set()
    dot_dropped: set[str] = set()
    for rec in records:
        src_case = case_of(rec.path)
        if src_case:
            touched.add(src_case)
        if rec.status in ("R", "C") and rec.new_path is not None:
            dst_case = case_of(rec.new_path)
            if dst_case:
                if dst_case.startswith(".") and src_case and src_case != dst_case:
                    dot_dropped.add(src_case)
                else:
                    touched.add(dst_case)

    survivor_cases = {name for path in survivors if (name := case_of(path))}
    dropped = set(dot_dropped) | {
        case for case in touched if case not in dot_dropped and case not in survivor_cases
    }
    return sorted(f"{prefix}{case}/" for case in dropped)


_HUNK_RE = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@")


def _added_lines(diff_text: str) -> list[tuple[str, int, str]]:
    """``[(file, line, content)]`` for every added line of a ``--unified=0`` diff (never the
    whole file): the new-file path from each ``+++ b/<path>`` header and the new line number
    from each ``@@ ... +<n> ...@@`` hunk header, advanced one per added line."""
    out: list[tuple[str, int, str]] = []
    current_file = ""
    next_line = 0
    for raw in diff_text.splitlines():
        if raw.startswith("+++ "):
            current_file = raw[len("+++ b/") :] if raw.startswith("+++ b/") else ""
            continue
        if raw.startswith("@@"):
            m = _HUNK_RE.match(raw)
            next_line = int(m.group(1)) if m else 0
            continue
        if raw.startswith("+"):  # not "+++", already consumed above
            if current_file:
                out.append((current_file, next_line, raw[1:]))
            next_line += 1
    return out


def skip_marker_hits(ctx: GateContext, test_patterns: list[str]) -> list[dict[str, Any]]:
    """``[{file, line, token}]`` for every ``SKIP_MARKER_TOKENS`` occurrence on an added line
    of a file under ``test_paths`` or a test-runner configuration file (``SKIP_MARKER_CONFIG_
    GLOBS``). Never affects ``ok`` - listed only (open question 2)."""
    if ctx.diff is None or not ctx.diff.merge_base:
        return []
    committed = diffmod.committed_files(ctx.root, ctx.diff.merge_base, ctx.diff.head)
    scanned = sorted(
        f
        for f in committed
        if any(matches(p, f) for p in test_patterns)
        or any(matches(g, f) for g in SKIP_MARKER_CONFIG_GLOBS)
    )
    if not scanned:
        return []
    ref = f"{ctx.diff.merge_base}...{ctx.diff.head or 'HEAD'}"
    text = diffmod._git(ctx.root, "diff", "-M", "--unified=0", ref, "--", *scanned, check=False)
    hits = []
    for file, line, content in _added_lines(text):
        for token in SKIP_MARKER_TOKENS:
            if token in content:
                hits.append({"file": file, "line": line, "token": token})
    return hits


def _declared_ratchets(plan_text: str) -> set[str]:
    """The ratchet names a '## Proof' item declares wholesale (``- ratchet: tests may fall,
    because <why>``); a name other than ``tests``/``evals`` is inert (open question 4)."""
    proof = art.split_sections(plan_text).get("## Proof", "")
    return {m.group(1).lower() for m in RATCHET_PROOF_RE.finditer(proof)}


RATCHET_PARK_NEED = RISK_PARK_NEED


def check_ratchets(ctx: GateContext) -> CheckResult:
    """A dropped test file or eval case, undeclared by the approved plan, is a risk-list hit
    named after its ratchet (``ratchet: tests``, ``ratchet: evals``; R15). The approved plan
    is read at the merge base (``ctx.approved_artifact``; on the fast lane, decision 30, at the
    design commit gate (design) passed on), never the working tree, so a
    commit cannot excuse its own drop by editing plan.md alongside it (the riskiest step,
    spec.md Design/Risks). Added skip markers are listed in ``details.skip_markers``, never
    affecting ``ok``.

    Decision 35 (1.0.15), point 6: the hit no longer parks. It is reported in
    ``details.hits`` (accepted or not) for the close-look banner, which the owner's merge
    accepts as every hit; a drop the plan declares is listed in ``details.declared`` and is a
    banner line too. The check fails only when the gate's reviewer says park on a ratchet
    item (``risk.parked_items``), which parks like any park on a risk item. Not
    caught here: a test emptied of its own tests, a dropped test inside a file that still
    exists, an edited test-runner configuration line (the measured ratchets, R15's second
    change)."""
    from hooks._common import ConfigError  # noqa: PLC0415
    from hooks.test_file_lock import test_path_patterns  # noqa: PLC0415

    if ctx.diff is None:
        return _fail("ratchets", ctx.diff_error, "Run the gate inside the project's git repo.")
    no_base = _no_base(ctx, "ratchets")
    if no_base:
        return no_base
    try:
        patterns = test_path_patterns(ctx.config)
    except ConfigError as exc:
        return _fail("ratchets", str(exc), "Fix sdlc.yaml: test_paths (a list of globs).")

    records = diffmod.name_status(ctx.root, ctx.diff.merge_base, ctx.diff.head)
    dropped_tests = dropped_test_files(records, patterns)
    survivors = diffmod.tree_files(ctx.root, ctx.diff.head, EVAL_CASES_PREFIX)
    dropped_cases = dropped_eval_cases(records, survivors, EVAL_CASES_PREFIX)

    plan = ctx.approved_artifact("plan.md") or ""
    planned = art.planned_files(plan)
    declared_ratchets = _declared_ratchets(plan)
    accepted = risk_mod.accepted(ctx.status)

    hits: dict[str, list[str]] = {}
    declared: list[str] = []
    for name, dropped in (("tests", dropped_tests), ("evals", dropped_cases)):
        key = RATCHET_KEYS[name]
        for path in dropped:
            # a case path is a directory ("evals/cases/bar/"), never a file itself: is_planned's
            # directory-prefix branch only matches something strictly under the prefix, so a
            # synthetic file name under it lets a plan.md entry that lists the folder with its
            # trailing slash (check_plan_sync's own convention) match the folder's own drop.
            probe = f"{path}." if path.endswith("/") else path
            if name in declared_ratchets or any(plan_sync.is_planned(probe, p) for p in planned):
                declared.append(f"{path} (plan)")
            else:
                hits.setdefault(key, []).append(path)

    skip_markers = skip_marker_hits(ctx, patterns)
    accepted_hit = sorted(k for k in hits if k.lower() in accepted)
    details = {
        "hits": hits,
        "declared": declared,
        "skip_markers": skip_markers,
        "accepted": accepted_hit,
    }
    if not hits:
        return _ok("ratchets", "no undeclared test file or eval case drop", **details)
    shown = "; ".join(f"'{k}': {', '.join(v[:5])}" for k, v in hits.items())
    parked = risk_mod.parked_items(sorted(hits), _phase_brief(ctx), _phase_verdict(ctx))
    if parked:
        return _fail(
            "ratchets",
            "the reviewer says park on ratchet item(s) "
            + ", ".join(f"'{i}'" for i in parked)
            + f" (dropped-ratchet hit: {shown})",
            RATCHET_PARK_NEED.format(brief=risk_mod.brief_rel(ctx.phase)),
            parked_on=parked,
            **details,
        )
    return _ok(
        "ratchets",
        f"dropped-ratchet hit, shown in the close-look banner (decision 35): {shown}",
        **details,
    )


# --- 13. the decisions ledger of deferred review (decision 21; build guide step 16a) ----------
def _blind_verdicts_problems(ctx: GateContext, entry: dict) -> list[str]:
    """A ledger line written since 0.2.30 names its item (``item_n``); both blind verdicts
    of that item must be committed (HEAD, the gate's rule), each with a ``## Verdict``
    clause. A line without ``item_n`` predates the rule and is not re-judged. The advocate's
    model is the phase's (``panel/models.py advocate_model``, R7)."""
    from panel import ledger, models  # noqa: PLC0415

    item_n = entry.get("item_n")
    if isinstance(item_n, bool) or not isinstance(item_n, int):
        return []
    phase = str(c.phase_name(entry.get("phase") or ctx.phase))
    texts: dict[str, str | None] = {}
    for member in ledger.BLIND_MEMBERS:
        path = ledger.member_path(ctx.change_dir, phase, item_n, member)
        if ctx.diff is not None:
            rel = str(path.relative_to(ctx.root)).replace("\\", "/")
            texts[member] = diffmod.file_at(ctx.root, "HEAD", rel)
        else:
            texts[member] = art.read_text(path)
    _verdicts, missing = ledger.member_verdicts(texts, phase, item_n)
    model_path = ledger.advocate_model_path(ctx.change_dir, phase, item_n)
    if ctx.diff is not None:
        rel = str(model_path.relative_to(ctx.root)).replace("\\", "/")
        model_text = diffmod.file_at(ctx.root, "HEAD", rel)
    else:
        model_text = art.read_text(model_path)
    missing += ledger.advocate_model_problems(
        model_text,
        models.advocate_model(ctx.config, phase, os.environ.get("SDLC_MODEL")),
        phase,
        item_n,
    )
    return [f"decision {entry.get('n')}: {problem}" for problem in missing]


def check_panel(ctx: GateContext) -> CheckResult:
    """Every panel decision has a ledger line, no panel decision touched a never-to-panel
    item, and no standing ``park`` decision upholds the adversarial reviewer's verdict:
    one that does not start with ``continue`` (``park``, empty, anything else) fails the
    check, so the gate parks (NOTES 45 gap 1, choice 205; an overturned line is the owner's
    act and is left alone). Passes trivially when there is no ledger and no concern closed
    by the panel."""
    from panel import ledger  # noqa: PLC0415

    error = ledger.ledger_error(ctx.change_dir, ctx.phase)
    if error:
        return _fail("panel", error, "Restore or remove the ledger; the gate cannot read it.")
    entries = ledger.load_ledger(ctx.change_dir, ctx.phase)
    spec = ctx.artifact("spec.md") or ""
    closed_by_panel = ledger.panel_closed_concerns(spec)
    if not entries and not closed_by_panel:
        return _ok("panel", "no panel decision at this gate")
    problems: list[str] = []
    for entry in entries:
        problems += ledger.validate_entry(entry)
        if entry.get("kind") in ledger.NEVER_TO_PANEL:
            problems.append(
                f"decision {entry.get('n')}: {entry.get('kind')} never goes to the panel"
            )
        problems += _blind_verdicts_problems(ctx, entry)
    standing = ledger.active(entries)
    upheld = [e for e in standing if e.get("kind") == "park" and not ledger.decides_continue(e)]
    for entry in upheld:
        problems.append(
            f"decision {entry.get('n')}: the panel upheld the adversarial reviewer's park "
            f"({str(entry.get('decision') or '').strip()[:80] or 'no decision'!r})"
        )
    # a closing names its ledger line (``decided (by panel #n):``, 0.2.15), so the words after
    # it may be tidied; the 0.2.14 form without the number is matched on the decision text.
    # The line may live in an earlier phase's ledger: a concern closed at (design) stays closed
    # through build, test and deploy (0.2.18; the first build under deferred review parked here)
    earlier = [
        e
        for _ph, phase_entries in ledger.load_ledgers(ctx.change_dir, ctx.phase)
        for e in phase_entries
        if e.get("kind") in ("concern", "policy")
    ]
    # each ledger line closes one concern: a line is consumed by the first closing that names
    # it, and a second closing on the same number is refused (1.0.0 readiness review, group A)
    unused = Counter(e.get("n") for e in earlier)
    concern_decisions = {
        " ".join(str(e.get("decision", "")).split()).lower() for e in ledger.active(earlier)
    }
    for n, item in ledger.panel_closings(spec):
        if n is not None:
            if n not in unused:
                problems.append(
                    f"spec.md closes a concern by panel decision {n}, which no ledger of "
                    f"phases {'/'.join(ledger.phases_up_to(ctx.phase))} carries: {item[:80]}"
                )
            elif unused[n] <= 0:
                problems.append(
                    f"spec.md closes a second concern by panel decision {n}; one ledger line "
                    f"closes one concern: {item[:80]}"
                )
            else:
                unused[n] -= 1
            continue
        text = ledger.PANEL_CLOSING_RE.sub("", item, count=1).strip().lower()
        if not any(text.startswith(d) for d in concern_decisions if d):
            problems.append(
                f"spec.md closes a concern by the panel with no ledger line: {item[:80]}"
            )
    if problems:
        return _fail(
            "panel",
            "; ".join(problems),
            "Every panel decision is one ledger line in evidence/decisions-<phase>.json (panel/"
            "cli.py record writes it); a never-to-panel item parks for the owner."
            + (
                " The panel upheld the adversarial reviewer's park (decision "
                + ", ".join(str(e.get("n")) for e in upheld)
                + f" of evidence/decisions-{ctx.phase}.md): read the reviewer's reasons and "
                "the panel's rationale, then either fix what the reviewer names (a review "
                "comment starts the fix round), or let the phase continue: a review comment "
                'on that line of "Decisions taken for you" that names the decision '
                "overturns it - the fix round marks the ledger line overturned (panel/cli.py "
                "overturn) and the owner's word replaces the panel's."
                if upheld
                else ""
            ),
            problems=problems,
            upheld=[e.get("n") for e in upheld],
        )
    return _ok(
        "panel",
        f"{len(standing)} panel decision(s) recorded"
        + (f", {len(entries) - len(standing)} overturned" if len(entries) > len(standing) else ""),
        decisions=[
            {"n": e.get("n"), "kind": e.get("kind"), "decision": e.get("decision")}
            for e in standing
        ],
        cost_usd=ledger.total_cost(entries),
    )


# --- which checks at which gate --------------------------------------------------------------
Check = Callable[[GateContext], CheckResult]
# --- 15/16. gate (maintain): the finding and its route (build guide steps 37, 39; decisions 14,
# 25, 26)
DETECTION_NEED = (
    "The maintain run files a change from a detection record (detect/cli.py run --file) or "
    "the weekly security review from a scan finding (scan/cli.py route); an incident intent "
    "without one, or from a dismissed finding, is not a triage item. Close this PR, or "
    "re-run the detection."
)
ROUTE_NEED = (
    "The diagnosis writes evidence/proposal.json (route, args, rationale) and detect/cli.py "
    "dispatch records the route's outcome in evidence/runbook-<name>.json; re-run "
    "/sdlc-maintain <id>."
)


def _detect_modules():
    from detect import dismissals, finding, routes  # noqa: PLC0415 - only at gate (maintain)

    return dismissals, finding, routes


def check_detection(ctx: GateContext) -> CheckResult:
    """The finding exists, is recent enough to act on (tier 2 or 3) and is not dismissed: a
    dismissal with a reason suppresses the signature (p.47 step 4), and a dismissed finding
    that is filed anyway is not the owner's to triage again."""
    dismissals, finding, _routes = _detect_modules()
    record, why = finding.read_any(ctx.evidence_dir)
    if record is None:
        return _fail("detection", why, DETECTION_NEED)
    if record["tier"] < 2:
        return _fail(
            "detection",
            f"tier {record['tier']} ({record.get('rule') or 'no rule'}): the 1σ tier only "
            "logs (p.43 step 3)",
            DETECTION_NEED,
            tier=record["tier"],
        )
    store = dismissals.load(dismissals.path_for(ctx.root, c.CHANGES_DIR))
    entry = dismissals.lookup(store, record["signature"])
    if entry:
        return _fail(
            "detection",
            f"finding {record['signature']} ({record['metric']}, {record.get('rule')}) was "
            f"dismissed by {entry.get('by')} on {entry.get('at')}: {entry.get('reason')}",
            DETECTION_NEED,
            dismissal=entry,
        )
    return _ok(
        "detection",
        f"{record['metric']} at tier {record['tier']} ({record.get('rule')}), "
        f"signature {record['signature']}, not dismissed",
        tier=record["tier"],
        rule=record.get("rule"),
        signature=record["signature"],
        forced=record.get("forced", False),
    )


def check_route(ctx: GateContext) -> CheckResult:
    """The proposed route is one bands.yaml lists for the tier, and it was taken: a
    pre-approved runbook ran (its PR is open, the record says ``ran``); an ``ask`` route waits
    for the owner's ``sdlc:go`` (parks with "Go" requested, decision 14); a failed runbook
    parks with its reason; ``pull_request`` is this PR itself."""
    dismissals, finding, routes = _detect_modules()
    from detect import bands as bands_mod  # noqa: PLC0415

    record, why = finding.read_any(ctx.evidence_dir)
    if record is None:
        return _fail("route", why, DETECTION_NEED)
    proposal, why = routes.load_proposal(ctx.evidence_dir / finding.PROPOSAL_FILE)
    if proposal is None:
        return _fail("route", why, ROUTE_NEED)
    # the bands the owner approved: the merge base's copy when the branch changed the file
    # (as the gate reads sdlc.yaml), else the checkout's
    bands_text = None
    if ctx.diff is not None and ctx.diff.merge_base and bands_mod.BANDS_FILE in ctx.diff.files:
        bands_text = diffmod.file_at(ctx.root, ctx.diff.merge_base, bands_mod.BANDS_FILE)
    try:
        bands = (
            bands_mod.load_text(bands_text)
            if bands_text is not None
            else bands_mod.load_project(ctx.root)
        )
    except bands_mod.BandsError as exc:
        return _fail("route", f"bands.yaml: {exc}", "Fix bands.yaml in a reviewed PR.")
    language = _project_language(ctx.root)
    resolved, why = routes.validate_proposal(
        proposal, int(record["tier"]), bands, ctx.config, language
    )
    if resolved is None:
        return _fail("route", why, ROUTE_NEED, proposal=proposal.as_dict())
    routes.apply_forced(resolved, bool(record.get("forced")))
    details = {"proposal": proposal.as_dict(), "resolved": resolved.as_dict()}
    if resolved.route == routes.PULL_REQUEST:
        return _ok("route", "pull_request: this intent PR is the route (p.44 step 5)", **details)
    name = resolved.runbook or ""
    outcome_path = ctx.evidence_dir / f"runbook-{name}.json"
    try:
        outcome = json.loads(outcome_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        outcome = None
    if not isinstance(outcome, dict):
        return _fail(
            "route",
            f"runbook {name} was proposed and no evidence/runbook-{name}.json records what "
            "happened",
            ROUTE_NEED,
            **details,
        )
    status = str(outcome.get("status") or "")
    details["outcome"] = outcome
    asked = resolved.authorization == routes.ASK
    if status == "ran" and asked and not outcome.get("authorized_by"):
        return _fail(
            "route",
            f"runbook {name} is recorded as run, but its route needs the service owner's Go "
            "and the record names nobody who gave it",
            f"An `ask` route runs only through `{c.GO_LABEL}` (sdlc-runbook.yml records the "
            "actor); re-run /sdlc-maintain <id> to record the route again.",
            **details,
        )
    if (
        status == "ran"
        and resolved.builtin
        and not (outcome.get("pr_url") or outcome.get("reason"))
    ):
        return _fail(
            "route",
            f"runbook {name} is recorded as run with no pull request and no reason",
            "The shipped runbooks open a pull request the review gate decides on (p.45); "
            "re-run /sdlc-maintain <id>.",
            **details,
        )
    if status == "ran":
        return _ok(
            "route",
            f"runbook {name} ran ({resolved.authorization}: {resolved.source})"
            + (f"; PR {outcome['pr_url']}" if outcome.get("pr_url") else ""),
            **details,
        )
    if status == "go-requested":
        return _fail(
            "route",
            f"runbook {name} touches a running system (authorization: ask): Go requested",
            f"Apply `{c.GO_LABEL}` on this PR to run runbook {name} now (it touches a running "
            "system, decision 14), or merge to fix through the pipeline, or close with a "
            "reason to dismiss the finding.",
            **details,
        )
    return _fail(
        "route",
        f"runbook {name}: {status or 'unknown'}: {outcome.get('reason') or ''}".rstrip(": "),
        f"The runbook did not complete: {outcome.get('reason') or 'see the record'}. Fix "
        "the cause (or run it by hand) and re-run /sdlc-maintain <id>, or merge / close this "
        "PR.",
        **details,
    )


def _lesson_field_problems(lesson_name: str, fm: dict[str, Any]) -> list[str]:
    problems = []
    for name, kind in art.LESSON_REQUIRED_FIELDS.items():
        value = fm.get(name)
        present = (
            (kind == "scalar" and isinstance(value, str) and value.strip())
            or (kind == "list" and isinstance(value, list) and value)
            or (kind == "mapping" and isinstance(value, dict) and value)
        )
        if not present:
            problems.append(f"{lesson_name}: frontmatter field {name!r} missing or not a {kind}")
    status = fm.get("status")
    if isinstance(status, str) and status.strip() and status not in art.LESSON_STATUSES:
        problems.append(f"{lesson_name}: status {status!r} is not one of {art.LESSON_STATUSES}")
    return problems


_SUPERSEDES_NAME_RE = re.compile(r"^[0-9]{4}-[0-9]{2}-.+\.md$")


def _supersedes_problem(lessons_dir: Path, lesson_name: str, fm: dict[str, Any]) -> str | None:
    supersedes = fm.get("supersedes")
    if not (isinstance(supersedes, str) and supersedes.strip()):
        return None

    if (
        Path(supersedes).name != supersedes
        or not _SUPERSEDES_NAME_RE.match(supersedes)
        or supersedes == lesson_name
    ):
        return f"{lesson_name}: supersedes must name a lesson file in lessons/"
    target = lessons_dir / supersedes
    if not target.is_file():
        return f"{lesson_name}: supersedes target {supersedes!r} does not exist"
    target_fm, _why = lessons_mod.read_frontmatter(target)
    if target_fm is None:
        return f"{lesson_name}: supersedes target {supersedes!r} is unreadable"
    if target_fm.get("status") != "retired":
        return f"{lesson_name}: supersedes target {supersedes!r} has not been retired"
    return None


# --- lesson and eval, gate (deploy) only (build guide: change 0003) -------------------------------
def lesson_and_eval(ctx: GateContext) -> CheckResult:
    """An incident change's fix ships with its lesson and its eval (spec.md change 0003).
    Guarded on ``ctx.phase == "deploy"`` as well as the route, not only registered for
    "deploy" in ``CHECKS_BY_PHASE``: the same ``entry_route == "incident"`` holds all the way
    through the maintain phase too, before either the lesson or the eval exists, and this
    check must never run there (the regression guard is
    ``test_gate_f_waits_for_the_owner_s_triage...``)."""
    if not (ctx.status.entry_route == "incident" and ctx.phase == c.DEPLOY):
        return _ok("lesson_and_eval", "not an incident change at gate (deploy): nothing to check")

    problems: list[str] = []
    lessons_dir = ctx.root / "lessons"
    pattern = art.lesson_glob(ctx.status.slug)
    matches = sorted(ctx.root.glob(pattern))
    if not matches:
        problems.append(f"no lesson file matches {pattern}")
    elif len(matches) > 1:
        names = ", ".join(m.relative_to(ctx.root).as_posix() for m in matches)
        problems.append(f"{len(matches)} lesson files match {pattern}: {names}")
    else:
        lesson_path = matches[0]
        fm, why = lessons_mod.read_frontmatter(lesson_path)
        if fm is None:
            problems.append(f"{lesson_path.name}: {why}")
        else:
            problems += _lesson_field_problems(lesson_path.name, fm)
            supersedes_problem = _supersedes_problem(lessons_dir, lesson_path.name, fm)
            if supersedes_problem:
                problems.append(supersedes_problem)

    eval_dir = ctx.root / "evals" / "cases" / f"{ctx.status.id}-{ctx.status.slug}"
    eval_rel = eval_dir.relative_to(ctx.root).as_posix()
    for name in (art.EVAL_PROMPT, art.EVAL_CHECKS):
        if not (eval_dir / name).is_file():
            problems.append(f"{eval_rel}/{name} is missing")

    index_ok, _diff, _notes = lessons_mod.check(ctx.root)
    if not index_ok:
        problems.append("lessons/index.md is not what `plugin/lessons/index.py build` would write")

    if problems:
        return _fail(
            "lesson_and_eval",
            "; ".join(problems),
            "\n    ".join(problems),
            problems=problems,
        )
    return _ok("lesson_and_eval", "the lesson, its frontmatter and the eval case are all present")


def _project_language(root: Path) -> str:
    try:
        from init import detect as detect_mod  # noqa: PLC0415

        return detect_mod.detect(root).language
    except Exception:  # noqa: BLE001 - detection is a hint for the runbooks, never a park
        return "unknown"


CHECKS_BY_PHASE: dict[str, tuple[Check, ...]] = {
    # gate (intent) judges the intent PR: since 0.2.26 ``design_scope`` refuses a source file on it
    # (OPERATING_MODEL section 4.2 promised it for the fix round at (intent); change 0000 is exempt)
    c.INTENT: (
        check_artifacts,
        check_evidence_links,
        check_design_scope,
        check_guardrails,
        check_risk_list,
    ),
    c.DESIGN: (
        check_artifacts,
        check_evidence_links,
        check_design_scope,
        check_open_concerns,
        check_proof_items,
        check_panel,
        check_commands,
        check_guardrails,
        check_risk_list,
        check_owner_actions,
        check_adversarial_verdict,
        check_reviewer_model,
    ),
    c.BUILD: (
        check_clean_tree,
        check_artifacts,
        check_evidence_links,
        check_open_concerns,
        check_panel,
        check_commands,
        check_evidence,
        check_proof,
        check_findings,
        check_plan_sync,
        check_guardrails,
        check_risk_list,
        check_owner_actions,
        check_test_lock,
        check_ratchets,
        check_adversarial_verdict,
        check_reviewer_model,
    ),
    c.TEST: (
        check_clean_tree,
        check_artifacts,
        check_evidence_links,
        check_open_concerns,
        check_panel,
        check_commands,
        check_evidence,
        check_proof,
        check_findings,
        check_plan_sync,
        check_guardrails,
        check_risk_list,
        check_owner_actions,
        check_test_lock,
        check_ratchets,
        check_adversarial_verdict,
        check_reviewer_model,
    ),
    c.DEPLOY: (
        check_clean_tree,
        check_artifacts,
        check_evidence_links,
        check_open_concerns,
        check_panel,
        check_commands,
        check_evidence,
        check_proof,
        check_findings,
        check_plan_sync,
        check_guardrails,
        check_risk_list,
        check_owner_actions,
        check_test_lock,
        check_ratchets,
        lesson_and_eval,
        check_adversarial_verdict,
        check_reviewer_model,
    ),
    # gate (maintain) = the owner's triage of the incident intent PR (decision 25): the intent in
    # its incident shape, nothing committed outside the change folder (the diagnosis is
    # read-only on source), the guardrails and the risk list as at (intent), the finding itself
    # and the route it took. No toolchain, no verdict, no panel: the maintain phase builds nothing.
    c.MAINTAIN: (
        check_artifacts,
        check_evidence_links,
        check_design_scope,
        check_guardrails,
        check_risk_list,
        check_detection,
        check_route,
    ),
}
