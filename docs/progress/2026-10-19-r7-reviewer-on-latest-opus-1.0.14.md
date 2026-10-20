# Progress — ROADMAP R7, the in-run reviewer on the latest Opus, as plugin **1.0.14**; the runs PR read against plugins 1.0.3 to 1.0.13 (2026-10-19)

This session ran on branch `ccr-e4a1d6f8-lgxd25`, from the owner's task of 2026-10-19: first a read-only look at what "the runs PR" still holds, then R7's plan checked against today's code, then, after the owner's "go", R7 built as a session pull request with an independent fresh-context review (framework candidates do not go through the framework's own pipeline: the owner's rule of 2026-10-16). The previous record (the Order before the real-project trial, choice 238, PR #252) is now `docs/progress/2026-10-19-order-before-the-trial-and-choice-238.md`, unchanged. The session's own file is `docs/handoffs/sessions/2026-10-19-ccr-e4a1d6f8-lgxd25.md`.

A change under `plugin/` and `template/`: plugin **1.0.14** (`.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`), the next free patch number (choice 184): no other branch on origin carried a bump when this PR was opened (R56 has no branch yet).

## Step 1: what "the runs PR" still holds
Read on `main` at `7960377` (plugin 1.0.13) against choice 180 (`docs/progress/session-25.md`), NOTES §38, decision 28 and session 25's "Known gaps" (listed "for the 0.3.8 runs PR"). Nothing was built from it.

| Item | Done in which PR/version, or still open | Evidence |
|---|---|---|
| 1. The turn cap as a hard park, a higher default for (c) | Partly. The higher cap: 1.0.8 (#233, R48, decision 32, `build_max_turns` 400). A capped fix round parks since 1.0.10 (#238). **Open:** a (b)/(c)/(d)/(e) session capped before its gate leaves no park record, label or PR body | `plugin/gate/limits.py:58`; `run_phase.py` (`park_unfinished_round` for `fix` only; every other phase ends in `report_failed_run`) |
| 2. The label race | **Open**: `apply-labels` has no runner guard; no second label read before `verify_owner_fields`. Choice 218 only narrowed whose label counts | `plugin/state/cli.py` (`cmd_apply_labels`), `plugin/state/unpark.py` (`apply_from_pr`), `run_phase.py` (`verify_owner_fields`, `owner_field_mismatches`) |
| 3. A re-run keeps the capped run's wall clock | **Open**: the runner never writes `started_at` (`stamp_run_record` refuses to create one); only the session's `start-run` resets it (`sdlc-build.md` step 1). A fix round resets it (`sdlc-fix.md` step 2) | as cited |
| 4. The (e) park text sends the owner to a dispatch that refuses | **Open, and spread**: `DEFERRED_PARK_NEED` unchanged; 1.0.3 (#220, R10) copied the words into `COMMANDS_CRASH_NEED` (`plugin/gate/gate.py`). Since 1.0.10 an `sdlc-fix.yml` dispatch runs a round, but the text names no workflow; `sdlc-deploy.yml` still skips at (e) (NOTES §39) | as cited |
| 5. A round bumps the counter before its own review pass | **Open**: `/sdlc-fix` step 2 bumps; at (e) its step 3 runs `/sdlc-deploy` step 2's loop, which bumps per Important finding | `plugin/commands/sdlc-fix.md`, `sdlc-deploy.md` |
| 6. A turn-capped fix round hides the gate's real park | Partly, 1.0.10 (#238): the park says "failed after its gate (…error_max_turns)" and keeps the work; the gate's own reason is still replaced (`keep_failed` keeps risk-hit checks only) | `run_phase.py` (`AFTER_GATE_PARK`, `park_and_publish`) |
| 7. The gate's lint target misses formatting | **Done**: the owner's row, on `main` since #203 (1.0.0) | `sdlc.yaml` line 19 |
| 8. The root `lessons/` folder and ruff's import grouping | Done in change 0002 (`v0.3.7`), carried from session 25's record, not re-verified | `docs/progress/session-25.md` |
| 9. The `as_posix()` rule for the coding-standards skill | **Open** | no `as_posix` or `WindowsPath` under `plugin/skills/` |
| 10. `claude_md_first_time_lines` from a one-off failure | **Open** | `plugin/review/findings.py` unchanged |
| 11. The reviewer's `at` time | Was open on 1.0.13 (NOTES §51); session 24 gave it to R7: **done in this PR** | below |
| 12. The runner's post-session check of `framework/` and the guardrail files | **Open**: `guardrail_changes` runs before the session; after it only the owner fields and the runner's files are compared | `run_phase.py` |
| 13. The template sandbox block (A6, set to ride with the runs PR) | **Open**, waiting for the sandbox proof: no `filesystem.denyWrite` in `template/.claude/settings.json` | that file |

Nothing in R7 depends on the sandbox proof (now R44's first step, rank 12): the reviewer has no shell, the models travel by flag and environment, and the model record is written by a hook process. Only item 13 waits for it.

## Step 2: R7's claims against today's code
- **The reviewer's frontmatter** said `model: inherit`, `maxTurns: 50`, as the proposal read; it had seven angles, not six (skip markers came later).
- **`model_matches`** still matched a full id by prefix both ways, so `claude-opus-5` met a `claude-opus-5-5` pin and the reverse.
- **`--model`** came only from `SDLC_MODEL`, which no workflow sets: every session ran on the CLI's default, `claude-sonnet-5` (NOTES §51).
- **`sdlc.yaml`**: root line 12 and template line 35 `panel_advocate_model: opus`; no `session_model`, no `adversarial_model`.
- **The gate**: `adversarial_review` checked no model; the advocate's model was read from its transcript by the `panel_blind` hook and checked by `panel` and `panel/cli.py record`, as the proposal said.
- **New since the proposal**: decision 29's judge (1.0.3) ran on `panel_advocate_model`, "the adversarial reviewer's model"; the turn caps are 400 (decision 32).
- **What did not hold**: the proposal passed the full id per invocation, but the Agent tool's per-invocation model takes one of four aliases, and the CLI's own `opus` alias resolved to `claude-opus-5` in every CI run on 2.1.278 (NOTES §51). The design below pins the alias instead.
- **"Before the design: two checks on change 0002's build run"** was not repeated: both were answered on 2026-10-09 (NOTES §38: the advocate ran on Opus, the panel worked on 0.3.6) and since (change 0005's panel on 2026-10-16). What no run has shown is `claude-opus-5-5` or `claude-fable-5-1` from this CI on 2.1.278; the new check parks on a mismatch instead of passing, so the first live run after the owner's rows is the reading.
- **Model ids** confirmed with the claude-api skill: `claude-opus-5-5`, `claude-fable-5-1` (NOTES §51).
- **No decision file** (the session's recommendation; the owner said "go" on it): a note beside decisions 11 and 21, not reopening them.

## Summary
- **`plugin/panel/models.py`** (new): per phase, the session's model (`sdlc.yaml: session_model`: one model, or `default` plus per-phase entries; a fix round takes its change's phase, the (e) review pass `e`), the reviewer's (`adversarial_model`) and the advocate's (`panel_advocate_model`, or `adversarial_model` where the session itself runs on the advocate's model, decision 21); the family alias each sub-agent is started with; the `ANTHROPIC_DEFAULT_<FAMILY>_MODEL` pins that make the alias resolve to the configured full id (a pin the workflow sets wins). `panel/cli.py models --phase <p>` prints them for the phase commands.
- **The runner** (`plugin/ci/run_phase.py`): `--model` from `SDLC_MODEL`, else `session_model` for the run's phase (`compose`, `model_phase`); the pins in the session's environment (`session_env`); the panel's model record reads the phase's advocate model and the run's `--model` as the session's; decision 29's judge runs on `adversarial_model`, else `panel_advocate_model` as before.
- **The reviewer's model record**: the `panel_blind` hook writes `evidence/adversarial-review-<phase>.model.json` when the reviewer writes its verdict (the writer, the models of its transcript, the verdict's `head`, the time) and refuses any tool write of it.
- **The gate's `reviewer_model` check** (gates (b) to (e)): with `adversarial_model` set, a verdict needs that record, written by `sdlc:adversarial-reviewer` for the verdict's `head`, on a model that meets the pin; otherwise a hard park (`ledger.NEVER_TO_PANEL`). Unset: not checked.
- **`model_matches`**: a full id is met by itself and its dated snapshots only; an alias still matches its family.
- **The reviewer** (`plugin/agents/adversarial-reviewer.md`): `model: opus`, `maxTurns: 80`, an eighth angle (every claim of `spec.md` and `plan.md` about today's code checked against the merge base: the files `plan.md` lists, `docs/decisions/index.md` and the decisions the spec cites), and no `at` in its verdict (the hook records the time).
- **The phase commands** start the reviewer with `reviewer.alias` and the advocate with `advocate.alias` from `panel/cli.py models`.
- **The template** (`template/sdlc.yaml`): `session_model: claude-opus-5-5`, `adversarial_model: claude-opus-5-5`, `panel_advocate_model: claude-fable-5-1`. A project's own `sdlc.yaml` is unchanged: the sample (`panel_advocate_model: opus`, no new key) keeps today's behaviour but for the exact full-id match.
- **Tests**: `tests/test_models.py` (new, 10 tests: the resolver, the pins, the conflicts, the CLI, the exact match, the record's problems, the gate's park and its absence without the key, the park never the panel's); the hook's record, its write and shell refusals and its fast path (`tests/test_hooks.py`); the session's `--model` per phase and the pins (`tests/test_ci.py`); the judge's model (`tests/test_auto_round.py`); the reviewer's frontmatter and angle (`tests/test_agents.py`). The tests that stand in for the reviewer now also write the hook's record (`tests/model_records.py`), and the expectations that named the template's old models (`opus`, `inherit`, `at`) follow the new template.
- **Docs**: NOTES §51; OPERATING_MODEL §3 and §9; the notes beside decisions 11 and 21; the proposal and ROADMAP R7 annotated.
- **The port list** (HANDOFF rules): this PR touches `plugin/ci/run_phase.py` (`compose`, `session_env`, `panel_models`, `run_reset_judge`).

## The independent review
A fresh-context general-purpose sub-agent on Opus reviewed the diff of `160c0ae` (report only). It found no Important bug in the template's default setup, and it confirmed four things: the hook and the gate read the same working-tree files; the record is committed with the change folder; a stale record is caught by its `head`; and the sample behaves as before, except that the reviewer is now `opus` instead of `inherit`. Its findings, and what this PR did with each:
- **Configurations no alias can satisfy** (rated Important-lite): a session on another id of the reviewer's or the advocate's family (through `SDLC_MODEL` or `session_model`), a workflow pin to another id, or the reviewer and the advocate as two ids of one family would park every gate with a misleading text. **Fixed:** `models.conflicts` names each such case; `panel/cli.py models` prints them, and the gate's `reviewer_model` park adds them to its reason. The advocate now also switches when the session runs on the advocate's *family*, not only on the same id. **Not done:** a refusal by the runner before the session starts. The gate's park names the cause on the first run, and a pre-session refusal would be new runner code for a misconfiguration.
- **A run by hand gets no pins** (Important-lite). **Fixed:** `panel/cli.py models` prints the pins to export, and the park's "What I need from you" says so.
- **A shell command could write a model record.** **Fixed:** the hook refuses any Bash or PowerShell command that names a `*.model.json`, at any time.
- **Records whose `models` is not a list, or that carry no `head`.** **Fixed:** the first parks with "models are not a list" instead of a crash; the second says "the verdict was not written whole by the reviewer".
- **The warning when no advocate model is set** said the advocate ran on the session's model. **Fixed:** it now says nothing shows it ran on another model.
- **The triage and the weekly scan now also take `session_model`'s `default`.** **Kept**, since the owner's rule is Opus and Fable only, and now said in the template's comment and in `models.py`. `plugin/evals/run.py` still reads `SDLC_MODEL` only; it is left out on purpose, because the eval runs measure the CLI default the workflow sets.
- **Angle 8's "beside the diff file"** could be read as a folder. **Fixed:** the wording now says to read each listed file in the working tree and take the diff's removed lines as what was there before.
- **The hook's fast path was untested.** **Fixed:** a test of `may_concern_panel` for the verdict path, Windows-style included, and for shell commands that name a record.
- **The fast lane's confirmation trusts `gate-b.json`.** **Not changed:** it trusts the gate record for every check, and this check is no different.

## The owner's decisions (2026-10-19)
None new. R7 was accepted on 2026-10-09; the owner's "go" of 2026-10-19 approved the plan above, without a decision file.

## Proposed edits for the owner
The root `sdlc.yaml` (decision 6), once this PR has merged and `v1.0.14` is tagged and pinned:

| Link | Row | What is there now | What it must become |
|---|---|---|---|
| [sdlc.yaml](https://github.com/luissiviero/sdlc-framework/blob/main/sdlc.yaml#L12) | 12 | `panel_advocate_model: opus` | `panel_advocate_model: claude-fable-5-1` |
| [sdlc.yaml](https://github.com/luissiviero/sdlc-framework/blob/main/sdlc.yaml#L12) | after 12 | (no line) | `adversarial_model: claude-opus-5-5` |
| [sdlc.yaml](https://github.com/luissiviero/sdlc-framework/blob/main/sdlc.yaml#L12) | after 12 | (no line) | three lines: `session_model:`, then `  default: claude-opus-5-5`, then `  b: claude-fable-5-1` |

*[2026-10-20: applied by the owner in #261 (`6b0ffcd`, merged as `e671eae`), before this PR merged; verified on `main`: `yamlish` and PyYAML read the same values, `panel/cli.py models` reports no conflict in any phase (at (b) the session on `claude-fable-5-1`, the reviewer and the advocate on `claude-opus-5-5`; at (c) to (e) the advocate on `claude-fable-5-1`), and the suite is green with `main` merged into this branch.]* The root pin is 0.3.6 (`sdlc.yaml` line 104 since #261), so these rows act only once that pin moves past 1.0.14; plugin 0.3.6 ignores the two new keys. For a live reading sooner, the sample would need its pin at 1.0.14 (the owner's edit) and, optionally, the same keys:

| Link | Row | What is there now | What it must become |
|---|---|---|---|
| [sample sdlc.yaml](https://github.com/luissiviero/sdlc-sample-python/blob/main/sdlc.yaml#L127) | 127 | `panel_advocate_model: opus` | `panel_advocate_model: claude-fable-5-1` |
| [sample sdlc.yaml](https://github.com/luissiviero/sdlc-sample-python/blob/main/sdlc.yaml#L127) | after 127 | (no line) | `adversarial_model: claude-opus-5-5` |
| [sample sdlc.yaml](https://github.com/luissiviero/sdlc-sample-python/blob/main/sdlc.yaml#L127) | after 127 | (no line) | `session_model: claude-opus-5-5` (or the three-line form above with `b: claude-fable-5-1`) |

## Left
- **The first live run after the owner's rows** reads whether `claude-opus-5-5` and `claude-fable-5-1` are reachable from this CI and whether CLI 2.1.278 honours `ANTHROPIC_DEFAULT_FABLE_MODEL` (NOTES §51, not read). If it does not, every run with a panel decision parks on `panel_models`; the fix is the owner's `claude_code` pin.
- **The external review's retirement count** (the proposal, "Retiring the external review") starts with the first change on 1.0.14.
- **The runs PR's open items** (step 1, items 1–6, 9, 10, 12 and 13) stay where ROADMAP and the session file carry them; none was built here.

## Checks (this repository)
On the final head, after `python -m pip install -e ".[dev]"`, chained with `set -o pipefail`: the four commands of `HANDOFF.md`'s standing precondition 1, plus `python tasks.py docs-lint`. Their output is in the PR.
