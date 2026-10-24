# Release notes — change 0004: Drive target and proof items

## In plain words

*Written by the model from the diff and the plan; every section below is generated from files and git.*

Until now the gate only checked that a change builds, its tests pass and its paperwork is in order, never that the product actually does what the plan promised. A project can now set one optional command, commands.drive, that runs the product without a screen and saves screenshots and state files into the change's evidence/proof/ folder; the runner runs it after each build, test and deploy session, never inside the session. The plan's Proof section can name state items (a file, a key and the expected value) and screenshot items, and the gate compares them on the final tree against the plan the owner approved, so a value that differs or a file never produced starts a fix round instead of reaching the owner as green. The PR shows how many items matched, images stay small (50 KB, ten per run), and the job time limits only count the drive when it is set, so a project without a drive sees no change at all. The timeout comments for the four workflow templates are handed to the owner in evidence/workflow-comments.md, because the run may not edit those files.

<!-- sdlc:plain-words describes 8b5c531ab70971c88ca4d099e6c3e6386aaf0c7e -->

## What changed

When this change is done, each of these is true and has a test:

## Commits

- cd8a9bc build(0004): proof item grammar and comparison
- 29ea284 build(0004): drive readers, the drive run, the proof judgment and the runner's step (steps 2-5, limits of step 7)
- 8370024 build(0004): a failed proof entry is a round; the shared change-folder rule (steps 6 and 9)
- 536c1ed build(0004): the job time counts the drive; the (e) wall clock gives up its minutes (step 7)
- 6aa98cf build(0004): collect.py runs the drive by hand and reports the items (step 8)
- e785ff2 build(0004): the readers know the drive: PR evidence line, check run, release notes, triage, ux check (step 10)
- ad35fc1 build(0004): /sdlc-init proposes the Playwright drive; the template's three keys; the workflow comments go to the owner (step 11, plan departure in Risks)
- 6c9c1df build(0004): the proof item grammar, the policy skills, the agents and the phase commands follow the drive (step 12)
- e24f3b6 build(0004): plugin 1.0.40; the port list (step 13)
- 64238be build(0004): the test helpers set the template's own drive line
- 70e38a4 build(0004): simplify
- da8ed38 build(0004): gate (c) evidence
- 194c53b run(c): spend recorded; gate commands run after the session
- e8c3b76 test(0004): evidence
- d5e4f22 test(0004): gate (d) evidence
- db77059 run(d): spend recorded; gate commands run after the session
- eae172d run(review): origin/main merged before gate (e) is offered (R51)
- 8b5c531 run(review): spend recorded

## Evidence

test green, build green, lint green, verifier.md present, 1 screenshot(s)

## Review findings

0 Important, 5 nits

## Links

- [intent.md](../intent.md)
- [spec.md](../spec.md)
- [plan.md](../plan.md)
