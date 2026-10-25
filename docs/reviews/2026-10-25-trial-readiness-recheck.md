# The trial readiness re-check (2026-10-25)

The central session asked wave 5's lane C to re-check the trial readiness review of 2026-10-20 (`docs/reviews/2026-10-20-trial-readiness-review.md`) against the code on `main` today, so that the real-project trial can start as soon as R45 (the rename, being built now) and R67 (decision 41, built after R45; choice 274) land. Report only: nothing under `plugin/`, `template/` or `.github/` is changed, and no ROADMAP row is edited.

## Method

One session, one reader. Read first: `CLAUDE.md`, `HANDOFF.md`, the session files of 2026-10-25, the review of 2026-10-20 in full, `docs/proposals/trial-project-shape.md` (R61), `docs/handoffs/waves.md`, the ROADMAP rows R21, R24, R25, R33, R44, R45, R53, R61 and R67 with choices 238, 257, 273 and 274, and decisions 39 and 41. Then the code each risk names. Every file and line below is as read on `main` at `7ac4131` (#391), plugin **1.0.44**, on 2026-10-25. Where a claim needed a run, this session ran `detect()` on four synthetic repositories (the script and its output are in this session's record); nothing ran against a real project or on a runner, and a claim that would need one says "not verified" with the reason.

The names are the ones decision 39 and the names page of #387 (`docs/reviews/2026-10-25-names-added-since-decision-39.md`) give: the phases are intent, design, build, test, deploy and maintain (plugin 1.0.43), gate (e) is gate (deploy), the ready labels are `sdlc:<phase>-ready` and the reviewer's verdict is `continue | park` (plugin 1.0.44). Quotes from the review of 2026-10-20 keep its letters.

## What landed since 2026-10-20

| PR | Plugin version | What it changed for the trial |
|---|---|---|
| #343 | 1.0.26 | R51 and R25 parts 1-2: every outer bound (turn limit, budget stop, runner timeout) parks at design to deploy and in a fix round |
| #344 | 1.0.27 | R44, R59 and R3's I5: the sandbox closes shell writes to the guardrails and hides the model credentials, `~/.ssh` and `~/.aws/credentials` from sandboxed commands |
| #350 | 1.0.29 | R61 (all five parts) and R33: the trial project's shape, and the formatter per file type |
| #355 | 1.0.32 | R61's four points (choice 265): `.npmrc` and `appsettings.*.json` proposed only when their content reads as a secret |
| #357 | none | R21 part 1: every settings act of `/sdlc-init` step 6 says desktop-only, with its direct link |
| #370 | 1.0.37 | R64: `/sdlc-init` refreshes the create-only copies nobody edited, and says when a kept copy was edited |
| #382 | 1.0.40 | change 0004 (R14): the optional drive target and the proof items |
| #389, #390 | 1.0.43, 1.0.44 | R45's PRs 1 and 2: the phase names, the labels and the park verdict |
| #391 | none | R67's proposal and decision 41, accepted by the merge |

Each merge commit and its tag were read with `git log --first-parent origin/main` and `git tag --points-at` (#357 and #391 change no plugin file and carry no tag).

## Each risk, on `main` today

### Risk 1 (ranked 1): the CI session's allow lists

**What landed.** R61 part 1 (#350, 1.0.29). `ci_settings_file` now appends the project's own rules (`plugin/ci/run_phase.py:2138`, `:2143`): `project_command_rules` gives a `Bash(...)` rule for each of `commands.build`, `test`, `lint` and `setup` (`run_phase.py:2054-2071`, through `rule_for`, `plugin/init/sdlc_init.py:93-99`), and `project_domains` adds the hosts of `sdlc.yaml: sandbox.allowed_domains` (`run_phase.py:2074-2081`). `/sdlc-init` proposes the registries of every language it counts: crates.io, the Go proxy, Maven Central and Gradle, NuGet, RubyGems (`plugin/init/detect.py:593-607`). The base file is unchanged: Python and Node commands, PyPI and npm (`plugin/ci/settings.ci.json:26-42`, `:50-59`).

**State: partly closed.** What is left:
- **Only the targets, as written.** `rule_for` keeps a target's first three words and a wildcard: `go test ./...` gives `Bash(go test ./... *)`, `go vet ./... && golangci-lint run` gives `Bash(go vet ./... *)` (run in this session). On a Go, Rust, Java, .NET or Ruby project the session can run each target as written, but not one test, a `go build` or a `cargo build`, and a compound target's later commands match no rule. Whether Claude Code also refuses those later commands in the session is not verified (no live run); the commands step runs each target outside the session either way (`run_phase.py:2495-2510`). On a Python or Node project nothing is left: `Bash(python *)` and `Bash(npm *)` cover every such command.
- **Where a sandboxed command may write.** The sandbox lets a command write the working directory and a temp folder, not `$HOME` (`docs/notes/44.md`, its description). The runner points `XDG_CACHE_HOME` into the checkout (`run_phase.py:2320-2325`), which covers Go's build cache, but not Gradle's `~/.gradle`, Maven's `~/.m2`, Cargo's `~/.cargo` or Go's module cache when a test downloads a module. A Java or Rust test run inside the session may fail on a write outside the checkout even with its rule and its registry allowed. Not verified: R61's record lists "a CI session with `sandbox.allowed_domains` reaching crates.io" as not verified live (`docs/progress/2026-10-23-claude-r61-r33-trial-shape-formatter.md:97`), and no run has tried such a write.

### Risk 2 (ranked 2): detection says "Python" whenever one `.py` file exists

**What landed.** R61 part 2 (#350, 1.0.29). `detect()` counts the source files and manifests of seven languages (`detect.py:452-478`), and when the leader holds fewer than two files in three, or is not Python or Node, it returns every target unset with a note, so `/sdlc-init` asks the owner (`detect.py:405-451`, `:572-582`). Run in this session: a Go module with five `.go` files and one `scripts/release.py` comes back `go` with no target and the note; a TypeScript package with a `docs/conf.py` comes back `node` with `npm test`.

**State: closed for the seven languages; open outside them.** The languages counted are Python, Node, Rust, Go, Java/Kotlin, .NET and Ruby (`detect.py:459-467`). A repository in any other (PHP, C or C++ with a Makefile, Swift, Scala, Elixir) is counted as Python alone when it holds one `.py` file: run in this session, a `composer.json` with five `.php` files and one `scripts/release.py`, and a Makefile with five `.c` files and one `scripts/gen.py`, both come back `python` with `python -m unittest discover -v` as the test target. Step 0 still shows the detection and asks the owner to override it, as on 2026-10-20.

### Risk 3 (ranked 3): the maintain metric counts every workflow

**What landed.** R61 part 3 (#350, 1.0.29). The review's premise was smaller than written: `maintain.source: github-actions:<workflow name>` already restricted the count (`plugin/detect/source.py:99-114`; the trial shape proposal, problem 3). What was missing was the default, and `/sdlc-init` now proposes `github-actions:<name>` when exactly one of several project workflows runs the tests (`sdlc_init.py:666-677`), with the reason in the report.

**State: closed, with one owner check.** When two project workflows both run the tests, or none does, `/sdlc-init` falls back to `github-actions` (every own workflow) and says so in the report (`sdlc_init.py:675-677`); the owner then passes `--maintain-source` (`plugin/commands/sdlc-init.md:80-82`).

### Risk 4 (ranked 4): duration, services and environment

**What landed.** R61 part 4 (#350, 1.0.29), and R25 parts 1-2 (#343, 1.0.26).
- *4a, duration.* `/sdlc-init --time-commands` runs the three targets once, raises `gate.command_timeout` to three times the longest run (never below 900), and names the job minutes to raise in `sdlc-build.yml` and `sdlc-fix.yml` (`sdlc_init.py:994-1064`, `:498`; `sdlc-init.md:155-165`). The session's `BASH_DEFAULT_TIMEOUT_MS` and `BASH_MAX_TIMEOUT_MS` follow `command_timeout` unless the workflow sets them (`run_phase.py:2374-2379`, `:2383`). Every outer bound parks (#343).
- *4b, services.* Still the owner's edit of the workflows; the change-0000 intent and `/sdlc-init` say that tests bound to a service are deselected for now (`sdlc_init.py:1087-1088`; `sdlc-init.md:83-89`), as the review proposed.
- *4c, environment.* `commands.env` names repository secrets or variables (test credentials only, choice 265); the install writes each into the setup and phase steps of six workflows (`sdlc_init.py:130-174`; the marker in `template/.github/workflows/sdlc-{design,build,test,deploy,fix,detect}.yml`), and `commands_env` hides only the framework's own credentials, so they reach the targets (`run_phase.py:2495-2510`).

**State: partly closed.** What is left:
- **The test job is not in `--time-commands`' arithmetic.** It names `sdlc-build.yml` and `sdlc-fix.yml` only (`sdlc_init.py:498`). The test job holds 200 minutes (`template/.github/workflows/sdlc-test.yml:63`), and by decision 41's arithmetic a test run needs the 120-minute session, 5 of grace, the commands step and 10 for the judge, 185 with the template's 900 seconds (`docs/decisions/41.md:19`; `run_phase.py:301`, `:338`, `:2393-2406`; `plugin/gate/limits.py:60`). From this arithmetic, read and not run: a `command_timeout` above 1,200 seconds, which `--time-commands` writes when the longest target takes more than 400 seconds, needs more than the test job's 200 minutes, and GitHub cancels the job. Today such a cancel ends with no park; R67's point 2 makes it park (decision 41, point 2), so after R67 this costs the owner a parked change, not a silent one. The deploy job (355 minutes, two sessions; `sdlc-deploy.yml:78`) was not computed.
- **The two live checks R61 left**: the `BASH_*_TIMEOUT_MS` variables taking effect in the CLI version the workflows install, and a registry reached through `sandbox.allowed_domains` (`docs/progress/2026-10-23-claude-r61-r33-trial-shape-formatter.md:97`). Both "wait for the trial project".
- Raising `timeout-minutes` in the copies still makes them `outdated` at each upgrade, as the review said; nothing changed there.

### Risk 5 (ranked 5): the project's secret files

**What landed.** R61 part 5 (#350, 1.0.29) and choice 265 (#355, 1.0.32). `/sdlc-init` scans for the secret-shaped names the review listed (`detect.py:684` and the lines after it), gates `.npmrc` and `appsettings.*.json` on their content, and writes the hits into `protected_paths` and as `Read` deny rules for the owner to confirm in the change-0000 PR (`detect.py:713-729`; `sdlc_init.py:239`). In CI, `protected_read_rules` turns each secret-shaped `protected_paths` entry into a `Read` deny (`run_phase.py:2084-2108`, appended at `:2139`); any other entry stays readable so the tests can read it. R44 (#344, 1.0.27) hides the model credentials, `~/.ssh` and `~/.aws/credentials` from sandboxed commands (`settings.ci.json:76-85`).

**State: closed for what the review ranked.** The related finding the trial shape proposal carried beside part 5, the plugin security review's M10, is still open: the secrets hook runs on the file tools only (`plugin/hooks/hooks.json:5`, the `Edit|Write|MultiEdit|NotebookEdit` matcher), so a secret a shell command writes is not scanned, and its `PLACEHOLDER` pattern is unanchored (`plugin/hooks/secrets_check.py:58-61`). No ROADMAP row builds it (`docs/reviews/2026-10-20-findings-cross-reference.md:100` places it in R61's proposal as a related finding, not a part).

### Risk 6 (below the line): the owner on a phone

**What landed.** R21 part 1 (#357, no plugin version; choice 257): every settings act of step 6 says desktop-only with its direct link (`sdlc-init.md:189-190` and each act below it), the report names them so, and step 0 stops on a missing App with the desktop-only links (`sdlc-init.md:51-62`). Step 6 says why a build PR shows "Unable to merge" and that the phone's Merge under it works (`sdlc-init.md:325-329`). Choice 258 moved the owner's PC acts to a GitHub Codespace, a desktop browser.

**State: closed for the trial.** The rest of R21 (the park on a missing setting, one table in Python) keeps its place after the trial.

### The smaller findings

| Finding | State on `main` |
|---|---|
| Trigger noise on a busy repository | Open. The `pull_request` triggers of the abandon, design, build and release workflows have no `paths:` filter (`template/.github/workflows/sdlc-abandon.yml`, `sdlc-design.yml`, `sdlc-build.yml`, `sdlc-release.yml`, their `on:` blocks). Each run still skips, in about 20 seconds as the review said. |
| The formatter hook on a project not formatted by ruff | Closed by R33 (#350, 1.0.29): `hooks.formatters` per file type, with black, yapf or autopep8 proposed from `pyproject.toml` (ROADMAP R33's annotation of 2026-10-23). |
| `plan_sync` and lockfiles | Open: `plan_sync.exempt` is still `*.md` alone (`template/sdlc.yaml:223-224`). |
| Existing folders kept silently | Partly closed by R64 (#370, 1.0.37): a kept `changes/README.md`, `evals/README.md`, `evals/check.py` or `lessons/README.md` that differs from the template is reported "kept; outdated (edited)" (`sdlc_init.py:437-441`, `:486-490`); a missing one is written beside the project's own folder (`sdlc_init.py:855-880`). `bands.yaml` is still reported plain "kept". |
| The design run's turn cap on a large repository | Unchanged and not measurable from the code: `gate.max_turns: 200` (`template/sdlc.yaml:167`). The trial's first design run shows it. |
| `python` on the runner | Unchanged; fine for the trial, as the review said. |

### Two findings the review did not have

- **R67, the fix round GitHub cancels.** A fix round at gate (deploy) needs 290 of the job's 260 minutes when the default branch moved, and a job GitHub cancels ends with no park (decision 41, "Today"). The trial runs such rounds, which is why choice 274 places R67 before the trial. Decision 41 is accepted (#391); its build is not started.
- **The detection probe of risk 2 and the sandbox write of risk 1** are new in this re-check; both are above, under their risks.

## What is still needed before `/sdlc-init` runs on the trial project

In order. "Now" means it depends on neither R45's remaining PRs nor R67's build.

| # | Item | Kind | Who | Depends on | Now? |
|---|---|---|---|---|---|
| 1 | Choose the trial project (decision T1 below) | owner decision | owner | nothing | yes |
| 2 | Run `/sdlc-init --detect-only` on a local clone of it and read the language, the targets, the registries and the secret-shaped files it finds (`sdlc_init.py:753-756`: it returns before writing anything; the clone's `origin` must be on GitHub, `:750-751`) | live check | owner, or a session the owner points at the clone | 1 | yes |
| 3 | If the project is Java, Rust or Go: one throwaway run on a runner, in a scratch repository of the same stack, of a sandboxed session running the test target, to see whether it writes outside the checkout (risk 1) and reaches its registry (R61's open live check) | live check | a session; the owner creates the scratch repository | 1 | yes |
| 4 | If item 3 fails: a build item. None covers it. Proposed line: "The runner points the toolchain homes a sandboxed target writes (`GRADLE_USER_HOME`, `CARGO_HOME`, `GOMODCACHE`, Maven's local repository) into `.sdlc-cache`, as it points `XDG_CACHE_HOME` (`run_phase.py:2320-2325`)." | build | a session | 3 | yes |
| 5 | If item 2 shows a language outside the seven: the owner overrides the targets at step 0, as on 2026-10-20; no build needed for the trial. Proposed line, for after it: "`detect()` counts every source file it cannot place as an 'other' language, so a helper `.py` file never makes a PHP, C or Swift repository Python." | owner act | owner | 2 | yes |
| 6 | If item 2's targets take more than about 400 seconds: a build item. None covers it. Proposed line: "`/sdlc-init --time-commands` also names the test job's minutes (`sdlc-test.yml`) and the deploy job's when the raised `command_timeout` needs more than they hold." Without it the owner raises them by hand; after R67 an overrun parks. | build, or owner act | a session, or owner | 2 | yes |
| 7 | R67's live check: GitHub runs an `always()` step after it cancels a job at `timeout-minutes` (decision 41, point 3), recorded as a note | live check | a session | nothing | yes |
| 8 | R45's PRs 3, 4 and 5 (the config names, then PRs 4 and 5 as decision 39's point 4 orders them; PR 3 is open on `claude/r45-3-config-values`, taking 1.0.45) | build | lane A; owner merges | R45 | no |
| 9 | This repository and the sample migrated and pinned at PR 4's version or later, each with its `status.yaml` migration (choice 273); the sample's move from 1.0.22 crosses R22, the App and its two secrets on the sample (carried from `docs/handoffs/sessions/2026-10-25-ccr-ca9f0149-a29zgl-wave-5.md`, not re-verified) | owner act (guardrail edits) | owner, with the rows a session gives | 8 | no |
| 10 | R45's PR 6, which removes the readers of live state (choice 273: after item 9, before the trial) | build | lane A; owner merges | 9 | no |
| 11 | R67's build: point 1 in a plugin version of its own, then point 2 with the workflow copies (decision 41, point 4) | build | a session; owner merges and commits the copies | 7, 10 | no |
| 12 | On the trial repository, before `/sdlc-init`: the project's GitHub App with `SDLC_APP_ID` and `SDLC_APP_PRIVATE_KEY` (step 0 stops without it, `sdlc-init.md:51-62`), and the cloud environment's four plugin lines if the owner runs `/sdlc-init` from a cloud session (`sdlc-init.md:195-203`) | owner act, desktop-only | owner | 1 | yes (the App); the plugin lines name no version |
| 13 | `/sdlc-init` on the trial project at the version of item 11 or later, with the shape choices of T3 below; `--time-commands` at step 4 | owner act | owner, in a session | 8 to 12 | no |
| 14 | After the change-0000 merge, step 6: the Actions workflow permission, the Claude secret, the merge App and its `sdlc-merge` environment (or none, T5), and both rulesets. Ruleset 2's name loses its decision numbers in R45's PR 5 (decision 39, row N10), so it is created after PR 5 merges, or renamed then | owner act, desktop-only | owner | 13 | no |

Items 8 to 11 are the ones R45 and R67 hold. Items 1 to 7 and the App of item 12 can start today.

## The owner's decisions the trial still needs

| # | Decision | Recommendation | Why |
|---|---|---|---|
| T1 | Which project | A repository the owner works in, with one CI workflow that runs its tests on `pull_request`, in Python or Node, or else in Go, Rust, Java, .NET or Ruby with each target one plain command | The loop is proven on Python and Node; on the five other counted languages the session runs only the targets as written, and Java and Rust have the unverified write of risk 1. A language outside the seven needs the step 0 override. One test workflow makes the maintain metric's default right (risk 3). |
| T2 | Public or private | Public, if the code allows it | A private repository needs a paid plan for the `sdlc-merge` environment (`sdlc-init.md`, the merge App's step 2) and counts Actions minutes against the plan, which the digest watches at 80% (R25, #343). |
| T3 | The shape choices at `/sdlc-init` (trial-project-shape.md) | Accept the detected targets only when step 0's language is right; `commands.env` with test credentials only (choice 265); `maintain.source` naming the test workflow; keep the proposed registries and secret-shaped paths; deselect service-bound tests for the trial; `deploy.action: none` | Each is a guardrail line merged once in the change-0000 PR. The review assumed `deploy.action` none or a by-hand release (its assumptions), and `deploy.command` runs on the runner with the repository's secrets and no `environment:` (R39 is after the trial). |
| T4 | The credential and the spend | The subscription token, with `gate.max_budget_usd: 150` per change as the template has it (`template/sdlc.yaml:171`) | R25's weekly ceiling is part 3, after the trial (choice 260); each run records the credential that paid and the PR shows the spend (#343), so the trial measures what R28 is judged against (choice 257, #13). |
| T5 | Merge App or no merge App | The merge App, if T2 is public | Your approving review is then your only act at gate (deploy) (decision 36); without it you merge after approving ("no merge App", decision 39 row N7). |
| T6 | Whether to register the three proposed lines of items 4, 5 and 6 as ROADMAP candidates | Register item 6's now if item 2 shows a target over 400 seconds, item 4's only if item 3 fails; leave item 5's for after the trial | Each is needed only on a stack or a build time the trial may not have. This re-check adds no row: `python tasks.py next-free` names R68 on `7ac4131` and its branches. |

## Verdict

**Ready once R45 and R67 land, for a Python or Node project; for another counted language, after the live check of item 3.** All five ranked risks have code on `main`: risks 2 to 6 are closed for the trial's likely shape, and risk 1 and risk 4 are partly closed, each with a residual that only shows on a stack or a build time the sample never had. Nothing left reopens a decision. The work that cannot start now is R45's PRs 3 to 6 with the two pin moves, and R67's build; the project choice, the detection on the real clone, the live checks and the App can all start today.

*Choices 238 and 274: R45 then R67 are the last changes before the trial; this re-check names no new change before it unless item 3 or item 2 says so.*

## Checks

`python tasks.py verify` on this PR's head; its output is in the PR body.
