# Notes — platform facts verified against the Claude Code docs

Everything here was read on 2026-09-19 from the official docs at `code.claude.com/docs`
(and the pages named). Quotes are verbatim. Re-verify when the plugin's minimum Claude Code
version moves; the container that built session 1 ran Claude Code 2.1.278.

One file per NOTES section, number only, no slug (`docs/notes/<N>.md`); each carries `title`,
`sources`, `generated.at`, `verified_with` and `stale_after` in its frontmatter.

1. [How Claude Code on Windows invokes hook commands (handoff deliverable 3; decision 7)](1.md)
2. [Does the current documentation allow CI authentication with a Max subscription? (decision 1)](2.md)
3. [Where the framework runs: owner's PC and Claude Code cloud sessions](3.md)
4. [The managed-settings keys and what they do to decision 6](4.md)
5. [Sandbox](5.md)
6. [Permission rule facts the template depends on](6.md)
7. [Plugin distribution facts](7.md)
8. [Hook output contract (checked against the decision-control table)](8.md)
9. [Known gaps carried to B2/B3](9.md)
10. [Facts added in session 2 (B2), read on 2026-09-21](10.md)
11. [Facts added in session 3 (B3), read on 2026-09-21](11.md)
12. [The always-protected patterns are anchored to the project root (plugin 0.2.10, 2026-09-23)](12.md)
13. [Facts added in session 5 (B5), read on 2026-09-25](13.md)
14. [Facts from the live phase (f) runs (session 6, 2026-09-25)](14.md)
15. [Facts read in session 7 (2026-09-25): the session's own environment and the sample's CI history](15.md)
16. [Facts read in session 8 (2026-09-26): the session's repository scope, git's ref resolution, the runner's shell](16.md)
17. [Facts read in session 9 (2026-09-26): the readiness review's environment, GitHub's branch protection, the console encoding](17.md)
18. [Facts read for session 10 (2026-09-28): the sample's schedule and the tag](18.md)
19. [Facts read in session 11 (2026-09-28): the sample under both repositories, the weekly scan's first framework finding](19.md)
20. [Facts read in session 12 (2026-09-28): the sample's points, the eval case run live, the GitHub actions' majors](20.md)
21. [Facts read in session 13 (2026-09-29): the sample's points, the article's p.40 steps, the gate's artifact reads](21.md)
22. [Facts read in session 14, first sitting (2026-09-29): the sample's points, the auto-mode classifier on a `git rm`, the clones' refs](22.md)
23. [Facts read in session 14, second sitting (2026-09-29 to 2026-09-30): the sample's points, the classifier in the default mode, the 0.2.28 copies live](23.md)
24. [Facts read on 2026-10-02 (between sessions 14 and 15): the sample's points, change 0001's first design run on this repository](24.md)
25. [Facts read for plugin 0.2.30 (2026-10-02): the review panel's enforcement](25.md)
26. [Facts read on 2026-10-02 (second sitting, between sessions 14 and 15): the sample's live check is isolated by its pin; what the judging run reads across runs](26.md)
27. [Facts read in session 15 (2026-10-02): the sample's points, issue #91 reproduced in the container, where the gate's commands run since 0.3.0](27.md)
28. [Facts read in session 16 (2026-10-02): the sample's points, PR #98's merged head, where the release record lives since 0.3.1](28.md)
29. [Facts read in session 17 (2026-10-02): the sample's points, the first live fix round on 0.3.1 — the runner's commands step proven inside a real sandboxed run, GitHub's rule on the owner's own pull request](29.md)
30. [Facts read in session 18 (2026-10-03): the sample's points, PR #105's merged head, where the evidence logs and the verifier's verdict come from since 0.3.2](30.md)
31. [Facts read in session 18, second sitting (2026-10-03): 0.3.2 merged, tagged and pinned; PR #90 merged; change 0001's first build run terminated waiting for background sub-agents](31.md)
32. [Facts read in session 18, third sitting (2026-10-03): 0.3.3 merged, tagged and pinned; change 0001's build run on 0.3.3 — the foreground rule and item 3b verified live at (c); the park on the sandbox-masked fixture `.env`](32.md)
33. [Facts read in session 19 (2026-10-04): change 0001's fix round on 0.3.4, phase (d), the (e) run and its fix rounds, the owner's merge and the release — item 3b verified live at (d); the (e) rounds parked on `changes/.review-seen.json`](33.md)
34. [Facts read in session 20 (2026-10-06 to 2026-10-07): the sample's points, change 0003 through the front door on plugin 0.3.5 — the intent PR by the API route, the design run started by the merge, gate (b) parked on one flagged concern; the scan's change 0002 (PR #118); GitHub's 500 on every review creation for PR #124](34.md)
35. [Facts read in session 21 (2026-10-07 to 2026-10-08): the sample's points, change 0003's two fix rounds on plugin 0.3.5 — the owner's twenty-item and seventeen-item reviews applied, PR #124 merged; the build run on the 200-turn cap, the re-run's preflight park on a red test, PR #132](35.md)

Sessions are append-only: a later session's file may correct or supersede an earlier one's
reading (each says so inline, e.g. "corrected by §17"); read the latest file on a topic
before relying on an earlier one.
