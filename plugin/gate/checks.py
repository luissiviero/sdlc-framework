"""The deterministic checks of the confidence gate (build guide step 16; OPERATING_MODEL
section 3). Each check is a function ``(GateContext) -> CheckResult``; ``CHECKS_BY_PHASE``
says which run at the gate of which phase. A failed check carries ``need``: the sentence the
"What I need from you" block shows the owner (decision 11).
"""

from __future__ import annotations

import json
import os
import re
import signal
import subprocess
import sys
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
    cmds = _commands(ctx)
    missing = [k for k in ("build", "test", "lint") if k not in cmds]
    if missing:
        return _fail(
            "commands",
            f"sdlc.yaml has no usable {', '.join(missing)} target",
            "Give the project one-command build/test/lint targets in sdlc.yaml "
            "(re-run /sdlc-init or edit sdlc.yaml in a reviewed PR); the framework does not "
            "enter phase (c) without them (article p.27 step 1).",
            missing=missing,
        )
    timeout = int(ctx.gate_setting("command_timeout", DEFAULT_COMMAND_TIMEOUT))
    runs = {name: run_command(cmd, ctx.root, timeout) for name, cmd in cmds.items()}
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
        )
    return _ok("commands", "build, test and lint exit 0", runs=runs)


# --- 4. evidence present (step 28) --------------------------------------------------------
COMMAND_LOGS = tuple(art.EVIDENCE_TARGETS.values())  # test.log, build.log, lint.log
HEADER_REQUIRED_AT = ("d", "e")  # the gates that read the toolchain's own output


def check_evidence(ctx: GateContext) -> CheckResult:
    required = art.REQUIRED_EVIDENCE.get(ctx.phase, ())
    if not required:
        return _ok("evidence", "no evidence required at this gate")
    missing = []
    red: list[str] = []
    red_names: list[str] = []
    for name in required:
        path = ctx.evidence_dir / name
        text = path.read_text(encoding="utf-8", errors="replace") if path.is_file() else ""
        if not text.strip():
            missing.append(name)
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
        if isinstance(f, dict) and str(f.get("severity", "")).lower() == "important"
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
    if important:
        return _fail(
            "findings",
            f"{len(important)} Important review finding(s) open",
            "Fix every Important finding (or have the owner waive it in a review comment), "
            f"then re-run the review pass so {ctx.change_rel}/evidence/{art.REVIEW_FINDINGS} "
            "shows none.",
            important=important[:20],
        )
    tally = data.get("tally") if isinstance(data.get("tally"), dict) else {}
    return _ok("findings", "no Important review finding", tally=tally)


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
    if ctx.diff is None:
        return _fail("guardrails", ctx.diff_error, "Run the gate inside the project's git repo.")
    patterns = protected_paths.protected_patterns(ctx.config)
    touched = [f for f in ctx.diff.files if any(matches(p, f) for p in patterns)]
    intent_rel = f"{ctx.change_rel}/intent.md"
    if ctx.phase != "a" and intent_rel in ctx.diff.files:
        # the intent was accepted at gate (a): a later phase may not rewrite it (it is what
        # the guardrail exemption and the risk acceptance are judged against)
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
    items = ctx.config.get("risk_list") or []
    if not isinstance(items, list):
        return _fail("risk_list", "sdlc.yaml: risk_list must be a list", "Fix sdlc.yaml.")
    items = [str(i) for i in items if str(i).strip()]
    accepted = {a.lower().strip() for a in ctx.status.risk_accepted}
    paths = ctx.diff.files if ctx.diff else []
    # Only the "Flagged concerns" section of spec.md is read, never its prose: the design
    # prompt and security-baseline rule 8 make every spec name the risk-list items it checked
    # ("none of auth, data migrations, ... is touched"), and a whole-text scan fired on that
    # sentence in every live design run of 2026-09-21. A risk item the design touches is a
    # flagged concern (skill spec-template), so that section is where it is declared.
    texts = {}
    spec = ctx.artifact("spec.md")
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
        return _fail(
            "adversarial_review",
            "adversarial reviewer says escalate: " + ("; ".join(reasons) or "no reason given"),
            "Read the reviewer's reasons and decide: fix and re-run, or accept in review.",
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
def check_clean_tree(ctx: GateContext) -> CheckResult:
    if ctx.diff is None:
        return _fail("clean_tree", ctx.diff_error, "Run the gate inside the project's git repo.")
    prefix = ctx.change_rel + "/"
    tree = diffmod.dirty_files(ctx.root)
    # two kinds of entry are nobody's work: the sandbox's empty placeholders, and the paths
    # the sandbox masks (.env, .idea, .vscode and friends — diffmod.SANDBOX_MASKED)
    ignored = sorted(
        set(diffmod.sandbox_placeholders(ctx.root, tree)) | set(diffmod.sandbox_masked(tree))
    )
    dirty = [f for f in tree if f not in set(ignored) and not f.startswith(prefix)]
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
    prefix = ctx.change_rel + "/"
    committed = diffmod.committed_files(ctx.root, ctx.diff.merge_base, ctx.diff.head)
    outside = [f for f in committed if not f.startswith(prefix)]
    dirty = diffmod.without_placeholders(ctx.root, diffmod.dirty_files(ctx.root))
    if outside:
        return _fail(
            "design_scope",
            f"{len(outside)} committed file(s) outside {prefix}: " + ", ".join(outside[:10]),
            f"Revert them on the branch: phase (b) commits only {prefix}; the first run with "
            "edit tools on source is phase (c).",
            outside=outside[:50],
            dirty=dirty[:50],
        )
    return _ok("design_scope", f"the committed diff stays inside {prefix}", dirty=dirty[:50])


# --- 12. owner-only state: accept-risk and set-iterations (build guide step 24.5) -------------
OWNER_ACTIONS_NEED = (
    "accept-risk and set-iterations are the owner's: run them on your machine or in your own "
    "session and commit; a run cannot approve itself (decision 11)."
)
STATUS_HISTORY_LIMIT = "200"  # commits of status.yaml history the check walks back through


def _status_fields(ctx: GateContext, ref: str) -> dict[str, Any] | None:
    """``risk_accepted`` and ``iterations`` of the change's status.yaml at ``ref``."""
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
    return {"risk": risk, "iterations": iterations}


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
    (PROGRESS known gap); this ties them to the commit author. The newest commit that gained
    a risk item and the newest that lowered the iteration count must not be the automation
    identity, and an acceptance that sits uncommitted in the working tree belongs to nobody:
    the owner commits theirs."""
    if ctx.diff is None:
        return _fail("owner_actions", ctx.diff_error, "Run the gate inside the project's git repo.")
    identities = automation_identity(ctx.config)
    empty = {"risk": set(), "iterations": 0}
    head = _status_fields(ctx, "HEAD") or empty
    tree_risk = {str(r).strip().lower() for r in ctx.status.risk_accepted if str(r).strip()}
    problems: list[str] = []
    gained = sorted(tree_risk - head["risk"])
    if gained:
        problems.append(
            f"risk_accepted gained {', '.join(gained)} in the working tree, in no commit"
        )
    if ctx.status.iterations < head["iterations"]:
        problems.append(
            f"iterations dropped from {head['iterations']} to {ctx.status.iterations} in the "
            "working tree, in no commit"
        )
    risk_event: tuple[str, str, str, list[str]] | None = None
    drop_event: tuple[str, str, str, int, int] | None = None
    for sha, email, name in _status_history(ctx):
        if risk_event is not None and drop_event is not None:
            break
        now = _status_fields(ctx, sha)
        if now is None:
            continue
        before = _status_fields(ctx, f"{sha}^") or empty
        added = sorted(now["risk"] - before["risk"])
        if added and risk_event is None:
            risk_event = (sha, email, name, added)
        if now["iterations"] < before["iterations"] and drop_event is None:
            drop_event = (sha, email, name, before["iterations"], now["iterations"])
    if risk_event and is_automation(risk_event[2], risk_event[1], identities):
        problems.append(
            f"risk_accepted gained {', '.join(risk_event[3])} in commit {risk_event[0][:10]}, "
            f"authored by the automation identity ({risk_event[2]} <{risk_event[1]}>)"
        )
    if drop_event and is_automation(drop_event[2], drop_event[1], identities):
        problems.append(
            f"iterations dropped from {drop_event[3]} to {drop_event[4]} in commit "
            f"{drop_event[0][:10]}, authored by the automation identity "
            f"({drop_event[2]} <{drop_event[1]}>)"
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
        "risk acceptances and iteration resets, if any, were committed by the owner",
        risk_accepted=sorted(tree_risk),
    )


# --- which checks at which gate --------------------------------------------------------------
Check = Callable[[GateContext], CheckResult]
CHECKS_BY_PHASE: dict[str, tuple[Check, ...]] = {
    "a": (check_artifacts, check_guardrails, check_risk_list),
    "b": (
        check_artifacts,
        check_design_scope,
        check_open_concerns,
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
        check_commands,
        check_evidence,
        check_findings,
        check_plan_sync,
        check_guardrails,
        check_risk_list,
        check_owner_actions,
        check_adversarial_verdict,
    ),
    "d": (
        check_clean_tree,
        check_artifacts,
        check_open_concerns,
        check_commands,
        check_evidence,
        check_findings,
        check_plan_sync,
        check_guardrails,
        check_risk_list,
        check_owner_actions,
        check_adversarial_verdict,
    ),
    "e": (
        check_clean_tree,
        check_artifacts,
        check_open_concerns,
        check_commands,
        check_evidence,
        check_findings,
        check_plan_sync,
        check_guardrails,
        check_risk_list,
        check_owner_actions,
        check_adversarial_verdict,
    ),
    "f": (),
}
