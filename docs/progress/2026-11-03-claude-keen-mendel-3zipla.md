# Progress — the gap of 27 and 28 October, and `HEAD_REF` kept out of the suite (2026-11-03, no plugin change)

This session ran on branch `claude/keen-mendel-3zipla`, from `main` at `51cea68` (#398, plugin 1.0.50). The owner asked where the project stood, then for the trial's edit table, then for this PR. No numbered choice, note or decision is taken in this PR, and nothing under `plugin/` or `template/` changes, so there is no version bump (choice 270).

## What was built
1. **`HEAD_REF` joins `RUNNER_NAMES`** (`tests/conftest.py`). The autouse fixture `_hook_log_in_tmp` removes every name in that tuple before each test, so a test that builds its environment from `os.environ` no longer reads the phase job's head branch. The two helpers that do so are `tests/test_fix_round_gaps.py:306`, `_owner_round`, and `tests/test_auto_round.py:343`, which builds its own environment. The owner pointed out that removing the variable in the first helper alone would leave `test_an_automatic_round_cancelled_with_nothing_to_keep_parks_as_decision_29_does` failing through the second. A test that sets `HEAD_REF` itself (`tests/test_cancelled_park.py:252`) sets it after the fixture ran, so it keeps its value.
2. **The session file** `docs/handoffs/sessions/2026-11-03-claude-keen-mendel-3zipla.md`, which records 27 and 28 October and why no file did.

## How the cause was found
Change 0006's design run (#403) parked on `commands: not green: test (exit 1)`, with ten failures, all in `tests/test_cancelled_park.py`. The assertions showed the fixture's park reason replaced by the job's own. Locally, the file passed under `GITHUB_ACTIONS`, `GITHUB_EVENT_NAME`, `GITHUB_OUTPUT`, `RUNNER_NAME` and `SDLC_TRIGGER`, which the conftest already removes or which do not matter. Under `HEAD_REF=sdlc/0006/design` it failed the same ten tests. `run_phase.cancel_state_refusal` (`plugin/ci/run_phase.py:3024`) reads `HEAD_REF` for a fix round, and the phase workflows set it in the phase step's environment (`.github/workflows/sdlc-design.yml`). The code is right, and a test fixture leaked the job's environment into the test.

## Verification
Before the fix:
```
$ HEAD_REF=sdlc/0006/design python -m pytest tests/test_cancelled_park.py -q -p no:cacheprovider
FAILED tests/test_cancelled_park.py::test_a_fix_round_cancelled_at_its_timeout_keeps_its_work_and_parks
FAILED tests/test_cancelled_park.py::test_a_cancel_by_hand_says_so - Assertio...
FAILED tests/test_cancelled_park.py::test_a_cancel_the_runner_cannot_place_says_both
FAILED tests/test_cancelled_park.py::test_a_cancelled_session_that_wrote_a_runner_file_parks_on_it_and_keeps_no_work
FAILED tests/test_cancelled_park.py::test_a_park_the_run_wrote_before_the_cancel_is_published_again_not_replaced
FAILED tests/test_cancelled_park.py::test_at_session_a_park_the_session_wrote_is_replaced_by_the_cancel_s
FAILED tests/test_cancelled_park.py::test_a_fix_round_cancelled_after_its_checks_keeps_nothing_uncommitted
FAILED tests/test_cancelled_park.py::test_a_run_that_updated_its_pr_parks_nothing
FAILED tests/test_cancelled_park.py::test_a_kill_after_the_result_was_stored_does_not_flag_the_runner_s_own_file
FAILED tests/test_cancelled_park.py::test_an_automatic_round_cancelled_with_nothing_to_keep_parks_as_decision_29_does
```
After it, 22 dots without and with the variable, and the whole suite green with it (exit 0). `python tasks.py verify` is in the PR body.

## The trial: the owner's edit table for change 0001 (trial #6)
The deploy gate parked trial #6 on two Important findings that only the owner can fix: `.github/workflows/ci.yml` (a run may not edit `.github/`) and `CLAUDE.md` (a guardrail). This session gave the owner the rows below and a PowerShell paste. It checked them in a fresh clone of the trial's `main` (`cc9ff5a`): each old text matched once, `git diff --stat` showed `2 files changed, 21 insertions(+), 8 deletions(-)`, and `main` stayed green (`1 passed`). Merged into `sdlc/0001/build`, the build diff touched no guardrail file and the suite gave `69 passed` with `polars==2.1.0`. The PowerShell itself was not run here.

| Link | Row | What is there | What it must become |
|---|---|---|---|
| trial `.github/workflows/ci.yml` | 24 | `pip install pytest==9.1.1 ruff==0.16.9` | the same plus `polars==2.1.0`, the version the build tested with (the change's `plan.md`, Risks) |
| trial `CLAUDE.md` | 4–5 | "Today it is a package skeleton (`app/`) and a smoke test (`tests/`)." | the package holds `app/data/`: Binance spot and USD-M futures klines as polars frames, a per-day Parquet cache outside the repository, and the CLI `python -m app.data` |
| trial `CLAUDE.md` | 9–10 | Setup `pip install pytest ruff`, "declares no extras" | Setup `pip install pytest ruff polars`, as `commands.setup`; the one runtime dependency `polars>=1.0`; the CI pins with polars |
| trial `CLAUDE.md` | 12 | healthy: `1 passed` | healthy: every test passes, `N passed` |
| trial `CLAUDE.md` | 26 | "`tests/` holds the pytest suite." | lines for `app/data/` (its modules, its public API, the cache directory's order), `scripts/measure_storage.py`, and the offline tests (`tests/binance_stub.py`, `tests/fixtures/binance/`) |
| trial `CLAUDE.md` | 33 | `- (none yet)` | optional: a change that adds a runtime dependency or tests leaves Setup, Test and the CI install step outdated, so `plan.md` names those lines for the owner |

## Port list
This PR touches none of `plugin/detect/`, `plugin/ci/run_phase.py` or the detect, runbook and fix workflow templates: it is not on the port list.

## Proposed edits for the owner
None to a guardrail file of this repository. One proposal for `HANDOFF.md` (stable, changed in a PR of its own), for the owner to accept or not: under "How a session ends", a session that works in the sample or the trial repository for this framework writes its session file and its record here, in a documentation PR of its own.

## What the owner does
| When | Act |
|---|---|
| Now | Merge this PR when `Framework checks` is green on its final head. |
| Then | #403: `gh pr update-branch 403 --repo luissiviero/sdlc-framework` (a design fix round does not merge `main` in, `plugin/ci/run_phase.py:3718`), then an `@claude` comment on #403. |
| Then | The trial: the table above as a PR on the trial's `main`, merged, then an `@claude` comment on trial #6. |
