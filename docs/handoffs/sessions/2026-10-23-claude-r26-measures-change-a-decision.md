# Session of 2026-10-23 on branch `claude/r26-measures-change-a-decision`: wave 4, lane A, R26

**Builds on:** `docs/handoffs/sessions/2026-10-23-ccr-545fcec0-ik69zj-end.md` (wave 3's close), and through it the files it names; `docs/handoffs/sessions/2026-10-23-ccr-545fcec0-ik69zj-wave-4.md` (the central session's start of wave 4, #374), merged into this branch from `main` at `a43f27c`.

## Where the project stands
- `main` at `b9dbd9b` (#373) on plugin 1.0.38 when this session started (verified, `git log -1 origin/main` after `git fetch origin`, read at 18:15 UTC). This branch bumps the plugin to 1.0.39, pushed at once to hold the number (`python tasks.py version-check` exits 0 after the fetch).
- **This session's PR**: #375, draft, R26 as plugin 1.0.39 (the record: `docs/progress/2026-10-23-claude-r26-measures-change-a-decision.md`).
- `main` moved to `a43f27c` (#374, documentation only) while this PR was open; this branch merged it with a merge commit. `python tasks.py next-free` then lists 1.0.39 as taken by this branch, and `version-check` exits 0.
- The parallel lane B (`session_01GMeUbY1Qeij4EVopiNaN8q`) prepares R14 (change 0004, PR #173); carried from the wave 4 file, not re-verified.

## Preconditions of the moment
- The standing ones are in `HANDOFF.md`; the central session's in `docs/handoffs/central-session.md`.

## Next steps, in order
1. **#375**: an independent review is run and its findings fixed with tests; `Framework checks` green on the final head; the central session names it for merge once this lane reports it ready; the owner merges.
2. **R26's DORA row** (part 4): a change of its own, as the proposal's Order table says; it reads R13's release record and owns the rollback record (the proposal's settle table).
3. The rest as wave 3's close lists it.

## Every open item
| Item | Where | What is left | Who acts | Blocks 1.0.0 |
|---|---|---|---|---|
| #375 | framework | Green checks on its final head, the owner's merge | owner | no |
| R26 part 4, DORA | `docs/proposals/measures-that-change-a-decision.md`, Order table | Its own change, after this one | a session | no |
| R26 part 3's R37 half | the proposal's Order table | The standing PR's "found in N changes" line, its digest line and the mark on a build PR after a line merged, built with R37 | a session | no |
| R14's preparation | lane B | The intent's refresh on #173, the pin-move rows | lane B; owner | no |
| The lanes' effort level | their settings | High; `create_session` cannot set it | owner | no |
| Everything wave 3's close lists open | `2026-10-23-ccr-545fcec0-ik69zj-end.md`, "Every open item" | Carried, not re-verified | as there | no |

## What the owner does
| When | Act |
|---|---|
| When the central session names #375 | Merge it, once `Framework checks` is green on its final head. |
| When lane B reports | The pin-move rows, then #173 (carried from the wave 4 file). |
