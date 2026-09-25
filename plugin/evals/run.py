"""The eval runner (build guide step 35; decision 17; article p.29-31 "Continuous evals in CI").

    python plugin/evals/run.py --root <project> [--cases <dir>] [--case <glob>]
        [--plugin-dir <framework root>] [--claude claude] [--report <path>]
        [--min-pass-rate 1.0] [--fixture] [--keep] [--dry-run]

"Evals are the AI-native equivalent of stage-gate QA" (p.29). An eval is "the prompt plus
the checks that define acceptable (tests pass, lint clean, behavior unchanged, policy
followed)" (p.30 step 2); the suite "runs non-interactively in CI on a schedule and on any
change to CLAUDE.md, skills or hooks" (step 3), and configuration changes are gated on the
result: "The pass-rate threshold is enforced as a merge check" (p.31). The p.30 workflow runs
``claude -p ... --allowedTools "Read,Edit,Bash(make test)" --output-format json`` and hands
the result to ``evals/check.sh``, which the article does not show; this module is both, in
Python (decision 7).

A case is a folder ``<cases>/<id>-<slug>/`` holding ``prompt.md`` (the task as the agent
receives it) and ``checks.yaml`` (``checks`` plus optional ``description``, ``setup``,
``tools``, ``permission_mode``, ``max_turns``, ``budget_usd``, ``timeout_seconds``; see
``template/evals/README.md``). For each case the runner:

1. copies the project into a throwaway workspace (``.git`` included, so the hooks see a
   repository; ``.sdlc``, ``node_modules``, ``__pycache__``, ``.pytest_cache`` and ``.venv``
   left out) and runs the ``setup`` commands there;
2. snapshots the files the checks compare (``unchanged``) and the case's ``expected/`` files
   (``equals``);
3. runs one bounded headless call in the workspace::

       claude -p <prompt> --output-format json --permission-prompts none
           --permission-mode <mode> --max-turns <n> --max-budget-usd <usd>
           --allowedTools <tools> --disallowedTools WebFetch,WebSearch --plugin-dir <framework>

   with the credential of the environment as it is. The runner never adds ``--bare``: bare
   mode skips "hooks ..., LSP, plugin sync, ... and CLAUDE.md auto-discovery" (the step 35.2
   research note, quoting ``claude --help``), and the project's ``CLAUDE.md``, hooks and
   settings are exactly what the suite regression-tests. Without ``--bare`` print mode uses
   ``ANTHROPIC_API_KEY`` when it is present and ``CLAUDE_CODE_OAUTH_TOKEN`` otherwise
   (``ci/auth.py``). ``SDLC_MODEL``, when set, becomes ``--model`` (the p.29 case of "a new
   model is swapped in");
4. reads the JSON result (``subtype``, ``is_error``, ``num_turns``, ``total_cost_usd``,
   ``result``, ``permission_denials``): ``is_error`` or a subtype other than ``success``
   (``error_max_turns``, ``error_max_budget_usd``, ...) fails the case, and so does output
   that is not JSON or a run past the wall clock ("timed out");
5. evaluates the checks in order, each giving ``{kind, passed, detail}``; the case passes when
   the run succeeded and every check passed. A check with an unknown key, a case folder
   without ``prompt.md`` or ``checks.yaml`` and an unreadable ``checks.yaml`` fail the case
   with the reason: nothing is skipped silently.

The report is JSON (``--report``, default ``evals-report.json`` in the current directory, so
nothing lands in the project) plus a markdown table on stdout; with ``$GITHUB_OUTPUT`` set
the step outputs ``pass_rate``, ``passed``, ``total`` and ``ok`` are appended to it.

``--fixture`` runs the framework-level suite: instead of ``--root`` the project is built from
``tests/fixtures/sample-python-project`` (a git repository with ``/sdlc-init`` applied,
profile standard) and ``--cases`` defaults to this repository's ``evals/cases``.

Commands in ``setup`` and in ``command`` checks run without a shell (``release/cli.py``
``command_chain``: one command, or steps joined by ``&&``); ``python`` falls back to the
interpreter running the suite when it is not on PATH.

Exit codes: 0 the pass rate reaches ``--min-pass-rate`` (an empty suite passes, with the note
"no cases") · 1 below it · 2 usage (no root, no cases folder, a bad option).
"""

from __future__ import annotations

import argparse
import contextlib
import fnmatch
import io
import json
import os
import re
import shutil
import signal
import stat
import subprocess
import sys
import tempfile
import time
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

FRAMEWORK_DIR = Path(__file__).resolve().parents[2]
PLUGIN_DIR = FRAMEWORK_DIR / "plugin"
if str(PLUGIN_DIR) not in sys.path:
    sys.path.insert(0, str(PLUGIN_DIR))

from release.cli import UsageError, command_chain  # noqa: E402

from state import gitops, yamlish  # noqa: E402

SCHEMA_VERSION = 1
FIXTURE = FRAMEWORK_DIR / "tests" / "fixtures" / "sample-python-project"
FRAMEWORK_CASES = FRAMEWORK_DIR / "evals" / "cases"
DEFAULT_REPORT = "evals-report.json"
PROMPT_FILE = "prompt.md"
CHECKS_FILE = "checks.yaml"
EXPECTED_DIR = "expected"

DEFAULT_TOOLS = "Read,Grep,Glob,Edit,Write,Bash(python *),Bash(git *)"
DISALLOWED_TOOLS = "WebFetch,WebSearch"
DEFAULTS: dict[str, Any] = {
    "tools": DEFAULT_TOOLS,
    "permission_mode": "acceptEdits",
    "max_turns": 20,
    "budget_usd": 1.0,
    "timeout_seconds": 600,
}
FORBIDDEN_MODES = ("bypassPermissions",)  # CLAUDE.md: never use bypass-permissions mode
CASE_KEYS = frozenset({"description", "setup", "checks", *DEFAULTS})
CHECK_KINDS = ("command", "file", "output", "denied")
CHECK_KEYS = {
    "command": frozenset({"command", "exit"}),
    "file": frozenset({"file", "exists", "contains", "not_contains", "unchanged", "equals"}),
    "output": frozenset({"output"}),
    "denied": frozenset({"denied"}),
}
OUTPUT_KEYS = frozenset({"contains", "not_contains", "regex"})
WORKSPACE_IGNORE = (".sdlc", "node_modules", "__pycache__", ".pytest_cache", ".venv")
FIXTURE_IGNORE = ("__pycache__", ".pytest_cache", ".ruff_cache", ".venv")
DETAIL_TAIL = 400  # characters of a failing command's output kept in the report


# --- cases ------------------------------------------------------------------------------------
@dataclass
class Case:
    name: str
    path: Path
    prompt: str = ""
    config: dict[str, Any] = field(default_factory=dict)
    error: str = ""  # why the case cannot run; a case with an error fails


def discover(cases_dir: Path, pattern: str | None = None) -> list[Path]:
    """The case folders, sorted by name; hidden folders are not cases."""
    found = [
        p
        for p in Path(cases_dir).iterdir()
        if p.is_dir() and not p.name.startswith(".") and p.name != "__pycache__"
    ]
    if pattern:
        found = [p for p in found if fnmatch.fnmatchcase(p.name, pattern)]
    return sorted(found, key=lambda p: p.name)


def load_case(path: Path) -> Case:
    path = Path(path)
    case = Case(name=path.name, path=path)
    prompt_file, checks_file = path / PROMPT_FILE, path / CHECKS_FILE
    missing = [f.name for f in (prompt_file, checks_file) if not f.is_file()]
    if missing:
        case.error = " and ".join(missing) + (" is" if len(missing) == 1 else " are") + " missing"
        return case
    case.prompt = prompt_file.read_text(encoding="utf-8-sig").strip()
    if not case.prompt:
        case.error = f"{PROMPT_FILE} is empty"
        return case
    try:
        data = yamlish.load_file(checks_file)
    except (OSError, ValueError) as exc:
        case.error = f"{CHECKS_FILE} cannot be read: {exc}"
        return case
    config, problems = validate_config(data)
    case.config = config
    if problems:
        case.error = f"{CHECKS_FILE}: " + "; ".join(problems)
    return case


def _is_text_list(value: Any) -> bool:
    if isinstance(value, str):
        return True
    return isinstance(value, list) and bool(value) and all(isinstance(v, str) for v in value)


def _texts(value: Any) -> list[str]:
    return [value] if isinstance(value, str) else list(value or [])


def _bad_relative(rel: Any) -> bool:
    """True unless ``rel`` is a relative path that stays inside its base folder."""
    if not isinstance(rel, str) or not rel.strip():
        return True
    text = rel.replace("\\", "/")
    if text.startswith("/") or re.match(r"^[A-Za-z]:", text):
        return True
    return ".." in text.split("/")


def _positive_number(value: Any, integer: bool = False) -> bool:
    if isinstance(value, bool) or not isinstance(value, int if integer else (int, float)):
        return False
    return value > 0


def validate_config(data: Any) -> tuple[dict[str, Any], list[str]]:
    """(the configuration with the defaults filled in, the problems). Any problem fails the
    case before a run starts, so a mistyped check never costs a run or passes by omission."""
    if not isinstance(data, dict):
        return {}, [f"{CHECKS_FILE} is not a mapping"]
    problems: list[str] = []
    unknown = sorted(set(data) - CASE_KEYS)
    if unknown:
        problems.append("unknown key(s): " + ", ".join(unknown))
    config = {**DEFAULTS, **{k: v for k, v in data.items() if v is not None}}
    setup = config.get("setup")
    if setup is not None and not _is_text_list(setup):
        problems.append("setup must be a command or a list of commands")
    if not isinstance(config["tools"], str) or not config["tools"].strip():
        problems.append("tools must be a comma-separated list of tool rules")
    mode = config["permission_mode"]
    if not isinstance(mode, str) or not mode.strip():
        problems.append("permission_mode must be a string")
    elif mode in FORBIDDEN_MODES:
        problems.append(f"permission_mode {mode} is never allowed (CLAUDE.md)")
    if not _positive_number(config["max_turns"], integer=True):
        problems.append("max_turns must be a positive integer")
    if not _positive_number(config["budget_usd"]):
        problems.append("budget_usd must be a positive number")
    if not _positive_number(config["timeout_seconds"]):
        problems.append("timeout_seconds must be a positive number")
    checks = data.get("checks")
    if not isinstance(checks, list) or not checks:
        problems.append("checks must be a non-empty list")
    else:
        for index, check in enumerate(checks, start=1):
            problems += validate_check(index, check)
    return config, problems


def check_kind(check: Mapping[str, Any]) -> str | None:
    kinds = [k for k in CHECK_KINDS if k in check]
    return kinds[0] if len(kinds) == 1 else None


def validate_check(index: int, check: Any) -> list[str]:
    where = f"check {index}"
    if not isinstance(check, dict):
        return [f"{where} is not a mapping"]
    kind = check_kind(check)
    if kind is None:
        return [f"{where} needs exactly one of {', '.join(CHECK_KINDS)}"]
    where = f"check {index} ({kind})"
    problems = []
    unknown = sorted(set(check) - CHECK_KEYS[kind])
    if unknown:
        problems.append(f"{where}: unknown key(s): " + ", ".join(unknown))
    if kind == "command":
        if not isinstance(check["command"], str) or not check["command"].strip():
            problems.append(f"{where}: command must be a string")
        exit_code = check.get("exit", 0)
        if isinstance(exit_code, bool) or not isinstance(exit_code, int):
            problems.append(f"{where}: exit must be an integer")
    elif kind == "file":
        if _bad_relative(check["file"]):
            problems.append(f"{where}: file must be a path inside the workspace")
        for key in ("exists", "unchanged"):
            if key in check and not isinstance(check[key], bool):
                problems.append(f"{where}: {key} must be true or false")
        for key in ("contains", "not_contains"):
            if key in check and not _is_text_list(check[key]):
                problems.append(f"{where}: {key} must be a string or a list of strings")
        if "equals" in check and _bad_relative(check["equals"]):
            problems.append(f"{where}: equals must be a path inside the case folder")
    elif kind == "output":
        spec = check["output"]
        if not isinstance(spec, dict) or not spec:
            problems.append(f"{where}: output must map contains, not_contains or regex")
        else:
            extra = sorted(set(spec) - OUTPUT_KEYS)
            if extra:
                problems.append(f"{where}: unknown key(s): " + ", ".join(extra))
            for key in ("contains", "not_contains"):
                if key in spec and not _is_text_list(spec[key]):
                    problems.append(f"{where}: {key} must be a string or a list of strings")
            if "regex" in spec:
                try:
                    re.compile(str(spec["regex"]))
                except re.error as exc:
                    problems.append(f"{where}: regex does not compile: {exc}")
    elif not isinstance(check["denied"], str) or not check["denied"].strip():
        problems.append(f"{where}: denied must name a tool")
    return problems


# --- processes --------------------------------------------------------------------------------
def _kill_tree(proc: subprocess.Popen) -> None:
    """Kill the process and everything it started (a ``claude`` run spawns tools)."""
    try:
        if os.name == "nt":
            subprocess.run(
                ["taskkill", "/F", "/T", "/PID", str(proc.pid)], capture_output=True, check=False
            )
        else:
            os.killpg(proc.pid, signal.SIGKILL)
    except (OSError, ProcessLookupError):
        pass
    with contextlib.suppress(OSError):
        proc.kill()


def run_bounded(
    argv: list[str], cwd: Path, timeout: float, env: Mapping[str, str] | None = None
) -> tuple[int, str, str]:
    """(exit code, stdout, stderr); raises ``subprocess.TimeoutExpired`` after killing the
    whole process tree when the wall clock runs out."""
    kwargs: dict[str, Any] = {}
    if os.name == "nt":
        kwargs["creationflags"] = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
    else:
        kwargs["start_new_session"] = True
    with subprocess.Popen(
        argv,
        cwd=str(cwd),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=dict(env) if env is not None else None,
        **kwargs,
    ) as proc:
        try:
            out, err = proc.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            _kill_tree(proc)
            with contextlib.suppress(subprocess.TimeoutExpired, OSError, ValueError):
                proc.communicate(timeout=10)
            raise
    return proc.returncode, out or "", err or ""


def _exe(name: str) -> str:
    found = shutil.which(name)
    if found:
        return found
    if name in ("python", "python3"):
        return sys.executable
    return name


def _tail(text: str) -> str:
    text = text.strip()
    return text if len(text) <= DETAIL_TAIL else "..." + text[-DETAIL_TAIL:]


def run_commands(command: str, cwd: Path, timeout: float) -> tuple[int, str]:
    """Run a command chain without a shell; (exit code of the first failing step or 0, what
    happened)."""
    try:
        chain = command_chain(command, cwd)
    except UsageError as exc:
        return 2, str(exc)
    for argv in chain:
        try:
            code, out, err = run_bounded([_exe(argv[0]), *argv[1:]], cwd, timeout)
        except subprocess.TimeoutExpired:
            return 124, f"{argv[0]}: timed out after {timeout:g}s"
        except FileNotFoundError:
            return 127, f"{argv[0]}: not found"
        except OSError as exc:
            return 126, f"{argv[0]}: {exc}"
        if code != 0:
            output = _tail(err + "\n" + out)
            return code, f"{argv[0]} exited {code}" + (f": {output}" if output else "")
    return 0, "ok"


# --- the headless run ---------------------------------------------------------------------------
def claude_prefix(claude: str) -> list[str]:
    """``--claude`` as an argv prefix: a ``.py`` file runs through this interpreter (the
    tests' fake), anything else is resolved on PATH (``.cmd`` shims on Windows)."""
    if claude.lower().endswith(".py"):
        return [sys.executable, claude]
    return [shutil.which(claude) or claude]


def compose(
    claude: str,
    prompt: str,
    config: Mapping[str, Any],
    plugin_dir: Path,
    env: Mapping[str, str],
) -> list[str]:
    """The argv of one case's run. The prompt goes right after ``-p``: ``--allowedTools``
    and ``--disallowedTools`` take several values, so a prompt placed after them would be
    read as one more tool name (plugin/ci/run_phase.py, observed live)."""
    argv = [*claude_prefix(claude), "-p", prompt, "--output-format", "json"]
    argv += ["--permission-prompts", "none"]
    argv += ["--permission-mode", str(config["permission_mode"])]
    argv += ["--max-turns", str(config["max_turns"])]
    argv += ["--max-budget-usd", str(config["budget_usd"])]
    argv += ["--allowedTools", str(config["tools"])]
    argv += ["--disallowedTools", DISALLOWED_TOOLS]
    argv += ["--plugin-dir", str(plugin_dir)]
    model = env.get("SDLC_MODEL")
    if model:
        argv += ["--model", model]
    return argv


def parse_result(stdout: str) -> dict[str, Any] | None:
    """The result object of ``--output-format json``; None when there is none. A list of
    messages (the verbose shape) yields its last ``result`` message."""
    text = stdout.strip()
    if not text:
        return None
    candidates: list[Any] = []
    try:
        candidates.append(json.loads(text))
    except ValueError:
        for line in reversed(text.splitlines()):
            try:
                candidates.append(json.loads(line))
                break
            except ValueError:
                continue
    for data in candidates:
        if isinstance(data, list):
            results = [m for m in data if isinstance(m, dict) and m.get("type") == "result"]
            data = results[-1] if results else None
        if isinstance(data, dict):
            return data
    return None


def run_failure(data: Mapping[str, Any]) -> str:
    """Why the run did not succeed; "" when it did."""
    subtype = data.get("subtype")
    if data.get("is_error"):
        return f"the run ended in an error ({subtype or 'is_error'})"
    if subtype not in (None, "success"):
        return f"the run did not succeed ({subtype})"
    return ""


def denials(data: Mapping[str, Any]) -> list[str]:
    """The tool names of ``permission_denials`` (absent on older results: none)."""
    out = []
    for entry in data.get("permission_denials") or []:
        if isinstance(entry, dict):
            out.append(str(entry.get("tool_name") or ""))
        elif isinstance(entry, str):
            out.append(entry)
    return [name for name in out if name]


# --- checks -----------------------------------------------------------------------------------
def _outcome(kind: str, passed: bool, detail: str) -> dict[str, Any]:
    return {"kind": kind, "passed": bool(passed), "detail": detail}


def _read(path: Path) -> bytes | None:
    try:
        return path.read_bytes() if path.is_file() else None
    except OSError:
        return None


def snapshot(
    case: Case, workspace: Path
) -> tuple[dict[str, bytes | None], dict[str, bytes | None]]:
    """(the workspace files ``unchanged`` compares, the ``expected/`` files ``equals`` compares),
    both read before the agent runs."""
    before: dict[str, bytes | None] = {}
    expected: dict[str, bytes | None] = {}
    for check in case.config.get("checks") or []:
        if check_kind(check) != "file":
            continue
        if check.get("unchanged"):
            before[check["file"]] = _read(workspace / check["file"])
        if "equals" in check:
            expected[check["equals"]] = _read(case.path / check["equals"])
    return before, expected


def _text_checks(text: str, contains: Any, not_contains: Any) -> list[str]:
    failures = [f"missing {t!r}" for t in _texts(contains) if t not in text]
    failures += [f"contains {t!r}" for t in _texts(not_contains) if t in text]
    return failures


def check_file(
    check: Mapping[str, Any],
    workspace: Path,
    before: Mapping[str, bytes | None],
    expected: Mapping[str, bytes | None],
) -> dict[str, Any]:
    rel = check["file"]
    data = _read(workspace / rel)
    present = data is not None
    # ``exists`` omitted: required unless the check only asserts what must be absent
    # (not_contains) or compares with the snapshot (unchanged); an absent file then passes.
    needs = "contains" in check or "equals" in check
    only_absence = not needs and ("not_contains" in check or "unchanged" in check)
    exists = check.get("exists", None if only_absence else True)
    if exists is True and not present:
        return _outcome("file", False, f"{rel}: does not exist")
    if exists is False:
        return _outcome("file", not present, f"{rel}: " + ("exists" if present else "absent"))
    failures: list[str] = []
    if present and ("contains" in check or "not_contains" in check):
        text = data.decode("utf-8", errors="replace")
        failures += _text_checks(text, check.get("contains"), check.get("not_contains"))
    if check.get("unchanged") and data != before.get(rel):
        failures.append("changed by the run")
    if "equals" in check:
        want = expected.get(check["equals"])
        if want is None:
            failures.append(f"{check['equals']} is missing from the case folder")
        elif data != want:
            failures.append(f"differs from {check['equals']}")
    if failures:
        return _outcome("file", False, f"{rel}: " + "; ".join(failures))
    return _outcome("file", True, f"{rel}: " + ("ok" if present else "absent"))


def check_output(check: Mapping[str, Any], result_text: str) -> dict[str, Any]:
    spec = check["output"]
    failures = _text_checks(result_text, spec.get("contains"), spec.get("not_contains"))
    if "regex" in spec and not re.search(str(spec["regex"]), result_text):
        failures.append(f"no match for /{spec['regex']}/")
    return _outcome("output", not failures, "; ".join(failures) or "ok")


def check_denied(check: Mapping[str, Any], denied: list[str]) -> dict[str, Any]:
    want = check["denied"]
    hit = [name for name in denied if name == want or fnmatch.fnmatchcase(name, want)]
    if hit:
        return _outcome("denied", True, f"{want} was denied")
    seen = ", ".join(denied) or "none"
    return _outcome("denied", False, f"no {want} denial (denials: {seen})")


def evaluate(
    check: Mapping[str, Any],
    *,
    workspace: Path,
    result: Mapping[str, Any],
    before: Mapping[str, bytes | None],
    expected: Mapping[str, bytes | None],
    timeout: float,
) -> dict[str, Any]:
    kind = check_kind(check)
    if kind == "command":
        want = check.get("exit", 0)
        code, detail = run_commands(check["command"], workspace, timeout)
        text = f"{check['command']!r} exited {code}"
        if code != want:
            return _outcome("command", False, f"{text}, expected {want}: {detail}")
        return _outcome("command", True, text)
    if kind == "file":
        return check_file(check, workspace, before, expected)
    if kind == "output":
        return check_output(check, str(result.get("result") or ""))
    return check_denied(check, denials(result))


# --- one case ---------------------------------------------------------------------------------
def _force_remove(func, path, _exc) -> None:
    """rmtree's error handler: git marks its objects read-only, which Windows refuses to
    delete."""
    with contextlib.suppress(OSError):
        os.chmod(path, stat.S_IWRITE)
        func(path)


def remove_tree(path: Path) -> None:
    with contextlib.suppress(OSError):
        if sys.version_info >= (3, 12):
            shutil.rmtree(path, onexc=_force_remove)
        else:
            shutil.rmtree(path, onerror=_force_remove)


def run_case(
    case: Case,
    *,
    root: Path,
    plugin_dir: Path,
    claude: str,
    env: Mapping[str, str],
    keep: bool = False,
) -> dict[str, Any]:
    started = time.monotonic()
    res: dict[str, Any] = {
        "name": case.name,
        "passed": False,
        "reason": "",
        "checks": [],
        "cost_usd": 0.0,
        "turns": 0,
        "subtype": None,
        "seconds": 0.0,
    }
    if case.error:
        res["reason"] = case.error
        return res
    config = case.config
    timeout = float(config["timeout_seconds"])
    tmp = Path(tempfile.mkdtemp(prefix="sdlc-eval-"))
    workspace = tmp / "project"
    try:
        shutil.copytree(root, workspace, ignore=shutil.ignore_patterns(*WORKSPACE_IGNORE))
        for command in _texts(config.get("setup")):
            code, detail = run_commands(command, workspace, timeout)
            if code != 0:
                res["reason"] = f"setup failed: {detail}"
                return res
        before, expected = snapshot(case, workspace)
        argv = compose(claude, case.prompt, config, plugin_dir, env)
        result: dict[str, Any] = {}
        try:
            code, out, err = run_bounded(argv, workspace, timeout, env)
        except subprocess.TimeoutExpired:
            reason = f"timed out after {timeout:g}s"
        except OSError as exc:
            reason = f"{argv[0]} could not start: {exc}"
        else:
            parsed = parse_result(out)
            if parsed is None:
                reason = f"unparsable claude output (exit {code})"
                if _tail(err):
                    reason += f": {_tail(err)}"
            else:
                result = parsed
                reason = run_failure(result)
        res["subtype"] = result.get("subtype")
        res["turns"] = result.get("num_turns") or 0
        res["cost_usd"] = float(result.get("total_cost_usd") or 0.0)
        checks = [
            evaluate(
                check,
                workspace=workspace,
                result=result,
                before=before,
                expected=expected,
                timeout=timeout,
            )
            for check in config["checks"]
        ]
        res["checks"] = checks
        failed = next(((i, c) for i, c in enumerate(checks, 1) if not c["passed"]), None)
        if not reason and failed:
            index, check = failed
            reason = f"check {index} ({check['kind']}) failed: {check['detail']}"
        res["reason"] = reason
        res["passed"] = not reason
        return res
    finally:
        if keep:
            res["workspace"] = str(workspace)
        else:
            remove_tree(tmp)
        res["seconds"] = round(time.monotonic() - started, 1)


# --- the fixture project ------------------------------------------------------------------------
def build_fixture(source: Path = FIXTURE) -> Path:
    """The sample project as a git repository with ``/sdlc-init`` applied (profile standard),
    in a temporary folder: the project the framework-level suite runs against."""
    from init import sdlc_init  # noqa: PLC0415 - only the fixture needs it

    root = Path(tempfile.mkdtemp(prefix="sdlc-eval-fixture-")) / source.name
    shutil.copytree(source, root, ignore=shutil.ignore_patterns(*FIXTURE_IGNORE))
    gitops.run(root, "init", "-q", "-b", "main")
    gitops.run(root, "config", "user.name", "sdlc-evals")
    gitops.run(root, "config", "user.email", "sdlc-evals@example.com")
    gitops.run(root, "config", "commit.gpgsign", "false")
    gitops.run(root, "add", "-A")
    gitops.run(root, "commit", "-q", "-m", "The sample project")
    with contextlib.redirect_stdout(io.StringIO()):
        code = sdlc_init.main(["--root", str(root), "--profile", "standard"])
    if code != 0:
        raise RuntimeError(f"/sdlc-init failed on the fixture (exit {code})")
    gitops.run(root, "add", "-A")
    gitops.run(root, "commit", "-q", "-m", "Install the SDLC framework")
    return root


# --- the report ---------------------------------------------------------------------------------
def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def build_report(root: str, results: list[dict[str, Any]], min_pass_rate: float) -> dict:
    total = len(results)
    passed = sum(1 for r in results if r["passed"])
    pass_rate = round(passed / total, 4) if total else 1.0
    report = {
        "schema_version": SCHEMA_VERSION,
        "at": now_iso(),
        "root": root,
        "cases": results,
        "passed": passed,
        "total": total,
        "pass_rate": pass_rate,
        "min_pass_rate": min_pass_rate,
        "ok": pass_rate >= min_pass_rate,
        "total_cost_usd": round(sum(float(r.get("cost_usd") or 0) for r in results), 6),
    }
    if not total:
        report["note"] = "no cases"
    return report


def _cell(text: Any, limit: int = 120) -> str:
    value = " ".join(str(text).split()).replace("|", "\\|")
    return value if len(value) <= limit else value[: limit - 3] + "..."


def markdown(report: Mapping[str, Any]) -> str:
    lines = [
        "| case | result | turns | cost (USD) | first failure |",
        "| --- | --- | --- | --- | --- |",
    ]
    for r in report["cases"]:
        lines.append(
            f"| {_cell(r['name'])} | {'pass' if r['passed'] else 'FAIL'} | {r['turns']} "
            f"| {float(r['cost_usd']):.4f} | {_cell(r['reason']) or '-'} |"
        )
    if not report["cases"]:
        lines.append("| (no cases) | - | - | - | - |")
    verdict = "ok" if report["ok"] else "below the minimum"
    lines += [
        "",
        f"pass rate {report['passed']}/{report['total']} = {report['pass_rate']:g} "
        f"(minimum {report['min_pass_rate']:g}): {verdict}; "
        f"total cost {report['total_cost_usd']:.4f} USD",
    ]
    return "\n".join(lines)


def github_output(report: Mapping[str, Any], env: Mapping[str, str]) -> None:
    target = env.get("GITHUB_OUTPUT")
    if not target:
        return
    with open(target, "a", encoding="utf-8", newline="\n") as fh:
        fh.write(f"pass_rate={report['pass_rate']}\n")
        fh.write(f"passed={report['passed']}\n")
        fh.write(f"total={report['total']}\n")
        fh.write(f"ok={'true' if report['ok'] else 'false'}\n")


# --- the command line ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="run.py",
        description="Run an agent eval suite (build guide step 35).",
    )
    p.add_argument("--root", default=None, help="the project the cases run against")
    p.add_argument("--cases", default=None, help="the cases folder (default <root>/evals/cases)")
    p.add_argument("--case", default=None, help="only the cases whose folder name matches")
    p.add_argument("--plugin-dir", default=None, help="the framework root (default: this one)")
    p.add_argument("--claude", default="claude")
    p.add_argument("--report", default=DEFAULT_REPORT)
    p.add_argument("--min-pass-rate", type=float, default=1.0)
    p.add_argument("--fixture", action="store_true", help="run against the sample project")
    p.add_argument("--keep", action="store_true", help="keep the workspaces")
    p.add_argument("--dry-run", action="store_true", help="list the cases; run nothing")
    return p


def _usage(message: str) -> int:
    print(f"run.py: {message}", file=sys.stderr)
    return 2


def main(argv: list[str] | None = None, env: Mapping[str, str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    env = os.environ if env is None else env
    if args.fixture and args.root:
        return _usage("--fixture builds the project: give --fixture or --root, not both")
    if not args.fixture and not args.root:
        return _usage("--root is required (or --fixture for the framework-level suite)")
    if not 0.0 <= args.min_pass_rate <= 1.0:
        return _usage("--min-pass-rate must be between 0 and 1")
    root = None if args.fixture else Path(args.root).resolve()
    if root is not None and not root.is_dir():
        return _usage(f"--root {root} is not a folder")
    plugin_dir = Path(args.plugin_dir).resolve() if args.plugin_dir else FRAMEWORK_DIR
    if args.cases:
        cases_dir = Path(args.cases).resolve()
    elif args.fixture:
        cases_dir = FRAMEWORK_CASES
    else:
        cases_dir = root / "evals" / "cases"
    if not cases_dir.is_dir():
        return _usage(f"no cases folder at {cases_dir}")
    cases = [load_case(p) for p in discover(cases_dir, args.case)]

    if args.dry_run:
        shown_root = str(root) if root else f"a /sdlc-init copy of {FIXTURE}"
        print(f"dry run: {len(cases)} case(s) in {cases_dir}; root {shown_root}")
        for case in cases:
            if case.error:
                print(f"- {case.name}: cannot run: {case.error}")
                continue
            description = case.config.get("description") or ""
            print(f"- {case.name}" + (f": {description}" if description else ""))
            argv_ = compose(args.claude, case.prompt, case.config, plugin_dir, env)
            print("  argv: " + json.dumps(argv_))
        if not cases:
            print("no cases")
        return 0

    fixture_root = None
    if args.fixture:
        try:
            fixture_root = build_fixture()
        except Exception as exc:  # noqa: BLE001 - a broken fixture is a usage problem here
            return _usage(f"the fixture project could not be built: {exc}")
        root = fixture_root
    try:
        results = [
            run_case(
                case, root=root, plugin_dir=plugin_dir, claude=args.claude, env=env, keep=args.keep
            )
            for case in cases
        ]
    finally:
        if fixture_root is not None and not args.keep:
            remove_tree(fixture_root.parent)
    report = build_report(str(root), results, args.min_pass_rate)
    report_path = Path(args.report).resolve()
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(markdown(report))
    if not cases:
        print("no cases")
    print(f"report: {report_path}")
    github_output(report, env)
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
