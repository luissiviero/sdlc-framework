"""Template files: structure required by the handoff, placeholders resolvable, valid JSON/YAML."""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from gate import limits
from init import render
from state import yamlish

TEMPLATE = Path(__file__).resolve().parents[1] / "template"

VALUES = {
    "PROJECT_NAME": "demo",
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
    # decision 35: what /sdlc-init renders for a project with no folder a default glob matches
    "RISK_LIST": '  - "auth"\n  - "data migrations"\n  - "money movement"\n  - "production config"',
    "FRAMEWORK_REPO": "luissiviero/sdlc-framework",
    "CLAUDE_CODE_VERSION": "2.1.304",
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


def test_review_md_skip_marker_rule_present():
    text = (TEMPLATE / "REVIEW.md").read_text(encoding="utf-8")
    assert "ratchets" in text and "details.skip_markers" in text
    assert "gate (e)" in text
    # rules added by the guide (step 26 notes; step 7 (iv); step 25; step 12)
    flat = " ".join(text.split())
    assert ".claude/**" in flat and "must not modify test files" in flat and "plan.md" in flat


def test_sdlc_yaml_renders_to_documented_keys():
    data = yamlish.loads(render.render_file(TEMPLATE / "sdlc.yaml", VALUES))
    # decision 37 (1.0.21): one profile and one review mode, so neither key is written
    assert "profile" not in data and "review" not in data
    # R7: the session's, the reviewer's and the devil's advocate's models (the advocate on
    # another model than the session)
    assert data["panel_advocate_model"] == "claude-fable-5-1"
    assert data["session_model"] == "claude-opus-5-5"
    assert data["adversarial_model"] == "claude-opus-5-5"
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
    # decision 35: a plain item, or {item, paths} where /sdlc-init found a matching folder
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


def test_sdlc_yaml_carries_decision_32_s_defaults():
    """Decision 32 (1.0.8), as decision 37 narrowed it: deferred review is the only mode and
    the template says so with no key to set; the build run and every fix round have their own
    caps, named explicitly, and the per-change budget cap is 150 USD; NOTES 45 gap 5."""
    from init import sdlc_init

    # an older command line still parses: the two retired options are accepted and ignored
    assert sdlc_init.build_parser().parse_args(["--profile", "full", "--review", "parked"])
    text = render.render_file(TEMPLATE / "sdlc.yaml", VALUES)
    block = text.split("# --- the gates and judgment calls", 1)[1].split("# --- models", 1)[0]
    assert "decision 37" in block and "goes to a review panel" in block
    assert "\nreview:" not in text and "\nprofile:" not in text
    gate = yamlish.loads(text)["gate"]
    assert gate["max_turns"] == 200 and gate["max_wall_clock_minutes"] == 120
    assert gate["build_max_turns"] == 400 and gate["build_max_wall_clock_minutes"] == 180
    assert gate["max_budget_usd"] == 150
    assert limits.run_caps(gate, True) == (400, 180) and limits.run_caps(gate, False) == (200, 120)
    for name in ALL_WORKFLOWS:
        text = (WORKFLOW_DIR / name).read_text(encoding="utf-8")
        text = text.split("\n  second-opinion:")[0]  # R8's job after the phase job: 20 minutes
        minutes = re.findall(r"(?m)^    timeout-minutes: (\d+)$", text)
        if name in ("sdlc-build.yml", FIX_WORKFLOW):
            assert minutes == ["260"], name  # 180 + 5 of grace, the commands step and the judge
        elif name in ("sdlc-design.yml", "sdlc-test.yml"):
            assert minutes == ["200"], name
        elif name == "sdlc-deploy.yml":  # R25 part 1: the review pass's 125 and phase (e)'s 185
            assert minutes == ["330"], name


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
COMMENT_WORKFLOW = "sdlc-comment.yml"  # the owner's @claude comment (decision 34, R17)
MERGE_WORKFLOW = "sdlc-merge.yml"  # gate (e) is the owner's approval (decision 36, R22)
ALL_WORKFLOWS = (
    *PHASE_WORKFLOWS,
    "sdlc-digest.yml",
    RELEASE_WORKFLOW,
    FIX_WORKFLOW,
    COMMENT_WORKFLOW,
    ABANDON_WORKFLOW,
    DETECT_WORKFLOW,
    RUNBOOK_WORKFLOW,
    EVALS_WORKFLOW,
    SCAN_WORKFLOW,
    MERGE_WORKFLOW,
)
# this repository's own installed copies (PR #21) and its substrate smoke test
REPO_WORKFLOW_DIR = TEMPLATE.parent / ".github" / "workflows"
# the explicit default branch a detect/scan CLI step reads before its git guess (live run of
# 2026-09-25: a checkout of a non-default ref has no origin/HEAD and no local main)
DEFAULT_BRANCH_EXPR = "${{ github.event.repository.default_branch }}"
# the pin step (0.2.24): the default branch's copy of the pin script, piped into python,
# reading the pin at the fully qualified remote-tracking ref (tests/test_ci.py checks it in
# every workflow; this is its body as YAML parses it)
PIN_RUN = (
    'git show "refs/remotes/origin/$SDLC_DEFAULT_BRANCH:.github/scripts/sdlc_pin.py" '
    '| python - --ref "refs/remotes/origin/$SDLC_DEFAULT_BRANCH"'
)


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
        if name == MERGE_WORKFLOW:
            # R22 (decision 36): plugin/ci/merge_step.py is not in the framework this
            # repository's sdlc.yaml pins, and this repository has no merge App yet: the copy
            # is installed with the pin, as the comment workflow's was
            assert not (REPO_WORKFLOW_DIR / name).exists()
            continue
        if name == COMMENT_WORKFLOW:
            # R17 (decision 34): the dispatcher calls plugin/ci/comment_dispatch.py, which the
            # framework this repository's sdlc.yaml pins does not ship, and framework changes
            # are not run through the pipeline here: the copy is installed with the pin
            assert not (REPO_WORKFLOW_DIR / name).exists()
            continue
        installed = (REPO_WORKFLOW_DIR / name).read_text(encoding="utf-8")
        assert installed == render.render_file(WORKFLOW_DIR / name, VALUES), name


FRAMEWORK_CHECKS = "framework-checks.yml"  # this repository's own suite (0.2.28)


def test_this_repository_runs_its_own_checks_on_linux_and_windows():
    """The 1.0.0 readiness review, group C: no CI job ran this repository's pytest or ruff,
    and the Windows-only code last ran under 657 tests (the owner's PC, session 4). The
    workflow is not a template: it runs `python tasks.py verify` (choice 253: the build, lint,
    docs lint and test commands a session runs, since R65's part 4) on both platforms on every
    pull request and every push to main, with python on every run line (CLAUDE.md)."""
    yaml = pytest.importorskip("yaml")
    text = (REPO_WORKFLOW_DIR / FRAMEWORK_CHECKS).read_text(encoding="utf-8")
    data = yaml.safe_load(text)
    on = _triggers(data)
    assert on["pull_request"]["branches"] == ["main"]
    assert on["push"]["branches"] == ["main"]
    assert "workflow_dispatch" in on
    assert data["permissions"] == {"contents": "read"}
    assert list(data["jobs"]) == ["platforms", "check", "check-windows-shard", "check-windows"]
    job = data["jobs"]["check"]
    windows = data["jobs"]["check-windows-shard"]
    jobs = {(entry["os"], entry["python"]) for entry in job["strategy"]["matrix"]["include"]}
    python = windows["steps"][1]["with"]["python-version"]
    jobs.add((windows["runs-on"], python))
    # both platforms on one interpreter, plus the oldest Python pyproject supports
    assert jobs == {
        ("ubuntu-latest", "3.12"),
        ("windows-latest", "3.12"),
        ("ubuntu-latest", "3.10"),
    }
    assert data["jobs"]["check-windows"]["name"] == "check (windows-latest, 3.12)"  # old name
    assert job["strategy"]["fail-fast"] is False
    assert job["runs-on"] == "${{ matrix.os }}"
    for each in (job, windows):
        assert each["timeout-minutes"] >= 30  # the Windows run of 657 tests took 17.5 minutes
        steps = each["steps"]
        uses = [step["uses"] for step in steps if "uses" in step]
        assert uses[0].startswith("actions/checkout@")
        setup = [s for s in steps if s.get("uses", "").startswith("actions/setup-python@")]
        assert len(setup) == 1
        assert all("${{" not in step.get("run", "") for step in steps)  # never in a run line
        runs = [step["run"] for step in steps if "run" in step]
        assert runs == [
            "python .github/scripts/framework_checks_runner.py",  # choice 235: speed only
            'python -m pip install -e ".[dev]"',
            "python tasks.py verify",
        ]
    assert job["steps"][1]["with"]["python-version"] == "${{ matrix.python }}"
    shard = {"FRAMEWORK_TEST_SHARD": "${{ matrix.shard }}/3"}
    assert windows["steps"] == [
        {**s, "with": {"python-version": "3.12"}}
        if "setup-python" in s.get("uses", "")
        else {**s, "env": shard}
        if s.get("run") == "python tasks.py verify"
        else s
        for s in job["steps"]
    ]
    assert not (WORKFLOW_DIR / FRAMEWORK_CHECKS).exists()  # not installed into projects
    assert FRAMEWORK_CHECKS not in ALL_WORKFLOWS


def test_main_runs_of_this_repository_s_checks_are_never_cancelled():
    """The batch ci revision, 10.1: a merge cancelled the run of the merge before it, so the
    suite never finished on the commit v0.3.6 names (run #279). A pull request's runs are
    keyed by its number and cancel each other; every other run is keyed by its commit and
    never cancelled, so a third merge cannot replace the second's pending run either."""
    yaml = pytest.importorskip("yaml")
    data = yaml.safe_load((REPO_WORKFLOW_DIR / FRAMEWORK_CHECKS).read_text(encoding="utf-8"))
    assert data["concurrency"] == {
        "group": "framework-checks-${{ github.event.pull_request.number || github.sha }}",
        "cancel-in-progress": "${{ github.event_name == 'pull_request' }}",
    }


def test_the_windows_job_is_skipped_only_on_a_documentation_only_pull_request():
    """The batch ci revision, 10.2: Windows is the whole wait of a pull request, and half the
    merges touch only documentation. The platforms job runs the selector; the Windows job is
    a job of its own whose `if:` reads it, so a skip reports the check as skipped. It runs on
    every other event, and when the pick failed (an empty output is never 'false'). The
    Linux jobs wait for nothing."""
    yaml = pytest.importorskip("yaml")
    data = yaml.safe_load((REPO_WORKFLOW_DIR / FRAMEWORK_CHECKS).read_text(encoding="utf-8"))
    pick = data["jobs"]["platforms"]
    assert pick["runs-on"] == "ubuntu-latest"
    assert pick["outputs"] == {"windows": "${{ steps.pick.outputs.windows }}"}
    assert pick["steps"][0]["with"]["fetch-depth"] == 2  # the merge commit and its parents
    step = pick["steps"][-1]
    assert step["id"] == "pick"
    assert step["run"] == "python3 .github/scripts/framework_checks_windows.py"
    assert (REPO_WORKFLOW_DIR.parent / "scripts" / "framework_checks_windows.py").is_file()
    runs_windows = (
        "${{ !cancelled() && (github.event_name != 'pull_request' || "
        "needs.platforms.outputs.windows != 'false') }}"
    )
    shards = data["jobs"]["check-windows-shard"]
    assert shards["needs"] == "platforms"
    assert shards["if"] == runs_windows
    verdict = data["jobs"]["check-windows"]
    assert verdict["needs"] == ["platforms", "check-windows-shard"]
    assert verdict["if"] == runs_windows
    assert "needs" not in data["jobs"]["check"] and "if" not in data["jobs"]["check"]


def test_the_windows_suite_runs_in_shards_and_its_check_is_their_verdict():
    """2026-10-19: the one Windows job took 20-23 minutes against 3 on Linux. Three shards run
    on parallel runners, each `python tasks.py verify` with its FRAMEWORK_TEST_SHARD (every
    test in exactly one shard: tests/test_scaffold.py), none cancelling the others; the check
    named as the Windows job always was is green only when every shard is."""
    yaml = pytest.importorskip("yaml")
    data = yaml.safe_load((REPO_WORKFLOW_DIR / FRAMEWORK_CHECKS).read_text(encoding="utf-8"))
    shards = data["jobs"]["check-windows-shard"]
    assert shards["runs-on"] == "windows-latest"
    assert shards["strategy"] == {"fail-fast": False, "matrix": {"shard": [1, 2, 3]}}
    count = len(shards["strategy"]["matrix"]["shard"])
    assert shards["name"] == f"check (windows-latest, 3.12, shard ${{{{ matrix.shard }}}}/{count})"
    (step,) = [s for s in shards["steps"] if s.get("run") == "python tasks.py verify"]
    assert step["env"] == {"FRAMEWORK_TEST_SHARD": f"${{{{ matrix.shard }}}}/{count}"}
    verdict = data["jobs"]["check-windows"]
    (only,) = verdict["steps"]
    assert only["env"] == {"SHARDS": "${{ needs.check-windows-shard.result }}"}
    assert only["run"].startswith("python3 -c ") and "${{" not in only["run"]
    assert "sys.exit(r != 'success')" in only["run"]


def test_a_superseded_pull_request_run_of_the_framework_evals_is_cancelled():
    """The batch ci revision, 10.8: keyed by head ref with no cancelling, three pushes to a
    plugin pull request ran the paid suite three times in a row, two of them on heads nobody
    merges. A pull request's runs are keyed by its number and cancel each other; the nightly
    and dispatched runs are keyed by their commit and never cancelled."""
    yaml = pytest.importorskip("yaml")
    text = (REPO_WORKFLOW_DIR / "framework-evals.yml").read_text(encoding="utf-8")
    data = yaml.safe_load(text)
    assert "schedule" in _triggers(data)
    assert data["concurrency"] == {
        "group": "framework-evals-${{ github.event.pull_request.number || github.sha }}",
        "cancel-in-progress": "${{ github.event_name == 'pull_request' }}",
    }


def test_the_framework_evals_prepare_the_runner_s_sandbox_before_the_suite():
    """ROADMAP R44, point 1 (the owner's item 15 on PR #144): the fixture runs sandboxed as a
    CI session does, so case 0006 proves denyWrite on a runner. The phase jobs' setup step
    runs from this checkout's plugin/ (the framework is the repository, not framework/)."""
    yaml = pytest.importorskip("yaml")
    text = (REPO_WORKFLOW_DIR / "framework-evals.yml").read_text(encoding="utf-8")
    steps = yaml.safe_load(text)["jobs"]["evals"]["steps"]
    runs = [s.get("run", "") for s in steps]
    setup = next(i for i, r in enumerate(runs) if r == "python plugin/ci/runner_setup.py")
    suite = next(i for i, r in enumerate(runs) if r.startswith("python plugin/evals/run.py "))
    assert setup < suite
    assert steps[setup]["name"] == "Prepare the runner for Claude Code's sandbox"
    assert "if" not in steps[setup]  # every run of the suite is sandboxed, not only some
    assert "framework/plugin" not in text


@pytest.mark.parametrize(
    "path",
    [*(WORKFLOW_DIR / n for n in ALL_WORKFLOWS), *sorted(REPO_WORKFLOW_DIR.glob("*.yml"))],
    ids=lambda p: f"{p.parent.parent.parent.name}/{p.name}",
)
def test_every_workflow_uses_checkout_and_setup_node_v5(path):
    """HANDOFF 4(c): the v4 actions run on Node 20, which GitHub deprecates. A pin by commit
    SHA (the merge job, choice 250) names its v5 tag in the line's comment."""
    text = path.read_text(encoding="utf-8")
    uses = [ln.split("uses:", 1)[1].strip() for ln in text.splitlines() if "uses:" in ln]
    assert uses, path
    for action in uses:
        if action.startswith(("actions/checkout@", "actions/setup-node@")):
            pinned = re.fullmatch(r"\S+@[0-9a-f]{40} # (v5[.\d]*)", action)
            assert action.endswith("@v5") or pinned, f"{path.name}: {action}"


def test_the_digest_reads_the_merge_environment_and_never_the_key():
    """Choice 250 (the R22 double check, F8): the digest reads the sdlc-merge environment
    (``actions: read``) and learns only whether the merge key is a repository secret."""
    data = _workflow_yaml("sdlc-digest.yml")
    assert data["permissions"]["actions"] == "read"
    post = next(s for s in data["jobs"]["digest"]["steps"] if s.get("name") == "Post the digest")
    flag = "${{ secrets.SDLC_MERGE_APP_PRIVATE_KEY != '' }}"
    assert post["env"]["SDLC_MERGE_KEY_IN_REPOSITORY"] == flag
    text = (WORKFLOW_DIR / "sdlc-digest.yml").read_text(encoding="utf-8")
    assert text.count("SDLC_MERGE_APP_PRIVATE_KEY") == 1


def test_release_workflow_runs_the_release_cli_on_merge_and_label():
    data = _workflow_yaml(RELEASE_WORKFLOW)
    on = _triggers(data)
    assert on["pull_request"]["types"] == ["closed", "labeled"]
    assert on["pull_request"]["branches"] == ["main"]  # /sdlc-init rewrites it
    assert on["workflow_dispatch"]["inputs"]["pr_number"]["required"] is True
    # read-only for the release job: the project's own toolchain and deploy.command run there
    # and must not be able to push (the review of the 0.3.1 diff, finding 4)
    assert data["permissions"] == {"contents": "read", "pull-requests": "read", "issues": "read"}
    assert "permissions" not in data["jobs"]["release"]
    # R51: one release at a time in the repository, so two deploy.command runs never overlap
    assert data["concurrency"] == {"group": "sdlc-release", "cancel-in-progress": False}
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
    assert job["steps"][-1]["id"] == "release"  # its outputs feed the record job
    assert job["outputs"] == {
        "released": "${{ steps.release.outputs.released }}",
        "change_id": "${{ steps.release.outputs.change_id }}",
        "pin": "${{ steps.pin.outputs.ref }}",
        # decision 35: the (e) merge's risk acceptance, stored by the record job
        "risk_acceptance": "${{ steps.release.outputs.risk_acceptance }}",
    }
    # the record job (0.3.1, issue #66): the only write token, the framework's step only;
    # since 1.0.15 it also runs to store the merge's risk acceptance (decision 35)
    record = data["jobs"]["record"]
    assert record["needs"] == "release"
    assert record["if"] == (
        "${{ !cancelled() && (needs.release.outputs.released == 'true' || "
        "needs.release.outputs.risk_acceptance != '') }}"
    )
    assert record["permissions"] == {"contents": "write"}
    assert [step.get("uses", step.get("run", "")).split(" ")[0] for step in record["steps"]] == [
        "actions/checkout@v5",
        "actions/checkout@v5",
        "python",
    ]
    assert record["steps"][1]["with"]["ref"] == "${{ needs.release.outputs.pin }}"
    assert record["steps"][-1]["run"] == (
        'python framework/plugin/release/cli.py record --root . --id "$CHANGE_ID" '
        '--pr "$PR_NUMBER" --merge-sha "$MERGE_SHA" --released "$RELEASED" '
        '--acceptance "$RISK_ACCEPTANCE"'
    )
    assert "project_setup" not in str(record) and "deploy" not in str(record["steps"])
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
    the PR's own head; decision 24: so does one of the two un-park labels (the third,
    sdlc:accept-risk, retired with decision 35). The workflow token's own review or label
    never does (a [bot] reviewer is refused besides)."""
    data = _workflow_yaml(FIX_WORKFLOW)
    on = _triggers(data)
    assert on["pull_request_review"]["types"] == ["submitted"]
    assert on["pull_request"]["types"] == ["labeled"]
    assert "branches" not in on["pull_request"]  # any base: the PR's head is what matters
    assert on["workflow_dispatch"]["inputs"]["change_id"]["required"] is True
    job = data["jobs"]["fix"]
    assert "github.event.review.state == 'changes_requested'" in job["if"]
    assert "!endsWith(github.event.review.user.login, '[bot]')" in job["if"]
    # D9 (the sample's weekly security review, 2026-09-25): only a member of the repository
    # starts a round; anyone with read access on a public repository can request changes
    for association in ("OWNER", "MEMBER", "COLLABORATOR"):
        assert f"github.event.review.author_association == '{association}'" in job["if"]
    for refused in ("CONTRIBUTOR", "FIRST_TIME_CONTRIBUTOR", "FIRST_TIMER", "NONE"):
        assert f"'{refused}'" not in job["if"], refused
    installed = (REPO_WORKFLOW_DIR / FIX_WORKFLOW).read_text(encoding="utf-8")
    assert installed == render.render_file(WORKFLOW_DIR / FIX_WORKFLOW, VALUES)
    for label in ("sdlc:reset-iterations", "sdlc:unlock-tests"):
        assert f"github.event.label.name == '{label}'" in job["if"], label
    assert "sdlc:accept-risk" not in job["if"]  # retired with decision 35
    assert "sdlc:c-approved" not in job["if"] and "sdlc:d-approved" not in job["if"]
    # the checkout is the PR's head, never the review event's merge ref (after the App's mint
    # step and its time, R49)
    checkout = job["steps"][2]
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
    # 1.0.3 (decision 29): the group is the job's, so a run whose job is skipped never enters
    # it and cannot cancel the automatic fix round pending there
    assert "concurrency" not in data
    assert job["concurrency"]["group"] == (
        "sdlc-${{ inputs.head_ref || github.event.pull_request.head.ref }}"
    )


def test_fix_workflow_refuses_fork_heads_and_takes_the_comment_s_link():
    """Decision 34 (R17): the review and the label path refuse a head in another repository
    in the job's `if:`; the find step reads the owner from the default branch's sdlc.yaml
    (it names that branch); the `trigger` input reaches the round through env only."""
    data = _workflow_yaml(FIX_WORKFLOW)
    job = data["jobs"]["fix"]
    fork = "github.event.pull_request.head.repo.full_name == github.repository"
    assert job["if"].count(fork) == 2
    review, label = job["if"].split("github.event_name == 'pull_request' &&", 1)
    assert fork in review.split("github.event_name == 'pull_request_review'", 1)[1]
    assert fork in label
    # the R17 review: a refused review must not enter the concurrency group and displace a
    # pending round, so on a personal repository the condition names the owner itself; an
    # organization's owner is named in sdlc.yaml, which an expression cannot read
    exact = (
        "(github.event.review.user.login == github.repository_owner || "
        "github.event.repository.owner.type == 'Organization')"
    )
    assert exact in review and exact not in label
    text = (WORKFLOW_DIR / FIX_WORKFLOW).read_text(encoding="utf-8")
    assert "a known limit" in text and "Known limit (decision 34)" in text
    trigger = _triggers(data)["workflow_dispatch"]["inputs"]["trigger"]
    assert trigger["required"] is False and trigger["type"] == "string"
    assert "@claude" in trigger["description"] and "decision 34" in trigger["description"]
    find = next(step for step in job["steps"] if step.get("id") == "find")
    assert find["env"]["SDLC_DEFAULT_BRANCH"] == DEFAULT_BRANCH_EXPR
    phase_step = [step for step in job["steps"] if "run" in step][-1]
    assert phase_step["env"]["SDLC_TRIGGER"] == "${{ inputs.trigger }}"
    assert "inputs.trigger" not in phase_step["run"] and "SDLC_TRIGGER" not in phase_step["run"]
    text = (WORKFLOW_DIR / FIX_WORKFLOW).read_text(encoding="utf-8")
    assert "the owner's account" in text and "decision 34" in text  # the reviewer rule


def test_comment_workflow_dispatches_the_fix_round_without_a_model():
    """Decision 34 (R17), NOTES section 46: on a new pull request comment only, a coarse
    `if:`, the default branch checked out (never the PR's head), the pin and the pinned
    framework as the fix workflow takes them, then one Python step; the comment's text
    appears in the `if:` and nowhere else; the token holds three scopes."""
    data = _workflow_yaml(COMMENT_WORKFLOW)
    assert data["name"] == "SDLC comment (fix round)"  # the prefix keeps it out of the metric
    assert _triggers(data) == {"issue_comment": {"types": ["created"]}}
    assert data["permissions"] == {
        "actions": "write",
        "contents": "read",
        "pull-requests": "read",
    }
    assert "concurrency" not in data
    assert list(data["jobs"]) == ["dispatch"]
    job = data["jobs"]["dispatch"]
    assert "permissions" not in job and "concurrency" not in job
    for clause in (
        "github.event.issue.pull_request",
        "startsWith(github.event.comment.body, '@claude')",
        "!endsWith(github.event.comment.user.login, '[bot]')",
        "github.event.comment.author_association == 'OWNER'",
        "github.event.comment.author_association == 'MEMBER'",
        "github.event.comment.author_association == 'COLLABORATOR'",
    ):
        assert clause in job["if"], clause
    for refused in ("CONTRIBUTOR'", "FIRST_TIME", "'NONE'"):
        assert refused not in job["if"], refused
    steps = job["steps"]
    assert steps[0]["uses"] == "actions/checkout@v5"
    assert steps[0]["with"]["ref"] == DEFAULT_BRANCH_EXPR
    assert "head" not in str(steps[0])
    assert steps[1]["id"] == "pin" and steps[1]["run"] == PIN_RUN
    fix = _workflow_yaml(FIX_WORKFLOW)["jobs"]["fix"]["steps"]
    assert steps[1] == next(step for step in fix if step.get("id") == "pin")
    assert steps[2] == next(step for step in fix if step.get("with", {}).get("path") == "framework")
    assert len(steps) == 4
    run = steps[3]
    assert run["run"] == 'python framework/plugin/ci/comment_dispatch.py --root . --repo "$REPO"'
    assert run["env"] == {
        "GITHUB_TOKEN": "${{ github.token }}",
        "REPO": "${{ github.repository }}",
        "DEFAULT_BRANCH": DEFAULT_BRANCH_EXPR,
    }
    # the body only inside the job's if: never in env, with or run, nor anywhere in steps
    assert "comment.body" not in str(steps)
    text = (WORKFLOW_DIR / COMMENT_WORKFLOW).read_text(encoding="utf-8")
    assert text.count("github.event.comment.body") == 1
    # no model, no secret
    for absent in ("secrets.", "claude-code@", "run_phase.py", "setup-node", "project_setup"):
        assert absent not in text, absent
    for cited in ("decision 34", "NOTES section 46", "p.33", "default branch"):
        assert cited in text, cited
    assert (TEMPLATE.parent / "plugin" / "ci" / "comment_dispatch.py").is_file()


def test_abandon_workflow_records_the_end_state_without_a_model():
    """Decision 25: a PR closed without a merge abandons its change on every branch of the
    change; not a phase run (no claude, no model credential, contents: write only)."""
    data = _workflow_yaml(ABANDON_WORKFLOW)
    on = _triggers(data)
    assert on == {"pull_request": {"types": ["closed"]}}
    # pull-requests: write since 0.2.19: the dismissal of gate (f) opens a pull request;
    # checks: write for its "not a build PR" check (the R22 double check, F1)
    assert data["permissions"] == {
        "contents": "write", "pull-requests": "write", "checks": "write",
    }  # fmt: skip
    job = data["jobs"]["abandon"]
    # decision 30: a PR the fast lane superseded (labelled by the runner first) is not an abandon
    assert job["if"] == (
        "${{ github.event.pull_request.merged == false && "
        "!contains(github.event.pull_request.labels.*.name, 'sdlc:superseded') }}"
    )
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
    # its own concurrency group (live run of 2026-09-25): a close also fires the merge-guarded
    # design and build workflows, and on a shared group GitHub displaced the pending abandon run
    group = data["concurrency"]["group"]
    assert group == "sdlc-abandon-${{ github.event.pull_request.head.ref }}"
    assert data["concurrency"]["cancel-in-progress"] is False
    for other in ("sdlc-design.yml", "sdlc-build.yml"):
        assert _workflow_yaml(other)["concurrency"]["group"] != group, other


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
        'python framework/plugin/detect/cli.py finish --root . --id "$CHANGE_ID" --repo "$REPO" '
        '--detection-sha256 "$DETECTION_SHA256"'
    )
    # 0.2.27: the record finish judges is the one the Detect step wrote (a step output)
    assert finish["env"]["DETECTION_SHA256"] == "${{ steps.detect.outputs.detection_sha256 }}"
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
    assert all(
        run.startswith("python ") or run.startswith("npm ") or run == PIN_RUN for run in runs
    ), runs
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
    # the incident PR's head only (0.2.24): a Go on a build PR has no incident to park and
    # would fail the setup step's outside-changes/ check every time
    # R49 (decision 33): a Go a [bot] applied never runs, now that the App's labels start runs
    assert job["if"] == (
        "${{ github.event.label.name == 'sdlc:go' && "
        "!endsWith(github.event.sender.login, '[bot]') && "
        "startsWith(github.event.pull_request.head.ref, 'sdlc/') && "
        "endsWith(github.event.pull_request.head.ref, '/a') }}"
    )
    # the project checkout follows the App's mint step and its time (R49)
    assert job["steps"][2]["with"]["ref"] == "${{ github.event.pull_request.head.ref }}"
    runs = [step["run"] for step in job["steps"] if "run" in step]
    assert runs[-2] == (
        'python framework/plugin/detect/cli.py go --root . --id "$CHANGE_ID" '
        '--repo "$REPO" --pr-number "$PR_NUMBER"'
    )
    go = [step for step in job["steps"] if "run" in step][-2]
    assert go["env"]["SDLC_DEFAULT_BRANCH"] == DEFAULT_BRANCH_EXPR
    # the Go step holds the runbook secrets: the install command is the default branch's,
    # never the PR head's copy of commands.setup (session-6 review finding)
    [setup] = [step for step in job["steps"] if "project_setup.py" in step.get("run", "")]
    assert setup["run"] == (
        "python framework/plugin/ci/project_setup.py --root . "
        '--ref "refs/remotes/origin/$SDLC_DEFAULT_BRANCH"'
    )
    assert setup["env"]["SDLC_DEFAULT_BRANCH"] == DEFAULT_BRANCH_EXPR
    assert job["steps"].index(setup) < job["steps"].index(go)
    # 0.2.24: a failed setup step is a park, not a red run - the job goes on past it, the Go
    # runs only on a success, and the last step parks with the setup step's error line and
    # no secret in its environment
    assert setup["id"] == "setup" and setup["continue-on-error"] is True
    assert go["if"] == "steps.find.outputs.change_id != '' && steps.setup.outcome == 'success'"
    park = [step for step in job["steps"] if "run" in step][-1]
    assert park["if"] == "steps.setup.outcome == 'failure'"
    assert park["run"] == (
        'python framework/plugin/detect/cli.py park --root . --id "$CHANGE_ID" '
        '--repo "$REPO" --pr-number "$PR_NUMBER" --check setup --reason "$SETUP_ERROR"'
    )
    assert park["env"]["SETUP_ERROR"] == "${{ steps.setup.outputs.error }}"
    assert park["env"]["SDLC_DEFAULT_BRANCH"] == DEFAULT_BRANCH_EXPR
    assert not any("secrets." in str(v) for v in park["env"].values())
    assert set(park["env"]) == {
        "GITHUB_TOKEN", "CHANGE_ID", "REPO", "PR_NUMBER", "SDLC_DEFAULT_BRANCH", "SETUP_ERROR",
        "SDLC_WORKFLOW_TOKEN",  # R49: the fallback after 50 minutes
    }  # fmt: skip
    for step in job["steps"]:
        assert "${{" not in step.get("run", ""), step["name"]
    # its own concurrency group (live, 2026-09-25): a label event also fires the fix, test and
    # deploy workflows, and on a shared group GitHub displaced a pending run at random
    assert data["concurrency"]["group"] == "sdlc-runbook-${{ github.event.pull_request.head.ref }}"
    assert data["concurrency"]["cancel-in-progress"] is False
    text = (WORKFLOW_DIR / RUNBOOK_WORKFLOW).read_text(encoding="utf-8")
    for absent in ("claude-code@", "runner_setup.py", "setup-node", "--phase f "):
        assert absent not in text, absent
    # no model credential: the one secret is the App's key, read by the mint step (R49)
    assert re.findall(r"secrets\.\w+", text) == ["secrets.SDLC_APP_PRIVATE_KEY"]


# --- R49 (decision 33): the automation pushes and opens pull requests as a GitHub App ---------
APP_WORKFLOWS = (*PHASE_WORKFLOWS, FIX_WORKFLOW, DETECT_WORKFLOW, RUNBOOK_WORKFLOW, SCAN_WORKFLOW)
TOKEN_WORKFLOWS = (
    ABANDON_WORKFLOW,
    COMMENT_WORKFLOW,
    "sdlc-digest.yml",
    RELEASE_WORKFLOW,
    EVALS_WORKFLOW,
)
APP_TOKEN = "${{ steps.app.outputs.token || github.token }}"
MINT_STEP = {
    "name": "Mint the App token (decision 33; skipped without vars.SDLC_APP_ID)",
    "id": "app",
    "if": "${{ vars.SDLC_APP_ID != '' }}",
    "uses": "actions/create-github-app-token@v2",
    "with": {
        "app-id": "${{ vars.SDLC_APP_ID }}",
        "private-key": "${{ secrets.SDLC_APP_PRIVATE_KEY }}",
    },
}
# the scopes the App holds (sdlc-init step 6) and so may narrow to the job's permissions:
APP_SCOPES = ("contents", "pull-requests", "issues", "checks", "actions")
# the mint time the runner's 50-minute fallback counts from (plugin/ci/app_token.py)
STAMP_STEP = {
    "name": "Record when the App token was minted",
    "if": "steps.app.outcome == 'success'",
    "run": (
        "python -c \"import os, time; f = open(os.environ['GITHUB_ENV'], 'a'); "
        "f.write('SDLC_APP_TOKEN_MINTED_AT=%d\\n' % time.time()); f.close()\""
    ),
}
WORKFLOW_TOKEN = "${{ github.token }}"


def _header(name: str) -> str:
    """The workflow's text with each comment's line breaks joined, for a phrase search."""
    return re.sub(r"\n# ?", " ", (WORKFLOW_DIR / name).read_text(encoding="utf-8"))


def _condition(name: str, job: str) -> str:
    return " ".join(_workflow_yaml(name)["jobs"][job]["if"].split())


def test_every_workflow_either_mints_the_app_token_or_keeps_the_workflow_token():
    # the merge workflow mints the merge App's token, never decision 33's (choice 242)
    assert sorted((*APP_WORKFLOWS, *TOKEN_WORKFLOWS, MERGE_WORKFLOW)) == sorted(ALL_WORKFLOWS)


def test_the_merge_workflow_rings_posts_and_merges_with_the_merge_app_only():
    """R22 (decision 36): the review-triggered job holds no key and only dispatches; the
    pull_request job posts "not a build PR"; the dispatched job alone reads the merge App's
    key, in the sdlc-merge environment, never decision 33's App's key."""
    data = _workflow_yaml(MERGE_WORKFLOW)
    on = _triggers(data)
    assert on["pull_request_review"]["types"] == ["submitted"]
    assert on["pull_request"]["types"] == ["opened", "synchronize", "reopened", "ready_for_review"]
    assert set(on["workflow_dispatch"]["inputs"]) == {"change_id", "head_ref", "pr"}
    assert data["permissions"] == {
        "actions": "write", "checks": "write", "contents": "read", "pull-requests": "read",
    }  # fmt: skip
    jobs = data["jobs"]
    assert list(jobs) == ["doorbell", "not-a-build-pr", "merge"]
    text = (WORKFLOW_DIR / MERGE_WORKFLOW).read_text(encoding="utf-8")
    assert "SDLC_APP_PRIVATE_KEY" not in text and "vars.SDLC_APP_ID" not in text
    assert re.findall(r"secrets\.\w+", text) == ["secrets.SDLC_MERGE_APP_PRIVATE_KEY"]
    for name in ("doorbell", "not-a-build-pr"):
        job = jobs[name]
        assert "environment" not in job
        assert "SDLC_MERGE" not in json.dumps(job)
        assert job["steps"][0]["with"]["ref"] == DEFAULT_BRANCH_EXPR
    doorbell = _condition(MERGE_WORKFLOW, "doorbell")
    assert "github.event.review.state == 'approved'" in doorbell
    assert jobs["doorbell"]["steps"][-1]["run"].startswith(
        "python framework/plugin/ci/merge_step.py doorbell "
    )
    assert "!(startsWith(github.event.pull_request.head.ref, 'sdlc/')" in (
        _condition(MERGE_WORKFLOW, "not-a-build-pr")
    )
    merge = jobs["merge"]
    assert merge["environment"] == "sdlc-merge"
    # a dispatch on the default branch only, beside the environment's branch rule (the R22
    # double check, F13)
    assert merge["if"] == (
        "${{ github.event_name == 'workflow_dispatch' && "
        "github.ref == format('refs/heads/{0}', github.event.repository.default_branch) }}"
    )
    # the job that holds the merge App's key runs its actions at a commit SHA (choice 250, F9)
    used = [s["uses"] for s in merge["steps"] if "uses" in s]
    assert used and all(re.fullmatch(r"[\w-]+/[\w-]+@[0-9a-f]{40}", u) for u in used), used
    assert merge["concurrency"]["group"].startswith("sdlc-merge-")
    mint = [s for s in merge["steps"] if s.get("uses", "").startswith("actions/create-github")]
    assert len(mint) == 1 and mint[0]["with"]["app-id"] == "${{ vars.SDLC_MERGE_APP_ID }}"
    assert {k for k in mint[0]["with"] if k.startswith("permission-")} == {
        "permission-contents", "permission-pull-requests",
    }  # fmt: skip
    last = merge["steps"][-1]
    assert last["env"]["SDLC_MERGE_TOKEN"] == "${{ steps.app.outputs.token }}"
    assert last["env"]["GITHUB_TOKEN"] == WORKFLOW_TOKEN  # the reads; the merge App merges only
    assert "SDLC_MERGE_TOKEN" not in json.dumps(merge["steps"][:-1])
    # without the merge App the job says so and stops: the owner merges (fallback C1)
    assert merge["steps"][0]["if"] == "${{ vars.SDLC_MERGE_APP_ID == '' }}"
    assert all(s.get("if") == "${{ vars.SDLC_MERGE_APP_ID != '' }}" for s in merge["steps"][1:])


# the steps that can post the passing sdlc/review "not a build PR" (decision 36, point 5):
# pr/cli.py upsert (also through run_phase.py and scan/cli.py), detect/cli.py dismiss and go
# (the runbook PR), merge_step.py not-build
CHECK_POSTERS = (
    "plugin/pr/cli.py", "plugin/ci/run_phase.py", "plugin/scan/cli.py",
    "plugin/detect/cli.py dismiss", "plugin/detect/cli.py go", "merge_step.py not-build",
)  # fmt: skip


@pytest.mark.parametrize("name", ALL_WORKFLOWS)
def test_a_job_that_posts_the_review_check_may_write_checks(name):
    """The R22 double check, F1 and F5: a job whose step posts sdlc/review holds
    ``checks: write``, and so does its App token, or the post is a 403 that the step keeps
    quiet and ruleset 2 holds the pull request."""
    data = _workflow_yaml(name)
    for job_name, job in data["jobs"].items():
        runs = " ".join(str(s.get("run") or "") for s in job.get("steps") or [])
        if not any(poster in runs for poster in CHECK_POSTERS):
            continue
        permissions = job.get("permissions", data.get("permissions")) or {}
        assert permissions.get("checks") == "write", (name, job_name)
        for step in job["steps"]:
            if str(step.get("uses", "")).startswith("actions/create-github-app-token"):
                assert step["with"].get("permission-checks") == "write", (name, job_name)


@pytest.mark.parametrize("name", APP_WORKFLOWS)
def test_a_workflow_that_pushes_mints_the_app_token_first(name):
    """The mint step is the job's first, skipped without the variable; the project checkout
    and every GitHub token of the job read its output, falling back to the workflow token."""
    data = _workflow_yaml(name)
    job = next(iter(data["jobs"].values()))  # R8's second-opinion job after it mints nothing
    steps = job["steps"]
    # the token carries no more than this job's permissions: block grants the workflow token
    narrowed = {
        f"permission-{s}": data["permissions"][s] for s in APP_SCOPES if s in data["permissions"]
    }
    assert steps[0] == {**MINT_STEP, "with": {**MINT_STEP["with"], **narrowed}}
    # the private key: in the mint step's with: and nowhere else, never in an env:
    text = (WORKFLOW_DIR / name).read_text(encoding="utf-8")
    assert text.count("SDLC_APP_PRIVATE_KEY") == 1
    assert "SDLC_APP_PRIVATE_KEY" not in json.dumps([data.get("env"), job.get("env"), steps[1:]])
    checkouts = [s for s in steps if s.get("uses", "").startswith("actions/checkout@")]
    project = [s for s in checkouts if s["with"].get("path") != "framework"]
    assert project == [steps[2]]  # the project checkout follows the mint step and its time
    assert steps[2]["with"]["token"] == APP_TOKEN  # pushes go out on its persisted token
    for framework in checkouts[1:]:
        assert "token" not in framework["with"]  # a public read, as before
    tokens = [
        value
        for step in steps
        for key, value in (step.get("env") or {}).items()
        if key in ("GITHUB_TOKEN", "GH_TOKEN")
    ]
    assert tokens and set(tokens) == {APP_TOKEN}
    # the workflow token beside the App's, for the fallback after 50 minutes, and nowhere
    # else (fix round 4: the checkout check's fetch takes both, like every other step)
    for step in steps:
        env = dict(step.get("env") or {})
        if "GITHUB_TOKEN" in env:
            assert env.pop("SDLC_WORKFLOW_TOKEN") == WORKFLOW_TOKEN, step.get("name")
        assert "SDLC_WORKFLOW_TOKEN" not in env and WORKFLOW_TOKEN not in json.dumps(env)
    # the token rule names the App and keeps the fallback's explicit dispatch
    header = _header(name)
    assert "Token rule (decision 33)" in header and "SDLC_APP_ID" in header
    assert "events the App causes do start workflow runs" in header


@pytest.mark.parametrize("name", ALL_WORKFLOWS)
def test_no_checkout_persists_a_credential(name):
    """R49 fix round 4: ``.git/config`` holds no token after any checkout, so neither
    project code (the commands step's targets, the toolchain install), a planted hook nor a
    planted config key can reach one; each git network call of the runner takes it in its
    own environment (``ci/app_token.py git_auth_env``)."""
    data = _workflow_yaml(name)
    checkouts = [
        step
        for job in data["jobs"].values()
        for step in job["steps"]
        if step.get("uses", "").startswith("actions/checkout@")
    ]
    assert checkouts, name
    for step in checkouts:
        assert step["with"]["persist-credentials"] is False, (name, step.get("name"))
    if name == RELEASE_WORKFLOW:
        # the record job's push takes the job's token from its step's environment
        [record] = [s for s in data["jobs"]["record"]["steps"] if "run" in s]
        assert record["env"]["GITHUB_TOKEN"] == "${{ github.token }}"


@pytest.mark.parametrize("name", APP_WORKFLOWS)
def test_a_workflow_that_mints_the_app_token_records_when(name):
    """The installation token expires an hour after it is minted; the step after the mint
    writes the time to $GITHUB_ENV for the runner's 50-minute fallback, and only when the
    mint ran (without the App the fallback has nothing to count from and stays a no-op)."""
    jobs = _workflow_yaml(name)["jobs"]
    # R8 (1.0.19): the second-opinion job after the phase job mints nothing
    minting = [
        job
        for job in jobs.values()
        if any("create-github-app-token" in str(step.get("uses", "")) for step in job["steps"])
    ]
    assert len(minting) == 1 and set(jobs) - {"second-opinion"} == {next(iter(jobs))}
    assert minting[0]["steps"][1] == STAMP_STEP


@pytest.mark.parametrize("name", TOKEN_WORKFLOWS)
def test_a_workflow_that_needs_no_ci_run_keeps_the_workflow_token(name):
    text = (WORKFLOW_DIR / name).read_text(encoding="utf-8")
    for absent in ("create-github-app-token", "SDLC_APP_", "steps.app."):
        assert absent not in text, absent
    assert "keeps the workflow token, not the App's (decision 33)" in _header(name)


def test_the_app_s_own_events_start_nothing_they_should_not():
    """The trigger audit: with the App, the automation's own pushes, PR opens and closes and
    labels start workflows. One assertion per guard."""
    # no template workflow runs on a push, so the App's pushes to sdlc/** start none of them
    assert not [n for n in ALL_WORKFLOWS if "push" in _triggers(_workflow_yaml(n))]
    # the runner's superseded close (labelled first) is not an abandon (R46)
    assert "!contains(github.event.pull_request.labels.*.name, 'sdlc:superseded')" in (
        _condition(ABANDON_WORKFLOW, "abandon")
    )
    # an intent PR the App opened (detect, scan) takes no fast lane: author and sender
    design = _condition("sdlc-design.yml", "design")
    assert "!endsWith(github.event.pull_request.user.login, '[bot]')" in design
    assert "!endsWith(github.event.sender.login, '[bot]')" in design
    # a close without a merge runs neither the design nor the build job
    assert "github.event.pull_request.merged == true" in design
    assert _condition("sdlc-build.yml", "build") == (
        "${{ github.event_name == 'workflow_dispatch' || "
        "github.event.pull_request.merged == true }}"
    )
    # a label a [bot] applied starts no round and approves no gate
    bot_sender = "!endsWith(github.event.sender.login, '[bot]')"
    fix = _condition(FIX_WORKFLOW, "fix")
    assert bot_sender in fix.split("github.event_name == 'pull_request' &&", 1)[1]
    # decision 37 (1.0.21): no approval label starts (d) or (e) any more; only a dispatch does
    for name in ("sdlc-test.yml", "sdlc-deploy.yml"):
        assert set(_triggers(_workflow_yaml(name))) == {"workflow_dispatch"}, name
    assert bot_sender in _condition(RUNBOOK_WORKFLOW, "go")
    # a [bot] review or @claude comment starts no round
    assert "!endsWith(github.event.review.user.login, '[bot]')" in fix
    assert "!endsWith(github.event.comment.user.login, '[bot]')" in (
        _condition(COMMENT_WORKFLOW, "dispatch")
    )
    # an approval by a [bot] rings no merge (decision 36)
    assert "!endsWith(github.event.review.user.login, '[bot]')" in (
        _condition(MERGE_WORKFLOW, "doorbell")
    )
    # the release label counts only on a merged PR (decision 33's App never merges, decision
    # 4; the merge App merges only on the owner's approval, decision 36)
    assert "github.event.pull_request.merged == true &&" in _condition(RELEASE_WORKFLOW, "release")


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
    proc = pin("--ref", "refs/remotes/origin/main")
    assert proc.returncode == 0, proc.stderr
    assert "ref=v0.2.16" in proc.stdout and "claude_code=" in proc.stdout
    # a ref the checkout lacks is fetched from origin into the remote-tracking ref, and the
    # checkout stays complete (no depth-limited fetch)
    git("update-ref", "-d", "refs/remotes/origin/main")
    proc = pin("--ref", "refs/remotes/origin/main")
    assert proc.returncode == 0, proc.stderr
    assert "ref=v0.2.16" in proc.stdout
    assert git("rev-parse", "--verify", "refs/remotes/origin/main").strip()
    assert not (work / ".git" / "shallow").exists()
    proc = pin("--ref", "refs/remotes/origin/nowhere")
    assert proc.returncode == 1
    assert "cannot read sdlc.yaml at refs/remotes/origin/nowhere" in proc.stderr
    # 0.2.24: a tag named origin/main (anyone with write access can push one) shadows the
    # short refname - git resolves refs/tags/<name> before refs/remotes/<name> - and the
    # short form still reads the tag's copy; the workflows pass the qualified ref
    (work / "sdlc.yaml").write_text("plugin:\n  version: 9.9.9\n", encoding="utf-8")
    git("commit", "-q", "-am", "the planted pin")
    git("tag", "origin/main")
    git("checkout", "-q", "sdlc/0001/b")
    assert "ref=v9.9.9" in pin("--ref", "origin/main").stdout
    assert "ref=v0.2.16" in pin("--ref", "refs/remotes/origin/main").stdout
    # the short form still works when no tag shadows it, and a value that reads as an
    # option is refused
    git("tag", "-d", "origin/main")
    assert "ref=v0.2.16" in pin("--ref", "origin/main").stdout
    assert pin("--ref=--output=x").returncode == 1


def test_the_pin_script_falls_back_to_the_cli_init_writes(tmp_path):
    """R63 (1.0.16): a project with no ``plugin.claude_code`` installs the CLI /sdlc-init
    writes, 2.1.304, the first version read to run a sub-agent on the template's
    ``claude-opus-5-5`` (NOTES §54); 2.1.278 ran it on the session's model."""
    from init import sdlc_init

    assert sdlc_init.DEFAULT_CLAUDE_CODE_VERSION == "2.1.304"
    proc = _pin(tmp_path, 'plugin:\n  version: "1.4.0"\n')
    assert proc.returncode == 0, proc.stderr
    assert f"claude_code={sdlc_init.DEFAULT_CLAUDE_CODE_VERSION}" in proc.stdout
    rendered = render.render_file(TEMPLATE / "sdlc.yaml", VALUES)
    assert "2.1.304 is the CLI the jobs install and the framework's minimum" in rendered
    assert "2.1.278" not in rendered


def test_pin_script_does_not_double_the_v_of_a_version(tmp_path):
    proc = _pin(tmp_path, 'plugin:\n  version: "v1.4.0"\n  claude_code: "2.1.304"\n')
    assert proc.returncode == 0, proc.stderr
    assert "ref=v1.4.0" in proc.stdout and "ref=vv" not in proc.stdout


def test_pin_script_refuses_a_claude_code_that_is_not_a_version(tmp_path):
    """The value is interpolated into the install step's shell command."""
    proc = _pin(tmp_path, 'plugin:\n  version: "1.4.0"\n  claude_code: "2.1.1; rm -rf /"\n')
    assert proc.returncode == 2
    assert "not a version string" in proc.stderr
    ok = _pin(tmp_path, 'plugin:\n  version: "1.4.0"\n  claude_code: "latest"\n')
    assert ok.returncode == 0 and "claude_code=latest" in ok.stdout


@pytest.mark.parametrize("name", [*PHASE_WORKFLOWS, FIX_WORKFLOW, DETECT_WORKFLOW])
def test_every_phase_run_step_names_the_default_branch(name):
    """0.2.25: ``SDLC_DEFAULT_BRANCH`` was set on the pin step only; the phase run's guard
    and gate guessed the default branch from ``origin/main`` or ``origin/master``, and a
    project whose default branch is neither parked at every gate ("no base branch"). Every
    step that runs a phase (not the 20-second find-the-change step) names it now."""
    data = _workflow_yaml(name)
    steps = [
        step
        for job in data["jobs"].values()
        for step in job["steps"]
        if "run_phase.py" in step.get("run", "") and "--find-change" not in step["run"]
    ]
    assert steps, name
    for step in steps:
        assert step["env"]["SDLC_DEFAULT_BRANCH"] == DEFAULT_BRANCH_EXPR, step["name"]
        assert step["env"]["DEFAULT_BRANCH"] == DEFAULT_BRANCH_EXPR, step["name"]
