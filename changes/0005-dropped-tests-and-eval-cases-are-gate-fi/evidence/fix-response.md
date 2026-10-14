# Fix response — round 1 (phase b)

Source: `evidence/fix-requests.json` (collected at 2026-10-14T15:19:00+00:00, head
486fd017d5d21fd7aa6d6e3eeb1811f92ce6cd31, PR #186). One review, `OWNER`, `CHANGES_REQUESTED`.

## Applied

1. **Version lockstep (plan.md step 9 and "Files that change", line 35).** `plan.md`'s
   "Files that change" and Order of work step 9 now bump `.claude-plugin/marketplace.json`
   together with `.claude-plugin/plugin.json`, to the same next-free-patch value, so
   `tests/test_scaffold.py:47` (`entry["version"] == manifest["version"]`) keeps passing. No
   exact version number is written into the plan, matching its existing convention: the
   build step picks the number at merge time.
2. **Missing Proof items for Risks lines 101–103, 121–124, 133–135.**
   - Added `test_ratchets_plan_edited_after_merge_base_does_not_excuse_drop` (lines 101–103's
     mitigation): a `plan.md` declaration committed only after the merge base must not excuse
     a drop.
   - Added `test_ratchets_risk_list_tests_configured_does_not_satisfy_ratchet_hit` (lines
     121–124's mitigation): a configured `risk_list: ["tests"]` item must not be confused
     with, or satisfy, the `"ratchet: tests"` hit key.
   - Amended `test_ratchets_skip_markers_listed_never_fail` (lines 133–135's mitigation) to
     name the fixture explicitly: this repository's own runbook test files (the `--deselect`
     lines Risks counts, nine of them), not a synthetic list, so a regression here is caught
     by this repository's own suite.

## Not applied (optional items), checked and left as-is

- **`spec.md:41`'s citation of `plugin/pr/description.py:249-259`.** Checked against the
  current `_conformance_line` definition at HEAD: it still starts at line 249 and ends at
  line 259. PR #199 (merged 2026-10-14T09:55:34Z, before this branch's own merge-base) did
  touch `description.py`, but the function is at the same lines after that merge. No change
  made; the citation is accurate as read right now.
- **`spec.md:2` naming plugin 0.3.6.** This is the "Produced by" stamp logging the plugin
  version actually in force when `/sdlc-design` ran for this change — the same pattern change
  0002's and 0003's `spec.md` headers use (0.3.6 and 0.3.5, each the version in force at that
  change's own design run). It is a historical record, not a citation that drifts with code
  movement; editing it to a later number would misrepresent what the design session actually
  saw. Left unchanged.
- **`intent.md:10` naming plugin 0.3.7.** Even read as a request, `intent.md` cannot be
  edited at phase (b) or later (framework rule: the one run that edits `intent.md` is phase
  (a), before the intent PR merges). Not applied for that reason, independent of whether the
  number itself is accurate.

## Checks

`gh pr checks 186`: three `check` jobs (ubuntu 3.10, ubuntu 3.12, windows) all `pass`; `fix`
was `pending` (this round).
