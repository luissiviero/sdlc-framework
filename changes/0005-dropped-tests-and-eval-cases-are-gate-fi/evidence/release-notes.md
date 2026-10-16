# Release notes — change 0005: Dropped tests and eval cases are gate findings

## What changed

When this change is done, each of these is true and has a test:

## Commits

- c5db264 park: preflight: claude_md: CLAUDE.md does not name the lint command of sdlc.yaml
- 09921cb owner labels applied: sdlc:reset-iterations
- 4b9259e fix(0005): propose the CLAUDE.md lint-command line the preflight park needs; owner to apply
- 6feb59b fix(0005): gate (c) re-run after the fix round parks again, now on missing verifier.md
- dddd5fb run(fix): spend recorded; gate commands run after the session
- 3f6b4ea run(fix): failed run record
- 43a1ab8 owner labels applied: sdlc:reset-iterations
- 7d4e472 build(0005): dropped tests and eval cases are ratchet gate findings
- 39dbee8 Merge branch 'main' into sdlc/0005/c
- 332b399 build(0005): verifier evidence
- 3bf9cc1 build(0005): gate (c) evidence
- aae41fa run(fix): spend recorded; gate commands run after the session
- e53be48 run(fix): spend recorded
- 7be5f77 owner labels applied: sdlc:reset-iterations
- 07f6d68 fix(0005): dot-prefixed rename destinations are not their own dropped case; ratchets check added to the expected set
- 2a2f793 build(0005): panel decision 1
- f8cfd28 fix(0005): panel decision 1 applied
- fdd2930 fix(0005): reconcile spec.md, plan.md and the dropped_eval_cases docstring with panel decision 1
- 4162bdb fix(0005): plan.md Proof lists the new pinning test
- d3b1a5a fix(0005): gate (c) continues
- 226b83b run(fix): spend recorded; gate commands run after the session
- 22f3aa2 test(0005): evidence
- ecac5c6 test(0005): gate (d) evidence
- 83ce2b3 run(d): spend recorded; gate commands run after the session
- ded6f36 run(review): spend recorded

## Evidence

test green, build green, lint green, verifier.md present, 1 screenshot(s)

## Review findings

0 Important, 3 nits

## Links

- [intent.md](../intent.md)
- [spec.md](../spec.md)
- [plan.md](../plan.md)
