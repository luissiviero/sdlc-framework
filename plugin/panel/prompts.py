"""The three briefs of the review panel (decision 21; build guide step 16a), printed by
``panel/cli.py prompt`` with the item filled in and handed to three fresh contexts:

1. the **reviewer** — the REVIEW.md pass over the item and its context;
2. the **devil's advocate** — the adversarial reviewer's angle, blind to the reviewer, on a
   different model than the reviewer (a panel reduces variance, not bias: three judges on
   one model share its blind spots; ``sdlc.yaml: panel_advocate_model``);
3. the **conciliator** — reads both verdicts and writes one decision with a rationale of at
   most five lines.

Each member writes exactly one file under ``changes/<id>-<slug>/evidence/panel/``; the
run records the conciliator's decision with ``panel/cli.py record``. Nobody fixes anything
and nobody asks the owner: the owner reads the decision at the next human gate and
overturns it with a review comment (``/sdlc-fix``).

The brief texts live in ``briefs/<member>.md`` beside this module, as the review pass keeps
``review/REVIEW_PROMPT.md``: prose the owner reviews as prose. ``panel/cli.py`` fills their
placeholders with ``str.format``, so a literal brace in a brief is doubled (the
conciliator's JSON example). They are read as UTF-8 whatever the platform's default (they
carry ``—`` and ``≠``); a Windows checkout's CRLF reads back as LF. The kind and phase hints
below are lookups, not prose, and stay here.
"""

from __future__ import annotations

from pathlib import Path

BRIEFS_DIR = Path(__file__).resolve().parent / "briefs"


def _brief(member: str) -> str:
    return (BRIEFS_DIR / f"{member}.md").read_text(encoding="utf-8")


REVIEWER = _brief("reviewer")
ADVOCATE = _brief("advocate")
CONCILIATOR = _brief("conciliator")

APPLY_HINT = {
    "concern": (
        "what the design does about this flagged concern, in one line: the decision alone. "
        "The run closes the item in spec.md with it and keeps the concern's text beside it, "
        "so do not repeat the concern and do not add any 'decided' prefix."
    ),
    "policy": (
        "which policy reading wins for this concern and what the design does about the "
        "other (the run closes the concern in spec.md with your decision)."
    ),
    "escalate": (
        "whether the adversarial reviewer's escalate verdict stands ('park') or the phase "
        "continues ('continue', with what the run changes first, if anything)."
    ),
    "finding": (
        "the fix the run applies for this Important finding, or 'settled: <why the finding "
        "does not block this change>' when no fix inside this change is possible (a "
        "guardrail file, a CLAUDE.md line the owner applies from the PR body)."
    ),
    "verifier": (
        "whether the verifier's mismatch is a defect the run fixes now (name it) or a "
        "report the run records and continues on (say why the plan is still met)."
    ),
}

EVIDENCE_HINT = {
    "b": "the diff file `diff-b.patch`, the adversarial verdict; no toolchain output yet.",
    "c": "`verifier.md`, the diff file `diff-c.patch`, the adversarial verdict.",
    "d": "`test.log`, `build.log`, `lint.log`, `verifier.md`, the diff file `diff-d.patch`.",
    "e": "the toolchain logs, `verifier.md`, `review-findings.json`, the diff file.",
}
