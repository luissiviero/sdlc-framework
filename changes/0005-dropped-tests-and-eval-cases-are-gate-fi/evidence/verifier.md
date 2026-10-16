# Verifier Report — Change 0005, Phase (c)

## Commands run

Per the CI-session rule, the build/test/lint targets were not run in this session. Read, not run, from `changes/0005-dropped-tests-and-eval-cases-are-gate-fi/evidence/gate-b.json` (the record of the phase before mine — phase (b) — `ran_by: runner`, no `deferred: true` on any check):

- `python -m compileall -q plugin tests tasks.py` — exit code 0, output: `""`
- `python -m pytest` — exit code 0, tail: `"1618 passed in 297.33s (0:04:57)\n"`
- `python -m ruff check . && python -m ruff format --check .` — exit code 0, output: `"All checks passed!\n200 files already formatted\n"`

No `evidence/test.log`, `build.log` or `lint.log` exist yet in this change's evidence directory (consistent with the brief: those logs are written at phases (d) and (e), not (c)), so there is nothing to quote a first line from. `gate-c.json` exists but was deliberately not read, per instructions (it is an earlier fix round's stale record).

## Behavior exercised

I did not run the test runner (`pytest -k ...`) — disallowed in this CI session. Instead I called the changed code directly in small Python scripts, the way its real caller (`gate.build_context` + `check_ratchets`) does, against a disposable git fixture repo I built under `$TMPDIR` (never touching any tracked file):

- `plugin/gate/diff.py: parse_name_status` / `name_status` — a synthetic `--name-status -M -z` blob with a plain `D`, an `M`, and an `R100` rename parsed into the correct typed records (confirmed field-by-field).
- `plugin/gate/checks.py: dropped_test_files` (pure) — a `D` under `tests/**` reported; an `M` ignored; a rename within `test_paths` not reported; a rename out of `test_paths` reported; a rename into `test_paths` not reported. All five match spec.
- `plugin/gate/checks.py: dropped_eval_cases` (pure) — a fully-deleted case reported; a dot-prefixed rename reported; a partial deletion with a surviving sibling (via a plain survivor-path argument) *not* reported; an internal move within one case folder not reported.
- `check_ratchets` end-to-end, built via `gate.build_context(root, "0001", "c")` on a real git fixture (base commit on `main`, work on a `scenario` branch — mirroring `tests/test_gate.py`'s own `_ratchet_repo` pattern):
  - Undeclared test-file drop → fails, `details.hits["ratchet: tests"] == ["tests/test_keep.py"]`.
  - Same drop declared in the **approved** (merge-base-committed) plan's "## Files that change" → `ok`, `details.declared == ["tests/test_keep.py (plan)"]`.
  - Same drop declared via a pre-approved `- ratchet: tests may fall, because ...` Proof line → `ok`.
  - Drop and plan-declaration committed together in the *same* branch commit (plan never updated at the merge base) → still fails with the same hit — confirms the check reads `ctx.approved_artifact("plan.md")`, not the working tree, exactly as spec's "riskiest step" requires.
  - Rename within `test_paths` → `ok`. Rename out of `test_paths` → fails, same hit shape.
  - Eval case folder fully emptied at HEAD → fails, `"ratchet: evals": ["evals/cases/bar/"]`. Partial deletion with a surviving sibling → `ok`. Dot-prefixed rename of a case folder → fails the same way.
  - An undeclared drop with `status.yaml: risk_accepted: ["ratchet: tests"]` recorded → `ok`, `details.accepted == ["ratchet: tests"]`.
  - A Proof line declaring an unrelated/unknown ratchet name (`- ratchet: docs may fall...`) → does not excuse the real, undeclared `tests` drop (inert, as spec's open question 4 answers).
  - Adding a line containing `@pytest.mark.skip` with no drop → `ok` stays true, and the hit appears in `details.skip_markers` (file, line, token) — confirms the scan never affects `ok`.

I also read (but, per the coordinator's instruction to stop, did not separately execute) `plugin/state/unpark.py: risk_hits` (`RISK_HIT_CHECKS = ("risk_list", "ratchets")`, union of both checks' `details.hits` keys) and `plugin/pr/description.py: _conformance_line` (appends `"declared drops: ..."` from the `ratchets` check's `details.declared` at (c)/(d)/(e) only). Both read exactly as spec/plan describe, and I verified `CHECKS_BY_PHASE` by direct source inspection: `check_ratchets` is present in the `"c"`, `"d"`, `"e"` tuples and absent from `"a"`, `"b"`, `"f"`. I did not execute a live call to `risk_hits` or `_conformance_line`, nor the `risk_list`-vs-`ratchet` separate-hit-key scenario (`test_ratchets_risk_list_tests_configured_does_not_satisfy_ratchet_hit`) with a real `sdlc.yaml: risk_list: ["tests"]` config — these remain **untested by me**, confirmed only by reading the implementation, not by running it.

## Mismatches with plan.md / spec.md

None found in anything I executed. Every behavior I ran — the diff parser, both pure drop-rule functions, `check_ratchets`'s declaration/acceptance/rename/partial-delete/dot-rename/skip-marker paths, and the approved-plan-vs-working-tree distinction (plan.md's "riskiest step") — matched spec.md's Requirements/Design and plan.md's Proof list exactly.

Untested (not a mismatch, just unverified by direct execution in this session): `unpark.py: risk_hits`'s union behavior, `_conformance_line`'s declared-drops clause rendering, and the `risk_list`/`ratchets` separate-hit-key non-interference case — all read as correct in source but not exercised live.

## Verdict

**matches the plan** — qualified: based on (a) the phase-(b) gate record showing build/test/lint green with no deferral, and (b) direct execution of the core `check_ratchets`/`diff.py` behavior across eleven scenarios, all consistent with plan.md and spec.md. The three items noted above as untested were reviewed by reading only, not run, due to the turn-limit instruction to stop and report.
