# Spec: Drive target and proof items
Change id: 0004. Status: proposed. Produced by: sdlc plugin 1.0.38, /sdlc-design prompt v1 (article p.14). Skills: coding-standards, security-baseline, ux-conventions, data-conventions, definition-of-done (plugin 1.0.38); overrides: none; policy sources: none

Read against `main` at `db47dbb` (plugin.json 1.0.39, R26 merged; this repository's pin
1.0.38), 2026-10-24. The intent's Proposed outcome is restated below as checkable
requirements; where the code of today differs from what the intent read at 1.0.38, the
difference is named.

## Requirements

### R1. The fourth optional target
- `template/sdlc.yaml: commands.drive` is one command string, empty by default (`""`, like
  `deploy.command`); empty means no drive. Its comment names `SDLC_PROOF_DIR` (the absolute
  path of `changes/<id>-<slug>/evidence/proof/`), `SDLC_CHANGE_ID`, the folder, the exit
  rule (non-zero when any step failed), the PNG / JSON / text outputs, and the rule that the
  drive runs on synthetic data, never personal data (data-conventions rule 1).
- The drive's environment is the runner's `commands_env()` (`plugin/ci/run_phase.py`: no
  model credential, no GitHub token, no git credential) plus the two variables above and the
  `commands.env` names the owner gave the targets (R61). Nothing else is added; no network
  allowance is added (security-baseline rule 7: the drive runs outside the sandbox exactly as
  the three targets do today).
- A project whose `sdlc.yaml` has no `commands.drive` key reads as empty: no behaviour, no
  log and no job figure changes for it (compatibility constraint of the intent). The one
  visible addition is uniform: its gate records at (c), (d) and (e) gain the `proof` entry of
  R7, always `ok` with the reason "no drive target: nothing to compare", so every reader
  (R19 included) reads one record shape.

### R2. Where the drive runs, and when
- The runner's step after the session (`gate.run_deferred_commands`) runs the drive once,
  after build, test and lint, at gates (c), (d) and (e), never at (b), and only when
  `commands.drive` is set. Its exit code and output tail join the gate record's `commands`
  entry as a fourth run named `drive`; its literal output is `evidence/drive.log`, written at
  (c), (d) and (e) whatever the session marked (today `write_deferred_logs` writes at (c)
  only the marked logs; the drive log has no session mark, since the session never writes it).
- The drive's timeout is `sdlc.yaml: gate.drive_timeout` (seconds, default 300), separate
  from `gate.command_timeout`. A drive killed at it is a red target (`timeout`), as a target's
  timeout is (decision 29).
- Before the drive the step empties `evidence/proof/` (every file under it) and recreates it;
  after the drive it writes `evidence/proof/manifest.json` (R6) and enforces the image caps
  (R8). A stale file never counts.
- A red drive follows decision 29 exactly as a red target: a round with `drive.log` as its
  constraint, a timeout a round, a command that did not start (126/127, no shell) one
  automatic re-run of the step and then a park, the iteration cap a park. The runner's outer
  bound on the step parks (R25 part 1, unchanged).
- Nothing new runs inside the session: `/sdlc-build`, `/sdlc-test` and the verifier never
  run the drive; the CI sandbox denies them nothing new and allows them nothing new.
- A gate run by hand inside a session (no `SDLC_GATE_COMMANDS=runner`) runs the three
  targets itself as today and never runs the drive: it records the `proof` entry (R7) as
  `ok` with `details.checked: false` and a reason naming `evidence/collect.py`.
- By hand, `python plugin/evidence/collect.py --root . --id <id>` runs the drive after the
  three targets when `commands.drive` is set, the same way (same environment additions,
  same clearing, same manifest, same caps, `drive.log`), and prints the drive's exit and the
  per-item outcomes of R7 in its JSON report; `--only drive` runs it alone. It writes no gate
  record. Inside a CI session it marks nothing for the drive (the runner's step writes
  `drive.log` without a mark to replace).

### R3. The drive is read apart from the three targets
- `checks.commands_from_config` still returns build, test and lint only; a new reader
  returns the drive command or None. `missing_targets` never asks for the drive.
- The two re-runs of the targets on another tree gain nothing: `plugin/ci/base_update.py`
  `recheck` (R51) and `plugin/release/cli.py` `recheck_targets` keep running
  `commands_from_config`'s three. When the branch moves after the gate and R51's check 12
  re-checks the merged tree, the proof is not re-run; the PR's evidence bullet (R12) names the
  commit the proof is of when the tree moved beyond the change folder since it.

### R4. The job time counts only the targets that are set (intent Q2)
- `run_phase.commands_timeout_seconds` is `3 × command_timeout + drive_timeout (only when
  commands.drive is set) + 5 minutes of grace`; `build_caps_minutes_needed` follows from it.
  A project without a drive keeps every figure of today: build and fix 245 of 260, test 185
  of 200, deploy 355 of 355.
- With a drive at the default 300 s: build and fix 250 of 260, test 190 of 200.
- At (e), when the drive is set, the drive's minutes (`ceil(drive_timeout / 60)`) come out
  of the session's wall-clock cap, for the (e) run and for a fix round whose gate phase is
  (e): `limits.run_caps` takes the minutes to subtract, and both of its readers pass them,
  the runner (`--max-turns` is unchanged; the subprocess timeout reads the reduced cap) and
  the gate's wall-clock check; so the deploy job stays at 355 (115 + 5 + 55 + 10 + 125 + 45).
  The REVIEW.md pass keeps `max_wall_clock_minutes` whole (it runs no drive). The
  subtraction never takes the cap below 30 minutes; a `drive_timeout` that would is a park of
  the `limits` check at (e) with the figure, since the owner set it.
- The three steps the workflow comments leave out are named, not fixed, and no
  `timeout-minutes` is raised: `commands.setup` (`project_setup.py`, 15 minutes, more with
  the browser install R10 adds), the R18 triage session (5 minutes; deploy already reaches
  360 with it, the most a GitHub-hosted job may run) and a fix round at (e) (R51's merge and
  re-check, 45, before the fix session, 185 today and 180 with a drive, then the step, 50 or
  55, and the judge, 10: 290 of 260 today and 290 of 260 with a drive). Each workflow
  template's timeout comment (`sdlc-build.yml`, `sdlc-fix.yml`, `sdlc-test.yml`,
  `sdlc-deploy.yml`) states the arithmetic with the drive and names the three. See Flagged
  concerns, item 2, for the fix round at (e).

### R5. Proof items have a fixed shape (skill `plan-template`)
- `## Proof` of `plan.md` lists one item per line, three kinds:
  - `- test: <name>`
  - `- screenshot: evidence/proof/<file>.png`, optionally followed by ` vs mock/<file>` when
    the spec's Acceptance carries `Mock: mock/<file>` (R29, 1.0.30)
  - `- state: evidence/proof/<file> <path> ==|contains|matches <value>`, where `<path>` is a
    dotted JSON key (`status.code`, `items.0.name`) for a JSON file or `line` for a text
    file, and `<value>` is the rest of the line.
- Prose, the `- ratchet: <name> may fall, because <why>` line and any other list item stay
  allowed beside the items; only a line that starts with `test:`, `screenshot:` or `state:`
  (after the list marker) is an item, and the gate's parser reads only those.
- Comparison rules (one definition, in `plugin/gate/artifacts.py`, used by the gate and by
  `collect.py`): the expected value is parsed as JSON when it parses (`200`, `true`, `"x"`,
  `null`) and is a string otherwise; `==` compares the parsed values (so `200` equals the
  JSON number 200 and the text `200`); `contains` is substring of the seen value's string
  form, or membership when the seen value is a list; `matches` is Python `re.search` on the
  string form. With `line`, the item holds when any line of the text file satisfies the
  comparison, and `seen` reports the first line that does not, or the file's first line. A
  file over 1 MiB, unreadable, not valid JSON (for a dotted path) or missing the path is
  `not produced`, with `seen` saying which.
- A malformed item (a `state:` line with a verb other than the three, no file, a `screenshot:`
  that does not end in `.png` or does not sit under `evidence/proof/`) is refused at gate (b)
  by name and line (R9), never silently ignored.

### R6. The manifest
- `evidence/proof/manifest.json`, written by the runner's step and by `collect.py` after
  every drive run: `{"schema_version": 1, "commit": <full sha of HEAD>, "run": {"id", "url",
  "event"} (from GITHUB_RUN_ID, GITHUB_SERVER_URL/GITHUB_REPOSITORY and GITHUB_EVENT_NAME
  when set, else null), "phase", "at", "files": [{"path": <relative to proof/>, "bytes"}],
  "dropped": [{"path", "bytes", "why"}]}`. It is sorted, written with newline `\n` and
  committed with the gate evidence (data-conventions rule 6: the proof says which commit and
  run produced it). The manifest is never itself a proof file: no item may name it.

### R7. The gate compares the state on the final tree, against the approved plan
- A new gate check `proof` exists at (c), (d) and (e), in every record (R1). Inside a CI
  session its result is `ok` with `details.deferred: true` (the step replaces it, as
  `commands` and `evidence`; `DEFERRABLE_CHECKS` gains it). By hand it is `ok` with
  `details.checked: false` (R2). In the runner's step, after the drive, it is judged: the
  items are read from `plan.md` at `GateContext.approved_artifact` (the merge base, or the
  fast lane's design commit), every `screenshot` and `state` item is checked against
  `evidence/proof/` (exists; for `state`, the comparison of R5), and the entry is written
  beside `commands`.
- The entry's shape (provisional, intent Q3 second half): `{"name": "proof", "ok", "reason",
  "details": {"manifest": "evidence/proof/manifest.json", "run": <the manifest's run>,
  "commit": <the manifest's commit>, "items": [{"item": <the plan's line verbatim>, "kind":
  "state" | "screenshot", "file", "approved": true | false, "outcome": "matches" | "differs"
  | "not produced", "seen": <the value read, on a differs or a not produced>}], "dropped":
  [<the manifest's dropped entries>], "deferred"?: true, "checked"?: false}}`. `test` items
  are not listed: the suite is the `commands` entry's.
- `ok` is false when any item with `approved: true` is `differs` or `not produced`. An item
  the (c) session added to the working-tree `plan.md` (not in the approved copy) is listed
  with `approved: false`, reported, and never the bar. With `commands.drive` empty the entry
  is `ok` with reason "no drive target: nothing to compare" and no `items` (gate (b) ensured
  the approved plan names no `state` or `screenshot` item).
- A `differs` or `not produced` on an approved item is a red target under decision 29:
  `plugin/ci/auto_round.red_targets` starts a round on a failed `proof` entry as on a red
  `commands` entry (today any failed entry other than `commands`, and `evidence` on the
  same logs, parks). A red drive whose items are also `not produced` is one round, not a
  park. The round's request (`red_targets_request`, `targets_summary`) names each failed
  item with its expected value and the value seen, beside the targets' exit codes and output
  tails; `drive.log` is among the constraint's logs. The two other readers of a round's
  targets follow: the PR's "What needs you" line (`description._auto_round_line`) renders a
  proof round as `proof (N items)`, never `proof (exit None)`, and the fresh-context judge
  at the iteration cap (`auto_round.JUDGE_PROMPT`) is told to read `drive.log` and the gate
  record's `proof` entry beside the three logs.
- The `evidence` check at (d) and (e) requires `drive.log` with the collector header when
  the drive is set (`REQUIRED_EVIDENCE` is read through a helper that adds it; a red header
  parks as a red log does); never when the drive is empty. At (c) it stays optional, as the
  three logs are.
- A `state` item is deterministic and never a panel item (decision 21 as amended by 37); a
  verifier `differs` on a screenshot stays a panel item as today.

### R8. Images stay small
- `sdlc.yaml: gate.proof_image_kb` (default 50, after filmcraft's golden cap) and at most
  ten images per run (a constant). An image (`.png`, `.jpg`, `.jpeg`, `.webp`, `.gif`) over
  either limit is deleted by the step (and by `collect.py`) before the evidence commit,
  listed in the manifest's `dropped` with the reason, and an item that named it is
  `not produced`. When more than ten images were written, the ten kept are the first ten by
  sorted relative path. Non-image files have no cap but the 1 MiB read cap of R5.

### R9. Gate (b) refuses a plan that needs a drive the project does not have
- A new check at (b), `proof_items`: parks when the working-tree `plan.md` names a `state`
  or `screenshot` item while `commands.drive` is empty (its "what I need" says to set the
  drive in a reviewed PR or to drop the items), and when an item is malformed (R5). A plan
  with prose-only Proof passes as today. The config read is the gate's (`ctx.config`, the
  merge base's copy when the branch edits `sdlc.yaml`).

### R10. `/sdlc-init` proposes the command where the tool exists (intent Q4)
- `plugin/init/detect.py`: `Detection` gains `drive: Target`. For Node, when
  `detect.node_dependencies(pkg)` holds `@playwright/test`, the proposed drive is a
  Playwright line that writes under `$SDLC_PROOF_DIR` (its origin names the dependency), and
  `commands.setup` gains Playwright's browser install appended with `&&`. For every other
  project the drive is `Target(None, "", "none")`, rendered `""` with the template's comment
  naming the slot. No skeleton file is written.
- `sdlc_init.py` renders `{{DRIVE_CMD}}` into `template/sdlc.yaml` and accepts `--drive`
  (`""` = none), as `--setup` does; the detection report shows the proposal under the
  targets. `plugin/commands/sdlc-init.md` says what is detected and that the owner confirms
  it like the three targets. An existing `sdlc.yaml` without the key needs no edit.

### R11. The lists that know three logs know four, the drive's only when it is set
- `plugin/gate/artifacts.py`: `EVIDENCE_DRIVE = "drive.log"`, `EVIDENCE_PROOF = "proof"`;
  `EVIDENCE_TARGETS` keeps the three required ones, and a helper gives the four when the
  drive is set. Readers that switch to the helper: `REQUIRED_EVIDENCE` (through
  `check_evidence`), `COMMAND_LOGS` and `HEADER_REQUIRED_AT`'s readers (`checks.py`),
  `write_deferred_logs` and `deferred_logs` (`gate.py`), `LOG_FILES` (`description.py`),
  `TARGETS` (`collect.py`), `red_targets` (`auto_round.py`), `logs_for` (`triage.py`), and
  the (d) check run summary (`pr/cli.py check_run_result`, through `evidence_status`).
- `plugin/skills/ux-conventions/check.py` looks for images in `evidence/proof/` and
  `evidence/screenshots/` instead of directly in `evidence/`; its finding reads "UI changed
  but evidence/proof/ and evidence/screenshots/ hold no screenshot".
- The two skill texts that say no gate check reads a screenshot are corrected:
  `plugin/skills/definition-of-done/SKILL.md` ("Deterministic backing": at (d) the
  screenshots named as `screenshot:` items of the approved plan are checked under
  `evidence/proof/` by the gate's `proof` entry when a drive is set; by-hand screenshots
  under `evidence/screenshots/` are still required by no check) and
  `plugin/skills/ux-conventions/SKILL.md` ("Check" and "Deterministic backing": the two
  folders the check reads; rule 7's `screenshot:` item of `proof/` when a drive is set).

### R12. The PR body and the check run show the result
- `plugin/pr/description.py` `evidence_status` takes the project root beside the change
  folder and the phase (it reads `sdlc.yaml` for the drive and the git tree for the
  manifest's commit; its three callers, `description.py`'s bullets, `pr/cli.py
  check_run_result` and `release/notes.py _evidence_line`, pass it): adds `drive <state>`
  after the three logs when the drive is set; adds `proof N, state items M of K matching`
  read from the `proof` entry of the phase's gate record (N = files in the manifest, M of K =
  `matches` over approved `state` items; `proof not checked` by hand; nothing when the drive
  is empty); counts screenshots without the `.gitkeep`; and adds `proof of <sha7>, not the
  final head` only when the tree moved beyond the change folder since the manifest's
  commit, by the rule `auto_round.head_matches` applies to a round's head today (the
  manifest's commit is HEAD, or an ancestor of HEAD from which only `changes/<id>-<slug>/`
  moved): the runner's own record commit, which always follows the step
  (`commit_run_record`), never trips it. The "Needs your close look" banner stays the risk
  list's (decision 35). The per-item Proof line is R19's, not this change.

### R13. The failed run explains itself with the drive's files (R18)
- `plugin/ci/triage.py` `logs_for`: on a red `commands` entry the logs include `drive.log`
  when it exists; on a failed `proof` entry, `drive.log` and `proof/manifest.json`.

### R14. The two folders, one owner each (intent Q1)
- `evidence/proof/` is the step's: only the drive writes in it, the step clears it, the gate
  checks only it, and only it may be named by `screenshot:` and `state:` items.
- `evidence/screenshots/` stays the (d) session's by-hand folder: `collect.py` keeps creating
  it with its `.gitkeep`; the verifier and the reviewers read it; the gate never checks it.

### R15. The commands and agents follow the drive (intent Q5)
- `plugin/commands/sdlc-test.md` step 3: when `commands.drive` is set, the session captures
  nothing by hand and compares (c)'s `evidence/proof/` images with the mock, writing what it
  compared and what differs into `evidence/verifier.md`; when it is empty, step 3 stays as
  today. Its sentence "the gate treats it as evidence missing only when the plan asked for
  screenshots" goes (no code does that).
- `plugin/commands/sdlc-build.md` step 4: with a drive set, the screenshot (d) compares with
  the mock is a `- screenshot: evidence/proof/<file>.png vs mock/<file>` item added to the
  plan during (c), reported and never the bar; without one it stays prose as today. The
  drive's own files are listed in the plan's "Files that change" (the reviewer reads them).
- `plugin/agents/verifier.md` gains one step at (d): open (c)'s images under
  `evidence/proof/` with the Read tool, compare each with the mock the spec's `Mock:` line
  names, report one line per item (`matches`, `differs` with what was seen, `not produced`),
  and name the tree it read as its step 2 does (decision 29's wording). `state` items are the
  gate's and are not re-judged. The verdict `does not match the plan` covers a `differs`.
- `plugin/agents/adversarial-reviewer.md` gains one angle at (c) and (d): does the drive
  read each value from the product, or write it?

### R16. Version, tests, policies
- `.claude-plugin/plugin.json` moves to the next free patch version (`python tasks.py
  version-check`); this repository's root `sdlc.yaml` and its workflow copies are untouched
  (guardrails; the owner adds the keys and refreshes the copies with `/sdlc-init`).
- Every piece has a test; `python -m pytest`, `python -m ruff check .`, `python -m ruff
  format --check .` and `python -m compileall -q plugin tests tasks.py .github/scripts` are
  green (coding-standards rules 4 and 8; definition-of-done).
- Policies: coding-standards applies (rules 2, 3, 4, 7, 8; rule 5: no new plugin dependency,
  Playwright is the project's own and only proposed). security-baseline applies: rule 2 (the
  drive line is the owner's `sdlc.yaml` string run through the shell as the three targets
  are, never built from external data; the item regex comes from the owner-approved plan and
  runs on a file capped at 1 MiB), rule 3 (the drive's output tail lands in the gate record
  and the round's request as the targets' does; the triage lines keep passing the secrets
  check; no credential enters the drive's environment), rule 7 (no new allowed domain), rule
  8 (no risk-list item is touched: `auth`, `data migrations`, `money movement` and
  `production config` do not apply, since the change adds project configuration keys and
  reads a product's own output, touches no credential, schema or deployment, and sets
  nothing on `deploy.production`). data-conventions applies: rule 1 (the proof files are
  internal; the template comment says synthetic data; the manifest holds paths, sizes and a
  run id), rule 4 (the gate record and the `commands` entry change additively; the manifest
  is new), rule 6 (the manifest names the commit and the run). ux-conventions applies to the
  text a person reads (rule 4: every park and `need` text says what happened and what to do;
  rule 7: the folder rule of R14); no screen is touched. definition-of-done applies to each
  phase as written; its (d) line "screenshots for UI changes" is backed by the gate's
  `proof` entry for the `screenshot:` items of the approved plan when a drive is set (R11),
  and by no check otherwise, as today.

## Design

**Shape.** The drive is a fourth adapter-shaped target (decision 19) beside build, test and
lint, read by one new accessor so the three-target readers never see it. The proof is a
new gate entry judged where the drive ran, from the plan the owner approved (decision 2).
Everything the session does with proof is read-only: it names items in `plan.md` and reads
images.

**`plugin/gate/artifacts.py`** owns the grammar: the item regex (`PROOF_ITEM_RE`), the
parser `proof_items(plan_text) -> list[ProofItem]` (kind, file, path, verb, value, the
line), `malformed_proof_items(plan_text)`, the comparison `compare_state(item, proof_dir)
-> (outcome, seen)`, the manifest name, `EVIDENCE_DRIVE`, `EVIDENCE_PROOF`, and the helper
`target_logs(drive_set)` the four-log readers call. One definition, as `SPEC_SECTIONS` and
the ratchet line are today.

**`plugin/gate/checks.py`**: `drive_from_config(config) -> str | None` beside
`commands_from_config`; `drive_timeout(ctx)`; `run_drive(ctx, head, phase) -> run` (clear
`proof/`, run the command through `run_command` with the environment additions and the drive
timeout, write `drive.log`, apply the caps, write the manifest; `seconds` kept); `judge_proof
(ctx, manifest) -> CheckResult` (approved plan's items against `proof/`); `check_proof(ctx)`
for `CHECKS_BY_PHASE` c, d, e (deferred in CI, `checked: false` by hand, "no drive target"
when empty); `check_proof_items(ctx)` for (b). `judge_targets` takes the drive's run as a
fourth entry (its red reads "drive (exit n)" or "drive (timed out)"). `check_evidence` reads
the required list through the helper. The `evidence` deferred reason names the drive log
when set.

**`plugin/gate/gate.py`** `run_deferred_commands`: after the targets' runs and before the
logs are written, when the drive is set, `runs["drive"] = run_drive(...)`; the drive's
not-started exits go through `not_started` like the others (one re-run, decision 29);
`write_deferred_logs` writes `drive.log` whenever a drive run exists (no mark to find);
`replaced["proof"] = judge_proof(...)` when `proof` is among the deferred checks (the
session's gate wrote it deferred; an older record without the entry gets none, and the
step adds nothing it cannot replace: the record's shape is kept). `DEFERRABLE_CHECKS =
("commands", "evidence", "proof")`. The verdict rule is unchanged: any failed entry parks,
and `auto_round` decides whether the park is a round.

**`plugin/ci/auto_round.py`** `red_targets`: a failed `proof` entry whose details carry
`items` contributes one red entry `{"target": "proof", "items": [the failed approved items
with item, expected, seen]}`, and a failed `evidence` entry on `drive.log` is accepted as
the `evidence`-on-red-logs case is today. `targets_summary` renders `proof (2 items)`;
`red_targets_request` adds one block per failed item (`<item>: expected <value>, seen
<seen>`). `REQUEST_TEXT` says "a red target or proof item". `JUDGE_PROMPT` lists
`drive.log` and the record's `proof` entry among what the judge reads. `head_matches` keeps
its behaviour and calls the shared rule below.

**`plugin/state/gitops.py`** gains `only_change_folder_moved(root, change_dir, sha) ->
bool` (the body of `auto_round.head_matches` today: `sha` is HEAD, or an ancestor of HEAD
from which only `changes/<id>-<slug>/` moved, renames counted as outside), so the PR body's
stale-proof line (R12) and the round's head check read one rule, and `pr/` imports nothing
from `ci/`.

**`plugin/ci/run_phase.py`**: `commands_timeout_seconds` adds the drive timeout when
set; `run_caps(config, phase, env, gate_phase=None)` subtracts the drive minutes when
`gate_phase` is `e` (the (e) run passes its own phase; a fix round passes the change's
gate phase at its two call sites, the `--max-turns` line and `run_timeout_seconds`) through
`limits.run_caps(settings, build, less_minutes)`; `build_caps_minutes_needed` passes
nothing new; `commands_env()` is unchanged and the drive's two variables are added by
`run_drive`, not here. The timeout comments above `JUDGE_TIMEOUT_SECONDS` state the drive's
figure. These lines put the change on the port list (HANDOFF rules); the build's session
record lists them.

**`plugin/gate/limits.py`** `run_caps(gate_settings, build, less_minutes=0)`: subtracts
from the wall clock, never below 30; its four callers (`run_phase.run_caps`,
`run_phase.build_caps_minutes_needed`, `limits.check_limits`, `sdlc_init.keep_build_caps`)
keep their result when they pass nothing; `check_limits` passes `drive_minutes(ctx.config)`
at (e). A `drive_timeout` that would take the cap below 30 is a `limits` park with the figure.

**`plugin/evidence/collect.py`**: `TARGETS` becomes the three plus `drive` when set; the
drive runs last through the same `run_drive`; the report gains `"drive": {"exit", "seconds",
"log", "timed_out", "items": [...]}` with the per-item outcomes from `judge_proof`'s
comparison (printed, not recorded); exit 1 when the drive is red or an approved item fails.
Inside a CI session the drive is skipped with `"exit": "deferred"` and no log is written.

**`plugin/pr/description.py`**: `evidence_status(change_dir, phase, root)` reads the gate
record's `proof` entry (`load_gate`), the manifest, `sdlc.yaml` at `root` (the drive) and
the tree through `gitops.only_change_folder_moved` (no repository means no commit line);
`LOG_FILES` through the helper; the screenshot count filters `.gitkeep`;
`_auto_round_line` renders a `proof` target by its item count. The three callers pass the
root they already hold.

**`plugin/ci/triage.py`** `logs_for`: the two additions of R13.

**`plugin/init/detect.py` and `sdlc_init.py`**: `Detection.drive`, the Playwright
proposal (`npx playwright test --output "$SDLC_PROOF_DIR"`, origin "detected:
@playwright/test in package.json"; setup gains ` && npx playwright install --with-deps`),
`{{DRIVE_CMD}}`, `--drive`, the report's `targets.drive`.

**`template/sdlc.yaml`**: `commands.drive` with its comment; `gate.drive_timeout: 300` and
`gate.proof_image_kb: 50` with comments saying they are read only when the drive is set.
**Workflow templates**: comment lines only (R4). **Skills, commands, agents**: the text of
R5, R11 and R15.

**Error behaviour.** A drive that cannot start: one re-run, then a park with
`COMMANDS_CRASH_NEED`. A drive that times out or exits non-zero: a round. An approved item
that differs or was not produced: a round. A malformed item or an item without a drive: a
park at (b). An image over the cap: deleted, listed, `not produced`. A missing manifest
after the step: the `proof` check fails with "the drive ran but wrote no manifest" (the
step's own failure, a park, never a round). An unreadable approved plan: the `proof` check
fails as `plan_sync` does on no base.

**What stays unchanged.** `commands_from_config` and its two re-check callers; the
`commands` entry's shape for the three targets; `evidence/screenshots/` and its `.gitkeep`;
the fast lane; the panel's list; the close-look banner; the verifier's step 2 and 3; the
REVIEW.md pass; this repository's `sdlc.yaml` and workflow copies.

## Open questions from intent

- "The `proof` entry's final shape against R11's record rules, once R11 is built
  (provisional above)." Carried forward: R11 (ROADMAP, accepted, not built) is the owner's
  turn; this change writes the provisional shape of R7 with the `run` object (`id`, `url`,
  `event`) R11's accepted rule "every run record names its workflow run and its trigger"
  asks for, so R19 reads one shape now and R11 renames nothing it needs. Decided by the
  owner at R11's design; nothing here blocks the build.
- "`gate.drive_timeout`'s default and the jobs' arithmetic: whether taking the drive's
  minutes from the (e) session's cap is the smallest change that keeps the deploy job under
  360 with the triage step, and what the design does about the setup step and a fix round
  at (e), which the workflow comments do not count today." Answered from the code
  (`run_phase.py` `commands_timeout_seconds`, `build_caps_minutes_needed`, `limits.run_caps`;
  the four workflow templates): yes, it is the smallest change. The deploy job is 125 + 125
  + 50 + 10 + 45 = 355 today; a 300 s drive added to the step alone makes it 360, which with
  the triage step's 5 reaches 365, past the 360 GitHub allows; subtracting the same 5 from
  the (e) session leaves 355 and 360 with triage, as today. The default of 300 s is the
  intent's; the other candidate, raising `timeout-minutes`, is refused by the intent's
  constraint. The setup step and the fix round at (e) are named in the comments and not
  fixed (R4): the setup step's 15 minutes are the same today for every job and are not this
  change's; the fix round at (e) is already over its job's bound today (290 of 260) and
  stays at 290 with a drive, since the drive's minutes come out of that session's cap too
  (Flagged concerns, item 2).

## Flagged concerns

1. The Playwright line `/sdlc-init` proposes writes to `"$SDLC_PROOF_DIR"`, which the shell
   expands on the Linux runner and in a by-hand run on Linux or macOS, and which `cmd.exe`
   does not expand in a by-hand run on Windows; the intent is silent on the by-hand Windows
   case. The design proposes the `$` form unchanged (the owner confirms the line, and a
   Windows owner writes `%SDLC_PROOF_DIR%` or reads `process.env.SDLC_PROOF_DIR` in the
   Playwright config), and `collect.py` does no substitution of its own. Guess made because
   the intent does not say.
2. A fix round at (e) stays over its job's budget: the fix workflow's 260 minutes hold R51's
   merge and re-check (45 minutes), the fix session (185 minutes today, 180 with a drive),
   the commands step (50 minutes today, 55 with a drive) and the judge (10 minutes), which
   is 290 minutes today and 290 with a drive, both past 260. The design raises no
   `timeout-minutes` (the intent's constraint), takes the drive's minutes out of that
   session's cap and names the shortfall in the fix template's comment; it does not shorten
   the fix session at (e) to fit the job. Guess made because the intent asks the design to
   say which of the three uncounted steps it fixes and which it names, and does not say
   which.
3. The `line` path of a `state` item on a text file is read as "any line satisfies the
   comparison" (an `==` holds when one line equals the value; `seen` is the first
   non-matching line, or the first line), and the expected value is parsed as JSON when it
   parses, else taken as a string, so `== 200` matches a JSON number and the text `200`
   alike; the intent fixes the three verbs and the `line` word but not these two readings.
   Guess made because the intent does not say.

## Acceptance

- Unit tests, by behaviour, all green under `python -m pytest`:
  - a `sdlc.yaml` with `commands.drive` set runs the drive in the runner's step after the
    three targets, with `SDLC_PROOF_DIR` and `SDLC_CHANGE_ID` in its environment and no
    token or model credential, writes `evidence/drive.log` at (c), (d) and (e), clears
    `proof/` first and writes `manifest.json`; with it empty, nothing of this runs: the
    logs, the verdict and the job figures are those of today, and the gate record differs
    only by the always-ok `proof` entry;
  - a red or timed-out drive is a red target that starts a round with `drive.log` as its
    constraint; a drive that does not start is re-run once and then parks;
  - the `proof` entry lists the approved items with `matches` / `differs` / `not produced`;
    a `differs` on an approved item starts a round whose request names the item, the
    expected and the seen value, whose PR line reads `proof (N items)`, and whose judge
    prompt names `drive.log` and the `proof` entry; an item added in (c) is reported and
    never fails the entry;
  - an image over `gate.proof_image_kb` or past the tenth is deleted, listed in `dropped`,
    and its item is `not produced`;
  - gate (b) parks a plan that names a `state` or `screenshot` item while the drive is empty
    and a malformed item, and passes a prose-only Proof;
  - `commands_timeout_seconds`, `build_caps_minutes_needed` and the (e) caps hold the figures
    of R4 with and without a drive (a fix round at (e) with a drive: 180 minutes of session);
    the four workflow templates' comments state them;
  - `commands_from_config`, `base_update.recheck` and `release.recheck_targets` never return
    or run the drive;
  - `collect.py` runs the drive the same way, reports the items and exits 1 on a red one;
  - `evidence_status` shows `drive`, `proof N, state items M of K matching` and the
    `.gitkeep`-free screenshot count; it shows the manifest's commit only when a commit
    after it changed a file outside the change folder, and not after the runner's own
    record commit; its three callers pass the root; `auto_round.head_matches` keeps its
    behaviour on the shared rule;
  - `triage.logs_for` adds `drive.log` on a red `commands` entry and `drive.log` plus
    `proof/manifest.json` on a failed `proof` entry;
  - `/sdlc-init` proposes the Playwright drive and the browser install only when
    `@playwright/test` is a dependency, `""` otherwise, writes no skeleton, and renders the
    three new keys;
  - the `ux-conventions` check reads `proof/` and `screenshots/`, and the two skill texts
    say what the gate now checks;
  - the command, skill and agent texts carry the item grammar, the step-3 rule, the
    verifier's step and the reviewer's angle (the existing text tests extended).
- `python -m compileall -q plugin tests tasks.py .github/scripts` prints nothing and exits 0;
  `python -m ruff check . && python -m ruff format --check .` is clean.
- `.claude-plugin/plugin.json` is bumped to the next free patch and `python tasks.py
  version-check` passes.
- No file outside `plugin/`, `template/`, `tests/`, `.claude-plugin/plugin.json` and the
  change folder changes; this repository's `sdlc.yaml`, `.github/workflows/` and `CLAUDE.md`
  are untouched.
- No screen is touched: no `Mock:` line.
