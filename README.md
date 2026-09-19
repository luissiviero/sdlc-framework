# SDLC framework — starting pack

Copy the contents of this folder into the root of the new framework repo, then open a Claude Code session there and start with: "Read HANDOFF.md and execute session 1."

| File | What it is | Used by |
|---|---|---|
| `HANDOFF.md` | Brief for the first Claude Code session (B0 + B1), deliverables and definition of done | the session |
| `CLAUDE.md` | Conventions for this repo (English only, Python hooks, plugin/template layout) | every session |
| `docs/OPERATING_MODEL.md` | The contract: phases, artifacts, profiles, gates, park-never-page, conventions (draft to finalise in step 1) | the framework itself |
| `docs/DECISIONS.md` | The 20 settled decisions with alternatives and reasons | sessions, to avoid reopening them |
| `docs/BUILD_GUIDE.md` | The 46-step build plan with article citations (Markdown) | sessions |
| `docs/build_guide.json` | Same data, machine-readable (`id`, `group`, `where[{p,s}]`, `phase`, `importance`, …) | scripts, progress tracking |
| `docs/reference/ai-native-sdlc-playbook.pdf` | The source article | citations |
| `docs/reference/ai-native-sdlc-playbook.txt` | Page-tagged text of the article (`===== PAGE N =====`) | grep-able citations |
| `docs/reference/playbook-p8-dependency-graph.png` | The adoption-order figure (article p.8) | build order |

Testing: layer 1 = self-tests without a project or a model; layer 2 = a fixture project inside the repo (`tests/fixtures/sample-python-project/`) for integration tests of `/sdlc-init` and the phase commands; layer 3 = evals and shakedown on a real project (B5). See `HANDOFF.md`.

Sessions after the first: write a new `HANDOFF.md` per build stage (B2 … B5) from `docs/PROGRESS.md`, keeping the same structure.
