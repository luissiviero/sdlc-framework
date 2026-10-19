"""Layer-1 test: the repo layout matches CLAUDE.md and the plugin/marketplace manifests parse.
The plugin root is the repository root (marketplace source "./"), so a marketplace-installed
copy carries template/ next to plugin/ (a script in a copied plugin cannot read above its
root)."""

import json
import os
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


def test_a_fixture_repository_is_built_once_and_every_copy_is_its_own(tmp_path, monkeypatch):
    """``tests/fixture_repos.py`` (choice 235): a template is built once per session, under
    the session's own environment, and each copy is an independent repository whose remote is
    its own; a commit pushed from one copy reaches neither the other copy nor the template."""
    import subprocess

    from tests import fixture_repos

    def git(cwd, *args):
        return subprocess.run(
            ["git", *args], cwd=cwd, capture_output=True, text=True, check=True, encoding="utf-8"
        ).stdout.strip()

    builds = []

    def build(base):
        builds.append(os.environ.get("SCAFFOLD_PROBE"))
        root, bare = base / "proj", base / "remote.git"
        root.mkdir()
        git(base, "init", "-q", "--bare", "-b", "main", str(bare))
        git(root, "init", "-q", "-b", "main")
        git(root, "config", "user.email", "owner@example.com")
        git(root, "config", "user.name", "Owner")
        (root / "a.txt").write_text("a\n", encoding="utf-8")
        git(root, "add", ".")
        git(root, "commit", "-q", "-m", "first")
        git(root, "remote", "add", "origin", str(bare))
        git(root, "push", "-q", "-u", "origin", "main")
        git(root, "fetch", "-q", "origin")  # FETCH_HEAD names the remote's path
        return git(root, "rev-parse", "HEAD")

    def relocate(dest):
        git(dest / "proj", "remote", "set-url", "origin", str(dest / "remote.git"))

    monkeypatch.setenv("SCAFFOLD_PROBE", "the requesting test's")
    first, second = tmp_path / "first", tmp_path / "second"
    first.mkdir()
    second.mkdir()
    head = fixture_repos.copy("scaffold-own", first, build, relocate)
    assert fixture_repos.copy("scaffold-own", second, build, relocate) == head
    assert builds == [None]  # once, and not under the requesting test's environment
    template = fixture_repos._templates["scaffold-own"][0]

    for dest in (first, second):
        assert git(dest / "proj", "remote", "get-url", "origin") == str(dest / "remote.git")
        assert (dest / "proj" / ".git" / "FETCH_HEAD").is_file()
        assert fixture_repos._files_naming(dest, template) == []  # FETCH_HEAD rewritten too
    (first / "proj" / "a.txt").write_text("changed\n", encoding="utf-8")
    git(first / "proj", "commit", "-q", "-am", "second")
    git(first / "proj", "push", "-q", "origin", "main")
    moved = git(first / "remote.git", "rev-parse", "main")
    assert moved != head
    assert git(second / "remote.git", "rev-parse", "main") == head
    assert git(second / "proj", "rev-parse", "HEAD") == head
    assert git(template / "remote.git", "rev-parse", "main") == head
    assert (second / "proj" / "a.txt").read_text(encoding="utf-8") == "a\n"


def test_a_fixture_repository_copy_that_still_names_its_template_is_refused(tmp_path):
    """A template whose git config names its own directory (a remote added by path) and no
    ``relocate`` would push from every copy into the template: the first copy is refused."""
    import subprocess

    import pytest

    from tests import fixture_repos

    def build(base):
        for args in (["init", "-q", "--bare", str(base / "remote.git")], ["init", "-q", "proj"]):
            subprocess.run(["git", *args], cwd=base, check=True, capture_output=True)
        subprocess.run(
            ["git", "remote", "add", "origin", str(base / "remote.git")],
            cwd=base / "proj",
            check=True,
            capture_output=True,
        )

    with pytest.raises(AssertionError, match="still names its template"):
        fixture_repos.copy("scaffold-unrelocated", tmp_path, build)
