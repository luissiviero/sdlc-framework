---
name: coding-standards
description: The organization's coding standards. Use whenever writing, changing or reviewing source code in a project that runs the SDLC framework — during the design pass (spec.md), the implementation run of phase (c), the code-simplifier and the review passes ("apply the coding standards", "is this idiomatic here", "review the diff for style").
---

# Coding standards

## Source
- Article p.19–21 (the CLAUDE.md play: commands with healthy output, conventions that matter,
  "Things Claude gets wrong", and the p.20 example rules "never edit generated classes",
  "Do not bump dependency versions; the platform team owns them") and p.28 (verification
  block: "If a test fails, fix the code, not the test").
- Owner's standards document: **no owner source yet** — when one exists, name it here and
  derive the rules from it (p.21 step 2: "write it from the policy owner's source of truth").
- Project override: a project replaces this skill with `.claude/skills/coding-standards/SKILL.md`.

## Rules
1. Follow the project's `CLAUDE.md` first: its Conventions and Architecture sections and
   "Things Claude gets wrong" outrank anything here.
2. Match the surrounding code: naming, layout, error handling, the language's idioms. A new
   style is a decision for the owner, not a side effect of a change.
3. One change, one concern: the diff stays inside `plan.md`'s "Files that change"; a
   departure updates `plan.md` in the same commit.
4. Every behavior change ships with a test that fails without it; never skip, weaken or
   delete a failing test. Fix the code, not the test.
5. No new dependency without a line in `plan.md` Risks and the owner's merge; never bump
   pinned versions as a side effect.
6. Never edit generated files; regenerate them from their source.
7. Small functions, explicit names, no dead code, no commented-out code, no TODO without a
   change id.
8. Lint and format clean before reporting done, with the project's own targets from
   `sdlc.yaml`.

## Check
Run the deterministic check and include its output in your summary (article p.22 pattern):
```
python "${CLAUDE_PLUGIN_ROOT}/plugin/skills/coding-standards/check.py" --root "${CLAUDE_PROJECT_DIR}"
```
It runs the project's lint target and reports changed source files without a test change and
files over 500 lines. Example output:
```
## coding-standards check
- nothing found
- note: lint target `python -m ruff check .` passed
```
The formatter hook (`hooks.format_on_edit`) and the lint target in the gate are the
deterministic backing; this skill is advisory (p.22 governance).
