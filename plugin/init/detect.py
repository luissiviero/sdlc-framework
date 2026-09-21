"""Detect (or propose) one-command build/test/lint targets (build guide step 14; article
p.27 step 1: 'wrap checks in a single target ... that exits non-zero on failure').

Python projects (session 1) and Node projects (session 2, from ``package.json`` scripts).
Python targets are ``python -m ...`` commands and Node targets ``npm ...`` commands, so each
runs identically on Windows, in a cloud session and on a Linux runner (decision 7). A target
the detector cannot find or create is left as ``None``: the installer writes a placeholder
and the gate refuses to enter phase (c) until the owner provides one.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

PY_TEST_GLOBS = ("test_*.py", "*_test.py")


@dataclass
class Target:
    command: str | None
    healthy: str
    origin: str  # "detected: <evidence>" | "created: <what>" | "none"


@dataclass
class Detection:
    language: str
    build: Target
    test: Target
    lint: Target
    stats: dict[str, int] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "language": self.language,
            "build": self.build.__dict__,
            "test": self.test.__dict__,
            "lint": self.lint.__dict__,
            "stats": self.stats,
            "notes": self.notes,
        }


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def _count(
    root: Path, pattern: str, exclude=(".git", ".venv", "venv", "node_modules", "__pycache__")
) -> int:
    n = 0
    for p in root.rglob(pattern):
        if any(part in exclude for part in p.parts):
            continue
        if p.is_file():
            n += 1
    return n


def _mentions(text: str, name: str) -> bool:
    return (
        re.search(rf"(?im)^\s*\[?tool\.{re.escape(name)}\b|\b{re.escape(name)}\b", text) is not None
    )


def detect_python(root: Path) -> Detection:
    root = Path(root)
    pyproject = _read(root / "pyproject.toml")
    setup_cfg = _read(root / "setup.cfg")
    tox_ini = _read(root / "tox.ini")
    requirements = "\n".join(_read(p) for p in root.glob("requirements*.txt"))
    deps_text = "\n".join([pyproject, setup_cfg, requirements])

    stats = {
        "py_files": _count(root, "*.py"),
        "test_files": sum(_count(root, g) for g in PY_TEST_GLOBS),
        "has_pyproject": int((root / "pyproject.toml").is_file()),
        "has_setup_py": int((root / "setup.py").is_file()),
        "has_tests_dir": int((root / "tests").is_dir() or (root / "test").is_dir()),
    }
    is_python = stats["py_files"] > 0 or stats["has_pyproject"] or stats["has_setup_py"]
    language = "python" if is_python else "unknown"
    notes: list[str] = []

    # --- test -----------------------------------------------------------------------------
    pytest_configured = (
        "[tool.pytest" in pyproject
        or (root / "pytest.ini").is_file()
        or "[pytest]" in tox_ini
        or "[tool:pytest]" in setup_cfg
        or re.search(r"(?m)^\s*\"?pytest", deps_text) is not None
    )
    if pytest_configured or stats["test_files"] > 0:
        why = "pytest configuration" if pytest_configured else f"{stats['test_files']} test files"
        test = Target(
            "python -m pytest",
            "'N passed' and exit code 0",
            f"detected: {why}",
        )
    elif is_python:
        test = Target(
            "python -m unittest discover -v",
            "'OK' and exit code 0",
            "created: unittest discovery (no tests found yet; add tests/test_*.py)",
        )
        notes.append("no tests found: the test target is unittest discovery until tests exist")
    else:
        test = Target(None, "", "none")

    # --- lint -----------------------------------------------------------------------------
    if (
        "[tool.ruff" in pyproject
        or (root / "ruff.toml").is_file()
        or (root / ".ruff.toml").is_file()
    ):
        lint = Target(
            "python -m ruff check .",
            "'All checks passed!'",
            "detected: ruff configuration",
        )
    elif _mentions(deps_text, "ruff"):
        lint = Target(
            "python -m ruff check .",
            "'All checks passed!'",
            "detected: ruff in dependencies",
        )
    elif "[flake8]" in setup_cfg or (root / ".flake8").is_file() or "[flake8]" in tox_ini:
        lint = Target(
            "python -m flake8",
            "no output and exit code 0",
            "detected: flake8 configuration",
        )
    elif is_python:
        lint = Target(
            "python -m ruff check .",
            "'All checks passed!'",
            "created: ruff.toml with default rules (pip install ruff)",
        )
        notes.append(
            "no linter configured: /sdlc-init creates ruff.toml; install ruff in the environment"
        )
    else:
        lint = Target(None, "", "none")

    # --- build ----------------------------------------------------------------------------
    if "[build-system]" in pyproject:
        build = Target(
            "python -m build",
            "'Successfully built' and exit code 0",
            "detected: [build-system] in pyproject.toml",
        )
    elif is_python:
        build = Target(
            "python -m compileall -q .",
            "no output and exit code 0",
            "created: byte-compile as the build check (no packaging configured)",
        )
    else:
        build = Target(None, "", "none")

    return Detection(language, build, test, lint, stats, notes)


def _package_json(root: Path) -> dict | None:
    path = root / "package.json"
    if not path.is_file():
        return None
    try:
        data = json.loads(_read(path) or "{}")
    except ValueError:
        return None
    return data if isinstance(data, dict) else None


def detect_node(root: Path, pkg: dict) -> Detection:
    """Targets from package.json ``scripts`` (npm runs them the same way on every OS)."""
    scripts = pkg.get("scripts") if isinstance(pkg.get("scripts"), dict) else {}
    stats = {
        "js_files": _count(root, "*.js") + _count(root, "*.mjs") + _count(root, "*.cjs"),
        "ts_files": _count(root, "*.ts") + _count(root, "*.tsx"),
        "test_files": _count(root, "*.test.*") + _count(root, "*.spec.*"),
        "has_test_script": int("test" in scripts),
        "has_lint_script": int("lint" in scripts),
        "has_build_script": int("build" in scripts),
    }
    notes: list[str] = []
    placeholder_test = 'echo "Error: no test specified" && exit 1'
    if "test" in scripts and scripts["test"].strip() != placeholder_test:
        test = Target(
            "npm test",
            "exit code 0",
            f"detected: scripts.test = {scripts['test']}",
        )
    else:
        test = Target(
            "node --test",
            "'# fail 0' and exit code 0",
            "created: node's built-in test runner (add *.test.js files; needs Node 18+)",
        )
        notes.append(
            "no test script in package.json: the test target is `node --test` until one exists"
        )
    if "lint" in scripts:
        lint = Target(
            "npm run lint",
            "exit code 0",
            f"detected: scripts.lint = {scripts['lint']}",
        )
    else:
        lint = Target(None, "", "none")
        notes.append("no lint script in package.json: add one (e.g. eslint) and re-run /sdlc-init")
    if "build" in scripts:
        build = Target(
            "npm run build",
            "exit code 0",
            f"detected: scripts.build = {scripts['build']}",
        )
    elif isinstance(pkg.get("main"), str) and pkg["main"].strip():
        build = Target(
            f"node --check {pkg['main'].strip()}",
            "no output and exit code 0",
            "created: syntax check of package.json main (no build script)",
        )
    else:
        build = Target(None, "", "none")
        notes.append("no build script and no main in package.json: add a build script")
    return Detection("node", build, test, lint, stats, notes)


def detect(root: Path) -> Detection:
    """Entry point: Python when Python signals exist, else Node when package.json exists."""
    root = Path(root)
    py = detect_python(root)
    if py.language == "python":
        return py
    pkg = _package_json(root)
    if pkg is not None:
        return detect_node(root, pkg)
    return py
