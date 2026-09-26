# Roadmap

Written in session 7 (2026-09-25) as the handoff asked. The owner calls the version that completes the current 47-step plan **Milestone 1**; what comes after it is discussed first and ordered later. This page says what Milestone 1 is, how it is marked, and which candidates are on the table for what follows. Nothing here reopens a decision (`docs/DECISIONS.md`).

## Milestone 1 — the 47-step plan complete

Milestone 1 is reached when all three hold:

1. **Every step built.** Build stages B0–B5 (`docs/BUILD_GUIDE.md`, steps 1–43 plus the reference steps) were built in sessions 1–5; step 33 (worktrees) is recorded "not built" under decision 17 and step 40 (chat entry) is optional — both are recorded, not owed (PROGRESS session 5, "Steps").
2. **The live checks 16–23 and the owed 8 proven** on the sample repository (`luissiviero/sdlc-sample-python`): done in session 6 (PROGRESS session 6, "Live checks — results"), plugins 0.2.20–0.2.22.
3. **The leftovers of PROGRESS "Left" done or moved here.** The table below is that move. Anything not in it is done.

| Leftover (from PROGRESS "Left", sessions 5–7) | Where it stands | Milestone 1? |
|---|---|---|
| The first real (un-forced) detection on the sample: the statistics on real data, `gh run view --log-failed` under the sandbox, the failed-run links | Waits for the sample's `CI` workflow to have enough points: the statistics need eight baseline points plus the eight-point tail (choice 67), and a day without a counted run gives no point, so sixteen days *with* runs are needed (it started on 2026-09-25 with one day of runs; NOTES §15). Session 8 (2026-09-26) could not read the sample at all (its session scope held this repository only; NOTES §16) and the calendar alone ruled it out; session 10 reads it when the points exist, from a session started with the sample in scope. The second sitting of session 8 (2026-09-26) found the pace-setter: `ci.yml` ran on `push` and `pull_request` only, so a day nobody touched the sample gave no point; a daily `schedule` line (a `schedule` run counts like a `push` run, `plugin/detect/source.py` `COUNTED_EVENTS`) is the owner's edit that keeps 2026-10-11 (PROGRESS "Session 8, second sitting"). | Yes — the one leftover Milestone 1 waits on |
| Check 19 on a real 3σ (decision 26's pre-approval of a rehearsed rollback) | Cannot be proven with a rehearsal (choice 81) and needs a real 3σ on a project with a declared production; unit-tested. | No — recorded as a known limit |
| D11, the second half of D9, the two Go-path items, choice 87's `/sdlc-init` line | Done in session 7, plugin 0.2.23. | Done |
| The session-7 review's three leftovers (the pin script's ref and copy, the runbook job's park on a failed setup step, the fix round's deterministic collection of reviews and comments) and the origin check before the approved copies' fetch | Done in session 8, plugin 0.2.24 (PROGRESS session 8). | Done |
| The `Diff.files` conversion; the per-decision panel cost (choice 52) | Untouched code; small; done when a fix touches the same files. | Optional |
| An owner `accept` verb for a review finding | A new decision, if the owner wants it (ask, do not build). | Owner's call |
| The release-page backfill for v0.2.15–v0.2.17 | Optional (`sdlc-tag.yml` tags once; the pages of the three tags made by hand carry no notes). | Optional |
| The deploy/status/rollback tools (choice 35) | Built when an adapter names a real deployment. | No — per project |
| A Node flaky-test runbook | When a Node project needs one. | No — per project |
| Session 3's Windows items (the watch setting, the test-file lock) | Ask, do not assume; the owner's PC is the only Windows host. | Owner's call |
| Whether the project's `CLAUDE.md` is loaded in a `--bare` API-key phase run | Every live run of the sample used the OAuth token, so no `--bare` transcript exists; read one when an API-key run happens (PROGRESS session 7, "Known gaps"). | Optional |

**How it is marked.** The owner chose the number on 2026-09-26: **`1.0.0`**. The session that reads the first real detection (the last leftover above) bumps `plugin.json` and `marketplace.json` to `1.0.0` in its PR; the merge of that bump to `main` makes `sdlc-tag.yml` tag the commit `v1.0.0` and write its release page (`sdlc_tag.py`, once, never moved). The root `sdlc.yaml` and the sample's pin follow as guardrail edits (the owner's format: link; row; what is there; what it needs to be), then the sample's upgrade PR with the 1.0.0 copies. The GitHub Milestone ("Milestone 1 — 1.0.0", the pull requests of sessions 6–11 attached, closed after the tag) is the owner's act by hand: a session's GitHub tools have no milestone call. The steps are the table below and `HANDOFF.md`. No other act marks it.

### The path to 1.0.0

Written in the second sitting of session 8 (2026-09-26) after reading the code the dates depend on (PROGRESS "Session 8, second sitting"). Three sessions because the calendar sets the pace: the first real detection needs sixteen daily points of the sample's `CI` workflow (choice 92) and no session can wait a day. The dates assume the `ci.yml` schedule edit (row 1) on 2026-09-26; a day it slips, every later date slips with it. A session marks its rows done with the date and the run URL or PR; a row that failed says why and what moved.

| # | Step | Who | Earliest | Blocked by | Done |
|---|---|---|---|---|---|
| 1 | The sample's `ci.yml` runs daily: a `schedule` line (01:29 UTC) and `workflow_dispatch` under `on:`, on the sample's `main` (the edit table in PROGRESS) | Owner | 2026-09-26 | — | |
| 2 | Start every session with both repositories selected (NOTES §16: the scope is fixed at start; `add_repo` denied twice) | Owner | each session | — | |
| 3 | The first scheduled `CI` run has a person's `actor.login`, not `github-actions[bot]` (else D12 drops it; a fix with a test) | Session 9 | 2026-09-27 | 1, 2 | |
| 4 | The sample's 0.2.24 upgrade PR (the twelve copies and the pin script) merged, then one dispatched detect run: the pin step's `git show … \| python -` line reads `0.2.24`, the framework checks out at `v0.2.24`, the log's `observations` equals the real count (its "insufficient baseline: N point(s)" N is that count minus today's day minus the tail) | Session 9 opens, owner merges | 2026-09-27 | 2 | |
| 5 | The fix round's file, live: a forced tier-2 rehearsal, one "Request changes" review by the owner (a review body and an inline comment, never a plain PR comment: a person's comment at any time becomes the dismissal reason at the close), `evidence/fix-requests.json` on the head as the API returned it | Session 9, owner reviews | 2026-09-27 | 4 | |
| 6 | The runbook park, live: a commit outside `changes/` on the rehearsal's head, `sdlc:go` applied, the job green with `gate-f.json` and `sdlc:needs-human` (choices 90, 96); the rehearsal closed without any comment by a person before the session ends (choices 86, 69) | Session 9, owner applies the label | 2026-09-27 | 5 | |
| 7 | Gaps from 3–6, a test each, an eval case per model lesson; plugin 0.2.25 only if `plugin/` or `template/` changed (then the tag, the two pins, a second upgrade PR) | Session 9 | 2026-09-27 | 3–6 | |
| 8 | Sixteen daily points (8 baseline + 8 tail); the count is read from `actions_list` at each session start | Calendar | 2026-10-10 | 1 | |
| 9 | The provoked bad day: a sample PR with two failing tests, opened by the owner on the sixteenth day before 23:59 UTC (no session that day; a flat zero baseline makes any failure an infinite-sigma, 3σ point: `stats.py`, article p.45 — session 9 checks the baseline is flat and says otherwise what rate is needed), closed without a merge afterwards | Owner | 2026-10-10 | 8 | |
| 10 | The first real detection read from the 05:41 UTC run: `detection.json` (`forced: false`, `we1`, `n_baseline` 8, `n_tail` 8), the incident PR, the diagnosis transcript's `gh run view --log-failed` outcome, the failed-run links; the runbooks the tier-3 diagnosis may have run unattended (the sample declares `production: true` with a rehearsed `rollback-deploy`, pre-approved by decision 26; quarantine and revert PRs preapproved in its `bands.yaml`) read from `evidence/runbook-*.json` — the rollback running is check 19 proven live; the incident and any runbook PR triaged by the owner (choice 69) | Session 10 | 2026-10-11 | 9 | |
| 11 | Gaps from 10, a test each; the bump of `plugin.json` and `marketplace.json` to `1.0.0` in the same PR, with the detection's record and the Milestone's PR list in PROGRESS | Session 10 | 2026-10-11 | 10 | |
| 12 | The merge; `sdlc-tag.yml` tags `v1.0.0` (dispatch it if no run appears, NOTES §14); then the two pins to `1.0.0` (root `sdlc.yaml` line 92, the sample's line 77), after the tag only | Owner | 2026-10-11 | 11 | |
| 13 | The sample's upgrade PR with the 1.0.0 copies, merged; one dispatched detect run at `v1.0.0` | Session 11 opens, owner merges | 2026-10-11 | 12 | |
| 14 | The GitHub Milestone "Milestone 1 — 1.0.0" created by hand in this repository, its PRs attached (a Milestone holds one repository's PRs; the sample's are listed in PROGRESS), closed | Owner | 2026-10-11 | 12 | |
| 15 | This page: "reached on <date>, `v1.0.0`", the tables closed; `HANDOFF.md` for the first post-1.0.0 session | Session 11 | 2026-10-11 | 13 | |

Owed but not blocking, done where the road passes them: the `--bare` check (only if the owner sets `ANTHROPIC_API_KEY` on the sample for one rehearsal; else carried); check 19 on a real 3σ (row 10 may prove it: the sample's production and rehearsed rollback are declared since session 6). After 1.0.0: R1, R2, the `accept` verb, the Windows items, the optional rows of the table above.

## Candidates for what comes after

Discussed first, ordered later. A candidate the owner accepts becomes a framework change through the normal front door — `changes/<id>-<slug>/intent.md` with `Entry route: idea` and `Framework change: yes` (`changes/README.md`) — and its row then carries the change id. Until then the row says `proposed` and the order is blank.

| # | Candidate | Source | Decisions it touches | Status | Order |
|---|---|---|---|---|---|
| R1 | **OKF adoption** — the Open Knowledge Format applied to this framework: frontmatter and `sources` on lessons and eval cases, a generated `lessons/index.md`, `status`/`stale_after` on platform facts, the docs split into small files with an index each, and the cross-project sharing question | `docs/proposals/okf-adoption.md` (from `docs/handoffs/inputs/session-6-okf-analysis.html`, the owner's thinking session of 2026-09-25) | 8 (sticky: shared lessons need a home outside the plugin), 9 (a shared store is a second copy); 7, 17 and 20 unchanged | proposed | |
| R2 | **Session tooling for PDFs and web pages** — Poppler through a Python SessionStart hook, `WebFetch`/`WebSearch` allowed in this repository's settings only, the "refused URLs are listed" rule, and OKF's `references/` reading: anything a session needs more than once is ingested into `docs/reference/` in a reviewed PR | `docs/proposals/session-tooling-pdf-web.md` (from `docs/handoffs/inputs/session-6-pdf-web-setup-prompt.md`, adapted, not run as written) | 6 (guardrail files are the owner's edit), 7 (Python for every hook), the security baseline (no network in phases (b)–(f)); 5 and 23 unchanged | proposed | |

R2 sits under R1 because its rule is OKF's `references/` convention applied to session inputs: mirror once, read files, never the network, which is what `docs/reference/ai-native-sdlc-playbook.txt` already is.

## How this page is kept

One page. A session adds a candidate row only when the owner asked for the proposal; the proposal file carries the argument, the row carries the status. When a candidate ships, its row moves under a "Done" heading with the change id and the plugin version.
