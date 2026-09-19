# Progress — session 1 (B0 + B1)

## Summary
- B0 (steps 1–9b) and B1 (steps 10–15) are built and green: 88 self-tests plus fixture integration tests pass with `python tasks.py check` (lint zero warnings) on Linux; Windows execution and the live-session checks (hook denial inside Claude Code, skill triggering, PR opening) are still owed and listed below as partial.
- Four Python hooks (protected paths with self-protection, secrets check, formatter/lint on edit, plan.md sync on `git commit`) ship in the plugin in exec form, fail closed, and are unit-tested with sample tool inputs; the protected-path hook demonstrably blocks an edit to `.claude/settings.json` (exit 2 + deny JSON).
- Docs verification changed two designs: the managed-settings keys are managed-scope only and machine-wide (so `docs/owner-machine/` documents, and does not install, the file), and the framework must work in cloud sessions, so a project loads the plugin through its own `.claude/settings.json` marketplace declaration. No decision was reopened; decision 6 keeps its three layers with corrected mechanics.
- `/sdlc-init` (minimal, step 21) and `/sdlc-plan` exist as commands over deterministic Python (`plugin/init`, `plugin/state`); the fixture project is initialised and gets its first PR branch `sdlc/0000/a`, and a recorded intent lands on `sdlc/0001/a` in the integration test.
- Left for B2: the confidence gate (`plugin/gate/`), agents, run limits, policy skills, `/sdlc-init` extras (evals/, bands.yaml, CI workflows), and the live checks above.

## Definition of done (handoff)
| Item | Status |
|---|---|
| `python tasks.py test` and `python tasks.py lint` green on Windows and Linux | Linux: done (88 passed, ruff clean). Windows: not executed in this session; code is path-agnostic (no shell, `pathlib`, backslash normalisation tested). Owner to run once on the PC. |
| Fixture initialised with `/sdlc-init` from a temporary copy; `/sdlc-plan` produces a committed `changes/<id>-<slug>/intent.md` on `sdlc/<id>/a` with an open PR | Python halves: done and tested against a temp copy with a bare remote (`tests/test_integration_fixture.py`). The model-driven halves (questions, `/init`, the PR) are prompts in `plugin/commands/`; the PR itself needs GitHub and is not exercised. |
| Every hook has a unit test; protected-path hook blocks an edit to `.claude/settings.json` | Done (`tests/test_hooks.py`, end-to-end over stdin with exit code 2). Not yet observed inside a live Claude Code session. |
| `docs/NOTES.md` answers the two verification questions with links | Done (sections 1 and 2), plus cloud, managed keys, sandbox, permissions and plugin facts. |
| `docs/PROGRESS.md` per step with what is left for B2 | This file. |

## Steps
| Step | Status | What exists / what is left |
|---|---|---|
| 1 Operating model | done | `docs/OPERATING_MODEL.md` edited, not rewritten: id/slug rule, branch roles, hook mechanism for plan sync, three guardrail layers with the docs-verified mechanics, cloud/PC substrate, adapter keys. |
| 2 Scaffold plugin + template | done | `plugin/` (manifest, commands, skills, hooks, state, init, empty `gate/`, `agents/`), `template/`, root `.claude-plugin/marketplace.json` (plugin id `sdlc@sdlc-framework`, version pinned 0.1.0), `tasks.py`, pytest + ruff. |
| 3 Execution substrate | done for B1 | Commands run by hand on the PC or in a cloud session; NOTES §2 records that subscription auth in CI is documented (terms not checked). Wiring is B3. |
| 4 Source of truth | done | OPERATING_MODEL §8; `status.yaml: external_ref` carries the ticket number; `changes/README.md` states the linkage rule. |
| 5 Roles / separation of duties | done (text) | OPERATING_MODEL §2; `risk_list` in `sdlc.yaml`. Enforcement of the risk list is the gate check (B2). |
| 6 Branch rules / automation identity | partial | Text in OPERATING_MODEL §2 and §4; the GitHub ruleset itself is repository configuration the owner applies (not automatable from the repo). Template denies `git push --force*`. |
| 7 Permissions and sandbox | done | `template/.claude/settings.json` (deny `.env*`, secrets, WebFetch, curl, wget; allow git + the three targets; bypass disabled; sandbox where available; second-layer `Edit(...)` denies); `docs/owner-machine/managed-settings.json` + README with the machine-wide consequences. |
| 8 Change requests → `/sdlc-fix` | not started (B3) | Rule stated in OPERATING_MODEL §5; `/sdlc-plan` tells the owner review comments are the change request. |
| 9 Orchestrator conventions | done | `plugin/state/` (conventions, status.yaml schema with validation, dependency-free YAML subset, git helpers, CLI: new-change / commit-phase / set-phase / park / show / labels). |
| 9a Profiles | done | `HUMAN_GATES` per profile, `profile_override` in status.yaml, `profile` in `sdlc.yaml`. Gate logic that reads them is B2. |
| 9b Phase adapters | done (schema) | `deploy.action`, `deploy.production`, `maintain.metric/source/runbooks` in `sdlc.yaml`, asked by `/sdlc-init`. Consumers are B4/B5. |
| 10 intent.md skill | partial | `plugin/skills/intent-template/SKILL.md` (five article sections in order, Author/Status header, change id, entry route, Evidence for incidents). Static tests pass; **"test that it triggers" needs a live model** — owner check: ask "draft an intent for X" in a project with the plugin and confirm the skill loads. |
| 11 `/sdlc-plan` | partial | `plugin/commands/sdlc-plan.md` + `state/cli.py`. Commit and push tested; PR step (gh → GitHub MCP → compare URL) needs a live session. |
| 12 plan.md template + interrogation | done (template) | `plugin/skills/plan-template/SKILL.md`: four article sections + Options not taken, five interrogation questions, read-only rule. `/sdlc-design` is B3. |
| 13 CLAUDE.md skeleton | done | `template/CLAUDE.md` (Commands with healthy output · Conventions · Architecture · Things Claude gets wrong · SDLC framework · Verifying your work, p.28 lines verbatim); `sdlc_init.py` merges missing sections into an existing CLAUDE.md. Note: Commands and Verifying both list the three commands, as the handoff asked; the owner may trim one. |
| 14 Feedback loop | partial | `plugin/init/detect.py` detects or creates build/test/lint for Python (pytest/unittest, ruff/flake8/created ruff.toml, build/compileall) with statistics; targets go into `sdlc.yaml` and CLAUDE.md. Non-Python detection and the "refuse to enter (c)" check are B2/B3. |
| 15 Hooks | done | `plugin/hooks/`: `protected_paths.py`, `secrets_check.py`, `format_on_edit.py` (ruff, Python only), `plan_sync.py` (PreToolUse on `git commit`, phase c branches only); `hooks.json` exec form. Test-file lock is step 25 (B3). |
| 21 `/sdlc-init` (minimal) | partial | `plugin/commands/sdlc-init.md` + `plugin/init/sdlc_init.py` (idempotent: merges sdlc.yaml/settings/CLAUDE.md, keeps REVIEW.md, creates change 0000). Not in this version: evals/, bands.yaml, CI workflows, daily digest, non-Python detection. |

## Decisions: none reopened, none impossible
- Decision 6 stays; mechanics corrected from the docs (managed keys are managed-scope only, machine-wide, ignore project rules, block non-managed plugin hooks). Recorded in NOTES §4 and OPERATING_MODEL §8.
- Decision 7 stays; `python` in exec form (NOTES §1). Assumption: `python` on PATH.
- Decision 1: subscription auth in CI is documented as supported (NOTES §2); terms not verified.

## Choices made where the pack left it open
1. Change id = four-digit sequence from `changes/`, `0000` reserved for `/sdlc-init`; slug = kebab-case title, ≤40 chars.
2. plan.md sync = Claude Code PreToolUse hook on `git commit` (Python, unit-testable), not a git-native hook (would need a shell shim). Exempt globs from `sdlc.yaml: plan_sync.exempt` (default `*.md`).
3. PR opening order in the commands: `gh` → GitHub MCP tool → compare URL printed for the owner.
4. Project protected list lives in `sdlc.yaml`, which the hook also protects.
5. The formatter hook covers Python only in this version; other suffixes are ignored.
6. `sdlc.yaml` and `status.yaml` are read and written by an in-tree YAML subset parser (no PyYAML at runtime); tests cross-check with PyYAML.
7. The article's tension between "protect CLAUDE.md" and "the second finding edits CLAUDE.md" is resolved for now as: the hook always denies; the review proposes the CLAUDE.md line and the owner applies it (REVIEW.md framework rules). Revisit in B3 with `/sdlc-fix`.

## Live checks the owner can do now (not automatable here)
1. On the PC: `python tasks.py check`.
2. In a fresh project: `claude --plugin-dir <framework>/plugin`, run `/sdlc:sdlc-init`, then ask Claude to edit `.claude/settings.json` → expect "Protected path".
3. Ask "draft an intent for ..." → the intent-template skill should load (step 10 trigger test).
4. Run `/sdlc:sdlc-plan` end to end and check the PR and the `sdlc:a-ready` label.

## Left for B2 (next handoff)
- Step 16 confidence gate in `plugin/gate/` (deterministic checks: artifact vs template, tests/build/lint, evidence, no Important findings, plan↔diff, no guardrail edits; risk list) + adversarial reviewer verdict continue/park.
- Step 17 agents (verifier, code-simplifier, researcher, adversarial-reviewer) in `plugin/agents/`.
- Step 18 auto-accept conditions; step 19 run limits (iterations, wall-clock, budget, pause flag) parking through the gate; `status.yaml: iterations` is ready for it.
- Step 20 policy skills; step 21 full `/sdlc-init` (evals/, bands.yaml, workflows, digest) and non-Python detection.
- Live verification items above; Windows run of the test suite.
