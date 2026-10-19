# Progress — the LLM wiki pattern: ROADMAP R55 to R57, three annotations, and the owner's choice 236 (2026-10-19)

This session ran on branch `claude/llm-wiki-sdlc-framework-g10zr0`, from the owner's request of 2026-10-19: read the artifact "LLM Wiki Crosswalk", research further, and assess what of Karpathy's LLM wiki pattern the framework should implement, internally and in the projects it drives. The previous record (the framework's own checks, faster, choice 235, PR #243) is now `docs/progress/2026-10-19-framework-checks-faster-and-choice-235.md`, unchanged. The session's own file is `docs/handoffs/sessions/2026-10-19-claude-llm-wiki-sdlc-framework-g10zr0.md`.

## Summary
- **The artifact's diagnosis holds; its placement did not.** It was read at `230a53c` (plugin 1.0.10). By `209325f` its proposed rows R50 to R53 were taken (R50 to R54 exist) and choice 234 had re-ranked the Order column, so its ranks and its session prompt were stale (verified, `docs/ROADMAP.md` at `209325f`).
- **Checked against the repository, not copied.** `/sdlc-maintain` is the only command that reads `lessons/` (verified, `grep lessons plugin/commands/*.md`); the notes index says nothing checks `verified_with` (`docs/notes/index.md`, its header); `verified_with` is free text, as the owner ruled in change 0001 (`changes/0001-split-the-large-docs-with-an-index-each/spec.md`, the PR #112 ruling); 43 of 367 relative links under `docs/` were broken at `209325f` (a link scan in the session, examples and quotes included, so a few are false positives); notes 12 and 43 to 49 name no Claude Code version (verified, `grep verified_with docs/notes/*.md` at `2a2a9b2`).
- **Overlaps found before writing:** the project `references/` folder is R2's item 1 (`docs/proposals/session-tooling-pdf-web.md`, "The OKF reading"), not a new row; routing architecture updates through R37's standing PR would amend R37, whose step runs no model, so it was withdrawn; the shared lessons store is R1's steps 3 and 4.
- **New rows:** R55, the docs lint (this repository, no plugin version); R56, the design run reads the lessons, with an optional lesson field `files`; R57, system pages, a compiled project wiki, proposed now and built after the real-project trial. **Annotated:** R2, R42, R45. No existing rank moves. The argument is `docs/proposals/llm-wiki-adoption.md`.
- No change under `plugin/` or `template/`; no version bump.

## The owner's decisions (2026-10-19)
236. **The session's 22 recommendations on the LLM wiki pattern, all accepted** ("All of them as recommended"):
    - `references/` in a project is R2's item 1, read by the runs and never written by them, a guardrail path like R27's `policies/` (an amendment of decision 6, its decision file before the intent);
    - `verified_with` stays free text (change 0001's ruling kept); the lint reads the Claude Code version from it, compares it with the pin in `plugin/init/sdlc_init.py` and lists any mismatch, newer or older, and the notes that name none, which a later notes session fills in;
    - architecture updates do not go through R37's standing PR (withdrawn); `CLAUDE.md`'s Architecture section stays the owner's, with a pointer to the system pages;
    - the link lint reports until the existing breaks are fixed, then fails; notes gain an optional `supersedes` field; `docs/decisions/index.md` is generated;
    - the design run reads the lessons in its own small plugin change, not inside R27; a lesson gains an optional `files` field read from the fix PR's diff; its name goes to R45;
    - system pages are written at (c) in the build diff, created the first time a change touches a module, checked by a warning line that never parks, proposed now and built after the real-project trial;
    - stale lessons become a digest line under R42; the shared lessons store stays R1's steps 3 and 4; no graph viewer;
    - the order: this documentation PR, then R55, then R56 after choice 235's second step and the sample's next change; rows from R55;
    - NOTES §49's candidate "park at once on findings no session can fix" is weighed beside R57 and decided on its own.

## Proposed edits for the owner
None: no guardrail line changes in this PR.

## Left
- **R55 is the next PR of this line:** the task, its tests, and the clean-up of the existing broken links; the notes without a Claude Code version are listed by the task, then filled in by a notes session.
- **R56 waits** for choice 235's second step and the sample's next change.
- **R57's measures** are defined in the proposal; the trial session records them.
- **The artifact "LLM Wiki Crosswalk"** keeps its 2026-10-19 placement (R50 to R53, the ranks before choice 234); this record and the proposal supersede it. It was not edited.

## Checks (this repository)
On the final head, after `python -m pip install -e ".[dev]"`, chained with `set -o pipefail`: the four commands of `HANDOFF.md`'s standing precondition 1. Their output is in the PR.
