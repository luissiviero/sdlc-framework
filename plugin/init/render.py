"""Template rendering for /sdlc-init: ``{{NAME}}`` placeholders, nothing else.

Deliberately not a template engine: every placeholder must be supplied, unknown ones fail,
so a half-filled project file cannot be committed silently.
"""

from __future__ import annotations

import re
from pathlib import Path

PLACEHOLDER = re.compile(r"\{\{([A-Z][A-Z0-9_]*)\}\}")


class RenderError(ValueError):
    pass


def placeholders(text: str) -> set[str]:
    return set(PLACEHOLDER.findall(text))


def render(text: str, values: dict[str, str]) -> str:
    missing = placeholders(text) - set(values)
    if missing:
        raise RenderError(f"missing values for placeholders: {sorted(missing)}")

    def sub(m: re.Match[str]) -> str:
        return str(values[m.group(1)])

    return PLACEHOLDER.sub(sub, text)


def render_file(src: Path, values: dict[str, str]) -> str:
    return render(src.read_text(encoding="utf-8"), values)
