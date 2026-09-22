# Build guide — AI-Native SDLC framework repo

Source: Louis Claxton, "The AI-Native SDLC playbook", Anthropic blog, August 21 2026 (PDF and page-tagged text in `docs/reference/`). Page numbers are PDF pages. Machine-readable version: `docs/build_guide.json`. Version 3 — all 20 decisions in `docs/DECISIONS.md` are applied; steps 3, 7, 13, 19 and 26 amended on 2026-09-22 to match the platform facts of `docs/NOTES.md` and the build as it stands (no decision reopened).

## Objective

A framework repo that connects to any new project and drives it through (a) plan → (b) design → (c) build → (d) test → (e) deploy → (f) maintain. Phase (a) is interactive and ends with your approval; phases (b)–(f) run autonomously to completion; you intervene only at gates — approve, or ask for changes — and which gates are human is set per project profile (step 9a); you are never interrupted.

## Phase mapping

Your (a) plan = the article's Stage 1 (intent.md). Your (b) design = Stage 2 (spec.md) plus, by the decision in step 12, the implementation plan (plan.md). (c)–(f) = Stages 3–6. The article's 'plan mode' belongs to Stage 3 Build; step 12 explains where it lands in your framework.

## Phase column

'Phase' is the phase in which the concept OPERATES once the framework runs (a–f, or cross-cutting) — not the order in which you build it. Build order is the 'Build stage' (B0 → B5), which follows the article's adoption-order graph on p.8; merge-triggered CI arrives in B3 so the first autonomous phase already fires on its own.

## Gate protocol

Every phase ends with an artifact on a branch. Which gates are HUMAN depends on the project's profile (step 9a). Standard (default): human gates at (a) — merge of the intent PR; (b) — merge of the spec+plan PR; (e) — merge of the build PR (+ a release label only where a real production exists). Gates (c) and (d) are passed by the confidence gate (step 16) and, on failure, PARKED (label sdlc:needs-human, nobody notified). Full: (c) and (d) are also human gates — an approving review + label (sdlc:c-approved, sdlc:d-approved) on the single build PR the article keeps open through Build → Test → Review. Lite: only (a) and (e) are human; (b) is confidence-gated too. Gate (f): triage of each incident intent PR — merge (fix now) / label (schedule) / close with a reason (dismiss). At every human gate, 'ask for changes' = review comments on that PR, consumed by one fix command (step 8). Nothing ever pages you: finished or parked work waits in the review queue (step 27a).

## Importance scale

5 Critical — the framework cannot deliver the objective without it · 4 High — large effect on autonomy, safety or quality · 3 Medium — valuable, can follow later · 2 Low — nice to have for a solo developer · 1 Optional

## Source tags

ARTICLE = taken from the playbook as written · ADAPTED = article concept re-shaped for a solo developer / your objective · ADDED = not in the article; needed for the objective

## Build stages and steps


### B0 · Foundations — decisions and conventions every later step writes to


#### Step 1 — Write OPERATING_MODEL.md: one committed artifact per phase, the gate protocol, and the AI-native definition

- **Source tag:** ADAPTED  
- **Phase it belongs to:** cross-cutting  
- **Importance:** 5 · Critical — Your 'approve or ask for changes' at the profile's human gates (9a) is exactly the article's 'accepted artifact fires the next gate'; every other step hangs off this one. The definition ('combines the old control objectives with new enforcement', p.4) is also the brief for step 5: the controls stay, the way they are enforced changes.


**Concept from the article.** "The AI-native SDLC is a reimagined process that combines the old control objectives with new enforcement. Instead of a linear flow, the process becomes a loop, and AI is embedded at each point. The AI-native SDLC promotes automated handover and triggering of subsequent plays". The committed artifact is the thread: "Each stage ends by writing one to version control (including intent.md, spec.md, plan.md, the diff and its tests, the PR with its review findings, and the incident record) and the next stage begins by reading it." "A stage ends by committing an artifact with the commit initiating the next stage." "First, you prompt each step by hand with the end state being a loop in which each accepted artifact fires the next gate." "Humans remain accountable for every decision that requires judgment." "The chain of commits is also the audit trail: who asked for what, what the agent produced, and who approved it."


**Where in the article.**

- p.4–5 — Intro › 'What is an AI-native SDLC?'
- p.6 — Intro › paragraph after the Traditional-vs-AI-native table (artifact chain, audit trail, human accountability)
- p.7 — Plays › 'A stage ends by committing an artifact…' and the pull quote
- p.8 — Plays › 'First, you prompt each step by hand…'
- p.5 — Figure 'Traditional — the line / AI-native — the loop'
- p.50 — Closing thoughts › 'The loop keeps running. Human judgement stays above it.'

**Implementation notes.** First file in the framework repo. It states: the six phases; the artifact each phase commits — (a) intent.md · (b) spec.md + plan.md (decision in step 12) · (c) the diff and its tests · (d) test evidence in the PR check run · (e) the reviewed PR / release · (f) the incident record → a new intent.md [this per-phase mapping is ours; the article lists the six artifacts on p.6 without mapping them one-to-one to stages]; the gate protocol from the header of this guide (decided, decision 3) — human gates per profile (step 9a): in the default Standard profile you merge at (a), (b) and (e), while (c) and (d) are passed by the confidence gate and parked on failure; Full adds approving review + label at (c) and (d); Lite keeps only (a) and (e); triage action for (f); review comments = 'ask for changes' everywhere (step 8); nothing ever notifies you (step 27a). It also names the per-project phase adapters (step 9b) that say what 'deploy' and 'maintain' mean for that project. Use the p.50 line as its epigraph.


#### Step 2 — Scaffold the framework repo as a Claude Code plugin + a project template; fix the platform rules

- **Source tag:** ADAPTED  
- **Phase it belongs to:** cross-cutting  
- **Importance:** 5 · Critical — It is the physical form of 'a framework repo that can be connected to any new project'; without a distribution mechanism every project re-copies files by hand.


**Concept from the article.** The article distributes institutional knowledge as files that ship with the code or through a plugin: skills 'in the repo at .claude/skills/<name>/ so it ships with the code, or distribute it organization-wide through a plugin'; subagents 'defined in markdown files in .claude/agents/ … Check the definitions into git so the whole team shares them'; hooks 'in .claude/settings.json in git'; approved plugin marketplaces ('strictKnownMarketplaces'). Resources: 'Plugins and private marketplaces — how skills and hooks are distributed organization-wide'.


**Where in the article.**

- p.21 — Stage 3 Build › Skills › step 3
- p.25 — Stage 3 Build › Parallel sessions and subagents › step 4
- p.36 — Stage 5 Deploy › Hooks as approval gates › step 3
- p.38 — Worked example › 'disableSideloadFlags and strictKnownMarketplaces'
- p.51 — Resources › 'Plugins and private marketplaces'

**Implementation notes.** Two halves. (1) The plugin: commands (/sdlc-plan, /sdlc-design, /sdlc-build, /sdlc-test, /sdlc-deploy, /sdlc-maintain, /sdlc-fix, /sdlc-init), skills, agents, hooks — installed once, shared by all repos; nothing framework-specific goes into your global ~/.claude except the plugin installation itself, so unrelated repos are untouched. (2) The template copied into each project by /sdlc-init (step 21): CLAUDE.md skeleton, REVIEW.md, sdlc.yaml (profile + phase adapters, steps 9a/9b), changes/, bands.yaml, evals/, CI workflows including the daily-digest job (27a). Rule: process content lives in the plugin; project content (CLAUDE.md body, test commands, protected paths) lives in the target repo. Pin the plugin version (a tag or SHA) per project so 'the skill versions in force' (p.14) can be recorded in each spec. Decided (decisions 7 and 8) [ADDED]: you work on Windows and the article's examples are bash/jq/make (p.20, p.28, p.36–37); every hook, gate check, detection script and eval check is written in Python, with one make-like task runner that works on Windows and Linux; verify once how Claude Code on Windows invokes hook commands before writing the first hook. Distribution is plugin + template (copies drift; submodules put the framework inside each project's diff surface). [not in article: the plugin file structure — take it from the plugin docs on p.51.]


#### Step 3 — Execution substrate for unattended runs — decided: local for B1 only, hosted CI + API key from B3 (subscription auth if the docs permit it)

- **Source tag:** ADDED  
- **Phase it belongs to:** cross-cutting  
- **Importance:** 4 · High — Every autonomous phase in this guide is a non-interactive `claude -p` run. Hands-off means you must not be the one launching phases either, so merge-triggered CI arrives in B3 with the first autonomous phase; the manual rung of the ladder is only B1. Graded 4 rather than 5 because B1–B2 are fully buildable and testable before it is wired; from B3 on it is load-bearing.


**Concept from the article.** Not decided by the article for a solo developer. What it assumes: 'CI that can run Claude Code non-interactively, and an API key with budget for eval runs'; 'A CI platform with the claude-code-action installed, or any runner that can call claude -p; model access through the API, or Bedrock, Foundry, or Vertex'; 'Claude runs stateless, either as a non-interactive step on a CI runner or as an Agent SDK service in a sandboxed container'.


**Where in the article.**

- p.30 — Stage 4 Test › Continuous evals › Infrastructure
- p.40 — Stage 5 Deploy › CI/CD › Infrastructure
- p.43–44 — Stage 6 Maintain › Closing the loop › Infrastructure and step 4

**Implementation notes.** Decided (decision 1): (i) B1 commands run on your PC by hand — the article's first rung ('Run it by hand at first', p.13); (ii) from B3 every phase runs in hosted CI (GitHub Actions) under the automation identity of step 6, authenticated with an API key — the only option with zero local maintenance; the per-change cost is bounded by step 19's limits; (iii) authentication in CI, checked and applied on 2026-09-21 (NOTES §2): the Claude Code docs document CLAUDE_CODE_OAUTH_TOKEN, generated locally with claude setup-token, for Pro/Max/Team/Enterprise subscriptions (runs then use the subscription instead of API billing; the token is tied to the person who generated it and is not read in bare mode); every workflow takes both repository secrets and prefers the API key — ANTHROPIC_API_KEY → claude -p --bare, else CLAUDE_CODE_OAUTH_TOKEN → claude -p — and the owner starts on the token and moves to the key from /usage data. Local-only with a scheduler was rejected: an always-on machine is a system you would have to keep alive. The CI runner installs the pinned plugin (step 2).


#### Step 4 — Declare the repo as the source of truth per artifact; link any external tracker

- **Source tag:** ARTICLE  
- **Phase it belongs to:** cross-cutting  
- **Importance:** 3 · Medium — With no Jira/ServiceNow the answer is the repo, but writing it down prevents a later split between GitHub Issues, a notes vault and the repo.


**Concept from the article.** "for every artifact the process produces, name one system as the source of truth, with everything else holding a copy or a link to the original." Three configurations: the repo as the source of truth ('one of the cleanest configurations for engineering-led organizations, as all records live in one tool with one timestamp authority'); the legacy system as the source of truth ('Claude reads the record at the start of the session and writes the outcome back through an MCP connector'); linkage as the minimum bar ('All artifacts note the record ID and all legacy records contain the commit SHA').


**Where in the article.**

- p.18–19 — Stage 3 Build › SIDEBAR 'Legacy systems and the source of truth'
- p.10 — Stage 1 Plan › Infrastructure – cross-reference to the sidebar

**Implementation notes.** Decided (decision 9): state configuration 1 in OPERATING_MODEL.md. If you track work in GitHub Issues or a knowledge vault, apply linkage from day one: issue number in intent.md's header, commit SHA in the issue — the article calls linkage 'a good place to start … accepting that there are two sources of truth'.


#### Step 5 — Map the article's roles onto one person; rebuild separation of duties from agent identity and fresh-context reviewers

- **Source tag:** ADAPTED  
- **Phase it belongs to:** cross-cutting  
- **Importance:** 4 · High — Almost every human gate in the article is a different person approving (intent and spec share the product owner). For you all roles collapse into one, so the control objective ('old control objectives with new enforcement', p.4) must be met by agent identity, fresh-context reviewers and branch rules — or the autonomy silently removes the checks.


**Concept from the article.** The article assigns a role per gate — originator, product owner, technical lead, engineer, platform engineer, tech lead, code owner, release manager, service owner / on-call, security lead — and derives control from that separation: "Separation of duties is preserved, because the agent that wrote the code has no way to approve it"; "Each non-interactive run acts under the agent's own identity, so the pipeline log separates what the agent did from what the engineer who triggered it did"; "A human team mate always makes this call"; higher-risk work goes to a tech lead ('consulting a technical lead for anything the organization classes as higher risk').


**Where in the article.**

- p.9–11 — Stage 1 Plan – originator / product owner
- p.14 — Stage 2 Design › step 6 – product owner, technical lead
- p.17 — Stage 3 Build › plan mode › Governance – engineer vs tech lead / architect
- p.34–35 — Stage 5 Deploy › PR review › Governance – separation of duties
- p.41 — Stage 5 Deploy › CI/CD › Governance – agent identity
- p.44 — Stage 6 Maintain › step 6 – service owner / on-call engineer

**Implementation notes.** Three rules for the framework: (1) writer ≠ judge — the agent that produced an artifact never judges it; a different agent in a fresh context reviews it (verifier p.27, adversarial reviewer p.42, review pass p.32) and only you approve; (2) non-interactive phases run under an automation identity distinct from your account (step 6), so the log separates the agent's actions from your approvals; (3) the article's technical-lead consultation for higher-risk work (p.14, p.17) becomes a written risk list (touches auth, data migrations, money movement, production config → the change is parked at its next gate with sdlc:needs-human and waits for your review — one rule, stated identically in steps 9a and 16; never a notification). Monthly tuning rituals the article assigns to a tech lead (p.34) become agent-initiated PRs you merge or ignore.


#### Step 6 — Branch rules: the agent has no route to main; only you can merge; automation identity = the CI workflow token

- **Source tag:** ADAPTED  
- **Phase it belongs to:** cross-cutting  
- **Importance:** 5 · Critical — It is the hard boundary that makes every gate real — intent, spec and build PRs alike: whatever an autonomous run does, nothing lands without your merge.


**Concept from the article.** "Anything the agent writes arrives as a PR through branch protection, and the agent has no route to push to main." "Branch protection turns anything the agent writes into a PR, with no direct path to main." "Approval comes from a human through branch protection, informed by the findings." "Findings do not approve or block a PR on their own, and branch protection still requires approval from a code owner." 'Branch protection policies that require a code owner's approval are also worthwhile.'


**Where in the article.**

- p.33 — Stage 5 Deploy › PR review › Infrastructure and step 3
- p.35 — PR review › Governance considerations
- p.40–41 — CI/CD › step 2 and Governance – 'no direct path to main'

**Implementation notes.** Decided (decisions 4 and 5) [ADAPTED — the article assumes a second person as code owner]: use a branch ruleset that restricts pushes and merges to main to your own account and gives the automation identity write access to branches only. Then 'merged by you' is the approval for every PR regardless of author — including the intent PR you author yourself in phase (a), which a 'require a reviewer' rule would block; add a require-one-review rule only if a second reviewer ever exists. Automation identity: the CI platform's built-in workflow token (GitHub's github-actions[bot]) — zero setup, no secrets to rotate; its documented limit — events caused by GITHUB_TOKEN (pushes, PRs, labels it sets) do not start new workflow runs, except workflow_dispatch and repository_dispatch — is designed around in step 30: your own merges and labels fire workflows normally, and every automated transition dispatches the next phase explicitly. Move to a GitHub App only if that limit bites; a machine account was rejected (a second login to protect for no benefit). Never give the automation identity bypass rights.


#### Step 7 — Permissions and sandbox for unattended sessions: deny secrets and raw network, allow the inner loop, disable bypass, protect the guardrails themselves

- **Source tag:** ADAPTED  
- **Phase it belongs to:** cross-cutting  
- **Importance:** 5 · Critical — In your framework the party being controlled is the agent, not an engineer. Every deterministic control in this guide (protected paths, test-file lock, plan-sync hook, production gate, deny list) lives in files inside the repo the agent edits; without the 'cannot switch them off' layer an unattended session can edit the hook that blocks it, and every hook degrades to an advisory control — the failure the Skills governance warns about (p.22).


**Concept from the article.** Worked example 'Managed settings for a regulated enterprise': permissions.deny (Read(.env*), Read(./secrets/**), WebFetch, Bash(curl *), Bash(wget *)); permissions.allow (Bash(git *), make build/test/lint); "disableBypassPermissionsMode": "disable"; "allowManagedPermissionRulesOnly": true; sandbox {enabled, failIfUnavailable, allowUnsandboxedCommands: false, network.allowedDomains, credentials denying ~/.ssh, ~/.aws/credentials and GITHUB_TOKEN}; allowManagedHooksOnly; disableSideloadFlags; allowManagedMcpServersOnly; strictKnownMarketplaces; requiredMinimumVersion. "disableBypassPermissionsMode plus allowManagedPermissionRulesOnly means no engineer, project file or command-line flag can widen the rules." "allowManagedHooksOnly means the approval gates from this play are the only hooks that run; nothing local can add to or replace them." 'Consider the above a starting point to tailor, rather than a recommendation to copy. Every deny trades against capability'. Build infrastructure: 'permission settings tuned so sessions are not waiting on approval prompts for commands the organization considers safe'.


**Where in the article.**

- p.37–38 — Stage 5 Deploy › WORKED EXAMPLE 'Managed settings for a regulated enterprise' and 'What each line buys, in control terms'
- p.36 — Hooks as approval gates › step 3 – 'non-negotiable hooks go in managed settings … where individual engineers cannot switch them off'
- p.24–25 — Stage 3 Build › Parallel sessions › Infrastructure – tuned permission settings
- p.40 — CI/CD › step 3 – sandboxed jobs, short-lived scoped tokens, no production credentials
- p.44 — Closing the loop › Governance – 'permissions and managed settings denying production access'
- p.50 — Resources – Settings reference, Permissions
- p.51 — Resources – Sandboxing, Managed MCP

**Implementation notes.** Ship in the template's .claude/settings.json: deny reads of .env* and secrets, deny WebFetch/curl/wget, allow the git/build/test/lint loop, enable the sandbox where the OS supports it. Never make unattended runs work by enabling bypass-permissions mode — the article's model is allow-list + deny-list + sandbox with bypass disabled. Decided (decision 6) — all three layers. Self-protection [from p.36/38]: (i) the protected-path hook of step 15 must cover .claude/**, CLAUDE.md, REVIEW.md and the hook scripts; (ii) put a managed settings file on your machine — docs/owner-machine/managed-settings.json, documented and installed by the owner, never by the framework (the article deploys it 'via MDM or the admin console', p.37 — MDM just places a file, so a single machine can hold one) — carrying disableBypassPermissionsMode, allowManagedPermissionRulesOnly and allowManagedHooksOnly; because those two keys ignore project permission rules and block non-managed plugin hooks (NOTES §4), the file must also carry the permission rules itself and force-enable sdlc@sdlc-framework through enabledPlugins; it is a guard against the agent, not the owner, and cloud sessions never read it — there the repo's .claude/settings.json and the plugin it declares are the layers; (iii) in CI, load hooks and permissions from the pinned plugin checkout, never from the PR branch; (iv) add 'no diff touches .claude/** or CLAUDE.md unless the change is the framework itself' to REVIEW.md and to the gate checks of step 16. Skip the enterprise-only keys (marketplaces, version floor, managed MCP) until you share the framework with others.


#### Step 8 — One change-request mechanism for every gate: review comments → /sdlc-fix

- **Source tag:** ADAPTED  
- **Phase it belongs to:** cross-cutting  
- **Importance:** 5 · Critical — Your objective has two human verbs — approve, or ask for changes. Approve is a merge/label (step 1); 'ask for changes' needs one uniform input or every phase invents its own.


**Concept from the article.** The article defines the mechanism for code PRs: "When a reviewer or the author tags @claude on a review comment, Claude addresses the comment and pushes the fix. The PR thread records both the request and the change." "let Claude babysit the PR to merge. Teams wrap the loop in a custom slash command that sweeps the unresolved review comments and failing checks on the PR, addresses them and pushes the fixes, until the PR is green and waiting only on code owner approval." For the early artifacts it only counts revisions in git ('the number of changes made to the intent.md that are made after the first spec.md commit'; 'spec.md commits dated after the first plan.md commit').


**Where in the article.**

- p.33–34 — Stage 5 Deploy › PR review › step 4
- p.12 — Stage 1 Plan › lagging indicator
- p.15 — Stage 2 Design › lagging indicator

**Implementation notes.** Rule: at any gate, your change request is a PR review comment on that phase's PR. Implementation: one command, /sdlc-fix (built in step 26), reads the unresolved comments and failing checks, re-runs the phase's command with the comments as constraints, and pushes to the same branch — for intent, spec+plan and build PRs alike. The article describes the sweep-until-green loop only in the PR review play (the CI/CD play, p.40, lists @claude comment handling as a write step); applying it to the spec/intent PRs is our generalisation. The git history then yields the article's rework metrics for free.


#### Step 9 — Orchestrator conventions: change folder, state file, branch and label names, idempotent phase commands

- **Source tag:** ADDED  
- **Phase it belongs to:** cross-cutting  
- **Importance:** 5 · Critical — The article assumes an engineer or a CI trigger starts each stage; your framework needs something that knows which phase each change is in, what runs next, and how to resume after your comments. Every later step writes to these conventions, so they come first.


**Concept from the article.** Not in the article. Nearest statements: 'A stage ends by committing an artifact with the commit initiating the next stage'; 'Claude runs stateless, either as a non-interactive step on a CI runner or as an Agent SDK service in a sandboxed container … a loop can begin and end without anyone starting it'; the adoption ladder 'Run it by hand at first, then codify it as an organization-level slash command. From there make the acceptance of intent.md in the intent home the trigger'; 'The engineer's job shifts to orchestrating, and eventually, to building and monitoring loops.'


**Where in the article.**

- p.7 — Plays › stage-ending commits trigger the next stage
- p.13 — Stage 2 Design › step 2 – by hand → slash command → trigger
- p.44 — Stage 6 › step 4 – stateless, non-interactive runs
- p.24 — Stage 3 Build › Parallel sessions › AI-native column

**Implementation notes.** Decided (decisions 3 and 10) — keep state in git, not in a database: one folder per change, changes/<id>-<slug>/ (our generalisation of the article's intent/ folder, p.10) holding intent.md, spec.md, plan.md, evidence/ and status.yaml (phase, profile override, change type feature/fix, gate result, parked reason, iteration count); branches sdlc/<id>/<phase>; PR labels: sdlc:<phase>-ready (set whenever a run stops at a human gate and waits for you), sdlc:<phase>-approved (Full profile only) and sdlc:needs-human (parked). The orchestrator reads the project's profile (step 9a) to decide, at each gate, whether it waits for a human label/merge or calls the confidence gate (step 16) and continues. Each phase command is idempotent and reads its inputs from the folder, so a re-run after your comments is the same command. Merge-triggered workflows (step 30) must read status.yaml and run only when the previous gate is recorded as passed — not on a file path alone, since intent.md edits after spec.md are expected and counted as rework (p.12); because events caused by the automation identity do not start workflow runs (step 6), automated transitions (Standard c→d→e, Lite b→c) end by dispatching the next phase's workflow explicitly (repository_dispatch / workflow_dispatch) with the change id; human transitions (your merge, your label) fire normally. Commands must also run locally without CI so B1 can be exercised by hand.


#### Step 9a — Project and change profiles: how many human gates a change gets (Standard · Full · Lite)

- **Source tag:** ADAPTED  
- **Phase it belongs to:** cross-cutting  
- **Importance:** 5 · Critical — Your objective taken literally is five approvals per change; for a small project that is more ceremony than the change, and it is the opposite of hands-off. The article's own end state runs gates as automated checks with humans only on escalation, and reserves human review for critical code — so the number of human gates should be a property of the project, not a constant. This is the largest consequence of the two constraints you made explicit (decision 18).


**Concept from the article.** The article's headless end state: "Stage 6: Maintenance runs headless, with an independent confidence gate between stages, a deterministic check or an adversarial reviewing agent, deciding whether the previous stage's output continues or is escalated to a human." Its Deploy row: 'Layers of agentic review with human review reserved for regulated and critical code.' Its condition for unattended work: 'auto-accept becomes the default for routine work: a tight spec.md, a small blast radius, and code the tests already cover.' And its principle for where human attention goes: "Human attention concentrates at the gates, reviewing what the agent flagged rather than starting each stage from scratch."


**Where in the article.**

- p.42 — Stage 6 Maintain › 'Maintenance and closing the loop' – confidence gate
- p.6 — Table row Deploy
- p.17 — Stage 3 Build › Auto mode – routine work
- p.8 — Plays › 'Human attention concentrates at the gates…'

**Implementation notes.** Decided (decision 18). Three profiles, set by /sdlc-init in the project's sdlc.yaml and overridable per change in status.yaml. Standard (default): human gates at (a), (b: spec+plan) and (e: merge); (c) and (d) are passed by the confidence gate (step 16) and parked on failure — reviewing the build PR at (e) is reviewing (c) and (d) after the fact, because its description carries plan conformance, evidence and review findings (step 27a). Full: all five human gates — projects with a live production or money at stake; (c) and (d) are approved with an approving review + label on the open build PR. Lite: only (a) and (e) — scripts, experiments, docs; (b) is confidence-gated too: spec.md + plan.md are committed on the change branch without a PR to main, the gate-16 verdict is recorded in status.yaml, and the design job dispatches the build job explicitly (step 30); intent (a) and the reviewed diff (e) remain the two merges. A risk-list hit (step 5) parks the change at its next gate with sdlc:needs-human, whatever the profile. [ADAPTED — the article has no profiles; it has the p.42 gate and the p.6 'reserved for critical code' rule.]


#### Step 9b — Phase adapters: what 'deploy' and 'maintain' mean for each project type

- **Source tag:** ADDED  
- **Phase it belongs to:** e. deploy · f. maintain  
- **Importance:** 4 · High — 'Any sort of project' includes research code, data pipelines and libraries that have no service to deploy and no 5xx rate to watch. Skipping (e) and (f) for them would lose the loop; the article itself shows the maintain machinery works on process metrics, so only the deploy action and the watched metric are project-specific (decision 19).


**Concept from the article.** Not in the article, which assumes a service with a pipeline and production traffic. What transfers: 'Tier the autonomy by environment. In development, the agent deploys freely. In production, the agent prepares the release and the release manager authorizes it'; the closing-the-loop examples include a process metric — 'When PR cycle time trips a drift rule, the agent writes a report for engineering leadership, which shows the harness works for process metrics as well as production ones.'


**Where in the article.**

- p.40 — Stage 5 Deploy › CI/CD › step 5
- p.45 — Stage 6 Maintain › Closing the loop › Examples

**Implementation notes.** Decided (decision 19). Each project declares in sdlc.yaml (written by /sdlc-init): deploy = the action that makes a merged change live for that project (publish the package, schedule the job, regenerate the report, promote a strategy to paper trading), plus whether a real production exists (which turns on the release label of step 32); maintain = the metric the project actually emits (job success rate, data freshness, backtest-vs-live drift, CI test failure rate) and its data source, plugged into the same bands.yaml machinery (step 37), plus the runbooks the 3σ tier may call and their authorization class (step 37). The phase commands (step 24) read the adapter instead of hard-coding a service deploy. Two separate frameworks were rejected: double the maintenance. [ADDED]


### B1 · The five 'clay' plays, as manual commands (article p.8: start anywhere)


#### Step 10 — intent.md template, encoded as a skill (with change ID and entry route)

- **Source tag:** ARTICLE  
- **Phase it belongs to:** a. plan  
- **Importance:** 4 · High — intent.md is the entry artifact of the loop and the re-entry artifact from Maintain (p.44, p.47 require 'the Stage 1 format'). A fixed shape keeps the design pass and the incident route consistent; the article files the template under infrastructure, not as a gate.


**Concept from the article.** "Ask Claude to write the result as intent.md using the organization's template, which can be encoded as a skill set up by a technical team member and signed off by a lead. This can cover the problem, proposed outcome, affected users and systems, constraints, and open questions." Example: header 'Author … Status: draft', sections Problem / Proposed outcome / Affected users and systems / Constraints / Open questions. Infrastructure: 'an agreed intent.md template'. Intent 'can enter through different routes. A person has an idea, a ticket is filed, or an incident is surfaced via an alert'. Incident intents cover 'the anomaly and its evidence, a proposed outcome, the affected systems and any open questions'.


**Where in the article.**

- p.10 — Stage 1 Plan › Infrastructure
- p.11 — Stage 1 Plan › step 3 and the intent.md example block after step 5
- p.9 — Stage 1 Plan › 'Capture as intent.md' – entry routes; AI-native column
- p.44 — Stage 6 Maintain › step 5 – incident intent contents

**Implementation notes.** A plugin skill (skills/intent-template) whose frontmatter says when it triggers (any request to write or update an intent) and whose body is the section list: the article's five sections + Author/Status, plus a change ID, the entry route (idea / ticket / incident) and, for incidents, an Evidence section. Same rules as every other skill (step 20): test that it triggers, change it via a PR to the plugin.


#### Step 11 — /sdlc-plan: brainstorm → intent.md → your correction → commit; gate (a) = merge of the intent PR

- **Source tag:** ARTICLE  
- **Phase it belongs to:** a. plan  
- **Importance:** 5 · Critical — The only interactive phase in your objective and the first approval point; its output quality decides how far the autonomous phases get, and its merge is the trigger for phase (b).


**Concept from the article.** Steps 1–5: "The originator describes the problem to Claude in their own words … No formal language is required." "Brainstorm until the idea is concrete. Claude asks the questions an analyst would ask: scope, users, constraints, and what success looks like." "The originator corrects anything Claude misunderstood." "Commit intent.md to the shared home. Author and timestamp join the record". Governance: "The product owner approves, and the accept or reject decision that sends the intent into Stage 2: Design is recorded as the merge or the closing review." 'An accepted intent.md triggers the requirements and design pass'. Infrastructure: 'a shared, version-controlled home for intent that the product owner watches. For a single product the simplest home is an intent/ folder in the product repo.'


**Where in the article.**

- p.10–11 — Stage 1 Plan › How to execute it, steps 1–5
- p.11 — Stage 1 Plan › Governance considerations
- p.10 — Stage 1 Plan › Infrastructure – intent home
- p.7 — Plays › 'An accepted intent.md triggers the requirements and design pass'

**Implementation notes.** Plugin command: (1) analyst-question brainstorm; (2) write changes/<id>-<slug>/intent.md via the template skill; (3) show you the draft to correct; (4) commit on sdlc/<id>/a and open the PR. For you the article's 'originator corrects' (p.11) and 'product owner reviews and corrects … before it is committed' (p.9) are one act — keep the merge as the recorded approval. Incident-generated intents (step 37) arrive as ready PRs: your review before merge is the correction step; /sdlc-plan is invoked on them only if you ask for changes.


#### Step 12 — plan.md: template, interrogation prompt, and the decision to produce it at the end of phase (b) in a read-only run

- **Source tag:** ADAPTED  
- **Phase it belongs to:** b. design (produced) · c. build (kept in sync)  
- **Importance:** 5 · Critical — The article's plan acceptance is a human act inside Build, which conflicts with 'phase (c) runs autonomously'. Where plan.md is approved decides whether phase (c) can be unattended.


**Concept from the article.** "Engineers start Claude Code sessions in plan mode, give Claude the approved spec.md … and let it interview them, iterating on the plan until the engineer is happy with it." Steps: start in plan mode; give intent.md and spec.md and ask for a plan 'that names the files that change, the order of the work, and the tests that prove it'; interrogate it — 'what the change could break, which step is most risky, and what other options Claude chose not to do'; iterate 'until an engineer who has never seen the conversation could implement the change from the plan alone'; commit as plan.md; accept and implement ('often a single pass'); 'When implementation departs from the plan, update plan.md in the same commit. Consider using a hook to enforce synchronization between the two.' Governance: "Design review happens before any code is generated, when changing course is still a matter of editing a document. Plan mode enforces this itself, since Claude cannot edit files until the engineer accepts the plan. The plan and its revisions are logged along with who accepted it. Routine changes are approved by the engineer, and anything the organization classes as higher risk goes to a tech lead or architect." Stage tagline: 'Nothing is implemented without an accepted plan.'


**Where in the article.**

- p.15 — Stage 3 Build › tagline and 'Claude Code plan mode as the default starting point'
- p.16 — Plan mode › steps 1–7
- p.16–17 — Plan mode › 'What it looks like (plan.md)' – Files that change / Order of work / Risks / Proof
- p.17 — Plan mode › Governance considerations
- p.14 — Stage 2 Design › step 6 – 'accepting the spec is what starts the plan mode play'

**Implementation notes.** Decided (decision 2) and propagated everywhere: plan.md is produced at the end of phase (b) and approved with spec.md at gate (b) — one gate, at the cheapest point to change course (p.17). The article's enforcement property ('cannot edit files until the engineer accepts the plan') is rebuilt for headless runs as a two-run rule: the planning run has read-only tools (Read/Grep/Glob) and commits plan.md; the implementation run (phase c) has edit/shell tools and starts only after gate (b). The interrogation questions (p.16 step 3) become a fixed prompt whose answers land in plan.md's Risks and an added 'Options not taken' section; plan.md keeps the article's four sections. In phase (c) the pre-commit check of step 15 enforces 'plan.md updated in the same commit'. The Lite profile (step 9a) already replaces your approval at (b) with the confidence gate; for Standard and Full, plan.md stays at gate (b).


#### Step 13 — CLAUDE.md skeleton (Commands with healthy output, Conventions, Architecture, Things Claude gets wrong, Verifying your work) and the 'mistake twice' rule

- **Source tag:** ARTICLE  
- **Phase it belongs to:** cross-cutting  
- **Importance:** 5 · Critical — A tier-1 'clay' play read at the start of every session of every phase; three plays depend on it in the graph (skills, subagents, evals) and PR review by the text prerequisite (p.32).


**Concept from the article.** "CLAUDE.md gives Claude the context a new joiner would need, covering conventions, commands, architecture, and the mistakes the team sees most often." 'a file the agent reads at the start of every session'. Steps: run /init; cut down ('Keep the build, test and lint commands, the conventions that matter, and the things Claude keeps getting wrong'); check in at the repo root; "When Claude makes a mistake twice, the correction goes into CLAUDE.md"; "Keep it under a page, because Claude reads all of it at the start of a session". Test play: 'In the CLAUDE.md's Commands section, list each command with an example of a healthy output'; verification block 'Run all three before reporting any task complete, and paste the output. If a test fails, fix the code, not the test.' Review 'also flags when a change has made CLAUDE.md outdated'. Governance: 'code owners approve those changes in PR review'.


**Where in the article.**

- p.19–20 — Stage 3 Build › The CLAUDE.md › steps 1–5 and example 'Payments service'
- p.20 — The CLAUDE.md › Governance and leading indicator
- p.27–28 — Stage 4 Test › steps 2 and 6, 'What it looks like (CLAUDE.md verification block)'
- p.34 — Stage 5 Deploy › PR review › step 5
- p.6 — Table row Build – 'institutional knowledge is maintained as versioned machine-readable CLAUDE.md files and skills'

**Implementation notes.** The plugin ships the skeleton (four example sections + the p.28 verification block); /sdlc-init fills the project-specific parts. Wire the working rule into the review loop (step 26): the second occurrence of a finding produces a proposed CLAUDE.md line in changes/<id>/evidence/claude-md-proposals.md — CLAUDE.md itself is a protected path for runs (step 7), so the proposal is applied by you in a separate commit when you approve the gate. Relief valve for 'under a page': policy that must apply consistently moves out to a skill (rule of thumb, p.21). Agent-written CLAUDE.md edits still ride in a PR you merge (p.20 governance). Note: the graph draws CLAUDE.md → Skills as a solid arrow, but the text says 'a skill does not depend on it' (p.21) — so the intent template (step 10) can exist before any project CLAUDE.md.


#### Step 14 — Feedback loop: one-command build/test/lint, quantifiable target, visual check for UI, verification is part of 'done'

- **Source tag:** ARTICLE  
- **Phase it belongs to:** c. build (inner loop) · d. test (final evidence run)  
- **Importance:** 5 · Critical — Without a self-check the autonomous phases produce work nobody has verified until you look — the article's point where 'that person becomes the bottleneck' (p.27). A tier-1 play that subagents and evals depend on.


**Concept from the article.** "Always give Claude a way to verify its own work, whether tests, a build, or a screenshot diff. A session checks its own work and fixes its own mistakes before an engineer sees them." 'The feedback loop runs through the whole task as many times as the work.' Steps: wrap checks in 'a single target such as "make test" or "npm test" that exits non-zero on failure'; 'State a target and make it quantifiable so Claude can check the work without asking you'; for UI, 'Give Claude a browser or screenshot tool, give it the mock, and let it iterate. Implement, screenshot, compare, and adjust. Two or three rounds is normal'; 'Make verification part of "done." … Run the tests before reporting a task complete, and show the output.' Infrastructure: 'A test suite and a build that run locally with one command each … either a browser tool or a screenshot utility wired in via MCP.'


**Where in the article.**

- p.26–27 — Stage 4 Test › 'Give Claude a feedback loop' › intro, What changes, Infrastructure
- p.27–28 — Feedback loop › steps 1–3, 5–6
- p.6 — Table row Test – 'Continuous evals woven through implementation'

**Implementation notes.** The framework refuses to enter phase (c) unless the project exposes one-command build/test/lint targets (detected or created by /sdlc-init, in the cross-platform runtime of step 2). The quantifiable target is written into plan.md's Proof section (p.17) so phase (d) checks it mechanically. For UI projects wire a browser/screenshot tool via MCP [the article names none]. The play sits in Test but the loop runs throughout (c); phase (d) is the separate fresh-context, full-suite, evidence-producing run (step 24).


#### Step 15 — Build-time guardrail hooks: block protected paths (incl. the guardrails themselves), format/lint after edits, keep secrets out, plan.md sync

- **Source tag:** ARTICLE  
- **Phase it belongs to:** c. build  
- **Importance:** 5 · Critical — The only deterministic control while the agent works unattended; auto-accept (step 18) is conditioned on it, so it must be in place before the first unattended run.


**Concept from the article.** "A skill is an advisory control while a hook is the deterministic layer behind it. Most of Claude's actions are file edits and shell commands during implementation, so the build phase is where hooks can end up firing most often." Build-phase hooks can: 'Block edits to protected paths such as generated classes or a frozen package'; 'Run the formatter and linter after file edits so drift never accumulates'; 'Keep credentials out of the diff'; 'Back any skill whose policy has to hold without exception'. 'build-phase hooks should be fast and scoped to the file that changed. Heavier checks such as the full test suite belong at the commit or the PR.' 'A hook that asks a human for approval belongs with the gates in Stage 5: Deploy, because an approval prompt during the build puts a person back on the critical path'. Hooks 'can block edits to migrations and infra without a change ticket during Stage 3: Build'. 'The skill makes violations rare and the hook makes them close to impossible.'


**Where in the article.**

- p.23 — Stage 3 Build › 'Hooks as build-time guardrails'
- p.22 — Skills › Governance – skill vs hook
- p.35 — Stage 5 Deploy › Hooks as approval gates – 'hooks are not deploy-specific'
- p.16 — Plan mode › step 7 – hook to keep plan.md in sync
- p.36 — Hooks as approval gates › step 3 – team hooks in .claude/settings.json; example PreToolUse hook

**Implementation notes.** Ship in the plugin: (1) a pre-tool-use hook denying edits to protected paths — the project's list plus, always, .claude/**, CLAUDE.md, REVIEW.md and the hook scripts (self-protection, step 7); (2) formatter/linter on the changed file after edits; (3) a secrets-pattern check on edits; (4) plan.md synchronization as a git pre-commit hook (fails when tracked source changes and changes/<id>/plan.md does not) plus the same rule in REVIEW.md's compliance pass — the article suggests the hook but not its mechanism; (5) the test-file lock is defined in step 25 and only referenced here. No 'ask' hooks in this phase. The article shows only the PreToolUse event (p.36); other event names come from the hooks reference (p.51).


### B2 · Autonomy kit — what a phase needs to run unattended safely


#### Step 16 — Independent confidence gate inside every autonomous phase: deterministic checks + adversarial reviewer → continue or park

- **Source tag:** ADAPTED  
- **Phase it belongs to:** cross-cutting  
- **Importance:** 5 · Critical — This sentence is the article's answer to 'run each step autonomously until its conclusion': inside a phase, continuation is decided by a deterministic check or an adversarial agent, and a failure is parked for your next review — while the profile's human gates (step 9a) stay human.


**Concept from the article.** "Stage 6: Maintenance runs headless, with an independent confidence gate between stages, a deterministic check or an adversarial reviewing agent, deciding whether the previous stage's output continues or is escalated to a human." The verifier runs 'a fresh context window once the session believes the work is done. This way the verdict is not colored by the assumptions that produced the code'; review severity counts are published 'as a machine-readable tally'; 'The pass-rate threshold is enforced as a merge check'.


**Where in the article.**

- p.42 — Stage 6 Maintain › 'Maintenance and closing the loop' – second paragraph
- p.27 — Stage 4 Test › feedback loop vs verifier subagent
- p.33 — PR review › step 3 – machine-readable severity tally
- p.31 — Continuous evals › Governance – pass-rate threshold as merge check

**Implementation notes.** One gate function used by every phase: (1) deterministic checks — artifact exists and matches its template; tests/lint green; evidence present; no Important review findings; plan.md ↔ diff consistency; no diff touching .claude/** or CLAUDE.md unless the change is the framework itself; (2) an adversarial reviewer agent (step 17) in a fresh context returning continue / escalate with reasons. Decided (decision 11): escalate means PARK, never page — the run stops, finishes every artifact it can, writes a 'what I need from you' section into the PR description, sets status.yaml and the sdlc:needs-human label, and notifies nobody; you find it in the review queue (step 27a). A risk-list hit (step 5) and a limit hit (step 19) park the same way; the routine/non-routine classification of step 18 only tightens this gate. Under the Standard profile (step 9a) this gate is what passes (c) and (d) without you; the article scopes the gate to the headless Maintain stage and uses it instead of the human between stages — we apply it inside every phase and keep you at the profile's human gates.


#### Step 17 — Subagents in .claude/agents/: verifier, code simplifier, researcher, plus the adversarial reviewer

- **Source tag:** ARTICLE  
- **Phase it belongs to:** c. build (verifier, simplifier, researcher) · cross-cutting (adversarial reviewer)  
- **Importance:** 4 · High — Fresh-context verification is how the article gets a verdict 'not colored by the assumptions that produced the code' — your substitute for a second person inside an autonomous phase (step 5).


**Concept from the article.** "A subagent runs inside a single session as a scoped helper with its own context window and tool limits and suits jobs that recur in multiple tasks such as verifying the app runs as expected." "Turn repeated jobs into subagents, as defined in markdown files in .claude/agents/, each with a name, a description of when to use it, and the tools it may touch. Examples include a code simplifier that strips needless complexity after the main agent finishes, a verifier that runs the app and checks behavior, a researcher that explores the codebase and reports back without flooding the main context." Example verifier.md: tools Bash, Read; 'Exercise the changed behavior and the two nearest neighboring flows. Report what you ran, what you saw, and any behavior that does not match plan.md. Do not fix anything; report only.'


**Where in the article.**

- p.24 — Stage 3 Build › Parallel sessions and subagents › subagent definition
- p.25–26 — Parallel sessions › step 4 and 'What it looks like (.claude/agents/verifier.md)'
- p.26–27 — Stage 4 Test › 'The feedback loop should not be confused with a verifier subagent'
- p.42 — Stage 6 Maintain › 'an adversarial reviewing agent'

**Implementation notes.** The plugin ships four agent files: verifier (copy p.25–26), code-simplifier, researcher, and adversarial-reviewer (used by the gate of step 16 between every pair of phases). Keep 'report only, do not fix' for all reviewers so writer ≠ judge holds. Prerequisites per the graph: CLAUDE.md (solid) and the feedback loop (dotted — the text says it 'also helps here', p.24).


#### Step 18 — Auto-accept for the implementation run, conditioned on the guardrails; routine vs non-routine sets gate strictness

- **Source tag:** ARTICLE  
- **Phase it belongs to:** c. build  
- **Importance:** 5 · Critical — Autonomy inside a phase is literally this setting plus its preconditions; the article ties it explicitly to 'running the SDLC autonomously'.


**Concept from the article.** "Claude Code can also run in auto mode, where the engineer approves the plan and, once happy and iterated upon, Claude applies each change without a per-edit prompt. As the guardrails from the later plays mature (a tuned CLAUDE.md, skills that encode policy, hooks that block unsafe actions, and a test suite Claude can run), auto-accept becomes the default for routine work: a tight spec.md, a small blast radius, and code the tests already cover." "Auto-accept mode further enables parallelism … and is fundamental to running the SDLC autonomously and closing the loop". 'permissions.allow pre-approves the safe inner loop so the deny list doesn't turn into prompt fatigue.'


**Where in the article.**

- p.17–18 — Stage 3 Build › 'Claude Code on auto mode'
- p.38 — Worked example › 'What each line buys' – permissions.allow / disableBypassPermissionsMode
- p.23 — Hooks as build-time guardrails – no approval prompts during the build

**Implementation notes.** Enable auto-accept for the implementation run only when its preconditions exist: CLAUDE.md (13), skills (20), blocking hooks (15), one-command tests (14). Use the allow-list of step 7, never bypass-permissions mode. Have the adversarial reviewer classify each plan as routine or not (tight spec, small blast radius, tests cover it); in a new project almost nothing is routine, so the classification changes the strictness of the gate (mandatory adversarial review, smaller iteration cap) and never interrupts you (decision 11). The article never says whether auto mode is a flag or a permission configuration; take it from the settings docs (p.38, p.50).


#### Step 19 — Run limits for unattended phases: iteration cap, wall-clock timeout, budget, pause flag — all park through the gate

- **Source tag:** ADDED  
- **Phase it belongs to:** cross-cutting  
- **Importance:** 4 · High — A loop that fixes its own failures can also loop forever; the article's gates bound what the agent may do, not how long or how much it may try.


**Concept from the article.** Not a play in the article. Related fragments: 'an API key with budget for eval runs'; 'Extra Usage turned on with a spend limit set … the spend limit should match the size and number of repositories'; 'Two or three rounds is normal' for the visual loop; 'add sessions only while review is keeping up'.


**Where in the article.**

- p.30 — Continuous evals › Infrastructure
- p.46–47 — Recurring scans › Infrastructure
- p.28 — Feedback loop › step 5
- p.25 — Parallel sessions › step 3

**Implementation notes.** Add to the gate of step 16: max fix iterations per phase (3, matching 'two or three rounds'), a wall-clock timeout per run, a per-change usage budget where the substrate exposes one (step 3), and a repo-level pause flag checked before every run. Use the CLI's own bounds for non-interactive runs as the outer limits: --max-turns and --max-budget-usd (print mode; sub-agent spend counts toward the cap; both from sdlc.yaml: gate, passed by plugin/ci/run_phase.py — Claude Code CLI reference, not the article). On any limit → park with the partial evidence attached (step 16); never stop silently, never notify. [ADDED]


#### Step 20 — Policy skills (coding standards, security, UX, data conventions, definition of done) and the skill update rule

- **Source tag:** ARTICLE  
- **Phase it belongs to:** cross-cutting (b. design, c. build, e. deploy)  
- **Importance:** 4 · High — The autonomous design pass has no human analyst to catch policy conflicts; skills are what replace that person (a solid prerequisite of Requirements & design in the graph). They are read again in Build and by the review passes.


**Concept from the article.** Design prerequisite: "Write an intent.md file, with brand, security, compliance, and UX policies written as skills." Rule of thumb: "write a skill for institutional knowledge that must be applied consistently; don't write a skill for components that belong in CLAUDE.md or a prompt." A skill is "a folder containing a SKILL.md whose frontmatter says when it triggers and whose body says what to do." Steps: pick 'one piece of knowledge that is enforced inconsistently today'; write it 'from the policy owner's source of truth'; 'Test that the skill triggers'; "When the policy changes, change the skill and have the policy owner sign off the change." "Engineers pick up the new version automatically in their next session." Infrastructure: 'One policy with a named owner and a written source of truth.' Governance: "A skill is a control, though an advisory one … A policy that must always hold needs something deterministic behind the skill, such as a hook that blocks the action or a review pass that re-checks the policy at the PR."


**Where in the article.**

- p.12–13 — Stage 2 Design › intro and Prerequisites
- p.21–22 — Stage 3 Build › Skills as institutional knowledge › rule of thumb, Infrastructure, steps 1–6, SKILL.md example 'secure-api-review'
- p.22 — Skills › Governance
- p.32 — PR review › Prerequisites – 'skills if the review passes enforce written policies'
- p.6 — Table row Design – 'guided by standards encoded as skills, versioned in git'

**Implementation notes.** Ship generic skills in the plugin — coding standards, security baseline, UX/UI conventions (if front-end), data/storage conventions, definition of done — and let each project override in .claude/skills/. Each skill names the written source it was derived from (your own standards doc). The update rule is how the framework evolves: a policy change is a PR to the plugin's skill, reviewed like code, and every project picks it up next session. The example skill on p.22 ends by running a deterministic script and including its output — a useful pattern for policy skills. Deterministic backing for must-hold policies: a hook (step 15) or the review pass (step 26).


#### Step 21 — /sdlc-init: connect the framework to a new project in one command

- **Source tag:** ADDED  
- **Phase it belongs to:** cross-cutting  
- **Importance:** 4 · High — 'Connect to any new project' becomes a one-command act instead of a manual checklist per repo.


**Concept from the article.** Not in the article as such. Nearest elements: "Run /init in the repo. Claude generates a starting CLAUDE.md from what it finds." and feedback-loop step 1, wrapping checks into one command.


**Where in the article.**

- p.19 — Stage 3 Build › The CLAUDE.md › step 1 (/init)
- p.27 — Stage 4 Test › Feedback loop › step 1

**Implementation notes.** Copies the template (2), asks for the project's profile (9a) and its deploy/maintain adapters (9b) and writes sdlc.yaml, runs /init and cuts CLAUDE.md down (13), detects or creates the one-command build/test/lint targets (14), installs hooks and settings (15, 7), creates changes/, REVIEW.md, evals/, bands.yaml, the CI workflows (30) and the daily-digest job (27a), records the pinned plugin version, and commits everything as the project's first PR so the framework's own installation goes through the same gate. Idempotent, so re-running upgrades an existing project. [ADDED]


### B3 · First autonomous phases, their gates, and the merge-triggered plumbing


#### Step 22 — /sdlc-design: the spec.md pass with skills loaded and flagged concerns, followed by the read-only plan.md run

- **Source tag:** ARTICLE  
- **Phase it belongs to:** b. design  
- **Importance:** 5 · Critical — The first fully autonomous phase in your objective; the article gives its exact automation ladder and prompt.


**Concept from the article.** "The product owner's prompt points at the intent.md, names the constraints, and demands flagged concerns. Run it by hand at first, then codify it as an organization-level slash command. From there make the acceptance of intent.md in the intent home the trigger, with a non-interactive job that fires on the merge, run the pass with the organization's skills loaded, and commit spec.md as a pull request (the CI/CD play in Stage 5: Deploy covers the plumbing). From that point the product owner's first involvement is the review." Example prompt: 'Read the attached intent.md and produce a requirements and design spec for integrating it into our existing codebase. Apply the skills available to you so the plan conforms to our brand guidelines, security policies and UX standards. Document the spec fully as spec.md, ready to hand to the engineering team. Describe clearly any areas of concern, especially where you cannot satisfy contradicting policies.'


**Where in the article.**

- p.13 — Stage 2 Design › steps 1–2 (the by-hand → slash command → merge-triggered ladder)
- p.14 — Stage 2 Design › 'What it looks like (the prompt)'
- p.12 — Stage 2 Design › 'Requirements and design collapse into one session'

**Implementation notes.** Follow the ladder literally: run the p.14 prompt by hand on two or three real intents; turn it into the command; then, still in B3, wire the merge-triggered job (step 30) guarded by status.yaml (step 9), so that once the design pass exists you never launch it by hand. The command ends with the read-only planning run of step 12 that appends plan.md, then opens one PR with spec.md + plan.md (Standard/Full) — or, in Lite, commits both on the change branch and hands over to the build job (steps 9a, 30). 'Flagged concerns' is a mandatory section — it is what you read first at the gate. Record the prompt and the pinned plugin version in spec.md's header ('the spec, the prompt that produced it, and the skill versions in force are all logged in version control', p.14). Prerequisites in the graph: Capture intent and Skills.


#### Step 23 — Gate (b): review spec.md + plan.md against the intent; concerns first; merge = go to build

- **Source tag:** ARTICLE  
- **Phase it belongs to:** b. design  
- **Importance:** 5 · Critical — Second human gate (Standard and Full; automated in Lite) and, with plan.md folded in (step 12), the article's strongest cheap checkpoint — the plan-mode governance calls it the point when 'changing course is still a matter of editing a document' (p.17).


**Concept from the article.** "The same product owner reviews the spec against the idea. Does the spec solve the stated problem, and are the open questions from intent.md answered or carried forward?" "Work through the flagged concerns first as they are the points an analyst would have escalated. The product owner resolves each one with its policy owner before engineering sees the spec." "Commit spec.md alongside intent.md. The file pair records what was asked for and what was decided." "The product owner decides whether the spec and intent progress to build, consulting a technical lead for anything the organization classes as higher risk. A human team mate always makes this call, and accepting the spec is what starts the plan mode play in Stage 3: Build." 'an approved spec.md triggers plan mode'.


**Where in the article.**

- p.14 — Stage 2 Design › steps 3–6 and Governance considerations
- p.7 — Plays › 'an approved spec.md triggers plan mode'
- p.17 — Plan mode › Governance – 'when changing course is still a matter of editing a document'

**Implementation notes.** The PR description carries the checklist: problem solved? open questions answered or carried forward? every flagged concern closed? plan.md implementable by someone who never saw the conversation (p.16 step 4)? Concern resolution for one person: either edit the 'Flagged concerns' section closing each item with a decision, or leave a review comment consumed by /sdlc-fix; the deterministic gate check is 'no open concern'. Your merge is recorded as the decision; the merge is the trigger for phase (c). Human in the Standard and Full profiles; in Lite this gate is passed by the confidence gate (step 9a).


#### Step 24 — Compose the phase runbooks: what /sdlc-build, /sdlc-test, /sdlc-deploy and /sdlc-maintain actually run

- **Source tag:** ADAPTED  
- **Phase it belongs to:** cross-cutting  
- **Importance:** 5 · Critical — The autonomy semantics — inputs, order, artifact, exit condition — live in the composition; without it phase (d) collapses into phase (c)'s inner loop and 'run until conclusion' has no defined conclusion.


**Concept from the article.** The article gives the components, not a per-phase composition. Build: 'Accept the plan and let Claude implement. With a solid plan, the implementation is often a single pass.' Test: 'Run the tests, run the build, take the screenshot. Claude iterates until the check passes, so what reaches the engineer has already passed it'; the verifier 'running a fresh context window once the session believes the work is done'; 'Heavier checks such as the full test suite belong at the commit or the PR.' Deploy: 'The agent does everything up to the production gate and nothing past it.' Maintain: 'Claude diagnoses, acts only through gated routes, and writes what it finds as intent.md'.


**Where in the article.**

- p.16 — Plan mode › step 6
- p.27 — Feedback loop › AI-native column; verifier in a fresh context
- p.23 — Hooks as build-time guardrails – heavy checks at commit or PR
- p.32 — Deploy stage tagline
- p.42 — Maintain › AI-native column

**Implementation notes.** (c) build: read spec+plan → implementation run under auto-accept with hooks → code simplifier → verifier → open/update the build PR with the generated description (step 27a) → gate 16; in Standard/Lite the orchestrator continues straight into (d), in Full it waits for your label (step 27). (d) test: fresh context; full suite, build, lint; UI screenshot loop against the mock; verifier report; write changes/<id>/evidence/ and the check run (step 28) → gate 16 → continue (Standard/Lite) or wait for your label (Full). (e) deploy: review passes (26) → fix loop until green → changelog/release notes → release prepared per the project's deploy adapter (step 9b) → gate 16 → stop and wait for your merge (step 32). (f) maintain: standing loop whose unit of work is one finding on the adapter's metric (steps 9b, 37); its gate is the triage of step 39. Each command is idempotent and re-runnable after your comments (step 8). [ADAPTED]


#### Step 25 — Failing-test-first for fix-type changes, and the hook that locks test files during the fix

- **Source tag:** ARTICLE  
- **Phase it belongs to:** c. build (fix-type changes) · e. deploy (review fallback)  
- **Importance:** 4 · High — The one control that keeps an unattended agent from 'passing' by weakening the test; the incident route of phase (f) makes fix-type runs frequent. The article files it under Test, but the sequence (test first, then implement) puts it at the start of the build of a fix.


**Concept from the article.** "For bug fixes, write the failing test first. Ask Claude to reproduce the bug as a test, run it, and confirm it fails for the reason you expect. Commit that test. Only then ask Claude to make it pass without editing the test, with the test-file hook from the final step enforcing the restriction. A test that existed before the fix, and that the agent couldn't rewrite, is proof the bug is gone." "the loop itself needs protecting, because an agent fixing code must not be able to weaken the check on that code. A hook that blocks edits to test files during a fix task does this. The alternative is to check the diff in review and reject any change that touches a test."


**Where in the article.**

- p.28 — Stage 4 Test › steps 4 and 7
- p.29 — Feedback loop › Governance – 'What is enforced'
- p.35 — Hooks as approval gates – 'stop the agent editing test files during a fix task in Stage 4: Test'

**Implementation notes.** Add a change type (feature / fix) to status.yaml. For fix: the planning run of step 12 specifies the reproducing test in plan.md's Proof; the build run writes and commits it first, then the pre-tool-use hook denies edits under the test directories for the rest of (c) and (d). Add the article's fallback to REVIEW.md: reject any change that touches a test in a fix task.


#### Step 26 — REVIEW.md, the review passes (bugs · security · compliance vs spec.md/plan.md), and /sdlc-fix (address comments, babysit to green, feed CLAUDE.md)

- **Source tag:** ARTICLE  
- **Phase it belongs to:** e. deploy (review passes) · cross-cutting (/sdlc-fix)  
- **Importance:** 5 · Critical — The article's replacement for line-by-line human review, the place the diff is checked against spec.md and plan.md at policy level, and — through /sdlc-fix — the engine behind your 'ask for changes' at every gate (step 8).


**Concept from the article.** "Claude both gives and receives reviews. It reviews incoming PRs against the organization's policies and addresses review comments on its own PRs." "The tech lead writes the review policy as REVIEW.md at the repo root, divided into the passes the organization cares about: bugs and logical errors; security and vulnerabilities; compliance against the spec (spec.md …), the implementation plan (plan.md …) and design principles. REVIEW.md also defines what counts as Important as opposed to a Nit, and what to skip." Example: 'Reserve Important for findings that would break behavior, leak data or breach a policy'; 'Report at most five nits per review'; under 'Do not report': 'Generated files under src/gen/ and anything CI already enforces.' Fix loop: '@claude on a review comment … Claude addresses the comment and pushes the fix'; 'babysit the PR to merge … until the PR is green and waiting only on code owner approval'. "When a review flags a mistake for the second time, the correction goes into CLAUDE.md as part of that review, and because review reads CLAUDE.md the mistake is caught from the next PR onwards." 'Once a month the tech lead tunes the setup by rating findings … and by capping Nit volume'. Infrastructure: managed Code Review (research preview) or the claude-code-action in your own CI.


**Where in the article.**

- p.32 — Stage 5 Deploy › 'AI in the PR review loop' › intro, What changes, Prerequisites
- p.33 — PR review › Infrastructure, steps 1–4
- p.34 — PR review › steps 4–6 and 'What it looks like (REVIEW.md)'
- p.6 — Table row Deploy – 'Layers of agentic review with human review reserved for regulated and critical code'

**Implementation notes.** Template REVIEW.md copies the p.34 structure plus the rules added by this guide (no edits to .claude/**; no test edits in fix tasks; plan.md in sync). Decided (decision 12): the review pass is a `claude -p` job in CI (step 30) with REVIEW.md, in a fresh context (writer ≠ judge), publishing findings as a check run with a machine-readable severity tally the gate (16) reads. A reviewer subagent inside the writing session is a stopgap only while runs are still local (B1); the managed Code Review service only if your plan offers it. /sdlc-fix is the single change-request handler for all phases' PRs; the second occurrence of a finding writes a proposed CLAUDE.md line to evidence/claude-md-proposals.md, which you apply in a separate commit (step 13); the monthly tuning becomes a scheduled agent PR you merge or ignore. The article never shows the slash command's contents.


#### Step 27 — Gate (c): automated in the Standard profile; approving review + label on the build PR in the Full profile

- **Source tag:** ADAPTED  
- **Phase it belongs to:** c. build  
- **Importance:** 3 · Medium — The article has no human gate between Build and Test (the diff is approved at PR review); your objective's gate here is kept only for the Full profile. In Standard it is the confidence gate, and whatever it would have shown you is in the build PR you review at (e). Its approval is a label, not a merge, because the same PR continues into (d) and (e).


**Concept from the article.** "The shift is now away from the user watching the agent make the edits and reviewing actions, towards the review of artifacts after longer autonomous sessions." Metrics: 'Share of changes that merge from the first implementation pass'; 'Rework cycles per change … and how often the merged diff still matches the committed plan.md.' Artifact: 'the diff and its tests'.


**Where in the article.**

- p.18 — Stage 3 Build › Auto mode – review of artifacts after longer autonomous sessions
- p.17 — Plan mode › How to measure it
- p.6 — Intro › artifact list (paragraph after the table)

**Implementation notes.** Decided (decisions 3 and 18). Standard / Lite: the confidence gate (step 16) passes or parks; no human action. Full: the generated PR description (step 27a) shows what is new at this gate — links to intent/spec/plan, a plan-vs-diff conformance note, the verifier report, first-pass test output — and you approve with an approving review + sdlc:c-approved; the orchestrator (9) then starts (d). 'Ask for changes' = review comments → /sdlc-fix on the same branch. [ADAPTED]


#### Step 27a — Review queue and daily digest: how finished or parked work reaches you (nothing pushes)

- **Source tag:** ADAPTED  
- **Phase it belongs to:** cross-cutting  
- **Importance:** 4 · High — Hands-off review only works if the review itself is cheap and comes on your cadence: a generated summary at the top of every PR is the article's 'what the agent flagged', and a daily digest replaces notifications with one predictable touchpoint (decision 20).


**Concept from the article.** "Human attention concentrates at the gates, reviewing what the agent flagged rather than starting each stage from scratch." "All PRs get an identical set of review passes, with findings ranked by severity. Human attention moves up a level, to whether the change does what the plan intended and whether the risk is acceptable." 'The code owner reviewing the PR, who can concentrate on intent and risk because the mechanical evidence is already attached.'


**Where in the article.**

- p.8 — Plays › 'Human attention concentrates at the gates…'
- p.32 — Stage 5 Deploy › PR review › AI-native column
- p.29 — Stage 4 Test › Feedback loop › Governance – 'Who approves'

**Implementation notes.** Decided (decision 20; placed in B3 because the first generated PRs appear there, though step 16 already relies on it). Every PR the framework opens or updates starts with a ≤5-bullet summary: what changed and why (linked intent), evidence status (tests/build/lint, screenshots), review findings by severity, plan conformance, and — if parked — 'what I need from you'. The review queue is the PR list filtered by the sdlc:*-ready and sdlc:needs-human labels of step 9 (needs-human first). A scheduled job posts a daily digest (one issue or PR comment) listing the queue with those bullets; it is the only recurring output, and it is pull, not push — no notifications are ever sent. The same PR description carries the two counters of step 42. [ADAPTED — the article's summary is the PR's ranked findings; the digest and the no-notification rule are ours.]


#### Step 28 — Gate (d): evidence from the toolchain in changes/<id>/evidence/ and the PR check run — automated in Standard, human label in Full

- **Source tag:** ADAPTED  
- **Phase it belongs to:** d. test  
- **Importance:** 3 · Medium — Defines what phase (d) must leave behind — pasted toolchain output and the check run, never the agent's claim that tests pass. In the article this evidence is consumed at PR review; in the Standard profile it is consumed by the confidence gate and by you at (e); the Full profile keeps a human label here.


**Concept from the article.** Governance table: What is enforced — 'Verification before a task is reported done, and the block on the agent editing test files during a fix, both implemented as hooks where the organization wants them guaranteed.' What the evidence is — "The literal output of "make test," the build log, or the screenshot diff that Claude ran and pasted, so the evidence comes from the toolchain." Where it is logged — 'In the session transcript, which the OpenTelemetry export forwards to the organization's observability stack, and in the PR's check run'. Who approves — 'The code owner reviewing the PR, who can concentrate on intent and risk because the mechanical evidence is already attached.'


**Where in the article.**

- p.28–29 — Stage 4 Test › Feedback loop › Governance considerations (four-row table)
- p.29 — Feedback loop › How to measure it

**Implementation notes.** Decided (decisions 3 and 18). Phase (d) writes evidence/ (test log, build log, lint output, screenshots, verifier report) and posts a summary check run. 'Evidence present and green' is a deterministic precondition of gate 16 for entering (e). Standard / Lite: no human action. Full: approve with an approving review + sdlc:d-approved. What is new versus gate (c): the full-suite, fresh-context run and its evidence. [ADAPTED]


#### Step 30 — Headless plumbing: claude -p in merge-triggered workflows per phase transition, sandboxed, under the automation identity

- **Source tag:** ARTICLE  
- **Phase it belongs to:** cross-cutting  
- **Importance:** 4 · High — This is what turns the manual commands of B1–B2 (and the first B3 runs) into 'merge fires the next phase'; the design pass (p.13) and the maintenance trigger (p.44) both point here. The prerequisites rule — gates before acceleration — is why it comes after the review pass (26) and the guardrails (7, 15); decision 1 moves it into B3 so that you never launch a phase by hand once the design pass exists. The article's other prerequisite, hooks as approval gates (29), is deferred to B4 because until a project's adapter (9b) names a deploy target there is no production gate for the hook to guard; the B3 workflows hold no production credentials.


**Concept from the article.** "Run Claude Code non-interactively inside the CI/CD pipeline, sandbox the execution so long-running agents run safely". Steps: 'The platform engineer starts with read-only judgment steps. Use claude -p in a pipeline job to triage a failed build, summarize a flaky test, or draft the changelog.' 'Add write steps behind the existing gates … Anything the agent writes arrives as a PR through branch protection'. 'Execution is sandboxed. Agent jobs run in containers under a network policy with short-lived scoped tokens, and hold no production credentials by default.' Prerequisites: 'Claude in the PR review loop and hooks as approval gates, because the gates must exist before automation accelerates anything through them.' Design step 2: 'a non-interactive job that fires on the merge … (the CI/CD play in Stage 5: Deploy covers the plumbing)'. Example pipeline step 'Triage failed build'.


**Where in the article.**

- p.39 — Stage 5 Deploy › 'CI/CD integration and deployment' › summary, Prerequisites
- p.40 — CI/CD › Infrastructure and steps 1–3
- p.41 — CI/CD › 'What it looks like (pipeline step)' and Governance
- p.13 — Stage 2 Design › step 2 – 'the CI/CD play … covers the plumbing'
- p.44 — Stage 6 › step 4 – 'the CI/CD play covers the deployment and model-access options'

**Implementation notes.** One workflow per transition — intent merged → design job; spec+plan merged (Standard/Full) or dispatched by the design job after a passing gate-16 verdict (Lite) → build job; then, per the profile (9a), either straight on to test and review jobs (Standard/Lite) or waiting for sdlc:c-approved / sdlc:d-approved (Full) — each: checks status.yaml (9), installs the pinned plugin (2), runs `claude -p` with the allow-list and sandbox of step 7 under the automation identity (6), with short-lived tokens and no production credentials. Triggers: your merges and labels fire the next workflow normally; automated transitions cannot rely on the bot token's own pushes, PRs or labels (GitHub documents that those do not start workflow runs), so each phase job ends by dispatching the next one (repository_dispatch / workflow_dispatch with the change id) — the two event types that rule exempts (step 6, step 9). Start with the copy-paste-ready read-only step from p.41 to prove the substrate decided in step 3. Everything the jobs write arrives as a PR.


### B4 · Deploy — release gate, deployment tooling, gate (e)


#### Step 29 — Hooks as approval gates: the production-gate hook, blocks that explain themselves, what counts as approval

- **Source tag:** ARTICLE  
- **Phase it belongs to:** e. deploy  
- **Importance:** 4 · High — The technical form of 'The agent does everything up to the production gate and nothing past it' (p.32) — for the cases where Claude itself can invoke a deployment: MCP deploy tools (step 31) and the 3σ runbook route (step 37). If your deploys run from a merge-triggered pipeline, the real gate is the merge plus the pipeline's environment protection, and this hook never fires.


**Concept from the article.** "A hook can also ask, pausing the action until a specific person approves, which is what release gating needs." Steps: leadership 'lists the human approval gates that must survive, such as change management sign-off, release authorization, and edits to protected paths'; 'expresses each gate as a hook, a script that runs before Claude acts that can allow, ask, or block'; 'A block should explain itself, so when a hook stops an action the reason and the route to approval appear in Claude's output.' Example: PreToolUse hook on Bash → production-gate.sh blocks commands containing 'deploy' and 'production' unless RELEASE_APPROVAL is set ('exit 2 blocks the action; the message goes to Claude'). Governance: "Hooks are the approval gates. The gate condition is enforced every time, for everyone. Allow and block decisions are logged with a timestamp. The gate also defines what counts as approval, whether that's an approved change ticket or the release manager's sign-off."


**Where in the article.**

- p.35 — Stage 5 Deploy › 'Hooks as approval gates' › intro
- p.36 — Hooks as approval gates › Infrastructure, steps 1–4, settings.json example
- p.36–37 — 'And the gate itself (.claude/hooks/production-gate.sh)' and Governance
- p.32 — Deploy stage tagline – 'The agent does everything up to the production gate and nothing past it.'

**Implementation notes.** Copy the p.36–37 example into the plugin and parameterise the command pattern per project. Define in OPERATING_MODEL.md what counts as approval (a release label or signed tag set by you) and have the hook read that rather than a raw environment variable. Article gaps to design yourself: it says hooks can 'ask' but the example only allows/blocks, and it never shows how RELEASE_APPROVAL is set. Blocks must print the reason and the route to approval.


#### Step 31 — Deployment tooling: deploy/status/rollback as MCP tools scoped per environment; tiered autonomy; rehearsed rollback

- **Source tag:** ARTICLE  
- **Phase it belongs to:** e. deploy  
- **Importance:** 3 · Medium — Only applies once a project has a real deploy target; when it does, the rehearsed rollback is a hard prerequisite of the 3σ tier in phase (f).


**Concept from the article.** 'Expose deployment through MCP. Deploy, status, and rollback become tools, scoped per environment, so the agent's deployment powers are an allowlist rather than a shell script with credentials.' 'Tier the autonomy by environment. In development, the agent deploys freely. In production, the agent prepares the release and the release manager authorizes it, and a hook enforces the production gate. Staging sits somewhere in the middle.' 'Rollback should be the most rehearsed path in the pipeline, a single command that the agent can run and that is exercised regularly in staging. The closing the loop play (Stage 6: Maintenance) calls this rollback when a control band is breached, so it has to be proven in advance.' Governance: 'Per-environment permission tiers set how much the agent may do on the way to the gate.'


**Where in the article.**

- p.40 — CI/CD › steps 4–6
- p.41 — CI/CD › Governance and metrics (DORA)
- p.39 — CI/CD › AI-native column

**Implementation notes.** Expose deploy/status/rollback as MCP tools only where the project's deploy adapter (step 9b) names a real deployment; keep them environment-scoped and let the production-gate hook (29) guard the production one. Rehearse rollback in staging before enabling the 3σ tier of step 37. DORA measures come from the CI system 'already' (p.41).


#### Step 32 — Gate (e): autonomous part ends at 'PR green, findings ranked, release prepared'; your merge (+ release label) triggers the deploy pipeline

- **Source tag:** ADAPTED  
- **Phase it belongs to:** e. deploy  
- **Importance:** 4 · High — The last human gate of every profile (third in Standard, second in Lite, fifth in Full); the article tells you what to judge (intent and risk) because everything mechanical is already attached. Deploy is the one phase where the agent's work continues after your approval — the deploy itself — which the article forbids before authorization.


**Concept from the article.** "Human attention moves up a level, to whether the change does what the plan intended and whether the risk is acceptable." 'All PRs get an identical set of review passes, with findings ranked by severity.' 'a merged PR triggers the pipeline'. 'In production, the agent prepares the release and the release manager authorizes it'. Post-deploy: 'When the post-deploy 5xx rate breaches 3σ with a deployment in the window, the agent triggers the existing rollback pipeline.'


**Where in the article.**

- p.32 — Stage 5 Deploy › PR review › AI-native column
- p.7 — Plays › 'a merged PR triggers the pipeline'
- p.40 — CI/CD › step 5
- p.45 — Closing the loop › Examples

**Implementation notes.** Decided (decision 13). Sequence: (e) runs review passes and the fix loop until green, drafts release notes, prepares the release → stops. Approve = merge; only when the project's adapter (9b) declares a real production does a release label, read by the production-gate hook, become a second act (decision 13). The merge-triggered pipeline deploys; the post-deploy band of step 37 is the safety net, with the rehearsed rollback (31) as its action. For a project without a production environment, merge is the whole gate. This is the review you do 'once the work is done': the PR opens with the ≤5-bullet summary of step 27a, and in the Standard profile it is the first time you look at the change since approving spec+plan. [ADAPTED]


### B5 · Closing the loop and later additions


#### Step 33 — Parallel sessions in git worktrees for file-disjoint tasks (optional, later)

- **Source tag:** ARTICLE  
- **Phase it belongs to:** c. build  
- **Importance:** 3 · Medium — A throughput multiplier whose ceiling is review capacity — and you review only at phase end, so the gain is bounded. The article's flow is interactive; unattended merging of parallel branches is our extension.


**Concept from the article.** "The engineer splits the work into tasks that touch different files, using the plan from the plan mode play (Stage 3: Build) to see where the work is independent. Tasks that share files run in a single session, one after another." 'Each parallel task gets its own worktree, for example claude --worktree feature-auth in one terminal and claude --worktree fix-rate-limit in another.' "Two or three sessions is a sensible starting point. The practical ceiling is how many streams one person can review properly, so add sessions only while review is keeping up." Governance: 'controls have to come from configuration in the repo. Hooks and permission settings there apply to all sessions'.


**Where in the article.**

- p.24 — Stage 3 Build › Parallel sessions and subagents › play summary
- p.25 — Parallel sessions › steps 1–3
- p.26 — Parallel sessions › Governance and metrics
- p.18 — Auto mode – 'enables parallelism … when used with worktrees'

**Implementation notes.** Decided (decision 17): build later, if ever — only when review keeps up. If built: /sdlc-build reads plan.md's 'Files that change' and spawns one worktree per proven file-disjoint task; at most two or three; on any merge conflict, escalate through the gate (16) rather than resolve autonomously. Every worktree inherits the repo's hooks and permissions.


#### Step 34 — Optional: Claude Design mock for front-end work, stored next to the spec as the visual target

- **Source tag:** ARTICLE  
- **Phase it belongs to:** b. design  
- **Importance:** 2 · Low — Only for projects with a UI; then the mock is the quantifiable target of the visual feedback loop (14).


**Concept from the article.** "Front-end work is the clearest example. Once the intent.md is accepted, the product owner mocks the design up in Claude Design (beta) from the intent.md, iterates on the mock, and then exports it to Claude Code to build." plan.md Proof example: 'screenshot matches the approved mock'.


**Where in the article.**

- p.12–13 — Stage 2 Design › intro
- p.17 — Stage 3 Build › plan.md example › Proof
- p.28 — Stage 4 Test › step 5 – 'give it the mock, and let it iterate'

**Implementation notes.** Store the exported mock in changes/<id>/mock/ so (c) and (d) compare screenshots against it. The article does not say how the export relates to spec.md or in what format.


#### Step 35 — Continuous evals: a per-project evals/ suite (fed by incidents) plus a framework-level suite, run on config changes and nightly

- **Source tag:** ARTICLE  
- **Phase it belongs to:** cross-cutting (runs on configuration changes and nightly, outside a change's a→f path)  
- **Importance:** 3 · Medium — Regression-tests the configuration that steers the agent — essential once the plugin serves several repos and incidents accumulate, but the '20 to 50 real tasks' only exist after months of use. Start it in B5, not on day one.


**Concept from the article.** "Evals are the AI-native equivalent of stage-gate QA. In practice that means a suite that runs whenever the agent's configuration changes. When a new model is swapped in or a prompt is rewritten, the eval suite says whether the agent still does the work to the same standard." 'The evals should be seen as a live suite.' Steps: collect '20 to 50 real tasks from recent work with its expected/accepted outcome'; write each as prompt + checks; run 'non-interactively in CI on a schedule and on any change to CLAUDE.md, skills or hooks'; 'Gate configuration changes on the results'; 'Each production incident gets an eval, written by the team that owned the incident, and stays in the suite as a regression test.' Example workflow in the product repo: on pull_request paths ['CLAUDE.md', '.claude/**'] + nightly cron; `claude -p … --allowedTools "Read,Edit,Bash(make test)" --output-format json`; evals/check.sh. 'some teams may prefer to run these evals offline on a set cadence rather than on every change.'


**Where in the article.**

- p.29–30 — Stage 4 Test › 'Continuous evals in CI' › intro, caveat, Prerequisites, Infrastructure, steps 1–5
- p.30–31 — Continuous evals › 'What it looks like (.github/workflows/agent-evals.yml)' and Governance
- p.44 — Stage 6 › step 7 – incident → eval
- p.47 — Recurring scans › step 7 – vulnerability class → eval

**Implementation notes.** Decided (decision 17): create the empty per-project evals/ on day one, write the suite once ~20 real changes exist. Two suites: (1) per project — /sdlc-init creates an empty evals/ with the p.30 workflow; phase (f) adds one eval per incident (37) and per fixed vulnerability class (38); (2) framework-level — in the plugin repo, triggered by PRs to the plugin. The article's own trigger is the product repo's CLAUDE.md and .claude/**, so a plugin-only suite would miss project-level changes. Do not wire it as a phase (d) job. evals/check.sh and the eval JSON are not shown in the article. Budget depends on the substrate decision (3).


#### Step 36 — Incident record: a version-controlled lessons file the diagnose agent reads and appends

- **Source tag:** ARTICLE  
- **Phase it belongs to:** f. maintain  
- **Importance:** 3 · Medium — It is the phase-(f) artifact of the artifact chain (step 1) and the memory that makes the second incident of a class cheaper than the first.


**Concept from the article.** 'writes the post-mortem to a version-controlled lessons file that future investigations can read'; the artifact list includes 'the incident record'; 'the response itself becomes part of the loop and memory for future incidents'. Figure: post-mortem written to lessons/2026-06-checkout-cache.md.


**Where in the article.**

- p.49 — Stage 6 Maintain › Claude on call with Claude Tag
- p.6 — Intro › artifact list – 'the incident record'
- p.49–50 — Figure – mock incident channel and caption

**Implementation notes.** Template ships lessons/ (one file per incident, in the intent's change folder or a top-level lessons/ directory); the diagnose agent of step 37 must read it before diagnosing and append the post-mortem when a fix ships. Reviewed like any file — it rides in the fix PR.


#### Step 37 — Closing the loop: deterministic detection script + bands.yaml tiers (1σ log · 2σ diagnose · 3σ propose) → intent.md

- **Source tag:** ARTICLE  
- **Phase it belongs to:** f. maintain  
- **Importance:** 4 · High — The article's end state — the loop closes with no person in the invocation path — and what turns your framework from a pipeline into a loop. Not 5 only because a new personal project may have no production metric yet; the article's first example (CI test failure rate) needs nothing but CI.


**Concept from the article.** "A deterministic script watches production and invokes Claude when a control band is breached." Steps: pick 'one metric with a stable rolling baseline, such as CI test failure rate, post-deploy 5xx rate, or PR cycle time'; write the detection script ('mean and standard deviation over a rolling window with rules (Western Electric or similar) … version controlled and unit tested, and detection stays entirely deterministic, with no model involved'); tiers in version-controlled config — 'At 1σ the script only logs, at 2σ it invokes Claude read-only to diagnose, and at 3σ Claude may act, though only by opening a PR into the review gate or triggering a pre-approved runbook'; trigger layer 'a scheduled workflow in GitHub or GitLab, a webhook from the existing monitoring stack, or a Cron Job'; 'Claude runs stateless'; 'The agent writes its diagnosis as intent.md in the Stage 1: Plan format'; 'When a fix ships, add an eval for the incident'. Infrastructure: 'A metrics store the detection script can query (Prometheus, the CI system's API, or equivalents), read access to the repository, a way to run Claude Code non-interactively in CI, or the Agent SDK for a service that receives webhooks.' Prerequisites: the intent.md format, accelerated PR reviews, hooks as an action boundary, 'a rollback path for CI/CD (which the highest autonomy tier invokes)'. bands.yaml: metric ci_test_failure_rate · baseline rolling_30d · rules western_electric · 1sigma log · 2sigma diagnose with tools 'Read,Grep,Bash(gh run view *)' · 3sigma propose with routes [pull_request, runbook:rollback-deploy]. Claude Tag figure: 'The rollback was rehearsed in staging this morning; shall I run it?' — 'Go.'; caption 'request, diagnosis, human authorization and fix all stay where the incident was handled.'


**Where in the article.**

- p.42–43 — Stage 6 Maintain › 'Closing the loop' › intro, Prerequisites, Infrastructure
- p.43–44 — Closing the loop › steps 1–7
- p.44 — 'What it looks like (… bands.yaml …)' and Governance
- p.45 — Closing the loop › metrics, the three 'Examples', 'Detection stays deterministic'
- p.49–50 — Claude Tag figure and caption – per-incident human authorization
- p.6 — Table row Maintain

**Implementation notes.** Template ships bands.yaml (copy p.44), a detection-script skeleton with unit tests in the cross-platform runtime, and a scheduled workflow. Decided (decision 15): the first metric is always CI test failure rate (the article's own example; exists on day one, reversible 3σ actions); the project's maintain adapter (9b) adds its own metric once it runs live. Detection stays model-free. 2σ reuses the diagnose agent read-only; 3σ may only open a PR (through gate (e)) or run a runbook you approved in advance — the article says 'act' in the text and 'propose' in the config; treat them as one. Decided (decision 14) — split by blast radius, written per route in bands.yaml: CI-scoped, reversible actions (quarantine a flaky test, open a revert PR) are pre-approved and run with no human in the path (p.43–44); anything touching a running system (rollback, config change) waits for your 'Go' (the p.49–50 model) — as a parked item in the queue, not a page. Output intent.md re-enters phase (a) via the triage queue (39). Phase (f) has no 'conclusion': its unit of work is one finding. Runtime: a CI step or an Agent SDK service for webhooks (p.43–44).


#### Step 38 — Recurring codebase scans (Claude Security, or a scheduled security-review run) → PR gate or intent.md → eval

- **Source tag:** ARTICLE  
- **Phase it belongs to:** f. maintain  
- **Importance:** 3 · Medium — Valuable, but the hosted product requires a Claude Enterprise organisation and cloud github.com; the pattern (scheduled scan → PR gate or intent.md → eval) is what matters.


**Concept from the article.** "A security scan is a point-in-time statement about a codebase under a particular model, and both halves go stale … The AI-native answer is to run the scan on a schedule, without a human in the invocation path, and to send what it finds through the same gates as any other change to the codebase." 'Claude Security is the hosted form of scheduled scanning' (Claude Enterprise, public beta, Mythos 5, findings validated with a confidence rating). Steps: connect and organise repos; first full scan as baseline; weekly schedule, 'scope scans to a directory or branch where a repository is large or mixed'; 'Dismiss with a reason, so the dismissal is recorded and the same finding does not return as new on the next run'; bounded finding → patch through the PR review gate; wider → intent.md; fix released → eval for the vulnerability class; export findings to the existing tracker. "Claude Security augments existing static analysis and dependency scanning. The deterministic checks stay in CI, and the model-driven scan covers the context-dependent vulnerabilities those checks are not built to find."


**Where in the article.**

- p.45–46 — Stage 6 Maintain › 'Recurring codebase scans' › intro, What changes, Prerequisites
- p.46–47 — Recurring scans › Infrastructure (availability, billing) and steps 1–7
- p.48 — Recurring scans › step 8, Governance and metrics

**Implementation notes.** Decided (decision 16): unless your plan includes Claude Security, implement the pattern with a weekly `claude -p` run of a security-review skill in read-only mode, routing findings exactly as the article's steps 5–7 (p.47) say [ADAPTED — the article gives no non-Enterprise alternative]. Keep deterministic scanners (dependency audit, SAST) in CI regardless. Dismissals record a reason and suppress that finding's signature.


#### Step 39 — Gate (f): triage queue of incident intents — fix now / schedule / dismiss with a reason; dismissals tune detection through a PR

- **Source tag:** ARTICLE  
- **Phase it belongs to:** f. maintain  
- **Importance:** 4 · High — The human gate of the autonomous loop and the feedback that keeps it quiet enough to trust; without recorded dismissals the same finding returns forever.


**Concept from the article.** "The service owner or on-call engineer triages the queue, routing product-facing findings to the product owner. Fix now, schedule, or dismiss. Dismissals tune the bands and help to reduce noise." Governance: 'A service owner triages and approves findings, resulting changes go through the normal PR review gate, and the runbooks the agent may trigger were approved in advance.' 'People triage and review that work, and no longer have to start it.'


**Where in the article.**

- p.44 — Stage 6 Maintain › Closing the loop › step 6 and Governance
- p.47 — Recurring scans › step 4 – dismiss with a reason
- p.42 — Maintain › AI-native column

**Implementation notes.** The queue is the set of open intent PRs labelled 'incident'; fix now = merge (which is also gate (a) for that intent), schedule = label, dismiss = close with a reason. Dismissals suppress that finding's signature; changes to the bands themselves go through a bands.yaml PR so the detection script stays 'version controlled and unit tested' (p.43) — the article says dismissals tune the bands, not that tuning is automatic.


#### Step 40 — Optional: a chat-channel entry route for incidents and requests (Claude Tag, or any bot that writes intent.md)

- **Source tag:** ARTICLE  
- **Phase it belongs to:** f. maintain  
- **Importance:** 1 · Optional — Team on-call tooling; for you the durable idea is that a message can start the loop with the same small-fix → PR / larger → intent.md rule.


**Concept from the article.** "Incidents can also arrive via other means such as workplace communication apps, like Slack or Teams." 'Claude Tag (public beta currently available in Slack) makes Claude a member of those channels under its own identity, so each new incident gets a first responder'. 'Tagged on a ticket over MCP or asked in the channel, Claude triages the work the same way. A small, well-bounded fix arrives as a PR through the review gate, and anything larger is written up as intent.md for Stage 1: Plan, at which point the loop starts feeding itself.' 'The channel is the audit trail'.


**Where in the article.**

- p.48–49 — Stage 6 Maintain › 'Claude on call with Claude Tag'
- p.50 — Figure caption
- p.42 — Maintain › AI-native column – 'a channel message … invokes Claude'

**Implementation notes.** Add later if you want to start intents from a chat app; Claude Tag is Slack-only in public beta (Teams is named only as an incident source). Any bot that can write intent.md and open the PR gives the same effect.


#### Step 41 — Observability: keep run transcripts, hook decisions and reviewer verdicts with the change; OpenTelemetry export later

- **Source tag:** ARTICLE  
- **Phase it belongs to:** cross-cutting  
- **Importance:** 3 · Medium — Runs you did not watch need a trace you can read afterwards; the article's hook and session metrics exist only in this export.


**Concept from the article.** 'what a session does is logged and attributed to the engineer who ran it'; 'Skill invocations are logged in session traces'; evidence is logged 'In the session transcript, which the OpenTelemetry export forwards to the organization's observability stack, and in the PR's check run'; 'Every hook decision is written to the OpenTelemetry export with a timestamp and an allow or block verdict'; 'Invocations, findings and triage decisions are logged with a timestamp.'


**Where in the article.**

- p.22 — Skills › Governance
- p.26 — Parallel sessions › Governance
- p.29 — Feedback loop › Governance – 'Where it is logged'
- p.39 — Hooks as approval gates › leading indicator
- p.44 — Closing the loop › Governance
- p.51 — Resources – Monitoring (OpenTelemetry), analytics dashboard, Compliance API

**Implementation notes.** Minimum viable: keep each non-interactive run's transcript (`--output-format json`) and the gate's verdicts in changes/<id>/evidence/, and log hook decisions to a CI artifact. Enable the OpenTelemetry export only if you later want dashboards.


#### Step 42 — Indicators: two counters in every PR description now; a scheduled agent report later

- **Source tag:** ARTICLE  
- **Phase it belongs to:** cross-cutting  
- **Importance:** 2 · Low — Almost every indicator is two git timestamps or a PR field, so it is cheap — but a monthly script you must run and read is the kind of system you said you cannot maintain.


**Concept from the article.** Every play in the dependency graph (plus Recurring scans) ends with 'How to measure it'. Plan: time to committed intent.md; survival rate; intent edits after the first spec.md (p.12). Design: intent→spec elapsed; spec edits after the first plan.md (p.15). Plan mode: first-pass merge share; plan-approval→merge time; rework cycles; diff matches plan.md (p.17). CLAUDE.md: repeated mistakes; time to first merged PR for a new member (p.20–21). Skills: policy-change→skill-merge time; findings citing the policy (p.23). Sessions: concurrent sessions; share of the day steering; merged per week vs rework (p.26). Feedback loop: first-pass CI success; review time per PR; change failure rate (p.29). Evals: pass rate; incident→eval time; CI vs production regressions (p.31). PR review: time to first review; comments resolved without a human; defects caught before merge vs escaping (p.35). Hooks: wait per gate; gate violations (p.39). CI/CD: failures triaged without paging; DORA (p.41). Closing the loop: breach→intent time; findings→merged fixes; repeat incidents (p.45). Scans: repos on schedule; finding→patch time; scan-found vs production-found; trend per scan (p.48).


**Where in the article.**

- p.12 — Stage 1 Plan › How to measure it
- p.15 — Stage 2 Design › How to measure it
- p.17 — Plan mode › How to measure it
- p.20–21 — The CLAUDE.md › How to measure it
- p.23 — Skills › How to measure it
- p.26 — Parallel sessions › How to measure it
- p.29 — Feedback loop › How to measure it
- p.31 — Continuous evals › How to measure it
- p.35 — PR review › How to measure it
- p.39 — Hooks as approval gates › How to measure it
- p.41 — CI/CD › How to measure it
- p.45 — Closing the loop › How to measure it
- p.48 — Recurring scans › How to measure it

**Implementation notes.** Now: the generated PR descriptions (27a) carry two counters — first-pass merge (yes/no) and fix iterations — which give the article's first-pass share and rework cycles for free. Later: a scheduled agent run walks changes/*/ and the PR history and opens a short report PR you merge or ignore. Skip the team-only indicators (new-member onboarding time, concurrent sessions per engineer).


#### Step 43 — Reference: adoption order per the p.8 dependency graph (how this guide's build stages were derived)

- **Source tag:** ARTICLE  
- **Phase it belongs to:** n/a (build-time guidance)  
- **Importance:** 3 · Medium — The article's own build order; B0–B5 follow it. It protects you from building a phase whose prerequisites are missing (an autonomous design pass without policy skills, CI/CD before the review gate).


**Concept from the article.** "The plays are listed with stage; the arrows give the order to adopt them in. The two are not the same. Start with any clay play — nothing points into it, so it needs nothing first. For any other play, the arrows pointing into it are the plays to adopt before it." Tier 1 (orange 'clay' nodes): Capture intent, CLAUDE.md, Feedback loop, Hooks, Plan mode. Tier 2: Skills (← CLAUDE.md), Subagents (← CLAUDE.md, ⇠ Feedback loop dotted), Evals (← CLAUDE.md, ← Feedback loop). Tier 3: Requirements & design (← Capture intent, ← Skills), PR review (← Evals, ⇠ Skills dotted). Tier 4: CI/CD (← PR review, ← Hooks). Tier 5: Closing the loop (← CI/CD, ← Capture intent).


**Where in the article.**

- p.8 — Figure – play dependency graph and its caption
- p.7 — Plays › 'Each play names its dependencies under "Prerequisites," which the dependency graph further illustrates'

**Implementation notes.** Caveats: the figure has no legend for dotted arrows; the text uses 'helps' exactly where the graph dots an arrow (p.24 'The feedback loop … also helps here'; p.32 'skills if the review passes enforce written policies'), which supports reading them as 'helps but not required'. The graph and the text prerequisites disagree in several places — PR review (text: CLAUDE.md, skills, defined subagents; graph: Evals, Skills dotted), Skills (text: 'a skill does not depend on' CLAUDE.md; graph: solid arrow), Plan mode (text: intent artifact and CLAUDE.md help; graph: nothing points in), Closing the loop (text adds PR reviews, hooks, rollback) — treat the union as the prerequisite list. Recurring scans, Claude Tag, Auto mode and the Legacy-systems sidebar are not nodes.
