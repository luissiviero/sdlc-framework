**Commands run** (CI session — build/test/lint not run directly; read from the runner's record)

Per the brief, for phase (c) the record to read is `evidence/gate-b.json` (phase before mine). `evidence/test.log`, `evidence/build.log`, `evidence/lint.log` are not present in `changes/0003-lessons-with-frontmatter-and-a-generated/evidence/` (none to quote; not "deferred" placeholders either, simply absent at this point).

From `changes/0003-lessons-with-frontmatter-and-a-generated/evidence/gate-b.json` (`commands` check, `details.ran_by: "runner"`, `ok: true`):
- `build`: `python -m compileall -q plugin tests tasks.py` — exit 0, output `""`
- `test`: `python -m pytest` — exit 0, tail: `.................................  [100%]\n1401 passed in 296.73s (0:04:56)\n`
- `lint`: `python -m ruff check .` — exit 0, output `All checks passed!\n`

No `details.deferred: true` on this record; gate-b itself resolved `"result": "wait"` (human gate, label `sdlc:b-ready`) with every check `ok: true`, including `commands`, `artifacts`, `design_scope`, `open_concerns`, `panel`, `guardrails`, `risk_list`, `owner_actions`, `adversarial_review`. This is a prior phase's green record, read not run, per the CI-session rule.

**Behavior exercised** (direct script/CLI calls only, no `.env*`, no test runner)

1. `plugin/lessons/index.py build`/`check` against a scratch `lessons/` tree (`/tmp/claude-1001/verify0003`) with: two lessons sharing a class spelled three ways (`Flaky Test`, `flaky-test`) → correctly merged into one normalised heading `## flaky-test`, newest-first ordering (Feb before Jan), stale marker applied only to the lesson whose `stale_after` (2025-01-01) is before `--today` (2026-10-08); a frontmatter-less file → routed to `## Unsorted` with a `## Unsorted: <file>: no frontmatter block` note, no crash.
   - `check` on the freshly built index: exit 0, no diff.
   - `check` after hand-editing the index to garbage: exit 1 with a correct unified diff (`lessons/index.md (on disk)` vs `(built)`).
   - `check` against a CRLF copy of the correct index: exit 0, no diff (confirms the universal-newline tolerance spec.md requires).
2. `plugin/gate/checks.py:lesson_and_eval` called directly with a hand-built `GateContext`/`Status` (no pytest):
   - Full pass case (`entry_route="incident"`, `phase="e"`, a complete lesson file matching the glob plus `evals/cases/<id>-<slug>/{prompt.md,checks.yaml}` plus a clean `index.py check`): `ok=True`, `reason="the lesson, its frontmatter and the eval case are all present"`.
   - `phase="f"` with the same `entry_route="incident"` and a nonexistent root: `ok=True`, `reason="not an incident change at gate (e): nothing to check"` — the guard short-circuits before touching the filesystem, confirming the plan's "never runs at gate (f)" requirement by direct call, not just by registration.
   - Missing lesson file: `ok=False`, `need="no lesson file matches lessons/[0-9][0-9][0-9][0-9]-[0-9][0-9]-missing-lesson.md"`.
   - Dangling `supersedes` target: `ok=False`, `need="2026-10-supersede-slug.md: supersedes target '2026-01-earlier.md' does not exist"`.
3. Read `plugin/gate/artifacts.py`'s new constants (`LESSON_REQUIRED_FIELDS`, `LESSON_STATUSES`, `lesson_glob`, `EVAL_PROMPT`, `EVAL_CHECKS`) and confirmed the field list is exactly spec.md's Requirements-bullet-one set minus `runbook`/`supersedes`/`retired_by`, and `CHECKS_BY_PHASE["e"]` carries `lesson_and_eval` while `CHECKS_BY_PHASE["f"]` does not (matches plan.md's step 2 and spec.md's registration requirement).

**Mismatches with plan.md / spec.md**
- none found in the behavior exercised.

**Verdict**: matches the plan
