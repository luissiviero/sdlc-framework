# Progress — session 25 (2026-10-12 to 2026-10-13): the consolidation session — both repositories read against the docs, one open-items table, the owner's seven decisions; change 0002 driven from its turn-capped (e) round to its merge and `v0.3.7`; `HANDOFF.md` rewritten as the single restart point; no bump in this PR

This session ran on the owner's consolidation prompt of 2026-10-12 (part 1: where things stand, read-only; part 2, after approval: one docs-only PR that makes `HANDOFF.md` the single restart point). Between the two parts it watched PR #152 on the owner's request and gave the owner each review text. Every fact below is in NOTES §39 with its run URL, file or command.

## Summary
- **Part 1, the read** (NOTES §39): `main` was `71e4da7` at plugin 0.3.6, `v0.3.6` the newest tag, root pin 0.3.6, the sample pinned at 0.2.30. The 1.0.0 road had stalled at its dated steps: **no provocation PR was opened on 2026-10-10** and the 2026-10-11 detect run logged tier 0 (`forced: false`, `rule: null`). The sample had seventeen complete days of points, so the baseline is ready. Open on the framework: PR #152 (change 0002, parked at (e)), #153 and #156; on the sample: #55; issues: the two digests only. All issues named in the prompt (#66, #67, #68, #71, #72, #91) were closed on 2026-10-02. The seven sessions of 2026-10-08/09 had all ended cleanly. The 26 framework branches "ahead of main" are merged history from before `main`'s restart on 2026-09-27.
- **The owner's acts during the session**: merged #153 and #156 (07:46 UTC); posted four reviews on PR #152 and applied `sdlc:reset-iterations` twice; approved the final checks; merged PR #152 at 00:31 UTC on 2026-10-13. `sdlc-tag.yml` tagged **`v0.3.7`** on `9783278`. The root pin stays at 0.3.6 (the pin rule).
- **PR #152's last day** (NOTES §39): four fix rounds, each started by a narrow review this session wrote and reproduced first — the lesson and eval case (then a cap park on the literal case list), the one-line test fix (then a lint park from the root `lessons/` folder), the lint fix (gate (e) passed), and the Windows path fix in three tests (the round's review pass also fixed chained `git -C`). Change 0002 cost **84.69 USD** over 18 recorded runs.
- **Part 2, this PR**: `HANDOFF.md` rewritten as the one brief every next session starts from (preconditions, the state, the open-items table, the ordered next steps, the owner's acts, the rules); session 24's record moved unchanged to `docs/progress/session-24.md` with its index line; NOTES §39 with its index line; `docs/ROADMAP.md` annotated beside rows 9, 10 and R7. No file under `plugin/` or `template/` changed: no bump, no tag.
- **Port list (choice 138):** this PR touches nothing under `plugin/detect/`, `plugin/ci/run_phase.py` or the detect, runbook and fix workflow templates. Change 0002 (PR #152, now in `v0.3.7`) touched `plugin/ci/run_phase.py` (`ci_settings_file`, `_deny_write_entries`): it is on the port list for item 11.

## The owner's decisions (2026-10-13, continuing session 24's numbering)
176. **The provocation is on 2026-10-13**, before 23:59 UTC; the read is on 2026-10-14. The baseline has had more than sixteen points since 2026-10-10, so only the provocation sets the date.
177. **The 26 stale framework branches are deleted.** Each was read: 24 merged as PRs, one closed unmerged (#46), one with its content on `main`. The session's delete was refused by the auto-mode classifier; the owner deletes them (Left).
178. **The 16 stale sample branches stay until after the 1.0.0 read** (the freeze, choice 138).
179. **Sample PRs #55, #56 and #57 stay untouched until after the 1.0.0 read**, then triaged. Their metric is the scan's, not the CI failure rate, so they do not block the detection.
180. **The runs PR comes before R7, as 0.3.8**; R7 becomes 0.3.9 and every later number shifts by one. It amends the order of 2026-10-09 (0002 → R7 → R5 → R6 → R10 → the gaps), which stays otherwise. The runs PR carries: the turn cap as a hard park with a higher default for (c), the label race, a re-run keeping the capped run's wall clock, the park text at (e) that sends the owner to a dispatch that refuses, and the counter that a round bumps before its own review pass. *[2026-10-14, the item-11 record (`docs/PROGRESS.md`, choice 184): the numbers are not kept. 0.3.8 went to PR #194 and the item-11 PR is 1.0.0; no number is reserved after 1.0.0, and each PR that changes `plugin/` or `template/` takes the next free patch number when it is the next to merge. The order of the work stands.]*
181. **The study's next proposal batch (T17, T19, T27, T28) waits until after the 1.0.0 read.**
182. **Part 2 is written now**, after `v0.3.7`.

## Checks (this repository)
On this PR's tree, chained on the exit codes with `set -o pipefail` (Claude Code 2.1.296, Python 3.13.16); the output is pasted in the pull request body.

## Known gaps (new, for the 0.3.8 runs PR unless the owner says otherwise)
- **A deploy dispatch at (e) skips**: gate (e)'s park text offers "a workflow_dispatch with the change id", but the deploy workflow only moves a change from (d) (`{"skipped": "change 0002 is at phase e, not d"}`). The text should name the fix round (a review) as the only restart.
- **A turn-capped fix round hides the gate's real park**: the runner overwrites `status.yaml`'s `parked_reason` with "commands: deferred to the runner and never run: claude exited 1"; the round's own `lesson_and_eval` reason was visible only in the job log.
- **A round bumps the counter before its review pass**, so one Important finding from that pass crosses the cap at 1 of 2 (session 21's "double bump-iteration" gap, seen again).
- **The gate's `lint` target misses formatting**: `ruff format --check .` failures reach `Framework checks` only (the guardrail row below).
- **The root `lessons/` folder changes ruff's import grouping**: fixed in `pyproject.toml` by change 0002's last round; any other first-party package named like a root folder would do the same.
- **Tests that put a `WindowsPath` into a Bash command string are not portable**: fixed in change 0002's three tests with `as_posix()`; the rule belongs in the coding-standards skill.
- **`claude_md_first_time_lines` proposed a CLAUDE.md line from a one-off test failure** again (session 21's gap).
- Carried unchanged from session 24: the label race, the turn cap, the re-run's wall clock, the reviewer's `at` stamp, the runner's post-session check of `framework/` and the guardrail files.

## The guardrail row (the owner's edit)
| Link | Row | What is there | What it must become |
|---|---|---|---|
| [sdlc.yaml](https://github.com/luissiviero/sdlc-framework/blob/main/sdlc.yaml#L19) | 19 | `lint: "python -m ruff check ."` | `lint: "python -m ruff check . && python -m ruff format --check ."`, once a session has verified that the runner's command step accepts `&&` (else a second lint entry or a `tasks.py` target) |

## Left
- **The owner**: delete the 26 framework branches listed in `HANDOFF.md` ("What the owner does"); open the provocation PR on the sample on 2026-10-13; the guardrail row above when a session has checked `&&`.
- **The next session**: the item-11 read on 2026-10-14 (`HANDOFF.md`, step 2), then the sandbox proof, then the 0.3.8 runs PR.
