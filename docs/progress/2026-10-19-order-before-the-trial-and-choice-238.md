# Progress — the Order before the real-project trial: R44 forward, R45 last before the trial, R28 after it, and the owner's choice 238 (2026-10-19)

This session ran on branch `ccr-8d38a8f0-6nj6hz`, from the owner's questions of 2026-10-19 on the full roadmap: would the order be rearranged, and what is free to start beside the work already running. The owner then accepted the three moves the session proposed (choice 238). The previous record (the framework's own checks, faster, part 4: the git lookups remembered, plugin 1.0.13, choice 235 item 5, PR #251, from the parallel session `ccr-eb707371-rh6z2g`, which merged while this PR was open) is now `docs/progress/2026-10-19-framework-checks-faster-part-4-git-lookups-1.0.13.md`, unchanged; #251 archived the one before it (R55 and choice 237, PR #249) as `docs/progress/2026-10-19-r55-docs-lint-and-choice-237.md`. The session's own file is `docs/handoffs/sessions/2026-10-19-ccr-8d38a8f0-6nj6hz.md`.

No change under `plugin/` or `template/`; no version bump.

## Summary
- **R44 moves from rank 28 to 12**, after R51 and R25 parts 1-2. Two of the sample's open scan incidents are R44's own gaps: #56 (`sandbox.failIfUnavailable` is false) and #57 (the deny list blocks only the Edit tool, not shell writes). At rank 28 the trial project would have run with them and a real credential. R44's first step, the sandbox proof, has been carried before rank 7 since 2026-10-13 and is still not done.
- **R45, the rename, stays at rank 20 and is now the last change before the real-project trial.** The trial project starts with the final phase, label and branch names and is never migrated. The decision table of 2026-10-15 (`docs/handoffs/2026-10-15-decision-table-r21-r45.md`, line 10) put the rename last before the trial for the same reason. R57 and R2's folder name already wait on R45.
- **R28 moves from rank 19 to 21, the first change after the trial.** Choice 234 says it adds model time, and its cost question is open. After the trial, the trial's speed and spend (R25, R26) measure the pipeline without it and give the baseline it is judged against.
- **The other ranks keep their relative order**: 12 to 18 move down by one (R18, R29 part 1 with R54, R26, R52, R33, R14, R27), as do 21 to 27 (R5, R6, R11, R12 with R13, R36, R21, R30). Every moved cell keeps its previous value beside the new one; the Order column's opening note and `docs/proposals/llm-wiki-adoption.md` (the trial "after R28, rank 19") are annotated.
- **Two corrections to the roadmap summary the owner pasted** (not to ROADMAP, which already holds both): R15's first change is done (change 0005, plugin 1.0.2, PR #211, 2026-10-17), and rank 32 is R15's second change, not a gap.

## The owner's decisions (2026-10-19)
238. **The Order before the real-project trial** (the session's three recommendations; the owner, "I agree with the changes you proposed"):
    - R44 at rank 12, after R51 and R25 parts 1-2 and before the trial; this answers the pending R44 timing question;
    - R45 at rank 20, the last change before the trial; its names are still decided in a documentation PR before the rename;
    - R28 at rank 21, the first change after the trial; its timing is answered, its cost question stays pending;
    - every other rank keeps its relative order.

## Proposed edits for the owner
None: no guardrail line changes in this PR.

## Left
- **What is free to start** (the session's reading on `main` at `22d99fc`, amended on `b1ae336`; not a decision): R7 (rank 7); the decision files of R24 and R22 (ranks 8 and 9), documentation PRs, numbered before they are written so two parallel PRs do not both take 35; and a read of what "the runs PR" still holds after plugins 1.0.3 to 1.0.13. R51 waited for choice 235's item 5, whose id reservation goes through `plugin/state/cli.py` and `gitops`; item 5 merged as #251 (plugin 1.0.13), so R51 now builds on `gitops.remembered` and must keep its cache correct across the reservation's push.
- **R30 is at rank 28, after the trial**, while the decision table of 2026-10-15 marked it "**Now** (before the trial's `/sdlc-init`)". Not moved: the owner was not asked. A question for the owner.
- **The sample's scan incidents #55, #56 and #57** are still open, waiting for the owner's triage since 2026-10-05 and 2026-10-12. Two of them are R44's gaps.

## Checks (this repository)
On the final head, after `python -m pip install -e ".[dev]"`, chained with `set -o pipefail`: the four commands of `HANDOFF.md`'s standing precondition 1, plus `python tasks.py docs-lint`. Their output is in the PR.
