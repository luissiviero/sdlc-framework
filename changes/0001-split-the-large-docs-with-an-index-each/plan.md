# Plan: split the large docs with an index each (from intent.md 2026-10-02, spec.md 2026-10-02)

## Files that change
- `docs/notes/index.md` — new; one line per NOTES section file, in section-number order.
- `docs/notes/<N>-<slug>.md` — new; one per `## ` section of today's `docs/NOTES.md` (23 at
  this reading: sections 1–23). Each carries the section's text unchanged plus frontmatter
  (`title`, `sources`, `generated.at`, `verified_with`, `stale_after`). A build-time pass
  re-derives the exact set and slugs from whatever `## ` headings exist in `docs/NOTES.md`
  then (sessions 15–16 may add sections 24+ before phase (c) runs; see Risks).
- `docs/NOTES.md` — rewritten to a short stub: title plus one pointer sentence to
  `docs/notes/index.md`.
- `docs/decisions/index.md` — new; one line per decision file, in decision-number order.
- `docs/decisions/<N>-<slug>.md` — new; one per numbered decision in today's
  `docs/DECISIONS.md` (26 at this reading). Each carries the decision's text unchanged plus
  frontmatter (`status`, `reversibility`, `amended_by`).
- `docs/DECISIONS.md` — rewritten to a short stub: title plus one pointer sentence to
  `docs/decisions/index.md`.
- `docs/progress/index.md` — new; one entry per archived record, grouped by session.
- `docs/progress/<slug>.md` — new; one per non-current top-level `# ` heading of today's
  `docs/PROGRESS.md` (14 at this reading: everything but "session 14, second sitting").
  Text unchanged; a build-time pass re-derives the set from whatever headings exist then
  (sessions 15–16 append new records; see Risks).
- `docs/PROGRESS.md` — rewritten to hold only its current top-level record (whichever one is
  current when phase (c) runs); no stub needed, name and role unchanged.
- `HANDOFF.md` — "Read in this order" rewritten index-first for the three split docs; every
  existing list item's reason kept, only the target file changed from a `docs/NOTES.md §N` /
  `docs/DECISIONS.md` / `docs/PROGRESS.md` pointer to the matching new path or index.
- `docs/ROADMAP.md` — its `docs/DECISIONS.md` mention (the "nothing here reopens a decision"
  line) repointed to `docs/decisions/index.md`.
- `docs/OPERATING_MODEL.md` — its `docs/DECISIONS.md` and `docs/NOTES.md` mentions repointed
  to the matching index.
- `README.md` — its `docs/OPERATING_MODEL.md`/`docs/PROGRESS.md`/`docs/NOTES.md`/
  `docs/DECISIONS.md` mentions (the overview paragraph and the two table rows) repointed to
  the matching index where the file split (NOTES, DECISIONS); the `docs/PROGRESS.md` mention
  is left as is (that file's name and role do not change).
- `docs/PROGRESS.md` (the then-current record) — a new entry recording this change's own
  work, including the `CLAUDE.md` guardrail-edit table for the owner (spec.md Acceptance),
  per "Things Claude gets wrong".

No file under `plugin/`, `template/` or `tests/` changes; `CLAUDE.md`, `.claude/**`,
`REVIEW.md` and `sdlc.yaml` are not touched (guardrails; the owner edits `CLAUDE.md` after
this merges, from the table this change's PROGRESS entry gives).

## Order of work
1. Re-list `docs/NOTES.md`'s `## ` sections, `docs/DECISIONS.md`'s numbered decisions and
   `docs/PROGRESS.md`'s non-current `# ` headings as they stand at the start of phase (c)
   (they may differ from this reading; sessions 15–16 run first). This list is the exact file
   set for the next three steps.
2. Split `docs/NOTES.md`: create `docs/notes/<N>-<slug>.md` per section (text moved verbatim,
   frontmatter added from the section's existing read date and sources), then
   `docs/notes/index.md`, then rewrite `docs/NOTES.md` to the stub. One commit.
3. Split `docs/DECISIONS.md`: create `docs/decisions/<N>-<slug>.md` per decision (text moved
   verbatim, frontmatter from the decision's existing Accepted/Amended/reversibility lines),
   then `docs/decisions/index.md`, then rewrite `docs/DECISIONS.md` to the stub. One commit.
4. Split `docs/PROGRESS.md`: create `docs/progress/<slug>.md` per non-current record (text
   moved verbatim), then `docs/progress/index.md` grouped by session, then rewrite
   `docs/PROGRESS.md` to hold only the current record. One commit.
5. Update the four live docs' links/mentions: `HANDOFF.md` (the reading list, index-first),
   `docs/ROADMAP.md`, `docs/OPERATING_MODEL.md`, `README.md`. One commit; with the Edit tool,
   sentence by sentence, never a script (CLAUDE.md: the auto-mode classifier blocks a scripted
   rewrite whose payload reads like instructions).
6. Run the project's build, test and lint commands (none are expected to change, since no
   `plugin/`/`template/`/`tests/` file moved) and record the evidence logs.
7. Add this change's own `docs/PROGRESS.md` entry (now the current record, after step 4
   rewrote the file) with the `CLAUDE.md` guardrail-edit table for the owner.

## Risks
- **Most of this is not implementable from this plan alone yet, by design**: the intent holds
  the design PR unmerged until session 16 closes Milestone 1, so phase (c) starts from
  whatever `docs/NOTES.md`, `docs/DECISIONS.md` and `docs/PROGRESS.md` contain *then*, not from
  today's 23/26/14. Step 1 of Order of work exists for exactly this reason: it is not
  optional busywork, it is how the plan stays correct despite the gap. The riskiest step is
  step 1 for that reason — get the count or a slug wrong there and every later step
  propagates it.
- A link-update miss in one of the four live docs (step 5) is low-impact (the stub still
  resolves the old path) but would leave a stale pointer; mitigate by grep'ing each of the
  four files for the three old paths after editing, not just before.
- A historical doc (`docs/handoffs/*`, `docs/reviews/*`, `docs/proposals/okf-adoption.md`)
  is deliberately not rewritten (spec.md Requirements); someone reading one later still sees
  `docs/NOTES.md §N`, and must follow the stub rather than a direct link. This is the chosen
  trade-off (choice 126: a kept record is never rewritten), not an oversight — called out here
  so a reviewer does not flag it as a missed file.
- Nothing in `plugin/` reads these docs at runtime (confirmed by grep: only comments and one
  user-facing reason string in `plugin/ci/auth.py` cite `docs/NOTES.md section 2`, and the
  stub keeps that string's citation resolvable), so the build/test/lint commands are not
  expected to change behaviour. If a future test is added that reads `docs/NOTES.md`'s content
  directly (none exists today), it would break on the stub; nothing in today's `tests/`
  does this.
- Caller/consumer check (interrogation Q1): every caller of these three files is a human
  reader or a prose citation, not code — confirmed by grepping `plugin/`, `template/`,
  `tests/`, `.github/` for `docs/NOTES.md`, `docs/DECISIONS.md`, `docs/PROGRESS.md` literal
  paths (10 files, all comments or an error-reason string) and for `NOTES §` / `decision N`
  (prose citations, ~140 occurrences across the repo, none of them a code path). No data
  shape changes; nothing is parsed from these files today.

## Options not taken
- **Split by `###` subsection too** (so `NOTES §11a` got its own file): rejected — the intent's
  example (`17-...md` for a whole section) and the "section per session, dated" rule (choice
  93) both treat one `##` section as the atomic, dated unit; splitting subsections would
  separate facts that share one read date and one `verified_with` value for no benefit, since
  every citation found in the codebase cites at most a `##`-level section or a lettered
  subsection that stays inside it.
- **Rewrite the historical docs' old-path citations to the new paths**: rejected — choice 126
  forbids rewriting a kept record's sentence; the stub exists precisely so this is unnecessary.
- **Update `docs/MODEL_ALLOCATION.md`'s two mentions along with the four live docs**: rejected
  for this change — the intent names exactly four files; `MODEL_ALLOCATION.md`'s mentions are
  prose, not links, and still resolve through the stub (spec.md Flagged concerns, closed).
- **A generated, code-validated frontmatter schema** (parsed and gate-checked, as
  `intent.md`/`spec.md`/`plan.md` are): rejected for this change — it would touch `plugin/`
  (a version bump, out of scope per intent Constraints) for a benefit (machine validation of
  reference docs nothing reads yet) the intent does not ask for; the OKF-adoption proposal
  files this under "medium effort, not before `lessons/` needs it", and these three docs are
  read by humans and by a session following a prose instruction, same as today.
- **Do the split now, merge now**: rejected — the intent's Constraints are explicit that
  sessions 15–16 must not have their reading list moved mid-road; the design is produced now
  so the owner can review it early, but the design PR itself is held unmerged until session 16
  closes the milestone.

## Proof
- `python -m compileall -q plugin tests tasks.py` — must finish with no output, exit 0
  (sdlc.yaml `commands.build`); unaffected by a docs-only diff, confirms nothing under
  `plugin/`/`tests/`/`tasks.py` was touched by mistake.
- `python -m pytest` — all green (sdlc.yaml `commands.test`); no new test is added by this
  change (nothing in `plugin/` or `tests/` changes behaviour), so this is a regression check,
  not new coverage.
- `python -m ruff check .` — zero warnings (sdlc.yaml `commands.lint`).
- A manual link-resolution pass over `HANDOFF.md`, `docs/ROADMAP.md`,
  `docs/OPERATING_MODEL.md`, `README.md` and the two stubs: every path they point at exists.
- A grep for `docs/NOTES.md`, `docs/DECISIONS.md`, `NOTES §`, `decision ` across `plugin/`,
  `template/`, `tests/`, `.github/`, `docs/` (excluding `docs/BUILD_GUIDE.md`,
  `docs/build_guide.json`, `docs/handoffs/`, `docs/reviews/`, `docs/proposals/`) resolving to
  an existing file, directly or through a stub — the spec's Acceptance target; no automated
  test exists for this today, so it is evidence collected by hand in phase (c)/(d), not a
  pytest name.
