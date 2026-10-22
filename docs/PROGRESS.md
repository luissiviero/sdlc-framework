# Progress — ROADMAP R65's part 2: `python tasks.py choices-index` and `docs/progress/choices.md` (2026-10-22)

This session ran on branch `claude/r65-part-2-choices-index`. It is the same session as R65's part 1 (#324), and the owner asked it to start part 2 once #323's merge was checked. Part 2 is built as the owner accepted it: choice 252, point 3, and `docs/proposals/one-owner-per-fact.md`, part 2. It is a documentation and `tasks.py` PR with no plugin version, and nothing under `plugin/` or `template/`.

**This branch is built on #324's branch**: the task reads choices with part 1's `choice_items`. Its diff against `main` holds #324's commits until #324 merges. The owner merges #324 first.

The previous record (R65's part 1, from #324) is now `docs/progress/2026-10-22-r65-part-1-next-free.md`, unchanged (verified, `cmp` against `claude/r65-part-1-next-free:docs/PROGRESS.md` at `c87725b`). This session's end file is `docs/handoffs/sessions/2026-10-22-claude-r65-part-2-choices-index.md`.

## Coordination with the other sessions
- **#323 merged** as `50eea3b` after part 1 was opened. It added only the previous session's end file (verified, `git diff --stat 30b0367 50eea3b`). `main` is merged into #324's branch, and so into this one; no file conflicted.
- **Numbers.** This PR takes none. `python tasks.py next-free` on `50eea3b` printed choice 253, candidate R66, note 58, decision 39 and patch 1.0.24, none taken above `main`.
- **Open PRs**, read after #323 merged: #324 (part 1) and #173 (intent 0004).

## What was built
1. **`python tasks.py choices-index`.** It writes `docs/progress/choices.md` from the records, one row per choice: the number, the record and line as a link, and the item's first sentence.
   - A choice is what docs-lint check 10 reads: a top-level item under a heading that states choices.
   - The first sentence is the item's first bold phrase, because every record leads its choices with one. 236 of the 237 items open with it; choice 168 opens with an italic note and then the bold phrase. An item with no bold phrase gives its first sentence.
   - Links are reduced to their text, and a bar is escaped for the table.
2. **docs-lint fails a stale or missing index** ("docs/progress/choices.md differs: run python tasks.py choices-index"), as it does for the decisions and the notes.
3. **The two generated pages beside the records** (`index.md`, `choices.md`) are no longer read as records, by check 10 or by `next-free`.
4. **The first index**: choices 16 to 252, 237 rows. Choices 1 to 15 are named in its opening as kept in git history only (`fe20f6a`, `57db1b3`), as #324's record found. `docs/progress/index.md` gains one sentence saying `choices.md` is not a record.
5. **Tests.** Three in layer 1 (the summary, the rows and their links, a stale or missing index each way) and one in layer 2 (the index on disk is what the task writes).

## Unclear points, with a recommendation
- **A line number moves with every edit above it.** A PR that edits `docs/PROGRESS.md` above a choice, or moves it to `docs/progress/`, changes the index, and docs-lint names the task to run. Two parallel PRs that both take a choice already conflict in `docs/PROGRESS.md`; the index adds one generated file to resolve by running the task. Recommendation: keep the line. The proposal asks for it, and the alternative, a heading anchor, does not name the item.
- **ROADMAP R65's row is not annotated per part.** Its Status says "accepted" until all six parts are built. Recommendation: one annotation when part 5 merges, not one per part.

## Left
- **R65's parts 3 to 5:** one session PR each, in the row's order. Part 4 waits for the owner's guardrail rows 1 to 3.
- **R65's part 6:** its own plugin patch after R51 merges (choice 252).

## What the owner does
| When | Act |
|---|---|
| Now | Merge #324 when `Framework checks` is green on its final head. |
| After #324 | Merge this PR when `Framework checks` is green on its final head. |
