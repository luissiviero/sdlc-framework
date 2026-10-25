# Progress — R45's first rename PR: the phases named after what they produce (2026-10-25, plugin 1.0.43)

This session ran on branch `claude/r45-1-phase-names`, from `main` at `11d5661` (#385, plugin 1.0.42), as lane A of wave 5 (choice 273). It is section 12's PR 1 of `docs/reviews/2026-10-20-names-against-the-article.md`, as decision 39's point 4 amends it, with rows N38 to N40 of `docs/reviews/2026-10-25-names-added-since-decision-39.md` (#387). Plugin **1.0.43** (`python tasks.py next-free` after `git fetch origin`). No numbered choice, note or decision is taken.

## What was built
1. **One reader of the letters** (`plugin/state/conventions.py`): `PHASES` is `intent`, `design`, `build`, `test`, `deploy`, `maintain`; `phase_name` turns a letter (a) to (f) into its name and leaves any other value as it is. Every reader passes what it reads through it: `status.yaml`'s `phase`, `gate.phase`, `fast_lane` keys and `risk_acceptances[].details.phase` (`Status` and `Gate` on construction), every `--phase` (`type=c.phase_name`, so an old workflow copy's `--phase c` runs the build), branches (`parse_branch` reads `sdlc/<id>/c` and `sdlc/<id>/build`), labels (`ready_label_phase`, `ready_labels`), `sdlc.yaml: session_model` keys and `external_review.phases` (`[b, e]` still works), gate records, verdict files, panel ledgers, run and spend records. Evidence files are read with `phase_file`, which takes the letter's file only when the name's is missing; every writer writes the name.
2. **A change in flight keeps its letter branch**: `gitops.existing_branch` picks `sdlc/<id>/c` when it exists and `sdlc/<id>/build` does not, for the runner's checkout, push, hand-over and dispatch, `state/cli.py commit-phase`, the PR upsert and the release record; a PR is looked up by both heads, the name's first. The merge workflow's two `'/c'` tests and the runbook workflow's `'/a'` test accept both suffixes.
3. **The names the owner sees**: branches `sdlc/<id>/<name>`, labels `sdlc:<name>-ready`, the check run `sdlc/<name>`, the evidence files (`gate-build.json`, `adversarial-review-build.json`, `run-build.json`, `claude-build.json`, `diff-design.patch`, `decisions-design.json`, `panel/design-1-reviewer.md`, `evidence/roles/security-policy-deploy.md`, ...), the commit subjects `run(<name>): ...`, the generated sentences ("Gate (deploy) parked change 0001", "waiting for the owner at gate (deploy)", "merged at gate (deploy)"), the workflow display names ("SDLC design", "SDLC merge (deploy)", N4) and step names ("Check gate (deploy) and merge", N3), the second opinion's phase (N12), the brief's file name and heading (N17), the digest's "Maintain: runbook and dismissal PRs" (row 67's phase part) and the counters' gate letters (N38).
4. **`/sdlc-intent`** (row 8): `plugin/commands/sdlc-intent.md` is the former `/sdlc-plan`; `sdlc-plan.md` stays one release as a command that only points to it (choice 273). Row 86: "the read-only planning run" is "the planning run".
5. **The readers of history** (choice 273) read both forms for good: `detect/cli.py` and `scan/route.py` read `origin/sdlc/<id>/a` and `/intent`; `counters.py` counts a change at `deploy` (a letter `e` is read as `deploy`); the old reason "waiting for the owner at gate (e)" is read as the merge reason on the default branch (`status.WAITING_AT_GATE_E_REASONS`).
6. **Not in this PR**, by section 12's order: `incident`, `schedule`, `escalate` and the triage session (PR 2), `external_review`'s key name (PR 3), `doorbell` and "fallback C1" (PR 4), the rulesets and the roles (PR 5). This repository's `changes/*/status.yaml` keep their letters: each repository migrates them in its own pin-move PR (choice 273).

## How it was built
The shared API (`conventions.py`, `status.py`, `gitops.py`) was written first, as its own commit ("readers"); four sub-agents then converted the rest in parallel, each on a disjoint set of files and the tests that cover them (the runner; the gate, panel and hooks; the PR, release, detect and scan modules; the commands, skills and templates), and this session merged their work, bumped the version, regenerated `plugin/init/template_hashes.json` (`python tasks.py template-hashes`, with every `v*` tag fetched) and ran the suite. Tests that asserted the old names now assert the new ones; none was deleted or skipped; each group added tests that its readers still accept the letters.

## The fresh-context review
A fresh-context sub-agent reviewed the whole diff (report only): mangled replacements, readers that refuse letters, in-flight branches, writers, prose, weakened tests, Windows. It found nothing blocking: no file mode, sha or flag was replaced, every `--phase` takes `phase_name`, no test was removed or skipped. Its findings and what was done:
1. **Fixed:** an old workflow copy filters the build PR on `/c` and the incident PR on `/a`, so a project that moves its pin past 1.0.42 without its copies never merges or runs a runbook for a change cut with the names. `/sdlc-init`'s upgrade text and `conventions.py` now say the copies move with the pin, in the same PR.
2. **Fixed:** the id reservation passed the letter `'a'` to `branch_name` (`plugin/state/gitops.py`); it passes `conventions.INTENT`.
3. **Fixed:** the release job's red-merge message named `/sdlc-plan`; it names `/sdlc-intent`, as do four docstrings.
4. **Optional, taken:** the preflight test now writes the letter's verdict file it said it tested, and the report names the file it read; `conventions.py` says the letter mapping stays for the readers of history.
5. **Optional, not taken:** a test of the fast lane on letter branches (the reviewer's probe passed: `stacked_design` found `sdlc/0001/b`, the build was cut from it); preferring the branch with an open PR in `gitops.existing_branch` over a stray name branch (on a runner a pushed stray is caught by `session_push_mismatches`); the order in `fix_branch_for` (every template fetches with `fetch-depth: 0`); "phase (build)" beside "the build phase" in two sentences.

## The window in this repository
This repository's pin is 1.0.38 (`sdlc.yaml`), and its `.github/workflows/` copies must equal the rendered templates (`tests/test_templates.py`). Once the owner commits this PR's copies, they pass `--phase build` and the other names to the pinned 1.0.38 runner, which refuses them. No change is in flight here (changes 0000 to 0005 are all past their last gate), so the window costs nothing as long as no change starts before this repository's pin moves to 1.0.43 or later. The sample moves its copies and its pin together (`/sdlc-init`'s upgrade, R64), so it has no such window.

## Port list
This PR touches `plugin/ci/run_phase.py`, `plugin/detect/` and the detect, runbook and fix workflow templates: it goes on the port list until the 1.0.0 read.

## Proposed edits for the owner
The workflow copies are in the PR body ("What I need from you"). The guardrail lines below are for this repository's pin-move PR; letters keep working until the sixth PR, so none is urgent.

| Link | Row | What is there | What it must become |
|---|---|---|---|
| `sdlc.yaml` | 16 | `   b: claude-fable-5-1` | `   design: claude-fable-5-1` |
| `CLAUDE.md` | 3 | `... with human gates at (a), (b) and (e), and the owner's triage at (f). ...` | `... with human gates at intent, design and deploy, and the owner's triage at maintain. ...` |
| `CLAUDE.md` | 19 | `` - `plugin/commands/`: /sdlc-init, /sdlc-plan, /sdlc-design, ... `` | `` - `plugin/commands/`: /sdlc-init, /sdlc-intent, /sdlc-design, ... `` |
| `REVIEW.md` | 27 | `... the gate's \`ratchets\` check listed at gate (e)` | `... the gate's \`ratchets\` check listed at gate (deploy)` |

The sample's guardrail lines (`sdlc.yaml`, `CLAUDE.md`, `REVIEW.md`, `bands.yaml`) are read at its own pin-move PR, from the sample's `main` then.

## What the owner does
| When | Act |
|---|---|
| Now | Commit the workflow copies on `claude/r45-1-phase-names` (the PR body's table), then merge the PR when `Framework checks` is green on its final head. |
| Before merging | Check whether any ruleset of this repository or the sample requires a check run by its old name (`sdlc/c`, `sdlc/e`): the check run is now `sdlc/build`, `sdlc/deploy` (section 12, PR 1). |
| Until this repository's pin moves past 1.0.42 | Start no change here. |
