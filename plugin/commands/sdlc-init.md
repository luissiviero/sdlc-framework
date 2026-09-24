---
description: Connect the SDLC framework to this project in one command — profile and phase adapters into sdlc.yaml, one-command build/test/lint targets (Python or Node detected), guardrail hooks and permissions, CLAUDE.md skeleton, REVIEW.md, changes/, evals/, bands.yaml — committed as the project's first PR (change 0000). Idempotent; re-run to upgrade.
argument-hint: [--profile standard|full|lite]
disable-model-invocation: true
allowed-tools: Bash(python "${CLAUDE_PLUGIN_ROOT}/plugin/init/sdlc_init.py" *), Bash(python "${CLAUDE_PLUGIN_ROOT}/plugin/state/cli.py" *), Bash(python "${CLAUDE_PLUGIN_ROOT}/plugin/pr/cli.py" *), Bash(git *), Bash(gh *), Read, Write, Edit, Glob, Grep, AskUserQuestion
---

# /sdlc-init — connect the framework (build guide step 21)

## 0. Preconditions
- The current directory is the root of a git repository. If not, stop and say so.
- Hosting is GitHub (decision 23): every trigger, the automation identity, the labels, the
  check runs and the digest issue are GitHub-specific. The install script refuses a project
  whose `origin` remote is on another host (exit 2, the reason in its JSON `error`): stop
  and tell the owner. A project with no `origin` yet, or a local-path remote, is let through
  and the report's `hosting` line says the CI plumbing will not run until a GitHub remote
  exists; say so in the report.
- Run the detection first and show it to the owner:
```
python "${CLAUDE_PLUGIN_ROOT}/plugin/init/sdlc_init.py" --root "${CLAUDE_PROJECT_DIR}" --detect-only
```
Detection covers Python (pyproject/pytest/ruff/flake8) and Node (`package.json` scripts →
`npm test`, `npm run lint`, `npm run build`). For other languages, or when a target is
reported as `none`, ask the owner for the command and pass it with `--build/--test/--lint`;
the gate does not enter phase (c) without all three. Detection also proposes `commands.setup`
— the one command that installs what those three need (`python -m pip install -e ".[dev]"`,
`npm ci`, ...), which the CI phase jobs run before every phase; override it with `--setup`
and pass `--setup ""` when the project has nothing to install.

## 1. Ask the owner (one question round, defaults in brackets)
- profile [standard]: standard (owner merges at a, b, e) · full (all five gates) · lite (a, e)
- deploy action [none]: what makes a merged change live — publish package · schedule job ·
  regenerate report · promote to paper trading · deploy service · none
- real production? [no] — turns on the release label and the production gate
- maintain metric and source [ci_test_failure_rate from github-actions]
- confirm or override the detected build/test/lint commands and the setup (install) command

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
python "${CLAUDE_PLUGIN_ROOT}/plugin/init/sdlc_init.py" --root "${CLAUDE_PROJECT_DIR}" --profile <profile> --deploy-action "<action>" --deploy-production <true|false> --maintain-metric <metric> --maintain-source <source> [--claude-md-from changes/0000-sdlc-init/CLAUDE.proposed.md] [--build "<cmd>"] [--test "<cmd>"] [--lint "<cmd>"] [--setup "<cmd>"]
```
It writes `sdlc.yaml`, `.claude/settings.json` (permissions + the pinned plugin
declaration; hooks come from the plugin), `REVIEW.md`, `changes/README.md`, builds
`CLAUDE.md` from the proposal plus the skeleton sections, creates `ruff.toml` when no linter
existed, creates `evals/` (empty suite, filled by incidents — decision 17) and `bands.yaml`
(control bands for the maintain metric — decision 15), and creates
`changes/0000-sdlc-init/` with an intent.md. It also installs the CI workflows (the phase
transitions, the release, the fix round, the abandon rule) and the daily digest under
`.github/`, create-only (an existing file is never overwritten); re-running it on an upgrade
installs the workflow files a newer plugin adds and reports an existing one that differs
from this version's template as `outdated` — the owner replaces it (delete it and re-run)
to get the newer steps, or keeps their edits. Read its JSON report and show the owner the
file-by-file result, the `outdated` ones first. Re-running is safe: it merges and never
overwrites the owner's edits. This script is the only sanctioned writer of guardrail files in a run;
everything it writes rides in the change-0000 PR the owner merges.

## 4. Verify the feedback loop
Run the three commands from `sdlc.yaml` once and paste the output. A target that fails is
reported, not hidden: the owner decides whether to fix the project or change the target.

## 5. Commit as the project's first PR (gate (a) of change 0000)
Branch policy: the framework's branch is `sdlc/0000/a`. If this session's platform assigns
a branch and forbids pushing any other (Claude Code on the web does), run the command below
without `--push`, then push the resulting commit to the assigned branch and open the PR from
it, keeping the label; say in the PR body that the framework branch is `sdlc/0000/a` locally.
```
python "${CLAUDE_PLUGIN_ROOT}/plugin/state/cli.py" commit-phase --root "${CLAUDE_PROJECT_DIR}" --id 0000 --phase a --message "sdlc-init: connect the SDLC framework" --paths sdlc.yaml .claude/settings.json REVIEW.md CLAUDE.md changes ruff.toml evals bands.yaml --start-point <default branch> --push
```
(paths that do not exist, such as an uncreated `ruff.toml`, are skipped). Then open the PR exactly as
`/sdlc-plan` step 6 does:
`python "${CLAUDE_PLUGIN_ROOT}/plugin/pr/cli.py" upsert --root "${CLAUDE_PROJECT_DIR}" --id 0000 --phase a`
(title `intent(0000): <title>`, label `sdlc:a-ready`, the generated ≤5-bullet summary from
`changes/0000-sdlc-init/intent.md`; routes gh → REST API → compare URL for the owner). In the
report, add what the summary cannot know: the detected targets and their health, and the
files the owner should review (CLAUDE.md trim, settings). Merge = accept.

## 6. After the merge (tell the owner, do not do it)
- The plugin is declared in `.claude/settings.json`. A local interactive session installs it
  from the marketplace once the owner accepts the trust dialog for the folder. A cloud
  session never shows that dialog, so the repository's marketplace declaration is ignored
  there ("marketplace not registered"): the owner adds two lines to the cloud environment's
  setup script — `claude plugin marketplace add luissiviero/sdlc-framework` and
  `claude plugin install sdlc@sdlc-framework --yes` (see `docs/NOTES.md` §3).
- The phase workflows open pull requests with the workflow token, which GitHub refuses
  until the owner turns on, once per repository, Settings → Actions → General → Workflow
  permissions → "Allow GitHub Actions to create and approve pull requests" (NOTES §11a).
  Without it every phase job ends with "GitHub Actions is not permitted to create or
  approve pull requests" after the phase has run. The workflows also need the repository
  secret `CLAUDE_CODE_OAUTH_TOKEN` or `ANTHROPIC_API_KEY` (NOTES §2).
- Optional, owner's machine only: `docs/owner-machine/README.md` in the framework repo
  explains the managed settings file and its machine-wide consequences.

Never edit `.claude/**`, `CLAUDE.md`, `REVIEW.md` or `sdlc.yaml` directly; only the install
script writes them, and the owner reviews the result in the PR. Never use bypass-permissions
mode. Never notify anyone.
