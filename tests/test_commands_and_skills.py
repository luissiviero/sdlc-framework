"""Static checks on the markdown process content: frontmatter, referenced scripts exist,
the intent skill carries the article's sections in order, the plan skill the four p.16–17
sections plus 'Options not taken'. Whether the model *triggers* the skill is a live check
(see docs/PROGRESS.md), not a layer-1 test."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

PLUGIN = Path(__file__).resolve().parents[1] / "plugin"


def frontmatter(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    assert m, f"{path} has no frontmatter"
    fm = {}
    for line in m.group(1).splitlines():
        key, _, value = line.partition(":")
        fm[key.strip()] = value.strip()
    return fm


@pytest.mark.parametrize("name", ["sdlc-plan", "sdlc-init"])
def test_command_frontmatter_and_script_references(name):
    path = PLUGIN / "commands" / f"{name}.md"
    fm = frontmatter(path)
    assert fm["description"] and fm["disable-model-invocation"] == "true"
    body = path.read_text(encoding="utf-8")
    for ref in re.findall(
        r"\$\{CLAUDE_PLUGIN_ROOT\}/([\w/.-]+\.py)", body + fm.get("allowed-tools", "")
    ):
        assert (PLUGIN / ref).is_file(), ref
    assert "bypass" in body.lower() or "Never edit" in body  # guardrail reminder present


def test_sdlc_plan_flow_matches_step_11():
    body = (PLUGIN / "commands" / "sdlc-plan.md").read_text(encoding="utf-8")
    for step in [
        "Brainstorm",
        "new-change",
        "intent-template",
        "owner corrects",
        "commit-phase",
        "sdlc:a-ready",
        "compare/",
    ]:
        assert step in body, step
    assert "$ARGUMENTS" in body
    assert "Do not start phase (b)" in " ".join(body.split())


def test_sdlc_init_flow_matches_step_21():
    body = (PLUGIN / "commands" / "sdlc-init.md").read_text(encoding="utf-8")
    for token in [
        "--detect-only",
        "profile",
        "deploy action",
        "maintain metric",
        "/init",
        "sdlc_init.py",
        "--id 0000",
        "sdlc:a-ready",
        "Re-running is safe",
    ]:
        assert token in body, token


def test_intent_skill_sections_in_article_order():
    path = PLUGIN / "skills" / "intent-template" / "SKILL.md"
    fm = frontmatter(path)
    assert fm["name"] == "intent-template"
    assert "intent" in fm["description"].lower() and "incident" in fm["description"].lower()
    body = path.read_text(encoding="utf-8")
    order = [
        "## Problem",
        "## Proposed outcome",
        "## Affected users and systems",
        "## Constraints",
        "## Open questions",
        "## Evidence",
    ]
    positions = [body.index(h) for h in order]
    assert positions == sorted(positions)
    assert (
        "Author:" in body and "Status:" in body and "Change id:" in body and "Entry route:" in body
    )
    assert "idea | ticket" in body and "incident" in body


def test_plan_skill_sections_and_interrogation():
    path = PLUGIN / "skills" / "plan-template" / "SKILL.md"
    fm = frontmatter(path)
    assert fm["name"] == "plan-template"
    body = path.read_text(encoding="utf-8")
    order = [
        "## Files that change",
        "## Order of work",
        "## Risks",
        "## Options not taken",
        "## Proof",
    ]
    positions = [body.index(h) for h in order]
    assert positions == sorted(positions)
    for q in [
        "could this change break",
        "most risky",
        "options did you consider",
        "never seen this conversation",
    ]:
        assert q in body, q
    assert "read-only" in body.lower() and "Read/Grep/Glob" in body


def test_no_portuguese_in_process_content():
    """CLAUDE.md: English only in every file."""
    for path in list(PLUGIN.rglob("*.md")) + list((PLUGIN.parent / "template").rglob("*")):
        if path.is_file():
            text = path.read_text(encoding="utf-8", errors="replace").lower()
            assert not re.search(r"\b(não|você|também|então|obrigado)\b", text), path
