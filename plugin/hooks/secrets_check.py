"""PreToolUse hook: keep credentials out of the diff (build guide step 15 (3); article p.23
'Keep credentials out of the diff', p.37 deny of .env* / secrets/**).

Scans every piece of text an Edit/Write would put into a file. A line containing
``sdlc: allow-secret`` is skipped only when that very line is already in the file's
committed version (``git show HEAD:<path>``, replacement refs ignored): the mark is the
owner's, placed in a reviewed PR so a documented test fixture can carry a fake key on
purpose, and a run that adds the mark to a new or changed line is refused like any other
(0.2.28: the denial message used to suggest the mark, and a live run of eval case 0003 saw
the model add it on a retry and land the key). For the generic credential-assignment rule,
placeholder values (``<...>``, ``${...}``, ``{{...}}``, example, changeme, dummy, xxx,
redacted, your-…) are not reported; the token-shaped rules (AWS, GitHub, Slack, Anthropic,
OpenAI, Google, private keys) always are.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import (  # noqa: E402
    Decision,
    new_texts,
    project_dir,
    rel_to,
    run_hook,
    target_paths,
)

ALLOW_MARK = "sdlc: allow-secret"

_NAME = (
    r"(?:api[_-]?key|secret(?:[_-]?(?:key|access[_-]?key))?|client[_-]?secret|password|passwd|"
    r"pwd|auth[_-]?token|access[_-]?token|refresh[_-]?token|private[_-]?key|"
    r"aws[_-]?secret[_-]?access[_-]?key)"
)
PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("private key block", re.compile(r"-----BEGIN (?:[A-Z ]+ )?PRIVATE KEY-----")),
    ("AWS access key id", re.compile(r"(?<![A-Za-z0-9])AKIA[0-9A-Z]{16}(?![A-Za-z0-9])")),
    ("GitHub token", re.compile(r"(?<![A-Za-z0-9])gh[pousr]_[A-Za-z0-9]{36,}")),
    ("GitHub fine-grained token", re.compile(r"(?<![A-Za-z0-9])github_pat_[A-Za-z0-9_]{50,}")),
    ("Slack token", re.compile(r"(?<![A-Za-z0-9])xox[abprs]-[A-Za-z0-9-]{10,}")),
    ("Anthropic API key", re.compile(r"(?<![A-Za-z0-9])sk-ant-[A-Za-z0-9_\-]{20,}")),
    ("OpenAI-style key", re.compile(r"(?<![A-Za-z0-9])sk-(?:proj-)?(?!ant-)[A-Za-z0-9_\-]{32,}")),
    ("Google API key", re.compile(r"(?<![A-Za-z0-9])AIza[0-9A-Za-z_\-]{35}")),
    (
        "hard-coded credential assignment",
        re.compile(
            r"(?i)(?<![A-Za-z0-9])[\"']?(?:[A-Z0-9_]*_)?" + _NAME + r"[\"']?"
            r"\s*[:=]\s*[\"']?([^\"'\s#][^\"'\n#]{7,})[\"']?"
        ),
    ),
]
PLACEHOLDER = re.compile(
    r"(?i)(<[^>]*>|\$\{[^}]*\}|\{\{[^}]*\}\}|\$[A-Z_][A-Z0-9_]*|os\.environ|getenv|env\(|"
    r"example|changeme|dummy|xxx+|your[_-]|placeholder|redacted|\*{3,}|\.\.\.)"
)


UNCOMMITTED_MARK = " on a line marked allow-secret that the owner has not committed"


def committed_lines(root: str, path: str) -> frozenset[str]:
    """The lines of ``path`` as committed at HEAD, or an empty set — no allowance — when the
    file is outside the project, untracked, or git cannot answer within its budget."""
    rel = rel_to(root, path)
    if not rel:
        return frozenset()
    try:
        proc = subprocess.run(
            ["git", "--no-replace-objects", "show", f"HEAD:{rel}"],
            cwd=root,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        return frozenset()
    return frozenset(proc.stdout.splitlines()) if proc.returncode == 0 else frozenset()


def find_secrets(text: str, committed: frozenset[str] = frozenset()) -> list[tuple[int, str]]:
    """(line number, what was found) per line; a line carrying the allow mark is skipped only
    when ``committed`` holds it byte for byte."""
    findings = []
    for lineno, line in enumerate(text.splitlines(), start=1):
        marked = ALLOW_MARK in line
        if marked and line in committed:
            continue
        for label, rx in PATTERNS:
            m = rx.search(line)
            if not m:
                continue
            value = m.group(1) if m.groups() else m.group(0)
            if label == "hard-coded credential assignment" and PLACEHOLDER.search(value):
                continue
            findings.append((lineno, label + (UNCOMMITTED_MARK if marked else "")))
            break
    return findings


def decide(payload: dict, argv: list[str], env: dict[str, str] | None = None) -> Decision:
    tool_input = payload.get("tool_input") or {}
    texts = new_texts(tool_input)
    paths = target_paths(tool_input)
    committed: frozenset[str] = frozenset()
    if paths and any(ALLOW_MARK in text for text in texts):
        committed = committed_lines(project_dir(payload, env), paths[0])
    for text in texts:
        findings = find_secrets(text, committed)
        if findings:
            where = ", ".join(f"line {n}: {label}" for n, label in findings[:5])
            target = tool_input.get("file_path") or tool_input.get("notebook_path") or "the file"
            return Decision.deny(
                f"Possible secret in the text written to {target} ({where}). Credentials never "
                "go into the diff: read them from the environment or a secrets store. A "
                f"deliberate fake value is allowed only on a line the owner already committed "
                f"with '# {ALLOW_MARK}' in a reviewed PR; a run cannot add the mark."
            )
    return Decision.allow()


if __name__ == "__main__":
    sys.exit(run_hook(decide, "PreToolUse", sys.argv[1:]))
