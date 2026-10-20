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

- **The framework fits the goal better; lifecycle-axis- is better only at the edges.** No item needs a new candidate or reopens a settled decision. Every port amends an accepted candidate (R11, R13, R24, R25, R26, R35, R37, R39, R44, R52 or R58). Two also touch candidates still only proposed: R59 (renames) and R61 (the trial's shape).
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

## How it was reached

| Step | File | Who |
|---|---|---|
| Study B, made without seeing Study A, committed first | `study-b.md` (commit `1884165`) | a new session with five profiling subagents |
| Study A, read only after that and recorded unchanged | `study-a.md` (commit `5885764`) | the same session, from the comparison doc (revision 19) |
| The judge: both studies blind as X and Y in random order, disputed claims checked in both repositories | `judge.md` (commit `824c606`) | a fresh subagent on a different model (Fable 5.1) that wrote neither study |

The judge found Study B's method right: it scores the delta over `main` plus the accepted candidates. Study A counted R52's and R39's accepted value in its two top scores. Study A contributed two items Study B lacked: the explicit grant with no wait, and the post-merge staging step. Both studies' arithmetic re-computed correctly. Each study's factual slips are listed in `judge.md` sections 1 and 4.
