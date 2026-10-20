---
type: Review
title: "Study A: lifecycle-axis- vs sdlc-framework (the comparison doc, recorded unchanged)"
description: The first study of R60, a Claude Docs doc written in a chat session of 2026-10-19/20, recorded here word for word after Study B was committed.
status: report
roadmap: R60
sources:
  - id: study-a
    resource: "https://claude.ai/code/artifact/9f0ad0d6-170a-4e4a-b841-89126493329d"
    title: "Claude Docs doc 'lifecycle-axis- vs sdlc-framework', tab 4bbc990f-1312, revision 19"
generated: { by: claude-code-session, at: 2026-10-20T06:14:51Z }
---

> **Recorded from** https://claude.ai/code/artifact/9f0ad0d6-170a-4e4a-b841-89126493329d (doc revision 19), **read at 2026-10-20T06:14:51Z**, after Study B (`study-b.md`) was committed and pushed.
>
> **How it was read.** The Claude Docs connector's `read` of the doc's one tab returned the full text as XML. That text is transcribed below as Markdown, unchanged: same words, headings, tables, lists, code block and links.
>
> **What could not be carried over.**
> - The doc's byline holds two chips, a date chip (2026-10-20) and a mention of the owner. Both are written out as plain text.
> - One embedded chart widget under the scoreboard heading has no text export. Its caption is kept in brackets in its place. The table beneath it carries the same scores.
> - An open comment thread is anchored at the end of the scoreboard's lead sentence. Its words are not part of the doc text and are not recorded here.
>
> **How the content was obtained.** The connector's Markdown export comes back base64-encoded, and the session's shell was not permitted to decode it. The XML read gives the same text.
>
> Nothing below this line was written by this session.

# lifecycle-axis- vs sdlc-framework

2026-10-20 · Luís

## Summary

sdlc-framework fits the original goal better. Of the ten things lifecycle-axis- does better, three are worth porting, each folded into a ROADMAP candidate that already exists.

- **Port 3:** environment tiers via R39 (+12), the delegation grant via R52 (+11), and a serial run-queue via R51 (+10).
- **Take one idea in another form:** Gemini as a second-model reviewer via R8, not lifecycle-axis-'s Gemini parity.
- **Don't port the other 6.** sdlc-framework already covers #4 (SHA-bound release), #5 (plan as a hard boundary) and #6 (deterministic evals). #8 (local execution) and #10 (multi-approver roles) go against the owner's own criteria.
- **Scoring:** each item gets −2 to +2 on the six criteria the owner saved on 2026-09-29, weighted Safety 1, Attention 3, Autonomy 3, Audit 2, Cost 0, Article 2.
- **Status:** these are recommendations, not decisions. R60 asks for an independent second study and a judged comparison before the owner decides.

## Side by side

Both turn Anthropic's AI-native SDLC playbook into enforced agent behaviour; they differ in where the work runs and who holds the controls.

| Dimension | lifecycle-axis- | sdlc-framework |
| --- | --- | --- |
| Model | Per-repo governance kit | Phase orchestrator (plugin + project template) |
| Life | Sep 2–18, 2026 · 673 commits · stopped | Sep 19–Oct 19, 2026 · 1,058 commits · v1.0.13 |
| Unit of work | `work/<slug>/`: intent → spec → plan → log | `changes/<id>-<slug>/`: intent → spec → plan → evidence + `status.yaml` |
| Runs where | Local sessions, chained via a committed HANDOFF | GitHub Actions `claude -p`, one job per phase |
| Human gates | Approve each artifact (script, web editor or one-tap dispatch) | Profile gates (a), (b), (e) via merges and labels; fast lane |
| Autonomy | Delegated items through a run-queue, with park and resume | Phases chain on merge; caps on iterations, wall-clock and budget |
| Hooks | 9, bash + jq | 8, Python exec-form |
| Models | Claude + Gemini CLI on the same hooks | Claude only; Fable/Opus split, blind two-model panel |
| Knowledge | OKF bundle: 17 decisions, 19 lessons, metric definitions | 34 decisions, 50 verified platform notes, 1 lesson |
| Tests and evals | ~1,000 tests · 55 evals (49 deterministic) · green | ~1,480 tests · 6 evals · green |
| Deploy | `environments.yaml` tiers; release bound to a commit SHA | Deploy adapters (publish, schedule, paper trading…); release label |
| Maintain | σ-band detector on GitHub metrics; incident flow never exercised | Detect + runbooks + weekly scan + daily digest; 1 real detection |
| Windows | Git Bash, partial | First-class, with Windows CI |
| Weight | No per-change model spend in CI | ~24 files scaffolded, 13 workflows, ~$50–85 per change |

## What lifecycle-axis- does better: scoreboard

Environment tiers, the delegation grant and a serial run-queue score +10 or more; local-session execution scores −15. Each item is scored −2 to +2 per criterion; the chart shows the weighted total.

[embedded content: Scores from this chat's analysis, 2026-10-20 · weights from docs/reviews/2026-09-28-playbook-vs-framework.md §7]

| # | Item | Safety ×1 | Attention ×3 | Autonomy ×3 | Audit ×2 | Cost ×0 | Article ×2 | Call |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 3 | Environment tiers | +2 | +1 | +1 | +1 | 0 | +1 | Port via R39 |
| 1 | Delegation grant | −1 | +2 | +2 | +1 | 0 | −1 | Port via R52 |
| 2 | Serial run-queue | +1 | +1 | +2 | 0 | 0 | 0 | Port via R51 |
| 9 | Metrics per play | 0 | 0 | 0 | +1 | 0 | +1 | Fold into R26 |
| 7 | Gemini as a reviewer | +1 | 0 | 0 | +1 | 0 | 0 | Via R8, not parity |
| 4 | SHA-bound release | +1 | 0 | 0 | 0 | 0 | 0 | Already covered |
| 5 | Plan as a hard boundary | +1 | 0 | 0 | 0 | 0 | 0 | Already covered |
| 6 | Deterministic evals | +1 | 0 | 0 | 0 | 0 | 0 | Already covered |
| 10 | Multi-approver roles | +1 | −2 | −1 | +1 | 0 | +2 | Don't port |
| 8 | Local-session execution | −1 | −2 | −2 | −1 | +2 | 0 | Don't port |

The scores are judgment, meant to be challenged. Gemini as parity (a second CLI and hook set) would score −3. The full reasoning for each item is in the next section.

## Per-item analysis

Each item answers (a) what it is, (b) how it would work in sdlc-framework, (c) the recommendation, (d) why, and (e) its effect on the six criteria and the decisions it touches.

### #3 Environment tiers (+12): port via R39

**(a) What it is.** `.sdlc/environments.yaml` lists environments, each with what the agent may do there. In development and staging the agent may deploy and roll back on its own. In production it may only prepare a release and propose a rollback, and a production deploy needs a human authorization for that exact commit.

**(b) In sdlc-framework.** Today there is one `deploy:` block with a `production: true/false` flag; R39 adds an optional preview. For a trading project the block would become a list:

```yaml
deploy:
  environments:
    - name: paper
      command: python ops/deploy.py --env paper
      agent_may: [deploy, rollback]
    - name: live
      command: python ops/deploy.py --env live
      agent_may: [prepare-release, propose-rollback]
      production: true
```

1. After the owner's (e) merge, the release job deploys to paper on its own.
2. Detection (phase f) watches the paper metric.
3. Promotion to live waits for `sdlc:release-approved` on the same merge commit, which is decision 13's second act.
4. A rollback on paper is pre-approved; on live, decision 26 applies.

**(c) Recommendation.** Generalize R39's single preview into this ordered list. Keep decision 13 unchanged for the tier marked `production`. The default stays one environment, so small projects see no change.

**(d) Why.** Risk should scale with the environment, not with each change. Paper → live is the natural promotion path for trading work, and it gives the agent a place to be wrong cheaply. The playbook study already judged the playbook better on this row (deploy-envs), so this moves toward the article.

**(e) Criteria and decisions.** Safety +2 (live gets a dedicated gate). Attention and Autonomy +1 (paper deploys never wait). Audit and Article +1. Touches decisions 13, 19 and 26, and R39 and R41.

### #1 Delegation grant (+11): port via R52

**(a) What it is.** When the owner writes an intent they add `mode: delegated` and a risk class; the policy delegates only `low`. The agent may then sign the spec and the plan, and a merge workflow running from main merges the PR when review shows zero Important findings. The agent can never sign the intent, so it can't grant itself autonomy.

**(b) In sdlc-framework.** The owner pushes an intent containing `Autonomy: delegated`. Decision 30's fast lane already skips (a), and (b) is already skipped for a routine plan. What changes is gate (e): the App merges the moment the build is green and none of these is present:

- a "Decisions taken for you" line
- a risk-list hit
- a declared production

The gate already reads the intent as the owner merged it, so the grant is unforgeable by construction. Any red signal voids it, and the PR falls back to a normal (e) wait.

**(c) Recommendation.** Add this to R52 as a second trigger next to "merge by silence". Keep R52's preconditions: R22's App merge, R26's measures, and R50's trigger of 20 changes. Opt-in per project with `sdlc.yaml: delegation: off | low`.

**(d) Why.** Silence is implicit consent: the owner still has to see the notification and choose not to act. A grant is explicit, recorded, and decided when the owner has the most context, while writing the intent. It also has zero latency, and it is the purest form of "approve the plan once, the rest runs".

**(e) Criteria and decisions.** Attention and Autonomy +2. Audit +1 (the grant sits in git). Safety and Article −1 (no human merge at (e)). Amends decision 4 opt-in, as R52 already does; touches decisions 13, 18 and 30.

### #2 Serial run-queue (+10): port via R51

**(a) What it is.** The owner grants N items up front, and `next_item.py` hands them out one at a time, oldest first. A parked item is skipped and the queue moves on; only the owner's `resumed:` line brings it back. Each item gets a fresh session seeded from a handoff file.

**(b) In sdlc-framework.** The owner pushes four intents on Friday night, with `sdlc.yaml: queue: serial` set.

1. Change 0021 starts and the other three get the label `sdlc:queued`.
2. 0021 parks at (b), so 0022 starts.
3. The owner's un-park label on 0021 puts it back in line behind 0022.
4. The digest shows the queue order.

**(c) Recommendation.** Make serial mode the first step of R51 and the default. R51's concurrency safety (rebase, re-check, reserved ids) becomes the opt-in for parallel work.

**(d) Why.** One change at a time removes the stale-base and id-collision problems R51 has to engineer around. It matches the article's ceiling, which decision 17 already cites: parallel streams are worth only as many as one person can review. The cost is throughput on unrelated changes.

**(e) Criteria and decisions.** Autonomy +2 (a batch handed over at once). Safety +1 (no concurrent writers). Attention +1 (queue once). Consistent with decisions 11, 17, 20 and 24.

### #9 Metrics per play (+4): fold into R26

**(a) What it is.** `docs/sdlc/metrics.md` pairs a leading and a lagging indicator for each playbook play. Only a few were ever computed.

**(b) In sdlc-framework.** There are global counters today, and R26 adds DORA and first-pass share by plan class. For example, design would get a leading indicator ("panel calls at (b)") paired with a lagging one ("changes needing a fix round").

**(c) Recommendation.** Don't port it as its own thing. Inside R26, label each counter with the phase it measures and the decision it informs; R26's title already says "measures that change a decision".

**(d) Why.** lifecycle-axis- defined many metrics and computed few. Pairing the counters is the cheap part worth keeping.

**(e) Criteria.** Audit and Article +1; nothing else changes.

### #7 Gemini (+3 as a reviewer; −3 as parity): via R8

**(a) What it is.** One rule source generated CLAUDE.md, GEMINI.md and AGENTS.md, and the Gemini CLI ran the same hooks. In practice the CLI refused the owner's personal account, and Antigravity ignored the hooks.

**(b) In sdlc-framework.** Every phase is `claude -p` in GitHub Actions, so parity would mean a second CLI, a second hook wiring and a second set of context files, all for runs that never use them. The useful form is R8: Gemini gives a second opinion on the design at (b) and never parks.

**(c) Recommendation.** Skip parity. Advance R8, and later consider Gemini as the panel's devil's advocate.

**(d) Why.** The panel's own rule is that judges on one model share its blind spots. Opus versus Fable is still one vendor; Gemini is real model diversity. It also fits the owner's plan of using Gemini as helpers under Claude.

**(e) Criteria and decisions.** As a reviewer: Safety and Audit +1. As parity: Attention −1 (two configs to maintain). Touches decisions 6 and 7.

### #4 SHA-bound release authorization (+1): already covered

**(a) What it is.** A production deploy needs `.sdlc/release-authorizations/<sha>`, or a secret equal to that exact SHA. Any other commit is refused.

**(b) In sdlc-framework.** `plugin/release/approval.py` already accepts the label only when the checkout is the build PR's own head or its merge commit. The release is recorded on `refs/sdlc/released/<id>`.

**(c) Recommendation.** Don't port it. At most, record the head SHA at labeling time in R11's `approvals` list, which the x-audit row already plans.

**(d) Why.** The only gap is a fix round that pushes after the label. The owner's merge at the new head is a second act on that exact content, so the gap closes itself.

**(e) Criteria.** Safety +1, marginally; nothing else changes.

### #5 Plan as a hard boundary (+1): already covered

**(a) What it is.** A hook blocks edits until the plan is approved, and CI fails any diff that touches files outside the plan's list.

**(b) In sdlc-framework.** The phase structure already does this: the (b) run is read-only, the first run with edit tools is (c), which starts only after (b), and the `plan_sync` hook and gate check judge departures by file name.

**(c) Recommendation.** Don't port it. The one gap is a by-hand `/sdlc-build` on the owner's PC before the design PR merges, which would take a one-line preflight refusal.

**(d) Why.** The playbook study already decided "keep" on this row (build-plansync).

**(e) Criteria.** Safety +1, marginally.

### #6 Deterministic evals (+1): already covered

**(a) What it is.** 49 YAML cases that run the hooks and CI scripts against fixtures, plus 6 model-driven cases.

**(b) In sdlc-framework.** `tests/test_hooks.py` alone has 155 tests, within about 1,480 overall, plus 6 evals. The test-evals row adds evals on `sdlc.yaml` and `policies/`, and cases drafted from merged changes after the 20th change.

**(c) Recommendation.** Don't port it. The coverage exists in pytest, and a second format would double the maintenance.

**(d) Why.** The two suites would cover the same guardrails in two places.

**(e) Criteria.** Safety +1, marginally.

### #10 Multi-approver roles (−2): don't port

**(a) What it is.** `approvers.yaml` maps each artifact to the roles allowed to approve it, CODEOWNERS enforces those roles, and a never-approve list blocks the bot identities.

**(b) In sdlc-framework.** Gates would check the actor against a role list instead of `owner`. With one person, every role is still the owner.

**(c) Recommendation.** Don't port it. The playbook study kept the one-owner premise (x-roles) and added role briefs instead. Revisit only if a collaborator joins.

**(d) Why.** For a solo owner it adds acts without adding separation.

**(e) Criteria.** Attention −2 and Autonomy −1; Article +2 (the playbook spreads roles across people); net negative under the weights.

### #8 Local-session execution (−15): don't port

**(a) What it is.** Work runs in sessions on the owner's machine, chained by handoff files, with no model spend in CI.

**(b) In sdlc-framework.** This would reverse decision 1: the PC would have to be on, and runs would stop when it sleeps.

**(c) Recommendation.** Don't port it. Handle cost through R25 (a weekly ceiling and a budget per change).

**(d) Why.** Cost has weight 0 in the owner's criteria, and local runs break the hands-off model. The $50–85 per change are estimates; decision 1 also accepts the subscription token, so actual marginal cost may be lower.

**(e) Criteria.** Attention and Autonomy −2; Audit and Safety −1; only Cost rises (+2), and Cost has weight 0.

## ROADMAP entry: R60, no decision

R60 now asks for a second, independent study and a judged comparison before the owner decides; this doc is Study A. The first version (merged in [PR #268](https://github.com/luissiviero/sdlc-framework/pull/268)) is substituted in [PR #270](https://github.com/luissiviero/sdlc-framework/pull/270).

| Field | Value |
| --- | --- |
| # | R60 (last in line) |
| Candidate | Which lifecycle-axis- features to port, settled by two independent studies and a judge |
| Source | `docs/proposals/lifecycle-axis-features.md` |
| Decisions it touches | None; the studies name them |
| Status | Proposed, no decision |
| Order | Blank |

1. **Study B.** A new session studies both repos without reading this doc, and commits its study first.
2. **Study A.** Only then does it read this doc and record it beside Study B.
3. **Judge.** A fresh context that wrote neither study compares them blind to authorship and checks disputed claims against the code.
4. **Owner.** The conclusion is a recommendation; the owner decides.

The repo's R60 entry states no finding of this study, so the new session keeps its independence. Records go to `docs/reviews/2026-10-20-lifecycle-axis-ports/`.

## Sources

Both repositories were cloned on 2026-10-19 and profiled file by file. Each repo's test suite was run on a scratch copy; both passed.

- [lifecycle-axis-](https://github.com/luissiviero/lifecycle-axis-) at commit `80328c1` (2026-09-18)
- [sdlc-framework](https://github.com/luissiviero/sdlc-framework) at commit `63d2710` (2026-10-19), plugin v1.0.13
- Spend figures: `evidence/spend.json` of sdlc-framework changes 0001, 0002, 0003 and 0005
