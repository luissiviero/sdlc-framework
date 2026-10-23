"""PostToolUse hook: run the formatter and linter on the file that changed (build guide
step 15 (2); article p.23 'Run the formatter and linter after file edits so drift never
accumulates' and 'build-phase hooks should be fast and scoped to the file that changed').

R33 (plugin 1.0.29): the project names its commands per file type in ``sdlc.yaml:
hooks.formatters``, a list of ``{glob, fix, check}`` entries; the first entry whose glob (a
gitignore glob, or a list of them) matches the file's project-relative path wins. Its ``fix``
commands run in order on the file, then its ``check`` commands; ``{file}`` is the file's path
from the project root, quoted for the platform shell. A ``check`` exit 1 is fed back to Claude
as a PostToolUse ``decision: block`` + ``reason`` (the decision-control table lists
PostToolUse under 'Top-level decision'); a ``fix`` command's output is not.

With no matching entry, a ``.py`` or ``.pyi`` file gets ruff as before: ``ruff check --fix``
(may delete lines), then ``ruff format``, then ``ruff check`` to report what is left. Any other
file type with no entry is left alone. One behaviour, always on: the switch
``hooks.format_on_edit`` of earlier versions is no longer read (options.md, row "Formatter
on edit").

This hook fails open: a missing tool, any exit code but a check's 1, a broken configuration
or a timeout is reported on stderr and never blocks.

A hook runs outside the Bash tool's sandbox. A project command runs project code (an eslint
or prettier configuration, a module next to the file) that the session can write, so in a CI
session (``CI_SESSION_ENV``, set by ``run_phase.session_env``, or ``GITHUB_ACTIONS``) the
project's commands are not run, and the runner's lint target judges the change after the
session; the session could otherwise reach the network or write the pinned framework's own
hooks through them (the review of 1.0.29). Ruff runs isolated (``python -I``): a module the
session wrote in the project cannot stand in for it. The project's commands run without the
model credentials or the GitHub tokens in their environment (an eslint or prettier
configuration is code the session can write), each within ``STEP_TIMEOUT`` and all of them
within ``BUDGET``, under the handler's 60 seconds in hooks.json. Every command run, with its
exit code, is written to the hook's log line.
"""

from __future__ import annotations

import os
import re
import shlex
import shutil
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import (  # noqa: E402
    FILE_TOOLS,
    ConfigError,
    Decision,
    load_sdlc_config,
    matches,
    project_dir,
    rel_to,
    run_hook,
    target_paths,
)

PY_SUFFIXES = {".py", ".pyi"}
STEP_TIMEOUT = 25  # seconds per command; the handler's own timeout in hooks.json is 60
BUDGET = 50  # seconds for every command of one edit; the hook passes when it is spent
# never in a project command's environment (ci/auth.py CREDENTIAL_VARS, the GitHub tokens the
# session holds, the second opinion's key; run_phase.commands_env hides the same)
HIDDEN_ENV = (
    "ANTHROPIC_API_KEY", "CLAUDE_CODE_OAUTH_TOKEN", "GITHUB_TOKEN", "GH_TOKEN",
    "SDLC_WORKFLOW_TOKEN", "GEMINI_API_KEY",
)  # fmt: skip
# what cmd.exe expands even inside double quotes: a path holding one is not passed on Windows
CMD_UNSAFE = ('"', "%", "!")
# a CI session: gate.checks.COMMANDS_RUNNER_ENV, which run_phase.session_env sets on every run
CI_SESSION_ENV = "SDLC_GATE_COMMANDS"
CI_SKIPPED = (
    "formatter: the project's commands for {rel} are not run in a CI session (they would run "
    "session-writable code outside the sandbox); the lint target judges it after the session"
)
# what a missing tool prints on an exit 1 of its own (npx --no, a shell): not a finding
MISSING_TOOL = re.compile(
    r"npx canceled due to missing packages|could not determine executable to run|"
    r"command not found|is not recognized as an internal or external command|E404",
    re.IGNORECASE,
)


def ruff_command() -> list[str] | None:
    """Prefer `python -m ruff` (same interpreter as the hook), else `ruff` on PATH."""
    try:
        probe = subprocess.run(
            [sys.executable, "-I", "-m", "ruff", "--version"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if probe.returncode == 0:
            return [sys.executable, "-I", "-m", "ruff"]
    except (OSError, subprocess.TimeoutExpired):
        pass
    exe = shutil.which("ruff")
    return [exe] if exe else None


def format_file(path: Path, root: Path, run=subprocess.run, ran=None) -> tuple[bool, str]:
    """Returns (clean, message). clean=False means unfixable lint findings remain. ``ran``,
    when given, collects ``{command, exit_code}`` for the log line."""
    cmd = ruff_command()
    if cmd is None:
        return True, "ruff not installed; skipped formatter/lint"
    common = dict(cwd=str(root), capture_output=True, text=True, timeout=STEP_TIMEOUT)
    proc = None
    for step in (
        ["check", "--fix", "--quiet"],
        ["format"],
        ["check", "--output-format", "concise"],
    ):
        proc = run([*cmd, *step, str(path)], **common)
        if ran is not None:
            ran.append(
                {"command": " ".join(["ruff", *step, path.name]), "exit_code": proc.returncode}
            )
    if proc.returncode == 0:
        return True, ""
    if proc.returncode == 1:  # lint findings; 2 = ruff itself failed (config error etc.)
        return False, (proc.stdout or proc.stderr).strip()
    return True, f"ruff could not run: {(proc.stderr or proc.stdout).strip()}"


class FormatterConfigError(ValueError):
    """``hooks.formatters`` is not a list of ``{glob, fix, check}`` entries."""


def _strings(value, what: str) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, list) and all(isinstance(v, str) for v in value):
        return list(value)
    raise FormatterConfigError(f"hooks.formatters: {what} must be a string or a list of them")


def formatter_entries(config: dict) -> list[dict[str, list[str]]]:
    """``hooks.formatters`` as ``[{glob: [...], fix: [...], check: [...]}]``; raises
    ``FormatterConfigError`` on any other shape (the hook then fails open)."""
    hooks_cfg = config.get("hooks") if isinstance(config.get("hooks"), dict) else {}
    raw = hooks_cfg.get("formatters")
    if raw is None:
        return []
    if not isinstance(raw, list):
        raise FormatterConfigError("hooks.formatters must be a list")
    out = []
    for entry in raw:
        if not isinstance(entry, dict) or not entry.get("glob"):
            raise FormatterConfigError("hooks.formatters: every entry needs a glob")
        out.append(
            {
                "glob": _strings(entry.get("glob"), "glob"),
                "fix": _strings(entry.get("fix"), "fix"),
                "check": _strings(entry.get("check"), "check"),
            }
        )
    return out


def matching_entry(entries: list[dict[str, list[str]]], rel: str) -> dict | None:
    return next((e for e in entries if any(matches(g, rel) for g in e["glob"])), None)


def quote_path(rel: str, windows: bool | None = None) -> str | None:
    """``rel`` quoted for the platform shell: double quotes for cmd.exe, where they keep
    ``&``, ``|`` and spaces literal (None when the path holds a character cmd.exe expands
    even there), ``shlex.quote`` elsewhere."""
    windows = os.name == "nt" if windows is None else windows
    if windows:
        if any(ch in rel for ch in CMD_UNSAFE):
            return None
        return f'"{rel}"'
    return shlex.quote(rel)


def command_env(environ: dict[str, str] | None = None) -> dict[str, str]:
    """The environment of a project formatter command: this one, without ``HIDDEN_ENV`` or
    a git credential handed through the environment (``ci/app_token.strip_git_auth``)."""
    from ci import app_token  # noqa: PLC0415

    environ = dict(os.environ if environ is None else environ)
    return app_token.strip_git_auth({k: v for k, v in environ.items() if k not in HIDDEN_ENV})


def run_project_commands(
    entry: dict[str, list[str]], rel: str, root: Path, ran: list[dict], run_command=None
) -> tuple[bool, str]:
    """Run ``entry``'s fix then check commands on ``rel``. Returns (clean, message): clean
    False only for a check's exit 1, with its output; anything else is a note."""
    if run_command is None:
        from gate.checks import run_command  # noqa: PLC0415 - the gate's shell and tree kill
    # a path the tool would read as an option (`-x.ts`) is passed as `./-x.ts`
    quoted = quote_path(os.path.join(".", rel) if rel.startswith("-") else rel)
    if quoted is None:
        return True, f"formatter skipped: {rel} holds a character cmd.exe expands"
    env = command_env()
    start = time.monotonic()
    notes: list[str] = []
    for kind in ("fix", "check"):
        for template in entry[kind]:
            left = BUDGET - (time.monotonic() - start)
            if left <= 1:
                notes.append("formatter budget spent; the remaining commands were not run")
                return True, "\n".join(notes)
            command = template.replace("{file}", quoted)
            result = run_command(command, root, int(min(STEP_TIMEOUT, left)), env=env)
            code = result.get("exit_code")
            ran.append({"command": command, "exit_code": code})
            output = str(result.get("output") or "").strip()
            if kind == "check" and code == 1 and not MISSING_TOOL.search(output):
                return False, output
            if kind == "fix" and code == 1:
                continue  # a fixer's exit 1 (eslint --fix with findings left) is the check's
            if code != 0:
                why = "timed out or could not start" if code is None else f"exited {code}"
                notes.append(f"`{command}` {why}: {output[-500:]}")
    return True, "\n".join(notes)


def ci_session(environ: dict[str, str] | None = None) -> bool:
    environ = os.environ if environ is None else environ
    return bool(environ.get(CI_SESSION_ENV)) or environ.get("GITHUB_ACTIONS") == "true"


def decide(payload: dict, argv: list[str], env: dict[str, str] | None = None) -> Decision:
    if payload.get("tool_name") not in FILE_TOOLS:
        return Decision.allow()
    root = Path(project_dir(payload, env))
    try:
        config = load_sdlc_config(str(root))
    except ConfigError as exc:
        sys.stderr.write(str(exc))
        config = {}
    try:
        entries = formatter_entries(config)
    except FormatterConfigError as exc:
        sys.stderr.write(f"{exc}; only the ruff default applies")
        entries = []
    ran: list[dict] = []
    for path_s in target_paths(payload.get("tool_input") or {}):
        path = Path(path_s)
        if not path.is_file() or rel_to(str(root), path_s) is None:
            continue  # gone, or outside the project: not ours to format
        rel = os.path.relpath(path, root)
        entry = matching_entry(entries, rel.replace("\\", "/"))
        if entry is not None and ci_session(env):
            sys.stderr.write(CI_SKIPPED.format(rel=rel))
            continue
        if entry is not None:
            clean, message = run_project_commands(entry, rel, root, ran)
            tool = "the project's check"
        elif path.suffix.lower() in PY_SUFFIXES:
            clean, message = format_file(path, root, ran=ran)
            tool = "ruff"
        else:
            continue
        if not clean:
            return Decision(
                block=True,
                reason=(
                    f"{tool} reports remaining problems in {path.name} after auto-fix; fix "
                    f"them before moving on:\n{message}"
                ),
                log={"commands": ran},
            )
        if message:
            sys.stderr.write(message)
    return Decision(False, log={"commands": ran} if ran else None)


if __name__ == "__main__":
    sys.exit(run_hook(decide, "PostToolUse", sys.argv[1:]))
