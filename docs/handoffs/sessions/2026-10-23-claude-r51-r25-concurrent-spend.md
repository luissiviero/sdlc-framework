# Session of 2026-10-23 on branch `claude/r51-r25-concurrent-spend`: R51 with R25 parts 1-2 (plugin 1.0.25), lane A of the parallel build sessions

**Builds on:**
- `docs/handoffs/sessions/2026-10-23-ccr-b2d02bf7-9ywgjn-r5.md`, merged with #341 (`f090652`), the newest on `main`;
- the files it carries: `2026-10-23-ccr-b2d02bf7-9ywgjn-records.md`, `2026-10-23-ccr-b2d02bf7-9ywgjn.md`, `2026-10-23-ccr-fc4dc248-6pmtbd-end.md` and `2026-10-23-claude-r65-part-5-handoff.md`;
- `2026-10-23-claude-note-58-merge-deny.md` (#338), which the newest file's header does not name: a session that ran in parallel with it.

No other session file reached `main` since (verified, `ls docs/handoffs/sessions/` after `git fetch origin`, read at 03:40 UTC on `f090652`). Lane B's session (R44 with R59 and R3's I5) runs in parallel and had added no file when this one was written.

## Where the project stands
- **Framework `main` is at `f090652`** (#341, R5's version check), on plugin **1.0.24** (verified, `git log -1 origin/main`, `.claude-plugin/plugin.json`, read at 03:40 UTC). The root pin at 1.0.17 is carried, not re-verified.
- **This PR** builds R51 and R25 parts 1-2 as plugin **1.0.25**. Its record, `docs/progress/2026-10-23-claude-r51-r25-concurrent-spend.md`, lists what was built, what was not, and the owner's four questions. R51's two GitHub facts are NOTES §59.
- **Open PRs**, read at 03:40 UTC on `f090652`: #173 (intent 0004) and, once opened, this PR. Lane B's PR is not open yet.

## Preconditions of the moment
- The standing ones are in `HANDOFF.md`.
- **Merge order (choice 238):** this PR first; lane B merges `main` in after it. Both touch `plugin/ci/run_phase.py`, and lane B's version takes the next free patch after 1.0.25 (`python tasks.py version-check` refuses a clash).
- **Numbers:** run `python tasks.py next-free` before taking one. This PR takes note 59 and patch 1.0.25.

## Next steps, in order
1. **This PR**: the owner answers the four questions in its record, then merges it when `Framework checks` is green on its final head.
2. **Lane B's PR** (R44 with R59 and R3's I5): it merges `main` in after this PR, re-bumps past 1.0.25, and regenerates any generated index that conflicts.
3. **R51's remaining checks**, if the owner wants them: check 8 (the (e) offer withdrawn on a later push) and the other half of check 11 (a release records every change its tip holds). Both are in this PR's record, "Not built".
4. **R25's weekly ceiling**: at part 3, or sooner if the owner answers question 1 so.
5. **R65's part 6** after R51, in a patch of its own (choice 252; carried).
6. The rest as the files this one builds on list it (carried, not re-verified): the template candidate for the merge-tool deny rule, the sample's four live facts and its pin, this repository's own move from pin 1.0.17 at R14's turn, and the Gemini items at R8's turn.

## Every open item
| Item | Where | What is left | Who acts | Blocks 1.0.0 |
|---|---|---|---|---|
| This PR | framework | The four answers, green checks, the owner's merge | owner | no |
| The probe branches | `claude/r51-ghref-probe`, `claude/r51-ghref-probe2` on `origin` (NOTES §59) | Delete them; the session's proxy refused it | owner | no |
| R51 check 8 and check 11's record half | this PR's record, "Not built" | A PR of their own, if wanted | a session | no |
| R25's weekly ceiling | this PR's record, question 1 | The owner's answer; then part 3 | owner, then a session | no |
| Decision 11's amendment file | this PR's record, question 3 | The owner's answer | owner | no |
| `HANDOFF.md`'s two lines | `docs/progress/2026-10-23-ccr-b2d02bf7-9ywgjn-r5.md`, "Left" | One PR of its own (carried) | a session | no |
| R5's tag-workflow red | ROADMAP R5 | With the row (carried) | a session at R5's turn | no |
| The template candidate | choice 253, point 7 | A ROADMAP row and a proposal (carried) | a session | no |
| The sample's stale branch | choice 253, point 9 | `ccr-76f1ceba-idf2w0`, not verified from here (carried) | owner | no |
| The speed suggestions | `docs/progress/2026-10-23-choices-257-258.md`, "Not decided" | The owner's answer on the rest (carried) | owner | no |
| The Gemini session's items | `2026-10-23-ccr-fc4dc248-6pmtbd-end.md`, "Every open item" | Carried, not re-verified; at R8's turn (choice 256) | as there | no |
| Everything the part-5 file lists open | `2026-10-23-claude-r65-part-5-handoff.md`, "Every open item" | Carried, not re-verified | as there | no |

Done, dropped:
- "This PR" of the `-r5` file (#341): merged as `f090652`.
- "The parallel build sessions, on the owner's word" (the `-r5` file's step 2): started by the owner on 2026-10-23; this session is lane A.
- "The merge-tool deny rule: a session checks live that it binds" (the `-r5` file's step 4): done in note 58 (#338), as the note-58 file says.

## What the owner does
| When | Act |
|---|---|
| Now | Answer the four questions in this PR's record ("What I need from you"), then merge it when `Framework checks` is green on its final head. |
| Any time | Delete the two probe branches. |
| After this PR | Merge lane B's PR once it has merged `main` in and its checks are green. |
