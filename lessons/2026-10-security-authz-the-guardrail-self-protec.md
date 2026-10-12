---
type: Lesson
title: "security: authz: The guardrail self-protection (protected_paths.py) only"
description: "security: authz found that the guardrail self-protection hook checked only the Edit/Write/MultiEdit/NotebookEdit tools, letting a Bash or PowerShell command rewrite a guardrail file unchecked."
tags:
  - authz
  - "security: authz"
change: "0002"
detected:
  at: "2026-10-05T14:53:56Z"
  metric: "security: authz"
  tier: 3
  rule: scan
fixed:
  pr: 152
generated:
  by: sdlc-plugin/0.3.7
  at: "2026-10-12T08:02:59Z"
status: stable
stale_after: "2027-10-12"
sources:
  - id: detection
    resource: evidence/scan-finding.json
  - id: eval
    resource: evals/cases/0002-security-authz-the-guardrail-self-protec/
  - id: fix-pr
    resource: https://github.com/luissiviero/sdlc-framework/pull/152
---

## What happened
The weekly security scan[^detection] flagged `plugin/hooks/hooks.json:32`: the guardrail
self-protection hook, `protected_paths.py`, was registered only on the `Edit|Write|MultiEdit|
NotebookEdit` tool matcher. The `Bash`/`PowerShell` matcher ran `plan_sync.py` and
`production_gate.py`, but neither checked a shell command's target path. `plugin/ci/
settings.ci.json`'s permission allow-list granted bare `Bash(python *)`, `Bash(node *)` and
similar with `--permission-prompts none`, so an unattended phase session could overwrite
`CLAUDE.md`, `REVIEW.md`, `sdlc.yaml` or `.claude/**` with a one-line `python`/`node` file
write via `Bash`, bypassing the protection the framework's own threat model (decision 6;
CLAUDE.md's "Never edit `.claude/**`, `CLAUDE.md`, `REVIEW.md` or `sdlc.yaml` in a run")
relies on entirely.

## Root cause
Authorization was checked by which of the two Claude Code tool matchers reached a path, not
by the path itself: a session routed through `Edit`/`Write`/`MultiEdit`/`NotebookEdit` was
denied, the identical session routed through `Bash`/`PowerShell` was not. The same gap
existed for `test_file_lock.py`'s fix-type test-file lock. Fixing the gap meant parsing shell
commands well enough to find every write/delete/rename target a review round subsequently
found many ways to evade — git global options before the subcommand, nested interpreter
calls, directory ancestors, PowerShell's own escaping and parameter binding, subshells and
command groups, heredocs, brace and pathspec expansion — each closed over five fix rounds.

## Fix
One new hook, `plugin/hooks/shell_guard.py`, registered on its own `Bash|PowerShell` matcher
entry, reusing `protected_paths.protected_patterns`/`_check_one` and `test_file_lock.
locked_change_id`/`is_locked`/`test_path_patterns` to judge a shell command's resolved write
targets the same way the two existing hooks judge an `Edit`/`Write`/`MultiEdit`/
`NotebookEdit` call. `plugin/ci/settings.ci.json` and `plugin/ci/run_phase.py`'s
`ci_settings_file` gained a `sandbox.filesystem.denyWrite` list as a second, OS-level layer
beside the hook. Shipped in PR #152[^fix-pr].

## Prevention
`evals/cases/0002-security-authz-the-guardrail-self-protec/`[^eval] reproduces a Bash write
to a project-protected file and asserts `shell_guard` logs a `block` verdict for the `Bash`
tool, the same shape `evals/cases/0005-hooks-loaded` already uses for the `Edit` tool, so the
suite fails again if the `Bash`/`PowerShell` matcher ever loses its guard. `tests/
test_hooks.py` carries one reproducing test per evasion the review rounds found (git global
options, nested interpreter `-c` flags, directory ancestors, destination-argument copy/move
calls, PowerShell escaping and parameter binding, subshells/groups/assignments, heredocs,
brace/pathspec expansion, and more), so the same class of bypass cannot return unnoticed.

[^detection]: evidence/scan-finding.json
[^eval]: evals/cases/0002-security-authz-the-guardrail-self-protec/
[^fix-pr]: the build PR
