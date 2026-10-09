---
type: Proposal
title: The state of the work in the repository, not in a hand-written handoff
description: A generated changes/index.md, built from every status.yaml, shows what is in flight; HANDOFF.md shrinks to a one-page queue and the working rules, the way the playbook carries state between sessions through committed artifacts.
status: accepted
roadmap: R9
sources:
  - id: owner-session
    resource: "the owner's session of 2026-10-09 (branch ccr-1578d710-8r04sw): the owner asked whether the playbook had this repository's handoff logic, and listed an alternative to it among the last changes the framework needs; accepted as R9 the same day"
    title: "The owner asks for an alternative to the hand-written handoff"
  - id: playbook-artifacts
    resource: docs/reference/ai-native-sdlc-playbook.pdf
    title: "p.6-7: every stage commits an artifact the next stage can read; p.18: name one system as the source of truth; p.19-20: CLAUDE.md read at the start of every session, kept under a page"
  - id: digest
    resource: docs/decisions/20.md
    title: "Decision 20: the review queue and the daily digest"
  - id: lessons-index
    resource: plugin/lessons/index.py
    title: "Change 0003: a generated index with build and check, the pattern this reuses"
generated: { by: sdlc-framework-session/ccr-1578d710-8r04sw, at: 2026-10-09T16:00:00Z }
---

# The state of the work in the repository

**Status: accepted by the owner on 2026-10-09 (roadmap R9).** Nothing is built. Part 1 is a change through the front door; part 2 is a documentation PR, which a session opens at a session boundary.

## The problem

This repository carries the state of its work between sessions in `HANDOFF.md`, a brief that every session rewrites for the next one, with the old briefs kept under `docs/handoffs/`. The playbook has no such file: each stage commits an artifact the next stage reads, the repository is the source of truth, and the context every session needs is `CLAUDE.md`, kept under a page[^playbook-artifacts].

The hand-written brief has grown into a log, and it costs every session time:
- Its first line alone is a paragraph of several hundred words; the file is 99 lines of dense text, with eight preconditions and a fifteen-row table.
- It repeats state that already lives in committed files. Each change's phase, gate result, reason, iterations and pull request are in its `status.yaml`; the order of the work is in `docs/ROADMAP.md`; the history is in `docs/PROGRESS.md` and `docs/notes/`.
- Two sessions that run in parallel both rewrite it, so their pull requests conflict on it.
- It goes stale between sessions: the starting prompt of 2026-10-09 for session 24 was written before the owner's decisions of the same day and still carries the old version plan.

A project that runs the framework has decision 20's queue (the pull requests filtered by `sdlc:*` labels) and the daily digest, a pinned issue the scheduled job rewrites[^digest]. Both live on GitHub; a session reading the repository has no committed view of what is in flight.

## The proposal

**Part 1 — `changes/index.md`, generated (a change, shipped to every project).**
- A Python command builds `changes/index.md` from every `changes/*/status.yaml`: one row per change with its id, title, phase, gate result and reason, iterations, panel calls, the pull request number, and the plugin version it last ran on. Parked changes come first, then those waiting for the owner, then those running, then the finished ones.
- The command has `build` and `check`, as `plugin/lessons/index.py` has since change 0003[^lessons-index]. The runner rebuilds the file whenever it commits a `status.yaml`, and a gate check fails on an index that is out of date.
- The digest and the queue stay: they are the owner's view on GitHub, and the index is the committed view a session reads. Both are built from the same `status.yaml` files, so they cannot disagree.

**Part 2 — `HANDOFF.md`, one page (a documentation PR, this repository only).**
- What stays: the preconditions a session must check, as a short list; the queue of work (pointers to `docs/ROADMAP.md` and to `changes/index.md`, in the owner's order); the working rules; the current starting prompt.
- What moves: per-change state goes to the change folder and the index, history to `docs/PROGRESS.md` and `docs/notes/`, decisions to `docs/decisions/` or the proposal they belong to.
- A limit like `CLAUDE.md`'s: under a page. A session that needs more writes it where it belongs and links it.
- Opened at a session boundary, by the session that would rewrite `HANDOFF.md` anyway, so it does not conflict with a parallel session.

## How it is judged

After part 2, the next three sessions' records note whether their starting prompt had to correct `HANDOFF.md` or `changes/index.md`. A stale entry is the failure this exists to remove.

## What to settle before building

| Question | Recommended |
|---|---|
| Where the index lives | `changes/index.md`, beside the folders it indexes; `changes/README.md` keeps the convention |
| Who rebuilds it | The runner, in the commit that writes a `status.yaml`; a by-hand run rebuilds it with the command |
| Does a stale index park? | Yes at a gate: the index is an artifact like `lessons/index.md`. The design confirms the check reads the working tree as `lessons/index.md`'s does |
| Part 2 before or after part 1 | Part 2 first: it needs no code, and it shows which entries part 1 must carry |
| Relation to the study | Study entries T27 (a "Next for you" line) and T28 (the digest ordered by what needs the owner) shape the digest; this shapes the committed view. The design keeps their order of rows the same |

## Decisions it touches

10 (the `changes/` layout: one new generated file), 20 (unchanged: the queue and the digest stay), 7 (Python), and change 0003's index pattern. `HANDOFF.md` is not a guardrail file; part 2 needs no owner edit table.

## Order

Part 2 is the next session-boundary documentation PR. Part 1 is a change, placed by the owner in the queue after the items before it (0002 → R7 → R5 → R6 → T10 → the carried gaps → R9's part 1, unless the owner moves it).

[^playbook-artifacts]: `docs/reference/ai-native-sdlc-playbook.pdf` p.6–7, p.18, p.19–20.
[^digest]: `docs/decisions/20.md`, "Queue + digest".
[^lessons-index]: `plugin/lessons/index.py`, `build` and `check`.
