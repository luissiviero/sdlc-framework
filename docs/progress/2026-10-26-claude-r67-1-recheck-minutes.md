# Progress — R67's first PR: a fix round at deploy gives up the minutes its merge and re-check took (2026-10-26, plugin 1.0.49)

This session ran on branch `claude/r67-1-recheck-minutes`, from `main` at `ae604a6` (#399, plugin 1.0.48), as lane H of wave 5, started by the central session on the owner's acceptance of decision 41 (2026-10-25). It builds decision 41's point 1 (the proposal's A1, `docs/proposals/fix-round-fits-its-job.md`) as one PR, plugin **1.0.49** (`python tasks.py next-free` after `git fetch origin` on `ae604a6`). No numbered choice, note or decision is taken in this PR.

## What was built
1. **The runner measures the merge and re-check** (`plugin/ci/run_phase.py`): in a fix round whose change is at deploy, the time around `base_update.update_before_offer` becomes `recheck_minutes`, whole minutes rounded up (`recheck_minutes_spent`), 0 when nothing was merged (the default branch had not moved) or the update parked. The review pass and the deploy run measure nothing: their jobs hold the re-check (the deploy job's 355).
2. **The minutes come off the session's wall clock** with the drive's, never below the 30-minute floor: `run_caps` and `run_timeout_seconds` take `recheck_minutes` at the deploy gate only (`limits.run_caps`' `less_minutes`, as change 0004 takes the drive's). The turn cap does not change. `build_caps_minutes_needed` does not count them (decision 41 point 1). The round's sum is r + (180 − r + 5) + 50 + 10 = 245 of 260 for any r up to 45, with or without a drive (the drive's 5 come off the session and go to the commands step).
3. **The floor park counts them**: `limits.drive_floor_refusal` takes the re-check's minutes as a third argument and names them in the reason; its "what I need from you" is the new `RECHECK_FLOOR_NEED` when they counted (`limits.floor_need`): the park pushes the merge, so the next round finds nothing to merge and keeps its whole cap.
4. **The session carries the figure** as `SDLC_RECHECK_MINUTES` (`limits.RECHECK_MINUTES_ENV`), beside `SDLC_RUN=fix` (`session_env`); any other session, and a value the workflow's `env:` set, carries none.
5. **`start-run` keeps it** in `evidence/run-<phase>.json` as `"recheck_minutes"`, only under `SDLC_RUN=fix` and only a positive whole number (`plugin/gate/cli.py`).
6. **The gate's wall-clock check subtracts it** at the deploy gate, read from the record (`limits.recorded_recheck_minutes`; a value that is not a whole number counts nothing), and its floor park counts it too. A session that lowered the recorded figure loosens only the gate's check, never the runner's subprocess timeout, which binds.
7. **Docs and comments**: `/sdlc-fix` step 2 names the variable; `sdlc-fix.yml`'s comment carries the new arithmetic (comment lines only; no line of YAML changes); the `limits.py`, `gate/cli.py` and `run_phase.py` docstrings.

Tests (none deleted or skipped): `tests/test_ci.py` gains the arithmetic (20 minutes → 160, none → 180, a drive → 155, 45 → 135, not at build, the floor at 30, the 245 sum for r in 0, 1, 20, 45, `build_caps_minutes_needed` unchanged), the session's environment, two end-to-end fix rounds at deploy with the runner's clock moved by the merge (19.5 minutes → a 165-minute timeout and `SDLC_RECHECK_MINUTES=20`; nothing merged → 185 and no variable) and the floor park before any session; `tests/test_gate.py` gains `start-run`'s record and the gate's wall-clock check reading it (160, 180 without, a drive, garbage values, the floor park and its need, another gate).

## The fresh-context review
PENDING

## Point 3: the live check (before PR 2)
PENDING

## Port list
This PR touches `plugin/ci/run_phase.py` and the comment of the fix workflow template: it goes on the port list until the 1.0.0 read.

## Proposed edits for the owner
None to a guardrail file. The fix workflow copy changes in comments only:

| Link | Row | What is there | What it must become |
|---|---|---|---|
| `.github/workflows/sdlc-fix.yml` | the comment above `timeout-minutes: 260` | the 1.0.48 template's comment | the 1.0.49 template's comment: `python tasks.py workflow-copies` on this PR's branch, then commit and push |

## What the owner does
| When | Act |
|---|---|
| Before merging | Run `python tasks.py workflow-copies` on this PR's branch, commit and push, so `Framework checks` can go green (its copies test compares this repository's copy with the template). |
| Then | Merge this PR when `Framework checks` is green on its final head. |
| For point 3 | The live check's steps in the PR body. |
