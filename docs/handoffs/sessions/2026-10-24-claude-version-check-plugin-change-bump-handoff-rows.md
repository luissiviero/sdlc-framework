# Session of 2026-10-24 on branch `claude/version-check-plugin-change-bump`, second PR: `HANDOFF.md`'s rows of choice 270 (choice 271)

**Builds on:** `docs/handoffs/sessions/2026-10-24-claude-version-check-plugin-change-bump.md`, this session's first file (#377), and through it the files it names; their open items are carried by reference, not re-verified, but for the rows named below.

## Where the project stands
- **Framework `main` is at `f2bb754`** (#377, merged 2026-10-24 at 12:44 UTC), on plugin **1.0.39** (verified, `git fetch origin` and `git log -1 origin/main`, read at about 12:55 UTC). From #377 on, `version-check` fails a change under `plugin/` or `template/` with no version above `main`'s.
- **This PR**: `HANDOFF.md`'s two rows and the annotation of `docs/handoffs/central-session.md:38` (choice 271; the record: `docs/progress/2026-10-24-claude-version-check-plugin-change-bump-handoff-rows.md`). Documentation only, no version.

## Preconditions of the moment
- The standing ones are in `HANDOFF.md`; the central session's in `docs/handoffs/central-session.md`.

## Next steps, in order
1. **This PR**: `Framework checks` green on its final head; the owner merges.
2. The rest as the files above list it.

## Every open item
| Item | Where | What is left | Who acts | Blocks 1.0.0 |
|---|---|---|---|---|
| This PR | framework | Green checks, the owner's merge | owner | no |
| Change 0004's build phase and the bump | `sdlc/0004/*` | Its build changes `plugin/`, so it must bump; its spec plans it, read by this session's reviewer, not verified here | the build run; owner | no |
| Everything the files above list open | their "Every open item" | Carried, not re-verified | as there | no |

Done, dropped: "#377" (merged as `f2bb754`); "`HANDOFF.md`'s description of `version-check`" (this PR).

## What the owner does
| When | Act |
|---|---|
| Now | Merge this PR when `Framework checks` is green. |
| On a web-editor PR that touches `plugin/` or `template/` | Bump `.claude-plugin/plugin.json` and the marketplace entry in the same PR (carried from the first file). |
