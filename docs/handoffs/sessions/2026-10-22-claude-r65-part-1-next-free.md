# Session of 2026-10-22 on branch `claude/r65-part-1-next-free`: R65's part 1, `python tasks.py next-free` and docs-lint check 10

**Builds on:**
- `docs/handoffs/sessions/2026-10-22-claude-sources-of-truth-study-csl6nq-end.md`, the newest file, read on its branch (PR #323, open when this session started);
- `2026-10-22-claude-sources-of-truth-study-csl6nq.md` (#322) and `2026-10-22-ccr-76f1ceba-idf2w0.md` (#321), which it names.

No other session file is newer or parallel: the only others of 2026-10-22, `2026-10-22-ccr-3fe1c65e-erwrby.md` and its `-end` file, are the ones #321's file builds on (verified, `ls docs/handoffs/sessions/` on `30b0367` and the header of #321's file).

## Where the project stands
- **Framework `main` is at `30b0367`** (#322), on plugin **1.0.23**, read at the start with `git log -1 origin/main` after `git fetch`. The tag `v1.0.23` and the root pin at 1.0.17 are carried from the newest file, not re-verified.
- **This session's PR** builds R65's part 1: `python tasks.py next-free`, docs-lint check 10, their tests and the record in `docs/PROGRESS.md`. It takes no number and no plugin version.
- **Open PRs**, read at the start of this session on `30b0367`: framework #323 (the previous session's end file), #173 (intent 0004), and this PR. The sample's #55 is carried from the newest file, not re-verified.

## Preconditions of the moment
- The standing ones are in `HANDOFF.md`.
- **Next free numbers:** run `python tasks.py next-free` once this PR merges. Its first live use, on `30b0367` and the four branches ahead of it, printed choice 253, candidate R66, note 58, decision 39 and patch 1.0.24, none taken above `main`.

## Next steps, in order
1. **This PR** (documentation and `tasks.py`): the owner merges it when `Framework checks` is green on its final head. #323 can merge before or after it: they share no file.
2. **R65's parts 2 to 5**, one session PR each, in the row's order. Part 4 waits for the owner's guardrail rows 1 to 3. Part 5 makes `HANDOFF.md`'s skeleton point to `python tasks.py next-free`.
3. **The queue** in ROADMAP's Order column, from R51 with R25, one build session at a time. R65's part 6 comes after R51 merges, in a patch of its own (carried).
4. **At the sample's next change**, read the four live facts the newest file lists into a note (carried from it, not re-verified).
5. **This repository's own move from pin 1.0.17** at R14's turn (#173; carried).

## Every open item
| Item | Where | What is left | Who acts | Blocks 1.0.0 |
|---|---|---|---|---|
| This PR | framework | Green checks, the owner's merge | this session; owner | no |
| #323 | framework | The owner's merge | owner | no |
| R65's parts 2 to 5 | ROADMAP R65; `docs/proposals/one-owner-per-fact.md` | One session PR each | the next sessions | no |
| R65's part 6 | ROADMAP R65 | A plugin patch of its own after R51 merges (choice 252) | the session after R51 | no |
| The guardrail rows of choice 252 | `docs/progress/2026-10-22-sources-of-truth-study-r65-choice-252.md`, "Proposed edits for the owner" | Row 5 now; rows 1 to 3 before part 4; row 4 optional; row 6 with the pin move | owner | no |
| Everything else the newest file carries | `2026-10-22-claude-sources-of-truth-study-csl6nq-end.md`, "Every open item" | Carried, not re-verified | as there | no |

Done, dropped:
- "R65's part 1" (the newest file's next step 2): this PR, once merged.

## What the owner does
| When | Act |
|---|---|
| Now | Merge #323, and this PR when `Framework checks` is green on its final head. |
| Now, any time | The sample's `sdlc.yaml:39` (row 5 of choice 252's record; carried). |
| Before R65's part 4 | Rows 1 to 3 of choice 252's record, in one PR (carried). |
