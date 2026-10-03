## Commands run

This is a CI session (`SDLC_GATE_COMMANDS=runner`), so per brief step 2 I did not run build/test/lint myself. I read the previous phase's gate record and the evidence logs instead.

**`changes/0001-split-the-large-docs-with-an-index-each/evidence/gate-b.json`** (phase (b), the phase before this one), `commands` check, `ok: true`, `details.ran_by: "runner"`:
- `python -m compileall -q plugin tests tasks.py` — exit 0, output `""`
- `python -m pytest` — exit 0, output ends `1293 passed in 218.86s (0:03:38)`
- `python -m ruff check .` — exit 0, output `All checks passed!`

No `details.deferred: true` anywhere in this record — it is a completed, green run.

**Evidence logs** (`build.log`, `test.log`, `lint.log` in this change's `evidence/`), first lines:
- `build.log`: `# python -m compileall -q plugin tests tasks.py — deferred to the runner — 2026-10-03T17:45:32Z`
- `test.log`: `# python -m pytest — deferred to the runner — 2026-10-03T17:45:32Z`
- `lint.log`: `# python -m ruff check . — deferred to the runner — 2026-10-03T17:45:32Z`

All three read "— deferred to the runner —", timestamped minutes before this session (this phase's own build session wrote these placeholders; the runner has not replaced them yet). Per the brief this is not a failure — it is reported as "deferred to the runner," not as a mismatch. No `gate-c.json` exists yet for this phase (expected: it is written after this run completes).

## Behavior exercised

Documentation-only change, so I exercised it as read-only path-resolution checks instead of running code:
- **Live-doc path checks**: `docs/ROADMAP.md`, `docs/OPERATING_MODEL.md`, `README.md` all repoint their `docs/DECISIONS.md`/`docs/NOTES.md` mentions to `docs/decisions/index.md`/`docs/notes/index.md`; `HANDOFF.md`'s "Read in this order" is index-first and every path it names (`docs/progress/session-17.md`, `session-15.md`, `2026-10-02-between-sessions-14-15-sitting-2.md`, `2026-10-02-change-0001-first-change.md`, `docs/notes/{30,29,27,25}.md`, `docs/decisions/{13,21,22,6,8,9}.md`) exists on disk. `docs/PROGRESS.md`'s own mention is correctly left unrepointed (its name/role is unchanged).
- **Index completeness**: `docs/notes/index.md` lists all 30 files (1–30, ascending); `docs/decisions/index.md` lists all 26 (1–26, ascending); `docs/progress/index.md` lists all 21 archived records in the right order, including the study record between sessions 12 and 13. `ls` confirms 30 note files, 26 decision files, 22 progress files (21 archived + index.md), matching the index counts exactly.
- **Citation resolution**: sampled `NOTES §11c` (`plugin/commands/sdlc-build.md` etc.) — resolves inside `docs/notes/11.md` (subsection `### 11c.` is physically present, confirming lettered subsections stay with the parent section). Sampled `decision 21`, `decision 22`, `decision 24`, `decision 25`, `decision 5`, `decision 6`, `decision 7`, `decision 12`, `decision 14` (`plugin/ci/run_phase.py`, `plugin/detect/bands.py`) — all resolve to existing `docs/decisions/<N>.md` files. Sampled literal `docs/NOTES.md section N` citations (`plugin/gate/limits.py`, `plugin/ci/auth.py`, `plugin/hooks/_common.py`, `plugin/init/sdlc_init.py`, `tests/test_substrate_smoke.py`) — these resolve through the `docs/NOTES.md` stub, which exists and points at `docs/notes/index.md`. Checked decision 18 specifically (spec's own example of an amendment): frontmatter correctly reads `status: amended`, `amended_by: 21`.
- **One input just outside scope**: `docs/BUILD_GUIDE.md` and `docs/handoffs/*` still carry old-style `NOTES §N` / `docs/DECISIONS.md` citations, deliberately unrewritten per plan.md's Risks/spec.md Requirements — confirmed these are still present and still resolve (through the stub or by number), exactly as the plan says they should.
- **PROGRESS.md current-record check**: `docs/PROGRESS.md` has exactly one top-level `# ` heading ("Session 18…"); this phase's own work was added as a `## Change 0001, phase (c)` subsection plus three rows in the "Guardrail lines for the owner" table (covering `CLAUDE.md` line 3, the new pointer line after line 3, and line 35; line 39 explicitly noted as needing no edit) — matching spec.md's Acceptance line (lines 3, 35, 39, plus the new pointer line).
- **Guardrail/scope check**: diffed this phase's build commits (`d5b7ab0^..1210a11`) — no file under `plugin/`, `template/`, `tests/`, `CLAUDE.md`, `.claude/**`, `REVIEW.md` or `sdlc.yaml` was touched by this change's own commits (the one `sdlc.yaml` version-bump line in the wider range came from a separate owner commit, `e2e2491`, not from this change). `hook-log.jsonl` shows zero `"verdict": "deny"` entries for this phase.

(Note: the sub-agent's own summary line said "20 archived / 21 total" for `docs/progress/`; the correct count, confirmed independently by the orchestrating session via `ls` and a full byte-for-byte diff against the pre-split `docs/PROGRESS.md`, is 21 archived files + `index.md` = 22 files. The count is corrected above; it does not change the verdict.)

## Mismatches with plan.md / spec.md

None found.

## Verdict

`matches the plan`
