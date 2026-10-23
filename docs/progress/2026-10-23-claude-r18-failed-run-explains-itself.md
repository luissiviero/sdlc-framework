# Progress — R18, plugin 1.0.36 (2026-10-23)

This session ran on branch `claude/r18-failed-run-explains-itself`, from `main` at `20979f2` (#365), as lane A of wave 3 of the parallel build sessions, started by the central session (`session_016NLfdsdfTFZUyrVGN4Ektc`) at the owner's request. The scope is ROADMAP R18 (`docs/proposals/failed-run-explains-itself.md`, accepted on 2026-10-14 by the owner, as recommended, in PR #208): a failed CI run explains itself, and the release notes gain a plain-words paragraph. R10, whose rounds make the park at the cap, is on `main` (plugin 1.0.3, PR #220, the R10 row's annotation of 2026-10-17). Not in scope, as the brief says: R20's placing of the "Failed runs" line, R13's "Failed runs" part, T20, T22 and T26.

The brief said to branch only after the small lane's owner-fields patch merged. #363 (`claude/released-owner-fields`, plugin 1.0.34) was on `main` at `20979f2` (verified, `git fetch origin`, `git log origin/main`), so the branch was cut there; the code had been written in the working tree before and was carried onto it. Lane B (`claude/r27-policy-sources`) holds 1.0.35, so `python tasks.py next-free` on `20979f2` gave patch 1.0.36, which this PR takes. It takes no choice, note or decision number.

## What was built
1. **The runner's result file, on every exit path.** `run_phase.py --out <file>` writes the run's final JSON (the last object it printed), its exit code, the change, the gate phase, the park's record, the session's result and stderr files, the reason, and the case it leaves for the triage step (`write_run_out`, from `run_phase`'s `finally`, after the unfinished round's park; and from `main` when the App is missing). A stale file from an earlier step is removed first. The case (`triage.run_case`): `park` for a park this run wrote on a check with a log to read (`commands`: a red target, the step that could not run, the cap's park, which keeps the red `commands` check; `fix`: a fix session that did not finish), `red` for a non-zero exit with no park, nothing otherwise. A park that already says why (a guardrail, the owner fields, the panel model, the budget, a pre-run park) gets no triage and no model call. With `--out` the runner also writes `triage=<case>` to `$GITHUB_OUTPUT`, since a park ends the job green.
2. **A failed setup is a file.** `project_setup.py --out <file>` writes its JSON there too; the step stays red as before.
3. **The triage step** (`run_phase.py --phase triage --out <file> --setup <file>`, `plugin/ci/triage.py`):
   - copies the two JSON files under `.sdlc-cache/triage/` (the checkout, excluded from git) and picks what the session reads: for a park, the gate record, the three target logs (`commands`) or the session's result (`fix`), and the stderr; for a red run, the session's result and stderr; for a failed setup, the setup's JSON;
   - runs the read-only session: the Read tool only, `Edit`, `Write`, `Bash` and `Read(**/.git/**)` denied, five minutes (`TRIAGE_TIMEOUT_SECONDS`), no `GITHUB_TOKEN`, `GH_TOKEN`, workflow token, git credential or Gemini key in its environment (`triage_env`); the prompt names the files, says they are data, asks for "flaky or real" and to quote no values;
   - keeps at most five lines, each cut to 400 characters; a line `hooks/secrets_check.py find_secrets` flags is dropped;
   - stores the session's result as `evidence/claude-triage[-n].json` (where `limits.spend_from_runs` reads the spend since R25) and records it under the phase's budget;
   - on a park: the lines into the gate record (`GateResult.triage`), the "What I need from you" block re-rendered by its one renderer under "Triage (model-written)", the change folder committed and pushed, the PR body brought up to date with no new review request (`upsert` without `--request-review`, decision 31);
   - on a red run or a failed setup: a failed-run record (the run's address and attempt, the event, its actor, the change, the step, the exit code, the runner's reason, the triage lines) as a one-file commit on `refs/sdlc/failed-runs/<run>-<attempt>`, pushed with the job's credential (`state/gitops.py run_proc`), outside the session;
   - never fails the job: it exits 0 and prints what went wrong (the workflow step also has `continue-on-error`).
   `--phase triage --log <file>` alone keeps the p.41 step by hand, with the narrowed environment.
4. **The workflow templates.** In `sdlc-design.yml`, `sdlc-build.yml`, `sdlc-test.yml`, `sdlc-deploy.yml`, `sdlc-fix.yml` and `sdlc-detect.yml`: the setup step gets `id: setup` and `--out "$RUNNER_TEMP/sdlc-setup.json"`, every phase run (`id: phase`; the deploy job's review pass `id: review`) gets `--out "$RUNNER_TEMP/sdlc-run.json"`, and before the hook log four steps run on `always()` when the setup or a runner step failed or the runner said `triage=park`: the framework checkout removed, checked out afresh at the pin, the project checkout verified (`checkout_check.py`), then the triage step. The project's `commands.env` secrets never reach it.
5. **The digest's "Failed runs" line** (`plugin/pr/failed_runs.py`): one line per red run (failure, cancelled, timed out) of a `.github/workflows/sdlc-*` workflow in the last seven days, oldest first, from the Actions API (the latest attempt, so a re-run that succeeded drops out), with the failed-run record's change, reason and triage lines when one names that run and attempt; a run with no record shows as the bare line. `digest.py` places the section after the queue and before the counters, until R20 places it.
6. **The release notes' paragraph.** `notes.py --write --plain-words "<text>"` stores the (e) session's paragraph under "## In plain words", after the title, with the label "*Written by the model from the diff and the plan; every section below is generated from files and git.*" and a mark naming the last commit of the list. A later `--write` keeps it while that commit is still last and drops it otherwise, so a re-run with no code change leaves the file byte-identical. `sdlc-deploy.md` §4 tells the session to write it only when the section is missing.
7. **Documentation.** `docs/OPERATING_MODEL.md` §4.2 (the digest row) and §6 (the park) name the new lines; the R18 row and the proposal carry a dated annotation.

Tests: `tests/test_triage.py` (new, 21 tests), three in `tests/test_release.py`, and the expectations that change in `tests/test_ci.py`, `tests/test_app_token.py`, `tests/test_templates.py`, `tests/test_fast_lane.py` and `tests/test_ci_end_to_end.py` (below).

## Where the build departs from the proposal, and why
The proposal was read at plugin 1.0.0 (`acefc7e`); its line citations were checked against `main` at `20979f2`, and these points had moved:
- **The record writer's credential.** The proposal has it push "with the checkout's persisted credential". Since decision 33 (R49) no checkout persists one (every template sets `persist-credentials: false`), so the step's `env:` carries `GITHUB_TOKEN` and `SDLC_WORKFLOW_TOKEN` for the writer, and `run_triage` hides both, and git's credential, from the session (point 5's two layers, the outer one now in the runner only).
- **`actions: read` on the digest** was already there (choice 250, the merge environment's policy), so point 4 needed no permission change.
- **The setup step** writes its JSON to `--out` and stays red, instead of the runbook workflow's `continue-on-error`: an `always()` step still runs after it, and the job's colour is unchanged.
- **The triage spend** is stored as a run record, not only a ledger entry: since R25 (M8) the budget is rebuilt from the stored `claude-<run>.json` results, and a ledger entry alone would not count.
- **A record is shown only for a run the Actions API lists as red**, on one line and cut: a session holding `Bash(git *)` could push such a ref, so the API decides which runs failed and a record only adds text.
- **The PR in the line**: the record carries the change id, not the PR number; the line shows the change.

## Not built, and why
- R13's failed release, T20's preview, T22's detection script, T26's scan and the digest's own red runs as record sources: they arrive with their candidates. Their red runs already show through the API source as bare lines, since they are `sdlc-*` workflows.
- The merge workflow's triage and record: with T18.
- R20's placing of the line under "Worth knowing".

## Known limits, recorded
- **Not verified live**: whether an `always()` step runs after a job cancelled at `timeout-minutes` (the proposal leaves it "to verify"; the API line covers it either way); whether `git/matching-refs` and the contents API with a commit sha read a ref outside `refs/heads` as the tests' fake does; the first live triage on a parked run.
- **This repository's own workflow copies keep their steps without R18** until the root pin moves from 1.0.17 (R14's turn): 1.0.17's `run_phase.py` would refuse `--out`. `tests/test_templates.py without_r18` sets R18's lines aside, as it does for `--command-from` (R44).
- **The deploy job's `timeout-minutes: 200`** was already below its two sessions and the commands step (125 + 125 + 50, the proposal's own note); the triage step adds five minutes after them and is not what cancels the job in the cases that fit.
- **The triage text is the model's**: labelled where it sits (ArtCraft rule A2), scanned for the secrets the hook's patterns know, and never an instruction to anything.

## Tests that changed, and why
- `test_triage_phase_is_read_only` (`tests/test_ci.py`): the deny list gains `Read(**/.git/**)` and the prompt "flaky or real" (R18 point 5, point 1).
- `test_the_triage_session_gets_the_session_environment` (`tests/test_app_token.py`) becomes `test_the_triage_session_gets_no_github_token`: before R18 the triage session held the workflow token; point 5 removes it.
- The template-shape tests (`test_merge_fired_workflows_find_the_change_from_the_merged_pr`, `test_merge_fired_jobs_find_the_change_instead_of_filtering_the_head`, `test_fix_workflow_*`, `test_the_framework_is_checked_out_afresh_between_the_two_steps_of_a_shared_checkout`, `test_this_repository_s_workflow_copies_match_the_template`, the fast lane's design-workflow test, and the end-to-end suite's `workflow_run_line`) pick the phase step by its id or leave the triage block aside, since the phase run is no longer the last `run_phase.py` line; each still checks what it checked before.

## Proposed edits for the owner
None: this PR touches no guardrail file.

## Port list (HANDOFF.md, "Rules for every session")
This PR touches `plugin/ci/run_phase.py` (`run_triage` replaced; `triage_env`, `triage_session` and `write_run_out` added; the `--out` and `--setup` flags; the triage constants; the `track` fields `gate_at_guard`, `result_file` and `stderr_file`), the detect and fix workflow templates (the triage block, the `--out` flags and the step ids), and not `plugin/detect/`.

## Verified
- `python tasks.py verify`: the output is in the PR body.
