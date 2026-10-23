# Intent: Drive target and proof items
Author: Claude, drafted for Luis Siviero (owner). Status: proposed. Change id: 0004. Entry route: idea.
Framework change: yes

## Problem
The confidence gate judges artifacts: the spec's shape, the plan against the diff, the exit
codes of the three targets, the evidence files, the review findings, the guardrails, the
limits. Nothing judges the product. A change whose test suite is green while the product does
the wrong thing reaches the owner's review at gate (e), or production, with every check
green.

Three things make this so today (read at `main` b9dbd9b, plugin 1.0.38, on 2026-10-23; first
drafted at `714f523`, plugin 0.3.7):
- `sdlc.yaml` has `commands.build`, `test`, `lint`, `setup` and `env`, and nothing that runs
  the product; `commands_from_config` (`plugin/gate/checks.py`) reads build, test and lint
  only. The screenshot loop of `/sdlc-test` step 3 runs when the plan's Proof or the spec's
  Acceptance names a mock, a screen or a screenshot and, without a browser in the session,
  writes a README saying so.
- `plan.md`'s Proof is free prose: "the tests that prove it, by name; the quantifiable target
  from the spec (p.27 step 3); for UI, the mock or screenshot to match", plus the `ratchet:`
  line R15 added. Nothing parses the rest of it, and no gate check reads
  `evidence/screenshots/` (`art.EVIDENCE_SCREENSHOTS` is used only by `evidence/collect.py`,
  to create the folder). A CLI, a library or a data pipeline has no screen, so its proof is
  the suite alone; the article's own example of a quantifiable target, "the endpoint returns
  200 with the new field" (p.28), has no place to be written and checked.
- The verifier reads the previous phase's gate record and exercises code through direct
  calls (`plugin/agents/verifier.md`). It reads no screenshot and compares no state with an
  expectation written before the build, and it never sees the final tree: at (d) it reads
  `gate-c.json`, and no verifier runs at (e).

The ArtCraft study (`docs/reviews/2026-10-13-artcraft-vs-framework.md`, row A1) showed why
its agents ship working features: they act on the product and look at the result without a
person. Their mechanism is product architecture and does not transfer; a check of the product
after the session does, with decision 29's rounds (fidelity partial: the article and ArtCraft
drive inside the session, p.27-28). This is ROADMAP R14, from
`docs/proposals/drive-target-and-proof.md` as corrected and accepted by the owner on
2026-10-13 (the twelve corrections of
`docs/reviews/2026-10-13-artcraft-vs-framework/a1-revision.md`), with the owner's answers of
choice 246 to the open questions of `docs/reviews/2026-10-20-0004-open-questions.md`.

## Proposed outcome
When this change is done, each of these is true and has a test:

- **A fourth optional target.** `template/sdlc.yaml: commands.drive` is one command that
  exercises the product headless and writes PNG screenshots and JSON or text state files
  into the folder named by the environment variable `SDLC_PROOF_DIR`
  (`changes/<id>-<slug>/evidence/proof/`, absolute), with `SDLC_CHANGE_ID` beside it; its
  exit status is non-zero when any step failed. Empty means none, like `deploy.command`. The
  key's comment names the two variables and the folder. The drive gets the same
  `commands.env` names as the other targets (R61).
- **The runner's step runs it after the session, beside build, test and lint**, at gates
  (c), (d) and (e), never (b): in `plugin/gate/gate.py` (`run_deferred_commands`,
  `write_deferred_logs`, `DEFERRABLE_CHECKS`) and `plugin/gate/checks.py` (`run_targets`,
  `judge_targets`), in `commands_env` (no model credential, no token; no checkout persists
  one, decision 33) and under `gate.drive_timeout` (below); its exit code and output tail
  join the gate record's `commands` entry, and the step writes `evidence/drive.log` at (c),
  (d) and (e) whatever the session marked (today `write_deferred_logs` writes at (c) only
  the logs the session marked). The session's gate leaves a deferred `proof` entry, or the
  step adds one, since `run_deferred_commands` replaces only deferred entries. A gate run by
  hand inside a session, which runs the targets itself, never runs the drive: it records the
  `proof` entry as not checked, and `collect.py` is the by-hand way to run it. The step clears `proof/`
  before the run and writes `proof/manifest.json` (the commit, the workflow run, the phase,
  each file with its size), so the record names the run that produced the proof. A red drive
  follows decision 29: a round with `drive.log` as its constraint, a timeout a round, an
  infrastructure failure one re-run, the cap a park; the runner's outer bound on the step
  parks (R25 part 1). By hand, `plugin/evidence/collect.py` runs it the same way. Nothing new
  runs inside the session.
- **The drive is read apart from the three targets.** `commands_from_config` stays three
  targets, so the targets' re-runs on a merged tree (`plugin/ci/base_update.py` `recheck`,
  R51) and on the release's merge commit (`plugin/release/cli.py` `recheck_targets`) do not
  gain it, and `missing_targets` never asks for it.
- **The job time counts only the targets that are set** (Q2, answered on the code of
  1.0.38). `commands_timeout_seconds` (`plugin/ci/run_phase.py`) and
  `build_caps_minutes_needed` count the drive only when `commands.drive` is set, so a project
  without one keeps today's figures. As the workflow comments count the phase step (session,
  commands step, judge): build and fix 245 of 260 minutes, test 185 of 200, deploy 355 of
  355. A set drive at the default 900 s brings build and fix to 260 of 260 and test to 200 of
  200, with no room left, and deploy to 370, past the 360 a GitHub-hosted job may run. So
  the drive gets its own timeout, `gate.drive_timeout` (300 s by default: build and fix 250
  of 260, test 190 of 200), and at (e) the drive's minutes come out of the (e) session's cap
  through `limits.run_caps` (the cap the session and the gate's wall-clock check read, not
  only the runner's kill), so the deploy job stays at 355; the REVIEW.md pass shares
  `max_wall_clock_minutes`. Those comments leave out three things the design run counts
  too, since they are already tight today: `commands.setup` (up to 15 minutes, more with
  Playwright's browser install), the R18 triage session after a park (5 minutes; deploy
  already reaches 360 with it), and a fix round at (e), which runs R51's merge and the
  targets' re-check (45 minutes) before its session (45 + 185 + 50 + 10 = 290 of 260
  today). The design raises no `timeout-minutes` it can avoid (the fix template is on the
  port list) and says which of these it fixes and which it names.
- **Proof items have a fixed shape.** The `plan-template` skill's `## Proof` lists one line
  per item: `- test: <name>`; `- screenshot: evidence/proof/<file>.png`, with
  `vs mock/<file>` when the spec's Acceptance carries a `Mock: mock/<file>` line (R29, built
  in 1.0.30); `- state: evidence/proof/<file> <path> ==|contains|matches <value>`,
  where `<path>` is a dotted JSON key or `line` for a text file and `matches` is a Python
  `re`. Prose and the `ratchet:` line stay allowed beside the items.
- **The gate compares the state on the final tree, against the plan the owner approved.** In
  the runner's step, after the drive, the gate reads the items from `plan.md` at the merge
  base (`GateContext.approved_artifact`), checks that every named proof file exists, compares
  every `state` value, and writes the result as a `proof` entry of its own in the gate
  record, beside `commands` (Q3, first half, choice 246). A `differs` or a `not produced` on
  an approved item is a red target under decision 29: `plugin/ci/auto_round.py`
  (`red_targets`) starts a round on a failed `proof` entry as on a red target, where today
  any failed entry other than `commands` and its own logs parks; a red drive with a
  `not produced` item is one round, not a park. The round's request
  (`red_targets_request`, `targets_summary`) names each failed item, its expected value and
  the value seen, beside the targets' exit codes and output tails. An item the (c) session
  added to the plan is reported, never the bar. Gate (b) refuses a plan whose Proof names a
  `state` or `screenshot` item while `commands.drive` is empty, so a project without a drive
  loses nothing and a plan that needs one is caught at the design. When the branch moves
  after the gate and R51's check 12 re-checks the merged tree with the three targets, the
  proof is not re-run: the PR's evidence line says the proof is of the manifest's commit,
  not the final head.
- **The `proof` entry's shape (provisional).** `{"name": "proof", "ok", "reason", "details":
  {"manifest": "evidence/proof/manifest.json", "run", "items": [{"item": <the plan's line>,
  "kind": "state" | "screenshot", "file", "approved": true | false, "outcome": "matches" |
  "differs" | "not produced", "seen": <the value read, for a differs>}], "dropped": [<images
  over the cap>]}}`. It is R19's contract for the per-item Proof line. It is provisional:
  R11's record rules (every run record names its workflow run and its trigger) are accepted
  but not built, and the design run aligns the entry with them as they stand then (Q3,
  second half).
- **Images stay small.** `sdlc.yaml: gate.proof_image_kb` (50 by default, after filmcraft's
  golden cap) and at most ten images per run; an image over either limit is deleted by the
  runner's step before the evidence commit and recorded as `not produced`.
- **Two folders, one owner each** (Q1, choice 246). `evidence/proof/` is the runner's step's:
  only `commands.drive` writes it, the step clears it, the gate checks only it, and only it is
  named by the plan's `screenshot:` items. `evidence/screenshots/` stays the (d) session's
  by-hand folder: the verifier and the reviewers read it, the gate never checks it.
- **`/sdlc-test` step 3 follows the drive** (Q5, choice 246). When `commands.drive` is set,
  step 3 stops capturing by hand and compares (c)'s `proof/` images with the mock; when it is
  empty, step 3 stays as today, writing to `evidence/screenshots/`. Its sentence that the
  gate treats a screenshots README as evidence missing, which no code does, goes. With a
  drive set, `/sdlc-build`'s instruction to name in Proof the screenshot (d) compares with
  becomes a `screenshot:` item of `proof/` added during (c), reported and never the bar;
  without one it stays prose.
- **The verifier keeps the images.** `plugin/agents/verifier.md` gains one step: at (d),
  open (c)'s screenshots under `proof/` with the Read tool, compare each with the mock the
  spec names, report per item, and name the tree it read (decision 29's wording). State items
  are the gate's; the verdict `does not match the plan` covers a `differs`.
- **The adversarial reviewer reads the drive.** Its card gains one angle at (c) and (d):
  does the drive read each value from the product, or write it? The drive's files are listed
  in the plan's "Files that change".
- **The PR body shows the result.** The evidence bullet of `plugin/pr/description.py`
  (`evidence_status`) gains "proof N, state items M of K matching", read from the `proof`
  entry, and no longer counts the `.gitkeep` as a screenshot. The "Needs your close look"
  banner (decision 35, R24) stays the risk list's. The per-item Proof line is not this
  change: it is R19's, which reads the `proof` entry above.
- **The failed run explains itself with the drive's files** (R18). `plugin/ci/triage.py`
  (`logs_for`) gives the triage session `evidence/drive.log` on a red `commands` entry and
  `drive.log` with `proof/manifest.json` on a failed `proof` entry.
- **`/sdlc-init` proposes the command where the tool exists** (Q4, choice 246). When
  `package.json` lists `@playwright/test` in `dependencies` or `devDependencies`, read through
  R33's helper `detect.node_dependencies` (`plugin/init/detect.py`), the detection proposes a
  Playwright line that writes to `$SDLC_PROOF_DIR` and adds the browser install to
  `commands.setup`; for every other project it proposes `""` with a comment naming the slot.
  No skeleton file is written.
- **The lists that know three logs know four**, the drive's only when it is set:
  `EVIDENCE_TARGETS` and `REQUIRED_EVIDENCE` (`plugin/gate/artifacts.py`), `COMMAND_LOGS`
  (`checks.py`), `LOG_FILES` (`description.py`), `TARGETS` in
  `collect.py`, `commands_summary` and the (d) check run. The `ux-conventions` check, which
  looks for images directly in `evidence/`, reads `proof/` and `screenshots/`.
- A plugin version bump, since `plugin/` and `template/` change; the session's record lists
  the `run_phase.py` lines on the port list.

## Affected users and systems
- The owner: reads a proof result in the PR instead of a diff, and a park only when the
  product still did not do what the approved plan promised at the round cap.
- Every project on the plugin: three new optional keys (`commands.drive`,
  `gate.drive_timeout`, `gate.proof_image_kb`), the two under `gate` read only when the
  drive is set; a project that leaves it empty sees no change, its job figures included. The sample
  repository takes it with its next upgrade.
- `plugin/gate/` (gate.py, checks.py, artifacts.py), `plugin/evidence/collect.py`,
  `plugin/ci/run_phase.py` (the timeout lines and the (e) wall clock),
  `plugin/ci/auto_round.py`, `plugin/ci/triage.py`, `plugin/pr/description.py`,
  `plugin/init/detect.py`, `plugin/skills/plan-template/SKILL.md`,
  `plugin/skills/ux-conventions/check.py`, `plugin/agents/verifier.md`,
  `plugin/agents/adversarial-reviewer.md`, `plugin/commands/sdlc-init.md`,
  `plugin/commands/sdlc-build.md`, `plugin/commands/sdlc-test.md`, `template/sdlc.yaml`, the workflow templates' timeout
  comments, and their tests.
- R19 (the per-item Proof line) reads the `proof` entry; R11 settles its final shape.
- The ArtCraft repositories: read once, nothing taken but the 50 KB figure.

## Constraints
- **After R10.** Met: decision 29's rounds were built in plugin 1.0.3 (PR #220).
- **The design run runs on this repository's pin.** `sdlc.yaml: plugin.version` moves to the
  plugin on `main` before this intent merges (choice 269), so the design run reads the gate,
  the templates and the skills named here.
- The drive runs in the runner's step and by hand, never inside the session (choices 133 and
  154; decision 29). No helper runs it for the session.
- Decisions kept, none amended: 2 (the plan is written read-only at (b) and the gate reads
  the approved copy), 11 as amended by 29, 19 (the target is shaped like its adapters), 21
  as amended by 37, the one review mode (a verifier `differs` goes to the panel; a
  gate-compared `state` item is deterministic and never a panel item), 35 (the close-look
  banner is the risk list's), OPERATING_MODEL §2 (writer ≠ judge).
- No guardrail file is edited in a run: `template/sdlc.yaml` gains the keys and their
  comments; this repository's root `sdlc.yaml` is untouched (the owner adds the key if
  wanted).
- The step's environment is `commands_env` as today; the drive adds no credential and no
  network allowance, and gets only the `commands.env` names the owner gave the targets.
- The proof files are committed under the cap; nothing is stored outside the repository; no
  personal data.
- Python only, Windows and Linux; every piece has a test; `python -m pytest`, `ruff check`
  and `ruff format --check` green.
- Compatibility: a plan with prose-only Proof still passes gate (b); only a `state` or
  `screenshot` item needs a drive. A project without a drive keeps every job figure.
- Lane A of wave 4 builds R26 in parallel, in `plugin/gate/checks.py` and
  `plugin/pr/description.py`, in other places of the two files (`docs/handoffs/waves.md`,
  wave 4); the design reads them as they are on the day it runs.

## Open questions
- The `proof` entry's final shape against R11's record rules, once R11 is built (provisional
  above).
- `gate.drive_timeout`'s default and the jobs' arithmetic: whether taking the drive's
  minutes from the (e) session's cap is the smallest change that keeps the deploy job under
  360 with the triage step, and what the design does about the setup step and a fix round at
  (e), which the workflow comments do not count today.

## Examples/References
- `docs/proposals/drive-target-and-proof.md` and
  `docs/reviews/2026-10-13-artcraft-vs-framework/a1-revision.md` (the twelve corrections).
- `docs/reviews/2026-10-20-0004-open-questions.md` (the five questions and the owner's
  answers of choice 246).
- filmcraft `crates/testkit/src/golden.rs:15` (`MAX_GOLDEN_BYTES = 50*1024`), the image cap's
  source.
