# Progress — the parallelism inventory, report only (2026-10-23)

This session ran on branch `claude/parallelism-inventory`, from `main` at `d80981a` (#346). It is a documentation PR: no plugin version, no file under `plugin/` or `template/`, no number taken.

## What was written
1. **`docs/reviews/2026-10-23-parallelism-inventory.md`**: every mechanism that runs work in parallel or keeps it from colliding, inside a project's pipeline (18 rows) and in this repository's own lanes (8 rows), with where each is defined, its status and its limits; the clashes of waves 1 and 2; the gaps a pipeline-level central session would fill and where each part would live; four options judged against the owner's weights; a recommendation and five questions for the owner.

## How it was checked
- Three read-only sub-agents did the wide searches; this session re-read a sample of their anchors at the source and corrected one path (`plugin/state/gitops.py`). Every citation in the review was opened and compared with its sentence (choice 241); the lines on #352's branch were read at `2faa553`.

## Found on the way
- `docs/handoffs/central-session.md:38` on #352's branch says `version-check` and check 10 refuse a number two branches took; neither does while both branches are open (`tasks.py:1315-1316`, `:1542-1551`).
- `docs/proposals/concurrent-changes.md:28` ("Nothing is built") and `docs/proposals/weekly-window-guarded.md:110` ("the framework runs one change at a time") are stale.

## What the owner does
| When | Act |
|---|---|
| Now | Merge this PR when `Framework checks` is green on its final head. |
| When you choose | Answer the five questions at the end of the review. |
