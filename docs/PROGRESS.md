# Progress — the pipeline sprint, part 2: R47 (decision 31) as plugin **1.0.7**, R48 (decision 32) as plugin **1.0.8**, R49 (decision 33) as plugin **1.0.9**, and the owner's choices 219 to 227 (2026-10-18)

This session ran on branch `ccr-b3531dc9-oioi5k`, from the sprint prompt (R47, R48, R49 in ROADMAP's Order). The previous record (R17 as 1.0.5, R46 as 1.0.6, choices 214 to 218) is now `docs/progress/2026-10-18-r17-r46-and-choices-214-218.md`, unchanged. The session's own file is `docs/handoffs/sessions/2026-10-18-ccr-b3531dc9-oioi5k.md`.

## Summary
- **R47 as plugin 1.0.7** (PR #230): when an automated publication leaves a pull request waiting for the owner (`sdlc:needs-human` or `sdlc:<phase>-ready`), `pr/cli.py upsert --request-review` requests the owner's review on it. `pr/review_request.py sync_owner_review` decides; `pr/github.py request_reviewers` and `remove_reviewers` act.
- **Who is requested:** R17's `owner_login`, judged by `is_owner_actor` (fail closed). On a runner it reads only the default branch's `sdlc.yaml` (`run_phase.owner_config`), so a head cannot choose who is notified. A pull request the owner authored is skipped, because GitHub refuses a review request to a PR's author.
- **Callers:** `ci/run_phase.py` (`ensure_pr`, `park_and_publish`), `detect/cli.py` (the three `upsert --phase f` calls) and `scan/route.py` (the weekly scan's incident intents). The model's own in-session upserts pass no flag.
- **Review:** one builder, one independent reviewer. Round 1 found nothing blocking and five should-fix findings: the scan's upsert, the park bullet "nobody was notified", stale notification text, the `gh` field set widened for every lookup, and a sync error that could change upsert's outcome. All were fixed with tests. The re-review found nothing blocking or should-fix; its line-wrap nit was fixed. PR #230 merged as `176fc37`, with `v1.0.7` on it (verified, `git ls-remote --tags origin`).
- **R48 as plugin 1.0.8** (PR #233), with NOTES §45 gaps 1 and 5 (choice 205):
  - `/sdlc-init` proposes `review: deferred` (`INIT_REVIEW_MODE`), and the template carries it. An unset `review:` key still reads as `parked` (the session's call, so a project without the key does not switch silently).
  - The build run and every fix round get `gate.build_max_turns` (400) and `gate.build_max_wall_clock_minutes` (180), falling back to the larger of the general setting and that default. The other runs keep 200 and 120.
  - `start-run` records `run: build`, so the gate's wall clock follows the run. `sdlc-build.yml` and `sdlc-fix.yml` go to 260 minutes and export `SDLC_JOB_TIMEOUT_MINUTES`; a job too short for the build caps keeps the general caps and says why. A re-run of `/sdlc-init` never lowers a project's build caps.
  - The template's per-change budget is 150 USD. Each session gets what the change has left, and a change with nothing left parks before its session.
  - Gap 1: an `escalate` the panel decided as anything but `continue` parks (`check_panel`, `ledger.decides_continue`), and the owner's overturn of it counts as the owner's continue for the same reasons (`settled_by_owner`).
- **R48's review:** round 1 found nothing blocking and four should-fix findings: a re-init lowering caps, old workflow copies killing a long build, the budget passed whole to each session, and no way out of a panel park. All were fixed with tests. The re-review found nothing blocking or should-fix; six of its optional nits were applied.
- **`docs/nits.md`** (the owner's request): a plain list of cosmetic nits left for later, not tracked work. PR #233 merged as `55938ad`, with `v1.0.8` on it (verified, `git ls-remote --tags origin`).
- **R49 as plugin 1.0.9** (PR #235):
  - With the repository variable `SDLC_APP_ID` and the secret `SDLC_APP_PRIVATE_KEY`, eight workflows (design, build, test, deploy, fix, detect, runbook, scan) mint a GitHub App token (`actions/create-github-app-token@v2`), narrowed to each job's `permissions:`, and push and open pull requests with it, so the project's CI runs on the automation's heads by itself. Without the variable, everything runs on the workflow token as before.
  - The token lasts an hour, so after 50 minutes the runner and the CLIs fall back to the workflow token (`plugin/ci/app_token.py`).
  - The key is only in the mint step. Every model session runs with the workflow token in its environment and in the git credential of `.git/config`. The App credential comes back after the session only when the config carries nothing credential-relevant the session could have set. The project's setup command gets no token.
  - `[bot]`-sender guards on the label triggers of test, deploy, fix and runbook; `label_applied_by_a_human` rejects any `[bot]`; detection leaves out CI runs on `sdlc/**` heads, so the fix loop's red runs never file incidents.
  - `/sdlc-init` step 6 carries the one-time App setup.
- **R49's review:** round 1 found one blocking finding (the session's own pushes, through the App credential checkout persists, would fail after an hour) and two should-fix findings (a tag push by the session as the App; the setup command inheriting the tokens). Round 2 found one should-fix finding (the App credential restored into a config the session controlled). Round 3 found a proxy hidden in the per-worktree config; round 4 found session-written code and planted hooks reaching the persisted credential, so the root cause was removed: no credential is written to `.git/config`, and each git network call takes it through its environment. Round 5 found that this reopened the config redirect for the runner's own pushes, now checked before the App's token goes out, and the `/proc` exposure (choice 227). All were fixed with tests, except the one left to R44.

## The owner's decisions (2026-10-18)
219. **A pending request is removed and requested again at every new wait** (the session's recommendation), so a wait after an `@claude` comment or an approval label, which do not clear a request, still sends one push.
220. **A publication that leaves the PR not waiting withdraws the owner's pending request** (`sdlc:fixing`, a gate's `continue`, any other label), so GitHub's "Review requests" list is the owner's waiting queue.
221. **The scope is every PR published by `pr/cli.py upsert` from the automation**: the runner's phase PRs and parks, and the incident intents of the detect workflow (and, from the review, the weekly scan's).
222. **The higher caps go to the build run and every fix round only: 400 turns and 180 minutes** (the session's recommendation). Design, test and deploy keep 200 and 120; the build and fix jobs go to 260 minutes.
223. **The template's per-change budget is 150 USD** (the session's recommendation; about 1.8 times the costliest change so far, 0002 at about 85 USD).
224. **A project without the App falls back to the workflow token** (the session's recommendation): `SDLC_APP_ID` unset means everything runs as before.
225. **R49's live proof comes with the sample's upgrade to 1.0.9** (the session's recommendation), not a probe before the build.
226. **After 50 minutes the App token gives way to the workflow token** (the session's recommendation): a long run still publishes; its final push waits for the owner's approval as before.
227. **The App token's `/proc` exposure is left to R44** (the session's recommendation): an unsandboxed process the runner starts (the project's setup or targets) can read the runner's initial environment, the App token included, as it already could the workflow token and the model key; R44 closes it for all three together.

## Proposed edits for the owner
*[2026-10-18: the three rows below are applied by the owner: `sdlc.yaml` in PR #231 (`f4241f6`), `REVIEW.md` in PR #232 (`d6ffafe`), the sample's `CLAUDE.md` in sample PR #66 (`5ea91cc`), each verified by its diff; the `sdlc.yaml:50` line was left unwrapped, recorded in `docs/nits.md`.]*

| File | Line | What is there now | What it must become |
|---|---|---|---|
| [`sdlc.yaml`](https://github.com/luissiviero/sdlc-framework/blob/main/sdlc.yaml#L50) | 50 | `# you" in the PR); nobody is notified. The owner accepts a risk-list hit per change by` | `# you" in the PR) and requests the owner's review on the PR, the only notification (decision 31). The owner accepts a risk-list hit per change by` (rewrap the comment as needed; the same text `template/sdlc.yaml:107-108` carries since 1.0.7) |
| [`REVIEW.md`](https://github.com/luissiviero/sdlc-framework/blob/main/REVIEW.md#L26) | after 26 | carried from the previous record (choice 208), not yet applied | as there |
| sample [`CLAUDE.md`](https://github.com/luissiviero/sdlc-sample-python/blob/main/CLAUDE.md#L45) | 45 | `- When a run cannot finish, park: write "what I need from you", never notify.` | `- When a run cannot finish, park: write "what I need from you"; the runner requests the owner's review on the waiting PR, and nothing else notifies.` (with the sample's upgrade, choice 207) |

R48's row *[2026-10-18: applied by the owner in PR #234 (`0991f43`), verified by its diff]*:

| File | Line | What is there now | What it must become |
|---|---|---|---|
| [`sdlc.yaml`](https://github.com/luissiviero/sdlc-framework/blob/main/sdlc.yaml#L62) | 62 | `  max_turns: 400                 # turns per phase session; unset = the runner's 200` | `  max_turns: 400                 # turns per session of every run but build/fix; unset = 200` (the build run and fix rounds take `build_max_turns`, unset = the larger of this and 400; decision 32) |

R49's rows (open):

| File | Line | What is there now | What it must become |
|---|---|---|---|
| [`CLAUDE.md`](https://github.com/luissiviero/sdlc-framework/blob/main/CLAUDE.md#L33) | 33 | `- Events caused by the CI workflow token do not start workflow runs (except workflow_dispatch / repository_dispatch): automated phase transitions dispatch the next workflow explicitly.` | `- Events caused by the CI workflow token do not start workflow runs (except workflow_dispatch / repository_dispatch): automated phase transitions dispatch the next workflow explicitly. With \`vars.SDLC_APP_ID\` the automation pushes as the project's GitHub App, whose events do start runs (decision 33); the explicit dispatch stays for the fallback.` |
| [`sdlc.yaml`](https://github.com/luissiviero/sdlc-framework/blob/main/sdlc.yaml#L68) | 68-69 | `# github-actions[bot] (plugin/gate/policy.py). Override only if your CI commits under another` / `# name:` | `# github-actions[bot] (plugin/gate/policy.py). Any <app>[bot] account, the project's GitHub` / `# App included (decision 33), counts as the automation whatever this lists. Override only if` / `# your CI commits under another name:` (the text `template/sdlc.yaml:130-133` carries since 1.0.9) |

## Left
- **Not verified:** whether GitHub's push reaches the owner for a review request on a draft pull request (the build PR waits as a draft at (c)), and whether a remove-then-request pair sends a fresh push. The first live wait shows both.
- **R47's known limits:** no request on a pull request the owner authored; none on runbook PRs (`detect/runbooks.py`) or dismissal PRs (`detect/cli.py cmd_dismiss`), which do not go through upsert; none from the model's in-session upserts.
- **This repository's own pin is 0.3.6**, so R47 does not run here until the pin moves.
- **R48's known limits** (the re-review's nits, left as they are):
  - an overturned panel `continue` on an `escalate` goes back to the panel when the same verdict returns (as before 1.0.8);
  - a dry run on a change with no budget left parks and publishes, as the guardrail and preflight parks already do;
  - gates (d) and (e) do not re-check a (c) panel `park` recorded before 1.0.8.
- **A project that pins 1.0.8 keeps the general caps** until it replaces `sdlc-build.yml` and `sdlc-fix.yml` with the 1.0.8 copies (`/sdlc-init` says so). The sample's upgrade (choice 207) includes them.
- **R49 not verified live** (choice 225): that a sandboxed session cannot read the runner's process through `/proc` (its own process namespace); that an App push starts the sample's CI with no approval; that a `permission-*`-narrowed installation token still reads metadata; that the App's PRs, labels and review requests behave as the workflow token's. The owner's App setup (`sdlc-init.md` step 6) and the sample's upgrade to 1.0.9 come first.
- **R49's known limits:**
  - runs longer than 50 minutes publish with the workflow token, so CI on their final head waits for the owner's approval (choice 226);
  - an unsandboxed process the runner starts can read the App token from the runner's initial environment through `/proc` (choice 227, left to R44);
  - a project's runbook commands inherit the App token (the owner's own code);
  - a same-repo PR head can rewrite its own workflow file, mint step included; only a person with write access can push one (the App has no Workflows permission), the class of choice 95, and a note for R22, whose App key gains merge rights;
  - the evals workflow now runs, with the model credentials, on the automation's pushes that touch `evals/**`, where it used to wait at `action_required`;
  - a runner whose global git config sets a proxy or turns off TLS verification keeps every run on the workflow token (fails safe; GitHub-hosted runners set neither);
  - detection's cache schema moved to 3, so the first detect run after the upgrade refetches at most 1000 runs of its window.

## Checks (this repository)
On #230's, #233's and #235's final heads, after `python -m pip install -e ".[dev]"`, chained with `set -o pipefail`: the four commands of `HANDOFF.md`'s standing precondition 1. Their output is in the PR.
