"""Layer-1 tests for plugin/review: the deterministic half of the review pass (build guide
step 26; article p.32-35).

Signatures are stable and line-independent; validation catches every shape problem the gate
would trip over; the tally is recomputed, never taken on trust; the REVIEW.md framework rule
"no pre-existing test edited in a fix task" is decided against a real fixture repository; the
seen-record answers the second-occurrence question across two change ids; and the CLI's three
subcommands behave as `/sdlc-deploy` calls them.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import types
from pathlib import Path

import pytest
from review import cli as review_cli
from review import findings as fmod

from gate import artifacts as art
from state import conventions as c
from state import status as status_mod

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "sample-python-project"
INIT = ROOT / "plugin" / "init" / "sdlc_init.py"
STATE_CLI = ROOT / "plugin" / "state" / "cli.py"
PROMPT_FILE = ROOT / "plugin" / "review" / "REVIEW_PROMPT.md"

BUG = {
    "pass": "bugs",
    "severity": "important",
    "file": "sample_pkg/calc.py",
    "line": 12,
    "summary": "add() returns None when b is 0, so callers crash.",
    "rule": "",
}
NIT = {
    "pass": "compliance",
    "severity": "nit",
    "file": "sample_pkg/calc.py",
    "line": 3,
    "summary": "Docstring does not say what the units are.",
    "rule": "",
}


def payload(head: str, items=None, **extra) -> dict:
    data = {
        "schema_version": 1,
        "head": head,
        "findings": list(items if items is not None else [BUG, NIT]),
        "tally": {"important": 99, "nit": 99, "nits_omitted": 2},
        "at": "2026-09-21T10:00:00Z",
    }
    data.update(extra)
    return data


# --- fixture repository -----------------------------------------------------------------------
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


def make_project(tmp_path: Path, change_type: str = "fix") -> tuple[Path, Path]:
    """A copy of the fixture project, initialised, with change 0001 on main and a phase-(c)
    branch that modifies the pre-existing ``tests/test_calc.py`` and adds ``tests/test_new.py``
    — the diff the framework rule of build guide step 25 judges."""
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
    git(root, "commit", "-q", "-m", "sdlc-init (as if the 0000 PR merged)")
    proc = run_py(
        str(STATE_CLI),
        "new-change",
        "--root",
        str(root),
        "--title",
        "Rounding is off by one",
        "--type",
        change_type,
        cwd=root,
    )
    assert proc.returncode == 0, proc.stderr
    change = c.find_change_dir(root, "0001")
    assert change is not None
    git(root, "add", ".")
    git(root, "commit", "-q", "-m", "intent(0001) (as if the a PR merged)")
    git(root, "checkout", "-q", "-b", "sdlc/0001/c")
    calc_test = root / "tests" / "test_calc.py"
    write(calc_test, calc_test.read_text(encoding="utf-8") + "\n\ndef test_more():\n    assert 1\n")
    write(root / "tests" / "test_new.py", "def test_reproduces_the_bug():\n    assert 1\n")
    git(root, "add", ".")
    git(root, "commit", "-q", "-m", "fix(0001): reproducing test and the fix")
    return root, change


def head_of(root: Path) -> str:
    return git(root, "rev-parse", "HEAD").strip()


def record_findings(change: Path, data: dict) -> Path:
    path = change / art.EVIDENCE_DIR / art.REVIEW_FINDINGS
    write(path, json.dumps(data, indent=2))
    return path


def run_cli(argv: list[str]) -> int:
    return review_cli.main(argv)


# --- signatures -------------------------------------------------------------------------------
def test_signature_is_stable_and_ignores_the_line_number():
    first = fmod.signature(BUG)
    assert re.fullmatch(r"[0-9a-f]{16}", first)
    assert fmod.signature(dict(BUG)) == first  # deterministic across calls and copies
    moved = dict(BUG, line=871)
    assert fmod.signature(moved) == first  # the same mistake further down the file
    renumbered = dict(BUG, summary="add() returns None when b is 7, so callers crash.")
    assert fmod.signature(renumbered) == first  # digits are normalised away
    shouted = dict(BUG, summary="Add() RETURNS None when b is 0 -- so callers crash!!")
    assert fmod.signature(shouted) == first  # case, punctuation and spacing are normalised
    assert fmod.signature(dict(BUG, file="SAMPLE_PKG\\calc.py")) == first


def test_signature_separates_pass_file_and_wording():
    first = fmod.signature(BUG)
    assert fmod.signature(dict(BUG, file="sample_pkg/other.py")) != first
    assert fmod.signature({**BUG, "pass": "security"}) != first
    assert fmod.signature(dict(BUG, summary="Something else entirely.")) != first


def test_normalise_file_keeps_dotfiles_and_drops_only_a_leading_dot_slash():
    """``lstrip("./")`` ate every leading "." and "/", so .github/... lost its dot."""
    assert fmod.normalise_file(".github/workflows/ci.yml") == ".github/workflows/ci.yml"
    assert fmod.normalise_file("./.github/workflows/ci.yml") == ".github/workflows/ci.yml"
    assert fmod.normalise_file("././src/a.py") == "src/a.py"
    assert fmod.normalise_file(".env") == ".env"
    assert fmod.normalise_file("  Sample_Pkg\\calc.py  ") == "sample_pkg/calc.py"
    assert fmod.strip_dot_slash("./tests/test_a.py") == "tests/test_a.py"


def test_normalise_summary_truncates_to_eighty_characters():
    assert len(fmod.normalise_summary("word " * 60)) == 80


# --- validation -------------------------------------------------------------------------------
def test_validate_accepts_a_good_file_and_an_abbreviated_head():
    head = "a" * 40
    assert fmod.validate(payload(head), head) == []
    assert fmod.validate(payload(head[:10]), head) == []  # prefix-compatible, as the gate does


def test_validate_reports_each_problem():
    head = "a" * 40

    def problems(**over) -> str:
        return " | ".join(fmod.validate({**payload(head), **over}, head))

    assert "schema_version" in problems(schema_version=2)
    assert "no 'head'" in problems(head=None)
    assert "HEAD is" in " | ".join(fmod.validate(payload("b" * 40), head))
    assert "'findings' must be a list" in problems(findings={})
    assert "findings[0] has no 'file'" in " | ".join(
        fmod.validate(payload(head, [dict(BUG, file="")]), head)
    )
    for field in ("pass", "severity", "summary"):
        assert f"findings[0] has no '{field}'" in " | ".join(
            fmod.validate(payload(head, [{k: v for k, v in BUG.items() if k != field}]), head)
        )
    assert "severity must be one of" in " | ".join(
        fmod.validate(payload(head, [dict(BUG, severity="blocker")]), head)
    )
    assert "pass must be one of" in " | ".join(
        fmod.validate(payload(head, [dict(BUG, **{"pass": "style"})]), head)
    )
    assert "not an object" in " | ".join(fmod.validate(payload(head, ["nope"]), head))
    assert fmod.validate([], head) == ["the findings file is not a JSON object"]


# --- normalisation ----------------------------------------------------------------------------
def test_normalise_fills_signatures_recomputes_the_tally_and_sorts():
    data = fmod.normalise(payload("c" * 40, [NIT, BUG]))
    assert [f["severity"] for f in data["findings"]] == ["important", "nit"]
    assert all(f["signature"] == fmod.signature(f) for f in data["findings"])
    assert data["tally"] == {"important": 1, "nit": 1, "nits_omitted": 2}
    assert data["schema_version"] == 1
    kept = fmod.normalise(payload("c" * 40, [BUG], tally={"nits_omitted": "many"}))
    assert kept["tally"] == {"important": 1, "nit": 0, "nits_omitted": 0}


def test_normalise_sorts_important_first_then_by_file_and_line():
    a = dict(NIT, file="a.py", line=9)
    b = dict(NIT, file="a.py", line=2)
    data = fmod.normalise(payload("c" * 40, [a, b, BUG]))
    assert [(f["file"], f["line"]) for f in data["findings"]] == [
        ("sample_pkg/calc.py", 12),
        ("a.py", 2),
        ("a.py", 9),
    ]


# --- the framework rule (build guide step 25; REVIEW.md) ---------------------------------------
def test_framework_findings_flag_a_pre_existing_test_in_a_fix_change(tmp_path):
    root, change = make_project(tmp_path, change_type="fix")
    st = status_mod.read_status(change)
    files = ["tests/test_calc.py", "tests/test_new.py", "sample_pkg/calc.py"]
    existed = {"tests/test_calc.py", "sample_pkg/calc.py"}
    found = fmod.framework_findings(root, change, st, files, lambda rel: rel in existed)
    assert [f["file"] for f in found] == ["tests/test_calc.py"]
    only = found[0]
    assert only["severity"] == "important" and only["pass"] == "compliance"
    assert only["rule"] == "REVIEW.md: no test edits in a fix task"
    assert "pre-existing test file modified in a fix-type change" in only["summary"]


def test_framework_findings_are_silent_for_a_feature_change(tmp_path):
    root, change = make_project(tmp_path, change_type="feature")
    st = status_mod.read_status(change)
    assert fmod.framework_findings(root, change, st, ["tests/test_calc.py"], lambda _r: True) == []


def test_framework_findings_use_the_real_diff_and_base(tmp_path):
    """Against the fixture repository: the modified pre-existing test is flagged, the new test
    and the change folder are not."""
    root, change = make_project(tmp_path, change_type="fix")
    st = status_mod.read_status(change)
    record_findings(change, payload(head_of(root), []))  # an untracked file inside the change
    extra, _note = review_cli._framework(root, change, st, None)
    assert [f["file"] for f in extra] == ["tests/test_calc.py"]


def test_test_path_globs_fall_back_to_the_defaults(tmp_path):
    (tmp_path / "sdlc.yaml").write_text("profile: standard\n", encoding="utf-8")
    assert fmod.test_path_globs(tmp_path) == fmod.DEFAULT_TEST_PATHS


# --- the record of findings already seen ------------------------------------------------------
def test_update_seen_round_trip_and_second_occurrence():
    record, repeated = fmod.update_seen({}, [BUG, NIT], "0001", "2026-09-21T10:00:00Z")
    assert repeated == []
    sig = fmod.signature(BUG)
    assert record[sig]["count"] == 1
    assert record[sig]["first_change"] == record[sig]["last_change"] == "0001"
    assert record[sig]["file"] == BUG["file"]

    same_change, again = fmod.update_seen(record, [BUG], "0001", "2026-09-21T11:00:00Z")
    assert again == []  # twice inside one change is one mistake, not a pattern
    assert same_change[sig]["count"] == 2

    later, repeated = fmod.update_seen(record, [dict(BUG, line=99)], "0002", "2026-09-22T09:00:00Z")
    assert [f["signature"] for f in repeated] == [sig]
    assert repeated[0]["first_change"] == "0001" and repeated[0]["change_id"] == "0002"
    assert later[sig] == {
        "count": 2,
        "first_change": "0001",
        "last_change": "0002",
        "summary": BUG["summary"],
        "file": BUG["file"],
        "last_seen": "2026-09-22T09:00:00Z",
    }


def test_seen_record_path_is_the_projects_changes_folder(tmp_path):
    assert fmod.seen_record_path(tmp_path) == tmp_path / "changes" / ".review-seen.json"


def test_claude_md_lines_are_one_per_finding_and_deduplicated():
    repeated = [
        dict(BUG, first_change="0001", change_id="0003"),
        dict(BUG, first_change="0001", change_id="0003"),
        dict(NIT, first_change="0002", change_id="0003"),
    ]
    lines = fmod.claude_md_lines(repeated)
    assert lines == [
        f"- {BUG['summary'].rstrip('.')} (seen in changes 0001 and 0003; bugs)",
        f"- {NIT['summary'].rstrip('.')} (seen in changes 0002 and 0003; compliance)",
    ]
    assert fmod.claude_md_lines([]) == []


def test_render_summary_shows_the_tally_and_every_important_finding():
    text = fmod.render_summary(fmod.normalise(payload("d" * 40)))
    assert "**1 Important, 1 nits**" in text
    assert "2 further nits omitted" in text
    assert "`sample_pkg/calc.py:12` — add() returns None" in text
    assert "### Important" in text and "### Nits" in text
    assert "No findings" in fmod.render_summary(fmod.normalise(payload("d" * 40, [])))


# --- the prompt -----------------------------------------------------------------------------
def test_review_prompt_renders_with_str_format():
    rendered = review_cli.render_prompt(
        PROMPT_FILE.read_text(encoding="utf-8"),
        change_id="0001",
        title="Rounding is off by one",
        branch="sdlc/0001/c",
        head="e" * 40,
        base="origin/main",
        root="/tmp/proj",
        change_dir="/tmp/proj/changes/0001-rounding",
    )
    assert re.search(r"\{[a-z_]+\}", rendered) is None  # every placeholder is known and filled
    assert '"schema_version": 1' in rendered  # the JSON braces were doubled, so they survive
    assert '"tally": {"important": 0, "nit": 0, "nits_omitted": 0}' in rendered


def test_cli_prompt_prints_the_change_the_head_and_the_json_shape(tmp_path, capsys):
    root, change = make_project(tmp_path)
    assert run_cli(["prompt", "--root", str(root), "--id", "0001"]) == 0
    out = capsys.readouterr().out
    assert "0001" in out and head_of(root) in out
    assert "Rounding is off by one" in out and "sdlc/0001/c" in out
    assert str(change.resolve()).replace("\\", "/") in out
    assert '"severity": "important | nit"' in out and '"findings": [' in out


def test_cli_prompt_on_an_unknown_id_is_a_usage_error(tmp_path, capsys):
    root, _change = make_project(tmp_path)
    assert run_cli(["prompt", "--root", str(root), "--id", "0099"]) == 2


# --- validate -------------------------------------------------------------------------------
def test_cli_validate_rewrites_the_file_and_records_the_signatures(tmp_path, capsys):
    root, change = make_project(tmp_path, change_type="feature")
    path = record_findings(change, payload(head_of(root)))
    assert run_cli(["validate", "--root", str(root), "--id", "0001"]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["ok"] is True and result["problems"] == []
    assert result["tally"] == {"important": 1, "nit": 1, "nits_omitted": 2}
    assert len(result["important"]) == 1
    assert "1 Important" in result["summary"]

    written = json.loads(path.read_text(encoding="utf-8"))
    assert [f["signature"] for f in written["findings"]] == [
        fmod.signature(BUG),
        fmod.signature(NIT),
    ]
    assert written["tally"] == result["tally"]
    assert b"\r\n" not in path.read_bytes()  # LF newlines on Windows too

    record = json.loads((root / "changes" / ".review-seen.json").read_text(encoding="utf-8"))
    assert record[fmod.signature(BUG)]["first_change"] == "0001"
    assert not (change / art.EVIDENCE_DIR / fmod.PROPOSALS_FILE).exists()


def test_cli_validate_is_re_runnable_and_adds_the_framework_finding_once(tmp_path, capsys):
    root, change = make_project(tmp_path, change_type="fix")
    path = record_findings(change, payload(head_of(root), []))
    for _ in range(2):
        assert run_cli(["validate", "--root", str(root), "--id", "0001"]) == 0
        result = json.loads(capsys.readouterr().out)
        assert result["tally"]["important"] == 1
        assert [f["file"] for f in result["important"]] == ["tests/test_calc.py"]
    written = json.loads(path.read_text(encoding="utf-8"))
    assert len(written["findings"]) == 1  # the second run does not duplicate it


def test_cli_validate_rejects_a_stale_head_and_a_missing_file(tmp_path, capsys):
    root, change = make_project(tmp_path, change_type="feature")
    path = record_findings(change, payload("f" * 40))
    assert run_cli(["validate", "--root", str(root), "--id", "0001"]) == 3
    result = json.loads(capsys.readouterr().out)
    assert result["ok"] is False and any("HEAD is" in p for p in result["problems"])
    assert "signature" not in path.read_text(encoding="utf-8")  # a stale file is not rewritten
    assert not (root / "changes" / ".review-seen.json").exists()

    path.unlink()
    assert run_cli(["validate", "--root", str(root), "--id", "0001"]) == 3
    assert "missing" in json.loads(capsys.readouterr().out)["problems"][0]


def test_cli_validate_writes_the_proposals_on_the_second_occurrence(tmp_path, capsys):
    root, change = make_project(tmp_path, change_type="feature")
    record_findings(change, payload(head_of(root), [BUG]))
    assert run_cli(["validate", "--root", str(root), "--id", "0001"]) == 0
    assert json.loads(capsys.readouterr().out)["proposals"] == []

    # the same finding in change 0002, on the same branch: the second occurrence
    second_dir, st = status_mod.new_change(root, "Another rounding fix")
    record_findings(second_dir, payload(head_of(root), [dict(BUG, line=40)]))
    assert run_cli(["validate", "--root", str(root), "--id", st.id]) == 0
    result = json.loads(capsys.readouterr().out)
    assert len(result["repeated"]) == 1
    assert result["proposals"] == [
        f"- {BUG['summary'].rstrip('.')} (seen in changes 0001 and {st.id}; bugs)"
    ]
    proposals = second_dir / art.EVIDENCE_DIR / fmod.PROPOSALS_FILE
    assert result["proposals"][0] in proposals.read_text(encoding="utf-8")

    # the finding is gone from the next review of that change: so is the proposals file
    record_findings(second_dir, payload(head_of(root), []))
    assert run_cli(["validate", "--root", str(root), "--id", st.id]) == 0
    assert not proposals.exists()


def test_cli_validate_no_record_leaves_the_seen_file_alone(tmp_path, capsys):
    root, change = make_project(tmp_path, change_type="feature")
    record_findings(change, payload(head_of(root), [BUG]))
    assert run_cli(["validate", "--root", str(root), "--id", "0001", "--no-record"]) == 0
    capsys.readouterr()
    assert not fmod.seen_record_path(root).exists()


# --- check-run -------------------------------------------------------------------------------
@pytest.fixture
def fake_github(monkeypatch):
    """``plugin/pr/github.py`` is written by its own task; the review only calls into it."""
    calls: list[dict] = []
    module = types.ModuleType("pr.github")

    def create_check_run(repo, head_sha, name, conclusion, title, summary):
        calls.append(
            {
                "repo": repo,
                "head_sha": head_sha,
                "name": name,
                "conclusion": conclusion,
                "title": title,
                "summary": summary,
            }
        )
        return {"id": 7, "html_url": "https://github.test/check/7"}

    module.create_check_run = create_check_run
    monkeypatch.setitem(sys.modules, "pr.github", module)
    return calls


def test_cli_check_run_posts_the_summary(tmp_path, capsys, monkeypatch, fake_github):
    root, change = make_project(tmp_path, change_type="feature")
    record_findings(change, payload(head_of(root)))
    assert run_cli(["validate", "--root", str(root), "--id", "0001"]) == 0
    capsys.readouterr()
    monkeypatch.setattr(review_cli.gitops, "github_repo", lambda *_a, **_k: "owner/repo")

    assert run_cli(["check-run", "--root", str(root), "--id", "0001", "--phase", "e"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["route"] == "check-run" and out["conclusion"] == "failure"
    assert out["result"] == {"id": 7, "html_url": "https://github.test/check/7"}
    assert len(fake_github) == 1
    call = fake_github[0]
    assert call["repo"] == "owner/repo" and call["name"] == "sdlc/review"
    assert call["head_sha"] == head_of(root) and call["title"] == "1 Important, 1 nits"
    assert "### Important" in call["summary"]


def test_cli_check_run_succeeds_when_no_important_finding_stands(
    tmp_path, capsys, monkeypatch, fake_github
):
    root, change = make_project(tmp_path, change_type="feature")
    record_findings(change, payload(head_of(root), [NIT]))
    monkeypatch.setattr(review_cli.gitops, "github_repo", lambda *_a, **_k: "owner/repo")
    assert run_cli(["check-run", "--root", str(root), "--id", "0001"]) == 0
    assert json.loads(capsys.readouterr().out)["conclusion"] == "success"
    assert fake_github[0]["conclusion"] == "success"


def test_cli_check_run_reports_no_route_when_github_cannot_post(tmp_path, capsys, monkeypatch):
    """``pr/github.py`` answers with ``route: none`` (no gh, no installation token) rather than
    raising; the phase carries on and the PR description still shows the summary."""
    root, change = make_project(tmp_path, change_type="feature")
    record_findings(change, payload(head_of(root), [NIT]))
    module = types.ModuleType("pr.github")
    module.create_check_run = lambda *_a, **_k: {"route": "none", "ok": False, "reason": "no token"}
    monkeypatch.setitem(sys.modules, "pr.github", module)
    monkeypatch.setattr(review_cli.gitops, "github_repo", lambda *_a, **_k: "owner/repo")
    assert run_cli(["check-run", "--root", str(root), "--id", "0001"]) == 0
    assert json.loads(capsys.readouterr().out)["reason"] == "no token"


def test_cli_check_run_without_a_github_remote_reports_no_route(tmp_path, capsys):
    root, change = make_project(tmp_path, change_type="feature")
    record_findings(change, payload(head_of(root), [NIT]))
    assert run_cli(["check-run", "--root", str(root), "--id", "0001"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out == {"route": "none", "reason": "no GitHub remote: nothing to post the check run to"}
