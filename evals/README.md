# evals/ — the project's agent eval suite

<!-- Written by /sdlc-init (build guide step 33, decision 17). Project content: the owner
and the incident route fill it; the plugin only creates the folder. -->

An eval is "the prompt plus the checks that define acceptable (tests pass, lint clean,
behavior unchanged, policy followed)" (article p.30 step 2). The suite regression-tests the
configuration that steers the agent — `CLAUDE.md`, the skills, the hooks — the way tests
regression-test the code (p.30 step 3).

**This suite starts empty on purpose** (decision 17): the article builds it from "20 to 50
real tasks from recent work" (p.30 step 1), which do not exist on day one. It fills from:
- every incident handled in phase (f): "Each production incident gets an eval ... and stays
  in the suite as a regression test" (p.30 step 5, p.44 step 7);
- every review finding that recurs (the "Things Claude gets wrong" line in `CLAUDE.md` gets an
  eval that proves the correction holds).

## Layout
```
evals/
  README.md          this file
  cases/<id>-<slug>/ one folder per eval, named after the change or incident it came from
    prompt.md        the task as the agent receives it
    checks.yaml      what acceptable means: commands that must exit 0, files that must or
                     must not change, text that must appear in the diff or the answer
    expected/        optional: golden files the checks compare against
```
The runner (`plugin/evals/`, B5) runs every case non-interactively with `claude -p`, applies
the checks, and publishes the pass rate; a change to `CLAUDE.md`, `.claude/**` or the plugin
version that drops the pass rate is reviewed before it merges (p.30 step 4, p.31 governance:
"The pass-rate threshold is enforced as a merge check").

Until the runner exists, a case folder is still worth writing when an incident closes: the
prompt and the checks are the record of what went wrong and what "fixed" means.
