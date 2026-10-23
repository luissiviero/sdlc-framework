# Session of 2026-10-23 on branch `ccr-fc4dc248-6pmtbd`, end: R8 fixed as plugin 1.0.24 (#335); the first live call refused for billing; the Gemini items moved to the end of the queue

**Builds on:**
- `docs/handoffs/sessions/2026-10-23-ccr-fc4dc248-6pmtbd.md`, this session's first file (#331, merged as `5357fdc`). This file is named `-end` because the branch is the same.
- `2026-10-23-claude-r65-part-5-handoff.md` (#334), the newest other file on `main`, which builds on the R65 files the first file read.

No other session file reached `main` (verified, `git ls-tree origin/main docs/handoffs/sessions/` after `git fetch`, read at 02:21 UTC on `5357fdc`).

## Where the project stands
- **Framework `main` is at `5357fdc`**, on plugin 1.0.23, with the root pin at 1.0.17 (verified, `git log -1 origin/main`, `.claude-plugin/plugin.json` and `sdlc.yaml:104` on it).
- **R65's parts 1 to 5 are on `main`** (#324, #325, #327, #329, #334). Part 6 waits for R51 (carried from the part-5 file, not re-verified).
- **#335, this session's PR**, builds plugin 1.0.24. Its record is `docs/PROGRESS.md`, and it carries this file.
  - Defect 1: the step is skipped green at a pin without `plugin/external/`.
  - The (e) job runs only when phase (e) ran (`phase_ran`).
  - Defect 2: the fast lane's (b) opinion is carried onto the build PR at (e) (choice 255).
  - An independent review's seven fixes, and the trace's list.
  - Every check on `4b4f801` is green (read at 02:20 UTC). The push carrying this file runs them again.
- **Choice 256** (in #335's record): the Gemini items go to the end of the queue. R8 stays last in ROADMAP's Order column, and R62 is ranked after it, not accepted. Part 2 and Part 3 of this session's prompt wait behind every other ranked candidate.
- **Part 2's first try** (#335's record, "Part 2's first try"):
  - The dry run on the sample's change 0017 built 8 files, 31,214 characters.
  - The real call got `HTTP 429` on the free tier, with `limit: 0` for `gemini-4-argon`. The sample key's Google project has no billing linked.
  - The request's shape is not verified, and note 58 is not written.
  - The owner's Google AI Pro plan includes no API quota, only Google Cloud credit: $10 a month by Google's plan pages, not verified from a bill.
- **Open PRs**, read at 02:21 UTC: #335, the owner's #328, #173. The sample's #55 is carried, not re-verified.

## Preconditions of the moment
- The standing ones are in `HANDOFF.md`.
- **Numbers:** run `python tasks.py next-free`. #335 takes choices 255 and 256 and patch 1.0.24; this session took no note and no decision.
- **The sample is not upgraded to 1.0.24.** Its `main` is at `28fba16`, with pin 1.0.22 and the 1.0.19 workflow copies. The carry and `phase_ran` need both its pin and its copies at 1.0.24 (#335's record, the trace).

## Next steps, in order
1. **#335**: the owner merges it when `Framework checks` is green on its final head; `sdlc-tag.yml` then tags `v1.0.24`.
2. **The other sessions' next steps**, in ROADMAP's Order column, as the part-5 file lists them: the merge-tool deny rule after #328, the queue from R51 with R25, the sample's next change, this repository's pin move at R14's turn. Carried, not re-verified.
3. **At R8's turn, last in the queue (choice 256):**
   - The owner links billing to the sample key's Google project, with the AI Pro credit and a $10 budget alert.
   - A session runs Part 2 again (the commands are in this session's chat, and repeated below) and writes note 58: the model id from Part 0, and the request's shape.
   - The sample's upgrade to 1.0.24: the workflow copies in a sample PR, and the owner's `sdlc.yaml` edits in full, in the owner's format. Those are the pin move and choice 252's row 5 (choice 253, point 8).
   - Then Part 3 (below), the owner's questions before any decision file.

Part 2, by hand, from a Codespace on `sdlc-sample-python` with a framework clone at `~/sdlc-framework`:
- `python ~/sdlc-framework/plugin/external/cli.py review --root . --id 0017 --phase b --ref main --dry-run`;
- then, with the key set in one terminal only (`read -rsp`), the same command without `--dry-run` and with `--out ~/review-0017.json`.

### Part 3, carried: Gemini in R28's roles (proposal drafted, questions not yet asked)
Read for it: R28's row and `docs/proposals/roles-and-manager.md`, decisions 11, 12 and 21, R7's model shape, the study and its check (row 4). The owner's rules: Gemini doubles a role and never replaces one; it never decides; it never parks; it is read-only; every call shows its cost.

The draft, to put to the owner as questions with these recommendations:
1. **Which roles get a Gemini double.** Recommended:
   - the Architect at (b), which is R8's (b);
   - the Code reviewer at (e), which is R8's (e);
   - Security & policy, only on a risk-list hit, on the diff;
   - the panel after the fact, below.

   Not doubled: Product, Platform & release, Operations, the manager, the conciliator, the `/sdlc-plan` interview and the three sub-agents. The study ranks them low; the manager and the conciliator decide; the interview runs in the owner's session, where the key never is.
2. **Whether the manager reads a Gemini brief.** Recommended: no. Each double is posted beside the role's brief on the PR, and the owner compares them. Gemini's text never enters a Claude prompt (the study check, row 8). The Gemini job also runs after the phase job, while the manager runs inside it.
3. **The panel (decision 21).** Recommended: a review after the fact, one call per "Decision taken for you", at most `gate.max_panel_calls`, on Argon (the check, row 4), posted before the owner's gate. The conciliator's decision stands, and the owner overturns as today. A live third voice would need the key inside the session, or Gemini's text in the conciliator's prompt.
4. **What "shows its cost" means.** Recommended: the measured tokens, plus a USD estimate from a dated per-model price table in the plugin, labelled as an estimate, and the change's Gemini total on the PR.
5. **The `sdlc.yaml` shape.** Recommended: one key per double, in R7's shape, under `external_review`. Today's `{model, phases}` reads as the Architect and Code reviewer doubles until it is migrated.
6. **The decision's form.** Recommended: one new decision that amends 21 with R28's own amendment (the role of a concern's kind replaces the general reviewer under deferred review) and the panel review above, as the check's row 4 asks. R28's part 0 then cites it for 21. R28 keeps its place in the order.

## Every open item
| Item | Where | What is left | Who acts | Blocks 1.0.0 |
|---|---|---|---|---|
| #335 | framework | Green checks, the owner's merge, then the tag | owner | no |
| The first live call and note 58 | sample, by hand | Billing on the sample key's project; Part 2 again (choice 256: at R8's turn) | owner; the session at R8's turn | no |
| The sample at 1.0.24 | sample | Copies in a sample PR; the owner's `sdlc.yaml` edits in full | the session at R8's turn; owner | no |
| Gemini in R28's roles | Part 3 above | The owner's answers, then the decision file, R28's annotations and a choice | the session at R8's turn; owner | no |
| `GITHUB_OUTPUT` in the session's environment | `plugin/ci/run_phase.py`, `session_env` | The review's finding 9 (#335's record): a stray heredoc could swallow `phase_ran` and the job would run as before 1.0.24 | the 1.0.0 read | no |
| A fix round runs no second opinion | `sdlc-fix.yml` | From the trace (#335's record): a design question for R8's tally | owner, at R8's tally | no |
| The Developer API's terms | `ai.google.dev/gemini-api/terms` | The owner's read (carried from the `ccr-6ed8a82e-cxmftx` end file) | owner | no |
| R8's tally | `docs/proposals/external-design-check.md` | No row until a live run (carried) | the session that reads the first one | no |
| The port list | `docs/PROGRESS.md` | #304's entries (carried); #335 touches `plugin/ci/run_phase.py` | the 1.0.0 read | no |
| Everything the part-5 file lists open | `2026-10-23-claude-r65-part-5-handoff.md`, "Every open item" (R65's part 6, #328 and the merge-tool deny rule, the sample's stale branch, and what it carries) | Carried, not re-verified | as there | no |

Done, dropped:
- "The pinned-below-1.0.19 job failure (defect 1)", "The fast lane's lost (b) opinion (defect 2)" and "The (e) job when phase (e) did not run" (the first file): #335.
- "R65's parts 4 and 5" (the first file): #329 and #334.
- "This PR" of the first file (#331): merged as `5357fdc`.
- "R62" (carried from the first file as unordered): ranked by choice 256; its status stays the owner's.

## What the owner does
| When | Act |
|---|---|
| Now | Merge #335 when `Framework checks` is green on its final head. |
| When R8's turn comes | Link billing to the sample key's Google project (the AI Pro credit, a $10 budget alert); start the session that runs Part 2 again and puts Part 3's questions. |
| Everything else | As the part-5 file's "What the owner does" lists it. |
