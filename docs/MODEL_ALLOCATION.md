# Model allocation for build sessions 3 and later

Purpose: the owner's Fable quota runs out faster than the Opus quota, and the build
sessions keep Fable as the session model. This file says, step by step for build stages
B3–B5 (sessions 3 and later, plus the unfinished rest of session 2), which tasks the Fable
main session should do itself and which it should hand to an Opus sub-agent. It does not
change any decision in `docs/DECISIONS.md`; it only says who does the work inside a session.

Model names: the current Opus generation available in Claude Code is Claude Opus 5 (alias
`opus`, API id `claude-opus-5`). There is no "Opus 5.1" in the model reference at the time of
writing (2026-09-21); where the owner says "Opus 5.1", read "the current Opus".

## 1. How the split works inside one session

- The session model stays Fable. Everything Fable reads (handoff, docs, sub-agent reports)
  and writes (prompts, decisions, reviews of reports) is charged to the Fable quota.
- Work handed to a sub-agent is served by the sub-agent's model. Verified against the
  Claude Code docs on 2026-09-21 (https://code.claude.com/docs/en/sub-agents,
  https://code.claude.com/docs/en/model-config, https://code.claude.com/docs/en/costs):
  - Resolution order for a sub-agent's model: "1. The per-invocation `model` parameter
    2. The subagent definition's `model` frontmatter, where `inherit` selects the main
    conversation's model 3. The `CLAUDE_CODE_SUBAGENT_MODEL` environment variable, when you
    set it to a model alias or model ID 4. The main conversation's model."
  - Frontmatter values: "`sonnet`, `opus`, `haiku`, `fable`, a full model ID such as
    `claude-opus-5`, or `inherit`". The Agent tool's per-invocation `model` parameter is
    "something Claude passes"; the docs give no user-facing way to set it per call, so the
    session prompt (the handoff) has to tell the model which sub-agents run on Opus.
  - Cheapest way to make Opus the default for every delegated task while the session stays
    on Fable: start the session with `CLAUDE_CODE_SUBAGENT_MODEL=opus` (or put it in the
    `env` block of the user's settings). Do not set `CLAUDE_CODE_SUBAGENT_MODEL_FORCE`: the
    docs say it "ignores the `model` field of every subagent definition", which would also
    override the plugin's own agents once they carry a `model:` line. The docs also state
    that the variable alone "doesn't change the model the built-in Explore and Plan
    subagents run on", so those two still follow the session model unless the invocation
    names one.
  - Check which model a sub-agent ran on with `/tasks` (v2.1.242 or later).
  - Usage: the docs describe both "a seat-based usage window on a subscription plan, shared
    across all models" and the model-specific "You've hit your Opus limit" window; `/usage`
    shows usage by model and an attribution breakdown for sub-agents. The docs never state
    in one sentence that a sub-agent's tokens count against its own model's window; it
    follows from usage being reported by model. Watch `/usage` after the first delegated
    session to confirm.
  - No documented way keeps a Fable main session and plans on Opus (`opusplan` swaps the
    whole session to Opus + Sonnet). The advisor tool is the documented "consult a second
    model mid-task" route; it is not used here.
- The saving comes from three things: (1) the sub-agent reads the files, not Fable — so a
  delegated task must include *reading* the step text, the article page and the code, not
  only writing; (2) the sub-agent returns a short report (what it changed, test output, open
  questions), never file contents; (3) sub-agents run in parallel, so independent Python
  modules land while Fable writes the prompts.
- What stays with Fable: choices the guide leaves open ("design yourself", "not shown in the
  article"), the model-facing prompt text of commands and agents (it is what every future run
  of the framework reads), the composition of phases (inputs, order, exit condition, profile
  branching), the trigger/dispatch design of the CI plumbing, anything that defines a
  guardrail's semantics, triage of review findings, and the handoff for the next session.
- What goes to Opus: Python from a written spec with tests (hooks, gate checks, detection
  statistics, evidence and PR-description writers, CI helper scripts), workflow YAML from a
  written trigger table, fixtures and tests, verification of platform facts against the
  Claude Code and GitHub docs (quote + URL into `docs/NOTES.md`), fresh-context reviews of
  the diff, and mechanical documentation (PROGRESS rows, README, NOTES entries).

Legend for the tables: **F** = Fable main session · **O** = Opus sub-agent · **F→O** = Fable
writes the spec (usually a few lines: file, function, inputs, outputs, tests to add), Opus
implements and tests, Fable reads the report · **O→F** = Opus produces a draft or a report,
Fable reviews it line by line before it is used.

## 2. Per-session rules (apply in every session from 3 on)

| Task in every session | Who | Notes |
|---|---|---|
| Preconditions (`python tasks.py check`, `claude plugin validate .`, PR merged state) | O | One sub-agent, report the counts. |
| Reading the contract (`OPERATING_MODEL.md`, `DECISIONS.md` for the steps of the session, the handoff) | F | Short files; Fable needs them in context to decide. |
| Reading `BUILD_GUIDE.md` step text and the cited article pages | O, per task | Put the step number and the page numbers in each sub-agent prompt; Fable reads only the implementation notes of the steps it designs itself. |
| Prompt text of commands, skills and agents | F | May start from an Opus draft (O→F) when the guide gives the wording, e.g. the p.14 design prompt. |
| Python modules and their tests | F→O | Spec = file, function names, inputs, outputs, error behaviour, the tests to add. |
| Workflow YAML | F→O | Spec = the trigger table (event, filter, guard, dispatch). |
| Docs facts (Claude Code docs, GitHub docs) | O | Report URL + quote; Fable decides the consequence. |
| Fresh-context reviews before the final commit (code review; compliance vs handoff + decisions) | O | Two separate sub-agents, each with the diff and the rules; Fable triages the findings and decides what to fix. |
| `docs/PROGRESS.md`, `docs/NOTES.md` additions, `README.md` | O→F | Opus drafts from the sub-agent reports; Fable writes the ≤5-bullet summary. |
| `HANDOFF.md` for the next session | F | It steers the next session; precision matters more than cost. |
| Commit, push, draft PR | O | Mechanical. |

## 3. Session 3 — build stage B3 (steps 22, 23, 24, 25, 26, 27, 27a, 28, 30)

Assumption: session 3 covers the whole of B3, as session 2 covers the whole of B2. If the
owner splits B3 in two, the rows split with it; the allocation per task does not change.

What already exists that B3 builds on (checked in the code on 2026-09-21): `plugin/gate/`
implements `check_artifacts`, `check_open_concerns` (step 23's "no open concern"),
`check_commands`, `check_evidence` (step 28's precondition), `check_findings` with the
findings JSON shape (`{"schema_version": 1, "head": ..., "findings": [{"pass": "bugs|security|compliance", ...}]}`,
step 26), `check_plan_sync`, `check_guardrails`, `check_risk_list`, `check_adversarial_verdict`
and `limits.check_limits`; `plugin/state/` owns `status.yaml` (with `change_type`) and the
branch/label names; the four agents carry `model: inherit`. Commands that exist:
`/sdlc-init`, `/sdlc-plan`. Not yet in the tree: `/sdlc-design`, the four phase runbooks,
`/sdlc-fix`, any hook beyond the four of step 15, any workflow, `evals/`, `bands.yaml`.

| Step · task | Who | What Fable must give the sub-agent, or why it stays with Fable |
|---|---|---|
| 22.1 Run the p.14 design prompt by hand on two or three real intents (the ladder's first rung) | O | One sub-agent per intent, Read/Grep/Glob plus Write limited to `changes/<id>/spec.md`; it reports the spec's section list and the flagged concerns. Fable reads the reports, not the specs, and decides what the command must say differently. |
| 22.2 `plugin/commands/sdlc-design.md`: spec pass with the policy skills loaded, mandatory "Flagged concerns" section, header with the prompt and the pinned plugin version, then the read-only plan run (plan-template skill), then one PR with spec+plan (Standard/Full) or commit on the change branch and hand over to the build job (Lite) | F | Prompt text plus the profile branching and the re-run-after-comments behaviour (step 8). Opus may draft the p.14 wording; Fable owns the final file. |
| 22.3 Deterministic support: spec.md section check (the gate's artifact templates already list the sections; confirm "Flagged concerns" is required), `state/cli.py commit-phase` for phase b, header rendering with the plugin version from `sdlc.yaml` | F→O | Spec: which sections, which CLI subcommand, what the header line looks like. Tests in `tests/test_gate.py` and `tests/test_state.py`. |
| 22.4 Static tests for the command file (sections, skill names, no bypass mode), like `tests/test_commands_and_skills.py` | O | No spec needed beyond "mirror the existing tests". |
| 23.1 PR-description checklist for gate (b) (problem solved? open questions carried forward? every concern closed? plan implementable by someone who never saw the conversation?) as a template rendered by the PR-description builder of 27a | O | The four items are quoted in the guide; mechanical. |
| 23.2 Convention for closing a concern (how a "Flagged concerns" item records the decision) so `check_open_concerns` can tell open from closed | F | One paragraph in the plan-template or intent-template skill and OPERATING_MODEL §8; Fable decides because every later spec is written against it. Opus then aligns `artifacts.open_concerns` and its tests (F→O). |
| 23.3 Lite profile: the design run calls the gate for (b) instead of opening a PR, using `conventions.is_human_gate` | F→O | Spec: the call in the command, the gate phase, the label to set. |
| 24.1 Phase composition — inputs, order, artifact, exit condition, profile branching, idempotence — for (c), (d), (e), (f) | F | The core of the step; the guide gives components, not the composition. Written once as a short table in OPERATING_MODEL or the command files. |
| 24.2 The four runbook prompts `sdlc-build.md`, `sdlc-test.md`, `sdlc-deploy.md`, `sdlc-maintain.md` (auto-accept under preflight, simplifier, verifier, PR description, gate call; fresh-context full run and evidence; review passes and fix loop and release preparation; one finding per maintain run) | F | Model-facing text that every future run reads. Opus may draft from the 24.1 table (O→F) if Fable reviews every line. |
| 24.3 Orchestrator glue in Python: phase transitions (`state/cli.py set-phase`, labels, evidence dir), the "refuse to enter (c) without the three commands" check left from step 14, and the calls into the existing `gate/cli.py` subcommands (`check`, `start-run`, `record-spend`, `set-iterations`) | F→O | Spec: subcommands, status.yaml fields touched, exit codes (the gate CLI already uses 0 continue / 3 wait / 4 park). Tests in `tests/test_state.py`, fixture run in `tests/test_integration_fixture.py`. |
| 24.4 Fixture states for the gate at (c), (d), (e) (continue and park cases) | O | Extend the existing fixture; the gate tests define the shape. |
| 25.1 Test-file lock semantics: when the lock is on (fix-type change, after the reproducing test is committed, for the rest of (c) and (d)), where the state lives (a `status.yaml` field set by the build run), what counts as a test path (a `sdlc.yaml` key with defaults per language) | F | Guardrail semantics; the article leaves the mechanism open. Three sentences in OPERATING_MODEL §8 and the sdlc.yaml comments. |
| 25.2 `plugin/hooks/test_file_lock.py` (PreToolUse on Edit/Write/MultiEdit/NotebookEdit, fail closed, exit 2 with the reason), registration in `hooks.json`, tests over stdin like `tests/test_hooks.py` | F→O | Spec from 25.1 plus the existing hook pattern in `_common.py`. |
| 25.3 Build-run wording for fix changes: write and commit the reproducing test first, confirm it fails for the expected reason; plan-template Proof names the test | F | Prompt text (part of 24.2 and the plan-template skill). |
| 25.4 REVIEW.md rule "reject any change that touches a test in a fix task" — confirm the template already carries it (session 1 says it does) and add a review-pass check for it | O | Mechanical; report what was found. |
| 26.1 Review-pass prompt for the CI `claude -p` job: the three passes from REVIEW.md, Important vs Nit rule, at most five nits, output = `evidence/review-findings.json` in the gate's shape plus a summary for the check run | F | Prompt text; the findings shape already exists. |
| 26.2 `plugin/review/` Python: validate the findings JSON, compute the severity tally, render the check-run summary and the PR-description block, post the check run through the GitHub REST API with `urllib` (no third-party dependency) | F→O | Spec: input file, outputs, the API call and its permissions (`checks: write`), error behaviour. Tests with fixture JSON. |
| 26.3 `/sdlc-fix` command: read unresolved review comments and failing checks (gh → GitHub MCP → API), re-run the phase with them as constraints, push to the same branch, babysit to green, propose the CLAUDE.md line on the second occurrence of a finding | F | Cross-phase mechanism with judgement (how a "second occurrence" is recognised, how the CLAUDE.md proposal rides in the PR given the protected-path hook — PROGRESS choice 7 says revisit here). |
| 26.4 Finding signatures: a deterministic `signature(finding)` and a per-project record of seen findings, so "second time" is computable | F→O | Fable fixes what a signature is made of (pass, rule, file, normalised message); Opus implements and tests. |
| 26.5 Monthly tuning as a scheduled agent PR (rate findings, cap nits) — workflow and prompt | O→F | Low priority in the guide; Opus drafts the workflow and prompt, Fable reviews the prompt only. |
| 27.1 Full profile at gate (c): the PR-description section (links to intent/spec/plan, plan-vs-diff note, verifier report, first-pass test output) and the wait for `sdlc:c-approved` | O | The content list is in the guide; the builder is 27a's. |
| 27a.1 PR-description builder `plugin/pr/description.py`: ≤5-bullet summary from status.yaml, evidence/, findings JSON, plan conformance, "What I need from you" when parked, the two counters of step 42 | F→O | Spec: the five bullets in order and their sources; deterministic and unit-tested. |
| 27a.2 Daily digest: Python that lists PRs by `sdlc:*-ready` and `sdlc:needs-human` (needs-human first) and posts one issue or PR comment; template workflow on a schedule | F→O | Spec: which labels, what the digest contains, where it is posted; `urllib` only. Fable notes that an issue comment may still trigger GitHub's own email to the owner (GitHub's setting, not the framework's), so the owner decides whether to unsubscribe from that issue. |
| 27a.3 Static tests: every command that opens or updates a PR uses the builder | O | Mechanical. |
| 28.1 Evidence writer `plugin/evidence/collect.py`: run the three `sdlc.yaml` commands and write the files `gate/artifacts.py` already requires (`test.log`, `build.log`, `lint.log`; the verifier agent writes `verifier.md`), plus a screenshots dir | F→O | Spec: the file names from `artifacts.py`, exit-code capture, timeouts; `check_evidence` is the consumer and already has tests. |
| 28.2 Check-run summary for phase (d) (same poster as 26.2) | O | Reuse. |
| 28.3 `/sdlc-test` prompt (fresh context, full suite, UI screenshot loop against the mock, verifier report) | F | Part of 24.2. |
| 30.1 Platform facts into `docs/NOTES.md` with URL and quote: `GITHUB_TOKEN` events not starting workflow runs and the `workflow_dispatch`/`repository_dispatch` exemption; `pull_request` `closed`+`merged` trigger for the owner's merges; label events; `permissions:` needed (`contents`, `pull-requests`, `checks`); `concurrency` per change id; how the pinned plugin is loaded with `--plugin-dir` in an untrusted checkout (NOTES §3); whether the API key or subscription auth is permitted in CI (decision 1, NOTES §2 says terms not checked); `--max-turns`, `--max-budget-usd`, `--permission-prompts none` (NOTES §10b already) | O | One research sub-agent, report only. |
| 30.2 Trigger and dispatch table: one workflow per transition (intent merged → design; spec+plan merged or design-job dispatch in Lite → build; build → test → review either directly or after `sdlc:c-approved`/`sdlc:d-approved`), the status.yaml guard, the change id carried in the dispatch payload, what runs under which token | F | The place where the token-event rule and the profiles meet; a wrong table silently stops the loop. |
| 30.3 `plugin/ci/run_phase.py`: composes and runs the `claude -p` call (pinned plugin via `--plugin-dir`, allow-list from step 7, `--max-turns`, `--max-budget-usd`, `--permission-mode acceptEdits` only when `preflight.py` allows, `--permission-prompts none`, `--output-format json`), stores the JSON transcript in `evidence/`, records spend, dispatches the next workflow | F→O | Spec = the 30.2 table plus NOTES §10b. Tested with a fake `claude` executable on PATH. |
| 30.4 `template/.github/workflows/*.yml` for each transition and the digest, all steps calling Python | F→O | Spec = 30.2; Opus writes YAML, and a test parses every workflow and asserts triggers, permissions and the guard step. |
| 30.5 The p.41 read-only "triage failed build" step as the first proof of the substrate | O | Copy from the article page, adapt to Python; the live run is the owner's. |
| 30.6 Re-verify decision 6 layer (iii): CI never loads hooks from the PR branch | O | Read the workflows and report; Fable decides if a change is needed. |
| B3 wrap-up: fresh-context code review and compliance review of the diff; PROGRESS/NOTES/README; handoff for session 4 | see §2 | Reviews and doc drafts on Opus; the handoff on Fable. |

## 4. Session 4 — build stage B4 (steps 29, 31, 32)

| Step · task | Who | What Fable must give the sub-agent, or why it stays with Fable |
|---|---|---|
| 29.1 What counts as release approval (a release label or a signed tag set by the owner), how the hook reads it instead of an environment variable, whether "ask" is used or only allow/block, which command patterns are guarded (from the project's `deploy.action` adapter), and the block text with the route to approval | F | The guide says "article gaps to design yourself"; it is the last guardrail before production. Written into OPERATING_MODEL §4/§9 and the sdlc.yaml comments. |
| 29.2 `plugin/hooks/production_gate.py` (PreToolUse on Bash and PowerShell, fail closed, exit 2 with the reason and the route), registration, tests over stdin, and the `deploy.production` switch that enables it | F→O | Spec from 29.1 plus the pattern of `plan_sync.py` (command parsing on Bash). |
| 29.3 Logging every allow/block decision with a timestamp (the article's governance line) into the CI artifact of step 41 | O | Mechanical, shared with 41.1. |
| 31.1 Whether deploy/status/rollback MCP tools are built at all now: the plugin ships no runtime dependency (decision 7), an MCP server needs one, and no project has a deploy target yet | F | A recorded choice in PROGRESS (not a reopened decision): most likely "document the interface, build when a project's adapter names a real deployment". |
| 31.2 If built: the per-environment MCP server skeleton and its allowlist, guarded by the production-gate hook; a rehearsed rollback command | F→O | Spec: the three tools, their arguments, the environment scoping. The rehearsal in staging is the owner's live check. |
| 32.1 `/sdlc-deploy` sequence (review passes → fix loop until green → release notes → release prepared per the adapter → stop) and the "waiting for your merge" PR state | F | Part of 24.2, finalised here with the release label of decision 13. |
| 32.2 Release-notes generator: commits since the base, links to intent/spec/plan, findings tally, evidence status | F→O | Spec: sources and format; deterministic and tested. |
| 32.3 Deploy workflow on merge of the build PR (plus the release label when `deploy.production` is true) running the adapter's action; environment protection where GitHub offers it | F→O | Spec = the trigger row for (e) in the 30.2 table plus the adapter values. |
| 32.4 Confirm the post-deploy safety net wiring points at step 37's bands and rollback route (no code yet) | O | Report only. |
| B4 wrap-up: reviews, docs, handoff for session 5 | see §2 | |

## 5. Session 5 — build stage B5 (steps 33–43)

Steps 33 (worktrees), 34 (design mock), 40 (chat entry) and 43 (reference) need no build
work now: decision 17 defers 33, 34 is a folder convention, 40 is optional, 43 is
documentation already in the guide. They appear below only where a small task exists.

| Step · task | Who | What Fable must give the sub-agent, or why it stays with Fable |
|---|---|---|
| 33 Worktrees: record "not built" in PROGRESS with the decision-17 reason | O | One line. If ever built: Fable designs the conflict escalation, Opus implements. |
| 34.1 `changes/<id>/mock/` convention in `changes/README.md` and the screenshot comparison instruction in the (c)/(d) prompts | O for the README, F for the prompt line | Small. |
| 35.1 Eval JSON shape (prompt, setup, checks a deterministic script can assert: file exists, command exits 0, output contains) and what "gate configuration changes on the results" means for the plugin repo | F | Design; the article shows neither `evals/check.sh` nor the JSON. Also decide whether Claude Code's own `claude plugin eval` fits after 35.2's report. |
| 35.2 Research: what `claude plugin eval` offers (suite format, JSON report, CI use) and the `claude -p ... --output-format json` invocation the p.30 workflow uses | O | Report with URLs and quotes into NOTES. |
| 35.3 `plugin/evals/run.py` (runs each eval non-interactively, applies the checks, exits non-zero on regression) and `evals/check.py` in the template; the framework-level suite in this repo triggered on PRs to `plugin/**`; the per-project template workflow (on PR to `CLAUDE.md`, `.claude/**` and nightly) | F→O | Spec from 35.1 and 35.2. Tested with a fake `claude` executable. |
| 35.4 First eval cases for the framework suite (intent skill triggers, protected path denied, gate parks on a failing test) | O→F | Opus writes them from the live checks already recorded in PROGRESS; Fable checks each one asserts a real property. |
| 36.1 `template/lessons/` with a README and a file naming rule; `changes/README.md` cross-reference | O | Mechanical. |
| 36.2 The diagnose run's instruction to read `lessons/` first and append the post-mortem when a fix ships (in the maintain prompt) | F | Prompt text (part of 24.2/37.5). |
| 37.1 `plugin/detect/` detection statistics: rolling window mean and standard deviation, Western Electric rules, tier evaluation against `bands.yaml`; pure functions, unit-tested with synthetic series, no model | F→O | The best Opus candidate in the whole guide: fully specified by p.43–44 and decision 15. Spec: input series shape, window, the rules to implement, output (tier, rule hit, values). |
| 37.2 Metric source for CI test failure rate: GitHub Actions runs API through `urllib`, cached to a file; the adapter's `maintain.source` for other metrics later | F→O | Spec: which endpoint, which runs count as a failure, the window. |
| 37.3 `template/bands.yaml` (p.44 shape) with the per-route `authorization: preapproved | go` split of decision 14, and the scheduled detection workflow | O | Copy p.44, add the two keys; step 21 may already have created the file — reuse. |
| 37.4 Tier actions: 1σ log; 2σ dispatch the read-only diagnose run; 3σ open the intent PR through gate (e) or run a pre-approved runbook, park with "Go" requested for `authorization: go` routes | F→O | Fable writes the routing rules and the two default runbooks (quarantine a flaky test in the project's suite, open a revert PR) including the guard that a runbook never edits a test in this repo; Opus implements the dispatcher and tests. |
| 37.5 The diagnose prompt: read-only tools, reads `lessons/`, writes the diagnosis as an intent.md in the intent-template shape with the Evidence section, labels the PR `incident` | F | Prompt text. |
| 37.6 Gate checks for phase (f): `CHECKS_BY_PHASE["f"]` is empty today; decide which checks apply to a maintain run (artifacts of the incident intent, guardrails, risk list, the route's authorization) | F for the list, O for the code and tests | The list is a gate semantics choice; the checks themselves exist. |
| 38.1 Weekly security review: which skill runs it (the plugin's `security-baseline` skill, Claude Code's `security-review`, or both), read-only, and the "bounded finding → PR through the review gate; wider → intent.md; fixed class → eval" criterion | F | Judgement on routing; decision 16 fixes the shape only. |
| 38.2 Workflow, findings-to-route Python, dismissal store (signature + reason) that suppresses a repeated finding, tests | F→O | Spec from 38.1; reuse the signature function of 26.4. |
| 39.1 Gate (f) mechanics: `incident` label on intent PRs, "schedule" label, close-with-reason recorded as a dismissal, a bands change always through a `bands.yaml` PR | F | Small design; the article's "dismissals tune the bands" is not automatic. |
| 39.2 Workflow on a closed-unmerged incident PR that reads the closing comment and appends the signature to the dismissal store in a PR | F→O | Spec from 39.1. |
| 41.1 Keep each headless run's JSON transcript and the gate verdicts in `evidence/`; hooks append one line per decision (allow/block, timestamp, tool, path) to a log file whose path comes from an environment variable; upload it as a CI artifact | F→O | Spec: the log line format and the variable name; touches every hook, so the tests in `tests/test_hooks.py` grow. |
| 42.1 The two counters (first-pass merge yes/no, fix iterations from `status.iterations`) in the PR description | O | Part of 27a.1 if not already there. |
| 42.2 The later scheduled report over `changes/*/` and PR history | O→F | Optional; Opus drafts, Fable decides whether to ship it. |
| B5 wrap-up: reviews, docs, final handoff | see §2 | |

## 6. Rest of session 2 (steps 18–21, not yet merged)

Steps 16 and 17 are merged; 18–21 are not. Same rules as above.

| Step · task | Who | Notes |
|---|---|---|
| 18 `plugin/gate/preflight.py` (CLAUDE.md with the three commands, policy skills present, `hooks.json` reachable and `python` on PATH, test target green) and its tests | F→O | Fully specified in HANDOFF.md deliverable 4. |
| 18 The routine/non-routine tightening (already in `limits.classification_for` and `iteration_cap`) — confirm and document | O | Report. |
| 19 Run limits: `limits.py`, the `gate:` block and `paused: false` in `template/sdlc.yaml`, and `gate/cli.py record-spend` already exist; confirm against HANDOFF.md deliverable 3 and document the pause mechanism in NOTES/PROGRESS | O | Report what is missing, then implement any gap from the handoff text. |
| 20 Five policy skills: frontmatter descriptions in the style that passed the live trigger check, body naming the source, deterministic script call at the end | F for the descriptions and the rules that a hook must back; O→F for the bodies | The trigger description is what the model matches on; the rules are policy. Opus drafts each body from the article pages named in the handoff; Fable edits. |
| 21 Full `/sdlc-init`: `template/evals/` with README, `template/bands.yaml`, Node detection in `detect.py`, idempotence tests | F→O | HANDOFF.md deliverable 6 is the spec. |
| Session 2 wrap-up | see §2 | |

## 7. Runtime model choice (not a build-session question, recorded for completeness)

The framework's own runs are a different budget from the build sessions:
- From B3 the phase jobs run in CI with an API key (decision 1), billed per token in
  dollars, not against either plan window. The model each job uses is a `--model` flag in
  `plugin/ci/run_phase.py`; the natural default is `opus` for every phase, with `fable`
  reserved for the read-only planning run and the adversarial reviewer if the owner wants
  it. This choice is not made here.
- Until then, and for the manual runs of B3's first rung, the phase commands run in the
  owner's own session and share its model. The four plugin agents say `model: inherit`. Pinning
  `model: opus` on `verifier`, `code-simplifier` and `researcher` would move those runs off the
  Fable window in every project session; the adversarial reviewer is the one to keep on
  `inherit`. That is a one-line change per agent file plus the static test in
  `tests/test_agents.py`, and it is a framework change to record in PROGRESS, not a build-session
  rule — so it is listed here and not applied.
