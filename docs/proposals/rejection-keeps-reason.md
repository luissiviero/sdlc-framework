---
type: Proposal
title: A rejection keeps its reason — the owner's closing comment is saved with the change
description: When the owner closes an intent pull request without a merge, the owner's last comment on it becomes the change's abandoned_reason in status.yaml instead of the fixed "pull request N closed without a merge", the fixed text staying when there is no comment; closing still abandons (decision 25), accepting is still the merge, and an incident's closing comment stays its dismissal reason.
status: accepted
roadmap: R32
sources:
  - id: study-entry
    resource: docs/reviews/2026-09-28-playbook-vs-framework/target-design.md
    title: "T7, confirmed at the close of the study on 2026-10-09; from the crosswalk row plan-accept (better: the playbook; decision: blend), 2026-10-02"
  - id: record
    resource: docs/reviews/2026-09-28-playbook-vs-framework.md
    title: "Section 7, the close bullet and the plan-accept row; section 8 part 1 (T7's close row: amends none, suggested yes, owner yes) and part 2 (the confirmed order: T7 in 'the rest in any order')"
  - id: crosswalk
    resource: docs/reviews/2026-09-28-playbook-vs-framework/crosswalk.json
    title: "Row plan-accept (whole); the decision fields of x-audit (T32: a close is a line of the approvals list) and maintain-triage (T23: the incident's closing comment and who wrote it)"
  - id: playbook
    resource: docs/reference/ai-native-sdlc-playbook.pdf
    title: "p.6: the chain of commits is the audit trail, who asked, what was produced, who approved; p.11: the accept or reject decision recorded as the merge or the closing review; p.12: the survival rate, read from the merge or the closed review; p.47 step 4 and p.48: a dismissal with a reason"
  - id: decision-25
    resource: docs/decisions/25.md
    title: "Decision 25: closing a PR at (a)-(e) abandons the change; closing an incident intent PR also dismisses its finding (kept)"
  - id: decision-9
    resource: docs/decisions/9.md
    title: "Decision 9: the repository is the source of truth (kept; the reason is written into status.yaml)"
  - id: notes
    resource: docs/notes/14.md
    title: "Lines 90-95: a cloud session's GitHub tools act as the owner's login, and the abandon job recorded a session's closing comment as the owner's reason (run 36166179352); with docs/notes/19.md line 38, a close without a comment dismisses nothing (run 36464442652)"
  - id: code
    resource: template/.github/workflows/sdlc-abandon.yml
    title: "The abandon job's trigger, its abandon step with the fixed reason and its dismiss step; plugin/state/cli.py cmd_abandon and cmd_list; plugin/state/status.py abandoned_reason and abandon; plugin/detect/cli.py BOT_RE, TOOL_FOOTER_RE, MEMBER_ASSOCIATIONS, _closing_reason and cmd_dismiss; plugin/pr/description.py GATE_CHECKLIST; plugin/ci/run_phase.py the abandoned guard; read at main 5542406, plugin 1.0.1"
generated: { by: sdlc-framework-session/ccr-01de3f80-ilnomi, at: 2026-10-15T20:00:00Z }
---

# A rejection keeps its reason: the owner's closing comment is saved with the change

**Status: proposed (roadmap R32), from study entry T7, confirmed by the owner on 2026-10-09.** *[2026-10-20: accepted 2026-10-16 (roadmap R32, PR #215)]* Nothing is built. It amends no decision: decision 25 (closing a pull request at gates (a) to (e) abandons the change) is kept, and only what the change's record says changes. It fills the reason that R11's close line and R19's close row point to; the briefs before gate (a) that the owner's note also names belong to R28 (T1), not here.

## The problem

Closing a pull request of gates (a) to (e) without a merge abandons the change (decision 25)[^decision-25]. Every abandoned change gets the same reason, "pull request N closed without a merge", whatever the owner was thinking when they closed it. Months later the change's record says that it was rejected and never why. Only an incident change keeps a person's words: the last comment by a repository member (owner, member or collaborator) on the closed pull request becomes the dismissal's reason, in `changes/.dismissed.json`. The crosswalk row plan-accept read the two workflows as the same and said there was nothing to decide "unless you want a recorded rejection reason for ideas and tickets too"; the owner wanted it[^crosswalk].

## What the article says

The article records the product owner's decision on an intent as "the merge or the closing review" (p.11), and reads the lagging indicator, the survival rate of intents, from the same record: "the merge of the artifact or the closed review" (p.12). The chain of commits is the audit trail: "who asked for what, what the agent produced, and who approved it" (p.6). In maintain, a dismissal carries a reason "so the dismissal is recorded" (p.47 step 4), and "every dismissal has a reason, so the scan history is an audit record of what was found, fixed, and consciously accepted" (p.48)[^playbook]. A rejection with its reason is the article's record; a rejection with a fixed text is half of it.

## What the framework does today

Read at `main` 5542406, plugin 1.0.1. The entry's "Today" (recorded 2026-10-02) cites files, not lines; the rows were last re-checked at 619f01a (plugin 0.3.5). `git diff 619f01a 5542406 --stat` over `template/.github/workflows/sdlc-abandon.yml`, `plugin/state/cli.py`, `plugin/state/status.py`, `plugin/detect/cli.py`, `plugin/pr/counters.py` and `plugin/pr/github.py` is empty; it touches `plugin/ci/run_phase.py` and `plugin/pr/description.py`, whose lines cited below were re-read at 5542406. What the entry's "Today" says still holds.

- **The close.** `sdlc-abandon.yml` runs on `pull_request` `closed` (`:32-34`) when the pull request was not merged (`:50`), finds the change from the head ref `sdlc/<id>/<phase>`, or else from the pull request's files (`:77-85`; `plugin/ci/run_phase.py` `find_change`, `:748-799`) and runs `state/cli.py abandon` with `--reason "pull request $PR_NUMBER closed without a merge"` on every `sdlc/<id>/*` branch (`:87-93`). Nothing checks who closed the pull request, and no comment is read for the reason.
- **The field.** `abandoned_reason` (`plugin/state/status.py:82-83`) is set by `Status.abandon` (`:210-219`), which falls back to "pull request closed without a merge" on an empty reason and, on a second close, "changes nothing but the reason". `cmd_abandon` (`plugin/state/cli.py:303-347`) writes it on each branch and commits with the title `abandon(<id>): <reason>`, cut at 200 characters (`:326`). The reason is shown by `state/cli.py list` (`:422`) and in the skip line every workflow prints for an abandoned change (`plugin/ci/run_phase.py:979-980`).
- **The incident's rule.** The next step of the same job (`sdlc-abandon.yml:95-105`) runs `detect/cli.py dismiss`, a no-op for a change without a finding record. `_closing_reason` (`plugin/detect/cli.py:1369-1396`) takes the last comment on the pull request whose `author_association` is `OWNER`, `MEMBER` or `COLLABORATOR` (`:1366`, `:1386`), skipping a `[bot]` and the automation identity of the default branch's `sdlc.yaml` (`:1381-1385`), strips a GitHub tool's attribution footer (`TOOL_FOOTER_RE`, `:79-89`) and collapses the text to one line (`:1388-1389`); with no such comment nothing is dismissed and the change is still abandoned (`:1393-1396`; seen live, `docs/notes/19.md:38`). A reason found becomes the dismissal's reason in `changes/.dismissed.json`, on a branch whose pull request the owner merges (`cmd_dismiss`, `:1399-1500`).
- **What the owner is told.** The intent PR's "What needs you" line says "read, correct via review comments, merge = approve (gate (a))" and nothing about closing; at (f) it says "close with a comment = dismiss the finding (the comment is the recorded reason)" (`plugin/pr/description.py:96-100`).
- **Who the comment's author is.** A cloud session's GitHub tools act as the owner's login, so a session's closing comment was recorded as the owner's reason (verified, `docs/notes/14.md:90-95`, run 36166179352).

## The proposal

Added; nothing replaced. Merge to accept and close to reject stay as today (decision 25).

1. **The owner's closing comment becomes the reason.** When the owner closes an intent PR without a merge, the owner's last comment on it, if there is one, is saved as the change's `status.yaml: abandoned_reason` on every `sdlc/<id>/*` branch, instead of the fixed "pull request N closed without a merge". Example: the intent PR for "Export as CSV" is closed with "Not needed, the PDF export covers it", and that sentence is what the change's record says months later.
2. **The comment is optional.** With no comment the fixed text stays, so a close costs the owner nothing when there is nothing to say.
3. **Incidents keep today's rule.** On an incident PR the closing comment also stays the dismissal reason, read by `_closing_reason` as today (the crosswalk row maintain-triage, T23, keeps the member rule for the dismissal's reason).
4. **Accepting stays the merge** (decision 25). T1's Product and Architect briefs and the manager's recommendation come before it; they arrive with R28 (T1), not here.
5. **What belongs elsewhere.** The closer, the time and the pull request belong to R11's close line (the approvals list names "a close (T7)"), and the act's wording on the PR to R19's block, whose (a) row already reads "close with a comment = abandon; the comment is kept as the reason (T7; today a fixed text)".

## How it is judged

On the next intent PRs the owner closes on the sample: closed with a comment, every `sdlc/<id>/*` branch's `status.yaml` reads the owner's sentence as `abandoned_reason`, and `state/cli.py list` shows it; closed with no comment that counts under the rules chosen below, the fixed text, as today; an incident PR closed with a comment is dismissed with that comment, as today. A reason taken from a bot, the automation identity or a comment the rule chosen below does not count, or a close that no longer abandons, is the failure. Measured before and after: the share of abandoned changes whose reason is in words, none today.

## What to settle before building

| Question | Recommended |
|---|---|
| Whether the same applies when the owner closes a PR of gates (b) to (e), which abandons the change the same way (the entry's open item) | Recommended (mine): yes. The same step of `sdlc-abandon.yml` abandons at every gate (`:87-93`), so one rule costs nothing more, and R11's settle table (R11 accepted on 2026-10-13) recommends a close line at (b) to (e), "with T7's open item on which closing comments count" |
| Which comments count: the owner's own, as T1 asks of approvals, or any repository member's, as the incident rule reads today (the entry's open item) | Recommended (mine): the owner's own account's last comment, as the owner's note says ("my last comment"); how the owner is known is **settled by R17** (accepted on 2026-10-14, point 3): the repository owner by default, `sdlc.yaml: owner` on an organization repository, one shared `is_owner_actor`, fail closed. A member's or collaborator's comment leaves the fixed text. The incident's dismissal reason keeps today's member rule (the owner's note; T23). A cloud session acting as the owner's login passes as the owner (`docs/notes/14.md:90-95`), a limit every owner check shares |
| Which comment is "the last" when the owner closes without writing a new one (mine) | `_closing_reason` takes the last qualifying comment whenever it was written (`plugin/detect/cli.py:1380-1391`, `issue_comments` reads every comment, oldest first, `plugin/pr/github.py:455`), so a close with no new comment would record an older one: an early question on the intent PR, or an `@claude` comment once R17 is built (a conversation comment by the owner's account, R17 point 1). Options: any age, as the note's "my last comment on it" reads; skip a comment whose body starts with `@claude`; only a comment written within N minutes before `closed_at`. Recommended (mine): any age, skipping `@claude` comments, which ask for a fix round and give no reason. The incident's dismissal reason keeps today's any-age rule (the owner's note: "Incidents keep today's rule") |
| How the comment reaches the step (mine) | The Python step reads it through `pr/github.py` `issue_comments`, with the default branch's `sdlc.yaml` for the automation identity, as `dismiss` does; the text never passes through a `${{ }}` expression or a `run:` line (`plugin/skills/security-baseline/SKILL.md:21-22`, rule 2: no shell command built from external data). `_closing_reason` becomes one shared function with the owner-only filter as a parameter, rather than a second copy, keeping its other rules (no `[bot]`, no automation identity, the tool footer stripped, one line); nothing else in the abandon job changes |
| The reason's shape and the commit (mine) | `abandoned_reason` holds the comment alone, in place of the fixed text, as the owner's note says ("instead of the fixed 'pull request N closed without a merge'"), footer stripped and collapsed to one line; the abandon commit's title gains the pull request's number (`abandon(<id>): #N: <reason>`, still cut at 200 characters), so the record names the pull request before R11's line exists |
| A comment written after the close (mine) | Not read: the job reads the comments when it starts. Reopening and closing again rewrites the reason: the code re-marks a change already abandoned, since the find step reads no status (`run_phase.py:154`, `fix` has no previous phase), `cmd_abandon` refuses no abandoned change (`state/cli.py:193-199`, `:318-322`) and `Status.abandon` sets a different reason (`status.py:214-218`); only whether GitHub fires `pull_request` `closed` again after a reopen is to verify on the sample |
| Whether a reason reaches the digest or a counter (mine) | No line of its own: the digest's lines are R20's, the measures R26's, and T31 records the survival rate of intents as not computed |

## Considered and not chosen

- **Today's fixed text alone** (the row read as "same", nothing to decide): the owner wanted a recorded rejection reason for ideas and tickets too.
- **A required reason**, the article's "closing review" as a mandatory act: the entry keeps the comment optional, so a close with nothing to say costs nothing.
- **Replacing the close as the rejection act**: decision 25 is kept; the entry adds and replaces nothing.

## Decisions it touches

None amended. 25 is kept: close abandons at (a) to (e), and an incident close also dismisses, with the comment as the reason; only the text of `abandoned_reason` changes. 9 is kept: the reason lives in the repository, in `status.yaml`. 5 is read (the automation identity's comments never count) and 22 is read (who may start a fix round is `sdlc-fix.yml`'s member rule, its narrowing of decision 22's "the owner's" review (0.2.21), and whose words reach a round is `ci/fix_requests.py`'s own member rule (0.2.23); neither is this proposal's rule; R17 point 3). 20 and 11 are kept: nothing notifies the owner of a close. No decision file is needed.

## Order

In the study's "rest in any order" group (the record, section 8 part 2: T3, T5, T6, T7, T8, T11, ...); the Order column is the owner's. It depends on no other proposal to be built; R17's `@claude` comments, once built, are comments it must skip, if the row above is chosen as recommended. It shares two pieces with others, whichever is built first adding them: `is_owner_actor` (R17, point 3), if the owner-only rule above is chosen, and the comment-reading function the incident's dismissal uses today (`_closing_reason`), whose author R23 (T23) checks against the owner when the dismissal is merged for them (the crosswalk row maintain-triage). It ships as a plugin version with tests and reaches a project through `/sdlc-init`'s workflow copies. The parts it takes:

| Part | Where | When |
|---|---|---|
| The reason from the closing comment, the fixed text without one, the number in the commit title | `plugin/state/cli.py` `cmd_abandon`, the shared comment function (from `plugin/detect/cli.py`), `template/.github/workflows/sdlc-abandon.yml`, tests | Now, one change |
| The closer, the time and the pull request on the close line | R11, the approvals list | With R11 |
| The close row of the PR's "What you can do here" block | R19 | With R19 |
| The Product and Architect briefs and the manager's recommendation before gate (a) | R28 (T1) | With R28 |

[^decision-25]: `docs/decisions/25.md`.
[^crosswalk]: `docs/reviews/2026-09-28-playbook-vs-framework/crosswalk.json`, row plan-accept (`weigh` and `decision`), and `target-design.md` T7.
[^playbook]: `docs/reference/ai-native-sdlc-playbook.pdf` p.6, p.11-12, p.47-48.
