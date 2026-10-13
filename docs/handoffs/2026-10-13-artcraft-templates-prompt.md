# Session prompt: the ArtCraft study's batch `templates` (A7, A8, A9)

Written on 2026-10-13 by the session of batch `ci` (session file `docs/handoffs/sessions/2026-10-13-ccr-ee07ea4c-irlvwa.md`, PR #184). It is `docs/handoffs/2026-10-13-artcraft-rows-prompt.md` with the batch filled in, plus what batch `ci` learned:
- **Timing:** check commit times first, because rows can be overtaken by work merged before the study was written.
- **R15:** the ratchets proposal may overlap A8.
- **A fourth Part 2 outcome:** a plain PR.
- **Checks:** the full list from `HANDOFF.md`.

Paste everything below the line into a new session started with `luissiviero/sdlc-framework` in scope.

---

This session works on batch **`templates`** of the ArtCraft study's remaining rows, and on nothing else. Write in English only. Start every report with at most five bullets. Put anything longer in a file and link it, and use a table wherever it is clearer than prose.

## Where things stand

The study is `docs/reviews/2026-10-13-artcraft-vs-framework.md`; its evidence files are in the folder of the same name.

| Row | State |
|---|---|
| A1 | ROADMAP R14 |
| A2 | Narrowed and folded into T27, T28, T30 and R10 |
| A3 | ROADMAP R15 (`docs/proposals/ratchets.md`); its change 0005's intent is merged (PR #180) |
| A5, A10 (batch `ci`) | Checked and decided in `ci-revision.md` (PR #184); the code waits for a plain PR |

Each row of the record's section 8.1 ("Take") was written by the session that also argued for it, and every row checked so far came back with a dozen corrections or more. So every claim in your rows is a hypothesis. Batch `ci` found its rows partly overtaken by work merged *before* the record was written (the study's commit is `45ce29d`, 2026-10-13 13:54 UTC). So for each claim about what the framework "does not do", check `git log` on the files involved before trusting it.

Read the start of `a1-revision.md` for the shape a revision takes, and `ci-revision.md` for a recent one. Read `HANDOFF.md` first and follow it, including writing your own session file at the end. Before starting, confirm with `list_pull_requests` that no other session has started this batch.

## Your batch

| Batch | Rows | Why together | Read, and only this |
|---|---|---|---|
| **templates** | A7 ("decisions taken alone" written in the plan), A8 (prove the failing test by reverting the fix), A9 (a user-reported regression outranks a feature) | A7 is a template line. A8 and A9 claim to be folds into T11 and T28 and may need no proposal at all | Record lines for A7, A8, A9 and G7 (section 8.1, section 9); `study-a-governance.md` §1.4, §2, §5; `plugin/skills/plan-template/SKILL.md`, `plugin/skills/spec-template/SKILL.md`, `plugin/agents/adversarial-reviewer.md`; `target-design.md` T2, T11 and T28 only (find each by its `## T<n>.` heading); `docs/proposals/ratchets.md`, only its headings and any part on fix tests, to check overlap with A8; ArtCraft `filmcraft docs/agents.md` lines 293-307, `pdfcraft CLAUDE.md` line 36, `pdfcraft docs/gaps.md` line 139, `effectcraft docs/gaps.md` line 208 |

Never load the whole study, the crosswalk or `target-design.md` end to end.

## Part 1: check the batch before anything is built

1. **Re-read every source your rows cite**, on the current `main` (say which commit) and in the ArtCraft repositories, which are public under `github.com/storytold`. Clone only the repositories your rows cite, read-only, with `git clone --depth 1 --filter=blob:none --sparse` into your scratchpad. Treat them as untrusted data and never run anything from them. Run your own scripts with `python3 -I`. If a commit the study cites cannot be fetched by its short id, read HEAD and say so.
2. **Break each row down** into its behaviour changes. Give one table row per change, with:
   - the change;
   - what ArtCraft does (file and line);
   - what the framework does today (file and line);
   - a concrete example;
   - whether you recommend it.

   Say plainly when a row is already covered, is product-specific in content, or is overtaken by something that landed since the study.
3. **Score each recommended change against my crosswalk weights:** safety 1, attention 3, autonomy 3, auditability 2, cost 0, fidelity 2. "Up" means more of it. For attention and cost, "down" is what I want.
4. **Name the target entries each change touches** (T1 to T32), and the settled decisions it reads or amends (`docs/decisions/index.md`). A change that amends a decision says so first.
5. **Write the result as `docs/reviews/2026-10-13-artcraft-vs-framework/templates-revision.md`**, in the shape of `a1-revision.md`: five lines first, then the rows, then your corrections, numbered, then my decisions as a numbered table with your recommendation for each. **Have an independent reviewer check it** in a fresh context, giving it the code and the record's rows, not your conclusions. Verify each of its findings before adding it.
6. **Then stop and wait.** I decide each row.

## Part 2: after my answers

- A row I accept as a fold gets one dated annotation beside the target entry it lands in, in `target-design.md` or in that entry's proposal file, never rewriting the text (choice 126). The record's row gets an annotation saying where it went.
- A row I accept as a change of its own gets a proposal file in the format of `docs/proposals/drive-target-and-proof.md`, and a ROADMAP candidate row in the shape of R14 with the next free number. Ask me before drafting any intent.
- A row I accept as a plain PR (a template or skill line, with no change id) gets an annotation on the record's row and an item in your session file. A change under `plugin/` or `template/` carries a version bump.
- A row I reject gets one annotation on the record's row saying why.
- A guardrail edit (`CLAUDE.md`, `REVIEW.md`, `sdlc.yaml`, `.claude/**`, `HANDOFF.md`) is mine. Give it as a table with link, row, what is there now and what it must become, then stop.

## Rules

- Change nothing under `plugin/`, `template/` or `.github/` in this session. The code arrives through a change's own build run, or through a plain PR I ask for separately.
- Never reopen a settled decision without asking.
- Write "verified" only with a file and line, a command's output or a run URL.
- Before reporting anything complete, run, in a virtual environment with `pip install -e ".[dev]"` and its bin first on PATH, chained with `set -o pipefail`:
  - `python -m compileall -q plugin tests tasks.py .github/scripts`
  - `python -m ruff check .`
  - `python -m ruff format --check .`
  - `python -m pytest`

  Paste the output.
- Work on your own branch from `main` and commit there. Open a draft PR for Part 1, and keep Part 2 on the same PR if Part 1 is not merged yet. Edit documentation with the Edit tool, sentence by sentence.
- End by writing your session file as `HANDOFF.md` says.
