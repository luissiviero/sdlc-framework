"""Layer-1 tests for plugin/detect/runbooks.py: the pre-approved runbooks of the 3sigma tier
(build guide step 37.4; decision 14; p.45 "the agent quarantines the flaky test or opens a
revert PR, and the review gate decides"). Each test runs against a temporary git repository
with a bare ``origin``; the GitHub client is a fake that records the calls, so nothing leaves
the machine."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest
from detect import runbooks

NODE = "tests/test_app.py::test_two"
PR = {"ok": True, "url": "https://x/pr/1", "number": 1, "route": "fake", "created": True}
TEST_FILE = (
    "from app import VALUE\n\n\ndef test_one():\n    assert VALUE\n\n\n"
    "def test_two():\n    assert True\n"
)


def git(cwd: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=cwd, capture_output=True, text=True, check=True, encoding="utf-8"
    ).stdout


def commit(root: Path, files: dict[str, str], message: str) -> str:
    for rel, text in files.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(text.encode("utf-8"))
    git(root, "add", "--", *files)
    git(root, "commit", "-q", "-m", message)
    return git(root, "rev-parse", "HEAD").strip()


def make_repo(tmp_path: Path, files: dict[str, str], *, remote: bool = True) -> Path:
    root = tmp_path / "proj"
    root.mkdir()
    git(root, "init", "-q", "-b", "main")
    git(root, "config", "user.email", "owner@example.com")
    git(root, "config", "user.name", "Owner")
    commit(root, files, "initial")
    if remote:
        bare = tmp_path / "origin.git"
        git(tmp_path, "init", "-q", "--bare", "-b", "main", str(bare))
        git(root, "remote", "add", "origin", str(bare))
        git(root, "push", "-q", "-u", "origin", "main")
        git(root, "symbolic-ref", "refs/remotes/origin/HEAD", "refs/remotes/origin/main")
    return root


def push(root: Path) -> None:
    git(root, "push", "-q", "origin", "main")


def bare(root: Path) -> Path:
    return root.parent / "origin.git"


def remote_show(root: Path, branch: str, rel: str) -> str:
    return git(bare(root), "show", f"refs/heads/{branch}:{rel}")


def remote_has(root: Path, branch: str) -> bool:
    return bool(git(bare(root), "branch", "--list", branch).strip())


def current(root: Path) -> str:
    return git(root, "rev-parse", "--abbrev-ref", "HEAD").strip()


def clean(root: Path) -> bool:
    return git(root, "status", "--porcelain").strip() == ""


class FakeGitHub:
    def __init__(self) -> None:
        self.calls: list[tuple[str, tuple[Any, ...], dict[str, Any]]] = []
        self.open_pr: dict[str, Any] | None = None

    def create_pr(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        self.calls.append(("create_pr", args, kwargs))
        return dict(PR)

    def find_open_pr(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        self.calls.append(("find_open_pr", args, kwargs))
        if self.open_pr:
            return {"ok": True, "route": "fake", **self.open_pr}
        return {"ok": True, "route": "fake", "number": None, "url": None, "html_url": None}

    def ensure_label(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        self.calls.append(("ensure_label", args, kwargs))
        return {"ok": True, "route": "fake", "label": args[1], "created": True}

    def set_labels(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        self.calls.append(("set_labels", args, kwargs))
        return {"ok": True, "route": "fake", "added": list(args[2]), "removed": list(args[3])}

    def named(self, name: str) -> list[tuple[tuple[Any, ...], dict[str, Any]]]:
        return [(a, k) for n, a, k in self.calls if n == name]


@pytest.fixture
def gh(monkeypatch) -> FakeGitHub:
    fake = FakeGitHub()
    for name in ("create_pr", "find_open_pr", "ensure_label", "set_labels"):
        monkeypatch.setattr(runbooks.github, name, getattr(fake, name))
    return fake


@pytest.fixture
def project(tmp_path) -> Path:
    return make_repo(tmp_path, {"app.py": "VALUE = 1\n", "tests/test_app.py": TEST_FILE})


# --- revert-pr ------------------------------------------------------------------------------
def test_revert_of_a_plain_commit_opens_the_labelled_pr_and_comes_back(project, gh):
    sha = commit(project, {"app.py": "VALUE = 2\n"}, "change the value")
    push(project)
    out = runbooks.revert_pr(
        project, "0007", {"sha": sha}, incident_pr_url="https://x/pr/9", repo="o/r"
    )
    branch = f"sdlc/0007/revert-{sha[:7]}"
    assert (out.status, out.branch, out.pr_url, out.pr_number) == ("ran", branch, PR["url"], 1)
    assert current(project) == "main" and clean(project)
    assert (project / "app.py").read_text() == "VALUE = 2\n"  # main is untouched
    assert remote_show(project, branch, "app.py") == "VALUE = 1\n"
    subject = git(bare(project), "log", "-1", "--format=%s", branch).strip()
    assert subject == 'Revert "change the value"'
    assert out.commit == git(bare(project), "rev-parse", branch).strip()
    [(args, kwargs)] = gh.named("create_pr")
    repo, base, head, title, body = args
    assert (repo, base, head, title) == ("o/r", "main", branch, "revert(0007): change the value")
    assert kwargs["draft"] is False
    assert body == (
        "Runbook revert-pr of incident 0007 (https://x/pr/9). "
        f"Reverts {sha} (change the value). The review gate decides: merge to apply, "
        "close to drop. Nothing merges by itself (decision 14)."
    )
    assert gh.named("ensure_label")[0][0][:2] == ("o/r", "incident")
    assert gh.named("set_labels")[0][0] == ("o/r", 1, ["incident"], [])


def test_revert_of_a_merge_commit_uses_the_first_parent(project, gh):
    git(project, "checkout", "-q", "-b", "feature")
    commit(project, {"feature.py": "ON = True\n"}, "add a feature")
    git(project, "checkout", "-q", "main")
    git(project, "merge", "-q", "--no-ff", "feature", "-m", "Merge the feature")
    merge = git(project, "rev-parse", "HEAD").strip()
    push(project)
    out = runbooks.revert_pr(project, "0007", {"sha": merge}, repo="o/r")
    assert out.status == "ran", out.reason
    branch = f"sdlc/0007/revert-{merge[:7]}"
    files = git(bare(project), "ls-tree", "--name-only", branch).split()
    assert "feature.py" not in files and "app.py" in files
    assert current(project) == "main" and (project / "feature.py").is_file()


def test_revert_refuses_a_sha_not_on_the_default_branch(project, gh):
    git(project, "checkout", "-q", "-b", "side")
    side = commit(project, {"app.py": "VALUE = 5\n"}, "a side commit")
    git(project, "checkout", "-q", "main")
    out = runbooks.revert_pr(project, "0007", {"sha": side}, repo="o/r")
    assert out.status == "failed" and "not on the default branch" in out.reason
    assert gh.calls == [] and current(project) == "main"
    bad = runbooks.revert_pr(project, "0007", {"sha": "not-a-sha"}, repo="o/r")
    assert bad.status == "failed" and "hexadecimal" in bad.reason
    unknown = runbooks.revert_pr(project, "0007", {"sha": "deadbeef" * 5}, repo="o/r")
    assert unknown.status == "failed" and "not a commit" in unknown.reason


def test_a_conflicting_revert_is_aborted_and_leaves_the_tree_clean(project, gh):
    first = commit(project, {"app.py": "VALUE = 2\n"}, "two")
    commit(project, {"app.py": "VALUE = 3\n"}, "three")
    push(project)
    out = runbooks.revert_pr(project, "0007", {"sha": first}, repo="o/r")
    assert out.status == "failed"
    assert out.reason == "revert conflicts: app.py"
    assert current(project) == "main" and clean(project)
    assert not (project / ".git" / "REVERT_HEAD").exists()
    branch = f"sdlc/0007/revert-{first[:7]}"
    assert git(project, "branch", "--list", branch).strip() == ""
    assert not remote_has(project, branch) and gh.named("create_pr") == []


def test_a_second_revert_run_reuses_the_branch_and_the_open_pr(project, gh):
    sha = commit(project, {"app.py": "VALUE = 2\n"}, "change the value")
    push(project)
    first = runbooks.revert_pr(project, "0007", {"sha": sha}, repo="o/r")
    branch = first.branch
    assert first.status == "ran"
    # the PR creation failed last time: the branch is reused, the revert not repeated
    again = runbooks.revert_pr(project, "0007", {"sha": sha}, repo="o/r")
    assert again.status == "ran" and again.commit == first.commit
    assert git(bare(project), "rev-list", "--count", f"main..{branch}").strip() == "1"
    gh.open_pr = {"number": 1, "url": PR["url"], "html_url": PR["url"]}
    third = runbooks.revert_pr(project, "0007", {"sha": sha}, repo="o/r")
    assert (third.status, third.pr_url, third.pr_number) == ("ran", PR["url"], 1)
    assert "already open" in third.reason
    assert len(gh.named("create_pr")) == 2  # the third run opened nothing
    assert current(project) == "main" and clean(project)


def test_revert_without_a_remote_commits_on_the_branch(tmp_path, gh):
    root = make_repo(tmp_path, {"app.py": "VALUE = 1\n"}, remote=False)
    sha = commit(root, {"app.py": "VALUE = 2\n"}, "change")
    out = runbooks.revert_pr(root, "0007", {"sha": sha})
    branch = f"sdlc/0007/revert-{sha[:7]}"
    assert (out.status, out.pr_url) == ("ran", None)
    assert out.reason == f"no remote: revert committed on {branch}"
    assert git(root, "show", f"{branch}:app.py") == "VALUE = 1\n"
    assert current(root) == "main" and gh.calls == []


def test_revert_dry_run_writes_nothing_and_contacts_nothing(project, gh):
    sha = commit(project, {"app.py": "VALUE = 2\n"}, "change")
    push(project)
    before = git(project, "for-each-ref")
    out = runbooks.revert_pr(project, "0007", {"sha": sha}, repo="o/r", dry_run=True)
    assert out.status == "ran" and out.reason.startswith("dry run: would git revert")
    assert git(project, "for-each-ref") == before and gh.calls == []


# --- quarantine-flaky-test ------------------------------------------------------------------
def quarantine(root: Path, **kwargs: Any) -> runbooks.Outcome:
    kwargs.setdefault("config", {"test_paths": ["tests/**", "**/test_*.py"]})
    kwargs.setdefault("repo", "o/r")
    args = kwargs.pop("args", {"test": NODE})
    return runbooks.quarantine_flaky_test(root, "0007", args, **kwargs)


def run_quarantine(tmp_path: Path, gh: FakeGitHub, files: dict[str, str], name: str) -> str:
    root = make_repo(tmp_path, {"app.py": "VALUE = 1\n", "tests/test_app.py": TEST_FILE, **files})
    before = (root / "tests/test_app.py").read_bytes()
    out = quarantine(root, incident_pr_url="https://x/pr/9")
    assert out.status == "ran", out.reason
    assert out.branch == "sdlc/0007/quarantine" and out.pr_url == PR["url"]
    assert current(root) == "main" and clean(root)
    assert (root / "tests/test_app.py").read_bytes() == before
    assert remote_show(root, out.branch, "tests/test_app.py").encode() == before
    changed = git(bare(root), "diff", "--name-only", f"main..{out.branch}").split()
    assert changed == [name]
    message = git(bare(root), "log", "-1", "--format=%s", out.branch).strip()
    assert message == f"quarantine(0007): {NODE}"
    [(args, _)] = gh.named("create_pr")
    assert args[:4] == ("o/r", "main", out.branch, f"quarantine(0007): {NODE}")
    assert "https://x/pr/9" in args[4] and "p.45" in args[4]
    assert "the test file is untouched" in args[4].lower()
    assert gh.named("set_labels")[0][0] == ("o/r", 1, ["incident"], [])
    return remote_show(root, out.branch, name)


def test_quarantine_appends_to_pytest_ini_addopts(tmp_path, gh):
    text = run_quarantine(tmp_path, gh, {"pytest.ini": "[pytest]\naddopts = -q\n"}, "pytest.ini")
    assert text == f"[pytest]\naddopts = -q --deselect {NODE}\n"


def test_quarantine_appends_inside_a_pyproject_string(tmp_path, gh):
    pyproject = (
        '[project]\nname = "x"\n\n[tool.pytest.ini_options]\naddopts = "-q"  # quiet\n'
        'testpaths = ["tests"]\n\n[tool.ruff]\nline-length = 100\n'
    )
    text = run_quarantine(tmp_path, gh, {"pyproject.toml": pyproject}, "pyproject.toml")
    assert text == pyproject.replace('"-q"', f'"-q --deselect {NODE}"')


def test_quarantine_appends_to_a_pyproject_array(tmp_path, gh):
    pyproject = (
        '[tool.pytest.ini_options]\naddopts = [\n    "-q",\n    "-ra"  # summary\n]\n'
        '\n[tool.other]\nx = ["a"]\n'
    )
    text = run_quarantine(tmp_path, gh, {"pyproject.toml": pyproject}, "pyproject.toml")
    assert text == (
        '[tool.pytest.ini_options]\naddopts = [\n    "-q",\n    "-ra",  # summary\n'
        f'    "--deselect", "{NODE}",\n]\n\n[tool.other]\nx = ["a"]\n'
    )


def test_quarantine_without_a_config_creates_pytest_ini(tmp_path, gh):
    text = run_quarantine(tmp_path, gh, {}, "pytest.ini")
    assert text == f"[pytest]\naddopts = --deselect {NODE}\n"


def test_the_edited_configs_really_deselect_the_test(tmp_path):
    """The edits are read by pytest itself: the quarantined test is not collected."""
    forms = {
        "pytest.ini": "[pytest]\naddopts =\n    -rN\n    -p no:cacheprovider\n",
        "pyproject.toml": (
            '[tool.pytest.ini_options]\naddopts = [\n  "-p",\n  "no:cacheprovider"\n]\n'
        ),
        "tox.ini": "[tox]\nenvlist = py\n\n[pytest]\naddopts = -p no:cacheprovider\n",
        "setup.cfg": "[metadata]\nname = x\n\n[tool:pytest]\npython_files = test_*.py\n",
    }
    for i, (name, text) in enumerate(forms.items()):
        root = tmp_path / f"p{i}"
        (root / "tests").mkdir(parents=True)
        (root / "app.py").write_text("VALUE = 1\n", encoding="utf-8")
        (root / "tests/test_app.py").write_text(TEST_FILE, encoding="utf-8")
        (root / name).write_text(text, encoding="utf-8")
        assert runbooks.pytest_config(root)[0] == name
        data, already = runbooks.add_deselect(root / name, runbooks.pytest_config(root)[1], NODE)
        assert not already
        (root / name).write_bytes(data)
        proc = subprocess.run(
            [sys.executable, "-m", "pytest", "--collect-only", "-q", "-p", "no:cacheprovider"],
            cwd=root,
            capture_output=True,
            text=True,
        )
        assert "test_one" in proc.stdout and "test_two" not in proc.stdout, (name, proc.stdout)
        assert runbooks.add_deselect(root / name, runbooks.pytest_config(root)[1], NODE)[1]


def test_line_edits_keep_the_rest_of_the_file_byte_identical(tmp_path):
    ini = tmp_path / "setup.cfg"
    ini.write_bytes(b"[metadata]\r\nname = x\r\n\r\n[tool:pytest]\r\naddopts = -q\r\n[flake8]\r\n")
    data, _ = runbooks.add_deselect(ini, "[tool:pytest]", NODE)
    assert data == (
        b"[metadata]\r\nname = x\r\n\r\n[tool:pytest]\r\naddopts = -q --deselect "
        + NODE.encode()
        + b"\r\n[flake8]\r\n"
    )
    one = tmp_path / "pyproject.toml"
    one.write_text('[tool.pytest.ini_options]\naddopts = ["-q"]\n', encoding="utf-8")
    data, _ = runbooks.add_deselect(one, "[tool.pytest.ini_options]", NODE)
    assert data.decode() == f'[tool.pytest.ini_options]\naddopts = ["-q", "--deselect", "{NODE}"]\n'
    keyless = tmp_path / "tox.ini"
    keyless.write_text("[pytest]\nmarkers = slow\n", encoding="utf-8")
    data, _ = runbooks.add_deselect(keyless, "[pytest]", NODE)
    assert data.decode() == f"[pytest]\naddopts = --deselect {NODE}\nmarkers = slow\n"


def test_an_already_deselected_test_is_quarantined_idempotently(tmp_path, gh):
    ini = f"[pytest]\naddopts = -q --deselect {NODE}\n"
    root = make_repo(
        tmp_path, {"app.py": "VALUE = 1\n", "tests/test_app.py": TEST_FILE, "pytest.ini": ini}
    )
    out = quarantine(root)
    assert (out.status, out.reason) == ("ran", "already quarantined")
    assert out.pr_url is None and gh.named("create_pr") == []
    assert git(root, "branch", "--list", "sdlc/*").strip() == ""
    assert current(root) == "main" and clean(root)


def test_a_second_quarantine_run_reuses_the_branch_and_the_pr(project, gh):
    first = quarantine(project)
    assert first.status == "ran"
    gh.open_pr = {"number": 1, "url": PR["url"], "html_url": PR["url"]}
    again = quarantine(project)
    assert (again.status, again.reason, again.pr_url) == ("ran", "already quarantined", PR["url"])
    assert again.commit == first.commit and len(gh.named("create_pr")) == 1


def test_a_bad_node_id_is_refused(project, gh):
    for node, why in (
        ("tests/test_app.py", "names a test function"),
        ("tests/test_app.py::", "names a test function"),
        ("tests/nope.py::test_x", "does not exist"),
        ("tests/test_app.py::test one", "whitespace"),
        ("../x.py::test_x", "not relative"),
        ("", "missing"),
    ):
        out = quarantine(project, args={"test": node})
        assert out.status == "failed" and why in out.reason, (node, out.reason)
    assert gh.calls == [] and current(project) == "main"


def test_the_runbook_never_edits_a_test_path(project, gh):
    out = quarantine(project, config={"test_paths": ["*.ini"]})
    assert out.status == "failed" and "refusing to edit pytest.ini" in out.reason
    out = quarantine(project, args={"test": NODE, "file": "tests/test_app.py"})
    assert out.status == "failed" and "never edits a test path" in out.reason
    assert not (project / "pytest.ini").exists() and gh.calls == [] and clean(project)


def test_quarantine_on_a_non_python_project_is_unsupported(tmp_path, gh):
    root = make_repo(tmp_path, {"package.json": '{"name": "x"}\n', "test/a.test.js": "\n"})
    out = quarantine(root, args={"test": "test/a.test.js::works"})
    assert out.status == "unsupported"
    assert out.reason == "the quarantine runbook supports python projects only"


def test_quarantine_dry_run_writes_nothing(project, gh):
    out = quarantine(project, dry_run=True)
    assert out.status == "ran" and out.reason.startswith("dry run: would add --deselect")
    assert not (project / "pytest.ini").exists() and gh.calls == []
    assert git(project, "branch", "--list", "sdlc/*").strip() == ""


# --- project runbooks -----------------------------------------------------------------------
SCRIPT = (
    "import pathlib, sys\n"
    "pathlib.Path('ran-' + sys.argv[1]).write_text('x')\n"
    "print('out of ' + sys.argv[1])\n"
    "print('err of ' + sys.argv[1], file=sys.stderr)\n"
    "if sys.argv[1] == 'long':\n    print('y' * 5000 + 'END')\n"
    "sys.exit(3 if sys.argv[1] == 'bad' else 0)\n"
)


def py_command(*steps: str) -> str:
    return " && ".join(f'"{Path(sys.executable).as_posix()}" step.py {s}' for s in steps)


@pytest.fixture
def scripted(tmp_path) -> Path:
    (tmp_path / "step.py").write_text(SCRIPT, encoding="utf-8")
    return tmp_path


def test_a_project_runbook_that_succeeds_records_its_output(scripted):
    entry = {"name": "rollback-deploy", "command": py_command("one", "two")}
    out = runbooks.project_runbook(scripted, "rollback-deploy", entry, timeout=60)
    assert (out.status, out.exit_code, out.reason) == ("ran", 0, "")
    for text in ("out of one", "err of one", "out of two", "err of two"):
        assert text in out.output_tail


def test_a_failing_project_runbook_stops_and_keeps_the_exit_code(scripted):
    entry = {"command": py_command("bad", "two")}
    out = runbooks.project_runbook(scripted, "rollback-deploy", entry, timeout=60)
    assert (out.status, out.exit_code) == ("failed", 3)
    assert "exited 3" in out.reason and "out of bad" in out.output_tail
    assert not (scripted / "ran-two").exists()
    missing = runbooks.project_runbook(
        scripted, "x", {"command": "no-such-command-xyz"}, timeout=60
    )
    assert (missing.status, missing.exit_code) == ("failed", 127)


def test_a_project_runbook_keeps_only_the_tail_of_its_output(scripted):
    out = runbooks.project_runbook(scripted, "r", {"command": py_command("long")}, timeout=60)
    assert out.status == "ran" and len(out.output_tail) == runbooks.OUTPUT_TAIL
    assert "END" in out.output_tail and "out of long" not in out.output_tail


def test_project_runbook_unsupported_and_dry_run(scripted, capsys):
    out = runbooks.project_runbook(scripted, "r", {"name": "r"}, timeout=60)
    assert out.status == "unsupported" and "no command" in out.reason
    dry = runbooks.project_runbook(scripted, "r", {"command": py_command("one")}, timeout=60,
                                   dry_run=True)  # fmt: skip
    assert dry.status == "ran" and dry.reason.startswith("dry run: would run")
    assert "step.py one" in capsys.readouterr().out
    assert not (scripted / "ran-one").exists()
    shell = runbooks.project_runbook(scripted, "r", {"command": "echo a | cat"}, timeout=60)
    assert shell.status == "failed" and "shell operator" in shell.reason


def test_run_dispatches_on_the_name(scripted, project, gh):
    common = {"config": {}, "incident_pr_url": None, "repo": "o/r", "timeout": 60}
    none = runbooks.run("rollback-deploy", scripted, "0007", {}, entry=None, **common)
    assert none.status == "unsupported" and "rollback-deploy" in none.reason
    entry = {"command": py_command("one")}
    ran = runbooks.run("runbook:rollback-deploy", scripted, "0007", {}, entry=entry, **common)
    assert (ran.runbook, ran.status) == ("rollback-deploy", "ran")
    sha = git(project, "rev-parse", "HEAD").strip()
    rev = runbooks.run(
        "revert-pr", project, "0007", {"sha": sha}, entry=None, dry_run=True, **common
    )
    assert rev.runbook == "revert-pr" and rev.status == "ran"
    q = runbooks.run(
        "quarantine-flaky-test", project, "0007", {"test": NODE}, entry=None, dry_run=True,
        **common,
    )  # fmt: skip
    assert q.runbook == "quarantine-flaky-test" and q.status == "ran"


def test_write_record_path_and_content(tmp_path):
    evidence = tmp_path / "changes/0007-x/evidence"
    out = runbooks.Outcome("revert-pr", "ran", branch="sdlc/0007/revert-abcdef1",
                           pr_url=PR["url"], pr_number=1, args={"sha": "abc"})  # fmt: skip
    assert runbooks.record_path(evidence, "revert-pr") == evidence / "runbook-revert-pr.json"
    path = runbooks.write_record(evidence, out)
    assert path == evidence / "runbook-revert-pr.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data == out.as_dict()
    assert data["status"] == "ran" and data["args"] == {"sha": "abc"}
    assert data["at"].endswith("Z") and data["exit_code"] is None
    assert b"\r\n" not in path.read_bytes()


def test_a_modified_record_inside_the_change_folder_never_blocks_a_runbook(project, gh):
    """Session-5 review: every hook appends to the change's tracked hook-log.jsonl before the
    dispatch call itself, and a fix round rewrites proposal.json; a runbook starts its branch
    from the default branch and never touches changes/, so such files are not "dirty" for
    it. A modified source file still is."""
    root = project
    change = root / "changes" / "0007-x" / "evidence"
    change.mkdir(parents=True)
    (change / "hook-log.jsonl").write_text('{"verdict": "allow"}\n', encoding="utf-8")
    git(root, "add", ".")
    git(root, "commit", "-q", "-m", "the change folder")
    git(root, "push", "-q", "origin", "main")
    sha = git(root, "rev-parse", "HEAD").strip()
    (change / "hook-log.jsonl").write_text('{"verdict": "allow"}\n{"verdict": "block"}\n', "utf-8")
    assert runbooks._dirty(root) == []
    outcome = runbooks.revert_pr(root, "0007", {"sha": sha}, repo="o/r", dry_run=True)
    assert outcome.status == "ran", outcome.reason
    (root / "app.py").write_text("VALUE = 2\n", encoding="utf-8")
    assert runbooks._dirty(root) == ["app.py"]
    outcome = runbooks.revert_pr(root, "0007", {"sha": sha}, repo="o/r")
    assert outcome.status == "failed" and "uncommitted" in outcome.reason
