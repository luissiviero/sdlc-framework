# Session of 2026-10-23 on branch `claude/r61-r33-trial-shape-formatter`, second file: choice 263, plugin 1.0.31

**Builds on:**
- `docs/handoffs/sessions/2026-10-23-claude-r61-r33-trial-shape-formatter.md`, this session's first file, merged with #350 (`4e122da`), the newest on `main`;
- `2026-10-23-ccr-b2d02bf7-9ywgjn-end.md` (#352, `dfd3f56`), the first central session's end file, read here for the first time; its lanes table and open items are carried below.

No other session file reached `main` since (verified, `git diff --name-only d80981a origin/main -- docs/handoffs/sessions` after `git fetch origin`, read on `4e122da`).

## Where the project stands
- **Framework `main` is at `4e122da`** (#350, R61 with R33), on plugin **1.0.29** (verified, `git show origin/main:.claude-plugin/plugin.json`; the tag `v1.0.29` exists, `git ls-remote --tags origin`). The root pin at 1.0.17 is carried, not re-verified.
- **#350 merged before #348**, not after it as the central session's merge order had it (`2026-10-23-ccr-b2d02bf7-9ywgjn-end.md`, "The running lanes"). Lane B's branch now holds 1.0.30 (`python tasks.py next-free`, read on `4e122da`).
- **This PR** registers choice 263 (the owner's answers to #350's four points) and builds its point 3 as plugin **1.0.31**. Its record is `docs/progress/2026-10-23-claude-r61-r33-trial-shape-formatter-four-points.md`.

## Preconditions of the moment
- The standing ones are in `HANDOFF.md`; a central session coordinates the lanes (`docs/handoffs/central-session.md`, choice 262).
- **Numbers:** this PR takes choice 263 and plugin 1.0.31. Choice 263 is also held on lane B's branch and on `ccr-9171b99a-q6u17y`; the choices on `main` must run without a gap, so the branch that merges after this PR renumbers its choice. Lane B (#348) holds 1.0.30, and the small lane (#349) renumbers after the PRs ahead of it. A lane that merges after this PR renumbers above 1.0.31 (`python tasks.py version-check`).

## Next steps, in order
1. **This PR**: the owner merges it when `Framework checks` is green on its final head.
2. **#348, #349 and #351**, in the central session's order; each merges `main` in and takes the number `next-free` gives.
3. **The rest, as the central session's end file lists it** (carried, not re-verified): the names decision (decision 39), the trial after wave 5, and the items carried from earlier files.

## Every open item
| Item | Where | What is left | Who acts | Blocks 1.0.0 |
|---|---|---|---|---|
| This PR | framework | Green checks, the owner's merge | owner | no |
| #348, #349, #351 | `2026-10-23-ccr-b2d02bf7-9ywgjn-end.md`, "The running lanes" | The owner's merges; each lane renumbers above `main` | owner; the lanes | no |
| The `sdlc.yaml` row | `docs/progress/2026-10-23-claude-r61-r33-trial-shape-formatter.md`, "Proposed edits for the owner" | `hooks.format_on_edit` becomes `formatters: []` at the move from pin 1.0.17 | owner | no |
| R61's and R33's live checks | the same record, "Verified" | `sandbox.allowed_domains` and the Bash timeout in a CI session, on the trial project | a session | no |
| R33's open items | `docs/proposals/formatter-per-language.md`, "Order" | Full Rust support; the quarantine runbook for Node and Rust | a session | no |
| Everything else carried | `2026-10-23-ccr-b2d02bf7-9ywgjn-end.md` and this session's first file, "Every open item" | Carried, not re-verified | as there | no |

Done, dropped:
- "This PR" of the first file (#350): merged as `4e122da`.
- "#350's four points": answered, choice 263.
- **Correction to the first file:** its row "The probe branches" (the owner deletes them) is done. The central session's end file records them deleted (`git ls-remote` lists none).

## What the owner does
| When | Act |
|---|---|
| Now | Merge this PR when `Framework checks` is green on its final head. |
| After it | Merge #348, #349 and #351 as the central session reports each green. |
| At the move from pin 1.0.17 | The `sdlc.yaml` row in the first record. |
