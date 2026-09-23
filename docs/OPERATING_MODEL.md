# Operating model

> The loop keeps running. Human judgement stays above it. — *The AI-Native SDLC playbook*, p.50

This file is the first artifact of the framework (build guide step 1; finalised in session 1). It states what the framework does, which artifact every phase commits, when a human is involved, and how change requests flow. Everything else in the repo implements it. Rationale and article citations live in `docs/BUILD_GUIDE.md`; the choices behind it in `docs/DECISIONS.md`; platform facts verified against the Claude Code docs in `docs/NOTES.md`.

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

Set per project in `sdlc.yaml` by `/sdlc-init`; overridable per change in `changes/<id>-<slug>/status.yaml` (`profile_override`).

| Profile | Human gates | Automated gates | For |
|---|---|---|---|
| **Standard** (default) | (a) merge intent PR · (b) merge spec+plan PR · (e) merge build PR | (c), (d) | most projects |
| **Full** | (a), (b), (c) review + label, (d) review + label, (e) merge (+ release label) | — | live production, money at stake |
| **Lite** (withdrawn, decision 21) | (a) merge intent PR · (e) merge build PR | (b), (c), (d) | do not choose it for a new project; still offered by `/sdlc-init` and in the code until step 16a ships and removes it |

Automated gates are passed by the **confidence gate** (`plugin/gate/`, session 2): deterministic checks (artifact matches its template; no open flagged concern in `spec.md`; tests, build, lint green; evidence present; no Important review findings; `plan.md` ↔ diff consistent; no diff touching `.claude/**`, `CLAUDE.md`, `REVIEW.md`, `sdlc.yaml` unless the change is the framework itself — `intent.md` says `Framework change: yes`; no risk-list hit the owner has not accepted; run limits) followed by the adversarial reviewer agent's verdict, written in a fresh context as `evidence/adversarial-review-<phase>.json`: *continue* or *escalate* (= park), required at (b), (c) and (d) in every profile. The gate judges committed work against what the owner approved: the intent as merged at gate (a), `sdlc.yaml` as on the base branch when the diff changes it, HEAD rather than the working tree. The same checks run at a human gate: all green → the run stops with `sdlc:<phase>-ready`; a failed check parks there too.

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

### 4.1 Composition of the phase runs (build guide step 24; B3)

Every run is one slash command (`/sdlc-design`, `/sdlc-build`, `/sdlc-test`, `/sdlc-deploy`), by hand or as a `claude -p` job. The same skeleton for all: **register** (`gate/cli.py start-run`, the wall clock) → **work** → **commit** on the phase's branch (`state/cli.py commit-phase`) → **adversarial verdict** for HEAD (`sdlc:adversarial-reviewer`, fresh context) → **gate** (`gate/cli.py check`: `continue` / `wait` / `park`, writes `evidence/gate-<phase>.json`) → **commit the evidence** → **surface** (open or update the PR with the ≤5-bullet summary, apply the label the gate printed) → **hand over** (a `continue` dispatches the next run; a `wait` or `park` stops). A run never asks the owner anything: a gap is a flagged concern, a parked reason or a review comment. Re-running a command on the same branch is safe and is how review comments are applied (`/sdlc-fix` re-runs the phase with the comments as constraints and bumps `status.iterations`).

| Phase · command | Inputs (as the owner approved them) | Branch | Work, in order | Artifact | Exit |
|---|---|---|---|---|---|
| (b) `/sdlc-design` | `intent.md` as merged at (a) | `sdlc/<id>/b` from the default branch | policy skills loaded → `spec.md` (prompt v1, p.14) → read-only planning run → `plan.md` → commit → verdict → gate (b) | `spec.md`, `plan.md` | Standard/Full: `wait`, PR with `sdlc:b-ready`; the owner's merge starts (c). Lite: `continue` → (c) starts from `sdlc/<id>/b`. Park in any profile still opens the PR (`sdlc:needs-human`, "what I need from you") |
| (c) `/sdlc-build` | `spec.md` + `plan.md` as merged at (b) (Lite: as committed on `sdlc/<id>/b`) | `sdlc/<id>/c` from the default branch (Lite: from `sdlc/<id>/b`); the build PR lives here through (d) and (e) | preflight → permission mode (`acceptEdits` only when it allows; never bypass) → fix-type: the reproducing test first, committed, shown to fail → implementation under the hooks, `plan.md` updated in the same commit when the work departs from it → code-simplifier → verifier → `evidence/verifier.md` → commit → verdict → gate (c) | the diff and its tests; `evidence/verifier.md` | Standard/Lite: `continue` → (d); the PR is opened as a draft. Full: `wait`, `sdlc:c-ready`; approving review + `sdlc:c-approved` starts (d) |
| (d) `/sdlc-test` | the build branch after gate (c) | `sdlc/<id>/c` (same PR) | fresh context → `evidence/collect.py` runs the three `sdlc.yaml` commands into `test.log`, `build.log`, `lint.log` → a failing target is fixed and re-run (each round bumps `iterations`; the cap parks) → screenshot loop against the mock when `plan.md` Proof names one → verifier → `evidence/verifier.md` → commit → verdict → gate (d) → check-run summary | `evidence/` | Standard/Lite: `continue` → (e). Full: `wait`, `sdlc:d-ready`; approving review + `sdlc:d-approved` starts (e) |
| (e) `/sdlc-deploy` | the build branch after gate (d) | `sdlc/<id>/c` (same PR) | review pass in a fresh context with `REVIEW.md` → `evidence/review-findings.json` → fix loop while an Important finding stands and the cap holds (`/sdlc-fix` semantics: fix, re-run (d)'s collection, re-review) → PR summary regenerated (findings by severity, plan conformance, counters) → gate (e) | reviewed PR, ready for review, `sdlc:e-ready` | always `wait` (human in every profile); the owner's merge is the gate; the deploy adapter and the release label are B4 (steps 29, 32) |
| (f) `/sdlc-maintain` | `bands.yaml`, the adapter's metric | `sdlc/<id>/a` of a new incident intent | detection (B5, step 37) → one finding per run → diagnosis through gated routes → incident `intent.md` (skill `intent-template`, Evidence section) → intent PR | `intent.md` | gate (f) = the owner's triage of the incident PR (merge, label, close); command file waits for B5 |

Rules the table relies on. **Wait sits where the label is read**: in the Full profile the (c) and (d) runs stop after the gate; the owner's label starts the next run (CI: the `labeled` event; by hand: the next command). **Evidence is committed after the gate** so the verdict judges the artifact commit; each phase produces its own verdict. **The PR is the audit record** (p.34–35): opened at (c) as a draft in every profile, marked ready at (e), never split. **Iterations are one counter per change** (`status.yaml: iterations`, bumped by every fix round in (c), (d), (e) and `/sdlc-fix`; the cap of `sdlc.yaml: gate` applies to the sum, and the owner resets it with `set-iterations`); `set-iterations` and `accept-risk` are owner actions (§8, decision 11) and the gate's `owner_actions` check parks when a run's own commit introduced them. **Nothing in a run edits guardrail files or `intent.md`.** **Spend is known only in CI**: `record-spend` is fed by `run_phase.py` from the `claude -p` result; a by-hand or cloud-session run has no spend figure, so `gate.max_budget_usd` binds unattended runs only, while iterations and the wall clock bind every run.

### 4.2 Merge-triggered workflows (build guide step 30; decisions 1, 5; B3)

One workflow per transition, installed into the project by `/sdlc-init` from `template/.github/workflows/`; every step is `python` or `claude`. Each phase job calls `plugin/ci/run_phase.py --phase <p> --id <id>`, which switches to the phase's work branch, guards (state, pause, approval label, no guardrail file changed on the branch), runs and hands over; a park commits `status.yaml`, pushes and updates the PR with `sdlc:needs-human`; a job whose guard fails exits green with `skip: <reason>`, so a duplicate trigger is harmless.

| Workflow | Trigger (the owner's act or the previous job's dispatch) | Change id from | Guard (`status.yaml`, base branch copy of `sdlc.yaml`) | Runs | Hands over |
|---|---|---|---|---|---|
| `sdlc-design.yml` | `pull_request` `closed` with `merged == true`, base = default branch, head `sdlc/<id>/a` · `workflow_dispatch(change_id)` for a re-run | head branch, or the input | phase `a`, not parked, not paused | `/sdlc-design <id>` (first creates the `sdlc:*` labels) | Lite and `continue`: dispatch `sdlc-build.yml`. Standard/Full: nothing (the spec+plan PR waits) |
| `sdlc-build.yml` | `pull_request` `closed` merged, head `sdlc/<id>/b` · `workflow_dispatch(change_id)` | head branch, or the input | phase `b`, gate `passed`, not parked | preflight → `/sdlc-build <id>` | `continue`: dispatch `sdlc-test.yml`. Full: nothing (label starts it) |
| `sdlc-test.yml` | `workflow_dispatch(change_id)` · `pull_request` `labeled` with `sdlc:c-approved`, head `sdlc/<id>/c` | input, or head branch | phase `c`, gate `passed`; Full: the label present and its actor is not the workflow token | `/sdlc-test <id>` (fresh job = fresh context) | `continue`: dispatch `sdlc-deploy.yml`. Full: nothing |
| `sdlc-deploy.yml` | `workflow_dispatch(change_id)` · `pull_request` `labeled` with `sdlc:d-approved`, head `sdlc/<id>/c` | input, or head branch | phase `d`, gate `passed`; Full: the label present, actor not the token | review job: `claude -p` with `review/cli.py prompt` output (Read/Grep/Glob, `git`, one Write) → `review/cli.py validate` → then `/sdlc-deploy <id>` | none: gate (e) is the owner's merge; the deploy adapter is B4 |
| `sdlc-digest.yml` | `schedule` daily, off the hour · `workflow_dispatch` | — | — | `pr/digest.py --repo <owner/repo>` | none |

Rules. **Events from the workflow token never start these workflows** (GitHub: only `workflow_dispatch` and `repository_dispatch` do), so the hand-over column is an explicit `workflow_dispatch` with the change id; the owner's merges and labels fire normally. **Concurrency is keyed on the change's work branch**: `group: sdlc-${{ inputs.head_ref || github.event.pull_request.head.ref }}`, `cancel-in-progress: false` (GitHub keeps one running and one pending run per group); every dispatch passes `change_id` and `head_ref` (the next phase's work branch, `sdlc/<id>/b` or `sdlc/<id>/c`), and a merge- or label-fired run keys on the PR's head branch, so all runs of one change serialise. A merge-fired design or build workflow runs only for heads under `sdlc/`. **Permissions per job**: `contents: write`, `pull-requests: write`, `issues: write`, `checks: write`, `actions: write`; nothing else, no deploy secret. **The pinned framework** is checked out from `luissiviero/sdlc-framework` at the version `sdlc.yaml` pins (a public repository, no token) and loaded with `--plugin-dir`; hooks and permissions come from that checkout (decision 6 layer iii). The project checkout still carries its own `.claude/settings.json`: in an untrusted folder Claude Code ignores its allow rules and marketplace declaration (NOTES §3) and honours its deny rules; whether it would honour a `hooks` or `env` block from the PR branch is not documented, so `run_phase.py` refuses to run a phase whose branch changed `.claude/**`, `CLAUDE.md`, `REVIEW.md`, `sdlc.yaml` or a protected path unless the merged intent says `Framework change: yes` (it parks instead), and the gate's `guardrails` check re-judges the diff afterwards. Managed settings (layer ii) cannot reach a runner. **Credential** (NOTES §2): `ANTHROPIC_API_KEY` → `claude -p --bare`, else `CLAUDE_CODE_OAUTH_TOKEN` → `claude -p`; the run passes `--settings` with the CI settings file (sandbox on, allowed domains, deny rules) explicitly, because bare mode reads no settings by itself. **Bounds**: `--max-turns`, `--max-budget-usd` from `sdlc.yaml: gate`, `--permission-mode acceptEdits` only when the preflight allows, `--permission-prompts none`; `total_cost_usd` from `--output-format json` goes to `gate/cli.py record-spend`; the JSON transcript is stored under `evidence/`. **Sandbox** (article p.40): the GitHub-hosted runner is an ephemeral VM holding only the CI credential; inside it Claude Code's own sandbox (bubblewrap, `failIfUnavailable: true`, `network.allowedDomains` = the API, GitHub and the package registries) confines the run. Minimum Claude Code version: 2.1.278.

## 5. Change requests

At any human gate, "ask for changes" = review comments on that PR. One command, `/sdlc-fix`, reads the unresolved comments and failing checks, re-runs the phase with them as constraints, and pushes to the same branch. This applies to intent, spec+plan and build PRs alike.

## 6. Park, never page

When a confidence gate fails, a run limit is hit (iterations, wall-clock, budget, pause flag), or a risk-list item is touched (auth, data migrations, money movement, production config), the run **parks**: it finishes every artifact it can, writes a "what I need from you" section into the PR description, records the reason in `status.yaml`, labels the PR `sdlc:needs-human`, and notifies nobody. Parked and finished work waits in the review queue. The owner un-parks by settling the item: a review comment (→ `/sdlc-fix`), `accept-risk` for a risk-list hit (recorded in `status.yaml: risk_accepted`), `set-iterations` after an iteration cap, `paused: false` in `sdlc.yaml`.

## 7. Review queue

The queue is the PR list filtered by `sdlc:*-ready` (a run stopped at a human gate) and `sdlc:needs-human` (parked). Every PR the framework opens or updates starts with a ≤5-bullet summary: what changed and why, evidence status, review findings by severity, plan conformance, and — if parked — what is needed. A scheduled job rewrites the body of one pinned issue ("SDLC review queue") with the digest. Nothing pushes to the owner: the framework never comments, assigns, @mentions or requests a review; the owner sets the repository watch to "Participating and @mentions", and may turn off GitHub's default e-mail for failed Actions runs — a parked phase is a green job by design (only an infrastructure failure is red).

## 8. Conventions

- One folder per change: `changes/<id>-<slug>/` with `intent.md`, `spec.md`, `plan.md`, `evidence/`, `status.yaml` (phase, profile override, change type feature/fix, entry route idea/ticket/incident, gate result, parked reason, iteration count, external reference). `<id>` is a four-digit sequence allocated from the folder (`0000` is the framework's own installation); `<slug>` is the kebab-case title. `plugin/state/` is the only writer.
- Branches `sdlc/<id>/<phase>`: `a` carries the intent PR, `b` the spec+plan PR, `c` the build PR that stays open through (d) and (e). Labels `sdlc:<phase>-ready`, `sdlc:<phase>-approved` (Full only), `sdlc:needs-human`.
- The repo is the source of truth for every artifact; any external tracker holds the issue number ↔ commit SHA link.
- `plan.md` is produced at the end of phase (b) by a read-only run (Read/Grep/Glob only) and approved with `spec.md`; the implementation run of phase (c) is the first run with edit and shell tools on source. (Phase (a) writes only `changes/<id>-<slug>/intent.md`, interactively with the owner.) In (c) a hook on `git commit` denies a commit that changes source without changing `plan.md` in the same commit.
- Process content (commands, skills, agents, hooks, gate logic) lives in the plugin, pinned per project by version; project content (`CLAUDE.md` body, test commands, protected paths, `sdlc.yaml`, `REVIEW.md`, `bands.yaml`, `evals/`) lives in the project.
- Every hook, gate check, detection script and eval check is Python with no third-party dependency; one task runner works on Windows and Linux. Hooks are registered in exec form (`python` plus the script path), so no shell is involved on any platform. Until B3 the phase commands run by hand, on the owner's PC or in a Claude Code cloud session; from B3 they run in GitHub Actions under the automation identity.
- Test-file lock for fix-type changes (build guide step 25; article p.28 step 4, p.35): in a change whose `status.yaml` says `change_type: fix`, the build run writes and commits the reproducing test first and then sets `status.yaml: tests_locked: true`; from that commit until the owner's merge the plugin's PreToolUse hook denies every edit under the project's test paths on the `sdlc/<id>/c` branch (phases (c), (d), (e) share it), and `REVIEW.md` rejects a diff that touches a pre-existing test in a fix task. Test paths are `sdlc.yaml: test_paths` (globs; `/sdlc-init` writes the defaults for the detected language). Only the owner unlocks (`state/cli.py unlock-tests`), in a reviewed PR, when the test itself was wrong.
- Guardrails protect themselves in three layers (decision 6). (i) The protected-path hook in the plugin covers `.claude/**`, `CLAUDE.md`, `REVIEW.md`, `sdlc.yaml` and the plugin's own files, with `Edit(...)` deny rules in the project settings as a second net; the hook has no exception. The only sanctioned writer of guardrail files in a run is `/sdlc-init`'s install script, which only adds (rules, keys, sections) and whose output rides in the change-0000 PR; every other guardrail change is made by the owner in a reviewed PR. (ii) On the owner's machine a *managed* settings file (system path, see `docs/owner-machine/`) sets `allowManagedPermissionRulesOnly` and `allowManagedHooksOnly`; because those keys ignore project permission rules and block non-managed plugin hooks, that file also carries the permission rules and force-enables `sdlc@sdlc-framework`. Cloud sessions never read it: there, the repo's `.claude/settings.json` and the plugin it declares are the layers. (iii) CI loads hooks and permissions from the pinned plugin, never from the PR branch. Bypass-permissions mode is never used and is disabled in every settings file.

## 9. Phase adapters (per project, in `sdlc.yaml`)

- `profile`: standard | full | lite (lite withdrawn, decision 21; in the code until step 16a)
- `commands.build` / `commands.test` / `commands.lint`: the one-command targets that exit non-zero on failure (detected or created by `/sdlc-init`); the framework refuses to enter phase (c) without them
- `protected_paths`: the project's own frozen paths, added to the always-protected set
- `risk_list`: touching any item parks the change at its next gate (default: auth, data migrations, money movement, production config)
- `plan_sync.exempt`: globs (besides `changes/**`) whose changes do not require a `plan.md` update in (c); `hooks.format_on_edit`: switch for the formatter hook
- `paused` and `gate.*` (`max_iterations`, `max_iterations_non_routine`, `max_wall_clock_minutes`, `max_budget_usd`, `command_timeout`): the run limits every gate enforces; a limit hit parks with the partial evidence
- `bands.yaml` (next to `sdlc.yaml`): the control bands of phase (f) — metric, baseline, rules, the three σ tiers and, per 3σ route, `authorization: preapproved | go`
- `plugin`: name, marketplace and pinned version of the process in force
- `deploy.action`: what makes a merged change live (publish package · schedule job · regenerate report · promote to paper trading · deploy service)
- `deploy.production`: true/false — turns on the release label and the production-gate hook
- `maintain.metric` and `maintain.source`: the watched metric and where the detection script reads it (default for every new project: CI test failure rate from the CI API)
- `maintain.runbooks`: each with `authorization: preapproved | go` — CI-scoped reversible actions are pre-approved; anything touching a running system waits for the owner's "Go" (as a parked item)

## 10. Adopted on 2026-09-23, not yet built (decisions 21–26, provisional until PR #22 merges)

| Decision | What changes in this model when it ships | Lands in |
|---|---|---|
| 21 Deferred review | `sdlc.yaml: review: deferred` (per-change override). Inside a phase, a judgment item from a fixed list (open flagged concern, contradicting policies, the adversarial reviewer's escalate verdict, undeterminable Important finding, verifier disagreement) goes to a review panel — reviewer and devil's advocate in blind fresh contexts, a conciliator that decides — and the run continues; every decision is a ledger line in `evidence/decisions-<phase>.md` and the PR summary opens with "Decisions taken for you (N)". The hard parks (risk-list hit, guardrail file change, run limit, infrastructure failure, merge to main, deploy) are unchanged; §6's "a confidence gate fails" then excludes the fixed-list items. The Lite profile is removed. | step 16a, B4 |
| 22 Fix trigger | The owner's "Request changes" review submission starts `sdlc-fix.yml` → `/sdlc-fix <id>`; `/sdlc-fix` covers gate (a). §5 then needs no owner-launched command. §4.1's "nothing in a run edits intent.md" and §8's "interactively" gain one exception: `/sdlc-fix` on the unmerged intent PR. | step 8, B4 |
| 23 GitHub only | `/sdlc-init` refuses a project whose origin is not GitHub; §1 "any project" reads "any GitHub-hosted project". | step 21, B4 |
| 24 Labels as un-park verbs | `sdlc:accept-risk`, `sdlc:reset-iterations`, `sdlc:unlock-tests` applied by the owner on the PR, recorded with the label's actor; the CLI commands of §6 and §8 stay for by-hand runs. | steps 9, 16, B4 |
| 25 Triage and abandon | Gate (f) is per-finding triage only (§4 row (f) is complete as written); closing a PR at (a)–(e) without merging sets `status.yaml: phase: abandoned` and every workflow skips the change. | steps 9, 39, B4 |
| 26 Rehearsed rollback | On `deploy.production: true`, a rollback runbook with `rehearsed_at` set by the owner is pre-approved; everything else that touches a running system keeps `authorization: go` (§9). Still no notification. | step 37, B5 |
