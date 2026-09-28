# Prompt for a session that has `luissiviero/sdlc-sample-python` in scope (session 10's reads)

Session 10 (2026-09-27, group A of the readiness review, plugin 0.2.26) ran with this
repository alone in its GitHub scope: every call on the sample was denied (precondition 1 of
`HANDOFF.md`). Group A needed nothing from the sample, so the build went ahead; the reads
below are what the session could not do. Paste this file whole into a Claude Code session
started with **both** repositories selected, and paste its report back into the framework
repository's `docs/PROGRESS.md` (session 10, "Read by the owner's session") or hand it to
session 11, which starts with the same preconditions.

Rules for that session: read only — no file of the sample is edited, no label applied, no
workflow dispatched, no comment left (choice 86: a person's comment becomes the dismissal
reason at a close). Report every number with the call that produced it. Write "not
verified" with the reason for anything the tools did not answer.

## 1. The `CI` point count (HANDOFF precondition 6; choice 92; D12)

Call `actions_list` (method `list_workflow_runs`) on the sample's `ci.yml`, paging until the
runs are older than 2026-09-25, and report:

1. Every UTC day since 2026-09-25 with at least one **counted** run: a run whose
   `actor.login` is not `github-actions[bot]` (D12), completed, whatever its conclusion. One
   point per day. Give the table: day · counted runs · excluded runs (by the bot) · failures
   among the counted runs. The failure of 2026-09-26 (run 36257154359, `pull_request`,
   `luissiviero-patch-9`, 16:54 UTC) must be among them (NOTES §17).
2. The **actor** and `created_at` of every run whose `event` is `schedule` (the cron
   `29 1 * * *` since the sample's PR #41): a person's login keeps the point; a
   `github-actions[bot]` actor drops it (ROADMAP row 3; a fix with a test in session 14 if
   so). Also how late after 01:29 UTC each one started (NOTES §17: GitHub's delay on a
   scheduled run exceeded four hours once).
3. The count of points as of the read, and the date on which the sixteenth point falls if
   every later day gives one (two points existed on 2026-09-26; the plan says the sixteenth
   is 2026-10-10 and the first judging run 2026-10-11).

## 2. The pins and the copies (HANDOFF precondition 3)

1. `sdlc.yaml` on the sample's `main`, the `plugin:` block (line 77 at the last read): the
   pinned version. Expected `0.2.25` until session 10's tag exists; **after `v0.2.26` exists
   on the framework repository** the owner changes it to `0.2.26` (a guardrail edit, the
   owner's: link; row; what is there; what it must become — the row is in PROGRESS session
   10's guardrail table). Report what it says now.
2. `.github/workflows/sdlc-*.yml` and `.github/scripts/sdlc_pin.py` on the sample's `main`:
   confirm they are still the **0.2.23** copies (session 9 byte-verified them against the
   tags; nothing should have changed them since). One way: `get_file_contents` on
   `.github/workflows/sdlc-design.yml` and compare its phase step's `env:` with the 0.2.25
   template (`SDLC_DEFAULT_BRANCH` is on every phase step since 0.2.25 and absent in 0.2.23).
   Session 14 opens the upgrade PR; nothing to do here.

## 3. The ruleset and the rehearsal (the state session 11 starts from)

1. `GET /repos/luissiviero/sdlc-sample-python/rules/branches/main` (through `gh api` or an
   unauthenticated read, NOTES §17): the active rules. Expected: none from a ruleset (the
   sample's `main` has a classic protection rule only; the same ruleset as this repository's,
   with the Repository admin as **Exempt** bypass actor, is the owner's optional act).
2. The open pull requests carrying the `incident` label: expected none (the rehearsal 0005
   is closed; choice 69, one open incident per metric). If one is open, report its number,
   title and head branch and stop — do not close it.
3. The branches `sdlc/0005/*` still exist (they mark the rehearsal abandoned: `open_incidents`
   and, since 0.2.26, the digest's counters read the marker from them; the review record says
   never to prune them). List them.

## 4. The report

At most one page: the three tables (points per day, scheduled runs, pins and copies), the
ruleset's rules, the incident state, and the "not verified" list. No recommendation; the
sessions decide.
