---
type: Proposal
title: An external second opinion on the design at gate (b), from a model of another vendor
description: After the (b) design run, the runner sends the intent, the spec, the plan and the files the plan lists to Gemini and records its verdict beside the adversarial reviewer's; it adds a reader, it replaces nothing, and it never parks.
status: proposed
roadmap: R8
sources:
  - id: owner-session
    resource: "the owner's session of 2026-10-09 (branch ccr-1578d710-8r04sw): the owner has a Gemini API key from Google AI Studio and asked for this use as R8, an addition to the current checks, not a substitute"
    title: "The owner asks for an independent design check at gate (b)"
  - id: panel-two-models
    resource: template/sdlc.yaml
    title: "Lines 27-29: a panel reduces variance, not bias; three judges on one model share its blind spots"
  - id: r7
    resource: docs/proposals/reviewer-on-opus.md
    title: "R7: the in-run reviewer on Opus 5.5, the design run on Fable 5.1"
generated: { by: sdlc-framework-session/ccr-1578d710-8r04sw, at: 2026-10-09T15:00:00Z }
---

# An external second opinion on the design at gate (b)

**Status: proposed (roadmap R8).** Nothing is built. The owner asked for it on 2026-10-09 as an **addition** to the current checks: the adversarial reviewer, the panel and the owner's review at gate (b) all stay as they are. It starts after R7 has been measured on two changes (below).

## The problem

Every judge in the framework is a Claude model. R7 spreads them over two (Fable 5.1 designs, Opus 5.5 reviews), but both come from one vendor and may share blind spots; the template's own comment on the panel says why that matters: "three judges on one model share its blind spots"[^panel-two-models]. Change 0003's design passed the in-run reviewer and still needed two review rounds at gate (b); change 0002's design needed three. A design gap found at (b) costs one review round; the same gap found at (e) costs a build.

## The proposal

After the (b) design run, the runner sends the change's `intent.md`, `spec.md`, `plan.md` and the files `plan.md` lists (at the merge base) to a Gemini model, with a brief taken from the adversarial reviewer's attack angles, including R7's seventh angle (the design's claims against today's code). It records the answer:
- `evidence/external-review-b.json`: the provider, the model id the API reports, the verdict (`no concerns` or `concerns`), one line per concern with the file and the claim it disputes, the tokens used, and the time;
- a "Second opinion" section in the design PR's body, one line per concern, so the owner reads it at gate (b) next to "what I need from you".

**It adds a reader and replaces nothing.**
- It never parks a change, never feeds the gate's verdict, and is not a panel item.
- A failed call (no key, an outage, a quota, a timeout, a refusal) is recorded as "not run: <reason>"; the job stays green and the phase continues.
- The owner decides what to do with each concern, as with any review finding: a "Request changes" review carries the real ones into the fix round.

**How it runs.**
- A Python step of the runner after the model's session (decision 7), like the commands step since 0.3.0: outside the session's sandbox, after the session has ended.
- The key lives only in a GitHub Actions secret (`GEMINI_API_KEY`), passed to that step's environment alone. The Claude session never sees it: the session's environment is built without it, and a test proves that.
- `sdlc.yaml` turns it on: `external_review: {provider: gemini, model: <the id the owner picks>, phases: [b]}`. An absent key means off, so no other project changes.
- Fix rounds at gate (b) run it again on the rewritten design.

## How it is judged

For each change after it is turned on, the session that reads the change records one row: did the second opinion raise a concern that proved real (the owner carried it into a review, or a later phase hit it) and that the in-run reviewer had not named? Kept in a tally table in this file, as R7's retirement rule is.

After five changes the owner decides, with that tally:
- keep it advisory;
- promote it (a concern becomes a panel item, or a park); this changes decision 11 or 21, so it is a new decision;
- or drop it.

## What to settle before building

| Question | Options | Recommended |
|---|---|---|
| When it starts | Now, beside R7 · after R7 is measured on two changes | **After R7's two changes**: if R7 alone stops the rounds at gate (b), a third judge adds cost and nothing else; if not, the tally starts from a clean baseline |
| What Google may do with the code | The key's terms decide | **Read the terms of the key's tier before the first call.** If the tier lets Google use submitted content to improve its products, use a tier that does not. The repository is the owner's; sending it to a second vendor is the owner's call, made knowingly. |
| Which Gemini model | The owner picks it in AI Studio | Recorded in `sdlc.yaml`; this file names no model id, none was verified here |
| The client | The vendor's Python package · plain HTTPS with the standard library | Decided in the design: one new dependency against a small hand-written request; either way, an outage must never turn the job red |
| Cost | Unknown: no Gemini price was verified here | The record keeps the tokens per call; the design states a per-change ceiling, and a call over it is "not run" |
| Network | The runner step calls one host | The security baseline keeps the model session off the network; this step is the runner's, outside the session, with one allowed host. Reviewed in the design against the security baseline skill. |

## Decisions it touches

7 (Python for the step), 11 (unchanged: it never parks), 21 (unchanged: not a panel member), 6 (the root `sdlc.yaml` key is the owner's edit), the security baseline (a secret and one outbound host in a runner step). The workflow templates that run phase (b) gain the secret in that step's environment.

## Not in scope

- **A model judge for the evals** (`plugin/evals/`, from another vendor so that no Claude model grades Claude's output). It belongs to the evals, not to gate (b), and the evals have no model judge today, so it needs its own design. It is noted here so it is not lost; it becomes its own candidate when the evals need a judge.
- Other phases: (c) to (e) have the verifier, the review pass and the runner's commands; a second opinion there is a later question, answered by this tally.

## Tally

| Change | Plugin | Concerns raised | Real and missed by the in-run reviewer | Cost |
|---|---|---|---|---|
| (the first change with it on) | | | | |

[^panel-two-models]: `template/sdlc.yaml`, the comment above `panel_advocate_model`.
