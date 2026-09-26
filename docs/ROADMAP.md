# Roadmap

Written in session 7 (2026-09-25) as the handoff asked. The owner calls the version that completes the current 47-step plan **Milestone 1**; what comes after it is discussed first and ordered later. This page says what Milestone 1 is, how it is marked, and which candidates are on the table for what follows. Nothing here reopens a decision (`docs/DECISIONS.md`).

## Milestone 1 — the 47-step plan complete

Milestone 1 is reached when all three hold:

1. **Every step built.** Build stages B0–B5 (`docs/BUILD_GUIDE.md`, steps 1–43 plus the reference steps) were built in sessions 1–5; step 33 (worktrees) is recorded "not built" under decision 17 and step 40 (chat entry) is optional — both are recorded, not owed (PROGRESS session 5, "Steps").
2. **The live checks 16–23 and the owed 8 proven** on the sample repository (`luissiviero/sdlc-sample-python`): done in session 6 (PROGRESS session 6, "Live checks — results"), plugins 0.2.20–0.2.22.
3. **The leftovers of PROGRESS "Left" done or moved here.** The table below is that move. Anything not in it is done.

| Leftover (from PROGRESS "Left", sessions 5–7) | Where it stands | Milestone 1? |
|---|---|---|
| The first real (un-forced) detection on the sample: the statistics on real data, `gh run view --log-failed` under the sandbox, the failed-run links | Waits for the sample's `CI` workflow to have enough points: the statistics need eight baseline points plus the eight-point tail (choice 67), and a day without a counted run gives no point, so sixteen days *with* runs are needed (it started on 2026-09-25 with one day of runs; NOTES §15). Session 8 (2026-09-26) could not read the sample at all (its session scope held this repository only; NOTES §16) and the calendar alone ruled it out; session 9 reads it when the points exist, from a session started with the sample in scope. | Yes — the one leftover Milestone 1 waits on |
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

**How it is marked.** The owner chose the number on 2026-09-26: **`1.0.0`**. The session that reads the first real detection (the last leftover above) bumps `plugin.json` and `marketplace.json` to `1.0.0` in its PR; the merge of that bump to `main` makes `sdlc-tag.yml` tag the commit `v1.0.0` and write its release page (`sdlc_tag.py`, once, never moved). The root `sdlc.yaml` and the sample's pin follow as guardrail edits (the owner's format: link; row; what is there; what it needs to be), then the sample's upgrade PR with the 1.0.0 copies. The GitHub Milestone ("Milestone 1 — 1.0.0", the pull requests of sessions 6–9 attached, closed after the tag) is the owner's act by hand: a session's GitHub tools have no milestone call. The steps are `HANDOFF.md` deliverable 6. No other act marks it.

## Candidates for what comes after

Discussed first, ordered later. A candidate the owner accepts becomes a framework change through the normal front door — `changes/<id>-<slug>/intent.md` with `Entry route: idea` and `Framework change: yes` (`changes/README.md`) — and its row then carries the change id. Until then the row says `proposed` and the order is blank.

| # | Candidate | Source | Decisions it touches | Status | Order |
|---|---|---|---|---|---|
| R1 | **OKF adoption** — the Open Knowledge Format applied to this framework: frontmatter and `sources` on lessons and eval cases, a generated `lessons/index.md`, `status`/`stale_after` on platform facts, the docs split into small files with an index each, and the cross-project sharing question | `docs/proposals/okf-adoption.md` (from `docs/handoffs/inputs/session-6-okf-analysis.html`, the owner's thinking session of 2026-09-25) | 8 (sticky: shared lessons need a home outside the plugin), 9 (a shared store is a second copy); 7, 17 and 20 unchanged | proposed | |
| R2 | **Session tooling for PDFs and web pages** — Poppler through a Python SessionStart hook, `WebFetch`/`WebSearch` allowed in this repository's settings only, the "refused URLs are listed" rule, and OKF's `references/` reading: anything a session needs more than once is ingested into `docs/reference/` in a reviewed PR | `docs/proposals/session-tooling-pdf-web.md` (from `docs/handoffs/inputs/session-6-pdf-web-setup-prompt.md`, adapted, not run as written) | 6 (guardrail files are the owner's edit), 7 (Python for every hook), the security baseline (no network in phases (b)–(f)); 5 and 23 unchanged | proposed | |

R2 sits under R1 because its rule is OKF's `references/` convention applied to session inputs: mirror once, read files, never the network, which is what `docs/reference/ai-native-sdlc-playbook.txt` already is.

## How this page is kept

One page. A session adds a candidate row only when the owner asked for the proposal; the proposal file carries the argument, the row carries the status. When a candidate ships, its row moves under a "Done" heading with the change id and the plugin version.
