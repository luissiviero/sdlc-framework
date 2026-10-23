# Session of 2026-10-23 on branch `claude/parallelism-inventory`: the parallelism inventory, report only

**Builds on:**
- `docs/handoffs/sessions/2026-10-23-ccr-b2d02bf7-9ywgjn-handoff.md` (#346, merged as `d80981a`), the newest on `main`, and the files it carries;
- `2026-10-23-ccr-b2d02bf7-9ywgjn-end.md`, the central session's end file, read on its branch at `2faa553` (#352, a draft, not on `main`).

No other session file reached `main` since (verified, `git fetch origin main` and `ls docs/handoffs/sessions/` on `d80981a`, read at 10:30 UTC).

## Where the project stands
- **Framework `main` is at `d80981a`** (#346), on plugin **1.0.27** (verified, `git log -1 origin/main`). The root pin at 1.0.17 is carried, not re-verified.
- **Open PRs**, read at 10:30 UTC on `d80981a`: #352 (choice 262, draft), #351, #350 (1.0.29, draft), #349 (1.0.29, draft), #348 (1.0.28, draft), #173.
- **This PR** adds `docs/reviews/2026-10-23-parallelism-inventory.md`: the inventory of the parallelism the framework has, has accepted and has dropped, the gaps a pipeline-level central session would fill, and the options. It is documentation only. Its record is `docs/progress/2026-10-23-claude-parallelism-inventory.md`.

## Preconditions of the moment
- The standing ones are in `HANDOFF.md`.
- **Numbers:** run `python tasks.py next-free` after `git fetch origin`; several branches hold numbers above `main`. This PR takes none.

## Next steps, in order
1. **This PR**: the owner merges it when `Framework checks` is green on its final head.
2. **The owner's six questions** at the end of the review, with a recommendation for each.
3. **#352**: its `docs/handoffs/central-session.md:38` overclaims what `version-check` and check 10 refuse (the review, section 1b); the central session corrects it, or the owner asks for it.
4. Everything else carried from `2026-10-23-ccr-b2d02bf7-9ywgjn-end.md` on #352's branch, "Next steps, in order", not re-verified.

## Every open item
| Item | Where | What is left | Who acts | Blocks 1.0.0 |
|---|---|---|---|---|
| This PR | framework | Green checks, the owner's merge | this session; owner | no |
| The central session as a pipeline feature | `docs/reviews/2026-10-23-parallelism-inventory.md`, "What the owner decides" | The owner's six answers | owner | no |
| Two stale proposal sentences | `docs/proposals/concurrent-changes.md:28`; `docs/proposals/weekly-window-guarded.md:110` | Annotate in a documentation PR | a session | no |
| Everything else carried | `2026-10-23-ccr-b2d02bf7-9ywgjn-end.md` (#352's branch) and `2026-10-23-ccr-b2d02bf7-9ywgjn-handoff.md`, "Every open item" | Carried, not re-verified | as there | no |

## What the owner does
| When | Act |
|---|---|
| Now | Merge this PR when `Framework checks` is green on its final head. |
| When you choose | Answer the review's six questions, as recommended or one by one. |
