"""``changes/<id>-<slug>/status.yaml`` — the per-change state file (step 9, decision 10).

Fields (OPERATING_MODEL section 8): phase, profile override, change type feature/fix,
gate result, parked reason, iteration count. Added for traceability: id, slug, title,
entry route (article p.9), external_ref (decision 9 linkage: issue number), timestamps.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from . import conventions as c
from . import yamlish

STATUS_FILE = "status.yaml"
SCHEMA_VERSION = 1


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


@dataclass
class Gate:
    phase: str | None = None  # gate the result refers to
    result: str | None = None  # one of conventions.GATE_RESULTS
    reason: str | None = None
    at: str | None = None


@dataclass
class Status:
    id: str
    slug: str
    title: str
    # The phase the change is in. On the default branch a change at phase e was merged by the
    # owner, and that merge is the whole of gate (e) (decision 13): ``read_status(...,
    # on_default_branch=True)`` derives gate e/passed from it (``merged_at_gate_e``) without
    # rewriting the file, because the automation identity never writes to the default branch.
    phase: str = "a"
    entry_route: str = "idea"
    change_type: str = "feature"
    profile_override: str | None = None
    gate: Gate = field(default_factory=Gate)
    parked_reason: str | None = None
    iterations: int = 0
    external_ref: str | None = None
    # risk-list items the owner has accepted for this change (gate check `risk_list`, step 16):
    # the change touches them knowingly; the gate no longer parks on them.
    risk_accepted: list[str] = field(default_factory=list)
    # test-file lock (build guide step 25; article p.28 step 4, p.35): set by the build run of a
    # fix-type change once the reproducing test is committed. While true the PreToolUse hook
    # denies every edit under `sdlc.yaml: test_paths` on the change's sdlc/<id>/(c|d|e) branch.
    # Only the owner clears it (`state/cli.py unlock-tests`), in a reviewed PR.
    tests_locked: bool = False
    # The owner's un-park verbs as labels (decision 24; build guide step 9): who applied the
    # label the run performed, per risk item (``[{item, actor}]``: a risk item may carry a
    # space, which a mapping key cannot here) / for the last iteration reset / for the last
    # unlock, as GitHub recorded the actor. A CLI command run by hand leaves these unset: the
    # gate's ``owner_actions`` check reads the commit author for those (PROGRESS choice 17)
    # and these fields for a label act a CI run committed under the automation identity.
    risk_accepted_by: list[dict[str, str]] = field(default_factory=list)
    iterations_reset_by: str | None = None
    tests_unlocked_by: str | None = None
    # Decision 25: the PR of gate (a)-(e) was closed without a merge; why, and when.
    abandoned_reason: str | None = None
    created_at: str = field(default_factory=_now)
    updated_at: str = field(default_factory=_now)
    schema_version: int = SCHEMA_VERSION

    # -- validation ---------------------------------------------------------------------
    def validate(self) -> None:
        c.change_dir_name(self.id, self.slug)
        if self.phase not in c.PHASES and self.phase != c.ABANDONED:
            raise ValueError(
                f"phase must be one of {c.PHASES} or {c.ABANDONED!r}, got {self.phase!r}"
            )
        if self.entry_route not in c.ENTRY_ROUTES:
            raise ValueError(f"entry_route must be one of {c.ENTRY_ROUTES}")
        if self.change_type not in c.CHANGE_TYPES:
            raise ValueError(f"change_type must be one of {c.CHANGE_TYPES}")
        if self.profile_override is not None and self.profile_override not in c.PROFILES:
            raise ValueError(f"profile_override must be one of {c.PROFILES} or null")
        if self.gate.result is not None and self.gate.result not in c.GATE_RESULTS:
            raise ValueError(f"gate.result must be one of {c.GATE_RESULTS} or null")
        if self.gate.phase is not None and self.gate.phase not in c.PHASES:
            raise ValueError("gate.phase must be a phase letter or null")
        if (
            isinstance(self.iterations, bool)
            or not isinstance(self.iterations, int)
            or self.iterations < 0
        ):
            raise ValueError("iterations must be a non-negative integer")
        if not self.title.strip():
            raise ValueError("title must not be empty")
        if not isinstance(self.risk_accepted, list) or not all(
            isinstance(r, str) and r.strip() for r in self.risk_accepted
        ):
            raise ValueError("risk_accepted must be a list of non-empty strings")
        if not isinstance(self.tests_locked, bool):
            raise ValueError("tests_locked must be a boolean")
        if not isinstance(self.risk_accepted_by, list) or not all(
            isinstance(e, dict)
            and set(e) == {"item", "actor"}
            and all(isinstance(v, str) and v.strip() for v in e.values())
            for e in self.risk_accepted_by
        ):
            raise ValueError("risk_accepted_by must be a list of {item, actor} entries")
        for name in ("iterations_reset_by", "tests_unlocked_by", "abandoned_reason"):
            value = getattr(self, name)
            if value is not None and (not isinstance(value, str) or not value.strip()):
                raise ValueError(f"{name} must be a non-empty string or null")

    # -- (de)serialisation --------------------------------------------------------------
    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["gate"] = asdict(self.gate)
        return d

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> Status:
        d = dict(d)
        gate = d.pop("gate", None) or {}
        known = {f for f in cls.__dataclass_fields__}
        unknown = set(d) - known
        if unknown:
            raise ValueError(f"unknown status.yaml keys: {sorted(unknown)}")
        st = cls(gate=Gate(**gate), **d)
        if stale_park(st):
            st.parked_reason = None
        st.validate()
        return st

    # -- mutations ----------------------------------------------------------------------
    def touch(self) -> None:
        self.updated_at = _now()

    def set_phase(self, phase: str) -> None:
        if phase not in c.PHASES:
            raise ValueError(f"phase must be one of {c.PHASES}, got {phase!r}")
        if self.phase == c.ABANDONED:
            raise ValueError(f"change {self.id} is abandoned; it does not re-enter a phase")
        self.phase = phase
        self.parked_reason = None
        self.touch()
        self.validate()

    @property
    def abandoned(self) -> bool:
        return self.phase == c.ABANDONED

    def abandon(self, reason: str) -> None:
        """The owner closed the change's PR without merging (decision 25): the change ends
        here. The park, if any, is left behind; the gate record is kept as it was; the
        branches stay. Idempotent: a second close changes nothing but the reason."""
        reason = reason.strip() or "pull request closed without a merge"
        if self.abandoned and self.abandoned_reason == reason:
            return  # a second close: the file stays as it is
        self.phase = c.ABANDONED
        self.abandoned_reason = reason
        self.parked_reason = None
        self.touch()
        self.validate()

    def record_owner_label(self, label: str, actor: str, items: list[str] | None = None) -> None:
        """Perform one of the owner's un-park labels (decision 24) and record who applied it.
        ``items`` are the risk-list items an ``sdlc:accept-risk`` accepts (the hits the last
        gate reported); the other two labels carry no argument."""
        actor = actor.strip()
        if not actor:
            raise ValueError("an owner label needs its actor")
        if label == c.ACCEPT_RISK_LABEL:
            for item in items or []:
                self.accept_risk(item)
                self.risk_accepted_by = [
                    e for e in self.risk_accepted_by if e["item"] != item.strip()
                ] + [{"item": item.strip(), "actor": actor}]
        elif label == c.RESET_ITERATIONS_LABEL:
            self.iterations = 0
            self.iterations_reset_by = actor
        elif label == c.UNLOCK_TESTS_LABEL:
            self.tests_locked = False
            self.tests_unlocked_by = actor
        else:
            raise ValueError(f"{label} is not an owner label ({', '.join(c.UNPARK_LABELS)})")
        self.touch()
        self.validate()

    def record_gate(self, phase: str, result: str, reason: str | None = None) -> None:
        """A gate result replaces the previous one, park included: a gate that passes after
        a park lifts it (the first fix round of change 0001 on the sample repository,
        2026-09-22, left the old reason behind a ``passed`` result, and the next phase's CI
        guard would have skipped the change as parked)."""
        self.gate = Gate(phase=phase, result=result, reason=reason, at=_now())
        self.parked_reason = reason if result == "parked" else None
        self.touch()
        self.validate()

    def park(self, reason: str, phase: str | None = None) -> None:
        """Park, never page (decision 11): record why and wait in the review queue. ``phase``
        is the gate that parked (defaults to the change's current phase)."""
        self.record_gate(phase or self.phase, "parked", reason)

    def lock_tests(self) -> None:
        """The reproducing test of a fix-type change is committed: freeze the test paths."""
        self.tests_locked = True
        self.touch()
        self.validate()

    def unlock_tests(self) -> None:
        """Owner-only (the test itself was wrong): thaw the test paths for this change."""
        self.tests_locked = False
        self.touch()
        self.validate()

    def bump_iteration(self) -> int:
        self.iterations += 1
        self.touch()
        return self.iterations

    def accept_risk(self, item: str) -> None:
        """The owner accepts a risk-list hit for this change (recorded, never inferred)."""
        item = item.strip()
        if item and item not in self.risk_accepted:
            self.risk_accepted.append(item)
        self.touch()
        self.validate()


def stale_park(st: Status) -> str | None:
    """The ``parked_reason`` a later gate result already lifted, or None.

    A park is a gate result (``park`` records one), so a reason beside any other result is
    a leftover: plugins before 0.2.6 kept it when a gate passed after a park, and the file
    the design PR merged into the sample repository's main (change 0001, 2026-09-22) still
    carries it. Every reader goes through ``from_dict``, so the guard, ``show``, ``list``
    and the preflight agree on it; nothing else is asked to judge the raw field.
    """
    if st.parked_reason and st.gate.result != "parked":
        return st.parked_reason
    return None


def status_path(change_dir: Path) -> Path:
    return Path(change_dir) / STATUS_FILE


def _load(change_dir: Path) -> dict[str, Any]:
    data = yamlish.load_file(status_path(change_dir))
    if not isinstance(data, dict):
        raise ValueError(f"{status_path(change_dir)} is not a mapping")
    return data


MERGED_AT_GATE_E_REASON = "merged by the owner: gate (e) is the merge (decision 13)"
# With ``sdlc.yaml: deploy.production`` true the phase gate is still passed by the merge (the
# change is done and merged), but the release needs a second act the release workflow checks.
MERGED_AT_GATE_E_PRODUCTION_REASON = (
    MERGED_AT_GATE_E_REASON + "; the release approval sdlc:release-approved is the release "
    "workflow's second act on this declared production"
)


def merged_at_gate_e(st: Status, production: bool = False) -> Status:
    """The status as the owner's merge of the build PR left it: gate (e) passed.

    Pure: returns a new ``Status`` and never touches ``st`` or the file. A change at phase e
    whose ``status.yaml`` sits on the default branch reached it through the owner's merge of
    the build PR, and that merge is the whole of gate (e) (decision 13; OPERATING_MODEL
    section 4). The last run on the branch may have parked (the thirteenth live run parked
    change 0001 on the iteration cap and the owner merged anyway), so the park is lifted and
    the gate reads e/passed, stamped with the file's ``updated_at``. Anything else (another
    phase, or gate (e) already passed) comes back as an unchanged copy. ``production`` is
    ``sdlc.yaml: deploy.production``: when true the gate still reads passed (the change is
    done and merged), but the reason says the release label is the second act, which is the
    release workflow's to check, not this function's.
    """
    derived = Status.from_dict(st.to_dict())
    if st.phase != "e" or (st.gate.phase == "e" and st.gate.result == "passed"):
        # an abandoned change (decision 25) never reads as merged: its phase is not e
        return derived
    reason = MERGED_AT_GATE_E_PRODUCTION_REASON if production else MERGED_AT_GATE_E_REASON
    derived.gate = Gate(phase="e", result="passed", reason=reason, at=st.updated_at)
    derived.parked_reason = None
    return derived


def read_status(
    change_dir: Path, on_default_branch: bool = False, production: bool = False
) -> Status:
    """``status.yaml`` of the change. ``on_default_branch`` says the file was read from a
    checkout of the default branch: a change at phase e there was merged by the owner, so
    gate (e) reads passed (``merged_at_gate_e``; ``production`` is ``sdlc.yaml:
    deploy.production`` and only changes the derived reason). The derivation happens in
    memory only; the file on disk is never rewritten by it (the default branch is read-only
    for automation, and only the owner's reviewed PRs reach it)."""
    st = Status.from_dict(_load(change_dir))
    return merged_at_gate_e(st, production=production) if on_default_branch else st


def lift_stale_park(change_dir: Path) -> str | None:
    """Rewrite ``status.yaml`` when its park was lifted by a later gate result, so a session
    that reads the file itself sees what every reader sees. Returns the lifted reason, or
    None when the file already says what ``read_status`` says (idempotent)."""
    data = _load(change_dir)
    st = Status.from_dict(data)
    raw = data.get("parked_reason")
    if raw and st.parked_reason is None:
        write_status(change_dir, st)
        return str(raw)
    return None


def write_status(change_dir: Path, status: Status) -> Path:
    status.validate()
    path = status_path(change_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    yamlish.dump_file(path, status.to_dict())
    return path


def new_change(
    project_root: Path,
    title: str,
    entry_route: str = "idea",
    change_type: str = "feature",
    profile_override: str | None = None,
    external_ref: str | None = None,
    change_id: str | None = None,
) -> tuple[Path, Status]:
    """Create ``changes/<id>-<slug>/`` with a status.yaml in phase (a). Idempotent per id."""
    project_root = Path(project_root)
    change_id = change_id or c.next_change_id(project_root)
    existing = c.find_change_dir(project_root, change_id)
    if existing is not None and status_path(existing).exists():
        return existing, read_status(existing)
    if existing is not None:
        # The folder exists without a status.yaml: /sdlc-init writes CLAUDE.proposed.md into
        # changes/0000-sdlc-init/ before the installer runs. Adopt the folder and its slug.
        slug = c.DIR_RE.match(existing.name).group("slug")
        change_dir = existing
    else:
        slug = c.slugify(title)
        change_dir = project_root / c.CHANGES_DIR / c.change_dir_name(change_id, slug)
    status = Status(
        id=change_id,
        slug=slug,
        title=title.strip(),
        entry_route=entry_route,
        change_type=change_type,
        profile_override=profile_override,
        external_ref=external_ref,
    )
    write_status(change_dir, status)
    (change_dir / "evidence").mkdir(exist_ok=True)
    (change_dir / "evidence" / ".gitkeep").write_text("", encoding="utf-8")
    return change_dir, status
