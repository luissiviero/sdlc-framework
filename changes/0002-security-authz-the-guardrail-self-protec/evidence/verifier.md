# Verifier report — change 0002, phase (d) test

## Verification summary — read-only check

This is a CI session (`SDLC_GATE_COMMANDS=runner`), so per standing instructions the
verifier read the previous phase's recorded evidence instead of invoking the test/build/
lint targets itself.

**Commands read (not run — CI session)**
- `changes/0002-security-authz-the-guardrail-self-protec/evidence/gate-c.json` (the
  phase-before-this record; `head: 22697f2a...`, `phase: c`, `result: continue`, no check
  has `ok: false`, none carries `details.deferred: true`):
  - `build`: `python -m compileall -q plugin tests tasks.py` — exit `0`, output `""`
  - `test`: `python -m pytest` — exit `0`, tail: `"1609 passed in 299.88s (0:04:59)"`
  - `lint`: `python -m ruff check .` — exit `0`, output `"All checks passed!"`
  - `details.ran_by: "runner"` on all three.
- `changes/0002-security-authz-the-guardrail-self-protec/evidence/{build,test,lint}.log`
  (this phase's own, phase d): each first line reads
  `# ... — deferred to the runner — 2026-10-09T10:57:53Z` — written by this session's own
  evidence-collect step minutes ago; the runner replaces them after this session ends. Not
  a failure, not yet available.
- `status.yaml`: `phase: d`, `gate: {phase: c, result: passed}` — consistent with
  gate-c.json's green state.

**Behavior exercised**
- Diff `git diff $(git merge-base main HEAD) HEAD`: changed files are exactly plan.md's
  "Files that change" list — `plugin/hooks/shell_guard.py` (new, 985 lines),
  `plugin/hooks/hooks.json`, `plugin/ci/settings.ci.json`, `plugin/ci/run_phase.py`,
  `tests/test_hooks.py`, `tests/test_ci.py`, `tests/test_evals.py`,
  `docs/OPERATING_MODEL.md`, `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`
  (both `0.3.6`→`0.3.7`), plus the change's own `changes/.../evidence/*` and `status.yaml`
  (process artifacts, expected). No undeclared file.
- Read `plugin/hooks/shell_guard.py` in full: `shell_write_targets`/
  `_chain_parts_tokenized` is a standalone shlex-style tokenizer (no import from
  `production_gate.py`); `decide()` imports `protected_paths.protected_patterns`/
  `_check_one` and `test_file_lock.locked_change_id`/`is_locked`/`test_path_patterns`/
  `REASON` as spec.md Design requires; fail-closed path (`REASON_NONLITERAL`) on
  `$VAR`/`$(...)`/backtick/`~`/glob/brace/git-pathspec-magic and on `cd -`/bare `cd`/
  `popd` with a later write idiom; `git -C` resolved locally per chain part without
  leaking into later parts (matches spec.md Design's chain-part description and the fix
  history visible in git log).
- Read `plugin/hooks/hooks.json`: one new `Bash|PowerShell` matcher entry,
  `--plugin-root ${CLAUDE_PLUGIN_ROOT}`, `timeout: 30` — matches plan.md.
- Read `plugin/ci/settings.ci.json`: `sandbox.filesystem.denyWrite` =
  `[".claude", "framework", "CLAUDE.md", "REVIEW.md", "sdlc.yaml"]` — matches spec.md
  Requirements (directories named, not globbed).
- Read `plugin/ci/run_phase.py`'s new `_deny_write_entries`/`ci_settings_file` changes:
  rewrites denyWrite entries to absolute paths and appends `sdlc.yaml: protected_paths`
  plain entries, skipping globs/escapes/root — matches spec.md/plan.md.
- Grepped `tests/test_hooks.py`: ~45 new `test_shell_guard_*`/`test_shell_write_targets_*`
  tests covering the Proof section's list (guardrail file, plugin-root form,
  protected_paths entry, locked test file in fix fixture, PowerShell forms, cwd/`cd`/
  `pushd`/`Set-Location`/`git -C` resolution incl. the git-C chain-leak case, fail-closed
  cases including brace expansion/pathspec-magic/`popd`, negative list incl. `2>&1`/
  `> /dev/null`/heredoc blockquote, inner-shell recursion and wrapper words, hooks.json
  wiring test `test_hooks_json_registers_shell_guard_on_bash_and_powershell`).
- Grepped `tests/test_ci.py`:
  `test_ci_settings_file_rewrites_the_sandbox_filesystem_deny_write_list` (new) and
  `test_ci_settings_are_rendered_against_the_project_root` (updated) both present.
- Grepped `tests/test_evals.py`:
  `FRAMEWORK_SUITE = tuple(p.name for p in run.discover(FRAMEWORK_CASES))` — no longer a
  literal tuple, as plan.md step 5 specifies.
- Read `docs/OPERATING_MODEL.md` diff: layer (i) and (iii) sentences updated exactly as
  plan.md describes.
- Read `changes/.../evidence/adversarial-review-c.json` (head `22697f2`, verdict
  `continue`): independently re-traced two previously-escalated bypasses (git
  global-option-before-verb, inner-shell flag-before-`-c`) against the current source and
  confirmed both fixed; noted one disclosed non-blocking plan deviation (test imports left
  at module scope rather than inside test functions) and flagged that the previous
  `verifier.md` on disk was scoped to an earlier, superseded commit (`3a90bd0`), not to
  this round.
- Read the previous `changes/.../evidence/verifier.md`: confirmed it was stale (a
  re-verification note for commit `3a90bd0`'s `git -C` chain-leak fix, referencing
  `gate-b.json`), consistent with the adversarial review's observation — it was from an
  earlier round, not phase (c) proper, and is superseded by this report.

**Mismatches with plan.md / spec.md**
- None found in the diff, hook implementation, hooks.json wiring, CI settings/
  run_phase.py, or the test additions against plan.md's Files-that-change/Order-of-work/
  Proof and spec.md's Requirements/Design/Acceptance.
- Pre-existing, already-disclosed deviation (not new, not blocking): plan.md's
  Order-of-work step 1 asked for the `shell_guard` import inside test functions;
  `fix-response.md` round 5 discloses it remains at module scope. Noted, not a
  code-correctness issue.

**Verdict:** matches the plan. Build/test/lint evidence for phase (d) is currently
deferred to the CI runner (expected under `SDLC_GATE_COMMANDS=runner`) and not yet
available; the runner will replace `evidence/{build,test,lint}.log` after this session
ends.
