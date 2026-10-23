# Progress — R64, `/sdlc-init` refreshes the copies nobody edited, plugin 1.0.37 (2026-10-23)

This session is lane B of wave 3, started by the central session (`session_016NLfdsdfTFZUyrVGN4Ektc`). Its first PR, R27, merged as #367 (`84d4aa3`, plugin 1.0.35); its record is `docs/progress/2026-10-23-claude-r27-policy-sources.md`. This second PR builds R64 (`docs/proposals/template-copies-refresh.md`, accepted 2026-10-20, choice 245) on branch `claude/r64-template-copies-refresh`, from `main` at `84d4aa3`.

It changes `plugin/`, so it bumps the patch. `python tasks.py next-free` gave 1.0.37 after `git fetch origin` on `84d4aa3`: lane A's `claude/r18-failed-run-explains-itself` held 1.0.36. It takes no choice and no note.

## What was built
1. **`plugin/init/refresh.py`** recognises a copy the template wrote and nobody edited. Both sides are hashed in a canonical form (after the review, see below):
   - **the template's:** its `# sdlc:commands.env` marker lines dropped for a project with no names (`files`), kept for one with names (`files_marked`), `{{FRAMEWORK_REPO}}` kept;
   - **the copy's:** the project's framework repository put back as `{{FRAMEWORK_REPO}}`, each exact block the markers expanded to put back as its marker line, the `branches:` filter put back to `main`, and CRLF read as LF.

   `{{FRAMEWORK_REPO}}` is the only placeholder these files have had at any of the 75 tags (checked with `git show` on each tag). A copy rendered with values the project no longer has does not match, so it is treated as edited: kept, never overwritten.
2. **`plugin/init/template_hashes.json`** records, for each refreshed copy, the hash of every text its template had at a `v*` tag. Each hash keeps the first version that shipped it. `python tasks.py template-hashes` writes the file from the tags and the working tree. A test fails when the current template's hash is missing from it, so a template change cannot ship without its hash.
3. **The re-run** (`sdlc_init.refresh_copy`):
   - **A pristine older copy** of a workflow, the pin script, `changes/README.md`, `evals/README.md`, `evals/check.py`, `lessons/README.md` or `policies/README.md` is replaced with this version's and reported `refreshed (was <version>)`. The report's `refreshed` map lists them for the upgrade PR's body. The refreshed copies ride in the same PR as the pin.
   - **An edited copy is never overwritten.** A workflow keeps its `outdated: …` line, which now says the copy was edited. A README or `evals/check.py` says `kept; outdated (edited): …`.
   - **`REVIEW.md` and `bands.yaml` are guardrail files** (decision 6) and are never written. One that differs from this version's template is reported `kept; outdated: …` for the owner's reviewed PR. `CLAUDE.md`, `sdlc.yaml` and `.claude/**` keep their own merge rules.
4. **`plugin/commands/sdlc-init.md`** describes the three outcomes and asks the PR body to list the refreshed copies. The module's docstring does too.
5. **Tests**, in `tests/test_refresh.py`:
   - a pristine older copy is refreshed, and the next re-run is unchanged;
   - an edited one is kept and reported;
   - a copy with no recorded hash is never replaced;
   - a guardrail is never written, even when it matches an older template;
   - `evals/check.py` is refreshed like the READMEs;
   - every workflow canonicalises to its template under env names, another default branch and CRLF;
   - an owner's own env line is not taken for the markers;
   - the manifest knows every current template;
   - the manifest is well formed.

   A manual check against the real manifest: a v1.0.20 `changes/README.md` and `sdlc-design.yml` were refreshed (`was 1.0.15`, `was 1.0.19`), and an edited v1.0.20 `sdlc-test.yml` was kept.

## The fresh-context review
A fresh-context sub-agent reviewed `36f0f4c`, report only. It found nothing blocking. What it found, fixed with tests:
1. **Important: an env edit could pass as pristine.** The canonical form dropped every declared-name line wherever it sat, so an owner's change was overwritten when they:
   - (A) added such a line to a step without a marker;
   - (B) deleted the lines the markers wrote, which the refresh would put back as secrets;
   - (E) added an `env:` key holding only the names.

   The copy's exact rendered blocks (every name, in order, at a marker's place) are now put back as the marker line. A project with names is compared only with the marked templates (`files_marked`, manifest schema 2). A–E, a reordered block and a missing name are tested.
2. **Important: `template-hashes` in a clone without tags** would have written a manifest with today's hashes only. It now refuses (`NoTagsError`). A test runs the task on a small repository: first version kept, a file missing at a tag skipped, no tags refused. Another asserts the shipped manifest holds 0.2.x texts.
3. **A `branches: [main]` line on a project whose default branch is another** is an edit: the install rewrote every filter.
4. **The report blamed an edit** where the cause can be values the project no longer has; the wording now names both.
5. **Guardrail noise.** `REVIEW.md` is reported outdated only when an older release wrote it and nobody edited it; an edited one, and `bands.yaml` always, say `kept`.
6. **The test gaps** named above are closed.

**Known limit:** where the current template minus its markers equals a release from before the markers existed (1.0.29), a copy with no env lines is that release's pristine copy. For `sdlc-build.yml` that is 1.0.27's text. A project whose owner deleted the marker lines from a copy rendered with names is then indistinguishable from that older copy, and the refresh writes the lines back for the names `sdlc.yaml` still declares. Removing a name from `commands.env` is the way to drop it.

## Settled at the build (the proposal's "What to settle")
- **Where the hashes come from:** read from the framework's own tags, by a script (`tasks.py template-hashes`), not recorded only from this build on. The sample's copies from 1.0.10 and 1.0.17 are recognised, which is where the proposal's problem was seen.
- **`evals/check.py`:** refreshed like the READMEs. A pristine copy is the plugin's own code with nothing of the project in it, and a newer one carries the runner's fixes; an edited one is kept.
- **The report's words:** `refreshed (was <version>)`, the version being the first release that shipped the text the copy had. `/sdlc-init` prints the list as the report's `refreshed` map, and the command puts it in the PR body.

## Lane A's merge
#368 (R18, 1.0.36) merged as `9ffd7c3` and was merged into this branch. The version conflict keeps 1.0.37. R18 changed six workflow templates (`sdlc-build`, `-deploy`, `-design`, `-detect`, `-fix`, `-test`), so `python tasks.py template-hashes` was re-run after `git fetch --tags`; their new texts are labelled 1.0.36, the tag that shipped them.

## Port list
None: the PR touches no file under `plugin/detect/`, `plugin/ci/run_phase.py` or the detect, runbook and fix workflow templates.

## What the owner does
| When | Act |
|---|---|
| When lane B says this PR is ready | Merge it, in wave 3's order by version: lane A's 1.0.36 merged first (#368); the small lane's 1.0.38 after this one. |
