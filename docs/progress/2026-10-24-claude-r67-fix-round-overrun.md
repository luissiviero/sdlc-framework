# Progress — ROADMAP R67, a fix round at (e) that can overrun its job (2026-10-24)

This session is the small lane of wave 4, asked by the central session `session_016NLfdsdfTFZUyrVGN4Ektc`. It ran on branch `claude/r67-fix-round-overrun`, from `main` at `f9a3f7e` (#379). It adds one row to `docs/ROADMAP.md`; documentation only, no plugin version.

## The owner's choices
272. **Add the R67 ROADMAP row** (the owner, 2026-10-24, to the central session: "Do this for me: add the R67 ROADMAP row, the fix round at (e) that can overrun its job time limit"). The row is the one change 0004's design drafted in `changes/0004-drive-target-and-proof-items/evidence/fix-response.md` (item 6, line 131), from panel decision 2 of its gate (b) and the owner's review on PR #378, item 6. A (b) branch may commit only its change folder, so the design could not add the row itself.

## What was written
1. **`docs/ROADMAP.md`**: R67 after R66, in the candidates table. The text is the draft's, with the escapes of the draft's own table removed (`\|` and `` \` ``). One dated annotation in the Status cell names choice 272 and the draft. The Order cell is blank and the status is `proposed`: the table's rule says "Until then the row says `proposed` and the order is blank", and "A blank cell is a candidate not yet placed" (the paragraph above the table). The owner ranks it.

## The row's facts, checked on `main` at `f9a3f7e`
- 260 minutes: `template/.github/workflows/sdlc-fix.yml:138` (`timeout-minutes: 260`) and `:142` (`SDLC_JOB_TIMEOUT_MINUTES: 260`).
- Session 185, commands step 50, judge 10: `plugin/ci/run_phase.py:265` ("session 185 + 50 + 10 < 260") and `:267` (`JUDGE_TIMEOUT_SECONDS = 10 * 60`).
- R51's merge and re-check, 45, only when the default branch moved: `template/.github/workflows/sdlc-deploy.yml:69-70` ("45, once: the second step merges only when the default branch moved in between"). With a drive, 180 and 55: change 0004's `spec.md:101-102`.
- 290 of 260 either way: 45 + 185 + 50 + 10 and 45 + 180 + 55 + 10; `spec.md:102`, `:504-505` and Flagged concerns item 2 (`:517`).
- "The park steps run only on a failed step": the triage and park steps of `sdlc-fix.yml` (`:284`, `:288`, `:298`) carry `if: always()`, but they also read `steps.setup.outcome == 'failure' || steps.phase.outcome == 'failure' || steps.phase.outputs.triage == 'park'`. A step cut by a cancelled job has the outcome `cancelled`, so none of them acts. The row's remedy "`if: always()` with the outcome read" means reading `cancelled` too.
- Decisions: 29 (`docs/decisions/29.md`, a red target starts the next fix round), 32 (`docs/decisions/32.md:13`, the raised build caps), 20 (`docs/decisions/20.md`, how finished work reaches the owner); each opened.

## Proposed edits for the owner
None.

## Port list
Not on it: documentation only.
