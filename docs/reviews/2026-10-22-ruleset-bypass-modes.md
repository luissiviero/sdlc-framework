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
| S3 | **Merged.** The bypass in this mode covers an API merge by a session acting as the owner | PR #314: `mergeable_state` read `blocked` through the same tools, then `merge_pull_request` answered `merged: true`, merge commit `54a05f6` on `main`. The PR's author also reads as the owner's login, though the session opened it. |
| O1 | **Merged from the phone.** The app shows "Unable to merge — Cannot merge at this time" under "All checks have passed", and still offers Merge; a tap opens the commit-message sheet, and its MERGE button merged | PR #315: the owner's screenshot of the sheet (14:09 local time), then `merged: true`, `merged_by: luissiviero`, `merged_at` 17:09:14 UTC. This answers NOTES §17's open point: the label discouraged the tap on 2026-09-27, but the tap merges in this mode too. |
| O2 | Not needed: O1 merged | |
| O3 | **Logged, as `fail` and `bypass`.** Every entry's actor is the owner's login, the session's included, so the log cannot tell the session from the owner | The owner's read of `GET /repos/luissiviero/sdlc-framework/rulesets/rule-suites` from a codespace (`gh auth login --web`; the codespace's own token got `403 Resource not accessible by integration`; the Rule Insights page is not in this repository's settings menu), times UTC: S2 17:01:35 `fail`, S1 17:01:44 `fail`, #314 (the session's merge) 17:03:34 `bypass`, #315 (the owner's tap) 17:09:14 `bypass`. The owner's other merges in this mode read `bypass` too (#307 15:05:53, #312 16:49:36, #313 17:21:47). |

## Results: "Exempt" (set by the owner on 2026-10-22)

| # | Result | Evidence |
|---|--------|----------|
| S1 | **Accepted.** The commit landed on `main` | `PUT …/contents/docs/reviews/ruleset-probe-s1.md` created commit `7c33f02` on `main`, its author the owner's login. The file is removed by the pull request that records this row. |
| S2 | **Accepted.** The push landed on `main` | `git push origin HEAD:main`: `2a782f1..906317a  HEAD -> main`. The file is removed by the same pull request. |
| S3 | **Merged** | PR #316: `merge_pull_request` answered `merged: true`, merge commit `1cdb45f` on `main`; it also removed the two probe files. |
| O1 | **Merged from the phone, with no warning.** The app shows "Ready to merge" under "All checks have passed"; a tap opens the same commit-message sheet, and its MERGE button merged | PR #318: `mergeable_state` read `clean` through the session's tools before the tap (#314 read `blocked` in the other mode), the owner's screenshot of the sheet, then the merge `45931cd` on `main`. |
| O2 | Not needed: O1 merged | |
| O3 | **Logged, as `pass`.** No entry says `bypass`, and every actor is the owner's login | The same read: S2 17:33:26 `pass` (the commit's author is `Claude`, the pusher the owner's login), S1 17:33:32 `pass`, #316 (the session's merge) 17:34:16 `pass`. The owner's later merges (#317 17:48:38, #319 18:30:02) and two direct web-editor commits to `main` (`2cf98e3` "Update CLAUDE.md" 17:49:57, `396e4b4` 18:43:34) read `pass` too. The mode changed between 17:21:47 and 17:33:26. |

## The owner's choice
On 2026-10-22, after the two runs, the owner chose **"For pull requests only"** for the admin role (choice 251). That mode refuses a direct commit or push to `main` by anything acting as the owner's login, and it costs the warning label and a confirmation sheet on the phone, plus a pull request for a guardrail edit made in the web editor. Neither mode stops a session acting as the owner from merging a pull request (S3). The facts are NOTES §57.
