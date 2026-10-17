# Progress — the study's proposals R21 to R45, the pipeline's speed (decisions 30 to 33, R46 to R49), and R10 as plugin **1.0.3** (2026-10-15 to 2026-10-17)

This session ran on branch `ccr-01de3f80-ilnomi`, at the owner's word, from a question about when the plugin is ready for an outside project. The previous record, the item-11 follow-ups', is now `docs/progress/2026-10-17-item-11-follow-ups.md`, unchanged. Only `luissiviero/sdlc-framework` was changed; the sample was read, never touched. The session's own file is `docs/handoffs/sessions/2026-10-15-ccr-01de3f80-ilnomi.md`.

## Summary
- **R21** (the owner's request): desktop-only acts — say when the GitHub mobile app cannot do an act, and give the link (`docs/proposals/desktop-only-acts.md`).
- **R22 to R45**: one proposal for each of the study's 24 remaining confirmed entries, in the confirmed order. The order is the gate changes, then the roles (T1's two proposals, T2 inside the second), then the rest, with T4 last. Each was written by an Opus agent and checked by two independent agents, one for the owner's intent and one for the facts. Each finding was verified before it was applied. The proposals were then cross-checked against each other (53 findings) and given a last verify-and-fix round. The ROADMAP rows, the R numbers beside the entries and the record's annotations were added. PR #215, merged as `d54c35e`.
- **The decision table** (`docs/handoffs/2026-10-15-decision-table-r21-r45.md`): R21 to R45 accepted on 2026-10-16, with the owner's answers recorded in the ROADMAP and the session file.
- **The pipeline's speed.** The gate records showed 0.3 to 6.4 model hours per change against 1.8 to 7.4 days elapsed. The owner approved the table of what made it slow. That gave decisions 30 to 33:
  - 30, the fast lane (amends 2 and 18);
  - 31, a review request when a PR waits for the owner (amends 11 and 20);
  - 32, deferred review and higher build caps by default (amends 21);
  - 33, a GitHub App identity (amends 5).

  Their candidates are R46 to R49 (`docs/proposals/pipeline-speed.md`). Framework candidates are now built as session PRs with an independent review, not through the framework's own pipeline. The ROADMAP Order was rewritten with the pipeline sprint first. The owner's `CLAUDE.md` rows for decision 31 and the count of 33 decisions went in through PR #219.
- **R10, plugin 1.0.3.** A red target found by the runner starts the next fix round by itself. At the cap, a read-only agent in a fresh context may reset the count once per change; the owner chose on 2026-10-17 that R10 builds it. An infrastructure failure gets one re-run, then parks. A missing target parks at once. The verifier names the record it read. It was built by an Opus agent and reviewed independently twice (9 findings, then 4, all verified and fixed or rejected with a reason). PR #220, merged as `571bc22`; `v1.0.3` is on it.

## The owner's decisions (2026-10-15 to 2026-10-17)
- Only the study's entries go onto the ROADMAP; the carried small items wait. One PR for R22 to R45, one commit per batch. Opus writes the proposals; Fable and Opus review them (from 2026-10-15 Opus only, at the owner's word).
- R21 to R45 accepted, with the recommendations of the decision table. The trial project starts after a short core, not after all of wave 1.
- The pipeline-speed table approved in full (decisions 30 to 33, R46 to R49), the pipeline sprint first.
- R10 builds decision 29's reset. R17 moves to 2nd in the sprint, because R46 and R47 need its owner check. The sprint is R10, R17, R46, R47, R48, R49.

## Checks (this repository)
On PR #220's final head `bc2cb6e`: `compileall` clean, `ruff check` "All checks passed!", `ruff format --check` "209 files already formatted", `pytest` "1742 passed in 791.44s". All `Framework checks` jobs (Linux 3.10 and 3.12, Windows) and the evals were green.

## Left
- **Next: R17**, then R46, R47, R48 and R49, each a session PR with an independent review and the next free patch version. The starting prompt is `docs/handoffs/2026-10-17-pipeline-sprint-prompt.md`.
- **Not verified live:**
  - R10's real judge call and real dispatch;
  - that a job skipped by its `if` never enters its concurrency group.

  The first red target on the sample or the trial project shows them.
- **Left out of R10 by its review:**
  - a check of the runner's reset against the Actions API;
  - re-running only the targets that did not start after a crash.
- **The owner's open answers:** R28's timing and cost; R44's timing.
