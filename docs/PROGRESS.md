# Progress — ROADMAP R65's part 3: docs-lint checks 11 and 12, S1 to S4 fixed (2026-10-22)

This session ran on branch `claude/r65-part-3-checks-11-12`, from `main` at `8e48bcc` (#325). It is the session of R65's parts 1 (#324) and 2 (#325). After #325 merged, the owner answered "The rest as recommended", and the recommendation was to start part 3 next. Part 3 is built as the owner accepted it:
- choice 252, point 4;
- choice 253, points 5 and 6;
- `docs/proposals/one-owner-per-fact.md`, part 3.

It is a documentation and `tasks.py` PR: no plugin version, nothing under `plugin/` or `template/`. The two manifests under `.claude-plugin/` change their description only.

The previous record (R65's part 2 and choice 253, from #325) is now `docs/progress/2026-10-22-r65-part-2-choices-index-choice-253.md`, unchanged (verified, `cmp` against `8e48bcc:docs/PROGRESS.md`). This session's end file is `docs/handoffs/sessions/2026-10-22-claude-r65-part-3-checks-11-12.md`.

## Coordination with the other sessions
- **Numbers.** This PR takes none. The owner's answer starts work choice 253 already decided, so it is not a new choice.
- **Open PRs**, read after #325 merged at 22:46 UTC: #173 (intent 0004) and #326 (session `ccr-6ed8a82e-cxmftx`'s end file, missed in this record's first draft). #326 has merged since, as `a8d6dba`, and `main` is merged into this branch.

## What was built
1. **docs-lint check 11: a rank lives in ROADMAP's Order column.**
   - In `docs/proposals/` and `docs/decisions/`, "rank N" fails outside a dated annotation (`*[YYYY-MM-DD …]*`).
   - In a session file dated from 2026-10-23 on, any "rank N" fails. So does a hand-written next free number: a "next free" line that names a choice, note, decision, candidate or version.
   - The session files of 2026-10-22 and before are kept as written (choices 126 and 252, point 4). The cutover is the day after the build, because that day's files already hold next-free lines.
2. **docs-lint check 12: no retired term used as a live one.** It reads `README.md`, the two manifests, `docs/OPERATING_MODEL.md`, `docs/ROADMAP.md` and every file under `template/`.
   - The terms are `conventions.ACCEPT_RISK_LABEL` and `status.RETIRED_KEYS`, read from the plugin, plus a short list in `tasks.py`: "profile-based", the Full profile, `sdlc:c-approved` and `sdlc:d-approved`.
   - A line passes if it says the term is retired, withdrawn, removed or gone, or "until 1.0.20", or if it carries a dated annotation.
   - `docs/BUILD_GUIDE.md` is not read: it is the version-3 plan with its annotations (choice 252, point 6). Read, it would fail four lines of the plan as written.
3. **The first runs, fixed in this PR:**
   - **Check 12** failed exactly S1 to S4, as the proposal said it would. `README.md:3`, `.claude-plugin/plugin.json:5` and `.claude-plugin/marketplace.json:3` and `:12` now read "with human gates at (a), (b) and (e)", the study's wording.
   - **Check 11** failed five ranks, not four. The study's section 1.6 counted `docs/proposals/llm-wiki-adoption.md:92` as annotated, but its "after R28, rank 19" stood outside the annotations. The five are:
     - `docs/decisions/36.md:23`;
     - `docs/proposals/template-cli-default.md:39`;
     - `docs/proposals/template-copies-refresh.md:48` (two ranks);
     - `docs/proposals/llm-wiki-adoption.md:92`.
   - Each sentence now names the candidate alone, and a dated annotation beside it keeps the text that stood there (choice 126).
4. **The study's annotations** in `docs/reviews/2026-10-22-sources-of-truth.md`:
   - section 2's "Who merges" row: `OPERATING_MODEL.md:28` keeps choice 251 written out, checked by a test (choice 253, point 5);
   - S1's "the next plugin PR": fixed here (choice 253, point 6);
   - section 1.6: the fifth rank.
5. **Tests.** Four in layer 1: ranks in proposals and decisions; session files on each side of the cutover; retired terms, failing and passing; the terms' sources. The repository's own lint test covers layer 2.

## Points left open, with a recommendation
- **`docs/BUILD_GUIDE.md` stays out of check 12.** Recommendation: keep it out. It is history with annotations, and the owner froze its JSON twin for the same reason (choice 252, point 6).
- **The pass words were widened** from the proposal's three ("retired", "withdrawn", "until 1.0.20") to also take "removed", "gone" and a dated annotation. Without them, check 12 fails `OPERATING_MODEL.md:42` and `:57`, which say the term is gone in other words, and annotated ROADMAP rows such as R12. Recommendation: keep the wider list. Each extra word marks the term as no longer live.

## Left
- **R65's part 4:** `python tasks.py verify` and check 13 in one PR, then CI on `verify`. The owner's rows 1 to 4 come after it (choice 253, points 2 to 4).
- **R65's part 5:** `HANDOFF.md`'s skeleton points to `python tasks.py next-free`. The same PR adds the annotation of R65's row (choice 253, point 13).
- **R65's part 6:** its own plugin patch after R51 merges (choice 252).
- **The merge-tool deny rule:** the owner's row 5 of #325's record, then a live check (choice 253, point 7).

## What the owner does
| When | Act |
|---|---|
| Now | Merge this PR when `Framework checks` is green on its final head. |
| Now, any time | Row 5 of choice 253's record (the merge-tool deny rule); the four branch deletions (choice 253, point 9). |
| After R65's part 4 merges | Rows 1 to 4 of choice 253's record, in one PR. |
