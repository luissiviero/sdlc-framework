# Session of 2026-10-22 on branch `ccr-3fe1c65e-erwrby`, part 2: choice 250 and its fixes as plugin 1.0.22

**Builds on:** `docs/handoffs/sessions/2026-10-20-ccr-3fe1c65e-erwrby.md`, this session's first file, merged with #312 (`1f58af2`).

No other session file reached `main` since (verified, `git log --diff-filter=A origin/main -- docs/handoffs/sessions/` on `1cdb45f`). Two parallel ones are open, read on their branches and not on `main`:
- `2026-10-20-ccr-0522ec37-iia2ok-part-4.md` (#317): decisions 38 and 37 merged; the owner keeps F3's fix for this PR;
- session `ccr-76f1ceba-idf2w0`'s ruleset bypass-mode test (#314 to #316 merged, #318 open), with no session file yet.

The first file's open items are carried, not re-verified unless a row says so.

## Where the project stands
- **Framework `main` is at `1cdb45f`** (#316), on plugin **1.0.21**: #313 (decision 37) merged as `2a782f1` (verified, `git log origin/main`, `.claude-plugin/plugin.json`). The root pin stays at 1.0.17 (choice 249, point 2).
- **Direct writes on `main`.** Session `ccr-76f1ceba-idf2w0` tested ruleset 1's bypass modes on this repository: `7c33f02` and `906317a` are its probes in Exempt, which landed and were removed by #316. See `docs/reviews/2026-10-22-ruleset-bypass-modes.md`.
- **This session's PR:**
  - **What:** choice 250 (the owner's "all as recommended" on the double check's four questions) and its fixes as **1.0.22**: F1 to F5, F8, F9 and F13's tests, with the review's documentation rows. The record is in `docs/PROGRESS.md`.
  - **The base:** the branch was #313's head with `main` merged in; with #313 merged, `main` at `1cdb45f` is merged in (`90f02de`). The PR is open as a draft.
- **The sample** (`21f1748`, pin 1.0.19): R22's steps A to D done (NOTES §56, #312).

## Preconditions of the moment
- The standing ones are in `HANDOFF.md`.
- **Next free numbers:** choice 251, candidate R65, note 57, decision 39, patch 1.0.23 (1.0.21 is #313's, 1.0.22 this PR's).

## Next steps, in order
1. **This PR (1.0.22):** the owner merges it when `Framework checks` is green on its final head.
2. **The sample's ruleset 1 bypass mode:** the owner decides after session `ccr-76f1ceba-idf2w0`'s test. In Exempt a session acting as the owner writes to `main` directly; in "For pull requests only" the phone tap merges (this PR's record, "Left").
3. **The sample's upgrade to 1.0.22**, after `v1.0.22`. The session opens a sample PR with the workflow copies, `evals/README.md` and the template's changed files. The owner makes the `sdlc.yaml` rows: the pin, and decision 37's rows from `docs/progress/2026-10-22-decision-37-one-profile-1.0.21.md`.
4. **At the sample's next change:** read the following, each into a note:
   - decision 36's live checks at (e);
   - R8's first second opinion at (b);
   - the digest's environment reading (`actions: read`).
5. **Then the queue** in ROADMAP's Order column, from R51 with R25, one build session at a time.

## Every open item
| Item | Where | What is left | Who acts | Blocks 1.0.0 |
|---|---|---|---|---|
| This session's PR | framework | Green checks, the owner's merge | this session; owner | no |
| The sample's ruleset 1 bypass mode | the sample, ruleset 24078926 | Exempt since 2026-10-22 (NOTES §56); the bypass-mode test's outcome may move it back | owner | no |
| The sample's upgrade to 1.0.22 | the sample | After `v1.0.22`; the owner's `sdlc.yaml` rows | this session or the next; owner | no |
| The `sdlc-merge` environment | the sample | Not readable from a session; the first merge run verifies it (NOTES §56) | the next session | no |
| Whether `actions: read` reads the environments API | `sdlc-digest.yml` | The digest's first run on 1.0.22 shows it: a failed lookup says nothing | the next session | no |
| `CLAUDE.md` rows 33 and 34, the root `sdlc.yaml` row 6 | `docs/progress/2026-10-20-r22-gate-e-approving-review-1.0.18.md` | The owner's edits (carried, not re-verified) | owner | no |
| Everything else the first file lists open | `2026-10-20-ccr-3fe1c65e-erwrby.md`, "Every open item" | Carried, not re-verified, except the rows above and the drops below | as there | no |

Done, dropped:
- "The review's questions" (the first file): choice 250, in this PR.
- "F1, F2, F4, F5 and F13" and "D1 to D9, M1 to M4, L4 to L6" (the first file): built and written in this PR.
- "#307's session file": #307 merged (`0a0554d`), and its session's part-4 file (#317) covers it.
- "#313" (the first file): merged as `2a782f1`.

## What the owner does
| When | Act |
|---|---|
| Now | Merge this PR when `Framework checks` is green on its final head. |
| After the bypass-mode test | Choose the sample's ruleset 1 bypass mode for the admin role. |
| After `v1.0.22` | The sample's `sdlc.yaml` rows (pin 1.0.22 and decision 37's rows), then merge the sample's 1.0.22 PR. |
| At the sample's next change | Approve its build PR from the phone after gate (e) has run (an earlier approval no longer counts, choice 250), and apply `sdlc:release-approved`. |
