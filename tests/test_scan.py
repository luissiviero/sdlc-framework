"""Layer-1 tests for plugin/scan/: the weekly security review, the routing of its findings
and the deterministic scanners (build guide step 38; decision 16; article p.46-48).

The filing tests run against a copy of the fixture project initialised with ``/sdlc-init``,
committed on ``main`` and pushed to a bare ``origin``, so ``commit-phase --start-point
origin/main --push`` works for real and ``pr/cli.py upsert`` finds no GitHub remote (route
``none``): nothing leaves the machine. ``claude`` is a stand-in script run through
``sys.executable`` that writes the findings file the prompt names."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest
from detect import dismissals
from review import findings as findings_mod
from scan import cli as scan_cli
from scan import prompt as prompt_mod
from scan import route as route_mod
from scan import scanners as scanners_mod

from gate import artifacts as art
from state import status as status_mod

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "sample-python-project"
INIT = ROOT / "plugin" / "init" / "sdlc_init.py"
DETECT_CLI = ROOT / "plugin" / "detect" / "cli.py"
WORKFLOW = ROOT / "template" / ".github" / "workflows" / "sdlc-scan.yml"
REPO = "o/r"
CLAUDE_INSTALL = 'npm install -g @anthropic-ai/claude-code@"$CLAUDE_CODE_VERSION"'
PIN_RUN = (
    'git show "refs/remotes/origin/$SDLC_DEFAULT_BRANCH:.github/scripts/sdlc_pin.py" '
    '| python - --ref "refs/remotes/origin/$SDLC_DEFAULT_BRANCH"'
)

PATCH = (
    "--- a/sample_pkg/db.py\n"
    "+++ b/sample_pkg/db.py\n"
    "@@ -10,3 +10,3 @@\n"
    " def find_user(conn, user_id):\n"
    '-    return conn.execute(f"SELECT * FROM users WHERE id = {user_id}")\n'
    '+    return conn.execute("SELECT * FROM users WHERE id = ?", (user_id,))\n'
)
BOUNDED = {
    "pass": "security",
    "severity": "important",
    "file": "sample_pkg/db.py",
    "line": 11,
    "summary": "The user id is formatted into the SQL string, so a crafted id injects SQL.",
    "rule": "security-baseline Rule 2 Input",
    "class": "injection",
    "bounded": True,
    "patch": PATCH,
}
WIDE = {
    "pass": "security",
    "severity": "important",
    "file": "sample_pkg/api.py",
    "line": 40,
    "summary": "Every handler trusts the role the client sends; no server-side authorization.",
    "rule": "security-baseline Rule 1 Authentication",
    "class": "authz",
    "bounded": False,
}
NIT = {
    "pass": "security",
    "severity": "nit",
    "file": "sample_pkg/calc.py",
    "line": 3,
    "summary": "The error message echoes the raw input back to the caller.",
    "class": "pii-in-logs",
}


# --- helpers ----------------------------------------------------------------------------------
def git(cwd: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=cwd, capture_output=True, text=True, check=True, encoding="utf-8"
    ).stdout


def bare(root: Path) -> Path:
    return root.parent / "origin.git"


def remote_has(root: Path, branch: str) -> bool:
    return bool(git(bare(root), "branch", "--list", branch).strip())


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def project(tmp_path: Path, push: bool = True) -> Path:
    """The fixture initialised (standard profile) and committed on main, pushed to a bare
    origin whose HEAD is main."""
    root = tmp_path / "proj"
    shutil.copytree(FIXTURE, root)
    git(root, "init", "-q", "-b", "main")
    git(root, "config", "user.email", "owner@example.com")
    git(root, "config", "user.name", "Owner")
    git(root, "add", ".")
    git(root, "commit", "-q", "-m", "fixture")
    proc = subprocess.run(
        [sys.executable, str(INIT), "--root", str(root), "--profile", "standard"],
        cwd=root,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert proc.returncode == 0, proc.stderr
    git(root, "add", ".")
    git(root, "commit", "-q", "-m", "sdlc-init (as if the 0000 PR merged)")
    origin = bare(root)
    git(tmp_path, "init", "-q", "--bare", "-b", "main", str(origin))
    git(root, "remote", "add", "origin", str(origin))
    git(root, "push", "-q", "-u", "origin", "main")
    git(root, "symbolic-ref", "refs/remotes/origin/HEAD", "refs/remotes/origin/main")
    return root


def head_of(root: Path) -> str:
    return git(root, "rev-parse", "HEAD").strip()


def findings_file(head: str, *items: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "head": head,
        "findings": [dict(i) for i in items],
        "tally": {"important": 0, "nit": 0, "nits_omitted": 0},
        "at": "2026-09-28T06:30:00Z",
    }


def dump(path: Path, data: Any) -> Path:
    write(path, json.dumps(data, indent=2))
    return path


def dismiss(root: Path, finding: dict[str, Any], commit: bool = True) -> str:
    """Record a scan dismissal of ``finding`` on main (as if the dismissal PR merged)."""
    sig = findings_mod.signature(finding)
    path = dismissals.path_for(root)
    store = dismissals.add(
        dismissals.load(path),
        sig,
        kind="scan",
        reason="the query runs on a constant, never on user input",
        by="owner",
        change_id="0007",
        summary=finding["summary"],
    )
    dismissals.save(path, store)
    if commit:
        git(root, "add", "changes/.dismissed.json")
        git(root, "commit", "-q", "-m", "dismiss(0007): scan finding")
        git(root, "push", "-q", "origin", "main")
    return sig


def show(root: Path, ref: str, path: str) -> str:
    return git(root, "show", f"{ref}:{path}")


def change_dir_name(root: Path, ref: str, change_id: str) -> str:
    listing = show(root, ref, "changes").split()
    names = [n.rstrip("/") for n in listing if n.startswith(change_id + "-")]
    assert names, listing
    return names[0]


@pytest.fixture
def fake_claude(tmp_path):
    """A stand-in ``claude``: it reads the prompt after ``-p``, writes the findings JSON of
    ``FAKE_SCAN_FINDINGS`` (when set) to the file the prompt names, records its argv in
    ``FAKE_ARGV_FILE`` and prints ``FAKE_CLAUDE_RESULT``."""
    bindir = tmp_path / "bin"
    bindir.mkdir()
    script = bindir / "claude.py"
    write(
        script,
        "import json, os, re, sys\n"
        "argv = sys.argv[1:]\n"
        "prompt = argv[argv.index('-p') + 1]\n"
        "if os.environ.get('FAKE_ARGV_FILE'):\n"
        "    open(os.environ['FAKE_ARGV_FILE'], 'w', encoding='utf-8').write(json.dumps(argv))\n"
        "m = re.search(r'Output file: `([^`]+)`', prompt)\n"
        "if m and os.environ.get('FAKE_SCAN_FINDINGS'):\n"
        "    with open(m.group(1), 'w', encoding='utf-8') as fh:\n"
        "        fh.write(os.environ['FAKE_SCAN_FINDINGS'])\n"
        "print(os.environ.get('FAKE_CLAUDE_RESULT', '{}'))\n",
    )
    launcher = bindir / "claude"
    write(launcher, f'#!/bin/sh\nexec "{sys.executable}" "{script}" "$@"\n')
    launcher.chmod(0o755)
    write(bindir / "claude.cmd", f'@echo off\r\n"{sys.executable}" "{script}" %*\r\n')
    return str(bindir / ("claude.cmd" if os.name == "nt" else "claude"))


def run_cli(capsys, *argv: str) -> tuple[int, Any]:
    code = scan_cli.main(list(argv))
    out = capsys.readouterr().out
    try:
        return code, json.loads(out)
    except ValueError:
        return code, out


# --- prompt -----------------------------------------------------------------------------------
def test_prompt_carries_the_skill_rules_the_dismissals_the_head_and_the_contract(tmp_path):
    root = project(tmp_path)
    sig = dismiss(root, BOUNDED)
    # a detection dismissal is not the reviewer's business, and an expired one is not in force
    record = dismissals.load(dismissals.path_for(root))
    record = dismissals.add(
        record, "feedfacefeedface", kind="detect", reason="noisy band", by="owner",
        change_id="0003", until="2020-01-01",
    )  # fmt: skip
    dismissals.save(dismissals.path_for(root), record)
    head = head_of(root)
    text = prompt_mod.build_prompt(root, {}, head=head, out_path="scan-findings.json")

    # the security-baseline skill's rules, and REVIEW.md's definition of Important
    assert "validate every external input against a schema" in text
    assert "Authorization is checked on the server" in text
    assert "Reserve Important for findings that would break behavior" in text
    # the dismissed signatures, so the reviewer does not report them again
    assert sig in text and BOUNDED["summary"] in text
    assert "feedfacefeedface" not in text
    # the head and the output contract
    assert f"`{head}`" in text and f'"head": "{head}"' in text
    assert "Output file: `scan-findings.json`" in text
    for key in ('"pass": "security"', '"bounded"', '"class"', '"patch"', '"severity"'):
        assert key in text
    assert f"at most {prompt_mod.MAX_PATCH_LINES} lines" in text
    assert "at most 3 Important findings" in text and "At most 5 nits" in text
    # the scope: the whole tracked tree minus the framework's records and the tests
    for excluded in ("`changes/`", "`evals/`", "`lessons/`", "`framework/`", "tests/**"):
        assert excluded in text
    assert "git ls-files" in text


def test_prompt_cap_absolute_out_path_and_no_dismissals(tmp_path):
    root = tmp_path / "proj"
    root.mkdir()
    text = prompt_mod.build_prompt(
        root,
        {"maintain": {"scan": {"max_findings": 2}}},
        head="abc123",
        out_path=tmp_path / "x.json",
    )
    assert "at most 2 Important findings" in text
    assert f"Output file: `{(tmp_path / 'x.json').resolve().as_posix()}`" in text
    assert "None are recorded." in text
    # no REVIEW.md: the brief says what Important means itself
    assert "Important = would break behaviour" in text
    assert (
        prompt_mod.build_prompt(root, {}, head="a", out_path="f", max_findings=1).count(
            "at most 1 Important findings"
        )
        == 1
    )


def test_prompt_uses_the_project_override_of_the_skill(tmp_path):
    root = tmp_path / "proj"
    write(
        root / ".claude" / "skills" / "security-baseline" / "SKILL.md",
        "---\nname: security-baseline\n---\n# Ours\n\n## Rules\n1. Every query is "
        "parameterised, no exception.\n",
    )
    text = prompt_mod.build_prompt(root, {}, head="abc", out_path="f.json")
    assert "Every query is parameterised, no exception." in text
    assert ".claude/skills/security-baseline/SKILL.md" in text
    assert "validate every external input" not in text


def test_tool_lists_are_read_only_but_for_one_write():
    assert prompt_mod.allowed_tools() == "Read,Grep,Glob,Bash(git *),Write"
    assert prompt_mod.disallowed_tools() == "Edit,MultiEdit,NotebookEdit,WebFetch,WebSearch"


def test_prompt_command_prints_the_brief(tmp_path, capsys):
    root = project(tmp_path)
    code, out = run_cli(capsys, "prompt", "--root", str(root), "--out", "scan-findings.json")
    assert code == 0
    assert f"`{head_of(root)}`" in out and "Output file: `scan-findings.json`" in out


# --- load_findings ----------------------------------------------------------------------------
def test_load_findings_validates_and_adds_the_extra_keys(tmp_path):
    no_keys = {k: v for k, v in WIDE.items() if k not in ("bounded", "class")}
    path = dump(tmp_path / "f.json", findings_file("abc123", BOUNDED, no_keys, NIT))
    data, problems = route_mod.load_findings(path, "abc123def")
    assert problems == [] and data is not None
    by_file = {f["file"]: f for f in data["findings"]}
    assert by_file["sample_pkg/api.py"]["bounded"] is False
    assert by_file["sample_pkg/api.py"]["class"] == "unclassified"
    assert by_file["sample_pkg/db.py"]["bounded"] is True
    assert by_file["sample_pkg/db.py"]["patch"] == PATCH
    for finding in data["findings"]:
        assert finding["signature"] == findings_mod.signature(finding)
    assert data["tally"] == {"important": 2, "nit": 1, "nits_omitted": 0}


def test_load_findings_refuses_a_bad_file(tmp_path):
    data, problems = route_mod.load_findings(tmp_path / "missing.json", "abc")
    assert data is None and "no findings file" in problems[0]
    write(tmp_path / "bad.json", "{not json")
    assert route_mod.load_findings(tmp_path / "bad.json", "abc")[0] is None
    stale = dump(tmp_path / "stale.json", findings_file("0123abc", BOUNDED))
    data, problems = route_mod.load_findings(stale, "fedcba9")
    assert data is None and "re-run the review" in problems[0]
    wrong = dump(
        tmp_path / "wrong.json",
        findings_file("abc", {**BOUNDED, "pass": "bugs"}, {**WIDE, "bounded": "yes"}),
    )
    data, problems = route_mod.load_findings(wrong, "abc")
    assert data is None
    assert any("'security'" in p for p in problems)
    assert any("bounded must be true or false" in p for p in problems)


def test_load_findings_drops_a_patch_that_is_not_one_small_diff(tmp_path):
    long_patch = PATCH + "".join(f"+line {i}\n" for i in range(70))
    items = (
        {**BOUNDED, "patch": long_patch},
        {**BOUNDED, "file": "sample_pkg/other.py", "patch": "replace line 11 with a query"},
    )
    data, problems = route_mod.load_findings(
        dump(tmp_path / "f.json", findings_file("a", *items)), "a"
    )
    assert problems == []
    by_file = {f["file"]: f for f in data["findings"]}
    long_one = by_file["sample_pkg/db.py"]
    assert long_one["bounded"] is False and "patch" not in long_one  # not "one patch": wide
    assert "over 60" in long_one["patch_dropped"]
    prose = by_file["sample_pkg/other.py"]
    assert prose["bounded"] is True and "patch" not in prose


# --- select -----------------------------------------------------------------------------------
def _loaded(tmp_path: Path, *items: dict[str, Any]) -> list[dict[str, Any]]:
    data, problems = route_mod.load_findings(
        dump(tmp_path / "sel.json", findings_file("h", *items)), "h"
    )
    assert problems == []
    return data["findings"]


def test_select_ranks_bounded_first_then_file_order_and_caps(tmp_path):
    items = [
        {**WIDE, "file": "a.py"},
        {**BOUNDED, "file": "z.py"},
        {**BOUNDED, "file": "m.py", "line": 9},
        {**BOUNDED, "file": "m.py", "line": 2, "summary": "Another injection in m."},
        NIT,
    ]
    findings = _loaded(tmp_path, *items)
    chosen, skipped = route_mod.select(findings, dismissals.empty(), 3)
    assert [(f["file"], f["line"]) for f in chosen] == [("m.py", 2), ("m.py", 9), ("z.py", 11)]
    reasons = {f["file"]: f["skip_reason"] for f in skipped}
    assert reasons["a.py"].startswith("over the cap")
    assert reasons["sample_pkg/calc.py"] == "nit"
    chosen, _ = route_mod.select(findings, dismissals.empty(), 10)
    assert [f["file"] for f in chosen][-1] == "a.py"  # the wide finding after every bounded one


def test_select_leaves_out_dismissed_and_already_filed_findings(tmp_path):
    findings = _loaded(tmp_path, BOUNDED, WIDE)
    record = dismissals.add(
        dismissals.empty(), findings_mod.signature(BOUNDED), kind="scan",
        reason="constant input only", by="owner", change_id="0002",
    )  # fmt: skip
    chosen, skipped = route_mod.select(findings, record, 3)
    assert [f["file"] for f in chosen] == ["sample_pkg/api.py"]
    assert skipped[0]["skip_reason"] == "dismissed"
    assert skipped[0]["dismissal"] == "constant input only"
    wide_sig = findings_mod.signature(WIDE)
    chosen, skipped = route_mod.select(findings, record, 3, already_filed={wide_sig: "0004"})
    assert chosen == []
    assert {f["skip_reason"] for f in skipped} == {"dismissed", "already filed as change 0004"}


# --- the intent -------------------------------------------------------------------------------
def _with_sig(finding: dict[str, Any]) -> dict[str, Any]:
    return {**finding, "signature": findings_mod.signature(finding)}


def test_intent_text_of_a_bounded_finding_is_the_patch():
    finding = _with_sig(BOUNDED)
    text = route_mod.intent_text(finding, "0005", "a" * 40, REPO)
    # the title cuts the summary at a word boundary (the 2026-09-25 live run cut mid-word)
    assert text.startswith(
        "# Intent: security: injection: The user id is formatted into the SQL string, so a "
        "crafted\n"
    )
    header = text.splitlines()[1]
    assert header == (
        "Author: security review (phase f). Status: proposed. Change id: 0005. "
        f"Entry route: incident scan:{finding['signature']}."
    )
    for field in art.INTENT_HEADER_FIELDS:
        assert field in header
    required = (*art.INTENT_SECTIONS, art.INTENT_EVIDENCE_SECTION)
    assert art.missing_sections(text, required) == []
    assert art.empty_sections(text, required) == []
    sections = art.split_sections(text)
    assert "```diff" in sections["## Proposed outcome"]
    assert '+    return conn.execute("SELECT * FROM users WHERE id = ?"' in text
    assert "evidence/suggested-patch.diff" in sections["## Proposed outcome"]
    assert sections["## Open questions"].strip() == "none"
    evidence = sections["## Evidence"]
    assert "sample_pkg/db.py:11" in evidence and "injection" in evidence
    assert "a" * 40 in evidence and BOUNDED["summary"] in evidence
    assert f"https://github.com/{REPO}/blob/{'a' * 40}/sample_pkg/db.py#L11" in evidence


def test_intent_text_of_a_wide_finding_describes_the_class():
    finding = _with_sig(WIDE)
    text = route_mod.intent_text(finding, "0006", "b" * 40, None)
    required = (*art.INTENT_SECTIONS, art.INTENT_EVIDENCE_SECTION)
    assert art.missing_sections(text, required) == []
    assert art.empty_sections(text, required) == []
    sections = art.split_sections(text)
    assert "```diff" not in text
    assert "No instance of this authz weakness remains" in sections["## Proposed outcome"]
    assert "eval case" in sections["## Proposed outcome"]
    assert "authz pattern occur" in sections["## Open questions"]
    assert "https://github.com" not in text  # no repo: no link
    assert art.intent_title(text).startswith("security: authz: ")


def test_title_for_cuts_a_long_summary_at_a_word_boundary():
    summary = (
        "The fixture `.env` file is committed and tracked in git (present since the first commit)"
    )
    title = route_mod.title_for({"class": "secrets", "summary": summary})
    assert title == "security: secrets: The fixture `.env` file is committed and tracked in git"
    assert len(title) <= len("security: secrets: ") + route_mod.TITLE_SUMMARY_CHARS
    short = route_mod.title_for({"class": "secrets", "summary": "A token in the log."})
    assert short == "security: secrets: A token in the log"


# --- filing -----------------------------------------------------------------------------------
def test_file_findings_opens_one_incident_change_per_finding(tmp_path):
    root = project(tmp_path)
    head = head_of(root)
    findings = _loaded(tmp_path, BOUNDED, WIDE)
    chosen, _ = route_mod.select(findings, dismissals.empty(), 3)
    results = route_mod.file_findings(root, chosen, head=head, repo=REPO, push=True, dry_run=False)

    assert [r.get("error") for r in results] == [None, None]
    assert [r["change_id"] for r in results] == ["0001", "0002"]
    assert [r["type"] for r in results] == ["fix", "feature"]
    assert all(r["pushed"] and r["commit"] for r in results)
    assert all(r["pr_route"] == "none" and r["pr"] is None for r in results)  # no GitHub remote
    # gate (f) ran on each filed change (the scan finding read as a tier-3 record): the
    # intent PR carries the gate's label beside `incident`, and the evidence is committed
    assert all(r["gate"] == "wait" and r["label"] == "sdlc:f-ready" for r in results), results
    # the checkout is back on main, with nothing of the changes left in it
    assert git(root, "rev-parse", "--abbrev-ref", "HEAD").strip() == "main"
    assert not list((root / "changes").glob("0001-*"))

    for result, finding, change_type in zip(
        results, (BOUNDED, WIDE), ("fix", "feature"), strict=True
    ):
        change_id = result["change_id"]
        branch = f"sdlc/{change_id}/a"
        assert result["branch"] == branch and remote_has(root, branch)
        ref = f"origin/{branch}"
        rel = f"changes/{change_dir_name(root, ref, change_id)}"
        assert rel == result["dir"]
        status = status_mod.Status.from_dict(
            status_mod.yamlish.loads(show(root, ref, f"{rel}/status.yaml"))
        )
        assert status.entry_route == "incident" and status.change_type == change_type
        assert status.phase == "f"
        intent = show(root, ref, f"{rel}/intent.md")
        assert f"Change id: {change_id}." in intent and "## Evidence" in intent
        record = json.loads(show(root, ref, f"{rel}/evidence/scan-finding.json"))
        assert record["kind"] == "scan" and record["schema_version"] == 1
        assert record["signature"] == findings_mod.signature(finding)
        assert record["head"] == head and record["severity"] == "important"
        assert record["file"] == finding["file"] and record["line"] == finding["line"]
        assert record["class"] == finding["class"] and record["bounded"] == finding["bounded"]
        assert record["summary"] == finding["summary"] and record["at"]
        proposal = json.loads(show(root, ref, f"{rel}/evidence/proposal.json"))
        assert proposal == route_mod.PROPOSAL
        files = git(root, "ls-tree", "-r", "--name-only", ref, f"{rel}/evidence").split()
        assert (f"{rel}/evidence/suggested-patch.diff" in files) is finding["bounded"]
        # the branch starts from the default branch and carries only the change folder
        diff = git(root, "diff", "--name-only", "origin/main", ref).split()
        assert diff and all(p.startswith(rel + "/") for p in diff)
    patch = show(root, "origin/sdlc/0001/a", f"{results[0]['dir']}/evidence/suggested-patch.diff")
    assert patch == PATCH


def test_file_findings_without_push_allocates_distinct_ids(tmp_path):
    root = project(tmp_path)
    chosen = _loaded(tmp_path, BOUNDED, WIDE)
    results = route_mod.file_findings(
        root, chosen, head=head_of(root), repo=REPO, push=False, dry_run=False
    )
    assert [r["change_id"] for r in results] == ["0001", "0002"]
    assert not any(r["pushed"] for r in results)
    assert git(root, "branch", "--list", "sdlc/0001/a", "sdlc/0002/a").split() == [
        "sdlc/0001/a",
        "sdlc/0002/a",
    ]
    assert not remote_has(root, "sdlc/0001/a")


def test_file_findings_dry_run_touches_nothing(tmp_path):
    root = project(tmp_path)
    chosen = _loaded(tmp_path, BOUNDED)
    results = route_mod.file_findings(root, chosen, head="h", repo=REPO, push=True, dry_run=True)
    assert results[0]["dry_run"] and results[0]["type"] == "fix"
    assert results[0]["title"].startswith("security: injection: ")
    assert git(root, "branch", "--list", "sdlc/*").strip() == ""
    assert git(root, "status", "--porcelain").strip() == ""


def test_a_filed_scan_change_can_be_dismissed_by_the_detect_cli(tmp_path):
    """``detect/cli.py dismiss`` reads ``evidence/scan-finding.json`` (the close of the intent
    PR with a comment): the kind is ``scan`` and there is no expiry."""
    root = project(tmp_path)
    chosen = _loaded(tmp_path, WIDE)
    results = route_mod.file_findings(
        root, chosen, head=head_of(root), repo=REPO, push=True, dry_run=False
    )
    git(root, "checkout", "-q", "sdlc/0001/a")
    proc = subprocess.run(
        [sys.executable, str(DETECT_CLI), "dismiss", "--root", str(root), "--id", "0001",
         "--reason", "accepted: internal tool", "--by", "owner", "--dry-run"],
        cwd=root, capture_output=True, text=True, encoding="utf-8",
    )  # fmt: skip
    assert proc.returncode == 0, proc.stderr
    out = json.loads(proc.stdout)
    assert out["kind"] == "scan" and out["until"] is None
    assert out["signature"] == results[0]["signature"] == findings_mod.signature(WIDE)


# --- the route command, end to end ------------------------------------------------------------
def test_route_files_the_undismissed_finding_and_is_idempotent(tmp_path, capsys, monkeypatch):
    root = project(tmp_path)
    dismissed_sig = dismiss(root, BOUNDED)
    head = head_of(root)
    path = dump(tmp_path / "scan-findings.json", findings_file(head, BOUNDED, WIDE, NIT))
    output = tmp_path / "gh-output.txt"
    monkeypatch.setenv("GITHUB_OUTPUT", str(output))

    code, out = run_cli(
        capsys, "route", "--root", str(root), "--findings", str(path), "--repo", REPO
    )
    assert code == 0, out
    assert out["problems"] == [] and out["dismissed"] == 1
    assert len(out["filed"]) == 1
    filed = out["filed"][0]
    assert filed["signature"] == findings_mod.signature(WIDE) and filed["type"] == "feature"
    assert remote_has(root, f"sdlc/{filed['change_id']}/a")
    reasons = {f["signature"]: f["skip_reason"] for f in out["skipped"]}
    assert reasons[dismissed_sig] == "dismissed"
    assert reasons[findings_mod.signature(NIT)] == "nit"
    assert output.read_text(encoding="utf-8").strip() == "filed=1"

    # next week, the same untriaged finding: already filed, nothing new
    output.unlink()
    code, out = run_cli(
        capsys, "route", "--root", str(root), "--findings", str(path), "--repo", REPO
    )
    assert code == 0 and out["filed"] == []
    reasons = {f["signature"]: f["skip_reason"] for f in out["skipped"]}
    assert reasons[findings_mod.signature(WIDE)] == f"already filed as change {filed['change_id']}"
    assert output.read_text(encoding="utf-8").strip() == "filed=0"


def test_route_refuses_an_invalid_findings_file(tmp_path, capsys, monkeypatch):
    root = project(tmp_path)
    monkeypatch.delenv("GITHUB_OUTPUT", raising=False)
    path = dump(tmp_path / "stale.json", findings_file("0123456789", WIDE))
    code, out = run_cli(
        capsys, "route", "--root", str(root), "--findings", str(path), "--repo", REPO
    )
    assert code == 1 and out["filed"] == [] and "re-run the review" in out["problems"][0]
    code, out = run_cli(
        capsys, "route", "--root", str(root), "--findings", str(tmp_path / "none.json"),
        "--repo", REPO,
    )  # fmt: skip
    assert code == 1 and "no findings file" in out["problems"][0]
    assert git(root, "branch", "--list", "sdlc/*").strip() == ""


def test_route_dry_run_and_usage(tmp_path, capsys):
    root = project(tmp_path)
    path = dump(tmp_path / "f.json", findings_file(head_of(root), BOUNDED, WIDE))
    code, out = run_cli(
        capsys, "route", "--root", str(root), "--findings", str(path), "--repo", REPO,
        "--max-findings", "1", "--dry-run",
    )  # fmt: skip
    assert code == 0 and len(out["filed"]) == 1 and out["filed"][0]["dry_run"]
    assert out["skipped"][0]["skip_reason"].startswith("over the cap")
    code, _ = run_cli(
        capsys, "route", "--root", str(root), "--findings", str(path), "--repo", REPO,
        "--max-findings", "-1",
    )  # fmt: skip
    assert code == 2
    with pytest.raises(SystemExit) as exc:
        scan_cli.main(["route", "--root", str(root), "--findings", str(path)])  # no --repo
    assert exc.value.code == 2


# --- the review run ---------------------------------------------------------------------------
def test_review_dry_run_composes_the_read_only_headless_call(tmp_path, capsys):
    root = project(tmp_path)
    head = head_of(root)
    code, out = run_cli(
        capsys, "review", "--root", str(root), "--plugin-dir", str(ROOT), "--claude", "claude",
        "--head", head, "--out", "scan-findings.json", "--dry-run",
    )  # fmt: skip
    assert code == 0
    argv = out["argv"]
    assert (
        argv[0] == "claude" and argv[1] == "-p" and "Output file: `scan-findings.json`" in argv[2]
    )
    assert f"`{head}`" in argv[2]

    def flag(name: str) -> str:
        return argv[argv.index(name) + 1]

    assert flag("--max-turns") == str(scan_cli.SCAN_MAX_TURNS) == "60"
    assert flag("--allowedTools") == "Read,Grep,Glob,Bash(git *),Write"
    assert flag("--disallowedTools") == "Edit,MultiEdit,NotebookEdit,WebFetch,WebSearch"
    assert flag("--permission-mode") == "default"
    assert flag("--permission-prompts") == "none"
    assert flag("--output-format") == "json"
    assert flag("--plugin-dir") == str(ROOT)
    assert Path(flag("--settings")).name == "settings.ci.json"
    assert argv.count("--allowedTools") == 1 and "bypassPermissions" not in argv


def test_review_runs_the_fake_claude_and_checks_the_findings(
    tmp_path, capsys, monkeypatch, fake_claude
):
    root = project(tmp_path)
    head = head_of(root)
    argv_file = tmp_path / "argv.json"
    monkeypatch.setenv("FAKE_ARGV_FILE", str(argv_file))
    monkeypatch.setenv("FAKE_SCAN_FINDINGS", json.dumps(findings_file(head, BOUNDED, NIT)))
    monkeypatch.setenv("FAKE_CLAUDE_RESULT", json.dumps({"is_error": False, "total_cost_usd": 0.5}))
    base = ["review", "--root", str(root), "--plugin-dir", str(ROOT), "--claude", fake_claude,
            "--head", head]  # fmt: skip

    code, out = run_cli(capsys, *base)
    assert code == 0, out
    assert out["problems"] == [] and out["tally"] == {"important": 1, "nit": 1, "nits_omitted": 0}
    assert out["cost_usd"] == 0.5
    written = json.loads((root / "scan-findings.json").read_text(encoding="utf-8"))
    assert written["head"] == head and len(written["findings"]) == 2
    assert json.loads((root / "scan-run.json").read_text(encoding="utf-8"))["total_cost_usd"] == 0.5
    assert "--allowedTools" in json.loads(argv_file.read_text(encoding="utf-8"))

    # the CLI reports an error: an infrastructure failure
    monkeypatch.setenv("FAKE_CLAUDE_RESULT", json.dumps({"is_error": True, "result": "auth"}))
    code, out = run_cli(capsys, *base)
    assert code == 1 and "claude exited" in out["error"]

    # a run that wrote no findings file fails, and an earlier file is never read as this one
    monkeypatch.setenv("FAKE_CLAUDE_RESULT", json.dumps({"is_error": False}))
    monkeypatch.delenv("FAKE_SCAN_FINDINGS")
    code, out = run_cli(capsys, *base)
    assert code == 1 and "no findings file" in out["problems"][0]
    assert not (root / "scan-findings.json").exists()


def test_review_refuses_a_plugin_dir_that_is_not_the_framework(tmp_path, capsys):
    root = project(tmp_path)
    code, _ = run_cli(capsys, "review", "--root", str(root), "--plugin-dir", str(tmp_path))
    assert code == 2


# --- the deterministic scanners ---------------------------------------------------------------
def test_scanners_plan_per_language(tmp_path):
    root = tmp_path / "proj"
    write(root / "pyproject.toml", "[project]\nname = 'x'\n")
    python = scanners_mod.plan(root, "python")
    assert [s["name"] for s in python] == ["pip-audit", "bandit"]
    pip_audit, bandit = python
    assert pip_audit["install"] == ["python", "-m", "pip", "install", "pip-audit"]
    assert pip_audit["run"][:3] == ["python", "-m", "pip_audit"]
    assert "--strict" in pip_audit["run"] and pip_audit["run"][-1] == "."
    assert pip_audit["report"] == "pip-audit.json"
    assert bandit["install"] == ["python", "-m", "pip", "install", "bandit"]
    assert bandit["run"][:5] == ["python", "-m", "bandit", "-r", "."]
    assert "./tests,./changes,./evals" in bandit["run"][bandit["run"].index("-x") + 1]
    assert bandit["run"][-2:] == ["--severity-level", "medium"]
    write(root / "requirements.txt", "requests\n")
    assert scanners_mod.plan(root, "python")[0]["run"][-2:] == ["-r", "requirements.txt"]

    (node,) = scanners_mod.plan(root, "node")
    assert node["install"] is None
    assert node["run"] == ["npm", "audit", "--audit-level=high", "--json"]
    assert node["report"] == "npm-audit.json" and node["report_from_stdout"]
    assert scanners_mod.plan(root, "unknown") == []
    assert "No deterministic scanner" in scanners_mod.summary(
        scanners_mod.run_all(root, "rust", dry_run=False)
    )


def test_run_all_dry_run_runs_nothing(tmp_path):
    root = tmp_path / "proj"
    root.mkdir()
    results = scanners_mod.run_all(root, "python", dry_run=True)
    assert [s["status"] for s in results["scanners"]] == ["dry-run", "dry-run"]
    assert list(root.iterdir()) == []
    text = scanners_mod.summary(results)
    assert "| pip-audit | dry-run |" in text and "| bandit | dry-run |" in text


def test_run_one_statuses(tmp_path):
    root = tmp_path / "proj"
    root.mkdir()

    def py(code: str) -> list[str]:
        return ["python", "-c", code]

    clean = scanners_mod.run_one(
        root, {"name": "ok", "install": py("pass"), "run": py("open('ok.json','w').write('[]')"),
               "report": "ok.json"}, dry_run=False,
    )  # fmt: skip
    assert clean["status"] == "clean" and clean["exit_code"] == 0
    assert clean["report_path"] == "ok.json"
    found = scanners_mod.run_one(
        root, {"name": "hits", "install": None,
               "run": py("import sys; open('hits.json','w').write('[1]'); sys.exit(1)"),
               "report": "hits.json"}, dry_run=False,
    )  # fmt: skip
    assert found["status"] == "findings" and found["exit_code"] == 1
    stdout = scanners_mod.run_one(
        root, {"name": "out", "install": None,
               "run": py("print('{\"v\": 1}'); raise SystemExit(1)"),
               "report": "out.json", "report_from_stdout": True}, dry_run=False,
    )  # fmt: skip
    assert stdout["status"] == "findings"
    assert json.loads((root / "out.json").read_text(encoding="utf-8")) == {"v": 1}
    broken = scanners_mod.run_one(
        root, {"name": "gone", "install": None, "run": ["no-such-scanner-anywhere"],
               "report": "gone.json"}, dry_run=False,
    )  # fmt: skip
    assert broken["status"] == "error" and broken["exit_code"] == 127
    failed = scanners_mod.run_one(
        root, {"name": "inst", "install": py("raise SystemExit(3)"), "run": py("pass"),
               "report": "x.json"}, dry_run=False,
    )  # fmt: skip
    assert failed["status"] == "install-failed" and failed["install_exit_code"] == 3
    text = scanners_mod.summary({"language": "python", "scanners": [clean, found, broken]})
    assert "| ok | clean | 0 | `ok.json` |" in text
    assert "| hits | findings | 1 | `hits.json` |" in text
    assert "| gone | error | 127 | - |" in text and "- gone: could not start" in text


def test_scanners_command_never_fails_the_step(tmp_path, capsys, monkeypatch):
    root = tmp_path / "proj"
    write(root / "package.json", "{}\n")
    summary_file = tmp_path / "summary.md"
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(summary_file))
    code, out = run_cli(capsys, "scanners", "--root", str(root), "--dry-run")
    assert code == 0 and "| npm-audit | dry-run |" in out
    assert not summary_file.exists()  # a dry run writes no job summary
    monkeypatch.setattr(
        scanners_mod,
        "plan",
        lambda root, language: [
            {"name": "boom", "install": None, "run": ["no-such-scanner-anywhere"], "report": "b"}
        ],
    )
    code, out = run_cli(capsys, "scanners", "--root", str(root), "--json")
    assert code == 0 and out["scanners"][0]["status"] == "error"
    assert "| boom | error |" in summary_file.read_text(encoding="utf-8")


# --- the workflow -----------------------------------------------------------------------------
def _workflow() -> dict:
    yaml = pytest.importorskip("yaml")
    data = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return data


def test_workflow_is_weekly_and_dispatchable():
    data = _workflow()
    triggers = data.get("on", data.get(True))  # YAML 1.1 reads a bare `on` key as True
    (schedule,) = triggers["schedule"]
    assert schedule["cron"] == "23 6 * * 1"
    minute, hour, dom, month, dow = schedule["cron"].split()
    assert dom == "*" and month == "*" and re.fullmatch(r"[0-6]", dow)  # once a week
    assert "workflow_dispatch" in triggers
    assert data["permissions"] == {
        "contents": "write",
        "pull-requests": "write",
        "issues": "write",
    }
    assert data["concurrency"]["group"] == "sdlc-scan"
    assert data["concurrency"]["cancel-in-progress"] is False


def test_workflow_run_lines_call_python_only():
    steps = _workflow()["jobs"]["scan"]["steps"]
    runs = [s["run"] for s in steps if "run" in s]
    assert runs
    for run in runs:
        assert "\n" not in run.strip(), run
        assert "${{" not in run, run
        # the pinned Claude Code install is the one line every phase workflow shares; the
        # pin step pipes the default branch's copy of the pin script into python (0.2.24)
        assert run.startswith("python ") or run in (CLAUDE_INSTALL, PIN_RUN), run
    joined = "\n".join(runs)
    assert "framework/plugin/scan/cli.py review" in joined and "--plugin-dir framework" in joined
    assert "framework/plugin/scan/cli.py route" in joined and "--max-findings 3" in joined
    assert "framework/plugin/scan/cli.py scanners" in joined
    order = [
        i
        for i, s in enumerate(steps)
        for cmd in ("cli.py review", "cli.py route", "cli.py scanners")
        if cmd in s.get("run", "")
    ]
    assert order == sorted(order) and len(order) == 3


def test_workflow_keeps_the_reports_and_never_fails_on_scanner_findings():
    steps = _workflow()["jobs"]["scan"]["steps"]
    scanners = next(s for s in steps if "cli.py scanners" in s.get("run", ""))
    assert scanners.get("continue-on-error") is True
    assert scanners.get("if") == "${{ always() }}"
    uploads = [s for s in steps if str(s.get("uses", "")).startswith("actions/upload-artifact@v4")]
    kept = next(s for s in uploads if "scan-findings.json" in s["with"]["path"])
    assert kept["if"] == "${{ always() }}" and kept["with"]["if-no-files-found"] == "ignore"
    for name in ("scan-findings.json", "scan-run.json", "pip-audit.json", "bandit.json",
                 "npm-audit.json"):  # fmt: skip
        assert name in kept["with"]["path"]
    review = next(s for s in steps if "cli.py review" in s.get("run", ""))
    assert set(review["env"]) >= {"ANTHROPIC_API_KEY", "CLAUDE_CODE_OAUTH_TOKEN"}
    assert "GITHUB_TOKEN" not in review["env"]  # the review reads code; it needs no GitHub
