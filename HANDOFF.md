# Handoff — session 3: build stage B3 (first autonomous phases, gates, merge-triggered plumbing; steps 22–30)

Session 2's brief is kept at `docs/handoffs/session-2-B2.md`; its result is on `main` once PR #6 is merged (PR #4, the gate, and PR #5, the agents, are already merged).

## Preconditions — check before building anything
1. PR #6 (session 2, last part) is merged to `main` and this session starts from `main`. If it is not merged, stop and say so.
2. The owner's live checks from `docs/PROGRESS.md` ("Live checks the owner can do now"). Read their status from the owner's first message; do not assume. If any is unreported, ask once and continue, marking the dependent step partial.
   - Windows: `python tasks.py check` green on the owner's PC (owed since session 1). If it failed, fixing it is the first task (the code is path-agnostic; NOTES §1).
   - Policy-skill and agent triggers in a live session (PROGRESS items 3–4): if they failed, fix the descriptions first (same style as `intent-template`, whose trigger passed).
   - Preflight `allow: true` in the sample repo (PROGRESS item 5).
3. `python tasks.py check` is green in this session before the first edit (203 tests at the end of session 2) and `claude plugin validate .` is clean.

## Read in this order
1. `docs/OPERATING_MODEL.md` — the contract (sections 3, 6 and 9 gained the gate mechanics in session 2).
2. `docs/DECISIONS.md` — 20 settled decisions. Do not reopen them; decision 1 (CI with API key or subscription token) and 12 (review pass as a CI job) are the ones B3 executes: re-read the consumer terms before choosing the subscription token (NOTES §2).
3. `docs/PROGRESS.md` — what exists after session 2, the 12 choices made, the live checks owed, and the B3 list this brief is written from.
4. `docs/NOTES.md` — platform facts; §3 (cloud sessions, `-p` runs ignore the project's marketplace declaration and allow rules in an untrusted checkout), §10 (subagents; `--max-turns`, `--max-budget-usd`, `--permission-mode`, `--permission-prompts none`, `total_cost_usd`). Re-verify a fact only if the minimum Claude Code version (2.1.228) changes.
5. `docs/BUILD_GUIDE.md` — steps 22–30 (B3) and, for the interfaces B3 must leave ready, steps 31–32 (B4).
6. `docs/reference/ai-native-sdlc-playbook.txt` — read a page when a step cites it (p.13–14 the design prompt; p.16 plan mode; p.27–29 the feedback loop and evidence; p.32–35 review passes and REVIEW.md; p.39–41 CI/CD).
7. `CLAUDE.md` — conventions for this repo.

## Objective of this session
Complete build stage **B3**: the first fully autonomous phase (`/sdlc-design`), the phase runbooks (`/sdlc-build`, `/sdlc-test`, `/sdlc-deploy`), the review pass and `/sdlc-fix`, the test-file lock, the PR summary and daily digest, and the merge-triggered `claude -p` workflows so that after gate (a) the owner never launches a phase by hand. Do not start B4 (release gate, production-gate hook, deploy adapters). Everything must still work by hand on the owner's PC and in a cloud session before the workflows exist.

## What session 2 left ready (build on it, do not rebuild)
- **The gate**: `python "${CLAUDE_PLUGIN_ROOT}/plugin/gate/cli.py" check --root . --id <id> --phase <phase>` (exit 0 continue, 3 wait, 4 park). It reads `sdlc.yaml`, `status.yaml`, the change's artifacts, `evidence/`, the diff against the default branch, and writes `status.yaml` + `evidence/gate-<phase>.json`. `--dry-run` for the definition-of-done skill. Phase runbooks call `start-run` first (wall clock) and `record-spend --usd <total_cost_usd>` after each `claude -p`.
- **Artifact contracts** in `plugin/gate/artifacts.py`: spec.md sections (Requirements · Design · Open questions from intent · Flagged concerns · Acceptance; an open concern is a list item starting with `[ ]` or `open`), plan.md sections, evidence file names (`test.log`, `build.log`, `lint.log`, `verifier.md`, screenshots), `adversarial-review-<phase>.json` (with `head`), `review-findings.json` (`findings[].severity important|nit`, `tally`), `gate-<phase>.json`, `run-<phase>.json`. Write a `spec-template` skill from these names for `/sdlc-design`; do not invent new ones.
- **Agents** `sdlc:verifier`, `sdlc:code-simplifier`, `sdlc:researcher`, `sdlc:adversarial-reviewer` (writes the verdict; the runbook passes the change id and phase). The calling run stores the verifier's report as `evidence/verifier.md`.
- **Preflight** `python "${CLAUDE_PLUGIN_ROOT}/plugin/gate/preflight.py" --root . --id <id>` → `permission_mode` for the implementation run and the iteration cap. Never bypass mode.
- **Policy skills** with `check.py` each; the design pass loads them (article p.14 prompt) and the review passes re-check them.
- **`/sdlc-init`** writes `evals/`, `bands.yaml`; it does not yet write the CI workflows or the digest job — B3 adds them to `template/` and to the installer (create-only, idempotent; extend `tests/test_init.py`).
- **State CLI**: `new-change`, `commit-phase`, `set-phase`, `park`, `accept-risk`, `show`, `list`, `labels`; `Status.bump_iteration()` for the fix loop.

## Deliverables (in dependency order)
1. **`/sdlc-design`** (step 22; decision 2): from the merged intent, run the p.14 prompt with the five policy skills loaded → `spec.md`; then the read-only planning run (`plan-template` skill; Read/Grep/Glob only) → `plan.md`; run the adversarial reviewer for phase (b); gate (b). Standard/Full: commit on `sdlc/<id>/b`, open the spec+plan PR with the ≤5-bullet summary and `sdlc:b-ready`. Lite: commit on the change branch and hand over to the build runbook after a `continue`. Re-runnable after review comments.
2. **Phase runbooks** (step 24): `/sdlc-build` (`start-run`, preflight → permission mode, implementation on `sdlc/<id>/c` under the hooks, code-simplifier, verifier → `evidence/verifier.md`, adversarial reviewer, gate (c), open or update the build PR), `/sdlc-test` (fresh context: full suite, build, lint into `evidence/*.log`, screenshots for UI changes, verifier, gate (d)), `/sdlc-deploy` (review passes → `evidence/review-findings.json`, fix loop bounded by `status.iterations` and the gate's cap, PR summary, gate (e) = the owner's merge). Each stops at a human gate with the ready label and parks on any gate failure; nothing notifies.
3. **Test-file lock** (step 25): PreToolUse hook denying edits under the test directories when `status.yaml: change_type == fix` on an `sdlc/<id>/c` or `/d` branch, after the failing test was committed; the REVIEW.md rule already exists. Unit-tested like `plugin/hooks/plan_sync.py`.
4. **Review pass + `/sdlc-fix`** (step 26; decision 12): a fresh-context review with REVIEW.md producing `review-findings.json` in the recorded format (tally by severity; framework rules as Important); `/sdlc-fix` reads unresolved PR comments and failing checks, re-runs the phase with them as constraints on the same branch, `bump_iteration()`, and parks at the cap.
5. **PR summary and daily digest** (step 27a; decision 20): the ≤5-bullet summary generated from `evidence/gate-<phase>.json`, the findings tally and the plan conformance; a scheduled digest of the queue (`sdlc:*-ready`, `sdlc:needs-human` first) as one issue or PR comment. The `sdlc:needs-human` label is applied when the gate parks (the gate prints it; nothing applies it yet).
6. **Merge-triggered workflows** (step 30; decisions 1, 5): one workflow per transition in `template/.github/workflows/`, installed by `/sdlc-init`: checks `status.yaml`, loads the pinned framework with `--plugin-dir` (NOTES §3: a `-p` run ignores the project's marketplace declaration), runs `claude -p` with `--max-turns`, `--max-budget-usd`, `--permission-mode` from the preflight, `--permission-prompts none`, the allow-list and sandbox of step 7, under the workflow token; pipes `total_cost_usd` into `record-spend`; dispatches the next phase explicitly (workflow-token events do not start runs); creates the `sdlc:*` labels on first run. Subscription token versus API key: decide per NOTES §2 after re-reading the terms; document in NOTES.
7. **Docs**: `docs/PROGRESS.md` rewritten for session 3 (same structure); `docs/NOTES.md` extended (cite URL and quote); `README.md` if usage changed; the next `HANDOFF.md` (B4) from the B3 progress, this brief archived under `docs/handoffs/`.

## How the framework is tested (unchanged; layer 3 stays in B5)
1. Self-tests (`python tasks.py check`): every hook, gate path and script with fixtures; commands, agents and skills statically; `claude plugin validate .` clean.
2. Fixture projects (`tests/fixtures/sample-python-project/`, `sample-node-project/`): the Python halves of every runbook against a temporary copy with a bare remote (as `tests/test_integration_fixture.py` and `tests/test_gate.py` do); the model-driven halves are prompts.
3. Evals and shakedown: B5; do not simulate. The first end-to-end autonomous run (intent merged → design PR opened by the workflow) is a live check on `luissiviero/sdlc-sample-python`.

## Definition of done for this session
- `python tasks.py check` green (report the count) and `claude plugin validate .` clean; Windows run by the owner listed as owed if not confirmed.
- `/sdlc-design` produces `spec.md` + `plan.md` for the fixture's change 0001 through their Python halves, and gate (b) continues on them.
- The three runbooks exist as commands over deterministic Python; each calls the gate and parks on failure; `evidence/` holds the named files after `/sdlc-test`'s Python half.
- The test-file lock hook denies a test edit in a fix-type change and allows it in a feature change (unit test).
- `review-findings.json` is produced in the recorded format; `/sdlc-fix` bumps the iteration and parks at the cap.
- The workflows are in the template, installed idempotently by `/sdlc-init`, and dispatch the next phase explicitly; the daily digest job exists.
- `docs/PROGRESS.md` for session 3 with the ≤5-bullet summary on top and the list of what B4 needs.

## Rules for this session
- Never reopen a decision in `docs/DECISIONS.md`; if one is technically impossible, document why in `docs/PROGRESS.md` and continue with the rest.
- Cite the PDF page in code comments or docs whenever the article is used.
- No notifications of any kind. No bypass-permissions mode. No third-party runtime dependency. Python for every script; the workflows are YAML that only call `python` and `claude`.
- Before the final commit run a fresh-context review of the diff against this handoff and the decisions, fix what it finds, and only then commit, push and open a draft PR against `main`.
- End with the ≤5-bullet summary at the top of `docs/PROGRESS.md`; the long version goes below it.
