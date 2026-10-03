# Review response — phase (e), round 1 (head `0f2b8d3447d2169313ac45599f6306a9fd3040d6`)

- **Important — `docs/notes/2.md:5` (and 28 of the other 31 `docs/notes/<N>.md` files): `verified_with` carries only the Claude Code version, never the plugin version or the runner, though spec.md Requirements line 11 asks for all three.**
  Partly fixed this round, left open overall. The phase (c)/(d) verifier already found and
  recorded this exact gap (`evidence/verifier.md`: "30 of 32 files carry only
  `Claude Code X.Y.Z` ... none carries a `runner` value") and judged it "a minor,
  mechanically-checkable documentation-metadata shortfall that nothing in
  `plugin/`/`tests/` reads today ... it should be noted for a follow-up fix" — a known,
  deliberately-deferred gap, not a regression this round introduced. The adversarial
  reviewer's verdict on this round's first attempt (escalate) pointed out, correctly, that
  the six files for `generated.at` 2026-10-02/10-03 (`docs/notes/27.md`–`32.md`, sessions
  15–18) have their plugin version stated directly and unambiguously in their own text
  (e.g. `32.md`: "The container (verified): the chained checks green on the 0.3.4 code")
  — so leaving even those untouched was not justified. Fixed now: `27.md` → "Claude Code
  2.1.287; plugin 0.3.0"; `28.md` → "Claude Code 2.1.287; plugin 0.3.1"; `29.md` → "Claude
  Code 2.1.288; plugin 0.3.1"; `30.md` → "Claude Code 2.1.288; plugin 0.3.2"; `31.md` →
  "Claude Code 2.1.288; plugin 0.3.3"; `32.md` → "Claude Code 2.1.288; plugin 0.3.4" (each
  plugin version taken from that session's own "built/lives/fix lives since <version>,
  read from the code written this session" sentence, i.e. the version the session's own
  fact was verified against, not the version at the session's start).
  A first attempt at this fix also set `30.md`–`32.md`'s runner to "a CI session", reading
  the GitHub Actions workflow-run details (job ids, `sandbox_applies: true`) these notes
  quote as proof of the note-writing session's own environment. A second, independent
  review pass on that attempt caught the conflation: those workflow-run details describe a
  *separate* thing each note is reporting on — change 0001's own automated, pinned-2.1.278
  build run, read from its job log — not the interactive 2.1.288 session that wrote the
  note. The same session's own "## Checks" section in `docs/PROGRESS.md` (session 18, each
  sitting) shows `compileall`/`pytest`/`ruff` run directly, with a literal `CHAIN EXIT 0`,
  which is how an interactive session reports its own commands, not how a CI session's
  deferred-to-the-runner mark reads — so the note-writing session is not itself the CI run
  it describes. The wrong "a CI session" value was removed before this round's commit, and
  sessions 15–18 (`27.md`–`32.md`) are treated alike: plugin version filled in, runner left
  out. None of the six states, in its own words, whether the session that wrote it ran on
  the owner's local machine or in a cloud session (checked directly in
  `docs/progress/session-{15,16,17}.md` and the matching parts of `docs/PROGRESS.md`); a
  CI-session identity is the one thing ruled out for all six, by the direct, non-deferred
  `CHAIN EXIT 0` evidence, but cloud versus local is not, so the runner field stays out
  rather than guessed.
  The remaining 26 files (sessions 1–14, `generated.at` 2026-09-19 through 2026-09-30) are
  left untouched: several of their dates each cover two to six different sittings with
  different plugin versions, so the date alone does not identify the session (the note's
  own title does); even once that correction is made, no file in that range states its own
  plugin version or runner in the same direct way sessions 15–18 do — reconstructing them
  would mean inferring from an indirect mechanism note (NOTES §16, about a cloud session's
  GitHub scope) rather than reading a direct citation. `verified_with` is the field a later
  session reads to decide whether a fact is stale (spec.md Requirements line 12-13); writing
  an inferred, unconfirmed value into it is worse than leaving the field incomplete, since it
  would read as settled provenance it is not.
  The owner can waive the remaining gap in a review comment (review: parked, so the gate's
  "findings" check is the owner's to settle), or ask for a follow-up change once sessions
  1–14's environment is identified from the owner's own memory of which ran locally versus
  in a cloud session.

- **Nits (4) — not fixed in this loop (article p.34: nits are listed, not fixed):**
  - `docs/PROGRESS.md:4` — the new top-level record's summary says "`docs/NOTES.md` (30
    sections)"; 32 section files are indexed. A wording slip in prose, not a structural
    defect; left for the owner to ask for by name.
  - `docs/PROGRESS.md:24` — the new record's guardrail table has 3 rows (CLAUDE.md lines 3,
    new-line-after-3, 35); spec.md's Acceptance text also names line 39, but line 39 needs
    no edit (unchanged, "docs/PROGRESS.md keeps its name and current-record role
    unstubbed" — stated in the record's own prose, just not as a fourth table row). Not
    fixed: adding a "no change" row would contradict the table's own "What it must become"
    column, which only ever lists an edit.
  - `docs/notes/1.md:3` — doubt about whether `sources` should also hold the verbatim quote;
    spec.md's Design section does not require the quote in frontmatter (quotes stay in the
    file body), so this is believed not to be a real gap; left as the reviewer's own stated
    doubt.
  - `docs/PROGRESS.md:1` — doubt about four top-level records instead of one "current"
    record; the reviewer's own note attributes the extra two (session 18, second and third
    sittings) to a later merge of `main` bringing in sessions this change's own commits
    never touched, not to this round's edit — already resolved reasoning, no action needed.

- **Important — `evidence/claude-md-proposals.md:2`: the second-occurrence framework rule
  (REVIEW.md) was triggered by the open `verified_with` gap recurring across review rounds,
  but a prior commit in this round left the proposals file untouched.**
  No action needed: `review/cli.py validate` (run as part of this round, after the fix
  above) regenerates `evidence/claude-md-proposals.md` itself from the current findings
  every time it runs — it is not a file this round edits by hand, and nothing is ever
  written to `CLAUDE.md` directly (protected path; the owner applies the line). The file
  now carries the proposed line for the recurring gap, written by that run.

No other Important finding stands. The previously-flagged splice (this change's own
`docs/PROGRESS.md` entry merged into an old, superseded record) was fixed this round —
see the commit-phase message — and the same review pass confirmed it independently.
