---
name: definition-of-done
description: What "done" means for a change in the SDLC framework. Use before reporting any task, phase or change complete, when asked whether something is finished, ready, mergeable or can move to the next phase, and when writing a PR summary ("is this done", "ready for review", "can we ship", "summarise the change").
---

# Definition of done

## Source
- Article p.28 step 6 ("Make verification part of 'done.' ... Run the tests before reporting
  a task complete, and show the output") and the CLAUDE.md verification block, p.28–29
  governance ("Verification before a task is reported done" is what is enforced; the
  evidence is "the literal output" of the toolchain), p.33 (findings "ranked by severity",
  the tally), p.42 (the confidence gate decides whether a stage's output continues).
- `docs/OPERATING_MODEL.md` sections 1, 3 and 6 of the framework: the artifact per phase, the
  deterministic checks of the gate, park never page.
- Owner's definition of done: the project's `policies/definition-of-done.md`, written by the
  owner in their own words (ROADMAP R27). Read it first when it exists: where it and this
  skill differ, the source wins, over a project override too; a rule here it does not
  mention still applies. No file means these rules alone. It is a guardrail path (decision
  40): never edit it in a run.
- Project override: `.claude/skills/definition-of-done/SKILL.md`.

## Done, per phase
- **intent**: `intent.md` with its five sections, status `proposed`, on `sdlc/<id>/intent`,
  PR open with `sdlc:intent-ready`.
- **design**: `spec.md` (requirements, design, open questions from the intent answered or
  carried forward, flagged concerns each closed with a decision, acceptance target) and
  `plan.md` (files that change, order of work, risks, options not taken, proof) written by
  the planning run; adversarial verdict written; the design gate passed or parked.
- **build**: the diff stays inside `plan.md`; every commit that changes source updates
  `plan.md` in the same commit; build, test and lint targets green with their literal output
  pasted; verifier report in `evidence/verifier.md`; adversarial verdict; the build gate.
- **test**: fresh-context full run; `evidence/test.log`, `build.log`, `lint.log`,
  screenshots for UI changes, `verifier.md`; the test gate.
- **deploy**: review passes published as `evidence/review-findings.json` with no
  Important finding open; PR summary ≤5 bullets (what changed and why, evidence status,
  findings by severity, plan conformance, what needs the code owner); merge is the code owner's.
- **Always**: no guardrail file touched unless the intent says `Framework change: yes`; no
  risk-list item touched without its line in the "Needs your close look" banner, which the
  owner's merge accepts (decision 35; at the deploy gate, the code owner's approving review,
  decision 36); no
  test skipped, weakened or
  deleted; nobody notified — a run that cannot finish parks with "What I need from you".

## Check
Run the deterministic check and include its output in your summary (article p.22 pattern):
```
python "${CLAUDE_PLUGIN_ROOT}/plugin/skills/definition-of-done/check.py" --root "${CLAUDE_PROJECT_DIR}" --id <change id> --phase <phase>
```
It runs the confidence gate in dry-run (nothing recorded) and prints each check. Example
output:
```
## definition-of-done check (gate dry run)
- change 0001 (percent-helper), gate (build), automated gate
- [x] limits: within the run limits
- [x] artifacts: every required artifact exists and has its template sections
- [ ] adversarial_review: evidence/adversarial-review-build.json missing
- verdict if run now: **park**
  - adversarial_review needs: Run the adversarial-reviewer agent in a fresh context for this phase; it writes the verdict JSON.
```
Deterministic backing, item by item (R27): intent to test, the gate itself (`plugin/gate/cli.py
check`: artifacts, commands, evidence, plan sync, the adversarial verdict); the screenshots
for UI changes at test only in part: when `sdlc.yaml: commands.drive` is set, the screenshots
named as `screenshot:` items of the approved plan are checked under `evidence/proof/` by the
gate's `proof` entry (change 0004), and by-hand screenshots under `evidence/screenshots/` are
still required by no check (`REQUIRED_EVIDENCE` names the verifier report and the toolchain
logs); deploy, the gate's
findings check on `evidence/review-findings.json`; "Always", the protected-paths hook, the
shell guard and the gate's `guardrails` check for the guardrail files, the gate's
`risk_list` check for the banner, the test ratchet and, on a fix-type change, the test-file
lock for the tests. "Nobody notified" has no hook: the runner sends nothing but the review
request (decision 31). This skill is advisory and tells the model what it will be measured
against (p.22 governance).
