# The trial readiness review (2026-10-20)

The owner asked, before the real-project trial: what will break or embarrass the framework on the first real project that the sample never exercised? Report only; nothing was fixed. This page is written in the spirit of `2026-09-26-readiness-review.md`, but the question is different: not "is the repository consistent with its own contract" but "what does a repository that is not `sdlc-sample-python` do to the plugin and the template".

## Method and assumptions

One session, 35 minutes, one reader. Read first: `docs/decisions/index.md`, `docs/notes/index.md`, the Order column of `docs/ROADMAP.md`, the Summary and Left of `docs/PROGRESS.md`. Then only the files a real project's differences land in: `plugin/init/detect.py`, `plugin/init/sdlc_init.py`, `plugin/commands/sdlc-init.md`, `template/sdlc.yaml`, `template/CLAUDE.md`, `template/.github/workflows/*.yml`, `plugin/ci/settings.ci.json`, `plugin/ci/project_setup.py`, the relevant parts of `plugin/ci/run_phase.py`, `plugin/gate/checks.py`, `plugin/detect/source.py`, `plugin/hooks/format_on_edit.py`, `plugin/hooks/plan_sync.py`, `plugin/hooks/secrets_check.py`, `plugin/pr/description.py`. File and line numbers are as read at commit 8546217 (`main`, 2026-10-20). Nothing was run against a real repository: every risk below is read from the code, and where a claim would need a live run to settle, it says so.

Assumptions, stated so the ranking can be judged:

- The trial project is a GitHub-hosted repository the owner already works in: it has its own CI workflows, branches, a formatter, a default branch that may not be `main`, and files that hold real credentials.
- It is not Python-only. Even a Python service has a front end, a `Dockerfile`, SQL migrations, shell or Node tooling; the review treats "more than one language" as the normal case.
- Its build and test take minutes, not seconds, and at least part of the test suite needs a service (a database, a queue) or an environment variable the sample never had.
- The owner reads and acts on pull requests mostly from the GitHub mobile app.
- The roadmap ranks 8 to 20 (R24, R22, R51, R25, R44, R18, R29/R54, R26, R52, R33, R14, R27, R45) land before the trial in that order, as choice 238 and choice 239 say; the sandbox proof lands next. A risk is counted as "covered" only when a row before the trial names the mechanism, not when a row after it does.
- `deploy.action` on the trial project is `none` or a by-hand release: `deploy.command` runs on the runner with the repository's secrets and no GitHub `environment:`, so a real deployment through it is out of scope for a first trial (R39, rank 43, is the row for that).

## What the sample never exercised

The sample is one Python package, four functions, one pytest module, no dependency outside pytest and ruff, a build of one second, no service, no secret that matters, one CI workflow named `CI`, no other contributor and no history. Every green live check in `docs/notes/` is a check of the plugin against that shape. The risks below are, each, a place where the code assumes that shape.

## The risks

Each risk: where it lives (file and line), whether a roadmap row before the trial covers it (row and rank), and if not, the smallest thing that would.

### 1. The CI session can run Python and Node, and nothing else

**Where.** `plugin/ci/settings.ci.json:20-36` is the allow list of every unattended phase run: `git`, `gh`, `python`, `python3`, `npm`, `npx`, `node`, `pytest`, `ruff`, plus the file tools. `--permission-prompts none` denies everything else (the file's own comment, line 2). `run_phase.ci_settings_file` (`plugin/ci/run_phase.py:2060-2091`) rewrites the deny rules and appends the project's `protected_paths` to `denyWrite`, and adds no allow rule. The project's own `.claude/settings.json` does get rules derived from the detected commands (`plugin/init/sdlc_init.py:78-82` builds `Bash(<first three words> *)`; `template/.claude/settings.json:17-20`), so a local session on the owner's machine can run `go test ./...` or `cargo test`; the CI session cannot. The sandbox's network allow list (`settings.ci.json:44-53`) names `pypi.org`, `files.pythonhosted.org` and `registry.npmjs.org` only: no `proxy.golang.org`, `crates.io`, `repo.maven.apache.org`, `api.nuget.org`, `rubygems.org`, `ghcr.io`, `docker.io`.

**What happens.** On a Go, Rust, Java, .NET, Ruby, PHP or Make project the build run edits code for up to 400 turns without once being able to run the tests it is asked to run before "done" (`template/CLAUDE.md:35-41` tells it to run all three and paste the output). The first time the targets run is the runner's commands step after the session (`run_phase.py:2310-2318`). A red target then starts a fix round (decision 29), which is just as blind. Three blind rounds (`gate.max_iterations: 3`) and the change parks. The sample never saw this because `python` and `pytest` are on the list.

**Roadmap.** Not covered. R44 (rank 12) closes the sandbox further; it opens nothing. R33 (rank 17) is the formatter hook, not the permission list. R53 measures setup time only.

**Smallest fix.** `ci_settings_file` appends the same three `_rule_for` rules the project settings carry (`commands.build`, `commands.test`, `commands.lint`, plus `commands.setup`), and `sdlc.yaml` gains an optional `sandbox.allowed_domains` list that `ci_settings_file` appends to the network allow list; `/sdlc-init` proposes the registry for the detected or declared toolchain. A test each. One plugin version.

### 2. Detection says "Python" whenever one `.py` file exists

**Where.** `plugin/init/detect.py:331-340`: `detect()` returns the Python detection whenever `detect_python` reports `language == "python"`, and only then looks at `package.json`. `detect_python` (`:166-182`) calls the project Python when `py_files > 0` or a `pyproject.toml` or `setup.py` exists. A Node, Go or Java repository with a `scripts/release.py`, a `conftest.py` for an end-to-end harness, or a `docs/conf.py` is "python": the test target becomes `python -m pytest` (if any `test_*.py` exists) or `python -m unittest discover -v` (`:200-206`), the lint target `python -m ruff check .` with a created `ruff.toml` (`:233-241`; `sdlc-init.md:62`), the build `python -m compileall -q .` (`:252-257`), the setup `python -m pip install pytest ruff` (`:127-131`), and `test_paths` the Python globs (`:24-31`), so the test-file lock of a fix change (`plugin/hooks/test_file_lock.py`) freezes nothing the project's tests live in.

**What happens.** `/sdlc-init` step 0 shows the detection and asks the owner to override (`sdlc-init.md:18-28`), so an attentive owner catches it. Two things make it embarrassing anyway. First, the detected commands are written into the project's `CLAUDE.md` twice (`template/CLAUDE.md:11-13` and `:37-39`) and appended to an existing `CLAUDE.md` as skeleton sections (`sdlc_init.py:187-190`), a guardrail file the owner then has to fix in a reviewed PR. Second, the report's "healthy output" lines (`detect.py:195-199`) describe pytest output on a project that has no pytest, and the `/sdlc-init` step 4 run of the three commands "passes" (compileall of three helper scripts, ruff of the same, unittest discovery of nothing) and so hides the mismatch.

**Roadmap.** Not covered. R33 (rank 17) names rustfmt and prettier for the formatter hook only and says `/sdlc-init` proposes them; it does not change which language `detect()` picks.

**Smallest fix.** `detect()` counts the signals per language it knows (Python files, `package.json` and JS/TS files, `go.mod`, `Cargo.toml`, `pom.xml`/`build.gradle*`, `*.csproj`/`*.sln`, `Gemfile`, `composer.json`, `Makefile`) and, when the dominant one is not Python or Node, returns `language: <name>` with every target `None` and a note naming the language, so `sdlc-init.md:22-25`'s "ask the owner for the command" path is actually reached; when Python is present but not dominant, the same. The report says which signals it counted. `test_paths` gains the conventional folders for the languages it names (`detect.py:24-42` already has an `unknown` entry). A test per language. One plugin version.

### 3. The maintain metric is the failure rate of every workflow the project has

**Where.** `plugin/detect/source.py:71` and `:134-156`: a run counts when it completed with `success` or `failure` on a counted event, its workflow name does not start with `SDLC `, its actor is not the automation and its head is not a work branch. `counts()` accepts a `workflow` name (`:136`, `:151`), but `sdlc.yaml` has no key for it: `template/sdlc.yaml:84-89` sets `maintain.metric` and `maintain.source` only, and the sample's `source: github-actions` was proven against one workflow named `CI`.

**What happens.** A real repository has a lint workflow, a CodeQL scan, a release workflow, a nightly job, a deploy that is red by design when a preview environment is down. The "CI test failure rate" the detection watches becomes the failure rate of all of them. A nightly that fails three days running files a tier-2 or tier-3 incident (`plugin/detect/cli.py`), opens a diagnosis or a proposed fix PR, and the first thing the trial owner sees from phase (f) is an incident about a workflow the change never touched. The sample's single `CI` workflow could not show this.

**Roadmap.** Not covered before the trial. R40 (rank 41) says "the next metric is a project setting" and lands after the trial. R30 (rank 28) lists the detection's needs in the change-0000 intent but does not name the workflow.

**Smallest fix.** `maintain.workflow: <name>` in `template/sdlc.yaml`, passed by `detect/cli.py` to `daily_series` as the `workflow` argument that already exists; `/sdlc-init` asks for it beside the metric (`sdlc-init.md:42`) and `maintain_observation` (`sdlc_init.py:402`) names it in the report. Unset keeps today's behaviour, so the sample is unchanged. One test. The smallest fix of the five.

### 4. The feedback loop on a real build: minutes, services and environment

Three related gaps; the sample's one-second, dependency-free build hid all of them.

**4a. Duration.** `template/sdlc.yaml:136` sets `command_timeout: 900` per target, and the runner waits `3 × command_timeout + grace` for the commands step (`run_phase.py:2310-2318`). A 20-minute `gradle build` or Docker-based test run times out, the gate records "timed out", and the owner learns from `run_phase.py:352-370` that raising `command_timeout` also means raising `timeout-minutes` and `SDLC_JOB_TIMEOUT_MINUTES` in `sdlc-build.yml:73,77` and `sdlc-fix.yml` by hand, after which both workflow copies read `outdated` at every upgrade (`sdlc-init.md:67-80`). Inside the session nothing sets `BASH_DEFAULT_TIMEOUT_MS` (no hit in `run_phase.py`), so each Bash call of the test command inside the sandbox runs under Claude Code's default two-minute timeout: a test suite that takes four minutes never returns a result to the model, which then guesses.

**4b. Services.** The workflows have no `services:` block (`sdlc-build.yml:55-78`) and `commands.setup` is one command with a fifteen-minute timeout (`project_setup.py:66`) that runs outside the sandbox. A test suite that needs Postgres, Redis or a browser has no route in `sdlc.yaml`; the owner's only way is to edit the thirteen workflow files, with the `outdated` cost above. Inside the sandbox, whether the session can reach a service the setup command started on `localhost` was not verified in this review.

**4c. Environment.** The gate's commands step runs the targets with `commands_env()` (`run_phase.py:2406-2414`): the runner's environment minus the credentials. No repository secret or variable reaches the test command, and `sdlc.yaml` has no key to name one. A suite that reads `DATABASE_URL` or `STRIPE_TEST_KEY` from the environment fails at the gate on every run.

**Roadmap.** Partly. R25 (rank 11) makes every outer bound park instead of ending red, so a timeout parks cleanly; it does not lift the bound. R53 says "no build on this measure" (its Order cell, 2026-10-19). R14 (rank 18) adds a fourth target, not an environment. R39 (rank 43) is a preview environment for deploys, after the trial. Nothing covers 4b or 4c.

**Smallest fix.** For 4a: `/sdlc-init` step 4 already runs the three commands once (`sdlc-init.md:89-91`); time them, write `command_timeout` as three times the longest run (minimum 900) and print the two workflow numbers the owner must set when it exceeds the template's, and set `BASH_DEFAULT_TIMEOUT_MS` to `command_timeout` in the session's environment. For 4c: `commands.env: [NAME, ...]` in `sdlc.yaml`, a list of repository secret or variable names the phase jobs pass through to the setup command, the session and the commands step (`commands_env` keeps them; the hidden set stays). For 4b: a documented line in `/sdlc-init` step 6 and the change-0000 intent that tests needing a live service are excluded from the test target for the trial (a marker the command deselects), with `services:` left to the owner's edit of the workflow. Two small plugin changes and one documentation line.

### 5. Secrets that matter: the deny list knows two spellings

**Where.** `settings.ci.json:5-8` denies `Read(.env*)`, `Read(**/.env*)`, `Read(./secrets/**)`, `Read(**/secrets/**)`. `template/sdlc.yaml:167` ships `protected_paths: []` and `/sdlc-init` proposes nothing for it. The secrets hook (`plugin/hooks/secrets_check.py:36-55`) matches named keys and known token shapes on write, which is sound for what it covers.

**What happens.** A real repository keeps credentials where the sample never did: `config/*.pem`, `*.key`, `terraform.tfvars`, `credentials.json`, `appsettings.Production.json`, `k8s/*-secret.yaml`, `.npmrc` with a token, `docker-compose.override.yml` with passwords. The session may read every one of them into the model's context, and nothing but the secrets hook's patterns keeps one out of a commit. `risk_list` (`template/sdlc.yaml:113-117`) does not help: `risk_hits` is a whole-token phrase match on paths (`plugin/gate/checks.py:751-781`), so `production config` matches no real path and `data migrations` does not match `db/migrations/0002_add_col.sql`; only single-word items fire on paths. The sample had `.env` and nothing else, so the deny list was always enough.

**Roadmap.** Partly. R44 (rank 12) hides the model credential and `~/.ssh` from sandboxed shell commands; it does not extend the Read deny to the project's own secret files. R24 (rank 8) gives each risk item globs the owner confirms, which fixes the phrase-match blindness for the risk list; it does not touch the Read deny. R27 (rank 19) adds `policies/` to `denyWrite`.

**Smallest fix.** `/sdlc-init` scans the tree for a fixed list of secret-shaped globs (the ones above plus `*.p12`, `*.pfx`, `*.jks`, `id_rsa*`, `*.keystore`), proposes them as `protected_paths` entries and as `Read(...)` deny rules in the project's `.claude/settings.json`, and lists them in the report for the owner to confirm. `ci_settings_file` already appends `protected_paths` to `denyWrite`; it would append the same list to the Read deny. A test. One plugin version, or part of R44.

### 6. The owner on a phone (below the line, but the trial will show it first)

**Where.** `sdlc-init.md:113-171` is the owner's setup after the merge: the Actions workflow permission, the Claude secret, the GitHub App with its private key as a secret and its ID as a variable, the branch ruleset with an Exempt bypass actor. None of those can be done in the GitHub mobile app. The same page records (`:156-162`) that the app labels the pull request "Unable to merge" under the ruleset, and that a tap merging under Exempt was verified live once. The PR body puts "What I need from you" first (`plugin/pr/description.py:660`), which is right for a phone.

**What happens.** The trial's first hour is desktop work the framework never says is desktop work, and the owner's first gate (e) on the phone shows "Unable to merge" on a mergeable PR. Neither breaks anything; both embarrass.

**Roadmap.** Covered, but after the trial: R21 (rank 27) is exactly this; R19 (rank 29) the acts table.

**Smallest fix.** Pull R21's first part (the `/sdlc-init` report and step 6 say "desktop only" with the direct settings link, and the digest's unprotected-branch line) into the documentation PR that precedes R45's rename (rank 20), with no plugin version, so the trial owner reads it before the first setup.

### 7. Smaller findings (not ranked)

- **Trigger noise on a busy repository.** `sdlc-abandon.yml` runs on every closed PR, `sdlc-comment.yml` on every issue comment, `sdlc-design.yml` on every PR opened against the default branch, `sdlc-build.yml`, `sdlc-release.yml` on every merged one (the `on:` blocks of each). Each is a short green job that finds no change folder and skips (the comment at `sdlc-build.yml:57-62` says about 20 seconds), but a repository with ten PRs a week shows forty framework runs in its Actions tab beside its own CI. A `paths: [changes/**]` filter on the `pull_request` triggers that support it (opened, reopened, closed) removes most of it; the labeled and comment triggers cannot filter by path.
- **The formatter hook on a project that is not formatted by ruff.** `plugin/hooks/format_on_edit.py:5-6,32` runs `ruff check --fix` and `ruff format` on every edited `.py` file with the project's ruff configuration, or ruff's defaults (line length 88) when there is none. A Python project formatted with black at 120 or with yapf gets its edited files reformatted, so every build PR carries formatting noise the owner reads on a phone. R33 (rank 17) makes the hook per language; it does not say "off when the project has another formatter". The smallest fix is `/sdlc-init` writing `hooks.format_on_edit: false` when `pyproject.toml` configures black, yapf or autopep8 and not ruff, with the reason in the report.
- **`plan_sync` and generated files.** `plugin/hooks/plan_sync.py:1-20` denies a (c) commit that changes a source file not listed in plan.md unless plan.md changes too; `plan_sync.exempt` is `*.md` only (`template/sdlc.yaml:168-171`). Lockfiles (`package-lock.json`, `go.sum`, `poetry.lock`, `Cargo.lock`), snapshot files and generated clients change in most real commits and are never in the plan's "Files that change". The run can list them, and a departure is recorded as the article asks; but the first real build run will spend a fix round learning it. Shipping the common lockfile names in the template's `exempt` list is one line.
- **Existing folders collide silently.** `changes/`, `evals/`, `lessons/` and `REVIEW.md` are written create-only and reported `kept` (`sdlc-init.md:72-74`). A repository that already has an `evals/` or `changes/` directory (both are common names) keeps its own, with the framework's `evals/check.py` and `changes/README.md` missing, and nothing says so beyond the word `kept`. The report should say `kept (not the framework's file)` when the kept file's first line is not the template's.
- **The design run on a repository with history.** The read-only planning run of phase (b) and the adversarial reviewer read the codebase with `Read`, `Grep` and `Glob` only, under `max_turns: 200` (`template/sdlc.yaml:130`). On a 50,000-file repository with a `node_modules/` or `vendor/` committed, or large generated folders, the turn cap is spent on reading. Not measurable from the code; the trial's first design run will show whether `max_turns` needs a per-phase default or an ignore list for the researcher.
- **`python` on the runner.** Every workflow step calls `python` (`sdlc-build.yml:101,117,138,155,159,173`) on `ubuntu-latest`, where it resolves to the image's Python 3; a project that sets up its own Python with `actions/setup-python` in `commands.setup` cannot, since setup is one shell command. Fine for the trial; worth one line in `/sdlc-init` step 6 when the project needs a specific Python.

## Ranked: the five to settle before `/sdlc-init` runs on the trial project

1. **The CI session's allow list and network list are Python and Node only** (`plugin/ci/settings.ci.json:20-36,44-53`; `run_phase.ci_settings_file` adds no project rule). On any other stack the build run cannot run its own tests inside the session; three blind rounds and the change parks. Not covered by a row before the trial. Fix: append the project's command rules and an `sdlc.yaml` domain list in `ci_settings_file`.
2. **`detect()` picks Python whenever one `.py` file exists** (`plugin/init/detect.py:331-340,166-182`). A mixed repository gets pytest, ruff and compileall targets written into `sdlc.yaml`, both `CLAUDE.md` sections and `test_paths`, and the step 4 run passes on nothing. Not covered (R33 is the formatter). Fix: count signals per language and reach the "ask the owner" path when Python is not dominant.
3. **The maintain metric counts every non-`SDLC ` workflow** (`plugin/detect/source.py:71,134-156`; no `maintain.workflow` key in `template/sdlc.yaml:84-89`). A nightly or a deploy that fails by design files the trial's first incident. Not covered before the trial (R40 is rank 41). Fix: `maintain.workflow` passed to the `workflow` argument `counts()` already takes.
4. **The feedback loop on a real build: duration, services, environment** (`template/sdlc.yaml:136`; `run_phase.py:2310-2318,352-370`; `sdlc-build.yml:73,77`; `commands_env` at `run_phase.py:2406-2414`; no `services:`; no Bash timeout for the session). Partly covered by R25 (rank 11: a timeout parks instead of ending red). Fix: `/sdlc-init` times the targets and writes `command_timeout`, sets the session's Bash timeout to it, and `commands.env` names the secrets the targets need; a documented exclusion for service-bound tests on the trial.
5. **The Read deny knows `.env*` and `secrets/**` only, and `protected_paths` starts empty** (`settings.ci.json:5-8`; `template/sdlc.yaml:167`). A real project's key, certificate and credential files are readable by the session and commit-protected only by the secrets hook's patterns. Partly covered by R44 (rank 12: the model credential and `~/.ssh`, not the project's files) and R24 (rank 8: the risk list's globs). Fix: `/sdlc-init` proposes the secret-shaped paths it finds as `protected_paths` and Read deny rules, confirmed by the owner in the change-0000 PR.

Risk 6 (the phone owner) is the sixth: covered by R21 at rank 27, which should move before the trial as a documentation PR with no plugin version.

## Verdict

**Not yet; ready after those five**, under the assumptions above (deploy by hand on the trial, ranks 8 to 20 landing as ordered). Risks 1 to 3 are small code changes with a test each, risk 5 is an `/sdlc-init` proposal, and risk 4 is two keys and one documentation line; none reopens a decision. Without risk 1 the trial on a non-Python, non-Node project is a trial of the gate only, not of the loop; without risk 3 the first thing phase (f) says about the real project will be wrong. *[2026-10-25: re-checked against `main` at `7ac4131` (plugin 1.0.44) in `docs/reviews/2026-10-25-trial-readiness-recheck.md`: R61 (#350, 1.0.29; #355, 1.0.32) built a mechanism for each of the five; risk 2 is closed for the seven languages detection counts, risks 3 and 5 are closed (3 with an owner check), risks 1 and 4 partly closed, risk 6 closed for the trial by R21 part 1 (#357). What is still needed before `/sdlc-init` is listed there, in order.]*

## Checks

Run on the review's head in this repository, after `python -m pip install -e ".[dev]"`; the output is pasted below as the three commands printed it.

```
$ python -m compileall -q plugin tests tasks.py
(no output, exit code 0)

$ python -m pytest
...                                                                      [100%]
2163 passed in 490.91s (0:08:10)

$ python -m ruff check . && python -m ruff format --check .
All checks passed!
227 files already formatted
```
