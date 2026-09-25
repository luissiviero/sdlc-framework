"""The brief of the weekly security review (build guide step 38; decision 16; article p.46-48).

The review is the security pass of ``plugin/review/REVIEW_PROMPT.md`` alone, over the whole
tracked tree at one commit instead of a diff: a fresh, read-only context applies the
``security-baseline`` skill and writes one findings file in the review findings shape
(``plugin/review/findings.py``) with three extra keys per finding: ``bounded`` (one file,
one patch), ``class`` (the vulnerability class) and, for a bounded finding, ``patch`` (a
unified diff the build run can apply). ``scan/route.py`` reads that file and files every
Important finding as an incident intent change.

Nothing here runs a model: ``build_prompt`` returns text, ``allowed_tools`` and
``disallowed_tools`` the two tool lists ``scan/cli.py review`` hands the headless run.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

PLUGIN_DIR = Path(__file__).resolve().parent.parent
if str(PLUGIN_DIR) not in sys.path:
    sys.path.insert(0, str(PLUGIN_DIR))

from detect import dismissals  # noqa: E402
from review import findings as findings_mod  # noqa: E402

from gate import artifacts as art  # noqa: E402
from state import conventions as c  # noqa: E402

PROMPT_VERSION = "v1"
SKILL_NAME = "security-baseline"
PLUGIN_SKILL = PLUGIN_DIR / "skills" / SKILL_NAME / "SKILL.md"
PROJECT_SKILL = Path(".claude") / "skills" / SKILL_NAME / "SKILL.md"  # the project override
SKILL_RULES_SECTION = "## Rules"
REVIEW_FILE = "REVIEW.md"
IMPORTANT_SECTION = "## What Important means here"
DEFAULT_MAX_FINDINGS = 3
MAX_NITS = 5
MAX_PATCH_LINES = 60
# The review's tools (decision 16: read-only but for the one findings file it writes). The
# same list as the per-change review pass (``ci/run_phase.py: REVIEW_ALLOWED_TOOLS``); the
# disallowed list also names the editing tools the per-change pass leaves to the CI settings.
ALLOWED_TOOLS = ("Read", "Grep", "Glob", "Bash(git *)", "Write")
DISALLOWED_TOOLS = ("Edit", "MultiEdit", "NotebookEdit", "WebFetch", "WebSearch")
# Out of scope: the framework's own records, the evals and lessons, the pinned framework
# checkout the workflow puts at ./framework, and what the project did not write itself.
EXCLUDED_DIRS = (
    f"{c.CHANGES_DIR}/",
    "evals/",
    "lessons/",
    "framework/",
    ".sdlc/",
    "node_modules/",
    "vendor/",
    "third_party/",
    "dist/",
    "build/",
    ".venv/",
    "venv/",
)
EXCLUDED_GENERATED = (
    "*.min.js",
    "*.map",
    "package-lock.json",
    "yarn.lock",
    "pnpm-lock.yaml",
    "poetry.lock",
    "files whose first lines say they are generated",
)


def allowed_tools() -> str:
    return ",".join(ALLOWED_TOOLS)


def disallowed_tools() -> str:
    return ",".join(DISALLOWED_TOOLS)


def _strip_front_matter(text: str) -> str:
    """The skill body without its ``---`` YAML header (the brief quotes the rules, not the
    trigger description)."""
    lines = text.splitlines()
    if lines and lines[0].strip() == "---":
        for i, line in enumerate(lines[1:], 1):
            if line.strip() == "---":
                return "\n".join(lines[i + 1 :]).strip()
    return text.strip()


def skill_text(root: Path) -> tuple[str, str]:
    """(the security-baseline skill's rules, where they came from): the project override
    under ``.claude/skills/`` when it exists, else the plugin's. Only the ``## Rules``
    section is quoted when the skill has one: its Source notes are for authors, and its
    Check section runs a script this read-only run has no tool for (the deterministic
    scanners run beside it in the same workflow)."""
    override = Path(root) / PROJECT_SKILL
    for path, origin in ((override, PROJECT_SKILL.as_posix()), (PLUGIN_SKILL, "plugin")):
        try:
            body = _strip_front_matter(path.read_text(encoding="utf-8"))
        except OSError:
            continue
        rules = art.split_sections(body).get(SKILL_RULES_SECTION, "").strip()
        return (rules or body), origin
    return "(the security-baseline skill could not be read)", "missing"


def important_meaning(root: Path) -> str | None:
    """REVIEW.md's "What Important means here" section, when the project has one."""
    text = art.read_text(Path(root) / REVIEW_FILE)
    if not text:
        return None
    body = art.split_sections(text).get(IMPORTANT_SECTION, "").strip()
    return body or None


def dismissed_entries(root: Path) -> list[tuple[str, dict[str, Any]]]:
    """The scan dismissals in force, (signature, entry), sorted by signature."""
    record = dismissals.load(dismissals.path_for(Path(root), c.CHANGES_DIR))
    out = []
    for sig, entry in sorted((record.get("entries") or {}).items()):
        if not isinstance(entry, dict) or entry.get("kind") != "scan":
            continue
        if dismissals.lookup(record, sig) is None:
            continue
        out.append((sig, entry))
    return out


def _test_globs(root: Path) -> list[str]:
    return findings_mod.test_path_globs(Path(root))


def _display_path(root: Path, out_path: str | Path) -> str:
    """The findings file as the reviewer should write it: relative to the project root (its
    working directory) when it lies inside it, else absolute; forward slashes either way."""
    path = Path(out_path)
    resolved = path if path.is_absolute() else Path(root) / path
    try:
        return resolved.resolve().relative_to(Path(root).resolve()).as_posix()
    except ValueError:
        return resolved.resolve().as_posix()


def _max_findings(config: dict[str, Any] | None, override: int | None) -> int:
    if isinstance(override, int) and not isinstance(override, bool) and override > 0:
        return override
    maintain = (config or {}).get("maintain") if isinstance(config, dict) else None
    scan = maintain.get("scan") if isinstance(maintain, dict) else None
    value = scan.get("max_findings") if isinstance(scan, dict) else None
    if isinstance(value, int) and not isinstance(value, bool) and value > 0:
        return value
    return DEFAULT_MAX_FINDINGS


def build_prompt(
    root: Path,
    config: dict[str, Any] | None,
    *,
    head: str,
    out_path: str | Path,
    max_findings: int | None = None,
) -> str:
    """The brief of one weekly security review of the project at ``root``, commit ``head``."""
    root = Path(root)
    cap = _max_findings(config, max_findings)
    out = _display_path(root, out_path)
    skill, origin = skill_text(root)
    meaning = important_meaning(root)
    dismissed = dismissed_entries(root)
    tests = ", ".join(f"`{g}`" for g in _test_globs(root))
    excluded = ", ".join(f"`{d}`" for d in EXCLUDED_DIRS)
    generated = ", ".join(EXCLUDED_GENERATED)

    parts: list[str] = []
    parts.append(
        f"# Weekly security review - brief for a fresh context (scan prompt {PROMPT_VERSION})\n"
        "\n"
        'Source: article p.46-48 (recurring security scans: "run the scan on a schedule, '
        "without a human in the invocation path, and send what it finds through the same gates "
        'as any other change"), decision 16, build guide step 38.\n'
        "\n"
        f"You are reviewing the whole project at commit `{head}` (head: `{head}`) for security "
        "vulnerabilities. This is the security pass of the pull-request review alone, over the "
        "codebase rather than a diff. You did not write this code. Report only; fix nothing; "
        "write exactly one file.\n"
    )
    parts.append(
        "## Scope\n"
        f"- The files tracked at `{head}`: list them with `git ls-files`; read them with Read, "
        "Grep and Glob, or `git show`.\n"
        f"- Leave out: {excluded}; the test files ({tests}); vendored and generated files "
        f"({generated}).\n"
        "- Look for the context-dependent vulnerabilities the deterministic scanners in CI "
        "(pip-audit, bandit, npm audit) are not built to find (p.48): authorization decided by "
        "the client, injection through a path the code builds itself, secrets reaching a log, "
        "unsafe deserialization of external data, a missing check on one route of many. A "
        "known-vulnerable dependency version is the scanners' job, not yours.\n"
    )
    parts.append(
        "## Tools\n"
        "Read-only: Read, Grep, Glob and `git` (`git ls-files`, `git log`, `git show`, "
        "`git grep`, `git blame`); never commit, check out, reset or push. One Write, of the "
        "findings file below. No Edit, no web access.\n"
    )
    parts.append(f"## The policy you apply: the security-baseline skill ({origin})\n{skill}\n")
    if meaning:
        parts.append(f"## What Important means here (the project's REVIEW.md)\n{meaning}\n")
    else:
        parts.append(
            "## What Important means here\n"
            "Important = would break behaviour, leak data, or breach a policy. Everything else "
            "is a nit.\n"
        )
    parts.append(
        "## Severity and the cap\n"
        f"- Report at most {cap} Important findings, the highest risk first (exploitable "
        "without authentication before exploitable with it; data exposure before denial of "
        "service). Say in the reply how many more you saw.\n"
        f"- At most {MAX_NITS} nits; a finding you are not sure about is a nit with the doubt "
        "stated, not an Important finding.\n"
        "- Never quote a credential, key or token in the findings file or the reply, even one "
        'you found in the code: describe it in words ("an API key literal in settings.py").\n'
    )
    parts.append(
        "## Bounded or wide\n"
        "- `bounded: true` when one patch in one file fixes the finding completely. Give that "
        f"patch in `patch`: a unified diff against `{head}` (`--- a/<file>`, `+++ b/<file>`, "
        f"`@@` hunks), at most {MAX_PATCH_LINES} lines. The build run applies it after a test "
        "that reproduces the vulnerability; it must not touch a test file.\n"
        "- `bounded: false` when the fix is wider than one patch: the same pattern in several "
        "places, a missing layer (no authorization model, no input schema), or a design "
        "choice. No `patch`; the summary names the class and where it shows.\n"
        "- `class`: the vulnerability class in one or two words, e.g. `injection`, `secrets`, "
        "`authz`, `authn`, `deserialization`, `path-traversal`, `ssrf`, `crypto`, "
        "`pii-in-logs`.\n"
    )
    if dismissed:
        lines = [
            "## Dismissed findings: do not report them again",
            'The owner closed these with a reason (article p.47 step 4: "the same finding '
            'does not return as new on the next run"). A finding with the same file and the '
            "same meaning is dismissed; report it only if the code changed so that it is a "
            "different finding.",
        ]
        for sig, entry in dismissed:
            summary = str(entry.get("summary") or "").strip() or "(no summary recorded)"
            reason = str(entry.get("reason") or "").strip()
            lines.append(f"- dismissed signature `{sig}`: {summary} (reason: {reason})")
        parts.append("\n".join(lines) + "\n")
    else:
        parts.append("## Dismissed findings: do not report them again\nNone are recorded.\n")
    parts.append(
        "## Output - the one file you write\n"
        f"Output file: `{out}` (relative to the project root, your working directory). "
        f"Exactly this shape; `head` is mandatory and must be `{head}`, `pass` is always "
        "`security`:\n"
        "\n"
        "```json\n"
        "{\n"
        '  "schema_version": 1,\n'
        f'  "head": "{head}",\n'
        '  "findings": [\n'
        "    {\n"
        '      "pass": "security",\n'
        '      "severity": "important | nit",\n'
        '      "file": "path/relative/to/root.py",\n'
        '      "line": 42,\n'
        '      "summary": "<one sentence: what is wrong and why it matters>",\n'
        '      "rule": "<the security-baseline rule it violates, e.g. Rule 2 Input>",\n'
        '      "class": "injection",\n'
        '      "bounded": true,\n'
        '      "patch": "--- a/path/relative/to/root.py\\n'
        '+++ b/path/relative/to/root.py\\n@@ ..."\n'
        "    }\n"
        "  ],\n"
        '  "tally": {"important": 0, "nit": 0, "nits_omitted": 0},\n'
        '  "at": "<ISO-8601 UTC>"\n'
        "}\n"
        "```\n"
        "\n"
        "Leave out `signature`: the router computes it. No finding at all is a valid result: "
        "write the file with an empty `findings` list. Then reply with a short markdown "
        "summary: the tally and every Important finding on one line (`file:line - class - "
        "summary`). The router reads the JSON, not your summary; every Important finding "
        "becomes an incident intent the owner triages.\n"
    )
    return "\n".join(parts)
