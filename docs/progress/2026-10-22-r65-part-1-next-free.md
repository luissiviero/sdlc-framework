# Progress — ROADMAP R65's part 1: `python tasks.py next-free` and docs-lint check 10 (2026-10-22)

This session ran on branch `claude/r65-part-1-next-free`. It builds R65's part 1 as the owner accepted it (choice 252, points 2 and 3; `docs/proposals/one-owner-per-fact.md`, part 1; the study `docs/reviews/2026-10-22-sources-of-truth.md`, sections 1.7 and 2). It is a documentation and `tasks.py` PR with no plugin version, and nothing under `plugin/` or `template/`.

The previous record (choice 252, from #322) is now `docs/progress/2026-10-22-sources-of-truth-study-r65-choice-252.md`, unchanged (verified, `cmp` against `30b0367:docs/PROGRESS.md`). This session's file is `docs/handoffs/sessions/2026-10-22-claude-r65-part-1-next-free.md`.

## Coordination with the other sessions
- **Numbers.** This PR takes none: no choice, candidate, note, decision or patch. `python tasks.py next-free` on `30b0367` and the four branches ahead of it printed choice 253, candidate R66, note 58, decision 39 and patch 1.0.24, none taken above `main`. These are the values the previous session file wrote by hand.
- **Open PRs**, read at the start: #323 (the previous session's end file) and #173 (intent 0004). Neither touches `tasks.py` or the tests.
- **`HANDOFF.md` is not edited.** Its skeleton changes to "run `python tasks.py next-free`" in R65's part 5, a PR of its own as that page requires.

## What was built
1. **`python tasks.py next-free`.**
   - It reads `origin/main`, or `main` when nothing was fetched, and every local or fetched branch ahead of it, plus a detached `HEAD`. Each is read at its own commit with `git ls-tree` and one `git cat-file --batch`.
   - It prints the next free choice, candidate, note, decision and patch: one above the highest number taken anywhere.
   - It names the branch that holds each number above `main`'s highest. Nothing is reserved (choices 184 and 252).
   - Standard library only (`json` is new to `tasks.py`). It passes argument lists to `git`, with no shell, so it runs on Windows and Linux.
2. **docs-lint check 10: a number taken twice fails.** It covers two choice items with one number, two decision or note files with one number (`7.md` and `07.md`), and two ROADMAP rows with one number. A choice whose every record is older than `NUMBERS_UNIQUE_SINCE` (2026-10-22) is reported, not failed (choice 126), as check 8 does. `docs/PROGRESS.md` is always the newest record.
3. **The one-line mentions.** `tasks.py`'s docstring and its help list the new task beside docs-lint.
4. **Tests.** Three in `tests/test_docs_lint.py` (the choice reader, a choice taken twice each way, two files and two rows) and one on this repository's docs. Seven in the new `tests/test_next_free.py`, on temporary git repositories.

## The design point: where a record states a choice
A naive read of every "N. **…**" line in `docs/PROGRESS.md` and `docs/progress/` finds 1 to 6 five times, 7, 8 and 17 to 23 twice, and 16 three times (verified, `grep` on `30b0367`). These are ordinary numbered lists, not choices taken twice:
- "Live checks the owner can do now" in `session-3.md` (1 to 8) and `session-5.md` (1 to 23);
- the review findings in `session-5.md` (1 to 16);
- the "What was built" and "Questions for the owner" lists of later records, such as `2026-10-20-r24-risk-hit-banner-1.0.15.md`.

So check 10 reads a choice only as a top-level list item under a heading that states choices. The three forms in the records are "Choices made where the pack left it open", "The owner's choices" and "The owner's decision(s)". Read that way, the records state choices 16 to 252, each exactly once, with no number repeated (verified, `tasks.number_problems(tasks.DOCS_DIR)` returns no failure and no report; the layer-2 test asserts it). No record repeats a choice number.

Choices 1 to 15 are not under `docs/progress/`. Sessions 1 and 2 wrote them in `docs/PROGRESS.md` before the rule that moves a record to `docs/progress/`, and git history alone keeps them (verified, `git show fe20f6a:docs/PROGRESS.md` holds 1 to 7 and `git show 57db1b3:docs/PROGRESS.md` holds 11 to 15). Check 10 cannot see them, and needs not: every later record numbers above them.

## Unclear points, with a recommendation
- **A stale branch inflates the next free number.** A branch ahead of `main` with no open PR still counts. Today's four are `sdlc/0004/a` (#173), `claude/sources-of-truth-study-csl6nq` (#323), `ccr-bc5e88a0-y1pwjg` and `luissiviero-patch-1`, and none takes a number above `main` (verified, `tasks.branches_ahead` on `30b0367`). Recommendation: keep it so. The task cannot read GitHub's open PRs without network access, a too-high number is harmless, and the task prints the branch so a session can judge.
- **The cutover is the date of the build, 2026-10-22, not the merge.** Two records from that date are already in `docs/progress/` and repeat no choice. Recommendation: keep it, as check 8 took its build date.

## Left
- **R65's parts 2 to 5:** one session PR each, in the row's order. Part 4 waits for the owner's guardrail rows 1 to 3 (choice 252's record). Part 5 makes `HANDOFF.md`'s skeleton point to `python tasks.py next-free`.
- **R65's part 6:** its own plugin patch after R51 merges (choice 252).

## What the owner does
| When | Act |
|---|---|
| Now | Review this PR, and merge it when `Framework checks` is green on its final head. |
