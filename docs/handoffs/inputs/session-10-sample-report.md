# Session 10 — read by the owner's session (sample: `luissiviero/sdlc-sample-python`)

Read at 2026-09-28T06:33Z. Read only: no file edited, no label, no dispatch, no comment.
`main` = `52cacff` (merge of PR #44). Tools: GitHub MCP (`actions_list`, `get_file_contents`,
`pull_request_read`, `search_pull_requests`, `list_pull_requests`, `list_branches`).

## 1. The `CI` point count

`actions_list` / `list_workflow_runs`, `ci.yml`, `per_page=100`: `total_count` 42, all on one
page, oldest run 36163416115 at 2026-09-25T16:51Z, so nothing older than 2026-09-25 exists.
Counted = `actor.login` ≠ `github-actions[bot]`, `status` completed, any conclusion.

| UTC day    | counted | excluded (bot) | failures among counted | note |
|------------|--------:|---------------:|-----------------------:|------|
| 2026-09-25 | 15 | 9 | 0 | bot runs: 36175325756 and 36183718786…36185378596 (runs #6, #11–#18, branches `sdlc/0006/a`, `sdlc/0006/dismiss`, `sdlc/0005/b`, `sdlc/0007/a`), all `failure` |
| 2026-09-26 | 14 | 0 | 1 | the failure is 36257154359 (`pull_request`, `luissiviero-patch-9`, created 16:54:51Z, attempt 2) — as NOTES §17 says |
| 2026-09-27 | 3 | 0 | 0 | includes the one `schedule` run (below) |
| 2026-09-28 | 1 | 0 | 0 | 36386521836, `pull_request` on `luissiviero-patch-11` (PR #45), 06:27Z, success |

Total 42 = 33 counted + 9 excluded. Runs on `main` since 2026-09-25 by anyone: all by
`luissiviero`; the nine bot runs are all `pull_request` runs on `sdlc/*` heads.

### Scheduled runs (`event: schedule`, cron `29 1 * * *` since PR #41, merged 2026-09-26T16:27Z)

| run | actor / triggering_actor | created_at | started after 01:29 UTC | conclusion |
|-----|--------------------------|------------|-------------------------|------------|
| 36300826732 | `luissiviero` / `luissiviero` | 2026-09-27T06:41:13Z (`run_started_at` same) | 5 h 12 min | success (head `main` 486b8f2) |

Only one scheduled run exists. 2026-09-26: none possible (cron merged after 01:29). 2026-09-28:
none as of the read (06:33Z); yesterday's started 06:41Z, so a delayed one may still come.
The actor is the person, so a scheduled run keeps the point (ROADMAP row 3 needs no fix on
this evidence).

### Points

- Points as of the read: **4** (2026-09-25, -26, -27, -28). Consistent with "two points on
  2026-09-26".
- If every later day gives one: 5th = 09-29 … **16th = 2026-10-10**, matching the plan
  (first judging run 2026-10-11).

## 2. The pins and the copies

| item | on `main` (52cacff) | verdict |
|------|---------------------|---------|
| `sdlc.yaml` `plugin:` block, line 77 | `version: 0.2.25` (`name: sdlc`, `marketplace: sdlc-framework`, `claude_code: "2.1.278"`) | as expected before the tag; **PR #45** (open, `luissiviero-patch-11` → `main`, by luissiviero, 2026-09-28T06:26:57Z, 1 file, +1/−1) changes exactly this line to `0.2.26`. CI check `test` success; no reviews; `mergeable_state: blocked`. |
| `.github/workflows/sdlc-*.yml` (12 files) | blob SHAs identical to those at `ed78a20` (head of `chore/framework-0.2.23`, PR #38, merged 2026-09-26T04:46Z) | still the 0.2.23 copies session 9 byte-verified; nothing changed them since |
| `.github/scripts/sdlc_pin.py` | SHA `55c72a57…` on `main` and at `ed78a20` | unchanged, 0.2.23 copy |
| `.github/workflows/ci.yml` | differs from `ed78a20` (`d436868` → `9fef9a5`) | expected: the cron (PR #41) and the pytest/ruff pins (PR #43); not an SDLC copy |

Env check on `sdlc-design.yml` ("Run phase (b)" step): `ANTHROPIC_API_KEY`,
`CLAUDE_CODE_OAUTH_TOKEN`, `GITHUB_TOKEN`, `CHANGE_ID`, `HEAD_REF`, `REPO`, `DEFAULT_BRANCH`.
No `SDLC_DEFAULT_BRANCH` on the phase step (it appears only on the pin step), consistent
with the 0.2.23 template as the prompt describes it.

## 3. The ruleset and the rehearsal

1. **Active rules on `main`: not verified.** The `rules/branches/main` read (unauthenticated
   `curl`) was denied by this session's permissions, and no GitHub MCP tool reads rulesets or
   the classic protection. `list_branches` reports `main` as `protected: true`.
2. **Open PRs with label `incident`: none.** `search_pull_requests label:incident` → 7, all
   closed (#25, #26, #27, #28, #30, #33, #35; #35 = 0007, closed 2026-09-25T20:25Z).
   `list_pull_requests state=open` → only #45, no labels.
3. **`sdlc/0005/*` branches exist:** `sdlc/0005/a` (128d5fd8), `sdlc/0005/b` (37f1d159).
   (Also present: `sdlc/0000/a`, `0001/a,b,c`, `0002/a,b,c`, `0003/a`, `0004/a`, `0004/dismiss`,
   `0006/a`, `0006/dismiss`, `0007/a`.)

## Not verified

- Ruleset rules on `main` (reason above).
- Whether `v0.2.26` exists on the framework repository: out of this session's GitHub scope.
- The 0.2.25 template's `env:` itself (framework repository, out of scope); the copies were
  checked by blob SHA against the sample's own 0.2.23 upgrade commit instead.
- Why PR #45 is `blocked` (protection settings need an admin read).
