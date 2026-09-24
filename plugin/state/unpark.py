"""The owner's un-park verbs as labels (decision 24; build guide steps 9, 16, 19; OPERATING_MODEL
section 6): ``sdlc:accept-risk``, ``sdlc:reset-iterations`` and ``sdlc:unlock-tests``, applied
by the owner on the change's PR, read by the next run, performed, and recorded in
``status.yaml`` with the label's actor as GitHub recorded it.

Why labels: point 3 of the objective puts the owner's input in the PR, not in a terminal, and
GitHub records who applied a label, so the actor is read from the PR's timeline instead of
inferred from a commit author (PROGRESS choice 17). The CLI commands (``accept-risk``,
``set-iterations``, ``unlock-tests``) stay for by-hand runs; the pause flag stays in
``sdlc.yaml`` because pausing is a reviewed change.

Rules:
- a label applied by the automation identity or by any ``<app>[bot]`` account is rejected and
  left on the PR: a run cannot un-park itself (decision 11);
- ``sdlc:accept-risk`` accepts the risk-list hits the last gate of the change's phase reported
  (``evidence/gate-<phase>.json``, check ``risk_list``, ``details.hits``); with no recorded hit
  there is nothing to accept and the label is left where it is, with the reason;
- a performed label is removed from the PR, so one application is one act and the next run
  does not perform it again; the ``labeled`` event stays in the PR's timeline as the record;
- the gate's ``owner_actions`` check (``plugin/gate/checks.py``) reads the recorded actor when
  the commit that carries the state change was authored by the automation identity.

``github`` is injectable: an object with ``pr_by_number``, ``label_actor`` and ``set_labels``
like ``plugin/pr/github.py``. No shell, no third-party dependency.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

PLUGIN_DIR = Path(__file__).resolve().parent.parent
if str(PLUGIN_DIR) not in sys.path:
    sys.path.insert(0, str(PLUGIN_DIR))

from state import conventions as c  # noqa: E402
from state import status as status_mod  # noqa: E402

GATE_FILE = "evidence/gate-{phase}.json"


def _load_github() -> tuple[Any, str]:
    try:
        from pr import github as gh_mod  # noqa: PLC0415
    except Exception as exc:  # noqa: BLE001 - any import failure means no route
        return None, f"plugin/pr/github.py cannot be imported: {exc!r}"
    return gh_mod, ""


def automation_identities(config: dict[str, Any]) -> list[str]:
    """``sdlc.yaml: automation_identity`` or the policy default (``gate/policy.py``)."""
    from gate.policy import automation_identity  # noqa: PLC0415

    return automation_identity(dict(config))


def is_automation_actor(actor: str, identities: list[str]) -> bool:
    """True for the automation identity and for any GitHub App account (``<app>[bot]``); the
    same rule as the release approval's (``release/approval.py``)."""
    who = (actor or "").strip().lower()
    if not who or who.endswith("[bot]"):
        return True
    return any(who == i.strip().lower() for i in identities)


def risk_hits(change_dir: Path, phase: str | None) -> list[str]:
    """The risk-list items the last gate of ``phase`` reported (the keys of the ``risk_list``
    check's ``details.hits``), or []. The gate file is the record the owner read in the PR's
    "What I need from you" block, so it is what the label answers."""
    if not phase or phase not in c.PHASES:
        return []
    path = Path(change_dir) / GATE_FILE.format(phase=phase)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    for check in (data.get("checks") if isinstance(data, dict) else None) or []:
        if isinstance(check, dict) and check.get("name") == "risk_list":
            hits = (check.get("details") or {}).get("hits")
            if isinstance(hits, dict):
                return [str(k) for k in hits if str(k).strip()]
    return []


def perform(
    st: status_mod.Status,
    present: dict[str, str | None],
    identities: list[str],
    hits: list[str],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Apply the owner labels ``present`` (label -> actor login, None when unknown) to
    ``st``; pure but for ``st``. Returns (performed, rejected), each a list of
    {label, actor, reason/items}."""
    performed: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    for label in c.UNPARK_LABELS:
        if label not in present:
            continue
        actor = (present.get(label) or "").strip()
        if not actor:
            rejected.append({"label": label, "actor": None, "reason": "no labeled event"})
            continue
        if is_automation_actor(actor, identities):
            rejected.append(
                {
                    "label": label,
                    "actor": actor,
                    "reason": f"applied by the automation identity {actor}: a run cannot "
                    "un-park itself (decision 11)",
                }
            )
            continue
        if label == c.ACCEPT_RISK_LABEL and not hits:
            rejected.append(
                {
                    "label": label,
                    "actor": actor,
                    "reason": f"no risk-list hit recorded in {GATE_FILE.format(phase=st.phase)}"
                    ": nothing to accept",
                }
            )
            continue
        st.record_owner_label(label, actor, hits if label == c.ACCEPT_RISK_LABEL else None)
        entry: dict[str, Any] = {"label": label, "actor": actor}
        if label == c.ACCEPT_RISK_LABEL:
            entry["items"] = list(hits)
        performed.append(entry)
    return performed, rejected


def apply_from_pr(
    root: Path,
    change_dir: Path,
    config: dict[str, Any],
    repo: str,
    pr_number: int,
    github: Any = None,
) -> dict[str, Any]:
    """Read the PR's labels, perform the owner's un-park labels on ``status.yaml`` and remove
    the performed ones from the PR. Returns {ok, performed, rejected, removed, reason}.

    Nothing is committed here: the caller commits ``status.yaml`` on the work branch (the
    CI run through ``commit-phase``; a by-hand ``/sdlc-fix`` round with its own commit).
    """
    out: dict[str, Any] = {"ok": False, "performed": [], "rejected": [], "removed": []}
    if github is None:
        github, why = _load_github()
        if github is None:
            return {**out, "reason": why}
    if not repo or not pr_number:
        return {**out, "reason": "no repository or pull request number to read labels from"}
    pr = github.pr_by_number(repo, int(pr_number), cwd=str(root))
    if not pr.get("ok"):
        return {**out, "reason": f"cannot read #{pr_number}: {pr.get('reason') or 'failed'}"}
    labels = [str(lb) for lb in (pr.get("labels") or [])]
    present: dict[str, str | None] = {}
    for label in c.UNPARK_LABELS:
        if label not in labels:
            continue
        found = github.label_actor(repo, int(pr_number), label)
        if not found.get("ok"):
            return {
                **out,
                "reason": f"cannot read who applied {label}: {found.get('reason') or 'failed'}",
            }
        present[label] = found.get("actor")
    if not present:
        return {**out, "ok": True, "reason": "no owner label on the pull request"}
    st = status_mod.read_status(change_dir)
    performed, rejected = perform(
        st, present, automation_identities(config), risk_hits(change_dir, st.phase)
    )
    if performed:
        status_mod.write_status(change_dir, st)
        removed = github.set_labels(
            repo, int(pr_number), [], [p["label"] for p in performed], cwd=str(root)
        )
        out["removed"] = removed.get("removed", []) if isinstance(removed, dict) else []
        if isinstance(removed, dict) and not removed.get("ok"):
            out["removal_reason"] = removed.get("reason", "")
    return {**out, "ok": True, "performed": performed, "rejected": rejected, "reason": ""}
