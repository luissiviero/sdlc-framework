# Progress — R45's fifth rename PR: the roles in prose and the rulesets' names (2026-10-26, plugin 1.0.47)

This session ran on branch `claude/r45-5-roles`, from `main` at `05d9412` (#394, plugin 1.0.46, tagged `v1.0.46`). It is section 12's PR 5 of `docs/reviews/2026-10-20-names-against-the-article.md` (row 87), as decision 39's point 4 amends it (N9 and N10). Plugin **1.0.47** (`python tasks.py next-free` after `git fetch origin` on `05d9412`). No numbered choice, note or decision is taken.

## What was built
1. **The roles where a decision is asked** (row 87; prose and prompts, no code, no data): the product owner merges the intent and the spec+plan PRs (p.9-12); the code owner's approving review merges the build PR, and the code owner answers its findings and lifts the test lock (p.29, p.33); the release manager applies `sdlc:release-approved` (p.37, p.40-41); the service owner triages the maintain queue, merges or dismisses an incident intent, labels it `sdlc:schedule` and says Go (p.43-44). Everywhere else "the owner" stays: the one person who owns the repository, edits the guardrail files, reads the digest and receives the review request, as `docs/OPERATING_MODEL.md` §2 says beside the four roles it now introduces. The un-park verbs that apply at any gate, the sentences that span several gates and the stored reason strings keep "the owner". Changed in `docs/OPERATING_MODEL.md`, `README.md`, the commands, the adversarial reviewer, five skills, `template/changes/README.md`, two comments of `template/sdlc.yaml` and one of `template/bands.yaml`, and the owner-facing strings of `plugin/pr/description.py` (the gates' "What needs you" lines and the release line), `plugin/hooks/production_gate.py` and `plugin/gate/checks.py`.
2. **"Ruleset 1" and "Ruleset 2" are "the merge ruleset" and "the review ruleset"** (N9), in `/sdlc-init` step 6, the living docs and the plugin's comments.
3. **The review ruleset's name is `review and no direct writes on main`** (N10): `/sdlc-init` step 6 names it so, and says a project set up with 1.0.23 to 1.0.46 renames its ruleset by hand, desktop-only; no plugin code reads the name.
4. **The decisions it renames, annotated** (choice 126): decision 36 (N9, N10, row 87), 13 (row 87: the code owner and the release manager) and 25 (row 87: the service owner), each beside its sentence. Decision 4's "Ruleset (1)" is an option's number, not this name, and stays. Choice 251, which named the review ruleset, is in a record (`docs/progress/2026-10-22-bypass-option-c-choice-251-1.0.23.md`, line 16), annotated never: this record carries the rename.

## How it was built
One sub-agent built the rewording on this branch, with the Edit tool, sentence by sentence; this session bumped the version, regenerated `plugin/init/template_hashes.json` (`template/changes/README.md` changed) and ran the suite. Tests that asserted the old sentences assert the new ones; none was deleted or skipped. No workflow template changed, so the owner commits no copy.

## The fresh-context review
<!-- filled in after the review -->

## Port list
This PR changes comments only in `plugin/detect/cli.py` and `plugin/detect/runbooks.py`; it goes on the port list until the 1.0.0 read.

## Proposed edits for the owner
- **This repository's review ruleset**, if it still carries `(decision 36, choice 251)` in its name: rename it `review and no direct writes on main` (desktop-only, Settings, Rules). Nothing reads the name.
- The guardrail templates' new comments (`template/sdlc.yaml`, `template/bands.yaml`) reach a project's copies only by the owner's edit; this repository's own `sdlc.yaml` and `bands.yaml` have no line that names the release label's or Go's actor.

## What the owner does
| When | Act |
|---|---|
| Now | Merge this PR when `Framework checks` is green on its final head. |
| When convenient | The ruleset rename above. |
