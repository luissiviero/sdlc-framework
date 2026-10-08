# The owner's answers of 2026-10-08 (recorded by the PR-audit session)

On 2026-10-08, after the PR audit (`docs/handoffs/2026-10-08-pr-audit.md`), the owner accepted every recommendation the audit session gave. This file records the answers so the next session applies them. It touches no record another session is editing: the ROADMAP rows and the HANDOFF lines named below are the next session's to write.

## State at 16:18 UTC

- `main` is `3cd27b1`, the merge of **PR #118** (change 0002, the weekly scan's security finding): the owner's triage is **fix now** (gate (f), decision 25).
- Change 0002's design run started by itself on the merge: run 37807603086 (`sdlc-design.yml`, `pull_request` closed, created 16:17:19 UTC). It runs on the pin `v0.3.6`, so it is also the first live check of PR #130's push-check fix: its result JSON should carry `branch.branch` equal to the prepared branch and `owner_fields.ok: true` (`docs/progress/2026-10-08-runner-push-check.md`, the live check).
- `v0.3.6` is on `eca1af2`; the root pin reads 0.3.6 (`0672873`).
- PR #134 (session 22's record) is open; the owner has the prompt to resume it, which records R5's acceptance in ROADMAP.

## The answers

| Question | The owner's answer | What follows |
|---|---|---|
| **The `accept` verb** (HANDOFF item 4) | Yes: build it **after change 0002 and R5** | The proposal is `docs/proposals/accept-verb.md` (R6). The next session adds R6's row to `docs/ROADMAP.md`: status "accepted by the owner on 2026-10-08; after 0002 and R5". It needs a decision recorded before its intent (it adds an un-park verb to decision 24). |
| **The Windows items** (item 4): the sample's watch setting, the test-file lock seen live on Windows | Do both in one sitting with item 12's hook timing (R4) | The owner's acts, below. A session records the results in PROGRESS and NOTES when the owner reports them. |
| **The pin-bump trigger** (item 4; choice 116) | **No**: `sdlc-evals.yml` keeps its triggers; a pin bump is not evaluated on its own pull request | Choice 95 stands (no branch chooses the plugin that judges it). The evals run nightly after the merge, and R5's pin pull request is one line the owner reviews. Item 4's question is closed. |
| **Lessons shared across projects** (item 4; R1) | **Option 1 now** (nothing shared), **option 2 when a second project runs phase (f) live** (a lesson seen in two projects becomes a policy-skill rule through a plugin PR) | `docs/proposals/okf-adoption.md`, "Sharing lessons across projects". Option 3 (a shared lessons repository) stays unchosen; decisions 8 and 9 are unchanged. |
| **R2's edit tables** (item 5) | Apply them soon, in their smallest form: the SessionStart hook and its new file, `WebSearch` allowed, `WebFetch` kept on the deny list, and the "Tooling rules" section of `CLAUDE.md` | The owner's edit (guardrail files): `docs/proposals/session-tooling-pdf-web.md`, part (b). A session then verifies once that `Read` opens `docs/reference/ai-native-sdlc-playbook.pdf` and records it in NOTES section 15. |
| **The study** (item 8) | One study session once change 0002's design run is under way: record T32 (x-audit's option B), annotate T29's "Open" item with PR #130 (merged `4d8f267`, released in `v0.3.6`), decide x-roles, the last row | The study's own resume prompt is section 8 of `docs/reviews/2026-09-28-playbook-vs-framework.md`. With x-roles decided the study ends, and its confirmed entries become ROADMAP proposals (item 14). |
| **The failed digest run** 37785997563 | Not re-run | The scheduled run of 2026-10-09 at 06:17 UTC refreshes the issue. |
| **ROADMAP R5** (the pin-bump pull request) | Accepted | Recorded by session 22's prompt (ROADMAP R5's status); its intent follows change 0002. |
| **The version plan** | Option (a) | `v0.3.6` carries change 0003, PR #130 and PR #133; the carried gaps are 0.3.7 (`docs/handoffs/2026-10-08-pr-audit.md`, section 0). |

## The order of the work after today

1. Change 0002 through its phases, from the design run already started: the owner reviews gate (b) and later merges the build PR at gate (e).
2. R5, the pin-bump pull request, through the front door (its intent after 0002).
3. R6, the `accept` verb: its decision, then its intent.
4. The carried 0.3.7 gaps (session 20's three and session 21's), as a session finds them in its order.
5. In parallel, whenever the owner is free: R2's edit, the Windows sitting, one study session.
6. Fixed dates: the provocation on 2026-10-10 before 23:59 UTC; item 11 after the first scheduled detect run that follows it.

## The owner's Windows sitting (one sitting, all three)

1. **The hook timing (R4).** `docs/proposals/python-language-audit.md`, "The owner's check".
2. **The test-file lock.** On a fix-type change's branch, ask Claude Code to edit a test file. The edit should be denied with the "Test-file lock" message. Report the message or what happened instead.
3. **The sample's watch setting.** On `luissiviero/sdlc-sample-python`, Watch → "Participating and @mentions". This is a GitHub setting, not a write to the sample, so the freeze (precondition 6) does not forbid it.
