---
type: Proposal
title: "/sdlc-init refreshes the files it wrote once, when nobody edited them"
description: "A re-run of /sdlc-init keeps every project file the template wrote: the workflow copies and the pin script are reported outdated and left alone, and the project READMEs and evals/check.py are never compared. So an upgraded project keeps the text and the steps of the plugin it was set up with, and every upgrade is a session's hand copy. A copy the owner never edited is recognised by its hash and replaced in the same upgrade PR as the pin; an edited copy and every guardrail file are only reported."
status: accepted
roadmap: R64
sources:
  - id: init-command
    resource: "plugin/commands/sdlc-init.md lines 72-83, plugin/init/sdlc_init.py (WORKFLOW_FILES line 304, OUTDATED line 352, install_workflows line 364, the \"kept\" report line 597), on main at 8474c93"
    title: "What a re-run of /sdlc-init writes, reports and leaves"
  - id: sample-readmes
    resource: "the sample's changes/README.md and evals/README.md before sample PR #91 (merged as 4a429c4): byte-identical to template/changes/README.md at cb23707 (2026-09-19) and template/evals/README.md at e49589c (2026-09-21), matched by git blob hash in the framework's history"
    title: "Two READMEs a month old on the sample"
  - id: sample-upgrades
    resource: "the sample's commit fbea83b (the 13 workflow copies from 1.0.10) and sample PR #90 (merged as d8290c1, the copies from 1.0.17): each a session's hand copy of the template; #90's release record step passes --released and --acceptance, which plugin 1.0.14 does not accept, so it had to merge after the pin PR #89"
    title: "Every upgrade of the workflow copies is done by hand, in an order the owner must keep"
  - id: owner
    resource: "the owner's message of 2026-10-20 in session ccr-5953b5a0-gblc0q: \"Write it and register it in roadmap. You decide where's its best implementation order among the other items.\""
    title: "Accepted, the rank delegated to the session"
generated: { by: sdlc-framework-session/ccr-5953b5a0-gblc0q, at: 2026-10-20T17:55:00Z }
---

# /sdlc-init refreshes the files it wrote once, when nobody edited them

**Status: accepted by the owner on 2026-10-20 (choice 245), the rank left to the session.** Nothing is built. It changes `plugin/` and `template/`, so it takes the next free patch version when it is built.

## The problem
- **A re-run keeps everything.** `/sdlc-init` installs the 13 workflows and the pin script create-only. On a re-run, a copy that differs from the template is reported `outdated` and left in place for the owner to replace by hand (`plugin/init/sdlc_init.py`, `install_workflows`). The other project files it writes create-only (`changes/README.md`, `evals/README.md`, `evals/check.py`, `lessons/README.md`, `REVIEW.md`, `bands.yaml`) are reported `kept` and never compared. The command says so itself: "on an upgraded project these files may still describe an older plugin" (`plugin/commands/sdlc-init.md`).
- **The sample shows the cost.** Until sample PR #91, its `changes/README.md` and `evals/README.md` were the unedited text of the templates of 2026-09-19 and 2026-09-21. Every phase session reads the first, because the sample's `CLAUDE.md` says "see `changes/README.md`". The second still said the eval runner did not exist and showed an older `checks.yaml` shape.
- **Every upgrade of the copies is a session's hand work** (the sample's `fbea83b` for 1.0.10, sample #90 for 1.0.17), and it comes with an order the owner must keep. #90's release record step passes options plugin 1.0.14 does not accept, so it could merge only after the pin PR #89.
- **It will get worse at R45.** The rename changes the branch, label and phase names that both READMEs and all 13 workflows carry. Without a refresh, every project that upgrades keeps the old names in the files its sessions read.

## The change
1. **A copy nobody edited is recognised.** The plugin ships the hash of every create-only template file at every released version (a file under `plugin/init/`, kept current by a test that fails when a template file changes and its new hash is missing). A project file whose content, with `{{FRAMEWORK_REPO}}` filled as `/sdlc-init` fills it, matches one of those hashes is pristine: the template wrote it and nobody changed it.
2. **A re-run replaces a pristine older copy** with this version's template and reports `refreshed (was <version>)`. This covers the workflow copies, the pin script, `changes/README.md`, `evals/README.md`, `evals/check.py` and `lessons/README.md`.
3. **An edited copy is never overwritten.** It is reported `outdated (edited)`, as a workflow copy is today, with the template path to diff against.
4. **The guardrail files are never refreshed**: `REVIEW.md`, `bands.yaml`, `CLAUDE.md`, `sdlc.yaml` and `.claude/**` (decision 6). An outdated one is reported, and the owner edits it in a reviewed PR as today.
5. **The pin and its copies move together.** The re-run already writes `sdlc.yaml` into the PR the owner merges, so the refreshed copies ride in that same PR as the pin. The ordering of sample #89 and #90 disappears.

Tests: a pristine copy of an older version is replaced, an edited one is kept and reported, a guardrail is never written, and a file with no recorded hash is reported, never replaced.

## What to settle at the build
- Where the hashes come from for the versions already released: read from the framework's own tags once, by a script, or recorded only from this build on (older copies then stay `outdated`).
- Whether `evals/check.py`, which is code the project may run, is refreshed like the READMEs or only reported.
- The report's exact words, and whether `/sdlc-init` prints the list of refreshed files for the PR body.

## Order
**After R27 and before R45, with no rank moved.** *[2026-10-22, R65's part 3 (docs-lint check 11): "R27 (rank 19)" and "R45 (rank 20)" stood here; ROADMAP's Order column holds the ranks]*
- **Why before R45:** the rename rewrites the names in both READMEs and every workflow copy. Built first, one re-run on each project carries the rename into its files. Built after, every project needs a hand copy at the rename, the costliest moment.
- **Why after R61:** R61 changes what `/sdlc-init` writes on a first install, in the same file (`plugin/init/sdlc_init.py`). Building this after it avoids reworking a moving file.
- **Why not sooner:** the sample is current since sample PRs #90 and #91, and no other project exists until the real-project trial.

## Decisions it touches
Decision 8 is kept: plugin plus template, the version pinned per project. This answers the "copies drift" its reasoning names, for the copies a project never edits. Decision 6 is kept: guardrail files stay the owner's edit. None is amended.
