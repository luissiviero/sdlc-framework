"""The finding of phase (f): its signature and the ``evidence/detection.json`` record
(build guide steps 37 and 39; article p.44 step 6 "Dismissals tune the bands", p.47 step 4
"Dismiss with a reason, so the dismissal is recorded and the same finding does not return as
new on the next run").

A finding is "the same" when the same metric trips the same rule: the signature is the first
16 hex characters of the sha1 of ``detect|<metric>|<rule>`` (the review pass's
``review/findings.signature`` does the same for a code finding; a scan finding of step 38
reuses that one). The date is deliberately not part of it - a breach that lasts a week is
one finding, not seven - and a dismissal expires after one baseline window
(``dismissals.py``), so a muted metric comes back once the band it was judged under has
rolled over.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1
KIND = "detect"
DETECTION_FILE = "detection.json"  # under changes/<id>-<slug>/evidence/
PROPOSAL_FILE = "proposal.json"  # the diagnosis's proposed route (tier 3) or pull_request
SIGNATURE_LEN = 16
RECENT_POINTS = 8  # the tail the record keeps, the span of the longest rule


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def signature(metric: str, rule: str | None, kind: str = KIND) -> str:
    key = "|".join((kind, str(metric).strip().lower(), str(rule or "").strip().lower()))
    return hashlib.sha1(key.encode("utf-8")).hexdigest()[:SIGNATURE_LEN]  # noqa: S324


def build_record(
    *,
    metric: str,
    source: str,
    verdict: dict[str, Any],
    observations: list[dict[str, Any]],
    action: str | None,
    failed_run_urls: list[str],
    commits: list[dict[str, Any]],
    forced: bool = False,
    at: str | None = None,
) -> dict[str, Any]:
    """``detection.json``: everything the diagnosis and the gate read about the breach. The
    verdict is ``stats.Verdict.as_dict()``; the observations are the series' tail."""
    rule = verdict.get("rule")
    return {
        "schema_version": SCHEMA_VERSION,
        "kind": KIND,
        "metric": metric,
        "source": source,
        "signature": signature(metric, rule),
        "at": at or now_iso(),
        "tier": int(verdict.get("tier") or 0),
        "action": action,
        "rule": rule,
        "rules_hit": list(verdict.get("rules_hit") or []),
        "mean": verdict.get("mean"),
        "sigma": verdict.get("sigma"),
        "sigmas": verdict.get("sigmas"),
        "latest": verdict.get("latest"),
        "breach_start": verdict.get("breach_start"),
        "window_days": verdict.get("window_days"),
        "n_baseline": verdict.get("n_baseline"),
        "n_tail": verdict.get("n_tail"),
        "direction": verdict.get("direction"),
        "reason": verdict.get("reason"),
        "observations": list(observations[-RECENT_POINTS:]),
        "failed_run_urls": list(failed_run_urls),
        "commits": list(commits),
        "forced": bool(forced),
    }


def validate(data: Any) -> list[str]:
    """Why a detection record cannot be trusted; [] when it can."""
    if not isinstance(data, dict):
        return ["detection.json is not a JSON object"]
    problems = []
    if data.get("schema_version") != SCHEMA_VERSION:
        problems.append(f"schema_version is not {SCHEMA_VERSION}")
    if data.get("kind") != KIND:
        problems.append(f"kind is not {KIND!r}")
    metric = data.get("metric")
    if not isinstance(metric, str) or not metric.strip():
        problems.append("metric is missing")
    tier = data.get("tier")
    if isinstance(tier, bool) or not isinstance(tier, int) or not 0 <= tier <= 3:
        problems.append("tier is not an integer between 0 and 3")
    if not isinstance(data.get("signature"), str) or len(data.get("signature", "")) != (
        SIGNATURE_LEN
    ):
        problems.append("signature is missing")
    elif isinstance(metric, str) and data["signature"] != signature(metric, data.get("rule")):
        problems.append("signature does not match metric and rule")
    if not isinstance(data.get("at"), str):
        problems.append("at is missing")
    return problems


def read(path: Path) -> tuple[dict[str, Any] | None, str]:
    """(the record, "") or (None, why)."""
    path = Path(path)
    if not path.is_file():
        return None, f"{path.name} is missing"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return None, f"{path.name} unreadable: {exc}"
    problems = validate(data)
    if problems:
        return None, f"{path.name}: " + "; ".join(problems)
    return data, ""


SCAN_FILE = "scan-finding.json"  # step 38: the weekly security review's finding (kind "scan")
SCAN_TIER = 3  # a scan finding proposes (its route is the intent PR), never only logs


def read_scan(path: Path) -> tuple[dict[str, Any] | None, str]:
    """A scan finding record (``plugin/scan/route.py`` writes it): ``kind`` "scan", a
    ``signature`` (``review.findings.signature``), ``summary``, ``file``, ``class``."""
    path = Path(path)
    if not path.is_file():
        return None, f"{path.name} is missing"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return None, f"{path.name} unreadable: {exc}"
    if not isinstance(data, dict) or data.get("kind") != "scan":
        return None, f"{path.name}: not a scan finding record"
    sig = data.get("signature")
    if not isinstance(sig, str) or len(sig) != SIGNATURE_LEN:
        return None, f"{path.name}: signature is missing"
    return data, ""


def read_any(evidence_dir: Path) -> tuple[dict[str, Any] | None, str]:
    """The finding an incident change carries: the detection record, else the scan record
    read as a tier-3 finding (``metric`` = the vulnerability class, ``rule`` = "scan")."""
    evidence_dir = Path(evidence_dir)
    record, why = read(evidence_dir / DETECTION_FILE)
    if record is not None:
        return record, ""
    scan, scan_why = read_scan(evidence_dir / SCAN_FILE)
    if scan is None:
        return None, why if not (evidence_dir / SCAN_FILE).exists() else scan_why
    return {
        **scan,
        "metric": f"security: {scan.get('class') or 'unclassified'}",
        "rule": "scan",
        "tier": SCAN_TIER,
        "forced": False,
    }, ""


def write(path: Path, data: dict[str, Any]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
