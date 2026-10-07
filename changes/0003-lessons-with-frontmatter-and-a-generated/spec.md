# Spec: lessons with frontmatter and a generated index
Change id: 0003. Status: proposed. Produced by: sdlc plugin 0.3.5, /sdlc-design prompt v1 (article p.14). Skills: coding-standards, security-baseline, ux-conventions, data-conventions, definition-of-done (plugin 0.3.5); overrides: none

## Requirements
- Every lesson `/sdlc-deploy` step 0b writes opens with a frontmatter block whose fields are
  read from a file the (e) run already has, never typed in when a source exists: `type`
  (`Lesson`), `title` (`status.yaml: title`), `description` (one sentence, written by the
  run), `tags` (class, metric, runbook — see Open questions), `change` (`status.yaml: id`),
  `detected` (`{at, metric, tier, rule}` from `evidence/detection.json`), `fixed` (`{pr}` from
  `status.yaml: build_pr`), `runbook` (from `evidence/proposal.json` /
  `status.yaml: runbook_authorized_by`, absent when none ran), `supersedes` (an earlier
  lesson's file name, when this incident repeats its class), `generated` (`{by:
  sdlc-plugin/<version>, at}`), `status` (`stable` at writing), `stale_after`
  (`generated.at` + 12 months, or `sdlc.yaml: lessons.stale_after_months`) and `sources`
  (`[{id, resource}]` for `detection`, `eval`, `fix-pr`, one `run-<n>` per failed run
  `detection.json` lists). The four body sections of today's shape stay (`## What happened`,
  `## Root cause`, `## Fix`, `## Prevention`, `template/lessons/README.md:23-34`), with keyed
  footnotes where the body cites a source; the prose header line
  (`template/lessons/README.md:21`) moves into frontmatter and is dropped from the body.
  Filename convention is unchanged: `lessons/<yyyy-mm>-<slug>.md`
  (`template/lessons/README.md:14`).
- `lessons/index.md` has exactly one writer: a new module `plugin/lessons/index.py` (Python,
  standard library only), with `build --root <path>` (rewrites the index from every
  `lessons/*.md` frontmatter — a heading per first tag, one line per lesson newest-first
  within a heading, `## Retired` last, `## Unsorted` for a file without a frontmatter block,
  `(stale)` appended when `stale_after` is past) and `check --root <path>` (exit 1 and the
  diff when the index on disk is not what `build` would write). `/sdlc-deploy` step 0b runs
  `build` in the same commit as the lesson and the eval (extending the commit convention
  already at `plugin/commands/sdlc-deploy.md:82-83`).
- `/sdlc-maintain` step 1 (today: "Every file under `lessons/`",
  `plugin/commands/sdlc-maintain.md:45`) instead reads `lessons/index.md` first, runs `check`
  first, and opens only the lessons whose tags name the metric or the rule in
  `detection.json`, plus `## Retired`. When the index is stale or missing it reads every file
  as today and says so in one line of the intent's `## Evidence` section. The maintain run
  commits nothing but the intent (unchanged), so it never rebuilds the index itself.
- `status` is `stable` or `retired`, nothing else. The only two writers of `retired`: the
  owner by hand in a reviewed PR, or step 0b of a later incident change whose lesson carries
  `supersedes: <file>` — which sets the earlier lesson's `status: retired` and adds
  `retired_by: <the new file>` in the same commit. No other writer edits an existing lesson
  (choice 126 applied to lessons, `docs/proposals/okf-adoption.md:256-257`). `stale_after` is
  written once, at creation; staleness is computed when a lesson is read (the index line's
  `(stale)`, the maintain run's reading) — no kept lesson is ever rewritten by a date passing.
- Links a script can follow, unchanged from intent: `change` → `changes/<id>-<slug>/`,
  `sources.eval` → `evals/cases/<id>-<slug>/`, `sources.fix-pr` → the build PR,
  `sources.run-<n>` → the failed runs, `supersedes`/`retired_by` between lessons, the index
  line → the file. Nothing links back from the change folder.
- Gate (e)'s `check_artifacts` (`plugin/gate/checks.py:186-227`, already special-cased for
  `entry_route == "incident"` at `checks.py:205-211`, wired into phase `e` at
  `checks.py:1646-1648`) gains, in that same branch, three more checks for an incident
  change: the lesson file exists with every required frontmatter field, the eval case folder
  (`evals/cases/<id>-<slug>/`, shape fixed by `plugin/evals/case.py`) exists, and
  `plugin/lessons/index.py check` passes. A `supersedes` target that does not exist, or a
  `status` outside `stable | retired`, fails the same check. Each failure is one more entry
  in the existing `problems` list, so each gets its own "what I need from you" line through
  the existing `_fail(name, reason, need, **details)` plumbing — no new check-registration
  machinery.
- `template/lessons/README.md` is rewritten to describe the new shape (the frontmatter, the
  footnote convention, the index) in place of the prose header line. A project that already
  has lessons in today's shape keeps them readable: a file without frontmatter is listed
  under `## Unsorted` with its first heading as its title, reported by `check`, and read by
  the maintain run as today.
- `template/sdlc.yaml` gains one commented row, in the style of the existing
  `automation_identity` commented row (`template/sdlc.yaml:113-120`), documenting the
  optional key `lessons.stale_after_months` and its default of twelve months; read only when
  a project sets it.
- `docs/OPERATING_MODEL.md` §9's `lessons/` bullet (`docs/OPERATING_MODEL.md:144`) gains one
  sentence naming the frontmatter and the generated index.
- No item of `sdlc.yaml: risk_list` applies: this change adds no authentication, no money
  movement and no production-config path, and "data migrations" names a migration of stored,
  queried data — a new markdown frontmatter convention on a project-content file is not that
  (data-conventions rule 3). None of the four is named under Flagged concerns.
- Checkable, per intent: tests under `tests/` for the index builder (ordering by first tag,
  the `## Retired` heading, the stale marker, `check` on a drifted index, a file without
  frontmatter under `## Unsorted`), for the new gate sub-checks, and for the two command
  files' instructions (the existing pattern of `tests/test_evals.py:701-767` and the
  instruction tests in `tests/test_commands_and_skills.py`); `python -m compileall`,
  `python -m pytest`, `python -m ruff check .` and `python -m ruff format --check .` green;
  `claude plugin validate .` clean; both manifests (`.claude-plugin/plugin.json:4`,
  `.claude-plugin/marketplace.json:11`, cross-checked by
  `tests/test_scaffold.py:41-47`) at **0.3.6**.

## Design
- New module `plugin/lessons/index.py`, mirroring the CLI shape `plugin/evals/case.py`
  already uses in this plugin (argparse `main(argv)`, subcommands, JSON or plain-text stdout,
  non-zero exit on failure) rather than inventing a new command convention.
- Frontmatter is a `---`-delimited YAML block at the top of the lesson file, parsed with the
  same split this repo already uses for `SKILL.md` frontmatter
  (`^---\n(.*?)\n---\n(.*)$`, `tests/test_policy_skills.py:28`) and then read/written with
  `plugin/state/yamlish.py` — the dependency-free YAML subset `status.yaml` and `sdlc.yaml`
  already use. `yamlish` already supports everything the fields need: nested mappings
  (`detected`, `fixed`, `generated`), lists of mappings (`sources`), and a leading `---`
  document marker is already skipped by its reader (`plugin/state/yamlish.py:122-123`). No
  new parser and no third-party dependency (`sdlc.yaml`'s own constraint,
  `plugin/state/yamlish.py:1-6`: a missing import must not turn a guardrail off silently).
  `yamlish.dump_file` writes with an explicit `newline="\n"`
  (`plugin/state/yamlish.py:309-310`) on every platform, so the index `build`/`check` byte
  comparison is stable on Windows and Linux without extra normalization code.
- Precedent and its limit: `docs/notes/*.md` already carry a comparable frontmatter
  (`title`, `sources`, `generated.at`, `verified_with`, `stale_after` —
  `docs/notes/1.md:1-6`), so the shape is not a new idea in this codebase. But
  `docs/notes/index.md` is hand-written prose (no script builds or checks it; a repo-wide
  search for an index-generator under `plugin/` found none) — `plugin/lessons/index.py` is
  the first generated index in this codebase, not a port of an existing one.
- Field sources, exact to the intent's table: `status.yaml` fields `id` (`status.py:36`),
  `title` (`status.py:38`), `entry_route` (`status.py:44`), `build_pr` (`status.py:89`),
  `runbook_authorized_by` (`status.py:81`); `evidence/detection.json`, built by
  `plugin/detect/finding.py:build_record` (`finding.py:40-80`), carrying `metric`
  (`finding.py:58`), `tier` (`finding.py:62`), `rule` (`finding.py:54,64`), `at`
  (`finding.py:61`); `evidence/proposal.json`, shaped by `Proposal`
  (`plugin/detect/routes.py:80-98`, fields `route`, `tier`, `args`, `rationale`) and resolved
  by `Resolved` (`routes.py:55-77`, fields `route`, `runbook`) — the lesson's `runbook` field
  should read the *resolved* route/runbook (what actually ran), not the proposed one, since a
  proposal can be overridden before it runs.
- Gate wiring stays inside the existing `check_artifacts` function and its `problems` list
  (`checks.py:186-227`); no new entry in `CHECKS_BY_PHASE` and no new `CheckResult` shape.
  This keeps the new checks subject to the same "what I need from you" rendering
  (`plugin/gate/gate.py:76-79`) every other artifact failure already uses — satisfying
  ux-conventions rule 4 (error text says what happened and what to do next) without new copy.
- `plugin/evals/case.py`'s case folder (`prompt.md`, `checks.yaml`) is the only shape the
  gate can check mechanically; it cannot verify that `checks.yaml` "asserts something real"
  (the command text's own caution, `plugin/commands/sdlc-deploy.md:66-84`). That judgment
  stays with the review passes and the adversarial reviewer, matching how this plugin already
  splits deterministic gate checks from advisory judgment elsewhere (skill
  `definition-of-done`: "the gate itself is the enforcement; this skill is advisory").
- `template/sdlc.yaml` and `docs/OPERATING_MODEL.md` are plugin-shipped content, not this
  repository's own guardrails: CLAUDE.md's guardrail list is `.claude/**`, `CLAUDE.md`,
  `REVIEW.md` and this repository's own root `sdlc.yaml` — `template/sdlc.yaml` is the
  template a project's `/sdlc-init` copies, and `docs/OPERATING_MODEL.md` is not on the
  guardrail list at all. Both are edited with the Edit tool like any other plugin file in
  phase (c); this repository's own `sdlc.yaml`/`CLAUDE.md`/`REVIEW.md`/`.claude/**` stay
  untouched, exactly as the intent's Constraints already say.
- No stored personal or sensitive field is added (data-conventions rule 1): every new
  frontmatter field is a constant, a date, a tag, or a link to an internal, non-personal
  identifier (change id, PR number, run URL) — the same class of data a lesson's prose body
  already carries today.

## Open questions from intent
- "Which tag comes first, and how are tags spelled? ... Proposed answer: the class first,
  then the metric, then the runbook; kebab-case, so one class is one heading." — Answered:
  adopt the intent's proposed order (class, then metric, then runbook; kebab-case), confirmed
  from the codebase rather than only from the proposal: a project configures exactly one
  `maintain.metric` (`sdlc.yaml:35`: `metric: ci_test_failure_rate`), so metric-first grouping
  would put every lesson of a typical project under a single heading until that project
  starts watching more than one metric — the exact failure mode the intent's own reasoning
  anticipated. Class is free text the (e) run names (no enum field in `detection.json`
  supplies it structurally, except that a security-scan finding's `metric` string already
  embeds a class, e.g. `"security: <class>"`, `plugin/detect/finding.py:158`); see Flagged
  concerns.
- "Sharing lessons across projects ... the owner decides it as item 4 of `HANDOFF.md`,
  because it touches decisions 8 and 9. Until then every lesson lives in its project's
  `lessons/`, which is what this change builds." — Carried forward, as the intent directs:
  not this change's decision (`HANDOFF.md:60-61`, item 4; decisions 8 `docs/decisions/8.md`
  and 9 `docs/decisions/9.md` unchanged).
- "Frontmatter for eval cases ... a later R1 row through its own intent. The lesson's link
  to the case is enough for the maintain run." — Carried forward, as the intent directs: this
  change links to `evals/cases/<id>-<slug>/` (`plugin/evals/case.py`'s existing shape) and
  changes nothing inside it.

## Flagged concerns
- The `class` part of `tags` is free text the (e) run names at write time, with no controlled
  vocabulary and no normalization beyond kebab-case: a spelling drift (`flaky-test` one month,
  `flaky_test` or `flakytest` the next) silently creates a second index heading for the same
  class, and nothing in this design catches it. Assumption made because the intent assigns
  naming "the class" to the run but does not say whether a fixed vocabulary is needed; left
  open for the owner — a controlled list (e.g. a short enum in `sdlc.yaml` or
  `bands.yaml`) is a possible answer but is not this spec's to decide unprompted.
- [x] Eval-case content quality is not something the deterministic gate check can verify:
  decided — the new check confirms only that `evals/cases/<id>-<slug>/{prompt.md,checks.yaml}`
  exist, per the existing split between deterministic gate checks and advisory review
  (skill `definition-of-done`, "the gate itself is the enforcement; this skill is advisory").
  Whether the eval "asserts something real" is a review-pass and adversarial-reviewer
  judgment, as it already is for every other eval case in this plugin.
- [x] Cross-platform stability of the generated index's byte comparison (the owner works on
  Windows; `check` must not false-positive on a line-ending difference): decided —
  `plugin/lessons/index.py` writes through `plugin/state/yamlish.py`'s `dump_file`, which
  already forces `newline="\n"` on every platform (`plugin/state/yamlish.py:309-310`), the
  same convention `status.yaml`/`sdlc.yaml` rely on today.

## Acceptance
- `python -m compileall -q plugin tests tasks.py`, `python -m pytest`,
  `python -m ruff check .` and `python -m ruff format --check .` all green;
  `claude plugin validate .` clean.
- New tests pass: the index builder's ordering (first tag, newest-first within a heading),
  the `## Retired` heading, the `(stale)` marker, `check`'s exit 1 and diff on a drifted
  index, a frontmatter-less file listed under `## Unsorted`; the gate's three new incident
  sub-checks (missing lesson, missing eval case, failing `index.py check`, a dangling
  `supersedes`, an out-of-enum `status`) each produce their own "what I need from you" line;
  the updated instructions in `plugin/commands/sdlc-deploy.md` and
  `plugin/commands/sdlc-maintain.md` pass their existing instruction tests.
- `tests/test_scaffold.py`'s manifest cross-check passes with both
  `.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json` at `0.3.6`.
- `docs/OPERATING_MODEL.md:144` carries the new sentence; `template/lessons/README.md`
  describes the frontmatter, footnote and index shape; `template/sdlc.yaml` documents
  `lessons.stale_after_months`. No lesson file exists in this repository or the sample to
  migrate, so acceptance does not include a migration step.
