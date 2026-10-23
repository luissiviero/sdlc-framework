# Progress — ROADMAP R65's part 4: `python tasks.py verify`, docs-lint check 13, CI on `verify` (2026-10-22)

This session ran on branch `claude/r65-part-4-verify`, from `main` at `8bca5fd` (#327). It is the session of R65's parts 1 to 3 (#324, #325, #327). The owner asked it to continue in the same session. Part 4 is built as the owner settled it:
- choice 252, point 7;
- choice 253, points 2 and 4: `verify` and check 13 in one PR, before the owner's rows; CI on `verify`;
- `docs/proposals/one-owner-per-fact.md`, part 4.

It is a documentation, `tasks.py` and CI PR: no plugin version, nothing under `plugin/` or `template/`. The workflow it changes is this repository's own `framework-checks.yml`, which is not a template.

The previous record (R65's part 3 and choice 254, from #327) is now `docs/progress/2026-10-22-r65-part-3-checks-11-12-choice-254.md`, unchanged (verified, `cmp` against `8bca5fd:docs/PROGRESS.md`). This session's end file is `docs/handoffs/sessions/2026-10-22-claude-r65-part-4-verify.md`.

## Coordination with the other sessions
- **Numbers.** This PR takes none (`python tasks.py next-free` on `8bca5fd`: choice 255, none taken above `main`, read at 23:51 UTC).
- **Open PRs**, read at 23:51 UTC: #173 (intent 0004) and the owner's #328 (row 5 of choice 253's record). Neither touches a file this PR changes.

## What was built
1. **`python tasks.py verify`, the one owner of the local checks** (choice 252, point 7).
   - It reads `commands` from `sdlc.yaml` and runs build, lint, the docs lint, test, and `claude plugin validate .` when the CLI is on the path. It holds no list of its own (choice 253, point 2).
   - Each command is split at `&&` and run as argument lists, with `python` replaced by this interpreter, so the same line runs in cmd.exe, PowerShell and bash.
   - `python -m pytest` runs as `tasks.py test`: the same pytest, spread over the cores.
   - Every step runs, each verdict is printed, and one red step fails the task.
   - Its first live use, on this branch: build, lint, docs-lint, test (2354 passed) and plugin validate all "ok".
2. **docs-lint check 13.** The Build, Test and Lint lines under `CLAUDE.md`'s "Verifying your work" must quote `sdlc.yaml: commands` word for word. A line that is missing or differs fails. It passes on `main` today: `CLAUDE.md:54` and `sdlc.yaml:21` hold the same build command.
3. **CI runs `python tasks.py verify`** (choice 253, point 4).
   - Both jobs of `framework-checks.yml` changed, and the Windows shards keep `FRAMEWORK_TEST_SHARD`.
   - In CI, `claude plugin validate .` reports "not run": no CLI is installed there.
   - The two tests that pin the run line (`tests/test_templates.py`) follow the decision.
4. **`README.md:5`** names `verify`. The study's note that CI runs no `compileall` is annotated (choice 126).
5. **Tests.** The new `tests/test_verify.py`:
   - the commands read from `sdlc.yaml`;
   - the argument lists;
   - every step run, and a red one failing the task;
   - another test command run as written, and the CLI's validate;
   - check 13 each way;
   - this repository's lines (layer 2).

## Points to know
- **Until the owner's row 3, `verify` compiles `plugin tests tasks.py` only**, as `sdlc.yaml:21` says. `.github/scripts` joins when rows 2 and 3 change `CLAUDE.md:54` and `sdlc.yaml:21` together. Check 13 fails if only one of the two changes.
- **`CLAUDE.md`'s "Commands" lines (8 to 11)** are not read by check 13. The owner's row 1 removes their copies of the Test and Lint lines.

## Proposed edits for the owner
From choice 253's record, now due: rows 1 to 4, in one PR, after this PR merges. Row 5 is the owner's #328.

| Link | Row | What is there now | What it must become |
|---|---|---|---|
| [CLAUDE.md](https://github.com/luissiviero/sdlc-framework/blob/main/CLAUDE.md?plain=1#L8-L11) | 8-11 | the Test and Lint lines, the task runner line, the "Run tests and lint" line | `- Task runner: python tasks.py <task> — must work on Windows and Linux; python tasks.py verify runs every check a PR needs (HANDOFF.md, standing precondition 1)`, line 11 unchanged; the Test and Lint lines live once, under "Verifying your work" |
| [CLAUDE.md](https://github.com/luissiviero/sdlc-framework/blob/main/CLAUDE.md?plain=1#L54) | 54 | ``- Build: `python -m compileall -q plugin tests tasks.py` (must finish with no output and exit code 0)`` | ``- Build: `python -m compileall -q plugin tests tasks.py .github/scripts` (must finish with no output and exit code 0)`` |
| [sdlc.yaml](https://github.com/luissiviero/sdlc-framework/blob/main/sdlc.yaml#L21) | 21 | `  build: "python -m compileall -q plugin tests tasks.py"` | `  build: "python -m compileall -q plugin tests tasks.py .github/scripts"` |
| [CLAUDE.md](https://github.com/luissiviero/sdlc-framework/blob/main/CLAUDE.md?plain=1#L34) | 34 | `- Events caused by the CI workflow token do not start workflow runs (except workflow_dispatch / repository_dispatch): …` | the same, with `; docs/notes/11.md` after `repository_dispatch` |

## Left
- **R65's part 5:** `HANDOFF.md`'s skeleton points to `python tasks.py next-free`, and its precondition 1 to `python tasks.py verify` (choice 252, point 7). The same PR annotates R65's row once (choice 253, point 13).
- **The Gemini session**, once parts 1 to 5 have merged, before part 6 (carried from `2026-10-22-ccr-6ed8a82e-cxmftx-end.md`).
- **R65's part 6:** its own plugin patch after R51 merges (choice 252).
- **The merge-tool deny rule:** the owner's #328, then a live check (choice 253, point 7).

## What the owner does
| When | Act |
|---|---|
| Now | Merge this PR when `Framework checks` is green on its final head; merge #328. |
| After this PR merges | Rows 1 to 4 above, in one PR. |
