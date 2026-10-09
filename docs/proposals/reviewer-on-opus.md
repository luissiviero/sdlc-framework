---
type: Proposal
title: The in-run reviewer on the latest Opus, checking the design against today's code
description: The CI sessions and the adversarial reviewer move to a pinned Opus 5.5, the (b) design run and the panel's advocate to Fable 5.1 (the advocate never on the session's model); the reviewer gains an angle that verifies the design's claims against the merge base, reads the files the plan lists, and has its model checked; the model check stops accepting an older model for a newer pin.
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

**Status: accepted by the owner on 2026-10-09 (roadmap R7).** Nothing is built. It goes through the front door as the next change after change 0002, which ships as 0.3.7; this change ships as **0.3.8**. The intent below is the draft that change starts from.

## The owner's decisions of 2026-10-09

| # | Question | Decision |
|---|---|---|
| 1 | Which models the framework runs on | **Opus and Fable only**, until cost says otherwise. The CI sessions move from the CLI default (Sonnet 5) to `claude-opus-5-5`, **except the (b) design run, which runs on `claude-fable-5-1`** (row 8); the adversarial reviewer runs on `claude-opus-5-5`; the panel's devil's advocate runs on `claude-fable-5-1`, so the panel keeps two models. |
| 2 | Which release the panel check is read on | Change 0002's runs on 0.3.6. The owner moves the pin to 0.3.7 before this change starts; the 0.3.6 reading stands unless 0.3.7's diff touches `plugin/panel/`, the gate's `panel` check or the panel steps of the phase commands. |
| 3 | Versions | Change 0002 = **0.3.7**, this change = **0.3.8**, the carried gaps after it. A number is fixed at the merge, not before. |
| 4 | Order | 0002 → this change → R5 → R6 → the carried gaps. *[2026-10-09, later: R10 (study entry T10) goes after R6, before the carried gaps; R9's part 1 after the gaps.]* *[2026-10-09, later: both placements approved by the owner; the R6 and R10 decision files are written together, one owner review for both; R9's part 2 at any session boundary.]* |
| 5 | The CLI and the full model ids | Verify that the pinned CLI accepts `claude-opus-5-5` and `claude-fable-5-1` as per-invocation models; bump `claude_code` if it does not. |
| 6 | Where the reviewer's model is recorded | Beside its verdict, read from the sub-agent's own transcript, as the advocate's is: the run's `modelUsage` cannot tell two sub-agents on one model apart. |
| 7 | Who adds the tally line to `HANDOFF.md` and the R6 row to `docs/ROADMAP.md` | Session 23, when it rewrites `HANDOFF.md`. *[2026-10-09, later: session 23's PR #146 added the R6 row; the tally line goes to the next session that rewrites `HANDOFF.md`.]* |
| 8 | The (b) design run on Fable | The design run is where change 0003's extra review rounds started (two rounds at gate (b)), and the cheapest place to buy quality: about 5% of the spend of changes 0001 and 0003. So `claude-fable-5-1` runs phase (b), `claude-opus-5-5` every other phase. At (b) the session and the advocate would then share Fable, so **the advocate runs on `claude-opus-5-5` at (b)**: the panel never puts its advocate on the session's model. Judged after two changes by the review rounds at gate (b) and `spend.json`. The owner confirmed it with the corrected price (Fable 5.1 is five times Sonnet 5 per token, below) and decided that **fix rounds at gate (b) run on Fable too**, since they rewrite the design. |

**Cost, at the list prices of 2026-10-06** (input / output per million tokens): Sonnet 5 $2 / $10, Opus 5.5 $4 / $20, Fable 5.1 $10 / $50. The sessions cost about twice as much per token on Opus 5.5: change 0003 cost 66 USD on Sonnet 5, so a change of that size would cost roughly 130 USD if it used the same tokens (an estimate; Opus 5.5 thinks at effort `medium` by default, and caching changes the figure). The advocate runs at most `gate.max_panel_calls` (4) times per change; at the sample's measured 11,000 output tokens per advocate call (NOTES §25), Fable adds a few dollars per change. Fable 5.1 costs five times Sonnet 5 per token: a design run like change 0003's (3.50 USD on Sonnet 5) would cost about 17.50 USD, change 0001's (2.47 USD) about 12 USD. With the fix rounds at gate (b) on Fable too (row 8), change 0003's two (12.61 USD on Sonnet 5) would have cost about 63 USD. Against Opus 5.5, Fable adds about 10 USD to a design run; one avoided review round at gate (b) (about 12 USD on Opus 5.5, about 30 USD on Fable, plus a day of the owner's time) covers it. `spend.json` of the first changes is the real figure.

## Why it is not a change folder yet

It will be a change: it alters `plugin/agents/`, the phase commands, the panel's model check and the gate, so it must go through the phases like 0001–0003. It does not get its folder now, for three reasons:
- Change ids are allocated in sequence when the folder is created (`changes/README.md`, decision 10). Created after 0002 merges, as the order above says, it takes the next free id, most likely 0004, ahead of R5 and R6.
- Merging an intent PR starts the design run within seconds. An intent merged now would start this change's design while 0002 is still in flight, and two changes at (d) or (e) at once collide on `changes/.review-seen.json` (choice 159).
- It is meant to start on 0.3.7. A folder written today would read a codebase that 0002 will change.

When its turn comes, the session copies the draft below into `changes/<id>-<slug>/intent.md` with the id `plugin/state` allocates, and opens the intent PR.

## Before the design: two checks on change 0002's build run

The owner set `review: deferred` on 2026-10-09 (`0e86cdf`, PR #147). Change 0002's build (c) is the first run on this repository, and the first on 0.3.x, that can send items to the review panel. Read that run for these two points and record them in NOTES. This change depends on both:

| Check | Where to read it | If it fails |
|---|---|---|
| **Opus is reachable from this repository's CI.** Every stored run here lists `claude-sonnet-5` alone; the sample repository ran `claude-opus-5` (NOTES §25). | `claude-c.json` `modelUsage`; `evidence/panel-models-c.json` when the panel ran | A panel run parks when no model of the run matches `panel_advocate_model`, and this change's model pins would park every run. Settle the credential before the design. |
| **The panel works on 0.3.6.** It ran live only on the sample, at 0.2.x. | `evidence/decisions-c.md`, `evidence/panel/`, `gate-c.json`'s `panel` entry, the PR's "Decisions taken for you (N)" | A gap with a test each in a 0.3.x PR before the next phase when it changes a verdict (choice 88), after the tag when it does not (choice 163). |

0002's advocate still runs on `panel_advocate_model: opus`, so its runs answer the Opus question, not the Fable one. Fable's reachability is read on the first panel run after the owner's rows below are applied; the first run of this change on 0.3.8 shows the session on Opus 5.5.

If the panel has no item at (c), (d) or (e) of 0002, neither point is exercised. Say so in the record; then a one-off probe run on Opus answers the first point before the design, and the second is read on this change's own runs.

## The intent (draft)

```markdown
# Intent: The in-run reviewer on the latest Opus, checking the design against today's code
Author: the owner (product owner). Status: proposed. Change id: <allocated by plugin/state>. Entry route: idea.

## Problem
The adversarial reviewer that judges every autonomous phase runs on the session's model (`model: inherit`), which in this repository's CI is Sonnet 5, and it never checks a design against the code that exists today. On change 0003 it said `continue` on the first design. Two fresh-context Opus reviews run by a supervising session then found build-breaking gaps: an example contradicting a decided normalisation rule, and an index line without the tag the maintain run selects by. The owner paid for two extra review rounds at gate (b). Separately, the model check of the panel cannot enforce a model version: `model_matches` accepts `claude-opus-5` for a pin of `claude-opus-5-5`, and the reverse. And no project can choose the model its CI sessions run on: the runner passes `--model` only when the `SDLC_MODEL` environment variable is set (`run_phase.py:1152`), no workflow sets it, so every session runs on the CLI's default. The owner wants the framework to run on Opus and Fable only.

## Proposed outcome
- The CI sessions run on the model `sdlc.yaml: session_model` names; the runner passes it as `--model`, and `SDLC_MODEL`, when set, still wins. A per-phase entry overrides it for one phase: this repository runs phase (b), and the fix rounds on a design pull request, on `claude-fable-5-1`, and every other phase on `claude-opus-5-5`. The template's value is `claude-opus-5-5`; an absent key keeps today's behaviour, the CLI default.
- The adversarial reviewer runs on the model `sdlc.yaml: adversarial_model` names, passed per invocation by every phase command that delegates to it, as `panel_advocate_model` is today. The plugin's default and the template's value are `claude-opus-5-5`.
- The template's `panel_advocate_model` becomes `claude-fable-5-1`, so the panel's reviewer and conciliator (on the session's model) and its devil's advocate stay on two models. The advocate never runs on the session's model: in a phase whose session runs on `panel_advocate_model` (phase (b) here), it runs on `adversarial_model` instead.
- The gate records which model the reviewer ran on, beside its verdict, read from the sub-agent's own transcript as the advocate's model is, and parks when it does not match `adversarial_model`.
- `model_matches` treats a full model id as exact: `claude-opus-5-5` matches `claude-opus-5-5` (and a context suffix such as `[1m]`), not `claude-opus-5`. A family alias (`opus`) still matches any model of that family.
- The reviewer gains a seventh angle, at (b) and (c): verify every claim `spec.md` and `plan.md` make about existing code, decisions and templates against the merge base. It reads every file `plan.md` lists, at the merge base, and `docs/decisions/index.md`.
- The reviewer's `maxTurns` rises from 50 to 80.
- Each item has a test; the change bumps both manifests to 0.3.8.

## Affected users and systems
`plugin/agents/adversarial-reviewer.md`; the phase commands that delegate to it (`sdlc-design`, `sdlc-build`, `sdlc-test`, `sdlc-fix`, `sdlc-deploy`); `plugin/ci/run_phase.py` (the session model); `plugin/panel/ledger.py` (`model_matches`, the model record); the gate's adversarial check; `template/sdlc.yaml`; `docs/OPERATING_MODEL.md` and `docs/MODEL_ALLOCATION.md`; every project that pins 0.3.8. The root `sdlc.yaml` is a guardrail file: its three lines are the owner's edit, proposed in the record as a table.

## Constraints
- The panel keeps two models in every phase: at (b) Fable 5.1 for its reviewer and conciliator and Opus 5.5 for its advocate; elsewhere the reverse.
- No new park reason except a reviewer model that does not match its pin.
- `plugin/ci/run_phase.py` changes for the session model: the record names this change in the port list (the files the first detection read may need ported). Nothing under `plugin/detect/`.
- Cost: the sessions move from Sonnet 5 to Opus 5.5, about twice the price per token, and the advocate to Fable 5.1; the design states the expected spend per change against the 0003 figures, and `spend.json` of the first two changes is read against it.

## Open questions
- Does the pinned CLI (`sdlc.yaml: claude_code`, 2.1.278 at the time of writing) accept the full ids `claude-opus-5-5` and `claude-fable-5-1`, as `--model` and as a sub-agent's per-invocation model? If not, the design bumps the CLI pin.
- Does this repository's CI credential reach Fable 5.1? Fable needs 30-day data retention on the account, and it runs safety classifiers that can end a turn with `stop_reason: refusal`. Read on the first (b) run after the owner's rows are applied.
- Fable takes longer turns on hard tasks: does the (b) run fit `gate.max_wall_clock_minutes` (120) and the runner's turn cap (200)?
```

## The owner's rows for the root `sdlc.yaml` (after the change merges)

| Link | Row | What is there now | What it must become |
|---|---|---|---|
| [`sdlc.yaml`](../../sdlc.yaml) | after line 12 | (no line) | `session_model: claude-opus-5-5` with the (b) entry `claude-fable-5-1`, in the shape the design settles |
| [`sdlc.yaml`](../../sdlc.yaml) | after line 12 | (no line) | `adversarial_model: claude-opus-5-5` |
| [`sdlc.yaml`](../../sdlc.yaml) | line 12 | `panel_advocate_model: opus` | `panel_advocate_model: claude-fable-5-1` |

## Retiring the external review

Supervising sessions run a fresh-context Opus review of every diff that touches `plugin/` or `template/` (`docs/MODEL_ALLOCATION.md:105`). Once the in-run reviewer is upgraded, that review exists only as a control: does it still find what the in-run reviewer misses?

**The rule.** For each change after 0.3.8, the session that reads the change records one line: did the external review find a build-breaking or Important item that the in-run reviewer's verdicts did not name? The external review is dropped after **two changes in a row** with "no". Any "yes" resets the count to zero.

Example: change A's design passes the in-run reviewer; the external review finds a gap → "yes", count 0. Change B: the external review finds nothing new → count 1. Change C: nothing new → count 2. The external review stops from change D on, and the line in `docs/MODEL_ALLOCATION.md` §2 is annotated with the date.

The count is per change, not per date, so it is not scheduled on a calendar. It is kept here and in each session's record:

| Change | Plugin | External review found something the in-run reviewer missed? | Count |
|---|---|---|---|
| (the first change on 0.3.8) | 0.3.8 | | |
