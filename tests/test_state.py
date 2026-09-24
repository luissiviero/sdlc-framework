import json
import subprocess
import sys
from pathlib import Path

import pytest

from state import cli, status, yamlish
from state import conventions as c

PLUGIN = Path(__file__).resolve().parents[1] / "plugin"


def test_branch_names_and_parse():
    assert c.branch_name("0001", "a") == "sdlc/0001/a"
    assert c.parse_branch("sdlc/0042/c") == ("0042", "c")
    assert c.parse_branch("main") is None
    with pytest.raises(ValueError):
        c.branch_name("1", "a")
    with pytest.raises(ValueError):
        c.branch_name("0001", "z")


def test_labels():
    assert c.ready_label("a") == "sdlc:a-ready"
    assert c.approved_label("c") == "sdlc:c-approved"
    assert c.NEEDS_HUMAN_LABEL == "sdlc:needs-human"
    labels = c.all_labels()
    assert "sdlc:d-approved" in labels and "sdlc:needs-human" in labels
    assert all(label.startswith("sdlc:") for label in labels)


def test_profiles_and_human_gates():
    assert c.HUMAN_GATES["standard"] == {"a", "b", "e"}
    assert c.HUMAN_GATES["full"] == {"a", "b", "c", "d", "e"}
    assert c.HUMAN_GATES["lite"] == {"a", "e"}
    assert c.effective_profile("standard", "lite") == "lite"
    assert c.effective_profile(None, None) == "standard"
    assert c.is_human_gate("standard", "c") is False
    assert c.is_human_gate("full", "c") is True


def test_slugify():
    assert c.slugify("Claims status self-service") == "claims-status-self-service"
    assert c.slugify("  Ünïcode & stuff!! ") == "n-code-stuff"
    assert len(c.slugify("x" * 100)) <= 40
    assert c.slugify("!!!") == "change"


def test_new_change_allocates_sequential_ids(tmp_path):
    d1, s1 = status.new_change(tmp_path, "First change")
    d2, s2 = status.new_change(tmp_path, "Second: change")
    assert s1.id == "0001" and s2.id == "0002"
    assert d1.name == "0001-first-change" and d2.name == "0002-second-change"
    assert (d1 / "status.yaml").exists() and (d1 / "evidence" / ".gitkeep").exists()
    # idempotent per id
    d1b, s1b = status.new_change(tmp_path, "ignored title", change_id="0001")
    assert d1b == d1 and s1b.title == "First change"
    assert c.next_change_id(tmp_path) == "0003"


def test_status_round_trip_and_schema(tmp_path):
    change_dir, st = status.new_change(
        tmp_path, "Fix the thing", entry_route="incident", change_type="fix", external_ref="#12"
    )
    st.record_gate("a", "passed")
    st.set_phase("b")
    st.bump_iteration()
    status.write_status(change_dir, st)
    raw = yamlish.load_file(change_dir / "status.yaml")
    assert set(raw) == {
        "id",
        "slug",
        "title",
        "phase",
        "entry_route",
        "change_type",
        "profile_override",
        "gate",
        "parked_reason",
        "iterations",
        "external_ref",
        "risk_accepted",
        "tests_locked",
        "risk_accepted_by",  # decision 24: the label actors
        "iterations_reset_by",
        "tests_unlocked_by",
        "abandoned_reason",  # decision 25
        "created_at",
        "updated_at",
        "schema_version",
    }
    back = status.read_status(change_dir)
    assert back.phase == "b" and back.iterations == 1 and back.gate.result == "passed"
    assert back.entry_route == "incident" and back.change_type == "fix"
    assert back.tests_locked is False
    assert back.id == "0001"  # stays a string, never the int 1


def test_park_records_reason(tmp_path):
    change_dir, st = status.new_change(tmp_path, "Risky change")
    st.set_phase("c")
    st.park("touches auth (risk list)")
    status.write_status(change_dir, st)
    back = status.read_status(change_dir)
    assert back.parked_reason == "touches auth (risk list)"
    assert back.gate.result == "parked" and back.gate.phase == "c"


def test_a_park_that_a_later_gate_result_lifted_is_dropped_on_read(tmp_path):
    """status.yaml as plugins before 0.2.6 wrote it (change 0001 on the sample repository,
    2026-09-22): gate (b) passed, and the reason of the park it lifted still beside it. The
    file on main outlives every plugin release, so the reader is where it is normalised: a
    park is a gate result, and a parked_reason without one is a leftover."""
    change_dir, st = status.new_change(tmp_path, "Percent helper")
    st.set_phase("b")
    st.park("open_concerns: 1 open")
    st.gate.result = "passed"  # what record_gate did before 0.2.6, the reason kept
    st.gate.reason = "waiting for the owner at gate (b)"
    status.write_status(change_dir, st)
    text = status.status_path(change_dir).read_text(encoding="utf-8")
    assert 'parked_reason: "open_concerns: 1 open"' in text
    back = status.read_status(change_dir)
    assert back.parked_reason is None and back.gate.result == "passed"
    # the file itself is rewritten on request, once
    assert status.lift_stale_park(change_dir) == "open_concerns: 1 open"
    text = status.status_path(change_dir).read_text(encoding="utf-8")
    assert "parked_reason: null" in text and "result: passed" in text
    assert status.lift_stale_park(change_dir) is None
    # a real park is a parked gate result, and holds
    st.park("open_concerns: 1 open")
    status.write_status(change_dir, st)
    assert status.read_status(change_dir).parked_reason == "open_concerns: 1 open"
    assert status.lift_stale_park(change_dir) is None


def test_invalid_status_rejected():
    with pytest.raises(ValueError):
        status.Status.from_dict({"id": "0001", "slug": "x", "title": "t", "phase": "q"})
    with pytest.raises(ValueError):
        status.Status.from_dict({"id": "0001", "slug": "x", "title": "t", "bogus": 1})


def test_pyyaml_reads_status_file(tmp_path):
    yaml = pytest.importorskip("yaml")
    change_dir, _ = status.new_change(tmp_path, "Any")
    data = yaml.safe_load((change_dir / "status.yaml").read_text(encoding="utf-8"))
    assert data["id"] == "0001" and data["profile_override"] is None


def test_cli_new_change_and_show(tmp_path, capsys):
    rc = cli.main(["new-change", "--root", str(tmp_path), "--title", "CLI change", "--type", "fix"])
    assert rc == 0
    out = json.loads(capsys.readouterr().out)
    assert out["id"] == "0001" and out["branch"] == "sdlc/0001/a"
    assert out["dir"] == "changes/0001-cli-change"
    rc = cli.main(["show", "--root", str(tmp_path), "--id", "0001"])
    assert rc == 0
    assert json.loads(capsys.readouterr().out)["status"]["change_type"] == "fix"


def test_cli_runs_as_a_script(tmp_path):
    proc = subprocess.run(
        [sys.executable, str(PLUGIN / "state" / "cli.py"), "labels"],
        capture_output=True,
        text=True,
        check=True,
    )
    assert "sdlc:needs-human" in json.loads(proc.stdout)


def test_slugify_falls_back_for_non_latin_titles():
    assert c.slugify("日本語のタイトル") == "change"


def test_next_change_id_considers_remote_ids(tmp_path):
    status.new_change(tmp_path, "one")
    assert c.next_change_id(tmp_path, ["0007"]) == "0008"


def test_github_repo_parsing(tmp_path, monkeypatch):
    from state import gitops

    cases = {
        "https://github.com/o/r.git": "o/r",
        "https://github.com/o/r": "o/r",
        "git@github.com:o/r.git": "o/r",
        "ssh://git@github.com/o/r": "o/r",
        "https://github.company.com/o/r": None,
        "https://gitlab.com/o/r": None,
    }
    for url, expected in cases.items():
        monkeypatch.setattr(gitops, "remote_url", lambda root, remote="origin", u=url: u)
        assert gitops.github_repo(tmp_path) == expected, url


def test_status_rejects_bool_iterations():
    with pytest.raises(ValueError):
        status.Status.from_dict({"id": "0001", "slug": "x", "title": "t", "iterations": True})


def test_new_change_adopts_folder_without_status(tmp_path):
    folder = tmp_path / "changes" / "0000-sdlc-init"
    folder.mkdir(parents=True)
    (folder / "CLAUDE.proposed.md").write_text("# x\n", encoding="utf-8")
    change_dir, st = status.new_change(tmp_path, "sdlc-init", change_id="0000")
    assert change_dir == folder and st.slug == "sdlc-init" and (folder / "status.yaml").exists()


def test_cli_lock_and_unlock_tests_round_trip(tmp_path, capsys):
    """Build guide step 25: the build run locks the tests of a fix, only the owner unlocks."""
    root = str(tmp_path)
    assert cli.main(["new-change", "--root", root, "--title", "Fix it", "--type", "fix"]) == 0
    capsys.readouterr()
    assert cli.main(["lock-tests", "--root", root, "--id", "0001"]) == 0
    assert json.loads(capsys.readouterr().out)["tests_locked"] is True
    change_dir = c.find_change_dir(tmp_path, "0001")
    assert status.read_status(change_dir).tests_locked is True
    assert cli.main(["unlock-tests", "--root", root, "--id", "0001"]) == 0
    assert json.loads(capsys.readouterr().out)["tests_locked"] is False
    assert status.read_status(change_dir).tests_locked is False
    assert cli.main(["lock-tests", "--root", root, "--id", "0099"]) == 2


def test_work_branch_keeps_the_build_branch_through_d_and_e():
    """OPERATING_MODEL section 8: (c) carries "the build PR that stays open through (d) and
    (e)"; an incident (f) produces a new intent, which is (a) work."""
    assert c.work_branch("0001", "a") == "sdlc/0001/a"
    assert c.work_branch("0001", "b") == "sdlc/0001/b"
    assert [c.work_branch("0001", p) for p in "cde"] == ["sdlc/0001/c"] * 3
    assert c.work_branch("0001", "f") == "sdlc/0001/a"
    assert c.branch_name("0001", "d") == "sdlc/0001/d"  # the literal name is still available
    assert c.parse_branch(c.work_branch("0042", "e")) == ("0042", "c")
    with pytest.raises(ValueError):
        c.work_branch("0001", "z")
    with pytest.raises(ValueError):
        c.work_branch("1", "c")


def _git(root: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=root, capture_output=True, text=True, check=True, encoding="utf-8"
    ).stdout


@pytest.fixture
def repo(tmp_path):
    root = tmp_path / "proj"
    root.mkdir()
    (root / "README.md").write_text("# project\n", encoding="utf-8")
    _git(root, "init", "-q", "-b", "main")
    _git(root, "config", "user.email", "owner@example.com")
    _git(root, "config", "user.name", "Owner")
    _git(root, "add", ".")
    _git(root, "commit", "-q", "-m", "initial")
    return root


def _commit_phase(
    root: Path, phase: str, message: str, capsys, paths: list[str] = ()
) -> tuple[int, dict, str]:
    rc = cli.main(
        [
            "commit-phase",
            "--root",
            str(root),
            "--id",
            "0001",
            "--phase",
            phase,
            "--message",
            message,
            *(["--paths", *paths] if paths else []),
        ]
    )
    captured = capsys.readouterr()
    return rc, (json.loads(captured.out) if captured.out.strip() else {}), captured.err


def test_commit_phase_d_lands_on_the_build_branch(repo, capsys):
    """Phases (d) and (e) commit on sdlc/<id>/c — the build PR stays open through them — and
    never create a branch of their own (build guide step 24.3)."""
    root = repo
    assert cli.main(["new-change", "--root", str(root), "--title", "Percent helper"]) == 0
    capsys.readouterr()
    change = c.find_change_dir(root, "0001")
    (change / "intent.md").write_text("# Intent: percent helper\n", encoding="utf-8")
    rc, out, _ = _commit_phase(root, "a", "intent(0001): percent helper", capsys)
    assert rc == 0 and out["branch"] == "sdlc/0001/a" and out["work_branch"] == "sdlc/0001/a"

    # (d) before /sdlc-build ever ran: the build branch is missing, which is an error
    rc, _out, err = _commit_phase(root, "d", "test(0001): evidence", capsys)
    assert rc == 2 and "sdlc/0001/c" in err
    assert _git(root, "branch", "--list", "sdlc/0001/c").strip() == ""

    (change / "plan.md").write_text("# Plan\n", encoding="utf-8")
    rc, out, _ = _commit_phase(root, "c", "build(0001): percent helper", capsys)
    assert rc == 0 and out["branch"] == "sdlc/0001/c"

    (change / "evidence" / "test.log").write_text("# python -m pytest\nok\n", encoding="utf-8")
    rc, out, _ = _commit_phase(root, "d", "test(0001): evidence", capsys)
    assert rc == 0 and out["branch"] == "sdlc/0001/c" and out["work_branch"] == "sdlc/0001/c"
    assert _git(root, "rev-parse", "--abbrev-ref", "HEAD").strip() == "sdlc/0001/c"
    assert _git(root, "branch", "--list", "sdlc/0001/d").strip() == ""
    assert status.read_status(change).phase == "d"

    (change / "evidence" / "review-findings.json").write_text("{}", encoding="utf-8")
    rc, out, _ = _commit_phase(root, "e", "review(0001): findings", capsys)
    assert rc == 0 and out["branch"] == "sdlc/0001/c"
    branches = set(_git(root, "branch", "--format=%(refname:short)").split())
    assert branches == {"main", "sdlc/0001/a", "sdlc/0001/c"}
    tracked = _git(root, "ls-tree", "-r", "--name-only", "sdlc/0001/c").split()
    assert "changes/0001-percent-helper/evidence/test.log" in tracked


def test_commit_phase_refuses_a_departure_from_the_plan_without_plan_md(repo, capsys):
    """/sdlc-build commits through commit-phase, which the plan-sync hook never sees: the
    hook is registered on ``git *`` shell commands and this is a python one. The first gated
    build run (2026-09-22) made three such commits and heard about plan.md from the gate,
    twenty turns and two dollars later. The command applies the hook's rule itself, at the
    commit, so the denial arrives when it is cheap to act on."""
    root = repo
    assert cli.main(["new-change", "--root", str(root), "--title", "Percent helper"]) == 0
    capsys.readouterr()
    change = c.find_change_dir(root, "0001")
    (change / "plan.md").write_text(
        "# Plan\n\n## Files that change\n- `src/a.py` - the helper\n\n## Order of work\n- 1\n",
        encoding="utf-8",
    )
    (root / "src").mkdir()
    (root / "src" / "a.py").write_text("x = 1\n", encoding="utf-8")
    (root / "src" / "b.py").write_text("y = 1\n", encoding="utf-8")
    # phases before (c) are not checked: the plan is written on sdlc/<id>/b
    rc, out, _ = _commit_phase(root, "b", "design(0001): plan", capsys)
    assert rc == 0 and out["branch"] == "sdlc/0001/b"
    # inside the plan: commits, no plan.md needed
    rc, out, _ = _commit_phase(root, "c", "build(0001): step 1", capsys, ["src/a.py"])
    assert rc == 0 and out["branch"] == "sdlc/0001/c"
    # a departure without plan.md in the commit: refused, nothing committed
    head = _git(root, "rev-parse", "HEAD").strip()
    rc, out, err = _commit_phase(root, "c", "build(0001): departure", capsys, ["src/b.py"])
    assert rc == 2 and out == {}
    assert "plan.md is out of sync" in err and "src/b.py" in err and "src/a.py" not in err
    assert _git(root, "rev-parse", "HEAD").strip() == head
    assert "src/b.py" not in _git(root, "ls-tree", "-r", "--name-only", "HEAD")
    # the plan updated in the same commit: the departure is recorded, and commits
    (change / "plan.md").write_text(
        (change / "plan.md")
        .read_text(encoding="utf-8")
        .replace(
            "- `src/a.py` - the helper\n", "- `src/a.py` - the helper\n- `src/b.py` - export\n"
        ),
        encoding="utf-8",
    )
    rc, out, _ = _commit_phase(root, "c", "build(0001): departure, planned", capsys, ["src/b.py"])
    assert rc == 0 and out["commit"]
    assert "src/b.py" in _git(root, "ls-tree", "-r", "--name-only", "HEAD")


def test_a_passing_gate_lifts_the_park(tmp_path):
    """The first fix round of change 0001 (2026-09-22) re-ran gate (b) to `passed` and left
    the old parked_reason behind; the next phase's CI guard would have skipped the change."""
    change_dir, st = status.new_change(tmp_path, "Percent helper")
    st.park("open_concerns: 1 flagged concern(s) still open in spec.md")
    assert st.parked_reason and st.gate.result == "parked"
    st.record_gate("b", "passed", "waiting for the owner at gate (b)")
    assert st.parked_reason is None and st.gate.result == "passed"
    status.write_status(change_dir, st)
    assert status.read_status(change_dir).parked_reason is None


# --- deliverable 32.0: the owner's merge is gate (e) (decision 13) -----------------------------
def _parked_at_e(tmp_path: Path) -> tuple[Path, status.Status]:
    """Change 0001 on the sample repository after the owner merged PR #7 (2026-09-23): phase
    e, the thirteenth run's park on the iteration cap still recorded, iterations 3."""
    change_dir, st = status.new_change(tmp_path, "Percent helper")
    st.set_phase("e")
    st.iterations = 3
    st.park("limits: iteration cap reached (3 of 3)")
    status.write_status(change_dir, st)
    return change_dir, status.read_status(change_dir)


def test_merged_at_gate_e_derives_passed_and_is_pure(tmp_path):
    _change_dir, st = _parked_at_e(tmp_path)
    before = st.to_dict()
    derived = status.merged_at_gate_e(st)
    assert st.to_dict() == before  # the argument is never touched
    assert derived is not st
    assert derived.gate == status.Gate(
        phase="e", result="passed", reason=status.MERGED_AT_GATE_E_REASON, at=st.updated_at
    )
    assert "decision 13" in derived.gate.reason
    assert derived.parked_reason is None and derived.phase == "e" and derived.iterations == 3
    # already passed at (e): an unchanged copy
    again = status.merged_at_gate_e(derived)
    assert again is not derived and again.to_dict() == derived.to_dict()
    # any other phase: an unchanged copy, park included
    st.phase = "c"
    other = status.merged_at_gate_e(st)
    assert other.to_dict() == st.to_dict() and other.parked_reason


def test_read_status_on_the_default_branch_derives_gate_e_without_a_write(tmp_path):
    change_dir, _ = _parked_at_e(tmp_path)
    path = status.status_path(change_dir)
    text = path.read_text(encoding="utf-8")
    plain = status.read_status(change_dir)
    assert plain.gate.result == "parked" and plain.parked_reason
    merged = status.read_status(change_dir, on_default_branch=True)
    assert merged.gate.phase == "e" and merged.gate.result == "passed"
    assert merged.parked_reason is None
    assert path.read_text(encoding="utf-8") == text  # main is read-only for automation
    # phases c and d are left as they are, even on the default branch
    for phase in ("c", "d"):
        st = status.read_status(change_dir)
        st.phase = phase
        status.write_status(change_dir, st)
        on_main = status.read_status(change_dir, on_default_branch=True)
        assert on_main.gate.result == "parked" and on_main.parked_reason
        assert on_main.to_dict() == status.read_status(change_dir).to_dict()
    # an e that already passed its gate keeps its own record
    st = status.read_status(change_dir)
    st.phase = "e"
    st.record_gate("e", "passed", "waiting for the owner at gate (e)")
    status.write_status(change_dir, st)
    kept = status.read_status(change_dir, on_default_branch=True)
    assert kept.gate.reason == "waiting for the owner at gate (e)"
    assert kept.to_dict() == status.read_status(change_dir).to_dict()


def test_show_and_list_on_the_default_branch_print_the_derived_gate(repo, capsys):
    root = repo
    change_dir, _ = _parked_at_e(root)
    _git(root, "add", ".")
    _git(root, "commit", "-q", "-m", "merge PR #7 (the owner's merge is gate e)")
    text = status.status_path(change_dir).read_text(encoding="utf-8")

    assert cli.main(["show", "--root", str(root), "--id", "0001"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["status"]["gate"]["phase"] == "e" and out["status"]["gate"]["result"] == "passed"
    assert out["status"]["parked_reason"] is None
    assert out["derived"] == "gate: e/passed (derived: merged on main)"
    assert cli.main(["list", "--root", str(root)]) == 0
    (row,) = json.loads(capsys.readouterr().out)
    assert row["id"] == "0001" and row["parked_reason"] is None
    assert row["derived"] == "gate: e/passed (derived: merged on main)"
    assert status.status_path(change_dir).read_text(encoding="utf-8") == text
    assert _git(root, "status", "--porcelain") == ""

    # on the build branch the park is the change's real state, and nothing is derived
    _git(root, "checkout", "-q", "-b", "sdlc/0001/c")
    assert cli.main(["show", "--root", str(root), "--id", "0001"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["status"]["gate"]["result"] == "parked" and "derived" not in out
    assert cli.main(["list", "--root", str(root)]) == 0
    (row,) = json.loads(capsys.readouterr().out)
    assert row["parked_reason"] and "derived" not in row


def test_show_outside_a_repository_derives_nothing(tmp_path, capsys):
    _parked_at_e(tmp_path)
    assert cli.main(["show", "--root", str(tmp_path), "--id", "0001"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["status"]["gate"]["result"] == "parked" and "derived" not in out


def test_merged_at_gate_e_reason_names_the_release_act_on_a_declared_production(tmp_path):
    """Review finding I4 (0.2.12): the merge passes gate (e) either way, but on a declared
    production the derived reason says the release label is the release workflow's second
    act (decision 13)."""
    change_dir, st = _parked_at_e(tmp_path)
    plain = status.merged_at_gate_e(st)
    assert plain.gate.result == "passed"
    assert plain.gate.reason == "merged by the owner: gate (e) is the merge (decision 13)"
    prod = status.merged_at_gate_e(st, production=True)
    assert prod.gate.phase == "e" and prod.gate.result == "passed"
    assert prod.parked_reason is None
    assert prod.gate.reason == (
        "merged by the owner: gate (e) is the merge (decision 13); the release approval "
        "sdlc:release-approved is the release workflow's second act on this declared production"
    )
    assert prod.gate.reason == status.MERGED_AT_GATE_E_PRODUCTION_REASON
    read = status.read_status(change_dir, on_default_branch=True, production=True)
    assert read.gate.reason == status.MERGED_AT_GATE_E_PRODUCTION_REASON
    assert status.read_status(change_dir, on_default_branch=True).gate.reason == (
        status.MERGED_AT_GATE_E_REASON
    )
    # production alone derives nothing off the default branch
    assert status.read_status(change_dir, production=True).gate.result == "parked"


def test_show_and_list_word_the_derived_reason_from_deploy_production(repo, capsys):
    root = repo
    _parked_at_e(root)
    _git(root, "add", ".")
    _git(root, "commit", "-q", "-m", "merge PR #7")

    # no sdlc.yaml: tolerated, the plain reason
    assert cli.main(["show", "--root", str(root), "--id", "0001"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["status"]["gate"]["reason"] == status.MERGED_AT_GATE_E_REASON

    for production, reason in (
        ("false", status.MERGED_AT_GATE_E_REASON),
        ("true", status.MERGED_AT_GATE_E_PRODUCTION_REASON),
    ):
        (root / "sdlc.yaml").write_text(
            f"deploy:\n  action: none\n  production: {production}\n", encoding="utf-8"
        )
        assert cli.main(["show", "--root", str(root), "--id", "0001"]) == 0
        out = json.loads(capsys.readouterr().out)
        assert out["status"]["gate"]["result"] == "passed"
        assert out["status"]["gate"]["reason"] == reason
        assert out["derived"] == "gate: e/passed (derived: merged on main)"
        assert cli.main(["list", "--root", str(root)]) == 0
        (row,) = json.loads(capsys.readouterr().out)
        assert row["derived"] == "gate: e/passed (derived: merged on main)"


# --- deliverable 4(b): commit-phase commits only what changed under its paths ------------------
def _committed(root: Path, ref: str = "HEAD") -> list[str]:
    out = _git(root, "diff-tree", "--no-commit-id", "--name-status", "-r", ref)
    return sorted(line.replace("\t", " ") for line in out.splitlines() if line.strip())


def test_commit_phase_commits_only_the_changed_paths(repo, capsys):
    """Until 0.2.12 commit-phase ran ``git add`` on its paths and committed the whole index,
    so anything staged beforehand (a hook, an earlier partial command, the session) rode
    along in the phase's commit."""
    root = repo
    assert cli.main(["new-change", "--root", str(root), "--title", "Percent helper"]) == 0
    capsys.readouterr()
    change = c.find_change_dir(root, "0001")
    rel = "changes/0001-percent-helper"
    (change / "intent.md").write_text("# Intent\n", encoding="utf-8")
    (change / "notes.md").write_text("scratch\n", encoding="utf-8")
    (root / "unrelated.txt").write_text("staged by someone else\n", encoding="utf-8")
    _git(root, "add", "unrelated.txt")

    rc, out, _ = _commit_phase(root, "a", "intent(0001): percent helper", capsys)
    assert rc == 0 and out["commit"]
    committed = _committed(root)
    assert f"A {rel}/intent.md" in committed and f"A {rel}/notes.md" in committed
    assert f"A {rel}/status.yaml" in committed  # untracked inside the change folder: included
    assert not any("unrelated.txt" in f for f in committed)
    # the unrelated file is still staged, and still not committed
    assert _git(root, "diff", "--cached", "--name-only").split() == ["unrelated.txt"]

    # a deletion and a rename inside the folder are recorded; --paths outside it are included
    (change / "notes.md").unlink()
    (change / "intent.md").rename(change / "intent-v2.md")
    (root / "src").mkdir()
    (root / "src" / "helper.py").write_text("x = 1\n", encoding="utf-8")
    rc, out, _ = _commit_phase(
        root, "a", "intent(0001): tidy", capsys, ["src/helper.py", "ruff.toml"]
    )
    assert rc == 0 and out["commit"]
    assert _committed(root) == sorted(
        [f"D {rel}/notes.md", f"D {rel}/intent.md", f"A {rel}/intent-v2.md", "A src/helper.py"]
    )
    assert _git(root, "diff", "--cached", "--name-only").split() == ["unrelated.txt"]

    # a deleted --paths entry outside the folder is recorded too (no exists() filter any more)
    (root / "src" / "helper.py").unlink()
    rc, out, _ = _commit_phase(root, "a", "intent(0001): drop helper", capsys, ["src/helper.py"])
    assert rc == 0 and _committed(root) == ["D src/helper.py"]

    # nothing changed under the paths: no commit, the staged file untouched
    head = _git(root, "rev-parse", "HEAD").strip()
    rc, out, _ = _commit_phase(root, "a", "intent(0001): again", capsys)
    assert rc == 0 and out["commit"] is None and out["base"] is None
    assert _git(root, "rev-parse", "HEAD").strip() == head
    assert _git(root, "diff", "--cached", "--name-only").split() == ["unrelated.txt"]


def test_gitops_changed_files_and_commit_paths(repo):
    from state import gitops

    root = repo
    folder = root / "changes" / "0001-x"
    folder.mkdir(parents=True)
    (folder / "a b.md").write_text("spaces\n", encoding="utf-8")
    (folder / "c[1].md").write_text("glob characters are names\n", encoding="utf-8")
    (root / "README.md").write_text("# changed, not under the paths\n", encoding="utf-8")
    assert gitops.changed_files(root, ["changes\\0001-x"]) == [
        "changes/0001-x/a b.md",
        "changes/0001-x/c[1].md",
    ]
    assert gitops.changed_files(root, []) == []
    assert gitops.changed_files(root, ["does/not/exist"]) == []
    sha = gitops.commit_paths(root, ["changes/0001-x"], "x")
    assert sha and _committed(root) == ["A changes/0001-x/a b.md", "A changes/0001-x/c[1].md"]
    assert _git(root, "status", "--porcelain").strip() == "M README.md"
    assert gitops.commit_paths(root, ["changes/0001-x"], "again") is None
    # a staged rename: both sides are changed files, and the commit records it
    _git(root, "mv", "changes/0001-x/a b.md", "changes/0001-x/moved.md")
    assert gitops.changed_files(root, ["changes/0001-x"]) == [
        "changes/0001-x/a b.md",
        "changes/0001-x/moved.md",
    ]
    assert gitops.commit_paths(root, ["changes/0001-x"], "rename")
    assert _committed(root) == ["A changes/0001-x/moved.md", "D changes/0001-x/a b.md"]
    # a file added and deleted again before the commit: nothing to commit
    (folder / "gone.md").write_text("x\n", encoding="utf-8")
    _git(root, "add", "changes/0001-x/gone.md")
    (folder / "gone.md").unlink()
    assert gitops.commit_paths(root, ["changes/0001-x"], "nothing") is None


# --- decision 24: the owner's un-park labels, recorded with their actor --------------------------
def test_record_owner_label_performs_the_act_and_keeps_the_actor(tmp_path):
    change_dir, st = status.new_change(tmp_path, "Labels")
    st.iterations = 3
    st.lock_tests()
    st.record_owner_label(c.ACCEPT_RISK_LABEL, "luissiviero", ["auth", "data migrations"])
    st.record_owner_label(c.RESET_ITERATIONS_LABEL, "luissiviero")
    st.record_owner_label(c.UNLOCK_TESTS_LABEL, "reviewer-2")
    status.write_status(change_dir, st)
    back = status.read_status(change_dir)
    assert back.risk_accepted == ["auth", "data migrations"]
    assert back.risk_accepted_by == [
        {"item": "auth", "actor": "luissiviero"},
        {"item": "data migrations", "actor": "luissiviero"},
    ]
    assert back.iterations == 0 and back.iterations_reset_by == "luissiviero"
    assert back.tests_locked is False and back.tests_unlocked_by == "reviewer-2"
    with pytest.raises(ValueError):
        st.record_owner_label("sdlc:needs-human", "luissiviero")
    with pytest.raises(ValueError):
        st.record_owner_label(c.RESET_ITERATIONS_LABEL, "  ")
    assert set(c.UNPARK_LABELS) <= set(c.all_labels())
    assert c.RELEASE_APPROVED_LABEL in c.all_labels()


def test_unpark_perform_honours_a_person_and_rejects_the_automation_identity(tmp_path):
    from state import unpark

    change_dir, st = status.new_change(tmp_path, "Labels")
    st.phase = "c"
    st.iterations = 4
    gate_file = change_dir / "evidence" / "gate-c.json"
    gate_file.write_text(
        json.dumps(
            {
                "checks": [
                    {"name": "risk_list", "ok": False, "details": {"hits": {"auth": ["src/auth"]}}}
                ]
            }
        ),
        encoding="utf-8",
    )
    assert unpark.risk_hits(change_dir, "c") == ["auth"]
    assert unpark.risk_hits(change_dir, "b") == [] and unpark.risk_hits(change_dir, None) == []
    present = {
        c.ACCEPT_RISK_LABEL: "luissiviero",
        c.RESET_ITERATIONS_LABEL: "github-actions[bot]",
        c.UNLOCK_TESTS_LABEL: "dependabot[bot]",
    }
    performed, rejected = unpark.perform(
        st, present, ["github-actions[bot]"], unpark.risk_hits(change_dir, "c")
    )
    assert performed == [{"label": c.ACCEPT_RISK_LABEL, "actor": "luissiviero", "items": ["auth"]}]
    assert [r["label"] for r in rejected] == [c.RESET_ITERATIONS_LABEL, c.UNLOCK_TESTS_LABEL]
    assert all("cannot un-park itself" in r["reason"] for r in rejected)
    assert st.iterations == 4 and st.risk_accepted_by == [{"item": "auth", "actor": "luissiviero"}]
    # accept-risk with no recorded hit accepts nothing and is left on the PR
    st2 = status.new_change(tmp_path, "No hit", change_id="0002")[1]
    performed, rejected = unpark.perform(st2, {c.ACCEPT_RISK_LABEL: "luissiviero"}, [], [])
    assert performed == [] and "nothing to accept" in rejected[0]["reason"]
    # a project's own automation identity counts as automation too
    performed, rejected = unpark.perform(
        st2, {c.RESET_ITERATIONS_LABEL: "ci-robot"}, ["ci-robot"], []
    )
    assert performed == [] and rejected[0]["actor"] == "ci-robot"


class _FakeGitHub:
    """The three calls ``unpark.apply_from_pr`` makes, answered from recorded payloads."""

    def __init__(self, labels, actors, ok=True):
        self.labels, self.actors, self.ok = labels, actors, ok
        self.removed: list[str] = []

    def pr_by_number(self, repo, number, cwd=None):
        if not self.ok:
            return {"ok": False, "reason": "HTTP 404"}
        return {"ok": True, "number": number, "labels": list(self.labels)}

    def label_actor(self, repo, number, label):
        return {"ok": True, "actor": self.actors.get(label)}

    def set_labels(self, repo, number, add, remove, cwd=None):
        self.removed += remove
        return {"ok": True, "added": add, "removed": remove}


def test_apply_from_pr_records_the_actor_and_removes_the_performed_label(tmp_path):
    from state import unpark

    change_dir, st = status.new_change(tmp_path, "Labels")
    st.iterations = 3
    status.write_status(change_dir, st)
    github = _FakeGitHub(
        ["sdlc:needs-human", c.RESET_ITERATIONS_LABEL, c.UNLOCK_TESTS_LABEL],
        {c.RESET_ITERATIONS_LABEL: "luissiviero", c.UNLOCK_TESTS_LABEL: "github-actions[bot]"},
    )
    out = unpark.apply_from_pr(tmp_path, change_dir, {}, "owner/name", 7, github=github)
    assert out["ok"] and [p["label"] for p in out["performed"]] == [c.RESET_ITERATIONS_LABEL]
    assert [r["label"] for r in out["rejected"]] == [c.UNLOCK_TESTS_LABEL]
    assert github.removed == [c.RESET_ITERATIONS_LABEL]  # the rejected one stays on the PR
    back = status.read_status(change_dir)
    assert back.iterations == 0 and back.iterations_reset_by == "luissiviero"
    assert back.tests_unlocked_by is None
    # no owner label at all: nothing read, nothing written
    quiet = _FakeGitHub(["sdlc:b-ready"], {})
    out = unpark.apply_from_pr(tmp_path, change_dir, {}, "owner/name", 7, github=quiet)
    assert out["ok"] and out["performed"] == [] and "no owner label" in out["reason"]
    # an unreadable PR consumes nothing and says why
    out = unpark.apply_from_pr(
        tmp_path, change_dir, {}, "owner/name", 7, github=_FakeGitHub([], {}, ok=False)
    )
    assert out["ok"] is False and "HTTP 404" in out["reason"]


def test_cli_apply_labels_uses_the_github_client(tmp_path, capsys, monkeypatch):
    from pr import github

    change_dir, st = status.new_change(tmp_path, "Labels")
    st.iterations = 2
    status.write_status(change_dir, st)
    fake = _FakeGitHub([c.RESET_ITERATIONS_LABEL], {c.RESET_ITERATIONS_LABEL: "luissiviero"})
    monkeypatch.setattr(github, "pr_by_number", fake.pr_by_number)
    monkeypatch.setattr(github, "label_actor", fake.label_actor)
    monkeypatch.setattr(github, "set_labels", fake.set_labels)
    rc = cli.main(
        ["apply-labels", "--root", str(tmp_path), "--id", "0001", "--repo", "o/n", "--pr", "7"]
    )
    out = json.loads(capsys.readouterr().out)
    assert rc == 0 and out["performed"][0]["actor"] == "luissiviero"
    assert status.read_status(change_dir).iterations == 0


# --- decision 25: abandon ------------------------------------------------------------------
def test_abandon_is_an_end_state(tmp_path):
    change_dir, st = status.new_change(tmp_path, "Abandoned")
    st.set_phase("b")
    st.park("open_concerns: 2 open")
    st.abandon("pull request 9 closed without a merge")
    status.write_status(change_dir, st)
    back = status.read_status(change_dir)
    assert back.phase == c.ABANDONED and back.abandoned
    assert back.abandoned_reason == "pull request 9 closed without a merge"
    assert back.parked_reason is None and back.gate.phase == "b"  # the record is kept
    with pytest.raises(ValueError):
        back.set_phase("c")
    assert status.merged_at_gate_e(back).phase == c.ABANDONED  # never reads as merged
    assert c.ABANDONED not in c.PHASES
    with pytest.raises(ValueError):
        c.branch_name("0001", c.ABANDONED)


def test_cli_abandon_marks_every_branch_of_the_change_on_the_remote(
    repo, tmp_path, capsys, monkeypatch
):
    """The abandon workflow runs on the closed PR's head; with --all-branches the other
    sdlc/<id>/* branches on the remote say the same, so a later dispatch of any phase
    finds the end state on the branch it switches to."""
    bare = tmp_path / "remote.git"
    _git(tmp_path, "init", "-q", "--bare", "-b", "main", str(bare))
    _git(repo, "remote", "add", "origin", str(bare))
    _git(repo, "push", "-q", "-u", "origin", "main")
    change_dir, _st = status.new_change(repo, "Abandoned")
    (change_dir / "intent.md").write_text("# Intent\n", encoding="utf-8")
    assert _commit_phase(repo, "a", "intent(0001): abandoned", capsys)[0] == 0
    _git(repo, "push", "-q", "-u", "origin", "sdlc/0001/a")
    assert _commit_phase(repo, "b", "design(0001): spec", capsys)[0] == 0
    _git(repo, "push", "-q", "-u", "origin", "sdlc/0001/b")
    _git(repo, "config", "--unset", "user.name")  # a runner has no identity of its own
    _git(repo, "config", "--unset", "user.email")
    (tmp_path / "gitconfig").write_text("", encoding="utf-8")  # nor a global one
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(tmp_path / "gitconfig"))
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
    rc = cli.main(
        ["abandon", "--root", str(repo), "--id", "0001", "--reason", "pull request 9 closed "
         "without a merge", "--push", "--all-branches"]
    )  # fmt: skip
    out = json.loads(capsys.readouterr().out)
    assert rc == 0 and out["phase"] == "abandoned"
    assert [b["branch"] for b in out["branches"]] == ["sdlc/0001/b", "sdlc/0001/a"]
    assert all(b["pushed"] and b["commit"] for b in out["branches"])
    for branch in ("sdlc/0001/a", "sdlc/0001/b"):
        text = _git(bare, "show", f"refs/heads/{branch}:changes/0001-abandoned/status.yaml")
        assert "phase: abandoned" in text and "pull request 9 closed" in text
        author = _git(bare, "log", "-1", "--format=%an", f"refs/heads/{branch}")
        assert author.strip() == "github-actions[bot]"
    assert _git(repo, "rev-parse", "--abbrev-ref", "HEAD").strip() == "sdlc/0001/b"
    # idempotent: a second close changes nothing
    rc = cli.main(
        ["abandon", "--root", str(repo), "--id", "0001", "--reason", "pull request 9 closed "
         "without a merge", "--push"]
    )  # fmt: skip
    out = json.loads(capsys.readouterr().out)
    assert rc == 0 and out["branches"][0]["commit"] is None and out["branches"][0]["already"]
    # commit-phase refuses to run a phase on it
    rc, _out, err = _commit_phase(repo, "c", "build(0001): nothing", capsys)
    assert rc == 2 and "abandoned" in err
    assert "sdlc/0001/c" not in _git(repo, "branch", "--list")  # nothing was created for it


def test_commit_phase_on_a_named_branch(repo, capsys):
    """Decision 22: a fix round on an intent PR a web session pushed from claude/... commits
    on that head, never on sdlc/<id>/a."""
    change_dir, _st = status.new_change(repo, "Web intent")
    (change_dir / "intent.md").write_text("# Intent\n", encoding="utf-8")
    _git(repo, "checkout", "-q", "-b", "claude/relaxed-x")
    _git(repo, "add", ".")
    _git(repo, "commit", "-q", "-m", "intent(0001): web intent")
    (change_dir / "intent.md").write_text("# Intent\nCorrected.\n", encoding="utf-8")
    rc = cli.main(
        ["commit-phase", "--root", str(repo), "--id", "0001", "--phase", "a", "--message",
         "fix(0001): corrected", "--branch", "claude/relaxed-x"]
    )  # fmt: skip
    out = json.loads(capsys.readouterr().out)
    assert rc == 0 and out["branch"] == "claude/relaxed-x" and out["commit"]
    assert _git(repo, "rev-parse", "--abbrev-ref", "HEAD").strip() == "claude/relaxed-x"
    assert "sdlc/0001/a" not in _git(repo, "branch", "--list")
    rc = cli.main(
        ["commit-phase", "--root", str(repo), "--id", "0001", "--phase", "a", "--message",
         "x", "--branch", "claude/missing"]
    )  # fmt: skip
    assert rc == 2 and "does not exist" in capsys.readouterr().err
