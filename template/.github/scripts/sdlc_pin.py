"""Print the framework pin this project's sdlc.yaml declares, for the workflows to check out.

Installed into the project by ``/sdlc-init`` (build guide step 30, task 30.8) and run as the
second step of every SDLC workflow, *before* the framework itself is checked out — which is
why it lives in the project and imports nothing but the standard library.

    python .github/scripts/sdlc_pin.py [--root .] [--file sdlc.yaml]

It reads the ``plugin:`` block of ``sdlc.yaml`` and writes two step outputs into
``$GITHUB_OUTPUT`` (and prints them, so a local run shows the same two lines):

    ref=v<plugin.version>            the git ref of the pinned framework release
    claude_code=<plugin.claude_code> the Claude Code CLI version the jobs install

A ``plugin.version`` that already starts with ``v`` is not doubled: ``v1.2.3`` prints
``ref=v1.2.3``. ``plugin.claude_code`` is checked against ``^[0-9A-Za-z.+-]+$`` because the
install step interpolates it into a shell command; anything else stops the workflow.

Exit codes: 0 the pin was read; 1 sdlc.yaml is missing or carries no ``plugin.version``
(the workflow must then stop rather than silently check out the framework's default branch);
2 ``plugin.claude_code`` is not a version string.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

DEFAULT_CLAUDE_CODE = "2.1.278"  # the framework's minimum, used when the key is absent
# npm version or dist-tag characters only: the value reaches a shell command in the job
CLAUDE_CODE_RE = re.compile(r"^[0-9A-Za-z.+-]+$")
PLUGIN_BLOCK_RE = re.compile(r"(?m)^plugin:[ \t]*$")
KEY_RE = r"(?m)^[ \t]+{key}:[ \t]*[\"']?([^\"'#\r\n]+)"


def plugin_block(text: str) -> str:
    """The indented body of the top-level ``plugin:`` key, or "" when there is none."""
    match = PLUGIN_BLOCK_RE.search(text)
    if not match:
        return ""
    lines = text[match.end() :].splitlines()
    body: list[str] = []
    for line in lines:
        if line.strip() and not line[0].isspace():
            break
        body.append(line)
    return "\n".join(body)


def read_key(block: str, key: str) -> str:
    match = re.search(KEY_RE.format(key=re.escape(key)), block)
    return match.group(1).strip() if match else ""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="sdlc-pin", description=__doc__.splitlines()[0])
    parser.add_argument("--root", default=".")
    parser.add_argument("--file", default="sdlc.yaml")
    args = parser.parse_args(argv)

    path = Path(args.root) / args.file
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        print(f"cannot read {path}: {exc}", file=sys.stderr)
        return 1
    block = plugin_block(text)
    version = read_key(block, "version")
    if not version:
        print(f"{path} has no plugin.version: run /sdlc-init first", file=sys.stderr)
        return 1
    claude_code = read_key(block, "claude_code") or DEFAULT_CLAUDE_CODE
    if not CLAUDE_CODE_RE.match(claude_code):
        print(
            f"{path}: plugin.claude_code {claude_code!r} is not a version string "
            "(allowed: letters, digits, '.', '+', '-')",
            file=sys.stderr,
        )
        return 2

    lines = [f"ref=v{version.removeprefix('v')}", f"claude_code={claude_code}"]
    for line in lines:
        print(line)
    out = os.environ.get("GITHUB_OUTPUT")
    if out:
        with open(out, "a", encoding="utf-8") as handle:
            handle.write("\n".join(lines) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
