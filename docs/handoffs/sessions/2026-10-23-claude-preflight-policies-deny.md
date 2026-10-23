# Session of 2026-10-23 on branch `claude/preflight-policies-deny`: the small lane of wave 3, the preflight's `Edit(/policies/**)` (plugin 1.0.37)

**Builds on:**
- `docs/handoffs/sessions/2026-10-23-claude-decision-39-names.md` (#366), this session's earlier file, which covers #363 and #366;
- `2026-10-23-claude-r27-policy-sources.md` (#367), lane B's file, which names this follow-up (its "Next steps", step 3);
- the files those carry, by reference, not re-verified.

## Where the project stands
- **Framework `main` is at `9554cf4`** (#369, the owner's `Edit(/policies/**)` in `template/.claude/settings.json`), on plugin **1.0.35** (verified, `git log -1 origin/main` and `git show origin/main:.claude-plugin/plugin.json` after `git fetch origin`, read at 16:40 UTC).
- **This PR** adds the rule to the preflight's `REQUIRED_DENY` as plugin 1.0.37 (1.0.36 is held by lane A); its record is `docs/progress/2026-10-23-claude-preflight-policies-deny.md`.

## Preconditions of the moment
- The standing ones are in `HANDOFF.md`; the wave's in the central session's file.
- **Numbers:** if lane B's R64 or lane A merges first with 1.0.37, this PR renumbers after `git fetch origin` and `python tasks.py next-free`.

## Next steps, in order
1. **This PR**: the owner merges it when `Framework checks` is green on its final head.
2. Everything else as the files above list it.

## Every open item
| Item | Where | What is left | Who acts | Blocks 1.0.0 |
|---|---|---|---|---|
| This PR | framework | Green checks, the owner's merge | this session; owner | no |
| A project initialised before #369 | this PR's record, "Known limits" | Re-run `/sdlc-init` on its next upgrade (the sample included) | owner | no |
| Everything the files above list open | their "Every open item" | Carried, not re-verified | as there | no |

Done, dropped: "The template's `Edit(/policies/**)` rule" of `2026-10-23-claude-r27-policy-sources.md`: the owner's edit is #369; the `REQUIRED_DENY` follow-up is this PR.

## What the owner does
| When | Act |
|---|---|
| When it is green | Merge this PR. |
