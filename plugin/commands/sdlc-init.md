---
description: Connect the SDLC framework to this project in one command — profile and phase adapters into sdlc.yaml, one-command build/test/lint targets (Python or Node detected), guardrail hooks and permissions, CLAUDE.md skeleton, REVIEW.md, changes/, evals/, bands.yaml — committed as the project's first PR (change 0000). Idempotent; re-run to upgrade.
argument-hint: [--profile standard|full] [--review parked|deferred]
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
- **The project's GitHub App is required** (decision 33; ROADMAP R22, plugin 1.0.18): the
  automation pushes and opens pull requests as it, and without it no phase run starts (the
  runner stops each run with the reason; it never falls back to the workflow token for a
  whole run). On a project whose `origin` is on GitHub, check that the repository variable
  is there: `gh variable list` must list `SDLC_APP_ID` (the private key, stored as a
  repository secret, cannot be read back; ask the owner to confirm it). If the variable is
  missing, or `gh` cannot list the variables and the owner does not confirm both, **stop
  here**: give the owner the App bullet of step 6 and say that it is desktop-only, since the
  GitHub mobile app cannot create an App or store a variable (open github.com in a desktop
  browser, or in the phone browser's desktop mode; ROADMAP R21), with the direct links
  `https://github.com/settings/apps/new` and
  `https://github.com/<owner>/<repo>/settings/variables/actions`, and ask the owner to
  re-run `/sdlc-init` once both are set. Nothing is written before that. A project with no
  GitHub remote yet goes on, and the report says the App comes with the remote.

## 1. Ask the owner (one question round, defaults in brackets)
- profile [standard]: standard (owner merges at a and b, and approves at e) · full (all five
  gates). (Lite,
  gates a and e only, was withdrawn by decision 21 and is gone since 0.2.14.)
- review [deferred]: deferred (a review panel decides a judgment item inside a phase in
  fresh contexts and the run continues; the owner reads "Decisions taken for you" at the
  next gate and overturns any of them with a review comment; decisions 21 and 32) · parked
  (a judgment item inside a phase parks the change for the owner; still available per
  project and per change). An escalation on a risk-list item, a guardrail file change, a
  run limit, an infrastructure failure, a merge to main and a deploy still park in both
  modes; a risk-list hit itself parks nothing (decision 35: it is a line of the "Needs your
  close look" banner on the PR the owner merges, and the merge accepts it).
- deploy action [none]: what makes a merged change live — publish package · schedule job ·
  regenerate report · promote to paper trading · deploy service · none
- real production? [no] — turns on the release label and the production gate
- maintain metric and source [ci_test_failure_rate from github-actions]
- confirm or override the detected build/test/lint commands and the setup (install) command
- the risk list is not asked here (decision 35): the install script proposes the four default
  items, each with the globs that match folders this project already has (a migrations
  folder, `infra/`, a production configuration, `auth/`, `payments/`; `init/detect.py
  risk_list`), an item no glob matches staying a plain string; the owner keeps or edits
  them in `sdlc.yaml` in the change-0000 PR, once

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
python "${CLAUDE_PLUGIN_ROOT}/plugin/init/sdlc_init.py" --root "${CLAUDE_PROJECT_DIR}" --profile <profile> --review <parked|deferred> --deploy-action "<action>" --deploy-production <true|false> --maintain-metric <metric> --maintain-source <source> [--claude-md-from changes/0000-sdlc-init/CLAUDE.proposed.md] [--build "<cmd>"] [--test "<cmd>"] [--lint "<cmd>"] [--setup "<cmd>"]
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
file-by-file result, the `outdated` ones first. The other project files the install writes
create-only — `changes/README.md`, `evals/README.md`, `evals/check.py`, `lessons/README.md`,
`REVIEW.md`, `bands.yaml` — are never compared with the template: the report says `kept`
for them (`created` on a first install), never `outdated`; and `sdlc.yaml` reports
`unchanged` or `updated (added …)` with its comments kept as the first install wrote them
(only `updated (… comments dropped)` loses them). So on an upgraded project these files may
still describe an older plugin. Whenever a workflow copy is `outdated`, say so to the owner
and name the template copies (`${CLAUDE_PLUGIN_ROOT}/template/`) to diff by hand; the
framework never rewrites them. For an outdated `sdlc-build.yml` or `sdlc-fix.yml`, also say:
replace sdlc-build.yml and sdlc-fix.yml to get the build caps (decision 32; an older copy
keeps the build and every fix round on the general caps). The report's `maintain.observation` line
says whether the maintain metric will have an observation: a project whose only workflows
are the framework's (`SDLC …`, excluded from the metric by design) has none until it
carries its own CI workflow — say so to the owner in the report, with the one-line workflow
to add (run the test command on `push` and `pull_request`). Re-running is safe: it merges and never
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
python "${CLAUDE_PLUGIN_ROOT}/plugin/state/cli.py" commit-phase --root "${CLAUDE_PROJECT_DIR}" --id 0000 --phase a --message "sdlc-init: connect the SDLC framework" --paths sdlc.yaml .claude/settings.json REVIEW.md CLAUDE.md changes ruff.toml evals bands.yaml lessons .github/workflows .github/scripts --start-point <default branch> --push
```
(paths that do not exist, such as an uncreated `ruff.toml`, are skipped; `.github/workflows`
and `.github/scripts` carry the fourteen `sdlc-*.yml` workflows (`sdlc-merge.yml` since
1.0.18) and `sdlc_pin.py` the install
wrote — without them the merged project has no automation, and every pin step's `git show` of
the script fails; a project's own workflow file already there rides along only if it was
uncommitted, so commit the project's own work first). Then open the PR exactly as
`/sdlc-plan` step 6 does:
`python "${CLAUDE_PLUGIN_ROOT}/plugin/pr/cli.py" upsert --root "${CLAUDE_PROJECT_DIR}" --id 0000 --phase a`
(title `intent(0000): <title>`, label `sdlc:a-ready`, the generated ≤5-bullet summary from
`changes/0000-sdlc-init/intent.md`; routes gh → REST API → compare URL for the owner). In the
report, add what the summary cannot know: the detected targets and their health, and the
files the owner should review (CLAUDE.md trim, settings, the risk list's globs). Merge =
accept: it also confirms the risk list, and accepts any risk-list hit the PR's "Needs your
close look" banner shows (gate (a) matches the globs on this PR's own files, decision 35).

## 6. After the merge (tell the owner, do not do it)
- The plugin is declared in `.claude/settings.json`. A local interactive session installs it
  from the marketplace once the owner accepts the trust dialog for the folder. A cloud
  session never shows that dialog, so the repository's marketplace declaration is ignored
  there ("marketplace not registered"): the owner adds four lines to the cloud environment's
  setup script — `claude plugin marketplace add luissiviero/sdlc-framework`,
  `claude plugin marketplace update sdlc-framework`, `claude plugin install
  sdlc@sdlc-framework --yes` and `claude plugin update sdlc@sdlc-framework` (the two
  `update` lines refresh the environment's cached copy after a framework release; see
  `docs/NOTES.md` §3a).
- The phase workflows open pull requests with the workflow token, which GitHub refuses
  until the owner turns on, once per repository, Settings → Actions → General → Workflow
  permissions → "Allow GitHub Actions to create and approve pull requests" (NOTES §11a).
  Without it every phase job ends with "GitHub Actions is not permitted to create or
  approve pull requests" after the phase has run. The workflows also need the repository
  secret `CLAUDE_CODE_OAUTH_TOKEN` or `ANTHROPIC_API_KEY` (NOTES §2).
- The GitHub App the automation pushes and opens pull requests as (decision 33), so the
  project's CI runs on its heads with no approval click and the events it causes start
  workflow runs. Create a GitHub App on the owner's account (Settings → Developer settings →
  GitHub Apps → New GitHub App) with the webhook turned off and these repository
  permissions: Actions, Checks, Contents, Issues and Pull requests read and write; Metadata
  read; Workflows **no access**, so the App can never change a workflow file. Generate a
  private key and install the App on this repository only. Store the App ID as the
  repository **variable** `SDLC_APP_ID` and the `.pem` file's content as the repository
  **secret** `SDLC_APP_PRIVATE_KEY` (Settings → Secrets and variables → Actions). Never add
  this App to a ruleset's bypass list: the phase runners hold its token, and GitHub grants a
  bypass to an actor, not to a job (choice 242, point 4); the merge App below is the only
  bypass actor besides you. This App is required since 1.0.18 (R22): `/sdlc-init` stops
  before writing anything until it is set (step 0), and without the variable the runner
  stops every phase run with the reason instead of running on the workflow token. The
  workflow token stays the in-job fallback once the App's token is 50 minutes old, the
  model session's token, and the token of the workflows that mint no App token. All of it
  is desktop-only (ROADMAP R21). On an upgrade to 1.0.9 or later,
  replace all thirteen `sdlc-*.yml` workflows (delete each and re-run /sdlc-init) and bump
  the pin in `sdlc.yaml` to 1.0.9 in the same pull request: the 1.0.9 copies persist no git
  credential in the checkout, and an older pinned framework would then push with none. On
  an upgrade to 1.0.18, re-running /sdlc-init installs `sdlc-merge.yml`; bump the pin in
  `sdlc.yaml` to 1.0.18 in the same pull request, since the copy runs
  `plugin/ci/merge_step.py`, which an older pinned framework does not have; replacing
  `sdlc-digest.yml` gives the digest its `checks: read` for the approved, unmerged build PR's
  line.
- The merge App (decision 36; ROADMAP R22): gate (e) is your approving review on the build
  PR, and a GitHub App of its own merges on it, so the approval is your only act there.
  It is not the App above: GitHub grants a bypass to an actor, not to a job, and only this
  App is a bypass actor of ruleset 1 (choice 242, point 4). Desktop-only (ROADMAP R21).
  1. Create a second GitHub App on your account
     (`https://github.com/settings/apps/new`): webhook off; repository permissions
     Contents read and write, Pull requests read and write, Metadata read; Workflows
     **no access**; no other permission. Generate a private key and install the App on
     this repository only.
  2. Create the environment `sdlc-merge` (Settings → Environments → New environment,
     `https://github.com/<owner>/<repo>/settings/environments`): no required reviewer, no
     wait timer; Deployment branches and tags → "Selected branches and tags" → add the rule
     `main` (your default branch's name), so only a run on the default branch reads its
     key. In that environment add the **variable** `SDLC_MERGE_APP_ID` (the App ID) and
     the **secret** `SDLC_MERGE_APP_PRIVATE_KEY` (the `.pem` file's content), never as a
     repository secret, which every workflow on every branch could read. Environments
     on a private repository need a paid plan (GitHub's documentation); on a free private
     repository the merge stays yours (fallback C1).
  3. Add this App to ruleset 1's bypass list (the ruleset bullet below), in "For pull
     requests only" mode.
  Without `SDLC_MERGE_APP_ID` the merge workflow says so and stops: you merge the build PR
  after approving it (fallback C1).
- On an organization repository, set `owner: <your login>` in `sdlc.yaml` (decision 34);
  otherwise no `@claude` comment or "Request changes" review starts a round and no
  `sdlc:c-approved` or `sdlc:d-approved` label counts. A personal repository needs nothing.
- The branch ruleset on the default branch (decision 4: only the owner merges; the
  automation identity has branch-only write access). The framework never creates it — a
  session must not be able to — and nothing but this rule keeps a session or a workflow
  from pushing to the default branch or merging its own pull request: the workflow token
  holds `contents: write` and the phase session may run `gh`, so a rule that only requires
  a pull request (with no approvals) or only stops direct pushes still lets `gh pr merge`
  through. Settings → Rules → Rulesets → New branch ruleset: target the default branch,
  **"Restrict updates"** with the repository admin (the owner) as the only bypass actor
  besides the merge App —
  the one rule that keeps a merge to the owner and to the merge App, which merges only on
  the owner's approval —, plus "Restrict deletions", "Block force
  pushes" and "Require a pull request before merging". Since 1.0.18 the merge App above is
  its second bypass actor, in "For pull requests only" mode (decision 36). The owner's
  bypass actor's mode is
  **Exempt** (the `…` menu of the actor's row in the bypass list): the rules do not run for
  the owner, so a merge from the GitHub mobile app goes through on a tap — the app still
  labels the pull request "Unable to merge", because it shows the general merge state, which
  is `blocked` for everyone the rules apply to; under "Allow for pull requests only" the app
  shows the same label with no bypass control and the owner merged from the web UI through
  its bypass checkbox (both verified live on 2026-09-27, NOTES §17; whether a tap would also
  have merged under that mode was not tested). From a terminal, `gh pr merge` refuses a
  `blocked` pull request before asking GitHub: use the REST merge endpoint through `gh api`
  or the web UI. The cost of Exempt is that GitHub writes no bypass audit entry for the
  owner's merges (the merge commit and the pull request's `merged_by` remain the record);
  the rules still run for every other actor, the workflow token included. The daily digest
  says so at the top
  of the review queue while the default branch has no such rule (`pr/digest.py`,
  `pr/github.py default_branch_protection`: the branch's active rules must include an
  `update` rule; the classic `protected` flag is reported but does not count, since on a
  user-owned repository a classic rule cannot restrict who pushes; since 0.2.25).
- Ruleset 2, which holds a build PR whose review is not green (decision 36, point 5;
  plugin 1.0.18). Desktop-only (ROADMAP R21). Settings → Rules → Rulesets → New branch
  ruleset (`https://github.com/<owner>/<repo>/settings/rules`): name
  `sdlc/review on every pull request (decision 36)`; enforcement **Active**; target the
  default branch ("Include default branch"); bypass list: the repository admin role (you),
  in "For pull requests only" mode; one rule, **"Require status checks to pass"**, with the
  check `sdlc/review` added from any source and "Require branches to be up to date before
  merging" off; no other rule, and no required approval (decision 4's reason: your own
  intent PRs could not pass one). Every pull request that is not a build PR gets a passing
  `sdlc/review` ("not a build PR") from `sdlc-merge.yml` or from the step that opens it,
  so intent, design, incident and your own PRs merge as before; a build PR whose review is
  red merges only through the web UI's bypass checkbox, a deliberate act. When you set it
  up, set your own bypass mode in ruleset 1 to **Exempt** if it is not already (choice
  242, point 5), so your merges from the phone still go through.
- Optional, owner's machine only: `docs/owner-machine/README.md` in the framework repo
  explains the managed settings file and its machine-wide consequences.

Never edit `.claude/**`, `CLAUDE.md`, `REVIEW.md` or `sdlc.yaml` directly; only the install
script writes them, and the owner reviews the result in the PR. Never use bypass-permissions
mode. Never notify anyone.
