---
type: Proposal
title: The eval suite grows — more triggers, the incident case checked, a first set drafted after twenty changes
description: The project's eval workflow also runs on sdlc.yaml (the pin bump, with the pin read from the pull request's head on such a change, so the bump is evaluated with the new framework before it merges) and on policies/**; gate (e) of an incident change requires its eval case with at least one check; and once the twentieth change has merged, a run drafts eval cases from merged changes in a PR the owner merges. Decision 17 stays and gains that step; a required status check stays not chosen.
status: accepted
roadmap: R35
sources:
  - id: study-entry
    resource: docs/reviews/2026-09-28-playbook-vs-framework/target-design.md
    title: "T13, confirmed at the close of the study on 2026-10-09; from the crosswalk row test-evals (better: the playbook; decision: blend), 2026-10-03; annotation of 2026-10-13 (R15, ArtCraft row A3)"
  - id: crosswalk
    resource: docs/reviews/2026-09-28-playbook-vs-framework/crosswalk.json
    title: "Row test-evals whole; the decision fields of build-config (the brief that quotes the eval result), build-skills (policies/ and the trigger evals) and maintain-learn (T25: the lesson beside T13's eval case)"
  - id: ratchets
    resource: docs/proposals/ratchets.md
    title: "R15 (ArtCraft row A3), accepted 2026-10-13: a dropped eval case is a gate finding and the case count a ratchet the gate counts itself"
  - id: playbook
    resource: docs/reference/ai-native-sdlc-playbook.pdf
    title: "p.29: evals as a live suite that runs whenever the agent's configuration changes; p.30 steps 1-5: 20 to 50 real tasks, the prompt plus the checks, run on a schedule and on any change to CLAUDE.md, skills or hooks, configuration changes gated on the results, an eval for each production incident; p.31: the pass rate a merge check, the time for an incident to become a permanent eval; p.44 step 7 and p.47 step 7: an eval when a fix ships"
  - id: decision-17
    resource: docs/decisions/17.md
    title: "Decision 17: evals after ~20 real changes, an empty evals/ from day one filled by incidents (kept; its trigger gains a step)"
  - id: decision-6
    resource: docs/decisions/6.md
    title: "Decision 6: CI loads hooks from the pinned plugin, never from the PR branch (kept)"
  - id: decision-8
    resource: docs/decisions/8.md
    title: "Decision 8: plugin plus template, the plugin version pinned per project (kept)"
  - id: code
    resource: template/.github/workflows/sdlc-evals.yml
    title: "The evals workflow's triggers, pin step and run step; template/.github/scripts/sdlc_pin.py; plugin/evals/run.py load_case and validate_config; plugin/evals/case.py render_checks; plugin/gate/checks.py lesson_and_eval; plugin/pr/counters.py; plugin/commands/sdlc-deploy.md §0b; template/evals/README.md; read at main 5542406, plugin 1.0.1"
generated: { by: sdlc-framework-session/ccr-01de3f80-ilnomi, at: 2026-10-15T20:00:00Z }
---

# The eval suite grows: more triggers, the incident case checked, a first set drafted after twenty changes

**Status: proposed (roadmap R35), from study entry T13, confirmed by the owner on 2026-10-09; the blend of the crosswalk row test-evals (the row has no option letters).** *[2026-10-20: accepted 2026-10-16 (PR #215)]* Nothing is built. It amends no decision: decision 17 stays (the suite starts empty and fills from incidents) and its "after ~20 real changes" gains a step, so no decision file is written and no number is reserved. It sits in the study's "rest in any order" group; R15 (ArtCraft row A3) already extends the entry (the suite cannot shrink unseen), and R42 (T25) owns the lesson half of the same gate (e) check whose eval half is this proposal's.

## The problem

Decision 17 starts the suite empty and lets incidents fill it, because the article's 20 to 50 real tasks do not exist on day one[^decision-17]. Three gaps remain:

- **New skills and hooks reach a project without its evals running.** A project receives a new framework through its pin bump, a change to `sdlc.yaml`, which is not among the evals workflow's paths. Adding the path is not enough: the workflow reads the pin from the default branch on purpose, so a pin-bump PR would still be evaluated with the old framework.
- **The incident's case is required in name only.** Gate (e) checks that the case's two files exist, not that the case holds a check the runner can run, so an incident can ship with a case that fails in the suite, or with none that asserts anything.
- **Nothing acts on decision 17's own trigger.** Once twenty changes exist, nothing drafts the article's suite from them; the only sources are incidents and recurring review findings.

## What the article says

Evals are "the AI-native equivalent of stage-gate QA": a suite "that runs whenever the agent's configuration changes", kept live, with new cases added "that arise from ongoing monitoring" (p.29)[^playbook]. The platform engineer "collects 20 to 50 real tasks from recent work"; each eval is "the prompt plus the checks that define acceptable"; the suite runs "on a schedule and on any change to CLAUDE.md, skills or hooks"; configuration changes are gated on the results; "each production incident gets an eval ... and stays in the suite as a regression test" (p.30 steps 1-5). "The pass-rate threshold is enforced as a merge check"; the leading indicator includes "how long a production incident takes to become a permanent eval" (p.31). When a fix ships, "add an eval for the incident" (p.44 step 7), and for a security fix "for the vulnerability class" (p.47 step 7).

## What the framework does today

Read at `main` 5542406, plugin 1.0.1. The entry's "Today" was read at 619f01a (0.3.5). `git diff --stat 619f01a 5542406` over the files below changes `plugin/gate/checks.py` (the `lesson_and_eval` check, plugin 0.3.6, change 0003), `plugin/commands/sdlc-deploy.md` (step 0b with it), three lines of `plugin/evals/run.py` (git's auto maintenance turned off in the fixture) and the concurrency group of `.github/workflows/framework-evals.yml`; `sdlc-evals.yml`, `sdlc_pin.py`, `case.py`, `template/evals/README.md`, `counters.py` and decision 17 are unchanged[^code].

- **The triggers.** `sdlc-evals.yml` runs on a pull request to the default branch that changes `CLAUDE.md`, `.claude/**` or `evals/**`, daily at 03:37 UTC and on dispatch (lines 28-37). `sdlc.yaml` and `policies/**` are not among the paths; `policies/` does not exist yet (R27, T1's first part). Verified.
- **The pin comes from the default branch.** The pin step runs the default branch's copy of `sdlc_pin.py` with `--ref refs/remotes/origin/<default branch>` (`sdlc-evals.yml:56-63`), "because the pin is the project's, not the branch's" (`sdlc_pin.py:10-16`, `:26-27`); the framework is checked out at `v<plugin.version>` from the fixed framework repository (`sdlc-evals.yml:65-70`) and the Claude Code CLI at `plugin.claude_code` (`:76-79`). `plugin.version` is not checked against a version pattern (`sdlc_pin.py:147-150`, `:160`); `claude_code` is checked against a character set only (letters, digits, '.', '+', '-', so an npm dist-tag such as `latest` passes; `:54-55`, `:152-158`). Verified.
- **The gap is documented, with a per-project option.** The template's README says a pin bump "is evaluated after its merge, not on its pull request", and names the head's pin for that event as "a decision of the project's owner, not of the template", taken knowing its cost (a branch could pin any older tag), so "a project that takes this route accepts from the head only a pin equal to or newer than the default branch's" (`template/evals/README.md:88-98`); the contract's `sdlc-evals.yml` row says the same (`docs/OPERATING_MODEL.md:95`, §4.2). Verified.
- **What the head already runs.** The project is checked out with no `ref:` (`sdlc-evals.yml:51-54`), so a pull request run reads the PR's files; the head's `commands.setup` runs (`:81-82`), and the suite is started by the head's `evals/check.py` with the Claude credentials in its environment (`:86-90`). The same setup line in eight workflows is folded into R44 (T29) by the owner's choice of 2026-10-14 (`target-design.md`, the dated annotation beside T29's status; `docs/handoffs/sessions/2026-10-14-ccr-20b39ad0-kcymdd.md:105`). That `actions/checkout` defaults to the PR's merge commit is GitHub's documented behaviour, not verified here.
- **Advisory, and green when empty.** A pass rate below `--min-pass-rate` exits 1; an empty suite exits 0 with "no cases" (`plugin/evals/run.py:61-62`, `:737`). No required status check binds the merge and the owner's Exempt bypass would skip one (crosswalk row build-config). The template's README still calls the pass rate "the merge check" (`template/evals/README.md:82-85`); that wording is corrected with the README part in "Order".
- **The incident's case.** Step 0b tells an incident's (e) run to write the skeleton with `case.py new` and complete `checks.yaml` so it "asserts the property the fix restored"; "a case that asserts nothing real is worse than none" (`plugin/commands/sdlc-deploy.md:94-99`). Gate (e)'s `lesson_and_eval` fails when `evals/cases/<id>-<slug>/prompt.md` or `checks.yaml` is missing (`plugin/gate/checks.py:1665-1669`) and reads nothing inside them. The runner is stricter: `load_case` fails a case whose prompt is empty or whose `checks.yaml` does not validate (`run.py:168-189`), and `validate_config` requires `checks` to be a non-empty list of valid checks (`run.py:245-249`). The skeleton for a project with no `commands.test` holds only commented-out checks (`case.py:154-160`): verified by command, `render_checks('0007', 'x', '')` parses to `checks: None` and `validate_config` returns `['checks must be a non-empty list']`, while gate (e) would pass it. Exercised live once in this repository: change 0002, a scan incident whose case holds two checks, passed the check (`changes/0002-security-authz-the-guardrail-self-protec/evidence/gate-e.json:169-171`).
- **Twenty changes.** Decision 17's "after ~20 real changes exist" names a trigger nothing acts on; the README names incidents and recurring review findings as the suite's sources (`template/evals/README.md:11-18`). The digest's counters already count the changes merged at gate (e), abandoned ones excluded and incidents included: "a change at phase e on the default branch was merged by the owner" (`plugin/pr/counters.py:32`, `:44-55`, `:98`). Change 0000 stays at phase a and is not counted. Verified.
- **The framework's own suite.** Skill and hook changes are tested in this repository by `framework-evals.yml` on `plugin/**`, `template/**` and `evals/**` (lines 12-21), on each plugin pull request, not on a project's pin bump.
- **R15 (accepted, not built).** A dropped eval case will be a gate finding, and the gate will count the cases as a ratchet; its first change, 0005, waits at gate (b) (`changes/0005-dropped-tests-and-eval-cases-are-gate-fi/status.yaml`).

## The proposal

Decision 17 stays: the suite starts empty and fills from incidents. A required status check stays not chosen (build-config). The owner's three additions, then where the result reaches the owner:

1. **More triggers.** `sdlc-evals.yml` also runs on pull requests that change `sdlc.yaml`, the pin bump through which new skills and hooks reach the project, and `policies/**`, the owner's policy sources (build-skills; the folder arrives with R27). On a pull request that changes `sdlc.yaml`, this workflow reads the pin from the pull request's head, so the bump is evaluated with the new framework before it merges: an exception to the "pin from the default branch" rule. The scheduled run keeps the default branch's pin.
2. **The incident case is checked.** Gate (e) of an incident change fails without its case under `evals/cases/<id>-<slug>/` holding at least one check. Today's instruction becomes a gate check; the case's quality stays the review pass's to judge.
3. **A first set after twenty changes.** Decision 17's "after ~20 real changes" gets a step: once the twentieth change has merged, a run drafts eval cases from merged changes (the intent as the prompt, the change's own tests and files as the checks) and opens a PR the owner merges. The article's platform engineer becomes a run, and the owner's merge decides which cases join the suite.
4. **Where the result reaches the owner.** Not as a required status check, which the owner's Exempt bypass would skip, but in the role brief on the owner's own guardrail and skill PRs, which quotes the pass rate, the failing cases, or "no cases yet" (build-config; R28, T1's second part).

## How it is judged

On the sample project and the next project. The owner's next pin-bump PR starts an evals run whose pin step prints the head's version, and the run's verdict is on the PR before the merge. The next incident change whose case has no valid check parks at gate (e) with the problem named, and one with a valid case passes; the incident's case is then part of the same build PR, which is the article's "how long a production incident takes to become a permanent eval" (p.31). Once the digest's "Shipped" counter reaches 20, one draft PR appears with its cases and what each checks. The failures: an owner's pin bump merged without an evals run on the new framework; an incident case the runner cannot load passing gate (e); a twentieth merged change with no draft.

## What to settle before building

| Question | Recommended |
|---|---|
| How the PR-head pin is read safely (the entry's open item) | Mine: only on a pull request whose author is the owner, by R17's owner rule (the repository owner, or `sdlc.yaml: owner` on an organization repository, one shared function); any other PR, and every scheduled or dispatched run, keeps the default branch's pin, and every other workflow keeps it too. The head's pin brings the Claude Code version it names as well (the pin step emits `claude_code` from the same block, `sdlc_pin.py:160`). The head's `plugin.version` must match `v?<major>.<minor>.<patch>` before it reaches `actions/checkout` (today it is unchecked, `sdlc_pin.py:147-150`), and must be equal to or newer than the default branch's, the condition the README already sets for this route (`template/evals/README.md:97-98`). The pin step still runs the default branch's copy of `sdlc_pin.py`, only its `--ref` changes to the head's commit. The head already chooses the setup command and `evals/check.py` that run in this job (`sdlc-evals.yml:81-90`); the setup command is R44's (T29, the owner's choice of 2026-10-14), and `evals/check.py` is settled two rows below |
| Whether the head pin touches decision 6 ("CI loads hooks from the pinned plugin, never from the PR branch") | Mine: no. The hooks still come from a tagged release of the fixed framework repository; the head names which release, in an `sdlc.yaml` the owner wrote. The owner judges whether that reading holds |
| Which code starts the suite with the model credential (R44 covers the head's setup command, not `evals/check.py`, and the new paths widen the pull requests that reach it) | Mine: the run step calls the pinned framework's runner itself, `python framework/plugin/evals/run.py --root . --plugin-dir framework`, the command `evals/check.py` builds (`template/evals/check.py:64-86`), so on every trigger the code that starts the suite with the credential comes from the pinned release, not from the head; `evals/check.py` stays the project's local entry point. The head's `CLAUDE.md`, hooks and cases still run in each case's `claude -p` call with the credential (`run.py:20-36`): that is what the suite tests (p.30). A pull request the workflow token opens starts that run only after a person approves it (`docs/notes/11.md` §11a). Whether a head's hooks or a case's `setup` should run without the credential is not proposed here |
| Whether `REVIEW.md` joins the paths (R28's Platform & release brief, which runs after this workflow, also covers the owner's `REVIEW.md` PRs) | Mine: no; the owner's note names `sdlc.yaml` and `policies/**` only. No case runs the review pass: a case is one `claude -p` task (`run.py:27-31`), so a run on a `REVIEW.md` PR would test nothing that file changes. The brief on such a PR says "no review-pass case", as R38 (T16) settles for its tuning PR. A review-pass case, which R38 leaves to this proposal, is not proposed here; the owner may ask for it later |
| What counts as "a real check" for the incident case, deterministically (the entry's open item; also the ArtCraft A3 revision's finding at `checks.py:1667-1669`) | Mine: the case loads in the runner: `lesson_and_eval` calls `plugin/evals/run.py` `load_case` and fails on any `error` (an empty prompt, no checks, an invalid check), so the gate and the suite apply one rule. The skeleton's test-command check alone counts; whether it asserts the incident is the review pass's to judge, as the owner's note says |
| How the twentieth change is counted (the entry's open item) | Mine: `counters.py`'s "Shipped (merged at gate (e))" count over the default branch, abandoned changes excluded, incident changes included (each is a real merged change), change 0000 not counted (it stays at phase a). To verify on the sample that a change's `status.yaml` reads phase e on the default branch only after its build PR merged |
| Whether the draft run repeats later (the entry's open item) | Mine: once, by itself, when the count first reaches 20 with no earlier draft (the draft PR's branch or a marker in `evals/` records it); after that only on the owner's dispatch. The incidents keep filling the suite (decision 17), and the article's "new ones ... from ongoing monitoring" (p.29) is that route |
| Where the draft run lives and what it may write | Mine: a step the scheduled evals run starts when the count is reached, dispatching the draft job explicitly (events of the workflow token start no run); the session reads the merged changes and writes under `evals/cases/` only, on a branch of its own, and opens the PR. Today the workflow holds `contents: read` and its header says it "starts nothing and writes nothing" (`sdlc-evals.yml:17-18`, `:39-40`): the scheduled job gains `actions: write` for the dispatch (or the draft job is a workflow of its own on its own schedule), the draft job holds `contents: write` and `pull-requests: write`, and the header comment changes with it. The skeletons come from `case.py`, extended from incidents to any merged change. Once R22 (T18) is built, its ruleset 2 holds every pull request without a passing `sdlc/review`, and a PR the workflow token opens starts no run that posts one; so the draft job posts the passing "not a build PR" `sdlc/review` on each head it pushes, as R22 asks of each step that opens an automation PR (`gate-e-approving-review.md`, point 5), and holds `checks: write` for it. R22's list of those steps does not name this job yet |
| How a drafted case is not passed by the code already merged | Mine: a drafted case's `setup` restores the files the change touched to their state before the change (the workspace carries `.git`, `run.py:22-23`), keeping the change's tests as the checks; the run executes each drafted case once and the PR body lists each case's result. A case that cannot be made to fail without the change is left out and named in the PR body. To verify on the sample |
| How the owner keeps some drafted cases and not others | Mine: the PR body lists each case with what it checks; the owner deletes a case's folder in the PR before merging, or closes the PR. The PR's "What you can do here" block is R19's. The draft PR gets no review pass: R36 (T14) gives the pass to the runbook PRs only and keeps every other PR as it is (`runbook-prs-reviewed.md`, point 3), and here the owner's merge is itself the choice of each case, read in the PR body with its result |
| The draft PR's evals run | Mine: a PR opened with the workflow token starts no `pull_request` run, so the draft job runs the cases itself (above) and the PR shows that run's report; no extra dispatch |
| The daily run's spend once the suite holds 20 or more cases | Mine: unchanged, daily (the owner's weights put cost at 0); the spend is visible where R25 (T30) shows it |
| The workflow's name (the entry's open item) | Judged with R45 (T4); `sdlc-agent-evals.yml` is the entry's placeholder |

## Considered and not chosen

- **A required status check on the eval result** (the article's merge check, p.31): the owner's Exempt bypass on the ruleset would skip it (build-config); the result reaches the owner in the role brief instead.
- **The `sdlc.yaml` trigger alone, with the pin still read from the default branch**: a pin-bump PR would still be evaluated with the old framework, so the run would say nothing about the bump.
- **The head pin as each project owner's own edit** (today's route, `template/evals/README.md:93-98`): the owner's choice puts the head pin in the template's `sdlc-evals.yml`, so every project has it rather than only those whose owner edits the workflow.
- **Seeding the suite on day one, or skipping evals**: decision 17's other options, settled; the suite starts empty and fills from incidents.
- **The incident case's quality as a gate check**: a deterministic gate can tell that a case loads and holds a check, not that it asserts the incident; that stays the review pass's.

## Decisions it touches

None amended, so no decision file is written and no number is reserved. Decision 17 is kept and gains a step for the trigger it already names ("after ~20 real changes"); its incident route is unchanged. Decision 6 is kept: the hooks come from a pinned framework release, never from the PR branch's files (the reading in "What to settle" is the owner's to confirm). Decision 8 is kept: the pin stays per project, and the head is read only to evaluate a proposed pin before it merges. Decision 4 is kept: its ruleset, with the Exempt bypass mode `/sdlc-init` §6 sets (`plugin/commands/sdlc-init.md:133-136`), is why no required status check is added. Decisions 11 and 20 are kept: a failed gate (e) check parks, and the draft is a PR the owner finds in the digest, never a notification. Decisions 27, 28 and 29 do not touch it.

## Order

In the study's "rest in any order" group (the record, section 8). It changes `template/` and `plugin/`, so it ships as a plugin version with tests and reaches a project through `/sdlc-init`'s workflow copies. The parts it takes:

| Part | Where | When |
|---|---|---|
| `sdlc.yaml` among the paths, the head pin on the owner's PR, the version check, the run step calling the pinned runner | `template/.github/workflows/sdlc-evals.yml`, `template/.github/scripts/sdlc_pin.py` | Now; the owner check is R17's shared function, or a coarse `if:` until R17 is built |
| The documentation the head pin makes false | `template/evals/README.md` (the pin-bump paragraph, `:88-98`, and "the merge check", `:82-85`), `docs/OPERATING_MODEL.md` §4.2 (the `sdlc-evals.yml` row, `:95`) | With the head pin |
| `policies/**` among the paths | `sdlc-evals.yml` | With R27, which creates the folder (a path that matches nothing starts nothing, so it may also go in now) |
| The case loads at gate (e) | `plugin/gate/checks.py` `lesson_and_eval`, `plugin/evals/run.py` | Now; the same function R42 (T25) touches for the lesson half, so whichever is built second rebases on the first |
| The draft run after twenty changes | `plugin/evals/case.py`, a job beside `sdlc-evals.yml`, `template/evals/README.md` | After the parts above; its PR block with R19, its passing `sdlc/review` with R22, its name with R45 |
| The eval result in the role brief | R28 (T1's second part) | With R28 |
| The drafted and incident cases protected from a silent drop | R15 | With R15, already accepted |

[^decision-17]: `docs/decisions/17.md`.
[^playbook]: `docs/reference/ai-native-sdlc-playbook.pdf` p.29-31, p.44, p.47.
[^code]: `template/.github/workflows/sdlc-evals.yml:17-18`, `:28-37`, `:39-40`, `:51-54`, `:56-63`, `:65-70`, `:76-79`, `:81-90`; `template/.github/scripts/sdlc_pin.py:10-16`, `:26-27`, `:54-55`, `:147-160`; `plugin/evals/run.py:20-36`, `:61-62`, `:168-189`, `:245-249`, `:737`; `plugin/evals/case.py:154-160`; `template/evals/check.py:64-86`; `plugin/gate/checks.py:1665-1669`; `plugin/commands/sdlc-deploy.md:94-99`; `plugin/pr/counters.py:32`, `:44-55`, `:98`; `template/evals/README.md:11-18`, `:82-98`; `docs/OPERATING_MODEL.md:95`; `plugin/commands/sdlc-init.md:133-136`; `.github/workflows/framework-evals.yml:12-21`; all at `main` 5542406.
