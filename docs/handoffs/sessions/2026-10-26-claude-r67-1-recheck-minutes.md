# Session of 2026-10-26 on branch `claude/r67-1-recheck-minutes`: wave 5, lane H, R67's first PR

**Builds on:** `docs/handoffs/sessions/2026-10-26-claude-r45-6-live-readers.md` (lane G, #399) and the files it names. Their open items are carried by reference, not re-verified, but for the rows below.

## Where the project stands
- **Framework `main` is at `ae604a6`** (#399), on plugin **1.0.48** (`git fetch origin` and `git log -1 origin/main`, read at 2026-10-26 on `ae604a6`). This repository's pin is carried from lane G's file, not re-verified (1.0.46).
- **This PR:** R67's first PR, plugin **1.0.49**: decision 41's point 1, a fix round at deploy gives up the minutes R51's merge and re-check took. Record: `docs/progress/2026-10-26-claude-r67-1-recheck-minutes.md`.
- **Point 3's live check** is designed and waits for the owner: the throwaway workflow is on the branch `claude/r67-timeout-check` (`702ca87`).

## Preconditions of the moment
- The standing ones (`HANDOFF.md`); the central session's in `docs/handoffs/central-session.md`.
- **Until the owner commits this PR's fix workflow copy** on its branch, `Framework checks` is red on two tests of `tests/test_templates.py` that compare the copy with the template (the copy changes in comments only).

## Next steps, in order
1. **This PR:** the owner commits the workflow copy and merges when `Framework checks` is green.
2. **Point 3:** the owner runs the live check (the PR body's steps); the lane reads the run and records a note.
3. **R67's second PR** (decision 41 point 2, B1, or the fallback the live check calls for), after step 2, with the five workflow copies.
4. The other next steps of the files this one builds on, carried, not re-verified; lane G's step 2 (R67) is under way here.

## Every open item
| Item | Where | What is left | Who acts | Blocks 1.0.0 |
|---|---|---|---|---|
| This PR | framework, branch `claude/r67-1-recheck-minutes` | The workflow copy, green checks, the merge | owner | no |
| Point 3's live check | branch `claude/r67-timeout-check` | The run, then the note, then both throwaway branches deleted | owner, then the lane | no |
| R67's second PR | decision 41 point 2 | Built after the live check | the lane | no |
| The port list | this PR's record | This PR touches `plugin/ci/run_phase.py` and the fix workflow template's comment | the 1.0.0 read | no |
| Everything the files above list open | their "Every open item" | Carried, not re-verified | as there | no |

## What the owner does
| When | Act |
|---|---|
| Now | Commit the fix workflow copy on this PR's branch (`python tasks.py workflow-copies`); merge when green. |
| Now or after | Run point 3's live check (the PR body's steps). |
