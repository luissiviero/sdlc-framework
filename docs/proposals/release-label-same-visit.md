---
type: Proposal
title: The release label stays a second act, given in the same visit; a waiting or failed release reaches the digest; the approver is recorded
description: On a declared production the build PR's banner says to apply sdlc:release-approved with the approval, so both acts happen in one visit; the daily digest lists releases waiting for their label and failed release runs; the release record stores who applied the label and when; the Platform & release brief comes before the approval.
status: proposed
roadmap: R13
sources:
  - id: study-entry
    resource: docs/reviews/2026-09-28-playbook-vs-framework/target-design.md
    title: "T21, confirmed at the close of the study on 2026-10-09; from the crosswalk row deploy-release (better: both; decision: blend, option B), 2026-10-07"
  - id: crosswalk
    resource: docs/reviews/2026-09-28-playbook-vs-framework/crosswalk.json
    title: "Row deploy-release: the article's release authorization against the framework's label"
  - id: playbook
    resource: docs/reference/ai-native-sdlc-playbook.pdf
    title: "p.35-37: the production deploy hook blocks until a named person authorizes, what counts as approval, decisions logged with a timestamp; p.40-41: the release manager"
  - id: decision-13
    resource: docs/decisions/13.md
    title: "Decision 13: gate (e) is the merge, plus a release label on a declared production (kept)"
  - id: code
    resource: plugin/release/approval.py
    title: "release_approval and is_automation_actor: the label's actor read from GitHub, a bot's never counting, read at main 71e4da7, plugin 0.3.6"
generated: { by: sdlc-framework-session/ccr-cd596b46-vq58fk, at: 2026-10-09T16:30:00Z }
---

# The release label stays a second act, given in the same visit

**Status: proposed (roadmap R13), from study entry T21, confirmed by the owner on 2026-10-09.** Nothing is built. Its approver line goes into R11's approvals list, so it follows R11 or is built with it.

## The problem

On a declared production (`deploy.production: true`) gate (e) has two acts (decision 13)[^decision-13]: the owner's merge of the build PR, then the label `sdlc:release-approved` on it. Three things about the second act are wrong or missing today:

- **It costs a second visit.** The PR body tells the owner to apply the label "after merging" (`plugin/pr/description.py`, `plugin/commands/sdlc-deploy.md` §5 and §6), although a label applied before the merge already counts: the labeled event on the open PR is skipped, and the merge then finds the label.
- **A waiting or failed release shows nowhere the owner looks.** A release waiting for its label is a green job on a closed PR, and the daily digest lists open PRs only; a failed release is a red run in Actions that nothing in the framework reports.
- **No framework record says who approved the release.** The release log prints "label applied by …" and GitHub's PR timeline keeps the event; the release record holds `released_at`, `released_sha` and `released_pr`, and no actor.

## What the article says

The production deploy hook blocks the release until a named release manager authorizes it, and the agent cannot pass the gate; a hook can ask, pausing the action until a specific person approves; the gate defines what counts as approval, and allow and block decisions are logged with a timestamp (p.35-37, p.40-41)[^playbook]. The release manager is a role apart from the code owner who approves the code (p.33, p.41): two acts, by two people, where the framework has two acts by one owner.

## What the framework does today

Read at `main` 71e4da7, plugin 0.3.6[^crosswalk].

- `sdlc-release.yml` runs on a pull request `closed` or `labeled` into the default branch (the labeled event only for that label on a merged PR) and on a `workflow_dispatch`; its release job holds a read-only token and runs no Claude session. `release/cli.py` checks the approval with the production-gate hook's own function (`plugin/release/approval.py` `release_approval`): the actor of the label's last `labeled` event, read from GitHub, never the automation identity or any `[bot]` account (`is_automation_actor`); a label removed again no longer counts; no route to GitHub fails closed ("cannot verify the label", a green "waiting")[^code].
- A label on the open build PR also opens the production-gate hook for a Claude session whose checkout is that PR's head (`approval.py` accepts an open PR's approval at its head); the "after merging" wording avoids that today.
- Since 0.3.1 a build PR merged while parked waits for the label whatever `deploy.production` says, and the log prints the park reason (issue #68). The production-gate hook blocks the adapter's guarded commands in any Claude session until the approval exists; it never asks, and on a declared production it logs each allow and block (`plugin/hooks/production_gate.py`).
- Exit codes of the release step (`release/cli.py run`): 0 when it releases, skips or waits (a label that cannot be verified is a green "waiting" too); 1 when `deploy.command` fails, or the release ran and its outputs for the record job could not be written; 2 on a configuration error or when the pull request, the change or the remote's release record cannot be read, failing closed. The `record` job exits 1 when the release cannot be stored and 2 on a bad change id.
- `release-notes.md` is read by the build PR's body (`plugin/pr/description.py`), never by the release workflow.

## The proposal

Decision 13's two acts stay; what changes is when the owner gives the second, and what the record and the digest show.

1. **Both acts in one visit.** On a declared production the build PR's "Needs your close look" banner (T9, T18) says: apply `sdlc:release-approved` with your approval to release on merge; without it the merge waits for the label. The label applied before the approval already counts, so the owner labels and approves in one visit, from the phone too; the PR body's "after merging" is corrected. The cost: while the labeled build PR is open, the production-gate hook lets a Claude session at its head run guarded deploy commands (a session by hand on the owner's machine, or an (e) fix round before its first commit; CI phase jobs hold no deploy secret, though they hold the workflow token); the hook accepting only a merged PR's label would remove it (to settle).
2. **Where it meets T18.** T18's GitHub App merges on the owner's approval. The App's merge fires the `closed` event that starts `sdlc-release.yml`, unlike the workflow token's own events (to verify); if it does not, T18's merge workflow dispatches `sdlc-release.yml` with the PR number, as the runner dispatches the next phase. The App is a `[bot]` account, so its acts never count as the release approval. The App merges only a build PR at `sdlc:e-ready` with a green `sdlc/review`, never a parked one, so issue #68's label-on-a-parked-merge is reached only by the owner's own merge.
3. **A waiting or failed release reaches the digest.** The daily digest gains a "Releases waiting for your label" line: merged build PRs at phase (e) whose release has no record and whose approval is missing. `sdlc-release.yml` joins T19's "Failed runs" line (exit 1 or 2). A release log gets no triage text: it can print the project's own secrets, which GitHub masks only in its own log view. Nothing notifies the owner (decisions 11 and 20).
4. **The approver is recorded.** The release record gains who applied the label and when, as one line of R11's approvals list (`act` "release approved", `by`, `at`, `via` the label on the pull request, the head commit), beside T18's approval line and R12's label lines, on the work branch and on `refs/sdlc/released/<id>`.
5. **The release checklist.** T1's Platform & release brief comes before the owner's approval on a declared production.

## How it is judged

On a project with a declared production: each release's record on its ref names the approver; a release that waited for its label appears in the digest the next morning; a failed release run appears in the digest's "Failed runs" line. A release the owner learns about from Actions alone is the failure.

## What to settle before building

| Question | Recommended |
|---|---|
| How the digest finds a release waiting for its label | A record the release step writes when it waits, read by the digest, rather than scanning closed PRs; it also tells "no label yet" from "the label could not be verified", which today both end as a green "waiting" |
| Whether the production-gate hook accepts the release label only on a merged PR | Yes, so a label applied with the approval opens no Claude session's guarded commands while the PR is open |
| The approver line's fields | R11's shape; carried to `refs/sdlc/released/<id>` with the release record |
| Whether a merge by a GitHub App starts `pull_request: closed` workflows | Verified when T18 is built; else T18's merge workflow dispatches the release |
| Whether a release that waits longer than some days shows in the change's own record | The digest only, until a case shows the record is needed |

## Considered and not chosen

- A, the row's text precisions only.
- C, the owner's T18 approval counted as the release authorization on a declared production, the label kept only for a parked merge: one act fewer, but it loses the article's separate release manager (p.40-41), decision 13's reason (a second act exactly where live trading is touched) and the option to merge now and release later; it would amend decision 13.
- An asking hook: the runs are unattended, so nobody would answer it.

## Decisions it touches

13 (two acts on a declared production) is kept; 11 (park, never notify) and 20 (the digest, pull not push) are kept, the new lines going to the digest. No decision is amended, so no decision file is written.

## Order

Third of the study's proposals, after R11 and R12; its T18 and T19 parts (the App's merge event, the "Failed runs" line) land with those entries' own proposals and are reached from here by the dispatch fallback and the digest line.

[^decision-13]: `docs/decisions/13.md`.
[^playbook]: `docs/reference/ai-native-sdlc-playbook.pdf` p.33, p.35-37, p.40-41.
[^crosswalk]: `docs/reviews/2026-09-28-playbook-vs-framework/crosswalk.json`, row deploy-release, and `target-design.md` T21 ("Today").
[^code]: `plugin/release/approval.py`, `release_approval` and `is_automation_actor`; `plugin/release/cli.py`; `template/.github/workflows/sdlc-release.yml`.
