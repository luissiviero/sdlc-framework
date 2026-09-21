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
        [sys.executable, str(INIT), "--root", str(root), "--profile", "lite", *extra],
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
    assert cfg["profile"] == "lite" and cfg["commands"]["test"] == "python -m pytest"
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
    text = (
        (root / "sdlc.yaml").read_text(encoding="utf-8").replace("version: 0.1.0", "version: 0.0.1")
    )
    (root / "sdlc.yaml").write_text(text, encoding="utf-8")
    report = _run_init(root)
    assert report["files"]["sdlc.yaml"] == "updated"
    new = (root / "sdlc.yaml").read_text(encoding="utf-8")
    assert "version: 0.1.0" in new and new.count("#") > 10


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
    assert det.test.permission_rule == "Bash(npm test*)"
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
    assert cfg["commands"] == {"build": "npm run build", "test": "npm test", "lint": "npm run lint"}
    settings = json.loads((root / ".claude" / "settings.json").read_text(encoding="utf-8"))
    for rule in ("Bash(npm run build *)", "Bash(npm test *)", "Bash(npm run lint *)"):
        assert rule in settings["permissions"]["allow"], rule
    assert "ruff.toml" not in report["files"]
    assert "npm test" in (root / "CLAUDE.md").read_text(encoding="utf-8")
    # the three targets really run, and the test target exits non-zero on failure
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
