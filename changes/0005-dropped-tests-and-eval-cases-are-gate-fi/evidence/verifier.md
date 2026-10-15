# Verifier (phase c, build)

**Commands run** (CI session — `SDLC_GATE_COMMANDS=runner` set; build/test/lint not run in
this session, per instructions — read, not run)

Read from `changes/0005-dropped-tests-and-eval-cases-are-gate-fi/evidence/gate-b.json`'s
`commands` check (the record of the phase before mine, `details.ran_by: "runner"`,
`ok: true`):

- `python -m compileall -q plugin tests tasks.py` — exit 0, output: `""`
- `python -m pytest` — exit 0, tail: `..................................  [100%]\n1618 passed in 297.33s (0:04:57)`
- `python -m ruff check . && python -m ruff format --check .` — exit 0, tail: `All checks passed!\n200 files already formatted`

No `details.deferred: true` on gate-b.json's `commands` or `evidence` checks.
`evidence/build.log`, `evidence/test.log`, `evidence/lint.log` do not exist yet in this
change's evidence directory (those are written at phases (d)/(e) per the runner's schedule,
not (c)), so there is nothing to quote a first line from.

`changes/.../evidence/gate-c.json` was not used as a verdict source (that record is this
phase's own earlier round, predating this build session's work); it was only glanced at to
confirm it also shows `commands: ok: true` from an earlier run, consistent with gate-b.json.

**Behavior exercised**

Called the new pure functions directly via `python -c` (no pytest, no `.env*` read):

- `dropped_test_files`: a `D` under `tests/**` → reported; a rename within `test_paths` →
  not a drop; a rename out of `test_paths` → reported (the source path); a non-test-path `D`
  → not reported.
- `dropped_eval_cases`: a folder emptied at HEAD → reported; a partial, multi-file deletion
  with a surviving sibling → not reported; a rename to a dot-prefixed folder name (the old
  name losing its last survivor) → the old name reported, the new hidden name not re-reported.
- `skip_marker_hits` on a synthetic patch adding `@pytest.mark.skip` to a `tests/test_x.py`
  file → listed with file and line; never affects `ok`.
- Declaration helpers (`RATCHET_PROOF_RE`, `_ratchet_path_declared`): a Proof line declaring
  `tests` matches only `tests`, not `evals`; a plan-declared test-file path and a
  directory-with-trailing-slash eval-case declaration both resolve `True`; an undeclared case
  resolves `False`.
- Neighboring flow 1 — `plugin.pr.description._conformance_line`: with `details.declared`
  non-empty → `"diff matches plan.md; declared drops: ratchet: tests (plan)"`; empty → the
  clause is absent.
- Neighboring flow 2 — `plugin.state.unpark.risk_hits`: a gate record with only a failing
  `ratchets` check → `['ratchet: tests']`; both `risk_list` and `ratchets` failing → the
  union of both keys.
- `CHECKS_BY_PHASE` membership confirmed: `check_ratchets` present in `"c"`, `"d"`, `"e"`;
  absent from `"a"`, `"b"`, `"f"`.
- One input just outside the Acceptance section's named cases: a dropped file matching no
  `test_paths` glob and outside `evals/cases/` returns `[]` from `dropped_test_files` —
  correctly out of this check's scope (`design_scope`'s concern, not `ratchets`'s).

**Mismatches with plan.md / spec.md**

None found in the behavior exercised.

**Verdict**

matches the plan
