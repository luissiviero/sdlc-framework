# Progress — R21's first part: desktop-only acts say so, with the link (2026-10-23)

This session ran on branch `claude/r21-desktop-only`, from `main` at `f41a336` (#349), as the small lane beside wave 2's two build sessions, started at the owner's request on 2026-10-23; this is its second item. The scope is choice 257, #7 (`docs/progress/2026-10-23-choices-257-258.md`): R21's first part (ROADMAP R21 and its 2026-10-20 annotation; `docs/proposals/desktop-only-acts.md`; `docs/reviews/2026-10-20-trial-readiness-review.md`, risk 6), before R45's rename, **with no plugin version**. It changes `plugin/commands/sdlc-init.md` and `plugin/pr/digest.py`, but by choice 257 it bumps nothing, so `.claude-plugin/plugin.json` stays at 1.0.31; `HANDOFF.md` allows a bump only for a change under `plugin/` or `template/` and does not require one. It started after lane A's #350 merged, as the owner asked. No choice, note, decision or patch number is taken.

## What was built
1. **`/sdlc-init` step 6, the workflow permission and the CI secret:** the bullet gives `https://github.com/<owner>/<repo>/settings/actions` and `https://github.com/<owner>/<repo>/settings/secrets/actions`, says both are desktop-only (the GitHub mobile app shows no repository settings; open the link in a desktop browser or in the phone browser's desktop mode), and tells the session to name both in the report with the links filled in.
2. **Step 6, the App bullet and ruleset 1's bullet:** both said or implied desktop-only but gave no link. The App bullet now gives `https://github.com/settings/apps/new` and the project's variables and secrets pages (the links step 0 already gave); ruleset 1's bullet says desktop-only and gives `https://github.com/<owner>/<repo>/settings/rules`, as ruleset 2's did.
3. **Step 5's report** names step 6's acts, each settings act marked desktop-only with its direct link.
4. **The digest** (`plugin/pr/digest.py`, `UNPROTECTED`): the unprotected-branch warning ends with "Desktop-only: the GitHub mobile app cannot change a ruleset; open https://github.com/<owner>/<repo>/settings/rules in a desktop browser, or in the phone browser's desktop mode (ROADMAP R21)". `main` hands the repository to the notice; without it (a rendering with no repository) the notice names the Settings → Rules page instead of a broken link.
5. **Tests:** `test_sdlc_init_marks_every_settings_act_desktop_only_with_its_link` checks that every step 6 bullet holding a "Settings →" path says desktop-only and gives a link, and that the report sentence is there; the two digest tests check the line, with and without the repository.

## Not built, and why
- **The park on a missing setting** (the proposal's point 3), **the digest's merge-key warning** (`MERGE_KEY_UNSAFE`, a settings act too), **one table of acts in Python** (point 1) and **R19's marks**: R21's rest, which keeps its place in ROADMAP.
- **The proposal's exact phone instructions** ("Chrome: ⋮ → Desktop site; Safari: aA → Request Desktop Website"): the existing step 0 wording ("in a desktop browser, or in the phone browser's desktop mode") is kept, so every place says the same thing.

## Known limits, recorded
- **The links are not verified in a browser** in this session (the proposal asks for one check before they are written). `…/settings/rules`, `…/settings/variables/actions`, `…/settings/environments` and `https://github.com/settings/apps/new` were already in step 0 and step 6 on `main`; `…/settings/actions` and `…/settings/secrets/actions` follow the same pattern. The owner's first click confirms them.

## Port list
This PR touches neither `plugin/detect/`, nor `plugin/ci/run_phase.py`, nor the detect, runbook and fix workflow templates.

## Proposed edits for the owner
None.

## What the owner does
| When | Act |
|---|---|
| Now | Merge this PR when `Framework checks` is green on its final head. |
| At the first `/sdlc-init` of the trial | Open each link once from the phone in desktop mode; a wrong one is a one-line fix. |
