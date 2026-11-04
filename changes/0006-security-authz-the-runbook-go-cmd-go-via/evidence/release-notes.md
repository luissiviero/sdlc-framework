# Release notes — change 0006: security: authz: The runbook Go (cmd_go via _human_label_actor) accepts the

## In plain words

*Written by the model from the diff and the plan; every section below is generated from files and git.*

The runbook Go, the label that lets an incident's runbook (a rollback or a configuration change) run with the runbook's secrets, now works only when the project owner's own account applies it. Before this change, any person with permission to label pull requests could start a runbook the owner never approved. A label from anyone else is now left in place and nothing runs, and the run's reason names the owner's account as the one that must apply it. The owner is read from the default branch's settings, so a branch cannot name its own owner. Every other owner action in the framework already worked this way.

<!-- sdlc:plain-words describes e9d99ece85c1441ee741734945c0175018694cc7 -->

## What changed

The finding is bounded (one file, one patch): `plugin/detect/cli.py:1183` no longer has the authz weakness, proven by a new test that reproduces it before the fix and passes after it.

## Commits

- 5ae9227 fix(0006): reproducing test
- 6a2429f fix(0006): the runbook Go needs the owner's account
- 78d19fe build(0006): parked: the locked reproducing test asserts no runbook record after dispatch
- 5e345d7 build(0006): build PR #405 recorded
- 30643eb owner labels applied: sdlc:unlock-tests
- 4904231 fix(0006): the collaborator Go test checks the dispatch record still says go-requested
- 8bbe5b7 fix(0006): round 2 evidence: verifier, verdict, gate continue
- 1efc48d run(fix): spend recorded; gate commands run after the session
- 44689aa test(0006): evidence
- e2eca9b test(0006): gate (test) evidence
- 892a57f run(test): spend recorded; gate commands run after the session
- 2b7db17 run(review): spend recorded
- e9d99ec release(0006): lesson and eval

## Evidence

test green, build green, lint green, verifier.md present, 0 screenshot(s)

## Review findings

4 Important, 2 nits

## Links

- [intent.md](../intent.md)
- [spec.md](../spec.md)
- [plan.md](../plan.md)
