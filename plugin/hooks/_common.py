"""Shared plumbing for the Python hooks (build guide step 15; decision 7).

Facts this relies on, from the Claude Code hooks reference (docs/NOTES.md has the quotes):
  - the hook receives one JSON object on stdin with ``hook_event_name``, ``tool_name``,
    ``tool_input``, ``cwd`` (and more);
  - ``tool_input.file_path`` is absolute and uses the platform's separators (backslashes on
    Windows); we still normalise ``..``, ``//``, case and symlinks ourselves so a spelling
    difference cannot slip past a comparison;
  - exit code 2 blocks the action and cannot be overridden by JSON; exit 1 is a
    *non-blocking* error, so a policy hook must never fail with 1 — we fail closed with 2;
  - a PreToolUse hook may also print ``hookSpecificOutput.permissionDecision`` JSON, which
    we do in addition so the reason reaches Claude either way; PostToolUse feedback uses the
    top-level ``decision: "block"`` + ``reason`` fields (decision-control table).
"""

from __future__ import annotations

import json
import os
import posixpath
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

PLUGIN_ROOT = Path(__file__).resolve().parent.parent  # <repo>/plugin
if str(PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(PLUGIN_ROOT))

from state import yamlish  # noqa: E402

FILE_TOOLS = ("Edit", "Write", "MultiEdit", "NotebookEdit")
SDLC_FILE = "sdlc.yaml"


@dataclass
class Decision:
    block: bool
    reason: str = ""
    extra: dict[str, Any] | None = None

    @staticmethod
    def allow() -> Decision:
        return Decision(False)

    @staticmethod
    def deny(reason: str) -> Decision:
        return Decision(True, reason)


def read_payload(stream=None) -> dict[str, Any]:
    raw = (stream or sys.stdin).read()
    if not raw.strip():
        raise ValueError("hook received no input")
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise ValueError("hook input is not a JSON object")
    return data


# --- paths ---------------------------------------------------------------------------------
def norm(path: str | os.PathLike[str]) -> str:
    """Comparison form: forward slashes, ``..``/``.``/``//`` collapsed, no trailing slash or
    whitespace, lower-cased (Windows and macOS paths are case-insensitive; on Linux a
    same-spelled file in another case is blocked too, which is the safe direction)."""
    s = str(path).strip().replace("\\", "/")
    if s.startswith("//") and not s.startswith("///"):  # UNC: keep the leading //
        s = "//" + posixpath.normpath(s[2:])
    else:
        s = posixpath.normpath(s)
    if len(s) >= 2 and s[1] == ":":
        s = s[0].lower() + s[1:]
    return s.lower()


def real(path: str) -> str:
    """norm() of the symlink-resolved path (falls back to norm(path) when it does not exist)."""
    try:
        return norm(os.path.realpath(path))
    except OSError:
        return norm(path)


def project_dir(payload: dict[str, Any], env: dict[str, str] | None = None) -> str:
    """CLAUDE_PROJECT_DIR (exported to hook processes), else the nearest ancestor of cwd that
    holds sdlc.yaml or .git, else cwd."""
    env = os.environ if env is None else env
    if env.get("CLAUDE_PROJECT_DIR"):
        return norm(env["CLAUDE_PROJECT_DIR"])
    cwd = str(payload.get("cwd") or os.getcwd())
    p = Path(cwd)
    for candidate in (p, *p.parents):
        if (candidate / SDLC_FILE).is_file() or (candidate / ".git").exists():
            return norm(candidate)
    return norm(cwd)


def rel_to(root: str, path: str) -> str | None:
    """Path relative to root (posix, normalised), or None when the path is outside root."""
    root_n, path_n = norm(root), norm(path)
    if path_n == root_n:
        return ""
    if path_n.startswith(root_n.rstrip("/") + "/"):
        return path_n[len(root_n.rstrip("/")) + 1 :]
    return None


def target_paths(tool_input: dict[str, Any]) -> list[str]:
    paths = []
    for key in ("file_path", "notebook_path"):
        if tool_input.get(key):
            paths.append(str(tool_input[key]))
    return paths


def new_texts(tool_input: dict[str, Any]) -> list[str]:
    """Every piece of text an edit/write would put into a file."""
    texts = []
    for key in ("content", "new_string", "new_source"):
        if isinstance(tool_input.get(key), str):
            texts.append(tool_input[key])
    for edit in tool_input.get("edits") or []:
        if isinstance(edit, dict) and isinstance(edit.get("new_string"), str):
            texts.append(edit["new_string"])
    return texts


class ConfigError(RuntimeError):
    pass


def load_sdlc_config(root: str) -> dict[str, Any]:
    """The project's sdlc.yaml as a dict; {} when absent. Raises ConfigError when the file
    exists but cannot be read, so a policy hook can fail closed instead of silently losing
    the owner's protected list."""
    path = Path(root) / SDLC_FILE
    if not path.is_file():
        return {}
    try:
        data = yamlish.load_file(path)
    except Exception as exc:  # noqa: BLE001
        raise ConfigError(f"{SDLC_FILE} could not be read: {exc}") from exc
    if not isinstance(data, dict):
        raise ConfigError(f"{SDLC_FILE} is not a mapping")
    return data


# --- glob matching, gitignore-style (case-insensitive, like norm()) -------------------------
def glob_to_regex(pattern: str) -> re.Pattern[str]:
    p = pattern.strip().replace("\\", "/")
    if p.startswith("./"):
        p = p[2:]
    anchored = "/" in p.rstrip("/")
    p = p.strip("/")
    out = ""
    i = 0
    while i < len(p):
        ch = p[i]
        if p.startswith("**/", i):
            out += "(?:.*/)?"
            i += 3
            continue
        if p.startswith("**", i):
            out += ".*"
            i += 2
            continue
        if ch == "*":
            out += "[^/]*"
        elif ch == "?":
            out += "[^/]"
        elif ch == "[":
            j = p.find("]", i + 1)
            if j == -1:
                out += re.escape(ch)
            else:
                out += "[" + p[i + 1 : j].replace("\\", "\\\\") + "]"
                i = j + 1
                continue
        else:
            out += re.escape(ch)
        i += 1
    prefix = "^" if anchored else "^(?:.*/)?"
    return re.compile(prefix + out + "(?:/.*)?$", re.IGNORECASE)


def matches(pattern: str, rel_path: str) -> bool:
    return bool(glob_to_regex(pattern).match(rel_path.replace("\\", "/")))


# --- output --------------------------------------------------------------------------------
def _deny_json(reason: str) -> str:
    return json.dumps(
        {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": reason,
            }
        }
    )


def emit(decision: Decision, event: str, out=None, err=None) -> int:
    """Print the hook's JSON (and reason on stderr) and return the exit code."""
    out = out or sys.stdout
    err = err or sys.stderr
    if event == "PreToolUse":
        if decision.block:
            out.write(_deny_json(decision.reason))
            err.write(decision.reason)
            return 2
        return 0
    if decision.block or decision.extra:
        payload: dict[str, Any] = {}
        if decision.block:
            payload.update({"decision": "block", "reason": decision.reason})
        if decision.extra:
            payload.update(decision.extra)
        out.write(json.dumps(payload))
    return 0


def run_hook(decide, event: str, argv: list[str] | None = None) -> int:
    """Standard main: read stdin, decide, emit. Any exception => fail closed (exit 2) for
    PreToolUse, fail open (exit 0 with a note on stderr) for PostToolUse."""
    try:
        payload = read_payload()
        decision = decide(payload, argv or [])
        return emit(decision, event)
    except Exception as exc:  # noqa: BLE001
        if event == "PreToolUse":
            reason = f"{decide.__module__} hook failed closed: {exc!r}"
            sys.stdout.write(_deny_json(reason))
            sys.stderr.write(reason)
            return 2
        sys.stderr.write(f"{decide.__module__} hook error (ignored): {exc!r}")
        return 0
