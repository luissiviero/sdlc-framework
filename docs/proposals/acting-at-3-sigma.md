---
type: Proposal
title: Acting at 3σ — the Go is the owner's own, a rollback needs a release in the window, a route changed by comment is dispatched by the runner
description: The sdlc:go label counts only from the owner's account; a rehearsed rollback on a declared production is pre-approved only when the breach window holds a release, read from the release record, and otherwise waits for the owner's Go; a "Request changes" comment that names another route makes the fix round write the proposal only, and the runner's own step dispatches it after the session, with the runbook secrets in that step alone.
status: proposed
roadmap: R41
sources:
  - id: study-entry
    resource: docs/reviews/2026-09-28-playbook-vs-framework/target-design.md
    title: "T24, confirmed at the close of the study on 2026-10-09; from the crosswalk row maintain-act (better: the framework; decision: blend, option B), 2026-10-07; the T1 annotation of the same day (sdlc:go closed for that label)"
  - id: record
    resource: docs/reviews/2026-09-28-playbook-vs-framework.md
    title: "Section 7, the close (all 32 entries confirmed as recommended); section 8, the close table row T24 (maintain-act; D26 a release in the window, D14 narrowed to the owner's account) and the confirmed order"
  - id: crosswalk
    resource: docs/reviews/2026-09-28-playbook-vs-framework/crosswalk.json
    title: "Row maintain-act whole; the decision fields of deploy-envs (T20), deploy-review (T14), deploy-release (T21), deploy-approve (T18), deploy-comments (T17), x-roles (T1) and test-gate (T12)"
  - id: playbook
    resource: docs/reference/ai-native-sdlc-playbook.pdf
    title: "p.40 step 6: rollback the most rehearsed path, proven in advance; p.43 step 3: at 3σ Claude acts only by a PR into the review gate or a preapproved runbook; p.44-45: runbooks approved in advance; p.45: the examples, the rollback 'with a deployment in the window'; p.49-50: the Claude Tag channel and its 'human authorization'"
  - id: decision-14
    resource: docs/decisions/14.md
    title: "Decision 14: split by blast radius; Go for anything that touches a running system (kept; its Go narrowed to the owner's account)"
  - id: decision-26
    resource: docs/decisions/26.md
    title: "Decision 26: a rehearsed rollback pre-approved on a declared production (amended: a release in the breach window as a second condition, beside R39's fresh rehearsal)"
  - id: decision-27
    resource: docs/decisions/27.md
    title: "Decision 27: whether the actor of the (c) and (d) approval labels must be the owner's own account is decided with T17, T18 and T24 (T24's note narrows sdlc:go only; R17's accepted point 3 settles the labels the same way, see 'What to settle')"
  - id: r17
    resource: docs/proposals/claude-comment-fix-round.md
    title: "R17 (T17), accepted by the owner on 2026-10-14 as recommended (PR #208): how the owner's account is known, is_owner_actor, 'T18 and T24 call it when they arrive'"
  - id: code
    resource: plugin/detect/cli.py
    title: "_act, _judge, cmd_dispatch, cmd_finish, _human_label_actor, cmd_go; with plugin/detect/routes.py, plugin/detect/runbooks.py, plugin/gate/checks.py check_route, plugin/release/cli.py, plugin/ci/run_phase.py session_env, plugin/commands/sdlc-fix.md, template/bands.yaml, template/sdlc.yaml and the sdlc-detect, sdlc-runbook and sdlc-fix workflows; read at main 5542406, plugin 1.0.1"
generated: { by: sdlc-framework-session/ccr-01de3f80-ilnomi, at: 2026-10-15T20:00:00Z }
---

# Acting at 3σ: the Go is the owner's own, a rollback needs a release in the window, a route changed by comment is dispatched by the runner

**Status: proposed (roadmap R41), from study entry T24, confirmed by the owner on 2026-10-09, option B of the crosswalk row maintain-act (the letters are the row's own).** Nothing is built. It amends decision 26: a rehearsed rollback is pre-approved only when the breach window holds a release, a second condition beside the fresh rehearsal R39 (T20) adds; the decision file comes before the intent, in a documentation PR of its own, and this proposal writes no decision file and reserves no number. Decision 14 is kept, its Go narrowed to the owner's account through the check R17 settled. In the confirmed order it sits in the group "the rest in any order"; the Go's line is placed by R11 and "no ping" by R20; the accepted R19 and R20 leave to this entry the act's row in R19's table and the digest's refresh after the runbook workflow (Order); the review pass on the runbook PRs is R36's (T14).

## The problem

At 3σ the framework acts through a route the project lists, and the split by blast radius (decision 14) holds. The owner's note answers the row's question, whether decision 26 going one step past the article is still comfortable: yes, as T20 amends it (R39: the owner's `rehearsed_at` plus a passing rehearsal within N days)[^entry]. Three gaps remain:

- **The Go is any person's.** `sdlc-runbook.yml` runs the runbook when the `sdlc:go` label's actor is not a `[bot]` and not the automation identity; the owner is not checked. That was T1's open item, which the owner's note closes for this label[^r17]; decision 27 left the same question, "whether the actor must be the owner's own account", for the (c) and (d) approval labels to T17, T18 and T24[^decision-27].
- **A rehearsed rollback runs whatever was released.** Decision 26 pre-approves it on the `rehearsed_at` date alone. The article's rollback is triggered "with a deployment in the window" (p.45); with nothing released in the window, a rollback rolls back the wrong thing.
- **A route changed by comment is dispatched inside the model's session.** A "Request changes" comment on the incident PR that names another route makes the fix round rewrite `proposal.json` and re-run the dispatcher inside the session: a pre-approved built-in runbook would run there with the session's token, and a project runbook's command would run without the secrets the detect job's finish step holds, and the record is written from inside the session rather than by a deterministic step.

## What the article says

At 3σ "Claude may act, though only by opening a PR into the review gate or triggering a preapproved runbook" (p.43 step 3). In the governance considerations, "the runbooks the agent may trigger were approved in advance" (p.44-45). The examples: at 3σ on the CI test failure rate "the agent quarantines the flaky test or opens a revert PR, and the review gate decides"; "when the post-deploy 5xx rate breaches 3σ with a deployment in the window, the agent triggers the existing rollback pipeline" (p.45). Rollback "should be the most rehearsed path in the pipeline … exercised regularly in staging … so it has to be proven in advance" (p.40 step 6). The Claude Tag section leaves the response to "anyone in the channel able to guide and action the response", and its figure records "request, diagnosis, human authorization and fix" (p.49-50); the figure's exchange, "The rollback was rehearsed in staging this morning; shall I run it?" and "Go.", is quoted by decision 26 and by the header of `sdlc-runbook.yml`, and is not in the page-tagged text[^playbook]. The article's authorization is a person in the channel; the framework's, under the one-owner premise (x-roles, R28), is the owner.

## What the framework does today

Read at `main` 5542406, plugin 1.0.1 (`.claude-plugin/plugin.json:4`). The entry's "Today" was read at 619f01a (0.3.5) or later; `git diff --stat 619f01a 5542406` over `plugin/detect`, `plugin/release`, `plugin/state/unpark.py`, `plugin/commands/sdlc-fix.md`, `template/bands.yaml`, `template/sdlc.yaml` and the detect, runbook and fix workflows touches only `plugin/release/notes.py` (the first-sentence fix) and `template/sdlc.yaml` (a commented `lessons:` block), so every claim of the entry still holds; each below was re-read at 5542406.

- **The routes are the project's.** `template/bands.yaml:32-40` lists `pull_request`, `runbook:quarantine-flaky-test` and `runbook:revert-pr` as `preapproved` and `runbook:rollback-deploy` as `go`; a route not listed is never taken (`plugin/detect/routes.py:149-151`); tier 2 may take `pull_request` only (`routes.py:52`, `TIER_ROUTES`; `validate_proposal`, 236-268). The diagnosis proposes and the dispatcher judges against the default branch's `bands.yaml` and `sdlc.yaml` (`detect/cli.py:968-987` `_judge`, `approved_files`).
- **The built-in runbooks.** `quarantine-flaky-test` is Python-only and adds `--deselect <node id>` to pytest's `addopts`, never editing a test path; `revert-pr` runs `git revert`, `-m 1` for a merge commit; both open a PR labelled `incident` that the framework never merges (`plugin/detect/runbooks.py:1-23`, `routes.py:37-49`, `runbooks.py:302`, `:329`).
- **A project runbook** is a `command` under `sdlc.yaml: maintain.runbooks` (`template/sdlc.yaml:69-88`; the list is empty, the `rollback-deploy` example commented, `authorization: go`, so no rollback exists until the owner adds one). It runs without a shell (`project_runbook`, `runbooks.py:729-782`), its exit code and output tail in `evidence/runbook-<name>.json` (`record_path` and `write_record`, 828-839). The proposal's `args` are recorded beside it and not passed to the command (`runbooks.py:823-824`; `project_runbook` takes no args, 729-731).
- **Authorization.** `routes.py:141-182` `authorization`: the bands' value, a stricter `go` in `sdlc.yaml` wins, and on a declared production a runbook whose name contains "rollback" with a real `rehearsed_at` date becomes `preapproved`, the record naming decision 26 and the date (172-181). A forced finding (a rehearsal) always waits for Go (`apply_forced`, 185-196). Nothing reads a release: the pre-approval is the date alone. The gate's own route check resolves the route with the same two functions (`plugin/gate/checks.py:1493-1527`, `check_route`).
- **Where a route is dispatched.** In the detect job, `detect/cli.py finish` (1049-1136) runs after the model's session: it refuses a session that wrote owner-only fields (1056-1063) or changed the detection record (1065-1093, against the Detect step's digest), dispatches with the approved `sdlc.yaml`, runs gate (f) and opens the intent PR; `sdlc-detect.yml:181-195` is that step, its comment saying a project runbook's secrets belong in its `env:` (183). A `go` route writes a `go-requested` record (`_act`, 818-831), and gate (f)'s `check_route` parks it with "Go requested".
- **The Go.** `sdlc-runbook.yml` runs on `pull_request: labeled` with `sdlc:go` on a head `sdlc/<id>/a` only (line 47), installs the project's toolchain from the default branch's `commands.setup` (91-97), and runs `detect/cli.py go` (99-107). `cmd_go` (1151-1214) reads the approved `sdlc.yaml` first, takes the label's actor through `_human_label_actor` (1139-1148: the last `labeled` event's actor, refused when it is a `[bot]` or the automation identity, `gate/policy.py:43-61`), runs the runbook only when its record says `go-requested` (once), writes `status.yaml: runbook_authorized_by` (1203), removes the label (1211) and re-runs gate (f). A failed setup step parks the incident (`cmd_park`, 1269-1341; workflow 113-122). No function or workflow at 5542406 names the owner: `git grep -n "is_owner_actor\|repository_owner\|GITHUB_REPOSITORY_OWNER" 5542406 -- plugin template` finds nothing.
- **A route changed by comment.** `plugin/commands/sdlc-fix.md:119-124`, phase (f): a comment that names another route "rewrites `evidence/proposal.json` and re-runs" `detect/cli.py dispatch --commit` inside the session; "a comment is not a Go". `cmd_dispatch` (990-1029) has no snapshot or owner-fields check of its own. The fix step's environment carries `GITHUB_TOKEN` and the model credentials and no runbook secret (`template/.github/workflows/sdlc-fix.yml:151-163`), and `session_env` passes that environment to the session with no credential removed (`plugin/ci/run_phase.py:1310-1320`); whether the sandbox lets a dispatch inside the session reach GitHub is not verified.
- **The release record** exists since 0.3.1: `released_at`, `released_sha` and `released_pr` in `status.yaml` on `refs/sdlc/released/<id>` (`plugin/release/cli.py:35-55`, `:106`; `plugin/state/status.py:90-98`), read with a fail-closed `remote_record` (`release/cli.py:248-262`). The detection record carries `breach_start` and the latest point, and the commits between them (`detect/cli.py:586-606`).
- **Live.** A Go ran a project runbook once on the owner's label (2026-09-25, the entry). No pre-approved runbook has run on a real 3σ: change 0013's tier-3 diagnosis chose `pull_request`, "No runbook ran, so check 19 (a rollback live) is not proven" (`docs/progress/2026-10-14-item-11.md:6`; NOTES §42).

## The proposal

Decision 14's split and decision 26's pre-approved rehearsed rollback stay, as R39 (T20) amends decision 26. Four additions, the owner's:

1. **The Go is the owner's own.** `sdlc:go` counts only from the owner's account, "as T18's approval and T21's label" in the owner's words; R13 (T21) does not itself narrow the release label, which the code at 5542406 checks for a person only (`plugin/release/approval.py:5-11`), and R17 names T18's merge step and T24's Go as its function's callers. A Go by any other account runs nothing and is left where it is, as a `[bot]`'s is today. The check is R17's `is_owner_actor` (the repository owner by default, `sdlc.yaml: owner` on an organization repository, one function, fail closed), which R17 builds and "T18 and T24 call … when they arrive". This closes T1's open item for that label; the approvals T1 adds stay T1's (R28)[^r17].
2. **A rollback needs a release in the window.** The dispatcher pre-approves a rehearsed rollback only when the breach window, from `breach_start` to the latest point in `evidence/detection.json`, holds a release, read from T21's record on `refs/sdlc/released/<id>`. With no release in the window the rollback waits for the owner's Go, as every other running-system route does. A release record that cannot be read fails closed to Go (the entry's Open).
3. **A route changed by comment is dispatched by the runner.** In a fix round at (f) the session writes `proposal.json` only; the runner's own step dispatches the route after the session, as `detect/cli.py finish` does in the detect job, with the project runbook's secrets in that step's environment and none in the model's, and the record written by the deterministic step. A comment stays never a Go.
4. **The runbook PRs get T14's review pass** (R36), already decided; nothing is built here for it.

The row as completed by the owner, unchanged by this proposal: the routes are `bands.yaml`'s per-project list and tier 2 proposes `pull_request` only; the diagnosis proposes and the dispatcher judges against the default branch's `bands.yaml` and `sdlc.yaml`; `quarantine-flaky-test` is Python-only and `revert-pr` uses `-m 1` for a merge, both opening an `incident` PR the framework never merges; a project runbook's command runs in the finish step with the repository's secrets; no rollback exists until the owner adds one; a `go` in `sdlc.yaml` wins over the bands; a forced finding always waits for Go; the Go runs once, removes the label and records `runbook_authorized_by`; a failed setup step parks; a failed runbook stays parked.

Not proposed here: a notification when Go is requested (decisions 11 and 20; R20's "No ping" restates decision 26 as T20 and T24 bound it); the quarantine runbook for Node and Rust (R33's open items); the Go's line in the approvals list (R11). The act's row "`sdlc:go` when Go is requested, your account only" is added to R19's table by this entry, as the accepted R19 leaves "the owner-only Go and the release window (T24)" to arrive with it; the digest's refresh after a Go or a park joins with this entry, as the accepted R20 says ("Runbook, from `detect/cli.py go` and `park` … with T24").

## How it is judged

The measures below are this proposal's own, not the entry's.

- **The Go.** A `sdlc:go` applied by any account other than the owner's runs nothing, leaves the label and says why; the owner's runs the runbook once. Unit tests on `_human_label_actor` with R17's function; a live check needs a second account on the sample (to verify whether one is available).
- **The window.** On a declared production with a rehearsed, fresh rollback: a breach with a release in the window dispatches the rollback pre-approved, one without parks with "Go requested", and an unreadable release ref parks with "Go requested". Unit tests now; the live proof is check 19, which stays pending until a real 3σ meets a release in its window.
- **The comment.** In an (f) round started by a comment that names a runbook, the hook log shows no `detect/cli.py dispatch` call from the session, the route's commit is the runner's step's, and the runbook's record and PR exist after the session.

The failure is a runbook run inside a model session, a Go counted from another account, or a rollback pre-approved with no release in the window.

## What to settle before building

| Question | Recommended |
|---|---|
| How the owner's account is known to the runbook workflow (shared with T1, T17 and T23) | **Settled** by R17, accepted by the owner on 2026-10-14 as recommended (PR #208; `docs/ROADMAP.md` R17 row): the repository owner by default, `sdlc.yaml: owner` on an organization repository, `is_owner_actor`, fail closed. Mine: the workflow's `if:` gains the coarse check (`github.event.sender.login`) and the Python step keeps the exact one, as R17 does for its dispatcher |
| Whether R12's `sdlc:c-approved` and `sdlc:d-approved` narrow to the owner too (the question decision 27 left to T17, T18 and T24) | **Settled** by R17's accepted point 3: it "settles the question R12 deferred to T17, T18 and T24, which T1 and T23 share, the same way for each", so these labels count from the owner's account through `is_owner_actor`, fail closed. No part builds it yet: R17's Order names T18's merge step and T24's Go as the function's callers, R12 keeps "any actor but the workflow token", and R12 is built with R13 before R17, so the function does not exist at R12's build. Mine: this entry's owner-only Go part, after R17, also calls `is_owner_actor` where the runner reads the (c) and (d) labels' actor for R12's line; recording it on R17's build instead would be a line in R17's Order, the owner's to choose |
| Who adds the act's row (R19) and the digest's refresh (R20) if a part of this entry is built before R19 or R20 | Mine: whichever is built second adds them, as R19 provides for R17's row ("whichever of R17 and R19 is built second adds the row") |
| The window check's edges: a release on the day the breach started, several releases in the window, a record that cannot be read | The last is the entry's own: fail closed to Go. Mine for the first two: the window is counted in the detection's own days, inclusive of `breach_start`'s day and the latest point's (R16 moves those days to the owner's offset when built), so a release on the breach's first day counts; several releases still pre-approve, every one named in the record; the releases are found by listing `refs/sdlc/released/*` and reading each `released_at`, through `release/cli.py`'s reader |
| Where the condition sits | Mine: beside `apply_forced` in `routes.py`, called by `_judge` and by `check_route`, so the dispatcher, the Go and gate (f) never disagree |
| Where the fix round's dispatch step sits in `sdlc-fix.yml`, and how a rejected proposal reaches the owner | Mine: a step after "Run the fix round", only on an incident head `sdlc/<id>/a`, running the same deterministic tail as `finish` (the owner-fields and detection-snapshot checks, the dispatch with the approved `sdlc.yaml`, gate (f), the PR refresh), the runbook secrets in that step's `env:` alone; a refused proposal parks through gate (f)'s route check with its reason in "What I need from you", as `cmd_dispatch`'s own comment intends (`detect/cli.py:1002`). The snapshot to compare against is the head's record before the session, to settle in the design |
| Whether a rollback the diagnosis proposes names the release to roll back (the `sha` or the change id), as `revert-pr` names its commit | Mine: yes, `args` carrying the change id and `released_sha`, which the dispatcher checks is one of the window's releases (a name outside the window is a Go). Passing them to the project's command is a new contract (today `args` are recorded, not passed, `runbooks.py:823-824`), for example as environment variables; to settle in the design |
| One decision file for decision 26 or two | Mine: R39 (T20) and this proposal both amend decision 26; if both are accepted, one decision file states both conditions, written before whichever intent comes first |

## Considered and not chosen

- A, the row's text completed only.
- C, the quarantine runbook for Node and Rust projects (jest's ignore patterns, cargo's `#[ignore]`), as T8 follows the project's languages: no project needs it; recorded under T8's open items (R33).

## Decisions it touches

26 is amended: a rehearsed rollback on a declared production is pre-approved only with a release in the breach window, beside R39's fresh rehearsal; otherwise it waits for the owner's Go. The decision file comes before the intent, in a documentation PR, as decisions 27 to 29 were; this proposal reserves no number. 14 is kept (the split by blast radius); its Go is narrowed to the owner's account, closing T1's open item for that label (the owner's note); recording that narrowing in the same decision file is this proposal's recommendation, not the entry's. 11 and 20 are kept (a Go waits as a park, nothing notifies). 22, as R17 amends it, is kept: the (f) round is the same round, and a comment is never a Go. 24 is kept (the Go removes its label as the un-park labels do, `template/.github/workflows/sdlc-runbook.yml:14`). 5 is kept (the automation identity, still refused). 27 is read: the owner-account question it left is answered by R17's accepted point 3, for the Go and for the (c) and (d) labels alike.

## Order

In the confirmed order's group "the rest in any order" (the record, section 8). It changes `plugin/` and `template/`, so it ships as a plugin version with tests and reaches a project through `/sdlc-init`'s workflow copies. The parts it takes:

| Part | Where | When |
|---|---|---|
| The owner-only Go | `detect/cli.py` `_human_label_actor` calling `is_owner_actor`; the coarse check in `sdlc-runbook.yml`'s `if:`; the (c) and (d) labels' actor through the same function (mine, settle table) | After R17, which builds the function (R17 is built after R13) |
| The release in the window | `detect/routes.py` beside `apply_forced`, read by `_judge` and `gate/checks.py` `check_route`; the release reader of `release/cli.py` | After the decision file amending 26; buildable on today's release record (since 0.3.1); with or after R39, whose condition sits beside it |
| The fix round's dispatch in a runner step | `plugin/commands/sdlc-fix.md` §3 (f), `sdlc-fix.yml`, `detect/cli.py` | Now; needs neither part above |
| The pass on the runbook PRs | R36 (T14) | With R36 |
| The Go's line in the approvals list | R11 | With R11; until then `runbook_authorized_by` |
| The act's row "`sdlc:go` when Go is requested, your account only" and the release window's wording | R19's table in `plugin/pr/` | With the owner-only Go and the window part, once R19's table exists (R19 is after R14) |
| The digest refreshed after a Go or a park | a "refresh wanted" output from `detect/cli.py go` and `park`, and R20's separate dispatch job in `sdlc-runbook.yml` (`:107`, `:122`) | With R20's part 2 |
| Check 19 live | the sample | After the window part, on the first real 3σ with a release in its window |

T31's DORA (R26) reads a release in the breach window the same way, and keeps the record of a rollback's release in its own change (R26's settle table); this proposal adds no such record. T29 (R44) keeps the workflow token in the session, recorded as accepted, so point 3 is what keeps a runbook from running in a session that holds it. Neither is a dependency. T4's names (R45) come last.

[^entry]: `docs/reviews/2026-09-28-playbook-vs-framework/target-design.md`, T24 (the owner's note, "Today", "Direction discussed", "Open"); the crosswalk row maintain-act, its `weigh` and `decision` fields.
[^decision-27]: `docs/decisions/27.md`, "Why": "Whether the actor must be the owner's own account is decided with the study's entries T17, T18 and T24, not here."
[^playbook]: `docs/reference/ai-native-sdlc-playbook.pdf` p.40, p.43-45, p.49-50; the figure's exchange as quoted in `docs/decisions/26.md` and `template/.github/workflows/sdlc-runbook.yml:1-3`.
[^r17]: `docs/proposals/claude-comment-fix-round.md`, "The proposal" point 3, "What to settle" row 2 and "Order" row 3; `target-design.md` T1, the annotation at maintain-act of 2026-10-07 ("closed for that label, open for the approvals T1 adds").
