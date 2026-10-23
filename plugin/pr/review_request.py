"""The owner's review request on a pull request that waits (decision 31; OPERATING_MODEL
sections 6 and 7): the one notification the framework sends.

Every automated publication (``pr/cli.py upsert --request-review``: the runner, the detect
workflow and the weekly scan) brings the owner's review request in line with the label the
gate printed:
- a waiting label (``sdlc:needs-human``, ``sdlc:<phase>-ready``) requests the owner's review;
  a request still pending from an earlier wait (an ``@claude`` comment does not clear it)
  is removed and requested again, so every new wait gives one fresh push;
- any other label, or none, withdraws a pending request, so GitHub's "Review requests" list
  is exactly the owner's waiting queue.

The owner is ``state/unpark.py owner_login`` of the default branch's ``sdlc.yaml``. Nothing
is requested (a skip with its reason) when there is no owner, when the owner key names a bot
or the automation identity (``is_owner_actor``, fail closed), when the PR is not open, or
when the owner wrote the PR (GitHub refuses a review request to a PR's author). No comment,
no mention, nothing else.

``github`` is injectable: an object with ``request_reviewers`` and ``remove_reviewers`` like
``plugin/pr/github.py``. No model, no shell.
"""

from __future__ import annotations

import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any

PLUGIN_DIR = Path(__file__).resolve().parent.parent
if str(PLUGIN_DIR) not in sys.path:
    sys.path.insert(0, str(PLUGIN_DIR))

from state import conventions as c  # noqa: E402
from state.unpark import is_owner_actor, owner_login  # noqa: E402

WAITING_LABELS = frozenset({c.NEEDS_HUMAN_LABEL, *(c.ready_label(p) for p in c.PHASES)})


def is_waiting_label(label: str | None) -> bool:
    """True for the labels that leave the PR waiting for the owner: a park or a human gate."""
    return label in WAITING_LABELS


def sync_owner_review(
    github: Any,
    repo: str,
    number: int,
    label: str | None,
    config: dict[str, Any],
    env: Mapping[str, str],
    found: dict[str, Any],
) -> dict[str, Any]:
    """Request, re-request or withdraw the owner's review on PR ``number`` for ``label``.

    ``found`` is the PR as ``find_open_pr`` or ``pr_by_number`` returned it (``state``,
    ``author``, ``requested_reviewers``). Returns {ok, action, owner} or {ok: True,
    skipped}; a GitHub failure is {ok: False, reason}, never an exception."""
    owner = owner_login(config, env, repo)
    if not owner:
        return {"ok": True, "skipped": "no owner account is known (decision 34)"}
    if not is_owner_actor(owner, config, env, repo):
        return {
            "ok": True,
            "skipped": f"the owner key names {owner}, a bot or the automation identity: "
            "nobody is requested (fail closed)",
        }
    if found.get("state") != "open":
        return {"ok": True, "skipped": f"#{number} is not open ({found.get('state') or 'unknown'})"}
    author = str(found.get("author") or "")
    if author.lower() == owner.lower():
        return {
            "ok": True,
            "skipped": f"#{number} was opened by the owner {author}: GitHub refuses a review "
            "request to a pull request's author",
        }
    pending = any(
        str(who).lower() == owner.lower() for who in found.get("requested_reviewers") or []
    )
    out: dict[str, Any] = {"ok": True, "owner": owner, "label": label}
    if is_waiting_label(label):
        if pending:
            removed = github.remove_reviewers(repo, int(number), [owner])
            if not removed.get("ok"):
                return {**out, "ok": False, "reason": f"remove: {removed.get('reason') or ''}"}
        requested = github.request_reviewers(repo, int(number), [owner])
        if not requested.get("ok"):
            return {**out, "ok": False, "reason": f"request: {requested.get('reason') or ''}"}
        return {**out, "action": "re-requested" if pending else "requested"}
    if not pending:
        return {**out, "action": "none"}
    removed = github.remove_reviewers(repo, int(number), [owner])
    if not removed.get("ok"):
        return {**out, "ok": False, "reason": f"remove: {removed.get('reason') or ''}"}
    return {**out, "action": "withdrawn"}
