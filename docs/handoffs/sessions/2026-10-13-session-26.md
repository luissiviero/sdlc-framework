# Handoff — the single restart point (rewritten by session 26 on 2026-10-13, after the provocation)

Every session starts here. This file holds the preconditions, the state, every open item, the ordered next steps and what only the owner does. History lives in `docs/PROGRESS.md` (newest record) and `docs/progress/` (older ones); verified facts live in `docs/notes/` (newest: §40). Each session ends by rewriting this file, not by appending to it (ROADMAP R9, part 2). Every guardrail edit is given in the owner's format: link; row; what is there; what it must become.

**Where the project stands.** Plugin **0.3.7** is on `main` (`1e3423e` after PR #157; tagged `v0.3.7` on `9783278`, 2026-10-13 00:31 UTC): change 0002, the shell guard the weekly scan asked for. The root pin is **0.3.6** on purpose until the sandbox proof passes. **The provocation happened on 2026-10-13** (NOTES §40, read by session 25): the owner's PR #58 on the sample (two failing tests) failed its CI at the Lint step, was merged by accident and reverted by PR #59 within eleven minutes; four counted runs, 2 failed and 2 passed, before the day's scheduled run. No provocation PR is left to close. **1.0.0** means one thing: the session that reads the sample's first real detection bumps to 1.0.0 in the same PR as the gaps it finds (ROADMAP "The path to 1.0.0", rows 9–15). That session is next, on **2026-10-14**.

## Preconditions — check before doing anything
1. **Both repositories in the session's scope.** Read the sample with `actions_list` on `ci.yml`, `perPage: 100`, leave out runs by `github-actions[bot]`, count one point per UTC `created_at` day, and write the count down (eighteen through 2026-10-12, NOTES §39; 2026-10-13 had four counted runs before its scheduled one, NOTES §40). Without the sample in scope, say so in the record and do only the parts that need no read of it (session 26 did exactly that).
2. **`main`, the tags and the pin.** Expect `main` at or after `1e3423e` (session 26's two PRs land after it), `.claude-plugin/plugin.json` 0.3.7, `git ls-remote --tags origin | sort -V -k2` ending `v0.3.7` (`-k2`, NOTES §17), root `sdlc.yaml` line 98 `version: 0.3.6`. Anything else moved after this file: read why before building on it.
3. **The local checks green before any PR.** `python -m pip install -e ".[dev]"`, then chained with `set -o pipefail`: `python -m compileall -q plugin tests tasks.py .github/scripts`, `python -m ruff check .`, `python -m ruff format --check .`, `python -m pytest`; `claude plugin validate .` clean but for the `CLAUDE.md`-at-the-root warning. All three `Framework checks` jobs, Windows included, must be green on a PR's final head before the owner is asked to merge; a bot-pushed head waits at `action_required` until the owner approves its runs.
4. **The sample is frozen until the 1.0.0 read** (choice 138): nothing pushed, no PR opened, no run approved, no PR closed with a comment (a member's comment at the close writes a dismissal, choice 69). The provocation was the one exception and it is done.
5. **Guardrail files are the owner's edit**: `CLAUDE.md`, `REVIEW.md`, `sdlc.yaml`, `.claude/**`, and the sample's `bands.yaml`.

## Next steps, in order
1. **2026-10-14, after about 12:40 UTC: the item-11 session.** The detect cron is 05:41 UTC, but its runs start between 10:16 and 12:39 UTC, so read the run's `created_at` first. Expect `detection.json` with `forced: false`, rule `we1`, tier 3, and an incident PR for change **0013** (the scan took 0011 and 0012 on 2026-10-12). The incident's failure log shows **two ruff `PLR0133` errors, not two failing tests** (the provocation's CI failed at Lint before pytest, NOTES §40): read how the tier-3 diagnosis and the runbooks handle that shape. Read the day's final rate too (the scheduled run of 2026-10-13 was not read). Follow `docs/handoffs/session-14-16-live-check-road.md`, sections "Session 15" and "Session 16", with 1.0.0 as the bump: the read, each gap with a test, the 1.0.0 bump in the same PR, then `v1.0.0`, both pins, the sample's upgrade PR with one dispatched detect run, the GitHub Milestone, ROADMAP closed. If the run does not file, record why, fix it in 0.3.x and repeat the provocation the next day. Session 26's PR 1 must be on `main` first: it edits `HANDOFF.md`, `docs/PROGRESS.md` and `docs/notes/`.
2. **After the read: the sandbox proof** (a session's plain PR). It adds `evals/cases/0006-sandbox-write-deny/` and the `runner_setup.py` step in `.github/workflows/framework-evals.yml`. One sandboxed `Framework evals` run with case 0006 green is the precondition for moving the root pin; the pin then moves straight to the newest tag.
3. **The 0.3.8 runs PR** (choice 180; a session's PR, a test per gap, a fresh-context Opus review). It fixes the turn cap as a hard park with a higher (c) default, the label race, a re-run keeping the capped run's wall clock, the (e) park text, and the counter bumped before a round's own review pass. The template sandbox block rides here as the owner's own commit, after step 2.
4. **Then the 2026-10-09 order, renumbered by choice 180:** R7 (change 0004, 0.3.9), then R5 (a plain PR, no bump), then R6 and R10 (their decision files first, one owner review for both; R6 is change 0005), then the carried gaps (two plain PRs), then R9 part 1. R8 starts after R7 has run on two changes. **Then the study's line** (accepted 2026-10-13, PR #162): R11 on its own first, then R12 and R13 together as one change; R12's decision file is `docs/decisions/27.md` (on `main` once PR #162 merges); a session drafts each intent from its proposal file, the owner corrects and merges at gate (a). T10's proposal file (for uniformity) is written in the PR that carries R6's and R10's decision files.
5. **After the read: the owner's triage** of the sample's scan incidents #55 (0010), #56 (0011) and #57 (0012), then the 18 stale sample branches.
6. **In parallel:** the notes-index work is session 26's PR 2, **PR #160** (`docs/handoffs/2026-10-09-notes-index-prompt.md`; §40 carries its three fields in this PR, so the two merge in either order; every later note carries `description`, `tags` and `sources` and runs `python tasks.py notes-index` in the same commit). After the read: the study's next proposal batch (T17, T19, T27, T28), kept there by the owner on 2026-10-13 (choice 181 reaffirmed in the checking session, PR #162); three or four files per PR, in the order of the record's section 8.

## Every open item
| Item | Where | What is left | Who acts | Blocks 1.0.0 |
|---|---|---|---|---|
| Session 26's PR 1, **PR #158** (this file, PROGRESS, NOTES §40) | framework | Merge before 12:00 UTC on 2026-10-14 | owner | yes (the item-11 session edits the same files) |
| Item 11, the read and the 1.0.0 bump | both | Not started; 2026-10-14 after about 12:40 UTC | a session, then the owner | yes |
| Sandbox proof, then the pin to the newest tag | framework | Case 0006 and the evals runner step | a session, then the owner's pin row | no |
| 0.3.8 runs PR | framework | Not started (`docs/progress/session-25.md`, known gaps) | a session | no |
| R7, R5, R6, R10, the carried gaps, R9 part 1, R8 | framework | Proposals merged; no intent yet | sessions; the owner reviews | no |
| Guardrail row: `ruff format --check` in the gate's lint | framework `sdlc.yaml` line 19 | The `&&` check is done (NOTES §40); the row is in PROGRESS "Session 26" | owner | no |
| Sample PRs #55, #56, #57 (scan incidents) | sample | Triage at gate (f) | owner, after the read | no |
| 57 merged branches left on origin (33 `ccr-*`, 7 `claude/*`, 9 `luissiviero-patch-*`, 8 `sdlc/<id>/<phase>`) | framework | All contained in `main` (NOTES §40); not on choice 177's list, so whether they go is the owner's call | owner | no |
| 18 stale sample branches | sample | Delete after the read (the two of the provocation added) | owner | no |
| R2's tables (SessionStart hook, `WebSearch`, "Tooling rules") | framework guardrails | Not applied | owner | no |
| Windows sitting (hook timing, test-file lock, watch setting; the `&&` chain through `run_command` on `cmd.exe`, NOTES §40) | owner's PC | Not done | owner | no |
| Notes-index work | framework | Session 26's PR 2, **PR #160**: open, checks green on its head, ready for the owner's review | owner | no |
| Study batch T17, T19, T27, T28 | framework | After the read (choice 181, reaffirmed 2026-10-13); `docs/handoffs/2026-10-13-study-line-start-table.md` (PR #159) was checked row by row and answered in PR #162 | a study session | no |
| The study's line R11, then R12 + R13 | framework | Accepted 2026-10-13 (PR #162); after R9 part 1; R12's decision file 27 in PR #162; no intent yet | sessions draft the intents; the owner merges | no |

## What the owner does
| When | Act |
|---|---|
| Before 12:00 UTC on 2026-10-14 | Approve the runs on session 26's PR 1 and merge it; then the guardrail row (PROGRESS "Session 26"). |
| 2026-10-14, about 12:40 UTC | Check that the detect run filed the incident for change 0013; start the item-11 session with both repositories in scope. |
| After the item-11 PR | Merge it; check `v1.0.0`; apply both pin rows; merge the sample's upgrade PR; create and close the Milestone. |
| A fix round parks on the cap | Post the review first, then apply `sdlc:reset-iterations` within the same minute (NOTES §35, §39). |
| Before merging any PR | Approve the bot-started `Framework checks` and `Framework evals` runs on the final head; merge only when all four jobs are green. |
| Any time | Decide the 57 merged branches on origin (NOTES §40 lists them by kind); R2's tables; the Windows sitting; review session 26's PR 2 when it is ready. |
| Any time | Merge PR #162 (the study line's start table checked and answered, decision 27, the crosswalk at 0.3.7); it carries the one `docs/decisions/` change, written at the owner's word. |

## Rules for every session
- Never reopen a settled decision (`docs/decisions/index.md`, the numbered choices in PROGRESS) without asking the owner.
- Never merge to `main`, never push to someone else's branch, never use bypass-permissions mode. A refused action is reported, not worked around.
- Write "verified" only with a run URL, a file or command output; otherwise write "not verified" and the reason. A fact another session read is cited as "read by session N" with its URL, never as one's own verification.
- A version bump only for a change under `plugin/` or `template/`; 1.0.0 belongs to the item-11 PR alone.
- A kept record is annotated beside the sentence, never rewritten (choice 126). `docs/PROGRESS.md` holds the newest record only; the previous one moves to `docs/progress/` unchanged with its index line.
- Read only parks (2026-10-09): a run that ends green, at a human gate or dispatching the next phase is not read in full; a parked run, a red job or a run named in an open question is.
- A review that starts a fix round goes on the PR before any label. A fix round at (e) starts only from a review, never from a deploy dispatch.
- Every PR that touches `plugin/detect/`, `plugin/ci/run_phase.py` or the detect, runbook and fix workflow templates goes on the port list in PROGRESS until the 1.0.0 read.
- Edit docs with the Edit tool, sentence by sentence; cite the article by PDF page.
