# Session of 2026-10-25 to 2026-10-26, wave 5 lane A (R45, the names), last branch `claude/r45-5-roles`

**Builds on:** `docs/handoffs/sessions/2026-10-25-ccr-ca9f0149-a29zgl-wave-5.md` (the third central session's wave 5 file, #386) and the files it carries; the parallel files written since (`2026-10-25-claude-r67-order-cell.md`, `2026-10-25-claude-r67-proposal-decision.md`, `2026-10-25-claude-trial-readiness-recheck.md`) are carried by reference, not re-verified.

## Where the project stands
- **Framework `main` is at `05d9412`** (#394), on plugin **1.0.46**, tagged `v1.0.46` (verified, `git fetch origin`, `git log -1 origin/main` and `git ls-remote origin 'refs/tags/v1.0.4*'`, read at 2026-10-26 on `05d9412`). This repository's pin is still **1.0.38** (`sdlc.yaml`).
- **R45 in this lane, merged:** #387 (the names added since decision 39, judged: `docs/reviews/2026-10-25-names-added-since-decision-39.md`, rows N29 to N40), #389 (PR 1, the phase names, 1.0.43), #390 (PR 2, `sdlc:triage`, `sdlc:schedule`, the verdict `park`, the explain step, 1.0.44), #393 (PR 3, `deploy.production_gate`, `allow | ask`, `second_opinion`, 1.0.45), #394 (PR 4, the intent's `Status:` line gone, `sdlc-agent-evals.yml`, `ux-and-brand`, `on-approval`, "no merge App", 1.0.46). Each PR's record is `docs/progress/2026-10-25-claude-r45-<n>-*.md`.
- **This PR:** PR 5, the roles where a decision is asked and the merge and review rulesets (row 87, N9, N10), plugin **1.0.47**; record `docs/progress/2026-10-26-claude-r45-5-roles.md`. No workflow template changed, so the owner commits no copy.
- **Added on the way:** `python tasks.py workflow-copies` (#389, at the central session's request), the owner's one command for this repository's workflow copies after a template change.

## Preconditions of the moment
- The standing ones are in `HANDOFF.md`; the central session's in `docs/handoffs/central-session.md`.
- **Every merge to `main` shows two red runs** (SDLC design and SDLC build) until this repository's pin moves: since #389 their copies pass phase names to the pinned 1.0.38 runner, which refuses them (`invalid choice: 'build'`; runs 40231733027 and 40231732955). No change is in flight, so nothing is lost.
- **Until the pin moves to 1.0.46 or later:** start no change in this repository, and merge an approved build PR here by hand (#394's merge copy runs `merge_step.py on-approval`, which the pinned plugin lacks).
- **Lane D** (the central session's) prepares this repository's single pin move from these records; it touches `changes/**` and docs only.

## Next steps, in order
1. **This PR (PR 5):** the owner merges it when `Framework checks` is green.
2. **The pin move of this repository** (lane D, the owner's single move): the pin to 1.0.47 or later, the `changes/*/status.yaml` migration to the phase names, and the guardrail rows of every record of this lane, in one PR. The rows: #389's record (`sdlc.yaml` `session_model` key, `CLAUDE.md` lines 3 and 19, `REVIEW.md` line 27), #393's (eleven rows of `sdlc.yaml` and `bands.yaml`), #394's (`framework-evals.yml` line 4 is already committed), this record's (`bands.yaml` 21-22, `sdlc.yaml` 64, merged with #393's rows for the same lines). `deploy.production` is renamed only with the pin at 1.0.45 or later (#393's record). The sample moves its copies and pin together with `/sdlc-init`'s upgrade; its guardrail lines are read at its own pin-move PR.
3. **The sixth PR** (a successor lane, on the central session's word): it removes only the readers of live state, after this repository and `luissiviero/sdlc-sample-python` are migrated and pinned at 1.0.46 (PR 4's version) or later, and before the real-project trial (choice 273). It keeps the readers of history for good: `conventions.LEGACY_PHASES`, `phase_name`'s letter mapping, `BRANCH_RE`'s letter branch, `Status`'s letter reading on a remote branch's file, `counters.py`'s `deploy` (and `e`), `detect/cli.py` and `scan/route.py`'s readers of the remote `sdlc/<id>/<letter>` branches, and the readers of merged changes' evidence files (decision 39's annotation of point 1; `docs/reviews/2026-10-25-names-added-since-decision-39.md`, "The readers the sixth PR keeps"). The live readers to remove, one release after 1.0.43 to 1.0.46: the letter `--phase` values, the letter labels (`ready_labels`' second name), `phase_file`'s letter fallback for an in-flight change, `gitops.existing_branch`'s letter branch for new runs, `session_model` and `second_opinion.phases` letter keys, the old labels `incident`/`schedule`, `escalate` and "Word", `--phase triage`, the `triage=` output and `triage` record keys, `claude-triage*.json`, `deploy.production`, `preapproved`/`go`, `external_review`, the intent's optional `Status:`, `sdlc-evals.yml`'s retirement, `policies/ux-conventions.md` and `.claude/skills/ux-conventions/`, the `doorbell` alias. Section 12's closing `git grep` excepts the readers of history and will list, besides, the merge workflow template's two comments still saying "ruleset 1/2" (`template/.github/workflows/sdlc-merge.yml` lines 8 and 22, left so this PR needed no copy).
4. The other next steps of the central session's file, carried, not re-verified.

## Every open item
| Item | Where | What is left | Who acts | Blocks 1.0.0 |
|---|---|---|---|---|
| PR 5 | framework, branch `claude/r45-5-roles` | Green checks, the owner's merge | owner | no |
| This repository's pin move | the records above | Pin to 1.0.47+, `status.yaml` migration, the guardrail rows | lane D; owner | no |
| R45's sixth PR | Next steps 3 | Remove the live readers, after both repositories are pinned at 1.0.46+ | successor lane; owner | no |
| The review ruleset's name | PR 5's record | Rename it `review and no direct writes on main` if it still says `(decision 36, choice 251)`; desktop-only; nothing reads it | owner | no |
| The port list | each record of this lane | #389, #390, #393, #394 and this PR touch `plugin/ci/run_phase.py`, `plugin/detect/` or the detect, runbook and fix templates | the 1.0.0 read | no |
| Everything the central session's file lists open | its "Every open item" | Carried, not re-verified | as there | no |

Done, dropped: "Wave 5 (R45)" of the central session's file is done but for the pin move and the sixth PR (rows above).

## What the owner does
| When | Act |
|---|---|
| Now | Merge PR 5 when it is green. |
| Then | Lane D's pin-move PR of this repository, with its guardrail rows. |
| When convenient | The review ruleset's name (desktop-only). |
| After both pins are at 1.0.46+ | The sixth PR, from a successor lane. |
