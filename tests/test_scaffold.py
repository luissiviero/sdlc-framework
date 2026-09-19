"""Layer-1 test: the repo layout matches CLAUDE.md and the plugin/marketplace manifests parse."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_layout_matches_claude_md():
    for rel in [
        "plugin/commands",
        "plugin/skills",
        "plugin/agents",
        "plugin/hooks",
        "plugin/gate",
        "plugin/state",
        "template",
        "docs/reference",
    ]:
        assert (ROOT / rel).is_dir(), rel


def test_plugin_manifest():
    manifest = json.loads((ROOT / "plugin/.claude-plugin/plugin.json").read_text(encoding="utf-8"))
    assert manifest["name"] == "sdlc"
    assert manifest["version"]


def test_marketplace_points_at_plugin():
    mp = json.loads((ROOT / ".claude-plugin/marketplace.json").read_text(encoding="utf-8"))
    assert mp["name"] == "sdlc-framework"
    entry = next(p for p in mp["plugins"] if p["name"] == "sdlc")
    assert entry["source"] == "./plugin"
    assert (ROOT / "plugin/.claude-plugin/plugin.json").exists()
    manifest = json.loads((ROOT / "plugin/.claude-plugin/plugin.json").read_text(encoding="utf-8"))
    assert entry["version"] == manifest["version"], "pin: marketplace and plugin versions agree"
