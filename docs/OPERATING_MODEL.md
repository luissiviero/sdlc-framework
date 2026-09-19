# Operating model (draft — step 1 of the build guide)

> The loop keeps running. Human judgement stays above it. — *The AI-Native SDLC playbook*, p.50

This file is the first artifact of the framework. It states what the framework does, which artifact every phase commits, when a human is involved, and how change requests flow. Everything else in the repo implements it. Rationale and article citations live in `docs/BUILD_GUIDE.md`; the choices behind it in `docs/DECISIONS.md`.

## 1. Purpose

A framework that connects to any project (any size, any type: service, library, research code, data pipeline) and drives each change through six phases:

| Phase | What runs | Artifact committed | Read by |
|---|---|---|---|
| (a) plan | interactive brainstorm with the owner | `intent.md` | (b) |
| (b) design | autonomous: spec pass with policy skills, then a read-only planning run | `spec.md` + `plan.md` | (c) |
| (c) build | autonomous: implementation under auto-accept with hooks, simplifier, verifier | the diff and its tests, on the build PR | (d) |
| (d) test | autonomous: fresh-context full run — tests, build, lint, screenshots, verifier | `evidence/` + PR check run | (e) |
| (e) deploy | autonomous: review passes, fix loop until green, release prepared per the project's adapter | reviewed PR / release | production |
| (f) maintain | standing loop: deterministic detection → diagnose → propose | incident record (`lessons/`) → new `intent.md` | (a) |

Principle (article p.6–8): every phase ends by committing its artifact; the accepted artifact fires the next phase. The chain of commits is the audit trail.

## 2. Roles

One person owns every role the article names (originator, product owner, tech lead, engineer, code owner, release manager, service owner). Separation of duties is therefore rebuilt from:

- **writer ≠ judge** — the agent that produced an artifact never judges it; a different agent in a fresh context reviews it, and only the owner approves;
- **an automation identity** distinct from the owner's account for every non-interactive run (the CI workflow token), so the log separates what the agent did from what the owner approved;
- **branch rules** — only the owner's account can merge to `main`; the automation identity has branch-only write access; no bypass rights.

## 3. Profiles — which gates are human

Set per project in `sdlc.yaml` by `/sdlc-init`; overridable per change in `changes/<id>/status.yaml`.

| Profile | Human gates | Automated gates | For |
|---|---|---|---|
| **Standard** (default) | (a) merge intent PR · (b) merge spec+plan PR · (e) merge build PR | (c), (d) | most projects |
| **Full** | (a), (b), (c) review + label, (d) review + label, (e) merge (+ release label) | — | live production, money at stake |
| **Lite** | (a) merge intent PR · (e) merge build PR | (b), (c), (d) | scripts, experiments, docs |

Automated gates are passed by the **confidence gate**: deterministic checks (artifact matches its template; tests, build, lint green; evidence present; no Important review findings; `plan.md` ↔ diff consistent; no diff touching `.claude/**`, `CLAUDE.md`, `REVIEW.md` unless the change is the framework itself) followed by an adversarial reviewer agent in a fresh context that returns *continue* or *park*.

## 4. Gate mechanics

| Gate | Human form | Event that starts the next phase |
|---|---|---|
| (a) | merge of the intent PR | merge → design workflow |
| (b) | merge of the spec+plan PR (Standard, Full) | merge → build workflow. Lite: spec+plan committed on the change branch; the design job dispatches the build job after a passing confidence gate |
| (c) | Full only: approving review + label `sdlc:c-approved` on the build PR | label → test workflow. Standard/Lite: the build job dispatches the test job |
| (d) | Full only: approving review + label `sdlc:d-approved` | label → review workflow. Standard/Lite: the test job dispatches the review job |
| (e) | merge of the build PR; plus a release label only when `sdlc.yaml` declares a real production | merge → the project's deploy adapter |
| (f) | triage of each incident intent PR: merge (fix now) · label (schedule) · close with a reason (dismiss) | merge = gate (a) of that intent |

GitHub rule the design respects: events caused by the workflow token do not start new workflow runs, except `workflow_dispatch` / `repository_dispatch`. The owner's merges and labels fire workflows normally; every automated transition dispatches the next phase explicitly with the change id.

## 5. Change requests

At any human gate, "ask for changes" = review comments on that PR. One command, `/sdlc-fix`, reads the unresolved comments and failing checks, re-runs the phase with them as constraints, and pushes to the same branch. This applies to intent, spec+plan and build PRs alike.

## 6. Park, never page

When a confidence gate fails, a run limit is hit (iterations, wall-clock, budget, pause flag), or a risk-list item is touched (auth, data migrations, money movement, production config), the run **parks**: it finishes every artifact it can, writes a "what I need from you" section into the PR description, records the reason in `status.yaml`, labels the PR `sdlc:needs-human`, and notifies nobody. Parked and finished work waits in the review queue.

## 7. Review queue

The queue is the PR list filtered by `sdlc:*-ready` (a run stopped at a human gate) and `sdlc:needs-human` (parked). Every PR the framework opens or updates starts with a ≤5-bullet summary: what changed and why, evidence status, review findings by severity, plan conformance, and — if parked — what is needed. A scheduled job posts a daily digest of the queue. Nothing pushes to the owner.

## 8. Conventions

- One folder per change: `changes/<id>-<slug>/` with `intent.md`, `spec.md`, `plan.md`, `evidence/`, `status.yaml` (phase, profile override, change type feature/fix, gate result, parked reason, iteration count).
- Branches `sdlc/<id>/<phase>`. Labels `sdlc:<phase>-ready`, `sdlc:<phase>-approved` (Full only), `sdlc:needs-human`.
- The repo is the source of truth for every artifact; any external tracker holds the issue number ↔ commit SHA link.
- `plan.md` is produced at the end of phase (b) by a read-only run (Read/Grep/Glob only) and approved with `spec.md`; the implementation run of phase (c) is the first run with edit and shell tools. In (c) a pre-commit check enforces that `plan.md` changes whenever source changes.
- Process content (commands, skills, agents, hooks, gate logic) lives in the plugin, pinned per project by version; project content (`CLAUDE.md` body, test commands, protected paths, `sdlc.yaml`, `REVIEW.md`, `bands.yaml`, `evals/`) lives in the project.
- Every hook, gate check, detection script and eval check is Python; one task runner works on Windows and Linux.
- Guardrails protect themselves: the protected-path hook covers `.claude/**`, `CLAUDE.md`, `REVIEW.md` and the hook scripts; a user-level managed settings file on the owner's machine sets `allowManagedPermissionRulesOnly` / `allowManagedHooksOnly`; CI loads hooks and permissions from the pinned plugin, never from the PR branch; bypass-permissions mode is never used.

## 9. Phase adapters (per project, in `sdlc.yaml`)

- `profile`: standard | full | lite
- `deploy.action`: what makes a merged change live (publish package · schedule job · regenerate report · promote to paper trading · deploy service)
- `deploy.production`: true/false — turns on the release label and the production-gate hook
- `maintain.metric` and `maintain.source`: the watched metric and where the detection script reads it (default for every new project: CI test failure rate from the CI API)
- `maintain.runbooks`: each with `authorization: preapproved | go` — CI-scoped reversible actions are pre-approved; anything touching a running system waits for the owner's "Go" (as a parked item)
