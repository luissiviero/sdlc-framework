# Progress — ROADMAP R22, gate (e) is the owner's approving review and a merge App merges on it, as plugin 1.0.18 (2026-10-20)

This session ran on branch `ccr-0edc2256-yax6jz`. The owner's task: build R22 (rank 9) as the next free patch version, 1.0.18, in a session pull request with an independent review, from decision 36, `docs/proposals/gate-e-approving-review.md`, choice 242 (points 2, 4, 5 and 6), R22's row as R60's answers left it and `docs/reviews/2026-10-20-lifecycle-axis-ports/options.md` rows 1 and 3, decision 33 with R49, and decision 35 with R24's `risk_acceptances`. The previous record (docs-lint check 8, choice 247, from #303) is now `docs/progress/2026-10-20-docs-lint-check-8-choice-247.md`, unchanged; #298 had already archived the R64 record and #303 the choice-246 one. The session's own file is `docs/handoffs/sessions/2026-10-20-ccr-0edc2256-yax6jz.md`.

## Coordination with the other sessions
- **The precondition.** R22's hold was still on `main` (`57b5a85`) when the session started: #296, which carries R60's answers into R22's row and lifts the hold, was open. The owner asked whether the build had to wait for it. It did not: the two sessions do different work, and their only shared lines are R22's ROADMAP row and the proposal. So this branch carried #296's commit (`e131e34`) from the start. #296 has merged since (`292f306`), so the hold is lifted on `main` too.
- **Numbers.** This build takes no decision, choice or note number. Decisions 37 and 38 and choices 246 and 247 are the other sessions' (#299, #302, #298, #303). Note 56 is kept for the sample's ruleset change (below), written once the owner has made it.
- **The merge order:** #303 before this PR, as agreed with its session; `main` at `0e11ae9` (its merge) is merged into this branch.
- **The version.** #304 (R8, the Gemini second opinion, open as a draft) also claims 1.0.18. Its session was told that R22 (rank 9) proposes to merge first as 1.0.18 and #304 to move to 1.0.19; the owner's merge order decides, and whichever merges second takes the next number. The session that writes decisions 37 and 38 builds their code after this PR.

## Summary
- **Gate (e) is the owner's approving review** (decision 36, point 1). The build PR's body, `/sdlc-deploy` steps 5 and 6, the close-look banner, the operating model and the README say so: approve = gate (e), and the merge App merges on it.
- **A merge workflow, `sdlc-merge.yml`, the fourteenth template workflow** (points 2 and 4), runs no model and has three jobs:
  - `doorbell`: the owner's approval of a build PR dispatches the merge on the default branch. It holds no key.
  - `not-a-build-pr`: every pull request whose head is not `sdlc/<id>/c` gets a passing `sdlc/review` check, "not a build PR".
  - `merge`: it runs in the `sdlc-merge` environment, which only the default branch may use. It mints the merge App's token and runs `plugin/ci/merge_step.py merge`, which re-checks everything from the API:
    - the build PR is open, not a draft, and at `sdlc:e-ready`;
    - at its head, gate (e) passed with no deferred commands check, and there is no Important finding;
    - every commit after the reviewed one, and after the approved one, is evidence or the run record (a rename's old path included);
    - on the `full` profile, the approved commit already carries gate (e)'s record, so the (d) approval never counts at (e);
    - `sdlc/review` is green on the head;
    - the owner's latest decisive review is an approval.

    Then it merges at exactly that head. A check that does not hold is a green "wait" line; a merge GitHub refuses (a conflict, a rule) is a red run. Either way the PR shows in the digest.
- **The check on the final head** (point 3): after its own last commit, the (e) run posts `sdlc/review` again (`review/cli.py check-run --final-head`). The check is green only while every commit since the reviewed one is evidence or the run record. When it is green and gate (e) waits for the owner, the run dispatches the merge workflow, so an early approval merges then (point 4).
- **The App is required** (R60's answer, options row "Automation identity"):
  - `ci/app_token.py app_missing` stops a run of a workflow that minted no App token: every phase run of `run_phase.py` (`--find-change` and `--phase triage`, which publish nothing, return before it), the detect step's filing and the scan's filing;
  - `/sdlc-init` stops at the App's setup (its step 0), desktop-only, with the links;
  - the workflow token stays the in-job fallback after 50 minutes, the session's token, and the token of the workflows that mint no App token.
- **The (e) acceptance** (choice 242, point 2): when the build PR is merged by anyone but the owner, the release record job takes the risk lines' acceptance from the owner's approving review (`via: approval`). The merge App's `[bot]` accepts nothing. The runner's baseline check confirms such a line from the PR's reviews.
- **The digest** marks an approved, unmerged build PR "approved <date>, not merged: <reason>" (the proposal's line, which R20 places later).
- **The one-time setup** is in `/sdlc-init` step 6: the merge App, its `sdlc-merge` environment, the merge App in ruleset 1, and ruleset 2. The owner's steps for the sample are in the PR body.

## How each "What to settle" row was taken
| Row (the proposal's table) | Taken |
|---|---|
| Whether the owner's approval counts on a PR the automation opened | By its recommendation: verified on the sample at the first (e) after the setup; the merge step reads the review itself, not a required-approval rule, so it holds either way. Not verified yet; C1 if it fails |
| Whether the automation's check satisfies a required check, and binds the head | By its recommendation: to verify at the first PR after ruleset 2 exists; C3 (no ruleset 2) if the first fails. Not verified yet |
| Whether a bypass in "for pull requests only" mode is logged | By its recommendation: to verify. Nothing in the build depends on it |
| The App as a bypass actor, its workflow, the key only for a definition the PR branch cannot change | By the proposal's own recommendation: the review-triggered job holds no key and only dispatches; the merge job reads the key from an environment limited to the default branch and re-checks from the API. That such an environment refuses another ref is to verify |
| Whether a push after the approval dismisses it | By its recommendation: the merge step's own rule decides (the approved commit, then evidence and the run record only) |
| An approval given before the runner's last commit | By the entry's rule: accepted only when every later commit is evidence or the run record (`review/findings.py allowed_after_review`: the change's `evidence/`, its `status.yaml`, `changes/.review-seen.json`). That a review names its commit is used (`commit_id`), verified at the first merge |
| How a build PR is told from the rest | By its recommendation: the merge step reads the findings and gate (e)'s record for the head, and requires `status.yaml: build_pr` to name the PR. The check job tells a build PR by its `sdlc/<id>/c` head alone. While the check has not posted, the PR waits |
| The exact fields of the (e) approval line | R11 is not built: until it is, the merge workflow's log lines are the record (who, when, the commit, the tally), as the proposal's Order says. The risk acceptance line takes the approval (choice 242, point 2) |
| How the owner's account is known | R17's `is_owner_actor`, fail closed, as settled |
| Whether the small workflow's waiting runs hold the required check | By its recommendation: to verify |
| Whether ruleset 2 blocks the owner's direct pushes | By its recommendation: to verify |
| Whether an approval on a conflicted PR starts the merge workflow | By its recommendation: to verify; the digest line is built |
| The digest line for an approved, unmerged build PR | By the proposal's recommendation: built in `pr/digest.py` (red or missing `sdlc/review`, a conflict, or not merged yet), shown on the PR's line under "Waiting at a human gate" until R20 orders the digest |
| Whether the merge App's merge starts the release | By R13's settling: verified at the first merge; the merge workflow dispatches nothing yet |
| The App, its key, ruleset 2 and the web bypass as desktop-only acts | R21's table is not built: `/sdlc-init` step 6 says "desktop-only" with the direct links for each, as R60's answer asks for the App |
| Runbook PRs under ruleset 2 before R36 | **A conflict with the task, put to the owner** (the PR body's question 1): the recommendation holds ruleset 2 back until R36, while the task sets it up now. Since every runbook PR the App opens gets the passing "not a build PR" check, the recommendation's reason no longer holds. The steps for ruleset 2 are given now |
| An (e) head whose findings `sdlc:accept-findings` accepted | R6 is not built: nothing now; the check follows the accepted signatures when R6 is |
| Whether the GitHub mobile app can submit an approving review | To verify on the owner's phone (question 6) |
| The merge App's merge of a dismissal PR | R23's own item |
| The green-preview requirement | R39's own item |
| One decision file or three | Done: decision 36 |

## The independent review
A fresh-context sub-agent reviewed the diff (at `fb29e89` with the working tree) before the PR, with the suite green. It changed no file. It found three Important issues and nine nits; the session had already fixed a tenth, the compare side's rename hole, in `fb29e89` while it read. What became of each:

| # | Finding | Severity | Outcome |
|---|---|---|---|
| 1 | On the `full` profile the owner's (d) approval, an approving review on the same build PR, would count as gate (e)'s | Important | Fixed: on `full` the approved commit must already carry `evidence/gate-e.json` (`merge_step.judge`); an early approval on `standard` still counts (point 4). Tested |
| 2 | A dismissal PR (opened by the abandon workflow's token) and a runbook PR after the App's 50-minute fallback get no "not a build PR" check, so ruleset 2 would hold them | Important | Fixed: `detect/cli.py dismiss --open-pr` and `detect/runbooks.py` post it on the new head. Tested |
| 3 | The final-head check is green for a source file renamed into `evidence/` (git lists only the new path), so ruleset 2 lets the owner merge it without the bypass | Important | Fixed: `review/cli.py` lists the paths with `--no-renames` and no filter. Tested |
| 4 | The final-head check is green when the findings name no reviewed commit | Nit | Fixed: then it is red. Tested |
| 5 | A forged `risk_acceptances` line naming the merge App passes the runner's baseline check, since the App now merges | Nit | Fixed: a line naming an automation account never passes. Tested. The line naming another change's build PR predates R22 and is left as it is |
| 6 | The digest's approved-PR line counts any approver, and its reason assumes a merge App | Nit | Fixed: the owner's account only (`is_owner_actor`, with the default branch's `sdlc.yaml` when the digest has the checkout); the reason names fallback C1 too |
| 7 | The merge job's concurrency group could be split by the dispatch's `head_ref` | Nit | Fixed: keyed on the PR's number |
| 8 | The merge job relies on the environment's branch rule alone, and GitHub creates a missing environment with no rule | Nit | Fixed: the job also requires `github.ref` to be the default branch; `/sdlc-init` says the key is never a repository secret |
| 9 | Installing `sdlc-merge.yml` under an older pin turns every PR's run red | Nit | Fixed: `/sdlc-init` says to bump the pin to 1.0.18 in the same pull request |
| 10 | Stale "the owner's merge" wording at (e) | Nit | Fixed: `sdlc-deploy.md` (description, sources, the human action), `README.md`, `OPERATING_MODEL.md` §2 and §4, `release/cli.py`, `sdlc-init.md` step 1, the review prompt's risk section and the adversarial reviewer's brief |
| 11 | Docs claims: a merge GitHub refuses is red, not green; `app_missing` does not run for `--find-change` and `triage` | Nit | Fixed in the module docstring, the workflow header and this record |
| 12 | Missing tests | Nit | Added: the GitHub helpers' shaping, the 300-file cap, the full-profile case, findings that do not normalise (now a "wait", not a crash). `offer_merge`'s call conditions inside `_run_phase` are tested through `offer_merge` only |

The review also checked these and found them sound:
- the doorbell holds no key and checks the owner against the default branch's `sdlc.yaml`;
- the merge job reads nothing the PR controls, and its key reaches only the mint step and the merge call;
- the head rule's paths (a folder named `changes/0007-x-evil/` is refused) and an "Update branch" merge commit;
- the reviews' states and `commit_id`, and the reading of `status.yaml`;
- `validate_acceptances`;
- `app_missing` runs before any side effect, in exactly the eight workflows that mint the App token;
- `offer_merge` dispatches only on a green check and a gate (e) that waits.

## The port list
This PR touches `plugin/ci/run_phase.py` (`offer_merge`, `MERGE_WORKFLOW`, `_approval_line_problems`, `ACCEPT_VIA_APPROVAL`, the App check in `main`), `plugin/detect/cli.py` (`_app_missing`, the refusal in `cmd_run`, `_post_not_build` in `dismiss`), `plugin/detect/runbooks.py` (the check on the runbook PR) and the detect, runbook and fix workflow templates (their token-rule comments). It goes on the port list until the 1.0.0 read.

## Proposed edits for the owner
| Link | Row | What is there now | What it must become |
|---|---|---|---|
| [sdlc.yaml](https://github.com/luissiviero/sdlc-framework/blob/main/sdlc.yaml#L104) | 104 | `  version: 1.0.17` | `  version: 1.0.18`, after this PR's merge, once `sdlc-tag.yml` has tagged `v1.0.18`, and only after the answer to the PR body's question 2 (this repository has no App) |
| [sdlc.yaml](https://github.com/luissiviero/sdlc-framework/blob/main/sdlc.yaml#L6) | 6 | `` # standard: owner merges at (a) intent PR, (b) spec+plan PR, (e) build PR; (c),(d) automated `` | `` # standard: owner merges at (a) intent PR, (b) spec+plan PR, and approves at (e) build PR `` / `` #           (the merge App merges on that approval, decision 36); (c),(d) automated `` |
| [CLAUDE.md](https://github.com/luissiviero/sdlc-framework/blob/main/CLAUDE.md#L34) | 34 | `` - Events caused by the CI workflow token do not start workflow runs (except workflow_dispatch / repository_dispatch): automated phase transitions dispatch the next workflow explicitly. With vars.SDLC_APP_ID the automation pushes as the project's GitHub App, whose events do start runs (decision 33); the explicit dispatch stays for the fallback. `` | `` - Events caused by the CI workflow token do not start workflow runs (except workflow_dispatch / repository_dispatch): automated phase transitions dispatch the next workflow explicitly. The automation pushes as the project's GitHub App, whose events do start runs (decision 33), and since 1.0.18 the App is required (R22): without vars.SDLC_APP_ID a run stops with the reason. The explicit dispatch stays for the in-job fallback to the workflow token after 50 minutes. `` |
| [CLAUDE.md](https://github.com/luissiviero/sdlc-framework/blob/main/CLAUDE.md#L33) | 33 | `` - Only the owner merges to `main`; the automation identity has branch-only write access. Never use bypass-permissions mode. `` | `` - Only the owner merges to `main`, or the merge App on the owner's approving review (decision 36); the automation identity has branch-only write access. Never use bypass-permissions mode. `` |
| [sample sdlc.yaml](https://github.com/luissiviero/sdlc-sample-python/blob/main/sdlc.yaml#L77) | 77 | `  version: 1.0.17` | `  version: 1.0.18`, at the sample's upgrade to 1.0.18 (after `v1.0.18`, with its fourteen workflow copies) |
| [sample sdlc.yaml](https://github.com/luissiviero/sdlc-sample-python/blob/main/sdlc.yaml#L6) | 6 | `` # standard: owner merges at (a) intent PR, (b) spec+plan PR, (e) build PR; (c),(d) automated `` | as row 6 of the root `sdlc.yaml` above, at the same upgrade |

## Left
- **The live checks of decision 36's "To verify before the design"**, on the sample once the owner's setup is done: whether the approval counts, the required check and its head, the environment's refusal of another ref, whether the merge App's merge starts the release, the mobile approval. Each answer goes into a note.
- **Note 56**, for the sample's ruleset 1 moved to Exempt with ruleset 2 created (choice 242, point 5): written after the owner's act, read from the rulesets API.
- **The sample's upgrade to 1.0.18** after `v1.0.18`: the fourteen workflow copies and the owner's two `sdlc.yaml` rows above.
- Every other open item is in the session file.

## Checks (this repository)
On the final head, after `python -m pip install -e ".[dev]"`, chained with `set -o pipefail`: `python -m compileall -q plugin tests tasks.py .github/scripts`, `python -m ruff check .`, `python -m ruff format --check .`, `python tasks.py docs-lint`, `python -m pytest -n 4` and `claude plugin validate .`. Their output is in the PR.
