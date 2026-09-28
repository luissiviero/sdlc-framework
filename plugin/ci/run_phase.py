"""One merge-triggered phase run: guard, compose, run ``claude -p``, hand over.

Build guide step 30 (tasks 30.3 and 30.5); the trigger and dispatch table it implements is
docs/OPERATING_MODEL.md sections 4.1 and 4.2; the flag facts are docs/NOTES.md sections 2,
3 and 10b; the read-only triage step is the article's p.41 pipeline step.

    python framework/plugin/ci/run_phase.py --root . --plugin-dir framework \
        --phase b|c|d|e|review --id 0001 --repo owner/name \
        [--head-ref sdlc/0001/a] [--pr-number 12] [--ref main] [--dry-run] [--no-dispatch]
        [--claude claude]
    python framework/plugin/ci/run_phase.py --root . --phase b|c|fix --head-ref <head> \
        --repo owner/name --pr-number 12 [--id 0001] --find-change
    python framework/plugin/ci/run_phase.py --root . --plugin-dir framework --phase fix \
        --id 0001 --head-ref <the PR's head> --repo owner/name --pr-number 12
    python framework/plugin/ci/run_phase.py --phase triage --log out/build.log

``--phase fix`` is the fix round (decision 22; ``template/.github/workflows/sdlc-fix.yml``):
the owner's "Request changes" review or one of the un-park labels (decision 24) on any
phase's pull request. It runs on that PR's own head (``--head-ref``, never created), performs
the owner's labels first (``state/unpark.py``, committed with the actor), then runs
``/sdlc-fix <id>``; the gate file, the spend and the PR are those of the change's own phase.
An abandoned change (decision 25) is skipped by every phase.

The change id comes from ``--id``, else from a head ref ``sdlc/<id>/<previous phase>``, else
from the one ``changes/<id>-<slug>/`` folder the merged pull request ``--pr-number`` touches
(``find_change``; HANDOFF 4(a): a web-session intent PR has a ``claude/...`` head). With
``--find-change`` the script prints only ``change_id=`` and ``reason=`` and writes the id to
``$GITHUB_OUTPUT``: the merge-fired design and build workflows run it first and skip every
later step when the merge carries no change.

What one run does, in order:

1. sets a git identity when the runner has none (the automation identity of
   OPERATING_MODEL section 2; the owner's account never commits from CI);
1b. **switches to the change's work branch** — a ``workflow_dispatch`` run checks out the
   default branch, where ``status.yaml`` says what main says, so every guard below would
   read the wrong phase. The run fetches ``origin`` and switches to the branch this phase
   works on (``sdlc/<id>/b`` for a design run, ``sdlc/<id>/c`` for build, test, deploy and
   the review pass), creating it for (b) and (c) from the default branch (the owner's merge
   at gate (b) put the approved spec and plan there). When there is nothing to switch to,
   the current checkout is used;
1c. **installs the project's own toolchain** — ``sdlc.yaml: commands.setup`` through
   ``ci/project_setup.py``. A GitHub-hosted runner carries none of the project's tools, and
   the installed workflow file may be an older copy without that step (the third live design
   run, 2026-09-21, failed the gate's ``commands`` check with "No module named pytest"), so
   the run does it itself. A project with no setup command is skipped; a setup command that
   fails is an infrastructure failure. A dry run installs nothing;
2. **guards** — not paused, the change exists, ``status.yaml`` is at the phase this run
   follows with a passing gate, not parked, and in the Full profile the owner's approval
   label is on the build PR and was applied by a human, not by the workflow token. A failed
   guard prints ``{"skipped": ...}`` and exits 0, so a duplicate trigger is harmless. One
   exception: a (b) or (c) run whose work branch already carries this phase but has no open
   pull request is a re-run of an attempt that never reached the queue, and it proceeds with
   the earlier park cleared (``rerun_reason``);
3. refuses to run on a branch that changed a guardrail file (``.claude/**``, ``CLAUDE.md``,
   ``REVIEW.md``, ``sdlc.yaml``, ``protected_paths``) unless intent.md says
   ``Framework change: yes``; a park commits the change folder on the work branch and
   updates the phase's PR, so the owner finds it in the queue (decision 6, layer iii);
4. for phase (c), runs ``gate/preflight.py``: it decides the permission mode, and a refusal
   that is not about auto-accept parks the change (same mechanics) instead of running;
4b. creates the ``sdlc:*`` labels the runs apply (422 = the label already exists);
5. composes and runs the bounded headless call — the pinned plugin through ``--plugin-dir``,
   the CI settings file through ``--settings`` (bare mode reads no settings by itself),
   ``--permission-prompts none``, ``--max-turns`` / ``--max-budget-usd`` from ``sdlc.yaml``,
   ``--output-format json`` — with exactly one credential in the environment;
6. stores the JSON result as ``changes/<id>-<slug>/evidence/claude-<phase>.json``, records
   ``total_cost_usd`` with ``gate/cli.py record-spend`` and commits the run record on the
   work branch (the model's session pushed before the spend was known), and validates the
   findings file after a review pass;
7. opens or updates the phase's pull request with ``pr/cli.py upsert`` (idempotent: an
   existing PR only has its body and its gate label refreshed), so a parked run is a queue
   item even when the model's session never reached that step. The upsert's own JSON says
   which route it took: a run that ends with no pull request is an infrastructure failure,
   because a phase result nobody can find in the queue is not a hand-over;
8. reads ``evidence/gate-<phase>.json`` and, on ``continue``, dispatches the next workflow
   with the change id and the next phase's work branch as ``head_ref`` (the only hand-over
   GitHub allows from the workflow token; ``head_ref`` keys the concurrency group).

Exit codes: 0 the run finished, was skipped or parked (a park is a queue item, not a CI
failure); 1 an infrastructure failure — the setup command failed, the CLI exited non-zero,
reported ``is_error``, left no gate file behind, or no pull request carries the result;
2 a usage error.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

PLUGIN_DIR = Path(__file__).resolve().parent.parent  # <framework root>/plugin
FRAMEWORK_ROOT = PLUGIN_DIR.parent
if str(PLUGIN_DIR) not in sys.path:
    sys.path.insert(0, str(PLUGIN_DIR))

from pr.github import next_page_url  # noqa: E402, F401 - re-exported, moved there in 0.2.12

from ci import auth as auth_mod  # noqa: E402
from ci import fix_requests, project_setup  # noqa: E402
from gate import artifacts as art  # noqa: E402
from gate import diff as gate_diff  # noqa: E402
from gate import limits  # noqa: E402
from hooks._common import (  # noqa: E402
    SDLC_FILE,
    ConfigError,
    config_flag,
    load_sdlc_config,
    matches,
)
from state import conventions as c  # noqa: E402
from state import status as status_mod  # noqa: E402

EXIT_OK, EXIT_FAILED, EXIT_USAGE = 0, 1, 2

# --- the phases this script runs -----------------------------------------------------------
PHASE_COMMAND = {
    "b": "sdlc-design",
    "c": "sdlc-build",
    "d": "sdlc-test",
    "e": "sdlc-deploy",
    # phase (f) maintain (build guide step 37): the diagnosis of a filed detection record,
    # read-only on source, that writes the incident intent and proposes a gated route
    "f": "sdlc-maintain",
    # decision 22: the owner's "Request changes" review (or an un-park label) starts a fix
    # round on the phase's own PR, whatever phase the change is in (a)-(f)
    "fix": "sdlc-fix",
}
RUNNABLE = (*PHASE_COMMAND, "review", "triage")
# The phase whose artifact this run consumes: status.yaml must be there, with a passing gate
# for every phase past (b) (OPERATING_MODEL section 4.2, "Guard" column). A fix round has no
# previous phase: it re-runs the change's current phase on the PR's own head.
# A maintain run follows the filing step (``detect/cli.py run --file``), which leaves the
# change at phase f itself; a merged incident intent PR is gate (a) of that change (decision
# 25), so the design run accepts a change at f as at a (``PHASE_BEFORE``).
PREVIOUS_PHASE = {"b": "a", "c": "b", "d": "c", "e": "d", "f": "f", "review": "d", "fix": None}
PHASE_BEFORE = {"b": ("a", "f")}  # the phases a run accepts where PREVIOUS_PHASE names one
GATE_MUST_HAVE_PASSED = ("c", "d", "e", "review")
FIX_PHASES = ("a", "b", "c", "d", "e", "f")  # the phases whose PR a fix round may run on
# Full profile only: the owner's approving label on the build PR, and who applied it.
APPROVAL_LABEL = {"d": "c", "e": "d", "review": "d"}  # run phase -> phase whose label is read
APPROVAL_BRANCH_PHASE = "c"  # the build PR, which lives on sdlc/<id>/c through (d) and (e)
# Hand-over (section 4.2, "Hands over" column). A `wait` or a `park` dispatches nothing;
# gate (b) is the owner's merge in every profile since the Lite removal (plugin 0.2.14), so
# a design run never dispatches the build.
NEXT_WORKFLOW = {"c": "sdlc-test.yml", "d": "sdlc-deploy.yml"}
# The phase the dispatched workflow runs; its work branch is the dispatch's ``head_ref``
# input, which keys the workflow's concurrency group on the change's own branch.
NEXT_PHASE = {"c": "d", "d": "e"}
# Permission mode per phase; (c) asks the preflight instead (step 18, never bypass).
PERMISSION_MODE = {
    "b": "default",
    "d": "acceptEdits",
    "e": "acceptEdits",
    "f": "default",
    "review": "default",
    "fix": "acceptEdits",
}
# Phase (b) writes spec.md and plan.md and nothing else: it may create files, never edit one.
# Write cannot be path-scoped (NOTES section 6), so the gate's design_scope check stays the
# net for a source file a Write overwrote.
DESIGN_ALLOWED_TOOLS = "Read,Grep,Glob,Write,Bash(python *),Bash(git *)"
DESIGN_DISALLOWED_TOOLS = "Edit,MultiEdit,NotebookEdit,WebFetch,WebSearch"
# Phases (c), (d) and (e) edit code and run the toolchain. The tools are named explicitly,
# as for (b): the project's allow rules are ignored in an untrusted checkout (NOTES section
# 3) and whether a --settings allow-list counts is undocumented; the eighth live run
# (2026-09-22, phase (c)) ended in 28 s without reaching its gate. The list mirrors the
# allow-list of settings.ci.json; the deny rules of that file still apply on top.
IMPLEMENT_ALLOWED_TOOLS = (
    "Read,Grep,Glob,Edit,MultiEdit,Write,Agent,Bash(git *),Bash(gh *),Bash(python *),"
    "Bash(python3 *),Bash(pytest *),Bash(ruff *),Bash(npm *),Bash(npx *),Bash(node *)"
)
IMPLEMENT_DISALLOWED_TOOLS = "WebFetch,WebSearch"
# The review pass is read-only but for the one file it writes (decision 12).
REVIEW_ALLOWED_TOOLS = "Read,Grep,Glob,Bash(git *),Write"
REVIEW_DISALLOWED_TOOLS = "Edit,WebFetch,WebSearch"
# The maintain run diagnoses read-only (p.43 step 3): the bands' own tool list plus what it
# needs to write intent.md and proposal.json and commit them (``detect/cli.py
# maintain_tools``); the gate's design_scope check refuses anything committed outside the
# change folder.
MAINTAIN_DISALLOWED_TOOLS = "Edit,MultiEdit,NotebookEdit,WebFetch,WebSearch"
# The p.41 read-only triage step: it reads a log and says what it thinks; it fixes nothing.
TRIAGE_ALLOWED_TOOLS = "Read"
TRIAGE_DISALLOWED_TOOLS = "Edit,Write,Bash"
TRIAGE_PROMPT = (
    "Read the CI log at {log}. In at most five lines say what failed, the likely cause and "
    "the first thing to check. Do not fix anything."
)
# Review spend belongs to the deploy phase's budget: it is part of the (e) run.
SPEND_PHASE = {"review": "e"}

CLAUDE_RESULT_FILE = "claude-{phase}.json"
CLAUDE_STDERR_FILE = "claude-{phase}.stderr.txt"
# A second run of the same phase (a fix round, a re-run by hand) keeps its own record:
# ``claude-<phase>-2.json``, ``-3``, ... The first deferred fix round on the sample
# repository (2026-09-24) overwrote nothing yet - the previous round's ``claude-fix.json``
# was still the only transcript when the adversarial reviewer read the evidence, and it
# escalated on a "proof mismatch" between that older run and the diff.
CLAUDE_RUN_FILE = "claude-{phase}-{n}.json"
CLAUDE_RUN_STDERR_FILE = "claude-{phase}-{n}.stderr.txt"
SETTINGS_REL = ("plugin", "ci", "settings.ci.json")

BOT_LOGIN = "github-actions[bot]"
BOT_EMAIL = "41898282+github-actions[bot]@users.noreply.github.com"
LABEL_COLOR_GATE = "0E8A16"  # the *-ready and *-approved labels
LABEL_COLOR_HUMAN = "D93F0B"  # sdlc:needs-human
TOKEN_VARS = ("GITHUB_TOKEN", "GH_TOKEN")

DEFAULT_MAX_TURNS = 200
GRACE_MINUTES = 5  # the subprocess timeout sits this far above the gate's wall clock


def _emit(obj: Any) -> None:
    print(json.dumps(obj, indent=2, sort_keys=True))


def _skip(reason: str) -> int:
    _emit({"skipped": reason})
    return EXIT_OK


# --- git identity ---------------------------------------------------------------------------
def ensure_git_identity(root: Path) -> str | None:
    """Give the checkout the automation identity when the runner configured none."""
    from state import gitops

    if not gitops.is_repo(root):
        return None
    return gitops.ensure_identity(root, BOT_LOGIN, BOT_EMAIL)


# --- configuration --------------------------------------------------------------------------
def _config(root: Path) -> dict[str, Any]:
    try:
        return load_sdlc_config(str(root)) or {}
    except ConfigError:
        return {}


def _gate_settings(config: dict[str, Any]) -> dict[str, Any]:
    gate_cfg = config.get("gate")
    return gate_cfg if isinstance(gate_cfg, dict) else {}


def _int_or(value: Any, default: int) -> int:
    try:
        n = int(value)
    except (TypeError, ValueError):
        return default
    return n if n > 0 else default


def run_timeout_seconds(config: dict[str, Any]) -> int:
    minutes = _int_or(
        _gate_settings(config).get("max_wall_clock_minutes"),
        limits.DEFAULT_MAX_WALL_CLOCK_MINUTES,
    )
    return (minutes + GRACE_MINUTES) * 60


# --- GitHub (imported lazily: plugin/pr/github.py is a sibling deliverable) --------------------
def _github():
    try:
        from pr import github  # noqa: PLC0415
    except ImportError:  # pragma: no cover - only when the plugin install is incomplete
        return None
    return github


def _token(env: dict[str, str]) -> str | None:
    for var in TOKEN_VARS:
        if env.get(var):
            return env[var]
    return None


def ensure_labels(repo: str, env: dict[str, str]) -> dict[str, Any]:
    """Create every label of ``conventions.all_labels()``; an existing one (422) is success."""
    github = _github()
    if github is None or not repo or not _token(env):
        return {"ensured": 0, "note": "no token in the environment: labels not created"}
    created, failed = [], []
    for name in c.all_labels():
        color = LABEL_COLOR_HUMAN if name == c.NEEDS_HUMAN_LABEL else LABEL_COLOR_GATE
        result = github.ensure_label(repo, name, color, f"SDLC framework: {name}")
        if not result.get("ok"):
            failed.append(name)
        elif result.get("created"):
            created.append(name)
    return {"ensured": len(c.all_labels()), "created": created, "failed": failed}


def label_applied_by_a_human(repo: str, number: int, label: str) -> tuple[bool, str]:
    """Say whether a person applied ``label`` last: (True, login) or (False, reason).

    The timeline is read by ``pr/github.py label_actor`` (the paging lives there since
    0.2.12); the workflow token's own label would be ``github-actions[bot]`` and must never
    pass a human gate (OPERATING_MODEL section 4.2, "actor not the token").
    """
    github = _github()
    if github is None:
        return False, "plugin/pr/github.py is not available"
    found = github.label_actor(repo, number, label)
    if not found.get("ok"):
        return False, f"could not read the label events: {found.get('reason') or 'failed'}"
    actor = found.get("actor")
    if not actor:
        return False, f"no `labeled` event for {label}"
    if actor == BOT_LOGIN:
        return False, f"{label} was applied by {actor}, not by a human"
    return True, actor


def check_approval(repo: str, change_id: str, run_phase: str, env: dict[str, str]) -> str | None:
    """Full profile: the skip reason when the owner's approval is not on the build PR."""
    label = c.approved_label(APPROVAL_LABEL[run_phase])
    github = _github()
    if github is None:
        return f"{label} cannot be checked: plugin/pr/github.py is not available"
    if not _token(env) and not github.gh_path():
        # fail closed: with no route to GitHub the label cannot be read at all, and an
        # unverifiable human gate is not a passed human gate (OPERATING_MODEL section 4.2).
        return f"{label} cannot be verified: no gh and no token"
    head = c.branch_name(change_id, APPROVAL_BRANCH_PHASE)
    pr = github.find_open_pr(repo, head)
    number = pr.get("number")
    if not number:
        return f"no open PR on {head} to read {label} from"
    if label not in (pr.get("labels") or []):
        return f"the build PR #{number} does not carry {label}"
    if not _token(env):
        print(f"note: no token, so the actor of {label} is not checked", file=sys.stderr)
        return None
    ok, who = label_applied_by_a_human(repo, int(number), label)
    return None if ok else f"{label} on PR #{number}: {who}"


# --- what the runner leaves in the working directory (first live design run, 2026-09-21) -----
# Two kinds of untracked entry appear in a phase job's checkout and belong to nobody:
#   * ``framework/`` — the pinned framework the workflow checks out beside the project
#     (actions/checkout with ``path: framework``); it is a nested repository, so git lists it
#     as one untracked entry;
#   * the placeholder dotfiles Claude Code's sandbox creates in the working directory.
# Neither is ever committed (commit-phase stages the change folder only), but both made the
# gate's ``design_scope`` check park the run. They are excluded per checkout, in
# ``.git/info/exclude``: a local file git never commits, so the project's own .gitignore is
# left alone. Root-anchored, so a project's real ``src/.env`` is untouched.
RUNNER_EXCLUDE_HEADER = (
    "# sdlc framework: entries the phase job leaves in the checkout "
    "(first live design run, 2026-09-21)"
)
# No trailing slash on the directory entries: ``/.idea/`` excludes a directory only, and the
# sandbox may leave a *file* of that name (third live design run, 2026-09-21). ``/.idea``
# matches both.
RUNNER_EXCLUDES = (
    "/framework/",
    "/.bash_profile",
    "/.bashrc",
    "/.env",
    "/.gitconfig",
    "/.gitmodules",
    "/.idea",
    "/.mcp.json",
    "/.profile",
    "/.ripgreprc",
    "/.vscode",
    "/.zprofile",
    "/.zshrc",
)


def write_git_exclude(root: Path) -> dict[str, Any]:
    """Append the runner's own untracked entries to ``<root>/.git/info/exclude``.

    Idempotent: an entry the file already carries is not written again, so a second run of
    the same checkout adds nothing.
    """
    from state import gitops

    out: dict[str, Any] = {"added": [], "path": None}
    if not gitops.is_repo(root):
        return {**out, "note": "not a git checkout: nothing to exclude"}
    git_dir = Path(root) / ".git"
    if git_dir.is_file():  # a worktree or submodule: .git points at the real directory
        return {**out, "note": ".git is a file (worktree): the exclude file was not touched"}
    path = git_dir / "info" / "exclude"
    out["path"] = str(path)
    try:
        current = path.read_text(encoding="utf-8") if path.is_file() else ""
        have = {line.strip() for line in current.splitlines()}
        missing = [entry for entry in RUNNER_EXCLUDES if entry not in have]
        if not missing:
            return out
        body = "" if not current or current.endswith("\n") else "\n"
        if RUNNER_EXCLUDE_HEADER not in have:
            body += RUNNER_EXCLUDE_HEADER + "\n"
        body += "".join(f"{entry}\n" for entry in missing)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(body)
    except OSError as exc:
        return {**out, "note": f"could not write the exclude file: {exc}"}
    return {**out, "added": missing}


# --- the project's own toolchain (third live design run, 2026-09-21) -------------------------
# The phase job installs it in a workflow step, but the workflow files a project carries are
# the copies /sdlc-init wrote when it ran: a project initialised with an older framework never
# gets the step, and its gate fails on "No module named pytest". The run therefore installs
# the toolchain itself, before the guard reads anything. Both are idempotent, so a checkout
# whose workflow already ran the step pays only the cost of a no-op install.
SETUP_FAILED = "the project's setup command failed: {reason}"


def install_toolchain(root: Path, dry_run: bool = False) -> tuple[dict[str, Any], bool]:
    """Run ``sdlc.yaml: commands.setup`` in ``root``. (result, ok).

    A project with no setup command is skipped, not failed; a dry run installs nothing.
    """
    if dry_run:
        return {"skipped": "dry run: nothing is installed"}, True
    try:
        result, code = project_setup.run_setup(root)
    except Exception as exc:  # noqa: BLE001 — an install must not crash the run silently
        return {"error": f"{type(exc).__name__}: {exc}"}, False
    return result, code == project_setup.EXIT_OK


def setup_failure_reason(result: dict[str, Any]) -> str:
    """The one line the run prints on stderr when the setup command failed."""
    if result.get("error"):
        return str(result["error"])
    command = result.get("command", "")
    tail = str(result.get("output", "")).strip().splitlines()[-1:] or [""]
    return f"{command} exited {result.get('exit_code')}: {tail[0]}"


# --- the work branch ----------------------------------------------------------------------
# The phase whose branch a run works on. A ``workflow_dispatch`` run starts on the default
# branch, where ``status.yaml`` is whatever main says, so every run puts the checkout on the
# change's own branch before the guard reads anything (OPERATING_MODEL section 8).
BRANCH_PHASE = {"review": "e"}  # the review pass runs on the build PR's branch (f: sdlc/<id>/a)
CREATES_ITS_BRANCH = ("b", "c")  # (d), (e) and the review pass need sdlc/<id>/c to exist


def work_branch_for(change_id: str, phase: str) -> str:
    return c.work_branch(change_id, BRANCH_PHASE.get(phase, phase))


def fix_branch_for(root: Path, change_id: str, head_ref: str | None) -> tuple[str, str | None]:
    """(the branch a fix round runs on, the change's phase as the checkout says it).

    The PR's own head when the event named one (``--head-ref``; a web-session intent PR has
    a ``claude/...`` head and no ``sdlc/<id>/a``), else the work branch of the phase
    ``status.yaml`` is at on the current checkout (a ``workflow_dispatch`` re-run).
    """
    phase = None
    change_dir = c.find_change_dir(root, change_id)
    if change_dir is not None:
        try:
            phase = status_mod.read_status(change_dir).phase
        except (OSError, ValueError):
            phase = None
    head = (head_ref or "").strip()
    if head:
        return head, phase
    if phase in FIX_PHASES:
        return c.work_branch(change_id, phase), phase
    return c.work_branch(change_id, "a"), phase


def _git_ok(root: Path, *args: str) -> bool:
    from state import gitops

    try:
        gitops.run(root, *args)
    except (gitops.GitError, OSError):
        return False
    return True


def gitops_current_branch(root: Path) -> str | None:
    from state import gitops  # noqa: PLC0415

    try:
        return gitops.current_branch(root) if gitops.is_repo(root) else None
    except Exception:  # noqa: BLE001
        return None


def _ref_exists(root: Path, ref: str) -> bool:
    from state import gitops

    return bool(gitops.run(root, "rev-parse", "--verify", "--quiet", ref, check=False).strip())


def checkout_profile(root: Path, change_id: str) -> str | None:
    """The change's effective profile as the current checkout says it (``sdlc.yaml: profile``
    and the change's ``status.yaml: profile_override``); None when it cannot be read.

    ``prepare_branch`` calls it before it switches, so it reads the default branch the run
    started on: the owner's merged ``sdlc.yaml`` and the merged intent's status."""
    override = None
    change_dir = c.find_change_dir(root, change_id)
    if change_dir is not None:
        try:
            override = status_mod.read_status(change_dir).profile_override
        except (OSError, ValueError):
            override = None
    try:
        return c.effective_profile(_config(root).get("profile"), override)
    except ValueError:
        return None


def _start_point(root: Path, change_id: str, phase: str, profile: str | None) -> str | None:
    """Where a missing work branch starts: the default branch, in every profile. The owner's
    merge at gate (b) put the approved spec and plan there, and a design branch left behind
    after that merge lacks the default branch's later commits and may carry commits made
    after the merge (PROGRESS known gaps, ninth live run; HANDOFF 6(a)). Until 0.2.14 the
    Lite profile started ``sdlc/<id>/c`` from ``sdlc/<id>/b``; Lite is gone (decision 21).
    ``change_id``, ``phase`` and ``profile`` are kept for the callers' symmetry."""
    del change_id, phase, profile
    base = gate_diff.default_base(root)
    return base if base and _ref_exists(root, base) else None


def prepare_branch(
    root: Path,
    change_id: str,
    phase: str,
    profile: str | None = None,
    branch: str | None = None,
) -> dict[str, Any]:
    """Put the checkout on the branch this phase works on, creating it for (b) and (c).

    Without this a dispatched run reads main's ``status.yaml`` and skips every phase past
    (c), and a park would have no branch to commit its own evidence on. ``profile`` decides
    where a new ``sdlc/<id>/c`` starts (``_start_point``); when it is not given it is read
    from the checkout before anything is switched (``checkout_profile``). ``branch`` names
    the branch outright (a fix round: the PR's own head), which is never created.
    """
    from state import gitops

    if profile is None:
        profile = checkout_profile(root, change_id)
    named = bool(branch)
    branch = branch or work_branch_for(change_id, phase)
    out: dict[str, Any] = {"branch": branch, "switched": False}
    if not gitops.is_repo(root):
        return {**out, "note": "not a git checkout: the current directory is used as it is"}
    if gitops.has_remote(root):
        gitops.run(root, "fetch", "origin", check=False)
    if gitops.current_branch(root) == branch:
        return {**out, "switched": True, "note": "already on the work branch"}
    if _ref_exists(root, f"refs/heads/{branch}"):
        return {**out, "switched": _git_ok(root, "checkout", branch), "from": "local"}
    if _ref_exists(root, f"refs/remotes/origin/{branch}"):
        ok = _git_ok(root, "checkout", "-b", branch, "--track", f"origin/{branch}")
        return {**out, "switched": ok, "from": f"origin/{branch}"}
    if named:
        return {**out, "note": f"{branch} does not exist: the pull request's head is gone"}
    if phase not in CREATES_ITS_BRANCH:
        return {**out, "note": f"{branch} does not exist: the build phase has not run yet"}
    start = _start_point(root, change_id, phase, profile)
    if start is None:
        return {**out, "note": "no base branch to create the work branch from"}
    return {**out, "switched": _git_ok(root, "checkout", "-b", branch, start), "from": start}


# --- the guardrails on the branch (decision 6, layer iii: prevention) -------------------------
GUARDRAIL_PARK = "guardrail file changed on the branch: {files}; CI refuses to run a phase on it"
NO_MERGE_BASE_PARK = (
    "no merge base with {base}: the branch shares no commit with the default branch, so its "
    "guardrail edits cannot be judged; CI refuses to run a phase on it"
)


class NoMergeBase(Exception):
    """The default branch exists but HEAD shares no history with it (an orphan branch, a
    shallow clone that stopped short of the fork point): the committed diff is empty for
    the wrong reason, so nothing judged on it may pass (readiness review, group B)."""

    def __init__(self, base: str) -> None:
        super().__init__(NO_MERGE_BASE_PARK.format(base=base))
        self.base = base


def _committed_diff(root: Path) -> tuple[list[str], str | None]:
    """(files changed against the base branch, the merge base) — committed changes only.
    Raises ``NoMergeBase`` when a base exists and shares no commit with HEAD; with no base
    at all (no remote, no main or master) there is nothing to compare with and the list is
    empty, as ``gate/diff.py`` reads it."""
    from state import gitops

    base = gate_diff.default_base(root)
    if base == "HEAD":
        return [], None
    merge_base = gitops.run(root, "merge-base", base, "HEAD", check=False).strip()
    if not merge_base:
        raise NoMergeBase(base)
    out = gitops.run(root, "diff", "--name-only", merge_base, "HEAD", check=False)
    files = [line.strip().replace("\\", "/") for line in out.splitlines() if line.strip()]
    return files, merge_base


def guardrail_changes(root: Path, change_dir: Path, config: dict[str, Any]) -> list[str]:
    """The guardrail files this branch changes, unless intent.md says it is a framework
    change (OPERATING_MODEL section 3). The hook denies such an edit inside a run; this is
    the same rule applied to a branch the run inherits. Raises ``NoMergeBase`` (the caller
    parks) when the branch shares no history with the default branch."""
    from hooks import protected_paths as pp

    if not gate_diff.is_repo(root):
        return []
    files, merge_base = _committed_diff(root)
    if not files:
        return []
    try:
        patterns = pp.protected_patterns(config)
    except ConfigError:
        patterns = list(pp.ALWAYS_PROTECTED)
    hits = sorted({f for f in files if any(matches(p, f) for p in patterns)})
    if not hits:
        return []
    try:
        rel = Path(change_dir).resolve().relative_to(Path(root).resolve()).as_posix()
    except ValueError:
        rel = ""
    base_intent = gate_diff.file_at(root, merge_base, f"{rel}/intent.md") if rel else None
    if base_intent and art.is_framework_change(base_intent):
        return []
    return hits


# --- the guard --------------------------------------------------------------------------------
def resolve_change_id(change_id: str | None, head_ref: str | None, run_phase: str) -> tuple:
    """(change id, skip reason). The id comes from ``--id`` or from ``sdlc/<id>/<phase>``."""
    if change_id:
        if not c.ID_RE.match(change_id):
            return None, f"change id {change_id!r} is not four digits"
        return change_id, None
    parsed = c.parse_branch(head_ref or "")
    if parsed is None:
        return None, "no change id: neither --id nor a head ref of the form sdlc/<id>/<phase>"
    parsed_id, branch_phase = parsed
    expected = PREVIOUS_PHASE[run_phase]
    if expected is not None and branch_phase != expected:
        return None, f"head branch {head_ref} is phase {branch_phase}, not {expected}"
    return parsed_id, None


# A merged pull request names its change by the folder it touches (HANDOFF 4(a)): the web
# platform pushes /sdlc-plan's intent to a branch of its own (``claude/...``), so the head
# name of a merged intent PR says nothing about the change.
CHANGE_FOLDER_RE = re.compile(r"^changes/(\d{4})-[^/]+/")


def _pr_number(value: Any) -> int | None:
    text = str(value or "").strip().lstrip("#")
    return int(text) if text.isdigit() and int(text) > 0 else None


def find_change(
    run_phase: str,
    change_id: str | None,
    head_ref: str | None,
    repo: str,
    pr_number: Any,
    env: dict[str, str],
) -> tuple[str | None, str | None]:
    """(change id, skip reason) for the run, from the first source that names one:

    1. ``--id`` (a ``workflow_dispatch`` or a by-hand run);
    2. a head ref of the form ``sdlc/<id>/<phase>``. One that names another phase keeps its
       skip reason and is never looked up by its files: it is that phase's own PR (the
       design PR ``sdlc/<id>/b`` also fires the design workflow when it merges), and its
       files carry the same change folder, so the lookup would re-run a merged phase;
    3. the merged pull request's files: exactly one ``changes/<id>-<slug>/`` folder names
       the change; none, several or no route to GitHub is a skip with the reason.

    ``env`` is the run's environment; the GitHub client reads its own token from the
    process environment, as every other call here does.
    """
    if change_id:
        return resolve_change_id(change_id, None, run_phase)
    if c.parse_branch(head_ref or "") is not None:
        return resolve_change_id(None, head_ref, run_phase)
    number = _pr_number(pr_number)
    if number is None:
        if str(pr_number or "").strip():
            return None, f"--pr-number {pr_number!r} is not a pull request number"
        return None, (
            "no change id: neither --id, a head ref of the form sdlc/<id>/<phase> nor --pr-number"
        )
    github = _github()
    if github is None:
        return None, "plugin/pr/github.py is not available"
    if not repo:
        return None, f"--repo is needed to read the files of pull request #{number}"
    listed = github.pr_files(repo, number)
    if not listed.get("ok"):
        why = listed.get("reason") or "failed"
        return None, f"the files of pull request #{number} could not be read: {why}"
    ids = sorted(
        {m.group(1) for f in listed.get("files") or [] if (m := CHANGE_FOLDER_RE.match(str(f)))}
    )
    if not ids:
        return None, f"pull request #{number} touches no changes/<id>-<slug>/ folder"
    if len(ids) > 1:
        return None, (
            f"pull request #{number} touches {len(ids)} change folders ({', '.join(ids)}): "
            "ambiguous, run the phase with --id"
        )
    return ids[0], None


def print_found_change(args, env: dict[str, str]) -> int:
    """``--find-change``: the workflow's first step. Prints ``change_id=<id or empty>`` and
    ``reason=<...>`` and appends ``change_id=<id>`` to ``$GITHUB_OUTPUT``, so every later
    step can be skipped for a merge that carries no change (about 20 s of a green job)."""
    change_id, reason = find_change(
        args.phase, args.id, args.head_ref, args.repo, getattr(args, "pr_number", None), env
    )
    found = change_id or ""
    print(f"change_id={found}")
    print("reason=" + " ".join(str(reason or "").split()))
    output = env.get("GITHUB_OUTPUT")
    if output:
        try:
            with open(output, "a", encoding="utf-8", newline="\n") as handle:
                handle.write(f"change_id={found}\n")
        except OSError as exc:  # later steps would be skipped silently: say so, fail
            print(f"could not write {output}: {exc}", file=sys.stderr)
            return EXIT_FAILED
    return EXIT_OK


def rerun_reason(
    root: Path, change_id: str, run_phase: str, repo: str, env: dict[str, str]
) -> str | None:
    """None when a run of ``run_phase`` may repeat on its existing work branch.

    The branch carries this phase's result but no open pull request: the earlier attempt
    never reached the queue (the fifth live design run of 2026-09-21 pushed ``sdlc/0001/b``
    and was refused the PR; the next dispatch then skipped with "at phase b, not a", and
    nothing could move the change). A branch whose pull request exists is a queue item:
    review comments go through ``/sdlc-fix``, not a second run. With no route to GitHub the
    question cannot be answered, so the run skips (fail closed).
    """
    head = work_branch_for(change_id, run_phase)
    github = _github()
    at = f"change {change_id} is already at phase {run_phase} on {head}"
    if github is None or not repo or (not _token(env) and not github.gh_path()):
        return f"{at}, and no GitHub route can tell whether its pull request exists"
    found = github.find_open_pr(repo, head, cwd=root)
    if found.get("number"):
        return (
            f"{at}; pull request #{found['number']} carries it (review comments go through "
            "/sdlc-fix, not a second run)"
        )
    if not found.get("ok", True) and found.get("reason"):
        return f"{at}, and the pull request lookup failed: {found['reason']}"
    return None


def _approved_ref(root: Path) -> str | None:
    """The remote-tracking ref of the default branch — where the copies the owner approved
    live — or None when the checkout has no such ref to read (a by-hand run without a remote,
    or a remote that has no such branch; a guessed name that is a framework branch or the
    current branch, which is nobody's approved copy). Shared by ``_approved_config`` and
    ``approved_overrides``."""
    from state import gitops  # noqa: PLC0415

    try:
        name = gitops.default_branch(root) if gitops.is_repo(root) else ""
    except Exception:  # noqa: BLE001 - no git, no remote: the checkout's copy is all there is
        name = ""
    if not name or name.startswith("sdlc/") or c.parse_branch(name):
        return None
    if not gitops.explicit_default_branch() and name not in ("main", "master"):
        # the guess fell through to the current branch (no origin/HEAD, no main or master):
        # on a PR head such as a web session's ``claude/…`` that is the branch's own copy
        try:
            if name == gitops.current_branch(root):
                return None
        except Exception:  # noqa: BLE001
            return None
    ref = f"refs/remotes/origin/{name}"
    return ref if _ref_exists(root, ref) else None


def _approved_config(root: Path) -> dict[str, Any]:
    """``sdlc.yaml`` as the default branch carries it — the copy the owner approved — when
    the checkout has that remote-tracking ref; else the checkout's copy (a by-hand run
    without a remote, a project not yet initialised on its default branch).

    The guard used to read the checkout's copy, which ``prepare_branch`` had already
    switched to the work branch: ``paused: true`` merged on the default branch stopped
    nothing in flight, and a branch could carry its own ``profile`` (OPERATING_MODEL
    section 4.2: the guard reads the "base branch copy of sdlc.yaml"; 1.0.0 readiness
    review, 2026-09-26). The default branch is named by ``SDLC_DEFAULT_BRANCH`` or guessed
    (``state/gitops.default_branch``); a guess that lands on a framework branch is refused,
    since a work branch's copy is not the owner's."""
    from state import yamlish  # noqa: PLC0415

    ref = _approved_ref(root)
    if ref is None:
        return _config(root)
    text = gate_diff.file_at(root, ref, SDLC_FILE)
    if text is None:
        return _config(root)
    try:
        data = yamlish.loads(text)
    except Exception:  # noqa: BLE001 - the same as an unreadable checkout copy (_config)
        return {}
    return data if isinstance(data, dict) else {}


class ApprovedCopyUnreadable(RuntimeError):
    """The default branch's ``status.yaml`` exists and cannot be read: fail closed (the
    review of the 0.2.26 diff, L3 — a None here read as "no override" and dropped the
    owner's ``profile_override: full``)."""


def _approved_status(root: Path, change_dir: Path):
    """The change's ``status.yaml`` as the default branch carries it (the copy the owner
    approved at gate (a) or a later merge), or None: no remote-tracking ref (by hand) or
    the folder not on the default branch yet (an intent PR before its merge). An unreadable
    copy raises ``ApprovedCopyUnreadable`` (an old plugin's schema still reads: unknown keys
    apart, ``Status.from_dict`` defaults the missing ones)."""
    from state import yamlish  # noqa: PLC0415

    ref = _approved_ref(root)
    if ref is None:
        return None
    rel = f"{c.CHANGES_DIR}/{change_dir.name}/{status_mod.STATUS_FILE}"
    text = gate_diff.file_at(root, ref, rel)
    if text is None:
        return None
    try:
        return status_mod.Status.from_dict(yamlish.loads(text))
    except Exception as exc:  # noqa: BLE001
        raise ApprovedCopyUnreadable(f"{rel} on the default branch is unreadable: {exc}") from exc


def approved_overrides(
    root: Path, change_dir: Path, st, env: dict[str, str] | None = None
) -> tuple[str | None, str | None, str]:
    """``(profile_override, review_override, note)`` the run judges by: the default branch's
    copy of ``status.yaml`` when the checkout has one (choice 103; the 1.0.0 readiness
    review: a branch that wrote ``profile_override: standard`` skipped the Full profile's
    (c)/(d) label gates, and ``review_override: deferred`` sent the park items to the
    panel). The branch's own values are ignored and the note says so when they differ. A
    folder not on the default branch yet has no approved override (None). Without a
    remote-tracking ref the checkout's values stand by hand only; on a runner
    (``GITHUB_ACTIONS``) no override applies, since the branch's copy is nobody's approval.
    An unreadable approved copy raises (``ApprovedCopyUnreadable``): the caller refuses."""
    if _approved_ref(root) is None:
        if (env if env is not None else os.environ).get("GITHUB_ACTIONS"):
            return None, None, "no default branch ref on the runner: no override applies"
        return st.profile_override, st.review_override, ""
    approved = _approved_status(root, change_dir)
    profile = approved.profile_override if approved is not None else None
    review = approved.review_override if approved is not None else None
    ignored = [
        f"{name} {branch!r} on the branch ignored ({expected!r} on the default branch)"
        for name, branch, expected in (
            ("profile_override", st.profile_override, profile),
            ("review_override", st.review_override, review),
        )
        if branch != expected
    ]
    return profile, review, "; ".join(ignored)


def guard(root: Path, change_id: str, run_phase: str, repo: str, env: dict[str, str]):
    """(change_dir, status, config, skip reason)."""
    config = _approved_config(root)
    try:
        paused = config_flag(config, "paused")
    except ConfigError as exc:
        return None, None, config, f"{exc}: nothing runs until it is fixed"
    if paused:
        return None, None, config, "sdlc.yaml says paused: true"
    change_dir = c.find_change_dir(root, change_id)
    if change_dir is None:
        return None, None, config, f"no change folder for id {change_id}"
    try:
        st = status_mod.read_status(change_dir)
    except (OSError, ValueError) as exc:
        return None, None, config, f"status.yaml is unreadable: {exc}"
    if st.abandoned:  # decision 25: every workflow skips an abandoned change
        return None, None, config, f"change {change_id} is abandoned: {st.abandoned_reason}"
    if run_phase == "fix":
        # a fix round runs on the phase the change is in, parked or not: the park is a change
        # request from the gate (/sdlc-fix step 1), and the owner's un-park label was read
        # before this guard. No gate needs to have passed and no approval label is read.
        if st.phase not in FIX_PHASES:
            return None, None, config, f"change {change_id} is at phase {st.phase}: no fix round"
        return change_dir, st, config, None
    expected = PREVIOUS_PHASE[run_phase]
    if st.phase == run_phase and run_phase in CREATES_ITS_BRANCH:
        # the work branch already carries this phase: a re-run, allowed only when no pull
        # request carries it (the earlier attempt never reached the queue)
        reason = rerun_reason(root, change_id, run_phase, repo, env)
        if reason:
            return None, None, config, reason
        st.set_phase(run_phase)  # clears the earlier attempt's park; the phase is unchanged
        status_mod.write_status(change_dir, st)
    else:
        accepted = PHASE_BEFORE.get(run_phase, (expected,))
        if st.phase not in accepted:
            return None, None, config, f"change {change_id} is at phase {st.phase}, not {expected}"
        if run_phase == "b" and st.phase == "f":
            # the owner merged the incident intent PR: that merge is gate (a) of the change
            # (decision 25) and lifts the park the maintain run left ("Go requested", a
            # refused proposal) - the owner chose the pipeline over the runbook. The file on
            # the work branch is set to phase a with gate (a) passed before the session
            # starts, because the model reads the raw file: the design run of 2026-09-25
            # (change 0005) read ``phase: f`` and refused ("nothing for /sdlc-design to do").
            # The session's own ``commit-phase --phase b`` moves it on to b.
            st = status_mod.merged_at_gate_a(st)
            st.set_phase("a")  # also clears the park
            status_mod.write_status(change_dir, st)
        # ``read_status`` ignores a park that a later gate result lifted (plugins before
        # 0.2.6 left the reason behind a ``passed`` result); the file on the work branch is
        # rewritten to say the same, because the session reads it itself: the ninth live
        # run (2026-09-22, phase (c)) passed this guard and then refused on the raw field
        status_mod.lift_stale_park(change_dir)
        if st.parked_reason:
            return None, None, config, f"change {change_id} is parked: {st.parked_reason}"
    if run_phase in GATE_MUST_HAVE_PASSED:
        if st.gate.phase != expected or st.gate.result != "passed":
            return (
                None,
                None,
                config,
                f"gate ({expected}) has not passed for change {change_id} "
                f"(gate: {st.gate.phase}/{st.gate.result})",
            )
    # the Full profile's label gates are judged by the override the owner approved, not the
    # branch's (0.2.26; a branch writing ``profile_override: standard`` skipped them before)
    try:
        profile_override, _review, note = approved_overrides(root, change_dir, st, env)
    except ApprovedCopyUnreadable as exc:
        return None, None, config, f"{exc}: nothing runs until it is fixed"
    if note:
        print(f"status.yaml: {note}", file=sys.stderr)
    profile = c.effective_profile(config.get("profile"), profile_override)
    if profile == "full" and run_phase in APPROVAL_LABEL:
        reason = check_approval(repo, change_id, run_phase, env)
        if reason:
            return None, None, config, reason
    return change_dir, st, config, None


# --- the claude command -----------------------------------------------------------------------
def _python() -> str:
    return sys.executable or "python"


def review_prompt(plugin_dir: Path, root: Path, change_id: str) -> tuple[str | None, str]:
    """The review prompt, printed by ``review/cli.py prompt`` (decision 12)."""
    cli = plugin_dir / "plugin" / "review" / "cli.py"
    argv = [_python(), str(cli), "prompt", "--root", str(root), "--id", change_id]
    try:
        proc = subprocess.run(argv, capture_output=True, text=True, encoding="utf-8", timeout=120)
    except (OSError, subprocess.SubprocessError) as exc:
        return None, f"review/cli.py prompt could not run: {exc}"
    if proc.returncode != 0 or not proc.stdout.strip():
        return None, f"review/cli.py prompt exited {proc.returncode}: {proc.stderr.strip()}"
    return proc.stdout.strip(), ""


# --- the CI settings, anchored to the project (permissions reference; NOTES 6 and 12) ---------
_ANCHORED_RULE = re.compile(r"^(Read|Edit)\(/(?!/)(.*)\)$")


def _posix_root(resolved: str) -> str:
    """A resolved project root as a ``//`` absolute permission path. Claude Code normalises
    Windows paths to POSIX form before matching (``C:\\Users\\alice`` becomes
    ``/c/Users/alice``), so ``C:/work/proj`` gives ``//c/work/proj`` and ``/home/r/proj``
    gives ``//home/r/proj``."""
    p = resolved.replace("\\", "/").rstrip("/")
    if len(p) >= 2 and p[1] == ":":
        p = "/" + p[0].lower() + p[2:]
    return "/" + p


def _absolute_rule_root(root: Path) -> str:
    return _posix_root(Path(root).resolve().as_posix())


def _absolute_rule(rule: str, base: str) -> str:
    m = _ANCHORED_RULE.match(rule)
    return f"{m.group(1)}({base}/{m.group(2)})" if m else rule


def ci_settings_file(plugin_dir: Path, root: Path) -> Path:
    """``settings.ci.json`` with its ``/``-anchored path rules resolved against the project
    root, written to a temporary copy. A ``/path`` rule anchors at the directory of the
    settings file that defines it, and for a ``--settings`` file that is the file's own
    directory (the permissions reference), so ``Edit(/CLAUDE.md)`` left in the framework
    checkout would guard ``plugin/ci/CLAUDE.md``, not the project's guardrail file. The copy
    carries ``Edit(//<absolute project root>/CLAUDE.md)`` instead; every other rule is kept."""
    source = Path(plugin_dir).joinpath(*SETTINGS_REL)
    data = json.loads(source.read_text(encoding="utf-8"))
    base = _absolute_rule_root(root)
    perms = data.get("permissions") or {}
    for key in ("deny", "ask", "allow"):
        if isinstance(perms.get(key), list):
            perms[key] = [_absolute_rule(r, base) for r in perms[key]]
    out = Path(tempfile.mkdtemp(prefix="sdlc-ci-")) / source.name
    out.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return out


def claude_prefix(claude: str) -> list[str]:
    """``--claude`` as an argv prefix: a ``.py`` file runs through this interpreter (the
    tests' fake, as ``evals/run.py`` takes it since 0.2.19; on Windows a ``.cmd`` launcher
    hands a multi-line prompt to cmd.exe, which does not carry it — the first Windows run
    of the suite, 0.2.28); anything else is the executable as given, resolved by the OS."""
    if claude.lower().endswith(".py"):
        return [sys.executable, claude]
    return [claude]


def compose(
    *,
    claude: str,
    plugin_dir: Path,
    phase: str,
    prompt: str,
    permission_mode: str,
    config: dict[str, Any],
    env: dict[str, str],
    root: Path | None = None,
) -> list[str]:
    """The full argv of one headless run. It carries no secret, so it is safe to print.
    With ``root`` the CI settings are rendered against the project (``ci_settings_file``);
    without it the file is passed as is."""
    # The prompt goes right after -p: --allowedTools / --disallowedTools take a list of
    # values, so a prompt placed after them is read as one more tool name and the CLI
    # answers "Input must be provided either through stdin or as a prompt argument"
    # (observed on the first live design run, 2026-09-21).
    argv = [*claude_prefix(claude), "-p", prompt, *auth_mod.flags(env)]
    argv += ["--plugin-dir", str(plugin_dir)]
    if root:
        settings = ci_settings_file(plugin_dir, root)
    else:
        settings = Path(plugin_dir).joinpath(*SETTINGS_REL)
    argv += ["--settings", str(settings)]
    argv += ["--permission-mode", permission_mode]
    argv += ["--permission-prompts", "none"]  # nobody is there to answer (NOTES 10b)
    gate_cfg = _gate_settings(config)
    argv += ["--max-turns", str(_int_or(gate_cfg.get("max_turns"), DEFAULT_MAX_TURNS))]
    budget = gate_cfg.get("max_budget_usd")
    if budget not in (None, "", "null"):
        argv += ["--max-budget-usd", str(budget)]
    argv += ["--output-format", "json"]
    model = env.get("SDLC_MODEL")
    if model:
        argv += ["--model", model]
    if phase == "b":
        argv += ["--allowedTools", DESIGN_ALLOWED_TOOLS]
        argv += ["--disallowedTools", DESIGN_DISALLOWED_TOOLS]
    elif phase in ("c", "d", "e", "fix"):
        # a fix round edits the phase's artifact (intent.md, spec.md, code) and re-runs the
        # toolchain; at (a) and (b) the gate's design_scope and guardrails checks still
        # refuse a source file it should not have touched
        argv += ["--allowedTools", IMPLEMENT_ALLOWED_TOOLS]
        argv += ["--disallowedTools", IMPLEMENT_DISALLOWED_TOOLS]
    elif phase == "review":
        argv += ["--allowedTools", REVIEW_ALLOWED_TOOLS]
        argv += ["--disallowedTools", REVIEW_DISALLOWED_TOOLS]
    elif phase == "f":
        argv += ["--allowedTools", maintain_allowed_tools(root)]
        argv += ["--disallowedTools", MAINTAIN_DISALLOWED_TOOLS]
    elif phase == "triage":
        argv += ["--allowedTools", TRIAGE_ALLOWED_TOOLS]
        argv += ["--disallowedTools", TRIAGE_DISALLOWED_TOOLS]
    return argv


def maintain_allowed_tools(root: Path | None) -> str:
    """The maintain run's tools: bands.yaml's diagnose tools plus the plugin's own."""
    from detect import bands as bands_mod  # noqa: PLC0415
    from detect import cli as detect_cli  # noqa: PLC0415

    bands = None
    if root is not None:
        try:
            bands = bands_mod.load_project(Path(root))
        except bands_mod.BandsError:
            bands = None
    return detect_cli.maintain_tools(bands)


def invoke(argv: list[str], root: Path, env: dict[str, str], timeout: int) -> tuple:
    """(result dict or None, stdout, stderr, exit code)."""
    try:
        proc = subprocess.run(
            argv,
            cwd=str(root),
            capture_output=True,
            text=True,
            encoding="utf-8",
            env=auth_mod.credential_env(env),
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return None, "", f"claude did not finish within {timeout}s", 124
    except OSError as exc:
        return None, "", f"claude could not start: {exc}", 127
    try:
        data = json.loads(proc.stdout)
    except ValueError:
        data = None
    return data, proc.stdout, proc.stderr, proc.returncode


# --- spend, evidence, hand-over ------------------------------------------------------------------
def run_record_paths(change_dir: Path, phase: str) -> tuple[Path, Path]:
    """(result, stderr) paths for this run of the phase: ``claude-<phase>.json`` for the
    first run, ``claude-<phase>-<n>.json`` for the n-th, so no run's record overwrites an
    earlier one and every transcript in ``evidence/`` says which run it belongs to."""
    evidence = change_dir / art.EVIDENCE_DIR
    first = evidence / CLAUDE_RESULT_FILE.format(phase=phase)
    if not first.exists():
        return first, evidence / CLAUDE_STDERR_FILE.format(phase=phase)
    n = 2
    while (evidence / CLAUDE_RUN_FILE.format(phase=phase, n=n)).exists():
        n += 1
    return (
        evidence / CLAUDE_RUN_FILE.format(phase=phase, n=n),
        evidence / CLAUDE_RUN_STDERR_FILE.format(phase=phase, n=n),
    )


def store_result(
    change_dir: Path, phase: str, data: Any, raw: str, path: Path | None = None
) -> Path:
    path = path or run_record_paths(change_dir, phase)[0]
    path.parent.mkdir(parents=True, exist_ok=True)
    body = json.dumps(data, indent=2, sort_keys=True) if data is not None else raw
    path.write_text(body + "\n", encoding="utf-8", newline="\n")
    return path


def store_stderr(change_dir: Path, phase: str, err: str, path: Path | None = None) -> Path | None:
    """The CLI's stderr next to its result: permission denials, ignored settings and the
    like are printed there and nowhere else (the eighth live run, 2026-09-22, ended in 28 s
    with nothing to read)."""
    if not (err or "").strip():
        return None
    path = path or run_record_paths(change_dir, phase)[1]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(err, encoding="utf-8", newline="\n")
    return path


def report_failed_run(
    root: Path, change_dir: Path, phase: str, data: Any, raw: str, err: str, why: str
) -> None:
    """A run that ends without its gate is an infrastructure failure: say why, show the
    CLI's last message, its counters and its stderr, and commit the stored result and
    stderr on the work branch so they outlive the runner."""
    print(why, file=sys.stderr)
    if isinstance(data, dict):
        counters = {
            k: data.get(k)
            for k in ("num_turns", "duration_ms", "total_cost_usd", "is_error", "subtype")
        }
        print(f"claude result: {json.dumps(counters)}", file=sys.stderr)
        text = str(data.get("result") or "")
    else:
        text = raw or ""
    if text.strip():
        print("claude's last message:\n" + text[-3000:], file=sys.stderr)
    if (err or "").strip():
        print("claude stderr:\n" + err[-3000:], file=sys.stderr)
    from state import gitops

    if not gitops.is_repo(root):
        return
    try:
        rel = str(change_dir.relative_to(root)).replace("\\", "/")
        sha = gitops.commit_paths(root, [rel], f"run({phase}): failed run record")
        if sha and gitops.has_remote(root):
            gitops.push(root, gitops.current_branch(root))
    except (gitops.GitError, OSError) as exc:
        print(f"the failed run record could not be committed: {exc}", file=sys.stderr)


def record_spend(plugin_dir: Path, root: Path, change_id: str, phase: str, usd: float) -> bool:
    cli = plugin_dir / "plugin" / "gate" / "cli.py"
    argv = [
        _python(), str(cli), "record-spend",
        "--root", str(root), "--id", change_id,
        "--phase", SPEND_PHASE.get(phase, phase), "--usd", str(usd),
    ]  # fmt: skip
    try:
        proc = subprocess.run(argv, capture_output=True, text=True, encoding="utf-8", timeout=120)
    except (OSError, subprocess.SubprocessError):
        return False
    return proc.returncode == 0


def validate_review(plugin_dir: Path, root: Path, change_id: str) -> dict[str, Any]:
    cli = plugin_dir / "plugin" / "review" / "cli.py"
    argv = [_python(), str(cli), "validate", "--root", str(root), "--id", change_id]
    try:
        proc = subprocess.run(argv, capture_output=True, text=True, encoding="utf-8", timeout=600)
    except (OSError, subprocess.SubprocessError) as exc:
        return {"ok": False, "reason": str(exc)}
    return {"ok": proc.returncode == 0, "exit_code": proc.returncode}


def read_gate(change_dir: Path, phase: str) -> dict[str, Any] | None:
    path = change_dir / art.EVIDENCE_DIR / art.GATE_RESULT.format(phase=phase)
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def dispatch(repo: str, workflow: str, ref: str, change_id: str, head_ref: str) -> dict[str, Any]:
    """``POST /repos/{repo}/actions/workflows/{file}/dispatches`` — 204 means accepted.

    ``workflow_dispatch`` is one of the two events GitHub still starts a run for when the
    workflow token causes it, which is why every automated transition goes through here.
    ``head_ref`` is the work branch of the phase being dispatched; the workflow keys its
    concurrency group on it, so every run of one change serialises (section 4.2).
    """
    github = _github()
    if github is None:
        return {"ok": False, "reason": "plugin/pr/github.py is not available"}
    tok = github.token()
    if not tok:
        return {"ok": False, "reason": "no GITHUB_TOKEN/GH_TOKEN to dispatch with"}
    url = f"{github.API_ROOT}/repos/{repo}/actions/workflows/{workflow}/dispatches"
    inputs = {"change_id": change_id, "head_ref": head_ref}
    result = github._request("POST", url, tok, {"ref": ref, "inputs": inputs})
    ok = result.get("status") == 204 or not result.get("error")
    return {"ok": ok, "status": result.get("status"), "reason": result.get("error", "")}


# --- the triage step (article p.41) ---------------------------------------------------------------
def run_triage(args, env: dict[str, str]) -> int:
    if not args.log:
        print("--phase triage needs --log <file>", file=sys.stderr)
        return EXIT_USAGE
    if auth_mod.choose_auth(env)["auth"] is None:
        return _skip(auth_mod.choose_auth(env)["reason"])
    root = Path(args.root).resolve()
    argv = compose(
        claude=args.claude,
        plugin_dir=Path(args.plugin_dir).resolve(),
        phase="triage",
        prompt=TRIAGE_PROMPT.format(log=args.log),
        permission_mode="default",
        config=_config(root),
        env=env,
        root=root,
    )
    if args.dry_run:
        _emit({"phase": "triage", "argv": argv})
        return EXIT_OK
    data, raw, err, code = invoke(argv, root, env, run_timeout_seconds(_config(root)))
    text = (data or {}).get("result") if isinstance(data, dict) else raw
    print(text or raw)
    if code != 0 or (isinstance(data, dict) and data.get("is_error")):
        print(err or raw, file=sys.stderr)
        return EXIT_FAILED
    return EXIT_OK


# --- the phase run --------------------------------------------------------------------------------
def run_phase(args, env: dict[str, str]) -> int:
    root = Path(args.root).resolve()
    plugin_dir = Path(args.plugin_dir).resolve()
    phase = args.phase
    ensure_git_identity(root)

    change_id, reason = find_change(
        phase, args.id, args.head_ref, args.repo, getattr(args, "pr_number", None), env
    )
    if reason:
        return _skip(reason)
    excluded = write_git_exclude(root)
    # a fix round (decision 22) runs on the PR's own head, never on a branch of its own
    fix_branch = fix_branch_for(root, change_id, args.head_ref)[0] if phase == "fix" else None
    branch = prepare_branch(root, change_id, phase, branch=fix_branch)
    setup, setup_ok = install_toolchain(root, args.dry_run)
    if not setup_ok:
        reason = setup_failure_reason(setup)
        print(SETUP_FAILED.format(reason=reason), file=sys.stderr)
        _emit({"phase": phase, "change_id": change_id, "setup": setup, "branch": branch})
        return EXIT_FAILED
    change_dir, st, config, reason = guard(root, change_id, phase, args.repo, env)
    if reason:
        return _skip(reason)
    if auth_mod.choose_auth(env)["auth"] is None and not args.dry_run:
        return _skip(auth_mod.choose_auth(env)["reason"])
    # the phase whose gate, evidence and PR this run produces: the change's own phase for a
    # fix round, the run's phase otherwise
    gate_phase = st.phase if phase == "fix" else phase
    # decision 24: the owner's un-park labels on the PR are performed before anything runs
    # and committed on the work branch, so the change request they answer (a park on a
    # risk hit, the iteration cap, a locked test) is settled when the session reads status.yaml
    labels_applied = None
    requests_collected = None
    if phase == "fix" and not args.dry_run:
        labels_applied = apply_owner_labels(
            plugin_dir, root, change_dir, config, args.repo, getattr(args, "pr_number", None),
            gate_phase, fix_branch, env,
        )  # fmt: skip
        st = status_mod.read_status(change_dir)
        # 0.2.24: the reviews and comments reach the session through a file the run wrote,
        # judged by author_association here, never read from the PR by the model itself
        requests_collected = collect_fix_requests(
            root, change_dir, config, args.repo, getattr(args, "pr_number", None), env,
            head_ref=fix_branch,
        )  # fmt: skip
        if not requests_collected.get("ok") and env.get("GITHUB_ACTIONS"):
            # on a runner the file is the session's only source: without it the round would
            # fall back to reading the PR itself (session-8 review), so it parks instead
            parked = park_and_publish(
                plugin_dir, root, change_dir, st, phase,
                FIX_REQUESTS_PARK.format(reason=requests_collected.get("unavailable")),
                branch=fix_branch,
            )  # fmt: skip
            _emit({**parked, "fix_requests": requests_collected, "branch": branch})
            return EXIT_OK

    # the branch itself must be clean of guardrail edits before a run touches it (decision 6)
    try:
        guardrails = guardrail_changes(root, change_dir, config)
        guardrail_park = GUARDRAIL_PARK.format(files=", ".join(guardrails)) if guardrails else ""
    except NoMergeBase as exc:  # an empty diff for the wrong reason never passes
        guardrail_park = str(exc)
    if guardrail_park:
        parked = park_and_publish(
            plugin_dir, root, change_dir, st, phase, guardrail_park, branch=fix_branch
        )
        _emit({**parked, "branch": branch})
        return EXIT_OK

    # phase (c): the preflight decides the permission mode, or parks the change (step 18)
    permission_mode = PERMISSION_MODE.get(phase, "default")
    if phase == "c":
        report = preflight(plugin_dir, root, change_id)
        if not report.get("allow"):
            reasons = report.get("reasons", [])
            parked = park_and_publish(
                plugin_dir, root, change_dir, st, phase, "preflight: " + "; ".join(reasons)
            )
            _emit({**parked, "parked": reasons, "branch": branch})
            return EXIT_OK
        permission_mode = report.get("permission_mode", "acceptEdits")

    if phase == "review":
        prompt, error = review_prompt(plugin_dir, root, change_id)
        if prompt is None:
            print(error, file=sys.stderr)
            return EXIT_FAILED
    else:
        prompt = f"/sdlc:{PHASE_COMMAND[phase]} {change_id}"
        if phase == "f":
            # the model writes the intent and the proposal and stops; the workflow's next
            # step (detect/cli.py finish) dispatches the route with the project's runbook
            # secrets in its own environment, runs gate (f) and opens the PR - nothing that
            # touches a running system runs where the model runs (decisions 11 and 14)
            prompt += " --diagnosis-only"

    argv = compose(
        claude=args.claude,
        plugin_dir=plugin_dir,
        phase=phase,
        prompt=prompt,
        permission_mode=permission_mode,
        config=config,
        env=env,
        root=root,
    )
    if args.dry_run:
        _emit(
            {
                "phase": phase,
                "change_id": change_id,
                "argv": argv,
                "branch": branch,
                "git_exclude": excluded,
                "setup": setup,
            }
        )
        return EXIT_OK

    # only a real run creates the labels it will apply (a dry run contacts nothing)
    labels = ensure_labels(args.repo, env)
    # choice 103: the owner-only fields as they stand when the session starts (the runner's
    # own label handling included) and as the default branch carries them; the baseline's
    # own entries checked against the pull request's label events, the change's remote
    # branches noted, so a push by the session shows
    before_st = status_mod.read_status(change_dir)
    try:
        approved_st = _approved_status(root, change_dir)
    except ApprovedCopyUnreadable as exc:
        return _skip(f"{exc}: nothing runs until it is fixed")
    pr_for_labels = _pr_number(getattr(args, "pr_number", None))
    if pr_for_labels is None and _github() is not None and args.repo:
        pr_for_labels = _pr_number(
            (_github().find_open_pr(args.repo, gitops_current_branch(root), cwd=root) or {}).get(
                "number"
            )
        )
    baseline = baseline_mismatches(
        owner_fields(before_st),
        owner_fields(approved_st) if approved_st is not None else None,
        args.repo, pr_for_labels, env,
    )  # fmt: skip
    if baseline:
        parked = park_and_publish(
            plugin_dir, root, change_dir, before_st, phase,
            OWNER_FIELDS_PARK.format(reasons="; ".join(baseline)),
            branch=fix_branch, check=OWNER_FIELDS_CHECK, need=OWNER_FIELDS_NEED,
        )  # fmt: skip
        _emit({**parked, "owner_fields": {"ok": False, "mismatches": baseline}, "branch": branch})
        return EXIT_OK
    refs_before = change_refs(root, change_id)
    pre_head = gate_diff.head_sha(root) if gate_diff.is_repo(root) else None
    data, raw, err, code = invoke(argv, root, env, run_timeout_seconds(config))
    result_path, stderr_path = run_record_paths(change_dir, phase)
    store_result(change_dir, phase, data, raw, result_path)
    store_stderr(change_dir, phase, err, stderr_path)
    cost = None
    if isinstance(data, dict):
        cost = data.get("total_cost_usd")
        if isinstance(cost, (int, float)):
            record_spend(plugin_dir, root, change_id, gate_phase, float(cost))
    owner = verify_owner_fields(change_dir, before_st, approved_st, root, pre_head, config)
    owner["mismatches"] += session_push_mismatches(
        root, gitops_current_branch(root), refs_before, change_refs(root, change_id)
    )
    owner["ok"] = not owner["mismatches"]
    for line in owner["overrides_changed"]:
        print(f"status.yaml: {line}", file=sys.stderr)
    if not owner["ok"]:
        # before any commit of this run: the fields are restored, the park names them
        parked = park_and_publish(
            plugin_dir, root, change_dir, before_st, phase,
            OWNER_FIELDS_PARK.format(reasons="; ".join(owner["mismatches"])),
            branch=fix_branch, check=OWNER_FIELDS_CHECK, need=OWNER_FIELDS_NEED,
        )  # fmt: skip
        _emit({**parked, "owner_fields": owner, "claude_exit": code, "cost_usd": cost,
               "branch": branch})  # fmt: skip
        return EXIT_OK
    if code != 0 or not isinstance(data, dict) or data.get("is_error"):
        report_failed_run(root, change_dir, phase, data, raw, err, f"claude exited {code}")
        return EXIT_FAILED

    if phase == "f":
        record = commit_run_record(plugin_dir, root, change_id, phase) if cost is not None else None
        _emit({"phase": phase, "change_id": change_id, "cost_usd": cost, "run_record": record,
               "labels": labels, "setup": setup, "next": "detect/cli.py finish"})  # fmt: skip
        return EXIT_OK

    review = validate_review(plugin_dir, root, change_id) if phase == "review" else None
    if phase == "review":
        _emit(
            {
                "phase": phase,
                "change_id": change_id,
                "cost_usd": cost,
                "review": review,
                "labels": labels,
                "setup": setup,
            }
        )
        return EXIT_OK if review and review.get("ok") else EXIT_FAILED

    result = read_gate(change_dir, gate_phase)
    if result is None:
        why = (
            f"the run left no evidence/{art.GATE_RESULT.format(phase=gate_phase)}: the phase "
            "command did not reach its gate"
        )
        report_failed_run(root, change_dir, phase, data, raw, err, why)
        return EXIT_FAILED
    # the spend is recorded after the run's own commits, so on an ephemeral runner it would
    # leave with the job (the fifth live run of 2026-09-21 pushed run-b.json with spend_usd
    # null): commit it on the work branch before the PR is brought up to date
    record = (
        commit_run_record(plugin_dir, root, change_id, phase, gate_phase, fix_branch)
        if cost is not None
        else None
    )
    # the PR is where the owner meets the change, parked or not: open it here rather than
    # trusting the run to have done it (the parked run of 2026-09-21 did not)
    pr = ensure_pr(plugin_dir, root, change_id, phase, args.repo, env, gate_phase, fix_branch)
    handed = hand_over(args, result, gate_phase, change_id) if pr.get("ok") else None
    _emit(
        {
            "phase": phase,
            "gate_phase": gate_phase,
            "change_id": change_id,
            "owner_labels": labels_applied,
            "owner_fields": owner,
            "fix_requests": requests_collected,
            "run_record": record,
            "result": result.get("result"),
            "label": result.get("label"),
            "cost_usd": cost,
            "dispatched": handed,
            "labels": labels,
            "setup": setup,
            "pr": pr,
        }
    )
    if not pr.get("ok"):
        # the evidence is written and the spend is recorded above; what is missing is the
        # queue item, and a phase result nobody can find is an infrastructure failure
        print(PR_MISSING.format(reason=pr.get("reason") or "no route"), file=sys.stderr)
        return EXIT_FAILED
    return EXIT_OK


def commit_run_record(
    plugin_dir: Path,
    root: Path,
    change_id: str,
    phase: str,
    branch_phase: str | None = None,
    branch: str | None = None,
) -> dict[str, Any]:
    """Commit and push the change folder after ``record_spend``: ``run-<phase>.json`` now
    carries the spend, and nothing commits after the model's session but the run itself.
    ``commit-phase`` is a no-op commit when nothing changed, so a by-hand run pays nothing.
    A fix round names the change's phase and the PR's head (``branch``)."""
    branch_phase = branch_phase or BRANCH_PHASE.get(phase, phase)
    return _cli_call(
        plugin_dir / "plugin" / "state" / "cli.py",
        ["commit-phase", "--root", str(root), "--id", change_id, "--phase", branch_phase,
         "--message", f"run({phase}): spend recorded", "--push",
         *(["--branch", branch] if branch else [])],
    )  # fmt: skip


# --- the owner's un-park labels (decision 24) --------------------------------------------------
def apply_owner_labels(
    plugin_dir: Path,
    root: Path,
    change_dir: Path,
    config: dict[str, Any],
    repo: str,
    pr_number: Any,
    branch_phase: str,
    branch: str | None,
    env: dict[str, str],
) -> dict[str, Any]:
    """Perform the owner's labels on the change's PR (``state/unpark.py``) and commit
    ``status.yaml`` on the work branch, so the session and the gate read the settled state.
    A run without a GitHub route or without the PR's number reads nothing and says so."""
    from state import unpark  # noqa: PLC0415

    number = _pr_number(pr_number)
    github = _github()
    if github is None or number is None or not repo:
        return {"ok": False, "reason": "no pull request number or repository: labels not read"}
    if not _token(env) and not github.gh_path():
        return {"ok": False, "reason": "no gh and no GITHUB_TOKEN/GH_TOKEN: labels not read"}
    result = unpark.apply_from_pr(root, change_dir, config, repo, number, github=github)
    if result.get("performed"):
        names = ", ".join(p["label"] for p in result["performed"])
        result["commit"] = _cli_call(
            plugin_dir / "plugin" / "state" / "cli.py",
            ["commit-phase", "--root", str(root), "--id", status_mod.read_status(change_dir).id,
             "--phase", branch_phase, "--message", f"owner labels applied: {names}", "--push",
             *(["--branch", branch] if branch else [])],
        )  # fmt: skip
    return result


# --- the owner-only fields of status.yaml, re-verified after the session (choice 103) ---------
# The session can write status.yaml, and the gate's ``owner_actions`` check believes a recorded
# label actor that is a person (the 1.0.0 readiness review, group A). The runner is the one
# reader the session cannot edit: it snapshots the fields only the owner sets right before
# ``claude -p`` (after its own label handling, ``apply_owner_labels``) and compares them right
# after. An entry the session added that the runner did not record and the default branch's
# copy does not carry, an act the session performed itself (a risk item accepted, the test-file
# lock lifted) and a counter lowered by anything but the runner's own reset park the change
# with the field, the session's value and the expected one; the fields are restored first, so
# no commit of the runner ever carries the session's version. The baseline itself is checked
# too (the review of the 0.2.26 diff, M1): an entry on the branch that the default branch does
# not carry must match a label event on the pull request, and a push by the session to any
# other branch of the change, or a remote tip the runner's checkout does not contain, parks.
OWNER_FIELDS_PARK = c.OWNER_FIELDS_PARK_PREFIX + "{reasons}"
OWNER_FIELDS_NEED = (
    "risk_accepted, risk_accepted_by, tests_locked, tests_unlocked_by, iterations_reset_by and "
    "the counters are written by the runner from your label on the pull request "
    "(sdlc:accept-risk, sdlc:reset-iterations, sdlc:unlock-tests) or by your own commit; the "
    "run cannot approve itself (decision 5). The fields were restored to their pre-session "
    "values (a test file changed under a lifted lock too); apply the label if the act is "
    "yours, else fix the phase command that wrote them and re-run the phase."
)
OWNER_FIELDS_CHECK = "owner_fields"
OWNER_LABEL_OF = {
    "risk_accepted_by": c.ACCEPT_RISK_LABEL,
    "iterations_reset": c.RESET_ITERATIONS_LABEL,
    "tests_unlocked_by": c.UNLOCK_TESTS_LABEL,
}


def owner_fields(st) -> dict[str, Any]:
    """The fields of ``status.yaml`` only the owner sets, in a comparable shape."""
    return {
        "risk_accepted": sorted(str(r).strip().lower() for r in st.risk_accepted if str(r).strip()),
        "risk_accepted_by": sorted(
            (str(e.get("item", "")).strip(), str(e.get("actor", "")).strip())
            for e in st.risk_accepted_by
            if isinstance(e, dict)
        ),
        "iterations_reset": (st.iterations_reset_by, st.iterations_reset_at),
        "tests_unlocked_by": st.tests_unlocked_by,
        # the lock as the hook and the gate read it: a fix-type change with tests_locked
        "locked": st.change_type == "fix" and bool(st.tests_locked),
        "iterations": st.iterations,
        "panel_calls": st.panel_calls,
        "profile_override": st.profile_override,
        "review_override": st.review_override,
    }


def owner_field_mismatches(
    before: dict[str, Any], after: dict[str, Any], approved: dict[str, Any] | None
) -> list[str]:
    """What the session changed that only the owner may: one line per field, with the
    session's value and the expected one. Allowed after the session: what the runner
    recorded before it (``before``), what the default branch's copy carries (``approved``: a
    merge of the default branch into the work branch brings it), and a cleared field (a
    dropped acceptance or a cleared actor fails closed at the gate; ``lock_tests`` clears
    ``tests_unlocked_by`` by design). The acts are judged with the actors (the review of the
    0.2.26 diff, H1): a risk item accepted with no entry, or the lock lifted with no actor,
    is the session's own act whatever the commit author says. The overrides are not judged
    here: they are restored and reported (``override_changes``)."""
    approved = approved or {}
    reasons: list[str] = []
    known_items = set(before["risk_accepted"]) | set(approved.get("risk_accepted") or [])
    known_by = set(before["risk_accepted_by"]) | set(approved.get("risk_accepted_by") or [])
    by_item = {item.lower(): actor for item, actor in after["risk_accepted_by"]}
    for item in after["risk_accepted"]:
        if item not in known_items:
            reasons.append(
                f"risk_accepted: the session accepted {item!r}"
                + (
                    f" and recorded {by_item[item]!r} for it; the runner recorded no label"
                    if item in by_item
                    else "; only the owner's label or commit does"
                )
            )
    for item, actor in after["risk_accepted_by"]:
        if (item, actor) not in known_by and item.lower() in known_items:
            reasons.append(
                f"risk_accepted_by: the session recorded {actor!r} for {item!r}; the runner "
                "recorded no label for it"
            )
    resets = {before["iterations_reset"], (None, None)}
    if approved.get("iterations_reset"):
        resets.add(tuple(approved["iterations_reset"]))
    if after["iterations_reset"] not in resets:
        reasons.append(
            f"iterations_reset_by: the session recorded {after['iterations_reset'][0]!r} "
            f"({after['iterations_reset'][1]!r}); expected {before['iterations_reset'][0]!r} "
            f"({before['iterations_reset'][1]!r})"
        )
    unlocks = {before["tests_unlocked_by"], approved.get("tests_unlocked_by"), None}
    if after["tests_unlocked_by"] not in unlocks:
        reasons.append(
            f"tests_unlocked_by: the session recorded {after['tests_unlocked_by']!r}; expected "
            f"{before['tests_unlocked_by']!r}"
        )
    if before["locked"] and not after["locked"]:
        reasons.append(
            "tests_locked: the session lifted the test-file lock (tests_locked false or the "
            "change no longer a fix); only sdlc:unlock-tests or the owner's commit does"
        )
    for counter in ("iterations", "panel_calls"):
        if after[counter] < before[counter]:
            reasons.append(
                f"{counter}: the session lowered it from {before[counter]} to {after[counter]}; "
                "only sdlc:reset-iterations does"
            )
    return reasons


def override_changes(before: dict[str, Any], after: dict[str, Any]) -> list[str]:
    """The overrides the session changed on the branch — restored and reported, never parked:
    the runner and the gate read the default branch's copy whatever the branch says, and the
    branch's value is put back so the owner's next merge does not carry it (the review of
    the 0.2.26 diff, H2)."""
    return [
        f"{name}: the session set {after[name]!r} (was {before[name]!r}); restored, the "
        "default branch's copy is what the runner and the gate read"
        for name in ("profile_override", "review_override")
        if after[name] != before[name]
    ]


def _test_files_changed_since(root: Path, pre_head: str, config: dict[str, Any]) -> list[str]:
    """The files under ``sdlc.yaml: test_paths`` that differ between ``pre_head`` and the
    working tree (committed by the session or not)."""
    from hooks._common import ConfigError as _ConfigError  # noqa: PLC0415
    from hooks.test_file_lock import test_path_patterns  # noqa: PLC0415

    try:
        patterns = test_path_patterns(config)
    except _ConfigError:
        return []
    changed = gate_diff._z(
        gate_diff._git(root, "diff", "--name-only", "-z", pre_head, check=False)
    ) + gate_diff._z(
        gate_diff._git(root, "ls-files", "--others", "--exclude-standard", "-z", check=False)
    )
    return sorted({f for f in changed if any(matches(p, f) for p in patterns)})


def restore_test_files(root: Path, pre_head: str, files: list[str]) -> list[str]:
    """Put the test files back as ``pre_head`` had them (a file new since then is removed):
    the runner's restore commit would otherwise be the newest lock commit and the gate's
    ``test_lock`` check would judge nothing before it (the review of the 0.2.26 diff, M2)."""
    from state import gitops  # noqa: PLC0415

    restored: list[str] = []
    for rel in files:
        if gate_diff.file_at(root, pre_head, rel) is None:
            try:
                (root / rel).unlink()
            except OSError:
                continue
        else:
            gitops.run(root, "checkout", pre_head, "--", rel, check=False)
        restored.append(rel)
    return restored


def restore_owner_fields(change_dir: Path, before_st, after_st=None) -> None:
    """Write the pre-session values of the owner-only fields back over what the session
    left, keeping the session's other fields (phase, gate, evidence) when its file is
    readable; the whole pre-session file when it is not."""
    if after_st is None:
        status_mod.write_status(change_dir, before_st)
        return
    after_st.risk_accepted = list(before_st.risk_accepted)
    after_st.risk_accepted_by = [dict(e) for e in before_st.risk_accepted_by]
    after_st.iterations_reset_by = before_st.iterations_reset_by
    after_st.iterations_reset_at = before_st.iterations_reset_at
    after_st.tests_unlocked_by = before_st.tests_unlocked_by
    if before_st.change_type == "fix" and before_st.tests_locked:
        after_st.change_type = "fix"
        after_st.tests_locked = True
    after_st.iterations = max(after_st.iterations, before_st.iterations)
    after_st.panel_calls = max(after_st.panel_calls, before_st.panel_calls)
    after_st.profile_override = before_st.profile_override
    after_st.review_override = before_st.review_override
    status_mod.write_status(change_dir, after_st)


def change_refs(root: Path, change_id: str) -> dict[str, str]:
    """``{branch: sha}`` of the change's branches on the remote (``origin/sdlc/<id>/*``), after
    a fetch; empty without a remote."""
    from state import gitops  # noqa: PLC0415

    if not gitops.is_repo(root) or not gitops.has_remote(root):
        return {}
    gitops.run(root, "fetch", "--prune", "origin", check=False)
    out = gitops.run(
        root,
        "for-each-ref",
        "--format=%(refname:short)%00%(objectname)",
        f"refs/remotes/origin/sdlc/{change_id}/",
        check=False,
    )
    refs: dict[str, str] = {}
    for line in out.splitlines():
        name, _, sha = line.partition("\0")
        if name and sha:
            refs[name.removeprefix("origin/")] = sha
    return refs


def session_push_mismatches(
    root: Path, branch: str | None, refs_before: dict[str, str], refs_after: dict[str, str]
) -> list[str]:
    """A push by the session outside its own branch, or a remote tip of its branch that the
    runner's checkout does not contain (the review of the 0.2.26 diff, M1: forged fields
    planted on the next phase's branch, or pushed and then reset locally, became the next
    run's baseline)."""
    from state import gitops  # noqa: PLC0415

    reasons: list[str] = []
    for name in sorted(set(refs_before) | set(refs_after)):
        if name == branch:
            continue
        if refs_before.get(name) != refs_after.get(name):
            reasons.append(
                f"origin/{name}: the session pushed to another branch of the change "
                f"({(refs_before.get(name) or 'absent')[:10]} -> "
                f"{(refs_after.get(name) or 'absent')[:10]}); a run pushes its own branch only"
            )
    remote = refs_after.get(branch or "")
    if remote:
        contained = gitops.run(
            root, "merge-base", "--is-ancestor", remote, "HEAD", check=False
        ) == "" and _git_ok(root, "merge-base", "--is-ancestor", remote, "HEAD")
        if not contained:
            reasons.append(
                f"origin/{branch}: the remote tip {remote[:10]} is not in the runner's checkout; "
                "the session pushed and then moved its branch"
            )
    return reasons


def baseline_mismatches(
    before: dict[str, Any],
    approved: dict[str, Any] | None,
    repo: str,
    pr_number: int | None,
    env: dict[str, str],
) -> list[str]:
    """The pre-session entries the default branch's copy does not carry must each match a
    ``labeled`` event on the pull request (the label, the actor) — choice 103's wording: an
    actor the runner recorded from GitHub. On a runner with no pull request or no route to
    read the events, such an entry parks (a by-hand run skips the read)."""
    approved = approved or {}
    pending: list[tuple[str, str, str]] = []  # (field, label, actor)
    known_by = set(approved.get("risk_accepted_by") or [])
    for item, actor in before["risk_accepted_by"]:
        if (item, actor) not in known_by:
            pending.append((f"risk_accepted_by[{item}]", c.ACCEPT_RISK_LABEL, actor))
    if before["iterations_reset"][0] and tuple(before["iterations_reset"]) != tuple(
        approved.get("iterations_reset") or (None, None)
    ):
        pending.append(
            ("iterations_reset_by", c.RESET_ITERATIONS_LABEL, before["iterations_reset"][0])
        )
    if before["tests_unlocked_by"] and before["tests_unlocked_by"] != approved.get(
        "tests_unlocked_by"
    ):
        pending.append(("tests_unlocked_by", c.UNLOCK_TESTS_LABEL, before["tests_unlocked_by"]))
    if not pending:
        return []
    if not env.get("GITHUB_ACTIONS"):
        return []
    github = _github()
    if github is None or pr_number is None or not repo:
        return [
            f"{field}: {actor!r} on the branch is not on the default branch and no pull "
            "request can confirm the label"
            for field, _label, actor in pending
        ]
    reasons: list[str] = []
    seen: dict[str, dict[str, Any]] = {}
    for field, label, actor in pending:
        if label not in seen:
            try:
                seen[label] = github.label_actor(repo, pr_number, label)
            except Exception as exc:  # noqa: BLE001 - no route: fail closed below
                seen[label] = {"ok": False, "reason": str(exc)}
        found = seen[label]
        if not found.get("ok"):
            reasons.append(
                f"{field}: {actor!r} on the branch is not on the default branch and the "
                f"{label} events of PR #{pr_number} could not be read: {found.get('reason')}"
            )
        elif str(found.get("actor") or "") != actor:
            reasons.append(
                f"{field}: {actor!r} on the branch is not on the default branch and PR "
                f"#{pr_number} has no {label} event by that actor "
                f"(last: {found.get('actor')!r})"
            )
    return reasons


def verify_owner_fields(
    change_dir: Path,
    before_st,
    approved_st,
    root: Path | None = None,
    pre_head: str | None = None,
    config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """After the session: ``{"ok", "mismatches", "overrides_changed", "test_files_restored"}``;
    on a mismatch (or an unreadable file) the owner-only fields are restored before anything
    is committed, and the test files changed under a lifted lock are put back; a changed
    override is restored whatever else happened."""
    before = owner_fields(before_st)
    approved = owner_fields(approved_st) if approved_st is not None else None
    try:
        after_st = status_mod.read_status(change_dir)
    except Exception as exc:  # noqa: BLE001 - whatever the session left, the owner's fields come back
        restore_owner_fields(change_dir, before_st)
        return {
            "ok": False,
            "mismatches": [f"status.yaml unreadable after the session: {exc}"],
            "overrides_changed": [],
            "test_files_restored": [],
        }
    after = owner_fields(after_st)
    mismatches = owner_field_mismatches(before, after, approved)
    overrides = override_changes(before, after)
    if mismatches or overrides:
        restore_owner_fields(change_dir, before_st, after_st)
    restored: list[str] = []
    if before["locked"] and not after["locked"] and root is not None and pre_head:
        restored = restore_test_files(
            root, pre_head, _test_files_changed_since(root, pre_head, config or {})
        )
        if restored:
            mismatches.append(
                "test files changed under the lifted lock, restored: " + ", ".join(restored[:10])
            )
    return {
        "ok": not mismatches,
        "mismatches": mismatches,
        "overrides_changed": overrides,
        "test_files_restored": restored,
    }


FIX_REQUESTS_PARK = (
    "the fix round's change requests could not be collected from the pull request: {reason}"
)


def collect_fix_requests(
    root: Path,
    change_dir: Path,
    config: dict[str, Any],
    repo: str,
    pr_number: Any,
    env: dict[str, str],
    head_ref: str | None = None,
) -> dict[str, Any]:
    """Write ``evidence/fix-requests.json`` (``ci/fix_requests.py``): the PR's reviews, review
    threads and comments, each judged by ``author_association`` before the model's session
    starts, so ``/sdlc-fix`` step 1 reads the file and never the PR. A ``workflow_dispatch``
    round has no event number: the open PR of ``head_ref`` supplies it. Without a route or a
    number the file says so (``unavailable``); by hand the command then falls back to ``gh``,
    on a runner the run parks (``run_phase``)."""
    number = _pr_number(pr_number)
    github = _github()
    head = gate_diff.head_sha(root) if gate_diff.is_repo(root) else None
    routed = github is not None and repo and (_token(env) or github.gh_path())
    if routed and number is None and head_ref:
        found = github.find_open_pr(repo, head_ref, cwd=root)
        number = _pr_number(found.get("number")) if found.get("number") else None
    if github is None or not repo:
        reason = "no repository: the requests were not collected"
    elif not routed:
        reason = "no gh and no GITHUB_TOKEN/GH_TOKEN: the requests were not collected"
    elif number is None:
        reason = f"no pull request number and no open pull request for {head_ref or 'the head'}"
    else:
        return fix_requests.collect_and_write(
            change_dir, repo, number, github, config, head, cwd=root
        )
    path = fix_requests.write(
        change_dir,
        {
            "schema_version": fix_requests.SCHEMA_VERSION,
            "repo": repo or None,
            "pr_number": number,
            "head": head,
            "ok": False,
            "unavailable": reason,
            "requests": [],
            "not_applied": [],
        },
    )
    return {"ok": False, "file": path.name, "requests": 0, "not_applied": 0, "unavailable": reason}


def hand_over(args, result: dict[str, Any], phase: str, change_id: str) -> Any:
    workflow = NEXT_WORKFLOW.get(phase)
    if result.get("result") != "continue" or not workflow:
        return None
    ref = args.ref or default_ref(Path(args.root))
    head_ref = work_branch_for(change_id, NEXT_PHASE[phase])
    if args.no_dispatch:
        return {
            "would_dispatch": workflow,
            "ref": ref,
            "change_id": change_id,
            "head_ref": head_ref,
        }
    return {
        "workflow": workflow,
        "ref": ref,
        "head_ref": head_ref,
        **dispatch(args.repo, workflow, ref, change_id, head_ref),
    }


def default_ref(root: Path) -> str:
    from state import gitops

    try:
        return gitops.default_branch(root) if gitops.is_repo(root) else "main"
    except Exception:  # noqa: BLE001 - a detached CI checkout must not fail the hand-over
        return "main"


def preflight(plugin_dir: Path, root: Path, change_id: str) -> dict[str, Any]:
    script = plugin_dir / "plugin" / "gate" / "preflight.py"
    argv = [
        _python(), str(script),
        "--root", str(root), "--plugin-root", str(plugin_dir), "--id", change_id,
    ]  # fmt: skip
    try:
        proc = subprocess.run(argv, capture_output=True, text=True, encoding="utf-8", timeout=3600)
    except (OSError, subprocess.SubprocessError) as exc:
        return {"allow": False, "reasons": [f"preflight could not run: {exc}"]}
    try:
        return json.loads(proc.stdout)
    except ValueError:
        return {"allow": False, "reasons": [f"preflight printed no JSON: {proc.stderr.strip()}"]}


def park(plugin_dir: Path, root: Path, change_id: str, reason: str) -> bool:
    cli = plugin_dir / "plugin" / "state" / "cli.py"
    argv = [
        _python(), str(cli), "park",
        "--root", str(root), "--id", change_id, "--reason", reason,
    ]  # fmt: skip
    try:
        proc = subprocess.run(argv, capture_output=True, text=True, encoding="utf-8", timeout=120)
    except (OSError, subprocess.SubprocessError):
        return False
    return proc.returncode == 0


# --- parking from CI: the park has to be visible where the owner looks -----------------------
PARK_CHECK = {"c": "preflight", "b": "guardrails", "d": "guardrails", "e": "guardrails"}


PRE_RUN_NEED = "Settle this, then re-run the phase: CI stopped before the run started."


def write_park_result(
    root: Path, change_dir: Path, st, phase: str, check: str, reason: str, need: str | None = None
) -> Path:
    """``evidence/gate-<phase>.json`` in the gate's own shape, so the PR description shows
    the park and its "What I need from you" block (the gate itself overwrites it later).
    ``need`` is the pre-run sentence unless the park came after the session."""
    from gate.checks import CheckResult  # noqa: PLC0415
    from gate.gate import GateResult  # noqa: PLC0415

    result = GateResult(
        change_id=st.id,
        slug=st.slug,
        phase=phase,
        profile=getattr(st, "profile_override", None) or "",
        human_gate=True,
        result="park",
        checks=[
            CheckResult(
                name=check,
                ok=False,
                reason=reason,
                need=need or PRE_RUN_NEED,
            )
        ],
        label=c.NEEDS_HUMAN_LABEL,
        head=gate_diff.head_sha(Path(root)) if gate_diff.is_repo(Path(root)) else None,
    )
    path = change_dir / art.EVIDENCE_DIR / art.GATE_RESULT.format(phase=phase)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(result.as_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return path


def _cli_call(script: Path, argv: list[str], timeout: int = 600) -> dict[str, Any]:
    """Run a plugin CLI and keep what it said.

    Every plugin CLI prints JSON, and that JSON is the only place the route, the URL and the
    reason live: discarding stdout is how a run of 2026-09-21 reported ``ok`` for an upsert
    that had opened no pull request. The parsed object comes back under ``output``; output
    that is not JSON is kept verbatim under ``stdout``.
    """
    try:
        proc = subprocess.run(
            [_python(), str(script), *argv],
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=timeout,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return {"ok": False, "reason": str(exc)}
    out: dict[str, Any] = {
        "ok": proc.returncode == 0,
        "reason": (proc.stderr or "").strip()[-500:],
    }
    text = (proc.stdout or "").strip()
    try:
        parsed = json.loads(text) if text else None
    except ValueError:
        parsed = None
    if isinstance(parsed, dict):
        out["output"] = parsed
    elif text:
        out["stdout"] = text[-2000:]
    return out


def park_and_publish(
    plugin_dir: Path,
    root: Path,
    change_dir: Path,
    st,
    phase: str,
    reason: str,
    branch: str | None = None,
    check: str | None = None,
    need: str | None = None,
) -> dict[str, Any]:
    """Park, then leave the park where the owner will find it: the change folder committed
    and pushed on the work branch, and the phase's PR carrying ``sdlc:needs-human`` and the
    "What I need from you" block (OPERATING_MODEL section 5: a park is a queue item). A fix
    round parks the change's own phase on the PR's head (``branch``)."""
    branch_phase = st.phase if phase == "fix" else BRANCH_PHASE.get(phase, phase)
    state_cli = plugin_dir / "plugin" / "state" / "cli.py"
    out: dict[str, Any] = {"parked": reason, "phase": phase, "change_id": st.id}
    # the phase first: ``set-phase`` clears any earlier park, so parking after it keeps
    # ``parked_reason`` in the commit (and ``commit-phase`` then leaves the phase alone).
    out["phase_set"] = _cli_call(
        state_cli, ["set-phase", "--root", str(root), "--id", st.id, "--phase", branch_phase]
    )
    out["status"] = park(plugin_dir, root, st.id, reason)
    write_park_result(
        root, change_dir, st, branch_phase, check or PARK_CHECK.get(phase, "ci"), reason, need
    )
    out["commit"] = _cli_call(
        state_cli,
        ["commit-phase", "--root", str(root), "--id", st.id, "--phase", branch_phase,
         "--message", f"park: {reason}"[:500], "--push",
         *(["--branch", branch] if branch else [])],
    )  # fmt: skip
    out["pr"] = upsert_outcome(
        _cli_call(
            plugin_dir / "plugin" / "pr" / "cli.py",
            [
                "upsert",
                "--root",
                str(root),
                "--id",
                st.id,
                "--phase",
                branch_phase,
                "--draft",
                *(["--head", branch] if branch else []),
            ],
        )  # fmt: skip
    )
    return out


# --- the phase's pull request (the surface of OPERATING_MODEL section 4.1) --------------------
# A parked run of 2026-09-21 pushed sdlc/0001/b with the evidence on it but opened no PR: the
# runbook asks the model to call ``pr/cli.py upsert`` and the model's session ended before it
# did. The hand-over does it itself now, whatever the session did: ``upsert`` is idempotent,
# so a PR that already exists only has its body and its gate label brought up to date.
PR_DRAFT_PHASES = ("c",)  # the build PR opens as a draft; (b), (d) and (e) open plain
PR_ROUTES = ("gh", "api")  # the routes that really reach GitHub; "none" opened nothing
PR_MISSING = "no pull request carries this phase's result: {reason}"


def upsert_outcome(call: dict[str, Any], fallback_number: int | None = None) -> dict[str, Any]:
    """What ``pr/cli.py upsert`` did, read from its own JSON: route, url, number, reason.

    ``ok`` means the owner can find the run in the queue: the upsert took a real route (gh or
    api) and named a pull request. Exit code 0 is not enough — ``upsert`` exits 0 with route
    "none" when there is no GitHub remote or no credential, and it prints the body instead
    (third live design run, 2026-09-21: ``{"existed": false, "ok": true}`` and no PR).
    """
    data = call.get("output") if isinstance(call.get("output"), dict) else {}
    route = data.get("route")
    number = data.get("number") if data.get("number") is not None else fallback_number
    url = data.get("url")
    ok = bool(call.get("ok")) and route in PR_ROUTES and bool(number or url)
    reason = str(data.get("reason") or call.get("reason") or "")
    if not ok and not reason:
        reason = f"pr upsert took route {route!r} and opened no pull request"
    out = {"ok": ok, "route": route, "number": number, "url": url, "reason": reason}
    if data.get("build_pr_recorded"):
        out["build_pr_recorded"] = data["build_pr_recorded"]
    return out


def ensure_pr(
    plugin_dir: Path,
    root: Path,
    change_id: str,
    phase: str,
    repo: str,
    env: dict[str, str],
    branch_phase: str | None = None,
    branch: str | None = None,
) -> dict[str, Any]:
    """Open or update the phase's PR for the work branch. Never marks one ready for review:
    that is the owner's move at a human gate.

    The result is the upsert's own answer (``upsert_outcome``): ``ok`` only when a pull
    request now carries the phase, whatever the CLI's exit code was. A fix round passes the
    change's phase and the PR's head (``branch``): the PR is the one the review was left on.
    """
    branch_phase = branch_phase or BRANCH_PHASE.get(phase, phase)
    head = branch or work_branch_for(change_id, phase)
    out: dict[str, Any] = {"head": head, "phase": branch_phase, "existed": None}
    github = _github()
    if github is None:
        return {**out, "ok": False, "reason": "plugin/pr/github.py is not available"}
    if not _token(env) and not github.gh_path():
        return {**out, "ok": False, "reason": "no gh and no GITHUB_TOKEN/GH_TOKEN: no PR route"}
    number = None
    if repo:
        found = github.find_open_pr(repo, head, cwd=root)
        number = found.get("number")
        out["existed"] = bool(number)
        out["number"] = number
    argv = ["upsert", "--root", str(root), "--id", change_id, "--phase", branch_phase]
    if branch_phase in PR_DRAFT_PHASES:
        argv.append("--draft")
    if branch:
        argv += ["--head", branch]
    call = _cli_call(plugin_dir / "plugin" / "pr" / "cli.py", argv)
    outcome = {**out, **upsert_outcome(call, fallback_number=number)}
    if outcome.get("build_pr_recorded"):
        # the upsert wrote ``build_pr`` into status.yaml (0.2.27): the record must reach the
        # branch, where the release approval and the default branch's copy read it
        outcome["build_pr_commit"] = _cli_call(
            plugin_dir / "plugin" / "state" / "cli.py",
            ["commit-phase", "--root", str(root), "--id", change_id, "--phase", branch_phase,
             "--message", f"run({phase}): build pull request #{outcome['build_pr_recorded']} "
             "recorded", "--push", *(["--branch", branch] if branch else [])],
        )  # fmt: skip
    return outcome


# --- CLI --------------------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="sdlc-run-phase",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--root", default=".", help="the project checkout")
    p.add_argument(
        "--plugin-dir",
        default=str(FRAMEWORK_ROOT),
        help="the pinned framework checkout, passed to claude as --plugin-dir",
    )
    p.add_argument("--phase", required=True, choices=RUNNABLE)
    p.add_argument("--id", default=None, help="change id; omit to read it from --head-ref")
    p.add_argument("--head-ref", default=None, help="the PR head branch sdlc/<id>/<phase>")
    p.add_argument(
        "--pr-number",
        default=None,
        help="the merged pull request; its changes/<id>-<slug>/ folder names the change when "
        "neither --id nor an sdlc/<id>/<phase> head ref does",
    )
    p.add_argument(
        "--find-change",
        action="store_true",
        help="only print change_id=<id or empty> and reason=<...> (and append change_id to "
        "$GITHUB_OUTPUT); exits 0 unless $GITHUB_OUTPUT cannot be written",
    )
    p.add_argument("--repo", default="", help="owner/name, for labels and the hand-over")
    p.add_argument("--ref", default=None, help="default branch the dispatch targets")
    p.add_argument("--log", default=None, help="--phase triage: the CI log to read")
    p.add_argument("--claude", default="claude", help="the CLI executable (default: on PATH)")
    p.add_argument("--dry-run", action="store_true", help="print the argv and stop")
    p.add_argument("--no-dispatch", action="store_true", help="print the hand-over, send nothing")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    env = dict(os.environ)
    if args.phase == "triage":
        return run_triage(args, env)
    if args.find_change:
        if args.phase not in PREVIOUS_PHASE:
            print(f"--find-change does not apply to --phase {args.phase}", file=sys.stderr)
            return EXIT_USAGE
        return print_found_change(args, env)
    if not args.id and not args.head_ref and not args.pr_number:
        print("--id, --head-ref or --pr-number is required for a phase run", file=sys.stderr)
        return EXIT_USAGE
    return run_phase(args, env)


if __name__ == "__main__":
    sys.exit(main())
