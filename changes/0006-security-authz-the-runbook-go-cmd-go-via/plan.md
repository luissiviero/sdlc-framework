# Plan: security: authz: The runbook Go (cmd_go via _human_label_actor) accepts the (from intent.md 2026-10-26, spec.md 2026-10-28)

## Files that change
- `tests/test_detect_cli.py` — the reproducing tests (a collaborator's `sdlc:go` is refused; the owner named in `sdlc.yaml` is read from the default branch, never the head) and the fixture change that names the test project's owner, in the first commit, before the test-file lock.
- `plugin/detect/cli.py` — `_human_label_actor` refuses a label whose actor is not the owner's account (`state.unpark.is_owner_actor`, decision 34); one top-level import added.

## Order of work
1. Write the reproducing test and see it fail. In `tests/test_detect_cli.py`, in the `# --- go` section, add `test_go_by_a_collaborator_performs_nothing`: `rollback_incident`, `write_proposal(change, "runbook:rollback-deploy")`, `dispatch` so the record says `go-requested`, `gh.actor = {"ok": True, "actor": "colleague", "reason": ""}`, then `go`; assert `code == 0`, `out["performed"] is False`, `"owner" in out["reason"]` and `"colleague" in out["reason"]`, `spy.calls == []`, `gh.named("set_labels") == []`, `runbook_records(change) == []`, `status_mod.read_status(change).runbook_authorized_by is None`. In the same commit, make the owner explicit: the `rollback_incident` fixture takes `monkeypatch` and sets `GITHUB_REPOSITORY_OWNER` to `the-owner` (the actor the existing Go tests use; `tests/conftest.py` removes every `GITHUB_*` variable and says a test that needs one sets it itself). Add the second test, `test_go_reads_the_owner_from_the_default_branch`, parametrized like `test_go_reads_the_automation_identity_from_the_default_branch`: `head` appends `owner: colleague` to the checkout's `sdlc.yaml` only and the colleague's label is still refused (`performed` false, no runbook call, no label change); `main` commits `owner: colleague` on `origin/main` through a clone, as `list_owner_as_automation_on_main` does, and the colleague's label then runs the runbook (`performed` true, `actor == "colleague"`, one runbook call) while `the-owner`'s does not. Run `python -m pytest tests/test_detect_cli.py -k go` and paste the output: the collaborator test and the `head` case fail (`performed` is True), the `main` case's `the-owner` half fails, every existing test passes. Commit the test file alone (`fix(0006): reproducing test`); the build run locks the test files after this commit.
2. The fix in `plugin/detect/cli.py`: add `from state.unpark import is_owner_actor  # noqa: E402` beside the `from state import ...` lines at the top; in `_human_label_actor`, after the bot/automation branch, add
   `if not is_owner_actor(actor, config, None, repo): return None, f"{label} was applied by {actor}, not by the owner's account: left where it is (decision 34)"`
   with a one-line comment that `config` is the default branch's copy. Nothing else in the function or in `cmd_go` changes. Update the function's section comment if it helps the reader; no other file.
3. Run the three targets (`python -m compileall -q plugin tests tasks.py .github/scripts`, `python -m pytest`, `python -m ruff check . && python -m ruff format --check .`) and the security-baseline check; paste the outputs. All green: the two new tests pass, the existing Go tests pass unchanged.
4. Commit the fix (`fix(0006): the runbook Go needs the owner's account`).

## Risks
- The existing Go tests use the actor `the-owner` on repository `o/r` with no owner named; without the fixture change of step 1 the fix breaks five of them. Mitigation: the fixture change ships in the test commit, before the lock, and is declared in spec.md's Flagged concerns; the tests' bodies and assertions are not touched, and they pass before the fix as today.
- `GITHUB_REPOSITORY_OWNER` set by the fixture could reach another reader. Checked: `plugin/state/unpark.py owner_login` is its only reader in the plugin; `origin_mismatch` reads `GITHUB_REPOSITORY`, which stays unset, so the tests of the rewritten origin keep their reasons.
- A circular import: `state.unpark` imports `state.conventions`, `state.status` and, lazily, `gate.policy` and `pr.github`; nothing from `detect`. A top-level import matches how `plugin/ci/run_phase.py`, `merge_step.py` and `comment_dispatch.py` import it; if the import order in `detect/cli.py` proves awkward, the suggested patch's function-local import (`# noqa: PLC0415`) is the fallback.
- The riskiest step is 2, the one line of authorization: a wrong argument (the head's `config` instead of the approved one, `env` other than the process's) would read the wrong owner. `cmd_go` passes `approved` already; the test's `head` case proves the head's copy is ignored, the `main` case proves the default branch's `owner` is read.
- The by-hand route (`detect/cli.py go --repo owner/name` on the owner's PC, no runner variables): the owner is the owner part of `--repo`, which `cmd_go` requires; an organization repository names `owner` in `sdlc.yaml`. Fail closed when none of the three is known: the Go is refused with its reason, nothing runs.
- A live project where the Go was authorized by a collaborator's account on purpose: after this change that label no longer runs the runbook; the reason names the owner's account, and the owner applies the label themselves. This is decision 34's intended narrowing, not a regression.
- No new dependency; no guardrail file; no workflow change (the runbook workflow's `if:` keeps its coarse `[bot]` check, as decision 34 allows).

## Options not taken
- Checking the owner in the runbook workflow's `if:` (`github.event.sender.login == github.repository_owner`): a workflow expression is the coarse check only (decision 34, point 3); it does not know `sdlc.yaml: owner` of an organization repository, and the step that holds the secrets must decide for itself (security-baseline rule 1). Not taken; the workflow is unchanged.
- Removing a non-owner's label instead of leaving it: the bot branch and the un-park labels leave a rejected label where it is (`plugin/state/unpark.py`), and removing it would need a labels call before the owner's act. Not taken (spec.md, the closed concern).
- Writing a second owner rule in `detect/cli.py` (reading `sdlc.yaml: owner` and the repository owner itself): decision 34 wants one function, fail closed; `is_owner_actor` already does it and is tested in `tests/test_owner_rounds.py`. Not taken.
- Naming the owner in the fixture project's `sdlc.yaml` on `main` instead of the environment variable: it would change the cached fixture repository (`fixture_repos.copy("detect-project", ...)`) for every test of the module and the dismiss tests' assumptions; the environment variable is one line in one fixture and the pattern `conftest.py` prescribes. Not taken.
- Changing the existing tests' actor from `the-owner` to `o`: edits six test bodies and the reason strings they assert; the intent forbids editing pre-existing tests to make the fix pass. Not taken.
- Also reading `author_association` of the label event: GitHub's `labeled` event carries the actor's login, not an association, and the owner rule is by login (decision 34). Not taken.

## Proof
- test: tests/test_detect_cli.py::test_go_by_a_collaborator_performs_nothing (to be written in step 1; fails on `80d7de5cebd4`, passes after step 2)
- test: tests/test_detect_cli.py::test_go_reads_the_owner_from_the_default_branch (to be written in step 1; parametrized `head` and `main`)
- test: tests/test_detect_cli.py::test_go_by_a_person_runs_the_runbook_and_reruns_the_gate (exists; unchanged)
- test: tests/test_detect_cli.py::test_go_not_by_a_person_performs_nothing (exists; unchanged)
- test: tests/test_detect_cli.py::test_go_reads_the_automation_identity_from_the_default_branch (exists; unchanged)
- test: tests/test_owner_rounds.py (exists; the rule itself)
- The three targets of `sdlc.yaml` green with their literal output pasted in the build's evidence; the security-baseline check reports nothing on the diff.
- Quantifiable target (spec.md Acceptance): a collaborator's `sdlc:go` performs nothing; the owner's runs the runbook once; the full suite green.

Interrogation (article p.16 step 3), answered and folded in above:
1. What could break: the callers of `_human_label_actor` (only `cmd_go`); the Go tests that use `the-owner`; nothing else reads the function. No data shape changes (`status.yaml: runbook_authorized_by` is written as before).
2. Riskiest step: step 2's argument choice, covered by the `head` and `main` test cases.
3. Options considered: the six above.
4. Implementable from the plan alone: yes, the test names, fixture, assertions, import and the one condition are named here; the suggested patch in `evidence/suggested-patch.diff` is the reference for the condition.
5. Proof items: the two new tests are to be written in step 1; the rest exist.
