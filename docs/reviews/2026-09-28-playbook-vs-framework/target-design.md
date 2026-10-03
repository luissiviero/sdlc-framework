# The framework as the owner wants it

**Tentative until the study ends.** This page collects what the owner wants the framework to become, as the playbook-versus-framework study (`../2026-09-28-playbook-vs-framework.md`) goes row by row. Nothing here changes the current version: no plugin, template, `docs/DECISIONS.md` or `docs/ROADMAP.md` edit follows from an entry until the owner confirms it after the whole study. Then each confirmed entry becomes a proposal under `docs/proposals/` and a candidate row in `docs/ROADMAP.md` ("proposed"), in ROADMAP's own format.

Each entry: the owner's idea in the owner's words, the direction discussed so far, the crosswalk rows it touches, the settled decisions (Dn) it would reopen or amend, what is still open, and a status: **tentative**, **confirmed** or **dropped**.

| Id | Entry | Status | Recorded |
|---|---|---|---|
| T1 | AI roles that advise, and one manager that reviews for the owner | tentative | 2026-09-30 |
| T2 | The interview: how the manager and the roles question the owner | tentative | 2026-09-30 |
| T3 | The intent home: in the repository, written from anywhere, with examples | tentative | 2026-09-30 |
| T4 | Names: the phases named after what they produce, and the other names judged against the article | tentative | 2026-09-30 |
| T5 | Starting a project: the whole loop from the first change, with an optional start by hand | tentative | 2026-10-02 |
| T6 | Tickets become intents: a GitHub issue the owner labels starts the intent PR | tentative | 2026-10-02 |
| T7 | A rejection keeps its reason: the owner's closing comment is saved with the change | tentative | 2026-10-02 |
| T8 | The formatter follows the project's languages: per file type, the project's own commands on the changed file | tentative | 2026-10-03 |

The target workflow page (https://claude.ai/artifact/13X8rzF9KsfekmeSs1w5rM, snapshot `target-workflow.html`) draws every entry. The crosswalk page (https://claude.ai/artifact/PFnRZ32pwTr4y422Gna2mz) shows T1 to T3 in a third column, "Target (tentative)", on the cards of the rows they touch, and `crosswalk.json` carries the same condensed text in each row's `target` field and in `targets`; at the owner's request the crosswalk is not extended with later entries (the review record's section 7).

## T1. AI roles that advise, and one manager that reviews for the owner

**Status:** tentative (the owner agrees with the direction below; the matter is not settled). Confirmed on design-concerns (better: the playbook; decision: blend, 2026-10-02): under parked review each open concern reaches the owner with the brief of the role of its kind and the manager's recommendation; under deferred review that role sits on the panel in place of the general reviewer (amends D21's panel line-up); the never-to-the-panel list stays. Confirmed on design-go (better: both; decision: blend, 2026-10-02): the owner's merge of the gate (b) PR stays the go to build (D2 and D18 unchanged); added: a spec verdict and a plan verdict in the one PR, and a "Needs your close look" banner, with the reasons, when the plan is classed non-routine or a risk-list item is hit; the same approval, no separate one (see the approvals table). Confirmed on build-plan (better: the playbook; decision: blend, 2026-10-02): the writer of the plan still answers the plan template's interrogation questions, and a fresh context also asks the article's three (what could break, the riskiest step, the options not chosen, p.16 step 3): the adversarial reviewer at (b) until the roles exist, then the Architect's brief, which feeds the plan verdict; the answers are committed in `evidence/`. Confirmed on build-plan-approve (better: both; decision: blend, 2026-10-02): the plan is approved in the same merge as the spec; a higher-risk plan gets the Architect's full review, whose recommendation (go, or fix first) the "Needs your close look" banner quotes unchanged; the runner records who accepted the plan, when, under which class and whether the close look was shown (the approvals table and the bullets below it). Confirmed on build-start (better: the framework; decision: blend, 2026-10-03): the unattended start stays the default; added, a per-change switch to the Full profile the owner flips at the gate (b) merge by labelling the design PR, so that change's (c) and (d) wait for the owner's labels; nothing happens without the label. Confirmed on build-subagents (better: the framework; decision: keep, 2026-10-03): the workers stay sub-agents and the judges become roles, in one agent catalogue in which every agent is created the same way (below).

**The owner's idea.**
- No review made alone any more: AI roles modelled on the article's roles (p.9-50) guide the owner's decisions.
- One project manager as the review companion, always holding the bigger picture (intent, spec, plan, what came before). It gathers what the roles found and suggests what to do.
- The manager never touches the project; its job is a reviewer's. The owner would let this manager, and only it, carry out in the owner's name the acts only the owner can do today (merges to `main` and the rest), each one approved by the owner.
- Still to investigate: which models, which documentation each role reads, and fewer roles by merging roles with similar jobs.

**Direction discussed (tentative).**
- **The roles advise, the owner decides.** Each role writes a short brief from its own field and its own sources; the manager reads all briefs and recommends; the owner remains the only approver. Roles on a model bring back a second perspective, not a second accountability: agents running on the session's model share its blind spots (all four agents are `model: inherit`, `plugin/agents/*.md`; D21 already puts the panel's advocate on another model for this reason, `sdlc.yaml: panel_advocate_model`).
- **The manager acts in the owner's name only through a signal the owner alone can give.** The manager prepares an act; the owner approves it from the owner's account (a label or an approving review); a deterministic workflow, not a model, checks who approved and carries the act out. The framework already works this way for one act: the owner's `sdlc:go` label on an incident PR makes `sdlc-runbook.yml` run the runbook once, after checking that the label's actor is a person and recording it (`status.yaml: runbook_authorized_by`).
- **The manager's summary must not replace the briefs.** If the owner reads only the manager, the manager becomes the single point of failure; each brief stays one click away.
- **A brief, never an approval.** On the record a role writes "security brief", not "security lead: approved", so the ledger never reads stronger than what a model can give.
- **Sources first.** A role is only as good as what it reads: without the owner's written policies a "security lead" is the generic model under another name. Writing those sources (security, data, coding standards, UX, definition of done) is the first step and needs no code; each policy skill has a line waiting for its owner source.
- **Where the roles help most** is where a check is lost with nothing in its place: gate (a), where the owner merges the owner's own intent after deterministic checks only, with no reviewing agent (`plugin/gate/checks.py`, `CHECKS_BY_PHASE["a"]`); the owner's own edits to CLAUDE.md, skills and `sdlc.yaml`; the skill sign-off; flagged concerns by kind at (b); higher-risk plans at (b); the release checklist on a declared production; triage at (f).
- **Each role gets an eval** that asks for its task without naming the role and checks it stays in its lane (article p.22, step 4).
- **Cost.** Every role is one more run per change. The owner weighs cost at 0; the per-change dollar cap, off by default, is compared with the change's running total since plugin 0.3.1 (`evidence/spend.json`, one entry per session; issue #71).
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

**One agent catalogue (build-subagents, 2026-10-03).** The owner chose to keep today's sub-agents and to fold the roles and the sub-agents into one catalogue; they keep different objectives, but every agent is created the same way.
- **Workers stay sub-agents:** the verifier, the code-simplifier and the researcher do work for the session and report to it; the roles may use the researcher to read the code.
- **The judges become roles:** at (b) the adversarial reviewer grows into the Architect (as build-plan decided); at (e) the REVIEW.md pass becomes the Code reviewer; the panel member of a concern's kind becomes that role (design-concerns).
- **Two reviewers, two jobs.** Today they are separated by when they run and what they give: the adversarial reviewer gives the gate a verdict (continue or escalate, and the plan's class) at (b), (c) and (d), and asks "should this output continue?" from six angles (intent, spec and plan, proof, blast radius, policies, tests), reading REVIEW.md for what Important means (`plugin/agents/adversarial-reviewer.md`); the REVIEW.md pass gives findings ranked Important or Nit at (e), read by the owner at the merge (`template/REVIEW.md`). So today their questions overlap: both look at the policies and at whether the code matches the spec and the plan. The direction chosen: the Code reviewer asks "is the code good?" (bugs, security, compliance), and the adversarial reviewer, which at (c) and (d) stays a checker reporting to the gate rather than a role writing to the owner, centres on "is the claim that it is done proven?"; how far its angles narrow is open (below). They keep a fresh context each and, ideally, different models (the to-do under Open).
- **The same card for every agent:** mission, reports to (the owner through the manager, the session, or the gate), model, the skills and documents it reads, its tools, its output format and its own eval (by analogy with the skill trigger test, article p.22 step 4). A role may load a skill and a sub-agent may read a source.
- **Where each field is decided:** build-skills decides the documents, for every agent; x-roles decides the list, the reporting lines and the models, for every agent. The documents and the cards themselves are written after the study, sources first.
- **Today:** four agents in the pinned plugin, all `model: inherit`: the code-simplifier in (c) and in a build fix round, the verifier in (c), (d) and a build fix round, the adversarial reviewer for the gate's verdict at (b), (c) and (d), the researcher available to any session (no command calls it); under deferred review the panel's three members also run as sub-agents in any phase, the devil's advocate being the adversarial-reviewer agent on `panel_advocate_model` (`plugin/agents/`, `plugin/panel/`).

**Approvals with the roles and the manager (tentative).** The owner's approval points stay where they are; what reaches the owner at each one changes. The roles write briefs, the manager turns them into one recommendation, the owner decides, and the act runs on the owner's signal (above).

| Gate | Role briefs | The manager brings the owner | The owner |
|---|---|---|---|
| (a) intent | Product (scope, success), Architect (feasibility) | accept, or the points to fix first, with the briefs linked | approves or sends corrections |
| (b) spec + plan | Product (does the spec solve the intent), Architect (the plan, and the article's three questions of it), Security & policy (flagged concerns) | two recommendations in the one PR: one for the spec, one for the plan | approves both or rejects one |
| (b), higher risk: the plan classed non-routine, or a risk-list hit | the same, plus the Architect's full plan review, in the article's tech-lead place (p.14, p.17): it reads the code the plan's "Files that change" names, answers the article's three questions with evidence (p.16 step 3) and ends with its own recommendation on the plan, go or fix first | "needs your close look" at the top of the PR, with the reasons: before T1 the adversarial reviewer's classification reasons and the risk hit, verbatim; with T1 the Architect's recommendation, quoted unchanged, the brief one click away | the same approval, after a close look; no separate gate (design-go: a separate approval was considered and not chosen) |
| (b), a plan the owner wants watched through build and test | the same | the class and its reasons, in the banner | labels the design PR before merging: the change runs under the Full profile, so (c) and (d) wait for the owner's labels (build-start, 2026-10-03); without the label the build starts on its own, as today |
| (e) code | Code reviewer (today's REVIEW.md pass), Platform & release | merge or request changes, with the Important findings | approves; the merge runs on the owner's signal |
| (f) incident | Operations, Security & policy (scans) | fix now, schedule or dismiss | triages |

- Separate verdicts, not separate gates: a spec verdict and a plan verdict inside the one gate (b) PR bring back the article's split (p.14, p.17) without another wait, so D2 can stay. The owner approves both or rejects one; a rejection is a "Request changes" review whose comments `/sdlc-fix` applies (D22).
- A closer look only for risk, not a stricter gate (design-go, 2026-10-02): a higher-risk plan gets a marked close look in the same approval, not a separate one, because the owner holds both the product owner's and the tech lead's part and would wait on their own second approval. The signal exists today: the adversarial reviewer's `classification` and `classification_reasons` (`plugin/gate/checks.py`, `load_verdict`), which only lower the iteration cap (`plugin/gate/limits.py`, D11), and the risk-list check, which reads the committed diff's file paths (not their contents) and the spec's Flagged concerns, and parks for `sdlc:accept-risk`; once accepted, the item lives in `status.yaml: risk_accepted`, so the banner reads it from there. The banner needs no roles, so it can come before them.
- The record of the plan's acceptance (build-plan-approve, 2026-10-02): the article logs "the plan and its revisions … along with who accepted it" (p.17); today GitHub's merge record on the spec+plan PR is the only log of who accepted, and the class under which the plan was accepted is never written beside it. At the start of phase (c) the runner writes one line to `status.yaml` and the (c) evidence: plan accepted by the merge actor, on which date, class routine or non-routine, close look shown or not, the risk items accepted. No act from the owner: `sdlc-build.yml` fires on the merged PR and the runner already reads its file list (`pr_files`); the merge actor would come from the pull object (`pr_by_number`, `GET /repos/{repo}/pulls/{number}`, whose response carries `merged_by`, which `_pr_from_api` would have to keep) or from the workflow's `pull_request` event payload; the gate (a) and (e) merges are already derived from the merge (`merged_at_gate_a`, `merged_at_gate_e` in `plugin/state/status.py`).
- When a separate plan gate is reconsidered (build-plan-approve, 2026-10-02): D2 option C is reopened only if the digest's first-pass merge share or fix iterations per shipped change (`plugin/pr/counters.py`, rendered in the digest by `plugin/pr/digest.py`) worsen on non-routine plans, the article's own indicators for this play (p.17). Which indicators to compute stays with the crosswalk row x-measure. Considered and not chosen: a negative Architect recommendation that parks the change, because it would reopen D11's "never parks" before the open question below on a negative brief is settled.
- The autonomous start stays the default (build-start, 2026-10-03): the owner's gate (b) merge fires the build, the preflight allows `acceptEdits` when the guardrail checks pass (`plugin/gate/preflight.py`), and the Standard profile continues to (d) on its own (D1, D2, D11, D18 unchanged). The article's "auto-accept only for routine work" (p.17) is not applied as written, since unattended there is no per-edit approver to fall back to; the routine test is the class in the "Needs your close look" banner, which the owner decides with. Added: a per-change switch to Full at that merge. A per-change `profile_override` already exists in `status.yaml` (asked at `/sdlc-plan`, read from the default branch's copy, `plugin/ci/run_phase.py`), but it is set before any class exists; the owner's label on the design PR before merging would be read by the build runner from the merged PR's label events (as `label_actor` reads the approval labels) as `profile_override: full` for that change. Considered and not chosen: non-routine plans automatically to Full, or a park before the build, which would reopen D11 and stop almost every change in a new project.
- Gate (a) gains the most: today it has no reviewing agent.
- Settled decisions: D2 and D18 stay (design-go: separate gates are not wanted); D11 and D21 keep their substance, since non-routine still never parks or notifies, but their wording that non-routine "only tightens the gate" / "only lowers the iteration cap" gains the banner; and the set above for acting in the owner's name.

**How the roles and the manager communicate (tentative).** A sub-agent hands back only its final message; what it read and weighed is lost when it ends, and a CI runner is thrown away (the stored run result holds the final message and metadata, not the conversation, issue #72). So the roles and the manager talk through files, as the panel already does ("Each member writes exactly one file under `changes/<id>-<slug>/evidence/panel/`", `plugin/panel/prompts.py`) and as the adversarial reviewer's JSON verdict does for the gate:

1. Round 1: each role runs in a fresh context, blind to the others, reads the change's files and its own sources, and writes `evidence/roles/<role>-r1.md` in a fixed shape: verdict, reasons with sources, questions for the owner, what it could not check.
2. The manager reads every brief and writes `evidence/manager.md`: its recommendation, where the roles agree or disagree, and a link to each brief.
3. Round 2, only on a disagreement: the manager starts the roles concerned again with the other brief as input; they write `-r2.md`. A new run, not a continued chat.
4. Everything is committed with the change, so the exchange can be read months later.

The roles keep no memory on purpose: each judges from the files alone (writer ≠ judge); a role that carried the manager's conversation would drift toward the manager's view. What is lost is a role's reasoning between reading and writing, which is why the brief must give its reasons with sources.

**Full conversations: two tiers.** Useful now and then (a wrong recommendation to debug, a role card to tune), rarely read otherwise, and too large and too exposed to commit (a transcript holds every file the run read).

| What | Where | How long |
|---|---|---|
| Briefs and the manager's recommendation (short, fixed format) | committed in `changes/<id>-<slug>/evidence/roles/` and `evidence/manager.md` | for good: the record |
| Full transcripts | a workflow artifact of the run that produced them; the brief names the run | until the artifact expires (GitHub's default retention is 90 days, adjustable per repository, organization or upload); kept longer only by moving one into `evidence/` on purpose |

The framework already keeps the hook log both ways: committed in `evidence/` and uploaded as a workflow artifact (crosswalk row x-audit).

**Gates (tentative, from the owner's setup-gates choice).** No new gates: (a), (b), (e) and (f) stay, with (c) and (d) in the Full profile; the project items stay in `sdlc.yaml` (risk list, protected paths, production settings) and the enforcement stays as today (D6, D18 unchanged). What changes is what reaches the owner: at each gate the owner approves after the role briefs that gate names (the approvals table above); a risk-list hit still parks, and the matching role's brief comes before the owner's `sdlc:accept-risk`; the owner's own edits to the gates themselves get a role's brief before the owner merges them.

**Crosswalk rows it touches:** x-roles, x-audit, setup-gates, plan-accept, design-concerns, design-go, build-plan, build-plan-approve, build-start, build-subagents, build-config, build-skills, build-risk, deploy-approve, deploy-release, maintain-triage, maintain-scan, setup-merge.

**Settled decisions it would reopen or amend:**
- D4 (only the owner merges), D5 (the automation identity), D13 (gate (e) is the merge) and D24 (the owner's labels), for the manager acting in the owner's name;
- D21 (who sits on the panel) and D11 (whether a missing brief parks a change);
- no Dn states the one-owner premise today (`docs/OPERATING_MODEL.md` §2, build guide step 5); the roles would need a decision of their own.

**Open.**
- To do: decide which model each role and each sub-agent runs on (owner's request, 2026-10-03, while weighing build-subagents). Today all four agents run on the session's own model (`model: inherit`, `plugin/agents/*.md`) and so share its blind spots, so a role or a reviewing agent brings a second perspective, not a second accountability; D21 already puts the panel's devil's advocate on a different model for that reason (`sdlc.yaml: panel_advocate_model`). Start with the agents that judge (the adversarial reviewer, the Architect, the Code reviewer), where a different model matters most.
- Which documentation each role reads: the five policy skills each say "no owner source yet" (`plugin/skills/*/SKILL.md`).
- How far the adversarial reviewer's angles narrow once the Code reviewer exists: today it also checks the policies, the spec and plan at (b), and the code against them at (c) and (d), where no Code reviewer runs.
- The agent catalogue's table, one line per agent (mission, reports to, model, documents read): the documents decided at build-skills, the list, reporting lines and models at x-roles; the documents themselves written after the study, sources first.
- How many roles after merging.
- To verify: whether a GitHub ruleset can let a workflow merge on the owner's behalf, or whether that needs a dedicated GitHub App.
- The approval check must confirm the signal came from the owner, not just from a person: today `sdlc-runbook.yml` checks only that a person, not a bot or the workflow token, applied `sdlc:go` (`plugin/detect/cli.py` `_human_label_actor`); from the owner's setup-merge choice.
- The record of a delegated merge: the merge commit, the owner's approval signal and the manager's recommendation in `evidence/` (setup-merge); with the owner's *Exempt* bypass GitHub writes no bypass audit entry for the owner's own merges.
- Whether a role brief is advice only, or whether a missing or negative brief parks the change.
- The exact fields of the plan-acceptance line, and where in the (c) evidence it goes.
- The name of the per-change Full label (judged with T4), and how the build runner reads it from the merged design PR and records it as the owner's override.
- Where the fresh context's answers to the article's three plan questions go: a new field of `evidence/adversarial-review-b.json` (a schema change the gate reads) or a file of its own; today the reviewer writes only the verdict (`plugin/agents/adversarial-reviewer.md`).

## T2. The interview: how the manager and the roles question the owner

**Status:** tentative. The owner's choice on the crosswalk row plan-idea (better: the playbook; decision: blend, 2026-10-02) takes this entry as the way an idea is interviewed: `/sdlc-plan` stays the entry point, and the role-fed interview led by the manager (T1) is added to it, nothing replaced. On design-trigger (both fine, keep, 2026-10-02) the owner chose no second interview before the spec. On build-plan (better: the playbook; decision: blend, 2026-10-02) the owner chose no live interview before the plan either, but questions in writing: the planning run ends Risks with a fixed "Questions for you" list (empty if none), the gate (b) PR shows it with the plan's riskiest step under the plan verdict (until T1 exists, beside the gate (b) checklist's plan question), and the owner answers in the "Request changes" review whose comments `/sdlc-fix` applies (D22).

**The owner's question.** How is the interview conducted: are the manager and the roles involved, and how is the prompt built for the model that receives it? The owner wants to explain the idea, show examples of what is wanted, and be asked questions that build the intent, the plan and the rest.

**Today.** `/sdlc-plan` (phase (a)) is the only interview: Claude asks an analyst's questions a few at a time (scope, users and systems, constraints, success, route, change type), drafts `intent.md`, and the owner corrects it until it is right (`plugin/commands/sdlc-plan.md`). The spec and the plan are written unattended in CI and never ask the owner anything (`plugin/commands/sdlc-design.md`); open points reach the owner at gate (b). The intent template has no place for examples or references (`plugin/skills/intent-template/SKILL.md`); files saved in the change folder ride with the intent PR, and the only named slot is `mock/` for an exported design mock, committed with the spec at (b).

**Direction discussed (tentative).**
- **The manager leads, the roles feed it.** The manager hears the idea; each role, as a sub-agent, proposes the questions of its field (Product: scope and success; Architect: technical constraints; Security & policy: data and auth; Operations: how the app runs and is watched); the manager merges them, drops duplicates and asks the owner a few at a time, the most important first.
- **After the draft**, each role reviews the intent and the manager shows the owner what is still open, by role.
- **Prompts across models.** One role card per role, independent of the model: mission, sources, what it must output and in which format. The manager assembles each prompt from the card, the change's artifacts and the project's sources; per role only the model setting changes, not the prompt. Each role gets an eval that checks it stays in its lane (article p.22, step 4). Claude Code sub-agents run Claude models, so "which model" means a Claude model.

**Crosswalk rows it touches:** plan-idea, design-trigger, design-mock, build-plan.

**Settled decisions it would reopen or amend:** none. D1 and D2 would have been reopened only by a second interview before the plan, and the owner chose none: before the spec, what the design pass cannot answer goes to its "Flagged concerns", which park for the owner (design-trigger, 2026-10-02, both fine, keep); before the plan, the planning run's questions go to the "Questions for you" list on the gate (b) PR (build-plan, 2026-10-02, blend).

**Open.**
- The exact wording of the "Questions for you" list at the end of Risks (inside `## Risks`: the plan template keeps the article's section names, `plugin/skills/plan-template/SKILL.md`), how `/sdlc-fix` marks a question answered, and the wording on the gate (b) PR.
- A place in the intent for examples and references (T3 proposes a section), and whether the roles read them.

## T3. The intent home: in the repository, written from anywhere, with examples

**Status:** tentative. Recorded from the owner's choice on the crosswalk row setup-home (better: the framework; decision: blend). Confirmed on plan-idea (better: the playbook; decision: blend, 2026-10-02): the claude.ai route is a second way to write an intent, added beside `/sdlc-plan`, and it must arrive as a PR on `sdlc/<id>/a`.

**The owner's note (saved on the crosswalk page).** "Blend: ideas stay in changes/<id>-<slug>/, set up by /sdlc-init (current). I write intents from Claude Code or from claude.ai / phone. I accept by merging, after a Product role's brief (T1). Template: the plugin default, overridable per project (to verify); a Product role reviews it and I approve (T1). The intent gets an Examples/References section (T2)."

**Direction discussed (tentative).**
- **Where:** as today, `changes/<id>-<slug>/` in the project repository: `/sdlc-init` sets up `changes/`, `/sdlc-plan` creates each folder through `plugin/state` (D8, D9, D10 unchanged; D10 chose this over the article's own advice for a single product, an `intent/` folder in the product repo, p.10).
- **From anywhere:** an intent can also be written from claude.ai (on a computer or a phone), the article's route for contributors who are not engineers (p.10: claude.ai or Cowork, with a connector to the version-control system that lets Claude commit the file on their behalf).
- **Accepted** by the owner's merge after the gate (a) briefs of T1 (Product, Architect).
- **The template:** the plugin's `intent-template` by default, overridable per project; a Product role reviews a change to it and the owner approves (T1).
- **Examples and references:** a section in the intent where the owner puts examples of what is wanted; `mock/` stays the slot for screens (T2 asks whether the roles read them). The `intent-template` skill fixes "exactly this shape", so the section is a change to the plugin's template, not only to one intent.
- **The mock (design-mock, 2026-10-02: better the playbook, decision blend).** Added, nothing replaced: when a change touches a screen, the interview asks "Do you have a mock or example screens?", and `spec.md` gets one line in its Acceptance section, "Mock: mock/<file>" or "Mock: none, screens follow the UX conventions" (the spec template's Acceptance already asks for "the screenshot or mock to match for UI"; the new part is the fixed `Mock:` line and its explicit "none"). The owner makes a mock in Claude Design when wanted; a missing mock never blocks. Considered and not chosen: making the article's front-end flow (p.12-13: the product owner mocks the design in Claude Design and exports it) a rule, a required mock for every screen change. References such as a competitor's screens go in Examples/References; the build matches the owner's mock, never those screens.

**Crosswalk rows it touches:** setup-home, plan-idea, design-mock.

**Settled decisions it would reopen or amend:** none known, provided the claude.ai route opens the intent PR on `sdlc/<id>/a` like `/sdlc-plan` and never commits to `main`: a claude.ai GitHub connector acts as the owner's account, the ruleset's only bypass actor (D4), so a direct commit would skip gate (a) (D10). The Product brief inherits T1's D11 question. Checked on plan-idea (2026-10-02): the owner requires the PR route, so none.

**Open.**
- Whether a project can override `intent-template` for `/sdlc-plan` (to verify); today only `/sdlc-design` documents a project override, for the five policy skills (`plugin/commands/sdlc-design.md`), `/sdlc-plan` names the plugin skill (`plugin/commands/sdlc-plan.md`), and gate (a) checks the plugin's `INTENT_SECTIONS` and header fields (`plugin/gate/artifacts.py`), so an override could add a section such as Examples/References but not drop or rename one.
- How an intent written in claude.ai gets its change id and folder: the id is allocated by `plugin/state` and never invented (`plugin/skills/intent-template/SKILL.md`), which a claude.ai conversation cannot run.

## T4. Names: the phases named after what they produce, and the other names judged against the article

**Status:** tentative. Recorded from the owner's questions of 2026-09-30: why `changes/` and not the article's `intent/`, which other names differ, and which name is better in each case, judged on the name alone, whatever decision approved it. The full table, 23 rows with the reason for each, is `naming.md` beside this page.

**The owner's rule for this entry.** A name that confuses is not kept because renaming costs something: either one side's name is better, or a third name is needed. Cost and the decisions behind the current names are listed apart, for the owner to weigh after the study.

**Direction discussed (tentative).**
- **Keep the framework's name** where it says more than the article's: `changes/<id>-<slug>/` (a folder of five kinds of file, not only the intent; T3 keeps it too), "planning run" rather than "plan mode" (the run is not the interactive feature), "park" (the article's "escalate" suggests paging, which D11 rules out; the adversarial reviewer's verdict becomes `park` so one event has one word), `security-baseline`, the spec sections.
- **Take the article's name** for the people who decide (product owner, code owner, release manager at each decision point, one person holding every role today) and for the triage queue ("findings", labels `sdlc:triage` and `sdlc:schedule`: a weekly scan result is not an incident, and those two labels are the only ones without the `sdlc:` prefix).
- **A third name where neither is good.** The main one: name each phase after what it produces or does — `intent`, `design`, `build`, `test`, `deploy`, `maintain` — in branches, labels and `status.yaml`, instead of the letters (a)–(f). This ends the clash in which `/sdlc-plan` writes `intent.md` while `plan.md` comes out of `/sdlc-design`; the clash starts in the article, whose "Plan" stage does not produce `plan.md` either, and its own dependency graph names the play "Capture intent" (p.8). The others: no `Status:` line in `intent.md` (it stays at `draft` after the merge; `status.yaml` is the one status), `sdlc-agent-evals.yml`, `authorization: allow | ask` for runbooks (the article's hook verbs, p.36), `deploy.production_gate`, `ux-and-brand`, and a profile name that says what `full` means.

**Crosswalk rows it touches:** setup-home, plan-idea, build-plan, build-skills, test-evals, maintain-triage, maintain-scan, maintain-act, deploy-release, x-roles.

**Settled decisions it would reopen or amend:** none in what the framework does; the names chosen in D3 (labels), D10 (branches), D11 (the verdict's word), D13 and D19 (the production switch), D14 and D26 (runbook authorization values), D18 (profile names) and D25 (the triage labels) would change. D2 stays: `plan.md` is still written in the design phase and approved with the spec.

**Open.**
- T1's advising roles and the owner's roles: if the owner's decisions are named by the article's roles (product owner, code owner, release manager), T1's AI roles need names that cannot be read as those people — T1 already writes "security brief", never "security lead: approved"; the role names themselves (Product, Architect, …) are to be checked against this.
- T2 and T3 name `/sdlc-plan`; under this entry it becomes `/sdlc-intent`.
- When: every rename also has to reach each project on the framework (today the sample project); the next project, `webapp-example`, is the last point with only one project to migrate. The order and the compatibility rules are in `naming.md`, "If a row is accepted".

## T5. Starting a project: the whole loop from the first change, with an optional start by hand

**Status:** tentative. Recorded from the owner's choice on the crosswalk row setup-adopt (better: the framework; decision: blend), 2026-10-02.

**The owner's note (saved on the crosswalk page).** "Blend: the whole loop from the first change stays the default (keep: no staged adoption, no per-phase switches). Added, nothing replaced: (#2) an optional, documented by-hand start - leave the Claude secret out, each phase job ends 'skipped' and I run the phase commands myself (the weekly scan fails until then); adding the secret later turns the automation on, nothing else changes (sdlc-init §6, README). (#3) the change-0000 intent lists what starts empty: evals (D17), lessons, CLAUDE.md 'Things Claude gets wrong', and the detection, which needs a CI workflow of the project's own and about 16 days of daily CI data before its first verdict (sdlc_init.py). Counting call: the playbook's adoption choice is a Setup decision (14 + 2)."

**Direction discussed (tentative).** Both additions add to the framework and replace nothing; the default stays as it is today.
- **The default, as today:** `/sdlc-init` installs the whole loop in the change-0000 PR. There is no staged adoption in the p.8 order and no per-phase switch; `sdlc.yaml: paused` still stops every phase at once. The article adopts the plays in the p.8 order and prompts each step by hand before automating it (p.8, p.13), and makes auto-accept the default only as the guardrails mature (p.17); the framework's own guardrails were built that way (by hand in stage B1, CI from B3), so a project does not repeat it.
- **An optional start by hand, documented:** without the repository secret (`CLAUDE_CODE_OAUTH_TOKEN` or `ANTHROPIC_API_KEY`), every phase job ends green as "skipped: no credential" (`plugin/ci/auth.py`; once the project's setup command has succeeded, since it runs first), and the owner runs each phase's command in their own Claude Code session. The weekly scan fails red instead until the secret exists. Adding the secret turns the automation on, and nothing else changes. This is the article's ladder, by hand first and then a job that fires on the merge (p.8, p.13), offered per project. Where it goes: one optional paragraph in `plugin/commands/sdlc-init.md` §6, which today presents the secret as required, and one sentence in `README.md`, "Phases by hand".
- **What starts empty, said in one place:** the change-0000 intent that `plugin/init/sdlc_init.py` writes gains a short list. It names the evals suite (D17; `evals/README.md` already says it starts empty), `lessons/`, the "(none yet)" in CLAUDE.md's "Things Claude gets wrong", and the detection. The detection needs a CI workflow of the project's own (the install report already warns when there is none) and about 16 days of daily CI data before its first verdict: 8 baseline points before the 8 most recent points it judges (`plugin/detect/stats.py`, `MIN_BASELINE`, `TAIL`). Today each fact sits in its own file, and the intent the owner reads before merging the install names none of them.

**Counting call (the same day).** On the playbook side, the organization's choice of which stages to transform first ("organizations may choose to prioritize transforming different stages at different times", p.7) counts as a once-per-project decision, so section 6 of the review record reads 14 + 2 for the playbook against the framework's 8 + 7.

**Crosswalk rows it touches:** setup-adopt.

**Settled decisions it would reopen or amend:** none. D1 (hosted CI) stays the default, and D17 (evals start empty) is only stated in one more place.

**Open.**
- Whether the weekly scan should end "skipped" like the phase jobs when no secret exists, instead of failing; that would be a code change, not only documentation.
- The exact wording of both additions, written after the study with the rest.

## T6. Tickets become intents: a GitHub issue the owner labels starts the intent PR

**Status:** tentative. Recorded from the owner's choice on the crosswalk row plan-ticket (better: the playbook; decision: blend), 2026-10-02. The owner wants to start using GitHub issues as the place where tickets arrive.

**The owner's note (saved on the crosswalk page).** "Blend, added and nothing replaced: alerts stay as today (detection and the weekly scan write the incident intent and open a PR; I correct it there with 'Request changes' and triage it), and /sdlc-plan with route 'ticket' stays. Added (T6): tickets arrive as GitHub issues; my label sdlc:intent on an issue starts a CI run that writes intent.md from the issue and opens the intent PR linked to it; what it cannot work out goes to Open questions; I correct and merge at gate (a) as today. Safeguards: only my own label starts a run (the workflow checks it was my account), and the issue text is read as data, never as instructions. No settled decision reopened."

**Today.** No workflow triggers on an issue (the template workflows use `issues` only as a token permission). A ticket becomes an intent only when the owner runs `/sdlc-plan` with route `ticket` and the ticket's number as its external reference. Alerts already become intents with no person: the detection runs `/sdlc-maintain`, and the weekly scan writes an intent per Important finding it routes.

**Direction discussed (tentative).** Added beside the routes of today; nothing replaced.
- **The trigger:** the owner applies the label `sdlc:intent` to an issue. A new workflow runs on that event, checks that the label was applied from the owner's account (not merely by a person, the check T1 asks for every approval), and starts a run that writes `changes/<id>-<slug>/intent.md` with entry route `ticket` and the issue as its external reference, then opens the intent PR on `sdlc/<id>/a`, linked to the issue.
- **What the run cannot work out** goes to the intent's "Open questions". The owner corrects the intent in the PR (review comments, or a "Request changes" review that starts the fix run) and accepts it by merging at gate (a), as today.
- **The issue text is data, never instructions:** anyone can open an issue on a public repository, so the run treats the title and body as quoted input, and only the owner's label starts it.
- **The record:** `intent.md` in the repository stays the record and the issue holds the link (D9's linkage rule).
- **Example:** issue #12 "Export the report as CSV"; the owner labels it `sdlc:intent`; the run writes `changes/0010-export-csv/intent.md` and opens the intent PR linked to #12.

**Crosswalk rows it touches:** plan-ticket.

**Settled decisions it would reopen or amend:** none. D9 (the repository is the record, issues hold links) is followed; the new label sits beside the owner's other labels (D3, D24).

**Open.**
- Whether a ticket intent gets the role-fed interview of T2; a CI run cannot interview the owner, so its questions go to "Open questions" in the PR.
- How the run is told the issue is untrusted input, and which tools it may use (the phase jobs' sandbox and settings, as today).
- The label's name, which T4 would judge with the other names.

## T7. A rejection keeps its reason: the owner's closing comment is saved with the change

**Status:** tentative. Recorded from the owner's choice on the crosswalk row plan-accept (better: the playbook; decision: blend), 2026-10-02.

**The owner's note (saved on the crosswalk page).** "Blend: merge to accept and close to reject stay as today (D25). Added (T7): when I close any intent PR, my last comment on it is saved as the change's reason (status.yaml abandoned_reason) instead of the fixed 'pull request N closed without a merge'; with no comment the fixed text stays. Incidents keep today's rule (my comment becomes the dismissal reason). Already recorded: T1's Product and Architect briefs and the manager's recommendation before gate (a). No settled decision reopened."

**Today.** Closing a pull request of gates (a) to (e) without a merge abandons the change (`sdlc-abandon.yml`, D25). Every closed change gets the same fixed text as its reason, "pull request N closed without a merge", in `status.yaml: abandoned_reason` on its branches. Only an incident change records the owner's words: closing any of its pull requests dismisses its finding, with the last comment by a repository member (owner, member or collaborator; bots and the automation identity skipped) as the reason, in a dismissal PR the owner merges (`plugin/detect/cli.py dismiss`). The article records a rejection as "the closing review" (p.11).

**Direction discussed (tentative).** Added; nothing replaced.
- **When the owner closes an intent PR**, the owner's last comment on it, if there is one, becomes `abandoned_reason`; with no comment the fixed text stays. Example: the intent PR for "Export as CSV" is closed with "Not needed, the PDF export covers it", and that sentence is what the change's record says months later.
- **The comment is optional**, so it costs the owner nothing when there is nothing to say.
- **Incidents keep today's rule:** the comment also stays the dismissal reason.
- **Accepting stays the merge** (D25), and T1's Product and Architect briefs with the manager's recommendation come before it.

**Crosswalk rows it touches:** plan-accept.

**Settled decisions it would reopen or amend:** none; D25 (closing abandons the change) is kept, and only what the record says changes.

**Open.**
- Whether the same applies when the owner closes a PR of gates (b) to (e), which abandons the change the same way.
- Which comments count: the owner's own (as T1 asks of approvals), or any repository member's, as the incident rule reads today.

## T8. The formatter follows the project's languages: per file type, the project's own commands on the changed file

**Status:** tentative. Recorded from the owner's choice on the crosswalk row build-hooks (better: the framework; decision: blend), 2026-10-03. The owner said in the session that they have projects in other languages (Rust, Node). Timing, the owner's choice: recorded now, built after the study.

**The owner's note (saved on the crosswalk page; corrected the same day at the owner's request, where it first said "every decision logged").** "Blend (T8), added and nothing replaced: the seven hooks stay as they are (protected paths, secrets check, formatter and linter on edit, plan sync, test-file lock, panel blindness, production gate), deterministic, every block logged (the panel-blindness hook logs only its blocks, the production gate nothing while inert), none asks (D6, D7 unchanged). Added (T8): the formatter hook follows the project's languages: per file type, the project's own format and lint commands in sdlc.yaml, run on the changed file only, failing open as today; ruff for Python stays the default; /sdlc-init proposes prettier/eslint for Node when package.json has them and rustfmt for Rust; only checks that are cheap per file go in the hook (clippy and other whole-project checks stay at the gate's lint, p.23); a file type with no command passes, so no default for HTML, CSS, Markdown, JSON or YAML (a project already on prettier may add them). Timing: recorded now, built after the study. Open in T8: full Rust support (detection of its targets, the test-file lock for tests inside source files, crates.io in the CI sandbox), revisited at test-bugfix; npm's .cmd shims on Windows. 'Back any skill whose policy has to hold' is decided with build-skills. Corrections approved: seven hooks, not six (panel_blind.py, 0.2.30, so 0.2.30 changes this row); relation adapted, not same (the formatter covers Python files only)."

**Today.** Seven hook scripts run in every session (`plugin/hooks/hooks.json`). Two log less than the others: the panel-blindness hook logs its blocks only, and the production gate logs nothing while inert (no production declared); every other hook logs each allow and block. The formatter and linter on edit act on Python files only: `ruff check --fix`, `ruff format`, then `ruff check` on the changed `.py` or `.pyi` file, failing open; other file types are ignored "in this version" (`plugin/hooks/format_on_edit.py`), and `sdlc.yaml: hooks.format_on_edit` only turns the hook on or off. `/sdlc-init` detects Python and Node projects (`plugin/init/detect.py`); a repository with no Python file, `pyproject.toml` or `setup.py` and no `package.json`, a Rust one for example, is "unknown" (one helper `.py` file makes it Python): its build, test and lint targets are placeholders the owner fills in before the gate lets phase (c) start. On a non-Python project a lint problem first shows when the verifier runs the lint target at the end of the session (`plugin/commands/sdlc-build.md` step 6, `plugin/agents/verifier.md`), and at the latest at the gate's lint target after the session, where a red target parks the change; a formatting problem shows only if that target checks formatting. The article runs the formatter and linter after file edits "so drift never accumulates", fast and scoped to the file that changed, with heavier checks at the commit or the PR (p.23).

**Direction discussed (tentative).** Added; nothing replaced.
- **Per file type, the project's own commands:** `sdlc.yaml` maps a file glob to the commands the hook runs on the changed file, for example `*.ts` to prettier then eslint `--fix`, `*.rs` to rustfmt. With no mapping, Python keeps ruff as today. The hook stays Python (D7) and calls the project's tools; it keeps failing open (a missing tool or a timeout never blocks).
- **Proposed at setup:** `/sdlc-init` proposes the commands from what it finds: prettier and eslint when `package.json` lists them, rustfmt for a `Cargo.toml` project. The owner keeps or edits them in the change-0000 PR; `sdlc.yaml` stays a guardrail file the owner changes.
- **Only what is cheap per file:** a check that compiles or scans the whole project (clippy for Rust, a full type check) stays at the gate's lint target, as p.23 puts heavier checks at the commit or the PR.
- **No default for HTML, CSS, Markdown, JSON or YAML:** a file type with no command passes, as every non-Python file does today. Unformatted files there cost diff noise, not a park, since such files rarely have a lint target at the gate. A project that already uses prettier may add them at no extra cost.

**Crosswalk rows it touches:** build-hooks; full Rust support also touches test-bugfix (the test-file lock) and setup-adopt (what `/sdlc-init` detects).

**Settled decisions it would reopen or amend:** none. D6 (the hooks load from the pinned plugin) and D7 (hooks are Python) stay.

**Open.**
- Full Rust support, beyond this hook: detecting its build, test and lint targets; the test-file lock, whose path globs cannot freeze unit tests written inside the source files (`#[cfg(test)]`), to revisit at test-bugfix; the crates.io hosts (`index.crates.io`, `static.crates.io`) are not among the CI sandbox's allowed domains and `Bash(cargo *)` is not among its allowed commands (`plugin/ci/settings.ci.json`), so the verifier's `cargo test` would be denied in CI; whether the project's setup command, which runs before the session and outside its sandbox, is enough is to verify.
- On Windows npm's tools are `.cmd` shims, which Claude Code's exec form cannot spawn without a shell (`docs/NOTES.md`); whether the hook starts them through the platform shell, as the gate's `run_command` does (`plugin/gate/checks.py`), is to verify.
- The exact shape of the `sdlc.yaml` setting, and whether it keeps the on/off switch `hooks.format_on_edit`.
- "Back any skill whose policy has to hold without exception" (p.23): whether a project declares its own hooks behind its policy skills is decided with build-skills.
