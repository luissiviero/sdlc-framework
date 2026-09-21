"""Deterministic check behind the coding-standards skill: runs the project's lint target from
sdlc.yaml and reports changed source files that grew without a test change (advisory).

    python "${CLAUDE_PLUGIN_ROOT}/plugin/skills/coding-standards/check.py" --root .
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from gate import policy  # noqa: E402
from gate.checks import PLACEHOLDER_COMMAND_RE, run_command  # noqa: E402

TEST_HINTS = ("test", "spec", "__tests__")
SOURCE_SUFFIXES = {".py", ".js", ".ts", ".tsx", ".jsx", ".go", ".rs", ".java", ".kt", ".rb", ".cs"}
LONG_FILE = 500


def main(argv: list[str] | None = None) -> int:
    args = policy.base_parser(__doc__).parse_args(argv)
    ch = policy.load_change(Path(args.root), args.base)
    findings: list[str] = []
    notes: list[str] = [ch.note] if ch.note else []
    lint = (ch.config.get("commands") or {}).get("lint") if isinstance(ch.config, dict) else None
    if isinstance(lint, str) and lint.strip() and not PLACEHOLDER_COMMAND_RE.match(lint):
        run = run_command(lint, ch.root, 600)
        if run["exit_code"] != 0:
            tail = run["output"].strip().splitlines()[-5:]
            findings.append(f"lint target `{lint}` exited {run['exit_code']}: " + " | ".join(tail))
        else:
            notes.append(f"lint target `{lint}` passed")
    else:
        findings.append("sdlc.yaml has no usable lint target (re-run /sdlc-init)")
    source = [f for f in ch.files if Path(f).suffix.lower() in SOURCE_SUFFIXES]
    tests = [f for f in source if any(h in f.lower() for h in TEST_HINTS)]
    if source and not tests:
        findings.append(
            f"{len(source)} source file(s) changed and no test file changed: "
            + ", ".join(source[:5])
        )
    for rel in source:
        path = ch.root / rel
        try:
            n = len(path.read_text(encoding="utf-8", errors="replace").splitlines())
        except OSError:
            continue
        if n > LONG_FILE:
            findings.append(f"{rel} is {n} lines; consider splitting (limit {LONG_FILE})")
    return policy.report("coding-standards check", findings, notes)


if __name__ == "__main__":
    sys.exit(main())
