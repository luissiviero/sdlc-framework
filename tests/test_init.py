"""Layer-1 tests for plugin/init: detection statistics, rendering, merges, idempotence."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from init import detect, sdlc_init
from state import yamlish

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "sample-python-project"
INIT = ROOT / "plugin" / "init" / "sdlc_init.py"


def test_detect_fixture_project():
    det = detect.detect(FIXTURE)
    assert det.language == "python"
    assert det.test.command == "python -m pytest" and det.test.origin.startswith("detected")
    assert det.lint.command == "python -m ruff check ." and det.lint.origin.startswith("detected")
    assert det.build.command == "python -m compileall -q ." and det.build.origin.startswith(
        "created"
    )
    assert det.stats["py_files"] == 4 and det.stats["test_files"] == 2
    assert det.stats["has_pyproject"] == 1 and det.stats["has_tests_dir"] == 1


def test_detect_empty_python_project_creates_targets(tmp_path):
    (tmp_path / "app.py").write_text("print('hi')\n", encoding="utf-8")
    det = detect.detect(tmp_path)
    assert det.test.command.startswith("python -m unittest") and det.test.origin.startswith(
        "created"
    )
    assert det.lint.origin.startswith("created") and det.build.origin.startswith("created")
    assert det.stats == {
        "py_files": 1,
        "test_files": 0,
        "has_pyproject": 0,
        "has_setup_py": 0,
        "has_tests_dir": 0,
    }
    assert len(det.notes) == 2


def test_detect_non_python_project(tmp_path):
    (tmp_path / "index.js").write_text("", encoding="utf-8")
    det = detect.detect(tmp_path)
    assert det.language == "unknown"
    assert det.build.command is None and det.test.command is None and det.lint.command is None


def test_detect_build_backend_and_flake8(tmp_path):
    (tmp_path / "pyproject.toml").write_text(
        '[build-system]\nrequires = ["setuptools"]\n', encoding="utf-8"
    )
    (tmp_path / "setup.cfg").write_text("[flake8]\nmax-line-length = 100\n", encoding="utf-8")
    det = detect.detect(tmp_path)
    assert det.build.command == "python -m build"
    assert det.lint.command == "python -m flake8"


def test_merge_helpers():
    assert sdlc_init.merge_missing({"a": 1, "n": {"x": 1}}, {"a": 2, "b": 3, "n": {"y": 2}}) == {
        "a": 1,
        "n": {"x": 1, "y": 2},
        "b": 3,
    }
    fresh = {
        "permissions": {"deny": ["WebFetch"], "allow": ["Bash(git *)"]},
        "enabledPlugins": {"sdlc@sdlc-framework": True},
        "extraKnownMarketplaces": {"sdlc-framework": {"source": {}}},
    }
    existing = {
        "permissions": {"deny": ["Bash(rm *)"], "allow": []},
        "hooks": {"PreToolUse": []},
        "env": {"X": "1"},
    }
    merged = sdlc_init.merge_settings(existing, fresh)
    assert merged["permissions"]["deny"] == ["Bash(rm *)", "WebFetch"]
    assert merged["permissions"]["allow"] == ["Bash(git *)"]
    assert merged["permissions"]["disableBypassPermissionsMode"] == "disable"
    assert merged["hooks"] == {"PreToolUse": []} and merged["env"] == {"X": "1"}


def test_merge_claude_md_keeps_existing_and_adds_missing_sections():
    skeleton = (
        "# demo\n\n## Commands\n- x\n\n## Conventions\n- c\n\n"
        "## Things Claude gets wrong\n- (none yet)\n\n## SDLC framework\n- s\n\n"
        "## Verifying your work\n- v\n"
    )
    existing = "# my project\n\n## Commands\n- mine\n\n## Conventions\n- mine\n"
    merged = sdlc_init.merge_claude_md(existing, skeleton)
    assert merged.startswith("# my project")
    assert merged.count("## Commands") == 1 and "- mine" in merged and "- x" not in merged
    assert "## Things Claude gets wrong" in merged and "## Verifying your work" in merged
    assert "## SDLC framework" in merged
    assert sdlc_init.merge_claude_md(None, skeleton) == skeleton
    assert sdlc_init.merge_claude_md(merged, skeleton) == merged  # idempotent


def _run_init(root: Path, *extra: str) -> dict:
    proc = subprocess.run(
        [sys.executable, str(INIT), "--root", str(root), "--profile", "full", *extra],
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(proc.stdout)


def test_init_on_fixture_copy_is_idempotent(tmp_path):
    root = tmp_path / "proj"
    shutil.copytree(FIXTURE, root)
    report = _run_init(root)
    files = report["files"]
    assert files["sdlc.yaml"] == "created" and files[".claude/settings.json"] == "created"
    assert files["REVIEW.md"] == "created" and files["changes/README.md"] == "created"
    assert files["CLAUDE.md"] == "created" and "ruff.toml" not in files  # ruff was detected
    assert report["change"] == {
        "id": "0000",
        "dir": "changes/0000-sdlc-init",
        "branch": "sdlc/0000/a",
    }
    cfg = yamlish.load_file(root / "sdlc.yaml")
    assert cfg["profile"] == "full" and cfg["commands"]["test"] == "python -m pytest"
    assert cfg["review"] == "parked"  # decision 21: off by default
    assert cfg["test_paths"] == detect.TEST_PATHS["python"]  # step 25: the test-file lock
    assert cfg["plugin"]["version"] == sdlc_init.plugin_version()
    settings = json.loads((root / ".claude" / "settings.json").read_text(encoding="utf-8"))
    assert "Bash(python -m pytest *)" in settings["permissions"]["allow"]
    assert (root / "changes" / "0000-sdlc-init" / "intent.md").exists()
    assert (root / "changes" / "0000-sdlc-init" / "status.yaml").exists()

    # owner edits survive a re-run (edited in place, comments and all); nothing else changes
    text = (root / "sdlc.yaml").read_text(encoding="utf-8")
    assert text.count("#") > 10, "template comments are kept on first write"
    text = text.replace("protected_paths: []", "protected_paths: [sample_pkg/generated/**]")
    (root / "sdlc.yaml").write_text(text, encoding="utf-8")
    (root / "CLAUDE.md").write_text(
        (root / "CLAUDE.md").read_text(encoding="utf-8") + "\n- owner note\n", encoding="utf-8"
    )
    report2 = _run_init(root)
    assert report2["files"]["sdlc.yaml"] == "unchanged"
    assert report2["files"][".claude/settings.json"] == "unchanged"
    assert report2["files"]["REVIEW.md"] == "kept" and report2["files"]["CLAUDE.md"] == "unchanged"
    assert yamlish.load_file(root / "sdlc.yaml")["protected_paths"] == ["sample_pkg/generated/**"]
    assert (root / "sdlc.yaml").read_text(encoding="utf-8").count("#") > 10, "comments kept"
    assert "- owner note" in (root / "CLAUDE.md").read_text(encoding="utf-8")


def test_init_creates_ruff_toml_when_no_linter(tmp_path):
    (tmp_path / "app.py").write_text("x = 1\n", encoding="utf-8")
    report = _run_init(tmp_path)
    assert report["files"]["ruff.toml"] == "created"
    assert report["detection"]["lint"]["origin"].startswith("created")


def test_init_detect_only_writes_nothing(tmp_path):
    (tmp_path / "app.py").write_text("x = 1\n", encoding="utf-8")
    report = _run_init(tmp_path, "--detect-only")
    assert "files" in report and report["files"] == {}
    assert not (tmp_path / "sdlc.yaml").exists()


def test_init_version_bump_patches_one_line_and_keeps_comments(tmp_path):
    root = tmp_path / "proj"
    shutil.copytree(FIXTURE, root)
    _run_init(root)
    current = sdlc_init.plugin_version()  # the manifest is the single source of the pin
    text = (
        (root / "sdlc.yaml")
        .read_text(encoding="utf-8")
        .replace(f"version: {current}", "version: 0.0.1")
    )
    (root / "sdlc.yaml").write_text(text, encoding="utf-8")
    report = _run_init(root)
    assert report["files"]["sdlc.yaml"] == "updated"
    updated = (root / "sdlc.yaml").read_text(encoding="utf-8")
    assert f"version: {current}" in updated and updated.count("#") > 10


def test_init_claude_md_from_proposal(tmp_path):
    (tmp_path / "app.py").write_text("x = 1\n", encoding="utf-8")
    prop = tmp_path / "CLAUDE.proposed.md"
    prop.write_text(
        "# my app\n\n## Commands\n- Test: `python -m pytest` — healthy: passed\n\n"
        "## Architecture\n- one file\n",
        encoding="utf-8",
    )
    report = _run_init(tmp_path, "--claude-md-from", str(prop))
    assert report["files"]["CLAUDE.md"] == "created"
    text = (tmp_path / "CLAUDE.md").read_text(encoding="utf-8")
    assert text.startswith("# my app") and text.count("## Commands") == 1 and "- one file" in text
    assert "## Verifying your work" in text and "## Things Claude gets wrong" in text


def test_init_escapes_commands_with_quotes_and_hashes(tmp_path):
    (tmp_path / "app.py").write_text("x = 1\n", encoding="utf-8")
    _run_init(tmp_path, "--test", 'python -m pytest -k "not slow" # fast')
    cfg = yamlish.load_file(tmp_path / "sdlc.yaml")
    assert cfg["commands"]["test"] == 'python -m pytest -k "not slow" # fast'
    settings = json.loads((tmp_path / ".claude" / "settings.json").read_text(encoding="utf-8"))
    assert "Bash(python -m pytest *)" in settings["permissions"]["allow"]


def test_init_accepts_preexisting_change_folder_with_only_the_proposal(tmp_path):
    """The command writes CLAUDE.proposed.md into changes/0000-sdlc-init/ before the installer
    runs (observed crash in the first live run, 2026-09-20)."""
    (tmp_path / "app.py").write_text("x = 1\n", encoding="utf-8")
    folder = tmp_path / "changes" / "0000-sdlc-init"
    folder.mkdir(parents=True)
    (folder / "CLAUDE.proposed.md").write_text("# app\n\n## Commands\n- x\n", encoding="utf-8")
    report = _run_init(tmp_path, "--claude-md-from", "changes/0000-sdlc-init/CLAUDE.proposed.md")
    assert report["change"]["dir"] == "changes/0000-sdlc-init"
    assert (folder / "status.yaml").exists() and (folder / "intent.md").exists()
    assert (folder / "CLAUDE.proposed.md").exists()
    assert (tmp_path / "CLAUDE.md").read_text(encoding="utf-8").startswith("# app")


# --- step 21 (session 2): Node detection, evals/, bands.yaml ---------------------------------
NODE_FIXTURE = ROOT / "tests" / "fixtures" / "sample-node-project"


def test_detect_node_fixture():
    det = detect.detect(NODE_FIXTURE)
    assert det.language == "node"
    assert det.test.command == "npm test" and det.test.origin.startswith("detected: scripts.test")
    assert det.lint.command == "npm run lint" and det.build.command == "npm run build"
    assert det.stats["has_test_script"] == 1 and det.stats["test_files"] == 1
    assert det.notes == []


def test_detect_node_without_scripts_creates_or_leaves_none(tmp_path):
    (tmp_path / "package.json").write_text(
        json.dumps(
            {
                "name": "x",
                "main": "index.js",
                "scripts": {"test": 'echo "Error: no test specified" && exit 1'},
            }
        ),
        encoding="utf-8",
    )
    (tmp_path / "index.js").write_text("module.exports = 1;\n", encoding="utf-8")
    det = detect.detect(tmp_path)
    assert det.language == "node"
    assert det.test.command == "node --test" and det.test.origin.startswith("created")
    assert det.lint.command is None and det.lint.origin == "none"
    assert det.build.command == "node --check index.js" and det.build.origin.startswith("created")
    assert len(det.notes) == 2


def test_detect_prefers_python_when_both_exist(tmp_path):
    (tmp_path / "package.json").write_text('{"scripts": {"test": "jest"}}', encoding="utf-8")
    (tmp_path / "app.py").write_text("x = 1\n", encoding="utf-8")
    assert detect.detect(tmp_path).language == "python"
    (tmp_path / "package.json").write_text("{not json", encoding="utf-8")
    (tmp_path / "app.py").unlink()
    assert detect.detect(tmp_path).language == "unknown"


def test_init_on_node_fixture_writes_npm_targets(tmp_path):
    root = tmp_path / "node"
    shutil.copytree(NODE_FIXTURE, root)
    report = _run_init(root)
    cfg = yamlish.load_file(root / "sdlc.yaml")
    assert cfg["commands"] == {
        "build": "npm run build",
        "test": "npm test",
        "lint": "npm run lint",
        "setup": "npm install",  # no package-lock.json in the fixture
    }
    assert cfg["test_paths"] == detect.TEST_PATHS["node"]  # step 25: the test-file lock
    settings = json.loads((root / ".claude" / "settings.json").read_text(encoding="utf-8"))
    for rule in ("Bash(npm run build *)", "Bash(npm test *)", "Bash(npm run lint *)"):
        assert rule in settings["permissions"]["allow"], rule
    assert "ruff.toml" not in report["files"]
    assert "npm test" in (root / "CLAUDE.md").read_text(encoding="utf-8")
    # the three targets really run, and the test target exits non-zero on failure
    if not shutil.which("npm"):
        pytest.skip("npm not installed: detection checked, execution skipped")
    for cmd in ("npm run build", "npm test", "npm run lint"):
        proc = subprocess.run(cmd, cwd=root, shell=True, capture_output=True, text=True)
        assert proc.returncode == 0, (cmd, proc.stdout, proc.stderr)
    proc = subprocess.run(
        "npm test",
        cwd=root,
        shell=True,
        capture_output=True,
        text=True,
        env={**os.environ, "SAMPLE_FAIL": "1"},
    )
    assert proc.returncode != 0


def test_init_writes_evals_and_bands_once(tmp_path):
    root = tmp_path / "proj"
    shutil.copytree(FIXTURE, root)
    report = _run_init(root)
    assert report["files"]["evals/README.md"] == "created"
    assert report["files"]["evals/cases/.gitkeep"] == "created"
    assert report["files"]["bands.yaml"] == "created"
    bands = yamlish.load_file(root / "bands.yaml")
    assert bands["metric"] == "ci_test_failure_rate" and bands["source"] == "github-actions"
    assert bands["rules"] == "western_electric" and bands["baseline"] == "rolling_30d"
    assert bands["tiers"]["1sigma"] == {"action": "log"}
    assert bands["tiers"]["2sigma"]["action"] == "diagnose"
    routes = bands["tiers"]["3sigma"]["routes"]
    assert {r["authorization"] for r in routes} == {"preapproved", "go"}
    assert (
        next(r for r in routes if r["name"] == "runbook:rollback-deploy")["authorization"] == "go"
    )
    readme = (root / "evals" / "README.md").read_text(encoding="utf-8")
    assert "starts empty on purpose" in readme and "p.30" in readme
    # owner edits survive: create-only files are kept on re-run
    (root / "bands.yaml").write_text("metric: my_metric\n", encoding="utf-8")
    report2 = _run_init(root)
    assert (
        report2["files"]["bands.yaml"] == "kept" and report2["files"]["evals/README.md"] == "kept"
    )
    assert (root / "bands.yaml").read_text(encoding="utf-8") == "metric: my_metric\n"


def test_bands_yaml_also_parses_with_pyyaml(tmp_path):
    yaml = pytest.importorskip("yaml")
    root = tmp_path / "proj"
    shutil.copytree(FIXTURE, root)
    _run_init(root)
    data = yaml.safe_load((root / "bands.yaml").read_text(encoding="utf-8"))
    assert data["tiers"]["3sigma"]["routes"][0]["name"] == "pull_request"


def test_init_upgrade_adds_new_top_level_keys_and_keeps_comments(tmp_path):
    """A project initialised by session 1 has no `paused` / `gate:` block; the re-run must add
    them with their template comments and leave the owner's edits and comments in place."""
    root = tmp_path / "proj"
    shutil.copytree(FIXTURE, root)
    _run_init(root)
    text = (root / "sdlc.yaml").read_text(encoding="utf-8")
    start = text.index("# --- confidence gate")
    end = text.index("# --- guardrails")
    old_style = text[:start] + text[end:]
    old_style = old_style.replace("protected_paths: []", "protected_paths: [gen/**]  # owner note")
    (root / "sdlc.yaml").write_text(old_style, encoding="utf-8")
    report = _run_init(root)
    assert report["files"]["sdlc.yaml"] == "updated (added paused, gate, test_paths)"
    new = (root / "sdlc.yaml").read_text(encoding="utf-8")
    assert "# owner note" in new and new.count("#") >= old_style.count("#") + 5
    cfg = yamlish.load_file(root / "sdlc.yaml")
    assert cfg["paused"] is False and cfg["gate"]["max_iterations"] == 3
    assert cfg["protected_paths"] == ["gen/**"]
    assert _run_init(root)["files"]["sdlc.yaml"] == "unchanged"


def test_init_unknown_language_gets_the_two_conventional_test_folders(tmp_path):
    (tmp_path / "main.go").write_text("package main\n", encoding="utf-8")
    _run_init(tmp_path)
    assert yamlish.load_file(tmp_path / "sdlc.yaml")["test_paths"] == ["tests/**", "test/**"]


def test_init_upgrade_adds_the_test_paths_block_once(tmp_path):
    """A project initialised before step 25 has no `test_paths:`: the re-run appends the block
    with its template comments, and a second run reports the file unchanged."""
    root = tmp_path / "proj"
    shutil.copytree(FIXTURE, root)
    _run_init(root)
    text = (root / "sdlc.yaml").read_text(encoding="utf-8")
    start = text.index("# --- test-file lock")
    end = text.index("# --- guardrails")
    (root / "sdlc.yaml").write_text(text[:start] + text[end:], encoding="utf-8")
    report = _run_init(root)
    assert report["files"]["sdlc.yaml"] == "updated (added test_paths)"
    new = (root / "sdlc.yaml").read_text(encoding="utf-8")
    assert new.count("test_paths:") == 1 and "# --- test-file lock" in new
    assert yamlish.load_file(root / "sdlc.yaml")["test_paths"] == detect.TEST_PATHS["python"]
    assert _run_init(root)["files"]["sdlc.yaml"] == "unchanged"


def test_detect_setup_command_per_language(tmp_path):
    """The one-command install the CI phase jobs run before the phase: the runner of the
    first live design run had neither pytest nor ruff (2026-09-21)."""
    assert detect.detect(FIXTURE).setup.command == "python -m pip install pytest ruff"
    assert detect.detect(NODE_FIXTURE).setup.command == "npm install"

    node = tmp_path / "node"
    node.mkdir()
    (node / "package.json").write_text('{"scripts": {"test": "jest"}}', encoding="utf-8")
    (node / "package-lock.json").write_text("{}", encoding="utf-8")
    assert detect.detect(node).setup.command == "npm ci"  # reproducible when locked

    extras = tmp_path / "extras"
    extras.mkdir()
    (extras / "pyproject.toml").write_text(
        '[project]\nname = "x"\n\n[project.optional-dependencies]\n'
        'lint = ["ruff"]\ndev = ["pytest", "ruff"]\n',
        encoding="utf-8",
    )
    assert detect.detect(extras).setup.command == 'python -m pip install -e ".[dev]"'

    bare = tmp_path / "bare"
    (bare / "pkg").mkdir(parents=True)
    (bare / "pkg" / "app.py").write_text("x = 1\n", encoding="utf-8")
    assert detect.detect(bare).setup.command == "python -m pip install pytest ruff"

    empty = tmp_path / "empty"
    empty.mkdir()
    assert detect.detect(empty).setup.command is None  # unknown language: nothing to install


def test_init_writes_an_empty_setup_for_an_unknown_project(tmp_path):
    root = tmp_path / "plain"
    root.mkdir()
    (root / "README.md").write_text("# a project with no toolchain\n", encoding="utf-8")
    _run_init(root)
    assert yamlish.load_file(root / "sdlc.yaml")["commands"]["setup"] == ""


def test_init_upgrade_adds_commands_setup_as_text(tmp_path):
    """A project initialised before this version has `commands:` without `setup`. The
    upgrade inserts the nested key as text, comments and layout intact."""
    root = tmp_path / "proj"
    shutil.copytree(FIXTURE, root)
    _run_init(root)
    text = (root / "sdlc.yaml").read_text(encoding="utf-8")
    pre = "\n".join(
        line
        for line in text.splitlines()
        if not line.strip().startswith(("setup:", "# one command that installs", "# the phase;"))
    )
    pre = pre.replace("protected_paths: []", "protected_paths: [gen/**]  # owner note")
    (root / "sdlc.yaml").write_text(pre + "\n", encoding="utf-8")
    assert "setup:" not in (root / "sdlc.yaml").read_text(encoding="utf-8")

    report = _run_init(root)
    assert report["files"]["sdlc.yaml"] == "updated (added commands.setup)"
    new_text = (root / "sdlc.yaml").read_text(encoding="utf-8")
    assert new_text.count("setup:") == 1 and "# owner note" in new_text
    assert "# one command that installs what test/build/lint need" in new_text
    for comment in [ln for ln in pre.splitlines() if ln.strip().startswith("#")]:
        assert comment in new_text
    cfg = yamlish.load_file(root / "sdlc.yaml")
    assert cfg["commands"]["setup"] == "python -m pip install pytest ruff"
    assert cfg["commands"]["test"] == "python -m pytest"  # the siblings are untouched
    assert _run_init(root)["files"]["sdlc.yaml"] == "unchanged"


def test_init_upgrade_adds_a_missing_nested_key_as_text(tmp_path):
    """A project initialised before B3 has `plugin:` but no `plugin.claude_code`, and no
    `test_paths:`. The upgrade adds both in one run, as text: re-serialising the file would
    drop every comment (and used to raise on the `**/test_*.py` default)."""
    root = tmp_path / "proj"
    shutil.copytree(FIXTURE, root)
    _run_init(root)
    text = (root / "sdlc.yaml").read_text(encoding="utf-8")
    start, end = text.index("# --- test-file lock"), text.index("# --- guardrails")
    pre_b3 = text[:start] + text[end:]
    pre_b3 = "\n".join(
        line
        for line in pre_b3.splitlines()
        if not line.strip().startswith(("claude_code:", "# @anthropic-ai/claude-code@<this>"))
    )
    pre_b3 = pre_b3.replace("protected_paths: []", "protected_paths: [gen/**]  # owner note")
    (root / "sdlc.yaml").write_text(pre_b3 + "\n", encoding="utf-8")

    report = _run_init(root)
    assert report["files"]["sdlc.yaml"] == "updated (added test_paths, plugin.claude_code)"
    new_text = (root / "sdlc.yaml").read_text(encoding="utf-8")
    assert new_text.count("claude_code:") == 1
    assert "# owner note" in new_text  # every comment the owner had is still there
    for comment in [ln for ln in pre_b3.splitlines() if ln.strip().startswith("#")]:
        assert comment in new_text
    cfg = yamlish.load_file(root / "sdlc.yaml")
    assert cfg["plugin"]["claude_code"] == sdlc_init.DEFAULT_CLAUDE_CODE_VERSION
    assert cfg["test_paths"] == detect.TEST_PATHS["python"]
    assert _run_init(root)["files"]["sdlc.yaml"] == "unchanged"


# --- the SDLC workflows /sdlc-init installs (build guide step 30, task 30.8) -----------------
def _git_init(root: Path, branch: str) -> None:
    """A repository with one commit, so gitops.default_branch() has a HEAD to read."""
    run = lambda *a: subprocess.run(  # noqa: E731
        ["git", "-C", str(root), *a], check=True, capture_output=True
    )
    subprocess.run(["git", "init", "-b", branch, str(root)], check=True, capture_output=True)
    run("config", "user.email", "test@example.com")
    run("config", "user.name", "test")
    run("add", "-A")
    run("commit", "-m", "fixture")


WORKFLOWS = (
    ".github/workflows/sdlc-design.yml",
    ".github/workflows/sdlc-build.yml",
    ".github/workflows/sdlc-test.yml",
    ".github/workflows/sdlc-deploy.yml",
    ".github/workflows/sdlc-digest.yml",
    ".github/workflows/sdlc-release.yml",  # build guide step 32.3 (plugin 0.2.12)
    ".github/workflows/sdlc-fix.yml",  # decisions 22 and 24 (plugin 0.2.13)
    ".github/workflows/sdlc-abandon.yml",  # decision 25 (plugin 0.2.13)
)
PIN_SCRIPT = ".github/scripts/sdlc_pin.py"


def test_init_upgrade_installs_the_release_workflow_beside_kept_ones(tmp_path):
    """A project initialised before 0.2.12 has the five older workflows; re-running
    /sdlc-init creates the release workflow and keeps the files it already has."""
    root = tmp_path / "proj"
    shutil.copytree(FIXTURE, root)
    _run_init(root)
    release = root / WORKFLOWS[5]
    release.unlink()  # the project as an older framework left it
    (root / WORKFLOWS[0]).write_text("name: an older design workflow\n", encoding="utf-8")
    report = _run_init(root)
    assert report["files"][WORKFLOWS[5]] == "created" and release.is_file()
    # 0.2.13: a differing file is reported as outdated, so the owner knows to replace it
    assert report["files"][WORKFLOWS[0]].startswith("outdated: differs from what plugin ")
    assert "an older design workflow" in (root / WORKFLOWS[0]).read_text(encoding="utf-8")
    assert "python framework/plugin/release/cli.py run" in release.read_text(encoding="utf-8")


def test_init_installs_the_workflows_and_the_pin_script(tmp_path):
    root = tmp_path / "proj"
    shutil.copytree(FIXTURE, root)
    report = _run_init(root)
    for rel in (*WORKFLOWS, PIN_SCRIPT):
        assert report["files"][rel] == "created", rel
        assert (root / rel).is_file()
    design = (root / WORKFLOWS[0]).read_text(encoding="utf-8")
    assert "{{" not in design.replace("${{", "")  # only GitHub's own expressions are left
    assert 'repository: "luissiviero/sdlc-framework"' in design
    # the CLI version comes from the pin step at run time, so a later sdlc.yaml bump applies;
    # it reaches the shell through a step-level env var, never interpolated into the run line
    assert "CLAUDE_CODE_VERSION: ${{ steps.pin.outputs.claude_code }}" in design
    assert 'npm install -g @anthropic-ai/claude-code@"$CLAUDE_CODE_VERSION"' in design
    assert "path: framework" in design
    # the pin the workflows check out comes from sdlc.yaml, not from the template
    cfg = yamlish.load_file(root / "sdlc.yaml")
    assert cfg["plugin"]["claude_code"] == sdlc_init.DEFAULT_CLAUDE_CODE_VERSION
    proc = subprocess.run(
        [sys.executable, str(root / PIN_SCRIPT), "--root", str(root)],
        capture_output=True,
        text=True,
        check=True,
    )
    assert f"ref=v{sdlc_init.plugin_version()}" in proc.stdout

    # re-running changes nothing and says so
    report2 = _run_init(root)
    for rel in (*WORKFLOWS, PIN_SCRIPT):
        assert report2["files"][rel] == "unchanged", rel


def test_init_keeps_a_workflow_the_owner_already_wrote(tmp_path):
    root = tmp_path / "proj"
    shutil.copytree(FIXTURE, root)
    target = root / WORKFLOWS[2]
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("name: mine\non: workflow_dispatch\n", encoding="utf-8")
    report = _run_init(root)
    assert report["files"][WORKFLOWS[2]].startswith("outdated: ")
    assert "replace it" in report["files"][WORKFLOWS[2]]
    assert target.read_text(encoding="utf-8") == "name: mine\non: workflow_dispatch\n"
    assert report["files"][WORKFLOWS[0]] == "created"  # the others are still installed


def test_init_rewrites_the_base_branch_filter_to_the_projects_default(tmp_path):
    root = tmp_path / "proj"
    shutil.copytree(FIXTURE, root)
    _git_init(root, "trunk")
    _run_init(root)
    for rel in (WORKFLOWS[0], WORKFLOWS[1], WORKFLOWS[5]):  # the three merge-triggered ones
        text = (root / rel).read_text(encoding="utf-8")
        lines = [ln for ln in text.splitlines() if ln.startswith("    branches:")]
        assert lines == ["    branches: [trunk]"], rel
    # the label-triggered ones carry no base filter at all
    labeled = (root / WORKFLOWS[2]).read_text(encoding="utf-8")
    assert not [ln for ln in labeled.splitlines() if ln.startswith("    branches:")]


def test_init_substitution_helpers_are_pure(tmp_path):
    values = {"FRAMEWORK_REPO": "me/fw", "CLAUDE_CODE_VERSION": "9.9.9"}
    text = sdlc_init.render_workflow(".github/workflows/sdlc-design.yml", values, "develop")
    assert "branches: [develop]" in text and "me/fw" in text
    assert "CLAUDE_CODE_VERSION: ${{ steps.pin.outputs.claude_code }}" in text
    assert 'claude-code@"$CLAUDE_CODE_VERSION"' in text
    same = sdlc_init.render_workflow(".github/workflows/sdlc-design.yml", values, "main")
    assert "branches: [main]" in same


# --- decision 23: GitHub only ------------------------------------------------------------------
def _with_origin(root: Path, url: str | None) -> None:
    _git_init(root, "main")
    if url:
        subprocess.run(
            ["git", "-C", str(root), "remote", "add", "origin", url],
            check=True,
            capture_output=True,
        )


def test_remote_host_reads_every_url_form():
    host = sdlc_init.remote_host
    assert host("https://github.com/a/b.git") == "github.com"
    assert host("git@github.com:a/b.git") == "github.com"
    assert host("ssh://git@github.com/a/b") == "github.com"
    assert host("https://user@GitHub.com/a/b") == "github.com"
    assert host("https://gitlab.com/a/b.git") == "gitlab.com"
    assert host("git@bitbucket.org:a/b.git") == "bitbucket.org"
    for local in ("/tmp/remote.git", "../remote.git", "file:///tmp/r.git", "C:\\work\\r.git", ""):
        assert host(local) is None, local


def test_init_refuses_a_project_hosted_elsewhere(tmp_path):
    """Every trigger, identity, label, check run and the digest issue are GitHub-specific:
    a non-GitHub origin is refused with the reason and nothing is written."""
    root = tmp_path / "proj"
    shutil.copytree(FIXTURE, root)
    _with_origin(root, "https://gitlab.com/someone/proj.git")
    ok, note = sdlc_init.hosting(root)
    assert ok is False and "gitlab.com, not github.com" in note and "decision 23" in note
    proc = subprocess.run(
        [sys.executable, str(sdlc_init.__file__), "--root", str(root), "--profile", "standard"],
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 2
    assert "not github.com" in proc.stderr
    assert json.loads(proc.stdout.splitlines()[0])["error"].startswith("hosting:")
    assert not (root / "sdlc.yaml").exists() and not (root / ".github").exists()
    # --detect-only is refused the same way: the answer would mislead
    proc = subprocess.run(
        [sys.executable, str(sdlc_init.__file__), "--root", str(root), "--detect-only"],
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 2


def test_init_accepts_github_and_lets_a_local_or_missing_origin_through(tmp_path):
    github = tmp_path / "gh"
    shutil.copytree(FIXTURE, github)
    _with_origin(github, "https://github.com/someone/proj.git")
    report = _run_init(github)
    assert report["hosting"] == "GitHub (https://github.com/someone/proj.git)"
    assert (github / "sdlc.yaml").exists()
    # a local bare remote (the fixture tests) or no remote at all: installed, with the note
    local = tmp_path / "local"
    shutil.copytree(FIXTURE, local)
    bare = tmp_path / "remote.git"
    subprocess.run(["git", "init", "-q", "--bare", str(bare)], check=True)
    _with_origin(local, str(bare))
    report = _run_init(local)
    assert report["hosting"].startswith("not GitHub (local remote ")
    assert "the CI plumbing will not run" in report["hosting"]
    none = tmp_path / "none"
    shutil.copytree(FIXTURE, none)
    _with_origin(none, None)
    assert _run_init(none)["hosting"] == (
        "not GitHub (no origin remote): the CI plumbing will not run; the commands work by hand"
    )
    plain = tmp_path / "plain"  # not even a git repository (the layer-1 tests' case)
    shutil.copytree(FIXTURE, plain)
    assert _run_init(plain)["hosting"].startswith("not GitHub (not a git repository)")
