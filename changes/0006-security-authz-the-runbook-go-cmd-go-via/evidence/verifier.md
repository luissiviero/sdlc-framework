# Verifier report: change 0006, test phase

Verdict: **matches the plan.**

## Which tree this covers
The verifier read `evidence/gate-build.json`, the runner's run on commit `490423111acdcb674ec26fe5474cebedb513ea04` (2026-11-04T19:28:55Z). That is the tree this phase started from, not the final one. The runner runs the three targets on the final tree after this session, and their result shows in the `sdlc/test` check run and in this phase's gate record. The two commits after `4904231` (`8bbe5b7`, `1efc48d`) change only files under `changes/0006-.../`, and no file under `plugin/` or `tests/`.

## Commands (read, not run: `SDLC_GATE_COMMANDS=runner`)
The build gate's `commands` check reads `ok: true`, `ran_by: runner`, with the reason "build, test and lint exit 0".

| Target | Command | Exit code | Output tail |
|---|---|---|---|
| build | `python -m compileall -q plugin tests tasks.py .github/scripts` | 0 | (no output) |
| test | `python -m pytest` | 0 | `2888 passed, 1 skipped in 296.68s (0:04:56)` |
| lint | `python -m ruff check . && python -m ruff format --check .` | 0 | `All checks passed!` / `301 files already formatted` |

The first lines of `test.log`, `build.log` and `lint.log` carry this session's deferred mark (2026-11-04T19:35:19Z). They are placeholders that the runner replaces, not failures.

`evidence/failing-test.log` holds the build's record of the tests before the fix:
- **Fixture line alone:** `96 passed`, with every existing Go test listed as PASSED.
- **With the two new tests, before the fix:** `3 failed, 16 passed, 80 deselected`. The three failures are `test_go_by_a_collaborator_performs_nothing` (`assert True is False`) and both `[head]` and `[main]`. The `main` failure is on the-owner's half.

## Behavior exercised
**Diff review (`git diff origin/main...HEAD -- plugin tests`).**
- Only two files changed: `plugin/detect/cli.py` and `tests/test_detect_cli.py`.
- **`plugin/detect/cli.py`:**
  - A top-level import was added: `from state.unpark import is_owner_actor  # noqa: E402`.
  - In `_human_label_actor`, after the bot/automation branch, the change adds `if not is_owner_actor(actor, config, None, repo): return None, "<label> was applied by <actor>, not by the owner's account: left where it is (decision 34)"`.
  - `cmd_go` passes `approved`, the default-branch copy, and `cmd_go` itself is unchanged.
- **`tests/test_detect_cli.py`, existing tests:** the only change is the `rollback_incident` fixture. It now takes `monkeypatch` and sets `GITHUB_REPOSITORY_OWNER=the-owner` (panel decision 1). No existing test body or assertion changed.
- **`test_go_by_a_collaborator_performs_nothing`:** it asserts every item in plan.md step 1:
  - `code == 0` and `performed is False`
  - the reason names the owner and the colleague
  - no runbook call and no label change
  - the dispatch record still says `go-requested`
  - `runbook_authorized_by` is None
- **`test_go_reads_the_owner_from_the_default_branch`:**
  - `[head]`: the head's `owner: colleague` is ignored, and the colleague is refused.
  - `[main]`: the-owner is refused first, then the colleague's Go runs the runbook once, with `runbook_authorized_by == "colleague"`.
- **Credentials:** grepping the added lines for tokens, secrets, passwords, API keys, `ghp_`, `github_pat_`, `sk-ant` and private keys found nothing.

**Direct call of `_human_label_actor`** (the GitHub call replaced by a stub; with `GITHUB_REPOSITORY_OWNER=the-owner` and repo `o/r` unless stated):

| Actor | Config | Result |
|---|---|---|
| `colleague` | `{}` | refused with the owner reason |
| `the-owner` | `{}` | accepted |
| `THE-OWNER` | `{}` | accepted (case ignored) |
| `github-actions[bot]` | `{}` | refused with the unchanged "not by a person" reason, which comes first |
| `the-owner` | `{owner: colleague}` | refused |
| `colleague` | `{owner: colleague}` | accepted |
| `sdlc-bot` | named both automation identity and owner | refused as "not by a person" (fails closed) |
| `o` | `{}`, no environment variables | accepted (the owner comes from `--repo`) |
| `the-owner` | `{}`, no environment variables | refused |

With no owner known anywhere, `is_owner_actor` returns False (fails closed).

## Not exercised
- **Full `cmd_go` path:** not run through pytest in this CI session (sandbox rule). Runbook execution, label removal and the `status.yaml` write are covered only by the runner's suite.
- **Final tree:** the targets were not run on HEAD; the runner does that after this session.
- **`tests/test_owner_rounds.py`:** not run separately. It passed as part of the runner's full suite.
- **Windows:** not run.
- **Live GitHub:** the label-events API and `sdlc-runbook.yml` were not exercised.
- **Security-baseline tool:** not run; only the credential grep above was done.

## Mismatches with plan.md / spec.md
None. R5's "is required" is conveyed by "not by the owner's account", the literal string of plan.md step 2.
