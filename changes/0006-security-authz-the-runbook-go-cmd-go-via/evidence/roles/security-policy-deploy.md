# Security & policy brief, gate (deploy)

## auth
- Verdict: continue
- What the change does to it: `plugin/detect/cli.py` `_human_label_actor` now refuses an `sdlc:go` label from any account that fails `state.unpark.is_owner_actor` (decision 34). The owner is read from the default branch's `sdlc.yaml`, the copy `cmd_go` already passes. Only the owner's account can authorize a runbook. A refused label performs nothing and stays on the PR. `tests/test_detect_cli.py` proves both cases: a collaborator's label is refused, and a head that names its own owner is ignored.
- What could break: Anyone who authorized Go from a collaborator's account will now get a refusal that names the owner's account. On an organization repository the Go is also refused, by design (fail closed), until `sdlc.yaml: owner` names the owner on the default branch. The two Important findings in review-findings.json are about the new eval case, not this auth check.
- How to undo it: Revert the commit that adds the `is_owner_actor` check and its import in `plugin/detect/cli.py` (6a2429f). The Go then falls back to the "any person" check. That brings back the weakness this incident reported.
