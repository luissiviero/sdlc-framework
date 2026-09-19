---
description: Connect the SDLC framework to this project in one command — profile and phase adapters into sdlc.yaml, one-command build/test/lint targets, guardrail hooks and permissions, CLAUDE.md skeleton, REVIEW.md, changes/ — committed as the project's first PR (change 0000). Idempotent; re-run to upgrade.
argument-hint: [--profile standard|full|lite]
disable-model-invocation: true
allowed-tools: Bash(python "${CLAUDE_PLUGIN_ROOT}/plugin/init/sdlc_init.py" *), Bash(python "${CLAUDE_PLUGIN_ROOT}/plugin/state/cli.py" *), Bash(git *), Bash(gh *), Read, Write, Edit, Glob, Grep, AskUserQuestion
---

# /sdlc-init — connect the framework (build guide step 21, minimal B1 version)

## 0. Preconditions
- The current directory is the root of a git repository. If not, stop and say so.
- Run the detection first and show it to the owner:
```
python "${CLAUDE_PLUGIN_ROOT}/plugin/init/sdlc_init.py" --root "${CLAUDE_PROJECT_DIR}" --detect-only
```
Only Python detection is implemented in this version; for other languages ask the owner for
the three commands and pass them with `--build/--test/--lint`.

## 1. Ask the owner (one question round, defaults in brackets)
- profile [standard]: standard (owner merges at a, b, e) · full (all five gates) · lite (a, e)
- deploy action [none]: what makes a merged change live — publish package · schedule job ·
  regenerate report · promote to paper trading · deploy service · none
- real production? [no] — turns on the release label and the production gate (B4)
- maintain metric and source [ci_test_failure_rate from github-actions]
- confirm or override the detected build/test/lint commands

## 2. CLAUDE.md proposal (the hook denies direct writes to CLAUDE.md, so write it here)
If `CLAUDE.md` does not exist yet: generate its content the way `/init` does (use the `init`
skill if it is available in this session; otherwise explore the codebase yourself): build,
test and lint commands with an example of healthy output, the conventions that matter, the
architecture a new joiner needs. Cut it down to the essentials (article p.19 step 2): under
a page. Write the result to `changes/0000-sdlc-init/CLAUDE.proposed.md` (create the folder
if needed) and pass it to the install script with `--claude-md-from`. The script creates
`CLAUDE.md` from it plus the skeleton sections it lacks.
If `CLAUDE.md` already exists: leave it; the script only appends the missing skeleton
sections, and the owner trims it in the PR.

## 3. Install
```
python "${CLAUDE_PLUGIN_ROOT}/plugin/init/sdlc_init.py" --root "${CLAUDE_PROJECT_DIR}" --profile <profile> --deploy-action "<action>" --deploy-production <true|false> --maintain-metric <metric> --maintain-source <source> [--claude-md-from changes/0000-sdlc-init/CLAUDE.proposed.md] [--build "<cmd>"] [--test "<cmd>"] [--lint "<cmd>"]
```
It writes `sdlc.yaml`, `.claude/settings.json` (permissions + the pinned plugin
declaration; hooks come from the plugin), `REVIEW.md`, `changes/README.md`, builds
`CLAUDE.md` from the proposal plus the skeleton sections, creates `ruff.toml` when no linter
existed, and creates `changes/0000-sdlc-init/` with an intent.md. Read its JSON report and
show the owner the file-by-file result. Re-running is safe: it merges and never overwrites
the owner's edits. This script is the only sanctioned writer of guardrail files in a run;
everything it writes rides in the change-0000 PR the owner merges.

## 4. Verify the feedback loop
Run the three commands from `sdlc.yaml` once and paste the output. A target that fails is
reported, not hidden: the owner decides whether to fix the project or change the target.

## 5. Commit as the project's first PR (gate (a) of change 0000)
```
python "${CLAUDE_PLUGIN_ROOT}/plugin/state/cli.py" commit-phase --root "${CLAUDE_PROJECT_DIR}" --id 0000 --phase a --message "sdlc-init: connect the SDLC framework" --paths sdlc.yaml .claude/settings.json REVIEW.md CLAUDE.md changes ruff.toml --start-point <default branch> --push
```
(paths that do not exist, such as an uncreated `ruff.toml`, are skipped). Then open the PR exactly as
`/sdlc-plan` step 6 does (gh, else the GitHub MCP tool, else the compare URL), title
`sdlc-init: connect the SDLC framework`, label `sdlc:a-ready`, body = ≤5 bullets: what was
installed · profile and adapters · detected targets and their health · files the owner should
review (CLAUDE.md trim, settings) · merge = accept.

## 6. After the merge (tell the owner, do not do it)
- The plugin is declared in `.claude/settings.json`; a new session (local or cloud) installs
  it from the marketplace once the owner has trusted the folder (allow rules and marketplace
  declarations apply only after workspace trust). Locally the owner may also run
  `claude plugin install sdlc@sdlc-framework`.
- Optional, owner's machine only: `docs/owner-machine/README.md` in the framework repo
  explains the managed settings file and its machine-wide consequences.

Never edit `.claude/**`, `CLAUDE.md`, `REVIEW.md` or `sdlc.yaml` directly; only the install
script writes them, and the owner reviews the result in the PR. Never use bypass-permissions
mode.
