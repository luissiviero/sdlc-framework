# Session of 2026-10-23 on branch `claude/r64-template-copies-refresh`: lane B of wave 3, R64 (plugin 1.0.37)

**Builds on:**
- `docs/handoffs/sessions/2026-10-23-claude-r27-policy-sources.md` (#367), this session's own file from its first PR;
- the files it names, carried by reference, not re-verified.

## Where the project stands
- **Framework `main` is at `9554cf4`** (#369, the owner's template settings row, after #367, R27), on plugin **1.0.35** (verified, `git log -1 origin/main` after `git fetch origin`, read at 16:40 UTC); merged into this branch with a merge commit. #364 and #365 (decision 40 and its corrections) merged before it.
- **This PR** builds R64 as plugin 1.0.37. Its record is `docs/progress/2026-10-23-claude-r64-template-copies-refresh.md`. Lane A's R18 holds 1.0.36 and merges first by version.
- **R27's live trigger evals**: 15 of 15 in `Framework evals` run 39984180036 (NOTES §61, the R27 record).

## Preconditions of the moment
- The standing ones are in `HANDOFF.md`; the central session's in `docs/handoffs/central-session.md`.
- **A template change now needs its hash:** `python tasks.py template-hashes`, committed with the change, or `tests/test_refresh.py` fails.

## Next steps, in order
1. **This PR**: the owner merges it when every check is green, after lane A's 1.0.36 and after the lane says it is ready.
2. **`REQUIRED_DENY` gains `Edit(/policies/**)`**, now that the template carries the rule: the small lane's follow-up (the central session, 16:34 UTC), not R64's.

## Every open item
| Item | Where | What is left | Who acts | Blocks 1.0.0 |
|---|---|---|---|---|
| This PR | framework | Green checks, the owner's merge in version order | lane B; owner | no |
| `REQUIRED_DENY` gains `Edit(/policies/**)` | `plugin/gate/preflight.py` | A small follow-up PR | the small lane | no |
| Everything the files above list open | their "Every open item" | Carried, not re-verified | as there | no |

Done, dropped: "#365" and "This PR" (R27) from R27's session file, merged as #365 and #367. "The template's `Edit(/policies/**)` rule": the owner's #369, `template/.claude/settings.json` line 17 (verified on `9554cf4`). "NOTES §61 not verified live", closed in #367: run 39984180036. "R64": this PR.

## What the owner does
| When | Act |
|---|---|
| When lane B says this PR is ready | Merge it after lane A's 1.0.36. |
