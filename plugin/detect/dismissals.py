"""The dismissal store of gate (f): ``changes/.dismissed.json`` (build guide steps 38 and
39; decision 25; article p.47 step 4 "Dismiss with a reason, so the dismissal is recorded
and the same finding does not return as new on the next run", p.44 "Dismissals tune the
bands").

One file per project, beside ``changes/.review-seen.json``, committed to the default branch
through a pull request the owner merges (the automation identity never writes to the
default branch). Shape::

    {"schema_version": 1,
     "entries": {"<signature>": {"kind": "detect" | "scan", "reason": "...", "by": "<login>",
                                 "at": "<ISO>", "until": "<YYYY-MM-DD>" | null,
                                 "change_id": "0007", "summary": "..."}}}

A detection dismissal carries ``until`` = the day it was made plus one baseline window
(``detect.finding``: a muted metric comes back once the band has rolled over; the owner
widens the band in ``bands.yaml`` when the noise is the band's, p.44 step 6). A scan
dismissal has no ``until``: the same code finding stays dismissed until the finding
changes (its signature is its pass, file and summary). Tuning the bands themselves is a
``bands.yaml`` change in a reviewed PR, never something this store does.
"""

from __future__ import annotations

import json
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1
FILE = ".dismissed.json"
KINDS = ("detect", "scan")


def path_for(root: Path, changes_dir: str = "changes") -> Path:
    return Path(root) / changes_dir / FILE


def empty() -> dict[str, Any]:
    return {"schema_version": SCHEMA_VERSION, "entries": {}}


def load(path: Path) -> dict[str, Any]:
    """The record; a missing or unreadable file reads as empty (a dismissal that cannot be
    read never suppresses a finding)."""
    path = Path(path)
    if not path.is_file():
        return empty()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return empty()
    if not isinstance(data, dict) or not isinstance(data.get("entries"), dict):
        return empty()
    return {"schema_version": SCHEMA_VERSION, "entries": dict(data["entries"])}


def save(path: Path, record: dict[str, Any]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n"
    )


def _today() -> date:
    return datetime.now(timezone.utc).date()


def until_date(days: int | None, made_on: date | None = None) -> str | None:
    if days is None:
        return None
    return ((made_on or _today()) + timedelta(days=int(days))).isoformat()


def add(
    record: dict[str, Any],
    signature: str,
    *,
    kind: str,
    reason: str,
    by: str,
    change_id: str | None,
    summary: str = "",
    until: str | None = None,
    at: str | None = None,
) -> dict[str, Any]:
    """Return a new record with the dismissal (a second dismissal of the same signature
    replaces the first: the newest reason and expiry stand)."""
    if kind not in KINDS:
        raise ValueError(f"kind must be one of {KINDS}, got {kind!r}")
    reason = " ".join(reason.split())
    if not reason:
        raise ValueError("a dismissal needs a reason (article p.47 step 4)")
    entries = dict(record.get("entries") or {})
    entries[signature] = {
        "kind": kind,
        "reason": reason,
        "by": by.strip(),
        "at": at
        or datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "until": until,
        "change_id": change_id,
        "summary": summary,
    }
    return {"schema_version": SCHEMA_VERSION, "entries": entries}


def lookup(record: dict[str, Any], signature: str, today: date | None = None) -> dict | None:
    """The dismissal in force for the signature, or None (absent or expired)."""
    entry = (record.get("entries") or {}).get(signature)
    if not isinstance(entry, dict):
        return None
    until = entry.get("until")
    if isinstance(until, str) and until.strip():
        try:
            expiry = date.fromisoformat(until.strip()[:10])
        except ValueError:
            return entry  # an unreadable expiry never revives a finding by accident
        if (today or _today()) > expiry:
            return None
    return entry


def is_dismissed(record: dict[str, Any], signature: str, today: date | None = None) -> bool:
    return lookup(record, signature, today) is not None
