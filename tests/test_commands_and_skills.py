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
# /sdlc-plan and /sdlc-init are the two attended commands: they talk to the owner. Every
# other command runs unattended and parks instead of asking (OPERATING_MODEL: escalate = park).
ATTENDED = ("sdlc-plan.md", "sdlc-init.md")
UNATTENDED = tuple(name for name in COMMAND_FILES if name not in ATTENDED)
POLICY_SKILLS = (
    "coding-standards",
    "security-baseline",
    "ux-conventions",
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


@pytest.mark.parametrize("name", ["sdlc-plan", "sdlc-init"])
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


def test_sdlc_plan_flow_matches_step_11():
    body = (PLUGIN / "commands" / "sdlc-plan.md").read_text(encoding="utf-8")
    for step in [
        "Brainstorm",
        "new-change",
        "intent-template",
        "owner corrects",
        "commit-phase",
        "sdlc:a-ready",
        "compare/",
    ]:
        assert step in body, step
    assert "$ARGUMENTS" in body
    assert "Do not start phase (b)" in " ".join(body.split())


def test_sdlc_init_flow_matches_step_21():
    body = (PLUGIN / "commands" / "sdlc-init.md").read_text(encoding="utf-8")
    for token in [
        "--detect-only",
        "profile",
        "deploy action",
        "maintain metric",
        "/init",
        "sdlc_init.py",
        "--id 0000",
        "sdlc:a-ready",
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
    assert (
        "Author:" in body and "Status:" in body and "Change id:" in body and "Entry route:" in body
    )
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
        if path.name in PR_BUILDER_EXEMPT:
            continue
        assert PR_BUILDER_CALL in body, f"{path.name} opens a PR without {PR_BUILDER_CALL}"
        checked.append(path.name)
    assert set(checked) == {p.name for p in sorted((PLUGIN / "commands").glob("*.md"))}, checked


# --- task 22.4: the session-3 process content (design/build/test/deploy/fix, spec-template,
# --- the review prompt) under the same static contract as the session-2 commands ----------


@pytest.mark.parametrize("name", COMMAND_FILES)
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
    """Only /sdlc-plan and /sdlc-init talk to the owner; the other five park instead."""
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
        "--phase b",
        "adversarial-reviewer",
        "check --root",
        "sdlc:b-ready",
        "sdlc:needs-human",
        'pr/cli.py" upsert',
        "Read, Grep and Glob only",
        "prompt v1",
        "Do not start phase (c)",
    ]:
        assert token in text, token
    positions = [text.index(section.removeprefix("## ")) for section in SPEC_SECTIONS]
    assert positions == sorted(positions), "the spec sections are not named in order"


def test_sdlc_build_flow_matches_step_24():
    text = flat(COMMANDS / "sdlc-build.md")
    for token in [
        "preflight.py",
        "lock-tests",
        "code-simplifier",
        "verifier",
        "evidence/verifier.md",
        "adversarial-reviewer",
        "--phase c",
        "bump-iteration",
        "--draft",
        "Do not run (d) here",
    ]:
        assert token in text, token


def test_sdlc_test_flow_matches_step_28():
    text = flat(COMMANDS / "sdlc-test.md")
    for token in [
        "evidence/collect.py",
        "bump-iteration",
        "screenshots",
        "--phase d",
        "fresh context",
        "Never weaken, skip or delete a test",
    ]:
        assert token in text, token


def test_sdlc_deploy_flow_matches_step_26():
    text = flat(COMMANDS / "sdlc-deploy.md")
    for token in [
        'review/cli.py" prompt',
        'review/cli.py" validate',
        "--phase e",
        "--ready",
        "sdlc:e-ready",
        "Never merge",
    ]:
        assert token in text, token
    assert "claude-md-proposals" in text or "Proposed CLAUDE.md lines" in text


def test_sdlc_fix_flow_matches_the_change_request_loop():
    text = flat(COMMANDS / "sdlc-fix.md")
    for token in ["bump-iteration", "park", "decided", "upsert", "Never merge"]:
        assert token in text, token
    for phase in ["(b)", "(c)", "(d)", "(e)"]:
        assert f"Phase {phase}" in text, phase


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
