# Progress — session 2 (B2: autonomy kit, steps 16–21)

## Summary
- B2 is built and green: 207 tests pass with `python tasks.py check` (ruff zero warnings) on Linux, `claude plugin validate .` is clean; the work landed in three PRs (#4: gate and run limits; #5: agents; #7: preflight, policy skills, full `/sdlc-init`, review fixes, docs) plus #8 for the editable install. Windows execution, owed at the end of the session, passed on 2026-09-21 (see "Results" below).
- The confidence gate (`plugin/gate/`) is one function for every autonomous phase: nine deterministic checks (artifact vs template, open concerns, commands green, evidence, no Important finding, plan.md vs diff, guardrail files, risk list, run limits) plus the adversarial reviewer's verdict as an input; result `continue` / `wait` (human gate) / `park` with `status.yaml`, the `sdlc:needs-human` label and a "What I need from you" block. Against the fixture it continues on a clean change and parks with the right reason for every prepared failure.
- Four agents ship and are registered (verifier from article p.25–26, code-simplifier, researcher, adversarial-reviewer writing `evidence/adversarial-review-<phase>.json`); five policy skills ship with a deterministic `check.py` each (article p.22 pattern) and "no owner source yet" where the owner's standards are still to be named; `preflight.py` decides `acceptEdits` versus `default` from six preconditions and never bypass mode.
- `/sdlc-init` is full for this stage: `evals/` (empty on purpose, decision 17), `bands.yaml` (p.44 shape with an authorization per 3σ route, decisions 14 and 15), Node detection from `package.json` scripts with a second fixture; idempotence kept. CI workflows and the daily digest stay in B3 as the handoff said.
- Left for B3: `/sdlc-design`, the phase runbooks (`/sdlc-build`, `/sdlc-test`, `/sdlc-deploy`), `/sdlc-fix`, the review pass that writes `review-findings.json`, the test-file lock hook, the PR summary and daily digest, and the merge-triggered `claude -p` workflows with the flags recorded in NOTES §10.

## Definition of done (handoff)
| Item | Status |
|---|---|
| `python tasks.py check` green (report the count) and `claude plugin validate .` clean; Windows run listed as owed if not confirmed | Linux: 207 passed, ruff clean, validate clean. Windows: **passed on 2026-09-21** (207 passed; see "Results" below). |
| Gate against the fixture: `continue` on a clean change; `park` with the right reason for each prepared failure; parking writes `status.yaml` and prints the "What I need from you" block | Done (`tests/test_gate.py`, 24 tests: missing plan.md, failing test behind `SAMPLE_FAIL=1`, a diff touching `.claude/settings.json`, a risk-list word, escalating / missing / stale verdict, open concern, unsynced commit, missing evidence, Important finding, iteration cap, pause flag). |
| Four agent files exist, are registered, say "report only, do not fix" | Done (`tests/test_agents.py`). |
| Preflight refuses auto-accept when any precondition is missing and allows it on the initialised fixture | Done (`tests/test_preflight.py`, 12 tests; the fixture passes with the plugin's own skills). |
| Five policy skills with static tests; full `/sdlc-init` writes `evals/` and `bands.yaml` and stays idempotent | Done (`tests/test_policy_skills.py`, `tests/test_init.py`). |
| `docs/PROGRESS.md` for session 2 with the ≤5-bullet summary and the list for B3 | This file. |

## Steps
| Step | Status | What exists / what is left |
|---|---|---|
| 16 Confidence gate | done | `plugin/gate/`: `artifacts.py` (section names for intent/spec/plan, evidence file names, JSON formats), `checks.py` (artifacts, open_concerns, commands, evidence, findings, plan_sync, guardrails, risk_list, adversarial_review), `diff.py`, `gate.py` (`run_gate` → continue / wait / park; writes `status.yaml` and `evidence/gate-<phase>.json`), `cli.py check --root . --id 0001 --phase c` (exit 0 / 3 / 4). Spec.md sections defined here for B3's `/sdlc-design`. The review pass that produces `review-findings.json` is B3. |
| 17 Agents | done | `plugin/agents/{verifier,code-simplifier,researcher,adversarial-reviewer}.md`, listed in `.claude-plugin/plugin.json` (`sdlc:<name>` when installed). The adversarial reviewer is the only one with `Write`, for its verdict JSON; `Edit` disallowed. The phase runbooks that call them are B3. |
| 18 Auto-accept | done | `plugin/gate/preflight.py --root . [--id]`: CLAUDE.md with the three targets, five policy skills (plugin or `.claude/skills/` override), `hooks.json` and scripts present + `python` on PATH, settings (bypass disabled, deny rules, plugin enabled), not paused, test target green → `acceptEdits`, else `default`. `--id` reports the routine / non-routine classification and the cap. B3 passes the answer to `claude -p --permission-mode`. |
| 19 Run limits | done | In the gate (`limits.py`, first check, stops early): `max_iterations` 3 (2 non-routine), `max_wall_clock_minutes` from `gate/cli.py start-run`, `max_budget_usd` from `record-spend`, `paused: true` in `sdlc.yaml`. `--max-turns` / `--max-budget-usd` / `total_cost_usd` recorded in NOTES §10b as the outer bound for B3. `maxTurns` set on every agent. |
| 20 Policy skills | done | `plugin/skills/{coding-standards,security-baseline,ux-conventions,data-conventions,definition-of-done}/SKILL.md` + `check.py` each (shared `plugin/gate/policy.py`). Sources cited by article page; **owner's own standards: none yet** (each skill says so and where to name them). Trigger test is a live check (below). |
| 21 `/sdlc-init` (full) | done for B2 | `evals/README.md` + `evals/cases/.gitkeep`, `bands.yaml`, Node detection (`init/detect.py`), `tests/fixtures/sample-node-project/`. Left for B3: CI workflows (phase transitions), daily digest. |

## Decisions: none reopened, none impossible
- Decision 11 (park, never page) is the shape of the gate: escalation from the adversarial reviewer is a park; no notification path exists anywhere in the code.
- Decision 7 (Python everywhere): the gate runs the project's own targets through the platform shell (`subprocess.run(shell=True)`) because they are the owner's one-liners (`npm test` needs cmd.exe on Windows); everything the framework itself runs stays argument lists.
- Decision 14 (split by blast radius) is written into `bands.yaml` as `authorization` per route; decision 15's metric is its default; decision 17 keeps `evals/` empty with a README.
- Decision 6 (guardrail layers): unchanged; the gate adds a fourth net for the gap NOTES §9 records (a script writing a guardrail file bypasses the hook: the diff check catches it at the next gate).

## Choices made where the pack left it open
1. **Gate result has three values**: `continue`, `wait` (all checks pass at a human gate → `sdlc:<phase>-ready`), `park`. A failed check parks even at a human gate, so the owner sees the reason in the queue instead of a green-looking PR.
2. **Framework changes**: a diff may touch guardrail files only when `intent.md` carries the header line `Framework change: yes` (or the change is 0000). Recorded in the intent-template skill; `/sdlc-init`'s own intent carries it.
3. **Risk acceptance**: a risk-list hit parks until the owner runs `state/cli.py accept-risk --id <id> --item "<item>"`, which writes `status.yaml: risk_accepted`. Matching is whole-token and plural-tolerant (`auth` matches `auth/` and `auth_token`, not `author`); owners add variants to the list.
4. **plan.md ↔ diff** is two checks in one: every changed source file (not `plan_sync.exempt`) is listed under "Files that change" (a path, a glob or a folder), and the plan-sync hook rule is re-applied to every commit on the branch (closes the NOTES §9 gap for commits the hook could not parse).
5. **Spec.md sections** (the article gives the prompt, not the shape): Requirements · Design · Open questions from intent · Flagged concerns · Acceptance. An open concern is a list item starting with `[ ]` or `open` — superseded by choice 14: every item is open unless it starts with `[x]`, `closed`, `resolved` or `decided`.
6. **Verdict freshness**: the adversarial verdict must carry `head` (a verdict without one is malformed); a verdict for another commit is rejected. A verdict is required at gates (b), (c) and (d) in every profile (the Full profile gets the same machine review as Standard); at (a) and (e) it is read when present. `review-findings.json` must carry `head` at gate (e) too.
7. **Findings JSON** (`evidence/review-findings.json`, produced by B3's review pass): `{"findings": [{"pass", "severity": "important|nit", "file", "line", "summary"}], "tally": {...}, "head"}`; required at gate (e), read at (c)/(d) when present.
8. **Pause flag** is `sdlc.yaml: paused: true` (a protected path, so a run cannot un-pause itself), not a `changes/PAUSE` file.
9. **Wall-clock and budget** are read from `evidence/run-<phase>.json`, written by `gate/cli.py start-run` and `record-spend`; a run that never called `start-run` is not wall-clock limited (B3's runbooks call it first).
10. **Evidence file names**: `test.log`, `build.log`, `lint.log`, `verifier.md` (required at (d) and (e); `verifier.md` also at (c)), plus screenshots for UI changes, `adversarial-review-<phase>.json`, `review-findings.json`, `gate-<phase>.json`, `run-<phase>.json`.
11. **Policy checks are advisory scripts** (exit 1 = something to look at, never a block); the must-hold policies have the hooks and the gate behind them, as p.22 governance asks. `definition-of-done/check.py` is the gate in dry-run.
12. **Node targets** come from `package.json` scripts; a missing lint script stays `none` (the gate then refuses phase (c)) rather than adding a dependency the owner did not choose.
13. **The gate judges committed, owner-approved inputs** (fresh-context review of session 2): `intent.md` is read as merged at gate (a) (the merge base), and a later phase that edits it parks; when the branch edits `sdlc.yaml`, limits, risk list and exemptions are read from the base copy (`config_note` says so) and the edit is a guardrail hit; uncommitted files outside the change folder park at (c)/(d)/(e) (`clean_tree`), because the verdict and the PR judge HEAD; an automated gate at (b)/(c)/(d) parks when the runbook did not call `start-run`; `--phase` must equal `status.yaml: phase`.
14. **Flagged concerns fail closed**: every list item under "Flagged concerns" is open unless it starts with `[x]`, `closed`, `resolved` or `decided` (`none` means no concern).
15. **A plugin upgrade adds new top-level `sdlc.yaml` keys as text blocks** with the template's comments; only a new nested key still re-dumps the file (reported as "comments dropped").

## Known gaps (carried to B3, found by the session's fresh-context review)
- `status.yaml: risk_accepted` and `iterations` are owner actions by convention only: a run could call `accept-risk` or `set-iterations` itself. B3 ties them to the commit author (owner ≠ automation identity) or moves the acceptance to a PR label.
- The adversarial reviewer has `Bash` (it needs `git diff` and the test target), so "the one file you write is the verdict" is an instruction, not a mechanism; the protected-path hook and the review pass are the nets.
- Risk-list matching is lexical (whole tokens, plural-tolerant); synonyms go into the owner's list.
- The policy `check.py` scripts are pattern-based and advisory by design (p.22).
- The `sdlc:needs-human` / `sdlc:<phase>-ready` labels are printed by the gate, not applied (B3's runbooks apply them).

## Live checks the owner can do now (not automatable here)
Test repository: `luissiviero/sdlc-sample-python` (plugin loaded through the setup script of NOTES §3a).
1. On the PC: `python tasks.py check` (owed since session 1). Done, see below.
2. Re-run `/sdlc:sdlc-init` in the sample repo: expect `evals/README.md`, `evals/cases/.gitkeep` and `bands.yaml` created and everything else `unchanged` / `kept`.
3. Policy-skill trigger (step 20's "test that it triggers"): ask "review this diff for security" → `sdlc:security-baseline` should load; ask "is change 0001 done?" → `sdlc:definition-of-done`.
4. Agents: ask "run the verifier on change 0001" → `sdlc:verifier` should run with Bash and Read only; ask "run the adversarial reviewer for phase c of change 0001" → it should write `changes/0001-*/evidence/adversarial-review-c.json`, and `python "${CLAUDE_PLUGIN_ROOT}/plugin/gate/cli.py" check --root . --id 0001 --phase c` should then read it.
5. Preflight: `python "${CLAUDE_PLUGIN_ROOT}/plugin/gate/preflight.py" --root .` → `allow: true` in the sample repo once `/sdlc-init` has been re-run (it needs the five skills, which the pinned plugin now ships).
6. Windows hook spawn (NOTES §1): on the PC with the plugin loaded, an attempted edit of `.claude/settings.json` shows the "Protected path" denial (the denial passed in the cloud; the Windows spawn is the unproven half).

Results:
- 2026-09-21 — Windows 10 (19045), Python 3.14.7, ruff 0.16.8, pytest 9.1.1, Node 24.19.0 / npm on PATH.
- `python tasks.py check` on Windows: PASS — ruff lint clean, 70 files formatted, 207 passed / 0 failed / 0 skipped (the npm half of `test_init_on_node_fixture_writes_npm_targets` ran); `claude plugin validate .` passed.
- `pip install -e ".[dev]"` failed on `main` (setuptools flat-layout: `plugin` + `template`, on any OS); fixed in PR #8 (`[tool.setuptools] packages = []`).

## Applied after session 2 (2026-09-21, outside a build session; owner action pending)
- **Step 3 (execution substrate)**: the credential arrangement of decision 1 is settled — every workflow takes both repository secrets, `ANTHROPIC_API_KEY` (bare mode, per-token billing, workspace spend limit) preferred over `CLAUDE_CODE_OAUTH_TOKEN` (the owner's subscription window); the owner starts with the token and moves to the key from usage data. Facts, quotes and the owner's setup steps are in NOTES §2. `.github/workflows/substrate-smoke.yml` (dispatch only) runs `.github/scripts/substrate_smoke.py`, unit-tested with a fake CLI (`tests/test_substrate_smoke.py`); the key-path command line was dry-run locally with an invalid key, the workflow itself has not run. Step 3 stays **open** until the owner has stored a secret and the smoke run is green; the merge-triggered workflows themselves are session 3 (step 30).
- **Model allocation for the build sessions**: `docs/MODEL_ALLOCATION.md` and the "Model rule" section of `HANDOFF.md` (owner-approved).

## Left for B3 (write the next `HANDOFF.md` from this list)
- `/sdlc-design` (step 22): the p.14 prompt with the policy skills loaded, `spec.md` with the five sections of `plugin/gate/artifacts.py`, then the read-only planning run (`plan-template` skill), adversarial verdict, gate (b), PR or hand-over per profile.
- Phase runbooks (step 24): `/sdlc-build` (`gate/cli.py start-run`, `preflight.py` → permission mode, implementation, code-simplifier, verifier → `evidence/verifier.md`, adversarial reviewer, gate (c)), `/sdlc-test` (fresh context; `evidence/test.log`, `build.log`, `lint.log`, screenshots; verifier; gate (d)), `/sdlc-deploy` (review passes → `review-findings.json`; fix loop bounded by `status.iterations`; PR summary; gate (e)).
- Test-file lock hook for fix-type changes (step 25) and the REVIEW.md rule that backs it.
- Review pass + `/sdlc-fix` (step 26): writes `review-findings.json` in the format of choice 7; `/sdlc-fix` reads unresolved comments and failing checks and re-runs the phase with `bump_iteration()`.
- PR summary and daily digest (step 27a): the ≤5-bullet summary from `evidence/gate-<phase>.json`, findings tally, plan conformance, "What I need from you".
- Merge-triggered `claude -p` workflows (step 30): `--plugin-dir` on the checked-out pinned framework, `--max-turns`, `--max-budget-usd`, `--permission-mode` from the preflight, `--permission-prompts none`, `total_cost_usd` → `record-spend`; explicit dispatch of the next phase (workflow-token rule); subscription token versus API key per NOTES §2.
- Labels on GitHub (`sdlc:*`) created by the first workflow; the `sdlc:needs-human` label applied when the gate parks (the gate prints it; nothing applies it yet).
- Known gaps carried: NOTES §9 items; the gate's risk matching is lexical (an owner's synonym list is the remedy); policy check scripts are pattern-based and advisory.
