"""Which model each part of a phase run uses (ROADMAP R7, ``docs/proposals/reviewer-on-opus.md``;
decision 21: a panel on one model shares its blind spots).

Three keys of ``sdlc.yaml`` name the models, each a full model id (``claude-opus-5-5``) or a
family alias (``opus``):

- ``session_model``: the CI session's model, which the runner passes as ``--model``. Either
  one model, or a mapping of ``default`` and per-phase entries (``intent`` to ``maintain``;
  the letters ``a`` to ``f`` an older ``sdlc.yaml`` names are read as those, R45)::

      session_model:
        default: claude-opus-5-5
        design: claude-fable-5-1

  A fix round runs on its change's phase's entry (a round on a design PR is a design run), the
  deploy review pass on ``deploy``'s. An absent key keeps the CLI's default. ``SDLC_MODEL`` in the
  workflow's environment still wins.
- ``adversarial_model``: the adversarial reviewer's model. When it is set, the gate's
  ``reviewer_model`` check requires the verdict's own record (written by the
  ``panel_blind`` hook from the reviewer's transcript) to name it. Absent: not checked.
- ``panel_advocate_model``: the devil's advocate's model (0.2.30). The advocate never runs on
  the session's model: in a phase whose session runs on its family, the advocate takes
  ``adversarial_model`` instead.

Every CI session the runner composes takes ``session_model``: the phases, a fix round, the
explain step and the weekly scan (their own run kinds read the ``default`` entry).

The Agent tool's per-invocation model takes a family alias, not a full id (Claude Code
2.1.304's Agent tool, docs/notes/51.md), and an alias the CLI resolves on its own may
name an older version (``opus`` was ``claude-opus-5`` in every CI run on 2.1.278 read up to
2026-10-16). So the phase commands pass the alias (``alias``), and the runner pins what each
alias resolves to with ``ANTHROPIC_DEFAULT_<FAMILY>_MODEL`` (``alias_pins``), a variable the
workflow already sets winning. Where the alias names the session's own family, Claude Code
runs the sub-agent on the session's exact model instead (the sub-agents reference, "Choose a
model"). A configuration whose sub-agent cannot reach its model that way is reported by
``conflicts``: ``panel/cli.py models`` prints it, and the gate's ``reviewer_model`` check names
it when it parks. A configured model the pinned CLI does not know is printed on the session's
stderr as ``[claude-code:unrecognized_model]`` (NOTES §54); ``unrecognized`` finds it, and the
runner parks on it with the pin to raise (ROADMAP R63).
"""

from __future__ import annotations

import re
from typing import Any

from state import conventions as c

FAMILIES = ("opus", "sonnet", "haiku", "fable")
ALIAS_ENV = "ANTHROPIC_DEFAULT_{family}_MODEL"
SESSION_KEY = "session_model"
REVIEWER_KEY = "adversarial_model"
ADVOCATE_KEY = "panel_advocate_model"
DEFAULT_ENTRY = "default"
# the run kinds whose session belongs to a phase other than their own name
SESSION_PHASE = {"review": c.DEPLOY}
FULL_ID_RE = re.compile(r"^claude-(opus|sonnet|haiku|fable)-")
# R63: the line a CLI prints for a sub-agent model it does not know, before it runs that
# sub-agent on the session's model (NOTES §54: 2.1.278 for the reviewer's claude-opus-5-5)
UNRECOGNIZED_MODEL_RE = re.compile(
    r'\[claude-code:unrecognized_model\][^\r\n]*?"model"\s*:\s*"(?P<model>[^"\r\n]+)"'
)


def _text(value: Any) -> str | None:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def session_model(config: dict[str, Any] | None, phase: str | None) -> str | None:
    """The model ``sdlc.yaml: session_model`` names for a run of ``phase``, or None."""
    value = (config or {}).get(SESSION_KEY)
    if isinstance(value, dict):
        key = SESSION_PHASE.get(str(phase), c.phase_name(str(phase)))
        # R45: the name's entry, else the letter's an older sdlc.yaml names (``c:``)
        letter = c.PHASE_LETTERS.get(key)
        named = _text(value.get(key)) or (_text(value.get(letter)) if letter else None)
        return named or _text(value.get(DEFAULT_ENTRY))
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


def advocate_model(
    config: dict[str, Any] | None, phase: str | None, session: str | None = None
) -> str | None:
    """The devil's advocate's model for ``phase``: ``panel_advocate_model``, or
    ``adversarial_model`` when the phase's session (``session``, the run's own ``--model``
    when given, else ``session_model``) runs on the former's family: an alias of the
    session's family would run the advocate on the session's model."""
    advocate = _text((config or {}).get(ADVOCATE_KEY))
    reviewer = reviewer_model(config)
    session = session or session_model(config, phase)
    if advocate and reviewer and session:
        if same_model(advocate, session) or family(advocate) == family(session):
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
    session = _text(env.get("SDLC_MODEL"))
    for model in (reviewer_model(config), advocate_model(config, phase, session)):
        fam = family(model)
        if not model or not fam or model.lower().split("[", 1)[0] in FAMILIES:
            continue
        var = ALIAS_ENV.format(family=fam.upper())
        if var not in env and var not in pins:
            pins[var] = model
    return pins


def conflicts(
    config: dict[str, Any] | None, phase: str | None, env: dict[str, str] | None = None
) -> list[str]:
    """Why a sub-agent of ``phase`` cannot run on its configured full id when started with its
    alias: the session runs on another id of the same family (the alias then runs on the
    session's model), or the reviewer and the advocate are two ids of one family (one pin
    per family). ``env`` carries the workflow's ``SDLC_MODEL`` and pins."""
    env = env or {}
    session = _text(env.get("SDLC_MODEL")) or session_model(config, phase)
    reviewer = reviewer_model(config)
    advocate = advocate_model(config, phase, session)
    found: list[str] = []
    for key, model in ((REVIEWER_KEY, reviewer), (ADVOCATE_KEY, advocate)):
        if not model or family(model) is None or model.lower() in FAMILIES:
            continue
        if session and family(session) == family(model) and not same_model(session, model):
            found.append(
                f"{key} {model} is in the family of the session's model {session} at "
                f"({phase}): started with its alias, it runs on {session}"
            )
        var = ALIAS_ENV.format(family=family(model).upper())
        pinned = _text(env.get(var))
        if pinned and not same_model(pinned, model):
            found.append(f"the workflow pins {var}={pinned}, not {model} ({key})")
    if (
        reviewer
        and advocate
        and family(reviewer) == family(advocate)
        and not (
            same_model(reviewer, advocate) or {reviewer.lower(), advocate.lower()} & set(FAMILIES)
        )
    ):
        found.append(
            f"{REVIEWER_KEY} {reviewer} and the advocate's {advocate} are two ids of one "
            "family: one alias cannot reach both"
        )
    return found


def for_phase(
    config: dict[str, Any] | None, phase: str | None, env: dict[str, str] | None = None
) -> dict[str, Any]:
    """What ``panel/cli.py models`` prints for the phase commands: each role's model and the
    alias to pass (None: pass no model), the pins a run by hand exports before it starts
    (the runner sets them itself) and the ``conflicts``."""
    env = env or {}
    session = _text(env.get("SDLC_MODEL")) or session_model(config, phase)
    reviewer = reviewer_model(config)
    advocate = advocate_model(config, phase, session)
    return {
        "phase": phase,
        "session": session,
        "reviewer": {"model": reviewer, "alias": alias(reviewer)},
        "advocate": {"model": advocate, "alias": alias(advocate)},
        "pins": alias_pins(config, phase, env),
        "conflicts": conflicts(config, phase, env),
    }


def unrecognized(
    stderr: str | None,
    config: dict[str, Any] | None,
    phase: str | None,
    env: dict[str, str] | None = None,
    ran: list[str] | None = None,
) -> list[str]:
    """The models the run was configured with (the session's, from the workflow's
    ``SDLC_MODEL`` or ``session_model``; ``adversarial_model``; the phase's advocate; an alias
    meets any id of its family) that an ``unrecognized_model`` line of the session's stderr
    reports and that did not run: ``ran`` is the session result's ``modelUsage``, sub-agents
    included. A fallback onto the same model (the session and the reviewer both on
    ``claude-opus-5-5``) loses nothing and is not reported; neither is a model the run was
    not configured with, since only a configured one is the owner's to fix by raising the
    pin. Once each, in the order printed."""
    from panel import ledger  # noqa: PLC0415

    env = env or {}
    session = _text(env.get("SDLC_MODEL")) or session_model(config, phase)
    named = [
        m for m in (session, reviewer_model(config), advocate_model(config, phase, session)) if m
    ]
    found: list[str] = []
    for match in UNRECOGNIZED_MODEL_RE.finditer(stderr or ""):
        model = match.group("model").strip()
        if model in found or not any(same_model(model, n) for n in named):
            continue
        if any(ledger.model_matches(model, m) for m in ran or []):
            continue
        found.append(model)
    return found
