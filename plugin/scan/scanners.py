"""The deterministic scanners of the weekly scan (decision 16; article p.48: "The
deterministic checks stay in CI, and the model-driven scan covers the context-dependent
vulnerabilities those checks are not built to find").

``plan(root, language)`` says which scanners apply to the project and how to install and run
them; ``run_all`` runs them, each a subprocess with a timeout, and collects exit codes and
report paths without ever raising; ``summary`` renders a markdown table for the job summary.
They are reports, not gates: a scanner that finds something exits non-zero, and the
workflow step keeps going.

pip-audit, bandit and npm are CI dependencies of the *project's* workflow, installed on the
runner by the step itself; the plugin's own runtime stays dependency-free (decision 7).
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

INSTALL_TIMEOUT = 600
RUN_TIMEOUT = 900
EXCLUDED = ("./tests", "./changes", "./evals", "./framework")  # framework: the pinned checkout
PYTHON_LANGUAGES = ("python",)
NODE_LANGUAGES = ("node", "javascript", "typescript")
OUTPUT_TAIL = 2000


def _requirements(root: Path) -> list[str]:
    return sorted(p.name for p in Path(root).glob("requirements*.txt") if p.is_file())


def _pip_audit_target(root: Path) -> list[str]:
    """What pip-audit audits: the project's requirements files, else the project itself
    (``pyproject.toml`` / ``setup.py``), else the environment it runs in."""
    reqs = _requirements(root)
    if reqs:
        out: list[str] = []
        for name in reqs:
            out += ["-r", name]
        return out
    if any((Path(root) / name).is_file() for name in ("pyproject.toml", "setup.py", "setup.cfg")):
        return ["."]
    return []


def plan(root: Path, language: str) -> list[dict[str, Any]]:
    """The scanners for the project's language: ``{name, install, run, report}`` each, with
    ``install`` an argv or None and ``report`` the file the scanner leaves in the project
    root. ``report_from_stdout`` marks a scanner whose report is its standard output."""
    root = Path(root)
    language = (language or "").strip().lower()
    if language in PYTHON_LANGUAGES:
        return [
            {
                "name": "pip-audit",
                "install": ["python", "-m", "pip", "install", "pip-audit"],
                "run": ["python", "-m", "pip_audit", "--strict", "--desc", "--format", "json",
                        "--output", "pip-audit.json", *_pip_audit_target(root)],
                "report": "pip-audit.json",
                "report_from_stdout": False,
            },
            {
                "name": "bandit",
                "install": ["python", "-m", "pip", "install", "bandit"],
                "run": ["python", "-m", "bandit", "-r", ".", "-x", ",".join(EXCLUDED),
                        "-f", "json", "-o", "bandit.json", "--severity-level", "medium"],
                "report": "bandit.json",
                "report_from_stdout": False,
            },
        ]  # fmt: skip
    if language in NODE_LANGUAGES:
        return [
            {
                "name": "npm-audit",
                "install": None,
                "run": ["npm", "audit", "--audit-level=high", "--json"],
                "report": "npm-audit.json",
                "report_from_stdout": True,
            }
        ]
    return []


def _executable(argv: list[str]) -> list[str]:
    """``python`` is this interpreter; ``npm`` is found on PATH (``npm.cmd`` on Windows)."""
    if not argv:
        return argv
    if argv[0] == "python":
        return [sys.executable or "python", *argv[1:]]
    found = shutil.which(argv[0])
    return [found, *argv[1:]] if found else list(argv)


def _run(argv: list[str], root: Path, timeout: int) -> dict[str, Any]:
    started = time.monotonic()
    try:
        proc = subprocess.run(
            _executable(argv),
            cwd=str(root),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return {"exit_code": 124, "stdout": "", "error": f"did not finish within {timeout}s",
                "seconds": round(time.monotonic() - started, 1)}  # fmt: skip
    except OSError as exc:
        return {"exit_code": 127, "stdout": "", "error": f"could not start: {exc}",
                "seconds": round(time.monotonic() - started, 1)}  # fmt: skip
    return {
        "exit_code": proc.returncode,
        "stdout": proc.stdout or "",
        "error": (proc.stderr or "").strip()[-OUTPUT_TAIL:],
        "seconds": round(time.monotonic() - started, 1),
    }


def run_one(
    root: Path,
    scanner: dict[str, Any],
    *,
    dry_run: bool,
    install_timeout: int = INSTALL_TIMEOUT,
    run_timeout: int = RUN_TIMEOUT,
) -> dict[str, Any]:
    """One scanner's result: ``status`` is ``dry-run``, ``clean`` (exit 0), ``findings``
    (non-zero exit with a report), ``install-failed`` or ``error``."""
    root = Path(root)
    out: dict[str, Any] = {
        "name": scanner["name"],
        "install": scanner.get("install"),
        "run": scanner["run"],
        "report": scanner["report"],
        "exit_code": None,
        "status": "dry-run",
    }
    if dry_run:
        return out
    try:
        if scanner.get("install"):
            installed = _run(scanner["install"], root, install_timeout)
            out["install_exit_code"] = installed["exit_code"]
            if installed["exit_code"] != 0:
                out["status"] = "install-failed"
                out["error"] = installed["error"] or f"exit {installed['exit_code']}"
                return out
        ran = _run(scanner["run"], root, run_timeout)
        out["exit_code"] = ran["exit_code"]
        out["seconds"] = ran["seconds"]
        report = root / scanner["report"]
        if scanner.get("report_from_stdout") and ran["stdout"].strip():
            report.write_text(ran["stdout"], encoding="utf-8", newline="\n")
        has_report = report.is_file()
        out["report_path"] = scanner["report"] if has_report else None
        if ran["exit_code"] == 0:
            out["status"] = "clean"
        elif has_report and ran["exit_code"] not in (124, 127):
            out["status"] = "findings"
        else:
            out["status"] = "error"
            out["error"] = ran["error"] or f"exit {ran['exit_code']}"
    except Exception as exc:  # noqa: BLE001 - a scanner never fails the scan step
        out["status"] = "error"
        out["error"] = str(exc)
    return out


def run_all(root: Path, language: str, *, dry_run: bool) -> dict[str, Any]:
    """Every planned scanner, in order; never raises."""
    try:
        planned = plan(root, language)
    except Exception as exc:  # noqa: BLE001
        return {"language": language, "dry_run": dry_run, "scanners": [], "error": str(exc)}
    return {
        "language": language,
        "dry_run": dry_run,
        "scanners": [run_one(root, s, dry_run=dry_run) for s in planned],
    }


def summary(results: dict[str, Any]) -> str:
    """The markdown table of the scanners' results (the job summary)."""
    lines = ["## Deterministic scanners (decision 16; article p.48)"]
    scanners = results.get("scanners") or []
    if not scanners:
        lines += [
            "",
            f"No deterministic scanner is configured for language "
            f"'{results.get('language') or 'unknown'}'.",
        ]
        if results.get("error"):
            lines.append(f"Error: {results['error']}")
        return "\n".join(lines) + "\n"
    lines += ["", "| Scanner | Status | Exit code | Report |", "|---|---|---|---|"]
    for item in scanners:
        code = item.get("exit_code")
        report = item.get("report_path") or (item.get("report") if item["status"] == "dry-run"
                                             else None)  # fmt: skip
        lines.append(
            f"| {item['name']} | {item['status']} | {'' if code is None else code} | "
            f"{f'`{report}`' if report else '-'} |"
        )
    errors = [i for i in scanners if i.get("error")]
    if errors:
        lines.append("")
        for item in errors:
            tail = " ".join(str(item["error"]).split())[:300]
            lines.append(f"- {item['name']}: {tail}")
    lines += [
        "",
        "Reports, not gates: a finding here is read by the owner; the model-driven weekly "
        "review files the context-dependent ones as incident intents.",
    ]
    return "\n".join(lines) + "\n"
