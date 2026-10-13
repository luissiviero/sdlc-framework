---
type: Proposal
title: The test loop closes by itself in CI — a red target found by the runner starts the next fix round, and the verifier says which tree it read
description: When the runner's commands step finds a red target, it dispatches the next fix round itself with the failing logs as its constraint, the iteration count goes up by one, and the change parks only at the iteration cap; in CI the verifier's report names the record it read and says the final tree's result is the runner's.
status: accepted
roadmap: R10
sources:
  - id: study-entry
    resource: docs/reviews/2026-09-28-playbook-vs-framework/target-design.md
    title: "T10, confirmed at the close of the study on 2026-10-09; from the crosswalk rows test-loop (better: the playbook; decision: blend) and test-verify (better: both; decision: blend), 2026-10-03"
  - id: roadmap
    resource: docs/ROADMAP.md
    title: "Row R10: accepted by the owner on 2026-10-09; its decision file is written together with R6's"
  - id: playbook
    resource: docs/reference/ai-native-sdlc-playbook.pdf
    title: "p.27: run, fix and re-run until the check passes, so what reaches the engineer has already passed it"
  - id: choice-154
    resource: docs/progress/session-18.md
    title: "Choice 154: a red target found by the runner parks the change and the owner's /sdlc-fix is the round"
  - id: decision-11
    resource: docs/decisions/11.md
    title: "Decision 11: park, never page"
  - id: start-table
    resource: docs/handoffs/2026-10-13-study-line-start-table.md
    title: "Row 2d: a short file for uniformity, written with R10's decision file"
generated: { by: sdlc-framework-session/ccr-9497322b-1iu07x, at: 2026-10-13T13:30:00Z }
---

# The test loop closes by itself in CI

**Status: accepted by the owner on 2026-10-09 (roadmap R10), from study entry T10.** Nothing is built. This short file exists for uniformity with the study's other proposals (the start table's row 2d); the entry's full text is `target-design.md` T10, and its decision is `docs/decisions/29.md`, written with R6's decision 28 for one owner review.

## The problem

The article's loop is run, fix and re-run until the check passes, "so what reaches the engineer has already passed it" (p.27)[^playbook]. Since plugin 0.3.2 no project target runs inside the CI session: after the session the runner runs build, test and lint once, outside the sandbox, writes the three logs, rewrites the gate record and parks the change on a red target (`plugin/gate/gate.py`, `run_deferred_commands`). The next round starts only on an act of the owner: a "Request changes" review, a `workflow_dispatch` of `sdlc-fix.yml` or an un-park label. That was the owner's choice in 0.3.2: "a red target found by the runner parks the change and the owner's `/sdlc-fix` is the round"[^choice-154]. In CI the verifier runs no target either: it quotes the runner's record of the previous phase, the run on the tree the phase started from.

## The proposal

1. **A red target starts the next round by itself.** When the runner's commands step finds a red target, it dispatches a fix round itself instead of waiting for the owner's review. The round's constraint is the failing logs, the iteration count goes up by one, and the runner runs the targets again after the round. Events caused by the workflow token start no workflow run that proceeds by itself, so the runner dispatches the round explicitly, as it already dispatches the next phase.
2. **The change parks only at the iteration cap** (`gate.max_iterations`, 3, or `max_iterations_non_routine`, 2), with its partial evidence, as any limit does today[^decision-11]. What reaches the owner on a red target has then passed the check or used up its rounds.
3. **The verifier says which tree it read.** In CI its report names the record it quoted, by phase and commit, and says that the final tree's result is the runner's, shown in the check run `sdlc/d`.
4. **The runner's single run stays**: build, test and lint once after the session, outside the sandbox, with the evidence logs written from that run.

## Considered and not chosen

- Running the targets inside the sandbox again: the sandbox denies a nested `.env` to every process the session starts, and renaming fixtures or narrowing the deny rule was rejected (choices 133 and 154).
- A helper that runs the targets for the session outside the sandbox while it works: it would be a hole in the sandbox the session controls.

## What to settle before building

The three open points of T10, with this PR's recommendations in decision 29: whether the automatic rounds share the iteration cap with the owner's own rounds; whether a target that cannot be fixed from the session (a missing target, a timeout, an infrastructure failure) starts a round or parks at once; the verifier's exact wording, and whether the PR's summary also says which run its evidence came from.

## Decisions it touches

Decision 11, since a red target found by the runner no longer parks at once (a limit hit still parks); PROGRESS choice 154, the owner's choice of 0.3.2. Both are amended by decision 29. Crosswalk rows: test-loop, test-verify; x-headless (the runner's step) and x-limits (the iteration cap now also counts these rounds).

## Order

Accepted by the owner on 2026-10-09 to run before 1.0.0, after R6 and before the carried gaps (ROADMAP R10). `HANDOFF.md`'s current order puts it after the 1.0.0 read; decision 29 records the question.

[^playbook]: `docs/reference/ai-native-sdlc-playbook.pdf` p.27.
[^choice-154]: `docs/progress/session-18.md`, choice 154.
[^decision-11]: `docs/decisions/11.md`.
