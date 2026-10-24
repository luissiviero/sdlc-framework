# Plan: Drive target and proof items (from intent.md 2026-10-23, spec.md 2026-10-24)

Read against `main` at `db47dbb` (plugin.json 1.0.39) with Read, Grep and Glob only. The
spec's requirement numbers (R1 to R16) are cited beside each step. The panel's three
decisions of gate (b) are folded into steps 1, 11 and 12; the owner's review of 2026-10-24
overturned decision 1 (plain `npx playwright test`) and added the drive-removed park (step
4), the 600 s cap (step 7), the setup rule (step 11) and the port-list file (step 13).

## Files that change
- `plugin/gate/artifacts.py` — `EVIDENCE_DRIVE`, `EVIDENCE_PROOF`, `PROOF_MANIFEST`,
  `PROOF_MAX_IMAGES`, `PROOF_IMAGE_SUFFIXES`, `STATE_FILE_MAX_BYTES`; `target_logs(drive_set)`
  and `required_evidence(phase, drive_set)`; the item grammar: `PROOF_ITEM_RE`, `ProofItem`,
  `proof_items(plan_text)`, `malformed_proof_items(plan_text)`, `parse_value(text)`,
  `string_form(value)`, `compare_state(item, proof_dir) -> (outcome, seen)` (R5, R6, R8, R11)
- `plugin/gate/checks.py` — `drive_from_config(config)`, `drive_timeout(ctx, phase)` (capped
  at 600 at (c) and (d)), `drive_env(ctx)`, `clear_proof_dir`, `apply_image_caps`,
  `write_manifest`, `run_drive(ctx, head, phase)` (`details.refused` when capped),
  `judge_proof(ctx, manifest)`, `check_proof(ctx)` (c, d, e; "drive removed after gate (b)"
  when the drive is empty and the approved plan names an item), `check_proof_items(ctx)` (b); `judge_targets` names a red `drive`; `check_evidence` and `COMMAND_LOGS` read
  through `target_logs`; `EVIDENCE_DEFERRED_REASON` names the drive log when set;
  `CHECKS_BY_PHASE` gains the two checks (R2, R3, R5, R7, R9, R11)
- `plugin/gate/gate.py` — `DEFERRABLE_CHECKS` gains `proof`; `run_deferred_commands` runs
  the drive after the targets at (c), (d) and (e) only and judges `proof`;
  `write_deferred_logs` and `deferred_logs` write and read the drive log through
  `target_logs` (R2, R7)
- `plugin/gate/limits.py` — `DRIVE_TIMEOUT_MAX_SECONDS = 600`; `run_caps(gate_settings,
  build, less_minutes=0)` (floor 30), `drive_minutes(config)`; `check_limits` subtracts them
  at (e) and parks on a floor hit (R4)
- `plugin/gate/cli.py` — nothing but the docstring line naming the drive in `run-commands`
- `plugin/state/gitops.py` — `only_change_folder_moved(root, change_dir, sha)`, the body of
  `auto_round.head_matches` today, shared with the PR body (R12)
- `plugin/ci/run_phase.py` — `commands_timeout_seconds` adds the drive timeout when set,
  capped at 600 at (c) and (d); `drive_timeout_refusal(config)` beside `build_caps_refusal`,
  its reason in the result JSON; `run_caps(config, phase, env, gate_phase=None)` and
  `run_timeout_seconds(config, phase, env, gate_phase=None)` subtract the drive minutes when
  `gate_phase` is `e`; their two call sites for a session (the `--max-turns` argument in the
  argv builder, `run_phase.py:2082` today, and the `invoke(...)` call, `:3333` today) pass
  the gate phase; the arithmetic comments above `JUDGE_TIMEOUT_SECONDS` and at
  `TRIAGE_TIMEOUT_SECONDS` (R4; port-list lines, recorded in `evidence/port-list.md`, step 13)
- `plugin/ci/auto_round.py` — `red_targets` accepts a failed `proof` entry (and `evidence`
  on `drive.log`); `targets_summary`, `red_targets_request`, `REQUEST_TEXT` name the items;
  `JUDGE_PROMPT` names `drive.log` and the record's `proof` entry; `head_matches` calls
  `gitops.only_change_folder_moved` (R7, R12)
- `plugin/ci/triage.py` — `logs_for` adds `drive.log` and `proof/manifest.json` (R13)
- `plugin/evidence/collect.py` — `TARGETS` plus `drive` when set; runs `run_drive`, reports
  the items, exits 1 on a red drive or a failed approved item; `--only drive` (R2)
- `plugin/pr/description.py` — `LOG_FILES` through `target_logs`; `evidence_status(change_dir,
  phase, root)` adds the drive state, the proof line, the `.gitkeep`-free count and the
  manifest's commit (only when the tree moved beyond the change folder since it); the
  bullets' call passes the root the builder holds; `_auto_round_line` renders a `proof`
  target as `proof (N items)` (R7, R12)
- `plugin/pr/cli.py` — `check_run_result` passes `root` to `evidence_status` (R12)
- `plugin/release/notes.py` — `_evidence_line(change_dir, root)` passes the root (R12)
- `plugin/init/detect.py` — `Detection.drive`, `playwright_drive(pkg)` (the plain `npx
  playwright test`), the setup suffix ` && npx playwright install --with-deps`, or the
  install alone when no setup was detected, `as_dict` (R10)
- `plugin/init/sdlc_init.py` — `{{DRIVE_CMD}}`, `--drive`, the report's `targets.drive`,
  the proposed block's line; `keep_build_caps` keeps calling `limits.run_caps(old_gate,
  False)` unchanged (R10)
- `plugin/skills/plan-template/SKILL.md` — the `## Proof` item grammar, with the any-line
  rule and the one parse of R5 (panel decision 3)
- `plugin/skills/ux-conventions/check.py` — images read from `evidence/proof/` and
  `evidence/screenshots/`; the finding's text names both folders (R11)
- `plugin/skills/ux-conventions/SKILL.md` — "Check" and "Deterministic backing" name the two
  folders and the gate's `proof` entry for `screenshot:` items when a drive is set (R11)
- `plugin/skills/definition-of-done/SKILL.md` — "Deterministic backing" at (d): the
  `screenshot:` items of the approved plan are checked under `proof/` when a drive is set;
  by-hand screenshots are still required by no check (R11)
- `plugin/agents/verifier.md` — the (d) step on `proof/` images (R15)
- `plugin/agents/adversarial-reviewer.md` — angle 9, the drive reads or writes (R15)
- `plugin/commands/sdlc-init.md` — the drive proposal in step 0, the plain line and the
  `process.env.SDLC_PROOF_DIR` sentence of R10 (the owner's decision on concern 1)
- `plugin/commands/sdlc-build.md` — step 4's screenshot item with a drive (R15)
- `plugin/commands/sdlc-test.md` — step 3 follows the drive; the "evidence missing" sentence
  goes (R15)
- `template/sdlc.yaml` — `commands.drive` with its comment (the shell sentence of R1
  included), `gate.drive_timeout` with the 600 s maximum and its arithmetic in the comment,
  `gate.proof_image_kb` with its comment (R1, R4, R8)
- `template/.github/workflows/sdlc-build.yml` — timeout comment only (R4)
- `template/.github/workflows/sdlc-fix.yml` — timeout comment only: the drive's figure, the
  worst case with R51's re-check and the cancellation sentence of R4 (panel decision 2); a
  port-list file (HANDOFF rules), recorded in `evidence/port-list.md` (step 13)
- `template/.github/workflows/sdlc-test.yml` — timeout comment only (R4)
- `template/.github/workflows/sdlc-deploy.yml` — timeout comment only (R4)
- `.claude-plugin/plugin.json` — the next free patch version (R16)
- `changes/0004-drive-target-and-proof-items/evidence/port-list.md` — new: the port-list
  lines of this change (`plugin/ci/run_phase.py` and `template/.github/workflows/sdlc-fix.yml`,
  one line per file with what changed), written by the build; the session file that records
  the merge copies them to `docs/PROGRESS.md` (the build may write only `plugin/`,
  `template/`, `tests/`, `.claude-plugin/plugin.json` and the change folder)
- `tests/test_proof.py` — new: the grammar, the comparison, the caps, the manifest
- `tests/test_gate.py` — the runner's step with a drive, `check_proof` (the drive-removed
  park among its cases), `check_proof_items`, `check_evidence` with `drive.log`, the (e)
  wall clock, the 600 s cap of `drive_timeout` at (c) and (d)
- `tests/test_auto_round.py` — a failed `proof` entry is a round; the request names the
  items; the judge prompt names the drive's files; `head_matches` unchanged on the shared rule
- `tests/test_gitops_lookups.py` — `only_change_folder_moved`
- `tests/test_ci.py` — `commands_timeout_seconds`, `build_caps_minutes_needed`, `run_caps`
  and `run_timeout_seconds` with and without a drive, for (e) and for a fix round at (e);
  `drive_timeout_refusal` and the 600 s cap on a `drive_timeout` of 900
- `tests/test_evidence.py` — `collect.py` with a drive, `--only drive`, the CI mark
- `tests/test_pr.py` — `evidence_status` (the stale line only when the tree moved beyond the
  change folder, never after a record commit), the check run's summary, the auto-round line
- `tests/test_release.py` — the release notes' evidence line still renders; `recheck_targets`
  never runs a drive
- `tests/test_triage.py` — `logs_for`
- `tests/test_init.py` — the plain Playwright proposal, the setup suffix with and without a
  detected setup, `--drive`, the rendered keys, the `process.env.SDLC_PROOF_DIR` sentence in
  the rendered comment and in `sdlc-init.md`
- `tests/test_templates.py` — the four comments (the fix template's worst case and
  cancellation sentence), the three keys and the `drive_timeout` comment's 600 s maximum
- `tests/test_base_update.py` — `recheck` never runs a drive
- `tests/test_commands_and_skills.py` — the skill grammar with the any-line rule and the one
  parse, the command texts, the two policy skill sentences
- `tests/test_agents.py` — the verifier's step and the reviewer's angle
- `tests/test_policy_skills.py` — the ux check's folders and finding text

## Order of work
1. Grammar and constants (`artifacts.py`, `tests/test_proof.py`): the item regex and parser
   (`test:`, `screenshot:` with optional `vs mock/<file>`, `state:` with the three verbs and
   the `line` path), `malformed_proof_items`, `parse_value` (JSON when it parses, else the
   string), `string_form` (the string itself, else `json.dumps`), `compare_state` on a JSON
   file (dotted key, `items.0.name`), on a text file (`line`, any line, `seen` the first
   line), over 1 MiB, empty, missing path, unreadable; the panel's four cases: `== 1`
   against JSON `true` differs, `contains true` against JSON `true` matches, the text `200`
   and the JSON number 200 both match `== 200`, `1` never equals `1.0`; `target_logs` and
   `required_evidence`. Pure functions, tests first.
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
   `ok` only on approved items; `check_proof` in `CHECKS_BY_PHASE` c, d, e: with a drive,
   deferred in CI and `checked: false` by hand; with the drive empty, never deferred (in CI
   too): it reads the approved plan's items itself and is `ok` "no drive target" with no
   `items` when there is none, and fails with "drive removed after gate (b)" (the items
   listed `not produced`, a park, never a round) when the approved plan names a `state` or
   `screenshot` item, with a test for each; `judge_targets` with a fourth run;
   `check_evidence` requiring `drive.log` at (d) and (e) when the drive is set.
5. The runner's step (`gate.py`, `tests/test_gate.py`): `DEFERRABLE_CHECKS`, the drive after
   the targets in `run_deferred_commands` at (c), (d) and (e) only (gate (b) runs the step
   too, since `CHECKS_BY_PHASE["b"]` holds `check_commands`: a test asserts no drive runs
   there), `not_started` covering it (the one re-run calls `run_drive` again, which clears
   `proof/` first; a test asserts the first run's file is gone), `write_deferred_logs`
   writing `drive.log` at (c) too,
   `replaced["proof"]`; the record keeps its shape; a red drive parks like a red target; a
   missing manifest after a drive run fails `proof` with the step's own reason (no `items`,
   so never a round).
6. The round (`auto_round.py`, `tests/test_auto_round.py`): `red_targets` on a failed `proof`
   entry (also when the `commands` entry is green: today the function returns as soon as
   `commands` passed, `auto_round.py:114`, and must read `proof` first) and on `evidence`
   red on `drive.log`; `targets_summary`, `red_targets_request` and `REQUEST_TEXT` with the
   items; a failed `proof` entry without `items` still parks; `JUDGE_PROMPT` with
   `drive.log` and the `proof` entry.
7. Time (`limits.py`, `run_phase.py`, `tests/test_ci.py`, `tests/test_gate.py`):
   `limits.run_caps(..., less_minutes)` with the floor, `drive_minutes`, `check_limits` at
   (e); `commands_timeout_seconds` with the drive; `run_phase.run_caps` and
   `run_timeout_seconds` with `gate_phase`, their two session call sites passing it (the
   (e) run passes `e`; a fix round passes the change's gate phase, which the runner already
   holds as `gate_phase`); the figures 245/250, 185/190, 355, and 180 for a fix session at
   (e) with a drive, asserted; `limits.DRIVE_TIMEOUT_MAX_SECONDS = 600`, applied by
   `checks.drive_timeout(ctx, phase)` and `commands_timeout_seconds` at (c) and (d) and not
   at (e), with `run_phase.drive_timeout_refusal(config)` giving the reason beside
   `build_caps_refusal` (written in the result JSON and in the `drive` run's
   `details.refused`), asserted on a `drive_timeout` of 900; the comments.
8. By hand (`collect.py`, `tests/test_evidence.py`): `drive` in `TARGETS` when set, the
   report's `drive` block with items, `--only drive`, exit 1 on red, the CI mark skipping it.
9. The shared tree rule (`state/gitops.py`, `auto_round.py`, `tests/test_gitops_lookups.py`,
   `tests/test_auto_round.py`): `only_change_folder_moved` lifted from `head_matches`, which
   calls it; the existing `head_matches` tests stay green.
10. Readers (`description.py`, `pr/cli.py`, `release/notes.py`, `triage.py`,
    `ux-conventions/check.py`, `tests/test_pr.py`, `tests/test_release.py`,
    `tests/test_triage.py`, `tests/test_policy_skills.py`): `evidence_status` with the root
    and its three callers, the stale-proof line through the shared rule (a test commits the
    change folder after the manifest and asserts no line; another commits a source file and
    asserts the line), `_auto_round_line` with a proof target, the logs for the triage, the
    two image folders and the finding's text; `base_update` and `release` tests asserting no
    drive.
11. `/sdlc-init` (`detect.py`, `sdlc_init.py`, `template/sdlc.yaml`, `sdlc-init.md`,
    `tests/test_init.py`, `tests/test_templates.py`): `Detection.drive`, the plain
    Playwright proposal `npx playwright test` and the setup suffix (` && npx playwright
    install --with-deps` after a detected setup; the install alone when `commands.setup` is
    empty), `{{DRIVE_CMD}}`, `--drive`, the three keys with comments (the `drive_timeout`
    comment with the 600 s maximum), the `process.env.SDLC_PROOF_DIR` sentence in the
    template comment and in `sdlc-init.md` (the owner's decision on concern 1); the fixture
    Node project without Playwright gets `""`; a `package.json` with `@playwright/test`
    under `dependencies` and one under `devDependencies` each get the line.
12. Texts (`plan-template/SKILL.md` with the any-line rule and the one parse,
    `ux-conventions/SKILL.md`, `definition-of-done/SKILL.md`, `verifier.md`,
    `adversarial-reviewer.md`, `sdlc-build.md`, `sdlc-test.md`, the four workflow comments
    with the fix template's worst case and cancellation sentence (panel decision 2),
    `tests/test_commands_and_skills.py`, `tests/test_agents.py`, `tests/test_templates.py`).
13. Version bump (`.claude-plugin/plugin.json`) to the next free patch; `python tasks.py
    verify`; the port list: the build writes `evidence/port-list.md` in the change folder
    (the one place outside `plugin/`, `template/` and `tests/` it may write; spec
    Acceptance) with one line per port-list file and what changed in it:
    `plugin/ci/run_phase.py` (the lines of step 7) and the fix workflow template
    `template/.github/workflows/sdlc-fix.yml` (the comment lines of step 12). The session
    file that records this change's merge copies the lines to `docs/PROGRESS.md`'s "The
    port list" (HANDOFF rules); no build commit touches `docs/`.

## Risks
- **Callers and shapes touched.** The gate record (`evidence/gate-<phase>.json`) gains a
  `proof` entry in every (c), (d) and (e) record and a fourth `runs` key `drive` when a drive
  is set; readers are `auto_round.red_targets`, `description.evidence_status`,
  `description._auto_round_line`, `triage.logs_for`, `run_phase.commands_summary`,
  `pr/cli.py check_run_result`, the judge's prompt, the verifier's and reviewer's prose, and
  R19 later. All read by name, so the additions are additive (data-conventions rule 4).
  `evidence/auto-round.json`'s `targets` may now carry an entry with `items` and no
  `exit_code`; its readers are `red_targets_request`, `targets_summary`, `_auto_round_line`
  and `judge_prompt`, all in this plan. `limits.run_caps` has four callers
  (`run_phase.run_caps`, `run_phase.build_caps_minutes_needed`, `limits.check_limits`,
  `sdlc_init.keep_build_caps`): the new argument defaults to 0 so the three that do not
  subtract are unchanged. `run_phase.run_caps` and `run_timeout_seconds` gain
  `gate_phase=None`; their other callers (`build_caps_refusal`'s neighbours, the review pass,
  the triage) pass nothing and keep today's caps. `evidence_status` gains the root; its three
  callers (`description.py`'s bullets, `pr/cli.py`, `release/notes.py`) all hold it.
  `auto_round.head_matches` keeps its signature and tests. `EVIDENCE_TARGETS` is read in six
  places (spec R11); each moves to `target_logs(drive_set)` and a project without a drive
  gets the same three. `collect.py`'s JSON gains a key; its readers are the phase commands'
  prose. `Detection` gains a field; `as_dict` and the init report tests change.
  `template/sdlc.yaml` gains three keys read only when the drive is set; an existing project
  file without them reads as before. `run_phase.commands_summary` keeps reporting the
  `commands` and `evidence` entries only; the `proof` verdict reaches the owner through the
  gate record, the PR body and the round's request, not through the runner's JSON (named,
  not changed: the intent lists `commands_summary` among the four-log lists, which it joins
  through `target_logs`).
- **The riskiest step is 5, the runner's step.** `run_deferred_commands` is the one place a
  red target becomes a park and a round; the drive adds a fourth run, a fourth log written
  even where no mark exists, and a second replaced entry. Mistakes park every CI run of every
  project at (c), (d) and (e), and a drive run at (b) would park a design on a tree with no
  implementation. Mitigations: the record's shape and order are kept (only deferred entries
  are replaced, as today); the drive runs only when `drive_from_config` is not None and the
  phase is (c), (d) or (e), so the no-drive path is the code of today plus one branch and an
  always-ok entry; the existing tests of the step (`test_the_runner_s_commands_step_*`) stay
  green untouched; the new tests run the step with a real drive one-liner on Windows and
  Linux (the platform shell, `$SDLC_PROOF_DIR` is not used in the test's command: the test
  reads the variable in Python) and once at (b) asserting no drive ran.
- **The step's own budget.** `run_gate_commands` waits `commands_timeout_seconds`; the drive's
  clearing, caps and manifest are file operations inside that budget, and the drive itself is
  bounded by `drive_timeout`. A drive that ignores `SDLC_PROOF_DIR` and writes elsewhere
  produces nothing under `proof/`: every item is `not produced`, a round; the request names
  the items, so the fix session sees it. A drive that writes thousands of files: only the
  images are capped; the manifest lists every file; the evidence commit grows. Named, not
  mitigated beyond the caps the intent fixes. A `state:` or `screenshot:` path is kept inside
  `evidence/proof/` once resolved (`..` and a link refused as `not produced`, through
  `artifacts.linked_part` and a resolved-prefix check), the cheap containment the reviewer
  asked for.
- **The approved plan at (c).** `judge_proof` reads the merge-base copy; on the fast lane
  the design commit. A plan that gains a `state` item in (c) is reported `approved: false`,
  never the bar, so a session cannot raise its own bar, and cannot lower it either (the
  approved items are judged whatever the working tree says).
- **The stale-proof line.** The runner commits the change folder right after the step
  (`commit_run_record`), so HEAD is always past the manifest's commit when the PR body is
  built; a plain "commit differs" test would fire on every PR. The line uses
  `only_change_folder_moved`, the rule `head_matches` already applies to a round's head
  (renames counted as outside, an unreadable diff read as moved), so it fires only when a
  spec, plan or source file changed after the drive ran. Step 10's two tests pin both sides.
- **The (e) cap subtraction.** `check_limits` must subtract exactly what the runner
  subtracted, or the gate's wall-clock check and the runner's kill disagree; both call
  `limits.run_caps` with `drive_minutes(config)`, the one copy. The runner knows the gate
  phase of a fix round (`gate_phase` in `run_phase.main`'s flow) while the gate's check reads
  `ctx.phase`, which is the change's phase for both; the test of step 7 asserts the two
  agree for the (e) run and for a fix round at (e). The floor of 30 prevents a nonsensical
  `drive_timeout` from zeroing the session. A fix round at (e) is already over its job's
  bound (spec concern 2, decided by the panel: named, not fixed); with the subtraction it
  stays at 290, and the fix template's comment says a job past 260 is cancelled with no park.
- **The Playwright test must write where the gate reads.** The proposed line is the plain
  `npx playwright test` (the owner's decision on concern 1): no `--output`, so Playwright's
  own traces and artifacts stay in its default folder and never meet the image caps, and
  every file the gate judges is one the test wrote to a path under
  `process.env.SDLC_PROOF_DIR` (`page.screenshot({path})`, `fs.writeFileSync`), the same on
  every platform since no shell expands anything. The template comment and `sdlc-init.md`
  say so; a test that writes elsewhere costs `not produced` items and a round, never a
  silent pass.
- **The drive disappearing after gate (b).** A project that empties `commands.drive` (or
  removes the key) after the plan was approved with `state` or `screenshot` items would,
  without the rule of step 4, pass `proof` as "no drive target"; `check_proof` reads the
  approved plan's items when the drive is empty and fails with "drive removed after gate
  (b)", a park (the owner changed a guardrail; no round can fix it). The config read is the
  gate's `ctx.config`, so the test sets the drive empty in the merge base's `sdlc.yaml`.
- **The 600 s cap.** `checks.drive_timeout` and `run_phase.commands_timeout_seconds` must
  cap the same value at the same phases, or the step's budget and the drive's timeout
  disagree; both read `limits.DRIVE_TIMEOUT_MAX_SECONDS` and the same phase set, and the
  test of step 7 asserts the two agree at (c), (d) and (e) on a `drive_timeout` of 900.
- **Windows.** `clear_proof_dir` must remove read-only files (`shutil.rmtree` with an
  `onerror` that clears the bit) and recreate the folder; paths in the manifest use `/`.
  `run_command` already runs the platform shell.
- **R26 landed on `main` (1.0.39) in `checks.py` and `description.py`**: the intent read
  1.0.38. Its lines (`_counters_line`, the check around `checks.py:1158`) are in other
  places than this change's; a merge conflict is unlikely and resolved by taking both.
- **Text tests.** `tests/test_commands_and_skills.py` asserts exact phrases of the commands
  and skills (`test_sdlc_test_flow_matches_step_28`, `test_plan_template_ratchet_proof_item_
  present`); step 12 updates them with the texts, never weakens them. The two policy skill
  texts (`definition-of-done`, `ux-conventions`) must stay true to the code after step 4:
  the gate checks `screenshot:` items under `proof/` only when a drive is set. The messages
  of `release/cli.py` and `merge_step.py` that say "commands check" for a record still
  deferred are left as they are: a `proof` entry is deferred only beside a `commands` entry,
  so the wording stays true.
- **Nothing must change before the plan can be written.**

## Options not taken
- Running the drive inside the session, so the agent iterates on the result (ArtCraft's
  loop): rejected by the intent and decision 29's reasons (the sandbox, a helper the session
  controls).
- Putting the per-item result inside the `commands` entry's details: rejected by choice 246
  (Q3): the `commands` entry is one exit code per target, and a drive can exit 0 while an
  item differs.
- A `proof` entry only when a drive is set: two record shapes for R19 and the PR body to
  read, and a reader could not tell "no drive" from "an older plugin"; the always-ok entry
  costs one line per record.
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
- Shortening the fix session at (e) to fit the fix job's 260 minutes (the advocate of panel
  item 2): a cap change for a shortfall this change did not cause (290 of 260 today), and the
  build caps are a settled guardrail (decision 32); the panel decided "named, not fixed", in
  the fix template's comment, for the owner.
- Re-running the drive on R51's merged tree: the proof would then be judged against a tree
  no gate record names; the evidence line says which commit the proof is of instead.
- Comparing the manifest's commit with HEAD by equality for the stale-proof line: it would
  fire on every PR, since the runner's record commit always follows the step; the shared
  change-folder rule is what the round's head check already uses.
- Importing `ci.auto_round.head_matches` from `pr/description.py` instead of lifting the
  rule into `state/gitops.py`: `pr/` reading `ci/` would be a new dependency direction, and
  `gitops` already holds the git lookups both read.
- Python's own equality for `==` (`True == 1`, `1 == 1.0`) and `str()` for the string form
  (the reviewer's lighter reading of panel item 3): a wrong value could pass or a right one
  fail silently on a proof item that is the owner's bar; the panel pinned the one parse,
  strict JSON-type equality and `json.dumps`.
- `npx playwright test --output "$SDLC_PROOF_DIR"` as the proposed line (the design's first
  reading of the intent's R10, kept by panel decision 1): `--output` is where Playwright
  puts its own traces and artifacts, not where `page.screenshot` writes, the `$` form fails
  silently under `cmd.exe` by hand, and the owner overturned the panel at gate (b): the plain
  line with the test writing to `process.env.SDLC_PROOF_DIR` is the one proposed.
- Parking at (c)/(d) on a `drive_timeout` over 600 s, or raising the jobs' `timeout-minutes`
  for it: the owner asked for the `build_caps_refusal` shape, which keeps the run going on a
  figure the job holds and records why; the park is kept for the (e) floor, where the value
  takes minutes from the session.
- A `proof/` skeleton drive for Python projects: a green drive that proves nothing, and
  project content written by the plugin (D8).
- Substituting `$SDLC_PROOF_DIR` textually in `collect.py` for Windows: the drive line is the
  owner's and runs through the platform shell as the three targets do; a substitution would
  make the by-hand run differ from the runner's (spec concern 1, decided by the panel).
- Reading the drive and HEAD inside `evidence_status` from the change folder's parents
  instead of a `root` argument: the change folder is always under `<root>/changes/`, but the
  three callers already hold the root, and an explicit argument is what the coding standards
  ask for (rule 7, explicit names).

## Proof
- test: tests/test_proof.py — the grammar parses the three kinds and refuses malformed items;
  `compare_state` on JSON dotted keys, `line` (any line; `seen` the first line), the 1 MiB
  cap, an empty file, a missing path, a path outside `proof/`; the panel's four cases (`== 1`
  against `true` differs, `contains true` against JSON `true` matches, text `200` and JSON
  200 both match `== 200`, `1` is not `1.0`); the image caps by size and by count; the
  manifest's shape and its `run` from the GitHub variables.
- test: tests/test_gate.py — the runner's step with a drive set writes `drive.log` at (c),
  (d) and (e) and runs no drive at (b), clears `proof/`, judges the `proof` entry on the
  approved plan, parks on a red drive, re-runs a drive that did not start once (the second
  run's `proof/` holds nothing of the first); with the drive empty and no approved item the
  logs and verdict are today's and the record differs only by the always-ok `proof` entry;
  with the drive empty and an approved `state` or `screenshot` item, `check_proof` fails
  with "drive removed after gate (b)" and parks, not deferred in CI; `check_proof_items` at
  (b); `check_evidence` with `drive.log`; the (e) wall clock subtracts the drive minutes and
  floors at 30; `drive_timeout` capped at 600 at (c) and (d), not at (e).
- test: tests/test_auto_round.py — a failed `proof` entry with items is a red target, also
  when `commands` is green, and the request names item, expected and seen; one without items
  parks; the judge prompt names `drive.log` and the `proof` entry; `head_matches` unchanged.
- test: tests/test_gitops_lookups.py — `only_change_folder_moved` on HEAD, on a change-folder
  commit, on a source commit, on a rename into the folder, on an unknown sha.
- test: tests/test_ci.py — 245/250, 185/190 and 355 with and without a drive; 180 minutes of
  session for a fix round at (e) with a drive, 185 at (c); a `drive_timeout` of 900 counts
  600 in the step's budget at (c) and (d) with `drive_timeout_refusal`'s reason, and 900 at
  (e); `commands_from_config` keeps three keys.
- test: tests/test_evidence.py — `collect.py` runs the drive, reports items, exits 1 on red,
  skips it in a CI session.
- test: tests/test_pr.py — the evidence line's drive state, proof line, screenshot count; the
  manifest commit shown after a source commit and not after a change-folder commit; the
  check run's summary carries them; the auto-round line reads `proof (N items)`.
- test: tests/test_release.py — the release notes' evidence line renders with the root;
  `recheck_targets` never runs a drive.
- test: tests/test_triage.py — `logs_for` with the drive's files.
- test: tests/test_init.py — the plain Playwright proposal from both dependency blocks, `""`
  elsewhere, the setup suffix with and without a detected setup, `--drive`, the rendered
  keys, the `process.env.SDLC_PROOF_DIR` sentence in the rendered comment and in
  `sdlc-init.md`, no skeleton file.
- test: tests/test_templates.py — the three keys and the four comments, the fix template's
  with the worst case and the cancellation sentence, the `drive_timeout` comment's 600 s
  maximum.
- test: tests/test_base_update.py — the re-check never runs a drive.
- test: tests/test_commands_and_skills.py, tests/test_agents.py, tests/test_policy_skills.py
  — the texts (the plan skill's any-line rule and one parse among them), the two policy skill
  sentences, and the ux check's folders and finding.
- Every test above is still to be written; the existing tests named in Risks stay as they are.
- The quantifiable target (spec Acceptance): `python -m pytest` green, `ruff check` and
  `ruff format --check` clean, `compileall` silent, `python tasks.py version-check` passing;
  no file outside `plugin/`, `template/`, `tests/`, `.claude-plugin/plugin.json` and the
  change folder in the diff; `evidence/port-list.md` present with its two lines. No screen,
  no mock.
