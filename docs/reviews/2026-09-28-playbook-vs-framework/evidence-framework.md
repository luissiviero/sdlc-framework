# Evidence: the framework page against the code

> The adversarial verification of the six slice audits of the framework workflow page (Artifact 2) against this repository at f2a2b29 (plugin 0.2.26) and the sample project, as it stood on 2026-09-28 before the page was corrected. File:line references are at that commit. The corrected page is `framework-workflow.html` (plugin 0.2.27); the defects are issues #66, #67 and #68.

Inputs: R1, R2, R3, R4, R5, R6 (R6 arrived during the work and is included). Each finding below was re-checked
against the code by me. Paths without a prefix are relative to /home/user/sdlc-framework. [sample] means
/home/user/sdlc-sample-python or the GitHub API for luissiviero/sdlc-sample-python (read-only).

## 0. Must-settle items (definitive answers)

**a. Full profile: the label alone starts (d)/(e). No approving review is required anywhere.**
- `plugin/ci/run_phase.py:319-341` `check_approval` has three steps. It finds the open PR on `sdlc/<id>/c` and requires
  `label in pr.labels`. Then `label_applied_by_a_human` (:297-316) rejects only `actor == BOT_LOGIN` ("github-actions[bot]").
  With no token it skips the actor check ("note: no token, so the actor … is not checked"). No code reads a review state:
  a grep for `APPROVED|reviewDecision|review_decision` in plugin/ and template/ finds nothing relevant.
- What starts (d): the owner's own `labeled` event. `template/.github/workflows/sdlc-test.yml:29-30` has `pull_request: types: [labeled]`,
  and `:51` has `if: … github.event.label.name == 'sdlc:c-approved'`. `sdlc-deploy.yml:52` does the same with `sdlc:d-approved`.
  The event is the owner's, not the token's, so it fires the workflow directly and no dispatch is involved. `NEXT_WORKFLOW` dispatches only
  after a `continue` (`run_phase.py:151`). The guard also requires gate (c) `passed` (`GATE_MUST_HAVE_PASSED`, :938-947).
  A `wait` records `passed` (`gate/gate.py:252-253` "waiting for the owner"), and the change must not be parked (:921-922).
- Docs that still require an "approving review + label": `docs/OPERATING_MODEL.md:71` (row (c)) and the (d) row, `pr/description.py:103`,
  and `template/sdlc.yaml:7`. That is a docs-vs-code gap (see §2).

**b. quarantine-flaky-test and revert-pr are pre-approved and run with no human. Only rollback-deploy is `go`. CONFIRMED end to end.**
- `template/bands.yaml:33-40`: `pull_request`, `runbook:quarantine-flaky-test` and `runbook:revert-pr` are `preapproved`.
  `runbook:rollback-deploy` is `go`.
- `sdlc-detect.yml:164` runs `detect/cli.py finish`. `cmd_finish` (`detect/cli.py:967-1025`) judges the route. For a runbook route
  it calls `_act(...)` (:1007-1010). `_act` (:726-776) returns `go-requested` only when `authorization == GO and not
  authorized_by`. Otherwise it calls `runbooks.run(...)` immediately.
- `detect/runbooks.py:5-7`: "Every built-in runbook ends in a pull request into the review gate (merge to apply, close to
  drop), labelled `incident`". revert-pr goes to `sdlc/<id>/revert-<sha7>` and "never merges". quarantine goes to `sdlc/<id>/quarantine`.
  **So yes: a pre-approved built-in runbook opens its own PR, and the owner must merge that PR for it to take effect.**
  A pre-approved *project* runbook runs its `command` directly, with the job's secrets (runbooks.py:16-18).
- Exceptions that make these runbooks `go`: a forced (rehearsal) finding (`routes.py:185-196` `apply_forced`), and a stricter
  `sdlc.yaml maintain.runbooks[].authorization: go` (routes.py:160-161). Decision 26 works the other way: a rehearsed rollback on
  `deploy.production: true` becomes pre-approved (routes.py:172-181). Runbooks exist only at 3σ: `TIER_ROUTES = {2: (PULL_REQUEST,)}`.
  `sdlc-runbook.yml:15`: "A pre-approved route never comes here".

**c. Scan findings never run /sdlc-maintain. CONFIRMED.**
`sdlc-scan.yml:90-107` has three steps: `scan/cli.py review` (read-only `claude -p`), then `scan/cli.py route … --max-findings 3`, then the scanners. No step
calls `run_phase.py`. `scan/route.py:503-505`: "gate (f) on the filed change (no diagnosis run: the review already wrote the
intent and the proposal)". Only findings with `severity == "important"` are filed (route.py:126-127). [sample] 0004, 0006 and 0008 have no claude-f.json.

**d. Merging a change-0000 PR can start a design run for 0000. This is a real latent bug; nothing in the code guards against it.**
- After init, the 0000 status is `phase: a`, gate null, `parked_reason: null` ([sample] `changes/0000-sdlc-init/status.yaml`; set by
  `init/sdlc_init.py:568` `status.new_change(..., change_id=c.INIT_CHANGE_ID)`). Nothing ever moves it off `a`.
- `sdlc-design.yml:57-59`: `if: workflow_dispatch || github.event.pull_request.merged == true`. There is no head filter and no paths filter.
- `run_phase.py find_change` (:659-701): a head `sdlc/0000/a` resolves to `0000` (`resolve_change_id`, and the expected phase for b is `a`).
  A web head `claude/…` resolves through the PR's files to the single folder `changes/0000-sdlc-init/`.
- `guard` (:862-941): not paused. The phase is `a`, which `PHASE_BEFORE["b"] = ("a","f")` accepts. The change is not parked. `b` is not in `GATE_MUST_HAVE_PASSED`.
  `INIT_CHANGE_ID` appears only in `gate/checks.py:565,787` (design_scope at gate a), never in run_phase.py or sdlc-design.md.
  tests/test_ci.py has no 0000 case.
- What actually happens depends on the credential. On a first install the owner is told to add the secret *after* the merge
  (`sdlc-init.md:112-117`). With no secret, the run reaches `auth_mod.choose_auth(env)["auth"] is None` and returns `_skip`, a green job
  (run_phase.py:1279-1280). With a secret set, the run does start `/sdlc:sdlc-design 0000`: for example when the secret was added first, or on any later
  merged PR whose only change folder is 0000, such as an `/sdlc-init` upgrade re-run, which commits `changes` on `sdlc/0000/a`
  (sdlc-init.md:49,88). The run spends model budget and opens `design(0000)`.
- Live: never observed. PR #4 (the one that first carried the workflows, 14d04cd) still had the old
  `startsWith(head.ref,'sdlc/')` filter and a `claude/…` head, and no later PR touched `changes/0000-sdlc-init/`.
- Verdict: **REAL BUG (latent, code-derived, unobserved)**. The fix is a one-line exemption of `INIT_CHANGE_ID` in `find_change` or `guard`.

**e. An infrastructure failure ends red. It does not park. CONFIRMED.**
`run_phase.py:79-82` (exit 1 = "an infrastructure failure — the setup command failed, the CLI exited non-zero … or no pull
request carries the result"). Four paths return `EXIT_FAILED` without a park or a label: setup fails (:1270-1275), claude exits non-zero or `is_error` (:1435-1437),
there is no gate file (:1455-1461), or there is no PR (:1497-1501). `report_failed_run` (:1138-1169) only commits "run(<phase>): failed run record".
Exceptions that do park: a gate check that crashes (gate.py:214-222), a failed fix-request collection (:1296-1307), and owner_fields (:1400-1434).
The docs contradict themselves. OPERATING_MODEL.md:43 says an infrastructure failure "still parks". OPERATING_MODEL.md:109 says "a parked phase is a green job by design (only an
infrastructure failure is red)". [sample] fc24645 is a failed run record with no status change.

**f. At (e), merging a PARKED build PR still releases. At (a)–(d), merging a parked PR starts nothing (a silent green skip). At (f), merging a parked incident PR proceeds.**
- (e): `release/cli.py:252-283` checks four things: merged, head == `sdlc/<id>/c`, phase `e` read `on_default_branch`, and the approval if
  production. It never checks `parked_reason`. `state/status.py:308-328` `merged_at_gate_e` states "the park is lifted".
- (a)–(d): the next workflow's guard runs `if st.parked_reason: return … "is parked"` (run_phase.py:921-922). The gate must also have
  passed (:938-947), and `Status.park` records the result as `parked`. [sample] PR #5's merge produced build run 35682185667 "skipped: change 0001 is
  parked" (stale status).
- (f): run_phase.py:896-907 lifts a park on a merged incident PR ("the owner chose the pipeline over the runbook").
- Corollary (R6 #4, confirmed): the draft state is the only mechanical guard against merging the build PR before gate (e). The PR is opened with
  `--draft` at (c) (`PR_DRAFT_PHASES = ("c",)`) and marked ready only by /sdlc-deploy (`--ready`). The ruleset that sdlc-init.md §6 prescribes
  exempts the owner. [sample] PR #17 timeline: `ready_for_review 18:48:44Z luissiviero`, then `merged 18:49:03Z`, which was the owner un-drafting it in the middle of (e).

**g. /sdlc-deploy does not run the adversarial reviewer as a gate step. CONFIRMED.**
`gate/checks.py:686` `VERDICT_REQUIRED_AT = ("b","c","d")`. `check_adversarial_verdict` is listed for (e) (:1485), but a missing
verdict passes there ("no adversarial verdict required at gate (e)", :693-696). `sdlc-deploy.md` names the agent only as the
panel's devil's advocate (:139, deferred review). `agents/adversarial-reviewer.md:3`: "(b design, c build, d test)". [sample]
0002 evidence has adversarial-review-b/c/d.json and no -e. At (e), the fresh-context judge is the REVIEW.md pass (`review-findings.json` for HEAD).

**h. "Close with a comment = dismiss" needs a later dismissal PR that the owner merges. CONFIRMED.**
`sdlc-abandon.yml:21-27, 95-105` leads to `detect/cli.py dismiss --open-pr`. That command (`cli.py:1305-1357`) writes `changes/.dismissed.json` on
`sdlc/<id>/dismiss` and runs `github.create_pr(...)`, body "Merging records it …". The reason is the last comment by a person on the PR. With no such comment,
nothing is dismissed. The close always abandons the change as well (abandon step :87-93). A metric dismissal expires after one baseline window (bands.yaml:42-43). [sample] Dismiss PRs
#27 and #33 were opened by github-actions[bot] and merged by the owner.

**i. The legend is wrong for Setup and (a). CONFIRMED.**
[sample] GitHub API: PRs #1, #2 and #4 (0000) and #3 and #12 (intent) have `user.login = luissiviero`. Every phase PR (#5, #7, #13, #17, #19, #25-#28, #30, #33-#35,
#46, #47) is `github-actions[bot]`. `sdlc-init.md:4` and `sdlc-plan.md:4` have `disable-model-invocation: true`, and `sdlc-plan.md:11` says "the only interactive
phase".

### Coordinator's R6 questions
1. **R6 #5 (no check run for gate (d)) is REFUTED.** The CI session runs the same `/sdlc:sdlc-test` command, and its step 6 is
   `pr/cli.py upsert … --phase d --check-run` (sdlc-test.md:134-141). The claude subprocess keeps `GITHUB_TOKEN`:
   `auth.credential_env` strips only the Claude credentials (auth.py:65-78). Live: `GET /commits/504093059e2c…/check-runs` returns
   `sdlc/d`, conclusion `success`, app `github-actions`, on commit 5040930 "test(0002): gate (d) evidence". [sample] 0002 claude-d.json
   says "phase (d) check run posted as `success`". R6 missed it because the later (e) commits moved the PR head, and the PR's
   checks tab shows only the head commit. The caveat R2 raised is correct: the runner's backstop upsert (run_phase.py `ensure_pr`) passes no `--check-run`,
   so the check run depends on the model reaching step 6, and it is not a required check.
2. **R6 #4:** no guard except the draft state (see f). The design relies on the owner. See also defect X2 (double release).
3. **R6 #1:** CONFIRMED, with a correction. 0ad707c (2026-09-25 18:59Z, plugin.json → 0.2.21) added `merged_at_gate_a` + `set_phase("a")`
   in the guard, plus the precondition in sdlc-design.md. `PHASE_BEFORE = {"b": ("a","f")}` already existed before 0ad707c
   (`git show 0ad707c^:plugin/ci/run_phase.py:136`). So at 0.2.19 the workflow fired and the guard passed, but the *model* refused on the raw `phase: f`,
   which gave a red job ([sample] fc24645). The edge is correct at HEAD.

---------------------------------------------------------------------------------------------------------
## 1. Verified findings on Artifact 2, de-duplicated, by severity

### HIGH
| # | Artifact element | What's wrong | Code evidence | Suggested correction |
|---|---|---|---|---|
| H1 | Diagram A `GO` → `RB` "sdlc-runbook.yml runs the runbook once: quarantine-flaky-test, revert-pr or a project runbook". Table (f) framework cell. [R3 M13/M20, R5 F-a] | The two built-in runbooks are `preapproved` in the shipped bands.yaml. At a real 3σ breach they run from `detect/cli.py finish` with no human and each opens its own PR. Only `go` routes (template: `runbook:rollback-deploy`, a project runbook that needs a `command`) wait for `sdlc:go`, as does any runbook of a forced rehearsal. | bands.yaml:33-40; detect/cli.py:1003-1015, 743-776; routes.py:160-196; sdlc-runbook.yml:15 | Add a solid edge F3 → "pre-approved runbook runs now (quarantine / revert PR, or a project runbook's command)". Relabel GO/RB to "a `go` route, e.g. runbook:rollback-deploy (project runbook); rehearsals always need Go". |
| H2 | Diagram B: the edge `PARK → OWNER → "merge or approval label" → The next phase starts`. [R4 B6; R4 rated MEDIUM, raised] | At (a)–(d), merging a parked PR (or labelling one) starts nothing. The next workflow's guard skips it as a green job, and the change is left stranded. Only at (e) (release) and (f) (incident merge = gate a) does a merge of a parked PR proceed. | run_phase.py:921-922, 938-947; status.py:308-328; run_phase.py:896-907; [sample] build run 35682185667 "skipped: change 0001 is parked" | Draw "merge or approval label" from READY only. From PARK: fix round, un-park label, or close. Add a note: "merging a parked PR at (e) still releases; at (b)–(d) nothing follows". |

### MEDIUM
| # | Artifact element | What's wrong | Code evidence | Suggested correction |
|---|---|---|---|---|
| M1 | Legend "box = a run or workflow under the automation identity" (I0, I1, A1, A2). Footer "by hand". [R1 L2, R5 G2/G5] | /sdlc-init and /sdlc-plan are the owner's interactive sessions. Their PRs are opened with the owner's credentials. By-hand phase runs are also not under the automation identity. | sdlc-init.md:4, sdlc-plan.md:4,11; [sample] PR authors (see i) | Give Setup and (a) a third style ("the owner's Claude Code session"), or: "box = a Claude run; unattended runs use the automation identity (github-actions[bot])". |
| M2 | Setup subgraph and Setup table row: nothing between "Owner merges the 0000 PR" and /sdlc-plan. [R1 S7, R5 O3/O4/T1o (HIGH→MEDIUM), R6 A-I1b] | Several owner steps are missing. (1) Allow Actions to create PRs. (2) The secret `CLAUDE_CODE_OAUTH_TOKEN`/`ANTHROPIC_API_KEY`. Without these two, every phase job skips or cannot open its PR. (3) The "Restrict updates" ruleset, owner Exempt; this is the only thing that keeps merges with the owner. (4) The project's own CI workflow, without which the (f) metric has no observations. (3) is DRIFT: added in 0.2.25, Exempt in 0.2.26. | sdlc-init.md:102-143, 70-74; run_phase.py:1279-1280; detect/source.py:1-11 | Add an owner hexagon after I2: "Owner, once: let Actions open PRs · add the Claude secret · ruleset 'Restrict updates' · a CI workflow for the metric". |
| M3 | Diagram A F2 → F3: a scan finding goes through "/sdlc-maintain --diagnosis-only reads lessons/ …". [R3 M11, R5 W10, R6 A-F3] | Scan findings get no diagnosis. `scan/cli.py route` files a template intent with a fixed `pull_request` proposal, runs gate (f) and opens the PR. At most 3 per week, Important only. | sdlc-scan.yml:90-107; scan/route.py:503-505, 126-127; [sample] 0004/0006/0008 have no claude-f.json | Route F2 directly to "incident intent PR (template intent; the PR is the route)". Keep the /sdlc-maintain box for F1 only. |
| M4 | Diagram A GF "close with a comment = dismiss". Diagram B AB "an incident PR closed with a comment also dismisses its finding". Table (f) owner cell. [R3 M16/B1/T1, R4 B9b, R5 O6, R6] | The close opens a dismissal PR on `sdlc/<id>/dismiss`, and only the owner's merge of it records the dismissal. The reason is the last comment by a person. A metric dismissal expires after one window. The close always abandons the change. | detect/cli.py:1267-1357; sdlc-abandon.yml:21-27, 95-105; bands.yaml:42-43; [sample] #27, #33 | "close = abandon; with a person's comment, a dismissal PR opens: merge it to record the dismissal (a metric dismissal lasts one window)". Table owner (f): "…; merges dismissal and runbook PRs". |
| M5 | Diagram B note: "Always parks … an infrastructure failure". [R4 BN4] | An infrastructure failure is a red job with a failed-run record. It has no park and no `sdlc:needs-human`, so it never appears in the queue. | run_phase.py:79-82, 1138-1169, 1435-1437, 1455-1461, 1497-1501 | "…a run limit the gate reaches. An infrastructure failure ends the job red (no queue item); a check that crashes parks." |
| M6 | Diagram C step S4 "Adversarial verdict, fresh context, for HEAD", which the intro applies to /sdlc-deploy as well. [R4 C5] | No verdict is required or run at (e). There the fresh-context judge is the REVIEW.md pass (its own `claude -p` job in CI). | checks.py:686, 693-696; adversarial-reviewer.md:3; [sample] no adversarial-review-e.json | "Adversarial verdict (b–d) / REVIEW.md pass (e), fresh context, for HEAD". |
| M7 | Diagram C S0 "Guard" and S9 "Hand over", presented as steps of every command "by hand or by run_phase.py". [R4 C0/C1/C10, R5 T-footer] | Guard and dispatch are the CI runner's. By hand there is no approval-label check (preflight.py has none) and no dispatch: the owner runs the next command. The guard list also omits "not parked" and "previous gate passed". A failed guard is a green skip, while a guardrail edit parks. | run_phase.py:862-941, 1961-1979; gate/preflight.py (no label check); sdlc-build.md:171-172 | Mark S0 and S9 as "(CI runner)". Guard: "paused, abandoned, phase, not parked, previous gate passed, Full label by a person". |
| M8 | Diagram A R1 "release/cli.py run: runs sdlc.yaml deploy.command" → LIVE "Change is live". Table (e) framework cell. [R2 R1a/LIVE/T-e-fw, R6 A-LIVE] | The command runs only for the change's build PR at phase e, after the approval on production. `/sdlc-init` writes `command: ""` and asks for none, so a fresh project deploys nothing. A failing command is a red job. | release/cli.py:245-319; template/sdlc.yaml:58; sdlc-init.md:57 (no deploy-command flag) | "checks it is the build PR at (e), then runs deploy.command (empty by default: nothing runs until the owner sets it)". |
| M9 | Diagram A GE "Owner merges the build PR" (gate (e)). [R6 A-GE] | Nothing but the draft state stops an early merge. The owner can un-draft and merge mid-run. The (e) run then continues and opens a second build PR, and each merge fires the release (see defect X2). | [sample] #17 `ready_for_review 18:48:44Z`, merged 18:49:03Z, then #19; run_phase.py PR_DRAFT_PHASES; release/cli.py (no gate check beyond phase e) | Note: "merge only after sdlc:e-ready; an earlier merge still releases and the run opens a second build PR". |
| M10 | Diagram A RB as a dead end; the (f) owner cell. [R3 M21/T1, R5 O7] | A built-in runbook ends in its own PR that the owner merges or closes, and the incident PR goes back to `sdlc:f-ready` for triage. A failed Go setup parks the incident (0.2.24, DRIFT). | runbooks.py:5-15; detect/cli.py:1092-1102; sdlc-runbook.yml:109-122 | RB → "runbook PR (owner merges)" and RB → GF. |

### LOW
| # | Element | Finding (verified) | Evidence |
|---|---|---|---|
| L1 | Dashed edges C2→D1 and D2→E1 "owner approves and applies sdlc:c/d-approved"; table (c),(d) owner cell [R2 E-C2D1f/T-cd, R5 T4o] | Only the label (applied by a non-`github-actions[bot]` actor) is enforced. The approving review is not checked. The artifact follows the docs, so the gap is mainly docs-vs-code (§2 D1). | run_phase.py:297-341 |
| L2 | I1 0000 PR contents [R1 S6, R5 D6] | The list is missing `.github/scripts/sdlc_pin.py` (every pin step reads it) and the optional `ruff.toml`. At 0.2.19 the commit had no `lessons/` or `.github/workflows`; the artifact became right at 0.2.25 (56594b4/c12aadb). | sdlc-init.md:88; sdlc_init.py:279 |
| L3 | I0 questions [R1 S4, R5 O1] | Also asked: "real production?" (`deploy.production`), the metric's source, and confirmation of the four commands. | sdlc-init.md:30-42 |
| L4 | B2→GB "wait: sdlc:b-ready"; E2 only the ready path [R1 B4, R2 E2e] | Gates (b) and (e) can also park. Diagram B covers this generically. | gate.py:225-226 |
| L5 | Diagram B note "Always parks" list [R4 BN5, R5 D10] | The list is incomplete. Every failed check that is not one of the 5 panel kinds parks: red commands, evidence, clean_tree, artifacts, plan_sync, design_scope, owner_actions, panel, test_lock (0.2.25). The owner_fields park is new in 0.2.26 (DRIFT). A CI pause is a green skip, not a park. | ledger.py:68-82; panel/cli.py:167-168; run_phase.py:866-869, 1400-1434 |
| L6 | E1 order and E2 "release-notes.md" [R2 E1b/E2b] | By hand, the release artifact is prepared before the review; in CI a review job runs first and is redone when HEAD moves. release-notes.md is written by release/notes.py after the gate. | sdlc-deploy.md:38-42, 172-180; sdlc-deploy.yml:94-106 |
| L7 | D1 "screenshot loop" [R2 D1d] | Only when the plan or spec names a mock. | sdlc-test.md:59-68 |
| L8 | F1 metric, LIVE→F1 edge, 1σ [R3 M2/M5/M22] | The only source is CI test failure rate (GitHub Actions runs API). Detection is an independent daily cron; the release dispatches nothing. At 1σ it only logs. | detect/source.py:1-11; sdlc-release.yml:29; bands.yaml:21-22 |
| L9 | F1→F3 / F2→F3 labels [R3 M6/M9] | Filing is skipped when the finding is dismissed or an incident is already open. At 2σ the only route is the intent PR. Scans are capped at 3 per week and the scanners file nothing. | detect/cli.py:575-596; routes.py:52; sdlc-scan.yml:107-110 |
| L10 | GF "schedule" [R3 M15, R5 L11] | This is a plain label that nothing acts on (the digest shows it). | conventions.py:84-89 |
| L11 | Note under A: lessons + eval at (e) [R3 N2/N3] | These are prompt instructions only, not gate-checked, and never exercised live. Only detection diagnoses read lessons/. | sdlc-deploy.md:58-76; no "lesson" in plugin/gate or plugin/ci |
| L12 | Hook note [R4 H4/H5/H7] | The formatter hook is formatter + linter (ruff, Python only, switchable). Plan sync runs only on `sdlc/<id>/c`. The production gate is inert unless `deploy.production: true`. | format_on_edit.py:1-11; plan_sync.py:1-17 |
| L13 | Diagram B FIX trigger [R5 D1, R4 B7] | Only an OWNER/MEMBER/COLLABORATOR "Request changes" starts it (0ad707c, 0.2.21). There is also a `workflow_dispatch`. | sdlc-fix.yml `if:` |
| L14 | Table "Any gate" [R4 T1] | An un-park label is carried out and then runs a fix round (iterations +1); it is not a separate "un-park" outcome. | run_phase.py:1287-1294 |
| L15 | Command spelling [R1 S1, R5 2.3] | The artifact mixes `/sdlc:sdlc-init` with `/sdlc-plan`, `/sdlc-design` and so on. Installed commands are `/sdlc:sdlc-*`. | plugin.json:3; run_phase.py builds `/sdlc:{cmd}` |
| L16 | Omitted owner options [R5 P3/O8/O9, R6 B-unshown] | Per-change `profile_override`/`review_override`, approved at the intent merge since 0.2.26. `paused: true` as a kill switch. Pin bumps and workflow-copy upgrades. Manual `workflow_dispatch` re-runs. | sdlc-plan.md:33-35; run_phase.py:925-940 |
| L17 | Eyebrow "0.2.19" | This is a stated snapshot and it matches tag v0.2.19. HEAD is 0.2.26 (DRIFT, informational). | plugin.json:4 |
| L18 | Diagram B "Decisions taken for you (N)" on "the next PR" [R4 BN7] | Imprecise. The block sits on the phase's own PR (the build PR accumulates (c)–(e)). OPERATING_MODEL.md:43 itself says "The PR at the next human gate", so this is cosmetic. | description.py:398-433 |
| L19 | GF→B1 "merge is gate (a) of the incident change" [R3 M24, R6 #1 HIGH] | MATCH at HEAD. At 0.2.19 the design model refused (fixed in 0ad707c, 0.2.21). R6's HIGH is downgraded: the task judges HEAD, and the edge is right there. Omitted detail: a merge while a Go is pending drops the runbook. | run_phase.py:896-907 |

## 2. Verified docs-vs-code disagreements
| # | Doc | Code | Sev |
|---|---|---|---|
| D1 | OPERATING_MODEL.md:71 and the (d) row, `pr/description.py:103`, `template/sdlc.yaml:7`, `conventions.py:100` say "approving review + label" | Only the label and its actor are read (run_phase.py:319-341). The actor check rejects only `github-actions[bot]`, while the release approval rejects any `[bot]` (release/approval.py). By hand, nothing checks the label (preflight.py). | MEDIUM |
| D2 | OPERATING_MODEL.md:43 says an infrastructure failure "still parks" | It is a red job with no park (see e). The same file's :109 agrees with the code. | MEDIUM |
| D3 | OPERATING_MODEL.md:74 lists "(or a scan finding)" as input to /sdlc-maintain | Scan findings get no diagnosis run (scan/route.py:503-505). | MEDIUM |
| D4 | OPERATING_MODEL.md:58 says closing an incident PR "dismisses" (unconditional). The sdlc-scan.yml:19-20 comment says "does not return". | A person's comment is required, and the dismissal lands only once the dismissal PR is merged (detect/cli.py:1264, 1305-1357). A pending scan dismissal does not stop re-filing (scan/cli.py:233 reads only the checkout's store; detection does read pending branches, detect/cli.py:352-377). | LOW |
| D5 | OPERATING_MODEL.md §4.2 design row: guard = "phase a, not parked, not paused" | The guard also accepts `f` for a merged incident and skips an abandoned change (run_phase.py:141-142, 877-906). | LOW |
| D6 | OPERATING_MODEL.md:76 and sdlc-deploy.md:40-42: the release artifact comes before the review | sdlc-deploy.yml:94-106 runs the review job first, and it is redone when HEAD moves. The effect is the same. | LOW |
| D7 | template/evals/README.md:82-83 says evals run on a plugin-version change | sdlc-evals.yml triggers only on `CLAUDE.md`, `.claude/**` and `evals/**`. | LOW |
| D8 | OPERATING_MODEL "read-only planning run" | It is a prompt-restricted pass in the same session, which has Write and Bash (run_phase.py:166). | LOW |

## 3. Potential real defects in the framework
| # | Defect | Evidence | Sev |
|---|---|---|---|
| X1 | **Change 0000 can get a design run** when merged (with a secret present) or on any later merged PR that touches only `changes/0000-sdlc-init/` (for example an /sdlc-init upgrade re-run on `sdlc/0000/a`). There is no exemption anywhere in find_change or guard, and no test covers it. | §0 d | MEDIUM |
| X2 | **Double release / release of unreviewed code.** release/cli.py requires only: merged, head `sdlc/<id>/c`, phase `e`. `set-phase e` happens at the start of /sdlc-deploy (sdlc-deploy.md:36), so a build PR merged mid-(e) releases the pre-review code. The (e) run then opens a second PR from the same head, and merging that releases again. Seen live with `action: none`: #17 → release run 36043873941 reached the action step at "phase: e", and #19 → 36147261876 did the same (R6 logs). With a non-empty deploy.command it would have run twice. Nothing records "already released". | release/cli.py:252-319; [sample] #17 timeline, #19 | MEDIUM (HIGH once a real deploy.command is set) |
| X3 | A parked build PR merged at (e) releases (the park is lifted by `merged_at_gate_e`), even when the park reason is a risk-list hit or a guardrail change. Only production + `sdlc:release-approved` adds a second human act. | status.py:308-328; release/cli.py (no parked check) | MEDIUM (it is a deliberate owner merge, but the park reason is not re-surfaced) |
| X4 | A parked PR merged at (b)–(d) strands the change: the next workflow skips it green and nothing tells the owner. | run_phase.py:921-922 | LOW–MEDIUM |
| X5 | The actor check on the Full-profile label rejects only `github-actions[bot]`, while the release approval rejects all `[bot]` accounts and `automation_identity`. With no token, the actor is not checked at all (run_phase.py:337-339). | run_phase.py:311-313, 337-339; release/approval.py:6-12 | LOW |
| X6 | A pending scan dismissal does not suppress next week's re-filing (detection does handle this). | scan/cli.py:233 vs detect/cli.py:352-377 | LOW |
| X7 | The gate (d) check run depends on the model reaching sdlc-test step 6; the runner's backstop upsert never posts one. | run_phase.py ensure_pr (no --check-run) | LOW |
| X8 | status.yaml on main goes stale after merges or abandons (0001 "e, parked", 0005 "f"). This is observational (R6 X-state). | [sample] | LOW |

## 4. REFUTED or corrected findings
| Finding | Verdict | Reason |
|---|---|---|
| R6 A-D2 / #5 "check run for gate (d) not observed; run_phase.py never posts one → MISMATCH MEDIUM" | **REFUTED** | A check run `sdlc/d` with conclusion success exists on 5040930 (the gate (d) evidence commit of 0002), posted by the CI session through sdlc-test.md step 6. The session keeps GITHUB_TOKEN (auth.py:65-78). It does not show on the PR because the head moved on. The artifact's "check run on the PR" holds; see X7 for the caveat. |
| R6 #1 "GF→B1 HIGH" | **SEVERITY CHANGED → LOW (informational)** | The artifact is correct at HEAD, and the audit is against HEAD. At 0.2.19 the guard already accepted `f`; the model refused. 0ad707c fixed it. |
| R5 top-1 "Setup owner acts HIGH" | **SEVERITY CHANGED → MEDIUM** (M2) | This is a missing step. It does not misstate who decides at any drawn gate. |
| R2/R4 "Full-profile approve" MEDIUM on the artifact | **SEVERITY CHANGED → LOW** (L1), with the docs-vs-code part kept as MEDIUM (D1) | The artifact reproduces the contract. The code is laxer. |
| R4 BN5 "incomplete always-parks list" MEDIUM | **SEVERITY CHANGED → LOW** (L5) | "the other judgment items go to the panel" is accurate for the 5 panel kinds. Red tests and similar are not judgment items. |
| R4 B6 MEDIUM | **SEVERITY CHANGED → HIGH** (H2) | It misstates what a merge triggers, and the change is stranded silently. |
| R4 BN7 "next PR" | **Downgraded to cosmetic** (L18) | OPERATING_MODEL.md:43 uses the same wording ("The PR at the next human gate"). |
| R1 S8 / R5 §2.8 "UNVERIFIED" for 0000 | **Settled: real latent bug** (X1) | It is not an artifact error, and it is unobserved live. On a first install with no secret, the job skips green (run_phase.py:1279-1280). |
| R6 A-B-owner-merge-park "MATCH (happened)" | **Corrected** | PR #7 was merged while parked, but no release workflow existed then. It shows the merge is possible, not that the next phase starts (see H2). |
| R2 "double release UNVERIFIED" | **Upgraded to CONFIRMED** (X2) | Both merges (#17 and #19) reached the release action step (R6 logs); the code path is confirmed. |
| R5 T5f "(e) framework: runs deploy.command MATCH" vs R2 PARTIAL | **R2 upheld** (M8) | The command runs only when set, and the release workflow runs it after the merge; the phase run does not. |
