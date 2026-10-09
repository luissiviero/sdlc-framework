"""PreToolUse hook: deny a Bash or PowerShell command whose text would write to a protected
path (build guide step 15; the review's `plugin/hooks/hooks.json:32` authz finding, change
0002). `protected_paths.py` and `test_file_lock.py` police `Edit`/`Write`/`MultiEdit`/
`NotebookEdit` only; neither ever looks at what file a shell command would *write*, so an
unattended run could reach the same guardrail file through a one-line interpreter script or a
shell redirection and the two path-based gates would never see it.

This hook reuses both existing hooks' matching primitives (`protected_paths.protected_patterns`
/ `_check_one`, `test_file_lock.locked_change_id` / `is_locked` / `test_path_patterns`) rather
than adding a Bash branch to either: their own wiring tests each assert exactly one `hooks.json`
matcher entry per hook (spec.md Requirements, third bullet).

`shell_write_targets(command)` is its own tokenizer (not a reuse of
`production_gate.command_parts`/`chain_parts`: that parser lower-cases text, splits inside
quotes and loses a redirection target behind its option-stripping suffix check, all wrong for a
parser that must extract path arguments with quotes and case preserved). It tokenises with
shlex-style quoting (a `>` inside a quote is text, not an operator, because the character loop
only recognises an operator when it is not inside a quote), skips heredoc bodies verbatim,
splits a command chain on `;`, `&&`, `||`, `|` and newline only where each sits outside a quote,
and keeps case throughout. A leading wrapper word (`sudo`, `nohup`, `time`, `env`) is skipped
before matching a write idiom; `bash -c '...'`, `sh -c '...'`, `cmd /c '...'` and
`pwsh -Command '...'` are read by recursing into the quoted inner string with the same
tokeniser.

A resolved write-target candidate is checked against `protected_paths.protected_patterns`/
`_check_one` first, then — only when the branch's change is a fix-type change whose tests are
locked — against `test_file_lock.test_path_patterns`. A relative candidate is resolved against
`payload["cwd"]`, following a literal `cd`/`pushd`/`Set-Location`/`git -C` earlier in the same
chain; a non-literal candidate (a `$VAR`, `$(...)`, a backtick, `~`, or a glob) or a `cd` to a
non-literal directory *with a write idiom after it* fails closed — denied, with a reason that
asks for the literal path. A `cd` to a non-literal directory with no write idiom after it is
allowed: the hook judges write targets, not directories.

What it closes, and what it cannot — see spec.md Design: it closes a command whose text names
the target literally beside a write idiom (every redirection form, `tee`, the in-place editors,
`cp`/`mv`/`rsync`/`install`/`ln`'s destination, `dd of=`, the git verbs that take a path,
`rm`/`truncate`/`touch`, and the python/node/PowerShell interpreter literals). It cannot close a
script written to an unprotected path and run separately, an `npm` lifecycle script, a git verb
that rewrites tracked files without a pathspec, or a path built from a variable or a heredoc
body — the sandbox's `filesystem.denyWrite` (CI) and the gate's diff-based `check_guardrails`/
`check_test_lock` are the other two layers for those.

Usage in hooks.json (exec form): python shell_guard.py --plugin-root <path>
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import protected_paths  # noqa: E402
import test_file_lock  # noqa: E402
from _common import (  # noqa: E402
    Decision,
    load_sdlc_config,
    log_decision,
    project_dir,
    run_hook,
)

TOOLS = ("Bash", "PowerShell")
HOOK = "shell_guard"

REASON_NONLITERAL = (
    "Shell guard: the write target `{target}` is not a literal path (a variable, command "
    "substitution, backtick, `~` or a glob); write the literal path so the guard can check it."
)

# --- tokenising ------------------------------------------------------------------------------
_HEREDOC_RE = re.compile(r"<<-?\s*(['\"]?)([A-Za-z_][A-Za-z0-9_]*)\1")
_REDIR_RE = re.compile(r"^\d*(>>|>\||&>>|&>|<>|>)$")
_FD_TARGET_RE = re.compile(r"^&?\d+$")
_FLAG_RE = re.compile(r"^-")
_NONLITERAL_RE = re.compile(r"[$`~*?\[]")

_WRAPPERS = {"sudo", "nohup", "time", "env"}
_INNER_SHELL_PAIRS = {("bash", "-c"), ("sh", "-c"), ("cmd", "/c"), ("pwsh", "-command")}
_CD_WORDS = {"cd", "pushd", "set-location"}


def _strip_heredocs(command: str) -> str:
    """Heredoc bodies (``<<WORD`` ... the terminator line) removed verbatim, so their text is
    never tokenised as a command (a blockquote mentioning a guardrail path is not a write)."""
    lines = command.split("\n")
    out: list[str] = []
    i = 0
    while i < len(lines):
        out.append(lines[i])
        m = _HEREDOC_RE.search(lines[i])
        i += 1
        if m:
            terminator = m.group(2)
            while i < len(lines) and lines[i].strip() != terminator:
                i += 1
            i += 1  # the terminator line itself
    return "\n".join(out)


def _chain_parts_tokenized(command: str) -> list[tuple[list[str], str]]:
    """Chain parts (split on ``;``, ``&&``, ``||``, ``|`` and newline, outside quotes), each a
    ``(words, raw_text)`` pair: ``words`` is a list of tokens — a quoted word with quotes
    stripped and case kept, or a redirection operator token (``>``, ``>>``, ``>|``, ``&>``,
    ``&>>``, ``<>``, ``<``, ``<<``, a digit-prefixed redirection) recognised only when it
    appears outside a quote, so a quoted ``>`` is just text — and ``raw_text`` is the part's
    original, unstripped text (the interpreter-literal scan needs the real quote characters,
    which a dequoted token has already lost)."""
    command = _strip_heredocs(command)
    parts: list[tuple[list[str], str]] = []
    words: list[str] = []
    cur: list[str] = []
    in_single = in_double = False
    i = 0
    n = len(command)
    part_start = 0

    def flush_word() -> None:
        if cur:
            words.append("".join(cur))
            cur.clear()

    def flush_part(end: int) -> None:
        nonlocal part_start
        flush_word()
        raw = command[part_start:end].strip()
        if words:
            parts.append((list(words), raw))
        words.clear()

    while i < n:
        ch = command[i]
        if in_single:
            if ch == "'":
                in_single = False
            else:
                cur.append(ch)
            i += 1
            continue
        if in_double:
            if ch == '"':
                in_double = False
            elif ch == "\\" and i + 1 < n and command[i + 1] in '"\\$`':
                cur.append(command[i + 1])
                i += 2
                continue
            else:
                cur.append(ch)
            i += 1
            continue
        if ch == "'":
            in_single = True
            i += 1
            continue
        if ch == '"':
            in_double = True
            i += 1
            continue
        if ch == "\\" and i + 1 < n and command[i + 1] != "\n":
            cur.append(command[i + 1])
            i += 2
            continue
        if ch in ";\n":
            flush_part(i)
            i += 1
            part_start = i
            continue
        if command[i : i + 2] == "&&" or command[i : i + 2] == "||":
            flush_part(i)
            i += 2
            part_start = i
            continue
        if ch == "|":
            flush_part(i)
            i += 1
            part_start = i
            continue
        if ch.isspace():
            flush_word()
            i += 1
            continue
        if ch == "&" and i + 1 < n and command[i + 1] == ">":
            op = "&>"
            j = i + 2
            if j < n and command[j] == ">":
                op = "&>>"
                j += 1
            flush_word()
            words.append(op)
            i = j
            continue
        if ch in "<>":
            op = ch
            j = i + 1
            if ch == ">":
                if j < n and command[j] == ">":
                    op = ">>"
                    j += 1
                elif j < n and command[j] == "|":
                    op = ">|"
                    j += 1
            elif ch == "<":
                if j < n and command[j] == "<":
                    op = "<<"
                    j += 1
                    if j < n and command[j] == "-":
                        op = "<<-"
                        j += 1
                elif j < n and command[j] == ">":
                    op = "<>"
                    j += 1
            fd = ""
            if cur and all(d.isdigit() for d in cur):
                fd = "".join(cur)
                cur.clear()
            flush_word()
            words.append(fd + op)
            i = j
            continue
        cur.append(ch)
        i += 1
    flush_part(n)
    return parts


def _strip_wrappers(words: list[str]) -> list[str]:
    out = list(words)
    while out and out[0].lower() in _WRAPPERS:
        out = out[1:]
    return out


def _inner_shell_command(words: list[str]) -> str | None:
    if len(words) >= 3 and (words[0].lower(), words[1].lower()) in _INNER_SHELL_PAIRS:
        return words[2]
    return None


def _git_dash_c(words: list[str]) -> tuple[str, list[str]] | None:
    if len(words) >= 3 and words[0] == "git" and words[1] == "-C":
        return words[2], ["git", *words[3:]]
    return None


def _dir_change_target(words: list[str]) -> str | None:
    if len(words) >= 2 and words[0].lower() in _CD_WORDS:
        return words[1]
    return None


def _is_literal(token: str) -> bool:
    return not _NONLITERAL_RE.search(token)


def _nonflag(words: list[str]) -> list[str]:
    return [w for w in words if not _FLAG_RE.match(w)]


# --- interpreter literals (python/node/PowerShell calls inline in the command text) ----------
_PY_OPEN_RE = re.compile(r"\bopen\(\s*['\"]([^'\"]+)['\"](?:\s*,\s*['\"]([^'\"]*)['\"])?")
_PY_PATH_RE = re.compile(
    r"\bPath\(\s*['\"]([^'\"]+)['\"]\s*\)\.(?:write_text|write_bytes|unlink|rename|replace|touch)\b"
)
_PY_OS_RE = re.compile(r"\bos\.(?:remove|unlink|rename|replace)\(\s*['\"]([^'\"]+)['\"]")
_PY_SHUTIL_RE = re.compile(r"\bshutil\.(?:copy2?|copyfile|move|rmtree)\(\s*['\"]([^'\"]+)['\"]")
_NODE_FS_RE = re.compile(
    r"\b(?:fs\.(?:promises\.)?|require\(['\"]fs['\"]\)\.)?"
    r"(?:writeFileSync|writeFile|appendFileSync|appendFile|rmSync|rm|unlinkSync|unlink|"
    r"renameSync|rename|copyFileSync|copyFile|cpSync|createWriteStream|truncateSync|truncate)"
    r"\(\s*['\"]([^'\"]+)['\"]"
)
_PS_STATIC_RE = re.compile(
    r"\[IO\.File\]::(?:WriteAllText|WriteAllBytes|AppendAllText|Delete|Copy|Move)"
    r"\(\s*['\"]([^'\"]+)['\"]"
)
_WRITE_MODE_RE = re.compile(r"[wax+]")


def _interpreter_targets(text: str) -> list[str]:
    out: list[str] = []
    for m in _PY_OPEN_RE.finditer(text):
        mode = m.group(2)
        if mode is not None and _WRITE_MODE_RE.search(mode):
            out.append(m.group(1))
    for pattern in (_PY_PATH_RE, _PY_OS_RE, _PY_SHUTIL_RE, _NODE_FS_RE, _PS_STATIC_RE):
        out.extend(m.group(1) for m in pattern.finditer(text))
    return out


# --- PowerShell cmdlets and their aliases -----------------------------------------------------
_PS_CMDLETS = {
    "set-content",
    "add-content",
    "out-file",
    "new-item",
    "copy-item",
    "move-item",
    "rename-item",
    "remove-item",
    "clear-content",
    "tee-object",
}
_PS_ALIASES = {"sc", "ac", "ni", "cpi", "mi", "rni", "ri", "del", "erase", "rm"}
_PS_PATH_FLAGS = {"-path", "-literalpath", "-filepath", "-destination"}
# Copy-Item/Move-Item take (source, destination) positionally; both are candidates (Move-Item
# also deletes its source). Every other cmdlet here takes the write target as its first
# positional argument.
_PS_BOTH_ARGS = {"copy-item", "cpi", "move-item", "mi"}


def _powershell_targets(words: list[str]) -> list[str]:
    if not words or words[0].lower() not in (_PS_CMDLETS | _PS_ALIASES):
        return []
    rest = words[1:]
    targets: list[str] = []
    found_flag = False
    i = 0
    while i < len(rest):
        if rest[i].lower() in _PS_PATH_FLAGS and i + 1 < len(rest):
            targets.append(rest[i + 1])
            found_flag = True
            i += 2
            continue
        i += 1
    if not found_flag:
        nonflag = _nonflag(rest)
        if words[0].lower() in _PS_BOTH_ARGS:
            targets.extend(nonflag)
        elif nonflag:
            targets.append(nonflag[0])
    return targets


# --- the write-idiom list (spec.md Design) -----------------------------------------------------
def _part_targets(words: list[str], raw: str = "") -> list[str]:
    """Every write-target candidate one chain part names, unresolved against any directory.
    ``raw`` is the part's original text, scanned for an interpreter-literal call: a dequoted
    token has already lost the quote characters the pattern needs."""
    if not words:
        return []
    targets: list[str] = []
    headl = words[0].lower()

    for i, w in enumerate(words):
        if _REDIR_RE.match(w) and i + 1 < len(words):
            nxt = words[i + 1]
            if not _FD_TARGET_RE.match(nxt):  # `2>&1`, `>&2`: a duplicated fd, not a file
                targets.append(nxt)

    if headl == "tee":
        targets.extend(_nonflag(words[1:]))
    elif headl in ("cp", "mv", "install", "ln", "rsync"):
        rest = _nonflag(words[1:])
        if rest:
            targets.append(rest[-1])
    elif headl in ("rm", "truncate", "touch"):
        targets.extend(_nonflag(words[1:]))
    elif headl == "sed" and any(w.startswith("-i") for w in words[1:]):
        rest = _nonflag(words[1:])
        if rest:
            targets.append(rest[-1])
    elif headl == "perl" and any(w == "-i" or w.startswith("-i") for w in words[1:]):
        rest = _nonflag(words[1:])
        if rest:
            targets.append(rest[-1])
    elif headl == "dd":
        targets.extend(w[len("of=") :] for w in words[1:] if w.startswith("of="))
    elif headl == "git" and len(words) >= 2:
        sub = words[1].lower()
        if sub == "checkout" and "--" in words:
            targets.extend(words[words.index("--") + 1 :])
        elif sub in ("restore", "rm", "mv", "apply"):
            targets.extend(_nonflag(words[2:]))

    targets.extend(_powershell_targets(words))
    targets.extend(_interpreter_targets(raw))
    return list(dict.fromkeys(targets))


def shell_write_targets(command: str) -> list[str]:
    """Every write-target candidate the command names anywhere in its chain, unresolved
    against any working directory. A thin projection of ``_resolution_walk`` (below), which
    does the identical chain-part dispatch (wrapper-stripping, ``git -C``, inner-shell
    recursion) while also tracking the directory each candidate resolves against; the
    ``cwd`` passed here is never read since only the target itself is kept."""
    out = [target for target, _base, _nonliteral in _resolution_walk(command, "")]
    return list(dict.fromkeys(out))


def _resolve(base: str, raw: str) -> str:
    raw_fs = raw.replace("\\", "/")
    if raw_fs.startswith("/") or (len(raw_fs) >= 2 and raw_fs[1] == ":"):
        return raw
    return str(Path(base) / raw)


def _resolution_walk(command: str, cwd: str):
    """Yields ``(raw_target, base_dir, base_is_nonliteral)`` for every write-target candidate,
    tracking a literal ``cd``/``pushd``/``Set-Location``/``git -C`` earlier in the chain."""
    current = cwd
    nonliteral = False
    for words, raw_text in _chain_parts_tokenized(command):
        plain = _strip_wrappers(words)
        if not plain:
            continue
        dirarg = _dir_change_target(plain)
        if dirarg is not None:
            if _is_literal(dirarg):
                current = _resolve(current, dirarg)
                nonliteral = False
            else:
                nonliteral = True
            continue
        git_c = _git_dash_c(plain)
        if git_c is not None:
            dirarg2, rest = git_c
            if _is_literal(dirarg2):
                current = _resolve(current, dirarg2)
                nonliteral = False
            else:
                nonliteral = True
            for target in _part_targets(rest, raw_text):
                yield target, current, nonliteral
            continue
        inner = _inner_shell_command(plain)
        if inner is not None:
            for target, base, base_nl in _resolution_walk(inner, current):
                yield target, base, base_nl or nonliteral
            continue
        for target in _part_targets(plain, raw_text):
            yield target, current, nonliteral


def _git(root: str, *args: str) -> str:
    try:
        proc = subprocess.run(
            ["git", *args], cwd=root, capture_output=True, text=True, encoding="utf-8", timeout=20
        )
    except (OSError, subprocess.TimeoutExpired):
        return ""
    return proc.stdout if proc.returncode == 0 else ""


def decide(payload: dict, argv: list[str], env: dict[str, str] | None = None, git=_git) -> Decision:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plugin-root", default=None)
    args = parser.parse_args(argv)

    if payload.get("tool_name") not in TOOLS:
        return Decision.allow()
    command = str((payload.get("tool_input") or {}).get("command") or "")
    if not command.strip():
        return Decision.allow()
    root = project_dir(payload, env)
    cwd = str(payload.get("cwd") or root)
    try:
        config = load_sdlc_config(root)
        patterns = protected_paths.protected_patterns(config)
    except protected_paths.ConfigError as exc:
        return Decision.deny(
            f"Shell guard cannot read the project's guardrail config ({exc}); refusing every "
            "shell write until the owner fixes sdlc.yaml."
        )
    plugin_root = protected_paths.real(args.plugin_root) if args.plugin_root else None

    test_patterns: list[str] | None = None
    branch = git(root, "rev-parse", "--abbrev-ref", "HEAD").strip()
    change_id = test_file_lock.locked_change_id(branch) if branch else None
    if change_id is not None:
        try:
            if test_file_lock.is_locked(root, change_id):
                test_patterns = test_file_lock.test_path_patterns(config)
        except test_file_lock.ConfigError as exc:
            return Decision.deny(test_file_lock.FAIL_CLOSED.format(error=exc))

    for raw, base, nonliteral in _resolution_walk(command, cwd):
        if nonliteral or not _is_literal(raw):
            return Decision.deny(REASON_NONLITERAL.format(target=raw))
        resolved = _resolve(base, raw)
        reason = protected_paths._check_one(resolved, root, patterns, plugin_root)
        if reason:
            return Decision.deny(protected_paths.REASON.format(what=reason))
        if test_patterns:
            for candidate in {protected_paths.norm(resolved), protected_paths.real(resolved)}:
                rel = protected_paths.rel_to(root, candidate)
                if rel is not None and any(
                    protected_paths.matches(pattern, rel) for pattern in test_patterns
                ):
                    return Decision.deny(test_file_lock.REASON.format(path=rel))
    return Decision.allow()


def _decide_and_log(payload: dict, argv: list[str]) -> Decision:
    decision = decide(payload, argv)
    if decision.block:
        log_decision(HOOK, "block", decision.reason, payload)
    return decision


if __name__ == "__main__":
    sys.exit(run_hook(_decide_and_log, "PreToolUse", sys.argv[1:], log=False))
