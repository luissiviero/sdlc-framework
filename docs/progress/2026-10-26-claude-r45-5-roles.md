# Progress — R45's fifth rename PR: the roles in prose and the rulesets' names (2026-10-26, plugin 1.0.47)

This session ran on branch `claude/r45-5-roles`, from `main` at `05d9412` (#394, plugin 1.0.46, tagged `v1.0.46`). It is section 12's PR 5 of `docs/reviews/2026-10-20-names-against-the-article.md` (row 87), as decision 39's point 4 amends it (N9 and N10). Plugin **1.0.47** (`python tasks.py next-free` after `git fetch origin` on `05d9412`). No numbered choice, note or decision is taken.

## What was built
1. **The roles where a decision is asked** (row 87; prose and prompts, no code, no data): the product owner merges the intent and the spec+plan PRs (p.9-12); the code owner's approving review merges the build PR, and the code owner answers its findings (p.29, p.33); the release manager applies `sdlc:release-approved` (p.37, p.40-41); the service owner triages the maintain queue, merges or dismisses an incident intent, labels it `sdlc:schedule` and says Go (p.43-44). Everywhere else "the owner" stays: the one person who owns the repository, edits the guardrail files, reads the digest and receives the review request, as `docs/OPERATING_MODEL.md` §2 says beside the four roles it now introduces. The un-park verbs that apply at any gate, the sentences that span several gates and the stored reason strings keep "the owner". Changed in `docs/OPERATING_MODEL.md`, `README.md`, the commands, the adversarial reviewer, five skills, `template/changes/README.md`, two comments of `template/sdlc.yaml` and one of `template/bands.yaml`, and the owner-facing strings of `plugin/pr/description.py` (the gates' "What needs you" lines and the release line), `plugin/hooks/production_gate.py` and `plugin/gate/checks.py`.
2. **"Ruleset 1" and "Ruleset 2" are "the merge ruleset" and "the review ruleset"** (N9), in `/sdlc-init` step 6, the living docs and the plugin's comments.
3. **The review ruleset's name is `review and no direct writes on main`** (N10): `/sdlc-init` step 6 names it so, and says a project set up with 1.0.23 to 1.0.46 renames its ruleset by hand, desktop-only; no plugin code reads the name.
4. **The decisions it renames, annotated** (choice 126): decision 36 (N9, N10, row 87), 13 (row 87: the code owner and the release manager) and 25 (row 87: the service owner), each beside its sentence. Decision 4's "Ruleset (1)" is an option's number, not this name, and stays. Choice 251, which named the review ruleset, is in a record (`docs/progress/2026-10-22-bypass-option-c-choice-251-1.0.23.md`, line 16), annotated never: this record carries the rename.

## How it was built
One sub-agent built the rewording on this branch, with the Edit tool, sentence by sentence; this session bumped the version, regenerated `plugin/init/template_hashes.json` (`template/changes/README.md` changed) and ran the suite. Tests that asserted the old sentences assert the new ones; none was deleted or skipped. No workflow template changed, so the owner commits no copy.

## The fresh-context review
A fresh-context sub-agent reviewed the diff (report only). It found nothing blocking: no string that code reads or stores changed, each role matches its page in the article, no "the owner" meaning the person was changed, and the test count is unchanged (1993). Its findings and what was done:
1. **Fixed:** `/sdlc-maintain`'s description still said "the owner's triage" (and PR 3's old `go`); now the service owner's, and `ask`.
2. **Fixed:** the test lock read as the code owner's in two places and the owner's un-park verb elsewhere; it is the owner's, as every un-park verb stays (`docs/OPERATING_MODEL.md`, `/sdlc-fix`).
3. **Fixed:** the three decision annotations were dated 2026-10-25; they are 2026-10-26.
4. **Fixed:** the tests' comments and docstrings that said "ruleset 1/2" use the new names. Left for the next change to the merge workflow template: its two comments that still say "ruleset 1" and "ruleset 2" (`template/.github/workflows/sdlc-merge.yml`, lines 8 and 22), since a template change costs the owner a copy commit; the sixth PR's closing `git grep` will list them.
5. **Optional, taken:** `/sdlc-deploy`'s two release lines read "the release manager's line".
6. **Optional, not taken:** three sentences on the fast lane or the incident path name the product owner where the deploy gate's code owner or the service owner may act (`/sdlc-design`, the intent template); "merge is the code owner's" in the definition of done (the merge App merges on that approval); two ragged comment wraps; no test pins the role wording of every checklist line.

## Port list
This PR changes comments only in `plugin/detect/cli.py` and `plugin/detect/runbooks.py`; it goes on the port list until the 1.0.0 read.

## Proposed edits for the owner
- **This repository's review ruleset**, if it still carries `(decision 36, choice 251)` in its name: rename it `review and no direct writes on main` (desktop-only, Settings, Rules). Nothing reads the name.
- The guardrail templates' new comments (`template/sdlc.yaml`, `template/bands.yaml`) reach a project's copies only by the owner's edit. In this repository, two comment lines name the owner's Go; with PR 3's rows for the same lines (`docs/progress/2026-10-25-claude-r45-3-config-values.md`) they become, at the pin move:

| Link | Row | What is there | What it must become |
|---|---|---|---|
| `bands.yaml` | 21-22 | `    # go = touches a running system, parks with "what I need from you" until the owner`<br>`    # says Go. A route not listed here is never taken.` | `    # ask = touches a running system, parks with "what I need from you" until the service`<br>`    # owner says Go. A route not listed here is never taken.` |
| `sdlc.yaml` | 64 | `  # or go (touches a running system; waits for the owner's "Go" as a parked item)` | `  # or ask (touches a running system; waits for the service owner's "Go" as a parked item)` |

## What the owner does
| When | Act |
|---|---|
| Now | Merge this PR when `Framework checks` is green on its final head. |
| When convenient | The ruleset rename above. |
