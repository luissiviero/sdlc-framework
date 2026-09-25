# lessons/ — the incident record

<!-- Written by /sdlc-init (build guide step 36; article p.49: the diagnosis "writes the
post-mortem to a version-controlled lessons file that future investigations can read").
Project content: the fix of an incident appends here; the plugin only creates the folder. -->

One file per incident, **written when its fix ships** (the phase (e) run of a change whose
entry route is `incident`, `/sdlc-deploy` step 0b), and **read before any diagnosis** (the
phase (f) run of `/sdlc-maintain` reads every file here first): the second incident of a
class is cheaper than the first only if the first was written down. The file rides in the
fix PR and is reviewed like any other file.

## Naming
`lessons/<yyyy-mm>-<slug>.md` — the month the fix shipped and the incident change's slug
(the article's own example, p.49: `lessons/2026-06-checkout-cache.md`). One incident, one
file; a repeat of the same class gets its own file that cites the earlier one.

## Shape
```markdown
# <title of the incident change>
Change: <id> · Detected: <date> (<metric> at tier <n>, <rule>) · Fixed: <date>, PR #<n>

## What happened
<the anomaly as the detection record and the diagnosis saw it; the run URLs>

## Root cause
<what was actually wrong, in one paragraph; what the diagnosis got wrong, if anything>

## Fix
<what changed and where; the runbook that ran, if one did, and whether it was the right call>

## Prevention
<the eval case added (evals/cases/<id>-<slug>/), the band or the test that would have caught
it earlier, the CLAUDE.md line proposed, if any>
```

The eval case (article p.44 step 7: "When a fix ships, add an eval for the incident") is
the executable half of the lesson; this file is the half a person reads.
