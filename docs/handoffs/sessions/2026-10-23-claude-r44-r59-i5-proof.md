# Session of 2026-10-23 on branch `claude/r44-r59-i5`, second file: R44's live proof of `sandbox.credentials` (eval case 0007)

**Builds on:**
- `docs/handoffs/sessions/2026-10-23-claude-r44-r59-i5.md`, this session's first file (#344, merged as `d72de6a`);
- `2026-10-23-claude-r51-r25-concurrent-spend.md` (#343), lane A's file, which ran in parallel with it.

No other session file reached `main` since (verified, `ls docs/handoffs/sessions/` on `f0e50f7` after `git fetch`).

## Where the project stands
- **Framework `main` is at `f0e50f7`** (#347), on plugin **1.0.27** (verified, `git log -1 origin/main`, `.claude-plugin/plugin.json`). Since the first file: #344 merged, and the owner's #345 and #347 put choice 261's five deny rules into both settings files (verified, `git show origin/main:.claude/settings.json` and the template's copy, lines 12 to 16).
- **Running sessions**, read at about 09:30 UTC: wave 2's lane A (R61 + R33) and lane B (R29 part 1 + R54, #348, which holds 1.0.28), and the small lane (the forged release ref first, then R21 part 1 and R65 part 6).
- **This PR** adds eval case 0007, R44's live proof of `sandbox.credentials`; its record is `docs/progress/2026-10-23-claude-r44-r59-i5-proof.md`. No plugin version.

## Preconditions of the moment
- The standing ones are in `HANDOFF.md`. Numbers: `python tasks.py next-free` after a fetch; this PR takes none.

## Next steps, in order
1. **This PR**: the owner merges it when `Framework checks` and `Framework evals` are green on its final head. Case 0007 passed in run 39932784745 (note 60), proving the deny for `CLAUDE_CODE_OAUTH_TOKEN`, the credential the runner held.
2. **The running lanes' PRs**, as the parent session orders them.
3. **The fix workflow's setup step, live:** at the sample's next change, after the owner moves its pin to 1.0.27 or later.
4. The rest as lane A's file lists it.

## Every open item
| Item | Where | What is left | Who acts | Blocks 1.0.0 |
|---|---|---|---|---|
| This PR | framework | Green checks, the owner's merge | this session; owner | no |
| The forged release ref | choice 261, point 2 | The small lane's PR (`claude/forged-release-ref`) | the small lane | no |
| The fix workflow's setup step, live | this PR's record, "Left" | One fix round on the sample at 1.0.27 or later, recorded in a note | owner (the pin); a session | no |
| The `/proc` read and the setup step's reach into the toolchain | choice 261, point 1 | With I6, after the real-project trial | a session | no |
| Everything lane A's file lists open | `2026-10-23-claude-r51-r25-concurrent-spend.md`, "Every open item" | Carried, not re-verified | as there | no |

Done, dropped:
- "The two settings rows" (the first file): the owner's #345 and #347.
- "R44's live checks", the `sandbox.credentials` half: this PR.
- "This PR" of the first file (#344): merged as `d72de6a`.

## What the owner does
| When | Act |
|---|---|
| Now | Merge this PR when its checks are green. |
| At the sample's next change | Move its pin to 1.0.27 or later, so a fix round there shows the new setup step. |
