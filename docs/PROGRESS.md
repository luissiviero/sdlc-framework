# Progress — the live proof on the sample, part 1: change 0015 up to a red deploy run, and the checkout check's bytecode as plugin **1.0.12** (2026-10-19)

This session runs on branch `ccr-6281cac2-hdaob7`, from the owner's prompt of 2026-10-19 (draft a small change's intent on the sample, follow its runs, record NOTES §47's "Not verified yet" claims in `docs/notes/`, stop at each gate). The previous record (the fast lane's recovery as 1.0.11, choice 232, PR #242 of the parallel session `ccr-9e7c0e1f-wgcq4m`) is now `docs/progress/2026-10-19-fast-lane-recovery-1.0.11-and-choice-232.md`, unchanged; the 1.0.10 record before it is #242's `docs/progress/2026-10-19-1.0.10-and-choices-228-231.md`. The owner's merge order of 2026-10-19 was #242, then this PR, then #240, so this PR is 1.0.12. The session's own file comes with its last PR.

## Summary
- **Change 0015 on the sample** (NOTES §48): the session opened intent PR #69 as a draft from the owner's account; the owner merged it. Design passed gate (b) on the fast lane (routine), build and test passed, and the deploy run 39270275720 ended red before phase (e).
- **What the runs proved:** the App's pushes start CI with no approval click; the App's labels, closes and dispatches work, and the `[bot]` guards skip its events; the build ran under the build caps. R47, the `/proc` claim, the App's own pull requests and the 1.0.10 paths were not met (NOTES §48 says why for each).
- **1.0.12: the checkout check no longer refuses its own bytecode.** `plugin/ci/checkout_check.py` imported `ci.app_token` (since R49's fix round 1, `d715754`) from the framework checkout it then judges with `status --ignored`, so Python's `__pycache__` made every deploy run of 1.0.9 to 1.0.11 red, and every detect run that files a change. The script now sets `sys.dont_write_bytecode` before the import. The new test runs the real script from a fresh clone carrying `plugin/ci`; on the old code it fails with the run's own message.

## Proposed edits for the owner
The sample's pin, after `v1.0.12` is tagged (a guardrail row, the owner's edit):

| Link | Row | What is there | What it must become |
|---|---|---|---|
| [sdlc.yaml](https://github.com/luissiviero/sdlc-sample-python/blob/main/sdlc.yaml) | `plugin: version:` | `1.0.10` | `1.0.12` |

The thirteen workflow copies do not change: neither 1.0.11 nor 1.0.12 changes a workflow template, and this fix is in the framework checkout the workflows fetch at the pin.

## Left
- **Change 0015 waits at the deploy run.** After the pin moves, SDLC deploy is dispatched again for 0015 (`change_id: 0015`, `head_ref: sdlc/0015/c`). Gate (e) and R47's review request on the draft build PR come after that.
- **Not verified live:** R47; a sandboxed session reading the runner's process through `/proc`; the App's own pull requests; the 1.0.10 paths (NOTES §48); that the ordinary fast-lane path still works on 1.0.11 (the next fast-lane change on the sample).
- **A nit for later:** `pr/cli.py upsert` cuts a long open question at its line end in the intent PR's summary (NOTES §48).
- **The port list** (HANDOFF rules): this PR touches none of its paths (`plugin/ci/checkout_check.py` only).

## Checks (this repository)
On the final head, after `python -m pip install -e ".[dev]"`, chained with `set -o pipefail`: the four commands of `HANDOFF.md`'s standing precondition 1. Their output is in the PR.
