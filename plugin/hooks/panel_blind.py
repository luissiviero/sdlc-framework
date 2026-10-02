"""PreToolUse hook on Read, Grep, Bash, PowerShell, Write, Edit and MultiEdit: the review
panel's two verdicts stay blind to each other, and the advocate's model is recorded
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
  another folder, or one limited to code (``type: py``, ``glob: "*.py"``), passes;
- a ``Bash`` or ``PowerShell`` command that names that verdict's file or the panel folder
  (``cat …/b-1-reviewer.md``, ``cat evidence/panel/*``) is denied.

When the devil's advocate writes its verdict (a Write, Edit or MultiEdit of
``<phase>-<n>-advocate.md``), the hook writes ``<phase>-<n>-advocate.model.json`` beside it:
the writer's ``agent_type`` and the models of its replies, read from its own transcript
(``subagent_transcript``). ``panel/cli.py record`` and the gate's ``panel`` check require it
to name the advocate and ``sdlc.yaml: panel_advocate_model``, so the model is proved per
advocate call, in CI and in a run made by hand. Only the hook writes that file: a Write or
Edit of any ``*.model.json`` in the panel folder is denied. When the transcript cannot be
found or names no model, the record says why and ``record`` refuses the item, which then
parks for the owner rather than passing unproved.

The rule is symmetric (the advocate's verdict is equally hidden from a reviewer that runs
second) and needs no knowledge of which agent calls: in the window only the member still to
write, or the session that starts it, acts. Once both files exist the conciliator reads
them freely. ``Glob`` is not hooked: it lists names, never contents.

What stays open: a shell command that reads a verdict without naming it or the panel
folder (``grep -r half-up .``): a command's text does not say which files it will read. The
advocate has no Bash at all; the main session has no reason to search the project in the
middle of a panel. A shell command could also write a ``.model.json`` file; the threat here
is a run drifting, not one forging its own evidence.

Speed: the hook fires on every call of those tools, so it decides from the payload (and,
for a Grep or a shell command that mentions the panel, a scan of
``changes/*/evidence/panel/``) with the standard library first, and loads the shared hook
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
SHELL_TOOLS = ("Bash", "PowerShell")
WRITE_TOOLS = ("Write", "Edit", "MultiEdit")
HOOKED_TOOLS = ("Read", "Grep", *SHELL_TOOLS, *WRITE_TOOLS)
ADVOCATE_FILE_RE = re.compile(
    r"(?:^|/)changes/[^/]+/evidence/panel/([a-z])-(\d+)-advocate\.md$", re.IGNORECASE
)
MODEL_RECORD_RE = re.compile(r"(?:^|/)evidence/panel/[^/]*\.model\.json$", re.IGNORECASE)
MODEL_RECORD = "{phase}-{n}-advocate.model.json"
# a shell command that names a verdict or the panel folder: the cheap first look
SHELL_HINT_RE = re.compile(r"panel|-reviewer\.md|-advocate\.md", re.IGNORECASE)
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
    "reads both once both exist. Judge the item from the change's files and your own sources. "
    "If you wrote this file yourself, it is saved: there is no need to read it back."
)
GREP_REASON = (
    "Review panel blindness (decision 21): this search would read {rel}, the {member}'s "
    "verdict on item {n} of phase ({phase}), which the {other} must not see before writing "
    "its own. Search a folder that does not contain {panel_dir}/ (for example src/ or "
    'plugin/), or limit the search to code with a type (type: py) or a glob (glob: "*.py").'
)
SHELL_REASON = (
    "Review panel blindness (decision 21): this command names {what}, and {rel} is the "
    "{member}'s verdict on item {n} of phase ({phase}), which the {other} must not see "
    "before writing its own. Run it once both verdicts exist, or without the panel folder."
)
RECORD_REASON = (
    "{rel} records which model wrote the devil's advocate's verdict; only the panel_blind "
    "hook writes it, when the advocate writes its own file (0.2.30)."
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
    if tool in WRITE_TOOLS:
        return any(
            ADVOCATE_FILE_RE.search(_slash(p)) or MODEL_RECORD_RE.search(_slash(p))
            for p in write_targets(tool_input)
        )
    if tool in SHELL_TOOLS and not SHELL_HINT_RE.search(str(tool_input.get("command") or "")):
        return False
    return bool(one_sided(project_root(payload, env)))


def write_targets(tool_input: dict) -> list[str]:
    paths = [str(tool_input.get("file_path") or "")]
    for edit in tool_input.get("edits") or []:
        if isinstance(edit, dict) and edit.get("file_path"):
            paths.append(str(edit["file_path"]))
    return [p for p in dict.fromkeys(paths) if p]


# --- which model wrote the advocate's verdict (0.2.30) ------------------------------------------
def subagent_transcript(payload: dict) -> Path | None:
    """The calling sub-agent's own transcript. Claude Code keeps it beside the session's,
    ``<session>/subagents/agent-<agent_id>.jsonl`` next to ``<session>.jsonl`` (observed on
    Claude Code 2.1.287, NOTES section 25; not documented), and the hook input carries
    ``agent_id`` and ``transcript_path`` (documented). Either path may be the one given."""
    agent_id = str(payload.get("agent_id") or "").strip()
    transcript = str(payload.get("transcript_path") or "").strip()
    if not agent_id or not transcript:
        return None
    given = Path(transcript)
    name = f"agent-{agent_id}.jsonl"
    candidates = [given] if given.name == name else []
    candidates.append(given.with_suffix("") / "subagents" / name)
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    try:
        return next(iter(given.parent.glob(f"**/{name}")), None)
    except OSError:
        return None


def transcript_models(path: Path) -> list[str]:
    """The models of the assistant replies in a transcript (``message.model`` per line)."""
    models: set[str] = set()
    try:
        with path.open(encoding="utf-8") as fh:
            for line in fh:
                try:
                    entry = json.loads(line)
                except ValueError:
                    continue
                message = entry.get("message") if isinstance(entry, dict) else None
                if entry.get("type") == "assistant" and isinstance(message, dict):
                    model = message.get("model")
                    if isinstance(model, str) and model.strip():
                        models.add(model.strip())
    except OSError:
        return []
    return sorted(models)


def record_advocate_model(payload: dict, verdict_path: str, phase: str, n: str) -> Path:
    """Write ``<phase>-<n>-advocate.model.json`` beside the advocate's verdict: who wrote it
    (``agent_type``) and on which model, read from the writer's own transcript. ``record``
    and the gate's ``panel`` check require it; ``reason`` says why ``models`` is empty."""
    from datetime import datetime, timezone  # noqa: PLC0415

    transcript = subagent_transcript(payload)
    models = transcript_models(transcript) if transcript else []
    if not payload.get("agent_id"):
        reason = "written by the main session, not by a sub-agent"
    elif transcript is None:
        reason = "the sub-agent's transcript was not found"
    elif not models:
        reason = "the sub-agent's transcript names no model"
    else:
        reason = None
    record = {
        "schema_version": 1,
        "phase": phase,
        "n": int(n),
        "member": "advocate",
        "agent_type": payload.get("agent_type"),
        "agent_id": payload.get("agent_id"),
        "models": models,
        "transcript": str(transcript) if transcript else None,
        "reason": reason,
        "at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }
    path = Path(verdict_path).with_name(MODEL_RECORD.format(phase=phase, n=n))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n"
    )
    return path


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
    if tool in WRITE_TOOLS:
        for path in write_targets(tool_input):
            slashed = _slash(common.fs_path(path))
            if MODEL_RECORD_RE.search(slashed):
                rel = common.rel_to(root, common.norm(path)) or path
                return common.Decision.deny(RECORD_REASON.format(rel=rel))
        for path in write_targets(tool_input):
            m = ADVOCATE_FILE_RE.search(_slash(common.fs_path(path)))
            if not m:
                continue
            try:
                record_advocate_model(payload, common.fs_path(path), m.group(1).lower(), m.group(2))
            except (OSError, ValueError):
                # never refuse the verdict itself: with no record, `record` refuses the item
                # and it parks for the owner
                pass
        return common.Decision.allow()
    if tool in SHELL_TOOLS:
        command = _slash(str(tool_input.get("command") or "")).lower()
        for file, phase, n, member, _counterpart in one_sided(root):
            rel = common.rel_to(root, common.norm(str(file))) or str(file)
            if file.name.lower() in command:
                what = file.name
            elif "evidence/panel" in command:
                what = "the panel folder (evidence/panel)"
            else:
                continue
            return common.Decision.deny(
                SHELL_REASON.format(
                    what=what, rel=rel, member=member, n=n, phase=phase, other=OTHER[member]
                )
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
