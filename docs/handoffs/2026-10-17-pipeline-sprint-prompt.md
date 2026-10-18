# Session prompt: the pipeline sprint, from R17 (2026-10-17)

Written by the session on branch `ccr-01de3f80-ilnomi` at its close, after R10 merged as plugin 1.0.3 (PR #220). Paste everything below the line into a new session started with `luissiviero/sdlc-framework` in scope.

---

This session builds the rest of the pipeline sprint, one session PR per candidate, in ROADMAP's Order: **R17, R46, R47, R48, R49**. Start with R17 and stop after each PR for my merge unless I say to go on. *[2026-10-18, session `ccr-4900ade8-1qc1s9`: R17 is built as plugin 1.0.5 (PR #227) and R46 as plugin 1.0.6 (PR #228); start at R47, check for `v1.0.6`, and read that session's file, `docs/handoffs/sessions/2026-10-18-ccr-4900ade8-1qc1s9.md`, besides the three below.]* *[2026-10-18, session `ccr-b3531dc9-oioi5k`: R47 is built as plugin 1.0.7 (PR #230); start at R48, check for `v1.0.7`, and read that session's file, `docs/handoffs/sessions/2026-10-18-ccr-b3531dc9-oioi5k.md`, too.]* Write in English only, and start every report with at most five bullets.

**Before anything else.** Read `HANDOFF.md` and follow it. Then read these session files:
- the newest one, `docs/handoffs/sessions/2026-10-15-ccr-01de3f80-ilnomi.md` (its last section);
- `2026-10-17-ccr-d96dbb91-v12amc.md`;
- `2026-10-17-ccr-f21be30b-5d5dpz.md`.

Check that `main` carries `v1.0.3` and that no open PR touches the files the candidate changes. *[2026-10-17, choice 212: the sprint starts after the safety PR (plugin 1.0.4) merges, so check for `v1.0.4` instead.]*

**How each candidate is built** (the owner's choice of 2026-10-16, decisions 30 to 33):
1. Write a precise spec from the candidate's proposal, its decision file and the code.
2. Have one Opus agent build it, with tests that fail on the old code.
3. Have an independent Opus agent review the diff, in a fresh context, report only.
4. Verify each finding, then send the real ones back to the builder.
5. Re-review the fix commit.
6. Run the four checks of `HANDOFF.md`'s precondition 1, with full `python -m pytest`, and paste the output.
7. Bump to the next free patch version (choice 184).
8. Open a draft PR and watch its CI to green.

Do not run the work through the framework's own pipeline. Never edit guardrail files; give me a table instead.

**The candidates:**
- **R17** — `docs/proposals/claude-comment-fix-round.md`. It is accepted. Decision 22's amendment needs its decision file first, in a documentation PR of its own. It also builds `is_owner_actor`, which R46 and R47 need, and the narrowing of the (c)/(d) labels to the owner's account (the owner agreed on 2026-10-16).
- **R46, R47, R48, R49** — `docs/proposals/pipeline-speed.md`, decisions 30 to 33. *[2026-10-17, the owner's choice 205 (`docs/PROGRESS.md`): R48 also covers NOTES §45 gap 1 (a panel `park` must park, fail closed, with a test) and gap 5 (the template's turn default).]* R49 needs my one-time GitHub App setup in a desktop browser: give me the exact steps when you reach it.

**Rules.** Keep tokens lean: a session PR is one builder and one reviewer, not a fan-out. End by writing your session file as `HANDOFF.md` says.
