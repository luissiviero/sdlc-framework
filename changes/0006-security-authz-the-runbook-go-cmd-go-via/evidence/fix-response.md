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

# Fix round 3 (deploy), 2026-11-05

Source of the requests: `evidence/fix-requests.json`, collected by the runner at head `05dad30`, after the owner's `sdlc:reset-iterations` label (`iterations_reset_by: luissiviero`). It has one request, review https://github.com/luissiviero/sdlc-framework/pull/405#pullrequestreview-5778108589 by luissiviero (OWNER), with four items, and nothing under `not_applied`. Iteration 1 of the cap of 2.

## Requests
- Item 1, the version bump: applied. `.claude-plugin/plugin.json` and the `sdlc` entry of `.claude-plugin/marketplace.json` now say `1.0.51`, the next free patch that `python tasks.py next-free` reported (main is at `1.0.50`).
- Item 2, the case list: applied. `tests/test_evals.py`, `test_the_framework_suite_s_cases_load`, now lists `0006-security-authz-the-runbook-go-cmd-go-via` between `0006-sandbox-write-deny` and `0007-sandbox-credentials-hidden`, in the order `run.discover` sorts them. `python -m pytest tests/test_evals.py -k "cases_load or dry_run_lists"` passes in this session.
- Item 3, the rewrite of `evals/cases/0006-security-authz-the-runbook-go-cmd-go-via` so it passes against `tests/fixtures/sample-python-project`: not applied, see "What I need from you".
- Item 4, `tests/fixtures/sample-python-project/.env`: no change was needed. The committed copy on this branch is the same blob as on main (`git ls-tree` shows `d0e75201088fed5501a5180b1bc729db67738a79` for both `HEAD` and `origin/main`). No commit on this branch touches the file (`git diff --stat origin/main...HEAD` does not list it). Inside this session's sandbox, `git status` reports the file as modified only because the sandbox masks it (`git diff` says "unsupported file type"). This round does not commit the file.

## Not applied
- Item 3 of review 5778108589 (luissiviero): not applied. It needs a decision this round cannot take (below).

## What I need from you
Item 3: the fixture cannot exercise the fix. A framework case runs in a copy of `tests/fixtures/sample-python-project` with `/sdlc-init` applied, and the plugin is loaded only through `--plugin-dir` (`plugin/evals/run.py`, `run_case` and `compose`). The incident's code path is `detect/cli.py go`, which `_human_label_actor` calls. Only the runbook workflow (`template/.github/workflows/sdlc-runbook.yml:145`) starts it, and it reads the label events from GitHub. No hook, no command and no skill reaches it in a session. The workspace holds no `plugin/` code, and a case's `setup` and `command` checks run without a shell and with no variable that names the framework's path. Case 0002 can pass against the fixture because the code it covers is a hook (`shell_guard`), and that hook runs inside the fixture session. For case 0006 the fixture has nothing like that.

Which of these should the next round do?
1. Leave the case as a framework-repository case. It keeps its pytest commands, the runner gives the case a way to reach the framework (a `framework_root` setting in `checks.yaml`, or `setup`/`command` steps run with the framework root as their working directory), and the next round adds the test of that mechanism. This is a change to `plugin/evals/run.py`, which ships under the 1.0.51 bump of this round.
2. Change the case into a session case against the fixture: the setup writes an incident change whose `sdlc:go` came from a collaborator, the prompt asks the agent to run the runbook, and the check is that no runbook action ran. This needs a guard the session hits, for example the shell-guard hook refusing a run of `detect/cli.py go` or `runbook` from a session. That is new hook code and a design change.
3. Drop the eval case and keep the regression in `tests/test_detect_cli.py` only. This needs your waiver of the `lesson_and_eval` gate check for this incident.

# Fix round 4 (deploy), 2026-11-05

Source of the requests: `evidence/fix-requests.json`, collected by the runner at head `ac187a0`. It has two requests by luissiviero (OWNER) and nothing under `not_applied`. Iteration 2 of the cap of 2.

## Requests
- Review https://github.com/luissiviero/sdlc-framework/pull/405#pullrequestreview-5778108589, item 3 (the case rewrite): replaced by your option 1 in the review below and applied as it says. Items 1, 2 and 4 were applied in round 3.
- Review https://github.com/luissiviero/sdlc-framework/pull/405#pullrequestreview-5778239621: applied in `4958e80`.
  - Eval runner: `plugin/evals/run.py` takes a new case key, `framework_root: true`. With it, the case's `setup` and `command` checks run in the framework root (`--plugin-dir`, by default this checkout). The session, the `file` checks and the `output` check stay in the fixture workspace. Only the framework suite (`--fixture`) runs such a case. A project's suite fails it with the reason `framework_root is for the framework suite (--fixture) only` and starts no session.
  - Test of the mechanism: `tests/test_evals.py::test_framework_root_runs_setup_and_commands_in_the_framework_only_in_its_suite`. This session cannot copy the fixture's `.env`, so it ran `tests/test_evals.py` against a copy of the fixture without that file: 79 passed.
  - `checks.yaml`: the case sets `framework_root: true`, keeps the targeted `pytest -k` command and the output check, and drops the whole-suite `python -m pytest` check.
  - A reading you may correct: the two `file` checks (`plugin/detect/cli.py`, `tests/test_detect_cli.py`) are dropped too. They read the fixture workspace, which has no `plugin/` code, so they could never pass. Your review limited the mechanism to setup and command checks, so it does not move them. The targeted command still fails the case when none of its tests is found (pytest exits 5).
  - The `lesson_and_eval` gate check is unchanged.
  - `docs/OPERATING_MODEL.md:98`: the `sdlc-runbook.yml` row now says the label's actor must be the owner's account (`state.unpark.is_owner_actor`, read from the default branch's `sdlc.yaml`, since 1.0.51), and that any other account's Go is refused and left, with nothing run.
- Follow-ups of this round:
  - `a2ad922`: the lesson's Prevention paragraph no longer says the eval checks the code of `plugin/detect/cli.py`. The adversarial verdict at `4958e80` pointed this out.
  - `8cd193f`: `plan.md` lists `.claude-plugin/marketplace.json` on its own line, because the gate's plan parser reads one path per bullet.
- The deploy review panel settled three Important framework findings of the fix-type test-file rule (decisions 1 to 3, `evidence/decisions-deploy.md`):
  - The fixture's `.env` appears only because this sandbox masks the file. No commit touches it.
  - The `rollback_incident` fixture line was declared by design panel decision 1.
  - The `tests/test_evals.py` edits are the ones you asked for.
  You may overturn any of the three.
- Nits from the review pass and the verdict, not fixed in this round (fixing them would move HEAD after the verdict):
  - The `plugin/detect/cli.py:28` docstring and the `template/.github/workflows/sdlc-runbook.yml:12` header still say "a person".
  - The `checks.yaml` comment overstates that a single renamed test fails the case. The lesson's wording, "when none of them is found", is the accurate one.
  - spec.md's Design and R1 still describe the pre-round wording.
  - A `framework_root` case's setup writes into the framework checkout, which nothing cleans up. Case 0006 has no setup.

## Not applied
none

## Gate
Gate (deploy) at `807860f`: every check passes and the result is `wait` (`sdlc:deploy-ready`). Build, test and lint are deferred to the runner, which runs them after this session.

## What I need from you
nothing
