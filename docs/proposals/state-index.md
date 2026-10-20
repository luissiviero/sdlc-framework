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

**Status: accepted by the owner on 2026-10-09 (roadmap R9).** Nothing is built. *[2026-10-13: part 2 applied in its amended shape, one file per session ("Amendment of 2026-10-13" below); part 1 is still not built.]* Part 1 is a change through the front door; part 2 is a documentation PR, which a session opens at a session boundary.

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
- Opened at a session boundary, by the session that would rewrite `HANDOFF.md` anyway, so it does not conflict with a parallel session. *[2026-10-13: amended by the owner — a one-page file that every session rewrites still conflicts whenever two sessions run in parallel; see "Amendment of 2026-10-13" below.]*

## Amendment of 2026-10-13: one file per session

**Status: applied by the owner's request of 2026-10-13 (session on branch `ccr-7da93fc5-33f691`).** It replaces the shape of part 2; part 1 is unchanged.

**Why.** Part 2 as accepted kept the rule that every session rewrites `HANDOFF.md`, and avoided conflicts only by assuming sessions do not overlap. They do. Eight merge commits touched `HANDOFF.md` up to 2026-10-13; in at least four of them two sessions had rewritten it in parallel, and the merging session kept one side and re-applied the other's lines by hand: `50324e6` ("PR #129's handoff kept, this PR's lines re-applied"), `324fbb6` (`# Conflicts: HANDOFF.md`, no note of what was kept), `a33e20e` (main's text kept, the session's annotations re-applied), `0fdb114` ("resolved on session 26's rewrite with this session's four edits re-applied", the step numbers replaced because the rewrite had renumbered them). Git does not lose a line silently, but a hand resolution can, and nothing checks it. A shorter file has fewer lines to conflict on, not fewer conflicts.

**What changes.**
- `HANDOFF.md` becomes a stable page with no state: where the state lives, how a session starts, how it ends, the skeleton of a session file, the standing preconditions and the rules. It changes only when the process changes, in a PR of its own.
- Each session writes one new file, `docs/handoffs/sessions/<YYYY-MM-DD>-<branch>.md`, at its end, and never edits another session's file. The branch makes the name unique, so two parallel sessions add two files and their PRs cannot conflict on the handoff. The file carries the state as that session left it (where the project stands, the preconditions of the moment, the next steps, every open item, what the owner does) and names the session files it built on.
- The next session reads the newest file and every file a parallel session wrote that the newest one did not build on, and reconciles them by reading, never by resolving a merge. No index file: a generated or hand-kept index would be a shared file again; the listing sorted by name is the index.
- Session 26's brief moved unchanged to `docs/handoffs/sessions/2026-10-13-session-26.md`; the briefs before it stay where they are.

**Left for the owner.** `docs/PROGRESS.md` follows the same pattern (the newest record only, rewritten by every session, the previous one archived) and so carries the same risk. The amendment leaves it as it is; folding the record into the session file, or giving `docs/progress/` a file per session from the start, is the owner's call.

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

Part 2 is the next session-boundary documentation PR. Part 1 is a change, placed by the owner in the queue after the items before it (0002 → R7 → R5 → R6 → T10 → the carried gaps → R9's part 1, unless the owner moves it). *[2026-10-20: part 2 applied on 2026-10-13 (PR #170); part 1 is rank 39 (choice 234); the rank is read from ROADMAP's Order column]*

[^playbook-artifacts]: `docs/reference/ai-native-sdlc-playbook.pdf` p.6–7, p.18, p.19–20.
[^digest]: `docs/decisions/20.md`, "Queue + digest".
[^lessons-index]: `plugin/lessons/index.py`, `build` and `check`.
