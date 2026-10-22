# Session of 2026-10-20 on branch `ccr-3fe1c65e-erwrby`: the R22 session double-checked (report only); the merge order; the queue held behind decision 37's code

**Builds on:**
- `docs/handoffs/sessions/2026-10-20-ccr-0edc2256-yax6jz-part-3.md` (#311), the newest session file on `main` at `a592a6d`;
- the parallel files it names: `2026-10-20-ccr-6ed8a82e-cxmftx.md` (#304, R8) and `2026-10-20-ccr-0522ec37-iia2ok-part-3.md` (#305).

No other session file is newer than these (verified, `git log --diff-filter=A origin/main -- docs/handoffs/sessions/`). `2026-10-20-claude-review-open-sessions-prs-37hoge.md` sorts last by name, but it reached `main` at 17:32 UTC (`fc30118`), before the files above. Session `ccr-0522ec37-iia2ok` has written no file for #307 yet: #307 is open, and its branch carries no new session file (verified, `git diff --stat origin/main origin/ccr-0522ec37-iia2ok-auth-order -- docs/handoffs`).

The owner's task had two parts:
1. Double-check the R22 session, report only: the code with an independent fresh-context sub-agent, the documents, the records and their citations, the sample's copies and `sdlc.yaml`, and the merge `f93d4d0`.
2. Continue from the part-3 file's "Next steps, in order".

## Where the project stands
- **Framework `main` is at `0a0554d`**, the merge of #307 on 2026-10-22 (verified, `git log -1 origin/main`). It is on plugin **1.0.20**, and `v1.0.20` is the newest tag (verified, `git tag`). The root pin stays at 1.0.17 (choice 249, point 2; verified, `sdlc.yaml:104`).
- **What #307 changed for the projects:** three template files between `v1.0.19` and `v1.0.20` (verified, `git diff --stat v1.0.19 v1.0.20 -- template/`). `template/.claude/settings.json` lost the Gemini host (#310); the sample's copy already lacks it. `sdlc-evals.yml` changed in a comment only, and `evals/README.md` names the new credential order. So the sample on pin 1.0.19 needs nothing to keep working; its move to 1.0.20 is #307's proposed row, at its next upgrade. #307 added no session file (verified, `git diff --name-only a592a6d 0a0554d -- docs/handoffs`).
- **The sample's `main` is at `21f1748`**, on pin 1.0.19 (verified, `git show origin/main:sdlc.yaml`).
- **The double check** is `docs/reviews/2026-10-20-r22-session-double-check.md`, in this session's PR. Nothing was fixed. It finds no high-severity defect: the merge App merges only on the owner's latest approving review, at a head the findings allow. It does find these:
  - four medium code defects with small fixes: F1 (the abandon workflow has no `checks` permission, so ruleset 2 would hold every dismissal PR), F2 (the baseline check confirms an approval line by anyone, on any change's build PR), F4 (the runbook Go does not refuse a run without the App) and F5;
  - one medium question for the owner, F3 (an approval given before gate (e) ran counts);
  - three medium stale (e) sentences in `docs/OPERATING_MODEL.md` (D1 to D3);
  - four medium record gaps: decision 36 point 5 and the proposal not annotated for choice 249 (M1, M2), ROADMAP R22's record pointer (M3), and part 1's next free choice (M5).

  The sample's copies, its `sdlc.yaml` and the merge `f93d4d0` hold (sections 4 and 5 of the review).
- **Open, framework** (verified, the GitHub PR list):
  - #173 (intent 0004), at R14's turn.
  - This session's PR, which merges cleanly onto `0a0554d` (verified, `git merge-tree`).
- **Decision 37's code** is on branch `ccr-0522ec37-iia2ok-modes-code` at `be487c6`, with no PR yet. It is based on `e4dfca1`, so it has neither #304 nor #307, and its `plugin.json` still reads 1.0.18 (verified, `git show`). Merged with `main` at `0a0554d` it conflicts in `docs/OPERATING_MODEL.md` only (verified, `git merge-tree --name-only`); that merge is its own session's.
- **Open, sample:** #55.
- **R22's setup on the sample:** the owner reports step A done (the merge App) on 2026-10-22. It is not verified: the session's GitHub route refuses `/apps/...` ("sessions are bound to their configured repositories"), and `/repos/.../installation` needs the App's own key. Step C verifies it, since only an App installed on the repository can be added to ruleset 1's bypass list. Steps B to D are not done (verified on 2026-10-22, the rulesets API): one ruleset, 24078926, whose one bypass actor is the admin role in `pull_request` mode; no second ruleset.

## Preconditions of the moment
- The standing ones are in `HANDOFF.md`.
- **Next free numbers:** choice 250, candidate R65, note 56 (kept for the sample's rulesets), decision 39. Patch 1.0.20 is #307's and 1.0.21 decision 37's code, so 1.0.22 is the next free. This session took none.

## Next steps, in order
1. **This session's PR** (documentation only): the owner merges it when `Framework checks` is green, at any point in the order below.
2. **Decision 37's code (1.0.21)**, session `ccr-0522ec37-iia2ok`'s. #307 merged as `0a0554d`. Decision 37's branch has to merge `main` (with #304 and #307) first, resolving `docs/OPERATING_MODEL.md`, and take 1.0.21.
3. **The owner's answers** to the review's four questions (F3, F8, F9, the fix PR).
4. **If the owner agrees, the fix PR as 1.0.22**: F1, F2, F4 and F5 with F13's tests, and the documentation rows the owner wants in it. It starts from `main` after decision 37's code merges, and before R51, which also changes the merge step.
5. **When the owner says R22's steps A to D are done on the sample:** read both rulesets, and the environment where the API shows it. Write note 56 (choice 242, point 5) in a documentation PR.
6. **At the sample's next change:** read decision 36's live checks at (e) and R8's first second opinion at (b), and record each answer in a note. The sample sets `deploy.production: true`, so its (e) also needs the release label.
7. **Then the queue in ROADMAP's Order column**, from R51 with R25, one build session at a time. It is not started here: decision 37's code (another session's build) is still open, and touches `run_phase.py`, the gate and the state code that R51 also changes.

## Every open item
| Item | Where | What is left | Who acts | Blocks 1.0.0 |
|---|---|---|---|---|
| This session's PR | framework | `Framework checks` green, then the owner's merge | owner | no |
| Decision 37's code | framework | Its PR is not opened yet; `main` to merge in first | session `ccr-0522ec37-iia2ok`; owner | no |
| #307's session file | `docs/handoffs/sessions/` | #307 merged with none; the file is session `ccr-0522ec37-iia2ok`'s to write | that session | no |
| The review's questions | `docs/reviews/2026-10-20-r22-session-double-check.md`, "Questions for the owner" | F3, F8, F9, and the 1.0.22 fix PR | owner | no |
| F1, F2, F4, F5 and F13 | the same review, section 1 | A plugin patch after decision 37's code | the next build session, if the owner agrees | no |
| D1 to D9, M1 to M4, L4 to L6 | the same review, sections 2 and 3 | Edits and annotations, in the fix PR or a documentation PR | the next session | no |
| R22's setup on the sample | #306's body, steps A to D | A reported done, not verified; B to D the owner's acts | owner | no |
| Note 56 | `docs/notes/` | After steps C and D | the next session | no |
| Decision 36's live checks; R8's first second opinion | the sample | At its next change | the next session | no |
| `CLAUDE.md` rows 33 and 34, the root `sdlc.yaml` row 6 | `docs/progress/2026-10-20-r22-gate-e-approving-review-1.0.18.md`, "Proposed edits for the owner" | The owner's edits. Not made on `a592a6d` (verified, `CLAUDE.md:33-34`, `sdlc.yaml:6`) | owner | no |
| The root pin | `sdlc.yaml:104` | At 1.0.17 until this repository has its App, at R14's turn (choice 249, point 2) | owner | no |
| A Gemini key per repository | the owner's Google Cloud projects | Carried from the part-3 file, not re-verified | owner | no |
| R8's open items | `2026-10-20-ccr-6ed8a82e-cxmftx.md`, "Every open item" | Carried unchanged, not re-verified, except the row dropped below | as there | no |
| Everything the R22 session's files list open | `2026-10-20-ccr-0edc2256-yax6jz.md`, `-part-2.md`, `-part-3.md` | Carried, not re-verified, except the rows above and the drops below | as there | no |
| Everything #305's session file lists open | `2026-10-20-ccr-0522ec37-iia2ok-part-3.md` | Carried unchanged, not re-verified | as there | no |

Done, dropped:
- "The holds" (R11, R30, R39, R16; `2026-10-20-ccr-0edc2256-yax6jz.md`, carried by its parts 2 and 3): #305 lifted them (`81b15bc`).
- "The sample's second opinion" (#304's file): the secret is reported set, and the `sdlc.yaml` paste is samples #97 and #98, the 1.0.19 copies sample #92 (`21f1748`). Only the first live run is left, as next step 6.

## Corrections to earlier files
- `2026-10-20-ccr-0edc2256-yax6jz.md`, "Next free numbers: choice 248": 248 was already #304's (`5a47c1c`), so the next free was 249, as its part 2 says.
- `2026-10-20-ccr-0edc2256-yax6jz-part-2.md`, "its pin since sample #95", and `2026-10-20-ccr-6ed8a82e-cxmftx.md`, "since sample #93 and #95": the pin moved to 1.0.18 in sample #94 (`2588c48`); #95 (`a801bb0`) changed row 6.
- `2026-10-20-ccr-0edc2256-yax6jz-part-3.md`, "Builds on": `2026-10-20-ccr-0522ec37-iia2ok-part-3.md` reached `main` with #305, before #308, and part 2 had already built on it.
- `2026-10-20-ccr-0edc2256-yax6jz-part-3.md`, "Done, dropped": #304's row is "The pastes of choice 248", not "The settings.json pastes".
- `2026-10-20-ccr-0edc2256-yax6jz.md`, next step 1 (a line to session `session_01MGH2eZ98Pv36WhdtkP3s55`): neither carried nor dropped by part 2. That session's #307 has since moved to 1.0.20 on its own, so the step is done in effect.

## What the owner does
| When | Act |
|---|---|
| Now | Merge this PR when `Framework checks` is green. Answer the review's four questions. |
| When its session opens it | Read decision 37's PR (1.0.21), and merge it when green. |
| Any time | R22's steps B to D on the sample (A is done), then tell the session; the `CLAUDE.md` rows 33 and 34 and the root `sdlc.yaml` row 6. |
| At the sample's next change | Approve its build PR from the phone, and apply `sdlc:release-approved` (`deploy.production: true`). |
