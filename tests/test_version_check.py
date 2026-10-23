"""``python tasks.py version-check``: a bump to a version taken already fails (ROADMAP R5's race).

Layer 1 (temporary git repositories): a branch that bumps nothing passes, also when it merges a
bump from ``main``; a bump above ``main`` with no tag passes; a bump to a tagged version, or to
``main``'s own version after the other pull request merged first, fails; the tag is read on
``origin`` when the clone lacks it; nothing is checked without a ``main``.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import tasks

GIT = ["git", "-c", "user.name=t", "-c", "user.email=t@t", "-c", "init.defaultBranch=main"]


def _git(root: Path, *args: str) -> str:
    return subprocess.run(
        [*GIT, *args], cwd=root, check=True, capture_output=True, text=True
    ).stdout.strip()


def _commit(root: Path, files: dict[str, str], message: str = "change") -> None:
    for rel, text in files.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8", newline="\n")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", message)


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


def test_a_branch_that_bumps_nothing_passes(tmp_path):
    root = _repo(tmp_path)
    _commit(root, {"plugin/a.py": "a = 2\n"})
    assert tasks.version_problems(root) == ([], [])


def test_merging_mains_bump_into_a_branch_is_not_a_bump(tmp_path):
    root = _repo(tmp_path)
    _commit(root, {"plugin/a.py": "a = 2\n"})
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


def test_main_itself_and_a_repository_without_main_check_nothing(tmp_path):
    root = _repo(tmp_path)
    _git(root, "checkout", "-q", "main")
    assert tasks.version_problems(root) == ([], [])
    _git(root, "branch", "-q", "-m", "main", "trunk")
    failures, reports = tasks.version_problems(root)
    assert failures == [] and reports[0].startswith("not checked: no main branch")
