# Workflow comparison study (2026-09-28): the playbook and the framework compared; docs only, written against plugin 0.2.27

## Summary
- The owner asked whether the framework does what its workflow page draws and whether the page drawing the article's workflow matches the article, then for a step-by-step comparison of the two. The record is `docs/reviews/2026-09-28-playbook-vs-framework.md`, with its data and snapshots in the folder of the same name; `crosswalk.json` is the source of truth for the 47 compared steps.
- Both workflow pages were corrected and republished. The playbook page was faithful (no invented step); the framework page, a 0.2.19 snapshot, had two wrong edges (the runbooks behind `sdlc:go`, merging a parked PR) and is now drawn from the 0.2.27 code.
- Five framework issues filed from the study: #66 (a release can run twice, first on unreviewed code), #67 (change 0000 can get a design run), #68 (a parked build PR merged at (e) releases), #71 (`max_budget_usd` is compared per session, not per change), #72 ("transcript" is the run's final result).
- No code, template, decision or guardrail file changed. The owner's per-step decisions are open; the record's section 8 gives the prompt for a session that continues the study.
- Plugin 0.2.28 (session 12) landed while the study's pull request was open. It changes none of the 47 crosswalk rows, and it closes one documents-versus-code gap the record lists: `template/evals/README.md` no longer says a plugin-version change runs the evals (the record's section 5 notes this).

---
