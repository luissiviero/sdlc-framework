# Progress — the framework's own checks, faster, part 2: the runner prepared before the suite (choice 235, item 6) (2026-10-19)

This session ran on branch `ccr-dc6617ae-y5l3n6`, from the owner's "Start the new PR for 6" of 2026-10-19, after #243 merged. The previous record (part 1: no real network in the tests, the Windows suite in three shards, choice 235, PR #243) is now `docs/progress/2026-10-19-framework-checks-faster-and-choice-235.md`, unchanged. The session's own file is `docs/handoffs/sessions/2026-10-19-ccr-dc6617ae-y5l3n6.md`, updated in this PR.

No change under `plugin/` or `template/`; no version bump. Not ROADMAP R53 (a project's phase jobs).

## Summary
- **Every test job of `Framework checks` prepares its runner** before it installs the dev tools: `.github/scripts/framework_checks_runner.py` sets `maintenance.auto false` and `gc.auto 0` in the runner's global git config, and on Windows turns Defender's real-time scan off (`Set-MpPreference -DisableRealtimeMonitoring $true`, read back with `Get-MpPreference`). The suite starts about 44,000 git processes; after a commit or a fetch git starts its automatic maintenance as one more, and on Windows Defender scans every process start and every file a test writes.
- **Speed only, never a red step.** The runner is thrown away after the job and runs only this repository's checks; no test reads either setting (a test that needs its own git config sets `GIT_CONFIG_GLOBAL`, and `plugin/evals/run.py` already turns the maintenance off in its fixture). A setting that cannot be applied is printed as "not applied" with the reason, and the job goes on.
- **Tests:** `tests/test_framework_checks_runner.py` (the plan per platform, the report, a refused or missing command keeps exit 0, a dry run changes nothing; the commands are recorded, never run). `tests/test_templates.py`: the prepare step is the first `run:` line of both test jobs.
- **Measured in a cloud session (Linux, 4 cores), the suite with an empty global git config against one with the two git settings:** 167 s and 183 s against 179 s and 180 s, no difference beyond the noise; on Linux the maintenance runs detached and does not hold a test up. It is not rare: `tests/test_fast_lane.py` alone started 4971 git processes, 482 of them `git maintenance` (strace, the same session, empty global config).
- **Measured on this PR's run** ([run 39304275334](https://github.com/luissiviero/sdlc-framework/actions/runs/39304275334), head `18ad150`, all green): every Windows shard logged "git maintenance.auto=false: applied", "git gc.auto=0: applied" and "Defender real-time scan off: applied (True)". The shards' test steps read "673 passed in 282.02s", "712 passed in 483.92s" and "709 passed in 464.07s", 1230 s in all against 1183 s on #243's first run; the run took about 9 minutes against about 10 and 11.5 on #243's two. No gain shows beyond the runners' own variance: what remains is the cost of starting git itself, which items 3 and 5 reduce.

## The owner's decisions (2026-10-19)
None new: item 6 of choice 235 (`docs/progress/2026-10-19-framework-checks-faster-and-choice-235.md`), started by the owner after #243 merged.

## Proposed edits for the owner
None: no guardrail line changes in this PR.

## Left
- **The second step of choice 235, after the live proof:** the fixture repositories built once per session, fewer repeated git lookups in `plugin/state/gitops.py` (a version bump), and a stand-in for the 25 requests from the subprocesses of one end-to-end test.
- **The Windows shards vary from run to run** (shard 3 took 6.1 minutes on #243's first run and 11.2 on its second, with the same tests); a split by time is not worth building while the runner's own variance is that large.

## Checks (this repository)
On the final head, after `python -m pip install -e ".[dev]"`, chained with `set -o pipefail`: the four commands of `HANDOFF.md`'s standing precondition 1. Their output is in the PR.
