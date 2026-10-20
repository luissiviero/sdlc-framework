# Progress — docs-lint check 8 reports a merge claim that may be another repository's (choice 247) (2026-10-20)

This session ran on branch `ccr-d6ff91d5-syonv1`, restarted from `main` at `2f37723` after #298 merged. The previous record (choice 246) is now `docs/progress/2026-10-20-0004-open-questions-choice-246.md`, unchanged. The session's file is `docs/handoffs/sessions/2026-10-20-ccr-d6ff91d5-syonv1.md`.

No change under `plugin/` or `template/` in this PR, so no version bump.

## Summary
- **Choice 246's aftermath**: `main` went red at #299's merge (`899aa08`; framework-checks run 39476793986).
  - Docs-lint check 8 (choice 241) read "its #88 … merged as `656eadd`" in `docs/handoffs/sessions/2026-10-20-ccr-0522ec37-iia2ok.md:8` as this repository's PR #88, whose merge commit is `5fdd4eb`. That #88 is the sample's PR.
  - The check skipped a claim only when "sample" stood within 40 characters before the number; here it stood further back.
  - #300 reworded the line, and #298 carried the same one-line change.
- **Choice 247**: check 8 itself is fixed, in `tasks.py` with two tests. It is not a ROADMAP candidate: it is this repository's tooling, built as checks 8 and 9 were (choices 241 and 243).

## The owner's decision (2026-10-20)
247. **Docs-lint check 8 reports, never fails, a merge claim that may be another repository's** (the owner, "yes, fix check 8", on the session's recommendation). A claim counts as possibly another repository's in two cases:
    - the commit it quotes is not a commit of this repository (`git cat-file -e`, through `commit_lookup` in `tasks.py`);
    - "sample" stands earlier in the claim's sentence, beyond the 40 characters the check already skipped.

    Such a claim's mismatches go to the reports, with "(another repository's PR?)". The two repositories' PR numbers overlap (the sample's #1 to #91, this repository's up to #300), so a sample claim the check misread turned `main` red and every open PR with it.

    The trade-off, stated with the recommendation: a framework claim that quotes a commit which does not exist (a typo) is reported, not failed. A claim that quotes a real commit of this repository other than the merge commit (a PR's head, say) still fails.

## Left
- **Q2, the second half of Q3 and the intent's refresh of change 0004**: at R14's turn, as choice 246's record says (`docs/reviews/2026-10-20-0004-open-questions.md`).

## The port list
This PR touches no file of the port list's paths.

## Proposed edits for the owner
None.

## Checks (this repository)
On the final head: `python -m compileall -q plugin tests tasks.py`, `python -m pytest`, `python -m ruff check .`, `python -m ruff format --check .` and `python tasks.py docs-lint`. Their output is in the PR.
