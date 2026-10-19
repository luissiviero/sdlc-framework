# Session of 2026-10-19 on branch `claude/llm-wiki-sdlc-framework-g10zr0`: the LLM wiki pattern, ROADMAP R55 to R57, choice 236

**Builds on:**
- `docs/handoffs/sessions/2026-10-19-ccr-6281cac2-hdaob7.md` (the live proof, part 2, PR #244), which builds on every other session file of 2026-10-19.

No other session file is newer than it or missing from its header (verified, `ls docs/handoffs/sessions/` on `main` at `2a2a9b2`).

The owner's task: read the artifact "LLM Wiki Crosswalk" (https://claude.ai/artifact/CM4NBjyjRWTQ9tBb9dszP4), research further, and assess what of the LLM wiki pattern to implement in the framework and in the projects it drives; then check the timing and the overlaps with the roadmap; then write the accepted rows.

## Where the project stands
- **`main` is at `2a2a9b2`** (#244 merged after #243); plugin 1.0.12 (verified, `.claude-plugin/plugin.json`); tags and the sample's pin at 1.0.12 carried from `2026-10-19-ccr-6281cac2-hdaob7.md`, not re-verified.
- **This session's PR** adds ROADMAP R55 to R57, annotates R2, R42 and R45, and writes `docs/proposals/llm-wiki-adoption.md` and the owner's choice 236 (`docs/PROGRESS.md`). Documentation only; no version.
- **Open PRs:** framework #173 and this documentation PR; sample #55, #56, #57 (verified, the pulls API, 2026-10-19).

## Preconditions of the moment
- The standing ones are in `HANDOFF.md`.
- R56 is a plugin version: it waits for choice 235's second step (its own version bump) and the sample's next change, so neither has the version move under it.
- Before writing a ROADMAP row number, check it is still free (R55 to R57 were free at `2a2a9b2`).

## Next steps, in order
1. **The owner merges this documentation PR.**
2. **R55, the docs lint**, as a documentation and tasks PR (no plugin version); it can run beside step 4 below, since it adds a task and its own tests and changes no fixture.
3. **R47's missing push:** the owner checks GitHub mobile's notification settings for review requests on the sample. Carried from `2026-10-19-ccr-6281cac2-hdaob7.md`, not re-verified.
4. **The second step of choice 235**, when the owner says "Go" in a new session. Carried from the same file, not re-verified.
5. **The next sample change**: the fast lane on 1.0.11, R47 on a draft build PR and a second request, and by chance the 1.0.10 paths. Carried from the same file, not re-verified.
6. **R56**, after steps 4 and 5.
7. **A decision for the owner, not built:** "park at once on findings no session can fix" (NOTES §49), weighed beside R57 and decided on its own (choice 236). Carried from the same file.
8. Carried, not re-verified: the runs PR and the sandbox proof, then the ROADMAP candidates in its Order column from rank 7; #173 at R14's turn (choice 211).

## Every open item
| Item | Where | What is left | Who acts | Blocks 1.0.0 |
|---|---|---|---|---|
| This documentation PR | framework | The merge | owner | no |
| R55's broken links | `docs/` (43 of 367 at `209325f`) | Fixed in R55's clean-up, then the lint fails on a new one | R55's session | no |
| Notes without a Claude Code version | `docs/notes/` 12 and 43 to 49 | Filled in, or marked "no Claude Code fact", once R55 lists them | a notes session | no |
| The artifact "LLM Wiki Crosswalk" | claude.ai | Keeps its stale placement (R50 to R53, ranks before choice 234); superseded by this PR's rows | owner, if wanted | no |
| Choice 235, second step | `docs/progress/2026-10-19-framework-checks-faster-and-choice-235.md`, "Left" | Carried from `2026-10-19-ccr-6281cac2-hdaob7.md`, not re-verified | owner says "Go"; a new session | no |
| R47's push to the owner; on a draft PR; a remove-then-request pair | NOTES §49 | Carried from the same file, not re-verified | owner; a later session | no |
| Fix rounds spent on findings no session can fix | NOTES §49 | The owner's call on the candidate (park at once) | owner | no |
| R49's `/proc` claim; the App's own PRs | NOTES §48 | Carried from the same file, not re-verified | a later session | no |
| The 1.0.10 paths; the fast lane on 1.0.11 | NOTES §49 | Carried from the same file, not re-verified | the next sample change | no |
| The intent PR's summary cuts a long open question | `docs/progress/2026-10-19-live-proof-part-1-1.0.12.md`, "Left" | A nit for later; carried | a later change | no |
| R50's trigger | ROADMAP R50 | Carried, not re-verified | a later session | no |
| 1.0.11's, 1.0.10's, R47's, R48's, R49's, R17's and R46's known limits | their `docs/progress/` records, "Left" | Carried unchanged from `2026-10-19-ccr-6281cac2-hdaob7.md` | a later change | no |
| Fork token of an `issue_comment` run | NOTES §46 | Carried: needs a second account | a session with one | no |
| Gap 8's second half | `.github/workflows/sdlc-tag.yml` | Carried: the tag waits for `Framework checks` (R5) | R5's session | no |
| "Small defects" and "E2"; R28's timing and cost; R44's timing | `2026-10-15-ccr-01de3f80-ilnomi.md` line 20; ROADMAP | Carried unchanged (choices 209, 213) | owner | no |
| The reminder for the PC | `trig_01Dbv76g2tPAEdw1wPC6b4Gf`, of session `ccr-d96dbb91-v12amc` | Fires 2026-10-21 11:55 UTC: `git pull`, then `python -m pip install -e ".[dev]"`; carried, not re-verified | that session delivers; owner acts | no |
| R10 not verified live; R10's two parts left out by its review; the rest of the d96dbb91 table | as there | Carried unchanged | as there | no |

Done, dropped:
- "This documentation PR" of `2026-10-19-ccr-6281cac2-hdaob7.md`: merged as #244 (`2a2a9b2`).

## What the owner does
| When | Act |
|---|---|
| Now | Merge this documentation PR once `Framework checks` is green on its final head. |
| When convenient | Check that GitHub mobile notifies you of review requests on `luissiviero/sdlc-sample-python`; decide the "park at once" candidate (carried). |
| When you choose | Say "Go" for R55 and for the second step of choice 235, each in a session. |
| The next sample change | Open its intent PR from your account, not as a draft, if it should take the fast lane on 1.0.11 (carried). |
| 2026-10-21 | On the PC: `git pull`, then `python -m pip install -e ".[dev]"` (carried). |
