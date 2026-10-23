# Progress — `next-free` names the next choice on main; two leftovers of choice 266 (2026-10-23)

This session ran on branch `claude/next-free-no-gap`, restarted from `main` at `2a4a867` (#356, which merged its earlier branch `claude/r66-follow-up`). It changes `tasks.py`, its tests and one proposal; no file under `plugin/` or `template/`, no plugin version.

## The owner's choices
267. **The three leftovers of choice 266 are fixed** (the owner, 2026-10-23, this session: "Fix them", on the list of three items that #356's record left open):
   - `python tasks.py next-free` and check 10's no-gap test agree on a choice number;
   - `docs/proposals/weekly-window-guarded.md:110` gets a dated annotation;
   - `HANDOFF.md`'s line on `version-check` is brought up to date, in a PR of its own (the page changes only that way).

## What was built
1. **`next-free` names the next choice on `main`.** When the next choice on `main` is held only by branches ahead of it, `next-free` adds one line: "choice N is next on main and held by <branches>: main's choices run without a gap, so a PR that merges before them takes N, one that merges after them M; the later renumbers". `test_the_repository_takes_no_number_twice` requires main's choices to run from 16 without a gap; notes, decisions, candidates and versions may have gaps, so only choices get the line (`GAPLESS_KINDS`). The number above every branch stays the one printed in the list, since it is right for a PR that merges after the others. New: `next_on_main`, `gap_notes`, `_one_above`; two tests in `tests/test_next_free.py`.
2. **`weekly-window-guarded.md:110`**: a dated annotation beside "the framework runs one change at a time", which the per-branch concurrency groups and R51 contradict; the sentence's other reason (dollars, not agent-hours) stands.

## The other PR
- `HANDOFF.md`, standing precondition 1: "a branch that bumps the plugin to a version `main` holds or a tag has fails; choice 257" becomes "… a version `main` holds, a tag has or a fetched open branch took first fails; choices 257 and 266", in a PR of its own (branch `claude/handoff-version-check`).

## What the owner does
| When | Act |
|---|---|
| Now | Merge this PR and the `HANDOFF.md` PR, each when `Framework checks` is green on its final head; either order. |
