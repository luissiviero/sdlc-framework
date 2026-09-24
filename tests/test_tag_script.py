"""The framework's release-tag script (.github/scripts/sdlc_tag.py; workflow sdlc-tag.yml):
the tag v<version> from .claude-plugin/plugin.json is created once on the default branch
and never moved. A cloud session cannot push a tag (its git proxy allows branch refs only,
2026-09-24), so the workflow does it on merge."""

from __future__ import annotations

import importlib.util
import json
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / ".github" / "scripts" / "sdlc_tag.py"
spec = importlib.util.spec_from_file_location("sdlc_tag", SCRIPT)
sdlc_tag = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sdlc_tag)


def git(cwd: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=cwd, check=True, capture_output=True, text=True, encoding="utf-8"
    ).stdout


@pytest.fixture
def repo(tmp_path):
    bare = tmp_path / "bare.git"
    git(tmp_path, "init", "-q", "--bare", str(bare))
    work = tmp_path / "work"
    git(tmp_path, "init", "-q", "-b", "main", str(work))
    git(work, "config", "user.email", "owner@example.com")
    git(work, "config", "user.name", "Owner")
    (work / ".claude-plugin").mkdir()
    (work / ".claude-plugin" / "plugin.json").write_text(
        json.dumps({"name": "sdlc", "version": "0.2.15"}), encoding="utf-8"
    )
    git(work, "add", ".")
    git(work, "commit", "-q", "-m", "plugin 0.2.15")
    git(work, "remote", "add", "origin", str(bare))
    git(work, "push", "-q", "-u", "origin", "main")
    return work, bare


def test_the_version_is_read_and_turned_into_a_tag(tmp_path):
    manifest = tmp_path / "plugin.json"
    manifest.write_text('{"version": "1.2.3"}', encoding="utf-8")
    assert sdlc_tag.read_version(manifest) == "1.2.3"
    assert sdlc_tag.tag_for("1.2.3") == "v1.2.3" and sdlc_tag.tag_for("v1.2.3") == "v1.2.3"
    manifest.write_text('{"version": "main"}', encoding="utf-8")
    with pytest.raises(SystemExit, match="not a version"):
        sdlc_tag.read_version(manifest)
    with pytest.raises(SystemExit, match="cannot read"):
        sdlc_tag.read_version(tmp_path / "missing.json")


def test_the_tag_is_created_once_and_never_moved(repo, capsys, monkeypatch):
    work, bare = repo
    out_file = work.parent / "outputs.txt"
    monkeypatch.setenv("GITHUB_OUTPUT", str(out_file))
    assert sdlc_tag.main(["--root", str(work), "--dry-run"]) == 0
    assert "created=false" in capsys.readouterr().out
    assert "v0.2.15" not in git(work, "ls-remote", "--tags", "origin")
    assert sdlc_tag.main(["--root", str(work)]) == 0
    assert "created=true" in capsys.readouterr().out
    first = git(work, "rev-parse", "HEAD").strip()
    assert git(bare, "rev-parse", "refs/tags/v0.2.15").strip() == first
    assert "tag=v0.2.15" in out_file.read_text(encoding="utf-8")
    # a later commit with the same version: the tag stays on the first
    (work / "README.md").write_text("later\n", encoding="utf-8")
    git(work, "add", ".")
    git(work, "commit", "-q", "-m", "later")
    git(work, "push", "-q", "origin", "main")
    assert sdlc_tag.main(["--root", str(work)]) == 0
    assert "created=false" in capsys.readouterr().out
    assert git(bare, "rev-parse", "refs/tags/v0.2.15").strip() == first
    # a bumped version gets its own tag on that commit
    (work / ".claude-plugin" / "plugin.json").write_text(
        json.dumps({"name": "sdlc", "version": "0.2.16"}), encoding="utf-8"
    )
    git(work, "add", ".")
    git(work, "commit", "-q", "-m", "plugin 0.2.16")
    git(work, "push", "-q", "origin", "main")
    assert sdlc_tag.main(["--root", str(work)]) == 0
    assert (
        git(bare, "rev-parse", "refs/tags/v0.2.16").strip()
        == git(work, "rev-parse", "HEAD").strip()
    )


class _FakeResponse:
    def __init__(self, status, payload):
        self.status, self._payload = status, payload

    def read(self):
        return json.dumps(self._payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def _opener(script: dict):
    """An urlopen stand-in: ``script`` maps (method, url tail) to (status, payload); a
    status of 404 is raised the way urllib raises it."""
    import urllib.error

    calls = []

    def opener(req, timeout=0):
        key = (req.get_method(), req.full_url.rsplit("/repos/", 1)[1])
        calls.append((key, req.data, dict(req.header_items())))
        status, payload = script[key]
        if status >= 400:
            raise urllib.error.HTTPError(req.full_url, status, "nope", {}, None)
        return _FakeResponse(status, payload)

    opener.calls = calls
    return opener


def test_a_release_page_is_created_once_with_generated_notes():
    made = _opener(
        {
            ("GET", "o/r/releases/tags/v0.2.18"): (404, {}),
            ("POST", "o/r/releases"): (
                201,
                {"html_url": "https://github.com/o/r/releases/tag/v0.2.18"},
            ),
        }
    )
    assert sdlc_tag.create_release("o/r", "v0.2.18", "tok", made) == (
        "https://github.com/o/r/releases/tag/v0.2.18"
    )
    (_get, post) = made.calls
    assert json.loads(post[1]) == {
        "tag_name": "v0.2.18",
        "name": "v0.2.18",
        "generate_release_notes": True,
    }
    assert post[2]["Authorization"] == "Bearer tok"
    # the tag already has a release page: nothing is created
    exists = _opener({("GET", "o/r/releases/tags/v0.2.18"): (200, {"id": 1})})
    assert sdlc_tag.create_release("o/r", "v0.2.18", "tok", exists) == "exists"
    assert len(exists.calls) == 1
    # a refusal is reported, never raised
    refused = _opener(
        {("GET", "o/r/releases/tags/v0.2.18"): (404, {}), ("POST", "o/r/releases"): (403, {})}
    )
    assert sdlc_tag.create_release("o/r", "v0.2.18", "tok", refused) == "failed:403"


def test_main_reports_the_release_and_skips_it_without_a_token(repo, capsys, monkeypatch):
    work, _bare = repo
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    monkeypatch.delenv("GITHUB_REPOSITORY", raising=False)
    assert sdlc_tag.main(["--root", str(work)]) == 0
    assert "release=skipped" in capsys.readouterr().out
    monkeypatch.setenv("GITHUB_TOKEN", "tok")
    monkeypatch.setenv("GITHUB_REPOSITORY", "o/r")
    monkeypatch.setattr(sdlc_tag, "create_release", lambda repo, tag, token: f"made:{repo}:{tag}")
    assert sdlc_tag.main(["--root", str(work)]) == 0
    out = capsys.readouterr().out
    assert "created=false" in out and "release=made:o/r:v0.2.15" in out  # the tag stood
    assert sdlc_tag.main(["--root", str(work), "--no-release"]) == 0
    assert "release=skipped" in capsys.readouterr().out
    monkeypatch.setattr(sdlc_tag, "create_release", lambda repo, tag, token: "failed:403")
    assert sdlc_tag.main(["--root", str(work)]) == 0
    captured = capsys.readouterr()
    assert "release=failed:403" in captured.out and "was not created" in captured.err


def test_a_missing_manifest_is_exit_1(tmp_path, capsys):
    assert sdlc_tag.main(["--root", str(tmp_path)]) == 1
    assert "manifest" in capsys.readouterr().err
