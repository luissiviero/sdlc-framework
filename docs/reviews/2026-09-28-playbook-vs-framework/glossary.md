# Glossary of the playbook-versus-framework study

Every code the study and its follow-up use, with what it names and where it lives. Generated on 2026-10-13 from the files themselves (`target-design.md`, `crosswalk.json`, the record, `docs/ROADMAP.md`, `docs/decisions/index.md`) at `main` 269fbe2, plugin 0.3.7; a code added later is in those files, not here.

## The families at a glance

| Code | Family | Where it is defined |
|---|---|---|
| T1 to T32 | Target entries: what the owner wants the framework to become | `target-design.md` |
| R1 to R13 | ROADMAP candidates: proposals with a status and an order; R11 on come from the study | `docs/ROADMAP.md`, files under `docs/proposals/` |
| D1 to D26 | Settled decisions ("decision n") | `docs/decisions/<n>.md`, index in `docs/decisions/index.md` |
| `setup-home`, `x-roles`, … (48) | Crosswalk rows: one decision point each | `crosswalk.json`, the crosswalk page |
| (a) to (f) | Phases and their gates: intent, design, build, test, deploy, maintain | `docs/OPERATING_MODEL.md` |
| A, B, C, D | Option letters of one row's proposal; each row's letters are its own | the row's note and its T entry |
| H1, M1, L1 … | Severity ids of the audit's findings (high, medium, low), per evidence file | `evidence-article.md`, `evidence-framework.md` |
| #66, #67, #68, #71, #72 | The five issues the study filed, all fixed in plugin 0.3.1 | the record, section 5 |
| p.N | A print page of the article | `docs/reference/ai-native-sdlc-playbook.pdf`, text tagged `===== PAGE N =====` |

## T: target entries (32, all confirmed on 2026-10-09)

| Code | Entry | Status | Recorded | Crosswalk rows it came from |
|---|---|---|---|---|
| T1 | AI roles that advise, and one manager that reviews for the owner | confirmed 2026-10-09, two proposals | 2026-09-30 | setup-gates, setup-merge, plan-accept, design-spec, design-concerns, design-go, build-plan, build-plan-approve, build-start, build-subagents, build-config, build-skills, build-risk, x-headless, x-roles |
| T2 | The interview: how the manager and the roles question the owner | confirmed 2026-10-09, inside T1's second proposal | 2026-09-30 | plan-idea, design-trigger, design-mock, build-plan |
| T3 | The intent home: in the repository, written from anywhere, with examples | confirmed 2026-10-09 | 2026-09-30 | setup-home, plan-idea, design-mock |
| T4 | Names: the phases named after what they produce, and the other names judged against the article | confirmed 2026-10-09 | 2026-09-30 | — |
| T5 | Starting a project: the whole loop from the first change, with an optional start by hand | confirmed 2026-10-09 | 2026-10-02 | setup-adopt |
| T6 | Tickets become intents: a GitHub issue the owner labels starts the intent PR | confirmed 2026-10-09 | 2026-10-02 | plan-ticket |
| T7 | A rejection keeps its reason: the owner's closing comment is saved with the change | confirmed 2026-10-09 | 2026-10-02 | plan-accept |
| T8 | The formatter follows the project's languages: per file type, the project's own commands on the changed file | confirmed 2026-10-09 | 2026-10-03 | build-hooks |
| T9 | A risk-list hit is a line in the close-look banner: the merge accepts it, the reviewer briefs it, the paths are the project's | confirmed 2026-10-09 | 2026-10-03 | build-risk |
| T10 | The test loop closes by itself in CI: a red target starts the next round, and the verifier says which tree it read | confirmed 2026-10-09, already R10 | 2026-10-03 | test-loop, test-verify |
| T11 | A fix proves itself: the gate requires the lock, and the runner shows the test red at the lock commit and green at HEAD | confirmed 2026-10-09 | 2026-10-03 | test-bugfix |
| T12 | The build and test approvals: the label alone, recorded by the runner | confirmed 2026-10-09; R12, `docs/proposals/build-test-approvals-label.md` | 2026-10-03 | test-gate |
| T13 | The eval suite grows: more triggers, the incident case checked, a first set drafted after twenty changes | confirmed 2026-10-09 | 2026-10-03 | test-evals |
| T14 | The runbook PRs get the review pass: every automated code change the owner merges has been reviewed | confirmed 2026-10-09 | 2026-10-04 | deploy-review |
| T15 | Review corrections reach CLAUDE.md through one standing PR the owner merges when they choose | confirmed 2026-10-09 | 2026-10-05 | deploy-claudemd |
| T16 | The reviewer is tuned twice a month from signals already on record, through a standing REVIEW.md PR | confirmed 2026-10-09 | 2026-10-05 | deploy-tuning |
| T17 | The owner's @claude comment starts a fix round, beside the 'Request changes' review | confirmed 2026-10-09 | 2026-10-06 | deploy-comments, maintain-tag |
| T18 | Gate (e) is the owner's approving review; a GitHub App merges on it, and a rule holds unreviewed build PRs | confirmed 2026-10-09 | 2026-10-06 | deploy-approve |
| T19 | A failed CI run explains itself, and the release notes gain a plain-words paragraph beside the deterministic list | confirmed 2026-10-09 | 2026-10-07 | deploy-ci |
| T20 | An optional preview environment before the approval, and a rollback rehearsed there on a schedule | confirmed 2026-10-09 | 2026-10-07 | deploy-envs |
| T21 | The release label stays a second act, given in the same visit; a waiting or failed release reaches the digest, and the approver is recorded | confirmed 2026-10-09; R13, `docs/proposals/release-label-same-visit.md` | 2026-10-07 | deploy-release |
| T22 | The detection's state reaches the digest and a ref, and the next metric is a project setting | confirmed 2026-10-09 | 2026-10-07 | maintain-detect, maintain-diagnose |
| T23 | Triage: a dismissal is one act, the band change has its number, a scheduled incident says what it mutes | confirmed 2026-10-09 | 2026-10-07 | maintain-triage |
| T24 | Acting at 3σ: the Go is the owner's own, a rollback needs a release in the window, a route changed by comment is dispatched by the runner | confirmed 2026-10-09 | 2026-10-07 | maintain-act |
| T25 | Learning from an incident: the lesson checked at gate (e), the metric's return to baseline on the record | confirmed 2026-10-09 | 2026-10-07 | maintain-learn |
| T26 | The weekly scan validates its findings, applies its patch and reaches the digest | confirmed 2026-10-09 | 2026-10-07 | maintain-scan |
| T27 | The owner is shown what to do at every step: a "What you can do here" block on each PR, a "Next for you" line in the digest, and a guide command | confirmed 2026-10-09 | 2026-10-07 | — |
| T28 | The digest: ordered by what needs the owner, current at every park, never failing silently | confirmed 2026-10-09 | 2026-10-07 | x-queue |
| T29 | The sandbox closes what is open: shell writes to the hooks and the protected paths denied, the model credential hidden from shell commands, the workflow token kept | confirmed 2026-10-09 | 2026-10-07 | x-sandbox |
| T30 | The weekly window is guarded: every limit parks, a weekly ceiling and a budget per change, the spend visible, overspends learned from without raising budgets by themselves | confirmed 2026-10-09 | 2026-10-08 | x-limits |
| T31 | Measures that change a decision: true definitions, first-pass split by the plan's class, repeats per CLAUDE.md line, and DORA | confirmed 2026-10-09 | 2026-10-08 | x-measure |
| T32 | The record answers who, when and why: one approvals list, the run on every record, a line per round, the transcript as an artifact | confirmed 2026-10-09; R11, `docs/proposals/approvals-list.md` | 2026-10-09 | x-audit |

A row with "—" in the last column was recorded from the owner's own question rather than from one row's decision (T4 from naming, T27 from a request), or touches rows through other entries; each entry's own "Crosswalk rows it touches" line is the full list.

## R: ROADMAP candidates

| Code | Candidate | Proposal file | From the study |
|---|---|---|---|
| R1 | OKF adoption | `docs/proposals/okf-adoption.md` | — |
| R2 | Session tooling for PDFs and web pages | `docs/proposals/session-tooling-pdf-web.md` | — |
| R3 | A fresh clone of the project for the second step of a shared-checkout job | — | — |
| R4 | Python language audit | `docs/proposals/python-language-audit.md` | — |
| R5 | The pin-bump pull request | `docs/proposals/pin-bump-pr.md` | — |
| R6 | The `accept` verb | `docs/proposals/accept-verb.md` | — |
| R7 | The in-run reviewer on the latest Opus | `docs/proposals/reviewer-on-opus.md` | — |
| R8 | An external second opinion on the design at gate (b) | `docs/proposals/external-design-check.md` | — |
| R9 | The state of the work in the repository | `docs/proposals/state-index.md` | — |
| R10 | The test loop closes by itself in CI (study entry T10, brought forward) | `docs/reviews/2026-09-28-playbook-vs-framework/target-design.md` | T10 |
| R11 | The record answers who, when and why (study entry T32) | `docs/proposals/approvals-list.md` | T32 |
| R12 | The build and test approvals: the label alone, recorded by the runner (study entry T12) | `docs/proposals/build-test-approvals-label.md` | T12 |
| R13 | The release label in the same visit, a waiting or failed release in the digest, the approver recorded (study entry T21) | `docs/proposals/release-label-same-visit.md` | T21 |

R10 is study entry T10 brought forward before the study closed. R11 on are the study's line, written a few per PR in the order the owner confirmed.

## D: settled decisions

| Code | Decision |
|---|---|
| D1 | Where unattended claude -p runs execute and how they authenticate |
| D2 | Where plan.md is produced and approved |
| D3 | How you approve gates (c) and (d), which sit on one open PR |
| D4 | Branch rule that keeps the agent off main |
| D5 | Automation identity for non-interactive runs |
| D6 | Where the guardrails live so the agent cannot switch them off |
| D7 | Runtime for hooks, gate checks, detection scripts and eval checks (you are on Windows) |
| D8 | Framework distribution |
| D9 | Source of truth for artifacts and work items |
| D10 | Change folder and naming convention |
| D11 | What happens when a phase cannot finish on its own |
| D12 | Where the AI review pass runs |
| D13 | Shape of gate (e) — merge only, or merge + release authorization |
| D14 | Authorization model for 3σ runbooks in phase (f) |
| D15 | First metric to close the loop on |
| D16 | Recurring security scans |
| D17 | When to start evals and parallel worktrees |
| D18 | How many human gates per change — project and change profiles |
| D19 | What "deploy" and "maintain" mean for non-service projects |
| D20 | How finished work reaches you |
| D21 | Deferred review inside a phase — the owner reviews once, at the end (replaces the Lite profile) |
| D22 | How "ask for changes" runs by itself |
| D23 | Hosting scope: GitHub only |
| D24 | The owner's un-park verbs are labels |
| D25 | Gate (f) is per-finding triage; closing a PR at (a)–(e) abandons the change |
| D26 | Rollback authorization on a declared production (amends 14) |

The study never edits a decision. An entry that changes one says "amends Dn", and its decision file is written before the change's intent (as for R6, R10 and R12).

## Crosswalk rows (48)

| Row | Stage | Decision point | Relation | Better | Decision | T entry |
|---|---|---|---|---|---|---|
| `setup-adopt` | Setup | How much of the loop a project starts with, and in what order it grows | diverges | framework | blend | T5 |
| `setup-home` | Setup | Where intents live and who sets it up | adapted | framework | blend | T3 |
| `setup-gates` | Setup | Which human approval gates exist, and where they are enforced | adapted | framework | blend | T1 |
| `setup-merge` | Setup | Who may merge to main | adapted | framework | blend | T1 |
| `plan-idea` | Plan | An idea becomes intent.md | adapted | playbook | blend | T2, T3 |
| `plan-ticket` | Plan | A ticket or an alert becomes intent.md | adapted | playbook | blend | T6 |
| `plan-accept` | Plan | Intent accepted or rejected | same | playbook | blend | T1, T7 |
| `design-trigger` | Design | What starts the requirements and design pass | same | both | keep | T2 |
| `design-spec` | Design | Writing the spec | same | both | keep | T1 |
| `design-mock` | Design | Front-end mock | adapted | playbook | blend | T2, T3 |
| `design-concerns` | Design | Resolving flagged concerns | adapted | playbook | blend | T1 |
| `design-go` | Design | Deciding the spec goes to build | same | both | blend | T1 |
| `build-plan` | Build | Producing the plan | adapted | playbook | blend | T1, T2 |
| `build-plan-approve` | Build | Approving the plan | adapted | both | blend | T1 |
| `build-start` | Build | What starts implementation | adapted | framework | blend | T1 |
| `build-hooks` | Build | Guardrail hooks during the session | adapted | framework | blend | T8 |
| `build-plansync` | Build | Keeping plan.md in step with the work | same | framework | keep | — |
| `build-subagents` | Build | Subagents and parallel sessions | adapted | framework | keep | T1 |
| `build-config` | Build | Who approves changes to CLAUDE.md and skills | adapted | framework | blend | T1 |
| `build-skills` | Build | Who writes the policy skills, and whether a project adds its own | adapted | playbook | blend | T1 |
| `build-risk` | Build | Risky edits (migrations, infra, change tickets) | adapted | framework | blend | T1, T9 |
| `test-loop` | Test | The feedback loop | adapted | playbook | blend | T10 |
| `test-bugfix` | Test | Bug fixes: the failing test first | same | playbook | blend | T11 |
| `test-verify` | Test | Final check before review | adapted | both | blend | T10 |
| `test-gate` | Test | The gates after Build and after Test | adapted | framework | blend | T12 |
| `test-evals` | Test | Evals | adapted | playbook | blend | T13 |
| `deploy-review` | Deploy | The AI review passes | adapted | both | blend | T14 |
| `deploy-claudemd` | Deploy | Review findings feed CLAUDE.md | adapted | playbook | blend | T15 |
| `deploy-tuning` | Deploy | Tuning the reviewer | missing | playbook | blend | T16 |
| `deploy-comments` | Deploy | Acting on review comments | adapted | framework | blend | T17 |
| `deploy-approve` | Deploy | Approving the code | adapted | playbook | blend | T18 |
| `deploy-ci` | Deploy | Judgment steps in CI | adapted | playbook | blend | T19 |
| `deploy-envs` | Deploy | Environments and deploy tools | adapted | playbook | blend | T20 |
| `deploy-release` | Deploy | Production release authorization | adapted | both | blend | T21 |
| `maintain-detect` | Maintain | Metric and detection | same | both | blend | T22 |
| `maintain-diagnose` | Maintain | Diagnosis becomes intent.md | same | both | blend | T22 |
| `maintain-triage` | Maintain | Triage | adapted | both | blend | T23 |
| `maintain-act` | Maintain | Acting at 3σ | adapted | framework | blend | T24 |
| `maintain-learn` | Maintain | Learning from an incident | same | both | blend | T25 |
| `maintain-scan` | Maintain | Recurring security scans | adapted | playbook | blend | T26 |
| `maintain-tag` | Maintain | Claude on call in a channel | missing | framework | keep | T17 |
| `x-headless` | Across stages | The gate between autonomous stages | adapted | framework | keep | T1 |
| `x-queue` | Across stages | How finished work reaches a person | added | framework | blend | T28 |
| `x-sandbox` | Across stages | Sandbox, tokens and identity of agent jobs | adapted | framework | blend | T29 |
| `x-limits` | Across stages | Run limits and cost bounds | added | framework | blend | T30 |
| `x-measure` | Across stages | Measuring whether the plays work | adapted | framework | blend | T31 |
| `x-audit` | Across stages | Logging and the audit trail | adapted | framework | blend | T32 |
| `x-roles` | Across stages | Who the humans are | diverges | playbook | blend | T1 |

Prefixes: `setup-`, `plan-`, `design-`, `build-`, `test-`, `deploy-`, `maintain-` name the article's stages; `x-` marks a row across stages.

## Values used in the rows

| Field | Value | Meaning |
|---|---|---|
| relation | same | both do it the same way |
| relation | adapted | same intent, different mechanism |
| relation | added | the framework does something the article does not ask for |
| relation | missing | the article has it, the framework does not |
| relation | diverges | they point in different directions |
| better | playbook, framework, both | which workflow the owner judged better at that step |
| decision | keep | the framework's version stays as it is |
| decision | blend | the framework's version stays, with additions (the T entry) |
| decision | later | parked for later (x-roles until 2026-10-09; none now) |
| status | tentative, confirmed, dropped | an entry's or a note's state; every entry is confirmed since 2026-10-09 |
| map kind | d, c, w, r | a decision every change needs (Setup: once per project), a decision only in some cases, work, the same act as another row |
| map lane | P, C, A | a person, Claude, the pipeline |

## The owner's criteria and weights

Saved on 2026-09-29 (`crosswalk.json`, `owner.criteriaWeights`): safety 1, owner attention 3, autonomy 3, auditability 2, cost 0, fidelity to the article 2. Every recommendation in the study is weighed against them.

## Phases, gates and the names T4 proposes

| Letter | Phase today | Gate | Name proposed by T4 |
|---|---|---|---|
| (a) | plan: `/sdlc-plan` writes `intent.md` | the owner merges the intent PR | intent |
| (b) | design: spec.md and plan.md | the owner merges the spec and plan PR | design |
| (c) | build | Standard: on its own; Full: `sdlc:c-approved` | build |
| (d) | test | Standard: on its own; Full: `sdlc:d-approved` | test |
| (e) | deploy: review pass and release | the owner merges the build PR (T18: approves it); on a declared production also `sdlc:release-approved` | deploy |
| (f) | maintain: detection, scan, triage | the owner triages: merge, `sdlc:schedule`, or close with a comment | maintain |

Profiles (D18): Standard, where (c) and (d) continue on their own, and Full, where they wait for the owner's labels. Branches are `sdlc/<id>/<phase letter>`.

## The pages and files of the study

| Name | What it is |
|---|---|
| the record | `docs/reviews/2026-09-28-playbook-vs-framework.md`; section 7 is the state and the decisions, section 8 the resume prompt |
| the crosswalk | `crosswalk.json` (the source of truth) and its page https://claude.ai/artifact/PFnRZ32pwTr4y422Gna2mz; the owner's notes live in the page's store, collection `choices` |
| the target design | `target-design.md`, T1 to T32 |
| the three workflow pages | playbook https://claude.ai/artifact/WhLTjcSzJqQmUFm3aP5G6L, framework https://claude.ai/artifact/KW8jWunfLNa9WgBSzJxw4S, target https://claude.ai/artifact/13X8rzF9KsfekmeSs1w5rM; snapshots beside the record |
| `naming.md` | the 23 naming differences behind T4 |
| the evidence files | `evidence-article.md`, `evidence-framework.md`, `evidence-source.md`: the audit's findings with their H, M, L ids |
| HANDOFF item 14 | the study's line: the confirmed entries become proposals and ROADMAP rows, built after 1.0.0 |
