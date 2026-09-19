"""Template files: structure required by the handoff, placeholders resolvable, valid JSON/YAML."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from init import render
from state import yamlish

TEMPLATE = Path(__file__).resolve().parents[1] / "template"

VALUES = {
    "PROJECT_NAME": "demo",
    "PROFILE": "standard",
    "BUILD_CMD": "python -m build",
    "TEST_CMD": "python -m pytest",
    "LINT_CMD": "python -m ruff check .",
    "BUILD_HEALTHY": "exit code 0",
    "TEST_HEALTHY": "N passed",
    "LINT_HEALTHY": "All checks passed!",
    "CONVENTIONS": "- x",
    "ARCHITECTURE": "- y",
    "DEPLOY_ACTION": "none",
    "DEPLOY_PRODUCTION": "false",
    "MAINTAIN_METRIC": "ci_test_failure_rate",
    "MAINTAIN_SOURCE": "github-actions",
    "PLUGIN_VERSION": "0.1.0",
    "BUILD_RULE": "Bash(python -m build*)",
    "TEST_RULE": "Bash(python -m pytest*)",
    "LINT_RULE": "Bash(python -m ruff*)",
    "FRAMEWORK_REPO": "luissiviero/sdlc-framework",
}


def test_render_rejects_missing_placeholders():
    with pytest.raises(render.RenderError):
        render.render("hello {{NAME}}", {})
    assert render.render("hello {{NAME}}", {"NAME": "x"}) == "hello x"


def test_every_template_placeholder_has_a_value():
    for path in TEMPLATE.rglob("*"):
        if path.is_file():
            missing = render.placeholders(path.read_text(encoding="utf-8")) - set(VALUES)
            assert not missing, f"{path}: {missing}"


def test_claude_md_skeleton_sections():
    text = render.render_file(TEMPLATE / "CLAUDE.md", VALUES)
    for heading in [
        "## Commands",
        "## Conventions",
        "## Architecture",
        "## Things Claude gets wrong",
        "## Verifying your work",
    ]:
        assert heading in text
    # article p.28 verification block, verbatim lines
    assert "Run all three before reporting any task complete, and paste the output." in text
    assert "If a test fails, fix the code, not the test." in text
    assert "(all green; never skip or delete a failing test)" in text
    assert "(zero warnings)" in text
    assert "healthy:" in text  # p.27 step 2: each command with a healthy output
    assert len(text.splitlines()) <= 60, "keep CLAUDE.md under a page (p.20)"


def test_review_md_structure():
    text = (TEMPLATE / "REVIEW.md").read_text(encoding="utf-8")
    for heading in [
        "## Passes",
        "## What Important means here",
        "## Cap the nits",
        "## Do not report",
    ]:
        assert heading in text
    for pass_name in ["Bugs:", "Security:", "Compliance:"]:
        assert pass_name in text
    assert (
        "Reserve Important for findings that would break behavior, leak data or breach a policy."
        in text
    )
    assert "Report at most five nits per review" in text
    # rules added by the guide (step 26 notes; step 7 (iv); step 25; step 12)
    flat = " ".join(text.split())
    assert ".claude/**" in flat and "must not modify test files" in flat and "plan.md" in flat


def test_sdlc_yaml_renders_to_documented_keys():
    data = yamlish.loads(render.render_file(TEMPLATE / "sdlc.yaml", VALUES))
    assert data["profile"] == "standard"
    assert data["commands"] == {
        "build": "python -m build",
        "test": "python -m pytest",
        "lint": "python -m ruff check .",
    }
    assert data["deploy"] == {"action": "none", "production": False}
    assert (
        data["maintain"]["metric"] == "ci_test_failure_rate" and data["maintain"]["runbooks"] == []
    )
    assert data["risk_list"] == ["auth", "data migrations", "money movement", "production config"]
    assert data["protected_paths"] == [] and data["plan_sync"]["exempt"] == ["*.md"]
    assert data["hooks"]["format_on_edit"] is True
    assert data["plugin"] == {"name": "sdlc", "marketplace": "sdlc-framework", "version": "0.1.0"}


def test_sdlc_yaml_also_parses_with_pyyaml():
    yaml = pytest.importorskip("yaml")
    text = render.render_file(TEMPLATE / "sdlc.yaml", VALUES)
    assert yaml.safe_load(text) == yamlish.loads(text)


def test_settings_json_contract():
    data = json.loads(render.render_file(TEMPLATE / ".claude" / "settings.json", VALUES))
    deny = data["permissions"]["deny"]
    for rule in ["Read(.env*)", "Read(./secrets/**)", "WebFetch", "Bash(curl *)", "Bash(wget *)"]:
        assert rule in deny  # article p.37
    for rule in ["Edit(.claude/**)", "Edit(CLAUDE.md)", "Edit(REVIEW.md)", "Edit(sdlc.yaml)"]:
        assert rule in deny  # second layer under the protected-path hook
    assert not any(r.startswith("Write(") for r in deny), (
        "Write() path rules are ignored by Claude Code"
    )
    assert "Bash(git *)" in data["permissions"]["allow"]
    assert data["permissions"]["disableBypassPermissionsMode"] == "disable"
    assert data["sandbox"]["enabled"] is True and data["sandbox"]["failIfUnavailable"] is False
    assert data["enabledPlugins"] == {"sdlc@sdlc-framework": True}
    assert (
        data["extraKnownMarketplaces"]["sdlc-framework"]["source"]["repo"]
        == "luissiviero/sdlc-framework"
    )
    assert "hooks" not in data, "hooks come from the pinned plugin, never from the project file"


def test_changes_readme_names_the_conventions():
    text = (TEMPLATE / "changes" / "README.md").read_text(encoding="utf-8")
    for token in [
        "status.yaml",
        "sdlc/<id>/a",
        "sdlc:needs-human",
        "intent.md",
        "plan.md",
        "evidence/",
    ]:
        assert token in text
