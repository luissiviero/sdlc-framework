"""Deterministic check behind the definition-of-done skill: the confidence gate's checks for
the change and phase, in dry-run (nothing recorded), as a table the summary can include.

    python "${CLAUDE_PLUGIN_ROOT}/plugin/skills/definition-of-done/check.py" \
        --root . --id 0001 --phase c
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from gate import gate, policy  # noqa: E402
from state import conventions as c  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    p = policy.base_parser(__doc__)
    p.add_argument("--id", required=True)
    p.add_argument("--phase", required=True, choices=c.PHASES)
    args = p.parse_args(argv)
    try:
        result = gate.run_gate(Path(args.root), args.id, args.phase, args.base, dry_run=True)
    except gate.GateError as exc:
        return policy.report("definition-of-done check", [f"gate could not run: {exc}"])
    print("## definition-of-done check (gate dry run)")
    print(
        f"- change {result.change_id} ({result.slug}), gate ({result.phase}), profile "
        f"{result.profile}, {'human' if result.human_gate else 'automated'} gate"
    )
    for ch in result.checks:
        print(f"- [{'x' if ch.ok else ' '}] {ch.name}: {ch.reason}")
    print(f"- verdict if run now: **{result.result}**")
    for ch in result.failed:
        if ch.need:
            print(f"  - {ch.name} needs: {ch.need}")
    return 0 if result.result != "park" else 1


if __name__ == "__main__":
    sys.exit(main())
