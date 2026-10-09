---
type: Proposal
title: The in-run reviewer on the latest Opus, checking the design against today's code
description: The adversarial reviewer moves from the session's model to a pinned Opus, gains an angle that verifies the design's claims against the merge base, reads the files the plan lists, and has its model checked; the model check stops accepting an older model for a newer pin.
status: accepted
roadmap: R7
sources:
  - id: owner-session
    resource: "the owner's session of 2026-10-09 (branch ccr-1578d710-8r04sw): the comparison of the in-run reviewer with the external Opus reviews, every recommendation accepted"
    title: "The owner accepts the reviewer recommendations and asks for an intent for 0.3.8"
  - id: reviewer-agent
    resource: plugin/agents/adversarial-reviewer.md
    title: "The adversarial reviewer: model inherit (line 6), maxTurns 50 (line 7), six attack angles"
  - id: model-matches
    resource: plugin/panel/ledger.py
    title: "model_matches, line 577: a full id is satisfied by any id it starts with or that starts with it"
  - id: design-run-0003
    resource: docs/notes/34.md
    title: "Change 0003's design run: the adversarial reviewer said continue on the first design"
  - id: second-review-0003
    resource: docs/notes/35.md
    title: "Change 0003's fix rounds: the second fresh-context review was needed for build-breaking gaps"
generated: { by: sdlc-framework-session/ccr-1578d710-8r04sw, at: 2026-10-09T12:00:00Z }
---

# The in-run reviewer on the latest Opus

**Status: accepted by the owner on 2026-10-09 (roadmap R7).** Nothing is built. It goes through the front door as a change after the carried gaps of 0.3.7, and ships as **0.3.8**. The intent below is the draft that change starts from.

## Why it is not a change folder yet

It will be a change: it alters `plugin/agents/`, the phase commands, the panel's model check and the gate, so it must go through the phases like 0001–0003. It does not get its folder now, for three reasons:
- Change ids are allocated in sequence when the folder is created (`changes/README.md`, decision 10). The owner's order (`docs/handoffs/2026-10-08-owner-answers.md`) gives the next ids to R5 (the pin-bump PR) and R6 (the `accept` verb). Taking 0004 now would shift them.
- Merging an intent PR starts the design run within seconds. An intent merged now would start this change's design while 0002 is still in flight, and two changes at (d) or (e) at once collide on `changes/.review-seen.json` (choice 159).
- It is meant to ship after 0.3.7. A folder written today would read a codebase that 0.3.7 will change.

When its turn comes, the session copies the draft below into `changes/<id>-<slug>/intent.md` with the id `plugin/state` allocates, and opens the intent PR.

## Before the design: two checks on change 0002's build run

The owner set `review: deferred` on 2026-10-09 (`0e86cdf`, PR #147). Change 0002's build (c) is the first run on this repository, and the first on 0.3.x, that can send items to the review panel. Read that run for these two points and record them in NOTES. This change depends on both:

| Check | Where to read it | If it fails |
|---|---|---|
| **Opus is reachable from this repository's CI.** Every stored run here lists `claude-sonnet-5` alone; the sample repository ran `claude-opus-5` (NOTES §25). | `claude-c.json` `modelUsage`; `evidence/panel-models-c.json` when the panel ran | A panel run parks when no model of the run matches `panel_advocate_model`. This change's model pin would park every gate too. Settle the credential before the design. |
| **The panel works on 0.3.6.** It ran live only on the sample, at 0.2.x. | `evidence/decisions-c.md`, `evidence/panel/`, `gate-c.json`'s `panel` entry, the PR's "Decisions taken for you (N)" | A gap with a test each in a 0.3.x PR before the next phase when it changes a verdict (choice 88), after the tag when it does not (choice 163). |

If the panel has no item at (c), (d) or (e) of 0002, neither point is exercised. Say so in the record and read the next change's runs instead.

## The intent (draft)

```markdown
# Intent: The in-run reviewer on the latest Opus, checking the design against today's code
Author: the owner (product owner). Status: proposed. Change id: <allocated by plugin/state>. Entry route: idea.

## Problem
The adversarial reviewer that judges every autonomous phase runs on the session's model (`model: inherit`), which in this repository's CI is Sonnet 5, and it never checks a design against the code that exists today. On change 0003 it said `continue` on the first design. Two fresh-context Opus reviews run by a supervising session then found build-breaking gaps: an example contradicting a decided normalisation rule, and an index line without the tag the maintain run selects by. The owner paid for two extra review rounds at gate (b). Separately, the model check of the panel cannot enforce a model version: `model_matches` accepts `claude-opus-5` for a pin of `claude-opus-5-5`, and the reverse.

## Proposed outcome
- The adversarial reviewer runs on the model `sdlc.yaml: adversarial_model` names, passed per invocation by every phase command that delegates to it, as `panel_advocate_model` is today. The plugin's default and the template's value are `claude-opus-5-5`. The session itself stays on its own model.
- The gate records which model the reviewer ran on, read from the run's `modelUsage`, and parks when no model of the run matches `adversarial_model`, like the panel's model check.
- `model_matches` treats a full model id as exact: `claude-opus-5-5` matches `claude-opus-5-5` (and a context suffix such as `[1m]`), not `claude-opus-5`. A family alias (`opus`) still matches any model of that family.
- The reviewer gains a seventh angle, at (b) and (c): verify every claim `spec.md` and `plan.md` make about existing code, decisions and templates against the merge base. It reads every file `plan.md` lists, at the merge base, and `docs/decisions/index.md`.
- The reviewer's `maxTurns` rises from 50 to 80.
- Each item has a test; the change bumps both manifests to 0.3.8.

## Affected users and systems
`plugin/agents/adversarial-reviewer.md`; the phase commands that delegate to it (`sdlc-design`, `sdlc-build`, `sdlc-test`, `sdlc-fix`, `sdlc-deploy`); `plugin/panel/ledger.py` (`model_matches`, the model record); the gate's adversarial check; `template/sdlc.yaml`; `docs/OPERATING_MODEL.md` and `docs/MODEL_ALLOCATION.md`; every project that pins 0.3.8. The root `sdlc.yaml` is a guardrail file: its two lines are the owner's edit, proposed in the record as a table.

## Constraints
- The session's model does not change. The panel's reviewer and conciliator keep inheriting it, so the panel keeps two models.
- No new park reason except a reviewer model that does not match its pin.
- Nothing under `plugin/detect/` or `plugin/ci/run_phase.py` unless the model record needs the runner; if it does, the record names it in the port list.
- Cost: one reviewer call per gate moves to Opus; the design states the expected spend per change against the 0003 figures.

## Open questions
- Does the pinned CLI (`sdlc.yaml: claude_code`, 2.1.278 at the time of writing) accept the full id `claude-opus-5-5` as a sub-agent's per-invocation model? If not, the design bumps the CLI pin, or uses the alias with the exact-id check failing loudly.
- Should the panel's advocate move to the same full id? The owner accepted it; the design confirms it keeps the panel on two models.
- Where does the reviewer's model record live: beside its verdict, as the panel's does, or in `gate-<phase>.json`?
```

## The owner's rows for the root `sdlc.yaml` (after the change merges)

| Link | Row | What is there now | What it must become |
|---|---|---|---|
| [`sdlc.yaml`](../../sdlc.yaml) | after line 12 | (no line) | `adversarial_model: claude-opus-5-5` |
| [`sdlc.yaml`](../../sdlc.yaml) | line 12 | `panel_advocate_model: opus` | `panel_advocate_model: claude-opus-5-5` |

## Retiring the external review

Supervising sessions run a fresh-context Opus review of every diff that touches `plugin/` or `template/` (`docs/MODEL_ALLOCATION.md:105`). Once the in-run reviewer is upgraded, that review exists only as a control: does it still find what the in-run reviewer misses?

**The rule.** For each change after 0.3.8, the session that reads the change records one line: did the external review find a build-breaking or Important item that the in-run reviewer's verdicts did not name? The external review is dropped after **two changes in a row** with "no". Any "yes" resets the count to zero.

Example: change A's design passes the in-run reviewer; the external review finds a gap → "yes", count 0. Change B: the external review finds nothing new → count 1. Change C: nothing new → count 2. The external review stops from change D on, and the line in `docs/MODEL_ALLOCATION.md` §2 is annotated with the date.

The count is per change, not per date, so it is not scheduled on a calendar. It is kept here and in each session's record:

| Change | Plugin | External review found something the in-run reviewer missed? | Count |
|---|---|---|---|
| (the first change on 0.3.8) | 0.3.8 | | |
