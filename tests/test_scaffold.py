"""Layer-1 test: the repo layout matches CLAUDE.md and the plugin/marketplace manifests parse.
The plugin root is the repository root (marketplace source "./"), so a marketplace-installed
copy carries template/ next to plugin/ (a script in a copied plugin cannot read above its
root)."""

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


def test_plugin_manifest_points_components_into_plugin_dir():
    manifest = json.loads((ROOT / ".claude-plugin/plugin.json").read_text(encoding="utf-8"))
    assert manifest["name"] == "sdlc" and manifest["version"]
    assert manifest["commands"] == "./plugin/commands"
    assert manifest["skills"] == "./plugin/skills"
    # agents: the manifest key takes a list of files (the validator rejects a directory)
    assert isinstance(manifest["agents"], list) and manifest["agents"]
    for rel in manifest["agents"]:
        assert rel.startswith("./plugin/agents/") and (ROOT / rel).is_file(), rel
    assert manifest["hooks"] == "./plugin/hooks/hooks.json"
    for key in ("commands", "skills", "hooks"):
        assert (ROOT / manifest[key]).exists(), key
    assert not (ROOT / "plugin" / ".claude-plugin").exists()


def test_marketplace_points_at_repo_root():
    mp = json.loads((ROOT / ".claude-plugin/marketplace.json").read_text(encoding="utf-8"))
    assert mp["name"] == "sdlc-framework"
    entry = next(p for p in mp["plugins"] if p["name"] == "sdlc")
    assert entry["source"] == "./"
    manifest = json.loads((ROOT / ".claude-plugin/plugin.json").read_text(encoding="utf-8"))
    assert entry["version"] == manifest["version"], "pin: marketplace and plugin versions agree"
