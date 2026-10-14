---
type: Proposal
title: The digest — ordered by what needs the owner, current at every park, never failing silently
description: The pinned "SDLC review queue" issue is reordered into "Needs you" (parked, then waiting; incident PRs first, then oldest first, each with how long it has waited and T27's "Next for you"), "Worth knowing", "State" and the counters; the runner dispatches the digest after every park or human gate; a digest that cannot list or publish exits 1. One issue, nothing notifying the owner.
status: proposed
roadmap: R20
sources:
  - id: study-entry
    resource: docs/reviews/2026-09-28-playbook-vs-framework/target-design.md
    title: "T28, confirmed at the close of the study on 2026-10-09; from the crosswalk row x-queue (better: the framework; decision: blend, option B), 2026-10-07; annotations of 2026-10-13 (A2) and 2026-10-14 (A9, E6)"
  - id: crosswalk
    resource: docs/reviews/2026-09-28-playbook-vs-framework/crosswalk.json
    title: "Row x-queue (whole); the decision fields of maintain-act, x-roles, deploy-ci, deploy-release, deploy-claudemd, deploy-envs, maintain-detect, maintain-triage, maintain-learn, maintain-scan, x-measure and x-limits"
  - id: artcraft
    resource: docs/reviews/2026-10-13-artcraft-vs-framework/templates-revision.md
    title: "E6 (row A9): incident PRs first within each section; record rows A2 and A9, gap G3"
  - id: playbook
    resource: docs/reference/ai-native-sdlc-playbook.pdf
    title: "p.8: attention concentrates at the gates; p.41: failures triaged without paging a human; p.44-45: the triage queue of maintain findings"
  - id: decision-20
    resource: docs/decisions/20.md
    title: "Decision 20: a review queue and a daily digest, nothing pushes to the owner (kept; 'daily' becomes 'refreshed at least daily')"
  - id: decision-11
    resource: docs/decisions/11.md
    title: "Decision 11: park, never page (untouched)"
  - id: decision-26
    resource: docs/decisions/26.md
    title: "Decision 26: the rehearsed rollback pre-approved, one notification rejected (untouched; its rejected option is this proposal's option C)"
  - id: code
    resource: plugin/pr/digest.py
    title: "render_digest, _phase_of, _line, publish and main, read at main acefc7e, plugin 1.0.0; with plugin/pr/counters.py, plugin/pr/github.py pinned_issue, plugin/ci/run_phase.py NEXT_WORKFLOW, dispatch and hand_over, template/.github/workflows/sdlc-digest.yml"
generated: { by: sdlc-framework-session/ccr-20b39ad0-kcymdd, at: 2026-10-14T15:30:00Z }
---

# The digest: ordered by what needs the owner, current at every park, never failing silently

**Status: proposed (roadmap R20), from study entry T28, confirmed by the owner on 2026-10-09.** Nothing is built. This proposal owns the digest's order, its refresh and its exit code. The lines it places are defined elsewhere: "Failed runs" in R18 (T19), "Next for you" in R19 (T27), the release line in R13, and the rest in entries not yet proposed (T15, T20, T22, T23, T25, T26, T30, T31). Each line arrives with its entry; the order and the refresh can be built first.

## The problem

The digest is the one surface the owner reads every day, and it is laid out for the framework, not for the owner:

- **It is ordered by phase letter, not by need.** "Waiting at a human gate" is sorted by the gate's letter and then by PR number (`plugin/pr/digest.py:141`), so an incident intent at `sdlc:f-ready`, the most time-sensitive item, is listed last; "Parked" keeps the order the pulls endpoint returns (`digest.py:139`). On 2026-10-14 the sample's digest (run 38560274588, issue #8) listed #55, #56, #57 and #60 under "Waiting at a human gate", the incident intent #60 last (`docs/handoffs/sessions/2026-10-14-ccr-5b7d20dc-ot5xgy.md`, "Later the same session", 12:15 UTC; `docs/notes/43.md` records the run and that #60 was listed, not where)[^artcraft].
- **It is a day old at the moment it matters.** The issue is rewritten once a day at 06:17 UTC (`template/.github/workflows/sdlc-digest.yml:26`); the sample's six runs of 2026-10-08 to 2026-10-13 started between 12:36 and 15:31 UTC. A run that parks at 08:00 is in no digest until the next day.
- **It fails green.** A digest that cannot list the pull requests, or cannot publish, prints the reason and exits 0 (`digest.py:239-246`); a failed lookup of the pinned issue opens a second "SDLC review queue" issue (`digest.py:192-198`).
- **It shows each item's first bullet** with its labels and `updated_at` (`digest.py:98-108`), not how long it has waited or what the owner can do.

## What the article says

Human attention "concentrates at the gates, reviewing what the agent flagged rather than starting each stage from scratch" (p.8); the maintain stage has a triage queue that a service owner triages ("fix now, schedule, or dismiss", p.44) and counts "the share of pipeline failures triaged without paging a human" as a leading indicator (p.41). The article describes no review queue or digest for finished work; the digest is the framework's own answer (decision 20), and this proposal makes it read in the order the owner's attention should go[^playbook].

## What the framework does today

Read at `main` acefc7e, plugin 1.0.0. The entry's "Today" was read at 619f01a (0.3.5); `git diff 619f01a acefc7e -- plugin/pr/digest.py plugin/pr/counters.py plugin/pr/github.py template/.github/workflows/` is empty, so every line the entry cites still holds, `digest.py:91-96` (`_phase_of`) and `:141` (the sort) among them. Of the files this proposal touches only `plugin/ci/run_phase.py` moved (0.3.6 and 0.3.7, 279 lines); `NEXT_WORKFLOW`, `dispatch` and `hand_over` are at `:164`, `:1550` and `:2536`[^code].

- **Schedule and trigger.** `sdlc-digest.yml`: `cron: "17 6 * * *"` and a `workflow_dispatch` with no inputs (`:24-27`); permissions `contents: read`, `issues: write`, `pull-requests: read`, no `actions` (`:29-32`); concurrency group `sdlc-digest`, `cancel-in-progress: false` (`:34-36`); a `fetch-depth: 0` checkout of the default branch.
- **Content and order.** The unprotected-branch notice; a count line ending "this issue is rewritten once a day (decision 20)" (`digest.py:147-151`); "Parked" (GitHub's order); "Waiting at a human gate" (by phase letter, then number); "Phase (f): runbook and dismissal PRs" (`incident` with no gate label, by number, `:166-169`); the counters table (`plugin/pr/counters.py` `render`: changes, shipped, first-pass share, fix iterations per shipped change, panel calls, incidents merged and shipped, dismissals in force by kind); "Generated <UTC>".
- **Reading and publishing.** The open pull requests, up to 100, filtered client-side (`:176-187`); the pinned issue found by exact title among the first 100 open issues (`plugin/pr/github.py:1009-1056`), pinning best effort (`:1135-1136`). Exit codes: 2 on a bad `--input` file (`digest.py:221`); 0 otherwise, a failed listing or publication included (`:239-246`). Whether editing an issue body notifies is not stated in GitHub's documentation (`docs/notes/11.md:157-162`); the design relies on the workflow token as author and the owner's "Participating and @mentions" watch (`docs/OPERATING_MODEL.md` §7, which also says the owner may turn off GitHub's failed-run e-mail).
- **No digest run follows a park.** `hand_over` dispatches only on `continue`, and only `sdlc-test.yml` after (c) and `sdlc-deploy.yml` after (d) (`run_phase.py:164`, `:2536-2555`); `dispatch` always sends `change_id` and `head_ref` (`:1565`). A park (`park_and_publish`, called at `:1424` to `:1899`) and a `wait` dispatch nothing. Design, build, test, deploy and fix hold `actions: write`; detect `actions: read`; abandon, runbook, scan, release, evals and the digest none.
- **Clocks.** The digest writes UTC (`digest.py:58-59`); GitHub's `updated_at` is UTC. R16 (`docs/proposals/detect-local-day.md`) moves the detection record's displayed times to the owner's offset, not the digest's.
- **What reaches no surface the owner reads:** a red run with no park, a release waiting for its label, the detection's state, the scan's run, the waiting CLAUDE.md lines, the rehearsal results, the week's spend.

## The proposal

One pinned issue, rewritten, never a comment; the PR list stays the queue; nothing notifies the owner (decisions 11 and 20). Three changes to the digest and one to the runner.

**1. Ordered by what needs the owner.** The outline below is the whole issue, top to bottom. "Feeds" names the proposal or entry that defines each line; "When" says whether it can be built with this proposal or arrives with its entry.

| # | Section and line | Shape of the line | Feeds | When |
|---|---|---|---|---|
| 0 | The unprotected-branch notice | as today, first, only while the ruleset is missing | built | now |
| 1 | The count line | "N parked, M waiting at a gate, K runbook or dismissal PRs. Nothing here notified you; this issue is rewritten after every park or gate and at least daily (decision 20)." | this | now |
| 2 | **Needs you — Parked** | one line per `sdlc:needs-human` PR: link, title, labels, "waiting N days", the park reason's first line; below it "Next for you: …" (R19) | this; R19 | order and wait now; "Next for you" with R19 |
| 3 | **Needs you — Waiting at a human gate** | one line per other `sdlc:` PR, same shape, the gate named from its label | this; R19 | now; R19 |
| 4 | **Needs you — Runbook and dismissal PRs** | the `incident` PRs with no gate label, same shape (today's third section, moved under "Needs you") | this; R19; T23 removes the dismissals the App merges | now |
| 5 | A spend line in "Needs you", only when the numbers look wrong | T30's text, with its suggested value | T30 | with T30 |
| 6 | **Worth knowing — Failed runs** | R18's line, one per red run with no park, the triage text marked model-written (A2) | R18 | with R18 |
| 7 | Worth knowing — Releases waiting for your label | R13's line | R13 | with R13 |
| 8 | Worth knowing — CLAUDE.md lines waiting | T15's count and the standing PR's link, with T31's "found in N changes" | T15, T31 | with T15 |
| 9 | Worth knowing — Rehearsals | T20's failed or stale rehearsal | T20 | with T20 |
| 10 | Worth knowing — A record line a step could not write | R11's point 6 (a GitHub call that failed, logged, never a park) | R11 | with R11 |
| 11 | **State — Detection** | T22's last verdict and baseline, T23's "muted by #n, scheduled since <date>", T25's "<id> fixed on <date>: N days within 1σ" | T22, T23, T25 | with T22 |
| 12 | State — Scan | T26's last run, findings filed and skipped, nits with the artifact link | T26 | with T26 |
| 13 | State — Spend | T30's week against the ceiling | T30 | with T30 |
| 14 | **Counters** | today's table; T31 adds the class split, the definitions under the table and the DORA row | built; T31 | now; T31 |
| 15 | "Generated <time>" | as today | built | now |

The sort within sections 2, 3 and 4: pull requests labelled `incident` first (E6, ArtCraft row A9), then oldest first by how long they have waited; parked stays above waiting because parked work is blocked. The phase letter is no longer a key (the gate is still on the line). A ticket's regression joins the first key when T6 gives tickets a label. A2's label applies in two places: where T1's manager recommendation is quoted on a queue line it is marked as the manager's judgment, and R18's triage text in "Failed runs" is marked model-written; every other line is measured by construction[^artcraft].

"How long it has waited" is read from the gate record's `at` (`plugin/gate/gate.py:99`, `:126`), or from the pull request's creation at gate (a), where no gate record exists; T31 settled it so (`target-design.md` T31, "No other new counter")[^t31]. The gate record is on the work branch, not the default branch; the digest's checkout already reads the remote `sdlc/<id>/*` branches for the abandon markers (`counters.py:5-6`, `:44`), the precedent.

**2. Current whenever the owner opens it.** Besides the daily run, the issue is rewritten after every phase run that parks or stops at a human gate: the runner dispatches `sdlc-digest.yml` in a call of its own, with no inputs, after `park_and_publish` and after a `wait` result, where `hand_over` runs today (`run_phase.py:1933`). The concurrency group collapses a burst to one running and one pending run. The count line no longer says "once a day". The same token edits the same issue, so the notification picture is today's.

**3. A failed digest is visible.** A digest that cannot list the pull requests or cannot publish exits 1: a red run, which R18's "Failed runs" line reports in the next digest that succeeds (GitHub's failed-run e-mail may follow unless it is off, OPERATING_MODEL §7, as for any red run today). The pinned issue is found reliably: the repository's pinned issues first (GraphQL, the route `pin_issue` already uses), then the title scan paged past 100; a failed lookup publishes nothing, exits 1 and never opens a second issue. Exit 2 on a bad `--input` stays.

**4. No ping.** This paragraph builds nothing: it restates decision 26 as T20 and T24 bind it. A rehearsed rollback with a fresh rehearsal and a release in the breach window is pre-approved and waits for nobody; every other running-system route parks with "Go requested" and waits for the owner's next look, the cost decision 26 accepted.

## How it is judged

On the sample, after it ships: a run that parks at 08:00 UTC is in the issue within minutes, not the next afternoon; an incident intent is the first line of its section; the owner's inbox gets nothing from the issue's edits (the first run's creation excepted); a digest that cannot publish is a red run and a "Failed runs" line the next day, never a green run with a reason in its log. The measure is the time from a park to its line in the issue, read from the park's commit time and the issue's "Generated" time.

## What to settle before building

| Question | Recommended |
|---|---|
| Where "how long it has waited" is read from | **Settled by T31**: the gate record's `at`, or the pull request's creation at gate (a) (`target-design.md` T31). Read from the work branch on the digest's checkout, as the counters read the abandon markers |
| Which workflows refresh the digest besides the phase runs | Design, build, test, deploy and fix now: they hold `actions: write` already. Detect (`actions: read` today), scan, runbook and release (none today) with T22, T26, T24 and R13, each adding `actions: write` to the job that ends at the owner's act. Gate (a) has no workflow (`/sdlc-plan` by hand); the owner's own merges and labels change the queue without a run: the daily run covers both |
| Whether the issue keeps a line of history (yesterday's counts) | No line in the digest; GitHub keeps the issue body's edit history (whether the API exposes it to a later reader: to verify). The counters' history is T31's own open item, shared with this one |
| How "Failed runs" finds failed runs, and how a failed digest is reported when every digest fails | **Answered by R18**, consistently with R13: a record the failing step writes, read by the digest; the digest workflow holds no `actions` permission. A digest that fails every day is a red run every day in Actions, and this proposal adds nothing for that case |
| Where the runbook and dismissal PRs go | A third group under "Needs you", after waiting: they need the owner's merge until T23's App merges a dismissal on the owner's own close |
| One clock, or each line's own | The digest keeps UTC for every instant it writes and for GitHub's times; a time copied from a record is shown as the record writes it, with its offset suffix (the detection record at R16's offset); "waiting N days" is a duration and has no clock. One sentence under the count line says so |
| The dispatch with no inputs | `dispatch` sends two inputs today (`run_phase.py:1565`) and `sdlc-digest.yml` declares none; a second helper, or an optional `inputs` argument; whether GitHub refuses unexpected inputs with 422 is to verify, and the helper sends none either way |

## Considered and not chosen

- A, the x-queue text corrected only.
- C, B plus an `@mention` comment by the workflow when Go is requested on a declared production, the cases B leaves waiting (no release in the window, a stale rehearsal, a runbook that is not a rollback): it reopens decision 20 and decision 26's rejected option 2 (one notification for a 3σ breach on a declared production)[^decision-26].
- A one-day triage SLA (ArtCraft 9.3, E7): it needs a notification when the deadline passes.

## Decisions it touches

20 is kept and its "daily digest" read as "refreshed at least daily", still pull; 11 is untouched (park, never notify); 26 is untouched, its rejected option being this proposal's option C. No decision is amended, so no decision file is written and no number is reserved[^decision-20][^decision-11].

## Order

After R18 and R19 in this batch for the lines it places, and after R10 for the runner (`run_phase.py` is on the port list; a change there ships as a plugin version with tests). The parts, as R14's "Order" lists them:

1. **The order, the wait and the sort** (`digest.py`, its tests in `tests/test_pr.py:947-1198`): incident first, oldest first, "waiting N days" from the gate record, the runbook and dismissal PRs under "Needs you", the count line's new text, the clock sentence. Buildable now.
2. **The refresh**: a no-input dispatch helper in `run_phase.py`, called after `park_and_publish` and after a `wait`, in the five phase workflows that already hold `actions: write` (design, build, test, deploy, fix; the digest's `permissions` unchanged). Buildable now, with part 1. Detect, scan, runbook and release join with T22, T26, T24 and R13, each adding `actions: write` to its template.
3. **Exit 1 and the reliable lookup** (`digest.py`, `github.py pinned_issue`). Buildable now.
4. **"Next for you"** on every queue line: with R19. **"Failed runs"**: with R18. The release line: with R13. R11's "could not write" line: with R11.
5. **The other lines** as their entries ship: T15, T20, T22 (with T23 and T25), T26, T30, T31's rows. T4's names cost nothing here: the digest reads every label from `state/conventions.py` (`digest.py:40`, `:75`, `:139`).

[^playbook]: `docs/reference/ai-native-sdlc-playbook.pdf` p.8, p.41, p.44-45.
[^decision-20]: `docs/decisions/20.md`.
[^decision-11]: `docs/decisions/11.md`.
[^decision-26]: `docs/decisions/26.md`.
[^artcraft]: `docs/reviews/2026-10-13-artcraft-vs-framework/templates-revision.md`, E6 and section 9.2; the record `docs/reviews/2026-10-13-artcraft-vs-framework.md`, rows A2 and A9, gap G3; `docs/notes/43.md` (run 38560274588); `docs/handoffs/sessions/2026-10-14-ccr-5b7d20dc-ot5xgy.md`, "Later the same session (2026-10-14, 12:15 UTC)".
[^t31]: `docs/reviews/2026-09-28-playbook-vs-framework/target-design.md`, T31, "Direction discussed", "No other new counter"; the crosswalk row x-measure, point (5).
[^code]: `plugin/pr/digest.py`; `plugin/pr/counters.py`; `plugin/pr/github.py` `pinned_issue`, `pin_issue`; `plugin/ci/run_phase.py` `NEXT_WORKFLOW`, `dispatch`, `hand_over`, `park_and_publish`; `template/.github/workflows/*.yml` `permissions`; `plugin/gate/gate.py`; the crosswalk row x-queue and `target-design.md` T28 ("Today").
