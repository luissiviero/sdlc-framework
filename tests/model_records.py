"""What the ``panel_blind`` hook writes beside a verdict, for the tests that stand in for the
adversarial reviewer and the devil's advocate (0.2.30; ROADMAP R7). The models are the
template's (``template/sdlc.yaml``), which every fixture initialised by ``/sdlc-init`` has."""

from __future__ import annotations

import json
from pathlib import Path

REVIEWER_MODEL = "claude-opus-5-5"  # template/sdlc.yaml: adversarial_model
ADVOCATE_MODEL = "claude-fable-5-1"  # template/sdlc.yaml: panel_advocate_model
AGENT = "sdlc:adversarial-reviewer"


def write_reviewer_record(
    verdict_path: Path, head: str, models=(REVIEWER_MODEL,), agent: str | None = AGENT
) -> Path:
    """``adversarial-review-<phase>.model.json`` beside ``verdict_path``, as the hook writes it
    when the reviewer writes its verdict for ``head``."""
    phase = verdict_path.stem.rsplit("-", 1)[-1]
    record = {
        "schema_version": 1,
        "phase": phase,
        "member": "reviewer",
        "head": head,
        "agent_type": agent,
        "models": list(models),
        "reason": None if models else "the sub-agent's transcript names no model",
        "at": "2026-10-19T10:00:00Z",
    }
    path = verdict_path.with_name(f"adversarial-review-{phase}.model.json")
    path.write_text(json.dumps(record), encoding="utf-8", newline="\n")
    return path
