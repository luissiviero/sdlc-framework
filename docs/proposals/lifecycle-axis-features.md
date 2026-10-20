---
type: Proposal
title: Analyze the value of porting lifecycle-axis- features into the framework
description: The owner's earlier kit, lifecycle-axis-, has ten features that are stronger than the framework's equivalents; this entry only asks for an analysis of what each would be worth here. Nothing is decided.
status: proposed
roadmap: R60
sources:
  - id: owner
    resource: "the owner's message of 2026-10-19 ('add it to the end of the line but without any decision. The task is analyzing the value of adding these changes')"
    title: "The request to register the analysis"
  - id: lifecycle-axis
    resource: "https://github.com/luissiviero/lifecycle-axis- (HEAD 80328c1, 2026-09-18)"
    title: "lifecycle-axis-, the starter kit the framework replaced"
  - id: comparison
    resource: "https://claude.ai/code/artifact/9f0ad0d6-170a-4e4a-b841-89126493329d"
    title: "lifecycle-axis- vs sdlc-framework (comparison doc, 2026-10-19)"
generated: { by: claude-chat-session, at: 2026-10-20T02:30:00Z }
---

# Analyze the value of porting lifecycle-axis- features

**Status: proposed on 2026-10-19 at the owner's request (ROADMAP R60), placed last, no decision.** Nothing is built, accepted or ranked. The work this entry asks for is an analysis: for each feature below, what porting it would be worth to the framework, what it would cost, and which decisions it would touch. The owner decides afterwards.

## Why

The owner started with `lifecycle-axis-` (2026-09-02 to 2026-09-18, 673 commits) and stopped it for this framework. The framework fits the original goal better: phases run unattended in CI and the owner acts only at phase ends. A side-by-side read of both repositories on 2026-10-19 found ten features where `lifecycle-axis-` is stronger, mostly on control, trust and cost.

## The features to analyze

The "initial estimate" column is a first read for a single, hands-off owner. It is an input to the analysis, not a decision.

| # | Feature in lifecycle-axis- | Where it lives there | The framework today | Initial estimate |
|---|---|---|---|---|
| 1 | Delegation grant: `mode: delegated` plus a risk class on the intent; the agent signs spec, plan and incident, never the intent | `.sdlc/delegation.yaml`, `scripts/sign.py` | No: only the owner approves (decision 34) | High |
| 2 | Run-queue across items, with park and resume and one successor session per item | `.claude/skills/sdlc-run/SKILL.md`, `scripts/next_item.py`, `docs/sdlc/handoff/HANDOFF.md` | Partial: concurrent changes are R51, not built | High |
| 3 | Environment tiers: agent deploy and rollback in dev and staging; production allows only prepare-release and propose-rollback | `.sdlc/environments.yaml` | No: a single `deploy:` block in `sdlc.yaml` | High |
| 4 | Release authorization bound to the exact commit SHA | `scripts/deploy.sh`, `.sdlc/release-authorizations/` | Partial: the `sdlc:release-approved` label (decision 13) | Medium |
| 5 | Plan as a hard boundary: a hook blocks edits until the plan is approved; CI fails a diff that touches files outside the plan's list | `.claude/hooks/require-plan.sh`, `scripts/check_artifact_chain.py` | Partial: `plugin/hooks/plan_sync.py` checks that the plan is kept in sync, not that it was approved | Medium |
| 6 | 55 eval cases, 49 of them deterministic regression tests for hooks and CI scripts | `evals/cases/`, `scripts/run_evals.sh` | 6 eval cases | Medium |
| 7 | Gemini parity: one rule source rendered into CLAUDE.md, GEMINI.md and AGENTS.md, with drift and size checks | `docs/sdlc/rules/`, `scripts/gen_context_files.py`, `.gemini/settings.json` | No | Medium (the Gemini CLI refused the owner's personal account in lifecycle-axis-) |
| 8 | Local-session execution: no model spend in CI per change | `docs/sdlc/handoff/HANDOFF.md` (session protocol) | Each change runs in GitHub Actions; about 50 to 85 USD per change on changes 0001 to 0005 | Medium |
| 9 | Metrics per play: one leading and one lagging indicator each | `docs/sdlc/metrics.md` | Global counters only (`plugin/pr/counters.py`) | Low |
| 10 | Multi-approver roles: approvers file, CODEOWNERS, a never-approve list of bot identities | `.sdlc/approvers.yaml`, `.github/CODEOWNERS` | Single owner | Low (one owner) |

## What the analysis should answer, per feature

1. The value to the owner's way of working: fewer interruptions, less spend, or fewer ways for an agent to go wrong.
2. The cost: code, workflows and docs added, and what it adds to a small project's scaffold.
3. The decisions it would touch or reopen. Likely candidates are decision 13 (release authorization), 23 (GitHub only) and 34 (who approves), but the analysis names them.
4. Whether part of it already exists under another name in the framework or in an accepted candidate (R11 to R57).

## What this entry is not

It accepts nothing, amends no decision and takes no rank. The Order cell stays blank until the owner decides.
