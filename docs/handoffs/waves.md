# The waves — the parallel build plan

Only the central session edits this page, in a documentation PR of its own, when a wave starts or closes (`docs/handoffs/central-session.md`; choice 262). The candidates follow ROADMAP's Order column, which is the owner's; this page groups them into waves of two build lanes and a small lane, paired by the files their proposals name. The rows after the running wave are a plan, re-checked against the code when each wave starts.

Written 2026-10-23 from the plan the first central session gave the owner (session `ccr-b2d02bf7-9ywgjn`). It keeps choice 238's order, with the real-project trial after R45; if the owner brings the trial forward, waves 3 and 4 move after it.

## Before the trial
| Wave | Lane A | Lane B | Small lane | Files both build lanes touch | State |
|---|---|---|---|---|---|
| 1 | R51 + R25 parts 1-2 | R44 + R59 + R3's I5 | `HANDOFF.md`'s two lines | `plugin/ci/run_phase.py` | **Merged:** #343 (1.0.26), #344 (1.0.27), #346, and the follow-up #351 (eval case 0007, R44's live proof, no version) |
| 2 | R61 + R33 | R29 part 1 + R54 | the forged release ref (choice 261); R21 part 1 after lane A; R65 part 6 after both | `plugin/ci/run_phase.py`, `plugin/gate/checks.py`, `plugin/skills/coding-standards/SKILL.md` | **Merged:** #350 (lane A, 1.0.29), #348 (lane B, 1.0.30), #349 (small lane, 1.0.31), #355 (lane A's four points, 1.0.32), #357 (R21 part 1, no version), #358 (R65 part 6, which changed files under `plugin/` and `template/` with `plugin.json` left at #355's 1.0.32, so its lines first shipped in 1.0.33), #359 (part 6's review fixes, 1.0.33) |
| 3 | R18 | R27, then R64 | first `status.yaml`'s `released_*` fields as owner-only fields (choice 268 (d), merged before lanes A and B branch); then the names decision (decision 39: the name table accepted, with the names added since plugin 1.0.14 judged by the same rule; choice 268 (b)) | `plugin/ci/run_phase.py`: R27 names `guardrail_changes` and `ci_settings_file`, R18 runs it from a fresh framework checkout, and the small lane's patch changes `owner_fields` *[2026-10-23, corrected by the second central session (choice 268): was "none in the proposals"; `docs/proposals/policy-sources.md:31` and `docs/proposals/failed-run-explains-itself.md:86` name the file]* | **Merged**, coordinated by the second central session (choice 268 (a)): #362 (choice 268), #363 (small lane, `released_*` owner-only, 1.0.34), #364 and #365 (lane B, decision 40 amending 6 and its review corrections), #366 (small lane, decision 39), #367 (lane B, R27, 1.0.35), the owner's #369 (the template's `Edit(/policies/**)`), #368 (lane A, R18, 1.0.36), #370 (lane B, R64, 1.0.37) and #371 (small lane, the preflight's `Edit(/policies/**)`, 1.0.38) |
| 4 | R26 | R14 | — | `plugin/gate/checks.py`, `plugin/pr/description.py` | planned, re-checked 2026-10-23 at wave 3's close: the proposals still share only these two files, in different places (R26: `description.py` `_counters_line` and `checks.py:1158-1167`; R14: `checks.py` `run_targets` and `description.py:61` and `:195-207`, as the proposals cite them); R14's turn also moves this repository off pin 1.0.17 (#173) |
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
