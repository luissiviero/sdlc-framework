# Change 0001 (2026-10-02, between sessions 14 and 15): the framework's first change through its own front door; one framework defect found; docs only, no bump

## Summary
- The owner asked what is left before 1.0.0, then chose R1's step 2 (the docs split) as the first roadmap work that cannot disturb the sample's live check. It became change **0001**, the first framework change through `changes/<id>-<slug>/`. The id came from `plugin/state/cli.py new-change`; the table discussed before it called this change "0002", because no other change existed yet.
- **The intent**: PR #86, merged by the owner. The draft's five open questions were settled before the merge:
  - `stale_after`: per file, the environment the facts were read under plus a 90-day backstop.
  - PROGRESS: one file per existing top-level heading.
  - Timing: the intent and the design run now; the design PR held until after `v1.0.0`. *[Amended the same day, second sitting, choice 139: the design PR is reviewed after 0.3.1 instead, 1.0.0 no longer sitting before the work.]*
  - `docs/BUILD_GUIDE.md`: out of scope.
  - The old paths: permanent stubs.
- **The design run** (run 36993453237, NOTES §24) wrote `spec.md` and `plan.md` on `sdlc/0001/b`. The adversarial reviewer answered `continue` (non-routine). Gate (b) parked on two checks:
  - `open_concerns`: two guesses the spec flagged, the file-name slugs and the index order.
  - `commands`: the test command failed.
  The design PR was refused by the repository setting. The owner enabled the setting, and PR #90 was opened from the branch with `sdlc:needs-human`.
- **The defect** behind the test failure is the framework's, not the design's. The gate runs the project's commands inside Claude Code's sandbox, where `Read(**/.env*)` makes a nested `.env*` unreadable. Any project whose tests read one (a `.env.example`, a fixture) fails the `commands` check. It is filed as issue #91.
- No file under `plugin/` or `template/` changed. No tag, no pin. The sample is untouched.

## The owner's choices (2026-10-02)
133. **The 1.0.0 road is not widened for issue #91.** It is recorded as the one known gap of 1.0.0 (ROADMAP, HANDOFF session 15) and fixed in **1.0.1**, the first change after the `v1.0.0` tag. The fix: the runner runs the gate's commands after the model's session, with a test. *[Amended the same day, second sitting, choice 137: the fix is session 15's, in 0.3.0, the first bump of the 0.3.x line; the reasons below stand.]*
    - Renaming this repository's fixture was not chosen: it hides the defect, and it may not work, because the rule matches at any depth.
    - Narrowing the deny rule was not chosen: it loosens decision 6.
    - Putting the fix in the 1.0.0 PR was not chosen: that PR takes the gaps the live detection finds.
134. **Change 0001's two flagged concerns are closed by rules, not names.**
    - Number-only file names: `docs/notes/<N>.md` and `docs/decisions/<N>.md`. Every citation already uses the number, so a renamed heading never leaves a stale file name.
    - PROGRESS records as `docs/progress/session-<N>[-sitting-<M>].md`, read from each heading, and `docs/progress/2026-09-28-workflow-comparison-study.md` for the one record that is not a session.
    - Each index in number order, one line per file, with the original heading as its description. Grouping by topic waits for R1's step 1 (tags).
    - These go to PR #90 as one "Request changes" review after 1.0.1, so the fix round re-runs gate (b) on the fixed framework (HANDOFF session 16).

## Read from the runs
| Read | Result |
|---|---|
| The sample's `CI` points | Eight at 08:30 UTC (NOTES §24); the sixteenth point is still 2026-10-10. |
| The design run 36993453237 | Phase (b) in 10 turns, 2.47 USD, no permission denial. 8 of gate (b)'s 10 checks passed (`design_scope`, `guardrails`, `risk_list`, `adversarial_review` among them). `open_concerns` and `commands` failed. `pr create` was refused. |
| The test command inside the gate | `78 failed, 943 passed, 272 errors`, every one a `Permission denied` on `tests/fixtures/sample-python-project/.env` (issue #91). |

## Checks (this documentation PR)
In the "Checks" section of the PR body.

---
