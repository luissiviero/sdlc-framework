# Progress — decisions 35 (R24) and 36 (R22), and the owner's choice 242 on their questions (2026-10-20)

This session ran on branch `ccr-8913e578-kwfegl`. The owner's task was to write the decision files of R24 and R22, numbered 35 and 36, one after the other, each in a documentation PR of its own, then answer the questions those PRs raised. The previous record (R61 accepted, NOTES §53, R58's check 8, choices 240 and 241) is now `docs/progress/2026-10-20-r61-accepted-notes-53-and-choices-240-241.md`, unchanged. The session's own file is `docs/handoffs/sessions/2026-10-20-ccr-8913e578-kwfegl.md`.

No change under `plugin/` or `template/`; no version bump.

## Summary
- **Decision 35** (R24): a risk-list hit is a line in the close-look banner, accepted by the owner's merge; it amends 11, 21 and 24. PR #279 merged as `d608f69`.
- **Decision 36** (R22): gate (e) is the owner's approving review, and a GitHub App merges on it; it amends 13, 4 and 5. PR #280 merged as `c15dd35`.
- **Choice 242**: the owner accepted the session's recommendation on each of the six questions the two PRs raised. Each answer is annotated beside the sentence it settles; nothing is reopened.
- **Choice 243**: no page kept by hand states a count of the decisions or the notes; docs-lint's check 9 keeps it so.

## The owner's decisions (2026-10-20)
242. **The questions of #279 and #280 are answered as the session recommended** (the owner, "accept all your recommendations"):
    1. **R15's measured ratchet fall, once `sdlc:accept-risk` retires,** is a banner line the owner's (e) merge accepts, as every risk-list hit is. It amends R15 point 9 and decision 29's park at the iteration cap, so its decision file is written with R15's second change's design, before that change's intent. Annotated: decision 35 ("Left to the design"), R15's and R24's ROADMAP rows, `docs/proposals/ratchets.md` point 9, `docs/proposals/risk-hit-in-banner.md` ("What to settle").
    2. **Once R22 is built, the owner's approving review accepts the banner's risk lines,** recorded on R22's (e) approval line. The App that then merges is a `[bot]` and never accepts a risk (`is_automation_actor`). Annotated: decision 35, point 2; R24's row; the R24 proposal's settle row.
    3. **Decision 11's "nobody is notified" stays as written.** Kept records are annotated, never rewritten (choice 126), and its `amended_by` already names 31. No edit.
    4. **R22 merges through a merge App of its own, not decision 33's App.** GitHub grants a bypass to an actor, not to a job, and the phase runners hold decision 33's App token; so that App is never a bypass actor, its merge step included. The merge App's key is a secret of a GitHub environment only the default branch can use, read only by the merge job. Annotated: decisions 33 and 36 (points 2 and 6), R22's row, `docs/proposals/gate-e-approving-review.md` point 2, `docs/proposals/pipeline-speed.md` (R49's row).
    5. **The sample's ruleset 1 moves from `pull_request` mode to Exempt** when R22 sets up ruleset 2 there, recorded in a note (`docs/notes/53.md` read it in `pull_request` mode). Annotated: decision 36, point 5; R22's row; the R22 proposal, point 5. *[2026-10-22, choice 251: reversed. The owner's bypass is "for pull requests only" on both repositories (NOTES §57)]*
    6. **C3 and C1 are both kept,** for different failures: C3 when a check the automation posts cannot satisfy a required check (it still needs the App), C1 when the App itself does not work. Annotated: decision 36, point 7; R22's row; the R22 proposal, point 7.
243. **No page kept by hand states a count of the decisions or the notes** (the owner, "agree", then "yes, build the docs-lint count check"):
    - `CLAUDE.md` line 3 drops "34" ("records the settled choices"; the owner's edit, on `main` at `f2b1522`) and `README.md` drops "29" (PR #281);
    - docs-lint gains check 9: `README.md`, `CLAUDE.md` and `docs/OPERATING_MODEL.md` fail on a count such as "N settled decisions", a correct one included (`tasks.py` `count_problems`, `tests/test_docs_lint.py`; `docs/proposals/docs-lint-checks.md`, "Check 9"). No plugin version.

## Proposed edits for the owner
| Link | Row | What is there now | What it must become |
|---|---|---|---|
| [CLAUDE.md](https://github.com/luissiviero/sdlc-framework/blob/main/CLAUDE.md#L3) | 3 | `` `docs/decisions/index.md` records the 34 settled choices — do not reopen them without asking. `` | `` `docs/decisions/index.md` records the settled choices — do not reopen them without asking. `` |

The count is dropped rather than raised (the owner, 2026-10-20): the index is generated and checked by docs-lint, so the number only went stale, and each new decision cost a guardrail edit. The same stale count in `README.md` ("The 29 settled decisions") is fixed in this PR. *[2026-10-20: the owner made this edit; `CLAUDE.md` line 3 reads "records the settled choices" on `main` at `f2b1522`. Choice 243 adds the check that keeps such a count out.]*

## Left
- **R15's decision file** (choice 242, point 1): with R15's second change's design.
- **The sample's bypass mode** (choice 242, point 5): at R22's setup on the sample, with a note.
- **The merge App** (choice 242, point 4): its creation and its environment join `/sdlc-init` step 6 when R22 is built, and R21's desktop-only table when both are built (the R22 proposal's settle row).
- Every other open item is in the session file of `ccr-8913e578-kwfegl`.

## Checks (this repository)
On the final head, after `python -m pip install -e ".[dev]"`, chained with `set -o pipefail`: the four commands of `HANDOFF.md`'s standing precondition 1, plus `python tasks.py docs-lint`. Their output is in the PR.
