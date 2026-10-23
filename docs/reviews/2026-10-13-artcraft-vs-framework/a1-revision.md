# A1 checked against the code: the drive target and the plan's Proof (2026-10-13)

Part 1 of `docs/handoffs/2026-10-13-a1-drive-target-prompt.md`. The proposal is `docs/proposals/drive-target-and-proof.md`. It is checked here against the framework at `main` **714f523** (plugin 0.3.7, after PR #167) and against the ArtCraft repositories read-only: lightcraft `b3d392b`, filmcraft `cee1feb` and effectcraft `549e9d8` (the study's commits), and photocraft `be7a1f8` (100 commits after the study's `6f85054`; none of the cited files moved between the two). Nothing in the proposal is changed here. The owner decides each divergence, and the accepted ones are annotated into the proposal beside the sentence they correct (choice 126).

## In five lines

- **The direction holds and the weights favour it, but only after R10.** Today a red target parks (decision 11). Until R10's automatic round exists, each red drive is one more park for the owner, which raises attention (weight 3).
- **The gate does not check screenshots today.** `artifacts.py:69` defines a constant that no check reads, so the proof-file check is a new check, not an extension of one.
- **The state value must be compared by the gate, in the runner's step, against the plan the owner approved.** The verifier never sees the final tree's proof: at (d) it reads (c)'s record, and no verifier runs at (e).
- **Three gaps.** The drive has no way to know where to write (the change folder varies, the command is fixed). The by-hand path (`collect.py`) is not covered. Gate (b) would run the drive on the base code.
- **The "runner step" is gate code.** It lives in `gate.py`/`checks.py`; `run_phase.py` needs one line (the timeout). The port-list rule records a PR; it does not forbid building one. So the split the owner expected does not match the code (section 5).

## 1. The six sub-changes

| # | Claim | What I found | Source at 714f523 | Verdict | What I would change |
|---|---|---|---|---|---|
| 1 | A fourth optional target, `commands.drive`, writes its outputs under `changes/<id>-<slug>/evidence/proof/`; empty means none | The `commands:` block has build, test, lint and setup. `commands_from_config` reads build, test and lint only, and both the gate and `collect.py` share it. **The command is one fixed string, but the folder changes with every change**, and the proposal does not say how the command learns where to write. | `template/sdlc.yaml:35-41`; `plugin/gate/checks.py:249-259`; `plugin/evidence/collect.py:103` | partly | The runner (and `collect.py`) set an environment variable such as `SDLC_PROOF_DIR` to the absolute proof folder, plus `SDLC_CHANGE_ID`. The drive writes there and nowhere else. Name the variable in the `sdlc.yaml` comment. |
| 2 | The runner runs it after the session, in the credential-free step, under `gate.command_timeout`; a red drive is a red target; under T10 a red drive starts a round, and one that cannot start parks at once "as T10 settles" | (a) The step is gate code: `run_phase` calls `gate/cli.py run-commands` → `gate.run_deferred_commands` → `checks.run_targets`/`judge_targets`, and `write_deferred_logs` writes the logs. In `run_phase.py`, only `commands_timeout_seconds` (`3 * per_command + grace`) would need to change, to 4×. (b) "Credential-free" is half true. `commands_env` strips the model credentials and `GITHUB_TOKEN`/`GH_TOKEN` from the environment, but the project checkout keeps the workflow token in `.git/config`, because no workflow sets `persist-credentials` (T29 "Today"). That is the same exposure as the test target, not a new one. (c) **T10 is not built.** R10 is accepted, but its decision file is not written (it amends decision 11 and choice 154). Today a red target parks. (d) **T10 does not settle the target that cannot start:** it lists that case under "Open". (e) The runner runs the targets at gates **(b)**, (c), (d) and (e). At (b) the drive would run on the base code, where the plan's proof files cannot exist yet. (f) By hand, `collect.py` runs the targets; the proposal leaves it out. | `plugin/ci/run_phase.py:1310-1331`, `:1400-1406`, `:1873`; `plugin/gate/gate.py:378-433`, `:344-375`; `template/.github/workflows/sdlc-test.yml:59-61`; `target-design.md` T29 "Today", T10 "Open"; `docs/ROADMAP.md` R10; `plugin/gate/checks.py:1694-1757` | partly | Write "after R10, a red drive follows R10's rule; before R10 it parks, as any red target does (decision 11)". Remove "as T10 settles"; whether a drive that cannot start gets a round is R10's open item. Run the drive at gates (c), (d) and (e) only. `collect.py` runs it by hand. Call the step "the step that holds no credential in its environment" and refer to T29 for the `.git/config` token. |
| 3 | `## Proof` gains a third kind, `state: evidence/proof/<file>, <path> == <value>` (also `contains`, `matches`). The gate's `evidence` check verifies that every named proof file exists "as it does for screenshots today"; the verifier compares the values | (a) Proof today is free prose ("the tests that prove it, by name; … for UI, the mock or screenshot to match"). It has no kinds and nothing parses it; the gate checks only that the heading exists. (b) **The gate does not check screenshots:** `EVIDENCE_SCREENSHOTS` is read only by `collect.py`, which creates the folder, and `check_evidence` reads `REQUIRED_EVIDENCE` (the logs and `verifier.md`). The sentence in `sdlc-test.md` saying "the gate treats it as evidence missing only when the plan asked for screenshots" has no code behind it. (c) The build session may edit `plan.md` in (c) (plan sync; `sdlc-build.md:87` tells it to add the screenshot to Proof), so a value read from the working tree is a value the writer can change. `GateContext.approved_artifact` already reads the approved copy at the merge base. (d) The article's own example of a quantifiable target is a state: "the endpoint returns 200 with the new field" (p.28 step 3). | `plugin/skills/plan-template/SKILL.md:31-33`; `plugin/gate/artifacts.py:53`, `:69`, `:82-86`; `plugin/gate/checks.py:425-488`, `:124-135`; `plugin/evidence/collect.py:75-80`; `plugin/commands/sdlc-test.md:82-84`; `plugin/commands/sdlc-build.md:85-87`; article p.27-28 | partly | Fix one line shape per item: `- test: <name>`, `- screenshot: evidence/proof/<file>.png` (with `vs mock/<file>` when the spec has a `Mock:` line), `- state: evidence/proof/<file> <path> == | contains | matches <value>`. `<path>` is a dotted JSON key, or `line` for a text file. Prose stays allowed beside the items. **The gate makes the comparison**, in the runner's step, reading the items from the approved `plan.md` (`approved_artifact`). An item added during (c) is reported, but it is not the bar. Correct "as it does for screenshots today": this is a new check. |
| 4 | The verifier opens the proof files "of the phase before yours", compares each with the Proof item and reports `matches` / `differs` / `not produced` per item | The verifier runs at (c) and (d) only. At (c) it reads `gate-b.json`, and gate (b) has no proof. At (d) it reads `gate-c.json`, the run on the tree (d) started from. No verifier runs at (e). Its tools are Bash and Read, so it can open a PNG. **The final tree's proof (the runner after (d), after a fix round, at (e)) is never read by the verifier.** | `plugin/agents/verifier.md:4`, `:26-30`; `plugin/commands/sdlc-build.md:105-116`; `plugin/commands/sdlc-test.md:86-93`; no verifier step in `sdlc-deploy.md` | partly | Narrow it to what only a judge can do: at (d), compare (c)'s screenshots with the mock and name the tree read (T10's wording). State items are the gate's (row 3). The verdict `does not match the plan` still covers a `differs`. |
| 5 | The PR body shows the proof in T27's block, with images under a cap the `evidence` check enforces (ArtCraft: 50 KB) | (a) **T27's block does not exist.** T27 has no proposal yet; it is in the study batch after the read. (b) The PR body already shows a screenshot **count** in the evidence line, so "no screenshot is shown" is partly wrong. (c) ArtCraft's 50 KB applies to **blessed golden PNGs**, checked when a golden is blessed (the file is written, then the bless fails; nothing shrinks it), not in CI. The goldens are committed on purpose: 27 files, the largest 42,952 bytes. Proof files are regenerated on every runner step, and the runner commits the whole change folder, so every round adds new image bytes to history. | `plugin/pr/description.py:195-207`; `target-design.md` T27 status; `plugin/state/cli.py:137-148`; filmcraft `docs/testing.md:163`, `crates/testkit/src/golden.rs:15`, `:236-240` | partly | Now: the evidence line gains "proof N, state items M of K matching". With T27: the per-item Proof line. Cap: `gate.proof_image_kb` (50 by default) and a count cap per run (for example 10). An oversized or extra image is not committed and is reported as `not produced`. That parks only when the approved plan names it. |
| 6 | `/sdlc-init` proposes the command: Node with Playwright → `npx playwright test proof/ --reporter=json`; Python → an empty `proof/run.py` skeleton that exits 0; otherwise `""` | Detection is in `plugin/init/detect.py` (not `sdlc_init.py`). The proposed Playwright line writes to Playwright's own output folder, not to the change's `evidence/proof/`. A Python skeleton that exits 0 is a **green drive that proves nothing**, and it is project content written into the repository. | `plugin/commands/sdlc-init.md:22-28`; `plugin/init/detect.py:265-291` | partly (Node) / disagree (Python) | Propose the Playwright line only when `@playwright/test` is in `package.json`, writing to `$SDLC_PROOF_DIR`. For Python and everything else, propose `""` with a comment naming the slot. No skeleton file. |

## 2. The four set aside

| Item | What I found | Source | Verdict | Change |
|---|---|---|---|---|
| The audit test (effectcraft `ui_agent_audit.rs`) | It checks that every *engine command* is reachable over the control channel and that every panel registers *automation ids*, not "every user-facing action". The widget test is ignored in release builds. | effectcraft `crates/ui-egui/tests/ui_agent_audit.rs:1-7`, `:38-49`, `:125-127` | agree, wording partly | Describe it accurately: "commands and widget ids". |
| The MCP route (filmcraft `.mcp.json`) | Two servers are registered. The bridge works only once a person has started the app with `--control 9876`. | filmcraft `.mcp.json:3-10`, `docs/agents.md:21-27` | agree | none |
| Running the drive inside the session | **This is what ArtCraft and the article actually do.** The agent drives the product in its own session and iterates (filmcraft `docs/agents.md:250-256`, lightcraft `AGENTS.md:120-121`; article p.27-28: "Claude iterates until the check passes"). **No ArtCraft CI workflow runs a drive;** lightcraft's "CI and nightly runs can judge a snapshot by its exit status" is unused. Setting it aside is right (sandbox, choices 133 and 154; T10 rejected the helper). But the proposal's "the step in the loop does [transfer]" overstates it: what transfers is a check after the session, and the loop exists only once R10 adds its rounds. | lightcraft `docs/control-protocol.md:254-262`; the agents' search of all four repositories' workflows | agree with setting it aside; disagree with "the step transfers" | Say plainly: fidelity is partial. The article's in-session loop becomes a check after the session plus R10's rounds. |
| Proof as workflow artifacts | Agreed that committed files are the record (D9, T32). | — | agree | Add that history grows with every round (row 5), which is why the cap matters. |

## 3. The ArtCraft citations

| Citation | Verdict |
|---|---|
| lightcraft `control-protocol.md:254-262` (exit status) | partly: it says what CI *could* do; no ArtCraft CI does it |
| photocraft `development.md:222-227` (the quote) | agree, literal (lines 226-227) |
| photocraft `agent_tasks.rs:1-4` | partly: it sets state checks against *engine internals*, not against screenshots |
| filmcraft `agents.md:250-256`, `:309-320` | partly: drive and screenshot are in the Definition of Done (`:317`, quoted literally); the assert step is in §3 only |
| photocraft `contributing.md:11` | agree; a contributor guideline, not enforced |
| filmcraft `testing.md:163` | agree; enforced when a golden is blessed, not in CI |

## 4. Decisions, order and fidelity

| Claim | What I found | Verdict | Change |
|---|---|---|---|
| "Amends no settled decision" | True of the proposal itself. But a red drive starting a round depends on **R10**, which amends decision 11 and choice 154; R10's decision file is not written yet. | partly | Write "amends none itself; its red-drive round rides on R10's amendment of 11". |
| Decision 19 "gives the target its shape" | Decision 19 covers what *deploy* and *maintain* mean per project. The drive is shaped like it (one command per project) but is not under it. | partly | Write "shaped like decision 19's adapters". |
| Decision 12 (the review pass in a fresh context) | Decision 12 is about where the **review job** runs. The verifier is build guide step 17 (article p.26-27). | disagree with the citation | Cite OPERATING_MODEL §2 (writer ≠ judge) and step 17. |
| Decision 2 | The plan is written read-only at (b) and approved at gate (b). State items are written there; the gate reads the approved copy (row 3). | agree, unstated | Name decision 2 among the decisions it keeps. |
| "Cannot be built before the 1.0.0 read because `run_phase.py` is on the port list" | HANDOFF only says that a PR touching `run_phase.py` **goes on the port list**. It records the PR; it does not bar it. The step is gate code, and `run_phase.py` needs one line. The real constraints are the queue (R7 … R13 come first) and R10. | disagree | Write "after R10 in the owner's queue; one line in `run_phase.py` puts it on the port list". |
| Article pages | p.25-27 → the verifier text is on p.26-27; p.27-29 → the loop is p.26-28. The state example ("returns 200 with the new field") is p.28 step 3. | partly | Correct the page numbers; cite p.28 for the state kind. |

## 5. Against the owner's weights (safety 1, attention 3, autonomy 3, auditability 2, cost 0, fidelity 2)

| # | Safety | Attention (down wanted) | Autonomy | Auditability | Fidelity | Holds? |
|---|---|---|---|---|---|---|
| 1 drive target | = (the same exposure as the test target) | = | + | + | + | yes, with the proof-folder variable |
| 2 runner step | = | **up before R10** (a red drive parks); down after R10 (a round, then a park only at the cap) | + after R10 | + | partial | **yes, sequenced after R10** |
| 3 `state` item, gate-compared | = | down (the owner reads a result, not a diff) | + | + (the expectation fixed at (b)) | + (p.28) | yes, if the gate compares |
| 4 verifier reads screenshots | = | = | + | + | + (p.26-28) | yes, narrowed to images at (d) |
| 5 PR line + cap | = | down | = | + | + (p.34-35) | yes: the evidence line now, the per-item line with T27 |
| 6 `/sdlc-init` | = | = | = | = | = | Node only; drop the Python skeleton |

## 6. A first look at the split (Part 2, for the owner's answer)

The owner expected two changes: first the parts that touch no runner code, then the runner step and the PR block after the read. **The code says otherwise.**

- The runner step lives in `gate.py`/`checks.py`, plus `collect.py` by hand. Only the timeout is in `run_phase.py`.
- A proof check whose files nothing produces would be dead code. So would an `sdlc.yaml` key that nothing reads.

My proposal:

- **Change 1, after R10 is built.** The drive end to end:
  - the target and its proof-folder variable;
  - the runner's run at (c), (d) and (e), and `collect.py`;
  - the gate's proof check with the state comparison against the approved plan, and the cap;
  - the plan template's grammar, the verifier card, the evidence line, the `sdlc.yaml` key and `/sdlc-init`;
  - the one-line timeout, which puts it on the port list.
- **Change 2, with T27.** The per-item Proof line.

If the owner wants it before R10, change 1 can land with a red drive parking. That costs attention until R10.

## 7. What the independent reviewer added

A fresh-context reviewer was given the proposal and the code, but not this file. It reached the same verdicts on rows 1 to 4, the screenshot claim, the step in gate code, the gates (b) to (e), R10 not built, T10's open item, the Python skeleton, decision 12 and the port-list reading. It added the points below, each checked here at 714f523:

| Point | Source | Verdict | Change to the proposal |
|---|---|---|---|
| **The writer authors the drive script.** A drive could write the expected value instead of reading it from the product. | The writer edits every source file in (c); the test lock covers only a fix-type change's tests. | agree | The adversarial reviewer at (c) and (d) reads the drive's diff with one extra angle: "does the drive read the value from the product, or write it?". The drive's files are listed in the plan's "Files that change". It is the same weakness feature tests already have, and it is named rather than closed. |
| **A cap enforced as a park does not stop the bytes.** `commit_run_record` commits the whole change folder, even on a park. | `plugin/ci/run_phase.py:1905-1916`, `:1996-2021`; `plugin/state/cli.py:137-148` | agree | The runner step deletes an oversized or extra image before the commit and records it as `not produced` (row 5 already says "not committed"; the order is now explicit). |
| **At (c) the `evidence` entry is not judged again after the runner's step.** Gate (c) defers no log, so `run_deferred_commands` re-judges `evidence` only when it was deferred or a log was written. | `plugin/gate/gate.py:433-446`; `plugin/gate/artifacts.py:82-86` | agree | The proof check and the state comparison belong to the judgment of the drive's run (the `commands` entry, or a `proof` entry judged in the same step), not to `check_evidence`. |
| **"An empty drive loses nothing" conflicts with sub-change 3.** A plan naming a `state` item while `commands.drive` is empty parks at (d). | — | agree | Gate (b) refuses a plan whose Proof names a `state` or `screenshot` item while `commands.drive` is empty. The park comes at the design, not after the build. |
| **Which run produced the proof is not recorded.** | — | agree | The runner writes `evidence/proof/manifest.json` (commit, run, phase, each file and its size). It clears `proof/` before each run so a stale file never counts. |
| **The job timeouts assume three targets:** the runner's `3 *` and the workflows' `timeout-minutes: 200`. | `plugin/ci/run_phase.py:1317`; `template/.github/workflows/sdlc-build.yml:66`, `sdlc-test.yml:56`, `sdlc-fix.yml:92` | agree | Scale the runner line. Raising the workflows' minutes would touch the fix template, which is on the port list; check first whether 200 minutes already cover a fourth target. |
| **Five lists know only three logs:** `EVIDENCE_TARGETS`, `LOG_FILES`, `HEADER_REQUIRED_AT`, `commands_summary`, the check run. | `plugin/gate/artifacts.py:70`; `plugin/pr/description.py:61`; `plugin/gate/checks.py:418` | agree | Plan detail for the design run; listed so it is not missed. |
| **Decision 21.** Under deferred review, a verifier mismatch goes to the panel. | OPERATING_MODEL §3 "Review mode" | agree | Add 21 to "Decisions it touches". A gate-compared `state` item is a deterministic check, not a panel item; the verifier's screenshot `differs` is a panel item. |
| **Sub-changes 3 and 6 are under `plugin/`**, so they need a version bump, not "a plain change". | HANDOFF "Rules for every session" | agree | Correct "could land first as a plain change". |
| **Playwright needs its browsers.** | — | agree | The `/sdlc-init` proposal adds the browser install to `commands.setup`. |
| **The network.** The runner's step has no sandbox and full network, and the checkout's token is readable there. | T29 "Today"; T29 option C | partly | It is the same exposure as the test target. The proposal names it and refers to T29; it adds no new hole. |
| The 50 KB figure is "not verified" | The reviewer did not clone ArtCraft; the citation check did: filmcraft `crates/testkit/src/golden.rs:15` `MAX_GOLDEN_BYTES = 50*1024` | disagree (verified) | Keep the figure with the `golden.rs:15` citation. |

## 8. Found on the way (not part of A1)

- `sdlc-test.md:82-84` says that the gate treats a screenshots README as evidence missing when the plan asked for screenshots. No code does this (row 3).
- `plugin/skills/ux-conventions/check.py` (the `glob` over `change_dir / "evidence"`) looks for images directly in `evidence/`, while `/sdlc-test` writes them to `evidence/screenshots/`. The advisory check would report "no screenshot" for a change that has them.
- `plugin/pr/description.py:204-206` counts the `.gitkeep` that `collect.py:80-82` writes, so the PR body reports one screenshot too many.

## 9. What I need from you

One answer per row: accept, reject or amend. Each accepted row becomes an annotation beside the sentence it corrects in the proposal (choice 126).

| # | Divergence | My recommendation |
|---|---|---|
| D1 | A red drive before R10 | Build A1 after R10, so a red drive starts a round. Building it earlier means a red drive parks. |
| D2 | Who compares a `state` value | The gate, in the runner's step, against the approved `plan.md`. The verifier keeps screenshots only, at (d). |
| D3 | How the drive learns its folder | `SDLC_PROOF_DIR` and `SDLC_CHANGE_ID`, set by the runner and `collect.py`. `proof/` is cleared before each run, and `manifest.json` records the run. |
| D4 | Which gates run the drive | (c), (d) and (e), never (b). Gate (b) refuses a plan whose Proof names a `state` or `screenshot` item while `commands.drive` is empty. |
| D5 | The proof grammar | `- test:`, `- screenshot:`, `- state: <file> <path> ==\|contains\|matches <value>`. Paths are dotted JSON keys or `line`; regexes are Python `re`. Prose stays allowed. |
| D6 | The image cap | `gate.proof_image_kb` (50 by default, after filmcraft `golden.rs:15`) and 10 images per run. An image over either limit is deleted before the commit and reported `not produced`. |
| D7 | The writer authors the drive | The adversarial reviewer gets one more angle on the drive's diff. The weakness is named in the proposal, not closed. |
| D8 | `/sdlc-init` | The Playwright line only when `@playwright/test` is present (browser install added to setup). Otherwise `""`, and no Python skeleton. |
| D9 | The PR body | The evidence line gains the proof count and the state results now; the per-item line comes with T27. |
| D10 | Decisions and order text | "Amends none itself; rides on R10's amendment of 11". Add 2 and 21, replace 12, and say "shaped like 19". Order: "after R10; one line in `run_phase.py` puts it on the port list". Sub-changes 3 and 6 need a version bump. |
| D11 | Fidelity wording | ArtCraft and the article run the drive inside the session. What transfers is a check after the session plus R10's rounds; say so. |
| D12 | The split (Part 2) | Change 1: the whole drive, after R10. Change 2: the per-item Proof line, with T27. Your expected split would build a check that nothing feeds. |
