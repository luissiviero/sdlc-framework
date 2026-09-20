"""PreToolUse hook: keep credentials out of the diff (build guide step 15 (3); article p.23
'Keep credentials out of the diff', p.37 deny of .env* / secrets/**).

Scans every piece of text an Edit/Write would put into a file. A line containing
``sdlc: allow-secret`` is skipped, so a documented test fixture can carry a fake key on
purpose. For the generic credential-assignment rule, placeholder values (``<...>``,
``${...}``, ``{{...}}``, example, changeme, dummy, xxx, redacted, your-…) are not reported;
the token-shaped rules (AWS, GitHub, Slack, Anthropic, OpenAI, Google, private keys) always
are.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import Decision, new_texts, run_hook  # noqa: E402

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


def find_secrets(text: str) -> list[tuple[int, str]]:
    findings = []
    for lineno, line in enumerate(text.splitlines(), start=1):
        if ALLOW_MARK in line:
            continue
        for label, rx in PATTERNS:
            m = rx.search(line)
            if not m:
                continue
            value = m.group(1) if m.groups() else m.group(0)
            if label == "hard-coded credential assignment" and PLACEHOLDER.search(value):
                continue
            findings.append((lineno, label))
            break
    return findings


def decide(payload: dict, argv: list[str]) -> Decision:
    tool_input = payload.get("tool_input") or {}
    for text in new_texts(tool_input):
        findings = find_secrets(text)
        if findings:
            where = ", ".join(f"line {n}: {label}" for n, label in findings[:5])
            target = tool_input.get("file_path") or tool_input.get("notebook_path") or "the file"
            return Decision.deny(
                f"Possible secret in the text written to {target} ({where}). Credentials never "
                "go into the diff: read them from the environment or a secrets store. If this is"
                f" a deliberate fake value, put '# {ALLOW_MARK}' on that line."
            )
    return Decision.allow()


if __name__ == "__main__":
    sys.exit(run_hook(decide, "PreToolUse", sys.argv[1:]))
