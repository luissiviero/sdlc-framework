"""``python tasks.py next-free``: the next free numbers read from git (ROADMAP R65, part 1).

Layer 1 (temporary git repositories): the numbers ``main`` takes, the ones each branch ahead of
it takes above ``main`` with the branch named, ``origin/main`` read before a local ``main``,
an older plugin version on a stale branch not counted, nothing read without a ``main``; a
choice held only by a branch named as the next on main, since main's choices run without a gap
(choice 267). The
task runs on this repository in the PR body's first live use, not here: a CI checkout of a pull
request may hold neither ``main`` nor ``origin/main``.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

import tasks

GIT = ["git", "-c", "user.name=t", "-c", "user.email=t@t", "-c", "init.defaultBranch=main"]


def _git(root: Path, *args: str) -> str:
    return subprocess.run(
        [*GIT, *args], cwd=root, check=True, capture_output=True, text=True
    ).stdout.strip()


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def _commit(root: Path, files: dict[str, str], message: str = "docs") -> str:
    for rel, text in files.items():
        _write(root / rel, text)
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", message)
    return _git(root, "rev-parse", "HEAD")


def _version(version: str) -> str:
    return json.dumps({"name": "sdlc", "version": version})


def _repo(tmp_path: Path) -> Path:
    """A ``main`` that takes choices 1 to 3, R1 and R2, notes 1 and 2, decision 1 and 1.0.2."""
    root = tmp_path / "repo"
    root.mkdir()
    _git(root, "init", "-q")
    _commit(
        root,
        {
            "docs/progress/session-3.md": "## Choices made\n1. One.\n2. Two.\n## Left\n7. x\n",
            "docs/PROGRESS.md": "## The owner's decision (2026-10-22)\n3. **Three**.\n",
            "docs/ROADMAP.md": "## Candidates\n| R1 | a |\n## Done\n| R2 | b |\n",
            "docs/notes/1.md": "x\n",
            "docs/notes/2.md": "x\n",
            "docs/notes/index.md": "x\n",
            "docs/decisions/1.md": "x\n",
            ".claude-plugin/plugin.json": _version("1.0.2"),
        },
    )
    return root


def test_main_alone_gives_one_above_each_highest(tmp_path):
    root = _repo(tmp_path)
    base, free, above, read = tasks.next_free(root)
    assert base.startswith("main at ")
    assert free == {
        "choice": "4",
        "candidate": "R3",
        "note": "3",
        "decision": "2",
        "patch": "1.0.3",
    }
    assert (above, read) == ([], 0)


def test_each_number_taken_above_main_names_its_branch(tmp_path):
    root = _repo(tmp_path)
    _git(root, "checkout", "-q", "-b", "claude/one")
    _commit(
        root,
        {
            "docs/PROGRESS.md": "## The owner's decision (2026-10-23)\n4. **Four**.\n",
            "docs/progress/2026-10-22-old.md": "## The owner's decision\n3. **Three**.\n",
            "docs/notes/3.md": "x\n",
            ".claude-plugin/plugin.json": _version("1.0.3"),
        },
    )
    _git(root, "checkout", "-q", "main")
    _git(root, "checkout", "-q", "-b", "claude/two")
    _commit(
        root,
        {
            "docs/PROGRESS.md": "## The owner's decision (2026-10-23)\n4. **Four again**.\n",
            "docs/ROADMAP.md": "## Candidates\n| R1 | a |\n| R3 | c |\n## Done\n| R2 | b |\n",
            "docs/decisions/2.md": "x\n",
        },
    )
    _git(root, "checkout", "-q", "main")
    _git(root, "branch", "behind")
    _, free, above, read = tasks.next_free(root)
    assert free == {
        "choice": "5",
        "candidate": "R4",
        "note": "4",
        "decision": "3",
        "patch": "1.0.4",
    }
    assert above == [
        ("choice", "4", ["claude/one", "claude/two"]),
        ("candidate", "R3", ["claude/two"]),
        ("note", "3", ["claude/one"]),
        ("decision", "2", ["claude/two"]),
        ("patch", "1.0.3", ["claude/one"]),
    ]
    assert read == 2


def test_origin_main_is_read_before_main_and_a_fetched_branch_loses_its_remote(tmp_path):
    root = _repo(tmp_path)
    first = _git(root, "rev-parse", "HEAD")
    newer = _commit(root, {"docs/notes/3.md": "x\n"})
    _git(root, "update-ref", "refs/remotes/origin/main", newer)
    _git(root, "update-ref", "refs/remotes/origin/HEAD", newer)
    _git(root, "reset", "-q", "--hard", first)
    _git(root, "checkout", "-q", "-b", "feature", newer)
    feature = _commit(root, {"docs/notes/4.md": "x\n"})
    _git(root, "update-ref", "refs/remotes/origin/feature", feature)
    base, free, above, read = tasks.next_free(root)
    assert base == f"origin/main at {newer[:7]}"
    assert free["note"] == "5"
    assert above == [("note", "4", ["feature"])]
    assert read == 1


def test_a_branch_and_its_fetched_copy_at_two_commits_are_named_once(tmp_path):
    root = _repo(tmp_path)
    _git(root, "checkout", "-q", "-b", "claude/one")
    pushed = _commit(root, {"docs/notes/3.md": "x\n"})
    _git(root, "update-ref", "refs/remotes/origin/claude/one", pushed)
    _commit(root, {"docs/notes/4.md": "x\n"})
    _, _, above, read = tasks.next_free(root)
    assert above == [("note", "3", ["claude/one"]), ("note", "4", ["claude/one"])]
    assert read == 2


def test_an_older_version_on_a_stale_branch_is_not_taken(tmp_path):
    root = _repo(tmp_path)
    old = _git(root, "rev-parse", "HEAD")
    _commit(root, {".claude-plugin/plugin.json": _version("1.0.9")})
    _git(root, "checkout", "-q", "-b", "stale", old)
    _commit(root, {"docs/notes/9.md": "x\n"})
    _git(root, "checkout", "-q", "main")
    _, free, above, _ = tasks.next_free(root)
    assert free["patch"] == "1.0.10"
    assert above == [("note", "9", ["stale"])]


def test_a_detached_head_ahead_of_main_is_read(tmp_path):
    root = _repo(tmp_path)
    _git(root, "checkout", "-q", "--detach")
    _commit(root, {"docs/decisions/5.md": "x\n"})
    _, free, above, _ = tasks.next_free(root)
    assert free["decision"] == "6"
    assert above == [("decision", "5", ["HEAD"])]


def test_without_main_nothing_is_read(tmp_path, monkeypatch, capsys):
    root = tmp_path / "repo"
    root.mkdir()
    _git(root, "init", "-q", "-b", "trunk")
    _commit(root, {"docs/notes/1.md": "x\n"})
    with pytest.raises(LookupError):
        tasks.next_free(root)
    monkeypatch.setattr(tasks, "ROOT", root)
    assert tasks.task_next_free() == 1
    assert "neither origin/main nor main exists" in capsys.readouterr().err


def test_the_task_prints_each_kind_and_each_branch(tmp_path, monkeypatch, capsys):
    root = _repo(tmp_path)
    _git(root, "checkout", "-q", "-b", "claude/one")
    _commit(root, {"docs/notes/3.md": "x\n"})
    monkeypatch.setattr(tasks, "ROOT", root)
    assert tasks.main(["next-free"]) == 0
    out = capsys.readouterr().out.splitlines()
    assert out[0].startswith("next-free: read on main at ")
    assert out[0].endswith(" and 1 branch(es) ahead of it, as last fetched")
    assert out[1:] == [
        "  choice     4",
        "  candidate  R3",
        "  note       4",
        "  decision   2",
        "  patch      1.0.3",
        "next-free: taken above main:",
        "  note 3: claude/one",
        "next-free: nothing is reserved (choice 184); git fetch origin reads the newest state",
    ]


def test_a_choice_held_only_by_a_branch_is_named_as_the_next_on_main(tmp_path):
    root = _repo(tmp_path)
    _git(root, "checkout", "-q", "-b", "claude/one")
    _commit(root, {"docs/PROGRESS.md": "## The owner's decision (2026-10-23)\n4. **Four**.\n"})
    _git(root, "checkout", "-q", "main")
    _, free, above, _ = tasks.next_free(root)
    on_main = tasks.next_on_main(root)
    assert (free["choice"], on_main["choice"]) == ("5", "4")
    assert tasks.gap_notes(free, on_main, above) == [
        "choice 4 is next on main and held by claude/one: main's choices run without a gap, "
        "so a PR that merges before them takes 4, one that merges after them 5; "
        "the later renumbers"
    ]


def test_no_gap_note_when_the_next_on_main_is_free(tmp_path):
    root = _repo(tmp_path)
    _git(root, "checkout", "-q", "-b", "claude/one")
    _commit(root, {"docs/notes/3.md": "x\n"})
    _git(root, "checkout", "-q", "main")
    _, free, above, _ = tasks.next_free(root)
    assert tasks.gap_notes(free, tasks.next_on_main(root), above) == []
