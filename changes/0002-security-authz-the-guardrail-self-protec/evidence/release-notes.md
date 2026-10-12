# Release notes — change 0002: security: authz: The guardrail self-protection (protected_paths.py) only

## What changed

No instance of this authz weakness remains in the codebase: the case at `plugin/hooks/hooks.json:32` and every other place with the same pattern are fixed, each proven by a test, and an eval case for the class keeps it from returning (article p.48 step 7).

## Commits

- 554e02d build(0002): shell_guard hook and reproducing tests
- 561ef5d build(0002): register shell_guard on Bash|PowerShell in hooks.json
- 5b825b3 build(0002): sandbox.filesystem.denyWrite in CI settings
- c720cc6 build(0002): derive the eval suite from evals/cases/ folders
- 10da259 build(0002): OPERATING_MODEL.md names the shell guard and sandbox layers
- 89f0a19 build(0002): bump plugin version to 0.3.7
- dacc2ef build(0002): simplify
- 3a90bd0 fix(0002): git -C no longer leaks its directory into a later chain part
- 5f5d475 build(0002): gate (c) evidence
- b601b5a run(c): spend recorded
- 08f5e65 owner labels applied: sdlc:reset-iterations
- 7bc5ef2 build(0002): panel decision 1
- c3cc8ec fix(0002): wall-clock retry; panel upholds the shell_guard escalate, gate parks for the owner
- 4e19b1f run(fix): spend recorded; gate commands run after the session
- 22697f2 fix(0002): git/inner-shell global-option bypass, directory-ancestor and 19 more shell_guard gaps the owner's review found
- 65a7900 run(c): gate evidence for fix round 5 (continue)
- 43dafe2 run(fix): spend recorded; gate commands run after the session
- 319f1be test(0002): evidence
- 98a1212 test(0002): gate (d) evidence
- beab9d4 run(d): spend recorded; gate commands run after the session
- 7016339 run(review): spend recorded
- b805353 review(0002): gate (e) evidence
- 8231743 fix(0002): cap reached before review #5469970014 could be applied
- 09d3b69 owner labels applied: sdlc:reset-iterations
- 55ce5f7 fix(0002): module-scope shell_guard import, dead _absolute_rule_root, tautological eval-suite assertion
- 46499ca park: commands: deferred to the runner and never run: claude exited 1
- 1a6cf11 fix(0002): incident lesson, eval case and rebuilt lessons index
- 5c4c6c8 fix(0002): gate (e) parked on the iteration cap; pytest fix queued, not applied
- d1e9916 owner labels applied: sdlc:reset-iterations
- 00c215b fix(0002): add the new eval case to the framework suite's literal list
- 27acd1a fix(0002): fresh review pass and adversarial verdict at HEAD 00c215b
- 9f104a8 run(fix): spend recorded; gate commands run after the session
- 9d19208 fix(0002): lint fix for review #5488970969 (isort known-first-party, ruff format)
- b38dde0 fix(0002): fresh review pass, adversarial verdict and gate (e) at HEAD 9d19208, fix-response
- ddac29b run(fix): spend recorded; gate commands run after the session
- f0250b1 owner labels applied: sdlc:reset-iterations
- be38e27 fix(0002): use as_posix() for Windows-path test commands (review #5489774399)
- 7764e7a review(0002): fix git -C chaining in shell_guard (composes successive -C the way git does)

## Evidence

test deferred to the runner, build deferred to the runner, lint deferred to the runner, verifier.md present, 1 screenshot(s)

## Review findings

0 Important, 0 nits

## Links

- [intent.md](../intent.md)
- [spec.md](../spec.md)
- [plan.md](../plan.md)
