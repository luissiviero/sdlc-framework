# Session of 2026-10-20 on branch `ccr-7ef35daa-7adzh8`, its end: change 0017 opened and read for R7, NOTES §53 and §54, docs-lint check 8, the citation rule

**Builds on:**
- `docs/handoffs/sessions/2026-10-20-ccr-7ef35daa-7adzh8.md`, this session's own first file (PR #269), kept as written.
- `docs/handoffs/sessions/2026-10-20-ccr-8913e578-kwfegl.md` (decisions 35 and 36, PRs #279 to #281), the newest other file on `main` at `f2b1522`, which builds on the first.

No other session file is newer (verified, `ls docs/handoffs/sessions/` on `main` at `f2b1522`). Two sessions have open drafts that wrote no file on `main` yet: #275 (R60's studies, session `ccr-d901d09c-s87xed`) and #283 (docs-lint check 9, choice 243).

This file closes the session because its context grew too large. What it did after its first file:
- **#273**: choice 240 (R61 accepted, after R44 and before R18); NOTES §53 (the sample's `main` has a ruleset with *Restrict updates*, ruleset 24078926).
- **#276**: docs-lint check 8 (merge claims against the merge commits, choice 241), then the fix after its first CI run (git's "Z" times on Python 3.10, the page order on Windows); R62 proposed (a citation reader on Gemini, sharing R8's key).
- **#278**: `HANDOFF.md`'s citation rule (choice 241).
- **#284** (open): NOTES §54, R7's first live reading, and this file.
- The sample's change 0017, below.

## Where the project stands
- **Framework `main` is at `f2b1522`** (verified, `git log -1 origin/main`), plugin **1.0.14**, `v1.0.14` on `53f9714` (carried from the first file; nothing under `plugin/`, `template/` or `.claude-plugin/` changed since, verified with `git diff v1.0.14 origin/main` on those paths at the first file and not re-run here). The root pin is 1.0.14 (#271). Decisions 35 and 36 are on `main` (#279, #280); choice 242 is the newest record in `docs/PROGRESS.md`.
- **The sample's `main` is at `ce2e855`** (verified): plugin pin 1.0.14, and `claude_code: "2.1.304"` since the owner's sample PR #87 (it was 2.1.278).
- **Change 0017** ("name the part in percent's zero-whole error"), opened by this session at the owner's word:
  - Intent PR sample #85 was opened from the owner's account at 06:14 UTC with the owner's approval of the text ("0017 intent: approved", "open it"); the fast lane started the design run and closed #85 as `sdlc:superseded`.
  - The design run (sample run 39379201252, CLI 2.1.278) parked gate (b) on two items: an open flagged concern (the intent's Constraints said `tests/test_calc.py` would not change, which this session wrote in error: 0015's test asserts the old message) and `reviewer_model` (the reviewer's `claude-opus-5-5` was `unrecognized_model` on 2.1.278 and ran on Fable).
  - The owner raised the sample's CLI pin to 2.1.304 (#87) and commented `@claude ` on sample #86 with no text. The fix round (sample run 39407985040, CLI 2.1.304) ran the reviewer and the advocate on `claude-opus-5-5`; the panel closed the concern ("the Proposed outcome wins": one assertion of `tests/test_calc.py` changes); the reviewer classed the plan non-routine, so gate (b) waits for the owner (decision 30).
  - The owner **approved** sample #86 at 10:35 UTC but has **not merged** it (verified, the PR at 11:20 UTC: open, `sdlc:b-ready`). Gate (b) is the merge; the approving review is the gate only at (e) and only once R22 is built (decision 36).
  - Spend to gate (b): 15.25 USD (`spend.json` on `sdlc/0017/b` at `2e5db02`).
- **Open framework PRs:** #284 (this session's; CI green, run 39409743794), #283 (another session's, check 9), #275 (R60, draft), #173 (intent 0004, waits for R14's turn, choice 211). #284 merges cleanly with #283 and with #275 (verified, `git merge-tree`).

## Preconditions of the moment
- The standing ones are in `HANDOFF.md`, including the citation rule of choice 241.
- The next free decision file is 37, the next free note 55 once #284 merges, the next free candidate R63. The next free patch number is 1.0.15 (R56's, choice 184, carried).

## Next steps, in order
1. **The owner merges sample #86** (gate (b)). The build (c) and test (d) runs then start on their own; the next stop for the owner is gate (e), a review request on the build PR.
2. **The owner merges #284** (NOTES §54, CI green).
3. **Read 0017's phases (c) to (e) for R7** when they end: the session on `claude-opus-5-5`, the advocate on `claude-fable-5-1`, the reviewer at each gate, the spend. Record it as a note (55) or an annotation of §54, and add the change's row to the tally in `docs/proposals/reviewer-on-opus.md` (the external review's retirement count starts with 0017).
4. **The owner decides the template's CLI default** (NOTES §54, "What this means beyond the sample"): `template/sdlc.yaml` sets `session_model` and `adversarial_model` to `claude-opus-5-5`, while `/sdlc-init` pins `DEFAULT_CLAUDE_CODE_VERSION = "2.1.278"`, which does not know that id for a sub-agent. A new project would park at every gate. A candidate of its own, or a part of R61; it blocks the real-project trial. A plugin change, so it takes a version.
5. **The next ranked build is R24 (rank 8)**, now that decision 35 is merged, then R22 (rank 9) on decision 36, then R51 with R25 parts 1-2 (ranks 10 and 11). One build session at a time: each bumps the plugin version and most touch the same files.
6. **The owner decides** what the first file and the 8913e578 file list as still open (below).
7. Then the ROADMAP candidates, in its Order column; #173 at R14's turn.

## Every open item
| Item | Where | What is left | Who acts | Blocks 1.0.0 |
|---|---|---|---|---|
| Sample #86, gate (b) of 0017 | the sample | The owner's merge (an approval is not the gate at (b)) | owner | no |
| #284 | framework | The owner's merge | owner | no |
| 0017's phases (c) to (e) | the sample; NOTES §54, "Not read yet" | Read for R7, record, tally | the next session | no |
| The template's CLI default | NOTES §54; `plugin/init/sdlc_init.py`, `template/sdlc.yaml` | The owner's decision on the fix and its place | owner | no |
| The decisions audit's questions | `docs/reviews/2026-10-20-findings-cross-reference.md` | Decisions 5, 1, 29, 16 and 3, and the five reason-changed ones (4 is answered by NOTES §53; 11's text by choice 242, point 3) | owner | no |
| R59 and the registered additions | ROADMAP R59, R5, R21, R23, R25, R31, R33, R43, R44, R45, R51 | The owner's decisions (carried) | owner | no |
| R62 and R8 | ROADMAP R62, R8 | Their places, and the key tier's terms (carried) | owner | no |
| A full docs sweep before the trial | choice 241 | Recommended, not decided (carried) | owner | no |
| R30 before the trial?; "park at once"; the runs PR's open items; R21's first part before the trial | the first file; ROADMAP R30, R21 | The owner's calls (carried) | owner | no |
| R45's names | `docs/reviews/2026-10-20-names-against-the-article.md` (#265) | The owner decides the rows, then the names decision file before R45 | owner | no |
| #283, #275 | framework | Other sessions' drafts; not read in full by this session | their sessions; owner | no |
| The sandbox proof's error text; the template sandbox block; coverage gaps 2, 4 and 5; R47's push and its two settings; the fast-lane "What needs you" line (R54); the trial readiness review's smaller findings; the Cowork artifact's comment; the R7 leftovers and the rest of the e4e43fa6 list | as in the 8913e578 file | Carried unchanged, not re-verified | as there | no |
| The reminder for the PC | `trig_01WqkM8vJPR1LB3JnVkJkTvx` | Fires 2026-10-24 at 11:55 UTC into this session (`session_01EdkDo7FWNERXD5ZcgZTqXV`); if that session is archived, the next session re-arms it into itself and deletes this one | the next session; owner acts | no |

Done, dropped:
- "#280": merged as `c15dd35`; its questions answered as choice 242 (8913e578 file).
- "The `CLAUDE.md` decision count": the owner dropped the count (#282).
- "The sample's CLI pin" (the fix for 0017's first park): the owner's sample PR #87.
- "R7's first live reading on 1.0.14": started with 0017; the session and the reviewer readings are in NOTES §54; phases (c) to (e) stay above.

## What the owner does
| When | Act |
|---|---|
| Now | Merge sample #86 (gate (b) of change 0017). |
| Now | Merge #284 (NOTES §54 and this file). |
| When convenient | Decide the template's CLI default (step 4) and the open items above. |
| At 0017's gate (e) | Read the build PR and merge it, or comment `@claude` with the change request. |
| 2026-10-24 | On the PC: `git pull`, then `python -m pip install -e ".[dev]"`. |
