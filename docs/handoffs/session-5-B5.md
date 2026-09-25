# Handoff — session 5: build stage B5 (maintain, evals, detection, scans, gate (f), observability; steps 33–43) and decision 26

Session 4's brief is kept at `docs/handoffs/session-4-B4.md`; its result is on `main`: PRs #32 (A), #34 (B), #35 (C), #36 (D), #37 (E), #38 (F), #39 (G), #40 (H), #41 (I) and #42 (J), with the owner's pin PR #33; plugin 0.2.12 → 0.2.18; A and #33 merged on 2026-09-23, B–J on 2026-09-24. Session 4 was interrupted once (the owner's PC died with PR B uncommitted; the PR was rebuilt in a cloud session from `docs/PROGRESS.md`) and then ran as one long cloud session that built, released and live-checked each PR against the sample repository before the next.

What is true at the start of this session: decisions 21 to 25 are built; 21, 22 and 24 are **live-proven** on `luissiviero/sdlc-sample-python` (change 0002: a deferred-review design with two panel decisions, the owner's overturn of one, the un-park label, and the first unattended (c) → (d) → (e) chain with a panel decision at (c) and at (e)); 23 is unit-tested; 25's abandon path is tested end to end but not yet live (live check 8 owed); the framework tags and releases itself on every merge that bumps `.claude-plugin/plugin.json` (`.github/workflows/sdlc-tag.yml`); every workflow reads the framework pin from the project's default branch. Decision 26 is the only adopted decision not built.

## Preconditions — check before building anything
1. PRs #32 through #42 are merged to `main` and this session starts from `main`; if not, stop and say so. `.claude-plugin/plugin.json` says 0.2.18 and `git ls-remote --tags origin` shows `v0.2.18` (sort as versions: `sort -V`).
2. The root `sdlc.yaml` pins 0.2.18 and the sample repository's `main` pins 0.2.18 (the owner applied both on 2026-09-24).
3. `python tasks.py check` is green in this session before the first edit (725 tests at the end of session 4, PROGRESS's closing bullet) and `claude plugin validate .` is clean.
4. Sub-agent model: `CLAUDE_CODE_SUBAGENT_MODEL=opus` in the cloud environment's variables; name `opus` in every sub-agent invocation and check with `/tasks`.
5. The cloud environment's setup script carries the two `update` lines of `docs/NOTES.md` §3a (owner action asked for on 2026-09-24; confirm in the first `claude plugin list`).

## Read in this order
1. `docs/OPERATING_MODEL.md` — the contract; §3 "Review mode", §4.1 (the panel step in every phase), §4.2 (the trigger table, the pin rule and the branch-migration sentence), §6 (labels and their stamps), §8 (the evidence files, the runner's records), §10 (what of 21–26 is built).
2. `docs/DECISIONS.md` — 26 settled decisions; 21 carries the 2026-09-24 amendment (panel calls are their own count). Do not reopen any.
3. `docs/PROGRESS.md` — the session-4 record on top: the summary, the definition of done, choices 31–65, the live checks 1–15 with their results, the known gaps, the "Left for B5" list this brief was written from.
4. `docs/NOTES.md` — platform facts; new in session 4: §3b (a cloud session cannot push a tag), §3c (a `labeled` event ran the PR head's copies of the workflow, the pin script and the pin; the one-time migration), §11 (GitHub Actions and Claude Code flags). Re-verify a fact before relying on it when the docs may have moved.
5. `docs/BUILD_GUIDE.md` — steps 33–43 (B5) and step 37 for decision 26; `docs/build_guide.json` must stay identical when a step is touched.
6. `docs/MODEL_ALLOCATION.md` — §2 for every session, §5 for this one.
7. `docs/reference/ai-native-sdlc-playbook.txt` — read a page when a step cites it (p.42–45 for maintain, detection and bands).
8. `CLAUDE.md` — conventions for this repo.

## Objective of this session
Complete build stage **B5**: phase (f) maintain — detection statistics and bands (step 37, with decision 26's pre-approved rehearsed rollback), the diagnose run and `/sdlc-maintain` (its composition is already in OPERATING_MODEL §4.1), incident records and lessons (36), evals (35), the weekly security review and the deterministic scanners (38), gate (f) triage and the dismissal store (39), observability (41, incl. 41.1), the two counters' report (42), the adoption reference (43). Worktrees (33) and the mock convention (34) need a recorded choice and a folder convention only.

## What session 4 left ready (build on it, do not rebuild)
- **Deferred review** (`plugin/panel/`): `items | prompt | record | overturn`; `record` commits the decision itself, counts against `gate.max_panel_calls` (`status.yaml: panel_calls`), closes a concern as `decided (by panel #n): …`; the gate's `panel` check reads the ledgers of every phase so far; `check_findings` and `check_adversarial_verdict` read the phase's ledger; the PR opens with "Decisions taken for you (N)"; every phase runbook and `/sdlc-fix` carry the panel step.
- **Fix rounds and labels**: `sdlc-fix.yml` on the owner's "Request changes" and on the three un-park labels (`state/unpark.py`, the actor and `iterations_reset_at` recorded), `workflow_dispatch(change_id, head_ref)` for a round by hand; `sdlc-abandon.yml`.
- **Release**: `sdlc-release.yml`, `release/cli.py`, the production-gate hook; the framework's own `sdlc-tag.yml` + `.github/scripts/sdlc_tag.py` (tag + release page on a version bump; `workflow_dispatch` to redo).
- **Runner** (`ci/run_phase.py`): one transcript per run (`claude-<phase>[-n].json`), the pin from the default branch (`sdlc_pin.py --ref`), `--find-change`, `--phase fix`.
- **Tests**: 725 (`tests/test_panel.py`, `test_tag_script.py`, the deferred end-to-end run in `test_ci_end_to_end.py`).
- **Sample repository**: change 0001 and 0002 merged; `main` pins 0.2.18; the workflows and `sdlc_pin.py` are the 0.2.17 copies.

## Deliverables (in dependency order; the step tasks are in MODEL_ALLOCATION §5)
1. **Step 37 with decision 26** — `plugin/detect/` (rolling statistics, Western Electric rules, tiers against `bands.yaml`; pure, unit-tested), the CI-test-failure-rate source through `urllib` with a file cache, the scheduled detection workflow in the template, the tier actions (1σ log, 2σ the read-only diagnose run, 3σ the intent PR through gate (e) or a pre-approved runbook; `authorization: go` parks with "Go" requested; a rollback runbook with `rehearsed_at` set by the owner is pre-approved on a declared production), the two default runbooks (quarantine a flaky test, open a revert PR; a runbook never edits a test), the runtime choice (a CI step or an Agent SDK service), `template/bands.yaml` reused as it exists (`authorization: preapproved | go`), the diagnose prompt, `CHECKS_BY_PHASE["f"]`, `/sdlc-maintain`.
2. **Step 36** — `template/lessons/`, the diagnose run reads `lessons/` first, a shipped incident fix appends the post-mortem and adds one eval case.
3. **Step 35** — after the 35.2 research note on `claude plugin eval` (URL and quote into NOTES): the eval JSON shape, `plugin/evals/run.py`, `evals/check.py` in the template, the framework-level suite on PRs to `plugin/**`, the per-project eval workflow in the template (PRs to `CLAUDE.md` and `.claude/**`, and nightly), the first cases from the live checks in PROGRESS.
4. **Step 38** — the weekly security review (which skill; read-only; bounded finding → PR through the review gate, wider → intent), the findings-to-route script with the dismissal store (reuse `review/findings.signature`), the deterministic scanners in the template's CI per detected language.
5. **Step 39** — gate (f) mechanics: `incident` and `schedule` labels, close-with-reason as a dismissal (decision 25's second half: the workflow on a closed-unmerged incident PR), a bands change only through a `bands.yaml` PR.
6. **Steps 41, 41.1, 42, 43, 33, 34** — every hook logs through `_common.log_decision` and the log is a CI artifact; the counters (42.1 exists: the `Counters:` line of the PR body) and the scheduled report over `changes/*/` and PR history (42.2, optional); the adoption reference; the "not built" record for worktrees (decision 17); the `mock/` convention in `changes/README.md` and the (c)/(d) prompts.
7. **Carried from session 4's known gaps** (do them where they touch code this session changes): the per-decision panel cost (choice 52); an owner `accept` verb for a review finding (a new decision — ask); the CI review-before-artifact order for a non-`none` adapter; the `Diff.files` conversion; the release-page backfill for v0.2.15–v0.2.17 (optional, one `workflow_dispatch` with a version argument if added); GitHub's review widget still showing "changes requested" after a fix round applied the comment (dismissal is the owner's; decision 20 forbids re-requesting) — record, do not build a notification; the deploy/status/rollback tools when a project's adapter names a real deployment (choice 35); the slow-test measurement; the monthly tuning of review findings (26.5); the `labeled`-event workflow-file question (verify from a job log when one can be read); the sample's first close-without-merge (live check 8, owed); owner-optional lines (`gate.max_panel_calls: 4` in the root `sdlc.yaml`, the template's note in place of its `# lite:` comment, the sample's `CLAUDE.md` Layout line for `mean`) and session 3's still-owed live items (the watch setting, the test-file lock seen live on Windows) — ask, do not assume.
8. **Docs**: `docs/PROGRESS.md` rewritten for session 5 (same structure); `docs/NOTES.md` extended (cite URL and quote); `README.md` if usage changed; `docs/BUILD_GUIDE.md` and `docs/build_guide.json` kept identical if a step is touched; OPERATING_MODEL §4, §4.1, §4.2, §9, §10 for phase (f).

## How the framework is tested
1. Self-tests (`python tasks.py check`): every hook, gate path and script with fixtures; commands, agents and skills statically; `claude plugin validate .` clean.
2. Fixture projects (`tests/fixtures/sample-python-project/`, `sample-node-project/`) for the Python halves of every runbook against a temporary copy with a bare remote; the end-to-end CI test with a fake `claude` (`tests/test_ci_end_to_end.py`).
3. Live checks on the sample repository: this session may run them itself when the repository is in its GitHub scope (session 4 did: `add_repo` with push, opened the pin PRs — the owner merged them, `sdlc.yaml` being a guardrail file there too —, the reviews and labels as the owner, `workflow_dispatch` of the phase workflows) — a branch created before 0.2.17 must first be updated from `main` once (NOTES §3c). Evals (35) become the fourth layer this session.

## Definition of done for this session
- `python tasks.py check` green (report the count) and `claude plugin validate .` clean.
- Detection statistics unit-tested on synthetic series; the three tiers act as decision 14 and 26 say; the diagnose run is read-only and writes an incident intent in the template's shape; gate (f) has its checks.
- The eval runner runs a suite non-interactively and fails on a regression; the framework suite has its first cases.
- The weekly security review and the dismissal store exist and are tested; the deterministic scanners are in the template's CI.
- Lessons, the mock convention and the worktree record exist; every hook logs its decisions; the two counters have their report.
- OPERATING_MODEL says what the code does for phase (f); §10 row 26 moves into the body.
- `docs/PROGRESS.md` for session 5 with the ≤5-bullet summary on top and the list of what remains (if anything).

## Model rule for this session (unchanged from session 4; `docs/MODEL_ALLOCATION.md` §1–2, `docs/NOTES.md` §11c)
- The session model stays Fable; delegated work runs on Opus (`CLAUDE_CODE_SUBAGENT_MODEL=opus`); check with `/tasks` after the first delegated task. Fresh-context reviews run as general-purpose sub-agents on Opus. Do not set `CLAUDE_CODE_SUBAGENT_MODEL_FORCE`. Sub-agents that edit code get disjoint file sets.

## Rules for this session
- Never reopen a decision in `docs/DECISIONS.md`; if one is technically impossible, document why in `docs/PROGRESS.md` and continue.
- Cite the PDF page in code comments or docs whenever the article is used.
- No notifications of any kind. No bypass-permissions mode. No third-party runtime dependency. Python for every script; the workflows are YAML whose `run:` lines call `python` (and the pinned `claude` install) only, never with a `${{ }}` in the line.
- `CLAUDE.md`, `.claude/**`, `REVIEW.md` and `sdlc.yaml` are guardrail files: propose the exact lines in `docs/PROGRESS.md` and leave the edit to the owner.
- A version bump goes into `.claude-plugin/plugin.json` and `marketplace.json` in the PR; the tag and the release page follow the merge by themselves. A cloud session cannot push a tag (NOTES §3b).
- Every PR: `python -m compileall -q plugin tests tasks.py .github/scripts`, the full `python -m pytest`, `python -m ruff check .`, `python -m ruff format --check .` — green before the push, with the output in the PR body. Session 4 pushed one red commit by chaining the push on the wrong exit code; do not.
- Before the final commit run a fresh-context review of the diff against this handoff and the decisions; fix what it finds; then commit, push and open a draft PR against `main`.
- End with the ≤5-bullet summary at the top of `docs/PROGRESS.md`; the long version goes below it, and the session-4 record is kept below that as written.
