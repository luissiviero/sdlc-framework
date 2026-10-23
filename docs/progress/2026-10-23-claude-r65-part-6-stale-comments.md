# Progress — R65's part 6: the stale places in comments under `plugin/` and `template/`, plugin 1.0.32 (2026-10-23)

This session ran on branch `claude/r65-part-6-stale-comments`, from `main` at `f41a336` (#349), as the small lane beside wave 2, started at the owner's request on 2026-10-23; this is its third item. The scope is choice 252 (ROADMAP R65, part 6; `docs/proposals/one-owner-per-fact.md`, item 6; `docs/reviews/2026-10-22-sources-of-truth.md`, section 3): a plugin patch of its own, started after both wave 2 PRs merged (#350, #348). This PR takes 1.0.32, the number `python tasks.py next-free` gave on `f41a336`; no choice, note or decision number is taken. Every place the study lists was re-read on `f41a336` before it was edited.

## What was built
1. **S15, the pointers at `docs/NOTES.md`:** the comments and strings that cite it are rewritten to `docs/notes/<N>.md`, with the subsection where the study's pointer had one (`10.md`, 10b; `3.md`, 3a): `gate/limits.py` (2), `hooks/protected_paths.py`, `hooks/_common.py`, `hooks/production_gate.py`, `ci/auth.py` (2, one of them the "no credential" reason, now "the framework's docs/notes/2.md"), `ci/run_phase.py`'s docstring, `init/sdlc_init.py`, `panel/models.py`, `commands/sdlc-init.md`, and this repository's `substrate-smoke.yml` and `substrate_smoke.py` (3); and the three test comments the study counted apart. None of those folders pointed at `docs/DECISIONS.md`.
2. **Check 5 widened** (`tasks.py`, `code_stub_problems`): `python tasks.py docs-lint` fails a file under `plugin/`, `template/` or `.github/` that names `NOTES.md` or `DECISIONS.md` at all, since every mention there is a fact's source; `tests/` and `docs/` keep their own rules. A test.
3. **S8:** `template/.github/workflows/sdlc-release.yml:14` and this repository's installed copy say the merge App's first merge "is to verify", not "is verified at R22's first merge": decision 36's "To verify" still holds, since no note records the merge App merging a build PR.
4. **S11:** `/sdlc-init` step 1's sentence on the close-look banner adds "at (e), the owner's approving review, on which the merge App merges, decision 36". The two copies in `skills/spec-template/SKILL.md` (lines 65 and 68) are left: they speak of the design PR's banner, which the owner merges at (b), so "the owner's merge accepts it" is true there.
5. **S12:** `pr/counters.py`'s `SHIPPED_PHASE` comment and `state/status.read_status`'s docstring say a change at phase e on the default branch was merged on the owner's approving review (decision 36: by the merge App, or by the owner). `status.py`'s two incident lines stay: an incident intent PR is gate (a), which the owner merges.
6. **The CLI message:** `run_phase.CLI_MODEL_NEED` takes its version from `init/sdlc_init.DEFAULT_CLAUDE_CODE_VERSION`, imported where the park is built, so the advice moves with the pin `/sdlc-init` writes.
7. **"Profile-based" after decision 37:** none is left under `plugin/` or `template/` (S1 to S4 were fixed in R65's part 3); the remaining "deferred review" wording is decision 21's live mechanism, not the retired `review:` key.

## Port list (HANDOFF.md, "Rules for every session")
This PR touches `plugin/ci/run_phase.py` (the docstring, `CLI_MODEL_NEED` and its one call), so it goes on the port list until the 1.0.0 read.

## The fresh-context review
Pending. *[2026-10-23: the review reported nothing blocking after this PR merged as `b6800ff`; its findings are fixed in the follow-up `docs/progress/2026-10-23-claude-r65-part-6-follow-up.md`, plugin 1.0.33]*

## Proposed edits for the owner
None.

## What the owner does
| When | Act |
|---|---|
| Now | Merge this PR when `Framework checks` is green on its final head. |
