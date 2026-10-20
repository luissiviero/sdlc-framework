# Test coverage of plugin/ before the real-project trial (2026-10-19)

## Summary

`plugin/` holds 84 Python files: 70 modules with code and 14 package `__init__.py` files that contain only a docstring. `plugin/commands/` and `plugin/agents/` hold no Python; they are Markdown, checked statically by `tests/test_commands_and_skills.py` and `tests/test_agents.py`. There is no separate `runner` package: the phase runner is `plugin/ci/run_phase.py`. Of the 70 modules, 68 have direct tests: a test file imports them, or runs them as a script or CLI. One is covered only through integration: `gate/policy.py`, which the gate's `owner_actions` tests and the five skill-check subprocesses reach, but no test calls directly. One is covered only by a live check: `ci/runner_setup.py`, whose single test runs the report-only `--check` mode; the install and AppArmor paths ran only on a GitHub runner (`docs/notes/23.md`, run 36592580162). No module has no test at all. Line coverage not measured: `python -m coverage run -m pytest -q` exited 1 with "No module named 'pytest'", because the container's base interpreter did not have the dev dependencies when the one attempt ran. So this report rests on import analysis alone, plus a count of which top-level functions each test file names. Coverage is broad, but eight modules are thin compared with what they control. Ranked by blast radius, the top five are: `gate/policy.py`, whose `is_automation` decides owner versus automation for the parking `owner_actions` check, and whose App-identity branch has no test; `ci/runner_setup.py`, where a failure stops every sandboxed phase job; `state/yamlish.py`, which parses every `sdlc.yaml`, so a misread makes `protected_paths` deny every edit; `hooks/format_on_edit.py`; and the policy-skill check scripts.

## Method

- **Modules**: every `*.py` under `plugin/` (`find plugin -name '*.py'`), on `main` at `7960377`.
- **Direct tests**: a test file that imports the module (`from gate import checks`, `from hooks import (...)`), runs it as a script (`[sys.executable, str(ROOT / "plugin" / "ci" / "checkout_check.py"), ...]`), or calls its CLI subcommands (`state/cli.py new-change`, `gate/cli.py record-spend`). The analysis parsed every test file with `ast` and searched it for each module's path. Then each thin case was read by hand.
- **Integration only**: no test calls the module itself. It runs only inside another module's test, or inside a scaffold or end-to-end test.
- **Live check only**: the only proof is a run on GitHub or on the sample, cited by its notes entry.
- **Thin**: a direct test exists, but it touches one or two paths of a module with many branches. The analysis counted the top-level functions a test file names; that count is a proxy, not a measure.
- Per-hook test counts in parentheses are counted from test names in `test_hooks.py`, so they are approximate.
- Where a classification was unclear, the weaker class was chosen, and the row says why.
- **Line %** is "n/m" (not measured) in every row: see the summary.

## Module table

Blast radius: **High** means the module can deny an edit, park a run, refuse a run or an auto-accept, approve or block production, or decide who counts as the owner. **Medium** means it can fail a job loudly, or file, dispatch or describe the wrong work. **Low** means it formats text, prompts or reports.

| Module | Classification | Tests | Line % | Blast radius |
|---|---|---|---|---|
| `ci/app_token.py` | Direct | `test_app_token`, `test_checkout_check`; static in `test_templates` | n/m | High: mints the App token every push and dispatch uses (decision 33) |
| `ci/auth.py` | Direct | `test_ci` (`choose_auth`, 4 tests) | n/m | Medium: picks the session's API key or OAuth token; a wrong pick fails the job at its start |
| `ci/auto_round.py` | Direct | `test_auto_round`; through `run_phase` in `test_fast_lane`, `test_fix_round_*` | n/m | High: runs and parks automated fix rounds |
| `ci/checkout_check.py` | Direct (CLI) | `test_checkout_check`, `test_app_token` | n/m | High: refuses the run when the framework checkout is not the pinned one; a false positive refuses every run (one found live, `docs/notes/48.md`) |
| `ci/comment_dispatch.py` | Direct | `test_comment_dispatch` (17) | n/m | Medium: decides whether an `@claude` comment dispatches a fix round |
| `ci/fix_requests.py` | Direct | `test_ci`, `test_fix_round_edges`, `test_owner_rounds`, `test_auto_round` | n/m | High: judges which review comments are the owner's fix requests |
| `ci/project_setup.py` | Direct | `test_ci`, `test_detect_cli` | n/m | Medium: runs the project's setup command; a failure fails the job |
| `ci/run_phase.py` | Direct | `test_ci` (170), `test_ci_end_to_end`, `test_fast_lane`, `test_fix_round_*`, `test_owner_rounds`, `test_auto_round`, `test_review_request`, `test_app_token`, `test_comment_dispatch` | n/m | High: the phase runner; starts the session, parks, commits, dispatches |
| `ci/runner_setup.py` | Live check only (weaker pick: the one test, `test_ci::test_runner_setup_check_reports_without_changing_anything`, runs `--check`, which installs nothing and returns an empty step list; installing bubblewrap and socat and loading the AppArmor profile ran only live, `docs/notes/23.md`, run 36592580162) | `test_ci` (1, report path only) | n/m | High: with `sandbox.failIfUnavailable: true`, a broken setup fails every phase job |
| `detect/bands.py` | Direct | `test_detect_stats`, `test_detect_routes`, `test_detect_cli` | n/m | Medium: the thresholds that decide when a detection files a change |
| `detect/cli.py` | Direct (CLI and import) | `test_detect_cli` (78), `test_review_request`; paths in `test_pr`, `test_scan`, `test_ci` | n/m | Medium: files incident changes, dispatches runbooks |
| `detect/dismissals.py` | Direct | `test_detect_routes`, `test_detect_cli`, `test_gate`, `test_pr`, `test_scan` | n/m | Medium: a dismissal silences a finding |
| `detect/finding.py` | Direct | `test_detect_routes`, `test_detect_cli`, `test_gate`, `test_pr` | n/m | Low: the finding record |
| `detect/routes.py` | Direct | `test_detect_routes` (67) | n/m | Medium: routes a finding to a runbook or a change |
| `detect/runbooks.py` | Direct | `test_detect_runbooks`, `test_detect_cli` | n/m | Medium: the runbook Go actions |
| `detect/source.py` | Direct | `test_detect_source`, `test_detect_cli` | n/m | Medium: reads CI runs as detection input |
| `detect/stats.py` | Direct | `test_detect_stats` | n/m | Low: statistics |
| `evals/case.py` | Direct | `test_evals` | n/m | Low: the incident case skeleton |
| `evals/run.py` | Direct | `test_evals` | n/m | Medium: a red eval fails the eval workflow |
| `evidence/collect.py` | Direct (CLI) | `test_evidence`, `test_gate`; paths in `test_ci_end_to_end`, `test_integration_fixture` | n/m | High: writes the build, test and lint logs the gate's evidence check reads |
| `gate/artifacts.py` | Direct | `test_gate`, `test_review`, `test_scan`, `test_pr`, `test_panel`, `test_evidence`, `test_agents` | n/m | High: the artifact paths and schemas every gate check reads |
| `gate/checks.py` | Direct | `test_gate` (141), `test_preflight`, `test_fast_lane`, `test_ci`, `test_agents`, `test_evidence` | n/m | High: the deterministic gate checks; each one can park |
| `gate/cli.py` | Direct (CLI and import) | `test_gate`, `test_auto_round`; paths in `test_ci_end_to_end`, `test_integration_fixture` | n/m | High: `check`, `start-run`, `record-spend`, `bump-iteration` |
| `gate/diff.py` | Direct | `test_gate`, `test_gitops_lookups`, `test_fast_lane`, `test_ci` | n/m | High: the diff every scope check reads |
| `gate/gate.py` | Direct | `test_gate`, `test_ci`, `test_ci_end_to_end`, `test_fast_lane`, `test_panel` | n/m | High: the verdict, continue or park |
| `gate/limits.py` | Direct | `test_gate`, `test_ci`, `test_init`, `test_templates` | n/m | High: the iteration cap, wall clock, budget and pause flag park runs |
| `gate/policy.py` | Integration only (weaker pick: `test_gate` imports it only for the constant `DEFAULT_AUTOMATION_IDENTITY`; `is_automation`, `automation_identity`, `added_lines` and `load_change` run only inside the `owner_actions` gate tests and the skill-check subprocesses) | `test_gate` (through `owner_actions`), `test_policy_skills` (subprocess) | n/m | High: `is_automation` decides whether a risk acceptance, iteration reset or test unlock came from the owner, and `owner_actions` parks on it |
| `gate/preflight.py` | Direct | `test_preflight` (17), `test_ci`, `test_policy_skills`, `test_pr`; path in `test_ci_end_to_end` | n/m | High: refuses auto-accept and the session start |
| `hooks/_common.py` | Direct | `test_hooks`, `test_scaffold` | n/m | High: config loading and glob matching for every hook |
| `hooks/format_on_edit.py` | Direct (thin: 5 tests; the "ruff not installed" and "ruff could not run" branches are not exercised) | `test_hooks` | n/m | Medium: blocks after an edit while ruff reports unfixable problems |
| `hooks/panel_blind.py` | Direct | `test_hooks` (about 12), `test_panel` | n/m | High: denies panel members the reads that would break blindness |
| `hooks/plan_sync.py` | Direct | `test_hooks`, `test_gate`, `test_pr` | n/m | High: denies work outside plan.md |
| `hooks/production_gate.py` | Direct | `test_hooks` (about 27) | n/m | High: blocks deploy commands without approval |
| `hooks/protected_paths.py` | Direct | `test_hooks` (about 17); path in `test_evals` | n/m | High: denies edits to guardrails |
| `hooks/secrets_check.py` | Direct | `test_hooks` (about 7), `test_preflight` | n/m | High: denies writes that carry a secret |
| `hooks/shell_guard.py` | Direct | `test_hooks` (about 58) | n/m | High: denies shell writes to protected targets |
| `hooks/test_file_lock.py` | Direct | `test_hooks` (about 20) | n/m | High: denies test edits in a fix task |
| `init/detect.py` | Direct | `test_init` | n/m | High for the trial: writes the build, test and lint commands into `sdlc.yaml` at `/sdlc-init` |
| `init/render.py` | Direct | `test_templates` | n/m | Low: template substitution |
| `init/sdlc_init.py` | Direct (CLI and import) | `test_init`, `test_templates`, `test_commands_and_skills`, `test_docs_lint`; setup step in nine more test files | n/m | High: scaffolds the trial project |
| `lessons/index.py` | Direct | `test_lessons`, `test_gate` | n/m | Low: the lessons index |
| `panel/cli.py` | Direct | `test_panel`; paths in `test_ci_end_to_end`, `test_hooks` | n/m | Medium: records the panel's calls the gate reads |
| `panel/ledger.py` | Direct | `test_panel` | n/m | High: the ledger decides continue |
| `panel/prompts.py` | Direct (thin: one test, `test_prompts_name_the_item_the_files_and_the_blindness`) | `test_panel` | n/m | Low: prompt text |
| `pr/cli.py` | Direct | `test_pr`, `test_auto_round`, `test_review_request` | n/m | Medium: upserts the PR description and check runs |
| `pr/counters.py` | Direct | `test_pr` | n/m | Low: digest counters |
| `pr/description.py` | Direct | `test_pr`, `test_auto_round`, `test_ci_end_to_end`, `test_fast_lane`, `test_panel` | n/m | Medium: the "what I need from you" block on the PR |
| `pr/digest.py` | Direct | `test_pr`, `test_auto_round` | n/m | Low: the daily digest text |
| `pr/github.py` | Direct | `test_pr` and ten more files | n/m | High: every GitHub call (labels, reviews, dispatches) |
| `pr/review_request.py` | Direct | `test_review_request` (22) | n/m | High: the only notification (decision 31) |
| `release/approval.py` | Direct | `test_release`, `test_app_token` | n/m | High: the production approval |
| `release/cli.py` | Direct | `test_release` (40) | n/m | High: the release record and the deploy step |
| `release/notes.py` | Direct | `test_release`, `test_pr` | n/m | Low: release note text |
| `review/cli.py` | Direct | `test_review` | n/m | Medium: the review pass's prompt and validation |
| `review/findings.py` | Direct | `test_review`, `test_scan`, `test_panel` | n/m | High: findings feed the gate's findings check |
| `scan/cli.py` | Direct | `test_scan` | n/m | Medium: the weekly scan entry point |
| `scan/prompt.py` | Direct | `test_scan` | n/m | Low: the scan prompt |
| `scan/route.py` | Direct | `test_scan` | n/m | Medium: files scan incidents |
| `scan/scanners.py` | Direct | `test_scan` | n/m | Medium: the deterministic scanners |
| `skills/coding-standards/check.py` | Direct (CLI; thin: one test) | `test_policy_skills` | n/m | Low: advisory |
| `skills/data-conventions/check.py` | Direct (CLI; thin: one test) | `test_policy_skills` | n/m | Low: advisory |
| `skills/definition-of-done/check.py` | Direct (CLI; thin: one test, two calls) | `test_policy_skills` | n/m | Medium: the gate's dry run; a false "clean" lets a session report done early, though the real gate still judges |
| `skills/security-baseline/check.py` | Direct (CLI; thin: one test asserts one of its nine dangerous-call patterns plus the secret finding) | `test_policy_skills` | n/m | Medium: the deterministic pattern scan the security skill runs; advisory, the secrets hook enforces |
| `skills/ux-conventions/check.py` | Direct (CLI; thin: one test) | `test_policy_skills` | n/m | Low: advisory |
| `state/cli.py` | Direct (CLI) | `test_state`, `test_fast_lane`; subcommands from `test_ci`, `test_ci_end_to_end`, `test_gate`, `test_integration_fixture` and more | n/m | High: `commit-phase`, `set-phase`, `lock-tests`, `accept-risk` |
| `state/conventions.py` | Direct | `test_state`, `test_review`, `test_pr` and more | n/m | High: change ids, branch names, paths |
| `state/gitops.py` | Direct | `test_gitops_lookups`, `test_state`, `test_app_token`, `test_fast_lane`, `test_detect_cli` | n/m | High: default branch, commit, push |
| `state/status.py` | Direct | `test_state` and 16 more files | n/m | High: the park state in `status.yaml` |
| `state/unpark.py` | Direct | `test_state`, `test_owner_rounds`, `test_auto_round`, `test_fix_round_*` | n/m | High: lifts a park |
| `state/yamlish.py` | Direct (thin for its reach: 10 tests in `test_yamlish`) | `test_yamlish`, `test_init`, `test_templates` and more | n/m | High: parses every `sdlc.yaml` and `status.yaml`; when `sdlc.yaml` cannot be read, `protected_paths` denies every edit |
| 14 package `__init__.py` files | No code (docstring only, no executable statement) | none needed | n/m | None |

Tally: 68 direct (8 of them thin for what they control), 1 integration only, 1 live check only, 0 untested; plus 14 package markers with no code.

## Top five by blast radius

1. **`gate/policy.py`** (integration only; High). A unit test should call `is_automation` with the default list, with case and whitespace variants, with an empty name or email, and with a custom App's `<app>[bot]@users.noreply.github.com` email that is not in the list. It should also call `automation_identity` with an empty list (falls back to the default) and `added_lines` on a real repository with a multi-hunk diff and an untracked file. It belongs beside `tests/test_gate.py`, next to the `owner_actions` tests that use `BOT_AUTHOR`. The App-email branch matters most: the trial pushes as the project's GitHub App (decision 33), and only `BOT_EMAIL_SUFFIX` matches that identity.
2. **`ci/runner_setup.py`** (live check only; High). A test should monkeypatch `shutil.which`, point `SYSCTL_PATH` and `APPARMOR_PROFILE_PATH` at temporary files, and fake `subprocess.run`. It should then assert that install mode installs only the missing packages, writes and loads the profile once when the sysctl reads 1, and does nothing on a second run or on a platform other than Linux. It belongs beside `test_runner_setup_check_reports_without_changing_anything` in `tests/test_ci.py`, in that file's runner-setup section.
3. **`state/yamlish.py`** (direct but thin; High). A parametrised cross-check against PyYAML should cover what an owner writes by hand in `sdlc.yaml`: comments after values, quoted strings that hold `#` or `:`, lists of mappings, block scalars. Each input should give PyYAML's value or a clear `ValueError`, never a different value. A second case should check that the error reaches `protected_paths` as a deny that names the file. It belongs beside `test_pyyaml_agrees_when_available` in `tests/test_yamlish.py`.
4. **`hooks/format_on_edit.py`** (direct but thin; Medium). Tests should monkeypatch `ruff_command` and the `run` callable to cover the three untested outcomes. With ruff missing, the hook allows and notes it on stderr; with ruff exit code 2, it allows with "ruff could not run"; when the project's own ruff config selects a rule the auto-fix cannot apply, it blocks and quotes the findings. They belong beside the five `test_format_on_edit_*` tests in `tests/test_hooks.py`.
5. **The policy-skill checks, led by `skills/security-baseline/check.py` and `skills/definition-of-done/check.py`** (direct but thin; Medium). One parametrised test should run the security check once per entry in `DANGEROUS` (today only `shell=True` and a secret are asserted), on a tracked `.env`, and on a settings file missing each `REQUIRED_DENY` rule. A second test should assert that the definition-of-done script's exit code matches `gate/cli.py check` on the same parked and unparked fixture. Both belong beside `test_security_baseline_check_finds_secrets_and_dangerous_calls` and `test_definition_of_done_check_is_the_gate_dry_run` in `tests/test_policy_skills.py`.

## Raw coverage report

Not measured. The one attempt, as instructed (`python -m pip install coverage` succeeded, coverage 7.16.2):

```
$ python -m coverage run -m pytest -q
No module named 'pytest'
(exit 1)
$ python -m coverage report
No data to report.
(exit 1)
```

Per the instructions, the run was not retried and no other tool was tried. A later measurement should also know this: many tests run plugin scripts as subprocesses (hooks end to end, `gate/cli.py`, `state/cli.py`, the skill checks, `run_phase.py` in `test_ci_end_to_end`). A plain `coverage run` does not follow subprocesses, so it would under-report those modules unless subprocess measurement is configured.
