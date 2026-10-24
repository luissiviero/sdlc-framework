# Verifier report: change 0004 (drive-target-and-proof-items), phase (d)

The change matches the plan. The runner's (c) record is green, every planned file and `test:` item is present, and the direct calls I made returned what the spec's Acceptance section asks for. I have one note on the spec's file list (marketplace.json) but no mismatch with the plan.

## Commands run

This is a CI session (`SDLC_GATE_COMMANDS=runner`), so I did not run the three targets. Everything in this section was **read, not run**.

**Which tree I read:** `changes/0004-drive-target-and-proof-items/evidence/gate-c.json`. It is the runner's run on commit `db321e6df06fb3b800e0f0896d832c36278c2195` of `2026-10-24T15:53:51Z`. That is the tree this phase started from, not the final one. The final tree's result belongs to the runner, which runs the three targets once after this session and shows it in the check run `sdlc/d`. Nothing in this report stands in for that.

The commits between `db321e6` and HEAD `194c53b` (`git diff --stat db321e6 HEAD`) touch only files inside `changes/0004-drive-target-and-proof-items/`, mostly evidence plus `status.yaml`. No source, test or template file changed after the run.

`gate-c.json` → `commands`: `ok: true`, `reason: "build, test and lint exit 0"`, `details.ran_by: "runner"`, no `deferred` flag.
- build: `python -m compileall -q plugin tests tasks.py .github/scripts`, exit 0, output `""`
- test: `python -m pytest`, exit 0, tail: `........s...... [ 99%] ... [100%]` / `2750 passed, 1 skipped in 382.68s (0:06:22)`
- lint: `python -m ruff check . && python -m ruff format --check .`, exit 0, output `All checks passed!` / `289 files already formatted`

`gate-c.json` → `evidence`: `ok: true`, `"evidence present: verifier.md"`, no `deferred` flag.

The first line of each log:
- `evidence/test.log`: `# python -m pytest — deferred to the runner — 2026-10-24T16:01:49Z`
- `evidence/build.log`: `# python -m compileall -q plugin tests tasks.py .github/scripts — deferred to the runner — 2026-10-24T16:01:49Z`
- `evidence/lint.log`: `# python -m ruff check . && python -m ruff format --check . — deferred to the runner — 2026-10-24T16:01:49Z`

All three logs carry the deferred mark that this session wrote, and the runner replaces them. They are not failures. I did not read any `gate-d.json`.

## Behavior exercised

I made direct Python calls (`python -I -c`), which read no `.env*` file and did not start the test runner.

**Proof grammar and comparison (R5)** via `artifacts.proof_items` / `compare_state` / `screenshot_outcome`, on a synthetic `proof/` folder:

| Item | Result |
| --- | --- |
| `s.json ok == 1` where the file holds JSON `true` | `('differs', True)` |
| `flags contains true` where the file holds `[true]` | `('matches', None)` |
| text file `t.txt line == 200` (one line is `200`) | `('matches', None)` |
| JSON `code == 200` | `('matches', None)` |
| `f == 1` where the file holds `1.0` | `('differs', 1.0)` |
| `code == 200.0` where the file holds `200` | `('differs', 200)` |
| empty text file | `('not produced', 'evidence/proof/e.txt is empty')` |
| `line == zzz` on `first\nsecond` | `('differs', 'first')` (the first line is reported as seen) |
| missing PNG | `('not produced', 'evidence/proof/home.png missing')` |
| `evidence/proof/../x.json` | `('not produced', 'evidence/proof/../x.json leaves evidence/proof/')` |

- The malformed items were refused: `the verb must be one of ==, contains, matches, not 'frobs'` and `a screenshot item names a .png file`.
- The `test:` item was read, and so was the prose line next to it. An item under a later `## Other` section was ignored.
- `strict_equal`: `[True]` vs `[1]` is False, `{"a":1}` vs `{"a":1.0}` is False, `[1,[2]]` vs `[1,[2]]` is True, `1` vs `1.0` is False, and a list vs a dict is False.

**Timeouts (R4)** with no drive / default drive / `drive_timeout: 900`:
- `commands_timeout_seconds` at None, c and d: `3000 / 3300 / 3600`. At e: `3000 / 3300 / 3900`. So 900 is capped at 600 at (c) and (d), and not at (e).
- `drive_timeout_refusal` at 900: `gate.drive_timeout=900 exceeds the 600 s the test and build jobs hold: 600 applied; ...`. With no drive or the default drive it returns `None`.
- `build_caps_minutes_needed`: `245` without a drive, `250` with one.
- `limits.drive_minutes`: `0 / 5 / 15`.
- `limits.run_caps(dict(), True)` → `(400, 180)`; with 5 drive minutes subtracted → `(400, 175)`; `run_caps(dict(), False, 500)` → `(200, 30)`, which shows the floor of 30.

**Reading the drive apart from the three targets (R3)**:
- `checks.commands_from_config` with a drive set returns `{'build','test','lint'}` only.
- `drive_from_config` returns `None` for `""`, `"  "`, `None` and a missing key, and `'npx playwright test'` when set.
- `target_logs(False)` gives the three logs; `target_logs(True)` adds `drive.log`.
- `required_evidence`: at b it is `()`; at c it is `verifier.md`; at d and e `drive.log` is added only when a drive is set.

**`/sdlc-init` proposal (R10)**: `detect.playwright_drive` proposes `npx playwright test` when `@playwright/test` is in either `dependencies` or `devDependencies`. It proposes nothing (`command=None`) when only `playwright` is present.

**Each Proof item has its test.** I matched them against the new test functions in the diff:
- `test_proof` (12 tests)
- `test_gate` (17, including the drive-removed park, the deferral in a CI session and the 600 s cap)
- `test_auto_round` (3; the judge prompt is asserted to name `drive.log` and "the record's `proof` entry"; the existing `head_matches` test at line 770 is unchanged)
- `test_gitops_lookups` (`test_only_change_folder_moved`)
- `test_ci` (4)
- `test_evidence` (3)
- `test_pr` (3, including the stale-manifest line after a source commit and not after a commit that touches only the change folder, plus the check-run summary)
- `test_release` (the evidence line rendered with the root, and the drive never re-checked)
- `test_triage`, `test_init` (6), `test_templates`, `test_base_update`, `test_commands_and_skills` (3), `test_agents` (1)
- `test_policy_skills`: an existing test was extended for the `proof/` and `screenshots/` folders and the finding text.

**Doc, skill and template edits are present**:
- `template/sdlc.yaml` has `commands.drive` with the `SDLC_PROOF_DIR` / `process.env` / `cmd.exe` sentence, and `gate.drive_timeout` / `gate.proof_image_kb` with the 600 s maximum and its arithmetic.
- The plan-template skill has "The one parse" and "The any-line rule".
- `plugin/agents/verifier.md` has the `proof/` image step.
- `plugin/agents/adversarial-reviewer.md` has angle 9, "The drive".
- `plugin/commands/sdlc-test.md` has the drive paragraph.
- `plugin/commands/sdlc-init.md` has the `process.env.SDLC_PROOF_DIR` sentence.
- The definition-of-done and ux-conventions skills both name the `proof` entry.
- `evidence/port-list.md` has its two lines, and `evidence/workflow-comments.md` has its four rows.
- The version moved from 1.0.39 to 1.0.40 in both `.claude-plugin/plugin.json` and `marketplace.json`.

**Diff scope**: `git diff --stat f39fa65 HEAD` outside `changes/` touches only `plugin/`, `template/sdlc.yaml`, `tests/` and `.claude-plugin/`. This repository's `sdlc.yaml`, `.github/workflows/`, `template/.github/workflows/` and `CLAUDE.md` are untouched.

## Not exercised

- **The targets on the final tree.** I did not run them; the runner's `sdlc/d` check run judges them.
- **The test suite.** I did not run it, not even with `-k`. The `test:` items were checked by reading them, not by running them.
- **The runner's step end to end.** I did not call `run_deferred_commands` or `run_drive` with a real subprocess. That covers clearing `proof/`, the image caps, writing the manifest, the single re-run of a drive that did not start, and the drive's environment as actually passed to it.
- **The gate checks.** I did not call `check_proof`, `check_proof_items` or `check_evidence`, including the in-session deferral and the drive-removed park.
- **Other changed code.** I did not call `auto_round.red_targets`, the request and judge prompt, `triage.logs_for`, `collect.py`, `pr/description.evidence_status`, the release notes, `gitops.only_change_folder_moved` or the `sdlc_init` rendering, `--setup` handling or `--drive`.
- **The image caps.** I did not try any image file, by size or by count.
- **Platforms.** I ran on Linux only, not Windows. That leaves out the read-only file clearing in `clear_proof_dir` and the `cmd.exe` expansion of `%SDLC_PROOF_DIR%`.
- **A real Playwright project.** No drive was run against one.
- **The four workflow timeout comments.** These are proposals for the owner in `evidence/workflow-comments.md`, not applied, so they were not checked in the workflows.
- **`python tasks.py version-check`.** Not run. I only read the version fields.

## Mismatches with plan.md / spec.md

None against the plan.

- **Note on spec.md:606** ("No file outside `plugin/`, `template/`, `tests/`, `.claude-plugin/plugin.json` and the change folder changes"): `.claude-plugin/marketplace.json` also changed. plan.md:107-108 records this as a phase (c) addition that `version-check` requires, so the plan accounts for it.
- **Working tree, not committed and not part of the change's diff:** `tests/fixtures/sample-python-project/.env` shows as modified, and `CLAUDE.local.md` and `policies/` are untracked. I did not judge them. They are left for the session that commits to look at.

## Verdict

matches the plan
