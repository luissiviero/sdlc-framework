# Session of 2026-10-25 on branch `claude/r67-proposal-decision`: wave 5, lane B, R67's proposal and decision 41 (draft)

**Builds on:** `docs/handoffs/sessions/2026-10-25-claude-r67-order-cell.md`, `2026-10-25-claude-0004-workflow-comments.md` and `2026-10-25-ccr-ca9f0149-a29zgl-wave-5.md`, and through them the files they name; their open items are carried by reference, not re-verified, but for the rows named below.

## Where the project stands
- **Framework `main` is at `0ce7f6b`** (#389, R45's first rename PR), on plugin **1.0.43** (verified, `git fetch origin` and `git log -1 origin/main`, read at the start of this session on 2026-10-25).
- **This PR**: R67's proposal (`docs/proposals/fix-round-fits-its-job.md`) and its decision file drafted as `docs/decisions/41.md` (the record: `docs/progress/2026-10-25-claude-r67-proposal-decision.md`). Documentation only, no version.

## Preconditions of the moment
- The standing ones are in `HANDOFF.md`; the central session's in `docs/handoffs/central-session.md`.
- Lane A's R45 PRs land on `main` in parallel; this PR shares only the generated indexes with them (regenerated after any merge of `main`, never by hand).

## Next steps, in order
1. **This PR**: `Framework checks` green on its final head; the owner accepts or amends decision 41 in review and merges.
2. **R67's build, after R45** (choice 274): A1 first, in a plugin version of its own; then the live check of an `always()` step after a job timeout (a note), then B1 with the workflow copies.
3. The rest as the files above list it.

## Every open item
| Item | Where | What is left | Who acts | Blocks 1.0.0 |
|---|---|---|---|---|
| This PR | framework | Green checks; the owner's choice on decision 41 and merge | owner | no |
| The `always()` step after a job timeout | R18's live checks (the wave-5 file); B1's precondition | One throwaway workflow run, recorded as a note | a session | no |
| Everything the files above list open | their "Every open item" | Carried, not re-verified | as there | no |

## What the owner does
| When | Act |
|---|---|
| When the central session names this PR | Read decision 41; accept it as drafted or ask for an amendment in review; merge once `Framework checks` is green. |
