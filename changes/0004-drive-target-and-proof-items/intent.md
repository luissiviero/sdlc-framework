# Intent: Drive target and proof items
Author: Claude, drafted for Luis Siviero (owner). Status: draft. Change id: 0004. Entry route: idea.
Framework change: yes

## Problem
The confidence gate judges artifacts: the spec's shape, the plan against the diff, the exit
codes of the three targets, the evidence files, the review findings, the guardrails, the
limits. Nothing judges the product. A change whose test suite is green while the product does
the wrong thing reaches the owner's review at gate (e), or production, with every check
green.

Three things make this so today (read at `main` 714f523, plugin 0.3.7):
- `sdlc.yaml` has `commands.build`, `test`, `lint` and `setup`, and nothing that runs the
  product. The screenshot loop of `/sdlc-test` step 3 keys on a mock the plan names and,
  without a browser in the session, writes a README saying so.
- `plan.md`'s Proof is free prose: "the tests that prove it, by name; for UI, the mock or
  screenshot to match". Nothing parses it, and no gate check reads `evidence/screenshots/`
  (`gate/artifacts.py:69` is a constant that only `evidence/collect.py` uses, to create the
  folder). A CLI, a library or a data pipeline has no screen, so its proof is the suite
  alone; the article's own example of a quantifiable target, "the endpoint returns 200 with
  the new field" (p.28), has no place to be written and checked.
- The verifier reads the previous phase's gate record and exercises code through direct
  calls (`plugin/agents/verifier.md`). It reads no screenshot and compares no state with an
  expectation written before the build, and it never sees the final tree: at (d) it reads
  (c)'s record, and no verifier runs at (e).

The ArtCraft study (`docs/reviews/2026-10-13-artcraft-vs-framework.md`, row A1) showed why
its agents ship working features: they act on the product and look at the result without a
person. Their mechanism is product architecture and does not transfer; a check of the product
after the session does. This is ROADMAP R14, from `docs/proposals/drive-target-and-proof.md`
as corrected and accepted by the owner on 2026-10-13 (the twelve corrections of
`docs/reviews/2026-10-13-artcraft-vs-framework/a1-revision.md`, annotated in the proposal).

## Proposed outcome
When this change is done, each of these is true and has a test:

- **A fourth optional target.** `template/sdlc.yaml: commands.drive` is one command that
  exercises the product headless and writes PNG screenshots and JSON or text state files
  into the folder named by the environment variable `SDLC_PROOF_DIR`
  (`changes/<id>-<slug>/evidence/proof/`, absolute), with `SDLC_CHANGE_ID` beside it; its
  exit status is non-zero when any step failed. Empty means none, like `deploy.command`. The
  key's comment names the two variables and the folder.
- **The runner's step runs it after the session, beside build, test and lint**, at gates
  (c), (d) and (e), never (b): in `plugin/gate/gate.py` (`run_deferred_commands`,
  `write_deferred_logs`) and `plugin/gate/checks.py` (`run_targets`, `judge_targets`), in the
  same credential-stripped environment and under the same `gate.command_timeout`; its exit
  code and output tail join the gate record's `commands` entry and `evidence/drive.log`. The
  step clears `proof/` before the run and writes `proof/manifest.json` (the commit, the
  workflow run, the phase, each file with its size), so the record names the run that
  produced the proof. A red drive follows decision 29: a round with `drive.log` as its
  constraint, a timeout a round, an infrastructure failure one re-run, the cap a park. By
  hand, `plugin/evidence/collect.py` runs it the same way. The timeout line in
  `plugin/ci/run_phase.py` (`commands_timeout_seconds`) counts four targets. Nothing new runs
  inside the session.
- **Proof items have a fixed shape.** The `plan-template` skill's `## Proof` lists one line
  per item: `- test: <name>`; `- screenshot: evidence/proof/<file>.png`, with
  `vs mock/<file>` when the spec names a mock; `- state: evidence/proof/<file> <path> ==|contains|matches <value>`,
  where `<path>` is a dotted JSON key or `line` for a text file and `matches` is a Python
  `re`. Prose stays allowed beside the items.
- **The gate compares the state on the final tree, against the plan the owner approved.** In
  the runner's step, after the drive, the gate reads the items from `plan.md` at the merge
  base (`GateContext.approved_artifact`), checks that every named proof file exists, compares
  every `state` value, and records one line per item in the gate record: `matches`,
  `differs` (with what was seen) or `not produced`. A `differs` or a `not produced` on an
  approved item is a red target under decision 29. An item the (c) session added to the plan
  is reported, never the bar. Gate (b) refuses a plan whose Proof names a `state` or
  `screenshot` item while `commands.drive` is empty, so a project without a drive loses
  nothing and a plan that needs one is caught at the design.
- **Images stay small.** `sdlc.yaml: gate.proof_image_kb` (50 by default, after filmcraft's
  golden cap) and at most ten images per run; an image over either limit is deleted by the
  runner's step before the evidence commit and recorded as `not produced`.
- **The verifier keeps the images.** `plugin/agents/verifier.md` gains one step: at (d),
  open (c)'s screenshots under `proof/` with the Read tool, compare each with the mock the
  spec names, report per item, and name the tree it read (decision 29's wording). State items
  are the gate's; the verdict `does not match the plan` covers a `differs`.
- **The adversarial reviewer reads the drive.** Its card gains one angle at (c) and (d):
  does the drive read each value from the product, or write it? The drive's files are listed
  in the plan's "Files that change".
- **The PR body shows the result.** The evidence line of `plugin/pr/description.py` gains
  "proof N, state items M of K matching", read from the gate record, and no longer counts the
  `.gitkeep` as a screenshot. The per-item Proof line is not this change: it comes with T27's
  "What you can do here" block.
- **`/sdlc-init` proposes the command where the tool exists.** When `package.json` lists
  `@playwright/test`, the detection proposes a Playwright line that writes to
  `$SDLC_PROOF_DIR` and adds the browser install to `commands.setup`; for every other
  project it proposes `""` with a comment naming the slot. No skeleton file is written.
- **The lists that know three logs know four**: `EVIDENCE_TARGETS`, `LOG_FILES`,
  `HEADER_REQUIRED_AT`, `commands_summary` and the check run.
- A plugin version bump, since `plugin/` and `template/` change; the PROGRESS record lists
  the `run_phase.py` line on the port list (choice 138).

## Affected users and systems
- The owner: reads a proof result in the PR instead of a diff, and a park when the product
  did not do what the approved plan promised.
- Every project on the plugin: one new optional key, read only when set; a project that
  leaves it empty sees no change. The sample repository takes it with its next upgrade.
- `plugin/gate/` (gate.py, checks.py, artifacts.py), `plugin/evidence/collect.py`,
  `plugin/ci/run_phase.py` (the timeout line only), `plugin/pr/description.py`,
  `plugin/init/detect.py`, `plugin/skills/plan-template/SKILL.md`,
  `plugin/agents/verifier.md`, `plugin/agents/adversarial-reviewer.md`,
  `plugin/commands/sdlc-init.md`, `plugin/commands/sdlc-test.md`, `template/sdlc.yaml`,
  and their tests.
- The ArtCraft repositories: read once, nothing taken but the 50 KB figure.

## Constraints
- **After R10.** The design assumes decision 29's round mechanism. This intent is merged only
  once R10 is built: the merge starts the design run.
- The drive runs in the runner's step and by hand, never inside the session (choices 133 and
  154; decision 29). No helper runs it for the session.
- Decisions kept, none amended: 2 (the plan is written read-only at (b) and the gate reads
  the approved copy), 11 as amended by 29, 19 (the target is shaped like its adapters), 21
  (a verifier `differs` goes to the panel under deferred review; a gate-compared `state`
  item is deterministic and never a panel item), OPERATING_MODEL §2 (writer ≠ judge).
- No guardrail file is edited in a run: `template/sdlc.yaml` gains the key and its comment;
  this repository's root `sdlc.yaml` is untouched (the owner adds the key if wanted).
- The step's environment keeps the model credentials and the tokens stripped as today; the
  drive adds no credential and no network allowance. The checkout's token in `.git/config`
  is the same exposure the test target has (T29), named, not widened.
- The proof files are committed under the cap; nothing is stored outside the repository; no
  personal data.
- Python only, Windows and Linux; every piece has a test; `python -m pytest`, `ruff check`
  and `ruff format --check` green.
- Compatibility: a plan with prose-only Proof still passes gate (b); only a `state` or
  `screenshot` item needs a drive.

## Open questions
- Which folder holds the screenshots the (d) run takes by hand today
  (`evidence/screenshots/`): does it move to `proof/`, or do both stay with a rule for each?
- Do the three workflow templates' `timeout-minutes: 200` cover a fourth target, or must the
  figure rise (the fix template is on the port list)?
- Does the per-item result live in the `commands` entry's details or in a `proof` entry of
  its own, and how does its shape follow R11's record rules?
- How is Playwright detected: `devDependencies` only, or `dependencies` too?
- Does `/sdlc-test`'s by-hand screenshot loop (step 3) write its captures as `screenshot`
  items of `proof/`, so the gate checks them the same way?
