---
type: Review
title: "Study B: what lifecycle-axis- does better than the framework, and what to port"
description: An independent study, made before Study A was read, of the mechanisms in the owner's earlier kit lifecycle-axis- (HEAD 80328c1) that beat the framework at main (dc40d61, plugin 1.0.14), each with a port recommendation and a score on the owner's six weighted criteria.
status: report
roadmap: R60
sources:
  - id: process
    resource: docs/proposals/lifecycle-axis-features.md
    title: "R60's two-study process: Study B first, then Study A, then a judge"
  - id: lifecycle-axis
    resource: "https://github.com/luissiviero/lifecycle-axis- (HEAD 80328c1, read-only clone, shallow: 180 commits from 2026-09-08 to 2026-09-18)"
    title: "lifecycle-axis-, the starter kit the framework replaced"
  - id: framework
    resource: "this repository at main dc40d61 (plugin 1.0.14)"
    title: "The framework as it stands"
  - id: criteria
    resource: docs/reviews/2026-09-28-playbook-vs-framework.md
    title: "Section 7, line 111: safety 1, owner attention 3, autonomy 3, auditability 2, cost 0, fidelity to the article 2"
  - id: article
    resource: docs/reference/ai-native-sdlc-playbook.txt
    title: "The AI-Native SDLC playbook, cited by PDF page"
generated: { by: claude-code-session, at: 2026-10-20T00:00:00Z }
---

# Study B: what lifecycle-axis- does better, and what to port

**Readings chosen (the owner is hands-off; these are the most reasonable readings, stated so a reader can disagree with them):**

- **"Better than the framework at main".** The baseline is `main` at `dc40d61` (plugin 1.0.14) *plus* every accepted ROADMAP candidate as its proposal file describes it. An item is counted only if neither a built feature nor an accepted proposal already gives it. An item may still extend a candidate; it then names that candidate.
- **Scores.** A score is the change the port would add over that baseline, not the value of the candidate it folds into. Each criterion is scored -2 to +2. The weighted total is safety×1 + attention×3 + autonomy×3 + audit×2 + cost×0 + article×2, using the weights saved on 2026-09-29 (`docs/reviews/2026-09-28-playbook-vs-framework.md:111`).
- **Phase names.** The phases are written (a) to (f), as `main` still names them; the R45 rename is not built.
- **Scope.** The study covers the kit's mechanisms (code, hooks, workflows, records), not its prose. A practice that lives only in prose counts when the kit's history shows it working: a commit, a ledger or a lesson that records it.

**Contamination.** One partial view of Study A, before this file was committed: while grepping for `lifecycle-axis` in this repository, I read one table row of `docs/handoffs/sessions/2026-10-20-ccr-7ef35daa-7adzh8.md` (line 57). It names "the Cowork comparison of `lifecycle-axis-`" and says that its artifact has an open comment ("whether a future collaborator counts"), and that its "both suites passed" line "was not one clean run for this repository". That row gives none of Study A's items or recommendations. I read nothing else of that file, and neither did the subagents, which were told to skip it, the artifact and PRs #268 and #270. The R60 row in `docs/ROADMAP.md` and `docs/proposals/lifecycle-axis-features.md` were read, as the task allows.

## Summary

- lifecycle-axis- is weaker than the framework on the main path. It has no autonomous phase runs, no confidence gate, no fix rounds and no deterministic incident route, so most of its machinery solves problems the framework does not have. Ten items are better, though, and **eight of them are worth porting**. All eight fold into accepted candidates; none needs a new candidate or reopens a settled decision.
- **Score 11, an oracle must be seen failing.** The highest-scoring port: an incident's eval case must be **seen failing before the fix**, checked deterministically, not merely present. It extends R35, whose own design names the gap and leaves it to the review pass.
- **Scores 10 and 8, CLAUDE.md upkeep.** The next two are about `CLAUDE.md`, which the article asks to keep "under a page" with every repeated mistake in it (p.20).
  - Each "Things Claude gets wrong" line should say what enforces it, and should be proposed for deletion once a hook, check or eval makes the mistake impossible.
  - A repeated *gate failure*, not only a repeated review finding, should become a proposed line.
  - Both extend R37.
- **Score 8 each, two record ports.** The plan's growth after the owner approved it should become a visible line in R24's banner, and R52's merge by silence should borrow the kit's per-change grant, its locked-path floor and its "merged unread" record. Both make the owner's record truer without adding an act.
- **The rest are small or not ported.** Measuring GitHub Actions minutes (R25) matters only on a private repository. A revisit date on decisions (R58), the model named on each record line (R11) and SHA-pinned actions (R44) are small. The kit's multi-vendor context files are better than nothing but should not be ported (decision 8). The tap approval, the risk detour, the session chain, the run queue and the two status words are not better than what the framework has or has accepted (section 4).

## Scoreboard

Sorted by weighted score. S = safety (×1), At = owner attention (×3), Au = autonomy (×3), Ad = auditability (×2), C = cost (×0), Ar = fidelity to the article (×2).

| # | Item | Recommendation | Fold into | S | At | Au | Ad | C | Ar | Weighted |
|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| L1 | An eval case must be seen failing before the fix | port adapted | R35 (with R34's red/green pattern) | +1 | +1 | +1 | +1 | 0 | +1 | **11** |
| L2 | Each `CLAUDE.md` line says what enforces it and retires when a check does; the page is measured | port adapted | R37 (with R26's repeats per line) | 0 | +1 | +1 | +1 | +1 | +1 | **10** |
| L3 | A mistake made twice is any repeated mistake: a repeated gate failure proposes a line too | port adapted | R37 (with R18, R26) | 0 | +1 | +1 | 0 | 0 | +1 | **8** |
| L4 | The plan's growth after approval is counted and shown | port adapted | R24 (banner), R26 (count) | +1 | +1 | 0 | +1 | 0 | +1 | **8** |
| L5 | Merge by silence borrows the per-change grant, the locked-path floor and the "merged unread" record | port adapted | R52 (with R11, R22) | +1 | 0 | +1 | +2 | 0 | 0 | **8** |
| L6 | GitHub Actions minutes are measured and budgeted | port adapted | R25 (with R61, R20) | 0 | +1 | +1 | 0 | +1 | 0 | **6** |
| L7 | A decision carries its revisit trigger, and the docs lint reports it when due | port adapted | R58 (with R50's pattern) | 0 | +1 | 0 | +1 | 0 | 0 | **5** |
| L8 | Third-party actions are pinned by commit SHA | port as-is | R44 (or a plain template PR) | +1 | 0 | 0 | +1 | 0 | 0 | **3** |
| L9 | Each record line names the model that wrote and the model that reviewed | port adapted | R11 | 0 | 0 | 0 | +1 | 0 | 0 | **2** |
| L10 | One rule source renders CLAUDE.md, GEMINI.md and AGENTS.md | don't port | (R8 stays the only other-vendor use) | 0 | 0 | 0 | 0 | 0 | -1 | **-2** |

## 1. Method

**Clones.** `lifecycle-axis-` at `80328c1`, read-only, cloned beside this repository. The clone is shallow: 180 commits, PRs #54 to #113. This repository is at `dc40d61`.

**Profiles, by five subagents in parallel, each citing a file path for every claim:**
1. lifecycle-axis- governance and approvals (hooks, `approve.py`, `sign.py`, the tap, delegation, the merge, the queue, the handoff, Gemini).
2. Its verification, CI, evals, detection and adoption (`verify.sh`, the chain check, the seven workflows, `run_evals.sh`, `detect_bands.py`, `adopt.sh`). This agent also ran the kit's read-only checks and one `adopt.sh` into a scratch folder.
3. Its knowledge, lessons, decisions, handoff and history (every `work/*/intent.md`, all 18 lessons, all 17 decision records, `git log`).
4. The framework's code and template (`plugin/**`, `template/**`, `tests/`). This agent also grepped for each mechanism a kit like lifecycle-axis- has, to establish absences.
5. A digest of decisions 1 to 34, candidates R1 to R61, the playbook study's T1 to T32, its 48 crosswalk rows, the ArtCraft review and the notes index.

**My own work.** I read the reports and re-checked every claim that a recommendation below rests on, against both repositories (each item's "What I checked").

**What the coverage check reads.** For every item, it reads:
- the framework's code and tests;
- the decisions;
- the playbook study's decided rows (`target-design.md`, `crosswalk.json`);
- the proposal file of every accepted candidate the item could overlap.

The items found better in only one direction are in section 4, each with the reason it is not counted.

## 2. The kit in one page

lifecycle-axis- (2026-09-02 to 2026-09-18) carries each change as a work item `work/<slug>/` with `intent.md`, `spec.md` and `plan.md`. Each artifact has YAML front matter (`status: draft | in-review | approved | delegated | superseded`, `approved-by`), plus an append-only gate ledger `log.md` (`docs/sdlc/templates/log.md`).

**Approval.**
- A human approves with `scripts/approve.py`, through a `workflow_dispatch` "tap" (`.github/workflows/approve.yml`), or in the web editor.
- Hooks refuse an agent's approval: `.claude/hooks/protect-approvals.sh`.
- CI re-derives every approval from git authorship, the ledger and the Actions run record: `scripts/check_artifact_chain.py`.

**Delegated mode.**
- An owner-granted intent (`mode: delegated`, policy in `.sdlc/delegation.yaml`) lets the agent sign the later artifacts under its own handle (`scripts/sign.py`).
- A no-model workflow merges the PR when nine printed conditions hold: `scripts/delegated_merge.py`, `.github/workflows/delegated-merge.yml`.

**Verification, detection and rules.**
- Everything runs through one local command, `scripts/verify.sh`, which ends `VERIFY: PASS (<sha>)` and picks up every `scripts/checks/*.sh`.
- Detection is a nightly band detector that files issues and never opens a PR: `scripts/detect_bands.py`, `.github/workflows/bands.yml`.
- Rules for three agent vendors are rendered from one source with a 120-line cap: `scripts/gen_context_files.py`, `.sdlc/config.env:53`.

**Phases and the record.**
- No phase runs unattended in CI. The agent works in interactive or cloud sessions, chained by `docs/sdlc/handoff/HANDOFF.md`.
- The repository documents its own failures in unusual depth: 18 lessons, each with "Where it is enforced", and decision records with "Residual risk" sections.

**Problems it hit, and what each produced.**
- 1,124 workflow runs exhausted 2,000 free Actions minutes in six days and blocked even the owner's approval tap (`work/ci-budget/intent.md:5`).
- A review round on PR 51 found defects introduced by the previous round's fixes (`docs/sdlc/rules/30-conventions.md:21-23`).
- Oracles could not fail (`work/agent-evals`; `knowledge/lessons/a-verifiable-command-fails-before-the-change.md`).
- `bands.yml` failed with a 403 for three days before anyone noticed (`knowledge/lessons/workflow-permissions-name-every-api.md`).

Several of the items below are what those incidents left behind.

## 3. The items

### L1. An eval case must be seen failing before the fix (score 11)

**(a) What it is.** lifecycle-axis- treats an oracle that has never been seen red as proving nothing:
- **The lesson.** "Watch a new test, eval case or `Verifiable:` clause fail before the change; one only ever seen green proves nothing" (`knowledge/lessons/a-verifiable-command-fails-before-the-change.md`). It came from six non-discriminating `Verifiable:` clauses in PR 70 and six silently skipped tests in PR 71.
- **A static check.** It refuses an eval case that cannot fail by construction: a bare `! cmd` under `set -e`, a missing `check:` or `prompt:`, an unknown `kind` (`scripts/check_eval_cases.py:1-20`, wired into verify by `scripts/checks/eval-cases.sh`).
- **A test.** `scripts/test_run_evals.py` `CaseBlocksAreWhole` catches a blank line that once truncated a `check:` block into an always-passing stub (`knowledge/lessons/eval-checks-have-no-blank-lines.md`).
- **Credential failures.** The nightly prompt-eval run takes `--require-claude`, so an expired credential turns red instead of skipping (`.github/workflows/agent-evals.yml:36-54`).
- **The incident template.** It makes the eval mandatory before the record closes (`docs/sdlc/templates/incident.md:26`).

The principle is mechanised for the case's *form*. For the case's *content* it stays a lesson.

**(b) How it would work here.**
- **The gap.** Gate (e) of an incident change checks only that the case exists and loads: `lesson_and_eval`, `plugin/gate/checks.py:2027-2073`. R35's design keeps it at "the case loads in the runner", and leaves "whether it asserts the incident" to "the review pass's to judge" (`docs/proposals/eval-suite-grows.md:86`). R35 already applies "a case that cannot be made to fail without the change is left out", but only to the cases drafted after the twentieth change (`:90`).
- **The port** applies the same rule to the incident's own case, without a model. A framework case's `command` and `file` checks can be evaluated on a tree without running the prompt (`plugin/evals/run.py:253-260`, `:506`).

Example: incident change `0021-ci-flake`, entry route `incident`, at gate (e).
1. `/sdlc-deploy` step 0b writes `evals/cases/0021-ci-flake/checks.yaml` as today.
2. The runner (deterministic, outside the session, like the deferred commands) evaluates the case's `command`/`file` checks twice with a new `run.py --checks-only`: on a worktree at the merge base with the case copied in, and at `HEAD`.
3. It writes `evidence/eval-proof.json`: `{"case": "0021-ci-flake", "base": {"sha": "...", "failed": ["command: python -m pytest tests/test_retry.py"]}, "head": {"passed": "all"}}`.
4. `lesson_and_eval` requires at least one check red at base and every check green at head.
5. A case that passes at base fails the gate. Per decision 29 that is a red target, so the next fix round rewrites the case. It is not a park, because the session can fix it.
6. The PR banner shows one line: "Eval 0021 fails without the fix: yes (1 of 2 checks)".

**(c) Recommendation.** Port adapted: fold into R35, as its incident-case clause. Neither the kit's bash lint nor the `set -e` rule applies here (framework checks are YAML, not shell), so they are not ported.

**(d) Reasoning.**
- The framework already does this for code: R34 (accepted) runs the fix's test red at the lock commit and green at HEAD (`docs/proposals/fix-proves-itself.md:3-4`).
- The eval case is the same kind of oracle, and the article asks: "When a fix ships, add an eval for the incident ... to ensure that such issues are protected against going forwards" (p.44 step 7). A case that passes without the fix does not do that.
- The kit's own history shows that an oracle seen only green was wrong more than once.
- A checks-only run costs no model call and no session time.
- It removes the one judgment R35 leaves to the review pass.

**(e) Effect.**

| Criterion | Score | Why |
|---|---:|---|
| Safety | +1 | A regression the eval should catch cannot ship with a hollow case. |
| Attention | +1 | The owner no longer judges at (e) whether the case asserts anything. |
| Autonomy | +1 | A deterministic check replaces a judgment; a hollow case becomes a fix round, not a question. |
| Audit | +1 | `eval-proof.json` records red at base and green at head. |
| Cost | 0 | No model call. |
| Article | +1 | p.44 step 7: an eval protects against the incident going forwards; p.28 step 4: reproduce, then fix. |

Weighted 11.
- **Decisions:** 17 kept (the suite still fills from incidents); 21 kept (a deterministic check, never the panel); 29 (the failure is a fix round).
- **Candidates:** R35 (amended), R34 (the same red/green pattern), R15 (ratchets keep the case once it exists).

**What I checked.**
- `plugin/gate/checks.py:2027-2073` (presence and frontmatter only).
- `plugin/evals/run.py` (check kinds, no base run).
- `docs/proposals/eval-suite-grows.md:44`, `:86`, `:90`.
- `docs/proposals/fix-proves-itself.md`.
- crosswalk rows `test-evals` and `maintain-learn` (T13, T25), which require the case, not its failure.

### L2. Each `CLAUDE.md` line says what enforces it and retires when a check does; the page is measured (score 10)

**(a) What it is.** In lifecycle-axis-:
- **One lesson file per repeated mistake**, with the sections "What happened", "Rule" and "Where it is enforced" (17 of 18 files, `knowledge/lessons/*.md`). The last section is honest; several say "Nothing enforces it" (`knowledge/lessons/workflow-permissions-name-every-api.md:34-38`).
- **One pointer line per lesson** in the rendered context file. The rule for those lines is written next to them: "delete the pointer when a hook makes the mistake impossible" (`docs/sdlc/rules/60-lessons.md:11`).
- **A deletion has actually happened.** Commit `e227ed6` deleted the pointer for `eval-checks-have-no-blank-lines.md` "(CaseBlocksAreWhole now makes that mistake impossible, which is what the lessons rule says to do)". The lesson file stayed.
- **The context file has a hard budget.** `gen_context_files.py` refuses to write a render longer than `MAX_CONTEXT_LINES=120` (`.sdlc/config.env:53`). The budget is measured where the adopter pays for it (`knowledge/lessons/adopter-context-file-sits-at-the-cap.md`), so every new line is paid for by deleting or re-flowing another.

**(b) How it would work here.**
- **What the framework has.** It proposes a `CLAUDE.md` line when a review finding repeats: `plugin/review/findings.py` `claude_md_lines`, `.review-seen.json`. R37 gathers those lines into one standing PR, "CLAUDE.md: Things Claude gets wrong", that the owner merges when they choose (`docs/proposals/claude-md-standing-pr.md:77`).
- **What it lacks.**
  - Nothing ever proposes *removing* a line.
  - Nothing records what enforces a line.
  - "Under a page" is prose only: no hit for a line-count check in `plugin/` or `tasks.py`.

The port adds three things to R37's standing PR, all deterministic:
1. Each proposed line carries an `enforced:` note in the PR table: `none`, or the hook, gate check or eval case that now catches it. The review pass's finding already names the rule it applied.
2. When a later change adds an eval case or a gate check whose signature matches a line's finding, the step proposes deleting that line in the same standing PR. A line is never deleted by a run; decision 6 holds.
3. The PR body shows `CLAUDE.md: 41 of 60 lines`. The budget is a new `sdlc.yaml` key, `claude_md.max_lines`, defaulting to the template's page. Over budget, the PR lists the oldest enforced lines first as deletion candidates.

Example: the line "Run the migrations test before reporting done" was added after changes 0007 and 0011. Change 0019's incident adds `evals/cases/0019-migrations/`, which fails without the test. The standing PR then shows that line with `enforced: eval 0019-migrations, proposed for deletion`, and the owner deletes it with the merge.

**(c) Recommendation.** Port adapted: fold into R37. R26's "repeats per CLAUDE.md line" measure gives the evidence for a deletion: no repeat since the enforcing check landed.

**(d) Reasoning.**
- The article asks for both halves:
  - "When Claude makes a mistake twice, the correction goes into CLAUDE.md";
  - "Keep it under a page, because Claude reads all of it at the start of a session ... anything stale is taking up context for no benefit" (p.20 steps 4-5).
- The framework mechanises the first half and not the second.
- The kit shows the second half working once, and shows the cap forcing it.
- Without retirement, R37's standing PR only grows. The file then drifts past a page, which is exactly the failure the article names.

**(e) Effect.**

| Criterion | Score | Why |
|---|---:|---|
| Safety | 0 | |
| Attention | +1 | The owner reviews a shorter file and is told which lines are now redundant. |
| Autonomy | +1 | Every run reads a page of live rules instead of a growing list. |
| Audit | +1 | Each line says what enforces it. |
| Cost | +1 | Fewer context tokens per run, though cost is weighted 0. |
| Article | +1 | p.20 steps 4-5. |

Weighted 10.
- **Decisions:** 6 kept (no run edits `CLAUDE.md`; deletions are proposed in the owner's PR).
- **Candidates:** R37 (amended), R26 (repeats per line), R38 (the same standing-PR pattern for `REVIEW.md`).

**What I checked.**
- `plugin/review/findings.py` (`update_seen`, `claude_md_lines`): add only.
- `docs/proposals/claude-md-standing-pr.md`: no deletion, no budget; its `:94` keeps signatures out of `CLAUDE.md` "which stays under a page", the only mention.
- `template/CLAUDE.md:23-25`.
- `template/lessons/README.md`: incident lessons, with "Prevention" but not a retirement rule for `CLAUDE.md` lines.
- crosswalk row `deploy-claudemd` (T15).

### L3. A mistake made twice is any repeated mistake: a repeated gate failure proposes a line too (score 8)

**(a) What it is.** lifecycle-axis- applies its rule 7 ("A mistake made twice becomes a line in this file or a skill, in the same PR", `CLAUDE.md` hard rule 7) to every kind of mistake, not just review findings. Most of its 18 lessons are process mistakes caught by a check or a red run:
- a plan bullet the chain check misread (`plan-bullets-start-with-the-path.md`);
- unstaged files that turned CI red twice (`stage-new-files-before-verify.md`);
- the chain check run before committing (`commit-before-the-chain-check.md`).

Each is written by whoever notices: the `/sdlc-review` skill (step 6), the `/sdlc-incident` skill (step 4) or the owner. Nothing in the kit enforces rule 7 deterministically; its own enforcement matrix marks the column "—" (`docs/sdlc/README.md:107`). What is better is the *scope*, not the mechanism.

**(b) How it would work here.**
- **Today's scope.** The framework's second-occurrence rule is deterministic but sees only the review pass's findings (`plugin/review/findings.py`). A gate check that fails the same way in two changes is recorded in `evidence/gate-<phase>.json` and the park reason, and nowhere else: no counter keys on it (`plugin/pr/counters.py`).
- **The port.** Give gate-check failures the same signature record:
  - key `gate|<check>|<normalised reason class>`, kept in `changes/.review-seen.json` beside the findings (or a sibling `changes/.gate-seen.json`);
  - on the second change with the same signature, R37's step proposes a line built from the check's fixed hint text.

Example: `plan_sync` fails in change 0012 ("1 changed file(s) not listed in plan.md") and again in 0015. The standing PR then proposes "List every file you create under `## Files that change` in the same commit (seen in changes 0012 and 0015; gate check plan_sync)".

**(c) Recommendation.** Port adapted: fold into R37. R18 (a failed run explains itself) supplies the plain-words reason when the check's hint is too terse.

**(d) Reasoning.**
- The article's rule is "a mistake", not "a review finding" (p.20 step 4).
- The framework has already paid for the deterministic mechanism; widening its input is cheap.
- A repeated park is the costliest repeat for this owner: each one is a wait, and owner attention carries weight 3.

**(e) Effect.**

| Criterion | Score | Why |
|---|---:|---|
| Safety | 0 | |
| Attention | +1 | Fewer repeated parks. |
| Autonomy | +1 | Runs avoid a known failure. |
| Audit | 0 | |
| Cost | 0 | |
| Article | +1 | p.20 step 4. |

Weighted 8.
- **Decisions:** 6 and 11 kept.
- **Candidates:** R37 (amended), R26 (the repeats count), R18 (wording).

**What I checked.**
- `plugin/review/findings.py:274-316` (findings only).
- `plugin/pr/counters.py` (no gate-repeat count).
- `plugin/gate/gate.py` (the park records the reason; nothing aggregates it).
- `docs/proposals/claude-md-standing-pr.md:65-66` (repeats of review findings only).
- `docs/proposals/measures-that-change-a-decision.md` (repeats per `CLAUDE.md` line, not per gate check).

Confidence medium. Whether gate reasons normalise into stable classes needs a look at real park reasons on the sample.

### L4. The plan's growth after approval is counted and shown (score 8)

**(a) What it is.** In lifecycle-axis-:
- A file-list or order deviation from the approved plan must be written into `plan.md` in the same commit (hard rule 2), and logged as a ledger note starting `deviation:`.
- On delegated items, `check_deviations` fails the chain once the count passes `max-deviations` (5, `.sdlc/delegation.yaml:33`), with "re-plan instead of deviating again" (`scripts/check_artifact_chain.py:537-545`).
- A re-signature after a change of plan needs a committed consensus record: at least two `## Reviewer: <role> (<model>)` sections, all `verdict: revise` (`docs/sdlc/templates/revision.md`; `check_revisions`, `check_artifact_chain.py:478-534`).

So the approved plan and the plan the build ended with are kept apart, and the gap is counted.

**(b) How it would work here.**
- **What the framework keeps in step.** The plan is kept in step with the diff by three layers: the `plan_sync` hook, gate check `plan_sync` (`plugin/gate/checks.py:645-691`) and the reviewer's spec/plan angle (`plugin/agents/adversarial-reviewer.md:36-37`).
- **What none of them measures.** All three read the *working* `plan.md` (`checks.py:656`). A build run can add files to the plan in the same commit and pass every check. Only `ratchets` reads the approved copy (`ctx.approved_artifact`, `checks.py:1640`).
- **Why it matters.** On the fast lane (decision 30) a routine plan reaches (c) with no human having read it, so its growth during the build is seen by nobody until the owner opens the build PR's diff at (e).

The port is one deterministic number per gate, shown where the owner already looks.
- The gate at (c), (d) and (e) compares `## Files that change` in `ctx.approved_artifact("plan.md")` with the working copy, and records `plan_growth: {added: [...], removed: [...]}` in `evidence/gate-<phase>.json`.
- The build PR's banner (R24's "Needs your close look") gains one line when the list grew: "The plan grew by 3 files since gate (b): `src/cache.py`, `src/cache_test.py`, `docs/cache.md`".
- Above a threshold (`gate.max_plan_growth`, default 5 files or half the approved list), the change reads as non-routine for the iteration cap (2), and the adversarial reviewer is told to judge the growth.
- It never parks. That keeps R24's direction and decision 21's list.

**(c) Recommendation.** Port adapted: fold into R24, with R26 counting the growth per change. Neither the kit's ledger-line counting nor its consensus record is ported. The framework's reviewer, panel and the owner's merge at (e) already judge plan changes; what is missing is only the number.

**(d) Reasoning.**
- The article's "the merged diff still matches plan.md" (p.17) is met formally today. "Matches the plan the owner approved" is not.
- The kit shows the value of keeping the two apart: its cap fired the re-plan rule on its own work.
- The cost is one comparison and one line.

**(e) Effect.**

| Criterion | Score | Why |
|---|---:|---|
| Safety | +1 | Scope creep is visible. |
| Attention | +1 | The owner sees the growth without diffing `plan.md`. |
| Autonomy | 0 | Nothing new waits. |
| Audit | +1 | The record holds the approved list and the final list. |
| Cost | 0 | |
| Article | +1 | p.16-17. |

Weighted 8.
- **Decisions:** 2 kept (the plan approved with the spec at (b)); 30 kept (the fast lane gets the line most); 21 kept.
- **Candidates:** R24 (amended), R26, R15 (the same approved-copy read), R19.

**What I checked.**
- `plugin/gate/checks.py:124-151` (`approved_base`, `approved_artifact`), `:645-691`, `:1640`.
- `plugin/pr/description.py` (plan conformance is a single pass/fail bullet, `:259-276`).
- `plugin/agents/adversarial-reviewer.md:36-37`.
- `docs/proposals/risk-hit-in-banner.md` (the banner lists risk hits only).
- crosswalk row `build-plansync` ("keep": the three layers, not a growth measure).

### L5. Merge by silence borrows the per-change grant, the locked-path floor and the "merged unread" record (score 8)

**(a) What it is.** lifecycle-axis-'s delegated mode, used on real work (bot merges #83, #100, #112):
- **The grant is per item.** The owner grants it on one approved intent (`mode: delegated`, `delegated-by`, `delegated-on`), only for listed risk classes (`risk-classes: [low]`, `.sdlc/delegation.yaml:28`). CI checks that the grant commit was authored by a human (`check_grant`, `scripts/check_artifact_chain.py:371-442`), and the merge reads the grant from the *base* branch, never the head (`scripts/delegated_merge.py:930-947`).
- **The agent signs in its own name.** It signs later artifacts `delegated` with its own handle, never `approved` (`scripts/sign.py`). As the owner put it, the ledger then shows "what I actually reviewed" (`work/delegated-mode/intent.md`).
- **The merge is a fixed, printed checklist.** A no-model workflow prints `CONDITION <name>: ok|refused|waiting` for nine conditions in order, then merges (`delegated_merge.py:883-1027`).
- **A floor of locked paths that policy can widen and never narrow.** `ALWAYS_LOCKED`: `.github`, `.claude`, `CLAUDE.md`, `REVIEW.md`, `.sdlc`, the verify scripts (`delegated_merge.py:86-94`). It is checked on both a rename's old and new names (`:663-683`).
- **Review binding.** The review verdict must be bound to the review workflow's own run, with `Important: 0`.

**(b) How it would work here.** R52 (accepted as a later step) lets the App merge a routine, green build PR after N hours of silence on an opted-in project. Its conditions:
- the plan is routine;
- every check is green;
- the PR carries no "Decisions taken for you";
- there is no risk-list hit;
- `deploy.production` is false.

These are stated once, project-wide (`docs/proposals/speed-beyond-the-sprint.md:46-48`). The port adds three things from the kit, none of which adds an owner act on the common path:
1. **A per-change switch at the gate the owner already passes.** On an opted-in project the default stays as R52 has it. The owner can turn a single change off with a label, `sdlc:merge-by-silence-off` (or on, on a project not opted in), at gate (a) or (b). The runner reads it from the base branch's `status.yaml`, the way `profile_override` is read today (`plugin/state/conventions.py`).
2. **A locked-path floor.** A diff touching a guardrail path (`.claude/**`, `CLAUDE.md`, `REVIEW.md`, `sdlc.yaml`), a `protected_paths` entry, `.github/**` or `evals/**` never merges by silence, whatever `risk_list` says. This reuses `plugin/hooks/protected_paths.py`'s matcher, so there is one spelling of the rule (the kit's lesson `one-path-spelling-in-guards.md`). Renames are judged on both names, as R59 asks.
3. **A truthful record.** The merge writes R11's approvals list entry as `{act: merged-unread, actor: <App>, at, conditions: [...]}`, never as the owner's merge. The PR gets the printed `CONDITION` lines as a comment.

Example: change 0024 is routine, green and has no decision taken. The digest shows "merges by silence at 18:00 unless you comment". At 18:00 the App merges. `status.yaml` records `merged-unread`, so the owner can tell, months later, which merges they never read.

**(c) Recommendation.** Port adapted: fold into R52's decision when R50's trigger comes. Not the kit's whole delegated mode: its tap, its signatures in front matter and its queue are not needed (section 4).

**(d) Reasoning.**
- R52 is accepted and already removes the owner's read. The kit is the only place the owner has run that idea live.
- Its history shows what to keep: separate words for "the owner approved" and "nobody read it", a floor the policy cannot lower, conditions read from the base branch, and a printed checklist.
- Each costs a few lines in a no-model step R52 needs anyway.

**(e) Effect.** Scored against R52 as proposed.

| Criterion | Score | Why |
|---|---:|---|
| Safety | +1 | The floor. |
| Attention | 0 | |
| Autonomy | +1 | The per-change switch extends silence to a single change on a project not opted in. |
| Audit | +2 | "merged-unread" versus the owner's merge, plus the printed conditions. |
| Cost | 0 | |
| Article | 0 | Both depart from the article's human merge equally. |

Weighted 8.
- **Decisions:** 4 (R52 amends it for opted-in projects, unchanged by the port); 13, 30 and 31 kept.
- **Candidates:** R52 (amended), R11 (the entry), R22 (the App merge), R59 (renames), R50 (trigger).

**What I checked.**
- `docs/proposals/speed-beyond-the-sprint.md:46-48`, `:67`.
- `docs/proposals/approvals-list.md`.
- `docs/decisions/4.md`, `30.md`.
- `plugin/hooks/protected_paths.py:46-61`.
- The kit: `scripts/delegated_merge.py:86-94`, `:663-683`, `:883-1027`; `.sdlc/delegation.yaml`.

### L6. GitHub Actions minutes are measured and budgeted (score 6)

**(a) What it is.** The kit ran 1,124 workflow runs in six days on a private repository and exhausted the account's 2,000 free Actions minutes. From then on "unable to run a single job since, including the owner's approval tap" (`work/ci-budget/intent.md:5`). Its answer:
- **A decision record.** It lists six crucial controls that stay and six loosened ones, each with its compensating control (`knowledge/decisions/ci-budget-crucial-and-loosened.md`).
- **A metric, `actions_minutes_per_pr`.** It counts billed minutes per PR, excluding scheduled and dispatched runs (`scripts/github_metrics.py`), and has its own band in `monitoring/bands.yaml`. A regression therefore becomes a filed issue.

**(b) How it would work here.**
- **What the framework measures.** Model spend (`evidence/spend.json`; R25's weekly ceiling and per-change budget). It does not measure runner minutes.
- **Why minutes matter.** One build job may run up to `timeout-minutes: 260` (`template/.github/workflows/sdlc-build.yml:73`), and a change runs several such jobs. On a private repository under a metered plan, a handful of changes can empty the monthly allowance. Every phase run, fix round and the digest then stop, and nothing in the framework sees it coming.
- **The port.** Extend R25's weekly window with a second meter. The digest job reads the repository's workflow-run timings (`GET /repos/{owner}/{repo}/actions/runs/{id}/timing`) and shows "Actions minutes this month: 1,140 of 2,000 (private repo)". Past a share set in `sdlc.yaml: gate.actions_minutes_warn` (default 80%), the digest's "Needs you" section says so. The digest workflow holds `contents: read`, `issues: write` and `pull-requests: read` today (`template/.github/workflows/sdlc-digest.yml:30-33`). It gains `actions: read` in the same change; the kit's lesson `workflow-permissions-name-every-api.md` (a missing scope failed silently for three days) is the reason.
- **The trial.** R61's trial-shape checks should ask `/sdlc-init` to note whether the repository is private, and set the meter on only then.

**(c) Recommendation.** Port adapted: fold into R25 (the meter) and R61 (when it applies). The kit's "loosened" list mostly does not transfer: the framework's phase jobs are dispatched, not run on every push.

**(d) Reasoning.**
- Cost is weighted 0, but running out of minutes is not a cost problem: it stops all autonomy at once, silently.
- The kit lost its own approval route that way.
- Public repositories have unmetered minutes, so the item is conditional; hence a score of 6 and medium confidence.

**(e) Effect.**

| Criterion | Score | Why |
|---|---:|---|
| Safety | 0 | |
| Attention | +1 | A warning arrives before a dead pipeline. |
| Autonomy | +1 | Avoids a hard stop. |
| Audit | 0 | |
| Cost | +1 | |
| Article | 0 | |

Weighted 6.
- **Decisions:** 1 (hosted runners) kept; 20 and 31 kept (pull-only digest).
- **Candidates:** R25 (amended), R61, R20, R53 (setup time is measured; minutes are not).

**What I checked.**
- `docs/proposals/weekly-window-guarded.md` (model spend only).
- `docs/proposals/speed-beyond-the-sprint.md` R53 (setup share, not minutes).
- `plugin/pr/digest.py`, `plugin/pr/counters.py` (no minutes).
- `template/.github/workflows/sdlc-build.yml:73`.
- The ArtCraft review's A10 (cancel superseded runs; patterns, not a meter).

### L7. A decision carries its revisit trigger, and the docs lint reports it when due (score 5)

**(a) What it is.** `knowledge/decisions/one-writer-until-ledger.md` is "Provisional, not final" (`:28-31`). It "expires on the first `cost_per_merged_pr` reading ... or on **2027-03-05**, whichever comes first". On expiry "the question reopens with one measurement, not a debate" (`:36-43`). Supersede and amend chains are explicit, and superseded records are kept (`self-enforcement-off.md:11-13`). The kit itself never checks the date (no code reads `2027-03-05`); the value is the form.

**(b) How it would work here.**
- **What decisions carry today.** Status, reversibility and `amended_by` (`docs/decisions/index.md`). One decision has a revisit trigger, but it lives only in a ROADMAP row: R50 revisits decision 17 after 20 changes past gate (e) on a project other than the sample.
- **The port.** An optional frontmatter field, `revisit: {on: 2027-01-31}` or `revisit: {when: "20 changes past gate (e) on a non-sample project", candidate: R50}`. `python tasks.py docs-lint` lists every decision whose date has passed as `docs-lint: decision 17: revisit due (R50)`. That is a report line, not a failure, so the lint stays green.

Example: decision 32 (deferred review by default) gets `revisit: {when: "R26's first-pass share over ten changes"}`, and the next docs-lint after R26 ships prints it.

**(c) Recommendation.** Port adapted: fold into R58 (the docs lint, part 2), generalising R50's one-off trigger. This is repository practice, not plugin code.

**(d) Reasoning.**
- The owner "wants to reconstruct decisions months later" (the criteria note, section 7). A decision that says when it should be looked at again is easier to keep honest.
- `CLAUDE.md` says not to reopen decisions without asking. A due line *is* the ask, raised at the right time.

**(e) Effect.**

| Criterion | Score | Why |
|---|---:|---|
| Safety | 0 | |
| Attention | +1 | The owner is told when instead of remembering. |
| Autonomy | 0 | |
| Audit | +1 | |
| Cost | 0 | |
| Article | 0 | |

Weighted 5.
- **Decisions:** none amended; the field is optional on any of 1-34.
- **Candidates:** R58 (amended), R50 (the pattern), R55.

**What I checked.**
- `docs/decisions/*.md` frontmatter (no `revisit`, `expir` or `provisional` hit).
- `tasks.py:446-464` (docs-lint).
- `docs/proposals/docs-lint-checks.md` (amendment and status consistency, no revisit).
- `docs/proposals/revisit-parallel-worktrees.md`.

### L8. Third-party actions are pinned by commit SHA (score 3)

**(a) What it is.** Every `uses:` in the kit is pinned to a full commit SHA with the tag as a comment, for example `actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1` (`.github/workflows/*.yml`). Its `check_workflow_permissions.py` also refuses `pull_request_target`, `write-all`, YAML anchors, a workflow without a top-level `permissions:` block, and `contents: write` outside an allowlist. Its tests do not check the SHA pins; those are a practice.

**(b) How it would work here.**
- **What the framework already has.** Its workflows' permission blocks are asserted one by one in `tests/test_templates.py` (`:325`, `:486`, `:647`, `:702`, `:757`, `:805`). That is stronger than the kit's generic rule.
- **What it lacks.** Every `uses:` is a mutable major tag:
  - `actions/checkout@v5` (62 uses);
  - `actions/create-github-app-token@v2` (16), which receives the App's private key;
  - `actions/setup-node@v5`;
  - `actions/upload-artifact@v4`;
  - `actions/cache@v4`;
  - `actions/setup-python@v7`.
- **The port.**
  - The template workflows pin each action to the SHA of the tag the framework tested, with the tag as a comment.
  - One test asserts that every `uses:` in `template/.github/workflows/` and `.github/workflows/` is `@<40 hex>`.
  - A framework release bumps the pins (R5's pin-bump PR can carry them).
  - `/sdlc-init` already reports project workflows as `outdated` when they differ (`plugin/init/sdlc_init.py`).

**(c) Recommendation.** Port as-is: fold into R44 (the sandbox closes what is open), or a plain template PR.

**(d) Reasoning.**
- The actions are first-party, so the risk is small.
- One of them, the App-token action, handles the credential that pushes as the project's App (decision 33).
- A SHA pin also records exactly which action code ran.
- Safety is weighted 1, hence the low score.

**(e) Effect.**

| Criterion | Score | Why |
|---|---:|---|
| Safety | +1 | |
| Attention | 0 | |
| Autonomy | 0 | |
| Audit | +1 | |
| Cost | 0 | |
| Article | 0 | |

Weighted 3.
- **Decisions:** 33 kept; 8 kept (the template ships the pins).
- **Candidates:** R44, R5, R59 (the security review's family).

**What I checked.**
- `grep uses:` over both workflow folders.
- `tests/test_templates.py` (permissions, no pin test).
- `docs/reviews/2026-10-19-plugin-security-review.md` (no SHA-pin finding).
- `docs/notes/20.md` (majors chosen by version, not by SHA).

### L9. Each record line names the model that wrote and the model that reviewed (score 2)

**(a) What it is.** The kit's convention: "A review runs on a different model from the one that wrote the work when a second is available ... The item's ledger records which model wrote and which reviewed" (`docs/sdlc/rules/30-conventions.md:21-23`). Its ledgers do so, for example "plan-reviewer claude-sonnet-5, security-reviewer claude-opus-5; the writer is claude-fable-5-1" (`work/chain-check-without-gh/log.md`), and its revision records name the model per reviewer (`docs/sdlc/templates/revision.md`). Nothing checks it mechanically: the chain check counts reviewers but never compares models.

**(b) How it would work here.**
- **What the framework holds.** More than the kit, but scattered:
  - `evidence/claude-<phase>.json` (`modelUsage`);
  - `adversarial-review-<phase>.model.json`, which only the hook may write (`plugin/hooks/panel_blind.py`);
  - a gate check that parks a reviewer on the wrong model (`reviewer_model`, `plugin/gate/checks.py:949`).
- **The port.** R11's approvals list gains `writer_model` and `reviewer_model` on each gate and fix-round line, copied from those files by the runner. For example: `{act: gate-c, result: continue, writer_model: claude-opus-5-5, reviewer_model: claude-opus-5-5, run: <url>}`.

**(c) Recommendation.** Port adapted: fold into R11. The kit's *rule* (reviewer on a different model) is not ported. R7 settled the in-run reviewer's model, and only the panel's advocate is kept off the session's model (`template/sdlc.yaml:44-46`).

**(d) Reasoning.** R11's own success test is "who approved each gate and why each fix round ran, from that file alone" (`docs/proposals/approvals-list.md:75`). Which models wrote and judged is part of that "why", and it is cheap.

**(e) Effect.**

| Criterion | Score | Why |
|---|---:|---|
| Safety | 0 | |
| Attention | 0 | |
| Autonomy | 0 | |
| Audit | +1 | |
| Cost | 0 | |
| Article | 0 | |

Weighted 2.
- **Decisions:** 21 kept.
- **Candidates:** R11 (amended), R7 (kept), R28 (its catalogue names models).

**What I checked.**
- `docs/proposals/approvals-list.md`.
- `plugin/panel/models.py`, `plugin/gate/checks.py:949`.
- The R7 row (done in 1.0.14).

### L10. One rule source renders CLAUDE.md, GEMINI.md and AGENTS.md (score -2, don't port)

**(a) What it is.**
- `docs/sdlc/rules/*.md` fragments with `targets:` and `order:` are rendered by `scripts/gen_context_files.py` into marked blocks of `CLAUDE.md`, `GEMINI.md` and `AGENTS.md`.
- `scripts/checks/context-drift.sh` fails verify on a hand edit.
- The same hook scripts are wired for Gemini CLI in `.gemini/settings.json`, and the production gate fails closed under Gemini.
- The kit's own record says live Gemini parity was never verified (`knowledge/decisions/gemini-hooks.md`, consequences).

**(b) How it would work here.**
- A `template/rules/` folder would be rendered by `/sdlc-init` into `CLAUDE.md` and `AGENTS.md`.
- The plugin's hooks would need a second wiring for another CLI.
- Every guarantee in decision 6 (managed settings, the pinned plugin in CI, the sandbox) is Claude Code's, so for another vendor the rules would be advisory.

**(c) Recommendation.** Don't port.

**(d) Reasoning.**
- Decision 8 distributes the framework as a Claude Code plugin.
- The article is written for Claude Code.
- The one other-vendor use the owner accepted is an external design opinion (R8), which needs no context file.
- For a small project, a second context file is cost with no reader.

**(e) Effect.**

| Criterion | Score | Why |
|---|---:|---|
| Safety | 0 | |
| Attention | 0 | |
| Autonomy | 0 | |
| Audit | 0 | |
| Cost | 0 | |
| Article | -1 | |

Weighted -2.
- **Decisions:** 6, 7 and 8 kept.
- **Candidates:** R8 kept.

**What I checked.** A grep of `plugin/` and `template/` for `gemini`, `AGENTS.md` and `GEMINI.md`, which matches only the OpenAI key pattern in `plugin/hooks/secrets_check.py`.

## 4. Checked and not counted

These are lifecycle-axis- mechanisms that are distinctive but not better than the framework at `main` plus its accepted candidates.

| Mechanism in the kit | Where | Why it is not counted |
|---|---|---|
| The approval "tap": `workflow_dispatch` plus `Approved-Run`/`Approved-Actor` trailers verified against the Actions run record | `.github/workflows/approve.yml`, `scripts/approve_dispatch.py`, `check_artifact_chain.py:216-310` | It exists because approval is a front-matter edit, which a phone cannot make safely. The framework's approvals are a merge or a label, already one tap in GitHub's app. The actor comes from GitHub's own event, checked by `is_owner_actor` (decision 24 as amended, decision 34). R21 covers the acts the app cannot do. |
| Two status words (`approved` by a human, `delegated` by the agent) in front matter, guarded by a hook that simulates the edit | `.claude/hooks/protect-approvals.sh:89-185`, `scripts/sign.py` | The framework keeps approval out of files the agent edits: it is the merge or the label event, read from GitHub with its actor (decisions 3 and 27; 24 as amended by 34). The part worth having, a separate record for what the owner did not read, is L5. |
| The risk detour: a low-only route found by reviewer consensus, else park | `scripts/check_detour.py`, `knowledge/decisions/risk-detour.md` | R24 (accepted) makes a risk hit a banner line the merge accepts, with no park and no detour. That is better for attention. |
| The session protocol and seed prompt: one item per session, successor scheduled, HANDOFF refreshed | `docs/sdlc/handoff/HANDOFF.md:37-52`, `.claude/skills/sdlc-run/SKILL.md:43-70` | Framework phases are CI runs whose state is `status.yaml` and the PR, so a run is disposable by construction. This repository's own sessions already use `docs/handoffs/` (R9 part 2). The kit's HANDOFF grew to 1,078 lines, the failure R9 part 2 cut. |
| The run queue and `.sdlc/active` pointer advanced on merge | `scripts/next_item.py`, `delegated_merge.py:1062-1110` | The framework runs every change in its own folder and branch concurrently. R51 (accepted) makes that safe; it needs no single pointer. |
| A Stop hook that blocks "done" when code changed since the last `VERIFY: PASS` | `.claude/hooks/stop-verify-reminder.sh` | The framework's runner runs the build, test and lint targets itself after every CI session (`plugin/ci/run_phase.py`, decision 29). Locally the gate's `commands` check runs them. A reminder is weaker than running them. |
| Self-registering checks (`scripts/checks/*.sh`, and a check that loses its executable bit fails verify) | `scripts/verify.sh:14-25` | A project adds its own checks to `commands.lint` or `commands.test`. Those are protected from the session (`sdlc.yaml` is a guardrail) and run by the runner. |
| The fix-kind test lock that locks only *existing* test files and allows new ones | `.claude/hooks/protect-tests.sh:15-32` | Weaker, not better. A new `conftest.py` or fixture file could change how the locked test runs. The framework locks every `test_paths` match after the reproducing test's commit (`plugin/hooks/test_file_lock.py:112-122`), and R34 adds the red/green proof. |
| The CI control-plane check that fails an agent-authored PR touching protected paths unless a human label is present | `scripts/check_control_plane.sh` | The framework blocks guardrail edits in three layers (decision 6). Gate check `guardrails` (`plugin/gate/checks.py:694`) and the runner's `guardrail_changes` refuse a guardrail diff in a phase run. The kit's own decision records the label persisting across later pushes as a residual. |
| The band detector's zero-variance and trailing-baseline handling | `scripts/detect_bands.py:36-75` | The framework's `plugin/detect/stats.py` has rolling statistics, Western Electric rules 1-4 and `min_sigma`, and it opens incident PRs and runbooks where the kit only files issues. |
| `adopt.sh` with a deliberately failing `VERIFY_CMDS` placeholder | `scripts/adopt.sh:412-420` | `/sdlc-init` detects the targets and verifies the feedback loop before change 0000 (`plugin/commands/sdlc-init.md`). The kit's scratch adoption also left checks that crash on missing scripts, masked by the placeholder (agent 2's run). |
| Decision records with "Residual risk" sections | `knowledge/decisions/*.md` | Good practice. The framework's security reviews (`docs/reviews/2026-10-19-plugin-security-review.md`) and R59 hold the same content for its code. |

## 5. What the kit shows about itself that the owner may want to know

These are not ports; they are observations the judge or owner may weigh.

- **Delegated mode's advance step was broken in production.** The post-merge advance pushed from a checkout older than the merge, so "no queue has ever advanced live" until `work/advance-push`. A standing grant was proposed and never approved (`work/standing-grant/intent.md`). The kit's most autonomous route was its least exercised. That argues for R52's measure-first placement.
- **No `incident.md` was ever written** (`work/*/incident.md` is absent). Its Maintain loop filed one issue (a real `pr_cycle_time_hours` breach), and the owner turned that into delegated mode instead. The framework's phase (f) has run live on the sample (NOTES §41-42).
- **Context management cost the owner by hand** until `work/session-chaining`. That is the main reason the framework's CI-run design fits the original goal better, as `docs/proposals/lifecycle-axis-features.md` says.
