# Handoff — sessions 10 to 16: the readiness review's four groups, then the road to 1.0.0

Session 9 (2026-09-26) was the 1.0.0 readiness review: three passes of fresh-context sub-agents over both repositories, the verdict "not 1.0.0 yet" by the repository's own criteria, six *must fix* defects built in plugin **0.2.25** with a test each, and the remaining findings sorted into four groups. The record is `docs/reviews/2026-09-26-readiness-review.md` (read it whole: every group below points into it), `docs/PROGRESS.md` "Session 9" and `docs/NOTES.md` §17. The previous brief (sessions 9–11, the live-check road) is kept at `docs/handoffs/session-9-11-road-to-1-0-0.md`; its three sessions are sessions 14–16 here, their content unchanged but for what session 9 corrected.

The owner's rule for this road: **each remaining group is one session** — sessions 10 to 13 — and they run before the live checks, in the days the calendar leaves free (the first judging run of the real detection is still 2026-10-11 if the sample's schedule holds). None of them needs the sample's points. Each session ends by rewriting this file for the next one. Keep the owner's format for every guardrail edit: "link; row; what is there; what it needs to be".

## Preconditions — check before doing anything
1. **The session's GitHub scope holds both repositories** (NOTES §16, §17): the first act is one read of the sample (`actions_list` on `ci.yml`). Session 9 was started so and every tool answered; without it, stop the live part and say so.
2. `main` is at plugin 0.2.25 (`.claude-plugin/plugin.json`; `git ls-remote --tags origin | sort -V -k2` ends with `v0.2.25` — `-k2`, the SHA column sorts first otherwise, NOTES §17). If session 9's PR is not merged yet, stop and say so: sessions 10–13 each bump the version and the tags must exist in order.
3. The root `sdlc.yaml` pins the last tag (line 92) and the sample's `main` pins it too (line 77): both are the owner's guardrail edits after each tag (PROGRESS session 9, the guardrail table). The sample's workflow copies and its `.github/scripts/sdlc_pin.py` are still the **0.2.23** ones (byte-verified in session 9 against the tags): session 14 opens the upgrade PR to the latest tag, the way sessions 5–7 did (`git rm .github/workflows/sdlc-*.yml`, `plugin/init/sdlc_init.py --root <sample>`, `git restore -- sdlc.yaml`, one PR the owner merges). Until then a fix round on the sample still reads the PR itself and a Go whose setup step fails is still a red run.
4. `python tasks.py check` green (1196 tests at the end of session 9) and `claude plugin validate .` clean; the dev tools are not in the container at start (`python -m pip install -e ".[dev]"` first; NOTES §16).
5. Sub-agents named by model explicitly (`model: "opus"` for the review; the split of MODEL_ALLOCATION §5d).
6. **The date and the points.** Sixteen days *with* counted runs of the sample's `CI` workflow since 2026-09-25 (choice 92): count them (`actions_list` on `ci.yml`, excluding the runs by `github-actions[bot]`, D12; one point per UTC `created_at` day) at the start of every session and write the count down. Two existed on 2026-09-26; with the schedule (PR #41, cron `29 1 * * *`) every later day gives one, so the sixteenth point is 2026-10-10 and the run of **2026-10-11** is the first that judges. The baseline is **not flat**: run 36257154359 (2026-09-26) is a counted failure (NOTES §17); the simulated bad day still files tier 3 (about 19σ).

## Read in this order
1. `docs/reviews/2026-09-26-readiness-review.md` — the verdict, what was fixed, the four groups with file:line, and what was ruled not a problem (so nobody reopens it).
2. `docs/PROGRESS.md` — the session-9 record (the six defects and their tests, choices 99–102, the guardrail rows, the questions), then session 8's two records.
3. `docs/ROADMAP.md`, "How it is marked" and "The path to 1.0.0" (rows 12a–12d are sessions 10–13).
4. `docs/NOTES.md` §17, §16 and §14.
5. `docs/OPERATING_MODEL.md` §2, §4.1 (the owner actions), §4.2 (the guard and the default branch), §8 (the hooks' encoding, the install's commit) — the sentences 0.2.25 added.
6. The code of the session's own group (below).

## Objective
Close the readiness review's four groups, one per session, each with a test per defect and an eval case per model lesson, then walk the live-check road (sessions 14–16) to the first real detection, the 1.0.0 bump, the tag, the pins, the sample's 1.0.0 copies and the closed milestone. The `--bare` check and the owner's four questions ride along where they can and do not block.

## Session 10 — group A: the gate and `status.yaml` (plugin 0.2.26)
The review's "Group A" list, in this order; each item a test in `tests/test_gate.py` (or the module's own test file) that asserts the wrong outcome today and the right one after.
1. `owner_actions`: a recorded `risk_accepted_by` or `tests_unlocked_by` actor is verified, not believed — the runner applied the label (`run_phase.py apply_labels`) and re-checks the recorded actor against the label event's actor after the session; by hand, the commit author is the act as before. (0.2.25's `test_lock` check already refuses a test changed while the lock stands; the forged actor on a lift is the part left.)
2. `owner_actions`: a `panel_calls` drop is judged like an `iterations` drop (the same label resets both).
3. `profile_override` and `review_override` read from the base branch's `status.yaml` (the copy the owner approved), in `gate/gate.py` and `run_phase.py guard`, as `intent.md` is; the branch's own values are ignored with a note in the gate result.
4. Gate (a) runs `design_scope` (with change 0000 exempt, as `guardrails` is).
5. The `panel` check consumes each ledger `#n` once; a second closing on the same line fails.
6. `important_findings` strips the severity before comparing.
7. `owner_actions` judges every risk-gaining commit in the walked history, not the newest only.
8. A non-boolean `paused` or `deploy.production` fails closed (`yes`/`on`/`"true"` are refused with the line named), in `gate/limits.py`, `gate/preflight.py`, `run_phase.py` and `hooks/production_gate.py`.
9. `pr/counters.py` excludes the remote-abandoned ids as `open_incidents` does.
10. `/sdlc-deploy.md` panel step: re-run the review pass after the panel's commit, and drop the diff-file and verdict-file sentences phase (e) has no step for.
Then: the version bump (`plugin.json` and `marketplace.json` to 0.2.26; `tests/test_scaffold.py` asserts they agree), the template's workflow copies and this repository's identical (tested), the checks of "Rules" below, a fresh-context Opus review of the diff, one draft PR against `main`; after the merge the owner checks `v0.2.26` and applies the two pins as guardrail rows. Docs: PROGRESS on top, NOTES §18 only if a fact was read, OPERATING_MODEL where the code changed, ROADMAP row 12a done, this file for session 11.

## Session 11 — group B: CI, release and detect (plugin 0.2.27)
1. The release approval is tied to the change: `release/approval.py` finds the PR by the number `status.yaml` records (written by `pr/cli.py upsert`) and accepts an open PR or the one merged at gate (e); a branch name alone finds nothing; the label is read from that PR only. The production-gate hook passes the change id it resolved.
2. `production_gate.py guarded()`: the binary's basename (a path, `.exe`, `.cmd`), options between the tool and its verb (`terraform -chdir=x apply`, `kubectl --context p apply`, `gh -R o/r release create`), and a test per spelling.
3. `detect/runbooks.py`: the fully qualified `refs/remotes/origin/<default>` everywhere the short form is used; a runbook branch that already exists locally is refused (a fresh name, or a failure that names it).
4. The detect step snapshots `evidence/detection.json` (and the proposal's inputs it judges) before the session starts, and `finish` judges the snapshot; a file the session changed is reported and the route refused (PROGRESS session 8's "shared checkout" gap, closed as a class for the detect path).
5. `gate/diff.py`: no merge base is a failed diff (fail closed), never an empty file list.
6. `sdlc-tag.yml`: a `workflow_dispatch` on a ref that is not the default branch ends green with "not the default branch"; `sdlc_tag.py` refuses the same.
7. Dismissals: a `sdlc/<id>/dismiss` branch whose PR was closed without a merge no longer counts as pending (read the PR's state, or delete the branch in `sdlc-abandon.yml` when the closed PR is a dismissal PR); `_closing_reason` keeps a person's comment only when its `author_association` is `OWNER`, `MEMBER` or `COLLABORATOR`.
8. `sdlc-design.md` and `sdlc-build.md`: the by-hand re-run reads the PR's comments with the same membership filter as `/sdlc-fix` step 1 (prose; in CI `rerun_reason` refuses the re-run).
Then the bump to 0.2.27, the copies, the checks, the Opus review, the draft PR, the pins, the docs, this file for session 12.

## Session 12 — group C: the test and eval infrastructure (a bump only if `plugin/` or `template/` changed)
1. A workflow in this repository (`.github/workflows/framework-checks.yml`, not a template): on `pull_request` and `push` to `main`, `python -m pip install -e ".[dev]"` then `python tasks.py check` on `ubuntu-latest` and `windows-latest` (the Windows run is the check of NOTES §17's encoding fact and of the `.cmd` launchers, last run under 657 tests). PROGRESS session 3's "the CI job of PR A is the check" is corrected in group D.
2. `plugin/evals/run.py`: an HTML comment at the top of `prompt.md` is stripped before the prompt is sent (a test with the dry-run argv); case 0003's note moves into its `checks.yaml`.
3. One eval case whose check proves the plugin's hooks loaded: the deny line in `evidence/hook-log.jsonl` (OPERATING_MODEL §8) after an attempted guardrail edit; 0004's regex tightened to the run's own line, not the prompt's example.
4. `template/evals/README.md`: say that a pin bump is evaluated against the old plugin unless the workflow triggers on `sdlc.yaml` (and add the trigger if the owner wants it).
Then the checks, the Opus review, the draft PR (the new workflow must be green on the PR itself), the docs, this file for session 13.

## Session 13 — group D: the documentation pass (no bump)
The review's "Group D" list, edited with the Edit tool sentence by sentence (never a scripted rewrite: CLAUDE.md "Things Claude gets wrong"). The guardrail files among them (`template/sdlc.yaml` is a template, editable; the root `sdlc.yaml` line 8 is the owner's) are given as guardrail rows. Also: PROGRESS session 3's CI claim; MODEL_ALLOCATION's session-6 figures; the "sessions 9–11" wording wherever it survives. Then the checks (the doc tests count), the Opus review, the draft PR, this file for session 14.

## Session 14 — the live checks that need no points (the former session 9)
Start after the first 01:29 UTC scheduled `CI` run has completed and been read (allow for GitHub's delays: the one scheduled detect run started 4 h 35 min late, NOTES §17; read the run's `created_at`).
1. Preconditions 1–6, the point count written down (the days, the runs per day, the excluded ones, the failure of 2026-09-26 among them), the actor of the first scheduled `CI` run (a person's login, else D12 drops it: a fix with a test).
2. **The sample at the latest tag**: the upgrade PR (precondition 3), the diff limited to the twelve `sdlc-*.yml` copies and `.github/scripts/sdlc_pin.py`, `sdlc_init.py --root <sample>` reporting every copy `unchanged` afterwards; the owner merges it during the session. Then one `workflow_dispatch` of `sdlc-detect.yml` with `force_tier` empty: the pin step's line reads the tag, the framework checks out at it, the verdict "insufficient baseline: N point(s), 8 needed" with `observations` equal to the count. The same run shows `SDLC_DEFAULT_BRANCH` on the phase step (0.2.25) and the first digest after it shows no unprotected-branch notice on the sample (its `main` has a classic rule) — and, on this repository, the notice until the owner creates the ruleset.
3. **The fix round's file, live**: dispatch `sdlc-detect.yml` with `force_tier: 2`; the owner leaves one "Request changes" review (a review body and an inline comment, **no plain PR comment**); read `evidence/fix-requests.json` on the head. A shape mismatch against GitHub's API is a defect with a test.
4. **The runbook park, live**: one commit outside `changes/` on the rehearsal's head, `sdlc:go` applied; expected a green job, `evidence/gate-f.json` with the step's error line, `status.yaml` parked, `sdlc:go` removed, `sdlc:needs-human` present. Revert the commit afterwards.
5. **Close the rehearsal** without a comment by a person (choice 86; check `issue_comments` first).
6. Gaps from 2–4 with a test each; a bump only if `plugin/` or `template/` changed.
7. The `--bare` check, only if the owner set `ANTHROPIC_API_KEY` on the sample for one rehearsal.
8. Docs as above; ROADMAP rows 3–7 done with dates; this file for session 15 with the exact point count and the date of the first judging run.

## Session 15 — the first real detection and the bump (the former session 10; 2026-10-11 if the schedule held; start in the afternoon UTC or read the run's `created_at` first)
Unchanged from `docs/handoffs/session-9-11-road-to-1-0-0.md` "Session 10" but for one correction: the baseline is not flat, so `detection.json` will carry a non-zero `mean` and `sigma` (NOTES §17) and the rule still `we1` at tier 3; the provoked bad day is the owner's act on 2026-10-10 before 23:59 UTC (a sample PR with two failing tests, closed without a merge afterwards). Then the run read, the diagnosis transcript, the runbooks the tier-3 diagnosis may have run unattended (check 19 live if the rehearsed rollback ran), the owner's triage, the gaps with a test each, and the 1.0.0 bump in the same PR with the Milestone's PR list in PROGRESS (this repository's PRs: #47–#56, session 9's, and sessions 10–15's). After the merge: `v1.0.0` (dispatch `sdlc-tag.yml` if no run appears), then the two pins.

## Session 16 — closing the milestone (the former session 11)
The sample's upgrade PR with the 1.0.0 copies; the GitHub Milestone by hand; `docs/ROADMAP.md` closed ("reached on <date>, `v1.0.0`"); the next `HANDOFF.md` for the first post-1.0.0 session with the owner's answers (R1, R2, the `accept` verb, the Windows items) and the optional rows.

## What the owner does on this road (nothing else is the owner's)
| When | Act |
|---|---|
| Now (after session 9's PR) | Merge it; check `v0.2.25` (dispatch `sdlc-tag.yml` if no run appears, NOTES §14); apply the two pins (root `sdlc.yaml` line 92 and the sample's line 77: `0.2.24` → `0.2.25`) after the tag; **create the branch ruleset on this repository's `main`**: *Restrict updates* with the repository admin as the only bypass actor, plus restrict deletions, block force pushes, require a pull request (decision 4; `/sdlc-init` §6) — the digest will say so until an `update` rule exists; the sample's classic rule does not count, so its digest says so too until the owner adds the same ruleset there. |
| Every session start | Start the session with both repositories selected (precondition 1). |
| Sessions 10, 11 (and 12 if it bumps) | Merge the PR when the session asks; check the tag; apply the two pins. |
| Session 13 | Merge the docs PR; apply the guardrail rows it lists (the root `sdlc.yaml` line 8 among them). |
| Session 14 | Merge the sample's upgrade PR when the session asks; leave the "Request changes" review (a body and an inline comment, never a plain comment); apply `sdlc:go`; if a bump happens: merge, tag, pins, a second upgrade PR. Optional: `ANTHROPIC_API_KEY` on the sample for the `--bare` check. |
| 2026-10-10, before 23:59 UTC | Open the failing sample PR (session 15, step 1); no session runs that day. |
| Session 15 | Triage the real incident; merge the 1.0.0 PR; check `v1.0.0`; apply the two pins after the tag. |
| Session 16 | Merge the sample's 1.0.0 upgrade PR; create and close the GitHub Milestone. |
| Any time | R1 and R2; the `accept` verb; the Windows items; the threat-model question of PROGRESS session 9 — none blocks 1.0.0. |

## Rules for these sessions
- Never reopen a decision; a decision a live run shows impossible as built is documented in PROGRESS. The review's "ruled not a problem" list is settled the same way.
- Cite the PDF page whenever the article is used.
- No notifications, no bypass-permissions mode, no third-party runtime dependency, Python for every script, workflows whose `run:` lines call `python` (and the pinned `claude` install) only — the one exception is the pin step's `git show … | python -` line under `shell: bash` (choice 95) — never with a `${{ }}` in the line (an `env:` value may carry one).
- Guardrail files here and in the sample (`CLAUDE.md`, `.claude/**`, `REVIEW.md`, `sdlc.yaml`, `bands.yaml`): the owner's edit, given as "link; row; what is there; what it needs to be".
- One open incident per metric (choice 69); a rehearsal is closed without a comment (choice 86) and never left open overnight on the road to the first real detection.
- The shakedown method of session 6 (choice 88) when a fix must be live-tested before the tag.
- A version is bumped only for a change in `plugin/` or `template/`; the 1.0.0 bump is the one exception and belongs to session 15's PR alone.
- Every PR: `python -m compileall -q plugin tests tasks.py .github/scripts`, the full `python -m pytest`, `python -m ruff check .`, `python -m ruff format --check .` — green before the push, chained on the exit codes; a fresh-context Opus review of the diff before the final commit; a draft PR against `main`.
- The secrets-check hook refuses any file whose text contains a credential-shaped string: describe a key in words.
- An environment fact is recorded in NOTES with its read date and re-tested only when the date is older than the environment's last change (choice 93).
- What a session cannot prove it writes as "not verified" with the reason; a fact is "verified" only with the run URL, the file or the command output that showed it.
