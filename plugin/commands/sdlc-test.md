---
description: The test phase — in a fresh context, run the project's full test, build and lint targets into changes/<id>/evidence/ (test.log, build.log, lint.log), fix what fails within the iteration cap, take screenshots for UI changes, run the verifier, get the adversarial verdict, call the test gate and update the build PR. Then continue to /sdlc-deploy. Re-runnable.
argument-hint: [change id, e.g. 0001]
disable-model-invocation: true
allowed-tools: Bash(python "${CLAUDE_PLUGIN_ROOT}/plugin/state/cli.py" *), Bash(python "${CLAUDE_PLUGIN_ROOT}/plugin/gate/cli.py" *), Bash(python "${CLAUDE_PLUGIN_ROOT}/plugin/panel/cli.py" *), Bash(python "${CLAUDE_PLUGIN_ROOT}/plugin/evidence/collect.py" *), Bash(python "${CLAUDE_PLUGIN_ROOT}/plugin/pr/cli.py" *), Bash(git *), Bash(gh *), Read, Glob, Grep, Edit, Write, Agent
---

# /sdlc-test — the test phase

Source: build guide step 24 (composition: OPERATING_MODEL §4.1), step 13 (the feedback
loop, article p.27–29: "Run the tests, run the build, take the screenshot. Claude iterates
until the check passes"; evidence is "the literal output" of the toolchain), step 28 (the
test gate: evidence in `changes/<id>/evidence/` and the check run), step 25 (test-file lock).

This phase runs in a **fresh context**: a new session or a separate `claude -p` job, never
the one that wrote the code (article p.27: the verdict "is not colored by the assumptions
that produced the code"). Unattended: never ask the owner; a blocker parks.
One shell command per Bash call: an unattended run allows only an explicit list of
command prefixes (`git *`, `python *` and a few more, per phase: `plugin/ci/run_phase.py`
and this command's `allowed-tools`), Claude Code checks each part of a chained command
against that list on its own, and a chain with one part the list does not cover is denied
whole, so the step it carried is lost (the first `/sdlc-fix` run of 2026-09-23 lost its
final commit to `cd ... && python ...`).
Sub-agents run in the foreground: in CI the runner disables background tasks for the
session (`CLAUDE_CODE_DISABLE_BACKGROUND_TASKS`, plugin 0.3.3), and by hand, when the Agent
tool offers `run_in_background`, set it to false; read the report in the same turn, and
never end a turn to wait for a sub-agent's notification. A headless run has no next turn —
when the turn ends with a sub-agent still running, the CLI waits a fixed time (ten minutes
by default) and terminates the run, its work uncommitted and nothing after it done (change
0001's first build run on plugin 0.3.2, 2026-10-03: two background agents splitting the
docs were killed mid-write and the run ended with no gate; this rule since 0.3.3).

## 0. Preconditions
- Change id `$ARGUMENTS` (or the single change whose `status.phase` is `build` (`c` in an older change) with gate
  `passed`; stop and list otherwise).
- `python "${CLAUDE_PLUGIN_ROOT}/plugin/gate/preflight.py" --root "${CLAUDE_PROJECT_DIR}" --id <id> --phase test`:
  if `allow` is false, stop and report its `reasons` (a `parked: ...` reason is the
  owner's item). Never judge `status.yaml` yourself.
- `git fetch origin`, `git switch sdlc/<id>/build`, `git pull --ff-only origin sdlc/<id>/build`
  (`sdlc/<id>/c` for a change started before the names).
  The build, test and deploy phases share this branch and its PR (OPERATING_MODEL §8).
- `python "${CLAUDE_PLUGIN_ROOT}/plugin/gate/cli.py" start-run --root "${CLAUDE_PROJECT_DIR}" --id <id> --phase test`
- `python "${CLAUDE_PLUGIN_ROOT}/plugin/state/cli.py" set-phase --root "${CLAUDE_PROJECT_DIR}" --id <id> --phase test`
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
In CI (plugin 0.3.2, item 3b; issue #91) the summary says `"deferred": true` and
`all_green` is null: the runner marked this session (`SDLC_GATE_COMMANDS=runner`), the
writer ran no target and left a deferred mark as each log's first line, and the runner
runs the three targets once after this session, outside the sandbox — it writes their
output into the three logs, rewrites the test gate's `commands` and `evidence` entries and parks
the change on a red target. Then skip step 2 (there is nothing to read yet) and go on to
step 3; a target that fails after the session is the owner's change request through
`/sdlc-fix`. By hand, without the mark, the writer runs the targets as before.

## 2. Fix loop, bounded (article p.28: "two or three rounds is normal")
While `all_green` is false (never when the summary says `deferred`):
1. `python "${CLAUDE_PLUGIN_ROOT}/plugin/gate/cli.py" bump-iteration --root "${CLAUDE_PROJECT_DIR}" --id <id>`
   — if it reports the cap reached (`gate.max_iterations`, or
   `max_iterations_non_routine` when the verdict classed the plan non-routine), stop:
   go to step 5 and let the gate park with the partial evidence.
2. Read the failing log, fix the code (never the test in a fix-type change: the lock hook
   denies it and REVIEW.md rejects it; in a feature change a test may change only when
   `plan.md` Proof says so and `plan.md` is updated in the same commit).
3. Commit: `python "${CLAUDE_PLUGIN_ROOT}/plugin/state/cli.py" commit-phase --root "${CLAUDE_PROJECT_DIR}" --id <id> --phase test --message "test(<id>): fix <what>" --paths <files>`
4. Re-run step 1.

## 3. UI changes: screenshot loop against the mock (article p.27 step 2)
Only when `plan.md` Proof or `spec.md` Acceptance names a mock, screen or screenshot.
When `sdlc.yaml: commands.drive` is set (change 0004), capture nothing by hand: the runner's
drive wrote the build's screenshots into `changes/<id>-<slug>/evidence/proof/` after the build
session, and the gate checks the plan's `screenshot:` items there; open those images with the
Read tool, compare each with the mock, and write into `evidence/verifier.md` what you
compared and what differs (the verifier's test step does the same in its fresh context). Never
run the drive in this session: the runner runs it again after this one.
When the drive is empty: run the app (the project's run instructions or the `run` skill if
available), capture the screen into `changes/<id>-<slug>/evidence/screenshots/<name>.png`,
compare with the mock (the exported design mock lives in `changes/<id>-<slug>/mock/`, build
guide step 34; a plan that names a mock the folder does not hold is a mismatch to report, not
a reason to skip), adjust and repeat (bounded by the same iteration cap). Say in
`evidence/verifier.md` what was compared and what differs. Without a browser or screenshot
tool in this session, write `evidence/screenshots/README.md` saying so.

## 4. Verify in a fresh context (agent `sdlc:verifier`)
Delegate to `sdlc:verifier` with the change id. Store its report as
`changes/<id>-<slug>/evidence/verifier.md` (overwrite the build's report: this one covers the
full suite; in CI the verifier reads the build gate's `commands` entry and the logs instead
of running the targets — never an earlier round's `gate-test.json`; its brief says when). Commit
the evidence:
`commit-phase ... --phase test --message "test(<id>): evidence"` and push
(`git push origin sdlc/<id>/build`, or the change's `sdlc/<id>/c`).

## 5. Adversarial verdict and the test gate
The reviewer has no shell, so write the diff it reads first, in one call (`<base>` is the
default branch, `origin/<default>` after the fetch: the base the gate diffs against):
`git diff --stat --patch --output=changes/<id>-<slug>/evidence/diff-test.patch <base>...HEAD`,
then `git rev-parse HEAD` for the full sha. The diff file is evidence: it is committed with
the test gate's evidence commit below.
First run
`python "${CLAUDE_PLUGIN_ROOT}/plugin/gate/cli.py" risk-hits --root "${CLAUDE_PROJECT_DIR}" --id <id> --phase test`
and pass its `hits` (each item with where it matched) and its `brief` path in the delegation
prompt: the reviewer writes one brief per item there (decision 35: a hit is a line of the
close-look banner, never a park; its park on an item is the owner's and stays off the panel).
Delegate to `sdlc:adversarial-reviewer` (change id, phase `test`, project root, the full HEAD
sha, the path `changes/<id>-<slug>/evidence/diff-test.patch`, the risk-list hits), started with
`reviewer.alias`
from `python "${CLAUDE_PLUGIN_ROOT}/plugin/panel/cli.py" models --root "${CLAUDE_PROJECT_DIR}" --phase test`
as its model (`null`: pass none; the gate's `reviewer_model` check reads the model it ran
on, R7); it writes
`evidence/adversarial-review-test.json` for HEAD.

### Deferred review: the panel settles the judgment items (decision 21; build guide step 16a)
```
python "${CLAUDE_PLUGIN_ROOT}/plugin/panel/cli.py" items --root "${CLAUDE_PROJECT_DIR}" --id <id> --phase test
```
It prints the items the gate would park on that belong to the panel's fixed list (an open
flagged concern, a concern naming contradicting policies, the reviewer's `park`
verdict, an Important finding the run cannot fix, the verifier's "does not match the
plan"), which of them the ledger already decides, and under `parks` what stays the owner's
(the reviewer's park on a risk-list item, a guardrail file, a run limit, an infrastructure
failure; a risk-list hit itself parks nothing, decision 35). When `pending` is empty, go on
to the gate. Otherwise, for each pending item `n` in
order, three fresh contexts, each with the brief printed by
`python "${CLAUDE_PLUGIN_ROOT}/plugin/panel/cli.py" prompt --root "${CLAUDE_PROJECT_DIR}" --id <id> --phase test --item <n> --member <reviewer|advocate|conciliator>`:
1. **reviewer** — delegate to a general-purpose sub-agent with the `reviewer` brief; it
   writes `evidence/panel/test-<n>-reviewer.md`.
2. **devil's advocate** — delegate to `sdlc:adversarial-reviewer` with the `advocate`
   brief, started with `advocate.alias` from `panel/cli.py models --phase test` (pass it as the
   sub-agent's model: the per-invocation model wins, NOTES §11c; a panel on one model shares
   its blind spots), blind to the reviewer's file; it writes `evidence/panel/test-<n>-advocate.md`.
3. **conciliator** — delegate to a general-purpose sub-agent with the `conciliator` brief;
   it reads both files and writes `evidence/panel/test-<n>-conciliator.json`.
Then record it:
`python "${CLAUDE_PLUGIN_ROOT}/plugin/panel/cli.py" record --root "${CLAUDE_PROJECT_DIR}" --id <id> --phase test --item <n>`
— one panel call counts against `gate.max_panel_calls` (its own count, not a fix
iteration; exit 3 at the cap: stop the panel, the gate parks); it appends the line to
`evidence/decisions-test.json` (and the `.md` the owner reads), for a concern closes the item
in `spec.md` as `decided (by panel #<n>): <decision> — <concern>`, and commits the change
folder itself (`test(<id>): panel decision <n>`), so the decision is in HEAD before anyone
judges it. Do not reword a closed concern line: the gate matches it to the ledger by
`#<n>`. Apply what the decision asks beyond that (a `park` verdict decided `continue` needs
nothing more; one decided `park`: go straight to the gate, it parks; a fix the decision names is made now, `plan.md` in the same commit, committed
with `commit-phase ... --phase test --message "test(<id>): panel decision <n> applied"`).
After the last item, re-run step 5 for the new HEAD, once (a verdict never
outlives the diff it judged, and the diff file must be regenerated first); from then on
nothing is committed before the gate except the gate evidence, and the verdict file never
travels in a commit with content the reviewer did not see (the first deferred run,
2026-09-24, committed each verdict beside the content it did not judge, three times, and
needed four commits to land one). A `park` verdict with new reasons is a new item: run
`items` once more. The panel never decides a park item, never raises a limit, never
touches a guardrail file, and never asks the owner: the code owner reads "Decisions taken for
you" at the deploy gate and overturns any line with a review comment.

Then the gate:
`python "${CLAUDE_PLUGIN_ROOT}/plugin/gate/cli.py" check --root "${CLAUDE_PROJECT_DIR}" --id <id> --phase test`
(it requires `test.log`, `build.log`, `lint.log` and `verifier.md`, green — in CI the three
logs may carry the session's deferred mark, which the gate accepts until the runner's step
replaces them; exit 0 continue · 3 wait · 4 park). Commit:
`commit-phase ... --phase test --message "test(<id>): gate (test) evidence" --push`.

## 6. Update the build PR and the check run
```
python "${CLAUDE_PLUGIN_ROOT}/plugin/pr/cli.py" upsert --root "${CLAUDE_PROJECT_DIR}" --id <id> --phase test --check-run
```
It regenerates the ≤5-bullet summary (evidence status now filled from the logs), applies
the gate's label (`sdlc:needs-human` when parked) and,
when a token is available, posts the `sdlc/test` check run with the evidence summary
(build guide step 28).

## 7. Hand over
- `continue`: report "gate (test) passed → /sdlc-deploy <id>"; the workflow
  dispatches the review job itself. Do not run the deploy phase here.
- `park`: report the PR URL and the gate's "What I need from you" block.

Never edit `.claude/**`, `CLAUDE.md`, `REVIEW.md`, `sdlc.yaml`, `policies/**`, `intent.md`
or `spec.md`. Never weaken, skip or delete a test to get green. Never use bypass-permissions
mode. Never notify anyone.
