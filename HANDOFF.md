# Handoff — build the SDLC framework repo (session 1: B0 + B1)

## Read in this order
1. `docs/OPERATING_MODEL.md` — the contract (gates, profiles, conventions). Treat it as the spec.
2. `docs/DECISIONS.md` — 20 settled decisions. Do not reopen them; if one proves impossible, stop and report why.
3. `docs/BUILD_GUIDE.md` — the 46-step build plan (`docs/build_guide.json` is the same data). Steps are grouped in build stages B0 → B5; the "Phase" of a step is where it operates once built, not when to build it.
4. `docs/reference/ai-native-sdlc-playbook.txt` — the source article, page-tagged (`===== PAGE N =====`). Read a page whenever a step cites it and you need the original wording; the PDF is beside it.
5. `CLAUDE.md` — conventions for this repo.

## Objective of this session
Complete build stage **B0** (foundations, steps 1–9b) and **B1** (the five "clay" plays as manual commands, steps 10–15). Do not start B2 in this session. Everything here must work locally on the owner's Windows PC with no CI (decision 1: CI arrives in B3).

## Deliverables (in order)
1. `docs/OPERATING_MODEL.md` reviewed against the guide and finalised (step 1) — it is already drafted; edit, do not rewrite.
2. Repo scaffold (step 2): `plugin/` and `template/` layout exactly as in `CLAUDE.md`; `tasks.py` task runner; `pytest` + `ruff` wired; a first passing test.
3. `docs/NOTES.md`: the verified answer to "how does Claude Code on Windows invoke hook commands" and the chosen way to run Python hooks from `.claude/settings.json` (step 2, decision 7). Check the Claude Code docs (hooks reference) before writing a hook. Also record whether the current docs allow CI authentication with a Max subscription (decision 1) — read only, no assumption.
4. Conventions implemented (step 9): `changes/<id>-<slug>/` layout, `status.yaml` schema (phase, profile override, change type, gate result, parked reason, iteration count), branch names `sdlc/<id>/<phase>`, label names. A small Python module `plugin/state/` reads and writes them.
5. Template files (steps 2, 9a, 9b, 10, 13): `template/sdlc.yaml` (profile + phase adapters, documented), `template/CLAUDE.md` skeleton (Commands with healthy output · Conventions · Architecture · Things Claude gets wrong · Verifying your work block from article p.28), `template/REVIEW.md` (article p.34 structure plus the rules in the guide's step 26), `template/changes/README.md`.
6. Skills (steps 10, 20 — only the intent template now): `plugin/skills/intent-template/SKILL.md` with the article's sections (Problem · Proposed outcome · Affected users and systems · Constraints · Open questions; header Author/Status; plus change id, entry route idea/ticket/incident, and an Evidence section for incidents). Test that it triggers.
7. Commands (steps 11, 12): `/sdlc-plan` (brainstorm → intent.md via the skill → owner corrects → commit on `sdlc/<id>/a` and open the PR) and the plan.md template + interrogation prompt (files that change · order of work · risks · options not taken · proof), used later by `/sdlc-design`. `/sdlc-design` itself is B3 — do not build it yet.
8. Feedback loop (step 14): `/sdlc-init` must detect or create one-command build/test/lint targets in the target project; implement the detection for Python projects first.
9. Hooks (step 15) in Python: protected-path deny (always including `.claude/**`, `CLAUDE.md`, `REVIEW.md`, the hook scripts), formatter/lint on edit, secrets-pattern check, plan.md-sync pre-commit check. Unit-test each hook with sample tool inputs.
10. Settings (step 7): `template/.claude/settings.json` with the allow-list (git, build, test, lint), deny-list (`.env*`, secrets, WebFetch, curl, wget), sandbox where available; plus a documented user-level managed settings file for the owner's machine.
11. `/sdlc-init` (step 21) — minimal version: copies the template, asks profile + adapters, writes `sdlc.yaml`, runs `/init` and trims `CLAUDE.md`, installs hooks/settings, commits as the project's first PR. Idempotent.

## How the framework is tested (three layers — build layer 1 and 2 in this session)
1. **Self-tests, no project and no model** (`pytest` in this repo): every hook with sample tool inputs, the confidence-gate deterministic checks, the `plugin/state/` module (status.yaml, labels, branch names), template rendering, the detection script's statistics. This is most of the framework and must be green on every commit.
2. **Fixture project** — `tests/fixtures/sample-python-project/`: a tiny Python package (one module, one passing test, one intentionally failing test behind a flag, a `.env` to prove the deny rules). Integration tests run `/sdlc-init` and the phase commands against a temporary copy of it, with the model calls replaced by recorded outputs where possible, and assert on the files, branches, labels and status.yaml they produce. Create this fixture in this session and use it for the definition of done below.
3. **Evals and shakedown (later, B5)**: the article's eval suite runs the real model on real tasks (20–50, collected from actual use), and the shakedown sessions run the framework on a real project. Neither exists on day one; do not simulate them.

## Definition of done for this session
- `python tasks.py test` and `python tasks.py lint` are green on Windows and Linux.
- The fixture project can be initialised with `/sdlc-init` from a temporary copy, and `/sdlc-plan` produces a committed `changes/<id>-<slug>/intent.md` on branch `sdlc/<id>/a` with an open PR.
- Every hook has a unit test; the protected-path hook demonstrably blocks an edit to `.claude/settings.json`.
- `docs/NOTES.md` answers the two verification questions above with links to the docs consulted.
- A `docs/PROGRESS.md` lists each B0/B1 step with done / partial / not started and what is left for B2.

## Rules for this session
- Never reopen a decision in `docs/DECISIONS.md`; if a decision is technically impossible, document why in `docs/PROGRESS.md` and continue with the rest.
- When something in the article is needed, cite the PDF page in code comments or docs.
- Do not add notifications of any kind. Do not use bypass-permissions mode.
- The owner reviews once the session is done. End with a ≤5-bullet summary at the top of `docs/PROGRESS.md`; the long version goes below it.
