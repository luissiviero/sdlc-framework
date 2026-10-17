# Progress — the item-11 follow-ups (2026-10-14 to 2026-10-17): change 0005 from gate (b) to plugin **1.0.2**, the sample's detect run of 2026-10-15, eight gaps recorded

This session ran the item-11 follow-ups hand-over (written by session `ccr-4a548fe6-7cqzlo`, whose context was full) on branch `ccr-f21be30b-5d5dpz`, with both repositories in scope. The previous record, 1.0.1's, is now `docs/progress/2026-10-14-1.0.1.md`, unchanged. The sample was only read: nothing was pushed to it, no run on it was dispatched or approved, and none of its PRs was commented on or closed. This session pushed no code: change 0005 was built by its own phase runs, and every act on `main`, on #186 and on #211 was the owner's.

## Summary
- **Change 0005 is merged and released as `v1.0.2`** (PR #211, `807c5f6`, 2026-10-17 13:41 UTC). The facts and the run links are in NOTES §45.
  - Gate (b): the fix round on #186 applied the owner's two asks; the owner merged #186 on the session's recommendation (choice 197).
  - Phase (c) took six fix rounds and three guardrail edits by the owner (choices 198 and 199) before gate (c) said `continue`; (d) and (e) followed without a park.
  - The change cost 56.30 USD (`evidence/spend.json`), 42.88 of it in the seven fix rounds.
- **The sample's scheduled detect run of 2026-10-15** (run 38719318852): `ref=v1.0.1`, latest point 2026-10-14 at 0, no rule fired, `filed: {}`, as choice 193 expected.
- **Eight gaps**, each traced in the code at `807c5f6` (NOTES §45, "The gaps"): the panel `park` that does not park; a build parked at the preflight that nothing can restart while its PR is open; fix-round work lost at the turn cap and at a question; an unattended session that asked a question; the 200-turn default; an `sdlc.yaml` that does not parse failing open; a PR in conflict that starts no workflow; the tag workflow tagging a version that `main`'s own checks fail. None is fixed here: each needs the owner's choice of route (below, "Left").
- **Undone on `main`:** the owner's PR #217 (`plugin.json` alone at 1.0.2) and the `v1.0.2` tag and release it caused (choice 201).

## The owner's decisions (2026-10-14 to 2026-10-17)
197. **PR #186 is merged at gate (b) without a second "Request changes" review.** A second review would have spent the last fix round of the change's counter (non-routine cap 2, one counter across the phases). The test the spec's skip-marker requirement implies for the test-runner's configuration files (`spec.md:58-61` and `:91` against Acceptance `:242-244`) stays without its own Proof item; the panel had judged it a nit.
198. **`CLAUDE.md` names `sdlc.yaml`'s lint command exactly** (PR #213, `2c6d31d`): lines 8 and 55 read `python -m ruff check . && python -m ruff format --check .`.
199. **The root `sdlc.yaml` sets `gate.max_turns: 400`** (PR #214, re-indented by PR #216, `0fddc29`; `sdlc.yaml:62`).
200. **Panel decision 1 of change 0005 at (c) stands** (2026-10-17): a dot-prefixed rename of one file of an eval case drops the whole case even when a sibling stays, and `test_ratchets_eval_case_dot_rename_wins_over_a_surviving_sibling` pins it. It fails closed; an unwanted hit is lifted with `sdlc:accept-risk` or a declaration in the change's `plan.md`.
201. **The `v1.0.2` made from PR #217 is undone:** PR #218 reverted it (`53e56e7`), and the owner deleted the tag and its release. Change 0005 keeps 1.0.2.
202. **PR #211 is merged at gate (e)** (2026-10-17, `807c5f6`), with its three review nits left for a later change.

## Proposed edit for the owner
Carried from change 0005 (its `plan.md` step 8; the 1.0.1 record, now `docs/progress/2026-10-14-1.0.1.md`). This repository's own root `REVIEW.md` is a guardrail file.

| File | Line | What is there now | What it must become |
|---|---|---|---|
| [`REVIEW.md`](https://github.com/luissiviero/sdlc-framework/blob/main/REVIEW.md#L26) | after 26 (the end of the `plan.md` bullet) | nothing; line 27 starts "- The second occurrence of the same finding …" | `- Each added skip marker the gate's \`ratchets\` check listed at gate (e) (\`evidence/gate-e.json\`'s \`details.skip_markers\`) must be declared in \`plan.md\` or explained in the PR; an undeclared one quietly narrowing what the suite actually runs is non-compliant.` (the same bullet `template/REVIEW.md:27-30` carries since 1.0.2) |

## Checks (this repository)
On the final head, after `python -m pip install -e ".[dev]"`, chained with `set -o pipefail`: the four commands of `HANDOFF.md`'s standing precondition 1. Their output is in the PR.

## Left
- **The eight gaps** wait for the owner's route (a ROADMAP candidate with a proposal, a framework change under `changes/`, or a plain fix PR). The session's recommended order, by what each risks: *[2026-10-17, after PR #221 merged: superseded by the mapping onto ROADMAP's Order (PR #215's pipeline sprint, R10 to R49) in `docs/handoffs/sessions/2026-10-17-ccr-f21be30b-5d5dpz.md`, section "After #221 merged"; the order below is kept as written (choice 126).]*
  1. Gap 6, the `sdlc.yaml` that fails open: a broken file turns off `paused` and the risk list without a word.
  2. Gap 8, the tag workflow: a tag on a commit whose own checks fail.
  3. Gaps 3 and 4, lost work and the unattended question in a fix round.
  4. Gap 2, the build that cannot be restarted.
  5. Gap 1, the panel `park`.
  6. Gap 7, the PR in conflict (GitHub's rule; a note in the owner's surface may be enough).
  7. Gap 5 is settled for this repository by choice 199; whether the template's default should rise too is part of gap 3's route.
- **The sample's pin to 1.0.2**: under `template/`, 1.0.2 changes only `REVIEW.md` (verified, `git diff --name-only v1.0.1 v1.0.2 -- template`), so the sample needs its pin row and, if wanted, the new `REVIEW.md` bullet. Both are guardrail rows for the owner, given when the owner asks.
