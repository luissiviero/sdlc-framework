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
import signal
import subprocess
import sys
import time
from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

PLUGIN_DIR = Path(__file__).resolve().parent.parent
if str(PLUGIN_DIR) not in sys.path:
    sys.path.insert(0, str(PLUGIN_DIR))

from gate import artifacts as art  # noqa: E402
from gate import diff as diffmod  # noqa: E402
from gate.diff import Diff  # noqa: E402
from gate.policy import automation_identity, is_automation  # noqa: E402
from hooks import plan_sync, protected_paths  # noqa: E402
from hooks._common import matches  # noqa: E402
from state import conventions as c  # noqa: E402
from state import yamlish  # noqa: E402
from state.status import STATUS_FILE, Status  # noqa: E402

PLACEHOLDER_COMMAND_RE = re.compile(r"^\s*echo\s+no\s+\w+\s+target\s*$", re.IGNORECASE)
DEFAULT_COMMAND_TIMEOUT = 900  # seconds per command; sdlc.yaml: gate.command_timeout
OUTPUT_TAIL = 4000  # characters of command output kept in the gate result
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
    profile: str = "standard"
    config_note: str = ""  # set when the config was taken from the merge base
    # decision 21: ``parked`` | ``deferred`` (sdlc.yaml: review, status.yaml: review_override)
    review_mode: str = "parked"
    # issue #91 (0.3.0): the runner runs the ``commands`` check after the session (set from
    # ``COMMANDS_RUNNER_ENV`` by ``gate.build_context``; a by-hand gate runs them itself)
    commands_deferred: bool = False

    @property
    def deferred(self) -> bool:
        return self.review_mode == "deferred"

    @property
    def evidence_dir(self) -> Path:
        return self.change_dir / art.EVIDENCE_DIR

    @property
    def change_rel(self) -> str:
        return str(self.change_dir.relative_to(self.root)).replace("\\", "/")

    def artifact(self, name: str) -> str | None:
        return art.read_text(self.change_dir / name)

    def approved_artifact(self, name: str) -> str | None:
        """The artifact as committed on the base branch (what the owner approved), falling
        back to the working tree only when there is no base to compare with."""
        if self.diff is not None and self.diff.merge_base:
            committed = diffmod.file_at(
                self.root, self.diff.merge_base, f"{self.change_rel}/{name}"
            )
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


# --- 3. tests/build/lint green via the sdlc.yaml commands (step 14: refuse to enter (c)) -----
def commands_from_config(config: dict[str, Any]) -> dict[str, str]:
    """The usable ``sdlc.yaml: commands`` targets ("echo no lint target" is not one). Shared
    with plugin/evidence/collect.py so the gate and the evidence writer run the same lines."""
    cmds = config.get("commands")
    out: dict[str, str] = {}
    if isinstance(cmds, dict):
        for key in ("build", "test", "lint"):
            value = cmds.get(key)
            if isinstance(value, str) and value.strip() and not PLACEHOLDER_COMMAND_RE.match(value):
                out[key] = value.strip()
    return out


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
    command: str, root: Path, timeout: int, tail: int | None = OUTPUT_TAIL
) -> dict[str, Any]:
    """Run one project target through the platform shell (the targets are the owner's own
    one-liners: `npm test`, `python -m pytest`; on Windows the .cmd shims need cmd.exe). The
    command runs in its own process group so a timeout kills the whole tree. ``tail`` caps
    the kept output (the gate result keeps the tail; ``None`` keeps the literal output, which
    is what the evidence writer of step 28 stores)."""
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
        "enter phase (c) without them (article p.27 step 1).",
        missing=missing,
    )


def run_targets(ctx: GateContext) -> dict[str, dict[str, Any]]:
    """Run the three targets once, keeping the literal output and the seconds each took:
    ``{name: {"command", "exit_code", "output", "seconds"[, "timeout"]}}``. The gate's record
    keeps the tail of the output (``judge_targets``); the evidence logs keep it whole (item
    3b: the runner writes ``test.log``, ``build.log`` and ``lint.log`` from this same run)."""
    timeout = int(ctx.gate_setting("command_timeout", DEFAULT_COMMAND_TIMEOUT))
    runs: dict[str, dict[str, Any]] = {}
    for name, cmd in _commands(ctx).items():
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
    return _ok("commands", "build, test and lint exit 0", runs=runs, **who)


def run_commands_check(ctx: GateContext, ran_by: str | None = None) -> CheckResult:
    """Run the three targets and judge them (``run_targets`` then ``judge_targets``)."""
    missing = missing_targets(ctx)
    if missing is not None:
        return missing
    return judge_targets(run_targets(ctx), ran_by)


# --- 4. evidence present (step 28) --------------------------------------------------------
COMMAND_LOGS = tuple(art.EVIDENCE_TARGETS.values())  # test.log, build.log, lint.log
HEADER_REQUIRED_AT = ("d", "e")  # the gates that read the toolchain's own output
EVIDENCE_DEFERRED_REASON = (
    "deferred to the runner: the session wrote no command log, the runner writes {logs} "
    "from its build, test and lint after the model's session (issue #91); not yet written"
)


def check_evidence(ctx: GateContext) -> CheckResult:
    required = art.REQUIRED_EVIDENCE.get(ctx.phase, ())
    if not required:
        return _ok("evidence", "no evidence required at this gate")
    missing = []
    red: list[str] = []
    red_names: list[str] = []
    deferred: list[str] = []
    for name in required:
        path = ctx.evidence_dir / name
        text = path.read_text(encoding="utf-8", errors="replace") if path.is_file() else ""
        if not text.strip():
            missing.append(name)
            continue
        if (
            ctx.commands_deferred
            and name in COMMAND_LOGS
            and art.parse_deferred_header(text) is not None
        ):
            # item 3b: inside a CI session the writer left the mark and the runner writes
            # the real log after the session; the mark is accepted only while that step is
            # still to come (``run_deferred_commands`` re-judges this check without it)
            deferred.append(name)
            continue
        # logs written by evidence/collect.py carry their exit code on the first line; a log
        # that records a failure is evidence of a red run, whatever a later re-run says, and
        # at (d) and (e) a command log without that header is not evidence at all
        failure = art.evidence_failure(
            text, require_header=ctx.phase in HEADER_REQUIRED_AT and name in COMMAND_LOGS
        )
        if failure:
            red.append(f"evidence/{name}: {failure}")
            red_names.append(name)
    if missing:
        return _fail(
            "evidence",
            f"evidence/ lacks {', '.join(missing)}",
            "Phase (d) must leave the literal toolchain output and the verifier report in "
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
            EVIDENCE_DEFERRED_REASON.format(logs=", ".join(deferred)),
            deferred=True,
            deferred_logs=deferred,
        )
    return _ok("evidence", f"evidence present: {', '.join(required)}")


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
            return _ok("findings", "no review findings yet (the review pass runs in phase e)")
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
            "under deferred review the panel may settle one the run cannot fix), then re-run "
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
    """The standing ledger entries of ``kind`` for this phase (decision 21), [] unless the
    review mode is deferred: under ``parked`` a ledger decides nothing."""
    if not ctx.deferred:
        return []
    from panel import ledger  # noqa: PLC0415

    return [
        e
        for e in ledger.active(ledger.load_ledger(ctx.change_dir, ctx.phase))
        if e.get("kind") == kind
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
    branch = c.branch_name(change_id, "c")
    exempt = plan_sync.exempt_patterns(ctx.config)
    unsynced = [
        commit.sha[:10]
        for commit in ctx.diff.commits
        if plan_sync.check(branch, commit.files, exempt, planned).block
    ]
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
        )
    unrealised = [p for p in planned if not any(plan_sync.is_planned(f, p) for f in committed)]
    return _ok(
        "plan_sync",
        "every committed source file is in plan.md",
        planned_but_unchanged=unrealised,
    )


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
    if ctx.phase not in ("a", "f") and intent_rel in committed:
        # the intent was accepted at gate (a): a later phase may not rewrite it (it is what
        # the guardrail exemption and the risk acceptance are judged against). Phase (f)
        # writes the incident intent itself (p.44 step 5): its PR is the intent PR of that
        # change, and the owner's merge is its gate (a) (decision 25)
        return _fail(
            "guardrails",
            "intent.md changed on this branch after gate (a)",
            "Revert the intent.md change; an accepted intent changes only through a new "
            "intent PR (phase a).",
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
        "Guardrail files (.claude/**, CLAUDE.md, REVIEW.md, sdlc.yaml, protected_paths) are "
        "changed by the owner in a reviewed PR. Revert them here; a framework change says "
        "'Framework change: yes' in the intent the owner merged at gate (a).",
        touched=touched,
    )


# --- 8. risk list (step 5; OPERATING_MODEL section 9) ------------------------------------------
def _tokens(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


def _phrase_in(tokens: list[str], phrase: list[str]) -> bool:
    n = len(phrase)
    for i in range(len(tokens) - n + 1):
        if all(_tok_eq(tokens[i + j], phrase[j]) for j in range(n)):
            return True
    return False


def _tok_eq(a: str, b: str) -> bool:
    return a == b or a == b + "s" or b == a + "s"


def risk_hits(items: list[str], paths: list[str], texts: dict[str, str]) -> dict[str, list[str]]:
    """{risk item: [where it matched]}; whole-token phrase match, plural-tolerant, so 'auth'
    matches 'auth/' and 'auth_token' but not 'author'."""
    hits: dict[str, list[str]] = {}
    for item in items:
        phrase = _tokens(item)
        if not phrase:
            continue
        where = [p for p in paths if _phrase_in(_tokens(p), phrase)]
        where += [
            f"{name}: text" for name, text in texts.items() if _phrase_in(_tokens(text), phrase)
        ]
        if where:
            hits[item] = where
    return hits


def check_risk_list(ctx: GateContext) -> CheckResult:
    """Risk-list items in the **committed** diff's paths and in the committed spec's
    "Flagged concerns" (OPERATING_MODEL section 3: the gate judges HEAD; see
    ``check_guardrails`` for the sandbox-masked ``.env`` this keeps out)."""
    items = ctx.config.get("risk_list") or []
    if not isinstance(items, list):
        return _fail("risk_list", "sdlc.yaml: risk_list must be a list", "Fix sdlc.yaml.")
    no_base = _no_base(ctx, "risk_list")
    if no_base:
        return no_base
    items = [str(i) for i in items if str(i).strip()]
    accepted = {a.lower().strip() for a in ctx.status.risk_accepted}
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
    # committed after the gate) and does not run at (a) or (b), so the working-tree spec is
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
    live = {k: v for k, v in hits.items() if k.lower().strip() not in accepted}
    if live:
        return _fail(
            "risk_list",
            "risk-list hit: " + "; ".join(f"'{k}' in {', '.join(v[:3])}" for k, v in live.items()),
            "Review the change with the risk in mind. To let it continue, accept the item for "
            'this change: `python "${CLAUDE_PLUGIN_ROOT}/plugin/state/cli.py" accept-risk '
            f'--root . --id {ctx.status.id} --item "<item>"` (recorded in status.yaml).',
            hits=live,
            accepted=sorted(accepted),
        )
    return _ok("risk_list", "no risk-list item touched", accepted=sorted(accepted))


# --- 9. the adversarial reviewer's verdict (step 17; an input, never run by the gate) ---------
def load_verdict(path: Path) -> tuple[dict[str, Any] | None, str]:
    """Format written by the adversarial-reviewer agent:
    {"schema_version": 1, "phase": "c", "head": "<sha>", "verdict": "continue|escalate",
     "reasons": [...], "classification": "routine|non-routine",
     "classification_reasons": [...], "at": "<iso>"}"""
    if not path.is_file():
        return None, "missing"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return None, f"unreadable: {exc}"
    if not isinstance(data, dict) or data.get("verdict") not in ("continue", "escalate"):
        return None, "malformed: 'verdict' must be 'continue' or 'escalate'"
    if data.get("classification") not in ("routine", "non-routine"):
        return None, "malformed: 'classification' must be 'routine' or 'non-routine'"
    if not isinstance(data.get("head"), str) or len(data["head"]) < 7:
        return None, "malformed: 'head' must be the commit sha the verdict judged"
    return data, ""


VERDICT_REQUIRED_AT = ("b", "c", "d")  # every profile: the reviewer runs before each of these


def check_adversarial_verdict(ctx: GateContext) -> CheckResult:
    path = ctx.evidence_dir / art.ADVERSARIAL_VERDICT.format(phase=ctx.phase)
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
    if data["verdict"] == "escalate":
        from panel import ledger  # noqa: PLC0415

        key = ledger.escalate_key(reasons)
        settled = next((e for e in _panel_entries(ctx, "escalate") if e.get("key") == key), None)
        if settled is not None and str(settled.get("decision", "")).lower().startswith("continue"):
            return _ok(
                "adversarial_review",
                "adversarial reviewer said escalate; the review panel decided to continue: "
                + str(settled.get("decision", "")),
                classification=data["classification"],
                reasons=reasons,
                settled_by_panel=settled.get("n"),
            )
        return _fail(
            "adversarial_review",
            "adversarial reviewer says escalate: " + ("; ".join(reasons) or "no reason given"),
            "Read the reviewer's reasons and decide: fix and re-run, or accept in review"
            + (
                " (the panel decided: " + str(settled.get("decision", "")) + ")"
                if settled is not None
                else ""
            )
            + ".",
            reasons=reasons,
            classification=data["classification"],
        )
    return _ok(
        "adversarial_review",
        "adversarial reviewer says continue",
        classification=data["classification"],
        reasons=reasons,
    )


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
    # pass's own record at (d) and (e) (changes/.review-seen.json, written by ``review/cli.py
    # validate`` right before this gate reads the findings file in the change's evidence/,
    # and committed with the evidence after it by ``commit-phase``, 0.3.5: change 0001's fix
    # rounds at gate (e) parked on it — a regular file holding a JSON object, so a deleted,
    # replaced or malformed record is still reported) and, inside a CI session only, what the
    # sandbox has mounted over at any depth (diffmod.sandbox_mounted, 0.3.4; the mark the
    # runner sets says the gate runs inside the sandbox, and by hand a mount over a tracked
    # path is nobody's mask)
    ignored = set(diffmod.sandbox_placeholders(ctx.root, tree)) | set(diffmod.sandbox_masked(tree))
    seen = c.review_seen_rel()
    if ctx.phase in ("d", "e") and seen in tree and _is_review_record(ctx.root / seen):
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


# --- 11. phase (b) touches no source (decision 2; OPERATING_MODEL section 8) -------------------
def check_design_scope(ctx: GateContext) -> CheckResult:
    """The spec-and-plan run of phase (b) is read-only on source: the only files it writes are
    the change folder's own artifacts. The first run with edit tools on source is phase (c).

    The verdict is the **committed** diff only: the files between the merge base and HEAD,
    which is what the PR carries and what would merge. The working tree is reported under
    ``details.dirty`` and never parks the run — the gate may be executed inside Claude Code's
    sandbox, whose masked paths (``diff.SANDBOX_MASKED``) show up as modified or untracked
    however clean the checkout is, and that parked the third live design run (2026-09-21).
    """
    if ctx.diff is None:
        return _fail("design_scope", ctx.diff_error, "Run the gate inside the project's git repo.")
    if ctx.phase == "a" and ctx.change_dir.name.startswith(c.INIT_CHANGE_ID + "-"):
        # the installation PR of /sdlc-init (change 0000) is the one intent PR that carries
        # files outside its folder: the guardrails, the workflows and the pin script it writes
        # (OPERATING_MODEL section 8, layer i). Keyed on the folder name and gate (a) only:
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
        if ctx.phase == "a":
            why = (
                " (the intent PR carries the intent alone; a fix round at gate (a) applies the "
                "owner's review comments to intent.md and nothing else, decision 22)."
            )
        elif ctx.phase == "f":
            why = (
                " (the diagnosis of phase (f) is read-only, p.43 step 3; a runbook works on "
                "a branch of its own)."
            )
        else:
            why = "."
        return _fail(
            "design_scope",
            f"{len(outside)} committed file(s) outside {prefix}: " + ", ".join(outside[:10]),
            f"Revert them on the branch: phase ({ctx.phase}) commits only {prefix}; the "
            "first run with edit tools on source is phase (c)" + why,
            outside=outside[:50],
            dirty=dirty[:50],
        )
    return _ok("design_scope", f"the committed diff stays inside {prefix}", dirty=dirty[:50])


# --- 12. owner-only state: accept-risk and set-iterations (build guide step 24.5) -------------
OWNER_ACTIONS_NEED = (
    "accept-risk, set-iterations and unlock-tests are the owner's: apply sdlc:accept-risk, "
    "sdlc:reset-iterations or sdlc:unlock-tests on the pull request, or run the command on "
    "your machine or in your own session and commit; a run cannot approve itself (decision 5)."
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
    from state.unpark import is_automation_actor  # noqa: PLC0415

    return bool(actor) and not is_automation_actor(str(actor), identities)


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
    # park; L5: without it the park could never be cleared).
    risk_events: list[tuple[str, str, str, list[str], dict[str, str], int]] = []
    drop_events: list[tuple[str, str, str, str, int, int, str | None]] = []
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
                drop_events.append(
                    (counter, sha, email, name, before[counter], now[counter], reset_by)
                )
    labels: dict[str, Any] = {}
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
    for counter, sha, email, name, was, now_count, reset_by in drop_events:
        if not is_automation(name, email, identities):
            continue
        if _label_actor_ok(reset_by, identities):
            labels.setdefault(f"{counter}_reset", reset_by)
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
    changed = diffmod._z(
        diffmod._git(
            ctx.root,
            "diff",
            "--name-only",
            "-z",
            "--diff-filter=ACMRD",
            f"{sha}..HEAD",
            check=False,
        )
    )
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


# --- 13. the decisions ledger of deferred review (decision 21; build guide step 16a) ----------
def _blind_verdicts_problems(ctx: GateContext, entry: dict) -> list[str]:
    """A ledger line written since 0.2.30 names its item (``item_n``); both blind verdicts
    of that item must be committed (HEAD, the gate's rule), each with a ``## Verdict``
    clause. A line without ``item_n`` predates the rule and is not re-judged."""
    from panel import ledger  # noqa: PLC0415

    item_n = entry.get("item_n")
    if isinstance(item_n, bool) or not isinstance(item_n, int):
        return []
    phase = str(entry.get("phase") or ctx.phase)
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
        model_text, ctx.config.get("panel_advocate_model"), phase, item_n
    )
    return [f"decision {entry.get('n')}: {problem}" for problem in missing]


def check_panel(ctx: GateContext) -> CheckResult:
    """Every panel decision has a ledger line and no panel decision touched a never-to-panel
    item. Passes trivially when there is no ledger and no concern closed by the panel."""
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
    if entries and not ctx.deferred:
        problems.append(
            f"the ledger has {len(entries)} decision(s) but the review mode is {ctx.review_mode}"
        )
    standing = ledger.active(entries)
    # a closing names its ledger line (``decided (by panel #n):``, 0.2.15), so the words after
    # it may be tidied; the 0.2.14 form without the number is matched on the decision text.
    # The line may live in an earlier phase's ledger: a concern closed at (b) stays closed
    # through (c), (d) and (e) (0.2.18; the first build under deferred review parked here)
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
            "cli.py record writes it); a never-to-panel item parks for the owner.",
            problems=problems,
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
# --- 15/16. gate (f): the finding and its route (build guide steps 37, 39; decisions 14, 25, 26)
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
    from detect import dismissals, finding, routes  # noqa: PLC0415 - only at gate (f)

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
    pre-approved runbook ran (its PR is open, the record says ``ran``); a ``go`` route waits
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
    if status == "ran" and resolved.authorization == routes.GO and not outcome.get("authorized_by"):
        return _fail(
            "route",
            f"runbook {name} is recorded as run, but its route needs the owner's Go and the "
            "record names nobody who gave it",
            f"A `go` route runs only through `{c.GO_LABEL}` (sdlc-runbook.yml records the "
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
            f"runbook {name} touches a running system (authorization: go): Go requested",
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
            problems.append(f"{lesson_name}: missing frontmatter field {name!r}")
    status = fm.get("status")
    if isinstance(status, str) and status.strip() and status not in art.LESSON_STATUSES:
        problems.append(f"{lesson_name}: status {status!r} is not one of {art.LESSON_STATUSES}")
    return problems


def _supersedes_problem(lessons_dir: Path, lesson_name: str, fm: dict[str, Any]) -> str | None:
    supersedes = fm.get("supersedes")
    if not (isinstance(supersedes, str) and supersedes.strip()):
        return None
    from lessons import index as lessons_mod  # noqa: PLC0415

    target = lessons_dir / supersedes
    if not target.is_file():
        return f"{lesson_name}: supersedes target {supersedes!r} does not exist"
    target_fm, why = lessons_mod.read_frontmatter(target)
    if target_fm is None:
        return f"{lesson_name}: supersedes target {supersedes!r} is unreadable: {why}"
    if target_fm.get("status") != "retired":
        return f"{lesson_name}: supersedes target {supersedes!r} has not been retired"
    return None


# --- lesson and eval, gate (e) only (build guide: change 0003) -------------------------------
def lesson_and_eval(ctx: GateContext) -> CheckResult:
    """An incident change's fix ships with its lesson and its eval (spec.md change 0003).
    Guarded on ``ctx.phase == "e"`` as well as the route, not only registered for phase "e" in
    ``CHECKS_BY_PHASE``: the same ``entry_route == "incident"`` holds all the way through
    phase (f) too, before either the lesson or the eval exists, and this check must never run
    there (the regression guard is ``test_gate_f_waits_for_the_owner_s_triage...``)."""
    if not (ctx.status.entry_route == "incident" and ctx.phase == "e"):
        return _ok("lesson_and_eval", "not an incident change at gate (e): nothing to check")
    from lessons import index as lessons_mod  # noqa: PLC0415

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
    # gate (a) judges the intent PR: since 0.2.26 ``design_scope`` refuses a source file on it
    # (OPERATING_MODEL section 4.2 promised it for the fix round at (a); change 0000 is exempt)
    "a": (check_artifacts, check_design_scope, check_guardrails, check_risk_list),
    "b": (
        check_artifacts,
        check_design_scope,
        check_open_concerns,
        check_panel,
        check_commands,
        check_guardrails,
        check_risk_list,
        check_owner_actions,
        check_adversarial_verdict,
    ),
    "c": (
        check_clean_tree,
        check_artifacts,
        check_open_concerns,
        check_panel,
        check_commands,
        check_evidence,
        check_findings,
        check_plan_sync,
        check_guardrails,
        check_risk_list,
        check_owner_actions,
        check_test_lock,
        check_adversarial_verdict,
    ),
    "d": (
        check_clean_tree,
        check_artifacts,
        check_open_concerns,
        check_panel,
        check_commands,
        check_evidence,
        check_findings,
        check_plan_sync,
        check_guardrails,
        check_risk_list,
        check_owner_actions,
        check_test_lock,
        check_adversarial_verdict,
    ),
    "e": (
        check_clean_tree,
        check_artifacts,
        check_open_concerns,
        check_panel,
        check_commands,
        check_evidence,
        check_findings,
        check_plan_sync,
        check_guardrails,
        check_risk_list,
        check_owner_actions,
        check_test_lock,
        lesson_and_eval,
        check_adversarial_verdict,
    ),
    # gate (f) = the owner's triage of the incident intent PR (decision 25): the intent in
    # its incident shape, nothing committed outside the change folder (the diagnosis is
    # read-only on source), the guardrails and the risk list as at (a), the finding itself
    # and the route it took. No toolchain, no verdict, no panel: phase (f) builds nothing.
    "f": (
        check_artifacts,
        check_design_scope,
        check_guardrails,
        check_risk_list,
        check_detection,
        check_route,
    ),
}
