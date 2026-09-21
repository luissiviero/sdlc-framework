"""Deterministic check behind the ux-conventions skill: which UI files the change touches and
whether the change folder holds the mock and the screenshots the visual loop needs (article
p.28 step 5). Advisory.

    python "${CLAUDE_PLUGIN_ROOT}/plugin/skills/ux-conventions/check.py" --root . [--id 0001]
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from gate import policy  # noqa: E402
from state import conventions as c  # noqa: E402

UI_SUFFIXES = {".html", ".css", ".scss", ".jsx", ".tsx", ".vue", ".svelte"}
UI_HINTS = ("templates/", "components/", "views/", "pages/", "static/", "ui/")
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".gif"}
HARDCODED_TEXT = re.compile(r">\s*[A-Z][a-z]+(?:\s+\w+){2,}\s*<")  # visible copy inline in markup


def is_ui(rel: str) -> bool:
    low = rel.lower()
    return Path(rel).suffix.lower() in UI_SUFFIXES or any(h in low for h in UI_HINTS)


def main(argv: list[str] | None = None) -> int:
    p = policy.base_parser(__doc__)
    p.add_argument("--id", default=None, help="change id whose evidence/ to inspect")
    args = p.parse_args(argv)
    ch = policy.load_change(Path(args.root), args.base)
    findings: list[str] = []
    notes: list[str] = [ch.note] if ch.note else []
    ui_files = [f for f in ch.files if is_ui(f)]
    if not ui_files:
        notes.append("no UI file in the diff; the UX conventions do not apply to this change")
        return policy.report("ux-conventions check", findings, notes)
    notes.append(f"UI files changed: {', '.join(ui_files[:10])}")
    for rel, lines in ch.added.items():
        if rel in ui_files and Path(rel).suffix.lower() in {
            ".html",
            ".jsx",
            ".tsx",
            ".vue",
            ".svelte",
        }:
            for line_no, text in lines:
                if HARDCODED_TEXT.search(text):
                    findings.append(f"{rel}:{line_no}: visible copy hard-coded in markup")
                    break
    if args.id:
        change_dir = c.find_change_dir(ch.root, args.id)
        if change_dir is None:
            findings.append(f"no change folder for id {args.id}")
        else:
            images = [
                q.name
                for q in (change_dir / "evidence").glob("*")
                if q.suffix.lower() in IMAGE_SUFFIXES
            ]
            if not images:
                findings.append(
                    "UI changed but evidence/ holds no screenshot: run the visual loop "
                    "(implement, screenshot, compare with the mock) and save the result"
                )
            else:
                notes.append(f"screenshots in evidence/: {', '.join(images[:10])}")
    else:
        notes.append("pass --id <change id> to check the screenshots in evidence/")
    return policy.report("ux-conventions check", findings, notes)


if __name__ == "__main__":
    sys.exit(main())
