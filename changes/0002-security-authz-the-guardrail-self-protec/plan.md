# Plan: security: authz: The guardrail self-protection (protected_paths.py) only (from intent.md 2026-10-05, spec.md 2026-10-08)

## Files that change
- `plugin/hooks/shell_guard.py` (new) — `shell_write_targets(command: str) -> list[str]`,
  its own tokenizer, not a reuse of `production_gate.command_parts`/`chain_parts` (round 3
  review, item 5): `shlex`-style quoting, heredoc-body skipping, chain-splitting on `;`/
  `&&`/`||`/`|`/newline only outside quotes, case kept throughout, a leading wrapper word
  (`sudo`/`nohup`/`time`/`env`) skipped, and `bash -c`/`sh -c`/`cmd /c`/`pwsh -Command`
  parsed by recursing into the quoted inner string; the write-idiom list (redirection,
  `tee`, in-place editors, `cp`/`mv`/`rsync`/`install`/`ln` destinations, `dd of=`, git verbs
  that take a path, `rm`/`truncate`/`touch`, the python/node/PowerShell interpreter literals
  — spec.md Design); the `cwd`/`cd`-chain path resolution and fail-closed rule for a
  non-literal candidate (a non-literal `cd` with no write idiom after it is allowed); and
  `decide()`, importing `protected_paths`' and `test_file_lock`'s matching primitives and
  `REASON` text (no import from `production_gate.py`), denying with `hook: shell_guard` in
  the log.
- `plugin/hooks/hooks.json` — one new `Bash|PowerShell` matcher entry for `shell_guard.py`,
  invoked with `--plugin-root ${CLAUDE_PLUGIN_ROOT}` (the plugin-root form of the Acceptance
  example depends on it), timeout 30 (the lock's git call and the log's are 20s each; a
  timed-out PreToolUse hook does not block). The hook logs its blocks only, as
  `panel_blind.py` does — an allow line on every shell call would bury the committed
  `evidence/hook-log.jsonl`.
- `plugin/ci/settings.ci.json` — a `sandbox.filesystem.denyWrite` list: the directories
  `.claude` and `framework`, the files `CLAUDE.md`, `REVIEW.md` and `sdlc.yaml`, and
  `sdlc.yaml: protected_paths`'s plain-path entries (a glob entry among them is skipped,
  noted in the result).
- `plugin/ci/run_phase.py` — `ci_settings_file` also builds and writes the
  `sandbox.filesystem.denyWrite` list (absolute paths, as a second rule beside
  `_ANCHORED_RULE`) into the temporary CI settings copy, reading `sdlc.yaml: protected_paths`
  for the extra entries. This function is also on the detect path's port list (`run_phase.py`
  carries both the phase runner and the detect dispatch helpers); the build PR's record notes
  that this change's edit to it was checked against that list.
- `tests/test_hooks.py` — reproducing tests for both hooks' Bash/PowerShell bypass (written
  first, seen to fail; imported inside the test functions, never at module top-level, so a
  failure in the new tests cannot abort collection of the rest of the file), negative cases
  proving ordinary commands still run (including `2>&1` and `> /dev/null`), direct unit
  tests of `shell_write_targets` and the path-resolution/fail-closed rule (including the
  non-literal-`cd`-with-no-write-after-it case), and a wiring test for the new `hooks.json`
  registration (`test_hooks_json_registers_shell_guard_on_bash_and_powershell`, in the shape
  of `test_hooks_json_registers_the_production_gate_on_bash_and_powershell`). If phase (c)
  places these in a new `tests/test_shell_guard.py` instead, that file is added to this list
  in the same commit — an unlisted file is a plan-sync denial.
- `tests/test_ci.py` — `test_ci_settings_are_rendered_against_the_project_root`'s
  `data["sandbox"] == source["sandbox"]` assertion is updated for the rewritten list (it
  cannot hold once `ci_settings_file` rewrites the sandbox paths — round 3 review, item 1,
  decision 1); a new test asserts the exact rendered `sandbox.filesystem.denyWrite` list,
  not just that the key exists.
- `tests/test_evals.py` — `FRAMEWORK_SUITE` (line 29) stops being a literal tuple of case
  names; `test_the_fixture_dry_run_lists_every_case` (line 602) derives the expected names
  and count from the folders under `evals/cases/` instead (round 3 review, item 1, decision
  1), so the suite grows without editing a literal.
  `test_the_framework_suite_s_cases_load` (line 522) was changed the same way in round 3,
  then reverted to a literal list of case names in the phase (e) fix round (review
  #5469970014, item 3): comparing `run.discover(FRAMEWORK_CASES)` against `FRAMEWORK_SUITE`
  checked `run.discover` against itself, so a skipped or duplicated case would pass
  silently; the literal list is ground truth the other assertion still doesn't have to be.
- `docs/OPERATING_MODEL.md` (line 121) — layer (i)'s sentence gains "and a Bash/PowerShell
  command that would write to the same paths" so it says the hook covers shell writes too;
  layer (iii)'s sentence names the new sandbox `filesystem.denyWrite` block in
  `plugin/ci/settings.ci.json` alongside hooks and permissions as CI-pinned content.
- `.claude-plugin/plugin.json` — version `0.3.6` → `0.3.7`. Required in the same commit as
  the source changes: `plan_sync.exempt` is only `changes/**` and `*.md` (`sdlc.yaml`), so a
  commit that bumps this file without listing it here is denied at the commit
  (`plugin/hooks/plan_sync.py`).
- `.claude-plugin/marketplace.json` — version `0.3.6` → `0.3.7`, same commit and same reason
  as `.claude-plugin/plugin.json` above.

Not touched: `plugin/hooks/_common.py`, `plugin/hooks/production_gate.py`,
`plugin/hooks/protected_paths.py`, `plugin/hooks/test_file_lock.py` (no shared-helper move
and no new branch inside either existing hook — spec.md Requirements, third bullet);
`plugin/hooks/secrets_check.py`, `plan_sync.py`; `plugin/gate/checks.py` (its imports of
`protected_paths.protected_patterns` and `test_file_lock.test_path_patterns` are unaffected
— spec.md Design, "what stays unchanged"); the permission allow-list in
`plugin/ci/settings.ci.json` / `template/.claude/settings.json` (spec.md Requirements);
`template/.claude/settings.json`'s own `sandbox.filesystem.denyWrite` block (round 3 review,
item 2 — the owner's edit after this build, proposed in the build PR's record);
`evals/cases/0002-security-authz-the-guardrail-self-protec/` (created at phase (e) from
spec.md Acceptance, round 3 review, item 4); `evals/cases/0006-sandbox-write-deny/` and
`.github/workflows/framework-evals.yml` (a follow-up PR, round 3 review, item 3 — a build
run's `GITHUB_TOKEN` cannot push a workflow-file change).

## Order of work
1. Write the reproducing tests for the Bash/PowerShell bypass of `protected_paths.py` and
   `test_file_lock.py` (including the `hooks.json` wiring test), imported inside the test
   functions (or in a new `tests/test_shell_guard.py`) so a failure cannot abort collection
   of the rest of `tests/test_hooks.py`; run them and confirm they fail against the current
   code (intent Constraints: the reproducing test comes first).
2. Add `plugin/hooks/shell_guard.py`: `shell_write_targets` as its own tokenizer (round 3
   review, item 5 — no import from `production_gate.py`; `shlex`-style quoting, heredoc-body
   skipping, chain-splitting outside quotes, case kept, wrapper-word skipping, recursive
   `bash -c`/`sh -c`/`cmd /c`/`pwsh -Command` parsing) with the idiom list from spec.md
   Design; the `cwd`/`cd`-chain resolution and fail-closed rule (a non-literal `cd` with no
   write idiom after it is allowed); `decide()` wired to both existing hooks' matching
   primitives. Add direct unit tests for the parser and the resolver (the write idioms
   denied; the read/no-op idioms and the negative list — `cat`, `grep`, `git status`,
   `git commit -m "..."`, `python -m pytest`, `2>&1`, `> /dev/null` — left alone; the
   recursive inner-shell forms and the wrapper words parsed correctly).
3. Register `shell_guard.py` on the `Bash|PowerShell` matcher in `plugin/hooks/hooks.json`
   with `--plugin-root ${CLAUDE_PLUGIN_ROOT}`; re-run step 1's tests — they now pass.
4. Add the `sandbox.filesystem.denyWrite` block to `plugin/ci/settings.ci.json` only (not
   `template/.claude/settings.json` — round 3 review, item 2); extend
   `plugin/ci/run_phase.py`'s `ci_settings_file` to build and rewrite it for the temporary CI
   copy as a second rule beside `_ANCHORED_RULE`; update
   `test_ci_settings_are_rendered_against_the_project_root`'s `sandbox` assertion for the
   rewritten list and add the new `ci_settings_file` test in `tests/test_ci.py` (round 3
   review, item 1, decision 1).
5. Make `tests/test_evals.py`'s `FRAMEWORK_SUITE` and `test_the_fixture_dry_run_lists_every_case`
   derive the suite's case names and count from the folders under `evals/cases/` instead of
   the literal tuple (round 3 review, item 1, decision 1). `test_the_framework_suite_s_cases_load`
   asserts a literal list of case names instead (phase (e) fix round, review #5469970014,
   item 3).
6. Update `docs/OPERATING_MODEL.md:121` (the two sentences named in Files that change).
7. Bump `.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json` to `0.3.7` in the
   same commit as the files above that are not exempt from `plan_sync`.
8. Run `python -m pytest`, `python -m ruff check .` and `python -m compileall -q plugin tests
   tasks.py`; paste the literal output (CLAUDE.md verification block, article p.28 step 6).
   Nothing about eval cases runs in this session: `evals/cases/0002-security-authz-the-
   guardrail-self-protec/` is created at phase (e) (round 3 review, item 4) and
   `evals/cases/0006-sandbox-write-deny/` is a follow-up PR (round 3 review, item 3).

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
- No new dependency: `shell_guard.py` uses only `re`/`shlex` from the standard library; it
  imports no helper from `production_gate.py` (round 3 review, item 5), so its own
  tokenizer, not that module's, is what must be gotten right.
- The fail-closed rule's cost to a session (Requirements, above): a `$VAR`/`$(...)`/glob
  write target, or a `cd` to such a directory followed by a write idiom, is denied with a
  reason that tells the session to write the path literally, not performed — a session that
  relies on a computed path for an ordinary, unprotected write must rewrite the command
  literally to proceed.
- The sandbox block (step 4) also denies a `git` command that would rewrite a guardrail file
  from inside the sandbox (e.g. merging `main` into a branch that touches `CLAUDE.md`); that
  is the intended outcome, and `prepare_branch` runs outside the session, so it is
  unaffected (spec.md Requirements).
- One more process per shell call: `shell_guard.py` runs as a second `python` invocation
  beside `production_gate.py` on every `Bash`/`PowerShell` call, about 60ms of added latency
  on Linux (Windows unmeasured).
- Windows: the hook runtime is the `python` exec form already (decision 7), so this is a
  parsing concern, not a platform one; PowerShell's own write idioms (`Set-Content`,
  `Out-File`, `Remove-Item`, `>`/`>>`, the `[IO.File]::` statics) are added explicitly to the
  idiom list, and the case-preserving tokenizer (round 3 review, item 5) is exercised against
  them the same way as the POSIX idioms, rather than reusing `production_gate`'s
  case-lowering `_suffixes`/`_without_leading_options` helpers, which would match a
  PowerShell alias case-insensitively where PowerShell's own aliasing does not.
- The test-file lock never engages for this change (`change_type: feature`): its own
  Bash/PowerShell branch is exercised only by the reproducing test's fix-type fixture, not
  by this change's own build (spec.md Requirements).
- `tests/test_ci.py`'s and `tests/test_evals.py`'s updated assertions (round 3 review,
  item 1, decision 1, steps 4–5): the first can no longer assert the sandbox block is
  unchanged by `ci_settings_file`, since this change makes that function rewrite it on
  purpose; `test_the_fixture_dry_run_lists_every_case` stops hard-coding the eval suite's
  case names so the suite can grow without a literal edit. Both are contract changes this
  design makes on purpose, not a weakening of either test (coding-standards rule 4; intent
  Constraints). `test_the_framework_suite_s_cases_load` went the other way in the phase (e)
  fix round (review #5469970014, item 3): it had come to compare `run.discover` against a
  value also derived from `run.discover`, catching nothing a bug in `discover` itself could
  not also hide; a literal list of case names is the ground truth that assertion needs.
- The hand-over of the eval case from this spec's Acceptance to `/sdlc-deploy` step 0b
  (round 3 review, item 4): phase (c) writes no `evals/cases/0002-...` folder at all, so
  `case.py new --id 0002` at (e) is never blocked by an existing case; the case's exact
  content (setup, prompt, checks) must match this spec's Acceptance closely enough that the
  (e) session can write it from the spec alone.
- Residual risk accepted, not mitigated by this plan: a command the idiom list does not
  recognise (an unlisted wrapper, content decoded and piped to an interpreter) still reaches
  a guardrail file at the hook layer alone; the sandbox layer (step 4) closes this in CI;
  see spec.md Flagged concerns, third concern, for the residual outside CI (Windows, or any
  host with no sandbox, and until the sandbox layer's live-proof follow-up PR lands). The
  gate's diff-based `check_guardrails`/`check_test_lock` remain the backstop for anything
  that is committed.

## Options not taken
- A single shared helper that both existing hooks (`protected_paths.py`, `test_file_lock.py`)
  call, instead of one new hook script. Not taken: `tests/test_hooks.py`'s existing wiring
  tests each assert exactly one `hooks.json` matcher entry per named hook
  (`test_hooks_json_registers_the_test_file_lock_with_the_protected_path_matcher`,
  `test_hooks_json_registers_the_production_gate_on_bash_and_powershell`); adding either
  hook to a second `Bash|PowerShell` entry fails one of them, and the intent forbids editing
  a pre-existing test to make the fix pass. The separate script is the one form that leaves
  both tests passing unmodified.
- Reusing `production_gate.command_parts`/`chain_parts` for the parser, or moving them into
  a shared `_common.py` module. Not taken (reversed twice: the earlier draft of this plan
  moved them to `_common.py`, the next drew `shell_guard.py` on importing them directly from
  `production_gate.py`, and round 3 review item 5 reproduced why neither holds):
  `command_parts` splits on newlines and `$(` and cuts inside quotes, loses a redirection
  target behind an option-stripping suffix check, turns a heredoc blockquote line into its
  own write-looking part, and lower-cases text for matching — all wrong for a parser that
  must extract path arguments with quotes and case preserved. `shell_guard.py` tokenizes
  independently; this is also a second, unrelated change to a hook this fix does not
  otherwise touch, with its own risk of changing `production_gate.py`'s behaviour for no
  requirement.
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
- One test per idiom class for each protected set: `tests/test_hooks.py::
  test_protected_paths_denies_a_bash_write_to_a_guardrail_file` (a direct guardrail file),
  a plugin-root variant (`rm plugin/hooks/protected_paths.py`, denied only through
  `--plugin-root`), a `sdlc.yaml: protected_paths` entry, and
  `test_test_file_lock_denies_a_bash_write_to_a_locked_test_file` (a locked test file in a
  fix-type fixture; this change's own lock never engages) — each written first, seen to fail
  against the current code, then pass.
- The PowerShell forms (`Set-Content`/`Out-File`/`Remove-Item`/`[IO.File]::` statics) of the
  same denials.
- The relative-path and `cd` cases: a candidate resolved against `cwd`, a `cd`/`pushd`/
  `Set-Location`/`git -C` earlier in the chain, and a `cd` to a non-literal directory with no
  write idiom after it being allowed.
- The fail-closed cases: a `$VAR` target, a `$(...)` target, a glob target, a `cd` to a
  non-literal directory followed by a write idiom.
- The negative list from Risks and spec.md Design (`cat`, `grep`, `git status`,
  `git commit -m "..."`, `python -m pytest`, the quoted/heredoc cases, `2>&1`,
  `> /dev/null`), none of which are write idioms, plus the recursive inner-shell forms
  (`bash -c`, `sh -c`, `cmd /c`, `pwsh -Command`) and the wrapper words (`sudo`, `nohup`,
  `time`, `env`) parsed correctly — all in `tests/test_hooks.py::test_shell_write_targets_*`
  or `tests/test_shell_guard.py`.
- `tests/test_hooks.py::test_hooks_json_registers_shell_guard_on_bash_and_powershell` — new
  wiring test, in the shape of
  `test_hooks_json_registers_the_production_gate_on_bash_and_powershell`.
- `tests/test_ci.py::test_ci_settings_file_rewrites_the_sandbox_filesystem_deny_write_list`
  (name indicative) — asserts the exact rendered `sandbox.filesystem.denyWrite` list
  (absolute rewrite, appended `protected_paths` entries, a skipped glob noted).
- The updated tests (round 3 review, item 1, decision 1):
  `test_ci_settings_are_rendered_against_the_project_root`'s `sandbox` assertion matching
  the rewritten list, and `test_the_fixture_dry_run_lists_every_case` deriving
  `FRAMEWORK_SUITE` from `evals/cases/`'s folders. `test_the_framework_suite_s_cases_load`
  instead asserts a literal list of case names (phase (e) fix round, review #5469970014,
  item 3), so a skipped or duplicated case folder is caught rather than passing against
  another copy of the same `run.discover` call.
- Every existing `test_protected_paths_*`, `test_test_file_lock_*` and `test_production_gate_*`
  test, unmodified, still passing.
- `python -m pytest`, `python -m ruff check .`, `python -m compileall -q plugin tests
  tasks.py` — all three listed in `sdlc.yaml: commands`, run and pasted at the gate.
- `python "${CLAUDE_PLUGIN_ROOT}/plugin/skills/security-baseline/check.py"` — no new
  finding.
- The `Framework evals` workflow run, after the merge, once `/sdlc-deploy` adds
  `evals/cases/0002-security-authz-the-guardrail-self-protec/` at phase (e) (the nightly, or
  a dispatch) — the live proof of the hook through case 0002; `evals/cases/0006-sandbox-
  write-deny/`'s live proof is a follow-up PR, outside this change's Proof.
All of the above are tests still to be written in phase (c); none exist yet.
