# Progress — two ROADMAP candidates registered: R50 (revisit decision 17's parallel worktrees) and R51 (concurrent changes, safe by construction), and the owner's choice 232 (2026-10-19)

This session ran on branch `ccr-70fb3ae3-39fz5m`, from the owner's questions of 2026-10-19: the work still to be done, whether several items can run at once, whether that adds risk, and whether the pipeline expects it. The previous record (1.0.10, choices 228 to 231) is now `docs/progress/2026-10-19-1.0.10-and-choices-228-231.md`, unchanged. The session's own file is `docs/handoffs/sessions/2026-10-19-ccr-70fb3ae3-39fz5m.md`.

## Summary
- **The session's answer, in short.** A project's pipeline already runs several changes at once: every phase workflow keys its concurrency group on the work branch, and a new id skips the ids with remote branches. Framework sessions already run in parallel by HANDOFF's design (one session file each). The one thing decision 17 leaves out is parallel worktrees on one local checkout.
- **R50, a trigger to revisit decision 17's worktrees** (choice 232), `docs/proposals/revisit-parallel-worktrees.md`. Decision 17 carries a note beside its accepted option.
- **R51, concurrent changes safe by construction** (proposed, not accepted), `docs/proposals/concurrent-changes.md`. On the sample now, concurrency saves no meaningful time; on a real project it raises throughput, because most of a change's elapsed time is waiting for the owner. Its gaps: a build PR whose checks are not re-run when the default branch moves (the owner's merge is Exempt from the ruleset, and the release runs `deploy.command` after the merge), and an id race between two allocations before either pushes. The spend ceiling and the view of the changes in flight are already R25, R9 part 1 and R20.
- No change under `plugin/` or `template/`; no version bump.

## The owner's decisions (2026-10-19)
232. **Decision 17's "probably never" for parallel worktrees is revisited, not read as "never"** (the owner: "register to revisit this once the plugin is up and running for a while"). The session's reading of "a while": 20 changes past gate (e) on a project other than the sample, decision 17's own threshold for evals. ROADMAP R50.

## Proposed edits for the owner
None: no guardrail line changes.

## Left
- **R51 waits for the owner:** accept it and give it an Order, or drop it.
- **R50 has no automatic check:** a session that reads a real project's changes counts the changes past gate (e) and raises R50 at 20.
- **R51's G1 is read from the workflows and `sdlc-init.md`, not seen live:** a build PR behind the default branch merging and releasing with no re-run.

## Checks (this repository)
On the final head, after `python -m pip install -e ".[dev]"`, chained with `set -o pipefail`: the four commands of `HANDOFF.md`'s standing precondition 1. Their output is in the PR.
