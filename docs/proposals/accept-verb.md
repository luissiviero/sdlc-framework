---
type: Proposal
title: The accept verb — a label that waives the Important review findings of the head it is applied on, without a fix round
description: The owner applies sdlc:accept-findings on a build PR; the next gate (e) counts every Important finding recorded for that head as accepted, records each signature with the label's actor, and still blocks any finding that appears later.
status: accepted
roadmap: R6
sources:
  - id: owner-answer
    resource: "the owner's answer of 2026-10-08 in the PR-audit session (docs/handoffs/2026-10-08-owner-answers.md)"
    title: "Yes, build it after change 0002 and R5"
  - id: carried
    resource: docs/progress/session-4.md
    title: "Session 4 (line 118): an owner accept verb for findings, a label or a comment that waives one Important finding without the panel, proposed, not built"
  - id: pr132
    resource: https://github.com/luissiviero/sdlc-framework/pull/132
    title: "Change 0003's build PR: four repeated nits graded Important parked gate (e) on 2026-10-08"
generated: { by: sdlc-framework-session/pr-audit, at: 2026-10-08T16:30:00Z }
---

# The accept verb

**Status: accepted by the owner on 2026-10-08 (roadmap R6), to be built after change 0002 and R5.** Nothing is built. It needs a decision recorded before its intent, because it adds an un-park verb to decision 24.

## The problem

At gate (e) the `findings` check parks the change while any Important review finding stands (`plugin/gate/checks.py`, `check_findings`). Today the owner has two answers to a finding: a "Request changes" review that fires a fix round, or, under `review: deferred`, the panel. Under `review: parked`, this repository's setting, a finding the owner judges harmless still costs a round.

On 2026-10-08 that cost was concrete. Change 0003's review pass graded four earlier nits Important (a misreading of the second-occurrence rule, fixed in PR #133). The change parked on the iteration cap, and clearing it took a reset label, a five-item review and two fix rounds, about three hours and 14 USD, for four findings the owner would have waived in one step.

The question has been carried since session 4: "an owner `accept` verb for findings (a label or a comment that waives one Important finding without the panel) would be a new decision: proposed here, not built".

## The proposal

1. **The verb is a label**, `sdlc:accept-findings`, beside the three un-park labels of decision 24 (`plugin/state/conventions.py`, `UNPARK_LABELS`). A label carries its actor, which is what the `owner_actions` check already reads (decision 24's reason).
2. **What it accepts.** Every Important finding in `evidence/review-findings.json` for the head the label was applied on, by its `signature`. The label accepts what the owner could read, nothing newer.
3. **What the next run records.** The next run reads the label, removes it as it removes the other un-park labels, and writes each accepted signature to `status.yaml` with the actor and time, for example `findings_accepted: [{signature, by, at}]`. The commit is the runner's, like "owner labels applied".
4. **What the gate does.** `check_findings` treats an accepted signature as not blocking and says so in its reason, for example "4 Important findings accepted by luissiviero". A new Important finding with another signature still parks.
5. **What the PR shows.** The PR body's "Review findings" line lists the accepted findings under their own heading, so the record of the waiver stays visible at the merge.

## Why this shape

- **One label per head, not one per finding.** GitHub labels are per pull request. A per-finding verb would need comment parsing, which decision 24 moved away from. Binding the label to the head's findings by signature keeps it exact: it cannot accept a finding the owner has not seen.
- **Signatures already exist.** Each finding carries a `signature` (`review-findings.json`), the same key `changes/.review-seen.json` counts repeats by.
- **The panel is untouched.** Under `review: deferred` the panel still settles what it settles. The label is the owner's direct answer under either setting.

## To settle in the decision and the design

- Whether a fix round's own Important findings can be accepted by the same label, or whether the label is honoured at gate (e) only. The safer first version is gate (e) only.
- Whether accepting a finding also suppresses its `CLAUDE.md` proposal (`claude_md_first_time_lines`). The suggested answer is no: the proposal records a pattern, the waiver records one decision.
- The name: `sdlc:accept-findings`, matching `sdlc:accept-risk`.

## Version and cost

It changes `plugin/` (the label reader, `check_findings`, the PR body), so it is a plugin bump with tests: the label read and removed, the signatures recorded with the actor, the gate passing on accepted signatures and parking on a new one, and the PR body's heading. It touches nothing on the detect path's port list.
