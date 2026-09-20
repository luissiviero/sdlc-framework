---
name: intent-template
description: The organization's intent.md template. Use whenever asked to write, draft, update or review an intent, an intent.md, a change request, a feature idea, a ticket write-up or an incident intent for the SDLC framework ("write the intent", "draft intent.md", "capture this idea", "turn this incident into an intent").
---

# intent.md template

Source: article p.10–11 (Stage 1 Plan: "Ask Claude to write the result as intent.md using
the organization's template, which can be encoded as a skill"), p.9 entry routes, p.44
incident intents ("the anomaly and its evidence, a proposed outcome, the affected systems and
any open questions"). Build guide step 10.

Write `changes/<id>-<slug>/intent.md` with exactly this shape. Keep the five article sections
in this order; add the Evidence section only for incidents.

```markdown
# Intent: <short title>
Author: <name> (<role>). Status: draft | proposed | accepted. Change id: <id>. Entry route: idea | ticket <number> | incident <reference>.

## Problem
<the situation in the originator's own words: who is affected, what happens today, cost>

## Proposed outcome
<what will be true when the change is done; stated so it can be checked>

## Affected users and systems
<people, teams, services, data stores, external parties>

## Constraints
<security, data (no new PII), compatibility, budget, deadline, things that must not change>

## Open questions
<questions the design pass must answer; "none" is an acceptable answer>

## Evidence   (incidents only)
<the anomaly: metric, threshold, when it started; where the evidence lives (logs, dashboard,
CI run); what was ruled out>
```

Rules
- Plain language, no formal notation (p.10 step 1). Short paragraphs or bullets.
- `Status` moves draft → proposed (owner has corrected it) → accepted (the intent PR merged).
  The merge is the record of acceptance; do not add approval lines to the file.
- `Change id` is allocated by `plugin/state` (four digits); never invent one.
- Ticket route: put the ticket number in the header and in `status.yaml: external_ref`
  (decision 9: the repo is the source of truth, the tracker holds the link).
- Incident route: fill Evidence from the detection record; the Proposed outcome is the fix
  or the mitigation, not the diagnosis.
- Never leave a section empty; write "none" or "unknown — to be settled in design".
