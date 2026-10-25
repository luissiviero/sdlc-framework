"""Orchestrator conventions (build guide step 9; decisions 3, 10, 18).

Everything that names a phase, a human gate, a folder, a branch or a label lives here so every
later step writes to one definition. Sources: docs/OPERATING_MODEL.md sections 3, 4 and 8.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from pathlib import Path
from typing import Any

# --- phases -----------------------------------------------------------------------------
PHASES = ("intent", "design", "build", "test", "deploy", "maintain")
INTENT, DESIGN, BUILD, TEST, DEPLOY, MAINTAIN = PHASES
# R45 (decision 39, row 1): the phases are named after what they produce, as the article's
# stages are (p.4), with (a) as ``intent`` so "plan" means plan.md only. Until plugin 1.0.42
# they were the letters (a) to (f). ``phase_name`` reads a letter as its name wherever a phase
# is read (status.yaml, --phase, branches, labels, sdlc.yaml keys, evidence files) for one
# release; the readers of history (a remote ``sdlc/<id>/<letter>`` branch, a merged change's
# folder) keep reading letters for good (choice 273).
LEGACY_PHASES = dict(zip(("a", "b", "c", "d", "e", "f"), PHASES, strict=True))
PHASE_LETTERS = {name: letter for letter, name in LEGACY_PHASES.items()}
# Not a phase: the end state of a change whose PR the owner closed without merging at a gate
# intent to deploy (decision 25). ``status.yaml: phase: abandoned``; the branches are kept and
# every workflow's guard skips the change. Never a value of ``gate.phase`` or a branch name.
ABANDONED = "abandoned"
# Artifact each phase commits (OPERATING_MODEL section 1; article p.6 lists the artifacts).
PHASE_ARTIFACTS = {
    INTENT: ["intent.md"],
    DESIGN: ["spec.md", "plan.md"],
    BUILD: ["<diff and tests on the build PR>"],
    TEST: ["evidence/"],
    DEPLOY: ["<reviewed PR / release>"],
    MAINTAIN: ["lessons/ (incident record) -> new intent.md"],
}


def phase_name(value: Any) -> Any:
    """The phase name for ``value``: a letter (a) to (f) becomes its name (R45), a name stays
    as it is, and anything else (``review``, ``fix``, ``abandoned``, None) comes back
    unchanged, so every reader can pass what it read through this one function."""
    if isinstance(value, str):
        stripped = value.strip()
        return LEGACY_PHASES.get(stripped, stripped if stripped in PHASES else value)
    return value


# --- the human gates (decisions 18, 30 and 25, as decision 37 narrowed them) --------------
# One profile (decision 37, plugin 1.0.21): the owner's gates are intent, design and deploy,
# shaped by the fast lane (decision 30), and maintain, the triage of each incident intent PR
# (decision 25). The build and test gates are the confidence gate's alone. The Full profile,
# its approval labels and the per-change ``profile_override`` are gone, as Lite was in 0.2.14
# (decision 21).
HUMAN_GATES = frozenset({INTENT, DESIGN, DEPLOY, MAINTAIN})

# --- deferred review (decisions 21 and 32, as decision 37 narrowed them) ------------------
# One review mode: a judgment item of the fixed list always goes to the review panel
# (reviewer, devil's advocate, conciliator, each in a fresh context), the run continues and
# the owner reads the panel's decisions at the next human gate. The ``parked`` mode and the
# per-change ``review_override`` are gone.
#
# The two ``sdlc.yaml`` keys that chose these, ``profile`` and ``review``, are no longer read.
# A file that still carries a value other than the one behaviour is reported once per gate run
# (``retired_settings_note``), never refused, so an old project keeps running.
RETIRED_SETTINGS = {"profile": ("standard", "lite"), "review": ("deferred",)}

CHANGE_TYPES = ("feature", "fix")
ENTRY_ROUTES = ("idea", "ticket", "incident")  # article p.9: idea / ticket / incident
GATE_RESULTS = ("passed", "parked", "approved", "changes-requested")

# --- labels (OPERATING_MODEL section 8) ---------------------------------------------------
LABEL_PREFIX = "sdlc:"
NEEDS_HUMAN_LABEL = "sdlc:needs-human"
# the CI runner's park after a session wrote a field only the owner sets (choice 103, plugin
# 0.2.26): ``ci/run_phase.py`` writes it, ``detect/cli.py finish`` refuses to run over it
OWNER_FIELDS_PARK_PREFIX = "status.yaml: the session wrote owner-only field(s): "
# The detect step's snapshot of the detection record (0.2.27): ``detect/cli.py run`` prints
# the digest of evidence/detection.json before the maintain session, ``finish`` compares.
DETECTION_SNAPSHOT_PARK_PREFIX = "evidence/detection.json changed after the detection step: "
# The second act at gate (e) when `sdlc.yaml: deploy.production` is true (decision 13; build
# guide step 29): the owner applies it on the build PR; the production-gate hook and the
# release workflow read it through the PR, never from an environment variable.
RELEASE_APPROVED_LABEL = "sdlc:release-approved"
# The owner's un-park verbs (decision 24; OPERATING_MODEL section 6): applied on the PR, read
# by the next run (``state/unpark.py``), performed and recorded in ``status.yaml`` with the
# label's actor, then removed from the PR so one application is one act. The CLI commands
# ``set-iterations`` and ``unlock-tests`` stay for by-hand runs, and so does ``accept-risk``:
# its label retired with decision 35 (plugin 1.0.15), since a risk-list hit no longer parks
# and the owner's merge of the PR whose banner shows it accepts it. ``ACCEPT_RISK_LABEL``
# stays only to confirm a ``risk_accepted_by`` entry recorded before then (its label event).
ACCEPT_RISK_LABEL = "sdlc:accept-risk"
RESET_ITERATIONS_LABEL = "sdlc:reset-iterations"
UNLOCK_TESTS_LABEL = "sdlc:unlock-tests"
UNPARK_LABELS = (RESET_ITERATIONS_LABEL, UNLOCK_TESTS_LABEL)
# Phase (f) (build guide steps 37 and 39; decisions 14, 25): ``incident`` marks every intent
# PR the maintain loop opens - the triage queue is the set of open PRs carrying it (p.44
# step 6); ``schedule`` is the owner's "not now" (the PR stays open, nothing runs); ``sdlc:go``
# is the owner's per-incident authorization of a runbook whose route says ``authorization:
# go`` (p.49-50: "shall I run it?" - "Go."), read by ``sdlc-runbook.yml``, performed once,
# recorded with the actor and removed, like the un-park labels.
INCIDENT_LABEL = "incident"
SCHEDULE_LABEL = "schedule"
GO_LABEL = "sdlc:go"
# Decision 29 (plugin 1.0.3, ROADMAP R10): a red target the CI runner finds after the session
# starts the next fix round by itself. While that round runs the PR carries ``sdlc:fixing``
# instead of ``sdlc:needs-human`` (the gate record keeps its failing checks and its ``park``,
# and the check run ``sdlc/<phase>`` stays red): nothing is needed from the owner until the
# iteration cap. ``evidence/auto-round.json`` is the round the runner dispatched;
# ``evidence/auto-reset.json`` the one judged reset of the count at the cap, whose
# ``iterations_reset_by`` names the runner with ``RUNNER_RESET_PREFIX`` (never a label actor).
FIXING_LABEL = "sdlc:fixing"
AUTO_ROUND_FILE = "auto-round.json"
AUTO_RESET_FILE = "auto-reset.json"
RUNNER_RESET_PREFIX = "sdlc-runner:"
# the start of ``status.yaml: parked_reason`` while an automatic round runs
FIXING_PARK_PREFIX = "automatic fix round "
# Decision 30 (the fast lane, ROADMAP R46): the runner closes the owner's intent PR once the
# design PR carries it, and the design PR once the build PR carries it, each after labelling
# it ``sdlc:superseded`` (no comment, decision 20). ``sdlc-abandon.yml`` skips a closed PR
# with this label, so a close that supersedes never abandons the change (decision 25).
SUPERSEDED_LABEL = "sdlc:superseded"


def ready_label(phase: str) -> str:
    """Set whenever a run stops at a human gate and waits for the owner: ``sdlc:<name>-ready``
    (R45; a letter is read as its name)."""
    return f"{LABEL_PREFIX}{_check_phase(phase)}-ready"


def legacy_ready_label(phase: str) -> str:
    """The label ``ready_label`` gave before R45 (``sdlc:c-ready``), read for one release on a
    PR an older plugin labelled."""
    return f"{LABEL_PREFIX}{PHASE_LETTERS[_check_phase(phase)]}-ready"


def ready_labels(phase: str) -> frozenset[str]:
    """The labels that say a PR waits at ``phase``'s gate: the name's and, for one release,
    the letter's."""
    return frozenset({ready_label(phase), legacy_ready_label(phase)})


READY_LABEL_RE = re.compile(rf"^{LABEL_PREFIX}(?P<phase>[a-f]|{'|'.join(PHASES)})-ready$")


def ready_label_phase(label: str) -> str | None:
    """The phase name a waiting label names (``sdlc:build-ready``, or ``sdlc:c-ready`` from an
    older plugin), or None for any other label."""
    m = READY_LABEL_RE.match(str(label))
    return phase_name(m.group("phase")) if m else None


def runner_labels() -> list[str]:
    """The labels only the CI runner applies, beside the gate and owner set of ``all_labels``
    (decision 29: ``sdlc:fixing`` while an automatic fix round runs). ``ensure_labels`` creates
    both; ``state/cli.py labels`` prints the documented set."""
    return [FIXING_LABEL]


def all_labels() -> list[str]:
    labels = [ready_label(p) for p in PHASES]
    labels.append(RELEASE_APPROVED_LABEL)
    labels += list(UNPARK_LABELS)
    labels.append(NEEDS_HUMAN_LABEL)
    labels += [INCIDENT_LABEL, SCHEDULE_LABEL, GO_LABEL]
    return labels


# --- branches -----------------------------------------------------------------------------
# R45: ``sdlc/<id>/<name>``; a letter branch (``sdlc/<id>/c``) is read as its phase for good,
# since remote branches are never renamed (choice 273): a change in flight keeps its branch.
BRANCH_RE = re.compile(rf"^sdlc/(?P<id>\d{{4}})/(?P<phase>[a-f]|{'|'.join(PHASES)})$")


def branch_name(change_id: str, phase: str) -> str:
    _check_id(change_id)
    return f"sdlc/{change_id}/{_check_phase(phase)}"


def legacy_branch_name(change_id: str, phase: str) -> str:
    """The branch an older plugin cut for ``phase`` (``sdlc/<id>/c``): a change in flight
    when its project moved past plugin 1.0.42 finishes on it."""
    _check_id(change_id)
    return f"sdlc/{change_id}/{PHASE_LETTERS[_check_phase(phase)]}"


def branch_names(change_id: str, phase: str) -> tuple[str, str]:
    """``(name, letter)`` branches of ``phase``: the one this plugin cuts, then the one an
    older plugin cut; a reader looks for both, the name first."""
    return branch_name(change_id, phase), legacy_branch_name(change_id, phase)


def parse_branch(name: str) -> tuple[str, str] | None:
    """``(id, phase name)`` for ``sdlc/<id>/<name>`` or ``sdlc/<id>/<letter>``, else None."""
    m = BRANCH_RE.match(name.strip())
    return (m.group("id"), phase_name(m.group("phase"))) if m else None


# Which branch a phase actually works on (OPERATING_MODEL section 8): intent carries the intent
# PR, design the spec+plan PR, and build "the build PR that stays open through test and
# deploy", so the test and deploy runs commit on sdlc/<id>/build, never on a branch of their
# own. Maintain produces a new intent, which is intent work of that change.
WORK_PHASE = {
    INTENT: INTENT,
    DESIGN: DESIGN,
    BUILD: BUILD,
    TEST: BUILD,
    DEPLOY: BUILD,
    MAINTAIN: INTENT,
}


def work_branch(change_id: str, phase: str) -> str:
    """The branch a run of ``phase`` commits on (``branch_name`` stays the literal name)."""
    return branch_name(change_id, WORK_PHASE[_check_phase(phase)])


def work_branches(change_id: str, phase: str) -> tuple[str, str]:
    """``(name, letter)`` of the branch a run of ``phase`` commits on (``branch_names``)."""
    return branch_names(change_id, WORK_PHASE[_check_phase(phase)])


def phase_file(directory: Path | str, pattern: str, phase: str, **fields: Any) -> Path:
    """The file ``pattern`` names for ``phase`` in ``directory`` (``gate-{phase}.json``,
    ``{phase}-{n}-reviewer.md``): the name's (``gate-build.json``), unless only the letter's
    exists (``gate-c.json``, written by a plugin before R45), which is then read. A writer
    takes the name's always: ``Path(directory) / pattern.format(phase=name)``. A run that is
    not a phase (``review``, ``fix``) has one name and its file is returned as it is."""
    name = phase_name(phase)
    path = Path(directory) / pattern.format(phase=name, **fields)
    if path.exists() or name not in PHASES:
        return path
    legacy = Path(directory) / pattern.format(phase=PHASE_LETTERS[name], **fields)
    return legacy if legacy.exists() else path


# --- change folder ------------------------------------------------------------------------
CHANGES_DIR = "changes"
REVIEW_SEEN_FILE = ".review-seen.json"  # changes/.review-seen.json: the review pass's record


def review_seen_rel() -> str:
    """``changes/.review-seen.json`` relative to the project root: the project's record of
    review findings, written by ``review/cli.py validate`` right before the gate whose
    ``findings`` check reads the findings file in the change's ``evidence/``. It lives
    outside the change folder (one file per project), so until 0.3.5 the gate's
    ``clean_tree`` read it as uncommitted work and every fix round of change 0001 at gate (e)
    parked on it (2026-10-03). Now, at (d) and (e), ``commit-phase`` carries it with the
    change folder and ``clean_tree`` sets it aside."""
    return f"{CHANGES_DIR}/{REVIEW_SEEN_FILE}"


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


TRIM_CHARS = " .,;:!?-([{"


def truncate_words(text: str, limit: int) -> str:
    """``text`` (whitespace collapsed) cut to at most ``limit`` characters at the last word
    boundary, with no trailing whitespace or punctuation after the cut (pull request and
    commit titles: the live runs of 2026-09-25 cut titles mid-word). A text within the limit
    is returned whole; a single word longer than ``limit`` is hard-cut. When the cut leaves
    only trim characters the hard cut is used, trimmed as well; ``limit <= 0`` gives ""."""
    if limit <= 0:
        return ""
    text = " ".join(str(text).split())
    if len(text) <= limit:
        return text
    cut = text[: limit + 1]  # one more: a space right at the limit keeps the last word whole
    space = cut.rfind(" ")
    short = cut[:space] if space > 0 else text[:limit]
    return short.rstrip(TRIM_CHARS) or text[:limit].rstrip(TRIM_CHARS)


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


def _check_phase(phase: str) -> str:
    """``phase``'s name (a letter is read as its name, R45), or ValueError."""
    name = phase_name(phase)
    if name not in PHASES:
        raise ValueError(f"unknown phase {phase!r}; expected one of {PHASES}")
    return name


def _check_id(change_id: str) -> None:
    if not ID_RE.match(change_id):
        raise ValueError(f"change id must be four digits, got {change_id!r}")


def is_human_gate(phase: str) -> bool:
    return _check_phase(phase) in HUMAN_GATES


def retired_settings_note(config: Mapping[str, Any]) -> str:
    """One line naming each ``sdlc.yaml`` key decision 37 retired that still holds another
    behaviour (``profile: full``, ``review: parked``), or ``""``. The key is not read: the
    change runs as ``standard`` with deferred review, and the note says so."""
    stale = [
        f"{key}: {config[key]}"
        for key, kept in RETIRED_SETTINGS.items()
        if config.get(key) not in (None, "", *kept)
    ]
    if not stale:
        return ""
    return (
        f"sdlc.yaml: {', '.join(stale)} is no longer read (decision 37): the change runs on "
        "the one profile with deferred review; the owner removes the key"
    )
