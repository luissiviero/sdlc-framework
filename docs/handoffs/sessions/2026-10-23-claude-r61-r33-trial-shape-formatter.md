# Session of 2026-10-23 on branch `claude/r61-r33-trial-shape-formatter`: R61 with R33, plugin 1.0.29 (wave 2, lane A)

**Builds on:**
- `docs/handoffs/sessions/2026-10-23-claude-r44-r59-i5.md` (#344, `d72de6a`), the newest on `main`, and `2026-10-23-claude-r51-r25-concurrent-spend.md` (#343), the parallel wave-1 file it carries;
- the files those two carry, not re-read here: the `ccr-b2d02bf7-9ywgjn` files, `2026-10-23-claude-note-58-merge-deny.md`, `2026-10-23-ccr-fc4dc248-6pmtbd-end.md` and `2026-10-23-claude-r65-part-5-handoff.md`;
- `2026-10-23-ccr-b2d02bf7-9ywgjn-handoff.md` (#346, `d80981a`), a parallel file that reached `main` during this session and was merged into this branch; its open items are carried below.

No other session file reached `main` since (verified, `git ls-tree origin/main docs/handoffs/sessions/` after `git fetch origin`, read at 10:40 UTC on `d80981a`). Lane B of wave 2 (R29 part 1 with R54, branch `claude/r29-r54-quick-intent`) runs in parallel; its session file is not on `main`.

## Where the project stands
- **Framework `main` is at `d80981a`** (#346), on plugin **1.0.27** (verified, `git log -1 origin/main` and `.claude-plugin/plugin.json` after `git fetch`, read at 10:40 UTC). #345 and #347 are the owner's two settings rows of choice 261 (`.claude/settings.json`, `template/.claude/settings.json`), and #346 is the `ccr-b2d02bf7-9ywgjn` session's fifth file (`HANDOFF.md`'s two lines); all three merged during this session. The root pin at 1.0.17 is carried, not re-verified.
- **This PR** builds R61 with R33 as plugin **1.0.29**, with `main` merged in at `f0e50f7`. Its record is `docs/progress/2026-10-23-claude-r61-r33-trial-shape-formatter.md`.
- **Lane B's branch** holds 1.0.28 (`python tasks.py next-free`, read on `f0e50f7`). It merges after this PR and renumbers above 1.0.29.
- **Open PRs**: #173 (intent 0004), carried, not re-verified; this PR; lane B's, once opened.

## Preconditions of the moment
- The standing ones are in `HANDOFF.md`.
- **Merge order:** this PR first (R61 precedes R29 and R54 in ROADMAP's Order column). Then lane B merges `main` in, re-bumps above 1.0.29 and regenerates any generated index that conflicts. Both lanes touch `plugin/ci/run_phase.py`.

## Next steps, in order
1. **This PR**: the owner answers its four points in "What I need from you" and merges it when `Framework checks` is green on its final head, the Windows job included (the `.cmd` shim test).
2. **Lane B's PR** (R29 part 1 with R54), after this one.
3. **The small lane, one PR each** (carried from `2026-10-23-ccr-b2d02bf7-9ywgjn-handoff.md`, step 3): R21's first part; R65's part 6; the forged release ref (choice 261, point 2); the documentation PR that decides the names before R45.
4. The rest of the queue in ROADMAP's Order column. The real-project trial now has R61's five parts and R33's formatter.
5. Carried, not re-verified: R51's check 8 and check 11's record half, R25's weekly ceiling at part 3, R65's part 6, the template candidate (choice 253, point 7), the sample's four live facts and its pin, this repository's move from pin 1.0.17 at R14's turn, and the Gemini items at R8's turn (choice 256).

## Every open item
| Item | Where | What is left | Who acts | Blocks 1.0.0 |
|---|---|---|---|---|
| This PR | framework | Green checks, the four points, the owner's merge | owner | no |
| The `sdlc.yaml` row | this PR's record, "Proposed edits for the owner" | `hooks.format_on_edit` becomes `formatters: []` at the move from pin 1.0.17 | owner | no |
| R61's and R33's live checks | this PR's record, "Verified" | `sandbox.allowed_domains` and the Bash timeout in a CI session, on the trial project | a session | no |
| R33's open items | `docs/proposals/formatter-per-language.md`, "Order" | Full Rust support; the quarantine runbook for Node and Rust | a session | no |
| The small lane's four PRs | `2026-10-23-ccr-b2d02bf7-9ywgjn-handoff.md`, next steps, item 3 | One PR each, the forged release ref (choice 261, point 2) among them | a session | no |
| The `/proc` read and the setup step's reach | choice 261, point 1 | With I6, after the trial (carried) | a session | no |
| The probe branches | `claude/r51-ghref-probe`, `claude/r51-ghref-probe2` on `origin` | Delete them (carried; still on `origin`, `git branch -r`) | owner | no |
| Everything else carried | `2026-10-23-ccr-b2d02bf7-9ywgjn-handoff.md`, `2026-10-23-claude-r44-r59-i5.md` and `2026-10-23-claude-r51-r25-concurrent-spend.md`, "Every open item" | Carried, not re-verified | as there | no |

Done, dropped:
- "The two settings rows" (the lane-B wave-1 file): applied by the owner in #345 and #347.
- "This PR" of both wave-1 files: #343 and #344 merged (`ebb3467`, `d72de6a`).
- "Lane B's PR" (the lane-A wave-1 file's step 2): merged as #344.

## What the owner does
| When | Act |
|---|---|
| Now | Answer the four points in this PR's "What I need from you", then merge it when `Framework checks` is green on its final head. |
| After this PR | Merge lane B's PR once it has merged `main` in and its checks are green. |
| At the move from pin 1.0.17 | The `sdlc.yaml` row in this PR's record. |
| Any time | Delete the two probe branches (carried). |
