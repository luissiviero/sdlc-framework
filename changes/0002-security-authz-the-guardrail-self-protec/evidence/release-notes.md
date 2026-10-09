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

## Evidence

test green, build green, lint green, verifier.md present, 1 screenshot(s)

## Review findings

1 Important, 3 nits

## Links

- [intent.md](../intent.md)
- [spec.md](../spec.md)
- [plan.md](../plan.md)
