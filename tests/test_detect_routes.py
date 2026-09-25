"""The gated routes, the dismissal store and the finding record of phase (f) (build guide
steps 37-39; decisions 14, 25 and 26; article p.43-47): route authorization and proposal
validation against a rendered template bands.yaml, the ``changes/.dismissed.json`` store and
the ``evidence/detection.json`` record, all on tmp files."""

from __future__ import annotations

import json
import re
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pytest
from detect import bands, dismissals, finding, routes
from detect.routes import Proposal, Resolved

TEMPLATE_BANDS = Path(__file__).resolve().parents[1] / "template" / "bands.yaml"
# the template's pull_request route (its name line, whatever comment follows, and its
# authorization line), to render a bands.yaml that does not list it
PR_ROUTE_RE = re.compile(r"^ *- name: pull_request\b[^\n]*\n *authorization: \w+[^\n]*\n", re.M)
TEMPLATE_ROUTES = {
    "pull_request": "preapproved",
    "runbook:quarantine-flaky-test": "preapproved",
    "runbook:revert-pr": "preapproved",
    "runbook:rollback-deploy": "go",
}
SHA = "a" * 40
NODE_ID = "tests/test_x.py::test_y"


# --- helpers --------------------------------------------------------------------------------


def _rendered_template() -> str:
    text = TEMPLATE_BANDS.read_text(encoding="utf-8")
    return text.replace("{{MAINTAIN_METRIC}}", "ci_test_failure_rate").replace(
        "{{MAINTAIN_SOURCE}}", "github-actions"
    )


def _load_bands(tmp_path: Path, text: str | None = None) -> bands.Bands:
    path = tmp_path / "bands.yaml"
    path.write_text(_rendered_template() if text is None else text, encoding="utf-8")
    return bands.load(path)


def _without_pull_request(text: str) -> str:
    out, count = PR_ROUTE_RE.subn("", text)
    assert count == 1, "the template lists pull_request exactly once"
    return out


@pytest.fixture
def template_bands(tmp_path: Path) -> bands.Bands:
    return _load_bands(tmp_path)


def _rollback_config(production: bool = True, **entry) -> dict:
    runbook = {"name": "rollback-deploy", "command": "x", "rehearsed_at": "2026-09-24"}
    runbook.update(entry)
    return {"deploy": {"production": production}, "maintain": {"runbooks": [runbook]}}


def _verdict(**kw) -> dict:
    verdict = {
        "tier": 3,
        "rule": "we1",
        "rules_hit": ["we1"],
        "mean": 0.1,
        "sigma": 0.02,
        "sigmas": 4.5,
        "latest": {"at": "2026-09-24T06:00:00Z", "value": 0.19, "meta": {}},
        "breach_start": "2026-09-24T06:00:00Z",
        "window_days": 30,
        "n_baseline": 22,
        "n_tail": 8,
        "direction": "above",
        "reason": "one point beyond 3 sigma",
    }
    verdict.update(kw)
    return verdict


def _record(**kw) -> dict:
    args = {
        "metric": "ci_test_failure_rate",
        "source": "github-actions",
        "verdict": _verdict(),
        "observations": [{"at": f"2026-09-{d:02d}", "value": 0.1} for d in range(1, 4)],
        "action": "propose",
        "failed_run_urls": ["https://example.invalid/run/1"],
        "commits": [{"sha": SHA, "subject": "fix", "at": "2026-09-23T00:00:00Z"}],
        "at": "2026-09-24T06:05:00Z",
    }
    args.update(kw)
    return finding.build_record(**args)


# --- finding: signature ---------------------------------------------------------------------


def test_signature_is_16_hex_and_stable():
    sig = finding.signature("ci_test_failure_rate", "we1")
    assert re.fullmatch(r"[0-9a-f]{16}", sig)
    assert finding.signature("ci_test_failure_rate", "we1") == sig


def test_signature_ignores_case_and_surrounding_whitespace():
    base = finding.signature("ci_test_failure_rate", "we1")
    assert finding.signature("  CI_Test_Failure_Rate ", " WE1\n") == base


def test_signature_differs_by_rule_and_by_kind():
    base = finding.signature("ci_test_failure_rate", "we1")
    assert finding.signature("ci_test_failure_rate", "we2") != base
    assert finding.signature("ci_test_failure_rate", "we1", kind="scan") != base
    assert finding.signature("ci_test_failure_rate", "we1", kind="detect") == base


# --- finding: record ------------------------------------------------------------------------


def test_build_record_validates_clean():
    record = _record()
    assert record["signature"] == finding.signature("ci_test_failure_rate", "we1")
    assert record["tier"] == 3 and record["kind"] == "detect"
    assert finding.validate(record) == []


def test_build_record_round_trips_through_json():
    record = _record()
    assert finding.validate(json.loads(json.dumps(record))) == []


def test_validate_tampered_signature_is_one_reason():
    record = _record()
    record["signature"] = "0" * 16
    assert finding.validate(record) == ["signature does not match metric and rule"]


def test_validate_wrong_tier_is_one_reason():
    for tier in (4, -1, "3", True):
        record = _record()
        record["tier"] = tier
        assert finding.validate(record) == ["tier is not an integer between 0 and 3"], tier


def test_validate_missing_metric_is_one_reason():
    record = _record()
    del record["metric"]
    assert finding.validate(record) == ["metric is missing"]


def test_validate_not_an_object():
    assert finding.validate([1, 2]) == ["detection.json is not a JSON object"]


def test_read_missing_file(tmp_path: Path):
    data, why = finding.read(tmp_path / "detection.json")
    assert data is None and why == "detection.json is missing"


def test_read_unreadable_file(tmp_path: Path):
    path = tmp_path / "detection.json"
    path.write_text("{not json", encoding="utf-8")
    data, why = finding.read(path)
    assert data is None and why.startswith("detection.json unreadable:")


def test_read_invalid_record_names_the_problem(tmp_path: Path):
    path = tmp_path / "detection.json"
    record = _record()
    record["signature"] = "0" * 16
    path.write_text(json.dumps(record), encoding="utf-8")
    data, why = finding.read(path)
    assert data is None and why == "detection.json: signature does not match metric and rule"


def test_read_valid_file(tmp_path: Path):
    path = tmp_path / "detection.json"
    record = _record()
    finding.write(path, record)
    data, why = finding.read(path)
    assert why == "" and data == record


def test_write_creates_parents(tmp_path: Path):
    path = tmp_path / "changes" / "0007-x" / "evidence" / finding.DETECTION_FILE
    finding.write(path, _record())
    assert path.is_file()
    assert path.read_text(encoding="utf-8").endswith("}\n")


def test_observations_keep_the_last_eight():
    points = [{"at": f"2026-09-{d:02d}", "value": float(d)} for d in range(1, 13)]
    record = _record(observations=points)
    assert record["observations"] == points[-8:]
    assert len(record["observations"]) == finding.RECENT_POINTS == 8


# --- dismissals -----------------------------------------------------------------------------


def test_dismissals_path_for():
    root = Path("/project")
    assert dismissals.path_for(root) == root / "changes" / ".dismissed.json"


def test_dismissals_load_missing(tmp_path: Path):
    assert dismissals.load(tmp_path / ".dismissed.json") == {"schema_version": 1, "entries": {}}


def test_dismissals_load_garbage(tmp_path: Path):
    path = tmp_path / ".dismissed.json"
    for text in ("{not json", "[1, 2]", '{"entries": [1]}', '"x"'):
        path.write_text(text, encoding="utf-8")
        assert dismissals.load(path) == dismissals.empty(), text


def test_dismissals_load_valid(tmp_path: Path):
    path = tmp_path / ".dismissed.json"
    entries = {"abc": {"kind": "detect", "reason": "noise", "until": None}}
    path.write_text(json.dumps({"schema_version": 1, "entries": entries}), encoding="utf-8")
    assert dismissals.load(path) == {"schema_version": 1, "entries": entries}


def test_add_requires_a_reason():
    for reason in ("", "   \n\t"):
        with pytest.raises(ValueError, match="reason"):
            dismissals.add(
                dismissals.empty(), "sig", kind="detect", reason=reason, by="o", change_id="0007"
            )


def test_add_requires_a_known_kind():
    with pytest.raises(ValueError, match="kind"):
        dismissals.add(dismissals.empty(), "sig", kind="other", reason="r", by="o", change_id=None)


def test_add_normalizes_and_records_the_entry():
    record = dismissals.add(
        dismissals.empty(),
        "sig",
        kind="scan",
        reason="  known   noise ",
        by=" owner ",
        change_id="0007",
        summary="s",
        at="2026-09-24T00:00:00Z",
    )
    assert record == {
        "schema_version": 1,
        "entries": {
            "sig": {
                "kind": "scan",
                "reason": "known noise",
                "by": "owner",
                "at": "2026-09-24T00:00:00Z",
                "until": None,
                "change_id": "0007",
                "summary": "s",
            }
        },
    }


def test_add_replaces_the_earlier_entry_and_does_not_mutate():
    first = dismissals.add(
        dismissals.empty(),
        "sig",
        kind="detect",
        reason="first",
        by="o",
        change_id="0001",
        until="2026-10-01",
    )
    second = dismissals.add(
        first, "sig", kind="detect", reason="second", by="o", change_id="0002", until="2026-11-01"
    )
    assert list(second["entries"]) == ["sig"]
    assert second["entries"]["sig"]["reason"] == "second"
    assert second["entries"]["sig"]["until"] == "2026-11-01"
    assert first["entries"]["sig"]["reason"] == "first"


def _one(until) -> dict:
    return {
        "schema_version": 1,
        "entries": {"sig": {"kind": "detect", "reason": "r", "until": until}},
    }


def test_lookup_expired_the_day_after():
    assert dismissals.lookup(_one("2026-09-24"), "sig", today=date(2026, 9, 25)) is None


def test_lookup_in_force_on_the_day_itself():
    record = _one("2026-09-24")
    assert dismissals.lookup(record, "sig", today=date(2026, 9, 24)) == record["entries"]["sig"]
    assert dismissals.lookup(record, "sig", today=date(2026, 9, 1)) is not None


def test_lookup_unreadable_until_keeps_the_entry():
    record = _one("next spring")
    assert dismissals.lookup(record, "sig", today=date(2030, 1, 1)) == record["entries"]["sig"]


def test_lookup_no_until_never_expires_and_absent_is_none():
    assert dismissals.lookup(_one(None), "sig", today=date(2099, 1, 1)) is not None
    assert dismissals.lookup(_one(None), "other", today=date(2026, 9, 24)) is None


def test_is_dismissed():
    record = _one("2026-09-24")
    assert dismissals.is_dismissed(record, "sig", today=date(2026, 9, 24)) is True
    assert dismissals.is_dismissed(record, "sig", today=date(2026, 9, 25)) is False
    assert dismissals.is_dismissed(record, "missing", today=date(2026, 9, 24)) is False


def test_until_date():
    assert dismissals.until_date(30, made_on=date(2026, 9, 24)) == "2026-10-24"
    today = datetime.now(timezone.utc).date()
    assert dismissals.until_date(30) == (today + timedelta(days=30)).isoformat()
    assert dismissals.until_date(None) is None


def test_save_writes_sorted_json_with_trailing_newline(tmp_path: Path):
    path = dismissals.path_for(tmp_path)
    record = dismissals.add(
        dismissals.empty(),
        "zz",
        kind="detect",
        reason="r",
        by="o",
        change_id="0001",
        at="2026-09-24T00:00:00Z",
    )
    record = dismissals.add(
        record, "aa", kind="scan", reason="r", by="o", change_id=None, at="2026-09-24T00:00:00Z"
    )
    dismissals.save(path, record)
    raw = path.read_bytes().decode("utf-8")
    assert raw == json.dumps(record, indent=2, sort_keys=True) + "\n"
    assert raw.index('"aa"') < raw.index('"zz"')
    assert raw.index('"entries"') < raw.index('"schema_version"')
    assert "\r\n" not in raw
    assert dismissals.load(path) == record


# --- routes.authorization -------------------------------------------------------------------


def test_template_routes_resolve_to_their_bands_value(template_bands: bands.Bands):
    config = {"maintain": {"runbooks": [{"name": "rollback-deploy", "command": "x"}]}}
    for name, auth in TEMPLATE_ROUTES.items():
        resolved = routes.authorization(name, template_bands.route(name), config, "python")
        assert resolved.authorization == auth, name
        assert resolved.source == "bands.yaml", name
        assert resolved.supported, name


def test_route_not_listed_is_unsupported_go():
    resolved = routes.authorization("runbook:unknown", None, {}, "python")
    assert resolved.authorization == "go"
    assert resolved.supported is False
    assert resolved.source == "not listed in bands.yaml"


def test_project_go_overrides_bands_preapproved(template_bands: bands.Bands):
    config = {"maintain": {"runbooks": [{"name": "revert-pr", "authorization": "go"}]}}
    route = "runbook:revert-pr"
    resolved = routes.authorization(route, template_bands.route(route), config, "python")
    assert resolved.authorization == "go"
    assert "sdlc.yaml" in resolved.source
    assert resolved.builtin and resolved.supported


def test_bands_go_not_weakened_by_project_preapproved(template_bands: bands.Bands):
    config = {
        "maintain": {
            "runbooks": [
                {"name": "rollback-deploy", "command": "x", "authorization": "preapproved"}
            ]
        }
    }
    route = "runbook:rollback-deploy"
    resolved = routes.authorization(route, template_bands.route(route), config, "python")
    assert resolved.authorization == "go"
    assert resolved.source == "bands.yaml"


@pytest.mark.parametrize("stamp", ["2026-09-24", date(2026, 9, 24)])
def test_decision_26_rehearsed_rollback_on_production_is_preapproved(
    template_bands: bands.Bands, stamp
):
    route = "runbook:rollback-deploy"
    config = _rollback_config(rehearsed_at=stamp)
    resolved = routes.authorization(route, template_bands.route(route), config, "python")
    assert resolved.authorization == "preapproved"
    assert resolved.rehearsed_at == "2026-09-24"
    assert "decision 26" in resolved.source
    assert resolved.supported
    assert resolved.project_runbook == config["maintain"]["runbooks"][0]


@pytest.mark.parametrize(
    "config",
    [
        _rollback_config(production=False),
        {"maintain": _rollback_config()["maintain"]},  # no deploy section at all
        _rollback_config(rehearsed_at=None),
        _rollback_config(rehearsed_at="last spring"),
        _rollback_config(rehearsed_at="2026-13-01"),
        _rollback_config(rehearsed_at=""),
    ],
    ids=["no-production", "no-deploy", "null", "unparseable", "bad-month", "empty"],
)
def test_decision_26_does_not_apply(template_bands: bands.Bands, config: dict):
    route = "runbook:rollback-deploy"
    resolved = routes.authorization(route, template_bands.route(route), config, "python")
    assert resolved.authorization == "go"
    assert resolved.rehearsed_at is None
    assert resolved.source == "bands.yaml"


def test_rollback_without_command_is_unsupported(template_bands: bands.Bands):
    route = "runbook:rollback-deploy"
    for config in ({}, _rollback_config(production=False, command="  ")):
        resolved = routes.authorization(route, template_bands.route(route), config, "python")
        assert resolved.supported is False
        assert "rollback-deploy" in resolved.note and "command" in resolved.note


def test_quarantine_on_node_is_unsupported_with_note(template_bands: bands.Bands):
    route = "runbook:quarantine-flaky-test"
    resolved = routes.authorization(route, template_bands.route(route), {}, "node")
    assert resolved.supported is False
    assert resolved.note == "the quarantine-flaky-test runbook supports python projects only"
    assert routes.authorization(route, template_bands.route(route), {}, "python").supported


def test_revert_pr_supported_on_any_language(template_bands: bands.Bands):
    route = "runbook:revert-pr"
    for language in ("python", "node", "go", "unknown", ""):
        resolved = routes.authorization(route, template_bands.route(route), {}, language)
        assert resolved.supported, language
        assert resolved.builtin and resolved.runbook == "revert-pr"


# --- routes.available -----------------------------------------------------------------------


def test_available_tier_1_and_0_is_empty(template_bands: bands.Bands):
    assert routes.available(template_bands, {}, "python", 1) == []
    assert routes.available(template_bands, {}, "python", 0) == []


def test_available_tier_2_is_pull_request_only(template_bands: bands.Bands):
    out = routes.available(template_bands, {}, "python", 2)
    assert [r.route for r in out] == ["pull_request"]
    assert out[0].authorization == "preapproved"


def test_available_tier_2_adds_pull_request_when_bands_list_none(tmp_path: Path):
    text = _rendered_template()
    no_pr = _load_bands(tmp_path, _without_pull_request(text))
    assert no_pr.route("pull_request") is None
    out = routes.available(no_pr, {}, "python", 2)
    assert [(r.route, r.authorization) for r in out] == [("pull_request", "preapproved")]


def test_available_tier_3_lists_every_route_resolved(template_bands: bands.Bands):
    config = {"maintain": {"runbooks": [{"name": "rollback-deploy", "command": "x"}]}}
    out = routes.available(template_bands, config, "node", 3)
    assert [r.route for r in out] == list(TEMPLATE_ROUTES)
    for resolved in out:
        expected = routes.authorization(
            resolved.route, template_bands.route(resolved.route), config, "node"
        )
        assert resolved == expected
    by_route = {r.route: r for r in out}
    assert by_route["runbook:quarantine-flaky-test"].supported is False


# --- routes.load_proposal -------------------------------------------------------------------


def _write_proposal(tmp_path: Path, data) -> Path:
    path = tmp_path / "proposal.json"
    path.write_text(data if isinstance(data, str) else json.dumps(data), encoding="utf-8")
    return path


def test_load_proposal_missing(tmp_path: Path):
    assert routes.load_proposal(tmp_path / "proposal.json") == (None, "proposal.json is missing")


def test_load_proposal_garbage(tmp_path: Path):
    proposal, why = routes.load_proposal(_write_proposal(tmp_path, "{nope"))
    assert proposal is None and why.startswith("proposal.json unreadable:")
    proposal, why = routes.load_proposal(_write_proposal(tmp_path, [1]))
    assert proposal is None and why == "proposal.json is not a JSON object"


def test_load_proposal_no_route(tmp_path: Path):
    for data in ({"tier": 3}, {"tier": 3, "route": "  "}, {"tier": 3, "route": 5}):
        proposal, why = routes.load_proposal(_write_proposal(tmp_path, data))
        assert proposal is None and why == "proposal.json: route is missing", data


def test_load_proposal_non_integer_tier(tmp_path: Path):
    for tier in ("3", 3.0, True, None):
        data = {"tier": tier, "route": "pull_request"}
        proposal, why = routes.load_proposal(_write_proposal(tmp_path, data))
        assert proposal is None and why == "proposal.json: tier is not an integer", tier


def test_load_proposal_valid_args_default_empty(tmp_path: Path):
    path = _write_proposal(tmp_path, {"tier": 3, "route": " runbook:revert-pr "})
    proposal, why = routes.load_proposal(path)
    assert why == ""
    assert proposal == Proposal(3, "runbook:revert-pr", {}, "")
    path = _write_proposal(
        tmp_path, {"tier": 3, "route": "pull_request", "args": [1], "rationale": "why"}
    )
    proposal, _ = routes.load_proposal(path)
    assert proposal.args == {} and proposal.rationale == "why"
    path = _write_proposal(
        tmp_path, {"tier": 3, "route": "runbook:revert-pr", "args": {"sha": SHA}}
    )
    assert routes.load_proposal(path)[0].args == {"sha": SHA}


# --- routes.validate_proposal ---------------------------------------------------------------


def test_validate_proposal_tier_mismatch(template_bands: bands.Bands):
    resolved, why = routes.validate_proposal(
        Proposal(3, "pull_request"), 2, template_bands, {}, "python"
    )
    assert resolved is None
    assert why == "the proposal says tier 3, the detection record says 2"


def test_validate_proposal_tier_1_proposes_nothing(template_bands: bands.Bands):
    resolved, why = routes.validate_proposal(
        Proposal(1, "pull_request"), 1, template_bands, {}, "python"
    )
    assert resolved is None and why == "tier 1 proposes nothing"


def test_validate_proposal_tier_2_runbook_refused(template_bands: bands.Bands):
    proposal = Proposal(2, "runbook:revert-pr", {"sha": SHA})
    resolved, why = routes.validate_proposal(proposal, 2, template_bands, {}, "python")
    assert resolved is None
    assert "tier 2" in why and "pull_request" in why and "runbook:revert-pr" in why


def test_validate_proposal_tier_2_pull_request_ok(template_bands: bands.Bands):
    resolved, why = routes.validate_proposal(
        Proposal(2, "pull_request"), 2, template_bands, {}, "python"
    )
    assert why == "" and resolved.route == "pull_request"
    assert resolved.authorization == "preapproved"


def test_validate_proposal_tier_3_pull_request_ok(template_bands: bands.Bands):
    resolved, why = routes.validate_proposal(
        Proposal(3, "pull_request"), 3, template_bands, {}, "python"
    )
    assert why == ""
    assert (resolved.route, resolved.authorization) == ("pull_request", "preapproved")


def test_validate_proposal_tier_3_pull_request_not_listed_refused(tmp_path: Path):
    no_pr = _load_bands(tmp_path, _without_pull_request(_rendered_template()))
    resolved, why = routes.validate_proposal(Proposal(3, "pull_request"), 3, no_pr, {}, "python")
    assert resolved is None and "pull_request" in why


def test_validate_proposal_unlisted_route_refused(template_bands: bands.Bands):
    config = {"maintain": {"runbooks": [{"name": "restart", "command": "x"}]}}
    resolved, why = routes.validate_proposal(
        Proposal(3, "runbook:restart"), 3, template_bands, config, "python"
    )
    assert resolved is None
    assert why == "runbook:restart is not a route of the 3sigma tier in bands.yaml"


def test_validate_proposal_revert_pr_needs_sha(template_bands: bands.Bands):
    for args in ({}, {"sha": ""}, {"sha": None}):
        resolved, why = routes.validate_proposal(
            Proposal(3, "runbook:revert-pr", args), 3, template_bands, {}, "python"
        )
        assert resolved is None and why == "runbook:revert-pr needs args sha", args
    resolved, why = routes.validate_proposal(
        Proposal(3, "runbook:revert-pr", {"sha": SHA}), 3, template_bands, {}, "node"
    )
    assert why == "" and resolved.authorization == "preapproved"


def test_validate_proposal_quarantine_on_python_ok(template_bands: bands.Bands):
    proposal = Proposal(3, "runbook:quarantine-flaky-test", {"test": NODE_ID})
    resolved, why = routes.validate_proposal(proposal, 3, template_bands, {}, "python")
    assert why == ""
    assert resolved.runbook == "quarantine-flaky-test" and resolved.builtin
    assert resolved.authorization == "preapproved"


def test_validate_proposal_quarantine_on_node_refused_with_note(template_bands: bands.Bands):
    proposal = Proposal(3, "runbook:quarantine-flaky-test", {"test": NODE_ID})
    resolved, why = routes.validate_proposal(proposal, 3, template_bands, {}, "node")
    assert resolved is None
    assert why == "the quarantine-flaky-test runbook supports python projects only"


def test_validate_proposal_quarantine_without_test_refused(template_bands: bands.Bands):
    proposal = Proposal(3, "runbook:quarantine-flaky-test")
    resolved, why = routes.validate_proposal(proposal, 3, template_bands, {}, "python")
    assert resolved is None and why == "runbook:quarantine-flaky-test needs args test"


def test_validate_proposal_project_runbook_with_command_ok(template_bands: bands.Bands):
    config = {"maintain": {"runbooks": [{"name": "rollback-deploy", "command": "x"}]}}
    resolved, why = routes.validate_proposal(
        Proposal(3, "runbook:rollback-deploy"), 3, template_bands, config, "node"
    )
    assert why == ""
    assert resolved.runbook == "rollback-deploy" and not resolved.builtin
    assert resolved.authorization == "go"
    assert resolved.project_runbook == config["maintain"]["runbooks"][0]


def test_validate_proposal_project_runbook_without_command_refused(template_bands: bands.Bands):
    resolved, why = routes.validate_proposal(
        Proposal(3, "runbook:rollback-deploy"), 3, template_bands, {}, "python"
    )
    assert resolved is None and "rollback-deploy" in why and "command" in why


@pytest.mark.parametrize(
    "route, args, config",
    [
        ("runbook:revert-pr", {"sha": SHA}, {}),
        (
            "runbook:revert-pr",
            {"sha": SHA},
            {"maintain": {"runbooks": [{"name": "revert-pr", "authorization": "go"}]}},
        ),
        ("runbook:rollback-deploy", {}, _rollback_config()),
        ("runbook:rollback-deploy", {}, _rollback_config(production=False)),
    ],
    ids=["builtin", "project-go", "decision-26", "rollback-go"],
)
def test_validate_proposal_resolution_is_authorizations(
    template_bands: bands.Bands, route: str, args: dict, config: dict
):
    resolved, why = routes.validate_proposal(
        Proposal(3, route, args), 3, template_bands, config, "python"
    )
    assert why == ""
    assert resolved == routes.authorization(route, template_bands.route(route), config, "python")


# --- shapes ---------------------------------------------------------------------------------


def test_proposal_runbook_and_runbook_name():
    assert Proposal(3, "runbook:revert-pr").runbook == "revert-pr"
    assert Proposal(3, "pull_request").runbook is None
    assert routes.runbook_name("runbook:rollback-deploy") == "rollback-deploy"
    assert routes.runbook_name("pull_request") is None
    assert routes.runbook_name("rollback-deploy") is None


def test_resolved_as_dict_shape():
    resolved = Resolved(
        "runbook:rollback-deploy",
        "preapproved",
        "decision 26: ...",
        runbook="rollback-deploy",
        project_runbook={"name": "rollback-deploy"},
        rehearsed_at="2026-09-24",
    )
    assert resolved.as_dict() == {
        "route": "runbook:rollback-deploy",
        "authorization": "preapproved",
        "source": "decision 26: ...",
        "runbook": "rollback-deploy",
        "builtin": False,
        "supported": True,
        "note": "",
        "rehearsed_at": "2026-09-24",
    }
    json.dumps(resolved.as_dict())  # serializable: the record carries it


def test_proposal_as_dict_shape():
    args = {"sha": SHA}
    proposal = Proposal(3, "runbook:revert-pr", args, "the regression came in with this commit")
    out = proposal.as_dict()
    assert out == {
        "schema_version": 1,
        "tier": 3,
        "route": "runbook:revert-pr",
        "args": {"sha": SHA},
        "rationale": "the regression came in with this commit",
    }
    assert out["args"] is not args
    assert Proposal(2, "pull_request").as_dict()["args"] == {}


# --- the session-5 review: a forced finding never pre-approves a runbook ----------------------
def test_apply_forced_turns_every_runbook_route_into_go_and_leaves_pull_request():
    from detect import routes

    resolved = routes.Resolved(
        "runbook:revert-pr", "preapproved", "bands.yaml", runbook="revert-pr", builtin=True
    )
    assert routes.apply_forced(resolved, False).authorization == "preapproved"
    forced = routes.apply_forced(resolved, True)
    assert forced.authorization == "go" and forced.source == routes.FORCED_SOURCE
    rehearsed = routes.Resolved(
        "runbook:rollback-deploy",
        "preapproved",
        "decision 26: ...",
        runbook="rollback-deploy",
        rehearsed_at="2026-09-24",
    )
    forced = routes.apply_forced(rehearsed, True)
    assert forced.authorization == "go" and forced.rehearsed_at is None
    intent = routes.Resolved("pull_request", "preapproved", "the incident intent PR")
    assert routes.apply_forced(intent, True).authorization == "preapproved"
    assert routes.apply_forced(None, True) is None
