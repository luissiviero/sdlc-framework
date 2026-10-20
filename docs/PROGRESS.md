# Progress — R22's six questions answered as recommended (choice 249); the sample's upgrade to 1.0.18 opened (2026-10-20)

This session ran on branch `ccr-0edc2256-yax6jz`, restarted from `main` at `18b2a22` after #306 (R22, plugin 1.0.18) merged. The owner's tasks after the merge:
- recommend whether to open the sample's upgrade to 1.0.18;
- give the six questions of #306's body in a table, with a recommendation each;
- then: "Accept all recommendations; open the sample's 1.0.18 upgrade PR".

The previous record (R22 as 1.0.18) is now `docs/progress/2026-10-20-r22-gate-e-approving-review-1.0.18.md`, unchanged. The session's file for this part is `docs/handoffs/sessions/2026-10-20-ccr-0edc2256-yax6jz-part-2.md`.

No change under `plugin/` or `template/`; no version bump.

## Summary
- **#306 merged** as `18b2a22`, and `sdlc-tag.yml` tagged `v1.0.18` on it (verified, `git ls-remote --tags origin v1.0.18`).
- **Choice 249**: the six questions of #306 are answered as the session recommended. Each answer is annotated beside the sentence it settles, where a kept record carries one.
- **The sample's upgrade to 1.0.18** is sample #93, a draft. It holds the thirteen workflow copies and the new `sdlc-merge.yml`, each the template at `v1.0.18` with `{{FRAMEWORK_REPO}}` filled. Every old copy equalled the template at `v1.0.17`, and `sdlc_pin.py` is unchanged between the two tags. The owner's two `sdlc.yaml` rows went first, in sample #94 and #95 (below).

## The owner's decision (2026-10-20)
249. **The six questions of #306 are answered as recommended** (the owner, "Accept all recommendations; open the sample's 1.0.18 upgrade PR"):
    1. **Ruleset 2 is created now**, before R36. Since 1.0.18 every runbook PR gets the passing "not a build PR" check, so none waits on the ruleset. R36 later gives runbook PRs a real review. Annotated: the R22 proposal's settle row "Runbook PRs under ruleset 2 before R36".
    2. **This repository's root pin stays at 1.0.17** until this repository has its own App. The App is set up when its pipeline is next used: #173 at R14's turn. Until then, the pin row of the previous record waits.
    3. **Where environments are not available** (a private repository on a free plan), the owner merges after approving (fallback C1). The merge App's key is never a repository secret. Annotated: decision 36, point 6.
    4. **The merge App's bypass mode in ruleset 1 is "For pull requests only".** It moves to Exempt only if the first API merge is refused with HTTP 405. As built (`/sdlc-init` step 6).
    5. **The merge step keeps the merge commit** (`merge_method: merge`). As built (`pr/github.py MERGE_METHOD`).
    6. **The owner approves the sample's next build PR from the GitHub mobile app once**, which answers decision 36's last "To verify" row. If the app cannot submit an approving review, the fallback is github.com in the phone browser's desktop mode, recorded in a note.

## The sample's rows
The owner made the two rows in sample #94 and #95, merged as `2588c48` and `a801bb0`. The sample's pin reads `version: 1.0.18` on its `main` (verified, `git show origin/main:sdlc.yaml`). `main` was then merged into sample #93's branch (`3fc7d74`), so its `not-a-build-pr` job re-ran on the new pin.

Row 6 landed as one line, its two halves joined by " / " (verified, the same read). It is a comment, so nothing reads it; the first row below splits it, when convenient.

## Proposed edits for the owner
| Link | Row | What is there now | What it must become |
|---|---|---|---|
| [sample sdlc.yaml](https://github.com/luissiviero/sdlc-sample-python/blob/main/sdlc.yaml#L6) | 6 | `# standard: owner merges at (a) intent PR, (b) spec+plan PR, and approves at (e) build PR / #           (the merge App merges on that approval, decision 36); (c),(d) automated` | two lines: `# standard: owner merges at (a) intent PR, (b) spec+plan PR, and approves at (e) build PR`, then `#           (the merge App merges on that approval, decision 36); (c),(d) automated` |
| [CLAUDE.md](https://github.com/luissiviero/sdlc-framework/blob/main/CLAUDE.md#L33) | 33 | ``- Only the owner merges to `main`; the automation identity has branch-only write access. Never use bypass-permissions mode.`` | as the previous record's row 33 (not yet made; verified on `main` at `18b2a22`) |
| [CLAUDE.md](https://github.com/luissiviero/sdlc-framework/blob/main/CLAUDE.md#L34) | 34 | the fallback sentence | as the previous record's row 34 (not yet made) |
| [sdlc.yaml](https://github.com/luissiviero/sdlc-framework/blob/main/sdlc.yaml#L6) | 6 | `# standard: owner merges at (a) intent PR, (b) spec+plan PR, (e) build PR; (c),(d) automated` | as the previous record's row 6 (not yet made) |

The root `sdlc.yaml` pin row (line 104) is held by choice 249, point 2.

## Left
- **Sample #93 merged** as `d602179`, after its checks were green on `3fc7d74`. On that head the `not-a-build-pr` job posted a passing `sdlc/review` check (verified, the PR's check runs), the first live run of `sdlc-merge.yml`. Its first `not-a-build-pr` run had been red, as expected: the pin was still 1.0.17, which lacks `merge_step.py` (job 118860513392).
- **The owner's GitHub steps A to C**, then D after #93 merges (#306's body).
- **Note 56**, from the rulesets API, once the owner has made C and D.
- **Decision 36's live checks**, at the sample's next change at (e), the approval from the phone included (point 6).

## The port list
This PR touches no file of the port list's paths.

## Checks (this repository)
On the final head, after `python -m pip install -e ".[dev]"`, chained with `set -o pipefail`: `python -m compileall -q plugin tests tasks.py .github/scripts`, `python -m ruff check .`, `python -m ruff format --check .`, `python tasks.py docs-lint`, `python -m pytest -n 4` and `claude plugin validate .`. Their output is in the PR.
