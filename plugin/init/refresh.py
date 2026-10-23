"""R64: a re-run of /sdlc-init refreshes the create-only copies nobody edited.

A copy the template wrote and nobody changed is recognised by its hash. ``template_hashes.json``
holds, for each file ``/sdlc-init`` writes create-only and refreshes, the hash of every text the
template had at a released version (``python tasks.py template-hashes``, read from the
framework's own tags; a test fails when the current template's hash is missing).

Both sides are hashed in a canonical form, so a copy rendered for one project compares with
the template it came from:

- the template's: the ``# sdlc:commands.env`` marker lines dropped (``{{FRAMEWORK_REPO}}`` is
  kept as written, the only placeholder these files have ever had);
- the copy's: the project's framework repository put back as ``{{FRAMEWORK_REPO}}``, the lines
  the markers expanded to for the project's ``commands.env`` names dropped, and the
  ``branches:`` filter put back to ``main``.

A copy whose canonical form matches an older release's template is pristine, and the re-run
replaces it with this version's text (``refreshed (was <version>)``). Anything else is an
edit, or a copy rendered with values the project no longer has: it is never overwritten.
Guardrail files are never refreshed (decision 6); ``sdlc_init`` only reports them.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

MANIFEST = Path(__file__).resolve().with_name("template_hashes.json")
SCHEMA = 1
PLACEHOLDER = "{{FRAMEWORK_REPO}}"
# the same marker as sdlc_init.ENV_MARKER_RE (tests/test_init.py holds the two equal)
MARKER_RE = re.compile(r"(?m)^( *)# sdlc:commands\.env( setup)?\n")
ENV_KEY_RE = re.compile(r"^( *)env:$")


def _lf(text: str) -> str:
    """Line endings as the install writes them (a Windows checkout may hold CRLF)."""
    return text.replace("\r\n", "\n")


def canonical_template(text: str) -> str:
    return MARKER_RE.sub("", _lf(text))


def _env_line(name: str) -> re.Pattern[str]:
    n = re.escape(name)
    return re.compile(rf"^ *{n}: \$\{{\{{ secrets\.{n} \|\| vars\.{n} \}}\}}$")


def _drop_env_lines(text: str, names: list[str]) -> str:
    """The lines the env markers expanded to, dropped: each ``NAME: ${{ secrets.NAME || vars.
    NAME }}`` line of a known name, and an ``env:`` key the setup marker added when nothing
    else is under it."""
    if not names:
        return text
    patterns = [_env_line(n) for n in names]
    lines = text.split("\n")
    is_env = [any(p.match(line) for p in patterns) for line in lines]
    out = []
    for i, line in enumerate(lines):
        if is_env[i]:
            continue
        key = ENV_KEY_RE.match(line)
        if key and i + 1 < len(lines) and is_env[i + 1]:
            j = i + 1
            while j < len(lines) and is_env[j]:
                j += 1
            rest = lines[j] if j < len(lines) else ""
            indent = len(rest) - len(rest.lstrip(" "))
            if not rest.strip() or indent <= len(key.group(1)):
                continue  # the setup marker's own env: key, holding only the names
        out.append(line)
    return "\n".join(out)


def canonical_copy(
    text: str, framework_repo: str, env_names: list[str], default_branch: str = "main"
) -> str:
    text = _lf(text)
    if framework_repo:
        text = text.replace(framework_repo, PLACEHOLDER)
    if default_branch and default_branch != "main":
        branch = re.escape(default_branch)
        text = re.sub(rf"(?m)^(\s*branches:\s*\[){branch}(\]\s*)$", r"\g<1>main\g<2>", text)
    return _drop_env_lines(text, env_names)


def digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def load_manifest(path: Path = MANIFEST) -> dict[str, dict[str, str]]:
    """``{rel: {hash: the first version whose template had that text}}``; empty when the
    file is missing or unreadable, so nothing is ever refreshed by mistake."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    files = data.get("files") if isinstance(data, dict) else None
    return files if isinstance(files, dict) else {}


def written_by(
    rel: str,
    text: str,
    *,
    framework_repo: str,
    env_names: list[str],
    default_branch: str = "main",
    manifest: dict[str, dict[str, str]] | None = None,
) -> str | None:
    """The release whose template wrote ``text`` unchanged, or None (an edit, or a file this
    module does not know)."""
    known = (load_manifest() if manifest is None else manifest).get(rel) or {}
    canon = canonical_copy(text, framework_repo, env_names, default_branch)
    return known.get(digest(canon))
