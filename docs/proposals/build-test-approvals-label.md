---
type: Proposal
title: The build and test approvals — the label alone, recorded by the runner
description: Under the Full profile gates (c) and (d) are approved by the owner's label alone, as the code already does; decision 3's "approving review + label" is amended and the docs corrected; the runner records who applied each label and when in status.yaml; a risk-list hit first found at build or test shows in the waiting PR's banner, and only the owner's deploy merge accepts it.
status: proposed
roadmap: R12
sources:
  - id: study-entry
    resource: docs/reviews/2026-09-28-playbook-vs-framework/target-design.md
    title: "T12, confirmed at the close of the study on 2026-10-09; from the crosswalk row test-gate (better: the framework; decision: blend), 2026-10-03"
  - id: crosswalk
    resource: docs/reviews/2026-09-28-playbook-vs-framework/crosswalk.json
    title: "Row test-gate: the article's gates around build and test against the framework's labels"
  - id: playbook
    resource: docs/reference/ai-native-sdlc-playbook.pdf
    title: "p.29, p.33: the code owner's approval at the end; p.42: an independent confidence gate between stages in a headless run"
  - id: decision-3
    resource: docs/decisions/3.md
    title: "Decision 3: approving review + phase label on the single build PR (the decision this amends)"
  - id: code
    resource: plugin/ci/run_phase.py
    title: "check_approval and label_applied_by_a_human: the label alone is checked, read at main 71e4da7, plugin 0.3.6"
generated: { by: sdlc-framework-session/ccr-cd596b46-vq58fk, at: 2026-10-09T16:30:00Z }
---

# The build and test approvals: the label alone, recorded by the runner

**Status: proposed (roadmap R12), from study entry T12, confirmed by the owner on 2026-10-09.** Nothing is built. Its line goes into the approvals list of R11, so it follows R11 or is built with it.

## The problem

Decision 3 says the owner approves gates (c) and (d), under the Full profile, with "approving review + phase label" on the single build PR[^decision-3]. The code checks the label only: the runner looks for `sdlc:c-approved` or `sdlc:d-approved` on the build PR and checks that the last `labeled` event's actor is not the workflow token (`plugin/ci/run_phase.py` `check_approval`, `label_applied_by_a_human`)[^code]. `docs/OPERATING_MODEL.md` §4, the hand-over text of `/sdlc-build` and `/sdlc-test` and the comment in `template/sdlc.yaml` repeat the decision's wording, so the documents promise a review the framework never asks for. And who applied the label is recorded only in GitHub's label event: nothing in the change's folder says who approved build or test, or when.

The owner chose, at the crosswalk row test-gate, the label alone: one act, not two, and the record made true.

## What the article says

The hand-run loop has no gate after build or test: the engineer runs the session, the tests run in it, and the code owner approves at the end, through branch protection on the PR (p.29, p.33). In a headless run an independent confidence gate decides between stages, and only a failed gate reaches a person (p.42)[^playbook]. The framework's Full profile adds two human gates the article does not have, which decision 18 chose for a new project; this proposal changes what those gates ask, not whether they exist.

## What the framework does today

Read at `main` 71e4da7, plugin 0.3.6[^crosswalk].

- Under the Standard profile gates (c) and (d) continue on their own. Under Full (the project's profile, or the change's `profile_override` in `status.yaml`; study entry T1 adds a per-change switch at the gate (b) merge) gate (c) labels the build PR `sdlc:c-ready` and the owner's `sdlc:c-approved` starts (d); gate (d) labels it `sdlc:d-ready` and `sdlc:d-approved` starts (e).
- The runner checks that the label is on the build PR and that the last `labeled` event's actor is not `github-actions[bot]` (`check_approval`, `label_applied_by_a_human`); another bot account would pass, and with no token the actor is not checked. The actor is not written anywhere in git.
- The un-park labels already record their actor in `status.yaml` (`risk_accepted_by`, `iterations_reset_by`, `tests_unlocked_by`, decision 24), a built precedent for the line below.
- The documents that say "approving review + label": decision 3, `docs/OPERATING_MODEL.md` §4 (the gates table), `plugin/commands/sdlc-build.md` and `plugin/commands/sdlc-test.md` (the `wait` hand-over text), `template/sdlc.yaml` (the profile comment).

## The proposal

1. **The label alone, as the code does it.** One act, not two. Decision 3 is amended to the label alone, and the four documents above are corrected to match the code. The actor check stays as it is (not the workflow token); whether it narrows to the owner's account is the question T17, T18 and T24 carry, and is decided there.
2. **The runner records the approval.** At the start of (d) and of (e) the runner writes who applied the approval label and when: one line of R11's approvals list in `status.yaml` (`act` "build approved" or "test approved", `by`, `at`, `via` the label on the pull request, the head commit), beside the plan-acceptance line (T1) and the risk-acceptance line (T9), so the change's record holds every approval without GitHub's label history.
3. **A risk-list hit under Full.** A hit first found at (c) or (d) shows in the "Needs your close look" banner of the PR waiting for the owner's label, so the owner can stop it with "Request changes"; only the owner's (e) merge accepts it (T9), so a risk is accepted in one act, recorded once.

## How it is judged

After it ships, every Full-profile change's `status.yaml` carries a line for each approval label with the owner's login and a time; a change approved with no such line is the failure. The four documents and the code say the same thing.

## What to settle before building

| Question | Recommended |
|---|---|
| The line's fields | R11's shape (`act`, `by`, `at`, `via`, `pr`, `head`, `details`); the key names judged with T4 |
| Who may apply the label | As today, any actor but the workflow token; narrowing it to the owner's account is decided with T17, T18 and T24, which carry that question |
| Where the banner line for a risk hit found at (c) or (d) comes from | The gate's risk-list check, already run at (c) and (d); the banner is T9's |
| The decision file | `docs/decisions/3.md` gains `amended_by` pointing at this change's decision file, written before the intent as R6 and R10 do |

## Considered and not chosen

None recorded in the entry: the question at the row was the documents' wording against the code's, and the owner took the code's.

## Decisions it touches

3 is amended: "approving review + phase label" becomes the label alone, with the actor recorded. A decision file is written before the intent, as R6 and R10 do. 18 (the profiles) and 24 (the un-park labels, the precedent for the line) are unchanged.

## Order

Second of the study's proposals, after R11, whose list it writes into.

[^decision-3]: `docs/decisions/3.md`.
[^code]: `plugin/ci/run_phase.py`, `check_approval` and `label_applied_by_a_human`.
[^playbook]: `docs/reference/ai-native-sdlc-playbook.pdf` p.29, p.33, p.42.
[^crosswalk]: `docs/reviews/2026-09-28-playbook-vs-framework/crosswalk.json`, row test-gate, and `target-design.md` T12 ("Today").
