"""Command-line face of the confidence gate (build guide steps 16 and 19).

    python "${CLAUDE_PLUGIN_ROOT}/plugin/gate/cli.py" check --root . --id 0001 --phase c \
        [--base origin/main] [--dry-run]
    python cli.py start-run --root . --id 0001 --phase c        # wall-clock start (step 19)
    python cli.py record-spend --root . --id 0001 --phase c --usd 1.25
    python cli.py set-iterations --root . --id 0001 --count 0

``check`` prints the gate result as JSON (result: continue | wait | park, the checks, the
"What I need from you" block) and exits 0 on continue, 3 on wait (human gate), 4 on park,
2 on a usage error. Without ``--dry-run`` it records the verdict in status.yaml and
evidence/gate-<phase>.json.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from gate import gate, limits  # noqa: E402
from state import conventions as c  # noqa: E402
from state import status as status_mod  # noqa: E402

EXIT = {"continue": 0, "wait": 3, "park": 4}


def _emit(obj) -> None:
    print(json.dumps(obj, indent=2, sort_keys=True))


def cmd_check(args) -> int:
    try:
        result = gate.run_gate(Path(args.root), args.id, args.phase, args.base, args.dry_run)
    except gate.GateError as exc:
        print(f"gate: {exc}", file=sys.stderr)
        return 2
    _emit(result.as_dict())
    block = result.what_i_need()
    if block:
        print(block, file=sys.stderr)
    return EXIT[result.result]


def _change(args):
    root = Path(args.root).resolve()
    change_dir = c.find_change_dir(root, args.id)
    if change_dir is None:
        print(f"no change folder for id {args.id}", file=sys.stderr)
        return None, None
    return change_dir, status_mod.read_status(change_dir)


def _run_file(change_dir: Path, phase: str) -> Path:
    return change_dir / "evidence" / limits.RUN_FILE.format(phase=phase)


def _write_run(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8", newline="\n")


def cmd_start_run(args) -> int:
    change_dir, _st = _change(args)
    if change_dir is None:
        return 2
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    data = {"phase": args.phase, "started_at": now, "spend_usd": None}
    _write_run(_run_file(change_dir, args.phase), data)
    _emit(data)
    return 0


def cmd_record_spend(args) -> int:
    change_dir, _st = _change(args)
    if change_dir is None:
        return 2
    path = _run_file(change_dir, args.phase)
    data = {}
    if path.is_file():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except ValueError:
            data = {}
    data.update({"phase": args.phase, "spend_usd": float(args.usd)})
    _write_run(path, data)
    _emit(data)
    return 0


def cmd_set_iterations(args) -> int:
    change_dir, st = _change(args)
    if change_dir is None:
        return 2
    st.iterations = int(args.count)
    st.touch()
    status_mod.write_status(change_dir, st)
    _emit(st.to_dict())
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="sdlc-gate", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    ck = sub.add_parser("check")
    ck.add_argument("--root", default=".")
    ck.add_argument("--id", required=True)
    ck.add_argument("--phase", required=True, choices=c.PHASES)
    ck.add_argument("--base", default=None, help="base ref for the diff (default: origin HEAD)")
    ck.add_argument("--dry-run", action="store_true", help="evaluate only; write nothing")
    ck.set_defaults(fn=cmd_check)

    sr = sub.add_parser("start-run")
    sr.add_argument("--root", default=".")
    sr.add_argument("--id", required=True)
    sr.add_argument("--phase", required=True, choices=c.PHASES)
    sr.set_defaults(fn=cmd_start_run)

    rs = sub.add_parser("record-spend")
    rs.add_argument("--root", default=".")
    rs.add_argument("--id", required=True)
    rs.add_argument("--phase", required=True, choices=c.PHASES)
    rs.add_argument("--usd", required=True, type=float)
    rs.set_defaults(fn=cmd_record_spend)

    si = sub.add_parser("set-iterations")
    si.add_argument("--root", default=".")
    si.add_argument("--id", required=True)
    si.add_argument("--count", required=True, type=int)
    si.set_defaults(fn=cmd_set_iterations)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
