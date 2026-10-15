---
type: Proposal
title: The runbook PRs get the review pass — every automated code change the owner merges has been reviewed
description: The REVIEW.md pass that runs at gate (e) also runs, in a fresh-context claude -p session, on every pull request a built-in runbook opens (revert-pr, quarantine-flaky-test), and publishes its findings and the sdlc/review check run on that PR, so the owner merges a revert or a quarantine with its findings in front of them; the (e) pass and its blocking Important finding stay as they are, and no other PR gains a pass.
status: proposed
roadmap: R36
sources:
  - id: study-entry
    resource: docs/reviews/2026-09-28-playbook-vs-framework/target-design.md
    title: "T14, confirmed at the close of the study on 2026-10-09; from the crosswalk row deploy-review (better: both; decision: blend), 2026-10-04"
  - id: crosswalk
    resource: docs/reviews/2026-09-28-playbook-vs-framework/crosswalk.json
    title: "Row deploy-review whole; the decision fields of maintain-act (T24: point 4, 'T14's review pass on the runbook PRs, already decided') and deploy-approve (T18: 'a runbook PR carries T14's own sdlc/review')"
  - id: record
    resource: docs/reviews/2026-09-28-playbook-vs-framework.md
    title: "Section 7, first bullet (the close, 'all as recommended'); section 8, part 1 (the close table row 'T14 The runbook PRs get the review pass | deploy-review | none | yes | yes') and part 2 (the format, the confirmed order: T14 among 'the rest in any order')"
  - id: artcraft
    resource: docs/reviews/2026-10-13-artcraft-vs-framework/a3-revision.md
    title: "Row 8: the quarantine's --deselect is exempt from R15's ratchet by construction; whether T14's pass lists the skip it adds is left to T14"
  - id: playbook
    resource: docs/reference/ai-native-sdlc-playbook.pdf
    title: "p.32: all PRs get an identical set of review passes; p.33: findings do not approve or block a PR on their own, the check run's machine-readable tally; p.43: at 3σ Claude may act only by opening a PR into the review gate or triggering a pre-approved runbook; p.44-45: resulting changes go through the normal PR review gate; the agent quarantines the flaky test or opens a revert PR, and the review gate decides"
  - id: decision-12
    resource: docs/decisions/12.md
    title: "Decision 12: the review pass is a claude -p CI job with REVIEW.md, fresh context, findings as a check run with a tally (applied to one more kind of PR; not amended)"
  - id: decision-14
    resource: docs/decisions/14.md
    title: "Decision 14: 3σ runbooks split by blast radius, revert and quarantine pre-approved (unchanged)"
  - id: decision-26
    resource: docs/decisions/26.md
    title: "Decision 26: the rehearsed rollback pre-approved on a declared production (unchanged)"
  - id: decision-28
    resource: docs/decisions/28.md
    title: "Decision 28: sdlc:accept-findings, honoured at gate (e) only (unchanged; a runbook PR has no gate)"
  - id: code
    resource: plugin/detect/runbooks.py
    title: "_pr_with_label, _revert, _quarantine, project_runbook and the record; with plugin/detect/cli.py _act, cmd_dispatch, cmd_finish and cmd_go, plugin/detect/routes.py apply_forced, template/.github/workflows/sdlc-detect.yml and sdlc-runbook.yml, template/bands.yaml, plugin/review/cli.py check-run, plugin/review/REVIEW_PROMPT.md, template/REVIEW.md, plugin/ci/run_phase.py (the review phase), plugin/gate/checks.py check_findings, plugin/commands/sdlc-fix.md (the (f) round); read at main 5542406, plugin 1.0.1"
generated: { by: sdlc-framework-session/ccr-01de3f80-ilnomi, at: 2026-10-15T20:00:00Z }
---

# The runbook PRs get the review pass: every automated code change the owner merges has been reviewed

**Status: proposed (roadmap R36), from study entry T14, confirmed by the owner on 2026-10-09.** Nothing is built. It amends no decision: decision 12 (the review pass is a CI job) is applied to one more kind of pull request, and decisions 14 and 26 (which runbooks run without a person) are unchanged. It is one of the entries the confirmed order places in "the rest in any order"; R41 (T24) lists it as its point 4, "already decided", and builds nothing for it, and R22 (T18) names the check this proposal posts as the one a runbook PR carries under its second ruleset.

## The problem

Among the pull requests the automation opens for the owner's merge are the build PR, which the REVIEW.md pass reads at (e) before the owner sees it; the intent and spec+plan PRs and the dismissal PRs (`detect/cli.py dismiss --open-pr`, `sdlc-abandon.yml:105`), which carry no code; and the runbook PRs, which carry code and which no review pass reads. At 3σ the `revert-pr` runbook pushes a `git revert` of one commit of the default branch, and `quarantine-flaky-test` a `--deselect` line in pytest's configuration, each on its own branch with a PR labelled `incident`, and the owner's merge applies it (`plugin/detect/runbooks.py:5-15`, `:215-236`). So the one automated code change that reaches the owner's merge unreviewed is the one opened at the worst moment, during an incident. The owner's note: "revert-pr and quarantine-flaky-test change code, and I merge their PRs with no review pass today."

## What the article says

"All PRs get an identical set of review passes, with findings ranked by severity" (p.32). The passes are bugs, security and compliance with `spec.md`, `plan.md` and the design principles; "Findings do not approve or block a PR on their own", and a platform engineer who wants to gate merges reads "the severity counts that the check run publishes as a machine-readable tally" (p.33). At 3σ "Claude may act, though only by opening a PR into the review gate or triggering a preapproved runbook" (p.43); "resulting changes go through the normal PR review gate" (p.44-45); and the example is this framework's two runbooks: "When the CI test failure rate breaches 3σ, the agent quarantines the flaky test or opens a revert PR, and the review gate decides" (p.45). The quarantine PR's body already quotes that line (`runbooks.py:60-62`, `:711`), and both runbook PR bodies say "The review gate decides: merge to apply, close to drop" (`:64-67`, `:298`, `:713`); what is missing is the review the line names.

## What the framework does today

Read at `main` 5542406, plugin 1.0.1. The entry's "Today" was read at 619f01a (plugin 0.3.5); `git diff --stat 619f01a 5542406` is empty for `plugin/detect`, `sdlc-detect.yml`, `sdlc-runbook.yml` and `sdlc-deploy.yml`; for `plugin/review`, `plugin/gate`, `plugin/commands`, `plugin/ci`, `template/REVIEW.md` and `template/bands.yaml` it lists eight files: `plugin/review/REVIEW_PROMPT.md` and `template/REVIEW.md` (the second-occurrence wording), `plugin/gate/checks.py` (the `lesson_and_eval` check), `plugin/gate/artifacts.py` (the lesson fields), `plugin/commands/sdlc-deploy.md` (step 0b), `plugin/commands/sdlc-maintain.md` (the lessons index), `plugin/ci/settings.ci.json` (a `sandbox.filesystem.denyWrite` list and one more allowed host, which apply to every session, the review pass included) and `plugin/ci/run_phase.py`. None of the changed parts is what the entry relies on. Every line of the entry's "Today" still holds; three precisions follow.

- **The (e) pass.** The deploy job's first phase step (after checkout and setup) runs `run_phase.py --phase review` in a fresh-context `claude -p` session (`template/.github/workflows/sdlc-deploy.yml:97-107`) with `Read,Grep,Glob,Bash(git *),Write` (`run_phase.py:193-194`): three passes, Important or Nit, at most five nits (`template/REVIEW.md:6-18`), written to `evidence/review-findings.json`. `review/cli.py check-run` posts the `sdlc/review` check run on the findings' `head`, `success` with no Important finding and `failure` otherwise, titled "N Important, M nits" (`plugin/review/cli.py:220-280`, `:235`). A fix loop runs while an Important finding stands (`plugin/commands/sdlc-deploy.md:135-152`) and gate (e) fails on an open one (`plugin/gate/checks.py:515-552`; the check blocks at any gate where a findings file exists, and requires one at (e) only, `gate/artifacts.py:121`). Decision 28 (accepted, not yet built: `git grep -n -i "accept.findings" 5542406 -- plugin template` returns nothing) adds `sdlc:accept-findings`, which accepts a head's Important findings by signature, at gate (e) only.
- **The review run is shaped for a build change.** `run_phase.py` runs the review only for a change whose gate (d) passed (`PREVIOUS_PHASE` and `GATE_MUST_HAVE_PASSED`, `:154-156`), on the build branch (`BRANCH_PHASE`, `:461`), and the brief reads `intent.md`, `spec.md`, `plan.md` and the diff `base...head` (`plugin/review/REVIEW_PROMPT.md:24-27`). `template/REVIEW.md`'s compliance pass and its `plan.md` rule assume a spec and a plan (`:10-11`, `:25-26`). An incident change at (f) has an intent, a detection record and a proposal, no spec or plan.
- **The runbook PRs.** `revert-pr` works on `sdlc/<id>/revert-<sha7>`, title `revert(<id>): <subject>` (`runbooks.py:292-295`); `quarantine-flaky-test` on `sdlc/<id>/quarantine`, title `quarantine(<id>): <node id>`, never touching a test path (`:648-665`, `:709-715`). Both branches start from the default branch, so they carry no change folder; the outcome, with `pr_url`, `pr_number` and `commit`, is written to `evidence/runbook-<name>.json` on the incident branch (`detect/cli.py:801-852`, the write at `:848-851`; the path from `runbooks.py:828-830`). Each run is idempotent: a re-run reuses the branch and the open PR (`runbooks.py:21-22`, `:309-315`). In `template/bands.yaml` both are `preapproved` (`:35-38`).
- **Precision 1: a runbook PR is opened from three places, not only the detect job.** A pre-approved route runs in the detect job's finish step, `detect/cli.py finish`, with no model and the project's runbook secrets in its `env:` (`sdlc-detect.yml:187-195`). A route with `authorization: go`, and every runbook route of a forced finding (a rehearsal: `plugin/detect/routes.py:185-194`), runs in the runbook job after a person's `sdlc:go` label (`sdlc-runbook.yml:99-107`; `detect/cli.py:1151-1216`; today any person's, never the workflow token or a `[bot]`, `sdlc-runbook.yml:10-14`; R41's point 1 narrows it to the owner's), a job that starts no `claude` and reads no model credential (`sdlc-runbook.yml:15-18`). And a "Request changes" comment on the incident PR that names another route makes the (f) fix round re-run `detect/cli.py dispatch` inside its session (`plugin/commands/sdlc-fix.md:119-125`), which R41 (T24) moves to a step of `sdlc-fix.yml` after the session that runs `detect/cli.py`'s deterministic tail, with the runbook secrets in that step's `env:` alone.
- **Precision 2: no workflow run starts on the runbook PR by itself.** The PR is opened with the workflow token: its `opened` run waits for a person's approval and its `labeled` event starts none (`docs/notes/11.md` §11a, `:55-62`); `workflow_dispatch` and `repository_dispatch` always start a run (same lines). The detect job holds `checks: write` and `actions: read` (`sdlc-detect.yml:55-60`); the runbook job holds `contents`, `pull-requests` and `issues: write` only (`sdlc-runbook.yml:31-34`), so neither can dispatch a workflow today, and the runbook job cannot post a check run.
- **Precision 3: a project runbook opens no PR.** `maintain.runbooks[]` with a `command` runs that command without a shell and records its exit code and output tail (`runbooks.py:729-782`); it commits nothing and opens no pull request the framework knows of.
- **Not seen live.** No runbook PR has been opened on the sample yet; the provocation of 2026-10-13 left `revert-pr` nothing to do (`docs/notes/41.md:43`).

## The proposal

Added; the (e) pass stays as it is.

1. **The runbook PRs get the same pass.** After a built-in runbook opens its PR, the REVIEW.md pass runs on it in a fresh-context `claude -p` session, as at (e), and publishes its findings and the `sdlc/review` check run with its tally on that PR's head, so the owner merges a revert or a quarantine with its findings in front of them. The three passes are REVIEW.md's: bugs, security and compliance. What the compliance pass reads in place of `spec.md` and `plan.md`, which an incident change does not have, is settled below.
2. **Blocking stays at (e).** An open Important finding still fails gate (e), as `check_findings` does today; the framework keeps that departure from the article (p.33) because the owner looks in once or twice a day and the fix loop has already run when the build PR reaches them. What a runbook PR's findings do is the first item to settle below.
3. **The other PRs stay as they are.** Intent and spec+plan PRs are covered by T1's briefs (R28) and the adversarial reviewer at (b); the owner's own configuration PRs by build-config's brief with the eval result (T1); a fix round's push on the build PR is judged by the (e) pass that follows. No extra pass on each fix round's PR.
4. **Not proposed here.** No change to which runbooks run without a person (decisions 14 and 26, and R41's conditions). No new verb: the owner's merge applies the runbook and closing the PR drops it, as `runbooks.py:64-67` says; another route is a "Request changes" on the incident PR (R41's point 3). The PR body's acts are R19's block; the PR's place in the digest is R20's "Needs you".

## How it is judged

The entry names no measure; this one is the session's recommendation. On the sample, a lint-clean provocation that fails a test and stays on `main` until a detect run reads it (`docs/notes/41.md:43`), or a forced tier-3 rehearsal that the owner answers with `sdlc:go`: the runbook PR carries an `sdlc/review` check run on its head with the tally in its title, and its findings in its body, before the owner opens it; the same holds for a runbook the Go path ran. A runbook PR the owner can merge with no `sdlc/review` on its head is the failure. Measured after: the share of runbook PRs merged with a pass on their head, 100 % (none has been opened live yet, so there is no "before" beyond "no pass exists").

## What to settle before building

The entry's three open items first, then the session's own additions, marked "(mine)". None is settled by a later decision, proposal or owner choice.

| Question | Recommended |
|---|---|
| What a runbook PR's findings do: inform the owner only, or hold the PR when one is Important (a revert is meant to land fast; under R22's ruleset 2 the runbook PR's `sdlc/review` is the required check, so a `failure` would hold the revert) | Inform only, as the article's findings do (p.33) and as p.45 has it ("the review gate decides", the owner's merge being that gate here): the check posts `neutral` when an Important finding stands and `success` otherwise, the title carrying the counts either way, so the tally stays machine-readable and the revert is not held. That a `neutral` conclusion satisfies a required check is to verify on the sample, with a temporary ruleset requiring `sdlc/review` (R22's ruleset 2 need not exist yet; R22's own check items can share the run); if it does not, the check posts `success` with the counts in its title (mine, on the entry's open item) |
| Which workflow runs the pass: the detect job after it opens the PR, or a job it dispatches | A small workflow of its own, dispatched (`workflow_dispatch`, `change_id` and the runbook branch) after every place a runbook PR is opened: the detect job's finish step, the runbook job's Go step and the (f) round's dispatch (R41's `sdlc-fix.yml` step once it lands). It holds the model credential, `checks: write` and `contents: write` for the incident branch, and no runbook secret; the Go job, which holds them and starts no model (`sdlc-runbook.yml:15-18`), stays model-free. The dispatch itself runs in a separate final job of the detect and runbook workflows, like R20's dispatch job (`actions: write` only, the default branch as ref), fed by a step output of the finish or Go step: the detect job runs the phase (f) session with `GITHUB_TOKEN` in its environment (`sdlc-detect.yml:141-152`) and the finish and Go steps hold the runbook secrets, so neither gains `actions: write`, which can dispatch any workflow. The (f) path's dispatch follows the same pattern, a final job of `sdlc-fix.yml` fed by a step output of R41's step; that workflow grants `actions: write` at its top level today (`sdlc-fix.yml:56-61`), so whether R41's secrets-holding step keeps it is R41's design to settle. Its name is a placeholder judged with T4 (R45) (mine, on the entry's open item) |
| Whether a project runbook (`maintain.runbooks[]` with a command) that changes files gets the same pass | No pass: it opens no PR the framework knows of (`runbooks.py:729-782`) and its record keeps the exit code and output tail; a command that changes the repository is the owner's own code, read when the owner adds it to `sdlc.yaml` (build-config's brief, T1, R28). Revisit if a project runbook ever opens a PR through the framework (mine, on the entry's open item) |
| Where the findings live, since the runbook branch carries no change folder (mine) | On the incident branch, `evidence/review-findings-<runbook>.json`, with `head` the runbook PR's head commit; the check run is posted on that commit, and `review/cli.py` gains a mode for it, beside the build-change review that requires gate (d) (`run_phase.py:154-156`) |
| What the reviewer reads in place of `spec.md` and `plan.md` (mine) | A runbook brief beside `REVIEW_PROMPT.md`: REVIEW.md's three passes and Important rule; the incident `intent.md`, `evidence/detection.json`, `evidence/proposal.json` and `evidence/runbook-<name>.json`; the runbook PR's diff against its base; compliance read against the runbook's own contract (one revert of the named commit; one `--deselect` line, no test file); bugs including, for example, a revert of a commit a later commit builds on (a revert that conflicts is aborted and opens no PR, `runbooks.py:330-339`); REVIEW.md's `plan.md` rule does not apply |
| Whether a re-run that reuses the open runbook PR (`runbooks.py:21-22`, `:309-315`) runs the pass again (mine) | Yes when the PR's head is one the pass has not read, no otherwise: the check run binds a head, so a new head needs its own |
| A fix loop on a runbook PR (mine) | None: a revert or a `--deselect` line is what it is; an Important finding means the owner closes the PR and, if they want, names another route on the incident PR (R41's point 3). So no iteration is counted (decision 29's counter is untouched) |
| Whether the pass lists the skip the quarantine adds (left to T14 by ArtCraft row A3's revision, row 8) (mine) | No separate list: the PR title already names the node id (`runbooks.py:665`) and the revision found the listing adds nothing the title does not say |
| Where the owner sees the findings besides the check (mine) | The runbook PR's body, under the body it carries today (`runbooks.py:296-299`, `:709-714`), the tally first; R19's block names the act, R20's digest line is unchanged |
| The pass's cost (mine) | Recorded as the incident change's spend, counted against R25's (T30) budget and weekly ceiling like any run |

## Considered and not chosen

- Leaving the runbook PRs unreviewed: they are the one automated code change that reaches the owner's merge without a pass (the owner's note; the row corrected).
- Moving the (e) pass to every PR, as the article's "all PRs" (p.32): intent and spec PRs are covered by T1's briefs and the (b) reviewer, the owner's configuration PRs by build-config's brief, and a pass per fix-round push would repeat the (e) pass that follows (the owner's note).
- Making the (e) pass non-blocking, as the article's findings are (p.33): the owner keeps the blocking Important finding at (e), so what reaches them has had its fixes (the owner's note; decision 28's label is the waiver).
- Running the pass on the runbook PR's own `pull_request` event: the workflow token's PR starts a run that waits for a person's approval (`docs/notes/11.md` §11a).

## Decisions it touches

None amended, as the close table records ("none"). Decision 12 is applied to one more kind of pull request: the same fresh-context `claude -p` job, REVIEW.md and the check run with its tally. Decisions 14 and 26 (which runbooks run without a person) are not changed by this proposal; R39 (T20) and R41 (T24) each add a condition to decision 26's rollback pre-approval, which does not touch the revert and quarantine runbooks reviewed here. Decision 28 is kept: `sdlc:accept-findings` stays at gate (e) only, and a runbook PR has no gate to accept findings at. Decisions 11 and 20 are kept: the pass notifies no one (decision 20); whether its findings hold the PR is the first item to settle. Decision 25 is kept: the incident PR's triage is untouched. No decision file is written for this proposal.

## Order

In the confirmed order T14 is among "the rest in any order" (the record, section 8). It changes `plugin/` and `template/`, so it ships as a plugin version with tests and reaches a project through `/sdlc-init`'s workflow copies. Its dependencies:

- **R22 (T18):** R22's second ruleset requires `sdlc/review` on every PR and names this proposal's check as the runbook PR's. If R22's ruleset ships first, a runbook PR needs a passing check from somewhere until this one ships; building R36 before or with R22's ruleset avoids that gap (mine).
- **R41 (T24):** its point 3 moves the (f) round's dispatch to a step of `sdlc-fix.yml` after the session that runs `detect/cli.py`'s deterministic tail; the pass's dispatch from that path is simplest after it. Before it, a step of `sdlc-fix.yml` after the session dispatches the pass when the session wrote a new runbook record (mine).
- **R19 (T27) and R20 (T28):** the runbook PR's block and its digest line are theirs; this proposal adds the findings to the PR body only. R20's separate dispatch-only job (`actions: write` and nothing else) is the pattern the pass's dispatch follows; whichever lands first adds the job to the detect workflow (mine).
- **R25 (T30):** the pass's spend counts against its budget when R25 lands.

| Part | Where | When |
|---|---|---|
| The runbook review mode and its brief | `plugin/review/` (`cli.py`, a brief beside `REVIEW_PROMPT.md`), `plugin/ci/run_phase.py` | Now |
| The dispatched review workflow | `template/.github/workflows/`, `/sdlc-init` | Now, after the `neutral` check is verified on the sample with a temporary required-check ruleset |
| The dispatch after the finish and Go steps, from a separate final job holding only `actions: write` (R20's pattern) | `plugin/detect/cli.py` (the step output), `sdlc-detect.yml`, `sdlc-runbook.yml` | Now; shares the detect workflow's dispatch job with R20 if R20 lands first |
| The dispatch from the (f) round | `sdlc-fix.yml` (a final job fed by R41's step after the fix session), `plugin/detect/cli.py` (the step output) | With R41, or the interim step above |
| The findings in the runbook PR body | `plugin/detect/runbooks.py` | Now; R19's block when it lands |
