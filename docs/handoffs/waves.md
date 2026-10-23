# The waves — the parallel build plan

Only the central session edits this page, in a documentation PR of its own, when a wave starts or closes (`docs/handoffs/central-session.md`; choice 262). The candidates follow ROADMAP's Order column, which is the owner's; this page groups them into waves of two build lanes and a small lane, paired by the files their proposals name. The rows after the running wave are a plan, re-checked against the code when each wave starts.

Written 2026-10-23 from the plan the first central session gave the owner (session `ccr-b2d02bf7-9ywgjn`). It keeps choice 238's order, with the real-project trial after R45; if the owner brings the trial forward, waves 3 and 4 move after it.

## Before the trial
| Wave | Lane A | Lane B | Small lane | Files both build lanes touch | State |
|---|---|---|---|---|---|
| 1 | R51 + R25 parts 1-2 | R44 + R59 + R3's I5 | `HANDOFF.md`'s two lines | `plugin/ci/run_phase.py` | **Merged:** #343 (1.0.26), #344 (1.0.27), #346; the follow-up #351 (eval case 0007, R44's live proof) open |
| 2 | R61 + R33 | R29 part 1 + R54 | the forged release ref (choice 261); R21 part 1 after lane A; R65 part 6 after both | `plugin/ci/run_phase.py`, `plugin/gate/checks.py`, `plugin/skills/coding-standards/SKILL.md` | **Running:** #350 (lane A, 1.0.29), #348 (lane B, 1.0.28), #349 (small lane, 1.0.29) |
| 3 | R18 | R27, then R64 | the names decision (decision 39), once the owner accepts the name table | none in the proposals | planned; R64 needs R61 and R27 merged |
| 4 | R26 | R14 | — | `plugin/gate/checks.py`, `plugin/pr/description.py` | planned; R14's turn also moves this repository off pin 1.0.17 (#173) |
| 5 | R45, alone | — | — | — | planned; it renames across the code, and it is the last change before the trial |
| — | **The real-project trial** | | | | the build lanes pause; only fixes the trial finds |

## After the trial
| Wave | Lane A | Lane B | Shared files | Note |
|---|---|---|---|---|
| 6 | R28 | R5, then R6 | none / one | R28 is judged against the trial's spend and speed (choice 257) |
| 7 | R11 | R36 | one | |
| 8 | R12 + R13 | R30 | one | R12 and R13 need R11 |
| 9 | R19 + R21's rest | R9 part 1 *(pulled forward)* | none | R19 needs R14 |
| 10 | R20 | R16 *(pulled forward)* | none | R20 needs R18 and R19 |
| 11 | R23 | R35 *(pulled forward)* | none | |
| 12 | R15's second change | R43 | two | |
| 13 | R34 | R32 | four | the tightest pair: lane A merges first |
| 14 | R31 | R37 | two | |
| 15 | R40 | R38 *(pulled forward)* | none | |
| 16 | R41 | R42 | two | R42 reads R40's ref |
| 17 | R39, alone | — | — | |
| 18 | Gemini: Parts 2 and 3, the API terms | R62, reassessed | — | choice 256: last |

*Pulled forward* marks a small item moved up to fill a lane. It changes the owner's order, so it waits for the owner's word, as `central-session.md` says.

## Built when their condition holds, not in a wave
- **R52**, after R50's trigger (20 changes past gate (e) on the trial project) and R26's measures.
- **R57**, after the trial and R45; the owner ranks it from the trial's measures.
- **R25 parts 3-5**, after the trial, from its spend.
- **R56**, after the sample's next change.
- **R3** stays unplaced; **R53** is measured, with no build.
