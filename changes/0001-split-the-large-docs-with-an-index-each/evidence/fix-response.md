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
