---
type: Proposal
title: A fix round at gate (deploy) that fits its job, and a park when GitHub cancels the job
description: R51's merge and re-check before a fix round at gate (deploy) take their measured minutes off that round's session, as the drive's minutes already are, so the round fits the fix job's 260 minutes with no workflow edit; and every phase workflow parks the change when its runner step ends cancelled, so a job GitHub stops at timeout-minutes ends with a label and "what I need from you" instead of nothing. timeout-minutes stays as it is.
status: proposed
roadmap: R67
sources:
  - id: row
    resource: docs/ROADMAP.md
    title: "R67, with its annotations of 2026-10-24 (choice 272) and 2026-10-25 (choice 274)"
  - id: concern
    resource: changes/0004-drive-target-and-proof-items/spec.md
    title: "Flagged concerns, item 2 (panel decision 2: named, not fixed), and R4's paragraph that names the shortfall a ROADMAP candidate"
  - id: fix-response
    resource: changes/0004-drive-target-and-proof-items/evidence/fix-response.md
    title: "Item 6: the row as change 0004's design drafted it, for the owner's documentation PR"
  - id: decision-32
    resource: docs/decisions/32.md
    title: "Decision 32: the build run's raised caps (as decision 37 left them: \"the raised build-run limits stay\")"
  - id: decision-29
    resource: docs/decisions/29.md
    title: "Decision 29: a red target starts the next fix round by itself; the judge at the iteration cap"
  - id: decision-20
    resource: docs/decisions/20.md
    title: "Decision 20, as amended by 31: the only notification is the review request on a PR that waits"
  - id: r18
    resource: docs/proposals/failed-run-explains-itself.md
    title: "R18: the triage steps on always(); its table (\"a job cancelled at timeout-minutes: no step runs\") and its open question whether an always() step runs after such a cancellation"
  - id: code
    resource: template/.github/workflows/sdlc-fix.yml
    title: "The fix job's timeout-minutes and SDLC_JOB_TIMEOUT_MINUTES, its comment on the worst case, and the triage steps' conditions; plugin/ci/run_phase.py (run_caps, run_timeout_seconds, commands_timeout_seconds, build_caps_minutes_needed, R51's update_before_offer call, the judge, check 12's re-check); plugin/ci/base_update.py; plugin/gate/limits.py (run_caps, the drive's floor, the gate's wall-clock check); read at main 0ce7f6b, plugin 1.0.43"
---

# A fix round at gate (deploy) that fits its job, and a park when GitHub cancels the job
**Names since R45** (decision 39; only the renames built after this file was written on `main` 0ce7f6b, in plugin 1.0.44 to 1.0.47; added on 2026-10-26, the text below keeps the old names, choice 126): `triage` -> `explain` (R18's step and its explanation); `plugin/ci/triage.py` -> `plugin/ci/explain.py`; `steps.phase.outputs.triage` -> `steps.phase.outputs.explain`. \
Phase names follow R45 as built in plugin 1.0.43 (decision 39): "gate (deploy)" is the gate the row calls (e). Every file and line below was read on `main` at `0ce7f6b` (#389).

## The problem

A fix round on a change at gate (deploy) can need more minutes than its job has. When it does, GitHub cancels the job, and nothing parks the change: no `sdlc:needs-human`, no "what I need from you", no review request. The owner learns of it only from the digest's "Failed runs" line, which lists a cancelled run with no text (`plugin/pr/failed_runs.py:7-11`, `:39`). An automatic round (decision 29) also leaves `sdlc:fixing` on the PR, so the change looks busy while nothing runs.

Change 0004's design named this and did not fix it (its spec, "Flagged concerns" item 2, panel decision 2); the owner accepted that for change 0004 and asked for the row (choice 272), placed after R45 and before the real-project trial (choice 274), because the trial runs fix rounds at gate (deploy).

## The failure, measured against the code

The fix job has 260 minutes (`template/.github/workflows/sdlc-fix.yml:148`) and tells the runner so (`:152`, `SDLC_JOB_TIMEOUT_MINUTES: 260`). One fix round at gate (deploy), in the order the runner runs it:

| Step | Minutes, defaults | Where |
|---|---|---|
| R51's merge of the default branch and re-check of the three targets, only when the default branch moved | up to 45: each target at `gate.command_timeout` (900 s), no grace | `plugin/ci/run_phase.py:3300-3313`; `plugin/ci/base_update.py:45-63` |
| The fix session | 185: `gate.build_max_wall_clock_minutes` (180) plus 5 of grace; with a drive, 180 (the drive's 5 come off the wall clock at gate (deploy)) | `run_phase.py:416-440`, `:317` (the phases that take the build caps), `:323` (`GRACE_MINUTES`); `plugin/gate/limits.py:63`, `:86-105` |
| The commands step | 50: three targets at 900 s plus 5 of grace; 55 with a drive at its default 300 s | `run_phase.py:2378-2391` |
| The judge, at the iteration cap only | 10 | `run_phase.py:286`, `:3717-3733`, `:5003` |
| **Sum** | **290 of 260**, with or without a drive | the row; `sdlc-fix.yml:141-145` says the same |

Two more steps the row does not count:

1. **Check 12's re-check, after the push.** When the work branch moved while the run worked (the owner's "Update branch", a commit by hand), the push merges the remote head in and the runner re-checks the merged tree, the three targets once more (`run_phase.py:3779-3796`): up to 45 minutes more, after the judge. A round that meets both merges needs 335. Check 12 runs after the session of every phase run, design, build, test, deploy and fix (the review pass and the maintain run return before it), not only at gate (deploy): the build job's own sum is then 185 + 50 + 10 + 45 = 290 of its 260 (`template/.github/workflows/sdlc-build.yml:68-78` counts neither check 12 nor the setup), the test job's 125 + 50 + 10 + 45 = 230 of 200, and the deploy job's 355 + 45 = 400 of 355.
2. **The setup and the triage.** `commands.setup` (up to 15 minutes) runs before the session and the R18 triage step (5) after a park; both workflow comments say they are not counted (`sdlc-fix.yml:140-141`).

The runner's own timeouts are the only stops that park: the session's subprocess timeout and the gate's wall-clock check park with "stopped by the runner's timeout". Whether the job can hold the build caps is checked before the session (`build_caps_refusal`, `run_phase.py:384-407`, called after R51's merge and from every `run_caps` call), and that check counts the session, the grace, the commands step and the judge (`build_caps_minutes_needed`, `:371-381`), not R51's re-checks.

**Why nothing parks.** The runner parks from inside its own step, and GitHub has stopped that process. The steps after it, R18's triage steps, are conditioned on `steps.setup.outcome == 'failure' || steps.phase.outcome == 'failure' || steps.phase.outputs.triage == 'park'` (`sdlc-fix.yml:294`, `:298`, `:308`); a step GitHub cancels has the outcome `cancelled`, so none of them runs either, and none of them parks: they explain a park or a failure that already happened. R18 recorded the same: "a job cancelled at timeout-minutes: no step runs", the digest's API line alone (`docs/proposals/failed-run-explains-itself.md:78`), and left "whether an `always()` step runs after a `timeout-minutes` cancellation" to verify (`:103`). It is still open: the central session's wave-5 file lists "the `always()` step after a timeout" among R18's live checks (`docs/handoffs/sessions/2026-10-25-ccr-ca9f0149-a29zgl-wave-5.md`, "Every open item").

## The options

The row lists three. They are not exclusive: A and C each change what fits; B changes what happens when something still does not.

### A. A cap that fits

The session of a fix round at gate (deploy) gives up the minutes the round has already spent before it, so the round's sum stays inside the job. Three forms:

- **A1, measured (recommended).** The runner measures how long R51's merge and re-check took (zero when the default branch had not moved) and takes those minutes off the session's wall clock, as `run_caps` already takes the drive's (`less_minutes`, `limits.py:103-104`), never below `RUN_CAP_FLOOR_MINUTES` (30, `limits.py:115`). The gate's wall-clock check must subtract the same figure, and it cannot recompute it: it recomputes the drive's minutes from `sdlc.yaml` (`drive_minutes(ctx.config)`, `limits.py:582`), but a measured figure exists only in the run. The session runs `start-run` itself and takes its run kind from its environment (`SDLC_RUN=fix`, `plugin/gate/cli.py:148-153`, set by `session_env`, `run_phase.py:2317`), so the runner passes the measured minutes the same way, `start-run` stores them in the run record beside `"run": "build"`, and the check reads them from there. The runner's own subprocess timeout does not read that record, so a session that altered the figure loosens only the gate's check, never the timeout that binds. The sum becomes r + (180 − r + 5) + 50 + 10 = 245 of 260 for any r up to 45, and 245 with a drive; the session loses minutes only in a round where the default branch moved. Check 12's 45 stay outside: they come after the session, so no cap known when the session starts can hold them without taking 45 more off every round.
- **A2, a fixed 45.** The same subtraction, always 45 at gate (deploy): 140 minutes of session in every such round, whether the default branch moved or not. Simpler, and it costs 45 minutes in the rounds that need nothing.
- **A3, a cap of its own.** A new `sdlc.yaml` key, `gate.deploy_fix_max_wall_clock_minutes` (the name to judge by decision 39's rule), 135 by default in code. A guardrail key the owner sets per project; the run reads it as decision 32's two build keys are read.

Files: `plugin/gate/limits.py` (`run_caps`' caller arithmetic, the floor check counts the measured minutes), `plugin/ci/run_phase.py` (measure around `base_update.update_before_offer`; pass the minutes to `run_caps`, `run_timeout_seconds` and the floor check, and to the session through `session_env`; `build_caps_minutes_needed` stays as it is, since with A1 the round needs the session's cap plus 65 minutes whatever the re-check took, and counting the re-check there would refuse the build caps to every round whose default branch moved), `plugin/gate/cli.py` (`start-run` stores the figure), `plugin/gate/limits.py` (the wall-clock check reads it from the run record), the comments of `template/.github/workflows/sdlc-fix.yml` (the arithmetic; no line of YAML changes), and for A3 `template/sdlc.yaml` and `/sdlc-init`. Test plan: `tests/test_gate.py`, `tests/test_ci.py` and `tests/test_base_update.py` (the files that cover `run_caps` and R51 today) gain a round at gate (deploy) with a moved default branch whose re-check took 20 minutes (session cap 160, gate check agrees), one whose branch did not move (180), one with a drive (175 − r), one where r would take the session under the floor (the floor park, as the drive's), and the gate's wall-clock check reading the recorded figure. Owner edits: none for A1 and A2 (the pin move carries them, and the workflow copies change only in comments); A3 adds a line to each project's `sdlc.yaml`.

### B. A park when GitHub cancels

The triage steps also run when the runner's step ends `cancelled`, and a new step parks the change from outside the stopped process.

- **B1, `if: always()` with the outcome read (recommended).** The triage steps' three conditions gain `|| steps.setup.outcome == 'cancelled' || steps.phase.outcome == 'cancelled'`, so the framework the session could reach is replaced and the project checkout verified first (`sdlc-fix.yml:293-316`). A new step after "Verify the project checkout", `if: always() && steps.triage_checkout.outcome == 'success' && (steps.setup.outcome == 'cancelled' || steps.phase.outcome == 'cancelled')`, runs the fresh framework's runner with a new entry (`--cancelled`, no model, no session): it never runs a framework the session could have changed, as the triage steps never do. The step uses the workflow token when the App token is older than 50 minutes, as every publish does (`ci/app_token.py`), and parks the change with `park_and_publish`: the reason "the job was cancelled at its timeout-minutes (N); no gate judged the run", a "what I need from you" that names the step that was running and the minutes the job had, and the review request, the one notification decision 31 allows. It parks with no re-run: a cancel is not decision 29's infrastructure failure, which gets one re-run of the commands step inside a run that is still alive. An owner who cancels a run by hand gets the same park, which says so. What it does beyond the park, per workflow:
  - **fix**: what the unfinished-round park does for a failed session (`park_unfinished_round`, `run_phase.py:2741-2766`, gaps 3 and 4 of `docs/notes/45.md`): the session's uncommitted work in one commit on the PR's head, not gated, and `sdlc:fixing` removed. That function reads the head before the session and the `status.yaml` before it from the runner's memory, which a stopped process loses, so the runner writes both to `$RUNNER_TEMP` before the session starts and the new entry reads them back;
  - **design, build, test**: the park the runner's own timeout makes today (decision 11's note of 2026-10-23: the bound in the reason, the partial evidence committed), on the work branch from the same saved state; the PR is opened if the run had none yet, as the runner's park path already does;
  - **deploy**: the same when the deploy step was cancelled. A cancelled review pass, the job's first runner step, does not park: decision 11's note keeps the review pass red, never parked, and once the job is cancelled no later step of it runs; R18's "Failed runs" line shows it, as today.
- **B2, a `post` step.** `runs.post` belongs to an action's metadata, documented for JavaScript and container actions (GitHub's "Metadata syntax" page, read on 2026-10-25; not tried live); a container action's equivalent is `runs.post-entrypoint`. The framework would need an action of its own, a JavaScript one (against decision 7) or a container image to build, publish and pin, for one step a workflow `if:` already expresses. Not recommended.
- **B3, a job of its own** (`needs: fix`, `if: always() && needs.fix.result == 'cancelled'`) on a fresh runner: it sees only what the round pushed, so the session's uncommitted work is lost, and it doubles the runner start. The fallback if the live check shows that B1's step does not run.

The precondition B rests on is not verified: whether GitHub runs an `always()` step after it cancels a job at its `timeout-minutes`, and for how long. A GitHub documentation issue quotes a GitHub engineer's old forum answer that steps marked `always()` keep running within about five minutes after a cancellation (github/docs issue 45403, read on 2026-10-25); it does not cover a job's timeout and is not GitHub's documentation. So B's build starts with a live check: a throwaway workflow in this repository whose job sleeps past a 2-minute `timeout-minutes`, with an `always()` step that writes a line and one that sleeps 6 minutes; the run's log says which ran and when the second was stopped, recorded as a note under `docs/notes/`. That check also closes R18's open item.

Files: `template/.github/workflows/sdlc-fix.yml` (the new step, the three triage conditions); the same in `sdlc-design.yml`, `sdlc-build.yml`, `sdlc-test.yml` and `sdlc-deploy.yml` if the owner takes B everywhere (below); `plugin/ci/run_phase.py` (the state saved to `$RUNNER_TEMP` before the session, the `--cancelled` entry, reusing `park_unfinished_round` and `park_and_publish`); `plugin/ci/triage.py` if the triage reads the cancelled step's log differently. Test plan: the `--cancelled` entry on a fix branch with uncommitted work (one commit, the park, `sdlc:fixing` removed), with none (the park alone), on an automatic round, on a change already parked (no second park), with no saved state (a park with no commit), on a build with no PR yet, and on a deploy job whose review pass was cancelled (no park), in `tests/test_fix_round_gaps.py` beside the unfinished-round tests and `tests/test_ci.py`; `tests/test_templates.py` checks each workflow's new step and its condition. Owner edits: each workflow copy the build changes, in the same PR as the pin move (`python tasks.py workflow-copies`); until a project's copies move, B does nothing there.

### C. `timeout-minutes` rises with `SDLC_JOB_TIMEOUT_MINUTES`

The fix job's ceiling goes from 260 to 355, as the deploy job's already is (`sdlc-deploy.yml:69-78`, "five under the 360 a GitHub-hosted job may run"): 45 + 185 + 50 + 10 + 45 = 335, and 350 with the setup's 15. The runner's `build_caps_minutes_needed` counts the re-checks at gate (deploy), so an older copy at 260 falls back to the general caps there.

Files: `template/.github/workflows/sdlc-fix.yml:148`, `:152` and its comment; `plugin/ci/run_phase.py` (`build_caps_minutes_needed` with the gate phase); `tests/test_templates.py`, `tests/test_ci.py`. Owner edits: the fix copy, two lines, in every project. A job's ceiling costs no minutes until it is used, but the round then holds the PR's concurrency group (`sdlc-fix.yml:128-130`) up to six hours, and a job at 355 has no room left: the next step anyone adds, or a setup over 15 minutes, is cancelled again with no park, so C moves the edge and keeps the failure.

## Recommendation

**A1 and B1 together, B1 in every phase workflow; C not taken.**

- A1 makes the case the row measures fit, in plugin code alone: a project gets it with the pin move and no edit to a workflow copy or to `sdlc.yaml`, and the runner's own timeout, which parks, fires before GitHub's as long as the installs, checkouts and `commands.setup` before the session take under 15 minutes (245 + 15 = 260); past that, B1 parks. It costs session minutes only in the rounds that spent them on the re-check, and a fix round at gate (deploy) answers review comments on a built change: 135 minutes is above the 120 every non-build run gets (`limits.py:60`). A2 costs those minutes in every round; A3 adds an option to every project's guardrail file, where decision 37 removed options nobody turned on.
- B1 is the net for what no cap foresees: check 12's re-check after the push, a setup over 15 minutes, a hung `git fetch`, an owner's cancel. It is the only option that turns "no park" into a park, which is the row's failure. Check 12 reaches every phase run and the R18 steps already sit in the design, build, test, deploy and fix workflows, so the same step goes in all five; a park in the fix workflow alone would leave the build job's 290 of 260, the test job's 230 of 200 and the deploy job's 400 of 355 (above) as they are.
- C changes nothing a round needs once A1 holds, costs an edit in every project's copy, and keeps a job that can still be cancelled with nothing parked.

Built in that order: A1 first (plugin only, its own version), then B1 after its live check, with the workflow copies.

## What to settle before building

| Question | Recommendation |
|---|---|
| A1, A2 or A3 | A1 (above) |
| B1 in the fix workflow alone, or in the five phase workflows | The five: check 12 runs in each |
| Check 12's 45 at build and test, counted in `build_caps_minutes_needed` | Not counted: B1 parks the rare round that meets it; counting it would take 45 from every build session |
| B1 at deploy when the review pass, not the deploy step, was cancelled | No park: decision 11's note keeps the review pass red; the "Failed runs" line shows it |
| B1's park when the owner cancelled the run by hand | Park, with a reason that says the run was cancelled; the owner removes the label or starts a round |
| If the live check shows no `always()` step runs after a job timeout | B3 instead of B1, with the decision file annotated |

## Considered and not chosen

- **Shortening the fix session at gate (deploy) by its own hand, with no measure** (change 0004's design declined it, "it does not shorten the fix session at (e) to fit the job", spec R4): A1 is that shortening, bounded by what the round actually spent.
- **A deadline for the whole job** (the runner reads the job's start and gives the session what is left after the commands step, the judge and a re-check reserve): it would cover the setup and check 12 too, but every run's cap would then move with the time GitHub took to start it, and the gate's wall-clock check could no longer say which cap a run had from the record alone. Not listed by the row; worth a row of its own if B1's parks show it is needed.

## Decisions it touches

- **32 is amended** (as decision 37 left it): the raised build caps stay, and a fix round at gate (deploy) gives up the minutes R51's merge and re-check took, as change 0004 already made it give up the drive's. The caps' figures in `sdlc.yaml` do not change. The decision file is drafted beside this proposal: `docs/decisions/41.md`, which the owner's merge of this PR accepts, as written or as amended in review; decision 32's sentence on the raised limits is annotated beside it, and its `amended_by` names 41.
- **R18 changes in one row:** a cancelled run that B1 parks is in the queue, so the digest's "Failed runs" line no longer lists it (`plugin/pr/failed_runs.py:4-6`: "that did not park"); R18's row "a job cancelled at timeout-minutes: no step runs" (`docs/proposals/failed-run-explains-itself.md:78`) then holds only for a lost runner, a cancelled review pass and a run whose B1 step did not run. B1's build annotates that row.
- **Kept:** 11 (a phase that cannot finish parks; B1 makes a job GitHub cancels do what 11 already says, and a cancelled review pass stays red as 11's note keeps it, so 11 itself does not change), 29 (the automatic round, the iteration cap and the judge; a cancelled automatic round parks and drops `sdlc:fixing`), 20 as amended by 31 (the park's review request is the only notification), 7 (Python only; B2 not taken), R51's merge and re-checks as they are, and the fix job's 260 minutes.

## Order

After R45 and before the real-project trial (ROADMAP R67's Order cell, choice 274). A1 first, then B1 after its live check.

| Part | Where | When |
|---|---|---|
| The decision file | `docs/decisions/41.md`, this documentation PR | First, before the intent |
| A1: the measured minutes off the session, the gate's check and the floor counting them | `plugin/gate/limits.py`, `plugin/gate/cli.py`, `plugin/ci/run_phase.py`, the fix template's comment, tests | After R45 |
| The live check of an `always()` step after a job timeout | a throwaway workflow; `docs/notes/` | Before B1 |
| B1: the park on `cancelled` and the triage conditions | `plugin/ci/run_phase.py`, the design, build, test, deploy and fix templates, tests; the owner's workflow copies | After the live check |
