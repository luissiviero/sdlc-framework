---
type: Proposal
title: The reviewer is tuned twice a month from signals already on record, through a standing REVIEW.md PR
description: A scheduled read-only run twice a month reads the period's review findings and the signals already on record (findings the owner waived or overturned, findings the panel settled, repeats, nit volume against the cap, findings in paths CI already enforces), writes a committed tuning report, and its proposed REVIEW.md edits go into one standing pull request, "REVIEW.md: tuning", kept up to date by a deterministic step that also starts the eval run and the brief; the owner merges it when they choose, rates nothing, and is notified of nothing.
status: accepted
roadmap: R38
sources:
  - id: study-entry
    resource: docs/reviews/2026-09-28-playbook-vs-framework/target-design.md
    title: "T16, confirmed at the close of the study on 2026-10-09; from the crosswalk row deploy-tuning (better: the playbook; decision: blend), 2026-10-05; the owner chose twice a month"
  - id: crosswalk
    resource: docs/reviews/2026-09-28-playbook-vs-framework/crosswalk.json
    title: "Row deploy-tuning (whole); the decision fields of deploy-review (T14), deploy-claudemd (T15, the standing-PR mechanism) and build-config (the brief on the owner's guardrail PRs)"
  - id: record
    resource: docs/reviews/2026-09-28-playbook-vs-framework.md
    title: "Section 7, the close; section 8, the close, part 1, the table row 'T16 The reviewer tuned twice a month | deploy-tuning | none | yes | yes'"
  - id: playbook
    resource: docs/reference/ai-native-sdlc-playbook.pdf
    title: "p.33 step 2: the tech lead writes REVIEW.md, what is Important, what is a Nit, what to skip; p.34 step 6: once a month the tech lead tunes the setup by rating findings and capping Nit volume, generated paths and anything CI enforces excluded; p.35: findings, fixes, ratings and approvals logged in the PR history"
  - id: decision-6
    resource: docs/decisions/6.md
    title: "Decision 6: the guardrails, REVIEW.md among them, cannot be switched off by the agent (kept: REVIEW.md stays the owner's, who changes it by merging)"
  - id: decision-16
    resource: docs/decisions/16.md
    title: "Decision 16: the weekly read-only claude -p scan (kept; its scheduled, read-only pattern is reused)"
  - id: decision-28
    resource: docs/decisions/28.md
    title: "Decision 28: the owner accepts a head's Important findings with the sdlc:accept-findings label, recorded by signature with its actor (postdates the study; it gives the waiver signal a structured home)"
  - id: decision-20
    resource: docs/decisions/20.md
    title: "Decisions 20 and 11: nothing pushes to the owner; park, never notify (kept)"
  - id: code
    resource: template/REVIEW.md
    title: "The nit cap, the framework rules and the 'Do not report' list; plugin/review/findings.py (signature, normalise, nits_omitted, update_seen); plugin/review/REVIEW_PROMPT.md (the rule field); plugin/gate/checks.py check_findings; plugin/panel/cli.py overturn and plugin/panel/ledger.py; plugin/ci/fix_requests.py; template/.github/workflows/sdlc-evals.yml and sdlc-scan.yml; plugin/hooks/protected_paths.py; read at main 5542406, plugin 1.0.1"
generated: { by: sdlc-framework-session/ccr-01de3f80-ilnomi, at: 2026-10-15T20:00:00Z }
---

# The reviewer is tuned twice a month from signals already on record, through a standing REVIEW.md PR

**Status: proposed (roadmap R38), from study entry T16, confirmed by the owner on 2026-10-09.** *[2026-10-20: accepted 2026-10-16 (PR #215); rank 45; the rank is read from ROADMAP's Order column]* Nothing is built. It amends no decision: decision 6 keeps `REVIEW.md` the owner's, who still makes every change by merging, and decision 16's scheduled read-only run is reused as a pattern. It is the second standing PR after R37 (T15, "CLAUDE.md: Things Claude gets wrong") and shares its mechanism; the brief it starts is T1's, R28.

## The problem

The review pass at gate (e) follows `REVIEW.md`, and nothing ever tells the owner whether that file still fits the project:

- **No tuning exists.** The build guide planned the article's monthly tuning as "a scheduled agent PR you merge or ignore" (`docs/BUILD_GUIDE.md:600`) and recorded sub-step 26.5 "not built" (`docs/ROADMAP.md:9`). Without it the only tuning signal is what the owner happens to notice at gate (e) (the crosswalk row deploy-tuning, "weigh").
- **The signals exist but nothing reads them.** Each change keeps its findings with a tally and the reviewer's count of omitted nits; the project keeps every finding's signature and count; the panel keeps what it settled and what the owner overturned. None of it reaches a decision about `REVIEW.md`.
- **The article's method is a chore for one owner.** The article's tech lead rates findings by hand once a month (p.34). The owner works alone and looks in once or twice a day; a recurring rating act is exactly what the study's weights (owner attention 3) count against.
- **A run cannot make the edit.** `REVIEW.md` is a guardrail file: the protected-paths hook denies a session's edit to it (`plugin/hooks/protected_paths.py:46`), and decision 6 keeps it so. A tuning job has to propose the edit for the owner to merge.

## What the article says

The tech lead writes the review policy as `REVIEW.md`, divided into passes, defining "what counts as Important as opposed to a Nit, and what to skip" (p.33, step 2). "Once a month the tech lead tunes the setup by rating findings so the reviewer improves and by capping Nit volume in REVIEW.md. Generated paths and anything CI already enforces are excluded" (p.34, step 6); the example `REVIEW.md` caps nits at five and lists what not to report (p.34). Under governance, "findings, fixes, ratings and approvals are logged in the PR history, so the PR is the audit record" (p.35)[^playbook].

The framework keeps the article's outcome, a reviewer tuned on a fixed rhythm with the nit cap and the exclusions as levers, and departs from it twice, both by the owner's choice: the ratings come from acts already on record instead of a rating act, and the rhythm is twice a month instead of monthly.

## What the framework does today

Read at `main` 5542406, plugin 1.0.1. The entry's "Today" was recorded at c8006f5 (plugin 0.3.5) and still held at the 2026-10-07 re-check at 619f01a, with no change under `plugin/` or `template/` between them. `git diff 619f01a 5542406 -- template/REVIEW.md plugin/review plugin/panel template/.github/workflows/sdlc-evals.yml template/.github/workflows/sdlc-scan.yml` touches only the second-occurrence wording of `template/REVIEW.md` and `plugin/review/REVIEW_PROMPT.md` (merge 2deaec7, PR #136). `git diff --stat 619f01a 5542406 -- plugin/gate/checks.py plugin/gate/artifacts.py plugin/evals/run.py` shows additions only (the lesson-and-eval check at gate (e), its lesson constants, git maintenance turned off in the eval fixture), none touching `check_findings`, `REVIEW_FINDINGS` or the runner's `claude -p` call; `plugin/ci/fix_requests.py` and `plugin/hooks/protected_paths.py` did not change. So every claim of the entry still holds; the lines below are 5542406's[^code].

- **`REVIEW.md`.** `template/REVIEW.md` ships the article's structure: the three passes, "What Important means here", the nit cap ("Report at most five nits per review; summarize the rest as a count", `:17-18`), the framework rules, each an Important finding (`:20-31`), and "Do not report": generated files, `changes/*/evidence/`, and anything CI already enforces (`:33-35`). It is in `ALWAYS_PROTECTED` (`plugin/hooks/protected_paths.py:46`).
- **What a review records.** One `evidence/review-findings.json` per change, rewritten for each reviewed head (`plugin/gate/artifacts.py:71` names it; its `head` is mandatory, `plugin/review/REVIEW_PROMPT.md:59-60`, and the gate rejects a stale one, `plugin/gate/checks.py:534-540`), each finding with `pass`, `severity`, `file`, `line`, `summary` and a `rule` naming the `REVIEW.md` rule, skill rule or spec requirement it violates (`plugin/review/REVIEW_PROMPT.md:66-74`). `normalise` fills each `signature` and recomputes the tally, keeping the reviewer's own `nits_omitted` (`plugin/review/findings.py:173-197`). The project-wide `changes/.review-seen.json` maps each signature to its count, first and last change (`findings.py:268-271`, `:274-288`); the reviewer is told not to read it (`REVIEW_PROMPT.md:14-23`).
- **The owner's and the panel's verdicts on findings.** At gate (e) `check_findings` lets through only the Important findings the review panel settled (`plugin/gate/checks.py:542-543`); its message still says "or have the owner waive it in a review comment" (`:548`), but nothing honours such a waiver: the comment reaches the next fix round as text in `evidence/fix-requests.json` (`plugin/ci/fix_requests.py:14-22`). A panel decision the owner overturns in a review comment is structured: `panel/cli.py overturn` writes `{"comment", "at"}` on the ledger entry (`plugin/panel/cli.py:384-397`, `plugin/panel/ledger.py:26`, `:348-350`). Decision 28's `sdlc:accept-findings` label, which records each accepted signature with its actor, is accepted (R6) and not built: `git grep -n "accept-findings\|accept_findings" 5542406 -- plugin template` returns nothing (verified by that command's empty output)[^decision-28].
- **Nothing tunes.** No workflow reads the findings across changes; no file proposes a `REVIEW.md` edit.
- **The pattern to reuse.** `sdlc-scan.yml` runs one read-only `claude -p` (Read, Grep, Glob and git, one Write of its findings file, `:11-12`, `:90`) on a weekly cron (`"23 6 * * 1"`, `:38`) with `contents: write` (`:41-42`); its commits and PRs start no workflow run (`:23-25`).
- **The eval run.** `sdlc-evals.yml` runs on pull requests that change `CLAUDE.md`, `.claude/**` or `evals/**` (`:29-34`) and nightly (`:36`); `REVIEW.md` is not among the paths. Its cases run tasks with `claude -p` (`plugin/evals/run.py:27-31`), never the review pass, so no case exercises `REVIEW.md` today. A pull request the workflow token opens or updates gets only a `pull_request` run waiting for a person's approval (`docs/notes/11.md` §11a, seen live in `docs/notes/23.md`).

## The proposal

Added; `REVIEW.md` stays the owner's, with its nit cap and its "Do not report" list (the owner's note).

1. **A tuning run twice a month.** A scheduled, read-only `claude -p` run, on the weekly scan's pattern (decision 16), reads the review findings of the period and the signals already on record, instead of ratings:
   - Important findings the owner waived or overturned in a review comment;
   - findings the review panel settled;
   - repeats (`changes/.review-seen.json`);
   - nit volume against the cap (the tally's `nit` and `nits_omitted`);
   - findings in paths CI already enforces, or in generated files.

   It writes a short tuning report, committed, saying what it saw and what it proposes, and a proposal file with the `REVIEW.md` edits it suggests. Twice a month instead of the article's monthly tuning: the owner's choice.
2. **One standing PR, as in T15 (R37).** A deterministic step (no model) takes the run's proposal file and opens, or updates, one pull request titled "REVIEW.md: tuning". The owner merges it whenever they choose; until then it waits like any PR.
3. **The step starts the checks itself.** Because a PR the automation opens starts no workflow run by itself (its `pull_request` runs wait for approval; decisions 5 and 22, `docs/notes/11.md` §11a), the step starts the eval run and build-config's brief (T1, R28) itself after each update; which workflow and which ref it dispatches is R37's open item (T15), and the brief's dispatch waits for the `workflow_dispatch` input R28 recommends on its brief workflow (`roles-and-manager.md:164`, R28's own recommendation, not yet settled), the eval run alone being dispatched until then. When R22 (T18) is built, the same step posts the passing `sdlc/review` check on the PR, as T18's entry assigns to "T15 and T16's step" (`target-design.md` T18, "Two rulesets")[^t18].
4. **No rating chore, no notification.** The owner's existing acts (a waiver, a "Request changes" review or comment that overturns a finding) are the ratings; the owner rates nothing. Nothing notifies the owner (decisions 11 and 20).

## How it is judged

On this repository or the sample, after two periods: a tuning report is committed for each period, naming the findings it read and the count behind each signal; the standing PR exists whenever there is an edit to propose, each edit traced to the signals behind it; the eval run and the brief ran on the PR's head without the owner's click; the owner's inbox got nothing; and the owner performed no act the framework did not already ask for. Over the following periods, the measure is the trend the tuning is for: nits per review (`nit` plus `nits_omitted`) against the cap, and the share of Important findings that ended waived, overturned or panel-settled, both read from the reports, falling after a merged tuning PR.

## What to settle before building

| Question | Recommended |
|---|---|
| Where a waiver or an overturn is read from (the entry's open item) | Decision 28 (accepted 2026-10-13, after the study) settles the label, `sdlc:accept-findings`, honoured at gate (e) only, and its record: each accepted signature written to `status.yaml` with the label's actor and the time; it says nothing about a tuning run. Recommended: once R6 is built, the run reads the accepted signatures from `status.yaml`; panel-settled findings and overturns from the ledger (`decisions-<phase>.json`, its `overturned` field); a waiver or overturn written only in a review comment from `evidence/fix-requests.json`, read as data, never as instructions. Only a comment that a later fix round collected reaches that file; a comment waiver on a PR where no round followed is not in it (my recommendation) |
| What the eval run on the `REVIEW.md` PR can show (`REVIEW.md` is not among `sdlc-evals.yml`'s paths, and no case runs the review pass) | The step's explicit dispatch makes the paths irrelevant for this PR. The brief says plainly that the suite has no review-pass case, as build-config's brief says "no cases yet" for an empty suite. A review-pass case (the period's diffs re-reviewed with the proposed `REVIEW.md`) is a later addition, judged with R35 (T13) (my recommendation) |
| What the run may propose: wording and the nit cap only, or also the "Do not report" list and the passes | Wording, the nit cap, "What Important means here", the "Do not report" list and the passes' descriptions; never the "Framework rules" section (`template/REVIEW.md:20-31`), which the build guide owns (`template/REVIEW.md:3-4`) and parts of which deterministic code backs (`findings.py` `framework_findings` for the test-file rule, `update_seen` for repeats, the protected-paths hook for the guardrail rule) (my recommendation) |
| Whether the run and T15's step share one workflow, and the two schedule days | Two workflows sharing one standing-PR module: T16's is a scheduled model run, T15's a deterministic step after each (e) merge or on the digest's schedule (T15's own open item). T16 on the 1st and the 15th of the month at an off-the-hour minute, UTC like the other crons (my recommendation) |
| How the standing PR is kept up to date when the owner edits it, closes it, or a period proposes nothing | R37's rule cannot be reused as it stands: it keys a line and its rejection by the finding's signature (R37's matching row), and a tuning edit is a change to `REVIEW.md`'s wording, the nit cap or the "Do not report" list, which carries no signature. Shared with R37: the module, and its way of keeping the PR current: the step only adds commits on top of the branch, so the owner's edits stay, and it reads a closed PR back at the next update, not on the close. R38's own identity: each edit is keyed by the `REVIEW.md` section it changes and a hash of its proposed text, kept in the PR description's table (section, hash, the period's report, the signals behind it); an edit already in the open PR or already merged is not added again; an edit the owner changed on the branch is merged as edited. R38's own rejection: an edit the owner deleted, or every edit of a PR closed without a merge, is rejected by its key, read back from the closed tuning PRs; the step drops an exact repeat, and the run is given the rejected edits with their periods, so it does not propose one again reworded and its report says when a signal behind a rejected edit persists. A period with nothing to propose still commits its report and leaves the PR as it is (my recommendation) |
| Where the report is committed | On a ref of its own that every period appends to, so a closed PR loses no report; the standing PR links the period's report (my recommendation) |
| Which findings make up "the period" | Every review of every change whose review ran in the period, read from the history of `evidence/review-findings.json` (rewritten per head), not only the last head; that git history reaches the run's checkout is to verify (my recommendation) |
| Merging the standing PR fires the workflows that run on any merged PR into the default branch | Each run skips a PR with no change folder; shared with R37, to verify |
| The run's spend | Counted in T30's weekly window and budget (R25) like any model run (my recommendation) |
| A line in the digest | Not in the entry: the owner's note says only that nothing notifies them. If wanted, a "Worth knowing" line beside T15's in R20's outline, the owner's call (my recommendation, not part of this proposal) |
| The workflow's, the PR's and the ref's names | Placeholders, judged with T4 (R45) |

## Considered and not chosen

- Rating each finding by hand, as the article's tech lead does: a recurring chore for one owner (the owner's note).
- Monthly, as the article says: the owner chose twice a month.

## Decisions it touches

None amended, so no decision file is written and no number is reserved. 6 is kept: `REVIEW.md` stays the owner's, changed only by the owner's merge; whether a pull request the automation opens on a guardrail file fits decision 6's wording is T15's item to confirm (R37), and the answer there holds here. 16 is kept, its scheduled read-only pattern reused. 11 and 20 are kept: nothing notifies the owner. 28 is kept and read: its label is the structured waiver this run counts. 12 is kept: the review pass itself is unchanged.

## Order

In the confirmed order's fifth group, "the rest in any order" (the record, section 8 part 2); the Order column of the ROADMAP row is the owner's. Only the standing-PR part depends on R37 (T15), whose mechanism is built once, for both. It changes `template/` and `plugin/`, so it ships as a plugin version with tests and reaches a project through `/sdlc-init`'s workflow copies. The parts it takes:

| Part | Where | When |
|---|---|---|
| The tuning run: prompt, the one Write of its report and proposal, the read of the signals on record | a new `plugin/` module beside `plugin/scan/`, a new template workflow on a twice-monthly cron | Now; the waiver signal from review comments only, until R6 |
| The standing PR "REVIEW.md: tuning", opened and updated by the deterministic step, with its own edit key and rejection rule | R37's standing-PR module | With R37 |
| The explicit dispatch of the eval run (which workflow and which ref: R37's open item) | the step | With R37's dispatch wiring |
| The brief on the PR | T1's role brief | With R28 |
| The `sdlc/review` check posted by the step | the step | With R22 (T18) |
| The accepted-findings signal | `status.yaml` | With R6 (decision 28) |
| A review-pass eval case | `evals/` | With R35 (T13), if chosen |
| The names | the workflow, the PR, the ref | With R45 (T4), last *[2026-10-20: R45 is rank 20, before R38 (45): the names come from R45's decision PR before this is built; the rank is read from ROADMAP's Order column]* |

[^playbook]: `docs/reference/ai-native-sdlc-playbook.pdf` p.33 (step 2), p.34 (step 6 and the example `REVIEW.md`), p.35 (governance).
[^code]: `template/REVIEW.md`; `plugin/review/findings.py`; `plugin/review/REVIEW_PROMPT.md`; `plugin/gate/checks.py` `check_findings`; `plugin/gate/artifacts.py`; `plugin/panel/cli.py` `cmd_overturn`; `plugin/panel/ledger.py`; `plugin/ci/fix_requests.py`; `plugin/hooks/protected_paths.py`; `plugin/evals/run.py`; `template/.github/workflows/sdlc-evals.yml`, `sdlc-scan.yml`; the crosswalk row deploy-tuning and `target-design.md` T16 ("Today").
[^decision-28]: `docs/decisions/28.md`; `docs/ROADMAP.md` row R6 (`docs/proposals/accept-verb.md`).
[^t18]: `docs/reviews/2026-09-28-playbook-vs-framework/target-design.md`, T18, "Direction discussed", "Two rulesets".
