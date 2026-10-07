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
