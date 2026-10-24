# Plan: Drive target and proof items (from intent.md 2026-10-23, spec.md 2026-10-24)

Read against `main` at `db47dbb` (plugin.json 1.0.39) with Read, Grep and Glob only. The
spec's requirement numbers (R1 to R16) are cited beside each step.

## Files that change
- `plugin/gate/artifacts.py` — `EVIDENCE_DRIVE`, `EVIDENCE_PROOF`, `PROOF_MANIFEST`,
  `PROOF_MAX_IMAGES`, `PROOF_IMAGE_SUFFIXES`, `STATE_FILE_MAX_BYTES`; `target_logs(drive_set)`
  and `required_evidence(phase, drive_set)`; the item grammar: `PROOF_ITEM_RE`, `ProofItem`,
  `proof_items(plan_text)`, `malformed_proof_items(plan_text)`, `parse_expected(value)`,
  `compare_state(item, proof_dir) -> (outcome, seen)` (R5, R6, R8, R11)
- `plugin/gate/checks.py` — `drive_from_config(config)`, `drive_timeout(ctx)`,
  `drive_env(ctx)`, `clear_proof_dir`, `apply_image_caps`, `write_manifest`, `run_drive(ctx,
  head, phase)`, `judge_proof(ctx, manifest)`, `check_proof(ctx)` (c, d, e), `check_proof_items
  (ctx)` (b); `judge_targets` names a red `drive`; `check_evidence` and `COMMAND_LOGS` read
  through `target_logs`; `EVIDENCE_DEFERRED_REASON` names the drive log when set;
  `CHECKS_BY_PHASE` gains the two checks (R2, R3, R5, R7, R9, R11)
- `plugin/gate/gate.py` — `DEFERRABLE_CHECKS` gains `proof`; `run_deferred_commands` runs
  the drive after the targets and judges `proof`; `write_deferred_logs` and `deferred_logs`
  write and read the drive log through `target_logs` (R2, R7)
- `plugin/gate/limits.py` — `run_caps(gate_settings, build, less_minutes=0)` (floor 30),
  `drive_minutes(config)`; `check_limits` subtracts them at (e) and parks on a floor hit (R4)
- `plugin/gate/cli.py` — nothing but the docstring line naming the drive in `run-commands`
- `plugin/ci/run_phase.py` — `commands_timeout_seconds` adds the drive timeout when set;
  `run_caps(config, phase, env, gate_phase=None)` and `run_timeout_seconds(config, phase,
  env, gate_phase=None)` subtract the drive minutes when `gate_phase` is `e`; their two call
  sites for a session (the `--max-turns` argument in the argv builder, `run_phase.py:2082`
  today, and the `invoke(...)` call, `:3333` today) pass the gate phase; the arithmetic
  comments above `JUDGE_TIMEOUT_SECONDS` and at `TRIAGE_TIMEOUT_SECONDS` (R4; port-list
  lines, recorded in the build session's record)
- `plugin/ci/auto_round.py` — `red_targets` accepts a failed `proof` entry (and `evidence`
  on `drive.log`); `targets_summary`, `red_targets_request`, `REQUEST_TEXT` name the items
  (R7)
- `plugin/ci/triage.py` — `logs_for` adds `drive.log` and `proof/manifest.json` (R13)
- `plugin/evidence/collect.py` — `TARGETS` plus `drive` when set; runs `run_drive`, reports
  the items, exits 1 on a red drive or a failed approved item; `--only drive` (R2)
- `plugin/pr/description.py` — `LOG_FILES` through `target_logs`; `evidence_status(change_dir,
  phase, root)` adds the drive state, the proof line, the `.gitkeep`-free count and the
  manifest's commit; the bullets' call passes the root the builder holds (R12)
- `plugin/pr/cli.py` — `check_run_result` passes `root` to `evidence_status` (R12)
- `plugin/release/notes.py` — `_evidence_line(change_dir, root)` passes the root (R12)
- `plugin/init/detect.py` — `Detection.drive`, `playwright_drive(pkg)`, the setup suffix
  `npx playwright install --with-deps`, `as_dict` (R10)
- `plugin/init/sdlc_init.py` — `{{DRIVE_CMD}}`, `--drive`, the report's `targets.drive`,
  the proposed block's line; `keep_build_caps` keeps calling `limits.run_caps(old_gate,
  False)` unchanged (R10)
- `plugin/skills/plan-template/SKILL.md` — the `## Proof` item grammar (R5)
- `plugin/skills/ux-conventions/check.py` — images read from `evidence/proof/` and
  `evidence/screenshots/`; the finding's text names both folders (R11)
- `plugin/skills/ux-conventions/SKILL.md` — "Check" and "Deterministic backing" name the two
  folders and the gate's `proof` entry for `screenshot:` items when a drive is set (R11)
- `plugin/skills/definition-of-done/SKILL.md` — "Deterministic backing" at (d): the
  `screenshot:` items of the approved plan are checked under `proof/` when a drive is set;
  by-hand screenshots are still required by no check (R11)
- `plugin/agents/verifier.md` — the (d) step on `proof/` images (R15)
- `plugin/agents/adversarial-reviewer.md` — angle 9, the drive reads or writes (R15)
- `plugin/commands/sdlc-init.md` — the drive proposal in step 0 (R10)
- `plugin/commands/sdlc-build.md` — step 4's screenshot item with a drive (R15)
- `plugin/commands/sdlc-test.md` — step 3 follows the drive; the "evidence missing" sentence
  goes (R15)
- `template/sdlc.yaml` — `commands.drive`, `gate.drive_timeout`, `gate.proof_image_kb` with
  comments (R1, R4, R8)
- `template/.github/workflows/sdlc-build.yml` — timeout comment only (R4)
- `template/.github/workflows/sdlc-fix.yml` — timeout comment only (R4)
- `template/.github/workflows/sdlc-test.yml` — timeout comment only (R4)
- `template/.github/workflows/sdlc-deploy.yml` — timeout comment only (R4)
- `.claude-plugin/plugin.json` — the next free patch version (R16)
- `tests/test_proof.py` — new: the grammar, the comparison, the caps, the manifest
- `tests/test_gate.py` — the runner's step with a drive, `check_proof`, `check_proof_items`,
  `check_evidence` with `drive.log`, the (e) wall clock
- `tests/test_auto_round.py` — a failed `proof` entry is a round; the request names the items
- `tests/test_ci.py` — `commands_timeout_seconds`, `build_caps_minutes_needed`, `run_caps`
  and `run_timeout_seconds` with and without a drive, for (e) and for a fix round at (e)
- `tests/test_evidence.py` — `collect.py` with a drive, `--only drive`, the CI mark
- `tests/test_pr.py` — `evidence_status` and the check run's summary
- `tests/test_release.py` — the release notes' evidence line still renders; `recheck_targets`
  never runs a drive
- `tests/test_triage.py` — `logs_for`
- `tests/test_init.py` — the Playwright proposal, `--drive`, the rendered keys
- `tests/test_templates.py` — the four comments and the three keys
- `tests/test_base_update.py` — `recheck` never runs a drive
- `tests/test_commands_and_skills.py` — the skill grammar, the command texts, the two
  policy skill sentences
- `tests/test_agents.py` — the verifier's step and the reviewer's angle
- `tests/test_policy_skills.py` — the ux check's folders and finding text

## Order of work
1. Grammar and constants (`artifacts.py`, `tests/test_proof.py`): the item regex and parser
   (`test:`, `screenshot:` with optional `vs mock/<file>`, `state:` with the three verbs and
   the `line` path), `malformed_proof_items`, `parse_expected`, `compare_state` on a JSON
   file (dotted key, `items.0.name`), on a text file (`line`), over 1 MiB, missing path,
   unreadable; `target_logs` and `required_evidence`. Pure functions, tests first.
2. Config readers and the (b) check (`checks.py`, `tests/test_gate.py`):
   `drive_from_config` (empty, placeholder and missing read as None), `drive_timeout`
   (default 300), `check_proof_items` added to `CHECKS_BY_PHASE["b"]`: parks on an item
   without a drive and on a malformed item, passes prose-only Proof. Also the test that
   `commands_from_config` still returns three keys with a drive set.
3. The drive run (`checks.py`, `tests/test_gate.py`, `tests/test_proof.py`): `drive_env`
   (the given environment plus the two variables), `clear_proof_dir`, `run_drive` writing
   `drive.log` through `write_evidence_log`, `apply_image_caps` (size and count, sorted
   paths, `dropped`), `write_manifest` (R6's shape; `run` from the GitHub variables when
   set). Test with a drive that is a small Python one-liner writing a JSON file and a PNG-
   named file of a chosen size.
4. The judgment (`checks.py`, `tests/test_gate.py`): `judge_proof` reading
   `ctx.approved_artifact("plan.md")`, `approved: false` for working-tree-only items,
   `ok` only on approved items; `check_proof` (deferred in CI, `checked: false` by hand,
   "no drive target" when empty) in `CHECKS_BY_PHASE` c, d, e; `judge_targets` with a fourth
   run; `check_evidence` requiring `drive.log` at (d) and (e) when the drive is set.
5. The runner's step (`gate.py`, `tests/test_gate.py`): `DEFERRABLE_CHECKS`, the drive after
   the targets in `run_deferred_commands`, `not_started` covering it, `write_deferred_logs`
   writing `drive.log` at (c) too, `replaced["proof"]`; the record keeps its shape; a red
   drive parks like a red target; a missing manifest after a drive run fails `proof` with the
   step's own reason (no `items`, so never a round).
6. The round (`auto_round.py`, `tests/test_auto_round.py`): `red_targets` on a failed `proof`
   entry and on `evidence` red on `drive.log`; `targets_summary`, `red_targets_request` and
   `REQUEST_TEXT` with the items; a failed `proof` entry without `items` still parks.
7. Time (`limits.py`, `run_phase.py`, `tests/test_ci.py`, `tests/test_gate.py`):
   `limits.run_caps(..., less_minutes)` with the floor, `drive_minutes`, `check_limits` at
   (e); `commands_timeout_seconds` with the drive; `run_phase.run_caps` and
   `run_timeout_seconds` with `gate_phase`, their two session call sites passing it (the
   (e) run passes `e`; a fix round passes the change's gate phase, which the runner already
   holds as `gate_phase`); the figures 245/250, 185/190, 355, and 180 for a fix session at
   (e) with a drive, asserted; the comments.
8. By hand (`collect.py`, `tests/test_evidence.py`): `drive` in `TARGETS` when set, the
   report's `drive` block with items, `--only drive`, exit 1 on red, the CI mark skipping it.
9. Readers (`description.py`, `pr/cli.py`, `release/notes.py`, `triage.py`,
   `ux-conventions/check.py`, `tests/test_pr.py`, `tests/test_release.py`,
   `tests/test_triage.py`, `tests/test_policy_skills.py`): `evidence_status` with the root
   and its three callers, the logs for the triage, the two image folders and the finding's
   text; `base_update` and `release` tests asserting no drive.
10. `/sdlc-init` (`detect.py`, `sdlc_init.py`, `template/sdlc.yaml`, `sdlc-init.md`,
    `tests/test_init.py`, `tests/test_templates.py`): `Detection.drive`, the Playwright
    proposal and setup suffix, `{{DRIVE_CMD}}`, `--drive`, the three keys with comments; the
    fixture Node project without Playwright gets `""`; a `package.json` with
    `@playwright/test` under `dependencies` and one under `devDependencies` each get the line.
11. Texts (`plan-template/SKILL.md`, `ux-conventions/SKILL.md`, `definition-of-done/SKILL.md`,
    `verifier.md`, `adversarial-reviewer.md`, `sdlc-build.md`, `sdlc-test.md`, the four
    workflow comments, `tests/test_commands_and_skills.py`, `tests/test_agents.py`,
    `tests/test_templates.py`).
12. Version bump (`.claude-plugin/plugin.json`) to the next free patch; `python tasks.py
    verify`; the build session's record lists the `run_phase.py` lines (port list).

## Risks
- **Callers and shapes touched.** The gate record (`evidence/gate-<phase>.json`) gains a
  `proof` entry and a fourth `runs` key `drive`; readers are `auto_round.red_targets`,
  `description.evidence_status`, `triage.logs_for`, `run_phase.commands_summary`,
  `pr/cli.py check_run_result`, the verifier's and reviewer's prose, and R19 later. All read
  by name, so the additions are additive (data-conventions rule 4). `limits.run_caps` has
  four callers (`run_phase.run_caps`, `run_phase.build_caps_minutes_needed`,
  `limits.check_limits`, `sdlc_init.keep_build_caps`): the new argument defaults to 0 so the
  three that do not subtract are unchanged. `run_phase.run_caps` and `run_timeout_seconds`
  gain `gate_phase=None`; their other callers (`build_caps_refusal`'s neighbours, the
  review pass, the triage) pass nothing and keep today's caps. `evidence_status` gains the
  root; its three callers (`description.py`'s bullets, `pr/cli.py`, `release/notes.py`) all
  hold it. `EVIDENCE_TARGETS` is read in six places (spec R11); each moves to
  `target_logs(drive_set)` and a project without a drive gets the same three. `collect.py`'s
  JSON gains a key; its readers are the phase commands' prose. `Detection` gains a field;
  `as_dict` and the init report tests change. `template/sdlc.yaml` gains three keys read only
  when the drive is set; an existing project file without them reads as before.
- **The riskiest step is 5, the runner's step.** `run_deferred_commands` is the one place a
  red target becomes a park and a round; the drive adds a fourth run, a fourth log written
  even where no mark exists, and a second replaced entry. Mistakes park every CI run of every
  project at (c), (d) and (e). Mitigations: the record's shape and order are kept (only
  deferred entries are replaced, as today); the drive runs only when `drive_from_config` is
  not None, so the no-drive path is the code of today plus one branch; the existing tests of
  the step (`test_the_runner_s_commands_step_*`) stay green untouched; the new tests run the
  step with a real drive one-liner on Windows and Linux (the platform shell, `$SDLC_PROOF_DIR`
  is not used in the test's command: the test reads the variable in Python).
- **The step's own budget.** `run_gate_commands` waits `commands_timeout_seconds`; the drive's
  clearing, caps and manifest are file operations inside that budget, and the drive itself is
  bounded by `drive_timeout`. A drive that ignores `SDLC_PROOF_DIR` and writes elsewhere
  produces nothing under `proof/`: every item is `not produced`, a round; the request names
  the items, so the fix session sees it. A drive that writes thousands of files: only the
  images are capped; the manifest lists every file; the evidence commit grows. Named, not
  mitigated beyond the caps the intent fixes.
- **The approved plan at (c).** `judge_proof` reads the merge-base copy; on the fast lane
  the design commit. A plan that gains a `state` item in (c) is reported `approved: false`,
  never the bar, so a session cannot raise its own bar, and cannot lower it either (the
  approved items are judged whatever the working tree says).
- **The (e) cap subtraction.** `check_limits` must subtract exactly what the runner
  subtracted, or the gate's wall-clock check and the runner's kill disagree; both call
  `limits.run_caps` with `drive_minutes(config)`, the one copy. The runner knows the gate
  phase of a fix round (`gate_phase` in `run_phase.main`'s flow) while the gate's check reads
  `ctx.phase`, which is the change's phase for both; the test of step 7 asserts the two
  agree for the (e) run and for a fix round at (e). The floor of 30 prevents a nonsensical
  `drive_timeout` from zeroing the session. A fix round at (e) is already over its job's
  bound (spec concern 2); with the subtraction it stays at 290.
- **Playwright's `--output`.** Playwright writes test artifacts (traces, `testInfo.outputPath`)
  under `--output`; a `page.screenshot({path})` with a relative path is relative to the
  working directory, not to `--output`. The proposed line is a proposal the owner confirms;
  the template comment says the test writes its screenshots under `SDLC_PROOF_DIR`. A wrong
  line costs `not produced` items and a round, never a silent pass.
- **Windows.** `clear_proof_dir` must remove read-only files (`shutil.rmtree` with an
  `onerror` that clears the bit) and recreate the folder; paths in the manifest use `/`.
  `run_command` already runs the platform shell.
- **R26 landed on `main` (1.0.39) in `checks.py` and `description.py`**: the intent read
  1.0.38. Its lines (`_counters_line`, the check around `checks.py:1158`) are in other
  places than this change's; a merge conflict is unlikely and resolved by taking both.
- **Text tests.** `tests/test_commands_and_skills.py` asserts exact phrases of the commands
  and skills (`test_sdlc_test_flow_matches_step_28`, `test_plan_template_ratchet_proof_item_
  present`); step 11 updates them with the texts, never weakens them. The two policy skill
  texts (`definition-of-done`, `ux-conventions`) must stay true to the code after step 4:
  the gate checks `screenshot:` items under `proof/` only when a drive is set.
- **Nothing must change before the plan can be written.**

## Options not taken
- Running the drive inside the session, so the agent iterates on the result (ArtCraft's
  loop): rejected by the intent and decision 29's reasons (the sandbox, a helper the session
  controls).
- Putting the per-item result inside the `commands` entry's details: rejected by choice 246
  (Q3): the `commands` entry is one exit code per target, and a drive can exit 0 while an
  item differs.
- One `EVIDENCE_TARGETS` with four entries: every reader of the three (required logs at (d)
  and (e), `missing_targets`' wording, R51 and the release) would then require the drive;
  the helper keeps the three required and adds the fourth only when set.
- A new `drive` log mark written by the session's `collect.py` so the step "replaces" it as
  the three logs: the session never runs the drive and a mark would be one more file to
  keep in sync; the step writes `drive.log` whenever it ran the drive.
- Letting the by-hand gate compare the proof `collect.py` produced: the intent says the
  by-hand gate records `not checked`; `collect.py` prints the comparison instead, so a
  by-hand run still sees it.
- Raising `timeout-minutes` of the four jobs: refused by the intent; the drive's own
  timeout and the (e) subtraction keep every figure.
- Shortening the fix session at (e) to fit the fix job's 260 minutes: a cap change for a
  shortfall this change did not cause (290 of 260 today); named in the comments and in spec
  concern 2 for the owner.
- Re-running the drive on R51's merged tree: the proof would then be judged against a tree
  no gate record names; the evidence line says which commit the proof is of instead.
- A `proof/` skeleton drive for Python projects: a green drive that proves nothing, and
  project content written by the plugin (D8).
- Substituting `$SDLC_PROOF_DIR` textually in `collect.py` for Windows: the drive line is the
  owner's and runs through the platform shell as the three targets do; a substitution would
  make the by-hand run differ from the runner's (spec concern 1).
- Reading the drive and HEAD inside `evidence_status` from the change folder's parents
  instead of a `root` argument: the change folder is always under `<root>/changes/`, but the
  three callers already hold the root, and an explicit argument is what the coding standards
  ask for (rule 7, explicit names).

## Proof
- test: tests/test_proof.py — the grammar parses the three kinds and refuses malformed items;
  `compare_state` on JSON dotted keys, `line`, the 1 MiB cap, a missing path; the image caps
  by size and by count; the manifest's shape and its `run` from the GitHub variables.
- test: tests/test_gate.py — the runner's step with a drive set writes `drive.log` at (c),
  (d) and (e), clears `proof/`, judges the `proof` entry on the approved plan, parks on a red
  drive, re-runs a drive that did not start once; with the drive empty the record, logs and
  verdict are today's; `check_proof_items` at (b); `check_evidence` with `drive.log`; the (e)
  wall clock subtracts the drive minutes and floors at 30.
- test: tests/test_auto_round.py — a failed `proof` entry with items is a red target and the
  request names item, expected and seen; one without items parks.
- test: tests/test_ci.py — 245/250, 185/190 and 355 with and without a drive; 180 minutes of
  session for a fix round at (e) with a drive, 185 at (c); `commands_from_config` keeps
  three keys.
- test: tests/test_evidence.py — `collect.py` runs the drive, reports items, exits 1 on red,
  skips it in a CI session.
- test: tests/test_pr.py — the evidence line's drive state, proof line, screenshot count and
  manifest commit; the check run's summary carries them.
- test: tests/test_release.py — the release notes' evidence line renders with the root;
  `recheck_targets` never runs a drive.
- test: tests/test_triage.py — `logs_for` with the drive's files.
- test: tests/test_init.py — the Playwright proposal from both dependency blocks, `""`
  elsewhere, `--drive`, the rendered keys, no skeleton file.
- test: tests/test_templates.py — the three keys and the four comments.
- test: tests/test_base_update.py — the re-check never runs a drive.
- test: tests/test_commands_and_skills.py, tests/test_agents.py, tests/test_policy_skills.py
  — the texts, the two policy skill sentences, and the ux check's folders and finding.
- Every test above is still to be written; the existing tests named in Risks stay as they are.
- The quantifiable target (spec Acceptance): `python -m pytest` green, `ruff check` and
  `ruff format --check` clean, `compileall` silent, `python tasks.py version-check` passing;
  no file outside `plugin/`, `template/`, `tests/`, `.claude-plugin/plugin.json` and the
  change folder in the diff. No screen, no mock.
