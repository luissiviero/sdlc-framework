"""Command-line face of the confidence gate (build guide steps 16 and 19).

    python "${CLAUDE_PLUGIN_ROOT}/plugin/gate/cli.py" check --root . --id 0001 --phase c \
        [--base origin/main] [--dry-run]
    python cli.py start-run --root . --id 0001 --phase c        # wall-clock start (step 19)
    python cli.py record-spend --root . --id 0001 --phase c --usd 1.25
    python cli.py set-iterations --root . --id 0001 --count 0   # owner only (decision 11)
    python cli.py bump-iteration --root . --id 0001             # one fix round (step 24)
    python cli.py spec-header --root . --id 0001 [--plugin-root <path>]

``bump-iteration`` counts one fix round of the change's current phase (the runbooks call it
per round of the verifier / evidence / review loops), writes ``status.yaml`` and prints the
new count with the cap in force (the adversarial reviewer's routine/non-routine
classification tightens it, step 19). It exits 3 once the count is past the cap, so a
runbook can stop the loop before the gate parks the change.

``spec-header`` prints the two header lines of spec.md (step 22; article p.14: the spec, the
prompt that produced it and the skill versions in force are logged together) as JSON, with
the pieces it rendered them from.

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

from gate import artifacts as art  # noqa: E402
from gate import gate, limits, preflight  # noqa: E402
from gate.checks import GateContext  # noqa: E402
from hooks._common import ConfigError, load_sdlc_config  # noqa: E402
from state import conventions as c  # noqa: E402
from state import status as status_mod  # noqa: E402

EXIT = {"continue": 0, "wait": 3, "park": 4}
EXIT_CAP_REACHED = 3  # bump-iteration: the loop has spent its last round
REPO_ROOT = Path(__file__).resolve().parents[2]  # the plugin root Claude Code installs
UNKNOWN_VERSION = "unknown"


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
    if args.panel_calls is not None:
        st.panel_calls = int(args.panel_calls)  # decision 21: the panel's own count
    st.touch()
    status_mod.write_status(change_dir, st)
    _emit(st.to_dict())
    return 0


def cmd_bump_iteration(args) -> int:
    """One more fix round in the change's current phase (OPERATING_MODEL section 4.1).

    The cap comes from the run limits (step 19), tightened when the adversarial reviewer
    classed the plan non-routine; the gate parks the change once the count is past it, so
    this command reports the cap and exits 3 to let the runbook stop one round earlier."""
    change_dir, st = _change(args)
    if change_dir is None:
        return 2
    root = Path(args.root).resolve()
    try:
        config = load_sdlc_config(str(root))
    except ConfigError as exc:
        print(f"gate: {exc}", file=sys.stderr)
        return 2
    # a bare context: the caps and the classification read only the config and evidence/
    ctx = GateContext(root, change_dir, st.phase, st, config, None, True, "no diff needed")
    classification = limits.classification_for(ctx)
    cap = limits.iteration_cap(ctx, classification)
    iterations = st.bump_iteration()
    status_mod.write_status(change_dir, st)
    cap_reached = iterations > cap
    _emit(
        {
            "iterations": iterations,
            "cap": cap,
            "cap_reached": cap_reached,
            "classification": classification,
        }
    )
    return EXIT_CAP_REACHED if cap_reached else 0


def plugin_version(root: Path, plugin_root: Path) -> str:
    """The pinned version from the project's sdlc.yaml (decision 8), falling back to the
    installed plugin's manifest when the project has no pin yet."""
    try:
        config = load_sdlc_config(str(root))
    except ConfigError:
        config = {}
    pinned = config.get("plugin") if isinstance(config.get("plugin"), dict) else {}
    version = str(pinned.get("version") or "").strip()
    if version:
        return version
    manifest = Path(plugin_root) / ".claude-plugin" / "plugin.json"
    try:
        data = json.loads(manifest.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return UNKNOWN_VERSION
    return str(data.get("version") or UNKNOWN_VERSION)


def skill_overrides(root: Path) -> list[str]:
    """Policy skills the project replaced with its own under .claude/skills/ (step 20)."""
    return [
        name
        for name in preflight.POLICY_SKILLS
        if (Path(root) / ".claude" / "skills" / name / "SKILL.md").is_file()
    ]


def cmd_spec_header(args) -> int:
    root = Path(args.root).resolve()
    change_dir, st = _change(args)
    if change_dir is None:
        return 2
    intent = art.read_text(change_dir / "intent.md") or ""
    title = art.intent_title(intent) or st.title
    version = plugin_version(root, Path(args.plugin_root))
    skills = list(preflight.POLICY_SKILLS)
    overrides = skill_overrides(root)
    _emit(
        {
            "title": title,
            "change_id": st.id,
            "plugin_version": version,
            "skills": skills,
            "overrides": overrides,
            "prompt_version": art.DESIGN_PROMPT_VERSION,
            "header": art.render_spec_header(title, st.id, version, skills, overrides),
        }
    )
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

    bi = sub.add_parser(
        "bump-iteration", help="count one fix round; exit 3 when the iteration cap is reached"
    )
    bi.add_argument("--root", default=".")
    bi.add_argument("--id", required=True)
    bi.set_defaults(fn=cmd_bump_iteration)

    si = sub.add_parser("set-iterations")
    si.add_argument("--root", default=".")
    si.add_argument("--id", required=True)
    si.add_argument("--count", required=True, type=int)
    si.add_argument("--panel-calls", default=None, type=int, help="also set the panel-call count")
    si.set_defaults(fn=cmd_set_iterations)

    sh = sub.add_parser(
        "spec-header", help="render the two header lines of spec.md for the design pass"
    )
    sh.add_argument("--root", default=".")
    sh.add_argument("--id", required=True)
    sh.add_argument(
        "--plugin-root",
        default=str(REPO_ROOT),
        help="installed plugin root, read when sdlc.yaml carries no plugin.version pin",
    )
    sh.set_defaults(fn=cmd_spec_header)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
