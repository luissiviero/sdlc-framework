# evals/ — the project's agent eval suite

<!-- Written by /sdlc-init (build guide steps 33 and 35, decision 17). Project content: the
owner and the incident route fill it; the plugin only creates the folder and the runner. -->

An eval is "the prompt plus the checks that define acceptable (tests pass, lint clean,
behavior unchanged, policy followed)" (article p.30 step 2). The suite regression-tests the
configuration that steers the agent — `CLAUDE.md`, the skills, the hooks — the way tests
regression-test the code (p.30 step 3).

**This suite starts empty on purpose** (decision 17): the article builds it from "20 to 50
real tasks from recent work" (p.30 step 1), which do not exist on day one. It fills from:
- every incident handled in phase (f): "Each production incident gets an eval ... and stays
  in the suite as a regression test" (p.30 step 5, p.44 step 7);
  `python framework/plugin/evals/case.py new --root . --id <id>` writes the skeleton from the
  change's `intent.md` and `evidence/detection.json`;
- every review finding that recurs (the "Things Claude gets wrong" line in `CLAUDE.md` gets an
  eval that proves the correction holds).

## Layout
```
evals/
  README.md          this file
  check.py           runs the suite (the p.30 evals/check.sh, in Python)
  cases/<id>-<slug>/ one folder per eval, named after the change or incident it came from
    prompt.md        the task as the agent receives it
    checks.yaml      what acceptable means (below)
    expected/        optional: golden files the `equals` checks compare against
```

## checks.yaml
Every key is optional except `checks`.
```yaml
description: one line for the report
setup:                         # commands run in the workspace before the agent (no shell; && steps)
  - "python -m pip install pytest"
tools: "Read,Grep,Glob,Edit,Write,Bash(python *)"   # the run's --allowedTools
permission_mode: acceptEdits   # default acceptEdits; bypassPermissions is refused
max_turns: 20                  # default 20
budget_usd: 1.0                # default 1.0 (--max-budget-usd)
timeout_seconds: 600           # wall clock, default 600
checks:
  - command: "python -m pytest -q"     # runs in the workspace after the agent
    exit: 0                            # default 0
  - file: "src/app.py"                 # relative to the project
    contains: "def double"             # a string or a list of strings, all required
    not_contains: "TODO"
  - file: "CLAUDE.md"
    unchanged: true                    # byte-identical to before the run
  - file: "out.txt"
    equals: "expected/out.txt"         # byte-identical to the case's golden file
  - file: "debug.log"
    exists: false                      # must not exist
  - output:                            # the agent's final answer
      contains: "passed"
      not_contains: "cannot"
      regex: "\\d+ passed"
  - denied: "Edit"                     # a tool the permission rules or a hook refused
```
A file check without `exists` requires the file when it asserts `contains` or `equals` (or
nothing else); a check that only asserts `not_contains` or `unchanged` passes when the file
is absent. A check with an unknown key, a case without `prompt.md` or `checks.yaml`, and a
`checks.yaml` that cannot be read fail the case with the reason: nothing is skipped.

## Running it
```
python evals/check.py                      # every case
python evals/check.py --case "0007-*"      # one case
python evals/check.py --dry-run            # list the cases and the command each would run
```
`check.py` finds the framework (`--framework <dir>`, `$SDLC_FRAMEWORK_DIR`, or the
`framework/` checkout beside `evals/`) and runs `plugin/evals/run.py` against this project.
Each case runs in a throwaway copy of the project with one bounded
`claude -p ... --output-format json --permission-prompts none` call; the project's
`CLAUDE.md`, hooks and settings stay loaded (no `--bare`), because they are what the suite
tests. The credential is the environment's: `ANTHROPIC_API_KEY` when present, else
`CLAUDE_CODE_OAUTH_TOKEN`. A run that ends in an error, hits `max_turns` or the budget, or
passes the wall clock fails its case.

The runner writes `evals-report.json` in the current directory (every case, its checks, turns
and cost, the pass rate) and prints a table; it exits 0 when the pass rate reaches
`--min-pass-rate` (default 1.0), 1 below. In CI the pass rate is the merge check on changes to
`CLAUDE.md`, `.claude/**` or the plugin version: "A skill change that drops the pass rate gets
reviewed before it merges" (p.30 step 4; p.31 governance: "The pass-rate threshold is
enforced as a merge check").
