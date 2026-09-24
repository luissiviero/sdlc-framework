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

With ``GITHUB_TOKEN`` and ``GITHUB_REPOSITORY`` in the environment (the workflow passes
``github.token``), the tag also gets a GitHub Release page named after it, with the
notes GitHub generates from the merged pull requests, unless one exists already; the
Releases page then lists every version, not only the ones made by hand (0.2.15–0.2.17
were tags only). A release that cannot be created is reported, never fatal: the tag is
what projects pin.

Outputs (``$GITHUB_OUTPUT`` and stdout): ``version=<version>``, ``tag=v<version>``,
``created=true|false``, ``release=<url>|exists|skipped|failed``. Exit 0 in all of those
cases; 1 when the manifest is missing or carries no version; 2 when git fails.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
from collections.abc import Callable
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


API = "https://api.github.com"


def _api(
    method: str, url: str, token: str, body: dict | None, opener: Callable
) -> tuple[int, dict]:
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("X-GitHub-Api-Version", "2022-11-28")
    if data is not None:
        req.add_header("Content-Type", "application/json")
    try:
        with opener(req, timeout=30) as resp:
            payload = resp.read().decode("utf-8")
            return resp.status, (json.loads(payload) if payload else {})
    except urllib.error.HTTPError as exc:
        return exc.code, {}


def create_release(
    repo: str, tag: str, token: str, opener: Callable = urllib.request.urlopen
) -> str:
    """A GitHub Release for ``tag`` in ``owner/repo`` with generated notes: the release's
    URL when created, ``exists`` when the tag already has one, ``failed:<status>`` when
    the API refused (reported, never fatal)."""
    status, _ = _api("GET", f"{API}/repos/{repo}/releases/tags/{tag}", token, None, opener)
    if status == 200:
        return "exists"
    body = {"tag_name": tag, "name": tag, "generate_release_notes": True}
    status, data = _api("POST", f"{API}/repos/{repo}/releases", token, body, opener)
    if status == 201:
        return str(data.get("html_url") or "created")
    return f"failed:{status}"


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
    p.add_argument("--no-release", action="store_true", help="the tag only, no release page")
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
    token = os.environ.get("GITHUB_TOKEN", "").strip()
    repo = os.environ.get("GITHUB_REPOSITORY", "").strip()
    release = "skipped"
    if not args.dry_run and not args.no_release and token and repo:
        release = create_release(repo, tag, token)
        if release.startswith("failed"):
            print(f"the release page for {tag} was not created ({release})", file=sys.stderr)
    write_outputs(
        {"version": version, "tag": tag, "created": str(created).lower(), "release": release}
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
