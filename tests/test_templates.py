"""Template files: structure required by the handoff, placeholders resolvable, valid JSON/YAML."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from init import render
from state import yamlish

TEMPLATE = Path(__file__).resolve().parents[1] / "template"

VALUES = {
    "PROJECT_NAME": "demo",
    "PROFILE": "standard",
    "REVIEW": "parked",
    "BUILD_CMD": "python -m build",
    "TEST_CMD": "python -m pytest",
    "LINT_CMD": "python -m ruff check .",
    "SETUP_CMD": "python -m pip install pytest ruff",
    "BUILD_HEALTHY": "exit code 0",
    "TEST_HEALTHY": "N passed",
    "LINT_HEALTHY": "All checks passed!",
    "CONVENTIONS": "- x",
    "ARCHITECTURE": "- y",
    "DEPLOY_ACTION": "none",
    "DEPLOY_PRODUCTION": "false",
    "MAINTAIN_METRIC": "ci_test_failure_rate",
    "MAINTAIN_SOURCE": "github-actions",
    "PLUGIN_VERSION": "0.1.0",
    "BUILD_RULE": "Bash(python -m build *)",
    "TEST_RULE": "Bash(python -m pytest *)",
    "LINT_RULE": "Bash(python -m ruff *)",
    "TEST_PATHS": '  - "tests/**"\n  - "**/test_*.py"',
    "FRAMEWORK_REPO": "luissiviero/sdlc-framework",
    "CLAUDE_CODE_VERSION": "2.1.278",
}


def test_render_rejects_missing_placeholders():
    with pytest.raises(render.RenderError):
        render.render("hello {{NAME}}", {})
    assert render.render("hello {{NAME}}", {"NAME": "x"}) == "hello x"


def test_every_template_placeholder_has_a_value():
    for path in TEMPLATE.rglob("*"):
        if path.is_file() and "__pycache__" not in path.parts:  # evals/check.py is importable
            missing = render.placeholders(path.read_text(encoding="utf-8")) - set(VALUES)
            assert not missing, f"{path}: {missing}"


def test_claude_md_skeleton_sections():
    text = render.render_file(TEMPLATE / "CLAUDE.md", VALUES)
    for heading in [
        "## Commands",
        "## Conventions",
        "## Architecture",
        "## Things Claude gets wrong",
        "## Verifying your work",
    ]:
        assert heading in text
    # article p.28 verification block, verbatim lines
    assert "Run all three before reporting any task complete, and paste the output." in text
    assert "If a test fails, fix the code, not the test." in text
    assert "(all green; never skip or delete a failing test)" in text
    assert "(zero warnings)" in text
    assert "healthy:" in text  # p.27 step 2: each command with a healthy output
    assert len(text.splitlines()) <= 60, "keep CLAUDE.md under a page (p.20)"


def test_review_md_structure():
    text = (TEMPLATE / "REVIEW.md").read_text(encoding="utf-8")
    for heading in [
        "## Passes",
        "## What Important means here",
        "## Cap the nits",
        "## Do not report",
    ]:
        assert heading in text
    for pass_name in ["Bugs:", "Security:", "Compliance:"]:
        assert pass_name in text
    assert (
        "Reserve Important for findings that would break behavior, leak data or breach a policy."
        in text
    )
    assert "Report at most five nits per review" in text
    # rules added by the guide (step 26 notes; step 7 (iv); step 25; step 12)
    flat = " ".join(text.split())
    assert ".claude/**" in flat and "must not modify test files" in flat and "plan.md" in flat


def test_sdlc_yaml_renders_to_documented_keys():
    data = yamlish.loads(render.render_file(TEMPLATE / "sdlc.yaml", VALUES))
    assert data["profile"] == "standard"
    # decision 21 (0.2.14): the review mode and the devil's advocate's model
    assert data["review"] == "parked" and data["panel_advocate_model"] == "opus"
    assert "lite" not in render.render_file(TEMPLATE / "sdlc.yaml", VALUES).split("review:")[
        0
    ].replace("(lite, gates (a) and (e) only, was withdrawn", "").replace(
        "that still says lite reads as standard", ""
    )
    assert data["commands"] == {
        "build": "python -m build",
        "test": "python -m pytest",
        "lint": "python -m ruff check .",
        # step 30: the one-command install the CI phase jobs run before the phase
        "setup": "python -m pip install pytest ruff",
    }
    # step 29 / 32: the release workflow's command and the production-gate hook's patterns
    assert data["deploy"] == {
        "action": "none",
        "production": False,
        "command": "",
        "guarded_commands": [],
    }
    assert (
        data["maintain"]["metric"] == "ci_test_failure_rate" and data["maintain"]["runbooks"] == []
    )
    assert data["risk_list"] == ["auth", "data migrations", "money movement", "production config"]
    assert data["test_paths"] == ["tests/**", "**/test_*.py"]  # step 25: the test-file lock
    assert data["protected_paths"] == [] and data["plan_sync"]["exempt"] == ["*.md"]
    assert data["hooks"]["format_on_edit"] is True
    assert data["plugin"] == {
        "name": "sdlc",
        "marketplace": "sdlc-framework",
        "version": VALUES["PLUGIN_VERSION"],
        "claude_code": VALUES["CLAUDE_CODE_VERSION"],  # step 30: the CLI the workflows pin
    }


def test_sdlc_yaml_also_parses_with_pyyaml():
    yaml = pytest.importorskip("yaml")
    text = render.render_file(TEMPLATE / "sdlc.yaml", VALUES)
    assert yaml.safe_load(text) == yamlish.loads(text)


def test_settings_json_contract():
    data = json.loads(render.render_file(TEMPLATE / ".claude" / "settings.json", VALUES))
    deny = data["permissions"]["deny"]
    for rule in ["Read(.env*)", "Read(./secrets/**)", "WebFetch", "Bash(curl *)", "Bash(wget *)"]:
        assert rule in deny  # article p.37
    for rule in ["Edit(/.claude/**)", "Edit(/CLAUDE.md)", "Edit(/REVIEW.md)", "Edit(/sdlc.yaml)"]:
        assert rule in deny  # second layer under the protected-path hook
    assert not any(r.startswith("Write(") for r in deny), (
        "Write() path rules are ignored by Claude Code"
    )
    assert "Bash(git *)" in data["permissions"]["allow"]
    assert data["permissions"]["disableBypassPermissionsMode"] == "disable"
    assert data["sandbox"]["enabled"] is True and data["sandbox"]["failIfUnavailable"] is False
    assert data["enabledPlugins"] == {"sdlc@sdlc-framework": True}
    assert (
        data["extraKnownMarketplaces"]["sdlc-framework"]["source"]["repo"]
        == "luissiviero/sdlc-framework"
    )
    assert "hooks" not in data, "hooks come from the pinned plugin, never from the project file"
    assert not any(k.startswith("$comment") for k in data)
    assert not any("--force" in r for r in deny), "force-push cannot be caught by Bash() rules"
    assert not any("tasks.py" in r for r in data["permissions"]["allow"])


def test_changes_readme_names_the_conventions():
    text = (TEMPLATE / "changes" / "README.md").read_text(encoding="utf-8")
    for token in [
        "status.yaml",
        "sdlc/<id>/a",
        "sdlc:needs-human",
        "intent.md",
        "plan.md",
        "evidence/",
    ]:
        assert token in text


def test_bands_yaml_has_the_p44_shape_with_authorization_per_route():
    text = render.render((TEMPLATE / "bands.yaml").read_text(encoding="utf-8"), VALUES)
    data = yamlish.loads(text)
    assert set(data) == {"metric", "source", "baseline", "rules", "tiers"}
    assert set(data["tiers"]) == {"1sigma", "2sigma", "3sigma"}
    for route in data["tiers"]["3sigma"]["routes"]:
        assert route["authorization"] in ("preapproved", "go")
    assert (TEMPLATE / "evals" / "README.md").is_file() and (
        TEMPLATE / "evals" / "cases" / ".gitkeep"
    ).is_file()


# --- the SDLC workflows (build guide step 30; OPERATING_MODEL section 4.2) --------------------
WORKFLOW_DIR = TEMPLATE / ".github" / "workflows"
PHASE_WORKFLOWS = ("sdlc-design.yml", "sdlc-build.yml", "sdlc-test.yml", "sdlc-deploy.yml")
RELEASE_WORKFLOW = "sdlc-release.yml"  # build guide step 32.3 (plugin 0.2.12)
FIX_WORKFLOW = "sdlc-fix.yml"  # decisions 22 and 24 (plugin 0.2.13)
ABANDON_WORKFLOW = "sdlc-abandon.yml"  # decision 25 (plugin 0.2.13)
DETECT_WORKFLOW = "sdlc-detect.yml"  # build guide step 37, decisions 14/15/26 (plugin 0.2.19)
RUNBOOK_WORKFLOW = "sdlc-runbook.yml"  # the owner's Go on a runbook (plugin 0.2.19)
EVALS_WORKFLOW = "sdlc-evals.yml"  # build guide step 35 (plugin 0.2.19)
SCAN_WORKFLOW = "sdlc-scan.yml"  # build guide step 38, decision 16 (plugin 0.2.19)
ALL_WORKFLOWS = (
    *PHASE_WORKFLOWS,
    "sdlc-digest.yml",
    RELEASE_WORKFLOW,
    FIX_WORKFLOW,
    ABANDON_WORKFLOW,
    DETECT_WORKFLOW,
    RUNBOOK_WORKFLOW,
    EVALS_WORKFLOW,
    SCAN_WORKFLOW,
)
# this repository's own installed copies (PR #21) and its substrate smoke test
REPO_WORKFLOW_DIR = TEMPLATE.parent / ".github" / "workflows"
# the explicit default branch a detect/scan CLI step reads before its git guess (live run of
# 2026-09-25: a checkout of a non-default ref has no origin/HEAD and no local main)
DEFAULT_BRANCH_EXPR = "${{ github.event.repository.default_branch }}"


def test_workflow_templates_exist_and_render():
    assert sorted(p.name for p in WORKFLOW_DIR.glob("*.yml")) == sorted(ALL_WORKFLOWS)
    for name in ALL_WORKFLOWS:
        text = render.render_file(WORKFLOW_DIR / name, VALUES)
        # GitHub's own ${{ ... }} expressions survive; no {{NAME}} placeholder may.
        assert render.placeholders(text) == set()
        assert VALUES["FRAMEWORK_REPO"] in text


def _workflow_yaml(name: str) -> dict:
    yaml = pytest.importorskip("yaml")
    data = yaml.safe_load(render.render_file(WORKFLOW_DIR / name, VALUES))
    assert isinstance(data, dict) and data.get("jobs"), name
    return data


def _triggers(data: dict) -> dict:
    return data.get("on", data.get(True))  # YAML 1.1 reads a bare `on` key as True


@pytest.mark.parametrize("name", ALL_WORKFLOWS)
def test_every_workflow_parses_as_yaml(name):
    data = _workflow_yaml(name)
    assert _triggers(data)
    for job in data["jobs"].values():
        assert job["runs-on"] == "ubuntu-latest" and job["steps"]


def test_this_repository_s_workflow_copies_match_the_template():
    """The installed copies differ from the template only by the framework repository."""
    for name in ALL_WORKFLOWS:
        if name == EVALS_WORKFLOW:
            # this repository runs framework-evals.yml (its own suite over the fixture) and
            # has no evals/check.py: the per-project workflow is not installed here
            assert not (REPO_WORKFLOW_DIR / name).exists()
            assert (REPO_WORKFLOW_DIR / "framework-evals.yml").is_file()
            continue
        installed = (REPO_WORKFLOW_DIR / name).read_text(encoding="utf-8")
        assert installed == render.render_file(WORKFLOW_DIR / name, VALUES), name


@pytest.mark.parametrize(
    "path",
    [*(WORKFLOW_DIR / n for n in ALL_WORKFLOWS), *sorted(REPO_WORKFLOW_DIR.glob("*.yml"))],
    ids=lambda p: f"{p.parent.parent.parent.name}/{p.name}",
)
def test_every_workflow_uses_checkout_and_setup_node_v5(path):
    """HANDOFF 4(c): the v4 actions run on Node 20, which GitHub deprecates."""
    text = path.read_text(encoding="utf-8")
    uses = [ln.split("uses:", 1)[1].strip() for ln in text.splitlines() if "uses:" in ln]
    assert uses, path
    for action in uses:
        if action.startswith(("actions/checkout@", "actions/setup-node@")):
            assert action.endswith("@v5"), f"{path.name}: {action}"


def test_release_workflow_runs_the_release_cli_on_merge_and_label():
    data = _workflow_yaml(RELEASE_WORKFLOW)
    on = _triggers(data)
    assert on["pull_request"]["types"] == ["closed", "labeled"]
    assert on["pull_request"]["branches"] == ["main"]  # /sdlc-init rewrites it
    assert on["workflow_dispatch"]["inputs"]["pr_number"]["required"] is True
    # read-only: the release runs the project's own deploy.command, it writes nothing
    assert set(data["permissions"].values()) == {"read"}
    assert {"contents", "pull-requests"} <= set(data["permissions"])
    assert data["concurrency"]["group"] == (
        "sdlc-release-${{ github.event.pull_request.number || inputs.pr_number }}"
    )
    job = data["jobs"]["release"]
    assert "github.event_name == 'workflow_dispatch'" in job["if"]
    assert "github.event.pull_request.merged == true" in job["if"]
    assert "github.event.label.name == 'sdlc:release-approved'" in job["if"]
    runs = [step["run"] for step in job["steps"] if "run" in step]
    assert runs[-1] == (
        'python framework/plugin/release/cli.py run --root . --repo "$REPO" --pr "$PR_NUMBER" '
        '--event "$EVENT_ACTION" --merge-sha "$MERGE_SHA"'
    )
    # I7: the documented `python -m build && twine upload dist/*` needs the project's own
    # tools on a bare runner, installed right before the release step
    assert runs[-2] == "python framework/plugin/ci/project_setup.py --root ."
    assert job["steps"][-2]["name"] == (
        "Install the project's own toolchain (sdlc.yaml: commands.setup)"
    )
    env = job["steps"][-1]["env"]
    assert set(env) == {"GITHUB_TOKEN", "REPO", "PR_NUMBER", "EVENT_ACTION", "MERGE_SHA"}
    # not a phase run: no model, no CLI install, no runner setup
    text = (WORKFLOW_DIR / RELEASE_WORKFLOW).read_text(encoding="utf-8")
    for absent in ("claude-code@", "run_phase.py", "runner_setup.py", "setup-node", "secrets."):
        assert absent not in text, absent
    assert "# environment: production" in text  # the owner's opt-in to environment rules
    assert "environment" not in job


@pytest.mark.parametrize("name", ("sdlc-design.yml", "sdlc-build.yml"))
def test_merge_fired_jobs_find_the_change_instead_of_filtering_the_head(name):
    """HANDOFF 4(a): any merge into the default branch starts the job; the find step names
    the change, and every later step waits for it."""
    job = next(iter(_workflow_yaml(name)["jobs"].values()))
    assert "startsWith" not in job["if"] and "sdlc/" not in job["if"]
    names = [step.get("id") or step.get("name") or step.get("uses") for step in job["steps"]]
    find = names.index("find")
    assert job["steps"][find - 1]["with"]["path"] == "framework"
    assert "--find-change" in job["steps"][find]["run"]
    for step in job["steps"][find + 1 :]:
        assert step["if"] == "steps.find.outputs.change_id != ''", step
    phase_step = [step for step in job["steps"] if "run" in step][-1]
    assert phase_step["env"]["CHANGE_ID"] == "${{ steps.find.outputs.change_id }}"
    # step 41.1: the hook log rides as an artifact after the run, gated like every step
    assert job["steps"][-1]["name"] == "Keep the hook log"
    assert "changes/**/evidence/hook-log.jsonl" in job["steps"][-1]["with"]["path"]


def test_fix_workflow_starts_on_request_changes_and_on_the_owner_labels():
    """Decision 22: the owner's "Request changes" review submission starts the fix round on
    the PR's own head; decision 24: so does one of the three un-park labels. The workflow
    token's own review or label never does (a [bot] reviewer is refused besides)."""
    data = _workflow_yaml(FIX_WORKFLOW)
    on = _triggers(data)
    assert on["pull_request_review"]["types"] == ["submitted"]
    assert on["pull_request"]["types"] == ["labeled"]
    assert "branches" not in on["pull_request"]  # any base: the PR's head is what matters
    assert on["workflow_dispatch"]["inputs"]["change_id"]["required"] is True
    job = data["jobs"]["fix"]
    assert "github.event.review.state == 'changes_requested'" in job["if"]
    assert "!endsWith(github.event.review.user.login, '[bot]')" in job["if"]
    for label in ("sdlc:accept-risk", "sdlc:reset-iterations", "sdlc:unlock-tests"):
        assert f"github.event.label.name == '{label}'" in job["if"], label
    assert "sdlc:c-approved" not in job["if"] and "sdlc:d-approved" not in job["if"]
    # the checkout is the PR's head, never the review event's merge ref
    checkout = job["steps"][0]
    assert checkout["with"]["ref"] == (
        "${{ inputs.head_ref || github.event.pull_request.head.ref || github.ref }}"
    )
    runs = [step["run"] for step in job["steps"] if "run" in step]
    assert runs[-1] == (
        "python framework/plugin/ci/run_phase.py --root . --plugin-dir framework --phase fix "
        '--id "$CHANGE_ID" --head-ref "$HEAD_REF" --repo "$REPO" --pr-number "$PR_NUMBER" '
        '--ref "$DEFAULT_BRANCH"'
    )
    find = next(step for step in job["steps"] if step.get("id") == "find")
    assert "--phase fix" in find["run"] and "--find-change" in find["run"]
    phase_step = [step for step in job["steps"] if "run" in step][-1]
    assert phase_step["env"]["PR_NUMBER"] == "${{ github.event.pull_request.number }}"
    assert job["steps"][-1]["name"] == "Keep the hook log"  # step 41.1
    assert data["concurrency"]["group"] == (
        "sdlc-${{ inputs.head_ref || github.event.pull_request.head.ref }}"
    )


def test_abandon_workflow_records_the_end_state_without_a_model():
    """Decision 25: a PR closed without a merge abandons its change on every branch of the
    change; not a phase run (no claude, no model credential, contents: write only)."""
    data = _workflow_yaml(ABANDON_WORKFLOW)
    on = _triggers(data)
    assert on == {"pull_request": {"types": ["closed"]}}
    # pull-requests: write since 0.2.19: the dismissal of gate (f) opens a pull request
    assert data["permissions"] == {"contents": "write", "pull-requests": "write"}
    job = data["jobs"]["abandon"]
    assert job["if"] == "${{ github.event.pull_request.merged == false }}"
    assert job["steps"][0]["with"]["ref"] == "${{ github.event.pull_request.head.ref }}"
    runs = [step["run"] for step in job["steps"] if "run" in step]
    assert runs[-2] == (
        'python framework/plugin/state/cli.py abandon --root . --id "$CHANGE_ID" '
        '--reason "pull request $PR_NUMBER closed without a merge" --push --all-branches'
    )
    # decision 25, second half (step 39): the close of an incident PR dismisses its finding
    # with the closing comment as the reason, through a dismissal PR
    assert runs[-1] == (
        'python framework/plugin/detect/cli.py dismiss --root . --id "$CHANGE_ID" '
        '--repo "$REPO" --pr-number "$PR_NUMBER" --open-pr'
    )
    for step in job["steps"][-2:]:
        assert step["if"] == "steps.find.outputs.change_id != ''"
    assert job["steps"][-1]["env"]["SDLC_DEFAULT_BRANCH"] == DEFAULT_BRANCH_EXPR
    text = (WORKFLOW_DIR / ABANDON_WORKFLOW).read_text(encoding="utf-8")
    for absent in ("claude-code@", "runner_setup.py", "setup-node", "secrets.", "--phase b"):
        assert absent not in text, absent


@pytest.mark.parametrize("name", [*PHASE_WORKFLOWS, FIX_WORKFLOW, DETECT_WORKFLOW])
def test_every_phase_run_keeps_the_hook_log_as_an_artifact(name):
    """Build guide step 41.1 (article p.39: every hook decision logged with a timestamp and
    a verdict): the log rides with the evidence and as a run artifact."""
    job = next(iter(_workflow_yaml(name)["jobs"].values()))
    step = job["steps"][-1]
    assert step["name"] == "Keep the hook log" and step["uses"].startswith(
        "actions/upload-artifact@"
    )
    assert step["with"]["if-no-files-found"] == "ignore"
    assert "changes/.hook-log.jsonl" in step["with"]["path"]


def test_detect_workflow_is_scheduled_deterministic_and_runs_the_diagnosis_only_when_filed():
    """Build guide step 37 (article p.43-44): the detection script runs on a schedule with no
    model, keeps its log as an artifact, and the diagnosis (a claude run) starts only when a
    change was filed; workflow_dispatch's force_tier rehearses the loop."""
    data = _workflow_yaml(DETECT_WORKFLOW)
    on = _triggers(data)
    assert "schedule" in on and on["schedule"][0]["cron"].split()[0] != "0"
    assert on["workflow_dispatch"]["inputs"]["force_tier"]["options"] == ["", "2", "3"]
    assert data["permissions"]["contents"] == "write"
    assert data["permissions"]["actions"] == "read"  # the runs API, nothing dispatched
    job = data["jobs"]["detect"]
    steps = {s.get("name") or s.get("uses"): s for s in job["steps"]}
    detect = steps["Detect"]
    assert detect["id"] == "detect"
    assert "secrets." not in json.dumps(detect)  # no model credential in the detection
    assert detect["run"] == (
        'python framework/plugin/detect/cli.py run --root . --repo "$REPO" '
        "--cache .sdlc/detect-cache.json --log detect-log.jsonl "
        '--force-tier "$FORCE_TIER" --file'
    )
    log = steps["Keep the detection log"]
    assert log["uses"].startswith("actions/upload-artifact@") and log["if"] == "${{ always() }}"
    phase = steps["Run phase (f)"]
    assert phase["if"] == "steps.detect.outputs.change_id != ''"
    # the dispatcher is its own step after the model's (decisions 11 and 14): no model
    # credential there, and the runbook secrets never where the model runs
    finish = steps["Dispatch the route, run gate (f) and open the intent PR"]
    assert finish["if"] == "steps.detect.outputs.change_id != ''"
    assert finish["run"] == (
        'python framework/plugin/detect/cli.py finish --root . --id "$CHANGE_ID" --repo "$REPO"'
    )
    assert "secrets." not in json.dumps(finish) and "secrets." in json.dumps(phase)
    for step in (detect, finish):
        assert step["env"]["SDLC_DEFAULT_BRANCH"] == DEFAULT_BRANCH_EXPR
    assert '--force-tier "$FORCE_TIER"' in detect["run"]
    assert "--phase f" in phase["run"] and "HEAD_REF: ${{ steps.detect.outputs.head_ref }}" in (
        (WORKFLOW_DIR / DETECT_WORKFLOW).read_text(encoding="utf-8")
    )
    installs = (
        "Install the pinned Claude Code CLI",
        "Prepare the runner for Claude Code's sandbox",
    )
    for name in installs:
        assert steps[name]["if"] == "steps.detect.outputs.change_id != ''"


def test_evals_workflow_runs_on_configuration_changes_and_nightly():
    """Build guide step 35 (article p.30 step 3: "on any change to CLAUDE.md, skills or
    hooks" and on a schedule; step 4: the pass rate gates the change)."""
    data = _workflow_yaml(EVALS_WORKFLOW)
    on = _triggers(data)
    assert on["pull_request"]["paths"] == ["CLAUDE.md", ".claude/**", "evals/**"]
    assert on["pull_request"]["branches"] == ["main"] and "schedule" in on
    assert data["permissions"] == {"contents": "read"}
    job = data["jobs"]["evals"]
    runs = [step["run"] for step in job["steps"] if "run" in step]
    assert runs[-1] == "python evals/check.py --framework framework --report evals-report.json"
    assert all("--bare" not in run and "run_phase.py" not in run for run in runs)
    assert job["steps"][-1]["name"] == "Keep the report"


def test_scan_workflow_is_weekly_reviews_routes_and_scans_in_that_order():
    """Build guide step 38 (decision 16; article p.46-48): a weekly read-only review, its
    findings routed through gate (f), then the deterministic scanners, reported and never a
    gate; every run line is python (the framework's rule for unattended jobs)."""
    data = _workflow_yaml(SCAN_WORKFLOW)
    on = _triggers(data)
    assert (
        len(on["schedule"][0]["cron"].split()) == 5 and on["schedule"][0]["cron"].split()[4] != "*"
    )
    assert "workflow_dispatch" in on
    job = next(iter(data["jobs"].values()))
    runs = [step["run"] for step in job["steps"] if "run" in step]
    assert all(run.startswith("python ") or run.startswith("npm ") for run in runs), runs
    assert all("${{" not in run for run in runs)
    review = next(run for run in runs if "scan/cli.py review" in run)
    route = next(run for run in runs if "scan/cli.py route" in run)
    scanners = next(run for run in runs if "scan/cli.py scanners" in run)
    assert runs.index(review) < runs.index(route) < runs.index(scanners)
    assert "--max-findings 3" in route
    [route_step] = [s for s in job["steps"] if "scan/cli.py route" in s.get("run", "")]
    assert route_step["env"]["SDLC_DEFAULT_BRANCH"] == DEFAULT_BRANCH_EXPR
    text = (WORKFLOW_DIR / SCAN_WORKFLOW).read_text(encoding="utf-8")
    assert "upload-artifact@" in text and "Bash(git *)" not in text  # the tools live in the CLI


def test_runbook_workflow_runs_the_go_once_without_a_model():
    """Decisions 14 and 26: the owner's sdlc:go on the incident PR runs the proposed runbook;
    a person must have applied it (detect/cli.py go reads the actor), no claude starts."""
    data = _workflow_yaml(RUNBOOK_WORKFLOW)
    assert _triggers(data) == {"pull_request": {"types": ["labeled"]}}
    job = data["jobs"]["go"]
    assert job["if"] == "${{ github.event.label.name == 'sdlc:go' }}"
    assert job["steps"][0]["with"]["ref"] == "${{ github.event.pull_request.head.ref }}"
    runs = [step["run"] for step in job["steps"] if "run" in step]
    assert runs[-1] == (
        'python framework/plugin/detect/cli.py go --root . --id "$CHANGE_ID" '
        '--repo "$REPO" --pr-number "$PR_NUMBER"'
    )
    go = [step for step in job["steps"] if "run" in step][-1]
    assert go["env"]["SDLC_DEFAULT_BRANCH"] == DEFAULT_BRANCH_EXPR
    text = (WORKFLOW_DIR / RUNBOOK_WORKFLOW).read_text(encoding="utf-8")
    for absent in ("claude-code@", "runner_setup.py", "setup-node", "secrets.", "--phase f "):
        assert absent not in text, absent


def test_pin_script_is_installed_and_reads_the_template_pin(tmp_path):
    script = TEMPLATE / ".github" / "scripts" / "sdlc_pin.py"
    assert script.is_file()
    rendered = render.render_file(TEMPLATE / "sdlc.yaml", VALUES)
    (tmp_path / "sdlc.yaml").write_text(rendered, encoding="utf-8")
    import subprocess
    import sys

    proc = subprocess.run(
        [sys.executable, str(script), "--root", str(tmp_path)],
        capture_output=True,
        text=True,
        check=True,
    )
    assert f"ref=v{VALUES['PLUGIN_VERSION']}" in proc.stdout
    assert f"claude_code={VALUES['CLAUDE_CODE_VERSION']}" in proc.stdout


def _pin(tmp_path: Path, plugin_block: str):
    import subprocess
    import sys

    script = TEMPLATE / ".github" / "scripts" / "sdlc_pin.py"
    (tmp_path / "sdlc.yaml").write_text(plugin_block, encoding="utf-8")
    return subprocess.run(
        [sys.executable, str(script), "--root", str(tmp_path)],
        capture_output=True,
        text=True,
    )


def test_pin_script_reads_the_default_branch_s_pin_not_the_head_s(tmp_path):
    """0.2.17: the workflows pass ``--ref origin/<default>``; a phase branch that started
    under an older pin runs the framework the project has today (the first overturn rounds
    on the sample repository ran 0.2.14 on a branch while main pinned 0.2.16)."""
    import subprocess
    import sys

    script = TEMPLATE / ".github" / "scripts" / "sdlc_pin.py"
    bare = tmp_path / "bare.git"
    subprocess.run(["git", "init", "-q", "--bare", str(bare)], check=True)
    work = tmp_path / "work"
    subprocess.run(["git", "init", "-q", "-b", "main", str(work)], check=True)

    def git(*args):
        return subprocess.run(
            ["git", *args], cwd=work, check=True, capture_output=True, text=True
        ).stdout

    git("config", "user.email", "owner@example.com")
    git("config", "user.name", "Owner")
    (work / "sdlc.yaml").write_text("plugin:\n  version: 0.2.14\n", encoding="utf-8")
    git("add", ".")
    git("commit", "-q", "-m", "pin 0.2.14")
    git("checkout", "-q", "-b", "sdlc/0001/b")  # the phase branch keeps the old pin
    git("checkout", "-q", "main")
    (work / "sdlc.yaml").write_text("plugin:\n  version: 0.2.16\n", encoding="utf-8")
    git("commit", "-q", "-am", "pin 0.2.16")
    git("remote", "add", "origin", str(bare))
    git("push", "-q", "-u", "origin", "main")
    git("checkout", "-q", "sdlc/0001/b")

    def pin(*extra):
        return subprocess.run(
            [sys.executable, str(script), "--root", str(work), *extra],
            capture_output=True, text=True,
        )  # fmt: skip

    assert "ref=v0.2.14" in pin().stdout  # the head's copy: what 0.2.16 and before read
    proc = pin("--ref", "origin/main")
    assert proc.returncode == 0, proc.stderr
    assert "ref=v0.2.16" in proc.stdout and "claude_code=" in proc.stdout
    # a ref the checkout lacks is fetched from origin
    git("update-ref", "-d", "refs/remotes/origin/main")
    proc = pin("--ref", "origin/main")
    assert proc.returncode == 0, proc.stderr
    assert "ref=v0.2.16" in proc.stdout
    proc = pin("--ref", "origin/nowhere")
    assert proc.returncode == 1 and "cannot read sdlc.yaml at origin/nowhere" in proc.stderr


def test_pin_script_does_not_double_the_v_of_a_version(tmp_path):
    proc = _pin(tmp_path, 'plugin:\n  version: "v1.4.0"\n  claude_code: "2.1.278"\n')
    assert proc.returncode == 0, proc.stderr
    assert "ref=v1.4.0" in proc.stdout and "ref=vv" not in proc.stdout


def test_pin_script_refuses_a_claude_code_that_is_not_a_version(tmp_path):
    """The value is interpolated into the install step's shell command."""
    proc = _pin(tmp_path, 'plugin:\n  version: "1.4.0"\n  claude_code: "2.1.1; rm -rf /"\n')
    assert proc.returncode == 2
    assert "not a version string" in proc.stderr
    ok = _pin(tmp_path, 'plugin:\n  version: "1.4.0"\n  claude_code: "latest"\n')
    assert ok.returncode == 0 and "claude_code=latest" in ok.stdout
