# Session of 2026-10-23 on branch `claude/r61-r33-trial-shape-formatter`, second file: choice 265, plugin 1.0.32

**Builds on:**
- `docs/handoffs/sessions/2026-10-23-claude-r61-r33-trial-shape-formatter.md`, this session's first file, merged with #350 (`4e122da`);
- the files that reached `main` after it, each read here: `2026-10-23-claude-r29-r54-quick-intent.md` (#348), `2026-10-23-ccr-9171b99a-q6u17y.md` (#354), `2026-10-23-claude-forged-release-ref.md` (#349) and `2026-10-23-claude-r44-r59-i5-proof.md` (#351, `cb602e5`, the newest on `main`);
- `2026-10-23-ccr-b2d02bf7-9ywgjn-end.md` (#352), the first central session's end file, which those carry.

No other session file reached `main` since (verified, `git diff --name-only 4e122da origin/main -- docs/handoffs/sessions` after `git fetch origin`, read at 13:05 UTC on `cb602e5`).

## Where the project stands
- **Framework `main` is at `cb602e5`** (#351), on plugin **1.0.31** (verified, `git show origin/main:.claude-plugin/plugin.json`, read at 13:05 UTC). Wave 2 is merged: #350 (lane A, 1.0.29), #348 (lane B, 1.0.30) and #349 (the small lane's forged release ref, 1.0.31). #351 (case 0007, R44's live proof) and #354 (R66, choice 264) merged too. The root pin at 1.0.17 is carried, not re-verified.
- **This PR** (#355) registers choice 265 (the owner's answers to #350's four points) and builds its point 3 as plugin **1.0.32**, with `main` merged in at `cb602e5`. Its record is `docs/progress/2026-10-23-claude-r61-r33-trial-shape-formatter-four-points.md`.

## Preconditions of the moment
- The standing ones are in `HANDOFF.md`; a central session coordinates the lanes (`docs/handoffs/central-session.md`, choice 262).
- **Numbers:** this PR takes choice 265 and plugin 1.0.32, after `main` was merged in at `cb602e5` (#348, #349, #351 and #354 merged first; `python tasks.py next-free`). Choice 265 is also held on `claude/r66-follow-up`; the choices on `main` run without a gap, so whichever merges second renumbers.

## Next steps, in order
1. **This PR**: the owner merges it when `Framework checks` is green on its final head.
2. **The small lane's next PRs**: R21's first part, now that #350 is in, then R65's part 6 (carried from `2026-10-23-claude-forged-release-ref.md`).
3. **The questions of `2026-10-23-ccr-9171b99a-q6u17y.md`** that wait for the owner (the review's questions 3 to 5), and its documentation follow-ups (carried, not re-verified).
4. The rest as those files list it (carried, not re-verified): the names decision (decision 39); the trial after wave 5; a quick intent live on the sample once its pin is past 1.0.30; the fix workflow's setup step live at the sample's next change; this repository's move from pin 1.0.17 at R14's turn; the Gemini items at R8's turn (choice 256).

## Every open item
| Item | Where | What is left | Who acts | Blocks 1.0.0 |
|---|---|---|---|---|
| This PR | framework | Green checks, the owner's merge | owner | no |
| Choice 265 taken twice | this PR and `claude/r66-follow-up` | The PR that merges second renumbers its choice | the later session | no |
| The `sdlc.yaml` row | `docs/progress/2026-10-23-claude-r61-r33-trial-shape-formatter.md`, "Proposed edits for the owner" | `hooks.format_on_edit` becomes `formatters: []` at the move from pin 1.0.17 | owner | no |
| R61's and R33's live checks | the same record, "Verified" | `sandbox.allowed_domains` and the Bash timeout in a CI session, on the trial project | a session | no |
| R33's open items | `docs/proposals/formatter-per-language.md`, "Order" | Full Rust support; the quarantine runbook for Node and Rust | a session | no |
| `status.yaml`'s `released_*` fields as owner-only fields | `2026-10-23-claude-forged-release-ref.md`, "Every open item" | The owner's answer, then a small PR (carried) | owner; a session | no |
| Everything else carried | the "Every open item" tables of `2026-10-23-ccr-9171b99a-q6u17y.md`, `2026-10-23-claude-forged-release-ref.md`, `2026-10-23-claude-r29-r54-quick-intent.md`, `2026-10-23-claude-r44-r59-i5-proof.md` and `2026-10-23-ccr-b2d02bf7-9ywgjn-end.md` | Carried, not re-verified, but for the rows dropped below | as there | no |

Done, dropped:
- "This PR" of the first file (#350): merged as `4e122da`. "#350's four points": answered, choice 265.
- "#348, #350, #349, #351" (the central session's end file): all four merged (`cb602e5`). "Choice 263 taken twice" (the lane B file): #348 kept 263 and #354 took 264.
- **Correction to the first file:** its row "The probe branches" (the owner deletes them) is done; the central session's end file records them deleted (`git ls-remote` lists none).

## What the owner does
| When | Act |
|---|---|
| Now | Merge this PR when `Framework checks` is green on its final head. |
| When you choose | The questions the files above carry (the parallelism review's 3 to 5, `released_*`, the names table). |
| At the move from pin 1.0.17 | The `sdlc.yaml` row in the first record. |
