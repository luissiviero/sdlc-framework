---
description: Phase (c) build — implement the merged spec+plan on sdlc/<id>/c under the guardrail hooks, after the preflight allows it. Fix-type changes write the reproducing test first. Then code-simplifier, verifier (evidence/verifier.md), adversarial verdict, gate (c), and the build PR (draft) with the generated summary. Standard/Lite: continue to /sdlc-test; Full: wait for sdlc:c-approved. Re-runnable.
argument-hint: [change id, e.g. 0001]
disable-model-invocation: true
allowed-tools: Bash(python "${CLAUDE_PLUGIN_ROOT}/plugin/state/cli.py" *), Bash(python "${CLAUDE_PLUGIN_ROOT}/plugin/gate/cli.py" *), Bash(python "${CLAUDE_PLUGIN_ROOT}/plugin/gate/preflight.py" *), Bash(python "${CLAUDE_PLUGIN_ROOT}/plugin/evidence/collect.py" *), Bash(python "${CLAUDE_PLUGIN_ROOT}/plugin/pr/cli.py" *), Bash(git *), Bash(gh *), Read, Glob, Grep, Edit, Write, Agent
---

# /sdlc-build — phase (c)

Source: build guide step 24 (composition: OPERATING_MODEL §4.1), step 16 (plan mode:
"Accept the plan and let Claude implement", article p.16 step 6), step 17 (code simplifier
and verifier, p.25), step 18 (preflight), step 25 (failing test first, p.28 step 4), step
27 (gate (c)), decision 2 (this is the first run with edit tools on source).

Unattended run: never ask the owner anything; a blocker becomes a parked reason. The
project's own commands and hooks are the guardrails: the protected-path hook denies
`.claude/**`, `CLAUDE.md`, `REVIEW.md`, `sdlc.yaml`; the plan-sync hook denies a commit that
changes source without `plan.md`; the test-file lock denies test edits in a fix after the
reproducing test is committed. Never work around a hook; if it blocks the plan, park.

## 0. Preconditions and preflight (build guide step 18)
- `sdlc.yaml` exists; the change id is `$ARGUMENTS` (or the single change whose
  `status.phase` is `b` with gate `passed`; stop and list candidates otherwise).
- `python "${CLAUDE_PLUGIN_ROOT}/plugin/state/cli.py" show --root "${CLAUDE_PROJECT_DIR}" --id <id>`:
  stop if `parked_reason` is set.
- `python "${CLAUDE_PLUGIN_ROOT}/plugin/gate/preflight.py" --root "${CLAUDE_PROJECT_DIR}" --id <id>`.
  Read `allow`, `permission_mode`, `reasons` and `change.iteration_cap`. If `allow` is
  false: do not implement anything; park with the reasons
  (`state/cli.py park --root ... --id <id> --reason "preflight: <reasons>"`) and report.
  The permission mode it prints is the one the unattended job runs under (`acceptEdits`
  at most; `bypassPermissions` never); by hand the session's own mode applies.
- The three `sdlc.yaml` commands (`build`, `test`, `lint`) must exist; the gate refuses (c)
  without them (build guide step 14). Preflight already checked the test target.

## 1. Branch and run registration
- Default branch as in `/sdlc-design` step 0. `git fetch origin`.
- Start point: the default branch when gate (b) was the owner's merge (Standard, Full);
  `sdlc/<id>/b` in the Lite profile (spec+plan were committed there). First run:
  `git switch -c sdlc/<id>/c <start point>`. Re-run: `git switch sdlc/<id>/c` and
  `git pull --ff-only origin sdlc/<id>/c`; the existing diff and the PR's unresolved review
  comments are the starting point (see `/sdlc-fix` for the change-request loop).
- `python "${CLAUDE_PLUGIN_ROOT}/plugin/gate/cli.py" start-run --root "${CLAUDE_PROJECT_DIR}" --id <id> --phase c`
- `python "${CLAUDE_PLUGIN_ROOT}/plugin/state/cli.py" set-phase --root "${CLAUDE_PROJECT_DIR}" --id <id> --phase c`

## 2. Read the approved plan
Read `changes/<id>-<slug>/intent.md`, `spec.md`, `plan.md` and `status.yaml`. The plan is
the contract: "Files that change", "Order of work", "Proof". Do not redesign; if the plan
cannot be followed, update `plan.md` in the same commit as the departure and say why under
Risks (article p.16 step 7). Load the policy skills (`coding-standards`,
`security-baseline`, `ux-conventions`, `data-conventions`, `definition-of-done`).

## 3. Fix-type change: the reproducing test first (build guide step 25, article p.28 step 4)
When `status.change_type` is `fix`:
1. Write the test that `plan.md` Proof names, so that it fails for the reason the intent
   describes. Run only that test and confirm it fails; paste the failing output into
   `changes/<id>-<slug>/evidence/failing-test.log`.
2. Commit it together with `plan.md`:
   `python "${CLAUDE_PLUGIN_ROOT}/plugin/state/cli.py" commit-phase --root "${CLAUDE_PROJECT_DIR}" --id <id> --phase c --message "fix(<id>): reproducing test" --paths <test file>`
3. Lock the test files for the rest of (c) and (d):
   `python "${CLAUDE_PLUGIN_ROOT}/plugin/state/cli.py" lock-tests --root "${CLAUDE_PROJECT_DIR}" --id <id>`
   From here the hook denies any edit under the test directories; the fix must make the
   test pass without touching it. If the test itself was wrong, park and say so.

## 4. Implement, one plan step per commit (article p.16 step 6)
Follow "Order of work". After each step run the project's `test` command for the tests the
step touches (the full suite is phase (d)). Commit with
`python "${CLAUDE_PLUGIN_ROOT}/plugin/state/cli.py" commit-phase --root "${CLAUDE_PROJECT_DIR}" --id <id> --phase c --message "build(<id>): <step>" --paths <files>`
— it commits the change folder plus the paths you name (the plan-sync hook expects
`plan.md` in the same commit whenever source changed and the plan needed an update).
Never edit `intent.md` or `spec.md` in this phase; never touch a guardrail file. No new
dependency without the plan naming it.

## 5. Simplify (agent `sdlc:code-simplifier`, article p.25 step 4)
When every plan step is done and its tests pass, delegate to `sdlc:code-simplifier` with
the list of files the change touched. It reports simplifications; apply the ones that keep
behaviour and tests unchanged, re-run the touched tests, commit as
`build(<id>): simplify`.

## 6. Verify in a fresh context (agent `sdlc:verifier`, article p.25–27)
Delegate to `sdlc:verifier` with the change id: it runs the changed behaviour and the two
nearest neighbouring flows and reports. Store its report verbatim as
`changes/<id>-<slug>/evidence/verifier.md`. If it reports behaviour that does not match
`plan.md`, fix it (step 4 again, bounded by the iteration cap from the preflight: run
`python "${CLAUDE_PLUGIN_ROOT}/plugin/state/cli.py" bump-iteration --root "${CLAUDE_PROJECT_DIR}" --id <id>`
per round; the gate parks at the cap), then re-run the verifier. Commit the evidence:
`commit-phase ... --phase c --message "build(<id>): verifier evidence"`.
Push: `git push -u origin sdlc/<id>/c`.

## 7. Adversarial verdict and gate (c) (build guide steps 16–17, 27)
Delegate to `sdlc:adversarial-reviewer` with the change id, phase `c`, the project root
and the default branch; it writes `evidence/adversarial-review-c.json` for HEAD. Then:
`python "${CLAUDE_PLUGIN_ROOT}/plugin/gate/cli.py" check --root "${CLAUDE_PROJECT_DIR}" --id <id> --phase c`
(exit 0 continue · 3 wait · 4 park; it writes `status.yaml` and `evidence/gate-c.json`).
Commit the evidence: `commit-phase ... --phase c --message "build(<id>): gate (c) evidence" --push`.

## 8. The build PR (article p.34: one PR from build to merge; build guide step 27a)
Open or update the build PR — draft, base the default branch, head `sdlc/<id>/c`, title
`build(<id>): <title>` — with the generated description and the label the gate printed:
```
python "${CLAUDE_PLUGIN_ROOT}/plugin/pr/cli.py" upsert --root "${CLAUDE_PROJECT_DIR}" --id <id> --phase c --draft
```
It renders the ≤5-bullet summary from `status.yaml`, `evidence/gate-c.json`, the verifier
report and the plan-vs-diff check, applies the label (`sdlc:c-ready` in the Full profile,
`sdlc:needs-human` when parked, none otherwise), and uses `gh`, then the GitHub REST API
with `GITHUB_TOKEN`/`GH_TOKEN`, then prints the compare URL and the body for the owner to
paste. Do not retry with other means.

## 9. Hand over
- `continue` (Standard, Lite): report "gate (c) passed → /sdlc-test <id>". In the
  merge-triggered workflow the job dispatches the test workflow itself. Do not run (d) here.
- `wait` (Full): report the PR URL and "gate (c): approving review + `sdlc:c-approved`
  starts the test phase; review comments are the change request (`/sdlc-fix`)".
- `park`: report the PR URL and the gate's "What I need from you" block.

Never edit `.claude/**`, `CLAUDE.md`, `REVIEW.md`, `sdlc.yaml` or `intent.md`. Never use
bypass-permissions mode. Never notify anyone.
