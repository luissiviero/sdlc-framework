# Session of 2026-10-23 on branch `claude/r27-policy-sources`: lane B of wave 3, R27 (plugin 1.0.35)

**Builds on:**
- `docs/handoffs/sessions/2026-10-23-ccr-545fcec0-ik69zj.md` (#362), the central session's file that started wave 3 and names this lane;
- the files it names, carried by reference, not re-verified: `2026-10-23-claude-next-free-no-gap.md`, `2026-10-23-claude-r65-part-6-follow-up.md`, `2026-10-23-claude-r66-follow-up.md`, `2026-10-23-claude-r61-r33-trial-shape-formatter-four-points.md`, `2026-10-23-claude-r44-r59-i5-proof.md`, `2026-10-23-claude-r21-desktop-only.md` and `2026-10-23-claude-forged-release-ref.md`.

## Where the project stands
- **Framework `main` is at `2a0e7c7`** (#363, the small lane's owner-fields patch), on plugin **1.0.34** (verified, `git log -1 origin/main` after `git fetch origin`, read at 15:35 UTC).
- **Decision 40** (amends 6: `policies/` a guardrail path) merged as #364 (`7cac00e`). Its review's corrections (`Edit(policies/**)` without the slash in the managed file; "Today"; "four checks"; the exceptions' sources) missed that merge by a minute. They are in **#365**, as dated annotations, open at the time of writing.
- **This PR** builds R27 as plugin 1.0.35; its record is `docs/progress/2026-10-23-claude-r27-policy-sources.md`. R64, the lane's second PR, waits for its merge.

## Preconditions of the moment
- The standing ones are in `HANDOFF.md`; the central session's in `docs/handoffs/central-session.md`.
- **Wave 3's merge order** is carried from the central session's file: lanes A and B by version, the later renumbering; R64 after R27.

## Next steps, in order
1. **#365**: the owner merges it when `Framework checks` is green.
2. **This PR**: the `Framework evals` run on its head is the live check of the trigger cases (NOTES §61). Add the run's URL to the note beside its "Not verified live" sentence. Then the owner merges it when every check is green, after the lane says it is ready.
3. **The owner's row** (this PR's record, "Proposed edits for the owner"): `Edit(/policies/**)` in `template/.claude/settings.json`. After it, a small PR adds the rule to the preflight's `REQUIRED_DENY`.
4. **R64**, on a branch from `main` after this PR merges.

## Every open item
| Item | Where | What is left | Who acts | Blocks 1.0.0 |
|---|---|---|---|---|
| #365 | framework | Green checks, the owner's merge | owner | no |
| This PR | framework | The live trigger run, the review's fixes, the owner's merge | lane B; owner | no |
| The template's `Edit(/policies/**)` rule | this PR's record | The owner's edit; then `REQUIRED_DENY` in a follow-up | owner; a session | no |
| NOTES §61 not verified live | `docs/notes/61.md` | The first `Framework evals` run on this branch; its URL beside the sentence | lane B | no |
| R64 | ROADMAP | Built after this PR merges | lane B | no |
| Everything the central session's file lists open | `2026-10-23-ccr-545fcec0-ik69zj.md`, "Every open item" | Carried, not re-verified | as there | no |

## What the owner does
| When | Act |
|---|---|
| Now | Merge #365 when it is green. |
| When lane B says this PR is ready | Merge it; apply the template settings row in its record. |
