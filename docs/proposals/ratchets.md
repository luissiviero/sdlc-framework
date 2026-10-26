---
type: Proposal
title: The bar is lowered only by the owner — a dropped test or eval case is a gate finding, the test and case counts are ratchets measured against the merge base, and the owner's existing label accepts a drop
description: A gate check `ratchets` judges, at gates (c), (d) and (e), every test file and eval case the branch drops (a delete, or a move out of the test paths) unless the approved plan declares it; later the runner's commands step measures named counts on a clean checkout of HEAD and on the merge base, and a fall is a red entry that starts decision 29's fix round; a drop the owner wants is accepted with sdlc:accept-risk, recorded as a risk-list hit named after the ratchet; added skip markers are listed for the reviewers and never park.
status: accepted
roadmap: R15 (accepted by the owner on 2026-10-13 with the twelve corrections D1 to D12 of docs/reviews/2026-10-13-artcraft-vs-framework/a3-revision.md as recommended; two changes, the diff form now and the measured ratchets after R10; each correction is marked beside the text it shapes)
sources:
  - id: artcraft-study
    resource: docs/reviews/2026-10-13-artcraft-vs-framework.md
    title: "Section 8.1 row A3 (ratchets instead of targets) and section 9 row G2 (nothing stops the bar from being lowered); evidence in study-a-governance.md §5 and study-c-evidence-measurement.md §5"
  - id: revision
    resource: docs/reviews/2026-10-13-artcraft-vs-framework/a3-revision.md
    title: "The eight-row breakdown of A3 checked against main fefd660 and the ArtCraft repositories, with an independent fresh-context review; twelve corrections D1 to D12, accepted by the owner as recommended on 2026-10-13 (PR #177)"
  - id: artcraft-sources
    resource: docs/reviews/2026-10-13-artcraft-vs-framework/study-a-governance.md
    title: "photocraft 99e1138 AGENTS.md:89 (raise FLOOR, never lower it), :100-102 (the agent raises a corpus floor), crates/ui-egui/src/parity.rs:9-10 and :90-93 (the floor asserted in a test), crates/io/tests/corpus.rs:35-36, :151-159, :435-436 (corpus floors), docs/development.md:312-314 and :328-341 (budgets as targets, the 15% regression threshold, nightly only); soundcraft c0cb993 AGENTS.md:54; filmcraft cee1feb docs/testing.md:9, :52-53"
  - id: study-entries
    resource: docs/reviews/2026-09-28-playbook-vs-framework/target-design.md
    title: "T9 (a risk-list hit becomes a banner line the merge accepts), T10 (the commands step and its rounds), T11 (the test lock of a fix), T13 (the eval suite grows), T14 (the runbook PRs), T30 (the cap and its one reset), T32 (the record answers who, when and why)"
  - id: playbook
    resource: docs/reference/ai-native-sdlc-playbook.pdf
    title: "p.28: the verification block ('never skip or delete a failing test'; 'If a test fails, fix the code, not the test') and step 7 ('an agent fixing code must not be able to weaken the check on that code', a hook, or 'check the diff in review and reject any change that touches a test'); p.35: hooks 'stop the agent editing test files during a fix task'"
  - id: decision-24
    resource: docs/decisions/24.md
    title: "Decision 24: the owner's un-park verbs are labels; sdlc:accept-risk accepts the risk-list hits the last gate reported (read, not amended)"
  - id: decision-29
    resource: docs/decisions/29.md
    title: "Decision 29: in CI a red target starts the next fix round by itself (read for the ratchets entry of the same step, not amended)"
  - id: code
    resource: plugin/gate/checks.py
    title: "check_test_lock :1268-1318, check_risk_list :732-780, check_owner_actions :1070-1240, check_plan_sync :601-648, GateContext.approved_artifact :124-130, CHECKS_BY_PHASE :1694-1767; plugin/gate/diff.py committed_files :246-256; plugin/gate/gate.py run_deferred_commands :378-464; plugin/state/unpark.py :68-84, :115-124; plugin/ci/run_phase.py :1310-1331; plugin/evals/run.py :142-151; plugin/detect/runbooks.py :639-700; read at main fefd660, plugin 0.3.7"
generated: { by: sdlc-framework-session/ccr-c6d8a9c3-3s7q61, at: 2026-10-13T21:30:00Z }
---

# The bar is lowered only by the owner: dropped tests and eval cases are findings, and the counts are ratchets
**Names since R45** (decision 39; the renames built in plugin 1.0.43 to 1.0.47; added on 2026-10-26, the text below keeps the old names, choice 126): `(a)` -> intent; `(b)` -> design; `(c)` -> build; `(d)` -> test; `(e)` -> deploy; `(f)` -> maintain; `incident` -> `sdlc:triage` (the label). \
**Status: proposed from the ArtCraft-versus-framework study of 2026-10-13 (row A3), checked against the code before it was written, and accepted the same day.** Nothing is built. *[2026-10-20: change 1 built as change 0005, PR #211, `v1.0.2` (2026-10-17); change 2 waits at rank 32; the rank is read from ROADMAP's Order column]* *[2026-10-13: accepted by the owner as ROADMAP **R15**, with the revision's twelve corrections (`docs/reviews/2026-10-13-artcraft-vs-framework/a3-revision.md`, section 9, D1 to D12) accepted as recommended. No proposal existed before the revision, so the corrections are the text below rather than notes on an earlier text; each paragraph a correction shapes carries its number, so the record of what changed is kept (choice 126). The first change's intent waits for PR #173 (R14's intent, change 0004), whose id the allocator would otherwise give again.]* *[2026-10-13, later: the allocator's `new-change` also counts remote `sdlc/<id>/*` branches (`plugin/state/cli.py:52`, `gitops.remote_change_ids`), so it gave 0005, not 0004; on the owner's word change 1's intent was drafted as change **0005** on `sdlc/0005/a`, PR #180 (draft, `sdlc:a-ready`).]*

## The problem

The playbook names one failure above all others in the test loop: the agent lowering the bar to pass it. The framework guards against it deterministically in one case only.

- **Outside a fix-type change, nothing deterministic judges the tests.** `check_test_lock` returns `ok` for every change that is not a fix (`plugin/gate/checks.py:1282-1283`). For the rest the rule is prose: "Never weaken, skip or delete a test to get green" (`plugin/commands/sdlc-test.md:171`), "a test may change only when `plan.md` Proof says so" (`:69-71`), the adversarial reviewer's angle 6 (`plugin/agents/adversarial-reviewer.md:51-52`), and `REVIEW.md:23-24`, which covers fix-type changes only. A feature change that deletes a failing test passes every gate if the rest is green.
- **Eval cases are unprotected.** A case is a folder under `evals/cases/` (`plugin/evals/run.py:142-151`); it is under neither `test_paths` nor `protected_paths` (`template/sdlc.yaml:133-141`), and the evals workflow passes with fewer cases. Moving a case to a name that starts with a dot hides it from `discover` with no deletion in the diff.
- **A bar is a count, and nothing counts.** Removing tests from a kept file, a `--ignore`, `-k` or `testpaths` line in the test runner's configuration, a `conftest.py` collection hook or an early `return` lower the bar with no file deleted and no marker added. Only a measured number catches them all.

ArtCraft keeps its floors in tests: photocraft's `FLOOR` is a constant that `parity_does_not_regress` asserts (`crates/ui-egui/src/parity.rs:9-10`, `:90-93`), the corpus floors are constants the corpus tests assert (`crates/io/tests/corpus.rs:151-159`, `:435-436`), and the rule is "raise `FLOOR` … (never lower it)" (`AGENTS.md:89`). Two things matter for the transfer. The agent itself raises the floor in the PR that improves the number (`AGENTS.md:100-102`), so the ratchet rises with no human act. And nothing compares a floor with the previous commit's: a lowering is a visible diff that only the rule and a human merge stop[^artcraft]. The framework can do better than ArtCraft on the second point and must not do worse on the first.

## What the article says

The verification block in CLAUDE.md: "never skip or delete a failing test", and "If a test fails, fix the code, not the test" (p.28). Step 7 of the loop: "an agent fixing code must not be able to weaken the check on that code"; a hook that blocks test edits during a fix task does it, and "the alternative is to check the diff in review and reject any change that touches a test" (p.28). Hooks "stop the agent editing test files during a fix task" (p.35)[^playbook]. The framework built the hook for fixes (build guide step 25) and the review for fixes (`REVIEW.md:23-24`); this proposal makes the article's review alternative a deterministic check for every change type, and adds the count ArtCraft keeps in a test. *[D11: the article's own examples are the fix task; extending them to every change type is this proposal's step, not the article's.]*

## What the framework does today

Read at `main` fefd660, plugin 0.3.7; `main` 0ad9215 differs in documentation only[^code].

- **The test-file lock**, fix-type changes only: the hook denies edits under `test_paths` once the reproducing test is committed and the lock set (`plugin/hooks/test_file_lock.py`), the shell guard denies `rm`, `git rm` and `git mv` of a locked test (`plugin/hooks/shell_guard.py`), and `check_test_lock` fails any test file added, changed, renamed or deleted between the lock commit and HEAD (`checks.py:1293-1318`). The reproducing test's own commit precedes the lock (T11), so a deletion riding in it is not judged.
- **The risk-list path**: `check_risk_list` reports hits in `details.hits` of the gate record; the owner's `sdlc:accept-risk` starts a fix round that records the reported hits in `status.yaml: risk_accepted` with the label's actor (`plugin/state/unpark.py:68-84`, `:115-124`; `plugin/state/status.py:223-235`); `owner_actions` judges that actor (`checks.py:1070-1240`). The label accepts nothing else: with no recorded risk-list hit it is rejected as "nothing to accept".
- **The runner's commands step** runs build, test and lint after the session, outside the sandbox, in gate code (`gate.py` `run_deferred_commands`, `checks.py` `run_targets` and `judge_targets`); `run_phase.py` holds its timeout (`3 * per_command`, `:1317`) and the call (`:1320-1331`). It runs on the working tree the session left, and nothing compares that tree with HEAD before it runs (`gate.py:383`; `run_phase.py:1283`); `clean_tree` ran inside the session, before it.
- **The quarantine runbook** adds `--deselect <node id>` to pytest's configuration on its own branch and opens a PR labelled `incident`; no gate and no review pass runs on it, and the owner's merge applies it (`plugin/detect/runbooks.py:639-700`; T14 "Today").
- **T9's banner** ("Needs your close look") does not exist in the code: `plugin/pr/description.py` has "What needs you" lines only. T9 is confirmed and has no proposal or R number.

## The proposal

Two changes. The first needs no runner code and no R10; the second measures, and its round needs R10. *[D12]*

### Change 1, now: a dropped test or eval case is a finding

1. **A gate check `ratchets`, in its diff form, at gates (c), (d) and (e).** It reads `git diff --name-status -M <merge base>...HEAD` (rename detection named explicitly, so the rule does not depend on the runner's git configuration). A **drop** is a `D` under a `test_paths` glob, or an `R` whose source matches a glob and whose destination matches none; an `R` from one test path to another is a rename and not a drop. The same rule runs over `evals/cases/` with one addition: an `R` whose destination folder name starts with a dot is a drop, since `discover` skips hidden folders; a case is dropped when nothing is left under its folder at HEAD. The finding names the dropped files and cases. Gates (a), (b) and (f) need nothing: `design_scope` already parks any committed file outside the change folder there, deletions included. *[D7, D8]*
2. **A drop the approved plan declares is not a finding.** The plan is read at the merge base (`GateContext.approved_artifact`), never from the working tree or HEAD, because the build session edits `plan.md` in (c) by design. A file drop is declared when the approved plan's "## Files that change" lists its path; a drop of a whole ratchet, by files or (in change 2) by count, is declared by a fixed Proof item, `- ratchet: <name> may fall, because <why>`, which the plan template gains beside A1's `test`, `screenshot` and `state` items. A declared drop is `ok` with details: it shows on the PR's plan-conformance line now, and as a banner line once T9 is built. A drop the owner wants that the approved plan does not declare is accepted by the act below, since a plan amended after the (b) merge is not the approved copy. *[D5]*
3. **An undeclared drop is recorded as a risk-list hit named after the ratchet**: `ratchet: tests` for the test files, `ratchet: evals` for the cases. It parks, as every failed deterministic check does (decision 11; never a panel item, decision 21). The owner's `sdlc:accept-risk` accepts it with no new label: `unpark.risk_hits` and `check_risk_list` learn to read the `ratchets` check's hits beside the risk list's, `status.yaml: risk_accepted` holds the item for the rest of the change, and `owner_actions` judges the label's actor unchanged. When T9 is built, the hit becomes a banner line the owner's merge accepts, as every risk-list hit does. *[D4]*
4. **Added skip markers are a list, never a park.** The check scans the added lines of files under `test_paths` and of the test runner's configuration files (`pytest.ini`, `pyproject.toml`'s `[tool.pytest.ini_options]`, `setup.cfg`, `tox.ini`, `conftest.py`; `package.json`'s `jest` block and `jest.config.*`), matching anchored per-language tokens (`@pytest.mark.skip`, `@pytest.mark.xfail`, `pytest.skip(`, `--deselect`, `--ignore`, `-k`, `testpaths`, `norecursedirs`, `collect_ignore`, `it.skip(`, `describe.skip(`, `xit(`, `.only(`, `test.todo(`, `#[ignore]`), and writes each hit with its file and line to the check's details. The adversarial reviewer's card at (c) and (d) gains one angle, "each added skip marker the gate listed, and the plan line that declares it or none"; the REVIEW.md pass at (e) reads the same list. A marker list parks nothing because it fires on legitimate code (this repository's own tests of the quarantine runbook carry `--deselect` on nine lines; platform skips use `pytest.skip(`; filmcraft keeps perf tests `#[ignore]` by design) and is easy to step around; the count in change 2 is the park. *[D6]*
5. **Under `plugin/`, so a version bump with tests.** The REVIEW.md pass's angle is a line in `template/REVIEW.md` (project content the template ships); this repository's own root `REVIEW.md` is a guardrail file the owner edits, and the build run proposes that line in the owner's table format instead of writing it.

What change 1 does not catch, and says so in its finding's "what I need from you": a file emptied of its tests, a configuration line, a collection hook. Those wait for change 2.

### Change 2, after R10: the counts are ratchets

6. **`sdlc.yaml: ratchets: [{name, command}]`.** Each command prints a number; the step reads the first number on its last non-empty line, so pytest's own `N tests collected in 0.55s` works unchanged. The gate counts `evals` itself (the case folders `discover` would run), with no command. `/sdlc-init` proposes `tests` per detected language: for Python `python -m pytest --collect-only -q -o addopts=` (the `-o addopts=` clears a project's own `-q`, which silences the count, as this repository's `pyproject.toml:31` does); for Node and the rest, an empty list with a comment naming the slot, the command left to the owner. *[D1]*
7. **The floor is the merge base's own value.** The step measures each ratchet on HEAD and on the merge base, once per merge base (a temporary worktree), and keeps the base value in the gate record for the later gates; gate (b)'s run of the targets on the base is a free source of it while the merge base is the (b) merge commit. A value below the base's is a fall. A rise needs no act, so the ratchet climbs with every merge, as ArtCraft's does, with no run and no owner editing a number. An optional `min` is a hard floor beneath the base value, never above it, so it can never make every change red. *[D2]*
8. **A clean checkout of HEAD.** The step measures the tree that merges: a clean worktree at HEAD, or a refusal (a park, with the files named) when the session's working tree differs from HEAD outside the change folder's evidence. Today's three targets run on the working tree the session left; whether this change closes that for them too, in the same step, or a separate fix does it sooner, is to settle (below). *[D2; a3-revision.md section 7]*
9. **A fall is a red `ratchets` entry of the commands step, judged beside `commands`, at (c), (d) and (e).** In CI, once R10 is built, it starts decision 29's fix round, with the step's log as the round's constraint; the change parks only at the iteration cap, after T30's one reset. At that park the entry's finding is recorded as a risk-list hit named after the ratchet (item 3), so the owner can accept a drop by the label, because no act clears a red target and the next round would be red again. Before R10 it parks at once, as every red target does. Decision 29 is read for one more entry of the step it governs, not amended. *[D3]* *[2026-10-20, choice 242: once R24 retires `sdlc:accept-risk`, the fall recorded at the cap is a banner line the owner's (e) merge accepts; this point and decision 29's cap park are amended by a decision file written with the second change's design (decision 35)]*
10. **One line in `run_phase.py`.** `commands_timeout_seconds` counts the ratchet commands beside the three targets; that line puts the change on the port list, which records it until the 1.0.0 read. By hand, `evidence/collect.py` and the gate's own `run_commands_check` run the ratchets as they run the targets. *[D9]*
11. **The diff form stays as the explanation.** Change 1's file and case drops become the detail of a count's finding ("tests fell from 1618 to 1612: tests/test_x.py dropped, 4 skip markers added"), and still park on their own when a project declares no `tests` ratchet.

## How it is judged

On the sample repository and the next project: a change that deletes a failing test or an eval case without declaring it parks at its next gate with the files named, and the owner's `sdlc:accept-risk` lets it continue with the actor recorded; a refactor whose approved plan lists the moved tests passes with the drop on the plan-conformance line; after change 2, a change whose suite shrinks by any means is red in the runner's step and starts a round. The failure is a merged change whose test or case count is lower than its merge base's with no declaration and no recorded acceptance.

## What to settle before building

| Question | Recommended |
|---|---|
| Which count `tests` measures by default | `tests collected`: it falls on a deleted, deselected or ignored test, takes about a second, and runs no test; `passed` also falls on a skip marker, but needs a whole run and changes with flaky tests. The skip markers are covered by item 4's list |
| The Node command | None proposed by `/sdlc-init` until a project needs one; jest's `--listTests` counts files, not tests |
| Where the base value is measured | A worktree at the merge base, once, kept in the gate record; gate (b)'s base run as the free source while the merge base is the (b) merge commit |
| The clean-checkout rule (item 8) | In change 2, for the targets and the ratchets together, since both are the same step; if the owner wants it sooner, a separate 0.3.x fix of the step, which then goes on the port list |
| The skip-marker token list | The list in item 4, anchored per language, in the plugin; no `sdlc.yaml` extension until a project needs one (D6) |
| Where a declared drop shows before T9 | The plan-conformance line of the PR's five bullets, one clause: "declared drops: tests/x.py (plan)" |

## Considered and not chosen

- **The floor as `min` in `sdlc.yaml`.** A run may never edit `sdlc.yaml`, so the floor would rise only by the owner's hand, and one set above the code's value makes every change red: a target, not a ratchet (D2).
- **A floor file the runner's step raises** when the number rises (ArtCraft's model, with the write moved from the agent to the runner). It goes stale on every merge that skips the step, a quarantine PR or the owner's own PR, and then shows a false drop or a lowered floor; the merge base's measured value has no such gap (D2).
- **Skip markers as a park.** False findings on legitimate code, and easy to step around; a list for the reviewers instead (D6).
- **A label of its own** (`sdlc:accept-drop`): it would amend decision 24, and T9 wants one label fewer; the risk-list path carries the act (D4).
- **The checks at gates (b) and (f)**: `design_scope` already parks there, and a ratchet at (b) would measure the base (D7).
- **Reading the count from `evidence/test.log`'s summary line**: a project's own `-q` silences it; the ratchet is a command with its own options (a3-revision.md section 7).
- **A gate on performance budgets.** ArtCraft's perf run "never runs on pull requests" and its budgets are targets with `enforce = false`; only the regression threshold is a ratchet, and a project can declare one as a `ratchets` command (D11).

## Decisions it touches

None is amended. *[D10]*

- **24** is read: a ratchet finding is recorded as a risk-list hit, so "accepts the risk-list hits the last gate reported" covers it with no new label.
- **29** is read: the `ratchets` entry is judged in the commands step, so a fall is a red entry that starts its round.
- **2** is kept: the approved plan, written read-only at (b), declares a drop, and the gate reads that copy.
- **6** is kept: `sdlc.yaml` stays the owner's, and the design needs no new guarded file. Decision 6 names `.claude/**`, `CLAUDE.md`, `REVIEW.md` and the hook scripts; `sdlc.yaml` is a guardrail by `ALWAYS_PROTECTED` and OPERATING_MODEL §8.
- **11** and **21** are kept: a failed deterministic check parks, and never goes to the panel.

## Order

Change 1 can be built now: it needs no runner code and does not wait for R10, and a finding parks as every gate failure does today. *[2026-10-20: change 1 built as change 0005, PR #211, `v1.0.2` (2026-10-17); change 2 waits at rank 32; the rank is read from ROADMAP's Order column]* Change 2 comes **after R10**, so a fall starts decision 29's round instead of parking; one timeout line in `run_phase.py` puts it on the port list, which records it and does not bar it. "After the 1.0.0 read because `run_phase.py` is on the port list" does not hold (a3-revision.md row 4). Where change 1 sits among R7 to R14 is the owner's call. *[D9, D12]*

## What changes in the playbook study's record

The entries this proposal extends are annotated, never rewritten (choice 126): one dated line beside the status of T9 (the ratchet hit is a risk-list hit, accepted by the label today and by the banner later), T10 (the commands step gains the ratchets under decision 29's rule), T11 (the protection of tests reaches every change type), T13 (the suite cannot shrink unseen) and T32 (the base and head values, the declared drops and the acceptance's actor are in the record). T14 and T30 are touched without being extended: the quarantine's `--deselect` is merged on the default branch and so lies inside every later merge base (exempt by construction), and the automatic rounds count against T30's cap as decision 29 has them. The crosswalk and its HTML snapshots are not changed, as the owner asked.

[^artcraft]: `docs/reviews/2026-10-13-artcraft-vs-framework/a3-revision.md` section 3; photocraft at `99e1138`: `AGENTS.md:89`, `:100-102`; `crates/ui-egui/src/parity.rs:9-10`, `:90-93`; `crates/io/tests/corpus.rs:35-36`, `:151-159`, `:435-436`; `.github/workflows/ci.yml:154-165`; `docs/development.md:312-314`, `:328-341`; `.github/workflows/perf-nightly.yml:3-7`. soundcraft `c0cb993` `AGENTS.md:54`.
[^playbook]: `docs/reference/ai-native-sdlc-playbook.pdf` p.28 (the verification block and step 7) and p.35, read in `docs/reference/ai-native-sdlc-playbook.txt` lines 1311-1323 and 1664-1666.
[^code]: `plugin/gate/checks.py:124-130`, `:601-648`, `:732-780`, `:1070-1240`, `:1268-1318`, `:1694-1767`; `plugin/gate/diff.py:246-256`; `plugin/gate/gate.py:378-464`; `plugin/state/unpark.py:68-84`, `:115-124`; `plugin/state/status.py:223-235`; `plugin/ci/run_phase.py:1283`, `:1310-1331`; `plugin/evals/run.py:142-151`; `plugin/detect/runbooks.py:639-700`; `plugin/commands/sdlc-test.md:69-71`, `:171`; `plugin/agents/adversarial-reviewer.md:51-52`; `REVIEW.md:23-24`; `template/sdlc.yaml:133-141`; `pyproject.toml:31`.
