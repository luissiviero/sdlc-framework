# Session of 2026-10-22 on branch `claude/sources-of-truth-study-csl6nq`, end: #322 merged; R65's part 1 handed to a new session

**Builds on:**
- `docs/handoffs/sessions/2026-10-22-claude-sources-of-truth-study-csl6nq.md`, this session's first file, merged with #322 (`30b0367`);
- `2026-10-22-ccr-76f1ceba-idf2w0.md` (#321, `0d229a6`), which the first file builds on.

No other session file reached `main` since (verified, `git ls-tree origin/main docs/handoffs/sessions/` at 21:40 UTC).

## Where the project stands
- **Framework `main` is at `30b0367`** (#322), on plugin **1.0.23**, tag `v1.0.23` on `0d229a6`. Verified at 21:40 UTC with `git log -1 origin/main`; the tag was read at 21:13 UTC with `git ls-remote`. The root pin stays at 1.0.17 (`sdlc.yaml:104`; choice 249, point 2).
- **#322 merged**:
  - the study `docs/reviews/2026-10-22-sources-of-truth.md`;
  - R65 accepted (choice 252, `docs/PROGRESS.md`), outside the ranks;
  - part 6 is a plugin patch of its own after R51 merges.
- **No stale copy is fixed yet.** #322 was report-only. The 33 places the study lists after #321 are still on `main` (re-read on `30b0367` with `git grep`, the sample on `28fba16`). Who fixes what:
  - the owner, through the guardrail rows;
  - R65's parts 3 to 5 (documentation and `tasks.py`);
  - R65's part 6 (the plugin patch after R51).
- **The sample's `main` is at `28fba16`**, on pin 1.0.22 (verified, `git log -1 origin/main`).
- **Open PRs**, read at 21:40 UTC:
  - framework: #173 (intent 0004) and this PR;
  - sample: #55.

## Preconditions of the moment
- The standing ones are in `HANDOFF.md`.
- **Next free numbers**, read at 21:40 UTC on `main` (`30b0367`) and every branch ahead of it: choice 253, candidate R66, note 58, decision 39, patch 1.0.24. R65's part 1 replaces this hand-written line with `python tasks.py next-free`.

## Next steps, in order
1. **This PR** (documentation only): the owner merges it when `Framework checks` is green on its final head.
2. **R65's part 1**, in a new session the owner asked this session to start:
   - `python tasks.py next-free`, and docs-lint check 10 (a number taken twice fails);
   - a documentation and `tasks.py` PR with no plugin version.

   The design point to settle in that PR: a naive read of "N. **…**" lines in the progress records finds the numbers 1 to 8 and 16 to 23 twice. These are almost certainly ordinary numbered lists in old records, not choices taken twice; the numbering is otherwise clean (251 distinct numbers up to 252, and no ROADMAP row repeated; verified, `git grep` on `30b0367`). So check 10 reads choices only where a record states them, under its "owner's decision" heading, and reports rather than fails a duplicate in records older than its cutover (choice 126), as check 8 does. Part 1 can run beside R51: they share no file.
3. **R65's parts 2 to 5**, one session PR each, in the row's order. Part 4 waits for the owner's guardrail rows 1 to 3.
4. **The queue** in ROADMAP's Order column, from R51 with R25, one build session at a time. R65's part 6 comes after R51 merges, in a patch of its own.
5. **At the sample's next change**, read each of these into a note (carried):
   - decision 36's live checks at (e);
   - R8's first second opinion at (b);
   - the digest's reading of the `sdlc-merge` environment;
   - whether the phone's tap merges a red build PR that ruleset 2 holds.
6. **This repository's own move from pin 1.0.17** (carried): its own automation App, then the `sdlc.yaml` rows, at R14's turn (#173).

## Every open item
| Item | Where | What is left | Who acts | Blocks 1.0.0 |
|---|---|---|---|---|
| This PR | framework | Green checks, the owner's merge | this session; owner | no |
| R65's parts 1 to 5 | ROADMAP R65; `docs/proposals/one-owner-per-fact.md` | Part 1 in the new session; then parts 2 to 5 | the next sessions | no |
| R65's part 6 | ROADMAP R65 | A plugin patch of its own after R51 merges (choice 252) | the session after R51 | no |
| The guardrail rows of choice 252 | `docs/PROGRESS.md`, "Proposed edits for the owner" | Row 5 (the sample's `sdlc.yaml:39`) now; rows 1 to 3 before part 4; row 4 optional; row 6 with the pin move | owner | no |
| The study's 33 stale places | `docs/reviews/2026-10-22-sources-of-truth.md`, section 3 | Fixed by the rows and parts above | sessions; owner | no |
| Everything else the first file carries | `2026-10-22-claude-sources-of-truth-study-csl6nq.md`, "Every open item" | Carried, not re-verified | as there | no |

Done, dropped:
- "This PR" (the first file): #322, merged as `30b0367`.
- "R65's part 6 and R51" (the first file, before the owner's second answer): settled in choice 252.

## What the owner does
| When | Act |
|---|---|
| Now | Merge this PR when `Framework checks` is green on its final head. |
| Now, any time | The sample's `sdlc.yaml:39`: "owner's merge" becomes "build PR's merge" (row 5). |
| Before R65's part 4 | Rows 1 to 3: `CLAUDE.md:8-11`, `CLAUDE.md:54` and `sdlc.yaml:21`, in one PR. |
| When the part-1 session opens its PR | Review it, and merge it when `Framework checks` is green. |
| At R14's turn, or earlier | This repository's own automation App, then the `sdlc.yaml` rows (carried). |
