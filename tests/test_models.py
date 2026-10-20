"""ROADMAP R7: the session's, the adversarial reviewer's and the devil's advocate's models
(``plugin/panel/models.py``), the exact model match, the reviewer's model record and the gate's
``reviewer_model`` check."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from panel import ledger, models

from gate import gate
from tests.model_records import ADVOCATE_MODEL, REVIEWER_MODEL, write_reviewer_record
from tests.test_gate import (
    git,
    on_base,
    project,  # noqa: F401 - the fixture
    verdict,
)

ROOT = Path(__file__).resolve().parents[1]
PANEL_CLI = ROOT / "plugin" / "panel" / "cli.py"
CONFIG = {
    "session_model": {"default": "claude-opus-5-5", "b": "claude-fable-5-1"},
    "adversarial_model": "claude-opus-5-5",
    "panel_advocate_model": "claude-fable-5-1",
}


# --- the resolver -------------------------------------------------------------------------------
def test_the_session_model_is_one_model_or_a_default_with_phase_entries():
    assert models.session_model({}, "c") is None  # unset: the CLI's default
    assert models.session_model({"session_model": " claude-opus-5-5 "}, "b") == "claude-opus-5-5"
    assert models.session_model(CONFIG, "b") == "claude-fable-5-1"
    assert models.session_model(CONFIG, "c") == "claude-opus-5-5"
    # the (e) review pass is a run of (e); a run kind with no entry takes the default
    only_e = {"session_model": {"default": "claude-opus-5-5", "e": "claude-fable-5-1"}}
    assert models.session_model(only_e, "review") == "claude-fable-5-1"
    assert models.session_model(only_e, "triage") == "claude-opus-5-5"
    assert models.session_model({"session_model": {"b": "fable"}}, "c") is None
    assert models.session_model({"session_model": 5}, "c") is None


def test_the_advocate_never_runs_on_the_session_s_model():
    # at (b) the session runs on Fable, the advocate's model: the advocate takes the
    # reviewer's model; elsewhere it keeps its own
    assert models.advocate_model(CONFIG, "b") == "claude-opus-5-5"
    assert models.advocate_model(CONFIG, "c") == ADVOCATE_MODEL
    # an alias against an id of its family is the same model
    alias_session = {**CONFIG, "session_model": "fable"}
    assert models.advocate_model(alias_session, "d") == "claude-opus-5-5"
    # with no reviewer model there is nothing to switch to: today's behaviour
    assert models.advocate_model({"panel_advocate_model": "opus"}, "b") == "opus"
    assert models.advocate_model({}, "b") is None


def test_aliases_and_the_pins_that_make_them_resolve_to_the_configured_ids():
    assert models.alias("claude-opus-5-5[1m]") == "opus" and models.alias("fable") == "fable"
    assert models.alias("arn:aws:bedrock:x") is None and models.alias(None) is None
    assert models.alias_pins(CONFIG, "c") == {
        "ANTHROPIC_DEFAULT_OPUS_MODEL": "claude-opus-5-5",
        "ANTHROPIC_DEFAULT_FABLE_MODEL": "claude-fable-5-1",
    }
    # at (b) both sub-agents are Opus: one pin
    assert models.alias_pins(CONFIG, "b") == {"ANTHROPIC_DEFAULT_OPUS_MODEL": "claude-opus-5-5"}
    # a pin the workflow sets wins; an alias is never pinned to itself
    env = {"ANTHROPIC_DEFAULT_OPUS_MODEL": "claude-opus-5"}
    assert models.alias_pins(CONFIG, "c", env) == {
        "ANTHROPIC_DEFAULT_FABLE_MODEL": "claude-fable-5-1"
    }
    assert (
        models.alias_pins({"adversarial_model": "opus", "panel_advocate_model": "fable"}, "c") == {}
    )
    # two ids of one family: the reviewer's wins
    two = {"adversarial_model": "claude-opus-5-5", "panel_advocate_model": "claude-opus-5"}
    assert models.alias_pins(two, "c") == {"ANTHROPIC_DEFAULT_OPUS_MODEL": "claude-opus-5-5"}


def test_a_configuration_no_alias_can_satisfy_is_named():
    """The review of R7's diff: an alias in the session's own family runs on the session's
    model (NOTES section 51), and one pin serves one family."""
    assert models.conflicts(CONFIG, "c") == [] and models.conflicts(CONFIG, "b") == []
    old_session = {**CONFIG, "session_model": "claude-opus-5"}
    assert (
        "in the family of the session's model claude-opus-5"
        in models.conflicts(old_session, "c")[0]
    )
    via_env = models.conflicts(CONFIG, "c", {"SDLC_MODEL": "claude-opus-5"})
    assert via_env and "adversarial_model claude-opus-5-5" in via_env[0]
    pinned = models.conflicts(CONFIG, "c", {"ANTHROPIC_DEFAULT_FABLE_MODEL": "claude-fable-5"})
    assert pinned == [
        "the workflow pins ANTHROPIC_DEFAULT_FABLE_MODEL=claude-fable-5, not claude-fable-5-1 "
        "(panel_advocate_model)"
    ]
    two = {"adversarial_model": "claude-opus-5-5", "panel_advocate_model": "claude-opus-5"}
    assert "two ids of one family" in models.conflicts(two, "c")[-1]
    # the advocate switches on the session's family, not only on the same id
    fable5 = {**CONFIG, "session_model": "claude-fable-5"}
    assert models.advocate_model(fable5, "c") == "claude-opus-5-5"
    assert models.advocate_model(CONFIG, "c", "claude-fable-5") == "claude-opus-5-5"


def test_the_panel_cli_prints_the_phase_s_models(tmp_path):
    (tmp_path / "sdlc.yaml").write_text(
        "session_model:\n  default: claude-opus-5-5\n  b: claude-fable-5-1\n"
        "adversarial_model: claude-opus-5-5\npanel_advocate_model: claude-fable-5-1\n",
        encoding="utf-8",
    )
    proc = subprocess.run(
        [sys.executable, str(PANEL_CLI), "models", "--root", str(tmp_path), "--phase", "b"],
        capture_output=True, text=True, encoding="utf-8",
    )  # fmt: skip
    assert proc.returncode == 0, proc.stderr
    assert json.loads(proc.stdout) == {
        "phase": "b",
        "session": "claude-fable-5-1",
        "reviewer": {"model": "claude-opus-5-5", "alias": "opus"},
        "advocate": {"model": "claude-opus-5-5", "alias": "opus"},
        "pins": {"ANTHROPIC_DEFAULT_OPUS_MODEL": "claude-opus-5-5"},  # a run by hand exports them
        "conflicts": [],
    }


# --- the exact match ----------------------------------------------------------------------------
def test_a_full_id_is_met_by_itself_and_its_snapshots_only():
    m = ledger.model_matches
    assert not m("claude-opus-5-5", "claude-opus-5") and not m("claude-opus-5", "claude-opus-5-5")
    assert m("claude-haiku-4-5", "claude-haiku-4-5-20251001")
    assert not m("claude-haiku-4-5", "claude-haiku-4-5-1")
    assert m("claude-opus-5-5[1m]", "claude-opus-5-5[1m]") and m("opus", "claude-opus-5-5")


# --- the reviewer's model record ----------------------------------------------------------------
def test_the_reviewer_s_model_record_is_judged_for_its_writer_head_and_model(tmp_path):
    verdict_path = tmp_path / "adversarial-review-c.json"
    head = "abc1234def5678"

    def problems(**kw):
        path = write_reviewer_record(verdict_path, kw.pop("recorded", head), **kw)
        return ledger.reviewer_model_problems(
            path.read_text(encoding="utf-8"), REVIEWER_MODEL, "c", head
        )

    assert problems() == []
    assert "not on claude-opus-5-5" in problems(models=("claude-opus-5",))[0]
    assert "unproved" in problems(models=())[0]
    assert "written by the main session" in problems(agent=None)[0]
    assert "written by general-purpose" in problems(agent="general-purpose")[0]
    assert "changed after the reviewer wrote it" in problems(recorded="0000000")[0]
    assert "not written whole by the reviewer" in problems(recorded="")[0]
    bad = json.dumps({"head": head, "agent_type": "sdlc:adversarial-reviewer", "models": 5})
    assert "not a list" in ledger.reviewer_model_problems(bad, REVIEWER_MODEL, "c", head)[0]
    assert "is missing" in ledger.reviewer_model_problems(None, REVIEWER_MODEL, "c", head)[0]
    assert "unreadable" in ledger.reviewer_model_problems("{", REVIEWER_MODEL, "c", head)[0]


# --- the gate's reviewer_model check ------------------------------------------------------------
def _check(result):
    return next(ch for ch in result.checks if ch.name == "reviewer_model")


def test_the_gate_parks_a_verdict_whose_reviewer_ran_on_another_model(project):  # noqa: F811
    root, change = project
    path = verdict(root, "c")  # the template pins adversarial_model, and the hook recorded it
    result = gate.run_gate(root, "0001", "c", dry_run=True)
    assert result.result == "continue" and _check(result).ok
    write_reviewer_record(path, git(root, "rev-parse", "HEAD").strip(), models=("claude-opus-5",))
    result = gate.run_gate(root, "0001", "c", dry_run=True)
    check = _check(result)
    assert result.result == "park" and not check.ok
    assert "ran on claude-opus-5, not on claude-opus-5-5" in check.reason
    assert "adversarial_model" in check.need and "pins" in check.need
    # no record at all parks too
    (change / "evidence" / "adversarial-review-c.model.json").unlink()
    assert "is missing" in _check(gate.run_gate(root, "0001", "c", dry_run=True)).reason


def test_the_reviewer_model_park_is_never_the_panel_s(project):  # noqa: F811
    root, change = project
    path = verdict(root, "c")
    write_reviewer_record(path, git(root, "rev-parse", "HEAD").strip(), models=("claude-opus-5",))
    proc = subprocess.run(
        [sys.executable, str(PANEL_CLI), "items", "--root", str(root), "--id", "0001",
         "--phase", "c"],
        capture_output=True, text=True, encoding="utf-8",
    )  # fmt: skip
    out = json.loads(proc.stdout)
    assert [p["check"] for p in out["parks"]] == ["reviewer_model"] and out["pending"] == []
    assert "reviewer_model" in ledger.NEVER_TO_PANEL


def test_without_adversarial_model_the_reviewer_s_model_is_not_checked(project):  # noqa: F811
    root, change = project

    def unpin(r: Path) -> None:
        cfg = r / "sdlc.yaml"
        text = cfg.read_text(encoding="utf-8")
        cfg.write_text(text.replace("adversarial_model: claude-opus-5-5\n", ""), encoding="utf-8")

    on_base(root, unpin, "owner: no reviewer model")
    verdict(root, "c")
    (change / "evidence" / "adversarial-review-c.model.json").unlink()
    check = _check(gate.run_gate(root, "0001", "c", dry_run=True))
    assert check.ok and "names no adversarial_model" in check.reason


# NOTES §54: what CLI 2.1.278 printed on the design run of the sample's change 0017
UNKNOWN_REVIEWER = (
    '[claude-code:unrecognized_model] {"model":"claude-opus-5-5",'
    '"query_source":"agent:custom:sdlc:adversarial-reviewer"}'
)


def test_an_unrecognized_model_line_names_the_configured_model_once():
    """R63: the line the pinned CLI prints for a sub-agent model it does not know, read from
    the session's stderr; a model sdlc.yaml names is reported once, in the order printed."""
    err = "\n".join(
        [
            "workspace trust: skipped",
            UNKNOWN_REVIEWER,
            UNKNOWN_REVIEWER,
            '[claude-code:unrecognized_model] {"model": "claude-fable-5-1"}',
        ]
    )
    assert models.unrecognized(err, CONFIG, "c") == ["claude-opus-5-5", "claude-fable-5-1"]
    # the run's own --model counts as the session's (here the design phase on Opus)
    env = {"SDLC_MODEL": "claude-opus-5-5"}
    assert models.unrecognized(UNKNOWN_REVIEWER, CONFIG, "b", env) == ["claude-opus-5-5"]


def test_an_unrecognized_model_sdlc_yaml_does_not_name_is_not_reported():
    other = '[claude-code:unrecognized_model] {"model":"claude-haiku-9-9"}'
    assert models.unrecognized(other, CONFIG, "c") == []
    assert models.unrecognized("", CONFIG, "c") == [] and models.unrecognized(None, {}, "c") == []
    # no model configured: nothing is the owner's to raise the pin for
    assert models.unrecognized(UNKNOWN_REVIEWER, {}, "c") == []
    # a stderr with no such line (the fix round on 2.1.304, NOTES §54)
    assert models.unrecognized("workspace trust: skipped\n", CONFIG, "b") == []
