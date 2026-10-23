# Session of 2026-10-19 on branch `claude/llm-wiki-sdlc-framework-g10zr0`: the LLM wiki pattern, ROADMAP R55 to R57, choices 236 and 237, R55 built

**Builds on:**
- `docs/handoffs/sessions/2026-10-19-ccr-6281cac2-hdaob7.md` (the live proof, part 2, PR #244), which builds on every other session file of 2026-10-19;
- `docs/handoffs/sessions/2026-10-19-ccr-dc6617ae-y5l3n6.md` as its session updated it in PR #245 (choice 235, item 6), which ran in parallel and merged while this file's PR was open.

The first was read on `main` at `2a2a9b2`, the second on `main` at `7626c92`, when this PR merged `main` (verified, `ls docs/handoffs/sessions/`). The parallel session `ccr-eb707371-rh6z2g` (choice 235's second step) has written no session file yet; its state is read from its record, `docs/progress/2026-10-19-framework-checks-faster-part-3-fixture-repositories.md`, on `main` at `ed38636`.

The owner's task: read the artifact "LLM Wiki Crosswalk" (https://claude.ai/artifact/CM4NBjyjRWTQ9tBb9dszP4), research further, and assess what of the LLM wiki pattern to implement in the framework and in the projects it drives; then check the timing and the overlaps with the roadmap; then write the accepted rows. After #247 merged: whether the PRs it lined up clash with the rest of ROADMAP (choice 237), then R55.

## Where the project stands
- **`main` is at `ed38636`** (#248 merged: item 3 of choice 235, the fixture repositories built once per session; before it #247: ROADMAP R55 to R57 and choice 236, `docs/progress/2026-10-19-llm-wiki-roadmap-r55-r57-and-choice-236.md`; before it #246 and #245, item 6 of choice 235); plugin 1.0.12 (verified, `.claude-plugin/plugin.json`); tags and the sample's pin at 1.0.12 carried from `2026-10-19-ccr-6281cac2-hdaob7.md`, not re-verified.
- **This session's second PR** builds R55 (`python tasks.py docs-lint`, `python tasks.py decisions-index`, `docs/links-baseline.txt`, `tests/test_docs_lint.py`) and records choice 237 (`docs/PROGRESS.md`). This repository's tasks, tests and docs only; no version.
- **Open PRs:** framework #173 and this PR; sample #55, #56, #57 (verified, the pulls API, 2026-10-19).

## Preconditions of the moment
- The standing ones are in `HANDOFF.md`.
- R56 is a plugin version: it waits for choice 235's second step (its own version bump) and the sample's next change, so neither has the version move under it.
- Before writing a ROADMAP row number, check it is still free (R55 to R57 were free at `2a2a9b2`).
- `python tasks.py docs-lint` is green on every PR (its layer-2 test runs in `Framework checks`): a new note names its Claude Code version, a new link resolves, a decision's title change is followed by `python tasks.py decisions-index`.

## Next steps, in order
1. **The owner merges this PR (R55).**
2. **R47's missing push:** the owner checks GitHub mobile's notification settings for review requests on the sample. Carried from `2026-10-19-ccr-6281cac2-hdaob7.md`, not re-verified.
3. **The rest of choice 235's second step**, in session `ccr-eb707371-rh6z2g`: item 5 as plugin 1.0.13 (items 6 and 3 merged, #245 and #248). Carried from its record, not re-verified.
4. **The next sample change**, change 0016 in session `ccr-6280ef4b-qilh53` per #248's record: the fast lane on 1.0.11, R47 on a draft build PR and a second request, and by chance the 1.0.10 paths. Carried, not re-verified.
5. **R56**, after steps 3 and 4; its lesson field's name is settled in its own PR (choice 237).
6. **A decision for the owner, not built:** "park at once on findings no session can fix" (NOTES §49), weighed beside R57 and decided on its own (choice 236). Carried from the same file.
7. Carried, not re-verified: the runs PR and the sandbox proof, then the ROADMAP candidates in its Order column from rank 7; #173 at R14's turn (choice 211).

## Every open item
| Item | Where | What is left | Who acts | Blocks 1.0.0 |
|---|---|---|---|---|
| This PR (R55) | framework | The merge | owner | no |
| The baseline's R2 line | `docs/links-baseline.txt` | Removed in the PR that creates `.claude/hooks/ensure_pdf_tools.py`; the lint names it | R2's session | no |
| The artifact "LLM Wiki Crosswalk" | claude.ai | Keeps its stale placement (R50 to R53, ranks before choice 234); superseded by this PR's rows | owner, if wanted | no |
| Choice 235, second step | `docs/progress/2026-10-19-framework-checks-faster-part-3-fixture-repositories.md`, "Left" | Item 5, the git lookups in `plugin/state/gitops.py` as plugin 1.0.13 (that session's next PR), and the stand-in for one test's 25 requests; items 6 and 3 are done (#245, #248). The sample's pin stays at 1.0.12 until change 0016 (session `ccr-6280ef4b-qilh53`) is finished. Carried from that record, not re-verified | session `ccr-eb707371-rh6z2g` | no |
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
- "This session's second PR (item 6)" of `2026-10-19-ccr-dc6617ae-y5l3n6.md`: merged as #245, its record as #246 (`7626c92`).
- "This documentation PR" (choice 236): merged as #247 (`e280caa`).
- "R55's broken links" and "Notes without a Claude Code version": choice 237; the links in kept records are the baseline, the notes are reported, not filled in.

## What the owner does
| When | Act |
|---|---|
| Now | Merge this PR (R55) once `Framework checks` is green on its final head. |
| When convenient | Check that GitHub mobile notifies you of review requests on `luissiviero/sdlc-sample-python`; decide the "park at once" candidate (carried). |
| When `v1.0.13` is tagged | Move the sample's pin after change 0016 finishes (the parallel session's row, carried). |
| The next sample change | Open its intent PR from your account, not as a draft, if it should take the fast lane on 1.0.11 (carried). |
| 2026-10-21 | On the PC: `git pull`, then `python -m pip install -e ".[dev]"` (carried). |
