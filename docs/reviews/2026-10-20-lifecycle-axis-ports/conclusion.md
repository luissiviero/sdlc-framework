---
type: Review
title: "R60's conclusion: which lifecycle-axis- features to port, and how"
description: The merged recommendation of R60's two independent studies and their blind judge; seven ports worth doing, all folded into existing candidates, five small ones, and the items not to port. No decision is taken here.
status: report
roadmap: R60
sources:
  - id: study-a
    resource: docs/reviews/2026-10-20-lifecycle-axis-ports/study-a.md
    title: "Study A, the comparison doc (recorded unchanged)"
  - id: study-b
    resource: docs/reviews/2026-10-20-lifecycle-axis-ports/study-b.md
    title: "Study B, made before Study A was read"
  - id: judge
    resource: docs/reviews/2026-10-20-lifecycle-axis-ports/judge.md
    title: "The blind judge's per-item verdicts and the code it checked"
  - id: criteria
    resource: docs/reviews/2026-09-28-playbook-vs-framework.md
    title: "Section 7, line 111: the owner's criteria weights"
generated: { by: claude-code-session, at: 2026-10-20T07:45:00Z }
---

# R60's conclusion: which lifecycle-axis- features to port

**A recommendation, not a decision.** It accepts nothing, amends no candidate and takes no rank; R60's Order stays blank. Accepted items go through the normal front door, as an amendment to the candidate named in the "How" column.

**The reading chosen.**
- The table is the judge's merged table (`judge.md` section 5), with its scores.
- A weighted score is the value a port adds over `main` (`dc40d61`, plugin 1.0.14) plus the accepted candidates as their proposals describe them. Weights: safety 1, attention 3, autonomy 3, audit 2, cost 0, article 2.
- Where Study A and Study B scored the same item differently, the judge's score stands, and its reason is in `judge.md` section 3.

## Summary

- **The framework fits the goal better; lifecycle-axis- is better only at the edges.** No item needs a new candidate or reopens a settled decision. Every port amends an accepted candidate (R11, R13, R24, R25, R26, R35, R37, R39, R44, R52 or R58). Two also touch candidates still only proposed: R59 (renames) and R61 (the trial's shape). *[2026-10-20, after this was written: R61 was accepted the same day (choice 240, merged to `main` in #273); R59 is still proposed]*
- **Four ports score 8.**
  - Show how much the plan grew after the owner approved it (R24).
  - Give R52's merge by silence a per-change grant, a locked-path floor and a "merged unread" record (R52, R11).
  - Require an incident's eval case to be seen red at the merge base when its checks are commands or files (R35).
  - Let a repeated, session-caused gate failure propose a `CLAUDE.md` line (R37).
- **Three ports score 6 to 7.**
  - Give `CLAUDE.md` a line budget and list lines that are now enforced or no longer repeating as deletion candidates (R37, R26).
  - Add an optional post-merge staging command before the release label (R39).
  - Add a GitHub Actions minutes meter, on private repositories only (R25, R61).
- **Five small, cheap ports score 2 to 4:**
  - metrics labelled by play (R26);
  - the release label bound to the head it was applied on (R13, R11);
  - actions pinned by commit SHA (a template PR or R44);
  - an optional `revisit:` field on decisions (R58);
  - the writer's and reviewer's model on each record line (R11).
- **Not to port:**
  - Gemini parity (R8 unchanged);
  - a serial run queue as the default, which would reopen accepted R51;
  - multi-approver roles;
  - local-session execution;
  - the kit's eval format and per-SHA release file.

  Both studies and the judge agree on all except the serial queue, where the judge sided with Study B.

## The merged recommendation

Sorted by weighted score. "A" and "B" name the study each item came from.

| Item | Merged recommendation | How | Weighted score | Confidence |
|---|---|---|---:|---|
| The plan's growth since gate (b) is recorded and shown (B L4; A #5 called the boundary covered) | port adapted | Amend **R24**: at (c), (d) and (e) the gate records `plan_growth: {added, removed}` against the approved `plan.md`, and the build PR's "Needs your close look" banner shows "The plan grew by N files since gate (b)". **R26** counts it. No park, no cap change. Separately, a one-line phase check in `plugin/gate/preflight.py` for a by-hand (c) run (a plugin fix, no candidate). | 8 | high on the gap, medium on the value |
| Merge by silence gains a per-change grant, a locked-path floor and a "merged unread" record (A #1, B L5) | port adapted | Amend **R52** at R50's trigger, as R52 is timed: <br>(i) a per-change switch, read from the base branch: an intent field or a label at (a)/(b); <br>(ii) a floor that never merges unread when `.claude/**`, `CLAUDE.md`, `REVIEW.md`, `sdlc.yaml`, `protected_paths`, `.github/**` or `evals/**` change, with renames judged on both names (**R59**); <br>(iii) an **R11** line `{act: merged-unread, actor: <App>, conditions: [...]}`, with the printed conditions on the PR. | 8 | high on the facts, medium on the value |
| An incident's eval case is seen red at the merge base (B L1; A #6 on the format) | port adapted, narrowed | Amend **R35**'s incident-case clause with **R34**'s red/green pattern. When the case holds `command` or `file` checks, the runner evaluates them at the merge base (the case's files copied in) and at HEAD, records both under `evidence/`, and gate (e) requires one red at the base. <br>A red caused only by a missing test file does not count. A case with only `output` or `denied` checks is recorded as "not provable without the model". | 8 | medium |
| A repeated gate failure proposes a `CLAUDE.md` line (B L3) | port adapted | Amend **R37** (with **R18**, **R26**). A `gate\|<check>\|<reason class>` signature is counted like review findings, for an allow-list of session-attributable checks (`plan_sync`, `design_scope`, `clean_tree`, a red target class). The proposed line is built from the check's hint text. | 8 | medium |
| `CLAUDE.md` gets a line budget, an `enforced:` note and deletion candidates (B L2) | port adapted | Amend **R37** and **R26**: <br>• `sdlc.yaml: claude_md.max_lines`, with the count in the standing PR's body; <br>• an optional `enforced:` note per line; <br>• a line is listed as a deletion candidate when its signature has not repeated in N merged changes, or when its `enforced:` note names a check. <br>Nothing is deleted by a run (decision 6). | 7 | medium |
| An optional post-merge staging command before the release label (A #3, narrowed) | port adapted, as an option | Amend **R39** with a "What to settle" row: an optional `deploy.staging_command` (name with R45) that the release workflow runs on the (e) merge, before the label. `deploy.command` stays the production step. The adapter's shape and decisions 13 and 19 are kept, and so is the deploy-envs decided row. | 6 | medium |
| GitHub Actions minutes are measured (B L6) | port adapted, private repositories only | Amend **R25**: the digest shows "Actions minutes this month: n of m" and warns past `gate.actions_minutes_warn`; the digest workflow gains `actions: read`. Amend **R61**: `/sdlc-init` turns the meter on only for a private repository. | 6 on a private repository, 0 on a public one | medium |
| Metrics labelled by the play they measure (A #9) | fold | Amend **R26**: a column in its measures table (play; leading or lagging). No counter is added. | 4 | medium-low |
| The release label counts only for the head it was applied on (A #4, narrowed) | fold | Amend **R13**, using the head **R11** records at labeling: a label applied on an earlier head does not authorise a later one. The kit's per-SHA file is not ported. | 3 | medium |
| Third-party actions pinned by commit SHA (B L8) | port as-is | A template PR, or inside **R44**: every `uses:` pinned to the tested tag's SHA with the tag as a comment, and one test asserting 40 hex digits. Bumps ride **R5**'s pin-bump PR. | 3 | high |
| A decision may carry a `revisit:` trigger (B L7) | fold, optional | Amend **R58**: an optional frontmatter field, and a docs-lint report line (never a failure) when it is due. Repository practice; no plugin change. | 2 | medium-low |
| Writer and reviewer models on each record line (B L9) | fold | Amend **R11**: two fields in the `details` of each gate and fix-round line. | 2 | high |
| Gemini as a second-model reviewer (A #7) | nothing to port | **R8** unchanged; it already is this. | 0 | high |
| Serial run queue as the default (A #2; B did not count it) | don't port | At most, one open row in **R51**: an optional `queue: serial` that waits at the (b) dispatch while another change is past (b). No pointer file, no new label. | −2 | high |
| Multi-approver roles (A #10) | don't port | The crosswalk row x-roles keeps one owner; revisit if a collaborator joins. | −2 | high |
| Gemini parity: generated `GEMINI.md`/`AGENTS.md`, a second hook wiring (A #7, B L10) | don't port | Decisions 6, 7 and 8 kept. | −5 | high |
| Local-session execution (A #8) | don't port | Decision 1 kept; cost is handled through **R25**. | −15 | high |

## Open questions only the owner can answer

1. **Are the trial projects private repositories on a metered Actions plan?** The minutes meter is worth 6 there and 0 on a public repository.
2. **On an explicit per-change grant, should the App merge at once or still wait R52's hours?** Study A says at once, because the grant is the consent. Study B keeps the hours as a safety margin for an owner who looks in once or twice a day.
3. **For a project with a paper-and-live split, do you want "staging on merge, production on the label" in addition to R39's pre-merge preview?** If the preview at each (e) head is enough, the staging command drops to 0.
4. **Do you want an optional serial queue on the sample, so its results stay attributable?** Nothing enforces one change at a time today; the sample is paced by hand.
5. **What line budget for `CLAUDE.md`?** The template's page holds about 40 lines; the kit allowed 120 across three files. `claude_md.max_lines` needs a number.
6. **Does a repeated gate failure count as "a mistake made twice"?** The article's rule is about Claude's mistakes. Plan-sync and scope failures are the session's; red targets already start fix rounds.
7. **Once R8's Gemini tally exists, would you consider Gemini as the panel's devil's advocate?** That would be a new decision, not a port.

## The owner's answers and the session's recommendations (2026-10-20)

These were given in the session after this file was first written. They are answers, not decisions: no candidate is amended until an accepted item goes through the normal front door.

| # | The owner's answer | The session's recommendation | State |
|---|---|---|---|
| 1 | Mostly private repositories, not exclusively | `/sdlc-init` turns the Actions-minutes meter on by default whenever the repository is private (R25, R61) | agreed |
| 2 | Wants the fewest stops; asked how often a change lacks an explicit grant, and whether a faster alternative to waiting exists | See "Question 2" below. Drop the silence timer: the owner's act at the start of each change is the consent, the App merges as soon as R52's conditions hold, and only changes that fail those conditions wait for the owner | approved as a whole (2026-10-20) |
| 3 | Keep the staging step after the merge: some of the owner's projects trade | Staging after the merge as an R39 key, paired with the preview and set by `/sdlc-init` from the deploy action (paper trading turns it on) | approved: keep (2026-10-20) |
| 4 | Agreed | No serial-queue mechanism; on the sample, merge one intent at a time when results must stay attributable | agreed |
| 5 | Asked for an explanation, then approved it | See "Question 5" below | approved (2026-10-20) |
| 6 | Agreed | A repeated failure counts as "a mistake made twice" for a fixed list of session-caused checks (`plan_sync`, `design_scope`, `clean_tree`, secrets, protected-path denials). Red targets, limits, infrastructure failures and owner acts are excluded | agreed |
| 7 | Agreed; later confirmed for Gemini as a whole ("do as you recommended") | Not now; decide after R8's five-change tally. The tally ends in one behaviour, on everywhere or removed, with no option left (`options.md`) | agreed |
| R52 | Merge by silence becomes the **default**; a project that does not want it opts out | Recorded as the owner's direction for R52's decision. That decision amends decision 4 for every project that has not opted out, instead of only for opted-in ones | the owner's direction |

### Question 2: how often a change has no explicit grant, and the faster alternative

**How often.** Twelve changes have run past change 0000 across the sample and this repository. Nine started from the owner's own intent (route `idea`). Three were incident intents from the daily detection or the weekly security scan, which the owner triages at gate (f) by merging the intent PR. *[2026-10-20, verified by the next session (C6): wrong count. The default branches hold twelve `changes/*/status.yaml` files, but two of them are the change 0000s. Past change 0000 there are ten changes: seven started from the owner's own intent (route `idea`: the sample's 0001, 0002, 0015 and 0016; this repository's 0001, 0003 and 0005) and three from incident intents (the sample's 0005 and 0008, still at phase f; this repository's 0002). Read with `git show origin/main:changes/<folder>/status.yaml` on both repositories. The conclusion holds: every change started with one act of the owner's.]*

**What that means.** Every change already starts with one act of the owner's:
- pushing their own intent;
- merging an incident intent at (f);
- labelling an issue under R31. *[2026-10-20, verified by the next session (C7): R31 is accepted but not built (ROADMAP R31, Order 37; no template workflow runs on an `issues` event), so this route is a future one.]*

If that act counts as the grant, no change is left in the "no grant" case, and the silence timer has nothing to wait for.

**Recommendation.** Make the grant implicit in that first act, and drop the timer. The App merges the build PR as soon as R52's conditions hold and the locked-path floor is clear. The PR must also have been brought up to date with the default branch and re-checked first (R51). *[2026-10-20, verified by the next session (C2): R52's own conditions (ROADMAP R52; `docs/proposals/speed-beyond-the-sprint.md`, section "R52") are a routine plan, every check green, no "Decisions taken for you", no risk-list hit and `deploy.production` false. The locked-path floor and the R51 update are this study's additions, and `options.md` section 3 adds a third, the plan-growth threshold, which this list does not name. With the timer dropped, R52's other stop ("any review comment or label stops it") has no window left: nothing here says how the owner objects before the merge. The owner decides both with `options.md`, row "Plan-growth threshold".]*

**What still stops.** A change that fails a condition still waits for the owner at (e), as it does today:
- a non-routine plan;
- "Decisions taken for you";
- a risk-list hit; *[2026-10-20, decision 35 (merged to `main` in #279 after this was written): a risk-list hit no longer parks; it is a line of the "Needs your close look" banner, and the owner's merge accepts it. Such a change still waits for the owner at (e), so it stays on this list, but not "as it does today".]*
- a declared production;
- a locked path.

Those are the changes where reading the code matters.

**Faster than stopping, for the margin a timer was meant to give.**
- **Merge now; a declared production still waits for the release label** (decision 13). *[2026-10-20, verified by the next session (C2): this contradicts the list above and R52 itself. R52 requires `deploy.production` false, so a change on a declared production never merges unread: it waits for the owner's merge at (e), then for the release label.]*
- **Undo with one act.** The digest lists each "merged unread" change, and the existing `revert-pr` runbook reverts one. *[2026-10-20, verified by the next session (C1): wrong. The "merged unread" list is not built (it is this study's proposal). `revert-pr` runs only as a tier-3 incident route that the diagnosis proposes (`plugin/detect/routes.py:44-48`, `plugin/commands/sdlc-maintain.md:81-95`), then pre-approval or `sdlc:go` on the incident intent PR (`template/.github/workflows/sdlc-runbook.yml:52`); every maintain CLI command needs an incident change id (`plugin/detect/cli.py`). The nearest by-hand path is a dispatch of `sdlc-detect.yml` with `force_tier: 3`, and then the model picks the commit. The runbook never merges (`plugin/detect/runbooks.py:5-7`), so the undo is two acts at best: open the revert PR, then merge it, as with GitHub's own Revert button. A one-act undo of a named merged change is new work for R52.]*
- **Waiting changes do not block the others.** Each change runs in its own branch (R51), so only a change that depends on a waiting one waits with it. *[2026-10-20, verified by the next session: the per-change branches exist today (`sdlc/<id>/<phase>`); R51 adds the bring-up-to-date and re-check before (e).]*

**What remains.** R52's decision is still timed for R50's trigger: 20 changes past gate (e) on a project other than the sample, with R26's measures. That is the one wait left before any of this applies.

### Question 5: the `CLAUDE.md` line budget, explained

Every session reads `CLAUDE.md` in full at its start. The article asks to keep it under a page and to add a line each time Claude repeats a mistake (p.20 steps 4-5). The framework does the adding, through R37's standing PR, but nothing ever removes a line, so the file only grows.

**The recommendation:**
- **A fixed cap of 60 lines for the whole file.** The template is 41 lines; the sample's filled-in file is 53.
- **The count is shown.** R37's standing PR shows it, for example "CLAUDE.md: 53 of 60 lines".
- **A line that would go past 60** makes the same PR list existing lines to delete:
  - first, lines whose mistake a hook, gate check or eval now catches, so the written rule is redundant;
  - then, lines whose mistake has not recurred in a set number of merged changes (R26 counts repeats per line).
- **The owner deletes them** by editing the PR before merging. No run deletes a line (decision 6).

The number is fixed in the plugin rather than a new `sdlc.yaml` key, so it adds no setting.

**Example.** "Run the migrations test before reporting done" was added after changes 0007 and 0011. Change 0019's incident adds an eval case that fails without that test. The next standing PR then shows the line as "enforced by eval 0019, proposed for deletion". *[2026-10-20, the next session: an illustration; changes 0007, 0011 and 0019 and this line exist in no repository.]*

## How it was reached

| Step | File | Who |
|---|---|---|
| Study B, made without seeing Study A, committed first | `study-b.md` (commit `1884165`) | a new session with five profiling subagents |
| Study A, read only after that and recorded unchanged | `study-a.md` (commit `5885764`) | the same session, from the comparison doc (revision 19) |
| The judge: both studies blind as X and Y in random order, disputed claims checked in both repositories | `judge.md` (commit `824c606`) | a fresh subagent on a different model (Fable 5.1) that wrote neither study *[2026-10-20, the next session (C9): the subagent was started with the `fable` alias; the model that served it was not recorded, so "Fable 5.1" is not verified]* |

The judge found Study B's method right: it scores the delta over `main` plus the accepted candidates. Study A counted R52's and R39's accepted value in its two top scores. Study A contributed two items Study B lacked: the explicit grant with no wait, and the post-merge staging step. Both studies' arithmetic re-computed correctly. Each study's factual slips are listed in `judge.md` sections 1 and 4.
