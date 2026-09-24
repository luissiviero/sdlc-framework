"""Command-line face of the review panel (decision 21; build guide step 16a), called by the
phase commands under ``sdlc.yaml: review: deferred`` (or ``status.yaml: review_override``).

    python "${CLAUDE_PLUGIN_ROOT}/plugin/panel/cli.py" mode --root . --id 0001
    python cli.py items --root . --id 0001 --phase b
    python cli.py prompt --root . --id 0001 --phase b --item 1 \
        --member reviewer|advocate|conciliator
    python cli.py record --root . --id 0001 --phase b --item 1 [--cost-usd 0.42]
    python cli.py overturn --root . --id 0001 --phase b --item 1 --comment "<the owner's words>"

``mode`` prints the effective review mode. ``items`` runs the gate's checks without
recording anything and lists what would park on a judgment item of the fixed list — an
open flagged concern (``concern``, or ``policy`` when it names contradicting policies), an
``escalate`` verdict of the adversarial reviewer, an Important review finding (``finding``)
and the verifier's "does not match the plan" (``verifier``) — as the items the panel may
settle, each with its stable key and whether the ledger already decides it; everything else
that failed is listed under ``parks`` and stays the owner's. It writes the list to
``evidence/panel/<phase>-items.json`` for ``prompt`` and ``record``. ``prompt`` prints one
member's brief with the item filled in (``panel/prompts.py``). ``record`` reads the
conciliator's ``evidence/panel/<phase>-<n>-conciliator.json``, counts one panel call
against ``gate.max_panel_calls`` (its own count since 0.2.15, never a fix iteration; exit 3
at the cap: nothing is recorded, the gate parks), appends the entry to
``evidence/decisions-<phase>.json`` (and renders the ``.md``), for a concern rewrites the
item in ``spec.md`` as ``decided (by panel #<n>): ...``, and commits the change folder on
the current branch (``--no-commit`` leaves that to the caller): the decision is then in
HEAD before the adversarial reviewer judges it, so a verdict never predates the panel (the
first deferred run committed each verdict beside the content it did not judge, three
times). ``overturn`` marks an entry overturned by the owner's review comment
(``/sdlc-fix`` applies the comment itself).

Under ``review: parked`` every command still answers (``items`` says the mode), so a
by-hand run can see what the panel would take; nothing is decided unless the mode is
``deferred``. Exit 0 ok, 2 usage, 3 the cap is reached, 4 the mode is parked (``record``).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from review import findings as fmod  # noqa: E402

from gate import artifacts as art  # noqa: E402
from gate import diff as diffmod  # noqa: E402
from gate import gate, limits  # noqa: E402
from gate.checks import GateContext  # noqa: E402
from hooks._common import ConfigError, load_sdlc_config  # noqa: E402
from panel import ledger  # noqa: E402
from panel import prompts as prompts_mod  # noqa: E402
from state import conventions as c  # noqa: E402
from state import gitops  # noqa: E402
from state import status as status_mod  # noqa: E402

EXIT_OK, EXIT_USAGE, EXIT_CAP, EXIT_PARKED_MODE = 0, 2, 3, 4
# the commit word of each phase's runbook (design(<id>): ..., build(<id>): ...)
COMMIT_WORD = {
    "a": "intent",
    "b": "design",
    "c": "build",
    "d": "test",
    "e": "review",
    "f": "maintain",
}


def _emit(obj: Any) -> None:
    print(json.dumps(obj, indent=2, sort_keys=True))


def _posix(path: Path) -> str:
    return str(Path(path).resolve()).replace("\\", "/")


def _change(args) -> tuple[Path, Path, status_mod.Status] | None:
    root = Path(args.root).resolve()
    change_dir = c.find_change_dir(root, args.id)
    if change_dir is None:
        print(f"no change folder for id {args.id}", file=sys.stderr)
        return None
    return root, change_dir, status_mod.read_status(change_dir)


def _config(root: Path) -> dict[str, Any]:
    try:
        return load_sdlc_config(str(root)) or {}
    except ConfigError:
        return {}


def review_mode(config: dict[str, Any], st: status_mod.Status) -> str:
    """The effective review mode: the change's override, else the project's, else parked."""
    try:
        return c.effective_review_mode(config.get("review"), st.review_override)
    except ValueError:
        return c.DEFAULT_REVIEW_MODE


# --- items ----------------------------------------------------------------------------------
def collect_items(
    root: Path, change_dir: Path, phase: str, result: gate.GateResult
) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    """(panel items, parks) from a dry-run gate result of the phase.

    The items come from the failed checks that belong to the fixed list; every other failed
    check is a park. The verifier's disagreement is not a gate check: it is read from
    ``evidence/verifier.md``."""
    items: list[dict[str, Any]] = []
    parks: list[dict[str, str]] = []
    for check in result.failed:
        if check.name == "open_concerns":
            for text in check.details.get("open") or []:
                stripped = art.CONCERN_ITEM_RE.match(str(text))
                body = stripped.group("text").strip() if stripped else str(text).strip()
                items.append(
                    {"kind": ledger.kind_of_concern(body), "key": ledger.concern_key(body),
                     "item": body}
                )  # fmt: skip
        elif check.name == "adversarial_review" and "escalate" in check.reason:
            reasons = [str(r) for r in (check.details.get("reasons") or [])]
            items.append(
                {
                    "kind": "escalate",
                    "key": ledger.escalate_key(reasons),
                    "item": "adversarial reviewer says escalate: "
                    + ("; ".join(reasons) or "no reason given"),
                }
            )
        elif check.name == "findings" and check.details.get("important"):
            for finding in check.details.get("important") or []:
                if not isinstance(finding, dict):
                    continue
                sig = str(finding.get("signature") or fmod.signature(finding))
                where = str(finding.get("file", "")).strip()
                line = finding.get("line")
                where = f"{where}:{line}" if where and isinstance(line, int) and line else where
                summary = str(finding.get("summary", "")).strip()
                rule = str(finding.get("rule") or "").strip()
                text = f"Important finding at {where or '?'}: {summary}" + (
                    f" [{rule}]" if rule else ""
                )
                items.append({"kind": "finding", "key": ledger.finding_key(sig), "item": text})
        else:
            parks.append({"check": check.name, "reason": check.reason})
    verifier = art.read_text(change_dir / art.EVIDENCE_DIR / art.EVIDENCE_VERIFIER)
    if ledger.verifier_disagrees(verifier):
        items.append(
            {
                "kind": "verifier",
                "key": ledger.VERIFIER_KEY,
                "item": "the verifier reports that the change does not match the plan "
                "(evidence/verifier.md)",
            }
        )
    decided = ledger.decided_keys(ledger.load_ledger(change_dir, phase))
    for n, item in enumerate(items, 1):
        item["n"] = n
        item["decided"] = item["key"] in decided
    return items, parks


def cmd_mode(args) -> int:
    loaded = _change(args)
    if loaded is None:
        return EXIT_USAGE
    root, _change_dir, st = loaded
    _emit({"mode": review_mode(_config(root), st), "override": st.review_override})
    return EXIT_OK


def cmd_items(args) -> int:
    loaded = _change(args)
    if loaded is None:
        return EXIT_USAGE
    root, change_dir, st = loaded
    mode = review_mode(_config(root), st)
    try:
        result = gate.run_gate(root, args.id, args.phase, args.base, dry_run=True)
    except gate.GateError as exc:
        print(f"gate: {exc}", file=sys.stderr)
        return EXIT_USAGE
    items, parks = collect_items(root, change_dir, args.phase, result)
    entries = ledger.load_ledger(change_dir, args.phase)
    ctx = GateContext(root, change_dir, args.phase, st, _config(root), None, True, "")
    cap = limits.iteration_cap(ctx, limits.classification_for(ctx))
    calls_cap = limits.panel_cap(ctx)
    out = {
        "mode": mode,
        "phase": args.phase,
        "items": items,
        "parks": parks,
        "pending": [i["n"] for i in items if not i["decided"]],
        "decided": len(ledger.active(entries)),
        "iterations": {"used": st.iterations, "cap": cap, "left": max(cap - st.iterations, 0)},
        "panel_calls": {
            "used": st.panel_calls,
            "cap": calls_cap,
            "left": max(calls_cap - st.panel_calls, 0),
        },
        "gate": result.result,
    }
    path = ledger.items_path(change_dir, args.phase)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(out, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n"
    )
    _emit(out)
    return EXIT_OK


# --- prompt ---------------------------------------------------------------------------------
def _item(change_dir: Path, phase: str, n: int) -> dict[str, Any] | None:
    path = ledger.items_path(change_dir, phase)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    for item in data.get("items") or []:
        if isinstance(item, dict) and item.get("n") == n:
            return item
    return None


def render_prompt(
    member: str, root: Path, change_dir: Path, st: status_mod.Status, phase: str, item: dict
) -> str:
    template = {
        "reviewer": prompts_mod.REVIEWER,
        "advocate": prompts_mod.ADVOCATE,
        "conciliator": prompts_mod.CONCILIATOR,
    }[member]
    n = int(item["n"])
    kind = str(item.get("kind"))
    return template.format(
        n=n,
        phase=phase,
        change_id=st.id,
        title=st.title,
        kind=kind,
        item=str(item.get("item", "")),
        root=_posix(root),
        change_dir=_posix(change_dir),
        output=_posix(ledger.member_path(change_dir, phase, n, member)),
        reviewer_file=_posix(ledger.member_path(change_dir, phase, n, "reviewer")),
        advocate_file=_posix(ledger.member_path(change_dir, phase, n, "advocate")),
        evidence_hint=prompts_mod.EVIDENCE_HINT.get(phase, "whatever the phase left there."),
        apply_hint=prompts_mod.APPLY_HINT.get(kind, "one line the run can act on."),
    )


def cmd_prompt(args) -> int:
    loaded = _change(args)
    if loaded is None:
        return EXIT_USAGE
    root, change_dir, st = loaded
    item = _item(change_dir, args.phase, args.item)
    if item is None:
        print(f"no item {args.item} for phase ({args.phase}): run `items` first", file=sys.stderr)
        return EXIT_USAGE
    text = render_prompt(args.member, root, change_dir, st, args.phase, item)
    sys.stdout.write(text if text.endswith("\n") else text + "\n")
    return EXIT_OK


# --- record ---------------------------------------------------------------------------------
def cmd_record(args) -> int:
    loaded = _change(args)
    if loaded is None:
        return EXIT_USAGE
    root, change_dir, st = loaded
    config = _config(root)
    mode = review_mode(config, st)
    if mode != "deferred":
        print(
            f"review mode is {mode}: the panel decides nothing; the item parks for the owner",
            file=sys.stderr,
        )
        return EXIT_PARKED_MODE
    item = _item(change_dir, args.phase, args.item)
    if item is None:
        print(f"no item {args.item} for phase ({args.phase}): run `items` first", file=sys.stderr)
        return EXIT_USAGE
    decision_path = ledger.member_path(change_dir, args.phase, args.item, "conciliator")
    try:
        decision = json.loads(decision_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        print(f"{decision_path.name} is missing or unreadable: {exc}", file=sys.stderr)
        return EXIT_USAGE
    if isinstance(decision, dict):
        # the decision alone: no closing prefix copied from the brief, no item text after it
        decision["decision"] = ledger.clean_decision(
            str(decision.get("decision") or ""), str(item.get("item", ""))
        )
    problems = ledger.validate_decision_file(decision)
    if problems:
        print("; ".join(problems), file=sys.stderr)
        return EXIT_USAGE
    entries = ledger.load_ledger(change_dir, args.phase)
    if item["key"] in ledger.decided_keys(entries):
        existing = next(e for e in ledger.active(entries) if e.get("key") == item["key"])
        _emit({"recorded": False, "reason": "already decided", "entry": existing})
        return EXIT_OK
    # one panel call counts against gate.max_panel_calls (decision 21, amended in 0.2.15:
    # the fix iterations are another count)
    ctx = GateContext(root, change_dir, st.phase, st, config, None, True, "no diff needed")
    cap = limits.panel_cap(ctx)
    if st.panel_calls + 1 > cap:
        _emit(
            {
                "recorded": False,
                "reason": "panel-call cap reached",
                "panel_calls": st.panel_calls,
                "cap": cap,
            }
        )
        return EXIT_CAP
    st.bump_panel_call()
    status_mod.write_status(change_dir, st)
    head = diffmod.head_sha(root) or "unknown"
    cost = float(args.cost_usd) if args.cost_usd is not None else None
    entry = ledger.new_entry(len(entries) + 1, args.phase, item, decision, head, cost)
    entries.append(entry)
    ledger.save_ledger(change_dir, args.phase, entries)
    applied = ledger.apply_decision(change_dir, entry)
    committed = None
    if not args.no_commit and gitops.is_repo(root):
        rel = str(change_dir.relative_to(root)).replace("\\", "/")
        gitops.ensure_identity(root)  # a CI runner commits under the automation identity
        committed = gitops.commit_paths(
            root,
            [rel],
            f"{COMMIT_WORD.get(args.phase, args.phase)}({st.id}): panel decision {entry['n']}",
        )
    _emit(
        {
            "recorded": True,
            "entry": entry,
            "applied_to_spec": applied,
            "panel_calls": st.panel_calls,
            "cap": cap,
            "iterations": st.iterations,
            "commit": committed,
            "ledger": str(ledger.ledger_path(change_dir, args.phase).relative_to(root)).replace(
                "\\", "/"
            ),
        }
    )
    return EXIT_OK


def cmd_overturn(args) -> int:
    loaded = _change(args)
    if loaded is None:
        return EXIT_USAGE
    _root, change_dir, _st = loaded
    entries = ledger.load_ledger(change_dir, args.phase)
    target = next((e for e in entries if e.get("n") == args.item), None)
    if target is None:
        print(f"no decision {args.item} in the ledger of phase ({args.phase})", file=sys.stderr)
        return EXIT_USAGE
    target["overturned"] = {"comment": " ".join(args.comment.split()), "at": ledger._now()}
    ledger.save_ledger(change_dir, args.phase, entries)
    _emit({"overturned": True, "entry": target})
    return EXIT_OK


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="sdlc-panel", description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)
    for name, fn in (
        ("mode", cmd_mode),
        ("items", cmd_items),
        ("prompt", cmd_prompt),
        ("record", cmd_record),
        ("overturn", cmd_overturn),
    ):
        s = sub.add_parser(name)
        s.add_argument("--root", default=".")
        s.add_argument("--id", required=True)
        if name != "mode":
            s.add_argument("--phase", required=True, choices=c.PHASES)
        if name == "items":
            s.add_argument("--base", default=None, help="base ref for the diff")
        if name in ("prompt", "record", "overturn"):
            s.add_argument("--item", required=True, type=int, help="the item's n from `items`")
        if name == "prompt":
            s.add_argument("--member", required=True, choices=ledger.MEMBERS)
        if name == "record":
            s.add_argument("--cost-usd", default=None, type=float)
            s.add_argument(
                "--no-commit",
                action="store_true",
                help="leave the change folder uncommitted (the caller commits it)",
            )
        if name == "overturn":
            s.add_argument("--comment", required=True)
        s.set_defaults(fn=fn)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
