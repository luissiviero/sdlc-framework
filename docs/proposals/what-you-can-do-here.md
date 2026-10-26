---
type: Proposal
title: The owner is shown what to do at every step — a "What you can do here" block on each PR, a "Next for you" line in the digest, and a guide command
description: Every pull request the framework opens, the runbook and dismissal PRs included, ends with a generated block that names each act the owner can take there, what it starts and what happens if the owner does nothing, rendered from one table shared with "What needs you" and never by a model; the daily digest carries the same text as one "Next for you" line per item; a guide command, run by hand in a checkout, says where every change stands and what to do first on a new project; T1's manager quotes the block.
status: accepted
roadmap: R19
sources:
  - id: study-entry
    resource: docs/reviews/2026-09-28-playbook-vs-framework/target-design.md
    title: "T27, confirmed at the close of the study on 2026-10-09; recorded from the owner's request of 2026-10-07 (option c of three), not a crosswalk row of its own; annotated 2026-10-13 with R14's Proof line (ArtCraft A1) and the judgment label (ArtCraft A2)"
  - id: crosswalk
    resource: docs/reviews/2026-09-28-playbook-vs-framework/crosswalk.json
    title: "The decision fields of the rows the entry names: x-queue (T28), x-roles (T1), setup-adopt (T5), deploy-comments (T17), build-start (the Full label), plan-accept (T7), maintain-triage (T23), maintain-act (T24), deploy-release (T21)"
  - id: artcraft-study
    resource: docs/reviews/2026-10-13-artcraft-vs-framework.md
    title: "Row A1 (the 2026-10-13 annotation: the per-item PR line with T27), row A2 and gap G3 (a model judgment beside measured lines is labelled)"
  - id: playbook
    resource: docs/reference/ai-native-sdlc-playbook.pdf
    title: "p.8: human attention concentrates at the gates, reviewing what the agent flagged; p.33-35: @claude, the slash command that babysits the PR, the PR as the audit record; p.42: the headless gate escalates to a human, an alert can be missed; p.44: fix now, schedule or dismiss"
  - id: decision-20
    resource: docs/decisions/20.md
    title: "Decision 20: the review queue and the digest, nothing pushes to the owner (kept)"
  - id: decision-11
    resource: docs/decisions/11.md
    title: "Decision 11: park, never page; the 'What I need from you' block (kept, extended)"
  - id: code
    resource: plugin/pr/description.py
    title: "GATE_CHECKLIST, RELEASE_APPROVAL_LINE and _owner_line; with gate.py's park block, digest.py's _line, the runbook and dismissal PR bodies and state/cli.py list (lines in the code footnote), read at main acefc7e, plugin 1.0.0"
generated: { by: sdlc-framework-session/ccr-20b39ad0-kcymdd, at: 2026-10-14T15:30:00Z }
---

# The owner is shown what to do at every step
**Names since R45** (decision 39; the renames built in plugin 1.0.43 to 1.0.47; added on 2026-10-26, the text below keeps the old names, choice 126): `(a)` -> intent; `(b)` -> design; `(c)` -> build; `(d)` -> test; `(e)` -> deploy; `(f)` -> maintain; `a` -> `intent`; `sdlc:e-ready` -> `sdlc:deploy-ready`; `sdlc:c-approved` -> none, decision 37 removed it (decision 39, point 2); `sdlc:d-approved` -> none, decision 37 removed it (decision 39, point 2); `/sdlc-plan` -> `/sdlc-intent`; `sdlc-plan.md` -> `sdlc-intent.md`; `schedule` -> `sdlc:schedule` (the label); `deploy.production` -> `deploy.production_gate`. \
**Status: proposed (roadmap R19), from study entry T27, confirmed by the owner on 2026-10-09.** *[2026-10-20: accepted 2026-10-14 (PR #208); rank 29; the rank is read from ROADMAP's Order column]* Nothing is built. Not a crosswalk row of its own: recorded from the owner's request of 2026-10-07, option c of three (deterministic guidance on the surfaces the owner already reads). It follows R14, whose per-item Proof line is this proposal's to render; its "Next for you" line is placed in the digest by R20. The `@claude` act is R17's, which comes before this proposal in the order: part 1 renders the `@claude` row once R17 has shipped, and whichever of the two is built second adds the row.

## The problem

The owner's words: "Looking at all these steps, when creating something with this plugin, I won't remember how to use it to its full capabilities on my own. I'd need the manager to walk me through all steps suggesting what to do at each new step, or some other role, or any other solution that would work better than these in this case."[^entry]

The framework has eleven acts the owner can take on a pull request (merge, "Request changes", close with a comment, eight labels), and it tells the owner about some of them, in some places:

- **The phase pull requests** carry one "What needs you" bullet from a fixed table (`plugin/pr/description.py` `GATE_CHECKLIST`, `_owner_line`)[^code]. At (b) it says "Merge = approve; a review comment = change request (/sdlc-fix)" and not that the build then starts by itself, nor that closing abandons the change, nor what the Full label would do (not built). At (c) and (d) it still says "approving review + label", which decision 27 amended to the label alone. At (e) on a declared production it says to apply the release label "after merging", which R13 owns: R13 corrects it once the production-gate hook accepts only a merged PR's label, the rule R13 settles first. It never names the un-park labels of decision 24 except when a park asks for one; a risk-list park asks with the CLI command, not the label (`plugin/gate/checks.py:773-775`), and every park's block ends with a by-hand gate re-run (`gate.py:81-84`).
- **The runbook and dismissal pull requests** carry two sentences: "The review gate decides: merge to apply, close to drop. Nothing merges by itself (decision 14)." (`runbooks.py:64-67`), or "Merging records it in changes/.dismissed.json so the same finding does not return as new on the next run (article p.47 step 4). Nothing else changes." (`detect/cli.py:1471-1473`).
- **The digest** lists each item's labels, title, last update and the first bullet of its summary (`digest.py:98-108`), not what the owner can do on it.
- **Before the first pull request** there is `/sdlc-init` §6 and the README; none of the eight commands reads the project's state for the owner, and `state/cli.py list` prints each folder's phase and park reason with no pull request and no act.

So the owner learns the acts from the OPERATING_MODEL, the notes and memory, which is what the owner said will not hold: every gate costs a look-up, and an act the owner does not know about is never taken.

## What the article says

Human attention "concentrates at the gates, reviewing what the agent flagged rather than starting each stage from scratch" (p.8); the engineer tags `@claude` on a review comment and Claude pushes the fix, a slash command babysits the PR until it is green, "waiting only on code owner approval" (p.33-34); approvals come from a human through branch protection, informed by the findings, and "the PR is the audit record" (p.35); in headless maintenance the gate decides whether the output "continues or is escalated to a human", and its picture of the traditional loop is that "an alert fires at 3 a.m. and can be missed" (p.42, the TRADITIONAL column); the owner triages: "fix now, schedule, or dismiss" (p.44)[^playbook].

The article has no guidance surface, because its engineer, code owner, release manager and service owner each know their one play. The framework's owner is all of them at once (T1, T4), which is the gap the owner named. The article does say where the owner reads: the pull request (p.35) and the gate (p.8). That is where the guidance goes, as decision 20 already puts the summary there[^decision-20].

## What the framework does today

Read at `main` acefc7e, plugin 1.0.0; the entry's "Today" was read at 619f01a (0.3.5). `git diff 619f01a acefc7e --stat` on `plugin/ci plugin/pr plugin/release template/.github/workflows` lists `run_phase.py`, `settings.ci.json`, `description.py` and `notes.py`; of the files this entry cites only `description.py` changed, in `_first_sentence` alone (e0d1768, 2dbcf0f, item 11's G1). `digest.py`, `detect/runbooks.py`, `detect/cli.py`, `state/cli.py`, `state/conventions.py` and `sdlc-init.md` are byte-identical; `gate/checks.py` changed at line 39 (one import, shifting the later lines by one) and from line 1590 (change 0002's check); the lines below are read at acefc7e and hold.

- **The phase PRs.** `build_description` is pure, from the change folder's files (`description.py:537`). The fifth bullet is `_owner_line` (`:308-316`): on a park, "parked at gate (x) - see 'What I need from you' below; nobody was notified (decision 11)"; on `wait`, and always at (f), the `GATE_CHECKLIST` text (`:96-110`); otherwise `NOTHING_NEEDED` (`:115`). At (a) `_intent_bullets` uses `GATE_CHECKLIST['a']` directly (`:340`) and `build_description` returns early (`:550-554`), so an intent PR has no park block today. At (e) on a declared production `RELEASE_APPROVAL_LINE` follows the bullets (`:111-114`, `:596`). The (f) text names the three triage verbs; PR #118 on this repository shows it verbatim (read through the REST API on 2026-10-14: "What needs you: triage (gate (f), decision 25): merge = fix now …; label `schedule` = later; close with a comment = dismiss the finding").
- **The park block** is `GateResult.what_i_need` (`gate.py:68-86`): one line per failed check with its `need` sentence, then "re-run the gate: `python … gate/cli.py check …`". The risk-list need gives the `state/cli.py accept-risk` command (`checks.py:773-775`); the owner-actions and test-lock needs name the labels (`OWNER_ACTIONS_NEED`, `checks.py:968-971`; `TEST_LOCK_NEED`, `:1245-1250`), and the route check's Go request names `sdlc:go` (`:1551`, `:1578`). The Go park asks for `sdlc:go` again (`detect/cli.py:1218-1221`).
- **Acts that exist.** Merge; "Request changes" by an owner, member or collaborator (decision 22; the member rule is `template/.github/workflows/sdlc-fix.yml:25-26`, `:81`; a fix round on every phase's PR, `run_phase.py:157` `FIX_PHASES`); close with a comment (decision 25: abandon at (a) to (e) with a fixed reason, dismiss at (f) with the comment as the reason); the labels `sdlc:c-approved`, `sdlc:d-approved`, `sdlc:release-approved`, `sdlc:accept-risk`, `sdlc:reset-iterations`, `sdlc:unlock-tests`, `schedule`, `sdlc:go` (`conventions.py:65-93`, the approval labels from `approved_label`, `:102-110`). **Acts that do not exist:** the `@claude` comment (R17); a per-change Full label (build-start: no label in the code, `profile_override` is asked at `/sdlc-plan`, `sdlc-plan.md:33`); `sdlc:accept-findings` (decision 28, R6: not in the code); the approving review as gate (e) (T18); the closing comment kept as the reason at (a) to (e) (T7); the one-act dismissal (T23); the owner-only Go (T24).
- **The digest, the state CLI, the start.** As the problem states (`digest.py:98-108`; `state/cli.py:404-433`; `sdlc-init.md:110-157`, the after-merge settings and nothing about the first change).

## The proposal

Guidance where the owner already is, generated from one table, with no model run. Four parts and two rules.

1. **"What you can do here" on every PR the framework opens**, the runbook and dismissal PRs included, after the summary and, at (b) to (f), after the "What I need from you" block when parked (an intent PR has none). It is rendered by `description.py` from one table keyed by gate, profile, park reason and the project's settings, the same table that renders "What needs you", so the two never disagree. Per act: the act, what it starts, and one closing line for "if you do nothing". The draft, with today's acts and the ones that arrive with their entries (marked):

| Where | Acts and what each starts | If you do nothing |
|---|---|---|
| (a) intent PR, every profile | merge = accept, the design run starts by itself · "Request changes" = a fix round on `intent.md` · `@claude` comment = the same round *(R17)* · close with a comment = abandon; the comment is kept as the reason *(T7; today a fixed text)* | waits; listed under the digest's "Needs you" |
| (b) design PR, Standard | merge = approve spec and plan; build, test and review run by themselves · "Request changes" / `@claude` *(R17)* = a fix round · the Full label before merging = (c) and (d) wait for your labels *(build-start, T1; not built)* · close with a comment *(T7)* | waits |
| (b) design PR, Full | as above, without the Full label: "this change runs Full: (c) and (d) will wait for your labels" | waits |
| (c), (d) build PR, Standard, not parked | nothing needed; "Request changes" / `@claude` still starts a round | continues to the next phase |
| (c), (d) build PR, Full, waiting | `sdlc:c-approved` = test starts; `sdlc:d-approved` = review starts (the label alone, decision 27) · "Request changes" / `@claude` · close | waits |
| (e) build PR, `sdlc:e-ready` | merge = gate (e) passed; the release workflow runs `deploy.command` *(T18: your approving review, the App merges)* · on a declared production: apply `sdlc:release-approved` with your approval to release on merge; without it the merge waits for the label *(arrives with R13, which first settles the hook rule; until then today's "after merging")* · `sdlc:accept-findings` when an Important finding stands *(R6)* · "Request changes" / `@claude` · close | waits |
| any gate, parked | the label that un-parks this park: `sdlc:accept-risk` (risk list), `sdlc:reset-iterations` (iteration cap), `sdlc:unlock-tests` (test lock), `sdlc:accept-findings` *(R6)*, `sdlc:go` when Go is requested; an un-park label starts a fix round that performs it first (`sdlc-fix.yml:1-4`) · "Request changes" = a fix round · close | stays parked, first in "Needs you" |
| (f) incident intent PR | merge = fix now, gate (a) of this change · `schedule` = later; the metric stays muted while open *(T23)* · close with a comment = dismiss, the comment is the reason; the dismissal PR opens *(T23: merged for you when the close is yours)* · `sdlc:go` when Go is requested *(T24: your account only)* | waits; the finding stays muted while the PR is open |
| runbook PR (revert, quarantine) | merge = the revert or quarantine lands on the default branch · close = dropped, the incident PR stays · "Request changes" on the incident PR = another route *(T24)* | stays open, under the digest's "Needs you" (R20's third group, runbook and dismissal PRs, incident first, then oldest first, the wait from the PR's creation) |
| dismissal PR | merge = the dismissal is recorded; a detection finding stays muted one window, a scan finding stops returning · close without a merge = the finding returns at the next run | the pending branch mutes a detection finding; a scan finding returns on Monday |

   The block gains R14's **Proof line, one per item** of the plan's Proof: the item, its outcome from the runner's record (`proof/manifest.json` and the gate record, never `verifier.md`, which never reads the final tree), and a link to the file at the head commit (R14 sub-change 5, D6 and D9)[^r14].
2. **"Next for you" in the digest**: the block's first line, written short ("#41 change 0012 at the design gate: merge, request changes, the Full label, or close"), one per "Needs you" item, the runbook and dismissal PRs included, which R20 moves under "Needs you" as its third group (incident first, then oldest first, the wait from the PR's creation). The digest copies it from the PR body as it copies the first bullet today, each line keeping today's first bullet and `updated_at` (R20), so there is one writer and no drift; a body with no block (an older plugin) gets one fixed generic line, "open the PR for its acts", never a recomputation from the labels. R20 places it[^r20]. No clock: the line carries no time.
3. **A guide command, by hand** (`/sdlc-guide`, name provisional, judged with T4, which is placed last). *[2026-10-20: T4 (R45) is rank 20; the rank is read from ROADMAP's Order column]* For the moments with no pull request in front of the owner: it reads `changes/index.md` when the project has one (R9 part 1, Order 5, before this proposal) *[2026-10-20: R9 part 1 is rank 39, after R19 (29), so the guide reads `status.yaml` first; the rank is read from ROADMAP's Order column]* and each `status.yaml` otherwise, through one reader in `plugin/state`; the open pull requests and their labels through GitHub when a token is at hand, else it says what it could not read; and it prints, per change, where it stands, what runs next by itself and what the owner can do, from the same table. On a project with no change past 0000 it says what to do first: T5's by-hand start, the policy sources (build-skills), the ruleset of decision 4 (`/sdlc-init` §6). It reports and never acts, and no model paraphrases it: the command runs one deterministic script under `plugin/state` that makes GitHub GET requests only and prints its output verbatim, so the guidance is the table's text, not a session's reading of it (otherwise this would be option (b) in small). It needs a checkout with the plugin, so it runs on the owner's PC or in a Claude Code cloud session (NOTES §3's setup-script install); the phone's surfaces are the block and the digest.
4. **T1's manager quotes the block** in its recommendation, so option (a), the walk-through, comes with the manager once it exists, at no cost here.

The two rules. **No model run**: every line is rendered from the table and the files, so the block is measured text; the one judgment beside it is T1's manager recommendation, which is labelled as a judgment (ArtCraft A2, G3)[^artcraft]. **Nothing pushes**: the block is on the PR, the line in the digest, the guide on request (decision 20).

## How it is judged

On the next five changes after it ships, every act the owner takes is one the block in front of them named, and the owner opens no other document to find it; an act looked up in the README, `/sdlc-init` §6 or the OPERATING_MODEL is the failure. The other failure is a block that names an act nothing reads (a label with no reader, a setting the project lacks). A session can check both from the PR bodies and the approvals list (R11).

## What to settle before building

| Question | Recommended |
|---|---|
| The block's exact wording per gate, profile and park reason, and how it follows the target's new acts as each is built | The table above, as one Python table in `plugin/pr/` keyed by (gate, profile, park check, settings), rendered three times: the bullet, the block, the digest's short line; each later entry adds its row when built (R17 the `@claude` line, T18 the approval, R6 the findings label, T23 and T24 the (f) lines, T7 the kept reason); a test renders every cell. Two of today's texts are corrected in passing: (c) and (d) to the label alone (decision 27: `GATE_CHECKLIST` is a fifth place R12's four documents do not list; if R12 is built first, its intent takes this correction and this proposal inherits it), and the park's CLI commands to decision 24's labels. The release line is R13's and is not corrected here |
| The guide command's name, and whether it can run from claude.ai or the phone | `/sdlc-guide` until T4 judges it. A checkout and the plugin are needed: the owner's PC or a cloud session; whether the claude.ai phone app can start a cloud session that runs a plugin command is to verify when built. The block and the digest are the phone's surfaces either way |
| Whether the block shows acts that need a setting the project has not made | Only the acts that apply; the guide command, on a new project, names the settings that would add acts (a declared production, a rollback runbook) |
| Where the digest's "Next for you" text comes from (T28's entry asks it) | Copied from the block's first line in the PR body, as the first bullet is; one fixed generic line ("open the PR for its acts") when the body has none |
| What the guide reads | `changes/index.md` (R9 part 1) when present, else every `status.yaml`; GitHub for the pull requests, degrading to "not read" |
| Settled elsewhere | The release act's wording (R13); the (c) and (d) label alone (decision 27); the `@claude` act (R17); the Proof line's source and link (R14, D6 and D9); "how long it has waited" (T31's note, in R20); the judgment label (ArtCraft A2) |

## Considered and not chosen

- **(a) The manager alone**: a model's paraphrase, only at the gates where it writes, and nothing before the first pull request. It comes anyway, quoting the block (part 4).
- **(b) A Guide role**: one more model run per gate per change, paraphrasing tables the code already holds, which can drift from what the code does after a plugin release.
- **The digest recomputing the acts from the labels**: two writers of the same text; the labels do not carry the profile or the park reason.
- **A page per gate in the README**: one more place to read; the block is where the owner already is.
- **Showing every act with "needs setting X"**: longer blocks on every PR for acts the project will never have.

## Decisions it touches

None is amended, so no decision file is written. 20 (the queue and the digest, pull not push) is kept: the three surfaces are the PR, the digest and a command the owner runs. 11 is kept and its block extended, nobody notified. 24, 27 and 28 are read: the block names their labels as they are decided, 28's once R6 is built. 22 is read; its one added trigger is R17's. 13 as R13 words it; 25's three verbs at (f). 29 (a red target starts a round), 14 (the Go) and 21 (deferred review) are read, none amended: they shape the parked row's "if you do nothing". The release cell arrives with R13 and reopens nothing.

## Order

Sixth of the study's proposals in the confirmed order (the record's section 8: T32, T12, T21, then T17, T19, T27, T28), so after R11 to R13, R17 and R18. **After R14** (after R10): the Proof line is R14's second change and cannot be rendered before R14's first produces the record. **With R20**, which places the digest line; after R9 part 1 only for the guide's index, which otherwise reads `status.yaml`. It needs no change to `run_phase.py`: `build_description` already reads the profile and `deploy.production`, so it is not on the port list. The parts:

1. **The table and the block on the phase PRs**, with today's acts and the two corrected texts (the release cell keeps today's wording until R13): buildable now, in `plugin/pr/description.py` and `plugin/gate/gate.py`, a plugin version with tests.
2. **The block on the runbook and dismissal PRs** (`detect/runbooks.py`, `detect/cli.py`): buildable now.
3. **"Next for you" in the digest**, from the body's line: buildable now in `digest.py`; its place under "Needs you" is R20's.
4. **The guide command**: buildable now reading `status.yaml`; it switches to `changes/index.md` with R9 part 1.
5. **The Proof line per item**: R14's second change, after its first.
6. **Rows that arrive with their entries**: the `@claude` comment (R17, before this proposal in the order: whichever of R17 and R19 is built second adds the row), the release cell's wording (R13, after its hook rule), the approving review and the App's merge (T18), the kept closing comment (T7), the Full label at (b) (T1, build-start), `sdlc:accept-findings` (R6), the one-act dismissal and the band number (T23), the owner-only Go and the release window (T24), the manager's quote (T1), the triage label names (T4).

[^entry]: `docs/reviews/2026-09-28-playbook-vs-framework/target-design.md` T27, "The owner's words" and "Today".
[^code]: `plugin/pr/description.py` `GATE_CHECKLIST` (:96-110), `RELEASE_APPROVAL_LINE` (:111-114), `NOTHING_NEEDED` (:115), `_owner_line` (:308-316); `plugin/gate/gate.py` `what_i_need` (:68-86); `plugin/gate/checks.py` :773-775, :968-971; `plugin/pr/digest.py` `_line` (:98-108); `plugin/detect/runbooks.py` :64-67, :296-299, :709-713; `plugin/detect/cli.py` :1218-1221, :1465-1473; `plugin/state/cli.py` `cmd_list` (:404-433); `plugin/state/conventions.py` :65-93; all at `main` acefc7e.
[^playbook]: `docs/reference/ai-native-sdlc-playbook.pdf` p.8, p.33-35, p.42, p.44.
[^decision-20]: `docs/decisions/20.md`; `docs/decisions/11.md`.
[^r14]: `docs/proposals/drive-target-and-proof.md`, sub-change 5 and its D6/D9 annotation, and "Order".
[^r20]: `docs/proposals/digest-needs-you-first.md` (R20, T28), which places the line under "Needs you"; the "Failed runs" line is R18's (`failed-run-explains-itself.md`).
[^artcraft]: `docs/reviews/2026-10-13-artcraft-vs-framework.md`, row A1 (the 2026-10-13 annotation), row A2 and gap G3.
