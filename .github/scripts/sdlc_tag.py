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

Only the default branch is tagged. The workflow's ``push`` trigger is limited to ``main``,
but a ``workflow_dispatch`` may be started from any ref, and a tag is created once and never
moved: a dispatch from a branch would have tagged unmerged code for good (the 1.0.0
readiness review, group B). The branch is ``GITHUB_REF_NAME`` (the workflow passes
``github.ref_name``), else the checked-out branch; the default branch is
``SDLC_DEFAULT_BRANCH`` (``github.event.repository.default_branch``), else ``origin``'s
``HEAD``, else ``main``. Any other branch, or a detached HEAD the environment does not name,
ends green with ``skipped=not the default branch`` and nothing tagged.

Nothing is tagged while ``.claude-plugin/marketplace.json`` names another version for the
plugin than ``plugin.json`` does: the run ends red with ``skipped=<the disagreement>``.
PR #217 set ``plugin.json`` alone to 1.0.2 on ``main``; this script tagged ``v1.0.2`` and
made its release while ``main``'s own checks failed on the mismatch
(``tests/test_scaffold.py``), and both had to be deleted by hand (NOTES §45 gap 8).

Outputs (``$GITHUB_OUTPUT`` and stdout): ``version=<version>``, ``tag=v<version>``,
``created=true|false``, ``release=<url>|exists|skipped|failed``, ``skipped=<reason>|``.
Exit 0 in all of those cases but the disagreement; 1 when the manifest is missing or
carries no version, or the two manifests disagree; 2 when git fails.
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
MARKETPLACE = Path(".claude-plugin") / "marketplace.json"
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


def manifests_disagree(root: Path, version: str) -> str:
    """Why ``marketplace.json`` and ``plugin.json`` disagree on the version, or "" when they
    agree or there is no marketplace manifest to disagree. An unreadable marketplace
    manifest, or one without the plugin's entry, is a disagreement: nothing is tagged."""
    path = root / MARKETPLACE
    if not path.is_file():
        return ""
    try:
        name = json.loads((root / MANIFEST).read_text(encoding="utf-8")).get("name")
        plugins = json.loads(path.read_text(encoding="utf-8")).get("plugins") or []
    except (OSError, ValueError, AttributeError) as exc:
        return f"{MARKETPLACE.as_posix()}: cannot read the marketplace manifest: {exc}"
    entry = next((p for p in plugins if isinstance(p, dict) and p.get("name") == name), None)
    if entry is None:
        return f"{MARKETPLACE.as_posix()} has no entry for the plugin {name!r}"
    listed = str(entry.get("version") or "").strip()
    if listed != version:
        return (
            f"{MARKETPLACE.as_posix()} names {name} {listed or 'without a version'} and "
            f"{MANIFEST.as_posix()} names {version}: the two manifests disagree"
        )
    return ""


def tag_for(version: str) -> str:
    return version if version.startswith("v") else f"v{version}"


def git(root: Path, *args: str) -> str:
    proc = subprocess.run(
        ["git", *args], cwd=root, capture_output=True, text=True, encoding="utf-8"
    )
    if proc.returncode != 0:
        raise SystemExit(f"git {' '.join(args)} failed: {proc.stderr.strip() or proc.stdout}")
    return proc.stdout


def current_branch(root: Path, env: dict[str, str]) -> str:
    """``GITHUB_REF_NAME`` when set, else the checked-out branch (``HEAD`` when detached)."""
    named = env.get("GITHUB_REF_NAME", "").strip()
    if named:
        return named
    return git(root, "rev-parse", "--abbrev-ref", "HEAD").strip()


def default_branch(root: Path, remote: str, env: dict[str, str]) -> str:
    """``SDLC_DEFAULT_BRANCH`` when set, else what ``refs/remotes/<remote>/HEAD`` names,
    else ``main`` (the framework repository's own default; this script is not a template)."""
    named = env.get("SDLC_DEFAULT_BRANCH", "").strip()
    if named:
        return named
    proc = subprocess.run(
        ["git", "symbolic-ref", "--quiet", f"refs/remotes/{remote}/HEAD"],
        cwd=root, capture_output=True, text=True, encoding="utf-8",
    )  # fmt: skip
    prefix = f"refs/remotes/{remote}/"
    if proc.returncode == 0 and proc.stdout.strip().startswith(prefix):
        return proc.stdout.strip()[len(prefix) :]
    return "main"


def not_the_default_branch(root: Path, remote: str, env: dict[str, str]) -> str:
    """Why nothing may be tagged from here, or "" on the default branch."""
    branch = current_branch(root, env)
    default = default_branch(root, remote, env)
    if branch == "HEAD":
        return f"not the default branch: a detached HEAD (the default branch is {default})"
    if branch != default:
        return f"not the default branch: {branch} (the default branch is {default})"
    return ""


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
    env = dict(os.environ)
    try:
        version = read_version(root / MANIFEST)
        tag = tag_for(version)
        skipped = not_the_default_branch(root, args.remote, env)
        if skipped:
            print(f"{skipped}; nothing tagged", file=sys.stderr)
            write_outputs(
                {
                    "version": version,
                    "tag": tag,
                    "created": "false",
                    "release": "skipped",
                    "skipped": skipped,
                }
            )
            return 0
        disagree = manifests_disagree(root, version)
        if disagree:
            print(f"{disagree}; nothing tagged", file=sys.stderr)
            write_outputs(
                {
                    "version": version,
                    "tag": tag,
                    "created": "false",
                    "release": "skipped",
                    "skipped": disagree,
                }
            )
            return 1
        exists = tag_exists(root, tag, args.remote)
        created = False
        if not exists and not args.dry_run:
            git(root, "tag", tag)
            git(root, "push", args.remote, f"refs/tags/{tag}")
            created = True
    except SystemExit as exc:
        print(str(exc), file=sys.stderr)
        return 1 if "manifest" in str(exc) else 2
    token = env.get("GITHUB_TOKEN", "").strip()
    repo = env.get("GITHUB_REPOSITORY", "").strip()
    release = "skipped"
    if not args.dry_run and not args.no_release and token and repo:
        release = create_release(repo, tag, token)
        if release.startswith("failed"):
            print(f"the release page for {tag} was not created ({release})", file=sys.stderr)
    write_outputs(
        {
            "version": version,
            "tag": tag,
            "created": str(created).lower(),
            "release": release,
            "skipped": "",
        }
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
