---
type: Proposal
title: The docs lint, part 2 — the cross-file facts a script can check, so the docs consistency review's mechanical classes cannot come back
description: Six deterministic checks added to python tasks.py docs-lint (decision amendments, proposal status against ROADMAP, built rows under Done, version and PR pairs against the tags, the moved stubs, a Portuguese word list), and one rule that proposals stop restating ROADMAP's status and order.
status: accepted
roadmap: R58
sources:
  - id: review
    resource: docs/reviews/2026-10-19-docs-consistency.md
    title: "The docs consistency review of 2026-10-19: 148 rows after six were withdrawn"
  - id: owner
    resource: "the owner's answer of 2026-10-20 in session ccr-e8220c2e-ya26hb ('go with your recommendations'), to the question whether these errors can be stopped without spending many tokens or much time"
    title: "The request and the acceptance"
  - id: lint
    resource: tasks.py lint_docs, tests/test_docs_lint.py test_the_repository_docs_pass_the_lint
    title: "The docs lint of R55, run by the test suite in every framework-checks job"
generated: { by: sdlc-framework-session/ccr-e8220c2e-ya26hb, at: 2026-10-20T12:00:00Z }
---

# The docs lint, part 2

**Status: accepted by the owner on 2026-10-20 (ROADMAP R58).** Nothing is built. Like R55, it is a documentation and tasks PR outside the ranks, with no plugin version.

## Why

The consistency review of 2026-10-19 cost about four million subagent tokens to find 148 rows. About half of them belong to classes a script can find in well under a second: a decision amended without its `amended_by`, a proposal still `proposed` after ROADMAP accepted it, a built candidate left in the candidates table, a version paired with the wrong PR. The docs lint already runs inside the test suite (`test_the_repository_docs_pass_the_lint`), so every check added to it is enforced on every pull request at no model cost.

## The rule

ROADMAP's Status and Order columns are the one place a candidate's state and rank are read (the owner's rule of 2026-10-14 for the Order column, ArtCraft row A4, extended to the Status column). A proposal keeps its `status` frontmatter only as a copy the lint checks, and states no rank: where its order matters it names the candidates it depends on, never a rank or "last". About 60 of the review's 81 roadmap-mismatch rows were proposals restating what ROADMAP later changed.

## The checks (each a failure unless marked a report line)

| # | Check | The review's rows it would have caught |
|---|---|---|
| 1 | A decision whose heading says `(amends N)` is listed in decision N's `amended_by`; `status` is `amended` exactly when `amended_by` is set (change 0001's spec) | 13 |
| 2 | A proposal's `status` agrees with the Status column of the ROADMAP row its `roadmap` field names (`accepted` when that column records an acceptance) | about 36 |
| 3 | A ROADMAP row whose Status says "built as plugin" or "built in PR" sits under a "Done" heading (the page's own rule) | 7 |
| 4 | Every "plugin X.Y.Z … PR #N" or "`vX.Y.Z` … PR #N" pair matches the tag's merge commit; a report line, not a failure, when the checkout has no tags (the Linux framework-checks job gets `fetch-depth: 0`) | a few |
| 5 | No citation of the moved stubs `docs/NOTES.md` or `docs/DECISIONS.md` as a source | 1 |
| 6 | A short list of Portuguese words finds nothing outside `docs/reference/` (proper nouns such as São Paulo are listed as allowed) | 0 today |

Each check has a test in `tests/test_docs_lint.py` on a temporary tree, as R55's checks do.

## What it does not catch

Whether a sentence means what its citation says — the wrong decision or note cited, a date or a time that disagrees with another record — needs a reader. That stays with an occasional full sweep, at a milestone, not on every pull request.

## Order

After the review's own fixes land (the rows held for open pull requests on `docs/ROADMAP.md` and `docs/proposals/reviewer-on-opus.md` included), so checks 2 and 3 pass on the first run.
