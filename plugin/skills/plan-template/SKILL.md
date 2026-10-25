---
name: plan-template
description: The plan.md template and the interrogation prompt for the planning run at the end of the design phase. Use whenever asked to write, review or update a plan.md or an implementation plan for a change in the SDLC framework ("write the plan", "plan.md", "implementation plan for change 0001", "interrogate the plan").
---

# plan.md template and interrogation prompt

Source: article p.16–17 (plan mode steps 2–5 and the plan.md example), build guide step 12,
decision 2: plan.md is produced at the **end of the design phase** by a run with read-only
tools (Read/Grep/Glob) and approved together with spec.md at the design gate. The first run
with edit tools is the build phase. `/sdlc-design` (B3) is the command that uses this skill.

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
the mock or screenshot to match; a dropped test file or eval case this plan's own work
requires, declared with `- ratchet: <name> may fall, because <why>` (`<name>` is `tests` or
`evals`; the gate's `ratchets` check reads this line)>
```

### Proof items (change 0004; the grammar is `plugin/gate/artifacts.py`)
Beside prose and the `ratchet:` line, `## Proof` may list items, one per line. Only a list
item whose text starts with `test:`, `screenshot:` or `state:` is an item; the gate's parser
reads only those, and every other line stays allowed:
- `- test: <name>` — a test by name; the suite is the `commands` entry's, not compared here.
- `- screenshot: evidence/proof/<file>.png`, optionally followed by ` vs mock/<file>` when the
  spec's Acceptance carries `Mock: mock/<file>` — the drive must write the file.
- `- state: evidence/proof/<file> <path> ==|contains|matches <value>` — `<path>` is a dotted
  JSON key (`status.code`, `items.0.name`) for a JSON file, or `line` for a text file; `<value>`
  is the rest of the line.

How a `state` item is compared (one definition, used by the gate and by `collect.py`):
- **The one parse**: the expected value and each line of a text file are read as JSON when they
  parse (`200`, `true`, `"x"`, `null`), else as the string itself.
- `==` holds only when the two parsed values have the same type and value at every depth: a
  bool never equals a number, `1` never equals `1.0`, `[true]` is not `[1]`; the text `200` and
  the JSON number 200 both equal `== 200`. `contains` is a substring of the string form (the
  value itself for a string, its JSON otherwise), or membership when the value seen is a list;
  `matches` is a Python `re.search` on the string form.
- **The any-line rule**: with `line`, the item holds when any line of the text file satisfies
  the comparison; on a `differs` the value seen is the file's first line. An empty file, a file
  over 1 MiB, an unreadable or invalid JSON file, or a missing key is `not produced`.

A `state` or `screenshot` item needs `sdlc.yaml: commands.drive` (the design gate's check
`proof_items` refuses the plan without one, and refuses a malformed item by its line). The
runner's step runs the drive after the session in the build, test and deploy phases and
compares the items of the plan approved at the design gate; an item added during the build is
reported, never the bar.

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
- In the build phase the plan-sync hook denies a commit that touches a source file "## Files
  that change" does not list unless plan.md changes in the same commit (p.16 step 7): when
  implementation departs from the plan, update plan.md in the same commit. The list is the
  contract, so name every file, or a directory with a trailing `/`.
- Fix-type change (`status.yaml: change_type: fix`; build guide step 25, article p.28 step 4):
  the first item of Order of work is "write the reproducing test and see it fail", and Proof
  names that test. The build run commits it first and then locks the test files
  (`tests_locked`); the fix must make it pass without touching tests.
- Keep the article's section names exactly; the review's compliance pass reads them.
