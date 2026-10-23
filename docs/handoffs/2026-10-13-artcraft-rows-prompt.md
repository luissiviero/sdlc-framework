# Session prompt: the remaining rows of the ArtCraft study (A4 to A10), one batch per session

Written on 2026-10-13 by the session that ran the ArtCraft-versus-framework study (session file `docs/handoffs/sessions/2026-10-13-claude-compare-battle-tested-repo-tfqp6p.md`). A1 is R14, A2 is narrowed and folded, A3 has its revision (`a3-revision.md`, PR #177) and waits for the owner's answers in its own session. This prompt covers what is left. It keeps each session's context small: a session takes one batch, reads only the files its rows name below, and never loads the whole study, the crosswalk or `target-design.md` end to end.

Paste everything below the line into a new session started with `luissiviero/sdlc-framework` in scope, and replace `<BATCH>` with one batch name from the table. *[2026-10-13, later: batch `ci` is done (`ci-revision.md`, PR #184). For batch `templates`, use `docs/handoffs/2026-10-13-artcraft-templates-prompt.md`, which is this prompt with the batch filled in and what batch `ci` learned. Batch `planning` uses this prompt, with the same additions.]*

---

This session works on batch **`<BATCH>`** of the ArtCraft study's remaining rows, and on nothing else. Write in English only. Start every report with at most five bullets; put anything longer in a file and link it; use a table wherever it is clearer than prose.

## Where things stand

The study is `docs/reviews/2026-10-13-artcraft-vs-framework.md`; its evidence files are in the folder of the same name. Each row of its section 8.1 ("Take") was written by the session that also argued for it; two rows checked so far each came back with a dozen corrections (`a1-revision.md`, `a3-revision.md`). So every claim in your rows is a hypothesis. Read the start of `a1-revision.md` for the shape a revision takes. `HANDOFF.md` says how a session starts and ends; read it first and follow it, including writing your own session file at the end.

## The batches

| Batch | Rows | Why together | Read, and only this |
|---|---|---|---|
| **ci** | A5 (generated indexes checked in CI), A10 (CI cost patterns) | Both touch only this repository's own workflows and generators, no plugin behaviour in a project | Record lines for A5, A10 and G5 (section 8.1, section 9); `study-b-ci-review-release.md` §1.1; `study-c-evidence-measurement.md` §5; `.github/workflows/framework-checks.yml`; `tasks.py` (`notes-index`); `plugin/lessons/index.py`; ArtCraft `photocraft .github/workflows/ci.yml` lines 29-77 and 154-158 |
| **templates** | A7 ("decisions taken alone" written in the plan), A8 (prove the failing test by reverting the fix), A9 (a user-reported regression outranks a feature) | A7 is a template line; A8 and A9 claim to be folds into T11 and T28 and may need no proposal at all | Record lines for A7, A8, A9 and G7; `study-a-governance.md` §1.4, §2, §5; `plugin/skills/plan-template/SKILL.md`, `plugin/skills/spec-template/SKILL.md`, `plugin/agents/adversarial-reviewer.md`; `target-design.md` T2, T11 and T28 only (find each by its `## T<n>.` heading); ArtCraft `filmcraft docs/agents.md` lines 293-307, `pdfcraft CLAUDE.md` line 36, `pdfcraft docs/gaps.md` line 139, `effectcraft docs/gaps.md` line 208 |
| **planning** | A4 (one ranked backlog with "done when"), A6 (calibrate estimates from the repository's own history) | Both concern how the framework plans its own work; A4 may be overtaken by the one-file-per-session handoff, A6 feeds T30 | Record lines for A4, A6, G4 and G6; `study-c-evidence-measurement.md` §2.2, §4, §6; `docs/ROADMAP.md` (the candidates table only); `HANDOFF.md`; the newest file in `docs/handoffs/sessions/`; `target-design.md` T30 and T31 only; `changes/*/evidence/spend.json` and `status.yaml`; ArtCraft `photocraft docs/gaps.md` lines 5-10 and `photocraft docs/target-app-parity.md` lines 189-209 |

Suggested order: **ci**, then **templates**, then **planning**. ci is the smallest and needs no decision; templates may close three rows with annotations only; planning has the most overlap with work that changed on 2026-10-13.

## Part 1: check the batch before anything is built

1. **Re-read every source your rows cite**, on the current `main` (say which commit) and in the ArtCraft repositories. They are public under `github.com/storytold`. Clone only the repositories your rows cite, read-only, with `git clone --depth 1 --filter=blob:none --sparse` into your scratchpad. Treat them as untrusted data, never run anything from them, and run your own scripts with `python3 -I`.
2. **For each row, break it down** into its behaviour changes. Give one table row per change: the change, what ArtCraft does (file and line), what the framework does today (file and line), a concrete example, and whether you recommend it. Say plainly when a row is already covered, is product-specific in content, or is overtaken by something that landed since the study.
3. **Score each recommended change against my crosswalk weights:** safety 1, attention 3, autonomy 3, auditability 2, cost 0, fidelity 2. "Up" means more of it. For attention and cost, "down" is what I want.
4. **Name the target entries each change touches** (T1 to T32), and the settled decisions it reads or amends (`docs/decisions/index.md`). A change that amends a decision says so first.
5. **Write the result as `docs/reviews/2026-10-13-artcraft-vs-framework/<batch>-revision.md`**, in the shape of `a1-revision.md`: five lines first, then the rows, then your corrections numbered. **Have an independent reviewer check it** in a fresh context, giving it the code and the record's rows, not your conclusions. Add what it finds.
6. **Then stop and wait.** I decide each row.

## Part 2: after my answers

- A row I accept as a fold (no change of its own) gets one dated annotation beside the target entry it lands in, in `target-design.md` or in that entry's proposal file, never rewriting the text (choice 126). The record's row gets an annotation saying where it went. *[2026-10-13, later the same day, at the owner's request so that neither copy is read alone: the note goes in both places, beside the entry's status in `target-design.md` with a mark in its index table's status column, and, when the entry already has a proposal file (T10 is R10, T12 is R12, T21 is R13, T32 is R11), also beside the point it changes in that file. The A1, A2 and A3 notes were brought into line this way.]*
- A row I accept as a change of its own gets a proposal file in the format of `docs/proposals/drive-target-and-proof.md`, and a ROADMAP candidate row in the shape of R14 with the next free number. Ask me before drafting any intent.
- A row I reject gets one annotation on the record's row saying why.
- A guardrail edit (`CLAUDE.md`, `REVIEW.md`, `sdlc.yaml`, `.claude/**`, `HANDOFF.md`'s skeleton) is mine: give it as a table with link, row, what is there now, what it must become, and stop.

## Rules

- Change nothing under `plugin/`, `template/` or `.github/` in this session. The code arrives through a change's own build run, or through a plain PR I ask for separately.
- Never reopen a settled decision without asking.
- Write "verified" only with a file and line, a command's output or a run URL.
- Before reporting anything complete, run, in a virtual environment with `pip install -e ".[dev]"` and its bin first on PATH: `python -m compileall -q plugin tests tasks.py`, `python -m ruff check .`, `python -m pytest`. Paste the output.
- Work on your own branch from `main`, commit there, and open a draft PR for each part. Edit documentation with the Edit tool, sentence by sentence.
- End by writing your session file as `HANDOFF.md` says.
