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

# Fix response — phase (e), round 3

`evidence/fix-requests.json` (collected 2026-10-03T21:09:02Z, head `428cbbd`) lists the same
two reviews as round 2 (`#pullrequestreview-5402438162`, `#pullrequestreview-5402516760`,
both "re-run gate (c): the park was the sandbox's view of the fixture `.env`"): applied
already, in round 2 — nothing new to apply from them this round. `status.yaml`'s
`parked_reason` was the iteration cap at gate (e) (3 fix iterations, cap 2), which the
owner cleared with the `sdlc:reset-iterations` label before this round started
(`iterations_reset_by: luissiviero`); that label is itself a change request (decision 24)
and is what let this round run at all.

With the cap reset, this round registered (`gate/cli.py start-run`, `bump-iteration`:
iterations 0 → 1 of 2) and moved to the substance the review pass at phase (e) had found
pending: one Important finding (this change's own `docs/PROGRESS.md` entry spliced into an
old, superseded session record instead of becoming its own new top-level record — fixed,
independently confirmed by a fresh review pass) and a second Important finding
(`docs/notes/<N>.md` frontmatter's `verified_with` missing the plugin-version/runner parts
spec.md Requirements asks for) that was only partly fixed: plugin version filled in for the
6 of 32 files whose own text states it directly (`docs/notes/27.md`–`32.md`), runner left
out for those six and the whole fix left out for the other 26, each reasoned in
`evidence/review-response.md` (writing an inferred, unconfirmed value into the field that
decides staleness is worse than leaving it incomplete). Gate (e) parked again, on the open
finding and the adversarial reviewer's `escalate` — a different reason than the round's
starting park, so this round stops here per step 5: the next round, fix or waiver, is the
owner's.

# Fix response — phase (e), round 4

`evidence/fix-requests.json` (collected 2026-10-03T22:32:33Z, head `5adc2a7`) lists three
reviews:

- luissiviero (OWNER), reviews
  https://github.com/luissiviero/sdlc-framework/pull/112#pullrequestreview-5402438162 and
  https://github.com/luissiviero/sdlc-framework/pull/112#pullrequestreview-5402516760
  ("re-run gate (c): the park was the sandbox's view of the fixture `.env`"): already
  applied, in round 2 (and read again, unchanged, in round 3's response) — nothing new to
  apply from them this round.
- luissiviero (OWNER), review
  https://github.com/luissiviero/sdlc-framework/pull/112#pullrequestreview-5403131990:
  applied. The owner waived the `verified_with` gap round 3 left open
  (`evidence/review-response.md`'s round-1 paragraph: 26 of the 32 `docs/notes/<N>.md`
  files cannot state their own writing session's environment, so a runner value would be
  inferred, not read) — "verified_with keeps the Claude Code version each section names,
  plus the plugin version where the section records one; a runner is not required."
  `spec.md` Requirements line 11 now says that, replacing "Claude Code version, plugin
  version, runner", and a new item under `## Flagged concerns` records it as
  `decided (owner, PR #112 review 2026-10-03, fix round 4): ...` with the owner's
  reasoning. This closes the one open Important finding (`docs/notes/2.md:5`, signature
  `7cd11e55e64ea40f`): the live frontmatter across all 32 files already matches the
  now-decided rule (Claude Code version everywhere, plugin version on the six files that
  state it directly, no file claims a runner), so no frontmatter edit was needed, only the
  spec.
  The same comment also asked to "count 32 sections in the PROGRESS summary (the index
  lists 32)": `docs/PROGRESS.md:4` ("`docs/NOTES.md` (30 sections)") corrected to "32
  sections", closing the matching nit (signature `3534444a4c1cb752`).

No requests were left unapplied this round. Not touched (not asked for, and still the same
open items from `evidence/review-findings.json`'s remaining nits, each with its own
accepted reasoning already in `evidence/review-response.md`): the four archived
`docs/PROGRESS.md` top-level records (traced to a later `main` merge, not this change's own
edits), the `docs/notes/1.md` `sources` doubt, and the `CLAUDE.md` guardrail table's
3-vs-4 rows.
