---
type: Proposal
title: Concurrent changes, safe by construction — a build PR is gated against the default branch it merges into
description: The pipeline already runs several changes at once; what it lacks is a guard that a build PR's checks still hold after another change merged, plus the id reservation, the spend ceiling and the view of the changes in flight that R25, R9 and R20 partly carry.
status: accepted
roadmap: R51
sources:
  - id: owner
    resource: "the owner's questions of 2026-10-19, session ccr-70fb3ae3-39fz5m ('Concurrency on the sample (the pipeline itself): will that save time meaningfully, either now or running real projects? If so, tell me how should we revise to structurally implement these concurrences')"
    title: "The question this proposal answers"
  - id: measurements
    resource: docs/proposals/pipeline-speed.md, its "measurements" source
    title: "Model time 0.3-6.4 hours per change against 1.8-7.4 days elapsed, before the pipeline sprint"
  - id: workflows
    resource: template/.github/workflows/sdlc-design.yml, sdlc-build.yml, sdlc-test.yml, sdlc-deploy.yml, sdlc-fix.yml (concurrency group "sdlc-<head_ref>"), sdlc-release.yml
    title: "One concurrency group per work branch; the release runs deploy.command on the owner's merge"
  - id: ruleset
    resource: plugin/commands/sdlc-init.md, the branch ruleset bullet
    title: "The owner is the ruleset's Exempt bypass actor, so the rules do not run for the owner's merges"
  - id: ids
    resource: plugin/state/conventions.py next_change_id, plugin/state/gitops.py remote_change_ids
    title: "A new id is the highest local or remote id plus one"
generated: { by: sdlc-framework-session/ccr-70fb3ae3-39fz5m, at: 2026-10-19T12:00:00Z }
---

# Concurrent changes, safe by construction

**Status: proposed on 2026-10-19 at the owner's request (ROADMAP R51).** Nothing is built. *[2026-10-19, the owner (choice 233): accepted as recommended, Order 10, with R25 parts 1-2 at 11.]*

## Does running changes concurrently save time?

- **On the sample, now: no.** Its changes are a few lines each and exist to prove the plugin live. One change at a time keeps each result attributable to one plugin version.
- **On a real project: yes, in throughput, not in a single change's elapsed time.** Before the pipeline sprint, the model worked 0.3 to 6.4 hours of a change's 1.8 to 7.4 days; the rest was waiting for the owner. R46 to R49 cut those waits, but every gate still waits for the owner's look. While one change waits at a gate, another's design, build or test run can work, so N changes in flight finish in far less than N times one change's elapsed time. The ceiling is the owner's review capacity (decision 17, article p.25), not the runners.

## What already works

- Every phase workflow keys its concurrency group on the change's work branch (`sdlc-<head_ref>`), so two changes' runs never queue behind each other, and one change's runs never overlap.
- Each change has its own folder, branches, gate records and PR; the maintain runs already opened three incident intents side by side (the sample's PRs #55 to #57).
- A new id skips every id that has a remote `sdlc/<id>/*` branch.
- Since 1.0.10, a build restarted after a preflight park merges the default branch first and parks on a conflict.

Running several changes needs no setting outside the pipeline today. What it lacks is below.

## The gaps

| # | Gap | Why it matters with several changes | Proposed answer | Where |
|---|---|---|---|---|
| G1 | **A build PR's checks are not re-run when the default branch moves.** Gates (c) and (d) and the project's CI ran against the base the branch had then. Nothing re-runs when another change merges, and the owner's merge is Exempt from the ruleset, so a "require branches to be up to date" rule would not bind it. | Two changes that pass alone can break together (the same function changed two ways, a renamed name still called). The release then runs `deploy.command` after the owner's merge. | Before gate (e) is offered, and again in the release before `deploy.command`, the runner checks that the build PR's head contains the default branch's tip. When it does not: merge the default branch into the work branch (a merge commit, as 1.0.10's restart), re-run the deterministic checks of gate (d), and park on a conflict or a red check with "Update branch" as the need. The spec decides whether the release refuses or re-checks. | `plugin/ci/run_phase.py`, `sdlc-release.yml`, OPERATING_MODEL §4 |
| G2 | **Two allocations before either pushes can take the same id.** The remote check sees only pushed branches. | Two intents written at once (two sessions, or a session and a maintain run) get two folders with one id. | `new-change` pushes an empty `sdlc/<id>/a` at allocation when a remote is reachable, and takes the next id if that push is refused. | `plugin/state/cli.py`, `/sdlc-plan` step 2 |
| G3 | **No ceiling across changes.** Each run has its caps; nothing caps the sum. | N changes in flight spend N times as much, unseen until the bill. | Already R25 (the weekly ceiling and a budget per change); no new work here. | R25 |
| G4 | **No single view of the changes in flight.** | The owner learns which change waits on what from the digest and the PR list. | Already R9 part 1 (`changes/index.md`) and R20 (the digest ordered by what needs the owner); no new work here. | R9, R20 |

R51 is G1 and G2. G3 and G4 stay where they are; R51 only names them as the other half of running several changes safely, so the owner can move them up the Order if concurrency becomes the way the project works.

## Not verified

- That a build PR behind the default branch merges and releases without any re-run was read from the workflows and `sdlc-init.md`, not seen on a live run.
- How often G2's window opens in practice is unknown; no collision has been recorded.

## Decisions it touches

13 (the release: kept, with a check before `deploy.command`), 17 (the ceiling on parallel streams: kept), 4 (only the owner merges: kept).
