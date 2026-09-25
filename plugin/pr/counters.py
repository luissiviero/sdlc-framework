"""The framework's indicators over ``changes/*/`` (build guide step 42, task 42.2; article
p.17 "first-pass merge share ... rework cycles", p.45 "the share of findings that become
merged fixes ... and repeat incidents of the same class").

Deterministic, from the change folders of the checkout and ``changes/.dismissed.json`` only
(no API, no model): the digest workflow renders it as a section of the review-queue issue
(``pr/digest.py``), so the report is pull, not push (decision 20) and costs no commit and no
model call. Task 42.1's two counters per PR (first-pass merge, fix iterations) stay in the
PR description; this is their sum over the project.

    python "${CLAUDE_PLUGIN_ROOT}/plugin/pr/counters.py" --root . [--json]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from detect import dismissals  # noqa: E402

from state import conventions as c  # noqa: E402
from state import status as status_mod  # noqa: E402

SHIPPED_PHASE = "e"  # a change at phase e on the default branch was merged by the owner


def collect(root: Path) -> dict[str, Any]:
    """Counts over every readable ``changes/<id>-<slug>/status.yaml`` under ``root``."""
    root = Path(root)
    changes: list[status_mod.Status] = []
    unreadable = 0
    for change_dir in c.list_change_dirs(root):
        try:
            changes.append(status_mod.read_status(change_dir, on_default_branch=True))
        except (OSError, ValueError):
            unreadable += 1
    shipped = [st for st in changes if st.phase == SHIPPED_PHASE]
    # an incident folder reaches the default branch when the owner merged its intent PR
    # (fix now): a closed one never does - its finding is in the dismissal store instead
    incidents = [st for st in changes if st.entry_route == "incident"]
    dismissed = dismissals.load(dismissals.path_for(root, c.CHANGES_DIR)).get("entries") or {}
    first_pass = sum(1 for st in shipped if st.iterations == 0)
    return {
        "changes": len(changes),
        "unreadable": unreadable,
        "shipped": len(shipped),
        "first_pass_merges": first_pass,
        "first_pass_share": (first_pass / len(shipped)) if shipped else None,
        "fix_iterations_total": sum(st.iterations for st in changes),
        "fix_iterations_mean": (
            sum(st.iterations for st in shipped) / len(shipped) if shipped else None
        ),
        "panel_calls_total": sum(st.panel_calls for st in changes),
        "incidents_merged": len(incidents),
        "incidents_shipped": sum(1 for st in incidents if st.phase == SHIPPED_PHASE),
        "dismissals": len(dismissed),
        "dismissals_by_kind": {
            kind: sum(
                1 for e in dismissed.values() if isinstance(e, dict) and e.get("kind") == kind
            )
            for kind in dismissals.KINDS
        },
    }


def _pct(value: float | None) -> str:
    return "n/a" if value is None else f"{value * 100:.0f}%"


def _num(value: float | None) -> str:
    return "n/a" if value is None else f"{value:.1f}"


def render(counts: dict[str, Any]) -> str:
    """The markdown section the digest carries (one table, a note on what each row means)."""
    by_kind = counts.get("dismissals_by_kind") or {}
    rows = [
        ("Changes (folders on the default branch)", str(counts["changes"])),
        ("Shipped (merged at gate (e))", str(counts["shipped"])),
        (
            "First-pass merge share (p.17)",
            f"{_pct(counts['first_pass_share'])} ({counts['first_pass_merges']} of "
            f"{counts['shipped']})",
        ),
        (
            "Fix iterations per shipped change (p.17 rework cycles)",
            _num(counts["fix_iterations_mean"]),
        ),
        ("Panel calls, all changes (decision 21)", str(counts["panel_calls_total"])),
        (
            "Incidents merged (fix now) / shipped (p.45)",
            f"{counts['incidents_merged']} / {counts['incidents_shipped']}",
        ),
        (
            "Dismissals in force (detect / scan)",
            f"{counts['dismissals']} ({by_kind.get('detect', 0)} / {by_kind.get('scan', 0)})",
        ),
    ]
    out = ["## Counters", "", "| Indicator | Value |", "|---|---|"]
    out += [f"| {name} | {value} |" for name, value in rows]
    out.append("")
    out.append(
        "From the change folders of the default branch and changes/.dismissed.json: a "
        "change closed without a merge, and an incident closed (dismissed) before its "
        "intent merged, never reach the default branch and are not counted here."
    )
    if counts.get("unreadable"):
        out.append("")
        out.append(f"{counts['unreadable']} change folder(s) had an unreadable status.yaml.")
    return "\n".join(out) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="pr/counters.py", description=__doc__)
    parser.add_argument("--root", default=".")
    parser.add_argument("--json", action="store_true", help="print the counts as JSON")
    args = parser.parse_args(argv)
    counts = collect(Path(args.root).resolve())
    if args.json:
        print(json.dumps(counts, indent=2, sort_keys=True))
    else:
        print(render(counts), end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
