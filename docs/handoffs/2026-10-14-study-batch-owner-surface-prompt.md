# Session prompt: the playbook study's next proposal batch, the owner's surface (T17, T19, T27, T28)

Written on 2026-10-14 by the session on branch `ccr-5c89bfa5-v2zq2a`, at the owner's request, after plugin 1.0.0 merged (PR #199); Part 3 of item 11 opened PR #202 the same day. It follows the close of the study (`docs/reviews/2026-09-28-playbook-vs-framework.md`, section 8, part 2) and the first batch (R11 to R13, PR #156). Four independent reviewers checked it against the repository before it merged; their verified findings are folded in. It adds what has happened since the entries were written:
- **The ArtCraft notes:** folded into T27 and T28 (T17 and T19 carry none). They must reach the proposals.
- **Decisions 28 and 29** (accepted 2026-10-13) and **proposals R10 to R16**: several already settle or carry points of these four entries.
- **ROADMAP:** Part 3 of item 11 has a claim on it until its PR merges.

Paste everything below the line into a new session started with `luissiviero/sdlc-framework` in scope.

---

This session writes the playbook study's next proposal batch, the owner's surface: **T17, T19, T27 and T28**, and nothing else. Write in English only. Start every report with at most five bullets. Put anything longer in a file and link it, and use a table wherever it is clearer than prose.

## Before anything else: may this session start?

Read `HANDOFF.md` first and follow it, including the session file you write at the end. Many session files share the date 2026-10-14, so sorting by name does not find the newest one. The newest is the one whose header builds on the others. Expect it to be the item-11 session's `2026-10-14-ccr-4a548fe6-7cqzlo.md` (Part 3) or a later one; read it, `2026-10-14-ccr-5b7d20dc-ot5xgy.md` and `2026-10-14-ccr-5c89bfa5-v2zq2a.md`, and skim the others only for open items.

Then check these three things and report them in one table, with the evidence for each:

| Check | Start only if |
|---|---|
| Part 3 of item 11 is closed | On `main`, `docs/ROADMAP.md`'s Milestone 1 row 15 ("This page: 'reached on <date>, `v1.0.0`', the tables closed") has its Done cell filled, and the page says "reached on <date>, `v1.0.0`". The PR expected to do this is #202 ("Item 11, Part 3"); if it was renumbered or split, the row on `main` is the test. Until then that PR carries ROADMAP's annotations (D-C in `docs/handoffs/sessions/2026-10-14-ccr-5b7d20dc-ot5xgy.md`), and choice 181 (`docs/progress/session-25.md:18`) holds this batch until after the 1.0.0 read. |
| No overlap | No open PR changes `docs/ROADMAP.md` or `docs/reviews/2026-09-28-playbook-vs-framework/target-design.md` (read every open PR's file list), and no PR of any state has started this batch (`search_pull_requests` in this repository for `T17`, `T19`, `T27`, `T28` and `owner-surface`). |
| The next free R number | Read the last row of ROADMAP's candidates table. R16 is `docs/proposals/detect-local-day.md`, so this batch expects **R17 to R20**. Use whatever is free when you start. |

If any check fails, stop and tell me what blocks you. Do not work around it.

## What the batch is, and why these four

The study closed on 2026-10-09 with 32 confirmed entries. Each becomes a proposal file and a ROADMAP candidate row, a few per PR, in study-only sessions (the record's section 8, part 2). So far:
- **The first batch (PR #156):** R11 (T32), R12 (T12) and R13 (T21).
- **T10:** already R10.
- **From the ArtCraft study:** R14 and R15.

This batch is the owner's surface. T28's digest and T27's blocks are where every later entry's lines land, and these four reduce my reading the most (`docs/handoffs/2026-10-13-study-line-start-table.md`, row 2a). Four entries, one PR, one proposal file each (row 2c).

## Read, and only this

Never load the record, the crosswalk, `target-design.md` or `plugin/ci/run_phase.py` end to end.

- **The record:** `docs/reviews/2026-09-28-playbook-vs-framework.md`, section 7 (first bullet) and section 8 (part 2, the format and the confirmed order). Find them with `grep -n`.
- **`target-design.md`:** the four entries whole, with every dated annotation and "Open" (find each by its `## T<n>.` heading), and their index rows. Other entries only where a point needs them; those named in the four entries are T1, T4, T5, T6, T7, T10, T15, T18, T20 to T26, T30 and T31.
- **`crosswalk.json`** (about 4.5 KB per row): read the primary row of each entry whole (T17 deploy-comments, T19 deploy-ci, T28 x-queue; T27 has no row of its own), and only the `decision` and `target` fields of the other rows an entry names, extracted with a short `python3 -I` script into your scratchpad. A row's `status: tentative` is its save date, not a contradiction; the entry's status is the confirmed one.
- **The article:** `docs/reference/ai-native-sdlc-playbook.txt`, cited by PDF page through its `===== PAGE n =====` markers. Open the PDF only where a quote is ambiguous.
- **The decisions:** `docs/decisions/index.md`, then 11, 20, 22, 24, 26, 28 and 29.
- **The proposals these entries meet:** R10 `test-loop-closes-in-ci.md`, R11 `approvals-list.md`, R12 `build-test-approvals-label.md`, R13 `release-label-same-visit.md`, R14 `drive-target-and-proof.md`, all under `docs/proposals/`. R11 to R13 are also the shape to copy.
- **The ArtCraft notes:** `docs/reviews/2026-10-13-artcraft-vs-framework.md`, rows A1 (its 2026-10-13 annotation only), A2 and A9, and gap G3; `templates-revision.md` E6; `planning-revision.md` P4 only if T30 comes up.
- **The code on the current `main`**, cited by file and line at the commit you name. In `run_phase.py`, open only the regions around `grep -n` hits.

| Entry | Code |
|---|---|
| T17 | `plugin/ci/fix_requests.py`; `template/.github/workflows/sdlc-fix.yml`; `plugin/commands/sdlc-fix.md`; `plugin/pr/github.py` (`issue_comments`, the review readers); `run_phase.py` (`dispatch_head`, the fix-branch lookup); `plugin/detect/cli.py` `_human_label_actor` (today's person-not-bot actor check); `plugin/gate/policy.py` (`is_automation`); NOTES §29 (GitHub refuses "Request changes" on one's own PR) |
| T19 | `run_phase.py` (`run_triage`, `RUNNABLE`, `TRIAGE_ALLOWED_TOOLS`, `commands_env`, `park_deferred_record`, `hand_over`, and what `main` passes to the triage run); `plugin/release/notes.py`; `plugin/commands/sdlc-deploy.md` (where the notes are written); `template/.github/workflows/sdlc-deploy.yml` (the review step's fresh checkout); `plugin/gate/gate.py` (`write_deferred_logs`) |
| T27 | `plugin/pr/description.py` (`GATE_CHECKLIST`, `_owner_line`, `RELEASE_APPROVAL_LINE`); `plugin/pr/digest.py` `_line`; `plugin/detect/runbooks.py` and `plugin/detect/cli.py` (the runbook and dismissal PR bodies); `plugin/state/cli.py list` |
| T28 | `plugin/pr/digest.py`; `template/.github/workflows/sdlc-digest.yml` (no inputs; `permissions` holds no `actions`); `run_phase.py` (`NEXT_WORKFLOW`, `dispatch`, `hand_over`); `plugin/pr/github.py` `pinned_issue`; `plugin/pr/counters.py`; each workflow template's `permissions` |

## What changed since the entries were written: check these first

Every claim in an entry is a hypothesis until you have re-read its source on the current `main`. The ArtCraft study found twelve to twenty corrections in every batch it checked. Before you write that the framework "does not do" something, check `git log` on the files involved.

**The code.** The entries were last re-checked against `main` `619f01a` (plugin 0.3.5, 2026-10-07). Since then, `run_phase.py` changed in 0.3.6 and 0.3.7 (about 280 lines; 0.3.7 added `dispatch_head`, which a dispatch with no head branch uses); 1.0.0 changed only `_first_sentence` in `plugin/pr/description.py` and `plugin/release/notes.py` (item 11's G1). `GATE_CHECKLIST`, `_owner_line`, the notes' section layout and `plugin/pr/digest.py` are unchanged since 0.3.7. So run `git diff 619f01a origin/main -- plugin/ci plugin/pr plugin/release template/.github/workflows` and re-read every place an entry cites; where a cited line still holds (T28's `digest.py:91-96` and `:141`), say so.

**Per entry, what already exists or is already settled.** Each row below was verified on 2026-10-14; re-read its source before you rely on it.

| Entry | Point | Where it stands |
|---|---|---|
| T17 | It amends decision 22 (one trigger beside the "Request changes" review) | Say so in the line under the title, as R13's opening paragraph does, and again under "Decisions it touches". The decision file comes before the intent, in a documentation PR I review on its own, never with the intent: decision 27 rode PR #162 with the study-line answers, and 28 and 29 shared PR #168. This session writes no decision file, and reserves no decision number. |
| T17 | The record of a round the `@claude` comment starts | R11 already carries it: point 3 of `approvals-list.md` ("the owner's review or `@claude` comment with its link (T17)"). T17 points to R11 and proposes no record of its own. |
| T17 | How a workflow knows the owner's account | R12 defers it to T17, T18 and T24 (`build-test-approvals-label.md`, "Who may apply the label"). Today the review path checks the author's association (`sdlc-fix.yml`) and `sdlc:go` checks person-not-bot (`_human_label_actor`). Settle it, or carry it explicitly with T18 and T24, and say whether the "Request changes" path becomes owner-only. A key in `sdlc.yaml` would be my guardrail edit. |
| T17 | Decisions 28 and 29 postdate the entry | The comment is a trigger, never a verb: it waives and accepts nothing (decision 24 moved the verbs to labels, decision 28 rejected a comment verb). Its round shares decision 29's one iteration counter and T30's one reset at the cap, unless the proposal argues otherwise. |
| T17 | "No more manual dispatch" | It replaces the owner's by-hand `workflow_dispatch`, not the trigger itself: R10's self-dispatched round and the runner's re-runs use `workflow_dispatch` (decision 29; `sdlc-fix.yml`). |
| T17 | The event and the comment's text | A PR conversation comment arrives as `issue_comment`, whose payload has no `pull_request.head.ref`; `sdlc-fix.yml` keys its concurrency group, checkout, `HEAD_REF` and `PR_NUMBER` on `github.event.pull_request.*`, so the head comes from the API. No note in `docs/notes/` covers `issue_comment` runs: mark that "to verify". The two-layer rule stays: the workflow's `if:` decides who starts a round, and `fix_requests.py` decides whose words reach it, reading the comment through the API as data. Its text never enters a `run:` line (`plugin/skills/security-baseline/SKILL.md`, rule 2), and the round never posts a comment or reply (`plugin/commands/sdlc-fix.md`, "Never post a PR comment, reply, review"; decision 20). Whether `@claude` collides with another GitHub App's trigger word on a project that installs one: unverified, a "considered" line at most. |
| T19 | Decision 29 postdates the entry | Rewrite the "park at the cap", "lost job" and "timed-out one" cases against it: a timeout starts a round; an infrastructure failure gets one automatic re-run, then parks; a missing target parks at once. |
| T19 | Where the "Failed runs" line comes from (its third "Open" point) | Answer it consistently with R13, which recommends a record the release step writes, read by the digest (`release-label-same-visit.md`, "What to settle"). The digest workflow holds no `actions` permission today. T19 defines the line and its sources (R13's release, T20's preview, T22's detection, T26's scan); T28 only places it. |
| T19 | Its first "Open" point (how a failed step's output is saved) | Partly answered by code: the runner already saves the session's result and stderr and the three target logs (`write_deferred_logs`). Only a setup or install step before the session and a failed checkout remain. The triage run receives the whole job environment today; `commands_env` is the precedent for narrowing it. |
| T19 | It leans on T18's merge workflow | Say per point whether it can be built now or arrives with T18, as R13 did. |
| T27 | R14's per-item Proof line (A1) | Read `drive-target-and-proof.md` sub-change 5 with its D6/D9 annotation: the per-item line comes with T27 as a second change, its outcome from the runner's record (never `verifier.md`), with a link at the head commit. The evidence line's "proof N, state items M of K matching" is R14's own first change, not T27's. T27 cannot sit before R14, which sits after R10. |
| T27 | A2: a model judgment shown beside measured lines is labelled as a judgment | T27's block is generated with no model run. The judgment beside it is T1's manager recommendation quoting it. |
| T27 | The release act at gate (e) | On a declared production the block uses R13's wording ("apply `sdlc:release-approved` with your approval"), not today's "after merging" (`RELEASE_APPROVAL_LINE`). |
| T27 | Which acts exist today | Say per act whether it exists now (merge, "Request changes", close with a comment, `sdlc:go`, the release label) or arrives with T17 (the `@claude` comment, this batch), T18, T23 or T24. The Full label is build-start's, not an entry. |
| T27 | The guide command | The name `/sdlc-guide` is provisional: T4, placed last, judges names. It needs a checkout, so whether it can run from claude.ai or the phone stays open. Say whether it reads R9 part 1's `changes/index.md` or each `status.yaml`. |
| T28 | A2's label | It applies to the manager's line in the summary (T1) and to T19's triage text in "Failed runs". |
| T28 | E6 (ArtCraft row A9): incident PRs first | Within "Parked" and within "Waiting at a human gate", PRs labelled `incident` come first; parked stays above waiting; a ticket's regression joins the key only when T6 labels tickets. Today only the waiting list is sorted, by phase letter (`digest.py:141`), so an incident intent at `sdlc:f-ready` is listed last; parked PRs keep GitHub's order. The live evidence: the sample's digest of 2026-10-14 (run 38560274588) listed #60 last under "Waiting at a human gate", recorded in NOTES §43 and in the session file of `ccr-5b7d20dc-ot5xgy`. Cite them, or say they are not on `main`. |
| T28 | Its "Open" item on how long an item has waited | Settled by T31's note (`target-design.md`, T31: "read from the gate record's `at`, or the pull request's creation at (a), which settles T28's open item"). Write it as settled and cite T31. The "line of history" item is shared with T31's own open item; say so. |
| T28 | Lines other proposals already put in the digest | R13's waiting or failed release; R11's "a line the step cannot write … shows in the daily digest" (`approvals-list.md`, point 6). Place them under "Worth knowing" and point to their proposals; do not propose them twice. |
| T28 | The refresh after every park or human gate | A runner change, not a digest change: today `hand_over` dispatches only on `continue` and only to the test and deploy workflows, always with inputs, and the digest workflow declares no inputs. Name in "Order" the runner, the dispatch, and the `actions` permission of every workflow that would refresh the digest. |
| T28 | What it leans on | T19's "Failed runs" and T27's "Next for you" (both in this batch); T15, T20, T22, T23, T25 and T26's lines; T24's cases that wait for Go; T30's limit parks; T1's recommendation line; T4's label names. Say per line whether it is built now or arrives with its entry. The "no ping" paragraph builds nothing: it restates decision 26 as T20 and T24 bind it. |
| T28 | Decisions | It writes no decision file: decision 20's "daily digest" becomes "refreshed at least daily", decision 11 and decision 26 are untouched, and the rejected option is decision 26's one notification. |
| T28 | The clocks | R16 moves the detection record's displayed times to the owner's offset, not the digest's (`digest.py` writes UTC). Say which clock each line uses. |

## Part 1: write the four proposals

1. **One file per entry** under `docs/proposals/<slug>.md`, in the shape of R11 to R13:
   - the frontmatter: `type: Proposal`, `title`, `description`, `status: proposed`, `roadmap: Rn`, `sources` (the entry, the crosswalk rows, the article pages, the decisions, the code), and `generated: { by: sdlc-framework-session/<your branch>, at: <UTC time> }`;
   - R11 to R13's nine headings, in their order, verbatim: The problem; What the article says; What the framework does today (naming the `main` commit and the plugin version from `.claude-plugin/plugin.json`); The proposal; How it is judged; What to settle before building (the entry's "Open" items as a Question / Recommended table, marking any another entry or decision already settled); Considered and not chosen; Decisions it touches; Order (where what it would take goes, as R14's does).

   The entry's text is the source. Condense it by hand, never by a script, and never change what I decided.
2. **One candidate row per file** in ROADMAP's candidates table, in the shape of R11 to R13, with the next free numbers:
   - Source: the file, the entry and the crosswalk rows.
   - Decisions it touches: as the proposal says.
   - Status: "proposed from the study (2026-10-09)".
   - Order: blank. The Order column is mine (`docs/reviews/2026-10-13-artcraft-vs-framework/planning-revision.md`, P1, accepted 2026-10-14).
3. **Write the R number back** in `target-design.md`, as PR #156 did for T12, T21 and T32:
   - in each entry's **Status** line, replace "; the proposal file and R number follow." with ". Proposal: `docs/proposals/<slug>.md`, ROADMAP Rn (written <date>)." and touch nothing else on the line (T27 and T28 keep their dated annotations);
   - in its index row, append "; Rn, `docs/proposals/<slug>.md`" to the status cell.
4. **Name the batch in the record**, as PR #156 did: one sentence at the end of section 7's first bullet and one in section 8's resume paragraph, each naming R17 to R20 (or the numbers you used), the four entries, the `main` commit and plugin version, and this PR; section 8's also names the next batch, the gate changes (T18, T23, T9, T30, T31). These are annotations (choice 126); nothing else in the record changes. The crosswalk rows' re-check against 0.3.8 and 1.0.0 (section 8's rule after a plugin release) is not this session's: write in your session file that it is owed.
5. **Have an independent reviewer check each file** in a fresh context. Give it the proposal file and its sources (the entry, the article pages, the code at the commit), not your reasoning. Verify each of its findings before applying it, and list them, numbered, with what you did about each, in the PR body.
6. **Open a draft PR** with the four files, the four rows, the `target-design.md` lines and the record's two sentences. Run the checks (below) and paste their output in the PR body.
7. **Then stop and send me a decision table**, one row per proposal:
   - the options: accept now; accept later, naming what it waits for; or drop;
   - where it would sit in the Order column, with its dependencies (T27 after R14; T28's lines after T19 and T27);
   - your recommendation, scored against my weights (safety 1, attention 3, autonomy 3, auditability 2, cost 0, fidelity 2; for attention and cost, "down" is what I want);
   - the settled decisions it amends.

   Wait for my answers.

## Part 2: after my answers

- **An accepted proposal:** if its row is still on this PR, set its Status to "accepted <date>"; if Part 1 merged first, leave "proposed from the study (2026-10-09)" standing and add `*[accepted by the owner on <date> (PR #n): …]*`, as R11 to R13 were (choice 126). Put my Order in the Order column, and add a dated annotation beside the entry's status in `target-design.md`.
- **A dropped proposal:** one annotation on its row and beside the entry, saying why.
- **A decision amendment I accept (T17 and decision 22):** an item in your session file, "a decision file before the intent". It is not written here.
- **Keep Part 2 on the same PR** if Part 1 is not merged yet.

## Rules

- Only `luissiviero/sdlc-framework` is in scope. The sample is read through the files on `main`, never touched.
- Change nothing under `plugin/`, `template/`, `.github/` or `docs/decisions/`. Draft no intent.
- Never reopen a settled decision without asking.
- Guardrail edits are mine: `CLAUDE.md`, `REVIEW.md`, `sdlc.yaml`, `.claude/**`, `HANDOFF.md`. Give each as a table with the link, the row, what is there now and what it must become, then stop.
- Write "verified" only with a file and line, a command's output or a run URL.
- Before reporting anything complete, run the checks in a virtual environment with `pip install -e ".[dev]"` and its bin first on PATH, chained with `set -o pipefail`:
  - `python -m compileall -q plugin tests tasks.py .github/scripts`
  - `python -m ruff check .`
  - `python -m ruff format --check .`
  - `python -m pytest`
  - `claude plugin validate .` (clean but for the root `CLAUDE.md` warning)

  Paste the output.
- Work on your own branch from `main`. Edit documentation with the Edit tool, sentence by sentence.
- End by writing your session file as `HANDOFF.md` says, committed on this same PR. If I have not answered the decision table in this session, put the table in the session file and leave the PR a draft. Its next steps name the next batch in the confirmed order (the record's section 8, part 2): the gate changes, T18, T23, T9, T30 and T31. I choose when it starts, so do not start it.
