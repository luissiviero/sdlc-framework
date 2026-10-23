# Session of 2026-10-22 on branch `claude/r65-part-4-verify`, end: R65's parts 1 to 4 (#324, #325, #327, this PR)

**Builds on:**
- `docs/handoffs/sessions/2026-10-22-claude-r65-part-3-checks-11-12.md`, this session's third file (#327, merged as `8bca5fd`), the newest on `main`;
- `2026-10-22-ccr-6ed8a82e-cxmftx-end.md` (#326), which that file read and carries.

No other session file reached `main` since (verified, `git ls-tree origin/main docs/handoffs/sessions/` after `git fetch`, `main` at `8bca5fd`).

## Where the project stands
- **Framework `main` is at `8bca5fd`** (#327), on plugin **1.0.23** (verified, `git log -1 origin/main` after `git fetch`). The tag `v1.0.23` and the root pin at 1.0.17 are carried, not re-verified.
- **On `main` from this session:**
  - R65's parts 1 to 3: `next-free`, check 10, `choices-index`, checks 11 and 12;
  - choices 253 and 254.
- **This PR** builds R65's part 4: `python tasks.py verify`, check 13 and CI on `verify`. It takes no number.
- **Open PRs**, read at 23:51 UTC: #173 (intent 0004), the owner's #328 (the merge-tool deny rule, row 5 of choice 253's record) and this PR. The sample's #55 is carried, not re-verified.

## Preconditions of the moment
- The standing ones are in `HANDOFF.md`.
- **Next free numbers:** run `python tasks.py next-free` before taking one.
- **The local checks:** `python tasks.py verify` runs `sdlc.yaml`'s build, lint and test commands, the docs lint and `claude plugin validate .`. Until the owner's row 3, add `python -m compileall -q .github/scripts` by hand, as `HANDOFF.md`'s precondition 1 asks.
- **Check 11 reads session files dated from 2026-10-23 on:** no rank, and no next free number written by hand.

## Next steps, in order
1. **This PR**: the owner merges it when `Framework checks` is green on its final head.
2. **The owner's rows 1 to 4** of this PR's record, in one PR. Check 13 then holds `CLAUDE.md:54` and `sdlc.yaml:21` together.
3. **R65's part 5**: `HANDOFF.md`'s skeleton points to `python tasks.py next-free`, and its precondition 1 to `python tasks.py verify` (choice 252, point 7). The same PR annotates R65's row once (choice 253, point 13).
4. **The merge-tool deny rule**: once the owner's #328 merges, a session checks live that it binds. Then the template candidate, or the gap recorded as a known limit (choice 253, point 7).
5. **The Gemini session**, once R65's parts 1 to 5 have merged and before part 6 (the owner, carried from the `ccr-6ed8a82e-cxmftx` end file, not re-verified).
6. **The queue** in ROADMAP's Order column, from R51 with R25. R65's part 6 comes after R51, in a patch of its own (carried).
7. **At the sample's next change**:
   - the four live facts go into a note (carried);
   - the sample's `sdlc.yaml:39` and its pin move (choice 253, point 8).
8. **This repository's own move from pin 1.0.17** at R14's turn (#173; carried).

## Every open item
| Item | Where | What is left | Who acts | Blocks 1.0.0 |
|---|---|---|---|---|
| This PR | framework | Green checks, the owner's merge | this session; owner | no |
| The owner's rows 1 to 4 | this PR's record, "Proposed edits for the owner" | One PR after this one | owner | no |
| R65's part 5 | ROADMAP R65; `HANDOFF.md` | One PR of its own | the next session | no |
| R65's part 6 | ROADMAP R65 | A plugin patch of its own after R51 merges (choice 252) | the session after R51 | no |
| The merge-tool deny rule | #328; choice 253, point 7 | The owner's merge, then a live check | owner; a session | no |
| The sample's stale branch | choice 253, point 9 | `ccr-76f1ceba-idf2w0`, not verified from here | owner | no |
| The Gemini session's items | `2026-10-22-ccr-6ed8a82e-cxmftx-end.md`, "Every open item" | Carried, not re-verified | as there | no |
| Everything else carried | `2026-10-22-claude-sources-of-truth-study-csl6nq-end.md`, "Every open item" | Carried, not re-verified | as there | no |

Done, dropped:
- "This PR" of the third file (#327): merged as `8bca5fd`.
- "R65's part 4" (the third file's next step 2): this PR, once merged.

## What the owner does
| When | Act |
|---|---|
| Now | Merge this PR when `Framework checks` is green on its final head; merge #328. |
| After this PR merges | Rows 1 to 4 of this PR's record, in one PR. |
| Once R65's parts 1 to 5 have merged | Start the Gemini session with the prompt in session `ccr-6ed8a82e-cxmftx`'s chat (carried). |
| At the sample's next upgrade | The sample's `sdlc.yaml:39` and its pin move (carried). |
