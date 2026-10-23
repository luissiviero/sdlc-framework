"""A red target found by the CI runner starts the next fix round by itself (decision 29;
ROADMAP R10; plugin 1.0.3).

Until 1.0.3 the runner's commands step (``gate.run_deferred_commands``) parked the change on a
red target and the owner's act was the round (PROGRESS choice 154). Now, after that step, the
runner (``ci/run_phase.py``) reads the rewritten gate record with the helpers here:

- ``red_targets``: whether the record is a park on red targets only - the ``commands`` check
  failed with real runs (a non-zero exit, or a timeout), and no other check failed but an
  ``evidence`` check that failed on the logs of those same targets. A missing target, a crashed
  step or a command that did not start is not a red target: the first is an ``sdlc.yaml`` gap
  no run may fix and parks at once, the other two are infrastructure failures, re-run once by
  the commands step itself and then parked;
- below the iteration cap the runner writes ``evidence/auto-round.json`` (``start_round``),
  marks the record and ``status.yaml`` (``mark_fixing``: the PR carries ``sdlc:fixing``
  instead of ``sdlc:needs-human``; the record keeps its failing checks and its ``park``, so the
  check run ``sdlc/<phase>`` stays red), commits them with the run record, refreshes the PR and
  dispatches ``sdlc-fix.yml`` (the workflow token starts no run but by ``workflow_dispatch``,
  and the fix job skips a label the App applied, decision 33);
- the dispatched round (``run_phase.py --phase fix``) turns the pending ``auto-round.json``
  whose head matches into one request of kind ``red-targets`` in ``evidence/fix-requests.json``
  and marks the file ``taken`` (``take_pending``), so a later round does not reuse it;
- at the cap a fresh-context, read-only judge may reset the count once per change
  (``parse_verdict``, ``write_reset``; the reset is marked ``sdlc-runner:<run>`` and recorded in
  ``evidence/auto-reset.json``, which the owner-field guards read); the second cap, a judge
  that declines or fails, parks for the owner as before (``park_record``).

Nothing here talks to GitHub or runs the model: the runner does both.
"""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PLUGIN_DIR = Path(__file__).resolve().parent.parent  # <framework root>/plugin
if str(PLUGIN_DIR) not in sys.path:
    sys.path.insert(0, str(PLUGIN_DIR))

from gate import artifacts as art  # noqa: E402
from gate.gate import NOT_STARTED_EXITS  # noqa: E402 - the shell's 126/127 (gate.not_started)
from state import conventions as c  # noqa: E402
from state import status as status_mod  # noqa: E402

SCHEMA_VERSION = 1
FIX_WORKFLOW = "sdlc-fix.yml"
REQUEST_KIND = "red-targets"
DISPATCHED, TAKEN, NOT_DISPATCHED = "dispatched", "taken", "not-dispatched"
OUTPUT_TAIL_CHARS = 3000
REASONS_CHARS = 1000  # the judge's reasons go into status.yaml, the gate record and the PR body
RUNNER_FILES = (c.AUTO_ROUND_FILE, c.AUTO_RESET_FILE)
HISTORY_LIMIT = 10
# The gates whose fix round may change the code (build, test, deploy): at (a), (b) and (f) the
# gate's design_scope check refuses a source file, so a round could not fix a red target there
# and the change parks for the owner as before.
AUTO_ROUND_PHASES = ("c", "d", "e")
FIX_ROUNDS_CHECK = "fix_rounds"  # the check a park at the cap or a failed dispatch adds
RUNNER_AUTHOR = "sdlc-runner"


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


# --- the run this process is ---------------------------------------------------------------
def github_run(env: dict[str, str]) -> dict[str, Any] | None:
    """``{"id", "url"[, "attempt"]}`` of the GitHub Actions run this process belongs to, from
    the variables every runner sets; None outside a workflow run (by hand)."""
    run_id = str(env.get("GITHUB_RUN_ID") or "").strip()
    if not run_id:
        return None
    server = str(env.get("GITHUB_SERVER_URL") or "https://github.com").rstrip("/")
    repo = str(env.get("GITHUB_REPOSITORY") or "").strip()
    out: dict[str, Any] = {
        "id": run_id,
        "url": f"{server}/{repo}/actions/runs/{run_id}" if repo else None,
    }
    attempt = str(env.get("GITHUB_RUN_ATTEMPT") or "").strip()
    if attempt:
        out["attempt"] = attempt
    return out


def run_label(env: dict[str, str]) -> str:
    """The run id, or ``local`` by hand: the suffix of the runner's reset actor."""
    run = github_run(env)
    return str(run["id"]) if run else "local"


# --- 1. is this park a red target? -----------------------------------------------------------
def _check(record: dict[str, Any], name: str) -> dict[str, Any] | None:
    for ch in record.get("checks") or []:
        if isinstance(ch, dict) and ch.get("name") == name:
            return ch
    return None


def _details(check: dict[str, Any] | None) -> dict[str, Any]:
    details = (check or {}).get("details")
    return details if isinstance(details, dict) else {}


def red_targets(record: dict[str, Any] | None) -> list[dict[str, Any]] | None:
    """The failing targets when ``record`` (a gate record the runner's commands step rewrote)
    is a park on red targets only; None otherwise. Each entry: ``target``, ``command``,
    ``exit_code`` (None on a timeout), ``timed_out``, ``timeout`` and ``output_tail``."""
    if not isinstance(record, dict) or record.get("result") != "park":
        return None
    commands = _check(record, "commands")
    if commands is None or commands.get("ok"):
        return None
    details = _details(commands)
    if details.get("missing") or details.get("crashed") or details.get("deferred"):
        return None  # an sdlc.yaml gap, or an infrastructure failure: parks as before
    if details.get("not_started"):
        return None
    runs = details.get("runs")
    if not isinstance(runs, dict) or not runs:
        return None
    red: list[dict[str, Any]] = []
    for name, run in runs.items():
        if not isinstance(run, dict):
            continue
        code = run.get("exit_code")
        timed_out = code is None and run.get("timeout") is not None
        if (code is None and not timed_out) or code in NOT_STARTED_EXITS:
            return None  # the command did not run (no shell, 126, 127): not the change's failure
        if timed_out or (isinstance(code, int) and not isinstance(code, bool) and code != 0):
            output = str(run.get("output") or "")
            red.append(
                {
                    "target": str(name),
                    "command": str(run.get("command") or ""),
                    "exit_code": None if timed_out else code,
                    "timed_out": timed_out,
                    "timeout": run.get("timeout") if timed_out else None,
                    "output_tail": output[-OUTPUT_TAIL_CHARS:],
                }
            )
    if not red:
        return None
    red_logs = {art.EVIDENCE_TARGETS.get(r["target"]) for r in red}
    for check in record.get("checks") or []:
        if not isinstance(check, dict) or check.get("ok") or check is commands:
            continue
        if check.get("name") == "evidence":
            ev = _details(check)
            files = ev.get("red_files")
            if (
                not ev.get("missing")
                and isinstance(files, list)
                and files
                and all(f in red_logs for f in files)
            ):
                continue  # the evidence check failed on the logs of the same red run
        return None
    return red


def targets_summary(targets: list[dict[str, Any]]) -> str:
    def state(t: dict[str, Any]) -> str:
        return "timed out" if t.get("timed_out") else f"exit {t.get('exit_code')}"

    return ", ".join(f"{t['target']} ({state(t)})" for t in targets)


# --- 2. the round's own file --------------------------------------------------------------------
def round_path(change_dir: Path) -> Path:
    return Path(change_dir) / art.EVIDENCE_DIR / c.AUTO_ROUND_FILE


def read_json(path: Path) -> dict[str, Any] | None:
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) else None


def write_json(path: Path, data: dict[str, Any]) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n"
    )
    return path


def read_round(change_dir: Path) -> dict[str, Any] | None:
    return read_json(round_path(change_dir))


def start_round(
    change_dir: Path,
    phase: str,
    iterations: int,
    cap: int,
    targets: list[dict[str, Any]],
    head: str | None,
    env: dict[str, str],
    after_reset: bool = False,
) -> dict[str, Any]:
    """Write ``evidence/auto-round.json`` for the round the runner is about to dispatch and
    return it. The round number is the count the round's own bump will reach
    (``iterations + 1``); the previous round, if any, moves to ``history``."""
    previous = read_round(change_dir)
    history: list[dict[str, Any]] = []
    if previous:
        history = [h for h in previous.get("history") or [] if isinstance(h, dict)]
        history.append(
            {k: v for k, v in previous.items() if k not in ("history", "schema_version")}
        )
    data = {
        "schema_version": SCHEMA_VERSION,
        "round": int(iterations) + 1,
        "cap": int(cap),
        "phase": phase,
        "head": head,
        "targets": targets,
        "run": github_run(env),
        "at": now(),
        "status": DISPATCHED,
        "after_reset": bool(after_reset),
        "history": history[-HISTORY_LIMIT:],
    }
    write_json(round_path(change_dir), data)
    return data


def set_round_status(change_dir: Path, status: str, **extra: Any) -> dict[str, Any] | None:
    data = read_round(change_dir)
    if data is None:
        return None
    data.update({"status": status, **extra})
    write_json(round_path(change_dir), data)
    return data


# --- 3. the gate record and status.yaml while the round runs -------------------------------
def gate_path(change_dir: Path, phase: str) -> Path:
    return Path(change_dir) / art.EVIDENCE_DIR / art.GATE_RESULT.format(phase=phase)


def mark_fixing(change_dir: Path, phase: str, round_data: dict[str, Any]) -> dict[str, Any]:
    """The record keeps its failing checks and its ``park`` (honest: the tree is red, and the
    check run says so), its label becomes ``sdlc:fixing`` and it names the round; the park
    reason in ``status.yaml`` says an automatic round runs, so neither the PR nor the queue
    shows the change as waiting for the owner."""
    path = gate_path(change_dir, phase)
    record = read_json(path) or {}
    record["label"] = c.FIXING_LABEL
    record["auto_round"] = {
        "round": round_data.get("round"),
        "cap": round_data.get("cap"),
        "file": f"{art.EVIDENCE_DIR}/{c.AUTO_ROUND_FILE}",
    }
    write_json(path, record)
    st = status_mod.read_status(change_dir)
    reason = (
        f"{c.FIXING_PARK_PREFIX}{round_data.get('round')} of {round_data.get('cap')} dispatched "
        f"by the runner (decision 29): {record.get('reason') or 'red target'}"
    )
    st.park(reason, phase=phase)
    status_mod.write_status(change_dir, st)
    return record


def park_record(
    change_dir: Path, phase: str, reason: str, need: str, details: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Park for the owner as today, with one more failed check (``fix_rounds``) that says why
    no automatic round runs: the cap and the judge's reasons, or a dispatch that failed. The
    record's other checks stay; the label is ``sdlc:needs-human`` and ``status.yaml`` carries
    the whole reason."""
    from gate.checks import CheckResult  # noqa: PLC0415
    from gate.gate import GateResult  # noqa: PLC0415

    path = gate_path(change_dir, phase)
    result = GateResult.from_dict(read_json(path) or {"phase": phase})
    result.checks = [ch for ch in result.checks if ch.name != FIX_ROUNDS_CHECK]
    result.checks.append(CheckResult(FIX_ROUNDS_CHECK, False, reason, need, dict(details or {})))
    result.result, result.label = "park", c.NEEDS_HUMAN_LABEL
    write_json(path, result.as_dict())
    st = status_mod.read_status(change_dir)
    st.park(result.reason, phase=phase)
    status_mod.write_status(change_dir, st)
    return result.as_dict()


# --- 4. the dispatched round takes its constraint ------------------------------------------------
def head_matches(root: Path, change_dir: Path, head: str | None) -> bool:
    """Whether the round's ``head`` (the tree the runner found red) is what the fix round
    starts from: HEAD itself, or an ancestor of HEAD from which only the change folder moved
    (the runner's own record commit, the owner's labels committed by the round)."""
    from state import gitops  # noqa: PLC0415

    if not head or not gitops.is_repo(root):
        return False
    try:
        current = gitops.run(root, "rev-parse", "HEAD").strip()
        if current == head:
            return True
        gitops.run(root, "merge-base", "--is-ancestor", head, "HEAD")
        # a rename's source counted (the review of 1.0.26): a file moved into the change
        # folder is a change outside it
        changed = gitops.run(root, "diff", "--name-status", "--no-renames", head, "HEAD")
    except (gitops.GitError, OSError):
        return False
    try:
        rel = Path(change_dir).resolve().relative_to(Path(root).resolve()).as_posix() + "/"
    except ValueError:
        return False
    paths = [line.split("\t", 1)[-1].strip() for line in changed.splitlines() if line.strip()]
    return all(path.startswith(rel) for path in paths)


REQUEST_TEXT = (
    "The runner ran build, test and lint after the session (outside the sandbox) and found "
    "a red target: {summary}. This is automatic fix round {round} of {cap} (decision 29). Make "
    "the failing targets pass: fix the code, not the test; the test-file lock still applies. "
    "The runner runs the targets again after this round."
)


def red_targets_request(data: dict[str, Any]) -> dict[str, Any]:
    """The ``evidence/fix-requests.json`` entry an automatic round applies: the failing
    targets with their exit codes and output tails as the round's constraint."""
    targets = [t for t in data.get("targets") or [] if isinstance(t, dict)]
    lines = [
        REQUEST_TEXT.format(
            summary=targets_summary(targets), round=data.get("round"), cap=data.get("cap")
        )
    ]
    for t in targets:
        state = (
            f"timed out after {t.get('timeout')} s"
            if t.get("timed_out")
            else f"exited {t.get('exit_code')}"
        )
        lines.append(f"\n{t.get('target')}: `{t.get('command')}` {state}; the tail of its output:")
        lines.append("```\n" + str(t.get("output_tail") or "").rstrip() + "\n```")
    run = data.get("run") if isinstance(data.get("run"), dict) else {}
    return {
        "kind": REQUEST_KIND,
        "id": f"auto-round-{data.get('round')}",
        "author": RUNNER_AUTHOR,
        "association": "RUNNER",
        "body": "\n".join(lines),
        "at": data.get("at"),
        "url": run.get("url"),
        "round": data.get("round"),
        "cap": data.get("cap"),
        "head": data.get("head"),
        "targets": [
            {k: t.get(k) for k in ("target", "command", "exit_code", "timed_out")} for t in targets
        ],
    }


def take_pending(
    root: Path, change_dir: Path, env: dict[str, str]
) -> tuple[dict[str, Any] | None, str]:
    """``(request, note)``: the ``red-targets`` request of the pending round whose head matches,
    with ``auto-round.json`` marked ``taken`` by this run; ``(None, why)`` otherwise."""
    data = read_round(change_dir)
    if data is None:
        return None, "no automatic round"
    if data.get("status") != DISPATCHED:
        return None, f"the automatic round {data.get('round')} is {data.get('status')}"
    if not head_matches(root, change_dir, data.get("head")):
        return None, (
            f"the automatic round {data.get('round')} was found red on "
            f"{str(data.get('head'))[:10]}, which is not what this round starts from"
        )
    request = red_targets_request(data)
    # the count as this round starts from it (the owner's labels already performed): the
    # runner counts the round from here, whatever reset came before, by label or by hand
    at_take = status_mod.read_status(change_dir).iterations
    set_round_status(
        change_dir, TAKEN, taken_by={"run": github_run(env) or "local"}, taken_at=now(),
        iterations_at_take=at_take,
    )  # fmt: skip
    request["iterations_at_take"] = at_take
    return request, ""


# --- 5. the judged reset at the cap --------------------------------------------------------------
JUDGE_PROMPT = (
    "You are the fresh-context judge of decision 29 for change {id} ({rel}). The runner's "
    "automatic fix rounds reached the iteration cap ({iterations} of {cap}) and the targets are "
    "still red: {summary}. Read the rounds, read-only: {rel}/evidence/{gate} (the runner's "
    "record of the last round), {rel}/evidence/{round_file} (the last round and the earlier "
    "ones under history), {rel}/evidence/fix-response.md, the logs {rel}/evidence/test.log, "
    "build.log and lint.log when they exist, and {rel}/plan.md. Decide whether one more set of "
    "{cap} automatic rounds is likely to make the targets pass. Reset only when the rounds make "
    "progress (fewer failures, a different failure, a cause the next round can fix in the code) "
    "and the failure is one a session can fix; do not reset when the rounds repeat the same "
    "failure, when the fix needs a test changed under the test-file lock, a guardrail file, a "
    "missing tool or another environment, or when a target hangs for a reason outside the "
    "change. This is the only automatic reset this change gets; the owner sees the change after "
    "the next cap either way. Change nothing. Answer with one JSON object and nothing else: "
    '{{"reset": true or false, "reasons": "two to five sentences"}}'
)
_JSON_RE = re.compile(r"\{.*\}", re.DOTALL)


def judge_prompt(
    change_id: str, rel: str, phase: str, iterations: int, cap: int, targets: list[dict[str, Any]]
) -> str:
    return JUDGE_PROMPT.format(
        id=change_id,
        rel=rel,
        iterations=iterations,
        cap=cap,
        summary=targets_summary(targets),
        gate=art.GATE_RESULT.format(phase=phase),
        round_file=c.AUTO_ROUND_FILE,
    )


def parse_verdict(text: Any) -> dict[str, Any] | None:
    """``{"reset": bool, "reasons": str}`` from the judge's answer, or None when the answer
    holds no such object (a judge that cannot be read parks, it never resets)."""
    if not isinstance(text, str) or not text.strip():
        return None
    candidates = [text.strip()]
    found = _JSON_RE.search(text)
    if found:
        candidates.append(found.group(0))
    for candidate in candidates:
        try:
            data = json.loads(candidate)
        except ValueError:
            continue
        if isinstance(data, dict) and isinstance(data.get("reset"), bool):
            reasons = data.get("reasons")
            text = " ".join(str(reasons).split()) if reasons is not None else ""
            if len(text) > REASONS_CHARS:
                text = text[: REASONS_CHARS - 1].rstrip() + "…"
            return {"reset": data["reset"], "reasons": text}
    return None


def reset_path(change_dir: Path) -> Path:
    return Path(change_dir) / art.EVIDENCE_DIR / c.AUTO_RESET_FILE


def reset_used(root: Path, change_dir: Path, st: Any) -> str:
    """Why the one automatic reset of this change is spent, or "": the file is on the branch,
    the count names a runner reset, or the file is anywhere in the branch's history (a
    session that deleted it does not earn a second reset)."""
    from state import gitops  # noqa: PLC0415
    from state.unpark import is_runner_reset  # noqa: PLC0415

    if reset_path(change_dir).is_file():
        return f"evidence/{c.AUTO_RESET_FILE} records it"
    if is_runner_reset(getattr(st, "iterations_reset_by", None)):
        return f"status.yaml names it ({st.iterations_reset_by})"
    if gitops.is_repo(root):
        try:
            rel = Path(change_dir).resolve().relative_to(Path(root).resolve()).as_posix()
        except ValueError:
            rel = ""
        if rel:
            found = gitops.run(
                root, "log", "--format=%H", "-n", "1", "--", f"{rel}/{art.EVIDENCE_DIR}/"
                f"{c.AUTO_RESET_FILE}", check=False,
            ).strip()  # fmt: skip
            if found:
                return f"the branch's history carries evidence/{c.AUTO_RESET_FILE} ({found[:10]})"
    return ""


def write_reset(
    change_dir: Path,
    phase: str,
    verdict: dict[str, Any],
    cap: int,
    env: dict[str, str],
    head: str | None,
    judge: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Reset the counts as ``sdlc:reset-iterations`` does (both back to 0), marked as the
    runner's (``iterations_reset_by = sdlc-runner:<run>``, ``iterations_reset_at``), and
    write ``evidence/auto-reset.json`` with the same actor and stamp, the verdict and the
    run: the record the owner-field guards accept this reset by, and nothing else."""
    st = status_mod.read_status(change_dir)
    actor = c.RUNNER_RESET_PREFIX + run_label(env)
    at = now()
    data = {
        "schema_version": SCHEMA_VERSION,
        "reset": True,
        "actor": actor,
        "at": at,
        "reasons": verdict.get("reasons") or "",
        "phase": phase,
        "cap": int(cap),
        "iterations_before": st.iterations,
        "panel_calls_before": st.panel_calls,
        "head": head,
        "run": github_run(env),
        "judge": dict(judge or {}),
    }
    st.iterations = 0
    st.panel_calls = 0
    st.iterations_reset_by = actor
    st.iterations_reset_at = at
    st.touch()
    status_mod.write_status(change_dir, st)
    write_json(reset_path(change_dir), data)
    return data


# --- 6. the runner's own files are not the session's ---------------------------------------------
def snapshot_runner_files(change_dir: Path) -> dict[str, bytes | None]:
    """``auto-round.json`` and ``auto-reset.json`` as they stand right before the session:
    the runner writes them, the session must not (a planted pending round would reach the
    next round as the runner's own request; a planted reset record would pass the owner-field
    guards)."""
    out: dict[str, bytes | None] = {}
    for name in RUNNER_FILES:
        path = Path(change_dir) / art.EVIDENCE_DIR / name
        try:
            out[name] = path.read_bytes() if path.is_file() else None
        except OSError:
            out[name] = None
    return out


def runner_file_mismatches(change_dir: Path, before: dict[str, bytes | None]) -> list[str]:
    """After the session: each runner file the session created, changed or deleted is put
    back as it was, and named (the caller parks, as for the owner-only fields)."""
    reasons: list[str] = []
    for name, was in before.items():
        path = Path(change_dir) / art.EVIDENCE_DIR / name
        try:
            now = path.read_bytes() if path.is_file() else None
        except OSError:
            now = None
        if now == was:
            continue
        what = "created" if was is None else ("deleted" if now is None else "changed")
        reasons.append(f"evidence/{name}: the session {what} it; only the runner writes it")
        if was is None:
            path.unlink(missing_ok=True)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(was)
    return reasons
