# Session of 2026-10-23 on branch `claude/r14-prepare-0004-pin-move`: wave 4, lane B, R14's turn prepared

**Builds on:** `docs/handoffs/sessions/2026-10-23-ccr-545fcec0-ik69zj-end.md`, the newest on `main`, and the files it names (carried by reference, not re-verified, but for the rows below). Lane A of wave 4 (R26) runs in parallel; it had no session file on `main` when this one was written.

## Where the project stands
- **Framework `main` is at `b9dbd9b`** (#373), on plugin **1.0.38** (verified, `git fetch origin`, `git log -1 origin/main` and `.claude-plugin/plugin.json`; read at about 19:00 UTC). This repository's pin is **1.0.17** (verified, `sdlc.yaml:104`).
- **PR #173** (change 0004's intent, `sdlc/0004/a`): `main` merged in by a merge commit, `38fcd57`; the intent refreshed in `adf53ec`, its head (read at about 19:30 UTC on `adf53ec`). Not merged, not labelled; no phase started. What changed is in `docs/progress/2026-10-23-claude-r14-prepare-0004-pin-move.md`.
- **This PR** carries the non-guardrail half of the pin move (`tests/test_templates.py`), R14's ROADMAP annotation, the open-questions file's annotations, the record and this file. Its test is red until the owner's guardrail rows (the record's "Proposed edits for the owner") are on its branch.

## Preconditions of the moment
- The standing ones (`HANDOFF.md`). The pin move lands before #173 merges (choice 269, registered by the central session).
- If `main` moves before #173 merges, `sdlc/0004/a` is brought up to date by another merge commit, never a rebase.

## Next steps, in order
1. **The owner** adds the record's rows to this PR's branch; `Framework checks` turns green; the owner merges this PR.
2. **The owner merges #173**: the design run of change 0004 starts on the moved pin.
3. **The design run** settles the two open questions the intent keeps: the `proof` entry's final shape against R11, and the jobs' arithmetic for a set drive (`gate.drive_timeout`, the (e) session's cap, the setup and triage steps, a fix round at (e)).

## Every open item
| Item | Where | What is left | Who acts | Blocks 1.0.0 |
|---|---|---|---|---|
| The pin move to `main`'s version | the record, "Proposed edits for the owner" | The rows on this PR's branch, then the merge | owner | no |
| #173 | `sdlc/0004/a`, head `adf53ec` | The owner's merge, after the pin move | owner | no |
| R18's live checks | `2026-10-23-claude-r18-failed-run-explains-itself.md` | Possible on this repository once its copies carry R18 (this PR) | a session | no |
| The `proof` entry's shape | change 0004's intent, Open questions | Settled at the design against R11 as it stands | the design run | no |
| A plugin or template change with no bump; the managed settings file (reminder 2026-10-26); R64's known limit; the trigger evals' nondeterminism | `2026-10-23-ccr-545fcec0-ik69zj-end.md` | Carried, not re-verified | as there | no |

Done, dropped: "This repository's workflow copies without R18" (`2026-10-23-claude-r18-failed-run-explains-itself.md`): `without_r18` is removed in this PR, and the copies come with the owner's rows on its branch. Choice 261's settings rows (`docs/progress/2026-10-23-claude-r44-r59-i5.md`): already on `main` (#345, #347).

## What the owner does
| When | Act |
|---|---|
| Now | Add the record's rows to this PR's branch; merge it when green. |
| After that | Merge #173. |
| 2026-10-26 | Copy the managed settings file (the reminder, carried). |
