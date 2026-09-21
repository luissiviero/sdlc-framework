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
    created_at: str = field(default_factory=_now)
    updated_at: str = field(default_factory=_now)
    schema_version: int = SCHEMA_VERSION

    # -- validation ---------------------------------------------------------------------
    def validate(self) -> None:
        c.change_dir_name(self.id, self.slug)
        if self.phase not in c.PHASES:
            raise ValueError(f"phase must be one of {c.PHASES}, got {self.phase!r}")
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
        st.validate()
        return st

    # -- mutations ----------------------------------------------------------------------
    def touch(self) -> None:
        self.updated_at = _now()

    def set_phase(self, phase: str) -> None:
        self.phase = phase
        self.parked_reason = None
        self.touch()
        self.validate()

    def record_gate(self, phase: str, result: str, reason: str | None = None) -> None:
        self.gate = Gate(phase=phase, result=result, reason=reason, at=_now())
        if result == "parked":
            self.parked_reason = reason
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


def status_path(change_dir: Path) -> Path:
    return Path(change_dir) / STATUS_FILE


def read_status(change_dir: Path) -> Status:
    data = yamlish.load_file(status_path(change_dir))
    if not isinstance(data, dict):
        raise ValueError(f"{status_path(change_dir)} is not a mapping")
    return Status.from_dict(data)


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
