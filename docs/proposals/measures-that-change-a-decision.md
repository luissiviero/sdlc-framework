---
type: Proposal
title: Measures that change a decision — true definitions, first-pass split by the plan's class, repeats per CLAUDE.md line, and DORA
description: The counters line and the digest's Counters table stay, computed with no model and no schedule; their definitions are made true and written under the table, the first-pass share and fix iterations are split by the plan's class, each CLAUDE.md line says in how many changes its mistake was found, and on a declared production one DORA row with counts is added in a change of its own, with no new counter for anything another entry already shows.
status: proposed
roadmap: R26
sources:
  - id: study-entry
    resource: docs/reviews/2026-09-28-playbook-vs-framework/target-design.md
    title: "T31, confirmed at the close of the study on 2026-10-09; from the crosswalk row x-measure (better: the framework; decision: blend, option B with DORA added), 2026-10-08; the owner's word of 2026-10-09 on the reset's mark"
  - id: record
    resource: docs/reviews/2026-09-28-playbook-vs-framework.md
    title: "Section 7, first bullet (the close: all 32 entries confirmed as recommended, 'T31's DORA in its own change'); section 8, parts 1 and 2 (part 1, the close table row T31: row x-measure, amends none, 'yes; DORA in its own change'; part 2, the confirmed order: the gate changes T18, T23, T9, T30, T31)"
  - id: crosswalk
    resource: docs/reviews/2026-09-28-playbook-vs-framework/crosswalk.json
    title: "Row x-measure (whole); the decision fields of build-plan-approve and build-start (T1: the class split, the Full label), deploy-claudemd (T15), deploy-release (T21), maintain-detect (T22), maintain-act (T24), x-queue (T28) and x-limits (T30)"
  - id: artcraft
    resource: docs/reviews/2026-10-13-artcraft-vs-framework/planning-revision.md
    title: "Rows 6.3 (a reset erases status.yaml iterations), 6.4 (all three plans of this repository's changes 0001 to 0003 non-routine; T31's class split) and 6.7 (the wait left to T28); the record docs/reviews/2026-10-13-artcraft-vs-framework.md, row 18 (measuring the process, mapped to T31) and row A2 (folded into T27, T28, T30 and R10, not T31)"
  - id: playbook
    resource: docs/reference/ai-native-sdlc-playbook.pdf
    title: "p.7: every play ends with how you measure whether it worked; p.11-48: a leading and a lagging indicator per play; p.17: first-pass share and rework cycles from the PR metadata; p.29: first-pass CI success and change failure rate; p.41: DORA measures as the CI/CD lagging indicator; p.45: repeat incidents of the same class"
  - id: decision-20
    resource: docs/decisions/20.md
    title: "Decision 20: a review queue and a daily digest, pull not push (kept: it sets the channel the counters stay in, not what is measured)"
  - id: decision-29
    resource: docs/decisions/29.md
    title: "Decision 29: one iteration counter with T30's one reset at the cap, the reset marked as the label's is (read, not amended: the mark this proposal reads)"
  - id: decision-2
    resource: docs/decisions/2.md
    title: "Decision 2: where plan.md is approved (read, not reopened: T1 names the class-split figure as its only reason to reconsider option C)"
  - id: code
    resource: plugin/pr/counters.py
    title: "collect and render; with plugin/pr/description.py _counters_line, plugin/pr/digest.py main, plugin/state/status.py apply-label branch and fields, plugin/gate/cli.py cmd_set_iterations, plugin/gate/limits.py classification_for, plugin/agents/adversarial-reviewer.md, plugin/review/findings.py update_seen, plugin/detect/dismissals.py lookup, plugin/release/cli.py, plugin/detect/runbooks.py Outcome and write_record, template/.github/workflows/sdlc-digest.yml and sdlc-release.yml, docs/BUILD_GUIDE.md step 42; read at main 5542406, plugin 1.0.1"
generated: { by: sdlc-framework-session/ccr-01de3f80-ilnomi, at: 2026-10-15T20:00:00Z }
---

# Measures that change a decision: true definitions, first-pass split by the plan's class, repeats per CLAUDE.md line, and DORA

**Status: proposed (roadmap R26), from study entry T31, confirmed by the owner on 2026-10-09, option B of the crosswalk row x-measure, with DORA added (the letters are the row's own).** Nothing is built. It amends no decision: decision 20 is kept, and build guide step 42's "scheduled report later" is dropped, a plan and not a decision. It is the last of the gate changes in the confirmed order; its note settles R20's (T28's) waited-time item, and DORA is built in a change of its own after the study.

## The problem

The counters exist, but three of them say something other than what their names promise, and none of them answers the questions the owner has to decide:

- **A reset change reads as first-pass.** First-pass is an iteration count of 0 (`plugin/pr/counters.py:60`), and the owner's `sdlc:reset-iterations` label sets the count back to 0 (`plugin/state/status.py:236-240`), so a change reset at the cap and merged with no later round counts as a first-pass merge. A reset also erases rounds: this repository's three shipped changes (0001 to 0003) were each reset by the label, and their `status.yaml` reads 1, 2 and 2 iterations against 4, 12 and 6 fix sessions (ArtCraft `planning-revision.md` 6.3)[^artcraft], so the fix iterations per shipped change are undercounted.
- **"First-pass merge: yes" on an open pull request** only means no fix round so far (`plugin/pr/description.py:529-531`).
- **"Dismissals in force" counts expired dismissals** (`counters.py:59`, `:75`), while the dismissal store itself treats an expired one as not in force (`plugin/detect/dismissals.py:109-123`).
- **The plan's class is read by no counter.** The adversarial reviewer classes each plan routine or non-routine (`plugin/agents/adversarial-reviewer.md:63-68`); only the iteration cap uses it (`plugin/gate/limits.py:69-95`, the panel CLI), and the preflight shows it. T1 waits on exactly this figure before reopening decision 2's option C, and it is the figure that tells the owner when a non-routine plan needs the Full label.
- **A repeated mistake is counted per signature**, so a reworded repeat is missed: the sample's outdated Layout finding has four signatures across changes 0001 and 0002, none counted as a repeat across changes (the entry's "Today").
- **Nothing computes DORA**, although records exist for most of it, and build guide step 42 still promises "a scheduled agent report later".

## What the article says

Every play ends with "How you measure whether it worked" (p.7): a leading and a lagging indicator read from records that already exist (p.11-48). For plan mode, the "share of changes that merge from the first implementation pass" and "rework cycles per change, again from the PR metadata" (p.17). For the feedback loop, "first-pass CI success rate" and "the change failure rate from an incident tracker" (p.29). For CI/CD, the lagging indicator is "DevOps Research and Assessment (DORA) measures, which the CI system and deployment tooling already emit" (p.41). For closing the loop, "repeat incidents of the same class" (p.45)[^playbook]. The article names indicators; it does not say which of them should change an owner's decision. This proposal keeps the ones that do.

## What the framework does today

Read at `main` 5542406, plugin 1.0.1. The entry's "Today" was read at 619f01a (plugin 0.3.5); `git diff --stat 619f01a 5542406` over the files below shows only `plugin/pr/description.py` moved, in the first-sentence helper (`_first_sentence`, lines 154-176), so every claim below holds at 5542406 as cited[^code].

- **The pull request line.** Each phase pull request the framework opens carries "Counters: first-pass merge: yes|no · fix iterations: N", plus panel calls when there are any, from the branch's `status.yaml` (`description.py:529-535`).
- **The digest's table.** `counters.py` `collect` and `render` (`:35-133`): changes, shipped (phase (e) on the default branch, `:32`, `:55`), the first-pass merge share with its "n of m", fix iterations per shipped change, panel calls, incidents merged and shipped, dismissals in force by kind, and a note on what is not counted (`:121-126`). No model, no schedule of its own; the digest renders it (decision 20).
- **First-pass.** An iteration count of 0 (`:60`). Every fix round raises it through the session's own bump-iteration call (`plugin/gate/cli.py:191`), the owner's change requests on the intent and design pull requests included (the entry). The label stamps `iterations_reset_by` and `iterations_reset_at` (`status.py:72`, `:77`, `:236-240`); the by-hand `gate/cli.py set-iterations` sets the count only, with no mark (`plugin/gate/cli.py:159-169`); the manager's one reset does not exist yet (decision 29, R10).
- **The plan's class** is written in the adversarial verdict and read by no counter: only the iteration cap uses it, through `limits.py` `classification_for` (`:87-95`; `plugin/panel/cli.py:205`), and the preflight shows it as information (`plugin/gate/preflight.py:321-333`).
- **Repeats.** `changes/.review-seen.json` maps each finding signature to a count, its first and its last change (`plugin/review/findings.py:274-311`): runs are counted, not changes, and the changes in between are not kept.
- **A digest that cannot list the pull requests** prints its reason and exits 0, publishing nothing (`plugin/pr/digest.py:239-242`); R20, accepted, changes this to exit 1.
- **DORA's records.** The release record (`released_at`, `released_sha`, `released_pr`, `status.py:96-98`) is written on `sdlc/<id>/c` and `refs/sdlc/released/<id>`, never on the default branch the counters read (`plugin/release/cli.py:48-56`); the change's start is `status.yaml` `created_at` (`status.py:99`); the incident's breach start is in `detection.json` (`plugin/detect/finding.py:70`). The release workflow releases only the change's build pull request, head `sdlc/<id>/c` (`release/cli.py:19-23`), so a runbook's revert pull request has only its merge. No record links an incident to a release. Whether the digest's checkout (`fetch-depth: 0`, `template/.github/workflows/sdlc-digest.yml`) sees `refs/sdlc/released/*`: not verified.
- **Build guide step 42** (`docs/BUILD_GUIDE.md:946`) reads "two counters in every PR description now; a scheduled agent report later"; the report is not built.

## The proposal

The pull request's counters line, the digest's Counters table and their computation with no model and no schedule stay (the owner's note, which cites decision 20 for the digest, the channel they stay in). Added, in the owner's order:

1. **True definitions, written under the table.** A change whose count was reset at the cap, by the manager's one reset (T30, R25; decision 29), by the owner's label or by hand, never counts as first-pass, and the note names it. Today only the label stamps `iterations_reset_at`, so the manager's reset and the by-hand command must leave the same mark (the owner's word of 2026-10-09). A pull request not yet merged says "no fix round so far" instead of "first-pass merge: yes". Only unexpired dismissals count as in force.
2. **First-pass split by the plan's class.** The first-pass share and the fix iterations per shipped change, each for routine and non-routine plans, each with its "n of m": the figure T1 (R28) waits on before reopening decision 2's option C, and the one that tells the owner when a non-routine plan needs the Full label at the design merge. (R11, T32's proposal, accepted on 2026-10-13, has these rounds by class read its fix-round lines; see the settle table.)
3. **Repeated mistakes per CLAUDE.md line.** Each line of T15's standing CLAUDE.md pull request (R37), and its digest line, says in how many changes the mistake was found (with T15's "repeat of" tag for reworded repeats, as the entry's direction has it); a finding that recurs after its line merged is marked on the build pull request.
4. **DORA, one row of the digest's table**, on projects with a declared production only (`sdlc.yaml: deploy.production`), with counts and not only rates: deployment frequency from the release record; lead time from the change's first commit to its release; change failure rate from releases followed by an incident or a rollback in the window; time to restore from the incident's breach start to its fix released or the rollback. For example: "DORA (30 days): 6 releases · lead time 1.8 days · failure 1 of 6 · restore 4 h". Computed with no model, and built in its own change after the study.
5. **No new counter for the rest.** Spend stays with T30 (R25); the wait on each item with T28 (R20), read from the gate record's time, or from the pull request's creation at gate (a), which settles R20's waited-time item; failed runs with T19 (R18); the detection, the fix and the scan with T22, T25 and T26 (R40, R42, R43).
6. **What is not computed, recorded with its reason** (time to first review, first-pass CI success, the survival rate of intents, the OpenTelemetry and team-only measures), and build guide step 42's scheduled report dropped, the digest being the report.

The crosswalk row is completed with what each surface shows, first-pass as the code defines it today (the owner's change requests on the intent and the design count against it, a reset reads as first-pass), what a counter does when its data is missing, where the other figures are, and what is not measured.

## How it is judged

On the sample, once built: a change reset by any of the three routes shows "first-pass: no" in the table, and the note under it names the reset; an open pull request's line reads "no fix round so far"; an expired detection dismissal leaves the "in force" count; the table shows the first-pass share and the fix iterations for routine and non-routine plans, each with its "n of m" (every plan so far, this repository's and the sample's, is non-routine: ArtCraft 6.4 for this repository, the sample's `adversarial-review-*.json` of 0001 and 0002); a CLAUDE.md line in the standing pull request says "found in N changes". With DORA's change, on a project with `deploy.production: true` the digest carries the DORA row with its counts, and a project without a declared production carries none. The sample declares production but releases nothing (`deploy.action: none`, `deploy.command: ""` at its local checkout f88b262; `plugin/release/cli.py:44-47`, `:638-642` write a release record only after a command that exited 0), so on the sample the check shows only the zero or too-few case; the counts are checked by unit tests over recorded release and incident fixtures. The measure of the proposal itself: the owner can answer "do non-routine plans need the Full label" and "is a separate plan gate warranted" from the digest alone.

## What to settle before building

| Question | Recommended |
|---|---|
| The mark of a reset | **Settled in part by decision 29** (first settle row): the manager's reset is marked as the label's is, `iterations_reset_by` naming the run and `iterations_reset_at`. Which candidate builds it is R25's recommendation, not settled: R10, or R25 if built first (`weekly-window-guarded.md`, settle table); this proposal reads the mark either way. *Mine:* `gate/cli.py set-iterations` stamps `iterations_reset_at` whenever it lowers the count and sets `iterations_reset_by` to null, so the `owner_actions` check reads the commit author as it does for a by-hand act (`status.py:65-70`). Stamping `iterations_reset_at` alone would not do: the check counts a changed stamp as a recorded label act and credits the drop to whatever `iterations_reset_by` already holds (`plugin/gate/checks.py:1158-1167`, `:1197-1201`), so an automation-identity commit would pass under the earlier label actor's name; that a null actor then parks such a commit: to verify with a test. The counter then reads `iterations_reset_at` for all three routes |
| Where the fix iterations per shipped change come from, since a reset zeroes the count (`status.py:237`) | *Mine:* R11's fix-round lines once R11 is built (T32: "T31's rounds by class read the same lines"); until then `status.yaml` `iterations`, with the reset changes named under the table |
| A class with no shipped change | *Mine:* the row reads "0 of 0, no routine plan shipped yet" rather than a rate; today the routine row would be empty (ArtCraft 6.4 for this repository; the sample's `adversarial-review-*.json` of 0001 and 0002) |
| How DORA links an incident to a release | *Mine:* the release in the breach window, read from the release record as T24's note reads it (maintain-act, point 2; R41), so the counter and the rollback rule agree on one reading; the incident's diagnosis is a model's text, and the counters use no model |
| What the DORA row says with fewer than a handful of releases | The counts are always shown (the owner's note). *Mine:* rates and the two durations only from five releases in the window, below that "N releases, too few for a rate"; the minimum is the design's to set |
| Where lead time starts | **The owner's note** (point 4): "from the change's first commit"; the entry keeps open whether that is read from `status.yaml` `created_at` or from the intent's merge. *Mine:* `created_at` (`status.py:99`), on every copy whatever the merge method (the entry), not the intent's merge; whether `created_at` matches the first commit's time on the sample: to verify |
| What records a rollback's release, since the release workflow skips a revert pull request (`release/cli.py:19-23`) | *Mine,* owned by this proposal's DORA change, one record per kind of rollback. A project rollback runbook (a `command` under `maintain.runbooks`, no pull request) already leaves `evidence/runbook-<name>.json` with its `at` and exit code (`plugin/detect/runbooks.py:93`, `:828-839`), read as the rollback's time. A `revert-pr` runbook's pull request is merged by the owner and released by nothing: its merge time, its pull request and the reverted commit are written by a deterministic step on that merge (the release workflow already fires on every closed pull request into the default branch, `sdlc-release.yml`, and skips this one); the runbook workflow fires on the Go label, not on a merge. Where that record lives, since the default branch takes only the owner's merges, is the design's to set, as the release record's ref is. R41 (T24) adds no such record and is not a dependency: it shares only the reading of a release in the breach window (`acting-at-3-sigma.md`, Order) |
| How the digest reads the release record, which is not on the default branch | *Mine:* an explicit read-only fetch of `refs/sdlc/released/*` in the digest's checkout; whether `fetch-depth: 0` already brings them: not verified |
| Whether the digest keeps a history of the counters | *Mine, as R20 recommends for the issue:* no stored history; the DORA row is a window by construction, the other rows all-time; GitHub's edit history of the issue body is there (whether its API serves it: to verify, R20) |
| The build of DORA "in its own change after the study, with the counters' fixes" | **Settled by the owner:** DORA in its own change (the close; the note, point 4). *Mine:* parts 1, 2, 5 and 6 first, in one change, since they correct what the owner reads today; DORA after |
| The reasons recorded for what is not computed | *Mine:* time to first review: the owner is the only reviewer, and R20's wait covers it; first-pass CI success: in CI the runner runs the targets after the session and a red target is a counted round (decision 29); the survival rate of intents: an intent closed unmerged never reaches the default branch the counters read (`counters.py:121-126`); OpenTelemetry: not needed for one owner (R11, point 5); team-only measures: step 42 already skips them |

## Considered and not chosen

- A, the x-measure text corrected only.
- C, B plus a repeat-incident counter (p.45; T25's option C, R42): with one metric per project incidents are few, and T25's since-the-fix line already says whether a fix held.
- A scheduled report (build guide step 42's "later"): the digest already is the report (the owner's note, point 6); decision 20's channel is kept.

## Decisions it touches

20 is kept: the counters stay in the digest, with no schedule of their own and nothing pushed. 29 is read, not amended: the reset's mark it settles is the one part 1 counts. 2 is read, not reopened: option C stays rejected, and this proposal computes the figure T1 (R28) names as the only reason to reconsider it. Build guide step 42's "scheduled agent report later" is dropped, a plan and not a decision. No decision is amended, so no decision file is written and no number is reserved[^decision-20][^decision-29].

## Order

Twelfth of the study's proposals in the confirmed order, and the last of the gate changes (the record, section 8: T32, T12, T21; T17, T19, T27, T28; T18, T23, T9, T30, T31). It changes `plugin/` (the counters, the PR line, the findings record, the gate CLI and its `owner_actions` check) and, for DORA, the digest workflow in `template/`, so it ships as a plugin version with tests and reaches a project through `/sdlc-init`. The parts:

| Part | Where | When |
|---|---|---|
| 1. True definitions: reset never first-pass, "no fix round so far", dismissals in force, the note under the table; the by-hand mark | `plugin/pr/counters.py`, `plugin/pr/description.py`, `plugin/gate/cli.py`, `plugin/gate/checks.py` (`owner_actions`, its tests at least) | Now for the label and by-hand resets; the manager's reset counts once decision 29's mark is built (the reset itself is T30's, R25; by R10, or by R25 if built first, as R25 recommends) |
| 2. The class split with its "n of m" | `counters.py`, reading the class as `limits.py:87-95` does | Now; the rounds move to R11's fix-round lines when R11 is built |
| 3. "Found in N changes" per CLAUDE.md line, the mark on a build PR after a line merged | `plugin/review/findings.py` record (the list of changes per signature), R37's standing PR | With R37 (T15); the list of changes in this change or R37's, whichever is built first |
| 4. The DORA row | `counters.py`, `template/.github/workflows/sdlc-digest.yml` (the release refs) | Its own change, after parts 1 and 2; reads R13's (T21's) release record; the incident link reads a release in the breach window as R41 (T24) does, and the rollback record is this change's own (settle table); neither waits on R41 |
| 5 and 6. No new counter; what is not computed; step 42's report dropped | the note under the table; `docs/BUILD_GUIDE.md` step 42 | Now, with part 1 |
| The table's place in the digest, and the "found in N changes" line | R20, rows 14 and 8 | With R20 |

T1 (R28) is a reader of part 2's figure, not a dependency. T4's names (R45) come last.

[^playbook]: `docs/reference/ai-native-sdlc-playbook.pdf` p.7, p.11-48, p.17, p.29, p.41, p.45.
[^decision-20]: `docs/decisions/20.md`.
[^decision-29]: `docs/decisions/29.md`, the first settle row (one counter, with T30's one reset at the cap, marked as the label's is).
[^artcraft]: `docs/reviews/2026-10-13-artcraft-vs-framework/planning-revision.md`, rows 6.3, 6.4 and 6.7; the record `docs/reviews/2026-10-13-artcraft-vs-framework.md`, rows 18 and A2.
[^code]: `plugin/pr/counters.py`; `plugin/pr/description.py` `_counters_line`; `plugin/pr/digest.py` `main`; `plugin/state/status.py`; `plugin/gate/cli.py` `cmd_set_iterations`; `plugin/gate/limits.py` `classification_for`; `plugin/agents/adversarial-reviewer.md`; `plugin/review/findings.py` `update_seen`; `plugin/detect/dismissals.py` `lookup`; `plugin/release/cli.py`; `plugin/detect/runbooks.py` `Outcome`, `write_record`; `template/.github/workflows/sdlc-digest.yml`, `sdlc-release.yml`; `docs/BUILD_GUIDE.md` step 42; the crosswalk row x-measure and `target-design.md` T31 ("Today").
