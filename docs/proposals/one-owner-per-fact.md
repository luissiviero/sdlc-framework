---
type: Proposal
title: "One owner per fact: every kind of fact has one place that holds its current value; the rest point to it, are generated from it or are checked against it"
description: "The sources-of-truth study found 39 stale places on main in 17 rows, every one a copy. It names one owner for each of eleven kinds of fact. Its tasks.py and docs-lint work: next-free and choices-index generate what sessions write by hand today; verify runs the pre-PR set; docs-lint checks 10 to 13 catch numbers taken twice, ranks outside ROADMAP, retired terms and commands that differ from sdlc.yaml; check 5 widened to the code's comments."
status: accepted
roadmap: R65
sources:
  - id: study
    resource: docs/reviews/2026-10-22-sources-of-truth.md
    title: "The inventory, the owner table and the drift count this proposal acts on"
  - id: double-check
    resource: docs/reviews/2026-10-20-r22-session-double-check.md
    title: "Sections 2 and 3: the rows were copies that had moved"
  - id: state-index
    resource: docs/proposals/state-index.md
    title: "R9: changes/index.md (part 1) and one file per session (part 2)"
  - id: docs-lint
    resource: docs/proposals/docs-lint-checks.md
    title: "R58: checks 1 to 9, and the rule that a proposal states no rank"
  - id: owner
    resource: "the owner's request of 2026-10-22 in this session (branch claude/sources-of-truth-study-csl6nq): a study of the sources of truth, report only, with one candidate row"
    title: "Why the row exists"
generated: { by: sdlc-framework-session/claude-sources-of-truth-study-csl6nq, at: 2026-10-22T19:20:00Z }
---

# One owner per fact

**Status: proposed on 2026-10-22 at the owner's request, and accepted the same day as recommended (choice 252).** Nothing is built. Every part but one is a documentation and `tasks.py` PR with no plugin version, as R55 and R58 were. The exception is part 6, which edits comments under `plugin/` and `template/` and rides the next plugin patch. *[2026-10-22, choice 252: a patch of its own, after R51 merges]*

## The problem
The study (`docs/reviews/2026-10-22-sources-of-truth.md`) found **39 stale places on `main` in 17 rows**, and every one is a copy:
- a manifest that still says "profile-based" after decision 37;
- a JSON twin of the build guide without its annotations;
- a session file whose "#318 is open" was wrong three minutes before it merged;
- thirteen code comments pointing at the moved `docs/NOTES.md`;
- a next-free list that a parallel PR made stale within the hour.

None was an owner that held a wrong value. The R22 double check's sections 2 and 3 found the same: every row was a copy that had moved.

Three kinds of fact have no owner at all, so every session derives them by hand:
- **the next free numbers**: 53 hand-written lines in 35 session files, one wrong when written;
- **where choice N is**: there is no index, only a `grep`;
- **the pre-PR checks**: `CLAUDE.md`, `HANDOFF.md`, `sdlc.yaml`, CI and the session prompts give four different sets.

## The proposal
The owner table is the study's section 2. For each kind, the owner is the one place that may hold the current value, and every other place is one of:
- **point**: names the owner without the value. `CLAUDE.md:34` since `396e4b4` is the model;
- **generated**: a task writes it from the owner;
- **linted**: a check compares it with the owner;
- **history**: append-only (choice 126);
- **delete**.

The work, in six parts:

1. **`python tasks.py next-free`** (new task). It reads `main` and every fetched branch ahead of it, and prints the next free choice, candidate, note, decision and patch, with the branch that holds each number taken above `main`. It reserves nothing (choice 184).
   - **Check 10** (new docs-lint check): a number taken twice fails: two choice items with one number, two decision or note files, two ROADMAP rows.
   - `HANDOFF.md`'s skeleton then says "the next free numbers: `python tasks.py next-free`" instead of a hand-written line.
2. **`python tasks.py choices-index`** (new task). It writes `docs/progress/choices.md` from the records: the number, the record's file and line, and the item's first sentence. docs-lint fails a stale index, as it does for the decisions and the notes. R62's gather step can then open "choice N".
3. **Checks 11 and 12** (new):
   - **Check 11:** no "rank N" outside a dated annotation in `docs/proposals/` and `docs/decisions/`, and none in a session file dated from this part's merge on. It is R58's own rule, which was not checked.
   - **Check 12:** no retired term as a live one in the living pages, `README.md`, the manifests and `template/`. The terms are the `full` profile, "profile-based", `sdlc:c-approved`, `sdlc:d-approved` and `sdlc:accept-risk`, read from `conventions.py`'s retired lists plus a short list in `tasks.py`. A term beside "retired", "withdrawn" or "until 1.0.20" passes. Its first run fails S1 to S4, which the same PR fixes in `README.md` and the manifests.
4. **`python tasks.py verify`** (new task) and **check 13**:
   - `verify` runs the pre-PR set: `compileall` over the build folders, ruff check, ruff format check, docs-lint, pytest, and `claude plugin validate .` when the CLI is on the path. `HANDOFF.md`'s precondition 1 and `CLAUDE.md` point to it.
   - **Check 13:** the three lines of `CLAUDE.md`'s "Verifying your work" equal `sdlc.yaml: commands`. It needs the study's guardrail rows 1 to 3 first.
5. **The history rule written down.** `HANDOFF.md`'s skeleton gains one sentence: an open PR, `main`'s head or a number is written "read at <time> UTC on <sha>". A snapshot then says when it was true. The same `HANDOFF.md` PR makes part 1's change to the skeleton.
6. **Check 5 widened** to `plugin/`, `template/` and `.github/`, with the thirteen comments that cite `docs/NOTES.md` by section rewritten to `docs/notes/<N>.md` (S15). The same plugin PR fixes S8, S11 and S12 and formats `run_phase.py`'s CLI message from `DEFAULT_CLAUDE_CODE_VERSION`. This is the one part with a plugin version: it rides the next plugin patch. *[2026-10-22, choice 252: a plugin patch of its own after R51 merges, never inside R51's PR, which rewrites the same `run_phase.py`]*

Not in R65:
- **`changes/index.md`** stays R9 part 1, at its place in ROADMAP's Order column.
- **A plugin check for projects** (their `CLAUDE.md` commands against `sdlc.yaml`) is a later candidate if the owner wants one.

## Order
The parts are independent PRs, in this order:
1. Part 1 first: it removes the most hand work, and check 10 guards the numbers every PR takes.
2. Part 2.
3. Part 3, with S1 to S4.
4. Part 4, after the owner's guardrail rows 1 to 3.
5. Part 5, a `HANDOFF.md` PR of its own as that page requires, after part 1.
6. Part 6, whenever the next plugin patch is built. *[2026-10-22, choice 252: in a patch of its own, after R51 merges]*

No other candidate waits on R65, and R65 waits on none.

## What to settle before building
The study's section 6 holds seven questions, each with a recommendation. Summary: accept as a candidate outside the ranks; compute the next free numbers; generate the choices index; lint session files from the merge on only; no `REVIEW.md` line; `build_guide.json` frozen; `tasks.py verify` as the owner of the local checks. *[2026-10-22, choice 252: the owner accepted all seven as recommended (`docs/PROGRESS.md`).]*

## Decisions it touches
- **Kept:** 7 (Python, both platforms), 9 (the repository is the record; GitHub holds the live PR state) and 10 (a generated file beside the folders, as R9's). None is amended.
- **Choices:** 126 (history is annotated, never rewritten) and 184 (no number reserved) are kept. 241's duty stays, with fewer copies to check.

## How it is judged
After parts 1 to 4, the next ten session files are read for three things: a hand-written next-free line, a rank outside ROADMAP, and a stale copy the study's classes would have caught. Each one found is a miss.
