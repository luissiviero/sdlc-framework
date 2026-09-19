---
description: Connect the SDLC framework to this project in one command — profile and phase adapters into sdlc.yaml, one-command build/test/lint targets, guardrail hooks and permissions, CLAUDE.md skeleton, REVIEW.md, changes/ — committed as the project's first PR (change 0000). Idempotent; re-run to upgrade.
argument-hint: [--profile standard|full|lite]
disable-model-invocation: true
allowed-tools: Bash(python ${CLAUDE_PLUGIN_ROOT}/init/sdlc_init.py *), Bash(python ${CLAUDE_PLUGIN_ROOT}/state/cli.py *), Bash(git *), Bash(gh *), Read, Write, Edit, Glob, Grep, AskUserQuestion
---

# /sdlc-init — connect the framework (build guide step 21, minimal B1 version)

## 0. Preconditions
- The current directory is the root of a git repository. If not, stop and say so.
- Run the detection first and show it to the owner:
```
python "${CLAUDE_PLUGIN_ROOT}/init/sdlc_init.py" --root "${CLAUDE_PROJECT_DIR}" --detect-only
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

## 2. CLAUDE.md
If `CLAUDE.md` does not exist, generate one the way `/init` does (use the `init` skill if it
is available in this session; otherwise explore the codebase yourself): build, test and lint
commands with an example of healthy output, the conventions that matter, the architecture a
new joiner needs. Then cut it down to the essentials (article p.19 step 2): keep it under a
page; the owner reviews the result in the PR.

## 3. Install
```
python "${CLAUDE_PLUGIN_ROOT}/init/sdlc_init.py" --root "${CLAUDE_PROJECT_DIR}" --profile <profile> --deploy-action "<action>" --deploy-production <true|false> --maintain-metric <metric> --maintain-source <source> [--build "<cmd>"] [--test "<cmd>"] [--lint "<cmd>"]
```
It writes `sdlc.yaml`, `.claude/settings.json` (permissions + the pinned plugin
declaration; hooks come from the plugin), `REVIEW.md`, `changes/README.md`, merges the
skeleton sections into `CLAUDE.md`, creates `ruff.toml` when no linter existed, and creates
`changes/0000-sdlc-init/` with an intent.md. Read its JSON report and show the owner the
file-by-file result. Re-running is safe: it merges and never overwrites the owner's edits.

## 4. Verify the feedback loop
Run the three commands from `sdlc.yaml` once and paste the output. A target that fails is
reported, not hidden: the owner decides whether to fix the project or change the target.

## 5. Commit as the project's first PR (gate (a) of change 0000)
```
python "${CLAUDE_PLUGIN_ROOT}/state/cli.py" commit-phase --root "${CLAUDE_PROJECT_DIR}" --id 0000 --phase a --message "sdlc-init: connect the SDLC framework" --paths sdlc.yaml .claude/settings.json REVIEW.md CLAUDE.md changes ruff.toml --start-point <default branch> --push
```
(omit `ruff.toml` from `--paths` if it was not created). Then open the PR exactly as
`/sdlc-plan` step 6 does (gh, else the GitHub MCP tool, else the compare URL), title
`sdlc-init: connect the SDLC framework`, label `sdlc:a-ready`, body = ≤5 bullets: what was
installed · profile and adapters · detected targets and their health · files the owner should
review (CLAUDE.md trim, settings) · merge = accept.

## 6. After the merge (tell the owner, do not do it)
- The plugin is declared in `.claude/settings.json`; a new session (local or cloud) installs
  it from the marketplace. Locally the owner may also run `claude plugin install sdlc@sdlc-framework`.
- Optional, owner's machine only: `docs/owner-machine/README.md` in the framework repo
  explains the managed settings file and its machine-wide consequences.

Never edit `.claude/**`, `CLAUDE.md`, `REVIEW.md` or `sdlc.yaml` after step 3 except through
the install script. Never use bypass-permissions mode.
