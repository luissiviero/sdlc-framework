# SDLC framework

A Claude Code plugin (`plugin/`) plus a project template (`template/`) that drives any project through plan → design → build → test → deploy → maintain with profile-based human gates. `docs/OPERATING_MODEL.md` is the contract; `docs/PROGRESS.md` says what exists after each build session; `docs/NOTES.md` holds the platform facts verified against the Claude Code docs; `docs/MODEL_ALLOCATION.md` says which build-session tasks run on Fable and which on Opus sub-agents.

- Tests and lint: `python tasks.py check` (or `test` / `lint` / `format`).
- Try the plugin in a project: `claude --plugin-dir <path-to-this-repo>` (the repository root is the plugin root; `.claude-plugin/plugin.json` points at `plugin/`), then `/sdlc:sdlc-init`.
- The framework installs itself into a project by declaring the marketplace in the project's `.claude/settings.json` (done by `/sdlc-init`), so cloud sessions and the owner's PC load the same pinned plugin.
- What a project gets (after B2): commands `/sdlc:sdlc-init`, `/sdlc:sdlc-plan`; agents `sdlc:verifier`, `sdlc:code-simplifier`, `sdlc:researcher`, `sdlc:adversarial-reviewer`; skills `intent-template`, `plan-template` and the five policy skills (`coding-standards`, `security-baseline`, `ux-conventions`, `data-conventions`, `definition-of-done`, each with a `check.py`); the guardrail hooks; and the deterministic gate tools, all called as `python "${CLAUDE_PLUGIN_ROOT}/plugin/<pkg>/<script>.py"`:
  - `state/cli.py` — change folders, `status.yaml`, phase branches, `accept-risk`;
  - `gate/cli.py check --root . --id 0001 --phase c` — the confidence gate (exit 0 continue, 3 wait at a human gate, 4 park), plus `start-run`, `record-spend`, `set-iterations` for the run limits;
  - `gate/preflight.py --root .` — whether the implementation run may use `--permission-mode acceptEdits` (never bypass mode).

## Starting pack (session 1 input)

The files below were the input to the first build session; that session's brief is `docs/handoffs/session-1-B0-B1.md`.

| File | What it is | Used by |
|---|---|---|
| `HANDOFF.md` | Brief for the **next** build session (now: session 3, B3); earlier briefs are kept in `docs/handoffs/` | the session |
| `CLAUDE.md` | Conventions for this repo (English only, Python hooks, plugin/template layout) | every session |
| `docs/OPERATING_MODEL.md` | The contract: phases, artifacts, profiles, gates, park-never-page, conventions (draft to finalise in step 1) | the framework itself |
| `docs/DECISIONS.md` | The 20 settled decisions with alternatives and reasons | sessions, to avoid reopening them |
| `docs/BUILD_GUIDE.md` | The 46-step build plan with article citations (Markdown) | sessions |
| `docs/build_guide.json` | Same data, machine-readable (`id`, `group`, `where[{p,s}]`, `phase`, `importance`, …) | scripts, progress tracking |
| `docs/reference/ai-native-sdlc-playbook.pdf` | The source article | citations |
| `docs/reference/ai-native-sdlc-playbook.txt` | Page-tagged text of the article (`===== PAGE N =====`) | grep-able citations |
| `docs/reference/playbook-p8-dependency-graph.png` | The adoption-order figure (article p.8) | build order |

Testing: layer 1 = self-tests without a project or a model; layer 2 = a fixture project inside the repo (`tests/fixtures/sample-python-project/`) for integration tests of `/sdlc-init` and the phase commands; layer 3 = evals and shakedown on a real project (B5). See the current `HANDOFF.md` and `docs/PROGRESS.md`.

Sessions after the first: write a new `HANDOFF.md` per build stage (B2 … B5) from `docs/PROGRESS.md`, keeping the same structure, and move the previous brief to `docs/handoffs/`.
