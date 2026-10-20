---
type: Proposal
title: "A citation reader for this repository's docs pull requests, on Gemini"
description: "On every pull request of this repository that changes docs/, a CI job gathers the added lines that cite a decision, a choice, a note, a PR, a version or a date, gathers the cited targets, and asks a Gemini model whether each sentence matches what it cites; it reports and never blocks, and spends no Claude tokens."
status: proposed
roadmap: R62
sources:
  - id: owner
    resource: "the owner's message of 2026-10-20 in session ccr-7ef35daa-7adzh8: use Gemini for the changed-lines reader so it does not consume Claude tokens, the bottleneck; then 'write R62 as proposed'"
    title: "Why the row exists"
  - id: choice-241
    resource: "docs/PROGRESS.md, choice 241; docs/proposals/docs-lint-checks.md, 'Check 8' and 'What it does not catch'"
    title: "The reader as a skill was not built; the meaning of a citation is left to a reader"
  - id: r8
    resource: docs/proposals/external-design-check.md
    title: "R8: the Gemini key, its secret and the terms of its tier, already designed for gate (b)"
  - id: measure
    resource: "git log origin/main --first-parent --merges --since=2026-10-12, read on 2026-10-20 at 06:50 UTC in session ccr-7ef35daa-7adzh8"
    title: "How often the job would run and how much it would read"
generated: { by: sdlc-framework-session/ccr-7ef35daa-7adzh8, at: 2026-10-20T07:15:00Z }
---

# A citation reader for this repository's docs pull requests, on Gemini

**Status: proposed on 2026-10-20 at the owner's request; the owner has not decided.** Nothing is built. It changes this repository's own CI and scripts, not `plugin/` or `template/`, so it takes no plugin version.

## The problem

The docs consistency review of 2026-10-19 found 148 errors, and about half were of a kind no script can find: a decision or note cited for something it does not say, a date that disagrees with another record. R58's eight checks find the mechanical half on every pull request. The meaning half has three answers today, none automatic on the pull requests where docs lines are written:

- the review pass compares a diff's citations (`REVIEW.md`, the owner's PR #274), but it runs only on changes that go through the phases, and nearly every docs line is written in a session pull request;
- the session-side rule (choice 241, `HANDOFF.md`'s "Rules for every session") depends on the session doing it;
- a full sweep costs about four million Claude tokens and runs at a milestone.

A reader that ran on Claude on every docs pull request would cost about 40,000 Claude tokens a run (the docs session's estimate of 2026-10-20, not measured), and Claude tokens are the bottleneck.

## The proposal

A job in this repository's CI, on every `pull_request` that changes `docs/**`:

1. **Gather (Python, no model).** From the pull request's diff, the added lines under `docs/` that cite a decision, a choice, a note, a PR, a version or a date; for each, the cited target: the decision file, the note, the PROGRESS choice, the ROADMAP row, or the PR's merge from git. R58's patterns and check 8's merge reader already do most of this (`tasks.py`).
2. **Ask (one Gemini call, or a few for a large diff).** Each added sentence beside the text it cites: does the sentence say what the target says? One line per claim: matches, misstates (and how), or cannot tell.
3. **Report, never block.** The answer goes to the job summary, and to one PR comment if the owner wants it. A failed call (no key, an outage, a quota, a refusal) is "not run: <reason>"; the job stays green.

What it reuses from R8: the key in a GitHub Actions secret (`GEMINI_API_KEY`) given to that one step alone, the rule that an outage never turns a job red, and the open question of the key tier's terms. This repository is public, so the job sends Google nothing that is not already published; R8 would send a project's private code. R62 can be the first live use of the key on text with nothing to lose, before R8 relies on it.

## How often and how long

Measured on `main` (git log, 2026-10-12 to 2026-10-20): 93 of 118 merged pull requests changed `docs/`, over 7 active days, about **12 to 13 runs a day** at that pace. Per pull request, the lines added under `docs/` had a median of 117 (90th percentile 281, maximum 3,851), with a median of 82 citation-like mentions (90th percentile 278); that count includes plain dates, so the claims to judge are fewer.

Not measured, an estimate: the gather step takes seconds; one call on a median pull request about 30 to 90 seconds; a large one 2 to 5 minutes in several calls. About **1 to 3 minutes a run** and **25 minutes of CI a day**, with **no Claude tokens**. Gemini's price was not verified here; the job records the tokens of each call.

## What to settle before building

| Question | Options | Recommended |
|---|---|---|
| The key tier's terms | as R8 asks | Read them before the first call (R8's question; one answer serves both) |
| Where the answer goes | job summary · one PR comment | The job summary first; a comment needs `pull-requests: write` for the job |
| Which Gemini model | the owner picks it | Named in the job's configuration; this file names none, none was verified here |
| How it is judged | a tally per pull request: claims flagged, flags that proved real | Keep it advisory; after 20 pull requests the owner keeps it, drops it, or makes a real misstatement a failure |
| Its order beside R8 | before R8 · with R8 · after R8 | The owner's; before R8 proves the key and the client on public text |

## What it does not cover

Projects: it reads this repository's docs only, not a project's, and adds nothing to `/sdlc-init`. The review pass, the session-side rule and the full sweep stay as they are; it adds a reader and replaces none.

## Decisions it touches

7 (Python for the gather step; kept), 1 (kept: it names how the Claude runs authenticate, and this job holds no Claude credential), 12 (kept: the review pass is unchanged), the security baseline (a secret and one outbound host in a CI step, as R8). No decision is amended. A second model vendor in this repository's CI is the owner's call, made knowingly; R8 asks the same for a project's phase (b).

## Order

Blank until the owner places it.
