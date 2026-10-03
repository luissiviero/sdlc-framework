# Decisions — accepted and applied in build guide v3

Companion to `BUILD_GUIDE.md`. Step numbers refer to that guide. The accepted alternative is marked **[ACCEPTED]**.

Decisions 21–26 were added on 2026-09-23 after the plan was audited against the owner's original objective and the article (session record: PR #22). The mechanism of 21 is the owner's, the rest are the session's suggestions adopted on the owner's instruction to proceed; all six were **confirmed on 2026-09-23** by the owner's merge of PR #22.

One file per decision, number only, no slug (`docs/decisions/<N>.md`); each carries `status`, `reversibility` and `amended_by` in its frontmatter.

1. [Where unattended claude -p runs execute and how they authenticate](1.md)
2. [Where plan.md is produced and approved](2.md)
3. [How you approve gates (c) and (d), which sit on one open PR](3.md)
4. [Branch rule that keeps the agent off main](4.md)
5. [Automation identity for non-interactive runs](5.md)
6. [Where the guardrails live so the agent cannot switch them off](6.md)
7. [Runtime for hooks, gate checks, detection scripts and eval checks (you are on Windows)](7.md)
8. [Framework distribution](8.md)
9. [Source of truth for artifacts and work items](9.md)
10. [Change folder and naming convention](10.md)
11. [What happens when a phase cannot finish on its own](11.md)
12. [Where the AI review pass runs](12.md)
13. [Shape of gate (e) — merge only, or merge + release authorization](13.md)
14. [Authorization model for 3σ runbooks in phase (f)](14.md)
15. [First metric to close the loop on](15.md)
16. [Recurring security scans](16.md)
17. [When to start evals and parallel worktrees](17.md)
18. [How many human gates per change — project and change profiles](18.md)
19. [What "deploy" and "maintain" mean for non-service projects](19.md)
20. [How finished work reaches you](20.md)
21. [Deferred review inside a phase — the owner reviews once, at the end (replaces the Lite profile)](21.md)
22. [How "ask for changes" runs by itself](22.md)
23. [Hosting scope: GitHub only](23.md)
24. [The owner's un-park verbs are labels](24.md)
25. [Gate (f) is per-finding triage; closing a PR at (a)–(e) abandons the change](25.md)
26. [Rollback authorization on a declared production (amends 14)](26.md)

Sticky decisions (2, 6, 7, 8, 10, 19) shape files and conventions every later step writes to.
