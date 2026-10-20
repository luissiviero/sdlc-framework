"""Decision 35 (ROADMAP R24, plugin 1.0.15): a risk-list hit is a line in the close-look
banner. The items with globs, the check that reports and never parks, the escalation on a
risk item that still parks and stays off the panel, the brief per hit item, the banner on
the PR the owner merges, the acceptance record the (b) and (e) merges write, the fast lane
that waits on a hit at (b), and what /sdlc-init proposes."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from ci import run_phase
from panel import cli as panel_cli
from pr import description as desc
from release import cli as release_cli

from gate import checks, gate, risk
from gate.checks import CheckResult
from init import detect, sdlc_init
from state import conventions as c
from state import status as status_mod
from state import yamlish
from tests.test_gate import PLAN, design_project, git, project, verdict, write  # noqa: F401
from tests.test_release import FakeGitHub, _git, _record, _repo_with_change, _run, _with_remote

OWNER = "luissiviero"
BRIEF = """# Security & policy brief, gate ({phase})

## auth
- Word: {word}
- What the change does to it: adds a token TTL in sample_pkg/auth.py
- What could break: sessions expire after a minute
- How to undo it: revert the commit
"""


# --- the items and the match ----------------------------------------------------------------
def test_an_item_is_a_string_or_words_with_globs():
    items, why = risk.parse_items(
        ["auth", {"item": "data migrations", "paths": ["**/migrations/**", " "]}, {"item": "x"}]
    )
    assert why == ""
    assert items == [
        risk.RiskItem("auth"),
        risk.RiskItem("data migrations", ("**/migrations/**",)),
        risk.RiskItem("x"),  # a mapping without paths reads as the plain item
    ]
    assert risk.parse_items(None) == ([], "")
    assert risk.parse_items("auth")[1] == "sdlc.yaml: risk_list must be a list"
    assert "unknown key(s): path" in risk.parse_items([{"item": "x", "path": ["a"]}])[1]
    assert risk.parse_items([{"paths": ["a"]}])[1].startswith("sdlc.yaml: a risk_list mapping")


def test_globs_match_paths_outside_changes_and_words_match_only_the_concerns():
    items = [
        {"item": "data migrations", "paths": ["**/migrations/**", "alembic/versions/**"]},
        {"item": "production config", "paths": ["config/production.*", "**/*.tf"]},
        "auth",
    ]
    paths = [
        "db/migrations/0002.sql",
        "alembic/versions/abc.py",
        "infra/main.tf",
        "config/production.yaml",
        "changes/0007-data-migrations/migrations/x.md",  # the change's own folder never hits
        "src/authentication.py",
        "changes/0007-auth-login/intent.md",  # nor a plain item's words (1.0.15)
    ]
    texts = {"spec.md Flagged concerns": "- data migrations: the column is renamed"}
    assert risk.hits(items, paths, texts) == {
        "data migrations": [
            "db/migrations/0002.sql",
            "alembic/versions/abc.py",
            "spec.md Flagged concerns: text",
        ],
        "production config": ["infra/main.tf", "config/production.yaml"],
    }
    # the same paths miss with the plain words (the proposal's "What the framework does today")
    plain = ["data migrations", "production config"]
    assert risk.hits(plain, paths[:4], {}) == {}
    # checks.risk_hits keeps its signature for plain strings
    assert checks.risk_hits(["auth"], ["src/auth/login.py"], {}) == {"auth": ["src/auth/login.py"]}


def test_a_glob_item_does_not_match_its_words_on_paths():
    items = [{"item": "auth", "paths": ["src/security/**"]}]
    assert risk.hits(items, ["src/auth/login.py"], {}) == {}
    assert risk.hits(items, ["src/security/keys.py"], {}) == {"auth": ["src/security/keys.py"]}


# --- the brief and the escalation -----------------------------------------------------------
def test_the_brief_is_read_per_item_with_the_reviewer_s_word():
    brief = risk.parse_brief(BRIEF.format(phase="c", word="escalate") + "\n## `money movement`\n")
    assert brief["auth"]["word"] == "escalate"
    assert brief["auth"]["What could break"] == "sessions expire after a minute"
    assert brief["money movement"] == {"item": "money movement", "word": "continue"}
    assert risk.parse_brief(None) == {}
    assert risk.escalated_items(["auth", "money movement"], brief, None) == ["auth"]
    escalate = {"verdict": "escalate", "reasons": ["risk item 'money movement': refunds double"]}
    assert risk.escalated_items(["money movement"], {}, escalate) == ["money movement"]
    assert risk.escalated_items(["money movement"], {}, {**escalate, "verdict": "continue"}) == []


def _auth_change(root: Path, change: Path) -> None:
    write(root / "sample_pkg" / "auth.py", "TOKEN_TTL = 60\n")
    write(
        change / "plan.md",
        PLAN.replace("## Order of work", "- `sample_pkg/auth.py` — ttl\n\n## Order of work"),
    )
    git(root, "add", ".")
    git(root, "commit", "-q", "-m", "auth ttl")


def test_a_hit_parks_nothing_and_its_park_record_keeps_no_reason(project):  # noqa: F811
    """The release guard on a merge over a parked gate (e) is unchanged in the code: a hit
    no longer sets ``parked_reason``, so it never makes the release wait for the label."""
    root, change = project
    _auth_change(root, change)
    verdict(root, "c")
    result = gate.run_gate(root, "0001", "c")
    assert result.result == "continue", result.reason
    assert status_mod.read_status(change).parked_reason is None
    record = json.loads((change / "evidence" / "gate-c.json").read_text(encoding="utf-8"))
    assert risk.recorded_hits(record) == {"auth": ["sample_pkg/auth.py"]}


def test_the_reviewer_s_escalation_on_a_risk_item_parks(project):  # noqa: F811
    root, change = project
    _auth_change(root, change)
    write(risk.brief_path(change, "c"), BRIEF.format(phase="c", word="escalate"))
    git(root, "add", ".")
    git(root, "commit", "-q", "-m", "the reviewer's brief")
    verdict(root, "c")
    result = gate.run_gate(root, "0001", "c", dry_run=True)
    assert result.result == "park"
    r = next(ch for ch in result.failed if ch.name == "risk_list")
    assert r.details["escalated"] == ["auth"] and "'auth'" in r.reason
    assert "never goes to the review panel" in r.need
    assert "evidence/roles/security-policy-c.md" in r.need
    # the reviewer's word continue: a banner line, no park
    write(risk.brief_path(change, "c"), BRIEF.format(phase="c", word="continue"))
    git(root, "commit", "-q", "-am", "the reviewer's brief, continue")
    verdict(root, "c")
    assert gate.run_gate(root, "0001", "c", dry_run=True).result == "continue"


def test_an_escalate_verdict_naming_a_hit_item_stays_off_the_panel(project):  # noqa: F811
    root, change = project
    _auth_change(root, change)
    head = git(root, "rev-parse", "HEAD").strip()
    path = change / "evidence" / "adversarial-review-c.json"
    verdict(root, "c", verdict="escalate")
    data = json.loads(path.read_text(encoding="utf-8"))
    data["reasons"] = ["risk item 'auth': the token never expires on refresh"]
    data["head"] = head
    write(path, json.dumps(data))
    result = gate.run_gate(root, "0001", "c", dry_run=True)
    assert {"risk_list", "adversarial_review"} <= set(ch.name for ch in result.failed)
    items, parks = panel_cli.collect_items(root, change, "c", result)
    assert not any(i["kind"] == "escalate" for i in items)
    assert any(
        p["check"] == "adversarial_review" and "never the panel's" in p["reason"] for p in parks
    )
    assert any(p["check"] == "risk_list" for p in parks)


def test_an_escalate_verdict_on_something_else_still_goes_to_the_panel(project):  # noqa: F811
    root, change = project
    _auth_change(root, change)
    verdict(root, "c", verdict="escalate")  # "blast radius larger than the plan says"
    result = gate.run_gate(root, "0001", "c", dry_run=True)
    assert "risk_list" not in {ch.name for ch in result.failed}
    items, _parks = panel_cli.collect_items(root, change, "c", result)
    assert [i["kind"] for i in items] == ["escalate"]


def test_risk_hits_now_lists_the_items_for_the_reviewer(project):  # noqa: F811
    root, change = project
    _auth_change(root, change)
    found = gate.risk_hits_now(root, "0001", "c")
    assert found["hits"] == {"auth": ["sample_pkg/auth.py"]}
    assert found["brief"] == "changes/0001-percent-helper/evidence/roles/security-policy-c.md"
    # the review pass asks for (e) while status.yaml still says (c) or (d)
    assert gate.risk_hits_now(root, "0001", "e")["phase"] == "e"
    with pytest.raises(gate.GateError):
        gate.build_context(root, "0001", "e")  # a gate itself still refuses the mismatch


# --- the fast lane --------------------------------------------------------------------------
def _results(hits: dict, accepted=()) -> list[CheckResult]:
    return [
        CheckResult("risk_list", True, "x", details={"hits": hits, "accepted": list(accepted)}),
        CheckResult("adversarial_review", True, "x", details={"classification": "routine"}),
    ]


def test_a_design_with_an_unaccepted_hit_never_takes_the_fast_lane():
    assert gate.fast_lane_applies("b", "standard", True, _results({}), True)
    assert not gate.fast_lane_applies("b", "standard", True, _results({"auth": ["x"]}), True)
    accepted = _results({"auth": ["x"]}, accepted=["auth"])
    assert gate.fast_lane_applies("b", "standard", True, accepted, True)
    assert gate.unaccepted_risk_hits(_results({"auth": ["x"], "b": ["y"]}, ["b"])) == ["auth"]


# --- the acceptance record ------------------------------------------------------------------
def _line(phase="b", items=("auth",), shown=True, pr=12, by=OWNER):
    return risk.acceptance_line(
        phase, list(items), by, "2026-10-20T10:00:00Z", pr, "abc1234", shown
    )


def test_the_acceptance_line_round_trips_and_is_absent_until_written(tmp_path):
    change_dir, st = status_mod.new_change(tmp_path, "Risky")
    assert "risk_acceptances" not in status_mod.read_status(change_dir).to_dict()
    assert risk.record_acceptance(st, _line())
    assert not risk.record_acceptance(st, _line(items=("other",)))  # one merge, one act
    status_mod.write_status(change_dir, st)
    back = status_mod.read_status(change_dir)
    assert back.risk_acceptances == [_line()]
    assert risk.accepted(back) == {"auth": "accepted at gate (b) by @luissiviero on 2026-10-20"}
    st.risk_acceptances = [_line(shown=False)]
    assert risk.accepted(st) == {}  # an acceptance the owner could not read is none
    st.risk_acceptances = [{**_line(), "via": "label"}]
    with pytest.raises(ValueError):
        st.validate()


def _gate_file(change: Path, phase: str, hits: dict, declared=()) -> None:
    checks_ = [{"name": "risk_list", "ok": True, "details": {"hits": hits}}]
    if declared:
        checks_.append({"name": "ratchets", "ok": True, "details": {"declared": list(declared)}})
    write(change / "evidence" / f"gate-{phase}.json", json.dumps({"checks": checks_}))


def test_the_banner_lists_each_item_with_its_brief_and_what_merging_does(tmp_path):
    change, st = status_mod.new_change(tmp_path, "Risky")
    _gate_file(change, "b", {"auth": ["spec.md Flagged concerns: text"]})
    write(risk.brief_path(change, "b"), BRIEF.format(phase="b", word="continue"))
    lines = risk.banner_lines(change, "b", st)
    assert lines[0].startswith(risk.BANNER_HEADING) and "Merging this PR accepts them" in lines[0]
    assert lines[1].startswith("- `auth` — first found at gate (b): spec.md Flagged concerns")
    assert "what could break: sessions expire after a minute" in lines[1]
    assert "evidence/roles/security-policy-b.md" in lines[1]
    assert risk.banner_shown("intro\n" + "\n".join(lines), ["auth"])
    assert not risk.banner_shown("no banner", ["auth"]) and risk.banner_shown("", [])
    # the build PR: accepted at (b), touched again at (c); a new item at (d) with no brief
    st.risk_acceptances = [_line()]
    _gate_file(change, "c", {"auth": ["sample_pkg/auth.py"]})
    _gate_file(change, "d", {"money movement": ["pay.py"]}, declared=["tests/a.py (plan)"])
    lines = risk.banner_lines(change, "d", st)
    assert "Only your merge at gate (e) accepts them" in lines[0]
    assert lines[1].startswith("- `auth` — accepted at gate (b) by @luissiviero on 2026-10-20")
    assert lines[2].startswith("- `money movement` — first found at gate (d): pay.py.")
    assert lines[2].endswith("the reviewer wrote no brief on it")
    assert lines[3] == "- dropped, declared by the approved plan: tests/a.py (plan)"
    assert risk.new_items(risk.banner_entries(change, "e", st)) == ["money movement"]
    assert risk.banner_lines(change, "f", st) == []  # (f) asks nothing
    assert risk.banner_lines(change, "a", st) == []  # (a) asks only on the install PR


def test_the_build_pr_body_opens_with_the_banner(project):  # noqa: F811
    root, change = project
    _auth_change(root, change)
    verdict(root, "c")
    gate.run_gate(root, "0001", "c")
    body = desc.build_description(root, "0001", "c")
    assert body.startswith(risk.BANNER_HEADING)
    assert "- `auth` — first found at gate (c): sample_pkg/auth.py." in body
    assert risk.banner_shown(body, ["auth"])


# --- the (b) merge's acceptance, recorded by the build run ----------------------------------
def _merge_event(tmp_path: Path, head: str, merged_by: str, body: str) -> dict[str, str]:
    payload = {
        "action": "closed",
        "pull_request": {
            "number": 12,
            "merged": True,
            "merged_by": {"login": merged_by},
            "merged_at": "2026-10-20T10:00:00Z",
            "merge_commit_sha": "abc1234",
            "head": {"ref": head},
            "body": body,
        },
    }
    path = tmp_path / "event.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return {
        "GITHUB_EVENT_NAME": "pull_request",
        "GITHUB_EVENT_PATH": str(path),
        "GITHUB_REPOSITORY_OWNER": OWNER,
    }


def test_the_build_run_records_the_design_merge_s_acceptance(tmp_path):
    root = tmp_path / "proj"
    change, st = status_mod.new_change(root, "Risky")
    _gate_file(change, "b", {"auth": ["spec.md Flagged concerns: text"]})
    body = "\n".join(risk.banner_lines(change, "b", st))
    env = _merge_event(tmp_path, f"sdlc/{st.id}/b", OWNER, body)
    out = run_phase.record_design_acceptance(root, change, {}, env)
    line = out["line"]
    assert (line["by"], line["pr"], line["at"]) == (OWNER, 12, "2026-10-20T10:00:00Z")
    assert line["details"] == {"phase": "b", "items": ["auth"], "banner_shown": True}
    assert status_mod.read_status(change).risk_acceptances == [line]
    # again (a re-run of the build): the item is accepted, nothing more is written
    assert run_phase.record_design_acceptance(root, change, {}, env) == {"ok": True, "items": []}
    assert status_mod.read_status(change).risk_acceptances == [line]
    # not the design PR, not a merge, not a pull request event: nothing recorded
    assert run_phase.record_design_acceptance(root, change, {}, {}) is None
    other = _merge_event(tmp_path, "feature/x", OWNER, body)
    assert run_phase.record_design_acceptance(root, change, {}, other) is None


def test_only_the_owner_s_merge_accepts_and_an_unseen_banner_is_recorded_as_such(tmp_path):
    root = tmp_path / "proj"
    change, st = status_mod.new_change(root, "Risky")
    _gate_file(change, "b", {"auth": ["x"]})
    env = _merge_event(tmp_path, f"sdlc/{st.id}/b", "sdlc-merge[bot]", "")
    out = run_phase.record_design_acceptance(root, change, {}, env)
    assert out["ok"] is False and "only the owner accepts a risk" in out["reason"]
    # a collaborator who may merge is a person, not the owner (decision 34's one rule)
    env = _merge_event(tmp_path, f"sdlc/{st.id}/b", "collaborator", "")
    assert run_phase.record_design_acceptance(root, change, {}, env)["ok"] is False
    assert status_mod.read_status(change).risk_acceptances == []
    env = _merge_event(tmp_path, f"sdlc/{st.id}/b", OWNER, "a body without the banner")
    line = run_phase.record_design_acceptance(root, change, {}, env)["line"]
    assert line["details"]["banner_shown"] is False
    assert risk.accepted(status_mod.read_status(change)) == {}  # the (e) banner asks again


def test_the_runner_guards_the_acceptance_record_like_an_owner_field(tmp_path, monkeypatch):
    _change, st = status_mod.new_change(tmp_path, "Risky")
    before = run_phase.owner_fields(st)
    st.risk_acceptances = [_line()]
    after = run_phase.owner_fields(st)
    reasons = run_phase.owner_field_mismatches(before, after, None)
    assert any(r.startswith("risk_acceptances: the session recorded") for r in reasons)
    assert run_phase.owner_field_mismatches(after, after, None) == []

    banner = f"{risk.BANNER_HEADING}: …\n- `auth` — first found at gate (b): x."

    class GitHub:
        def __init__(self, merged_by, head="sdlc/0001/b", body=banner):
            self.merged_by, self.head, self.body = merged_by, head, body

        def pr_by_number(self, repo, number):
            return {"ok": True, "merged": True, "merged_by": self.merged_by,
                    "head_ref": self.head, "body": self.body}  # fmt: skip

    env = {"GITHUB_ACTIONS": "true"}
    cases = (
        (GitHub(OWNER), []),
        (GitHub("mallory"), ["was not merged by 'luissiviero'"]),
        (GitHub(OWNER, head="sdlc/0001/c"), ["is not the PR whose merge is gate (b)"]),
        (GitHub(OWNER, body="no banner"), ["shows no banner line for auth"]),
    )
    for fake, expected in cases:
        monkeypatch.setattr(run_phase, "_github", lambda fake=fake: fake)
        found = run_phase.acceptance_mismatches(after, {}, "owner/name", env)
        assert [e for e in expected if not any(e in r for r in found)] == [], found
        assert bool(found) is bool(expected)
    # the default branch's copy carries it: nothing to confirm
    assert run_phase.acceptance_mismatches(after, after, "owner/name", env) == []


# --- the (e) merge's acceptance, recorded by the release workflow's record job ---------------
class MergedBy(FakeGitHub):
    def __init__(self, merged_by=OWNER, body="", **kwargs):
        super().__init__(**kwargs)
        self.merged_by, self.body = merged_by, body

    def pr_by_number(self, repo, number, cwd=None):
        out = super().pr_by_number(repo, number, cwd)
        return {**out, "merged_by": self.merged_by, "merged_at": "2026-10-21T08:00:00Z",
                "body": self.body}  # fmt: skip


def _e_hit(change_dir: Path) -> None:
    path = change_dir / "evidence" / "gate-e.json"
    record = json.loads(path.read_text(encoding="utf-8"))
    record["checks"].append(
        {"name": "risk_list", "ok": True, "details": {"hits": {"auth": ["report.py"]}}}
    )
    path.write_text(json.dumps(record), encoding="utf-8")


def test_the_e_merge_s_acceptance_is_stored_by_the_record_job(tmp_path):
    root, change_dir = _repo_with_change(tmp_path)
    _e_hit(change_dir)
    _git(root, "commit", "-q", "-am", "gate (e) reported a hit")
    _git(root, "checkout", "-q", "main")
    _git(root, "merge", "-q", "--no-ff", "-m", "merge #7", "sdlc/0001/c")
    _git(root, "checkout", "-q", "sdlc/0001/c")
    _with_remote(root)
    _git(root, "merge", "-q", "sdlc/0001/c")  # the merge commit carries the gate (e) record
    outputs = tmp_path.parent / f"{tmp_path.name}-outputs"
    outputs.write_text("", encoding="utf-8")
    body = f"{risk.BANNER_HEADING}: …\n- `auth` — first found at gate (e): report.py."
    env = {"GITHUB_OUTPUT": str(outputs), "GITHUB_REPOSITORY_OWNER": OWNER}
    code, lines = _run(root, MergedBy(body=body), env=env)
    assert code == 0, lines
    assert "release: risk: accepted by luissiviero's merge: auth (banner shown)" in lines
    written = dict(line.split("=", 1) for line in outputs.read_text(encoding="utf-8").splitlines())
    acceptance = json.loads(written["risk_acceptance"])
    assert acceptance["details"] == {"phase": "e", "items": ["auth"], "banner_shown": True}
    assert acceptance["by"] == OWNER and written["change_id"] == "0001"
    assert "released" not in written  # deploy.action none: no release ran
    code, lines = _record(root, "--released", "", "--acceptance", written["risk_acceptance"])
    assert code == 0 and lines[0].startswith("release: record: stored on"), lines
    _git(root, "fetch", "-q", "origin", "+refs/sdlc/*:refs/sdlc/*")
    for ref in ("refs/remotes/origin/sdlc/0001/c", "refs/sdlc/released/0001"):
        text = _git(root, "show", f"{ref}:changes/0001-export-the-claims-report/status.yaml")
        stored = yamlish.loads(text)
        assert stored["risk_acceptances"] == [acceptance] and not stored.get("released_at"), ref
    # the ref carries the acceptance and no release: the release still reads it as none
    st, where = release_cli.remote_record(
        root, "0001", "changes/0001-export-the-claims-report/status.yaml", _approval_git()
    )
    assert st is None and where == "no release record on sdlc/0001/c"  # the branch is read too
    # the job re-run changes nothing
    code, lines = _record(root, "--released", "", "--acceptance", written["risk_acceptance"])
    assert code == 0 and "already records it" in lines[0]


def _approval_git():
    from release import approval

    return approval.make_git()


def test_only_the_owner_s_e_merge_accepts(tmp_path):
    root, change_dir = _repo_with_change(tmp_path)
    _e_hit(change_dir)
    st = status_mod.read_status(change_dir)
    env = {"GITHUB_REPOSITORY_OWNER": OWNER}
    collaborator = release_cli.merge_acceptance(
        change_dir, st, {"merged_by": "collaborator"}, 7, "abc", {}, env
    )
    assert collaborator[0] is None and "not the owner's account" in collaborator[1]
    assert (
        release_cli.merge_acceptance(
            change_dir, st, {"merged_by": "sdlc-merge[bot]"}, 7, "abc", {}
        )[0]
        is None
    )
    line, _why = release_cli.merge_acceptance(
        change_dir, st, {"merged_by": OWNER, "body": ""}, 7, "abc", {}, env
    )
    assert line["details"] == {"phase": "e", "items": ["auth"], "banner_shown": False}
    st.risk_acceptances = [_line(phase="e", pr=7)]
    again = release_cli.merge_acceptance(change_dir, st, {"merged_by": OWNER}, 7, "abc", {}, env)
    assert again is None


# --- the label retired; /sdlc-init proposes globs -------------------------------------------
def test_sdlc_accept_risk_is_no_longer_an_owner_label():
    assert c.ACCEPT_RISK_LABEL not in c.UNPARK_LABELS
    assert c.ACCEPT_RISK_LABEL not in c.all_labels()


def test_init_proposes_globs_only_for_folders_that_exist(tmp_path):
    for rel in ("db/migrations/0001.sql", "src/auth/login.py", "changes/0007-pay/payments/x.md"):
        write(tmp_path / rel, "x\n")
    proposed = detect.risk_list(tmp_path)
    assert proposed == [
        {"item": "auth", "paths": ["**/auth/**"]},
        {"item": "data migrations", "paths": ["**/migrations/**"]},
        "money movement",  # changes/ is never read for a proposal
        "production config",
    ]
    text = "risk_list:\n" + sdlc_init._risk_list_yaml(proposed) + "\n"
    assert yamlish.loads(text)["risk_list"] == proposed
    assert risk.parse_items(proposed)[1] == ""


def test_the_review_pass_is_asked_for_the_e_brief_and_the_cli_lists_the_hits(
    project,  # noqa: F811
    capsys,
):
    from review import cli as review_cli

    from gate import cli as gate_cli

    root, change = project
    assert review_cli.risk_section(root, "0001", None) == ""
    _auth_change(root, change)
    text = review_cli.risk_section(root, "0001", None)
    assert "evidence/roles/security-policy-e.md" in text
    assert "- `auth`: sample_pkg/auth.py" in text and "- Word: continue" in text
    assert gate_cli.main(["risk-hits", "--root", str(root), "--id", "0001", "--phase", "c"]) == 0
    assert json.loads(capsys.readouterr().out)["hits"] == {"auth": ["sample_pkg/auth.py"]}
