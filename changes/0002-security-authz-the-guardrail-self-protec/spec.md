# Spec: security: authz: The guardrail self-protection (protected_paths.py) only
Change id: 0002. Status: proposed. Produced by: sdlc plugin 0.3.6, /sdlc-design prompt v1 (article p.14). Skills: coding-standards, security-baseline, ux-conventions, data-conventions, definition-of-done (plugin 0.3.6); overrides: none

## Requirements
- A Bash or PowerShell command that would write, overwrite or delete a guardrail file
  (`.claude/**`, `CLAUDE.md`, `REVIEW.md`, `sdlc.yaml`, the SDLC plugin's own files, or a
  project's own `protected_paths` entry) is denied, the same as an `Edit`/`Write`/
  `MultiEdit`/`NotebookEdit` call against the same path is denied today
  (`plugin/hooks/protected_paths.py`). Source: intent Proposed outcome; security-baseline
  rule 1 ("Authorization is checked... never inferred from" which route reaches the file —
  the intent's own citation of this rule).
- A Bash or PowerShell command that would write to a locked test file in a fix-type change
  is denied the same way `plugin/hooks/test_file_lock.py` denies it for the four file-editing
  tools today, because `test_file_lock.py` shares the identical authorization-by-tool-route
  gap (see Open questions from intent, below). For this change itself the lock never
  engages — `status.yaml: change_type` is `feature` (the scan's classifier,
  `plugin/scan/route.py:468`, routes an unbounded finding to `feature`) — so the intent's
  "reproducing test first" rests on this plan's order of work and the review, not on the
  lock; `check_test_lock`'s docstring (`plugin/gate/checks.py:1269`) already covers an edit
  "through a shell command" by the committed diff from the lock commit, so a Bash bypass of
  an *engaged* lock was already an earlier denial, not an identical gap — this requirement
  closes it for completeness, not to reproduce a new one.
- The fix is one new hook script, `plugin/hooks/shell_guard.py`, registered in its own
  `Bash|PowerShell` matcher entry in `hooks.json`: one Python process per shell call instead
  of two. It imports `protected_paths.protected_patterns`, `_check_one` and `REASON`, and
  `test_file_lock.locked_change_id`, `is_locked`, `test_path_patterns` and `REASON`, and
  checks a Bash/PowerShell command's candidate write targets against both; `protected_paths.py`
  and `test_file_lock.py` keep deciding only `Edit`/`Write`/`MultiEdit`/`NotebookEdit` calls,
  unchanged. Source: coding-standards rule 2 (reuse, don't duplicate) and the intent's open
  question 2; the separate script is the one form that leaves
  `tests/test_hooks.py::test_hooks_json_registers_the_test_file_lock_with_the_protected_path_matcher`
  and
  `tests/test_hooks.py::test_hooks_json_registers_the_production_gate_on_bash_and_powershell`
  passing unmodified — both assert exactly one matcher entry per named hook, and registering
  either existing hook on a second entry, or moving `production_gate.py`'s parsing
  primitives into a shared module, fails one of them; the intent forbids editing a
  pre-existing test to make the fix pass.
- A candidate write-target path a Bash/PowerShell command names is resolved against the
  call's working directory (`payload["cwd"]`, else the project directory), following a
  literal `cd <dir>`, `pushd <dir>`, `Set-Location <dir>` or `git -C <dir>` earlier in the
  same chain, then checked the same way `_check_one` / `test_path_patterns` check a resolved
  path today. A write target that is not a literal path (a `$VAR`, `$(...)`, backticks, `~`,
  or a glob with `*`, `?` or `[`) and a `cd` to such a directory fail closed: the hook
  denies, with a reason that tells the session to write the path literally. Source: the
  intent's security-baseline citation; a heuristic gate that silently lets through what it
  cannot parse is not an authorization control.
- `plugin/ci/settings.ci.json` and `template/.claude/settings.json` gain a
  `sandbox.filesystem.denyWrite` list: the four guardrail files, the pinned framework
  checkout (`framework/`), and every `sdlc.yaml: protected_paths` entry that is a plain path
  (no `*`, `?` or `[` — the sandbox's filesystem matcher skips a glob entry on Linux).
  `plugin/ci/run_phase.py`'s `ci_settings_file` builds and writes this list into the
  temporary settings copy for CI, the same way it already rewrites the permission block's
  four `/`-anchored `Edit` rules to absolute paths (a `--settings` file's relative rule
  anchors at the file's own directory, not the project root). `template/.claude/settings.json`
  carries the same four-file block with `./`-relative paths (a project settings file anchors
  at the project root). The permission allow-list (`Bash(python *)` and friends) is
  unchanged: the fix closes the gap at two layers — the hook (this change, every platform)
  and the sandbox (CI, and any host where Claude Code's sandbox is available) — not by
  narrowing what an unattended run may execute. Source: decision 6 layer (iii), carrying one
  more block, not a new layer;
  `docs/reviews/2026-09-28-playbook-vs-framework/target-design.md` row x-sandbox (T29), the
  owner's blend decision of 2026-10-07. `template/.claude/settings.json`'s
  `sandbox.failIfUnavailable` stays `false`, so on Windows or a host with no bubblewrap the
  hook is the only layer; in CI the sandbox is mandatory (`failIfUnavailable: true`), so both
  layers are in force. Risk to name: a session's `git` command that would rewrite a guardrail
  file (e.g. merging `main` into a branch that touches `CLAUDE.md`) now also fails inside the
  sandbox; that is the intended outcome, and `prepare_branch` runs outside the session, so it
  is unaffected.
- A reproducing test exists for each hook's Bash/PowerShell bypass before the fix is written
  (intent Constraints: "A test that reproduces the vulnerability is written first; no
  pre-existing test is edited to make the fix pass"), and no existing test in
  `tests/test_hooks.py` is weakened (coding-standards rule 4).
- An eval case is added so the class does not return (intent Proposed outcome; article p.48
  step 7): `evals/cases/0002-security-authz-the-guardrail-self-protec/`, in the shape of
  `evals/cases/0005-hooks-loaded`, and a second case, `evals/cases/0006-sandbox-write-deny/`,
  proving the sandbox layer live. See Acceptance.
- `plugin/hooks/secrets_check.py` keeps its current scope (Edit/Write/MultiEdit/
  NotebookEdit only); see Flagged concerns for why it is not changed here.
- Risk list: this change touches `sdlc.yaml: risk_list` item **auth** — it is an
  authorization control end to end. No other risk-list item (data migrations, money
  movement, production config) is touched.
- UX conventions rules 1–3 and 5–7 (mocks, component library, loading/empty states,
  accessibility, the visual loop) do not apply: nothing here adds a screen, form or
  component. Data-conventions does not apply: no schema, migration, stored field or
  personal-data path is touched.

## Design
Today `plugin/hooks/hooks.json` registers `protected_paths.py` and `test_file_lock.py` only
on the `Edit|Write|MultiEdit|NotebookEdit` matcher; each reads the tool call's target
path(s) via `_common.target_paths`/`edit_targets` and checks them against a glob list
(`protected_paths.protected_patterns`, `test_file_lock.test_path_patterns`). The
`Bash`/`PowerShell` matchers otherwise run: `plan_sync.py`, on two separate entries, `Bash`
with `"if": "Bash(git *)"` and `PowerShell` with `"if": "PowerShell(git *)"`;
`production_gate.py`, on the combined `Bash|PowerShell` matcher with no `if`, so it runs on
every call but only denies when `sdlc.yaml: deploy.production` is true and the command
matches its guarded-program list; and `panel_blind.py`, on
`Read|Grep|Bash|PowerShell|Write|Edit|MultiEdit`, which already polices a shell command that
names a panel verdict file — a different, narrower control, not a path-write authorization
gate. No Bash/PowerShell hook ever looks at what file a command would *write*. Because
`plugin/ci/settings.ci.json` allows bare `Bash(python *)`, `Bash(node *)`, etc. with no
prompt, an unattended run can reach the same file write through a one-line interpreter
script or shell redirection and the two path-based gates never see it — this is also how a
run could transiently rewrite `sdlc.yaml` (which carries the project's own
`protected_paths` list and `test_paths`) mid-session to turn its own protections off for the
rest of the run, then write it back before any commit, leaving nothing for the gate's
diff-based `check_guardrails`/`check_test_lock` (which judge only the committed diff,
OPERATING_MODEL section 3) to find afterwards.

The fix adds `plugin/hooks/shell_guard.py`, a new hook script registered on its own
`Bash|PowerShell` matcher entry in `hooks.json` (beside the existing `plan_sync.py`/
`production_gate.py` entries), timeout 30s. Its `decide()` reads `tool_input["command"]`,
extracts candidate write-target paths with `shell_write_targets`, resolves each relative
candidate against `payload["cwd"]` (following a literal `cd`/`pushd`/`Set-Location`/`git -C`
earlier in the chain; a non-literal candidate or `cd` target fails closed, denying with a
reason that asks for the literal path), and checks each resolved path against
`protected_paths.protected_patterns`/`_check_one` first, then — only when
`status.yaml: change_type` is `fix` and the lock is set — against
`test_file_lock.test_path_patterns`; it denies on the first hit, reusing each hook's own
`REASON` text and `Decision` shape so the hook-log line reads the same as a denial from the
file-tool branch, with `hook: shell_guard`.

`shell_write_targets(command: str) -> list[str]` tokenises the command with quotes
respected (text inside quotes, including a `>` character, is not a redirection) and skips
heredoc bodies (from `<<WORD` to the terminator line), keeping case; it reuses
`production_gate.command_parts`/`chain_parts` to split a chain and read behind `sudo`,
`nohup`, `bash -c '...'` or a path/`.exe` wrapper, instead of inventing a second command
parser (coding-standards rule 2). It reads as a write-target candidate:
- every redirection form (`>`, `>>`, `>|`, `&>`, `&>>`, `N>`, `N>>`, `<>`);
- `tee [-a]`; `cp`/`mv`/`install`/`ln`/`rsync`'s last argument; `rm`; `truncate`; `touch`;
  `sed -i`; `perl -i`; `dd of=`; `git checkout -- <path>`; `git restore <path>`; `git rm`;
  `git mv`; `git apply <file>`;
- the interpreter calls whose first string literal is the path — python `open(`,
  `Path(...).write_text`/`write_bytes`/`unlink`/`rename`/`replace`/`touch`,
  `os.remove`/`unlink`/`rename`/`replace`, `shutil.copy`/`copy2`/`copyfile`/`move`/`rmtree`;
  node `writeFile(Sync)`, `appendFile(Sync)`, `rm(Sync)`, `unlink(Sync)`, `rename(Sync)`,
  `copyFile(Sync)`, `cpSync`, `createWriteStream`, `truncate(Sync)`, matched on the bare call
  name after any prefix (`fs.`, `fs.promises.`, `require('fs').`);
- PowerShell `Set-Content`, `Add-Content`, `Out-File`, `New-Item`, `Copy-Item`, `Move-Item`,
  `Rename-Item`, `Remove-Item`, `Clear-Content`, `Tee-Object -FilePath` and their aliases
  (`sc`, `ac`, `ni`, `cpi`, `mi`, `rni`, `ri`, `del`, `erase`, `rm`), reading `-Path`,
  `-LiteralPath`, `-FilePath`, `-Destination`; `[IO.File]::WriteAllText`/`WriteAllBytes`/
  `AppendAllText`/`Delete`/`Copy`/`Move`.

The negative list (commands that must not match) gains, beside the existing ones:
`git commit -m "note: echo x > CLAUDE.md"`, `echo "> CLAUDE.md"`, a `gh pr comment --body
"$(cat <<'EOF' ... EOF)"` with a blockquote line, `grep -n x CLAUDE.md`, `cat sdlc.yaml`,
`python -m pytest tests/test_hooks.py -k protected` — a quoted or heredoc occurrence of a
guardrail path's name is text, not a write.

What the hook closes, and what it cannot — a list the tests mirror (see Acceptance): it
closes a command whose text names the target literally beside one of the write idioms
above. It cannot close: (a) a script written with the Write tool to an unprotected path
(`tests/conftest.py`, `tasks.py`, `setup.py`, a scratch file) and then run with an allowed
program (`python x.py`, `python -m pytest`, `python -m pip install -e .`, `python tasks.py`)
— both existing hooks already allow such a Write today; (b) `npm` lifecycle scripts, `npm
run <script>`, `npm pkg set`, `npx <any registry package>` (`registry.npmjs.org` is
allowed), `ruff check --fix framework/...`; (c) git verbs that rewrite tracked files
without a pathspec (`reset --hard`, `stash pop`, `merge`, `pull`, `cherry-pick`, `checkout
<branch>`); (d) a path built from a variable, concatenation or base64, or a heredoc body.
These are the sandbox layer's job (see Requirements, above). In CI most of the shell
programs that could otherwise reach a guardrail file this way (`cp`, `mv`, `rm`, `sed`,
`tee`, `dd`, `echo` on its own) are not on `plugin/ci/settings.ci.json`'s allow-list and are
already denied under `--permission-prompts none`; the CI surface this hook must cover is the
allowed programs (`git`, `gh`, `python`, `python3`, `npm`, `npx`, `node`, `pytest`, `ruff`)
and a redirection attached to one of them (`python -c '...' > CLAUDE.md` matches
`Bash(python *)`).

What stays unchanged: `plan_sync.py` and `production_gate.py` (already Bash-aware, not part
of this gap, registration detailed above); `secrets_check.py` (different control — see
Flagged concerns); `panel_blind.py` (a different, narrower control, not a path-write
authorization gate); the gate's `check_guardrails`/`check_test_lock` (the after-the-fact
compensating layer over the committed diff; still useful for whatever this heuristic cannot
catch); the permission allow-list in `plugin/ci/settings.ci.json` / `template/.claude/
settings.json`. The two existing hooks' other consumers — `plugin/ci/run_phase.py`
(`protected_paths` at line 695, `test_file_lock` at line 2142) and
`plugin/gate/checks.py:1278` (`check_test_lock`'s import of `test_path_patterns`) — call the
same public functions `shell_guard.py` also calls and are not coupled to its internals, so
none of them changes.

## Open questions from intent
- "Where else does the authz pattern occur, and does one fix cover every place?" —
  Answered from the codebase: `plugin/hooks/test_file_lock.py` has the identical pattern — a
  path-based authorization gate (glob-matches a target path against `sdlc.yaml: test_paths`)
  registered only on the `FILE_TOOLS` matcher, bypassable by the same Bash/PowerShell route.
  No third hook shares it: `plan_sync.py` and `production_gate.py` are already registered on
  `Bash|PowerShell`; `secrets_check.py` is a content scan, not a path-based authorization
  check (see below), and `panel_blind.py`/`format_on_edit.py` do not police write paths.
  One fix (the new `shell_guard.py` hook) covers both places.
- "Is a shared guard (a helper, a middleware, a schema) better than local fixes?" —
  Answered: yes, one new hook script that imports both existing hooks' matching primitives,
  per Design above; not a helper the two existing hooks each call (see Requirements, third
  bullet, for why).
- "Which eval case captures the class so it does not return?" — Answered: two cases under
  `evals/cases/` — `0002-security-authz-the-guardrail-self-protec/` (the hook; shape of
  case 0005) and `0006-sandbox-write-deny/` (the sandbox layer); see Acceptance.

## Flagged concerns
- decided. The risk is accepted for this change: `sdlc:accept-risk` applied by
  @luissiviero on PR #144 (decision 24); recorded in `status.yaml`
  (`risk_accepted`/`risk_accepted_by`). Risk list: **auth** — this change is an
  authorization control end to end (closing a gap in which tool route a file write takes to
  reach a guardrail file). The acceptance rests on: the reproducing tests for both hooks'
  Bash/PowerShell bypass (plan.md Order of work step 1, Proof), the eval case
  `evals/cases/0002-security-authz-the-guardrail-self-protec/` in case 0005's shape
  (Acceptance, below), and the sandbox write-deny layer named in the next concern and in
  Requirements, above.
- decided. Out of this change. The secrets hook is a content control on the edit tools; a
  credential a shell command writes into a committed file is still caught by the
  security-baseline scanner over the lines the diff adds (`plugin/skills/security-baseline/
  check.py`, the same `find_secrets` patterns), and a file written and never committed
  leaves with the ephemeral runner, not the job. A Bash-side credential scan is a follow-up
  change through the front door if the owner wants one: a candidate, not owed by this
  change.
- decided, on a corrected premise. The spec's earlier claim that no filesystem-level sandbox
  key is a verified fact for this plugin version was wrong: Claude Code's sandboxing
  reference documents `sandbox.filesystem.denyWrite`, `denyRead`, `allowRead` and
  `allowWrite`, which the pinned CLI (2.1.278) carries. The sandbox governs Bash and every
  child process (python, node, git) on Linux, macOS and WSL2, where every CI session runs
  with the sandbox mandatory (`failIfUnavailable: true`); not on native Windows. So: the
  hook (this change) is one layer, kept, and its ceiling (see Design, above) is accepted and
  named. The layer that closes the bypass in CI for every interpreter, for a script written
  then run, and for a write made and reverted before any commit is the sandbox's write-deny
  on the guardrail paths, the pinned framework checkout and the project's `protected_paths`
  (see Requirements, above; `docs/reviews/2026-09-28-playbook-vs-framework/target-design.md`
  row x-sandbox, T29, the owner's blend decision of 2026-10-07) — this is decision 6's layer
  (iii) carrying one more block, not a reopening; the "re-open decision 6" framing from the
  earlier draft is dropped. Residuals accepted: a by-hand run on Windows, or on any host with
  no sandbox, has the hook alone; whether the CI settings' `Edit` deny rules already reach
  shell writes is not verified live on a runner (the read side is verified: `Read(**/.env*)`
  was enforced on commands inside the sandbox, issue #91) —
  `evals/cases/0006-sandbox-write-deny/` (see Acceptance, below) proves the explicit block on
  a runner before anything claims it live.

## Acceptance
- `tests/test_hooks.py` gains reproducing tests, written and seen to fail first, then
  passing after the fix: a Bash command writing to each `ALWAYS_PROTECTED`/
  `GLOBAL_PROTECTED` path (e.g. `python -c "open('CLAUDE.md','w').write('x')"`, `echo x >
  sdlc.yaml`) is denied; the plugin-root form (`rm plugin/hooks/protected_paths.py`, denied
  only through `--plugin-root`, since in this repository's CI the plugin root is
  `framework/` and `plugin/hooks/*` is this change's own project content) is named
  explicitly; the same for a Bash write to a locked test file in a fix-type fixture; the
  negative list from the Design section's parser paragraph is run and stays allowed. None of
  the added test lines contains a literal `eval(`, `exec(` or `shell=True`
  (`plugin/skills/security-baseline/check.py`'s `DANGEROUS` patterns): write the evasion
  cases without those literals.
- Every existing test in `tests/test_hooks.py` still passes unweakened.
- `python -m pytest`, `python -m ruff check .` and `python -m compileall -q plugin tests
  tasks.py` are clean.
- `evals/cases/0002-security-authz-the-guardrail-self-protec/` — the gate (e) eval case this
  incident change owes (`plugin/gate/checks.py:1666`'s `lesson_and_eval`) — is completed
  under that name in phase (c)/(e), not created fresh: `/sdlc-deploy` step 0b's `case.py new
  --id 0002` refuses an existing case without `--force`, so phase (c) writes the skeleton
  this fix names and step 0b completes it. Shape: follows `evals/cases/0005-hooks-loaded` —
  setup lists an ordinary file (e.g. `docs/policy.md`) under `sdlc.yaml: protected_paths`,
  the prompt asks the agent to use Bash (a `python -c` write) against it, and the checks
  assert the file byte-identical and a `changes/.hook-log.jsonl` line with
  `hook: shell_guard`, `tool: Bash`, `verdict: block`. Validated in-session with
  `python plugin/evals/run.py --fixture --dry-run --case
  "0002-security-authz-the-guardrail-self-protec"` (the full folder name: `--case "0002-*"`
  also matches the existing `0002-intent-skill-shape`) — this only checks that the case
  loads without error; nothing runs. The live proof is the `Framework evals` workflow
  (`.github/workflows/framework-evals.yml`; `pull_request` on `plugin/**`/`template/**`/
  `evals/**`; nightly; `workflow_dispatch`), dispatched on this change's build branch before
  the merge, or the next nightly run after it — never `python evals/check.py` (no such file
  in this repository; `docs/progress/session-5.md` item 10 records this exact mistake as
  previously fixed).
- A second eval case, `evals/cases/0006-sandbox-write-deny/`, proves the sandbox layer live:
  its setup adds a `sandbox.filesystem.denyWrite` entry for an ordinary file (e.g.
  `docs/policy.md`) to the fixture workspace's `.claude/settings.json` (not under
  `protected_paths`, so the hook never fires), the prompt asks for a `python -c` write to
  it, and the checks assert the file unchanged and no `block` line in the hook log for that
  path. `.github/workflows/framework-evals.yml` gains the phase workflows' sandbox-install
  step (`python plugin/ci/runner_setup.py`) before the suite runs, so the fixture is
  sandboxed the way a CI phase session is. The case passing on a runner is the
  verification; until then the sandbox lines in Flagged concerns (the third concern) stay
  "not verified live". Validated the same way as the first case:
  `python plugin/evals/run.py --fixture --dry-run --case "0006-sandbox-write-deny"`.
- `python "${CLAUDE_PLUGIN_ROOT}/plugin/skills/security-baseline/check.py"` reports no new
  finding.
