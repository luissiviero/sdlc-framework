# Progress — the review of PRs #250 to #252 and its follow-ups: R44's `policies/` entry after R27, the sandbox proof back in the queue, the superseded PR's token, and the owner's choice 239 (2026-10-20)

This session ran on branch `ccr-e4e43fa6-d3y9ly`, from the owner's task of 2026-10-19: a fresh-context adversarial review of the last three merged PRs (#250, #251, #252), report only. The owner then accepted the review's recommendations (choice 239) and asked for the two documentation fixes in a PR that merges after the roadmap session's PR (#257, R7), with every other finding registered in ROADMAP. The previous record (ROADMAP R7, the in-run reviewer on the latest Opus, plugin 1.0.14, PR #257, from the parallel session `ccr-e4a1d6f8-lgxd25`, which merged first as the owner asked) is now `docs/progress/2026-10-19-r7-reviewer-on-latest-opus-1.0.14.md`, unchanged; #257 archived the one before it (choice 238, PR #252) as `docs/progress/2026-10-19-order-before-the-trial-and-choice-238.md`, and this PR's identical copy of it merged without a change. The session's own file is `docs/handoffs/sessions/2026-10-20-ccr-e4e43fa6-d3y9ly.md`.

No change under `plugin/` or `template/`; no version bump.

## Summary
- **The review**: `docs/reviews/2026-10-19-prs-250-252-review.md`. #250 sound with notes, #251 sound with notes, #252 one finding to act on; one Important, seven Minor and four Nit rows, each traced to a file and line.
- **R44's `policies/` entry waits for R27** (the review's Important row). R44's scope names "the policy sources", R27's `policies/` folder. The decision table of 2026-10-15 (`docs/handoffs/2026-10-15-decision-table-r21-r45.md`, line 43) lists "R27 for the `policies` entry" as R44's prerequisite. Choice 238 put R44 at rank 12, before R27 at 19, without saying so. R44's Order cell now says that one entry comes with or after R27. The rest of R44 stays at 12.
- **The sandbox proof is back in the queue**, next after R7's PR and before rank 8. It was carried "before rank 7" from 2026-10-13. #252's session file said it was now R44's first step, at rank 12, which choice 238 did not decide. R7 (#257) was already open when choice 239 was taken; #257's record (step 1, item 13) and session file repeat the rank-12 reading, which this choice corrects. With #257 merged, the sandbox proof is the next queue item.
- **`docs/OPERATING_MODEL.md` §4**: a superseded intent or design PR is closed with the automation's token, the App's when `SDLC_APP_ID` is set (decision 33), else the workflow token. That is what `run_phase.supersede_pr` does and what NOTES §50 saw on the sample's #77 (`closed_by: sdlc-automation-luissiviero[bot]`). The sentence said "the workflow token".
- **Registered in ROADMAP**, no rank moved:
  - R51 (rank 10) carries the six notes on #251's `gitops.remembered`: the lookups' timeout, the narrowed comment, the audit-event test, the separate-valued global options, `is_repo` for a removed linked worktree, and a test's name. R51's id reservation relies on that cache.
  - R54 (rank 14) carries the intent PR's "What needs you" line on the fast lane, which still says "merge = approve (gate (a))" after the PR's opening was gate (a).
  - R47's row: the next note that reads R47's push annotates NOTES §49's R47 bullet, whose two conditions stay unverified.

## The owner's decisions (2026-10-20)
239. **The review of PRs #250 to #252 is acted on** (the review's recommendations; the owner, "I accept the recommendations"):
    - R44's `denyWrite` entry for R27's `policies/` sources comes with or after R27 (rank 19); the rest of R44 stays at rank 12;
    - the sandbox proof stays in the queue outside the ranks, next after R7's PR and before rank 8;
    - `docs/OPERATING_MODEL.md` §4 names the automation's token for the superseded PR's close;
    - the other findings ride with R51 (the `gitops` notes), R54 (the fast-lane "What needs you" line) and R47's next note (NOTES §49's bullet);
    - this PR merges after the roadmap session's PR (#257, R7).

## Proposed edits for the owner
None: no guardrail line changes in this PR.

## Left
- **The sandbox proof** is the next queue item, now that R7's PR (#257) has merged. The template sandbox block (#257's step 1, item 13) waits on it.
- **NOTES §49's bullet** waits for the next note on R47.

## Checks (this repository)
On the final head, after `python -m pip install -e ".[dev]"`, chained with `set -o pipefail`: the four commands of `HANDOFF.md`'s standing precondition 1, plus `python tasks.py docs-lint`. Their output is in the PR.
