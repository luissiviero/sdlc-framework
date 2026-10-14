---
type: Proposal
title: The owner's @claude comment starts a fix round, beside the "Request changes" review
description: A pull request comment by the owner that starts with @claude starts the same fix round as the owner's "Request changes" review, with every unresolved comment as a constraint; a small workflow with no model checks the comment is the owner's and dispatches sdlc-fix.yml as the owner does by hand today; the comment is a trigger and never a verb, its text is read as data, and the round shares decision 29's one iteration counter.
status: proposed
roadmap: R17
sources:
  - id: study-entry
    resource: docs/reviews/2026-09-28-playbook-vs-framework/target-design.md
    title: "T17, confirmed at the close of the study on 2026-10-09; from the crosswalk row deploy-comments (better: the framework; decision: blend), 2026-10-06"
  - id: crosswalk
    resource: docs/reviews/2026-09-28-playbook-vs-framework/crosswalk.json
    title: "Row deploy-comments whole; the decision fields of test-loop (T10), deploy-review (T14) and maintain-tag (the incident PR thread is the channel)"
  - id: playbook
    resource: docs/reference/ai-native-sdlc-playbook.pdf
    title: "p.33 step 4: a reviewer or the author tags @claude on a review comment and Claude addresses it and pushes; p.34: for PRs Claude opened, a slash command babysits the PR until it is green"
  - id: decision-22
    resource: docs/decisions/22.md
    title: "Decision 22: the owner's \"Request changes\" review starts the fix run (the decision this amends, one trigger added)"
  - id: decision-29
    resource: docs/decisions/29.md
    title: "Decision 29: the runner dispatches the next fix round itself; one iteration counter with T30's one reset at the cap"
  - id: code
    resource: template/.github/workflows/sdlc-fix.yml
    title: "The fix workflow's triggers and job condition; plugin/ci/fix_requests.py (whose words reach the round); plugin/ci/run_phase.py dispatch_head and dispatch; plugin/pr/github.py issue_comments; read at main acefc7e, plugin 1.0.0"
generated: { by: sdlc-framework-session/ccr-20b39ad0-kcymdd, at: 2026-10-14T15:30:00Z }
---

# The owner's @claude comment starts a fix round, beside the "Request changes" review

**Status: proposed (roadmap R17), from study entry T17, confirmed by the owner on 2026-10-09.** Nothing is built. It amends decision 22: one trigger added beside the "Request changes" review, its substance unchanged. The decision file comes before the intent, in a documentation PR the owner reviews on its own, never with the intent; this proposal writes no decision file and reserves no number. The round's record is R11's point 3; the act it adds is listed in R19's "What you can do here" block.

## The problem

Decision 22 made the owner's "Request changes" review the act that starts a fix round, so applying the owner's change requests is no longer a step the owner runs by hand[^decision-22]. Two gaps remain:

- **GitHub refuses "Request changes" on the reviewer's own pull request** (verified on PR #90 of this repository, `docs/notes/29.md`). Every intent PR the owner opens by hand is such a PR. There the owner writes a comment review and then a `workflow_dispatch` of `sdlc-fix.yml` with the change id and the head branch (`plugin/commands/sdlc-fix.md:55-59`): two acts in two places, the second in the Actions tab. Decision 24's reason was the opposite: the owner's input lives in the PR, not in a terminal.
- **No workflow runs on a comment** (`sdlc-fix.yml:41-54`). The article's loop is a comment: tag `@claude`, Claude addresses it and pushes (p.33)[^playbook].

A third point rides along. A round is started today by any member or collaborator who requests changes (`sdlc-fix.yml:76-83`), and the Go by any person who is not a bot (`plugin/detect/cli.py:1139-1148`). R12 deferred "who may apply the label" to T17, T18 and T24; the owner's note at deploy-comments asks that the comment count "from my account (not just any person)".

## What the article says

"When a reviewer or the author tags @claude on a review comment, Claude addresses the comment and pushes the fix. The PR thread records both the request and the change" (p.33 step 4). For PRs Claude opened, "let Claude babysit the PR to merge": a slash command sweeps the unresolved comments and failing checks "until the PR is green and waiting only on code owner approval" (p.34)[^playbook]. In the managed service "@claude review" requests a fresh review instead. The article's trigger is per comment and open to any reviewer; the framework's is one round per act, by the owner.

## What the framework does today

Read at `main` acefc7e, plugin 1.0.0. The entry's "Today" was read at 619f01a (0.3.5). `git diff 619f01a acefc7e --stat -- plugin/ci plugin/pr plugin/release template/.github/workflows` touches `plugin/ci/run_phase.py` (279 lines), `plugin/ci/settings.ci.json`, `plugin/pr/description.py` and `plugin/release/notes.py` only; `sdlc-fix.yml`, `fix_requests.py`, `pr/github.py`, `sdlc-fix.md`, `detect/cli.py`, `gate/policy.py` and `state/unpark.py` have an empty diff over that range, so every line the entry cites still holds[^crosswalk].

- **The triggers and the job condition.** `sdlc-fix.yml` runs on a `workflow_dispatch` (`change_id` required, `head_ref` optional), a `pull_request_review` `submitted` and a `pull_request` `labeled` (lines 41-54). Its `if:` (76-89) takes a dispatch, a review with state `changes_requested` by a non-`[bot]` whose `author_association` is `OWNER`, `MEMBER` or `COLLABORATOR`, or an un-park label. The job holds five write scopes (56-61) and no deploy secret.
- **Two layers.** The `if:` decides who starts a round; `plugin/ci/fix_requests.py` decides whose words reach it (lines 5-7): it reads every review, review thread (with its resolved flag) and PR comment through `pr/github.py` (`collect`, 137-161), keeps those by a member that is neither a `[bot]` nor the automation identity (`why_not`, 63-74) and lists the rest without their text. `/sdlc-fix` step 1 reads that file only (`sdlc-fix.md:59-63`); on a runner a failed collection parks (`run_phase.py:1651-1658`). The text never enters a `run:` line (`plugin/skills/security-baseline/SKILL.md:21-22`, rule 2); the round never posts a comment, reply or review (`sdlc-fix.md:203-207`; decision 20).
- **Everything is keyed on `github.event.pull_request.*`:** the concurrency group (`sdlc-fix.yml:66`), the checkout ref (99), `HEAD_REF` (125, 158), `PR_NUMBER` (127, 160). A PR conversation comment arrives as `issue_comment`, whose payload carries `issue.number` and no `pull_request.head.ref`; the head would come from the API.
- **The by-hand route, and what 0.3.6 added.** A dispatched round with no `head_ref` finds its head through `dispatch_head` (`run_phase.py:495-543`, PR #130): the PR named by `--pr-number`, else the open PR of the checkout's branch, only when that PR's files carry the change's folder. A dispatched round reads the un-park labels and collects the requests from the head's open PR (2030-2062, 2489-2533). The runner's own dispatch is `POST .../workflows/{file}/dispatches` with `change_id` and `head_ref` (`dispatch`, 1550-1569), the one event the workflow token may cause that starts a run (`docs/notes/11.md:56-63`).
- **Decision 29 (accepted 2026-10-13, R10 not built):** a red target will dispatch the next round through that same `workflow_dispatch`; the automatic rounds share the one iteration counter (`plugin/gate/limits.py:5`, 69-75; `gate/cli.py` `bump-iteration`, 172-196) with T30's one reset at the cap[^decision-29].
- **Three actor checks, none "the owner".** `gate/policy.py` `is_automation` (53-61) compares a commit author with `sdlc.yaml: automation_identity` (default `github-actions[bot]`, `template/sdlc.yaml:120-127`); `state/unpark.py` `is_automation_actor` (59-65) rejects that identity and any `[bot]`; `detect/cli.py` `_human_label_actor` (1139-1148) applies both to the Go. No key in `sdlc.yaml` names the owner.
- **The install step reads the head.** `sdlc-fix.yml:149` runs `project_setup.py --root .` with no `--ref`, so `commands.setup` comes from the head's `sdlc.yaml` (`project_setup.py:16`; the runbook job passes `refs/remotes/origin/<default>`), before the runner's guardrail park (`run_phase.py:1620-1627`). Whoever may start a round may run a head's setup command on the runner.
- **PR comments have no resolved state.** `issue_comments` (`github.py:455-498`) shapes `id`, `author`, `type`, `association`, `body`, `created_at`, `url`; `partition` judges a PR comment by its author alone (`fix_requests.py:132-133`) while a resolved thread's comments are dropped (121-131). Each round rewrites `fix-requests.json` with `head` and `collected_at` (184-191) and re-reads every PR comment.
- **No note covers `issue_comment` runs** (`grep -rn issue_comment docs/notes/` finds nothing): which workflow file such a run uses, its token on a PR from a fork, and whether `needs` reaches a job-level `concurrency` key are to verify.

## The proposal

Decision 22's round stays as it is; what changes is one more way to start it, and who may.

1. **The trigger.** A comment in a pull request's conversation (`issue_comment` `created`, on an issue that is a pull request) whose body starts with `@claude`, by the owner's account, starts the same fix round as the owner's "Request changes" review, on an intent, design, build or incident PR alike (the (f) round of the row maintain-tag included). Only `created` counts: editing a comment to add `@claude` starts nothing, so one comment is one round. A line comment is never a trigger: where GitHub allows a review, "Request changes" is the act; on the owner's own PR the owner submits the line comments as a comment review and adds one `@claude` comment, and the round reads them all through the threads as today.
2. **The comment dispatches the round.** A small workflow, `sdlc-comment.yml`, no model and no checkout of the change, runs on `issue_comment`. Its `if:` tests the event (a pull request, body `startsWith` `@claude`, author not a `[bot]`, `author_association == 'OWNER'`). One Python step reads the PR through the API (`pr_by_number`: head, head repository, files), finds the change as `find_change` does (`run_phase.py:747-797`), refuses a head in another repository or a PR with no change folder (a green skip with its reason), and dispatches `sdlc-fix.yml` with `change_id`, `head_ref` and a new optional input `trigger`, the comment's link. This is the by-hand `workflow_dispatch` made automatic, so "no more manual dispatch" is literal and the round's path does not change: the group keys on `inputs.head_ref`, the head is checked out, the labels are performed, the requests are collected from the head's open PR, and the `@claude` comment is one of them (a PR comment by an `OWNER`). The dispatcher holds `actions: write` and read scopes; the comment's text reaches it inside the `if:` expression only.
3. **Who starts a round: the owner's account, on both paths.** The "Request changes" path becomes owner-only too: decision 22's own wording is "the owner's" review, and the member rule was `sdlc-fix.yml`'s narrowing from anyone (0.2.21). Whose words reach a round stays `fix_requests.py`'s member rule. The owner is known as the repository owner by default (`github.repository_owner` in an `if:`, `GITHUB_REPOSITORY_OWNER` in Python), no setting needed on a personal repository; an organization repository sets `sdlc.yaml: owner: <login>`, read from the default branch's copy, the owner's guardrail edit, asked for by `/sdlc-init` §6. One function, `is_owner_actor`, beside `is_automation_actor`, shared by T18's merge step and T24's Go: this proposal settles the question the three carry, the same way for each. The `if:` keeps the coarse check, the Python step the exact one, fail closed.
4. **A trigger, never a verb.** The comment accepts and waives nothing: the un-park verbs are labels (decision 24), a comment verb was rejected (decision 28), "a comment is not a Go" (`sdlc-fix.md:124`). Its words after `@claude` are a constraint like any review comment. The round answers in `evidence/fix-response.md` and the PR body, never in a reply (decision 20).
5. **One counter.** The round counts one iteration like a "Request changes" round and shares decision 29's counter with the automatic rounds; T30's one reset is for those, not for the owner's. A comment at the cap parks with "iteration cap reached" as today (`sdlc-fix.md:98-107`); the owner's `sdlc:reset-iterations` label is then the round, and it reads the comment.
6. **Comments already handled.** Before the runner rewrites `fix-requests.json`, it reads the committed copy's `collected_at` and `head` (the file travels with the change folder). A PR comment created at or before that `collected_at`, and listed in the previous `fix-response.md`, goes to `not_applied` with `why` "not applied: handled by an earlier round, see fix-response.md", without its text; a later one is a request. Threads keep the resolved rule, reviews the dismissed rule, the first round of a change reads everything. An edited comment is not re-read (`created_at` only): the owner writes a new one.
7. **The security boundary**, since this is a comment-driven workflow on a repository that may be public:

| Question | Answer |
|---|---|
| Who can start a round | The owner's account only, both paths; a `[bot]`, the automation identity, a member or a stranger starts nothing |
| What text reaches the model | What `fix_requests.py` keeps today, the `@claude` comment among it; the rest is listed without its text; the session reads nothing from the PR |
| Which token each job holds | The dispatcher: `actions: write`, read elsewhere, no checkout, no model; the round: today's five write scopes, no deploy or runbook secret |
| A PR from a fork | Refused by the dispatcher (head repository is not `github.repository`); the review path gains the same condition in its `if:`; an `issue_comment` run's token on a fork PR is to verify, and the design holds either way |
| The head's setup command | The install step reads `commands.setup` from the default branch (`project_setup.py --ref`, the runbook job's pattern), so no round runs a head's own command before the guardrail park |
| Where the act is recorded | R11's point 3, the round's line with the comment's link (the `trigger` input); `fix-requests.json` keeps author, association, time and link as today |

8. **Not proposed here.** No record of its own (R11, point 3). No PR-body line of its own (R19's block). A dispatcher run that fails is a red run for R18's "Failed runs" line; nothing notifies the owner (decisions 11 and 20).

## How it is judged

On the next three intent PRs the owner opens by hand: each round is started by one comment on the PR with no visit to the Actions tab; each round's line (R11) names the comment; no PR comment is applied twice across rounds. A round started by anyone but the owner, on either path, is the failure. Measured before and after: the owner's acts per round on a by-hand PR, two today, one after.

## What to settle before building

| Question | Recommended |
|---|---|
| Which comments count, and on which PRs | A PR conversation comment created with the `@claude` prefix; a line comment is read, never a trigger; every phase's PR (decision 22 covers them all) |
| How the owner's account is known (shared with T1, T18, T23 and T24) | The repository owner by default; `sdlc.yaml: owner` for an organization repository, the owner's guardrail edit; one shared function, fail closed |
| Whether the round counts against the iteration cap | Yes: settled by decision 29, one counter for every round; T30's reset is for the automatic ones |
| Whether the review path becomes owner-only too | Yes, one rule for who starts a round, decision 22's wording; whose words reach it stays the member rule |
| How a round avoids re-applying handled PR comments | Point 6, from the committed `fix-requests.json` and the previous `fix-response.md`; no GitHub state is written |
| What `issue_comment` runs use and hold (workflow file, token on a fork PR) | To verify on the sample before the design, recorded in `docs/notes/`; the dispatcher refuses fork heads whatever the answer |
| The dispatcher's and the input's names | Judged with T4; `sdlc-comment.yml` and `trigger` are placeholders |

## Considered and not chosen

- A, the row's text precisions only.
- A round per comment, as the article's: more runs and many small pushes for the owner to follow (the owner's note).
- `issue_comment` added to `sdlc-fix.yml` itself: no head in the payload, so the group, the checkout ref, `HEAD_REF` and `PR_NUMBER` would need a second shape and a first job to key the group on (whether `needs` reaches a job-level `concurrency` key is unverified); the dispatch route reuses what exists.
- A review comment (`pull_request_review_comment`) as a trigger: the line comments already reach the round through the threads.
- Keeping the member rule for starting a round: against the one-owner premise (T1) and decision 22's wording, and on a public repository it lets a collaborator run a head's setup command on the runner.
- A reply or reaction from the round to say it started: a notification (decision 20).
- A collision with another GitHub App's `@claude` trigger word on a project that installs one (the article's managed Code Review reads "@claude review"): unverified; if it bites, the prefix becomes a project setting, and the design does not depend on the word.

## Decisions it touches

22 is amended: one trigger, the owner's `@claude` comment, beside the "Request changes" review; the round, the command and the record are unchanged. The decision file is written before the intent, in a documentation PR the owner reviews on its own, never with the intent, as decision 27 (PR #162) and decisions 28 and 29 (PR #168) were. This proposal writes no decision file and reserves no number. 24 and 28 are kept (a trigger, not a verb); 29 is kept (one counter, the same dispatch); 20 and 11 are kept (no reply, no notification, a park at the cap); 5 is kept.

## Order

Fourth of the study's proposals in the confirmed order (the record, section 8: T32, T12, T21, then T17, T19, T27, T28), so after R11 to R13 and first of this batch. It changes `template/` and `plugin/`, so it ships as a plugin version with tests and reaches a project through `/sdlc-init`'s workflow copies. The parts it takes:

| Part | Where | When |
|---|---|---|
| The dispatcher workflow and the `trigger` input | `template/.github/workflows/`, `/sdlc-init` | Now, after a live check of `issue_comment` on the sample |
| The owner-only `if:` and the fork condition on the review path | `sdlc-fix.yml` | Now, same change |
| `is_owner_actor` and the optional `sdlc.yaml: owner` key | `plugin/state/unpark.py`, `template/sdlc.yaml`, `/sdlc-init` §6 | Now; T18 and T24 call it when they arrive |
| The handled-comments rule | `plugin/ci/fix_requests.py`, `run_phase.py` `collect_fix_requests` | Now |
| The install step's `--ref` | `sdlc-fix.yml:149` | Now, same change |
| The round line with the comment's link | R11, point 3 | With R11; until then the link is in the dispatch's inputs and the run's log |
| The act in the PR's block | R19 | With R19 |
| A failed dispatcher in the digest | R18's "Failed runs" | With R18 |

[^decision-22]: `docs/decisions/22.md`.
[^playbook]: `docs/reference/ai-native-sdlc-playbook.pdf` p.33-34.
[^crosswalk]: `docs/reviews/2026-09-28-playbook-vs-framework/crosswalk.json`, row deploy-comments, and `target-design.md` T17 ("Today").
[^decision-29]: `docs/decisions/29.md`, the first settle row (one counter with T30's one reset) and its "Why" (the runner dispatches explicitly).
