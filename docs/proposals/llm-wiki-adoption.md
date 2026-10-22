---
type: Proposal
title: The LLM wiki pattern in the framework and in the projects it drives
description: Karpathy's LLM wiki (raw sources, compiled pages, a schema; ingest, query, lint; an index read first) checked against the framework at main 209325f to 2a2a9b2; three new candidates (a docs lint, lessons read at design, system pages), three annotations (R2, R42, R45) and what is deliberately not built.
status: accepted
roadmap: [R55, R56, R57]
sources:
  - id: crosswalk
    resource: "https://claude.ai/artifact/CM4NBjyjRWTQ9tBb9dszP4"
    title: "LLM Wiki Crosswalk, the owner's artifact read at main 230a53c (plugin 1.0.10); its row numbers and ranks predate choice 234"
  - id: owner
    resource: "the owner's messages of 2026-10-19, session claude/llm-wiki-sdlc-framework-g10zr0 ('All of them as recommended')"
    title: "Choice 236: the session's 22 recommendations accepted"
  - id: okf
    resource: docs/proposals/okf-adoption.md
    title: "R1, the same shape as a file format; its row 17 and its 'Sharing lessons across projects' section"
  - id: r2
    resource: docs/proposals/session-tooling-pdf-web.md
    title: "R2, 'The OKF reading: mirror once, read files' (in a project: references/<slug>.md)"
  - id: change-0001
    resource: changes/0001-split-the-large-docs-with-an-index-each/spec.md
    title: "The owner's ruling on verified_with (PR #112 review, fix round 4)"
  - id: notes-49
    resource: docs/notes/49.md
    title: "Three fix rounds spent on a stale test count in the sample's CLAUDE.md, a file no run can edit"
  - id: article
    resource: docs/reference/ (PDF p.19-20, p.25, p.49)
    title: "CLAUDE.md as the project's memory; the researcher sub-agent; the lessons file future investigations read"
generated: { by: sdlc-framework-session/claude-llm-wiki-sdlc-framework-g10zr0, at: 2026-10-19T19:00:00Z }
---

# The LLM wiki pattern in the framework and in the projects it drives

**Status: accepted by the owner on 2026-10-19 (choice 236), every recommendation as written below.** It adds ROADMAP R55, R56 and R57, annotates R2, R42 and R45, and moves no existing rank.

## The pattern, and where the framework stands

Andrej Karpathy's "LLM wiki" (April 2026) has an agent compile raw sources into persistent markdown pages and keep them current, so knowledge compounds instead of being rediscovered on every question. It has three layers (immutable raw sources, the compiled pages, a schema file such as `CLAUDE.md`) and three operations (ingest, query, lint), with an index read first and a log of changes. R1's OKF proposal already cites it as evidence for the index-first shape (`okf-adoption.md`, the table of evidence).

**Inside this repository the pattern is mostly in place:** `docs/reference/` is the untouched source, `docs/notes/` and `docs/decisions/` are frontmatter pages, the notes index is generated and read first, and `docs/PROGRESS.md` with `docs/progress/` is the log. What is missing is lint.

**In a project the framework drives, only incidents compound:** `lessons/` has frontmatter, a generated index and a gate (e) check, and the maintain run reads it (p.49). An ordinary change leaves no "how the system works now" page: `spec.md` and `plan.md` stay inside each change folder, and `CLAUDE.md`'s Architecture section is filled once by `/sdlc-init` and then never updated, because `CLAUDE.md` is a guardrail no run may edit. The design run never reads `lessons/`.

## R55: the docs lint (this repository)

A `python tasks.py docs-lint` task with tests, outside `plugin/` and `template/`, so no version bump. It reports four things:

1. **Broken relative links under `docs/`.** A scan at `209325f` found 43 of 367 relative links broken, most of them in `docs/progress/` after change 0001's split. The task reports only until a clean-up PR fixes the existing breaks; the test then turns it into a failure, in that same PR. *[2026-10-19, choice 237: most breaks sit in kept records, which choice 126 forbids rewriting; they stay as written, listed in `docs/links-baseline.txt`, and the lint fails on any other break from the start. With code spans and fenced blocks skipped the 43 are 21: 20 in `docs/progress/`, written as `docs/PROGRESS.md`, and one in R2's edit table, a file R2 creates.]*
2. **The Claude Code version of each note.** The lint reads "Claude Code X.Y.Z" out of the existing free-text `verified_with`, which the owner's ruling in change 0001 keeps as text (`spec.md`, "decided (owner, PR #112 review 2026-10-03, fix round 4)"); the field is not restructured. It compares that version with the pin the jobs install, `CLAUDE_CODE_VERSION` in `plugin/init/sdlc_init.py`, and lists every note read on another version, newer or older: a fact seen on 2.1.296 in a cloud container is not proven on the 2.1.278 the runs install. Notes that name no Claude Code version (12 and 43 to 49 at `2a2a9b2`) are listed too; the next notes session fills each one in with the Edit tool, or writes "no Claude Code fact" where the note holds only GitHub or git facts. *[2026-10-19, choice 237: not filled in; notes are append-only and the version they were read on was not recorded, so the lint only reports them; a note after 49 names a version or says "no Claude Code fact", and the lint fails when it does neither.]*
3. **Superseded notes.** An optional `supersedes` field on a note (the name lessons already use) makes the existing "corrected by §17" convention checkable: the target must exist, and the index shows "(superseded by N)" beside the older note, so the current fact is one read.
4. **A generated decisions index.** `python tasks.py decisions-index` writes `docs/decisions/index.md` from each decision file's heading and frontmatter, keeping the page's introduction, and a test fails on drift, as for the notes index. R27 and R28 are about to add decision files.

Contradiction detection is not built: it is a model's judgment, not a deterministic check.

## R56: the design run reads the lessons (plugin)

1. **Phase (b) reads `lessons/index.md`.** The spec pass and the planning run of `/sdlc-design` read the index the way `/sdlc-maintain` step 1.2 does (`plugin/lessons/index.py check` first, every file on a stale or missing index). On an empty `lessons/` (every new project) the read costs nothing. `/sdlc-plan` (phase (a)) is unchanged: the files a change touches are not known before the plan.
2. **A lesson names the files its fix touched.** Lesson tags are a class, a metric and a runbook name, not code areas, so matching a change to a lesson by tag mostly misses. `/sdlc-deploy` step 0b gains an optional `files` field, read from the fix PR's diff against the default branch (every path outside `changes/`, `lessons/` and `evals/`), so it is read from a source, never typed in. `index.py build` prints it in the lesson's index line.
3. **The plan cites the lessons it matched.** After the planning run lists "Files that change", it opens every lesson whose `files` intersect that list and every lesson whose tags name the change's area, and names each one under Risks with what it changes in the plan. A later step may show the match in the gate (b) banner; not this row.
4. **Gate (e) keeps R1's design.** `files` is optional, `LESSON_REQUIRED_FIELDS` is unchanged, and no existing lesson needs an edit. The field name is a placeholder until R45 judges it. *[2026-10-19, choice 237: settled in R56's own PR instead, before any lesson in any project carries it, as R11's keys were.]*

Touches `plugin/commands/sdlc-design.md`, `plugin/commands/sdlc-deploy.md` step 0b, `plugin/lessons/index.py`, `template/lessons/README.md` and their tests; a plugin version. R54, R27 and R28 also edit `sdlc-design.md`: the overlap is textual, and whichever ships second merges.

## R57: system pages, a compiled project wiki (plugin; proposal now, build after the trial)

1. **Where they live.** A project folder of pages, `system/` as a placeholder name until R45, one page per module with an "Invariants" section, and a generated `system/index.md` (build and check, as `lessons/index.md`). Frontmatter: `type: SystemPage`, `title`, `description`, `covers` (the paths and globs the page describes), `sources` (the change ids that wrote it) and `generated`. Not a guardrail: runs write it, the owner reviews it.
2. **Read first at (b).** The spec pass and the planning run read the index and the pages whose `covers` match before delegating to the researcher sub-agent (p.25 step 4), which reads the index first too.
3. **Written at (c), in the build diff.** The build run knows what it changed, and the owner reviews the pages with the code at gate (e). The planning run lists the pages under "Files that change", or gate (c)'s plan-sync check parks the run.
4. **Started lazily.** A page is created the first time a change touches its module, from what the planning run's researcher reported. `/sdlc-init` seeds nothing: a bulk-generated wiki in the change-0000 PR would be a large unchecked review.
5. **Kept honest by a check.** A pull request that changes files a page `covers` without touching that page gets a warning line in its banner, never a park. A stale page is worse than none, because runs trust it over the code.
6. **`CLAUDE.md` stays the owner's.** Its Architecture section stays short and owner-written, with one line pointing at `system/index.md` (in `template/CLAUDE.md`). Routing architecture updates through R37's standing PR is not proposed: R37's step runs no model, and these updates need one.

**Why after the trial.** It is a cost and context saving, and the trial measures it: researcher calls, turns and tokens per design run, the warning lines raised, and review findings that cite a page wrongly. The owner places its rank from those measures. Evidence it pays: NOTES §49, where the review pass spent three fix rounds on a stale test count in the sample's `CLAUDE.md`, a fact no run can update. The candidate in that session's file, "park at once on findings no session can fix", complements this row: system pages reduce such findings, the park stops the waste when one occurs.

Related: R28's Architect reads the pages; R30's list of what starts empty gains the folder; R45 judges the names.

## Annotations to existing rows

- **R2:** in a project, `references/` (R2 item 1) is read by the runs and never written by them, a guardrail path like R27's `policies/`. That amends decision 6, so its decision file comes before the intent, as R27's did. Not a new row. *[2026-10-19, choice 237: after R27's decision file, which amends the same list first.]*
- **R42:** a lesson past its `stale_after` is listed in the daily digest for the owner to refresh or retire: a digest line, no notification (decision 20).
- **R45:** the names to judge gain R56's lesson field `files`, R57's folder, its index and frontmatter keys, and R2's project `references/`.

## Not built

- **One consolidated page per notes topic:** a large rewrite that loses the dated record; `supersedes` gives most of the value.
- **Cross-links as a graph and a graph viewer:** `docs/` is plain markdown and opens as an Obsidian vault as it is.
- **A separate log file:** `docs/PROGRESS.md`, `docs/progress/` and R9 part 1's `changes/index.md` are the log.
- **A shared lessons store across projects:** it stays R1's steps 3 and 4, blocked on decision 9 and on a second live project.

## Order

R55 first, a documentation and tasks PR. R56 after choice 235's second step and the sample's next change, so the plugin version does not move under either; no rank moves. R57's proposal is this file; its build waits for the real-project trial (after R28) *[2026-10-22, R65's part 3 (docs-lint check 11): "after R28, rank 19" stood here; ROADMAP's Order column holds the rank]* and its rank is the owner's, placed from the trial's measures. *[2026-10-19, choice 237: and after R45 (rank 20), so its names are not changed twice.]* *[2026-10-19, choice 238: the trial now comes after R45 (rank 20); R28 moved after it, to rank 21.]* Before writing a row number, a session checks that R55 to R57 are still free.

## Decisions it touches

6 (amended by R2's annotation, at R2's build, with its own decision file); 2, 17 and 20 kept; R1's lesson design (change 0003) kept, with one optional field.
