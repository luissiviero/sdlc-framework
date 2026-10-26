---
type: Proposal
title: Revisit decision 17's parallel worktrees once the plugin has run real work for a while
description: Decision 17 says worktrees come "only once review keeps up, i.e. probably never for one person"; the owner asked for that "probably" to be revisited rather than read as "never", at a trigger the record can count.
status: proposed
roadmap: R50
sources:
  - id: owner
    resource: "the owner's message of 2026-10-19, session ccr-70fb3ae3-39fz5m ('Since it's \"probably never\", that is, it's not actually \"never\" — register to revisit this once the plugin is up and running for a while')"
    title: "The request to register the revisit"
  - id: decision-17
    resource: docs/decisions/17.md
    title: "When to start evals and parallel worktrees (option 2 accepted; reversible)"
  - id: article
    resource: docs/reference/ (PDF p.25)
    title: "Parallel sessions' ceiling is how many streams one person can review properly"
generated: { by: sdlc-framework-session/ccr-70fb3ae3-39fz5m, at: 2026-10-19T12:00:00Z }
---

# Revisit decision 17's parallel worktrees
**Names since R45** (decision 39; the renames built in plugin 1.0.43 to 1.0.47; added on 2026-10-26, the text below keeps the old names, choice 126): `(e)` -> deploy. \
**Status: proposed on 2026-10-19 at the owner's request (ROADMAP R50).** Nothing is built and nothing is reopened now: this row only says when decision 17's second half is put back to the owner.

## What decision 17 says today

"Worktrees only once review keeps up, i.e. probably never for one person" (option 2, reversible). Step 33 of the build guide is recorded "not built" under it. The reason is the article's ceiling (p.25): parallel sessions are worth as many streams as one person can review properly, and the owner reviews at phase ends.

Worktrees are a local-checkout concern: several sessions on the owner's machine, each in its own `git worktree`. The CI runs already isolate (one runner per job, one concurrency group per work branch), and cloud sessions each get their own container, so neither needs worktrees.

## The trigger

The revisit is due when **20 changes have passed gate (e) on a project other than the sample**, counted from that project's `changes/*/status.yaml`. Twenty is decision 17's own threshold for its first half (the eval suite starts from "20 to 50 real tasks", p.30), so both halves of the decision come back together, from the same body of real work.

## What the revisit answers

1. **Does the owner's review keep up?** The time each PR waited for the owner at its gates, from the gate records and the PRs' timestamps (R26's measures, if built by then).
2. **Does the owner still run sessions locally?** If every session runs in CI or in the cloud, worktrees buy nothing and the decision stays.
3. **If both say yes:** a proposal for step 33 (how `/sdlc-*` commands find their worktree, and which files two local sessions must never share), through the front door as a framework change.

## Decisions it touches

17 (its second half, at the revisit only, with the owner).
