# Session of 2026-10-22 on branch `claude/r65-part-3-checks-11-12`, end: R65's parts 1 to 3 (#324, #325, this PR)

**Builds on:**
- `docs/handoffs/sessions/2026-10-22-claude-r65-part-2-choices-index.md`, this session's second file (#325, merged as `8e48bcc`), the newest on `main`;
- `2026-10-22-claude-r65-part-1-next-free.md` (#324) and `2026-10-22-claude-sources-of-truth-study-csl6nq-end.md` (#323), which it builds on;
- `2026-10-22-ccr-6ed8a82e-cxmftx-end.md` (#326, merged as `a8d6dba`), a session that ran in parallel and builds on the csl6nq "-end" file.

No other session file reached `main` (verified, `git ls-tree origin/main docs/handoffs/sessions/` after `git fetch`, `main` at `a8d6dba`).

## Where the project stands
- **Framework `main` is at `a8d6dba`** (#326), on plugin **1.0.23** (verified, `git log -1 origin/main` after `git fetch`). The tag `v1.0.23` and the root pin at 1.0.17 are carried, not re-verified.
- **On `main` from this session:**
  - R65's part 1 (#324, `8e8d5c6`): `python tasks.py next-free` and check 10;
  - part 2 (#325, `8e48bcc`): `python tasks.py choices-index`;
  - choice 253, the owner's answer on the sources-of-truth session's nine decisions.
- **This PR** builds R65's part 3: checks 11 and 12, S1 to S4 fixed, and the study annotated.
- **Open PRs**, read after #326 merged: #173 (intent 0004) and this PR (#327). The sample's #55 is carried, not re-verified.

## Preconditions of the moment
- The standing ones are in `HANDOFF.md`.
- **Next free numbers:** run `python tasks.py next-free` before taking one. This PR takes none.
- **From 2026-10-23 on, check 11 reads session files:** name a candidate by its number only, and write no next free number by hand.
- **A PR that edits a record runs `python tasks.py choices-index`.**

## Next steps, in order
1. **This PR**: the owner merges it when `Framework checks` is green on its final head.
2. **R65's part 4**: `python tasks.py verify` and check 13 in one PR, then CI on `verify` (choice 253, points 2 and 4). After it, the owner's rows 1 to 4 of choice 253's record.
3. **R65's part 5**: `HANDOFF.md`'s skeleton points to `python tasks.py next-free` and may name `docs/progress/choices.md` for "choice N". The same PR annotates R65's row once (choice 253, point 13).
4. **The merge-tool deny rule**: once the owner adds row 5 of choice 253's record, a session checks live that it binds. Then a template candidate, or the gap recorded as a known limit (choice 253, point 7).
5. **The Gemini session**, once R65's parts 1 to 5 have merged and before part 6 (the owner, carried from the `ccr-6ed8a82e-cxmftx` end file, not re-verified): its two defects, the (e) job, a first live call, and Gemini in R28's roles. The owner starts it with the prompt in that session's chat.
6. **The queue** in ROADMAP's Order column, from R51 with R25. R65's part 6 comes after R51, as a patch of its own (carried).
7. **At the sample's next change**: the four live facts into a note (carried); row 5 of choice 252's record and the pin move (choice 253, point 8).
8. **This repository's own move from pin 1.0.17** at R14's turn (#173; carried).

## Every open item
| Item | Where | What is left | Who acts | Blocks 1.0.0 |
|---|---|---|---|---|
| This PR | framework | Green checks, the owner's merge | this session; owner | no |
| R65's parts 4 and 5 | ROADMAP R65; `docs/proposals/one-owner-per-fact.md` | One session PR each | the next sessions | no |
| R65's part 6 | ROADMAP R65 | A plugin patch of its own after R51 merges (choice 252) | the session after R51 | no |
| The guardrail rows | `docs/progress/2026-10-22-r65-part-2-choices-index-choice-253.md`, "Proposed edits for the owner" | Row 5 now; rows 1 to 4 after part 4 | owner | no |
| The merge-tool deny rule, live | choice 253, point 7 | A live check after row 5 | a session | no |
| Four stale branches | choice 253, point 9 | Delete them | owner | no |
| `BUILD_GUIDE.md` and check 12; the widened pass words | this PR's record, "Points left open" | The owner's word, or the recommendation stands | owner | no |
| The Gemini session's items | `2026-10-22-ccr-6ed8a82e-cxmftx-end.md`, "Every open item" (the two defects, the (e) job, the first live call, the API terms, Gemini in the x-roles, R8's tally, R62, the port list) | Carried, not re-verified | as there | no |
| Everything else carried | `2026-10-22-claude-sources-of-truth-study-csl6nq-end.md`, "Every open item" | Carried, not re-verified | as there | no |

Done, dropped:
- "This PR" of the second file (#325): merged as `8e48bcc`.
- "R65's parts 3 to 5" becomes "parts 4 and 5": part 3 is this PR.

## What the owner does
| When | Act |
|---|---|
| Now | Merge this PR when `Framework checks` is green on its final head. |
| Now, any time | Row 5 of choice 253's record (the merge-tool deny rule); delete the four branches (choice 253, point 9). |
| After R65's part 4 merges | Rows 1 to 4 of choice 253's record, in one PR. |
| At the sample's next upgrade | The sample's `sdlc.yaml:39` and its pin move (carried). |
| Once R65's parts 1 to 5 have merged | Start the Gemini session with the prompt in session `ccr-6ed8a82e-cxmftx`'s chat (carried). |
