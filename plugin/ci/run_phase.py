"""One merge-triggered phase run: guard, compose, run ``claude -p``, hand over.

Build guide step 30 (tasks 30.3 and 30.5); the trigger and dispatch table it implements is
docs/OPERATING_MODEL.md sections 4.1 and 4.2; the flag facts are docs/NOTES.md sections 2,
3 and 10b; the read-only triage step is the article's p.41 pipeline step.

    python framework/plugin/ci/run_phase.py --root . --plugin-dir framework \
        --phase b|c|d|e|review --id 0001 --repo owner/name \
        [--head-ref sdlc/0001/a] [--ref main] [--dry-run] [--no-dispatch] [--claude claude]
    python framework/plugin/ci/run_phase.py --phase triage --log out/build.log

What one run does, in order:

1. sets a git identity when the runner has none (the automation identity of
   OPERATING_MODEL section 2; the owner's account never commits from CI);
2. **guards** — not paused, the change exists, ``status.yaml`` is at the phase this run
   follows with a passing gate, not parked, and in the Full profile the owner's approval
   label is on the build PR and was applied by a human, not by the workflow token. A failed
   guard prints ``{"skipped": ...}`` and exits 0, so a duplicate trigger is harmless;
3. creates the ``sdlc:*`` labels the runs apply (422 = the label already exists);
4. for phase (c), runs ``gate/preflight.py``: it decides the permission mode, and a refusal
   that is not about auto-accept parks the change instead of running;
5. composes and runs the bounded headless call — the pinned plugin through ``--plugin-dir``,
   the CI settings file through ``--settings`` (bare mode reads no settings by itself),
   ``--permission-prompts none``, ``--max-turns`` / ``--max-budget-usd`` from ``sdlc.yaml``,
   ``--output-format json`` — with exactly one credential in the environment;
6. stores the JSON result as ``changes/<id>-<slug>/evidence/claude-<phase>.json``, records
   ``total_cost_usd`` with ``gate/cli.py record-spend``, and validates the findings file
   after a review pass;
7. reads ``evidence/gate-<phase>.json`` and, on ``continue``, dispatches the next workflow
   with the change id (the only hand-over GitHub allows from the workflow token).

Exit codes: 0 the run finished, was skipped or parked (a park is a queue item, not a CI
failure); 1 an infrastructure failure — the CLI exited non-zero, reported ``is_error``, or
left no gate file behind; 2 a usage error.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

PLUGIN_DIR = Path(__file__).resolve().parent.parent  # <framework root>/plugin
FRAMEWORK_ROOT = PLUGIN_DIR.parent
if str(PLUGIN_DIR) not in sys.path:
    sys.path.insert(0, str(PLUGIN_DIR))

from ci import auth as auth_mod  # noqa: E402
from gate import artifacts as art  # noqa: E402
from gate import limits  # noqa: E402
from hooks._common import ConfigError, load_sdlc_config  # noqa: E402
from state import conventions as c  # noqa: E402
from state import status as status_mod  # noqa: E402

EXIT_OK, EXIT_FAILED, EXIT_USAGE = 0, 1, 2

# --- the phases this script runs -----------------------------------------------------------
PHASE_COMMAND = {"b": "sdlc-design", "c": "sdlc-build", "d": "sdlc-test", "e": "sdlc-deploy"}
RUNNABLE = (*PHASE_COMMAND, "review", "triage")
# The phase whose artifact this run consumes: status.yaml must be there, with a passing gate
# for every phase past (b) (OPERATING_MODEL section 4.2, "Guard" column).
PREVIOUS_PHASE = {"b": "a", "c": "b", "d": "c", "e": "d", "review": "d"}
GATE_MUST_HAVE_PASSED = ("c", "d", "e", "review")
# Full profile only: the owner's approving label on the build PR, and who applied it.
APPROVAL_LABEL = {"d": "c", "e": "d", "review": "d"}  # run phase -> phase whose label is read
APPROVAL_BRANCH_PHASE = "c"  # the build PR, which lives on sdlc/<id>/c through (d) and (e)
# Hand-over (section 4.2, "Hands over" column). A `wait` or a `park` dispatches nothing.
NEXT_WORKFLOW = {"b": "sdlc-build.yml", "c": "sdlc-test.yml", "d": "sdlc-deploy.yml"}
# Permission mode per phase; (c) asks the preflight instead (step 18, never bypass).
PERMISSION_MODE = {"b": "default", "d": "acceptEdits", "e": "acceptEdits", "review": "default"}
# The review pass is read-only but for the one file it writes (decision 12).
REVIEW_ALLOWED_TOOLS = "Read,Grep,Glob,Bash(git *),Write"
REVIEW_DISALLOWED_TOOLS = "Edit,WebFetch,WebSearch"
# The p.41 read-only triage step: it reads a log and says what it thinks; it fixes nothing.
TRIAGE_ALLOWED_TOOLS = "Read"
TRIAGE_DISALLOWED_TOOLS = "Edit,Write,Bash"
TRIAGE_PROMPT = (
    "Read the CI log at {log}. In at most five lines say what failed, the likely cause and "
    "the first thing to check. Do not fix anything."
)
# Review spend belongs to the deploy phase's budget: it is part of the (e) run.
SPEND_PHASE = {"review": "e"}

CLAUDE_RESULT_FILE = "claude-{phase}.json"
SETTINGS_REL = ("plugin", "ci", "settings.ci.json")

BOT_LOGIN = "github-actions[bot]"
BOT_EMAIL = "41898282+github-actions[bot]@users.noreply.github.com"
LABEL_COLOR_GATE = "0E8A16"  # the *-ready and *-approved labels
LABEL_COLOR_HUMAN = "D93F0B"  # sdlc:needs-human
TOKEN_VARS = ("GITHUB_TOKEN", "GH_TOKEN")

DEFAULT_MAX_TURNS = 200
GRACE_MINUTES = 5  # the subprocess timeout sits this far above the gate's wall clock


def _emit(obj: Any) -> None:
    print(json.dumps(obj, indent=2, sort_keys=True))


def _skip(reason: str) -> int:
    _emit({"skipped": reason})
    return EXIT_OK


# --- git identity ---------------------------------------------------------------------------
def ensure_git_identity(root: Path) -> str | None:
    """Give the checkout the automation identity when the runner configured none."""
    from state import gitops

    if not gitops.is_repo(root):
        return None
    name = gitops.run(root, "config", "--get", "user.name", check=False).strip()
    email = gitops.run(root, "config", "--get", "user.email", check=False).strip()
    if name and email:
        return None
    gitops.run(root, "config", "user.name", BOT_LOGIN)
    gitops.run(root, "config", "user.email", BOT_EMAIL)
    return BOT_LOGIN


# --- configuration --------------------------------------------------------------------------
def _config(root: Path) -> dict[str, Any]:
    try:
        return load_sdlc_config(str(root)) or {}
    except ConfigError:
        return {}


def _gate_settings(config: dict[str, Any]) -> dict[str, Any]:
    gate_cfg = config.get("gate")
    return gate_cfg if isinstance(gate_cfg, dict) else {}


def _int_or(value: Any, default: int) -> int:
    try:
        n = int(value)
    except (TypeError, ValueError):
        return default
    return n if n > 0 else default


def run_timeout_seconds(config: dict[str, Any]) -> int:
    minutes = _int_or(
        _gate_settings(config).get("max_wall_clock_minutes"),
        limits.DEFAULT_MAX_WALL_CLOCK_MINUTES,
    )
    return (minutes + GRACE_MINUTES) * 60


# --- GitHub (imported lazily: plugin/pr/github.py is a sibling deliverable) --------------------
def _github():
    try:
        from pr import github  # noqa: PLC0415
    except ImportError:  # pragma: no cover - only when the plugin install is incomplete
        return None
    return github


def _token(env: dict[str, str]) -> str | None:
    for var in TOKEN_VARS:
        if env.get(var):
            return env[var]
    return None


def ensure_labels(repo: str, env: dict[str, str]) -> dict[str, Any]:
    """Create every label of ``conventions.all_labels()``; an existing one (422) is success."""
    github = _github()
    if github is None or not repo or not _token(env):
        return {"ensured": 0, "note": "no token in the environment: labels not created"}
    created, failed = [], []
    for name in c.all_labels():
        color = LABEL_COLOR_HUMAN if name == c.NEEDS_HUMAN_LABEL else LABEL_COLOR_GATE
        result = github.ensure_label(repo, name, color, f"SDLC framework: {name}")
        if not result.get("ok"):
            failed.append(name)
        elif result.get("created"):
            created.append(name)
    return {"ensured": len(c.all_labels()), "created": created, "failed": failed}


def label_applied_by_a_human(repo: str, number: int, label: str) -> tuple[bool, str]:
    """Read the issue's timeline and say whether a person applied ``label``.

    GitHub records one ``labeled`` event per application, with the actor that caused it; the
    workflow token's own label would be ``github-actions[bot]`` and must never pass a human
    gate (OPERATING_MODEL section 4.2, "actor not the token").
    """
    github = _github()
    if github is None:
        return False, "plugin/pr/github.py is not available"
    tok = github.token()
    if not tok:
        return False, "no GITHUB_TOKEN/GH_TOKEN to read the label events with"
    url = f"{github.API_ROOT}/repos/{repo}/issues/{number}/events"
    result = github._request("GET", url, tok)
    if result.get("error"):
        return False, f"could not read the label events: {result['error']}"
    actors = [
        (event.get("actor") or {}).get("login") or "unknown"
        for event in (result.get("data") or [])
        if event.get("event") == "labeled" and (event.get("label") or {}).get("name") == label
    ]
    if not actors:
        return False, f"no `labeled` event for {label}"
    actor = actors[-1]
    if actor == BOT_LOGIN:
        return False, f"{label} was applied by {actor}, not by a human"
    return True, actor


def check_approval(repo: str, change_id: str, run_phase: str, env: dict[str, str]) -> str | None:
    """Full profile: the skip reason when the owner's approval is not on the build PR."""
    label = c.approved_label(APPROVAL_LABEL[run_phase])
    github = _github()
    if github is None:
        return f"{label} cannot be checked: plugin/pr/github.py is not available"
    if not _token(env) and not github.gh_path():
        print(
            f"note: no GITHUB_TOKEN/GH_TOKEN and no gh on PATH, so the actor of {label} is "
            "not checked; the Full profile relies on branch protection here",
            file=sys.stderr,
        )
        return None
    head = c.branch_name(change_id, APPROVAL_BRANCH_PHASE)
    pr = github.find_open_pr(repo, head)
    number = pr.get("number")
    if not number:
        return f"no open PR on {head} to read {label} from"
    if label not in (pr.get("labels") or []):
        return f"the build PR #{number} does not carry {label}"
    if not _token(env):
        print(f"note: no token, so the actor of {label} is not checked", file=sys.stderr)
        return None
    ok, who = label_applied_by_a_human(repo, int(number), label)
    return None if ok else f"{label} on PR #{number}: {who}"


# --- the guard --------------------------------------------------------------------------------
def resolve_change_id(change_id: str | None, head_ref: str | None, run_phase: str) -> tuple:
    """(change id, skip reason). The id comes from ``--id`` or from ``sdlc/<id>/<phase>``."""
    if change_id:
        if not c.ID_RE.match(change_id):
            return None, f"change id {change_id!r} is not four digits"
        return change_id, None
    parsed = c.parse_branch(head_ref or "")
    if parsed is None:
        return None, "no change id: neither --id nor a head ref of the form sdlc/<id>/<phase>"
    parsed_id, branch_phase = parsed
    expected = PREVIOUS_PHASE[run_phase]
    if branch_phase != expected:
        return None, f"head branch {head_ref} is phase {branch_phase}, not {expected}"
    return parsed_id, None


def guard(root: Path, change_id: str, run_phase: str, repo: str, env: dict[str, str]):
    """(change_dir, status, config, skip reason)."""
    config = _config(root)
    if config.get("paused") is True:
        return None, None, config, "sdlc.yaml says paused: true"
    change_dir = c.find_change_dir(root, change_id)
    if change_dir is None:
        return None, None, config, f"no change folder for id {change_id}"
    try:
        st = status_mod.read_status(change_dir)
    except (OSError, ValueError) as exc:
        return None, None, config, f"status.yaml is unreadable: {exc}"
    expected = PREVIOUS_PHASE[run_phase]
    if st.phase != expected:
        return None, None, config, f"change {change_id} is at phase {st.phase}, not {expected}"
    if st.parked_reason:
        return None, None, config, f"change {change_id} is parked: {st.parked_reason}"
    if run_phase in GATE_MUST_HAVE_PASSED:
        if st.gate.phase != expected or st.gate.result != "passed":
            return (
                None,
                None,
                config,
                f"gate ({expected}) has not passed for change {change_id} "
                f"(gate: {st.gate.phase}/{st.gate.result})",
            )
    profile = c.effective_profile(config.get("profile"), st.profile_override)
    if profile == "full" and run_phase in APPROVAL_LABEL:
        reason = check_approval(repo, change_id, run_phase, env)
        if reason:
            return None, None, config, reason
    return change_dir, st, config, None


# --- the claude command -----------------------------------------------------------------------
def _python() -> str:
    return sys.executable or "python"


def review_prompt(plugin_dir: Path, root: Path, change_id: str) -> tuple[str | None, str]:
    """The review prompt, printed by ``review/cli.py prompt`` (decision 12)."""
    cli = plugin_dir / "plugin" / "review" / "cli.py"
    argv = [_python(), str(cli), "prompt", "--root", str(root), "--id", change_id]
    try:
        proc = subprocess.run(argv, capture_output=True, text=True, encoding="utf-8", timeout=120)
    except (OSError, subprocess.SubprocessError) as exc:
        return None, f"review/cli.py prompt could not run: {exc}"
    if proc.returncode != 0 or not proc.stdout.strip():
        return None, f"review/cli.py prompt exited {proc.returncode}: {proc.stderr.strip()}"
    return proc.stdout.strip(), ""


def compose(
    *,
    claude: str,
    plugin_dir: Path,
    phase: str,
    prompt: str,
    permission_mode: str,
    config: dict[str, Any],
    env: dict[str, str],
) -> list[str]:
    """The full argv of one headless run. It carries no secret, so it is safe to print."""
    argv = [claude, "-p", *auth_mod.flags(env)]
    argv += ["--plugin-dir", str(plugin_dir)]
    argv += ["--settings", str(Path(plugin_dir).joinpath(*SETTINGS_REL))]
    argv += ["--permission-mode", permission_mode]
    argv += ["--permission-prompts", "none"]  # nobody is there to answer (NOTES 10b)
    gate_cfg = _gate_settings(config)
    argv += ["--max-turns", str(_int_or(gate_cfg.get("max_turns"), DEFAULT_MAX_TURNS))]
    budget = gate_cfg.get("max_budget_usd")
    if budget not in (None, "", "null"):
        argv += ["--max-budget-usd", str(budget)]
    argv += ["--output-format", "json"]
    model = env.get("SDLC_MODEL")
    if model:
        argv += ["--model", model]
    if phase == "review":
        argv += ["--allowedTools", REVIEW_ALLOWED_TOOLS]
        argv += ["--disallowedTools", REVIEW_DISALLOWED_TOOLS]
    elif phase == "triage":
        argv += ["--allowedTools", TRIAGE_ALLOWED_TOOLS]
        argv += ["--disallowedTools", TRIAGE_DISALLOWED_TOOLS]
    argv.append(prompt)
    return argv


def invoke(argv: list[str], root: Path, env: dict[str, str], timeout: int) -> tuple:
    """(result dict or None, stdout, stderr, exit code)."""
    try:
        proc = subprocess.run(
            argv,
            cwd=str(root),
            capture_output=True,
            text=True,
            encoding="utf-8",
            env=auth_mod.credential_env(env),
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return None, "", f"claude did not finish within {timeout}s", 124
    except OSError as exc:
        return None, "", f"claude could not start: {exc}", 127
    try:
        data = json.loads(proc.stdout)
    except ValueError:
        data = None
    return data, proc.stdout, proc.stderr, proc.returncode


# --- spend, evidence, hand-over ------------------------------------------------------------------
def store_result(change_dir: Path, phase: str, data: Any, raw: str) -> Path:
    path = change_dir / art.EVIDENCE_DIR / CLAUDE_RESULT_FILE.format(phase=phase)
    path.parent.mkdir(parents=True, exist_ok=True)
    body = json.dumps(data, indent=2, sort_keys=True) if data is not None else raw
    path.write_text(body + "\n", encoding="utf-8", newline="\n")
    return path


def record_spend(plugin_dir: Path, root: Path, change_id: str, phase: str, usd: float) -> bool:
    cli = plugin_dir / "plugin" / "gate" / "cli.py"
    argv = [
        _python(), str(cli), "record-spend",
        "--root", str(root), "--id", change_id,
        "--phase", SPEND_PHASE.get(phase, phase), "--usd", str(usd),
    ]  # fmt: skip
    try:
        proc = subprocess.run(argv, capture_output=True, text=True, encoding="utf-8", timeout=120)
    except (OSError, subprocess.SubprocessError):
        return False
    return proc.returncode == 0


def validate_review(plugin_dir: Path, root: Path, change_id: str) -> dict[str, Any]:
    cli = plugin_dir / "plugin" / "review" / "cli.py"
    argv = [_python(), str(cli), "validate", "--root", str(root), "--id", change_id]
    try:
        proc = subprocess.run(argv, capture_output=True, text=True, encoding="utf-8", timeout=600)
    except (OSError, subprocess.SubprocessError) as exc:
        return {"ok": False, "reason": str(exc)}
    return {"ok": proc.returncode == 0, "exit_code": proc.returncode}


def read_gate(change_dir: Path, phase: str) -> dict[str, Any] | None:
    path = change_dir / art.EVIDENCE_DIR / art.GATE_RESULT.format(phase=phase)
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def dispatch(repo: str, workflow: str, ref: str, change_id: str) -> dict[str, Any]:
    """``POST /repos/{repo}/actions/workflows/{file}/dispatches`` — 204 means accepted.

    ``workflow_dispatch`` is one of the two events GitHub still starts a run for when the
    workflow token causes it, which is why every automated transition goes through here.
    """
    github = _github()
    if github is None:
        return {"ok": False, "reason": "plugin/pr/github.py is not available"}
    tok = github.token()
    if not tok:
        return {"ok": False, "reason": "no GITHUB_TOKEN/GH_TOKEN to dispatch with"}
    url = f"{github.API_ROOT}/repos/{repo}/actions/workflows/{workflow}/dispatches"
    result = github._request("POST", url, tok, {"ref": ref, "inputs": {"change_id": change_id}})
    ok = result.get("status") == 204 or not result.get("error")
    return {"ok": ok, "status": result.get("status"), "reason": result.get("error", "")}


# --- the triage step (article p.41) ---------------------------------------------------------------
def run_triage(args, env: dict[str, str]) -> int:
    if not args.log:
        print("--phase triage needs --log <file>", file=sys.stderr)
        return EXIT_USAGE
    if auth_mod.choose_auth(env)["auth"] is None:
        return _skip(auth_mod.choose_auth(env)["reason"])
    root = Path(args.root).resolve()
    argv = compose(
        claude=args.claude,
        plugin_dir=Path(args.plugin_dir).resolve(),
        phase="triage",
        prompt=TRIAGE_PROMPT.format(log=args.log),
        permission_mode="default",
        config=_config(root),
        env=env,
    )
    if args.dry_run:
        _emit({"phase": "triage", "argv": argv})
        return EXIT_OK
    data, raw, err, code = invoke(argv, root, env, run_timeout_seconds(_config(root)))
    text = (data or {}).get("result") if isinstance(data, dict) else raw
    print(text or raw)
    if code != 0 or (isinstance(data, dict) and data.get("is_error")):
        print(err or raw, file=sys.stderr)
        return EXIT_FAILED
    return EXIT_OK


# --- the phase run --------------------------------------------------------------------------------
def run_phase(args, env: dict[str, str]) -> int:
    root = Path(args.root).resolve()
    plugin_dir = Path(args.plugin_dir).resolve()
    phase = args.phase
    ensure_git_identity(root)

    change_id, reason = resolve_change_id(args.id, args.head_ref, phase)
    if reason:
        return _skip(reason)
    change_dir, st, config, reason = guard(root, change_id, phase, args.repo, env)
    if reason:
        return _skip(reason)
    if auth_mod.choose_auth(env)["auth"] is None and not args.dry_run:
        return _skip(auth_mod.choose_auth(env)["reason"])
    labels = ensure_labels(args.repo, env)

    # phase (c): the preflight decides the permission mode, or parks the change (step 18)
    permission_mode = PERMISSION_MODE.get(phase, "default")
    if phase == "c":
        report = preflight(plugin_dir, root, change_id)
        if not report.get("allow"):
            park(plugin_dir, root, change_id, "preflight: " + "; ".join(report.get("reasons", [])))
            _emit({"parked": report.get("reasons", []), "phase": phase, "change_id": change_id})
            return EXIT_OK
        permission_mode = report.get("permission_mode", "acceptEdits")

    if phase == "review":
        prompt, error = review_prompt(plugin_dir, root, change_id)
        if prompt is None:
            print(error, file=sys.stderr)
            return EXIT_FAILED
    else:
        prompt = f"/sdlc:{PHASE_COMMAND[phase]} {change_id}"

    argv = compose(
        claude=args.claude,
        plugin_dir=plugin_dir,
        phase=phase,
        prompt=prompt,
        permission_mode=permission_mode,
        config=config,
        env=env,
    )
    if args.dry_run:
        _emit({"phase": phase, "change_id": change_id, "argv": argv, "labels": labels})
        return EXIT_OK

    data, raw, err, code = invoke(argv, root, env, run_timeout_seconds(config))
    store_result(change_dir, phase, data, raw)
    cost = None
    if isinstance(data, dict):
        cost = data.get("total_cost_usd")
        if isinstance(cost, (int, float)):
            record_spend(plugin_dir, root, change_id, phase, float(cost))
    if code != 0 or not isinstance(data, dict) or data.get("is_error"):
        text = (data or {}).get("result") if isinstance(data, dict) else raw[-2000:]
        print(text or err or f"claude exited {code}", file=sys.stderr)
        return EXIT_FAILED

    review = validate_review(plugin_dir, root, change_id) if phase == "review" else None
    if phase == "review":
        _emit({"phase": phase, "change_id": change_id, "cost_usd": cost, "review": review})
        return EXIT_OK if review and review.get("ok") else EXIT_FAILED

    result = read_gate(change_dir, phase)
    if result is None:
        print(
            f"the run left no evidence/{art.GATE_RESULT.format(phase=phase)}: the phase command "
            "did not reach its gate",
            file=sys.stderr,
        )
        return EXIT_FAILED
    handed = hand_over(args, result, phase, change_id)
    _emit(
        {
            "phase": phase,
            "change_id": change_id,
            "result": result.get("result"),
            "label": result.get("label"),
            "cost_usd": cost,
            "dispatched": handed,
        }
    )
    return EXIT_OK


def hand_over(args, result: dict[str, Any], phase: str, change_id: str) -> Any:
    workflow = NEXT_WORKFLOW.get(phase)
    if result.get("result") != "continue" or not workflow:
        return None
    ref = args.ref or default_ref(Path(args.root))
    if args.no_dispatch:
        return {"would_dispatch": workflow, "ref": ref, "change_id": change_id}
    return {"workflow": workflow, "ref": ref, **dispatch(args.repo, workflow, ref, change_id)}


def default_ref(root: Path) -> str:
    from state import gitops

    try:
        return gitops.default_branch(root) if gitops.is_repo(root) else "main"
    except Exception:  # noqa: BLE001 - a detached CI checkout must not fail the hand-over
        return "main"


def preflight(plugin_dir: Path, root: Path, change_id: str) -> dict[str, Any]:
    script = plugin_dir / "plugin" / "gate" / "preflight.py"
    argv = [
        _python(), str(script),
        "--root", str(root), "--plugin-root", str(plugin_dir), "--id", change_id,
    ]  # fmt: skip
    try:
        proc = subprocess.run(argv, capture_output=True, text=True, encoding="utf-8", timeout=3600)
    except (OSError, subprocess.SubprocessError) as exc:
        return {"allow": False, "reasons": [f"preflight could not run: {exc}"]}
    try:
        return json.loads(proc.stdout)
    except ValueError:
        return {"allow": False, "reasons": [f"preflight printed no JSON: {proc.stderr.strip()}"]}


def park(plugin_dir: Path, root: Path, change_id: str, reason: str) -> bool:
    cli = plugin_dir / "plugin" / "state" / "cli.py"
    argv = [
        _python(), str(cli), "park",
        "--root", str(root), "--id", change_id, "--reason", reason,
    ]  # fmt: skip
    try:
        proc = subprocess.run(argv, capture_output=True, text=True, encoding="utf-8", timeout=120)
    except (OSError, subprocess.SubprocessError):
        return False
    return proc.returncode == 0


# --- CLI --------------------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="sdlc-run-phase",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--root", default=".", help="the project checkout")
    p.add_argument(
        "--plugin-dir",
        default=str(FRAMEWORK_ROOT),
        help="the pinned framework checkout, passed to claude as --plugin-dir",
    )
    p.add_argument("--phase", required=True, choices=RUNNABLE)
    p.add_argument("--id", default=None, help="change id; omit to read it from --head-ref")
    p.add_argument("--head-ref", default=None, help="the PR head branch sdlc/<id>/<phase>")
    p.add_argument("--repo", default="", help="owner/name, for labels and the hand-over")
    p.add_argument("--ref", default=None, help="default branch the dispatch targets")
    p.add_argument("--log", default=None, help="--phase triage: the CI log to read")
    p.add_argument("--claude", default="claude", help="the CLI executable (default: on PATH)")
    p.add_argument("--dry-run", action="store_true", help="print the argv and stop")
    p.add_argument("--no-dispatch", action="store_true", help="print the hand-over, send nothing")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    env = dict(os.environ)
    if args.phase == "triage":
        return run_triage(args, env)
    if not args.id and not args.head_ref:
        print("--id or --head-ref is required for a phase run", file=sys.stderr)
        return EXIT_USAGE
    return run_phase(args, env)


if __name__ == "__main__":
    sys.exit(main())
