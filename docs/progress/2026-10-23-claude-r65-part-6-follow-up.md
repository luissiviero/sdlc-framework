# Progress — R65's part 6, follow-up: the independent review's findings, plugin 1.0.33 (2026-10-23)

This session ran on branch `claude/r65-part-6-follow-up`, from `main` at `b6800ff` (#358), as the small lane beside wave 2. R65's part 6 (`docs/progress/2026-10-23-claude-r65-part-6-stale-comments.md`) merged as #358 before its independent review reported. This PR carries the review's fixes, so the lane's rule (an independent review on items 1 and 3, fixed with tests) is met on `main`. It takes 1.0.33, the number `python tasks.py next-free` gave on `b6800ff`; no choice, note or decision number is taken.

## The version on `main`
#355 (lane A's follow-up) merged 1.0.32 and was tagged `v1.0.32` at its merge, `69f2679`; #358 then merged with the same number in `plugin.json`, so `main` at `b6800ff` holds part 6's code under a version its tag does not contain. This PR's 1.0.33 gives that code a number of its own.

## The fresh-context review
A fresh-context sub-agent reviewed part 6 (report only) and found nothing blocking. Every rewritten pointer holds its fact (`2.md`; `10.md`, 10b; `3.md`, 3a; `8.md`; `12.md`; `51.md`), and S8, S12 and S15 are fixed. Its findings and what was done:
1. **Medium, fixed:** `pr/digest.py` (`UNPROTECTED` and `unprotected_notice`), `pr/github.default_branch_protection` and `gate/policy.py` still said decision 4 as "only the owner merges", with only the repository admin in the ruleset's bypass list. Decision 36 amends it (`docs/decisions/4.md:11`): the merge App merges on the owner's approving review and is the ruleset's second bypass actor. The digest's warning, which the owner acts on, now says to add the merge App in "For pull requests only" mode; the other two say decision 36.
2. **Low, fixed:** `run_phase.CLI_MODEL_NEED`, which part 6 reformatted, said "the framework's NOTES §54"; it now names `docs/notes/54.md`. The "NOTES §N" shorthand elsewhere under `plugin/` is left: the study scoped S15 to `docs/NOTES.md`, and the repository's own documents use the shorthand.
3. **Low, fixed:** `hooks/_common.py` now points at `docs/notes/1.md` for the input and the exit codes, and `8.md` for the output contract.
4. **Low, fixed:** the sentence `spec-template` tells the design pass to write ends "(at (e), the owner's approving review)", since the gate reads a declared item at every gate and the build PR's banner shows it too.
5. **Low, fixed:** check 5's pattern had no left boundary and matched `RELEASE_NOTES.md`; it now does not; the test has the case.
6. **Low, fixed:** the CLI park's test checks the version reaches "What I need from you".
7. to 10. Info: the lazy import follows the file's pattern; the check's encoding, paths and speed hold; S8, S12 and S15 confirmed. Recorded.

## Port list (HANDOFF.md, "Rules for every session")
This PR touches `plugin/ci/run_phase.py` (`CLI_MODEL_NEED`), so it goes on the port list until the 1.0.0 read.

## Proposed edits for the owner
None.

## What the owner does
| When | Act |
|---|---|
| Now | Merge this PR when `Framework checks` is green on its final head. |
