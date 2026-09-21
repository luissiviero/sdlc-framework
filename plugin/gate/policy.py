"""Shared plumbing for the policy skills' deterministic checks (build guide step 20; article
p.22: the example skill "ends by running a deterministic script and including its output").

Each skill under ``plugin/skills/<name>/`` ships a ``check.py`` that uses this module to look
at the change's diff and print a short report; the skill's body tells the model to run it
and include the output. The scripts are advisory (the skill is "a control, though an
advisory one", p.22): they exit 1 when they found something to look at, 0 otherwise, and
never edit anything. The must-hold policies have a hook (step 15) or a gate check (step 16)
behind them.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

PLUGIN_DIR = Path(__file__).resolve().parent.parent
if str(PLUGIN_DIR) not in sys.path:
    sys.path.insert(0, str(PLUGIN_DIR))

from gate import diff as diffmod  # noqa: E402
from hooks._common import ConfigError, load_sdlc_config  # noqa: E402

# The identities the framework itself runs under (OPERATING_MODEL section 8: the automation
# identity has branch-only write access; only the owner merges). A project overrides the list
# with `sdlc.yaml: automation_identity` — the GitHub Actions bot is the default, matched
# against a commit's author name or email. The gate's `owner_actions` check (build guide step
# 24.5) uses it to refuse a risk acceptance or an iteration reset a run made for itself.
DEFAULT_AUTOMATION_IDENTITY = [
    "github-actions[bot]",
    "41898282+github-actions[bot]@users.noreply.github.com",
]
# Any GitHub App writes as "<app>[bot]@users.noreply.github.com", so the suffix is automation
# whatever the project listed.
BOT_EMAIL_SUFFIX = "[bot]@users.noreply.github.com"


def automation_identity(config: dict[str, Any]) -> list[str]:
    """``sdlc.yaml: automation_identity`` when the owner set one, else the default list."""
    listed = config.get("automation_identity")
    if isinstance(listed, list):
        names = [str(i).strip() for i in listed if str(i).strip()]
        if names:
            return names
    return list(DEFAULT_AUTOMATION_IDENTITY)


def is_automation(author_name: str, author_email: str, identities: list[str]) -> bool:
    """True when a commit's author is the framework's own automation identity, never the
    owner: a run cannot approve itself (decision 11)."""
    who = {(author_name or "").strip().lower(), (author_email or "").strip().lower()}
    who.discard("")
    if any(i.strip().lower() in who for i in identities):
        return True
    return (author_email or "").strip().lower().endswith(BOT_EMAIL_SUFFIX)


TEXT_SUFFIXES = {
    ".py", ".js", ".ts", ".tsx", ".jsx", ".mjs", ".cjs", ".json", ".yaml", ".yml", ".toml",
    ".md", ".txt", ".html", ".css", ".scss", ".vue", ".svelte", ".sql", ".sh", ".ps1", ".cfg",
    ".ini", ".env", ".xml", ".java", ".kt", ".go", ".rs", ".rb", ".php", ".cs", ".c", ".h",
    ".cpp", ".hpp", ".swift", ".tf", ".graphql", ".proto",
}  # fmt: skip


@dataclass
class Change:
    root: Path
    config: dict[str, Any]
    files: list[str] = field(default_factory=list)
    added: dict[str, list[tuple[int, str]]] = field(default_factory=dict)  # path -> (line, text)
    note: str = ""


def _git(root: Path, *args: str) -> str:
    try:
        proc = subprocess.run(
            ["git", *args],
            cwd=str(root),
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=60,
        )
    except (OSError, subprocess.TimeoutExpired):
        return ""
    return proc.stdout if proc.returncode == 0 else ""


def added_lines(root: Path, ref: str | None, files: list[str]) -> dict[str, list[tuple[int, str]]]:
    """Added lines per file from ``git diff <ref>`` (working tree vs merge base), plus every
    line of untracked files."""
    out: dict[str, list[tuple[int, str]]] = {}
    text = _git(root, "diff", "--no-color", "-U0", ref or "HEAD", "--")
    current, line_no = None, 0
    for line in text.splitlines():
        if line.startswith("+++ "):
            current = line[4:].strip()
            current = current[2:] if current.startswith("b/") else None
        elif line.startswith("@@"):
            m = re.search(r"\+(\d+)", line)
            line_no = int(m.group(1)) if m else 0
        elif current and line.startswith("+") and not line.startswith("+++"):
            out.setdefault(current, []).append((line_no, line[1:]))
            line_no += 1
        elif current and not line.startswith("-"):
            line_no += 1
    tracked = set(_git(root, "ls-files", "-z").split("\0"))
    for rel in files:
        if rel in tracked or rel in out:
            continue
        path = root / rel
        if path.is_file() and path.suffix.lower() in TEXT_SUFFIXES:
            try:
                lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
            except OSError:
                continue
            out[rel] = list(enumerate(lines, 1))
    return out


def load_change(root: Path, base: str | None = None) -> Change:
    root = Path(root).resolve()
    try:
        config = load_sdlc_config(str(root))
    except ConfigError as exc:
        config = {"_error": str(exc)}
    try:
        d = diffmod.collect(root, base)
    except diffmod.GitUnavailable as exc:
        return Change(root, config, note=f"no git diff available: {exc}")
    return Change(root, config, d.files, added_lines(root, d.merge_base, d.files), d.note)


def is_text(rel: str) -> bool:
    return Path(rel).suffix.lower() in TEXT_SUFFIXES


def base_parser(description: str) -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=description)
    p.add_argument("--root", default=".")
    p.add_argument("--base", default=None, help="base ref for the diff (default: origin HEAD)")
    return p


def report(title: str, findings: list[str], notes: list[str] | None = None) -> int:
    """Print the p.22-style output block and return the exit code (1 = something to look at)."""
    print(f"## {title}")
    if findings:
        for f in findings:
            print(f"- {f}")
    else:
        print("- nothing found")
    for n in notes or []:
        print(f"- note: {n}")
    return 1 if findings else 0
