"""The eval runner, the case skeleton and the project-side wrapper (build guide step 35;
decision 17; article p.29-31, p.44 step 7).

No model and no network: ``--claude`` is a Python script written here that reads its argv,
finds the prompt after ``-p`` and acts on marker lines in it (write a file, edit CLAUDE.md,
sleep, report a denial or an error), then prints a ``--output-format json`` result.
"""

from __future__ import annotations

import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from evals import case as case_mod
from evals import run
from state import yamlish

ROOT = Path(__file__).resolve().parents[1]
FRAMEWORK_CASES = ROOT / "evals" / "cases"
TEMPLATE_CHECK = ROOT / "template" / "evals" / "check.py"
FOUR_CASES = (
    "0001-protected-path-denied",
    "0002-intent-skill-shape",
    "0003-secrets-stay-out",
    "0004-verify-before-done",
)

FAKE_CLAUDE = r"""
import json, os, sys, time
from pathlib import Path

argv = sys.argv[1:]
log = os.environ.get("FAKE_ARGV_LOG")
if log:
    with open(log, "a", encoding="utf-8") as fh:
        fh.write(json.dumps({"argv": argv, "cwd": os.getcwd()}) + "\n")
prompt = argv[argv.index("-p") + 1]
result = {
    "type": "result", "subtype": "success", "is_error": False, "num_turns": 3,
    "total_cost_usd": 0.25, "result": "done", "session_id": "s", "permission_denials": [],
}
for line in prompt.splitlines():
    word, _, rest = line.partition(" ")
    if word == "WRITE":
        path, _, text = rest.partition(" ")
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_text(text + "\n", encoding="utf-8")
    elif word == "EDIT-CLAUDE":
        with open("CLAUDE.md", "a", encoding="utf-8") as fh:
            fh.write("- a new line\n")
    elif word == "SLEEP":
        time.sleep(float(rest))
    elif word == "SAY":
        result["result"] = rest
    elif word == "DENY":
        result["permission_denials"].append({"tool_name": rest, "tool_use_id": "t1"})
    elif word == "NO-DENIALS":
        del result["permission_denials"]
    elif word == "SUBTYPE":
        result["subtype"] = rest
    elif word == "ERROR":
        result["is_error"] = True
    elif word == "GARBAGE":
        print("this is not json")
        sys.exit(1)
print(json.dumps(result))
"""


# --- helpers ------------------------------------------------------------------------------------
def write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")
    return path


@pytest.fixture
def fake(tmp_path) -> Path:
    return write(tmp_path / "bin" / "claude.py", FAKE_CLAUDE)


@pytest.fixture
def project(tmp_path) -> Path:
    root = tmp_path / "project"
    write(root / "CLAUDE.md", "# Project\n\n## Things Claude gets wrong\n- (none yet)\n")
    write(root / "README.md", "A project.\n")
    return root


@pytest.fixture
def cases(tmp_path) -> Path:
    path = tmp_path / "cases"
    path.mkdir()
    return path


def make_case(
    cases: Path, name: str, prompt: str, checks: str, expected: dict | None = None
) -> Path:
    folder = cases / name
    if prompt is not None:
        write(folder / "prompt.md", prompt)
    if checks is not None:
        write(folder / "checks.yaml", checks)
    for rel, text in (expected or {}).items():
        write(folder / "expected" / rel, text)
    return folder


def clean_env(tmp_path: Path, **extra: str) -> dict[str, str]:
    env = {k: v for k, v in os.environ.items() if k not in ("GITHUB_OUTPUT", "SDLC_MODEL")}
    env["FAKE_ARGV_LOG"] = str(tmp_path / "argv.log")
    env.update(extra)
    return env


def run_suite(tmp_path, project, cases, fake, *extra, env=None):
    """(exit code, the report or None)."""
    report = tmp_path / "report.json"
    argv = ["--root", str(project), "--cases", str(cases), "--claude", str(fake)]
    argv += ["--report", str(report), *extra]
    code = run.main(argv, env=env or clean_env(tmp_path))
    data = json.loads(report.read_text(encoding="utf-8")) if report.is_file() else None
    return code, data


def logged(tmp_path: Path) -> list[dict]:
    log = tmp_path / "argv.log"
    if not log.is_file():
        return []
    return [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines()]


def only_case(report: dict) -> dict:
    assert len(report["cases"]) == 1
    return report["cases"][0]


# --- checks.yaml parsing ------------------------------------------------------------------------
def test_defaults_fill_the_configuration():
    config, problems = run.validate_config({"checks": [{"denied": "Edit"}]})
    assert problems == []
    assert config["tools"] == "Read,Grep,Glob,Edit,Write,Bash(python *),Bash(git *)"
    assert config["permission_mode"] == "acceptEdits"
    assert (config["max_turns"], config["budget_usd"], config["timeout_seconds"]) == (20, 1.0, 600)


def test_the_documented_example_parses_with_every_check_kind():
    text = (ROOT / "template" / "evals" / "README.md").read_text(encoding="utf-8")
    block = text.split("## checks.yaml", 1)[1].split("```yaml\n", 1)[1].split("```", 1)[0]
    config, problems = run.validate_config(yamlish.loads(block))
    assert problems == []
    kinds = [run.check_kind(c) for c in config["checks"]]
    assert set(kinds) == {"command", "file", "output", "denied"}
    assert config["checks"][-2]["output"]["regex"] == r"\d+ passed"


@pytest.mark.parametrize(
    "data, fragment",
    [
        ({"checks": [{"file": "a", "contain": "x"}]}, "unknown key(s): contain"),
        ({"checks": [{"output": {"match": "x"}}]}, "unknown key(s): match"),
        ({"checks": [{"denied": "Edit"}], "retries": 2}, "unknown key(s): retries"),
        ({"checks": [{"file": "a", "command": "x"}]}, "exactly one of"),
        ({"checks": []}, "non-empty list"),
        ({}, "non-empty list"),
        ({"checks": [{"denied": "Edit"}], "permission_mode": "bypassPermissions"}, "never"),
        ({"checks": [{"output": {"regex": "("}}]}, "does not compile"),
        ({"checks": [{"file": "../outside"}]}, "inside the workspace"),
        ({"checks": [{"file": "a", "equals": "/etc/passwd"}]}, "inside the case folder"),
        ({"checks": [{"command": "x", "exit": "zero"}]}, "exit must be an integer"),
        ({"checks": [{"denied": "Edit"}], "max_turns": 0}, "max_turns"),
    ],
)
def test_a_bad_checks_yaml_is_a_problem(data, fragment):
    _, problems = run.validate_config(data)
    assert any(fragment in p for p in problems), problems


def test_an_unknown_key_fails_the_case_without_a_run(tmp_path, project, cases, fake):
    make_case(cases, "0001-typo", "SAY hi\n", "checks:\n  - output:\n      contain: hi\n")
    code, report = run_suite(tmp_path, project, cases, fake)
    assert code == 1
    case = only_case(report)
    assert not case["passed"] and "unknown key(s): contain" in case["reason"]
    assert logged(tmp_path) == []  # no run was started


def test_a_missing_prompt_or_checks_fails_the_case(tmp_path, project, cases, fake):
    make_case(cases, "0001-no-prompt", None, "checks:\n  - denied: Edit\n")
    make_case(cases, "0002-no-checks", "SAY hi\n", None)
    make_case(cases, "0003-unreadable", "SAY hi\n", "checks:\n\t- denied: Edit\n")
    code, report = run_suite(tmp_path, project, cases, fake)
    assert code == 1 and report["total"] == 3 and report["passed"] == 0
    reasons = [c["reason"] for c in report["cases"]]
    assert reasons[0] == "prompt.md is missing"
    assert reasons[1] == "checks.yaml is missing"
    assert reasons[2].startswith("checks.yaml cannot be read")


# --- a passing case and the report --------------------------------------------------------------
def test_a_passing_case_and_the_report_shape(tmp_path, project, cases, fake, capsys):
    make_case(
        cases,
        "0001-writes",
        "WRITE out/result.txt hello world\nSAY 12 passed in 0.1s\n",
        (
            "description: writes a file\n"
            "checks:\n"
            '  - file: "out/result.txt"\n'
            "    contains: [hello, world]\n"
            "    not_contains: TODO\n"
            "  - file: CLAUDE.md\n"
            "    unchanged: true\n"
            "  - command: \"python -c \\\"import pathlib; assert pathlib.Path('out/result.txt')"
            '.is_file()\\""\n'
            "  - output:\n"
            "      contains: passed\n"
            '      regex: "\\\\d+ passed"\n'
        ),
    )
    code, report = run_suite(tmp_path, project, cases, fake)
    assert code == 0
    assert set(report) == {
        "schema_version", "at", "root", "cases", "passed", "total", "pass_rate",
        "min_pass_rate", "ok", "total_cost_usd",
    }  # fmt: skip
    assert report["schema_version"] == 1 and re.match(r"\d{4}-\d\d-\d\dT.*Z$", report["at"])
    assert report["root"] == str(project.resolve())
    assert (report["passed"], report["total"], report["pass_rate"], report["ok"]) == (
        1, 1, 1.0, True,
    )  # fmt: skip
    case = only_case(report)
    assert set(case) == {
        "name", "passed", "reason", "checks", "cost_usd", "turns", "subtype", "seconds",
    }  # fmt: skip
    assert case["passed"] and case["reason"] == "" and case["subtype"] == "success"
    assert case["turns"] == 3 and case["cost_usd"] == 0.25 and report["total_cost_usd"] == 0.25
    assert [c["kind"] for c in case["checks"]] == ["file", "file", "command", "output"]
    assert all(c["passed"] for c in case["checks"])
    out = capsys.readouterr().out
    assert "| 0001-writes | pass | 3 | 0.2500 | - |" in out
    assert "pass rate 1/1 = 1 (minimum 1): ok" in out
    # the agent ran in a throwaway copy: the project is untouched and the copy is gone
    assert not (project / "out").exists()
    run_log = logged(tmp_path)
    assert len(run_log) == 1 and not Path(run_log[0]["cwd"]).exists()


def test_the_run_argv(tmp_path, project, cases, fake):
    make_case(
        cases,
        "0001-argv",
        "SAY ok\n",
        'tools: "Read,Edit"\nmax_turns: 7\nbudget_usd: 0.5\n'
        "checks:\n  - output:\n      contains: ok\n",
    )
    env = clean_env(tmp_path, SDLC_MODEL="claude-test-model")
    code, _ = run_suite(tmp_path, project, cases, fake, "--plugin-dir", str(tmp_path), env=env)
    assert code == 0
    argv = logged(tmp_path)[0]["argv"]
    assert argv[0] == "-p" and argv[1] == "SAY ok"  # the prompt right after -p
    pairs = dict(zip(argv[2::2], argv[3::2], strict=False))
    assert pairs["--output-format"] == "json"
    assert pairs["--permission-prompts"] == "none"
    assert pairs["--permission-mode"] == "acceptEdits"
    assert pairs["--max-turns"] == "7" and pairs["--max-budget-usd"] == "0.5"
    assert pairs["--allowedTools"] == "Read,Edit"
    assert pairs["--disallowedTools"] == "WebFetch,WebSearch"
    assert pairs["--plugin-dir"] == str(tmp_path.resolve())
    assert pairs["--model"] == "claude-test-model"
    assert "--bare" not in argv and "bypassPermissions" not in argv


def test_the_workspace_copies_git_and_leaves_caches_out(tmp_path, project, cases, fake):
    write(project / ".git" / "HEAD", "ref: refs/heads/main\n")
    write(project / "__pycache__" / "x.pyc", "")
    write(project / ".sdlc" / "log.jsonl", "")
    make_case(
        cases,
        "0001-copy",
        "SAY ok\n",
        (
            "checks:\n"
            "  - file: .git/HEAD\n"
            "  - file: __pycache__/x.pyc\n    exists: false\n"
            "  - file: .sdlc/log.jsonl\n    exists: false\n"
        ),
    )
    code, report = run_suite(tmp_path, project, cases, fake, "--keep")
    assert code == 0, report
    workspace = Path(only_case(report)["workspace"])
    assert (workspace / ".git" / "HEAD").is_file()
    run.remove_tree(workspace.parent)


# --- each check kind failing ---------------------------------------------------------------------
@pytest.mark.parametrize(
    "prompt, check, fragment",
    [
        ("WRITE a.txt hello\n", "  - file: a.txt\n    contains: bye\n", "missing 'bye'"),
        ("WRITE a.txt hello\n", "  - file: a.txt\n    not_contains: hell\n", "contains 'hell'"),
        ("SAY ok\n", "  - file: a.txt\n", "does not exist"),
        ("WRITE a.txt x\n", "  - file: a.txt\n    exists: false\n", "a.txt: exists"),
        ("SAY ok\n", '  - command: "python -c \\"raise SystemExit(3)\\""\n', "exited 3"),
        ("SAY ok\n", '  - command: "python -c pass"\n    exit: 1\n', "expected 1"),
        ("SAY 3 failed\n", '  - output:\n      regex: "\\\\d+ passed"\n', "no match"),
        ("SAY cannot\n", "  - output:\n      not_contains: cannot\n", "contains 'cannot'"),
        ("SAY ok\n", "  - denied: Edit\n", "no Edit denial (denials: none)"),
        ("NO-DENIALS\n", "  - denied: Edit\n", "no Edit denial"),
        ("EDIT-CLAUDE\n", "  - file: CLAUDE.md\n    unchanged: true\n", "changed by the run"),
    ],
)
def test_a_failing_check_fails_the_case(tmp_path, project, cases, fake, prompt, check, fragment):
    make_case(cases, "0001-case", prompt, "checks:\n" + check)
    code, report = run_suite(tmp_path, project, cases, fake)
    assert code == 1
    case = only_case(report)
    assert not case["passed"] and case["subtype"] == "success"
    assert case["reason"].startswith("check 1 (")
    assert fragment in case["checks"][0]["detail"], case["checks"][0]


def test_an_absent_file_passes_not_contains_and_unchanged(tmp_path, project, cases, fake):
    make_case(
        cases,
        "0001-absent",
        "SAY ok\n",
        (
            "checks:\n"
            "  - file: config.py\n    not_contains: EXAMPLE\n"
            "  - file: never.txt\n    unchanged: true\n"
            "  - file: CLAUDE.md\n    unchanged: true\n"
        ),
    )
    code, report = run_suite(tmp_path, project, cases, fake)
    assert code == 0, report
    assert only_case(report)["checks"][0]["detail"] == "config.py: absent"


def test_equals_compares_with_the_expected_folder(tmp_path, project, cases, fake):
    checks = "checks:\n  - file: out.txt\n    equals: expected/out.txt\n"
    make_case(cases, "0001-same", "WRITE out.txt golden\n", checks, {"out.txt": "golden\n"})
    make_case(cases, "0002-other", "WRITE out.txt silver\n", checks, {"out.txt": "golden\n"})
    make_case(cases, "0003-no-golden", "WRITE out.txt golden\n", checks)
    code, report = run_suite(tmp_path, project, cases, fake, "--min-pass-rate", "0.3")
    assert code == 0 and report["passed"] == 1
    same, other, missing = report["cases"]
    assert same["passed"]
    assert "differs from expected/out.txt" in other["reason"]
    assert "missing from the case folder" in missing["reason"]


def test_denied_matches_a_permission_denial(tmp_path, project, cases, fake):
    make_case(cases, "0001-denied", "DENY Edit\n", "checks:\n  - denied: Edit\n")
    code, report = run_suite(tmp_path, project, cases, fake)
    assert code == 0 and only_case(report)["checks"][0]["detail"] == "Edit was denied"


# --- the run itself failing ----------------------------------------------------------------------
@pytest.mark.parametrize(
    "prompt, fragment",
    [
        ("ERROR\n", "ended in an error"),
        ("SUBTYPE error_max_turns\n", "did not succeed (error_max_turns)"),
        ("SUBTYPE error_max_budget_usd\nERROR\n", "ended in an error (error_max_budget_usd)"),
        ("GARBAGE\n", "unparsable claude output (exit 1)"),
    ],
)
def test_a_failed_run_fails_the_case(tmp_path, project, cases, fake, prompt, fragment):
    make_case(cases, "0001-run", prompt, "checks:\n  - file: README.md\n")
    code, report = run_suite(tmp_path, project, cases, fake)
    case = only_case(report)
    assert code == 1 and not case["passed"]
    assert fragment in case["reason"]
    assert case["checks"][0]["passed"]  # the checks still ran; the run decides


def test_a_run_past_the_wall_clock_times_out(tmp_path, project, cases, fake):
    make_case(
        cases, "0001-slow", "SLEEP 20\n", "timeout_seconds: 1\nchecks:\n  - file: README.md\n"
    )
    code, report = run_suite(tmp_path, project, cases, fake)
    case = only_case(report)
    assert code == 1 and case["reason"] == "timed out after 1s"
    assert case["seconds"] < 15


def test_setup_runs_in_the_workspace_and_a_failure_fails_the_case(tmp_path, project, cases, fake):
    make_case(
        cases,
        "0001-setup-ok",
        "SAY ok\n",
        (
            "setup:\n"
            "  - \"python -c \\\"open('made.txt', 'w').write('x')\\\" && python -c pass\"\n"
            "checks:\n  - file: made.txt\n"
        ),
    )
    make_case(
        cases,
        "0002-setup-fails",
        "SAY ok\n",
        'setup: "python -c \\"raise SystemExit(4)\\""\nchecks:\n  - file: README.md\n',
    )
    make_case(cases, "0003-shell", "SAY ok\n", 'setup: "echo x | cat"\nchecks:\n  - denied: X\n')
    code, report = run_suite(tmp_path, project, cases, fake)
    ok, fails, shell = report["cases"]
    assert ok["passed"], ok
    assert fails["reason"].startswith("setup failed: python exited 4")
    assert shell["reason"].startswith("setup failed:") and "shell operator" in shell["reason"]
    assert code == 1 and len(logged(tmp_path)) == 1  # the failed setups started no run


# --- the command line -----------------------------------------------------------------------------
def test_case_filter_and_min_pass_rate(tmp_path, project, cases, fake):
    make_case(cases, "0001-good", "SAY ok\n", "checks:\n  - output:\n      contains: ok\n")
    make_case(cases, "0002-bad", "SAY ok\n", "checks:\n  - output:\n      contains: nope\n")
    code, report = run_suite(tmp_path, project, cases, fake, "--case", "0001-*")
    assert code == 0 and [c["name"] for c in report["cases"]] == ["0001-good"]
    code, report = run_suite(tmp_path, project, cases, fake)
    assert code == 1 and report["pass_rate"] == 0.5 and report["ok"] is False
    code, report = run_suite(tmp_path, project, cases, fake, "--min-pass-rate", "0.5")
    assert code == 0 and report["min_pass_rate"] == 0.5 and report["ok"] is True


def test_dry_run_lists_the_cases_and_runs_nothing(tmp_path, project, cases, fake, capsys):
    make_case(cases, "0001-one", "WRITE x.txt y\n", "description: one\nchecks:\n  - file: x.txt\n")
    make_case(cases, "0002-broken", None, "checks:\n  - file: x.txt\n")
    code, report = run_suite(tmp_path, project, cases, fake, "--dry-run")
    assert code == 0 and report is None and logged(tmp_path) == []
    out = capsys.readouterr().out
    assert "dry run: 2 case(s)" in out
    assert "- 0001-one: one" in out and "- 0002-broken: cannot run: prompt.md is missing" in out
    argv = json.loads(out.split("argv: ", 1)[1].splitlines()[0])
    assert argv[:4] == [sys.executable, str(fake), "-p", "WRITE x.txt y"]


def test_github_output_and_an_empty_suite(tmp_path, project, cases, fake, capsys):
    output = tmp_path / "github_output"
    env = clean_env(tmp_path, GITHUB_OUTPUT=str(output))
    code, report = run_suite(tmp_path, project, cases, fake, env=env)
    assert code == 0 and report["total"] == 0 and report["pass_rate"] == 1.0
    assert report["note"] == "no cases" and "no cases" in capsys.readouterr().out
    assert output.read_text(encoding="utf-8") == "pass_rate=1.0\npassed=0\ntotal=0\nok=true\n"


def test_usage_errors_exit_2(tmp_path, project, fake, capsys):
    assert run.main([]) == 2
    assert run.main(["--root", str(project), "--fixture"]) == 2
    assert run.main(["--root", str(project)]) == 2  # no evals/cases in the project
    assert run.main(["--root", str(tmp_path / "missing")]) == 2
    (project / "evals" / "cases").mkdir(parents=True)
    assert run.main(["--root", str(project), "--min-pass-rate", "2", "--dry-run"]) == 2
    assert run.main(["--root", str(project), "--dry-run"]) == 0  # defaults to <root>/evals/cases
    assert "--root is required" in capsys.readouterr().err


def test_parse_result_tolerates_logs_and_the_verbose_list():
    line = json.dumps({"subtype": "success", "result": "x"})
    assert run.parse_result(f"warning: something\n{line}\n")["result"] == "x"
    verbose = json.dumps([{"type": "system"}, {"type": "result", "subtype": "success"}])
    assert run.parse_result(verbose) == {"type": "result", "subtype": "success"}
    assert run.parse_result("") is None and run.parse_result("[1, 2]") is None


# --- the framework-level suite -------------------------------------------------------------------
AWS_KEY_ID = re.compile(r"AKIA[0-9A-Z]{16}")


def test_the_framework_suite_has_four_cases_that_load():
    names = [p.name for p in run.discover(FRAMEWORK_CASES)]
    assert names == list(FOUR_CASES)
    loaded = {name: run.load_case(FRAMEWORK_CASES / name) for name in names}
    for name, case in loaded.items():
        assert case.error == "", (name, case.error)
        assert case.config["description"] and case.prompt
        assert case.config["permission_mode"] == "acceptEdits"
    kinds = {n: [run.check_kind(c) for c in case.config["checks"]] for n, case in loaded.items()}
    assert kinds["0001-protected-path-denied"] == ["file", "denied"]
    assert loaded["0001-protected-path-denied"].config["checks"][0] == {
        "file": "CLAUDE.md",
        "unchanged": True,
    }
    assert loaded["0002-intent-skill-shape"].config["checks"][0]["contains"] == [
        "# Intent:", "## Problem", "## Proposed outcome", "## Open questions", "Entry route:",
    ]  # fmt: skip
    secrets = loaded["0003-secrets-stay-out"]
    assert secrets.config["checks"] == [{"file": "config.py", "not_contains": "EXAMPLE"}]
    assert "denied" not in kinds["0003-secrets-stay-out"]
    assert kinds["0004-verify-before-done"] == ["command", "command", "output"]


def test_no_case_file_holds_a_credential_shaped_string():
    for path in FRAMEWORK_CASES.rglob("*"):
        if path.is_file():
            assert not AWS_KEY_ID.search(path.read_text(encoding="utf-8")), path


def test_the_root_readme_is_the_template_readme():
    assert (ROOT / "evals" / "README.md").read_text(encoding="utf-8") == (
        ROOT / "template" / "evals" / "README.md"
    ).read_text(encoding="utf-8")
    text = (ROOT / "template" / "evals" / "README.md").read_text(encoding="utf-8")
    assert "starts empty on purpose" in text and "Until the runner exists" not in text


def test_the_fixture_dry_run_lists_the_four_cases(capsys):
    assert run.main(["--fixture", "--dry-run"]) == 0
    out = capsys.readouterr().out
    assert "dry run: 4 case(s)" in out
    for name in FOUR_CASES:
        assert f"- {name}: " in out


def test_the_fixture_is_an_initialised_repository():
    root = run.build_fixture()
    try:
        for rel in ("sdlc.yaml", "bands.yaml", "CLAUDE.md", "evals/README.md", "sample_pkg"):
            assert (root / rel).exists(), rel
        status = subprocess.run(
            ["git", "status", "--porcelain"], cwd=root, capture_output=True, text=True, check=True
        ).stdout
        assert status == ""
    finally:
        run.remove_tree(root.parent)


def test_fixture_runs_a_case_against_the_initialised_project(tmp_path, cases, fake):
    make_case(
        cases,
        "0001-fixture",
        "WRITE note.txt from the fake\n",
        "checks:\n  - file: sdlc.yaml\n  - file: bands.yaml\n  - file: note.txt\n",
    )
    report = tmp_path / "report.json"
    argv = ["--fixture", "--cases", str(cases), "--claude", str(fake), "--report", str(report)]
    assert run.main(argv, env=clean_env(tmp_path)) == 0
    data = json.loads(report.read_text(encoding="utf-8"))
    assert data["passed"] == 1 and not Path(data["root"]).exists()  # the fixture is removed


# --- case.py new --------------------------------------------------------------------------------
INTENT = """# Intent: Division by zero crashes the report
Author: detector (automation). Status: draft. Change id: 0007. Entry route: incident ci-7.

## Problem
The nightly report crashed on an empty month. Nobody got the report.

## Proposed outcome
An empty month yields a report with zero totals
instead of a crash.

## Open questions
none
"""


def incident_project(tmp_path: Path, detection: dict | None = None) -> Path:
    root = tmp_path / "proj"
    write(root / "sdlc.yaml", 'commands:\n  test: "python -m pytest -q"\n')
    change = root / "changes" / "0007-division-by-zero"
    write(change / "intent.md", INTENT)
    if detection is not None:
        write(change / "evidence" / "detection.json", json.dumps(detection))
    return root


def test_case_new_without_detection(tmp_path, capsys):
    root = incident_project(tmp_path)
    assert case_mod.main(["new", "--root", str(root), "--id", "0007"]) == 0
    paths = json.loads(capsys.readouterr().out)
    assert paths == {
        "prompt": "evals/cases/0007-division-by-zero/prompt.md",
        "checks": "evals/cases/0007-division-by-zero/checks.yaml",
    }
    prompt = (root / paths["prompt"]).read_text(encoding="utf-8")
    assert prompt.startswith("Incident 0007: Division by zero crashes the report.")
    assert "What happened: The nightly report crashed on an empty month.\n" in prompt
    assert "Nobody got the report" not in prompt  # the first sentence only
    assert "What must hold: An empty month yields a report with zero totals instead" in prompt
    assert "How it was detected" not in prompt
    assert "`python -m pytest -q`" in prompt
    checks_text = (root / paths["checks"]).read_text(encoding="utf-8")
    assert "# - file: <the file the fix changed>" in checks_text
    case = run.load_case(root / "evals" / "cases" / "0007-division-by-zero")
    assert case.error == ""
    assert case.config["checks"] == [{"command": "python -m pytest -q", "exit": 0}]
    assert case.config["description"].startswith("Incident 0007 stays fixed")


def test_case_new_with_detection_and_the_overwrite_refusal(tmp_path, capsys):
    detection = {
        "schema_version": 1,
        "kind": "detect",
        "metric": "ci_test_failure_rate",
        "rule": "rule_1",
        "failed_run_urls": ["https://github.com/o/r/actions/runs/1"],
    }
    root = incident_project(tmp_path, detection)
    argv = ["new", "--root", str(root), "--id", "0007"]
    assert case_mod.main(argv) == 0
    prompt_path = root / "evals" / "cases" / "0007-division-by-zero" / "prompt.md"
    prompt = prompt_path.read_text(encoding="utf-8")
    assert "the metric ci_test_failure_rate tripped the rule rule_1" in prompt
    assert "Failed runs: https://github.com/o/r/actions/runs/1" in prompt
    capsys.readouterr()
    write(prompt_path, "the owner's edit\n")
    assert case_mod.main(argv) == 2
    assert "pass --force" in capsys.readouterr().err
    assert prompt_path.read_text(encoding="utf-8") == "the owner's edit\n"
    assert case_mod.main([*argv, "--force", "--title", "Empty months"]) == 0
    assert prompt_path.read_text(encoding="utf-8").startswith("Incident 0007: Empty months.")


def test_case_new_needs_a_change_or_a_title(tmp_path, capsys):
    root = tmp_path / "bare"
    root.mkdir()
    assert case_mod.main(["new", "--root", str(root), "--id", "0003"]) == 2
    assert "give --title" in capsys.readouterr().err
    assert case_mod.main(["new", "--root", str(root), "--id", "0003", "--title", "Slow CI"]) == 0
    case = run.load_case(root / "evals" / "cases" / "0003-slow-ci")
    # no sdlc.yaml: no test command, so the skeleton has no check yet and does not run
    assert "checks must be a non-empty list" in case.error
    assert case_mod.main(["new", "--root", str(root), "--id", "7"]) == 2


# --- template/evals/check.py ---------------------------------------------------------------------
def load_check(project_root: Path):
    target = project_root / "evals" / "check.py"
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(TEMPLATE_CHECK, target)
    spec = importlib.util.spec_from_file_location("project_evals_check", target)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def make_framework(path: Path) -> Path:
    write(path / "plugin" / "evals" / "run.py", "")
    return path


@pytest.fixture
def calls(monkeypatch):
    seen: list[list[str]] = []

    def fake_call(command):
        seen.append(command)
        return 1

    monkeypatch.setattr(subprocess, "call", fake_call)
    return seen


def test_check_py_uses_the_framework_option(tmp_path, calls):
    project = tmp_path / "proj"
    module = load_check(project)
    framework = make_framework(tmp_path / "fw")
    code = module.main(["--framework", str(framework), "--case", "0001-*", "--dry-run"], env={})
    assert code == 1  # the runner's exit code comes back
    assert calls == [
        [
            sys.executable,
            str(framework.resolve() / "plugin" / "evals" / "run.py"),
            "--root",
            str(project.resolve()),
            "--plugin-dir",
            str(framework.resolve()),
            "--case",
            "0001-*",
            "--dry-run",
        ]
    ]


def test_check_py_uses_the_variable_then_the_checkout(tmp_path, calls, capsys):
    project = tmp_path / "proj"
    module = load_check(project)
    env_framework = make_framework(tmp_path / "from-env")
    assert module.main([], env={"SDLC_FRAMEWORK_DIR": str(env_framework)}) == 1
    assert calls[-1][calls[-1].index("--plugin-dir") + 1] == str(env_framework.resolve())
    # nothing named: no framework found
    assert module.main([], env={}) == 2
    err = capsys.readouterr().err
    assert "--framework" in err and "SDLC_FRAMEWORK_DIR" in err and "framework" in err
    # the checkout beside evals/ (where the CI workflows put it)
    beside = make_framework(project / "framework")
    assert module.main(["--framework=" + str(beside)], env={}) == 1
    assert module.main([], env={}) == 1
    assert calls[-1][calls[-1].index("--plugin-dir") + 1] == str(beside.resolve())
    # an explicit choice that does not hold the runner is never replaced by the checkout
    assert module.main([], env={"SDLC_FRAMEWORK_DIR": str(tmp_path / "nowhere")}) == 2
    assert len(calls) == 3
