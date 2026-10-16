# Plan: Dropped tests and eval cases are gate findings (from intent.md 2026-10-13, spec.md 2026-10-13)

## Files that change

- `plugin/gate/diff.py` — a parser for `git diff --name-status -M -z <merge base>...HEAD`
  into typed records (status letter, source path, and destination path for a rename), beside
  the existing `_z`/`committed_files`; invoked through the module's own `_git` argument-list
  helper, no shell string. A second new helper, `tree_files(root, ref, prefix)`, lists every
  path HEAD's committed tree holds under a prefix (`git ls-tree -r --name-only <ref> --
  <prefix>`, same argument-list convention), so the eval-case drop rule can tell a survivor
  from a drop (panel decision #2, phase b).
- `plugin/gate/checks.py` — a new `check_ratchets(ctx) -> CheckResult` beside
  `check_test_lock`; a small pure drop-rule function for test files (D/R over the parsed
  `--name-status` records alone) and a second pure drop-rule function for eval cases (the
  same records plus the `tree_files` survivor list at `ctx.diff.head`, with the dot-prefix
  addition for a renamed-to-hidden case); a pure skip-marker scan function over added lines;
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
- `.claude-plugin/plugin.json` — the `version` field, bumped to the next free patch number
  when this change merges (decision 8).
- `.claude-plugin/marketplace.json` — its `version` field, bumped to the same value in the
  same commit. `tests/test_scaffold.py:47` asserts the two stay equal; bumping only
  `plugin.json` fails that test. (Split into its own bullet from the combined one two fix
  rounds wrote: `art.planned_files` takes only the first backtick span of a list item, so
  the combined bullet declared `plugin.json` alone to `plan_sync` and parked this commit on
  `marketplace.json` as undeclared.)
- `tests/test_gate.py` — `check_ratchets`: the test-file drop rule (D, R-not-a-rename,
  R-is-a-rename), the eval-case drop rule (dot-prefixed rename, folder emptied of survivors
  at HEAD, a partial multi-file deletion that leaves a survivor), declaration via "## Files
  that change", declaration via the `- ratchet:` Proof item, an accepted hit passing on a
  later run, the skip-marker scan never affecting `ok`, and `CHECKS_BY_PHASE` membership at
  (a)/(b)/(c)/(d)/(e)/(f). Also the new `diff.py` `--name-status -M` parser and `tree_files`
  helper, directly.
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

1. `plugin/gate/diff.py`: add the `--name-status -M` record parser and the `tree_files`
   helper, with their direct unit tests in `tests/test_gate.py` (no behavior elsewhere
   depends on either yet, so both land and are provably correct on their own).
2. `plugin/gate/checks.py`: add the pure test-file drop-rule function (D/R over the parsed
   records alone) and the pure eval-case drop-rule function (the same records plus a
   survivor-path argument), with unit tests using step 1's parser and a plain survivor-list
   argument as fixtures, not live git — proving both rules in isolation from the check and
   the gate, including the partial-multi-file-deletion case (panel decision #2, phase b).
3. `plugin/gate/checks.py`: add `check_ratchets` wiring the two drop rules — the eval-case
   one supplied with `tree_files(ctx.root, ctx.diff.head, "evals/cases")` — to
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
9. `.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json`: bump the version in
   both, to the same next-free-patch value, last, once every other file in the diff is
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
- **A `--name-status -M` diff cannot tell an eval case's survivor from its drop on its own**
  (found by the adversarial reviewer and the panel at phase (b), decision #2): a file under
  a case folder that the diff never touches carries no record, so a diff-records-only rule
  cannot distinguish a partial, multi-file deletion (a sibling survives) from the whole
  case's drop. Mitigation: the eval-case drop rule additionally takes the survivor-path list
  `tree_files` reads at `ctx.diff.head`, and step 2's test suite includes the
  partial-deletion case directly (`test_ratchets_eval_case_partial_delete_is_not_a_drop`).
  The test-file drop rule has no such gap: a test file is either present at HEAD or it is
  not, with no "folder" grouping to lose a sibling under. A narrower sub-case — a sibling
  surviving a *dot-prefixed rename* of another file in the same case, rather than a plain
  deletion — surfaced in the phase c fix round and was settled separately (panel decision
  #1, phase c fix round): the dot-prefixed-rename rule stays independent of this survivor
  check by design, pinned by `test_ratchets_eval_case_dot_rename_wins_over_a_surviving_sibling`.
- **A `--name-status -M` parser is new to this codebase**: every existing diff-reading check
  uses `--name-only`, which cannot carry a rename's source and destination. A rename record's
  two paths must not be mistaken for two separate files (a false double-count or a false
  "both dropped"). Mitigation: the parser's own direct unit tests in step 1, including a
  rename whose destination also matches a `test_paths` glob (not a drop) and one whose
  destination does not (a drop).
- **The `ratchet: <name>` hit key could be confused with a configured `risk_list` item of
  the bare name** (for example a project that lists `tests` on its own risk list). Mitigation:
  the detail text uses the literal key `"ratchet: tests"` / `"ratchet: evals"`
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
  2. The riskiest step is 3, as above; the survivor-vs-drop gap in the eval-case rule
     (second risk bullet) is the second riskiest, and is now closed by the design, not left
     open.
  3. See "Options not taken" below.
  4. Yes: steps 1-10 name every file and every test by path, the exact detail-dict shape and
     the two-drop-rule split are in spec.md's Design section, and the token list and
     glob-matching helpers to reuse (`test_path_patterns`, `art.planned_files`,
     `plan_sync.is_planned`) are named by file:line in spec.md.
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
- **Keeping the eval-case drop rule as a records-only pure function** (the original draft
  of this plan). Not chosen: the adversarial reviewer and the phase-(b) panel (decision #2)
  showed a records-only rule cannot distinguish a case's partial deletion from its full drop,
  since an untouched sibling file leaves no diff record at all; the fix (a `tree_files`
  survivor-path argument read at `ctx.diff.head`) stays inside the files this plan already
  lists and adds exactly one test.

## Proof

- `tests/test_gate.py::test_ratchets_drop_test_file_undeclared_fails` — a `D` under a
  `test_paths` glob with no plan declaration fails `check_ratchets`, `details.hits["ratchet:
  tests"]` names the file.
- `tests/test_gate.py::test_ratchets_drop_test_file_declared_in_files_that_change_ok` — the
  same `D`, with its path listed in the approved plan's "## Files that change", is `ok`.
- `tests/test_gate.py::test_ratchets_drop_test_file_declared_in_proof_ok` — the same `D`,
  with `- ratchet: tests may fall, because <why>` in the approved plan's "## Proof", is `ok`.
- `tests/test_gate.py::test_ratchets_plan_edited_after_merge_base_does_not_excuse_drop` — the
  same `D`, with the declaration committed only after the merge base (absent from the
  approved, merge-base copy of `plan.md`), still fails: proves `check_ratchets` reads
  `ctx.approved_artifact("plan.md")`, not `ctx.artifact("plan.md")` (riskiest step, step 3).
- `tests/test_gate.py::test_ratchets_rename_within_test_paths_is_not_a_drop` — an `R` whose
  source and destination both match a `test_paths` glob is `ok`.
- `tests/test_gate.py::test_ratchets_rename_out_of_test_paths_is_a_drop` — an `R` whose
  source matches a `test_paths` glob and whose destination matches none fails with
  `details.hits["ratchet: tests"]` naming the file (panel decision #3, phase b).
- `tests/test_gate.py::test_ratchets_drop_eval_case_folder_emptied_fails` — an eval case
  folder with no survivor in `tree_files`'s list at HEAD fails with `"ratchet: evals"`.
- `tests/test_gate.py::test_ratchets_drop_eval_case_dot_rename_fails` — an `R` whose
  destination folder name starts with `.` fails the same way.
- `tests/test_gate.py::test_ratchets_drop_eval_case_declared_in_files_that_change_ok` — the
  same emptied-case drop, with the case folder's path listed (trailing `/`) in the approved
  plan's "## Files that change", is `ok` (panel decision #3, phase b).
- `tests/test_gate.py::test_ratchets_drop_eval_case_declared_in_proof_ok` — the same
  emptied-case drop, with `- ratchet: evals may fall, because <why>` in the approved plan's
  "## Proof", is `ok` (panel decision #3, phase b).
- `tests/test_gate.py::test_ratchets_eval_case_partial_delete_is_not_a_drop` — one file
  under a multi-file eval case is dropped while `tree_files` still lists a sibling file
  under the same case folder at HEAD; `ok` (panel decision #2, phase b).
- `tests/test_gate.py::test_ratchets_eval_case_internal_move_is_not_a_drop` — files moving
  within one case folder is `ok`.
- `tests/test_gate.py::test_ratchets_accepted_hit_passes_on_later_run` — `status.yaml:
  risk_accepted` containing `"ratchet: tests"` makes the same undeclared drop `ok`.
- `tests/test_gate.py::test_ratchets_risk_list_tests_configured_does_not_satisfy_ratchet_hit`
  — `sdlc.yaml: risk_list` configured with `["tests"]` alongside the same undeclared
  test-file drop: `check_ratchets` still fails with `details.hits["ratchet: tests"]`, and
  `check_risk_list`'s own bare-`"tests"` hit stays in its own check's `details`; neither
  check's acceptance satisfies the other's hit key.
- `tests/test_gate.py::test_ratchets_skip_markers_listed_never_fail` — run over this
  repository's own runbook test files as the fixture (the `--deselect` lines the Risks
  section counts, nine of them), not a synthetic one: at least one hit per listed token
  appears in `details.skip_markers` with file and line; `ok` is unaffected when only skip
  markers, no drop, are present.
- `tests/test_gate.py::test_ratchets_declaring_unknown_ratchet_name_is_inert` — a Proof line
  `- ratchet: docs may fall, because ...` declares nothing and does not change the verdict of
  an unrelated undeclared drop.
- `tests/test_gate.py::test_checks_by_phase_ratchets_membership` — `check_ratchets` is in the
  (c), (d), (e) tuples and absent from (a), (b), (f).
- `tests/test_gate.py::test_diff_name_status_rename_detection_parses_rename` (and a sibling
  for a plain delete) — the new `diff.py` `--name-status -M` parser's own unit tests.
- `tests/test_gate.py::test_diff_tree_files_lists_committed_paths_under_prefix` — the new
  `diff.py: tree_files` helper's own unit test.
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
