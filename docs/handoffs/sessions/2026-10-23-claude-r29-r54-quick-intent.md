# Session of 2026-10-23 on branch `claude/r29-r54-quick-intent`: R29 part 1 with R54, plugin 1.0.28 (wave 2, lane B)

**Builds on:**
- `docs/handoffs/sessions/2026-10-23-claude-r44-r59-i5.md` (#344, `d72de6a`) and `2026-10-23-claude-r51-r25-concurrent-spend.md` (#343, `ebb3467`), wave 1's two lanes, the newest on `main`, and the files they carry.

No other session file reached `main` since (verified, `ls docs/handoffs/sessions/` after `git fetch origin`, read at the session's start on `d72de6a`). Lane A of wave 2 (R61 with R33) runs in parallel; its session file is not on `main`.

## Where the project stands
- **Framework `main` is at `d72de6a`** (#344), on plugin **1.0.27** (verified, `git log -1 origin/main` and `.claude-plugin/plugin.json` after `git fetch origin`, read at the session's start).
  Since then the owner merged #345 and #347 (the settings rows, `f0e50f7`, read at 09:29 UTC), merged into this branch. The root pin at 1.0.17 is carried, not re-verified.
- **This PR** (#348) builds R29 part 1 with R54 and choice 239's line as plugin **1.0.28** (its record: `docs/progress/2026-10-23-claude-r29-r54-quick-intent.md`). It takes no choice, note or decision number.
- **Open PRs**: #173 (intent 0004), carried, not re-verified; lane A's PR and this one.

## Preconditions of the moment
- The standing ones are in `HANDOFF.md`.
- **Merge order:** lane A first (R61 precedes R29 and R54 in ROADMAP's Order column). This PR then merges `main` in with a merge commit and re-bumps past lane A's version (`python tasks.py version-check` refuses a clash).

## Next steps, in order
1. **Lane A's PR**, then **this PR**: the owner merges each when `Framework checks` is green on its final head.
2. **The forged release ref** (choice 261, point 2; carried from the R44 file).
3. The rest of the queue in ROADMAP's Order column.
4. **At the sample's next change**: a quick intent on the sample once its pin is past 1.0.28 (this PR's "Not verified live"), with the four live facts, `sdlc.yaml:39` and the pin (carried).
5. **This repository's own move from pin 1.0.17** at R14's turn (#173; carried).
6. **At R8's turn, last in the queue (choice 256)**: the Gemini items (carried).

## Every open item
| Item | Where | What is left | Who acts | Blocks 1.0.0 |
|---|---|---|---|---|
| This PR | framework | Lane A's merge, `main` merged in, green checks, the owner's merge | this session; owner | no |
| A quick intent live | the sample | One change started with `/sdlc-plan quick: ...` once the pin is past 1.0.28 | a session | no |
| R29's later parts | `docs/proposals/intent-home.md`, "Order" | The template override, the claude.ai route, the briefs, the names | sessions, at their ranks | no |
| The forged release ref | choice 261, point 2 | Carried | a session | no |
| The probe branches | `claude/r51-ghref-probe`, `claude/r51-ghref-probe2` | Carried from the R51 file | owner | no |
| Everything else carried | the R44 file's and the R51 file's "Every open item" | Carried, not re-verified | as there | no |

Done, dropped:
- "Lane B's PR" (the R51 file's step 2): #344 merged as `d72de6a`. "This PR" of both wave-1 files: #343 and #344 merged.
- "The two settings rows" (the R44 file): applied by the owner in #345 and #347 (`f0e50f7`, `template/.claude/settings.json` and `.claude/settings.json`, five lines each; verified, `git diff --stat d72de6a origin/main`), merged into this branch.

## What the owner does
| When | Act |
|---|---|
| After lane A's PR | Merge this PR once it has merged `main` in and its checks are green. |
| Any time | As the wave-1 files list it (carried). |
