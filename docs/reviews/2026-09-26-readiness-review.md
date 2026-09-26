# The 1.0.0 readiness review (session 9, 2026-09-26)

The owner asked whether the framework was ready to be tagged 1.0.0 and for every mistake, inconsistency and divergence from the goal to be found first. Three passes ran, all fresh-context sub-agents, none editing a file:

1. **Seven slice reviewers** (Opus), one per slice: the plan and the contract (BUILD_GUIDE, DECISIONS, OPERATING_MODEL, the article's citations); the session records (PROGRESS, NOTES, ROADMAP, HANDOFF, README); the gate, state and panel code; the CI, detect, scan and hook code; the commands, skills, agents and templates; the sample repository; the test suite and the eval cases.
2. **Two independent passes over the consolidated findings**: a verifier (Fable 5.1) that re-derived each item from the code and reproduced it where it could, and a contrarian (Opus 5.5) whose brief was to knock each item down (a misread guard, a known and accepted gap, threat-model overreach, a stale line that is right in context).
3. **An adjudicator** (Fable 5.1) over both, ruling per item on the primary source and on the contract's own promises, not a stricter threat model.

The session then reproduced the six items ruled *must fix* by hand before building them. This page is the record the follow-up sessions work from; each group below is one session (`HANDOFF.md`).

## The verdict on 1.0.0

Not reached, by the repository's own criteria (`docs/ROADMAP.md`, "Milestone 1" and "The path to 1.0.0"): the first real detection on the sample is owed (two of sixteen daily `CI` points existed on 2026-09-26; the earliest judging run is 2026-10-11), every row of the path table was undone, the sample ran the 0.2.23 workflow copies while pinning 0.2.24, and the 0.2.24 live checks were owed. All three passes agreed.

What the second pass changed: the contrarian knocked down about half of the first pass, and the adjudicator sided with it on the largest item — the confidence gate running inside the session and writing `evidence/gate-<phase>.json` is the design (OPERATING_MODEL §4.1, PROGRESS session 5, decision 18), not a defect; only the sub-parts that break an explicit promise survived. The first pass also carried three factual errors, corrected here: sub-step 26.5 *is* recorded as not built (PROGRESS session 5); DECISIONS.md's line on Lite is the withdrawal amendment, not stale text; the branch ruleset is decision 4, not "only in NOTES". The contrarian strengthened one finding: this repository's own `main` had no branch protection and no ruleset (read through the GitHub API, unauthenticated), while the sample's `main` has a classic protection rule.

## Fixed in this session — plugin 0.2.25 (a test each; `docs/PROGRESS.md` session 9 has the table)

| # | Defect | Where | Promise it broke |
|---|---|---|---|
| 1 | `/sdlc-init` step 5 committed neither `.github/` nor `lessons/`: a project set up by the book merged with no workflows and no pin script | `plugin/commands/sdlc-init.md` | §8 layer (i): the install's output rides in the change-0000 PR |
| 2 | The hooks read their JSON input in text mode; on Windows (cp1252) a project path with an accented letter matched no protected path and the guardrail edit was allowed; `review/cli.py prompt`, `panel/cli.py prompt` and `pr/cli.py description` crashed on `≠` / `→` under a cp1252 pipe | `plugin/hooks/_common.py`, the three CLIs | decision 6, §8: "the hook has no exception" |
| 3 | Nothing in the gate read `tests_locked`: a run that set it to false, turned the fix into a feature or ran `unlock-tests` itself edited the frozen tests unnoticed | `plugin/gate/checks.py` `owner_actions` | §6, §8: "only the owner unlocks"; the actor re-judged |
| 4 | The CI guard read `paused` and `profile` from the checkout after `prepare_branch` had switched to the work branch: a pause merged on `main` stopped nothing in flight | `plugin/ci/run_phase.py` `guard` → `_approved_config` | §4.2: the guard reads the "base branch copy of `sdlc.yaml`" |
| 5 | `SDLC_DEFAULT_BRANCH` was set on the pin step only; a project whose default branch is neither `main` nor `master` parked at every gate ("no base branch") | the phase-run steps of `sdlc-design/build/test/deploy/fix/detect.yml` | §1: any GitHub-hosted project |
| 6 | Decision 4's ruleset was never prescribed or checked; this repository's `main` was unprotected | `plugin/commands/sdlc-init.md` §6, `pr/github.py default_branch_protection`, the digest's notice | §2: only the owner merges |

## Group A — the gate and `status.yaml` (session 10)

Real defects with a small blast radius; each breaks a stated rule or fails open. File:line as read at commit 5275171.

- `owner_actions` believes a recorded `risk_accepted_by` actor that is any non-bot string (`plugin/gate/checks.py:853-858`): a run can write a person's login itself. The same for `tests_unlocked_by` since 0.2.25 judges the lift (the review of the 0.2.25 diff, finding M1: a lift the run records under the owner's login passes; the `test_lock` check of 0.2.25 covers the other form, a test changed while the lock stands). The runner applied the labels (`run_phase.py:1153`) and can re-verify the recorded actor against the label event after the session.
- `panel_calls` reset by the run is not judged (`checks.py:939-948` judges `iterations` only); OPERATING_MODEL §6 says the label resets "the fix-iteration and panel-call counts".
- `profile_override` and `review_override` are read from the branch's `status.yaml` (`gate/gate.py:312-316`, `run_phase.py:798`): the Full profile's (c)/(d) human gates are skipped by a branch that writes `profile_override: standard`. Read them from the base branch's copy, as `intent.md` is.
- Gate (a) has no `design_scope` check (`checks.py:1228`) though §4.2 says the fix round at (a) is refused a source file by it.
- One panel ledger line closes several concerns; `by_n` is not consumed per closing (`checks.py:1017-1035`).
- A severity `"Important "` with a trailing space passes validation and the tally but not `important_findings` (`checks.py:389-394`: `lower()` without `strip()`).
- `owner_actions` judges the newest risk-gaining commit only (`checks.py:920`): an earlier self-acceptance is laundered by the owner's later acceptance of another item.
- `yes` / `on` in `sdlc.yaml` are strings to `yamlish` (YAML 1.2, correct) and every reader tests `is True` (`gate/limits.py:118`, `gate/preflight.py:237`, `run_phase.py:740`, `hooks/production_gate.py:325`): `deploy.production: yes` turns the release approval and the hook off, `paused: yes` does not pause. Fail closed on a non-boolean.
- The digest's counters count the abandoned rehearsal 0005 as an incident merged (`pr/counters.py:36-48` reads the default branch's `status.yaml`, where an abandon is never written; `detect/cli.py open_incidents` already excludes the remote-abandoned ids).
- `/sdlc-deploy.md:154-156` re-runs `validate` only after the panel's commit moves HEAD; `validate` does not re-review, so gate (e) refuses the stale findings (fails closed, wastes a round); the text names a diff file and a verdict file phase (e) has no step for.

## Group B — CI, release and detect (session 11)

- The release approval is found by the current branch's *name*, merged PRs included (`plugin/release/approval.py:147-166`, `find_pr(..., state="all")`), and `sdlc:release-approved` is never removed: a session that checks out `sdlc/<old id>/c` inherits that change's approval. Tie the approval to the change (the PR number recorded in `status.yaml`, or the merge sha) and to an open or just-merged PR. Reachable by hand with a production credential only (CI holds no deploy secret).
- The production gate's command matching misses ordinary spellings: `terraform -chdir=x apply`, `kubectl --context p apply`, `/usr/local/bin/twine upload`, `twine.exe`, `npm.cmd` (`plugin/hooks/production_gate.py`, `guarded()`).
- `detect/runbooks.py:130-135` reads the default branch through the short `origin/<default>` (a tag of that name shadows it: the class 0.2.24 fixed in the pin script); a runbook reuses a local `sdlc/<id>/revert-*` or `quarantine` branch the session could have planted (`:153`).
- `detect/cli.py finish` (the step holding the runbook secrets) reads `evidence/detection.json` from the shared checkout (`cli.py:643-647`): a session with `Write` and `Bash(git *)` (`:75`) edits tier 2 to 3 and a pre-approved runbook runs. PROGRESS session 8 names the class ("the shared checkout"); the fix is a snapshot the detect step takes before the session starts, judged by `finish`.
- The gate's diff checks pass on an empty file list when the base and HEAD have no merge base (`gate/diff.py:245-247`); fail closed.
- `sdlc-tag.yml` has `workflow_dispatch` with no ref guard and `sdlc_tag.py` tags HEAD once, never moved: an honest dispatch on a branch tags unmerged code for good. Refuse a ref that is not the default branch.
- A closed (rejected) `sdlc/<id>/dismiss` PR keeps suppressing the finding while its branch exists (`detect/cli.py:350-374`); `_closing_reason` (`:1237-1255`) takes any person's comment with no `author_association` filter.
- `sdlc-design.md:50-51` and `sdlc-build.md:46` tell a by-hand re-run to read the PR's comments without the membership filter `/sdlc-fix` step 1 has (in CI `rerun_reason`, `run_phase.py:709-735`, refuses a re-run while an open PR carries the branch, so the prose is the whole exposure).

## Group C — the test and eval infrastructure (session 12)

- No CI job runs this repository's `pytest` or `ruff`: `framework-evals.yml` installs pytest for the fixture only. PROGRESS session 3 says "the CI job of PR A is the check" — there is no such job. The Windows-only code (`plugin/evals/run.py:295-298,313-314`, `release/cli.py:120-121`, the `.cmd` launchers) last ran under 657 tests; there are 1196. Add a workflow on `pull_request` and `push` to `main`: `python tasks.py check` on `ubuntu-latest` and `windows-latest`.
- Eval case 0003's HTML "Eval note" is sent to the model verbatim (`plugin/evals/run.py:159` reads `prompt.md` whole) and says that declining passes. Strip an HTML comment at the top of a prompt in the runner, with a test; move the note to `checks.yaml`.
- No eval case would fail if the plugin's hooks stopped loading: 0001 and 0003 pass when the agent declines on its own (the outcome-only design the cases document), 0004's `\d+ passed` regex matches the example in its own prompt. Add one case whose check reads the hook log for the deny line (`evidence/hook-log.jsonl`, §8), and tighten 0004's regex to the run's own line.
- `template/evals/README.md` says the evals workflow covers "the plugin version"; `sdlc-evals.yml` does not trigger on `sdlc.yaml` and its pin step reads the default branch's copy, so a PR that bumps the pin is evaluated against the old plugin. Say so, or add `sdlc.yaml` to the trigger with the head's pin for that event only.

## Group D — the documentation pass (session 13)

- "Decision 11: a run cannot approve itself" cites the wrong decision (11 is park-never-page; 5 is the automation identity): OPERATING_MODEL §4 (the release approval) and §4.1, `plugin/hooks/production_gate.py` (the block message, lines 12 and 294), `template/sdlc.yaml` (lines 50, 95, 108 — copied into every project), `plugin/gate/checks.py` `OWNER_ACTIONS_NEED`, PROGRESS session 4.
- ROADMAP criterion 1 ("Every step built") omits step 31 (decided, not built; its own row in the leftovers table) and sub-step 26.5 (monthly tuning; PROGRESS session 5 "not built"); the Milestone section names one blocker where the path table and HANDOFF name four; PROGRESS session 8's "shared checkout" gap is in "Known gaps" but in no roadmap row.
- OPERATING_MODEL §3 / §4.1: one sentence that the (c) and (d) gates are the run's own check, reviewed by the owner at (e) (the design the adjudicator upheld); §3 that `plan_sync`, `open_concerns`, `artifacts` and `panel` read the working tree by design (the evidence commit lands it); §4.2 permissions rule lists five scopes while the detect, runbook, scan and abandon jobs declare fewer (least privilege; the rule text is off); §4.1 (e) and §4.2 disagree on whether the review pass runs before or after the release artifact (PROGRESS session 4 records the order built).
- BUILD_GUIDE.md and `docs/build_guide.json` still describe Lite as current in sixteen lines (the step 9a title among them) and step 33's note contradicts itself ("Built … not built"); step 29's note still offers a signed tag as approval (rejected in OPERATING_MODEL §4); step 16a's notes name `decided-by: panel`, a `.md` ledger and "three claude -p runs" (the panel runs as sub-agents, choice 52); OPERATING_MODEL §9 cites p.40 "step 5" for the tools (it is step 4).
- `template/sdlc.yaml` tells the owner to accept a risk with the CLI (decision 24 made the label the verb; the CLI stays for by-hand runs — say both), says "Bands and the 3-sigma tiers arrive in B5", and its `# --- automation identity (decision 11 …)` comment; the root `sdlc.yaml` line 8 still describes `lite` (the owner's edit, PROGRESS session 7).
- README: the pack row says "(now: session 8 …)"; the tool list leaves out `detect/cli.py`, `scan/cli.py`, `evals/run.py`, `init/sdlc_init.py`, `ci/project_setup.py`, `pr/counters.py`; "(after B3)" on the plugin line.
- MODEL_ALLOCATION: session 6's figures disagree with PROGRESS (two scans, D2 folded into D1); no entries for sessions 9 and later.
- The flat-baseline premise of the session-10 plan (HANDOFF "mean 0, sigma 0", ROADMAP row 9, NOTES §16): the sample's `CI` run 36257154359 (a `pull_request` run by the owner, 2026-09-26 16:54 UTC, a failed install on placeholder pins) is a counted failure inside the baseline. The verifier's simulation through `stats.evaluate` still files tier 3 by `we1` (about 19σ: mean 0.0089, sigma 0.025), so the plan holds and its wording does not.
- The sample's project files `changes/README.md`, `evals/README.md` and the `sdlc.yaml` comments are 0.2.0-era; `/sdlc-init` writes them create-only by design and never says they are outdated. Say so in `/sdlc-init`'s report, or list them as `outdated` beside the workflows.
- `docs/owner-machine/README.md` quotes OPERATING_MODEL on a "user-level" managed settings file; the model now says "system path" (decision 6 still says user-level).

## Ruled not a problem (with the reason, so nobody reopens them)

- The in-session gate and the runner dispatching from `evidence/gate-<phase>.json`: the design (OPERATING_MODEL §4.1, PROGRESS session 5 "the record is what the run committed", decision 18); the runner keeps its own guards (`guardrail_changes` by the merge base's intent, the preflight, the label actor) and the owner's merge at (e) is the human gate in every profile.
- `id: '0000'` in `status.yaml` skipping the gate's `guardrails` check: the runner's guard judges the branch by the merge base's `intent.md`, not `status.id`.
- `--base HEAD~0`, a tag named `origin/main` inside the session, an emptied diff by the session's own git: in-session tricks the design does not defend against.
- `open_concerns` reading the branch's spec: the panel closes concerns on the branch by design (`panel/ledger.py`), and the `panel` check ties every closing to a ledger line; an overturn not reopening: the owner's words replace the panel's (`/sdlc-fix` step).
- The CI review pass before the release artifact: recorded in PROGRESS session 4; the sample runs `deploy.action: none`.
- The Full-profile label check without a token: PROGRESS session 4 accepts the degradation; in CI the token is always set.
- Precondition 0 "unmarked": the sample's `ci.yml` schedule landed (PR #41) after the docs were written; ROADMAP says sessions mark rows.
- `status.yaml` on the sample's `main` reading 0001 as parked and 0005 as waiting at (f): gate (e) is derived from the merge and an abandon is written to branches only (OPERATING_MODEL §4). Do not prune the sample's `sdlc/0005/*` branches: they are what marks the rehearsal abandoned; without them `open_incidents` counts it open and the first real detection files nothing.
- The sample at the 0.2.23 copies: HANDOFF precondition 3, planned.
- `max_budget_usd` per change: OPERATING_MODEL §4.1 already says it binds unattended runs only; the "per change" wording of `template/sdlc.yaml` and `gate/limits.py` is group D's.
- `panel_advocate_model` read by no code: the command text tells the model which alias to name; change 0002's panel did run on two models. Group D records that it is prose-enforced.
