"""R64: a re-run of /sdlc-init refreshes the create-only copies nobody edited, recognised by
the hash of an older release's template (plugin/init/refresh.py,
plugin/init/template_hashes.json); an edited copy and every guardrail file are only
reported."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from init import refresh, sdlc_init

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "sample-python-project"
TEMPLATE = ROOT / "template"
README = "changes/README.md"
WORKFLOW = ".github/workflows/sdlc-design.yml"
OLDER = "\n<!-- a sentence an older release had -->\n"
OLDER_YAML = "\n# a line an older release had\n"


def _init(root: Path, *extra: str) -> dict:
    return sdlc_init.run(sdlc_init.build_parser().parse_args(["--root", str(root), *extra]))


@pytest.fixture
def project(tmp_path) -> Path:
    root = tmp_path / "proj"
    shutil.copytree(FIXTURE, root)
    _init(root)
    return root


def _older(rel: str) -> str:
    """The template as an older release had it: today's text plus one line."""
    extra = OLDER_YAML if rel.endswith((".yml", ".py")) else OLDER
    return (TEMPLATE / rel).read_text(encoding="utf-8") + extra


def _manifest_with(monkeypatch, entries: dict[str, str]) -> None:
    """The shipped manifest plus ``{rel: older template text}``, each as version 1.0.10."""
    files = {rel: dict(known) for rel, known in refresh.load_manifest().items()}
    for rel, text in entries.items():
        files.setdefault(rel, {})[refresh.digest(refresh.canonical_template(text))] = "1.0.10"
    monkeypatch.setattr(refresh, "load_manifest", lambda path=refresh.MANIFEST: files)


def _render(rel: str, text: str, names: list[str] | None = None, branch: str = "main") -> str:
    """``text`` rendered as /sdlc-init renders ``rel`` for the fixture project."""
    values = {"FRAMEWORK_REPO": sdlc_init.DEFAULT_FRAMEWORK_REPO}
    out = sdlc_init.apply_env_markers(
        text.replace("{{FRAMEWORK_REPO}}", "{{FRAMEWORK_REPO}}"), names or []
    )
    out = out.replace("{{FRAMEWORK_REPO}}", values["FRAMEWORK_REPO"])
    if branch != "main":
        out = sdlc_init.BRANCH_FILTER_RE.sub(rf"\g<1>{branch}\g<2>", out)
    return out


# --- the manifest -------------------------------------------------------------------------
@pytest.mark.parametrize("rel", sdlc_init.REFRESHED_COPIES)
def test_the_manifest_knows_every_current_template(rel):
    """A template change without its hash would leave this version's copies unrecognised on
    the next upgrade: run `python tasks.py template-hashes` and commit the file."""
    text = (TEMPLATE / rel).read_text(encoding="utf-8")
    assert refresh.digest(refresh.canonical_template(text)) in refresh.load_manifest()[rel]


def test_the_refreshed_copies_hold_no_guardrail_file():
    """Decision 6: REVIEW.md, bands.yaml, CLAUDE.md, sdlc.yaml and .claude/** are the owner's."""
    for rel in sdlc_init.REFRESHED_COPIES:
        assert rel not in ("REVIEW.md", "bands.yaml", "CLAUDE.md", "sdlc.yaml")
        assert not rel.startswith(".claude/")
    assert refresh.MARKER_RE.pattern == sdlc_init.ENV_MARKER_RE.pattern


def test_a_missing_or_broken_manifest_refreshes_nothing(tmp_path):
    assert refresh.load_manifest(tmp_path / "none.json") == {}
    broken = tmp_path / "broken.json"
    broken.write_text("{not json", encoding="utf-8")
    assert refresh.load_manifest(broken) == {}


# --- the canonical forms --------------------------------------------------------------------
@pytest.mark.parametrize("branch", ["main", "trunk"])
@pytest.mark.parametrize("names", [[], ["NPM_TOKEN"], ["NPM_TOKEN", "DB_URL"]])
def test_a_rendered_copy_canonicalises_to_its_template(names, branch):
    """The workflow as a project with env names and another default branch has it compares
    with the template it came from; so does a CRLF checkout of it."""
    for rel in sdlc_init.WORKFLOW_FILES:
        text = (TEMPLATE / rel).read_text(encoding="utf-8")
        copy = _render(rel, text, names, branch)
        canon = refresh.canonical_copy(copy, sdlc_init.DEFAULT_FRAMEWORK_REPO, names, branch)
        assert canon == refresh.canonical_template(text), (rel, names, branch)
        crlf = copy.replace("\n", "\r\n")
        canon = refresh.canonical_copy(crlf, sdlc_init.DEFAULT_FRAMEWORK_REPO, names, branch)
        assert canon == refresh.canonical_template(text), rel


def test_a_names_line_the_owner_added_is_not_taken_for_the_markers():
    """Only the names the project declares are dropped: an env line for another name, or an
    env: key that holds more than the names, is an edit."""
    text = "    env:\n      OTHER: ${{ secrets.OTHER || vars.OTHER }}\n    run: x\n"
    assert refresh.canonical_copy(text, "", ["NPM_TOKEN"]) == text
    mixed = "    env:\n      NPM_TOKEN: ${{ secrets.NPM_TOKEN || vars.NPM_TOKEN }}\n      X: 1\n"
    assert refresh.canonical_copy(mixed, "", ["NPM_TOKEN"]) == "    env:\n      X: 1\n"


# --- the re-run ------------------------------------------------------------------------------
def test_a_pristine_older_copy_is_refreshed_with_this_version(project, monkeypatch):
    _manifest_with(monkeypatch, {README: _older(README), WORKFLOW: _older(WORKFLOW)})
    (project / README).write_text(_older(README), encoding="utf-8")
    (project / WORKFLOW).write_text(_render(WORKFLOW, _older(WORKFLOW)), encoding="utf-8")
    report = _init(project)
    assert report["files"][README] == "refreshed (was 1.0.10)"
    assert report["files"][WORKFLOW] == "refreshed (was 1.0.10)"
    assert report["refreshed"] == {README: "1.0.10", WORKFLOW: "1.0.10"}
    assert (project / README).read_text(encoding="utf-8") == (TEMPLATE / README).read_text(
        encoding="utf-8"
    )
    assert OLDER_YAML.strip() not in (project / WORKFLOW).read_text(encoding="utf-8")
    again = _init(project)  # the refreshed copies are now this version's: nothing moves
    assert again["files"][README] == "kept" and again["files"][WORKFLOW] == "unchanged"
    assert again["refreshed"] == {}


def test_an_edited_copy_is_kept_and_reported(project, monkeypatch):
    _manifest_with(monkeypatch, {README: _older(README), WORKFLOW: _older(WORKFLOW)})
    edited = _older(README) + "Our own note.\n"
    (project / README).write_text(edited, encoding="utf-8")
    workflow = _render(WORKFLOW, _older(WORKFLOW)) + "# ours\n"
    (project / WORKFLOW).write_text(workflow, encoding="utf-8")
    report = _init(project)
    assert report["files"][README].startswith("kept; outdated (edited)")
    assert (
        report["files"][WORKFLOW].startswith("outdated: ")
        and "(edited" in report["files"][WORKFLOW]
    )
    assert (project / README).read_text(encoding="utf-8") == edited
    assert (project / WORKFLOW).read_text(encoding="utf-8") == workflow
    assert report["refreshed"] == {}


def test_a_copy_with_no_recorded_hash_is_reported_never_replaced(project, monkeypatch):
    monkeypatch.setattr(refresh, "load_manifest", lambda path=refresh.MANIFEST: {})
    (project / README).write_text(_older(README), encoding="utf-8")
    report = _init(project)
    assert report["files"][README].startswith("kept; outdated (edited)")
    assert (project / README).read_text(encoding="utf-8") == _older(README)


def test_a_guardrail_file_is_never_written_even_when_pristine(project, monkeypatch):
    """Decision 6: REVIEW.md as an older release wrote it is reported, never refreshed."""
    older = _older("REVIEW.md")
    _manifest_with(monkeypatch, {"REVIEW.md": older})
    (project / "REVIEW.md").write_text(older, encoding="utf-8")
    report = _init(project)
    assert report["files"]["REVIEW.md"].startswith("kept; outdated: ")
    assert "reviewed PR" in report["files"]["REVIEW.md"]
    assert (project / "REVIEW.md").read_text(encoding="utf-8") == older


def test_the_check_script_is_refreshed_like_the_readmes(project, monkeypatch):
    rel = "evals/check.py"
    _manifest_with(monkeypatch, {rel: _older(rel)})
    (project / rel).write_text(_older(rel), encoding="utf-8")
    assert _init(project)["files"][rel] == "refreshed (was 1.0.10)"


def test_the_shipped_manifest_is_well_formed():
    data = json.loads(refresh.MANIFEST.read_text(encoding="utf-8"))
    assert data["schema"] == refresh.SCHEMA
    assert set(data["files"]) == set(sdlc_init.REFRESHED_COPIES)
    for known in data["files"].values():
        for digest, version in known.items():
            assert len(digest) == 64 and version.count(".") == 2
