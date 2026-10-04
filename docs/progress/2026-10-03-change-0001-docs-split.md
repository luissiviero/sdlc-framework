# Change 0001 (2026-10-03, session 18): the docs split — `docs/NOTES.md`, `docs/DECISIONS.md` and `docs/PROGRESS.md`'s archived records each moved to a file per section/decision/record with an index; docs only, no bump

## Summary
- `docs/NOTES.md` (32 sections), `docs/DECISIONS.md` (26 decisions) and `docs/PROGRESS.md`'s 21
  then-archived records (everything but the then-current record) each moved to one file per
  section/decision/record, number- or heading-named, under `docs/notes/`, `docs/decisions/`
  and `docs/progress/` respectively, with an `index.md` each in ascending order (the study
  record keeping its place between sessions 12 and 13). `docs/NOTES.md` and `docs/DECISIONS.md`
  are now short stubs pointing at their index; `docs/PROGRESS.md` keeps its name and
  current-record role unstubbed. `HANDOFF.md`'s "Read in this order", `docs/ROADMAP.md`,
  `docs/OPERATING_MODEL.md` and `README.md` are repointed to the new indexes wherever they
  named one of the split files; `docs/PROGRESS.md` mentions were left as is. Every moved
  record's text is unchanged (choice 126); the splitting tool-calls used Read/Write, never a
  script, per "Things Claude gets wrong". No file under `plugin/`, `template/` or `tests/`
  changed, so no version bump; build/test/lint deferred to the runner as in every CI session
  (issue #91). The owner's `CLAUDE.md` guardrail edits that this split needs are below. One
  guardrail line this split touches needs no edit: `CLAUDE.md` line 39 ("propose the exact
  lines in docs/PROGRESS.md and leave the edit to the owner") still holds, since
  `docs/PROGRESS.md` keeps its name and current-record role unstubbed.

## Guardrail lines for the owner (this session cannot edit these files)
| Link | Row | What is there now | What it must become |
|---|---|---|---|
| [CLAUDE.md](../CLAUDE.md) | line 3 | `...` is the build plan; `` `docs/DECISIONS.md` `` records the 26 settled choices — do not reopen them without asking. `docs/ROADMAP.md` is what comes after Milestone 1: ... | same sentence with `` `docs/DECISIONS.md` `` replaced by `` `docs/decisions/index.md` `` |
| [CLAUDE.md](../CLAUDE.md) | new line after line 3 (line 4 is blank today) | — | Insert: "Indexes first: `docs/notes/index.md` lists every verified platform fact, `docs/decisions/index.md` every settled decision; read the index, then only the files you need." (`docs/proposals/okf-adoption.md`'s table, "Point to the indexes from `CLAUDE.md`") |
| [CLAUDE.md](../CLAUDE.md) | line 35 | `- Verify how Claude Code on Windows invokes hook commands before writing the first hook; record the answer in `` `docs/NOTES.md` ``.` | same sentence with `` `docs/NOTES.md` `` replaced by `` `docs/notes/1.md` `` (NOTES §1 is that exact fact) |
