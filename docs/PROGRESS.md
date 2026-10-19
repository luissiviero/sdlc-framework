# Progress — the speed-first order: ROADMAP R50 to R54, the Order rewritten, and the owner's choices 233 and 234 (2026-10-19)

This session ran on branch `ccr-70fb3ae3-39fz5m`, from the owner's questions of 2026-10-19: the work left, whether it can run concurrently, and then how to speed the plugin's use up as far as possible, "even if it means giving up a bit of control for a meaningful time boost". The previous record (the fast lane's recovery as 1.0.11, choice 232, PR #242) is now `docs/progress/2026-10-19-fast-lane-recovery-1.0.11-and-choice-232.md`, unchanged; the one before it (1.0.10, choices 228 to 231) is `docs/progress/2026-10-19-1.0.10-and-choices-228-231.md`, as #242 archived it. This record's choices were first numbered 232 and 233 and moved to 233 and 234 when #242's choice 232 merged first. The session's own file is `docs/handoffs/sessions/2026-10-19-ccr-70fb3ae3-39fz5m.md`.

## Summary
- **Concurrency, the session's answer.** A project's pipeline already runs several changes at once: every phase workflow keys its concurrency group on the work branch, and a new id skips the ids with remote branches. Framework sessions already run in parallel by HANDOFF's design. On the sample, concurrency saves no meaningful time; on a real project it raises throughput, since most of a change's elapsed time is waiting for the owner.
- **R50**: a trigger to revisit decision 17's parallel worktrees at 20 changes past gate (e) on a real project (choice 233). Decision 17 carries a note.
- **R51**: concurrent changes, safe by construction (`docs/proposals/concurrent-changes.md`): a build PR behind the default branch is brought up to date and re-checked before gate (e) and the release, and a new id is reserved on the remote.
- **The speed-first order** (choice 234, `docs/proposals/speed-beyond-the-sprint.md`): R7, then R24, R22, R51 with R25 parts 1-2, R18, R29 part 1 with R54, R26 and R52 move to ranks 7 to 15; the rest keep their order among themselves after them. Each moved cell is annotated with its previous rank.
- **Three new candidates**: R52, merge by silence at gate (e), opt-in, decided only at R50's trigger; R53, faster CI jobs, measured first; R54, the quick intent, with R29 part 1.
- No change under `plugin/` or `template/`; no version bump.

## The owner's decisions (2026-10-19)
233. **Decision 17's "probably never" for parallel worktrees is revisited, not read as "never"** (the owner: "register to revisit this once the plugin is up and running for a while"). The session's reading of "a while": 20 changes past gate (e) on a project other than the sample, decision 17's own threshold for evals. ROADMAP R50.
234. **The speed table's recommendations, all accepted** ("I accept all recommendations as you suggest them"):
    - the speed-first Order above, with R51 accepted and R52 to R54 added;
    - the sample runs `review: deferred` (applied by the owner, sample PR #72);
    - the existing profiles are used per project (`deploy.production: false` where there is no real production, Lite for scripts, documentation and experiments); the sample keeps `production: true`;
    - incident intents keep gate (a);
    - the fix-round caps stay until R26's measures.

## Proposed edits for the owner
None: no guardrail line changes in this PR. (The sample's pin is #241's row.)

## Left
- **The owner's merge order is #242, #241, #240.** #242 is merged into this branch. When #241 merges, this branch merges `main` again: #241's record moves to `docs/progress/` unchanged, this record stays, and one copy of the 1.0.10 archive is kept (#242's name; #241 archives it as `2026-10-19-fix-round-robustness-1.0.10-and-choices-228-231.md`). #241 becomes 1.0.12.
- **R50 has no automatic check:** a session that reads a real project's changes counts the changes past gate (e) and raises R50 at 20.
- **R51's G1 is read from the workflows and `sdlc-init.md`, not seen live.**
- **R53's measure** is the live-proof session's to take from change 0015's job steps, if it agrees.

## Checks (this repository)
On the final head, after `python -m pip install -e ".[dev]"`, chained with `set -o pipefail`: the four commands of `HANDOFF.md`'s standing precondition 1. Their output is in the PR.
