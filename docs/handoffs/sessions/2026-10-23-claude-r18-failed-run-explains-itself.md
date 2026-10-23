# Session of 2026-10-23 on branch `claude/r18-failed-run-explains-itself`: lane A of wave 3, R18 (plugin 1.0.36)

**Builds on:**
- `docs/handoffs/sessions/2026-10-23-ccr-545fcec0-ik69zj.md`, the second central session's file, which starts wave 3 and names this lane;
- `2026-10-23-claude-decision-39-names.md`, the small lane's file, the newest on `main` at `20979f2`;
- the files they name, and `2026-10-23-claude-r66-follow-up.md`, `2026-10-23-claude-r65-part-6-follow-up.md` and `2026-10-23-claude-r65-part-5-handoff.md`, read at this session's start. Their open items are carried by reference, not re-verified.

## Where the project stands
- **Framework `main` is at `20979f2`** (#365), on plugin **1.0.34** (verified, `git fetch origin`, `git log -1 origin/main`, read at 15:52 UTC). The small lane's owner-fields patch is on it (#363, merged as `2a0e7c7`, 1.0.34; verified, `git show 2a0e7c7:.claude-plugin/plugin.json`). The root pin at 1.0.17 is carried, not re-verified.
- **`main` merged in at `9554cf4`** (#369), with lane B's R27 (#367, plugin 1.0.35) in it (verified, `git log origin/main` after `git fetch origin`, read at 16:36 UTC); the version conflict was resolved to this PR's 1.0.36, and `python tasks.py verify` is green on the merge.
- **This PR** builds R18 and takes 1.0.36: lane B's `claude/r27-policy-sources` holds 1.0.35 (`python tasks.py next-free` on `20979f2`). Its record is `docs/progress/2026-10-23-claude-r18-failed-run-explains-itself.md`.

## Preconditions of the moment
- The standing ones are in `HANDOFF.md`; the central session's in `docs/handoffs/central-session.md`.
- **The merge order of wave 3** is the central session's file's: lanes A and B by version, lowest first, the later renumbering. If lane B merges first, this PR stays at 1.0.36; if this PR merges first, lane B keeps 1.0.35 and `version-check` passes both. Run `git fetch origin`, `python tasks.py next-free` and `python tasks.py version-check` after every merge.

## Next steps, in order
1. **This PR**: the independent review's fixes, `Framework checks` green, then the owner marks it ready and merges it in the central session's order.
2. **The first live triage**: the next parked or red phase run on a project pinned at 1.0.36 or later; read its park block or the digest's "Failed runs" line against the job log (the proposal's "How it is judged").
3. **This repository's own workflow copies** gain R18's lines when the root pin moves from 1.0.17 (R14's turn), with `tests/test_templates.py without_r18` removed.
4. Everything else as the files above list it.

## Every open item
| Item | Where | What is left | Who acts | Blocks 1.0.0 |
|---|---|---|---|---|
| This PR | framework | The review's fixes, green checks, the owner's merge | this session; owner | no |
| R18's live checks | this PR's record, "Known limits" | An `always()` step after `timeout-minutes`; `matching-refs` and the contents API on `refs/sdlc/failed-runs/`; the first live triage | a session at the first trial run | no |
| The deploy job's `timeout-minutes` | this PR's record, "Known limits" | 200 minutes is below the review pass, (e) and the commands step (125 + 125 + 50), as the proposal noted; the triage adds five | owner (whether to raise it); a session | no |
| This repository's workflow copies without R18 | `tests/test_templates.py` (`without_r18`) | Installed with the pin move | the session of R14's turn | no |
| Everything the files above list open | their "Every open item" | Carried, not re-verified | as there | no |

## What the owner does
| When | Act |
|---|---|
| When this PR is green | Mark it ready and merge it in the central session's order. |
