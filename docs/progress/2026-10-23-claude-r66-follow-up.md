# Progress — R66's follow-up: four points from the closed #353 (choice 265) (2026-10-23)

This session ran on branch `claude/r66-follow-up`, built on #354's branch (`ccr-9171b99a-q6u17y` at `3a540ef`, which holds `main` at `0733b8c`), so #354 merges first. It changes `tasks.py` and its tests and four documentation files; no file under `plugin/` or `template/`, no plugin version.

## The owner's choices
265. **#354 is the version kept, with four points of #353 as a follow-up** (the owner, 2026-10-23, session `claude/parallelism-inventory`: "#354 with those 4 points after follow-up", after a table comparing #353 and #354). #353 is closed. The four points:
   - (1) the coordinator's relay never starts a comment with `@claude`: a dated annotation on R66's part 3;
   - (2) the conflict at the base update before gate (e) resolved by a fix round instead of a park, decided on the trial's measure: point 5 of R66's "What to settle";
   - (3) R28's manager reading the changes in flight, as the alternative to the coordinator reading `evidence/manager.md`: point 6;
   - (4) `docs/handoffs/central-session.md:38`'s claim corrected by a dated annotation, and `python tasks.py version-check` failing a patch that a fetched open branch bumped to first.

## What was built
1. **`tasks.py` `version-check`** (`_open_branch_problems`, `_bump_key`, `_is_ancestor`): for each fetched branch ahead of `main` that bumps to the same version, the branch whose bump came first (committer time of its first commit holding the version) keeps it. The later one fails with "the branch bumps to X, which <branch> took first", and the earlier one gets the report "X is also taken by <branch>, later: that branch renumbers". A branch built on this one, or one it is built on, is skipped. Four tests in `tests/test_version_check.py` (the later fails, the earlier is told, a stacked branch shares the bump). Live, read at 12:30 UTC on `0733b8c`: on `claude/forged-release-ref` it fails 1.0.31, which `claude/r61-r33-trial-shape-formatter` took first; on the latter it reports the clash and passes.
2. **`docs/proposals/changes-in-flight-coordinator.md`**: the relay guard beside part 3's relay bullet; points 5 and 6 under "What to settle before building".
3. **`docs/ROADMAP.md` R66**: one dated annotation naming the three additions.
4. **`docs/handoffs/central-session.md:38`**: a dated annotation that says what each check refuses, and when.

## Limits
- CI checks out the pull request alone, so `version-check` sees no other branch there; it acts on a session's `verify` after `git fetch origin`. Choice, note and candidate numbers still have only `next-free` before a merge.
- `HANDOFF.md`'s description of `version-check` (standing precondition 1) is not changed: it is a stable page changed in a PR of its own. Proposed for that PR: "a branch that bumps the plugin to a version `main` holds, a tag has or a fetched open branch took first fails".

## Carried from #353 (closed), not in #354
- `docs/proposals/weekly-window-guarded.md:110` says "the framework runs one change at a time", which the per-branch concurrency groups contradict (`template/.github/workflows/sdlc-build.yml:52-54`). A dated annotation is due in a documentation PR.

## What the owner does
| When | Act |
|---|---|
| After #354 merges | Merge this PR when `Framework checks` is green on its final head. |
