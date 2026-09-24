"""Layer-1 tests for plugin/pr: the generated PR description (the five bullets in their
fixed order for phases b, c, d and e, the parked block, the counters and the links), the
`upsert --dry-run` contract the phase commands call, the three routes of the GitHub client
(with `gh` off PATH and `_request` monkeypatched, so nothing leaves the process) and the
daily digest (build guide step 27a, decision 20)."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
from pr import cli as pr_cli
from pr import description as desc
from pr import digest as digest_mod
from pr import github

from gate import artifacts as art
from gate import preflight
from state import conventions as c
from state import status as status_mod

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "sample-python-project"
INIT = ROOT / "plugin" / "init" / "sdlc_init.py"
STATE_CLI = ROOT / "plugin" / "state" / "cli.py"
PLUGIN_VERSION = json.loads((ROOT / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))[
    "version"
]
CHANGE_DIR_NAME = "0001-percent-helper"

INTENT = """# Intent: percent helper
Author: owner (developer). Status: accepted. Change id: 0001. Entry route: idea.

## Problem
Callers compute percentages by hand and get rounding wrong. It shows up in invoices.

## Proposed outcome
`sample_pkg.percent(part, whole)` returns a rounded percentage; covered by tests.

## Affected users and systems
sample_pkg users.

## Constraints
No new dependencies.

## Open questions
none
"""

SPEC_HEADER = art.render_spec_header(
    "percent helper", "0001", PLUGIN_VERSION, list(preflight.POLICY_SKILLS), []
)
SPEC_BODY = """
## Requirements
- percent(part, whole) returns part / whole * 100 rounded to one decimal.

## Design
A pure function in sample_pkg/percent.py exported from the package. Nothing else moves.

## Open questions from intent
- Rounding mode: answered, half-up.
- Locale-aware formatting: carried forward to a later change.

## Flagged concerns
- [x] Rounding half-even vs half-up: decided half-up via round() (documented).
- Invoices may depend on the old behaviour; nobody has checked.

## Acceptance
Tests in tests/test_percent.py pass; lint clean.
"""
SPEC = SPEC_HEADER + "\n" + SPEC_BODY

PLAN = """# Plan: percent helper

## Files that change
- `sample_pkg/percent.py` — new: percent(part, whole)

## Order of work
1. Add the function and its test.

## Risks
Rounding; nothing else.

## Options not taken
Decimal module: overkill.

## Proof
tests/test_percent.py::test_percent_rounds
"""


# --- helpers ------------------------------------------------------------------------------
def git(cwd: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=cwd, capture_output=True, text=True, check=True, encoding="utf-8"
    ).stdout


def run_py(*args: str, cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        env=os.environ.copy(),
        encoding="utf-8",
    )


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def bullets(body: str) -> list[str]:
    """The leading bullet block of the body: every line until the first non-bullet line."""
    out = []
    for line in body.splitlines():
        if line.startswith("- "):
            out.append(line)
        elif out:
            break
    return out


def gate_json(
    change_dir: Path,
    phase: str,
    result: str,
    label: str | None,
    plan_sync_ok: bool = True,
    with_block: bool = True,
) -> dict:
    """``evidence/gate-<phase>.json`` in the shape ``GateResult.as_dict()`` writes."""
    checks = [
        {
            "name": "artifacts",
            "ok": True,
            "reason": "every artifact matches",
            "need": "",
            "details": {},
        },
        {
            "name": "plan_sync",
            "ok": plan_sync_ok,
            "reason": (
                "every changed source file is in plan.md"
                if plan_sync_ok
                else "2 changed file(s) not listed in plan.md"
            ),
            "need": (
                ""
                if plan_sync_ok
                else "Update '## Files that change' in plan.md to match the diff."
            ),
            "details": {},
        },
    ]
    if result == "park":
        checks.append(
            {
                "name": "risk_list",
                "ok": False,
                "reason": "the diff touches the risk-list item 'auth'",
                "need": "Accept the risk with state/cli.py accept-risk, or split the change.",
                "details": {},
            }
        )
    data = {
        "schema_version": 1,
        "change_id": "0001",
        "slug": "percent-helper",
        "phase": phase,
        "profile": "standard",
        "human_gate": result == "wait",
        "result": result,
        "label": label,
        "head": "0123456789abcdef0123456789abcdef01234567",
        "at": "2026-09-21T10:00:00Z",
        "dry_run": False,
        "reason": "; ".join(f"{ch['name']}: {ch['reason']}" for ch in checks if not ch["ok"]),
        "config_note": "",
        "checks": checks,
    }
    if with_block:
        failed = [ch for ch in checks if not ch["ok"]]
        lines = [
            "## What I need from you",
            f"Gate ({phase}) parked change 0001 (percent-helper) on 2026-09-21T10:00:00Z.",
        ]
        for ch in failed:
            lines.append(f"- **{ch['name']}**: {ch['reason']}")
            if ch["need"]:
                lines.append(f"  - what I need: {ch['need']}")
        data["what_i_need"] = "\n".join(lines) + "\n" if result == "park" else ""
    write(
        change_dir / art.EVIDENCE_DIR / art.GATE_RESULT.format(phase=phase),
        json.dumps(data, indent=2),
    )
    return data


def logs(change_dir: Path, exit_code: int | None = 0) -> None:
    """The three command logs with the header plugin/evidence/collect.py writes."""
    for name, command in (
        (art.EVIDENCE_TEST, "python -m pytest"),
        (art.EVIDENCE_BUILD, "python -m build"),
        (art.EVIDENCE_LINT, "ruff check ."),
    ):
        header = art.render_evidence_header(command, exit_code, 1.2, "2026-09-21T10:00:00Z")
        write(change_dir / art.EVIDENCE_DIR / name, header + "\nall good\n")


def findings(change_dir: Path, important: int = 0, nits: int = 0) -> None:
    items = [
        {"pass": "bugs", "severity": "important", "file": "a.py", "line": i, "summary": f"bug {i}"}
        for i in range(important)
    ]
    items += [
        {"pass": "bugs", "severity": "nit", "file": "a.py", "line": i, "summary": f"nit {i}"}
        for i in range(nits)
    ]
    write(
        change_dir / art.EVIDENCE_DIR / art.REVIEW_FINDINGS,
        json.dumps(
            {
                "schema_version": 1,
                "head": "0123456789abcdef",
                "findings": items,
                "tally": {"important": important, "nit": nits},
            }
        ),
    )


@pytest.fixture
def project(tmp_path):
    """A fixture copy, initialised, with change 0001 and its three artifacts written by hand."""
    root = tmp_path / "proj"
    shutil.copytree(FIXTURE, root)
    git(root, "init", "-q", "-b", "main")
    git(root, "config", "user.email", "owner@example.com")
    git(root, "config", "user.name", "Owner")
    git(root, "add", ".")
    git(root, "commit", "-q", "-m", "fixture")
    proc = run_py(str(INIT), "--root", str(root), "--profile", "standard", cwd=root)
    assert proc.returncode == 0, proc.stderr
    git(root, "add", ".")
    git(root, "commit", "-q", "-m", "sdlc-init")
    proc = run_py(
        str(STATE_CLI), "new-change", "--root", str(root), "--title", "Percent helper", cwd=root
    )
    assert proc.returncode == 0, proc.stderr
    change = root / "changes" / CHANGE_DIR_NAME
    write(change / "intent.md", INTENT)
    write(change / "spec.md", SPEC)
    write(change / "plan.md", PLAN)
    git(root, "add", ".")
    git(root, "commit", "-q", "-m", "intent, spec and plan")
    return root, change


# --- the five bullets ----------------------------------------------------------------------
def test_five_bullets_at_phase_a_describe_the_intent(project):
    root, change = project
    write(
        change / "intent.md",
        INTENT.replace("## Open questions\nnone", "## Open questions\n- Which rounding mode?\n"),
    )
    body = desc.build_description(root, "0001", "a")  # no gate file exists at (a)
    lines = bullets(body)
    assert len(lines) == 5
    heads = [line.split("**")[1] for line in lines]
    assert heads == [
        "What changed and why",
        "Entry route",
        "Affected users and systems",
        "Open questions",
        "What needs you",
    ]
    assert lines[0] == (
        "- **What changed and why**: Percent helper: Callers compute percentages by hand "
        "and get rounding wrong."
    )
    assert lines[1].endswith("idea route, feature change")
    assert lines[2].endswith("sample_pkg users.")
    assert lines[3].endswith("1 open: Which rounding mode?")
    assert lines[4].endswith("read, correct via review comments, merge = approve (gate (a))")
    # phase (a) links only the artifact that exists, and carries the counters
    assert f"Links: changes/{CHANGE_DIR_NAME}/intent.md" in body
    assert "spec.md" not in body and "gate-a.json" not in body
    assert "Counters: first-pass merge: yes · fix iterations: 0" in body


def test_phase_a_open_questions_none_and_default_label(project):
    root, change = project
    assert bullets(desc.build_description(root, "0001", "a"))[3].endswith("none")
    st = status_mod.read_status(change)
    assert desc.pr_title(st, "a") == "intent(0001): Percent helper"
    assert desc.head_branch("0001", "a") == "sdlc/0001/a"
    assert desc.label_for(None, "a") == "sdlc:a-ready"  # no gate file at (a)
    assert desc.label_for(None, "c") is None


def test_five_bullets_in_order_at_phase_b(project):
    root, change = project
    gate_json(change, "b", "wait", c.ready_label("b"))
    body = desc.build_description(root, "0001", "b")
    lines = bullets(body)
    assert len(lines) == 5
    heads = [line.split("**")[1] for line in lines]
    assert heads == [
        "What changed and why",
        "Evidence",
        "Review findings",
        "Plan conformance",
        "What needs you",
    ]
    assert "Percent helper (feature, idea route)" in lines[0]
    assert "Callers compute percentages by hand and get rounding wrong." in lines[0]
    assert "Design: A pure function in sample_pkg/percent.py exported from the package." in lines[0]
    assert lines[1].endswith("design phase, no code yet")
    # phase (b): the flagged concerns, with the open one quoted verbatim
    assert "1 open / 1 closed" in lines[2]
    assert "Invoices may depend on the old behaviour; nobody has checked." in lines[2]
    assert "open questions from intent: 1 answered / 1 carried forward" in lines[3]
    # the four questions of build guide step 23
    assert "Does the spec solve the problem the intent states?" in lines[4]
    assert "Merge = approve; a review comment = change request (/sdlc-fix)." in lines[4]


def test_phase_c_evidence_missing_and_not_yet_reviewed(project):
    root, change = project
    gate_json(change, "c", "continue", None)
    body = desc.build_description(root, "0001", "c")
    lines = bullets(body)
    assert len(lines) == 5
    assert "test missing, build missing, lint missing" in lines[1]
    assert "verifier.md missing" in lines[1] and "0 screenshot(s)" in lines[1]
    assert lines[2].endswith("not yet reviewed")
    assert "diff matches plan.md" in lines[3]
    assert "nothing: the run continues to the next phase" in lines[4]


def test_phase_d_green_logs_and_full_profile_checklist(project):
    root, change = project
    logs(change, exit_code=0)
    write(change / art.EVIDENCE_DIR / art.EVIDENCE_VERIFIER, "# Verifier\nRan it.\n")
    write(change / art.EVIDENCE_DIR / desc.SCREENSHOT_DIR / "home.png", "png")
    findings(change, important=0, nits=2)
    gate_json(change, "d", "wait", c.ready_label("d"))
    lines = bullets(desc.build_description(root, "0001", "d"))
    assert "test green, build green, lint green" in lines[1]
    assert "verifier.md present" in lines[1] and "1 screenshot(s)" in lines[1]
    assert "0 Important, 2 nits (nit 0; nit 1)" in lines[2]
    assert "sdlc:d-approved" in lines[4]


def test_red_log_is_red(project):
    root, change = project
    logs(change, exit_code=1)
    gate_json(change, "d", "park", c.NEEDS_HUMAN_LABEL)
    lines = bullets(desc.build_description(root, "0001", "d"))
    assert "test red, build red, lint red" in lines[1]


def test_phase_e_release_note_and_counters(project):
    root, change = project
    logs(change)
    write(change / art.EVIDENCE_DIR / art.EVIDENCE_VERIFIER, "# Verifier\n")
    findings(change, important=0, nits=1)
    gate_json(change, "e", "wait", c.ready_label("e"))
    body = desc.build_description(root, "0001", "e")
    assert len(bullets(body)) == 5
    assert "merge = approve; a review comment is the change request (/sdlc-fix)" in body
    assert "## Release note" in body
    assert "returns a rounded percentage" in body.split("## Release note")[1]
    assert "Counters: first-pass merge: yes · fix iterations: 0" in body
    # relative repository paths when the fixture has no GitHub remote
    assert f"changes/{CHANGE_DIR_NAME}/intent.md" in body
    assert f"changes/{CHANGE_DIR_NAME}/evidence/gate-e.json" in body
    # waiting for the owner's merge; the release workflow runs after it (build guide step 32)
    assert "merge = gate (e) passed; the release workflow then runs `deploy.command`" in body
    # the fixture declares no production: merge is the whole gate (decision 13)
    assert "Release approval" not in body and "sdlc:release-approved" not in body


RELEASE_NOTES = """# Release notes — change 0001: Percent helper

## What changed

- `sample_pkg.percent(part, whole)` added.

## Evidence

test green, build green, lint green
"""


def test_phase_e_release_note_quotes_the_release_notes_file(project):
    """32.2: at (e) the "## Release note" section is evidence/release-notes.md verbatim,
    without its H1 title; the intent's proposed outcome is only the fallback."""
    root, change = project
    logs(change)
    gate_json(change, "e", "wait", c.ready_label("e"))
    write(change / art.EVIDENCE_DIR / desc.RELEASE_NOTES, RELEASE_NOTES)
    body = desc.build_description(root, "0001", "e")
    assert len(bullets(body)) == 5
    note = body.split("## Release note\n")[1]
    assert note.startswith("\n### What changed\n\n- `sample_pkg.percent(part, whole)` added.\n")
    assert "### Evidence\n\ntest green, build green, lint green" in note
    # the file's headings are demoted one level so they nest under "## Release note"
    assert "\n## What changed" not in body and "\n## Evidence" not in body
    assert "# Release notes — change 0001" not in body
    assert "returns a rounded percentage" not in note  # the fallback is not used


def test_phase_e_release_note_falls_back_to_the_intent_outcome(project):
    root, change = project
    gate_json(change, "e", "wait", c.ready_label("e"))
    write(change / art.EVIDENCE_DIR / desc.RELEASE_NOTES, "# Release notes — change 0001\n\n")
    body = desc.build_description(root, "0001", "e")
    assert "returns a rounded percentage" in body.split("## Release note")[1]


def _declare_production(root: Path, value: str) -> None:
    config = root / "sdlc.yaml"
    text = config.read_text(encoding="utf-8")
    lines = [
        f"  production: {value}" if line.strip().startswith("production:") else line
        for line in text.splitlines()
    ]
    assert sum(line.strip().startswith("production:") for line in text.splitlines()) == 1
    write(config, "\n".join(lines) + "\n")


def test_release_approval_line_only_when_production_is_declared(project):
    """Decision 13: with `deploy.production: true` the release label is the second act; the
    line sits below the five bullets (not a sixth bullet) and only at phase (e)."""
    root, change = project
    logs(change)
    gate_json(change, "e", "wait", c.ready_label("e"))
    gate_json(change, "d", "continue", None)
    _declare_production(root, "true")
    body = desc.build_description(root, "0001", "e")
    assert len(bullets(body)) == 5
    line = (
        "Release approval: apply `sdlc:release-approved` on this PR after merging; the "
        "release workflow waits for it."
    )
    assert line in body.splitlines()
    assert "signed tag" not in body  # decision 11: the label is the only route
    assert body.index(line) > body.index(bullets(body)[-1]) and body.index(line) < body.index(
        "Links:"
    )
    assert line not in desc.build_description(root, "0001", "d")
    _declare_production(root, "false")
    assert line not in desc.build_description(root, "0001", "e")


def test_counters_after_a_fix_round(project):
    root, change = project
    st = status_mod.read_status(change)
    st.iterations = 3
    status_mod.write_status(change, st)
    gate_json(change, "c", "continue", None)
    body = desc.build_description(root, "0001", "c")
    assert "Counters: first-pass merge: no · fix iterations: 3" in body


def test_claude_md_proposals_block(project):
    root, change = project
    gate_json(change, "e", "wait", c.ready_label("e"))
    write(
        change / art.EVIDENCE_DIR / desc.CLAUDE_MD_PROPOSALS,
        "- Always pass encoding='utf-8' to open().\n",
    )
    body = desc.build_description(root, "0001", "e")
    assert "## Proposed CLAUDE.md lines" in body
    assert "> - Always pass encoding='utf-8' to open()." in body


# --- parked --------------------------------------------------------------------------------
def test_parked_body_carries_what_i_need_from_you(project):
    root, change = project
    data = gate_json(change, "c", "park", c.NEEDS_HUMAN_LABEL)
    body = desc.build_description(root, "0001", "c")
    lines = bullets(body)
    assert len(lines) == 5
    assert "parked at gate (c)" in lines[4] and "nobody was notified" in lines[4]
    assert data["what_i_need"].strip() in body
    assert "the diff touches the risk-list item 'auth'" in body
    assert "what I need: Accept the risk with state/cli.py accept-risk" in body


def test_parked_block_rebuilt_when_the_json_does_not_carry_it(project):
    root, change = project
    gate_json(change, "c", "park", c.NEEDS_HUMAN_LABEL, with_block=False)
    body = desc.build_description(root, "0001", "c")
    assert "## What I need from you" in body
    assert "Gate (c) parked change 0001 (percent-helper)" in body
    assert "- **risk_list**: the diff touches the risk-list item 'auth'" in body
    assert "re-run the gate" in body


def test_plan_conformance_reports_the_failed_check(project):
    root, change = project
    gate_json(change, "c", "park", c.NEEDS_HUMAN_LABEL, plan_sync_ok=False)
    lines = bullets(desc.build_description(root, "0001", "c"))
    assert "2 changed file(s) not listed in plan.md" in lines[3]


def test_no_gate_file_means_nothing_needed(project):
    root, _change = project
    lines = bullets(desc.build_description(root, "0001", "c"))
    assert "nothing: the run continues to the next phase" in lines[4]


# --- titles, labels, branches -----------------------------------------------------------------
def test_pr_title_and_label_and_branch(project):
    _root, change = project
    st = status_mod.read_status(change)
    assert desc.pr_title(st, "b") == "design(0001): Percent helper"
    for phase in ("c", "d", "e"):
        assert desc.pr_title(st, phase) == "build(0001): Percent helper"
    assert desc.head_branch("0001", "b") == "sdlc/0001/b"
    assert all(desc.head_branch("0001", p) == "sdlc/0001/c" for p in ("c", "d", "e"))
    assert desc.label_for({"label": "sdlc:e-ready"}) == "sdlc:e-ready"
    assert desc.label_for({"label": None}) is None
    assert desc.label_for(None) is None


# --- the CLI ------------------------------------------------------------------------------
def test_upsert_dry_run_contacts_nothing(project, capsys, monkeypatch):
    root, change = project
    gate_json(change, "c", "park", c.NEEDS_HUMAN_LABEL)

    def boom(*_args, **_kwargs):  # any HTTP call in a dry run is a bug
        raise AssertionError("--dry-run must contact nothing")

    monkeypatch.setattr(github, "_request", boom)
    monkeypatch.setattr(github.shutil, "which", lambda *_a, **_k: None)
    code = pr_cli.main(
        ["upsert", "--root", str(root), "--id", "0001", "--phase", "c", "--draft", "--dry-run"]
    )
    assert code == 0
    out = json.loads(capsys.readouterr().out)
    assert out["route"] == "dry-run"
    assert out["head"] == "sdlc/0001/c" and out["base"] == "main"
    assert out["label"] == c.NEEDS_HUMAN_LABEL
    assert out["title"] == "build(0001): Percent helper"
    assert out["created"] is False and out["number"] is None
    assert "## What I need from you" in out["body"]


def test_description_subcommand_prints_the_body_only(project, capsys):
    root, change = project
    gate_json(change, "b", "wait", c.ready_label("b"))
    assert pr_cli.main(["description", "--root", str(root), "--id", "0001", "--phase", "b"]) == 0
    out = capsys.readouterr().out
    assert out.startswith("- **What changed and why**:")
    assert len(bullets(out)) == 5


def test_cli_unknown_change_exits_2(project, capsys):
    root, _change = project
    assert pr_cli.main(["description", "--root", str(root), "--id", "0099", "--phase", "c"]) == 2
    assert "no change folder" in capsys.readouterr().err


def test_check_run_without_remote_reports_route_none(project, capsys):
    root, change = project
    gate_json(change, "d", "park", c.NEEDS_HUMAN_LABEL)
    logs(change, exit_code=1)
    assert pr_cli.main(["check-run", "--root", str(root), "--id", "0001", "--phase", "d"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["route"] == "none" and out["conclusion"] == "failure"
    assert out["name"] == "sdlc/d" and "test red" in out["summary"]


def test_upsert_posts_the_phase_check_run_when_asked(project, capsys, monkeypatch):
    """The phase (d) runbook line is one command: upsert --check-run (build guide step 28)."""
    root, change = project
    gate_json(change, "d", "park", c.NEEDS_HUMAN_LABEL)
    logs(change, exit_code=1)
    monkeypatch.setattr(github.shutil, "which", lambda *_a, **_k: None)
    posted: list[tuple] = []
    monkeypatch.setattr(
        github,
        "create_check_run",
        lambda *args: posted.append(args) or {"route": "api", "ok": True, "id": 3},
    )
    code = pr_cli.main(
        ["upsert", "--root", str(root), "--id", "0001", "--phase", "d", "--check-run"]
    )
    assert code == 0
    out = json.loads(capsys.readouterr().out)
    assert out["check_run"]["name"] == "sdlc/d"
    assert out["check_run"]["conclusion"] == "failure"  # the gate parked
    assert "test red" in out["check_run"]["summary"]  # the evidence summary, as posted
    # without the flag nothing is posted at all
    assert pr_cli.main(["upsert", "--root", str(root), "--id", "0001", "--phase", "d"]) == 0
    assert "check_run" not in json.loads(capsys.readouterr().out)


def test_label_colours(project):
    assert pr_cli.label_color(c.NEEDS_HUMAN_LABEL) == "D93F0B"
    assert pr_cli.label_color(c.ready_label("c")) == "0E8A16"


# --- the GitHub client ------------------------------------------------------------------------
@pytest.fixture
def no_gh(monkeypatch):
    """No `gh` on PATH: every route decision falls to the token."""
    monkeypatch.setattr(github.shutil, "which", lambda *_a, **_k: None)
    for var in github.TOKEN_VARS:
        monkeypatch.delenv(var, raising=False)


@pytest.fixture
def fake_gh(monkeypatch):
    """A ``gh`` on PATH that runs nothing: it records (args, stdin, cwd) and answers from a
    queue of ``_gh`` results (an empty queue means success with no output)."""
    calls: list[dict] = []
    answers: list[dict] = []

    def run(*args, stdin=None, cwd=None):
        calls.append({"args": list(args), "stdin": stdin, "cwd": cwd})
        return answers.pop(0) if answers else {"ok": True, "code": 0, "out": "", "err": ""}

    monkeypatch.setattr(github, "gh_path", lambda: "/usr/bin/gh")
    monkeypatch.setattr(github, "_gh", run)
    return calls, answers


@pytest.fixture
def gh_only(monkeypatch, fake_gh):
    """``gh`` and no token: the fallback route on its own."""
    for var in github.TOKEN_VARS:
        monkeypatch.delenv(var, raising=False)
    return fake_gh


@pytest.fixture
def recorder(monkeypatch, no_gh):
    """Record every call to the single HTTP entry point and answer from a canned table."""
    calls: list[tuple] = []
    answers: dict[tuple[str, str], dict] = {}

    def fake(method, url, tok, payload=None):
        assert tok == "secret-token"
        calls.append((method, url, payload))
        for (m, fragment), answer in answers.items():
            if m == method and fragment in url:
                return answer
        return {"status": 200, "data": {}, "error": ""}

    monkeypatch.setenv("GITHUB_TOKEN", "secret-token")
    monkeypatch.setattr(github, "_request", fake)
    return calls, answers


def test_no_route_without_gh_or_token_returns_the_compare_url(no_gh):
    result = github.create_pr("o/r", "main", "sdlc/0001/c", "t", "b", draft=True)
    assert result["route"] == "none"
    assert result["compare_url"] == "https://github.com/o/r/compare/main...sdlc/0001/c?expand=1"
    assert github.find_open_pr("o/r", "sdlc/0001/c")["number"] is None
    assert github.create_check_run("o/r", "abc", "sdlc/d", "success", "t", "s")["route"] == "none"


def test_find_open_pr_and_create_and_update(recorder):
    calls, answers = recorder
    answers[("GET", "/pulls?")] = {"status": 200, "data": [], "error": ""}
    assert github.find_open_pr("o/r", "sdlc/0001/c")["number"] is None
    assert "head=o%3Asdlc%2F0001%2Fc" in calls[0][1]

    answers[("POST", "/repos/o/r/pulls")] = {
        "status": 201,
        "data": {"number": 7, "html_url": "https://github.com/o/r/pull/7", "node_id": "PR_7"},
        "error": "",
    }
    created = github.create_pr("o/r", "main", "sdlc/0001/c", "build(0001): x", "body", draft=True)
    assert created["route"] == "api" and created["number"] == 7 and created["created"] is True
    assert calls[-1][2]["draft"] is True and calls[-1][2]["base"] == "main"

    answers[("PATCH", "/repos/o/r/pulls/7")] = {
        "status": 200,
        "data": {"number": 7, "html_url": "https://github.com/o/r/pull/7"},
        "error": "",
    }
    updated = github.update_pr("o/r", 7, "new body", "new title")
    assert updated["ok"] and updated["created"] is False
    assert calls[-1][2] == {"body": "new body", "title": "new title"}


def test_set_labels_removes_then_adds(recorder):
    calls, _answers = recorder
    result = github.set_labels("o/r", 7, ["sdlc:e-ready"], ["sdlc:d-ready", "sdlc:needs-human"])
    assert result["ok"] is True
    methods = [call[0] for call in calls]
    assert methods == ["DELETE", "DELETE", "POST"]  # remove first, then add
    assert calls[0][1].endswith("/issues/7/labels/sdlc%3Ad-ready")
    assert calls[-1][2] == {"labels": ["sdlc:e-ready"]}


def test_set_labels_ignores_404_on_remove(recorder):
    _calls, answers = recorder
    answers[("DELETE", "/labels/")] = {
        "status": 404,
        "data": {"message": "Not Found"},
        "error": "Not Found",
    }
    result = github.set_labels("o/r", 7, [], ["sdlc:c-ready"])
    assert result["ok"] is True and result["removed"] == []


def test_ensure_label_never_forces_and_accepts_an_existing_label(monkeypatch, gh_only):
    """--force would rewrite the colour and description of a label the owner edited."""
    calls, answers = gh_only
    answers.append({"ok": False, "code": 1, "out": "", "err": "label already exists; ..."})
    result = github.ensure_label("o/r", "sdlc:c-ready", "0E8A16", "SDLC gate (c)")
    assert result["ok"] is True and result["created"] is False
    assert "--force" not in calls[0]["args"]


def test_ensure_label_treats_already_exists_as_success(recorder):
    _calls, answers = recorder
    answers[("POST", "/labels")] = {
        "status": 422,
        "data": {"message": "Validation Failed", "errors": [{"code": "already_exists"}]},
        "error": "Validation Failed",
    }
    result = github.ensure_label("o/r", "sdlc:c-ready", "0E8A16", "SDLC gate (c)")
    assert result["ok"] is True and result["created"] is False


def test_set_ready_uses_the_graphql_mutation(recorder):
    calls, answers = recorder
    answers[("GET", "/pulls/7")] = {"status": 200, "data": {"node_id": "PR_7"}, "error": ""}
    answers[("POST", "/graphql")] = {"status": 200, "data": {"data": {}}, "error": ""}
    assert github.set_ready("o/r", 7)["ok"] is True
    assert "markPullRequestReadyForReview" in calls[-1][2]["query"]
    assert calls[-1][2]["variables"] == {"id": "PR_7"}


def test_check_run_and_issue_helpers(recorder):
    calls, answers = recorder
    answers[("POST", "/check-runs")] = {"status": 201, "data": {"id": 3}, "error": ""}
    assert github.create_check_run("o/r", "sha", "sdlc/d", "success", "t", "s")["id"] == 3
    assert calls[-1][2]["conclusion"] == "success"

    answers[("GET", "/issues?")] = {
        "status": 200,
        "data": [{"number": 9, "title": digest_mod.ISSUE_TITLE, "node_id": "I_9"}],
        "error": "",
    }
    found = github.pinned_issue("o/r", digest_mod.ISSUE_TITLE)
    assert found["number"] == 9 and found["node_id"] == "I_9"
    answers[("PATCH", "/issues/9")] = {"status": 200, "data": {"number": 9}, "error": ""}
    assert github.update_issue_body("o/r", 9, "# queue")["ok"] is True


# --- the order of the routes (third live design run, 2026-09-21) ------------------------------
def test_the_token_route_goes_first_and_gh_is_never_called(recorder, fake_gh):
    """A CI runner has both. The token is the identity the workflow acts as and the REST call
    behaves the same everywhere, so it goes first; ``gh`` is the fallback."""
    calls, answers = recorder
    gh_calls, _gh_answers = fake_gh
    answers[("POST", "/repos/o/r/pulls")] = {
        "status": 201,
        "data": {"number": 7, "html_url": "https://github.com/o/r/pull/7"},
        "error": "",
    }
    created = github.create_pr("o/r", "main", "sdlc/0001/c", "t", "body", cwd="/tmp/project")
    assert created["route"] == "api" and created["number"] == 7
    assert gh_calls == [] and calls[-1][0] == "POST"


def test_gh_takes_over_when_the_token_route_fails(recorder, fake_gh):
    _calls, answers = recorder
    gh_calls, gh_answers = fake_gh
    answers[("POST", "/repos/o/r/pulls")] = {
        "status": 403,
        "data": {"message": "Resource not accessible by integration"},
        "error": "Resource not accessible by integration",
    }
    gh_answers.append({"ok": True, "code": 0, "out": "https://github.com/o/r/pull/9\n", "err": ""})
    created = github.create_pr("o/r", "main", "sdlc/0001/c", "t", "body", cwd="/tmp/project")
    assert created["route"] == "gh" and created["number"] == 9 and created["created"] is True
    assert gh_calls[0]["args"][:2] == ["pr", "create"]
    assert gh_calls[0]["cwd"] == "/tmp/project"  # gh reads the repo from its directory
    assert gh_calls[0]["stdin"] == "body"


def test_when_both_routes_fail_the_reason_names_both(recorder, fake_gh):
    _calls, answers = recorder
    _gh_calls, gh_answers = fake_gh
    answers[("PATCH", "/repos/o/r/pulls/7")] = {
        "status": 404,
        "data": {"message": "Not Found"},
        "error": "Not Found",
    }
    gh_answers.append(
        {"ok": False, "code": 1, "out": "", "err": "could not determine base repository"}
    )
    result = github.update_pr("o/r", 7, "body", "title", cwd="/tmp/project")
    assert result["ok"] is False and result["route"] == "none" and result["number"] == 7
    assert "api: Not Found" in result["reason"]
    assert "gh: gh pr edit exited 1: could not determine base repository" in result["reason"]


def test_gh_alone_still_opens_the_pull_request(gh_only):
    calls, answers = gh_only
    answers.append({"ok": True, "code": 0, "out": "https://github.com/o/r/pull/4\n", "err": ""})
    result = github.create_pr("o/r", "main", "sdlc/0001/b", "t", "body", cwd="/tmp/project")
    assert result["route"] == "gh" and result["number"] == 4
    assert calls[0]["cwd"] == "/tmp/project"

    answers.append({"ok": True, "code": 0, "out": "[]", "err": ""})
    assert github.find_open_pr("o/r", "sdlc/0001/b", cwd="/tmp/project")["number"] is None
    assert calls[-1]["cwd"] == "/tmp/project"


# --- the daily digest ---------------------------------------------------------------------
QUEUE = [
    {
        "number": 4,
        "title": "build(0002): invoice totals",
        "html_url": "https://github.com/o/r/pull/4",
        "updated_at": "2026-09-20T08:00:00Z",
        "labels": [{"name": "sdlc:needs-human"}],
        "body": "- **What changed and why**: invoice totals (fix, ticket route)\n- more\n",
    },
    {
        "number": 2,
        "title": "design(0001): percent helper",
        "html_url": "https://github.com/o/r/pull/2",
        "updated_at": "2026-09-21T09:00:00Z",
        "labels": [{"name": "sdlc:b-ready"}],
        "body": "- **What changed and why**: percent helper (feature, idea route)\n",
    },
    {
        "number": 5,
        "title": "chore: unrelated",
        "html_url": "https://github.com/o/r/pull/5",
        "updated_at": "2026-09-21T09:30:00Z",
        "labels": [{"name": "dependencies"}],
        "body": "- nothing to do with the framework\n",
    },
]


def test_render_digest_puts_parked_first_and_skips_unlabelled_prs():
    markdown = digest_mod.render_digest(QUEUE, "2026-09-21T10:00:00Z")
    assert markdown.startswith("# SDLC review queue — 2026-09-21")
    assert "1 parked, 1 waiting at a gate." in markdown
    parked_at = markdown.index("## Parked")
    ready_at = markdown.index("## Waiting at a human gate")
    assert parked_at < ready_at
    assert markdown.index("#4") < ready_at < markdown.index("#2")
    assert "invoice totals (fix, ticket route)" in markdown  # the first bullet of the body
    assert "unrelated" not in markdown


def test_render_digest_empty_queue():
    markdown = digest_mod.render_digest([], "2026-09-21T10:00:00Z")
    assert digest_mod.NOTHING_WAITING in markdown
    assert "## Parked" not in markdown


def test_digest_main_dry_run_reads_the_input_file(tmp_path, capsys, no_gh):
    path = tmp_path / "prs.json"
    write(path, json.dumps(QUEUE))
    assert digest_mod.main(["--repo", "o/r", "--dry-run", "--input", str(path)]) == 0
    out = capsys.readouterr().out
    assert "## Parked" in out and "design(0001): percent helper" in out


def test_digest_main_without_a_token_still_renders(capsys, no_gh):
    assert digest_mod.main(["--repo", "o/r"]) == 0
    out = capsys.readouterr().out
    assert "no GITHUB_TOKEN/GH_TOKEN" in out
    assert digest_mod.NOTHING_WAITING in out


def test_digest_publish_updates_the_issue_body(recorder):
    calls, answers = recorder
    answers[("GET", "/issues?")] = {
        "status": 200,
        "data": [{"number": 9, "title": digest_mod.ISSUE_TITLE, "node_id": "I_9"}],
        "error": "",
    }
    answers[("PATCH", "/issues/9")] = {"status": 200, "data": {"number": 9}, "error": ""}
    result = digest_mod.publish("o/r", "# queue\n")
    assert result["ok"] is True and result["number"] == 9
    assert calls[-1][0] == "PATCH" and calls[-1][2] == {"body": "# queue\n"}
