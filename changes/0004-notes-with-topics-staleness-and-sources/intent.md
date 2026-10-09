# Intent: notes with topics, staleness and sources
Author: Claude, drafted for Luis Siviero (owner). Status: draft. Change id: 0004. Entry route: idea.
Framework change: yes

## Problem
Change 0001 split `docs/NOTES.md` into `docs/notes/<N>.md` with an index, so that a session
reads the index and then only the note it needs. Three gaps keep that from working as intended.

- **The index does not say what a note holds.** A note is one session's batch of facts with one
  read date (choice 93), so its title names the session ("Facts read in session 9 (2026-09-26):
  …"), not the topics. To find the note that records how the sandbox treats `.env*` files, or
  which token a scheduled run uses, a session still opens notes one by one or searches the
  whole folder, which the split was meant to avoid. There are 36 notes on `main`, and every
  session adds one.
- **Nothing reads `stale_after`.** Every note carries it (`generated.at` plus 90 days), but no
  script or test compares it with today's date, and `docs/notes/index.md` is written by hand.
  The first notes pass their date on 2026-12-18. After that, a session has no way to tell a
  stale note from a current one without opening its frontmatter. The index's opening paragraph
  is also out of date: it still says everything was read on 2026-09-19.
- **Half the notes give no sources.** 19 of the 36 notes have `sources: null`, and the other 17
  hold one plain string. The body of each note already cites its sources (docs pages, run ids,
  PR numbers, API endpoints), but nothing a script can list or follow.

The Open Knowledge Format recommends exactly these three things: a `description` and `tags`
per file so an index can work as a table of contents, an expiry date that is a plain comparison,
and structured `sources`. This change is what remains of step 2 of roadmap candidate R1 (`docs/proposals/okf-adoption.md`, "What
it would take"): change 0001 did the split, and change 0003 applied the same ideas to
`lessons/`.

## Proposed outcome
- Every note's frontmatter gains `description` (one sentence naming the topics its facts cover)
  and `tags` (topics from one closed list, for example hooks, sandbox, permissions, auth,
  github-actions, rulesets, windows, plugin, sample, runs). The note's body is not changed.
- Every note's `sources` becomes a list of entries `{id, resource}` (with `title` where useful),
  one per docs page, run, PR or API endpoint its body already cites. This is the shape change
  0003 gave lessons. The entries restate what the body cites; the body is not reworded. A
  note whose facts were read from the session's own environment says so in an entry rather than
  carrying `null`.
- `docs/notes/index.md` has one writer: a `python tasks.py notes-index` task. The task rebuilds
  the index from the notes' frontmatter, grouped by tag, one line per note with its number, title
  and description. It appends `(stale)` to a line when the note's `stale_after` has passed. It
  also writes a fixed opening paragraph that states the staleness rule (choice 93, plus the
  90-day backstop) instead of the 2026-09-19 sentence. The index is never edited by hand.
- A test fails when the index on disk differs from what the task would write. The test also fails
  when a note lacks `description`, `tags` or `sources`, or carries a tag that is not on the
  list. A note passing its `stale_after` date is not a difference: the test compares
  everything except the `(stale)` markers, as 0003's `check` does, so CI never turns red because
  of the calendar.
- The index's fixed text keeps today's closing rule (sessions are append-only; read the latest
  note on a topic) and adds that a new note carries the three fields and that the index is
  regenerated in the same commit.
- Checkable: the task is idempotent; the index lists every `docs/notes/<N>.md` on `main` when
  the build runs, including notes added after this intent; `git diff` on the notes shows changes
  to frontmatter only; the build, test and lint commands of `CLAUDE.md` stay green on Windows
  and Linux.

## Affected users and systems
- Every later session in this repository: it reads a grouped index with descriptions and stale
  markers, and adds the three fields when it writes a note.
- The owner, who reviews the change and the tag list.
- `docs/notes/` (every note's frontmatter, the generated index), `tasks.py` and one new test
  under `tests/`.
- Not affected: `plugin/` and `template/` (no version bump, no tag, no pin), projects and the
  sample, `docs/decisions/` (its index lines already name each decision's topic) and
  `docs/progress/`.

## Constraints
- No change under `plugin/` or `template/`. If the task reuses the frontmatter reader of
  `plugin/lessons/index.py`, it imports it unchanged.
- The text of a kept note is never rewritten (choice 126); only its frontmatter grows. Each note
  keeps its read date and its `stale_after` (choice 93). The new fields describe a note; they
  never correct it. A correction still goes in a later note, as today.
- Python only, standard library, working on Windows and Linux (decision 7).
- Edit the notes with the Edit tool, not a script (`CLAUDE.md`, "Things Claude gets wrong").
  Only the generated index is written by the task.
- `CLAUDE.md` is not touched: its line 4 already points to `docs/notes/index.md`.
- Out of scope: OKF's required `type`, nesting `generated.at` as `generated: {at}`, a
  `status` or `deprecated` field for notes that later notes replace, any check of
  `verified_with` against the environment, the same treatment for `docs/decisions/`, and
  cross-project sharing (R1 step 4). Each can be its own change if wanted.
- No decision is reopened.

## Open questions
- The tag list: which topics, and how many. Change 0003's design parked at gate (b) on an
  undecided vocabulary, so the design pass proposes the list, with the notes each tag would
  cover, under Flagged concerns for the owner to settle.
- How the index groups a note with several tags: under its first tag only, as `lessons/index.md`
  does, or under each of its tags.
- Whether the task reuses `plugin/lessons/index.py` beyond its frontmatter reader, which
  already reads every note's frontmatter as it stands (checked on 17 and 30), or keeps its own
  rendering.
