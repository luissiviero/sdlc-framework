# Security & policy brief, gate (build)

## auth
- Verdict: continue
- What the change does to it: `plugin/detect/cli.py` `_human_label_actor` now also requires the `sdlc:go` label's actor to be the owner's account (`state.unpark.is_owner_actor`, decision 34), judged against the default branch's `sdlc.yaml`; a collaborator's label is refused with `performed: false`, nothing runs and the label stays. `tests/test_detect_cli.py` adds the reproducing tests and names the fixture's repository owner.
- What could break: a project whose Go was routinely applied by a non-owner collaborator will see the runbook refused until the owner applies the label; an organization repository that does not set `sdlc.yaml: owner` on the default branch will have its Go judged against the repository owner part of `GITHUB_REPOSITORY_OWNER`, and fails closed when that does not match.
- How to undo it: revert the fix commit on `plugin/detect/cli.py` (the one import and the one condition); the tests then fail, so revert the test commit with it.
