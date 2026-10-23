"""Layer-1 tests of R25 parts 1-2 with M8 (choice 257; ``gate/limits.py``): the change's spend is
rebuilt from the runner's stored session results, never from ``evidence/spend.json``; each
run line names the credential that paid and the session's time; the runner guards the stored
results; an outer bound (the turn limit, the CLI's budget stop, the runner's timeout) parks."""

from __future__ import annotations

import json
from pathlib import Path

from gate import limits


def result(evidence: Path, name: str, **fields) -> Path:
    evidence.mkdir(parents=True, exist_ok=True)
    path = evidence / name
    path.write_text(json.dumps(fields), encoding="utf-8")
    return path


def meta(credential: str, seconds: float, timed_out: bool = False) -> dict:
    return {"credential": credential, "seconds": seconds, "timed_out": timed_out, "at": "t"}


def test_the_spend_is_rebuilt_from_the_stored_results_not_the_ledger(tmp_path):
    """M8: emptying spend.json used to give the next session the whole budget again."""
    ev = tmp_path / "evidence"
    result(ev, "claude-c.json", total_cost_usd=4.0, sdlc_run=meta("api_key", 600))
    result(ev, "claude-fix.json", total_cost_usd=1.5, sdlc_run=meta("api_key", 60))
    result(ev, "claude-fix-2.json", total_cost_usd=2.5, sdlc_run=meta("api_key", 120))
    (ev / "spend.json").write_text('{"total_usd": 0, "entries": []}', encoding="utf-8")
    (ev / "claude-md-proposals.md").write_text("not a run\n", encoding="utf-8")
    (ev / "claude-c.stderr.txt").write_text("stderr\n", encoding="utf-8")
    spent = limits.spend_from_runs(ev)
    assert spent["total_usd"] == 8.0 and spent["unknown"] == 0
    assert [e["source"] for e in spent["entries"]] == [
        "claude-c.json",
        "claude-fix.json",
        "claude-fix-2.json",
    ]
    assert limits.budget_left({"max_budget_usd": 10}, ev) == (10.0, 8.0, 2.0)


def test_the_records_are_ordered_by_run_and_number(tmp_path):
    ev = tmp_path / "evidence"
    for name in ("claude-fix-10.json", "claude-fix-2.json", "claude-fix.json", "claude-b.json"):
        result(ev, name, total_cost_usd=1)
    names = [p.name for p in limits.run_record_paths(ev)]
    assert names == ["claude-b.json", "claude-fix.json", "claude-fix-2.json", "claude-fix-10.json"]


def test_each_line_names_its_credential_and_time_and_a_timeout_has_no_figure(tmp_path):
    ev = tmp_path / "evidence"
    result(ev, "claude-c.json", total_cost_usd=3.0, num_turns=40, sdlc_run=meta("oauth", 3600))
    result(ev, "claude-d.json", total_cost_usd=0.5, subtype="error_max_turns", duration_ms=90000)
    result(ev, "claude-e.json", sdlc_run=meta("oauth", 7500, timed_out=True), raw="")
    lines = limits.run_lines(ev)
    assert [(ln["credential"], ln["usd"], ln["seconds"], ln["stop"]) for ln in lines] == [
        ("oauth", 3.0, 3600.0, None),
        (None, 0.5, 90.0, "error_max_turns"),
        ("oauth", None, 7500.0, "timeout"),
    ]
    spent = limits.spend_from_runs(ev)
    assert spent["unknown"] == 1 and spent["total_usd"] == 3.5
    assert spent["by_credential"]["oauth"] == {"runs": 2, "seconds": 11100.0, "usd": 3.0}
    line = limits.spend_line(ev)
    assert line.startswith("Spend: 3.50 USD over 3 sessions (subscription token: 2 runs, 3 h 05")
    assert "credential not recorded: 1 run, 2 min, 0.50 USD" in line
    assert line.endswith("; 1 without a figure (a timeout or a crash), not counted.")


def test_no_session_no_spend_line(tmp_path):
    assert limits.spend_line(tmp_path / "evidence") == ""


def test_the_gate_reads_the_rebuilt_total(tmp_path):
    from gate.checks import GateContext
    from state import status as status_mod

    change = tmp_path / "changes" / "0001-x"
    ev = change / "evidence"
    result(ev, "claude-c.json", total_cost_usd=12.0)
    (ev / "run-c.json").write_text('{"started_at": null, "spend_usd": 1.0}', encoding="utf-8")
    (ev / "spend.json").write_text('{"total_usd": 0, "entries": []}', encoding="utf-8")
    st = status_mod.Status(id="0001", slug="x", title="x", phase="c")
    ctx = GateContext(
        root=tmp_path, change_dir=change, phase="c", status=st,
        config={"gate": {"max_budget_usd": 10}}, diff=None, human_gate=False,
    )  # fmt: skip
    check = limits.check_limits(ctx)
    assert not check.ok and "12.00 USD spent on the change" in check.reason


def test_a_record_the_session_touched_is_put_back_and_named(tmp_path):
    ev = tmp_path / "evidence"
    first = result(ev, "claude-c.json", total_cost_usd=4.0)
    second = result(ev, "claude-fix.json", total_cost_usd=2.0)
    before = limits.snapshot_run_records(ev)
    first.write_text('{"total_cost_usd": 0}', encoding="utf-8")  # changed
    second.unlink()  # deleted
    result(ev, "claude-fix-9.json", total_cost_usd=0)  # planted
    result(ev, "claude-fix-2.json", total_cost_usd=1.0)  # the runner's own record of this run
    reasons = limits.run_record_mismatches(ev, before, {"claude-fix-2.json"})
    assert reasons == [
        "evidence/claude-c.json: the session changed it; only the runner writes it",
        "evidence/claude-fix-9.json: the session created it; only the runner writes it",
        "evidence/claude-fix.json: the session deleted it; only the runner writes it",
    ]
    assert json.loads(first.read_text(encoding="utf-8"))["total_cost_usd"] == 4.0
    assert second.is_file() and not (ev / "claude-fix-9.json").exists()
    assert (ev / "claude-fix-2.json").is_file()
    assert limits.run_record_mismatches(ev, limits.snapshot_run_records(ev)) == []


def test_the_outer_bounds_are_named():
    assert limits.outer_bound({"subtype": "error_max_turns", "num_turns": 400}, 1) == (
        "stopped at the turn limit (400 turns)"
    )
    assert (
        limits.outer_bound({"subtype": "error_max_budget_usd", "total_cost_usd": 9.5}, 1)
        == "stopped at the session's budget (9.50 USD)"
    )
    assert limits.outer_bound(None, 124, "claude did not finish within 7500s") == (
        "stopped by the runner's timeout (claude did not finish within 7500s)"
    )
    # anything else is not a bound: an error result, a crash, a CLI that could not start
    assert limits.outer_bound({"subtype": "error_during_execution"}, 1) is None
    assert limits.outer_bound(None, 127, "claude could not start") is None
    assert limits.outer_bound({"subtype": "success"}, 0) is None
