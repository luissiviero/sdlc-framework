# Progress — change 0004's workflow timeout comments, plugin 1.0.42 (2026-10-25)

This session is the small lane started by the central session `session_013TgyuTukXLjdZU3rmrgyRt` at the owner's request. It ran on branch `claude/0004-workflow-comments`, from `main` at `5ed1545` (#384, plugin 1.0.41). It builds follow-up 1 of the table "Change 0004's follow-ups" in `docs/handoffs/sessions/2026-10-24-ccr-545fcec0-ik69zj-final.md`: the four workflow comments of `changes/0004-drive-target-and-proof-items/evidence/workflow-comments.md`. No new choice.

## What was built
1. **The four template comments**, appended below each comment's last line and above `timeout-minutes`, wrapped at the files' 100 columns: `template/.github/workflows/sdlc-build.yml:74-77`, `sdlc-fix.yml:138-147`, `sdlc-test.yml:59-62`, `sdlc-deploy.yml:71-76`. Each is inserted as new lines, so the copies take a pure insertion.
2. **The two figures the owner corrected**: 255, not 260, in the build and fix rows (at most 600 s at (c) and (d): 185 + 60 + 10), and 195, not 200, in the test row (125 + 60 + 10); the R18 triage step is not counted in either.
3. **The deploy row's floor**, rewritten for #384: "never below 30" became "a cap already under 30 gives up nothing, and a drive that would take a cap of 30 or more below 30 parks the change before the session starts".
4. **`plugin/init/template_hashes.json`**: `python tasks.py template-hashes` adds the four new templates' hashes under 1.0.42 (eight lines, `files` and `files_marked`), which `tests/test_refresh.py::test_the_manifest_knows_every_current_template` requires. The task reads every `v*` tag: a clone without them rewrites the file wrongly, so `git fetch origin 'refs/tags/*:refs/tags/*'` first.
5. **Version**: `.claude-plugin/plugin.json` and the marketplace entry 1.0.41 → 1.0.42 (choice 270), the patch `python tasks.py next-free` named after `git fetch origin` on `5ed1545`.

## Each figure, checked against the code on `main` at 1.0.41 (`5ed1545`)
- Session caps 120 and 180: `plugin/gate/limits.py:59` and `:62`; the build caps for the build run and every fix round: `plugin/ci/run_phase.py:303` (`BUILD_CAP_PHASES`); grace 5: `run_phase.py:309`.
- Commands step 50, 55 and 60: `run_phase.py:2304` (three targets at `gate.command_timeout`, 900 s by default, `plugin/gate/checks.py:49`, plus the drive, 300 s by default, `checks.py:51`, plus the grace); the drive capped at 600 s at (c) and (d) and uncapped at (e): `limits.py:112` and `limits.drive_timeout_seconds`.
- Judge 10: `run_phase.py:272`; triage 5, not counted: `run_phase.py:257`.
- At (e) the drive's minutes come off the session's cap: `run_phase.py:414` (the runner) and `limits.py:573` (the gate's check); so the deploy job's 355 holds whatever the drive's timeout, since the commands step grows by what the session loses.
- The floor after #384: `limits.py:103` (a cap under 30 keeps its own figure), `limits.py:157-170` (`drive_floor_refusal`: no refusal when the cap is under 30, a refusal when a cap of 30 or more would go below 30), the runner's park before the session `run_phase.py:3244-3257`, the gate's park `limits.py:575`.
- R51's merge and re-check before the (e) session and a fix round at (e): `run_phase.py:3206` (45 minutes: three targets at 900 s).

## Proposed edits for the owner
The four copies in `.github/workflows/` (a guardrail; `Edit(/.github/workflows/**)` in `.claude/settings.json`, `plugin/hooks/protected_paths.py`). This session did not write them. Each is a pure insertion of the template's new lines, as `tests/test_templates.py::test_this_repository_s_workflow_copies_match_the_template` requires; the exact lines are in the PR body, under "What I need from you".

| Link | Row | What is there now | What it must become |
|---|---|---|---|
| `.github/workflows/sdlc-build.yml` | after line 73 (`# so 185 + 50 + 10, with room`) | nothing | `template/.github/workflows/sdlc-build.yml:74-77` |
| `.github/workflows/sdlc-fix.yml` | after line 137 (`# so 185 + 50 + 10, with room`) | nothing | `template/.github/workflows/sdlc-fix.yml:138-147` |
| `.github/workflows/sdlc-test.yml` | after line 58 (`# 1.0.3 (decision 29): + 10 for the judge at the iteration cap`) | nothing | `template/.github/workflows/sdlc-test.yml:59-62` |
| `.github/workflows/sdlc-deploy.yml` | after line 70 (`# 125 + 185 + 45 = 355, five under the 360 a GitHub-hosted job may run`) | nothing | `template/.github/workflows/sdlc-deploy.yml:71-76` |

Not in scope: R67, any other timeout change, any rename.

## Port list
- `template/.github/workflows/sdlc-fix.yml` — comment only: the drive's figures and the fix round at (e)'s worst case (290 of 260), above `timeout-minutes`; no step changed.
