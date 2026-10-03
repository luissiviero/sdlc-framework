# Release notes — change 0001: Split the large docs with an index each

## What changed

`docs/notes/` holds one file per NOTES section.

## Commits

- c444810 build(0001): split docs/DECISIONS.md
- 3114681 build(0001): split docs/NOTES.md
- d5b7ab0 build(0001): split docs/PROGRESS.md
- ec5846e build(0001): repoint live-doc links to the new indexes
- e2a134a build(0001): PROGRESS entry with the CLAUDE.md guardrail table
- 1210a11 build(0001): simplify
- 6053046 build(0001): gate (c) evidence
- 3f171d6 run(c): park record
- c6cb7ce run(c): spend recorded; gate commands run after the session
- 1923176 Merge main into sdlc/0001/c: the docs appended since the split
- 1183760 fix(0001): re-run gate (c); the park was the sandbox's masked view of the fixture .env
- 2b809c4 fix(0001): gate (c) evidence for the re-run — result continue
- 9d4eb88 run(fix): spend recorded; gate commands run after the session
- 552123c test(0001): evidence
- e2a923d test(0001): gate (d) evidence
- 5825bac run(d): spend recorded; gate commands run after the session

## Evidence

test green, build green, lint green, verifier.md present, 1 screenshot(s)

## Review findings

1 Important, 1 nits

## Links

- [intent.md](../intent.md)
- [spec.md](../spec.md)
- [plan.md](../plan.md)
