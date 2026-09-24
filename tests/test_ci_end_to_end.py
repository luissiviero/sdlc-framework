"""Layer-2 end-to-end run of a phase job: ``plugin/ci/run_phase.py`` invoked exactly as
``template/.github/workflows/sdlc-design.yml`` invokes it (its ``run:`` line and ``env:``),
against a fixture checkout with a bare remote, a fake ``claude`` that performs the design's
deterministic half (steps 5-7 of ``/sdlc-design`` with the plugin's own CLIs) and a fake
``gh`` that answers like GitHub - or refuses like GitHub did on the fifth live design run of
2026-09-21 ("GitHub Actions is not permitted to create or approve pull requests").

Five live runs found one fault each, at a plugin release apiece (PROGRESS, session 3); this
test is where the next fault in the CI path is found first. The model's work is recorded
text, as in ``tests/test_integration_fixture.py``; nothing leaves the machine: the remote's
fetch URL looks like GitHub so the PR client finds a repository, pushes go to the bare
repository through ``remote.origin.pushurl``, and a dead proxy makes the run's ``git fetch``
fail at once instead of reaching github.com.
"""

from __future__ import annotations

import json
import os
import re
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from state import status as status_mod
from tests.test_ci import (
    FIXTURE,
    INIT,
    NOOP_SETUP,
    ROOT,
    WORKFLOW_DIR,
    git,
    run_py,
    set_setup_command,
)
from tests.test_gate import PERCENT, TEST_PERCENT
from tests.test_integration_fixture import RECORDED_INTENT, RECORDED_PLAN, RECORDED_SPEC_BODY

STATE_CLI = ROOT / "plugin" / "state" / "cli.py"
REPO = "owner/name"
PR_URL = f"https://github.com/{REPO}/pull/7"
GH_REFUSAL = (
    "pull request create failed: GraphQL: GitHub Actions is not permitted to create or "
    "approve pull requests (createPullRequest)"
)
CHANGE = "changes/0001-percent-helper"

# The fake claude. Its argv is the one run_phase composes: it reads the plugin directory and
# the command from it, does what the command's prose says - step 0 as written (read the
# change, stop on a park, ask the preflight for (c)), then the deterministic half of the
# phase with the plugin's own CLIs - and prints the JSON the real CLI prints with
# --output-format json. The model's rule-following is the seam the ninth live run
# (2026-09-22) failed at, so the fake obeys the prose literally.
FAKE_CLAUDE = """
import json, os, subprocess, sys
from pathlib import Path

argv = sys.argv[1:]
if os.environ.get("FAKE_CLAUDE_MODE") == "idle":  # a session that gives up at once
    print("Ignoring 4 permissions.allow entries: this workspace has not been trusted",
          file=sys.stderr)
    print(json.dumps({"type": "result", "is_error": False, "num_turns": 2, "duration_ms": 900,
                      "total_cost_usd": 0.01,
                      "result": "I cannot run the build: every Bash call was denied."}))
    sys.exit(0)
plugin = Path(argv[argv.index("--plugin-dir") + 1])
command, change_id = argv[argv.index("-p") + 1].split()
phase = {"/sdlc:sdlc-design": "b", "/sdlc:sdlc-build": "c", "/sdlc:sdlc-fix": "fix"}[command]
root = Path.cwd()
state = str(plugin / "plugin" / "state" / "cli.py")
gate = str(plugin / "plugin" / "gate" / "cli.py")
preflight = str(plugin / "plugin" / "gate" / "preflight.py")
change = next(root.glob(f"changes/{change_id}-*"))


def run(*args, ok=(0,)):
    proc = subprocess.run(
        [sys.executable, *args], cwd=root, capture_output=True, text=True, encoding="utf-8"
    )
    assert proc.returncode in ok, proc.stdout + proc.stderr
    return proc.stdout


def give_up(message):  # the session stops in step 0 and reports, as the prose tells it to
    print(json.dumps({"type": "result", "is_error": False, "num_turns": 4,
                      "duration_ms": 30995, "total_cost_usd": 0.13, "result": message}))
    sys.exit(0)


# step 0: /sdlc-design reads the change and stops on a park; /sdlc-build asks the preflight
shown = json.loads(run(state, "show", "--root", ".", "--id", change_id))["status"]
if phase == "fix":  # the recorded fix round of /sdlc-fix: one comment, applied literally
    fix_phase = shown["phase"]
    if fix_phase == "abandoned":
        give_up("No fix round: the change is abandoned.")
    on = ["--branch", os.environ["FAKE_FIX_BRANCH"]] if os.environ.get("FAKE_FIX_BRANCH") else []
    run(gate, "start-run", "--root", ".", "--id", change_id, "--phase", fix_phase)
    run(gate, "bump-iteration", "--root", ".", "--id", change_id, ok=(0, 3))
    target = change / ("intent.md" if fix_phase == "a" else "spec.md")
    target.write_text(
        target.read_text(encoding="utf-8") + "\\nRevised per the owner's review comment.\\n",
        encoding="utf-8",
    )
    (change / "evidence" / "fix-response.md").write_text(
        "- comment 1: applied in the commit below\\n", encoding="utf-8"
    )
    run(state, "commit-phase", "--root", ".", "--id", change_id, "--phase", fix_phase,
        "--message", f"fix({change_id}): apply the review comment", "--push", *on)
    if fix_phase != "a":
        head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
        verdict = {"schema_version": 1, "phase": fix_phase, "head": head, "verdict": "continue",
                   "reasons": [], "classification": "routine", "classification_reasons": [],
                   "at": "2026-09-24T10:00:00Z"}
        (change / "evidence" / f"adversarial-review-{fix_phase}.json").write_text(
            json.dumps(verdict), encoding="utf-8"
        )
    run(gate, "check", "--root", ".", "--id", change_id, "--phase", fix_phase, ok=(0, 3, 4))
    run(state, "commit-phase", "--root", ".", "--id", change_id, "--phase", fix_phase,
        "--message", f"fix({change_id}): gate ({fix_phase}) evidence", "--push", *on)
    print(json.dumps({"type": "result", "is_error": False, "result": "fix round done",
                      "total_cost_usd": 0.2, "num_turns": 5}))
    sys.exit(0)
if phase == "b" and shown["parked_reason"]:
    give_up(f"Phase (b) cannot start: parked_reason is set: {shown['parked_reason']}")
if phase == "c":
    report = json.loads(
        run(preflight, "--root", ".", "--id", change_id, "--phase", "c", ok=(0, 4))
    )
    if not report["allow"]:
        give_up("Phase (c) cannot start: preflight refused: " + "; ".join(report["reasons"]))

run(gate, "start-run", "--root", ".", "--id", change_id, "--phase", phase)
if phase == "b":  # steps 5-7 of /sdlc-design
    header = json.loads(run(gate, "spec-header", "--root", ".", "--id", change_id))["header"]
    (change / "spec.md").write_text(
        header + "\\n" + os.environ["FAKE_SPEC_BODY"], encoding="utf-8"
    )
    (change / "plan.md").write_text(os.environ["FAKE_PLAN"], encoding="utf-8")
    run(state, "commit-phase", "--root", ".", "--id", change_id, "--phase", "b",
        "--message", "design(0001): percent helper", "--push")
else:  # the recorded implementation of /sdlc-build, as tests/test_integration_fixture.py
    run(state, "set-phase", "--root", ".", "--id", change_id, "--phase", "c")
    (root / "sample_pkg" / "percent.py").write_text(os.environ["FAKE_PERCENT"], encoding="utf-8")
    (root / "tests" / "test_percent.py").write_text(
        os.environ["FAKE_TEST_PERCENT"], encoding="utf-8"
    )
    init_py = root / "sample_pkg" / "__init__.py"
    init_py.write_text(
        init_py.read_text(encoding="utf-8") + "from .percent import percent  # noqa\\n",
        encoding="utf-8",
    )
    (change / "plan.md").write_text(
        os.environ["FAKE_PLAN"] + "\\nProgress: steps 1 and 2 done.\\n", encoding="utf-8"
    )
    run(state, "commit-phase", "--root", ".", "--id", change_id, "--phase", "c",
        "--message", "build(0001): percent helper", "--paths", "sample_pkg/percent.py",
        "tests/test_percent.py", "sample_pkg/__init__.py", "--push")
    (change / "evidence" / "verifier.md").write_text(
        "# Verifier\\nRan percent(1, 3) -> 33.3 and the two nearest flows; both behave.\\n",
        encoding="utf-8",
    )
panel = str(plugin / "plugin" / "panel" / "cli.py")


def write_verdict():
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
    verdict = {"schema_version": 1, "phase": phase, "head": head, "verdict": "continue",
               "reasons": [], "classification": "routine", "classification_reasons": [],
               "at": "2026-09-21T10:00:00Z"}
    (change / "evidence" / f"adversarial-review-{phase}.json").write_text(
        json.dumps(verdict), encoding="utf-8"
    )


write_verdict()
# deferred review (decision 21): the panel settles the judgment items before the gate; the
# three members are fresh contexts here stood in by recorded files, the record is the CLI's
items = json.loads(run(panel, "items", "--root", ".", "--id", change_id, "--phase", phase))
if items["mode"] == "deferred" and items["pending"]:
    for n in items["pending"]:
        for member in ("reviewer", "advocate", "conciliator"):
            run(panel, "prompt", "--root", ".", "--id", change_id, "--phase", phase,
                "--item", str(n), "--member", member)
        folder = change / "evidence" / "panel"
        (folder / f"{phase}-{n}-reviewer.md").write_text(
            "## Verdict\\nkeep half-up\\n\\n## Why\\nthe coding standard names round().\\n",
            encoding="utf-8",
        )
        (folder / f"{phase}-{n}-advocate.md").write_text(
            "## Verdict\\nno objection\\n\\n## The case against\\nnone found.\\n", encoding="utf-8"
        )
        (folder / f"{phase}-{n}-conciliator.json").write_text(
            json.dumps({"reviewer": "keep half-up", "advocate": "no objection",
                        "decision": "keep half-up rounding via round()",
                        "rationale": ["both verdicts agree", "the coding standard says so"]}),
            encoding="utf-8",
        )
        run(panel, "record", "--root", ".", "--id", change_id, "--phase", phase,
            "--item", str(n), "--cost-usd", "0.09", ok=(0, 3))
    word = "design" if phase == "b" else "build"
    run(state, "commit-phase", "--root", ".", "--id", change_id, "--phase", phase,
        "--message", f"{word}(0001): panel decisions", "--push")
    write_verdict()  # a verdict never outlives the diff it judged
run(gate, "check", "--root", ".", "--id", change_id, "--phase", phase, ok=(0, 3, 4))
word = "design" if phase == "b" else "build"
run(state, "commit-phase", "--root", ".", "--id", change_id, "--phase", phase,
    "--message", f"{word}(0001): gate ({phase}) evidence", "--push")
print(json.dumps({"type": "result", "is_error": False, "result": f"{word} done",
                  "total_cost_usd": 0.5, "num_turns": 3}))
"""

# The fake gh: every call is logged; `pr list` finds nothing (or PR #7 when its --head is
# FAKE_OPEN_PR_HEAD), `pr view <n> --json files` lists FAKE_PR_FILES, `pr view <n> --json
# <fields>` answers with PR #7 and its FAKE_PR_LABELS, `api .../issues/<n>/events` answers
# with FAKE_LABEL_EVENTS (one page), `pr create` answers with the PR URL (or refuses as
# GitHub does while the repository setting is off), `pr edit` and `label create` succeed
# silently.
FAKE_GH = """
import json, os, sys

args = sys.argv[1:]
with open(os.environ["FAKE_GH_LOG"], "a", encoding="utf-8") as log:
    log.write(json.dumps(args) + "\\n")
if "--body-file" in args and "-" in args:
    sys.stdin.read()


def open_pr(head):
    labels = json.loads(os.environ.get("FAKE_PR_LABELS", "[]"))
    return {"number": 7, "url": os.environ["FAKE_PR_URL"], "isDraft": False, "state": "OPEN",
            "mergeCommit": None, "headRefName": head, "baseRefName": "main",
            "labels": [{"name": name} for name in labels]}


if args[:2] == ["pr", "list"]:
    head = args[args.index("--head") + 1] if "--head" in args else ""
    mine = bool(head) and head == os.environ.get("FAKE_OPEN_PR_HEAD")
    print(json.dumps([open_pr(head)]) if mine else "[]")
elif args[:2] == ["pr", "view"] and args[-2:] != ["--json", "files"] and "--json" in args:
    print(json.dumps(open_pr(os.environ.get("FAKE_OPEN_PR_HEAD", "sdlc/0001/b"))))
elif args[:1] == ["api"] and "/issues/" in args[1] and "/events" in args[1]:
    page = args[1].rsplit("page=", 1)[-1]
    print(json.dumps(json.loads(os.environ.get("FAKE_LABEL_EVENTS", "[]")) if page == "1" else []))
elif args[:2] == ["pr", "view"] and args[-2:] == ["--json", "files"]:
    # the merged pull request's files, as `gh pr view <n> --json files` prints them
    paths = json.loads(os.environ.get("FAKE_PR_FILES", "[]"))
    print(json.dumps({"files": [{"path": p, "additions": 1, "deletions": 0} for p in paths]}))
elif args[:2] == ["pr", "create"]:
    if os.environ.get("FAKE_GH_MODE") == "refuse":
        print(os.environ["FAKE_GH_REFUSAL"], file=sys.stderr)
        sys.exit(1)
    print(os.environ["FAKE_PR_URL"])
elif args[:2] == ["pr", "edit"]:
    print(os.environ["FAKE_PR_URL"])
"""


def launcher(bindir: Path, name: str, script_text: str) -> Path:
    """``<bindir>/<name>`` (sh) and ``<name>.cmd`` (Windows) running ``script_text``."""
    script = bindir / f"{name}_fake.py"
    script.write_text(script_text, encoding="utf-8", newline="\n")
    sh = bindir / name
    sh.write_text(f'#!/bin/sh\nexec "{sys.executable}" "{script}" "$@"\n', encoding="utf-8")
    sh.chmod(0o755)
    cmd = bindir / f"{name}.cmd"
    cmd.write_text(f'@echo off\r\n"{sys.executable}" "{script}" %*\r\n', encoding="utf-8")
    return cmd if os.name == "nt" else sh


WORKFLOW_FILE = {"b": "sdlc-design.yml", "c": "sdlc-build.yml", "fix": "sdlc-fix.yml"}


def workflow_run_line(phase: str = "b", find: bool = False) -> list[str]:
    """The ``run:`` line of the phase's workflow, as the template ships it: the phase run,
    or with ``find`` the step before it that finds the change (``--find-change``)."""
    text = (WORKFLOW_DIR / WORKFLOW_FILE[phase]).read_text(encoding="utf-8")
    lines = re.findall(r"(?m)^\s+run: (python framework/plugin/ci/run_phase\.py .*)$", text)
    lines = [ln for ln in lines if ("--find-change" in ln) == find]
    assert len(lines) == 1, f"the run line of {WORKFLOW_FILE[phase]} moved"
    return shlex.split(lines[0])


@pytest.fixture
def checkout(tmp_path):
    """The runner's view: the project checked out on main with change 0001 merged at gate
    (a), the pinned framework beside it under ``framework/``, and a bare remote."""
    root = tmp_path / "proj"
    shutil.copytree(FIXTURE, root)
    bare = tmp_path / "remote.git"
    git(tmp_path, "init", "-q", "--bare", "-b", "main", str(bare))
    git(root, "init", "-q", "-b", "main")
    git(root, "config", "user.email", "owner@example.com")
    git(root, "config", "user.name", "Owner")
    git(root, "remote", "add", "origin", f"https://github.com/{REPO}.git")
    git(root, "config", "remote.origin.pushurl", str(bare))
    git(root, "add", ".")
    git(root, "commit", "-q", "-m", "fixture")
    git(root, "push", "-q", "-u", "origin", "main")
    proc = run_py(str(INIT), "--root", str(root), "--profile", "standard", cwd=root)
    assert proc.returncode == 0, proc.stderr
    set_setup_command(root, NOOP_SETUP)  # installs nothing, reaches no network
    git(root, "add", ".")
    git(root, "commit", "-q", "-m", "sdlc-init: connect the SDLC framework")
    git(root, "push", "-q", "origin", "main")
    proc = run_py(
        str(STATE_CLI), "new-change", "--root", str(root), "--title", "Percent helper", cwd=root
    )
    assert proc.returncode == 0, proc.stderr
    (root / CHANGE / "intent.md").write_text(RECORDED_INTENT, encoding="utf-8", newline="\n")
    proc = run_py(
        str(STATE_CLI), "commit-phase", "--root", str(root), "--id", "0001", "--phase", "a",
        "--message", "intent(0001): percent helper", "--start-point", "main", "--push",
        cwd=root,
    )  # fmt: skip
    assert proc.returncode == 0, proc.stderr
    git(root, "checkout", "-q", "main")
    git(root, "merge", "-q", "--no-edit", "sdlc/0001/a")  # gate (a): the owner's merge
    git(root, "push", "-q", "origin", "main")
    framework = root / "framework"
    ignore = shutil.ignore_patterns("__pycache__", "*.pyc")
    shutil.copytree(ROOT / "plugin", framework / "plugin", ignore=ignore)
    shutil.copytree(ROOT / ".claude-plugin", framework / ".claude-plugin", ignore=ignore)
    return root, bare


def run_phase_job(
    root: Path,
    tmp_path: Path,
    gh_mode: str,
    spec_body: str = RECORDED_SPEC_BODY,
    claude_mode: str = "design",
    phase: str = "b",
    step_env: dict | None = None,
    find: bool = False,
    run_line: list[str] | None = None,
) -> tuple:
    """Run the workflow's step with its env; return (process, parsed JSON, gh calls).

    ``step_env`` overrides the step's env block (a merge-fired run: no CHANGE_ID, the PR's
    head and number); ``find`` runs the step before the phase run that finds the change;
    ``run_line`` runs another step's line (the abandon workflow's) with the same fakes."""
    bindir = tmp_path / "bin"
    bindir.mkdir(parents=True)
    claude = launcher(bindir, "claude", FAKE_CLAUDE)
    launcher(bindir, "gh", FAKE_GH)
    gh_log = tmp_path / "gh.log"
    job_env = {  # the workflow's env: block, for a workflow_dispatch of change 0001
        "CLAUDE_CODE_OAUTH_TOKEN": "placeholder-token",  # sdlc: allow-secret
        "CHANGE_ID": "0001",
        "HEAD_REF": "",
        "REPO": REPO,
        "DEFAULT_BRANCH": "main",
        "PR_NUMBER": "",
        **(step_env or {}),
    }
    env = {k: v for k, v in os.environ.items() if k not in ("GITHUB_TOKEN", "GH_TOKEN")}
    for var in ("ANTHROPIC_API_KEY", "GITHUB_OUTPUT"):
        env.pop(var, None)
    env.update(job_env)
    env.update(
        {
            "PATH": str(bindir) + os.pathsep + env.get("PATH", ""),
            "FAKE_SPEC_BODY": spec_body,
            "FAKE_CLAUDE_MODE": claude_mode,
            "FAKE_PLAN": RECORDED_PLAN,
            "FAKE_PERCENT": PERCENT,
            "FAKE_TEST_PERCENT": TEST_PERCENT,
            "FAKE_GH_LOG": str(gh_log),
            "FAKE_GH_MODE": gh_mode,
            "FAKE_GH_REFUSAL": GH_REFUSAL,
            "FAKE_PR_URL": PR_URL,
            # the fetch URL is github.com so the PR client finds a repository; the run's
            # own `git fetch origin` must fail at once, offline, without a credential prompt
            "GIT_CONFIG_COUNT": "1",
            "GIT_CONFIG_KEY_0": "http.proxy",
            "GIT_CONFIG_VALUE_0": "http://127.0.0.1:9",
            "GIT_TERMINAL_PROMPT": "0",
        }
    )
    argv = [sys.executable if a == "python" else env.get(a[1:], "") if a.startswith("$") else a
            for a in (run_line or workflow_run_line(phase, find))]  # fmt: skip
    if os.name == "nt":
        argv += ["--claude", str(claude)]  # CreateProcess does not resolve claude.cmd on PATH
    proc = subprocess.run(
        argv, cwd=root, capture_output=True, text=True, encoding="utf-8", env=env, timeout=600
    )
    out = proc.stdout
    data = json.loads(out[out.index("{") :]) if "{" in out else None
    lines = gh_log.read_text(encoding="utf-8").splitlines() if gh_log.exists() else []
    calls = [json.loads(line) for line in lines]
    return proc, data, calls


def remote_file(bare: Path, branch: str, path: str) -> str:
    return git(bare, "show", f"refs/heads/{branch}:{path}")


def test_the_design_job_pushes_the_evidence_and_opens_the_pr(checkout, tmp_path):
    root, bare = checkout
    proc, out, calls = run_phase_job(root, tmp_path, "ok")
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert out["result"] == "wait" and out["label"] == "sdlc:b-ready"  # Standard: the owner
    assert out["dispatched"] is None and out["cost_usd"] == 0.5
    assert out["setup"]["ok"] is True and out["setup"]["command"] == NOOP_SETUP
    assert out["pr"] == {
        **out["pr"],
        "ok": True,
        "route": "gh",
        "number": 7,
        "url": PR_URL,
        "head": "sdlc/0001/b",
        "existed": False,
    }
    # the branch on the remote carries the spec, the plan and the gate's own record
    gate_file = json.loads(remote_file(bare, "sdlc/0001/b", f"{CHANGE}/evidence/gate-b.json"))
    assert gate_file["result"] == "wait" and gate_file["phase"] == "b"
    assert "## Flagged concerns" in remote_file(bare, "sdlc/0001/b", f"{CHANGE}/spec.md")
    assert "## Order of work" in remote_file(bare, "sdlc/0001/b", f"{CHANGE}/plan.md")
    assert "phase: b" in remote_file(bare, "sdlc/0001/b", f"{CHANGE}/status.yaml")
    run_file = json.loads(remote_file(bare, "sdlc/0001/b", f"{CHANGE}/evidence/run-b.json"))
    assert run_file["spend_usd"] == 0.5
    # the PR was opened from the branch against the default branch, by the framework's builder
    create = next(c for c in calls if c[:2] == ["pr", "create"])
    assert create[create.index("--repo") + 1] == REPO
    assert create[create.index("--base") + 1] == "main"
    assert create[create.index("--head") + 1] == "sdlc/0001/b"
    assert create[create.index("--title") + 1].startswith("design(0001)")
    assert "--draft" not in create  # (b) opens plain; the owner's merge is gate (b)


def test_the_design_job_is_red_when_github_refuses_the_pr(checkout, tmp_path):
    """The fifth live run: everything ran, GitHub refused `pr create` because the repository
    setting was off. The evidence still reaches the remote; the job fails and says why."""
    root, bare = checkout
    proc, out, calls = run_phase_job(root, tmp_path, "refuse")
    assert proc.returncode == 1, proc.stdout + proc.stderr
    assert "no pull request carries this phase's result" in proc.stderr
    assert "not permitted to create or approve pull requests" in proc.stderr
    assert out["pr"]["ok"] is False and out["pr"]["number"] is None
    assert "not permitted to create or approve pull requests" in out["pr"]["reason"]
    assert out["result"] == "wait" and out["cost_usd"] == 0.5  # the phase itself succeeded
    gate_file = json.loads(remote_file(bare, "sdlc/0001/b", f"{CHANGE}/evidence/gate-b.json"))
    assert gate_file["result"] == "wait"
    assert any(c[:2] == ["pr", "create"] for c in calls)


def test_a_second_dispatch_repeats_the_design_when_the_first_left_no_pr(checkout, tmp_path):
    """The sixth live run (2026-09-22): the fifth had pushed sdlc/0001/b, parked, and was
    refused the PR; the next dispatch skipped with "change 0001 is at phase b, not a" and
    nothing could move the change. A fresh runner starts on main; the run must find the
    branch, see that no pull request carries it, clear the park, run again and open it."""
    root, bare = checkout
    open_concern = RECORDED_SPEC_BODY.replace("- [x] Rounding", "- Rounding")
    proc, out, _calls = run_phase_job(root, tmp_path / "first", "refuse", open_concern)
    assert proc.returncode == 1 and out["result"] == "park" and out["pr"]["ok"] is False
    assert "parked_reason: null" not in remote_file(bare, "sdlc/0001/b", f"{CHANGE}/status.yaml")
    git(root, "checkout", "-q", "main")  # a fresh runner checks out the default branch
    proc, out, calls = run_phase_job(root, tmp_path / "second", "ok")
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "skipped" not in out
    assert out["result"] == "wait" and out["pr"]["ok"] is True and out["pr"]["number"] == 7
    status = remote_file(bare, "sdlc/0001/b", f"{CHANGE}/status.yaml")
    assert "phase: b" in status and "parked_reason: null" in status
    assert any(c[:2] == ["pr", "create"] for c in calls)


def test_a_run_that_never_reaches_its_gate_leaves_its_record_on_the_branch(checkout, tmp_path):
    """The eighth live run (2026-09-22, phase (c)) ended in 28 s with one line, "the run
    left no evidence/gate-c.json", and the runner took the CLI's result and stderr with
    it. The failure must say what the session said, and keep it on the work branch."""
    root, bare = checkout
    proc, out, _calls = run_phase_job(root, tmp_path / "idle", "ok", claude_mode="idle")
    assert proc.returncode == 1 and out is None
    assert "did not reach its gate" in proc.stderr
    assert "every Bash call was denied" in proc.stderr
    assert "not been trusted" in proc.stderr and '"num_turns": 2' in proc.stderr
    stored = json.loads(remote_file(bare, "sdlc/0001/b", f"{CHANGE}/evidence/claude-b.json"))
    assert stored["num_turns"] == 2
    stderr_file = remote_file(bare, "sdlc/0001/b", f"{CHANGE}/evidence/claude-b.stderr.txt")
    assert "not been trusted" in stderr_file
    # the next dispatch runs the phase for real on the same branch
    git(root, "checkout", "-q", "main")
    proc, out, _calls = run_phase_job(root, tmp_path / "again", "ok")
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert out["result"] == "wait" and out["pr"]["ok"] is True


def legacy_park_on(root: Path, branch: str) -> None:
    """status.yaml as plugin 0.2.5 left it on the sample repository's sdlc/0001/b and, through
    the owner's merge, on main: gate (b) passed, the reason of the lifted park still beside it."""
    git(root, "checkout", "-q", branch)
    change = root / CHANGE
    st = status_mod.read_status(change)
    assert st.gate.phase == "b" and st.gate.result == "passed" and st.parked_reason is None
    st.parked_reason = "risk_list: risk-list hit: 'auth' in spec.md: text"
    status_mod.write_status(change, st)
    git(root, "add", f"{CHANGE}/status.yaml")
    git(root, "commit", "-q", "-m", "fix(0001): gate (b) evidence and fix response for round 2")
    git(root, "push", "-q", "origin", branch)


def test_the_build_starts_although_main_carries_a_lifted_park(checkout, tmp_path):
    """The ninth and tenth live runs (2026-09-22, phase (c), plugins 0.2.6 and 0.2.7): the
    design PR merged status.yaml as plugin 0.2.5 wrote it, gate (b) passed with the old
    parked_reason still beside it. The CI guard let the change through; the session read
    the raw field, obeyed its command's "stop if parked_reason is set" and gave up after
    four turns, twice. One reader decides now: the guard rewrites the file the session
    reads on the work branch, and the preflight says whether the phase may start."""
    root, bare = checkout
    proc, out, _calls = run_phase_job(root, tmp_path / "design", "ok")
    assert proc.returncode == 0 and out["result"] == "wait"
    legacy_park_on(root, "sdlc/0001/b")
    git(root, "checkout", "-q", "main")
    git(root, "merge", "-q", "--no-edit", "sdlc/0001/b")  # gate (b): the owner's merge
    git(root, "push", "-q", "origin", "main")
    assert "risk-list hit: 'auth'" in remote_file(bare, "main", f"{CHANGE}/status.yaml")

    proc, out, calls = run_phase_job(root, tmp_path / "build", "ok", phase="c")
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "cannot start" not in proc.stderr
    assert out["result"] == "continue" and out["pr"]["ok"] is True and out["cost_usd"] == 0.5
    status = remote_file(bare, "sdlc/0001/c", f"{CHANGE}/status.yaml")
    assert "phase: c" in status and "parked_reason: null" in status
    gate_file = json.loads(remote_file(bare, "sdlc/0001/c", f"{CHANGE}/evidence/gate-c.json"))
    assert gate_file["result"] == "continue"
    assert "def percent" in remote_file(bare, "sdlc/0001/c", "sample_pkg/percent.py")
    create = next(c for c in calls if c[:2] == ["pr", "create"])
    assert "--draft" in create and create[create.index("--head") + 1] == "sdlc/0001/c"


# --- the merge of a web-session intent PR (HANDOFF 4(a), plugin 0.2.12) ----------------------
def find_step(root: Path, tmp_path: Path, head_ref: str, files: list[str]) -> tuple:
    """Run the design workflow's find step for merged PR #5 with ``head_ref``, whose files
    the fake gh lists; return (process, stdout lines, what it wrote to $GITHUB_OUTPUT)."""
    output = tmp_path / "github_output"
    step_env = {
        "CHANGE_ID": "",  # a merge event carries no dispatch input
        "HEAD_REF": head_ref,
        "PR_NUMBER": "5",
        "GITHUB_OUTPUT": str(output),
        "FAKE_PR_FILES": json.dumps(files),
    }
    proc, _data, calls = run_phase_job(root, tmp_path, "ok", step_env=step_env, find=True)
    view = [c for c in calls if c[:2] == ["pr", "view"]]
    assert view == [["pr", "view", "5", "--repo", REPO, "--json", "files"]]
    written = output.read_text(encoding="utf-8") if output.exists() else ""
    return proc, proc.stdout.splitlines(), written


def test_a_merged_web_session_intent_pr_starts_the_design(checkout, tmp_path):
    """The web platform pushed /sdlc-plan's intent to claude/relaxed-x; the old head rule
    (sdlc/<id>/a) never fired for it. The find step names the change from the PR's files,
    and the phase step runs with that id exactly as the workflow passes it."""
    root, bare = checkout
    files = [f"{CHANGE}/intent.md", f"{CHANGE}/status.yaml", "changes/README.md"]
    proc, lines, written = find_step(root, tmp_path / "find", "claude/relaxed-x", files)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert lines == ["change_id=0001", "reason="]
    assert written == "change_id=0001\n"

    found = written.strip().split("=", 1)[1]  # steps.find.outputs.change_id
    step_env = {"CHANGE_ID": found, "HEAD_REF": "claude/relaxed-x", "PR_NUMBER": "5"}
    proc, out, calls = run_phase_job(root, tmp_path / "design", "ok", step_env=step_env)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert out["change_id"] == "0001" and out["result"] == "wait"
    assert out["pr"]["ok"] is True and out["pr"]["head"] == "sdlc/0001/b"
    assert "phase: b" in remote_file(bare, "sdlc/0001/b", f"{CHANGE}/status.yaml")
    assert any(c[:2] == ["pr", "create"] for c in calls)


def test_an_unrelated_merge_finds_no_change_and_stays_green(checkout, tmp_path):
    """Any merge into the default branch starts the job now; one that carries no change
    folder prints an empty id, and the workflow skips every later step."""
    root, _bare = checkout
    proc, lines, written = find_step(root, tmp_path, "claude/docs-typo", ["README.md"])
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert lines[0] == "change_id="
    assert lines[1] == "reason=pull request #5 touches no changes/<id>-<slug>/ folder"
    assert written == "change_id=\n"
    assert "sdlc/0001/b" not in git(root, "branch", "--list")  # nothing else ran


# --- the fix round, the owner labels and abandon (decisions 22, 24, 25; plugin 0.2.13) --------
FIX_STEP_ENV = {"CHANGE_ID": "0001", "HEAD_REF": "sdlc/0001/b", "PR_NUMBER": "7"}


def _design_pr(root: Path, tmp_path: Path) -> None:
    """The design job has run: PR #7 on sdlc/0001/b waits for the owner (gate (b))."""
    proc, out, _calls = run_phase_job(root, tmp_path / "design", "ok")
    assert proc.returncode == 0 and out["result"] == "wait", proc.stdout + proc.stderr


def _fix_job(root: Path, tmp_path: Path, **env: str) -> tuple:
    step_env = {**FIX_STEP_ENV, "FAKE_OPEN_PR_HEAD": "sdlc/0001/b", "FAKE_PR_LABELS": "[]", **env}
    return run_phase_job(root, tmp_path, "ok", phase="fix", step_env=step_env)


def test_a_request_changes_review_starts_a_fix_round_on_the_design_pr(checkout, tmp_path):
    """Decision 22: the owner's review starts sdlc-fix.yml → run_phase.py --phase fix on the
    PR's head; the round applies the comment, re-runs the gate, pushes and refreshes the
    PR summary; nobody is notified (no comment, no review, no assignment)."""
    root, bare = checkout
    _design_pr(root, tmp_path)
    proc, out, calls = _fix_job(root, tmp_path / "fix")
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert out["phase"] == "fix" and out["gate_phase"] == "b" and out["change_id"] == "0001"
    assert out["result"] == "wait" and out["label"] == "sdlc:b-ready"  # the owner again
    assert out["dispatched"] is None and out["cost_usd"] == 0.2
    assert out["pr"] == {**out["pr"], "ok": True, "number": 7, "head": "sdlc/0001/b"}
    assert out["owner_labels"]["ok"] and out["owner_labels"]["performed"] == []
    spec = remote_file(bare, "sdlc/0001/b", f"{CHANGE}/spec.md")
    assert "Revised per the owner's review comment." in spec
    status = remote_file(bare, "sdlc/0001/b", f"{CHANGE}/status.yaml")
    assert "phase: b" in status and "iterations: 1" in status
    assert "applied in the commit below" in remote_file(
        bare, "sdlc/0001/b", f"{CHANGE}/evidence/fix-response.md"
    )
    run_file = json.loads(remote_file(bare, "sdlc/0001/b", f"{CHANGE}/evidence/run-b.json"))
    assert run_file["spend_usd"] == 0.2
    edit = [c for c in calls if c[:2] == ["pr", "edit"]]
    assert edit and edit[-1][2] == "7"  # the existing PR is refreshed, never a second one
    assert not any(c[:2] == ["pr", "create"] for c in calls)
    for verb in ("comment", "review"):
        assert not any(verb in c for c in calls), calls


def test_an_owner_label_is_performed_before_the_round_and_a_bot_s_is_refused(checkout, tmp_path):
    """Decision 24: sdlc:reset-iterations applied by the owner resets the count and records
    the actor; the run commits that under the automation identity and the gate's
    owner_actions check accepts it; sdlc:unlock-tests applied by a bot stays on the PR."""
    root, bare = checkout
    _design_pr(root, tmp_path)
    git(root, "checkout", "-q", "sdlc/0001/b")
    change = root / CHANGE
    st = status_mod.read_status(change)
    st.iterations = 3  # three rounds spent: the next one would park at the cap
    status_mod.write_status(change, st)
    git(root, "add", f"{CHANGE}/status.yaml")
    git(root, "commit", "-q", "-m", "fix(0001): three rounds")
    git(root, "push", "-q", "origin", "sdlc/0001/b")
    git(root, "config", "--unset", "user.name")  # the runner commits as the automation identity
    git(root, "config", "--unset", "user.email")
    (tmp_path / "gitconfig").write_text("", encoding="utf-8")
    events = [
        {"event": "labeled", "label": {"name": "sdlc:reset-iterations"},
         "actor": {"login": "luissiviero"}},
        {"event": "labeled", "label": {"name": "sdlc:unlock-tests"},
         "actor": {"login": "github-actions[bot]"}},
    ]  # fmt: skip
    proc, out, calls = _fix_job(
        root,
        tmp_path / "fix",
        FAKE_PR_LABELS=json.dumps(["sdlc:b-ready", "sdlc:reset-iterations", "sdlc:unlock-tests"]),
        FAKE_LABEL_EVENTS=json.dumps(events),
        GIT_CONFIG_GLOBAL=str(tmp_path / "gitconfig"),
        GIT_CONFIG_NOSYSTEM="1",
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    labels = out["owner_labels"]
    assert labels["performed"] == [{"label": "sdlc:reset-iterations", "actor": "luissiviero"}]
    assert labels["rejected"][0]["label"] == "sdlc:unlock-tests"
    assert "cannot un-park itself" in labels["rejected"][0]["reason"]
    assert labels["removed"] == ["sdlc:reset-iterations"] and labels["commit"]["ok"]
    assert out["result"] == "wait"  # the round ran and the gate passed: no park at the cap
    status = remote_file(bare, "sdlc/0001/b", f"{CHANGE}/status.yaml")
    assert "iterations: 1" in status and "iterations_reset_by: luissiviero" in status
    assert "tests_unlocked_by: null" in status
    log = git(bare, "log", "--format=%an|%s", "refs/heads/sdlc/0001/b")
    assert "github-actions[bot]|owner labels applied: sdlc:reset-iterations" in log
    gate_file = json.loads(remote_file(bare, "sdlc/0001/b", f"{CHANGE}/evidence/gate-b.json"))
    owner = next(ch for ch in gate_file["checks"] if ch["name"] == "owner_actions")
    assert owner["ok"] and owner["details"]["label_actors"] == {"iterations_reset": "luissiviero"}
    removal = next(c for c in calls if c[:2] == ["pr", "edit"] and "--remove-label" in c)
    assert removal[removal.index("--remove-label") + 1] == "sdlc:reset-iterations"
    assert "sdlc:unlock-tests" not in removal


def test_a_fix_round_on_a_web_session_intent_pr_edits_the_intent_on_its_own_head(
    checkout, tmp_path
):
    """Decision 22 at gate (a): the intent PR was pushed from claude/relaxed-y (no
    sdlc/<id>/a); the round runs on that head, corrects intent.md there and refreshes PR #7."""
    root, bare = checkout
    proc = run_py(
        str(STATE_CLI), "new-change", "--root", str(root), "--title", "Second idea", cwd=root
    )
    assert proc.returncode == 0, proc.stderr
    second = "changes/0002-second-idea"
    (root / second / "intent.md").write_text(
        RECORDED_INTENT.replace("0001", "0002"), encoding="utf-8", newline="\n"
    )
    git(root, "checkout", "-q", "-b", "claude/relaxed-y", "main")
    git(root, "add", second)
    git(root, "commit", "-q", "-m", "intent(0002): second idea")
    git(root, "push", "-q", "-u", "origin", "claude/relaxed-y")
    git(root, "checkout", "-q", "main")
    proc, out, calls = run_phase_job(
        root, tmp_path / "fix", "ok", phase="fix",
        step_env={"CHANGE_ID": "0002", "HEAD_REF": "claude/relaxed-y", "PR_NUMBER": "7",
                  "FAKE_OPEN_PR_HEAD": "claude/relaxed-y", "FAKE_PR_LABELS": "[]",
                  "FAKE_FIX_BRANCH": "claude/relaxed-y"},
    )  # fmt: skip
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert out["gate_phase"] == "a" and out["result"] == "wait" and out["label"] == "sdlc:a-ready"
    assert out["pr"]["ok"] and out["pr"]["head"] == "claude/relaxed-y"
    intent = remote_file(bare, "claude/relaxed-y", f"{second}/intent.md")
    assert "Revised per the owner's review comment." in intent
    assert "phase: a" in remote_file(bare, "claude/relaxed-y", f"{second}/status.yaml")
    assert "sdlc/0002/a" not in git(bare, "branch", "--list")  # nothing else was pushed
    edit = next(c for c in calls if c[:2] == ["pr", "edit"])
    assert edit[2] == "7" and not any(c[:2] == ["pr", "create"] for c in calls)
    listed = next(c for c in calls if c[:2] == ["pr", "list"])
    assert listed[listed.index("--head") + 1] == "claude/relaxed-y"


def abandon_run_line() -> list[str]:
    text = (WORKFLOW_DIR / "sdlc-abandon.yml").read_text(encoding="utf-8")
    lines = re.findall(r"(?m)^\s+run: (python framework/plugin/state/cli\.py abandon .*)$", text)
    assert len(lines) == 1
    return [
        re.sub(r"\$(\w+)", lambda m: {"CHANGE_ID": "0001", "PR_NUMBER": "7"}[m.group(1)], a)
        for a in shlex.split(lines[0])
    ]


def test_a_pr_closed_without_a_merge_abandons_the_change_and_every_run_skips_it(checkout, tmp_path):
    """Decision 25: the owner closes design PR #7; the abandon workflow finds the change
    from the PR (its head here), records the end state on every branch of the change and
    keeps the branches; a later dispatch of the design or a fix round skips."""
    root, bare = checkout
    _design_pr(root, tmp_path)
    git(root, "checkout", "-q", "sdlc/0001/b")  # the abandon job checks the head out
    step_env = {"CHANGE_ID": "", "HEAD_REF": "sdlc/0001/b", "PR_NUMBER": "7"}
    proc, _data, _calls = run_phase_job(
        root, tmp_path / "find", "ok", phase="fix", step_env=step_env, find=True
    )
    assert proc.returncode == 0 and proc.stdout.splitlines()[0] == "change_id=0001"
    proc, _data, _calls = run_phase_job(
        root,
        tmp_path / "abandon",
        "ok",
        phase="fix",
        step_env=step_env,
        run_line=abandon_run_line(),
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    out = json.loads(proc.stdout[proc.stdout.index("{") :])
    assert out["phase"] == "abandoned" and out["reason"] == "pull request 7 closed without a merge"
    assert sorted(b["branch"] for b in out["branches"]) == ["sdlc/0001/a", "sdlc/0001/b"]
    for branch in ("sdlc/0001/a", "sdlc/0001/b"):
        assert "phase: abandoned" in remote_file(bare, branch, f"{CHANGE}/status.yaml")
    assert "## Flagged concerns" in remote_file(bare, "sdlc/0001/b", f"{CHANGE}/spec.md")
    # a fresh runner dispatches the design again, or a review starts a fix round: both skip
    git(root, "checkout", "-q", "main")
    git(root, "branch", "-q", "-D", "sdlc/0001/b")
    proc, out, _calls = run_phase_job(root, tmp_path / "design-again", "ok")
    assert proc.returncode == 0 and out == {
        "skipped": "change 0001 is abandoned: pull request 7 closed without a merge"
    }
    proc, out, _calls = _fix_job(root, tmp_path / "fix-again")
    assert proc.returncode == 0 and out["skipped"].startswith("change 0001 is abandoned")


# --- deferred review (decision 21; plugin 0.2.14) --------------------------------------------
def test_under_deferred_review_the_panel_closes_the_concern_and_the_pr_says_so(checkout, tmp_path):
    """The design run leaves one open concern. Under review: parked it parks (the third
    test above). Under review: deferred the run puts it to the panel, records the decision,
    commits (``record`` does), re-runs the verdict, and the gate waits for the owner with
    the decision at the top of the PR body; one panel call was spent, no fix iteration."""
    root, bare = checkout
    change = root / CHANGE
    st = status_mod.read_status(change)
    st.review_override = "deferred"  # the per-change switch; sdlc.yaml stays as merged
    status_mod.write_status(change, st)
    git(root, "add", f"{CHANGE}/status.yaml")
    git(root, "commit", "-q", "-m", "intent(0001): deferred review for this change")
    git(root, "push", "-q", "origin", "main")
    open_concern = RECORDED_SPEC_BODY.replace("- [x] Rounding", "- Rounding")
    proc, out, calls = run_phase_job(root, tmp_path, "ok", open_concern)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert out["result"] == "wait" and out["label"] == "sdlc:b-ready"
    spec = remote_file(bare, "sdlc/0001/b", f"{CHANGE}/spec.md")
    assert "- decided (by panel #1): keep half-up rounding via round() — Rounding" in spec
    ledger_md = remote_file(bare, "sdlc/0001/b", f"{CHANGE}/evidence/decisions-b.md")
    assert "1. [concern] Rounding" in ledger_md and "cost: $0.09" in ledger_md
    ledger_json = json.loads(
        remote_file(bare, "sdlc/0001/b", f"{CHANGE}/evidence/decisions-b.json")
    )
    assert ledger_json["decisions"][0]["decision"] == "keep half-up rounding via round()"
    status = remote_file(bare, "sdlc/0001/b", f"{CHANGE}/status.yaml")
    assert "panel_calls: 1" in status and "iterations: 0" in status  # not a fix iteration
    log = git(root, "log", "--format=%s", "origin/main..origin/sdlc/0001/b")
    assert "design(0001): panel decision 1" in log  # record committed the decision itself
    gate_file = json.loads(remote_file(bare, "sdlc/0001/b", f"{CHANGE}/evidence/gate-b.json"))
    assert gate_file["result"] == "wait"
    names = {ch["name"]: ch["ok"] for ch in gate_file["checks"]}
    assert names["open_concerns"] and names["panel"] and names["adversarial_review"]
    assert any(c[:2] == ["pr", "create"] for c in calls)
    # the body went through stdin: read it from the description builder on the branch
    git(root, "checkout", "-q", "sdlc/0001/b")
    from pr import description as desc

    text = desc.build_description(root, "0001", "b")
    assert text.startswith("**Decisions taken for you (1)**")
    assert "[concern] Rounding half-even vs half-up" in text
    assert "0 open / 1 closed" in text  # the concern reads as closed in the bullets
