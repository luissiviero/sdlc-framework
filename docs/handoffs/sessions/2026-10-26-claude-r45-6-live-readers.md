# Session of 2026-10-26 on branch `claude/r45-6-live-readers`: wave 5, lane G, R45's sixth PR

**Builds on:** `docs/handoffs/sessions/2026-10-26-claude-r45-5-roles.md` (lane A's last file, #396) and the files it names; the parallel file written since, `2026-10-26-claude-r45-names-blocks-in-proposals.md` (lane E, #397). Their open items are carried by reference, not re-verified, but for the rows below.

## Where the project stands
- **Framework `main` is at `0aeffde`** (#397), on plugin **1.0.47**, tagged `v1.0.47` (verified, `git fetch origin` and `git log -1 origin/main`, read at 2026-10-26 on `0aeffde`). This repository's pin is **1.0.46** (`sdlc.yaml:143`).
- **This PR:** R45's sixth PR, plugin **1.0.48**: the readers of live state removed, the readers of history kept (choice 273). Record: `docs/progress/2026-10-26-claude-r45-6-live-readers.md`. With it, R45's six PRs are built.

## Preconditions of the moment
- The standing ones (`HANDOFF.md`); the central session's in `docs/handoffs/central-session.md`.
- **Until the owner commits this PR's four workflow copies** on its branch, `Framework checks` is red on `tests/test_templates.py::test_this_repository_s_workflow_copies_match_the_template` alone.
- **After this PR merges**, a project pinned before 1.0.47 that moves its pin to 1.0.48 or later renames its old names by hand in the same PR (`/sdlc-init`'s upgrade text lists them). This repository (1.0.46) has already migrated its values and `status.yaml` files; its remaining guardrail rows are prose (the record's table). The sample stays at 1.0.47.

## Next steps, in order
1. **This PR:** the owner commits the workflow copies, relabels or closes sample PR #55, and merges when `Framework checks` is green.
2. **R67** (decision 41 A1+B1), the next lane after this PR, on the central session's word (the ROADMAP candidates, in its Order column).
3. The other next steps of the files this one builds on, carried, not re-verified; lane A's next step 3 (the sixth PR) is done here.

## Every open item
| Item | Where | What is left | Who acts | Blocks 1.0.0 |
|---|---|---|---|---|
| This PR | framework, branch `claude/r45-6-live-readers` | The workflow copies, sample PR #55, green checks, the merge | owner | no |
| This repository's guardrail rows | this PR's record | Seven prose rows (two carried from PR 5's record) | owner, at the next pin move | no |
| The port list | each record of R45 | This PR touches `plugin/ci/run_phase.py`, `plugin/detect/` and the runbook template | the 1.0.0 read | no |
| Everything the files above list open | their "Every open item" | Carried, not re-verified | as there | no |

Done, dropped: lane A's "R45's sixth PR" row (this PR).

## What the owner does
| When | Act |
|---|---|
| Now | Commit the workflow copies on this PR's branch; relabel or close sample PR #55; merge when green. |
| At the next pin move | The guardrail rows of this PR's record. |
