---
type: Proposal
title: "The CLI a new project installs knows the models its sdlc.yaml names"
description: "/sdlc-init and the pin script default the Claude Code CLI to 2.1.278, which does not know claude-opus-5-5 as a sub-agent's model, while the template sets session_model and adversarial_model to claude-opus-5-5; the defaults move to 2.1.304, the CLI that ran the reviewer and the advocate on claude-opus-5-5 on the sample."
status: accepted
roadmap: R63
sources:
  - id: note-54
    resource: docs/notes/54.md
    title: "R7's first live reading: 2.1.278 runs the reviewer on the session's model; 2.1.304 runs it on claude-opus-5-5"
  - id: files
    resource: "plugin/init/sdlc_init.py:62, template/.github/scripts/sdlc_pin.py:53, .github/scripts/sdlc_pin.py:53, template/sdlc.yaml:44-45 and 182, sdlc.yaml:107-108, on main at fe315da"
    title: "Where 2.1.278 is the default"
  - id: owner
    resource: "the owner's message of 2026-10-20 in session ccr-a6fc1017-mkylxv: 'accept R63 as recommended', 'sdlc.yaml changed' (PR #287)"
    title: "Accepted, and the root pin raised"
generated: { by: sdlc-framework-session/ccr-a6fc1017-mkylxv, at: 2026-10-20T14:10:00Z }
---

# The CLI a new project installs knows the models its sdlc.yaml names

**Status: accepted by the owner on 2026-10-20, as recommended (choice 244).** Nothing is built yet. *[2026-10-20: built as plugin 1.0.16 in PR #291; item 4 is built as the runner's `cli_model` park, and the two workflows stay on 2.1.278 (neither runs a sub-agent on a full model id); the reasons are in `docs/PROGRESS.md`]* It changes `plugin/` and `template/`, so it takes the next free patch version.

## The problem
- `template/sdlc.yaml` sets `session_model: claude-opus-5-5` and `adversarial_model: claude-opus-5-5` (lines 44-45).
- `/sdlc-init` writes `claude_code` from `DEFAULT_CLAUDE_CODE_VERSION = "2.1.278"` (`plugin/init/sdlc_init.py:62`), and the pin script falls back to the same version when the key is absent (`template/.github/scripts/sdlc_pin.py:53`).
- On 2.1.278 the adversarial reviewer's `claude-opus-5-5` is `unrecognized_model`, the reviewer runs on the session's model, and R7's `reviewer_model` check parks the gate (NOTES §54, the sample's change 0017). A project set up on plugin 1.0.14 with the template's defaults would park at every gate until its owner raised the pin.
- On 2.1.304 the reviewer and the advocate ran on `claude-opus-5-5` (NOTES §54, sample run 39407985040).

## The change
1. `DEFAULT_CLAUDE_CODE_VERSION` in `plugin/init/sdlc_init.py` and `DEFAULT_CLAUDE_CODE` in `template/.github/scripts/sdlc_pin.py` and its copy `.github/scripts/sdlc_pin.py` move from 2.1.278 to 2.1.304.
2. The comment above `claude_code` in `template/sdlc.yaml` ("2.1.278 is the CLI the jobs install and the framework's minimum") names 2.1.304 and says why: the first version read to run a sub-agent on a full model id.
3. The tests that pin the default follow.
4. Optional, decided at the build: the runner names a `[claude-code:unrecognized_model]` line in the session's stderr as a park reason of its own ("the pinned CLI does not know model X; raise `sdlc.yaml: claude_code`"), which says more than the `reviewer_model` mismatch it causes.

The root `sdlc.yaml` is the owner's edit: its pin moved to 2.1.304 in PR #287 and its comment on line 107 in PR #288. The framework's own workflows that install a fixed CLI (`.github/workflows/substrate-smoke.yml`, `.github/workflows/framework-evals.yml`) are read at the build: they move only if they run a sub-agent on a full model id.

## Order
Before R24 (rank 8), with no rank moved *[2026-10-20: R24 merged first, as plugin 1.0.15 (PR #286), in a session that ran in parallel; R63 is the next build, as 1.0.16]*. It is built once change 0017's build run (c) shows the session on `claude-opus-5-5` under 2.1.304, which completes the reading the new default rests on.

## Why not a part of R61
R61 (after R44, before R18) is about the trial project's shape and is several builds away; until this lands, any project set up on the current plugin parks at every gate. The change is small and touches different lines from R61's `/sdlc-init` work.
