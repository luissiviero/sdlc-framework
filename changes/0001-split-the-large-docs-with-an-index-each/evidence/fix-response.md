# Fix response — phase (b), round 1

- luissiviero (OWNER), review https://github.com/luissiviero/sdlc-framework/pull/90#pullrequestreview-5397029919:
  applied. Both flagged concerns closed in `spec.md` under `## Flagged concerns`, each
  starting `decided (PROGRESS choice 134): ...`. Concern 1 (file-name slugs): `spec.md`
  Requirements and Design, and `plan.md` "Files that change" and "Order of work" steps 1-4,
  now name `docs/notes/<N>.md`, `docs/decisions/<N>.md`, `docs/progress/session-<N>.md` /
  `docs/progress/session-<N>-sitting-<M>.md` and
  `docs/progress/2026-09-28-workflow-comparison-study.md` — number-only, no slug — everywhere
  a `<N>-<slug>.md` or `<slug>.md` form appeared, including the HANDOFF reading-list sentence.
  Concern 2 (index order): the three index sentences in `spec.md` Requirements, Design and
  Acceptance, and the three `index.md` lines of `plan.md` "Files that change" and "Order of
  work" steps 2-4, now say ascending number order, one line per file, the original heading as
  the description; `docs/progress/index.md`'s rule keeps the study record's place between
  sessions 12 and 13 and groups a sitting's line directly after its session's, with no
  grouping by topic or tag. `plan.md`'s Risks paragraph on slugs updated to reflect that file
  names no longer depend on a heading-derived slug. Nothing else changed; `intent.md` was not
  touched (decision 22).

No requests were left unapplied.

# Fix response — phase (c), round 2

- luissiviero (OWNER), review https://github.com/luissiviero/sdlc-framework/pull/112#pullrequestreview-5402438162:
  applied. Re-ran gate (c) as asked (commit 1183760). No code change: the prior park
  (`clean_tree: 1 uncommitted file(s) outside the change folder: tests/fixtures/sample-python-project/.env`)
  was the CI sandbox masking that fixture file by mounting `/dev/null` over it, not a real
  uncommitted change — `plugin/gate/checks.py`'s `clean_tree` check already looks past a
  sandbox-mounted path inside a CI session (plugin 0.3.4) and confirmed it this round
  (`"ignored": ["tests/fixtures/sample-python-project/.env"]`). The adversarial reviewer
  verdict is `continue`, non-routine; gate (c) result is `continue`.
- luissiviero (OWNER), review https://github.com/luissiviero/sdlc-framework/pull/112#pullrequestreview-5402516760:
  applied. Same request, same round and result as above (duplicate re-run instruction).

No requests were left unapplied.
