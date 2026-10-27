# Progress — the third central session closes wave 5: choices 276 to 280 (2026-10-26)

This session ran on branch `ccr-ca9f0149-a29zgl`, restarted from `main` at `57b6ee7` (#401). It is a documentation PR: no plugin version, no file under `plugin/` or `template/`.

## The owner's choices
276. **A lane writes the "Names since R45" block into each unbuilt proposal** (the owner, 2026-10-25, this session, quoting the central session's sentence about the candidates written before R45's names: "Shouldn't we open a session that edits these to the names set by 45?", then "ok, after PR 5 with the block approach"). The lane (wave 5's lane E) added the block under the title of each unbuilt proposal and of decision 41, and annotated their ROADMAP rows; no sentence of a proposal was rewritten (decision 39, choice 126). Merged as #397.
277. **This repository's pin moves once, after R45's fourth PR** (the owner, 2026-10-25, this session, accepting the recommendation). The move to 1.0.46 merged as #395, with `changes/*/status.yaml` in the phase names (choice 273). The pin is still 1.0.46 on `main` at `57b6ee7`.
278. **The trial follows the trial readiness re-check's six recommendations, T1 to T6** (the owner, 2026-10-25, this session: "#392 merged / I accept all recommendations"; `docs/reviews/2026-10-25-trial-readiness-recheck.md`, "The owner's decisions the trial still needs"). T1's "a repository the owner works in" is amended by choice 280.
279. **Successor lanes start without asking, and their cost is not a concern** (the owner, 2026-10-25, this session: "Using successor approved / Never mind the cost"). Wave 5 ran lanes E, F, G and H under it: the names blocks (#397), the sample's pin move (luissiviero/sdlc-sample-python#102), R45's sixth PR (#399) and R67 (#400, #401).
280. **The trial repository is a near-empty Python project** (the owner, 2026-10-26, this session: "I want the repo as empty as possible, only the least amount of information to test the plugin. If that means an empty repo, so be it."). It amends choice 278's T1 ("a repository the owner works in"). The repository holds the smallest project `/sdlc-init` detects with no input: `pyproject.toml`, one package module, one test, `README.md`, `.gitignore` and the project's own `ci.yml`, which runs lint and the tests on `pull_request` and on pushes to `main` and is the one workflow the maintain metric counts (T1). What the project builds arrives as intents. The session gave the owner a reset script for it, proved on a stand-in repository; the owner has not yet named the repository.

## What was written
1. **`docs/handoffs/waves.md`**: wave 5's row is merged, with its PRs and versions.
2. **The end file**, `docs/handoffs/sessions/2026-10-26-ccr-ca9f0149-a29zgl-end.md`: the merges, what the wave taught, the trial's next steps and every open item.

## Checked
- After `git fetch origin` on `57b6ee7`: `python tasks.py next-free` gave choice 276, and `python tasks.py version-check` exits 0 with no branch above `main`.
- The tags: `v1.0.48` on `ae604a6` (#399), `v1.0.49` on `0fb7b99` (#400) and `v1.0.50` on `57b6ee7` (#401) (`git ls-remote origin 'refs/tags/v1.0.4*' 'refs/tags/v1.0.5*'`).
- The sample's `main` is at `3fc88fa` (#103), pinned at 1.0.47 (`sdlc.yaml:121`, read after #102 merged as `76a06e3`).
- The reset script for the trial: run against a local bare stand-in holding two files, it listed them, asked, removed them, wrote the six files, passed `ruff check` and the one test, and pushed; `/sdlc-init --detect-only` on the result found `python`, the lint target `python -m ruff check .` from the ruff configuration and the build target `python -m compileall -q .`.

## What the owner does
| When | Act |
|---|---|
| Now | Merge this PR when `Framework checks` is green on its final head. |
| Next | The trial's first steps, in the end file's "Next steps". |
