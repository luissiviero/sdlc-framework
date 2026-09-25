"""The gated routes of the 3σ tier (build guide step 37; decisions 14 and 26; article p.43
step 3 "at 3σ Claude may act, though only by opening a PR into the review gate or triggering
a pre-approved runbook", p.44 governance "the runbooks the agent may trigger were approved
in advance").

Every route is one of two authorization models, written per route in ``bands.yaml``
(decision 14, split by blast radius): ``preapproved`` (CI-scoped and reversible: the intent
PR, quarantining a flaky test, a revert PR) runs with no human in the path; ``go`` (anything
that touches a running system: a rollback, a config change) parks the incident PR with "Go"
requested, and the owner's ``sdlc:go`` label runs it (``sdlc-runbook.yml``). Decision 26
amends one case: on a project with ``deploy.production: true``, a rollback runbook the owner
has rehearsed (``sdlc.yaml: maintain.runbooks[].rehearsed_at`` set to a date) is
pre-approved - the p.49 figure makes the rehearsal the precondition, and a "Go" that waits
silently in the queue brings back the missed alert the loop exists to remove.

The diagnosis proposes; this module judges. ``authorization()`` resolves the route's
effective authorization, ``validate_proposal()`` says whether a ``proposal.json`` may be
acted on at the finding's tier, and ``available()`` lists what the diagnosis may propose.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any

PULL_REQUEST = "pull_request"
RUNBOOK_PREFIX = "runbook:"
PREAPPROVED, GO = "preapproved", "go"
AUTHORIZATIONS = (PREAPPROVED, GO)
# The runbooks the plugin ships (CI-scoped, reversible, p.45 "the agent quarantines the flaky
# test or opens a revert PR, and the review gate decides"); a project adds its own under
# ``sdlc.yaml: maintain.runbooks`` with a ``command``.
BUILTIN_RUNBOOKS = {
    "quarantine-flaky-test": {
        "args": {"test": "the pytest node id, e.g. tests/test_x.py::test_y"},
        "languages": ("python",),
        "what": "adds --deselect <node id> to pytest's addopts on a branch and opens the PR; "
        "never edits the test itself",
    },
    "revert-pr": {
        "args": {"sha": "the full sha of the commit on the default branch to revert"},
        "languages": (),
        "what": "git revert on a branch from the default branch and opens the PR; never merges",
    },
}
ROLLBACK_RE = re.compile(r"(?i)rollback")
PROPOSAL_SCHEMA_VERSION = 1
TIER_ROUTES = {2: (PULL_REQUEST,)}  # tier 2 diagnoses; the intent PR is its only route


@dataclass
class Resolved:
    route: str
    authorization: str
    source: str  # where the authorization came from, for the record
    runbook: str | None = None
    project_runbook: dict[str, Any] | None = None  # the sdlc.yaml entry, when there is one
    builtin: bool = False
    supported: bool = True
    note: str = ""
    rehearsed_at: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "route": self.route,
            "authorization": self.authorization,
            "source": self.source,
            "runbook": self.runbook,
            "builtin": self.builtin,
            "supported": self.supported,
            "note": self.note,
            "rehearsed_at": self.rehearsed_at,
        }


@dataclass
class Proposal:
    tier: int
    route: str
    args: dict[str, Any] = field(default_factory=dict)
    rationale: str = ""

    @property
    def runbook(self) -> str | None:
        return self.route[len(RUNBOOK_PREFIX) :] if self.route.startswith(RUNBOOK_PREFIX) else None

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema_version": PROPOSAL_SCHEMA_VERSION,
            "tier": self.tier,
            "route": self.route,
            "args": dict(self.args),
            "rationale": self.rationale,
        }


def runbook_name(route: str) -> str | None:
    return route[len(RUNBOOK_PREFIX) :] if route.startswith(RUNBOOK_PREFIX) else None


def project_runbooks(config: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """``sdlc.yaml: maintain.runbooks`` by name (entries without a name are skipped)."""
    maintain = config.get("maintain") if isinstance(config.get("maintain"), dict) else {}
    out: dict[str, dict[str, Any]] = {}
    for entry in maintain.get("runbooks") or []:
        if isinstance(entry, dict) and isinstance(entry.get("name"), str) and entry["name"]:
            out[entry["name"].strip()] = entry
    return out


def production_declared(config: dict[str, Any]) -> bool:
    deploy = config.get("deploy") if isinstance(config.get("deploy"), dict) else {}
    return deploy.get("production") is True


def rehearsed(entry: dict[str, Any] | None) -> str | None:
    """The ``rehearsed_at`` date of a runbook entry when it is a real date, else None."""
    if not entry:
        return None
    value = entry.get("rehearsed_at")
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, str) and value.strip():
        try:
            return date.fromisoformat(value.strip()[:10]).isoformat()
        except ValueError:
            return None
    return None


def authorization(route: str, bands_route: Any, config: dict[str, Any], language: str) -> Resolved:
    """Resolve one route (decision 14 as written in bands.yaml, decision 26 on top).

    ``bands_route`` is ``bands.Route`` (``name``, ``authorization``) or None when bands.yaml
    does not list the route - then it is never taken. The bands' value stands unless the
    project's own ``maintain.runbooks`` entry of the same name says ``go`` (the stricter
    wins), and a rehearsed rollback on a declared production is pre-approved whatever the
    two files say (decision 26)."""
    if bands_route is None:
        return Resolved(route, GO, "not listed in bands.yaml", supported=False,
                        note="a route not listed in bands.yaml is never taken")  # fmt: skip
    auth = str(getattr(bands_route, "authorization", GO) or GO)
    source = "bands.yaml"
    name = runbook_name(route)
    if name is None:
        return Resolved(route, auth, source)
    entry = project_runbooks(config).get(name)
    builtin = name in BUILTIN_RUNBOOKS
    resolved = Resolved(route, auth, source, runbook=name, project_runbook=entry, builtin=builtin)
    if entry is not None and str(entry.get("authorization") or "").strip() == GO and auth != GO:
        resolved.authorization, resolved.source = GO, "sdlc.yaml: maintain.runbooks (stricter)"
    if builtin:
        langs = BUILTIN_RUNBOOKS[name]["languages"]
        if langs and language not in langs:
            resolved.supported = False
            resolved.note = f"the {name} runbook supports {', '.join(langs)} projects only"
    elif entry is None or not str(entry.get("command") or "").strip():
        resolved.supported = False
        resolved.note = (
            f"no runbook named {name!r} with a command under sdlc.yaml: maintain.runbooks"
        )
    stamp = rehearsed(entry)
    if (
        resolved.authorization == GO
        and ROLLBACK_RE.search(name)
        and production_declared(config)
        and stamp
    ):
        resolved.authorization = PREAPPROVED
        resolved.source = f"decision 26: rollback rehearsed on {stamp} on a declared production"
        resolved.rehearsed_at = stamp
    return resolved


FORCED_SOURCE = "a forced finding (a rehearsal) never pre-approves a runbook: Go required"


def apply_forced(resolved: Resolved | None, forced: bool) -> Resolved | None:
    """A rehearsal (``detection.json: forced``) has no breach behind it: decision 26's
    pre-approval and a bands ``preapproved`` are for a real 3σ, so every runbook route of a
    forced finding waits for the owner's Go (the intent PR is still opened)."""
    if resolved is not None and forced and resolved.runbook:
        resolved.authorization = GO
        resolved.source = FORCED_SOURCE
        resolved.rehearsed_at = None
    return resolved


def available(bands: Any, config: dict[str, Any], language: str, tier: int) -> list[Resolved]:
    """The routes the diagnosis may propose at this tier, resolved."""
    if tier < 2:
        return []
    allowed = TIER_ROUTES.get(tier)
    out = []
    for route in bands.routes():
        if allowed is not None and route.name not in allowed:
            continue
        out.append(authorization(route.name, route, config, language))
    if tier == 2 and not any(r.route == PULL_REQUEST for r in out):
        # the intent PR is the diagnosis's own artifact: it needs no bands entry to exist
        out.append(Resolved(PULL_REQUEST, PREAPPROVED, "the incident intent PR (p.44 step 5)"))
    return out


def load_proposal(path: Path) -> tuple[Proposal | None, str]:
    path = Path(path)
    if not path.is_file():
        return None, f"{path.name} is missing"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return None, f"{path.name} unreadable: {exc}"
    if not isinstance(data, dict):
        return None, f"{path.name} is not a JSON object"
    route = data.get("route")
    if not isinstance(route, str) or not route.strip():
        return None, f"{path.name}: route is missing"
    tier = data.get("tier")
    if isinstance(tier, bool) or not isinstance(tier, int):
        return None, f"{path.name}: tier is not an integer"
    args = data.get("args") if isinstance(data.get("args"), dict) else {}
    rationale = str(data.get("rationale") or "")
    return Proposal(tier, route.strip(), dict(args), rationale), ""


def validate_proposal(
    proposal: Proposal, detection_tier: int, bands: Any, config: dict[str, Any], language: str
) -> tuple[Resolved | None, str]:
    """(the resolved route, "") when the proposal may be acted on, else (None, why)."""
    if proposal.tier != detection_tier:
        return None, (
            f"the proposal says tier {proposal.tier}, the detection record says {detection_tier}"
        )
    if detection_tier < 2:
        return None, f"tier {detection_tier} proposes nothing"
    allowed = TIER_ROUTES.get(detection_tier)
    if allowed is not None and proposal.route not in allowed:
        return None, (
            f"tier {detection_tier} may only take {', '.join(allowed)}; "
            f"{proposal.route} is a tier-3 route"
        )
    if proposal.route == PULL_REQUEST:
        listed = bands.route(PULL_REQUEST)
        if listed is None and detection_tier == 3:
            return None, "pull_request is not a route of the 3sigma tier in bands.yaml"
        return Resolved(PULL_REQUEST, PREAPPROVED, "the incident intent PR (p.44 step 5)"), ""
    listed = bands.route(proposal.route)
    if listed is None:
        return None, f"{proposal.route} is not a route of the 3sigma tier in bands.yaml"
    resolved = authorization(proposal.route, listed, config, language)
    if not resolved.supported:
        return None, resolved.note
    name = resolved.runbook or ""
    if resolved.builtin:
        missing = [k for k in BUILTIN_RUNBOOKS[name]["args"] if not str(proposal.args.get(k) or "")]
        if missing:
            return None, f"{proposal.route} needs args {', '.join(missing)}"
    return resolved, ""
