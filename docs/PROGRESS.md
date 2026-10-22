# Progress — ROADMAP R65's part 2: `python tasks.py choices-index` and `docs/progress/choices.md` (2026-10-22)

This session ran on branch `claude/r65-part-2-choices-index`. It is the same session as R65's part 1 (#324), and the owner asked it to start part 2 once #323's merge was checked. Part 2 is built as the owner accepted it: choice 252, point 3, and `docs/proposals/one-owner-per-fact.md`, part 2. It is a documentation and `tasks.py` PR with no plugin version, and nothing under `plugin/` or `template/`.

**This branch is built on #324's branch**: the task reads choices with part 1's `choice_items`. Its diff against `main` holds #324's commits until #324 merges. The owner merges #324 first.

The previous record (R65's part 1, from #324) is now `docs/progress/2026-10-22-r65-part-1-next-free.md`, unchanged (verified, `cmp` against `claude/r65-part-1-next-free:docs/PROGRESS.md` at `c87725b`). This session's end file is `docs/handoffs/sessions/2026-10-22-claude-r65-part-2-choices-index.md`.

## Coordination with the other sessions
- **#323 merged** as `50eea3b` after part 1 was opened. It added only the previous session's end file (verified, `git diff --stat 30b0367 50eea3b`). `main` is merged into #324's branch, and so into this one; no file conflicted.
- **Numbers.** This PR takes choice 253, for the owner's answer below, and nothing else. `python tasks.py next-free` on `50eea3b` printed choice 253, candidate R66, note 58, decision 39 and patch 1.0.24, none taken above `main` (verified again after `git fetch` at 22:20 UTC, before taking it).
- **Open PRs**, read after #323 merged: #324 (part 1) and #173 (intent 0004).

## The owner's decision (2026-10-22)
253. **The sources-of-truth session's nine decisions are taken as this session reviewed them** (the owner, "all as in your verdicts", on this session's independent review of the table that session `ccr-aaab8db4-pn5lsc` gave at 21:44 UTC, plus four rows of its own):
    1. what to build next: done, as R65's parts 1 (#324) and 2 (this PR);
    2. R65's part 4 ships `python tasks.py verify` and check 13 in one PR, before the owner's guardrail rows. Check 13 passes on the day it merges, because `CLAUDE.md:54` and `sdlc.yaml:21` hold the same build command today (verified, both read on `50eea3b`). The rows then change both lines together, under check 13. Part 4 adds no new copy of the command list;
    3. the owner's rows 1 to 4 go in one guardrail PR after part 4. Row 4 cites `docs/notes/11.md`, not "NOTES §11" (the table below);
    4. CI runs `python tasks.py verify` from part 4 on, keeping the Windows shards (`FRAMEWORK_TEST_SHARD`). Low priority: docs-lint already runs in CI inside pytest, so only `compileall` and `claude plugin validate` are missing there;
    5. `docs/OPERATING_MODEL.md:28` keeps choice 251 written out, pinned by `tests/test_commands_and_skills.py:800-802`. The study's section 2 row is annotated in R65's part 3 PR, not in part 1's;
    6. "profile-based human gates" (S1 to S4) is fixed in R65's part 3, as the accepted proposal already says. The same PR annotates the study's line that gave "the next plugin PR";
    7. the API-merge gap is closed first by a deny rule. The owner adds `mcp__github__merge_pull_request` and `mcp__github__enable_pr_auto_merge` to `.claude/settings.json` (the table below), and a session checks live that it binds. A candidate for projects, written for the template only, comes after that check, at the number `python tasks.py next-free` gives then. If the rule does not bind, the gap is recorded as a known limit;
    8. the sample's row 5 and its pin move ride the sample's next upgrade PR (not verified here: the sample is outside this session's scope);
    9. the owner deletes the sample's branch `ccr-76f1ceba-idf2w0` and this repository's `ccr-bc5e88a0-y1pwjg`, `luissiviero-patch-1` and `ccr-b3531dc9-oioi5k`. The first two of this repository are ahead of `main` with no open PR, and the third is merged (#235) (verified, `git rev-list` after `git fetch`);
    10. #324 merges before this PR;
    11. check 10's cutover stays the build date, 2026-10-22;
    12. `docs/progress/choices.md` keeps the line number: a PR that edits a record runs `python tasks.py choices-index`;
    13. R65's ROADMAP row gets its status annotation once, when part 5 merges. The order change of point 2 is annotated now, beside part 4 in the row and in the proposal.

## What was built
1. **`python tasks.py choices-index`.** It writes `docs/progress/choices.md` from the records, one row per choice: the number, the record and line as a link, and the item's first sentence.
   - A choice is what docs-lint check 10 reads: a top-level item under a heading that states choices.
   - The first sentence is the item's first bold phrase, because every record leads its choices with one. 236 of the 237 items open with it; choice 168 opens with an italic note and then the bold phrase. An item with no bold phrase gives its first sentence.
   - Links are reduced to their text, and a bar is escaped for the table.
2. **docs-lint fails a stale or missing index** ("docs/progress/choices.md differs: run python tasks.py choices-index"), as it does for the decisions and the notes.
3. **The two generated pages beside the records** (`index.md`, `choices.md`) are no longer read as records, by check 10 or by `next-free`.
4. **The first index**: choices 16 to 252, 237 rows. Choices 1 to 15 are named in its opening as kept in git history only (`fe20f6a`, `57db1b3`), as #324's record found. `docs/progress/index.md` gains one sentence saying `choices.md` is not a record.
5. **Tests.** Three in layer 1 (the summary, the rows and their links, a stale or missing index each way) and one in layer 2 (the index on disk is what the task writes).

## Points this PR left to the owner, now settled
- **A line number moves with every edit above it.** A PR that edits `docs/PROGRESS.md` above a choice, or moves it to `docs/progress/`, changes the index, and docs-lint names the task to run. Two parallel PRs that both take a choice already conflict in `docs/PROGRESS.md`; the index adds one generated file, resolved by running the task. Kept (choice 253, point 12).
- **ROADMAP R65's row is not annotated per part.** Its Status says "accepted" until all six parts are built; one annotation when part 5 merges (choice 253, point 13).

## Proposed edits for the owner
Rows 1 to 4 replace those of choice 252's record (`docs/progress/2026-10-22-sources-of-truth-study-r65-choice-252.md`) after R65's part 4 merges, in one PR. Row 4 now cites the note's file. Row 5 is new and can come now; a session then checks live that it binds (choice 253, point 7).

| Link | Row | What is there now | What it must become |
|---|---|---|---|
| [CLAUDE.md](https://github.com/luissiviero/sdlc-framework/blob/main/CLAUDE.md?plain=1#L8-L11) | 8-11 | the Test and Lint lines, the task runner line, the "Run tests and lint" line | `- Task runner: python tasks.py <task> — must work on Windows and Linux; python tasks.py verify runs every check a PR needs (HANDOFF.md, standing precondition 1)`, line 11 unchanged; the Test and Lint lines live once, under "Verifying your work" |
| [CLAUDE.md](https://github.com/luissiviero/sdlc-framework/blob/main/CLAUDE.md?plain=1#L54) | 54 | ``- Build: `python -m compileall -q plugin tests tasks.py` (must finish with no output and exit code 0)`` | ``- Build: `python -m compileall -q plugin tests tasks.py .github/scripts` (must finish with no output and exit code 0)`` |
| [sdlc.yaml](https://github.com/luissiviero/sdlc-framework/blob/main/sdlc.yaml#L21) | 21 | `  build: "python -m compileall -q plugin tests tasks.py"` | `  build: "python -m compileall -q plugin tests tasks.py .github/scripts"` |
| [CLAUDE.md](https://github.com/luissiviero/sdlc-framework/blob/main/CLAUDE.md?plain=1#L34) | 34 | `- Events caused by the CI workflow token do not start workflow runs (except workflow_dispatch / repository_dispatch): …` | the same, with `; docs/notes/11.md` after `repository_dispatch` |
| [.claude/settings.json](https://github.com/luissiviero/sdlc-framework/blob/main/.claude/settings.json#L14) | 14 | `      "Bash(wget *)"` | `      "Bash(wget *)",` then `      "mcp__github__merge_pull_request",` then `      "mcp__github__enable_pr_auto_merge"` |

## Left
- **R65's parts 3 to 5:** one session PR each, in the row's order. Part 3 also carries the study's two annotations (choice 253, points 5 and 6). Part 4 ships `verify` and check 13 together, and CI moves to `verify` (choice 253, points 2 and 4).
- **The live check of row 5**, then the template candidate or the known limit (choice 253, point 7).
- **R65's part 6:** its own plugin patch after R51 merges (choice 252).

## What the owner does
| When | Act |
|---|---|
| Now | Merge #324 when `Framework checks` is green on its final head. |
| After #324 | Merge this PR when `Framework checks` is green on its final head. |
| Now, any time | Row 5 above (the merge-tool deny rule). Delete the four branches of choice 253, point 9. |
| After R65's part 4 merges | Rows 1 to 4 above, in one PR. |
