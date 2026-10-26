---
type: Proposal
title: The detection's state reaches the digest and a ref, and the next metric is a project setting
description: The daily detection's log line is also appended to a record on a ref so the breach history outlives the workflow artifact, a "Detection" line in the digest shows the last verdict, the baseline's size or the days until it fills and the 1σ events, the detect workflow's red runs join the "Failed runs" line, and a `command` metric source lets a project's own script print the day's value with no agent; one metric per project, no notification.
status: accepted
roadmap: R40
sources:
  - id: study-entry
    resource: docs/reviews/2026-09-28-playbook-vs-framework/target-design.md
    title: "T22, confirmed at the close of the study on 2026-10-09; from the crosswalk row maintain-detect (better: both; decision: blend, option B), 2026-10-07; the owner's note corrected after the independent review (the artifact retention marked to verify)"
  - id: record
    resource: docs/reviews/2026-09-28-playbook-vs-framework.md
    title: "Section 7, first bullet (the close); section 8, the close table's T22 row: amends none; the owner's yes; the confirmed order puts T22 in 'the rest in any order'"
  - id: crosswalk
    resource: docs/reviews/2026-09-28-playbook-vs-framework/crosswalk.json
    title: "Row maintain-detect whole; the decision fields of maintain-diagnose (the command source's evidence in meta), maintain-triage (T23: the mute said on the Detection line), deploy-ci (T19), deploy-envs (T20) and x-measure (T31); x-audit (T32) and x-roles (T1: the Operations role reads the detection) are rows the entry touches, with nothing drawn from their decision fields"
  - id: playbook
    resource: docs/reference/ai-native-sdlc-playbook.pdf
    title: "p.42: a deterministic script invokes Claude when a band is breached; p.43 steps 1-4: one metric with a stable rolling baseline (CI test failure rate, post-deploy 5xx rate, PR cycle time), a version-controlled, unit-tested deterministic script, tiers in config, a scheduled trigger; p.44: bands.yaml, invocations and findings logged with a timestamp; p.45: the detection script's log as the leading indicator, process metrics as well as production ones"
  - id: decision-15
    resource: docs/decisions/15.md
    title: "Decision 15: CI test failure rate first, a production metric once a project runs live (kept, given a code path)"
  - id: decision-19
    resource: docs/decisions/19.md
    title: "Decision 19: the maintain adapter names the metric the project emits (kept, given a code path)"
  - id: decision-20
    resource: docs/decisions/20.md
    title: "Decision 20: a review queue and a daily digest, nothing pushes to the owner (kept: the Detection line is a digest line)"
  - id: decision-4
    resource: docs/decisions/4.md
    title: "Decision 4: the automation identity has branch-only write access (kept: the record is a ref, never the default branch)"
  - id: r20
    resource: docs/proposals/digest-needs-you-first.md
    title: "R20 (T28), accepted 2026-10-14: the Detection line placed under 'State'; its recommendation of a fixed 24-hour window for the 1σ events, deferred to T22 ('settled with T22')"
  - id: code
    resource: plugin/detect/cli.py
    title: "cmd_run, _log_line and the exit codes; with plugin/detect/source.py (parse_source, daily_series, DEFAULT_EXCLUDED_ACTORS), plugin/detect/stats.py (TAIL, MIN_BASELINE, evaluate), plugin/detect/finding.py build_record, template/bands.yaml, template/.github/workflows/sdlc-detect.yml, template/.github/workflows/sdlc-digest.yml, plugin/pr/digest.py, plugin/pr/counters.py, plugin/release/cli.py (RELEASED_REF, remote_record), plugin/commands/sdlc-maintain.md §2, plugin/commands/sdlc-init.md §1; read at main 5542406, plugin 1.0.1"
  - id: live
    resource: docs/notes/39.md
    title: "The sample's quiet detect run of 2026-10-11 (tier 0, read from the job log); with docs/notes/41.md, the scheduled run of 2026-10-13 (tier 0) and the dispatched run that filed change 0013 at tier 3"
generated: { by: sdlc-framework-session/ccr-01de3f80-ilnomi, at: 2026-10-15T20:00:00Z }
---

# The detection's state reaches the digest and a ref, and the next metric is a project setting
**Names since R45** (decision 39; the renames built in plugin 1.0.43 to 1.0.47; added on 2026-10-26, the text below keeps the old names, choice 126): `triage` -> `explain` (R18's step and its explanation). \
**Status: proposed (roadmap R40), from study entry T22, confirmed by the owner on 2026-10-09, option B of the crosswalk row maintain-detect (the letters are the row's own).** *[2026-10-20: accepted 2026-10-16 (PR #215)]* Nothing is built. It amends no decision: decisions 15 and 19 are kept and given a code path, 20 and 4 are kept. It defines the "Detection" line that R20 (T28, accepted) places under "State"; R23 (T23) and R42 (T25) each add a sentence to that line, and the detect workflow's red runs reach R18's (T19, accepted) "Failed runs" line. T1's Operations role (R28) reads the detection; nothing here changes it.

## The problem

The detection runs every day, and the owner sees almost nothing of it:

- **The state is visible only in Actions.** A tier 0 run ("insufficient baseline", or no rule fired) and a 1σ verdict change nothing but one JSON line in a workflow artifact and the job log. On the sample, the quiet runs of 2026-10-11 and 2026-10-13 were read by sessions from the Detect step's output, not from anything the owner opens (`docs/notes/39.md:54`, `docs/notes/41.md:37`)[^live]. The digest, the one surface the owner reads daily, has no line about the detection.
- **The breach history expires.** The log is uploaded as an artifact with no `retention-days`; GitHub's default retention is 90 days, from the model's knowledge, to verify. The article's leading indicator, "the detection script's log has the breach timestamp and tier" (p.45), has no record that lasts.
- **The next metric is a framework change.** The code accepts one source kind, `github-actions`; any other source is a usage error. Decision 19's project metrics (job success rate, data freshness, drift) and decision 15's production metric have no code path.
- **An infrastructure failure of the detect run is a red run with no park,** and nothing the owner reads says so.

## What the article says

Maintenance closes the loop with "a deterministic script [that] watches production and invokes Claude when a control band is breached" (p.42). The service owner "picks one metric with a stable rolling baseline, such as CI test failure rate, post-deploy 5xx rate, or PR cycle time"; the script is "version controlled and unit tested, and detection stays entirely deterministic, with no model involved"; the tiers are in version-controlled config, "at 1σ the script only logs"; the trigger can be a scheduled workflow (p.43 steps 1-4). "Invocations, findings and triage decisions are logged with a timestamp" (p.44). The leading indicator is the time from band breach to an intent in the triage queue, and "the detection script's log has the breach timestamp and tier of incident"; the harness "works for process metrics as well as production ones" (p.45)[^playbook]. The article names no digest; showing the state there is the framework's own answer (decision 20).

## What the framework does today

Read at `main` 5542406, plugin 1.0.1. The entry's "Today" was read at 619f01a (plugin 0.3.5); `git diff --stat 619f01a 5542406 -- plugin/detect template/bands.yaml template/.github/workflows/sdlc-detect.yml plugin/pr/digest.py plugin/pr/counters.py plugin/release/cli.py plugin/commands/sdlc-init.md` is empty, so every line it cites still holds (the 1.0.0 read certified `plugin/detect/` unchanged since 0.2.30, `docs/handoffs/sessions/2026-10-14-ccr-15574406-xqm2bq.md:24`). Of the files named here only `plugin/commands/sdlc-maintain.md` moved (the lessons index of 0.3.6, §1) and `template/sdlc.yaml` (a commented `lessons` block, 0.3.6, af4fd87; `maintain:` unchanged)[^code].

- **Schedule and trigger.** `sdlc-detect.yml` runs at `cron: "41 5 * * *"` and on a `workflow_dispatch` whose `force_tier` (2 or 3) rehearses the loop (`template/.github/workflows/sdlc-detect.yml:43-53`), recorded as `forced` and never pre-approving a runbook (`plugin/detect/routes.py:188` `apply_forced`). The workflow's top-level permissions (`:55-60`) give its one job, `detect` (`:67`), `contents: write`, `pull-requests: write`, `issues: write`, `checks: write` and `actions: read`; the concurrency group `sdlc-detect` runs one detection at a time, `cancel-in-progress: false` (`:62-64`).
- **The source.** `cmd_run` reads the source from `bands.yaml`, else `sdlc.yaml: maintain.source`, else `github-actions` (`plugin/detect/cli.py:521`); `parse_source` accepts `github-actions` or `github-actions:<workflow>` and raises on anything else (`plugin/detect/source.py:55`, `:89-104`), which `cmd_run` turns into exit 2, a usage error (`cli.py:522-526`). The series is the CI test failure rate, one point per UTC day that had counted runs, each point's `meta` holding the runs, the failures and up to ten failed runs' ids and URLs, newest first (`source.py:61`, `:153-186`), of which the diagnosis reads at most five (`plugin/commands/sdlc-maintain.md:66`); the framework's own `SDLC …` workflows (`source.py:65`, `:139`) and the workflow token's runs (`github-actions[bot]`, `source.py:70`; a project's own `automation_identity` is counted, `cli.py:544-551`) are excluded. `/sdlc-init` asks for "maintain metric and source [ci_test_failure_rate from github-actions]" (`plugin/commands/sdlc-init.md:41`).
- **The statistics.** A rolling window from `baseline: rolling_30d`; the last `TAIL = 8` points judged against the mean and sample deviation of the older ones; fewer than `MIN_BASELINE = 8` baseline points is tier 0, "insufficient baseline: N point(s), 8 needed" (`plugin/detect/stats.py:56-57`, `:240-252`), so a first verdict needs about 16 counted days. Only complete UTC days are judged (`cli.py:566-567`). `bands.yaml` already accepts `direction: above | below | both` and `min_sigma` (`template/bands.yaml:11-18`; `stats.py:21-28`).
- **The log.** Every run appends one JSON line to `detect-log.jsonl`: `at`, `metric`, `tier`, `rule`, `rules_hit`, `mean`, `sigma`, `latest`, `sigmas`, `action`, `outcome`, `change_id`, `forced`, `reason` (`cli.py:640-657`); a source failure appends an `error` line and exits 1 (`:553-556`); a write that fails is silently skipped (`:441-449`). The line carries the baseline's size only inside `reason`, while the detection record has `n_baseline` and `n_tail` (`plugin/detect/finding.py:72-73`). The workflow uploads the file as the artifact `sdlc-detect-log-<run id>`, with no `retention-days` (`sdlc-detect.yml:112-118`). Nothing commits it.
- **At 2σ and 3σ** one incident change is filed unless an incident of the same metric is open or the finding is dismissed for one baseline window (`cli.py:612-638`); the diagnosis reads the failed runs the record lists (`plugin/commands/sdlc-maintain.md:64-70`), from `failed_run_urls` taken from the latest point's `meta` (`cli.py:583`, `:590`), and the last eight observations, `meta` included, reach `evidence/detection.json` (`finding.py:28`, `:76`).
- **Exit codes:** 0 done (a skip is green with its reason), 1 an infrastructure failure, 2 a usage error (`cli.py:63`). A red run parks nothing.
- **The digest** has no line about the detection: `git show 5542406:plugin/pr/digest.py | grep -ci "detect\|sigma\|baseline"` prints 0. Its only detection figure is the counters' "Dismissals in force (detect / scan)" (`plugin/pr/counters.py:114-115`). The digest job holds `contents: read`, `issues: write`, `pull-requests: read` (`template/.github/workflows/sdlc-digest.yml:29-32`).
- **The precedent for a record on a ref.** The release record is committed into `status.yaml` and pushed to `refs/sdlc/released/<id>`, not a branch, so it survives the head branch's deletion (`plugin/release/cli.py:47-55`, `:106`), and is read back by `ls-remote` and a fetch of the ref, failing closed (`:248-262`).

The crosswalk row's framework text was completed with the entry (the schedule and dispatch, the only source kind, the counted points, one per UTC day with runs, the framework's own workflows and the workflow token's runs excluded, the tail and the tier 0, the log in an artifact only, one incident per metric, the dismissal's one-window mute)[^crosswalk].

## The proposal

One metric per project, CI test failure rate first, the deterministic daily detection, the Western Electric rules, the tiers in `bands.yaml` and the rehearsal by dispatch stay (decisions 15 and 19 unchanged). The owner's note adds four things, "recorded now and built when a project needs it". No notification (decision 20)[^entry].

1. **A `command` metric source.** Beside `github-actions`, `maintain.source: command` names the project's own script, which prints the day's value (or the day's observations) on the runner, with the project's secrets and no agent, as `deploy.command` and the runbooks run. Decision 19's project metrics and the article's post-deploy rate then need no framework change per metric. The script's own evidence for the day rides in the observation's `meta`, which already reaches `evidence/detection.json`; `/sdlc-maintain` §2 reads it where it reads the failed runs today, so a project metric is diagnosable (the crosswalk row maintain-diagnose, option B). The diagnose tools stay `bands.yaml`'s per-project list.
2. **A "Detection" line in the daily digest:** the last verdict (tier, the sigmas of the latest point), the baseline's size or the days until it fills (about 16 counted days before a first verdict), and the 1σ events since the last digest (read as a fixed window, the 24 hours before the digest run: "What to settle", mine). R20 places it under "State"; R23 adds "muted by #n, scheduled since <date>" while a scheduled incident holds the mute, and R42 adds "<id> fixed on <date>: N days, all within 1σ" or "still breaching" after a fix ships.
3. **The log line kept on a ref.** Each run's log line is also appended to a record on a ref, as the release record is on `refs/sdlc/released/<id>`, so the breach history outlives the workflow artifact and the article's leading indicator (p.45) has a record that does not expire. The automation identity still writes nothing to the default branch (decision 4). The digest's Detection line and R42's since-the-fix summary read this record.
4. **The detect workflow joins the "Failed runs" line.** An infrastructure failure of `sdlc-detect.yml` (exit 1) is a red run with no park; it reaches R18's "Failed runs" line through R18's Actions API source, with no triage text, as R18 lists it ("the detection script's … red runs, through the API source with no text").

Not added: several metrics per project (option C), and any notification.

## How it is judged

On the sample, once parts 1 and 2 of "Order" ship (part 3 for the last clause): the morning after each detect run the digest has a Detection line (under "State" once R20 ships) whose tier, sigmas and baseline size match that run's Detect step output; the record on the ref holds one line per run and is still readable after the run's artifact has expired; a dispatched rehearsal reads as a rehearsal, not as a verdict; a detect run that fails at the source shows as a "Failed runs" line the next day. The `command` source is judged when the first project uses it: its metric is detected, a breach is diagnosed from the script's `meta`, and no framework change was needed for the metric.

## What to settle before building

The first five rows are the entry's Open items; the rest are this proposal's own recommendations, marked "mine".

| Question | Recommended |
|---|---|
| The `command` source's contract: one value for the day, or a series with dates; how a missing day is treated; the secrets the step holds and that no agent runs in that job | Mine: the script prints a JSON series on stdout, `[{"at": "YYYY-MM-DD", "value": <number>, "meta": {...}}]`, for every day it can answer within the window, the same shape `daily_series` returns (`source.py:153-186`), so a missed run is backfilled the next day and the window is recomputed every run as today; a day the script leaves out has no point, as a day without runs has none today; a non-zero exit or unparsable output is exit 1 with an `error` log line, as a source failure is (`cli.py:553-556`). The command is named in `sdlc.yaml` (a guardrail file, the owner's edit, as `deploy.command` is), never in `bands.yaml`, and runs in a job of its own with only the secrets it names and `contents: read`, before the job that holds a model session, handing the series over as a step output or a file; no Claude session runs in that job |
| Whether `bands.yaml`'s `direction: below` and `min_sigma` suffice for a metric whose good side is high (a success rate), or whether the source declares it | Mine: they suffice. `direction` already accepts `below` and `both` (`template/bands.yaml:11-13`, `stats.py:21-26`), and `bands.yaml` is where the owner tunes the bands; the source declares nothing. `/sdlc-init` proposes `direction: below` when the owner names a success or throughput metric |
| The ref's name and record shape, shared with T20's rehearsal record (R39); how the digest reads the last verdict (the ref, or the artifact) | Mine: one ref for the project's one metric, a commit per run appending the line to a `detect-log.jsonl` on it; the detect workflow's concurrency group already serializes the writers (`sdlc-detect.yml:62-64`), so one ref suffices where R18 needs one per run; the name is judged with T4 (R45), as R18's ref is, under the `refs/sdlc/` prefix; R39's rehearsal record takes the same shape. The digest reads the ref, by `ls-remote` and a fetch as `remote_record` reads the release ref (`release/cli.py:248-262`), with its `contents: read`; not the artifact, which needs a download and expires (the `actions: read` it also needs, R18 grants the digest anyway, `failed-run-explains-itself.md:82`). A failed push: the verdict stands, the line stays in the artifact, and the run exits 1 as a release whose record could not be pushed does (`release/cli.py:55`), so R18's line shows it |
| How many 1σ events the digest line shows, and whether "insufficient baseline" names the day the baseline fills | Mine, taking R20's recommendation (its "What to settle" row defers the window to this entry, "settled with T22"): a fixed window, the 24 hours before the digest run, so the figure means the same in a dispatched and a scheduled digest once R20 rewrites the issue after every park; the count with each event's date, at most three dates and then "and N more". "Insufficient baseline" shows "n of 8 baseline points, at least k more counted days", not a date: a day counts only when the metric has a value (`source.py:153-186`) |
| The artifact's retention (90 days, from the model's knowledge) | Not verified. Read GitHub's documentation or an artifact's `expires_at` from the API when part 3 is built; the record on the ref makes the figure matter less, and `sdlc-detect.yml` may set `retention-days` explicitly |
| The baseline's size in the log line (mine) | The line gains `n_baseline` and `n_tail`, which the record already has (`finding.py:72-73`), so the Detection line never parses `reason` |
| A rehearsal and an error line on the ref (mine) | Both are appended: a rehearsal line keeps `forced: true` (`cli.py:640-657`) and the Detection line says "rehearsal" beside it; an `error` line shows the gap in the history, and the run is R18's "Failed runs" line |
| What "built when a project needs it" means for each part (mine) | The record on the ref and the Detection line: the sample needs them now (its quiet runs were read only from the job log, `docs/notes/39.md:54`, `41.md:37`). The "Failed runs" source: with R18. The `command` source: when a project names a metric the `github-actions` source cannot read (decision 19's project metrics, decision 15's production metric) |

## Considered and not chosen

- A, the crosswalk text completed and nothing added.
- C, several metrics per project in `bands.yaml`: more than the article's "one metric" (p.43 step 1), and a second incident stream to triage.

## Decisions it touches

None amended, so no decision file is written and no number is reserved (the record's close table: "none"). Decision 15 (CI test failure rate first; a production metric once a project runs live) and decision 19 (the adapter names the metric) are kept and given a code path by the `command` source; decision 20 (the digest, pull not push) is kept, the Detection line being a digest line with no notification; decision 4 is kept, the record living on a ref and never on the default branch[^decision-15][^decision-19][^decision-20][^decision-4].

## Order

In the study's confirmed order, T22 is in "the rest in any order" (the record, section 8). It places nothing itself: R20 (T28, accepted, after R18 and R19) places the Detection line under "State", and R18 (T19, accepted, after R10) defines "Failed runs". R23 (T23) keeps its earlier place in the confirmed order (the gate changes); only its sentence on the Detection line ("muted by #n, scheduled since <date>") ships with or after part 2. R42's (T25) since-the-fix sentence and its reading of the record on the ref come after parts 1 and 2; R39 (T20) shares the record's shape and R45 (T4) judges the ref's name. R16 changes the same code (the detection's days in the owner's offset); mine: build R16 first, so the record on the ref starts on one clock. Parts 1 and 4 change `plugin/detect/`, which the 1.0.0 read certified, and ship as a plugin version with tests (`tests/test_detect_cli.py`, `test_detect_source.py`, `test_detect_stats.py`). The parts:

| Part | Files | When |
|---|---|---|
| 1. The log line on a ref, with `n_baseline` and `n_tail` | `plugin/detect/cli.py`, `template/.github/workflows/sdlc-detect.yml` | buildable now |
| 2. The Detection line, read from the ref | `plugin/pr/digest.py`, `sdlc-digest.yml` (the ref's fetch) | after part 1; placed under "State" by R20, and until R20 ships it sits after the queue and before the counters, as R18's line does |
| 3. The detect workflow's red runs in "Failed runs" | R18's API source | with R18 |
| 4. The `command` source and its evidence in `meta`, read by `/sdlc-maintain` §2 | `plugin/detect/source.py`, `cli.py`, `sdlc-detect.yml` (its own job), `plugin/commands/sdlc-maintain.md`, `plugin/commands/sdlc-init.md`, `template/sdlc.yaml` | when a project needs a metric the `github-actions` source cannot read |

[^entry]: `docs/reviews/2026-09-28-playbook-vs-framework/target-design.md`, T22, the owner's note and "Direction discussed".
[^crosswalk]: `docs/reviews/2026-09-28-playbook-vs-framework/crosswalk.json`, rows maintain-detect and maintain-diagnose.
[^playbook]: `docs/reference/ai-native-sdlc-playbook.pdf` p.42, p.43, p.44, p.45.
[^live]: `docs/notes/39.md` (run 38136170556, 2026-10-11, tier 0); `docs/notes/41.md` (run 38401120163, 2026-10-13, tier 0; run 38498439762, change 0013 at tier 3).
[^code]: `plugin/detect/cli.py`, `source.py`, `stats.py`, `finding.py`, `routes.py`; `template/bands.yaml`; `template/.github/workflows/sdlc-detect.yml` and `sdlc-digest.yml`; `plugin/pr/digest.py`, `counters.py`; `plugin/release/cli.py`; read at `main` 5542406, plugin 1.0.1.
[^decision-15]: `docs/decisions/15.md`.
[^decision-19]: `docs/decisions/19.md`.
[^decision-20]: `docs/decisions/20.md`.
[^decision-4]: `docs/decisions/4.md`.
