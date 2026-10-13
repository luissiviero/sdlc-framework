# Handoff — the single restart point (rewritten by session 25 on 2026-10-13, after `v0.3.7`)

Every session starts here. This file holds the preconditions, the state, every open item, the ordered next steps and what only the owner does. History lives in `docs/PROGRESS.md` (newest record) and `docs/progress/` (older ones); verified facts live in `docs/notes/` (newest: §39). Each session ends by rewriting this file, not by appending to it (ROADMAP R9, part 2). Every guardrail edit is given in the owner's format: link; row; what is there; what it must become.

**Where the project stands.** Plugin **0.3.7** is on `main` (`9783278`, tagged `v0.3.7`, 2026-10-13 00:31 UTC): change 0002, the shell guard the weekly scan asked for. The root pin is **0.3.6** on purpose until the sandbox proof passes. **1.0.0** means one thing: the session that reads the sample's first real detection bumps to 1.0.0 in the same PR as the gaps it finds (ROADMAP "The path to 1.0.0", rows 9–15). That road waits on one owner act: the provocation PR on the sample, set for **2026-10-13**.

## Preconditions — check before doing anything
1. **Both repositories in the session's scope.** Read the sample with `actions_list` on `ci.yml`, `perPage: 100`, leave out runs by `github-actions[bot]`, count one point per UTC `created_at` day, and write the count down (eighteen through 2026-10-12, NOTES §39). Without the sample in scope, say so in the record and do only the parts that need no read of it.
2. **`main`, the tags and the pin.** Expect `main` at or after `9783278`, `.claude-plugin/plugin.json` 0.3.7, `git ls-remote --tags origin | sort -V -k2` ending `v0.3.7` (`-k2`, NOTES §17), root `sdlc.yaml` line 98 `version: 0.3.6`. Anything else moved after this file: read why before building on it.
3. **The local checks green before any PR.** `python -m pip install -e ".[dev]"`, then chained with `set -o pipefail`: `python -m compileall -q plugin tests tasks.py .github/scripts`, `python -m ruff check .`, `python -m ruff format --check .`, `python -m pytest`; `claude plugin validate .` clean but for the `CLAUDE.md`-at-the-root warning. All three `Framework checks` jobs, Windows included, must be green on a PR's final head before the owner is asked to merge; a bot-pushed head waits at `action_required` until the owner approves its runs.
4. **The sample is frozen until the 1.0.0 read** (choice 138): nothing pushed, no PR opened, no run approved, no PR closed with a comment (a member's comment at the close writes a dismissal, choice 69). The one exception is the owner's provocation PR.
5. **Guardrail files are the owner's edit**: `CLAUDE.md`, `REVIEW.md`, `sdlc.yaml`, `.claude/**`, and the sample's `bands.yaml`.

## Next steps, in order
1. **2026-10-13, before 23:59 UTC: the owner's provocation.** A PR on the sample with two failing tests and no other change, opened by the owner, not a bot. No other sample activity that day. Never approve a bot-started run on the sample. Close the PR without a merge after step 2's run.
2. **2026-10-14, after about 12:40 UTC: the item-11 session.** The detect cron is 05:41 UTC, but its runs start between 10:16 and 12:39 UTC, so read the run's `created_at` first. Expect `detection.json` with `forced: false`, rule `we1`, tier 3, and an incident PR for change **0013** (the scan took 0011 and 0012 on 2026-10-12). Follow `docs/handoffs/session-14-16-live-check-road.md`, sections "Session 15" and "Session 16", with 1.0.0 as the bump: the read, each gap with a test, the 1.0.0 bump in the same PR, then `v1.0.0`, both pins, the sample's upgrade PR with one dispatched detect run, the GitHub Milestone, ROADMAP closed. If the run does not file, record why, fix it in 0.3.x and repeat the provocation the next day.
3. **After the read: the sandbox proof** (a session's plain PR). It adds `evals/cases/0006-sandbox-write-deny/` and the `runner_setup.py` step in `.github/workflows/framework-evals.yml`. One sandboxed `Framework evals` run with case 0006 green is the precondition for moving the root pin; the pin then moves straight to the newest tag.
4. **The 0.3.8 runs PR** (choice 180; a session's PR, a test per gap, a fresh-context Opus review). It fixes the turn cap as a hard park with a higher (c) default, the label race, a re-run keeping the capped run's wall clock, the (e) park text, and the counter bumped before a round's own review pass. The template sandbox block rides here as the owner's own commit, after step 3.
5. **Then the 2026-10-09 order, renumbered by choice 180:** R7 (change 0004, 0.3.9), then R5 (a plain PR, no bump), then R6 and R10 (their decision files first, one owner review for both; R6 is change 0005), then the carried gaps (two plain PRs), then R9 part 1. R8 starts after R7 has run on two changes. **Then the study's line** (accepted 2026-10-13, PR #162): R11 on its own first, then R12 and R13 together as one change; R12's decision file is `docs/decisions/27.md` (on `main` once PR #162 merges); a session drafts each intent from its proposal file, the owner corrects and merges at gate (a). T10's proposal file (for uniformity) is written in the PR that carries R6's and R10's decision files.
6. **After the read: the owner's triage** of the sample's scan incidents #55 (0010), #56 (0011) and #57 (0012), then the 16 stale sample branches.
7. **Any time, in parallel:** the notes-index work (`docs/handoffs/2026-10-09-notes-index-prompt.md`). After the read: the study's next proposal batch (T17, T19, T27, T28), kept there by the owner on 2026-10-13 (choice 181 reaffirmed in the checking session, PR #162); three or four files per PR, in the order of the record's section 8.

## Every open item
| Item | Where | What is left | Who acts | Blocks 1.0.0 |
|---|---|---|---|---|
| Provocation PR | sample | Not opened on 2026-10-10; set for 2026-10-13 | owner | yes |
| Item 11, the read and the 1.0.0 bump | both | Not started | a session, then the owner | yes |
| Sandbox proof, then the pin to the newest tag | framework | Case 0006 and the evals runner step | a session, then the owner's pin row | no |
| 0.3.8 runs PR | framework | Not started (PROGRESS "Session 25", known gaps) | a session | no |
| R7, R5, R6, R10, the carried gaps, R9 part 1, R8 | framework | Proposals merged; no intent yet | sessions; the owner reviews | no |
| Guardrail row: `ruff format --check` in the gate's lint | framework `sdlc.yaml` line 19 | A session checks that the runner accepts `&&` first | owner | no |
| Sample PRs #55, #56, #57 (scan incidents) | sample | Triage at gate (f) | owner, after the read | no |
| 26 stale framework branches | framework | Delete; all merged history (NOTES §39) | owner | no |
| 16 stale sample branches | sample | Delete after the read | owner | no |
| R2's tables (SessionStart hook, `WebSearch`, "Tooling rules") | framework guardrails | Not applied | owner | no |
| Windows sitting (hook timing, test-file lock, watch setting) | owner's PC | Not done | owner | no |
| Notes-index work | framework | Prompt saved; not started | a session | no |
| Study batch T17, T19, T27, T28 | framework | After the read (choice 181, reaffirmed 2026-10-13) | a study session | no |
| The study's line R11, then R12 + R13 | framework | Accepted 2026-10-13 (PR #162); after R9 part 1; R12's decision file 27 in PR #162; no intent yet | sessions draft the intents; the owner merges | no |

## What the owner does
| When | Act |
|---|---|
| 2026-10-13, before 23:59 UTC | The provocation PR (step 1). |
| 2026-10-14, about 12:40 UTC | Check that the detect run filed the incident; start the item-11 session with both repositories in scope. |
| After the item-11 PR | Merge it; check `v1.0.0`; apply both pin rows; merge the sample's upgrade PR; create and close the Milestone; close the provocation PR without a merge. |
| A fix round parks on the cap | Post the review first, then apply `sdlc:reset-iterations` within the same minute (NOTES §35, §39). |
| Before merging any PR | Approve the bot-started `Framework checks` and `Framework evals` runs on the final head; merge only when all four jobs are green. |
| Any time | Delete these 26 framework branches: `fix/live-run-blockers`, `claude/vigilant-mccarthy-4a8xx4`, `claude/happy-galileo-v3979m`, `fix/editable-install`, `claude/session-2-handoff-review-b8kju3`, `claude/handoff-review-planning-cjdn46`, `fix/stale-park-after-gate`, `fix/build-run-observability`, `fix/stale-park-single-reader`, `fix/plan-sync-committed-diff`, `claude/project-concept-comparison-r5rsnf`, `anchor-edit-deny-rules`, `owner/anchor-root-settings`, `claude/find-project-plan-artifact-ykj4cx`, `owner/pin-0.2.12`, `owner/pin-0.2.10`, `claude/b4-release-gate`, `claude/session-recovery-dead-pc-cbsm7h`, `claude/plugin-workflow-diagram-o1fgxh`, `claude/session-objectives-table-vzcqrm`, `claude/documentation-review-08tyam`, `claude/phase-f-shakedown-vbr2c6`, `claude/session-8-handoff-8v3zrm`, `claude/okf-benefits-analysis-6pzoez`, `claude/roadmap-1-0-0-pi7pmo`, `luissiviero-patch-1`. |
| Any time | R2's tables; the Windows sitting; the guardrail row in PROGRESS "Session 25". |
| Any time | Merge PR #162 (the study line's start table checked, decision 27, the owner's answers of 2026-10-13); it carries the one `docs/decisions/` change, written at the owner's word. |

## Rules for every session
- Never reopen a settled decision (`docs/decisions/index.md`, the numbered choices in PROGRESS) without asking the owner.
- Never merge to `main`, never push to someone else's branch, never use bypass-permissions mode. A refused action is reported, not worked around.
- Write "verified" only with a run URL, a file or command output; otherwise write "not verified" and the reason.
- A version bump only for a change under `plugin/` or `template/`; 1.0.0 belongs to the item-11 PR alone.
- A kept record is annotated beside the sentence, never rewritten (choice 126). `docs/PROGRESS.md` holds the newest record only; the previous one moves to `docs/progress/` unchanged with its index line.
- Read only parks (2026-10-09): a run that ends green, at a human gate or dispatching the next phase is not read in full; a parked run, a red job or a run named in an open question is.
- A review that starts a fix round goes on the PR before any label. A fix round at (e) starts only from a review, never from a deploy dispatch.
- Every PR that touches `plugin/detect/`, `plugin/ci/run_phase.py` or the detect, runbook and fix workflow templates goes on the port list in PROGRESS until the 1.0.0 read.
- Edit docs with the Edit tool, sentence by sentence; cite the article by PDF page.
