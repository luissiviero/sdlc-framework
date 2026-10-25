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
    shipped = refresh.load_manifest()
    maps = {key: {rel: dict(known) for rel, known in shipped[key].items()} for key in shipped}
    for rel, text in entries.items():
        for key, marked in (("files", False), ("files_marked", True)):
            digest = refresh.digest(refresh.canonical_template(text, marked))
            maps[key].setdefault(rel, {})[digest] = "1.0.10"
    monkeypatch.setattr(refresh, "load_manifest", lambda path=refresh.MANIFEST: maps)


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
    manifest = refresh.load_manifest()
    assert refresh.digest(refresh.canonical_template(text)) in manifest["files"][rel]
    assert refresh.digest(refresh.canonical_template(text, True)) in manifest["files_marked"][rel]


def test_the_refreshed_copies_hold_no_guardrail_file():
    """Decision 6: REVIEW.md, bands.yaml, CLAUDE.md, sdlc.yaml and .claude/** are the owner's."""
    for rel in sdlc_init.REFRESHED_COPIES:
        assert rel not in ("REVIEW.md", "bands.yaml", "CLAUDE.md", "sdlc.yaml")
        assert not rel.startswith(".claude/")
    assert refresh.MARKER_RE.pattern == sdlc_init.ENV_MARKER_RE.pattern


def test_a_missing_or_broken_manifest_refreshes_nothing(tmp_path):
    empty = {"files": {}, "files_marked": {}}
    assert refresh.load_manifest(tmp_path / "none.json") == empty
    broken = tmp_path / "broken.json"
    broken.write_text("{not json", encoding="utf-8")
    assert refresh.load_manifest(broken) == empty
    old = tmp_path / "old.json"
    old.write_text(json.dumps({"schema": 1, "files": {README: {"x": "1.0.0"}}}), encoding="utf-8")
    assert refresh.load_manifest(old) == empty  # another schema: nothing is trusted


# --- the canonical forms --------------------------------------------------------------------
@pytest.mark.parametrize("branch", ["main", "trunk"])
@pytest.mark.parametrize("names", [[], ["NPM_TOKEN"], ["NPM_TOKEN", "DB_URL"]])
def test_a_rendered_copy_canonicalises_to_its_template(names, branch):
    """The workflow as a project with env names and another default branch has it compares
    with the template it came from; so does a CRLF checkout of it."""
    for rel in sdlc_init.WORKFLOW_FILES:
        text = (TEMPLATE / rel).read_text(encoding="utf-8")
        copy = _render(rel, text, names, branch)
        want = refresh.canonical_template(text, marked=bool(names))
        canon = refresh.canonical_copy(copy, sdlc_init.DEFAULT_FRAMEWORK_REPO, names, branch)
        assert canon == want, (rel, names, branch)
        crlf = copy.replace("\n", "\r\n")
        canon = refresh.canonical_copy(crlf, sdlc_init.DEFAULT_FRAMEWORK_REPO, names, branch)
        assert canon == want, rel


BUILD = ".github/workflows/sdlc-build.yml"
TOKEN = "      NPM_TOKEN: ${{ secrets.NPM_TOKEN || vars.NPM_TOKEN }}"


def _is_pristine(copy: str, names: list[str], branch: str = "main") -> bool:
    return (
        refresh.written_by(
            BUILD,
            copy,
            framework_repo=sdlc_init.DEFAULT_FRAMEWORK_REPO,
            env_names=names,
            default_branch=branch,
        )
        is not None
    )


def test_an_env_edit_is_never_taken_for_the_markers():
    """The fresh review of R64: an owner's change to the env lines is an edit, wherever it
    is. A: a names line added to a step with no marker; B: the lines the markers wrote,
    deleted; E: an env: key holding only the names, added; a block out of order, a block
    with a name missing. A copy with no env lines at all is the text 1.0.27 shipped, before
    the markers existed, so it is that release's pristine copy (the record's known limit)."""
    template = (TEMPLATE / BUILD).read_text(encoding="utf-8")
    assert sdlc_init.ENV_MARKER_RE.search(template), "the build workflow carries markers"
    names = ["NPM_TOKEN", "DB_URL"]
    copy = _render(BUILD, template, names)
    assert _is_pristine(copy, names)
    lines = copy.split("\n")
    run = next(i for i, line in enumerate(lines) if line.strip().startswith("run:"))
    block = [f"{' ' * 10}{n}: ${{{{ secrets.{n} || vars.{n} }}}}" for n in names]
    a = "\n".join([*lines[:run], *block, *lines[run:]])
    assert not _is_pristine(a, names)  # A
    b = "\n".join(
        line for line in lines if "secrets.NPM_TOKEN" not in line and "secrets.DB_URL" not in line
    )
    assert not _is_pristine(b, names)  # B
    e = "\n".join([*lines[:run], "        env:", *(" " * 2 + x for x in block), *lines[run:]])
    assert not _is_pristine(e, names)  # E
    swapped = _render(BUILD, template, list(reversed(names)))
    assert not _is_pristine(swapped, names)
    assert not _is_pristine(_render(BUILD, template, names[:1]), names)
    stripped = refresh.written_by(
        BUILD,
        _render(BUILD, template, []),
        framework_repo=sdlc_init.DEFAULT_FRAMEWORK_REPO,
        env_names=names,
    )
    assert stripped is None or tuple(map(int, stripped.split("."))) < (1, 0, 29)


def test_a_main_filter_on_a_trunk_project_is_an_edit():
    """The install rewrote every filter to the default branch, so one set back is an edit."""
    rel = ".github/workflows/sdlc-agent-evals.yml"
    template = (TEMPLATE / rel).read_text(encoding="utf-8")
    copy = _render(rel, template, [], "trunk")
    assert "branches: [trunk]" in copy
    kwargs = {"framework_repo": sdlc_init.DEFAULT_FRAMEWORK_REPO, "env_names": []}
    assert refresh.written_by(rel, copy, default_branch="trunk", **kwargs) is not None
    edited = copy.replace("branches: [trunk]", "branches: [main]", 1)
    assert refresh.written_by(rel, edited, default_branch="trunk", **kwargs) is None


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
        and "an edit" in report["files"][WORKFLOW]
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
    assert report["files"]["REVIEW.md"].startswith("kept; outdated (was 1.0.10)")
    assert "reviewed PR" in report["files"]["REVIEW.md"]
    assert (project / "REVIEW.md").read_text(encoding="utf-8") == older
    (project / "REVIEW.md").write_text(older + "Our own rule.\n", encoding="utf-8")
    assert _init(project)["files"]["REVIEW.md"] == "kept"  # the owner's content: no noise


OLD_EVALS = ".github/workflows/sdlc-evals.yml"
NEW_EVALS = ".github/workflows/sdlc-agent-evals.yml"


def _old_evals() -> str:
    """The evals workflow as a release before 1.0.46 had it, under its old name."""
    text = (TEMPLATE / NEW_EVALS).read_text(encoding="utf-8")
    return text.replace("name: SDLC agent evals\n", "name: SDLC evals\n") + OLDER_YAML


def test_the_renamed_evals_workflow_is_known_by_its_old_name():
    """R45 row 78: the old name stays readable for one release, beside the new one."""
    assert sdlc_init.RENAMED_COPIES == {OLD_EVALS: NEW_EVALS}
    assert NEW_EVALS in sdlc_init.WORKFLOW_FILES and OLD_EVALS not in sdlc_init.WORKFLOW_FILES
    assert not (TEMPLATE / OLD_EVALS).exists()


def test_an_upgrade_replaces_a_pristine_old_evals_workflow_with_the_new_one(project, monkeypatch):
    """R45 row 78: /sdlc-init's upgrade removes a pristine sdlc-evals.yml and installs
    sdlc-agent-evals.yml in its place; a second re-run moves nothing."""
    _manifest_with(monkeypatch, {OLD_EVALS: _old_evals()})
    (project / NEW_EVALS).unlink()
    (project / OLD_EVALS).write_text(_render(OLD_EVALS, _old_evals()), encoding="utf-8")
    report = _init(project)
    assert report["files"][OLD_EVALS].startswith("removed (was 1.0.10)")
    assert "sdlc-agent-evals.yml" in report["files"][OLD_EVALS]
    assert report["files"][NEW_EVALS] == "created"
    assert not (project / OLD_EVALS).exists()
    text = (project / NEW_EVALS).read_text(encoding="utf-8")
    assert "name: SDLC agent evals" in text
    again = _init(project)
    assert OLD_EVALS not in again["files"] and again["files"][NEW_EVALS] == "unchanged"


def test_an_upgrade_keeps_an_edited_old_evals_workflow_and_reports_it(project, monkeypatch):
    """R45 row 78: an edited sdlc-evals.yml is the owner's: kept, reported, and the new file
    waits for it to go, so the suite never runs twice; once it is gone the new file comes."""
    _manifest_with(monkeypatch, {OLD_EVALS: _old_evals()})
    (project / NEW_EVALS).unlink()
    edited = _render(OLD_EVALS, _old_evals()) + "# ours\n"
    (project / OLD_EVALS).write_text(edited, encoding="utf-8")
    report = _init(project)
    assert report["files"][OLD_EVALS].startswith("kept; renamed (edited)")
    assert "sdlc-agent-evals.yml" in report["files"][OLD_EVALS]
    assert report["files"][NEW_EVALS].startswith("not installed: the edited sdlc-evals.yml")
    assert (project / OLD_EVALS).read_text(encoding="utf-8") == edited
    assert not (project / NEW_EVALS).exists()
    (project / OLD_EVALS).unlink()  # the owner moved the edits, or dropped them
    assert _init(project)["files"][NEW_EVALS] == "created"


def test_the_check_script_is_refreshed_like_the_readmes(project, monkeypatch):
    rel = "evals/check.py"
    _manifest_with(monkeypatch, {rel: _older(rel)})
    (project / rel).write_text(_older(rel), encoding="utf-8")
    assert _init(project)["files"][rel] == "refreshed (was 1.0.10)"


def test_the_shipped_manifest_is_well_formed():
    data = json.loads(refresh.MANIFEST.read_text(encoding="utf-8"))
    assert data["schema"] == refresh.SCHEMA
    # R45 row 78: an old name keeps its released hashes for one release
    rels = {*sdlc_init.REFRESHED_COPIES, *sdlc_init.REPORTED_COPIES, *sdlc_init.RENAMED_COPIES}
    for key in ("files", "files_marked"):
        assert set(data[key]) == rels
        for known in data[key].values():
            for digest, version in known.items():
                assert len(digest) == 64 and version.count(".") == 2
    # the history is there: the oldest copies (0.2.x) are recognised, not only today's
    assert any(v.startswith("0.2.") for v in data["files"][README].values())


def _tasks():
    import importlib.util  # noqa: PLC0415

    spec = importlib.util.spec_from_file_location("tasks_r64", ROOT / "tasks.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _git(cwd: Path, *args: str) -> None:
    import subprocess  # noqa: PLC0415

    subprocess.run(
        ["git", "-c", "user.email=o@x", "-c", "user.name=o", *args],
        cwd=cwd,
        check=True,
        capture_output=True,
    )


def test_template_hashes_keeps_the_first_version_and_refuses_a_clone_without_tags(
    tmp_path, monkeypatch
):
    """`python tasks.py template-hashes`: each text keeps the first tag that shipped it, a
    file missing at a tag is skipped, and a clone without tags writes nothing (it would lose
    every release's text)."""
    tasks = _tasks()
    monkeypatch.setattr(sdlc_init, "REFRESHED_COPIES", (README,))
    monkeypatch.setattr(sdlc_init, "REPORTED_COPIES", ("REVIEW.md",))
    old_name = "changes/OLD.md"  # R45 row 78: a name the template no longer has
    monkeypatch.setattr(sdlc_init, "RENAMED_COPIES", {old_name: README})
    root = tmp_path / "fw"
    (root / ".claude-plugin").mkdir(parents=True)
    (root / "template" / "changes").mkdir(parents=True)

    def ship(version: str, readme: str, review: str | None) -> None:
        (root / ".claude-plugin" / "plugin.json").write_text(
            json.dumps({"version": version}), encoding="utf-8"
        )
        (root / "template" / README).write_text(readme, encoding="utf-8")
        if review is not None:
            (root / "template" / "REVIEW.md").write_text(review, encoding="utf-8")

    _git(tmp_path, "init", "-q", str(root))
    ship("1.0.0", "one\n", None)
    (root / "template" / old_name).write_text("old\n", encoding="utf-8")
    _git(root, "add", ".")
    _git(root, "commit", "-q", "-m", "1.0.0")
    with pytest.raises(tasks.NoTagsError):
        tasks.template_hashes(root)
    _git(root, "tag", "v1.0.0")
    ship("1.0.1", "two\n", "review\n")
    (root / "template" / old_name).unlink()  # renamed: gone from the working tree
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "1.0.1")
    _git(root, "tag", "v1.0.1")
    ship("1.0.2", "one\n", "review\n")  # the first text, back in the working tree
    maps = tasks.template_hashes(root)
    readme = maps["files"][README]
    assert readme == {refresh.digest("one\n"): "1.0.0", refresh.digest("two\n"): "1.0.1"}
    assert maps["files"]["REVIEW.md"] == {refresh.digest("review\n"): "1.0.1"}
    # the old name keeps the texts its tags shipped, though the working tree has none
    assert maps["files"][old_name] == {refresh.digest("old\n"): "1.0.0"}
