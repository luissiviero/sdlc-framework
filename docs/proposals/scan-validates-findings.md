---
type: Proposal
title: The weekly scan validates its findings, applies its patch and reaches the digest
description: Each Important finding of the weekly security review carries the exploit path traced from an entry point (or why it is not reachable) and a confidence of high or medium, low staying a nit, both riding into the intent's Evidence section and the Security & policy brief of R28 (T1); the build run of a bounded scan change starts from evidence/suggested-patch.diff after the failing test; a "Scan" line reaches the digest and the scan's red runs join "Failed runs"; decision 16's pattern without Claude Security stays.
status: proposed
roadmap: R43
sources:
  - id: study-entry
    resource: docs/reviews/2026-09-28-playbook-vs-framework/target-design.md
    title: "T26, confirmed at the close of the study on 2026-10-09; from the crosswalk row maintain-scan (better: the playbook; decision: blend, option B), 2026-10-07"
  - id: record
    resource: docs/reviews/2026-09-28-playbook-vs-framework.md
    title: "Section 7, first bullet (the close) and the owner's decisions, row maintain-scan; section 8 part 1 (the close table, row T26: amends none); section 8 part 2 (the confirmed order, T26 among 'the rest in any order')"
  - id: crosswalk
    resource: docs/reviews/2026-09-28-playbook-vs-framework/crosswalk.json
    title: "Row maintain-scan (whole); the decision fields of maintain-triage (T23), maintain-learn (T25), test-bugfix (T11), deploy-ci (T19), maintain-detect (T22), maintain-diagnose, x-queue (T28), x-measure (T31) and x-roles (T1)"
  - id: playbook
    resource: docs/reference/ai-native-sdlc-playbook.pdf
    title: "p.46: scans on a schedule, no human in the invocation path, the same gates; Claude Security validates each finding and attaches a confidence rating; p.47 steps 3-7: weekly, triage with the confidence rating, dismiss with a reason, a bounded finding's patch through the PR gate, a wider one as intent.md, an eval for the class; p.48: every finding has a validation result and a confidence rating, the deterministic checks stay in CI, the leading and lagging indicators"
  - id: decision-16
    resource: docs/decisions/16.md
    title: "Decision 16: recurring security scans, a weekly read-only claude -p, the deterministic scanners in CI (kept)"
  - id: decision-20
    resource: docs/decisions/20.md
    title: "Decision 20: a review queue and a daily digest, nothing pushes to the owner (kept: the scan's lines go to the digest)"
  - id: decision-25
    resource: docs/decisions/25.md
    title: "Decision 25: gate (f) is per-finding triage (kept: the owner triages each scan PR, now with the rating)"
  - id: decision-17
    resource: docs/decisions/17.md
    title: "Decision 17: when to start evals and parallel worktrees (untouched: the class eval at /sdlc-deploy step 0b)"
  - id: artcraft
    resource: docs/reviews/2026-10-13-artcraft-vs-framework.md
    title: "Row A2 (model judgments labelled where they sit beside measured lines; folded into T27, T28, T30 and R10, not T26), for this writer's recommendation in 'What to settle'"
  - id: live
    resource: docs/notes/14.md
    title: "The first live scan on the sample, 2026-09-25 (118 s, $0.55); with docs/notes/39.md:56 (the scan's PRs #56 and #57 of 2026-10-12) and docs/handoffs/sessions/2026-10-13-session-26.md:31 (#55 to #57 at gate (f))"
  - id: code
    resource: plugin/scan/
    title: "prompt.py build_prompt and EXCLUDED_DIRS, route.py load_findings, select, intent_text, finding_record and file_one, cli.py cmd_review and cmd_route; with template/.github/workflows/sdlc-scan.yml, plugin/review/findings.py normalise, plugin/commands/sdlc-build.md step 3, plugin/commands/sdlc-deploy.md step 0b, plugin/pr/description.py (the scan line of the incident PR), plugin/pr/digest.py and plugin/pr/counters.py; read at main 5542406, plugin 1.0.1"
generated: { by: sdlc-framework-session/ccr-01de3f80-ilnomi, at: 2026-10-15T20:00:00Z }
---

# The weekly scan validates its findings, applies its patch and reaches the digest

**Status: proposed (roadmap R43), from study entry T26, confirmed by the owner on 2026-10-09, option B of the crosswalk row maintain-scan (the letters are the row's own).** Nothing is built. It amends no decision: decision 16 is kept (the pattern without Claude Security) and decision 20 is kept (the lines go to the digest), so no decision file is written and no number is reserved. It feeds two lines other proposals place: the "Scan" line, which R20 (T28) puts under "State", and the scan's red runs in R18's (T19) "Failed runs" line; its validation rides into the Security & policy brief of R28 (T1 with T2), and its patch step follows R34's (T11) order, the failing test before the fix.

## The problem

The weekly scan works and has found real problems: on the sample the two filings of 2026-09-25 (changes 0004 and 0006) were real findings the owner dismissed with reasons, and on this repository change 0002, a wide authz finding filed on 2026-10-05, went through the whole loop and shipped in 0.3.7 (PR #152) as the shell-guard hook. Three gaps remain between what it produces and what the owner needs:

- **The owner triages without a rating.** A finding is `important` or `nit`; "a finding you are not sure about is a nit with the doubt stated" (`plugin/scan/prompt.py:221-222`) is the only stand-in for the article's validation and confidence. The intent's Evidence section gives the place, the class, the commit and the review's one sentence (`plugin/scan/route.py:275-284`), nothing on how the weakness is reached. On 2026-10-12 the sample's scan filed #56 and #57, and with #55 three scan incidents waited at gate (f) for the owner's triage (`docs/notes/39.md:56`; `docs/handoffs/sessions/2026-10-13-session-26.md:31`).
- **The promised patch is applied by nobody.** The router stores a bounded finding's patch as `evidence/suggested-patch.diff` "for the build run to apply" (`route.py:10-11`, `:230`, `:485-487`), and the review's brief says "The build run applies it after a test that reproduces the vulnerability" (`prompt.py:230-231`); no command reads the file (`git grep -n "suggested-patch\|PATCH_FILE" 5542406 -- plugin template` finds only `route.py`).
- **The scan reaches no surface the owner reads.** The nits, the findings over the cap and the run itself live only in the run's artifact and its job log; the digest's counters show the scan dismissals in force and the incidents merged (`plugin/pr/counters.py:109-116`), not the run. A failed scan is a red run with no park (exit 1) that only the Actions tab shows.

## What the article says

Scans run "on a schedule, without a human in the invocation path", and what they find goes "through the same gates as any other change"; in Claude Security, the hosted form, "each finding [is] validated before it is reported and a confidence rating attached", and "coverage is dated from the last run" (p.46). The steps: a weekly schedule (step 3); "Triage findings with the confidence rating in hand. Dismiss with a reason, so the dismissal is recorded and the same finding does not return as new on the next run" (step 4); a bounded finding's suggested patch reviewed and sent "through the PR review gate like any other change" (step 5); anything wider written up as `intent.md` (step 6); an eval for the vulnerability class once the fix is released (step 7) (p.47). "Every finding has a validation result and a confidence rating, and every dismissal has a reason, so the scan history is an audit record"; "the deterministic checks stay in CI"; the leading indicator is the time from a finding being reported to its patch entering the PR review gate, the lagging one the trend in findings per scan (p.48). Claude Security needs a Claude Enterprise organization (p.46), which a solo owner has no route to[^playbook].

## What the framework does today

Read at `main` 5542406, plugin 1.0.1. The entry's "Today" was read at 619f01a (plugin 0.3.5); `git diff --stat 619f01a 5542406` over `plugin/scan`, `template/.github/workflows/sdlc-scan.yml`, `plugin/pr/digest.py`, `plugin/pr/counters.py`, `plugin/commands/sdlc-build.md`, `plugin/review/findings.py` and `plugin/detect/finding.py` is empty, so every line the entry cites still holds; `plugin/pr/description.py` changed (27 lines) and `plugin/commands/sdlc-deploy.md` changed (47 lines, step 0b's scan fallback, 0.3.6); both are cited at 5542406[^code].

- **Schedule and run.** `sdlc-scan.yml` runs on Mondays at 06:23 UTC and on dispatch (`:37-39`), with `contents: write`, `pull-requests: write`, `issues: write` and no `actions` (`:41-44`). `scan/cli.py review` runs one read-only `claude -p` over the whole tree (Read, Grep, Glob, `Bash(git *)`, one Write of the findings file; Edit and web tools denied; `prompt.py:44-45`), `SCAN_MAX_TURNS` 60 (`cli.py:51`), with the `security-baseline` skill (the project override first, `prompt.py:92-106`) and REVIEW.md's "What Important means here" (`:109-115`). Out of scope: `changes/`, `evals/`, `lessons/`, `framework/`, `.sdlc/`, build outputs and vendored or generated files (`:48-70`).
- **The finding.** `pass`, `severity` (`important` or `nit`), `file`, `line`, `summary`, `rule`, `class`, `bounded`, and for a bounded one a unified-diff `patch` of at most `MAX_PATCH_LINES` = 60 (`prompt.py:40`, `:226-238`, `:254-288`); at most the configured cap of Important findings (`maintain.scan.max_findings`, 3 by default, `:38`, `:146-154`), "say in the reply how many more you saw", at most five nits (`:216-222`); a credential is never quoted (`:223-224`); the dismissed signatures are listed and not reported again (`:239-253`). `load_findings` validates the file and keeps unknown keys (`route.py:78-123`; `review/findings.py:173-197` copies each finding whole); a patch over the limit is dropped and the finding routed as wide (`route.py:111-116`).
- **Filing.** `scan/cli.py route` (`cli.py:222-257`) takes the Important, undismissed, not-already-filed findings, bounded first, then by file and line, at most `--max-findings 3` (`sdlc-scan.yml:107`; `route.py:130-174`, the rest "over the cap: returns next week"). `file_one` (`route.py:455-534`) creates an incident change, `fix` for a bounded finding and `feature` for a wide one (`:468`), writes the intent from a template (a bounded finding's patch inline in "Proposed outcome", `:225-234`), `evidence/scan-finding.json` (`:288-303`), the patch file and `proposal.json`; there is no diagnosis run (`:503`); gate (f) runs and the intent PR opens with `sdlc:f-ready` and `incident`. The PR's summary line reads "security review (<class>, bounded|wide): <summary> at <file:line>" (`plugin/pr/description.py:354-361`).
- **The build of a bounded change.** `/sdlc-build` step 3 writes the reproducing test for any `fix` change, commits it, runs `lock-tests` and then implements (`plugin/commands/sdlc-build.md:72-82`); nothing in it, nor in `/sdlc-design`, mentions the suggested patch.
- **The scanners.** `pip-audit` and `bandit`, or `npm audit`, run `if: always()` and `continue-on-error: true` as reports, never a gate (`sdlc-scan.yml:111-114`; `cli.py:261-272`).
- **What the run leaves.** The artifact `sdlc-scan-<run_id>` keeps `scan-findings.json`, `scan-run.json` (the reviewer's reply, its cost) and the scanners' reports (`sdlc-scan.yml:116-128`). The router's own output, `{filed, skipped, dismissed, problems}` with each skip reason, goes to the job log only (`cli.py:256`), and `filed=<n>` to `$GITHUB_OUTPUT` (`:255`). The reviewer's "how many more you saw" is prose in `scan-run.json`. The artifact's lifetime: 90 days by default, to verify (as in R40, T22).
- **Exit codes.** 0 done; 1 the review failed or wrote no valid findings file, or a filing failed: a red run with no park, in no digest line; 2 a usage error (`cli.py:22-23`, `:48`).
- **The digest.** `plugin/pr/digest.py` has no line of the scan's run; the counters table has "Incidents merged (fix now) / shipped" and "Dismissals in force (detect / scan)" (`counters.py:109-116`).
- **Live.** One run on the sample took 118 s and $0.55 (`docs/notes/14.md:87-89`, run 36166536603). The vulnerability-class eval and lesson are `/sdlc-deploy` step 0b, which reads `scan-finding.json` for a scan incident (`plugin/commands/sdlc-deploy.md:77-79`). Whether any bounded scan change has yet reached a build run: not verified (0002 was wide; 0004 and 0006 were dismissed; 0010 to 0012 waited at (f) on 2026-10-13).

## The proposal

Decision 16 stays as it is: the weekly read-only review with the `security-baseline` skill and REVIEW.md's "What Important means here", at most three Important findings filed as incident intents (bounded first, the rest return next week), the dismissed signatures told to the reviewer and skipped, the deterministic scanners as reports, never a gate. Claude Security stays out: it needs an Enterprise organization. Added, as the owner's note says:

**1. A validation and a confidence per Important finding.** The review's prompt asks, for each Important finding, for the exploit path traced from an entry point, or why the code is not reachable, and a confidence of `high` or `medium`. A finding the reviewer would rate low stays a nit, as "a finding you are not sure about is a nit" says today. Both fields ride into the intent's Evidence section and T1's Security & policy brief (R28), so the owner triages with the rating in hand (p.47 step 4, p.48). Until R28's roles exist, the Evidence section is where the owner reads them.

**2. The patch is applied.** The build run of a bounded scan change is told to start from `evidence/suggested-patch.diff` after writing the failing test (T11's order, R34): write the reproducing test, see it fail, commit and lock it as step 3 does today, then apply the suggested patch as the first fix step and run the test. The entry's direction adds that the run says in `plan.md` whether it applied the patch as given. This keeps the route's own promise (`route.py:10-11`, `prompt.py:230-231`).

**3. The scan reaches the digest.** A "Scan" line in the daily digest: the last run, the Important findings filed and the ones skipped over the cap, and the nits with the artifact's link. R20 places it under "State" (its row 12). `sdlc-scan.yml` joins R18's "Failed runs" line for exit 1 (the review failed or wrote no valid findings file, or a filing failed: a red run with no park), through R18's Actions-API source with no text. Nothing notifies the owner (decision 20). The scan's dispatch of the digest after a filing is R20's part 2, which lists the scan "from `scan/route.py file_findings`, with T26".

**4. The scanners stay reports**, as the article keeps the deterministic checks in CI (p.48).

**The row's corrections**, part of the decision and true of the code above: Mondays 06:23 UTC and on dispatch; the finding's fields (severity, file, line, rule, class, bounded, patch); a bounded finding becomes a `fix` change and a wide one a `feature` change; the nits and the over-the-cap findings live only in the run's artifact; the live run on the sample found two real findings the owner dismissed with reasons.

## How it is judged

On the next scans of the sample and of this repository, after it ships:

- Every filed scan intent's Evidence section carries the traced path (or the reason it is unreachable) and `high` or `medium`; no finding the reviewer rated low is filed. The owner triages each scan PR from the PR alone, without opening the code to find out how the weakness is reached. A filed finding with no validation is the failure.
- Every bounded scan change's build starts from the suggested patch after the red test, and its `plan.md` says whether it applied the patch as given, adapted it or discarded it (the entry's direction and its open item; the reason for an adapted or discarded patch is this proposal's recommendation in "What to settle", mine). A build that rewrites the fix from nothing with the patch unread is the failure.
- The digest's "Scan" line names a run of the last seven days; a scan run that exits 1 is a "Failed runs" line in the next digest, never a red run seen only in Actions.
- The article's leading indicator, read rather than counted (R26, T31, adds no counter for the scan): the time from a scan PR's creation to its build PR, from the PR metadata (p.48).

## What to settle before building

| Question | Recommended |
|---|---|
| The exact fields | Recommended (mine): two keys on each Important finding of the findings file, `validation` (one or two sentences: the entry point and the path to the weak line, or why it is unreachable) and `confidence` (`high` or `medium`), kept by `load_findings` (which already keeps unknown keys), then written by `finding_record` into `scan-finding.json` and by `intent_text` as two Evidence lines; both write a fixed set of keys today (`route.py:288-303`, `:273-285`), so both change. An Important finding with no `validation`, or a `confidence` other than `high` or `medium`, is routed as a nit with the reason in the router's output, not a failed run |
| Whether the router files a `medium` finding as it files a `high` one, or lists it in the digest only | Recommended (mine): filed as a `high` one is: the owner's note sends both ratings into the intent and the brief "so I triage with the rating in hand", and the triage is the owner's. Within the cap, after "bounded first", `high` before `medium` (mine, a second sort key); the rating also on the PR's summary line (`description.py:354-361`) |
| How the build run records that it applied, adapted or discarded the suggested patch, and what the review pass checks about it | Recommended (mine): "Order of work" names the patch as the first fix step; an adapted or discarded patch gets an "Options not taken" line with the reason (the plan-template sections); `git apply --check` against the build branch tells "as given" from "adapted", since the patch was written against the scanned commit. The review pass checks only that the line exists and that the finding's `file:line` changed; it does not judge the patch against the fix |
| Whether the artifact's link in the digest outlives the artifact (90 days by default, to verify, as in R40, T22), or the scan's summary is also kept on a ref | Recommended (mine): a summary on a ref, written by the route step (the job holds `contents: write`): the run's address, its date, the filed changes, the skips by reason, the nit count and the artifact's name; read by the digest with `contents: read`, as R13's release record and R18's failed-run record are. The link is shown while the artifact lives. The route's output goes only to the job log today (`cli.py:256`), so the digest has nothing to read without it |
| What "skipped over the cap" counts | Recommended (mine): the router's "over the cap" skips plus the Important findings the reviewer saw beyond the cap, which today it states only in prose ("say in the reply how many more you saw", `prompt.py:219-220`); a `tally.important_omitted` beside the existing `nits_omitted` makes the number readable with no model, which `normalise` must then keep (it rebuilds the tally with three keys today, `plugin/review/findings.py:192-196`) |
| Whether the scan should read `lessons/` (today only the detection diagnosis does), or the dismissed list suffices | Recommended (mine): the review stays blind to `lessons/` (it is out of the review's scope, `prompt.py:51`, and the class eval of step 0b already tests a fixed class). How a scan incident's lesson is matched to a later finding of the same class is T25's own open item, R42's (T25) to settle; a match outside the review is enough (mine). The dismissed list covers what the owner accepted, the lessons what was fixed |
| A scan dismissal made before the dismissal PR merges | Not this proposal's: a scan dismissal is R23's (T23), as the entry's crosswalk rows say ("maintain-triage (T23: a scan dismissal)"). A dismissal is made with the rating in hand once this ships |
| Whether the validation and the confidence carry a model-judgment label where they are shown | Recommended (mine, beyond the note): yes, they are the reviewer's judgment, labelled as R18 and R20 apply ArtCraft rule A2; the owner folded A2 into T27, T28, T30 and R10, not into T26 (the ArtCraft record, row A2 and "What the owner decides")[^artcraft] |

## Considered and not chosen

- A, the maintain-scan text corrected only.
- C, a diagnosis run for scan findings: the review already investigates the whole tree and writes the finding with its patch, so a second read-only run would repeat it (the same option maintain-diagnose set aside, crosswalk row maintain-diagnose).
- Claude Security itself: it needs a Claude Enterprise organization, which a solo owner has no route to (decision 16 kept).

## Decisions it touches

16 is kept: the weekly read-only review and the scanners as reports, Claude Security out[^decision-16]. 20 is kept: the scan's line and its failed runs go to the digest, nothing notifies[^decision-20]. 25 is kept: gate (f) stays the owner's triage of each scan PR, now with the rating[^decision-25]. 17 is untouched (the class eval at step 0b)[^decision-17]. No decision is amended (the record's close table, row T26), so no decision file is written and no number is reserved.

## Order

In the study's confirmed order T26 sits among "the rest in any order" (the record, section 8 part 2). It changes `plugin/` and `template/`, so it ships as a plugin version with tests; it does not touch `plugin/ci/run_phase.py`. The parts:

| Part | Where | When |
|---|---|---|
| The validation and the confidence: the prompt, the router, the finding record, the Evidence lines, the PR's summary line | `plugin/scan/prompt.py`, `route.py` (`finding_record`, `intent_text`), `plugin/review/findings.py` (`normalise` keeps `important_omitted`), `plugin/pr/description.py`, their tests | Buildable now, independent of every other candidate |
| The same in the Security & policy brief | R28's brief | With R28 (T1 with T2) |
| The patch applied after the failing test, and its line in `plan.md` | `plugin/commands/sdlc-build.md` step 3 and after | Buildable now (step 3's order exists); best after R34 (T11), whose red-at-the-lock, green-at-HEAD proof then covers the applied patch |
| The scan's summary for the digest, and the "Scan" line | the route step, `plugin/scan/cli.py`; `plugin/pr/digest.py` | Buildable now; placed under "State" by R20 (T28). Until R20 ships, the line sits after the queue (mine) |
| `sdlc-scan.yml` in "Failed runs" | R18's Actions-API source | With R18 (T19), which lists "the scan" among its sources with T26; nothing in the scan's code changes (its exit 1 exists) |
| The digest refreshed after a filing | `scan/route.py file_findings`, R20's dispatch job | With R20's part 2 |
| The scan lesson's class matched to a later finding | the router, the lesson's frontmatter | With R42 (T25), whose entry holds the match as an open item |

R45 (T4) may rename what this proposal names; it comes last. The Order column of the ROADMAP row is the owner's.

[^playbook]: `docs/reference/ai-native-sdlc-playbook.pdf` p.46-48.
[^decision-16]: `docs/decisions/16.md`.
[^decision-20]: `docs/decisions/20.md`.
[^decision-25]: `docs/decisions/25.md`.
[^decision-17]: `docs/decisions/17.md`.
[^artcraft]: `docs/reviews/2026-10-13-artcraft-vs-framework.md`, row A2 and "What the owner decides".
[^code]: `plugin/scan/prompt.py`, `plugin/scan/route.py`, `plugin/scan/cli.py`, `template/.github/workflows/sdlc-scan.yml`, `plugin/review/findings.py`, `plugin/commands/sdlc-build.md`, `plugin/commands/sdlc-deploy.md`, `plugin/pr/description.py`, `plugin/pr/digest.py`, `plugin/pr/counters.py`, read at `main` 5542406 (plugin 1.0.1, `.claude-plugin/plugin.json:4`); the crosswalk row maintain-scan and `target-design.md` T26 ("Today").
