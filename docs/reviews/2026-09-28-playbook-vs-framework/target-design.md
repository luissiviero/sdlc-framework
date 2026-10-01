# The framework as the owner wants it

**Tentative until the study ends.** This page collects what the owner wants the framework to become, as the playbook-versus-framework study (`../2026-09-28-playbook-vs-framework.md`) goes row by row. Nothing here changes the current version: no plugin, template, `docs/DECISIONS.md` or `docs/ROADMAP.md` edit follows from an entry until the owner confirms it after the whole study. Then each confirmed entry becomes a proposal under `docs/proposals/` and a candidate row in `docs/ROADMAP.md` ("proposed"), in ROADMAP's own format.

Each entry: the owner's idea in the owner's words, the direction discussed so far, the crosswalk rows it touches, the settled decisions (Dn) it would reopen or amend, what is still open, and a status: **tentative**, **confirmed** or **dropped**.

| Id | Entry | Status | Recorded |
|---|---|---|---|
| T1 | AI roles that advise, and one manager that reviews for the owner | tentative | 2026-09-30 |
| T2 | The interview: how the manager and the roles question the owner | tentative | 2026-09-30 |
| T3 | The intent home: in the repository, written from anywhere, with examples | tentative | 2026-09-30 |
| T4 | Names: the phases named after what they produce, and the other names judged against the article | tentative | 2026-09-30 |

The crosswalk page (https://claude.ai/artifact/PFnRZ32pwTr4y422Gna2mz) shows each entry in a third column, "Target (tentative)", on the cards of the rows it touches; `crosswalk.json` carries the same condensed text in each row's `target` field, and the entries in `targets` (T1 to T3 so far; T4 is still to be added, see the review record's section 7).

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
- **A brief, never an approval.** On the record a role writes "security brief", not "security lead: approved", so the ledger never reads stronger than what a model can give.
- **Sources first.** A role is only as good as what it reads: without the owner's written policies a "security lead" is the generic model under another name. Writing those sources (security, data, coding standards, UX, definition of done) is the first step and needs no code; each policy skill has a line waiting for its owner source.
- **Where the roles help most** is where a check is lost with nothing in its place: gate (a), where the owner merges the owner's own intent after deterministic checks only, with no reviewing agent (`plugin/gate/checks.py`, `CHECKS_BY_PHASE["a"]`); the owner's own edits to CLAUDE.md, skills and `sdlc.yaml`; the skill sign-off; flagged concerns by kind at (b); higher-risk plans at (b); the release checklist on a declared production; triage at (f).
- **Each role gets an eval** that asks for its task without naming the role and checks it stays in its lane (article p.22, step 4).
- **Cost.** Every role is one more run per change. The owner weighs cost at 0, but the per-change dollar cap compares only the last session's cost today (issue #71).
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

**Approvals with the roles and the manager (tentative).** The owner's approval points stay where they are; what reaches the owner at each one changes. The roles write briefs, the manager turns them into one recommendation, the owner decides, and the act runs on the owner's signal (above).

| Gate | Role briefs | The manager brings the owner | The owner |
|---|---|---|---|
| (a) intent | Product (scope, success), Architect (feasibility) | accept, or the points to fix first, with the briefs linked | approves or sends corrections |
| (b) spec + plan | Product (does the spec solve the intent), Architect (the plan), Security & policy (flagged concerns) | two recommendations in the one PR: one for the spec, one for the plan | approves both or rejects one |
| (b), higher risk | the same, plus the Architect's full plan review | "needs your close look", with the reasons | approves separately, as the article's tech-lead step does (p.14, p.17) |
| (e) code | Code reviewer (today's REVIEW.md pass), Platform & release | merge or request changes, with the Important findings | approves; the merge runs on the owner's signal |
| (f) incident | Operations, Security & policy (scans) | fix now, schedule or dismiss | triages |

- Separate verdicts, not separate gates: a spec verdict and a plan verdict inside the one gate (b) PR bring back the article's split (p.14, p.17) without another wait, so D2 can stay.
- Stricter only for risk: a separate, closer approval only for a higher-risk plan, the article's own rule; today "non-routine" only lowers the iteration cap (D11).
- Gate (a) gains the most: today it has no reviewing agent.
- Settled decisions: D2 only if separate gates are wanted; D11 (what non-routine does); D18 (profiles); and the set above for acting in the owner's name.

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

**Crosswalk rows it touches:** x-roles, x-audit, setup-gates, plan-accept, design-concerns, design-go, build-plan-approve, build-config, build-skills, build-risk, deploy-approve, deploy-release, maintain-triage, maintain-scan, setup-merge.

**Settled decisions it would reopen or amend:**
- D4 (only the owner merges), D5 (the automation identity), D13 (gate (e) is the merge) and D24 (the owner's labels), for the manager acting in the owner's name;
- D21 (who sits on the panel) and D11 (whether a missing brief parks a change);
- no Dn states the one-owner premise today (`docs/OPERATING_MODEL.md` §2, build guide step 5); the roles would need a decision of their own.

**Open.**
- Which model each role runs on.
- Which documentation each role reads: the five policy skills each say "no owner source yet" (`plugin/skills/*/SKILL.md`).
- How many roles after merging.
- To verify: whether a GitHub ruleset can let a workflow merge on the owner's behalf, or whether that needs a dedicated GitHub App.
- The approval check must confirm the signal came from the owner, not just from a person: today `sdlc-runbook.yml` checks only that a person, not a bot or the workflow token, applied `sdlc:go` (`plugin/detect/cli.py` `_human_label_actor`); from the owner's setup-merge choice.
- The record of a delegated merge: the merge commit, the owner's approval signal and the manager's recommendation in `evidence/` (setup-merge); with the owner's *Exempt* bypass GitHub writes no bypass audit entry for the owner's own merges.
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
- A place in the intent for examples and references (T3 proposes a section), and whether the roles read them.

## T3. The intent home: in the repository, written from anywhere, with examples

**Status:** tentative. Recorded from the owner's choice on the crosswalk row setup-home (better: the framework; decision: blend).

**The owner's note (saved on the crosswalk page).** "Blend: ideas stay in changes/<id>-<slug>/, set up by /sdlc-init (current). I write intents from Claude Code or from claude.ai / phone. I accept by merging, after a Product role's brief (T1). Template: the plugin default, overridable per project (to verify); a Product role reviews it and I approve (T1). The intent gets an Examples/References section (T2)."

**Direction discussed (tentative).**
- **Where:** as today, `changes/<id>-<slug>/` in the project repository: `/sdlc-init` sets up `changes/`, `/sdlc-plan` creates each folder through `plugin/state` (D8, D9, D10 unchanged; D10 chose this over the article's own advice for a single product, an `intent/` folder in the product repo, p.10).
- **From anywhere:** an intent can also be written from claude.ai (on a computer or a phone), the article's route for contributors who are not engineers (p.10: claude.ai or Cowork, with a connector to the version-control system that lets Claude commit the file on their behalf).
- **Accepted** by the owner's merge after the gate (a) briefs of T1 (Product, Architect).
- **The template:** the plugin's `intent-template` by default, overridable per project; a Product role reviews a change to it and the owner approves (T1).
- **Examples and references:** a section in the intent where the owner puts examples of what is wanted; `mock/` stays the slot for screens (T2 asks whether the roles read them). The `intent-template` skill fixes "exactly this shape", so the section is a change to the plugin's template, not only to one intent.

**Crosswalk rows it touches:** setup-home, plan-idea, design-mock.

**Settled decisions it would reopen or amend:** none known, provided the claude.ai route opens the intent PR on `sdlc/<id>/a` like `/sdlc-plan` and never commits to `main`: a claude.ai GitHub connector acts as the owner's account, the ruleset's only bypass actor (D4), so a direct commit would skip gate (a) (D10). The Product brief inherits T1's D11 question. To check when the plan-idea row is decided.

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
