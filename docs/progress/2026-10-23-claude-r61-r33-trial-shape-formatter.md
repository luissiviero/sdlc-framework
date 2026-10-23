# Progress — R61 with R33, plugin 1.0.29 (2026-10-23)

This session ran on branch `claude/r61-r33-trial-shape-formatter`, from `main` at `d72de6a` (#344), as lane A of wave 2 of the parallel build sessions the owner started on 2026-10-23 ("start wave 2"). Lane B builds R29 part 1 with R54 on `claude/r29-r54-quick-intent`. R61 comes before them in ROADMAP's Order column, so this PR merges first and lane B merges `main` in after it. The scope is ROADMAP R61 (`docs/proposals/trial-project-shape.md`, parts 1 to 5, accepted as one candidate by choice 240) and R33 (`docs/proposals/formatter-per-language.md`, accepted on 2026-10-16). R33 takes the owner's revised answer in `docs/reviews/2026-10-20-lifecycle-axis-ports/options.md`, row "Formatter on edit": one behaviour, on, the switch gone, and a `*.py` mapping for a project's own formatter. R61 takes the row "Network allow list": `/sdlc-init` sets `sandbox.allowed_domains` from the detected registry. This PR changes `plugin/` and `template/`, so it bumps the patch. `python tasks.py next-free` on `d72de6a` gave 1.0.29, since lane B's branch already holds 1.0.28, so this PR takes 1.0.29. It takes no choice, note or decision number.

## What was built
**R61.**
1. **Part 1, the CI session's allow lists follow the project.** `run_phase.ci_settings_file` appends to the copy of `settings.ci.json`:
   - the `Bash(...)` rule of each of `commands.build`, `test`, `lint` and `setup` (`project_command_rules`, the same `sdlc_init.rule_for` the project's own settings use; `/sdlc-init`'s `echo no ... target` placeholders get none);
   - the hosts of `sdlc.yaml: sandbox.allowed_domains` (`project_domains`; an entry that is not a host name is left out).

   `/sdlc-init` writes `sandbox.allowed_domains` from the registries of the languages found (`detect.REGISTRY_DOMAINS`: crates.io, the Go proxy, Maven Central and Gradle, NuGet, RubyGems; PyPI and npm are already in the base list), and adds the same hosts to the project's `.claude/settings.json`.
2. **Part 2, detection asks on a mixed repository.** `detect.language_signals` counts the source files of Python, Node, Rust, Go, Java/Kotlin, .NET and Ruby, and notes each one's manifests in any folder. The files are `git ls-files -co --exclude-standard` in a repository, otherwise a walk; either way it skips the tool folders and any folder holding a `pyvenv.cfg` (`detect.project_files`). A language takes part with a manifest; Python also takes part with `.py` files alone. A Node leader with no `package.json` at the root (a frontend in `web/`) gets no target either. The leader's targets are detected only when it is Python or Node and holds two files in three of the files that take part (`DOMINANT_SHARE`). Any other leader, or a leader below that share, comes back with every target `None` and a note that names the signals, so `/sdlc-init`'s "ask the owner for the command" path is reached. The report carries `detection.signals`. Results:
   - a Node project with one helper `.py` file is Node;
   - a Go project with one `.py` file is `go`, with no target;
   - a Django project's static JavaScript, with no `package.json`, does not take part, so the project stays Python.
3. **Part 3, the maintain metric names its workflow.** With no `--maintain-source`, `/sdlc-init` proposes `github-actions:<name>` when the project has several workflows of its own and exactly one holds the test command, or else exactly one names a test runner (`sdlc_init.testing_workflow`). Otherwise it writes `github-actions` as before. The report says why. A name that holds `:` or `#` is quoted in `sdlc.yaml` and `bands.yaml`.
4. **Part 4, the targets' duration and environment.**
   - `/sdlc-init --time-commands` runs the installed `sdlc.yaml`'s three targets once through the gate's `run_command` and times them. When three times the longest run is above `gate.command_timeout` (900 at least), it raises the value. When the build caps then need more job minutes than the template's 260, it names the two numbers to raise in `sdlc-build.yml` and `sdlc-fix.yml`. Step 4 of `sdlc-init.md` calls it.
   - `run_phase.session_env` sets `BASH_DEFAULT_TIMEOUT_MS` and `BASH_MAX_TIMEOUT_MS` from `command_timeout`; a value the workflow sets is kept.
   - `--time-commands` flags a target that hit the timeout, and reads the job minutes from the project's installed `sdlc-build.yml` when there is one.
   - `--env NAME` (repeatable) writes `commands.env` and turns each `# sdlc:commands.env` marker of the six phase workflows into `NAME: ${{ secrets.NAME || vars.NAME }}`. The markers sit in the setup step and the phase step, and the install drops them when no name is given, so this repository's installed copies are unchanged. The model credentials, the GitHub tokens, `GEMINI_API_KEY` and every `SDLC_*`, `GITHUB_*` and `RUNNER_*` name are refused. A re-run keeps the names `sdlc.yaml` lists. A kept workflow copy reported `outdated` says it may lack the lines. A new `--env` name that the kept `sdlc.yaml` lacks is named in the report.
   - The change-0000 intent says that a test bound to a service is deselected until the owner adds the service.
5. **Part 5, the project's secret files.** `/sdlc-init` proposes each pattern of the proposal's list that matches a file of the project (`detect.secret_paths`) as a `protected_paths` entry and as `Read(<p>)` and `Read(**/<p>)` deny rules in `.claude/settings.json`. `ci_settings_file` adds a `Read(//<root>/...)` deny for each secret-shaped `protected_paths` entry (`detect.is_secret_pattern`), and one more in any folder for a bare name (`protected_read_rules`). Any other entry (`migrations/`, generated code) stays readable to the CI session: the sandbox hides a denied path from every command, the tests included (`docs/notes/24.md`), and `denyWrite` keeps the entry unwritable. On a re-run, the settings take the `protected_paths` and `allowed_domains` of the `sdlc.yaml` just written, and the report names a secret-shaped file the kept list leaves out.

**R33.**
6. **The hook is one behaviour, always on.** `format_on_edit.py` no longer reads `hooks.format_on_edit`, and the template no longer writes it; a project that still carries it keeps the line, unread.
7. **Per file type, the project's own commands.** `sdlc.yaml: hooks.formatters` is a list of `{glob, fix, check}` entries, where `glob` is a gitignore glob or a list of them. The first entry that matches the file's project-relative path wins. Its `fix` commands run in order on the file, then its `check` commands, with `{file}` quoted for the platform shell (double quotes for cmd.exe; a path holding `"`, `%` or `!` is skipped there).
   - A `check` exit 1 is fed back as today's PostToolUse block. Any other exit, a missing tool or a timeout is a note on stderr: the hook fails open.
   - A fixer's exit 1 is left to the check.
   - **In a CI session the project's commands are not run.** A hook runs outside the Bash tool's sandbox, and a project command runs code the session can write (an eslint or prettier configuration); through it a session could reach the network or rewrite the pinned framework's hooks. The runner's lint target judges the change after the session instead. A CI session is `SDLC_GATE_COMMANDS`, which `session_env` sets on every run, or `GITHUB_ACTIONS`. Ruff, the default, runs as `python -I -m ruff`, so a `ruff.py` the session wrote cannot stand in for it.
   - A check's exit 1 whose output says the tool is missing (`npx canceled due to missing packages`, `command not found`) is a note, not a finding.
   - The commands run through the gate's `run_command`, which kills the process tree on a timeout. Their environment has no model credential, no GitHub token and no git credential header. Each command gets 25 seconds and all of them 50, under the handler's 60.
   - The hook's log line carries `commands`, with each command and its exit code (`Decision.log`, a new field in `_common`); ruff's steps are logged too.
   - An explicit `*.py` entry replaces the ruff default. A file type with no entry is left alone.
8. **Proposed at setup.** `detect.formatters` reads each language on its own:
   - `[tool.black]`, `[tool.yapf]` or `[tool.autopep8]` in `pyproject.toml` gives a `*.py`/`*.pyi` entry for that formatter;
   - prettier or eslint in `dependencies` or `devDependencies` (`detect.node_dependencies`, choice 246's helper, which R14 can reuse) gives `npx --no prettier --write`, then `npx --no eslint --fix`, with `npx --no eslint` as the check;
   - a `Cargo.toml` gives `rustfmt --edition <its edition>`.

   `/sdlc-init` writes them under `hooks.formatters`, and the report's `proposed` block lists them.
9. **Windows.** The proposal asked to check the `.cmd` shims before building. `test_a_cmd_shim_gets_a_path_with_a_space_and_an_ampersand_whole` starts a fake `.cmd` shim that passes `%*` on, as npm's do, with `src\a & b.ts`. It runs on the Framework checks Windows job; its result is under "Verified".
10. **Upgrade.** A re-run on a 1.0.27 project adds `commands.env`, `hooks.formatters` and the `sandbox` block by a text edit, keeping the owner's comments (`test_an_upgrade_adds_the_new_keys_and_keeps_the_comments`).

Tests: `tests/test_trial_shape.py` (new), with the expectations that change in `tests/test_hooks.py`, `tests/test_init.py` and `tests/test_templates.py`.

## Not built, and why
- **Full Rust support** (targets, the test-file lock for tests inside source files) and **the quarantine runbook for Node and Rust**: open in R33's proposal, for later changes.
- **R61's related findings** (M10's diff-level secret scan, trigger noise, lockfiles against `plan_sync`, and the others the proposal lists): left for the trial to show, as the proposal says.

## Known limits, recorded
- **`commands.env` reaches code the session wrote.** The setup command and the targets run outside the sandbox, so a named secret is readable by any test the session writes. `template/sdlc.yaml` and `sdlc-init.md` say to name test credentials only; see "What I need from you".
- **A local session still runs the project's formatter commands outside its sandbox**, on code it can write. It is the owner's own machine, and its sandbox already lets the session write the project; see "What I need from you". The proposed `python -m black`, `yapf` and `autopep8` commands are not isolated (`-I` would hide a `--user` install), so a session-written `black.py` at the root would run there.
- **A project that set `hooks.format_on_edit: false`** gets ruff on its next edit after it moves its pin to 1.0.29, until `/sdlc-init` writes its `*.py` mapping; a re-run's report says so. No project is known to carry `false`: the trial has not started and the sample formats with ruff (not re-verified on the sample).
- **The detection's share is a judgment**: two files in three, counted by file, not by size. A project the rule misjudges gets no target and a note, never wrong targets, and the owner gives the commands.
- **The workflow lines are written at install only.** The workflows are create-only, so a name added later needs the copies replaced; `/sdlc-init` reports them `outdated`.

## Proposed edits for the owner
| Link | Row | What is there now | What it must become |
|---|---|---|---|
| [sdlc.yaml](../../sdlc.yaml) | `hooks:` block (line 97-98) | `format_on_edit: true` | Nothing now: the root pin is 1.0.17, which still reads it. At the move from pin 1.0.17 (R14's turn), replace it with `formatters: []` |

## Port list (HANDOFF.md, "Rules for every session")
This PR touches `plugin/ci/run_phase.py` (`ci_settings_file`, `session_env` and three helpers beside them). It does not touch `plugin/detect/` or the detect, runbook and fix workflow logic beyond the `# sdlc:commands.env` marker lines in `sdlc-detect.yml` and `sdlc-fix.yml`.

## The fresh-context review
A general-purpose agent in a fresh context reviewed the diff against `origin/main` (the owner's rule of 2026-10-16). It reproduced each finding before reporting it, and edited nothing. All eleven are fixed, each with a test in `tests/test_trial_shape.py`:
1. **Blocking: every `protected_paths` entry became a CI `Read` deny**, and the sandbox hides a denied path from the tests (a protected `migrations/` folder would be empty to `pytest`). Now only secret-shaped entries become a `Read` deny.
2. **The hook ran session-writable code outside the sandbox in CI.** The project's commands are skipped in a CI session, and ruff runs isolated.
3. **`npx --no` exits 1 for a missing package**, which blocked every edit before `npm ci`. That output is now a note.
4. **Untracked trees were counted, and only root-level manifests.** The file list is now `git ls-files`, venvs are pruned by `pyvenv.cfg`, and a manifest counts in any folder.
5. **`commands.env` was lost on a re-run.** The existing names are kept, and the report names the gaps.
6. **An upgrade added `Read` denies without `protected_paths`.** The settings now follow the written `sdlc.yaml`.
7. **`{file}` comes already quoted**, and the template now says so.
8. **A re-run re-added domains the owner removed.** Same fix as 6.
9. **`--time-commands` read the template's job minutes and gave no timeout flag.** Both are fixed.
10. **Three tree walks per install** are now one.
11. **A retired `false` switch went silent.** The report now says it is no longer read.

The review found no problem in the marker replacement (valid YAML with one and two names), the flow lists (yamlish and PyYAML agree), the reserved names, the guardrail park that stops a session-edited `sdlc.yaml` from widening the CI settings (checked here for the phase run: `guardrail_changes` parks before `compose` builds the settings; the two other `compose` callers were not traced), the shell quoting, or the rules' anchoring.

## Verified
- `python tasks.py verify` on this branch after the review's fixes, with `main` merged in at `f0e50f7` (#345, #347): build, lint, docs lint, version check, tests (2512 passed, 1 skipped: the Windows shim test) and `claude plugin validate` all ok. The output is in the PR body.
- The `.cmd` shim test runs only on the Framework checks Windows job; its result is read from that job, not here.
- Not verified live: a CI session with `sandbox.allowed_domains` reaching crates.io, and the `BASH_*_TIMEOUT_MS` variables taking effect in Claude Code 2.1.304. Both wait for the trial project.

## What I need from you
1. **`commands.env` reaches code the session wrote.** The setup command, the session and the targets read the names, and the targets run outside the sandbox. Recommended: accept as built. The template says to name test credentials only, never production ones.
2. **A local session runs the project's formatter commands outside its sandbox** (CI does not). Recommended: accept for local sessions, since the session can already write the project there. The other way is to skip them everywhere, which leaves Node and Rust projects with no format on edit.
3. **Two patterns of the proposal's list are often read by tests:** `appsettings.*.json` (.NET) and `.npmrc`. When confirmed in `protected_paths`, the CI session cannot read them. Recommended: keep them in the list. The owner drops an entry in the change-0000 PR when the tests read it, and the template comment says that a denied path is hidden from the tests.
4. **The number.** This PR is 1.0.29; lane B's branch holds 1.0.28. Lane B merges after this PR and renumbers above 1.0.29, so 1.0.28 is never released. No action unless the owner prefers otherwise.
