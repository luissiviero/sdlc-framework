# Progress — note 58: the merge-tool deny rule binds a cloud session; the `gh` path left open (2026-10-23)

This session ran on branch `claude/note-58-merge-deny`, from `main` at `26f03c1` (#336), rebuilt on #337's branch (`2cea05e`) so that it follows choice 259. It is the session of R65's parts 1 to 5. The owner said "Continue" after part 5 merged.

The next step the newest session files name for a session was the live check of the owner's merge-tool deny rule (choice 253, point 7), once #328 merged. It merged, and this PR records the check as note 58. It is a documentation PR: no plugin version, no file under `plugin/` or `template/`.

Under choice 259 (#337), this record is a file of its own, named as the session's end file, `docs/handoffs/sessions/2026-10-23-claude-note-58-merge-deny.md`. `docs/PROGRESS.md` and `docs/progress/index.md` are not edited.

## Coordination with the other sessions
- **Numbers.** This PR takes note 58 and nothing else. `python tasks.py next-free` on `26f03c1` printed note 58, none taken above `main`, read at 02:52 UTC.
- **Read before writing:**
  - the newest session file, `2026-10-23-ccr-b2d02bf7-9ywgjn.md` (#336);
  - the Gemini session's end file, which it builds on (#335).

  Their next steps are R5's check (choice 257) and this live check; this PR does the second.
- **Open PRs**, read at 03:00 UTC on `26f03c1`: #173 and #337 (choice 259, one record file per session). This PR is built on #337's branch, so the owner merges #337 first.

## What was checked
- **The deny rule binds** (verified, note 58).
  - Before the rule reached this session's checkout, both merge tools were in its tool list.
  - Once the checkout held `main` at `26f03c1`, the harness withdrew both. `ToolSearch` returns the other GitHub tools but not these two.
  - The user-level settings deny neither, so the project file is the rule's only source.
  - The session never called a merge tool.
- **The `gh` path is not verified** (note 58). In this container `gh` reads GitHub through the session's proxy (`gh run view` worked), although its own token is invalid. Whether it could merge is not known: the only test is a merge attempt, which this session did not make. Its read of `gh api user` was denied by the permission system, and the session did not work around that.

## Proposed edits for the owner
One row, recommended, closing the `gh` path the same way. After it merges, a session checks live that a `gh pr merge` command is refused before it runs.

| Link | Row | What is there now | What it must become |
|---|---|---|---|
| [.claude/settings.json](https://github.com/luissiviero/sdlc-framework/blob/main/.claude/settings.json#L16) | 16 | `      "mcp__github__enable_pr_auto_merge"` | `      "mcp__github__enable_pr_auto_merge",` then `      "Bash(gh pr merge *)",` then `      "Bash(gh api *)"` |

`Bash(gh api *)` is denied whole, because a merge through `gh api` hides in its arguments. Sessions read GitHub with the GitHub tools, and `gh run view` stays allowed.

## Left
- **R5's check** (choice 257): the framework checks refuse a pull request that bumps `plugin.json` to a version whose tag already exists. One documentation and `tasks.py` PR, outside the ranks.
- **The template candidate** (choice 253, point 7): with the rule shown to bind, a candidate for projects comes next, at the number `python tasks.py next-free` gives then.
- The rest as the end file lists it.

## What the owner does
| When | Act |
|---|---|
| Now | Merge #337, then this PR when `Framework checks` is green on its final head. |
| Now, recommended | The row above (the `gh` path). |
