# Progress — R14's turn: change 0004's intent refreshed, this repository's pin move prepared (2026-10-23)

This session is lane B of wave 4, started by the central session (`session_016NLfdsdfTFZUyrVGN4Ektc`) at the owner's request. Its candidate is ROADMAP R14, built as change 0004 through the framework's own phases: the owner's merge of PR #173 (branch `sdlc/0004/a`, the intent) starts the design run in CI. This session prepares that merge and stops before it. The owner's answers that set the scope are registered by the central session as choice 269: prepare #173 and stop before it; move this repository's pin to `main`'s version before #173 merges. This session takes no choice, note, decision or version number: its PR changes no file under `plugin/` or `template/`.

The parallel lane, lane A, builds R26 in `plugin/gate/checks.py` and `plugin/pr/description.py`; this session changed no plugin code.

## What was done on #173
1. **`main` merged into `sdlc/0004/a`** with a merge commit, `38fcd57` (`main` at `b9dbd9b`, plugin 1.0.38), never a rebase or a force-push. The branch was 1033 commits behind (`git rev-list --count`). The merge was clean: the branch adds only `changes/0004-drive-target-and-proof-items/`.
2. **The intent refreshed by hand**, with the `intent-template` skill, in `adf53ec`. The changes:
   - **Header and Problem**: Status `proposed` (the owner corrected it through choice 246's answers); read at `b9dbd9b`, plugin 1.0.38; the claims re-checked against today's code (`commands_from_config`, the Proof prose with R15's `ratchet:` line, `EVIDENCE_SCREENSHOTS` read by `collect.py` only, the verifier at (c) and (d) only).
   - **Choice 246 carried** into Proposed outcome and removed from Open questions: Q1 (two folders, one owner each), Q4 (`detect.node_dependencies`, R33's helper, 1.0.29), Q5 (`/sdlc-test` step 3 follows the drive), Q3's first half (a `proof` entry of its own).
   - **Q2 answered on the code of 1.0.38.** As the workflow comments count the phase step, build and fix need 245 of 260 minutes, test 185 of 200, deploy 355 of 355. A set drive at the default 900 s fills build, fix and test exactly and takes deploy to 370, past the 360 a GitHub-hosted job may run. The intent counts only a set drive, gives it its own `gate.drive_timeout` (300 s proposed), and takes its minutes at (e) out of the session's cap through `limits.run_caps`. It names three costs the comments do not count: the setup step (15 minutes), the R18 triage step (5) and a fix round at (e), which runs R51's re-check (45) first.
   - **Q3's second half provisional**: the `proof` entry's shape is written out as R19's contract; R11 is accepted, not built.
   - **The registered items 5 to 10**: R29's `Mock:` line and `## Examples/References` (the intent has the section); R18's `logs_for` gets `drive.log` and the manifest; R44's environment (`commands_env`, the `commands.env` names; R51's and the release's re-checks of `commands_from_config` must not gain the drive); R24's banner stays the risk list's and `auto_round.red_targets` must start a round on a failed `proof` entry; R33's helper reused; R19's contract.
   - **Constraints**: "After R10" marked met (1.0.3, PR #220); the design run runs on this repository's pin, which moves first; the decisions kept now cite 37 (one review mode) and 35 (the banner); the step's environment is today's `commands_env`, where the old sentence about the token in `.git/config` no longer holds (no checkout persists a credential, decision 33).
3. **Gate (a), dry run**, on the branch against `origin/main`: `wait`, every check ok (limits, artifacts, evidence_links, design_scope, guardrails, risk_list).
4. **`python tasks.py verify`** on the branch: build, lint, docs-lint, version-check, test and plugin validate all ok.
5. **#173 is not merged, not labelled**, and no phase was started.

## The fresh-context review of the intent
A general-purpose sub-agent with no part in the writing read the intent, the proposal, the A1 revision, the open-questions file, the ROADMAP rows and the code at 1.0.38 (report only). It confirmed every name, file and function the intent cites, the Q2 figures as the workflow comments count them, choice 246's carry and D1 to D12. Its fourteen findings, all applied before the push:
1. The setup and triage steps are outside the comments' count (build today 265 of 260 at worst; deploy 360 with triage): named.
2. A fix round at (e) runs R51's re-check first (290 of 260 today): named.
3. A deploy job at 360 cannot hold the triage step, and a cut of the runner's kill alone removes only the grace: the cut goes through `limits.run_caps`.
4. The drive's timeout was named two ways: `gate.drive_timeout` in both places; three keys, not "two and one".
5. At (c) `write_deferred_logs` writes only the marked logs: the step writes `drive.log` at (c), (d) and (e).
6. `run_deferred_commands` replaces only deferred entries, and a gate run by hand inside a session runs the targets itself: the `proof` entry is deferred or added by the step, and the by-hand gate never runs the drive.
7. The round's request formats only exit codes: it names each failed item, its expected and seen values.
8. R51's check 12 re-checks a moved branch with three targets: the evidence line says the proof is of the manifest's commit.
9. `/sdlc-build`'s instruction to name a screenshot in Proof: added to the affected files.
10. `HEADER_REQUIRED_AT` lists phases, not logs: dropped from the list.
11. Choice 269 has no record yet: it is the central session's to register.
12. R26 runs in parallel, not before: corrected, citing `waves.md`.
13. Decisions 21 and 35 are amended by 37: cited.
14. What `/sdlc-test` step 3 keys on: corrected.

## The pin move, from 1.0.17 to `main`'s version
`plugin.version` in this repository's `sdlc.yaml` (line 104) is 1.0.17. The owner moves it to `main`'s version before #173 merges (choice 269): 1.0.38 at `b9dbd9b`. If lane A's R26 merges first, it is 1.0.39 and the workflow copies are taken from that version.

**What `/sdlc-init` would refresh here.** Its re-run was run on a scratch worktree of `main` at `b9dbd9b` (plugin 1.0.38, R64's refresh), with this repository's values (`--deploy-action none --deploy-production false --maintain-metric ci_test_failure_rate --maintain-source github-actions`):
- **Refreshed (was 1.0.27):** `sdlc-build.yml`, `sdlc-deploy.yml`, `sdlc-design.yml`, `sdlc-detect.yml`, `sdlc-test.yml`. The copies were 1.0.27's text: R18's lines were left out of them for the 1.0.17 pin.
- **Kept as outdated:** `sdlc-fix.yml`, whose setup line lacks R44's `--command-from` and so matches no release. Deleted and re-run, it is written as the template's.
- **Created:** `sdlc-comment.yml` and `sdlc-merge.yml`, which `tests/test_templates.py` says are installed with the pin. Also `sdlc-evals.yml` and `evals/check.py`, which this repository does not take: it runs `framework-evals.yml`, and the test asserts `sdlc-evals.yml` is absent. And `lessons/README.md` and `policies/README.md`, which the move does not need.
- **Unchanged:** `.github/scripts/sdlc_pin.py`, `sdlc-abandon.yml`, `sdlc-digest.yml`, `sdlc-release.yml`, `sdlc-runbook.yml`, `sdlc-scan.yml`, `CLAUDE.md` and `.claude/settings.json`. `changes/README.md` is kept as edited; `evals/README.md`, `REVIEW.md` and `bands.yaml` are kept.
- **`sdlc.yaml`:** the pin, plus the keys 1.0.18 to 1.0.38 added (`commands.env`, `deploy.command`, `deploy.guarded_commands`, `gate.max_panel_calls`, `gate.build_max_turns`, `gate.build_max_wall_clock_minutes`, `hooks.formatters`, `sandbox`). Each added key holds its default, so only the pin and the formatter row change behaviour. `hooks.format_on_edit: true` is kept unread; the R61/R33 record's row replaces it.

**Checked:** on the scratch worktree, with those copies and this PR's test change, `python -m pytest` passed except one test that reads the checkout folder's name (`test_no_session_holds_the_gemini_key_and_the_sandbox_never_reaches_its_host` expects `sdlc-framework`, and the worktree was named otherwise). In this repository's own checkout the name matches.

**The choice 261 settings rows** are already on `main`: `.claude/settings.json` and `template/.claude/settings.json` both hold the five deny lines (lines 12 to 16; the owner's commits `a2ffeca`, merged in #345, and `9460ce0`, merged in #347). Nothing is left of them.

**`tests/test_templates.py`** (this PR): `without_r18`, `R18_BLOCK_RE`, `R18_OUTS`, `COMMAND_FROM` and the two "installed with the pin" exceptions for `sdlc-merge.yml` and `sdlc-comment.yml` are removed, so the copies test and the fix workflow test compare the installed copies with the full template. **This PR's test is red until the owner's rows below are on the same branch**, and the rows turn the old test red without it: the two land together, as one merge.

## Proposed edits for the owner
Made on this PR's branch, `claude/r14-prepare-0004-pin-move`, before it merges.

| Link | Row | What is there now | What it must become |
|---|---|---|---|
| [sdlc.yaml](https://github.com/luissiviero/sdlc-framework/blob/main/sdlc.yaml#L104) | 104 | `  version: 1.0.17` | `  version: 1.0.38` (`main`'s version on the day) |
| [sdlc.yaml](https://github.com/luissiviero/sdlc-framework/blob/main/sdlc.yaml#L98) | 98 | `  format_on_edit: true` | `  formatters: []`, with the comment block `template/sdlc.yaml` puts above it (the R61/R33 record's row) |
| [.github/workflows/sdlc-build.yml](https://github.com/luissiviero/sdlc-framework/blob/main/.github/workflows/sdlc-build.yml) | whole file | 1.0.27's copy, without R18's lines | the template's copy as `/sdlc-init` renders it here (`refreshed (was 1.0.27)`) |
| [.github/workflows/sdlc-deploy.yml](https://github.com/luissiviero/sdlc-framework/blob/main/.github/workflows/sdlc-deploy.yml) | whole file | 1.0.27's copy, without R18's lines | the template's copy as `/sdlc-init` renders it here |
| [.github/workflows/sdlc-design.yml](https://github.com/luissiviero/sdlc-framework/blob/main/.github/workflows/sdlc-design.yml) | whole file | 1.0.27's copy, without R18's lines | the template's copy as `/sdlc-init` renders it here |
| [.github/workflows/sdlc-detect.yml](https://github.com/luissiviero/sdlc-framework/blob/main/.github/workflows/sdlc-detect.yml) | whole file | 1.0.27's copy, without R18's lines | the template's copy as `/sdlc-init` renders it here |
| [.github/workflows/sdlc-test.yml](https://github.com/luissiviero/sdlc-framework/blob/main/.github/workflows/sdlc-test.yml) | whole file | 1.0.27's copy, without R18's lines | the template's copy as `/sdlc-init` renders it here |
| [.github/workflows/sdlc-fix.yml](https://github.com/luissiviero/sdlc-framework/blob/main/.github/workflows/sdlc-fix.yml) | whole file | the template's copy without R18's lines and without `--command-from` | the template's copy as `/sdlc-init` renders it here (delete the file first: the re-run keeps a copy that matches no release) |
| .github/workflows/sdlc-comment.yml | new file | absent | the template's copy as `/sdlc-init` renders it here |
| .github/workflows/sdlc-merge.yml | new file | absent | the template's copy as `/sdlc-init` renders it here (without `vars.SDLC_MERGE_APP_ID` its merge job says so and stops; the owner merges, as today) |

Optional, not needed by the move (each key holds its default): the keys a re-run adds to `sdlc.yaml`, listed under "What `/sdlc-init` would refresh here". Not taken: `sdlc-evals.yml`, `evals/check.py`, `lessons/README.md`, `policies/README.md`.

One way to make every row at once: on the branch, delete `.github/workflows/sdlc-fix.yml`, run `python <framework>/plugin/init/sdlc_init.py --root . --deploy-action none --deploy-production false --maintain-metric ci_test_failure_rate --maintain-source github-actions` from a framework checkout at the target version, remove the four files not taken, and replace `format_on_edit: true` with nothing (the re-run already writes `formatters: []` below it).

## Port list
None: the PR touches no file under `plugin/detect/`, `plugin/ci/run_phase.py` or the detect, runbook and fix workflow templates. The owner's row for this repository's `sdlc-fix.yml` changes an installed copy, not the template.

## What the owner does
| When | Act |
|---|---|
| Now | Add the rows above to this PR's branch; merge the PR when `Framework checks` is green on that head. |
| After that merge | Merge #173 (head `adf53ec`, or its next head if `main` moved and the branch was brought up to date): the design run starts. |
