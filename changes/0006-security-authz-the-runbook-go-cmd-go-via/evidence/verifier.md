# Verifier report — change 0006, build, fix round 2 (HEAD 490423111acdcb674ec26fe5474cebedb513ea04)

The record read is `evidence/gate-design.json`, the runner's run on `ff4344849a` (2026-11-04T14:19:39Z): the design-phase tree, older than the fix commits `5ae9227` and `6a2429f` and this round's `4904231`, so it says nothing about the new tests or the fix. The final tree's result is the runner's, from the three targets it runs once after this session (check run `sdlc/test` and this phase's gate record). A red target there starts the next fix round by itself; nothing here stands in for it.

## Commands run
In this CI session (`SDLC_GATE_COMMANDS=runner`) the targets were read from the record, not run.

`gate-design.json` `commands` check: `ok: true`, `"reason": "build, test and lint exit 0"`, `"ran_by": "runner"`, no `deferred` flag.
- `python -m compileall -q plugin tests tasks.py .github/scripts`: exit 0, output `""`
- `python -m pytest`: exit 0, tail `.......................................................................s [ 97%] ... 2885 passed, 1 skipped in 250.68s (0:04:10)`
- `python -m ruff check . && python -m ruff format --check .`: exit 0, output `All checks passed!` / `299 files already formatted`

The change folder has no `evidence/test.log`, `build.log` or `lint.log`, as expected at build.

## Behavior exercised
`_human_label_actor` was called directly from an inline `python -I -c` script that loaded `plugin/detect/cli.py`, stubbed `_github().label_actor`, read no `.env*` and wrote no files; pytest was not started. `cmd_go` passes `approved` from `_approved_config` (the default branch's copy) at `plugin/detect/cli.py:1218-1222`.

**The changed behavior**
- Actor `colleague`, `GITHUB_REPOSITORY_OWNER=the-owner`: `(None, "sdlc:go was applied by colleague, not by the owner's account: left where it is (decision 34)")`.
- Actor `the-owner`: `('the-owner', '')`.
- Actor `THE-OWNER`: `('THE-OWNER', '')` (the match is case-insensitive).
- Config `{"owner": "colleague"}` (the default branch's stand-in), actor `the-owner`: refused with the owner reason.
- Same config, actor `colleague`: `('colleague', '')`.
- Just outside the tested inputs:
  - No environment variable, `--repo o/r`, actor `o`: `('o', '')`.
  - Same setup, actor `the-owner`: refused.
  - Empty repo and no environment variable: refused (fails closed).

**First neighbouring flow: the bot or automation branch.** Actor `github-actions[bot]`: `(None, 'sdlc:go was applied by github-actions[bot], not by a person: left where it is')`. The text is unchanged and this check still runs before the owner check (R6).

**Second neighbouring flow: the label-event paths.**
- Actor `None`: `(None, 'no \`labeled\` event for sdlc:go on #12')`.
- `ok: False`: `(None, 'could not read the label events: boom')`.

Both texts are unchanged.

**This round's test edit.** The diff of `tests/test_detect_cli.py:859-860` replaces `runbook_records(change) == []` with a check that `evidence/runbook-rollback-deploy.json` has `status == "go-requested"`. The path matches `plugin/detect/runbooks.py:956` (`runbook-{safe}.json`) and `json` is imported at line 13. The test runs `dispatch` before `go`, so the record exists. plan.md step 1 (line 10) says the same. The edit follows the owner's `sdlc:unlock-tests` (commit `30643eb`).

## Not exercised
- `cmd_go` end to end: the dispatch, the `_approved_config` read of `origin/main`, the runbook spy, `set_labels` and the `status.yaml` write. Only the call site's argument was checked.
- The new tests and every existing Go test on the final tree; in CI the runner judges them.
- The three targets on the final tree; `gate-design.json` covers `ff43448` only.
- Windows (this ran on Linux).
- An `sdlc.yaml: owner` given as a non-string or blank value.
- A `GITHUB_REPOSITORY`-only environment.
- The security-baseline check on the diff.

## Mismatches with plan.md / spec.md
None in behavior. One wording note: spec.md:5 (R1) and spec.md:33 (Acceptance) say "no runbook record is written" / "no runbook record". The dispatch writes `runbook-rollback-deploy.json` before the Go, so the test checks that the Go left that record at `go-requested` and wrote none of its own. plan.md:10 was updated to match; spec.md keeps the old wording.

## Verdict
matches the plan
