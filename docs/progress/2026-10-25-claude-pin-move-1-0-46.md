# Progress — this repository's pin move from plugin 1.0.38 to 1.0.46 (2026-10-25)

This session ran on branch `claude/pin-move-1-0-46`, from `main` at `05d9412` (#394, plugin 1.0.46, tagged `v1.0.46` on `05d9412`), as lane D of wave 5, started by the third central session (`session_013TgyuTukXLjdZU3rmrgyRt`) at the owner's request. It is the single pin move the owner chose, after R45's fourth rename PR, and it carries the `status.yaml` migration choice 273 puts in the pin-move PR. This is a documentation and state PR: nothing under `plugin/` or `template/`, no plugin version, no numbered choice, note or decision.

## Why now
- Since #389 this repository's workflow copies pass the phase names, and the pinned 1.0.38 runner refuses them. Verified on #394's merge: SDLC design run 40245262804 and SDLC build run 40245262856 failed; the build job's log ends `sdlc-run-phase: error: argument --phase: invalid choice: 'build' (choose from 'b', 'c', 'd', 'e', 'f', 'fix', 'review', 'triage')` at the step that runs `run_phase.py ... --find-change`, after checking out `refs/tags/v1.0.38`. Run 40231733027, the design run of #389's head, failed the same way (its conclusion read on GitHub; the central session read its log).
- Since #394 the merge workflow's `on-approval` job calls `merge_step.py on-approval`, which 1.0.38 does not have (`docs/progress/2026-10-25-claude-r45-4-files.md`, "In this repository until the pin moves").
- No change is in flight: changes 0000 to 0005 are past their last gate.

## What was built
1. **`changes/0000` to `0005`'s `status.yaml` in the phase names.** Each file was read with the plugin's own `Status.from_dict` and written back with `write_status` (`plugin/state/status.py`), from `git archive v1.0.46 plugin`, by the script below; nothing was edited by hand. What changed:
   - `phase` and `gate.phase`: `a` becomes `intent` (0000), `e` becomes `deploy` (0001 to 0005), through `conventions.phase_name`;
   - `profile_override` and `review_override` are left out (`RETIRED_KEYS`, decision 37: "the next `write_status` leaves them out");
   - change 0000, written by an older installer, gains the fields every later file has, at their defaults (`panel_calls: 0`, `build_pr: null`, ...);
   - no file has `fast_lane` or `risk_acceptances`; `created_at` and `updated_at` are unchanged.
2. **What stays as written, on purpose:**
   - `gate.reason: waiting for the owner at gate (e)` (0002 to 0005): the code derives nothing for it, and `status.WAITING_AT_GATE_E_REASONS` reads it as the merge reason for good ("merged changes keep it", `plugin/state/status.py`).
   - The evidence files with a letter (`gate-e.json`, `panel/b-items.json`, `claude-c.json`, ...) and the panel ledgers' `escalate:` lines: row N39 of `docs/reviews/2026-10-25-names-added-since-decision-39.md` says "Files already written stay as they are; ... a reader over every change's history reads both for good (choice 273)", and its section "The readers the sixth PR keeps" lists N39's readers.
3. **The other files the pinned plugin reads**, checked with `grep` on `05d9412`: `evals/cases/` already carries `ux-and-brand` (#394); `lessons/` holds no renamed name; there is no `policies/` folder; `.claude/settings.json` names none of the old names. `bands.yaml`'s `preapproved` and `go`, read for one release, are the owner's rows below.

## The proof
The migration script, `migrate_status.py`, run with `python -I` against the plugin at the tag (`git archive v1.0.46 plugin`) and this repository:

```text
plugin read from .../v1046/plugin/state/status.py
0000-sdlc-init: phase intent, gate None/None; on the default branch: gate None/None (changed)
0001-split-the-large-docs-with-an-index-each: phase deploy, gate deploy/parked; on the default branch: gate deploy/passed (changed)
0002-security-authz-the-guardrail-self-protec: phase deploy, gate deploy/passed; on the default branch: gate deploy/passed (changed)
0003-lessons-with-frontmatter-and-a-generated: phase deploy, gate deploy/passed; on the default branch: gate deploy/passed (changed)
0004-drive-target-and-proof-items: phase deploy, gate deploy/passed; on the default branch: gate deploy/passed (changed)
0005-dropped-tests-and-eval-cases-are-gate-fi: phase deploy, gate deploy/passed; on the default branch: gate deploy/passed (changed)
6 file(s) migrated
```

After the write, each file loads again, its `to_dict()` equals the one written, and its text equals `yamlish.dumps` of what it loads (the round trip, asserted per file); a second run with `--check` reports `0 file(s) would change`. Each file reads at the default branch as it did before (`read_status(..., on_default_branch=True)`: gate deploy/passed for 0001 to 0005).

The owner's edits were proved in a scratch clone outside this one, from a bare copy standing in for `origin`: the command sequence below ran as written, changed 17 lines in four files (`17 insertions(+), 17 deletions(-)`), committed and pushed. The clone must sit in a folder named `sdlc-framework`, as a Codespace's `/workspaces/sdlc-framework` does: `tests/test_ci.py`'s second-opinion test names the repository by its folder, and a first proof in a folder named `proof` failed it on that alone. Plugin 1.0.46 reads the same values from the old and the new lines (`production_gate` false; `session_model` for design `claude-fable-5-1`, for build `claude-opus-5-5`; the four routes `allow`, `allow`, `allow`, `ask`). `python tasks.py verify` passed in that clone with the edits applied (the PR body), and passes on this branch without them: no check reads the pin.

## The fresh-context review
A fresh-context sub-agent reviewed the migration, the rows and the command sequence (report only). It found nothing blocking. It loaded each `status.yaml` from `05d9412` and from this branch with v1.0.46, on and off the default branch, with `production_gate` false and true: all 24 `to_dict()` results are the same. `pr/counters.collect` gives the same output on both trees. Its findings and what was done:
1. **Fixed:** `REVIEW.md:28` names `evidence/gate-e.json`, which a change cut after the pin move does not have; R45's first record left it out. It is the seventeenth row and the commands carry it.
2. **Noted, nothing to do:** until the merge, the PR's own SDLC design run is red, as on every PR since #389: the workflow reads the pin from `main`'s `sdlc.yaml`, where it is still 1.0.38, and that runner refuses `--phase design` (`RUNNABLE` in `plugin/ci/run_phase.py` at v1.0.38).
3. **Noted:** 1.0.38 refuses every migrated file ("phase must be one of ('a', ...) ... got 'deploy'"); if this PR merged without the owner's commit, `counters` would count the six changes unreadable and detect and scan would skip them. Nothing fails, and the commands commit on this branch before the merge (the order of acts below).
4. **Noted:** the letters left in guardrail comments ("Not in the rows" below).

It also traced the merge of this PR under 1.0.46: `find_change` sees six change folders and skips as ambiguous, so SDLC design and SDLC build skip green; the release skips; `merge_step.py on-approval` exists.

## Proposed edits for the owner
The rows are R45's records (`2026-10-25-claude-r45-1-phase-names.md`, the four rows; `2026-10-25-claude-r45-3-config-values.md`, the eleven rows; `2026-10-25-claude-r45-2-labels-verdict.md` and `2026-10-25-claude-r45-4-files.md` have none for these files), the pin itself, and `REVIEW.md` row 28, which the records left out (the review below): the review pass reads `REVIEW.md`, and from 1.0.43 the gate writes `gate-deploy.json` (`GATE_RESULT = "gate-{phase}.json"`, `plugin/gate/artifacts.py`), as `template/REVIEW.md:28` already says. Each was read again on `05d9412`. The root `sdlc.yaml` has no `external_review` block, so there is no `second_opinion` row; `session_model`'s only letter key is `b`.

| Link | Row | What is there | What it must become |
|---|---|---|---|
| `sdlc.yaml` | 16 | `   b: claude-fable-5-1` | `   design: claude-fable-5-1` |
| `sdlc.yaml` | 41 | `  production: false` | `  production_gate: false` |
| `sdlc.yaml` | 43 | `  # build PR's merge (and, when production is true, after the release label): e.g.` | `  # build PR's merge (and, when production_gate is true, after the release label): e.g.` |
| `sdlc.yaml` | 55 | `  # "python scripts/promote.py"). Only read when production is true.` | `  # "python scripts/promote.py"). Only read when production_gate is true.` |
| `sdlc.yaml` | 63 | `  # runbooks the 3-sigma tier may call; authorization: preapproved (CI-scoped, reversible)` | `  # runbooks the 3-sigma tier may call; authorization: allow (CI-scoped, reversible)` |
| `sdlc.yaml` | 64 | `  # or go (touches a running system; waits for the owner's "Go" as a parked item)` | `  # or ask (touches a running system; waits for the owner's "Go" as a parked item)` |
| `sdlc.yaml` | 143 | `  version: 1.0.38` | `  version: 1.0.46` |
| `bands.yaml` | 20 | `    # radius): preapproved = CI-scoped and reversible, runs with no human in the path;` | `    # radius): allow = CI-scoped and reversible, runs with no human in the path;` |
| `bands.yaml` | 21 | `    # go = touches a running system, parks with "what I need from you" until the owner` | `    # ask = touches a running system, parks with "what I need from you" until the owner` |
| `bands.yaml` | 25 | `        authorization: preapproved` | `        authorization: allow` |
| `bands.yaml` | 27 | `        authorization: preapproved` | `        authorization: allow` |
| `bands.yaml` | 29 | `        authorization: preapproved` | `        authorization: allow` |
| `bands.yaml` | 31 | `        authorization: go` | `        authorization: ask` |
| `CLAUDE.md` | 3 | `... with human gates at (a), (b) and (e), and the owner's triage at (f). ...` | `... with human gates at intent, design and deploy, and the owner's triage at maintain. ...` |
| `CLAUDE.md` | 19 | `` - `plugin/commands/`: /sdlc-init, /sdlc-plan, /sdlc-design, ... `` | `` - `plugin/commands/`: /sdlc-init, /sdlc-intent, /sdlc-design, ... `` |
| `REVIEW.md` | 27 | `` - Each added skip marker the gate's `ratchets` check listed at gate (e) `` | `` - Each added skip marker the gate's `ratchets` check listed at gate (deploy) `` |
| `REVIEW.md` | 28 | `` (`evidence/gate-e.json`'s `details.skip_markers`) must be declared in `plan.md` or `` | `` (`evidence/gate-deploy.json`'s `details.skip_markers`) must be declared in `plan.md` or `` |

The same edits as commands, for a GitHub Codespace (bash) on this branch; the `git diff --stat` line must read `4 files changed, 17 insertions(+), 17 deletions(-)` before the commit:

```bash
git fetch origin claude/pin-move-1-0-46 && git checkout claude/pin-move-1-0-46 && git pull --ff-only origin claude/pin-move-1-0-46
sed -i \
  -e 's/^   b: claude-fable-5-1$/   design: claude-fable-5-1/' \
  -e 's/^  production: false$/  production_gate: false/' \
  -e 's/^  # build PR.s merge (and, when production is true, after the release label): e\.g\.$/  # build PR'"'"'s merge (and, when production_gate is true, after the release label): e.g./' \
  -e 's/^  # "python scripts\/promote\.py")\. Only read when production is true\.$/  # "python scripts\/promote.py"). Only read when production_gate is true./' \
  -e 's/^  # runbooks the 3-sigma tier may call; authorization: preapproved (CI-scoped, reversible)$/  # runbooks the 3-sigma tier may call; authorization: allow (CI-scoped, reversible)/' \
  -e 's/^  # or go (touches a running system; waits for the owner.s "Go" as a parked item)$/  # or ask (touches a running system; waits for the owner'"'"'s "Go" as a parked item)/' \
  -e 's/^  version: 1\.0\.38$/  version: 1.0.46/' \
  sdlc.yaml
sed -i \
  -e 's/^    # radius): preapproved = CI-scoped/    # radius): allow = CI-scoped/' \
  -e 's/^    # go = touches a running system,/    # ask = touches a running system,/' \
  -e 's/^        authorization: preapproved$/        authorization: allow/' \
  -e 's/^        authorization: go$/        authorization: ask/' \
  bands.yaml
sed -i \
  -e 's/with human gates at (a), (b) and (e), and the owner.s triage at (f)\./with human gates at intent, design and deploy, and the owner'"'"'s triage at maintain./' \
  -e 's|^- `plugin/commands/`: /sdlc-init, /sdlc-plan, /sdlc-design,|- `plugin/commands/`: /sdlc-init, /sdlc-intent, /sdlc-design,|' \
  CLAUDE.md
sed -i \
  -e 's/^\(- Each added skip marker the gate.s `ratchets` check listed at gate \)(e)$/\1(deploy)/' \
  -e 's/^  (`evidence\/gate-e\.json`.s `details\.skip_markers`)/  (`evidence\/gate-deploy.json`'"'"'s `details.skip_markers`)/' \
  REVIEW.md
git diff --stat -- sdlc.yaml bands.yaml CLAUDE.md REVIEW.md
git commit -am "Pin move to plugin 1.0.46: the guardrail lines" && git push origin claude/pin-move-1-0-46
```

Not in the rows: the letters left in comments and prose that no plugin reads (`sdlc.yaml` lines 6 to 8, 40 and 119; `CLAUDE.md` lines 24 and 34; `bands.yaml` line 3). R45's records did not list them; they can go with a later prose PR or the owner's own edit. If lane A's fifth rename PR merges first and changes one of these four files, this PR merges `main` and the rows are read again before the owner's commit.

## Order of acts
1. The owner runs the commands above on this branch (or edits by the table), which commits the guardrail lines on it.
2. `Framework checks` runs on that head; the owner approves the runs if they wait at `action_required`.
3. The owner merges this PR: the pin and the migrated `status.yaml` files reach `main` together.

## What the owner checks after the merge
- This PR's own merge, and the next one after it, run SDLC design and SDLC build with the 1.0.46 runner (the pin is read from the default branch at run time): each is green or skipped, never the `invalid choice` failure above. This PR touches six change folders, so its find step skips as ambiguous.
- The next approving review on a PR runs the merge workflow without `invalid choice: 'on-approval'`.
- `python plugin/state/cli.py list` (or the digest) shows changes 0001 to 0005 at `deploy`, gate deploy/passed.

## Port list
This PR touches none of `plugin/detect/`, `plugin/ci/run_phase.py` or the detect, runbook and fix workflow templates.

## Citations
Checked against their targets (choice 241): runs 40245262804, 40245262856 and 40231733027 (GitHub, read at about 23:50 UTC); #389, #394 and their records; decision 39's point 1 and choice 273; row N39 and "The readers the sixth PR keeps"; `RETIRED_KEYS` and `WAITING_AT_GATE_E_REASONS` in `plugin/state/status.py` at `05d9412`.
