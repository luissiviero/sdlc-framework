"""Layer-1 tests for plugin/init: detection statistics, rendering, merges, idempotence."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

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
    assert "hooks" not in merged and merged["env"] == {"X": "1"}


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
    assert "Bash(python -m pytest*)" in settings["permissions"]["allow"]
    assert (root / "changes" / "0000-sdlc-init" / "intent.md").exists()
    assert (root / "changes" / "0000-sdlc-init" / "status.yaml").exists()

    # owner edits survive a re-run; the re-run changes nothing else
    cfg["protected_paths"] = ["sample_pkg/generated/**"]
    yamlish.dump_file(root / "sdlc.yaml", cfg)
    (root / "CLAUDE.md").write_text(
        (root / "CLAUDE.md").read_text(encoding="utf-8") + "\n- owner note\n", encoding="utf-8"
    )
    report2 = _run_init(root)
    assert report2["files"]["sdlc.yaml"] == "unchanged"
    assert report2["files"][".claude/settings.json"] == "unchanged"
    assert report2["files"]["REVIEW.md"] == "kept" and report2["files"]["CLAUDE.md"] == "unchanged"
    assert yamlish.load_file(root / "sdlc.yaml")["protected_paths"] == ["sample_pkg/generated/**"]
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
