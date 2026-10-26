"""Static checks on the markdown process content: frontmatter, referenced scripts exist,
the intent skill carries the article's sections in order, the plan skill the four p.16–17
sections plus 'Options not taken'. Whether the model *triggers* the skill is a live check
(see docs/PROGRESS.md), not a layer-1 test."""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from gate.artifacts import SPEC_SECTIONS

PLUGIN = Path(__file__).resolve().parents[1] / "plugin"
COMMANDS = PLUGIN / "commands"
REVIEW_PROMPT = PLUGIN / "review" / "REVIEW_PROMPT.md"
# Every command file, so a command added later is covered without editing this list.
COMMAND_FILES = sorted(path.name for path in COMMANDS.glob("*.md"))
# R45 (decision 39, row 8; choice 273): a renamed command stays one release as a short command
# that only points to its new name; it runs no phase, so the phase checks below skip it and
# ``test_a_renamed_command_stays_one_release_and_points_to_its_new_name`` covers it.
RENAMED = {"sdlc-plan.md": "/sdlc-intent"}
PHASE_COMMAND_FILES = [name for name in COMMAND_FILES if name not in RENAMED]
# /sdlc-intent and /sdlc-init are the two attended commands: they talk to the owner. Every
# other command runs unattended and parks instead of asking (OPERATING_MODEL: a park, never a
# page; the reviewer's verdict says park too, R45 row 62).
ATTENDED = ("sdlc-intent.md", "sdlc-init.md")
UNATTENDED = tuple(name for name in PHASE_COMMAND_FILES if name not in ATTENDED)
POLICY_SKILLS = (
    "coding-standards",
    "security-baseline",
    "ux-and-brand",
    "data-conventions",
    "definition-of-done",
)
# The runbook phases: each registers the run before it calls the gate (build guide step 19).
RUNBOOKS = ("sdlc-design.md", "sdlc-build.md", "sdlc-test.md", "sdlc-deploy.md")
GATE_CHECK = 'python "${CLAUDE_PLUGIN_ROOT}/plugin/gate/cli.py" check'
GATE_START_RUN = 'python "${CLAUDE_PLUGIN_ROOT}/plugin/gate/cli.py" start-run'


def flat(path: Path) -> str:
    """The body with its line wrapping removed, so a sentence split over two lines matches."""
    return " ".join(path.read_text(encoding="utf-8").split())


def frontmatter(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    assert m, f"{path} has no frontmatter"
    fm = {}
    for line in m.group(1).splitlines():
        key, _, value = line.partition(":")
        fm[key.strip()] = value.strip()
    return fm


@pytest.mark.parametrize("name", ["sdlc-intent", "sdlc-init"])
def test_command_frontmatter_and_script_references(name):
    path = PLUGIN / "commands" / f"{name}.md"
    fm = frontmatter(path)
    assert fm["description"] and fm["disable-model-invocation"] == "true"
    body = path.read_text(encoding="utf-8")
    refs = re.findall(
        r"\$\{CLAUDE_PLUGIN_ROOT\}/([\w/.-]+\.py)", body + fm.get("allowed-tools", "")
    )
    assert refs
    for ref in refs:  # the plugin root is the repository root
        assert (PLUGIN.parent / ref).is_file(), ref
    # allow rules and the body spell the script call identically (quoted), so no prompt
    for rule in re.findall(r"Bash\((python [^)]*\.py\") \*\)", fm["allowed-tools"]):
        assert rule in body, rule
    assert "bypass" in body.lower() or "Never edit" in body  # guardrail reminder present


def test_sdlc_intent_flow_matches_step_11():
    body = (PLUGIN / "commands" / "sdlc-intent.md").read_text(encoding="utf-8")
    for step in [
        "Brainstorm",
        "new-change",
        "intent-template",
        "owner corrects",
        "commit-phase",
        "sdlc:intent-ready",
        "--phase intent",
        "sdlc/<id>/intent",
        "compare/",
    ]:
        assert step in body, step
    assert "$ARGUMENTS" in body
    assert "Do not start the design phase" in " ".join(body.split())


@pytest.mark.parametrize("name", sorted(RENAMED))
def test_a_renamed_command_stays_one_release_and_points_to_its_new_name(name):
    """R45 (decision 39, row 8; choice 273): `/sdlc-plan` stays one release as a command that
    points to `/sdlc-intent`, and does nothing else: no script, no write, no PR."""
    path = COMMANDS / name
    new = RENAMED[name]
    assert (COMMANDS / f"{new.lstrip('/')}.md").is_file(), new
    fm = frontmatter(path)
    assert fm["disable-model-invocation"] == "true"
    assert new in fm["description"] and "one release" in fm["description"]
    assert fm["allowed-tools"] == "Read"
    text = flat(path)
    assert f"run `{new} $ARGUMENTS` instead" in text
    assert "decision 39, row 8" in text
    assert "${CLAUDE_PLUGIN_ROOT}" not in text and "upsert" not in text
    assert "Never use bypass-permissions mode" in text and "Never notify" in text


def test_sdlc_init_flow_matches_step_21():
    body = (PLUGIN / "commands" / "sdlc-init.md").read_text(encoding="utf-8")
    for token in [
        "--detect-only",
        "decision 37",
        "deploy action",
        "maintain metric",
        "/init",
        "sdlc_init.py",
        "--id 0000",
        "--phase intent",
        "sdlc:intent-ready",
        "Re-running is safe",
        "evals",
        "bands.yaml",
        "Node",
    ]:
        assert token in body, token


def test_intent_skill_sections_in_article_order():
    path = PLUGIN / "skills" / "intent-template" / "SKILL.md"
    fm = frontmatter(path)
    assert fm["name"] == "intent-template"
    assert "intent" in fm["description"].lower() and "incident" in fm["description"].lower()
    body = path.read_text(encoding="utf-8")
    order = [
        "## Problem",
        "## Proposed outcome",
        "## Affected users and systems",
        "## Constraints",
        "## Open questions",
        "## Evidence",
    ]
    positions = [body.index(h) for h in order]
    assert positions == sorted(positions)
    assert "Author:" in body and "Change id:" in body and "Entry route:" in body
    # R45 row 77: the header carries no status line; an old intent keeps its line as history
    header = next(line for line in body.splitlines() if line.startswith("Author:"))
    assert "Status:" not in header and "keeps its `Status:` line as history" in body
    assert "idea | ticket" in body and "incident" in body


def test_plan_skill_sections_and_interrogation():
    path = PLUGIN / "skills" / "plan-template" / "SKILL.md"
    fm = frontmatter(path)
    assert fm["name"] == "plan-template"
    body = path.read_text(encoding="utf-8")
    order = [
        "## Files that change",
        "## Order of work",
        "## Risks",
        "## Options not taken",
        "## Proof",
    ]
    positions = [body.index(h) for h in order]
    assert positions == sorted(positions)
    for q in [
        "could this change break",
        "most risky",
        "options did you consider",
        "never seen this conversation",
    ]:
        assert q in body, q
    assert "read-only" in body.lower() and "Read/Grep/Glob" in body


def test_plan_template_ratchet_proof_item_present():
    body = (PLUGIN / "skills" / "plan-template" / "SKILL.md").read_text(encoding="utf-8")
    assert "- ratchet: <name> may fall, because <why>" in body
    text = " ".join(body.split())
    assert "`tests` or `evals`" in text


def test_no_portuguese_in_process_content():
    """CLAUDE.md: English only in every file. PLUGIN.rglob covers plugin/review/*.md too
    (REVIEW_PROMPT.md is a prompt file, not a skill); the assertion below keeps it covered."""
    scanned = []
    for path in list(PLUGIN.rglob("*.md")) + list((PLUGIN.parent / "template").rglob("*")):
        if path.is_file():
            scanned.append(path)
            text = path.read_text(encoding="utf-8", errors="replace").lower()
            assert not re.search(r"\b(não|você|também|então|obrigado)\b", text), path
    assert REVIEW_PROMPT in scanned, "the review prompt file is outside the English-only scan"


# --- build guide task 27a.3: one PR-description builder, not three hand-written ones -------
# /sdlc-plan and /sdlc-design have been migrated to `plugin/pr/cli.py upsert`, so nothing is
# exempt any more: the assertion below covers every command file that opens or updates a PR.
PR_BUILDER_EXEMPT = ()
PR_MENTIONS = ("pr create", "create_pull_request", "upsert")
PR_BUILDER_CALL = 'plugin/pr/cli.py" upsert'


def test_every_pr_opening_command_uses_the_description_builder():
    """Every command that opens or updates a PR calls the step-27a builder, so the <=5-bullet
    summary, the label and the counters are rendered in one place (decision 20)."""
    checked = []
    for path in sorted((PLUGIN / "commands").glob("*.md")):
        body = path.read_text(encoding="utf-8")
        if not any(mention in body for mention in PR_MENTIONS):
            continue
        if path.name in PR_BUILDER_EXEMPT or path.name in RENAMED:
            continue
        assert PR_BUILDER_CALL in body, f"{path.name} opens a PR without {PR_BUILDER_CALL}"
        checked.append(path.name)
    assert set(checked) == set(PHASE_COMMAND_FILES), checked


# --- task 22.4: the session-3 process content (design/build/test/deploy/fix, spec-template,
# --- the review prompt) under the same static contract as the session-2 commands ----------


@pytest.mark.parametrize("name", PHASE_COMMAND_FILES)
def test_every_command_frontmatter_and_guardrails(name):
    """Frontmatter, every referenced script on disk, allow rules quoted identically in the
    body, and the two guardrail reminders every command carries."""
    path = COMMANDS / name
    fm = frontmatter(path)
    assert fm["description"].strip(), f"{name}: empty description"
    assert fm["disable-model-invocation"] == "true", name
    body = path.read_text(encoding="utf-8")
    refs = sorted(set(re.findall(r"\$\{CLAUDE_PLUGIN_ROOT\}/([\w/.-]+\.py)", body)))
    assert refs, f"{name}: no ${{CLAUDE_PLUGIN_ROOT}} script reference"
    for ref in refs:  # the plugin root is the repository root
        assert (PLUGIN.parent / ref).is_file(), f"{name} calls a script that does not exist: {ref}"
    for rule in re.findall(r"Bash\((python [^)]*\.py\") \*\)", fm.get("allowed-tools", "")):
        assert rule in body, f"{name}: allow rule not spelled identically in the body: {rule}"
    text = flat(path)
    assert "Never use bypass-permissions mode" in text or "bypass" in text.lower(), name
    assert "Never notify" in text, f"{name}: no 'Never notify anyone' reminder"


@pytest.mark.parametrize("name", UNATTENDED)
def test_unattended_commands_never_ask_the_owner(name):
    """Only /sdlc-intent and /sdlc-init talk to the owner; the other five park instead."""
    text = flat(COMMANDS / name)
    assert "Never ask the owner" in text or "never ask the owner" in text, name


def test_sdlc_design_flow_matches_steps_22_23():
    text = flat(COMMANDS / "sdlc-design.md")
    for token in [
        "spec-template",
        "plan-template",
        *POLICY_SKILLS,
        "spec-header",
        "start-run",
        "commit-phase",
        "--phase design",
        "sdlc/<id>/design",
        "adversarial-reviewer",
        "check --root",
        "sdlc:design-ready",
        "sdlc:needs-human",
        'pr/cli.py" upsert',
        "Read, Grep and Glob only",
        "prompt v1",
        "Do not start the build phase",
        "the planning run",
    ]:
        assert token in text, token
    positions = [text.index(section.removeprefix("## ")) for section in SPEC_SECTIONS]
    assert positions == sorted(positions), "the spec sections are not named in order"
    assert "read-only planning run" not in text  # row 86: the tool list says read-only


def test_sdlc_design_accepts_a_merged_incident_change_at_phase_maintain():
    """The design run of 2026-09-25 (change 0005) read ``phase: f`` (now ``maintain``) on a
    merged incident intent and stopped with nothing to do: the preconditions say that change
    is at the intent gate."""
    text = flat(COMMANDS / "sdlc-design.md")
    preconditions = text[text.index("## 0. Preconditions") : text.index("## 1. Branch")]
    for token in (
        "entry_route: incident",
        "phase: maintain",
        "the intent gate",
        "decision 25",
        "Proceed",
    ):
        assert token in preconditions, token


def test_the_by_hand_re_run_reads_pr_comments_with_the_membership_filter():
    """The readiness review's group B, item 8: the design and build re-run steps told a
    by-hand session to read the PR's comments with no membership filter, while `/sdlc-fix`
    step 1 keeps only reviews and comments by an `OWNER`, `MEMBER` or `COLLABORATOR`
    (a public repository lets anyone comment: a prompt-injection channel). The prose is
    the whole exposure — in CI `rerun_reason` refuses a re-run while an open PR carries
    the branch."""
    for name in ("sdlc-design", "sdlc-build"):
        text = flat(COMMANDS / f"{name}.md")
        step = text[text.index("## 1. Branch") : text.index("## 2.")]
        for token in (
            "`/sdlc-fix` step 1",
            "`author_association` `OWNER`, `MEMBER` or `COLLABORATOR`",
            "never a `[bot]`",
            "not a change request",
            "`rerun_reason`",
        ):
            assert token in step, f"{name}: {token}"
    fix = flat(COMMANDS / "sdlc-fix.md")
    assert "`OWNER`, `MEMBER` or `COLLABORATOR`, never a `[bot]`" in fix


def test_every_unattended_command_states_the_one_command_rule():
    """The first /sdlc-fix run of 2026-09-23 chained `cd ... && python ...` and was denied
    its last step: a headless run allows only an explicit list of command prefixes, per phase
    (plugin/ci/run_phase.py, the command's allowed-tools), and a chain is allowed only when
    every part of it matches one of them, so the prose says one shell command per Bash call."""
    for name in ("sdlc-design", "sdlc-build", "sdlc-test", "sdlc-deploy", "sdlc-fix"):
        assert "One shell command per Bash call" in flat(COMMANDS / f"{name}.md"), name


# the maintain run has no Agent tool (``detect/cli.py maintain_tools``): it cannot delegate
DELEGATING = tuple(name for name in UNATTENDED if name != "sdlc-maintain.md")


@pytest.mark.parametrize("name", DELEGATING)
def test_every_delegating_command_keeps_its_sub_agents_in_the_foreground(name):
    """Plugin 0.3.3: a headless run has no next turn, so a sub-agent delegated in the
    background and waited for ends the run (change 0001's first build run, 2026-10-03:
    terminated after ten minutes with two agents mid-write, no gate). Every command that
    delegates says so beside its one-command rule, naming the runner's switch."""
    text = (COMMANDS / name).read_text(encoding="utf-8")
    assert "CLAUDE_CODE_DISABLE_BACKGROUND_TASKS" in text, name
    assert "`run_in_background`, set it to false" in text, name
    assert "never end a turn to wait for a sub-agent" in text, name
    assert text.index("Sub-agents run in the foreground") < text.index("## 0."), name
    assert "elegate to" in text, name  # it does delegate


def test_sdlc_build_flow_matches_step_24():
    text = flat(COMMANDS / "sdlc-build.md")
    for token in [
        "preflight.py",
        "lock-tests",
        "code-simplifier",
        "verifier",
        "evidence/verifier.md",
        "adversarial-reviewer",
        "--phase build",
        "sdlc/<id>/build",
        "bump-iteration",
        "--draft",
        "Do not run the test phase here",
    ]:
        assert token in text, token


def test_sdlc_test_flow_matches_step_28():
    text = flat(COMMANDS / "sdlc-test.md")
    for token in [
        "preflight.py",
        "--phase test",
        "evidence/collect.py",
        "bump-iteration",
        "screenshots",
        "sdlc/<id>/build",
        "fresh context",
        "Never weaken, skip or delete a test",
    ]:
        assert token in text, token


def test_sdlc_deploy_flow_matches_step_26():
    text = flat(COMMANDS / "sdlc-deploy.md")
    for token in [
        "preflight.py",
        'review/cli.py" prompt',
        'review/cli.py" validate',
        "--phase deploy",
        "--ready",
        "sdlc:deploy-ready",
        "Never merge",
    ]:
        assert token in text, token
    assert "claude-md-proposals" in text or "Proposed CLAUDE.md lines" in text
    # steps 36 and 37 (plugin 0.2.19): an incident's fix ships with its lesson and its eval,
    # before the review pass reads the diff (p.44 step 7, p.49)
    step = text[text.index("## 0b.") : text.index("## 1. Review passes")]
    for token in ("lessons/<yyyy-mm>-<slug>.md", 'evals/case.py" new', "entry_route", "incident"):
        assert token in step, token
    assert text.index("## 0a.") < text.index("## 0b.") < text.index("## 1. Review passes")


def test_sdlc_deploy_writes_the_lesson_s_frontmatter_and_rebuilds_the_index():
    """Change 0003: the lesson's frontmatter fields, each from a named source, the
    ``supersedes``/``retired_by`` edit to the earlier lesson, and the index rebuild in the
    same commit as the lesson and the eval."""
    path = COMMANDS / "sdlc-deploy.md"
    text = flat(path)
    step = text[text.index("## 0b.") : text.index("## 1. Review passes")]
    for token in [
        "type",
        "`title`",
        "status.yaml: title",
        "description",
        "tags",
        "status.yaml: id",
        "detected",
        "evidence/detection.json",
        "evidence/scan-finding.json",
        "fixed",
        "status.yaml: build_pr",
        "runbook",
        "evidence/proposal.json: route",
        "supersedes",
        "status: retired",
        "retired_by",
        "generated",
        "stale_after",
        "lessons.stale_after_months",
        "sources",
        "run-<n>",
        'lessons/index.py" build',
        "never hand-edit",
        "lesson_and_eval",
    ]:
        assert token in step, token
    assert step.index('evals/case.py" new') < step.index('lessons/index.py" build')
    fm = frontmatter(path)
    assert 'Bash(python "${CLAUDE_PLUGIN_ROOT}/plugin/lessons/index.py" *)' in fm["allowed-tools"]


def test_lessons_readme_sources_example_includes_a_run_n_entry():
    """The ``sources`` example must show the one case `/sdlc-deploy` step 0b actually
    writes for a failed run (spec.md: one `run-<n>` per failed run `detection.json`
    lists), not only the always-present `detection`/`eval`/`fix-pr` ids."""
    template = Path(__file__).resolve().parents[1] / "template"
    text = (template / "lessons" / "README.md").read_text(encoding="utf-8")
    assert '- id: "run-1"' in text
    assert "run-<n>` per failed run" in text


def test_sdlc_fix_flow_matches_the_change_request_loop():
    text = flat(COMMANDS / "sdlc-fix.md")
    for token in ["bump-iteration", "park", "decided", "upsert", "Never merge"]:
        assert token in text, token
    for phase in ["intent", "design", "build", "test", "deploy", "maintain"]:
        assert f"Phase {phase}" in text, phase


def test_sdlc_fix_covers_gate_a_and_the_owner_labels():
    """Decision 22: the fix round on the unmerged intent PR edits intent.md - the one
    exception - on the PR's own head; decision 24: the labels are performed before the
    comments are applied; the trigger is the workflow, never the model."""
    path = COMMANDS / "sdlc-fix.md"
    text = flat(path)
    assert frontmatter(path)["disable-model-invocation"] == "true"
    assert (
        "the phase is `intent`, `design`, `build`, `test`, `deploy` or `maintain` (an older "
        "change may say `a` to `f`" in text
    )  # maintain since 0.2.19; the names since R45
    assert "phase `intent` → the intent PR's head" in text and "`claude/...`" in text
    assert "without re-running the brainstorm" in text
    assert "This is the one place a run edits `intent.md`" in text
    assert "Never edit `intent.md` at design or later" in text
    # decision 35: sdlc:accept-risk retired; the two labels' actors land in status.yaml
    assert "apply-labels" in text and "`iterations_reset_by`" in text
    assert "`sdlc:accept-risk` retired with decision 35" in text
    assert "--branch <head>" in text and "--head <head>" in text
    assert "At phase intent or maintain skip the verdict" in text  # maintain since 0.2.19
    assert "`sdlc-fix.yml`" in text and "Request changes" in text
    assert "`abandoned` change has no fix round" in text
    # D9: only a member's review or comment reaches the round (the second security review)
    assert "`OWNER`, `MEMBER` or `COLLABORATOR`" in text
    assert "not applied: not a member of the repository" in text
    # 0.2.24: in CI the run collected and judged them; the file is the only source
    assert "`changes/<id>-<slug>/evidence/fix-requests.json`" in text
    assert "it is the **only** source of reviews and comments" in text
    assert "not applied: the thread is resolved" in text
    assert "`git rev-parse HEAD`" in text


def test_sdlc_init_states_the_hosting_rule_and_the_outdated_report():
    text = flat(COMMANDS / "sdlc-init.md")
    assert "Hosting is GitHub (decision 23)" in text
    assert "refuses a project whose `origin` remote is on another host" in text
    assert "`outdated`" in text and "the fix round, the abandon rule" in text
    assert "`maintain.observation`" in text  # choice 87


@pytest.mark.parametrize("name", COMMAND_FILES)
def test_the_gate_is_called_in_one_quoted_form(name):
    """One spelling of the gate call everywhere, so the allow rule covers it without a prompt."""
    text = COMMANDS.joinpath(name).read_text(encoding="utf-8")
    if "gate/cli.py" not in text or " check" not in text:
        return
    assert GATE_CHECK in text, f"{name}: the gate check is not spelled {GATE_CHECK}"


@pytest.mark.parametrize("name", RUNBOOKS)
def test_runbooks_register_the_run_before_the_gate(name):
    """start-run gives the gate its wall clock; an automated gate parks without it (step 19)."""
    text = COMMANDS.joinpath(name).read_text(encoding="utf-8")
    assert GATE_START_RUN in text, f"{name}: no start-run"
    assert GATE_CHECK in text, f"{name}: no gate check"
    assert text.index(GATE_START_RUN) < text.index(GATE_CHECK), f"{name}: start-run after check"


def test_spec_skill_sections_and_closing_words():
    path = PLUGIN / "skills" / "spec-template" / "SKILL.md"
    fm = frontmatter(path)
    assert fm["name"] == "spec-template"
    assert "spec.md" in fm["description"] and "Flagged concerns" in fm["description"]
    body = path.read_text(encoding="utf-8")
    positions = [body.index(section) for section in SPEC_SECTIONS]
    assert positions == sorted(positions)
    assert "Change id:" in body and "Produced by:" in body
    for word in ["[x]", "closed", "resolved", "decided"]:
        assert word in body, word
    assert "The closing word must be the first word of the item" in " ".join(body.split())


def test_spec_skill_sections_equal_the_gate_contract():
    """The section names are defined once, in plugin/gate/artifacts.py; the skill repeats them."""
    body = (PLUGIN / "skills" / "spec-template" / "SKILL.md").read_text(encoding="utf-8")
    block = re.search(r"```markdown\n(.*?)```", body, re.S)
    assert block, "the skill has no markdown template block"
    headings = tuple(re.findall(r"^## .+$", block.group(1), re.M))
    assert headings == SPEC_SECTIONS, headings


def test_review_prompt_passes_severity_and_json_shape():
    text = REVIEW_PROMPT.read_text(encoding="utf-8")
    for token in ["Bugs", "Security", "Compliance", "at most five"]:
        assert token in text, token
    for key in ["schema_version", "head", "findings", "tally"]:
        assert key in text, key


def test_review_prompt_keeps_a_repeated_nit_a_nit():
    """Change 0003's (e) fix round (NOTES §35, run 37734768551): the reviewer read
    `changes/.review-seen.json`, saw four nits of the earlier pass at count 2, graded them
    Important as a breach of REVIEW.md's second-occurrence rule and cited that rule in each
    finding's `rule` field, so `validate` proposed four CLAUDE.md lines and the gate parked.
    The rule is the framework's own mechanism (`review/cli.py validate`, `update_seen`: a
    repeat counts across changes only), never a breach by the diff: the brief says so even
    against REVIEW.md's wording, forbids reading the record and citing the rule, and keeps a
    repeated finding's own severity; the template REVIEW.md says "across changes" and that a
    repeated finding keeps its own severity."""
    text = " ".join(REVIEW_PROMPT.read_text(encoding="utf-8").split())
    for token in [
        "except for how its second-occurrence rule is read",
        "Do not read `changes/.review-seen.json`",
        "do not grade a finding by how often it was reported",
        "never cite that rule in a finding's `rule` field",
        "whatever REVIEW.md's wording: a repeated nit is a nit",
        "counts a finding's occurrences across changes",
    ]:
        assert token in text, token
    review_md = " ".join(
        (PLUGIN.parent / "template" / "REVIEW.md").read_text(encoding="utf-8").split()
    )
    assert "across changes produces a one-line entry" in review_md
    assert "a repeated finding keeps its own severity" in review_md


def test_review_prompt_renders_with_str_format():
    """cli.py prompt fills the placeholders with str.format, so the JSON braces must be
    doubled: a single brace would raise KeyError or IndexError here."""
    rendered = REVIEW_PROMPT.read_text(encoding="utf-8").format(
        change_id="0001",
        title="Sample change",
        branch="sdlc/0001/c",
        head="0" * 40,
        base="main",
        root="/tmp/project",
        change_dir="/tmp/project/changes/0001-sample",
    )
    assert "{change_id}" not in rendered and "0001" in rendered
    block = re.search(r"```json\n(.*?)```", rendered, re.S)
    assert block, "the review prompt has no JSON block"
    shape = json.loads(block.group(1))
    assert shape["head"] == "0" * 40
    assert sorted(shape["tally"]) == ["important", "nit", "nits_omitted"]
    assert shape["findings"][0]["severity"]


# --- 0.2.12: the reviewer has no shell (deliverable 6(e)); gate (e) finished (step 32) -------
REVIEWER_BRIEFS = {
    "sdlc-design.md": "design",
    "sdlc-build.md": "build",
    "sdlc-test.md": "test",
    "sdlc-fix.md": "<phase>",
}


@pytest.mark.parametrize("name", sorted(REVIEWER_BRIEFS))
def test_reviewer_delegation_writes_the_diff_file_and_passes_the_sha_first(name):
    """The adversarial reviewer has no Bash, so every run that delegates to it writes the
    diff file in one git call and reads HEAD's sha before the delegation, and hands both over;
    the diff file is evidence committed after the gate."""
    text = flat(COMMANDS / name)
    phase = REVIEWER_BRIEFS[name]
    diff_file = f"changes/<id>-<slug>/evidence/diff-{phase}.patch"
    write = f"git diff --stat --patch --output={diff_file} <base>...HEAD"
    assert write in text, name
    assert "git rev-parse HEAD" in text, name
    delegate = re.search(r"Delegate to (?:the )?`sdlc:adversarial-reviewer`", text).start()
    assert text.index(write) < delegate, f"{name}: the diff file is written after delegating"
    assert text.index("git rev-parse HEAD") < delegate, name
    brief = text[delegate : delegate + 400]
    assert "full HEAD sha" in brief and diff_file in brief, name
    assert "The diff file is evidence" in text, name
    assert " && " not in write  # one shell command per Bash call


def test_sdlc_deploy_prepares_the_release_around_the_review_and_the_gate():
    """Step 32: the adapter's artifact is prepared and committed BEFORE the review pass, so
    the review and gate (e) judge HEAD with it (no extra review job); the release notes are
    written AFTER the gate check and ride in the evidence commit (OPERATING_MODEL 4.1:
    evidence is committed after the gate); step 5 only marks the PR ready."""
    text = flat(COMMANDS / "sdlc-deploy.md")
    prep = text[text.index("## 0a. Prepare the release artifact") :]
    prep = prep[: prep.index("## 1. Review passes")]
    assert text.index("## 0a. Prepare the release artifact") < text.index("## 1. Review passes")
    assert text.index("## 0a.") < text.index('review/cli.py" prompt')
    assert "notes.py" not in prep
    assert "is a departure from `plan.md` unless the plan lists it" in prep
    assert '"## Files that change" of `plan.md` in the same commit' in prep
    assert '--phase deploy --message "release(<id>): release prepared"' in prep
    assert "## 3a." not in text and "fresh review of the new HEAD" not in text
    # 0.2.26: after the panel's commits the review pass runs again; ``validate`` alone re-reads
    # the stale findings file and gate (e) refuses it; phase (e) has no diff or verdict file
    panel = text[text.index("### Deferred review") : text.index("## 4. The deploy gate")]
    assert "run step 1 again for the new HEAD, once" in panel
    assert "`validate` only re-reads `review-findings.json`, it re-reviews nothing" in panel
    assert "re-run step 1's `validate`" not in panel
    assert "diff file" not in panel and "verdict file" not in panel
    notes_call = (
        'python "${CLAUDE_PLUGIN_ROOT}/plugin/release/notes.py" --root "${CLAUDE_PROJECT_DIR}" '
        "--id <id> --write"
    )
    gate = text[text.index("## 4. The deploy gate") : text.index("## 5. Mark the PR ready")]
    evidence_commit = (
        'commit-phase --root "${CLAUDE_PROJECT_DIR}" --id <id> --phase deploy '
        '--message "review(<id>): gate (deploy) evidence" --push'
    )
    assert gate.index(GATE_CHECK) < gate.index(notes_call) < gate.index(evidence_commit)
    assert "evidence/release-notes.md" in gate
    step5 = text[text.index("## 5. Mark the PR ready with the final summary") :]
    step5 = step5[: step5.index("## 6. Hand over")]
    assert "notes.py" not in step5 and "commit-phase" not in step5
    assert "evidence/release-notes.md" in step5
    for adapter in (
        "publish package",
        "regenerate report",
        "schedule job",
        "promote to paper trading",
        "deploy service",
        "none",
    ):
        assert f"`{adapter}` →" in prep, adapter
    for nothing in (
        "nothing uploaded",
        "nothing scheduled",
        "nothing promoted",
        "nothing deployed",
    ):
        assert nothing in prep, nothing
    assert "--ready" in step5 and "sdlc:deploy-ready" in step5
    assert "The agent does everything up to the production gate and nothing past it" in text
    # R22 (decision 36): the approval is gate (e), and the merge App merges on it
    assert "the approval = gate (deploy) passed (decision 36); the merge App then merges it" in (
        " ".join(step5.split())
    )
    two_acts = (
        "the release label `sdlc:release-approved` is the second act: apply it on this PR "
        "in the same visit; the release workflow waits for it"
    )
    assert two_acts in " ".join(step5.split())
    # decision 5: the label is the only route, a signed tag a run could make is not one
    assert "signed tag" not in text
    hand_over = text[text.index("## 6. Hand over") :]
    assert two_acts in " ".join(hand_over.split()) and "Nothing else runs" in hand_over
    fm = frontmatter(COMMANDS / "sdlc-deploy.md")
    assert 'Bash(python "${CLAUDE_PLUGIN_ROOT}/plugin/release/notes.py" *)' in fm["allowed-tools"]
    assert "is B4" not in fm["description"] and "release workflow" in fm["description"]


def test_no_command_or_agent_defers_to_a_finished_build_stage():
    """B3 shipped in 0.2.x and B4 ships with 0.2.12: no process file may still say that
    something "is B4" or "is/are B3" (or "from B3 on", "(B4)")."""
    stale = re.compile(r"\b(?:is|are|from|available from)\s+B[34]\b|\(B[34]\)|\bB[34] on\b")
    for path in sorted(COMMANDS.glob("*.md")) + sorted((PLUGIN / "agents").glob("*.md")):
        for match in stale.finditer(flat(path)):
            raise AssertionError(f"{path.name}: stale build-stage reference {match.group(0)!r}")
    for path in sorted(COMMANDS.glob("*.md")) + sorted((PLUGIN / "agents").glob("*.md")):
        assert not re.search(r"\bB[34]\b", path.read_text(encoding="utf-8")), path.name


def test_pr_route_order_matches_the_github_client():
    """pr/github.py tries the REST API with the token first, then `gh`, then the compare URL
    (since 0.2.3); the commands describe the same order."""
    plan = flat(COMMANDS / "sdlc-intent.md")
    assert (
        "the GitHub REST API with the token (`GITHUB_TOKEN`/`GH_TOKEN`) first, then the `gh` CLI"
        in plan
    )
    build = flat(COMMANDS / "sdlc-build.md")
    assert "uses the GitHub REST API with `GITHUB_TOKEN`/`GH_TOKEN` first, then `gh`" in build


def test_sdlc_maintain_flow_matches_step_37():
    """Build guide step 37 (article p.43-44): the diagnosis reads lessons/ and the detection
    record first, investigates read-only, writes the incident intent with its Evidence
    section and a proposal, dispatches it through the route's authorization, runs gate (f)
    and opens the intent PR labelled incident; nothing is fixed, merged or deployed."""
    path = COMMANDS / "sdlc-maintain.md"
    fm = frontmatter(path)
    text = flat(path)
    assert "Edit" not in fm["allowed-tools"].replace("acceptEdits", "")
    assert "Bash(gh run view *)" in fm["allowed-tools"]
    for token in [
        'detect/cli.py" run',
        "detection.json",
        "lessons/",
        "intent-template",
        "## Evidence",
        "proposal.json",
        'detect/cli.py" routes',
        'detect/cli.py" dispatch',
        "--phase maintain",
        "sdlc/<id>/intent",
        "sdlc:maintain-ready",
        "incident",
        "sdlc:go",
        "decision 25",
        "decision 26",
        "Never edit source",
        "Do not start the design phase",
    ]:
        assert token in text, token
    assert text.index('detect/cli.py" routes') < text.index("proposal.json")
    assert text.index("commit-phase") < text.index('detect/cli.py" dispatch')
    assert text.index('detect/cli.py" dispatch') < text.index(GATE_CHECK)
    assert text.index(GATE_START_RUN) < text.index(GATE_CHECK)


def test_sdlc_maintain_reads_the_generated_index_first():
    """Change 0003: the diagnosis reads ``lessons/index.md`` and opens only the lessons its
    tags name, falling back to every file when the index is stale or missing, and never
    rebuilds the index itself (that is `/sdlc-deploy` step 0b)."""
    path = COMMANDS / "sdlc-maintain.md"
    text = flat(path)
    fm = frontmatter(path)
    assert 'Bash(python "${CLAUDE_PLUGIN_ROOT}/plugin/lessons/index.py" *)' in fm["allowed-tools"]
    for token in [
        "lessons/index.md",
        'lessons/index.py" check',
        "Tags",
        "## Retired",
        "## Unsorted",
        "stale or missing",
        "## Evidence",
        "(stale)",
        "never rebuild",
    ]:
        assert token in text, token


def test_sdlc_init_commits_every_path_the_install_writes():
    """0.2.25 (1.0.0 readiness review): the change-0000 commit listed neither ``.github``
    nor ``lessons``, so a project set up by the book merged with no workflows and no pin
    script — every pin step's ``git show`` of the script then fails. ``commit-phase``
    commits the change folder plus ``--paths`` and nothing else."""
    from init import sdlc_init

    text = (COMMANDS / "sdlc-init.md").read_text(encoding="utf-8")
    match = re.search(r"--paths (.+?) --start-point", text)
    assert match, "the commit-phase call of step 5 names its --paths"
    listed = match.group(1).split()
    written = [
        *sdlc_init.WORKFLOW_FILES,
        "lessons/README.md",
        "policies/README.md",  # R27
        "REVIEW.md",
        "changes/README.md",
        "evals/README.md",
        "evals/cases/.gitkeep",
        "evals/check.py",
        "bands.yaml",
        "sdlc.yaml",
        ".claude/settings.json",
        "CLAUDE.md",
        "ruff.toml",
    ]
    for rel in written:
        covered = any(rel == p or rel.startswith(p.rstrip("/") + "/") for p in listed)
        assert covered, f"{rel} is written by the install but not committed by step 5"


def test_sdlc_init_marks_every_settings_act_desktop_only_with_its_link():
    """R21's first part (choice 257): every act of step 6 that is a repository setting, which
    the GitHub mobile app does not show, says it is desktop-only and gives the direct link
    to the project's settings page; step 5's report names them the same way."""
    text = flat(COMMANDS / "sdlc-init.md")
    step_6 = text[text.index("## 6. After the merge") :]
    bullets = [b for b in step_6.split(" - ") if "Settings →" in b]
    assert len(bullets) >= 4  # the permission and the secret, the App, the merge App, rulesets
    for bullet in bullets:
        assert "Desktop-only" in bullet or "desktop-only" in bullet, bullet[:80]
        assert "https://github.com/" in bullet, bullet[:80]
    for link in ("/settings/actions`", "/settings/secrets/actions`", "/settings/rules`"):
        assert f"https://github.com/<owner>/<repo>{link}" in step_6
    report = text[text.index("## 5. Commit") : text.index("## 6. After the merge")]
    assert "each settings act marked desktop-only with its direct link (ROADMAP R21)" in report


def test_sdlc_init_prescribes_the_branch_ruleset_of_decision_4():
    """0.2.25: decision 4 is enforced by a GitHub ruleset the framework never creates; the
    owner is told to create it, and the digest says while it is missing."""
    text = flat(COMMANDS / "sdlc-init.md")
    assert "branch ruleset on the default branch (decision 4" in text
    assert "Require a pull request before merging" in text
    # the review of the 0.2.25 diff (H1): only "Restrict updates" with the owner as the sole
    # bypass actor keeps the workflow token from merging a pull request
    assert (
        '**"Restrict updates"** with the repository admin (the owner) as the only bypass actor '
        "besides the merge App" in text
    )
    # R22 (decision 36): the merge App is the second bypass actor, decision 33's App never
    assert 'the merge App above is its second bypass actor, in "For pull requests only"' in text
    assert "Never add this App to a ruleset's bypass list" in text
    assert "still lets `gh pr merge` through" in text
    assert "The daily digest says so" in text
    # 0.2.26: the owner is Exempt in the merge ruleset (NOTES section 17); 1.0.23 (choice 251,
    # NOTES section 57): Exempt alone let anything acting as the owner's login write to the
    # default branch, so the review ruleset also holds the no-direct-writes rules, with the
    # owner's bypass for pull requests only
    assert "The owner's bypass actor's mode is **Exempt**" in text
    assert "No setting stops a session acting as your login from merging" in text
    assert "the workflow token included" in text
    # R45's fifth rename PR (decision 39, rows N9 and N10): "Ruleset 1" and "Ruleset 2" are
    # the merge ruleset and the review ruleset, and the review ruleset's name on GitHub drops
    # its decision reference; a project with the old name renames it by hand
    assert "name `review and no direct writes on main`; enforcement **Active**" in text
    assert "rename it to `review and no direct writes on main` yourself" in text
    for old in ("Ruleset 1", "Ruleset 2", "ruleset 1", "ruleset 2"):
        assert old not in text
    ruleset_2 = text[text.index("- The review ruleset, which holds a build PR") :]
    for rule in (
        '**"Require status checks to pass"**',
        '**"Require a pull request before merging"**, with required approvals **0**',
        '**"Block force pushes"**',
        '**"Restrict deletions"**',
    ):
        assert rule in ruleset_2
    assert 'role (you), in "For pull requests only" mode, so your bypass never covers a push' in (
        ruleset_2
    )
    model = (PLUGIN.parent / "docs" / "OPERATING_MODEL.md").read_text(encoding="utf-8")
    assert "The owner's bypass mode is *Exempt*" in model
    assert '"Require a pull request before merging", "Block force pushes" and' in model


# --- R29 part 1 and R54: examples, the mock and the quick intent --------------------------------
def test_intent_template_has_examples_after_the_article_sections():
    """R29 part 1: Examples/References follows Open questions and precedes the incident-only
    Evidence; the gate does not require it (INTENT_SECTIONS is unchanged)."""
    from gate import artifacts as art

    body = (PLUGIN / "skills" / "intent-template" / "SKILL.md").read_text(encoding="utf-8")
    block = re.search(r"```markdown\n(.*?)```", body, re.S).group(1)
    headings = [h.split("   ")[0] for h in re.findall(r"^## .+$", block, re.M)]
    assert headings == [*art.INTENT_SECTIONS, art.INTENT_EXAMPLES_SECTION, "## Evidence"]
    assert art.INTENT_EXAMPLES_SECTION not in art.INTENT_SECTIONS
    text = " ".join(body.split())
    assert "never a referenced screen" in text
    # the quick intent's marker is the gate's, word for word
    assert f"`{art.QUICK_INTENT_MARKER}`" in text and "`Quick intent: yes`" in text


def test_the_mock_question_and_the_mock_line():
    """R29 part 1: the interview asks for a mock on a screen change; spec.md's Acceptance gets
    a fixed Mock: line; the build matches the mock, never the referenced screens."""
    plan = flat(COMMANDS / "sdlc-intent.md")
    assert '"Do you have a mock or example screens?"' in plan and "never blocks" in plan
    spec = flat(PLUGIN / "skills" / "spec-template" / "SKILL.md")
    assert "`Mock: mock/<file>`" in spec
    assert "`Mock: none, screens follow the UX conventions`" in spec
    build = flat(COMMANDS / "sdlc-build.md")
    assert "never the screens the intent's Examples/References only refer to" in build
    assert "`Mock:` line" in flat(COMMANDS / "sdlc-design.md")


def test_the_quick_intent_route():
    """R54: one paragraph, no correction loop at (a); the design run states its assumptions
    in the section the gate requires and the reviewer judges."""
    from gate import artifacts as art

    plan = flat(COMMANDS / "sdlc-intent.md")
    assert "**The quick intent**" in plan and "`quick:`" in plan
    assert "skip step 4's correction loop" in plan
    heading = art.SPEC_ASSUMED_SECTION
    for path in (
        COMMANDS / "sdlc-design.md",
        PLUGIN / "skills" / "spec-template" / "SKILL.md",
    ):
        assert f"`{heading}`" in flat(path), path.name
    assert heading.lstrip("# ") in flat(PLUGIN / "agents" / "adversarial-reviewer.md")


def test_the_plan_skill_states_the_proof_item_grammar():
    """Change 0004 (R5, panel decision 3): the three kinds, the any-line rule and the one
    parse beside the grammar; the grammar the skill shows is the one the gate parses."""
    from gate import artifacts as art

    text = flat(PLUGIN / "skills" / "plan-template" / "SKILL.md")
    for words in (
        "`- test: <name>`",
        "`- screenshot: evidence/proof/<file>.png`, optionally followed by ` vs mock/<file>`",
        "`- state: evidence/proof/<file> <path> ==|contains|matches <value>`",
        "Only a list item whose text starts with `test:`, `screenshot:` or `state:` is an item",
        "**The one parse**: the expected value and each line of a text file are read as JSON",
        "a bool never equals a number, `1` never equals `1.0`, `[true]` is not `[1]`",
        "**The any-line rule**: with `line`, the item holds when any line of the text file",
        "the value seen is the file's first line",
        "the design gate's check `proof_items` refuses the plan without one",
    ):
        assert words in text, words
    example = (
        "## Proof\n- test: tests/test_x.py\n"
        "- screenshot: evidence/proof/home.png vs mock/home.png\n"
        "- state: evidence/proof/s.json status.code == 200\n- ratchet: tests may fall, because x\n"
    )
    assert [i.kind for i in art.proof_items(example)] == ["test", "screenshot", "state"]
    assert art.malformed_proof_items(example) == []


def test_the_phase_commands_follow_the_drive():
    """Change 0004 (R15): /sdlc-test step 3 compares (c)'s proof/ images when a drive is set and
    loses the sentence no code backed; /sdlc-build names the drive's screenshot item."""
    test = flat(COMMANDS / "sdlc-test.md")
    assert "When `sdlc.yaml: commands.drive` is set (change 0004), capture nothing by hand" in test
    assert "open those images with the Read tool, compare each with the mock" in test
    assert "When the drive is empty: run the app" in test
    assert "Never run the drive in this session" in test
    assert "the gate treats it as evidence missing" not in test
    build = flat(COMMANDS / "sdlc-build.md")
    assert (
        "`- screenshot: evidence/proof/<file>.png vs mock/<file>`, added to the plan during "
        "the build," in (build)
    )
    assert "reported and never the bar" in build
    assert (
        'list the drive\'s own files (the Playwright test, its config) under "Files that change"'
        in (build)
    )


def test_the_policy_skills_say_what_the_gate_checks_of_a_screenshot():
    """Change 0004 (R11): the two skills that said no gate check reads a screenshot."""
    done = flat(PLUGIN / "skills" / "definition-of-done" / "SKILL.md")
    assert (
        "the screenshots named as `screenshot:` items of the approved plan are checked under "
        "`evidence/proof/` by the gate's `proof` entry (change 0004)"
    ) in done
    assert (
        "by-hand screenshots under `evidence/screenshots/` are still required by no check" in done
    )
    ux = flat(PLUGIN / "skills" / "ux-and-brand" / "SKILL.md")
    assert "`evidence/proof/` or `evidence/screenshots/` holds a screenshot" in ux
    assert "Rule 7 has one only when `sdlc.yaml: commands.drive` is set" in ux
    assert "UI changed but evidence/proof/ and evidence/screenshots/ hold no screenshot" in ux


@pytest.mark.parametrize(
    "path",
    [
        *sorted(COMMANDS.glob("*.md")),
        *sorted((PLUGIN / "skills").glob("*/SKILL.md")),
        *sorted((PLUGIN / "panel" / "briefs").glob("*.md")),
        PLUGIN / "review" / "REVIEW_PROMPT.md",
        PLUGIN / "agents" / "adversarial-reviewer.md",
    ],
    ids=lambda p: f"{p.parent.name}/{p.name}",
)
def test_every_instruction_names_the_reviewer_s_verdict_park(path):
    """R45 row 62: the adversarial reviewer's verdict is ``continue | park``, the word the
    gate's result and the state use for the same event. An instruction to a model never asks
    for ``escalate``; it names it only as an older plugin's word (the history lines that quote
    what a run did, "escalated on ...", stay)."""
    text = " ".join(path.read_text(encoding="utf-8").split())
    for old in ("an `escalate`", "the reviewer's `escalate`", "escalation on", "`continue` or "
                "`escalate`", "- Word:", "escalates on"):  # fmt: skip
        assert old not in text, (path.name, old)
