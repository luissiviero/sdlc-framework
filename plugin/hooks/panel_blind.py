"""PreToolUse hook on Read and Grep: the review panel's two verdicts stay blind to each other
(decision 21; 0.2.30).

The panel is "two blind verdicts and a conciliator" (``plugin/panel/briefs/advocate.md``):
the reviewer writes ``evidence/panel/<phase>-<n>-reviewer.md``, then the devil's advocate,
which must not see it, writes ``<phase>-<n>-advocate.md``, then the conciliator reads both.
Until 0.2.30 the advocate's blindness was a sentence in its brief. This hook makes it hold
while it matters: while an item has one blind verdict and not the other (the *window*),

- a ``Read`` of that verdict is denied, whoever asks — the main session included, so the
  verdict cannot be passed on inside the advocate's prompt;
- a ``Grep`` that would search that verdict is denied: its ``path`` is the file, or a folder
  that holds it, and neither its ``type`` nor its ``glob`` rules the file out. A Grep over
  another folder, or one limited to code (``type: py``, ``glob: "*.py"``), passes.

The rule is symmetric (the advocate's verdict is equally hidden from a reviewer that runs
second) and needs no knowledge of which agent calls: in the window only the member still to
write, or the session that starts it, acts. Once both files exist the conciliator reads
them freely. ``Glob`` is not hooked: it lists names, never contents.

What stays open: a Bash command (``cat``) by a member that has Bash (the reviewer and the
conciliator are general-purpose sub-agents; the advocate, ``sdlc:adversarial-reviewer``, has
no Bash). The record (``panel/cli.py record``) and the gate's ``panel`` check still require
both verdicts; this hook only keeps them apart while they are written.

Speed: the hook fires on every Read and Grep, so it decides from the payload and a scan of
``changes/*/evidence/panel/`` with the standard library first, and loads the shared hook
plumbing only when a panel verdict is involved. It logs its blocks only (an allow line per
Read would bury the log).

Usage in hooks.json (exec form): python panel_blind.py
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

PANEL_FILE_RE = re.compile(
    r"(?:^|/)changes/[^/]+/evidence/panel/([a-z])-(\d+)-(reviewer|advocate)\.md$", re.IGNORECASE
)
OTHER = {"reviewer": "advocate", "advocate": "reviewer"}
HOOKED_TOOLS = ("Read", "Grep")
# ripgrep file types whose globs never include a Markdown file: a Grep limited to one of
# them cannot read a verdict. Any other type (markdown, txt, an unknown name) is treated as
# possibly matching, the safe direction.
CODE_TYPES = frozenset(
    "c cpp cs css go h html java js json jsx kotlin kt php py python rb ruby rust sh sql "
    "swift toml ts tsx typescript yaml yml".split()
)

READ_REASON = (
    "Review panel blindness (decision 21): {rel} is the {member}'s verdict on item {n} of "
    "phase ({phase}), and the {other} has not written its own yet "
    "({other_rel} is missing). The two verdicts are blind to each other; the conciliator "
    "reads both once both exist. Judge the item from the change's files and your own sources."
)
GREP_REASON = (
    "Review panel blindness (decision 21): this search would read {rel}, the {member}'s "
    "verdict on item {n} of phase ({phase}), which the {other} must not see before writing "
    "its own. Search a folder that does not contain {panel_dir}/ (for example src/ or "
    'plugin/), or limit the search to code with a type (type: py) or a glob (glob: "*.py").'
)


def _slash(path: str) -> str:
    return str(path).replace("\\", "/")


def project_root(payload: dict, env: dict[str, str] | None = None) -> str:
    env = os.environ if env is None else env
    if env.get("CLAUDE_PROJECT_DIR"):
        return env["CLAUDE_PROJECT_DIR"]
    cwd = str(payload.get("cwd") or os.getcwd())
    p = Path(cwd)
    for candidate in (p, *p.parents):
        if (candidate / "sdlc.yaml").is_file() or (candidate / ".git").exists():
            return str(candidate)
    return cwd


def one_sided(root: str) -> list[tuple[Path, str, str, str, Path]]:
    """Every blind verdict whose counterpart is missing:
    ``(file, phase, n, member, counterpart)``. Standard library only (the fast path)."""
    found = []
    changes = Path(root) / "changes"
    try:
        change_dirs = [d for d in changes.iterdir() if d.is_dir()]
    except OSError:
        return []
    for change in change_dirs:
        panel = change / "evidence" / "panel"
        try:
            names = os.listdir(panel)
        except OSError:
            continue
        present = set(names)
        for name in names:
            m = re.fullmatch(r"([a-z])-(\d+)-(reviewer|advocate)\.md", name, re.IGNORECASE)
            if not m:
                continue
            phase, n, member = m.group(1).lower(), m.group(2), m.group(3).lower()
            counterpart = f"{phase}-{n}-{OTHER[member]}.md"
            if counterpart not in present:
                found.append((panel / name, phase, n, member, panel / counterpart))
    return found


def may_concern_panel(payload: dict, env: dict[str, str] | None = None) -> bool:
    """The fast path: False when the call cannot touch a blind verdict in its window."""
    tool = payload.get("tool_name")
    if tool not in HOOKED_TOOLS:
        return False
    tool_input = payload.get("tool_input") or {}
    if tool == "Read":
        path = str(tool_input.get("file_path") or "")
        # a symlink with an innocent name is judged by the file it points to
        return any(PANEL_FILE_RE.search(_slash(p)) for p in (path, os.path.realpath(path)))
    return bool(one_sided(project_root(payload, env)))


def _grep_reads(tool_input: dict, search_root: str, target: str, common) -> bool:
    """Would this Grep read ``target``? True unless its path, type or glob rules it out."""
    rel = common.rel_to(search_root, target)
    if rel is None:
        return False  # the file is outside the folder searched
    if rel == "":
        return True  # the file itself is the path: filters do not apply to it
    kind = str(tool_input.get("type") or "").strip().lower()
    if kind and kind in CODE_TYPES:
        return False
    glob = str(tool_input.get("glob") or "").strip()
    if glob and "{" not in glob and not glob.startswith("!"):
        return common.matches(glob, rel)
    return True


def decide(payload: dict, argv: list[str], env: dict[str, str] | None = None):
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import _common as common  # noqa: PLC0415

    if not may_concern_panel(payload, env):
        return common.Decision.allow()
    tool = payload.get("tool_name")
    tool_input = payload.get("tool_input") or {}
    root = common.fs_path(project_root(payload, env))
    if tool == "Read":
        path = str(tool_input.get("file_path") or "")
        # the path as given and the file it resolves to (a symlink), case kept so the
        # counterpart is looked up beside the real file on a case-sensitive file system
        for candidate in dict.fromkeys(
            (common.fs_path(path), common.fs_path(os.path.realpath(path)))
        ):
            m = PANEL_FILE_RE.search(candidate)
            if not m:
                continue
            phase, n, member = m.group(1).lower(), m.group(2), m.group(3).lower()
            counterpart = Path(candidate).with_name(f"{phase}-{n}-{OTHER[member]}.md")
            if counterpart.is_file():
                continue
            rel = common.rel_to(root, candidate) or candidate
            other_rel = common.rel_to(root, common.norm(str(counterpart))) or str(counterpart)
            return common.Decision.deny(
                READ_REASON.format(
                    rel=rel,
                    member=member,
                    n=n,
                    phase=phase,
                    other=OTHER[member],
                    other_rel=other_rel,
                )  # fmt: skip
            )
        return common.Decision.allow()
    cwd = str(payload.get("cwd") or root)
    raw_path = str(tool_input.get("path") or "").strip()
    search_root = raw_path if raw_path else cwd
    if not os.path.isabs(search_root):
        search_root = os.path.join(cwd, search_root)
    search_root = common.fs_path(search_root)
    for file, phase, n, member, _counterpart in one_sided(root):
        if _grep_reads(tool_input, search_root, common.fs_path(file), common):
            rel = common.rel_to(root, common.norm(str(file))) or str(file)
            return common.Decision.deny(
                GREP_REASON.format(
                    rel=rel,
                    member=member,
                    n=n,
                    phase=phase,
                    other=OTHER[member],
                    panel_dir=rel.rsplit("/", 1)[0],
                )  # fmt: skip
            )
    return common.Decision.allow()


def main() -> int:
    raw = getattr(sys.stdin, "buffer", sys.stdin).read()
    try:
        text = raw.decode("utf-8") if isinstance(raw, bytes) else raw
        payload = json.loads(text)
    except ValueError:
        payload = None
    try:
        irrelevant = isinstance(payload, dict) and not may_concern_panel(payload)
    except Exception:  # noqa: BLE001 - an odd payload takes the full path, which fails closed
        irrelevant = False
    if irrelevant:
        return 0  # not a panel verdict, or no verdict in its window: nothing to say
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import io  # noqa: PLC0415

    import _common as common  # noqa: PLC0415

    sys.stdin = io.TextIOWrapper(io.BytesIO(raw if isinstance(raw, bytes) else raw.encode()))
    return common.run_hook(_decide_and_log, "PreToolUse", sys.argv[1:], log=False)


def _decide_and_log(payload: dict, argv: list[str]):
    decision = decide(payload, argv)
    if decision.block:
        import _common as common  # noqa: PLC0415

        common.log_decision("panel_blind", "block", decision.reason, payload)
    return decision


if __name__ == "__main__":
    sys.exit(main())
