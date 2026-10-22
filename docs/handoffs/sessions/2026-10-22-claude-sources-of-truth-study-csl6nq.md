# Session of 2026-10-22 on branch `claude/sources-of-truth-study-csl6nq`: the study of the sources of truth; ROADMAP R65 accepted (choice 252)

**Builds on:**
- `docs/handoffs/sessions/2026-10-22-ccr-76f1ceba-idf2w0.md` (on `main`, #321), the newest file;
- `2026-10-22-ccr-3fe1c65e-erwrby-end.md` (#320), which #321's file builds on.

No other session file is newer (verified, `git ls-tree origin/main docs/handoffs/sessions/` after `git fetch`, read at 21:13 UTC).

## Where the project stands
- **Framework `main` is at `0d229a6`** (#321), on plugin **1.0.23**, tag `v1.0.23` on `0d229a6`. Verified at 21:13 UTC with `git log -1 origin/main` and `git ls-remote --tags origin v1.0.23`. The root pin stays at 1.0.17 (`sdlc.yaml:104`; choice 249, point 2).
- **The rulesets** follow choice 251, Option C, on both repositories: the owner Exempt in ruleset 1, plus a no-direct-writes ruleset. The facts are NOTES §57. Read by session `ccr-76f1ceba-idf2w0`, not by this one.
- **The sample's `main` is at `28fba16`**, on pin 1.0.22 (verified, `git log -1 origin/main` and its `sdlc.yaml:88`).
- **Open PRs**, read at 21:13 UTC:
  - framework: this session's PR (#322) and #173 (intent 0004);
  - sample: #55.
- **This session's PR (documentation only):**
  - the study `docs/reviews/2026-10-22-sources-of-truth.md`: the inventory, the owner table, and the drift (39 stale places on `84c50a0` in 17 rows; 33 left after #321);
  - the proposal `docs/proposals/one-owner-per-fact.md`;
  - ROADMAP R65, accepted as recommended (choice 252, recorded in `docs/PROGRESS.md`).

## Preconditions of the moment
- The standing ones are in `HANDOFF.md`.
- **Next free numbers**, read at 21:13 UTC on `main` (`0d229a6`) and every branch ahead of it, this PR included: choice 253, candidate R66, note 58, decision 39, patch 1.0.24. This is the last session file that writes them by hand, if R65's part 1 lands before the next session ends (choice 252, point 2).

## Next steps, in order
1. **This PR:** the owner merges it when `Framework checks` is green on its final head.
2. **R65's parts 1 to 5**, one session PR each, outside the ranks, in the row's order:
   1. `tasks.py next-free` with check 10;
   2. `tasks.py choices-index`;
   3. checks 11 and 12, with the `README.md` and manifest fixes S1 to S4;
   4. `tasks.py verify` with check 13, after the owner's guardrail rows 1 to 3;
   5. `HANDOFF.md`'s skeleton.

   Part 6 is a plugin patch of its own after R51 merges, never inside R51's PR (choice 252).
3. **At the sample's next change**, read each of these into a note (carried from #321's file):
   - decision 36's live checks at (e);
   - R8's first second opinion at (b);
   - the digest's reading of the `sdlc-merge` environment;
   - whether the phone's tap merges a red build PR that ruleset 2 holds.
4. **This repository's own move from pin 1.0.17** (carried): its own automation App, then the `sdlc.yaml` rows, at R14's turn (#173).
5. **Then the queue** in ROADMAP's Order column, from R51 with R25, one build session at a time.

## Every open item
| Item | Where | What is left | Who acts | Blocks 1.0.0 |
|---|---|---|---|---|
| This PR | framework | Green checks, the owner's merge | this session; owner | no |
| R65's parts 1 to 5 | ROADMAP R65; `docs/proposals/one-owner-per-fact.md` | Built as session PRs, outside the ranks | the next sessions | no |
| R65's part 6 | ROADMAP R65 | A plugin patch of its own after R51 merges, at the next free patch number then (choice 252) | the session after R51 | no |
| The guardrail rows of choice 252 | `docs/PROGRESS.md`, "Proposed edits for the owner" | Rows 1 to 3 before part 4; row 4 optional; row 5 (the sample's `sdlc.yaml:39`) now; row 6 with the pin move | owner | no |
| The study's stale places not fixed by #321 | `docs/reviews/2026-10-22-sources-of-truth.md`, section 3 | 33 places, fixed by R65's parts, the next plugin patch and the owner's rows | sessions; owner | no |
| The phone's tap on a red build PR that ruleset 2 holds | the sample | Not verified (carried from #321's file) | the next session, at the sample's next red build PR | no |
| A session's API merge as the owner | both repositories | No setup stops it (NOTES §57); only the session's instructions do. A ROADMAP candidate if the owner wants one (carried) | owner | no |
| The sample's branch `ccr-76f1ceba-idf2w0` | the sample | Holds #101's throwaway file; the owner may delete it (carried) | owner | no |
| Decision 36's live checks; R8's first second opinion; the digest's environment reading; the `sdlc-merge` environment | the sample | At its next change (carried) | the next session | no |
| This repository's App and pin | `sdlc.yaml:104`, `vars.SDLC_APP_ID` | Next step 4 (carried) | owner; then a session | no |
| Everything else the end file of `ccr-3fe1c65e-erwrby` carries | its "Every open item" | Carried, not re-verified | as there | no |

Done, dropped:
- "The owner's study of the sources of truth" (#321's file, next step 2): this PR. R65 was free, and this PR takes it.
- "#321 (1.0.23)": merged as `0d229a6`, tag `v1.0.23`.

## Corrections to earlier files
- `2026-10-22-ccr-3fe1c65e-erwrby-end.md`:
  - lines 7-8 ("Its #318 is open") and line 21 ("Open, framework: #318 … and #173"): #318 merged as `45931cd` at 18:59:34 UTC, before #320 merged at 19:02:22 UTC (verified, `git log --first-parent origin/main`);
  - its "Framework `main` is at `396e4b4`" (line 10) was `45931cd` by then.
- `2026-10-22-ccr-76f1ceba-idf2w0.md`, "Next free numbers: … candidate R65": this PR takes R65, and the next free candidate is R66. Its choice 252 is this PR's, and the next free choice is 253.

## What the owner does
| When | Act |
|---|---|
| Now | Merge this PR when `Framework checks` is green on its final head. |
| Now, any time | Row 5 of `docs/PROGRESS.md`'s table: the sample's `sdlc.yaml:39`. |
| Before R65's part 4 | Rows 1 to 3 of the same table, in one PR. |
| At the sample's next change | Approve the build PR from the phone after gate (e) has run; apply `sdlc:release-approved` (carried). |
| At R14's turn, or earlier | This repository's own automation App, then the `sdlc.yaml` rows (carried). |
