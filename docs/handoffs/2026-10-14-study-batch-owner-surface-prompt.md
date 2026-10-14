# Session prompt: the playbook study's next proposal batch, the owner's surface (T17, T19, T27, T28)

Written on 2026-10-14 by the session on branch `ccr-5c89bfa5-v2zq2a`, at the owner's request, after plugin 1.0.0 merged (PR #199) and before Part 3 of item 11 ran. It follows the close of the study (`docs/reviews/2026-09-28-playbook-vs-framework.md`, section 8, part 2) and the first batch (R11 to R13, PR #156). It adds what has happened since:
- **The ArtCraft notes:** they are folded into these four entries and must reach their proposals.
- **The code these entries rest on:** it moved at 1.0.0.
- **ROADMAP:** Part 3 of item 11 has a claim on it.

Paste everything below the line into a new session started with `luissiviero/sdlc-framework` in scope.

---

This session writes the playbook study's next proposal batch, the owner's surface: **T17, T19, T27 and T28**, and nothing else. Write in English only. Start every report with at most five bullets. Put anything longer in a file and link it, and use a table wherever it is clearer than prose.

## Before anything else: may this session start?

Read `HANDOFF.md` first and follow it, including the session file you write at the end. Then check these three things and report them in one table, with the evidence for each:

| Check | Start only if |
|---|---|
| Part 3 of item 11 | Its PR that closes ROADMAP's 1.0.0 tables is merged. Until then Part 3 is the only session that edits `docs/ROADMAP.md` (`docs/handoffs/sessions/2026-10-14-ccr-5b7d20dc-ot5xgy.md`, D-C), and choice 181 holds this batch until after the 1.0.0 read. |
| Open PRs | No open PR changes `docs/ROADMAP.md` or `docs/reviews/2026-09-28-playbook-vs-framework/target-design.md`, and no PR has started this batch (`list_pull_requests`, every state, the 20 newest). |
| The next free R number | Read the last row of ROADMAP's candidates table. R16 is item 11's `detect-local-day.md`, so this batch expects **R17 to R20**. Use whatever is free when you start. |

If any check fails, stop and tell me what blocks you. Do not work around it.

## What the batch is, and why these four

The study closed on 2026-10-09 with 32 confirmed entries. Each becomes a proposal file and a ROADMAP candidate row, a few per PR, in study-only sessions (the record's section 8, part 2). So far:
- **The first batch (PR #156):** R11 (T32), R12 (T12) and R13 (T21).
- **T10:** already R10.
- **From the ArtCraft study:** R14 and R15.

This batch is the owner's surface. T28's digest and T27's blocks are where every later entry's lines land, and these four reduce my reading the most (`docs/handoffs/2026-10-13-study-line-start-table.md`, row 2a). Four entries, one PR, one proposal file each (row 2c).

## Read, and only this

- **The record:** `docs/reviews/2026-09-28-playbook-vs-framework.md`, sections 7 (first bullet) and 8 (part 2, the proposal format). Never load the record, the crosswalk or `target-design.md` end to end.
- **`target-design.md`:** T17, T19, T27 and T28 only (find each by its `## T<n>.` heading), the index table's rows for them, and the entries they lean on only where a point needs them (T1, T4, T10, T15, T18, T20 to T26, T30, T32).
- **`crosswalk.json`:** only the rows each entry names under "Crosswalk rows it touches".
- **The article:** `docs/reference/ai-native-sdlc-playbook.txt`, cited by PDF page. Check each page against the PDF before you cite it.
- **The proposal format:**
  - `docs/proposals/approvals-list.md` and `docs/proposals/release-label-same-visit.md`, for the shape and the frontmatter;
  - `docs/proposals/drive-target-and-proof.md`, for R14's Proof line, which T27 carries.
- **The ArtCraft notes** (read the dated annotations beside each entry's status first):
  - `docs/reviews/2026-10-13-artcraft-vs-framework.md`, rows A2 and A9 only;
  - `templates-revision.md` E6;
  - `planning-revision.md` P4, only if T30 comes up.
- **The code on the current `main`**, cited by file and line, at the commit you name:

| Entry | Code |
|---|---|
| T17 | `plugin/ci/fix_requests.py`, the `sdlc-fix.yml` template, `plugin/commands/sdlc-fix.md` |
| T19 | `plugin/ci/run_phase.py` (the triage phase), `plugin/release/notes.py` |
| T27 | `plugin/pr/description.py` (`GATE_CHECKLIST`, `_owner_line`) |
| T28 | `plugin/pr/digest.py`, the `sdlc-digest.yml` template |

## What changed since the entries were written: check these first

| What | Why it matters |
|---|---|
| **1.0.0 changed `plugin/pr/description.py` and `plugin/release/notes.py`** (item 11's G1, PR #199) | T27 builds on the first file and T19 on the second. Re-read both at the current `main` (`git diff v0.3.7 origin/main -- plugin/pr plugin/release`); do not reuse the entries' line numbers. |
| **T27 carries two ArtCraft notes** | R14's per-item Proof line (A1, R14's second change, built with T27). A2: a model judgment shown beside measured lines is labelled as a judgment. Both go in the proposal's body, not only in its sources. |
| **T28 carries two ArtCraft notes** | A2's label, as above. A9's E6: within "Parked" and within "Waiting at a human gate", PRs labelled `incident` come first, because today `digest.py` sorts waiting PRs by phase letter and lists an incident intent last. |
| **R13 already puts a waiting or failed release in the digest** | T28's "releases waiting for their label" line is R13's. Point to it; do not propose it twice. |
| **T17 amends decision 22** (one trigger added beside the "Request changes" review) | Say so first in the proposal. The decision file is written before the intent, in a PR of its own, as R12's and R10's were. This session writes no decision file. |
| **T19 and T28 lean on entries that have no proposal yet** (T18's merge workflow; T15, T20, T22, T23, T25 and T26's digest lines) | For each point, say whether it can be built now or arrives with its own entry, as R13 did for T18. |
| **Part 3 of item 11 reads the first real digest that lists an incident** (sample PR #60) | Before writing T28, read what Part 3 recorded about that digest, if it is on `main`. Cite it, or say it was not yet there. |

Every claim in an entry is a hypothesis until you have re-read its source on the current `main`. The ArtCraft study found a dozen corrections or more in every row it checked. Before you write that the framework "does not do" something, check `git log` on the files involved.

## Part 1: write the four proposals

1. **One file per entry** under `docs/proposals/<slug>.md`, in the format of section 8, part 2:
   - the frontmatter: `type`, `title`, `description`, `status: proposed`, `roadmap: Rn`, `sources` with the entry, the crosswalk rows and the article pages, and `generated`;
   - the sections section 8 lists: the problem; what the article says, by page; what the framework does today, by file and line at the `main` you name; the proposal; considered and not chosen; the decisions it touches, naming the decision file to write first where it amends one; open (from the entry's "Open"); and what it would take. R11 to R13 add "How it is judged" and "Order"; keep those too.

   The entry's text is the source. Condense it by hand, never by a script, and never change what I decided.
2. **One candidate row per file** in ROADMAP's candidates table, in the shape of R11 to R13, with the next free numbers:
   - Source: the file, the entry and the crosswalk rows.
   - Decisions it touches: as the proposal says.
   - Status: "proposed from the study (2026-10-09)".
   - Order: blank. The Order column is mine (`docs/reviews/2026-10-13-artcraft-vs-framework/planning-revision.md`, P1, accepted 2026-10-14).
3. **Write the R number back** beside each entry's status in `target-design.md` and in its index row. Add these as annotations, as the first batch did (choice 126).
4. **Have an independent reviewer check each file** in a fresh context. Give it the entry, the article and the code, not your conclusions. Verify each of its findings before applying it, and list them, numbered, with what you did about each.
5. **Open a draft PR** with the four files, the four rows and the annotations. Run the checks (below) and paste their output in the PR body.
6. **Then stop and send me a decision table**, one row per proposal:
   - the options: accept now; accept later, naming what it waits for; or drop;
   - where it would sit in the Order column;
   - your recommendation, scored against my weights (safety 1, attention 3, autonomy 3, auditability 2, cost 0, fidelity 2; for attention and cost, "down" is what I want);
   - the settled decisions it amends.

   Wait for my answers.

## Part 2: after my answers

- **An accepted proposal:** set the row's Status to "accepted <date>", and put my Order in the Order column. Add a dated annotation beside the entry's status in `target-design.md`.
- **A dropped proposal:** one annotation on its row and beside the entry, saying why.
- **A decision amendment I accept (T17 and decision 22):** an item in your session file, "a decision file before the intent". It is not written here.
- **Keep Part 2 on the same PR** if Part 1 is not merged yet.

## Rules

- Change nothing under `plugin/`, `template/`, `.github/` or `docs/decisions/`. Draft no intent.
- Never reopen a settled decision without asking.
- Guardrail edits are mine: `CLAUDE.md`, `REVIEW.md`, `sdlc.yaml`, `.claude/**`, `HANDOFF.md`. Give each as a table with the link, the row, what is there now and what it must become, then stop.
- Write "verified" only with a file and line, a command's output or a run URL.
- Before reporting anything complete, run the checks in a virtual environment with `pip install -e ".[dev]"` and its bin first on PATH, chained with `set -o pipefail`:
  - `python -m compileall -q plugin tests tasks.py .github/scripts`
  - `python -m ruff check .`
  - `python -m ruff format --check .`
  - `python -m pytest`

  Paste the output.
- Work on your own branch from `main`. Edit documentation with the Edit tool, sentence by sentence.
- End by writing your session file as `HANDOFF.md` says. Its next steps name the next batch in the confirmed order (the record's section 8, part 2): the gate changes, T18, T23, T9, T30 and T31. I choose when it starts, so do not start it.
