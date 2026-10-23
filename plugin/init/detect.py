"""Detect (or propose) one-command build/test/lint targets (build guide step 14; article
p.27 step 1: 'wrap checks in a single target ... that exits non-zero on failure').

Python projects (session 1) and Node projects (session 2, from ``package.json`` scripts),
detected when that language leads the repository's counted signals (R61 part 2); the
registry hosts, the formatter commands and the secret-shaped paths /sdlc-init proposes
(R61 parts 1 and 5, R33).
Python targets are ``python -m ...`` commands and Node targets ``npm ...`` commands, so each
runs identically on Windows, in a cloud session and on a Linux runner (decision 7). A target
the detector cannot find or create is left as ``None``: the installer writes a placeholder
and the gate refuses to enter phase (c) until the owner provides one.
"""

from __future__ import annotations

import fnmatch
import json
import re
from dataclasses import dataclass, field
from pathlib import Path

PY_TEST_GLOBS = ("test_*.py", "*_test.py")

# Test-file lock (build guide step 25; OPERATING_MODEL section 8): the globs /sdlc-init writes
# into `sdlc.yaml: test_paths` for the detected language. They are the paths the PreToolUse
# hook freezes once a fix-type change has committed its reproducing test. Gitignore-style
# globs, matched against the project-relative path with forward slashes.
TEST_PATHS = {
    "python": [
        "tests/**",
        "test/**",
        "**/test_*.py",
        "**/*_test.py",
        "**/conftest.py",
    ],
    "node": [
        "test/**",
        "tests/**",
        "__tests__/**",
        "**/*.test.js",
        "**/*.spec.js",
        "**/*.test.ts",
        "**/*.spec.ts",
    ],
    "unknown": ["tests/**", "test/**"],
}


def test_paths(language: str) -> list[str]:
    """The default test-path globs for a detected language (unknown languages get the two
    conventional folders; the owner edits `test_paths` in sdlc.yaml afterwards)."""
    return list(TEST_PATHS.get(language, TEST_PATHS["unknown"]))


# Decision 35 (ROADMAP R24): the default risk-list items, and the globs /sdlc-init proposes
# for each, each only when it matches a file the project already has (a migrations folder,
# infra/, a production configuration). An item no glob matches stays a plain string, matched
# by its words as before; the owner keeps or edits the list in the change-0000 PR.
RISK_ITEMS = ("auth", "data migrations", "money movement", "production config")
RISK_GLOBS = {
    "auth": ("**/auth/**",),
    "data migrations": ("**/migrations/**", "alembic/versions/**"),
    "money movement": ("**/payments/**",),
    "production config": ("config/production.*", "infra/**", "**/*.tf"),
}
RISK_SCAN_EXCLUDE = (".git", ".venv", "venv", "node_modules", "__pycache__", "changes")


def risk_list(root: Path) -> list[str | dict[str, object]]:
    """The risk list /sdlc-init proposes: each default item, with the globs of ``RISK_GLOBS``
    that match at least one file of the project (``changes/`` and the usual tool folders left
    out), as ``{item, paths}``; an item none matches stays a plain string."""
    from hooks._common import matches  # noqa: PLC0415

    root = Path(root)
    files = [
        p.relative_to(root).as_posix()
        for p in root.rglob("*")
        if p.is_file() and not any(part in RISK_SCAN_EXCLUDE for part in p.relative_to(root).parts)
    ]
    out: list[str | dict[str, object]] = []
    for item in RISK_ITEMS:
        globs = [g for g in RISK_GLOBS[item] if any(matches(g, f) for f in files)]
        out.append({"item": item, "paths": globs} if globs else item)
    return out


@dataclass
class Target:
    command: str | None
    healthy: str
    origin: str  # "detected: <evidence>" | "created: <what>" | "none"


def _no_target() -> Target:
    return Target(None, "", "none")


@dataclass
class Detection:
    language: str
    build: Target
    test: Target
    lint: Target
    stats: dict[str, int] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)
    # The one-command install of everything build/test/lint need. The CI phase jobs run it
    # before the phase (plugin/ci/project_setup.py): a GitHub-hosted runner has neither the
    # project nor its test and lint tools installed, which failed the gate's `commands` check
    # on the first live design run (2026-09-21). None means "nothing to install".
    setup: Target = field(default_factory=_no_target)
    # R61 part 2: every language's counted signals (``language_signals``), for the report
    signals: dict[str, dict[str, object]] = field(default_factory=dict)

    def as_dict(self) -> dict:
        return {
            "language": self.language,
            "build": self.build.__dict__,
            "test": self.test.__dict__,
            "lint": self.lint.__dict__,
            "setup": self.setup.__dict__,
            "stats": self.stats,
            "notes": self.notes,
            "signals": self.signals,
        }


# The extra a Python project's setup command installs when pyproject.toml declares optional
# dependencies; the first declared extra is used when none of these is there.
SETUP_EXTRAS = ("dev", "test", "tests", "develop", "all")
# What a Python project needs installed when it declares no extra of its own: the toolchain
# the detected test and lint targets call.
PY_SETUP_TOOLS = "pytest ruff"


def optional_extra(pyproject: str) -> str | None:
    """The extra to install from ``[project.optional-dependencies]``, or None when there is
    none (PEP 621 tables only; a project with another layout gets the plain install)."""
    block = re.search(r"(?ms)^\[project\.optional-dependencies\]\s*$(.*?)(?=^\[|\Z)", pyproject)
    if not block:
        return None
    names = re.findall(r"(?m)^\s*[\"']?([A-Za-z0-9_.-]+)[\"']?\s*=", block.group(1))
    if not names:
        return None
    lower = {n.lower(): n for n in names}
    for preferred in SETUP_EXTRAS:
        if preferred in lower:
            return lower[preferred]
    return names[0]


def python_setup(root: Path, pyproject: str) -> Target:
    """The one-command install for a Python project (article p.27: one command, exits
    non-zero on failure)."""
    extra = optional_extra(pyproject)
    if extra:
        return Target(
            f'python -m pip install -e ".[{extra}]"',
            "'Successfully installed' and exit code 0",
            f"detected: [project.optional-dependencies] extra '{extra}' in pyproject.toml",
        )
    # No editable install without a declared extra: `pip install -e .` runs setuptools'
    # automatic package discovery, which refuses a flat layout with several top-level folders
    # (changes/, evals/, framework/ checked out by the CI job, the package itself) - observed on
    # the fourth live design run, 2026-09-21. Tests import the package from the working
    # directory anyway; a project that needs the install declares an extra.
    return Target(
        f"python -m pip install {PY_SETUP_TOOLS}",
        "'Successfully installed' and exit code 0",
        "created: the test and lint toolchain (no extras declared; no editable install)",
    )


def node_setup(root: Path) -> Target:
    """``npm ci`` when the lockfile is there (reproducible), else ``npm install``."""
    if (root / "package-lock.json").is_file():
        return Target("npm ci", "exit code 0", "detected: package-lock.json")
    return Target("npm install", "exit code 0", "created: no package-lock.json to install from")


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

    setup = python_setup(root, pyproject) if is_python else _no_target()
    return Detection(language, build, test, lint, stats, notes, setup)


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
    return Detection("node", build, test, lint, stats, notes, node_setup(root))


def detect(root: Path) -> Detection:
    """Entry point: the language that leads the counted signals (``language_signals``).
    Python's or Node's targets are detected when that language is dominant; any other leader,
    or a leader that is not dominant (a mixed repository), comes back with every target unset
    and a note, so /sdlc-init asks the owner for the commands (R61 part 2)."""
    root = Path(root)
    signals = language_signals(root)
    leader, dominant = leading_language(signals)
    pkg = _package_json(root)
    if leader == "unknown" or (leader == "node" and pkg is None):
        det = detect_python(root)  # "unknown", every target None, as before R61
    elif not dominant:
        det = _unset(
            leader,
            [
                f"mixed repository ({_signals_text(signals)}): no language holds two source "
                "files in three, so no target is detected; ask the owner for the commands"
            ],
        )
    elif leader == "python":
        det = detect_python(root)
    elif leader == "node":
        det = detect_node(root, pkg)  # type: ignore[arg-type]
    else:
        det = _unset(
            leader,
            [
                f"{leader} project ({_signals_text(signals)}): no target detection for "
                f"{leader}; ask the owner for the commands"
            ],
        )
    det.signals = signals
    return det


# --- R61 part 2: which language the repository is, counted -----------------------------------
# The trial readiness review of 2026-10-20 (risk 2): one helper `.py` file made a Node, Go or
# Rust repository "Python", with pytest, ruff and compileall targets that pass on nothing.
# Each language's source files are counted, and its manifest noted; a language takes part only
# with its manifest (Python also with `.py` files alone, which run without one). Python or
# Node targets are detected only when that language holds two source files in three of the
# taking part; otherwise the leader is returned with every target unset, and /sdlc-init asks
# the owner for the commands.
LANGUAGE_SUFFIXES = {
    "python": (".py",),
    "node": (".js", ".mjs", ".cjs", ".jsx", ".ts", ".tsx"),
    "rust": (".rs",),
    "go": (".go",),
    "java": (".java", ".kt"),
    "dotnet": (".cs", ".fs", ".vb"),
    "ruby": (".rb",),
}
LANGUAGE_MANIFESTS = {
    "python": ("pyproject.toml", "setup.py", "setup.cfg"),
    "node": ("package.json",),
    "rust": ("Cargo.toml",),
    "go": ("go.mod",),
    "java": ("pom.xml", "build.gradle", "build.gradle.kts"),
    "dotnet": ("*.csproj", "*.fsproj", "*.vbproj", "*.sln"),
    "ruby": ("Gemfile",),
}
DOMINANT_SHARE = 2 / 3
SIGNAL_SCAN_EXCLUDE = (
    ".git", ".venv", "venv", "node_modules", "__pycache__", ".tox", "target", "dist",
    "build", "vendor", "changes",
)  # fmt: skip


def language_signals(root: Path) -> dict[str, dict[str, object]]:
    """``{language: {"files": n, "manifests": [name, ...]}}`` for every language of
    ``LANGUAGE_SUFFIXES`` with at least one source file or manifest at the project root."""
    root = Path(root)
    files = dict.fromkeys(LANGUAGE_SUFFIXES, 0)
    by_suffix = {s: lang for lang, suffixes in LANGUAGE_SUFFIXES.items() for s in suffixes}
    for path in root.rglob("*"):
        rel = path.relative_to(root).parts
        if any(part in SIGNAL_SCAN_EXCLUDE for part in rel[:-1]) or not path.is_file():
            continue
        lang = by_suffix.get(path.suffix.lower())
        if lang:
            files[lang] += 1
    out: dict[str, dict[str, object]] = {}
    for lang in LANGUAGE_SUFFIXES:
        manifests = sorted(
            {p.name for pattern in LANGUAGE_MANIFESTS[lang] for p in root.glob(pattern)}
        )
        if files[lang] or manifests:
            out[lang] = {"files": files[lang], "manifests": manifests}
    return out


def _taking_part(signals: dict[str, dict[str, object]]) -> dict[str, int]:
    """The languages that take part, with their file counts: a manifest, or Python files."""
    return {
        lang: int(sig["files"])  # type: ignore[call-overload]
        for lang, sig in signals.items()
        if sig["manifests"] or (lang == "python" and sig["files"])
    }


def _signals_text(signals: dict[str, dict[str, object]]) -> str:
    parts = []
    for lang, sig in signals.items():
        manifests = ", ".join(sig["manifests"]) or "no manifest"  # type: ignore[arg-type]
        parts.append(f"{lang} {sig['files']} file(s) ({manifests})")
    return "; ".join(parts) or "none"


def leading_language(signals: dict[str, dict[str, object]]) -> tuple[str, bool]:
    """(language, dominant): the taking-part language with the most source files (Python,
    then Node, then the others on a tie, as before R61), and whether it holds
    ``DOMINANT_SHARE`` of their files; ``("unknown", False)`` when none takes part."""
    counts = _taking_part(signals)
    if not counts:
        return "unknown", False
    order = list(LANGUAGE_SUFFIXES)
    leader = max(counts, key=lambda lang: (counts[lang], -order.index(lang)))
    total = sum(counts.values())
    return leader, total == 0 or counts[leader] >= DOMINANT_SHARE * total


def _unset(language: str, notes: list[str]) -> Detection:
    return Detection(language, _no_target(), _no_target(), _no_target(), {}, notes)


# --- R61 part 1: the package registry the CI session may reach ---------------------------------
# What `sandbox.allowed_domains` proposes per language, beyond the hosts plugin/ci/
# settings.ci.json already allows (PyPI and npm): the owner keeps or edits the list in the
# change-0000 PR (options.md, row "Network allow list").
REGISTRY_DOMAINS = {
    "rust": ("crates.io", "index.crates.io", "static.crates.io"),
    "go": ("proxy.golang.org", "sum.golang.org"),
    "java": (
        "repo.maven.apache.org", "repo1.maven.org", "plugins.gradle.org", "services.gradle.org",
    ),
    "dotnet": ("api.nuget.org",),
    "ruby": ("rubygems.org", "index.rubygems.org"),
}  # fmt: skip


def registry_domains(signals: dict[str, dict[str, object]]) -> list[str]:
    """The registry hosts of every language that takes part, in ``REGISTRY_DOMAINS`` order."""
    present = _taking_part(signals)
    return [d for lang, domains in REGISTRY_DOMAINS.items() if lang in present for d in domains]


# --- R33: the formatter commands /sdlc-init proposes per file type ------------------------------
# `sdlc.yaml: hooks.formatters`, read by plugin/hooks/format_on_edit.py: each entry maps a glob
# (or a list of globs) to the `fix` commands run in order on the changed file and the `check`
# commands whose exit 1 is fed back; `{file}` is the file's project-relative path. Only what is
# cheap per file (p.23); a whole-project check (clippy, a type check) stays the lint target.
NODE_GLOBS = ["*.js", "*.jsx", "*.mjs", "*.cjs", "*.ts", "*.tsx"]
PY_GLOBS = ["*.py", "*.pyi"]
PY_OTHER_FORMATTERS = {
    "black": "python -m black --quiet {file}",
    "yapf": "python -m yapf --in-place {file}",
    "autopep8": "python -m autopep8 --in-place {file}",
}


def node_dependencies(pkg: dict) -> set[str]:
    """The package names of ``dependencies`` and ``devDependencies`` (choice 246: one helper
    for R33's formatter proposal and R14's ``@playwright/test``)."""
    names: set[str] = set()
    for key in ("dependencies", "devDependencies"):
        block = pkg.get(key)
        if isinstance(block, dict):
            names.update(str(name) for name in block)
    return names


def python_formatter(pyproject: str) -> str | None:
    """The formatter ``pyproject.toml`` configures other than ruff (``[tool.black]``,
    ``[tool.yapf]``, ``[tool.autopep8]``), or None: such a project gets a ``*.py`` mapping to
    its own formatter instead of ruff's (options.md, row "Formatter on edit")."""
    for name in PY_OTHER_FORMATTERS:
        if re.search(rf"(?m)^\s*\[tool\.{name}\]", pyproject):
            return name
    return None


def _rust_edition(cargo: str) -> str:
    match = re.search(r"""(?m)^\s*edition\s*=\s*["'](\d{4})["']""", cargo)
    return match.group(1) if match else "2021"


def formatters(root: Path, signals: dict[str, dict[str, object]] | None = None) -> list[dict]:
    """The ``hooks.formatters`` entries to propose, each language read on its own (a Node
    project with a helper ``.py`` file still gets prettier): a Python project on black, yapf
    or autopep8 gets that formatter for ``*.py`` and ``*.pyi`` (ruff stays the default
    otherwise, with no entry); a ``package.json`` with prettier or eslint in its
    dependencies gets them for the JavaScript and TypeScript files; a ``Cargo.toml`` gets
    rustfmt for ``*.rs``. Empty when nothing applies."""
    root = Path(root)
    signals = language_signals(root) if signals is None else signals
    out: list[dict] = []
    other = python_formatter(_read(root / "pyproject.toml"))
    if other and "python" in signals:
        out.append({"glob": list(PY_GLOBS), "fix": [PY_OTHER_FORMATTERS[other]]})
    pkg = _package_json(root)
    deps = node_dependencies(pkg) if pkg else set()
    fix: list[str] = []
    check: list[str] = []
    if "prettier" in deps:
        fix.append("npx --no prettier --write {file}")
    if "eslint" in deps:
        fix.append("npx --no eslint --fix {file}")
        check.append("npx --no eslint {file}")
    if fix:
        entry: dict = {"glob": list(NODE_GLOBS), "fix": fix}
        if check:
            entry["check"] = check
        out.append(entry)
    if (root / "Cargo.toml").is_file():
        edition = _rust_edition(_read(root / "Cargo.toml"))
        out.append({"glob": "*.rs", "fix": [f"rustfmt --edition {edition} {{file}}"]})
    return out


# --- R61 part 5: the project's secret-shaped files ----------------------------------------------
SECRET_PATTERNS = (
    "*.pem", "*.key", "*.p12", "*.pfx", "*.jks", "*.keystore", "id_rsa*", "credentials.json",
    "terraform.tfvars", "*-secret.yaml", "appsettings.*.json", ".npmrc",
)  # fmt: skip


def secret_paths(root: Path) -> list[str]:
    """The patterns of ``SECRET_PATTERNS`` that match a file of the project (the usual tool
    folders left out), for ``protected_paths`` and the ``Read`` deny rules; the owner confirms
    them in the change-0000 PR."""
    root = Path(root)
    names = {
        p.name
        for p in root.rglob("*")
        if p.is_file() and not any(part in RISK_SCAN_EXCLUDE for part in p.relative_to(root).parts)
    }
    return [pat for pat in SECRET_PATTERNS if any(fnmatch.fnmatchcase(n, pat) for n in names)]
