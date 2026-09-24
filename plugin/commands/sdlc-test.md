---
description: Phase (d) test — in a fresh context, run the project's full test, build and lint targets into changes/<id>/evidence/ (test.log, build.log, lint.log), fix what fails within the iteration cap, take screenshots for UI changes, run the verifier, get the adversarial verdict, call gate (d) and update the build PR. Standard: continue to /sdlc-deploy; Full: wait for sdlc:d-approved. Re-runnable.
argument-hint: [change id, e.g. 0001]
disable-model-invocation: true
allowed-tools: Bash(python "${CLAUDE_PLUGIN_ROOT}/plugin/state/cli.py" *), Bash(python "${CLAUDE_PLUGIN_ROOT}/plugin/gate/cli.py" *), Bash(python "${CLAUDE_PLUGIN_ROOT}/plugin/panel/cli.py" *), Bash(python "${CLAUDE_PLUGIN_ROOT}/plugin/evidence/collect.py" *), Bash(python "${CLAUDE_PLUGIN_ROOT}/plugin/pr/cli.py" *), Bash(git *), Bash(gh *), Read, Glob, Grep, Edit, Write, Agent
---

# /sdlc-test — phase (d)

Source: build guide step 24 (composition: OPERATING_MODEL §4.1), step 13 (the feedback
loop, article p.27–29: "Run the tests, run the build, take the screenshot. Claude iterates
until the check passes"; evidence is "the literal output" of the toolchain), step 28 (gate
(d): evidence in `changes/<id>/evidence/` and the check run), step 25 (test-file lock).

This phase runs in a **fresh context**: a new session or a separate `claude -p` job, never
the one that wrote the code (article p.27: the verdict "is not colored by the assumptions
that produced the code"). Unattended: never ask the owner; a blocker parks.
One shell command per Bash call: an unattended run allows only an explicit list of
command prefixes (`git *`, `python *` and a few more, per phase: `plugin/ci/run_phase.py`
and this command's `allowed-tools`), Claude Code checks each part of a chained command
against that list on its own, and a chain with one part the list does not cover is denied
whole, so the step it carried is lost (the first `/sdlc-fix` run of 2026-09-23 lost its
final commit to `cd ... && python ...`).

## 0. Preconditions
- Change id `$ARGUMENTS` (or the single change whose `status.phase` is `c` with gate
  `passed` — in the Full profile also labelled `sdlc:c-approved`; stop and list otherwise).
- `python "${CLAUDE_PLUGIN_ROOT}/plugin/gate/preflight.py" --root "${CLAUDE_PROJECT_DIR}" --id <id> --phase d`:
  if `allow` is false, stop and report its `reasons` (a `parked: ...` reason is the
  owner's item). Never judge `status.yaml` yourself.
- `git fetch origin`, `git switch sdlc/<id>/c`, `git pull --ff-only origin sdlc/<id>/c`.
  Phases (c), (d) and (e) share this branch and its PR (OPERATING_MODEL §8).
- `python "${CLAUDE_PLUGIN_ROOT}/plugin/gate/cli.py" start-run --root "${CLAUDE_PROJECT_DIR}" --id <id> --phase d`
- `python "${CLAUDE_PLUGIN_ROOT}/plugin/state/cli.py" set-phase --root "${CLAUDE_PROJECT_DIR}" --id <id> --phase d`
- Read `spec.md` (Acceptance), `plan.md` (Proof) and `status.yaml` (`change_type`,
  `iterations`). Load `definition-of-done` and `coding-standards`.

## 1. Collect the evidence (build guide step 28; article p.27 step 1)
```
python "${CLAUDE_PLUGIN_ROOT}/plugin/evidence/collect.py" --root "${CLAUDE_PROJECT_DIR}" --id <id>
```
It runs the three `sdlc.yaml` commands (`test`, `build`, `lint`) with the gate's timeout,
writes the literal output to `changes/<id>-<slug>/evidence/test.log`, `build.log`,
`lint.log` (exit code and duration in the first line) and prints a JSON summary with
`all_green`. Read the summary, not the logs, unless something failed.

## 2. Fix loop, bounded (article p.28: "two or three rounds is normal")
While `all_green` is false:
1. `python "${CLAUDE_PLUGIN_ROOT}/plugin/gate/cli.py" bump-iteration --root "${CLAUDE_PROJECT_DIR}" --id <id>`
   — if it reports the cap reached (`gate.max_iterations`, or
   `max_iterations_non_routine` when the verdict classed the plan non-routine), stop:
   go to step 5 and let the gate park with the partial evidence.
2. Read the failing log, fix the code (never the test in a fix-type change: the lock hook
   denies it and REVIEW.md rejects it; in a feature change a test may change only when
   `plan.md` Proof says so and `plan.md` is updated in the same commit).
3. Commit: `python "${CLAUDE_PLUGIN_ROOT}/plugin/state/cli.py" commit-phase --root "${CLAUDE_PROJECT_DIR}" --id <id> --phase d --message "test(<id>): fix <what>" --paths <files>`
4. Re-run step 1.

## 3. UI changes: screenshot loop against the mock (article p.27 step 2)
Only when `plan.md` Proof or `spec.md` Acceptance names a mock, screen or screenshot: run
the app (the project's run instructions or the `run` skill if available), capture the
screen into `changes/<id>-<slug>/evidence/screenshots/<name>.png`, compare with the mock,
adjust and repeat (bounded by the same iteration cap). Say in `evidence/verifier.md` what
was compared and what differs. Without a browser or screenshot tool in this session, write
`evidence/screenshots/README.md` saying so; the gate treats it as evidence missing only when
the plan asked for screenshots.

## 4. Verify in a fresh context (agent `sdlc:verifier`)
Delegate to `sdlc:verifier` with the change id. Store its report as
`changes/<id>-<slug>/evidence/verifier.md` (overwrite the (c) report: this one covers the
full suite). Commit the evidence:
`commit-phase ... --phase d --message "test(<id>): evidence"` and push
(`git push origin sdlc/<id>/c`).

## 5. Adversarial verdict and gate (d)
The reviewer has no shell, so write the diff it reads first, in one call (`<base>` is the
default branch, `origin/<default>` after the fetch: the base the gate diffs against):
`git diff --stat --patch --output=changes/<id>-<slug>/evidence/diff-d.patch <base>...HEAD`,
then `git rev-parse HEAD` for the full sha. The diff file is evidence: it is committed with
the gate (d) evidence commit below.
Delegate to `sdlc:adversarial-reviewer` (change id, phase `d`, project root, the full HEAD
sha, the path `changes/<id>-<slug>/evidence/diff-d.patch`); it writes
`evidence/adversarial-review-d.json` for HEAD.

### Deferred review: the panel settles the judgment items (decision 21; build guide step 16a)
```
python "${CLAUDE_PLUGIN_ROOT}/plugin/panel/cli.py" items --root "${CLAUDE_PROJECT_DIR}" --id <id> --phase d
```
It prints the review mode (`sdlc.yaml: review`, `status.yaml: review_override`), the items
the gate would park on that belong to the panel's fixed list (an open flagged concern, a
concern naming contradicting policies, the reviewer's `escalate` verdict, an Important
finding the run cannot fix, the verifier's "does not match the plan"), which of them the
ledger already decides, and under `parks` what stays the owner's whatever the mode (a
risk-list hit, a guardrail file, a run limit, an infrastructure failure). When `mode` is
`parked` or `pending` is empty, go on to the gate. Otherwise, for each pending item `n` in
order, three fresh contexts, each with the brief printed by
`python "${CLAUDE_PLUGIN_ROOT}/plugin/panel/cli.py" prompt --root "${CLAUDE_PROJECT_DIR}" --id <id> --phase d --item <n> --member <reviewer|advocate|conciliator>`:
1. **reviewer** — delegate to a general-purpose sub-agent with the `reviewer` brief; it
   writes `evidence/panel/d-<n>-reviewer.md`.
2. **devil's advocate** — delegate to `sdlc:adversarial-reviewer` with the `advocate`
   brief, on the model `sdlc.yaml: panel_advocate_model` names (pass it as the sub-agent's
   model: the per-invocation model wins, NOTES §11c; a panel on one model shares its blind
   spots), blind to the reviewer's file; it writes `evidence/panel/d-<n>-advocate.md`.
3. **conciliator** — delegate to a general-purpose sub-agent with the `conciliator` brief;
   it reads both files and writes `evidence/panel/d-<n>-conciliator.json`.
Then record it:
`python "${CLAUDE_PLUGIN_ROOT}/plugin/panel/cli.py" record --root "${CLAUDE_PROJECT_DIR}" --id <id> --phase d --item <n>`
— one panel call is one iteration (exit 3 at the cap: stop the panel, the gate parks); it
appends the line to `evidence/decisions-d.json` (and the `.md` the owner reads), and for
a concern closes the item in `spec.md` as `decided (by panel): <decision> — <concern>`. Apply
what the decision asks beyond that (an `escalate` decided `continue` needs nothing more; a
fix the decision names is made now, `plan.md` in the same commit). When any file changed,
commit (`commit-phase ... --phase d --message "test(<id>): panel decisions"`),
then re-run step 5 for the new HEAD (a verdict never outlives the diff it
judged); an `escalate` with new reasons is a new item: run `items` once more. The panel
never decides a park item, never raises a limit, never touches a guardrail file, and never
asks the owner: the owner reads "Decisions taken for you" at the gate and overturns any
line with a review comment.

Then the gate:
`python "${CLAUDE_PLUGIN_ROOT}/plugin/gate/cli.py" check --root "${CLAUDE_PROJECT_DIR}" --id <id> --phase d`
(it requires `test.log`, `build.log`, `lint.log` and `verifier.md`, green; exit 0 continue ·
3 wait · 4 park). Commit: `commit-phase ... --phase d --message "test(<id>): gate (d) evidence" --push`.

## 6. Update the build PR and the check run
```
python "${CLAUDE_PLUGIN_ROOT}/plugin/pr/cli.py" upsert --root "${CLAUDE_PROJECT_DIR}" --id <id> --phase d --check-run
```
It regenerates the ≤5-bullet summary (evidence status now filled from the logs), applies
the gate's label (`sdlc:d-ready` in the Full profile, `sdlc:needs-human` when parked) and,
when a token is available, posts the phase (d) check run with the evidence summary
(build guide step 28).

## 7. Hand over
- `continue` (Standard): report "gate (d) passed → /sdlc-deploy <id>"; the workflow
  dispatches the review job itself. Do not run (e) here.
- `wait` (Full): report the PR URL and "gate (d): approving review + `sdlc:d-approved`
  starts the review phase".
- `park`: report the PR URL and the gate's "What I need from you" block.

Never edit `.claude/**`, `CLAUDE.md`, `REVIEW.md`, `sdlc.yaml`, `intent.md` or `spec.md`.
Never weaken, skip or delete a test to get green. Never use bypass-permissions mode. Never
notify anyone.
