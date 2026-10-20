# Item 11, Part 1: the read of the sample's first real detection (change 0013)

Written on 2026-10-14 by the item-11 session (branch `ccr-4a548fe6-7cqzlo`), from `docs/handoffs/2026-10-14-item-11-prompt.md` (on `main` since PR #197) and the owner's rulings D1 to D3 (`docs/handoffs/sessions/2026-10-14-ccr-15574406-xqm2bq.md`). Read only: nothing was pushed to the sample, no run was approved or dispatched on it, and none of its PRs was commented on or closed. Nothing under `plugin/` or `template/` changed in Part 1 *[Part 2, in the same PR, changes `plugin/pr/description.py` and `plugin/release/notes.py` (G1) and bumps the plugin to 1.0.0]*. Times are UTC.

## 1. Before anything else

| Check | Result | Evidence |
|---|---|---|
| `HANDOFF.md`, the newest session file and the files it builds on | Read: `2026-10-14-ccr-15574406-xqm2bq.md` (on `main` since PR #198); `2026-10-14-ccr-afc4a290-isvaf0.md` on its branch at `3e714e2` (PR #196, still open, draft); `2026-10-14-ccr-2723d779-08vouq.md`, `2026-10-14-ccr-e0c2918e-as946g.md`, `2026-10-14-ccr-207169b6-odl5m1.md`, and `2026-10-14-ccr-bddc73de-kyyw0b.md` (named and read by the newest file) | `ls docs/handoffs/sessions/`; `git show origin/ccr-afc4a290-isvaf0:docs/handoffs/sessions/2026-10-14-ccr-afc4a290-isvaf0.md` |
| Both repositories in scope | Yes | the session's scope; reads on both below |
| No other session has started item 11 | Verified at 08:33: the newest framework PRs are #198 and #197 (merged 08:25 and 08:32), #196 (draft, the cross-session review) and #187, #186, #173; the newest sample PR is #60 | `list_pull_requests`, `state: all`, both repositories |
| `main` | `ae4cc25` (PR #197 merged), plugin **0.3.8** (`.claude-plugin/plugin.json:4`, `marketplace.json:11`), tag `v0.3.8` on `e89649a`, no `v1.0.0`, root pin **0.3.6** (`sdlc.yaml:98`) | `git ls-remote --tags origin`; the files |
| The sample | `main` at `78abbb0` (unchanged since 2026-10-13 07:26), pin **0.2.30** (`sdlc.yaml:77`), PR #60 open | `git fetch`; `get` on PR #60 |

## 2. The read

| What | Result | Evidence |
|---|---|---|
| **The Detect step** of the dispatch run 38498439762 (created 01:56:58, `workflow_dispatch` by luissiviero, `ref=v0.2.30`, `claude_code=2.1.278`, `FORCE_TIER` empty) | `outcome: "filed change 0013"`, `forced: false`, `metric: ci_test_failure_rate`, `rule: we1`, `rules_hit: [we1]`, `tier: 3`, `action: propose`, `mean 0.006493506493506493`, `sigma 0.021536524612697398`, `sigmas 18.271587481412478`, `observations 19`, `runs_total 69`, `since 2026-09-12`, `window_days 30`, `latest {at: 2026-10-13, value: 0.4, runs: 5, failed: 2}`, `breach_start 2026-10-13`, `signature 68b6897ece2328d6`; reason "tier 3 by we1 (rules hit: we1): latest value 0.4 is 18.27 sigma from the mean 0.006494 (sigma 0.02154, 11 baseline point(s) over 30d, above); breach since 2026-10-13"; `filed` on `sdlc/0013/a` at `da45c85`, pushed | https://github.com/luissiviero/sdlc-sample-python/actions/runs/38498439762, job 115639451365, the Detect step (01:57:07–01:57:11) |
| **`detection.json`** | As §41 says: `forced: false`, `we1`, tier 3, 18.27 sigma, `n_baseline` **11**, `n_tail` 8, the eight tail points 2026-10-06 to 2026-10-13 (seven at 0, one at 0.4), the two failed run URLs, four breach-window commits (`c61007b`, `edc4f4b`, `7a7f739`, `78abbb0`), `at 2026-10-14T01:57:08Z` | `sdlc/0013/a` at `fd5e7ab`, `changes/0013-ci-test-failure-rate-breached-3sigma-we1/evidence/detection.json` |
| **The incident PR** | Sample PR #60, opened by `github-actions[bot]` at 02:01:02, labels `sdlc:f-ready` and `incident`, head `fd5e7ab`, base `78abbb0`, open, no comments. Its CI run 38498815186 waits at `action_required` (a bot-pushed head), so `mergeable_state` is `blocked` | https://github.com/luissiviero/sdlc-sample-python/pull/60; https://github.com/luissiviero/sdlc-sample-python/actions/runs/38498815186 |
| **The failed-run links** in the intent and the record | Both present and right: 38361544355 (PR #58's `pull_request` run on `c61007b`) and 38361643987 (the merge's `push` run on `edc4f4b`), both `failure` | `intent.md` Problem and Evidence; `actions_list` on the sample |
| **The diagnosis** | 35 turns, 0.679 USD, 201 s, `is_error: false`; one permission denial (a `Bash` probe of ruff's configuration under `$HOME`). Cause named right: ruff `PLR0133` at the `Lint` step on `tests/test_provocation.py`, `Test` skipped | `evidence/claude-f.json`; `intent.md` |
| **`gh run view --log-failed`** | The calls are confirmed, the denial is not: `hook-log.jsonl` records `gh run view 38361643987 --log-failed 2>&1 \| head -200` at 01:58:11 and the same with `head -300` at 01:58:16, both allowed by the hooks, then `gh run view` without `--log-failed` on both runs (01:58:20–01:58:30). The hook log keeps commands, not their output, and `claude-f.json` keeps the result only, so "egress to `results-receiver.actions.githubusercontent.com` is denied" is the diagnosis's own words (`intent.md` Evidence), not verified from a transcript. No transcript exists: BUILD_GUIDE step 41's transcript half is not built (`docs/progress/session-16.md`, line 10) | `evidence/hook-log.jsonl` (43 lines); `evidence/claude-f.json` |
| **The lint shape** | Handled: the diagnosis saw `Lint` fail and `Test` skipped, reproduced `PLR0133` by piping `c61007b`'s file through `ruff check --isolated`, and called the metric name "slightly misleading" because no test failed. `proposal.json`: route `pull_request`; `runbook:quarantine-flaky-test` ruled out (not intermittent, the test step never ran), `runbook:revert-pr` ruled out (already reverted by #59), `runbook:rollback-deploy` ruled out (no deploy). Gate (f): `wait`, all seven checks ok | `evidence/proposal.json`; `evidence/gate-f.json` |
| **`evidence/runbook-*.json`** and runbook PRs | None: no runbook ran and no runbook PR exists. Check 19 (a rollback live) is **not** proven by this read | `git ls-tree` of `sdlc/0013/a`; the sample's PR list |
| **The route step** | `dispatch.outcome: "pull_request: this intent PR is the route"`, evidence commit `fd5e7ab`, gate (f) `wait` | the job's "Dispatch the route, run gate (f) and open the intent PR" step (02:01:00–02:01:05) |
| **`status.yaml`** on `sdlc/0013/a` | `phase: f`, gate `f/passed` "waiting for the owner at gate (f)", `iterations: 0`, not abandoned | the file at `fd5e7ab` |
| **The duplicate check**, the owner's dispatch run 38531213086 (07:52:30, `ref=v0.2.30`, `FORCE_TIER` empty, PR #60 open) | As expected: `tier: 3`, `rule: we1`, `forced: false`, `filed: {}`, `open_incidents: [{change_id: 0013, ref: origin/sdlc/0013/a, signature: 68b6897ece2328d6}]`, `outcome: "open incident 0013 already carries ci_test_failure_rate"`; every step from setup-node to the route step skipped. `observations` read 20 (2026-10-14's scheduled `CI` run 38521399931 at 06:18 is counted, then dropped from the judgment as an incomplete day: the mean, sigma and 11 baseline points are unchanged) | https://github.com/luissiviero/sdlc-sample-python/actions/runs/38531213086, job 115743286263 |
| **Today's scheduled detect run** | Not started at 08:37 (the two newest `sdlc-detect.yml` runs are the dispatches); not waited for (D1) | `actions_list` on `sdlc-detect.yml` |
| **The digest that followed** | Not run yet. The last digest, run 38411867308 (2026-10-13 14:15), predates the detection; its issue #8 lists #55, #56 and #57 only. The next scheduled digest (its runs started 12:36–15:31 on 2026-10-10 to 2026-10-13) is the first to list #60; Part 2 reads it if it has run | https://github.com/luissiviero/sdlc-sample-python/actions/runs/38411867308; issue #8 |

**Correction to the intent** (the diagnosis's words, not a framework defect): "reverted on `main` 3 minutes after it merged" is wrong. 3 min 10 s is the revert *commit* `7a7f739` on its PR branch; the revert reached `main` when PR #59 merged at 07:26:39, 10 min 5 s after PR #58's merge at 07:16:34 (verified, `list_pull_requests` on the sample). The breach-window commit list carried the merge `78abbb0` with its time; the diagnosis read the wrong line.

## 3. The gaps the read found

| # | Gap | Evidence | Proposed fix | Proposed test | Recommendation |
|---|---|---|---|---|---|
| G1 | **The intent PR's "Proposed outcome" stops mid-sentence.** `_first_sentence` takes the first physical line of the section and looks for a sentence end in it; a hard-wrapped paragraph gives half a sentence. PR #60 reads "No design-phase code change is required: the commit that caused the breach was already" and stops. The same helper builds the release note's "What changed" | PR #60's body, line 2, against `intent.md` lines 15–17; `plugin/pr/description.py:154-165` and `plugin/release/notes.py:74-84` on `main`; reproduced on `main`'s code (the call returns the same cut string) | Join the first paragraph (lines up to a blank line, a heading or a list item) before taking its first sentence, in both helpers (or one shared helper) | `tests/`: an incident intent whose first sentence wraps over two lines gives a PR body whose "Proposed outcome" line holds the whole sentence; the same for the release note; a one-line sentence and a list item still give what they give today | Fix in the 1.0.0 PR |
| G2 | **Commit times in `detection.json` keep the committer's offset** (`2026-10-13T04:16:33-03:00`), while every other time in the record and the run is UTC (`Z`). It did not cause the timing error above (the diagnosis converted correctly), so the read shows it as an inconsistency, not a failure | `detection.json` `commits[].at`; `plugin/detect/cli.py:211` (`--format=%H%x1f%s%x1f%cI`) | Normalise each `at` to UTC `Z` where the commits are listed | A commit made with a `-03:00` committer date is listed with the same instant in `Z` | Optional; my lean is to leave it out of 1.0.0, because it touches `plugin/detect/`, which the read just certified unchanged since 0.2.30 |

**Read and judged not to be gaps:**
- The metric's name: `ci_test_failure_rate` counts a run's conclusion, whatever step failed (`plugin/detect/source.py`, the module docstring: "A run counts when it completed with `success` or `failure`"). The name comes from decision 15. A lint failure counting is as written, and the diagnosis said so.
- `status.yaml` reads gate `f/passed` while `gate-f.json` reads `wait`: the status file's vocabulary, with the reason "waiting for the owner at gate (f)".
- "Counters: first-pass merge: yes" on an unmerged PR: the indicator is `iterations == 0` (`plugin/pr/description.py`, `_counters_line`).
- No transcript to confirm the log denial from: a known unbuilt item (step 41's transcript half), not new.

## 4. The port list and what the read did not exercise

The sample ran **0.2.30**, so the read certifies 0.2.30's detect path. `main`'s history restarted at PR #126 (`v0.2.30` is not an ancestor of `main`: `git merge-base --is-ancestor`), so the list comes from the records' "Port list (choice 138)" lines, checked against a content diff (`git diff v0.2.30 origin/main`). *[2026-10-20, docs review: `v0.2.30` (`6ff3af9`, PR #93) is an ancestor of `main` (`git merge-base --is-ancestor v0.2.30 origin/main` is true on a full clone); the port list still holds.]*

| PR | Version | Detect-path files it touched | Record |
|---|---|---|---|
| #98 | 0.3.0 | `plugin/ci/run_phase.py` (the gate's commands after the session); `sdlc-fix.yml` (`timeout-minutes` 150 → 200) | `docs/progress/session-15.md:8` |
| #101 | 0.3.1 | `run_phase.py` (the change-0000 guard skip, `record_spend`) | `docs/progress/session-16.md:10` |
| #107 | 0.3.2 | `run_phase.py` (`DEFERRED_GATE_SKIP` wording, the head-ref lookup in `apply_owner_labels`); `sdlc-fix.yml` (F2's header paragraph) | `docs/progress/session-18.md:11` |
| #110 | 0.3.3 | `run_phase.py` (`session_env`: background tasks off) | `docs/progress/session-18-sitting-2.md:9` |
| #130 | in 0.3.6 | `run_phase.py` (the push check, `fix_branch_for`, `dispatch_head`, the result's `branch`) | `docs/progress/2026-10-08-runner-push-check.md:12` |
| #152 (change 0002) | 0.3.7 | `run_phase.py` (`ci_settings_file`, `_deny_write_entries`); `plugin/ci/settings.ci.json` | `docs/progress/session-25.md:10`; `session-26.md:11` |
| #194 | 0.3.8 | `plugin/ci/settings.ci.json` (allows `results-receiver.actions.githubusercontent.com`) | `2026-10-14-ccr-2723d779-08vouq.md:11` |

The content diff agrees: `plugin/detect/`, `sdlc-detect.yml` and `sdlc-runbook.yml` are identical in 0.2.30 and on `main`; `run_phase.py` (548 lines added, 41 removed), `sdlc-fix.yml` (10 added, 1 removed) and `settings.ci.json` (5 added, 1 removed) changed (`git diff --numstat v0.2.30 origin/main`).

**What the read did not exercise in 1.0.0:**
- every `run_phase.py` change above, as the detect workflow's "Run phase (f)" step runs it: the push check, `session_env`, `record_spend`, the deny-write entries of `ci_settings_file`;
- PR #194's sandbox log host: it ships in 1.0.0, but the sample runs 0.2.30, so no diagnosis has fetched a log through it. Whether `gh run view --log-failed` asks for that host or for the job-log blob host is still not verified (NOTES §41);
- the `sdlc-fix.yml` changes (no fix round ran on #60) and the runbook workflow (no runbook ran);
- a rollback (check 19), a runbook PR, and a failing *test* (the provocation failed at lint).

## 5. Decisions for the owner

*Answered on 2026-10-14: decisions 2, 3 and 4 as recommended, G2 moved to ROADMAP R16 (days counted in the owner's -03:00 offset, after 1.0.0), and the root pin as reading B, on the session's recommendation. The record is `docs/PROGRESS.md`, choices 183 to 187.*

| # | Decision | Options | My recommendation |
|---|---|---|---|
| 1 | **The root pin** (`sdlc.yaml:98`, now 0.3.6) after `v1.0.0` | **Reading A**, ROADMAP row 12: both pins to 1.0.0 right after the tag (the root's line 98 and the sample's line 77). **Reading B**, the session files since session 26 (`2026-10-13-session-26.md`, line 16): the root pin stays at 0.3.6 until the sandbox proof (evals case 0006 green in one sandboxed `Framework evals` run, a plain PR after the read), then moves straight to the newest tag; the sample's pin moves in row 13's upgrade PR either way. A runs this repository's own phase runs on 0.3.7's deny-write rewrite and 0.3.8's log host before either is proven live; B keeps ROADMAP row 12's text wrong until annotated | None, as the prompt asks. Whichever you pick, I annotate ROADMAP row 12 to match in Part 2 |
| 2 | **Version numbers after 1.0.0** | Choice 180's "runs PR as 0.3.8, R7 as 0.3.9" cannot stand: #194 took 0.3.8 and this PR takes 1.0.0. (a) Keep the order and shift into 1.0.x: the runs PR 1.0.1, R7 1.0.2, every later number by one. (b) No reserved numbers: each PR under `plugin/` or `template/` takes the next free patch number when it is next to merge, and the order stays in ROADMAP's Order column | (b). Reserving numbers ahead has already collided twice (#194 against the runs PR, change 0005's slot in #187). A red `main` run on the 1.0.0 merge then takes 1.0.1 without renumbering anything |
| 3 | **The triage of sample PR #60** (choice 69); no runbook PR exists | (a) **Close without a comment**: the abandon workflow marks 0013 abandoned on its branches; no dismissal; `open_incidents` stops counting it. (b) **Close with a comment**: abandoned, plus a dismissal PR on `sdlc/0013/dismiss`; once you merge it, the signature `68b6897ece2328d6` mutes `ci_test_failure_rate`/`we1` for one baseline window (to about 2026-11-13), because the signature is `detect\|metric\|rule` with no date in it (`plugin/detect/finding.py:35-37`). (c) **Label `schedule`**: stays open, and an open incident mutes the metric (`open_incidents`). (d) **Merge** (fix now): first approve CI run 38498815186; the design run then starts on an intent that proposes no code, and the metric stays muted until 0013 ships or is abandoned | (a), after this PR merges (the freeze, D3) and before the sample's upgrade PR. The incident is resolved by #59; (b), (c) and (d) would each keep the next provocation (`we1` on the same metric) from filing |
| 4 | **Which gaps go in the 1.0.0 PR** | G1 only; or G1 and G2 | G1 only |

## 6. Annotations this PR makes (choice 126), no rewrite

- Choice 138 (`docs/progress/2026-10-02-between-sessions-14-15-sitting-2.md`, line 13): the owner's ruling D3 beside it.
- ROADMAP row 10 (`docs/ROADMAP.md`, line 51): the same ruling, the start-time window corrected (13:31 on 2026-10-12, read by session `ccr-15574406-xqm2bq`), `n_baseline` 11 not 8, and the duplicate check.
