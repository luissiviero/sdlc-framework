# Session of 2026-10-24 on branch `ccr-545fcec0-ik69zj`, wave 4's end: the second central session closes wave 4's lanes

**Builds on:**
- `docs/handoffs/sessions/2026-10-23-ccr-545fcec0-ik69zj-wave-4.md`, this session's wave 4 file (#374), and `2026-10-23-ccr-545fcec0-ik69zj-end.md`, its wave 3 end file (#373);
- the wave 4 lanes' files, each on `main`: `2026-10-23-claude-r26-measures-change-a-decision.md` (#375), `2026-10-23-claude-r14-prepare-0004-pin-move.md` (#376), `2026-10-24-claude-version-check-plugin-change-bump.md` (#377) and `2026-10-24-claude-version-check-plugin-change-bump-handoff-rows.md` (#379). Their open items are carried by reference, not re-verified, but for the rows named below.

## Where the project stands
- **Framework `main` is at `f9a3f7e`** (#379), on plugin **1.0.39**, tagged `v1.0.39` on #375's merge `db47dbb` (verified, `git log -1 origin/main`, `git rev-list -n1 v1.0.39` after `git fetch origin`). This repository's pin is **1.0.38** (`sdlc.yaml`, the owner's rows in #376).
- **Wave 4's PRs are merged:** #374 (`a43f27c`, choice 269), #375 (`db47dbb`, R26, 1.0.39), #376 (`954414b`, the pin move), #173 (`bcda497`, change 0004's intent), #377 (`f2bb754`, choice 270), #378 (`f39fa65`, change 0004's gate (b)) and #379 (`f9a3f7e`, choice 271). `python tasks.py version-check` exits 0 on `main`.
- **Change 0004 (R14) is in phase (c):** its build run started 2026-10-24 14:56 UTC (run 40104741215). Its spend so far is 50.21 USD: the design run 34.93, the two fix rounds at (b) 8.72 and 6.56 (`changes/0004-drive-target-and-proof-items/evidence/spend.json` on `main`).
- **Lanes:** wave 4's lanes A (`session_01LQcku3xihdbRu5idmX8gpd`) and B (`session_01GMeUbY1Qeij4EVopiNaN8q`) are archived; the small lane (`session_0121RgbuXNXpG8Tv8m5yK7YM`) writes the ROADMAP row change 0004's design drafted (the owner's word of 2026-10-24), then is archived.
- **The check:** `trig_01Y1ziXWCgBi4s2qGxKAnPH2`, hourly, now follows change 0004's runs and the small lane's PR.

## What the wave taught
- **A pin move is also a move across the plugin's preconditions.** Moving this repository from 1.0.17 to 1.0.38 made the project's GitHub App required (R22, plugin 1.0.18); lane B's ten-item list for R14's turn did not name it, nor did this session, and the first design run stopped before it started (run 40029078478, attempt 1). The owner installed the automation App on this repository and set `SDLC_APP_ID` and `SDLC_APP_PRIVATE_KEY`; attempt 2 ran.
- **A fresh-context review of spec and plan before gate (b) paid twice.** Each review found points the panel had not: the first, six (one a gap a removed drive opened); the second, six more (two of them mechanisms the plan left unnamed, `run_phase.py:3503` and `checks.py:463-466`). Each fix round took about 20 minutes.
- **A design run longer than 50 minutes publishes with the workflow token.** #378 was opened by `github-actions[bot]` after the 61-minute design session; its Framework checks then waited at `action_required` for the owner's approval. The fix rounds, shorter, pushed as the App.

## Corrections to other files
- `2026-10-23-ccr-545fcec0-ik69zj-end.md`, "What the wave taught", fourth bullet: #358 did bump, to 1.0.32, the version #355 took first, so it was a version taken twice, not a change with no bump; only the owner's #369 was a change with no bump (the small lane's finding, in `docs/progress/2026-10-24-claude-version-check-plugin-change-bump.md`).
- The same file, "Every open item", the row "A plugin or template change with no bump": done, #377 (choice 270).

## Preconditions of the moment
- The standing ones are in `HANDOFF.md` (as #379 corrected it); the central session's in `docs/handoffs/central-session.md`.

## Next steps, in order
1. **This PR**: the owner merges it when `Framework checks` is green.
2. **Change 0004's build (c)**: at its gate or park, a fresh-context check that the six points of the owner's second gate (b) review are in the code, and that the build bumps the plugin (`version-check`, choice 270).
3. **The small lane's ROADMAP row PR**, then the lane is archived.
4. **Wave 5 (R45)** once change 0004 merges (`waves.md`).

## Every open item
| Item | Where | What is left | Who acts | Blocks 1.0.0 |
|---|---|---|---|---|
| This PR | framework | Green checks, the owner's merge | owner | no |
| Change 0004, phases (c) to (e) | PR on `sdlc/0004/c` once the run opens it | The build's gate, the owner's gates | the runner; owner | no |
| The live checks for change 0004 at (d) and (e) | this file | A Node and Playwright project's `/sdlc-init` proposal and setup minutes; a (c) run with a drive (`drive.log`, the manifest, `proof` judged on the approved plan, the image caps); the (d) record's deferred `evidence` re-judged by the runner; a red drive or a differing item starting one round; an emptied `commands.drive` parking with `drive_removed`; `drive_timeout: 900` capped at 600 at (c) and (d); a drive exiting 127 re-run once with `proof/` cleared; `collect.py` by hand on Windows; the stale-proof line after R51's merge at (e); real job minutes against 200, 260 and 355 | the runner; owner | no |
| The ROADMAP row change 0004's design drafted | `changes/0004-drive-target-and-proof-items/evidence/fix-response.md:131` | The small lane's documentation PR | the small lane; owner | no |
| The owner-machine managed settings | `docs/owner-machine/managed-settings.json` | Copy it again if installed; the reminder fires 2026-10-26 | owner | no |
| R18's live checks | `2026-10-23-claude-r18-failed-run-explains-itself.md` | The refs half is seen live: run 40029078478 wrote `refs/sdlc/failed-runs/40029078478-1` (`git ls-remote origin 'refs/sdlc/failed-runs/*'`); the triage session itself and the `always()` step after a timeout remain | the runner | no |
| Everything the files above list open | their "Every open item" | Carried, not re-verified | as there | no |

Done, dropped: "R26" and "R14's preparation" (this session's wave 4 file): #375, and #376 with #173. "The lanes' effort level": set. "A plugin or template change with no bump" (the wave 3 end file): #377.

## What the owner does
| When | Act |
|---|---|
| Now | Merge this PR when it is green. |
| At change 0004's gate (c) or park | Its review, with the central session's check. |
| 2026-10-26 | The managed settings copy (the reminder). |
