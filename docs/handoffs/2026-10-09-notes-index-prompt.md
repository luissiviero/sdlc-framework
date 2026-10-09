# Starting prompt for the notes index work (written 2026-10-09)

The text below is the prompt the owner gives a fresh session. It does what is left of roadmap
candidate R1 on `docs/notes/`: a description and tags per note with a generated index, the
stale marker, and structured sources. The work goes as a plain PR with no change id (the
owner's choice; the withdrawn intent is PR #148, commit `c5a7d6d`). It can run in parallel
with change 0002: 0002's plan changes hooks, CI settings and their tests, never `docs/notes/`.

````text
Work in luissiviero/sdlc-framework. This is a plain PR with no change id: it does not go
through /sdlc-plan or changes/<id>-<slug>/ (the owner's choice; it ships nothing to projects).

## Goal
Sessions spend less context and get fewer facts wrong, because they find the one note they
need, see whether it is still current, and see what it was checked against. Do the three
things below for docs/notes/ (the platform facts that change 0001 split out of NOTES.md).

## Read first
- CLAUDE.md, then docs/notes/index.md and three notes of different ages (1.md, 17.md, 30.md).
- The withdrawn intent for this work, for the reasoning (do not create its folder):
  `git fetch origin pull/148/head && git show c5a7d6d:changes/0004-notes-with-topics-staleness-and-sources/intent.md`
- plugin/lessons/index.py (change 0003): its read_frontmatter and is_stale, and how its
  `check` ignores the (stale) markers.

## Decisions (the owner's, already made)
1. Tags: a closed list. Start from: hooks, permissions, sandbox, auth, github-actions,
   github-api, rulesets, windows, plugin-release, sample-runs. After reading all the notes
   you may add, drop or rename tags; list every change from this list, with the reason, in
   the PR body for the owner.
2. Index grouping: a note appears under every tag it carries (one section per tag, in the
   order of the list; inside a section, ascending note number).
3. Reuse: import read_frontmatter and is_stale from plugin/lessons/index.py unchanged; write
   the notes index layout yourself. No change under plugin/ or template/ (no version bump).

## What to build
1. Frontmatter on every docs/notes/<N>.md (all notes on main when you start, plus any that
   land before you merge): add `description` (one sentence naming the topics its facts
   cover) and `tags` (from the list). Replace `sources` (today null or one string) with a
   list of {id, resource} entries, plus title where useful: one per docs page, run, PR or
   API endpoint the note's body already cites. Restate only what the body cites; never
   invent a source. A note whose facts come from the session's own environment gets an
   entry that says so, not null. Keep title, generated.at, verified_with and stale_after
   exactly as they are.
2. A `python tasks.py notes-index` task (in tasks.py itself: the build check compiles only
   plugin, tests and tasks.py) that rewrites docs/notes/index.md from the notes'
   frontmatter. The index:
   - opens with a fixed paragraph: what a note is (one session's batch of facts with one
     read date); the staleness rule (stale when the environment no longer matches
     verified_with, or when stale_after has passed, whichever comes first); the tag list;
     that the index is generated, never edited by hand; and that a new note carries
     description, tags and sources and is added by running the task in the same commit.
     Keep today's closing rule (sessions are append-only; read the latest note on a topic
     before relying on an earlier one).
   - has one line per note under each of its tags: `N. [title](N.md) — description`, with
     ` (stale)` appended when stale_after is before today (UTC date).
   - is written with "\n" line endings and UTF-8 on every OS (the owner works on Windows).
   - Running the task twice gives the same file.
3. tests/test_notes_index.py. It fails when:
   - docs/notes/index.md differs from what the task would write, comparing everything
     except the (stale) markers, so a date passing never turns CI red;
   - a note lacks description, tags or a non-empty sources list;
   - a note carries a tag that is not on the list;
   - a sources entry has no resource.
   Plus unit tests of the layout on a small fixture folder: grouping under several tags,
   the stale marker against a fixed "today", and idempotence.
4. docs/ROADMAP.md, row R1: append an annotation in the row's existing *[...]* style (never
   rewrite the row): the platform notes' topics, stale marker and sources were done outside
   the front door by the owner's choice, PR #<n>.

## Rules
- Edit each note with the Edit tool, frontmatter only. `git diff` on docs/notes/<N>.md must
  show frontmatter lines only (choice 126: a kept record is never rewritten; choice 93: each
  note keeps its read date). Only index.md is written by the task.
- Never edit CLAUDE.md, .claude/**, REVIEW.md or sdlc.yaml. If one needs a change, give the
  owner a table: link, row, what is there now, what it must become.
- Python standard library only; it must work on Windows and Linux.
- Out of scope: a `type` field, nesting generated.at, a status/deprecated field,
  checking verified_with against the environment, docs/decisions/, lessons/.
- Change 0002 runs in parallel and its sessions add notes. Before opening the PR, and again
  before asking for the merge: merge main, give any new note the three fields, and rerun
  the task. Never hand-merge index.md.

## Done when
- `python -m compileall -q plugin tests tasks.py` prints nothing and exits 0;
  `python -m pytest` is all green; `python -m ruff check .` and `ruff format --check .`
  are clean. Paste the output in the PR body.
- `python tasks.py notes-index` leaves no diff on a clean checkout.
- A draft PR to main, with: what changed, the final tag list (and changes from the starting
  list), how many notes had sources: null before and none after, and which notes (if any)
  the index marks stale today.
````
