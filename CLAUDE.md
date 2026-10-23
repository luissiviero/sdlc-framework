# SDLC framework repo

This repository builds a Claude Code plugin + project template that drives any project through plan → design → build → test → deploy → maintain with human gates at (a), (b) and (e), and the owner's triage at (f). Read `docs/OPERATING_MODEL.md` first; it is the contract. `docs/BUILD_GUIDE.md` (47 steps, article-cited) is the build plan; `docs/decisions/index.md` records the settled choices — do not reopen them without asking. `docs/ROADMAP.md` is what comes after Milestone 1: candidates with a proposal each, never a decision.
Indexes first: `docs/notes/index.md` lists every verified platform fact, `docs/decisions/index.md` every settled decision; read the index, then only the files you need.
Every session starts and ends by `HANDOFF.md`: read the newest file in `docs/handoffs/sessions/` and the parallel ones first, write your own at the end, and follow its "Rules for every session".

## Commands
- Task runner: `python tasks.py <task>` — must work on Windows and Linux; `python tasks.py verify` runs every check a PR needs (HANDOFF.md, standing precondition 1)
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
- plugin/detect/: phase (f) — detection statistics, bands, routes and runbooks, the dismissal store, the maintain CLI
- plugin/evals/: the eval runner and the incident case skeleton
- plugin/scan/: the weekly security review and the deterministic scanners
- `template/`: CLAUDE.md skeleton, REVIEW.md, sdlc.yaml, changes/, bands.yaml, evals/, lessons/, CI workflows (phase transitions, daily digest, detection, runbook Go, weekly scan, evals)
- `docs/reference/`: the source article (PDF, page-tagged text, dependency graph). Cite it by PDF page.

## Things to get right
- Only the owner merges to `main`, or the merge App on the owner's approving review (decision 36); the automation identity has branch-only write access. Never use bypass-permissions mode.
- Events caused by the CI workflow token do not start workflow runs (except workflow_dispatch / repository_dispatch): automated phase transitions dispatch the next workflow explicitly. The automation pushes as the project's GitHub App, whose events do start runs (decision 33). The plugin requires the App (R22): without vars.SDLC_APP_ID a run stops with the reason; which plugin version runs here is `plugin.version` in `sdlc.yaml`. The explicit dispatch stays for the in-job fallback to the workflow token after 50 minutes.
- Escalation means park (label `sdlc:needs-human`, write "what I need from you"); the only notification is the review request on a PR that waits for the owner (decision 31).
- The plan.md run is read-only (Read/Grep/Glob); the first run with edit tools is phase (c).
- Verify how Claude Code on Windows invokes hook commands before writing the first hook; record the answer in `docs/notes/1.md`.

## Things Claude gets wrong
<!-- One line per recurring mistake; added when a review flags the same finding twice. -->
- Editing a guardrail file (CLAUDE.md, .claude/**, REVIEW.md, sdlc.yaml) from a session: the tools are denied; propose the exact lines in docs/PROGRESS.md and leave the edit to the owner.
- Rewriting documentation with a script: the auto-mode classifier blocks a scripted rewrite whose payload reads like instructions; edit docs with the Edit tool, sentence by sentence.
- Asking the owner to edit a file: give a table with link, row, what is there now, what it must become (or the suggestion), one row per edit; nothing else.

## SDLC framework
- Every change lives in `changes/<id>-<slug>/` (intent.md → spec.md + plan.md → evidence/);
  phase branches are `sdlc/<id>/<phase>`; see `changes/README.md`.
- Never edit `.claude/**`, `CLAUDE.md`, `REVIEW.md` or `sdlc.yaml` in a run: they are
  guardrails the owner changes in a reviewed PR. Never use bypass-permissions mode.
- When a run cannot finish, park: write "what I need from you"; notify only by the review request of decision 31.

## Verifying your work
<!-- Verbatim structure of the article's verification block (p.28). -->
- Build: `python -m compileall -q plugin tests tasks.py` (must finish with no output and exit code 0)
- Test: `python -m pytest` (all green; never skip or delete a failing test)
- Lint: `python -m ruff check . && python -m ruff format --check .` (zero warnings)
Run all three before reporting any task complete, and paste the output.
If a test fails, fix the code, not the test.
