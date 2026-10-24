# Workflow timeout comments for the owner (change 0004, spec R4)

The build could not write these lines. `tests/test_templates.py`
(`test_this_repository_s_workflow_copies_match_the_template`,
`test_fix_workflow_starts_on_request_changes_and_on_the_owner_labels`) requires this
repository's `.github/workflows/` copies to equal the rendered templates byte for byte, and
`.github/workflows/**` is a protected path no run may edit (`plugin/hooks/protected_paths.py`).
A template comment changed without its copy turns the suite red; so the four comments go in one
reviewed PR that edits each template and its copy together (or re-runs `/sdlc-init` after the
template change). Each row: the file, the comment's last line as it is now, and the sentences to
append after it, before `timeout-minutes`. The runner's own arithmetic is already in the code
(`plugin/ci/run_phase.py` above `JUDGE_TIMEOUT_SECONDS`, `plugin/gate/limits.py` beside
`DRIVE_TIMEOUT_MAX_SECONDS`) and in `template/sdlc.yaml`'s `gate.drive_timeout` comment.

| File (template and copy) | Now ends with | Append |
| --- | --- | --- |
| `template/.github/workflows/sdlc-build.yml`, `.github/workflows/sdlc-build.yml` | `# so 185 + 50 + 10, with room` | `Change 0004: a set commands.drive adds gate.drive_timeout to the commands step (300 s by default: 185 + 55 + 10 = 250 of 260; at most 600 s at (c) and (d): 260). Not counted here: commands.setup (up to 15 minutes, more with Playwright's browser install), the R18 triage step after a park (5 minutes) and a fix round at (e) (sdlc-fix.yml)` |
| `template/.github/workflows/sdlc-fix.yml`, `.github/workflows/sdlc-fix.yml` | `# so 185 + 50 + 10, with room` | `Change 0004: a set commands.drive adds gate.drive_timeout to the commands step (300 s by default: 185 + 55 + 10 = 250 of 260; at most 600 s at (c) and (d): 260). Not counted here: commands.setup (up to 15 minutes, more with Playwright's browser install) and the R18 triage step after a park (5 minutes). The worst case is a fix round at (e): R51's merge and re-check of the targets (45 minutes, only when the default branch moved) come before the session, so 45 + 185 + 50 + 10 = 290 of 260 without a drive, and 45 + 180 + 55 + 10 = 290 of 260 with one (the drive's minutes come off that session's cap). A job past 260 is cancelled by GitHub, and the park steps run only on a failed step, so such a round ends with no park; raise timeout-minutes together with SDLC_JOB_TIMEOUT_MINUTES, or amend the build caps, in a reviewed PR` |
| `template/.github/workflows/sdlc-test.yml`, `.github/workflows/sdlc-test.yml` | `# 1.0.3 (decision 29): + 10 for the judge at the iteration cap` | `Change 0004: a set commands.drive adds gate.drive_timeout to the commands step (300 s by default: 125 + 55 + 10 = 190 of 200; at most 600 s: 200). Not counted here: commands.setup (up to 15 minutes, more with Playwright's browser install) and the R18 triage step after a park (5 minutes)` |
| `template/.github/workflows/sdlc-deploy.yml`, `.github/workflows/sdlc-deploy.yml` | `# 125 + 185 + 45 = 355, five under the 360 a GitHub-hosted job may run` | `Change 0004: a set commands.drive adds gate.drive_timeout to the commands step and takes its minutes off the (e) session's wall clock (never below 30), so the job stays at 355 (115 + 5 + 55 + 10 + 125 + 45 with the default 300 s). Not counted here: commands.setup (up to 15 minutes, more with Playwright's browser install) and the R18 triage step after a park (5 minutes; 360 with it, the most a GitHub-hosted job may run)` |

Wrap each appended text at the file's comment width (`    # `, 100 columns), as the lines above it
are wrapped.
