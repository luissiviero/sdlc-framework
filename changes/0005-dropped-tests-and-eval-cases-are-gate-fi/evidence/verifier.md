**Commands run** (read, not run — CI session, `SDLC_GATE_COMMANDS=runner` is set; per the verifier brief the build/test/lint targets and the test runner are never started in this session)

- `changes/0005-dropped-tests-and-eval-cases-are-gate-fi/evidence/gate-c.json` (the phase before mine, phase (c)) — `commands` check: `ok: true`, `details.ran_by: "runner"`:
  - build: `python -m compileall -q plugin tests tasks.py` → exit 0, output `""`
  - test: `python -m pytest` → exit 0, output ends `"1694 passed in 301.22s (0:05:01)\n"`
  - lint: `python -m ruff check . && python -m ruff format --check .` → exit 0, output `"All checks passed!\n206 files already formatted\n"`
  - All other gate-c.json checks are `ok: true` (limits, clean_tree, artifacts, open_concerns, panel, evidence, findings, plan_sync, guardrails, risk_list, owner_actions, test_lock, adversarial_review). `result: "continue"`, no `details.deferred: true` anywhere.
- `evidence/build.log`, `evidence/test.log`, `evidence/lint.log` (phase d, this session's own evidence folder) — each file's first line reads `"# <command> — deferred to the runner — 2026-10-16T19:00:08Z"`. This is **not a failure**: this session's `evidence/collect.py` run wrote these minutes ago in deferred mode; the runner replaces them after this session with the real output.

**Behavior exercised** (direct calls only, no git subprocess beyond read-only inspection, no `.env*` touched — confirmed safe, no sandbox denial)

Imported `plugin/gate/diff.py`, `plugin/gate/checks.py`, `plugin/state/unpark.py`, `plugin/pr/description.py` directly and called the pure functions with constructed inputs matching spec.md's Acceptance cases:

- `dropped_test_files`: a `D` under `tests/**/*.py` → `['tests/test_foo.py']` (hit); an `R` from a matching glob to another matching glob → `[]` (not a drop); an `R` from a matching glob to a non-matching path → `['tests/test_foo.py']` (hit). Matches spec's rename rule exactly.
- `diff.parse_name_status`: confirmed the parser strips git's similarity-score suffix (`"R100"` → status `"R"`); re-run with the parser's actual single-letter output matched spec in every case.
- `dropped_eval_cases`: whole case emptied (no survivor) → `['evals/cases/case1/']`; partial multi-file deletion with a surviving sibling → `[]` (not a drop); dot-prefixed rename destination → `['evals/cases/case1/']` even with a surviving sibling (independent of the survivor rule, per panel decision #1); internal move within the case folder → `[]`. All four match spec.md's Design/Acceptance exactly.
- `_declared_ratchets` / `art.planned_files` / `hooks.plan_sync.is_planned`: a Proof line `- ratchet: evals may fall, because ...` declares `{'evals'}`; an unrecognized `- ratchet: docs ...` line is correctly inert (not in `{tests, evals}`); a directory path `evals/cases/case1/` listed in "## Files that change" with trailing slash is matched via the `probe = f"{path}."` convention, an undeclared sibling `case2/` is not.
- `plugin/state/unpark.py: risk_hits` — `RISK_HIT_CHECKS = ("risk_list", "ratchets")`; source confirms it unions both checks' `details.hits` keys from the gate JSON.
- `plugin/pr/description.py: _conformance_line` — with `ratchets.details.declared` non-empty at phase (c): `"diff matches plan.md; declared drops: tests/x.py (plan)"`; with `declared: []`: `"diff matches plan.md"` (clause correctly omitted); at phase (d) with declared present, same clause appended.
- `_added_lines` (skip-marker scan): a unified diff adding `@pytest.mark.skip(...)` correctly reports `(file, line, content)` at the right new-file line number.
- Checked `CHECKS_BY_PHASE`: `check_ratchets` present in (c), (d), (e) tuples, absent from (a), (b), (f) — matches spec.

**Static cross-checks**

- `.claude-plugin/plugin.json` and `marketplace.json` both at `1.0.2` (equal, per decision 8).
- Diff vs `main` touches exactly the files plan.md's "Files that change" lists (`.claude-plugin/{plugin,marketplace}.json`, `docs/OPERATING_MODEL.md`, `docs/PROGRESS.md`, `plugin/agents/adversarial-reviewer.md`, `plugin/gate/{checks,diff}.py`, `plugin/pr/description.py`, `plugin/skills/plan-template/SKILL.md`, `plugin/state/unpark.py`, `template/REVIEW.md`, and the six `tests/test_*.py` files) — nothing extra, nothing missing; `framework/` and the root `REVIEW.md` are untouched, matching plan.md's "Not touched" list.
- `docs/PROGRESS.md` carries the exact proposed table row (file/line/before/after) for the owner's root `REVIEW.md` edit, as spec.md requires (never writing the guardrail itself).
- Every test name plan.md's Proof section lists exists in `tests/test_gate.py`, `tests/test_state.py`, `tests/test_pr.py`, `tests/test_agents.py`, `tests/test_commands_and_skills.py`, `tests/test_templates.py`.
- Prose additions present and on-point: `adversarial-reviewer.md` angle 7 ("Skip markers"), `plan-template/SKILL.md`'s `- ratchet: <name> may fall, because <why>` item form, `template/REVIEW.md`'s new skip-marker bullet, `docs/OPERATING_MODEL.md` §3/§6 clauses naming `ratchets`.
- `status.yaml`: `phase: d`, `gate.phase: c`, `gate.result: passed` — consistent with being at the start of phase (d).

**Mismatches with plan.md / spec.md**

None found.

**Verdict**

matches the plan
