"""R18: a failed CI run explains itself (``docs/proposals/failed-run-explains-itself.md``).

The phase runner writes its final JSON to ``--out`` on every exit path, with the case it
leaves for the triage step (``run_case``): ``park`` when this run parked on a check with a
log to read (the commands step, an unfinished fix session; a red target at the iteration
cap keeps its ``commands`` check), ``red`` when it ended non-zero with no park, nothing
otherwise; a park that already says why (a guardrail, the owner fields, the panel model, a
pre-run park) gets no triage and costs no model call. The setup step's ``--out`` file is
the third source: a failed setup is a red run with no runner result.

``run_phase.py --phase triage --out <file> [--setup <file>]`` runs after a fresh framework
checkout. The read-only session (the Read tool only, ``.git`` denied, no GitHub token in its
environment) reads the files ``logs_for`` names and answers in at most five lines; each
line passes the secrets check (``hooks/secrets_check.py find_secrets``) or is dropped. Then,
outside the session, the lines join the park block (``GateResult.triage``, printed under
"Triage (model-written)") or a failed-run record on its own ref, ``FAILED_RUN_REF``, which
the digest's "Failed runs" line reads (``pr/failed_runs.py``). Decisions 11 and 20 stay:
nothing posts a comment and nothing notifies.
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PLUGIN_DIR = Path(__file__).resolve().parent.parent
if str(PLUGIN_DIR) not in sys.path:
    sys.path.insert(0, str(PLUGIN_DIR))

from gate import artifacts as art  # noqa: E402
from hooks.secrets_check import find_secrets  # noqa: E402

OUT_SCHEMA = 1
# the failed checks whose park has a log to read: the commands step (a red target, or a step
# that could not run) and the fix session that did not finish (``run_phase.UNFINISHED_CHECK``)
TRIAGED_PARK_CHECKS = ("commands", "fix")
CASES = ("park", "red", "setup")
MAX_LINES = 5
LINE_MAX = 400  # characters of one stored line
FAILED_RUN_REF = "refs/sdlc/failed-runs/{run}-{attempt}"  # one ref per run: nothing races
FAILED_RUN_PREFIX = "refs/sdlc/failed-runs/"
RECORD_FILE = "failed-run.json"
WORK_DIR = (".sdlc-cache", "triage")  # under the checkout, excluded from git by the runner
RUNNER_DID_NOT_FINISH = "the runner did not finish: it wrote no result file"
SETUP_FAILED = "the project's setup failed: {line}"
NO_RUN_ID = "no GITHUB_RUN_ID: not a workflow run, so no failed-run record"
REASON_WITHHELD = "the runner's reason is withheld: the secrets check flagged it; read the job log"


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_json(path: str | Path | None) -> dict[str, Any] | None:
    if not path:
        return None
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) else None


def failed_checks(record: dict[str, Any] | None) -> list[str]:
    """The names of the failed checks of a park record; [] for anything else."""
    if not isinstance(record, dict) or record.get("result") != "park":
        return []
    return [
        str(ch.get("name"))
        for ch in record.get("checks") or []
        if isinstance(ch, dict) and ch.get("ok") is False
    ]


def run_case(code: int, record: dict[str, Any] | None, fresh: bool) -> str | None:
    """What the triage step does after a phase run: ``park`` for a park this run wrote on a
    check with a log to read, ``red`` for a non-zero exit with no park this run wrote, None
    otherwise (a green run, a park that already says why: it is in the queue already)."""
    if fresh and failed_checks(record):
        return "park" if set(failed_checks(record)) & set(TRIAGED_PARK_CHECKS) else None
    return "red" if code != 0 else None


def setup_failed(setup: dict[str, Any] | None) -> bool:
    """Whether ``project_setup.py --out`` recorded a failure (``ok`` false, an ``error``, or
    a non-zero exit); a skipped setup did not fail."""
    if not isinstance(setup, dict):
        return False
    code = setup.get("exit_code")
    failed_exit = isinstance(code, int) and not isinstance(code, bool) and code != 0
    return bool(setup.get("error")) or setup.get("ok") is False or failed_exit


def case_of(out: dict[str, Any] | None, setup: dict[str, Any] | None) -> str | None:
    """The case the triage step handles: the setup's failure first (the runner never ran),
    then the runner's own ``triage`` field; a missing result file reads as a red run whose
    runner did not finish (the workflow runs the step only after a failure or a park)."""
    if setup_failed(setup):
        return "setup"
    if out is None:
        return "red"
    case = out.get("triage")
    return case if case in CASES else None


def _existing(root: Path, paths: list[Any]) -> list[str]:
    seen: list[str] = []
    for raw in paths:
        if not raw:
            continue
        path = Path(raw)
        path = path if path.is_absolute() else root / path
        if path.is_file():
            try:
                rel = path.resolve().relative_to(root.resolve()).as_posix()
            except ValueError:
                continue  # outside the checkout: the session could not read it
            if rel not in seen:
                seen.append(rel)
    return seen


def logs_for(root: Path, case: str, out: dict[str, Any] | None, copies: list[str]) -> list[str]:
    """The files the session reads, relative to ``root``: ``copies`` (the runner's and the
    setup's JSON, copied under the checkout), then for a park the gate record and the target
    logs or the session's result and stderr, for a red run the session's files."""
    out = out or {}
    paths: list[Any] = list(copies)
    change_dir = out.get("change_dir")
    if case == "park" and change_dir:
        evidence = Path(change_dir) / art.EVIDENCE_DIR
        checks = failed_checks(read_json(root / str(out.get("gate_record") or "")))
        paths.append(out.get("gate_record"))
        if "commands" in checks:
            paths += [evidence / name for name in art.EVIDENCE_TARGETS.values()]
        if "fix" in checks:
            paths.append(out.get("result_file"))
        paths.append(out.get("stderr_file"))
    elif case == "red":
        paths += [out.get("result_file"), out.get("stderr_file")]
    return _existing(root, paths)


def copy_in(root: Path, name: str, data: dict[str, Any] | None) -> str | None:
    """``data`` as a JSON file under the checkout's ``WORK_DIR`` (the session reads only the
    checkout); its path relative to ``root``, or None."""
    if data is None:
        return None
    path = root.joinpath(*WORK_DIR, name)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path.relative_to(root).as_posix()


def lines_of(text: str | None) -> tuple[list[str], int]:
    """The session's answer as at most ``MAX_LINES`` stored lines, each without its bullet
    and cut at ``LINE_MAX``; a line the secrets check flags is dropped (a target's output or
    the session's stderr can carry a project secret, and the text lands in the gate record,
    the PR body, a ref and the digest issue). (kept, dropped count)."""
    lines = []
    for raw in (text or "").splitlines():
        line = raw.strip().lstrip("-*").strip()
        if line:
            lines.append(line[:LINE_MAX])
    lines = lines[:MAX_LINES]
    kept = [line for line in lines if not find_secrets(line)]
    return kept, len(lines) - len(kept)


def add_to_park(path: Path, lines: list[str]) -> bool:
    """The triage lines into the park record at ``path``, the "What I need from you" block
    re-rendered by its one renderer (``GateResult.what_i_need``). False when the record is
    gone or no longer a park."""
    from gate.gate import GateResult  # noqa: PLC0415

    data = read_json(path)
    if not failed_checks(data):
        return False
    result = GateResult.from_dict(data or {})
    result.triage = list(lines)
    path.write_text(
        json.dumps(result.as_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return True


def reason_of(case: str, out: dict[str, Any] | None, setup: dict[str, Any] | None) -> str:
    """The runner's deterministic reason for the failed run, or ``REASON_WITHHELD`` when the
    secrets check flags it: a setup's or a target's last output line can carry a credential
    (an index URL with a token), and the reason lands in a ref and the digest issue."""
    reason = _reason(case, out, setup)
    return REASON_WITHHELD if find_secrets(reason) else reason


def _reason(case: str, out: dict[str, Any] | None, setup: dict[str, Any] | None) -> str:
    if case == "setup":
        from ci.project_setup import failure_line  # noqa: PLC0415

        return SETUP_FAILED.format(line=failure_line(setup or {}))
    if out is None:
        return RUNNER_DID_NOT_FINISH
    if out.get("why"):
        return str(out["why"])
    emitted = out.get("emitted") if isinstance(out.get("emitted"), dict) else {}
    for key in ("skipped", "parked"):
        if emitted.get(key):
            return str(emitted[key])
    return f"the runner exited {out.get('exit_code')}"


def failed_run_record(
    case: str,
    out: dict[str, Any] | None,
    setup: dict[str, Any] | None,
    lines: list[str],
    env: dict[str, str],
    cost: float | None = None,
) -> dict[str, Any]:
    """The record of a red run: the run's address and attempt, the event and its actor, the
    change, the step, the exit code, the reason, whether it parked (a park that ended the
    job red is in the queue already, and the digest drops it) and the triage text."""
    out = out or {}
    server = env.get("GITHUB_SERVER_URL") or "https://github.com"
    repo, run_id = env.get("GITHUB_REPOSITORY", ""), env.get("GITHUB_RUN_ID", "")
    attempt = env.get("GITHUB_RUN_ATTEMPT") or "1"
    return {
        "schema_version": OUT_SCHEMA,
        "run": {
            "id": run_id,
            "attempt": attempt,
            "url": f"{server}/{repo}/actions/runs/{run_id}/attempts/{attempt}" if run_id else "",
            "workflow": env.get("GITHUB_WORKFLOW", ""),
            "event": env.get("GITHUB_EVENT_NAME", ""),
            "actor": env.get("GITHUB_ACTOR", ""),
        },
        "change_id": out.get("change_id"),
        "phase": out.get("phase"),
        "step": "setup" if case == "setup" else "runner",
        "exit_code": None if case == "setup" else out.get("exit_code"),
        "reason": reason_of(case, out or None, setup),
        "parked": case == "park",
        "triage": list(lines),
        "cost_usd": cost,
        "at": _now(),
    }


def _git(root: Path, args: list[str], stdin: str | None = None) -> str | None:
    try:
        proc = subprocess.run(
            ["git", *args],
            cwd=str(root),
            input=stdin,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=60,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return proc.stdout.strip() if proc.returncode == 0 else None


def write_record_ref(root: Path, record: dict[str, Any], env: dict[str, str]) -> dict[str, Any]:
    """The record as a one-file commit on ``FAILED_RUN_REF``, pushed to origin with the job's
    credential (``state/gitops.py run_proc``: git's command-scope config, never a file),
    outside the session. Nothing on a branch moves, and the commit has no parent. The push
    is forced: the ref is this run's own, and one a session pushed first under the same name
    (it knows ``GITHUB_RUN_ID``) is replaced, not kept."""
    from state import gitops  # noqa: PLC0415

    run_id = env.get("GITHUB_RUN_ID")
    if not run_id:
        return {"ok": False, "reason": NO_RUN_ID}
    ref = FAILED_RUN_REF.format(run=run_id, attempt=env.get("GITHUB_RUN_ATTEMPT") or "1")
    body = json.dumps(record, indent=2, sort_keys=True) + "\n"
    blob = _git(root, ["hash-object", "-w", "--stdin"], body)
    tree = _git(root, ["mktree"], f"100644 blob {blob}\t{RECORD_FILE}\n") if blob else None
    commit = (
        _git(root, ["commit-tree", tree, "-m", f"failed run {run_id}: {record['reason']}"[:200]])
        if tree
        else None
    )
    if not commit:
        return {"ok": False, "ref": ref, "reason": "git could not write the record"}
    try:
        proc = gitops.run_proc(root, "push", "origin", f"+{commit}:{ref}")
    except Exception as exc:  # noqa: BLE001 - the record is best effort; the API line stays
        return {"ok": False, "ref": ref, "reason": str(exc)}
    if proc.returncode != 0:
        return {"ok": False, "ref": ref, "reason": (proc.stderr or "").strip()[-300:]}
    return {"ok": True, "ref": ref, "commit": commit}
