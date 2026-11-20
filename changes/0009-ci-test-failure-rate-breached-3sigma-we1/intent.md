# Intent: Fail the evals job loudly when the runner cannot install the sandbox's tools
Author: sdlc-maintain diagnosis (automation). Change id: 0009. Entry route: incident 68b6897ece2328d6.

## Problem
The scheduled "Framework evals" run on 2026-11-19 failed every one of its 24 cases with zero
turns, and the CI test failure rate jumped from about 2% to 100% for that day (tier 3). No code
had changed. The same commit (4f7f597) passed on 2026-11-18 and again on 2026-11-20. The
runner setup step could not download `socat` from the Ubuntu mirror. Claude Code's sandbox
needs `socat`, and the evals run the sandbox with `failIfUnavailable: true`, so every `claude`
call exited 1 before its first turn.

The setup step (`plugin/ci/runner_setup.py`) always exits 0. It reported
`missing_packages_after: ["socat"]` and still let the job continue. The result was 24 eval
failures that read as a regression ("unparsable claude output (exit 1)"), not one clear
infrastructure failure. The breach filed a tier-3 incident and cost the owner a triage over a
mirror outage.

## Proposed outcome
- When a Linux runner still lacks `bubblewrap` or `socat` after the install attempt, the
  runner setup retries the install once (a transient mirror error recovers). If the tools are
  still missing, the job stops at that step with a message that names the missing package and
  the apt error, so the eval step never runs without a sandbox.
- The eval runner's failure reason for a `claude` exit that has no parsable output keeps the
  start of the error message, so a sandbox-unavailable failure says so in the report table.
- A runner-setup failure is not counted as a test failure by `ci_test_failure_rate`, or it is
  told apart from one. Which of the two is for design to settle (see Open questions).
- Tests cover the retry, the non-zero exit when tools are still missing, and the unchanged
  exit 0 on macOS and Windows.

## Affected users and systems
- The owner, who triages incidents and reads the evals report.
- `plugin/ci/runner_setup.py` and every workflow that runs it (Framework evals, and the phase
  workflows that use the CI sandbox settings).
- `plugin/evals/run.py`: how it reports a `claude` exit that has no parsable output.
- Possibly `plugin/detect/`: how the CI test failure rate counts a run that failed before its
  tests started.

## Constraints
- The sandbox stays mandatory: `failIfUnavailable: true` and `allowUnsandboxedCommands: false`
  do not change. An eval or phase job never runs unconfined.
- Python only, and it must work on Windows and Linux. On a platform where the sandbox does not
  apply, the setup still exits 0.
- No new network destinations beyond the Ubuntu mirrors apt already uses.
- Guardrail files (`sdlc.yaml`, `bands.yaml`, `.claude/**`) do not change.

## Open questions
- Should a run that fails at runner setup count toward `ci_test_failure_rate` at all, or be
  recorded as an infrastructure failure that the detection reports separately? Changing the
  metric's definition may need a bands change, and that is the owner's PR.
- The visible part of the `claude` error was cut to its tail, which mentions
  `projects["/tmp/sdlc-eval-.../project"].hasTrustDialogAccepted: true in /home/ru...`. The
  first thing to check is the full stderr of one case run without `socat`. It should confirm
  that the message is the sandbox-unavailable error and not a separate workspace-trust problem.
  The report artifact `framework-evals-report-44521976196` may hold more of it.
- Retry count and back-off for the apt install: one retry, or a short loop?

## Examples/References
- Failed run: https://github.com/luissiviero/sdlc-framework/actions/runs/44521976196
- Passing runs on the same commit: actions runs 44302898726 (2026-11-18) and 44734073099
  (2026-11-20).

## Evidence
- Anomaly: metric `ci_test_failure_rate`, tier 3 by rule `we1`. The latest value was 1.0 (1
  of 1 runs failed) on 2026-11-19, against a baseline mean of 0.0178 and sigma of 0.0409
  (24.04 sigma, 23 baseline points over 30 days). The breach started on 2026-11-19. Record:
  `evidence/detection.json`.
- Where it lives: `gh run view 44521976196 --log-failed`, job `evals`.
  - Step "Prepare the runner for Claude Code's sandbox" (12:14:24 to 12:17:33): `apt-get
    install -y socat` exited 100 with `E: Failed to fetch
    http://security.ubuntu.com/ubuntu/pool/main/s/socat/socat_1.8.1.1-1ubuntu0.1_amd64v3.deb
    Connection failed [IP: 91.189.91.83 80]`. The step reported
    `missing_packages_after: ["socat"]` and still exited 0. The AppArmor profile was written
    and loaded without error.
  - Step "Run the framework eval suite" (12:17:36 to 12:17:54): all 24 cases `FAIL` with
    0 turns, 0.0000 USD, and `unparsable claude output (exit 1)`, then
    `pass rate 0/24 = 0 (minimum 1)` and `Process completed with exit code 1`. Eighteen
    seconds for 24 cases means no case reached the model.
- Why every case failed: `plugin/evals/run.py` (`CI_EVAL_SETTINGS`) runs each case with
  `sandbox.failIfUnavailable: true`, and the sandbox on Linux needs `socat`
  (`plugin/ci/runner_setup.py`, `PACKAGES`). `runner_setup.main` always returns 0.
- Ruled out:
  - A code change. The breach window lists no commits, and the failed run checked out
    4f7f597, the same commit that passed on 2026-11-18 (run 44302898726) and on 2026-11-20
    (run 44734073099).
  - A flaky test. All 24 cases failed the same way before their first turn, so no single test
    is intermittent.
  - An authentication or credit problem. Cost and turns were zero, and the next day's run
    passed with the same secret.
  - The Claude Code version. It is pinned at 2.1.278 in all three runs.
- Lessons: `lessons/index.md` is current (`index.py check` exited 0). No lesson names
  `ci_test_failure_rate`, `we1`, or the runner setup. The index has no `## Retired` or
  `## Unsorted` section, so no lesson was relied on.
