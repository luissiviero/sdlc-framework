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
    with pytest.raises(ValueError):
        c.slugify("!!!")


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
        "created_at",
        "updated_at",
        "schema_version",
    }
    back = status.read_status(change_dir)
    assert back.phase == "b" and back.iterations == 1 and back.gate.result == "passed"
    assert back.entry_route == "incident" and back.change_type == "fix"
    assert back.id == "0001"  # stays a string, never the int 1


def test_park_records_reason(tmp_path):
    change_dir, st = status.new_change(tmp_path, "Risky change")
    st.set_phase("c")
    st.park("touches auth (risk list)")
    status.write_status(change_dir, st)
    back = status.read_status(change_dir)
    assert back.parked_reason == "touches auth (risk list)"
    assert back.gate.result == "parked" and back.gate.phase == "c"


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
