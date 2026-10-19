# Progress — the framework's own checks, faster: no real network in the tests, the Windows suite in three shards, and the owner's choice 235 (2026-10-19)

This session ran on branch `ccr-dc6617ae-y5l3n6`, from the owner's question of 2026-10-19: why `Framework checks` takes so much longer now, and what makes it faster without giving up safety. The previous record (the speed-first order, choices 233 and 234, PR #240) is now `docs/progress/2026-10-19-speed-first-order-and-choices-233-234.md`, unchanged. The session's own file is `docs/handoffs/sessions/2026-10-19-ccr-dc6617ae-y5l3n6.md`.

This is this repository's own CI, not ROADMAP R53: R53 is about the setup time of a project's phase jobs, and nothing here touches `plugin/` or `template/`, so there is no version bump.

## Why the checks got slower
- **The Windows job is the whole wait.** Its "Lint and test" step went from 10.3 minutes for 1694 tests on 2026-10-17 ([run 39052509110](https://github.com/luissiviero/sdlc-framework/actions/runs/39052509110), "1694 passed in 616.22s") to 22.1 minutes for 2086 tests on 2026-10-19 ([run 39279514134](https://github.com/luissiviero/sdlc-framework/actions/runs/39279514134), "2086 passed in 1323.83s"). The Linux jobs stayed at 2 to 3.5 minutes. The 45 to 49 minutes the Actions list shows for some runs come from the run record being updated later; every job of those runs ended within about 23 minutes.
- **The new tests are end-to-end tests that start many processes.** From `cd8baf7` to `209325f`, `test_fast_lane.py`, `test_fix_round_edges.py`, `test_auto_round.py`, `test_fix_round_gaps.py`, `test_owner_rounds.py` and `test_panel.py` added about 190 seconds of test time on Linux (re-measured, junit timings of both commits in a cloud session, 836 s against 1025 s). The suite starts about 47,700 processes, 44,000 of them `git` (13,600 `rev-parse`, 975 `init`), measured with a logging `sitecustomize` in the same session. Windows pays for each process several times over, so the same tests doubled the Windows step.
- **40 tests reached the real api.github.com.** They sent 673 requests to `repos/owner/name` with a fake token, 17 label creations per `run_phase` run among them, because `full_run` in `tests/test_ci.py` hands the runner `GITHUB_TOKEN=FAKE_TOKEN` and nothing stubbed `ensure_labels`. Each request took about 0.3 seconds and came back 401: about 218 seconds of the 1025, measured the same way.
- **The end of the Windows run waited on one worker.** The last 4 % of its tests took about three minutes (15:58:18 to 16:01:12 in the run above), the end of pytest-xdist's default `load` scheduling.

## Summary
- **No real network in the tests.** An autouse fixture in `tests/conftest.py` answers every request to a host other than loopback with the same 401 "Bad credentials" the runner got, at once and in-process, so every test reads the answer it read before. A token a developer exported (`GH_TOKEN`) no longer leaves the machine. A test that needs another answer patches `_request` or `urlopen` itself, as before. One test of `tests/test_ci_end_to_end.py` still sends 25 requests from its subprocesses, which the fixture cannot reach.
- **The Windows suite runs in three shards** on parallel runners (`check-windows-shard` in `framework-checks.yml`). `FRAMEWORK_TEST_SHARD=i/3` keeps the tests whose id hashes (crc32) to shard i, so every test still runs on Windows exactly once; a malformed value stops the run. The check `check (windows-latest, 3.12)` keeps its name and is now the shards' verdict, green only when every shard is, skipped on a documentation-only pull request as before.
- **`--dist worksteal`** in `python tasks.py test` (pytest-xdist 3.2 or later, pyproject's dev extra): an idle worker takes queued tests over.
- **Tests:** `test_a_test_reaches_no_host_but_loopback` and `test_the_shards_split_the_suite_with_nothing_lost` (`tests/test_scaffold.py`), `test_the_windows_suite_runs_in_shards_and_its_check_is_their_verdict` (`tests/test_templates.py`). Two existing workflow tests in `tests/test_templates.py` follow the new job layout.
- **Measured in a cloud session (Linux, 4 cores):** total test time 1025 s to 856 s; one test of `tests/test_ci.py` from 6.1 s to 0.4 s; wall time 270 s to 249 s, since the cores were already busy. The three shards hold 672, 711 and 707 of the 2090 tests, with none lost or repeated (`--collect-only` per shard). `worksteal` made no difference locally (250 s against 249 s); its target is the Windows run's end. The Windows figure is this PR's own run.

## The owner's decisions (2026-10-19)
235. **The framework's own checks are made faster in two steps** (the session's recommendation; the owner, "Go ahead"): now, the network fixture, the Windows shards and `worksteal` (this PR), in parallel with the live proof since none of them touches `plugin/` or `template/`; after the live proof, building the fixture repositories once per session, fewer repeated git lookups in `plugin/state/gitops.py` (a plugin change, with a version bump), and the runner settings (Defender's real-time scan, git's automatic maintenance). Dropping the Windows job from pull requests was not proposed: it caught the Windows-only `PermissionError` of PR #241 on 2026-10-19.

## Proposed edits for the owner
None: no guardrail line changes in this PR.

## Left
- **The second step of choice 235**, after the live proof: the fixture repositories built once, the git lookups in `gitops.py`, the runner settings. Estimated, not measured: the Windows shards from about 7 minutes to about 4 or 5.
- **The 25 requests from the subprocesses** of `test_the_commands_step_runs_the_targets_without_the_job_s_credentials`: they need an environment-level stand-in, left for the second step.
- **The Windows time after this PR** is read from this PR's run, not verified yet.

## Checks (this repository)
On the final head, after `python -m pip install -e ".[dev]"`, chained with `set -o pipefail`: the four commands of `HANDOFF.md`'s standing precondition 1. Their output is in the PR.
