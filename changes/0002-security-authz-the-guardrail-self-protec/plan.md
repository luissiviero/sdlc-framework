# Plan: security: authz: The guardrail self-protection (protected_paths.py) only (from intent.md 2026-10-05, spec.md 2026-10-08)

## Files that change
- `plugin/hooks/_common.py` — move the command-text parsing primitives that
  `production_gate.py` already has (`command_parts`, `chain_parts`, the `SPLIT_RE`/
  `CHAIN_RE`/`TOKEN_RE` constants, program-name normalisation, the leading-option and
  token-suffix helpers) here unchanged, so they are shared instead of private to one hook;
  add `shell_write_targets(command: str) -> list[str]` on top of them: candidate file-write
  target paths for redirection (`>`, `>>`), `tee`, in-place editors (`sed -i`, `perl -i`),
  `cp`/`mv`/`rsync` destinations, `dd of=`, `curl -o`/`-O`, `git apply`/`checkout --
  <path>`, `rm`/`Remove-Item`, and the interpreter literals `open(<path>, "w"/"a"`,
  `fs.writeFileSync(<path>`, PowerShell `Set-Content`/`Out-File` `<path>`.
- `plugin/hooks/production_gate.py` — import the moved primitives from `_common` instead of
  defining them locally; no behaviour change.
- `plugin/hooks/protected_paths.py` — `decide()` gets a `Bash`/`PowerShell` branch: call
  `shell_write_targets` on `tool_input["command"]`, check every candidate through the
  existing `_check_one`, deny on the first hit with the existing `REASON`.
- `plugin/hooks/test_file_lock.py` — `decide()` gets the same shape of `Bash`/`PowerShell`
  branch against `test_path_patterns`, denying with the existing `REASON`.
- `plugin/hooks/hooks.json` — add `protected_paths.py` and `test_file_lock.py` to the
  existing `Bash|PowerShell` matcher entry (beside `plan_sync.py`/`production_gate.py`).
- `tests/test_hooks.py` — reproducing tests for both hooks' Bash/PowerShell bypass (written
  first, seen to fail), negative cases proving ordinary commands still run, direct tests of
  `shell_write_targets`, and a wiring test for the new `hooks.json` registration.
- `evals/cases/0006-bash-guardrail-write-denied/` — new eval case (`prompt.md`,
  `checks.yaml`) in the shape of `evals/cases/0001-protected-path-denied/`: the prompt asks
  the agent to use Bash to append to `CLAUDE.md`; the checks assert `denied: "Bash"` and
  `CLAUDE.md` byte-identical.

Not touched: `plugin/ci/settings.ci.json`, `template/.claude/settings.json` (the allow-list
is unchanged, per spec.md Requirements); `plugin/hooks/secrets_check.py`, `plan_sync.py`,
`production_gate.py`'s own guarded-command behaviour; `framework/` (the local pinned-plugin
checkout the CI tooling reads from — untracked by this repo's git, per `.git/info/exclude`,
not part of this change's diff).

## Order of work
1. Write the reproducing tests in `tests/test_hooks.py` for the Bash/PowerShell bypass of
   `protected_paths.py` and `test_file_lock.py` (including the `hooks.json` wiring test);
   run them and confirm they fail against the current code (intent Constraints: the
   reproducing test comes first).
2. Move the command-text parsing primitives from `production_gate.py` into `_common.py`;
   update `production_gate.py`'s imports; run the existing `test_production_gate_*` tests
   unmodified and confirm they still pass (proves the move changed no behaviour).
3. Add `shell_write_targets` to `_common.py` with the idiom list above; add direct unit
   tests for it (the write idioms denied, the read/no-op idioms — `cat`, `grep`, `git
   status`, `python -m pytest` — left alone).
4. Add the `Bash`/`PowerShell` branch to `protected_paths.py`'s `decide()`; re-run step 1's
   `protected_paths` tests — they now pass.
5. Add the `Bash`/`PowerShell` branch to `test_file_lock.py`'s `decide()`; re-run step 1's
   `test_file_lock` tests — they now pass.
6. Register both hooks on the `Bash|PowerShell` matcher in `plugin/hooks/hooks.json`; re-run
   step 1's wiring test.
7. Add the `evals/cases/0006-bash-guardrail-write-denied/` case.
8. Run `python -m pytest`, `python -m ruff check .`, `python -m compileall -q plugin tests
   tasks.py`, and `python evals/check.py --case "0006-*"`; paste the literal output
   (CLAUDE.md verification block, article p.28 step 6).

## Risks
- **What this could break** (every caller and consumer touched): both hooks now run on
  every `Bash`/`PowerShell` call in every phase, in CI and by hand, not only on
  `Edit`/`Write`/`MultiEdit`/`NotebookEdit`. A false positive — `shell_write_targets`
  matching a command that only *mentions* a guardrail-looking path without writing it
  (`grep CLAUDE.md`, `cat sdlc.yaml`, `python -m pytest tests/test_hooks.py -k protected`,
  `git commit -m "update CLAUDE.md wording"`) — would block ordinary work and park every
  run. This is the riskiest step (4 and 5): unlike `production_gate.guarded()`, which
  matches known destructive *program names*, `shell_write_targets` must recognise *write
  idioms* and extract *path arguments*, a larger surface to get wrong. Mitigation: it only
  fires on an explicit write-mode idiom (an actual redirection operator, an `-i` flag, `of=`,
  a write-mode literal beside `open(`/`writeFileSync`/etc.), never on a bare filename
  mention; step 1's negative cases (`cat`, `grep`, `git status`, `git commit -m "..."`,
  `python -m pytest`) are run before and after each hook change to catch a regression early.
  `plugin/gate/checks.py` (imports `protected_paths.protected_patterns`, `plan_sync`) and
  `plugin/skills/security-baseline/check.py` (imports `hooks.secrets_check.find_secrets`
  only) are not coupled to the new branch's internals and need no change.
- Moving code out of `production_gate.py` (step 2) could silently change its behaviour;
  mitigated by running its full existing test suite unmodified immediately after the move,
  before adding anything new.
- No new dependency: `shell_write_targets` uses only `re`/`shlex`, already imported by
  `production_gate.py` (security-baseline rule 6, coding-standards rule 5).
- Windows: the hook runtime is the `python` exec form already (decision 7), so this is a
  parsing concern, not a platform one; PowerShell's own write idioms (`Set-Content`,
  `Out-File`, `Remove-Item`, `>`/`>>`) are added explicitly to the idiom list rather than
  assumed from the POSIX ones, and the existing `_suffixes`/`_without_leading_options`
  helpers (already exercised by `production_gate`'s PowerShell coverage) are reused as-is.
- Residual risk accepted, not mitigated by this plan: a command the idiom list does not
  recognise (an unlisted wrapper, content decoded and piped to an interpreter) still reaches
  a guardrail file; see spec.md Flagged concerns. The gate's diff-based `check_guardrails`/
  `check_test_lock` remain the backstop for anything that is committed.

## Options not taken
- A new, separate `bash_guardrails.py` hook replacing the Bash/PowerShell logic inside both
  existing hooks. Not taken: it would need its own copy of each hook's pattern-loading (or
  import both `decide` functions anyway), adding a third registered script without removing
  the duplication the shared-helper approach already removes, for a larger diff.
- Relying on Claude Code's OS-level sandbox to deny filesystem writes to guardrail paths
  (the way `plugin/ci/settings.ci.json`'s `sandbox` block already restricts network). Not
  taken: no filesystem-level sandbox key is a verified fact for this plugin's pinned Claude
  Code version (`docs/notes/11.md` 11b lists only `sandbox.enabled`,
  `sandbox.network.allowedDomains`, `sandbox.failIfUnavailable`); building on an unverified
  setting risks doing nothing silently, or breaking every by-hand run where the sandbox is
  unavailable. Carried forward as a flagged concern for the owner to decide whether to
  pursue once verified.
- Narrowing `plugin/ci/settings.ci.json`'s allow-list instead of parsing Bash commands. Not
  taken: it would also block the legitimate uses the allow-list exists for, and does not
  reach a by-hand run, which has no `--settings` file at all; decision 6 already names the
  hook as the layer "the agent cannot switch off".
- Extending `secrets_check.py`'s coverage to Bash in this change. Not taken: it is a
  content-scanning control, not a path-based authorization gate — a different, larger piece
  of work (see spec.md Flagged concerns); left for a follow-up change if the owner wants it.

## Proof
- `tests/test_hooks.py::test_protected_paths_denies_a_bash_write_to_a_guardrail_file` (and
  variants for `rm`, an interpreter one-liner, and PowerShell `Set-Content`/`Out-File`) —
  written first, seen to fail against the current code, then pass.
- `tests/test_hooks.py::test_test_file_lock_denies_a_bash_write_to_a_locked_test_file` —
  same, for the test-file lock.
- `tests/test_hooks.py::test_shell_write_targets_*` — direct unit tests of the new helper,
  including the negative cases from Risks (`cat`, `grep`, `git status`, `git commit -m
  "..."`, `python -m pytest`, none of which are write idioms).
- `tests/test_hooks.py::test_hooks_json_registers_protected_paths_and_test_file_lock_on_bash_and_powershell`
  — new wiring test, in the shape of the existing
  `test_hooks_json_registers_the_production_gate_on_bash_and_powershell`.
- Every existing `test_protected_paths_*`, `test_test_file_lock_*` and `test_production_gate_*`
  test, unmodified, still passing.
- `evals/cases/0006-bash-guardrail-write-denied/` passing under
  `python evals/check.py --case "0006-*"`.
- `python -m pytest`, `python -m ruff check .`, `python -m compileall -q plugin tests
  tasks.py` — all three listed in `sdlc.yaml: commands`, run and pasted at the gate.
All of the above are tests still to be written in phase (c); none exist yet.
