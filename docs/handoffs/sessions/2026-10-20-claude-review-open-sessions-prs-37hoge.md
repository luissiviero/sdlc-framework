# Session of 2026-10-20 on branch `claude/review-open-sessions-prs-37hoge`: the merge order of the open sessions' PRs, then the sandbox proof, the security findings registered, two coverage tests

**Builds on:**
- `docs/handoffs/sessions/2026-10-20-ccr-e4e43fa6-d3y9ly.md` (choice 239, PR #254), the newest file on `main` at `8546217` when this part of the session started.

No other session file is newer (verified, `ls docs/handoffs/sessions/` on `main` at `8546217`). The sessions that ran in parallel on 2026-10-20 (#255, #256, #258, #259, #260, #262, #263, #264, #265) wrote report files under `docs/reviews/`, not session files; their open items are in "Every open item" below.

The owner's task, in two parts. First, a coordination pass: review every open session and its PR, and give the order of merges and edits that avoids conflicts; the owner then did the merges, and this session verified each on `main`, unblocked the two sessions that were waiting (#254's and #256's) and resolved the sample's dismissal conflict (sample #81). Second, "for the ones you agree with and that don't depend on me: start implementation": this PR is that second part.

## Where the project stands
- **`main` is at `8546217`** (verified, `git log -1 origin/main`), with #254, #255, #256, #257, #258, #259, #260 and #261 merged on 2026-10-20. It is on plugin **1.0.14** (verified, `.claude-plugin/plugin.json`), with `v1.0.14` on `53f9714` and its release page (verified, `git rev-list -n1 v1.0.14`, `releases/latest`). Framework checks passed on every one of those merge commits (verified, the runs of workflow `framework-checks.yml` on `main`).
- **The sample** (`luissiviero/sdlc-sample-python`) is at `62b752c`: its pin is **1.0.14** and its `sdlc.yaml` carries `panel_advocate_model: claude-fable-5-1`, `adversarial_model: claude-opus-5-5` and `session_model: {default: claude-opus-5-5, b: claude-fable-5-1}` (the owner's #83 and #84; verified, `git show origin/main:sdlc.yaml`). `panel/cli.py models` on 1.0.14 reports no conflict in any phase (verified in this session: at (b) the session on `claude-fable-5-1`, the reviewer and the advocate on `claude-opus-5-5`; at (c) to (e) the advocate on `claude-fable-5-1`). `changes/.dismissed.json` holds the four scan dismissals (0004, 0006, 0011, 0012; verified). #55 stays open, labelled `schedule`.
- **Open framework PRs** at 03:30 UTC: #173 (intent 0004, waits for R14's turn, choice 211), #262 (three proposal frontmatters quoted; R58's check 7), #263 (the decisions audit, report only), #264 (the R51 race analysis, report only), #265 (R45's names against the article, report only), and this one. Each of #262 to #265 merges cleanly onto `8546217` (verified, `git merge-tree`). #256's session was building R58 when this file was written.
- **This PR** carries four things, each a commit of its own:
  1. **The sandbox proof's case** (ROADMAP R44, point 1; the owner's item 15 of 2026-10-08 on PR #144; choices 173 and 187): `evals/cases/0006-sandbox-write-deny/`, and `.github/workflows/framework-evals.yml` gains the phase jobs' runner setup step (`python plugin/ci/runner_setup.py`) before the suite. The `Framework evals` run on this PR is the live proof; its result is to be recorded in a note (the next free number is 52) and in R44's row, by the session that reads the run. Until then the sandbox lines of every record stay "not verified live". No plugin version bump: nothing under `plugin/` or `template/` changed.
  2. **The security review's findings registered** (`docs/reviews/2026-10-19-plugin-security-review.md`, merged as #259 with no row in ROADMAP): I2, I3 and M9 as candidate **R59** (`docs/proposals/gate-diff-and-evidence-hardening.md`, proposed, no order); I1, I4, M1, M5 and N6 proposed as additions to R44's scope and I6 for after the trial, on R44's row; I5 on R3's row (and R41 named); the dismissal-store conflict of sample #81/#82 on R23's row. The owner has decided none of these.
  3. **Two coverage gaps closed** (`docs/reviews/2026-10-19-plugin-test-coverage.md`, gaps 1 and 3): `tests/test_policy.py` (new: `is_automation`'s App-email suffix branch, the custom list, `automation_identity`'s fallbacks) and `tests/test_yamlish.py` (hand-written `sdlc.yaml` shapes against PyYAML, the pins as strings, the YAML 1.1 shapes read as 1.2 strings on purpose, a misread file reaching the protected-path hook as a deny). Gaps 2, 4 and 5 are open below.
  4. This file.

## Preconditions of the moment
- The standing ones are in `HANDOFF.md`; `python tasks.py docs-lint` is green on this head (0 failures; the four permanent lines for notes 46 to 49).
- The next free patch number is 1.0.15; R56 takes it when it merges (choice 184; carried from the e4a1d6f8 file). R59, if accepted, takes the next free one at its merge.
- The next free decision file is 35 (carried). The next free note is 52 (verified, `ls docs/notes/`).
- Three proposal frontmatters on `main` do not parse as YAML (`claude-md-standing-pr.md`, `learning-from-incidents.md`, `reviewer-tuning.md`); #262 fixes them. This PR's new proposal parses (verified with PyYAML).

## Next steps, in order
1. **The owner merges #262, #263, #264 and #265** (report-only or docs-only; each merges cleanly), and this PR once its `Framework checks` and `Framework evals` runs are green.
2. **The sandbox proof's reading**: the first `Framework evals` run on this PR's head with the setup step. Green: case 0006 passed, `denyWrite` holds on a runner; a note records it, R44's row and the "today" of `docs/proposals/sandbox-closes-gaps.md` are annotated, and the root pin may move straight to the newest tag (choice 187, the owner's edit). Red on check 2 (`docs/policy.md` changed): the sandbox did not hold or did not start (the template's `failIfUnavailable: false` runs the command unconfined), and the job log says which. Red on check 1: the agent declined or the sandbox denied an ordinary write; read the run.
3. **R7's first live reading on 1.0.14**: one small sample change (carried from the e4a1d6f8 file; the pin and the rows are in since #83 and #84, so only the change is left; the R7 session's estimate for one change on Opus and Fable was about 12 to 20 USD). It also counts as "the sample's next change" that R56 waits for.
4. **The owner decides** on R59 and on the additions to R44 (this PR's registrations), and on R30's place, the "park at once" candidate and the runs PR's open items (carried).
5. **Free beside the queue:** the decision files of R24 and R22 (ranks 8 and 9), each in a documentation PR of its own, numbered 35 and 36 before they are written (carried); R58's build (#256's session, in progress).
6. **R51** (rank 10) builds on `gitops.remembered`, carries the review's six `gitops` notes (ROADMAP R51) and reads #264's fourteen missing checks before its design.
7. **R47's push, live:** the owner's two GitHub Mobile settings, then the next waiting PR (carried).
8. Then the ROADMAP candidates, in its Order column; #173 at R14's turn (choice 211).

## Every open item
| Item | Where | What is left | Who acts | Blocks 1.0.0 |
|---|---|---|---|---|
| This PR | framework | `Framework checks` and `Framework evals` green on the final head, then the owner's merge | owner | no |
| The sandbox proof's result | this PR's `Framework evals` run | A note (52) and R44's annotation from the run's report artifact; `docs/proposals/sandbox-closes-gaps.md`'s "today" corrected (N6) | the next session | no |
| The template sandbox block | `docs/progress/2026-10-19-r7-reviewer-on-latest-opus-1.0.14.md`, step 1, item 13 | Waits on the sandbox proof's reading (carried) | the session after the proof | no |
| The root pin | root `sdlc.yaml` (0.3.6) | Moves to the newest tag once the proof passes (choice 187); the owner's edit | owner | no |
| R59 and the additions to R44 | ROADMAP R59, R44, R3, R23 | The owner's decision; R59 then needs its order | owner | no |
| #262, #263, #264, #265 | framework | The owner's merges; #263's weakened decisions (1, 4, 16, 29) are its reading, nothing is reopened | owner | no |
| R58's build | #256's session | In progress when this file was written; a docs-and-tasks PR outside the ranks | that session; owner merges | no |
| R7's first live reading | NOTES §51; the R7 record, "Left" | One sample change (step 3); the pin and the rows are in | owner starts it | no |
| Coverage gaps 2, 4 and 5 | `docs/reviews/2026-10-19-plugin-test-coverage.md` | `ci/runner_setup.py`'s install path with faked `shutil.which` and `subprocess.run`; `hooks/format_on_edit.py`'s three untested outcomes; the skill check scripts' `DANGEROUS` entries one by one | the next change to each module | no |
| Line coverage | the same report | Not measured; needs subprocess coverage to mean anything. Left out on purpose | nobody, unless asked | no |
| R30 before the trial? | ROADMAP R30 (rank 28); the decision table of 2026-10-15 | The owner's call (carried) | owner | no |
| Fix rounds spent on findings no session can fix ("park at once") | NOTES §49 | The owner's call (carried) | owner | no |
| The runs PR's open items | the R7 record, step 1, items 1–6, 9, 10 and 12 | Whether and where to place them (carried) | owner | no |
| The external review's retirement count | `docs/proposals/reviewer-on-opus.md` | Starts with the first change on 1.0.14 (carried) | the sessions that read changes | no |
| R47's push to the phone; R47 on a draft PR | NOTES §50 | The owner's two settings; the next note on R47 annotates NOTES §49's bullet (carried) | owner; a later change | no |
| The fast-lane intent PR's "What needs you" line | ROADMAP R54 | Rides with R54 (carried) | R54's session | no |
| `gitops.remembered`'s six notes; #264's fourteen checks | ROADMAP R51; `docs/reviews/2026-10-20-r51-race-analysis.md` | Ride with R51 | R51's session | no |
| The R7 leftovers | the R7 record, "The independent review" | A runner refusal before the session starts; `plugin/evals/run.py` reads `SDLC_MODEL` only. Left out on purpose, not scheduled | nobody, unless asked | no |
| The 1.0.10 paths; the 25 requests of one end-to-end test; fixture builders not converted; R49's `/proc` claim; the intent PR's cut open question; R50's trigger; the known limits of 1.0.11, 1.0.10, R47, R48, R49, R17 and R46; the fork token of an `issue_comment` run; gap 8's second half; "Small defects", "E2" and R28's cost; the baseline's R2 line; the artifact "LLM Wiki Crosswalk"; R10 not verified live and the rest of the d96dbb91 table | as in the e4e43fa6 file | Carried unchanged, not re-verified | as there | no |
| The reminder for the PC | `trig_01Dbv76g2tPAEdw1wPC6b4Gf` | Fires 2026-10-21 11:55 UTC (carried, not re-verified) | that session delivers; owner acts | no |

Done, dropped:
- "#254" of the e4e43fa6 file: merged as `63d2710`. #256 merged as `8546217`. The sample's dismissal PRs: #82 merged (`0e8ae49`), #81 merged (`6c69462`) after this session merged the default branch into `sdlc/0012/dismiss` keeping both entries.
- "For R7's live reading, move the sample's pin to 1.0.14 and add its optional rows": done by the owner, sample #83 and #84.
- "The sandbox proof, the next queue item": its case and workflow step are this PR; its reading is open item 2.
- The security review's findings had no ROADMAP row: registered in this PR (owner decides).

## What the owner does
| When | Act |
|---|---|
| Now | Merge #262, #263, #264 and #265; merge this PR once `Framework checks` and `Framework evals` are green on its final head. |
| After the evals run | Read the proof's verdict (step 2); if green, move the root `sdlc.yaml` pin to the newest tag (choice 187). |
| When convenient | Decide R59 and R44's proposed additions (ROADMAP R59, R44); say whether R30 moves before the trial; decide the "park at once" candidate; say whether the runs PR's open items become a ROADMAP candidate (carried). |
| When convenient | Start one small sample change for R7's live reading (step 3). |
| Now, if not done | GitHub Mobile's "Review Requested" push type and the GitHub Mobile tick under "Participating, @mentions and custom" (carried). |
| 2026-10-21 | On the PC: `git pull`, then `python -m pip install -e ".[dev]"` (carried). |
