---
type: Proposal
title: "The trial project's shape — what a repository that is not the sample needs from /sdlc-init and the CI session"
description: "The five risks the trial readiness review of 2026-10-20 ranks before /sdlc-init runs on the real project, each checked against main and the roadmap: the CI session's command and network allow lists follow the project, detection reaches the 'ask the owner' path on a mixed repository, /sdlc-init names the CI workflow the maintain metric reads, the targets' duration and environment reach the gate, and the project's secret-shaped files are proposed as protected and unreadable."
status: proposed
roadmap: R61
sources:
  - id: review
    resource: docs/reviews/2026-10-20-trial-readiness-review.md
    title: "The trial readiness review of 2026-10-20: risks 1 to 5, ranked, with file and line"
  - id: cross-reference
    resource: docs/reviews/2026-10-20-findings-cross-reference.md
    title: "The cross-reference of 2026-10-20: each risk checked against main at 86dc563 and the roadmap rows"
  - id: owner
    resource: "the owner's instruction of 2026-10-20 in session ccr-7ef35daa-7adzh8 ('Go'): cross-reference the merged reports' findings with the roadmap and register what no row holds"
    title: "Why the row exists"
generated: { by: sdlc-framework-session/ccr-7ef35daa-7adzh8, at: 2026-10-20T06:00:00Z }
---

# The trial project's shape

**Status: proposed on 2026-10-20 from the trial readiness review; the owner has not decided.** Nothing is built. Changes under `plugin/` and `template/`, so it takes the next free patch number at its merge (choice 184), as one session pull request or one per part, each with an independent fresh-context review (the owner's rule of 2026-10-16).

## The problem

The trial readiness review (`docs/reviews/2026-10-20-trial-readiness-review.md`) asked what a repository that is not `sdlc-sample-python` does to the plugin and the template. It ranked five risks to settle before `/sdlc-init` runs on the trial project. The cross-reference of 2026-10-20 (`docs/reviews/2026-10-20-findings-cross-reference.md`) re-read each one on `main` at `86dc563`. Four hold as written and one is smaller than the review says:

1. **The CI session can run Python and Node tools only.** `plugin/ci/settings.ci.json` allows `git`, `gh`, `python`, `python3`, `npm`, `npx`, `node`, `pytest` and `ruff`, and its network list names PyPI and npm only; `run_phase.ci_settings_file` rewrites the path rules and `denyWrite` and adds no allow rule (re-read on `86dc563`). On a Go, Rust, Java, .NET or Ruby project the build run cannot run the tests it is told to run before "done", and every fix round is as blind.
2. **`detect()` answers "Python" whenever one `.py` file exists** (`plugin/init/detect.py`, `detect`). A mixed repository gets pytest, ruff and compileall targets in `sdlc.yaml`, in both `CLAUDE.md` sections and in `test_paths`, and the step 4 run passes on nothing.
3. **The maintain metric counts every project workflow unless the source names one.** The review says `sdlc.yaml` has no key for the workflow. The mechanism exists since 0.2.19: `maintain.source: github-actions:<workflow name>` restricts the count to that workflow (`plugin/detect/source.py`, `parse_source`; `plugin/detect/cli.py` passes it to `counts`), and `maintain_observation` already matches it. What is missing is the default: `/sdlc-init` writes `github-actions` (`plugin/init/sdlc_init.py`, `--maintain-source`), so a repository with a lint workflow, a nightly and a deploy counts all of them.
4. **The targets' duration and environment do not reach the gate.** `command_timeout: 900` is the template's value whatever the project's build takes, nothing sets `BASH_DEFAULT_TIMEOUT_MS` for the session (no hit under `plugin/`), and `commands_env` passes no repository secret or variable to the targets.
5. **The project's own secret files are readable by the session.** The Read deny names `.env*` and `secrets/**` only, and `template/sdlc.yaml` ships `protected_paths: []`.

## The proposal

1. `ci_settings_file` appends to the session's allow list the rules the project's own `.claude/settings.json` already derives from `commands.build`, `commands.test`, `commands.lint` and `commands.setup` (`sdlc_init.py`, `_rule_for`), and an optional `sandbox.allowed_domains` list in `sdlc.yaml` to the network list; `/sdlc-init` proposes the registry of the detected or declared toolchain. A test each.
2. `detect()` counts the signals of each language it knows and, when Python or Node is present but not dominant, returns the language with every target unset and a note, so `/sdlc-init`'s "ask the owner for the command" path is reached; the report names the signals counted. A test per language.
3. `/sdlc-init` lists the project's own workflows (it already does, for `maintain_observation`) and, when there is more than one, proposes `github-actions:<name>` for the one that runs the tests and says so in the report. No new key.
4. `/sdlc-init` step 4 times the three commands, writes `command_timeout` as three times the longest run (at least the template's 900) and prints the two workflow numbers to raise when it exceeds the template's; the runner sets `BASH_DEFAULT_TIMEOUT_MS` from `command_timeout`; `commands.env: [NAME, ...]` names repository secrets or variables passed to the setup command, the session and the commands step. A service a test needs stays the owner's edit of the workflow, and the change-0000 intent says that service-bound tests are deselected for the trial.
5. `/sdlc-init` scans for secret-shaped paths (`*.pem`, `*.key`, `*.p12`, `*.pfx`, `*.jks`, `*.keystore`, `id_rsa*`, `credentials.json`, `terraform.tfvars`, `*-secret.yaml`, `appsettings.*.json`, `.npmrc`) and proposes them as `protected_paths` entries and as `Read(...)` deny rules, confirmed by the owner in the change-0000 PR; `ci_settings_file` appends `protected_paths` to the Read deny as it does to `denyWrite`.

## Related findings, carried here for the owner

- The plugin security review's M10 (`docs/reviews/2026-10-19-plugin-security-review.md`): the secrets hook scans file-tool writes only, misses some token formats, and its `PLACEHOLDER` match is unanchored; a diff-level secret scan at the gate is its fix. It meets part 5 on the same question: what keeps a real project's credential out of a commit.
- The review's smaller findings that no part above takes (trigger noise on a busy repository, lockfiles against `plan_sync`, an existing `evals/` or `changes/` folder kept silently, the design run's turn cap on a large codebase, `python` on the runner) are left for the trial to show; the formatter finding is on R33's row.

## What it does not cover

R44 (the sandbox: shell writes, the model credential, `~/.ssh`) and R24 (the risk list's globs) are untouched; part 5 is about the project's own files, which neither names. Part 5 could instead ride with R44, which the review also offers; the owner decides. A deploy through `deploy.command` on the trial is out of scope (R39).

## Decisions it touches

6 (the guardrails' three layers; kept: the new deny and protected entries are written into the project's guardrail files by `/sdlc-init` and merged by the owner in the change-0000 PR), 7 (Python; kept), 15 (the first metric; kept: one workflow's failure rate is still the CI test failure rate), 23 (GitHub only; kept). No decision is amended.

## Order

Blank until the owner places it. The review's verdict is that the trial is "ready after those five"; parts 1 to 3 are small and independent of every other candidate.
