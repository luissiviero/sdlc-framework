# Progress — ROADMAP R8 fixed as plugin 1.0.24: the second opinion at any pin, after phase (e) only, and carried on the fast lane (2026-10-23)

This session ran on branch `ccr-fc4dc248-6pmtbd`. Its first file (#331) recorded Part 0. The branch was then restarted from `main` at `5357fdc` (#331 merged after R65's part 5, #334). It is the Gemini session that `docs/handoffs/sessions/2026-10-22-ccr-6ed8a82e-cxmftx-end.md` asked for.

This PR is its Part 1: the fix of R8's two defects and one waste, which that file found, as plugin **1.0.24**.

The previous record (R65's part 5, from #334) is now `docs/progress/2026-10-23-r65-part-5-handoff.md`, unchanged (verified, `cmp` against `5357fdc:docs/PROGRESS.md`).

## Coordination with the other sessions
- **Numbers.** `python tasks.py next-free`, read at the start of Part 1 on `5357fdc`, gave choice 255 and patch 1.0.24, with nothing taken above `main`. This PR takes both.
- **Open PRs**, read when this session resumed: the owner's #328 and #173. R65's parts 1 to 5 are on `main` (#324, #325, #327, #329, #334); part 6 waits for R51.

## The owner's decisions (2026-10-23)
255. **On the fast lane, the (b) second opinion reaches the owner on the build PR at (e)** (the owner, "Carried at (e) (Recommended)", on this session's question). The design PR is closed as `sdlc:superseded` once the build PR exists, and the owner's first look is the build PR at (e) (`docs/OPERATING_MODEL.md` §4, "The fast lane"). So when phase (e) has run, the deploy workflow's `second-opinion` job carries the (b) opinion of the superseded design PR onto the build PR:
    - once per build PR, with the verdict, the concerns and a link to the original comment;
    - as a section of the (e) comment when (e) is on, else as a comment of its own;
    - with no model call;
    - only when the build head's `status.yaml` records `fast_lane.b.pr` and that PR carries `sdlc:superseded`;
    - when none was posted there, saying so instead of staying silent.

    The other options were a line in the build PR's body, a comment on the build PR at (b), or turning on (e) in the sample. They were not taken: the first two race the build run, and the last loses the (b) opinion still.
256. **The Gemini items go to the end of the queue** (the owner, "Send this Gemini roadmap items to the end of the queue", after Part 2's first live call was refused, below). R8 stays last in ROADMAP's Order column, and R62 is ranked after it, still not accepted. Two parts of this session wait behind every other ranked candidate:
    - Part 2, the first live call;
    - Part 3, Gemini in R28's roles. The proposal and its questions are carried in the session file, not put to the owner yet.

    This PR's fix stays as built: it keeps this repository's own job green at its pin whatever Gemini's order.

## What was built (plugin 1.0.24)
1. **Defect 1: the job at any pin.** In both copies of `sdlc-design.yml` and `sdlc-deploy.yml` and their templates, the second-opinion step runs only when `hashFiles('framework/plugin/external/cli.py')` is not empty. A framework pinned before 1.0.19, as this repository's 1.0.17, has no `plugin/external/`, so the step is skipped and the job stays green. With `external_review` off, `cli.py review` now writes no record file and posts nothing; the printed record is the only trace. Tests: `test_a_pin_without_plugin_external_skips_the_step_green` (the four copies) and `test_off_writes_and_posts_nothing`.
2. **The (e) waste.** `run_phase.py` writes `phase_ran=true|false` to `$GITHUB_OUTPUT` (`write_phase_ran`). It is `true` once the run passed the guard and the credential check, so the phase ran on this event (a session, or a park before one), and `false` otherwise. The deploy job exports the `Run phase (e)` step's value, and the `second-opinion` job runs only when it is not `false`. A framework pinned before 1.0.24 writes nothing, and the job runs as before. Tests: `test_the_run_says_whether_the_phase_ran_for_the_e_second_opinion` and `test_the_e_job_runs_only_when_phase_e_ran`.
3. **Defect 2, as choice 255 has it.** `cli.carry_design_opinion` and `review.carried` build the carry, and `publish` posts it. The quote drops the original's marker, so the carried text never reads as a verdict on the build head (`given_on_head`). Tests: `test_the_fast_lane_carries_the_b_opinion_onto_the_build_pr_once`, `test_with_e_on_the_carried_opinion_is_a_section_of_the_e_comment` and `test_the_carry_only_for_a_superseded_design_and_never_silent`.
4. **The trace (Part 1, point 4)**, below: one more silent path fixed, the others listed.

`docs/OPERATING_MODEL.md` (the `GEMINI_API_KEY` sentence), the template's `sdlc.yaml` comment and R8's row say the same, the row in a dated annotation.

## The trace: other ways the job can silently never run
Read on `main` at `5357fdc`, through R22's App (1.0.18), decisions 37 and 38 and the deploy workflow's dispatch-only inputs.

**Fixed in this PR:**
- **A `phases` value that is not a list** (`phases: b`) read as "off", so nothing was posted. It is now the visible reason "external_review.phases is not a list" (`test_a_phases_value_that_is_not_a_list_is_said_never_silent`).
- **The fast lane's race.** If the build run superseded the design PR before the (b) job looked it up, the (b) record found no open PR and went to the artifact only. The carry at (e) now says "was not found" on the build PR.
- **Two second-opinion jobs on one head.** A duplicate deploy dispatch is skipped by the guard, so `phase_ran=false` now keeps the second job from running. Before, both could pass `given_on_head` before either posted.

**Not silent, unchanged:**
- **Without the App** (R22), the design and deploy jobs end red before any work (`app_token.app_missing`), so the job is skipped behind a red job.
- **A missing key or model id** is posted as "not run".
- **Decision 38** (the subscription token wins) does not reach this job, which holds no Claude credential.
- **The deploy workflow's inputs:** since decision 37 it starts only on a dispatch. Its `change_id` and `head_ref` outputs are always set, which is why the old condition was always true, the (e) waste above.

**Listed, not fixed (not small, or not this PR's):**
- **A fix round runs no second opinion.** `sdlc-fix.yml` has no `second-opinion` job, so a design revised at (b), or a build revised at (e) before the next deploy run, gets none on its new head. Adding one is a design question for R8's tally, not a small fix.
- **GitHub runs the head's own workflow file on a `pull_request` event** (`docs/OPERATING_MODEL.md` §4.2). An intent PR branched before the project carried the job takes the fast lane without it. Merging the default branch into it once is the remedy, as for every workflow change.
- **The new behaviour needs both the copies and the pin at 1.0.24.**
  - Copies at 1.0.24 and pin 1.0.22, which is the sample once its copies move: the (e) job runs as before, and the carry is missing until the pin moves.
  - Copies at 1.0.19 and pin 1.0.24: the carry runs, but `phase_ran` is not read.

## The independent review
A fresh-context review of `50753e7` found no high-severity defect: the `hashFiles` guard, the folded job condition, the `phase_ran` output on every return path and the carry's main paths held. Its findings, and what this PR did with each:
1. **The `phases` check blocked a by-hand `--model` run**, against the module's "whatever `sdlc.yaml` says". Fixed: the check applies only without `--model`, and the test runs both.
2. **A failing carry would cost the (e) record its post**, after the paid call. Fixed: the carry is caught and recorded as a reason (`test_a_failed_carry_never_costs_the_e_record_its_post`).
3. **`fast_lane.b.pr` is optional** (`state/status.py`, `FAST_LANE_REQUIRED`). The build then supersedes the design PR it finds by its branch, which left the opinion uncarried and unsaid. Fixed: the carry finds the closed PR of `sdlc/<id>/b` the same way, and says so when there is none.
4. **Any bot's comment counted as the source, and the quote was posted raw.** Fixed: only the workflow token's `github-actions[bot]` counts, and every quoted line loses raw HTML, mentions and links once more (`test_the_carried_quote_is_inert_and_only_the_workflow_bot_s_counts`).
5. **A design PR the owner reopened was still carried.** Fixed: the carry needs the PR closed as well as labelled.
6. **A carry that only had a reason reached the log alone.** Fixed: it goes to the job summary and the JSON, never to a comment.
7. **An (e) record with no PR of its own now goes with the carry onto the build PR** (no model, say). Kept on purpose, since it makes a not-run visible, and said in `publish`'s docstring.
8. **Untested paths** (a re-run with (e) on, unread comments, the credential skip's `phase_ran`). Tests added, and one test's docstring corrected.
9. **A session can write to `$GITHUB_OUTPUT`** (hardening). Not taken here. `write_phase_ran` runs after the session, so its line comes last. A stray heredoc the session left open could swallow it, and the job would then run as before 1.0.24 (fails open, costs one call). Dropping `GITHUB_OUTPUT` from `session_env` touches every session and is left to the 1.0.0 read, recorded in the session file.

## The port list
This PR touches `plugin/ci/run_phase.py` (`write_phase_ran`, one line in `run_phase` and one in `_run_phase`). It goes on the port list until the 1.0.0 read.

## Proposed edits for the owner
None in this repository: the root pin stays at 1.0.17 (choice 249, point 2), and the step is now skipped green there.

The sample takes 1.0.24 in a sample PR after the tag `v1.0.24`. That PR carries the workflow copies and the owner's `sdlc.yaml` edits, given in full in the owner's format with the pin move and choice 252's row 5 (choice 253, point 8).

## Part 2's first try (2026-10-23)
- **The dry run passed:** `cli.py review --root . --id 0017 --phase b --ref main --dry-run` on the sample's `main` (`28fba16`) built 8 files, 31,214 characters (verified here, command output).
- **The real call was refused, at 0.2 s:** `HTTP 429` on the free tier, with `generate_content_free_tier_requests` and `..._input_token_count` both at `limit: 0` for `gemini-4-argon`. This is the owner's run in a Codespace, read from the owner's screenshot.
  - The key's Google project has no billing linked, and on the free tier Argon has no quota at all.
  - Listing a model (Part 0) is no proof it can be called.
  - The client recorded the refusal as "not run" and exited 0, as designed.
  - The request's shape is not verified: the refusal came before it was read.
- **The owner's Google AI Pro plan carries no Gemini API quota.** It does carry Google Cloud credit for the API, $10 a month by Google's plan pages (not verified from a bill). The remedy is billing on the key's project, with that credit and a budget alert. None of it is done yet; it waits with R8 (choice 256).
- Note 58 is not written: the request's shape it was to record is not verified.

## Left
- **Part 2, the first live call** and note 58, after billing on the sample key's project; behind every other ranked candidate (choice 256).
- **Part 3:** Gemini in R28's roles, the owner's questions first; the same.
- Every other open item is in the session file.

## What the owner does
| When | Act |
|---|---|
| Now | Merge this PR when `Framework checks` is green on its final head. |
| When R8's turn comes | Billing on the sample key's Google project (the AI Pro credit, a $10 budget alert); then the session that takes R8 runs Part 2 again. |

## Checks (this repository)
`python tasks.py verify` on the final head; its output is in the PR.
