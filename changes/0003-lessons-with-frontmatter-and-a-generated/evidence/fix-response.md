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

## Self-found gaps (not from the owner)
1. The plan.md/spec.md sync fix above (applying items 1-3) left two "Files that change"
   bullets and the Acceptance list behind: `checks.py`'s and `test_gate.py`'s bullets still
   enumerated the old eight fail cases, and `test_lessons.py`'s bullet still said only
   "malformed frontmatter" (missing the non-UTF-8 and bad-date-shape cases). A re-review
   caught it; fixed in commit `00ddfc7`, re-reviewed clean.
2. The first adversarial pass at HEAD `00ddfc7` escalated because `evidence/verifier.md`
   was still the phase (d) report — stale for this round's code changes. A fresh
   `sdlc:verifier` sub-agent ran and exercised `_supersedes_problem` and
   `plugin/lessons/index.py build`/`check` directly (path-traversal, absolute, self-
   reference and secret-content inputs for the first; wrong-type `stale_after`,
   out-of-range `detected.at`, non-UTF-8 file for the second); this session then failed to
   write its report to `evidence/verifier.md` (the verifier agent has no Write tool — the
   calling session persists its report, and this round's session initially did not).
   Caught on the next adversarial pass; `evidence/verifier.md` written from the sub-agent's
   actual report, re-reviewed: `continue`.

## Iteration cap: a process error, not a content problem
`/sdlc-fix` step 2 already bumped the iteration counter once for this round (1 → 2, at the
cap, not over it) before any work started. Resolving the phase (e) `findings` check's
staleness (the review pass needed to run on this round's new HEAD; see "Self-found gaps"
above) led this session to also call `/sdlc-deploy` step 2's own `bump-iteration` — a second
bump within the same already-registered `/sdlc-fix` round, which pushed the counter to 3
against the non-routine cap of 2. There is no self-service undo (only the owner's
`sdlc:reset-iterations` label, or `set-iterations` by hand, lifts it), so gate (e) now parks
on `limits` regardless of the content above, all of which is otherwise complete and green:
the three owner-requested fixes, the two self-found plan/spec sync gaps, the refreshed
review pass, and the fresh verifier evidence.

## The 4 Important findings on this round's final review pass
Documented separately in `evidence/review-response.md`: the framework's second-occurrence
rule fired on four pre-existing nits (three of them the owner's own PR #132 review already
marked "can wait for the tag (0.3.7)") because this round's own extra review re-runs (to
chase the plan.md sync gaps above) crossed the recurrence threshold inside one round rather
than across separate historical ones. The rule's actual remedy — proposing the one-line
`CLAUDE.md` entries — is satisfied (`evidence/claude-md-proposals.md`, carried into the PR
body by `pr/cli.py upsert`); the underlying code is not changed, per the owner's own
deferral and to avoid scope creep beyond what either the owner or this round's intent asked
for.

## Verdict and gate (phase e)
Adversarial review: `continue` (at HEAD `00ddfc7e177c2bdb289e0ec10fbf7fca9e9824e5`, after the
verifier-evidence gap above was closed). Panel: mode `parked`, no pending items. Gate (e):
`park` — `limits: iteration cap reached: 3 fix iterations, cap 2 (non-routine)`, label
`sdlc:needs-human`. What's needed from the owner: `sdlc:reset-iterations` (or
`set-iterations --count 0`) to open another round, if one is wanted; otherwise the three
requested fixes, the plan/spec sync, and the fresh verifier/review evidence all stand as
committed and green, and the four proposed `CLAUDE.md` lines are ready to apply from the PR
body.

## Round 4 (after `sdlc:reset-iterations`): nothing new to apply

Source: `evidence/fix-requests.json`, re-collected at `2026-10-08T11:27:23+00:00`
(`head` `35794300dabdd36135578b9028adfc651504afbe`). The two `requests` are the same OWNER
reviews #5451184217 (2026-10-08T04:02:50Z) and #5452163356 (2026-10-08T05:54:37Z) already
worked through in earlier rounds; GitHub keeps a "Request changes" review active until the
author re-reviews or dismisses it, so the same text resurfaces every time this file is
collected. `not_applied` is empty (both authors are the OWNER).

Checked each item against the current tree:
- Review #5451184217 (the preflight/`eval (` wording, finish phase (c)): `template/lessons/
  README.md` already reads "the eval case, in `/sdlc-deploy` step 0b" (no `eval (` shape
  left), and phase (c)'s verdict, gate and PR summary were already reached (the change is at
  phase (e)). Nothing to do.
- Review #5452163356, items 1-3 ("fix in this round"): `_supersedes_problem` already rejects
  a non-bare-filename, a self-reference and a non-`[0-9][0-9][0-9][0-9]-[0-9][0-9]-*.md`
  name, and reports "is unreadable" without the parser's message
  (`plugin/gate/checks.py:1612-1632`); `plugin/lessons/index.py`'s `_read_text` catches
  `UnicodeDecodeError` alongside `OSError`, and `_bad_field_shapes` sends a wrong-type
  `stale_after` or an out-of-range `detected.at` to `## Unsorted` before `_date_only`/
  `_month_label` ever see them, each with its own `tests/test_lessons.py` case; and
  `plugin/commands/sdlc-maintain.md` step 1 already names `## Unsorted`, asserted in
  `tests/test_commands_and_skills.py`. All three were committed in an earlier round; still
  green. Nothing to do.
- Items 4-9 ("Can wait for the tag (0.3.7); include or drop"): not applied, but not for lack
  of trying first. This round initially drafted items 8 and 9 (reworded the `eval (`-shaped
  comments at `plugin/gate/artifacts.py:89` and `plugin/gate/checks.py:1637`, and
  `docs/OPERATING_MODEL.md:144`'s "a heading per tag" to "a heading per class";
  `evidence/hook-log.jsonl` has the three `Edit` calls at 11:38:30-11:38:37Z) before
  reconsidering: the owner's own review text marks items 4-9 optional and a prior round
  (`review-response.md`: "not changed ... per the owner's own deferral and to avoid scope
  creep") already made the deliberate choice to leave all six for the owner or the 0.3.7 tag,
  and nothing in this round's `fix-requests.json` reopens items 8 or 9 specifically — the
  same two reviews, unchanged. Picking two of the six to apply now, with no new instruction
  naming them, would overturn that documented decision without the owner asking for it, so
  the three edits were reverted with `git checkout --` before this round's commit (confirmed
  by `git diff` showing no change to those three files beforehand). They stay available for a
  future round, or the 0.3.7 tag, at the owner's choice.

What actually needed doing this round was the park itself: gate (e) parked only on `limits`
(`evidence/gate-e.json`'s single check, `"stop": true`), which the prior round's own note
calls "a process error, not a content problem" — a second `bump-iteration` inside one
`/sdlc-fix` round pushed the counter to 3 against the non-routine cap of 2, while every
other check was green. The owner's `sdlc:reset-iterations` label (recorded in `status.yaml:
iterations_reset_by: luissiviero`, `iterations_reset_at: 2026-10-08T11:27:20Z`) is the
change request this round applies: `gate/cli.py start-run` then `bump-iteration` (→ 1 of 2,
cap not reached), no code change, and the verdict and gate re-run below on the unchanged
diff.

Build, lint and the targeted tests for the files these reviews touch
(`tests/test_lessons.py`, `tests/test_gate.py -k "supersedes or lesson_and_eval"`,
`tests/test_commands_and_skills.py`) are green. The full `python -m pytest` cannot complete
in this sandboxed session: the sandbox's read-deny list covers
`tests/fixtures/sample-python-project/.env` itself (and its `framework/` copy), so every
test that copies that fixture tree hits `shutil.Error: Permission denied` on that one file —
present at this round's very first `git status`, before any edit, and unrelated to this
change's code. `tests/test_gate.py::test_the_sandbox_s_mask_is_read_from_its_mounts` also
fails here (`_mount_masked(Path("/dev/null"))` is `True` in this container, where the test
expects `False`); `plugin/gate/diff.py` was last touched by plugin 0.3.4, not by this change,
so this is a pre-existing environment difference, not a regression from this round.
