# Plan: lessons with frontmatter and a generated index (from intent.md 2026-10-06, spec.md 2026-10-07)

## Files that change
- `plugin/lessons/__init__.py` (new) — empty, like every other plugin subpackage's.
- `plugin/lessons/index.py` (new) — the frontmatter split (the same `^---\n...\n---\n`
  pattern already used for `SKILL.md`, `tests/test_policy_skills.py:28`, reading the file
  with `utf-8-sig`) plus `plugin/state/yamlish.py` read/write for the YAML between the
  markers; `build --root <path> [--today YYYY-MM-DD]` (rewrite `lessons/index.md` from
  every `lessons/*.md` frontmatter except `README.md` and `index.md` themselves, excluded
  by name; each line ends with a `Tags:` clause (class, metric, runbook — runbook omitted
  when absent) so the maintain run can match on tags without opening every file; a
  malformed or missing frontmatter block goes to `## Unsorted`, never raises;
  `(stale)` appended from `--today`, default the real date) and
  `check --root <path> [--today YYYY-MM-DD]` (exit 1 and the diff when the index on disk,
  with `(stale)` stripped from both sides before comparing, is not what `build` would
  write — exit 0 with `## Unsorted` entries present); the index itself is written with
  `Path.write_text(..., newline="\n")` directly
  (not through `yamlish.dump_file`, which writes YAML, not markdown), `check` reads the file
  in universal-newline text mode, and every link is rendered with the native path's
  `.as_posix()` (`Path(...).as_posix()`, as `case.py:181` does, never
  `PurePosixPath(str(p)).as_posix()`); mirrors the CLI shape of `plugin/evals/case.py`.
- `plugin/gate/artifacts.py` — new constants beside `SPEC_SECTIONS`/`REQUIRED_ARTIFACTS`
  (`artifacts.py:33-39,76-88`) naming the lesson's required frontmatter fields (every field
  of spec.md Requirements' first bullet except `runbook`, `supersedes` and `retired_by`,
  optional) and the eval case's required file names, `prompt.md` and `checks.yaml`, for the
  new gate check to read; the two names are constants here, not imported from
  `plugin/evals/case.py` (which names them as locals, `case.py:178`, not as constants) —
  with a one-line comment naming `case.py:178` as the writer that must agree.
  `plugin/evals/case.py` stays untouched.
- `plugin/gate/checks.py` — a new check function `lesson_and_eval`, guarded by
  `ctx.status.entry_route == "incident" and ctx.phase == "e"` (not inside
  `check_artifacts`'s `entry_route == "incident"` branch, `checks.py:205-211`, which every
  gate from `a` to `f` runs and would otherwise require the lesson and the eval at gate (f)
  too, before either exists): exactly one lesson file matches the glob
  `lessons/[0-9][0-9][0-9][0-9]-[0-9][0-9]-<slug>.md` (zero matches fails as "missing
  lesson", more than one match fails too) and it carries every required frontmatter
  field; `evals/cases/<id>-<slug>/prompt.md` and `checks.yaml` both exist;
  `plugin/lessons/index.py check` passes; a
  `supersedes` target that does not exist fails, and so does one whose `status` did not
  move to `retired`; a `status` outside `stable | retired` fails. Each problem is one line,
  joined with `"\n    "` (a newline and four spaces) into the single `CheckResult.need` the
  existing "what I need from you" rendering (`gate.py:76-79`, which prints
  `  - what I need: <need>` for one line) already prints per failed check, so every later
  problem lands indented under that bullet instead of at column 0. Registered in
  `CHECKS_BY_PHASE["e"]` (today `checks.py:1646-1660`) alongside the existing checks; no
  change to `CHECKS_BY_PHASE["f"]` and no change to the `CheckResult` shape.
- `plugin/commands/sdlc-deploy.md` — step 0b (today `sdlc-deploy.md:66-84`): write the
  frontmatter block with the field/source mapping of spec.md Design (block style for every
  nested field, double-quoted `title` and `description`), including the `supersedes` /
  `retired_by` edit to the earlier lesson in the same commit when this incident repeats a
  class, and the scan-shaped `detected` fields when the incident came from the weekly scan;
  then run `plugin/lessons/index.py build` in the same commit as the lesson and the eval
  (today's commit convention at `sdlc-deploy.md:82-83` stays, with the `build` call added
  before it). `allowed-tools` (today `sdlc-deploy.md:5`) gains
  `Bash(python "${CLAUDE_PLUGIN_ROOT}/plugin/lessons/index.py" *)`, quoted the same way the
  body's own call is.
- `plugin/commands/sdlc-maintain.md` — step 1 (today `sdlc-maintain.md:40-50`, specifically
  the "every file under `lessons/`" line at `sdlc-maintain.md:45`): read `lessons/index.md`
  first, run `check` first, open only the lessons whose heading or tags name the metric or
  the rule in `detection.json` (the index line now ends with a `Tags:` clause so this does
  not require opening every file) plus `## Retired`; on a stale or missing index, read every
  file as today and log that fact in the intent's `## Evidence` section. `allowed-tools` (today
  `sdlc-maintain.md:5`) gains
  `Bash(python "${CLAUDE_PLUGIN_ROOT}/plugin/lessons/index.py" *)`, quoted the same way.
- `template/lessons/README.md` — rewritten: the frontmatter block and its fields replace the
  prose header line (today `template/lessons/README.md:21`), in block style with `title`
  and `description` double-quoted in the example; the four body headings (`:23-34`) stay
  with a footnote convention added; one paragraph on `## Unsorted` for a file without
  frontmatter, or whose frontmatter does not parse.
- `template/sdlc.yaml` — one new commented row documenting `lessons.stale_after_months`
  (default twelve months, read only when set), in the style of the existing
  `automation_identity` commented rows (`template/sdlc.yaml:113-120`).
- `docs/OPERATING_MODEL.md` — one sentence added to the `lessons/` bullet
  (`docs/OPERATING_MODEL.md:144`) naming the frontmatter and the generated index.
- `.claude-plugin/plugin.json` — `version`: `0.3.5` → `0.3.6` (`plugin.json:4`).
- `.claude-plugin/marketplace.json` — the `plugins[0].version` entry: `0.3.5` → `0.3.6`
  (`marketplace.json:11`), kept equal to `plugin.json` (cross-checked by
  `tests/test_scaffold.py::test_marketplace_points_at_repo_root`, `test_scaffold.py:41-47`).
- `tests/test_lessons.py` (new) — the index builder: ordering by first tag, newest-first
  within a heading, `## Retired` before `## Unsorted`; `README.md` and `index.md` present on
  disk and excluded from the build; a lesson with malformed frontmatter listed under
  `## Unsorted` with no crash; a zero-lesson tree; the `(stale)` marker with `--today` and
  its removal before `check` compares; a drifted index's exit 1 and diff, including a
  byte-identical index written with CRLF line endings still passing `check`; class
  normalisation (`flaky-test`/`flaky_test`/`Flaky Test` sharing one heading).
- `tests/test_gate.py` — a new fixture at phase (e) with `entry_route: "incident"`
  (`_ctx(tmp_path, phase="e")`, the existing helper at `test_gate.py:364`, with the route
  set), since no (e) incident fixture exists yet (the one at `test_gate.py:2306-2338`,
  `maintain_project`, is phase (f)); the all-present pass case and one test per fail case
  (missing lesson, two lesson files matching the glob, missing a required frontmatter
  field, `prompt.md` or `checks.yaml`
  missing, a failing
  `index.py check`, a dangling `supersedes`, a `supersedes` target whose `status` did not
  move to `retired`, an out-of-enum `status`), each asserting the whole rendered "what I
  need from you" block, each problem on its own indented line; one unit test calling
  `lesson_and_eval` directly with a phase-(f) incident context and asserting it passes, so
  the guard itself is proven and not only its registration; plus a regression case
  confirming
  `test_gate_f_waits_for_the_owner_s_triage_with_the_finding_and_its_route`
  (`test_gate.py:2341-2354`) still lists the same gate (f) checks unchanged, proving the new
  check never runs there.
- `tests/test_commands_and_skills.py` — extends the instruction-shape tests to cover the
  updated `sdlc-deploy.md` step 0b and `sdlc-maintain.md` step 1 text.

## Order of work
1. `plugin/lessons/__init__.py` (empty) and `plugin/lessons/index.py` with its frontmatter
   split, `build` and `check`, and
   `tests/test_lessons.py` in the same commit (coding-standards rule 4: no behavior change
   without a test that fails without it).
2. `plugin/gate/artifacts.py` + `plugin/gate/checks.py`'s new `lesson_and_eval` check (nine
   fail cases: missing lesson, two lesson files matching the glob, missing a required
   frontmatter field, `prompt.md` or
   `checks.yaml` missing, a failing `index.py check`, a dangling `supersedes`, a `supersedes` target whose
   `status` did not move to `retired`, an out-of-enum `status`, a `supersedes` value that is
   not a bare lesson file name — outside `lessons/`, absolute, or the lesson's own name —
   fix round, PR #132), and the matching new cases
   in `tests/test_gate.py`, in the same commit — this is the riskiest step (see Risks) and
   should land as its own reviewable unit, not folded into step 1 or 3.
3. `plugin/commands/sdlc-deploy.md` step 0b and `plugin/commands/sdlc-maintain.md` step 1,
   and the matching additions to `tests/test_commands_and_skills.py`, in the same commit.
4. `template/lessons/README.md` and `template/sdlc.yaml`'s new row; confirm
   `tests/test_templates.py` still passes unchanged (it renders and parses `sdlc.yaml` but
   asserts no specific key count that a new commented row would break).
5. `docs/OPERATING_MODEL.md`'s one new sentence at line 144.
6. `.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json` to `0.3.6`, last, so
   every preceding commit's tests ran against the version the change actually ships.
7. Full verification: `python -m compileall -q plugin tests tasks.py`, `python -m pytest`,
   `python -m ruff check .`, `python -m ruff format --check .`, `claude plugin validate .`.

## Risks
1. **What this could break.** Every project pinned to this plugin version going forward:
   `/sdlc-deploy` step 0b (writes a lesson differently), `/sdlc-maintain` step 1 (reads
   `lessons/` differently), and gate (e) for any `entry_route: incident` change (one new way
   to park, with up to nine reasons). No caller is touched retroactively: a project stays
   on its pinned version until it bumps it (decision 8), and the sample repository is frozen
   at 0.2.30 until item 11 of `HANDOFF.md` — not a caller of this version at all right now.
   No database schema or stored row is touched; the only data shapes are the markdown
   frontmatter block (new) and `lessons/index.md` (new, generated, never hand-edited). A
   project-level skill override under `.claude/skills/` for any of the five policy skills is
   unaffected, since this change does not touch the policy skills themselves. No change to
   `plugin/evals/case.py` (its shape is only linked to, per spec.md and decision 17), to
   `plugin/detect/**`, `plugin/ci/run_phase.py`, the detect/runbook/fix workflow templates,
   or the sample repository (frozen, `HANDOFF.md` precondition 6, choice 138); no change to
   this repository's own `sdlc.yaml`, `CLAUDE.md`, `REVIEW.md` or `.claude/**` (the root pin
   to 0.3.6 is the owner's guardrail-row edit after the tag, per intent Constraints).
2. **Riskiest step: step 2, the gate check.** A mistake here either blocks every future
   incident change at gate (e) with a wrong "what I need from you" line, or — worse — silently
   stops requiring the lesson/eval it was meant to enforce, which would not fail loudly; it
   would just quietly stop protecting the invariant the whole change exists for. A second way
   to get it wrong: guarding on `entry_route == "incident"` alone, which would also fire at
   gate (f) before the lesson or the eval exists (the first draft of this plan made exactly
   that mistake; the guard is `entry_route == "incident" and ctx.phase == "e"`). Mitigation:
   `tests/test_gate.py` must cover both the all-present pass case and every new fail case
   (missing lesson, two lesson files matching the glob, missing a required frontmatter
   field, `prompt.md` or `checks.yaml`
   missing, a failing
   `index.py check`, a dangling `supersedes`, a `supersedes` target whose `status` did not
   move to `retired`, an out-of-enum `status`, a `supersedes` value that is not a bare
   lesson file name) individually, plus the existing gate (f) case
   (`test_gate_f_waits_for_the_owner_s_triage_with_the_finding_and_its_route`,
   `test_gate.py:2341-2354`) still passing unchanged, so a regression in the new check or its
   guard fails its own assertion, not just the suite in general.
3. **The maintain-run fallback path.** Step 1's new "stale or missing index → read every
   file" branch is the safety net for a corrupted or hand-edited index; if its test coverage
   only exercises the happy (fresh index) path, a bug in the fallback would silently cause the
   diagnosis to miss lessons rather than error loudly. Mitigation: `tests/test_commands_and_skills.py`
   must assert, as instruction text, that step 1 names the fallback (a deliberately stale
   index, a missing index) and the one-line `## Evidence` note — pytest exercises the
   instructions `/sdlc-maintain` reads, not a live model run, so it cannot assert that an
   actual diagnosis wrote that line; the mitigation is that the instruction says to, in
   terms specific enough for a reviewer to catch a vaguer rewrite.
4. **Two-manifest version bump.** `plugin.json` and `marketplace.json` must move together;
   `tests/test_scaffold.py::test_marketplace_points_at_repo_root` already cross-checks them,
   so a partial bump fails the suite immediately rather than shipping a mismatch — this risk
   is self-mitigating given the existing test, provided step 6 changes both files in one
   commit.
5. **`yamlish` reuse for a two-marker document.** `plugin/state/yamlish.py` has only ever
   parsed a document with one leading `---` (`yamlish.py:122-123` skips every `---` line
   before the first content line; a `---` encountered after content has begun raises
   `expected 'key: value'`); a
   lesson's frontmatter is bounded by a leading **and** a trailing `---`. The split into "the
   YAML between the two markers" vs. "the body after the second marker" must happen in
   `plugin/lessons/index.py` before the result is handed to `yamlish.loads` — exactly as the
   existing `SKILL.md` frontmatter reader already does it (`tests/test_policy_skills.py:28`)
   — `yamlish` itself needs no change. Getting this wrong would make `yamlish.loads` try to
   parse the lesson's body prose as YAML and raise `YamlishError`; `tests/test_lessons.py`
   must include a lesson with a non-trivial body (one containing a line that looks like
   `key: value`) to catch a reader that does not stop at the second `---`.
6. **No existing lesson file to migrate.** Confirmed: this repository has no root `lessons/`
   directory at all (only `template/lessons/README.md`, the file `/sdlc-init` copies into a
   new project), and the sample is frozen, so there is no migration step and no risk of
   breaking a real lesson in this change; the `## Unsorted` handling is only proven by a
   synthetic frontmatter-less fixture in `tests/test_lessons.py`, not a real file.
7. **The clock inside `(stale)`.** `build`'s and `check`'s notion of "past `stale_after`"
   depends on the date they run with; without the `--today` override `tests/test_lessons.py`
   would need to either mock the system clock or write `stale_after` dates relative to
   whenever the suite happens to run, both more fragile than a flag. Mitigation: `--today`
   accepts a fixed date in the tests, so the staleness tests are deterministic regardless of
   when the suite runs; `/sdlc-deploy` step 0b never passes it, so the real run always uses
   the actual date.
8. **Build order depends on the open concern.** Step 1 cannot start until spec.md's `class`
   concern is closed (it was, this round — see spec.md Flagged concerns): the class
   normalisation rule step 1 implements is part of that decision. The decision itself leaves
   the plan's file list unchanged (no vocabulary file, no new `sdlc.yaml`/`bands.yaml` key),
   so no step above needed to change once it closed.

## Options not taken
- **A third-party YAML dependency (e.g. PyYAML) for the frontmatter.** Not chosen:
  `sdlc.yaml`'s own constraint and `plugin/state/yamlish.py`'s documented reason (a missing
  import exits 1, which Claude Code treats as non-blocking, so a guardrail could switch
  itself off silently) already rule this out, and `yamlish` already supports every shape the
  fields need (nested mappings, lists of mappings, flow lists).
- **A separate `plugin/lessons/frontmatter.py` module, split from `index.py`.** Considered,
  not chosen for this change: `index.py` is the only script-level consumer today (the write
  side is the (e) run itself, writing with Write/Edit, not a script call); splitting the
  parser out is easy later if a second consumer appears, and a premature split would be an
  abstraction this change does not need.
- **A controlled vocabulary for the `class` tag (e.g. an enum in `bands.yaml`).** Not chosen,
  decided in spec.md Flagged concerns: kebab-case normalisation in `index.py build` is
  enough for now; a fixed vocabulary is a guardrail-file edit on every project and there is
  no lesson yet to design one from (decision 17). Revisit once a project has accumulated
  real lessons to design the vocabulary from.
- **Migrating existing lesson files as part of this change.** Not applicable: none exist in
  this repository or the (frozen) sample to migrate.

## Proof
- `tests/test_lessons.py` (new, to be written): ordering by first tag, newest-first within a
  heading, `## Retired` before `## Unsorted`, `README.md`/`index.md` excluded, a malformed
  frontmatter file, a non-UTF-8 lesson file and a bad-shaped `detected.at`/`stale_after`
  value each under `## Unsorted` with no crash, a zero-lesson tree, the `(stale)`
  marker with `--today` and its removal before comparing, `check` exit 0 on a built index
  (CRLF included) and exit 1 with a diff on a drifted one, class normalisation
  (`flaky-test`/`flaky_test`/`Flaky Test` sharing one heading), and a lesson
  whose body contains a `key: value`-shaped line to prove the frontmatter split stops at the
  second `---`.
- `tests/test_gate.py` (existing file, new cases to be written): a new phase-(e)-incident
  fixture (none exists today; the one at `test_gate.py:2306-2338` is phase (f)) carrying the
  all-present pass case and each new fail case (missing lesson, two lesson files matching
  the glob, missing frontmatter field,
  `prompt.md` or `checks.yaml` missing, failing `index.py check`, dangling `supersedes`, a `supersedes`
  target whose `status` did not move to `retired`, out-of-enum `status`, and a `supersedes`
  value that is not a bare lesson file name — outside `lessons/`, absolute, or the lesson's
  own name), each asserting the
  whole rendered "what I need from you" block with one problem per indented line; one unit
  test calling `lesson_and_eval` directly with a phase-(f) incident context asserting it
  passes, proving the guard itself and not only its registration; plus confirming
  `test_gate_f_waits_for_the_owner_s_triage_with_the_finding_and_its_route`
  (`test_gate.py:2341-2354`, gate (f), not (e)) still passes unchanged.
- `tests/test_commands_and_skills.py` (existing file, new cases to be written): the updated
  `sdlc-deploy.md` step 0b and `sdlc-maintain.md` step 1 instructions pass their existing
  instruction-shape assertions.
- `tests/test_scaffold.py::test_marketplace_points_at_repo_root` (existing, already runnable
  today at 0.3.5): must keep passing with both manifests at `0.3.6`.
- Full suite, literal output pasted into evidence per spec.md Acceptance:
  `python -m compileall -q plugin tests tasks.py` (exit 0, no output), `python -m pytest`
  (all green), `python -m ruff check .` (zero warnings), `python -m ruff format --check .`
  (clean), `claude plugin validate .` (clean).

An engineer who has not seen this conversation can implement from this plan and spec.md
alone: every file is named with what changes in it, the order is small commits each with
its own test, and the field/source mapping and file:line anchors live in spec.md Design.
Every flagged concern spec.md raised is decided (Flagged concerns, this round); none is
left for the implementer to guess.
