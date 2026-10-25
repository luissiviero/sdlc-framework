---
description: Connect the SDLC framework to this project in one command — phase adapters into sdlc.yaml, one-command build/test/lint targets (Python or Node detected), guardrail hooks and permissions, CLAUDE.md skeleton, REVIEW.md, changes/, evals/, bands.yaml — committed as the project's first PR (change 0000). Idempotent; re-run to upgrade.
argument-hint: [none; it asks its questions in one round]
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
`npm test`, `npm run lint`, `npm run build`). It counts each language's source files and
manifests first (the report's `detection.signals`): the targets are detected only when
Python or Node holds two source files in three, so a mixed repository, or a Go, Rust, Java,
.NET or Ruby project, comes back with every target `none` and a note naming the signals
(R61). For other languages, or when a target is reported as `none`, ask the owner for the
command and pass it with `--build/--test/--lint`; the gate does not enter the build phase
without all three. The report's `proposed` block shows what else the install writes for the owner
to confirm in the change-0000 PR: the package registries the CI session may reach
(`sandbox.allowed_domains`), the secret-shaped files found (`protected_paths`, and the same
names as `Read` deny rules; `.npmrc` and `appsettings.*.json` only when one holds a token,
a password, a secret or a connection string), and the formatter commands per file type (`hooks.formatters`:
black, yapf or autopep8 from `pyproject.toml`, prettier and eslint from `package.json`,
rustfmt for `Cargo.toml`; ruff stays Python's default with no entry). Detection also proposes `commands.setup`
— the one command that installs what those three need (`python -m pip install -e ".[dev]"`,
`npm ci`, ...), which the CI phase jobs run before every phase; override it with `--setup`
and pass `--setup ""` when the project has nothing to install. When a drive is proposed
(below), an explicit `--setup` must install `@playwright/test` and its browsers itself: it is
written as given, with nothing appended, and the report's drive origin says so.
Detection proposes `commands.drive` too (change 0004), the optional fourth target that
exercises the product after the session: when `package.json` lists `@playwright/test` under
`dependencies` or `devDependencies`, the plain line `npx playwright test`, with
` && npx playwright install --with-deps` appended to the detected setup for the browsers
(`npm ci` or `npm install` installs `@playwright/test` itself); for every other project `""`,
no drive. The owner confirms it like the three targets, or passes `--drive "<cmd>"` (`""` =
none). The proposed line is plain `npx playwright test`, and the Playwright test writes its
screenshots and JSON files to paths under `process.env.SDLC_PROOF_DIR` (a line the owner
writes by hand may still use the variable: the platform shell expands `$SDLC_PROOF_DIR`, and
a by-hand run under `cmd.exe` writes `%SDLC_PROOF_DIR%`).
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
- Not asked (decision 37): the gates and the review mode are one behaviour for every
  project. The owner merges at the intent and design gates and approves at the deploy
  gate; the build and test gates are the confidence gate's. A judgment item inside a phase goes to a review panel in fresh contexts and the
  run continues; the owner reads "Decisions taken for you" at the next gate and overturns
  any of them with a review comment (decisions 21 and 32). An escalation on a risk-list
  item, a guardrail file change, a run limit, an infrastructure failure, a merge to main
  and a deploy still park; a risk-list hit itself parks nothing (decision 35: it is a line
  of the "Needs your close look" banner on the PR the owner merges, and the merge accepts
  it; at the deploy gate, the owner's approving review, on which the merge App merges, decision 36).
- deploy action [none]: what makes a merged change live — publish package · schedule job ·
  regenerate report · promote to paper trading · deploy service · none
- real production? [no] — turns on the release label and the production gate
- maintain metric and source [ci_test_failure_rate from github-actions; when the project
  has several workflows of its own, the detection report's `maintain.source` proposes
  `github-actions:<name>` for the one that runs the tests (R61): pass `--maintain-source`
  only when the owner names another]
- the repository secrets or variables the targets need [none]: names only, each passed as
  `--env NAME`; the install writes them under `commands.env` and into the setup and phase
  steps of the phase workflows. Say to the owner that the setup command, the session and
  the targets (which run code the session wrote, the targets outside the sandbox) can read
  them, so they should be test credentials, never production ones; a service a test needs
  (a database) is the owner's edit of the workflow, and the change-0000 intent says that
  tests bound to a service are deselected for now
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
python "${CLAUDE_PLUGIN_ROOT}/plugin/init/sdlc_init.py" --root "${CLAUDE_PROJECT_DIR}" --deploy-action "<action>" --deploy-production <true|false> --maintain-metric <metric> [--maintain-source <source>] [--env NAME ...] [--claude-md-from changes/0000-sdlc-init/CLAUDE.proposed.md] [--build "<cmd>"] [--test "<cmd>"] [--lint "<cmd>"] [--setup "<cmd>"] [--drive "<cmd>"]
```
It writes `sdlc.yaml`, `.claude/settings.json` (permissions + the pinned plugin
declaration; hooks come from the plugin), `REVIEW.md`, `changes/README.md`, builds
`CLAUDE.md` from the proposal plus the skeleton sections, creates `ruff.toml` when no linter
existed, creates `evals/` (empty suite, filled by incidents — decision 17) and `bands.yaml`
(control bands for the maintain metric — decision 15), and creates
`changes/0000-sdlc-init/` with an intent.md. It also installs the CI workflows (the phase
transitions, the release, the fix round, the abandon rule) and the daily digest under
`.github/`, create-only (an edited file is never overwritten). Re-running it on an upgrade
(R64) installs the workflow files a newer plugin adds, and compares each existing copy with
the template of every release (`plugin/init/template_hashes.json`):
- a copy an older release wrote and nobody changed since (the workflows, the pin script,
  `changes/README.md`, `evals/README.md`, `evals/check.py`, `lessons/README.md`,
  `policies/README.md`) is replaced with this version's and reported
  `refreshed (was <version>)`, the first release that shipped the text it had; the report's
  `refreshed` map lists them;
- an edited copy is kept, and so is one rendered with values the project no longer has
  (another framework repository, a renamed default branch, changed `commands.env` names): a
  workflow is reported `outdated: …`, a README or `evals/check.py` `kept; outdated (edited):
  …`; the owner diffs it with the template copy
  (`${CLAUDE_PLUGIN_ROOT}/template/`) to take the newer text, or keeps their edits;
- `REVIEW.md` and `bands.yaml` are guardrail files and never rewritten (decision 6): a
  `REVIEW.md` an older release wrote and nobody edited is reported `kept; outdated (was
  <version>): …` for the owner's reviewed PR; an edited one and `bands.yaml` are the owner's
  content and say `kept`;
- `sdlc.yaml` reports `unchanged` or `updated (added …)` with its comments kept as the first
  install wrote them (only `updated (… comments dropped)` loses them).

Read its JSON report and show the owner the file-by-file result, the `outdated` ones first,
then the `refreshed` ones; the refreshed copies ride in the same PR as the pin, so the two
move together, and the PR body lists them. Whenever a copy is `outdated`, say so to the owner
and name the template copy to diff by hand; the framework never rewrites an edited one. For an outdated `sdlc-build.yml` or `sdlc-fix.yml`, also say:
replace sdlc-build.yml and sdlc-fix.yml to get the build caps (decision 32; an older copy
keeps the build and every fix round on the general caps). The report's `maintain.observation` line
says whether the maintain metric will have an observation: a project whose only workflows
are the framework's (`SDLC …`, excluded from the metric by design) has none until it
carries its own CI workflow — say so to the owner in the report, with the one-line workflow
to add (run the test command on `push` and `pull_request`). Re-running is safe: it merges and never
overwrites the owner's edits. This script is the only sanctioned writer of guardrail files in a run;
everything it writes rides in the change-0000 PR the owner merges.

## 4. Verify the feedback loop
Run and time the three commands from `sdlc.yaml` once (give the Bash call a timeout that
covers them):
```
python "${CLAUDE_PLUGIN_ROOT}/plugin/init/sdlc_init.py" --root "${CLAUDE_PROJECT_DIR}" --time-commands
```
and paste each target's output, exit code and seconds from its JSON report. A target that
fails is reported, not hidden: the owner decides whether to fix the project or change the
target. It raises `gate.command_timeout` to three times the longest run when that is above
the template's 900 seconds (the CI session's Bash timeout follows it, R61); when its
`workflows` line says to raise `timeout-minutes` and `SDLC_JOB_TIMEOUT_MINUTES`, tell the
owner the two numbers for `sdlc-build.yml` and `sdlc-fix.yml`. Commit the changed
`sdlc.yaml` with the rest in step 5.

## 5. Commit as the project's first PR (the intent gate of change 0000)
Branch policy: the framework's branch is `sdlc/0000/intent`. If this session's platform assigns
a branch and forbids pushing any other (Claude Code on the web does), run the command below
without `--push`, then push the resulting commit to the assigned branch and open the PR from
it, keeping the label; say in the PR body that the framework branch is `sdlc/0000/intent` locally.
```
python "${CLAUDE_PLUGIN_ROOT}/plugin/state/cli.py" commit-phase --root "${CLAUDE_PROJECT_DIR}" --id 0000 --phase intent --message "sdlc-init: connect the SDLC framework" --paths sdlc.yaml .claude/settings.json REVIEW.md CLAUDE.md changes ruff.toml evals bands.yaml lessons policies .github/workflows .github/scripts --start-point <default branch> --push
```
(paths that do not exist, such as an uncreated `ruff.toml`, are skipped; `.github/workflows`
and `.github/scripts` carry the fourteen `sdlc-*.yml` workflows (`sdlc-merge.yml` since
1.0.18) and `sdlc_pin.py` the install
wrote — without them the merged project has no automation, and every pin step's `git show` of
the script fails; a project's own workflow file already there rides along only if it was
uncommitted, so commit the project's own work first). Then open the PR exactly as
`/sdlc-intent` step 6 does:
`python "${CLAUDE_PLUGIN_ROOT}/plugin/pr/cli.py" upsert --root "${CLAUDE_PROJECT_DIR}" --id 0000 --phase intent`
(title `intent(0000): <title>`, label `sdlc:intent-ready`, the generated ≤5-bullet summary from
`changes/0000-sdlc-init/intent.md`; routes gh → REST API → compare URL for the owner). In the
report, add what the summary cannot know: the detected targets and their health, and the
files the owner should review (CLAUDE.md trim, settings, the risk list's globs), and the
acts of step 6 the owner does after the merge, each settings act marked desktop-only with
its direct link (ROADMAP R21). Merge =
accept: it also confirms the risk list, and accepts any risk-list hit the PR's "Needs your
close look" banner shows (the intent gate matches the globs on this PR's own files, decision 35).

## 6. After the merge (tell the owner, do not do it)
- The plugin is declared in `.claude/settings.json`. A local interactive session installs it
  from the marketplace once the owner accepts the trust dialog for the folder. A cloud
  session never shows that dialog, so the repository's marketplace declaration is ignored
  there ("marketplace not registered"): the owner adds four lines to the cloud environment's
  setup script — `claude plugin marketplace add luissiviero/sdlc-framework`,
  `claude plugin marketplace update sdlc-framework`, `claude plugin install
  sdlc@sdlc-framework --yes` and `claude plugin update sdlc@sdlc-framework` (the two
  `update` lines refresh the environment's cached copy after a framework release; see
  `docs/notes/3.md`, 3a).
- The phase workflows open pull requests with the workflow token, which GitHub refuses
  until the owner turns on, once per repository, Settings → Actions → General → Workflow
  permissions → "Allow GitHub Actions to create and approve pull requests" (NOTES §11a;
  `https://github.com/<owner>/<repo>/settings/actions`). Without it every phase job ends
  with "GitHub Actions is not permitted to create or approve pull requests" after the phase
  has run. The workflows also need the repository secret `CLAUDE_CODE_OAUTH_TOKEN` or
  `ANTHROPIC_API_KEY` (NOTES §2; Settings → Secrets and variables → Actions,
  `https://github.com/<owner>/<repo>/settings/secrets/actions`). Both are desktop-only: the
  GitHub mobile app shows no repository settings, so open the links in a desktop browser,
  or in the phone browser's desktop mode (ROADMAP R21). In the report, name both with
  their links filled with the project's owner and repository, and say they are
  desktop-only.
- The GitHub App the automation pushes and opens pull requests as (decision 33), so the
  project's CI runs on its heads with no approval click and the events it causes start
  workflow runs. Create a GitHub App on the owner's account (Settings → Developer settings →
  GitHub Apps → New GitHub App, `https://github.com/settings/apps/new`) with the webhook
  turned off and these repository
  permissions: Actions, Checks, Contents, Issues and Pull requests read and write; Metadata
  read; Workflows **no access**, so the App can never change a workflow file. Generate a
  private key and install the App on this repository only. Store the App ID as the
  repository **variable** `SDLC_APP_ID` and the `.pem` file's content as the repository
  **secret** `SDLC_APP_PRIVATE_KEY` (Settings → Secrets and variables → Actions,
  `https://github.com/<owner>/<repo>/settings/variables/actions` and
  `https://github.com/<owner>/<repo>/settings/secrets/actions`). Never add
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
  line. On an upgrade to 1.0.22, replace `sdlc-abandon.yml`, `sdlc-runbook.yml` and
  `sdlc-scan.yml` (they may now write checks, so their pull requests get the "not a build
  PR" check ruleset 2 requires), `sdlc-digest.yml` (it reads the `sdlc-merge` environment)
  and `sdlc-merge.yml` (its pinned actions), with the pin in the same pull request. On an
  upgrade to 1.0.38, re-run /sdlc-init in the pin's pull request: it adds
  `Edit(/policies/**)` to `.claude/settings.json`, which the build's preflight requires from
  that version on (decision 40); without it the first build parks with the missing rule.
- The merge App (decision 36; ROADMAP R22): the deploy gate is your approving review on the build
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
  after approving it (fallback C1). The daily digest says so at the top while the
  environment lets a branch other than the default one use it, or while the key is also a
  repository secret (choice 250). The merge job runs its actions pinned by commit SHA;
  when you refresh `sdlc-merge.yml` from a later framework version, keep the pins it brings.
- On an organization repository, set `owner: <your login>` in `sdlc.yaml` (decision 34);
  otherwise no `@claude` comment or "Request changes" review starts a round. A personal
  repository needs nothing.
- The branch ruleset on the default branch (decision 4: only the owner merges; the
  automation identity has branch-only write access). The framework never creates it — a
  session must not be able to — and nothing but this rule keeps a session or a workflow
  from pushing to the default branch or merging its own pull request: the workflow token
  holds `contents: write` and the phase session may run `gh`, so a rule that only requires
  a pull request (with no approvals) or only stops direct pushes still lets `gh pr merge`
  through. Desktop-only (ROADMAP R21). Settings → Rules → Rulesets → New branch ruleset
  (`https://github.com/<owner>/<repo>/settings/rules`): target the default branch,
  **"Restrict updates"** with the repository admin (the owner) as the only bypass actor
  besides the merge App —
  the one rule that keeps a merge to the owner and to the merge App, which merges only on
  the owner's approval —, plus "Restrict deletions", "Block force
  pushes" and "Require a pull request before merging". Since 1.0.18 the merge App above is
  its second bypass actor, in "For pull requests only" mode (decision 36). The owner's
  bypass actor's mode is
  **Exempt** (the `…` menu of the actor's row in the bypass list): this ruleset does not
  run for you, so the phone's merge label shows ruleset 2's verdict alone (below). Exempt
  alone would also let anything that acts as your login write to the default branch
  directly, which a cloud session's GitHub tools and git proxy do. Ruleset 2's
  no-direct-writes rules close that (choice 251, tested live on 2026-10-22, NOTES §57).
  No setting stops a session acting as your login from merging a pull request through the
  API. From a terminal, `gh pr merge` refuses a `blocked` pull request before asking GitHub:
  use the REST merge endpoint through `gh api` or the web UI. The rules run for every other
  actor, the workflow token included. The daily digest
  says so at the top
  of the review queue while the default branch has no such rule (`pr/digest.py`,
  `pr/github.py default_branch_protection`: the branch's active rules must include an
  `update` rule; the classic `protected` flag is reported but does not count, since on a
  user-owned repository a classic rule cannot restrict who pushes; since 0.2.25).
- Ruleset 2, which holds a build PR whose review is not green (decision 36, point 5;
  plugin 1.0.18) and refuses a direct write to the default branch by your login (choice
  251, plugin 1.0.23). Desktop-only (ROADMAP R21). Settings → Rules → Rulesets → New branch
  ruleset (`https://github.com/<owner>/<repo>/settings/rules`): name
  `review and no direct writes on main (decision 36, choice 251)`; enforcement **Active**;
  target the default branch ("Include default branch"); bypass list: the repository admin
  role (you), in "For pull requests only" mode, so your bypass never covers a push. Four
  rules:
  - **"Require status checks to pass"**, with the check `sdlc/review` added from any
    source and "Require branches to be up to date before merging" off;
  - **"Require a pull request before merging"**, with required approvals **0** and every
    other option under it off (decision 4's reason: your own intent PRs could not pass a
    required approval);
  - **"Block force pushes"**;
  - **"Restrict deletions"**.

  Nothing else. Every pull request that is not a build PR gets a passing `sdlc/review`
  ("not a build PR") from `sdlc-merge.yml` or from the step that opens it, so intent,
  design, incident and your own PRs merge as before, and the phone shows them "Ready to
  merge". A build PR whose review is red, or a pull request with no `sdlc/review` yet,
  shows "Unable to merge" and merges only through your bypass, a deliberate act: the web
  UI's bypass checkbox, or the phone's Merge under that label (verified for a bypass in
  this mode, NOTES §57). A session's direct commit to the default branch is refused (NOTES
  §57). A project set up with plugin 1.0.18 to 1.0.22 has ruleset 2 with the check alone:
  add the three rules to it, rename it, and keep your bypass in ruleset 1 Exempt.
- Optional, owner's machine only: `docs/owner-machine/README.md` in the framework repo
  explains the managed settings file and its machine-wide consequences.

Never edit `.claude/**`, `CLAUDE.md`, `REVIEW.md`, `sdlc.yaml` or `policies/**` directly;
only the install script writes them, and the owner reviews the result in the PR. Never use
bypass-permissions mode. Never notify anyone.
