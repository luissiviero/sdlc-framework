# Plan: security: authz: The guardrail self-protection (protected_paths.py) only (from intent.md 2026-10-05, spec.md 2026-10-08)

## Files that change
- `plugin/hooks/shell_guard.py` (new) — `shell_write_targets(command: str) -> list[str]`
  (the parser: redirection, `tee`, in-place editors, `cp`/`mv`/`rsync`/`install`/`ln`
  destinations, `dd of=`, git verbs that take a path, `rm`/`truncate`/`touch`, the python/
  node/PowerShell interpreter literals — spec.md Design); the `cwd`/`cd`-chain path
  resolution and fail-closed rule for a non-literal candidate; `decide()`, importing
  `protected_paths`' and `test_file_lock`'s matching primitives and `REASON` text, denying
  with `hook: shell_guard` in the log.
- `plugin/hooks/hooks.json` — one new `Bash|PowerShell` matcher entry for `shell_guard.py`,
  timeout 30 (the lock's git call and the log's are 20s each; a timed-out PreToolUse hook
  does not block). The hook logs its blocks only, as `panel_blind.py` does — an allow line
  on every shell call would bury the committed `evidence/hook-log.jsonl`.
- `plugin/ci/settings.ci.json` — a `sandbox.filesystem.denyWrite` list: the four guardrail
  files, `framework/`, and `sdlc.yaml: protected_paths`'s plain-path entries.
- `template/.claude/settings.json` — the same four-guardrail-file `sandbox.filesystem.
  denyWrite` block with `./`-relative paths; `failIfUnavailable` stays `false`.
- `plugin/ci/run_phase.py` — `ci_settings_file` also builds and writes the
  `sandbox.filesystem.denyWrite` list (absolute paths, same rewrite rule as the four `Edit`
  deny rules) into the temporary CI settings copy, reading `sdlc.yaml: protected_paths` for
  the extra entries.
- `tests/test_hooks.py` — reproducing tests for both hooks' Bash/PowerShell bypass (written
  first, seen to fail; imported inside the test functions or placed in a new
  `tests/test_shell_guard.py`, never at module top-level, so a failure in the new tests
  cannot abort collection of the whole file), negative cases proving ordinary commands still
  run, direct unit tests of `shell_write_targets` and the path-resolution/fail-closed rule,
  and a wiring test for the new `hooks.json` registration
  (`test_hooks_json_registers_shell_guard_on_bash_and_powershell`, in the shape of
  `test_hooks_json_registers_the_production_gate_on_bash_and_powershell`).
- `tests/test_ci.py` — a `ci_settings_file` test asserting the sandbox paths are rewritten
  to absolute and the `protected_paths` entries are appended.
- `evals/cases/0002-security-authz-the-guardrail-self-protec/` (`prompt.md`, `checks.yaml`)
  — the gate (e) eval case this incident change owes, completed under its own id (spec.md
  Acceptance), in the shape of `evals/cases/0005-hooks-loaded`.
- `evals/cases/0006-sandbox-write-deny/` (`prompt.md`, `checks.yaml`) — the sandbox layer's
  live case (spec.md Acceptance).
- `.github/workflows/framework-evals.yml` — adds the sandbox-install step
  (`python plugin/ci/runner_setup.py`) before the suite, so the fixture runs sandboxed.
- `docs/OPERATING_MODEL.md` (line 121) — layer (i)'s sentence gains "and a Bash/PowerShell
  command that would write to the same paths" so it says the hook covers shell writes too;
  layer (iii)'s sentence names the new sandbox `filesystem.denyWrite` block alongside hooks
  and permissions as pinned-plugin content.
- `.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json` — version `0.3.6` →
  `0.3.7`. Required in the same commit as the source changes: `plan_sync.exempt` is only
  `changes/**` and `*.md` (`sdlc.yaml`), so a commit that bumps these two JSON files without
  listing them here is denied at the commit (`plugin/hooks/plan_sync.py`).

Not touched: `plugin/hooks/_common.py`, `plugin/hooks/production_gate.py`,
`plugin/hooks/protected_paths.py`, `plugin/hooks/test_file_lock.py` (no shared-helper move
and no new branch inside either existing hook — spec.md Requirements, third bullet);
`plugin/hooks/secrets_check.py`, `plan_sync.py`; `plugin/gate/checks.py` (its imports of
`protected_paths.protected_patterns` and `test_file_lock.test_path_patterns` are unaffected
— spec.md Design, "what stays unchanged"); the permission allow-list in
`plugin/ci/settings.ci.json` / `template/.claude/settings.json` (spec.md Requirements).

## Order of work
1. Write the reproducing tests for the Bash/PowerShell bypass of `protected_paths.py` and
   `test_file_lock.py` (including the `hooks.json` wiring test), imported inside the test
   functions (or in a new `tests/test_shell_guard.py`) so a failure cannot abort collection
   of the rest of `tests/test_hooks.py`; run them and confirm they fail against the current
   code (intent Constraints: the reproducing test comes first).
2. Add `plugin/hooks/shell_guard.py`: `shell_write_targets` with the idiom list from
   spec.md Design, reusing `production_gate.command_parts`/`chain_parts` for chain/quote/
   heredoc handling (no code moved out of `production_gate.py`); the `cwd`/`cd`-chain
   resolution and fail-closed rule; `decide()` wired to both existing hooks' matching
   primitives. Add direct unit tests for the parser and the resolver (the write idioms
   denied; the read/no-op idioms and the negative list — `cat`, `grep`, `git status`,
   `git commit -m "..."`, `python -m pytest` — left alone).
3. Register `shell_guard.py` on the `Bash|PowerShell` matcher in `plugin/hooks/hooks.json`;
   re-run step 1's tests — they now pass.
4. Add the `sandbox.filesystem.denyWrite` block to `plugin/ci/settings.ci.json` and
   `template/.claude/settings.json`; extend `plugin/ci/run_phase.py`'s `ci_settings_file` to
   build and rewrite it for the temporary CI copy; add the `ci_settings_file` test in
   `tests/test_ci.py`.
5. Add `evals/cases/0002-security-authz-the-guardrail-self-protec/` and
   `evals/cases/0006-sandbox-write-deny/`; validate both with `--dry-run` (step 8).
6. Add the sandbox-install step to `.github/workflows/framework-evals.yml`.
7. Update `docs/OPERATING_MODEL.md:121` (the two sentences named in Files that change).
8. Bump `.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json` to `0.3.7` in the
   same commit as the files above that are not exempt from `plan_sync`.
9. Run `python -m pytest`, `python -m ruff check .`, `python -m compileall -q plugin tests
   tasks.py`, `python plugin/evals/run.py --fixture --dry-run --case
   "0002-security-authz-the-guardrail-self-protec"` and the same `--case
   "0006-sandbox-write-deny"`; paste the literal output (CLAUDE.md verification block,
   article p.28 step 6). The live proof of both eval cases (the `Framework evals` workflow)
   is dispatched on the build branch or runs on the next nightly after merge — not run
   inside this session (spec.md Acceptance).

## Risks
- **What this could break** (every caller and consumer touched): both existing hooks' matching
  primitives now run, via `shell_guard.py`, on every `Bash`/`PowerShell` call in every phase,
  in CI and by hand, not only on `Edit`/`Write`/`MultiEdit`/`NotebookEdit`. A false positive
  — `shell_write_targets` matching a command that only *mentions* a guardrail-looking path
  without writing it (`grep CLAUDE.md`, `cat sdlc.yaml`, `python -m pytest
  tests/test_hooks.py -k protected`, `git commit -m "update CLAUDE.md wording"`, a
  `gh pr comment` body quoting a heredoc that mentions `CLAUDE.md`) — would block ordinary
  work and park every run. This is the riskiest step (2): unlike `production_gate.guarded()`,
  which matches known destructive *program names*, `shell_write_targets` must recognise
  *write idioms* and extract *path arguments* with quotes and heredocs respected, a larger
  surface to get wrong. Mitigation: it only fires on an explicit write-mode idiom (an actual
  redirection operator, an `-i` flag, `of=`, a write-mode literal beside `open(`/
  `writeFileSync`/etc.), never on a bare filename mention or inside quotes/a heredoc body;
  the negative list (spec.md Design) is run before and after each change to catch a
  regression early. `plugin/gate/checks.py` and `plugin/skills/security-baseline/check.py`
  are not coupled to the new hook's internals and need no change (spec.md Design).
- The sandbox layer (step 4) is new surface in `ci_settings_file`, read by every CI phase
  job: a malformed `sandbox.filesystem.denyWrite` entry (a glob character the sandbox skips
  on Linux, per spec.md Requirements) silently does nothing rather than erroring, so the
  `ci_settings_file` test (step 4) asserts the exact rewritten paths, not just that the key
  exists.
- No new dependency: `shell_guard.py` uses only `re`/`shlex` plus `production_gate`'s own
  helpers, already imported there (security-baseline rule 6, coding-standards rule 5).
- Windows: the hook runtime is the `python` exec form already (decision 7), so this is a
  parsing concern, not a platform one; PowerShell's own write idioms (`Set-Content`,
  `Out-File`, `Remove-Item`, `>`/`>>`, the `[IO.File]::` statics) are added explicitly to the
  idiom list rather than assumed from the POSIX ones, and the existing `_suffixes`/
  `_without_leading_options` helpers (already exercised by `production_gate`'s PowerShell
  coverage) are reused as-is.
- The test-file lock never engages for this change (`change_type: feature`): its own
  Bash/PowerShell branch is exercised only by the reproducing test's fix-type fixture, not
  by this change's own build (spec.md Requirements).
- The hand-over of the eval case from phase (c) to `/sdlc-deploy` step 0b (spec.md
  Acceptance): phase (c) must write `evals/cases/0002-security-authz-the-guardrail-self-
  protec/` under that exact name so step 0b's `case.py new --id 0002` (which refuses an
  existing case without `--force`) completes it instead of colliding with it.
- Residual risk accepted, not mitigated by this plan: a command the idiom list does not
  recognise (an unlisted wrapper, content decoded and piped to an interpreter) still reaches
  a guardrail file at the hook layer alone; the sandbox layer (step 4) closes this in CI;
  see spec.md Flagged concerns, third concern, for the residual outside CI (Windows, or any
  host with no sandbox). The gate's diff-based `check_guardrails`/`check_test_lock` remain
  the backstop for anything that is committed.

## Options not taken
- A single shared helper that both existing hooks (`protected_paths.py`, `test_file_lock.py`)
  call, instead of one new hook script. Not taken: `tests/test_hooks.py`'s existing wiring
  tests each assert exactly one `hooks.json` matcher entry per named hook
  (`test_hooks_json_registers_the_test_file_lock_with_the_protected_path_matcher`,
  `test_hooks_json_registers_the_production_gate_on_bash_and_powershell`); adding either
  hook to a second `Bash|PowerShell` entry fails one of them, and the intent forbids editing
  a pre-existing test to make the fix pass. The separate script is the one form that leaves
  both tests passing unmodified.
- Moving `production_gate.py`'s command-parsing primitives into a shared `_common.py`
  module. Not taken (reversed from the earlier draft of this plan): it is not needed —
  `shell_guard.py` imports `production_gate`'s `command_parts`/`chain_parts` directly — and
  it would be a second, unrelated change to a hook this fix does not otherwise touch, with
  its own risk of changing `production_gate.py`'s behaviour for no requirement.
- Relying on Claude Code's OS-level sandbox alone, with no hook. Not taken: the sandbox is
  not available on native Windows and is off when `failIfUnavailable: false` and the host
  has no bubblewrap (the template's own setting, for a by-hand run); the hook is the layer
  the agent cannot switch off on any platform. The sandbox is added as a second layer in CI
  (spec.md Requirements), not as a replacement for the hook.
- Narrowing `plugin/ci/settings.ci.json`'s allow-list instead of parsing Bash commands. Not
  taken: it would also block the legitimate uses the allow-list exists for, and does not
  reach a by-hand run, which has no `--settings` file at all; decision 6 already names the
  hook as the layer "the agent cannot switch off".
- Extending `secrets_check.py`'s coverage to Bash in this change. Not taken: it is a
  content-scanning control, not a path-based authorization gate — a different, larger piece
  of work (see spec.md Flagged concerns); left for a follow-up change if the owner wants it.

## Proof
- `tests/test_hooks.py::test_protected_paths_denies_a_bash_write_to_a_guardrail_file` (and
  variants for `rm`, the plugin-root form, an interpreter one-liner, and PowerShell
  `Set-Content`/`Out-File`) — written first, seen to fail against the current code, then
  pass.
- `tests/test_hooks.py::test_test_file_lock_denies_a_bash_write_to_a_locked_test_file` —
  same, for the test-file lock (a fix-type fixture; this change's own lock never engages).
- `tests/test_hooks.py::test_shell_write_targets_*` (or `tests/test_shell_guard.py`) — direct
  unit tests of the new parser and the `cwd`/`cd`-chain resolver, including the negative
  cases from Risks (`cat`, `grep`, `git status`, `git commit -m "..."`, `python -m pytest`,
  the quoted/heredoc cases from spec.md Design, none of which are write idioms) and the
  fail-closed cases (a `$VAR` target, a glob target, a `cd` to a non-literal directory).
- `tests/test_hooks.py::test_hooks_json_registers_shell_guard_on_bash_and_powershell` — new
  wiring test, in the shape of
  `test_hooks_json_registers_the_production_gate_on_bash_and_powershell`.
- `tests/test_ci.py::test_ci_settings_file_rewrites_the_sandbox_filesystem_deny_write_list`
  (name indicative) — asserts the absolute rewrite and the appended `protected_paths`
  entries.
- Every existing `test_protected_paths_*`, `test_test_file_lock_*` and `test_production_gate_*`
  test, unmodified, still passing.
- `evals/cases/0002-security-authz-the-guardrail-self-protec/` validated with `--dry-run`
  in-session; passing live under the `Framework evals` workflow (dispatched on the build
  branch, or the next nightly after merge).
- `evals/cases/0006-sandbox-write-deny/` — same, proving the sandbox layer.
- `python -m pytest`, `python -m ruff check .`, `python -m compileall -q plugin tests
  tasks.py` — all three listed in `sdlc.yaml: commands`, run and pasted at the gate.
- `python "${CLAUDE_PLUGIN_ROOT}/plugin/skills/security-baseline/check.py"` — no new
  finding.
All of the above are tests still to be written in phase (c); none exist yet.
