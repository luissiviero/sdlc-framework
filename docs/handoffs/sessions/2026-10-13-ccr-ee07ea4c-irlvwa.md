# Session of 2026-10-13 on branch `ccr-ee07ea4c-irlvwa`: the ArtCraft study's batch `ci` (A5, A10), Part 1

**Builds on:** `docs/handoffs/sessions/2026-10-13-claude-compare-battle-tested-repo-tfqp6p.md`, the newest file. It builds on `2026-10-13-ccr-0dad187c-vi8sc0.md` and, through that, on the two before it. No other session file exists on `main` at `3efb45f` (verified with `ls docs/handoffs/sessions/`).

This session ran the starting prompt `docs/handoffs/2026-10-13-artcraft-rows-prompt.md` for batch **ci**, which the owner chose as "one of the batches not yet started". No PR or other session had started any of the three: verified with `list_pull_requests` and `list_sessions`. Only `luissiviero/sdlc-framework` was in scope, plus a read-only sparse clone of photocraft.

## Where the project stands
- Plugin **0.3.7** on `main` (verified, `.claude-plugin/plugin.json:4`). Newest tag `v0.3.7` and root pin 0.3.6 are carried from the file this builds on, not re-verified.
- Merged since the file this builds on (verified, `git log --merges` to `3efb45f`):
  - #175 (the A3 prompt and A2's annotations);
  - #177 (A3's revision);
  - #181 (the rows prompt);
  - #179 (A3 accepted as ROADMAP **R15**, `docs/proposals/ratchets.md`);
  - #180 (R15's first change, **0005**, its intent merged at gate (a)).
- **This session's work, in this branch's PR:** `docs/reviews/2026-10-13-artcraft-vs-framework/ci-revision.md`, independently reviewed. It waits for the owner's answers to C1 to C7. Its findings:
  - A5 is mostly overtaken: the notes index has been checked in CI since PR #160. What is left is one test for this repository's own `lessons/index.md`.
  - A10's real gap is that `main` runs cancel each other. The merge that shipped `v0.3.6` (`eca1af2`) has its run #279 `cancelled`, and run #450 on `a92a022` was cancelled too.
  - Windows can be skipped on documentation-only PRs, about half the merges.
- **The ArtCraft rows:**

| Row | Where it stands |
|---|---|
| A1 | Accepted as R14; change 0004, PR #173, waits for R10 (carried) |
| A2 | Narrowed and accepted; residue in T27, T28, T30 and R10 (carried) |
| A3 | Accepted as R15 (#179); change 0005's intent merged (#180). The state of its design run was not read |
| A5, A10 | Done here (Parts 1 and 2, PR #184). The owner accepted every recommendation of `ci-revision.md` (C1, C3, C4, C6, C7; C2 and C5 rejected), and the record's rows A5, A10 and G5 are annotated. The code waits for a plain PR the owner asks for |
| A7, A8, A9 (batch `templates`) | Not started |
| A4, A6 (batch `planning`) | Not started |

## Preconditions of the moment
The standing ones are in `HANDOFF.md`. Carried from the file this builds on, not re-verified: both repositories in scope for the item-11 read; tags and pin as above; the sample frozen until the 1.0.0 read (choice 138). `main` at or after `3efb45f`.

## Next steps, in order
1. **2026-10-14, after about 12:40 UTC: the item-11 session.** Carried, unchanged.
2. **After the read: the sandbox proof.** Carried.
3. **The 0.3.8 runs PR.** Carried.
4. **Then the 2026-10-09 order:** R7, R5, R6 and R10, the carried gaps, R9 part 1; R8 after R7; then R11, then R12 and R13. Carried.
5. **R14 after R10** (PR #173). Carried.
6. **R15's change 0005 continues through its phases.** Its intent merged in #180; not read further here.
7. **Batch `ci`'s plain PR, when the owner asks for it** (no change id, no bump; `tests/` and `.github/` only), in the CI-speed line of PR #167:
   - C1: one layer-2 test, `les.check(ROOT)` in `tests/test_lessons.py`;
   - C3: `cancel-in-progress: ${{ github.event_name == 'pull_request' }}` in `framework-checks.yml`;
   - C4: a separate Windows job with a job-level `if:` from a `.github/scripts/` file and its test, skipping only when every changed path is `docs/**`, `HANDOFF.md` or `README.md`. This comes after the owner's ruleset check and `HANDOFF.md` edit (`ci-revision.md` section 7);
   - C6: `framework-evals.yml` PR runs keyed by PR number and cancelled when superseded, the nightly run never.
8. **Batches `templates` and `planning`:** one session each, with the same prompt, changing the batch name on its first line.
9. **After the read:** the owner's triage of sample PRs #55, #56 and #57, then the stale sample branches. Carried.
10. **After the read: the study's next proposal batch** (T17, T19, T27, T28). Carried.
11. **The CI-speed line's step 2** (prebuilt fixture repositories), and step 3 only if still needed. Carried from `docs/PROGRESS.md`, not re-verified. C4, if accepted, removes most of step 3's reason on documentation-only PRs.

## Every open item
| Item | Where | What is left | Who acts | Blocks 1.0.0 |
|---|---|---|---|---|
| Batch `ci` (this PR) | framework | Merge | owner | no |
| Batch `ci`'s plain PR (C1, C3, C4, C6) | framework `tests/`, `.github/` | Build when the owner asks. C3 first: `main` runs cancel each other, so tags can name unchecked commits | owner asks; a session builds | no |
| `HANDOFF.md` standing precondition 1, for C4 | framework guardrail | The owner's edit (`ci-revision.md` section 7), after checking whether ruleset 24077592 requires the Windows job | owner | no |
| Batches `templates` (A7, A8, A9) and `planning` (A4, A6) | framework | Part 1 each | the owner chooses when | no |
| R15, change 0005 | framework | Its phases after gate (a) | the pipeline; owner at gates | no |
| A2's residue in T27, T28 and T30 | framework | Carried | a study session | no |
| Item 11, the read and the 1.0.0 bump | both | Carried: 2026-10-14 after about 12:40 UTC | a session, then the owner | yes |
| Sandbox proof, then the pin to the newest tag | framework | Carried | a session, then the owner's pin row | no |
| 0.3.8 runs PR | framework | Carried | a session | no |
| R7, R5, R6, R10, the carried gaps, R9 part 1, R8 | framework | Carried | sessions; the owner reviews | no |
| R14, change 0004 (PR #173) | framework | Carried: waits for R10, then gate (a) | owner | no |
| R14's per-item Proof line on the PR | framework | Carried: rides T27's proposal | a study session | no |
| `sdlc-test.md:82-84` prose on the screenshots README | framework | Carried: fixed by R14's build | the R14 build | no |
| `ux-conventions/check.py` image path | framework | Carried: a one-line fix with a test | a session | no |
| The PR body counting `.gitkeep` as a screenshot | framework | Carried: fixed by R14's build | the R14 build | no |
| CI-speed line, steps 2 and 3 | framework | Carried from `docs/PROGRESS.md` | a session | no |
| `docs/PROGRESS.md` rewritten by every session | framework | Carried: the owner decides | owner | no |
| Sample PRs #55, #56, #57 | sample | Carried: triage at gate (f) after the read | owner | no |
| Merged branches left on origin | framework | Carried. `claude/compare-battle-tested-repo-tfqp6p` and `ccr-c6d8a9c3-3s7q61-part2` now join the list: their PRs #181 and #179 are merged | owner | no |
| 18 stale sample branches | sample | Carried | owner | no |
| R2's tables | framework guardrails | Carried | owner | no |
| Windows sitting | owner's PC | Carried | owner | no |
| Study batch T17, T19, T27, T28 | framework | Carried: after the read (choice 181) | a study session | no |
| The study's line R11, then R12 + R13 | framework | Carried | sessions draft; the owner merges | no |

Done since the file this builds on, dropped from the table: PR #175 (merged); the A3 session (#177 and #179 merged, A3 accepted as R15, intent #180 merged).

## What the owner does
| When | Act |
|---|---|
| Now | Merge PR #184 (C1 to C7 answered: every recommendation accepted). |
| When you want the CI changes | Ask a session for batch `ci`'s plain PR. Before its C4 part: check whether ruleset 24077592 on `main` requires `check (windows-latest, 3.12)` by name, and make the `HANDOFF.md` edit of `ci-revision.md` section 7. |
| Any time | Start the `templates` or `planning` batch session with the rows prompt. |
| 2026-10-14, about 12:40 UTC | Carried: check the sample's detect run and start the item-11 session with both repositories in scope. |
| After the item-11 PR | Carried: merge it; check `v1.0.0`; both pin rows; the sample's upgrade PR; the Milestone. |
| When R10 is built | Carried: read, correct and merge PR #173 at gate (a). |
| A fix round parks on the cap | Carried: post the review first, then `sdlc:reset-iterations` within the same minute. |
| Before merging any PR | Carried: approve the bot-started runs on the final head; merge only when every job is green. |
| Any time | Carried: the merged branches on origin; R2's tables; the Windows sitting; whether `docs/PROGRESS.md` follows the handoff into the session file. |
