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
  gap (see Open questions from intent, below).
- The fix is one shared mechanism, not two copies of similar regex: a single helper extracts
  candidate file-write target paths from a Bash/PowerShell command's text, and both
  `protected_paths.py` and `test_file_lock.py` call it when the tool is `Bash`/`PowerShell`.
  Source: coding-standards rule 2 (match the surrounding code's idiom — reuse, don't
  duplicate) and the intent's open question 2.
- `plugin/ci/settings.ci.json` and `template/.claude/settings.json`'s permission allow-list
  (`Bash(python *)`, `Bash(python3 *)`, `Bash(node *)`, `Bash(npm *)`, `Bash(npx *)`) is
  unchanged: the fix closes the gap at the hook layer (the layer decision 6 already commits
  to — "a self-protecting hook that denies edits to .claude/**, CLAUDE.md, REVIEW.md and the
  hook scripts"), not by narrowing what an unattended run may execute.
- A reproducing test exists for each hook before the fix is written (intent Constraints: "A
  test that reproduces the vulnerability is written first; no pre-existing test is edited to
  make the fix pass"), and no existing test in `tests/test_hooks.py` is weakened
  (coding-standards rule 4).
- An eval case is added so the class does not return (intent Proposed outcome; article p.48
  step 7), following the shape of the existing `evals/cases/0001-protected-path-denied`.
- `plugin/hooks/secrets_check.py` keeps its current scope (Edit/Write/MultiEdit/
  NotebookEdit only); see Open questions from intent for why it is not changed here.
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
`Bash|PowerShell` matcher runs only `plan_sync.py` (gated to `git *` commands) and
`production_gate.py` (gated to commands matching a known destructive-program glob list); no
Bash/PowerShell hook ever looks at what file a command would write. Because
`plugin/ci/settings.ci.json` allows bare `Bash(python *)`, `Bash(node *)`, etc. with no
prompt, an unattended run can reach the same file write through a one-line interpreter
script or shell redirection and the two path-based gates never see it — this is also how a
run could transiently rewrite `sdlc.yaml` (which carries the project's own
`protected_paths` list and `test_paths`) mid-session to turn its own protections off for the
rest of the run, then write it back before any commit, leaving nothing for the gate's
diff-based `check_guardrails`/`check_test_lock` (which judge only the committed diff,
OPERATING_MODEL section 3) to find afterwards.

The fix adds one shared helper, `shell_write_targets(command: str) -> list[str]`, next to
the other path helpers in `plugin/hooks/_common.py`. It returns the candidate target paths
a Bash/PowerShell command text contains for the recognised file-writing idioms: output
redirection (`>`, `>>`), `tee`, in-place editors (`sed -i`, `perl -i`), `cp`/`mv`/`rsync`
destinations, `dd of=`, `curl -o`/`-O`, `git apply`/`checkout -- <path>`, `rm`/
`Remove-Item` (removing a hook script or a guardrail file is as effective as editing it),
and the common interpreter one-liners that name a path literal next to a write-mode call
(`open(<path>, "w"`, `fs.writeFileSync(<path>`, PowerShell's `Set-Content`/`Out-File`). It
reuses `production_gate.command_parts`/`chain_parts`/token-suffix splitting so a command
behind `sudo`, `nohup`, `bash -c '...'` or a path/`.exe` wrapper is still read, instead of
inventing a second command parser (coding-standards rule 2). Each candidate path is resolved
against the command's working directory the same way `target_paths`' output is today and
run through the existing `_check_one` (protected_paths) / glob match (test_file_lock) — no
new matching logic, only a new source of candidate paths.

`hooks.json` adds `protected_paths.py` and `test_file_lock.py` to the `Bash|PowerShell`
matcher (new entries beside the existing `plan_sync.py`/`production_gate.py` ones, same
matcher group). Each script's `decide()` branches on `payload["tool_name"]`: the
`FILE_TOOLS` branch is unchanged; a new `Bash`/`PowerShell` branch calls
`shell_write_targets` on `tool_input["command"]` and checks every candidate the way the
existing branch checks `target_paths()`. Nothing else in either script's public shape
changes (same `Decision`, same fail-closed-on-bad-`sdlc.yaml` behaviour, same log format).

What stays unchanged: `plan_sync.py` and `production_gate.py` (already Bash-aware, not part
of this gap), `secrets_check.py` (different control — see Open questions), the gate's
`check_guardrails`/`check_test_lock` (the after-the-fact compensating layer; still useful for
whatever this heuristic cannot catch), and the permission allow-list in
`plugin/ci/settings.ci.json` / `template/.claude/settings.json`.

## Open questions from intent
- "Where else does the authz pattern occur, and does one fix cover every place?" —
  Answered from the codebase: `plugin/hooks/test_file_lock.py` has the identical pattern — a
  path-based authorization gate (glob-matches a target path against `sdlc.yaml: test_paths`)
  registered only on the `FILE_TOOLS` matcher, bypassable by the same Bash/PowerShell route.
  No third hook shares it: `plan_sync.py` and `production_gate.py` are already registered on
  `Bash|PowerShell`; `secrets_check.py` is a content scan, not a path-based authorization
  check (see below), and `panel_blind.py`/`format_on_edit.py` do not police paths at all.
  One fix (the shared helper) covers both places.
- "Is a shared guard (a helper, a middleware, a schema) better than local fixes?" —
  Answered: yes, `shell_write_targets` in `_common.py`, used by both hooks, per Design above.
- "Which eval case captures the class so it does not return?" — Carried forward to
  `plan.md`: a new case under `evals/cases/`, in the shape of `0001-protected-path-denied`,
  exercising a Bash command that attempts a guardrail-file write; plan.md names the case id
  and the files it adds.

## Flagged concerns
- Risk list: **auth**. This change is an authorization control top to bottom (closing a gap
  in which tool route a file write takes to reach a guardrail file). Per security-baseline
  rule 8 and decision 11, the change parks at its next gate until the owner accepts the risk
  with `sdlc:accept-risk` or `state/cli.py accept-risk`; the design pass does not close this
  — only the owner does.
- `secrets_check.py` is examined but not changed here. Its control is a content scan
  (regex over text an Edit/Write would place in a file), not a path-based authorization
  check — the intent evidence's own framing ("authorization inferred from which tool route
  is used, not enforced uniformly") describes `protected_paths.py`/`test_file_lock.py`'s
  mechanism, not `secrets_check.py`'s. A Bash command that writes a credential straight into
  a file (a heredoc, `echo ... > file`) is a real, related gap, but closing it needs scanning
  arbitrary command text for secret-shaped literals, which is a different, larger piece of
  work than reusing `shell_write_targets`. Carried forward: whether to open a follow-up
  change for it is the owner's call at this gate.
- The fix is heuristic command-text parsing, the same kind `production_gate.py` already
  does for guarded commands, with the same ceiling: a command the parser's idiom list does
  not recognise (an unlisted wrapper program, content decoded from base64 and piped to an
  interpreter, a custom script that itself shells out) can still reach a guardrail file
  without being caught at the hook layer. The gate's diff-based `check_guardrails` and
  `check_test_lock` remain the backstop for anything committed; a write that is made and then
  reverted before any commit has no backstop at all. This residual is inherent to policing
  shell text rather than the filesystem itself (notes/11.md 11b: only `sandbox.enabled`,
  `sandbox.network.allowedDomains` and `sandbox.failIfUnavailable` are verified Claude Code
  settings keys for this plugin version; no filesystem-level sandbox restriction is a
  documented option to fall back on instead). Carried forward: the owner decides whether this
  residual is acceptable for now or whether to re-open decision 6 once a stronger mechanism
  is verified.

## Acceptance
- `tests/test_hooks.py` gains reproducing tests, written and seen to fail first, then passing
  after the fix: a Bash command writing to each `ALWAYS_PROTECTED`/`GLOBAL_PROTECTED` path
  (e.g. `python -c "open('CLAUDE.md','w').write('x')"`, `echo x > sdlc.yaml`,
  `rm plugin/hooks/protected_paths.py`) is denied; the same for a Bash write to a locked test
  file in a fix-type change; an unrelated Bash command (e.g. `python -m pytest`,
  `git status`) is still allowed.
- Every existing test in `tests/test_hooks.py` still passes unweakened.
- `python -m pytest`, `python -m ruff check .` and `python -m compileall -q plugin tests
  tasks.py` are clean.
- The new eval case passes under `plugin/evals/run.py`.
- `python "${CLAUDE_PLUGIN_ROOT}/plugin/skills/security-baseline/check.py"` reports no new
  finding.
