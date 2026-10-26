---
type: Proposal
title: A failed CI run explains itself, and the release notes gain a plain-words paragraph beside the deterministic list
description: The existing read-only triage step runs on always() in the phase and fix workflows, reads the failed step's saved log or the parked gate's logs, says what failed, the likely cause and whether it looks flaky or real, and puts its lines, labelled model-written, into the park block on the PR or into a "Failed runs" line of the daily digest, fed by a record each failed run writes and by the Actions API for jobs where no step ran; the release notes stay deterministic and gain a model-written paragraph, kept on a re-run unless the code changed.
status: accepted
roadmap: R18
sources:
  - id: study-entry
    resource: docs/reviews/2026-09-28-playbook-vs-framework/target-design.md
    title: "T19, confirmed at the close of the study on 2026-10-09; from the crosswalk row deploy-ci (better: the playbook; decision: blend, option C), 2026-10-07"
  - id: crosswalk
    resource: docs/reviews/2026-09-28-playbook-vs-framework/crosswalk.json
    title: "Row deploy-ci: the article's read-only judgment steps against the framework's; rows test-loop and test-verify (T10), deploy-release (T21), deploy-approve (T18), x-headless, maintain-detect (T22), decision fields only"
  - id: playbook
    resource: docs/reference/ai-native-sdlc-playbook.pdf
    title: "p.40: start with read-only judgment steps (triage a failed build, summarize a flaky test, draft the changelog); p.41: the triage pipeline step and the leading indicator"
  - id: decision-11
    resource: docs/decisions/11.md
    title: "Decision 11: park, never page (as amended by 21 and 29)"
  - id: decision-20
    resource: docs/decisions/20.md
    title: "Decision 20: the queue and the daily digest, pull not push"
  - id: decision-29
    resource: docs/decisions/29.md
    title: "Decision 29: in CI a red target starts the next fix round by itself; a timeout starts a round, an infrastructure failure gets one re-run then parks, a missing target parks at once"
  - id: code
    resource: plugin/ci/run_phase.py
    title: "run_triage, TRIAGE_ALLOWED_TOOLS, commands_env, park_deferred_record, report_failed_run, hand_over, main; plugin/gate/gate.py write_deferred_logs; plugin/release/notes.py; plugin/pr/digest.py; the workflow templates; read at main acefc7e, plugin 1.0.0"
generated: { by: sdlc-framework-session/ccr-20b39ad0-kcymdd, at: 2026-10-14T15:30:00Z }
---

# A failed CI run explains itself

**Status: proposed (roadmap R18), from study entry T19, confirmed by the owner on 2026-10-09.** *[2026-10-20: accepted 2026-10-14 (PR #208)]* Nothing is built. *[2026-10-23: built in plugin 1.0.36, the parts this file's "Order" marks "now"; the record `docs/progress/2026-10-23-claude-r18-failed-run-explains-itself.md` lists where the build departs from the text below, which was read at plugin 1.0.0: the record writer pushes with the job's token through git's command-scope config, since no checkout persists a credential (decision 33); the digest already held `actions: read` (choice 250); a failed setup writes its JSON to `--out` and keeps the job red instead of `continue-on-error`; the triage session's result is stored as `evidence/claude-triage.json`, which the budget reads since R25.]* It defines the digest's "Failed runs" line and its sources, which R13 (T21), T20, T22, T26 and R20 (T28) feed or place; its merge-workflow part arrives with T18. The owner chose option C of the row deploy-ci: the triage step wired (B) plus a model-written paragraph in the release notes.

## The problem

When a CI run of the framework fails, the owner gets a red run in Actions and a job log. Nothing says in a sentence what failed or whether it looks flaky or real, and nothing the owner reads daily lists the run:

- **A red run with no park shows nowhere the owner looks.** A failed setup ends the run red with no park; a session that exits non-zero, overruns its wall clock or never reaches its gate ends red with its result and stderr committed on the work branch, parked only when its gate record was still deferred (`run_phase.py:1816-1827`, `:1862-1869`); a pull request that cannot be opened or a record that cannot be pushed ends red (`:1926-1930`, `:1956-1960`). The daily digest lists the open `sdlc:` PRs, the incident PRs and the counters, never a failed run (`plugin/pr/digest.py:128-150`).
- **A park says what failed, not why.** The "What I need from you" block quotes the failed check's reason and its "what I need" sentence (`plugin/gate/gate.py:68-82`). Today a red target parks at once (R10 is unbuilt); after R10 it parks only at the iteration cap, after T30's one judged reset, and the owner meets a change that used up its rounds, with the logs in `evidence/` and no cause in plain words.
- **The triage step exists and nothing runs it.** `run_phase.py --phase triage --log <file>` composes a read-only session: the Read tool only, Edit, Write and Bash denied, at most five lines on what failed, the likely cause and the first thing to check (`:201-206`, `:1572-1597`; `tests/test_ci.py:246-258`). No workflow template names it (grep over `template/.github/workflows/`: no hit).
- **The release notes say what was intended.** Their "What changed" is the intent's first outcome sentence (`plugin/release/notes.py:177`), then the commits, the evidence line, the findings tally and the links. Nothing says in plain words what the change did.

## What the article says

The platform engineer "starts with read-only judgment steps. Use `claude -p` in a pipeline job to triage a failed build, summarize a flaky test, or draft the changelog"; write steps come later, behind the existing gates (p.40)[^playbook]. The example is a step on `if: failure()` that reads the build log, identifies the most likely cause, says "whether the failure looks flaky or real" and writes a three-line summary for the PR thread (p.41). The leading indicator is "the share of pipeline failures triaged without paging a human" (p.41). Agent jobs hold no production credentials (p.40, step 3).

## What the framework does today

Read at `main` acefc7e, plugin 1.0.0. The entry's "Today" was read at 619f01a (0.3.5)[^crosswalk]. Since then `run_phase.py` changed in no function this cites (`git diff 619f01a acefc7e`: `run_phase`, `fix_branch_for`, `dispatch_head`, `ci_settings_file`, `session_push_mismatches`, `work_branch_for`, `change_refs` and their helpers), so every region cited here holds; `notes.py` changed only in `_first_sentence` (1.0.0, item 11's G1, commits e0d1768 and 2dbcf0f); the workflow templates, `gate.py`, `digest.py` and `sdlc-deploy.md` are unchanged in what this cites.

- **Three read-only judgment jobs run in CI**: the weekly security review (`sdlc-scan.yml`), the 2σ/3σ diagnosis, whose tools include `Bash(gh run view *)` (`template/bands.yaml:25`, `plugin/detect/cli.py:75`), and the REVIEW.md pass, read-only but for its findings file (`REVIEW_ALLOWED_TOOLS`, `run_phase.py:193`; decision 12). The triage step is the fourth, never wired.
- **What `run_triage` does** (`:1572-1597`): needs `--log`, skips with no model credential, composes with the triage tools, prints the session's text, exits 1 when the CLI failed. `main` routes `--phase triage` to it first (`:2850-2854`) with `env = dict(os.environ)`, the job's whole environment; `invoke` passes it through `auth_mod.credential_env`, which keeps one model credential and everything else, the GitHub token included (`:1253-1262`; `plugin/ci/auth.py:72-76`). `commands_env` is the precedent for narrowing: the commands step runs without the model credentials, `GITHUB_TOKEN` and `GH_TOKEN` (`:1400-1407`).
- **What a failed run already saves.** The session's result `evidence/claude-<phase>.json` and its stderr (`:210-211`; `store_result`, `store_stderr`, `:1450-1469`); on a failure `report_failed_run` prints the counters, the last message and the stderr to the job log and commits both files on the work branch (`:1472-1498`). A wall-clock overrun is caught inside the step (`invoke`, exit 124, `:1265-1266`) and goes the same way. The commands step writes the three target logs under `evidence/` from its own run (`gate.py:344-376`, `write_deferred_logs`), so a red target's output is a file. The project's setup runs in a workflow step before the runner (`project_setup.py --root .`, `sdlc-deploy.yml:94-95`), which prints its JSON and writes `error=` to `$GITHUB_OUTPUT` (`plugin/ci/project_setup.py:198-205`); when it fails, the job is red there and no runner JSON exists. The runner's own install is the no-op second pass (`:1620-1625`), whose failure emits the whole setup dict. `sdlc-runbook.yml:91-114` already handles a failed setup step with `continue-on-error` and `steps.setup.outcome`. Not a file anywhere: a step before the runner (a checkout, the CLI install) and the runner's own JSON, printed to stdout only (`_emit`, `:231`), and on two exit paths not even that (a failed session with no deferred record, `:1816-1827`; a run that left no gate record, `:1862-1869`).
- **Exit codes and parks.** A park normally ends the job green: exit 0, and `hand_over` dispatches only on `continue` (`:2536-2554`). Two parks end red: the commands step that could not run (`park_deferred_record`, `:1873-1882`) and a session that failed after its gate pushed a deferred record (`:1816-1827`). A guard refusal skips the run (`_skip`, `:235-237`). The park block has one renderer, `GateResult.what_i_need` (`gate.py:68-82`), fed by the gate record, which `write_park_result` also writes for a pre-run park (`:2602-2636`).
- **Timeouts and spend.** The deploy job runs two sessions, the review pass (`sdlc-deploy.yml:97`) and (e) (`:133`), each under `run_timeout_seconds` (`run_phase.py:271-276`, 125 minutes), then the commands step: 125 + 125 + 50 can already exceed its `timeout-minutes: 200` (`:54-57`). `run_triage` uses the same 125-minute timeout (`:1592`) and records no spend (`record_spend` is called from `run_phase` only, `:1767`, `:1793`).
- **The token and the checkout.** `actions/checkout` persists the workflow token in the project checkout's `.git/config` (no template sets `persist-credentials: false`); `settings.ci.json` denies `Read(.env*)` and `Read(**/secrets/**)`, not `.git`. The phase session holds Edit, Write, `Bash(git *)` and `Bash(python *)` (`IMPLEMENT_ALLOWED_TOOLS`, `:187-190`) and can reach the `framework` checkout, which is why the deploy job removes, re-checks out and verifies it after the review pass (`sdlc-deploy.yml:109-131`).
- **The digest** holds `contents: read`, `issues: write`, `pull-requests: read` and no `actions` permission (`sdlc-digest.yml:29-32`), and needs no model credential. The detect workflow holds `actions: read` and reads the runs API (`sdlc-detect.yml:60`; `plugin/detect/source.py:246-250`).
- **The release notes** are written by the (e) session after the gate (e) check and committed with the evidence (`plugin/commands/sdlc-deploy.md:208-222`); the PR body quotes them under "## Release note" (`plugin/pr/description.py:511-520`). The commit list leaves out evidence-only commits (`EVIDENCE_ONLY`, `notes.py:45`), so a review-comment re-run gives the same text unless the code changed.

## The proposal

Decisions 11 and 20 stay: nothing posts a comment, nothing notifies; the text goes where the owner already looks.

1. **The triage step is wired, on `always()`.** After the phase step (before the `always()` hook-log upload, `sdlc-deploy.yml:148-156`) of the design, build, test, deploy and fix workflows, and of the detect workflow, whose phase (f) session also runs through `run_phase.py` (`sdlc-detect.yml:152`), a step runs `run_phase.py --phase triage` when the runner's step failed or when the runner's own result says it parked, so a green park is reached too. The runner writes its final JSON to a file as well as stdout (`--out <file>`) on every exit path, and the step reads it to pick the log: the parked gate's failing target logs under `evidence/`, the session's result and stderr files; a missing file reads as "the runner did not finish". A failed setup step follows the runbook workflow's pattern (`continue-on-error`, `steps.setup.outcome`, the `error=` output), so its output is a file and the triage step runs. The prompt gains the article's "flaky or real" and "quote no values". The session keeps the Read tool only, with its own short timeout in `run_triage` (minutes, not the 125 of a phase), so it is never what cancels the job, and its spend goes to `record_spend` under the phase's budget (`SPEND_PHASE`).
2. **Where its lines go.** On a park with a log to read, its lines join the "What I need from you" block beside the gate's own text, as a field of the gate record that the one renderer prints under "Triage (model-written):". On a red run with no park they go into the **"Failed runs" line** of the daily digest (point 4). A park that already says why (a guardrail or risk-list hit, a missing target, the owner fields, the panel model, a pre-run park) gets no triage and costs no model call. Before the lines are stored anywhere, the runner passes them through `plugin/hooks/secrets_check.py`'s `find_secrets` and drops a line with a hit: a target's output, a package index URL or the session's stderr can carry a project secret, and the text lands in the gate record, the PR body, a ref and the digest issue.
3. **The cases, after decision 29.**

| Case | Decision 29 | Here |
|---|---|---|
| A red target | the runner dispatches the next round; no park | nothing: the failing logs are the round's constraint |
| A red target at the cap, after T30's one reset | parks | triage reads the last round's logs; its lines in the park block |
| A target's timeout | starts a round | as a red target; the park block at the cap |
| An infrastructure failure in the commands step (decision 29 names the runner lost, an install that fails, a GitHub error; its re-run is of the commands step only) | one automatic re-run, then a park | triage reads the step's output; the park block (today one of the two parks that end red). The same failures outside the commands step fall to the two rows below |
| A missing target | parks at once | no triage: the park names the `sdlc.yaml` gap |
| A failed setup before the session; a session that exits non-zero, hits its wall clock or never reaches its gate; `PR_MISSING`; `COMMIT_NOT_PUSHED`; a failed review validation | not covered: red runs with no park (a wall-clock hit is a limit, decision 11; whether it parks is R10's design to settle, not this) | triage reads the saved files; the "Failed runs" line |
| A lost runner, a job cancelled at `timeout-minutes`, a failed checkout | no step runs | the "Failed runs" line alone, from the Actions API, no text *[2026-10-26, decision 41 point 2, plugin 1.0.50: an `always()` step does run after a `timeout-minutes` cancellation, for about five minutes past the timeout (`docs/notes/62.md`); a job whose runner step GitHub cancelled, at its timeout or by hand, now parks the change, and its line in the digest says it parked; the row holds for a lost runner, a failed checkout, a cancelled review pass and a cancel before the runner saved its state (the park step then writes the runner's result file with no case, so no explain session runs in the minutes left)]* |

4. **The "Failed runs" line, defined here for every entry that names it.** One line per **red run with no park** of the last seven days, oldest first: the workflow, the run with its attempt and link, the change and PR when there is one, the runner's deterministic reason, then "triage (model-written): …" when a step wrote one. A run that parked is in "Needs you" already, so the digest drops a run whose record or PR says parked, and a run whose later attempt succeeded. Two sources, both read by `digest.py`, which keeps no model call:
   - **A failed-run record**: one JSON file on a ref per run, `refs/sdlc/failed-runs/<run_id>-<attempt>` (the name judged with T4), so concurrent workflows never race on one ref and nothing grows; written by the runner after the triage session with the checkout's persisted credential, outside the session, as the release record goes to `refs/sdlc/released/<id>`. It carries the run's address and attempt, the event and its actor (R11's "run on every record" shape), the change id, the step, the exit code, the reason, whether the run parked, and the triage text. The digest lists the refs under the prefix with its `contents: read` and treats each as data: the phase session holds `Bash(git *)` and could push such a ref too. This is R13's answer for a waiting release, applied to a failed run.
   - **The Actions API**, for runs that wrote no record: the digest gains `actions: read`, as `sdlc-detect.yml` holds (this proposal's change; R20 relies on it), lists the framework workflows' runs with conclusion failure, cancelled or timed out in the window, and shows those with no record as the bare line. The only route for a lost runner, a cancelled job, a failed checkout, and for a failed digest (T28), which the next digest that succeeds reports.

   Who feeds it: red phase, fix and detect-session runs with no park (here); T18's merge workflow (with T18); R13's failed release, through the API source only, since the release job holds `contents: read` (`sdlc-release.yml:65-68`) and only its record job, which runs after a release (`:143`), can write, and a release log can print the project's secrets (with R13); T20's preview that could not start (with T20); the detection script's, the scan's and the digest's red runs, through the API source with no text (T22, T26, T28). R20 (T28) places the line under "Worth knowing"; until then it sits after the queue and before the counters. The record stores UTC; which clock the line shows is R20's.
5. **The triage session's environment.** Two layers, as `commands_env` and the workflow's `env:` are today: the step's `env:` passes the model credential and the two file paths only, and `run_triage` hides `GITHUB_TOKEN`, `GH_TOKEN` and the second credential before `invoke`, so a project whose workflow copy predates the step is covered too. Hiding variables does not remove the token persisted in `.git/config`, so the triage session's deny list gains `Read(**/.git/**)`; the record writer (point 4) runs outside the session and pushes with that persisted credential. The phase jobs hold no deploy secret (`sdlc-deploy.yml`, header). The log is read as data: the prompt names the file, and the step never passes its content as text.
6. **A fresh framework checkout before triage.** The triage step runs `framework/plugin/ci/run_phase.py` after a session that could reach the `framework` checkout, so the deploy job's three steps after the review pass (remove, re-checkout at the pin, `checkout_check.py`; `sdlc-deploy.yml:109-131`) are repeated before it in every workflow that gains the step; the record writer runs from that fresh copy, after the Read-only session.
7. **Release notes: a paragraph beside the list.** `notes.py` stays deterministic and stays the record. The (e) session writes a short paragraph in plain words, three to five sentences, under its own heading right after the title ("## In plain words", judged with T4; "What changed" is taken), opening with the label "*Written by the model from the diff and the plan; every section below is generated from files and git.*" and closing with a marker naming the last non-evidence commit it describes. `notes.py --write` keeps the section while that commit is still the last entry of `commits()` and drops it otherwise; `sdlc-deploy.md` §4 tells the session to write it only when the section is missing. So a review-comment re-run with no code change leaves it byte-identical, and a code change gets a fresh paragraph. The PR body quotes it as it quotes the notes today, so the owner reads it at the approval (T18) and the release carries it (R13). It never replaces the list.
8. **The judgment jobs that exist stay**: the REVIEW.md pass (decision 12), the weekly security review, the 2σ/3σ diagnosis.

ArtCraft rule A2 applies throughout: the triage text and the paragraph are model judgments beside measured lines, and both carry the label where they sit.

## How it is judged

The article's indicator, read for one owner: on the first ten failed or parked-red runs after it ships, each has a cause in the park block or in the "Failed runs" line, and the owner acts from the PR or the digest without opening the job log. A failure the owner learns about from Actions alone is the failure this exists to remove. For the notes: at each (e) approval the paragraph says what the change did without the commit list, and a re-run after a review comment with no code change leaves it unchanged.

## What to settle before building

| Question | Recommended |
|---|---|
| How a failed step's output becomes a file the triage step can read | Mostly answered by the code: the session's result and stderr and the three target logs are files already. Left: the setup step follows the runbook workflow's pattern, the runner writes its JSON to `--out`; a failed checkout and a lost runner have no file and get the API line |
| Which parks triage reads, and how the step reads the run's result | Only parks with a log to read (a red target at the cap, the commands step, a failed session); the step reads the runner's `--out` JSON, written on every exit path (today two paths emit nothing, `:1816-1827`, `:1862-1869`), and treats a missing file as "the runner did not finish" |
| How the "Failed runs" line reaches the digest | Point 4: a record on a ref plus the Actions API with `actions: read`; consistent with R13's record for a waiting release |
| Whether a separate job (`needs:`, `if: failure()`) explains a failed checkout or a cancelled job | Not now: the API line covers both with no text; a second job doubles the runner time and holds the same token. Whether an `always()` step runs after a `timeout-minutes` cancellation stays "to verify" and decides nothing here *[2026-10-26: verified, it runs (`docs/notes/62.md`, run 40414066074)]* |
| The paragraph's heading, length and place; how "the code changed" is told | Point 7 |
| The model credential the triage step needs, kept out of the commands step; the token and deploy secrets kept out of triage | Point 5: the token vars hidden, `Read(**/.git/**)` denied, the record pushed outside the session |
| The fresh framework checkout before the triage step | Point 6: the deploy job's remove, re-checkout and `checkout_check.py` steps repeated before it |
| The record's and the heading's names | Judged with T4, as R11's keys are |

The entry's "park at the cap", "lost job" and "timed-out one" are settled by decision 29, and point 3 reads them so; whether a session's wall-clock hit parks belongs to R10's design.

## Considered and not chosen

- A, the crosswalk text corrected and nothing wired.
- B alone, the triage wired and the notes list-only (the session's recommendation; the owner chose C).
- Triage posted as a PR comment, as in the article: GitHub notifies the PR's participants, against decisions 11 and 20.
- A model-written changelog in place of the deterministic list: a re-run would give different text, and the record would be model text.
- Triage on every red target: after decision 29 the round is the judgment and carries the logs; a model call per round would cost without informing the owner, who sees the change only at the cap.
- A separate `needs:` job for the cases where no step ran, and the digest parsing job logs through the API for the triage text: the record carries the text, and the model-free digest stays small.
- A `::error` workflow annotation instead of a record: it shows in the run's own summary, not where the owner looks.
- One appended file on a single ref: concurrent workflows would race on it and it would grow without end.

## Decisions it touches

11 (park, never notify) and 20 (the digest, pull not push) are kept: the triage text goes into the park block and the digest, and nothing notifies. 12 (the review pass in CI) stays. 29 is read as settled, not amended: it fixes which failures become rounds and which park; this proposal adds the explanation at the park and the line for what no round sees. That the release notes are deterministic is build guide step 32.2, not a decision, and it stays. No decision is amended, so no decision file is written.

## Order

After R10 (decision 29), whose rounds define the park at the cap that triage explains; before R20 (T28), which places the line, and before R13's "Failed runs" part, T20, T22 and T26, which feed it. It touches `run_phase.py`, so it goes on HANDOFF's port list, and it ships as a plugin version with tests. The parts, and when each can be built:

| Part | Built now or arrives with |
|---|---|
| `run_triage`: the environment narrowed, `.git` denied, its own timeout and spend, the "flaky or real" prompt, the secrets pass, the record writer; `--out` on every runner exit path; the `always()` step with the fresh framework checkout in the design, build, test, deploy, fix and detect templates; the setup step's runbook pattern | now |
| The triage text in the gate record and in `GateResult.what_i_need` | now; the red-target-at-the-cap case fills after R10 |
| The record on a ref; the digest's "Failed runs" section from the record and the API; `actions: read` on the digest | now; placed under "Worth knowing" by R20 |
| The paragraph: `notes.py` keeping the section, `sdlc-deploy.md` §4 telling the session to write it | now |
| The merge workflow's triage and record | with T18 |
| The release, preview, detection, scan and digest sources | with R13, T20, T22, T26, R20 |

[^playbook]: `docs/reference/ai-native-sdlc-playbook.pdf` p.40-41.
[^crosswalk]: `docs/reviews/2026-09-28-playbook-vs-framework/crosswalk.json`, row deploy-ci, and `target-design.md` T19 ("Today").
