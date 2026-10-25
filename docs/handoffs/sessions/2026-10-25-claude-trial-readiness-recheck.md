# Session of 2026-10-25 on branch `claude/trial-readiness-recheck`: wave 5, lane C, the trial readiness re-check

**Builds on:** `docs/handoffs/sessions/2026-10-25-ccr-ca9f0149-a29zgl-wave-5.md` (#386), `2026-10-25-claude-r67-order-cell.md` (#388), `2026-10-25-claude-r67-proposal-decision.md` (#391) and `2026-10-25-claude-0004-workflow-comments.md` (#385), and through them the files they name; their open items are carried by reference, not re-verified, but for the rows named below.

## Where the project stands
- **Framework `main` is at `7ac4131`** (#391), on plugin **1.0.44**, tagged `v1.0.44` on `dc9692b` (#390) (verified, `git fetch origin`, `git log -1 origin/main` and `git tag --points-at dc9692b`). R45's PRs 1 and 2 are merged (#389, 1.0.43; #390, 1.0.44); PR 3 is on `claude/r45-3-config-values`, taking the next patch (`python tasks.py next-free`). Read at 22:02 UTC on 2026-10-25 on `7ac4131`. Decision 41 is accepted (#391).
- **This PR**: the trial readiness re-check (`docs/reviews/2026-10-25-trial-readiness-recheck.md`) and one dated annotation on the review of 2026-10-20 (the record: `docs/progress/2026-10-25-claude-trial-readiness-recheck.md`). Documentation only, no version.

## Preconditions of the moment
- The standing ones are in `HANDOFF.md`; the central session's in `docs/handoffs/central-session.md`.
- Lane A's R45 PRs land on `main` in parallel; this PR shares no file with them.

## Next steps, in order
1. **This PR**: `Framework checks` green on its final head; the central session names it; the owner merges.
2. **What the re-check lists before `/sdlc-init`**, in its table "What is still needed": items 1 to 7 and the App of item 12 can start now; items 8 to 11 are R45's PRs 3 to 6 with the two pin moves, and R67's build.
3. The rest as the files above list it.

## Every open item
| Item | Where | What is left | Who acts | Blocks 1.0.0 |
|---|---|---|---|---|
| This PR | framework | Green checks, the owner's merge | owner | no |
| The trial's decisions T1 to T6 | the re-check, "The owner's decisions the trial still needs" | The owner's answers | owner | no |
| The trial's live checks (items 2, 3 and 7) | the re-check | The detection on the real clone; a sandboxed Java or Rust target's writes and registry, if the stack is one; the `always()` step after a job timeout (already an open item of `2026-10-25-claude-r67-proposal-decision.md`) | owner; a session | no |
| Everything the files above list open | their "Every open item" | Carried, not re-verified | as there | no |

## What the owner does
| When | Act |
|---|---|
| When the central session names this PR | Merge it, once `Framework checks` is green. |
| Now | Answer T1 (which project) and T2 (public or private); the rest of the re-check's decisions can wait for `/sdlc-init`. |
| Once T1 is answered | Create the project's GitHub App on the trial repository (desktop-only; `/sdlc-init` step 6's App bullet). |
