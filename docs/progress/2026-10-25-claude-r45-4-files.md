# Progress — R45's fourth rename PR: the files (2026-10-25, plugin 1.0.46)

This session ran on branch `claude/r45-4-files`, built on R45's third rename PR (#393, merged as `54d498e`, plugin 1.0.45, tagged `v1.0.45`), with `main` merged in by a merge commit. It is section 12's PR 4 of `docs/reviews/2026-10-20-names-against-the-article.md` (rows 77, 78 and 80), as decision 39's point 4 amends it (N5 and N7), with row N35's UX file of `docs/reviews/2026-10-25-names-added-since-decision-39.md`. Plugin **1.0.46** (`python tasks.py next-free` after `git fetch origin` on `54d498e`). No numbered choice, note or decision is taken.

## What was built
1. **The intent's `Status:` line is gone** (row 77): the intent template and the gate's required header fields (`gate/artifacts.py INTENT_HEADER_FIELDS`) no longer have it; an intent that still carries it passes, and the intents already written keep it as history. The writers of an intent (`/sdlc-intent`, `/sdlc-maintain`, `/sdlc-init`'s change 0000, the weekly scan's route) stop writing it. The spec header's `Status:` stays: row 77 names the intent only.
2. **`sdlc-evals.yml` is `sdlc-agent-evals.yml`** (row 78, the article's `agent-evals.yml`, p.30), named "SDLC agent evals". `/sdlc-init`'s upgrade installs the new file and removes an old copy nobody edited (`RENAMED_COPIES`, `retire_renamed_copies`, by R64's hashes: `removed (was <version>)`); an edited old copy is kept and reported `kept; renamed (edited)`, and the new file waits until it is gone, so the suite never runs twice. `tasks.py template-hashes` keeps the old name's hashes from the tags. This repository runs `framework-evals.yml` and installs neither.
3. **`ux-conventions` is `ux-and-brand`** (row 80, with N35's `policies/ux-and-brand.md`): the skill's folder and name, its eval cases, the commands, the reviewer's brief and `template/policies/README.md`. For one release the gate and the skill still read `policies/ux-conventions.md` when the new file is missing, and still count a project override in `.claude/skills/ux-conventions/` (`gate/policy.py RENAMED_SKILLS`); `/sdlc-init` reports each old path in `legacy_paths`, and a `.claude/settings.json` rule that names `sdlc:ux-conventions` as not honoured, since a permission rule cannot be aliased.
4. **The merge workflow's `doorbell` is `on-approval`** (N5): the job id, `merge_step.py on-approval` (with `doorbell` still accepted, so an old copy keeps working) and its log prefix.
5. **"fallback C1" is "no merge App"** (N7), in the merge workflow, the digest's reason ("no merge App: merge it yourself"), `/sdlc-init`, `/sdlc-deploy` and `docs/OPERATING_MODEL.md` (its gate table and its merge-workflow row, which also name the job `on-approval`).
6. **The decision it renames, annotated** (choice 126): decision 36's point 7, beside its C1 sentence.

## How it was built
One sub-agent built the renames on this branch; this session merged `main`, bumped the version, regenerated `plugin/init/template_hashes.json` and ran the suite. Tests that asserted the old names assert the new ones; none was deleted or skipped; tests show each old name is still read.

## The fresh-context review
A fresh-context sub-agent reviewed the diff (report only). It found nothing blocking, and ran `/sdlc-init`'s upgrade end to end from v1.0.45's install: a pristine `sdlc-evals.yml` (LF and CRLF) is `removed (was 1.0.27)` and the new file created, an edited one is kept and the new one waits, a second run changes nothing, and the shipped manifest equals a fresh `template_hashes()`. Its findings and what was done:
1. **Fixed:** `docs/OPERATING_MODEL.md` still named "fallback C1" and the `doorbell` job in two rows; `README.md` still listed `ux-conventions`.
2. **Fixed:** the record left out this repository's pin window (below).
3. **Optional, taken:** `/sdlc-init`'s report lists the removed copies (`report["removed"]`, with a test) and its command text names the new states; the "not installed" line says a renamed edited copy then reads as outdated and keeps its edits.
4. **Optional, not taken:** the settings check matches any mention of `ux-conventions` in `.claude/settings.json`, not only a rule (the message is advice either way); the old copy is removed before the new one is written (a failure in between leaves neither; the next run installs the new one).

## In this repository until the pin moves
Once the owner commits this PR's merge workflow copy, its `on-approval` job runs `merge_step.py on-approval` against the pinned plugin, and a pin below 1.0.46 has no such subcommand: the job exits 2 and no merge is dispatched. So, until this repository's pin moves to 1.0.46 or later, an approved build PR here is merged by the owner (none is open; no change is in flight). The single pin move the owner chose comes next, after this PR.

## Port list
This PR touches none of `plugin/detect/` or the detect, runbook and fix workflow templates; its docstring edit in `plugin/ci/run_phase.py` (the "no merge App" wording) puts it on the port list until the 1.0.0 read.

## Proposed edits for the owner
- **The merge workflow's copy** is the owner's commit on this branch with `python tasks.py workflow-copies` (the PR body).
- **`.github/workflows/framework-evals.yml`** is this repository's own workflow, not a template copy, so the task does not write it:

| Link | Row | What is there | What it must become |
|---|---|---|---|
| `.github/workflows/framework-evals.yml` | 4 | `# changes the plugin and nightly. Not a template: a project gets sdlc-evals.yml instead.` | `# changes the plugin and nightly. Not a template: a project gets sdlc-agent-evals.yml instead.` |

`CLAUDE.md`, `REVIEW.md`, the root `sdlc.yaml` and `.claude/settings.json` name none of the old names (checked with `grep` on this branch).

## What the owner does
| When | Act |
|---|---|
| Now | Write and commit the workflow copy on `claude/r45-4-files` with `python tasks.py workflow-copies`, and the one comment line above, then merge the PR when `Framework checks` is green on its final head. |
| Then | This repository's single pin move (the owner's default, the central session's message of 2026-10-25, 22:26 UTC). |
