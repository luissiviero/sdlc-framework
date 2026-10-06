# Intent: lessons with frontmatter and a generated index
Author: Claude, drafted for Luis Siviero (owner). Status: proposed. Change id: 0003. Entry route: idea.
Framework change: yes

## Problem
A lesson is the post-mortem of an incident, written when its fix ships (the (e) run of a change
whose entry route is `incident`, `/sdlc-deploy` step 0b) and read before the next diagnosis
(`/sdlc-maintain` step 1, article p.49: "a version-controlled lessons file that future
investigations can read"). Today a lesson is prose with one header line (`Change: … · Detected: …
· Fixed: …`, `template/lessons/README.md`). Nothing can read that line without parsing prose, so
the maintain run opens every file under `lessons/` on every diagnosis. With five lessons that is
cheap; with eighty it is the difference between a diagnosis that fits the run's budget and one
that does not. Nothing says when a lesson no longer describes the code (the layer it names may be
gone), nothing links the lesson to the change folder, the fix PR, the failed runs or the eval case
in a form a script can follow, and nothing checks at gate (e) that an incident's fix shipped with
its lesson and its eval at all.

This is step 1 of roadmap candidate R1 (`docs/proposals/okf-adoption.md`), narrowed to `lessons/`
and designed by session 19 in that proposal's section "R1 on `lessons/`: the design". Step 2 of R1
(the docs split) was change 0001. No lesson file exists yet in this repository or in the sample,
so there is nothing to migrate.

## Proposed outcome
- Every lesson written by `/sdlc-deploy` step 0b opens with a frontmatter block whose every field
  is read from a file the (e) run already has, never typed in by the model when a source exists:
  `type` (`Lesson`), `title` (`status.yaml: title`), `description` (one sentence in the metric's
  terms, written by the run), `tags` (the metric from `evidence/detection.json`, the runbook that
  ran if one did, then the class the run names), `change` (`status.yaml: id`), `detected`
  (`{at, metric, tier, rule}` from `evidence/detection.json`), `fixed` (`{pr}`, the build PR
  from `status.yaml: build_pr`; no `at`, because the merge comes after the lesson is written),
  `runbook` (the route performed, from `evidence/proposal.json` and
  `status.yaml: runbook_authorized_by`; absent when none ran), `supersedes` (an earlier
  lesson's file name when this incident repeats its class), `generated` (`{by:
  sdlc-plugin/<version>, at}`), `status` (`stable` at writing), `stale_after` (`generated.at`
  plus twelve months, or `sdlc.yaml: lessons.stale_after_months` when the owner sets that
  optional key) and `sources` (`[{id, resource}]`: `detection`, `eval`, `fix-pr`, one `run-<n>`
  per failed run the detection record lists). The four body sections of today's README (what
  happened, root cause, fix, prevention) stay, with keyed footnotes where the body cites a
  source; the prose header line goes.
- `lessons/index.md` has one writer: `plugin/lessons/index.py` (Python, standard library), with
  `build --root .` (rewrites the index from every `lessons/*.md` frontmatter: a heading per
  first tag, one line per lesson, newest first within a heading, `## Retired` last,
  `## Unsorted` for a file without frontmatter, `(stale)` appended when `stale_after` is past)
  and `check --root .` (exit 1 and the difference when the index on disk is not what `build`
  would write). Step 0b runs `build` right after writing the lesson, in the same commit as the
  lesson and the eval. The index is never edited by hand; a hand edit is undone by the next
  `build`.
- `/sdlc-maintain` step 1 reads `lessons/index.md` first and opens only the lessons whose tags
  name the metric or the rule in `detection.json`, plus `## Retired`. It runs `check` first;
  when the index is stale or missing it reads every file as today and says so in one line of the
  intent's Evidence section. The maintain run commits nothing but the intent, so it never
  rebuilds the index itself.
- `status` is `stable` or `retired`, nothing else. Only two writers set `retired`: the owner by
  hand in a reviewed PR, or step 0b of a later incident change whose lesson carries
  `supersedes: <file>`, which sets the earlier lesson's `status: retired` and adds
  `retired_by: <the new file>` in the same commit. Staleness is not a status: `stale_after` is
  written once and whether a lesson is stale is computed when it is read (the index line's
  `(stale)`, the maintain run's reading), so no file changes when a date passes and no kept
  lesson is ever rewritten (PROGRESS choice 126). A stale lesson is still read; the maintain run
  says when it relied on one.
- The links a script can follow: `change` to `changes/<id>-<slug>/`, `sources.eval` to
  `evals/cases/<id>-<slug>/`, `sources.fix-pr` to the build PR, `sources.run-<n>` to the failed
  runs, `supersedes` and `retired_by` between lessons, the index line to the file. Nothing links
  back from the change folder: the lesson's file name is the change's slug with the month in
  front, as today.
- The gate's `artifacts` check at (e), for a change whose entry route is `incident`, also
  requires: the lesson file exists with the frontmatter fields above, the eval case folder
  exists, and `check` passes; a `supersedes` target that does not exist or a `status` outside
  `stable | retired` fails the same check. Each failure has its own "what I need from you"
  line.
- `template/lessons/README.md` describes the new shape (the frontmatter, the footnote
  convention, the index) and `/sdlc-init` copies it as today. A project that already has lessons
  in today's shape keeps them readable: a file without frontmatter is listed under `## Unsorted`
  with its first heading as its title, reported by `check`, and read by the maintain run as
  today.
- `template/sdlc.yaml` gains one commented row documenting the optional key
  `lessons.stale_after_months` and its default of twelve months, so an owner can find it; the
  key is read only when a project sets it. The `lessons/` bullet of `docs/OPERATING_MODEL.md` §9
  gains one sentence naming the frontmatter and the generated index, so the contract stays true.
- Checkable: tests under `tests/` for the index builder (ordering, the retired heading, the stale
  marker, `check` on a drifted index, a file without frontmatter), for the gate check and for the
  two command files' instructions where a test reads them today; `python -m compileall`,
  `python -m pytest`, `python -m ruff check .` and `python -m ruff format --check .` green;
  `claude plugin validate .` clean; both manifests at **0.3.6**.

## Affected users and systems
- The owner, who merges this change and, after the tag, moves the root `sdlc.yaml` pin to 0.3.6
  as a guardrail row.
- `plugin/lessons/index.py` (new), `plugin/commands/sdlc-deploy.md` step 0b,
  `plugin/commands/sdlc-maintain.md` step 1, `plugin/gate/checks.py` and `plugin/gate/artifacts.py`
  (the `artifacts` check for an incident change at (e)), `template/lessons/README.md`,
  `tests/`, the two plugin manifests, and the one line of `docs/OPERATING_MODEL.md` §9 that
  describes `lessons/`.
- Every project on the plugin from 0.3.6: the (e) run of an incident change writes the
  frontmatter and the index; the (f) run reads the index first.
- Not affected: the sample repository, which stays at plugin 0.2.30 and its copies until item 11
  of `HANDOFF.md` (PROGRESS choice 138); `plugin/detect/`, `plugin/ci/run_phase.py` and the
  detect, runbook and fix workflow templates (the port list for the 1.0.0 read stays empty);
  the eval cases' own shape (`evals/cases/<id>-<slug>/`, `plugin/evals/case.py`), which the
  lesson only links.

## Constraints
- Python, standard library only, for the index writer and the gate check; it must run on Windows
  and Linux (the owner works on Windows); paths in the index with forward slashes.
- No guardrail file changes: this repository's root `sdlc.yaml`, `CLAUDE.md`, `.claude/**` and
  `REVIEW.md` are untouched (`template/sdlc.yaml` is plugin-shipped content, edited in a reviewed
  PR like any plugin file). `lessons.stale_after_months` is optional and read only when present,
  so no project's `sdlc.yaml` needs an edit. The root pin moves after the tag, as a guardrail row
  for the owner.
- A kept lesson is never rewritten (choice 126): the only edit to an existing lesson is
  `status: retired` plus `retired_by`, by the two writers named above.
- No decision is reopened: 8 and 9 (where lessons live and the repo as the source of truth) and
  17 (evals and lessons grow from incidents) are unchanged.
- No third-party runtime dependency; no workflow template changes.
- The sample is frozen until item 11 (precondition 6 of `HANDOFF.md`): nothing in this change is
  pushed to it or copied into it.
- Plugin 0.3.6; the change's own phases on this repository are the live test of 0.3.5 and the
  shakedown of 0.3.6 (choice 88): a framework gap a run finds gets a fix with a test in a 0.3.x
  PR before the next phase.

## Open questions
One question for the design pass:
- Which tag comes first, and how are tags spelled? The index groups lessons under a heading per
  first tag, so the first tag decides the grouping. The proposal's field table says the metric
  first, then the runbook, then the class; its example index groups by the class
  (`flaky-test`). Metric first would put every lesson of a project under one heading. Proposed
  answer: the class first, then the metric, then the runbook; kebab-case, so one class is one
  heading.

Two questions are not this change's and have a named owner; the design pass carries them forward
with that owner and does not answer them:
- Sharing lessons across projects (`docs/proposals/okf-adoption.md`, "Sharing lessons across
  projects"): the owner decides it as item 4 of `HANDOFF.md`, because it touches decisions 8 and
  9. Until then every lesson lives in its project's `lessons/`, which is what this change builds.
- Frontmatter for eval cases (`evals/cases/<id>-<slug>/`): a later R1 row through its own
  intent. The lesson's link to the case is enough for the maintain run.
