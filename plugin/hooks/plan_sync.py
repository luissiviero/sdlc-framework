"""PreToolUse hook on ``git commit``: plan.md must change whenever source changes in phase (c)
(build guide step 15 (4) and step 12; article p.16 step 7 'When implementation departs from
the plan, update plan.md in the same commit. Consider using a hook to enforce
synchronization between the two.').

Mechanism (the article suggests the hook but not its mechanism): registered on the Bash and
PowerShell tools with ``"if": "Bash(git *)"`` (a narrower ``Bash(git commit *)`` would skip
``git -C dir commit``). The hook itself finds a ``commit`` subcommand anywhere in the command
text (chains, subshells, env prefixes). It reads the current branch; only ``sdlc/<id>/c``
branches are checked (OPERATING_MODEL section 8: 'In (c) a hook on git commit denies a
commit that changes source without changing plan.md in the same commit'). The files the
commit would contain are the index, plus the working tree when ``-a``/``--all``/``--include``
is given, plus any pathspec named after ``commit``. If any of them is source — not matched by
``changes/**`` or by ``plan_sync.exempt`` in sdlc.yaml — **and not listed under "## Files that
change" of ``changes/<id>-*/plan.md``** (a departure from the plan), then that plan.md must be
among them, or the commit is denied. A commit inside the plan needs nothing: the first gated
build run (2026-09-22) committed exactly the three files the plan listed, one plan step per
commit as /sdlc-build asks, and was parked because no commit carried plan.md.
"""

from __future__ import annotations

import re
import shlex
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import Decision, load_sdlc_config, matches, project_dir, run_hook  # noqa: E402

from gate import artifacts as art  # noqa: E402
from state import conventions as c  # noqa: E402

DEFAULT_EXEMPT = ("changes/**",)
# `git`, optional global options (-C dir, -c k=v, --long[=v]), then the `commit` word.
COMMIT_RE = re.compile(
    r"(?<![\w./-])git(?:\s+(?:-C\s+(?:\"[^\"]*\"|'[^']*'|\S+)|-c\s+\S+|--[\w-]+(?:=\S+)?))*"
    r"\s+commit(?![\w-])"
)
_TAKES_ARG = {
    "-m",
    "--message",
    "-F",
    "--file",
    "--author",
    "--date",
    "-C",
    "-c",
    "--reuse-message",
    "--reedit-message",
    "--fixup",
    "--squash",
    "--trailer",
    "--cleanup",
    "-t",
    "--template",
}


def _git(root: str, *args: str) -> str:
    try:
        proc = subprocess.run(
            ["git", *args], cwd=root, capture_output=True, text=True, encoding="utf-8", timeout=20
        )
    except (OSError, subprocess.TimeoutExpired):
        return ""
    return proc.stdout if proc.returncode == 0 else ""


def _tokens(command: str) -> list[str]:
    try:
        return shlex.split(command, posix=True)
    except ValueError:
        return command.split()


def commit_options(command: str) -> tuple[bool, list[str]]:
    """(includes working tree?, pathspecs) for the first `git ... commit` in the command."""
    tokens = _tokens(command)
    try:
        idx = next(i for i, t in enumerate(tokens) if t == "commit" and "git" in tokens[:i])
    except StopIteration:
        return False, []
    rest = tokens[idx + 1 :]
    all_files, paths, i, after_dashes = False, [], 0, False
    while i < len(rest):
        t = rest[i]
        if t in ("&&", "||", ";", "|"):
            break
        if after_dashes:
            paths.append(t)
        elif t == "--":
            after_dashes = True
        elif t in ("-a", "--all", "-i", "--include"):
            all_files = True
        elif t in _TAKES_ARG:
            i += 1
        elif t.startswith("-") and not t.startswith("--") and len(t) > 2:
            # bundled short options, e.g. -am 'msg', -qa: any 'a'/'i' includes the tree;
            # a trailing m/F/C/c/t consumes the next token
            flags = t[1:]
            if "a" in flags or "i" in flags:
                all_files = True
            if flags[-1] in "mFCct":
                i += 1
        elif t.startswith("-"):
            pass
        else:
            paths.append(t)
        i += 1
    return all_files, paths


def _z(out: str) -> list[str]:
    return [f.replace("\\", "/") for f in out.split("\0") if f]


def files_in_commit(root: str, command: str, git=_git) -> list[str]:
    all_files, paths = commit_options(command)
    files = _z(git(root, "diff", "--cached", "--name-only", "-z", "--diff-filter=ACMRD"))
    if all_files:
        files += _z(git(root, "diff", "--name-only", "-z", "--diff-filter=ACMRD"))
    if paths:
        files += _z(git(root, "diff", "--name-only", "-z", "--diff-filter=ACMRD", "--", *paths))
        files += _z(git(root, "ls-files", "-z", "--others", "--exclude-standard", "--", *paths))
    return sorted(set(files))


def is_planned(changed: str, planned: str) -> bool:
    """``changed`` is covered by one entry of the plan's "## Files that change": the same
    path (case-insensitive), a glob, or a directory entry ending in ``/``."""
    changed = changed.lower().strip("/")
    planned = planned.lower().lstrip("/")
    if planned.endswith("/"):  # a directory entry covers everything under it
        return changed.startswith(planned)
    if changed == planned:
        return True
    return any(ch in planned for ch in "*?[") and matches(planned, changed)


def planned_files(root: str, change_id: str) -> list[str]:
    """The "## Files that change" entries of ``changes/<id>-*/plan.md`` as it is in the
    working tree (a plan.md in the same commit lifts the rule anyway)."""
    for path in sorted(Path(root).glob(f"changes/{change_id}-*/plan.md")):
        try:
            return art.planned_files(path.read_text(encoding="utf-8", errors="replace"))
        except OSError:
            continue
    return []


def check(branch: str, files: list[str], exempt: list[str], planned=()) -> Decision:
    """``planned`` is the plan's file list; without it every source file is a departure."""
    parsed = c.parse_branch(branch)
    if not parsed or parsed[1] != "c":
        return Decision.allow()
    change_id = parsed[0]
    plan_rx = re.compile(rf"^changes/{change_id}-[^/]+/plan\.md$", re.IGNORECASE)
    plan_staged = any(plan_rx.match(f) for f in files)
    source = [f for f in files if not any(matches(p, f) for p in exempt)]
    departures = [f for f in source if not any(is_planned(f, p) for p in planned)]
    if departures and not plan_staged:
        listed = "\n".join(f"  - {f}" for f in departures[:20])
        return Decision.deny(
            "plan.md is out of sync: this commit changes source files the plan does not list "
            f"but not changes/{change_id}-<slug>/plan.md. When implementation departs from "
            "the plan, update plan.md in the same commit (article p.16, step 7). Files in "
            f"the commit that '## Files that change' does not cover:\n{listed}"
        )
    return Decision.allow()


def exempt_patterns(config: dict) -> list[str]:
    cfg = config.get("plan_sync")
    extra = cfg.get("exempt") if isinstance(cfg, dict) else None
    if not isinstance(extra, list):
        extra = []
    return list(DEFAULT_EXEMPT) + [str(p) for p in extra if str(p).strip()]


def decide(payload: dict, argv: list[str], env: dict[str, str] | None = None, git=_git) -> Decision:
    if payload.get("tool_name") not in ("Bash", "PowerShell"):
        return Decision.allow()
    command = str((payload.get("tool_input") or {}).get("command") or "")
    if not COMMIT_RE.search(command):
        return Decision.allow()
    root = project_dir(payload, env)
    branch = git(root, "rev-parse", "--abbrev-ref", "HEAD").strip()
    if not branch:
        return Decision.allow()  # not a git repo: nothing to enforce
    exempt = exempt_patterns(load_sdlc_config(root))
    parsed = c.parse_branch(branch)
    planned = planned_files(root, parsed[0]) if parsed else []
    return check(branch, files_in_commit(root, command, git), exempt, planned)


if __name__ == "__main__":
    sys.exit(run_hook(decide, "PreToolUse", sys.argv[1:]))
