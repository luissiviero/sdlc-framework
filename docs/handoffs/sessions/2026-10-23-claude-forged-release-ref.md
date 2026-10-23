# Session of 2026-10-23 on branch `claude/forged-release-ref`: the forged release ref (plugin 1.0.31), the small lane beside wave 2

**Builds on:**
- `docs/handoffs/sessions/2026-10-23-claude-r44-r59-i5.md` (#344, `d72de6a`), the newest on `main`, and the files it builds on;
- `2026-10-23-claude-r51-r25-concurrent-spend.md` (#343), lane A of wave 1, whose open items that file does not list.

No other session file reached `main` since (verified, `ls docs/handoffs/sessions/` after `git fetch origin`, `main` at `d72de6a`).

## Where the project stands
- **Framework `main` is at `d72de6a`** (#344), on plugin **1.0.27** (verified, `git log -1 origin/main`, `.claude-plugin/plugin.json`). The root pin at 1.0.17 is carried, not re-verified.
- **Wave 2 runs**: lane A (R61 with R33) and lane B (R29 part 1 with R54, PR #348, plugin 1.0.28; `python tasks.py next-free` lists its branch `claude/r29-r54-quick-intent`). This session is the small lane beside them.
- **This PR** builds the forged release ref (choice 261, point 2) as plugin 1.0.31; its record is `docs/progress/2026-10-23-claude-forged-release-ref.md`.

## Preconditions of the moment
- The standing ones are in `HANDOFF.md`.
- Three sessions run at once: run `git fetch origin` and `python tasks.py next-free` before taking any number, and again after every merge of `main`.

## Next steps, in order
1. **This PR**: the owner merges it when `Framework checks` is green on its final head.
2. **R21's first part** (choice 257), in this lane, after lane A's PR merges: the desktop-only wording on step 6's CI secret and "Allow GitHub Actions to create and approve pull requests" bullets of `/sdlc-init`, its report, and the digest's unprotected-branch warning.
3. **R65's part 6** (choice 252), in this lane, after both wave 2 PRs merge: the stale places in comments under `plugin/` and `template/`.
4. The rest as `2026-10-23-claude-r44-r59-i5.md` lists them (carried, not re-verified).

## Every open item
| Item | Where | What is left | Who acts | Blocks 1.0.0 |
|---|---|---|---|---|
| This PR | framework | Green checks, the owner's merge | this session; owner | no |
| `status.yaml`'s `released_*` fields as owner-only fields | this PR's record, "What I need from you" | The owner's answer; then a small PR in R44's class | owner; a session | no |
| R21's first part, R65's part 6 | this lane | Next steps 2 and 3 | this session | no |
| Everything `2026-10-23-claude-r44-r59-i5.md` lists open | its "Every open item" | Carried, not re-verified, but for "The forged release ref", which is this PR, and "The two settings rows", merged by the owner as #345 and #347 (`f0e50f7`) | as there | no |
| The probe branches, R51 check 8 and check 11's record half, R25's weekly ceiling, R5's tag-workflow red | `2026-10-23-claude-r51-r25-concurrent-spend.md`, "Every open item" | Carried, not re-verified | as there | no |

Done, dropped:
- "The forged release ref" (the r44-r59-i5 file): this PR.
- "The two settings rows" (the r44-r59-i5 file): the owner's #345 and #347, on `main` at `f0e50f7`.

**The patch number:** lane A's #350 merged 1.0.29 (`4e122da`) and lane B's #348 merged 1.0.30 (`0733b8c`) first; after merging `main` this PR takes 1.0.31 (`python tasks.py next-free`, read at 12:20 UTC on `0733b8c`).

## What the owner does
| When | Act |
|---|---|
| Now | Merge this PR when `Framework checks` is green on its final head; answer its "What I need from you". |
| Any time | The rows the r44-r59-i5 file lists (carried). |
