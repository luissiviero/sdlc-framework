---
type: Review
title: "The judge: Study A and Study B compared blind, disputed claims checked against the code"
description: An independent judge on a different model from Study B's writer compared the two R60 studies blind to their authorship, checked each disputed claim in both repositories, and wrote a verdict per item and one merged recommendation; the mapping of the blind names is at the end.
status: report
roadmap: R60
sources:
  - id: study-a
    resource: docs/reviews/2026-10-20-lifecycle-axis-ports/study-a.md
    title: "Study A, recorded from the comparison doc"
  - id: study-b
    resource: docs/reviews/2026-10-20-lifecycle-axis-ports/study-b.md
    title: "Study B, the independent study"
generated: { by: claude-code-session, at: 2026-10-20T07:30:00Z }
---

# The judge's verdict on Study A and Study B

**How the judge ran.**
- **Who.** A fresh subagent that wrote neither study. It ran on Fable 5.1, a different model from the one that wrote Study B (Opus 5.5) and that prepared this file.
- **Inputs.** It received two blind copies, "Study X" and "Study Y", made in the session's scratchpad. The order was drawn at random (`secrets.choice`).
- **Repositories.** It had read access to both: `lifecycle-axis-` at `80328c1` and this repository at `main` `dc40d61`.
- **Kept out of reach.** This folder, the handoff session file that mentions Study A, the comparison doc, PRs #268 and #270, and the branch's history after `dc40d61`.
- **Its rubric:**
  - factual accuracy, with every disputed claim checked against the code;
  - fit to the owner's weighted criteria;
  - consistency with the settled decisions and the playbook study's decided rows;
  - cost and complexity for small projects;
  - concreteness of the proposed change.
- **Its report.** It is reproduced below unchanged, from its first heading to its list of files checked.

**What was stripped to make the copies blind:**
- each file's front matter;
- each study's own name in its title;
- Study A's recording header, its byline (date and author chip) and its "ROADMAP entry: R60" section, which describes the two-study process and names itself Study A;
- the word "chat" in Study A's chart caption, and its summary's sentence about R60 asking for a second study;
- Study B's "Contamination" paragraph, which names Study A.

Nothing else was changed in either copy.

**The judge's note on blindness.** The judge reports one channel it could not avoid. R60's proposal file, which it read for context, describes how each study was made, and the two copies' sources and method sections fit those descriptions. It says it did not use that guess. The verdicts rest on the code.

---

# Judge report: Study X vs Study Y on what lifecycle-axis- does better

Judged against sdlc-framework at `main` dc40d61 (the working tree of branch ccr-d901d09c-s87xed differs from dc40d61 only by the two review files I was told not to open; `git diff --stat dc40d61 HEAD` lists exactly those two) and lifecycle-axis- at 80328c1 (a shallow clone, 180 commits, grafted boundaries). Weights: Safety 1, Attention 3, Autonomy 3, Audit 2, Cost 0, Article 2 (`docs/reviews/2026-09-28-playbook-vs-framework.md:111`, verified).

Blindness note: I opened neither forbidden path. `docs/proposals/lifecycle-axis-features.md` (R60, which I had to read for context) describes Study A as "a chat session of 2026-10-19/20 (comparison doc)" and Study B as a new session committed before reading A. Study X's Sources ("cloned on 2026-10-19", plugin 1.0.13, an "[embedded content: Scores …]" chart) and Study Y's method ("This repository is at dc40d61", five subagents) let one guess which is which. I did not use that guess; every verdict below rests on the code.

## 1. Verdict in five bullets

- **The studies barely overlap.** Of 16 merged items, only two are shared (the delegation grant / merge-by-silence extras; Gemini). Study X profiles the kit's big mechanisms and finds most already covered; Study Y profiles the kit's records and lessons and finds eight small ports. Both are right about their own ground, and Y's method (score the delta over `main` plus accepted candidates) is the correct one; X double-counts the value of R52 and R39 in its two top scores.
- **Port, folded into accepted candidates (score 6–8 each):** the plan's growth after approval shown in the banner (R24), the merge-by-silence extras: per-change grant, locked-path floor, "merged-unread" record (R52), the incident eval case seen red at the merge base (R35, narrower than Y claims), a repeated gate failure proposing a CLAUDE.md line (R37), CLAUDE.md line budget and retirement candidates (R37/R26), a post-merge staging command before the release label (R39, an option, not X's environments list), and an Actions-minutes meter on private repositories only (R25/R61).
- **Small, cheap ports (score 2–4):** SHA-pinned actions in the template (R44 or a template PR), the writer's and reviewer's model on R11's record lines, the release label bound to the head it was applied on (R13/R11), metrics labelled by play in R26's table, an optional `revisit:` field on decisions reported by R58's lint.
- **Don't port:** Gemini parity (both studies agree; R8 stays as is), a serial run-queue as the default (Study X; it reopens accepted R51 and the owner's choice 234), multi-approver roles (reopens the x-roles decision), local-session execution (reverses decision 1), the kit's YAML eval format, the per-SHA release file.
- **Defects found:** X's #3 reshapes the deploy block the owner's deploy-envs decision explicitly kept (one adapter, `production` as the switch); X's #2 makes serial the default against accepted R51; X's counts are slightly off (18 lessons not 19, 7 eval cases not 6). Y's one bad citation: commit `e227ed6` is the shallow clone's grafted boundary and its diff *adds* the pointer line it says was deleted (the deletion is real, its commit is not identifiable in this clone). Y overstates L1: "red at base" is satisfied trivially by a case whose test file does not exist at the base, and prompt-driven cases cannot be checked without the model. Neither study saw authorship; neither reopens a settled decision knowingly.

## 2. Item map

| # | Merged item | Study X | Study Y | Agree? |
|---|---|---|---|---|
| 1 | Per-change delegation grant, locked-path floor, "merged-unread" record (merge by silence) | #1 Delegation grant | L5 | partly (same target R52; X scores it against `main`, Y against R52) |
| 2 | Environment tiers: a staging step between merge and the release label | #3 Environment tiers | — (not listed) | only X |
| 3 | Serial run-queue | #2 Serial run-queue | §4 "not counted" | no |
| 4 | Gemini: parity (no) vs reviewer (R8) | #7 | L10 | yes |
| 5 | Release authorization bound to a commit | #4 SHA-bound release | — | only X |
| 6 | Plan as a hard boundary / the plan's growth after approval | #5 (already covered) | L4 (growth is a gap) | partly |
| 7 | Evals: deterministic suite / an eval case seen failing | #6 (already covered) | L1 | partly |
| 8 | Metrics per play (leading + lagging) | #9 | — | only X |
| 9 | Multi-approver roles | #10 | — | only X |
| 10 | Local-session execution | #8 | §5 (observation only) | only X (Y agrees the CI design is better) |
| 11 | CLAUDE.md: enforcement note, retirement, line budget | — | L2 | only Y |
| 12 | A repeated gate failure proposes a CLAUDE.md line | — | L3 | only Y |
| 13 | GitHub Actions minutes measured and budgeted | — | L6 | only Y |
| 14 | A decision carries a revisit trigger | — | L7 | only Y |
| 15 | Third-party actions pinned by SHA | — | L8 | only Y |
| 16 | Writer and reviewer model on each record line | — | L9 | only Y |

## 3. Per item

Scores are mine, in the order S / At / Au / Ad / C / Ar, weighted 1/3/3/2/0/2.

### Item 1. Per-change grant, locked-path floor, merged-unread record (X #1, Y L5)

- **X says:** port the kit's `mode: delegated` grant into R52 as a second trigger: an intent with `Autonomy: delegated` lets the App merge the green build PR at once, voided by "Decisions taken for you", a risk hit or a declared production; opt-in `sdlc.yaml: delegation: off | low`. Score 11.
- **Y says:** fold into R52 three things from the kit: a per-change switch (a label at (a)/(b), read from the base branch like `profile_override`), a locked-path floor that policy cannot narrow (reusing `protected_paths.py`'s matcher, renames judged on both names), and a truthful record (`merged-unread` in R11's list, the printed `CONDITION` lines as a PR comment). Score 8.
- **Agree?** Partly: same candidate, complementary additions. They disagree on latency (X: zero wait on a grant; Y: R52's hours stay) and on the baseline.
- **What the code shows.** The kit: `delegation.yaml` delegates `risk-classes: [low]`, `signable` excludes `intent.md`, `max-deviations: 5`; `scripts/delegated_merge.py:86-94` `ALWAYS_LOCKED` floor, `:663-683` rename checked on `previous_filename`, `run()` reads the grant from `base_ref` (`contents/work/<slug>/intent.md?ref=<base>`), prints `CONDITION <name>` lines in order and merges with `commit_title "… (delegated)"`; `check_artifact_chain.py:371-442` `check_grant` refuses an agent-authored grant commit. Live: PRs #83, #100 and #112 were merged by `github-actions[bot]` (`work/approve-tap-regenerates-index/log.md:25-26`, `work/parked-marker-on-retired/log.md:21`, `work/chain-check-without-gh/log.md:24`). The framework: R52 is accepted "as a later step", its decision "written only at R50's trigger" (ROADMAP R52; `docs/proposals/speed-beyond-the-sprint.md:46-48`: conditions project-wide, the App merges after a set number of hours). `plugin/hooks/protected_paths.py:46-47` has the one spelling of the guardrail paths; `plugin/state/status.py:46-48` holds `profile_override`/`review_override` (Y cites `conventions.py`; the field lives in `status.py`, `conventions.py:56` only documents it: a harmless slip). Decision 30 already skips (a) for the owner's own intent and (b) for a routine plan, as X says. `plugin/skills/intent-template/SKILL.md` has no `Autonomy` field: X's field is new.
- **Who is right.** Y on the baseline: X's +2/+2 on Attention and Autonomy is R52's own value (the owner's read at (e) removed), which the owner already accepted. The port's delta is what Y lists. X's zero-latency grant is a real addition Y lacks: an explicit per-change grant written with the intent is a stronger consent than silence and costs the owner nothing extra at the moment they have most context. Y's floor and record are safety and audit the kit proved live; R52 as written has neither.
- **Merged recommendation.** Port adapted, fold into R52 (at R50's trigger, as R52 is timed): (i) a per-change switch, either an intent field the fast lane already reads as the owner's act or Y's label at (a)/(b), read from the base branch; on an explicit grant the wait may be zero (owner's choice, open question 2); (ii) the locked-path floor: a diff touching `.claude/**`, `CLAUDE.md`, `REVIEW.md`, `sdlc.yaml`, `protected_paths`, `.github/**` or `evals/**` never merges unread, renames on both names (R59); (iii) R11's line `{act: merged-unread, actor: <App>, conditions: [...]}` and the printed conditions on the PR. Not ported: signatures in front matter, the tap, the queue, the deviation cap.
- **Score:** +1 / 0 / +1 / +2 / 0 / 0 = **8**. Confidence: high on the facts, medium on the value (R52 has no live run yet; the kit's own advance step was broken in production until `work/advance-push`, which argues for R52's measure-first placement, as Y notes).

### Item 2. Environment tiers (X #3)

- **X says:** generalise R39's single preview into an ordered `deploy.environments` list with `agent_may` per entry; paper deploys on merge, live waits for `sdlc:release-approved`; default one environment. Score 12.
- **Y says:** nothing (not listed, not in §4).
- **What the code shows.** The kit: `.sdlc/environments.yaml` has three tiers with `agent_may` and `approval`; `scripts/deploy.sh:75-101` refuses unless `RELEASE_APPROVAL` or `.sdlc/release-authorizations/<HEAD>` equals HEAD; the deploy command itself is a placeholder (`deploy.sh:112-115`, prints "would run"), so the tiers were never exercised against a real environment. The framework: `template/sdlc.yaml:59-83` one `deploy` block, `production` the one switch, one `command` run after the merge and, when production is true, after the label (decision 13). R39 (accepted 2026-10-16) adds `deploy.preview_command` at each (e) head before the approval, plus the rehearsed rollback (`docs/proposals/preview-environment.md`, "The proposal" 1-7). The crosswalk row `deploy-envs` reads "better: playbook, decision: blend", and its note says "The one deploy adapter … and deploy.production as the production switch stay (D13, D19)" (crosswalk.json, row deploy-envs; also `target-design.md` T20). Decision 19 (sticky) is the per-project adapter.
- **Who is right.** X is right that the article tiers autonomy by environment (p.40 step 5) and that R39's preview is the dev tier. X is wrong to present an environments list as a generalisation of R39: the owner's deploy-envs decision kept the single adapter and the `production` switch, so the list reshapes a decided row. The one thing neither R39 nor decision 13 gives is a *post-merge* step before the label: today, with `production: true`, nothing deploys until the label; R39's preview runs before the merge. "Paper on merge, live on label" is that gap, and for a trading project it is the natural promotion path (decision 19 already names "promote to paper trading" as an action).
- **Merged recommendation.** Port adapted, as an option inside R39's design: an optional `deploy.staging_command` (name with R45) run by the release workflow on the (e) merge, before and independent of the label; `deploy.command` stays the production step; `agent_may` is not ported (no Claude session deploys in the framework, stricter than the article, R39 point 7). Keep the adapter's shape. Small projects: unset, no change.
- **Score:** +1 / 0 / +1 / 0 / 0 / +1 = **6**. Confidence: medium (the delta is real; whether the owner wants a post-merge tier beyond R39's pre-merge preview is open question 3).

### Item 3. Serial run-queue (X #2 vs Y §4)

- **X says:** make serial mode R51's first step and the default (`sdlc.yaml: queue: serial`, label `sdlc:queued`, a parked item skipped, the owner's un-park puts it back in line); R51's concurrency safety becomes the opt-in. Score 10.
- **Y says:** not counted: the framework runs every change in its own folder and branch concurrently, R51 (accepted) makes that safe, no single pointer is needed.
- **What the code shows.** The kit: `scripts/next_item.py:57-79` hands out one item (approved, `mode: delegated`, risk in policy, unstarted, not parked), oldest `delegated-on` first; `delegated_merge.py` `advance()` moves `.sdlc/active` after a merge, and `work/advance-push/intent.md` records that "no queue has ever advanced live" until that fix. The framework: R51 "Concurrent changes, safe by construction", accepted 2026-10-19 by the owner's choice 234 ("Several changes in flight, safely", `speed-beyond-the-sprint.md:37`), whose proposal says "The pipeline already runs several changes at once" and "On a real project: yes, in throughput" (`concurrent-changes.md:30-42`); every phase workflow keys its concurrency group on the work branch. Decision 17 cites p.25's ceiling for *parallel sessions on the owner's machine* (R50 says worktrees are "a local-checkout concern"), not for CI runs.
- **Who is right.** Y. Making serial the default reverses an accepted candidate and the owner's stated reason for it, and X's reading of decision 17 does not transfer to CI runs. X's practical point stands narrowly: R51's own text says one change at a time keeps the sample's results attributable, so an opt-in serial mode is cheap for small projects. But nothing enforces serial today and the sample has managed it by pacing; the cost of building a queue (a label, a pointer, a dispatch on merge) exceeds its value.
- **Merged recommendation.** Don't port as the default. At most, one row in R51's "What to settle": an optional `queue: serial` that the runner honours by waiting at the (b) dispatch while another change is past (b); no pointer file, no `sdlc:queued` label.
- **Score (as X proposes it, the default):** +1 / 0 / −1 / 0 / 0 / 0 = **−2**. Confidence: high.

### Item 4. Gemini (X #7, Y L10)

- **X says:** skip parity (−3); advance R8 as the reviewer (+3); later consider Gemini as the panel's devil's advocate.
- **Y says:** don't port the one-source render of CLAUDE.md/GEMINI.md/AGENTS.md (−2); R8 stays the only other-vendor use.
- **What the code shows.** The kit: `scripts/gen_context_files.py` renders three files under `MAX_CONTEXT_LINES=120` (`.sdlc/config.env:53`); `.gemini/settings.json` wires the same hooks; `knowledge/decisions/gemini-hooks.md:31-32, 91-96` records the personal-account refusal (`IneligibleTierError`) and that Antigravity is "the open roadmap item", so X's "Antigravity ignored the hooks" is a fair reading and live parity was never verified (Y). The framework: decisions 6, 7, 8; R8 proposed, "starts after R7 is measured on two changes", "never parks", a promotion "changes decision 11 or 21, so it is a new decision" (`external-design-check.md`). `template/sdlc.yaml:38-46`: the advocate already runs on a different model from the session and the reviewer (Fable vs Opus).
- **Who is right.** Both; they agree. X's "Gemini as the advocate" is premature: R8's own tally decides promotion, and decision 21's blind-spot argument is already met within one vendor; cross-vendor diversity is a plausible later step through R8's stated path, not a port.
- **Merged recommendation.** Don't port parity. R8 unchanged. Score of the "reviewer" form over the baseline is 0 (it *is* R8).
- **Score (parity):** 0 / −1 / 0 / 0 / 0 / −1 = **−5**; (reviewer via R8): **0**. Confidence: high.

### Item 5. Release authorization bound to a commit (X #4)

- **X says:** already covered by `plugin/release/approval.py`; at most record the head SHA at labeling in R11's list. Score +1.
- **Y says:** nothing.
- **What the code shows.** `plugin/release/approval.py:163-180` `_recorded_pr`: the label counts only when the checkout is the recorded build PR's head commit or its merge commit, read by PR number from `status.yaml: build_pr`; a bot's label never counts (`:121-126`). The kit's `deploy.sh:92-101` compares the authorization to HEAD exactly. R11 already gives each act line "the head commit" (`approvals-list.md:64`). The gap X names is real: the label stays on the PR when a fix round pushes a new head, and `approval.py` checks the actor, not the head the label was applied on.
- **Who is right.** X, with one refinement: under decision 13 the owner's merge of the new head is a second act, but once R22's App merges on the owner's approving review the label is the only act that is not head-bound. One line closes it: the label counts for the head R11 recorded at labeling, else "not approved".
- **Merged recommendation.** Don't port the per-SHA file. Fold one check into R13 (the release label) using R11's recorded head: a label applied on an earlier head does not authorise a later one.
- **Score:** +1 / 0 / 0 / +1 / 0 / 0 = **3**. Confidence: medium.

### Item 6. Plan as a hard boundary / plan growth after approval (X #5, Y L4)

- **X says:** already covered: the (b) run is read-only, (c) starts after (b), `plan_sync` hook and gate judge departures; the one gap is a by-hand `/sdlc-build` before the design merges. Score +1.
- **Y says:** the three layers all read the *working* `plan.md`, so a build run may grow the plan in the same commit and pass; only `ratchets` reads the approved copy. Port: compare `## Files that change` of `ctx.approved_artifact("plan.md")` with the working copy at (c)-(e), record `plan_growth` in the gate record, one banner line in R24, a threshold that reads the change as non-routine. Score 8.
- **What the code shows.** The kit: `.claude/hooks/require-plan.sh` blocks edits under `PLAN_REQUIRED_PATHS` without an approved or delegated plan; `check_artifact_chain.py:973` fails a changed file not listed in the plan; `check_deviations` caps `deviation:` ledger lines at `max-deviations: 5` (`.sdlc/delegation.yaml`, `check_artifact_chain.py:537-545`). The framework: `plugin/gate/checks.py:656` `plan = ctx.artifact("plan.md")` (working copy) in `check_plan_sync`; `:124-151` `approved_base`/`approved_artifact` exist and `:1640` `ratchets` uses them; `plugin/pr/description.py:259-276` renders plan conformance as one pass/fail line; `plugin/agents/adversarial-reviewer.md:36-37` judges "the diff inside the files plan.md lists". Crosswalk `build-plansync`: "better: framework, keep". `plugin/gate/preflight.py` checks seven things (CLAUDE.md, skills, hooks, settings, pause, park, test target) and not the change's phase, so X's by-hand gap is real; in CI `run_phase.py` `guard()` (`:1874`) checks the state.
- **Who is right.** Both, on different points. X correctly reads the decided row; Y found a measurable gap the row's "keep" did not consider: "the merged diff still matches plan.md" (p.17) is met against a plan the build may have rewritten. On the fast lane (decision 30) nobody reads a routine plan before (e), so growth during the build is invisible until the owner diffs `plan.md`. One comparison and one banner line is cheap. Y's threshold-to-non-routine and "tell the reviewer" add machinery I would leave out at first.
- **Merged recommendation.** Port adapted, fold into R24 (the banner line) with R26 counting it: at (c), (d) and (e) the gate records `plan_growth: {added, removed}` from the approved copy; the build PR banner shows "The plan grew by N files since gate (b): …" when N > 0. No park, no cap change. Separately, a one-line preflight check that the change is at phase b with gate passed before a by-hand (c) closes X's gap (no candidate needed; a plugin fix).
- **Score:** +1 / +1 / 0 / +1 / 0 / +1 = **8**. Confidence: high on the gap, medium on the value.

### Item 7. Evals: deterministic suite / a case seen failing (X #6, Y L1)

- **X says:** the kit's 49 YAML hook cases are covered by pytest (155 tests in `tests/test_hooks.py`) plus 6 evals; a second format doubles maintenance. Score +1.
- **Y says:** the kit refuses an oracle that cannot fail (`check_eval_cases.py`, `--require-claude`, the lesson); the framework's `lesson_and_eval` only checks the case's two files exist, and R35 leaves "whether it asserts the incident" to the review pass. Port: a `run.py --checks-only` pass at the merge base and at HEAD, `evidence/eval-proof.json`, gate (e) requires red at base and green at head, a hollow case is a fix round. Score 11.
- **What the code shows.** The kit: 55 cases, 49 `kind: hook` and 6 `kind: skill` (`evals/cases`, counted); `scripts/check_eval_cases.py:1-22` refuses a bare `! cmd` under `set -e`, an unknown kind, a case with neither `check:` nor `prompt:`; `.github/workflows/agent-evals.yml:54` `--require-claude`; `docs/sdlc/templates/incident.md` "Eval added … mandatory before this record is closed"; `scripts/test_run_evals.py:345` `CaseBlocksAreWhole`; the lesson `a-verifiable-command-fails-before-the-change.md` says itself "No hook can tell a discriminating command from a decorative one". The framework: `tests/test_hooks.py` has 155 `def test_` (X exact), the suite about 1,510 test functions, 7 case folders under `evals/cases/` (X says 6); `plugin/gate/checks.py:2027-2073` `lesson_and_eval` checks presence of `prompt.md` and `checks.yaml` and the lessons index, nothing inside; `plugin/evals/run.py:117` kinds `command`, `file`, `output`, `denied`; `docs/proposals/eval-suite-grows.md:86` ("whether it asserts the incident is the review pass's to judge") and `:90` (a drafted case "that cannot be made to fail without the change is left out"); `fix-proves-itself.md:3-4` runs the fix's test red at the lock commit and green at HEAD (R34).
- **Who is right.** X on the format (the kit's bash-YAML cases are not worth porting; both agree in effect). Y on the gap, but Y overstates the proof: (a) a `command` check that runs a test file added by the fix is red at the base because the file is missing, not because the bug exists, so "red at base" can be hollow (R35's drafted-case rule has the same weakness); (b) `output` and `denied` checks, the usual shape of a hook or skill incident, need the model and cannot be run checks-only; (c) the owner does not judge the case today, so Attention +1 is not earned. Still, for an incident whose case is a command check, the same red/green pattern R34 already builds is cheap and removes a judgment R35 leaves to a model.
- **Merged recommendation.** Port adapted, narrower than Y: fold into R35's incident-case clause: when the case holds `command` or `file` checks, the runner evaluates them at the merge base with the case's own files copied in and at HEAD, records both in `evidence/`, and gate (e) requires at least one red at base; a case with only `output`/`denied` checks is recorded as "not provable without the model" and stays the review pass's. No `--checks-only` red counts when the only failure is a missing test file (the runner reports the reason class). The kit's bash lint is not ported.
- **Score:** +1 / 0 / +1 / +1 / 0 / +1 = **8**. Confidence: medium.

### Item 8. Metrics per play (X #9)

- **X says:** fold into R26: label each counter with the phase it measures and the decision it informs. Score 4.
- **What the code shows.** `docs/sdlc/metrics.md:14-28` pairs a leading and a lagging indicator for 13 plays, with "Where"; `scripts/sdlc_metrics.py` computes four and `github_metrics.py` the GitHub ones, as X says ("many defined, few computed"). R26 (`measures-that-change-a-decision.md:55`) already cites the article's per-play pairs and keeps "the ones that change a decision"; its table has no play column.
- **Merged recommendation.** Fold into R26 as a column of its measures table (play, leading or lagging); no counter added. A documentation convention, not plugin work.
- **Score:** 0 / 0 / 0 / +1 / 0 / +1 = **4**. Confidence: medium-low (value is presentational).

### Item 9. Multi-approver roles (X #10)

- **X says:** don't port; the study kept one owner (x-roles). Score −2.
- **What the code shows.** `.sdlc/approvers.yaml` maps four roles to one handle, `never-approve` lists the bots, `.github/CODEOWNERS` routes everything to the owner. Crosswalk `x-roles`: "The one-owner premise stays: I remain the only approver". R28 adds advisory roles.
- **Merged recommendation.** Don't port; revisit only if a collaborator joins (the kit itself ran every role as one person).
- **Score:** +1 / −2 / −1 / +1 / 0 / +2 = **−2**. Confidence: high.

### Item 10. Local-session execution (X #8)

- **X says:** don't port; reverses decision 1; handle cost through R25. Score −15.
- **Y says (§5):** context management "cost the owner by hand" until session chaining; the main reason the CI design fits better.
- **What the code shows.** Decision 1 (hosted CI from B3, revised to "hands-off means you should not be the one launching phases"); `changes/*/evidence/spend.json` total_usd 50.69, 84.69, 66.00, 56.30 (X's "$50–85" verified); the kit's `HANDOFF.md` is 1,078 lines (Y verified).
- **Merged recommendation.** Don't port. Agreed by both.
- **Score:** −1 / −2 / −2 / −1 / +2 / 0 = **−15**. Confidence: high.

### Item 11. CLAUDE.md: enforcement note, retirement, line budget (Y L2)

- **Y says:** each proposed line carries `enforced:`; a later eval case or gate check "whose signature matches a line's finding" proposes deleting the line; the standing PR shows `CLAUDE.md: N of M lines` against `claude_md.max_lines`. Score 10.
- **What the code shows.** The kit: `docs/sdlc/rules/60-lessons.md:11` "delete the pointer when a hook makes the mistake impossible"; `gen_context_files.py:192-201` refuses a render over `MAX_CONTEXT_LINES=120`; 17 of 18 lesson files carry "Where it is enforced" (counted; `stage-new-files-before-verify.md` lacks it). The deletion Y cites did happen: `git diff e227ed6 HEAD -- docs/sdlc/rules/60-lessons.md` removes the "No blank line in an eval `check:` block" pointer while the lesson file remains; but `e227ed6` is one of the shallow clone's grafted boundaries (`git rev-list --max-parents=0` lists it) and its diff *adds* that line (`+- No blank line …`), so Y's commit citation is wrong and the deleting commit is not identifiable here. The framework: `plugin/review/findings.py:274-316` `update_seen` only increments; no removal path; `template/CLAUDE.md:23-25`; `claude-md-standing-pr.md:94` the only "under a page" mention; no line-count check anywhere in `plugin/` or `tasks.py` (Y's grep, confirmed by mine).
- **Who is right.** Y on the gap: R37's PR only grows, and p.20 step 5 is the half the framework does not mechanise. Y's deletion trigger is not deterministic as described: nothing links an eval case or gate check to a finding's signature unless a person writes the link. What is deterministic: the line count against a budget, and "no repeat of this signature in the last N merged changes" from R26's per-line count, which is a good enough retirement candidate.
- **Merged recommendation.** Port adapted, fold into R37 with R26: (i) `sdlc.yaml: claude_md.max_lines` (default the template's page) and the count in the standing PR body; (ii) each line in the PR table gets an optional `enforced:` note the owner (or the review pass, when a finding's `rule` names a hook or check) fills, default `none`; (iii) a line whose signature has not repeated in N merged changes since it merged, or whose `enforced:` names a check, is listed as a deletion candidate, oldest first when over budget. Nothing deletes by itself (decision 6).
- **Score:** 0 / +1 / 0 / +1 / +1 / +1 = **7** (Y's Autonomy +1 is not earned: no run acts more on its own). Confidence: medium.

### Item 12. A repeated gate failure proposes a CLAUDE.md line (Y L3)

- **Y says:** key `gate|<check>|<reason class>` in `.review-seen.json` or a sibling; on the second change with the same signature, R37's step proposes a line from the check's fixed hint. Score 8, confidence medium.
- **What the code shows.** The kit: its enforcement matrix marks rule 7 "—" (`docs/sdlc/README.md`, the "Mistake twice → memory" row), so the kit has the wider *scope* in prose only (Y says so). The framework: `findings.py` keys on review findings only; `plugin/pr/counters.py` has no gate-repeat count (`collect`, `render` only); `plugin/gate/gate.py:73-74` joins the failed checks' reasons into the park reason and nothing aggregates them; `claude-md-standing-pr.md:65-66` counts review-finding repeats.
- **Who is right.** Y, with a caveat Y half-states: many gate failures are not the session's mistake (a missing label, an infrastructure failure, a limit, an owner-only field). The signature must be restricted to session-attributable checks (`plan_sync`, `design_scope`, `clean_tree`, a red target class, `secrets`), else the standing PR fills with lines about the pipeline.
- **Merged recommendation.** Port adapted, fold into R37: a `gate` signature for a fixed allow-list of checks, the line built from the check's `hint` text, counted across changes as review findings are; R18's plain-words reason where the hint is terse.
- **Score:** 0 / +1 / +1 / 0 / 0 / +1 = **8**. Confidence: medium (the allow-list and the reason classes need a look at real park reasons).

### Item 13. GitHub Actions minutes measured and budgeted (Y L6)

- **Y says:** the digest sums run timings (`actions: read`), shows "minutes this month: n of 2,000", warns past `gate.actions_minutes_warn`; R61's trial check asks `/sdlc-init` whether the repository is private. Score 6.
- **What the code shows.** The kit: `work/ci-budget/intent.md:5` (1,124 runs, 2,000 minutes exhausted, "unable to run a single job since, including the owner's approval tap"); `scripts/github_metrics.py:11, 197` `actions_minutes_per_pr`; `monitoring/bands.yaml` has the metric with its tiers. The framework: `template/.github/workflows/sdlc-build.yml:73` `timeout-minutes: 260`; `sdlc-digest.yml:30-33` `contents: read`, `issues: write`, `pull-requests: read`; `weekly-window-guarded.md` measures model spend only; R53 measured setup share, not minutes.
- **Who is right.** Y; the item is conditional on a private repository under a metered plan, where the failure mode is a silent full stop of every run. On a public repository it is nothing. Y scores it accordingly.
- **Merged recommendation.** Port adapted, fold into R25 (the meter beside the spend) and R61 (on only when `/sdlc-init` finds the repository private). The kit's "loosened controls" list is not ported.
- **Score:** 0 / +1 / +1 / 0 / +1 / 0 = **6** on a private repository, 0 on a public one. Confidence: medium (open question 1).

### Item 14. A decision carries a revisit trigger (Y L7)

- **Y says:** optional `revisit: {on: <date>}` or `{when: …, candidate: Rn}` in a decision's frontmatter; `docs-lint` prints a report line when due. Score 5.
- **What the code shows.** The kit: `knowledge/decisions/one-writer-until-ledger.md:36-43` expires on a reading or on 2027-03-05 (nothing checks the date, Y says so). The framework: every decision's frontmatter is `status`, `reversibility`, `amended_by` (`docs/decisions/17.md:1-5`; no `revisit`/`expir`/`provisional` hit); R50 is the one revisit trigger, in a ROADMAP row; `tasks.py:446-454` `task_docs_lint` prints reports and failures; R58 accepted 2026-10-20, no revisit check (`docs-lint-checks.md:36-38`).
- **Who is right.** Y on the facts; the value is small: R50 already shows the pattern as a ROADMAP row with a countable trigger, and a date-only revisit is a reminder the owner would otherwise meet in the ROADMAP's Order. Attention +1 is generous.
- **Merged recommendation.** Fold into R58 as an optional field and a report line (never a failure); repository practice, no plugin change.
- **Score:** 0 / 0 / 0 / +1 / 0 / 0 = **2**. Confidence: medium-low.

### Item 15. Third-party actions pinned by SHA (Y L8)

- **Y says:** pin every `uses:` to the tested tag's SHA with the tag as a comment; one test asserts `@<40 hex>`; R5's pin-bump PR carries bumps. Score 3.
- **What the code shows.** The kit: all `uses:` are `@<sha> # vX` (`.github/workflows/*.yml`, counted: checkout, upload-artifact, claude-code-action). The framework: `actions/checkout@v5` 62 times (56 + 6, counted exactly as Y says), `create-github-app-token@v2` 16, `setup-node@v5` 17, `upload-artifact@v4` 20, `cache@v4` 2, `setup-python@v7` 2; `tests/test_templates.py` asserts permission blocks (`:325`) and nothing about pins; `docs/reviews/2026-10-19-plugin-security-review.md` has no pin finding (grep empty); `docs/notes/20.md` records majors chosen by version.
- **Who is right.** Y. First-party actions, small risk, but the App-token action handles the key decision 33 relies on, and a SHA says which code ran. The cost for a project is nil (the template ships the pins); the cost for the framework is a bump per release.
- **Merged recommendation.** Port as-is: a template PR (or inside R44), with the 40-hex test and the bump folded into R5.
- **Score:** +1 / 0 / 0 / +1 / 0 / 0 = **3**. Confidence: high.

### Item 16. Writer and reviewer model on each record line (Y L9)

- **Y says:** R11's lines gain `writer_model` and `reviewer_model`, copied from `evidence/claude-<phase>.json` and the `panel_blind` record; the kit's "review on a different model" rule is not ported (R7 settled it). Score 2.
- **What the code shows.** The kit: `docs/sdlc/rules/30-conventions.md:21-23`; ledgers name the models (`work/chain-check-without-gh/log.md:26` "Writer claude-fable-5-1", `work/parked-marker-on-retired/log.md:20` "Opus 5 against a Fable 5.1 writer"). The framework: `plugin/gate/checks.py:949` `check_reviewer_model` parks a verdict not written on `adversarial_model`; `plugin/hooks/panel_blind.py` exists; `template/sdlc.yaml:44-46` the three model keys; `approvals-list.md:64` lists each line's fields (`act, by, at, via, head, details`) with no model.
- **Merged recommendation.** Fold into R11: two fields in the `details` map of each gate and fix-round line.
- **Score:** 0 / 0 / 0 / +1 / 0 / 0 = **2**. Confidence: high.

## 4. Rubric scorecard per study

| Criterion | Study X | Study Y |
|---|---|---|
| 1. Factual accuracy | Mechanisms described correctly at coarse grain, but few file:line citations, so little to check. Small count errors: 19 lessons (18 exist), 6 evals (7 case folders), "~1,480 tests" (about 1,510 test functions). "Antigravity ignored the hooks" is a fair reading of `gemini-hooks.md:92-96`. Its "already covered" verdicts on #4, #5, #6 are right and the gaps it names (a label after a fix round; no phase check in the by-hand preflight) are real. It omits that the deploy-envs decision kept the single adapter. | Dense and almost every citation checks out (listed per item above). One wrong citation: `e227ed6` is the shallow clone's grafted boundary whose diff adds the pointer line; the deletion is real but its commit is not identifiable here. One slip: `profile_override` lives in `plugin/state/status.py`, not `conventions.py`. One overstatement: L1's "red at base" can be trivially satisfied and does not cover `output`/`denied` cases. |
| 2. Fit to the weighted criteria | Arithmetic correct on every row (re-computed). Method flawed on the two top rows: #1 and #3 are scored against `main`, not against the accepted R52 and R39, so they count value the owner already accepted. Cost scored +2 where it earns the item nothing (weight 0): fine, and X says so. | Arithmetic correct on every row (re-computed). Method right (delta over `main` plus accepted candidates). Generous on Attention and Autonomy for L1 (the owner does not judge the case today; a model does) and L2 (no run acts more on its own); L7's Attention +1 is a reminder, not an act removed. |
| 3. Consistency with decisions and decided rows | #2 (serial default) reopens accepted R51 and choice 234; #3's environments list reshapes the deploy-envs decided row and touches sticky decision 19; #7's "Gemini as the advocate" is R8's own promotion path, so not a defect. The rest consistent. | Each item names the decisions it keeps; I found none reopened. L5 correctly reads R52 as amending decision 4 only for opted-in projects. |
| 4. Cost and complexity for small projects | #3 and #1 default off (good). #2 is the simplest model for a small project but is not free to build (a pointer, a label, a dispatch). #8 and #10 rightly rejected on cost of attention. | L4, L8, L9, L16 are a few lines each. L1 (two worktree evaluations per incident) and L2's signature matching add plugin machinery; I trimmed both. L6 is conditional and off on public repositories. L5's floor reuses an existing matcher: cheap. |
| 5. Concreteness | `sdlc.yaml` shapes for #3 (`deploy.environments`), #1 (`delegation: off|low`, `Autonomy: delegated`), #2 (`queue: serial`, `sdlc:queued`); the rest is prose. No gate or workflow named for the merge-on-grant step. | Keys, files, gate names and workflow scopes for every item: `run.py --checks-only`, `evidence/eval-proof.json`, `claude_md.max_lines`, `gate|<check>|<class>`, `plan_growth` in `evidence/gate-<phase>.json`, `gate.max_plan_growth`, `sdlc:merge-by-silence-off`, `gate.actions_minutes_warn` with `actions: read`, `revisit:` frontmatter, a 40-hex test, `writer_model`/`reviewer_model`. |

Overall: Y is the stronger study on method, accuracy and concreteness; X contributes two things Y lacks (the explicit per-change grant with zero wait; the post-merge staging step) and the correct rejection of items Y did not consider.

## 5. Merged recommendation table

Sorted by my weighted score; ties by confidence.

| Item | Recommendation | How | Score | Confidence |
|---|---|---|---|---|
| 6. Plan growth after approval shown | port adapted | amend R24 (banner line) and R26 (count); a one-line phase check in `preflight.py` for by-hand (c), no candidate | 8 | high (gap) / medium (value) |
| 1. Per-change grant, locked-path floor, merged-unread record | port adapted | amend R52 (at R50's trigger), R11 (the line), R59 (renames) | 8 | high / medium |
| 7. Incident eval case seen red at the base | port adapted, narrowed to `command`/`file` checks | amend R35's incident-case clause, R34's pattern | 8 | medium |
| 12. Repeated gate failure proposes a CLAUDE.md line | port adapted, allow-listed checks | amend R37 (with R18, R26) | 8 | medium |
| 11. CLAUDE.md budget, `enforced:` note, retirement candidates | port adapted | amend R37 and R26 | 7 | medium |
| 2. Post-merge staging command before the release label | port adapted, as an option; keep the adapter shape | amend R39 ("What to settle" row); decisions 13 and 19 kept | 6 | medium |
| 13. Actions-minutes meter | port adapted, private repositories only | amend R25 (meter) and R61 (when on) | 6 (0 on public) | medium |
| 8. Metrics labelled by play | fold | a column in R26's table | 4 | medium-low |
| 5. Release label bound to its head | fold | amend R13 using R11's recorded head | 3 | medium |
| 15. Actions pinned by SHA | port as-is | a template PR or R44; the bump in R5 | 3 | high |
| 14. `revisit:` on decisions | fold, optional | amend R58 (a report line) | 2 | medium-low |
| 16. Models on record lines | fold | amend R11 (`details`) | 2 | high |
| 4. Gemini as reviewer | nothing to port | R8 unchanged | 0 | high |
| 3. Serial run-queue | don't port as default; optional at most | one open row in R51 | −2 | high |
| 9. Multi-approver roles | don't port | — | −2 | high |
| 4. Gemini parity (context files, hook wiring) | don't port | decisions 6, 7, 8 kept | −5 | high |
| 10. Local-session execution | don't port | decision 1 kept; cost through R25 | −15 | high |

Nothing above needs a new candidate; every port amends an accepted one, and R60's own text says accepted items go "through the normal front door".

## 6. Open questions only the owner can answer

1. **Are the trial projects private repositories under a metered Actions plan?** Item 13 is worth 6 on a private repository and 0 on a public one.
2. **On an explicit per-change grant, should the App merge at once or still wait R52's hours?** X says at once (the grant is the consent); Y keeps the hours. The owner's own criteria (Autonomy 3) favour at once; the owner's "look in once or twice a day" favours the hours as a safety margin.
3. **For a trading project, is "paper on merge, live on label" wanted in addition to R39's pre-merge preview?** If the preview at each (e) head is enough, item 2 drops to 0.
4. **Is an optional serial queue wanted on the sample for attribution?** R51's text says one change at a time keeps the sample's results attributable; nothing enforces it.
5. **What line budget for CLAUDE.md?** The template's page is about 40 lines filled; the kit used 120 for three files. A number is needed for `claude_md.max_lines`.
6. **Should a gate check's repeated failure count as "a mistake made twice"?** The article's rule is about Claude's mistakes; the owner decides whether plan-sync and scope failures qualify (they are the session's) and whether red targets do (they already start fix rounds).
7. **R8's promotion path:** once the Gemini tally exists, would the owner consider Gemini as the panel's advocate (X's suggestion)? Decision 21's "different model" is already met within one vendor, so this is a new decision, not a port.

## 7. What I checked

sdlc-framework (working tree equal to dc40d61 except the two forbidden review files, confirmed by `git diff --stat dc40d61 HEAD`):
`docs/ROADMAP.md` (every candidate row; R5, R8, R11, R15, R18, R20, R22, R24–R26, R34, R35, R37, R39, R41, R44, R50–R53, R58–R61 in full); `docs/decisions/index.md`, `1.md`, `2.md`, `4.md`, `6.md`, `7.md`, `8.md`, `11.md`, `13.md`, `17.md`, `18.md`, `19.md`, `21.md`, `24.md`, `26.md`, `30.md`, `33.md`; `docs/reviews/2026-09-28-playbook-vs-framework.md:100-120`; `docs/reviews/2026-09-28-playbook-vs-framework/target-design.md` (head); `crosswalk.json` rows build-plansync, test-evals, deploy-claudemd, deploy-approve, deploy-envs, deploy-release, maintain-learn, x-headless, x-queue, x-limits, x-measure, x-audit, x-roles; `docs/proposals/lifecycle-axis-features.md`, `speed-beyond-the-sprint.md`, `concurrent-changes.md`, `eval-suite-grows.md:30-110`, `fix-proves-itself.md:1-30`, `claude-md-standing-pr.md:40-110`, `measures-that-change-a-decision.md` (grep), `risk-hit-in-banner.md` (grep), `approvals-list.md` (grep), `preview-environment.md`, `external-design-check.md`, `weekly-window-guarded.md` (grep), `docs-lint-checks.md` (grep), `revisit-parallel-worktrees.md`; `docs/reference/ai-native-sdlc-playbook.txt` pages 16, 17, 20, 28, 37, 44; `docs/OPERATING_MODEL.md` (grep: queue, concurrent); `docs/notes/20.md` (head); `docs/reviews/2026-10-19-plugin-security-review.md` (grep: pin); `plugin/gate/checks.py:120-155, 640-700, 940-960, 1630-1650, 2020-2080`; `plugin/gate/preflight.py` (docstring, check list); `plugin/gate/gate.py` (grep: reason); `plugin/evals/run.py:117-120, 240-270, 495-515` and its function list; `plugin/review/findings.py:260-330`; `plugin/pr/counters.py` (defs); `plugin/pr/description.py:250-285`; `plugin/release/approval.py:1-200`; `plugin/hooks/protected_paths.py:40-65`; `plugin/hooks/test_file_lock.py:105-125`; `plugin/hooks/` and `plugin/panel/` listings; `plugin/state/status.py` and `conventions.py` (grep: override); `plugin/ci/run_phase.py` (grep: guardrail_changes, guard); `plugin/detect/stats.py` (grep: Western Electric, min_sigma); `plugin/agents/adversarial-reviewer.md:30-40`; `plugin/commands/sdlc-build.md:1-66`; `plugin/skills/intent-template/SKILL.md` (grep: autonomy, delegat); `template/sdlc.yaml`; `template/CLAUDE.md`; `template/lessons/README.md` (grep); `template/.github/workflows/` listing, `sdlc-build.yml:65-80`, `sdlc-digest.yml:25-40`, `uses:` counts over both workflow folders; `tests/test_templates.py` (grep); test counts (`def test_` in `tests/`); `evals/cases/` listing; `lessons/` listing; `changes/` listing and `evidence/spend.json` totals; `tasks.py:440-470`.

lifecycle-axis- (80328c1): `.sdlc/environments.yaml`, `delegation.yaml`, `approvers.yaml`, `config.env`, `active`, `release-authorizations/`; `.github/workflows/deploy.yml`, `agent-evals.yml:30-60`, `uses:` over all workflows; `.github/CODEOWNERS`; `scripts/deploy.sh:1-116`; `scripts/next_item.py:1-150`; `scripts/delegated_merge.py:80-100, 655-690, 880-1030, 1055-1115`; `scripts/check_artifact_chain.py:365-445, 475-550, 973`; `scripts/check_eval_cases.py:1-60`; `scripts/github_metrics.py` (grep); `scripts/gen_context_files.py` (grep); `scripts/test_run_evals.py:345`; `monitoring/bands.yaml`; `docs/sdlc/metrics.md`; `docs/sdlc/rules/60-lessons.md`, `30-conventions.md:15-30`; `docs/sdlc/README.md:100-115`; `docs/sdlc/templates/incident.md:20-32`; `docs/sdlc/handoff/HANDOFF.md` (line count); `knowledge/lessons/` listing and "Where it is enforced" count, `a-verifiable-command-fails-before-the-change.md:1-60`; `knowledge/decisions/` listing, `one-writer-until-ledger.md:25-45`, `gemini-hooks.md` (grep); `.claude/hooks/` listing, `require-plan.sh:1-40`, `protect-tests.sh:10-40`; `.gemini/` listing; `evals/cases` counts by kind; `work/` listing, `work/ci-budget/intent.md:1-20`, `work/standing-grant/intent.md`, `work/advance-push/intent.md` (title, description), `work/*/log.md` (grep: #83, #100, #112, delegated); git: `rev-list --max-parents=0`, `show e227ed6`, `diff e227ed6 HEAD -- docs/sdlc/rules/60-lessons.md`, `log -S/-G` on the pointer line.

---

## The mapping (recorded after the verdict)

| Blind name | Study | File |
|---|---|---|
| Study X | Study A (the comparison doc of 2026-10-19/20) | `study-a.md` |
| Study Y | Study B (the independent study of 2026-10-20) | `study-b.md` |

Drawn at random before the judge started (`python3 -c "import secrets; print(secrets.choice(['A=X,B=Y','A=Y,B=X']))"` printed `A=X,B=Y`). The mapping was not given to the judge.

**Corrections the verdict implies for Study B.** They are recorded here, not edited into `study-b.md`, which stays as it was committed before Study A was read:
- **L2.** Commit `e227ed6` is the shallow clone's grafted boundary, so it cannot be cited as the commit that deleted the pointer. The deletion itself is real: `git diff e227ed6 HEAD -- docs/sdlc/rules/60-lessons.md` shows it.
- **L5.** `profile_override` lives in `plugin/state/status.py:46-48`, not in `plugin/state/conventions.py`.
- **L1.** "Red at base" can be met trivially by a case whose test file is new. `output` and `denied` checks cannot be evaluated without the model.
