# Progress — the fast lane's recovery PR: a pushed `fast_lane.b` always has a build behind it, as plugin **1.0.11**, and the owner's choice 232 (2026-10-19)

This session ran on branch `ccr-9e7c0e1f-wgcq4m`, from the owner's questions of 2026-10-19 on the fast lane (decision 30) and the one state that needed the owner's hand. The previous record (1.0.10, choices 228 to 231) is now `docs/progress/2026-10-19-1.0.10-and-choices-228-231.md`.

## The gap
The design run on the fast lane recorded `status.yaml: fast_lane.b`, pushed it, opened the design PR and then dispatched `sdlc-build.yml`. A run that failed after the push and before the dispatch (GitHub refused the design PR, or refused the dispatch) left a pushed `fast_lane.b` with no build behind it: every later design event skipped as "design done" (`carried_forward`), and nothing told the owner. `docs/OPERATING_MODEL.md` §4 recorded it as the one state that needed the owner's by-hand dispatch of SDLC build. It was a documented limit, not a decision: no decision, proposal or test covered it.

## Summary
- **A design PR GitHub refuses to open does not hold the build back.** On the fast lane the build's own check (`stacked_refusal`) and the hand-over now run once the record is pushed, whether or not the design PR exists; the build PR carries the intent, spec and plan anyway. The run still ends red ("no pull request carries this phase's result"), and its log says the build was dispatched.
- **A build dispatch GitHub refuses puts the design back at (b).** `fast_lane.b` is dropped and the gate record goes back to the ordinary `wait` with `sdlc:b-ready` (the same demotion as the build's-check refusal, now one helper, `fast_lane_wait`), pushed, and the design PR is updated, which requests the owner's review (decision 31). The owner's merge starts the build the usual way. If that demotion itself cannot be pushed, the run ends red and says to dispatch SDLC build with the change id: the one state left that needs the owner's hand.
- **The build closes the intent PR as `sdlc:superseded` when no design PR was opened** (`supersede_earlier_pr` falls back to `fast_lane.a.pr`, with its head check, so the owner's later pushes stay open).
- **Not built (item 4 of the proposal):** a reopened intent PR or a by-hand design dispatch that resumes the build. With the three changes above it is needed only when the demotion's push fails too.
- **The build reads the owner's close of the intent PR when no design PR was opened** (`earlier_pr_closed` at (c) falls back to `fast_lane.a.pr`): a close without the label while the build runs abandons the change (decision 25), as a design PR's close does.
- **Tests:** new cases in `tests/test_fast_lane.py` (section 8b, and the build's-check refusal parametrized with a demotion that is not pushed); the first four fail on the 1.0.10 runner and pass on this one.
- **One existing test changed, by the owner's answer of 2026-10-19:** `tests/test_ci_end_to_end.py::test_a_routine_design_takes_the_fast_lane_to_the_build` runs the real design step with no `GITHUB_TOKEN` (its PR calls take the fake `gh`), so its dispatch has no route. It asserted `continue` while that dispatch failed, which is the stuck state itself; it now asserts the wait at (b) with `fast_lane.b` dropped on the pushed branch. The dispatched path stays pinned in `tests/test_fast_lane.py`.
- **Review:** one independent reviewer, its findings verified by the session. No blocking finding. Fixed: a demotion that was not pushed lost its message when the design PR had failed too; the message told the owner to dispatch the build where only the design PR's merge works (the build's-check refusal); the build missed the owner's close of the intent PR (above); the wording "GitHub refuses" where a dispatch with no answer counts the same, and "supersedes" where a moved head is left open; four untested paths. Not changed: `--no-dispatch` still leaves a pushed `fast_lane.b` with nothing dispatched, because the flag sends nothing on purpose and no workflow passes it; `docs/OPERATING_MODEL.md` now says "in a CI run".

## The owner's decisions (2026-10-19)
232. **The fast lane's recovery is built now, as plugin 1.0.11, not as a ROADMAP candidate** (the session's recommendation; the owner, "Go"): items 1 to 3 of the session's proposal, item 4 left out. Item 2 is built as the ordinary `wait` at (b) rather than a park with `sdlc:needs-human`: the same review request reaches the owner, the act is the usual merge, and no un-park label is needed (a parked change would refuse the build). *To confirm in the PR.* *[2026-10-19, the owner: confirmed after #242 merged ("I accept it as your recommendation"); the wait at (b) stays. Relayed by session `ccr-9e7c0e1f-wgcq4m`, annotated by session `ccr-6281cac2-hdaob7`.]*

## Proposed edits for the owner
None: no guardrail line changes in 1.0.11.

## Left
- **Not verified live:** the three paths need a GitHub failure at the wrong moment, so the tests are their proof. The sample's next fast-lane change shows the ordinary path still works.
- **Known limits:**
  - a dispatch GitHub accepted but reported as failed (a lost answer) demotes a design whose build may be running; the build PR still supersedes the design PR, and a later merge of the design PR starts no second build while the build PR is open (`rerun_reason`, not tested for this path);
  - the demotion's own push failing still needs the by-hand dispatch (above).
- **The port list** (HANDOFF rules): this PR touches `plugin/ci/run_phase.py`.

## Checks (this repository)
On the final head, after `python -m pip install -e ".[dev]"`, chained with `set -o pipefail`: the four commands of `HANDOFF.md`'s standing precondition 1. Their output is in the PR.
