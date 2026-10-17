---
type: Proposal
title: A fix proves itself — the gate requires the lock, and the runner shows the test red at the lock commit and green at HEAD
description: For a fix-type change gate (c) fails when the test-file lock was never set or when the lock commit changes anything but test files and the change folder; the lock is committed together with the reproducing test; the runner runs the test target at the lock commit (red expected) and at HEAD (green) outside the sandbox and records both runs in the gate record; the failing test first, the lock hook, the test_lock check, sdlc:unlock-tests, the reviews and the session's failing-test.log all stay.
status: proposed
roadmap: R34
sources:
  - id: study-entry
    resource: docs/reviews/2026-09-28-playbook-vs-framework/target-design.md
    title: "T11, confirmed at the close of the study on 2026-10-09; from the crosswalk row test-bugfix (better: the playbook; decision: blend), 2026-10-03; annotations of 2026-10-13 (R15, ArtCraft row A3) and 2026-10-14 (ArtCraft row A8, E4 and E5)"
  - id: record
    resource: docs/reviews/2026-09-28-playbook-vs-framework.md
    title: "Section 7, first bullet (the close, all 32 entries confirmed as recommended); section 8, the close table's row T11 (test-bugfix; amends: none; suggested: yes; owner: yes) and part 2 (the format and the confirmed order: T11 among \"the rest in any order\")"
  - id: crosswalk
    resource: docs/reviews/2026-09-28-playbook-vs-framework/crosswalk.json
    title: "Row test-bugfix whole; the decision field of build-hooks (T8: the Rust test-file lock open, revisited at test-bugfix)"
  - id: artcraft
    resource: docs/reviews/2026-10-13-artcraft-vs-framework.md
    title: "Row A8 (prove the failing test by reverting the fix, pdfcraft CLAUDE.md:36) with its 2026-10-14 annotation: a confirmation of T11, the extension not taken"
  - id: templates-revision
    resource: docs/reviews/2026-10-13-artcraft-vs-framework/templates-revision.md
    title: "Rows 8.1 to 8.5; E4 (accepted: keep failing-test.log, it shows why the test failed) and E5 (rejected: no extension beyond fix-type changes), the owner accepting every recommendation on 2026-10-14 (PR #189)"
  - id: ratchets
    resource: docs/proposals/ratchets.md
    title: "R15 (ArtCraft row A3, accepted 2026-10-13): the protection of tests reaches every change type (ratchets.md:127, the annotation it adds to T11); that the lock and its red/green proof stay as T11 has them is T11's own 2026-10-13 annotation in target-design.md"
  - id: playbook
    resource: docs/reference/ai-native-sdlc-playbook.pdf
    title: "p.28 step 4 (reproduce the bug as a test, confirm it fails for the reason you expect, commit it, make it pass without editing it: 'proof the bug is gone') and step 7 (the test-file hook, or review rejecting a test change); p.35 (hooks 'stop the agent editing test files during a fix task')"
  - id: decision-11
    resource: docs/decisions/11.md
    title: "Decision 11: park, never page (kept: a failed proof parks)"
  - id: decision-21
    resource: docs/decisions/21.md
    title: "Decision 21: deferred review; the panel is reserved for a fixed list, never for deterministic checks (kept)"
  - id: decision-24
    resource: docs/decisions/24.md
    title: "Decision 24: sdlc:unlock-tests is the owner's label (kept)"
  - id: decision-29
    resource: docs/decisions/29.md
    title: "Decision 29: in CI a red target starts the next fix round by itself (kept: a red run at HEAD is a red target)"
  - id: code
    resource: plugin/gate/checks.py
    title: "check_test_lock, _lock_commit, run_targets, judge_targets, CHECKS_BY_PHASE; plugin/gate/artifacts.py REQUIRED_EVIDENCE; plugin/gate/gate.py run_deferred_commands; plugin/gate/preflight.py check_test_target; plugin/ci/run_phase.py (the phase (c) preflight, commands_timeout_seconds); plugin/state/cli.py lock-tests; plugin/state/status.py; plugin/hooks/test_file_lock.py; plugin/hooks/shell_guard.py; plugin/commands/sdlc-build.md step 3; plugin/skills/plan-template/SKILL.md; read at main 5542406, plugin 1.0.1"
generated: { by: sdlc-framework-session/ccr-01de3f80-ilnomi, at: 2026-10-15T20:00:00Z }
---

# A fix proves itself — the gate requires the lock, and the runner shows the test red at the lock commit and green at HEAD

**Status: proposed (roadmap R34), from study entry T11, confirmed by the owner on 2026-10-09.** Nothing is built. It amends no decision. It adds a proof the gate checks to what a fix-type change already does, and replaces nothing. R15 (ArtCraft row A3) protects the tests that already exist, in every change type; this proposal proves that the new reproducing test of a fix failed before the fix. The two do not overlap (`templates-revision.md` row 8.5).

## The problem

A fix-type change is meant to prove itself. The session writes a test that reproduces the bug and sees it fail. It commits the test and locks the test files. Then it makes the test pass without touching it. Three of those steps rest on the session alone (the crosswalk row test-bugfix, corrected on the owner's word of 2026-10-03):

- **The lock exists only if the session runs `lock-tests`.** Gate (c) passes a fix-type change that never set the lock: `test_lock` returns "the lock is not set at HEAD".
- **Nothing checks that the test was committed before the fix.**
- **Nothing checks that the test failed.** `failing-test.log` is a prompt instruction and is not required evidence.

So a fix can reach the owner with a test that was never seen failing. ArtCraft's pdfcraft reached the same rule on its own: "A test nobody has seen fail is not evidence. This has caught two worthless tests" (pdfcraft `CLAUDE.md:36`, record row A8).

## What the article says

"For bug fixes, write the failing test first. Ask Claude to reproduce the bug as a test, run it, and confirm it fails for the reason you expect. Commit that test. Only then ask Claude to make it pass without editing the test, with the test-file hook from the final step enforcing the restriction. A test that existed before the fix, and that the agent couldn't rewrite, is proof the bug is gone" (p.28 step 4). Step 7 protects the loop: a hook that blocks edits to test files during a fix task, or, as the alternative, "check the diff in review and reject any change that touches a test" (p.28). Hooks "stop the agent editing test files during a fix task" (p.35)[^playbook].

## What the framework does today

Read at `main` 5542406, plugin 1.0.1. The entry's "Today" names no commit. It was written on 2026-10-03 and re-checked by the owner's audit of the rows T10 to T19 on 2026-10-07, when `main` was at 619f01a (plugin 0.3.5; the record, section 7), and it carries a 0.3.7 annotation for the shell guard. `git diff --stat 619f01a 5542406` over the files it cites leaves `sdlc-build.md`, `test_file_lock.py`, `state/cli.py`, `gate/gate.py` and the plan template unchanged. `checks.py` and `artifacts.py` gained only the incident's `lesson_and_eval` check and its constants (change 0003). `run_phase.py` changed elsewhere. `shell_guard.py` is new since then (0.3.7)[^code].

- **The order is a prompt.** `/sdlc-build` step 3, when `status.change_type` is `fix`, tells the session to write the test the plan's Proof names, run only that test, confirm it fails and paste the output into `evidence/failing-test.log` (`plugin/commands/sdlc-build.md:72-76`). It then commits the test with `plan.md` through `commit-phase` (`:77-78`), and then runs `lock-tests` (`:79-82`). The plan template says the same: "The build run commits it first and then locks the test files" (`plugin/skills/plan-template/SKILL.md:54-57`).
- **`lock-tests` does not commit.** It sets `tests_locked: true` and writes `status.yaml` (`plugin/state/cli.py:236-246`; `plugin/state/status.py:264-271`). So the lock rides in the next `commit-phase`, normally the first fix commit. That commit is what `_lock_commit` finds: the newest commit where `status.yaml` gained `tests_locked: true` (`plugin/gate/checks.py:1253-1265`).
- **The lock holds once set.** The hook denies edits under `sdlc.yaml: test_paths` while the change is a fix and `tests_locked` is true (the condition is `is_locked`, `plugin/hooks/test_file_lock.py:112-122`). The shell guard denies a shell write that names a locked test file (the lookup and the denial, `plugin/hooks/shell_guard.py:923-954`). `check_test_lock`, at gates (c), (d) and (e), fails any test file added, changed, renamed or deleted between the lock commit and HEAD (`checks.py:1268-1318`; `CHECKS_BY_PHASE`, `:1694-1760`). Only the owner lifts the lock: `sdlc:unlock-tests` (decision 24), judged by `owner_actions` (`checks.py:1070-1240`).
- **The gaps, verified in the code.** `check_test_lock` returns `ok` with "the lock is not set at HEAD (owner_actions judges a lift)" when the lock was never set (`checks.py:1285-1286`). It also returns `ok` when "no commit in the walked history set the lock" (`:1288-1289`). Nothing reads the lock commit's contents. `REQUIRED_EVIDENCE` at (c) names `verifier.md` only, and (d) and (e) name the three target logs and `verifier.md` (`plugin/gate/artifacts.py:84-88`). `failing-test.log` appears nowhere in `plugin/` or `template/` but `sdlc-build.md:76` (`git grep -n failing-test 5542406 -- plugin template`).
- **What the runner already runs.** Before a (c) run in CI, the runner runs the preflight in its own process (`plugin/ci/run_phase.py:1688-1691`). The preflight runs the test target and refuses auto-accept on a red one (`plugin/gate/preflight.py:293-318`, `:370`). In CI a refused preflight parks the change before the session (`run_phase.py:1692-1698`). After the session, the runner's commands step runs build, test and lint outside the sandbox, on the tree the session left. It rewrites the gate record's `commands` entry with the runs (`plugin/gate/gate.py:378-430`; `checks.py:364-406`). The record is `evidence/gate-<phase>.json` (`gate.py:11`, `:273`). The step's timeout is three targets' worth (`run_phase.py:1323-1330`). A fix round runs no preflight, as the entry says: a round runs with the phase `fix` (`run_phase.py:1629-1631`), and the preflight runs only when the phase is `c` (`:1690`).
- **The article's alternative runs too.** The adversarial reviewer asks "could the tests pass with the bug still present? were pre-existing tests weakened" (`plugin/agents/adversarial-reviewer.md:51-52`). The REVIEW.md pass at (e) holds that a fix-type diff "must not modify test files that existed before the fix" (`template/REVIEW.md:23-24`). Both are judgements.
- **No code runs the test at the lock commit.** `grep` of `checks.py` and `run_phase.py` at 5542406 finds no red-run, no lock-commit run and no ratchet. R15's first change, change 0005, has its design on `main` (PR #186, `status.yaml` at phase b) but not its build; `git grep -i ratchet 5542406 -- plugin/gate/checks.py` finds nothing.

## The proposal

Everything that runs today stays: the failing test first, the test-file lock hook, the `test_lock` gate check, `sdlc:unlock-tests` and the reviews that reject a weakened test (the owner's note). Added: a proof the gate checks.

1. **The gate requires the lock.** For a fix-type change, gate (c) fails in two cases: the lock was never set, or the lock commit changes anything but test files (and the change folder).
2. **The lock is committed with the test.** `/sdlc-build` step 3 changes so that `lock-tests` runs before the test's commit. The lock commit then holds the test and the lock together. Without this change, point 1 would park every fix, and the run in point 3 would see fix code. The plan template's line changes to match.
3. **Red at the lock commit, green at HEAD, run by the runner.** The runner also runs the test target at the lock commit, outside the sandbox. The build preflight already found the base green, so a red run there shows that the new test fails. The run at HEAD shows that it passes. Both runs go in the gate record and become the proof the gate checks, the article's "proof the bug is gone". The proof holds even where the session cannot run the test in its sandbox.
4. **`failing-test.log` stays** (the owner's acceptance of E4, 2026-10-14). The runner's red run shows that the test failed, not why. The article asks to "confirm it fails for the reason you expect" (p.28 step 4), and pdfcraft's example is a test whose result came from the wrong cause. Once this proposal is built, the session keeps writing the log it writes today.
5. **Fix-type changes only** (E5, rejected on 2026-10-14). `/sdlc-plan` asks for the change type, feature or fix (`plugin/commands/sdlc-plan.md:32`), and a reported regression is a fix (`templates-revision.md` row 8.2, E5). The incident route always files a fix (`plugin/detect/cli.py:15-20`). Only a fix has a lock commit to anchor the red run.
6. **Rust.** A unit test written inside a source file (`#[cfg(test)]`) cannot be frozen by path globs. The red/green proof still covers it (the owner's note). Freezing it stays open in T8: R33 leaves it, with full Rust support, to a later Rust change of its own, which has no R number yet.

## How it is judged

On the sample project, with three seeded fix-type changes:

- A run that skips `lock-tests` parks at gate (c).
- A run whose reproducing test passes without the fix parks at gate (c), with the green run at the lock commit in the record.
- A correct fix passes with both runs, red then green, in `gate-c.json`.

On the next real fix-type changes, each gate (c) record carries the lock commit, its red run and the green run at HEAD. The owner can read from the record alone that the test failed before the fix. A fix-type change that passes gate (c) without that proof is the failure.

## What to settle before building

| Question | Recommended |
|---|---|
| Where the two runs go in the gate record | The entry's open item. **Mine:** in the details of `test_lock` at gate (c): the lock commit's sha, the command, the exit code, the output's tail, the seconds and `ran_by`. The run at HEAD is the commands step's own test run, quoted from the `commands` entry, not a second run. With R11, the record names the workflow run as every record does |
| What a green run at the lock commit tells the owner | The entry's open item. **Mine:** a park (decision 11). "What I need from you" says the reproducing test passes without the fix, so it does not reproduce the bug, and points to `failing-test.log`. The act is `sdlc:unlock-tests`, so that the next round can rewrite the test, or a close. A fix round cannot help here, because the test is locked |
| What a red run at HEAD tells the owner | The entry's open item. **Mine:** it is a red test target, nothing new: today it parks, as every red target does. After R10 it starts the next fix round by itself (decision 29), with the lock still standing |
| Whether the lock-commit run uses the whole test target or only the test files the lock commit added | The entry's open item. **Mine:** the whole test target, which is what the owner's note names ("runs the test target at the lock commit"). `sdlc.yaml` has one test command and no per-file selector per language. A red run that comes from another test is what `failing-test.log` and the reviewers read |
| Whether the session still writes `failing-test.log` | **Settled: yes**, by E4, accepted by the owner on 2026-10-14 (`templates-revision.md:128`, `:144`; the T11 annotation) |
| Whether `failing-test.log` becomes required evidence at gate (c) for a fix | **Mine, beyond the entry:** yes, present and not empty, with nothing parsed. E4 keeps the log because it is the only record of why the test failed, and today nothing makes the session write it |
| Which commits the "test files only" rule reads | **Mine, beyond the entry:** every commit from the merge base to the lock commit, not the lock commit alone. A fix committed before the lock commit would otherwise turn the red run green (a park) or make it red for another reason |
| Where a test file outside `test_paths` (a helper, a fixture) or a Rust test inside a source file stands | **Mine:** "test files" means files under `sdlc.yaml: test_paths`, which the hook and `test_lock` already read. A fix whose reproducing test must live in a source file does not park: the owner's note says the red/green proof covers it. **Mine:** its lock commit may also change the source file that holds that test, named in the plan's Proof; fix code in that file would turn the red run green, which parks. Freezing that test after the lock stays open in T8, for the later Rust change R33 leaves it to |
| At which gates the lock-commit run happens, and how often | **Mine:** at gate (c), where the owner's note puts it, once per lock commit. Gates (d) and (e), and later rounds, quote (c)'s run by the lock commit's sha, since `test_lock` proves that the test has not changed since. A new lock after an owner's unlock is a new run |
| How the run reaches the lock commit, and the by-hand gate | **Mine:** a detached checkout of the lock commit beside the working tree, with the project's setup as for the commands step. One more target's worth goes on `commands_timeout_seconds` (`run_phase.py:1330`). A gate run by hand runs it in its own process, as the `commands` check does today (`checks.py:337-346`). A fix round runs no preflight (`run_phase.py:1629-1631`, `:1690`), so the base's green run is the one before the first (c) run |
| What gate (c) says when the owner has lifted the lock | **Mine, beyond the entry:** today `test_lock` passes any unlocked HEAD and leaves a lift to `owner_actions` (`checks.py:1285-1286`). A lift the owner recorded (`tests_unlocked_by`, `status.py:243`) is not "never set": gate (c) still fails until a new lock commit exists, and its reason says that the lock was lifted and waits for the new lock commit, not that it was never set |

## Considered and not chosen

- **Keeping the framework's mechanism as it is.** The row's relation is "same", and stays so. On 2026-10-03 the session's re-check added to its framework text what rests on the session alone (the record, section 7; the owner's note: "Row corrected"). The row asked whether the gate should check the lock and the proof, which rest on the session's own steps. The owner judged the playbook better ("better: playbook") and chose the blend.
- **Replacing the hook or the reviews with the proof.** Nothing is replaced (the owner's note: "all stay").
- **Extending the red/green runs to any change that adds a test for a reported crash or regression, whatever the change type** (ArtCraft row A8's extension, E5, rejected by the owner on 2026-10-14). A reported regression is already a fix at `/sdlc-plan`. "The spec names a regression" is prose that no check reads. Only a fix has a lock commit to anchor the red run. A feature's new test, run on the old code, fails on a missing import, which proves nothing (`templates-revision.md` rows 8.2 and 8.3). If the owner wants it later, it is a design question for this entry: a structured Proof line naming the regression test, and a red run on the merge base's source.
- **Dropping `failing-test.log` once the runner's runs are the proof.** Not chosen (E4): the exit code does not say why the test failed.
- **The session's own run as the proof.** The session can fail to run a test inside its sandbox (a nested `.env` is unreadable there, `preflight.py:287-289`). The runner's run, outside the sandbox, is the one the gate trusts, as for the commands step.

## Decisions it touches

None amended (the record's close table, row T11). 11 is kept: a failed proof parks, nobody is notified. 24 is kept: `sdlc:unlock-tests` remains the owner's label, judged by `owner_actions`. 29 is kept: a red run at HEAD is a red target, a round after R10. 21 is kept: the proof is a deterministic check and never a panel item.

## Order

In the study's confirmed order T11 sits among "the rest in any order" (the record, section 8 part 2). It needs no other candidate to be built:

- A red run at HEAD parks until R10 and starts a round after it.
- The runs go in the gate record's details until R11 gives every record its run.
- R15's change 1 (change 0005) also edits `checks.py` beside `check_test_lock`. **Mine:** build this after change 0005's build PR merges, so the two do not conflict. R15's diff from the merge base also judges a test file deleted inside the lock commit, which `test_lock` does not read.
- R43 (T26) reuses this order for a scan fix (the failing test before the patch).
- Freezing a Rust test inside a source file stays open in T8. R33 (T8) does not settle it: it leaves it, with full Rust support, to a later Rust change of its own, which has no R number yet. The red/green proof covers such a fix now.

It changes `plugin/` (including `plugin/ci/run_phase.py`), so it ships as a plugin version with tests. The parts it takes:

| Part | Where | When |
|---|---|---|
| `lock-tests` before the test's commit; the lock commit holds both | `plugin/commands/sdlc-build.md` step 3, `plugin/skills/plan-template/SKILL.md` | Now, with the gate rule below |
| Gate (c) fails a fix with no lock, or with a lock commit that changes anything but test files and the change folder (and, if the owner takes those recommendations, the commits before it and the source file that holds a Rust reproducing test) | `plugin/gate/checks.py` `check_test_lock` | Now, with the part above |
| The run at the lock commit, recorded with the HEAD run in the gate record | `plugin/gate/gate.py` `run_deferred_commands`, `checks.py`, `run_phase.py` `commands_timeout_seconds` | Now; quoted in R11's record shape when R11 lands |
| `failing-test.log` kept; required at (c) for a fix, if the owner takes that recommendation | `sdlc-build.md:76`, `plugin/gate/artifacts.py` `REQUIRED_EVIDENCE` | Now |
| A red run at HEAD starts a round | R10 (decision 29) | With R10 |
| Freezing the Rust test inside a source file | `plugin/hooks/test_file_lock.py`, in the later Rust change R33 leaves it to | With that change; open in T8 |

[^playbook]: `docs/reference/ai-native-sdlc-playbook.pdf` p.28 (step 4 and step 7) and p.35, read in `docs/reference/ai-native-sdlc-playbook.txt` at its "===== PAGE 28 =====" and "===== PAGE 35 =====" markers.
[^code]: At `main` 5542406, plugin 1.0.1 (`.claude-plugin/plugin.json`): `plugin/commands/sdlc-build.md:72-82`; `plugin/skills/plan-template/SKILL.md:54-57`; `plugin/state/cli.py:236-246`; `plugin/state/status.py:243`, `:264-271`; `plugin/hooks/test_file_lock.py:112-122`; `plugin/hooks/shell_guard.py:923-954`; `plugin/gate/checks.py:337-346`, `:364-406`, `:1070-1240`, `:1245-1318`, `:1694-1760`; `plugin/gate/artifacts.py:84-88`; `plugin/gate/gate.py:11`, `:273`, `:378-430`; `plugin/gate/preflight.py:282-318`, `:370`; `plugin/ci/run_phase.py:1323-1330`, `:1629-1631`, `:1688-1698`; `plugin/agents/adversarial-reviewer.md:51-52`; `template/REVIEW.md:23-24`; `plugin/commands/sdlc-plan.md:32`; `plugin/detect/cli.py:15-20`. `git diff --stat 619f01a 5542406` over these files: `checks.py` +94 (`lesson_and_eval`), `artifacts.py` +30 (its constants), `run_phase.py` +271/-33 (elsewhere), `shell_guard.py` new, `template/REVIEW.md` lines 27-30 only.
