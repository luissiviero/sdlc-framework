# Starting prompt for R6's and R10's decision files (written 2026-10-13)

The text below is the prompt the owner gives a fresh session. It writes the two decisions that
must exist before the intents of roadmap candidates R6 (the accept verb) and R10 (the test loop
closes by itself in CI), plus T10's short proposal file, as one docs-only PR for one owner
review (the owner's choice of 2026-10-09). It builds nothing. It touches no file the item-11
session edits (`HANDOFF.md`, `docs/PROGRESS.md`, `docs/notes/`, `plugin/`), so it can run
before or in parallel with that session; it moves the paper ahead of R7 and R5 in the order on
the owner's word, without changing the build order.

````text
Work in luissiviero/sdlc-framework only. The sample (luissiviero/sdlc-sample-python) is out of
scope and frozen until the 1.0.0 read (choice 138); do not read or touch it.

Read first: CLAUDE.md, HANDOFF.md, docs/decisions/index.md, docs/decisions/24.md, 11.md, 21.md
and 27.md (27 is the newest decision and the layout to copy), docs/ROADMAP.md rows R6 and R10,
docs/proposals/accept-verb.md, docs/proposals/approvals-list.md (the proposal layout),
docs/reviews/2026-09-28-playbook-vs-framework/target-design.md section "T10", choice 154 in
docs/progress/session-18.md, and docs/handoffs/2026-10-13-study-line-start-table.md row 2d.
Expect main at or after bbdfbab (PR #160 merged).

## Goal
One docs-only draft PR to main that records R6's and R10's decisions before their intents, so
the owner reviews both in one sitting (the owner's choice of 2026-10-09, ROADMAP R6 and R10).
This PR moves the paper ahead of R7 and R5 in the build order on the owner's word; it builds
nothing and changes no build order.

## What to write
1. docs/decisions/28.md, R6, the accept verb (amends 24). Use 27.md's layout exactly:
   frontmatter (status, reversibility, amended_by), "## 28. <title> (amends 24)", the
   Reference line, the alternatives as bullets, "Accepted:", "Why:", "Decide by /
   reversibility:". Take the alternatives from accept-verb.md, including its three points
   under "To settle in the decision and the design" (gate (e) only or fix rounds too; whether
   an accepted finding still yields its CLAUDE.md proposal; the label name). Note that the
   label race R6's design depends on is fixed first by the 0.3.8 runs PR (choice 180).
2. docs/decisions/29.md, R10, the test loop closes by itself in CI (amends the decision and
   the choice R10's row names: 11 as amended by 21, and choice 154). Take the alternatives from
   target-design.md T10 and the R10 row: what dispatches the next fix round, what it carries as
   its constraint, how it counts against the iteration cap, where the change parks, and how
   the verifier names the tree it read.
3. docs/proposals/test-loop-closes-in-ci.md, T10's short proposal file "for uniformity"
   (start-table row 2d), in approvals-list.md's layout, restating only what target-design.md
   T10 and the R10 row already say. Never invent a mechanism the sources do not name.
4. Two index lines in docs/decisions/index.md, in the existing style.
5. docs/ROADMAP.md rows R6 and R10: append one annotation each in the row's *[...]* style,
   never rewrite the row.

## How the owner decides
- Write both files with `status: proposed`, every alternative listed, your recommendation
  marked **[RECOMMENDED]** with its reason, and "Accepted: pending the owner's review".
- In the PR body, give one table per decision: the question, the alternatives, your
  recommendation and why. The owner answers in a review on the PR.
- After the owner's answers, in the same PR: set `status: accepted`, mark the chosen
  alternative **[ACCEPTED]**, fill "Accepted:" and "Why:" from the owner's words, set
  `amended_by` in each amended decision's frontmatter (24 for R6; the one R10 amends), and
  update the two ROADMAP annotations. Never record an answer the owner did not give.

## Rules
- Docs only. No change under plugin/ or template/, no version bump, no intent, no change
  folder: an intent merge starts a phase (b) run by itself.
- Do not edit HANDOFF.md, docs/PROGRESS.md or docs/notes/: the item-11 session rewrites them
  on 2026-10-14. Put this session's record in the PR body; that session carries it forward.
- Never edit CLAUDE.md, REVIEW.md, sdlc.yaml or .claude/**. CLAUDE.md line 3 still says
  "the 26 settled choices"; give the owner the row for it as a table: link; row; what is
  there; what it must become (the count after this PR's decisions are accepted).
- Never reopen a settled decision; an amendment is written only because R6 and R10 were
  accepted by the owner (ROADMAP). If a source contradicts another, say so in the PR body and
  ask; do not pick.
- Edit docs with the Edit tool, sentence by sentence; cite the article by PDF page.
- Write "verified" only with a file, a run URL or command output.
- Before the PR, chained with set -o pipefail and all green:
  python -m compileall -q plugin tests tasks.py .github/scripts; python -m pytest;
  python -m ruff check .; python -m ruff format --check .
  Paste the output in the PR body. All three Framework checks jobs, Windows included, must be
  green on the final head before you tell the owner the PR is ready. Never merge.
- At the end, tell the owner the PR link, its status and the questions to answer, as a table.
````
