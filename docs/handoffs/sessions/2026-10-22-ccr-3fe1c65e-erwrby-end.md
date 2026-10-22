# Session of 2026-10-22 on branch `ccr-3fe1c65e-erwrby`, end: 1.0.22 merged, the sample on 1.0.22, the root `CLAUDE.md` edited

**Builds on:**
- `docs/handoffs/sessions/2026-10-22-ccr-3fe1c65e-erwrby.md`, this session's second file, merged with #319 (`cbea66b`);
- `2026-10-20-ccr-0522ec37-iia2ok-part-4.md` (#317, merged as `e5cf3a5`): the files of the two sessions agree on 1.0.21, 1.0.22 and choice 250.

Session `ccr-76f1ceba-idf2w0`'s ruleset bypass-mode test has no session file yet. Its #318 is open; read on its branch, not on `main`.

## Where the project stands
- **Framework `main` is at `396e4b4`**, on plugin **1.0.22** with tag `v1.0.22` on `cbea66b` (verified, `git log -1 origin/main`, `git ls-remote --tags origin v1.0.22`). The root pin stays at 1.0.17 (choice 249, point 2).
- **The root `CLAUDE.md`** (verified, `git show origin/main:CLAUDE.md`, compared line by line with the text the session gave):
  - **line 3:** "human gates at (a), (b) and (e), and the owner's triage at (f)";
  - **line 33:** the merge App merges on the owner's approving review (decision 36);
  - **line 34:** the App is required (R22) and the version is read in `sdlc.yaml`'s `plugin.version`, with no version number in the line.

  The owner's commits are `2cf98e3` (line 3) and `396e4b4` (lines 3, 33 and 34). These are #306's rows 33 and 34, in the no-version form.
- **The sample's `main` is at `28fba16`, on pin 1.0.22** (verified, its `sdlc.yaml:88`).
  - Sample #100, the owner's `sdlc.yaml`: the pin, plus decision 37's block replacing `profile:` and `review:`.
  - Sample #99, this session's upgrade: the workflow copies, `sdlc_pin.py`, `changes/README.md` and `evals/README.md`. All fifteen `.github` files equal the templates at `v1.0.22` (verified, a byte comparison).
  - On #99's last head, with the pin at 1.0.22, `not-a-build-pr` posted a passing `sdlc/review`, and `test` and `evals` passed (run 39834740891 and its siblings).
- **Open, framework:** #318 (session `ccr-76f1ceba-idf2w0`, docs) and #173 (intent 0004).
- **Open, sample:** #55.

## Preconditions of the moment
- The standing ones are in `HANDOFF.md`.
- **Next free numbers:** choice 251, candidate R65, note 57, decision 39, patch 1.0.23.

## Next steps, in order
1. **The owner's study of the sources of truth** in a new session; the session suggested a prompt in the chat. It reads ROADMAP R9, R58 and R62 first, and its result is a candidate (R65 if still free), not a decision.
2. **At the sample's next change**, read the following, each into a note:
   - decision 36's live checks at (e): the approval counts; the check binds the head; the environment refuses another ref; the merge App's merge starts the release; the approval from the phone;
   - R8's first second opinion at (b);
   - the digest's reading of the `sdlc-merge` environment with `actions: read`.
3. **The sample's ruleset 1 bypass mode**, after session `ccr-76f1ceba-idf2w0`'s test (#318): the owner's call.
4. **This repository's own move from pin 1.0.17:**
   - its own automation App (a separate App is recommended; the session's chat gives the reason);
   - then the `sdlc.yaml` rows: the pin and decision 37's block, in one PR.

   No merge App is needed here (no `sdlc-merge.yml`; fallback C1). Choice 249, point 2 times this at R14's turn (#173).
5. **Then the queue** in ROADMAP's Order column, from R51 with R25, one build session at a time.

## Every open item
| Item | Where | What is left | Who acts | Blocks 1.0.0 |
|---|---|---|---|---|
| Decision 36's live checks; R8's first second opinion; the digest's environment reading | the sample | At its next change | the next session | no |
| The `sdlc-merge` environment | the sample | Not readable from a session; the first merge run verifies it (NOTES §56) | the next session | no |
| The sample's ruleset 1 bypass mode | the sample, ruleset 24078926 | Exempt since 2026-10-22; the bypass-mode test's outcome may move it back | owner | no |
| This repository's App and pin | `sdlc.yaml:104`, `vars.SDLC_APP_ID` | Step 4 above | owner; then a session | no |
| Everything else the second file lists open | `2026-10-22-ccr-3fe1c65e-erwrby.md`, "Every open item" | Carried, not re-verified, except the drops below | as there | no |

Done, dropped:
- "This session's PR" (the second file): #319 merged as `cbea66b`, tag `v1.0.22`.
- "The sample's upgrade to 1.0.22" (the second file): sample #100 and #99, merged as `f8a10ef` and `28fba16`.
- "`CLAUDE.md` rows 33 and 34" (carried since #306): made by the owner in `396e4b4`, in the no-version form.
- "The root `sdlc.yaml` row 6" (#306's table): superseded by decision 37's block (#313's record). It lands with this repository's pin move (step 4).

## What the owner does
| When | Act |
|---|---|
| Now | Merge this PR (documentation only) when `Framework checks` is green. |
| At the sample's next change | Approve the build PR from the phone after gate (e) has run; apply `sdlc:release-approved`. |
| When the bypass-mode test ends | Choose the sample's admin bypass mode in ruleset 1. |
| At R14's turn, or earlier | This repository's own automation App, then the `sdlc.yaml` rows the session will give. |
