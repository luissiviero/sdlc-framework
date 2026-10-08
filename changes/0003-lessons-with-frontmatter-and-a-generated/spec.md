# Spec: lessons with frontmatter and a generated index
Change id: 0003. Status: proposed. Produced by: sdlc plugin 0.3.5, /sdlc-design prompt v1 (article p.14). Skills: coding-standards, security-baseline, ux-conventions, data-conventions, definition-of-done (plugin 0.3.5); overrides: none

## Requirements
- Every lesson `/sdlc-deploy` step 0b writes opens with a frontmatter block whose fields are
  read from a file the (e) run already has, never typed in when a source exists: `type`
  (`Lesson`), `title` (`status.yaml: title`), `description` (one sentence, written by the
  run), `tags` (class, metric, runbook — see Open questions), `change`
  (`status.yaml: id`), `detected` (`{at, metric, tier, rule}`, with the mapping
  `finding.read_any` implements (`finding.py:150-160`), which also covers an incident the
  weekly scan filed: `evidence/scan-finding.json` mapped to metric `security: <class>`, rule
  `scan`, tier 3, with no `run-<n>` source — a scan incident has no failed run), `fixed` (`{pr}` from
  `status.yaml: build_pr`), `runbook` (`evidence/proposal.json: route` when
  `evidence/runbook-<name>.json` exists with `status: ran`; absent otherwise, a failed or
  `go-requested` route included — `Resolved.route` is always the proposal's route, not
  necessarily what ran, and `status.yaml: runbook_authorized_by` is set only for a `go`
  route), `supersedes` (an earlier lesson's file name, when this incident repeats its
  class — when present, step 0b also edits that earlier lesson in the same commit, setting
  its `status: retired` and adding `retired_by: <this new file>`, the one case the status
  bullet below names as an edit to an existing lesson), `generated` (`{by:
  sdlc-plugin/<version>, at}`), `status` (`stable` at writing), `stale_after`
  (`generated.at` + 12 months, or `sdlc.yaml: lessons.stale_after_months`) and `sources`
  (`[{id, resource}]` for `detection`, `eval`, `fix-pr`, one `run-<n>` per failed run
  `detection.json` lists — absent for an incident the weekly scan filed, which has no failed
  run; the `detection` resource is `evidence/detection.json`, or `evidence/scan-finding.json`
  for an incident the weekly scan filed). The four body sections of today's shape stay (`## What happened`,
  `## Root cause`, `## Fix`, `## Prevention`, `template/lessons/README.md:23-34`), with keyed
  footnotes where the body cites a source; the prose header line
  (`template/lessons/README.md:21`) moves into frontmatter and is dropped from the body.
  Filename convention is unchanged: `lessons/<yyyy-mm>-<slug>.md`
  (`template/lessons/README.md:14`).
- `description` is one sentence, in the metric's terms.
- Both `plugin/commands/sdlc-deploy.md` and `plugin/commands/sdlc-maintain.md` add
  `Bash(python "${CLAUDE_PLUGIN_ROOT}/plugin/lessons/index.py" *)` to their `allowed-tools`
  frontmatter line, and each file's body quotes the call to `index.py` the same way.
- `lessons/index.md` has exactly one writer: a new module `plugin/lessons/index.py` (Python,
  standard library only), with `build --root <path> [--today YYYY-MM-DD]` (rewrites the
  index from every `lessons/*.md` frontmatter except `README.md` and `index.md` itself,
  excluded by name — a heading per first tag, one line per lesson newest-first within a
  heading, `## Retired` last, `## Unsorted` for a file whose frontmatter is missing or does
  not parse, `(stale)` appended when `stale_after` is before `--today`, default today's date)
  and `check --root <path> [--today YYYY-MM-DD]` (exit 1 and the diff when the index on disk,
  compared with any `(stale)` suffix stripped from both sides, is not what `build` would
  write — so a lesson crossing `stale_after` between two runs changes the index text with no
  file changed, and `check` must not treat that alone as drift). Both commands take
  `--today` only so `tests/test_lessons.py` can fix the clock; `/sdlc-deploy` step 0b passes
  none, so `build` uses the real date. A file whose frontmatter does not parse is listed
  under `## Unsorted` like a frontmatter-less file, never raises, and `build`/`check` print
  one line per `## Unsorted` file naming the parser's error (or "no frontmatter block") next
  to it; `check` exits 0 with `## Unsorted` entries present and prints that same one note
  line per `## Unsorted` file — only a drift of the generated text is exit 1.
  `/sdlc-deploy` step 0b runs `build` in the same commit as the lesson and the eval
  (extending the commit convention already at `plugin/commands/sdlc-deploy.md:82-83`). The
  index is never edited by hand.
- A hand edit of `lessons/index.md` is undone by the next `build`.
- The index is written with `Path.write_text(..., newline="\n")`, so `build`'s output is
  byte-identical on Windows and Linux; `check` reads the file on disk in Python's default
  universal-newline text mode before comparing, so a CRLF checkout does not false-positive as
  drift. Every link the index or the frontmatter renders (`change`, `sources.*.resource`,
  `supersedes`, `retired_by`) uses the native path's `.as_posix()` (`Path(...).as_posix()`,
  as `case.py:181` does) so it never carries a backslash regardless of platform — never
  `PurePosixPath(str(p)).as_posix()`, which keeps a backslash from a Windows path unconverted
  (the intent's forward-slash constraint).
- `/sdlc-maintain` step 1 (today: "Every file under `lessons/`",
  `plugin/commands/sdlc-maintain.md:45`) instead reads `lessons/index.md` first, runs `check`
  first, and opens only the lessons whose heading or tags name the metric or the rule in
  `detection.json`, plus `## Retired`. When the index is stale or missing it reads every file
  as today and says so in one line of the intent's `## Evidence` section. The maintain run
  commits nothing but the intent (unchanged), so it never rebuilds the index itself.
- `status` is `stable` or `retired`, nothing else. The only two writers of `retired`: the
  owner by hand in a reviewed PR, or step 0b of a later incident change whose lesson carries
  `supersedes: <file>` — which sets the earlier lesson's `status: retired` and adds
  `retired_by: <the new file>` in the same commit. No other writer edits an existing lesson
  (choice 126 applied to lessons, `docs/proposals/okf-adoption.md:256-257`). `stale_after` is
  written once, at creation; staleness is computed when a lesson is read (the index line's
  `(stale)`, the maintain run's reading) — no kept lesson is ever rewritten by a date
  passing.
- A stale lesson is still read, not skipped; the maintain run says in the intent's
  `## Evidence` section when it relied on a stale one.
- Links a script can follow, unchanged from intent: `change` → `changes/<id>-<slug>/`,
  `sources.eval` → `evals/cases/<id>-<slug>/`, `sources.fix-pr` → the build PR,
  `sources.run-<n>` → the failed runs, `supersedes`/`retired_by` between lessons, the index
  line → the file. Nothing links back from the change folder.
- Determinism the implementer would otherwise have to guess, written down here instead: the
  index opens with `# Lessons` and no frontmatter of its own; tag headings are ordered
  alphabetically by the normalised class; a normal line is
  `* [title](file) - description. Tier n, Mon yyyy. Tags: class, metric, runbook.` (the
  `Tags:` clause's `runbook` name omitted when the lesson carries no `runbook` field; the
  proposal's own shape, `docs/proposals/okf-adoption.md:229-230`, extended with the tags);
  `file` is the lesson's file name relative to `lessons/` (e.g. `2026-10-<slug>.md`), never a
  full path; `description` itself carries no trailing period, since the line template adds
  one; "Mon yyyy" is the month of `detected.at`; "newest first" within a heading sorts by
  `detected.at` descending, then by file name ascending on a tie; a `## Retired` line has the
  same shape as a normal line (title, file, description, tier, month, tags); an `## Unsorted`
  line is `* [first heading](file)` only, since an Unsorted entry has no parsed frontmatter to
  draw the rest from; `(stale)` is appended at the end of the line, on `## Retired` lines
  too; `## Unsorted` comes after `## Retired`, last; `build` on zero lessons writes the file
  with no tag heading and the one line `No lessons yet.`; the gate's `lesson_and_eval` check
  finds the lesson file by the glob `lessons/[0-9][0-9][0-9][0-9]-[0-9][0-9]-<slug>.md` (the
  year and month vary, the slug does not; a looser `lessons/*-<slug>.md` would also match a
  file whose name merely ends in another change's slug) — more than one match fails the
  check; the frontmatter fields the gate check requires are every field named in the first
  Requirements bullet except `runbook`, `supersedes` and `retired_by`, which stay optional
  (absent when no runbook ran, no earlier lesson is superseded, or this lesson was never used
  to retire one); "the eval case exists" means both `evals/cases/<id>-<slug>/prompt.md` and
  `evals/cases/<id>-<slug>/checks.yaml` exist.
- A new check function, `lesson_and_eval`, runs only when
  `ctx.status.entry_route == "incident" and ctx.phase == "e"` and is registered in
  `CHECKS_BY_PHASE` for phase `"e"` only — not inside `check_artifacts`'s existing
  `entry_route == "incident"` branch (`plugin/gate/checks.py:205-211`), which every gate from
  `a` to `f` runs: an incident change sits at `entry_route == "incident"` all the way through
  phase `f` too, so a check gated on the route alone would require the lesson and the eval
  before either exists and park every incident at gate (f)
  (`tests/test_gate.py::test_gate_f_waits_for_the_owner_s_triage_with_the_finding_and_its_route`
  is the regression guard: it asserts gate (f)'s check list and must keep passing unchanged).
  `lesson_and_eval` checks: the lesson file exists with every required frontmatter field;
  `evals/cases/<id>-<slug>/prompt.md` and `evals/cases/<id>-<slug>/checks.yaml` both exist
  (shape fixed by `plugin/evals/case.py`); `plugin/lessons/index.py check` passes; a
  `supersedes` target that does not exist fails, and so does a `supersedes` target whose
  `status` is not `retired` (proving step 0b's retirement write landed); a `status` outside
  `stable | retired` fails. Each problem is one line of text; the check returns one
  `CheckResult` whose `need` joins every problem's line with `"\n    "` (a newline and four
  spaces), so the existing "what I need from you" rendering (`plugin/gate/gate.py:76-79`,
  which prints `  - what I need: <need>` for one line) renders every later problem indented
  under that same bullet instead of at column 0; `tests/test_gate.py` asserts the whole
  rendered block, each problem on its own indented line, not just that each line is present
  somewhere in the text.
- `template/lessons/README.md` is rewritten to describe the new shape (the frontmatter, the
  footnote convention, the index) in place of the prose header line. A project that already
  has lessons in today's shape keeps them readable: a file without frontmatter is listed
  under `## Unsorted` with its first heading as its title; `check` exits 0 with it present
  and prints one note line naming it, and it is read by the maintain run as today.
- `/sdlc-init` copies `template/lessons/README.md` into a new project exactly as it does
  today; nothing about that step changes.
- `template/sdlc.yaml` gains one commented row, in the style of the existing
  `automation_identity` commented row (`template/sdlc.yaml:113-120`), documenting the
  optional key `lessons.stale_after_months` and its default of twelve months; read only when
  a project sets it.
- `docs/OPERATING_MODEL.md` §9's `lessons/` bullet (`docs/OPERATING_MODEL.md:144`) gains one
  sentence naming the frontmatter and the generated index.
- No workflow template changes: this change touches no file under a workflow template.
- The sample repository stays frozen at its pinned version (`HANDOFF.md` precondition 6,
  choice 138); nothing in this change is pushed to it or copied into it.
- Decisions 8, 9 and 17 are unchanged (lessons stay per-project; the repo stays the source of
  truth; evals and lessons grow from incidents).
- No item of `sdlc.yaml: risk_list` applies: this change adds no authentication, no money
  movement and no production-config path, and "data migrations" names a migration of stored,
  queried data — a new markdown frontmatter convention on a project-content file is not that
  (data-conventions rule 3). None of the four is named under Flagged concerns.
- Checkable, per intent: tests under `tests/` for the index builder (ordering by first tag,
  the `## Retired` heading, the stale marker, `check` on a drifted index, a file without
  frontmatter under `## Unsorted`), for the new `lesson_and_eval` gate check, and for the
  two command files' instructions (the existing instruction-test pattern in
  `tests/test_commands_and_skills.py`); `python -m compileall`,
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
  Every nested field (`detected`, `fixed`, `generated`, each item of `sources`) is written
  in block style, never flow style: `yamlish.loads` raises `YamlishError` on a flow mapping
  (`"flow mappings are not supported: ..."`, `plugin/state/yamlish.py:102`), and `title` and
  `description` are always double-quoted, since an unquoted scalar is truncated at ` #`
  (the same rule `status.yaml`/`sdlc.yaml` already live with). `plugin/lessons/index.py`
  reads a lesson file with `utf-8-sig` (strips a BOM an editor may have written) before
  splitting the frontmatter from the body. `template/lessons/README.md`'s example and
  `/sdlc-deploy` step 0b's instructions show block style and the quoting throughout.
- The index (`lessons/index.md`) is markdown, not YAML, so it is written directly with
  `Path.write_text(..., newline="\n")`, not through `yamlish.dump_file` (which writes YAML
  documents, not markdown): this keeps `build`'s output byte-identical on Windows and Linux.
  `check` reads the file on disk in universal-newline mode (Python's default text mode
  translates any of `\n`, `\r\n`, `\r` to `\n`) before comparing it with what `build` would
  write, so a CRLF checkout — the owner works on Windows — does not false-positive as drift.
  Every link in the index and the frontmatter (`change`, `sources.*.resource`, `supersedes`,
  `retired_by`) is rendered with the native path's `.as_posix()` (`Path(...).as_posix()`, as
  `case.py:181` does), so a path never carries a backslash regardless of platform (the
  intent's forward-slash constraint) — never `PurePosixPath(str(p)).as_posix()`, which treats
  a backslash as a literal character rather than a separator and so keeps it unconverted when
  the string came from a Windows path.
- Precedent and its limit: `docs/notes/*.md` already carry frontmatter with comparable
  fields (`title`, `sources`, `generated.at`, `verified_with`, `stale_after` —
  `docs/notes/1.md:1-6`), so a frontmatter block is not a new idea in this codebase — but
  that frontmatter is flat (`generated.at` is one key, not a nested `generated: {at: ...}`
  mapping), so it is not itself precedent for the lesson's nested fields; `yamlish`'s
  existing support for nested mappings and lists of mappings is why those are safe to add
  here, not the notes' example. `docs/notes/index.md` is hand-written prose (no script
  builds or checks it; a repo-wide search for an index-generator under `plugin/` found
  none) — `plugin/lessons/index.py` is the first generated index in this codebase, not a
  port of an existing one.
- Field sources, exact to the intent's table: `status.yaml` fields `id` (`status.py:36`),
  `title` (`status.py:38`), `entry_route` (`status.py:44`), `build_pr` (`status.py:89`);
  `detected` follows the mapping `finding.read_any` implements (`finding.py:150-160`) —
  step 0b is instruction text for the model, nothing in this plan calls that function —
  which is: `evidence/detection.json` when it exists (built by `plugin/detect/finding.py:build_record`,
  carrying `metric` (`finding.py:58`), `tier` (`finding.py:62`), `rule` (`finding.py:54,64`),
  `at` (`finding.py:61`)), else `evidence/scan-finding.json` mapped to `metric`
  `f"security: {class}"`, `rule` `"scan"`, `tier` 3 (`finding.py:150-160`); `runbook` is read
  from `evidence/proposal.json: route` (`Proposal`, `plugin/detect/routes.py:80-98`) only
  when `evidence/runbook-<name>.json` exists with `status: ran`, else absent — not from
  `Resolved` (`routes.py:55-77`): `Resolved.route` is always the proposal's route whether or
  not it ran, and `status.yaml: runbook_authorized_by` is set only for a `go` route, so
  neither tells the lesson what actually ran; the runbook record's `status` does.
- Gate wiring adds one check function, `lesson_and_eval`, registered in `CHECKS_BY_PHASE`
  for phase `"e"` only (not inside `check_artifacts`), guarded by
  `ctx.status.entry_route == "incident" and ctx.phase == "e"` so it never runs at gate (f),
  where the same `entry_route` is already `"incident"` but neither the lesson nor the eval
  exists yet. Each problem it finds is appended to a local list and joined with `"\n    "`
  (a newline and four spaces) into the one `CheckResult.need` string, so the existing "what
  I need from you" rendering (`plugin/gate/gate.py:76-79`, which prints
  `  - what I need: <need>` for one line) shows one problem per line, indented under that
  same bullet instead of at column 0 — satisfying ux-conventions rule 4 (error text says
  what happened and what to do next) without a new rendering path.
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
  not this change's decision (`HANDOFF.md`, item 4; decisions 8 `docs/decisions/8.md`
  and 9 `docs/decisions/9.md` unchanged).
- "Frontmatter for eval cases ... a later R1 row through its own intent. The lesson's link
  to the case is enough for the maintain run." — Carried forward, as the intent directs: this
  change links to `evals/cases/<id>-<slug>/` (`plugin/evals/case.py`'s existing shape) and
  changes nothing inside it.

## Flagged concerns
- [x] The `class` part of `tags` is free text the (e) run names at write time: decided — no
  controlled vocabulary now. `index.py build` normalises the class (lower-case; spaces and
  underscores turned to hyphens; one heading per normalised value), so a spelling drift
  (`flaky-test` vs. `flaky_test` vs. `Flaky Test`) cannot create a second index heading for
  the same class. For an incident the weekly scan filed, the class is the `class` field of
  `evidence/scan-finding.json`. No fixed vocabulary is defined: no lesson exists yet to name
  one from (decision 17: evals and lessons grow from incidents), and a list would be a
  guardrail-file edit (`sdlc.yaml` or `bands.yaml`) on every project for a problem this
  change has no evidence of yet. Revisit when a project has accumulated on the order of ten
  lessons and a real spelling-drift case to design the vocabulary from.
- [x] Eval-case content quality is not something the deterministic gate check can verify:
  decided — the new check confirms only that `evals/cases/<id>-<slug>/{prompt.md,checks.yaml}`
  exist, per the existing split between deterministic gate checks and advisory review
  (skill `definition-of-done`, "the gate itself is the enforcement; this skill is advisory").
  Whether the eval "asserts something real" is a review-pass and adversarial-reviewer
  judgment, as it already is for every other eval case in this plugin.
- [x] Cross-platform stability of the generated index's comparison (the owner works on
  Windows; `check` must not false-positive on a line-ending difference): reopened — the
  first close named `yamlish.dump_file` as the mechanism, but `dump_file` writes a YAML
  document and the index is markdown, so it is never the writer here; a concern is closed by
  a policy or the owner, not by a wrong mechanism. Decided (by the owner, this round): the
  index is written with `Path.write_text(..., newline="\n")` directly, `check` reads the
  file on disk in Python's default universal-newline text mode before comparing (so a CRLF
  checkout is read as `\n` and does not false-positive as drift), and every link the index
  or the frontmatter renders uses the native path's `.as_posix()` (`Path(...).as_posix()`,
  as `case.py:181` does — never `PurePosixPath(str(p)).as_posix()`, which keeps a backslash
  from a Windows path unconverted; the intent's forward-slash constraint, which the first
  version of this spec dropped).

## Acceptance
- `python -m compileall -q plugin tests tasks.py`, `python -m pytest`,
  `python -m ruff check .` and `python -m ruff format --check .` all green;
  `claude plugin validate .` clean.
- New tests pass: the index builder's ordering (first tag, newest-first within a heading),
  the `## Retired` heading before `## Unsorted`, the `(stale)` marker (with `--today` fixing
  the clock) and its removal when comparing with `check`, class normalisation (`flaky-test`,
  `flaky_test` and `Flaky Test` sharing one heading), `README.md` and `index.md` themselves
  excluded from the build, a malformed-frontmatter file listed under `## Unsorted` with no
  crash, a zero-lesson index, `check`'s exit 1 and diff on a drifted index (a CRLF copy of a
  correct index must pass); the gate's new `lesson_and_eval` check at phase (e) only, with
  one test per fail case (missing lesson, two lesson files matching the glob, missing a
  required frontmatter field, `prompt.md`
  or `checks.yaml` missing, failing `index.py check`, a dangling `supersedes`, a `supersedes`
  target whose `status` did not actually move to `retired`, an out-of-enum `status`)
  asserting the whole rendered "what I need from you" block, each problem on its own
  indented line, not just that each line is present somewhere in the text,
  plus the existing gate (f) test
  (`test_gate_f_waits_for_the_owner_s_triage_with_the_finding_and_its_route`) still passing
  unchanged; the updated instructions in `plugin/commands/sdlc-deploy.md` and
  `plugin/commands/sdlc-maintain.md` pass their existing instruction tests in
  `tests/test_commands_and_skills.py`.
- `tests/test_scaffold.py`'s manifest cross-check passes with both
  `.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json` at `0.3.6`.
- `docs/OPERATING_MODEL.md:144` carries the new sentence; `template/lessons/README.md`
  describes the frontmatter, footnote and index shape; `template/sdlc.yaml` documents
  `lessons.stale_after_months`. No lesson file exists in this repository or the sample to
  migrate, so acceptance does not include a migration step.
