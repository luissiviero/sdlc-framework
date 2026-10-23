---
type: Proposal
title: Triage — a dismissal is one act, the band change has its number, a scheduled incident says what it mutes
description: Decision 25's three verbs at gate (f) stay; when the owner's own account closes an incident PR and wrote the closing comment, a deterministic workflow checks it and R22's GitHub App merges the dismissal PR, so a dismissal costs one act; the dismissal PR's body states the min_sigma or direction that would have kept the latest point inside the rule that fired; a scheduled incident keeps muting its metric and the digest's Detection line says so.
status: accepted
roadmap: R23
sources:
  - id: study-entry
    resource: docs/reviews/2026-09-28-playbook-vs-framework/target-design.md
    title: "T23, confirmed at the close of the study on 2026-10-09; from the crosswalk row maintain-triage (better: both; decision: blend, option B), 2026-10-07"
  - id: crosswalk
    resource: docs/reviews/2026-09-28-playbook-vs-framework/crosswalk.json
    title: "Row maintain-triage (whole); the decision fields of deploy-approve (T18), maintain-detect (T22), maintain-scan (T26), plan-accept (T7), x-queue (T28), x-audit (T32) and x-roles (T1)"
  - id: playbook
    resource: docs/reference/ai-native-sdlc-playbook.pdf
    title: "p.44 step 6: triage, fix now, schedule or dismiss, dismissals tune the bands; p.44-45: triage decisions logged with a timestamp, changes through the normal PR review gate; p.47 step 4: dismiss with a reason; p.40: the agent has no route to push to main"
  - id: decision-4
    resource: docs/decisions/4.md
    title: "Decision 4: only the owner's account merges to main, the automation identity has branch-only write access (amended here in R22's direction)"
  - id: decision-25
    resource: docs/decisions/25.md
    title: "Decision 25: gate (f) is per-finding triage; closing an incident PR dismisses and abandons (kept)"
  - id: decision-20
    resource: docs/decisions/20.md
    title: "Decision 20: a review queue and a daily digest, nothing pushes to the owner (kept)"
  - id: r17
    resource: docs/proposals/claude-comment-fix-round.md
    title: "R17 (T17), accepted on 2026-10-14: how the owner's account is known, one shared function for T1, T18, T23 and T24"
  - id: code
    resource: plugin/detect/cli.py
    title: "open_incidents, _dismissal_rejected, _with_pending_dismissals, cmd_run, _closing_reason, cmd_dismiss; with plugin/detect/dismissals.py, plugin/detect/stats.py, plugin/detect/finding.py, plugin/scan/cli.py cmd_route, plugin/pr/digest.py, template/.github/workflows/sdlc-abandon.yml, template/bands.yaml; read at main 5542406, plugin 1.0.1"
generated: { by: sdlc-framework-session/ccr-01de3f80-ilnomi, at: 2026-10-15T20:00:00Z }
---

# Triage: a dismissal is one act, the band change has its number, a scheduled incident says what it mutes

**Status: proposed (roadmap R23), from study entry T23, confirmed by the owner on 2026-10-09, option B of the crosswalk row maintain-triage (the letters are that row's own).** *[2026-10-20: accepted 2026-10-16 (PR #215); rank 31; the rank is read from ROADMAP's Order column]* Nothing is built. It amends decision 4 in the direction R22 (T18) amends it: a second actor, R22's GitHub App, may merge a dismissal PR, only on the owner's own close. The decision file comes before the intent, in a documentation PR of its own; this proposal writes no decision file and reserves no number. One recommendation of its own departs from the owner's confirmed notes and waits for the owner's answer: that the dismissal reason skip an `@claude` comment, where T7's note and this entry's correction keep today's rule (What to settle before building). Second of the gate changes in the confirmed order (T18, T23, T9, T30, T31), after R22, whose App, merge workflow and `sdlc/review` check it uses.

## The problem

Decision 25 made gate (f) the owner's triage of each incident intent PR: merge to fix now, the `schedule` label for later, close with a comment to dismiss[^decision-25]. Three things cost the owner more than they should, or say less:

- **A dismissal costs two acts.** The close with a comment writes the dismissal on a branch and opens a dismissal PR; the owner then has to find that PR and merge it. The crosswalk row's own question was whether this second merge is worth its friction; the row's correction is that it is bookkeeping, not the mute (below).
- **"Dismissals tune the bands" is a mute in the framework.** A dismissal mutes the metric-and-rule pair for one baseline window; the band changes only through the owner's `bands.yaml` PR, and nothing computes what to change. A dismissal that should tune the band leaves the owner to work the number out.
- **A scheduled incident mutes its metric silently.** An open incident mutes every later finding on its metric for as long as it stays open, with no expiry and no line saying so.

## What the article says

"The service owner or on-call engineer triages the queue, routing product-facing findings to the product owner. Fix now, schedule, or dismiss. Dismissals tune the bands and help to reduce noise" (p.44 step 6)[^playbook]. "Invocations, findings and triage decisions are logged with a timestamp. A service owner triages and approves findings, resulting changes go through the normal PR review gate" (p.44-45). For scans: "Dismiss with a reason, so the dismissal is recorded and the same finding does not return as new on the next run" (p.47 step 4). And "the agent has no route to push to main" (p.40), decision 4's ground. Routing to a product owner has no counterpart: the owner is both (the owner's note).

## What the framework does today

Read at `main` 5542406, plugin 1.0.1. The entry's "Today" names no commit; the crosswalk completed the maintain-triage text at `main` cc96151, plugin 0.3.5, whose plugin and template are those of 619f01a (the five commits after it touch `docs/reviews` only). `git diff 619f01a 5542406 --stat` over `plugin/detect`, `plugin/scan`, `plugin/pr/digest.py`, `plugin/state/unpark.py`, `plugin/state/conventions.py`, `plugin/gate/policy.py`, `template/bands.yaml` and the abandon, scan, detect and design workflows is empty. `plugin/ci/run_phase.py` did change (271 insertions, 33 deletions), but `PHASE_BEFORE` still reads `{"b": ("a", "f")}` (`run_phase.py:155` at 5542406, the same line at 619f01a). So every line the entry cites still holds.

- **The three verbs.** The merge of the incident PR is gate (a) of the incident change: `sdlc-design.yml` fires on a merged PR (`template/.github/workflows/sdlc-design.yml:31`, `:59`) and the design run accepts a change at `f` as at `a` (`plugin/ci/run_phase.py:155`, `PHASE_BEFORE`). `schedule` is a label that stops and starts nothing (`plugin/state/conventions.py:86-92`); the digest shows it since D11's fix (`plugin/pr/digest.py:6-8`, the live run of 2026-09-25), in 0.2.23 (`docs/OPERATING_MODEL.md` §4.2, the `sdlc-digest.yml` row). A close without a merge fires `sdlc-abandon.yml` (`:34`, `:50`), which abandons the change on its branches (`:93`) and runs `detect/cli.py dismiss --open-pr` (`:97-105`).
- **Whose comment is the reason.** `_closing_reason` (`plugin/detect/cli.py:1369-1396`) takes the last comment whose `author_association` is `OWNER`, `MEMBER` or `COLLABORATOR` (`:1366`), never a bot or the automation identity, with a GitHub tool's footer stripped; with no such comment nothing is dismissed (`:1395`) and the change is still abandoned. Nothing checks who closed the PR.
- **The dismissal PR.** `cmd_dismiss` (`:1399-1498`) writes the entry to `changes/.dismissed.json` on `sdlc/<id>/dismiss` (`:71`, `:1452-1455`), a detection entry with `until` one baseline window ahead (`:1423`; `plugin/detect/dismissals.py:15-20`), and opens a PR against the default branch with the workflow token (`:1476`), labelled `incident` (`:1488`). Its body already says "widen the band in bands.yaml if the noise is the band's, p.44 step 6" (`:1468-1470`), with no number. The digest lists it under "runbook and dismissal PRs" (`digest.py:71-75`, `:166-168`). The automation identity never writes to the default branch (`dismissals.py:6-8`); no GitHub App is in any template workflow and no function names the owner's account (`git grep` at 5542406: only `is_automation` in `plugin/gate/policy.py:53` and `is_automation_actor` in `plugin/state/unpark.py:59` and `plugin/release/approval.py:116`).
- **The second merge is not the mute.** For a detection finding, `cmd_run` reads the store plus every pending `origin/sdlc/<id>/dismiss` branch (`detect/cli.py:614-616`, `_with_pending_dismissals`, `:378-414`), unless that branch's PR was closed without a merge or none was opened (`_dismissal_rejected`, `:355-375`): the mute holds from the close. For a scan finding, `scan/cli.py route` reads only the checkout's store (`plugin/scan/cli.py:234`), and the scan workflow checks out the default branch on Mondays (`template/.github/workflows/sdlc-scan.yml:38`, `:56`): a dismissed scan finding returns the next Monday until the owner merges.
- **The band.** `template/bands.yaml:41-43`: "widen a band before muting a metric"; a dismissal mutes the metric-and-rule pair (the signature is `detect|<metric>|<rule>`, `plugin/detect/finding.py:6-7`, `:35-37`) for one window. The detection record keeps what a computation needs: `mean`, `sigma` (already floored at `min_sigma`), `latest`, `rule`, `rules_hit`, `direction`, `window_days` and the tail's last eight observations (`finding.py:54-80`). The rules (`plugin/detect/stats.py:34-39`): `we1` the latest point beyond 3 sigma, `we2` two of three beyond 2 sigma with the latest among them, `we3` four of five beyond 1 sigma, `we4` eight points on one side of the mean; sigma is the baseline's sample deviation floored at `min_sigma` (`:255`). Only tier 2 and above files an incident (`detect/cli.py:614`), so `we3` (tier 1) never reaches a dismissal.
- **A scheduled incident.** `open_incidents` (`detect/cli.py:291-353`) counts any filed, unabandoned, unshipped incident change of the metric; while one is open the next breach is logged as "open incident … already carries" the metric and nothing is filed (`:626-628`). No expiry, and no digest line names it.

## The proposal

Decision 25's three verbs stay: merge is gate (a) of the incident change, `schedule` is a label that stops nothing and starts nothing, close with a comment abandons the change and runs the dismissal. On the incident PR, R28's (T1) Operations brief (Security & policy for a scan finding) and the manager's recommendation, fix now, schedule or dismiss, as the row's Target already says; they arrive with R28, not here. Added, as the owner's note says:

1. **The dismissal PR merged on the owner's own close.** When the close and the closing comment are the owner's own account's, a deterministic workflow, no model, checks that, as R22's merge workflow checks the approval, and R22's GitHub App merges the dismissal PR, so a dismissal is one act, from the phone too. A comment by a member or a collaborator still opens the PR for the owner's merge, as today. The store entry is unchanged: the reason, the author and the date in `changes/.dismissed.json` on the default branch; the record now has the App's merge as the second line. R11's approvals list carries a dismissal (T23) as an act with its actor; this proposal adds the App's merge of the dismissal PR beside it, with its actor, the App, an act R11 does not list yet. The automation identity still writes nothing to the default branch.
2. **The band change has its number.** The dismissal PR's body states, computed from the detection record (the baseline's mean and sigma, the latest point, the rule that fired), the `min_sigma` or `direction` value that would have kept the latest point inside that rule, so the owner's `bands.yaml` PR starts from a number when a dismissal should tune the band rather than mute it. `bands.yaml` stays the owner's file. A scan finding has no band and no line.
3. **A scheduled incident says what it mutes.** A scheduled incident keeps muting its metric while it is open (one incident per metric keeps the queue quiet, p.44 step 6), and T22's Detection line (R40) in the digest says so: "muted by #n, scheduled since <date>".

The row's corrections are part of the decision and are what the code above does: the reason is the last comment by an `OWNER`, `MEMBER` or `COLLABORATOR`, never a bot or the automation identity, and with no such comment nothing is dismissed while the change is still abandoned; the second merge is bookkeeping, not the mute (a detection finding muted from the close by the pending branch, unless its PR is closed without a merge; a scan finding only once the PR is merged); the dismissal PRs are listed in the digest; "dismissals tune the bands" is a one-window mute of the metric-and-rule pair, and nothing computes a band change; "product-facing findings to the product owner" has no counterpart.

## How it is judged

On the next dismissals on the sample: each detection or scan dismissal the owner makes by closing with a comment is merged by the App with no second act, and its line in R11's list names the close and the App's merge; a member's or collaborator's closing comment leaves the PR open for the owner, listed in the digest. A dismissal PR merged by the App on any close or comment that is not the owner's own is the failure. Each detection dismissal PR's body carries the number, and a test confirms it: the rules `we1`, `we2` and `we4` re-run over the record's eight tail observations against the recorded mean, with sigma = max(recorded sigma, the number), give no tier-2 or tier-3 rule. A plain re-run of the detection over the record cannot be that test: the record keeps only the tail (`plugin/detect/finding.py:28`, `:76`), so `stats.evaluate` finds no baseline and returns tier 0 whatever the band (`plugin/detect/stats.py:16-20`, `:248-252`); the test needs a helper in `stats.py` that takes a given mean and sigma. While an incident is scheduled, the digest's Detection line names it. Measured before and after: the owner's acts per dismissal, two today (the close with a comment, the merge), one after.

## What to settle before building

| Question | Recommended |
|---|---|
| How the workflow knows the owner's account (the entry: shared with T1, T17 and T24; R17 adds T18: shared with R28 (T1), R17 (T17), R22 (T18) and R41 (T24)) | **Settled by R17** (accepted on 2026-10-14, point 3): the repository owner by default, `sdlc.yaml: owner` for an organization repository, one shared function `is_owner_actor`, fail closed. Here it is applied to the close's actor and to the author of the comment `_closing_reason` returns; both must pass |
| Whether a comment by a member or a collaborator should still dismiss at all | The entry lists it as open; the owner's note already answers it: "a collaborator's or member's comment still opens the PR for my merge". Recommended: as the note says (it still writes the dismissal and opens the PR, for the owner's merge), the owner confirming the closure when this proposal is reviewed |
| Whether the dismissal reason skips a comment that starts with `@claude` (not in the entry; mine) | R17 (accepted on 2026-10-14, point 1) lets the owner's `@claude` comment start a fix round on an incident PR too, and `_closing_reason` takes the last qualifying comment whenever it was written (`plugin/detect/cli.py:1380-1391` at 5542406), so a close with no new comment would record a fix request as the dismissal's reason and, under point 1, have the App merge it. The owner's confirmed notes fix the incident's rule: T7's "Incidents keep today's rule (my comment becomes the dismissal reason)" and this entry's correction "the reason is the last comment by an OWNER, MEMBER or COLLABORATOR". R32 (T7, proposed, not accepted) *[2026-10-20: R32 (T7, accepted 2026-10-16)]* recommends skipping `@claude` comments for a close's reason and, citing T7's note, leaves the incident's reason to today's any-age rule (`docs/proposals/rejection-keeps-reason.md:77`). Recommended (mine), a departure from both notes that is the owner's to accept or reject when this proposal is reviewed: the dismissal reason skips a comment whose body starts with `@claude`, through the comment-reading function R32 and this proposal share, whichever is built first adding the skip, so a fix request never becomes a dismissal reason; the member rule is otherwise unchanged. If the owner keeps the notes as written, a close with no new comment after an `@claude` comment records the fix request as the reason, and the owner's own close has the App merge it |
| Whether the App's merge needs R22's passing `sdlc/review` check, and which step posts it | **Partly settled by the deploy-approve note (T18, R22):** every PR that is not a build PR gets a passing "not a build PR" `sdlc/review`, posted by the step that opens or updates an automation PR, the dismissal step among them. Recommended (mine): the dismiss step posts it on the dismissal PR's head before the merge is attempted, and the App merges only that head |
| Where the owner check and the App's key run (not in the entry; mine) | The App's key out of reach of a workflow file a PR branch can change, as R22 requires: `sdlc-abandon.yml` runs on `pull_request` `closed`, whose workflow file is recorded as the head's (`docs/notes/16.md`, not verified; `docs/OPERATING_MODEL.md` §4.2), so the key cannot sit in it. Recommended: the abandon job dispatches R22's merge workflow (a `workflow_dispatch` the workflow token may start) with the incident and dismissal PR numbers, which needs `actions: write` the abandon job lacks today (`template/.github/workflows/sdlc-abandon.yml:37-39` at 5542406); that run, on the default branch's file, re-reads the close's actor and the reason's author from GitHub and merges, or leaves the PR for the owner and says why in its log |
| The exact computation of the band number for each rule, and its wording | Recommended (mine), with sigma = max(recorded sigma, X) and the rules re-run over the record's tail to confirm no tier-2 rule then fires: `we1`, `min_sigma` above abs(latest − mean) / 3; `we2`, above abs(latest − mean) / 2; `we3` never reaches a dismissal (tier 1); `we4` does not depend on sigma, so no `min_sigma` keeps it inside: the line names the `direction` that would (only where the direction is `both`) or says no band value does and the window carries the shift. Wording: "To keep this point inside `<rule>`, `bands.yaml` would need `min_sigma: <X>` (today <current>)", rounded up |
| Whether the scan's route should also honour a pending dismissal branch | Recommended (mine): yes, through the same `_with_pending_dismissals` and its rejection rule, a small change in `plugin/scan/cli.py`, so the mute holds from the close for both kinds; with point 1 it matters only for a member's or collaborator's dismissal, which waits for the owner's merge |
| Whether a scheduled incident should expire, or only be shown | The entry lists it as open; the owner's note, point 3, already answers it: "a scheduled incident keeps muting its metric while it is open". Recommended: as the note says (no expiry; shown in R40's (T22) Detection line), the owner confirming the closure when this proposal is reviewed |
| Whether a `schedule`-labelled incident PR stays in R20's "Needs you" (sorted last, its label shown) or leaves it and appears only on R40's (T22) Detection line (handed over by R20, accepted 2026-10-14, `docs/proposals/digest-needs-you-first.md:113`; not in the entry) | Recommended (mine): it leaves "Needs you" and appears only on the Detection line, which names it ("muted by #n, scheduled since <date>"), so the owner can still open it: the `schedule` label is the owner's own "not now", already given, and kept in "Needs you" it would stand there for good |
| Whether decision 4's amendment is one file with R22's | Recommended (mine): one decision file naming both acts (the (e) merge on the owner's approval, the dismissal merge on the owner's own close) if R22 and R23 are accepted together; otherwise a file of its own before R23's intent |

## Considered and not chosen

- **A, the text corrected only.** The row's corrections without the three additions.
- **C, a run that proposes the `bands.yaml` PR itself** from the computed number: an automated edit of an owner's file and the owner's merge each time, the objection that set aside T20's (R39) standing `rehearsed_at` PR.

## Decisions it touches

4 is amended in R22's direction: R22's App may merge a dismissal PR, only when the close and the closing comment are the owner's own account's, checked by a deterministic workflow; the automation identity still writes nothing to the default branch. A decision file before the intent, in a documentation PR of its own; no number reserved here. 25 is kept (the three verbs; close abandons and dismisses). 20 is kept (the lines go to the digest; nothing notifies). 5 is amended by R22 (T18), not here; this proposal uses the App R22 introduces. *[2026-10-20: 5 is amended by decision 33 (`docs/decisions/33.md`, accepted: the App pushes and opens PRs); the App's merge stays R22's to settle]*

## Order

Second of the gate changes in the confirmed order (the record, section 8: T18, T23, T9, T30, T31). It changes `template/` and `plugin/`, so it ships as a plugin version with tests and reaches a project through `/sdlc-init`'s workflow copies. The parts it takes:

| Part | Where | When |
|---|---|---|
| Decision 4's amendment | `docs/decisions/` | Before the intent, with R22's or on its own |
| The owner check and the App's merge of the dismissal PR | `sdlc-abandon.yml`, R22's merge workflow, `plugin/detect/cli.py` `cmd_dismiss` | After R22 (the App, its key, the merge workflow, `sdlc/review` on non-build PRs) and R17 (`is_owner_actor`) |
| The band number in the dismissal PR's body | `plugin/detect/cli.py` `cmd_dismiss`, `plugin/detect/stats.py` | Independent of R22; can ship first |
| The scan route honouring a pending dismissal (if accepted) | `plugin/scan/cli.py` `cmd_route` | Independent |
| The scheduled incident's mute in the Detection line | T22's Detection line (R40), placed by R20 | With R40 |
| The dismissal (R11 lists it) and the App's merge of the dismissal PR (added here) recorded | R11's approvals list | With R11 |
| The act in the PR's block ("merged for you when the close is yours") | R19 | With R19 |
| The Operations brief and the manager's recommendation on the incident PR | R28 (T1); a scan dismissal's validation with R43 (T26) | With those |

[^decision-25]: `docs/decisions/25.md`.
[^playbook]: `docs/reference/ai-native-sdlc-playbook.pdf` p.40, p.44-45, p.47.
