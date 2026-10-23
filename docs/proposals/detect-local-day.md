---
type: Proposal
title: Detection counts days in the owner's offset — a fixed UTC offset in sdlc.yaml for the daily points, the complete-days rule and the times the record shows
description: The detect script counts one point per UTC day; the owner lives at UTC-03:00, so a day's point is not the owner's day. A fixed offset in sdlc.yaml (default +00:00) moves the day boundary, the complete-days rule and the record's displayed times to the owner's clock.
status: proposed
roadmap: R16
sources:
  - id: owner-choice
    resource: "the owner's answer of 2026-10-14 in the item-11 session (G2 of docs/handoffs/2026-10-14-item-11-part-1-read.md): count days in -03:00, after 1.0.0"
    title: "The owner asks for the detection's days in their own offset"
  - id: source-day
    resource: plugin/detect/source.py
    title: "One observation per UTC day: a run's day is the first ten characters of its created_at"
  - id: complete-days
    resource: plugin/detect/cli.py
    title: "_today() is the UTC date; only days before it are judged"
  - id: notes-42
    resource: docs/notes/42.md
    title: "The breach-window commits carry the committer's -03:00 while every other time is UTC"
generated: { by: sdlc-framework-session/item-11, at: 2026-10-14T10:00:00Z }
---

# Detection counts days in the owner's offset

## Why
`plugin/detect/source.py` puts a run on the UTC day of its `created_at`, and `plugin/detect/cli.py` judges only days before the UTC today. The owner lives at UTC-03:00. A run the owner starts at 22:00 on Monday counts on Tuesday; the sample's scheduled `CI` run (cron `29 1 * * *`, 01:29 UTC) is 22:29 the evening before on the owner's clock. The detection record mixes clocks too: its breach-window commits keep the committer's `-03:00`, every other time is UTC (NOTES §42, item 11's G2). The owner chose, on 2026-10-14, to have the days counted in their own offset, after 1.0.0.

## What changes
- **One key** in `sdlc.yaml`, under `maintain` (or `detect`): `day_offset: "-03:00"`, a fixed UTC offset, default `"+00:00"` (today's behaviour). The project's `sdlc.yaml` is a guardrail file: the owner sets the key; the template carries it commented. *[2026-10-20, R60's answers (the owner, for when this is built; `docs/reviews/2026-10-20-lifecycle-axis-ports/options.md`, section 2, row "Detection's day boundary"): `/sdlc-init` writes the key from the owner's time zone, asked once, so the owner does not set it by hand; it stays a fixed offset]*
- **The day of a run** is the date of `created_at` shifted by the offset (`source.py`), and **today** for the complete-days rule is the date at that offset (`cli.py _today`).
- **The record's displayed times** (`detection.json` `at` and `commits[].at`, the PR body) are written in the same offset, so one record reads on one clock. `breach_start` and the observations' `at` are local dates.
- **Not changed**: the signature (`detect|metric|rule`), the dismissal store's `until` (a date, read in the same offset), the bands and the rules.

## Why a fixed offset and not a time zone name
A name such as `America/Sao_Paulo` needs `zoneinfo`, which has no time zone database on Windows without the third-party `tzdata` package (decision 7: no third-party dependency). São Paulo has had no daylight saving time since 2019, so a fixed offset is exact for the owner today; a project in a zone with daylight saving time would see its day boundary move by an hour twice a year, which a daily rate tolerates.

## What it costs
- The series is recounted once when the key is set: the run cache keeps each run's `created_at`, so no history is lost, but points move between days, and a baseline built on UTC days changes on the first run after the change. Set the key on a quiet day, not in the middle of a breach.
- The detect cron (`41 5 * * *`, 05:41 UTC, 02:41 at -03:00) still runs after the owner's day ends, so "complete days only" keeps its meaning.

## Tests
- A run created at `2026-10-14T01:29:00Z` counts on 2026-10-13 with `-03:00` and on 2026-10-14 with the default.
- With `-03:00` and a clock at `2026-10-14T02:00:00Z`, today is 2026-10-13 and 2026-10-13's point is not judged.
- A commit made at `-03:00` is listed in the record at the configured offset; with the default it is listed in `Z`.
- An invalid offset is a configuration error naming the key, never a silent fall back to UTC.

## Decisions it touches
15 read (the metric is unchanged); 7 kept (no `tzdata`); 6 kept (the key in the project's `sdlc.yaml` is the owner's edit). No decision amended.
