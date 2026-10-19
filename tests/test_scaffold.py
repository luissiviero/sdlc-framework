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


def test_the_root_sdlc_yaml_parses():
    """NOTES §45 gap 6: PR #214 indented ``max_turns`` four spaces, the root ``sdlc.yaml``
    stopped parsing, and every check stayed green because no test read the file."""
    from hooks._common import config_flag, load_sdlc_config

    config = load_sdlc_config(str(ROOT))
    assert config, "the root sdlc.yaml exists and is a mapping"
    assert config_flag(config, "paused") in (True, False)
    assert isinstance(config.get("gate"), dict)


def test_a_test_never_sees_the_runner_s_variables():
    """The autouse fixture of conftest.py removes what a GitHub Actions runner sets (0.2.28:
    the first run of the suite in Actions failed seven tests on ``GITHUB_REF_NAME``,
    ``GITHUB_ACTIONS`` and ``GITHUB_REPOSITORY`` leaking into the scripts under test). On the
    owner's PC and in a cloud session this passes trivially; on a runner it is the proof."""
    import os

    from tests.conftest import runner_variables

    assert runner_variables() == []
    assert "SDLC_HOOK_LOG" in os.environ  # the fixture's own setting stays
    sample = {"GITHUB_ACTIONS": "true", "RUNNER_OS": "Linux", "CI": "true", "HOME": "/h"}
    assert runner_variables(sample) == ["CI", "GITHUB_ACTIONS", "RUNNER_OS"]


def test_a_test_reaches_no_host_but_loopback():
    """The autouse fixture of conftest.py (2026-10-19): 40 tests sent 673 real requests to
    api.github.com with a fake token. Any host but loopback now gets the 401 they got, at once,
    and through ``pr/github.py``'s one HTTP entry point the caller reads it as before."""
    import urllib.error
    import urllib.request

    import pytest
    from pr import github

    with pytest.raises(urllib.error.HTTPError) as refused:
        urllib.request.urlopen("https://api.github.com/repos/owner/name/labels", timeout=1)
    assert refused.value.code == 401
    result = github._request("POST", f"{github.API_ROOT}/repos/owner/name/labels", "fake", {})
    assert (result["status"], result["error"]) == (401, "Bad credentials")


def test_the_shards_split_the_suite_with_nothing_lost():
    """framework-checks.yml runs the Windows suite in shards (``FRAMEWORK_TEST_SHARD=i/n``):
    every test id lands in exactly one shard, and a malformed value is refused rather than
    read as an empty shard."""
    import os

    import pytest

    from tests.conftest import SHARD_VARIABLE, in_shard, parse_shard

    assert SHARD_VARIABLE not in os.environ  # a test's subprocesses never inherit it
    ids = [f"tests/test_x.py::test_{n}[{p}]" for n in range(300) for p in ("a", "b")]
    for count in (1, 2, 3, 4):
        homes = [[i for i in range(1, count + 1) if in_shard(nid, i, count)] for nid in ids]
        assert all(len(home) == 1 for home in homes)
        sizes = [sum(home == [i] for home in homes) for i in range(1, count + 1)]
        assert min(sizes) > len(ids) / count / 2  # no shard is (nearly) empty
    assert parse_shard("2/3") == (2, 3)
    for bad in ("0/3", "4/3", "3", "a/b", "1/0", "-1/2"):
        with pytest.raises(ValueError):
            parse_shard(bad)
