"""Orchestrator conventions (build guide step 9; decisions 3, 10, 18).

Everything that names a phase, a profile, a folder, a branch or a label lives here so every
later step writes to one definition. Sources: docs/OPERATING_MODEL.md sections 3, 4 and 8.
"""

from __future__ import annotations

import re
from pathlib import Path

# --- phases -----------------------------------------------------------------------------
PHASES = ("a", "b", "c", "d", "e", "f")
PHASE_NAMES = {
    "a": "plan",
    "b": "design",
    "c": "build",
    "d": "test",
    "e": "deploy",
    "f": "maintain",
}
# Artifact each phase commits (OPERATING_MODEL section 1; article p.6 lists the artifacts).
PHASE_ARTIFACTS = {
    "a": ["intent.md"],
    "b": ["spec.md", "plan.md"],
    "c": ["<diff and tests on the build PR>"],
    "d": ["evidence/"],
    "e": ["<reviewed PR / release>"],
    "f": ["lessons/ (incident record) -> new intent.md"],
}

# --- profiles (decision 18; OPERATING_MODEL section 3) ------------------------------------
PROFILES = ("standard", "full", "lite")
DEFAULT_PROFILE = "standard"
HUMAN_GATES = {
    "standard": frozenset({"a", "b", "e"}),
    "full": frozenset({"a", "b", "c", "d", "e"}),
    "lite": frozenset({"a", "e"}),
}

CHANGE_TYPES = ("feature", "fix")
ENTRY_ROUTES = ("idea", "ticket", "incident")  # article p.9: idea / ticket / incident
GATE_RESULTS = ("passed", "parked", "approved", "changes-requested")

# --- labels (OPERATING_MODEL section 8) ---------------------------------------------------
LABEL_PREFIX = "sdlc:"
NEEDS_HUMAN_LABEL = "sdlc:needs-human"
# The second act at gate (e) when `sdlc.yaml: deploy.production` is true (decision 13; build
# guide step 29): the owner applies it on the build PR; the production-gate hook and the
# release workflow read it through the PR, never from an environment variable.
RELEASE_APPROVED_LABEL = "sdlc:release-approved"


def ready_label(phase: str) -> str:
    """Set whenever a run stops at a human gate and waits for the owner."""
    _check_phase(phase)
    return f"{LABEL_PREFIX}{phase}-ready"


def approved_label(phase: str) -> str:
    """Full profile only: the owner's approving review + this label passes gate (c)/(d)."""
    _check_phase(phase)
    return f"{LABEL_PREFIX}{phase}-approved"


def all_labels() -> list[str]:
    labels = [ready_label(p) for p in PHASES]
    labels += [approved_label(p) for p in ("c", "d")]
    labels.append(RELEASE_APPROVED_LABEL)
    labels.append(NEEDS_HUMAN_LABEL)
    return labels


# --- branches -----------------------------------------------------------------------------
BRANCH_RE = re.compile(r"^sdlc/(?P<id>\d{4})/(?P<phase>[a-f])$")


def branch_name(change_id: str, phase: str) -> str:
    _check_id(change_id)
    _check_phase(phase)
    return f"sdlc/{change_id}/{phase}"


def parse_branch(name: str) -> tuple[str, str] | None:
    m = BRANCH_RE.match(name.strip())
    return (m.group("id"), m.group("phase")) if m else None


# Which branch a phase actually works on (OPERATING_MODEL section 8): (a) carries the intent
# PR, (b) the spec+plan PR, and (c) "the build PR that stays open through (d) and (e)" — so
# the test and deploy runs commit on sdlc/<id>/c, never on a branch of their own. Phase (f)
# produces a new intent, which is phase (a) work of that change.
WORK_PHASE = {"a": "a", "b": "b", "c": "c", "d": "c", "e": "c", "f": "a"}


def work_branch(change_id: str, phase: str) -> str:
    """The branch a run of ``phase`` commits on (``branch_name`` stays the literal name)."""
    _check_phase(phase)
    return branch_name(change_id, WORK_PHASE[phase])


# --- change folder ------------------------------------------------------------------------
CHANGES_DIR = "changes"
ID_RE = re.compile(r"^\d{4}$")
INIT_CHANGE_ID = "0000"  # reserved for the framework's own installation PR (step 21)
DIR_RE = re.compile(r"^(?P<id>\d{4})-(?P<slug>[a-z0-9]+(?:-[a-z0-9]+)*)$")


def slugify(title: str, max_len: int = 40) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    if not s:
        s = "change"  # e.g. a title written entirely in non-Latin script
    if len(s) > max_len:
        s = s[:max_len].rstrip("-")
    return s


def change_dir_name(change_id: str, slug: str) -> str:
    _check_id(change_id)
    if not DIR_RE.match(f"{change_id}-{slug}"):
        raise ValueError(f"invalid slug: {slug!r}")
    return f"{change_id}-{slug}"


def list_change_dirs(project_root: Path) -> list[Path]:
    root = Path(project_root) / CHANGES_DIR
    if not root.is_dir():
        return []
    return sorted(p for p in root.iterdir() if p.is_dir() and DIR_RE.match(p.name))


def next_change_id(project_root: Path, extra_ids: list[str] | None = None) -> str:
    """Zero-padded sequence: max known id + 1, starting at 0001 (0000 is /sdlc-init).
    ``extra_ids`` lets the caller add ids seen elsewhere (remote sdlc/<id>/* branches), so
    a change started on the PC and one started in a cloud session do not collide."""
    ids = [int(DIR_RE.match(p.name).group("id")) for p in list_change_dirs(project_root)]
    ids += [int(i) for i in (extra_ids or []) if i.isdigit()]
    return f"{(max(ids) if ids else 0) + 1:04d}"


def find_change_dir(project_root: Path, change_id: str) -> Path | None:
    _check_id(change_id)
    for p in list_change_dirs(project_root):
        if p.name.startswith(change_id + "-"):
            return p
    return None


def _check_phase(phase: str) -> None:
    if phase not in PHASES:
        raise ValueError(f"unknown phase {phase!r}; expected one of {PHASES}")


def _check_id(change_id: str) -> None:
    if not ID_RE.match(change_id):
        raise ValueError(f"change id must be four digits, got {change_id!r}")


def effective_profile(project_profile: str | None, override: str | None) -> str:
    profile = override or project_profile or DEFAULT_PROFILE
    if profile not in PROFILES:
        raise ValueError(f"unknown profile {profile!r}; expected one of {PROFILES}")
    return profile


def is_human_gate(profile: str, phase: str) -> bool:
    _check_phase(phase)
    return phase in HUMAN_GATES[effective_profile(profile, None)]
