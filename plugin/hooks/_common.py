"""Shared plumbing for the Python hooks (build guide step 15; decision 7).

Facts this relies on, from the Claude Code hooks reference (docs/NOTES.md has the quotes):
  - the hook receives one JSON object on stdin with ``hook_event_name``, ``tool_name``,
    ``tool_input``, ``cwd`` (and more);
  - ``tool_input.file_path`` is always absolute and uses the platform's separators
    (backslashes on Windows), so we normalise before comparing;
  - exit code 2 blocks the action and cannot be overridden by JSON; exit 1 is a
    *non-blocking* error, so a policy hook must never fail with 1 — we fail closed with 2;
  - a PreToolUse hook may also print ``hookSpecificOutput.permissionDecision`` JSON, which
    we do in addition so the reason reaches Claude either way.
"""

from __future__ import annotations

import json
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
if str(PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(PLUGIN_ROOT))

from state import yamlish  # noqa: E402

FILE_TOOLS = ("Edit", "Write", "MultiEdit", "NotebookEdit")
SDLC_FILE = "sdlc.yaml"


@dataclass
class Decision:
    block: bool
    reason: str = ""
    extra: dict[str, Any] | None = None  # extra JSON fields (PostToolUse feedback etc.)

    @staticmethod
    def allow() -> Decision:
        return Decision(False)

    @staticmethod
    def deny(reason: str) -> Decision:
        return Decision(True, reason)


def read_payload(stream=None) -> dict[str, Any]:
    raw = (stream or sys.stdin).read()
    data = json.loads(raw) if raw.strip() else {}
    if not isinstance(data, dict):
        raise ValueError("hook input is not a JSON object")
    return data


def norm(path: str | os.PathLike[str]) -> str:
    """Forward slashes, no trailing slash; Windows drive letters lower-cased."""
    s = str(path).replace("\\", "/")
    if len(s) >= 2 and s[1] == ":":
        s = s[0].lower() + s[1:]
    return s.rstrip("/") if len(s) > 1 else s


def project_dir(payload: dict[str, Any], env: dict[str, str] | None = None) -> str:
    env = os.environ if env is None else env
    return norm(env.get("CLAUDE_PROJECT_DIR") or payload.get("cwd") or os.getcwd())


def rel_to(root: str, path: str) -> str | None:
    """Path relative to root (posix), or None when the path is outside root."""
    root_n, path_n = norm(root), norm(path)
    if path_n == root_n:
        return ""
    if path_n.startswith(root_n + "/"):
        return path_n[len(root_n) + 1 :]
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


def load_sdlc_config(root: str) -> dict[str, Any]:
    path = Path(root) / SDLC_FILE
    if not path.is_file():
        return {}
    try:
        data = yamlish.load_file(path)
    except Exception:  # a broken config must not switch a guardrail off
        return {}
    return data if isinstance(data, dict) else {}


# --- glob matching, gitignore-style ------------------------------------------------------
def glob_to_regex(pattern: str) -> re.Pattern[str]:
    p = pattern.strip().replace("\\", "/")
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
        else:
            out += re.escape(ch)
        i += 1
    prefix = "^" if anchored else "^(?:.*/)?"
    return re.compile(prefix + out + "(?:/.*)?$")


def matches(pattern: str, rel_path: str) -> bool:
    return bool(glob_to_regex(pattern).match(PurePosixPath(rel_path).as_posix()))


# --- output --------------------------------------------------------------------------------
def emit(decision: Decision, event: str, out=None, err=None) -> int:
    """Print the hook's JSON (and reason on stderr) and return the exit code."""
    out = out or sys.stdout
    err = err or sys.stderr
    if event == "PreToolUse":
        if decision.block:
            payload = {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": decision.reason,
                }
            }
            out.write(json.dumps(payload))
            err.write(decision.reason)
            return 2
        return 0
    # PostToolUse and others: block == "feed the reason back to Claude"
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
            sys.stdout.write(
                json.dumps(
                    {
                        "hookSpecificOutput": {
                            "hookEventName": "PreToolUse",
                            "permissionDecision": "deny",
                            "permissionDecisionReason": reason,
                        }
                    }
                )
            )
            sys.stderr.write(reason)
            return 2
        sys.stderr.write(f"{decide.__module__} hook error (ignored): {exc!r}")
        return 0
