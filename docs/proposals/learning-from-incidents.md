---
type: Proposal
title: Learning from an incident, the rest of it — the metric's return to baseline on the record, and a scan incident's lesson
description: After an incident's fix ships, the daily detection's verdicts for that metric since the fix are summarised with no agent in R40's Detection line ("<id> fixed on <date>: N days, all within 1σ", or still breaching), read from the log on the ref, and the next diagnosis of the same metric reads them; a scan incident's lesson names the finding's class and signature where a detection incident's names the metric and the tier; the lesson checked at gate (e), the entry's first addition, is already built (plugin 0.3.6).
status: proposed
roadmap: R42
sources:
  - id: study-entry
    resource: docs/reviews/2026-09-28-playbook-vs-framework/target-design.md
    title: "T25, confirmed at the close of the study on 2026-10-09; from the crosswalk row maintain-learn (better: both; decision: blend, option B), 2026-10-07; the annotation of 2026-10-09 (re-checked at plugin 0.3.6)"
  - id: record
    resource: docs/reviews/2026-09-28-playbook-vs-framework.md
    title: "Section 8, the close table's T25 row: amends none; yes, the lesson check is built (0.3.6), the baseline line and the scan lesson remain; the owner's yes"
  - id: crosswalk
    resource: docs/reviews/2026-09-28-playbook-vs-framework/crosswalk.json
    title: "Row maintain-learn whole; the decision fields of test-evals (T13), maintain-detect (T22), maintain-diagnose, maintain-scan (T26), x-measure (T31), maintain-tag and x-roles (T1)"
  - id: playbook
    resource: docs/reference/ai-native-sdlc-playbook.pdf
    title: "p.44 step 7: an eval for the incident when a fix ships; p.45: the detection log's breach timestamp and tier, repeat incidents of the same class as the lagging indicator; p.47 step 7: an eval for the vulnerability class; p.49: Claude verifies the metric is back at baseline and writes the post-mortem to a version-controlled lessons file"
  - id: decision-17
    resource: docs/decisions/17.md
    title: "Decision 17: evals after ~20 real changes, the folder filled by incidents from day one (kept)"
  - id: decision-20
    resource: docs/decisions/20.md
    title: "Decision 20: the queue and the daily digest, nothing pushes to the owner (kept: the baseline line is a digest line)"
  - id: decision-16
    resource: docs/decisions/16.md
    title: "Decision 16: the weekly read-only scan, fixed classes to evals (kept)"
  - id: code
    resource: plugin/commands/sdlc-deploy.md
    title: "Step 0b; with template/lessons/README.md, plugin/gate/checks.py lesson_and_eval, plugin/gate/artifacts.py LESSON_REQUIRED_FIELDS, plugin/lessons/index.py, plugin/commands/sdlc-maintain.md §1, plugin/detect/cli.py and stats.py, template/.github/workflows/sdlc-detect.yml, plugin/pr/digest.py, plugin/release/cli.py, plugin/scan/prompt.py and route.py; read at main 5542406, plugin 1.0.1"
  - id: live
    resource: lessons/2026-10-security-authz-the-guardrail-self-protec.md
    title: "This repository's change 0002, a scan incident, through gate (e) on 2026-10-12 (lesson committed in 1a6cf11, gate (e) evidence in c2e327f, evidence/gate-e.json); the sample's change 0013, its first real detection incident, filed on 2026-10-14 (docs/notes/41.md) and abandoned that day with its duplicate 0014 (docs/notes/43.md)"
generated: { by: sdlc-framework-session/ccr-01de3f80-ilnomi, at: 2026-10-15T20:00:00Z }
---

# Learning from an incident, the rest of it: the metric's return to baseline on the record, and a scan incident's lesson

**Status: proposed (roadmap R42), from study entry T25, confirmed by the owner on 2026-10-09, option B of the crosswalk row maintain-learn (the letters are the row's own).** Part of the entry is built: its first addition, gate (e) requiring the lesson beside the eval case, shipped before the close in plugin 0.3.6 as change 0003 (ROADMAP R1 on `lessons/`) and is not proposed again; this proposal covers the two parts that remain, the baseline line and the scan incident's lesson. One recommendation in "What to settle" (row 1) would extend the built check to the four body sections; it is this session's, beyond the close row's "remain", and the owner accepts or declines it. It amends no decision. Its baseline line is a sentence inside R40's (T22) Detection line, which R20 (T28) places under "State"; the scan lesson shares an open item with R43 (T26).

## The problem

The article closes an incident in two halves: an eval for the incident, and Claude confirming "the metric is back at baseline" before writing the post-mortem to a lessons file future investigations read (p.44, p.49)[^playbook]. The framework writes both files and, since 0.3.6, checks them at gate (e). Two gaps remain:

- **Nothing ties the metric's return to baseline to the incident.** After the fix ships, the daily detection keeps judging the metric, but its verdicts reach only the job log and a workflow artifact. The owner cannot see whether a fix held without opening artifacts, and the next diagnosis of the same metric starts without the previous fix's outcome. The confirmation cannot go into the lesson, which is written before the verdicts exist.
- **A scan incident's lesson borrows a detection incident's fields.** The lesson's `detected` block names a metric and a tier. For a scan incident, step 0b writes `metric: "security: <class>"` and `tier: 3`, and the finding's signature appears nowhere in the lesson. The index then shows the scan lesson as "Tier 3", a tier the scan never computed.

## What the article says

Maintain's step 7: "When a fix ships, add an eval for the incident" (p.44)[^playbook]; for the scan, "When a fix is released to production, add an eval for the vulnerability class" (p.47 step 7). The leading indicator is "the detection script's log", which "has the breach timestamp and tier of incident"; the lagging indicator includes "repeat incidents of the same class, which should fall as the fixes add cases to the eval suite" (p.45). In the incident channel, "Claude verifies the metric is back at baseline and confirms it in the thread, writes the post-mortem to a version-controlled lessons file that future investigations can read" (p.49). The framework has no channel (the row maintain-tag: the incident PR thread is the channel, and this proposal's line is its baseline confirmation), so the confirmation becomes a line on the record that no agent writes.

## What the framework does today

Read at `main` 5542406, plugin 1.0.1. The entry's "Today" was read at 619f01a (0.3.5) and re-checked at 0.3.6. `git diff --stat v0.3.6 5542406` on the files cited below shows one change, `plugin/gate/checks.py | 3 +--`: change 0002's import reorder (9d19208). The detection log, the digest and the lesson's fields stand as 0.3.6 shipped them[^code].

- **Built: the lesson and the eval at gate (e).** When `status.yaml: entry_route` is `incident`, the (e) run writes `lessons/<yyyy-mm>-<slug>.md` with R1's frontmatter and the four body sections, one eval case under `evals/cases/<id>-<slug>/`, and the rebuilt `lessons/index.md`, before the review pass, and lists all three in `plan.md` (`plugin/commands/sdlc-deploy.md:66-111`; the shape in `template/lessons/README.md:20-73`). Gate (e)'s `lesson_and_eval` (`plugin/gate/checks.py:1636-1682`) fails an incident change with no single lesson matching its slug, a required frontmatter field missing or empty (`plugin/gate/artifacts.py:93-105`; `detected` only has to be a non-empty mapping, `checks.py:1593-1607`), a `supersedes` target not retired (`:1613-1631`), a missing `prompt.md` or `checks.yaml` (`:1664-1669`), or a stale index (`:1671-1673`). It does not read the four body sections. The eval case's "at least one check" is R35's (T13).
- **The diagnosis reads the lessons.** `/sdlc-maintain` §1 runs `lessons/index.py check`. It opens only the lessons whose heading or tags name the finding's metric or the rule that fired, plus every retired and unsorted one, and cites the lesson it relied on in the intent's Evidence section (`plugin/commands/sdlc-maintain.md:45-59`). The weekly scan does not read `lessons/`: its prompt excludes the folder from its scope (`plugin/scan/prompt.py:46-51`).
- **A scan incident's lesson.** The entry's "Today" said step 0b read "what happened" from `evidence/detection.json`, which a scan incident lacks. Since 0.3.6, step 0b falls back to `evidence/scan-finding.json`, with `metric: "security: <class>"`, `rule: "scan"` and `tier: 3` (`sdlc-deploy.md:76-79`). The finding record carries a `signature` and a `class` (`plugin/scan/route.py:288-300`), but no lesson field holds the signature. The index requires `detected.tier`; a lesson without one goes to `## Unsorted` (`plugin/lessons/index.py:101-103`). Each line prints "Tier <n>" (`:246`).
- **Exercised live once, on a scan incident.** This repository's change 0002 (a scan finding, `entry_route: incident`) passed gate (e)'s `lesson_and_eval` (`changes/0002-security-authz-the-guardrail-self-protec/evidence/gate-e.json:168-173`, 2026-10-12; the lesson committed in 1a6cf11, the gate (e) evidence in c2e327f). Its lesson's `detected` block reads `metric: "security: authz"`, `tier: 3`, `rule: scan`, with no signature (`lessons/2026-10-security-authz-the-guardrail-self-protec.md:9-13`). The index line reads "Tier 3, Oct 2026" (`lessons/index.md:4`). This overtakes the entry's "no incident has reached (e)" for the scan path. No detection incident has reached (e) yet. The sample's first real one, change 0013 (tier 3, `we1`, 18.27σ), was filed on 2026-10-14 (`docs/notes/41.md`) and abandoned that day: the owner closed its PR #60 without a merge or a dismissal. The duplicate a dispatched run then filed, 0014, was closed the same way (PR #62) (`docs/notes/43.md:39`, `:44`).
- **The detection log.** Each run, scheduled or dispatched, appends one JSON line with `at`, `metric`, `tier`, `rule`, `rules_hit`, `mean`, `sigma`, `latest`, `sigmas`, `action`, `outcome`, `change_id`, `forced` and `reason` (`plugin/detect/cli.py:441-449`, `:640-657`) to `detect-log.jsonl` (`template/.github/workflows/sdlc-detect.yml:110`). A dispatch with `force_tier` rehearses the loop whatever the metric says, and its line carries `forced` (`:21-22`, `:575-581`). The file is kept only as a workflow artifact, with no `retention-days` set (`:112-118`; the default retention is to verify, R40). No line of `plugin/pr/digest.py` mentions the detection (`grep -ci detect` prints 0). The log on a ref and the Detection line are R40's (T22).
- **The fix date.** The release record writes `released_at`, `released_sha` and `released_pr` to `refs/sdlc/released/<id>` (`plugin/release/cli.py:48-56`, `:106`). The record job runs only after a command that exited 0 (`:45-47`). With `deploy.action none` or an empty `deploy.command`, the release workflow ends at "done" and writes no record (`:638-643`), so such a project has no release date to read.
- **The baseline absorbs the breach.** The baseline is every point of the rolling window older than the 8-point tail (`plugin/detect/stats.py:14-20`). The breach days enter it eight counted days after they happen, which widens the band a later "within 1σ" is judged against.

## The proposal

D17 stays, and step 0b and the gate check stay as built. Two additions:

1. **The metric's return to baseline, on the record, with no agent.** After the fix ships, a deterministic step reads the detection log on R40's ref. It summarises that metric's verdicts since the fix date in R40's Detection line: "<id> fixed on <date>: N days, all within 1σ", or "still breaching: <tier> on <date>". R20 places the line under "State" (T28's owner's note: "T25's since-the-fix text"). The next diagnosis of the same metric reads the same summary, so a repeat is diagnosed with the previous fix's outcome in hand (p.49). No line goes into the lesson, which is written before the verdicts exist. Nothing notifies the owner (decision 20).
2. **For a scan incident, the lesson's header line names the finding's class and signature instead of a metric and a tier** (the owner's words; since 0.3.6 the header's fields are the frontmatter's `detected` block). This session reads that as: step 0b's scan branch, the README's shape, and the index's render and Unsorted rule (`index.py:101-103`, `:246`), so the lesson does not fall into `## Unsorted` and the index does not print a tier the scan never computed ("What to settle", the scan lesson's `detected` fields). Gate (e)'s required fields are unchanged (`detected` stays a required mapping).

Not proposed, as the owner's note says: a repeat-of-class counter in the digest (option C). R26 (T31) records the same choice and leaves "whether a fix held" to this line.

## How it is judged

On the first detection incident that reaches (e) after this ships (on the sample, a new breach's incident: 0013 and 0014 were abandoned, and the sample's pin, plugin 1.0.1 on its `main` at f88b262 (`sdlc.yaml:77`), must first be raised to a version carrying this proposal and R40; with the sample's `deploy.action: none` (`sdlc.yaml:24`), its fix date would come from the merge-time fallback in "What to settle", row 2):

- From the fix date on, each daily digest's Detection line carries "<id> fixed on <date>: N days …", with N equal to the counted days the log holds since that date (lines marked `forced` not counted, if the owner takes row 2's recommendation).
- A breach of the same metric after the fix shows as "still breaching" in the next digest, not only in an artifact, including the breach that files the metric's next incident.
- The next diagnosis of that metric cites the since-the-fix summary in its intent's Evidence section.
- On the next scan incident, the lesson's `detected` block carries the class and the signature and no tier, and the index lists it under its class without "Tier".

Any model call in the baseline path is a failure, and so is a line the log does not support.

## What to settle before building

The first four rows are the entry's Open items. The recommendations, and the rows after them, are this session's, not the owner's.

| Question | Recommended |
|---|---|
| Deterministically, what "in the README's shape" means for the gate | Partly settled by 0.3.6: the frontmatter fields, the `supersedes` rule and the fresh index (`artifacts.py:93-105`, `checks.py:1636-1682`); the header's fields are now the frontmatter's. The owner's close row treats the lesson check as built and names only the baseline line and the scan lesson as remaining, so what follows is an extension for the owner to accept or decline. Recommended (this session): also require the four body sections present and non-empty with the existing `missing_sections`/`empty_sections` helpers (`artifacts.py:245-252`), as the artifacts check already does for an incident intent's Evidence section (`checks.py:206-212`). The lesson's quality stays the review pass's. |
| The window of the "since the fix" summary, and how the fix date is read | Recommended (this session): from the fix date until the metric's next incident is filed or one baseline window (`bands.yaml: baseline`, 30 days) has passed, whichever comes first. The day that files the next incident is inside the window: a shipped incident no longer blocks filing (`detect/cli.py:291-295`), so a tier 2 or 3 breach after the fix files a new incident in the same run, and the line ends on "still breaching: <tier> on <date>" with the new incident's id. Lines marked `forced` (a rehearsal) are skipped and not counted in N. For the first eight counted days after the fix the tail still holds pre-fix points (`stats.py:16-20`, `:29-39`), so a rule such as `we4` can fire partly on them; the line reports the verdict as the log has it. After the window the line leaves the digest but stays readable on the ref. The fix date is `released_at` from `refs/sdlc/released/<id>`, read as R41 (T24) reads it for the breach window. Whenever no record exists (for instance `deploy.action none` or an empty `deploy.command`, `release/cli.py:638-643`), it is the merge time of the incident's build PR (`fixed.pr`). |
| Whether R1's generated `lessons/index.md` is written by the (e) run or by the runner | Settled by 0.3.6 (the entry's own annotation): the (e) run rebuilds it in step 0b and lists it under "Files that change" (`sdlc-deploy.md:100-106`). |
| How a scan incident's lesson is matched to a later finding of the same class, since the scan does not read `lessons/` | Recommended (this session): deterministically, by the class in the lesson's frontmatter. When the scan's router files a finding, it names the lessons with the same class in the new intent's Evidence section, so the build run and the review pass read them, with no model. Whether the scan's review itself reads `lessons/` stays R43's (T26) open item. |
| Where the next diagnosis reads the since-the-fix summary (this session's addition) | `detect/cli.py` copies the metric's since-the-fix summaries into the new incident's detection record, which `/sdlc-maintain` §1 already reads first. No new tool, no read of the ref by the session. The Operations role of R28 (T1), which reads `lessons/` and the incident, gets the summary the same way, through the incident's detection record; its brief gains no source. |
| The scan lesson's `detected` fields (this session's addition) | `at`, `class`, `signature`, `rule: scan`, with no metric and no tier. The index groups the lesson by class (its first tag) and prints no tier for it. Lessons already written, such as change 0002's, keep their fields and are not rewritten. The field names are judged with R45 (T4). |
| Who settles an overspend lesson's `detected` block and its index rule (this session's addition) | R25 (T30) writes an overspend lesson in `lessons/` and leaves its shape "settled with R42". This proposal settles only the detection block and the scan block; an overspend lesson has no metric and no tier, so under the index's rule it goes to `## Unsorted` (`index.py:101-103`). Recommended (this session): R25 owns the overspend lesson's `detected` block and the index rule that groups it by its `overspend` tag, built after the scan block here, whose grouping by first tag it can reuse. |
| Whether "within 1σ" is judged against the mean and sigma frozen in the incident's `evidence/detection.json` instead of the log's own verdicts (this session's question) | A departure from the owner's note, which reports "the metric's verdicts since the fix ... read from the log on the ref". The log's tier and sigmas are judged against the rolling baseline, which takes in the breach days eight counted days after them (`stats.py:14-20`), and a frozen baseline would print lines that can disagree with the log's own verdicts. Not recommended: the log's verdicts stand unless the owner chooses otherwise. |

## Considered and not chosen

- A, the row's text corrected only.
- C, a repeat-of-class counter in the digest, the article's lagging indicator (p.45): x-measure's row, which left the same counter out as its own option C (R26, T31), with the reason that with one metric per project incidents are few and this proposal's since-the-fix line already says whether a fix held.
- From the entry's direction: a "back at baseline" line in the lesson. It is not possible, since the lesson is written before the verdicts exist.

## Decisions it touches

None amended, so no decision file is written and no number is reserved. Decision 17 is kept (the suite fills from incidents; step 0b unchanged). The lesson check is R1's own design, cited and not changed. Decision 20 is kept: the baseline line is a digest line, and nothing notifies the owner. Decisions 15 and 19 are kept (the CI test failure rate first, a production metric once a project runs live; the metric each project emits; one watched metric per project, as T22 and R40 keep it), and so is decision 16 (the weekly read-only scan, fixed classes to evals). Decisions 27, 28 and 29 do not touch it[^decision-17][^decision-20].

## Order

The record's confirmed order puts T25 among "the rest in any order" (section 8). Its dependencies:

| Part | Where | When |
|---|---|---|
| The since-the-fix summary and its sentence in the Detection line | `plugin/detect/` (a summary read from the log on the ref), `plugin/pr/digest.py` | After R40 (T22: the log on a ref and the Detection line), placed by R20 (T28) under "State"; the fix date read as R41 (T24) reads the release record |
| The summary in the next incident's detection record | `plugin/detect/cli.py`, `plugin/detect/finding.py`, `/sdlc-maintain` §1 | With the part above |
| The scan lesson's class and signature | `/sdlc-deploy` step 0b, `template/lessons/README.md`, `plugin/lessons/index.py` | Buildable now, independent of R40; best beside R43 (T26), which shares the open item on matching a later finding of the same class |
| The router naming the lessons of the same class in a scan intent's Evidence section, only if the owner takes "What to settle", row 4 | `plugin/scan/route.py` `intent_text` | After the scan lesson's `class` field above; beside R43 (T26), whose Order places the same part "With R42 (T25)" |
| The four body sections at gate (e), only if the owner accepts the extension ("What to settle", row 1) | `plugin/gate/checks.py` `lesson_and_eval` | Buildable now; beside R35 (T13), which owns the eval half of the same check |

It changes `plugin/` and `template/`, so it ships as a plugin version with tests. R25 (T30) writes its overspend lesson beside these lessons; its `detected` block and index rule are R25's to settle ("What to settle", the overspend row), after the scan lesson's block here. R45 (T4) renames last.

[^playbook]: `docs/reference/ai-native-sdlc-playbook.pdf` p.44 step 7, p.45, p.47 step 7, p.49.
[^code]: Read at `main` 5542406 (plugin 1.0.1) with `git show 5542406:<path>`; the line numbers above are at that commit.
[^decision-17]: `docs/decisions/17.md`.
[^decision-20]: `docs/decisions/20.md`.
