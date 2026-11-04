# Fix round 1 (design), 2026-11-04

Source of the requests: `evidence/fix-requests.json`, collected by the runner at head `7d9793a` (decision 34); no review or comment was read from the pull request by this session.

## Requests
- luissiviero (OWNER), https://github.com/luissiviero/sdlc-framework/pull/403#issuecomment-6632926759 — applied: the comment is the round's trigger and carries no words after `@claude` (decisions 24 and 28), so the change request of this round is the gate's park below. Nothing in `spec.md` or `plan.md` was asked for and nothing in them changed.
- The gate's park (`status.yaml: parked_reason`, `evidence/gate-design.json` of 2026-10-28T16:48:12Z): `commands: not green: test (exit 1)`, ten failures in `tests/test_cancelled_park.py` — applied by the merge of `main` into this branch. The cause was not this change's work: the phase workflows export `HEAD_REF`, the suite's autouse fixture did not remove it, and the cancelled-run check compared the fixture's branch with the job's own (the session file `docs/handoffs/sessions/2026-11-03-claude-keen-mendel-3zipla.md`). Pull request #404 (`b118a1b`, merged in `5a4178d`) added `HEAD_REF` to the runner's variables `tests/conftest.py` removes before every test, with no assertion changed. The owner merged `main` into `sdlc/0006/design` in `7d9793a`, so `origin/main` is an ancestor of this round's head and `tests/conftest.py` on this branch carries the fix (checked by `git merge-base --is-ancestor`). This session cannot run the suite (the sandbox denies the fixture's `.env`, as `/sdlc-fix` step 1 says); the runner runs the three targets after this session, in the same workflow environment where they failed.

## Not applied
none

## What I need from you
nothing

# Fix round 2 (build), 2026-11-04

Source of the requests: `evidence/fix-requests.json`, collected by the runner at head `30643eb`. It has no review or comment requests and nothing under `not_applied`.

## Requests
- The gate's park (`status.yaml: parked_reason`, 2026-11-04T15:24:03Z) and the owner's `sdlc:unlock-tests` label (`tests_unlocked_by: luissiviero`): applied in `4904231`. In `tests/test_detect_cli.py`, `test_go_by_a_collaborator_performs_nothing` no longer asserts `runbook_records(change) == []`. It now asserts that the dispatch's `evidence/runbook-rollback-deploy.json` still says `go-requested`, as the park proposed. plan.md step 1 was updated in the same commit.
- Note: spec.md R1 and Acceptance still say "no runbook record". The dispatch writes that record before the Go, so the test checks that the Go leaves it unchanged. spec.md is not edited at build; the owner may reword it.
- Targets: this session cannot run them (the sandbox denies the fixture's `.env`). Ruff check and format pass on the edited file. The runner runs the three targets after this round.

## Not applied
none

## What I need from you
nothing
