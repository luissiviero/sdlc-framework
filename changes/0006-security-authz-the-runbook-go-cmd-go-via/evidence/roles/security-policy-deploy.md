# Security & policy brief, gate (deploy)

## auth
- Verdict: continue
- What the change does to it: `plugin/detect/cli.py` `_human_label_actor` now also refuses a `sdlc:go` label unless `state.unpark.is_owner_actor` says its actor is the owner's account (decision 34). The rule reads the default branch's approved `sdlc.yaml` that `cmd_go` already passes in, so a collaborator with label rights can no longer start a runbook that holds the runbook secrets. `tests/test_detect_cli.py` adds the reproducing tests (a collaborator is refused; `owner:` is read from `origin/main`, never from the head) and one declared fixture line.
- What could break: a Go applied by any account other than the owner's now does nothing (`performed: false`, the label stays). An organization repository that does not name `owner:` in `sdlc.yaml` falls back to the organization login, and no person's label will match it until `owner:` is set. In both cases nothing runs (fail closed).
- How to undo it: revert commit `6a2429f` (the import and the owner check in `plugin/detect/cli.py`) together with the two new tests in `tests/test_detect_cli.py`, which would fail without it. The fixture line can stay.
