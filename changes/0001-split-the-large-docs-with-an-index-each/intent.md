# Intent: split the large docs with an index each
Author: Claude, drafted for Luis Siviero (owner). Status: draft. Change id: 0001. Entry route: idea.
Framework change: yes

## Problem
Every session in this repository is told to read three large files: `docs/NOTES.md` (1027 lines,
23 sections of platform facts), `docs/DECISIONS.md` (411 lines, the 26 settled decisions) and
`docs/PROGRESS.md` (1143 lines, fifteen session records, newest first). A session that needs one
platform fact or one decision reads a whole file, or reads a search hit without the context
around it. The cost is context space and attention, not money. Those are the limits that matter
for runs with a budget and a turn limit.

NOTES facts carry a read date, but nothing says when a fact is stale. Today the rule is "re-test
when the date is older than the environment's last change" (choice 93), and a session has to work
that out section by section.

This is step 2 of roadmap candidate R1 (`docs/proposals/okf-adoption.md`, "Context loading" and
"What it would take", step 2). The owner chose it as the first R1 step because it is
documentation only and does not touch the sample's live detection check before 2026-10-11.

## Proposed outcome
- `docs/notes/` holds one file per NOTES section. Each file name keeps the section number
  (for example `17-...md`), so every "NOTES §17" citation in code, tests and docs still points at
  one file. Each file has a short frontmatter: `title`, `sources` (the docs URL or run URL and the
  verbatim quote it already cites), `generated.at` (the read date already in the text) and
  `stale_after`. `docs/notes/index.md` lists every file with a one-line description.
- `docs/decisions/` holds one file per decision, named by its number. Each file has frontmatter
  with `status` (accepted or amended), `reversibility` (sticky or reversible, as the decision says
  today) and `amended_by` where an amendment exists. `docs/decisions/index.md` has one line per
  decision.
- `docs/PROGRESS.md` keeps the current session record only; earlier sessions move to
  `docs/progress/` (one file per session) with an `index.md`.
- Every move keeps the text unchanged (choice 126: a kept record is annotated, never rewritten).
  Only links and section references are updated.
- `HANDOFF.md`'s reading list says "index first, then the files you need".
- The old paths `docs/NOTES.md` and `docs/DECISIONS.md` become one-paragraph stubs that point to
  the new index, so old links and citations in closed PRs still resolve.
- The owner gets the guardrail edits as a table (link; row; what is there; what it must become):
  `CLAUDE.md` line 3 (the `docs/DECISIONS.md` path), line 35 (`docs/NOTES.md`), line 39
  (`docs/PROGRESS.md`), and the new pointer line after line 3 that the proposal gives.
- Checkable: every `NOTES §N` and `decision N` citation in `plugin/`, `template/`, `tests/`,
  `.github/` and `docs/` resolves to an existing file; the build, test and lint commands of
  `CLAUDE.md` stay green; no file under `plugin/` or `template/` changes, so there is no
  version bump.

## Affected users and systems
- The owner, who reviews and merges the split and makes the `CLAUDE.md` edits.
- Every later session in this repository: what it reads at the start changes.
- `docs/`: NOTES, DECISIONS, PROGRESS, HANDOFF, ROADMAP, OPERATING_MODEL, BUILD_GUIDE, README
  and the proposals, wherever they link to these files.
- Comments in about 48 files under `plugin/`, `tests/`, `template/` and `.github/` cite NOTES by
  section number. If the file names keep the numbers, those comments need no change.
- Not affected: the sample repository, its pinned `v0.2.29` framework, and its detection run of
  2026-10-11. The sample reads the framework at the pinned tag, never this repository's `main`.

## Constraints
- Documentation only. No change under `plugin/` or `template/`, so no version bump, no tag and
  no pin. If a code comment must change, it waits for the next plugin release instead.
- The text of a kept record is moved, never rewritten (choice 126). Each NOTES fact keeps its
  read date (choice 93).
- Split with the Edit tool, not a script: `CLAUDE.md` says the auto-mode classifier blocks a
  scripted rewrite whose payload reads like instructions.
- `CLAUDE.md` is a guardrail file. The session proposes its edits and the owner makes them, after
  the split merges.
- English only. No decision is reopened (decisions 8, 9, 17, 7 and 20 are unchanged, per the
  proposal's table).
- Do not merge it in a way that moves anything the sessions on the road to 1.0.0 (sessions 15 and
  16) are told to read, unless `HANDOFF.md` is updated in the same PR.

## Open questions
- `stale_after`: one fixed period for every platform fact (for example 30 days after the read
  date), or a date set per fact? Unknown — to be settled in design.
- PROGRESS: one file per session, or one file per session sitting (session 14 had two sittings,
  session 8 had two)?
- Timing: merge before session 15 (2026-10-11), or hold until after `v1.0.0` so sessions 15 and 16
  read the files they were briefed on?
- `docs/BUILD_GUIDE.md` (990 lines) is not in the proposal. Split it the same way, or leave it?
- Should the old-path stubs stay for good, or be removed after the next release?
