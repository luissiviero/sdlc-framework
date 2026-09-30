# The framework as the owner wants it

**Tentative until the study ends.** This page collects what the owner wants the framework to become, as the playbook-versus-framework study (`../2026-09-28-playbook-vs-framework.md`) goes row by row. Nothing here changes the current version: no plugin, template, `docs/DECISIONS.md` or `docs/ROADMAP.md` edit follows from an entry until the owner confirms it after the whole study. Then each confirmed entry becomes a proposal under `docs/proposals/` and a candidate row in `docs/ROADMAP.md` ("proposed"), in ROADMAP's own format.

Each entry: the owner's idea in the owner's words, the direction discussed so far, the crosswalk rows it touches, the settled decisions (Dn) it would reopen or amend, what is still open, and a status: **tentative**, **confirmed** or **dropped**.

| Id | Entry | Status | Recorded |
|---|---|---|---|
| T1 | AI roles that advise, and one manager that reviews for the owner | tentative | 2026-09-30 |
| T2 | The interview: how the manager and the roles question the owner | tentative | 2026-09-30 |

## T1. AI roles that advise, and one manager that reviews for the owner

**Status:** tentative (the owner agrees with the direction below; the matter is not settled).

**The owner's idea.**
- No review made alone any more: AI roles modelled on the article's roles (p.9-50) guide the owner's decisions.
- One project manager as the review companion, always holding the bigger picture (intent, spec, plan, what came before). It gathers what the roles found and suggests what to do.
- The manager never touches the project; its job is a reviewer's. The owner would let this manager, and only it, carry out in the owner's name the acts only the owner can do today (merges to `main` and the rest), each one approved by the owner.
- Still to investigate: which models, which documentation each role reads, and fewer roles by merging roles with similar jobs.

**Direction discussed (tentative).**
- **The roles advise, the owner decides.** Each role writes a short brief from its own field and its own sources; the manager reads all briefs and recommends; the owner remains the only approver. Roles on a model bring back a second perspective, not a second accountability: agents running on the session's model share its blind spots (all four agents are `model: inherit`, `plugin/agents/*.md`; D21 already puts the panel's advocate on another model for this reason, `sdlc.yaml: panel_advocate_model`).
- **The manager acts in the owner's name only through a signal the owner alone can give.** The manager prepares an act; the owner approves it from the owner's account (a label or an approving review); a deterministic workflow, not a model, checks who approved and carries the act out. The framework already works this way for one act: the owner's `sdlc:go` label on an incident PR makes `sdlc-runbook.yml` run the runbook once, after checking that the label's actor is a person and recording it (`status.yaml: runbook_authorized_by`).
- **The manager's summary must not replace the briefs.** If the owner reads only the manager, the manager becomes the single point of failure; each brief stays one click away.
- **Where it lives.** The role and manager definitions are process content, so they belong in `plugin/` (agents or skills), versioned and pinned like the rest (D8). What each role reads is project content: the project's policies, product vision and constraints live in each project, with slots created by `/sdlc-init`. A separate repository only pays off if the roles are wanted outside this plugin.
- **Fewer roles, a first cut to adjust:**

| Merged role | Covers (article roles) |
|---|---|
| Product | originator, product owner |
| Architect | tech lead or architect, the engineer's plan review |
| Code reviewer | code owner (today's REVIEW.md pass) |
| Security & policy | security lead, policy owners |
| Platform & release | platform engineer, release manager |
| Operations | service owner or on-call |

**Crosswalk rows it touches:** x-roles, plan-accept, design-concerns, design-go, build-plan-approve, build-config, build-skills, build-risk, deploy-approve, deploy-release, maintain-triage, maintain-scan, setup-merge.

**Settled decisions it would reopen or amend:**
- D4 (only the owner merges), D5 (the automation identity), D13 (gate (e) is the merge) and D24 (the owner's labels), for the manager acting in the owner's name;
- D21 (who sits on the panel) and D11 (whether a missing brief parks a change);
- no Dn states the one-owner premise today (`docs/OPERATING_MODEL.md` §2, build guide step 5); the roles would need a decision of their own.

**Open.**
- Which model each role runs on.
- Which documentation each role reads: the five policy skills each say "no owner source yet" (`plugin/skills/*/SKILL.md`).
- How many roles after merging.
- To verify: whether a GitHub ruleset can let a workflow merge on the owner's behalf, or whether that needs a dedicated GitHub App.
- Whether a role brief is advice only, or whether a missing or negative brief parks the change.

## T2. The interview: how the manager and the roles question the owner

**Status:** tentative.

**The owner's question.** How is the interview conducted: are the manager and the roles involved, and how is the prompt built for the model that receives it? The owner wants to explain the idea, show examples of what is wanted, and be asked questions that build the intent, the plan and the rest.

**Today.** `/sdlc-plan` (phase (a)) is the only interview: Claude asks an analyst's questions a few at a time (scope, users and systems, constraints, success, route, change type), drafts `intent.md`, and the owner corrects it until it is right (`plugin/commands/sdlc-plan.md`). The spec and the plan are written unattended in CI and never ask the owner anything (`plugin/commands/sdlc-design.md`); open points reach the owner at gate (b). The intent template has no place for examples or references (`plugin/skills/intent-template/SKILL.md`); files saved in the change folder ride with the intent PR, and the only named slot is `mock/` for an exported design mock, committed with the spec at (b).

**Direction discussed (tentative).**
- **The manager leads, the roles feed it.** The manager hears the idea; each role, as a sub-agent, proposes the questions of its field (Product: scope and success; Architect: technical constraints; Security & policy: data and auth; Operations: how the app runs and is watched); the manager merges them, drops duplicates and asks the owner a few at a time, the most important first.
- **After the draft**, each role reviews the intent and the manager shows the owner what is still open, by role.
- **Prompts across models.** One role card per role, independent of the model: mission, sources, what it must output and in which format. The manager assembles each prompt from the card, the change's artifacts and the project's sources; per role only the model setting changes, not the prompt. Each role gets an eval that checks it stays in its lane (article p.22, step 4). Claude Code sub-agents run Claude models, so "which model" means a Claude model.

**Crosswalk rows it touches:** plan-idea, design-trigger, design-mock, build-plan.

**Settled decisions it would reopen or amend:** D1 and D2, only if a second interview is added before the spec or the plan (both are written unattended today).

**Open.**
- A second interview before the spec, or before the plan (the article's plan mode interviews the engineer, p.15-16).
- A place in the intent for examples and references, and whether the roles read them.
