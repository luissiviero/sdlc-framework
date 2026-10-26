# Session of 2026-10-25 on branch `claude/pin-move-1-0-46`: wave 5, lane D, this repository's pin move to 1.0.46

**Builds on:** `docs/handoffs/sessions/2026-10-25-ccr-ca9f0149-a29zgl-wave-5.md`, the newest on `main`, and the files it names (carried by reference, not re-verified, but for the rows below); R45's records on `main` (`docs/progress/2026-10-25-claude-r45-0-names-since-decision-39.md` to `...-r45-4-files.md`). Lane A (R45's fifth rename PR) runs in parallel; it had no open PR when this was written.

## Where the project stands
- **Framework `main` is at `05d9412`** (#394), on plugin **1.0.46**, tagged `v1.0.46` on `05d9412` (verified, `git fetch origin`, `git ls-remote origin refs/tags/v1.0.46`; read at about 23:45 UTC). This repository's pin is **1.0.38** (`sdlc.yaml:143`) until this PR merges.
- **Since #389** every merge to `main` leaves SDLC design and SDLC build red, because the pinned 1.0.38 runner refuses `--phase build` (#394's merge: runs 40245262804 and 40245262856). This PR ends that.
- **This PR** carries `changes/0000` to `0005`'s `status.yaml` in the phase names (migrated with the plugin's own code), its record and this file. The guardrail lines are the owner's commit on its branch (the record, "Proposed edits for the owner").

## Preconditions of the moment
- The standing ones (`HANDOFF.md`). No change starts here before this PR merges (`docs/progress/2026-10-25-claude-r45-1-phase-names.md`, "What the owner does").
- If `main` moves before the merge, this branch takes it by a merge commit; if the moved `main` changes `sdlc.yaml`, `bands.yaml`, `CLAUDE.md` or `REVIEW.md`, the rows are read again first.

## Next steps, in order
1. **The owner** runs the record's commands on this branch (or edits by its table); `Framework checks` turns green on that head; the owner merges.
2. **After the merge**, the owner checks the record's "What the owner checks after the merge".
3. **The sample's pin move** with its own `status.yaml` migration, before R45's sixth PR (choice 273).

## Every open item
| Item | Where | What is left | Who acts | Blocks 1.0.0 |
|---|---|---|---|---|
| This repository's pin move | this PR | The owner's commit of the guardrail lines, then the merge | owner | no |
| The checks after the merge | the record | SDLC design and build green or skipped; `on-approval` recognised | owner | no |
| The letters left in guardrail comments and prose | the record, "Not in the rows" | A later prose PR or the owner's own edit | owner | no |
| The sample's pin move | choice 273 | Its own PR, before the sixth | a lane; owner | no |
| Everything the files above list open | their "Every open item" | Carried, not re-verified | as there | no |

Done, dropped: "The pin moves of this repository" (`2026-10-25-ccr-ca9f0149-a29zgl-wave-5.md`, next step 4), for this repository: this PR, once merged.

## What the owner does
| When | Act |
|---|---|
| Now | Run the record's commands in a Codespace on `claude/pin-move-1-0-46`; merge the PR when `Framework checks` is green on that head. |
| After the merge | The record's checks. |
