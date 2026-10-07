# Plan: lessons with frontmatter and a generated index (from intent.md 2026-10-06, spec.md 2026-10-07)

## Files that change
- `plugin/lessons/index.py` (new) — the frontmatter split (the same `^---\n...\n---\n` pattern
  already used for `SKILL.md`, `tests/test_policy_skills.py:28`) plus `plugin/state/yamlish.py`
  read/write; `build --root <path>` (rewrite `lessons/index.md` from every `lessons/*.md`
  frontmatter) and `check --root <path>` (exit 1 and the diff on drift), mirroring the CLI
  shape of `plugin/evals/case.py`.
- `plugin/gate/artifacts.py` — new constants beside `SPEC_SECTIONS`/`REQUIRED_ARTIFACTS`
  (`artifacts.py:33-39,76-88`) naming the lesson's required frontmatter fields and the eval
  case's required files, for the incident-only sub-checks to read.
- `plugin/gate/checks.py` — extend `check_artifacts`'s `entry_route == "incident"` branch
  (today `checks.py:205-211`) with: lesson file exists and carries every required frontmatter
  field; `evals/cases/<id>-<slug>/` exists; `plugin/lessons/index.py check` passes; a
  `supersedes` target that does not exist fails; a `status` outside `stable | retired` fails.
  Each appends to the existing `problems` list, so each becomes its own "what I need from
  you" line through the existing `_fail(name, reason, need, **details)` path — no change to
  `CHECKS_BY_PHASE` (`checks.py:1646-1648`) or the `CheckResult` shape.
- `plugin/commands/sdlc-deploy.md` — step 0b (today `sdlc-deploy.md:66-84`): write the
  frontmatter block with the field/source mapping of spec.md Design, then run
  `plugin/lessons/index.py build` in the same commit as the lesson and the eval (today's
  commit convention at `sdlc-deploy.md:82-83` stays, with the `build` call added before it).
- `plugin/commands/sdlc-maintain.md` — step 1 (today `sdlc-maintain.md:40-50`, specifically
  the "every file under `lessons/`" line at `sdlc-maintain.md:45`): read `lessons/index.md`
  first, run `check` first, open only the lessons whose tags name the metric or the rule in
  `detection.json` plus `## Retired`; on a stale or missing index, read every file as today
  and log that fact in the intent's `## Evidence` section.
- `template/lessons/README.md` — rewritten: the frontmatter block and its fields replace the
  prose header line (today `template/lessons/README.md:21`); the four body headings
  (`:23-34`) stay with a footnote convention added; one paragraph on `## Unsorted` for a file
  without frontmatter.
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
  within a heading, `## Retired` last, `## Unsorted` for a frontmatter-less file, the
  `(stale)` marker, `check`'s exit 0/1 and diff.
- `tests/test_gate.py` — extends the existing incident/`entry_route`/`artifacts` coverage
  (today around `test_gate.py:2346-2364`) with the new sub-checks' pass and fail cases.
- `tests/test_commands_and_skills.py` — extends the instruction-shape tests to cover the
  updated `sdlc-deploy.md` step 0b and `sdlc-maintain.md` step 1 text.

No change to `plugin/evals/case.py` (its shape is only linked to, per spec.md and decision
17), to `plugin/detect/**`, `plugin/ci/run_phase.py`, the detect/runbook/fix workflow
templates, or the sample repository (frozen, `HANDOFF.md` precondition 6, choice 138); no
change to this repository's own `sdlc.yaml`, `CLAUDE.md`, `REVIEW.md` or `.claude/**` (the
root pin to 0.3.6 is the owner's guardrail-row edit after the tag, per intent Constraints).

## Order of work
1. `plugin/lessons/index.py` with its frontmatter split, `build` and `check`, and
   `tests/test_lessons.py` in the same commit (coding-standards rule 4: no behavior change
   without a test that fails without it).
2. `plugin/gate/artifacts.py` + `plugin/gate/checks.py`'s three new incident sub-checks, and
   the matching new cases in `tests/test_gate.py`, in the same commit — this is the riskiest
   step (see Risks) and should land as its own reviewable unit, not folded into step 1 or 3.
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
   `lessons/` differently), and gate (e) for any `entry_route: incident` change (three new
   ways to park). No caller is touched retroactively: a project stays on its pinned version
   until it bumps it (decision 8), and the sample repository is frozen at 0.2.30 until item
   11 of `HANDOFF.md` — not a caller of this version at all right now. No database schema or
   stored row is touched; the only data shapes are the markdown frontmatter block (new) and
   `lessons/index.md` (new, generated, never hand-edited). A project-level skill override
   under `.claude/skills/` for any of the five policy skills is unaffected, since this change
   does not touch the policy skills themselves.
2. **Riskiest step: step 2, the gate sub-checks.** A mistake here either blocks every future
   incident change at gate (e) with a wrong "what I need from you" line, or — worse — silently
   stops requiring the lesson/eval it was meant to enforce, which would not fail loudly; it
   would just quietly stop protecting the invariant the whole change exists for. Mitigation:
   `tests/test_gate.py` must cover both the all-present pass case and every new fail case
   (missing lesson, missing a required frontmatter field, missing eval case folder, a failing
   `index.py check`, a dangling `supersedes`, an out-of-enum `status`) individually, alongside
   the existing `## Evidence`-section case it already covers (`test_gate.py:2363-2364`), so a
   regression in any one sub-check fails its own assertion, not just the suite in general.
3. **The maintain-run fallback path.** Step 1's new "stale or missing index → read every
   file" branch is the safety net for a corrupted or hand-edited index; if its test coverage
   only exercises the happy (fresh index) path, a bug in the fallback would silently cause the
   diagnosis to miss lessons rather than error loudly. Mitigation: test the fallback
   explicitly (a deliberately stale index, a missing index, a lesson with malformed
   frontmatter) and assert the intent's `## Evidence` section says the fallback happened.
4. **Two-manifest version bump.** `plugin.json` and `marketplace.json` must move together;
   `tests/test_scaffold.py::test_marketplace_points_at_repo_root` already cross-checks them,
   so a partial bump fails the suite immediately rather than shipping a mismatch — this risk
   is self-mitigating given the existing test, provided step 6 changes both files in one
   commit.
5. **`yamlish` reuse for a two-marker document.** `plugin/state/yamlish.py` has only ever
   parsed a document with one leading `---` (`yamlish.py:122-123` skips exactly one); a
   lesson's frontmatter is bounded by a leading **and** a trailing `---`. The split into "the
   YAML between the two markers" vs. "the body after the second marker" must happen in
   `plugin/lessons/index.py` before the result is handed to `yamlish.loads` — exactly as the
   existing `SKILL.md` frontmatter reader already does it (`tests/test_policy_skills.py:28`)
   — `yamlish` itself needs no change. Getting this wrong would make `yamlish.loads` try to
   parse the lesson's body prose as YAML and raise `YamlishError`; `tests/test_lessons.py`
   must include a lesson with a non-trivial body (one containing a line that looks like
   `key: value`) to catch a reader that does not stop at the second `---`.
6. **No existing lesson file to migrate.** Confirmed: `lessons/` in this repository holds
   only `README.md`, and the sample is frozen, so there is no migration step and no risk of
   breaking a real lesson in this change; the `## Unsorted` handling is only proven by a
   synthetic frontmatter-less fixture in `tests/test_lessons.py`, not a real file.

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
- **A controlled vocabulary for the `class` tag (e.g. an enum in `bands.yaml`).** Considered,
  not chosen: the intent does not ask for one, and inventing a vocabulary is a separate,
  larger decision; left as the open, owner-visible concern spec.md records rather than
  decided unprompted here.
- **Migrating existing lesson files as part of this change.** Not applicable: none exist in
  this repository or the (frozen) sample to migrate.

## Proof
- `tests/test_lessons.py` (new, to be written): ordering by first tag, newest-first within a
  heading, `## Retired` last, `## Unsorted` for a frontmatter-less file, the `(stale)` marker,
  `check` exit 0 on a built index and exit 1 with a diff on a drifted one, and a lesson whose
  body contains a `key: value`-shaped line to prove the frontmatter split stops at the second
  `---`.
- `tests/test_gate.py` (existing file, new cases to be written): extends the incident-artifact
  coverage at `test_gate.py:2346-2364` with the all-present pass case and each new fail case
  (missing lesson, missing frontmatter field, missing eval case folder, failing `index.py
  check`, dangling `supersedes`, out-of-enum `status`).
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
its own test, and the field/source mapping and file:line anchors live in spec.md Design. The
one thing deliberately left for the owner rather than decided here is the `class` tag's
vocabulary (spec.md Flagged concerns) — the plan does not ask the implementer to guess it
silently.
