# Session of 2026-10-22 on branch `claude/r65-part-2-choices-index`, end: R65's parts 1 (#324) and 2 (this PR)

**Builds on:**
- `docs/handoffs/sessions/2026-10-22-claude-r65-part-1-next-free.md`, this session's first file, in #324 (open; read on its branch at `c87725b`);
- `2026-10-22-claude-sources-of-truth-study-csl6nq-end.md` (#323, merged as `50eea3b`), the newest file on `main`, which the first file builds on.

No other session file reached `main` since (verified, `git ls-tree origin/main docs/handoffs/sessions/` after `git fetch`, `main` at `50eea3b`).

## Where the project stands
- **Framework `main` is at `50eea3b`** (#323), on plugin **1.0.23** (verified, `git log -1 origin/main` after `git fetch`). The tag `v1.0.23` and the root pin at 1.0.17 are carried from the first file, not re-verified.
- **#324** (R65's part 1: `python tasks.py next-free`, docs-lint check 10) is open, a draft, with `main` merged in at `c87725b`.
- **This PR** (R65's part 2: `python tasks.py choices-index`, `docs/progress/choices.md`) is built on #324's branch and holds its commits until #324 merges.
- **Open PRs**, read after #323 merged: #324, #173 (intent 0004), and this PR. The sample's #55 is carried, not re-verified.

## Preconditions of the moment
- The standing ones are in `HANDOFF.md`.
- **Next free numbers:** `python tasks.py next-free`, once #324 merges. On `50eea3b` it printed choice 253, candidate R66, note 58, decision 39 and patch 1.0.24, none taken above `main`.
- **A PR that edits a record runs `python tasks.py choices-index`**, once this PR merges: docs-lint fails a stale `docs/progress/choices.md`.

## Next steps, in order
1. **#324**, then **this PR**: the owner merges each when `Framework checks` is green on its final head, #324 first.
2. **R65's parts 3 to 5**, one session PR each, in the row's order. Part 4 waits for the owner's guardrail rows 1 to 3. Part 5 makes `HANDOFF.md`'s skeleton point to `python tasks.py next-free`, and may name `choices.md` as where "choice N" is found.
3. **The queue** in ROADMAP's Order column, from R51 with R25, one build session at a time. R65's part 6 comes after R51 merges, in a patch of its own (carried).
4. **At the sample's next change**, read the four live facts the newest file on `main` lists into a note (carried, not re-verified).
5. **This repository's own move from pin 1.0.17** at R14's turn (#173; carried).

## Every open item
| Item | Where | What is left | Who acts | Blocks 1.0.0 |
|---|---|---|---|---|
| #324 | framework | Green checks, the owner's merge | this session; owner | no |
| This PR | framework | #324 first; green checks, the owner's merge | this session; owner | no |
| R65's parts 3 to 5 | ROADMAP R65; `docs/proposals/one-owner-per-fact.md` | One session PR each | the next sessions | no |
| R65's part 6 | ROADMAP R65 | A plugin patch of its own after R51 merges (choice 252) | the session after R51 | no |
| R65's row annotation | `docs/ROADMAP.md`, R65 | One annotation when part 5 merges (recommended in this PR's record) | the part-5 session | no |
| The guardrail rows of choice 252 | `docs/progress/2026-10-22-sources-of-truth-study-r65-choice-252.md`, "Proposed edits for the owner" | Row 5 now; rows 1 to 3 before part 4; row 4 optional; row 6 with the pin move | owner | no |
| Everything else the newest file on `main` carries | `2026-10-22-claude-sources-of-truth-study-csl6nq-end.md`, "Every open item" | Carried, not re-verified | as there | no |

Done, dropped:
- "#323" (the first file, before its correction on #324's branch): merged as `50eea3b`.
- "R65's part 2" (the first file's next step 2): this PR, once merged.

## What the owner does
| When | Act |
|---|---|
| Now | Merge #324 when `Framework checks` is green on its final head. |
| After #324 | Merge this PR when `Framework checks` is green on its final head. |
| Now, any time | The sample's `sdlc.yaml:39` (row 5 of choice 252's record; carried). |
| Before R65's part 4 | Rows 1 to 3 of choice 252's record, in one PR (carried). |
