# Fix response — change 0003, phase (b)

Source: `evidence/fix-requests.json`, PR #124 review #5444369078 (OWNER, `CHANGES_REQUESTED`,
2026-10-07). All requests were from a repository member; `not_applied` in the source file
was empty, so every line below is applied.

1. Concern 1 (the `class` tag's vocabulary) closed as `decided` in spec.md Flagged concerns:
   kebab-case normalisation in `index.py build`, no controlled vocabulary now, revisit once
   lessons accumulate. Commit `065c4cf`.
2. Gate scope guard stated explicitly (`entry_route == "incident" and ctx.phase == "e"`),
   with the gate (f) regression test named. Commit `065c4cf`.
3. Separate `lesson_and_eval` check registered in `CHECKS_BY_PHASE["e"]`, one `need` line
   per problem; "no new `CHECKS_BY_PHASE` entry" constraint dropped. Commit `065c4cf`.
4. `(stale)`-suffix-stripped comparison and `--today YYYY-MM-DD` on `build`/`check`, stated
   under Requirements and Acceptance. Commit `065c4cf`.
5. `README.md`/`index.md` excluded by name; `## Unsorted` never fails `check`; one-line note
   per `## Unsorted` file; a parse error never crashes. Commit `065c4cf`.
6. Block style required for every nested frontmatter field, double-quoted `title`/
   `description`, `utf-8-sig` read before the frontmatter split. Commit `065c4cf`.
7. Concern 3 (Windows newline stability) reopened (the first close named the wrong
   mechanism) and reclosed with `Path.write_text(..., newline="\n")`, a universal-newline
   read in `check`, and `as_posix()` links. Commit `065c4cf`.
8. `runbook` source corrected to `evidence/proposal.json: route` gated on
   `evidence/runbook-<name>.json: status == "ran"`, not `Resolved`; Requirements and Design
   now agree. Commit `065c4cf`.
9. Scan-filed incidents: `detected` read through `finding.read_any`; the scan shape, its
   tier/rule/metric mapping, and the absence of `run-<n>` sources stated. Commit `065c4cf`.
10. Determinism (index line shape, sort tie-break, `## Unsorted` after `## Retired`, the
    zero-lesson text, the gate's lesson glob, the optional `runbook`/`supersedes` fields,
    "the eval case exists") written down; the Acceptance sub-check count now matches the
    cases listed (fixed twice: commit `065c4cf`, then `22ef512` after the reviewer caught a
    6-vs-7 mismatch between spec.md and plan.md).
11. Restored from intent: a stale lesson is still read and logged when relied on; the
    description is one sentence in the metric's terms; a hand edit of the index is undone by
    the next `build`; `/sdlc-init` copies the README unchanged; no workflow template
    changes; the sample stays frozen; decisions 8, 9, 17 unchanged. Commit `065c4cf`.
12. `supersedes` tied to the deploy requirement (step 0b retires the earlier lesson in the
    same commit) and to the gate check (a `supersedes` target whose `status` did not move to
    `retired` fails). Commit `065c4cf`.
13. `allowed-tools` additions for `plugin/lessons/index.py` on both command files, reflected
    in plan.md's file items for `sdlc-deploy.md` and `sdlc-maintain.md`. Commit `065c4cf`.
14. Citations corrected: `HANDOFF.md:42` (item 4, not `:60-61`, which is item 11);
    `tests/test_evals.py:701-767` dropped as the instruction-test precedent (it is the
    `case.py new` CLI tests); `tests/test_gate.py:2341-2354` identified as gate (f)
    coverage, with the (e) fixture named as new (`_ctx(tmp_path, phase="e")`); `docs/notes/
    1.md`'s frontmatter described as flat, not a nested precedent. Commit `065c4cf`.
15. `plugin/lessons/__init__.py` added to plan.md's "## Files that change". Commit `065c4cf`.
16. The "No change to …" paragraph moved out of "## Files that change" (where a wrapped
    line starting with "17)," was being mis-parsed as a numbered file item) into Risk 1.
    Commit `065c4cf`.
17. Items 2–13 reflected in plan.md's file items (the `checks.py`/`artifacts.py`/`index.py`/
    `sdlc-deploy.md`/`sdlc-maintain.md` entries, the test-file entries, and Risk 2).
    Commit `065c4cf`.
18. `tests/test_lessons.py` and `tests/test_gate.py` plan items expanded with the README/
    index exclusion, malformed frontmatter, CRLF index, zero lessons, `--today`, class
    normalisation, the new (e) fixture, one test per fail case, the rendered need text, and
    the gate (f) regression; noted importing eval-case names from `plugin/evals/case.py`
    rather than duplicating them. Commit `065c4cf`.
19. Risks updated: the clock dependence of `(stale)` added (Risk 7); Risk 6's fact corrected
    (no root `lessons/` in this repository, only `template/lessons/README.md`); Risk 3's
    mitigation reworded as an instruction-text assertion (pytest cannot assert a model's
    Evidence-section line); Risk 8 added (build starts only after the concern closed; the
    free-text answer leaves the file list unchanged). Commit `065c4cf`.
20. Order of work step 2's count aligned with the file item (seven fail cases, named).
    Commit `065c4cf`.

## Not applied
(none — `fix-requests.json: not_applied` was empty)

## Verdict and gate
Adversarial review (phase b): continue, non-routine, at HEAD `22ef512` (after the one
reviewer-noted 6-vs-7 count fix, re-reviewed). Panel: mode `parked`, no pending items.
Gate (b): `wait`, label `sdlc:b-ready`, no park.

---

# Fix response — change 0003, phase (b), round 2

Source: `evidence/fix-requests.json`, PR #124 review #5449795190 (OWNER,
`CHANGES_REQUESTED`, "iteration 2 of 2", 2026-10-07). All 17 items were from a repository
member and are applied below. One item in the source file's `not_applied` was left out:
review #5444556016 (OWNER) — not applied: the review was dismissed.

**What changes the build**
1. `flakytest` replaced with `Flaky Test` (the decided normalisation rule maps `flakytest`
   to itself, not to `flaky-test`, so it did not demonstrate the rule) in spec.md Flagged
   concerns and plan.md's `test_lessons.py` item; also added to plan.md/spec.md's Proof and
   Acceptance mentions of the class-normalisation test for consistency. Commit `ac1ce30`.
2. Index line now ends with a `Tags:` clause (class, metric, runbook; runbook omitted when
   absent); `/sdlc-maintain` step 1 opens the lessons whose heading **or** tags name the
   metric or rule. spec.md's determinism bullet and `/sdlc-maintain` bullet; plan.md's
   `index.py` and `sdlc-maintain.md` items. Commit `ac1ce30`.
3. `CheckResult.need` now joins problems with `"\n    "` (newline + four spaces), not `"\n"`,
   so later problems render indented under the gate's one `  - what I need: <need>` bullet
   instead of at column 0; tests assert the whole rendered block. spec.md Requirements,
   Design and Acceptance; plan.md's `checks.py` item, `test_gate.py` item and Proof. Commit
   `ac1ce30`.
4. `prompt.md`/`checks.yaml` are now constants in `plugin/gate/artifacts.py` itself (with a
   comment naming `case.py:178` as the writer that must agree), not imported from
   `plugin/evals/case.py`; the conditional dropped, `case.py` stays untouched. plan.md's
   `artifacts.py` item. Commit `ac1ce30`.
5. "Prompt.md and checks.yaml both exist" used everywhere instead of "the eval case folder
   exists"; the fail case renamed "`prompt.md` or `checks.yaml` missing" throughout spec.md
   and plan.md. Commit `ac1ce30`.

**spec.md: sentences the first review asked for, restored as their own bullets**
6. New Requirements bullet: the index is written with `Path.write_text(...,
   newline="\n")`, `check` compares in universal-newline mode, every link uses the native
   path's `.as_posix()` (`Path(...).as_posix()`, as `case.py:181` does — not
   `PurePosixPath(str(p)).as_posix()`, which keeps a Windows path's backslashes
   unconverted). Also corrected in Design and in Flagged concern 3, which had the wrong
   call. Commit `ac1ce30`.
7. Added the sentence: `check` exits 0 with `## Unsorted` entries present and prints one
   note line per `## Unsorted` file; only a drift of the generated text is exit 1. Reworded
   the README bullet to say the same. Commit `ac1ce30`.
8. Acceptance now names `--today` fixing the clock alongside the class-normalisation test.
   Commit `ac1ce30`.
9. The `sources` sentence now states the `detection` resource is `evidence/detection.json`
   or `evidence/scan-finding.json`; "read through `plugin/detect/finding.read_any`" replaced
   with "with the mapping `finding.read_any` implements (`finding.py:150-160`)" in
   Requirements and in Design's Field sources bullet (step 0b is instruction text; nothing
   in the plan calls that function). Commit `ac1ce30`.
10. New Requirements bullet naming the `allowed-tools` addition
    (`Bash(python "${CLAUDE_PLUGIN_ROOT}/plugin/lessons/index.py" *)`) on both command
    files. Commit `ac1ce30`.
11. Seven restored intent sentences split into their own Requirements bullets: `description`
    is one sentence in the metric's terms; a stale lesson is still read and logged when
    relied on; a hand edit of the index is undone by the next `build`; `/sdlc-init` copies
    the README unchanged; no workflow template changes; the sample stays frozen; decisions
    8, 9, 17 unchanged (previously folded into other bullets). Commit `ac1ce30`.

**spec.md: determinism the build would otherwise guess**
12. Determinism bullet rewritten: index opens with `# Lessons`, no frontmatter; tag
    headings ordered alphabetically by normalised class; `file` is the name relative to
    `lessons/`; "Mon yyyy" is `detected.at`'s month; `description` carries no trailing
    period; `## Unsorted` line is `* [first heading](file)` only; `## Retired` line has the
    same shape as a normal line; `(stale)` appended at the end of the line, on `## Retired`
    lines too. Commit `ac1ce30`.
13. Required-field exception list corrected to `runbook`, `supersedes` **and**
    `retired_by` (the prior wording would have made `retired_by` required on every new
    lesson). Commit `ac1ce30`.
14. Gate's glob corrected to `lessons/[0-9][0-9][0-9][0-9]-[0-9][0-9]-<slug>.md` (so a slug
    ending in another change's slug does not also match) and "more than one match fails the
    check" stated. Commit `ac1ce30`.

**plan.md**
15. Order of work step 1 now names `plugin/lessons/__init__.py`. Commit `ac1ce30`.
16. Added a direct unit test calling `lesson_and_eval` with a phase-(f) incident context and
    asserting it passes, proving the guard itself rather than only its registration in
    `CHECKS_BY_PHASE`. Commit `ac1ce30`.
17. Citations corrected: `HANDOFF.md:42` → `HANDOFF.md`, item 4 (no line number, since line
    42 is now item 2b on `main`); `CHECKS_BY_PHASE["e"]` → `checks.py:1646-1660` (was
    `:1646-1648`); Risk 5's `yamlish` description corrected ("skips every `---` line before
    the first content line; a `---` after content raises `expected 'key: value'`", not
    "skips exactly one"). Commit `ac1ce30`.

## Self-found gap (not from the owner)
The adversarial reviewer's first pass at this round's HEAD (`ac1ce30`) escalated: item 14's
new glob states "more than one match fails the check", but none of plan.md's four fail-case
enumerations (the `checks.py` file item, Order of work step 2, Risk 2, Proof's
`test_gate.py` item) included a test for that path — all four still listed the same seven
cases. Added "two lesson files matching the glob" as an eighth fail case to all four
plan.md enumerations, to spec.md's `checks.py` bullet and Acceptance list, and bumped every
"seven"/"up to seven reasons" count to "eight". Commit `31ca678`. Re-reviewed at HEAD
`31ca678`: continue.

## Not applied (round 2)
(none — every item in `requests` was applied; the one `not_applied` entry, a dismissed
review, carries no text to apply)

## Verdict and gate (round 2)
Adversarial review (phase b): escalate at HEAD `ac1ce30` (the eighth fail case missing from
plan.md's enumerations — see "Self-found gap" above); continue, non-routine, at HEAD
`31ca678` after the fix. Panel: mode `parked`, no pending items. Gate (b): `wait`, label
`sdlc:b-ready`, no park. Iterations: 2 of 2 (non-routine cap) — the next round, if the owner
requests more changes, is the owner's to start and the owner's `sdlc:reset-iterations`
label to re-open iterations here.

---

# Fix response — change 0003, phase (c)

Source: `evidence/fix-requests.json`, PR #132 review #5451184217 (OWNER, `CHANGES_REQUESTED`,
2026-10-08). `not_applied` in the source file was empty.

Before this round could start, the owner applied `sdlc:reset-iterations` (iterations and
panel-call count reset; `status.yaml: iterations_reset_by: luissiviero`), since gate (c) had
parked on the wall-clock/iteration limit from the prior run that hit the 200-turn cap.

1. `template/lessons/README.md` line 87 reworded from "the lesson and the eval
   (`/sdlc-deploy` step 0b)" to "the lesson and the eval case, in `/sdlc-deploy` step 0b", so
   the word "eval" is never directly followed by an opening parenthesis (the
   security-baseline scanner's `eval\s*\(` pattern was matching the prose, not code).
   `plugin/commands/sdlc-deploy.md`'s heading "## 0b. An incident's fix ships with its
   lesson and its eval (build guide steps 36, 37; ...)" had the same shape and was reworded
   to "... and its eval case (build guide steps 36, 37; ...)". Checked the rest of
   `template/lessons/README.md`, `plugin/commands/sdlc-deploy.md` and
   `plugin/commands/sdlc-maintain.md` for the same shape (grep for `eval` in all three,
   tested each hit against the scanner's exact regex): no other occurrence matches —
   `lesson_and_eval` and `` `eval` `` (backtick-delimited identifiers) are not followed by
   `(`, and "eval case"/"an eval for" are not followed by `(` either. Commit `bfe078b`.
2. Finished phase (c): wrote `evidence/diff-c.patch` (`origin/main...HEAD` at
   `bfe078b69dc691ecfd226d2872cff41dcb1b8360`), ran the adversarial reviewer (verdict:
   continue, non-routine — no reasons found; it independently traced the preflight failure
   to the same `eval\s*\(` match and confirmed no occurrence remains), then gate (c):
   `continue`. The prior run's verifier evidence (`evidence/verifier.md`) stood; nothing in
   this round's diff touched the code the verifier already exercised.

## Not applied
(none — `fix-requests.json: not_applied` was empty)

## Verification note
This session's sandbox denies read access to `tests/fixtures/sample-python-project/.env`,
which a large share of the test suite copies as part of an autouse project fixture; every
such test errors on `shutil.Error: Permission denied` in this sandbox regardless of this
change, including `tests/test_policy_skills.py` itself. This is a sandbox limitation of this
agent session, not a code defect: `python -m ruff check .` and
`python -m compileall -q plugin tests tasks.py` both ran clean, and the exact failure the
owner described was independently reproduced and confirmed fixed by (a) testing the
scanner's own `eval\s*\(` regex against the before/after lines directly, and (b) manually
replaying the `test_security_baseline_check_finds_secrets_and_dangerous_calls` fixture setup
(fixture copy minus the unreadable `.env`, `git init`/`commit`, real `/sdlc-init`, real
`security-baseline/check.py`) end to end: `rc 0`, "nothing found". The CI runner, which does
not carry this sandbox restriction, should see the test target go green.

## Verdict and gate (phase c)
Adversarial review (phase c): continue, non-routine, at HEAD `bfe078b69dc691ecfd226d2872cff41dcb1b8360`.
Panel: review mode is `parked` (not `deferred`), so no panel items apply at a fix round.
Gate (c): `continue`. Iterations: 1 of 2 (non-routine cap), after the owner's
`sdlc:reset-iterations`.

---

# Fix response — change 0003, phase (e)

Source: `evidence/fix-requests.json`, PR #132. Two reviews, both OWNER/`CHANGES_REQUESTED`.
`not_applied` in the source file was empty.

1. Review #5451184217 (2026-10-08T04:02:50Z, the eval-wording finding): already applied and
   closed in the phase (c) fix round above (commit `bfe078b`, gate (c) `continue`); nothing
   further to do.
2. Review #5452163356 (2026-10-08T05:54:37Z): three findings marked "Fix in this round",
   applied below, one test each; six marked "can wait for the tag (0.3.7); include or drop"
   — read as optional (the owner's own wording), so dropped this round and listed under "Not
   applied" rather than expanding the round's scope past what was asked.
   1. `plugin/gate/checks.py` `_supersedes_problem`: `supersedes` must now be a bare file
      name matching `[0-9][0-9][0-9][0-9]-[0-9][0-9]-*.md` (`Path(value).name == value`,
      checked with a regex) and not the lesson's own name; any other value is one problem
      line `"<lesson>: supersedes must name a lesson file in lessons/"`. The "is unreadable"
      line no longer includes `read_frontmatter`'s parser message (just the target name), so
      a crafted `supersedes` can no longer smuggle another file's first unparsable line, an
      absolute path, or a relative `../` path into the gate's "What I need from you" text.
      Three new tests in `tests/test_gate.py`: outside-`lessons/` traversal, an absolute
      path, and self-reference.
   2. `plugin/lessons/index.py`: `_read_text` now also catches `UnicodeDecodeError` (a
      non-UTF-8 lesson file goes to `## Unsorted` instead of crashing `build`/`check`); a new
      `_bad_field_shapes` check sends a present-but-wrong-shaped `detected.at` or
      `stale_after` (wrong type, or a month/day out of range) to `## Unsorted` with a note
      naming the field and the value, before either reaches `_month_label` or `is_stale`;
      `_month_label` and `_date_only` were also hardened to return `""` rather than raise on
      a non-string or out-of-range input, as the finding named them directly. Four new tests
      in `tests/test_lessons.py`: an int `stale_after`, a `detected.at` with month `13`, a
      non-UTF-8 lesson file, and a direct check that `_month_label`/`_date_only` never raise.
   3. `plugin/commands/sdlc-maintain.md` step 1: added "plus every lesson under
      `## Unsorted`" to the set of lessons the diagnosis opens (a frontmatter-less or
      unparsable lesson is still read, as the spec and README already say). Asserted in
      `tests/test_commands_and_skills.py::test_sdlc_maintain_reads_the_generated_index_first`.
   Commit: see the commit message below.

## Not applied
- Items 4–9 of review #5452163356 (the test-shape cleanup in `tests/test_gate.py`, the
  `Tags:` line test, the `sdlc-deploy.md`/README wording on `description` and scan-filed
  incidents, moving `check`'s `mkdir` and rejecting a bad `--today`, the two advisory
  `eval (`-shaped comments, and the `docs/OPERATING_MODEL.md` wording) — not applied: the
  owner marked them "can wait for the tag (0.3.7); include or drop" rather than "fix in this
  round".

## Verification note
As in the phase (c) round above, this session's sandbox denies read access to
`tests/fixtures/sample-python-project/.env`; every test that copies that fixture tree
(`shutil.copytree`) errors on `Permission denied` regardless of this change. Of 395
failing/erroring items in a full `python -m pytest` run, 394 are that one denial (including
`tests/test_gate.py::test_clean_tree_ignores_a_nested_env_the_sandbox_mounted_over`, which
names the same phenomenon) and the last is
`tests/test_gate.py::test_the_sandbox_s_mask_is_read_from_its_mounts`, whose own docstring
describes exactly this kind of nested-sandbox mount reclassification — neither touches code
this round changed. `python -m ruff check .` and
`python -m compileall -q plugin tests tasks.py` both ran clean, and every test added or
touched by this round (`tests/test_gate.py -k "supersedes or lesson_and_eval or
month_label or date_only"`, all of `tests/test_lessons.py`, all of
`tests/test_commands_and_skills.py`) passed in isolation from the masked fixture.

## Verdict and gate (phase e)
See `evidence/gate-e.json` and the adversarial review recorded for this round's HEAD.
