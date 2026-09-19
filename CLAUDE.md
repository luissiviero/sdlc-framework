# SDLC framework repo

This repository builds a Claude Code plugin + project template that drives any project through plan → design → build → test → deploy → maintain with profile-based human gates. Read `docs/OPERATING_MODEL.md` first; it is the contract. `docs/BUILD_GUIDE.md` (46 steps, article-cited) is the build plan; `docs/DECISIONS.md` records the 20 settled choices — do not reopen them without asking.

## Commands
- Test: `python -m pytest` (all green; never skip or delete a failing test)
- Lint: `ruff check .` (zero warnings)
- Task runner: `python tasks.py <task>` — must work on Windows and Linux
Run tests and lint before reporting any task complete, and paste the output. If a test fails, fix the code, not the test.

## Conventions
- English only in every file. Never mix Portuguese and English.
- Python for every hook, gate check, detection script and eval check. No bash/jq/make scripts — the owner works on Windows.
- Layout: `plugin/` (commands, skills, agents, hooks, gate logic — process content) and `template/` (files copied into a project by `/sdlc-init` — project content). Never put project content in the plugin or process content in the template.
- Prefer small, idempotent commands; every phase command must be re-runnable after review comments.
- Keep CLAUDE.md under a page; consistently-applied rules go into a skill, not here.

## Architecture
- `plugin/commands/`: /sdlc-init, /sdlc-plan, /sdlc-design, /sdlc-build, /sdlc-test, /sdlc-deploy, /sdlc-maintain, /sdlc-fix
- `plugin/skills/`: intent-template, policy skills (coding standards, security baseline, UX, data conventions, definition of done)
- `plugin/agents/`: verifier, code-simplifier, researcher, adversarial-reviewer (all "report only, do not fix")
- `plugin/hooks/`: protected paths (incl. self-protection), formatter/lint on edit, secrets check, test-file lock for fix tasks, production gate
- `plugin/gate/`: the confidence gate (deterministic checks + adversarial reviewer) and run limits
- `template/`: CLAUDE.md skeleton, REVIEW.md, sdlc.yaml, changes/, bands.yaml, evals/, CI workflows (phase transitions + daily digest)
- `docs/reference/`: the source article (PDF, page-tagged text, dependency graph). Cite it by PDF page.

## Things to get right
- Only the owner merges to `main`; the automation identity has branch-only write access. Never use bypass-permissions mode.
- Events caused by the CI workflow token do not start workflow runs (except workflow_dispatch / repository_dispatch): automated phase transitions dispatch the next workflow explicitly.
- Escalation means park (label `sdlc:needs-human`, write "what I need from you"), never a notification.
- The plan.md run is read-only (Read/Grep/Glob); the first run with edit tools is phase (c).
- Verify how Claude Code on Windows invokes hook commands before writing the first hook; record the answer in `docs/NOTES.md`.
