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
only recognises an operator when it is not inside a quote), skips heredoc bodies verbatim (a
quote-aware scan: a `<<WORD` inside a quoted string is not a heredoc, and `<<<` is a here-string,
never a heredoc), strips an unquoted `#` comment, splits a command chain on `;`, `&&`, `||`,
`|`, a lone `&` and newline only where each sits outside a quote, and keeps case throughout. A
leading wrapper word (`sudo`, `nohup`, `time`, `env`), a shell keyword (`then`/`do`/`else`/...)
and a `NAME=value` assignment prefix are all skipped before matching a write idiom; `bash -c
'...'`, `sh -c '...'`, `cmd /c '...'` and `pwsh -Command '...'` are read by recursing into the
quoted inner string with the same tokeniser, a flag between the interpreter and its `-c`/`/c`/
`-Command` token skipped first (`bash --norc -c '...'`, `cmd /d /c '...'`).

A resolved write-target candidate is checked against `protected_paths.protected_patterns`/
`_check_one` first (including an ancestor check: a recursive delete or move of a directory that
contains a protected path, or of the plugin root, is denied even though the directory's own name
never matches a file pattern), then — only when the branch's change is a fix-type change whose
tests are locked — against `test_file_lock.test_path_patterns`. A relative candidate is resolved
against `payload["cwd"]`, following a literal `cd`/`pushd`/`Set-Location`/`git -C` earlier in the
same chain; a non-literal candidate (a `$VAR`, `$(...)`, a backtick, `~`, a glob, a brace
expansion, or a git pathspec-magic prefix) or a `cd` to a non-literal, unresolvable or untracked
directory (`cd -`, a bare `cd`, `popd`, `Pop-Location`) *with a write idiom after it* fails
closed — denied, with a reason that asks for the literal path. A `cd` to such a directory with no
write idiom after it is allowed: the hook judges write targets, not directories.

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
    HOOK_LOG_DEFAULT,
    HOOK_LOG_EVIDENCE,
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
    "substitution, backtick, `~`, a glob, a brace expansion or a git pathspec-magic prefix), or "
    "the working directory it would resolve against is not tracked (`cd -`, a bare `cd`, "
    "`popd`/`Pop-Location`); write the literal path, from a tracked directory, so the guard can "
    "check it."
)

# --- tokenising ------------------------------------------------------------------------------
_HEREDOC_WORD_RE = re.compile(r"\s*(['\"]?)([A-Za-z_][A-Za-z0-9_]*)\1")
_REDIR_RE = re.compile(r"^\d*(>>|>\||&>>|&>|<>|>)$")
_FD_TARGET_RE = re.compile(r"^&?\d+$")
_FLAG_RE = re.compile(r"^-")
_NONLITERAL_RE = re.compile(r"[$`~*?\[{]")

_WRAPPERS = {"sudo", "nohup", "time", "env"}
_SHELL_KEYWORDS = {
    "then",
    "do",
    "else",
    "elif",
    "fi",
    "done",
    "if",
    "while",
    "for",
    "until",
    "{",
    "}",
}
_ASSIGNMENT_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")
_CD_WORDS = {"cd", "pushd", "popd", "set-location", "sl", "chdir", "push-location", "pop-location"}
_CD_NONLITERAL_WORDS = {"popd", "pop-location"}


class _NonLiteralDir:
    """A directory change the hook cannot or will not resolve (`cd -`, a bare `cd`, `popd`):
    a sentinel, not a path, so a later write idiom in the same chain fails closed."""


_NONLITERAL_DIR = _NonLiteralDir()


def _find_heredoc_terminator(line: str) -> str | None:
    """The heredoc terminator word when ``line`` opens a heredoc — a quote-aware ``<<``/``<<-``
    outside any quote, never a ``<<<`` here-string and never a ``<<`` written inside a quoted
    string (a `git log --format='<<EOF'` argument is not a heredoc)."""
    in_single = in_double = False
    i = 0
    n = len(line)
    while i < n:
        ch = line[i]
        if in_single:
            if ch == "'":
                in_single = False
            i += 1
            continue
        if in_double:
            if ch == '"':
                in_double = False
            elif ch == "\\" and i + 1 < n:
                i += 1
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
        if ch == "\\" and i + 1 < n:
            i += 2
            continue
        if ch == "<" and line[i : i + 2] == "<<":
            if line[i : i + 3] == "<<<":
                i += 3
                continue
            j = i + 2
            if j < n and line[j] == "-":
                j += 1
            m = _HEREDOC_WORD_RE.match(line, j)
            i = j
            if m:
                return m.group(2)
            continue
        i += 1
    return None


def _strip_heredocs(command: str) -> str:
    """Heredoc bodies (``<<WORD`` ... the terminator line) removed verbatim, so their text is
    never tokenised as a command (a blockquote mentioning a guardrail path is not a write)."""
    lines = command.split("\n")
    out: list[str] = []
    i = 0
    while i < len(lines):
        out.append(lines[i])
        term = _find_heredoc_terminator(lines[i])
        i += 1
        if term is not None:
            while i < len(lines) and lines[i].strip() != term:
                i += 1
            i += 1  # the terminator line itself
    return "\n".join(out)


def _chain_parts_tokenized(
    command: str, *, powershell: bool = False
) -> list[tuple[list[str], str]]:
    """Chain parts (split on ``;``, ``&&``, ``||``, ``|``, a lone ``&`` and newline, outside
    quotes), each a ``(words, raw_text)`` pair: ``words`` is a list of tokens — a quoted word
    with quotes stripped and case kept, or a redirection operator token (``>``, ``>>``, ``>|``,
    ``&>``, ``&>>``, ``<>``, ``<``, ``<<``, a digit-prefixed redirection) recognised only when
    it appears outside a quote, so a quoted ``>`` is just text, and an unquoted ``#`` starts a
    comment that runs to the end of the line — and ``raw_text`` is the part's original,
    unstripped text (a PowerShell static-method call such as ``[IO.File]::Copy(...)`` is
    matched against this text directly, quotes and all; a dequoted word has already lost the
    quote characters that pattern needs). ``powershell`` keeps a backslash literal
    (PowerShell's own escape character is the backtick, not the backslash POSIX shells use)."""
    command = _strip_heredocs(command)
    parts: list[tuple[list[str], str]] = []
    words: list[str] = []
    cur: list[str] = []
    in_single = in_double = False
    just_emitted_redir = False
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
        was_redir = just_emitted_redir
        just_emitted_redir = False
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
            elif powershell and ch == "`" and i + 1 < n:
                cur.append(command[i + 1])
                i += 2
                continue
            elif not powershell and ch == "\\" and i + 1 < n and command[i + 1] in '"\\$`':
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
        if powershell and ch == "`" and i + 1 < n:
            cur.append(command[i + 1])
            i += 2
            continue
        if not powershell and ch == "\\" and i + 1 < n and command[i + 1] != "\n":
            cur.append(command[i + 1])
            i += 2
            continue
        if ch == "#" and not cur:
            j = command.find("\n", i)
            i = n if j == -1 else j
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
        if ch in "()":
            # subshell grouping (`(cmd)`) is invisible to word tokenisation, so
            # `(git rm -q CLAUDE.md)` still reads `git` as the head word, not `(git` (round 4
            # fix-request item 9). `{`/`}` are not treated the same way: unlike `(`, `{` is
            # also brace-expansion syntax glued to a word (`{CLAUDE,README}.md`), so it must
            # stay inside the word there; only a `{`/`}` standing alone (`{ cmd; }`, whitespace
            # on both sides) is brace *grouping*, handled below by stripping it as a leading
            # keyword, the same way `then`/`do` are.
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
        if ch == "&":
            if was_redir:
                cur.append(ch)
                i += 1
                continue
            flush_part(i)
            i += 1
            part_start = i
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
            just_emitted_redir = True
            continue
        cur.append(ch)
        i += 1
    flush_part(n)
    return parts


def _strip_prefix(words: list[str]) -> list[str]:
    """A leading shell keyword (``then``/``do``/``else``/...), wrapper word (``sudo``/``nohup``/
    ``time``/``env``) or ``NAME=value`` assignment, in any combination and order, stripped
    before the real command word is matched."""
    out = list(words)
    changed = True
    while changed and out:
        changed = False
        if out[0].lower() in _SHELL_KEYWORDS:
            out = out[1:]
            changed = True
        elif out and out[0].lower() in _WRAPPERS:
            out = out[1:]
            changed = True
        elif out and _ASSIGNMENT_RE.match(out[0]):
            out = out[1:]
            changed = True
    return out


_INNER_SHELL_C_TOKEN = {
    "bash": "-c",
    "sh": "-c",
    "cmd": "/c",
    "pwsh": "-command",
    "powershell": "-command",
}


def _inner_shell_command(words: list[str]) -> str | None:
    """The quoted inner command of ``bash -c '...'``/``sh -c '...'``/``cmd /c '...'``/
    ``pwsh -Command '...'``, a flag between the interpreter and its ``-c``/``/c``/``-Command``
    token skipped (``bash --norc -c '...'``, ``cmd /d /c '...'``)."""
    if not words:
        return None
    c_token = _INNER_SHELL_C_TOKEN.get(words[0].lower())
    if c_token is None:
        return None
    for i in range(1, len(words)):
        tok = words[i].lower()
        if tok == c_token:
            return words[i + 1] if i + 1 < len(words) else None
        if not (tok.startswith("-") or tok.startswith("/")):
            return None  # a non-flag word before the -c/-Command token: not this idiom
    return None


_GIT_GLOBAL_VALUE_OPTS = {"-c", "-C", "--git-dir", "--work-tree", "--namespace", "--exec-path"}


def _git_global_scan(words: list[str]) -> tuple[int, str | None]:
    """From ``words[1:]`` (``words[0]`` is ``git``), skip every global option and its value,
    returning the index of the subcommand (``len(words)`` when there is none) and the directory
    of the last ``-C <dir>`` seen — so a global option before the verb (``git -c x=y rm f``) or
    before ``-C`` (``git -c x=y -C dir rm f``) is no longer mistaken for the verb itself (round
    4 fix-request item 1)."""
    i = 1
    n = len(words)
    dash_c: str | None = None
    while i < n:
        w = words[i]
        if w == "--":
            return i + 1, dash_c
        if not w.startswith("-") or w == "-":
            return i, dash_c
        name, has_eq, value = w.partition("=")
        if name in _GIT_GLOBAL_VALUE_OPTS:
            if has_eq:
                if name == "-C":
                    dash_c = value
                i += 1
            else:
                if name == "-C" and i + 1 < n:
                    dash_c = words[i + 1]
                i += 2
            continue
        i += 1
    return i, dash_c


def _git_dash_c(words: list[str]) -> tuple[str, list[str]] | None:
    if not words or words[0] != "git":
        return None
    verb_index, dash_c = _git_global_scan(words)
    if dash_c is None:
        return None
    return dash_c, ["git", *words[verb_index:]]


def _dir_change_target(words: list[str]):
    if not words:
        return None
    head = words[0].lower()
    if head not in _CD_WORDS:
        return None
    if head in _CD_NONLITERAL_WORDS:
        return _NONLITERAL_DIR  # the directory stack is not tracked: fail closed
    rest = _nonflag(words[1:])
    if not rest:
        return _NONLITERAL_DIR  # a bare `cd`/`pushd`/...: destination not tracked
    if rest[0] == "-":
        return _NONLITERAL_DIR  # `cd -`: the previous directory, not tracked
    return rest[0]


def _is_literal(token: str) -> bool:
    if token.lower() == "$null":
        return True  # PowerShell's null device, the `> /dev/null` of the negative list
    return not (_NONLITERAL_RE.search(token) or token.startswith(":"))  # git pathspec magic


def _nonflag(words: list[str]) -> list[str]:
    return [w for w in words if not _FLAG_RE.match(w)]


# --- interpreter literals (python/node/PowerShell calls inline in the code argument) ----------
_INTERPRETER_CODE_FLAGS = {
    "python": "-c",
    "python3": "-c",
    "node": "-e",
    "nodejs": "-e",
    "pwsh": "-command",
    "powershell": "-command",
}


def _interpreter_code_argument(words: list[str]) -> str | None:
    """The code argument of ``python -c``/``python3 -c``/``node -e``/``pwsh -Command``, scanned
    for a write call — never the command's other text (a quoted ``-m``/``--body``/``-m``
    argument that merely *mentions* ``open('CLAUDE.md','w')`` is not code the hook runs; round 4
    fix-request item 15)."""
    if not words:
        return None
    flag = _INTERPRETER_CODE_FLAGS.get(words[0].lower())
    if flag is None:
        return None
    for i in range(1, len(words)):
        if words[i].lower() == flag:
            return words[i + 1] if i + 1 < len(words) else None
    return None


_STR_PREFIX = r"[rRbBuU]{0,2}"
_STRING_LITERAL_RE = re.compile(r"['\"]([^'\"]+)['\"]")
_WRITE_MODE_RE = re.compile(r"[wax+]")
_PY_OPEN_RE = re.compile(r"\bopen\(\s*" + _STR_PREFIX + r"['\"]([^'\"]+)['\"]\s*(?:,\s*([^)]*))?\)")
_PY_PATH_OPEN_RE = re.compile(
    r"\bPath\(\s*" + _STR_PREFIX + r"['\"]([^'\"]+)['\"]\s*\)\.open\(\s*([^)]*)\)"
)
_PY_OPEN_MODE_KW_RE = re.compile(r"\bmode\s*=\s*['\"]([^'\"]*)['\"]")
_PY_OPEN_MODE_STR_RE = re.compile(r"^" + _STR_PREFIX + r"['\"]([^'\"]*)['\"]")
_OS_OPEN_RE = re.compile(r"\bos\.open\(\s*" + _STR_PREFIX + r"['\"]([^'\"]+)['\"]\s*,\s*([^)]*)\)")
_OS_WRITE_FLAGS_RE = re.compile(r"\bO_(?:WRONLY|RDWR|CREAT|TRUNC|APPEND)\b")
_PY_PATH_RE = re.compile(
    r"\bPath\(\s*['\"]([^'\"]+)['\"]\s*\)\.(?:write_text|write_bytes|unlink|rename|replace|touch)\b"
)
_PY_OS_FIRST_RE = re.compile(r"\bos\.(?:remove|unlink)\(([^)]*)\)")
_PY_OS_DEST_RE = re.compile(r"\bos\.(?:rename|replace)\(([^)]*)\)")
_PY_SHUTIL_FIRST_RE = re.compile(r"\bshutil\.rmtree\(([^)]*)\)")
_PY_SHUTIL_DEST_RE = re.compile(r"\bshutil\.(?:copy2?|copyfile|move)\(([^)]*)\)")
_NODE_FS_FIRST_RE = re.compile(
    r"\b(?:fs\.(?:promises\.)?|require\(['\"]fs['\"]\)\.)?"
    r"(?:writeFileSync|writeFile|appendFileSync|appendFile|rmSync|rm|unlinkSync|unlink|"
    r"createWriteStream|truncateSync|truncate)\(([^)]*)\)"
)
_NODE_FS_DEST_RE = re.compile(
    r"\b(?:fs\.(?:promises\.)?|require\(['\"]fs['\"]\)\.)?"
    r"(?:copyFileSync|copyFile|renameSync|rename|cpSync)\(([^)]*)\)"
)
_PS_STATIC_FIRST_RE = re.compile(
    r"\[IO\.File\]::(?:WriteAllText|WriteAllBytes|AppendAllText|Delete)\(([^)]*)\)"
)
_PS_STATIC_DEST_RE = re.compile(r"\[IO\.File\]::(?:Copy|Move)\(([^)]*)\)")


def _first_literal(args_text: str) -> str | None:
    found = _STRING_LITERAL_RE.findall(args_text)
    return found[0] if found else None


def _last_literal(args_text: str) -> str | None:
    found = _STRING_LITERAL_RE.findall(args_text)
    return found[-1] if found else None


def _open_is_write(rest: str | None) -> bool:
    """Whether a Python ``open(...)``/``Path(...).open(...)`` call (``rest`` is its text after
    the path argument, ``None`` when there is none) writes: a quoted mode literal with a write
    character, a ``mode=`` keyword the same way, or — fail closed — a second positional argument
    that is neither a quoted literal nor a keyword the hook recognises (a variable holding the
    mode, round 4 fix-request item 5)."""
    if rest is None:
        return False
    rest = rest.strip()
    if not rest:
        return False
    kw = _PY_OPEN_MODE_KW_RE.search(rest)
    if kw:
        return bool(_WRITE_MODE_RE.search(kw.group(1)))
    m = _PY_OPEN_MODE_STR_RE.match(rest)
    if m:
        return bool(_WRITE_MODE_RE.search(m.group(1)))
    first_token = rest.split(",", 1)[0].strip()
    if "=" in first_token and not first_token.startswith(("'", '"')):
        return False  # a keyword the hook does not treat as a mode (encoding=..., newline=...)
    return True  # a bare second argument: the mode cannot be verified, so treat it as a write


def _interpreter_targets(code: str) -> list[str]:
    out: list[str] = []
    for m in _PY_OPEN_RE.finditer(code):
        if _open_is_write(m.group(2)):
            out.append(m.group(1))
    for m in _PY_PATH_OPEN_RE.finditer(code):
        if _open_is_write(m.group(2)):
            out.append(m.group(1))
    for m in _OS_OPEN_RE.finditer(code):
        if _OS_WRITE_FLAGS_RE.search(m.group(2)):
            out.append(m.group(1))
    for m in _PY_PATH_RE.finditer(code):
        out.append(m.group(1))
    for pattern in (_PY_OS_FIRST_RE, _PY_SHUTIL_FIRST_RE, _NODE_FS_FIRST_RE):
        for m in pattern.finditer(code):
            lit = _first_literal(m.group(1))
            if lit is not None:
                out.append(lit)
    for pattern in (_PY_OS_DEST_RE, _PY_SHUTIL_DEST_RE, _NODE_FS_DEST_RE):
        for m in pattern.finditer(code):
            lit = _last_literal(m.group(1))
            if lit is not None:
                out.append(lit)
    return out


def _ps_static_targets(raw: str) -> list[str]:
    """``[IO.File]::...`` static-method calls, matched directly against the part's raw text —
    its own command, not code nested inside another interpreter's ``-c``/``-Command`` argument,
    so the quote characters the pattern needs are still there (round 4 fix-request item 15's
    scoping does not apply: this is the whole of what the PowerShell tool ran)."""
    out: list[str] = []
    for m in _PS_STATIC_FIRST_RE.finditer(raw):
        lit = _first_literal(m.group(1))
        if lit is not None:
            out.append(lit)
    for m in _PS_STATIC_DEST_RE.finditer(raw):
        lit = _last_literal(m.group(1))
        if lit is not None:
            out.append(lit)
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
_PS_SWITCH_FLAGS = {"-recurse", "-force", "-whatif", "-confirm", "-passthru", "-nonewline"}
_PS_PARAM_RE = re.compile(r"^-([A-Za-z]+)(?::(.*))?$")
# Copy-Item/Move-Item take (source, destination) positionally; both are candidates (Move-Item
# also deletes its source). Every other cmdlet here takes the write target as its first
# positional argument.
_PS_BOTH_ARGS = {"copy-item", "cpi", "move-item", "mi"}


def _powershell_targets(words: list[str]) -> list[str]:
    if not words or words[0].lower() not in (_PS_CMDLETS | _PS_ALIASES):
        return []
    rest = words[1:]
    targets: list[str] = []
    found_path_flag = False
    positionals: list[str] = []
    i = 0
    while i < len(rest):
        w = rest[i]
        m = _PS_PARAM_RE.match(w)
        if m:
            lname = f"-{m.group(1).lower()}"
            inline_value = m.group(2)
            if inline_value is not None:
                if lname in _PS_PATH_FLAGS:
                    targets.append(inline_value)
                    found_path_flag = True
                i += 1
                continue
            if lname in _PS_PATH_FLAGS and i + 1 < len(rest):
                targets.append(rest[i + 1])
                found_path_flag = True
                i += 2
                continue
            if lname in _PS_SWITCH_FLAGS:
                i += 1
                continue
            # an unrecognised named parameter takes its own value too, so that value is never
            # mistaken for the positional path argument (round 4 fix-request item 7)
            i += 2 if i + 1 < len(rest) else 1
            continue
        positionals.append(w)
        i += 1
    if not found_path_flag:
        if words[0].lower() in _PS_BOTH_ARGS:
            targets.extend(positionals)
        elif positionals:
            targets.append(positionals[0])
    return targets


# --- the write-idiom list (spec.md Design) -----------------------------------------------------
def _part_targets(words: list[str], raw: str = "") -> list[str]:
    """Every write-target candidate one chain part names, unresolved against any directory.
    ``raw`` is the part's original text, scanned for a PowerShell static-method call: a
    dequoted token has already lost the quote characters that pattern needs."""
    if not words:
        return []
    targets: list[str] = []
    headl = words[0].lower()

    for i, w in enumerate(words):
        if _REDIR_RE.match(w) and i + 1 < len(words):
            nxt = words[i + 1]
            if _FD_TARGET_RE.match(nxt):
                continue  # `2>&1`, `>&2`: a duplicated fd, not a file
            if nxt.startswith("&") and len(nxt) > 1:
                nxt = nxt[1:]  # `>&WORD`: WORD is neither a digit nor `-`, so it is a file
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
        verb_index, _dash_c = _git_global_scan(words)
        if verb_index < len(words):
            sub = words[verb_index].lower()
            rest = words[verb_index + 1 :]
            if sub == "checkout":
                if "--" in rest:
                    targets.extend(rest[rest.index("--") + 1 :])
                else:
                    nonflag = _nonflag(rest)
                    if len(nonflag) >= 2:
                        targets.extend(nonflag[1:])
                    elif len(nonflag) == 1:
                        targets.append(nonflag[0])
            elif sub in ("restore", "rm", "mv", "apply"):
                targets.extend(_nonflag(rest))
            elif sub == "config":
                for flag in ("--file", "-f"):
                    if flag in rest:
                        idx = rest.index(flag)
                        if idx + 1 < len(rest):
                            targets.append(rest[idx + 1])
            elif sub == "diff":
                for w in rest:
                    if w.startswith("--output="):
                        targets.append(w[len("--output=") :])
                if "--output" in rest:
                    idx = rest.index("--output")
                    if idx + 1 < len(rest):
                        targets.append(rest[idx + 1])
    elif headl in ("python", "python3") and len(words) >= 3 and words[1] == "-m":
        mod = words[2].lower()
        rest = words[3:]
        if mod == "json.tool":
            nonflag = _nonflag(rest)
            if len(nonflag) >= 2:
                targets.append(nonflag[1])
        elif mod == "pytest":
            for w in rest:
                if w.startswith("--basetemp="):
                    targets.append(w[len("--basetemp=") :])
            if "--basetemp" in rest:
                idx = rest.index("--basetemp")
                if idx + 1 < len(rest):
                    targets.append(rest[idx + 1])
    elif headl == "gh" and len(words) >= 3 and words[1] == "release" and words[2] == "download":
        for flag in ("-O", "--output"):
            if flag in words:
                idx = words.index(flag)
                if idx + 1 < len(words):
                    targets.append(words[idx + 1])

    targets.extend(_powershell_targets(words))
    targets.extend(_ps_static_targets(raw))
    code = _interpreter_code_argument(words)
    if code is not None:
        targets.extend(_interpreter_targets(code))
    return list(dict.fromkeys(targets))


def shell_write_targets(command: str, *, powershell: bool = False) -> list[str]:
    """Every write-target candidate the command names anywhere in its chain, unresolved
    against any working directory. A thin projection of ``_resolution_walk`` (below), which
    does the identical chain-part dispatch (wrapper/keyword/assignment-stripping, ``git -C``,
    inner-shell recursion) while also tracking the directory each candidate resolves against;
    the ``cwd`` passed here is never read since only the target itself is kept."""
    out = [
        target
        for target, _base, _nonliteral in _resolution_walk(command, "", powershell=powershell)
    ]
    return list(dict.fromkeys(out))


_GIT_BASH_ABS_RE = re.compile(r"^/([A-Za-z])(/.*)?$")


def _resolve(base: str, raw: str) -> str:
    raw_fs = raw.replace("\\", "/")
    if len(raw_fs) >= 2 and raw_fs[1] == ":":
        return raw
    if raw_fs.startswith("/"):
        base_fs = str(base).replace("\\", "/")
        if len(base_fs) >= 2 and base_fs[1] == ":":
            m = _GIT_BASH_ABS_RE.match(raw_fs)
            if m:  # Git Bash's `/c/...` spelling of a Windows root's `C:/...`
                return f"{m.group(1)}:{m.group(2) or '/'}"
        return raw
    return str(Path(base) / raw)


def _resolution_walk(command: str, cwd: str, *, powershell: bool = False):
    """Yields ``(raw_target, base_dir, base_is_nonliteral)`` for every write-target candidate,
    tracking a literal ``cd``/``pushd``/``Set-Location``/``git -C`` earlier in the chain."""
    current = cwd
    nonliteral = False
    for words, raw_text in _chain_parts_tokenized(command, powershell=powershell):
        plain = _strip_prefix(words)
        if not plain:
            continue
        dirarg = _dir_change_target(plain)
        if dirarg is not None:
            if dirarg is _NONLITERAL_DIR:
                nonliteral = True
            elif _is_literal(dirarg):
                current = _resolve(current, dirarg)
                nonliteral = False
            else:
                nonliteral = True
            continue
        git_c = _git_dash_c(plain)
        if git_c is not None:
            # `git -C <dir>` changes the working directory of that one git process only; unlike
            # `cd`, it never persists to a later part of the same chain (round 4 review finding:
            # `git -C docs status && echo x > CLAUDE.md` writes the real root CLAUDE.md, not
            # docs/CLAUDE.md, no matter what the git invocation's own directory was) — so `base`
            # is local to this part and `current`/`nonliteral` are left untouched.
            dirarg2, rest = git_c
            if _is_literal(dirarg2):
                base, base_nl = _resolve(current, dirarg2), False
            else:
                base, base_nl = current, True
            for target in _part_targets(rest, raw_text):
                yield target, base, base_nl
            continue
        inner = _inner_shell_command(plain)
        if inner is not None:
            inner_ps = powershell or plain[0].lower() in ("pwsh", "powershell")
            for target, base, base_nl in _resolution_walk(inner, current, powershell=inner_ps):
                yield target, base, base_nl or nonliteral
            continue
        for target in _part_targets(plain, raw_text):
            yield target, current, nonliteral


_PROTECTED_WILDCARD_RE = re.compile(r"[*?\[]")


def _pattern_anchor_and_prefix(pattern: str) -> tuple[bool, str]:
    """Mirrors ``_common.glob_to_regex``'s own anchoring rule exactly (a pattern is anchored
    when it contains a ``/`` anywhere but a lone trailing one): the fixed, non-wildcard prefix
    of an anchored pattern, so an ancestor directory of that prefix can be recognised even
    though it never matches the pattern itself (round 4 fix-request item 3)."""
    p = pattern.strip().replace("\\", "/")
    if p.startswith("./"):
        p = p[2:]
    anchored = "/" in p.rstrip("/")
    p = p.strip("/")
    m = _PROTECTED_WILDCARD_RE.search(p)
    cut = m.start() if m else len(p)
    prefix = p[:cut].rstrip("/")
    return anchored, prefix


def _protected_roots(root: str, patterns: list[str], plugin_root: str | None) -> list[str]:
    """Absolute, normalised prefixes that must not be deleted or moved away as a whole: the
    plugin root, and the fixed prefix of every *anchored* protected pattern. A bare-name
    pattern (no ``/``, matching any directory) is left out — with no anchor, its ancestor is
    any directory at all, no narrower a check than the file-level match already does."""
    out: list[str] = []
    if plugin_root:
        out.append(plugin_root)
    for pattern in patterns:
        anchored, prefix = _pattern_anchor_and_prefix(pattern)
        if anchored and prefix:
            out.append(protected_paths.norm(str(Path(root) / prefix)))
    return out


def _is_ancestor_of_protected(resolved: str, protected_roots: list[str]) -> bool:
    cand = protected_paths.norm(resolved).rstrip("/")
    return any(prot == cand or prot.startswith(cand + "/") for prot in protected_roots)


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
    powershell = payload.get("tool_name") == "PowerShell"

    # Nothing to check at all: skip the config load, the branch lookup and the test-file-lock
    # query entirely, so an ordinary read-only command (`git status`) is never denied just
    # because the project's change folder or sdlc.yaml cannot be read (round 4 fix-request
    # item 18).
    candidates = list(_resolution_walk(command, cwd, powershell=powershell))
    if not candidates:
        return Decision.allow()

    try:
        config = load_sdlc_config(root)
        patterns = protected_paths.protected_patterns(config)
    except protected_paths.ConfigError as exc:
        return Decision.deny(
            f"Shell guard cannot read the project's guardrail config ({exc}); refusing every "
            "shell write until the owner fixes sdlc.yaml."
        )
    plugin_root = protected_paths.real(args.plugin_root) if args.plugin_root else None
    protected_roots = _protected_roots(root, patterns, plugin_root)

    test_patterns: list[str] | None = None
    branch = git(root, "rev-parse", "--abbrev-ref", "HEAD").strip()
    change_id = test_file_lock.locked_change_id(branch) if branch else None
    if change_id is not None:
        try:
            if test_file_lock.is_locked(root, change_id):
                test_patterns = test_file_lock.test_path_patterns(config)
        except test_file_lock.ConfigError as exc:
            return Decision.deny(test_file_lock.FAIL_CLOSED.format(error=exc))

    for raw, base, nonliteral in candidates:
        if nonliteral or not _is_literal(raw):
            d = Decision.deny(REASON_NONLITERAL.format(target=raw))
            d.extra = {"branch": branch}
            return d
        resolved = _resolve(base, raw)
        reason = protected_paths._check_one(resolved, root, patterns, plugin_root)
        if not reason and _is_ancestor_of_protected(resolved, protected_roots):
            reason = f"{resolved} is or contains a path that matches the project's guardrails"
        if reason:
            d = Decision.deny(protected_paths.REASON.format(what=reason))
            d.extra = {"branch": branch}
            return d
        if test_patterns:
            for candidate in {protected_paths.norm(resolved), protected_paths.real(resolved)}:
                rel = protected_paths.rel_to(root, candidate)
                if rel is not None and any(
                    protected_paths.matches(pattern, rel) for pattern in test_patterns
                ):
                    d = Decision.deny(test_file_lock.REASON.format(path=rel))
                    d.extra = {"branch": branch}
                    return d
    return Decision.allow()


def _log_default_path(root: str, branch: str | None) -> Path:
    """The evidence-folder log path ``log_decision`` would compute itself, from a branch this
    call already knows — so a block never pays for a second ``git rev-parse`` (``decide()``'s
    own, above) on top of the log's: with a hung git, two sequential 20s calls against the
    hook's 30s timeout meant a denial was never emitted at all, and a timed-out PreToolUse hook
    does not block (round 4 fix-request item 19)."""
    path = Path(root) / HOOK_LOG_DEFAULT
    if not branch:
        return path
    try:
        from state import conventions as conv

        parsed = conv.parse_branch(branch)
        change_dir = conv.find_change_dir(Path(root), parsed[0]) if parsed else None
        if change_dir is not None:
            path = change_dir / HOOK_LOG_EVIDENCE
    except (OSError, ValueError):
        pass
    return path


def _decide_and_log(payload: dict, argv: list[str]) -> Decision:
    decision = decide(payload, argv)
    if decision.block:
        branch = (decision.extra or {}).get("branch")
        default_path = _log_default_path(project_dir(payload), branch) if branch else None
        log_decision(HOOK, "block", decision.reason, payload, default_path=default_path)
    return decision


if __name__ == "__main__":
    sys.exit(run_hook(_decide_and_log, "PreToolUse", sys.argv[1:], log=False))
