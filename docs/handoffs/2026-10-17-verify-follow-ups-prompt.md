# Starting prompt: verify the item-11 follow-ups session's records and analysis (2026-10-17)

Paste everything below the line into a new session started with **both** `luissiviero/sdlc-framework` and `luissiviero/sdlc-sample-python` in scope.

---

You verify the work of session `ccr-f21be30b-5d5dpz` (session_01CNjpVWeFL5wkg8xaCoBXys, the item-11 follow-ups), which the owner is closing. Your job is to make sure every claim it left is right before the owner merges. Write in English only. Start every report with at most five bullets, and use a table wherever it is clearer than prose.

## Before anything else
1. Read `HANDOFF.md` and follow it. Read `docs/handoffs/sessions/2026-10-17-ccr-f21be30b-5d5dpz.md` in full, with its last section "After #221 merged", then `docs/handoffs/sessions/2026-10-15-ccr-01de3f80-ilnomi.md` and any session file newer than both.
2. **Schedule the owner's reminder with `send_later`** (`initiation: human_request`), because the closed session's reminder was cancelled: at **2026-10-21 11:55 UTC**, remind the owner, in one message: on the PC, in the local `sdlc-framework` clone, run `git pull`, then `python -m pip install -e ".[dev]"`. Deliver it when it fires; nothing else.

## What to verify
Every claim is a claim until you check it against its source: a run URL, a file and line at the commit named, or command output. For each item, report **right**, **wrong (what is right, with the source)** or **not verifiable (why)**.

| # | What | Where it is written | Check against |
|---|---|---|---|
| 1 | NOTES §45, every fact: run IDs, commits, times, counts, costs (56.30 USD total; 42.88 USD for the seven fix rounds), the six fix rounds' table, the sample's detect run of 2026-10-15 | `docs/notes/45.md` (merged in PR #221) | The runs and jobs (GitHub Actions), `git log`, `changes/0005-dropped-tests-and-eval-cases-are-gate-fi/evidence/` at `807c5f6` |
| 2 | The eight gaps, each traced to code: the file and line, and whether the code at `807c5f6` really behaves as stated (for example `_approved_config` returning `{}` on a parse error; `check_panel` not reading the decision; `rerun_reason` refusing a re-run when a PR is open; `sdlc_tag.py` not reading `marketplace.json`) | NOTES §45, "The gaps" | The code at `807c5f6`; reproduce what a test can show, in a scratch copy (never push code) |
| 3 | The owner's choices 197 to 202 match what happened, and the numbers do not collide with any other record | `docs/PROGRESS.md` | The PRs (#186, #211, #213, #214, #216, #217, #218), `docs/progress/`, `docs/decisions/` |
| 4 | The 1.0.1 record was moved unchanged | `docs/progress/2026-10-14-1.0.1.md` | `git show 807c5f6:docs/PROGRESS.md`, compared byte for byte |
| 5 | The gap-to-ROADMAP mapping: that R10, R48, R5 and decision 32 really cover what the table says, and that no other candidate (R1 to R49) already covers gap 1, 2, 3, 4, 6, 7 or 8 | The session file's section "After #221 merged" | `docs/ROADMAP.md`, `docs/proposals/`, `docs/decisions/30.md` to `33.md`, PR #220's branch `ccr-01de3f80-ilnomi` |
| 6 | The claims about PR #220: it merges cleanly onto `main`; it takes 1.0.3; it already tells a fix round it cannot run the targets; it does not guard a round that ends without a commit or with a question | The same section | `git merge-tree` against the current `main`, the branch's `plugin/ci/auto_round.py`, `plugin/ci/run_phase.py`, `plugin/commands/sdlc-fix.md` |
| 7 | The open items carried from the three earlier session files are complete: nothing dropped without a line saying where it was done | The session file's "Every open item" and its last section | `2026-10-14-ccr-4a548fe6-7cqzlo.md`, `2026-10-14-ccr-03233066-k1441l.md`, `2026-10-14-ccr-20b39ad0-kcymdd.md`, `2026-10-15-ccr-01de3f80-ilnomi.md` |
| 8 | The two corrections the session file names in other files are right | The session file | The files and sentences named |

## Where you work: the same PR
- **The owner wants one PR, not a new one:** push your corrections to the branch **`ccr-f21be30b-5d5dpz`**, the branch of the open docs PR this session left ("docs(follow-ups): after #221 — the gaps mapped onto ROADMAP's Order …"). If your environment assigns you a different branch, tell the owner and ask before pushing anywhere.
- Correct a record by annotating beside the sentence, never by rewriting it (choice 126). A wrong fact in NOTES §45 gets a dated annotation in `docs/notes/45.md` and, if it moves a figure, the evidence beside it. Edit docs with the Edit tool, sentence by sentence.
- Add your own session file at the end (`HANDOFF.md`, "How a session ends"), in the same PR.
- **Read only:** PR #220 and its branch belong to another session; report on them, never push to them or comment on them. Do not touch the sample.
- Guardrail files (`CLAUDE.md`, `REVIEW.md`, `sdlc.yaml`, `.claude/**`, and the sample's `bands.yaml` and `sdlc.yaml`) are the owner's: any edit to them is given as a table (link, row, what is there now, what it must become).

## When you are done
1. Run `HANDOFF.md`'s standing precondition 1 on the final head and paste the output.
2. Report to the owner in one table: each of the eight checks above, its verdict, and what you changed.
3. Say plainly whether the PR is safe to merge (every `Framework checks` job green on the final head, the branch up to date with `main`), and what the owner must decide next: the gaps' routes, and whether to raise gaps 3 and 4 with PR #220's session before #220 merges.
