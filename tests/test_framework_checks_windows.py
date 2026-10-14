"""The Windows selector of this repository's own checks (workflow framework-checks.yml;
.github/scripts/framework_checks_windows.py): on a pull request the Windows job is skipped
only when every changed path is documentation; every other event, and every doubt, runs it
(the batch ci revision, 10.2)."""

from __future__ import annotations

import importlib.util
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / ".github" / "scripts" / "framework_checks_windows.py"
spec = importlib.util.spec_from_file_location("framework_checks_windows", SCRIPT)
selector = importlib.util.module_from_spec(spec)
spec.loader.exec_module(selector)


def git(cwd: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=cwd, check=True, capture_output=True, text=True, encoding="utf-8"
    ).stdout


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


@pytest.fixture
def repo(tmp_path):
    work = tmp_path / "work"
    git(tmp_path, "init", "-q", "-b", "main", str(work))
    git(work, "config", "user.email", "owner@example.com")
    git(work, "config", "user.name", "Owner")
    git(work, "config", "core.autocrlf", "false")
    write(work / "README.md", "# readme\n")
    write(work / "plugin" / "hooks" / "guard.py", "print('guard')\n")
    write(work / "docs" / "notes" / "1.md", "note 1\n")
    git(work, "add", ".")
    git(work, "commit", "-q", "-m", "base")
    git(work, "checkout", "-q", "-b", "pr")
    return work


def merge_into_main(work: Path) -> None:
    """GitHub's checkout of a pull request: a merge commit whose first parent is the base,
    after the base has moved on with a code change of its own."""
    git(work, "commit", "-q", "-am", "the pull request", "--allow-empty")
    git(work, "checkout", "-q", "main")
    write(work / "plugin" / "gate" / "checks.py", "print('base moved')\n")
    git(work, "add", ".")
    git(work, "commit", "-q", "-m", "base moved")
    git(work, "merge", "-q", "--no-ff", "--no-edit", "pr")


@pytest.mark.parametrize(
    ("paths", "windows"),
    [
        (["docs/notes/1.md"], False),
        (["docs/decisions/index.md", "HANDOFF.md", "README.md"], False),
        (["docs/notes/1.md", "tests/test_hooks.py"], True),
        (["plugin/hooks/guard.py"], True),
        (["CLAUDE.md"], True),  # a root guardrail is not documentation here
        (["REVIEW.md"], True),
        (["changes/0005-x/intent.md"], True),  # the owner kept changes/** out (C4)
        (["plugin/docs/x.md"], True),  # docs/ only at the root
        (["docs"], True),  # a file named docs, not the folder
        (["sub/README.md"], True),
        ([".github/workflows/framework-checks.yml"], True),
    ],
)
def test_a_pull_request_skips_windows_only_when_every_path_is_documentation(paths, windows):
    assert selector.decide("pull_request", paths)[0] is windows


@pytest.mark.parametrize("event", ["push", "workflow_dispatch", "schedule", ""])
def test_every_other_event_runs_windows_whatever_changed(event):
    assert selector.decide(event, ["docs/notes/1.md"]) == (
        True,
        f"a {event or 'unnamed'} event runs every platform",
    )


def test_a_doubt_runs_windows():
    assert selector.decide("pull_request", None) == (True, "the changed paths could not be read")
    assert selector.decide("pull_request", []) == (True, "no changed path was read")


def test_a_documentation_only_merge_skips_windows_although_the_base_moved(repo):
    write(repo / "docs" / "notes" / "2.md", "note 2\n")
    write(repo / "HANDOFF.md", "# handoff\n")
    git(repo, "add", ".")
    merge_into_main(repo)
    paths = selector.changed_paths(repo)
    assert sorted(paths) == ["HANDOFF.md", "docs/notes/2.md"]  # not the base's checks.py
    assert selector.decide("pull_request", paths)[0] is False


def test_moving_code_into_docs_runs_windows(repo):
    git(repo, "mv", "plugin/hooks/guard.py", "docs/guard.py")
    merge_into_main(repo)
    paths = selector.changed_paths(repo)
    assert sorted(paths) == ["docs/guard.py", "plugin/hooks/guard.py"]
    assert selector.decide("pull_request", paths)[0] is True


def test_a_head_that_is_not_a_merge_commit_reads_no_paths(repo):
    write(repo / "docs" / "notes" / "2.md", "note 2\n")
    git(repo, "add", ".")
    git(repo, "commit", "-q", "-m", "docs only, no merge")
    assert selector.changed_paths(repo) is None


def test_the_outputs_are_written_for_the_workflow(repo, tmp_path, monkeypatch, capsys):
    write(repo / "README.md", "# readme, edited\n")
    git(repo, "add", ".")
    merge_into_main(repo)
    out_file = tmp_path / "github_output"
    monkeypatch.setenv("GITHUB_OUTPUT", str(out_file))
    assert selector.main(["--root", str(repo), "--event", "pull_request"]) == 0
    written = out_file.read_text(encoding="utf-8")
    assert "windows=false\n" in written
    assert "reason=all 1 changed path(s) are documentation\n" in written
    assert "windows=false" in capsys.readouterr().out
    out_file.unlink()
    assert selector.main(["--root", str(repo), "--event", "push"]) == 0
    assert out_file.read_text(encoding="utf-8").startswith("windows=true\n")


def test_the_event_defaults_to_the_runner_s_event_name(repo, monkeypatch, capsys):
    monkeypatch.delenv("GITHUB_OUTPUT", raising=False)
    monkeypatch.setenv("GITHUB_EVENT_NAME", "push")
    assert selector.main(["--root", str(repo)]) == 0
    assert capsys.readouterr().out.startswith("windows=true\nreason=a push event")
