# Session of 2026-10-22 on branch `ccr-6ed8a82e-cxmftx`, end: R8 shipped as 1.0.19, never run live; two defects found; the next session's prompt

**Builds on:**
- `docs/handoffs/sessions/2026-10-20-ccr-6ed8a82e-cxmftx.md`, this session's first file, merged with #304 (`405d31f`, tag `v1.0.19`). This file is named `-end` because the branch is the same.
- `docs/handoffs/sessions/2026-10-22-claude-sources-of-truth-study-csl6nq-end.md`, the newest session file on `main` at `50eea3b` (#323). It names its own first file and `2026-10-22-ccr-76f1ceba-idf2w0.md`; no other session file reached `main` after those (verified, `git log --diff-filter=A` per file on `50eea3b`).

The branch was restarted from `main` at `50eea3b`, since #304 merged; this file is its only change.

The owner asked, two days after #304: is Gemini being used, or was it ever? Then: write this file, and the prompt for a new session that fixes the Gemini use and adds it to the agreed x-roles (R28).

## Where the project stands
- **Framework `main` is at `50eea3b`**, plugin **1.0.23** (verified, `git log -1 origin/main`, `.claude-plugin/plugin.json`). The root pin stays at 1.0.17 (`sdlc.yaml:104`; choice 249, point 2).
- **R8 shipped as 1.0.19** (#304, `405d31f`). Neither the framework repository's root `sdlc.yaml` nor any session step holds an `external_review` block or the key (verified, `git show origin/main`). The Gemini host is on none of the three sandbox lists (the two `.claude/settings.json` files since #309 and #310, `plugin/ci/settings.ci.json` since #304; verified, `grep`).
- **The sample has it on**: pin 1.0.22, `external_review: {model: gemini-4-argon, phases: [b]}` (verified, its `sdlc.yaml` on `28fba16`), the 1.0.19 copies since sample #92 (`21f1748`). Its secret was reported set by the owner (carried from `2026-10-20-ccr-0edc2256-yax6jz-part-3.md`; a session cannot read secrets).

**Gemini has never been called by either repository** (the owner's question, answered from the runs):
- **The sample**: every `second-opinion` job so far was skipped, because each design run since the 1.0.19 copies was an upgrade or `sdlc.yaml` PR with no change (verified, runs 39851009446 and 39835549859, job `second-opinion: skipped`). No real change has run there since.
- **The 1.0.17 window** (#290 merged 17:07 UTC, #304 21:13 UTC, 2026-10-20): every framework design and build run in it took 51 seconds or less, so no Claude session started. There were no scan or detect runs, and no command, agent or skill at `v1.0.17` mentions Gemini (verified, the run list and `git grep -il gemini v1.0.17 -- plugin/commands plugin/agents plugin/skills`).
- **Not seen from here**: the key's use on Google's side (the key's Google project shows it).

## Two defects found in this session, not fixed
1. **This repository's own copies call a file its pin does not have.** `.github/workflows/sdlc-design.yml` and `sdlc-deploy.yml` on `main` run `python framework/plugin/external/cli.py` in the `second-opinion` job (`sdlc-design.yml:256`). The framework is checked out at the root pin, 1.0.17, which has no `plugin/external/` (verified, `git show v1.0.17:plugin/external/cli.py` fails). The command stops before it can read `sdlc.yaml`, so the job fails red on this repository's first real change (change 0004, #173, at R14's turn), although `external_review` is off here. Every project pinned below 1.0.19 that copies the 1.0.19+ templates has the same defect.
2. **On the fast lane, the (b) opinion lands on a PR the owner never reads.** On a routine plan, the design PR is closed as `sdlc:superseded` once the build PR exists, and the owner's first look is at (e) (`docs/OPERATING_MODEL.md` §4.2, the build row). That is the sample's normal path, and (b) is the only phase it turns on. The comment goes on the closed design PR, and nothing carries it to the build PR. As built, the second opinion reaches the owner only on a non-routine plan.

Known before, still open: the (e) job runs whenever the deploy job succeeds, also when the runner's guard skipped phase (e) on that event (this session's first file).

## Preconditions of the moment
- The standing ones are in `HANDOFF.md`.
- **Next free numbers**, read on `main` at `50eea3b`: choice 253, candidate R66, note 58, decision 39, patch 1.0.24. They match the csl6nq "-end" file.

## Next steps, in order
1. **The owner merges this session's PR** (this file only, documentation).
2. **A new session fixes the Gemini use and puts it into the x-roles**, from the prompt this session gave in the chat: both defects above, the (e) waste, a first live call, then the owner's questions on Gemini in R28's roles before any decision file.
3. Then the next steps of the csl6nq "-end" file, carried unchanged, not re-verified: R65's part 1 and on, the queue from R51 with R25, the sample's next-change notes, this repository's own App at R14's turn.

## Every open item
| Item | Where | What is left | Who acts | Blocks 1.0.0 |
|---|---|---|---|---|
| This PR | framework | Green checks, the owner's merge | owner | no |
| The pinned-below-1.0.19 job failure | `.github/workflows/sdlc-design.yml:256`, `sdlc-deploy.yml`, their templates | Defect 1 above | the next session | no |
| The fast lane's lost (b) opinion | `plugin/external/cli.py`, the design workflow | Defect 2 above | the next session; owner (where it should land) | no |
| The (e) job when phase (e) did not run | `sdlc-deploy.yml`, the `second-opinion` job | Gate it on the phase step's own outcome | the next session | no |
| The first live call | the sample, or by hand | The model id and the request's shape are unconfirmed live: `cli.py models` with the key, or the sample's next real change | owner; the next session | no |
| The Developer API's terms | `ai.google.dev/gemini-api/terms` | Not readable from a session's proxy; the owner's read from the PC | owner | no |
| Gemini in the x-roles | R28; `docs/proposals/roles-and-manager.md`; decision 21 | R28 as accepted says "Opus and Fable only" and "Claude Code sub-agents run Claude models". Adding Gemini amends that and decision 21 (the panel), so it is the owner's call, in one decision with R28's own amendment of 21 (`docs/reviews/2026-10-20-gemini-study-check.md`, row 4) | the next session; owner | no |
| R8's tally | `docs/proposals/external-design-check.md`, "Tally" | No row yet: no live run | the session that reads the first one | no |
| R62 | ROADMAP R62 | Unordered; it can reuse `plugin/external/gemini.py` | owner | no |
| The port list | `docs/PROGRESS.md` | #304 touched `plugin/ci/run_phase.py` and the detect and fix templates (carried) | the 1.0.0 read | no |
| Everything the csl6nq "-end" file lists open | `2026-10-22-claude-sources-of-truth-study-csl6nq-end.md`, "Every open item" | Carried unchanged, not re-verified | as there | no |

Done, dropped (from this session's first file):
- "This session's PR": #304, merged as `405d31f`, tag `v1.0.19`.
- "The pastes of choice 248": the framework's two `.claude/settings.json` files by #309 and #310 (verified, no host line on `main`); the root pin is held at 1.0.17 by choice 249.
- "The sample's second opinion": samples #92, #97 and #98 (verified, `git log` on the sample); the secret is reported set.
- "R22's build" and the version collision: R22 is 1.0.18 (#306), R8 1.0.19.
- "The model id" and "The request's shape": folded into "The first live call" above.

## What the owner does
| When | Act |
|---|---|
| Now | Merge this PR when `Framework checks` is green. |
| Now | Start the new session with the prompt in this session's chat. |
| Any time, optional | In one PowerShell window on the PC: `$env:GEMINI_API_KEY = "<key>"`, then `python plugin/external/cli.py models` from the framework checkout; tell the new session the ids it lists. |
| Any time | The key's usage page in its Google project, if a check of past use is wanted. |
