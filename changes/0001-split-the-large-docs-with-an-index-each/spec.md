# Spec: split the large docs with an index each
Change id: 0001. Status: proposed. Produced by: sdlc plugin 0.2.29, /sdlc-design prompt v1 (article p.14). Skills: coding-standards, security-baseline, ux-conventions, data-conventions, definition-of-done (plugin 0.2.29); overrides: none

## Requirements
- `docs/notes/` holds one file per `docs/NOTES.md` `## ` section (23 files today), named
  `docs/notes/<N>.md` by number only, no slug (for example `docs/notes/17.md`), so every
  `NOTES §N` citation (about 20 in `plugin/`, `docs/` and `tests/`, none of them under
  `docs/BUILD_GUIDE.md`) still points at one file; a `### 11a`/`11b`/`11c`-style subsection
  stays inside its parent section's file, so a citation like `NOTES §11c` still resolves
  without a per-subsection split. Each file's frontmatter carries `title`, `sources`,
  `generated.at` (the section's existing read date), `verified_with` (Claude Code version,
  plugin version, runner) and `stale_after` (`generated.at` + 90 days); a file is stale when
  `verified_with` no longer matches the environment or `stale_after` has passed, whichever
  first (both from choice 93: one section is one session's dated batch, so the fields are per
  file). `docs/notes/index.md` lists every file in ascending section-number order, one line
  each, the section's original `## ` heading as the description.
- `docs/decisions/` holds one file per decision in `docs/DECISIONS.md` (26 files), named
  `docs/decisions/<N>.md` by number only, no slug (for example `docs/decisions/21.md`). Each
  file's frontmatter carries `status` (`accepted` or `amended`), `reversibility` (`sticky` or
  `reversible`, as stated today) and `amended_by` where an amendment exists (for example
  decision 18, amended by 21). `docs/decisions/index.md` lists every decision in ascending
  number order, one line each, the decision's original heading as the description.
- `docs/PROGRESS.md` keeps only its current top-level record (session 14, second sitting); the
  other 14 top-level records move to `docs/progress/`, one file per heading, named from the
  heading: `docs/progress/session-<N>.md` for a session's record, `docs/progress/session-<N>-
  sitting-<M>.md` for a sitting (so "session 14, first sitting" is `session-14-sitting-1.md`),
  and `docs/progress/2026-09-28-workflow-comparison-study.md` for the one record that is not a
  session. `docs/progress/index.md` lists every record in ascending session-number order, one
  line each, a sitting's line directly after its session's, the record's original `# ` heading
  as the line; the study record keeps the place it has in today's `docs/PROGRESS.md`, between
  the records of sessions 12 and 13. No grouping by topic or tag.
- Every moved record keeps its text unchanged (choice 126: a kept record is annotated beside
  the sentence, never rewritten); only links and section references are updated by the move,
  never the sentence itself. This applies to every file moved by this change, not only
  `docs/progress/`.
- `HANDOFF.md`'s "Read in this order" list is rewritten to read the index first, then only the
  files needed, for each of the three split docs, keeping its existing per-item explanation of
  why that file matters.
- `docs/NOTES.md` and `docs/DECISIONS.md` become short permanent stub files pointing at
  `docs/notes/index.md` and `docs/decisions/index.md`; a link or citation that names the old
  path still resolves to a file. `docs/PROGRESS.md` is not stubbed: it keeps its purpose
  (current record) under the same name, per the Proposed outcome.
- The same PR updates the links in `HANDOFF.md`, `docs/ROADMAP.md`, `docs/OPERATING_MODEL.md`
  and `README.md` to the new index paths — exactly the four files the intent names. A doc not
  on that list (for example `docs/MODEL_ALLOCATION.md`, which names `docs/PROGRESS.md` and
  `docs/NOTES.md` once each in prose, not as a link) is left as written; see Flagged concerns.
- A historical record that cites the old path in prose (`docs/handoffs/*.md`, `docs/reviews/*`,
  `docs/proposals/*`, and the archived sessions inside `docs/progress/` themselves) is not
  rewritten: it is a point-in-time record, and the stub keeps the citation resolvable (choice
  126 applies to records, not to live reference docs).
- No file under `plugin/` or `template/` changes. The code strings and comments that cite
  `docs/NOTES.md section N` (for example `plugin/ci/auth.py`'s unattended-run error reason,
  `plugin/hooks/_common.py`, `plugin/gate/limits.py`) keep resolving through the stub; they are
  not edited, so there is no version bump, no tag and no pin (coding-standards rule 6: never
  edit generated or out-of-scope files as a side effect; here, never touch code as a side
  effect of a docs-only change).
- `docs/BUILD_GUIDE.md` and `docs/build_guide.json` are not touched (intent Constraints); their
  "NOTES §N" / "decision N" mentions are prose citations of a number, not paths, and keep
  resolving under the new layout unchanged.
- Checkable: every `NOTES §N`, `decision N` and `docs/NOTES.md` / `docs/DECISIONS.md` /
  `docs/PROGRESS.md` path citation under `plugin/`, `template/`, `tests/`, `.github/` and
  `docs/` still resolves (directly, or through a stub) to an existing file; `python -m
  compileall -q plugin tests tasks.py`, `python -m pytest` and `python -m ruff check .` stay
  green (sdlc.yaml commands; none of them read the moved docs, so none are expected to change
  behaviour).
- security-baseline, data-conventions: no secret, credential or personal/sensitive data is
  moved or introduced; the moved text is the existing platform facts, decisions and session
  records, unchanged (rules 3–4 of each skill do not constrain this change beyond that).
- ux-conventions: does not apply — there is no user-facing screen, component or visible copy
  here; the "UI changed" check has nothing to flag.
- risk_list (`sdlc.yaml`): none of auth, data migrations, money movement or production config
  is touched; this is a documentation-only move, so none of the four items is named under
  Flagged concerns (spec-template rule: name only what the design touches).

## Design
- Three independent splits, same shape each time: one source file becomes one `index.md` plus
  N small files, each keeping the source section's number in its file name and its text
  byte-for-byte except for updated internal links/section references. No file outside
  `docs/notes/`, `docs/decisions/`, `docs/progress/`, the two stub files, `HANDOFF.md`,
  `docs/ROADMAP.md`, `docs/OPERATING_MODEL.md` and `README.md` changes.
- Frontmatter is a plain YAML block per file, read by nothing today (no code parses
  `docs/notes/*.md` or `docs/decisions/*.md` yet); it is documentation metadata only, matching
  how `intent.md`/`spec.md`/`plan.md` already carry a prose header line rather than a validated
  schema (OKF-adoption proposal, row 2). Nothing in `plugin/gate/artifacts.py` is changed or
  needs to be: these files are not gated artifacts.
- `docs/notes/<N>.md` frontmatter fields, one block per the Requirements above:
  `title`, `sources` (the docs URL or run URL and the verbatim quote already in the section,
  restated as structured data, not reworded), `generated.at` (copied from the section's
  existing read date), `verified_with`, `stale_after`. The staleness rule is unchanged from
  choice 93, expressed as two comparable fields instead of prose ("re-test when the date is
  older than the environment's last change").
- `docs/decisions/<N>.md` frontmatter: `status`, `reversibility`, `amended_by`. These
  three values already exist in `docs/DECISIONS.md`'s "Accepted"/"Amended by"/"Decide by /
  reversibility" lines for every decision; the frontmatter restates them, it does not decide
  anything new.
- `docs/progress/session-<N>.md` / `docs/progress/session-<N>-sitting-<M>.md` per top-level
  `# ` heading of today's `docs/PROGRESS.md` (14 files for the 14 non-current records), named
  from the heading, plus `docs/progress/2026-09-28-workflow-comparison-study.md` for the one
  non-session record; `docs/progress/index.md` lists them in ascending session-number order,
  one line per file, a sitting's line directly after its session's, the study record keeping
  the place it has in today's `docs/PROGRESS.md` (between sessions 12 and 13), the original
  `# ` heading as each line, no grouping by topic or tag. `docs/PROGRESS.md` itself shrinks to
  the current record (session 14, second sitting) and keeps its name and role: the file a
  session appends to next.
- Stubs: `docs/NOTES.md` and `docs/DECISIONS.md` become a one-line title plus a pointer
  sentence to the matching `index.md`, so an old link still opens a file and a reader lands on
  the index one click away. `docs/PROGRESS.md` needs no stub because its name and role do not
  change.
- `HANDOFF.md`'s "Read in this order" keeps one list item per file it names today, each still
  carrying its existing one-line reason; where it names `docs/NOTES.md §N` today, it names the
  matching `docs/notes/<N>.md` file (or the index, for a section-agnostic pointer); same for
  `docs/DECISIONS.md` and `docs/PROGRESS.md`'s archived sessions. The index-first instruction
  itself ("index first, then the files you need") is a new, one-line opening note, not a
  restructuring of the list.
- `CLAUDE.md`'s own three references (`docs/DECISIONS.md` line 3, `docs/NOTES.md` line 35,
  `docs/PROGRESS.md` line 39) are not touched by this change: `CLAUDE.md` is a guardrail file,
  edited only by the owner, in a reviewed PR, after this split merges. This spec's job ends at
  handing the owner the table of what those lines must become; `plan.md` carries the exact
  rows (skill `plan-template`; build guide step this PR cannot take).
- Timing (intent Constraints, carried into Design because it shapes the diff's lifetime): this
  spec and the plan are produced now, at change 0001's phase (b); the design PR stays open,
  unmerged, until session 16 closes the Milestone 1 roadmap. Phase (c) build — the actual file
  moves — starts only after that merge, from whatever `docs/NOTES.md`, `docs/DECISIONS.md` and
  `docs/PROGRESS.md` look like then (sessions 15 and 16 both still append to them). `plan.md`'s
  "files that change" is therefore a shape (one file per section/decision/heading existing at
  build time), not a fixed list of names — the exact count of NOTES sections, decisions and
  PROGRESS records may have grown by the time phase (c) runs.

## Open questions from intent
Intent's "## Open questions" section states none are open; it quotes the five questions the
owner settled on 2026-09-02 (PR #86) and gives each an answer already folded into Proposed
outcome and Constraints above:
- "`stale_after`: the environment the facts were read under plus a 90-day backstop, per
  file" — carried into Requirements/Design's `docs/notes/` frontmatter above.
- "PROGRESS: one file per existing top-level heading, so no record is merged or rewritten" —
  carried into Requirements/Design's `docs/progress/` split above.
- "Timing: intent now, design now, the design PR held until after `v1.0.0`" — carried into
  Design's Timing paragraph above.
- "`docs/BUILD_GUIDE.md`: left as it is" — carried into Requirements above (not touched).
- "Old-path stubs: kept for good; live-doc links updated in the same PR" — carried into
  Requirements/Design's stub and four-file link update above.
None of the five is reopened here; all five are restated as design constraints, not decided
again.

## Flagged concerns
- [x] `docs/MODEL_ALLOCATION.md` names `docs/PROGRESS.md` and `docs/NOTES.md` once each, in
  prose describing what a build session produces, not as a navigational link. The intent's
  Proposed outcome names exactly four live docs to update (`HANDOFF.md`, `docs/ROADMAP.md`,
  `docs/OPERATING_MODEL.md`, `README.md`); `docs/MODEL_ALLOCATION.md` is not among them, and
  its mentions still resolve through the stub, so it is left unedited per the intent's explicit
  list (decided: follow the named scope, not every file a grep finds).
- decided (PROGRESS choice 134): number-only file names, no slug. `docs/notes/<N>.md` (one
  file per `## N.` section of `docs/NOTES.md`; a lettered subsection — `11a`/`11b`/`11c` —
  stays inside its parent section's file); `docs/decisions/<N>.md` (one file per decision);
  `docs/progress/session-<N>.md` for a session's record and `docs/progress/session-<N>-
  sitting-<M>.md` for a sitting, both read from the record's heading, and
  `docs/progress/2026-09-28-workflow-comparison-study.md` for the one record that is not a
  session. Why: every citation already uses the number (`NOTES §17`, `decision 21`, "session
  14, second sitting"), so a renamed heading never leaves a stale file name, and nothing
  derives a slug at build time.
- decided (PROGRESS choice 134): each index in number order, one line per file, the original
  heading as its description. `docs/notes/index.md` and `docs/decisions/index.md`: ascending
  number order. `docs/progress/index.md`: ascending session-number order, a sitting's line
  directly after its session's, the study record keeping the place it has in today's
  `docs/PROGRESS.md` (between sessions 12 and 13). No grouping by topic or tag in any of the
  three indexes (that waits for R1's step 1, tags).

## Acceptance
- Every `NOTES §N`, `decision N` reference and every literal `docs/NOTES.md` / `docs/DECISIONS.md`
  / `docs/PROGRESS.md` path under `plugin/`, `template/`, `tests/`, `.github/` and `docs/`
  (excluding `docs/BUILD_GUIDE.md`, `docs/build_guide.json`, and the historical
  `docs/handoffs/`, `docs/reviews/`, `docs/proposals/` records) resolves to an existing file,
  directly or through the `docs/NOTES.md` / `docs/DECISIONS.md` stub.
- `docs/notes/index.md` lists all 23 section files; `docs/decisions/index.md` lists all 26
  decision files; `docs/progress/index.md` lists the 14 archived records in session order,
  one line per file; `docs/PROGRESS.md` holds only the current record.
- `HANDOFF.md`, `docs/ROADMAP.md`, `docs/OPERATING_MODEL.md` and `README.md` link to the new
  index paths, not to the old file paths, wherever they cited one.
- `python -m compileall -q plugin tests tasks.py`, `python -m pytest` and `python -m ruff
  check .` (sdlc.yaml commands) stay green, unchanged from before the split, since no file
  under `plugin/`, `template/` or `tests/` is edited.
- The owner has, in `docs/PROGRESS.md` (this change's own record, per "Things Claude gets
  wrong"), the exact `CLAUDE.md` guardrail edit: the table of link, row, current text, new
  text, covering line 3 (`docs/DECISIONS.md` mention), line 35 (`docs/NOTES.md`), line 39
  (`docs/PROGRESS.md`), and the new pointer line the proposal gives.
