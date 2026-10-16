---
type: Proposal
title: The pipeline's speed — the fast lane, review requests at waiting gates, deferred review by default, and a GitHub App identity
description: Four changes that cut a routine change from 1.8-7.4 days to the same day by removing the waits that do not need the owner, built first, before every other candidate, as session pull requests.
status: accepted
roadmap: R46, R47, R48, R49
sources:
  - id: owner
    resource: "the owner's question of 2026-10-15 ('1.8 to 7.4 days per change … unacceptable') and approval of 2026-10-16 ('Approved'), session ccr-01de3f80-ilnomi"
    title: "The table of the decisions that make the pipeline slow, with the recommendation per row"
  - id: measurements
    resource: changes/0001-*/evidence/gate-*.json, changes/0002-*/…, changes/0003-*/…, and the sample's changes/0001-*, 0002-* (claude-*.json duration_ms)
    title: "Model time 0.3-6.4 hours per change against 1.8-7.4 days elapsed; the sample's change 0002 reached its last gate 5.5 hours after its intent"
  - id: decisions
    resource: docs/decisions/30.md, 31.md, 32.md, 33.md
    title: "The fast lane (amends 2, 18); review requests at waiting gates (amends 11, 20); deferred review by default (amends 21); a GitHub App identity (amends 5)"
generated: { by: sdlc-framework-session/ccr-01de3f80-ilnomi, at: 2026-10-16T12:00:00Z }
---

# The pipeline's speed

**Status: accepted by the owner on 2026-10-16 (roadmap R46 to R49), with decisions 30 to 33.** Nothing is built. These four, with R10 and R17, are built before every other candidate.

## The problem

Across the five changes that finished, the model sessions worked 0.3 to 6.4 hours per change, while each change took 1.8 to 7.4 days from intent to its last gate. More than nine tenths of the time was waiting: every human gate waits for the owner's next look (once or twice a day, nothing notifies), a red target or a judgment item parks for the owner, every fix round starts from the owner's review, and the project's own CI on an automation-pushed head waits for the owner's approval of the runs. When nothing parked and the owner answered quickly, the sample's change 0002 reached gate (e) 5.5 hours after its intent.

## The proposal

| R | What | Decision |
|---|---|---|
| R46 | **The fast lane.** An intent the owner wrote and pushed is accepted by that act (no gate (a)); gate (b) waits for the owner only on a non-routine plan (the adversarial reviewer's class); a routine design continues to the build, its spec and plan reaching the owner at (e) | 30 |
| R47 | **Review requests at waiting gates.** When a pull request starts waiting for the owner (a human gate, a park), the automation requests the owner's review, so GitHub's own push reaches the phone; nothing else notifies | 31 |
| R48 | **Deferred review by default, and higher run caps for the build.** `/sdlc-init` proposes and the template carries `review: deferred`; the build run's turn and wall-clock caps rise, within the budget cap | 32 |
| R49 | **A GitHub App identity.** The automation pushes and opens pull requests as a GitHub App, so the project's CI runs on them by itself; the App is the one R22 creates, so R22's App setup comes first and R22's merge step stays in R22 | 33 |

With R10 (a red target starts the next round itself) and R17 (an `@claude` comment starts a round), a routine change goes from intent to merge the same day: model time plus the owner's one look at (e); a non-routine change takes about a day.

## How it is judged

On the next five changes of a project: time from the intent's push to the (e) merge, and the owner's acts per change, against the five measured above.

## What to settle before building

| Question | Recommended |
|---|---|
| How "the owner wrote the intent" is read | The pull request's author, or the intent commit's author, is the owner's account (R17's `is_owner_actor`) |
| Whether an incident or ticket intent takes the fast lane | No: those are written by the automation, and gate (a) is their triage |
| Who is requested as reviewer on an organization repository | The owner key R17 adds to `sdlc.yaml` |
| The new build caps | Set from the turn counts of changes 0001 to 0003, with the budget cap as the bound |
| Whether the App setup needs a desktop browser | Yes (R21 lists it) |

## Considered and not chosen

- Dropping gate (b) for every plan: a non-routine design is where a look before code pays most.
- A notification channel of the framework's own: a second channel to maintain.
- A personal access token instead of an App: tied to a person and broader than needed.

## Decisions it touches

30 (amends 2 and 18), 31 (amends 11 and 20; the `CLAUDE.md` line is the owner's edit), 32 (amends 21), 33 (amends 5; 4 kept).

## Order

First, before every other candidate: R10, R46, R47, R48, R17, R49 (the "pipeline sprint", ROADMAP Order 1 to 6), built as session pull requests with an independent review, not through the framework's own pipeline (the owner's choice of 2026-10-16 for framework changes). Before R10's build, the owner answers who builds decision 29's reset (R10 or R25).
