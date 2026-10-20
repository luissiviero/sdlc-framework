---
type: Proposal
title: Review corrections reach CLAUDE.md through one standing pull request the owner merges when they choose
description: After each gate (e) merge, a deterministic step with no model opens or updates one pull request, "CLAUDE.md: Things Claude gets wrong", that collects every proposed line, each traceable to its finding and change, and starts the eval run and build-config's brief itself; the owner merges it whenever they choose, one act for many lines; the digest lists the lines waiting; the review pass may tag a reworded repeat with the earlier signature; no run edits CLAUDE.md and nothing notifies the owner.
status: accepted
roadmap: R37
sources:
  - id: study-entry
    resource: docs/reviews/2026-09-28-playbook-vs-framework/target-design.md
    title: "T15, confirmed at the close of the study on 2026-10-09; from the crosswalk row deploy-claudemd (better: the playbook; decision: blend), 2026-10-05, the owner's note completed the same day"
  - id: record
    resource: docs/reviews/2026-09-28-playbook-vs-framework.md
    title: "Section 7: the deploy-claudemd row of the decisions table and the re-checks of 2026-10-05 (0.3.4, then 0.3.5 adding a sentence to the row) and of 2026-10-09 against 0.3.6 (adding the brief's rule to the row); section 8 part 1: the close table's row for T15 (\"D6's wording, to confirm\"), and part 2's confirmed order"
  - id: crosswalk
    resource: docs/reviews/2026-09-28-playbook-vs-framework/crosswalk.json
    title: "Row deploy-claudemd whole; the decision fields of build-config (T1, the brief), deploy-tuning (T16, the same mechanism), x-queue (T28, the digest line) and x-measure (T31, the repeats per line)"
  - id: playbook
    resource: docs/reference/ai-native-sdlc-playbook.pdf
    title: "p.20 steps 4-5, its governance and its leading indicator: a mistake made twice goes into CLAUDE.md, kept under a page, code owners approve the edit in PR review, how often Claude repeats a mistake CLAUDE.md should have caught; p.30 steps 3-4: the eval suite runs on any change to CLAUDE.md and gates it; p.34 step 5: the correction goes in as part of the review that flags it the second time, and review flags an outdated CLAUDE.md"
  - id: decision-6
    resource: docs/decisions/6.md
    title: "Decision 6: the guardrails in three layers, CLAUDE.md the owner's (kept; whether an automation PR on CLAUDE.md fits its wording is to confirm)"
  - id: decision-4
    resource: docs/decisions/4.md
    title: "Decision 4: only the owner merges to main, the owner's merge the approval for every PR whoever opened it (kept)"
  - id: decision-20
    resource: docs/decisions/20.md
    title: "Decision 20: a review queue and a daily digest, nothing pushes to the owner (kept)"
  - id: decision-17
    resource: docs/decisions/17.md
    title: "Decision 17: the eval suite starts empty and fills from incidents (kept)"
  - id: decision-28
    resource: docs/decisions/28.md
    title: "Decision 28: sdlc:accept-findings, an accepted finding's CLAUDE.md proposal kept (kept)"
  - id: code
    resource: plugin/review/findings.py
    title: "signature, normalise, update_seen, claude_md_first_time_lines and claude_md_lines; with plugin/review/cli.py cmd_validate, plugin/review/REVIEW_PROMPT.md, template/REVIEW.md, plugin/pr/description.py, plugin/pr/digest.py, plugin/commands/sdlc-deploy.md, plugin/hooks/shell_guard.py, template/.github/workflows/sdlc-evals.yml, sdlc-design.yml, sdlc-build.yml, sdlc-abandon.yml, sdlc-fix.yml, plugin/release/cli.py, docs/OPERATING_MODEL.md; read at main 5542406, plugin 1.0.1"
generated: { by: sdlc-framework-session/ccr-01de3f80-ilnomi, at: 2026-10-15T20:00:00Z }
---

# Review corrections reach CLAUDE.md through one standing pull request the owner merges when they choose

**Status: proposed (roadmap R37), from study entry T15, confirmed by the owner on 2026-10-09.** *[2026-10-20: accepted 2026-10-16 (PR #215)]* Nothing is built. It amends no decision in substance: decision 6 keeps `CLAUDE.md` the owner's, who makes the change by merging; whether a pull request the automation opens on a guardrail file fits decision 6's wording is the one point the close left to confirm, and if the owner reads it as an amendment, a decision file comes before the intent, in a documentation PR of its own. It defines the CLAUDE.md line that R20 (T28) places in the digest and the mechanism R38 (T16) reuses for `REVIEW.md`; R26 (T31) adds the repeat count to each line.

## The problem

The (e) review already finds the mistakes the article wants written into `CLAUDE.md`, and proposes the line. What it lacks is the step from proposal to file:

- **Each line is the owner's by hand.** No run may edit `CLAUDE.md` (decision 6, the protected-paths hook), so a proposed line is quoted in the build PR's description and the owner applies it "in the PR review", one commit of their own per line. Only the owner may change `CLAUDE.md`, so the first proposal, a pull request per line, would call on the owner every time; the owner asked whether it would, and approved one standing pull request instead: one act for many lines.
- **A line not applied is lost.** Nothing lists the proposals the owner has not applied; the digest does not. Once the build PR is merged, its block is out of sight.
- **A reworded repeat is missed.** A repeat is matched on an exact signature of the pass, the file and the normalised summary, so the same mistake described in other words is a first occurrence again.
- **The eval run does not reach the owner's CLAUDE.md change by itself** when the automation opens the pull request: a `pull_request` run caused by the workflow token waits for a person's approval.

## What the article says

"When Claude makes a mistake twice, the correction goes into CLAUDE.md", which is kept "under a page, because Claude reads all of it at the start of a session" (p.20 steps 4-5). `CLAUDE.md` is version controlled, "changes to it are logged in git history, and code owners approve those changes in PR review" (p.20, governance). Its leading indicator is "how often Claude repeats a mistake CLAUDE.md should have caught", the corrections "tracked within the git history" (p.20). In the review stage: "When a review flags a mistake for the second time, the correction goes into CLAUDE.md as part of that review, and because review reads CLAUDE.md the mistake is caught from the next PR onwards. Review also flags when a change has made CLAUDE.md outdated" (p.34 step 5). The eval suite "runs non-interactively in CI on a schedule and on any change to CLAUDE.md, skills or hooks", and configuration changes are gated on its results (p.30 steps 3-4)[^playbook].

Read with the crosswalk row deploy-claudemd ("Review writes the correction"), the review writes the line as part of the PR it reviews, and a code owner approves it in PR review. The framework keeps the run out of `CLAUDE.md` and leaves the edit to the owner.

## What the framework does today

Read at `main` 5542406, plugin 1.0.1. The entry's "Today" was read at 619f01a (0.3.5). `git diff --stat 619f01a 5542406` over the files below touches `docs/OPERATING_MODEL.md`, `docs/notes/11.md`, `docs/notes/23.md`, `plugin/commands/sdlc-deploy.md`, `plugin/gate/checks.py`, `plugin/pr/description.py`, `plugin/review/REVIEW_PROMPT.md` and `template/REVIEW.md` only; `plugin/review/findings.py`, `plugin/review/cli.py`, `plugin/pr/digest.py`, `plugin/hooks/protected_paths.py`, `sdlc-evals.yml`, `sdlc-design.yml`, `sdlc-build.yml` and `plugin/release/cli.py` have an empty diff over that range. Two changes bear on this entry: the reviewer's brief of 0.3.6 (PR #133) and the shell guard of 0.3.7 (change 0002), both below[^crosswalk].

- **The record.** `review/cli.py validate` writes every finding's `signature` (`cmd_validate`, 153-216): the first 16 hex characters of a sha1 of the pass, the lower-cased file and the normalised summary, with no line number (`findings.py` `signature`, 90-108). `normalise` overwrites any signature the reviewer gave (180-181), and the brief tells the reviewer to leave it out (`REVIEW_PROMPT.md:81`). The record is `changes/.review-seen.json`, one per project (`state/conventions.py` `review_seen_rel`, 151-159); since 0.3.5 every `commit-phase` commit at (d) and (e) carries it when it changed and the gate's `clean_tree` sets it aside (`gate/checks.py:883-896`), so it reaches the default branch with the build PR's merge.
- **What counts as a repeat.** `update_seen` (`findings.py:274-316`) maps each signature to `count`, `first_change`, `last_change`, `summary`, `file` and `last_seen`; a finding is repeated only when its signature was recorded by an earlier change, occurrences inside one change never counting. `count` grows once per review run, not per change: `validate` runs again after every fix of the (e) loop (`sdlc-deploy.md:150`), and the record keeps no list of the changes that saw a finding.
- **The proposal.** A repeat becomes the line `- <summary> (seen in changes <first> and <this>; <pass>)` (`claude_md_lines`, 341-354); a finding whose summary or rule names `CLAUDE.md` is proposed the first time it is seen, as `- <summary> (change <id>; the owner edits CLAUDE.md)` (`claude_md_first_time_lines`, 322-338). Both go into `evidence/claude-md-proposals.md` in the change folder, rewritten by each `validate` and deleted when it has no line (`cli.py:186-202`), under a header comment that says "only the owner edits CLAUDE.md" (`cli.py:195-197`). The lines carry no signature. This repository's own change 0001 left one such file: a finding that its split made two lines of `CLAUDE.md` name the wrong files, an edit to existing lines rather than a line under the heading.
- **Where the owner sees it.** The build PR's description quotes the file under "Proposed CLAUDE.md lines" (`pr/description.py:599-602`), the module's docstring saying "the owner applies the line in the PR review" (`pr/description.py:25`). `/sdlc-deploy` tells the run never to edit `CLAUDE.md`, "the owner applies the line in the PR review" (`sdlc-deploy.md:153-158`); the protected-paths hook denies the edit (`protected_paths.py:46`), and since change 0002 the shell guard also denies a Bash or PowerShell command that would write to it (`plugin/hooks/shell_guard.py`, `docs/OPERATING_MODEL.md:121`). The digest lists the pull requests that carry an `sdlc:*` label (`digest.py:138`), the open `incident` pull requests with no gate label (`digest.py:71-75`, `:142`) and the counters, and nothing about `CLAUDE.md`.
- **The reviewer is told not to read the record (0.3.6, after T15 was recorded).** The brief says the second-occurrence rule "is the framework's own mechanism": "Do not read `changes/.review-seen.json`, do not grade a finding by how often it was reported, and never cite that rule in a finding's `rule` field" (`REVIEW_PROMPT.md:17-23`); `template/REVIEW.md:27-30` says the framework counts the repeats and a repeated finding keeps its own severity.
- **The eval run.** `sdlc-evals.yml` runs on a `pull_request` that changes `CLAUDE.md`, `.claude/**` or `evals/**`, nightly, and on a `workflow_dispatch` with no inputs (28-37); an empty suite is a green job (decision 17). Events the workflow token causes start no workflow run except `workflow_dispatch` and `repository_dispatch` (`docs/OPERATING_MODEL.md:97`); a `pull_request` run caused by the token is created "in an approval-required state" (`docs/notes/11.md:55-61`), seen live as `action_required` on the bot's runs (`docs/notes/23.md:35`). No role brief exists yet (build-config's brief is T1, R28).
- **What a merged PR with no change folder starts.** The design and build workflows run on every merged PR and end green after a 20-second "find the change" step when its files touch no `changes/<id>-<slug>/` folder (`sdlc-design.yml:51-56`, `sdlc-build.yml:52-58`); the release step skips "no change folder" (`release/cli.py:511-513`); the abandon workflow is for a PR closed without a merge. Read in the code; not verified live for a PR that changes `CLAUDE.md` alone.
- **The one sanctioned writer.** "The only sanctioned writer of guardrail files in a run is `/sdlc-init`'s install script, which only adds ...; every other guardrail change is made by the owner in a reviewed PR" (`docs/OPERATING_MODEL.md:121`).

## The proposal

The signature record and the rule that no run edits `CLAUDE.md` stay (decision 6); a repeat still counts only when its signature was first recorded by an earlier change, and a finding about `CLAUDE.md` itself is still proposed the first time. Three things are added, as the owner decided.

1. **One standing pull request.** After each (e) merge that produced a proposal, a deterministic step (no model) opens, or updates, one pull request titled "CLAUDE.md: Things Claude gets wrong" that collects every proposed line, each traceable to its finding and change. The owner merges it whenever they choose (for example once a week): one act for many lines. Until then it waits like any pull request, and nothing notifies the owner (decisions 11 and 20). Being a change to `CLAUDE.md`, it gets build-config's brief with the eval result (R28, T1) and the eval run, both started by the step itself after each update: the PR is opened and updated with the workflow token, whose `pull_request` runs wait for a person's approval, so the step dispatches the eval run, and the brief's run, explicitly on the PR's branch (the dispatch input on the brief's workflow is R28's own recommendation, not yet settled, below).
2. **The digest shows what waits.** The daily digest lists the proposals not yet merged and points to the standing PR. R20 places that line under "Worth knowing" (its row 8), with R26's count of the changes each mistake was found in.
3. **Reworded repeats.** The review pass reads the earlier findings' summaries and may tag a reworded repeat with the earlier signature, so the count catches it: a mistake described in new words still counts as its second occurrence.

The study corrected the row on the way: a repeat counts only across changes; nothing lists the proposals not applied; the article's repeat indicator (p.20) is not computed (R26, T31, takes it up).

## How it is judged

Over the first changes whose review proposes a line: every line of a merged change's `evidence/claude-md-proposals.md` appears in the standing PR, traceable to its finding and change, or is recorded as rejected; a rejected line is never proposed again; the eval run on the standing PR's head is started by the step, not by the owner's approval click; the owner's merge of the standing PR, a close without a merge, a review or a label on it starts no phase run beyond the green skips; and the owner's acts per applied line fall from one commit each to one merge for the batch. A run that edits `CLAUDE.md`, or a line that reaches `CLAUDE.md` without the owner's merge, is the failure.

## What to settle before building

The first five rows are the entry's open items and the sixth is the point the close table left to confirm; the rows marked "(This session's)" are questions this session adds. The Recommended column is this session's throughout; where it quotes the owner's note, the row says so.

| Question | Recommended |
|---|---|
| Whether the step runs after each (e) merge or on the digest's schedule | The owner's note says "after each (e) merge" (crosswalk row deploy-claudemd, the decision field; the record, section 7, the row's decision); the entry keeps the question open. Recommended (this session's): after each (e) merge, as the note reads |
| How the PR stays current when a line is already there, when the owner edits a line in the PR, or when a line is rejected (the PR closed, or a line deleted before merging), so a rejected line is not proposed again | Identity by signature, kept in the PR description's table (line, signature, finding file, changes), not in `CLAUDE.md`, which stays under a page (p.20 step 5). A signature already in the open PR or already merged is not added again. The step only adds commits on top of the branch and never rewrites a commit it did not make, so the owner's edits stay. When the PR closes, the step compares its final head with its own last commit: a line kept is merged, a line changed is merged as edited, a line deleted, or every line of a PR closed without a merge, is rejected by signature, read back from the closed standing PRs at every update, so it is never proposed again and no file on the default branch is needed. The comparison is made at the next update after the close, not on the close itself, so the step needs no trigger beyond the one the first row chooses |
| How a reviewer's "repeat of" tag is carried and checked | A field of its own, `repeat_of`, beside `signature` (which `normalise` overwrites, `findings.py:180-181`). The runner hands the pass a list of earlier signatures with their file and summary, not the record and its counts, so the 0.3.6 rule stays: no finding is graded by how often it was reported, a repeated nit is a nit (`REVIEW_PROMPT.md:17-23`); its "do not read the record" sentence becomes "read the list the runner gives you, only to tag a reworded repeat". `validate` honours a tag only when it names a signature an earlier change recorded, and ignores any other with a note. The proposed line says the repeat was the reviewer's tag, since a model's judgment now feeds a count that was deterministic |
| Whether merging the standing PR starts phase runs | Read in the code at 5542406: design and build end green after the "find the change" step, the release skips "no change folder", the abandon workflow is not fired by a merge (above), and on a close without a merge its job ends green after the "find the change" step when no change folder is found (`sdlc-abandon.yml:15-18`, `:50`); the owner's other acts on the standing PR fire workflows too: a "Request changes" review fires `sdlc-fix.yml` (decision 22; `sdlc-fix.yml:76-84`), and a label fires the test, deploy, fix, runbook or release workflow, each of which should end at its label filter or its "find the change" or "no change folder" skip; all to verify live on the sample. Recommended (this session's): the standing PR changes `CLAUDE.md` only, never a file under `changes/<id>-<slug>/`, and its branch matches no `sdlc/<id>/<phase>` pattern |
| How the explicit dispatch of the eval run and the brief's run is wired | The eval run: `sdlc-evals.yml` already has a `workflow_dispatch` (28-37), dispatched with `ref` set to the standing branch, the job holding `actions: write`; whether a dispatched run's result shows among the PR's checks is to verify. The brief's run: that the step starts it is the owner's note; how is R28's own recommendation, not a settled point. R28's approvals table gives "the automation's standing `CLAUDE.md` and `REVIEW.md` PRs" the same Platform & release brief as the owner's own guardrail PRs, citing the owner's notes on T15 and T16 (`roles-and-manager.md:118`), and its workflow row, marked as its own, has the brief's workflow, triggered on the guardrail PRs, also take "a `workflow_dispatch` input naming the PR or its branch" for the standing PRs of R37 and R38 (`roles-and-manager.md:164`). Recommended (this session's): the step dispatches the brief through that input with the standing PR's number; until R28 is built with it, the step dispatches the eval run only |
| Whether a PR the automation opens on `CLAUDE.md` fits decision 6's wording (the close table: "D6's wording, to confirm") | Still the owner's to confirm. This session's reading: it fits. Decision 6's layers bind what a run's tools can do; the step is not a run and has no model; decision 4 makes the owner's merge the approval "for every PR, whoever opened it"; the owner still makes the change by merging. `docs/OPERATING_MODEL.md:121` names `/sdlc-init`'s install script as the only sanctioned writer "in a run"; the build change adds the step there as the one writer outside a run, proposing only. If the owner reads it as an amendment, a decision file before the intent |
| (This session's) A first-time finding about `CLAUDE.md`'s own text | It asks for an edit to existing lines, not a line under the heading (change 0001's file, above), which a step with no model cannot write. Recommended: listed in the standing PR's description as an edit for the owner to make on that branch, not appended under "Things Claude gets wrong" |
| (This session's) "Found in N changes" on each line (R26, T31) | The record counts review runs, not changes, and keeps only the first and last change (`findings.py:274-316`); it gains the list of changes per signature, in this change or R26's, whichever is built first |
| (This session's) The default branch's `CLAUDE.md` moves while the PR is open | The step merges the default branch into the standing branch at each update; on a conflict it leaves the branch as it is and the digest line says so; nothing parks, since no change is waiting on it |
| (This session's) The build PR's "Proposed CLAUDE.md lines" block | Kept, with one sentence saying the lines go to the standing PR after the merge, so "the owner applies the line in the PR review" (`sdlc-deploy.md:158`, `pr/description.py:25`) is rewritten, beside the block itself (`pr/description.py:599-602`) and the proposals file's header comment (`review/cli.py:195-197`) |
| The title, the branch and the step's names | Judged with T4 (R45); "CLAUDE.md: Things Claude gets wrong" is the owner's title |

## Considered and not chosen

- The (e) run editing `CLAUDE.md` in the build PR, as the article does: the run would edit the file that steers it, which decision 6 forbids.
- A pull request per proposal: one owner act per line. It was the first proposal; the owner asked whether it would call on them every time and approved the standing PR instead.
- Applying the lines without the owner: a finding's text comes from a model reading the code, so an unattended write would let code shape the instructions every later run follows.

## Decisions it touches

None amended in substance. 6 is kept: no run edits `CLAUDE.md`, the owner makes the change by merging; whether an automation PR on `CLAUDE.md` fits its wording is to confirm, and only if the owner reads it as an amendment does a decision file come before the intent, in a documentation PR of its own (this proposal writes none and reserves no number). 4 and 5 are kept (the automation identity pushes a branch, the owner alone merges). 11 and 20 are kept (no notification; the digest is where the lines show). 17 is kept (the eval run on the standing PR passes "no cases" while the suite is empty, and build-config's brief says so). 22 is kept (an owner's "Request changes" review on the standing PR fires `sdlc-fix.yml`, which should skip a PR with no change folder; to verify on the sample). 12 is kept (the review pass runs where it runs; its output gains a field). 28 is kept: an Important finding the owner accepts with `sdlc:accept-findings` still yields its `CLAUDE.md` proposal (its settled table: "the proposal records a pattern, the waiver records one decision"), so the step collects that line into the standing PR like any other. 27 and 29 were read and neither touches this proposal.

## Order

In the confirmed order's fifth group, "the rest in any order" (the record, section 8 part 2), after the roles. It changes `plugin/` and `template/`, so it ships as a plugin version with tests and reaches a project through `/sdlc-init`'s workflow copies. Its dependencies:

- **R28 (T1, the roles):** the brief on the standing PR. The step can ship before R28 with the eval run alone and dispatch the brief once R28's brief workflow covers the standing PRs and takes a dispatch, as R28 recommends and has not yet settled (the row above).
- **R20 (T28):** places the digest line (its row 8). The line is defined here; R20 places it in its order, or, if this ships first, it goes at the end of today's digest until R20 reorders it.
- **R26 (T31):** "found in N changes" on each line and the mark on a build PR when a mistake recurs after its line merged; it needs the record's list of changes (above).
- **R22 (T18):** if ruleset 2 requires `sdlc/review` on every pull request, the step posts the passing check on each new head of the standing PR itself, as T18 names; whichever of the two is built second adds it.
- **R38 (T16):** the same mechanism for `REVIEW.md`; built after this, reusing the step (whether the two share one workflow is T16's open item).
- **R35 (T13):** the eval suite that gives the standing PR's eval run something to say; not a prerequisite.
- **R45 (T4):** the names, last.

| Part | Where | When |
|---|---|---|
| The step: open or update the standing PR, the description table, the comparison with a closed standing PR at the next update, the rejected record | a new merge-fired workflow or job in `template/.github/workflows/` (the shape this session recommends, following the note's "after each (e) merge"), a script under `plugin/review/` | Now, after a live check on the sample that a PR changing `CLAUDE.md` alone starts no phase run when merged, closed without a merge, reviewed or labelled |
| The eval run dispatched on the standing branch | the step, `sdlc-evals.yml` unchanged | Now; whether its result shows on the PR's checks verified first |
| The `repeat_of` field, the list given to the pass, the brief's sentence | `plugin/review/findings.py`, `cli.py`, `REVIEW_PROMPT.md`, `template/REVIEW.md` | Now, same change |
| `OPERATING_MODEL` §8's writer sentence; the build PR's block sentence | `docs/OPERATING_MODEL.md`, `plugin/pr/description.py`, `plugin/commands/sdlc-deploy.md` | Now, after the owner confirms decision 6's reading |
| The brief's run | the step | With R28 |
| The digest line | `plugin/pr/digest.py` | With R20, or at the end of today's digest if this ships first |
| The count of changes per line | `plugin/review/findings.py` record | With R26 or this change, whichever is first |

[^playbook]: `docs/reference/ai-native-sdlc-playbook.pdf` p.20, p.30, p.34.
[^crosswalk]: `docs/reviews/2026-09-28-playbook-vs-framework/crosswalk.json`, row deploy-claudemd, and `target-design.md` T15 ("Today").
