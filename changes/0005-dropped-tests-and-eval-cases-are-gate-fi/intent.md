# Intent: Dropped tests and eval cases are gate findings
Author: Claude, drafted for Luis Siviero (owner). Status: draft. Change id: 0005. Entry route: idea.
Framework change: yes

## Problem
The playbook names one failure above the others in the test loop: the agent lowering the
bar to pass it ("never skip or delete a failing test", "fix the code, not the test", p.28).
The framework guards against it deterministically only in a fix-type change.

Read at `main` 0ad9215, plugin 0.3.7:
- Outside a fix-type change nothing deterministic judges the tests. `check_test_lock`
  returns `ok` for every other change type (`plugin/gate/checks.py:1282-1283`). The rest is
  prose: "Never weaken, skip or delete a test to get green" (`plugin/commands/sdlc-test.md`),
  the adversarial reviewer's angle on tests, and `REVIEW.md`, whose rule covers fix-type
  changes only. A feature change that deletes a failing test passes every gate if the rest
  is green.
- Eval cases are unprotected. A case is a folder under `evals/cases/`; it is under neither
  `test_paths` nor `protected_paths`, and moving it to a folder name that starts with a dot
  hides it from the eval runner with no deletion in the diff (`plugin/evals/run.py:142-151`).
- Even in a fix-type change, a deletion in the reproducing test's own commit, which comes
  before the lock, is not judged.

This is the first of the two changes of ROADMAP R15, from `docs/proposals/ratchets.md` as
checked against the code and accepted by the owner on 2026-10-13 (the twelve corrections of
`docs/reviews/2026-10-13-artcraft-vs-framework/a3-revision.md`). It is the diff form of the
ratchet; the measured counts are the second change, after R10.

## Proposed outcome
When this change is done, each of these is true and has a test:

- **A gate check `ratchets` runs at gates (c), (d) and (e)**, for every change type, from the
  committed diff `git diff --name-status -M <merge base>...HEAD` (rename detection named
  explicitly, so the rule does not depend on the git configuration of the machine).
- **A dropped test file is a finding.** A drop is a `D` under a `test_paths` glob, or an `R`
  whose source matches a glob and whose destination matches none. An `R` from one test path
  to another is a rename and not a drop. The finding names the files.
- **A dropped eval case is a finding.** The same rule over `evals/cases/`, with one addition:
  an `R` whose destination folder name starts with a dot is a drop. A case is dropped when
  nothing is left under its folder at HEAD.
- **A drop the approved plan declares is not a finding.** The plan is read at the merge base
  (`GateContext.approved_artifact`), never from the working tree or HEAD. A file drop is
  declared when the approved plan's "## Files that change" lists its path. A drop of a whole
  ratchet is declared by a fixed Proof item, `- ratchet: <name> may fall, because <why>`,
  which the `plan-template` skill gains. A declared drop is `ok` with its details, and the
  PR's plan-conformance line names it ("declared drops: tests/x.py (plan)").
- **An undeclared drop is recorded as a risk-list hit named after the ratchet**:
  `ratchet: tests` for test files, `ratchet: evals` for eval cases. It parks, as every failed
  deterministic check does, and never goes to the panel. The owner's `sdlc:accept-risk`
  accepts it with no new label: `plugin/state/unpark.py` `risk_hits` reads the ratchet hits
  beside the risk list's, `status.yaml: risk_accepted` holds the item for the rest of the
  change, the `ratchets` check passes an accepted item, and `owner_actions` judges the
  label's actor unchanged.
- **Added skip markers are listed, never parked on.** The check scans the added lines of
  files under `test_paths` and of the test runner's configuration files (`pytest.ini`,
  `pyproject.toml`'s pytest section, `setup.cfg`, `tox.ini`, `conftest.py`, `package.json`'s
  jest block, `jest.config.*`) for anchored per-language tokens (`@pytest.mark.skip`,
  `@pytest.mark.xfail`, `pytest.skip(`, `--deselect`, `--ignore`, `-k`, `testpaths`,
  `norecursedirs`, `collect_ignore`, `it.skip(`, `describe.skip(`, `xit(`, `.only(`,
  `test.todo(`, `#[ignore]`) and writes each hit, with its file and line, to the check's
  details.
- **The reviewers read the list.** `plugin/agents/adversarial-reviewer.md` gains one angle at
  (c) and (d): each added skip marker the gate listed, and the plan line that declares it or
  none. `template/REVIEW.md` gains the same line for the (e) pass. This repository's root
  `REVIEW.md` is the owner's: the build run proposes the line in the owner's table format and
  does not write it.
- **The finding says what it cannot see.** Its "what I need from you" names the files, says
  how to declare or accept the drop, and says that a file emptied of its tests or a
  configuration line is not caught until the measured ratchets (R15's second change).
- A plugin version bump, since `plugin/` and `template/` change.

## Affected users and systems
- The owner: a park when a run drops a test file or an eval case without the approved plan
  saying so, accepted with the label already used for the risk list; the drops the plan
  declares shown on the PR.
- Every project on the plugin: one more gate check at (c), (d) and (e), silent when nothing
  is dropped. No new key in `sdlc.yaml`; the existing `test_paths` globs are reused.
- `plugin/gate/checks.py` (the new check and `CHECKS_BY_PHASE`), `plugin/state/unpark.py`,
  `plugin/pr/description.py` (the plan-conformance line), `plugin/skills/plan-template/SKILL.md`,
  `plugin/agents/adversarial-reviewer.md`, `template/REVIEW.md`, `docs/OPERATING_MODEL.md`
  §3 and §6, and their tests.

## Constraints
- **No runner code.** Nothing in `plugin/ci/run_phase.py` or the workflow templates changes,
  so this change does not go on the port list and does not wait for R10 or the 1.0.0 read.
- Decisions kept, none amended: 24 is read (a ratchet finding is a risk-list hit, so
  `sdlc:accept-risk` accepts it), 2 (the gate reads the plan approved at gate (b)), 6, 11 and
  21 (a failed deterministic check parks and never goes to the panel). No new label.
- The gate judges committed work, never the working tree (OPERATING_MODEL §3).
- No guardrail file is edited in a run; the root `REVIEW.md` line is proposed to the owner.
- The test-file lock of a fix-type change, its hook and its red/green proof (T11) stay as
  they are; the new check also runs on fix-type changes, so it covers the commit before the
  lock.
- Compatibility: a change that drops nothing sees nothing new; a plan with prose-only Proof
  still passes.
- Python only, no third-party dependency, Windows and Linux; every piece has a test;
  `python -m compileall -q plugin tests tasks.py`, `python -m ruff check .` and
  `python -m pytest` green.

## Open questions
- How the finding becomes a risk-list hit: written into the `risk_list` check's
  `details.hits`, or read by `unpark.risk_hits` from the `ratchets` check's own details.
- The exact token list per language and how each token is anchored, so a test that mentions
  a token in a string (this repository's own runbook tests carry `--deselect` nine times)
  is listed at most, never parked on.
- Whether `evals/cases/` is a fixed path or read from the eval runner's own default.
- What a `- ratchet:` Proof item naming a ratchet that does not exist does: ignored with a
  note, or a finding at gate (b).
- The wording of the plan-conformance clause on the PR, and of the banner line once T9 is
  built.
