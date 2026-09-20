# Handoff — session 2: build stage B2 (autonomy kit, steps 16–21)

Session 1's brief is kept at `docs/handoffs/session-1-B0-B1.md`; its result is on `main` once PR #1 is merged.

## Preconditions — check before building anything
1. PR #1 (session 1) is merged to `main` and this session starts from `main`. If it is not merged, stop and say so.
2. The owner's live checks from `docs/PROGRESS.md` ("Live checks the owner can do now"). Read their status from the owner's first message or from the PR #1 checklist; do not assume. If any is unreported, ask once and continue with the rest of B2, marking the dependent step partial.
   - Windows: `python tasks.py check` green on the owner's PC. If it failed, fixing it is the first task (the code is meant to be path-agnostic; see NOTES §1).
   - Hook denial in a live session: with the plugin loaded, an attempted edit of `.claude/settings.json` is refused with "Protected path". If it was **not** refused, step 18 (auto-accept) must not be enabled in this session; diagnose first (hooks.json exec form, `python` on PATH, plugin actually loaded — `/plugin` shows `sdlc@sdlc-framework`).
   - Intent-skill trigger: "draft an intent for …" loads `intent-template`. If not, tune the skill's `description` (article p.22 step 4) before writing the policy skills of step 20 the same way.
3. `python tasks.py check` is green in this session before the first edit (142 tests at the end of session 1).

## Read in this order
1. `docs/OPERATING_MODEL.md` — the contract, finalised in session 1.
2. `docs/DECISIONS.md` — 20 settled decisions. Do not reopen them; if one proves impossible, document why in `docs/PROGRESS.md` and continue.
3. `docs/PROGRESS.md` — what exists after session 1, the choices made where the pack was open, and the gaps carried forward.
4. `docs/NOTES.md` — platform facts verified against the Claude Code docs (hooks, cloud sessions, managed settings, permissions, plugin layout). Re-verify a fact only if the plugin's minimum Claude Code version (2.1.228) changes.
5. `docs/BUILD_GUIDE.md` — steps 16–21 (B2) and, for the interfaces B2 must leave ready, steps 22–30 (B3).
6. `docs/reference/ai-native-sdlc-playbook.txt` — page-tagged article; read a page when a step cites it.
7. `CLAUDE.md` — conventions for this repo.

## Objective of this session
Complete build stage **B2**: everything a phase needs to run unattended safely — the confidence gate, the four agents, auto-accept conditions, run limits, the policy skills, and the full `/sdlc-init`. Do not start B3 (`/sdlc-design`, the phase runbooks, CI workflows). Everything must still work by hand on the owner's PC and in a Claude Code cloud session (decision 1: CI arrives in B3).

## Layout facts from session 1 that B2 builds on
- The **repository root is the plugin root** (marketplace `source: "./"`, `.claude-plugin/plugin.json` points at `./plugin/...`). Scripts are called as `python "${CLAUDE_PLUGIN_ROOT}/plugin/<pkg>/<script>.py"`; hooks live in `plugin/hooks/hooks.json` in exec form. When adding agents, add `"agents": ["./plugin/agents/<name>.md", ...]` to `.claude-plugin/plugin.json` (the validator rejects a directory string for `agents`) and run `claude plugin validate .`.
- `plugin/state/` owns `status.yaml` (fields: id, slug, title, phase, entry_route, change_type, profile_override, gate{phase,result,reason,at}, parked_reason, iterations, external_ref, timestamps). `Status.park()`, `record_gate()` and `bump_iteration()` already exist for the gate to call. `conventions.HUMAN_GATES` gives the human gates per profile; `is_human_gate(profile, phase)` decides whether a gate waits for the owner or calls the confidence gate.
- The YAML subset reader/writer is `plugin/state/yamlish.py` (no PyYAML at runtime; never add a third-party runtime dependency — decision 7 and NOTES §1 explain why a crashing hook is worse than a missing one).
- The protected-path hook has no exception; the only sanctioned writer of guardrail files in a run is `plugin/init/sdlc_init.py`. Any B2 code that must write `.claude/**`, `CLAUDE.md`, `REVIEW.md` or `sdlc.yaml` goes through that script or is left to the owner.
- Commands are single-file prompts in `plugin/commands/`; deterministic work is Python called from them, so it is testable without a model (layer 1) and against the fixture (layer 2).

## Deliverables (in dependency order)
1. **Confidence gate** (step 16) as `plugin/gate/`: one function used by every autonomous phase. Deterministic checks — artifact exists and matches its template (intent/spec/plan section names), tests/build/lint green via the `sdlc.yaml` commands, evidence present for (d), no Important review findings (read a findings JSON; format to define now, produced by the review pass in B3), plan.md ↔ diff consistency (reuse `plugin/hooks/plan_sync.check`), no diff touching the guardrail files unless the change's intent.md says it is the framework itself, no risk-list hit (`sdlc.yaml: risk_list` words against the diff paths and the spec). Result: `continue` or `park` with reasons. Park = `Status.park(reason)`, the `sdlc:needs-human` label, and a "What I need from you" block for the PR description; never a notification (decision 11). CLI: `python "${CLAUDE_PLUGIN_ROOT}/plugin/gate/cli.py" check --root . --id 0001 --phase c`. Every check unit-tested with fixtures; the adversarial reviewer's verdict is an input to the gate (a JSON the agent writes), not something the gate runs itself.
2. **Agents** (step 17) in `plugin/agents/`: `verifier.md` (copy the article's p.25–26 example: tools Bash, Read; "Exercise the changed behavior and the two nearest neighboring flows … Do not fix anything; report only"), `code-simplifier.md`, `researcher.md`, `adversarial-reviewer.md` (fresh context; returns continue/escalate with reasons and a routine/non-routine classification for step 18, written as JSON into `changes/<id>-<slug>/evidence/`). All four "report only, do not fix". Register them in the manifest.
3. **Run limits** (step 19) in the gate: max fix iterations per phase (3; `status.iterations`), wall-clock per run, a per-change budget where the substrate exposes one, and a repo-level pause flag (`sdlc.yaml: paused: true` or a `changes/PAUSE` file — pick one and document). On any limit: park with partial evidence. Check the Claude Code CLI docs for `--max-turns` as the outer bound for `claude -p` runs (B3 uses it); record the answer in NOTES.
4. **Auto-accept conditions** (step 18): a deterministic preflight, `python "${CLAUDE_PLUGIN_ROOT}/plugin/gate/preflight.py" --root .`, that says whether the implementation run may use `--permission-mode acceptEdits`: CLAUDE.md present with the three commands, the policy skills present, the plugin's hooks loaded (check `hooks.json` reachable and `python` on PATH), one-command test target green. Never bypass-permissions mode (the template disables it). The routine/non-routine verdict tightens the gate (mandatory adversarial review, iteration cap 2) and never interrupts the owner.
5. **Policy skills** (step 20) in `plugin/skills/`: `coding-standards`, `security-baseline`, `ux-conventions`, `data-conventions`, `definition-of-done`. Each frontmatter description says when it triggers; each body names its written source (start from the article pages and the owner's own standards if provided; say "no owner source yet" otherwise) and ends, where possible, with a deterministic script call and its output (article p.22 pattern). Projects override in `.claude/skills/`. Static tests on frontmatter and sections, like `tests/test_commands_and_skills.py`.
6. **Full `/sdlc-init`** (step 21): extend `plugin/init/sdlc_init.py` and the command with `template/evals/` (empty suite with a README: filled by incidents from B5, decision 17), `template/bands.yaml` (the p.44 shape for CI test failure rate, decision 15), and non-Python detection for at least Node (package.json scripts) so a JS project gets its three targets. The CI workflows and the daily digest stay in B3. Keep it idempotent (the tests in `tests/test_init.py` define the contract: unchanged files stay untouched, comments survive).
7. **Docs**: `docs/PROGRESS.md` rewritten for session 2 (same structure, 5-bullet summary on top, a row per step 16–21, decisions not reopened, choices made, live checks owed, what is left for B3); `docs/NOTES.md` extended with any new docs fact (cite URL and quote); `README.md` if the usage changed.

## How the framework is tested (unchanged; layer 3 stays in B5)
1. Self-tests (`python tasks.py check`): every gate check, the preflight, run limits and the pause flag with fixtures; agents and skills statically (frontmatter, required sections, manifest registration); `claude plugin validate .` clean.
2. Fixture project (`tests/fixtures/sample-python-project/`): a copy initialised with the full `/sdlc-init`, then the gate run against a prepared change folder in states that must continue and states that must park (missing plan.md, failing test behind `SAMPLE_FAIL=1`, a diff touching `.claude/settings.json`, a risk-list word). Add a second minimal fixture for Node detection if step 21's non-Python detection is built.
3. Evals and shakedown: B5; do not simulate.

## Definition of done for this session
- `python tasks.py check` green (report the count) and `claude plugin validate .` clean; Windows run by the owner listed as owed if not confirmed.
- The gate, run against the fixture, returns `continue` on a clean change and `park` with the right reason for each prepared failure; parking writes `status.yaml` (gate result, parked reason) and prints the "What I need from you" block.
- The four agent files exist, are registered, and say "report only, do not fix".
- Preflight refuses auto-accept when any precondition is missing and allows it on the initialised fixture.
- Five policy skills with static tests; the full `/sdlc-init` writes evals/ and bands.yaml and stays idempotent.
- `docs/PROGRESS.md` for session 2 with the ≤5-bullet summary on top and the list of what B3 needs.

## Rules for this session
- Never reopen a decision in `docs/DECISIONS.md`; if one is technically impossible, document why in `docs/PROGRESS.md` and continue with the rest.
- Cite the PDF page in code comments or docs whenever the article is used.
- No notifications of any kind. No bypass-permissions mode. No third-party runtime dependency.
- Before the final commit run a fresh-context review of the diff against this handoff and the decisions, fix what it finds, and only then commit, push and open a draft PR against `main`.
- End with the ≤5-bullet summary at the top of `docs/PROGRESS.md`; the long version goes below it.
