"""Tag the framework release the plugin manifest names, once, on the default branch.

Run by ``.github/workflows/sdlc-tag.yml`` after every push to ``main`` that touches
``.claude-plugin/plugin.json`` (and by hand: ``python .github/scripts/sdlc_tag.py``). It reads
``version`` from the manifest and creates the lightweight tag ``v<version>`` on HEAD when no
such tag exists on ``origin``; an existing tag is left exactly where it is (a version is
tagged once, on the commit that first carried it, never moved). Projects pin the framework by
this tag (``sdlc.yaml: plugin.version``; ``.github/scripts/sdlc_pin.py`` in the project turns
it into ``ref=v<version>``), so a release without its tag breaks every phase job of every
project that pins it.

Why a workflow: the owner asked for the tags to be created by the session, and a cloud
session's git proxy refuses ``refs/tags/*`` (HTTP 403, 2026-09-24, session 4): it pushes
branches only. The workflow token may push a tag (``permissions: contents: write``), and a
tag push starts no other workflow (the token rule), which is what a release tag needs.

Outputs (``$GITHUB_OUTPUT`` and stdout): ``version=<version>``, ``tag=v<version>``,
``created=true|false``. Exit 0 in both cases; 1 when the manifest is missing or carries no
version; 2 when git fails.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

MANIFEST = Path(".claude-plugin") / "plugin.json"
VERSION_RE = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+(?:[-+][0-9A-Za-z.-]+)?$")


def read_version(manifest: Path) -> str:
    try:
        data = json.loads(manifest.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise SystemExit(f"{manifest}: cannot read the plugin manifest: {exc}") from exc
    version = str(data.get("version") or "").strip() if isinstance(data, dict) else ""
    if not VERSION_RE.match(version):
        raise SystemExit(f"{manifest}: 'version' is missing or not a version: {version!r}")
    return version


def tag_for(version: str) -> str:
    return version if version.startswith("v") else f"v{version}"


def git(root: Path, *args: str) -> str:
    proc = subprocess.run(
        ["git", *args], cwd=root, capture_output=True, text=True, encoding="utf-8"
    )
    if proc.returncode != 0:
        raise SystemExit(f"git {' '.join(args)} failed: {proc.stderr.strip() or proc.stdout}")
    return proc.stdout


def tag_exists(root: Path, tag: str, remote: str) -> bool:
    out = git(root, "ls-remote", "--tags", remote, f"refs/tags/{tag}", f"refs/tags/{tag}^{{}}")
    return any(line.strip() for line in out.splitlines())


def write_outputs(values: dict[str, str]) -> None:
    lines = [f"{k}={v}" for k, v in values.items()]
    print("\n".join(lines))
    path = os.environ.get("GITHUB_OUTPUT")
    if path:
        with open(path, "a", encoding="utf-8") as fh:
            fh.write("\n".join(lines) + "\n")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0])
    p.add_argument("--root", default=".")
    p.add_argument("--remote", default="origin")
    p.add_argument("--dry-run", action="store_true", help="report; create and push nothing")
    args = p.parse_args(argv)
    root = Path(args.root).resolve()
    try:
        version = read_version(root / MANIFEST)
        tag = tag_for(version)
        exists = tag_exists(root, tag, args.remote)
        created = False
        if not exists and not args.dry_run:
            git(root, "tag", tag)
            git(root, "push", args.remote, f"refs/tags/{tag}")
            created = True
    except SystemExit as exc:
        print(str(exc), file=sys.stderr)
        return 1 if "manifest" in str(exc) else 2
    write_outputs({"version": version, "tag": tag, "created": str(created).lower()})
    return 0


if __name__ == "__main__":
    sys.exit(main())
