"""R64: a re-run of /sdlc-init refreshes the create-only copies nobody edited.

A copy the template wrote and nobody changed is recognised by its hash. ``template_hashes.json``
holds, for each file ``/sdlc-init`` writes create-only and refreshes (and ``REVIEW.md``, which
it only reports), the hash of every text the template had at a released version (``python
tasks.py template-hashes``, read from the framework's own tags; a test fails when the current
template's hash is missing).

Both sides are hashed in a canonical form, so a copy rendered for one project compares with
the template it came from. ``{{FRAMEWORK_REPO}}`` is the only placeholder these files have
ever had; the ``# sdlc:commands.env`` marker lines are the one part whose rendering depends on
the project's ``commands.env`` names, so the manifest holds two hashes per text:

- ``files``, the template with its marker lines dropped: what a project with no names has;
- ``files_marked``, the template as written: a project with names is compared with it, its
  copy's exact rendered blocks (every name, in order, at a marker's place) put back as the
  marker line. A names line anywhere else, a block with a name missing or out of order, or
  a block the owner deleted, stays as it is and never matches: an edit.

The copy's other canonical steps: its framework repository put back as ``{{FRAMEWORK_REPO}}``
and its ``branches:`` filter put back to ``main`` (a ``branches: [main]`` line on a project
whose default branch has another name is an edit, since the install rewrote every one).

A copy whose canonical form matches an older release's template is pristine, and the re-run
replaces it with this version's text (``refreshed (was <version>)``). Anything else is an
edit, or a copy rendered with values the project no longer has (another ``--framework-repo``,
a renamed default branch, changed ``commands.env`` names): it is never overwritten. Guardrail
files are never refreshed (decision 6); ``sdlc_init`` only reports them.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

MANIFEST = Path(__file__).resolve().with_name("template_hashes.json")
SCHEMA = 2
PLACEHOLDER = "{{FRAMEWORK_REPO}}"
# the same marker as sdlc_init.ENV_MARKER_RE (tests/test_refresh.py holds the two equal)
MARKER_RE = re.compile(r"(?m)^( *)# sdlc:commands\.env( setup)?\n")
MARKER = "# sdlc:commands.env"
NEVER = "\0an edit no release wrote\n"  # appended to a canonical form that must not match


def _lf(text: str) -> str:
    """Line endings as the install writes them (a Windows checkout may hold CRLF)."""
    return text.replace("\r\n", "\n")


def canonical_template(text: str, marked: bool = False) -> str:
    """The template as a project with no ``commands.env`` names has it, or (``marked``) as
    written, its marker lines kept."""
    return _lf(text) if marked else MARKER_RE.sub("", _lf(text))


def _name_line(indent: str, name: str) -> str:
    return f"{indent}{name}: ${{{{ secrets.{name} || vars.{name} }}}}"


def _restore_markers(lines: list[str], names: list[str]) -> list[str]:
    """The exact blocks ``sdlc_init.apply_env_markers`` writes for ``names`` put back as their
    marker lines: ``<i>env:`` and every name at ``<i>  `` (the setup marker), or every name at
    ``<i>`` (the env marker). Nothing else is touched."""
    out: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        indent = line[: len(line) - len(line.lstrip(" "))]
        setup = [_name_line(indent + "  ", n) for n in names]
        plain = [_name_line(indent, n) for n in names]
        if line == f"{indent}env:" and lines[i + 1 : i + 1 + len(names)] == setup:
            out.append(f"{indent}{MARKER} setup")
            i += 1 + len(names)
        elif lines[i : i + len(names)] == plain:
            out.append(f"{indent}{MARKER}")
            i += len(names)
        else:
            out.append(line)
            i += 1
    return out


def canonical_copy(
    text: str, framework_repo: str, env_names: list[str], default_branch: str = "main"
) -> str:
    text = _lf(text)
    if framework_repo:
        text = text.replace(framework_repo, PLACEHOLDER)
    if default_branch and default_branch != "main":
        if re.search(r"(?m)^\s*branches:\s*\[main\]\s*$", text):
            return text + NEVER  # the install rewrote every filter: this one is an edit
        branch = re.escape(default_branch)
        text = re.sub(rf"(?m)^(\s*branches:\s*\[){branch}(\]\s*)$", r"\g<1>main\g<2>", text)
    if env_names:
        text = "\n".join(_restore_markers(text.split("\n"), env_names))
    return text


def digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def load_manifest(path: Path = MANIFEST) -> dict[str, dict[str, dict[str, str]]]:
    """``{"files": {rel: {hash: version}}, "files_marked": {...}}``, the version being the
    first release whose template had that text; empty maps when the file is missing,
    unreadable or of another schema, so nothing is ever refreshed by mistake."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        data = None
    ok = isinstance(data, dict) and data.get("schema") == SCHEMA
    return {
        key: data[key] if ok and isinstance(data.get(key), dict) else {}
        for key in ("files", "files_marked")
    }


def written_by(
    rel: str,
    text: str,
    *,
    framework_repo: str,
    env_names: list[str],
    default_branch: str = "main",
    manifest: dict[str, dict[str, dict[str, str]]] | None = None,
) -> str | None:
    """The release whose template wrote ``text`` unchanged, or None (an edit, values the
    project no longer has, or a file this module does not know)."""
    data = load_manifest() if manifest is None else manifest
    known = (data.get("files_marked" if env_names else "files") or {}).get(rel) or {}
    canon = canonical_copy(text, framework_repo, env_names, default_branch)
    return known.get(digest(canon))
