# Progress — R67's second PR: a job GitHub cancels parks the change (2026-10-26, plugin 1.0.50)

This session ran on branch `claude/r67-2-park-on-cancel`, from `main` at `ae604a6` with R67's first PR (`claude/r67-1-recheck-minutes`, #400, plugin 1.0.49) merged in before its own merge, as lane H of wave 5. It builds decision 41's point 2 (the proposal's B1, `docs/proposals/fix-round-fits-its-job.md`) after point 3's live check, plugin **1.0.50**, and takes **note 62** (`python tasks.py next-free` after `git fetch origin`: note 62, patch 1.0.50, with 1.0.49 taken by #400). No numbered choice or decision is taken.

## Point 3: the live check
The owner ran the throwaway workflow this session designed (branch `r67-timeout-check`, head `e72a11d`, run 40414066074), and this session read its jobs and logs through the GitHub tools; the facts are `docs/notes/62.md`. A job cancelled at its `timeout-minutes` runs its later `always()`, `cancelled()` and `always() && steps.<id>.outcome == 'cancelled'` steps at once; GitHub stops the job about five minutes past the timeout (here 4 min 19 s after the step's cancel, which came 43 s late), killing a step still running; a job of its own on the cancelled result runs after it. B1 works, so decision 41 is not annotated (its point 3 asks for an annotation only if it did not).

## What was built
1. **The runner saves its state as the run goes** (`plugin/ci/run_phase.py`, `save_cancel_state`), in `$RUNNER_TEMP/sdlc-run.state.json` beside `--out` (outside the checkout the session writes), at three stages: `prepared` after the guard (the phase, the change, the gate's phase, the prepared branch, the fix branch, the park the change already had, the approved config); `session` right before the session (the head before it, `status.yaml` before it and the default branch's copy, and the snapshots the checks after the session compare with: the runner's own files, the stored results, the requests file, the change's remote refs); `after` once the runner's own checks after the session passed. A run starts by removing a stale state; a dry run and the review pass save none.
2. **`run_phase.py --phase <phase> --cancelled`** (`run_cancelled`) parks from that state, with no model and no session:
   - no state: nothing to park (the job was cancelled before the runner started the change's run);
   - a park this run already wrote: no second park;
   - at `session`, the checks after the session are replayed from the snapshots (`replay_session_checks`); what they find is restored and parks, keeping no work, as the runner does;
   - a fix round: `park_unfinished_round` with the cancel as its reason: the session's uncommitted work in one commit on the PR's head, not gated, the change parked, `sdlc:fixing` replaced; an automatic round with nothing to keep gets decision 29's own park (`release_unfinished_round`), which the stopped runner would have made on its way out;
   - design, build, test and deploy: the change folder committed with the reason and the park, check `cancelled`, as the runner's timeout park does (decision 11's note of 2026-10-23);
   - the reason tells GitHub's cancel at the job's `timeout-minutes` from a cancel by hand (the Actions API's `started_at` of the job on this runner against `SDLC_JOB_TIMEOUT_MINUTES`), or says it cannot tell and why; no re-run;
   - a stale `.git/index.lock` a stopped git process left is removed first.
3. **The failed-run record** of the cancelled run is written by the park step itself, marked parked, with no explanation (the explain session may not fit the minutes GitHub leaves); the step writes `--out` with no case, so the explain steps that follow write no red record over it. `plugin/pr/failed_runs.py` leaves a **cancelled** run whose record says parked out of the digest's "Failed runs" line (it is in the queue); a red run whose record says parked keeps its bare line, as its existing test pins.
4. **The five workflow templates** (`sdlc-design.yml`, `sdlc-build.yml`, `sdlc-test.yml`, `sdlc-deploy.yml`, `sdlc-fix.yml`): R18's three explain-chain conditions also run on `steps.setup.outcome == 'cancelled' || steps.phase.outcome == 'cancelled'`, and a step "Park the change after a cancelled run, before the explain steps (decision 41)" sits between the checkout's check and the explain session, `continue-on-error`, with the GitHub token and no model credential; design, test and deploy give it their `timeout-minutes` as `SDLC_JOB_TIMEOUT_MINUTES` (build and fix export it at the job). The deploy job's review step is not in the condition: a cancelled review pass stays red. The fix template's comment on the arithmetic says the step now parks such a round.
5. **Docs**: `docs/OPERATING_MODEL.md` §5's list of what parks; R18's proposal, two rows annotated (decision 41's proposal asked B1's build to annotate the "no step runs" row); R67's ROADMAP row.

Tests: `tests/test_cancelled_park.py` (13): a fix round cancelled at its timeout keeps its work and parks with the review request; a cancel by hand says so; a cancel the runner cannot place says both; a session that planted a runner file parks on it and keeps no work; no state; no second park; a build cancelled before its session; an automatic round with nothing to keep; the review pass refused; the state file; the parked record and the digest; the index lock; the job's elapsed minutes. Two existing layout tests were edited because the new step changes the explain chain's layout: `tests/test_explain.py`'s check of each workflow's chain (now also asserting the park step's place, command, condition and environment, and the `cancelled` conditions) and `tests/test_ci.py`'s step count of the merge-fired jobs (12 with the park step, its condition asserted). No test was deleted or skipped.

## The fresh-context review
PENDING

## Port list
This PR touches `plugin/ci/run_phase.py` and the fix workflow template (with the design, build, test and deploy templates): it goes on the port list until the 1.0.0 read.

## Proposed edits for the owner
None to a guardrail file. The workflow copies:

| Link | Row | What is there | What it must become |
|---|---|---|---|
| `.github/workflows/sdlc-design.yml`, `sdlc-build.yml`, `sdlc-test.yml`, `sdlc-deploy.yml`, `sdlc-fix.yml` | the explain chain | the 1.0.49 copies | the 1.0.50 templates: `python tasks.py workflow-copies` on this PR's branch, then commit and push |

## What the owner does
| When | Act |
|---|---|
| Before merging | Run `python tasks.py workflow-copies` on this PR's branch, commit and push (#400 is merged, as `0fb7b99`; the live check's two throwaway branches are deleted, as the central session reported). |
| Then | Merge when `Framework checks` is green on the final head. |
