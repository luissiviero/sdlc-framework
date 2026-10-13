# Session of 2026-10-13 on branch `ccr-bddc73de-kyyw0b`: the ArtCraft study's batch `templates` (A7, A8, A9), Part 1

**Builds on:** `docs/handoffs/sessions/2026-10-13-ccr-ee07ea4c-irlvwa.md`, the newest file. It builds on `2026-10-13-claude-compare-battle-tested-repo-tfqp6p.md` and, through that, on the files before it. `2026-10-13-ccr-c6d8a9c3-3s7q61.md` is not named in its header and is not older than the file it names, so it was read too (HANDOFF step 3); its open items are carried below. No other session file exists on `main` at `ca0a5bb` (verified with `ls docs/handoffs/sessions/`).

This session ran the starting prompt `docs/handoffs/2026-10-13-artcraft-templates-prompt.md` for batch **templates**. No PR had started it (verified with `list_pull_requests`, the 15 newest PRs of every state). Only `luissiviero/sdlc-framework` was in scope, plus read-only sparse clones of filmcraft `cee1feb`, pdfcraft `3f044b6` (the study's `7437bde` read after a deeper blobless fetch) and effectcraft `549e9d8`.

## Where the project stands
- Plugin **0.3.7** on `main` (verified, `.claude-plugin/plugin.json:4`); root pin **0.3.6** (verified, `sdlc.yaml:98`). Newest tag `v0.3.7`: carried from `2026-10-13-ccr-ee07ea4c-irlvwa.md`, not re-verified. This session changed nothing under `plugin/`, `template/` or `.github/`.
- `main` is at `ca0a5bb` (verified, `git fetch origin main`): PR #184 (batch `ci`, Parts 1 and 2) is merged since the file this builds on.
- Open PRs seen: #186 (change 0005's design PR, `sdlc/0005/b`, not read) and #173 (change 0004's intent, carried).
- **This session's work, in this branch's PR:** `docs/reviews/2026-10-13-artcraft-vs-framework/templates-revision.md`, independently reviewed. It waits for the owner's answers to E1 to E9. Its findings:
  - A7 is mostly covered already: flagged concerns, the panel's "Decisions taken for you", "Options not taken", departures under Risks. The residue is one line for phase (c).
  - A8 confirms T11 (not built). Its extension has nothing to read.
  - A9's sources rank regressions sixth and second, not first. The residue is an `incident`-first sort key in T28.
- **The ArtCraft rows:**

| Row | Where it stands |
|---|---|
| A1 | Accepted as R14; change 0004, PR #173, waits for R10 (carried) |
| A2 | Narrowed and accepted; residue in T27, T28, T30 and R10 (carried) |
| A3 | Accepted as R15; change 0005's intent merged (#180), its design PR #186 open (not read) |
| A5, A10 | Done (PR #184). The code waits for a plain PR the owner asks for (carried) |
| A7, A8, A9 (batch `templates`) | Part 1 done here; waits for the owner's answers E1 to E9 |
| A4, A6 (batch `planning`) | Not started |

## Preconditions of the moment
The standing ones are in `HANDOFF.md`. Carried from `2026-10-13-ccr-ee07ea4c-irlvwa.md`, not re-verified: both repositories in scope for the item-11 read; the tag as above; the sample frozen until the 1.0.0 read (choice 138). `main` at or after `ca0a5bb`.

## Next steps, in order
1. **2026-10-14, after about 12:40 UTC: the item-11 session.** Carried, unchanged.
2. **After the read: the sandbox proof.** Carried.
3. **The 0.3.8 runs PR.** Carried.
4. **Then the 2026-10-09 order:** R7, R5, R6 and R10, the carried gaps, R9 part 1; R8 after R7; then R11, then R12 and R13. Carried.
5. **R14 after R10** (PR #173). Carried.
6. **R15's change 0005:** its design PR #186 waits at gate (b) or has parked (not read here). Carried from `2026-10-13-ccr-c6d8a9c3-3s7q61.md`: before its build, the owner places its version against item 11 and the 0.3.8 runs PR.
7. **R15's second change after R10** (the measured counts). Carried from `2026-10-13-ccr-c6d8a9c3-3s7q61.md`.
8. **Batch `ci`'s plain PR when the owner asks for it** (C1, C3, C4, C6). Carried.
9. **Batch `templates` Part 2**, on this PR, after the owner answers E1 to E9: annotations only (T2, T11, T28 and the record's rows A7, A8, A9 and G7). If E2 is accepted, its plain PR (one line in `plan-template` and in `sdlc-build.md`, with a version bump) waits until the owner asks for it.
10. **Batch `planning` (A4, A6):** one session, from the rows prompt with the same additions. Carried.
11. **After the read:** the owner's triage of sample PRs #55, #56 and #57, then the stale sample branches; the study's next proposal batch (T17, T19, T27, T28); the CI-speed line's steps 2 and 3. Carried.

## Every open item
| Item | Where | What is left | Who acts | Blocks 1.0.0 |
|---|---|---|---|---|
| Batch `templates` (this PR) | framework | The owner's answers E1 to E9, then Part 2 on this PR, then merge | owner, then this session | no |
| Batch `templates`' plain PR (E2, if accepted) | framework `plugin/` | One rule line in `plan-template` and `sdlc-build.md` step 2, with a version bump | owner asks; a session builds | no |
| Batch `ci`'s plain PR (C1, C3, C4, C6) | framework `tests/`, `.github/` | Carried: build when the owner asks; C3 first | owner asks; a session builds | no |
| Batch `planning` (A4, A6) | framework | Part 1 | the owner chooses when | no |
| R15, change 0005 | framework | Carried: design PR #186 at gate (b), then the build with a version bump | the pipeline; owner at gates | no |
| Change 0005's version slot | framework | Carried from `2026-10-13-ccr-c6d8a9c3-3s7q61.md` | owner | no |
| The root `REVIEW.md` line for the skip-marker list | framework guardrails | Carried from `2026-10-13-ccr-c6d8a9c3-3s7q61.md`: proposed by change 0005's build | owner | no |
| The runner measures the working tree, not HEAD | framework | Carried from `2026-10-13-ccr-c6d8a9c3-3s7q61.md`: a 0.3.x fix or inside R15's second change | owner decides; a session builds | no |
| Three small defects (`sdlc-test.md:69-71`, `lesson_and_eval` loading, test globs) | framework | Carried from `2026-10-13-ccr-c6d8a9c3-3s7q61.md` | a session, any 0.3.x PR | no |
| R15's second change (the measured counts) | framework | Carried: after R10 | a session | no |
| A2's residue in T27, T28 and T30 | framework | Carried | a study session | no |
| Item 11, the read and the 1.0.0 bump | both | Carried: 2026-10-14 after about 12:40 UTC | a session, then the owner | yes |
| Sandbox proof, then the pin to the newest tag | framework | Carried | a session, then the owner's pin row | no |
| 0.3.8 runs PR | framework | Carried | a session | no |
| R7, R5, R6, R10, the carried gaps, R9 part 1, R8 | framework | Carried | sessions; the owner reviews | no |
| R14, change 0004 (PR #173) | framework | Carried: waits for R10, then gate (a) | owner | no |
| R14's per-item Proof line on the PR | framework | Carried: rides T27's proposal | a study session | no |
| `sdlc-test.md:82-84` prose on the screenshots README | framework | Carried: fixed by R14's build | the R14 build | no |
| `ux-conventions/check.py` image path | framework | Carried | a session | no |
| The PR body counting `.gitkeep` as a screenshot | framework | Carried: fixed by R14's build | the R14 build | no |
| CI-speed line, steps 2 and 3 | framework | Carried | a session | no |
| `docs/PROGRESS.md` rewritten by every session | framework | Carried: the owner decides | owner | no |
| Sample PRs #55, #56, #57 | sample | Carried | owner | no |
| Merged branches left on origin | framework | Carried; `ccr-ee07ea4c-irlvwa` joins the list (#184 merged) | owner | no |
| 18 stale sample branches | sample | Carried | owner | no |
| R2's tables | framework guardrails | Carried | owner | no |
| Windows sitting | owner's PC | Carried | owner | no |
| Study batch T17, T19, T27, T28 | framework | Carried: after the read (choice 181) | a study session | no |
| The study's line R11, then R12 + R13 | framework | Carried | sessions draft; the owner merges | no |

Done since the files this builds on, dropped from the table: batch `ci` (PR #184 merged); batch `templates` Part 1 (this PR).

## What the owner does
| When | Act |
|---|---|
| Now | Answer E1 to E9 in `templates-revision.md` section 9; this session then writes Part 2 on the same PR. |
| After Part 2 | Approve the bot-started runs on the final head; merge when every job is green. |
| When you want them | Ask a session for the plain PRs: batch `ci`'s (C1, C3, C4, C6) and, if E2 is accepted, batch `templates`' rule line. |
| When change 0005's design PR (#186) is ready | Carried: read its spec and plan at gate (b), or its park. |
| 2026-10-14, about 12:40 UTC | Carried: check the sample's detect run and start the item-11 session with both repositories in scope. |
| After the item-11 PR | Carried: merge it; check `v1.0.0`; both pin rows; the sample's upgrade PR; the Milestone. |
| When R10 is built | Carried: read, correct and merge PR #173 at gate (a); then R15's second change. |
| A fix round parks on the cap | Carried: post the review first, then `sdlc:reset-iterations` within the same minute. |
| Any time | Carried: the merged branches on origin; R2's tables; the Windows sitting; whether `docs/PROGRESS.md` follows the handoff into the session file; when to start batch `planning`. |
