# Session of 2026-10-13 on branch `claude/compare-battle-tested-repo-tfqp6p` — the ArtCraft study, A1's proposal, the A3 prompt, A2 narrowed

**Builds on:** `docs/handoffs/sessions/2026-10-13-ccr-0dad187c-vi8sc0.md` (the newest file, which builds on `2026-10-13-ccr-7da93fc5-33f691.md` and, through it, `2026-10-13-session-26.md`). No other session file exists on `main` at `9b864ab` (verified with `ls docs/handoffs/sessions/` after a rebase onto `origin/main`).

This session ran the ArtCraft-versus-framework study at the owner's request. It ran in parallel with the sessions of `ccr-7da93fc5-33f691` and `ccr-0dad187c-vi8sc0`; the second of them ran this session's A1 prompt. Only `luissiviero/sdlc-framework` was in scope, plus read-only clones of the nine public `storytold` repositories; the sample was not read.

## Where the project stands
- Plugin **0.3.7** on `main`, the newest tag `v0.3.7`, the root pin **0.3.6**: carried from `2026-10-13-ccr-0dad187c-vi8sc0.md`, not re-verified.
- Merged since the file this builds on (verified, `git log origin/main` at `9b864ab`): #176 (that session's file and R6's id annotation); #178 (the owner's edit of `HANDOFF.md` line 27: a figure that differs from the file it builds on names the evidence that moved it, from this session's A2 row 4, verified on `main`).
- **This session's work on `main`:** the study record `docs/reviews/2026-10-13-artcraft-vs-framework.md` and its six evidence files, the proposal `docs/proposals/drive-target-and-proof.md` (A1, since accepted as R14 by the other session) and the A1 prompt, all through PR #169 (merged through #171).
- **This session's work in PR #175, open:** the A3 starting prompt `docs/handoffs/2026-10-13-a3-ratchet-prompt.md`; A2 narrowed (annotations on rows A2 and G3 of the record); R10's proposal annotated with the verifier's "Not exercised" section (A2 row 5, accepted by the owner); this file.
- **The ArtCraft rows and where each stands:**

| Row | Where it stands |
|---|---|
| A1 the drive target and the plan's Proof | Accepted as R14; intent change 0004, PR #173, waits for R10 (carried) |
| A2 every figure says how it was obtained | Narrowed and accepted; no proposal of its own. The residue lands in T27 and T28 (model judgments labelled), T30 (an estimate shows its inputs), `HANDOFF.md` line 27 (done, #178) and R10 (the "Not exercised" section, annotated) |
| A3 the bar is lowered only by the owner | Prompt ready (PR #175); not checked yet |
| A4 to A10 | Recorded in the study (section 8.1); not broken down, not accepted |

## Preconditions of the moment
The standing ones are in `HANDOFF.md`. Carried from `2026-10-13-ccr-0dad187c-vi8sc0.md`, not re-verified: both repositories in scope for the item-11 read; `main` at or after `9b864ab`, plugin 0.3.7, newest tag `v0.3.7`, root pin 0.3.6; the sample frozen until the 1.0.0 read (choice 138).

## Next steps, in order
1. **2026-10-14, after about 12:40 UTC: the item-11 session.** Carried, unchanged.
2. **After the read: the sandbox proof.** Carried, unchanged.
3. **The 0.3.8 runs PR.** Carried, unchanged.
4. **Then the 2026-10-09 order:** R7, R5, R6 and R10, the carried gaps, R9 part 1; R8 after R7 on two changes; then R11, then R12 and R13 together. Carried, unchanged.
5. **R14 after R10.** Carried: the owner corrects and merges PR #173 at gate (a) once R10 is built.
6. **The A3 session, in parallel, any time.** Start a new session with the prompt in PR #175, read from its branch until it merges. Part 1 is documentation only and needs no read of the sample. Part 2 drafts an intent: its change id comes from `plugin/state` at that moment, the next after 0004.
7. **After the read: the owner's triage** of the sample's #55, #56, #57, then the stale sample branches. Carried.
8. **After the read: the study's next proposal batch** (T17, T19, T27, T28). Carried. T27 and T28 now also carry A2's labelled model judgments, beside R14's per-item Proof line.
9. **When the owner wants them: A4 to A10 broken down** one by one, as A1 to A3 were, each with its sources re-read before the breakdown.

## Every open item
| Item | Where | What is left | Who acts | Blocks 1.0.0 |
|---|---|---|---|---|
| PR #175 (the A3 prompt, A2's annotations, R10's annotation, this file) | framework | Merge | owner | no |
| The A3 session | framework | Part 1 (`a3-revision.md`, reviewed), the owner's answers, Part 2 (`docs/proposals/ratchets.md`, the ROADMAP row, the intent) | a session, then the owner | no |
| A4 to A10 of the ArtCraft study | framework | Breakdown and acceptance, one at a time | the owner chooses when | no |
| A2's residue in T27, T28 and T30 | framework | Written into those entries' proposals when they are written | a study session | no |
| Item 11, the read and the 1.0.0 bump | both | Carried: 2026-10-14 after about 12:40 UTC | a session, then the owner | yes |
| Sandbox proof, then the pin to the newest tag | framework | Carried | a session, then the owner's pin row | no |
| 0.3.8 runs PR | framework | Carried | a session | no |
| R7, R5, R6, R10, the carried gaps, R9 part 1, R8 | framework | Carried | sessions; the owner reviews | no |
| R14, change 0004 (PR #173) | framework | Carried: waits for R10, then gate (a) | owner | no |
| R14's per-item Proof line on the PR | framework | Carried: rides T27's proposal | a study session | no |
| `sdlc-test.md:82-84` prose on the screenshots README | framework | Carried: fixed by R14's build | the R14 build | no |
| `ux-conventions/check.py` image path | framework | Carried: a one-line fix with a test in any 0.3.x PR | a session | no |
| The PR body counting `.gitkeep` as a screenshot | framework | Carried: fixed by R14's build | the R14 build | no |
| `docs/PROGRESS.md` rewritten by every session | framework | Carried: the owner decides | owner | no |
| Sample PRs #55, #56, #57 | sample | Carried: triage at gate (f) after the read | owner | no |
| Merged branches left on origin | framework | Carried. *Corrects `2026-10-13-ccr-0dad187c-vi8sc0.md`, the row "Merged branches left on origin": `claude/compare-battle-tested-repo-tfqp6p` is not a merged branch to delete while PR #175 is open; it joins the list once #175 merges* | owner | no |
| 18 stale sample branches | sample | Carried | owner | no |
| R2's tables | framework guardrails | Carried | owner | no |
| Windows sitting | owner's PC | Carried | owner | no |
| Study batch T17, T19, T27, T28 | framework | Carried: after the read (choice 181) | a study session | no |
| The study's line R11, then R12 + R13 | framework | Carried | sessions draft; the owner merges | no |

Done since the file this builds on, dropped from the table: that session's last PR (#176, merged); the A2 row-4 sentence in `HANDOFF.md` (#178, the owner's edit).

## What the owner does
| When | Act |
|---|---|
| Now | Merge PR #175 (approve its bot-started runs first). |
| Any time, in parallel | Start the A3 session with the prompt in PR #175; answer its Part 1 row by row. |
| 2026-10-14, about 12:40 UTC | Carried: check the sample's detect run and start the item-11 session with both repositories in scope. |
| After the item-11 PR | Carried: merge it; check `v1.0.0`; both pin rows; the sample's upgrade PR; the Milestone. |
| When R10 is built | Carried: read, correct and merge PR #173 at gate (a). |
| A fix round parks on the cap | Carried: post the review first, then `sdlc:reset-iterations` within the same minute. |
| Before merging any PR | Carried: approve the bot-started runs on the final head; merge only when every job is green. |
| Any time | Carried: the merged branches on origin; R2's tables; the Windows sitting; whether `docs/PROGRESS.md` follows the handoff into the session file; when to break down A4 to A10. |
