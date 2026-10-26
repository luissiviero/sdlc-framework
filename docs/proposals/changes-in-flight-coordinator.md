---
type: Proposal
title: Changes in flight, ordered and warned, and a project coordinator that is stateless beyond the repository
description: Two deterministic pieces in the pipeline (a dependency line between changes read at the (e) offer, and a file-overlap warning at design time) and, on top of them, an optional text-only coordinator session for a project that starts every time from status.yaml, changes/index.md and the digest alone.
status: accepted
roadmap: R66
sources:
  - id: owner
    resource: "the owner's messages of 2026-10-23, session ccr-9171b99a-q6u17y ('Ok. After the trial.'; 'I want this change' on the stateless rule)"
    title: "The request: after the trial, and the coordinator stateless beyond the repository"
  - id: inventory
    resource: docs/reviews/2026-10-23-parallelism-inventory.md
    title: "The parallelism inventory: sections 2 (gaps) and 3 (options B and D)"
  - id: concurrent-changes
    resource: docs/proposals/concurrent-changes.md
    title: "R51: concurrent changes, safe by construction (gaps G1 to G4)"
  - id: state-index
    resource: docs/proposals/state-index.md
    title: "R9: the state of the work in the repository (part 1, changes/index.md)"
  - id: central-session
    resource: docs/handoffs/central-session.md (on branch ccr-b2d02bf7-9ywgjn, PR #352)
    title: "The central session: this repository's practice (choice 262)"
  - id: article
    resource: docs/reference/ (PDF p.25)
    title: "Parallel work splits by files that do not overlap; the ceiling is how many streams one person can review"
generated: { by: sdlc-framework-session/ccr-9171b99a-q6u17y, at: 2026-10-23T12:00:00Z }
---

# Changes in flight, ordered and warned, and a project coordinator that is stateless beyond the repository
**Names since R45** (decision 39; the renames built in plugin 1.0.43 to 1.0.47; added on 2026-10-26, the text below keeps the old names, choice 126): `(b)` -> design; `(e)` -> deploy; `/sdlc-plan` -> `/sdlc-intent`; `escalate` -> `park`. \
**Status: accepted on 2026-10-23 (the owner, choice 264; ROADMAP R66), built after the real-project trial.** Nothing is built. The study behind it is `docs/reviews/2026-10-23-parallelism-inventory.md`; this file carries only what is to be built and the one design rule the owner fixed.

## The problem

Since R51 (plugin 1.0.26) several changes run through the pipeline at once safely: ids are reserved, a build PR is brought up to date and re-checked before gate (e), one release runs at a time. What the pipeline does not give (the inventory, section 2):
- a change cannot say that it comes after another, so two changes that touch the same code are reviewed in the order they happen to arrive, and the second learns of the first only when it parks at (e);
- nothing compares two changes' "Files that change" lists, so the owner discovers an overlap at a park, never before;
- an answer the owner gives on one PR reaches no other change;
- the owner has no one place that says, across changes, what waits on what. R9 part 1 and R20 give the view; nothing gives the order.

This repository runs a central session for the same jobs by hand (choice 262). Its first day showed what a coordinator costs when its state lives in a chat: two number clashes, two false claims and a context that grew long in two waves (`central-session.md`, "Why these rules").

## The proposal

**Part 1, the dependency line (plugin and template).** The intent gains an optional `after:` line naming one or more change ids; `/sdlc-plan` and the quick intent (R54) write it into `status.yaml`. At the (e) offer, one deterministic check holds the PR while a named change is not merged, with the reason on the PR. A park it is not: the PR waits, and the owner is not asked for anything. The merge order among dependent changes follows from it, for the owner, for the merge App (decision 36) and for merge by silence (R52) alike.

**Part 2, the overlap warning (plugin).** At the end of the design run, a deterministic check reads the new plan's "Files that change" and the same list of every open build branch (`sdlc/*/c`, found with `ls-remote` and read with `git show`, as `remote_change_ids` reads the ids). An overlap prints one line on the design PR and in the digest's "Worth knowing": the other change, the files, and whether an `after:` line exists. A warning, never a park (decision 11 unchanged). For this repository, the same check over the paths that two proposals name is a `tasks.py` task, so that the central session's pairing is a read instead of a judgment.

**Part 3, the project coordinator (template page, no plugin code).** Optional, text-only, started by the owner with a start prompt kept in the template, as `central-session.md` is kept here:
- **Stateless beyond the repository.** It starts every time from `changes/*/status.yaml`, `changes/index.md` (R9 part 1) and the digest, plus the open PRs read from GitHub. It keeps no plan file of its own and no end file: a second coordinator session starts from the repository alone. This is the rule the owner fixed on 2026-10-23 ("I want this change").
- **It reads and reports.** One table for the owner: each change, its phase, what it waits on, the overlap warnings, the `after:` lines, and the manager's recommendation where R28 wrote one (`evidence/manager.md`). It never re-judges a change.
- **It relays by writing on the receiving PR.** The owner's answer that concerns another change is written as a comment on that change's PR, quoted and linked, so that the repository stays the record ("the repo is the source of truth for every artifact", `docs/OPERATING_MODEL.md:119`). *[2026-10-23, the owner (choice 266): a relayed comment never starts with `@claude` and quotes the owner's words with `>`. A cloud session's GitHub tools act as the owner's login (`docs/notes/14.md:90`), and a comment by the owner's login that starts with `@claude` starts a fix round (`template/.github/workflows/sdlc-comment.yml`, decision 34), so an unguarded relay would start one in the owner's name. The build adds a test that the start prompt states the rule.]*
- **It never acts.** No label, no merge, no intent opened, no push to a change's branch: R28's rule 8 holds for it as for the manager (`roles-and-manager.md:140`). Decisions 17, 24 and 36 are untouched.

**What the coordinator reads from the manager, and never the reverse.** The manager (R28) is inside one change at one gate and writes `evidence/manager.md`; the coordinator is across changes and reads every `manager.md`. The `after:` line and the plan's file list come out of the `/sdlc-plan` interview the manager leads, so the coordinator's checks are reads of files the manager helped write. Built in that order: the manager first, judged against the trial as its row says; the coordinator after.

## How it is judged

- Part 1: a change with `after: 0012` is not offered at (e) while 0012's PR is open, and is offered on the next run after 0012 merges; a change without the line behaves as today.
- Part 2: two plans naming one file produce one warning line on the second design PR and in the digest; two plans naming none produce nothing; a parked base update at (e) on an overlap that was warned at (b) is the measure of whether the warning is read.
- Part 3: a second coordinator session, started from the start prompt on a repository where the first one ran, produces the same table with no file the first one wrote. If it cannot, the design is wrong, not the session.
- Against the owner's weights (`docs/reviews/2026-09-28-playbook-vs-framework.md:111`): owner attention down (one table, no overlap found at a park), autonomy up by the same, auditability up (every relay on a PR), fidelity kept (p.25's split by files, applied across changes), safety unchanged (nothing merges or acts that did not before).

## What to settle before building

1. Whether `after:` may name a change of another repository (the sample and the framework): proposed no, one repository.
2. Whether the overlap check reads plan.md on the remote branches (a read per open change at every design run) or a committed list in `changes/index.md` once R9 part 1 exists: proposed the index when it exists, the branches until then.
3. Whether the coordinator's table is also written to the digest ("Worth knowing") by the coordinator itself: proposed no, the digest is the workflow's; the coordinator writes only on PRs.
4. The decision text for 31: the review request stays the only notification the pipeline sends; the coordinator's report is a page the owner opens, not a notification, so 31 may need only a dated note. To be read against 31's rejected option ("a notification channel of the framework's own") when the decision is written.
5. *[2026-10-23, the owner (choice 266)]* **The conflict that comes anyway.** A conflict at the base update before gate (e) parks today (`docs/OPERATING_MODEL.md:88`, R51, choice 234), after the build and test spend. Proposed: one automatic fix round resolves it; the targets re-run and the adversarial reviewer judges it; it parks only if the round fails, the iteration cap is hit or a locked path is in the conflict; the owner still approves at (e). It amends R51's park and step 33's "escalate on any merge conflict" (`docs/BUILD_GUIDE.md:784`). Decided on the trial's measure: how often a `base_update` conflict parks, and how many of those parks part 2 had warned of.
6. *[2026-10-23, the owner (choice 266)]* **Where the judgment across changes sits.** As written, the coordinator reads each change's `evidence/manager.md` and the manager stays inside one change. The alternative: R28's manager also reads the changes in flight and names in its brief the clashes no file list shows (one behaviour changed in two places) and the order it recommends. The judgment then has one author and a file of record, and the coordinator only reports it. Settled when R28's first change is built, which comes before this one.

## Decisions it touches

- **11** (park, never page): a dated note, since the coordinator reports parks it reads but sends nothing; the park, its label and "what I need from you" are unchanged.
- **31** (one notification): a dated note or an amendment, as settled in point 4 above.
- **17, 24, 36**: kept; the coordinator runs no worktree, applies no label, merges nothing.
- **R9 part 1 and R20**: read, not changed; part 3 needs R9 part 1 built first.
- **R28**: read; its rule 8 is shared.
- **R51**: extended by parts 1 and 2; its checks 8 and 11's record half stay R51's own follow-ups.

## Order

After the real-project trial, so that the trial measures the pipeline without it (the owner, 2026-10-23, choice 264); after R28's first change, which this proposal reads; after R9 part 1 for part 3. The rank is the Order column's.
