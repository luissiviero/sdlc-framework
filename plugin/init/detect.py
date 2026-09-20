"""Detect (or propose) one-command build/test/lint targets (build guide step 14; article
p.27 step 1: 'wrap checks in a single target ... that exits non-zero on failure').

Python projects first (handoff deliverable 8). Every target is a ``python -m ...`` command so
it runs identically on Windows, in a cloud session and on a Linux runner (decision 7).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

PY_TEST_GLOBS = ("test_*.py", "*_test.py")


@dataclass
class Target:
    command: str | None
    healthy: str
    origin: str  # "detected: <evidence>" | "created: <what>" | "none"
    permission_rule: str | None = None


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
            "Bash(python -m pytest*)",
        )
    elif is_python:
        test = Target(
            "python -m unittest discover -v",
            "'OK' and exit code 0",
            "created: unittest discovery (no tests found yet; add tests/test_*.py)",
            "Bash(python -m unittest*)",
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
            "Bash(python -m ruff*)",
        )
    elif _mentions(deps_text, "ruff"):
        lint = Target(
            "python -m ruff check .",
            "'All checks passed!'",
            "detected: ruff in dependencies",
            "Bash(python -m ruff*)",
        )
    elif "[flake8]" in setup_cfg or (root / ".flake8").is_file() or "[flake8]" in tox_ini:
        lint = Target(
            "python -m flake8",
            "no output and exit code 0",
            "detected: flake8 configuration",
            "Bash(python -m flake8*)",
        )
    elif is_python:
        lint = Target(
            "python -m ruff check .",
            "'All checks passed!'",
            "created: ruff.toml with default rules (pip install ruff)",
            "Bash(python -m ruff*)",
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
            "Bash(python -m build*)",
        )
    elif is_python:
        build = Target(
            "python -m compileall -q .",
            "no output and exit code 0",
            "created: byte-compile as the build check (no packaging configured)",
            "Bash(python -m compileall*)",
        )
    else:
        build = Target(None, "", "none")

    return Detection(language, build, test, lint, stats, notes)


def detect(root: Path) -> Detection:
    """Entry point; only Python is implemented in this session (handoff deliverable 8)."""
    return detect_python(root)
