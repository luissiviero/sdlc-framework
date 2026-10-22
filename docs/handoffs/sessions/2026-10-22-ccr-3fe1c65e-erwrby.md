# Session of 2026-10-22 on branch `ccr-3fe1c65e-erwrby`, part 2: choice 250 and its fixes as plugin 1.0.22

**Builds on:** `docs/handoffs/sessions/2026-10-20-ccr-3fe1c65e-erwrby.md`, this session's first file, merged with #312 (`1f58af2`).

No other session file reached `main` since (verified, `git log --diff-filter=A origin/main -- docs/handoffs/sessions/`). #313 (decision 37, session `ccr-0522ec37-iia2ok`) adds none on its branch (verified, `git diff --name-status`). Its open items are carried from the first file, not re-verified unless a row says so.

## Where the project stands
- **Framework `main` is at `1f58af2`** (#312), on plugin **1.0.20**, tag `v1.0.20` (verified, `git log -1 origin/main`, `git tag`). The root pin stays at 1.0.17 (choice 249, point 2).
- **#313** (decision 37, 1.0.21) is an open draft at `2e5b1d9` (verified, the GitHub PR list).
- **This session's PR:**
  - **What:** choice 250 (the owner's "all as recommended" on the double check's four questions) and its fixes as **1.0.22**: F1 to F5, F8, F9 and F13's tests, with the review's documentation rows. The record is in `docs/PROGRESS.md`.
  - **The base:** the branch is #313's head with `main` merged in. The PR stays a draft until #313 merges and `main` is merged in again.
- **The sample** (`21f1748`, pin 1.0.19): R22's steps A to D done (NOTES §56, #312).

## Preconditions of the moment
- The standing ones are in `HANDOFF.md`.
- **Next free numbers:** choice 251, candidate R65, note 57, decision 39, patch 1.0.23 (1.0.21 is #313's, 1.0.22 this PR's).

## Next steps, in order
1. **#313 (1.0.21)** merges (the owner, when `Framework checks` is green on its final head).
2. **This PR (1.0.22):** merge `main` with #313 in, re-archive #313's final record if it changed, run the checks, leave draft. The owner merges when `Framework checks` is green.
3. **The sample's upgrade to 1.0.22**, after `v1.0.22`. The session opens a sample PR with the workflow copies, `evals/README.md` and the template's changed files. The owner makes the `sdlc.yaml` rows: the pin, and decision 37's rows from `docs/progress/2026-10-22-decision-37-one-profile-1.0.21.md`.
4. **At the sample's next change:** read the following, each into a note:
   - decision 36's live checks at (e);
   - R8's first second opinion at (b);
   - the digest's environment reading (`actions: read`).
5. **Then the queue** in ROADMAP's Order column, from R51 with R25, one build session at a time.

## Every open item
| Item | Where | What is left | Who acts | Blocks 1.0.0 |
|---|---|---|---|---|
| This session's PR | framework | #313's merge, `main` merged in, green checks, the owner's merge | this session; owner | no |
| #313 | framework | `Framework checks` green, the owner's merge | session `ccr-0522ec37-iia2ok`; owner | no |
| The sample's upgrade to 1.0.22 | the sample | After `v1.0.22`; the owner's `sdlc.yaml` rows | this session or the next; owner | no |
| The `sdlc-merge` environment | the sample | Not readable from a session; the first merge run verifies it (NOTES §56) | the next session | no |
| Whether `actions: read` reads the environments API | `sdlc-digest.yml` | The digest's first run on 1.0.22 shows it: a failed lookup says nothing | the next session | no |
| `CLAUDE.md` rows 33 and 34, the root `sdlc.yaml` row 6 | `docs/progress/2026-10-20-r22-gate-e-approving-review-1.0.18.md` | The owner's edits (carried, not re-verified) | owner | no |
| Everything else the first file lists open | `2026-10-20-ccr-3fe1c65e-erwrby.md`, "Every open item" | Carried, not re-verified, except the rows above and the drops below | as there | no |

Done, dropped:
- "The review's questions" (the first file): choice 250, in this PR.
- "F1, F2, F4, F5 and F13" and "D1 to D9, M1 to M4, L4 to L6" (the first file): built and written in this PR.
- "#307's session file": #307 merged (`0a0554d`), and its session wrote none; that is session `ccr-0522ec37-iia2ok`'s to settle.

## What the owner does
| When | Act |
|---|---|
| Now | Merge #313 when `Framework checks` is green on its final head. |
| After #313 | Merge this PR when it leaves draft with `Framework checks` green. |
| After `v1.0.22` | The sample's `sdlc.yaml` rows (pin 1.0.22 and decision 37's rows), then merge the sample's 1.0.22 PR. |
| At the sample's next change | Approve its build PR from the phone after gate (e) has run (an earlier approval no longer counts, choice 250), and apply `sdlc:release-approved`. |
