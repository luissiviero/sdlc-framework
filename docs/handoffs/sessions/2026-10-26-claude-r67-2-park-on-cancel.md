# Session of 2026-10-26 on branch `claude/r67-2-park-on-cancel`: wave 5, lane H, R67's second PR

**Builds on:** `docs/handoffs/sessions/2026-10-26-claude-r67-1-recheck-minutes.md` (this lane's first PR, #400) and the files it names. Their open items are carried by reference, not re-verified, but for the rows below.

## Where the project stands
- **Framework `main` is at `0fb7b99`** (#400), on plugin **1.0.49**, tagged `v1.0.49` (as the central session reported at 23:04 UTC; `git fetch origin` read `0fb7b99` on `main`).
- **This PR:** R67's second PR, plugin **1.0.50**: decision 41's point 2, a job GitHub cancels parks the change, after point 3's live check (note 62, run 40414066074). Record: `docs/progress/2026-10-26-claude-r67-2-park-on-cancel.md`. With it, R67's points are built.
- The live check's throwaway branches are deleted (the central session's message of 23:04 UTC).

## Preconditions of the moment
- The standing ones (`HANDOFF.md`); the central session's in `docs/handoffs/central-session.md`.
- **Until the owner commits this PR's five workflow copies** on its branch, `Framework checks` is red on two tests of `tests/test_templates.py` that compare the copies with the templates.

## Next steps, in order
1. **This PR:** the owner commits the workflow copies and merges when `Framework checks` is green.
2. **The owner's two answers** in the record's "What I need from you" (a second throwaway check of a cancelled step's child processes; the digest's mark), each with a recommendation.
3. The other next steps of the files this one builds on, carried, not re-verified; R67's points are done here.

## Every open item
| Item | Where | What is left | Who acts | Blocks 1.0.0 |
|---|---|---|---|---|
| This PR | framework, branch `claude/r67-2-park-on-cancel` | The five workflow copies, green checks, the merge | owner | no |
| A cancelled step's child processes | this PR's record, "What I need from you" 1 | Whether they outlive the step: a second throwaway check, then a follow-up if they do | owner, then a lane | no |
| The port list | this PR's record | This PR touches `plugin/ci/run_phase.py` and the fix workflow template | the 1.0.0 read | no |
| Everything the files above list open | their "Every open item" | Carried, not re-verified | as there | no |

Done, dropped: lane H's "R67's second PR" and "point 3's live check" rows (this PR; note 62).

## What the owner does
| When | Act |
|---|---|
| Now | Commit the five workflow copies on this PR's branch (`python tasks.py workflow-copies`); merge when green. |
| When convenient | Answer the record's "What I need from you". |
