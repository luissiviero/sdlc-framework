---
name: plan-template
description: The plan.md template and the interrogation prompt for the read-only planning run at the end of phase (b) design. Use whenever asked to write, review or update a plan.md or an implementation plan for a change in the SDLC framework ("write the plan", "plan.md", "implementation plan for change 0001", "interrogate the plan").
---

# plan.md template and interrogation prompt

Source: article p.16–17 (plan mode steps 2–5 and the plan.md example), build guide step 12,
decision 2: plan.md is produced at the **end of phase (b)** by a run with read-only tools
(Read/Grep/Glob) and approved together with spec.md at gate (b). The first run with edit
tools is phase (c). `/sdlc-design` (B3) is the command that uses this skill.

## The plan (article p.16–17, four sections + one added)

```markdown
# Plan: <title> (from intent.md <date>, spec.md <date>)

## Files that change
<each path, new or changed, one per line, with a phrase saying what changes in it>

## Order of work
1. <step; small enough to be one commit>
2. ...

## Risks
<what the change could break; the riskiest step and why; mitigations>

## Options not taken
<the alternatives Claude considered and why they were not chosen — from the interrogation>

## Proof
<the tests that prove it, by name; the quantifiable target from the spec (p.27 step 3); for UI,
the mock or screenshot to match>
```

## Interrogation prompt (article p.16 step 3; answers land in Risks and Options not taken)

After drafting, answer these in writing before finishing:
1. What could this change break? List every caller, consumer and data shape touched.
2. Which step is the most risky, and what makes it so?
3. What other options did you consider and choose not to do? Why?
4. Could an engineer who has never seen this conversation implement the change from the
   plan alone (p.16 step 4)? If not, what is missing? Add it.
5. Does every item in Proof exist as a runnable test, or is it a test still to be written?
   Say which.

## Rules
- Read-only: this run never edits source files (decision 2). If something must change before
  the plan can be written, say so in Risks.
- In phase (c) the plan-sync hook denies a commit that changes source without changing
  plan.md (p.16 step 7): when implementation departs from the plan, update plan.md in the
  same commit.
- Fix-type change (`status.yaml: change_type: fix`; build guide step 25, article p.28 step 4):
  the first item of Order of work is "write the reproducing test and see it fail", and Proof
  names that test. The build run commits it first and then locks the test files
  (`tests_locked`); the fix must make it pass without touching tests.
- Keep the article's section names exactly; the review's compliance pass reads them.
