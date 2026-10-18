# Progress — the pipeline sprint, part 2: R47 (decision 31) as plugin **1.0.7**, R48 (decision 32) as plugin **1.0.8**, and the owner's choices 219 to 223 (2026-10-18)

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
- **`docs/nits.md`** (the owner's request): a plain list of cosmetic nits left for later, not tracked work.

## The owner's decisions (2026-10-18)
219. **A pending request is removed and requested again at every new wait** (the session's recommendation), so a wait after an `@claude` comment or an approval label, which do not clear a request, still sends one push.
220. **A publication that leaves the PR not waiting withdraws the owner's pending request** (`sdlc:fixing`, a gate's `continue`, any other label), so GitHub's "Review requests" list is the owner's waiting queue.
221. **The scope is every PR published by `pr/cli.py upsert` from the automation**: the runner's phase PRs and parks, and the incident intents of the detect workflow (and, from the review, the weekly scan's).
222. **The higher caps go to the build run and every fix round only: 400 turns and 180 minutes** (the session's recommendation). Design, test and deploy keep 200 and 120; the build and fix jobs go to 260 minutes.
223. **The template's per-change budget is 150 USD** (the session's recommendation; about 1.8 times the costliest change so far, 0002 at about 85 USD).

## Proposed edits for the owner
*[2026-10-18: the three rows below are applied by the owner: `sdlc.yaml` in PR #231 (`f4241f6`), `REVIEW.md` in PR #232 (`d6ffafe`), the sample's `CLAUDE.md` in sample PR #66 (`5ea91cc`), each verified by its diff; the `sdlc.yaml:50` line was left unwrapped, recorded in `docs/nits.md`.]*

| File | Line | What is there now | What it must become |
|---|---|---|---|
| [`sdlc.yaml`](https://github.com/luissiviero/sdlc-framework/blob/main/sdlc.yaml#L50) | 50 | `# you" in the PR); nobody is notified. The owner accepts a risk-list hit per change by` | `# you" in the PR) and requests the owner's review on the PR, the only notification (decision 31). The owner accepts a risk-list hit per change by` (rewrap the comment as needed; the same text `template/sdlc.yaml:107-108` carries since 1.0.7) |
| [`REVIEW.md`](https://github.com/luissiviero/sdlc-framework/blob/main/REVIEW.md#L26) | after 26 | carried from the previous record (choice 208), not yet applied | as there |
| sample [`CLAUDE.md`](https://github.com/luissiviero/sdlc-sample-python/blob/main/CLAUDE.md#L45) | 45 | `- When a run cannot finish, park: write "what I need from you", never notify.` | `- When a run cannot finish, park: write "what I need from you"; the runner requests the owner's review on the waiting PR, and nothing else notifies.` (with the sample's upgrade, choice 207) |

R48's row (open):

| File | Line | What is there now | What it must become |
|---|---|---|---|
| [`sdlc.yaml`](https://github.com/luissiviero/sdlc-framework/blob/main/sdlc.yaml#L62) | 62 | `  max_turns: 400                 # turns per phase session; unset = the runner's 200` | `  max_turns: 400                 # turns per session of every run but build/fix; unset = 200` (the build run and fix rounds take `build_max_turns`, unset = the larger of this and 400; decision 32) |

## Left
- **Not verified:** whether GitHub's push reaches the owner for a review request on a draft pull request (the build PR waits as a draft at (c)), and whether a remove-then-request pair sends a fresh push. The first live wait shows both.
- **R47's known limits:** no request on a pull request the owner authored; none on runbook PRs (`detect/runbooks.py`) or dismissal PRs (`detect/cli.py cmd_dismiss`), which do not go through upsert; none from the model's in-session upserts.
- **This repository's own pin is 0.3.6**, so R47 does not run here until the pin moves.
- **R48's known limits** (the re-review's nits, left as they are):
  - an overturned panel `continue` on an `escalate` goes back to the panel when the same verdict returns (as before 1.0.8);
  - a dry run on a change with no budget left parks and publishes, as the guardrail and preflight parks already do;
  - gates (d) and (e) do not re-check a (c) panel `park` recorded before 1.0.8.
- **A project that pins 1.0.8 keeps the general caps** until it replaces `sdlc-build.yml` and `sdlc-fix.yml` with the 1.0.8 copies (`/sdlc-init` says so). The sample's upgrade (choice 207) includes them.

## Checks (this repository)
On #230's and #233's final heads, after `python -m pip install -e ".[dev]"`, chained with `set -o pipefail`: the four commands of `HANDOFF.md`'s standing precondition 1. Their output is in the PR.
