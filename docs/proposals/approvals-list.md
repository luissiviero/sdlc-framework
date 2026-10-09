---
type: Proposal
title: The record answers who, when and why — one approvals list, the run on every record, a line per fix round, the transcript as an artifact
description: Every act with an actor (the gate merges, the approval labels, the release label, the un-park labels, the Go, a close, a dismissal) gets one appended line in status.yaml, written by the deterministic step the act fires, from GitHub's own record; every run record names its workflow run and its trigger; each fix round gets a line with its reason; the session transcript is uploaded as a workflow artifact; the OpenTelemetry export is closed as not needed for one owner.
status: proposed
roadmap: R11
sources:
  - id: study-entry
    resource: docs/reviews/2026-09-28-playbook-vs-framework/target-design.md
    title: "T32, confirmed at the close of the study on 2026-10-09; from the crosswalk row x-audit (better: the framework; decision: blend, option B), accepted 2026-10-08, saved 2026-10-09"
  - id: crosswalk
    resource: docs/reviews/2026-09-28-playbook-vs-framework/crosswalk.json
    title: "Row x-audit: what the article records, what the framework records, and what no record holds"
  - id: playbook
    resource: docs/reference/ai-native-sdlc-playbook.pdf
    title: "p.6: the chain of commits is the audit trail; p.11, p.17, p.26, p.29, p.35, p.37, p.39, p.41, p.44, p.47: what is logged, with whom and when"
  - id: decision-9
    resource: docs/decisions/9.md
    title: "Decision 9: the repository is the source of truth"
  - id: decision-24
    resource: docs/decisions/24.md
    title: "Decision 24: the un-park labels, recorded with the label's actor"
  - id: code
    resource: plugin/state/status.py
    title: "The owner fields written today (risk_accepted_by, iterations_reset_by and iterations_reset_at, tests_unlocked_by, runbook_authorized_by, released_at, released_sha, released_pr), read at main 71e4da7, plugin 0.3.6"
generated: { by: sdlc-framework-session/ccr-cd596b46-vq58fk, at: 2026-10-09T16:30:00Z }
---

# The record answers who, when and why

**Status: proposed (roadmap R11), from study entry T32, confirmed by the owner on 2026-10-09.** Nothing is built. The first of the study's proposals in the owner's order: every later entry writes a line into the list this one creates.

## The problem

The article's audit trail is the chain of commits: "who asked for what, what the agent produced, and who approved it"[^playbook]. It logs each act with its actor and a timestamp: the intent's author and acceptance, the plan "along with who accepted it", a session's work "attributed to the engineer who ran it", approvals in the PR history, hook decisions with a timestamp, each run under the agent's own identity and apart from "the engineer who triggered it", triage decisions and dismissals with their reason.

The framework keeps the repository as the record (decision 9)[^decision-9], and most of the record is there: each run's result record, the run and gate records, the spend ledger, the verdicts, the findings, the panel ledger and the hook log under `evidence/`, the release record on `refs/sdlc/released/<id>`, the check runs on GitHub. What it does not hold is *who* did most of the owner's acts, and *which run* wrote each record:

- **Acts recorded with their actor, today.** The three un-park labels, as `risk_accepted_by`, `iterations_reset_by` with `iterations_reset_at` and `tests_unlocked_by`, written by the runner from the last `labeled` event's actor (decision 24)[^decision-24]; only the reset carries a time, and each field keeps the last act. The Go, as `runbook_authorized_by`. A dismissal's `by` and `at` in `changes/.dismissed.json`. The owner's change requests in `evidence/fix-requests.json`, rewritten each round. The owner's merges, as the merge commit and GitHub's `merged_by`.
- **Acts recorded with no actor, today.** The approval labels `sdlc:c-approved` and `sdlc:d-approved` (checked not to be the bot's, then left in GitHub's events). The release label's actor, in the release job's log only, while the release record holds the time, the commit and the pull request. The merges of gates (a), (b) and (e): (e) derived on the default branch's copy with no actor, (a) only for an incident change, (b) in no file of the change. A close, with a fixed reason and no closer. The `schedule` label. A fix round, one more in a count with no time and no reason.
- **What a run leaves.** `evidence/claude-<phase>.json` holds the final message and the metadata (turns, cost, permission denials, the CLI's `session_id`, `modelUsage`), not the transcript (issue #72); the transcript exists on the runner while the job runs and is thrown away with it. The run record `evidence/run-<phase>.json` carries `started_at` and `spend_usd`. None of these names the workflow run that wrote it, so a record is matched to its job log and artifacts by time alone; a hook-log line has `at`, `hook`, `event`, `tool`, `verdict`, `reason`, `cwd` and `extra`, and no run id.

Six months later the owner asks who approved the release of change 0012 and why its build took three rounds. Today the release ref says when, which commit and which pull request, not who; the log line naming the approver is gone with the log; `iterations: 3` says how many rounds, and the reasons are spread over three result records, the git history of `fix-requests.json` and commit messages.

## What the article says

- The chain of commits is the audit trail (p.6); intent acceptance is recorded as the merge or the closing review, with author and timestamp (p.11); the plan is logged with who accepted it (p.17); a session's work is attributed to the engineer who ran it (p.26); findings, fixes, ratings and approvals are logged in the PR history, "so the PR is the audit record" (p.35); allow and block decisions are logged with a timestamp, and "the gate also defines what counts as approval" (p.37); each non-interactive run acts under the agent's own identity, "so the pipeline log separates what the agent did from what the engineer who triggered it did", and a named release manager authorizes the release (p.41); triage decisions and dismissals are logged with a timestamp and a reason (p.44, p.47)[^playbook].
- The evidence of a review lives in the session transcript, "which the OpenTelemetry export forwards to the organization's observability stack", and in the PR's check run (p.29); hook decisions go to the same export with a timestamp and a verdict (p.39).

## What the framework does today

Read at `main` 71e4da7, plugin 0.3.6 (the study's row x-audit, re-checked on 2026-10-09)[^crosswalk].

- The owner fields of `status.yaml` are the only actor records in git: `risk_accepted_by` (a list of item and actor), `iterations_reset_by` and `iterations_reset_at`, `tests_unlocked_by`, `runbook_authorized_by`; the release record is `released_at`, `released_sha` and `released_pr` (`plugin/state/status.py`). They are written by the runner's un-park step from the PR timeline's `labeled` event (`plugin/state/unpark.py`) and by the release workflow's record job (`plugin/release/cli.py`).
- The un-park actors are owner-only: after the session the runner compares them with what it recorded before and with the default branch's copy, restores them and parks under `owner_fields` (`plugin/ci/run_phase.py` `verify_owner_fields`); the gate's `owner_actions` check accepts a risk gain, a count drop or a lock lift only when the same commit recorded a person's actor. "A person" is any account that is not the automation identity or a `[bot]`; it is not "the owner" (closed by T17, T23 and T24 for their own labels).
- Every commit of a run is authored by the automation identity (decision 5); the message alone tells the session's commits from the runner's. The runner's stdout JSON, in the job log and in no record, names the branch it prepared (since 0.3.6, PR #130).
- Workflow artifacts (the hook log's copy, the detection log, the eval report, the scan's files) are uploaded with no `retention-days`, so they last for the repository's retention; the label events, `merged_by`, the reviews, the comments and the check runs live on GitHub, outside git.
- `evidence/` is under no protected path: a later session can rewrite an earlier run's result record or hook log on its own branch with nothing noticing; what is on the default branch stays behind the ruleset (decision 4).

## The proposal

Nothing new to approve, nothing new to read until the owner looks: every line is written by a deterministic step from a signal the owner already gives.

1. **One approvals list in `status.yaml`**, appended and never rewritten, for every act with an actor: the (a), (b) and (e) merges (the (b) line carrying the plan's acceptance: the class, whether the close look was shown, the risk items accepted, as a details map; study entries T1 and T9), the (c) and (d) approval labels (T12, R12), the (e) approval and the App's merge (T18), the release label (T21, R13), each un-park label with every reset kept, the Go (T24), the `schedule` label, a close (T7) and a dismissal (T23). Each line: `act`, `by`, `at`, `via` (label, review, merge or close, with the pull request), the head commit, and a details map, empty for most acts. Written by the deterministic step of the workflow the act fires: the design run for the (a) merge, the build run for the (b) merge, the release workflow's record job for the (e) merge (which then runs on every (e) merge, not only after a release), the un-park step for the labels. Owner-only like the un-park actors: a session that adds, changes or drops a line is parked, and a line the default branch lacks must match a GitHub event by that actor. Carried to `refs/sdlc/released/<id>` with the release record. One shape settles the "exact fields" item of T1, T12, T18 and T21.
2. **The run on every record.** `evidence/run-<phase>.json` names its workflow run (address and attempt), the event that started it and that event's actor; every hook-log line carries the run id. The durable record then points at the logs and artifacts while they last and says who triggered each run (p.41).
3. **A line per fix round** beside the count, written by the runner and not owner-only: when, the phase, the run and the trigger it already knows (the verifier's mismatch, a red target (T10, R10), an Important finding, the owner's review or `@claude` comment with its link (T17), an un-park label). T31's rounds by class read the same lines.
4. **The transcript as an artifact.** The session's transcript, the sub-agents' with it, uploaded as an artifact of its run, named in the run record, never committed, under the repository's default retention. First a check: on a public repository, workflow artifacts may be downloadable by any signed-in account (to verify); if so, the upload is a project setting, off by default, that the owner sets once per project; on a private repository it is on. A parked run is read within days, inside the retention.
5. **The OpenTelemetry export** recorded as not needed for one owner and not built: build guide step 41's deferral closed. A live view of a running session and a sum across projects are not what one owner looking in twice a day uses; every other panel is answered from git by this proposal, T28, T30 and T31. Reopen only if several projects run.
6. **Two rules so that nothing here costs the owner an act.** A line the step cannot write (a GitHub call fails) is logged and shows in the daily digest, never a park. The approvals list is not rendered in the PR body the owner reads, except in a collapsed section.

With this, 0012's `status.yaml` on the release ref reads, one line each: "spec and plan accepted · luissiviero · 2026-09-24 17:44 UTC · merge of #13 · non-routine, close look shown", "build approved · luissiviero · 18:49 · review on #17", "release approved · luissiviero · 18:50 · label on #17", and three round lines each ending with its workflow run's address, the first "red target: test_export", the second "Important finding: missing null check", the third "owner's review on #17".

## How it is judged

On the first three changes after it ships, a session reads each change's `status.yaml` on its release ref and answers, from that file alone, who approved each gate and why each fix round ran; a question it cannot answer from the file is the failure this exists to remove. The owner-only check parks nothing on those changes unless a line was really changed.

## What to settle before building

| Question | Recommended |
|---|---|
| The key names and the YAML shape of a line (`act`, `by`, `at`, `via`, `pr`, `head`, `details`) | Judged with the study's names entry (T4) before the design; whether `via` also carries the review's or the label event's id is decided there |
| Which step writes the (e) merge line once T18's App merges | The release workflow's record job, made unconditional, so one step writes it whether the owner or the App merged |
| Whether a close at gates (b) to (e) and the `schedule` label get lines | Yes, with T7's open item on which closing comments count |
| Whether the hook line's run id is read from the runner's environment by the hook or added by the runner after the session | By the hook, from the runner's environment, so a line is complete when written |
| Where the sub-agents' transcripts are on the runner, and a transcript's size against the artifact limits | Read on the first run that uploads one; the hooks receive the main session's `transcript_path` (to verify) |
| Who can download a public repository's artifacts | Verified before the design; the setting's name and default follow from the answer |

## Considered and not chosen

- A, the row's text corrected only.
- C, transcripts kept for good on a ref per change (`refs/sdlc/transcripts/<id>`): a transcript holds every file the run read and every command's output, and on a public repository every ref is public.
- A separate append-only file under `evidence/` for the approvals: the owner-only protection exists today for `status.yaml` fields only.
- GitHub as the only record of the approvals: what exists today, and what the row found wanting.
- The daily digest catching the acts up: a gap of up to a day.
- The export kept as a deferred candidate.

## Decisions it touches

9 (the repository is the record) and 5 (the automation identity's commits, the owner's acts kept apart) are kept and extended; 24's reading of GitHub's actor record becomes one list instead of three fields, its substance unchanged. No decision is amended, so no decision file is written. Build guide step 41's transcript and export half is closed: a plan, not a decision.

## Order

First of the study's proposals, by the owner's confirmed order (the record and the approvals: this, then R12 and R13), after the queue the owner has already set (0002 → R7 → R5 → R6 → R10 → the carried gaps). R12 and R13 write their lines into the list this creates, so they follow it or are built with it.

[^playbook]: `docs/reference/ai-native-sdlc-playbook.pdf` p.6, p.11, p.17, p.26, p.29, p.35, p.37, p.39, p.41, p.44, p.47.
[^decision-9]: `docs/decisions/9.md`.
[^decision-24]: `docs/decisions/24.md`.
[^crosswalk]: `docs/reviews/2026-09-28-playbook-vs-framework/crosswalk.json`, row x-audit, and `target-design.md` T32 ("Today").
