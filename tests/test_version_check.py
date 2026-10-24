"""``python tasks.py version-check``: a bump to a version taken already fails (ROADMAP R5's race).

Layer 1 (temporary git repositories): a branch that bumps nothing and changes nothing under
``plugin/`` or ``template/`` passes, also when it merges a bump from ``main``; a bump above
``main`` with no tag passes; a bump to a tagged version, or to ``main``'s own version after the
other pull request merged first, fails; the tag is read on ``origin`` when the clone lacks it;
``main`` itself checks nothing, and a clone without ``main`` fails. Two open branches that bump
to one version: the later bump fails and the earlier is told, and a branch built on the other
shares its bump (choice 266). A path added, changed or deleted under ``plugin/`` or
``template/`` since the merge base with ``main`` fails without a version above ``main``'s, as
it runs in Framework checks too (a detached merge commit, ``origin/main`` only); a change
reverted on the branch, one that only ``main`` made, or one a criss-cross merge brings from
``main``, needs none; a push to ``main`` checks nothing; no merge base fails.
"""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import tasks

GIT = ["git", "-c", "user.name=t", "-c", "user.email=t@t", "-c", "init.defaultBranch=main"]


def _git(root: Path, *args: str, date: str | None = None) -> str:
    env = {**os.environ, "GIT_COMMITTER_DATE": date} if date else None
    return subprocess.run(
        [*GIT, *args], cwd=root, check=True, capture_output=True, text=True, env=env
    ).stdout.strip()


def _commit(
    root: Path, files: dict[str, str], message: str = "change", date: str | None = None
) -> None:
    for rel, text in files.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8", newline="\n")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", message, date=date)


def _version(version: str) -> dict[str, str]:
    return {".claude-plugin/plugin.json": json.dumps({"name": "sdlc", "version": version})}


def _repo(tmp_path: Path) -> Path:
    """A ``main`` at plugin 1.0.2, and a branch ``work`` checked out from it."""
    root = tmp_path / "repo"
    root.mkdir()
    _git(root, "init", "-q")
    _commit(root, {**_version("1.0.2"), "plugin/a.py": "a = 1\n"})
    _git(root, "checkout", "-q", "-b", "work")
    return root


def test_a_branch_that_bumps_nothing_and_ships_nothing_passes(tmp_path):
    root = _repo(tmp_path)
    _commit(root, {"docs/x.md": "x\n", "tasks.py": "t = 1\n", "tests/test_a.py": "a = 1\n"})
    assert tasks.version_problems(root) == ([], [])


def test_merging_mains_bump_into_a_branch_is_not_a_bump(tmp_path):
    root = _repo(tmp_path)
    _commit(root, {"docs/x.md": "x\n"})
    _git(root, "checkout", "-q", "main")
    _commit(root, {**_version("1.0.3"), "plugin/b.py": "b = 1\n"})
    _git(root, "checkout", "-q", "work")
    _git(root, "merge", "-q", "--no-edit", "main")
    assert tasks.version_problems(root) == ([], [])


def test_a_bump_above_main_with_no_tag_on_origin_passes(tmp_path):
    root = _repo(tmp_path)
    origin = tmp_path / "origin"
    _git(tmp_path, "clone", "-q", "--bare", str(root), str(origin))
    _git(root, "remote", "add", "origin", str(origin))
    _commit(root, _version("1.0.3"))
    assert tasks.version_problems(root) == ([], [])


def test_a_bump_to_a_tagged_version_fails(tmp_path):
    root = _repo(tmp_path)
    _git(root, "tag", "v1.0.3", "main")
    _commit(root, _version("1.0.3"))
    failures, _ = tasks.version_problems(root)
    assert failures == [
        "the branch bumps to 1.0.3, and v1.0.3 is already tagged: "
        "take the next free patch (python tasks.py next-free)"
    ]


def test_the_tag_is_read_on_origin_when_the_clone_lacks_it(tmp_path):
    root = _repo(tmp_path)
    origin = tmp_path / "origin"
    _git(tmp_path, "clone", "-q", "--bare", str(root), str(origin))
    _git(origin, "tag", "v1.0.3", "main")
    _git(root, "remote", "add", "origin", str(origin))
    _commit(root, _version("1.0.3"))
    failures, _ = tasks.version_problems(root)
    assert len(failures) == 1 and "v1.0.3 is already tagged" in failures[0]


def test_the_second_pull_request_to_one_version_fails_after_the_first_merged(tmp_path):
    root = _repo(tmp_path)
    _commit(root, {**_version("1.0.3"), "plugin/a.py": "a = 2\n"}, "work: 1.0.3")
    _git(root, "checkout", "-q", "main")
    _commit(root, {**_version("1.0.3"), "plugin/b.py": "b = 1\n"}, "other: 1.0.3")
    _git(root, "checkout", "-q", "work")
    _git(root, "merge", "-q", "--no-edit", "main")  # clean: both sides hold 1.0.3
    failures, _ = tasks.version_problems(root)
    assert failures == [
        "the branch bumps to 1.0.3, not above main's 1.0.3: "
        "take the next free patch (python tasks.py next-free)"
    ]


def test_an_unanswered_tag_lookup_is_reported_not_failed(tmp_path):
    root = _repo(tmp_path)
    _commit(root, _version("1.0.3"))
    assert tasks.version_problems(root) == (
        [],
        ["v1.0.3's tag not checked: no tag here and origin did not answer"],
    )


def test_main_itself_checks_nothing_and_a_repository_without_main_fails(tmp_path):
    root = _repo(tmp_path)
    _git(root, "checkout", "-q", "main")
    assert tasks.version_problems(root) == ([], [])
    _git(root, "branch", "-q", "-m", "main", "trunk")
    failures, reports = tasks.version_problems(root)
    assert failures == [
        "cannot compare the branch with main: no main branch: neither origin/main nor main exists"
    ]
    assert reports == []


def _two_bumps(tmp_path: Path, work_date: str, other_date: str) -> Path:
    """``work`` and ``other``, both open from ``main``, both bumping to 1.0.3."""
    root = _repo(tmp_path)
    _commit(root, {**_version("1.0.3"), "plugin/a.py": "a = 2\n"}, "work: 1.0.3", work_date)
    _git(root, "checkout", "-q", "-b", "other", "main")
    _commit(root, {**_version("1.0.3"), "plugin/b.py": "b = 1\n"}, "other: 1.0.3", other_date)
    _git(root, "checkout", "-q", "work")
    return root


def test_the_later_of_two_open_bumps_to_one_version_fails(tmp_path):
    root = _two_bumps(tmp_path, "2026-10-23T11:00:00Z", "2026-10-23T10:00:00Z")
    failures, reports = tasks.version_problems(root)
    assert failures == [
        "the branch bumps to 1.0.3, which other took first: "
        "take the next free patch (python tasks.py next-free)"
    ]
    assert reports == []


def test_the_earlier_of_two_open_bumps_is_told_and_passes(tmp_path):
    root = _two_bumps(tmp_path, "2026-10-23T10:00:00Z", "2026-10-23T11:00:00Z")
    failures, reports = tasks.version_problems(root)
    assert failures == []
    assert reports[0] == "1.0.3 is also taken by other, later: that branch renumbers"


def test_a_branch_built_on_this_one_shares_its_bump(tmp_path):
    root = _repo(tmp_path)
    _commit(root, {**_version("1.0.3"), "plugin/a.py": "a = 2\n"}, "work: 1.0.3")
    _git(root, "checkout", "-q", "-b", "stacked")
    _commit(root, {"docs/x.md": "x\n"}, "stacked: docs")
    _git(root, "checkout", "-q", "work")
    failures, reports = tasks.version_problems(root)
    assert failures == [] and not any("also taken" in line for line in reports)
    _git(root, "checkout", "-q", "stacked")
    failures, reports = tasks.version_problems(root)
    assert failures == [] and not any("also taken" in line for line in reports)


# --- a change under plugin/ or template/ needs a version above main's -------------------------

NO_BUMP = (
    "under plugin/ or template/ with .claude-plugin/plugin.json at 1.0.2, not above main's "
    "1.0.2: bump it and the marketplace entry to the next free patch (python tasks.py next-free)"
)


def test_a_plugin_change_without_a_bump_fails(tmp_path):
    root = _repo(tmp_path)
    _commit(root, {"plugin/a.py": "a = 2\n"})
    assert tasks.version_problems(root) == ([f"the branch changes plugin/a.py {NO_BUMP}"], [])


def test_a_template_file_added_without_a_bump_fails(tmp_path):
    root = _repo(tmp_path)
    _commit(root, {"template/.claude/settings.json": "{}\n", "docs/x.md": "x\n"})
    assert tasks.version_problems(root) == (
        [f"the branch changes template/.claude/settings.json {NO_BUMP}"],
        [],
    )


def test_a_plugin_file_deleted_or_moved_out_without_a_bump_fails(tmp_path):
    root = _repo(tmp_path)
    (root / "docs").mkdir()
    _git(root, "mv", "plugin/a.py", "docs/a.py")
    _git(root, "commit", "-q", "-m", "move out")
    assert tasks.version_problems(root) == ([f"the branch changes plugin/a.py {NO_BUMP}"], [])


def test_more_than_three_paths_are_counted(tmp_path):
    root = _repo(tmp_path)
    _commit(root, {f"plugin/m{n}.py": "m = 1\n" for n in range(5)})
    failures, _ = tasks.version_problems(root)
    assert failures[0].startswith(
        "the branch changes plugin/m0.py, plugin/m1.py, plugin/m2.py and 2 more under plugin/"
    )


def test_a_plugin_change_with_a_bump_above_main_passes(tmp_path):
    root = _repo(tmp_path)
    _commit(root, {**_version("1.0.3"), "plugin/a.py": "a = 2\n", "template/t.md": "t\n"})
    failures, _ = tasks.version_problems(root)
    assert failures == []


def test_a_plugin_change_reverted_on_the_branch_needs_no_bump(tmp_path):
    root = _repo(tmp_path)
    _commit(root, {"plugin/a.py": "a = 2\n"})
    _commit(root, {"plugin/a.py": "a = 1\n"})
    assert tasks.version_problems(root) == ([], [])


def test_a_plugin_change_only_main_made_needs_no_bump_on_the_branch(tmp_path):
    root = _repo(tmp_path)
    _commit(root, {"docs/x.md": "x\n"})
    _git(root, "checkout", "-q", "main")
    _commit(root, {"plugin/b.py": "b = 1\n"})  # main's own, unbumped (#369's shape)
    _git(root, "checkout", "-q", "work")
    assert tasks.version_problems(root) == ([], [])
    _git(root, "merge", "-q", "--no-edit", "main")
    assert tasks.version_problems(root) == ([], [])


def test_a_plugin_change_still_needs_its_own_bump_after_main_bumped(tmp_path):
    root = _repo(tmp_path)
    _commit(root, {"plugin/a.py": "a = 2\n"})
    _git(root, "checkout", "-q", "main")
    _commit(root, {**_version("1.0.3"), "plugin/b.py": "b = 1\n"})
    _git(root, "checkout", "-q", "work")
    _git(root, "merge", "-q", "--no-edit", "main")
    failures, _ = tasks.version_problems(root)
    assert failures == [
        "the branch changes plugin/a.py under plugin/ or template/ with "
        ".claude-plugin/plugin.json at 1.0.3, not above main's 1.0.3: bump it and the "
        "marketplace entry to the next free patch (python tasks.py next-free)"
    ]


def _as_framework_checks(root: Path) -> None:
    """The clone as Framework checks has it: ``main`` only as ``origin/main``, ``HEAD``
    detached at the pull request's merge commit into it."""
    main = _git(root, "rev-parse", "main")
    _git(root, "update-ref", "refs/remotes/origin/main", main)
    _git(root, "checkout", "-q", "--detach", "main")
    _git(root, "merge", "-q", "--no-ff", "--no-edit", "work")
    _git(root, "branch", "-q", "-D", "main", "work")


def test_framework_checks_shape_fails_an_unbumped_plugin_change(tmp_path):
    root = _repo(tmp_path)
    _commit(root, {"plugin/a.py": "a = 2\n"})
    _as_framework_checks(root)
    assert tasks.version_problems(root) == (
        [
            "the branch changes plugin/a.py under plugin/ or template/ with "
            ".claude-plugin/plugin.json at 1.0.2, not above origin/main's 1.0.2: bump it and "
            "the marketplace entry to the next free patch (python tasks.py next-free)"
        ],
        [],
    )


def test_framework_checks_shape_passes_a_bumped_plugin_change(tmp_path):
    root = _repo(tmp_path)
    _commit(root, {**_version("1.0.3"), "plugin/a.py": "a = 2\n"})
    _as_framework_checks(root)
    failures, _ = tasks.version_problems(root)
    assert failures == []


def test_no_merge_base_with_main_fails_clearly(tmp_path):
    root = _repo(tmp_path)
    _git(root, "checkout", "-q", "--orphan", "alone")
    _commit(root, {**_version("1.0.2"), "docs/x.md": "x\n"})
    failures, reports = tasks.version_problems(root)
    assert len(failures) == 1 and reports == []
    assert failures[0].startswith("cannot compare the branch with main: HEAD has no merge base")


def test_task_version_check_fails_when_git_cannot_be_read(monkeypatch, capsys):
    def broken(_root):
        raise subprocess.CalledProcessError(128, ["git", "merge-base"])

    monkeypatch.setattr(tasks, "version_problems", broken)
    assert tasks.task_version_check() == 1
    assert "version-check: FAIL cannot read git:" in capsys.readouterr().out


def test_a_file_moved_into_plugin_without_a_bump_fails(tmp_path):
    root = _repo(tmp_path)
    _commit(root, {"docs/b.py": "b = 1\n"})
    _git(root, "checkout", "-q", "main")
    _git(root, "merge", "-q", "work")
    _git(root, "checkout", "-q", "-B", "work")
    _git(root, "mv", "docs/b.py", "plugin/b.py")
    _git(root, "commit", "-q", "-m", "move in")
    assert tasks.version_problems(root) == ([f"the branch changes plugin/b.py {NO_BUMP}"], [])


def test_an_unreadable_version_fails_a_plugin_change(tmp_path):
    root = _repo(tmp_path)
    _commit(root, {".claude-plugin/plugin.json": "{", "plugin/a.py": "a = 2\n"})
    assert tasks.version_problems(root) == (
        [".claude-plugin/plugin.json holds no readable version at HEAD"],
        [],
    )
    _git(root, "checkout", "-q", "main")
    _commit(root, {".claude-plugin/plugin.json": "{"})
    _git(root, "checkout", "-q", "-B", "work")
    _commit(root, {"plugin/a.py": "a = 3\n"})
    failures, _ = tasks.version_problems(root)
    assert failures[0].startswith(
        "the branch changes plugin/a.py under plugin/ or template/ with "
        ".claude-plugin/plugin.json at no readable version, not above main's none readable"
    )


def test_a_push_to_main_as_framework_checks_has_it_checks_nothing(tmp_path):
    root = _repo(tmp_path)
    _git(root, "checkout", "-q", "main")
    _commit(root, {"plugin/a.py": "a = 2\n"})  # an unbumped change already on main
    _git(root, "update-ref", "refs/remotes/origin/main", _git(root, "rev-parse", "main"))
    _git(root, "checkout", "-q", "--detach", "main")
    _git(root, "branch", "-q", "-D", "main", "work")
    assert tasks.version_problems(root) == ([], [])


def test_a_criss_cross_merge_counts_none_of_mains_changes(tmp_path):
    root = _repo(tmp_path)
    _commit(root, {"docs/x.md": "x\n"}, "b1")
    _git(root, "checkout", "-q", "main")
    _commit(root, {"plugin/a.py": "a = 2\n"}, "m0: main's own, unbumped")
    m0 = _git(root, "rev-parse", "HEAD")
    _git(root, "merge", "-q", "--no-ff", "--no-edit", "work")  # main merges b1
    _git(root, "checkout", "-q", "work")
    _git(root, "merge", "-q", "--no-ff", "--no-edit", m0)  # work merges m0, not main's tip
    assert len(_git(root, "merge-base", "--all", "main", "HEAD").split()) == 2
    assert tasks.version_problems(root) == ([], [])


def test_an_unbumped_branch_above_main_still_meets_the_tag_check(tmp_path):
    root = _repo(tmp_path)
    _git(root, "checkout", "-q", "main")
    _commit(root, _version("1.0.3"))
    _git(root, "tag", "v1.0.3")
    _git(root, "checkout", "-q", "work")
    _git(root, "merge", "-q", "--no-edit", "main")
    _commit(root, {"plugin/a.py": "a = 2\n"})
    _git(root, "checkout", "-q", "main")
    _commit(root, _version("1.0.2"))  # main lowers its version
    _git(root, "checkout", "-q", "work")
    failures, _ = tasks.version_problems(root)
    assert failures == [
        "the branch bumps to 1.0.3, and v1.0.3 is already tagged: "
        "take the next free patch (python tasks.py next-free)"
    ]
