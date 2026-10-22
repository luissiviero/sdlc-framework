# Ruleset 1's bypass mode for the owner: "For pull requests only" versus "Exempt" (2026-10-22)

The owner asked for a live test of both bypass modes of the Repository admin role in this repository's ruleset 24077592 ("main — owner merges only (decision 4)") before choosing one and updating `/sdlc-init` step 6 and NOTES §17. This file is the test record; the verified facts go into a note once both modes are tested.

## Why the choice is open
- NOTES §17 (`docs/notes/17.md`) chose Exempt for the mobile merge and named one cost: no bypass audit entry. It says the rules "still run for every other actor, the workflow token included".
- NOTES §14 (`docs/notes/14.md`) records that the GitHub MCP tools of a cloud session act as the owner's login. Under Exempt the rules do not run for that login, so they do not run for such a session either. No framework hook refuses a GitHub MCP write to `main` or a `git push` to `main`.
- Whether an API merge by a bypass actor in "For pull requests only" mode goes through is not verified: choice 249, point 4 (`docs/progress/2026-10-20-choice-249-r22-questions.md`) leaves the same question open for the merge App.
- Whether a bypass in "For pull requests only" mode writes an audit entry is not verified (`docs/progress/2026-10-20-r22-gate-e-approving-review-1.0.18.md`, the table's row on it).

## The tests
Each test runs once per mode. "Session" means this cloud session, acting through its GitHub MCP tools or its git proxy. A test whose write is accepted lands on `main` and is undone by a pull request.

| # | Who | Act | Question |
|---|-----|-----|----------|
| S1 | session | Create a new file on `main` through the GitHub MCP tool (`create_or_update_file`, branch `main`) | Does the ruleset refuse a direct commit by a session acting as the owner? |
| S2 | session | `git push origin HEAD:main` of a one-file commit, through the session's git proxy | Does the proxy or the ruleset refuse a direct push from the session? |
| S3 | session | Merge an open pull request through the GitHub MCP tool (`merge_pull_request`) | Does the ruleset refuse a merge by a session acting as the owner? |
| O1 | owner | In the GitHub mobile app, open a pull request, read the label, tap Merge | Does a tap merge? (NOTES §17: not tested in this mode) |
| O2 | owner | If O1 does not merge: merge from the web UI | Which control does the web UI show? |
| O3 | owner | Settings → Rules → Insights: find the entries of the merges above | Is each merge logged, and is it marked as a bypass? |

Not tested, in either mode: a force-push to `main` and the deletion of `main`. If accepted, either would rewrite or remove the default branch. Both fall under the same rules as S1 and S2, so S1 and S2 stand for them.

## Results: "For pull requests only" (set by the owner on 2026-10-22)

| # | Result | Evidence |
|---|--------|----------|
| S1 | Refused by the ruleset | `PUT …/contents/docs/reviews/ruleset-probe-s1.md` answered `409 Repository rule violations found`: "Cannot update this protected ref. Changes must be made through a pull request." |
| S2 | Refused by the ruleset; the session's git proxy let the push through to GitHub | `git push origin HEAD:main` of `95abcf6` on top of `1f58af2`: `! [remote rejected] HEAD -> main (push declined due to repository rule violations)`, with the same two messages as S1. A first attempt on a stale `main` (`0a0554d`) failed with `rejected (fetch first)` and an `HTTP 403` from the transfer, so it is not counted. |
| S3 | not run yet | |
| O1 | not run yet | |
| O2 | not run yet | |
| O3 | not run yet | |

## Results: "Exempt"

Not run yet.
