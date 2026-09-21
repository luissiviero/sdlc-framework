"""Deterministic check behind the security-baseline skill: secrets in added lines (the same
patterns as the secrets hook), tracked .env files, dangerous calls in added code, and the
guardrail deny rules in .claude/settings.json (advisory; the hook and the settings enforce).

    python "${CLAUDE_PLUGIN_ROOT}/plugin/skills/security-baseline/check.py" --root .
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from gate import policy  # noqa: E402
from hooks.secrets_check import find_secrets  # noqa: E402

DANGEROUS = (
    (re.compile(r"\bshell\s*=\s*True\b"), "subprocess with shell=True"),
    (re.compile(r"(?<![\w.])eval\s*\("), "eval()"),
    (re.compile(r"(?<![\w.])exec\s*\("), "exec()"),
    (re.compile(r"\bpickle\.loads?\s*\("), "pickle deserialisation of untrusted data"),
    (re.compile(r"\byaml\.load\s*\((?![^)]*Loader)"), "yaml.load without a Loader"),
    (re.compile(r"\bverify\s*=\s*False\b"), "TLS verification disabled"),
    (re.compile(r"\binnerHTML\s*="), "innerHTML assignment"),
    (re.compile(r"dangerouslySetInnerHTML"), "dangerouslySetInnerHTML"),
    (
        re.compile(r"\bexecute\s*\(\s*f?[\"'].*%s|\bexecute\s*\(\s*f[\"']"),
        "SQL built by string formatting",
    ),
)
REQUIRED_DENY = ("Read(.env*)", "Edit(.claude/**)", "Edit(CLAUDE.md)", "Edit(sdlc.yaml)")


def main(argv: list[str] | None = None) -> int:
    args = policy.base_parser(__doc__).parse_args(argv)
    ch = policy.load_change(Path(args.root), args.base)
    findings: list[str] = []
    notes: list[str] = [ch.note] if ch.note else []
    for rel, lines in ch.added.items():
        if not policy.is_text(rel):
            continue
        text = "\n".join(t for _, t in lines)
        for _, what in find_secrets(text):
            findings.append(f"{rel}: possible secret in added lines ({what})")
        for line_no, t in lines:
            for rx, what in DANGEROUS:
                if rx.search(t):
                    findings.append(f"{rel}:{line_no}: {what}")
    for rel in ch.files:
        name = Path(rel).name
        if name.startswith(".env") and name != ".env.example":
            findings.append(f"{rel}: an .env file is in the diff")
    settings = ch.root / ".claude" / "settings.json"
    if settings.is_file():
        try:
            deny = (json.loads(settings.read_text(encoding="utf-8")).get("permissions") or {}).get(
                "deny"
            ) or []
        except ValueError:
            deny = []
        for rule in REQUIRED_DENY:
            if rule not in deny:
                findings.append(f".claude/settings.json lacks the deny rule {rule}")
    else:
        findings.append(".claude/settings.json is missing (run /sdlc-init)")
    return policy.report("security-baseline check", findings, notes)


if __name__ == "__main__":
    sys.exit(main())
