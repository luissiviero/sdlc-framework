---
type: Proposal
title: A drive target proves the product; the plan's Proof names states as well as screenshots; the runner produces the proof and the verifier reads it
description: A fourth optional target in sdlc.yaml, commands.drive, exercises the product headless and writes screenshots and state files into evidence/; the runner runs it after the session beside build, test and lint, and a red drive is a red target; plan.md's Proof section may name a state file with an expected value; the verifier reads the proof files of the previous phase and reports per item; the PR body shows them; /sdlc-init proposes the command where the stack already has the tool.
status: proposed
roadmap: none yet; the owner places it (section Order)
sources:
  - id: artcraft-study
    resource: docs/reviews/2026-10-13-artcraft-vs-framework.md
    title: "Section 8.1 row A1 and the breakdown into eight sub-changes given in the same session; evidence in 2026-10-13-artcraft-vs-framework/study-e-inner-loop.md"
  - id: artcraft-sources
    resource: docs/reviews/2026-10-13-artcraft-vs-framework/study-e-inner-loop.md
    title: "lightcraft docs/control-protocol.md:254-262 (a scripted session judged by its exit status); photocraft docs/development.md:222-227 and crates/automation/tests/agent_tasks.rs:1-4 (state inspection instead of screenshots); filmcraft docs/agents.md:250-256, 309-320 (drive, assert, screenshot, in the Definition of Done); photocraft docs/contributing.md:11 (before/after screenshots in PRs); filmcraft docs/testing.md:163 (golden PNGs under 50 KB)"
  - id: study-entries
    resource: docs/reviews/2026-09-28-playbook-vs-framework/target-design.md
    title: "T3 (the Mock: line stays), T10 (the runner's step and the round on a red target), T27 (the PR block), T32 (the proof files as records); T20 (where a live product would be driven, later)"
  - id: playbook
    resource: docs/reference/ai-native-sdlc-playbook.pdf
    title: "p.25-27: the fresh-context verifier; p.27-29: run the tests, run the build, take the screenshot, iterate; p.12-13: the design mock as the visual target; p.34-35: the pull request as the audit record"
  - id: decision-19
    resource: docs/decisions/19.md
    title: "Decision 19: what deploy and maintain mean per project, the adapter shape this target follows"
  - id: decision-11
    resource: docs/decisions/11.md
    title: "Decision 11: a phase that cannot finish parks; a red drive follows the red-target rule"
  - id: code
    resource: plugin/commands/sdlc-test.md
    title: "Step 3, the screenshot loop against the mock, lines 75-84; plugin/agents/verifier.md steps 2 to 4; plugin/skills/plan-template/SKILL.md lines 31-33 (Proof); plugin/skills/spec-template/SKILL.md line 41; plugin/gate/artifacts.py line 69; template/sdlc.yaml lines 35-41; plugin/commands/sdlc-init.md lines 22-25; read at main after PR #166, plugin 0.3.7"
generated: { by: sdlc-framework-session/session_01EkLAGQBH3JG2kGHgqQe9xv, at: 2026-10-13T15:30:00Z }
---

# A drive target proves the product, and the plan's Proof names what to look at

**Status: proposed, from the ArtCraft-versus-framework study of 2026-10-13 (row A1), not yet placed.** Nothing is built. It extends four confirmed entries of the playbook study (T3, T10, T27, T32) and amends no settled decision.

## The problem

The confidence gate judges artifacts: the spec's shape, the plan against the diff, the three targets' exit codes, the evidence files, the review findings, the guardrails, the limits. Nothing judges the product. Three things follow:

- **The agent cannot show that the product works, only that the suite passes.** `sdlc.yaml` has `commands.build`, `test`, `lint` and `setup` and nothing that runs the product (`template/sdlc.yaml:35-41`). The (d) run's screenshot loop exists, but it keys on a mock or screen the plan names and, "without a browser or screenshot tool in this session", writes a README saying so (`plugin/commands/sdlc-test.md:75-84`).
- **Proof is a test or a screenshot, never a state.** `plan.md`'s `## Proof` lists "the mock or screenshot to match" beside the tests (`plan-template/SKILL.md:31-33`); the spec's Acceptance asks for "the screenshot or mock to match for UI" (`spec-template/SKILL.md:41`). A CLI, a library or a data pipeline has no screen, so its proof is the suite alone.
- **The verifier never looks at the product's output.** It runs the targets by hand, reads the previous phase's record in CI, and exercises code through direct calls (`plugin/agents/verifier.md` steps 2 to 4). It reads no screenshot and compares no state with an expectation written before the build.

ArtCraft's agents ship working features because they can act on the product and look at the result without a person: a scripted session judged by its exit status, a state dump "so agents can verify what they did without a screenshot", and a Definition of Done that reads "you have driven it through the control channel and reviewed a screenshot"[^artcraft]. Their mechanism is product architecture (a control protocol, a command registry) and does not transfer; the step in the loop does.

## What the article says

The verifier runs in a fresh context so that its verdict "is not colored by the assumptions that produced the code" (p.25-27); the test phase is "run the tests, run the build, take the screenshot" and iterate (p.27-29); the design mock is the visual target the build matches (p.12-13); the pull request is the audit record that carries the evidence (p.34-35)[^playbook]. The framework has each of these as a prompt line or a conditional loop; this proposal makes them steps the runner performs and the gate records.

## What the framework does today

Read at `main` after PR #166, plugin 0.3.7[^code].

- **Targets.** The runner runs `commands.build`, `test` and `lint` once after a CI session, outside the sandbox, in the step that holds none of the job's credentials, and rewrites the gate record's `commands` and `evidence` checks; a red target parks (OPERATING_MODEL §3, 0.3.0 and 0.3.2). Inside the session no target runs: the sandbox denies a nested `.env*` to every process the session starts (issue #91; choices 133 and 154). T10 keeps this and adds the automatic round on a red target.
- **Proof and screenshots.** `plan.md` has `## Proof`; `/sdlc-build` names there "the screenshot that phase (d) compares with" the mock (`sdlc-build.md:85-87`); the (d) run compares and writes `evidence/screenshots/<name>.png` when the plan names one, and the gate's `evidence` check knows that folder (`gate/artifacts.py:69`), treating it as missing only when the plan asked for screenshots. T3 fixes a `Mock: mock/<file>` or `Mock: none` line in the spec's Acceptance.
- **The verifier.** In CI it never runs the test runner, reads the previous phase's gate record and logs, exercises the changed behaviour through direct calls that read no `.env*`, and reports commands, behaviour, mismatches and a verdict. Its report is `evidence/verifier.md`.
- **The PR body.** Five bullets, the findings, the plan conformance, the counters; T27 adds the "What you can do here" block. No screenshot or proof file is shown.
- **`/sdlc-init`.** Detects Python and Node targets (`sdlc-init.md:22-25`); the owner confirms or overrides each.

## The proposal

Six sub-changes, in the order they depend on one another. Two more were considered and set aside (below).

1. **A fourth optional target, `commands.drive`.** One command that exercises the product headless and writes its outputs under `changes/<id>-<slug>/evidence/proof/` (PNG screenshots, JSON or text state files), exit status non-zero when any step failed. Empty means none, like `deploy.command`. The command is the project's: a Playwright script for a web app, a Python script that runs the CLI and dumps its state for a tool, a snapshot renderer for a desktop app. The framework never asks a project to adopt an architecture; it asks for one command.
2. **The runner runs it after the session, and a red drive is a red target.** The commands step gains a fourth entry beside build, test and lint, under the same timeout (`gate.command_timeout`), in the same credential-free step, on the working tree the session left; its exit code and output tail join the gate record's `commands` check and `evidence/drive.log`; the outputs land with the evidence commit. Under T10 a red drive dispatches the next fix round with `drive.log` as its constraint; at the cap it parks. Nothing new runs inside the session.
3. **Proof items may name a state with an expected value.** `## Proof` gains a third kind beside the test and the screenshot: `state: evidence/proof/<file>, <path> == <value>` (or `contains`, `matches`). The gate's `evidence` check verifies that every proof file the plan names exists after the runner's step, as it does for screenshots today; the comparison of values is the verifier's.
4. **The verifier reads the proof and reports per item.** Its card gains a step: open the proof files the runner produced for the phase before yours (a PNG through the Read tool, a state file as text), compare each with the plan's Proof item, and report one line per item, `matches`, `differs` (with what was seen) or `not produced`, each marked measured. The verdict `does not match the plan` covers a `differs`. The writer still never judges; the judge now sees the product.
5. **The PR body shows the proof.** T27's block gains a "Proof" line per item: the item, the outcome from `verifier.md`, and a link to the file at the head commit. Images stay under a size cap the gate's `evidence` check enforces (ArtCraft caps golden PNGs at 50 KB; the value is to settle), so the repository does not grow with every change; a larger image is reduced by the drive command or refused.
6. **`/sdlc-init` proposes the command where the tool already exists.** Node with Playwright in `package.json`: `npx playwright test proof/ --reporter=json`; Python: an empty `proof/run.py` skeleton that exits 0 and writes nothing, named so the owner sees the slot; anything else: `""` with a comment. The owner confirms as for the three targets.

## How it is judged

On the sample repository and the next project: a change whose plan names a state item ships with `evidence/proof/` filled by the runner, `verifier.md` reporting the item, and the PR body showing it; a change whose product behaviour is wrong while its suite is green is caught by the drive step or by the verifier's `differs` before the owner's (e) review. The failure is a merged change whose product did not do what the plan promised while the proof folder is empty or unread.

## What to settle before building

| Question | Recommended |
|---|---|
| Where the drive runs | The runner's commands step, never the session: the sandbox decisions stand (T10, choices 133 and 154) |
| Whether a red drive starts a round or parks at once | T10's rule: a round with `drive.log` as the constraint, a park at the cap; a drive that cannot start (no command, a timeout) parks at once, as T10 settles for the other targets |
| The proof item grammar | Three kinds, `test`, `screenshot`, `state`; the state item names the file, a path into it and one of `==`, `contains`, `matches`; the plan template fixes the shape so the `artifacts` check can parse it |
| The image size cap | A number the owner picks once in `sdlc.yaml: gate.proof_image_kb`, default to decide (ArtCraft uses 50 KB for goldens); over the cap is evidence missing |
| Whether the verifier's PNG reading counts against the budget | It does; the cost is a few images per change, weighted 0 by the owner |
| How the `Mock:` line (T3) and the `screenshot` item relate | The spec's `Mock:` names the target image; the plan's `screenshot` item names the file the drive writes; the verifier compares the two when both exist |
| Whether a project with `commands.drive` empty loses anything | Nothing: the gate ignores the drive and the Proof's `state` and `screenshot` items are reported `not produced` only when the plan named them |

## Considered and not chosen

- **A project audit test that every user-facing action is reachable headless** (effectcraft's `ui_agent_audit.rs`): product architecture, not process; at most one sentence in the `ux-conventions` skill that a new screen must be reachable by the drive command.
- **The session driving the live product through a project MCP server registered in the repository** (filmcraft's `.mcp.json`): it runs inside the sandbox the drive step avoids, puts a project-controlled server inside a privileged session, and leaves no committed record; sub-change 1 gives the same evidence deterministically. Its place is T20, where a preview environment is a URL the verifier can call.
- **Running the drive inside the session** so the agent iterates on the result as ArtCraft's agents do: the sandbox denies the nested `.env*`, and a helper that runs it outside the sandbox for the session was rejected by T10 as a hole the session controls.
- **Proof files as workflow artifacts instead of committed files**: the record would outlive nothing (T32 keeps transcripts as artifacts because they are large and sensitive; proof files are small and are the evidence the owner approves), so they are committed under the cap.

## Decisions it touches

None is amended. 19 (the adapter per project) gives the target its shape; 11 (park, never notify) and T10's rule give a red drive its consequence; 12 (the review pass in a fresh context) and OPERATING_MODEL §2 (writer never judges) are kept: the verifier reads what the runner produced. No decision file is written.

## Order

Not placed. It cannot be built before the 1.0.0 read because the runner's commands step is in `run_phase.py`, on the port list until then (HANDOFF, rules for every session). Among the study's proposals it belongs with T10 (R10), whose runner step it extends, and before T27, whose PR block it fills; sub-changes 3 and 6 (the plan template and `/sdlc-init`) touch no runner code and could land first as a plain change. Where it sits in the queue is the owner's call, as for R11 to R13.

## What changes in the playbook study's record

The entries this proposal extends are annotated, never rewritten (choice 126): one dated line beside the status of T3 ("the `Mock:` line stays; the plan's Proof gains the `state` kind, proposal `drive-target-and-proof.md`"), T10 ("the commands step gains the drive target under the same rule"), T27 ("the block gains the Proof line") and T32 ("the proof files are records at the head commit"). The crosswalk is not extended, as the owner asked; the rows test-loop, test-verify and design-mock are named here instead. The target workflow page is not redrawn until the proposal is accepted.

[^artcraft]: `docs/reviews/2026-10-13-artcraft-vs-framework/study-e-inner-loop.md` §1, §2, §5; the cited lines are `lightcraft docs/control-protocol.md:254-262`, `photocraft docs/development.md:222-227`, `filmcraft docs/agents.md:250-256` and `:309-320`, `photocraft docs/contributing.md:11`, all at the HEAD commits the study names.
[^playbook]: `docs/reference/ai-native-sdlc-playbook.pdf` p.12-13, p.25-29, p.34-35, as `plugin/commands/sdlc-test.md`, `sdlc-build.md` and `plugin/agents/verifier.md` cite them.
[^code]: `template/sdlc.yaml:35-41`; `plugin/commands/sdlc-test.md:55-84`; `plugin/commands/sdlc-build.md:85-87`; `plugin/agents/verifier.md`; `plugin/skills/plan-template/SKILL.md:31-33`; `plugin/skills/spec-template/SKILL.md:41`; `plugin/gate/artifacts.py:69`; `plugin/commands/sdlc-init.md:22-25`; `docs/OPERATING_MODEL.md` §3.
