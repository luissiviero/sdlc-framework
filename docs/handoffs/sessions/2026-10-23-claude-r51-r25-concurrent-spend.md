# Session of 2026-10-23 on branch `claude/r51-r25-concurrent-spend`: R51 with R25 parts 1-2 (plugin 1.0.26), lane A of the parallel build sessions

**Builds on:**
- `docs/handoffs/sessions/2026-10-23-ccr-b2d02bf7-9ywgjn-status.md`, merged with #342 (`1d89cf1`), the newest on `main`;
- the files it carries: `2026-10-23-ccr-b2d02bf7-9ywgjn-r5.md`, `2026-10-23-claude-note-58-merge-deny.md`, `2026-10-23-ccr-fc4dc248-6pmtbd-end.md` and `2026-10-23-claude-r65-part-5-handoff.md`, with the `-records` and first files of `ccr-b2d02bf7-9ywgjn` that the `-r5` file carries.

No other session file reached `main` since (verified, `ls docs/handoffs/sessions/` after `git fetch origin`, read at 04:35 UTC on `1d89cf1`). Lane B (R44 with R59 and R3's I5, branch `claude/r44-r59-i5`) runs in parallel; its session file is not on `main`.

## Where the project stands
- **Framework `main` is at `1d89cf1`** (#342, a merged change reads "merged at gate (e)" on `main`), on plugin **1.0.25**; the tag `v1.0.25` exists on `origin` (verified, `git fetch origin`, `git log -1 origin/main`, read at 04:35 UTC). The root pin at 1.0.17 is carried, not re-verified.
- **This PR** builds R51 and R25 parts 1-2 as plugin **1.0.26**, re-bumped after #342 took 1.0.25. Its record, `docs/progress/2026-10-23-claude-r51-r25-concurrent-spend.md`, lists what was built, what was not, the independent review's findings and the owner's answers to its four questions (choice 260). R51's two GitHub facts are NOTES §59.
- **Note 59 is taken twice**: by this PR and by lane B's branch (`python tasks.py next-free`, read at 04:35 UTC). This PR merges first, so lane B takes the number `next-free` gives when it merges `main` in.
- **Open PRs**, read at 04:35 UTC on `1d89cf1`: #173 (intent 0004) and, once opened, this PR.

## Preconditions of the moment
- The standing ones are in `HANDOFF.md`.
- **Merge order:** this PR first, since choice 238 places R44 after R51 and R25 parts 1-2; lane B merges `main` in after it. Both touch `plugin/ci/run_phase.py`, and lane B bumps above this PR's version (`python tasks.py version-check` refuses a clash).
- **Numbers:** run `python tasks.py next-free` before taking one. This PR takes note 59.

## Next steps, in order
1. **This PR**: the owner merges it when `Framework checks` is green on its final head. The owner answered its four questions as recommended (choice 260).
2. **Lane B's PR** (R44 with R59 and R3's I5): it merges `main` in after this PR, re-bumps past 1.0.26, and regenerates any generated index that conflicts.
3. **R51's remaining checks**, if the owner wants them: check 8 (the (e) offer withdrawn on a later push) and the other half of check 11 (a release records every change its tip holds). Both are in this PR's record, "Not built".
4. **R25's weekly ceiling**: at part 3 (choice 260, #1).
5. **R65's part 6** after R51, in a patch of its own (choice 252; carried).
6. The rest as the files this one builds on list it (carried, not re-verified): the template candidate for the merge-tool deny rule, the sample's four live facts and its pin, this repository's own move from pin 1.0.17 at R14's turn, and the Gemini items at R8's turn.

## Every open item
| Item | Where | What is left | Who acts | Blocks 1.0.0 |
|---|---|---|---|---|
| This PR | framework | Green checks, the owner's merge | owner | no |
| The probe branches | `claude/r51-ghref-probe`, `claude/r51-ghref-probe2` on `origin` (NOTES §59) | Delete them; the session's proxy refused it | owner | no |
| R51 check 8 and check 11's record half | this PR's record, "Not built" | A PR of their own, if wanted | a session | no |
| R25's weekly ceiling | ROADMAP R25, part 3 (choice 260, #1) | With part 3, after the trial | a session | no |
| `HANDOFF.md`'s two lines | `docs/progress/2026-10-23-ccr-b2d02bf7-9ywgjn-r5.md`, "Left" | One PR of its own (carried) | a session | no |
| R5's tag-workflow red | ROADMAP R5 | With the row (carried) | a session at R5's turn | no |
| The template candidate | choice 253, point 7 | A ROADMAP row and a proposal (carried) | a session | no |
| The sample's stale branch | choice 253, point 9 | `ccr-76f1ceba-idf2w0`, not verified from here (carried) | owner | no |
| The speed suggestions | `docs/progress/2026-10-23-choices-257-258.md`, "Not decided" | The owner's answer on the rest (carried) | owner | no |
| The Gemini session's items | `2026-10-23-ccr-fc4dc248-6pmtbd-end.md`, "Every open item" | Carried, not re-verified; at R8's turn (choice 256) | as there | no |
| Everything the part-5 file lists open | `2026-10-23-claude-r65-part-5-handoff.md`, "Every open item" | Carried, not re-verified | as there | no |

Done, dropped:
- "Decision 11's amendment" and the four questions of this PR: answered as recommended (choice 260); decision 11 carries a dated note.
- "This PR" of the `-r5` file (#341): merged as `f090652`; "This PR" of the `-status` file (#342): merged as `1d89cf1`, tagged `v1.0.25`.
- "Lanes A and B" of the `-status` file: lane A is this PR; lane B is next steps, item 2.
- "The parallel build sessions, on the owner's word" (the `-r5` file's step 2): started by the owner on 2026-10-23; this session is lane A.
- "The merge-tool deny rule: a session checks live that it binds" (the `-r5` file's step 4): done in note 58 (#338), as the note-58 file says.

## What the owner does
| When | Act |
|---|---|
| Now | Merge this PR when `Framework checks` is green on its final head. |
| Any time | Delete the two probe branches. |
| After this PR | Merge lane B's PR once it has merged `main` in and its checks are green. |
