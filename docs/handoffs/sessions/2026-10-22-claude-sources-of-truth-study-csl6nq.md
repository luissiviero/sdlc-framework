# Session of 2026-10-22 on branch `claude/sources-of-truth-study-csl6nq`: the study of the sources of truth (report only), ROADMAP R65 proposed

**Builds on:**
- `docs/handoffs/sessions/2026-10-22-ccr-3fe1c65e-erwrby-end.md` (on `main`, #320), the newest file;
- `2026-10-22-ccr-76f1ceba-idf2w0.md`, open in #321 and read on its branch, not on `main`. It ran in parallel and is not in the end file's header, so its items are carried from it.

No other session file is newer than the end file's header names (verified, `git ls-tree origin/main docs/handoffs/sessions/` after `git fetch`).

## Where the project stands
- **Framework `main` is at `84c50a0`** (#320), on plugin **1.0.22**, tag `v1.0.22` on `cbea66b` (verified, `git log -1 origin/main`, `git rev-parse v1.0.22^{commit}`, read at 19:18 UTC). The root pin stays at 1.0.17 (`sdlc.yaml:104`; choice 249, point 2).
- **The sample's `main` is at `28fba16`**, on pin 1.0.22 (verified, its `sdlc.yaml:88`).
- **Open, framework:**
  - #321, session `ccr-76f1ceba-idf2w0`: choice 251, NOTES §57, 1.0.23;
  - #173, intent 0004;
  - this session's PR.
- **Open, sample:** #55. All read at 19:18 UTC.
- **This session's PR (documentation only):**
  - the study `docs/reviews/2026-10-22-sources-of-truth.md`: the inventory of eleven kinds of fact, the owner table, and the drift count (39 stale places on `main` in 17 rows; 5 of them fixed on #321's branch);
  - the proposal `docs/proposals/one-owner-per-fact.md`;
  - the ROADMAP row R65, proposed, Order blank.

## Preconditions of the moment
- The standing ones are in `HANDOFF.md`.
- **Next free numbers**, read at 19:18 UTC on `main` (`84c50a0`) and every branch ahead of it:
  - choice **252**, note **58** and patch **1.0.24**, since #321 takes choice 251, note 57 and 1.0.23 on its branch (on `main` alone: 251, 57, 1.0.23);
  - candidate **R66**, since this PR takes R65;
  - decision **39**.

## Next steps, in order
1. **The owner sets both rulesets' admin bypass to "For pull requests only", then merges #321** (carried from #321's file, not re-verified).
2. **This PR:** the owner reads the study's section 6 (seven questions) and merges it when `Framework checks` is green on its final head. R65 is a candidate, not a decision.
3. **If R65 is accepted:** its parts in the order of its row, as documentation and `tasks.py` PRs, the last one in the next plugin patch.
4. **At the sample's next change**, read each of these into a note (carried from #321's file and the end file):
   - decision 36's live checks at (e);
   - R8's first second opinion at (b);
   - the digest's reading of the `sdlc-merge` environment;
   - whether the phone's tap merges a build PR that ruleset 2 holds.
5. **This repository's own move from pin 1.0.17** (carried): its own automation App, then the `sdlc.yaml` rows, at R14's turn (#173).
6. **Then the queue** in ROADMAP's Order column, from R51 with R25, one build session at a time.

## Every open item
| Item | Where | What is left | Who acts | Blocks 1.0.0 |
|---|---|---|---|---|
| This PR | framework | Green checks; the owner's answers to section 6; the merge | this session; owner | no |
| R65 | `docs/ROADMAP.md`, its row | The owner's decision (study, section 6, question 1) | owner | no |
| The study's stale places not fixed by #321 | `docs/reviews/2026-10-22-sources-of-truth.md`, section 3: S1 to S8 and S11 to S17 | Fixed by R65's parts, the next plugin patch, or the owner's guardrail rows (section 5) | sessions; owner | no |
| #321 (1.0.23) and the bypass modes of both rulesets 1 | framework; ruleset 24077592, sample ruleset 24078926 | As #321's file says (carried, not re-verified) | owner | no |
| Everything else #321's file carries | `2026-10-22-ccr-76f1ceba-idf2w0.md` on #321's branch, "Every open item" | Carried, not re-verified | as there | no |

Done, dropped:
- "The owner's study of the sources of truth" (the end file, next step 1; #321's file, next step 2): this PR.

## Corrections to earlier files
- `2026-10-22-ccr-3fe1c65e-erwrby-end.md`, lines 7-8 ("Its #318 is open") and line 21 ("Open, framework: #318 … and #173"): #318 merged as `45931cd` at 18:59:34 UTC, before #320 merged at 19:02:22 UTC (verified, `git log --first-parent origin/main`). Its "Framework `main` is at `396e4b4`" (line 10) was `45931cd` by then.
- The same file, line 26: its next free choice 251, note 57 and patch 1.0.23 are right for `main`, and #321 takes all three on its branch.

## What the owner does
| When | Act |
|---|---|
| Now | Set both rulesets' admin bypass and merge #321 (#321's table). |
| Now | Answer the study's section 6, then merge this PR when `Framework checks` is green on its final head. |
| If R65 is accepted | The guardrail rows of the study's section 5, rows 1 to 3 before R65's part 4. Row 5 (the sample's `sdlc.yaml:39`) is due now, whatever R65's fate. |
| At the sample's next change | Approve the build PR from the phone after gate (e) has run; apply `sdlc:release-approved` (carried). |
