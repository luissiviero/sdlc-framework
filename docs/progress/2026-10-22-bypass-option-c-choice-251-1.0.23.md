# Progress — the owner's bypass tested live; Exempt in ruleset 1 plus a no-direct-writes ruleset (choice 251), as plugin 1.0.23 (2026-10-22)

This session ran on branch `ccr-76f1ceba-idf2w0`. The owner asked whether the Repository admin's bypass in this repository's ruleset 24077592 should be "For pull requests only" or Exempt, then asked for a live test before choosing. The test ran three setups, recorded in `docs/reviews/2026-10-22-ruleset-bypass-modes.md`:
- "For pull requests only" and Exempt, through #314, #315, #316 and #318 (all merged);
- C, through sample #101 (closed unmerged) and this PR.

The facts are NOTES §57.

The previous record (the R22 double check's fixes as 1.0.22, from #319) is now `docs/progress/2026-10-22-r22-double-check-fixes-1.0.22.md`, unchanged. This session's file is `docs/handoffs/sessions/2026-10-22-ccr-76f1ceba-idf2w0.md`.

## Coordination with the other sessions
- **Numbers.** Choice 251, note 57 and patch 1.0.23, the next free ones in `2026-10-22-ccr-3fe1c65e-erwrby.md` and in #320's file. No open PR claims them (verified, the open PRs on 2026-10-22: #320, documentation only and since merged, and #173).
- **The direct writes.** The test's probes in Exempt (`7c33f02`, `906317a`) landed on `main` and #316 removed them; the session `ccr-3fe1c65e-erwrby` recorded them as well.

## The owner's decision (2026-10-22)
251. **Option C on both repositories: the owner stays Exempt in ruleset 1, and a ruleset with the owner's bypass "For pull requests only" holds "Require a pull request before merging" (no approvals), "Block force pushes" and "Restrict deletions"** (the owner, "I like C", after the two first runs and the comparison against the six criteria). It completes choice 242's point 5 rather than reversing it. What the runs showed:
    - Exempt alone accepts a direct commit or push to `main` by anything acting as the owner's login, a cloud session included, and logs it as `pass`;
    - "For pull requests only" in ruleset 1 refuses those writes, but the phone then shows "Unable to merge" on every pull request;
    - C refuses the session's direct commit on both repositories. On the sample, the phone shows "Ready to merge" on an ordinary pull request and "Unable to merge" only on one ruleset 2 holds;
    - no setup stops a session acting as the owner's login from merging a pull request through the API.

    The owner made the setup on 2026-10-22:
    - this repository: ruleset 1 to Exempt, and the new ruleset 25674595 "main — no direct writes (choice 251)";
    - the sample: the three rules added to ruleset 2 (25656269), renamed "review and no direct writes on main (decision 36, choice 251)".

    The session verified all four rulesets from the owner's exports and from the rules endpoint of each `main`. Annotated: NOTES §17, decision 36 point 5, R22's row, choice 242 point 5.

## Summary
- **The test** (`docs/reviews/2026-10-22-ruleset-bypass-modes.md`):
  - in each of the first two setups, six tests: three by the session (a direct commit through the GitHub MCP tool, a direct `git push`, an API merge), three by the owner (the phone merge, the web merge if needed, the rule-suites log);
  - in C: the direct commit on both repositories and the phone's label on the sample. This PR's own merge from the phone is the framework's label check.
  - The owner gave the session an explicit go for the writes to `main`, which `HANDOFF.md` forbids otherwise.
  - In C, the session's own safety check refused the `git push` to `main`, so S2 was not run there.
- **NOTES §57**: the facts, with the rule-suites log the owner read from a codespace. The repository's settings show no Rule Insights page, and a codespace's own token gets 403.
- **`/sdlc-init` step 6** (`plugin/commands/sdlc-init.md`):
  - ruleset 1 keeps the owner Exempt, with the reason and its gap;
  - ruleset 2 gets its new name and four rules, with the owner's bypass for pull requests only;
  - a project set up with 1.0.18 to 1.0.22 adds the three rules to its ruleset 2.
- **`docs/OPERATING_MODEL.md` §2**: the same.
- **The test pinning that text** (`test_sdlc_init_prescribes_the_branch_ruleset_of_decision_4`) follows choice 251. It passes on the new text and fails on the previous one (verified, the instruction files stashed).
- **1.0.23** in `.claude-plugin/plugin.json` and `marketplace.json`. The root pin stays at 1.0.17 (choice 249, point 2).
- The citations added under `docs/` were opened and compared with each sentence (choice 241).

## Left
- **Ruleset 2 from the phone.** A tap merged a pull request blocked by a ruleset where the owner's bypass is for pull requests only (#315). The same tap is expected to merge a red build PR on the sample past its "Unable to merge" label, but that is not verified. The first red build PR on the sample shows it.
- **What stops a session from merging as the owner.** No setup (NOTES §57, S3). A session's merge of its own pull request is refused by its instructions only (`HANDOFF.md`, "Never merge to `main`"). This is a candidate for the ROADMAP, not something this record decides.
- **The sample's branch `ccr-76f1ceba-idf2w0`** holds the throwaway file of #101. The session's tools cannot delete a branch; the owner may delete it from #101's page.

## What the owner does
| Where | What is there now | What it must become |
|---|---|---|
| This PR | ready for review | Merge it from the phone: "Ready to merge" is expected (the framework's label check). |
| [Sample #101](https://github.com/luissiviero/sdlc-sample-python/pull/101) | closed, its branch kept | Optional: "Delete branch". |
