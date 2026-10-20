"""What the second opinion reads (ROADMAP R8): built by the runner from git at one commit, so
the Claude session neither chooses nor sees it, and capped in size.

Left out, always: every ``.env*`` file and every path under a ``secrets`` folder (the deny
rules of ``settings.ci.json``), the change's ``evidence/`` folder (Claude's own verdicts,
the gate record and the panel's decisions: the second opinion is blind to them, as the
panel's two verdicts are to each other) and binary files. A line the secrets hook would
refuse (``hooks/secrets_check.find_secrets``) is replaced by a marker before anything is
sent. Only tracked content at the commit is read (``git show <sha>:<path>``), never the
working tree, so an untracked file or the session's cache folder never leaves the runner.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path, PurePosixPath
from typing import Any

PLUGIN_DIR = Path(__file__).resolve().parent.parent
if str(PLUGIN_DIR) not in sys.path:
    sys.path.insert(0, str(PLUGIN_DIR))

from gate.artifacts import planned_files  # noqa: E402
from hooks.secrets_check import find_secrets  # noqa: E402

DEFAULT_MAX_CHARS = 400_000  # about 100K tokens: the whole design, or a large build diff
GIT_TIMEOUT = 60
CHANGE_FILES = ("intent.md", "spec.md", "plan.md")
PROJECT_FILES = ("CLAUDE.md", "REVIEW.md")
WITHHELD = "[line withheld before sending: {what}]"


def run_git(root: Path, *args: str) -> tuple[bool, str]:
    try:
        proc = subprocess.run(
            ["git", "--no-replace-objects", *args],
            cwd=str(root),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=GIT_TIMEOUT,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return False, str(exc)
    return proc.returncode == 0, proc.stdout if proc.returncode == 0 else proc.stderr.strip()


def resolve(root: Path, rev: str) -> str | None:
    ok, out = run_git(root, "rev-parse", "--verify", "--quiet", f"{rev}^{{commit}}")
    return out.strip() if ok and out.strip() else None


def excluded(path: str, change_rel: str) -> str | None:
    """Why ``path`` is never sent, or None."""
    p = PurePosixPath(path.replace("\\", "/"))
    if p.name.lower().startswith(".env"):
        return ".env file"
    if any(part.lower() == "secrets" for part in p.parts[:-1]):
        return "under a secrets folder"
    if str(p).startswith(f"{change_rel}/evidence/"):
        return "the change's evidence (Claude's verdicts)"
    return None


def redact(text: str) -> tuple[str, int]:
    """``text`` with each line the secrets hook would refuse replaced by a marker."""
    found = dict(find_secrets(text))
    if not found:
        return text, 0
    lines = text.splitlines()
    for n, what in found.items():
        lines[n - 1] = WITHHELD.format(what=what)
    return "\n".join(lines) + ("\n" if text.endswith("\n") else ""), len(found)


def read_at(root: Path, sha: str, path: str) -> str | None:
    ok, out = run_git(root, "show", f"{sha}:{path}")
    if not ok or "\x00" in out:
        return None
    return out


def change_folder(root: Path, sha: str, change_id: str) -> str | None:
    """``changes/<id>-<slug>`` at ``sha``, or None."""
    ok, out = run_git(root, "ls-tree", "-d", "--name-only", sha, "changes/")
    if not ok:
        return None
    for line in out.splitlines():
        name = line.strip().removeprefix("changes/")
        if name.startswith(f"{change_id}-"):
            return f"changes/{name}"
    return None


def changed_files(root: Path, base: str, head: str) -> list[str]:
    ok, out = run_git(root, "diff", "--no-ext-diff", "--name-only", "--no-renames", base, head)
    return [line.strip() for line in out.splitlines() if line.strip()] if ok else []


def build(
    root: Path,
    change_id: str,
    phase: str,
    head: str,
    base: str | None,
    max_chars: int = DEFAULT_MAX_CHARS,
) -> dict[str, Any]:
    """{'ok', 'pieces': [{'title', 'text'}], 'sent', 'left_out': [{'path', 'why'}],
    'withheld_lines', 'chars', 'change_dir', 'reason'}. The pieces in priority order: the
    change's own three files, the project's ``CLAUDE.md`` and ``REVIEW.md``, then at (b) the
    files ``plan.md`` lists and at (e) the diff from ``base``; a piece that would pass
    ``max_chars`` is left out and named. ``ok`` false when the change's own files alone do
    not fit or the folder is not at ``head``."""
    root = Path(root)
    out: dict[str, Any] = {
        "ok": False,
        "pieces": [],
        "sent": [],
        "left_out": [],
        "withheld_lines": 0,
        "chars": 0,
        "change_dir": None,
        "reason": "",
    }
    change_rel = change_folder(root, head, change_id)
    if change_rel is None:
        out["reason"] = f"no folder changes/{change_id}-<slug>/ at {head[:12]}"
        return out
    out["change_dir"] = change_rel

    def add(title: str, path: str | None, text: str | None, required: bool = False) -> bool:
        if text is None:
            return True
        why = excluded(path, change_rel) if path else None
        if why:
            out["left_out"].append({"path": path, "why": why})
            return True
        text, withheld = redact(text)
        if out["chars"] + len(text) > max_chars:
            out["left_out"].append({"path": path or title, "why": f"size cap ({max_chars} chars)"})
            return not required
        out["pieces"].append({"title": title, "text": text})
        out["sent"].append(path or title)
        out["chars"] += len(text)
        out["withheld_lines"] += withheld
        return True

    plan_text = None
    for name in CHANGE_FILES:
        path = f"{change_rel}/{name}"
        text = read_at(root, head, path)
        if name == "plan.md":
            plan_text = text
        if not add(path, path, text, required=True):
            out["reason"] = f"the change's own files pass the size cap ({max_chars} chars)"
            return out
    for name in PROJECT_FILES:
        add(name, name, read_at(root, head, name))
    if phase == "b":
        for path in planned_files(plan_text or ""):
            if path.startswith(f"{change_rel}/") or path in PROJECT_FILES:
                continue
            text = read_at(root, head, path)
            if text is None:
                out["left_out"].append(
                    {"path": path, "why": "not in the repository yet, or binary"}
                )
                continue
            add(path, path, text)
    elif base:
        files = [p for p in changed_files(root, base, head) if not excluded(p, change_rel)]
        for path in changed_files(root, base, head):
            why = excluded(path, change_rel)
            if why:
                out["left_out"].append({"path": path, "why": why})
        if files:
            ok, diff = run_git(
                root,
                "diff",
                "--no-ext-diff",
                "--no-textconv",
                "--no-renames",
                "-U10",
                base,
                head,
                "--",
                *files,
            )
            if ok and "\x00" not in diff:
                add(f"the diff {base[:12]}..{head[:12]}", None, diff)
    out["ok"] = True
    return out
