# Session of 2026-10-23 on branch `claude/decision-39-names`: the small lane of wave 3 (the release record as owner-only fields, decision 39)

**Builds on:**
- `docs/handoffs/sessions/2026-10-23-claude-r66-follow-up.md` (#361) and `2026-10-23-claude-r65-part-6-follow-up.md` (#359), the newest on `main` at `be5be5e`, read in full;
- `2026-10-23-ccr-545fcec0-ik69zj.md`, the second central session's file, read on its branch for the lanes of wave 3, and on `main` since;
- the files those carry, by reference, not re-verified.

This session built two PRs: #363 (branch `claude/released-owner-fields`, choice 268 (d), plugin 1.0.34) and this one (choice 268 (b), decision 39, no version). This file is committed in the last of them, this one.

## Where the project stands
- **Framework `main` is at `2a0e7c7`** (#363), plugin **1.0.34** (verified, `git log -1 origin/main` after `git fetch origin`, read at 15:30 UTC). #363 made `released_at`, `released_sha` and `released_pr` owner-only fields; the central session's choice 268 and lane B's decision 40 reached `main` before it. `main` is merged into this branch with a merge commit; the decisions index was regenerated, not merged by hand.
- **This PR** writes decision 39; nothing is renamed. R45's renames are wave 5.

## Preconditions of the moment
- The standing ones are in `HANDOFF.md`; the wave's in the central session's file.
- **Numbers:** decision 39 is this PR's (choice 268 (b)); decision 40 and patch 1.0.34 are on `main`. A conflict in `docs/decisions/index.md` is fixed by `python tasks.py decisions-index`.

## Next steps, in order
1. **This PR**: the owner merges it when `Framework checks` is green on its final head.
2. Lanes A and B branch from `2a0e7c7` or later (the central session tells them).
3. Everything else as the files above list it.

## Every open item
| Item | Where | What is left | Who acts | Blocks 1.0.0 |
|---|---|---|---|---|
| This PR | framework | Green checks, the owner's merge | this session; owner | no |
| The release record's known limits (a release during a run; a record already on the branch; `OPERATING_MODEL.md:108`) | `docs/progress/2026-10-23-claude-released-owner-fields.md`, "Known limits" | A follow-up if the owner wants one | owner; a session | no |
| The names older than 1.0.14 the table missed | `docs/progress/2026-10-23-claude-decision-39-names.md`, "Known limits" | R45's PR 1 lists those with a phase letter | the R45 session | no |
| Everything the files above list open | their "Every open item" | Carried, not re-verified | as there | no |

Done, dropped: "`status.yaml`'s `released_*` fields as owner-only fields" of `2026-10-23-claude-r65-part-6-follow-up.md`: the owner's answer is choice 268 (d); merged as `2a0e7c7` (#363).

## What the owner does
| When | Act |
|---|---|
| Now | Merge this PR when it is green. |
