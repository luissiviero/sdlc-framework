# Progress — ROADMAP R67's proposal and its decision file, drafted (2026-10-25)

This session is lane B of wave 5, started by the central session `session_013TgyuTukXLjdZU3rmrgyRt` at the owner's request. It ran on branch `claude/r67-proposal-decision`, from `main` at `0ce7f6b` (#389, plugin 1.0.43). Documentation only: no file under `plugin/`, `template/` or `.github/`, no version. No numbered choice or note is taken; decision 41 is drafted for the owner's merge (`python tasks.py next-free` after `git fetch origin`: decision 41).

## What was written
1. **`docs/proposals/fix-round-fits-its-job.md`**: R67's failure measured against `main` (290 of 260 for a fix round at gate (deploy), 335 when check 12's re-check after the push also runs; check 12 also takes the build job to 290 of 260), the three options of the row in their forms (A1 measured, A2 fixed, A3 an `sdlc.yaml` key; B1 `if: always()` with the outcome read, B2 a `post` step, B3 a job of its own; C `timeout-minutes` at 355), the files, test plan and owner edits of each, and the recommendation: **A1 and B1 together, B1 in the five phase workflows, C not taken**, B1 built only after a live check of an `always()` step after a job timeout.
2. **`docs/decisions/41.md`**: the draft decision (amends 32; keeps 11, 29, 20 as amended by 31, and 7). Its frontmatter says `accepted`: the docs lint takes no other status for a decision without `amended_by` (`tasks.py`, `decision_problems`), so "proposed until the owner merges" is said in the file's reference line and its "Accepted" line instead; the owner's merge is the acceptance.
3. **`docs/decisions/32.md`**: `amended_by: [37, 41]` (the lint requires it once 41's heading says "amends 32") and one dated annotation beside the sentence on the raised limits (choice 126).
4. **`docs/decisions/index.md`**: regenerated with `python tasks.py decisions-index`.
5. **`docs/ROADMAP.md`**: one dated annotation in R67's Status cell; the status stays `proposed`.

## Checked
- Every file:line the proposal and decision 41 cite was opened on this branch and compared with the sentence (choice 241).
- GitHub facts: neither "an `always()` step runs after a `timeout-minutes` cancellation" nor "`runs.post` is for JavaScript and container actions only" was tried live. The first is the open R18 live check; the proposal makes it B1's precondition. The second was read on GitHub's "Metadata syntax" page in a web search on 2026-10-25, not re-read in full.

## The fresh-context review
A fresh-context sub-agent reviewed the proposal and decision 41 against the code (report only). It confirmed the citations, the arithmetic (290, 335, A1's 245 with and without a drive) and the order (the judge before the commit, check 12 after), and found five blocking and eight optional points. All were taken:
1. The gate's wall-clock check recomputes the drive's minutes from `sdlc.yaml` and cannot recompute a measured figure: A1 now passes it through `session_env` to `start-run`'s run record.
2. Counting the measured minutes in `build_caps_minutes_needed` would refuse the build caps to every round whose default branch moved: A1 leaves that function as it is, and says why.
3. The steps at `sdlc-fix.yml:294-308` are R18's triage steps, not park steps; the runner parks from inside its own step.
4. B1's step runs only after the triage steps' fresh framework checkout and project check, never on a framework the session could reach.
5. B1 is specified per workflow: the state `park_unfinished_round` needs is saved to `$RUNNER_TEMP` before the session; design, build and test park as the runner's timeout does; a cancelled review pass stays red (decision 11's note).
6. to 13. Optional, taken: check 12's reach (the test and deploy jobs' sums), the grace's own line (`:323`), "before the session" for `build_caps_refusal`, `docs/notes/45.md` for "NOTES §45", B2's container form, the 15-minute margin, no re-run on a cancel (decision 29), and R18's "Failed runs" row under "Decisions it touches".

## Port list
This PR touches no file under `plugin/` or the workflow templates.

## Proposed edits for the owner
None in a guardrail file. Decision 41's choice is the PR's "What I need from you".
