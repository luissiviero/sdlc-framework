# Progress — item 11 (2026-10-14): the sample's first real detection read (change 0013, filed by the owner's dispatch), one gap fixed with its tests, plugin **1.0.0**

This session ran the item-11 prompt (`docs/handoffs/2026-10-14-item-11-prompt.md`, on `main` since PR #197) with both repositories in scope, on branch `ccr-4a548fe6-7cqzlo`, PR #199. The sample was only read: nothing was pushed to it, no run on it was approved or dispatched, and none of its PRs was commented on or closed. The freeze of choice 138 ends when PR #199 merges (the owner's ruling D3).

## Summary
- **The read (ROADMAP row 10)**, in full in `docs/handoffs/2026-10-14-item-11-part-1-read.md` and as facts in NOTES §42. Change 0013 was filed by the owner's `workflow_dispatch` run 38498439762 (`forced: false`, tier 3, `we1`, 18.27 sigma, 11 baseline points, 2 of 5 runs failed on 2026-10-13), which opened the sample's PR #60 (`sdlc:f-ready`, `incident`). The tier-3 diagnosis named the cause right (ruff `PLR0133` at the `Lint` step, `Test` skipped) and chose the route `pull_request`, ruling out all three runbooks with reasons; gate (f) `wait`, all seven checks ok. No runbook ran, so check 19 (a rollback live) is not proven.
- **The duplicate check** (the owner's dispatch run 38531213086, PR #60 open): tier 3 logged, `filed: {}`, 0013 named as the open incident. The scheduled run of 2026-10-14 and the first digest after the detection had not run when the read was made.
- **`gh run view --log-failed`**: the hook log keeps the diagnosis's two calls (01:58:11 and 01:58:16 UTC); no file keeps their output, so the denied host stays the diagnosis's own words (NOTES §41, §42).
- **G1, fixed in this PR**: the incident PR's "Proposed outcome" stopped at the first line's end (PR #60: "… the commit that caused the breach was already"). `_first_sentence` in `plugin/pr/description.py` and its copy in `plugin/release/notes.py` now read the first paragraph or list item whole. A code fence ends the paragraph and a leading fenced block is skipped (found by the fresh-context review: joining lines would have pulled a fence after a spec's first sentence into it). Tests: `test_phase_f_proposed_outcome_keeps_a_sentence_wrapped_over_lines` and `test_first_sentence_reads_the_whole_first_paragraph` (nine cases, run against both helpers) in `tests/test_pr.py`, `test_notes_what_changed_keeps_a_sentence_wrapped_over_lines` in `tests/test_release.py`; the wrapped cases failed on 0.3.8's code, the fence cases on the first version of the fix, and all pass on 1.0.0.
- **G2, not in 1.0.0**: the breach-window commits keep the committer's `-03:00` while every other time is UTC. The owner chose to count the detection's days in their own offset instead, after 1.0.0: ROADMAP **R16**, `docs/proposals/detect-local-day.md`.
- **The bump**: `.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json` from 0.3.8 to **1.0.0**. Files under `plugin/`: `plugin/pr/description.py`, `plugin/release/notes.py`. Nothing under `template/`.
- **Port list (choice 138)** and what the read did not exercise: the Part 1 file, section 4. The sample ran 0.2.30; `plugin/detect/` and the detect and runbook workflow templates are identical in 0.2.30 and 1.0.0. Not exercised: the `run_phase.py` changes of PRs #98, #101, #107, #110, #130 and #152, the `sdlc-fix.yml` changes of #98 and #107, and the CI sandbox's log host of PR #194 (0.3.8). This PR touches nothing on the detect path.

## The owner's decisions (2026-10-14)
183. **Sample PR #60 is closed without a comment**, by the owner, after PR #199 merges and before the sample's upgrade PR (choice 69). A close with a comment would write a dismissal, and a detect signature carries no date (`detect|metric|rule`), so it would mute `ci_test_failure_rate`/`we1` for a baseline window; labelling it `schedule` or merging it would keep the metric muted through `open_incidents`. Either would stop the next provocation from filing. No runbook PR exists.
184. **No version number is reserved after 1.0.0.** Each PR that changes `plugin/` or `template/` takes the next free patch number when it is the next to merge (1.0.1, 1.0.2, …); the order of the work stays in ROADMAP's Order column. This replaces choice 180's "the runs PR as 0.3.8, R7 as 0.3.9" (0.3.8 went to PR #194). A red `main` run on the 1.0.0 merge takes the next number as its fix.
185. **The 1.0.0 PR carries G1 only.** G2 does not go in, because it would change `plugin/detect/`, which the read certified unchanged since 0.2.30.
186. **Detection days in the owner's offset (-03:00) become ROADMAP R16**, after 1.0.0 (the owner's answer to G2). Its order is not placed.
187. **The root pin waits for the sandbox proof** (reading B, as the session recommended). After `v1.0.0` the root pin (`sdlc.yaml:98`) stays at 0.3.6 until one sandboxed `Framework evals` run passes with case 0006 (the sandbox proof, a plain PR after the read), then moves straight to the newest tag. 0.3.7's deny-write rewrite and 0.3.8's log host are not yet proven in a live sandboxed run here, and change 0005's build is this repository's next phase run. The sample's pin moves to 1.0.0 in its upgrade PR (ROADMAP row 13) as planned. ROADMAP row 12 is annotated, not rewritten.

## Checks (this repository)
On the final head, in a virtual environment with `pip install -e ".[dev]"`, chained with `set -o pipefail`: the four commands of `HANDOFF.md`'s standing precondition 1, their output in the PR.

## The Milestone's PR list (ROADMAP row 14)
Read on 2026-10-14 with `list_pull_requests`, `state: all`, on both repositories.

| Repository | Merged | Closed without a merge | Open |
|---|---|---|---|
| `luissiviero/sdlc-framework` (187 merged before this PR) | #1–#23, #25–#45, #47–#65, #69–#70, #73–#90, #92–#147, #149–#172, #174–#185, #187–#198, and #199 (this PR) when it merges | #46, #148 | #173 (change 0004's intent, draft), #186 (change 0005's design, `sdlc:b-ready`) |
| `luissiviero/sdlc-sample-python` (46 merged) | #2–#7, #9–#19, #21–#24, #27–#29, #31–#33, #36–#46, #48–#50, #52–#54, #58–#59 | #1, #25, #26, #30, #34, #35, #47, #51 | #55, #56, #57, #60 (incident intents at `sdlc:f-ready`) |

The numbers missing from each list are issues (framework: #24, #66, #67, #68, #71, #72, #91; sample: #8, #20). A GitHub Milestone holds one repository's PRs: the framework's list is the Milestone's; the sample's stays here.

## Left
- **The owner**: approve PR #199's runs if they wait; merge it when all three `Framework checks` jobs are green on its final head and the branch is up to date with `main`; then close sample PR #60 without a comment (choice 183).
- **Part 3, after the merge** (ROADMAP rows 12, 13 and 15): `v1.0.0` on the merge commit, the `main` run of the merge green, the sample's pin row (the root pin waits for the sandbox proof, choice 187), the sample's upgrade PR with one dispatched detect run at `v1.0.0`, the 1.0.0 tables closed. Row 14 (the Milestone) is the owner's.

## Part 3 (2026-10-14, from 11:50 UTC): after the merge
PR #199 merged at 09:55:34 UTC as `e02e085`. Part 3 ran on the owner's word, in the order of their rulings D-A to D-D (`docs/handoffs/sessions/2026-10-14-ccr-5b7d20dc-ot5xgy.md`, PR #201).

- **`v1.0.0`** is on `e02e085` (verified, `git ls-remote --tags origin`), tagged by run https://github.com/luissiviero/sdlc-framework/actions/runs/38545917596 (read by session `ccr-5b7d20dc-ot5xgy`). The `main` run of `e02e085`, https://github.com/luissiviero/sdlc-framework/actions/runs/38545917551, ended `success` at 10:12:31 UTC (verified, `get_workflow_run`). No 1.0.1 is owed.
- **Today's scheduled detect run** (verified, https://github.com/luissiviero/sdlc-sample-python/actions/runs/38550795354, job 115807971304, created 10:36:49 UTC, `ref=v0.2.30`): tier 3, `we1`, `forced: false`, `filed: {}`, `open_incidents` 0013, `outcome: "open incident 0013 already carries ci_test_failure_rate"`. NOTES §43.
- **The sample's upgrade, prepared and not pushed**: its fourteen SDLC files are unedited 0.2.30 copies; seven change at 1.0.0 (the build, deploy, design, fix, release and test workflows and `lessons/README.md`). 1.0.0's own `sdlc_init.py`, run on a scratch copy, reports the same workflows outdated, `sdlc.yaml` changed only on the pin line, leaves `.claude/settings.json` and `CLAUDE.md` unchanged, and keeps `REVIEW.md` (create-only), whose one changed rule at 1.0.0 is the owner's guardrail edit. The sample's build, test and lint pass on the upgraded tree (`9 passed`, `All checks passed!`). NOTES §43.

## The owner's decisions (2026-10-14, Part 3)
188. **Sample PR #60 is closed after today's scheduled detect run and today's digest have both run** (D-A), and before the sample's upgrade PR (choice 183). A close before the detect run would have let it judge 2026-10-13 with no open incident and file a duplicate; a close before the digest leaves #60 out of every digest.
189. **ROADMAP row 13's dispatched detect run at `v1.0.0` happens on 2026-10-15 or later** (D-B), after #60 is closed. Expected: no rule fires and nothing is filed (2026-10-14's counted runs passed).
190. **The item-11 session annotates the stale lines in its ROADMAP-closing PR** (D-C): `docs/ROADMAP.md` lines 66, 76, 77 and 81 and `docs/decisions/28.md:27` (the "0.3.8 runs PR" and "R7 ships as 0.3.9", superseded by choice 184); `docs/notes/39.md:55` (the detect start window); `docs/ROADMAP.md:51`'s "was denied by the CI sandbox" (not verified). Done in this PR, beside each sentence (choice 126).
191. **PR #200, then PR #201, are merged** (D-D) before the ROADMAP-closing PR.
