"""Which model each part of a phase run uses (ROADMAP R7, ``docs/proposals/reviewer-on-opus.md``;
decision 21: a panel on one model shares its blind spots).

Three keys of ``sdlc.yaml`` name the models, each a full model id (``claude-opus-5-5``) or a
family alias (``opus``):

- ``session_model``: the CI session's model, which the runner passes as ``--model``. Either
  one model, or a mapping of ``default`` and per-phase entries (``a`` to ``f``)::

      session_model:
        default: claude-opus-5-5
        b: claude-fable-5-1

  A fix round runs on its change's phase's entry (a round on a design PR is a (b) run), the
  (e) review pass on ``e``'s. An absent key keeps the CLI's default. ``SDLC_MODEL`` in the
  workflow's environment still wins.
- ``adversarial_model``: the adversarial reviewer's model. When it is set, the gate's
  ``reviewer_model`` check requires the verdict's own record (written by the
  ``panel_blind`` hook from the reviewer's transcript) to name it. Absent: not checked.
- ``panel_advocate_model``: the devil's advocate's model (0.2.30). The advocate never runs on
  the session's model: in a phase whose session runs on it, the advocate takes
  ``adversarial_model`` instead.

The Agent tool's per-invocation model takes a family alias, not a full id (this framework's
reading of Claude Code 2.1.304, R7's record), and an alias the CLI resolves on its own may
name an older version (``opus`` was ``claude-opus-5`` in every CI run on 2.1.278 read up to
2026-10-16). So the phase commands pass the alias (``alias``), and the runner pins what each
alias resolves to with ``ANTHROPIC_DEFAULT_<FAMILY>_MODEL`` (``alias_pins``), a variable the
workflow already sets winning. Where the alias names the session's own family, Claude Code
runs the sub-agent on the session's exact model instead (the sub-agents reference, "Choose a
model"); the gate's check then says so when that is not the configured model.
"""

from __future__ import annotations

import re
from typing import Any

FAMILIES = ("opus", "sonnet", "haiku", "fable")
ALIAS_ENV = "ANTHROPIC_DEFAULT_{family}_MODEL"
SESSION_KEY = "session_model"
REVIEWER_KEY = "adversarial_model"
ADVOCATE_KEY = "panel_advocate_model"
DEFAULT_ENTRY = "default"
# the run kinds whose session belongs to a phase other than their own name
SESSION_PHASE = {"review": "e"}
FULL_ID_RE = re.compile(r"^claude-(opus|sonnet|haiku|fable)-")


def _text(value: Any) -> str | None:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def session_model(config: dict[str, Any] | None, phase: str | None) -> str | None:
    """The model ``sdlc.yaml: session_model`` names for a run of ``phase``, or None."""
    value = (config or {}).get(SESSION_KEY)
    if isinstance(value, dict):
        key = SESSION_PHASE.get(str(phase), str(phase))
        return _text(value.get(key)) or _text(value.get(DEFAULT_ENTRY))
    return _text(value)


def reviewer_model(config: dict[str, Any] | None) -> str | None:
    """``sdlc.yaml: adversarial_model``, or None."""
    return _text((config or {}).get(REVIEWER_KEY))


def family(model: str | None) -> str | None:
    """The family of an alias or a full id (``opus`` for ``claude-opus-5-5[1m]``), or None
    for anything else (a provider's own identifier)."""
    text = str(model or "").strip().lower().split("[", 1)[0]
    if text in FAMILIES:
        return text
    m = FULL_ID_RE.match(text)
    return m.group(1) if m else None


def alias(model: str | None) -> str | None:
    """What a phase command passes as the sub-agent's model: the family alias."""
    return family(model)


def same_model(a: str | None, b: str | None) -> bool:
    """Do two configured models name the same model (an alias against an id of its family
    counts)?"""
    from panel import ledger  # noqa: PLC0415

    if not a or not b:
        return False
    return ledger.model_matches(a, b) or ledger.model_matches(b, a)


def advocate_model(config: dict[str, Any] | None, phase: str | None) -> str | None:
    """The devil's advocate's model for ``phase``: ``panel_advocate_model``, or
    ``adversarial_model`` when the phase's session itself runs on the former."""
    advocate = _text((config or {}).get(ADVOCATE_KEY))
    reviewer = reviewer_model(config)
    if advocate and reviewer and same_model(advocate, session_model(config, phase)):
        return reviewer
    return advocate


def alias_pins(
    config: dict[str, Any] | None, phase: str | None, env: dict[str, str] | None = None
) -> dict[str, str]:
    """``ANTHROPIC_DEFAULT_<FAMILY>_MODEL`` for each full id the phase's sub-agents run on
    (the reviewer's first, then the advocate's), so the alias a command passes resolves to
    it. A family already pinned by ``env`` is left alone, and the first id of a family wins."""
    env = env or {}
    pins: dict[str, str] = {}
    for model in (reviewer_model(config), advocate_model(config, phase)):
        fam = family(model)
        if not model or not fam or model.lower().split("[", 1)[0] in FAMILIES:
            continue
        var = ALIAS_ENV.format(family=fam.upper())
        if var not in env and var not in pins:
            pins[var] = model
    return pins


def for_phase(config: dict[str, Any] | None, phase: str | None) -> dict[str, Any]:
    """What ``panel/cli.py models`` prints for the phase commands: each role's model and the
    alias to pass (None: pass no model)."""
    reviewer = reviewer_model(config)
    advocate = advocate_model(config, phase)
    return {
        "phase": phase,
        "session": session_model(config, phase),
        "reviewer": {"model": reviewer, "alias": alias(reviewer)},
        "advocate": {"model": advocate, "alias": alias(advocate)},
    }
