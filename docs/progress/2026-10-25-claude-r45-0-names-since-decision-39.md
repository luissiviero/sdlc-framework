# Progress — R45's first PR: the names added since decision 39, judged (2026-10-25)

This session ran on branch `claude/r45-0-names-since-decision-39`, from `main` at `11d5661` (#385, plugin 1.0.42), as lane A of wave 5, started by the third central session (`session_013TgyuTukXLjdZU3rmrgyRt`) at the owner's request. It builds the first of R45's seven PRs as choice 273 orders them (`docs/progress/2026-10-25-ccr-ca9f0149-a29zgl-wave-5.md`, on the central session's branch `ccr-ca9f0149-a29zgl`, PR #386, open when this was written). This is a documentation PR: no plugin version, nothing under `plugin/` or `template/`, nothing renamed. It takes no numbered choice, note or decision; its rows go on from decision 39's N28.

## What was written
1. **`docs/reviews/2026-10-25-names-added-since-decision-39.md`**: rows N29 to N40, judged by decision 39's rule. Change 0004's names are kept as choice 273 says (N29), with the drive's other names (N30) and `SDLC_JOB_TIMEOUT_MINUTES` (N31). R18's read-only session, `--phase triage` and every name built on it, becomes `explain` (N32), with PR 2, beside row 37's `sdlc:triage`. The failed-run names (N33), the release notes' plain-words names (N34), the eval `skill` check (N36), R64's refresh states (N37) and R26's counters (N38, whose gate letters follow row 16) are kept. R27's policy files are kept, but the UX file follows row 80 with PR 4 (N35). The evidence names with a phase letter that row 60 does not list (N39) and the `run(<phase>):` commit subjects (N40) follow row 1 with PR 1. The page also lists the readers of history the sixth PR keeps.
2. **`docs/decisions/39.md`**: one annotation beside point 1's sentence (`:13`), as choice 273 asks: the sixth PR removes only the readers of live state, keeps the readers of history (named), and merges only after both repositories are pinned at the fourth rename PR's version or later and before the real-project trial; with a pointer to the new page.
3. **R45's ROADMAP row**: one dated annotation. No other row is touched.

## How the names were found
From `git diff be5be5e 11d5661 -- plugin template` (63 files), searched for the added CLI flags, environment variables, `refs/sdlc/*` names, evidence file names, gate check ids, headings and owner-facing strings, then read in the files each row names. The versions are those of the first-parent merge that added each name (`git log --first-parent -S<name> be5be5e..11d5661`): R27 1.0.35 (#367), R18 1.0.36 (#368), R64 1.0.37 (#370), R26 1.0.39 (#375), change 0004 1.0.40 (#382). `--phase triage` was already in `plugin/ci/run_phase.py` at `be5be5e` (20 lines name it), which decision 39's read did not list; R18 widened it. Each article quotation was checked against `docs/reference/ai-native-sdlc-playbook.txt` by its page tag. "Diagnose" was set aside for N32 because `template/bands.yaml:24` already uses it (`action: diagnose`).

## The fresh-context review
<!-- filled in after the review -->

## Port list
This PR touches none of `plugin/detect/`, `plugin/ci/run_phase.py` or the detect, runbook and fix workflow templates.

## Proposed edits for the owner
None.

## What the owner does
| When | Act |
|---|---|
| Now | Merge this PR when `Framework checks` is green on its final head. Merging accepts rows N29 to N40 as judged. |
| Then | R45's first rename PR, from this lane. |
