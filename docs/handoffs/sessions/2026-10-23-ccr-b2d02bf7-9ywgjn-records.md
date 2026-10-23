# Session of 2026-10-23 on branch `ccr-b2d02bf7-9ywgjn`, second file: one record file per session (choice 259)

**Builds on:**
- `docs/handoffs/sessions/2026-10-23-ccr-b2d02bf7-9ywgjn.md`, this session's first file, merged with #336 (`26f03c1`), the newest on `main`;
- the files it builds on and carries: `2026-10-23-ccr-fc4dc248-6pmtbd-end.md` and `2026-10-23-claude-r65-part-5-handoff.md`.

No other session file reached `main` since (verified, `ls docs/handoffs/sessions/` on `26f03c1` after `git fetch`).

## Where the project stands
- **Framework `main` is at `26f03c1`** (#336), on plugin **1.0.24** (verified, `git log -1 origin/main`, `.claude-plugin/plugin.json`). The root pin at 1.0.17 is carried, not re-verified.
- **This PR** changes how sessions keep their records (choice 259): one file per session in `docs/progress/`, and `docs/PROGRESS.md` a fixed page. Its record is `docs/progress/2026-10-23-ccr-b2d02bf7-9ywgjn.md`, the first written that way.
- **Open PRs**, read at 02:52 UTC on `26f03c1`: #173 (intent 0004) and this PR. The owner's #328 (the merge-tool deny rule) is merged (verified, the GitHub API: `merged_at` 2026-10-23T02:46:38Z).

## Preconditions of the moment
- The standing ones are in `HANDOFF.md`. Once this PR merges, a session writes its record as its own file ("How a session ends", step 4).
- **Numbers:** run `python tasks.py next-free` before taking one.

## Next steps, in order
1. **This PR**: the owner merges it when `Framework checks` is green on its final head.
2. **R5's check** (choice 257): one PR with `tasks.py` and its tests, no plugin version.
3. **The parallel build sessions**, once this PR and R5's check are in: the queue in ROADMAP's Order column, from R51 with R25, with R44 and R59 beside it in a second session, as the owner's speed suggestions describe (`docs/progress/2026-10-23-choices-257-258.md`, "Not decided"). Whether to run them is the owner's word.
4. **The merge-tool deny rule**: #328 is in, so a session checks live that it binds; then the template candidate, or the gap recorded as a known limit (choice 253, point 7; carried from the part-5 file).
5. **At the sample's next change**: the four live facts go into a note; the sample's `sdlc.yaml:39` and its pin move (carried).
6. **This repository's own move from pin 1.0.17** at R14's turn (#173; carried).
7. **At R8's turn, last in the queue (choice 256):** the Gemini items (carried from this session's first file).

## Every open item
| Item | Where | What is left | Who acts | Blocks 1.0.0 |
|---|---|---|---|---|
| This PR | framework | Green checks, the owner's merge | this session; owner | no |
| The `CLAUDE.md` row of choice 259 | this PR's record, "Proposed edits for the owner" | Line 39 names the session's record instead of `docs/PROGRESS.md` | owner | no |
| R5's check | ROADMAP R5 (choice 257) | One PR | the next session | no |
| The speed suggestions | `docs/progress/2026-10-23-choices-257-258.md`, "Not decided" | The owner's answer on the others; the trial project's facts if the trial moves forward | owner | no |
| The Gemini session's items | `2026-10-23-ccr-fc4dc248-6pmtbd-end.md`, "Every open item" | Carried, not re-verified; at R8's turn (choice 256) | as there | no |
| Everything the part-5 file lists open | `2026-10-23-claude-r65-part-5-handoff.md`, "Every open item" | Carried, not re-verified | as there | no |

Done, dropped:
- "This PR" of this session's first file (#336): merged as `26f03c1`.
- "Merge #328" (the part-5 file's "What the owner does"): merged at 02:46:38 UTC on 2026-10-23.

## What the owner does
| When | Act |
|---|---|
| Now | Merge this PR when `Framework checks` is green on its final head. |
| Any time | The `CLAUDE.md` row in this PR's record. |
| When you choose | Say whether to start the parallel build sessions, and name the trial project if it moves forward. |
