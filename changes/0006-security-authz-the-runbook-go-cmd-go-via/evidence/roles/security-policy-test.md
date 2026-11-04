# Security & policy brief, gate (test)

## auth
- Verdict: continue
- What the change does to it: `plugin/detect/cli.py` `_human_label_actor` now also requires the `sdlc:go` label's actor to be the owner's account (`state.unpark.is_owner_actor`, decision 34), read from the default branch's `sdlc.yaml`, so a collaborator with label rights can no longer start a runbook with the runbook secrets; `tests/test_detect_cli.py` adds the reproducing tests and one declared fixture line.
- What could break: a project whose Go was routinely applied by a non-owner account (or an organization repository that does not name `owner:` in `sdlc.yaml`) now gets `performed: false` with the reason and must have the owner apply the label; nothing runs in that case (fail closed).
- How to undo it: revert the fix commit on `plugin/detect/cli.py` (the import and the four-line owner check); the tests' fixture line is harmless to keep, but the two new tests would then fail and must be reverted with it.
