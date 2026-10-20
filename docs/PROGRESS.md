# Progress — change 0004's open questions: four answered by the owner (choice 246), the rest registered for R14's turn (2026-10-20)

This session ran on branch `ccr-d6ff91d5-syonv1`, after #297 merged. The owner's tasks:
- recall what #173 (the intent of change 0004, R14) works on, whether it is obsolete, and when it comes back;
- say whether to answer its five open questions now and whether to refresh the intent now;
- register everything left for later.

The previous record (R64 registered, choice 245) is now `docs/progress/2026-10-20-r64-registered-choice-245.md`, unchanged. The session's file is `docs/handoffs/sessions/2026-10-20-ccr-d6ff91d5-syonv1.md`.

No change under `plugin/` or `template/` in this PR, so no version bump.

## Summary
- **Choice 246**: the owner answered four of the intent's open questions as recommended in `docs/reviews/2026-10-20-0004-open-questions.md`: Q1, Q4, Q5 and the first half of Q3.
- **Left for R14's turn and registered** in the same file:
  - Q2 (the job timeouts), after R25 and R44;
  - the second half of Q3 (the `proof` entry's shape under R11's record rules), after R11, which is on hold;
  - the intent's refresh, with the ten items it needs.
- **ROADMAP annotations**: the R14 row points to the file. The R33 row carries Q4's shared detection helper, since R33 (rank 17) is built before R14 (rank 18).

## The owner's decision (2026-10-20)
246. **Q1, Q4, Q5 and the first half of Q3 of change 0004's intent are answered as recommended** (the owner, "Q1, Q4, Q5 and Q3a as recommended"). Each answer is in its row of `docs/reviews/2026-10-20-0004-open-questions.md`:
    - **Q1**: `evidence/proof/` belongs to the runner's step. Only `commands.drive` writes it, the step clears it before each run, and it is the only folder the gate checks and the plan's `screenshot:` items name. `evidence/screenshots/` stays the (d) session's by-hand folder, which the gate never checks.
    - **Q3, first half**: the per-item result is a `proof` entry of its own in the gate record, beside `commands`.
    - **Q4**: `@playwright/test` is detected in `dependencies` and in `devDependencies`, through one helper in `plugin/init/detect.py` that R33 builds and R14 reuses.
    - **Q5**: with `commands.drive` set, `/sdlc-test` step 3 compares (c)'s `proof/` images with the mock instead of capturing by hand; with it empty, step 3 stays as today.

    The intent on `sdlc/0004/a` is not edited now. The answers go into its Proposed outcome at R14's turn, with its refresh (item 2 of the file's list).

## Left
- **Q2 and the second half of Q3**, at R14's turn (the file's items 3 and 4).
- **The intent's refresh**, at R14's turn (the file's items 1 to 10). The owner merges #173 only after it, since the merge starts the design run.
- **R33's build** reads choice 246's Q4 before it builds the detection.

## The port list
This PR touches no file of the port list's paths.

## Proposed edits for the owner
None.

## Checks (this repository)
On the final head: `python -m compileall -q plugin tests tasks.py`, `python -m pytest`, `python -m ruff check .`, `python -m ruff format --check .` and `python tasks.py docs-lint`. Their output is in the PR.
