# Progress — the pipeline sprint, part 2: R47 (decision 31) as plugin **1.0.7**, and the owner's choices 219 to 221 (2026-10-18)

This session ran on branch `ccr-b3531dc9-oioi5k`, from the sprint prompt (R47, R48, R49 in ROADMAP's Order). The previous record (R17 as 1.0.5, R46 as 1.0.6, choices 214 to 218) is now `docs/progress/2026-10-18-r17-r46-and-choices-214-218.md`, unchanged. The session's own file is `docs/handoffs/sessions/2026-10-18-ccr-b3531dc9-oioi5k.md`.

## Summary
- **R47 as plugin 1.0.7** (PR #230): when an automated publication leaves a pull request waiting for the owner (`sdlc:needs-human` or `sdlc:<phase>-ready`), `pr/cli.py upsert --request-review` requests the owner's review on it. `pr/review_request.py sync_owner_review` decides; `pr/github.py request_reviewers` and `remove_reviewers` act.
- **Who is requested:** R17's `owner_login`, judged by `is_owner_actor` (fail closed). On a runner it reads only the default branch's `sdlc.yaml` (`run_phase.owner_config`), so a head cannot choose who is notified. A pull request the owner authored is skipped, because GitHub refuses a review request to a PR's author.
- **Callers:** `ci/run_phase.py` (`ensure_pr`, `park_and_publish`), `detect/cli.py` (the three `upsert --phase f` calls) and `scan/route.py` (the weekly scan's incident intents). The model's own in-session upserts pass no flag.
- **Review:** one builder, one independent reviewer. Round 1 found nothing blocking and five should-fix findings: the scan's upsert, the park bullet "nobody was notified", stale notification text, the `gh` field set widened for every lookup, and a sync error that could change upsert's outcome. All were fixed with tests. The re-review found nothing blocking or should-fix; its line-wrap nit was fixed.

## The owner's decisions (2026-10-18)
219. **A pending request is removed and requested again at every new wait** (the session's recommendation), so a wait after an `@claude` comment or an approval label, which do not clear a request, still sends one push.
220. **A publication that leaves the PR not waiting withdraws the owner's pending request** (`sdlc:fixing`, a gate's `continue`, any other label), so GitHub's "Review requests" list is the owner's waiting queue.
221. **The scope is every PR published by `pr/cli.py upsert` from the automation**: the runner's phase PRs and parks, and the incident intents of the detect workflow (and, from the review, the weekly scan's).

## Proposed edits for the owner
| File | Line | What is there now | What it must become |
|---|---|---|---|
| [`sdlc.yaml`](https://github.com/luissiviero/sdlc-framework/blob/main/sdlc.yaml#L50) | 50 | `# you" in the PR); nobody is notified. The owner accepts a risk-list hit per change by` | `# you" in the PR) and requests the owner's review on the PR, the only notification (decision 31). The owner accepts a risk-list hit per change by` (rewrap the comment as needed; the same text `template/sdlc.yaml:107-108` carries since 1.0.7) |
| [`REVIEW.md`](https://github.com/luissiviero/sdlc-framework/blob/main/REVIEW.md#L26) | after 26 | carried from the previous record (choice 208), not yet applied | as there |
| sample [`CLAUDE.md`](https://github.com/luissiviero/sdlc-sample-python/blob/main/CLAUDE.md#L45) | 45 | `- When a run cannot finish, park: write "what I need from you", never notify.` | `- When a run cannot finish, park: write "what I need from you"; the runner requests the owner's review on the waiting PR, and nothing else notifies.` (with the sample's upgrade, choice 207) |

## Left
- **Not verified:** whether GitHub's push reaches the owner for a review request on a draft pull request (the build PR waits as a draft at (c)), and whether a remove-then-request pair sends a fresh push. The first live wait shows both.
- **R47's known limits:** no request on a pull request the owner authored; none on runbook PRs (`detect/runbooks.py`) or dismissal PRs (`detect/cli.py cmd_dismiss`), which do not go through upsert; none from the model's in-session upserts.
- **This repository's own pin is 0.3.6**, so R47 does not run here until the pin moves.

## Checks (this repository)
On #230's final head, after `python -m pip install -e ".[dev]"`, chained with `set -o pipefail`: the four commands of `HANDOFF.md`'s standing precondition 1. Their output is in the PR.
