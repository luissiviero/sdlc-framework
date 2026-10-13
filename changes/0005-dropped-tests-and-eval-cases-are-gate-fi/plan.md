# Plan: Dropped tests and eval cases are gate findings (from intent.md 2026-10-13, spec.md 2026-10-13)

## Files that change

- `plugin/gate/diff.py` — a parser for `git diff --name-status -M -z <merge base>...HEAD`
  into typed records (status letter, source path, and destination path for a rename), beside
  the existing `_z`/`committed_files`; invoked through the module's own `_git` argument-list
  helper, no shell string.
- `plugin/gate/checks.py` — a new `check_ratchets(ctx) -> CheckResult` beside
  `check_test_lock`; a small pure drop-rule function (test-path and eval-case D/R rule, the
  dot-prefix addition for eval renames); a pure skip-marker scan function over added lines;
  `CHECKS_BY_PHASE["c"]`, `["d"]`, `["e"]` gain `check_ratchets`. `check_risk_list`,
  `check_plan_sync`, `check_test_lock` and every other check are unchanged.
- `plugin/state/unpark.py` — `risk_hits` reads a check named `ratchets` beside `risk_list`
  and unions their `details.hits` keys. `perform` is unchanged (it already treats any
  returned hit uniformly).
- `plugin/pr/description.py` — `_conformance_line` appends a `"declared drops: ... (plan)"`
  clause at phases (c)/(d)/(e), built from the `ratchets` check's `details.declared`, when
  non-empty.
- `plugin/skills/plan-template/SKILL.md` — the "## Proof" section gains the fixed item form
  `- ratchet: <name> may fall, because <why>`.
- `plugin/agents/adversarial-reviewer.md` — a new numbered attack angle after the existing
  angle 6 ("The tests"), read at phases (c) and (d): each added skip marker the gate listed,
  and the plan line that declares it or "none".
- `template/REVIEW.md` — one new bullet under "## Framework rules", for every change type,
  reading the same skip-marker list at phase (e).
- `docs/OPERATING_MODEL.md` — §3's list of diff-reading checks gains `ratchets`; §6's
  description of what `sdlc:accept-risk` accepts gains a clause that a ratchet hit is
  included. Edited sentence by sentence (CLAUDE.md: no scripted rewrite of documentation).
- `.claude-plugin/plugin.json` — the `version` field, bumped (decision 8).
- `tests/test_gate.py` — `check_ratchets`: the drop rule (D, R-not-a-rename, R-is-a-rename),
  the eval-case addition (dot-prefixed rename, emptied folder), declaration via "## Files
  that change", declaration via the `- ratchet:` Proof item, an accepted hit passing on a
  later run, the skip-marker scan never affecting `ok`, and `CHECKS_BY_PHASE` membership at
  (a)/(b)/(c)/(d)/(e)/(f). Also the new `diff.py` `--name-status -M` parser, directly.
- `tests/test_state.py` — `unpark.risk_hits` reading a `ratchets`-only gate record (no
  `risk_list` check present or failing) and returning its hit keys.
- `tests/test_pr.py` — `_conformance_line`'s declared-drops clause, present when
  `details.declared` is non-empty, absent otherwise, at phases (c)/(d)/(e); unchanged at
  (a)/(b).
- `tests/test_agents.py` — the new attack angle's presence and wording in
  `adversarial-reviewer.md`.
- `tests/test_commands_and_skills.py` — the new Proof item form's presence in
  `plan-template/SKILL.md`.
- `tests/test_templates.py` — the new bullet's presence in `template/REVIEW.md`.
- `docs/PROGRESS.md` — one appended table row (link, row, what is there now, what it must
  become) proposing the matching bullet for this repository's own root `REVIEW.md`, which
  the build run does not edit.

Not touched: `framework/` (the separately pinned plugin checkout `docs/OPERATING_MODEL.md`
§6 names; spec.md's flagged concern), `check_risk_list`, `check_plan_sync`, `check_test_lock`,
the hooks, the panel, `sdlc.yaml` and this repository's own root `REVIEW.md`.

## Order of work

1. `plugin/gate/diff.py`: add the `--name-status -M` record parser and its direct unit
   tests in `tests/test_gate.py` (no behavior elsewhere depends on it yet, so it lands and is
   provably correct on its own).
2. `plugin/gate/checks.py`: add the pure drop-rule function (test-path and eval-case D/R
   rule) and its unit tests, using the parser from step 1 as a fixture input, not live git —
   proves the rule in isolation from the check and the gate.
3. `plugin/gate/checks.py`: add `check_ratchets` wiring the drop rule to
   `ctx.approved_artifact("plan.md")` for declaration (reusing `art.planned_files` /
   `plan_sync.is_planned`, and a plain search for the `- ratchet:` Proof line) and to
   `ctx.status.risk_accepted` for acceptance; add it to `CHECKS_BY_PHASE["c"/"d"/"e"]`; tests
   for the undeclared-drop fail, the two declaration paths, the accepted-hit pass, and the
   phase membership.
4. `plugin/gate/checks.py`: add the pure skip-marker scan function and wire it into
   `check_ratchets`'s `details.skip_markers`, with its own tests proving it never changes
   `ok`.
5. `plugin/state/unpark.py`: extend `risk_hits` to also read a `ratchets` check; test with a
   gate record carrying only a failing `ratchets` check.
6. `plugin/pr/description.py`: extend `_conformance_line`; test the clause present/absent.
7. `plugin/skills/plan-template/SKILL.md`, `plugin/agents/adversarial-reviewer.md`,
   `template/REVIEW.md`, `docs/OPERATING_MODEL.md`: the prose edits, each with the matching
   content-assertion test from "Files that change" updated in the same commit.
8. `docs/PROGRESS.md`: append the proposed root-`REVIEW.md` row.
9. `.claude-plugin/plugin.json`: bump the version, last, once every other file in the diff is
   settled.
10. Full `python -m compileall -q plugin tests tasks.py`, `python -m pytest`,
    `python -m ruff check .`; paste the output.

## Risks

- **The riskiest step is 3**: `check_ratchets` is the first check to read `plan.md` at the
  merge base rather than the working tree or HEAD for a purpose other than `plan_sync`'s own
  (which reads the working tree on purpose, by design, since the build session edits
  `plan.md` in (c)). Getting the two reads confused — using `ctx.artifact("plan.md")`
  (working tree) instead of `ctx.approved_artifact("plan.md")` (merge base) — would let a
  session that drops a test and edits `plan.md` in the same commit excuse its own drop,
  defeating the point of the check. Mitigation: a test that commits a `plan.md` edit
  declaring a drop *after* the merge base, with no such declaration at the merge base, and
  asserts `check_ratchets` still fails.
- **A `--name-status -M` parser is new to this codebase**: every existing diff-reading check
  uses `--name-only`, which cannot carry a rename's source and destination. A rename record's
  two paths must not be mistaken for two separate files (a false double-count or a false
  "both dropped"). Mitigation: the parser's own direct unit tests in step 1, including a
  rename whose destination also matches a `test_paths` glob (not a drop) and one whose
  destination does not (a drop).
  Mitigation: the detail text uses the literal key `"ratchet: tests"` / `"ratchet: evals"`
  (never the bare word), and a test with `risk_list: ["tests"]` configured alongside an
  undeclared test-file drop proves the two hits stay in separate `details` and neither
  satisfies the other's acceptance.
- **`unpark.risk_hits`'s caller, `perform`, is shared with `risk_list`'s own acceptance
  path**: a change that breaks the union (for example, returning only one check's hits when
  both are present) would silently narrow what `sdlc:accept-risk` accepts. Mitigation: a test
  with both a failing `risk_list` check and a failing `ratchets` check in the same gate
  record, asserting `risk_hits` returns the union of both.
- **The skip-marker scan is a list, not a gate**: a bug that makes it fail the check instead
  of only annotating it would park changes that use `pytest.skip(` or `--deselect`
  legitimately (this repository's own runbook tests do, nine times). Mitigation: step 4's
  test asserts `ok` is unaffected whenever only skip markers, no drop, are present; the
  existing runbook test files are used as a fixture so the regression would be caught by this
  repository's own suite, not only a synthetic one.
- Blast radius: `check_ratchets` is additive to `CHECKS_BY_PHASE` — no existing check's
  signature, return shape, or call site changes, so no caller of `CHECKS_BY_PHASE` elsewhere
  (the gate CLI, `run_phase.py`'s guard, the panel's `items` fixed list) needs a change; none
  of them special-case a check by name except `unpark.py` and `description.py`, both in
  "Files that change". `unpark.risk_hits`'s one other caller (`plugin/state/cli.py
  accept-risk`, the by-hand command) is unaffected: it calls the same function and gets the
  wider union for free.
- Options not taken, folded in from the interrogation:
  1. What could this change break? The accept-risk label path (if the union is wrong, see
     above), the PR's plan-conformance bullet (if the new clause is malformed, it would
     garble an otherwise-working sentence at every (c)/(d)/(e) gate) and the adversarial
     reviewer's new angle (if it reads a file the gate's delegation prompt does not actually
     supply, it would always report "none" — not a false park, but a dead angle; this plan's
     step 7 test only proves the prose is present, not that the live delegation wires the
     skip-marker list to the reviewer's prompt, which is a gap this plan accepts because
     spec.md's Design says the delegation prompt, already built, is what carries findings to
     every existing angle the same way).
  2. The riskiest step is 3, as above.
  3. See "Options not taken" below.
  4. Yes: steps 1-10 name every file and every test by path, the exact detail-dict shape is
     in spec.md's Design section, and the token list and glob-matching helpers to reuse
     (`test_path_patterns`, `art.planned_files`, `plan_sync.is_planned`) are named by
     file:line in spec.md.
  5. Every Proof item below names a test to be written in this plan's own order of work (none
     exists yet); none claims an existing test already covers this behavior.

## Options not taken

- **Writing the ratchet hit into `check_risk_list`'s own `details.hits`** (reading
  `sdlc.yaml: risk_list` plus a fixed `["tests", "evals"]` list) instead of a separate
  `check_ratchets`. Not chosen: it would conflate a project-configured risk category with a
  framework-fixed one, and intent.md's own Proposed outcome (its lines 49-51) already names
  the separate-check-plus-`unpark.py`-extension shape as the answer; spec.md's open question
  1 closes on that reading.
  Skipping drop logic until the "measured ratchets" is not chosen
  either: this is the change with no runner-code constraint that intent.md states explicitly
  (its Constraints section), and the diff form is the full requirement for this change, not
  a placeholder for it.
- **Giving the skip-marker scan its own `check_skip_markers`**, separate from
  `check_ratchets`. Not chosen: spec.md's Requirements keep it inside the one `ratchets`
  check's `details` (matching intent.md's own Proposed outcome, which lists it as part of
  the same gate check, not a new one), and a second check would need its own
  `CHECKS_BY_PHASE` wiring and its own always-`ok` convention for no added benefit.
- **A new `sdlc.yaml` key for the eval-cases path or the skip-marker token list.** Not
  chosen: spec.md's open questions 2 and 3 close on the fixed, code-level answer already in
  place (`plugin/evals/run.py`'s own default; intent.md's own fixed token list), and
  intent.md's Constraints say "No new key in `sdlc.yaml`".
- **Editing `framework/`'s copy of the same files**, so the CI runner's pinned checkout
  picks up the new check immediately. Not chosen: spec.md's flagged concern treats
  `framework/` as a separate, independently-pinned checkout outside this change's named
  scope (intent.md's own file list is root-only); re-pinning it is the project's existing
  release process, not a step this plan performs.

## Proof

- `tests/test_gate.py::test_ratchets_drop_test_file_undeclared_fails` — a `D` under a
  `test_paths` glob with no plan declaration fails `check_ratchets`, `details.hits["ratchet:
  tests"]` names the file.
- `tests/test_gate.py::test_ratchets_drop_test_file_declared_in_files_that_change_ok` — the
  same `D`, with its path listed in the approved plan's "## Files that change", is `ok`.
- `tests/test_gate.py::test_ratchets_drop_test_file_declared_in_proof_ok` — the same `D`,
  with `- ratchet: tests may fall, because <why>` in the approved plan's "## Proof", is `ok`.
- `tests/test_gate.py::test_ratchets_rename_within_test_paths_is_not_a_drop` — an `R` whose
  source and destination both match a `test_paths` glob is `ok`.
- `tests/test_gate.py::test_ratchets_drop_eval_case_folder_emptied_fails` — an eval case
  folder with nothing left under it at HEAD fails with `"ratchet: evals"`.
- `tests/test_gate.py::test_ratchets_drop_eval_case_dot_rename_fails` — an `R` whose
  destination folder name starts with `.` fails the same way.
- `tests/test_gate.py::test_ratchets_eval_case_internal_move_is_not_a_drop` — files moving
  within one case folder is `ok`.
- `tests/test_gate.py::test_ratchets_accepted_hit_passes_on_later_run` — `status.yaml:
  risk_accepted` containing `"ratchet: tests"` makes the same undeclared drop `ok`.
- `tests/test_gate.py::test_ratchets_skip_markers_listed_never_fail` — at least one hit per
  listed token appears in `details.skip_markers` with file and line; `ok` is unaffected when
  only skip markers, no drop, are present.
- `tests/test_gate.py::test_ratchets_declaring_unknown_ratchet_name_is_inert` — a Proof line
  `- ratchet: docs may fall, because ...` declares nothing and does not change the verdict of
  an unrelated undeclared drop.
- `tests/test_gate.py::test_checks_by_phase_ratchets_membership` — `check_ratchets` is in the
  (c), (d), (e) tuples and absent from (a), (b), (f).
- `tests/test_gate.py::test_diff_name_status_rename_detection_parses_rename` (and a sibling
  for a plain delete) — the new `diff.py` parser's own unit tests.
- `tests/test_state.py::test_risk_hits_reads_ratchets_check_when_risk_list_absent` —
  `unpark.risk_hits` returns the `ratchets` check's hit keys from a gate record with no
  `risk_list` check present.
- `tests/test_state.py::test_risk_hits_unions_risk_list_and_ratchets` — both checks failing
  in the same record returns the union.
- `tests/test_pr.py::test_conformance_line_declared_drops_clause_present` and
  `test_conformance_line_declared_drops_clause_absent` — the PR clause.
- `tests/test_agents.py::test_adversarial_reviewer_skip_marker_angle_present` — the new
  attack angle's text.
- `tests/test_commands_and_skills.py::test_plan_template_ratchet_proof_item_present` — the
  new Proof item form's text.
- `tests/test_templates.py::test_review_md_skip_marker_rule_present` — the new
  `template/REVIEW.md` bullet's text.
- Quantifiable target (spec.md Acceptance): `python -m compileall -q plugin tests tasks.py`
  exits 0 with no output; `python -m pytest` all green, none skipped or deleted;
  `python -m ruff check .` zero warnings.
- No screenshot or mock: no UI changed.
