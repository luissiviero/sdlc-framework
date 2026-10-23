"""The framework's indicators over ``changes/*/`` (build guide step 42, task 42.2; article
p.17 "first-pass merge share ... rework cycles", p.45 "the share of findings that become
merged fixes ... and repeat incidents of the same class").

Deterministic, from the change folders of the checkout, the abandon markers on the remote
``sdlc/<id>/*`` branches and ``changes/.dismissed.json`` (no API, no model): the digest
workflow renders it as a section of the review-queue issue
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
from detect.cli import _remote_abandoned_ids  # noqa: E402

from gate import artifacts as art  # noqa: E402
from gate import limits  # noqa: E402
from gate import risk as risk_mod  # noqa: E402
from state import conventions as c  # noqa: E402
from state import status as status_mod  # noqa: E402

SHIPPED_PHASE = "e"  # at phase e on the default branch: merged on the owner's approval (dec. 36)
CLASSES = ("routine", "non-routine")  # the adversarial reviewer's call on the plan

# R26, choice 257 (R60's port): the play each row measures, with the article page, and
# whether the article names it a leading or a lagging indicator; "" for a plain count
PLAN_MODE = "Plan mode (p.17)"
CLOSING_THE_LOOP = "Closing the loop (p.45)"

# R26 parts 5 and 6: what the table leaves to other entries and what it does not compute,
# each with its reason, written under the table so the owner never looks for it
NOT_COUNTED = (
    "Not counted here, with the reason: spend is each PR's spend line and the weekly "
    "ceiling's; the wait at each gate is the review queue's; failed runs are the section "
    "above; time to first review (the owner is the only reviewer); first-pass CI success "
    "(the runner runs the targets after the session, and a red target is a counted fix "
    "round); the share of intents that survive (an intent closed unmerged never reaches the "
    "default branch); OpenTelemetry and per-engineer measures (one owner, no team); DORA, "
    "built in a change of its own on a project with a declared production."
)


def _was_reset(st: status_mod.Status) -> bool:
    """A count reset by the owner's label, the runner's judged reset at the cap (decision
    29) or ``set-iterations`` by hand: each stamps ``iterations_reset_at`` (R26 part 1)."""
    return bool(st.iterations_reset_at)


def _first_pass(st: status_mod.Status) -> bool:
    """Merged with no fix round and no reset of the count: a reset zeroes it, and a change
    reset at the cap read as first-pass until R26."""
    return st.iterations == 0 and not _was_reset(st)


def _class_counts(group: list[status_mod.Status]) -> dict[str, Any]:
    first = sum(1 for st in group if _first_pass(st))
    return {
        "shipped": len(group),
        "first_pass_merges": first,
        "first_pass_share": (first / len(group)) if group else None,
        "fix_iterations_mean": (sum(st.iterations for st in group) / len(group) if group else None),
    }


def collect(root: Path) -> dict[str, Any]:
    """Counts over every readable ``changes/<id>-<slug>/status.yaml`` under ``root``."""
    root = Path(root)
    changes: list[tuple[Path, status_mod.Status]] = []
    unreadable = 0
    abandoned = 0
    # an abandon is written on the change's branches, never on the default branch (decision
    # 25): the rehearsal 0005 of the sample, merged and then closed, counted as an incident
    # merged until 0.2.26 — ``detect/cli.py open_incidents`` reads the same markers
    remote_abandoned = _remote_abandoned_ids(root)
    for change_dir in c.list_change_dirs(root):
        try:
            st = status_mod.read_status(change_dir, on_default_branch=True)
        except (OSError, ValueError):
            unreadable += 1
            continue
        if st.abandoned or st.id in remote_abandoned:
            abandoned += 1
            continue
        changes.append((change_dir, st))
    statuses = [st for _, st in changes]
    shipped_dirs = [(d, st) for d, st in changes if st.phase == SHIPPED_PHASE]
    shipped = [st for _, st in shipped_dirs]
    # an incident folder reaches the default branch when the owner merged its intent PR
    # (fix now): a closed one never does - its finding is in the dismissal store instead
    incidents = [st for st in statuses if st.entry_route == "incident"]
    dismissed = dismissals.load(dismissals.path_for(root, c.CHANGES_DIR)).get("entries") or {}
    # only an unexpired dismissal is in force, as the store itself reads it (R26 part 1)
    in_force = {
        sig: e for sig, e in dismissed.items() if dismissals.lookup({"entries": dismissed}, sig)
    }
    # R26 part 2: the plan's class as the iteration cap reads it, the newest verdict first
    by_class: dict[str, list[status_mod.Status]] = {k: [] for k in (*CLASSES, "unclassified")}
    grown: dict[str, int] = {}
    for change_dir, st in shipped_dirs:
        found = limits.classification_in(change_dir / art.EVIDENCE_DIR, SHIPPED_PHASE)
        by_class[found if found in CLASSES else "unclassified"].append(st)
        # choice 257 (R60's port): the files the plan gained after gate (b)
        added = risk_mod.plan_grown(change_dir, SHIPPED_PHASE)
        if added:
            grown[st.id] = len(added)
    first_pass = sum(1 for st in shipped if _first_pass(st))
    return {
        "changes": len(changes),
        "abandoned": abandoned,
        "unreadable": unreadable,
        "shipped": len(shipped),
        "first_pass_merges": first_pass,
        "first_pass_share": (first_pass / len(shipped)) if shipped else None,
        "reset_shipped": sorted(st.id for st in shipped if _was_reset(st)),
        "by_class": {k: _class_counts(group) for k, group in by_class.items()},
        "plan_grown": grown,
        "fix_iterations_total": sum(st.iterations for st in statuses),
        "fix_iterations_mean": (
            sum(st.iterations for st in shipped) / len(shipped) if shipped else None
        ),
        "panel_calls_total": sum(st.panel_calls for st in statuses),
        "incidents_merged": len(incidents),
        "incidents_shipped": sum(1 for st in incidents if st.phase == SHIPPED_PHASE),
        "dismissals": len(in_force),
        "dismissals_expired": len(dismissed) - len(in_force),
        "dismissals_by_kind": {
            kind: sum(1 for e in in_force.values() if isinstance(e, dict) and e.get("kind") == kind)
            for kind in dismissals.KINDS
        },
    }


def _pct(value: float | None) -> str:
    return "n/a" if value is None else f"{value * 100:.0f}%"


def _num(value: float | None) -> str:
    return "n/a" if value is None else f"{value:.1f}"


def _class_share(name: str, counts: dict[str, Any]) -> str:
    """A class's first-pass share with its "n of m"; a class with no shipped change says so
    instead of a rate (the proposal's settle table)."""
    if not counts["shipped"]:
        return f"0 of 0, no {name} plan shipped yet"
    share = _pct(counts["first_pass_share"])
    return f"{share} ({counts['first_pass_merges']} of {counts['shipped']})"


def _class_iterations(name: str, counts: dict[str, Any], shipped: int) -> str:
    if not counts["shipped"]:
        return f"0 of 0, no {name} plan shipped yet"
    return f"{_num(counts['fix_iterations_mean'])} ({counts['shipped']} of {shipped} shipped)"


def render(counts: dict[str, Any]) -> str:
    """The markdown section the digest carries: one table with the play each row measures,
    and the definitions under it (R26 part 1)."""
    by_kind = counts.get("dismissals_by_kind") or {}
    by_class = counts.get("by_class") or {}
    empty = {"shipped": 0, "first_pass_merges": 0, "first_pass_share": None}
    shipped = counts["shipped"]
    grown = counts.get("plan_grown") or {}
    rows = [
        ("Changes (folders on the default branch, not abandoned)", str(counts["changes"]), ""),
        ("Shipped (merged at gate (e))", str(shipped), ""),
        (
            "First-pass merge share",
            f"{_pct(counts['first_pass_share'])} ({counts['first_pass_merges']} of {shipped})",
            f"{PLAN_MODE}, leading",
        ),
    ]
    for name in CLASSES:
        rows.append(
            (
                f"First-pass merge share, {name} plans",
                _class_share(name, by_class.get(name) or empty),
                f"{PLAN_MODE}, leading",
            )
        )
    rows.append(
        (
            "Fix iterations per shipped change (rework cycles)",
            _num(counts["fix_iterations_mean"]),
            f"{PLAN_MODE}, lagging",
        )
    )
    for name in CLASSES:
        rows.append(
            (
                f"Fix iterations per shipped change, {name} plans",
                _class_iterations(name, by_class.get(name) or empty, shipped),
                f"{PLAN_MODE}, lagging",
            )
        )
    rows += [
        (
            "Plan grown since gate (b) (shipped changes)",
            f"{len(grown)} of {shipped} ({sum(grown.values())} files)",
            f"{PLAN_MODE}, lagging",
        ),
        ("Panel calls, all changes (decision 21)", str(counts["panel_calls_total"]), ""),
        (
            "Incidents merged (fix now) / shipped",
            f"{counts['incidents_merged']} / {counts['incidents_shipped']}",
            f"{CLOSING_THE_LOOP}, lagging",
        ),
        (
            "Dismissals in force (detect / scan)",
            f"{counts['dismissals']} ({by_kind.get('detect', 0)} / {by_kind.get('scan', 0)})",
            f"{CLOSING_THE_LOOP}, lagging",
        ),
    ]
    out = ["## Counters", "", "| Indicator | Value | Play, leading or lagging |", "|---|---|---|"]
    out += [f"| {name} | {value} | {play or '—'} |" for name, value, play in rows]
    out.append("")
    out.append(
        "From the change folders of the default branch and changes/.dismissed.json: a "
        "change closed without a merge, and an incident closed (dismissed) before its "
        "intent merged, never reach the default branch and are not counted here; a change "
        "abandoned after a merge (the marker sits on its sdlc/<id>/* branches) is left out."
    )
    out.append("")
    out.append(
        "First-pass: a shipped change with no fix round and no reset of its count (the "
        "owner's sdlc:reset-iterations, the runner's one reset at the cap, or set-iterations "
        "by hand); the owner's change requests on the intent and design PRs are fix rounds "
        "too. Fix iterations are read from status.yaml, which a reset sets back to 0, so a "
        "reset change counts fewer rounds than it ran. The plan's class is the adversarial "
        "reviewer's newest call, as the iteration cap reads it. Plan grown: the files the "
        "plan lists that the copy approved at gate (b) did not. Dismissals in force: unexpired "
        "only."
    )
    reset = counts.get("reset_shipped") or []
    if reset:
        out.append("")
        out.append(f"Reset, never first-pass: {', '.join(reset)}.")
    unclassified = (by_class.get("unclassified") or {}).get("shipped", 0)
    if unclassified:
        out.append("")
        out.append(
            f"{unclassified} shipped change(s) carry no class (no adversarial verdict in "
            "evidence/): in the totals only."
        )
    if counts.get("dismissals_expired"):
        out.append("")
        out.append(f"{counts['dismissals_expired']} expired dismissal(s), not in force.")
    out.append("")
    out.append(NOT_COUNTED)
    if counts.get("abandoned"):
        out.append("")
        out.append(f"{counts['abandoned']} change folder(s) abandoned after a merge, left out.")
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
