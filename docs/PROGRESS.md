# Progress — the framework's own checks, faster, part 3: the fixture repositories built once per session (choice 235, item 3) (2026-10-19)

This session ran on branch `ccr-eb707371-rh6z2g`, from the owner's task of 2026-10-19: the second step of choice 235, in two PRs (this one first, the git lookups of `plugin/state/gitops.py` second). The previous record (the LLM wiki pattern, ROADMAP R55 to R57 and choice 236, PR #247, from the parallel session `claude/llm-wiki-sdlc-framework-g10zr0`, which merged first) is now `docs/progress/2026-10-19-llm-wiki-roadmap-r55-r57-and-choice-236.md`, unchanged; the one before it (part 2 of choice 235, item 6) was archived by #247 as `docs/progress/2026-10-19-framework-checks-faster-part-2-runner-prepared.md`. The session's own file is `docs/handoffs/sessions/2026-10-19-ccr-eb707371-rh6z2g.md`, written in its last PR.

Tests only: no change under `plugin/` or `template/`, no version bump, not on the port list.

## Summary
- **`tests/fixture_repos.py`:** `copy(name, tmp_path, build, relocate)` runs `build` once per test session in a directory of its own (`tmp_path_factory`, so each xdist worker builds its own), then copies the result into each test's `tmp_path` with `shutil.copytree`. Every test still gets its own repositories; nothing is linked, shared or handed to a test twice.
- **Converted:** `project` of `tests/test_ci.py` (also used by `test_auto_round.py`, `test_fast_lane.py`, `test_fix_round_edges.py`, `test_fix_round_gaps.py` and `test_owner_rounds.py`); `_initialised_fixture`, `project` and `design_project` of `tests/test_gate.py` (also used by `test_panel.py` and `test_evidence.py`); `lane` of `tests/test_fast_lane.py`; `checkout` of `tests/test_ci_end_to_end.py`; `project` of `tests/test_detect_cli.py`; and the same builders in `tests/test_pr.py`, `tests/test_review.py` (one template per change type) and `tests/test_scan.py`. Each builder's steps are the fixture's old steps, unchanged; no assertion of any test changed.
- **What a copy must not inherit:**
  - The template's path: a remote added by path is pointed at the copy's own bare repository by `relocate` (`git remote set-url`, or `git config remote.origin.pushurl` for the end-to-end checkout), `FETCH_HEAD` is rewritten, and the first copy of each template is scanned: a template path left anywhere stops the session.
  - The requesting test's environment: a build runs under the environment the session started with, cleaned as `conftest.py` cleans each test's, with its own hook log.
  - The clock: `start_run` (a run's `started_at`, which the wall-clock limit reads) stays in the `project` and `design_project` fixtures of `test_gate.py`, after the copy.
- **Tests:** `test_a_fixture_repository_is_built_once_and_every_copy_is_its_own` (one build, under the session's environment; a commit pushed from one copy reaches neither the other copy nor the template) and `test_a_fixture_repository_copy_that_still_names_its_template_is_refused` (`tests/test_scaffold.py`).
- **Measured in a cloud session (Linux, 4 cores), with the same method as #243:** a `sitecustomize` on `PYTHONPATH` that logs every `subprocess.Popen`, `GIT_CONFIG_GLOBAL` an empty file, `GH_TOKEN` and `GITHUB_TOKEN` unset, `python -m pytest -n auto --dist worksteal`. The suite started 47,702 processes, 44,060 of them git, on `main` (`7626c92`), and 36,930, 34,286 of them git, on this branch: `init` 979 to 278, `commit` 1,996 to 835, `add` 1,850 to 688, `rev-parse --is-inside-work-tree` 5,151 to 3,616. Without the logger, alternating runs of `main` and this branch: total test time 741 s and 758 s against 575 s and 566 s (about 24 % less), wall time 201 s and 200 s against 170 s and 167 s; 2094 tests passed on `main`, 2096 on this branch (the two above).
- **What is left of the 34,286 git processes** is mostly the plugin's own git work during the tests; the next PR (item 5) takes the repeated `is_repo` and default-branch lookups.

## The owner's decisions (2026-10-19)
None new: item 3 of choice 235 (`docs/progress/2026-10-19-framework-checks-faster-and-choice-235.md`), started by the owner's task of 2026-10-19.

## Proposed edits for the owner
None: no guardrail line changes in this PR.

## Left
- **Item 5 of choice 235:** fewer repeated git lookups in `plugin/state/gitops.py`, as plugin 1.0.13 (this session's next PR). The sample's pin stays at 1.0.12 until change 0016 (session `ccr-6280ef4b-qilh53`) is finished and `v1.0.13` is tagged; that edit is the owner's.
- **The 25 requests from the subprocesses** of `test_the_commands_step_runs_the_targets_without_the_job_s_credentials`: carried from part 1, not taken here.
- **Builders not converted:** `make_repo` of `tests/test_detect_runbooks.py` (its files differ per test), the per-test `git init` of `tests/test_release.py`, `tests/test_hooks.py`, `tests/test_checkout_check.py` and `tests/test_state.py`; together about 280 `init` calls are left.
- **The Windows shards** are read from this PR's run below, as a hint and not a verdict: the same shard has varied by five minutes between runs.

## Checks (this repository)
On the final head, after `python -m pip install -e ".[dev]"`, chained with `set -o pipefail`: the four commands of `HANDOFF.md`'s standing precondition 1. Their output is in the PR.
