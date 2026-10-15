---
type: Proposal
title: An optional preview environment before the approval, and a rollback rehearsed there on a schedule
description: Two additions, both optional and off by default — deploy.preview_command deploys each (e) head to a preview environment after the review pass, in a job of its own with a "preview" GitHub environment's secrets, a read-only token and no Claude session, its result a line of the banner the owner reads before approving and a red preview failing gate (e) as a red target does; and a weekly workflow runs the rollback runbook's rehearse_command there with no agent and records pass or fail on a ref, so that decision 26's pre-approval needs the owner's rehearsed_at and a passing rehearsal within N days.
status: proposed
roadmap: R39
sources:
  - id: study-entry
    resource: docs/reviews/2026-09-28-playbook-vs-framework/target-design.md
    title: "T20, confirmed at the close of the study on 2026-10-09; from the crosswalk row deploy-envs (better: the playbook; decision: blend, option B), 2026-10-07; the record's section 7 (first bullet) and section 8 part 1 (close table row: D26; optional and off by default) and part 2 (the order: the rest in any order)"
  - id: crosswalk
    resource: docs/reviews/2026-09-28-playbook-vs-framework/crosswalk.json
    title: "Row deploy-envs whole; the decision fields of maintain-act (T24), deploy-approve (T18), test-loop (T10), deploy-ci (T19), x-sandbox (T29) and maintain-detect (T22)"
  - id: playbook
    resource: docs/reference/ai-native-sdlc-playbook.pdf
    title: "p.39: rehearse the rollback paths before the agent ever needs them, gates defined per environment; p.40 steps 3 to 6: no production credentials by default, deploy, status and rollback as MCP tools, autonomy tiered by environment, rollback the most rehearsed path, exercised regularly in staging; p.43: a rollback path for CI/CD which the highest tier invokes; p.44: the 3σ routes include runbook:rollback-deploy; p.45: with a deployment in the window, the agent triggers the existing rollback pipeline"
  - id: decision-26
    resource: docs/decisions/26.md
    title: "Decision 26: a rehearsed rollback pre-approved on a declared production by the owner's rehearsed_at (the decision this amends: a passing rehearsal within N days added)"
  - id: decision-13
    resource: docs/decisions/13.md
    title: "Decision 13: merge is the whole gate until a real production, then a release label (kept: the preview is a step before the gate, not a tier of the release)"
  - id: decision-19
    resource: docs/decisions/19.md
    title: "Decision 19: per-project phase adapters (kept: the one deploy adapter stays)"
  - id: decision-29
    resource: docs/decisions/29.md
    title: "Decision 29: in CI a red target starts the next fix round by itself, one counter, a park at the cap (the round a red preview starts)"
  - id: decision-14
    resource: docs/decisions/14.md
    title: "Decision 14: the split by blast radius; a rollback waits for Go (kept)"
  - id: code
    resource: plugin/detect/routes.py
    title: "rehearsed, authorization and apply_forced; with template/sdlc.yaml (deploy, maintain.runbooks), template/bands.yaml, template/.github/workflows/sdlc-release.yml, sdlc-deploy.yml, sdlc-fix.yml, sdlc-scan.yml, plugin/release/cli.py, plugin/detect/cli.py _judge, docs/OPERATING_MODEL.md §9, docs/BUILD_GUIDE.md step 31, docs/notes/11.md §11a; read at main 5542406, plugin 1.0.1"
generated: { by: sdlc-framework-session/ccr-01de3f80-ilnomi, at: 2026-10-15T20:00:00Z }
---

# An optional preview environment before the approval, and a rollback rehearsed there on a schedule

**Status: proposed (roadmap R39), from study entry T20, confirmed by the owner on 2026-10-09, option B of the crosswalk row deploy-envs (the letters are the row's own, not deploy-approve's or deploy-ci's).** Nothing is built. It amends decision 26: the pre-approved rollback also needs a passing rehearsal within N days; the decision file comes before the intent, in a documentation PR of its own; this proposal writes no decision file and reserves no number. Both its parts are optional and off by default. The preview's result is a line of the banner the owner reads before approving at gate (e) (T18, R22); the banner block is R24's (T9), or R28's part 1 if that comes first. A red preview starts decision 29's round (R10) and reaches R18's triage (T19) at the cap; R41 (T24) adds a second condition to the same pre-approval, a release in the breach window.

## The problem

Two gaps against the article's environments and rollback, as the crosswalk row deploy-envs reads them[^crosswalk]:

- **Nothing sits between the pull request and production.** `deploy.production` is the one tier switch (decision 13), and there is one deploy adapter (decision 19), which runs only after the merge (decision 13, `sdlc-release.yml:51-53`). The owner approves code that has never been deployed anywhere; the article's development tier, where "the agent deploys freely", has no counterpart.
- **The rollback's pre-approval rests on a date that never expires.** On a declared production a rollback runbook is pre-approved once the owner sets `rehearsed_at` after a staging rehearsal of the owner's own (decision 26)[^decision-26]. Nothing re-checks it: a rollback rehearsed once, months ago, against a system that has changed since, still runs at 3σ with nobody in the path. The article asks for the opposite: the rollback "exercised regularly in staging" and "proven in advance".

## What the article says

The CI/CD play's aim: "rehearse the rollback paths before the agent ever needs them", with deployment "inside gates the organization defines per environment" (p.39). Its steps (p.40)[^playbook]: agent jobs "hold no production credentials by default" (step 3); "Deploy, status, and rollback become tools, scoped per environment, so the agent's deployment powers are an allowlist rather than a shell script with credentials" (step 4); "Tier the autonomy by environment. In development, the agent deploys freely. In production, the agent prepares the release and the release manager authorizes it ... Staging sits somewhere in the middle" (step 5); "Rollback should be the most rehearsed path in the pipeline, a single command that the agent can run and that is exercised regularly in staging. The closing the loop play ... calls this rollback when a control band is breached, so it has to be proven in advance" (step 6). The maintenance play lists "a rollback path for CI/CD (which the highest autonomy tier invokes)" as a prerequisite (p.43), names `runbook:rollback-deploy` among the 3σ routes (p.44), and triggers "the existing rollback pipeline" when the breach comes "with a deployment in the window" (p.45).

## What the framework does today

Read at `main` 5542406, plugin 1.0.1. The entry's "Today" was read at 619f01a (0.3.5). Over `619f01a..5542406`, `git diff --stat` on `sdlc-release.yml`, `sdlc-deploy.yml`, `sdlc-fix.yml`, `sdlc-scan.yml`, `sdlc-detect.yml`, `plugin/release/`, `plugin/detect/routes.py`, `plugin/detect/cli.py`, `template/bands.yaml`, `template/sdlc.yaml`, `docs/OPERATING_MODEL.md` and `plugin/commands/sdlc-deploy.md` touches only `OPERATING_MODEL.md` (a §8 sentence on the shell guard, a §9 sentence on lessons), `sdlc-deploy.md` (§0b: the lesson's frontmatter, the `lessons/index.py build` step and gate (e)'s `lesson_and_eval` check), `release/notes.py` and `template/sdlc.yaml` (a `lessons` block); none changes deployment or rollback, so the entry's "Today" still holds (verified below by file and line).

- **One deploy adapter, after the merge.** `template/sdlc.yaml:44-59`: `deploy.action`, `deploy.production` (the one switch, line 53) and `deploy.command` (empty by default, line 59). `sdlc-release.yml` runs on the merge (`closed`) or the release label (`labeled`, lines 51-53); the release job holds `contents: read` (65-66), runs `deploy.command` on the runner with no Claude session (126-134), and a GitHub environment on it is the owner's to add (82-85, commented out); only the record job holds `contents: write` and writes `refs/sdlc/released/<id>` (136-147). An action `none` or an empty command releases nothing (`plugin/release/cli.py:638-643`).
- **No preview anywhere.** `git grep -i "preview\|rehearse_command" 5542406 -- plugin template` finds nothing. The (e) workflow is one job, `deploy`, whose review pass and phase (e) are two steps "in that order" (`sdlc-deploy.yml:48-51`, 107, 143), under workflow-level write scopes (32-37); its header says "The job holds no deploy secret and no production credential" (11-12). A fix round at (e) runs in `sdlc-fix.yml` (`--phase fix`, lines 128, 163).
- **Why a pull_request trigger cannot carry the preview.** `pull_request` `synchronize` events caused by the workflow token "create workflow runs in an approval-required state" (`docs/notes/11.md:60-63`), and every automated transition dispatches the next workflow explicitly (decision 5).
- **The rollback route.** `template/bands.yaml:39-40` lists `runbook:rollback-deploy` with `authorization: go`. No runbook of that name exists until the owner adds one with a `command` under `maintain.runbooks` (the template's example is commented out, `template/sdlc.yaml:84-88`); until then the route is unsupported (`routes.py:167-171`).
- **Decision 26 as coded.** `authorization` pre-approves a `go` route whose name matches `rollback` on a declared production when `rehearsed` returns a date (`routes.py:172-181`); `rehearsed` only parses the date (`routes.py:126-138`), with no age check: the date never expires (verified). A forced finding (the framework's own loop rehearsal, a dispatch of `sdlc-detect.yml`) never pre-approves (`apply_forced`, `routes.py:185-196`, called from `detect/cli.py` `_judge`, 968-987).
- **The weekly schedule this proposal copies.** `sdlc-scan.yml:37-38`, `cron: "23 6 * * 1"`.
- **The MCP tools are deferred.** `docs/OPERATING_MODEL.md:141` (§9) records the interface and says "not built": the plugin ships no runtime dependency and no project has named a real deployment yet; build guide step 31 (`docs/BUILD_GUIDE.md:703`) carries it. No Dn decides the deferral.
- **The sample** (`sdlc-sample-python` at f88b262, `sdlc.yaml:24-26`, 50-53): `deploy.action: none`, `deploy.production: true`, a `rollback-deploy` runbook that prints a line, `rehearsed_at: 2026-09-25`.

## The proposal

The owner's choice, condensed. The one deploy adapter, `deploy.command` run on the runner after the merge with no Claude session, and `deploy.production` as the production switch stay (decisions 13 and 19). Added, both optional and off by default:

1. **A preview environment, the article's development tier (p.40 step 5).** `deploy.preview_command`, empty means off, deploys the build PR's head to a preview environment at each (e) head, after the REVIEW.md pass. It runs on the runner in a job of its own, with the secrets of a GitHub environment named `preview`, a read-only token and no Claude session, as the release job does; no production secret is in reach. The automation's pushes start no workflow run by themselves (their `pull_request` runs wait for approval), so it is a job of the (e) workflows (`sdlc-deploy.yml`, and `sdlc-fix.yml` at (e)), run after the phase job or in a workflow they dispatch explicitly, never a `pull_request` trigger.
2. **Its result is a banner line.** Passed, or the failing step and its exit code, in the banner the owner reads before approving (T18, R22). The banner is one generated block that R24 (T9) builds, or R28's part 1 if that comes first; this proposal adds its preview line.
3. **A red preview fails gate (e) as a red target does:** decision 29's round starts by itself (R10, T10), and at the iteration cap the change parks with T19's triage of the preview log (R18), stored where that triage reads a parked gate's logs ("What to settle"). Until R22's merge step requires the check, nothing blocks the merge mechanically, as nothing blocks it on a red target today (ruleset 1 requires no check): the red `sdlc/preview` check, the PR body and the round tell the owner, whose merge is the gate (decision 13).
4. **The rollback rehearsed there, regularly (p.40 step 6).** A project rollback runbook gains `rehearse_command`, the same rollback aimed at the preview environment. A scheduled workflow, weekly like the scan, runs it on the runner with the preview environment's secrets and no agent; a separate job with `contents: write` records pass or fail (date, commit, exit code) on a ref, as the release record does on `refs/sdlc/released/<id>`; no file of the default branch changes.
5. **Decision 26's pre-approval then needs both:** the owner's `rehearsed_at`, which stays the owner's one-time consent, and a passing rehearsal within N days. A failed or stale rehearsal puts the rollback back to Go and shows in the daily digest (R20 places it under "Worth knowing"); nothing notifies the owner (decisions 11 and 20). With R41 (T24), the breach window must also hold a release. What a runbook with no `rehearse_command` gets is open ("What to settle").
6. **The cost, accepted.** The preview credentials reach code the model wrote before the owner approves it, after the review pass; they are scoped to the preview environment, as the article's "in development, the agent deploys freely" allows.
7. **The MCP tools stay deferred** (build guide step 31, `OPERATING_MODEL.md` §9): no Claude session deploys in this design and no agent holds a deploy credential, stricter than the article's allowlist.

The row is corrected as the owner wrote: both sides gain the rehearsed rollback; no rollback exists until the owner adds one with a command under `maintain.runbooks`, then it waits for Go, and it is pre-approved under decision 26 once the owner sets `rehearsed_at` on a declared production, a date that never expires; the MCP deferral rests on step 31 and §9, not on a Dn.

## How it is judged

These measures are this proposal's, from the entry's aims. On the first three build PRs at (e) of a project with `deploy.preview_command` set: each banner carries a preview line naming the head it deployed; a red preview starts a round with no act of the owner's; before R22's merge step requires the check, a red preview informs only (the check, the PR body and the round), and the owner's merge decides, as on a red target today; once it requires the check, no build PR merges on a red preview through the owner's approval (a direct merge by the owner stays possible, since R22's ruleset 2 requires only `sdlc/review`); no phase or fix job's environment holds a `preview` secret (read from the workflow files and the run logs). Over the first four weeks with a `rehearse_command`: four rehearsal records on the ref; a rollback resolved at 3σ shows in its `source` the rehearsal it relied on; a failed or stale rehearsal turns the route back to Go and appears in the digest the next morning. A project that sets neither key sees no change in its (e) runs and its release; whether a declared-production rollback with `rehearsed_at` and no `rehearse_command` keeps its decision-26 pre-approval is open ("What to settle", the row on a project with no preview environment): under this proposal's recommendation there it waits for Go, as the sample's would.

## What to settle before building

| Question | Recommended |
|---|---|
| N, the days a passing rehearsal keeps the rollback pre-approved, and the schedule | The schedule is settled: weekly, like the scan (the owner's note). N is open; (this proposal's) 15 days by default, an `sdlc.yaml` key the owner may lower, so one missed weekly run, with the next one up to a day late, does not drop the pre-approval while a failed one does at once (at 14 days the next run would have to be exactly on time) |
| The ref that holds the rehearsal record, and how `routes.py` reads it on the runner at 3σ | (This proposal's) `refs/sdlc/rehearsed/<runbook>`, in the record shape R40 (T22) settles for the detection record (the entry's open item shared with T22); the detect job fetches the ref and passes the last record to `authorization`; a ref that cannot be read counts as no rehearsal, so the route waits for Go (fail closed) |
| Where the preview job sits, how its result reaches the banner, and whether R22's merge step requires it green | (This proposal's) a job after the phase job in `sdlc-deploy.yml` and in `sdlc-fix.yml` at (e), with `environment: preview` and `contents: read` only; a second job that runs nothing of the project's posts an `sdlc/preview` check on the head and refreshes the banner line, as the release splits its run and record jobs; R22's merge step requires `sdlc/preview` green on the head it merges whenever `deploy.preview_command` is set (R22 left this question here) |
| How a red preview fails gate (e) when gate (e)'s record is written before it | (This proposal's) the record is not re-written: the red `sdlc/preview` check stops R22's merge step (row above), and the result job dispatches decision 29's round with the preview's failing step as its constraint, counted on the one counter; running the preview before the gate would split today's single (e) job. Before R22's merge step exists, the check blocks nothing (ruleset 1 requires no check), so until then a red preview fails gate (e) through the round and the PR body only, as a red target does today. At the cap the result job parks the change and stores the preview's failing step, its exit code and, under the masking row below, the log tail as the parked gate's preview log under `evidence/`, where R18's triage reads a parked gate's logs; R18's list of its sources gains it with T20 |
| What a preview that could not start (the environment down, a missing secret) does | (This proposal's) decision 29's rule for an infrastructure failure: one automatic re-run, not counted, then a park with the reason; a missing secret or an unset `preview` environment is a setup gap the owner fixes, so it parks at once. R18 already lists "T20's preview that could not start" as a source of its "Failed runs" line |
| Whether the preview is torn down after the merge or the close, and one preview shared by several changes | (This proposal's) an optional `deploy.preview_teardown_command`, off by default, run at the merge or the close; one concurrency group for every preview and rehearsal job of a project, so one deploy runs at a time and the banner names the commit it deployed |
| What a project with no preview environment rehearses against | (This proposal's) a `rehearse_command` aimed at whatever non-production environment the project has, holding the `preview` environment's secrets; with no `rehearse_command`, the freshness condition cannot be met and the rollback waits for Go on a declared production, since the owner's "still comfortable" at maintain-act rests on this amendment (T24). The alternative, decision 26 as today with the date alone (the answer the entry's open item names), keeps the sample's pre-approval unchanged and makes item 5 and the amendment apply only to a runbook that declares a `rehearse_command`; the decision file chooses, and the upgrade note names the sample |
| What part of a preview log reaches the round's model session | (This proposal's) the failing step and exit code always; the log tail only after a check that GitHub masks the `preview` environment's secrets in it (to verify), as R18 reads a failed release through the API source only because a release log can print the project's secrets |
| That a GitHub environment's secrets reach only the job that names it, and that the preview job's checkout of the head cannot read the release job's secrets | To verify on the sample before the design, recorded in `docs/notes/` |
| Whether the (d) verifier of R14 may call the preview environment's URL once it exists (R14's "Considered and not chosen" sets aside a session driving the live product through a project MCP server and says "Its place is T20, where a preview environment is a URL the verifier can call", `docs/proposals/drive-target-and-proof.md:90`) | (This proposal's, a question added beyond the entry) not chosen in this design, so R14's pointer ends here: the owner's T20 note keeps every Claude session out of the preview job ("no Claude session"), and the preview deploys at (e) heads after the review pass, so no preview of the change exists when the (d) verifier runs. If the owner wants a verifier that reads a deployed URL, it becomes a ROADMAP candidate of its own |
| The key, workflow and ref names | Judged with R45 (T4); `preview_command`, `rehearse_command` and the ref are placeholders |

## Considered and not chosen

- A, the crosswalk text corrected and nothing added.
- C, B plus deploy, status and rollback as MCP tools now: no step has an agent deploy or roll back, so the tools would add powers nothing uses, for fidelity alone.
- A standing PR that proposes the new `rehearsed_at` after each passing rehearsal (the previous session's form of B): an automated edit of `sdlc.yaml`, a guardrail file (decision 6), and the owner's merge every time just to keep the rollback pre-approved. The ref record replaces it.
- The preview as a `pull_request` `synchronize` trigger: the workflow token's pushes create runs that wait for approval, so it would never run by itself on the automation's heads.

## Decisions it touches

26 is amended: the pre-approval of a rehearsed rollback on a declared production needs a passing rehearsal within N days besides the owner's `rehearsed_at`; a failed or stale rehearsal returns the route to Go. Whether that holds for a runbook with no `rehearse_command` is the open row of "What to settle" on a project with no preview environment, for the decision file to choose. A decision file comes before the intent, in a documentation PR of its own, never with the intent; this proposal writes no decision file and reserves no number. R41 (T24) amends the same decision with a second condition (a release in the breach window); (this proposal's suggestion) the two amendments read best in one documentation PR if both are accepted together. 13 and 19 are kept: the preview is a step before the gate, not a tier of the release, and the one adapter stays. 14 is kept (the rollback waits for Go unless pre-approved). 11 and 20 are kept (a park at the cap, nothing notifies). 29 is kept (the round a red preview starts, one counter). 5 and 6 are kept (explicit dispatch; no automated edit of `sdlc.yaml`).

## Order

In the record's confirmed order T20 is among "the rest in any order" (section 8). Its dependencies: the decision file amending 26 first; the preview's round after R10 (decision 29's round, which a red preview starts); the banner line with whichever of R24 (T9) and R28's part 1 builds the banner block; the merge step's requirement with or after R22 (T18); the triage at the cap and the "Failed runs" source with R18 (T19); the digest line with R20 (T28); the ref's shape with R40 (T22); the second condition on the same pre-approval with R41 (T24). R14 points here for a verifier that calls a preview URL (its row in "What to settle", not chosen here); nothing here waits on it. It changes `template/` and `plugin/`, so it ships as a plugin version with tests and reaches a project through `/sdlc-init`. The parts it takes:

| Part | Where | When |
|---|---|---|
| The decision file amending 26 | `docs/decisions/` | First, in a documentation PR of its own (with R41's amendment if accepted together) |
| `rehearse_command`, the weekly rehearsal workflow and its record job, the ref | `template/sdlc.yaml`, `template/.github/workflows/`, `plugin/` | After the decision file; independent of the preview job; the ref's shape with R40 |
| `authorization` reading the last rehearsal (freshness, failure, fail closed) | `plugin/detect/routes.py`, `plugin/detect/cli.py` | With the rehearsal workflow |
| `deploy.preview_command`, the preview job and its result job, the `sdlc/preview` check | `template/sdlc.yaml`, `sdlc-deploy.yml`, `sdlc-fix.yml`, `plugin/`, `/sdlc-init` (the `preview` environment) | After R10; after a live check of environment secrets on the sample |
| The banner's preview line | R24 (T9), or R28's part 1 | With whichever builds the banner block first; until then the check and the PR body carry it |
| The merge step's green-preview requirement | R22's merge step | With whichever of R22 and this proposal's preview job is built second (R22's order row); until then the red check blocks nothing and the round and the PR body carry it |
| The triage of a red preview at the cap (the preview log under `evidence/`), and the "Failed runs" source | R18 | With R18 |
| The failed or stale rehearsal in the digest | R20 ("Worth knowing") | With R20 |

[^crosswalk]: `docs/reviews/2026-09-28-playbook-vs-framework/crosswalk.json`, row deploy-envs, and `target-design.md` T20 ("Today", the owner's note).
[^decision-26]: `docs/decisions/26.md`.
[^playbook]: `docs/reference/ai-native-sdlc-playbook.pdf` p.39-40, p.43-45.
