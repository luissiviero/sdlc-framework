# Model allocation for build sessions 3 and later

Purpose: the owner's Fable quota runs out faster than the Opus quota, and the build
sessions keep Fable as the session model. This file says, step by step for build stages
B3–B5 (sessions 3 and later), which tasks the Fable
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
  - Resolution order for a sub-agent's model (Claude Code v2.1.251 or later; before that
    the environment variable came first): "1. The per-invocation `model` parameter
    2. The subagent definition's `model` frontmatter, where `inherit` selects the main
    conversation's model 3. The `CLAUDE_CODE_SUBAGENT_MODEL` environment variable, when you
    set it to a model alias or model ID 4. The main conversation's model."
  - Frontmatter accepts an alias (`sonnet`, `opus`, `haiku`, `fable`), a full model id such
    as `claude-opus-5`, or `inherit`. Per invocation: "When Claude invokes a subagent, it
    can also pass a `model` parameter for that specific invocation." The docs give no
    user-facing way to set it per call, so the session prompt (the handoff) has to tell the
    model which sub-agents run on Opus, and the model names it in each invocation.
  - Default for every delegated task while the session stays on Fable: start the session
    with `CLAUDE_CODE_SUBAGENT_MODEL=opus`. Where it goes depends on the surface: a cloud
    session "copies the environment's values once, at startup" from the cloud environment's
    environment variables and never reads `~/.claude/settings.json` ("User and project local
    settings ... not read"); on the PC the `env` block of `~/.claude/settings.json` applies
    "for every session and its subprocesses". A repo's `.claude/settings.json` `env` block is
    read in a single-repository cloud session, but this is the owner's quota policy, so it is
    not committed. Never in the template. Two limits, both from the docs: the variable alone
    "doesn't change the model the built-in Explore and Plan subagents run on" (the built-in
    general-purpose sub-agent does honour it, and on the Claude API Explore under a Fable
    session is already "capped at Opus"), and a definition's `model` field, "including
    `inherit`", outranks it. The four
    plugin agents already say `model: inherit`, so in a session that loads the plugin
    (`--plugin-dir`, or a project session) they would still run on Fable. Since PR #21
    (2026-09-22, the framework's own `/sdlc-init` on this repository) this repo has a
    `.claude/settings.json` that declares the plugin, so build sessions here do load it;
    that changes nothing for the model rule as long as delegated work uses the built-in
    general-purpose sub-agent with `opus` named per invocation and never the plugin's
    `adversarial-reviewer`, whose `model: inherit` would run on Fable. `CLAUDE_CODE_SUBAGENT_MODEL_FORCE=1` (v2.1.257 or later) is the documented
    way to override every definition, plugin agents included; it also stops Claude passing
    a model per invocation, so use it only in a session where every sub-agent should be
    Opus, and never commit it.
  - Check which model a sub-agent ran on with `/tasks` (v2.1.242 or later): "Claude Code
    names the model on the subagent's row". This is the authoritative check, and only the
    owner can run it in the session UI. Because the per-invocation model is first in the
    order, naming `opus` per invocation also covers the built-in Explore and Plan
    sub-agents, which the variable alone does not move; only a forked sub-agent always
    inherits the session model.
  - Usage: the docs describe both "a seat-based usage window on a subscription plan, shared
    across all models" and the model-specific "You've hit your Opus limit" window; `/usage`
    shows usage by model and an attribution breakdown for sub-agents. The docs never state
    in one sentence that a sub-agent's tokens count against its own model's window; it
    follows from usage being reported by model. Its figures are "computed from local session
    history on this machine" and the docs say nothing about what it shows in a cloud
    session (re-verified 2026-09-21), so read `/usage` on the PC. Check it after the first delegated
    session; if the Fable window moved by the delegated share, stop delegating for
    quota reasons and rely on the CI route of §7 once B3 has built it (on the key it is
    outside every plan window).
  - No documented way keeps a Fable main session and plans on Opus without also forcing
    every other sub-agent (`opusplan` swaps the whole session to Opus + Sonnet; the built-in
    Plan sub-agent moves only under `CLAUDE_CODE_SUBAGENT_MODEL` plus `_FORCE`). The advisor tool is the documented "consult a second
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
Fable reviews it line by line before it is used · **F+O** = the row names which part is
which.

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
| Fresh-context reviews before the final commit (code review; compliance vs handoff + decisions) | O | Two separate general-purpose sub-agents with `opus` named in the invocation (not the plugin's `adversarial-reviewer`, whose `model: inherit` would run on Fable), each with the diff and the rules; Fable triages the findings and decides what to fix. |
| `docs/PROGRESS.md`, `docs/NOTES.md` additions, `README.md` | O→F | Opus drafts from the sub-agent reports; Fable writes the ≤5-bullet summary. |
| `HANDOFF.md` for the next session | F | It steers the next session; precision matters more than cost. |
| Final `python tasks.py check` (pytest + ruff) with the output pasted into the report, as CLAUDE.md requires | O | Runs after the review fixes; a failure goes back to the F→O row that caused it. |
| Commit, push, draft PR | O | Mechanical. |

## 3. Session 3 — build stage B3 (steps 22, 23, 24, 25, 26, 27, 27a, 28, 30)

Assumption: session 3 covers the whole of B3, as session 2 covers the whole of B2. If the
owner splits B3 in two, the rows split with it; the allocation per task does not change.

What already exists that B3 builds on (checked against `main` after session 2's last PR, #7,
and PR #8, on 2026-09-21): `plugin/gate/` implements `check_artifacts`, `check_open_concerns`
(step 23's "no open concern"; PROGRESS choice 14: a concern is open unless its item starts
with `[x]`, `closed`, `resolved` or `decided`), `check_commands`, `check_evidence` (step 28's
precondition), `check_findings` with the findings JSON of PROGRESS choice 7
(`findings[].severity important|nit`, `tally`, `head`), `check_plan_sync`, `check_guardrails`,
`check_risk_list`, `check_adversarial_verdict` and `limits.check_limits`; `preflight.py`
(step 18) and `policy.py`; `plugin/state/` owns `status.yaml` (with `change_type`) and the
branch/label names; the four agents carry `model: inherit`; the five policy skills ship with
a `check.py` each; `/sdlc-init` writes `evals/` and `bands.yaml` and detects Node. Commands
that exist: `/sdlc-init`, `/sdlc-plan`. Not yet in the tree: `/sdlc-design`, the phase
runbooks, `/sdlc-fix`, any hook beyond the four of step 15, any phase workflow in
`template/` (the dispatch-only smoke workflow exists in this repo), the digest.
The session-3 `HANDOFF.md` lists the same work as seven deliverables; the rows below map to
them as: deliverable 1 = 22.x and 23.x, 2 = 24.x and 28.x, 3 = 25.x, 4 = 26.x, 5 = 27.x and
27a.x, 6 = 30.x, 7 = §2.

| Step · task | Who | What Fable must give the sub-agent, or why it stays with Fable |
|---|---|---|
| 22.1 Run the p.14 design prompt by hand on two or three real intents (the ladder's first rung) | O | One sub-agent per intent, Read/Grep/Glob plus Write limited to `changes/<id>-<slug>/spec.md`; it reports the spec's section list and the flagged concerns. Writing `spec.md` is allowed because OPERATING_MODEL §8 makes phase (c) the first run with edit tools *on source*; `changes/**` is not source. Fable reads the reports, not the specs, and decides what the command must say differently. |
| 22.2 `plugin/commands/sdlc-design.md`: spec pass with the policy skills loaded, mandatory "Flagged concerns" section, header with the prompt and the pinned plugin version, then the read-only plan run (plan-template skill), then one PR with spec+plan (Standard/Full) or commit on the change branch and hand over to the build job (Lite) | F | Prompt text plus the profile branching and the re-run-after-comments behaviour (step 8). Opus may draft the p.14 wording; Fable owns the final file. |
| 22.2a `plugin/skills/spec-template/SKILL.md`: the spec.md shape from `gate/artifacts.py` (the handoff says to write it from those names and invent none), the closed-concern wording of PROGRESS choice 14, and the header line | F | Skill text the design run reads on every change; short. |
| 22.3 Deterministic support: spec.md section check (`gate/artifacts.py` already lists the spec sections including "Flagged concerns"; confirm the check is wired for (b)) and header rendering with the prompt text that produced the spec and the pinned plugin version from `sdlc.yaml` (p.14: the spec, the prompt and the skill versions in force are all logged); `state/cli.py commit-phase` already accepts phase `b` and needs no code | F→O | Spec: which sections, what the header line looks like. Tests in `tests/test_gate.py` and `tests/test_state.py`. |
| 22.4 Static tests for the command file (sections, skill names, no bypass mode), like `tests/test_commands_and_skills.py` | O | No spec needed beyond "mirror the existing tests". |
| 23.1 PR-description checklist for gate (b) (problem solved? open questions answered or carried forward? every concern closed? plan implementable by someone who never saw the conversation?) as a template rendered by the PR-description builder of 27a | O | The four items are quoted in the guide; mechanical. Depends on 27a.1 — do it in the same sub-agent task or after it. |
| 23.2 Closing a concern: the first route (edit the item so it starts with `[x]`, `closed`, `resolved` or `decided`) is decided and implemented (PROGRESS choice 14); what is left is the second route the guide names — a review comment that `/sdlc-fix` consumes and turns into that edit — as one rule in the `/sdlc-fix` prompt (26.3) | F | Prompt text; no new gate code. |
| 23.3 Lite profile: the design run calls the gate for (b) instead of opening a PR, using `conventions.is_human_gate` | F→O | Spec: the call in the command, the gate phase, the label to set. |
| 24.1 Phase composition — inputs, order, artifact, exit condition, profile branching, idempotence — for (c), (d), (e), (f) | F | The core of the step. The article gives components only; the guide's implementation notes for step 24 give the composition per phase, which is the starting point. What they leave open — idempotence, re-run after review comments, the exact exit condition of each run, and where the gate (c) wait of the Full profile sits — is Fable's. Written once as a short table in OPERATING_MODEL or the command files. |
| 24.2 The runbook prompts `sdlc-build.md`, `sdlc-test.md`, `sdlc-deploy.md` (and `sdlc-maintain.md`, whose composition is written here but whose file waits for session 5's step 37) (auto-accept under preflight, simplifier, verifier, PR description, gate call; fresh-context full run and evidence; review passes and fix loop and release preparation; one finding per maintain run) | F | Model-facing text that every future run reads. Opus may draft from the 24.1 table (O→F) if Fable reviews every line. |
| 24.3 Orchestrator glue in Python: phase transitions (`state/cli.py set-phase`, labels, evidence dir), the "refuse to enter (c) without the three commands" check left from step 14, the calls into the existing `gate/cli.py` subcommands (`check`, `start-run`, `record-spend`, `set-iterations`), and applying the `sdlc:*-ready` / `sdlc:needs-human` labels the gate prints but nothing applies yet (PROGRESS known gap) | F→O | Spec: subcommands, status.yaml fields touched, exit codes (the gate CLI already uses 0 continue / 3 wait / 4 park). Tests in `tests/test_state.py`, fixture run in `tests/test_integration_fixture.py`. |
| 24.4 Fixture states for the gate at (c), (d), (e) (continue and park cases) | O | Extend the existing fixture; the gate tests define the shape. |
| 24.5 Owner-only state: `accept-risk` and `set-iterations` are owner actions by convention only (PROGRESS known gap); decide whether they are tied to the commit author (owner ≠ automation identity) or moved to a PR label | F for the choice, F→O for the check and its tests | A guardrail-semantics choice the handoff carries into B3. |
| 25.1 Test-file lock semantics: when the lock is on (fix-type change, after the reproducing test is committed, for the rest of (c) and (d)), where the state lives (a `status.yaml` field set by the build run), what counts as a test path (a `sdlc.yaml` key with defaults per language) | F | Guardrail semantics; the article leaves the mechanism open. Three sentences in OPERATING_MODEL §8 and the sdlc.yaml comments. |
| 25.2 `plugin/hooks/test_file_lock.py` (PreToolUse on Edit/Write/MultiEdit/NotebookEdit, fail closed, exit 2 with the reason), registration in `hooks.json`, tests over stdin like `tests/test_hooks.py` | F→O | Spec from 25.1 plus the existing hook pattern in `_common.py`. |
| 25.3 Build-run wording for fix changes: write and commit the reproducing test first, confirm it fails for the expected reason; plan-template Proof names the test | F | Prompt text (part of 24.2 and the plan-template skill). |
| 25.4 REVIEW.md rule "reject any change that touches a test in a fix task" — confirm the template already carries it (session 1 says it does) and add a review-pass check for it | O | Mechanical; report what was found. |
| 26.1 Review-pass prompt for the CI `claude -p` job: the three passes from REVIEW.md, Important vs Nit rule, at most five nits, output = `evidence/review-findings.json` in the gate's shape plus a summary for the check run | F | Prompt text; the findings shape already exists. |
| 26.2 `plugin/review/` Python: validate the findings JSON, compute the severity tally, render the check-run summary and the PR-description block, post the check run through the GitHub REST API with `urllib` (no third-party dependency) | F→O | Spec: input file, outputs, the API call and its permissions (`checks: write`), error behaviour. Tests with fixture JSON. |
| 26.3 `/sdlc-fix` command: read unresolved review comments and failing checks (gh → GitHub MCP → API), re-run the phase with them as constraints, push to the same branch, babysit to green, propose the CLAUDE.md line on the second occurrence of a finding | F | Cross-phase mechanism with judgement (how a "second occurrence" is recognised, how the CLAUDE.md proposal rides in the PR given the protected-path hook — `template/REVIEW.md` records the current rule: the hook always denies, the review proposes the line, the owner applies it). |
| 26.4 Finding signatures: a deterministic `signature(finding)` and a per-project record of seen findings, so "second time" is computable | F→O | Fable fixes what a signature is made of (pass, rule, file, normalised message); Opus implements and tests. |
| 26.5 Monthly tuning as a scheduled agent PR (rate findings, cap nits) — workflow and prompt | F for the prompt (Opus may draft, O→F), F→O for the workflow | Low priority in the guide; same rule as every prompt-text row. |
| 27.1 Full profile at gate (c): the PR-description section (links to intent/spec/plan, plan-vs-diff note, verifier report, first-pass test output) | O | The content list is in the guide; the builder is 27a's. The wait for `sdlc:c-approved` is phase composition and belongs to 24.1 (F) and the trigger table of 30.2. |
| 27a.0 Digest delivery medium that satisfies decision 20's "nothing pushes": GitHub auto-subscribes the owner to their own repository, so every PR the framework opens and every issue comment it posts reaches the owner's inbox by default — the digest is not special. Fable chooses the medium (one long-lived digest issue the owner can unsubscribe from, a committed digest file, or the daily PR comment) and writes the owner's repository watch setting into OPERATING_MODEL §7 / `docs/owner-machine/README.md` | F | A guardrail-semantics choice, not a footnote on an implementation row. |
| 27a.1 PR-description builder `plugin/pr/description.py`: ≤5-bullet summary from status.yaml, evidence/, findings JSON, plan conformance, "What I need from you" when parked (read from `evidence/gate-<phase>.json`, which `GateResult.what_i_need()` already renders — do not re-derive it), the two counters of step 42 | F→O | Spec: the five bullets in order and their sources; deterministic and unit-tested. |
| 27a.2 Daily digest: Python that lists PRs by `sdlc:*-ready` and `sdlc:needs-human` (needs-human first) and posts one issue or PR comment; template workflow on a schedule | F→O | Spec: which labels, what the digest contains, the medium from 27a.0; `urllib` only. |
| 27a.3 Static tests: every command that opens or updates a PR uses the builder | O | Mechanical. |
| 28.1 Evidence writer `plugin/evidence/collect.py`: run the three `sdlc.yaml` commands and write the files `gate/artifacts.py` already requires (`test.log`, `build.log`, `lint.log`; the verifier agent writes `verifier.md`), plus a screenshots dir | F→O | Spec: the file names from `artifacts.py`, exit-code capture, timeouts; `check_evidence` is the consumer and already has tests. |
| 28.2 Check-run summary for phase (d) (same poster as 26.2) | O | Reuse. |
| 28.3 `/sdlc-test` prompt (fresh context, full suite, UI screenshot loop against the mock, verifier report) | F | Part of 24.2. |
| 28.4 Full profile at gate (d): the wait for `sdlc:d-approved` and what the PR description shows as new versus (c) (the full-suite, fresh-context run and its evidence) | F for the wait (24.1 / 30.2), O for the description section (27a.1) | Mirror of 27.1. |
| 30.1 Platform facts into `docs/NOTES.md` with URL and quote: `GITHUB_TOKEN` events not starting workflow runs and the `workflow_dispatch`/`repository_dispatch` exemption; `pull_request` `closed`+`merged` trigger for the owner's merges; label events; `permissions:` needed (`contents`, `pull-requests`, `checks`); `concurrency` per change id; how the pinned plugin is loaded with `--plugin-dir` in an untrusted checkout (NOTES §3); the credential selection is decided (both secrets, key preferred, NOTES §2); `--max-turns`, `--max-budget-usd`, `--permission-prompts none` (NOTES §10b already) | O | One research sub-agent, report only. |
| 30.2 Trigger and dispatch table: one workflow per transition (intent merged → design; spec+plan merged or design-job dispatch in Lite → build; build → test → review either directly or after `sdlc:c-approved`/`sdlc:d-approved`), the status.yaml guard, the change id carried in the dispatch payload, what runs under which token | F | The place where the token-event rule and the profiles meet; a wrong table silently stops the loop. |
| 30.3 `plugin/ci/run_phase.py`: composes and runs the `claude -p` call (pinned plugin via `--plugin-dir`, allow-list from step 7, `--max-turns`, `--max-budget-usd`, `--permission-mode acceptEdits` only when `preflight.py` allows, `--permission-prompts none`, `--output-format json`), stores the JSON transcript in `evidence/`, records spend, dispatches the next workflow | F→O | Spec = the 30.2 table plus NOTES §10b. Tested with a fake `claude` executable on PATH. |
| 30.4 `template/.github/workflows/*.yml` for each transition and the digest, all steps calling Python | F→O | Spec = 30.2; the first workflow also creates the `sdlc:*` labels (handoff deliverable 6); Opus writes YAML, and a test parses every workflow and asserts triggers, the `permissions:` block, `concurrency` per change id, the status.yaml guard step, no deploy secrets, and the sandbox settings of 30.7. |
| 30.5 The p.41 read-only "triage failed build" step as the first proof of the substrate | O | `.github/workflows/substrate-smoke.yml` with `.github/scripts/substrate_smoke.py` (dispatch only, one headless turn, either secret) already exists in this repo as the credential proof; `plugin/ci/run_phase.py` reuses its credential selection, and the p.41 triage step extends it in Python. The live run is the owner's. |
| 30.6 Re-verify decision 6 layer (iii): CI never loads hooks from the PR branch | O | Read the workflows and report; Fable decides if a change is needed. |
| 30.7 Sandboxing of the phase jobs (p.40: containers under a network policy, short-lived scoped tokens, no production credentials by default): what the GitHub-hosted runner gives, the `permissions:` block per job, no deploy secrets in B3 workflows, the network limits Claude Code's own sandbox setting adds (NOTES §5) | F for the policy, F→O for the YAML | The policy is a guardrail choice; the YAML follows from it and from 30.1's facts. |
| 30.8 `/sdlc-init` installs `template/.github/workflows/` (phase transitions and the digest job) into the project, idempotent, with tests in `tests/test_init.py` — step 21's text and the session-2 handoff both leave this to B3 | F→O | Spec: which files, merge behaviour when a workflow already exists. |
| B3 wrap-up: fresh-context code review and compliance review of the diff; PROGRESS/NOTES/README; handoff for session 4 | see §2 | Reviews and doc drafts on Opus; the handoff on Fable. |

## 4. Session 4 — build stage B4 (steps 29, 31, 32)

| Step · task | Who | What Fable must give the sub-agent, or why it stays with Fable |
|---|---|---|
| 29.1 What counts as release approval (a release label or a signed tag set by the owner — outcome: the label only, PROGRESS choice 31), how the hook reads it instead of an environment variable, whether "ask" is used or only allow/block, which command patterns are guarded (from the project's `deploy.action` adapter), and the block text with the route to approval | F | The guide says "article gaps to design yourself"; it is the last guardrail before production. Written into OPERATING_MODEL §4/§9 and the sdlc.yaml comments. |
| 29.2 `plugin/hooks/production_gate.py` (PreToolUse on Bash and PowerShell, fail closed, exit 2 with the reason and the route), registration, tests over stdin, and the `deploy.production` switch that enables it | F→O | Spec from 29.1 plus the pattern of `plan_sync.py` (command parsing on Bash). |
| 29.3 Logging every allow/block decision with a timestamp (the article's governance line): the log line format and the environment variable naming the file are fixed in 29.1, the production-gate hook writes it first, and 41.1 extends the same format to the other hooks | F→O | The format is decided once, here; the code is mechanical. |
| 31.1 Whether deploy/status/rollback MCP tools are built at all now: the plugin ships no runtime dependency (decision 7), an MCP server needs one, and no project has a deploy target yet | F | A recorded choice in PROGRESS (not a reopened decision): most likely "document the interface, build when a project's adapter names a real deployment". |
| 31.2 If built: the per-environment MCP server skeleton and its allowlist, guarded by the production-gate hook; a rehearsed rollback command | F→O | Spec: the three tools, their arguments, the environment scoping. The rehearsal in staging is the owner's live check. |
| 32.1 `/sdlc-deploy` sequence (review passes → fix loop until green → release notes → release prepared per the adapter → stop) and the "waiting for your merge" PR state | F | Part of 24.2, finalised here with the release label of decision 13. |
| 32.2 Release-notes generator: commits since the base, links to intent/spec/plan, findings tally, evidence status | F→O | Spec: sources and format; deterministic and tested. |
| 32.3 Deploy workflow on merge of the build PR (plus the release label when `deploy.production` is true) running the adapter's action; environment protection where GitHub offers it | F→O | Spec = the trigger row for (e) in the 30.2 table plus the adapter values. |
| 32.4 Confirm the post-deploy safety net wiring points at step 37's bands and rollback route (no code yet) | O | Report only. |
| 31.3 DORA measures: no build work — the guide says they come from the CI system and the deployment tooling already (p.41) | — | Record as such in PROGRESS. |
| 32.0 The owner's merge counts as gate (e) passed without a write to `main` (`read_status(..., on_default_branch=True)` derives it) | F for the route, F→O for the code | The route (derive on read, or reach `main` through a PR) is a state-model choice; the code and tests are mechanical. |
| Deliverable 4 (carried live-check gaps): the merge-triggered workflows find the change from the merged PR's files (`run_phase.py --find-change`), `commit-phase` stages only changed paths, checkout/setup-node v5 | F→O | Spec: the resolution order (`--id`, head ref, PR files), the find step before the installs, the `git status --porcelain -z` staging; three Opus agents with disjoint file sets (CI runner and workflows; state and gate; hook and release package), a fourth for the commands and the PR summary. |
| Deliverable 6(a)(d)(e): `_start_point` Lite-only; `guardrails` and `risk_list` judge merge base…HEAD; the adversarial reviewer without `Bash` (the run writes `evidence/diff-<phase>.patch` and passes HEAD's sha) | F for the reviewer's tool route (verified against the sub-agents docs, NOTES §11c), F→O for the code | Spec per gap; the reviewer prompt is rewritten by Opus from the docs fact and reviewed by Fable. |
| Deliverable 5 (decisions 22, 24, 25, 23, 21, in that order) and 6(b)(f): the fix trigger and `/sdlc-fix` at gate (a); the un-park labels with the actor recorded; abandon; the GitHub-only init check; deferred review and the Lite removal | F for every prompt, gate rule and OPERATING_MODEL sentence; F→O for the Python halves and the workflow YAML; O for the fresh-context reviews | Same pattern as deliverable 4: one Opus agent per disjoint file set from a written spec, Fable reviews every report before anything is committed; the panel's model-driven half is a prompt exercised by the fake `claude` in the end-to-end test. |
| B4 wrap-up: reviews, docs, handoff for session 5 | see §2 | Done 2026-09-24: session 4 ended with plugin 0.2.18 (PRs A–J), the live-check results (1–15, 8 still owed) in PROGRESS and `HANDOFF.md` rewritten for session 5. |

## 5. Session 5 — build stage B5 (steps 33–43)

Steps 33 (worktrees), 34 (design mock), 40 (chat entry) and 43 (reference) need no build
work now: decision 17 defers 33, 34 is a folder convention, 40 is optional, 43 is
documentation already in the guide. They appear below only where a small task exists.

| Step · task | Who | What Fable must give the sub-agent, or why it stays with Fable |
|---|---|---|
| 33 Worktrees: record "not built" in PROGRESS with the decision-17 reason | O | One line. If ever built: Fable designs the conflict escalation, Opus implements. |
| 34.1 `changes/<id>-<slug>/mock/` convention in `changes/README.md` and the screenshot comparison instruction in the (c)/(d) prompts | O for the README, F for the prompt line | Small. |
| 35.1 Eval JSON shape (prompt, setup, checks a deterministic script can assert: file exists, command exits 0, output contains) and what "gate configuration changes on the results" means for the plugin repo | F | Design; the article shows neither `evals/check.sh` nor the JSON. Also decide whether Claude Code's own `claude plugin eval` fits after 35.2's report. |
| 35.2 Research: what `claude plugin eval` offers (suite format, JSON report, CI use) and the `claude -p ... --output-format json` invocation the p.30 workflow uses | O | Report with URLs and quotes into NOTES. |
| 35.3 `plugin/evals/run.py` (runs each eval non-interactively, applies the checks, exits non-zero on regression) and `evals/check.py` in the template; the framework-level suite in this repo triggered on PRs to `plugin/**`; the per-project template workflow (on PR to `CLAUDE.md`, `.claude/**` and nightly) | F→O | Spec from 35.1 and 35.2. Tested with a fake `claude` executable. |
| 35.4 First eval cases for the framework suite (intent skill triggers, protected path denied, gate parks on a failing test) | O→F | Opus writes them from the live checks recorded in PROGRESS (`tasks.py check`, protected path denied, intent-skill trigger, `/sdlc-plan` end to end) and from the fixture park cases of the session-2 handoff (`SAMPLE_FAIL=1`, a diff touching `.claude/settings.json`, a risk-list word); Fable checks each one asserts a real property. |
| 36.1 `template/lessons/` with a README and a file naming rule; `changes/README.md` cross-reference | O | Mechanical. |
| 36.2 The diagnose run's instruction to read `lessons/` first and append the post-mortem when a fix ships (in the maintain prompt) | F | Prompt text (part of 24.2/37.5). |
| 36.3 Incident → eval (p.44 step 7, step 35's note): when a fix for an incident intent ships, the fix PR adds one eval case to the project's `evals/` | F for the instruction in the fix/maintain prompt, O for the eval-case skeleton | Pairs with 38.1's vulnerability-class → eval rule. |
| 37.1 `plugin/detect/` detection statistics: rolling window mean and standard deviation, Western Electric rules, tier evaluation against `bands.yaml`; pure functions, unit-tested with synthetic series, no model | F→O | The strongest Opus candidate in the guide: pure statistics with unit tests and no model. Not everything is fixed, though: p.43 says "Western Electric or similar" without listing the rules, and decision 15 fixes the metric, not the statistics — so Fable's spec must name the rule set, the window semantics and the tie-breaking. Spec: input series shape, window, the rules to implement, output (tier, rule hit, values). |
| 37.2 Metric source for CI test failure rate: GitHub Actions runs API through `urllib`, cached to a file; the adapter's `maintain.source` for other metrics later | F→O | Spec: which endpoint, which runs count as a failure, the window. |
| 37.3 `template/bands.yaml` (p.44 shape) with the per-route `authorization: preapproved \| go` key of decision 14 (one key, two values, as `template/sdlc.yaml` already words it for `maintain.runbooks`) | F | The routes and their authorization encode the blast-radius split, a guardrail choice; the p.44 copy itself is mechanical and step 21 may already have created the file — reuse. |
| 37.3a The scheduled detection workflow in the template | F→O | Spec = its row in the 30.2 trigger table (schedule, guard, what it dispatches at each tier). |
| 37.4 Tier actions: 1σ log; 2σ dispatch the read-only diagnose run; 3σ open the intent PR through gate (e) or run a pre-approved runbook, park with "Go" requested for `authorization: go` routes | F→O | Fable writes the routing rules and the two default runbooks (quarantine a flaky test in the project's suite, open a revert PR) including the guard that a runbook never edits a test in this repo, and chooses the runtime (a CI step, or an Agent SDK service for webhooks — p.43–44, "design yourself"); Opus implements the dispatcher and tests. |
| 37.5 The diagnose prompt: read-only tools, reads `lessons/`, writes the diagnosis as an intent.md in the intent-template shape with the Evidence section, labels the PR `incident` | F | Prompt text. |
| 37.6 Gate checks for phase (f): `CHECKS_BY_PHASE["f"]` is empty today; decide which checks apply to a maintain run (artifacts of the incident intent, guardrails, risk list, the route's authorization) | F for the list, O for the code and tests | The list is a gate semantics choice; the checks themselves exist. |
| 38.1 Weekly security review: which skill runs it (the plugin's `security-baseline` skill, Claude Code's `security-review`, or both), read-only, and the "bounded finding → PR through the review gate; wider → intent.md; fixed class → eval" criterion | F | Judgement on routing; decision 16 fixes the shape only. |
| 38.2 Workflow, findings-to-route Python, dismissal store (signature + reason) that suppresses a repeated finding, tests | F→O | Spec from 38.1; reuse the signature function of 26.4. |
| 38.3 Deterministic scanners stay in CI regardless (decision 16): a dependency audit and a SAST step in the template's CI, per language detected by `/sdlc-init` | O | Mechanical; the guide and decision 16 name it. |
| 39.1 Gate (f) mechanics: `incident` label on intent PRs, "schedule" label, close-with-reason recorded as a dismissal, a bands change always through a `bands.yaml` PR | F→O | The guide's notes for step 39 already state all four elements; a three-line spec carries it, plus the new labels (`incident`, `schedule`) added to `conventions.all_labels()` — they do not exist today. The one judgement — that "dismissals tune the bands" is not automatic — is already recorded there. |
| 39.2 Workflow on a closed-unmerged incident PR that reads the closing comment and appends the signature to the dismissal store in a PR | F→O | Spec from 39.1. |
| 41.1 Keep each headless run's JSON transcript in `evidence/` (the gate verdicts already land there as `gate-<phase>.json`); every hook appends one line per decision (allow/block, timestamp, tool, path) to the log file defined in 29.1; upload it as a CI artifact | F→O | Spec: the 29.1 format and variable name; touches every hook, so the tests in `tests/test_hooks.py` grow. |
| 42.1 The two counters (first-pass merge yes/no, fix iterations from `status.iterations`) in the PR description | O | Part of 27a.1 if not already there. |
| 42.2 The later scheduled report over `changes/*/` and PR history | O→F | Optional; Opus drafts, Fable decides whether to ship it. |
| B5 wrap-up: reviews, docs, final handoff | see §2 | Done 2026-09-25: session 5 ended with plugin 0.2.19 (PR #44), the sample repository upgraded (its PR #23), the live checks 16–23 listed in PROGRESS (none run yet but the evals) and `HANDOFF.md` rewritten for session 6 (§5a). |

Outcome (2026-09-25, plugin 0.2.19; the record is `docs/PROGRESS.md`): every row above was
built in one cloud session. Opus wrote, from Fable's specs, `plugin/detect/stats.py` and
`bands.py` (37.1), `source.py` (37.2), `runbooks.py` (37.4), `plugin/evals/` with the
template wrapper and the first four cases (35.3, 35.4), `plugin/scan/` (38.2, 38.3), the
35.2 research report, and the unit tests of `routes.py`, `dismissals.py`, `finding.py` and
`detect/cli.py`; Fable wrote the specs, the phase (f) design (the routes and their
authorization, the dispatcher, the dismissal store, the gate (f) checks, the CLI), the
prompts (`/sdlc-maintain`, the lines of `/sdlc-deploy`, `/sdlc-fix`, `/sdlc-build` and
`/sdlc-test`), the workflows, the observability change (every hook logs), the counters and
the docs. Step 33 stays not built (decision 17); step 40 stays optional.

## 5a. Session 6 — the phase (f) shakedown (live checks 16–23 and the owed 8)

No build stage remains; the session runs the loop live on the sample repository and fixes
what breaks. The split follows §1: judgement stays with Fable, mechanical work from a
written spec goes to Opus (named `model: "opus"` explicitly; the environment variable was
unset in session 5).

| Task | Who | What Fable must give the sub-agent, or why it stays with Fable |
|---|---|---|
| Triggering each live check, reading the job log, the transcript and the committed evidence, deciding whether a misbehaviour is the framework's, the platform's or the model's | F | The verdict decides what is fixed, what becomes a NOTES fact and what becomes an eval case; wrong attribution costs a session. |
| The regression test and the fix for a framework defect a check revealed | F→O | Spec: the observed behaviour (log lines), the expected one (the OPERATING_MODEL sentence or the decision), the file set. Disjoint file sets when two fixes run at once. |
| A NOTES correction from live evidence (the runs API's filters and paging, the sandbox's `gh`, the artifact download) | O | URL and quote, plus the run URL that showed it. |
| An eval case from a model-behaviour lesson (a prompt the model misread, a rule it skipped) | O→F | Opus writes the case from the transcript; Fable checks it asserts the behaviour, not the wording (session 5's case 0001 lesson). |
| The sample's guardrail edits (a runbook under `maintain.runbooks`, a route in `bands.yaml`, `deploy.production`) | F | Given to the owner in the "link; row; what is there; what it needs to be" format; never edited by the session. |
| The fresh-context review of the diff before the commit | O | As in every session (§2). |
| Session-6 wrap-up: PROGRESS, the next handoff (if anything remains) | F | As in every session (§2). Done 2026-09-25: six detect runs, two scans, four digests, one design run, one fix round, one Go and five abandon jobs on the sample; ten defects (D1–D10) fixed by Opus from Fable's specs, each with its test, across plugin 0.2.20, 0.2.21 and 0.2.22 (PRs #47, #48, #49, all merged and tagged the same day); every live check of the table proven; no model lesson, so no eval case; NOTES §14; `HANDOFF.md` rewritten for session 7 (the first real breach and the recorded gaps). |

## 6. Session 2 (steps 16–21) — finished

Session 2 completed on `main` (PRs #4, #5, #7, plus #8 for the editable install) before
this file was first merged, with 207 tests green on Linux and on the owner's Windows PC.
Nothing of B2 is left to allocate; the live checks it left (policy-skill and agent triggers,
preflight in the sample repo) are the owner's, not a model's.

## 7. Runtime model choice (not a build-session question, recorded for completeness)

The framework's own runs are a different budget from the build sessions:
- From B3 the phase jobs run in CI (decision 1) with the credential of NOTES §2: on the
  subscription token they draw on the owner's Pro window, on an API key they are billed per
  token in dollars outside every plan window; the owner starts with the token. The model each job uses is a `--model` flag in
  `plugin/ci/run_phase.py`; the natural default is `opus` for every phase, with `fable`
  reserved for the read-only planning run and the adversarial reviewer if the owner wants
  it. This choice is not made here.
- Until then, and for the manual runs of B3's first rung, the phase commands run in the
  owner's own session and share its model. The four plugin agents say `model: inherit`. Pinning
  `model: opus` on `verifier`, `code-simplifier` and `researcher` would move those runs off the
  Fable window in every project session; the adversarial reviewer could stay on `inherit`
  (the operating model's "writer ≠ judge" is about a fresh context, not a different model) or
  be pinned too. That is a one-line change per agent file plus the static test in
  `tests/test_agents.py`, and it is a framework change to record in PROGRESS, not a build-session
  rule — so it is listed here and not applied.
