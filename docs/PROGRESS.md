# Progress — ruleset 1's bypass modes tested live; the owner's bypass is "for pull requests only" (choice 251), as plugin 1.0.23 (2026-10-22)

This session ran on branch `ccr-76f1ceba-idf2w0`. The owner asked whether the Repository admin's bypass in this repository's ruleset 24077592 should be "For pull requests only" or Exempt, then asked for a live test of both modes before choosing. The test record is `docs/reviews/2026-10-22-ruleset-bypass-modes.md` (#314, #315, #316 and #318, all merged), and the facts are NOTES §57.

The previous record (the R22 double check's fixes as 1.0.22, from #319) is now `docs/progress/2026-10-22-r22-double-check-fixes-1.0.22.md`, unchanged. This session's file is `docs/handoffs/sessions/2026-10-22-ccr-76f1ceba-idf2w0.md`.

## Coordination with the other sessions
- **Numbers.** Choice 251, note 57 and patch 1.0.23, the next free ones in `2026-10-22-ccr-3fe1c65e-erwrby.md` and in #320's file. No open PR claims them (verified, the open PRs on 2026-10-22: #320, documentation only, and #173).
- **The direct writes.** The test's probes in Exempt (`7c33f02`, `906317a`) landed on `main` and #316 removed them; the session `ccr-3fe1c65e-erwrby` recorded them as well.

## The owner's decision (2026-10-22)
251. **The owner's bypass in ruleset 1 is "For pull requests only", on both repositories** (the owner, "I'll stay with the `For pull requests only` version", after both runs). It reverses choice 242's point 5. The two runs showed:
    - in "For pull requests only", a direct commit or push to `main` by the owner's login is refused, and so is one by a cloud session, which acts as that login (NOTES §57);
    - Exempt accepts both and logs them as `pass`;
    - the phone merges in both modes, through an "Unable to merge" label and a confirmation sheet in the chosen one;
    - neither mode stops a session acting as the owner's login from merging a pull request through the API.

    Annotated: NOTES §17, decision 36 point 5, R22's row, choice 242 point 5.

## Summary
- **The test** (`docs/reviews/2026-10-22-ruleset-bypass-modes.md`): six tests in each mode.
  - Three by the session: a direct commit through the GitHub MCP tool, a direct `git push`, and an API merge.
  - Three by the owner: the phone merge, the web merge if needed, and the rule-suites log.
  - The owner gave the session an explicit go for the writes to `main`, which `HANDOFF.md` forbids otherwise.
- **NOTES §57**: the facts, with the rule-suites log the owner read from a codespace. The repository's settings show no Rule Insights page, and a codespace's own token gets 403.
- **`/sdlc-init` step 6** (`plugin/commands/sdlc-init.md`):
  - the owner's bypass in ruleset 1 is "For pull requests only", with the reason and a warning against Exempt;
  - the ruleset 2 bullet no longer asks for Exempt;
  - a red build PR merges through the owner's bypass, from the web UI's checkbox or from the phone.
- **`docs/OPERATING_MODEL.md` §2**: the same, with Exempt's period (0.2.26 to 1.0.22) named.
- **The test pinning that text** (`test_sdlc_init_prescribes_the_branch_ruleset_of_decision_4`) follows choice 251. It fails on the old text and passes on the new (verified, the instruction files stashed).
- **1.0.23** in `.claude-plugin/plugin.json` and `marketplace.json`. The root pin stays at 1.0.17 (choice 249, point 2).
- The citations added under `docs/` were opened and compared with each sentence (choice 241).

## Left
- **Ruleset 2 from the phone.** On ruleset 1, a tap merged a blocked pull request in this mode. The same tap is expected to merge a build PR that ruleset 2 holds, since the owner's bypass there is in the same mode, but that is not verified. If it holds, a red build PR merges from the phone past the label: still the owner's act, though a lighter one than the web checkbox. The first red build PR on the sample shows it.
- **What stops a session from merging as the owner.** Nothing in either mode (NOTES §57, S3). A session's merge of its own pull request is refused by its instructions only (`HANDOFF.md`, "Never merge to `main`"). This is a candidate for the ROADMAP, not something this record decides.

## What the owner does
| Where | What is there now | What it must become |
|---|---|---|
| [This repository's ruleset 1](https://github.com/luissiviero/sdlc-framework/settings/rules/24077592), bypass list, Repository admin row, `…` menu | Exempt (set for the test's second run) | For pull requests only |
| [The sample's ruleset 1](https://github.com/luissiviero/sdlc-sample-python/settings/rules/24078926), bypass list, Repository admin row, `…` menu | Exempt (NOTES §56) | For pull requests only; the merge App's row stays "For pull requests only" |
