# Handoff — session 15 and after: the 0.3.x line, while the sample's live check runs untouched

Sessions 9 to 14 (2026-09-26 to 2026-09-30) took the framework from the 1.0.0 readiness review to plugin **0.2.29**: the six *must fix* defects, the four follow-up groups, and the live checks that need no points (the sample at the 0.2.29 copies, a dispatched detect run, the tier-2 rehearsal, the runbook park). Between sessions 14 and 15 (2026-10-02, two sittings) the framework's first change through its own front door, **change 0001** (the docs split, R1's step 2), got its intent merged (PR #86) and its design run, which parked gate (b) on two flagged concerns and on one framework defect: **issue #91**, the gate's `commands` check runs inside Claude Code's sandbox, where `Read(**/.env*)` makes this repository's own fixture `.env` unreadable, so `python -m pytest` fails there and no framework change can pass gate (b). Its design PR #90 is open with `sdlc:needs-human`. The records: `docs/PROGRESS.md` "Change 0001" and "Between sessions 14 and 15, second sitting"; NOTES §24 and §25.

**The owner's decision of 2026-10-02, second sitting (PROGRESS, choices 135–139):** the framework does not wait for the sample's live check. The check keeps counting on the sample (sixteen daily points of its `CI` workflow since 2026-09-25; the sixteenth is 2026-10-10 and the first judging run 2026-10-11) and is read when it has filed; meanwhile this repository moves on a **0.3.x line**, starting with the fix of issue #91 in **0.3.0**. **1.0.0 keeps its meaning**: ROADMAP "How it is marked" still holds, the session that reads the first real detection bumps to 1.0.0. The brief this one replaces, with the full step lists for that read, is kept at `docs/handoffs/session-14-16-live-check-road.md`; its "Session 15" and "Session 16" are item 11 of the order below.

Each session ends by rewriting this file for the next one. Keep the owner's format for every guardrail edit: "link; row; what is there; what it needs to be".

## Preconditions — check before doing anything
1. **The session's GitHub scope holds both repositories** (NOTES §16, §17, §19–§26): the first act is one read of the sample, `actions_list` on `ci.yml` with `perPage: 100`, excluding the runs by `github-actions[bot]`, one point per UTC `created_at` day; write the count down (eight at 08:30 UTC on 2026-10-02, NOTES §24; every later day with a green scheduled run adds one). Nothing is written to the sample (precondition 6). Without the scope, session 15 can still do its work, which is on this repository alone; say so in the record.
2. `main` is at plugin 0.2.29 (`.claude-plugin/plugin.json`; `git ls-remote --tags origin | sort -V -k2` ends with `v0.2.29` — `-k2`, the SHA column sorts first otherwise, NOTES §17). The root `sdlc.yaml` pins 0.2.29 (line 98, PR #81) and the sample's `main` pins 0.2.29 (line 77, its PR #52); the sample's workflow copies and `.github/scripts/sdlc_pin.py` are the 0.2.29 ones (its PR #53).
3. `python -m pip install -e ".[dev]"` first (the dev tools are not in the container at start, NOTES §16); `python tasks.py check` green (1293 tests collected on 2026-10-02, second sitting, all green; the sitting changed no code) and `claude plugin validate .` clean. Since 0.2.28 the same check runs on every pull request on `ubuntu-latest` (Python 3.10 and 3.12) and `windows-latest` (3.12) (`.github/workflows/framework-checks.yml`): a red job on a PR is the PR's defect, and the Windows job is the suite's only Windows run — read all three before asking the owner to merge.
4. The permission mode: the auto-mode classifier refused a `git rm` on the sample and a push to a branch the session did not create (NOTES §22, §23). Session 15 works on this repository only, on its own branch; if a refusal comes, park with "what I need from you" as session 14's first sitting did.
5. Sub-agents named by model explicitly (`model: "opus"` for the fresh-context review of the diff; the split of MODEL_ALLOCATION §5d–§5h).
6. **The freeze of the sample (choice 138), until the first scheduled detect run after 2026-10-10 has filed:** nothing pushed to the sample and no PR opened on it, except the owner's provocation of 2026-10-10; its pin, its copies and its `bands.yaml` stay at 0.2.29; the tag `v0.2.29` never moved or deleted; a PR the weekly scan files there is left open or closed without a comment, never pushed to; no sample PR of any kind closed with a comment (a member's comment at the close writes a dismissal, choice 69). The root pin on line 98 is this repository's own and follows every tag. Every session until the read keeps, in its PROGRESS record, the list of its PRs that touch `plugin/detect/`, `plugin/ci/run_phase.py` or the detect, runbook and fix workflow templates: the port cost of the gaps the read finds.

## Read in this order
1. `docs/PROGRESS.md` "Between sessions 14 and 15, second sitting" — the decision, choices 135–139, the order table, what was read from the code; then "Change 0001" (issue #91, choices 133 and 134, the design run's facts) and "Session 14, second sitting" (the last live checks, choices 129–132).
2. `docs/ROADMAP.md` — Milestone 1 and its leftovers, "How it is marked" (unchanged in meaning; annotated), the path table with rows 9–15 annotated, the candidates R1–R4.
3. `docs/NOTES.md` §26 (the pin isolation, the detection's state across runs, read from the code), §24 (the sample's points, the design run, the sandbox defect), §23.
4. Issue #91 on this repository and NOTES §24's `commands` facts: the defect session 15 fixes.
5. `plugin/ci/run_phase.py` (where the gate runs and in which process the project's commands run), `plugin/gate/` (the `commands` check), `tests/test_ci.py` and the gate's tests — read before the fix is designed; `docs/OPERATING_MODEL.md` §3 (where the gate runs; which checks read the working tree).
6. `docs/reviews/2026-09-26-readiness-review.md` "ruled not a problem", so nobody reopens it; `docs/DECISIONS.md` (decision 6 on the deny rules: not to be loosened for #91, choice 133).

## Objective
Walk the order below from item 1. Session 15 is items 1–3: issue #91 fixed with a test, plugin **0.3.0**, the tag and the root pin. The owner's items 4 and 5 and the study's item 8 run whenever the owner wants; none blocks a session.

## The pending work, in order (choice 139)
| # | Item | Who | Version | Depends on | Detect path before the read? |
|---|---|---|---|---|---|
| 1 | Session 15 opens with the PROGRESS record of 2026-10-02 (second sitting) read; this file is its brief | Session 15 | — | — | no |
| 2 | Fix issue #91 (the runner runs the gate's commands after the model's session), a test, bump `plugin.json` and `marketplace.json` | Session 15 | **0.3.0** | 1 | yes, `plugin/ci/run_phase.py` |
| 3 | Merge; `v0.3.0` by `sdlc-tag.yml`; the root pin on line 98 as a guardrail row | Owner | — | 2 | no |
| 4 | Answer the four carried questions in one message: the `accept` verb, the Windows items (the watch setting, the test-file lock), the pin-bump trigger (choice 116), lessons sharing across projects (R1) | Owner | — | nothing | no |
| 5 | Apply R2's edit tables (`docs/proposals/session-tooling-pdf-web.md`, "What it would take" 1–3); a session then verifies once that `Read` opens the article PDF and records it in NOTES | Owner, then a session | no bump | nothing | no |
| 6 | The five study issues as one PR, a test each: #66 (a release can run twice, first on unreviewed code), #68 (a parked build PR merged at (e) releases silently), #67 (change 0000 gets a design run), #71 (`max_budget_usd` per session, not per change), #72 ("transcript" in the docs) | Session 16 | **0.3.1** | 3 | no |
| 7 | Change 0001: the "Request changes" review on PR #90 with choice 134's rules; the fix round re-runs gate (b) on 0.3.1; the owner merges #90; phase (c) the docs split, then (d); the owner merges | Session 17, owner merges twice | no bump | 3, 6 | no |
| 8 | The workflow study, a parallel track in study-only sessions (`docs/reviews/2026-09-28-playbook-vs-framework.md` §8 has the prompt): the housekeeping first (T4 onto the page and `crosswalk.json`, the seven row corrections of §7, the header to the current version), then the rows in order (setup-adopt, the Plan rows, Design, …) until all 48 are decided; the designv2 PDF check once item 5 is done | Study sessions; the owner decides each row | none until the study ends | 5 for the PDF | no |
| 9 | R1 on `lessons/`: frontmatter, a generated `index.md`, `status` and `stale_after`, links to the change and the eval case | Session 18 | **0.3.2** | 7 (the new layout); 4 for the sharing question | no |
| 10 | The provoked bad day: a sample PR with two failing tests before 23:59 UTC, closed without a merge afterwards (ROADMAP row 9; the rate it needs is in `docs/handoffs/session-14-16-live-check-road.md` "Session 15") | Owner, 2026-10-10 | — | the calendar | the check itself |
| 11 | Read the first scheduled detect run after it (ROADMAP row 10; the step list is the kept brief's "Session 15" and "Session 16", with 1.0.0 in place of their 0.2.29-era wording); triage; the gaps with a test each; the **1.0.0** bump in the same PR; `v1.0.0`; both pins; the sample's upgrade PR to the 1.0.0 copies with one dispatched run; the Milestone; ROADMAP closed. The `--bare` check rides along if `ANTHROPIC_API_KEY` is set on the sample | Session 19; the owner merges, pins and creates the Milestone | **1.0.0** | 10 | ends the freeze |
| 12 | R4: the owner's hook timing on the Windows PC (`docs/proposals/python-language-audit.md`, "The owner's check"), then its optional rows | Owner, then a session | only if `plugin/` changes | nothing | no |
| 13 | R3: a fresh clone for the second step of the shared-checkout jobs | A session | 1.0.x | 11 | yes, so after it |
| 14 | The study's confirmed entries (T1–T4) become proposals under `docs/proposals/` and candidate rows in ROADMAP, built as the first post-1.0.0 line | Sessions after the study | 1.x | 8, 11 | no |
| 15 | Optional, when a fix touches the files: the `Diff.files` conversion, the per-decision panel cost (choice 52), the release-page backfill for v0.2.15–v0.2.17, the sample's `sdlc.yaml` comment rows, the runner's `owner_fields` check on a real Windows console, the sample's ruleset with the Exempt bypass | any | — | — | no |

## Session 15 — issue #91 and plugin 0.3.0
1. Preconditions 1–6; the count of the sample's points written down.
2. **Reproduce before designing.** Read how `run_phase.py` runs the gate and in which process the project's `commands.*` run: NOTES §24 recorded the design run's `commands` check as `78 failed, 943 passed, 272 errors`, every one a `Permission denied` on `tests/fixtures/sample-python-project/.env`. Reproduce the mechanism in this container with a test that fails on the current order (the commands run from the model's session) and passes on the fixed one; the eval or the live run of change 0001's fix round (item 7) is the live proof later.
3. **The fix, as choice 133 chose it:** the runner runs the gate's `commands` check after the model's session, outside the sandbox, so the check reads the same working tree the session left and the gate record keeps its shape. Not chosen, and not to be reopened: renaming this repository's fixture (hides the defect; the rule matches at any depth) and narrowing the deny rule (loosens decision 6). If the fix touches a template workflow, the sample's copies diverge from the tag until item 11; that is expected under the freeze.
4. The bump: `plugin.json` and `marketplace.json` to **0.3.0**; the "since 0.2.x" comments stay. This is the only bump of session 15; nothing else under `plugin/` or `template/` is widened into it.
5. Every check chained on the exit codes: `python -m compileall -q plugin tests tasks.py .github/scripts`, the full `python -m pytest`, `python -m ruff check .`, `python -m ruff format --check .`, `claude plugin validate .`; a fresh-context Opus review of the diff before the final commit, its findings reproduced before any is acted on; a draft PR against `main`; the three jobs of `framework-checks.yml` green before the owner is asked to merge.
6. Docs: the PROGRESS record ("Session 15", with the port-list line: `run_phase.py` touched), NOTES §27 (facts read this session), ROADMAP (the known-gap paragraph annotated once 0.3.0 is tagged), this file rewritten for session 16; the root pin as a guardrail row (line 98: `0.2.29` → `0.3.0`), applied by the owner after the tag exists. No sample upgrade PR follows this tag (precondition 6).

## Sessions 16 to 19 — in one line each
- **Session 16** (item 6): the five study issues in one PR, a test each, plugin 0.3.1; #66 and #68 first, they are the release path's safety; the tag and the root pin follow.
- **Session 17** (item 7): change 0001 — one "Request changes" review on PR #90 that closes its two flagged concerns with choice 134's rules (number-only file names `docs/notes/<N>.md` and `docs/decisions/<N>.md`; PROGRESS records as `docs/progress/session-<N>[-sitting-<M>].md` and `docs/progress/2026-09-28-workflow-comparison-study.md`; each index in number order, one line per file, the original heading as its description), so the fix round re-runs gate (b) on 0.3.1; the owner merges #90; phase (c), the split, then (d); docs only, no bump.
- **Session 18** (item 9): R1 on `lessons/` after the split, plugin 0.3.2, with the owner's answer on sharing (item 4).
- **Session 19** (item 11), the first session after 2026-10-11 whose scheduled detect run has filed: the kept brief's "Session 15" and "Session 16", with 1.0.0 as the bump; if the run did not file (a point missing, a delay past midnight, the actor rule), record why, fix it in 0.3.x, and repeat the provocation for the next morning.

## What the owner does on this road (nothing else is the owner's)
| When | Act |
|---|---|
| Every session start | Both repositories selected (precondition 1). |
| After session 15's PR | Merge; check `v0.3.0` (dispatch `sdlc-tag.yml` if no run appears within minutes, NOTES §14); apply the root pin row (line 98) after the tag. Not the sample's pin. |
| Any day (5 minutes) | Item 4: the four carried questions, answered in one message. |
| Any day (10 minutes) | Item 5: R2's edit tables; then a session verifies the PDF read. |
| Any day, as often as wanted | Item 8: a study session, one or more rows decided. |
| After each later tag | The root pin row; never the sample's until item 11. |
| 2026-10-10, before 23:59 UTC | Item 10: open the failing sample PR; no session touches the sample that day. |
| After 2026-10-11's run has filed | Item 11 with session 19: triage; merge the 1.0.0 PR; check `v1.0.0`; both pins after the tag; merge the sample's upgrade PR; create and close the Milestone. Optional before it: `ANTHROPIC_API_KEY` on the sample for the `--bare` check. |
| Any time | Item 12's hook timing on the Windows PC. |

## Rules for these sessions
- Never reopen a decision; a decision a live run shows impossible as built is documented in PROGRESS. The review's "ruled not a problem" list is settled the same way.
- Cite the PDF page whenever the article is used.
- No notifications, no bypass-permissions mode, no third-party runtime dependency, Python for every script, workflows whose `run:` lines call `python` (and the pinned `claude` install) only — the one exception is the pin step's `git show … | python -` line under `shell: bash` (choice 95) — never with a `${{ }}` in the line (an `env:` value may carry one).
- Guardrail files here and in the sample (`CLAUDE.md`, `.claude/**`, `REVIEW.md`, `sdlc.yaml`, `bands.yaml`): the owner's edit, given as "link; row; what is there; what it needs to be".
- The freeze of precondition 6, until item 11.
- A kept record (a PROGRESS session, a NOTES fact) is annotated beside the sentence, never rewritten (choice 126); a NOTES fact keeps its read date and is re-tested only when the date is older than the environment's last change (choice 93).
- One open incident per metric (choice 69); a rehearsal is closed without a comment (choice 86).
- The shakedown method of session 6 (choice 88) when a fix must be live-tested before the tag — on this repository, never on the sample before item 11.
- A version is bumped only for a change in `plugin/` or `template/`; 0.3.0 carries issue #91's fix and the 1.0.0 bump belongs to item 11's PR alone.
- Every PR: `python -m compileall -q plugin tests tasks.py .github/scripts`, the full `python -m pytest`, `python -m ruff check .`, `python -m ruff format --check .` — green before the push, chained on the exit codes; a fresh-context Opus review of the diff before the final commit; a draft PR against `main`; both runners' jobs of `framework-checks.yml` green on the PR before the owner is asked to merge.
- The secrets-check hook refuses any file whose text contains a credential-shaped string: describe a key in words.
- What a session cannot prove it writes as "not verified" with the reason; a fact is "verified" only with the run URL, the file or the command output that showed it.
