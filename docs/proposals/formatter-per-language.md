---
type: Proposal
title: The formatter follows the project's languages — per file type, the project's own commands on the changed file
description: The formatter-and-linter hook runs, per file type, the format and lint commands the project names in sdlc.yaml on the changed file only, failing open as today, with ruff for Python the default, /sdlc-init proposing prettier and eslint for Node and rustfmt for Rust, whole-project checks left at the gate's lint target and no default for a file type with no command; added, nothing replaced.
status: proposed
roadmap: R33
sources:
  - id: study-entry
    resource: docs/reviews/2026-09-28-playbook-vs-framework/target-design.md
    title: "T8, confirmed at the close of the study on 2026-10-09; from the crosswalk row build-hooks (better: the framework; decision: blend), 2026-10-03; the owner's note corrected the same day at the owner's request; annotation of 2026-10-13 (0.3.7, the eighth hook)"
  - id: record
    resource: docs/reviews/2026-09-28-playbook-vs-framework.md
    title: "Section 7 (the close, the build-hooks row of the decisions table, the re-check against 0.3.7 of 2026-10-13) and section 8 part 2 (the close table's T8 row, the format, the confirmed order)"
  - id: crosswalk
    resource: docs/reviews/2026-09-28-playbook-vs-framework/crosswalk.json
    title: "Row build-hooks whole; the decision fields of test-bugfix (T11), setup-adopt (T5) and build-skills (T1, 'back any skill'); the maintain-act entry T24, whose option C left the quarantine runbook for Node and Rust here"
  - id: playbook
    resource: docs/reference/ai-native-sdlc-playbook.pdf
    title: "p.23: 'Hooks as build-time guardrails': run the formatter and linter after file edits so drift never accumulates; fast and scoped to the file that changed; heavier checks at the commit or the PR"
  - id: decision-6
    resource: docs/decisions/6.md
    title: "Decision 6: the guardrails' three layers; CI loads the hooks from the pinned plugin (kept)"
  - id: decision-7
    resource: docs/decisions/7.md
    title: "Decision 7: Python for every hook (kept; the hook stays Python and calls the project's tools)"
  - id: decision-29
    resource: docs/decisions/29.md
    title: "Decision 29: in CI a red target starts the next fix round by itself (accepted 2026-10-13, R10 not built at main 5542406; kept)"
  - id: notes
    resource: docs/notes/1.md
    title: "How Claude Code invokes hook commands: exec form cannot spawn npm's .cmd shims on Windows (lines 38-40); with docs/notes/20.md:44 (a test helper's .cmd shim lost an argument's tail at an unquoted &, read from cmd.exe's rules, not traced)"
  - id: code
    resource: plugin/hooks/format_on_edit.py
    title: "PY_SUFFIXES, ruff_command, format_file and decide, read at main 5542406, plugin 1.0.1; with plugin/hooks/hooks.json, plugin/hooks/_common.py run_hook, plugin/init/detect.py, plugin/init/sdlc_init.py build_values, plugin/gate/checks.py commands_from_config and run_command, plugin/gate/gate.py run_deferred_commands, plugin/ci/settings.ci.json, plugin/ci/run_phase.py commands_env, plugin/agents/verifier.md, plugin/skills/coding-standards/SKILL.md, template/sdlc.yaml"
generated: { by: sdlc-framework-session/ccr-01de3f80-ilnomi, at: 2026-10-15T20:00:00Z }
---

# The formatter follows the project's languages: per file type, the project's own commands on the changed file

**Status: proposed (roadmap R33), from study entry T8, confirmed by the owner on 2026-10-09.** Nothing is built. It amends no decision: decisions 6 and 7 stay, as the owner's note says, and this proposal writes no decision file. It is one of the study's "rest in any order" proposals (the record, section 8 part 2), added to the formatter hook and to the commands `/sdlc-init` proposes for it, with no other hook changed; full Rust support, the test-file lock for tests inside source files and the quarantine runbook for Node and Rust stay open here, beside R34 (T11) and R41 (T24).

## The problem

The owner has projects in other languages than Python (Rust, Node), said in the session of 2026-10-03[^entry]. On those projects nothing formats or lints on edit:

- **The formatter and linter on edit act on Python files only.** Every other file type is skipped "in this version" (`plugin/hooks/format_on_edit.py:8`, `:32`, `:80`), so on a Node or Rust project formatting drift and lint findings accumulate during the session, against the article's "so drift never accumulates" (p.23)[^playbook].
- **They first show at the lint target, a round later.** In CI no project target runs inside the session (plugin 0.3.2): the runner runs build, test and lint after it, and a red target parks the change (`plugin/gate/gate.py:378-394`, `plugin/agents/verifier.md:18-25`). A formatting problem shows there only if the project's lint target checks formatting. With decision 29 built (R10), the red target starts the next fix round instead of parking, which spends a round of the iteration cap on what a per-file hook would have fixed in the same edit[^decision-29].
- **`/sdlc-init` does not see a Rust project at all.** A repository with no Python signal and no `package.json` is "unknown" (`plugin/init/detect.py:181-182`, `:331-340`), and its targets are placeholders (`plugin/init/sdlc_init.py:97-99`) the gate drops (`plugin/gate/checks.py:249-258`) and then refuses until the owner fills them in (`:349-361`).

## What the article says

"Build-phase hooks can: Block edits to protected paths [...]; Run the formatter and linter after file edits so drift never accumulates; Keep credentials out of the diff. Back any skill whose policy has to hold without exception. A hook runs on each action that matches it, so build-phase hooks should be fast and scoped to the file that changed. Heavier checks such as the full test suite belong at the commit or the PR." A hook that asks a human "belongs with the gates in Stage 5: Deploy" (p.23)[^playbook]. The article names no language; the framework's hook covers one.

## What the framework does today

Read at `main` 5542406, plugin 1.0.1. The entry's "Today" was read at 619f01a (plugin 0.3.5); `git diff --stat 619f01a 5542406` over the files below touches only `plugin/hooks/hooks.json` (the shell guard, 0.3.7), `plugin/ci/settings.ci.json` (the write-deny list, 0.3.7, and the Actions log host, 0.3.8), `plugin/gate/checks.py` and `template/sdlc.yaml` (a commented `lessons:` block); `format_on_edit.py`, `_common.py`, `detect.py`, `sdlc_init.py`, `gate.py`, `verifier.md` and the coding-standards skill have an empty diff, so the entry's claims about them still hold[^code].

- **Eight hooks, not seven.** The owner's note of 2026-10-03 lists seven (with the corrections approved on the row: seven, not six, and the relation "adapted", not "same"); 0.3.7 added the shell guard on Bash and PowerShell (`hooks.json:67-81`), logging its blocks only. The record keeps the note as saved, "overtaken without being made untrue" (section 7, re-check of 2026-10-13)[^record]. All are deterministic and none asks.
- **The formatter hook.** A `PostToolUse` hook on `Edit|Write|MultiEdit`, with a 60-second handler timeout (`hooks.json:94-105`). For each changed path that is a `.py` or `.pyi` file inside the project (`format_on_edit.py:78-83`), it runs `ruff check --fix`, `ruff format`, then `ruff check` (`:50-63`), each with a 25-second timeout (`:33`), preferring `python -m ruff` and falling back to `ruff` on `PATH` (`:36-47`). Ruff's exit 1 (findings left) is fed back to Claude as a `PostToolUse` block with the findings (`:85-92`): the edit has already happened, so this is feedback, as session 24 saw on this repository (`docs/progress/session-24.md:116`). It fails open: no ruff or a ruff failure (exit 2) passes with a note (`:53-54`, `:63`), and a timeout raises out of `format_file` into `run_hook`, which fails open on `PostToolUse` with a note on stderr and no log line (`plugin/hooks/_common.py:400-409`, the fail-open lines `:408-409`; docstring `format_on_edit.py:9-10`).
- **The one switch.** `sdlc.yaml: hooks.format_on_edit` turns the hook on or off (`format_on_edit.py:75-77`; `template/sdlc.yaml:146-147`, `true`); nothing in `sdlc.yaml` names a command for the hook.
- **What `/sdlc-init` detects.** Python when any `.py` file, `pyproject.toml` or `setup.py` exists (`detect.py:181-182`), so one helper script makes a Node or Rust repository Python; else Node when `package.json` exists (`:331-340`), its lint target `npm run lint` when `scripts.lint` exists, else none (`:304-312`). `detect_node` reads `scripts`, not the dependencies, so it does not see prettier or eslint (`:276-329`). No `Cargo.toml` signal exists; a Rust repository is "unknown", its test paths `tests/**` and `test/**` (`:41`).
- **The skill's backing.** The coding-standards skill names "the formatter hook (`hooks.format_on_edit`) and the lint target in the gate" as its deterministic backing (`plugin/skills/coding-standards/SKILL.md:46-47`).
- **Windows.** Claude Code's exec form, which every hook in `hooks.json` uses, cannot spawn npm's `.cmd` shims (`docs/notes/1.md:38-40`); the hook's own child processes are started by Python, and the gate's `run_command` runs a target through the platform shell because "on Windows the .cmd shims need cmd.exe" (`plugin/gate/checks.py:288-310`). A test helper's fake `gh.cmd` shim lost the part of an argument after an unquoted `&` (`docs/notes/20.md:44`; the mechanism read from cmd.exe's rules, not traced in a console); whether npm's shims do the same is to verify.
- **The CI sandbox and Rust.** The CI settings allow `Bash(npm *)`, `Bash(npx *)` and `Bash(node *)` but not `Bash(cargo *)` (`plugin/ci/settings.ci.json:20-36`), and the allowed domains include `registry.npmjs.org` but not `index.crates.io` or `static.crates.io` (`:44-53`). The project's setup command runs before the session, outside the sandbox.

## The proposal

Added, nothing replaced: the hooks stay as they are, deterministic, every block logged (the panel-blindness hook logs only its blocks, the production gate nothing while inert), none asks; decisions 6 and 7 are unchanged. The note names seven hooks; the eighth, the shell guard of 0.3.7, came after it and logs its blocks only, and this proposal, on its own reading, leaves it as it is too. What the owner decided on 2026-10-03, with the entry's direction where the note is silent:

1. **Per file type, the project's own commands.** `sdlc.yaml` maps a file glob to the format and lint commands the hook runs, in order, on the changed file only; for example `*.ts` to prettier, then eslint `--fix`, and `*.rs` to rustfmt. The hook stays Python (decision 7), loads from the pinned plugin in CI (decision 6) and calls the project's tools.
2. **Failing open, as today.** A missing tool, a tool that cannot run or a timeout never blocks; it is reported and the edit stands.
3. **Ruff for Python stays the default.** With no mapping, a `.py` or `.pyi` file gets today's three ruff steps, so a Python project that never touches the setting sees no change.
4. **Proposed at setup.** `/sdlc-init` proposes the commands from what it finds: prettier and eslint for Node when `package.json` has them, rustfmt for Rust (a `Cargo.toml` project). The owner keeps or edits them in the change-0000 PR; `sdlc.yaml` stays a guardrail file the owner changes in a reviewed PR.
5. **Only what is cheap per file.** A check that compiles or scans the whole project (clippy for Rust, a full type check) stays at the gate's lint target, as p.23 puts heavier checks at the commit or the PR.
6. **A file type with no command passes.** So there is no default for HTML, CSS, Markdown, JSON or YAML, as every non-Python file passes today; unformatted files there cost diff noise, not a park. A project already on prettier may add them at no extra cost.
7. **Timing.** Recorded on 2026-10-03, built after the study.
8. **Not proposed here.** Full Rust support beyond this hook (its targets, the test-file lock for tests inside source files, crates.io in the CI sandbox) and the quarantine runbook for Node and Rust stay open (below). "Back any skill whose policy has to hold" is not this proposal's: it was settled at build-skills (each skill's "Deterministic backing" line, a new hook decided rule by rule once the owner's policy sources exist, R27).

## How it is judged

The entry names no measure; this one is the session's recommendation. On the owner's first Node or Rust project after the release: the hook log (`evidence/hook-log.jsonl`) shows the mapped commands on each edit of a mapped file type, which needs a field the hook does not write today (below, "What the hook log records"); over its first five changes, no runner lint result (the gate record's `commands` check at (c), `lint.log` at (d) and (e), `plugin/agents/verifier.md:22-25`) is red for a finding the per-file commands fix (a formatting or auto-fixable lint finding), against today, where such a finding first shows there, if the lint target checks it at all; a missing or failing tool never blocks an edit (a unit test per failure kind, on Windows and Linux). A Python project with no mapping behaves as before: the same hook-log lines apart from the timestamp.

## What to settle before building

The entry's open items first, then the session's own recommendations, marked as such.

| Question | Recommended |
|---|---|
| The exact shape of the `sdlc.yaml` setting, and whether it keeps the on/off switch `hooks.format_on_edit` (entry, Open) | The session's: keep `hooks.format_on_edit` as the switch (every project's `sdlc.yaml` carries it, `template/sdlc.yaml:147`), and add beside it an ordered list of `{glob, commands}` entries, each command a string with a `{file}` placeholder; the first matching glob wins; an explicit `*.py` entry replaces the ruff default. Its name judged with T4 (R45) |
| npm's `.cmd` shims on Windows: whether the hook starts them through the platform shell, as the gate's `run_command` does (entry, Open) | To verify on Windows before the design, recorded in `docs/notes/`, including a changed path with a space or `&` (`docs/notes/20.md:44`) |
| Full Rust support: detecting its build, test and lint targets (entry, Open; crosswalk setup-adopt) | Still open; the session's: its own change after this one, since rustfmt in the hook needs only the `Cargo.toml` signal |
| The test-file lock for unit tests inside source files (`#[cfg(test)]`) (entry, Open; crosswalk test-bugfix) | In part settled: the owner's note at test-bugfix (2026-10-03) makes the runner's red run at the lock commit and green run at HEAD prove such a fix (R34, T11); freezing the test stays open here |
| crates.io in the CI sandbox: the hosts and `Bash(cargo *)` are absent (`settings.ci.json:20-53`); whether the project's setup command, run before the session and outside its sandbox, is enough (entry, Open) | To verify on a Rust sample with the Rust change; the session's: add the hosts and the allow rule only if the session's own `cargo` calls need them |
| The quarantine runbook for Node and Rust (jest's ignore patterns, cargo's `#[ignore]`), left here by maintain-act (T24, option C of maintain-act, not chosen) | Still open: no project needs it yet (T24's note, R41) |
| "Back any skill whose policy has to hold without exception" (p.23) | Settled at build-skills (2026-10-03, T1 "Sources and documents"; R27): rule by rule, once the owner's sources exist |
| How a project command's result is read (the session's) | A `check` command's exit 1 is fed back as today's `PostToolUse` block with its output; any other non-zero exit, a missing tool or a timeout is reported on stderr and passes (failing open); a `fix` command's output is not fed back |
| The time budget (the session's) | All the commands for one file fit the 60-second handler (`hooks.json:102`); each command keeps today's 25 seconds (`format_on_edit.py:33`) and the hook stops, passing, when the budget is spent |
| What environment the commands run with (the session's) | An eslint or prettier configuration in JavaScript is code the session can write, and the hook's child runs outside the Bash tool's sandbox (to verify): the hook strips the model credentials and the GitHub token from the child's environment, as `commands_env` does for the targets (`plugin/ci/run_phase.py:1413-1419`) |
| What the hook log records (the session's) | Today a line holds `at`, `hook`, `event`, `tool`, `verdict`, `reason`, `cwd` and the target paths (`plugin/hooks/_common.py:347-357`, `:390-398`), and the formatter's allow carries no reason (`format_on_edit.py:95`), so no line names a command: the hook adds the commands it ran, with each exit code, to its log line |
| A mixed repository (the session's) | `/sdlc-init` reads each language's signals on its own, not only the one detected language, so a Node project with a helper `.py` file (detected as Python, `detect.py:181`) still gets the prettier and eslint proposal |

## Considered and not chosen

- **Replacing or reshaping the hooks.** The owner's note: added, nothing replaced; the hooks stay as they are.
- **Defaults for HTML, CSS, Markdown, JSON and YAML.** Not chosen: a type with no command passes; a project already on prettier may add them.
- **Whole-project checks in the hook** (clippy, a full type check): they stay at the gate's lint target (p.23).
- **A fixed tool per language in the plugin** instead of the project's own commands: the note names the project's commands in `sdlc.yaml`; ruff stays only as Python's default.
- **The quarantine runbook for Node and Rust now** (maintain-act's option C, T24): no project needs it; recorded under this entry's open items.

## Decisions it touches

None amended. 6 is kept (CI loads the hooks, this one included, from the pinned plugin). `sdlc.yaml` stays a guardrail file the owner changes in a reviewed PR; decision 6 does not name it, the protected-paths hook protects it (`plugin/hooks/protected_paths.py:46`). 7 is kept (the hook is Python and calls the project's tools). 29 is kept: once R10 is built, a red lint target starts a fix round by itself, and this hook catches part of what would have started one. No decision file is written and no number is reserved.

## Order

In the study's "rest in any order" group (the record, section 8 part 2: T3, T5, T6, T7, T8, T11, ...); the Order column is the owner's. It depends on no other proposal: it changes `plugin/hooks/format_on_edit.py`, `plugin/init/` and `template/sdlc.yaml`, so it ships as a plugin version with tests on Windows and Linux and reaches a project through the owner's pin bump and `/sdlc-init`. Related, not blocking: R10 (decision 29), R30 (T5, the change-0000 PR where the proposed commands appear), R34 (T11, the Rust fix proof), R41 (T24, the runbook left here), R44 (T29, from the crosswalk row x-sandbox, where the CI sandbox's open items sit), R27 (T1's sources, for any hook that backs a skill) and R45 (T4, the setting's name). The parts it takes:

| Part | Where | When |
|---|---|---|
| The `.cmd` shim check on Windows | `docs/notes/` | The session's: first, before the design (see What to settle) |
| The per-file-type mapping, ruff the default, failing open; the stripped environment and the commands in the log line (the session's, see What to settle) | `plugin/hooks/format_on_edit.py`, `template/sdlc.yaml`, tests | Now |
| The proposed commands: prettier and eslint from `package.json`, rustfmt from `Cargo.toml` | `plugin/init/detect.py`, `plugin/init/sdlc_init.py`, the change-0000 intent | Now, same change |
| Full Rust support (targets, the lock for tests inside source files, crates.io in the CI sandbox) | `plugin/init/`, `plugin/hooks/test_file_lock.py`, `plugin/ci/settings.ci.json` | Open in this entry; the session's: later, its own change |
| The quarantine runbook for Node and Rust | `plugin/detect/` | When a project needs it |

[^entry]: `docs/reviews/2026-09-28-playbook-vs-framework/target-design.md` T8 (Status, the owner's note, Today, Direction, Open) and its index row.
[^playbook]: `docs/reference/ai-native-sdlc-playbook.pdf` p.23.
[^record]: `docs/reviews/2026-09-28-playbook-vs-framework.md` section 7 (the build-hooks row; the re-check of 2026-10-13 against 0.3.7) and section 8 part 2 (the close table's T8 row).
[^decision-29]: `docs/decisions/29.md`; R10 is accepted and not built at `main` 5542406 (`plugin/gate/gate.py:389`: "A red target parks the change").
[^code]: `git diff --stat 619f01a 5542406 -- plugin/hooks/format_on_edit.py plugin/hooks/hooks.json plugin/hooks/_common.py plugin/init/detect.py plugin/init/sdlc_init.py plugin/ci/settings.ci.json plugin/gate/checks.py plugin/gate/gate.py template/sdlc.yaml plugin/agents/verifier.md plugin/skills/coding-standards/SKILL.md`: four files changed, 121 insertions, 1 deletion.
