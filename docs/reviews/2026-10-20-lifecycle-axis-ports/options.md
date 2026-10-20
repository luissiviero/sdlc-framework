---
type: Review
title: "Every optional feature and mode, with a proposal for which to keep"
description: The owner asked for a list of everything optional in the framework (built, accepted, or proposed by R60) so that each can be kept as a choice or narrowed to one behaviour; this lists them with what each does and a recommendation each, and decides nothing.
status: report
roadmap: R60
sources:
  - id: template
    resource: template/sdlc.yaml
    title: "Every setting /sdlc-init writes, with its default"
  - id: roadmap
    resource: docs/ROADMAP.md
    title: "The accepted and proposed candidates whose proposals add an option"
  - id: conclusion
    resource: docs/reviews/2026-10-20-lifecycle-axis-ports/conclusion.md
    title: "R60's merged recommendation and the owner's answers"
generated: { by: claude-code-session, at: 2026-10-20T09:00:00Z }
---

# Optional features: which to keep, which to narrow

**Why this list.** The owner raised a concern on 2026-10-20: every optional feature multiplies the combinations to try, and an option nobody turns on is work that never gets used. So each row ends as one of two things: a real choice worth keeping, or one behaviour for every project. **Nothing here is decided**, except the staging row, which the owner settled on 2026-10-20.

**What counts as an option.** A setting that changes *how the pipeline behaves*. These are not counted:
- facts about the project: its commands, test paths, risk list, metric and runbooks;
- the limits' numbers, since nobody tests their combinations.

**The recommendation column:**
- **Keep** means the choice stays, because projects really differ on it.
- **One behaviour** means the setting goes and every project behaves the same way.
- **Set by `/sdlc-init`** means it stays a setting, but the owner never picks it: `/sdlc-init` reads it from the project and writes it.

## 1. Modes built today

| Option | What it does | Where | Today | Recommendation | Why |
|---|---|---|---|---|---|
| Profile: `standard` or `full` | Sets which phase ends wait for the owner. `standard` waits at the intent, the design and the merge. `full` also waits for the owner's label after the build (c) and after the test (d). | `sdlc.yaml: profile`; per change `status.yaml: profile_override` | `standard` | **One behaviour: `standard`**, and drop the per-change override. **The owner: approved as recommended (2026-10-20).** | `full` adds two waits per change, against the owner's autonomy weight. A risky change already waits through the risk list and the R24 banner. |
| Review mode: `deferred` or `parked` | Sets what a run does with a judgment call, such as an open concern or a reviewer's "escalate". `deferred` lets a review panel decide and lists the decision in the PR. `parked` stops the change until the owner answers. | `sdlc.yaml: review`; per change `status.yaml: review_override` | `deferred` (decision 32) | **One behaviour: `deferred`**, and drop the override. **The owner: approved as recommended (2026-10-20).** | `parked` stops at every judgment call. Since decision 32 nobody uses it. |
| Automation identity: the project's GitHub App or the workflow token | Sets which account pushes branches and opens PRs for the runs. Only the App's pushes start the next workflow by themselves. | `vars.SDLC_APP_ID` (decision 33) | App when set, else the workflow token | **One behaviour: the App** **The owner: approved the next session's revised recommendation (2026-10-20): the App is required for every project from R22's build on; `/sdlc-init` stops at the App setup and says it is desktop-only, with the link (R21), instead of running on the workflow token. The workflow token stays as the in-job fallback, the session's token and in the workflows that mint no App token. This carries out decision 33; `CLAUDE.md`'s fallback sentence is the owner's edit.** | R22 (the App merges at (e)) and R52 need it anyway, and the fallback doubles every path that pushes or opens a PR. *[2026-10-20, verified by the next session (C5): partly. The row leaves out the cost: a one-time App setup per project in a desktop browser and a key to guard (decision 33, "What it gives up"; `plugin/commands/sdlc-init.md` step 6: create the App, set five permissions, generate a key, install it, set `SDLC_APP_ID` and `SDLC_APP_PRIVATE_KEY`); without the fallback no run works before that. And the reason overstates it: nothing is doubled. Eight of the thirteen template workflows mint the App token in one conditional step; the transitions go through the explicit dispatch in both cases (`plugin/ci/run_phase.py:2735-2741`); and the workflow token stays anyway, as the in-job fallback once the App token is 50 minutes old (`plugin/ci/app_token.py:108-123`), as the model session's token (`app_token.py:278-284`), and in the five workflows that mint no App token. Dropping the setting removes the no-App path only.]* |
| Model credential: API key or subscription token | Sets how CI pays for Claude: an Anthropic API key, or the owner's Pro/Max subscription token. | repository secret (decision 1) | either | **Keep** **The owner: approved as recommended, with one change (2026-10-20): when both secrets are set, `CLAUDE_CODE_OAUTH_TOKEN` wins.** Today the key wins (`plugin/ci/auth.py:18`; decision 1's note of 2026-09-21, "`ANTHROPIC_API_KEY` preferred"), as the CLI itself does in print mode ("the key is always used when present", `docs/notes/2.md:91`), so the token winning means the runner drops the key from the session's environment when the token is set. A change to decision 1's applied note and to `plugin/ci/auth.py`, through the front door. | It follows the owner's account, not the pipeline. One works, and nothing else changes. |
| Declared production | Says the project has a live system real users depend on. It turns on the second act before a release (the `sdlc:release-approved` label) and the hook that blocks deploy commands in a session. | `deploy.production` | `false` | **Keep, set by `/sdlc-init`**. **The owner: approved as recommended (2026-10-20).** | Whether a project has a production is a fact. |
| Rollback pre-approval | Lets a rehearsed rollback run on a detected breach without the owner's "Go". Without it, the incident PR waits for the owner's `sdlc:go`. | `maintain.runbooks[].rehearsed_at` (decision 26) | unset = "Go" needed | **Keep**. **The owner: approved as recommended (2026-10-20).** | It records an act the owner performed (a rehearsal). R39 would make it automatic. *[2026-10-20, verified by the next session: R39 automates the rehearsal (a weekly workflow), not the pre-approval; it adds a condition, a passing rehearsal within N days, beside the owner's `rehearsed_at` (`docs/proposals/preview-environment.md`, points 4 and 5).]* |
| Formatter on edit | Runs the formatter and linter on each file Claude edits, and feeds problems back at once. | `hooks.format_on_edit` | on | **One behaviour: on** **The owner: approved the next session's revised recommendation (2026-10-20): one behaviour, on, once R33 is built (the project names its formatter per file type and the key goes); until then the switch stays and `/sdlc-init` writes `false` on a Python project formatted by black, yapf or autopep8 (R33's proposed addition).** | R33 makes the formatter follow each language. The one reason to switch it off, a project with its own formatter, is covered by R33's per-language command. *[2026-10-20, found at the session's close: this conflicts with R33's proposed addition in `docs/ROADMAP.md` (`/sdlc-init` writes `format_on_edit: false` when `pyproject.toml` configures another formatter). The next session reconciles the two.]* *[2026-10-20, verified by the next session (E5): the conflict is real, with R33's proposed addition, not with its accepted design. Today the off switch is a black, yapf or autopep8 project's only escape (`plugin/hooks/format_on_edit.py:75-77`). R33's accepted design lets a file glob map to the project's own commands, with ruff only where there is no mapping (`docs/proposals/formatter-per-language.md`). Reconciled: once R33 is built, `/sdlc-init` writes a `*.py` mapping to the project's formatter and the key goes; until then, `/sdlc-init` writes `false` for such a project, as R33's addition proposes.]* |
| Dollar cap per change | Parks a change whose model spend reaches the cap. | `gate.max_budget_usd` | 150 USD; `null` = off | **One behaviour: on** | R25's weekly ceiling assumes a cap. "Off" is a combination nobody should run. |
| Lesson staleness | Sets how long an incident's lesson stays fresh before the index marks it "(stale)". | `lessons.stale_after_months` | unset = 12 | **One behaviour: 12 months**, key removed | Nobody has a reason to tune it. |
| Pause everything | Stops every run before it starts, project-wide. | `paused` | `false` | **Keep** | It is the emergency stop, not a combination. |
| Automation login override | Names other bot accounts whose acts never count as the owner's. | `automation_identity` | unset | **Keep, hidden** | It is needed only when CI commits under another name. `/sdlc-init` never writes it. |
| Owner's login | Names the account whose labels, reviews and comments count as the owner's. | `owner` | unset on personal repositories | **Keep, set by `/sdlc-init`** | A fact: required on organisation repositories. |

## 2. Options that accepted or proposed candidates would add

| Option | What it does | Candidate (status) | As proposed | Recommendation | Why |
|---|---|---|---|---|---|
| Merge by silence | Merges a routine, green build PR with nothing for the owner to look at, without waiting for the owner's merge. | R52 (accepted, later step) | opt-in per project, after N hours of silence | **On by default**, with the owner's act at the start of each change as the consent. The timer is dropped; the opt-out is the next row. | The owner's direction and approval (2026-10-20, conclusion question 2). |
| Opt out of merge by silence | Keeps every merge the owner's own act on that project. | R52 | (new, from the owner's direction) | **Keep, one switch** | A project with real users may want every merge read. This is the one combination worth keeping, because it is the only safety lever on unread merges. |
| Preview environment | Deploys each build PR's code to a throwaway copy before the owner approves. The result is a line in the PR's banner. | R39 (accepted) | `deploy.preview_command`, off by default | **Keep, set by `/sdlc-init`**: on when the project has a deploy target that can run a second copy | Whether a project *can* have a preview is a fact. Asking the owner each time adds nothing. |
| Staging after the merge | After the owner's merge, deploys the merged code to a long-lived staging copy (paper trading) before the release label sends it to production. | R60 (this study, question 3) | `deploy.staging_command`, off | **Keep (the owner, 2026-10-20)**: paired with the preview, set by `/sdlc-init` from the deploy action; paper trading turns it on | Some of the owner's projects trade, and their behaviour shows only over days of market data. |
| Rollback rehearsal | Runs the rollback against the preview environment weekly and records pass or fail. A recent pass is what pre-approves the real rollback. | R39 (accepted) | `rehearse_command`, off by default | **One behaviour: on whenever a rollback runbook exists** | A rollback runbook without a rehearsal is the case decision 26 already distrusts. *[2026-10-20, verified by the next session (C4): wrong as written. The rehearsal needs a `rehearse_command` the project writes, aimed at the preview or another non-production environment (`docs/proposals/preview-environment.md`, point 4 and "What to settle"). A project with a rollback runbook and no such environment cannot rehearse; the sample is one (`deploy.action: none`). What a runbook with no `rehearse_command` gets (Go, or decision 26's date alone) is left to R39's decision file. So this is a project fact, not a mode: set by `/sdlc-init` when a non-production target exists.]* |
| Preview teardown | Removes a preview once its PR merges or closes. | R39 "What to settle" | `preview_teardown_command`, off | **Drop** | The preview command can replace the previous preview itself. A third key for one environment is not worth it. |
| Drive target | One command that runs the product headless and saves screenshots or state as proof that a change works. | R14 (accepted) | `commands.drive`, optional | **Keep, set by `/sdlc-init`** | Only a project with a screen or a runnable product has one; `/sdlc-init` detects it. |
| Start by hand (no Claude secret) | Lets the owner run each phase from their own sessions instead of CI. The CI jobs skip themselves. | R30 (accepted) | documented optional path | **Drop** | It is a second way to run every phase, which the owner will not use. The whole loop from change 0000 stays the one way. |
| Transcript upload | Keeps each CI session's full transcript as a downloadable workflow artifact, for reading a run later. | R11 (accepted) | a setting, off on public repositories | **One behaviour**: on for private repositories, off for public ones, no setting | It follows the repository's visibility, as the minutes meter will. |
| A ratchet's floor | Sets a minimum the test or eval count can never fall below, under the "never falls without a reason" rule. | R15 (accepted, second change) | optional `min` per ratchet | **Drop** | The ratchet already never falls without a declared reason. A floor is a second knob on the same thing. *[2026-10-20, verified by the next session: R15 does not propose a `min`. Its floor is the merge base's own value (`docs/proposals/ratchets.md`, point 7), and "The floor as `min` in `sdlc.yaml`" is under "Considered and not chosen". There is no option here to drop.]* |
| Detection's day boundary | Sets where detection's "day" starts, so the daily counts follow the owner's clock. | R16 (proposed) | UTC offset, default `+00:00` | **Set by `/sdlc-init`** from the owner's timezone, asked once | It is a fact about the owner, not a choice to try. |
| Network allow list | Lists extra sites a sandboxed CI session may reach, such as the language's package registry. | R61 (proposed; *[accepted 2026-10-20, choice 240]*) | optional `sandbox.allowed_domains` | **Set by `/sdlc-init`** from the detected package registry | It is a fact about the project's language. |
| Policy sources | The owner's own rules (coding, security, data, UX, done) in `policies/`, which the plugin's skills read first. | R27 (accepted) | without them the plugin's defaults apply | **Keep** | This is the owner's content, not a mode. |
| Second opinion from Gemini | Sends the design to a Gemini model at gate (b) and shows its verdict in the PR. It never parks. | R8 (proposed) | a Gemini key in a secret; no key = off | **Decide at R8**: one behaviour after its five-change tally, either on everywhere or removed (the owner approved, 2026-10-20) | R8 is itself an experiment. Its tally should end in one answer, not leave an option. |
| Parallel worktrees | Several local sessions working on different changes at once. | R50 (proposed, a trigger) | — | Nothing to narrow yet | It is a question for later, not an option. |

## 3. Options this study (R60) proposed

| Option | What it does | As proposed | Recommendation |
|---|---|---|---|
| Actions-minutes meter | Shows GitHub Actions minutes used this month in the digest, and warns before they run out. | `gate.actions_minutes_warn`; on for private repositories | **One behaviour**: on for private repositories at 80%, no key (the owner agreed: question 1) |
| `CLAUDE.md` line budget | Caps `CLAUDE.md`'s length and lists lines to delete when a new one would pass the cap. | `claude_md.max_lines` (the judge's version) | **One behaviour**: 60 lines fixed in the plugin, no key (the owner approved: question 5) |
| Plan-growth threshold | Treats a change as non-routine when its plan grew past a size after approval. | `gate.max_plan_growth` (Study B) | **Keep as one behaviour, no key: one of R52's conditions.** A change whose plan grew by more than half its approved file list (at least 5 files) since gate (b) does not merge by silence; it waits for the owner at (e). *Changed on 2026-10-20: with merge by silence on by default, this is the only check that a routine plan stayed the plan the reviewer classed routine before it merges unread.* *[2026-10-20, verified by the next session (C2): R52's conditions do not include it (ROADMAP R52; `docs/proposals/speed-beyond-the-sprint.md`, section "R52"), nor does `conclusion.md`'s question 2, which the owner approved before this change. It is a new condition for the owner to accept or refuse.]* |
| `revisit:` on decisions | A date or measure on a decision, after which the docs lint says it is due for review. | optional frontmatter field | **Drop** (excluded in the session's recommendation) |
| Serial queue | Runs one change at a time and queues the rest. | `queue: serial` (Study A) | **Drop** (the owner agreed: question 4) |

## Summary of the proposal

If every row above went as recommended, the owner would face **four real choices** per project. Everything else is either one behaviour, or written by `/sdlc-init` from facts it detects.

**The four choices:**
1. the model credential;
2. opting out of merge by silence;
3. pausing everything;
4. the policy sources.

**No decision is left open.** The owner settled the staging step on 2026-10-20: keep it. Gemini is settled the same day: R8's tally decides it, with one behaviour.

**What would drop out:** about ten optional paths and their combinations:
- the `full` profile;
- the `parked` review mode;
- the per-change profile and review overrides;
- the workflow-token fallback;
- switching off the formatter or the dollar cap;
- the by-hand start;
- preview teardown;
- a ratchet's floor;
- the serial queue.

Narrowing the built ones means removing code and amending decisions 18, 21 (its `parked` mode) and 33 (its fallback). Each needs a decision file through the front door, as any amendment does. *[2026-10-20, verified by the next session (C3): partly. The `full` profile and the per-change profile override touch 18 (it defines both), 30 ("the Full profile's (c) and (d) are unchanged"), 3 and 27 (the (c) and (d) labels), 34 point 3 and 35 point 1 (the Full profile's banner). The `parked` mode and its override touch 21 and 32 ("`parked` stays available per project and per change"). Decision 33 holds no fallback and already rejects keeping the workflow token, so dropping the fallback carries 33 out rather than amending it; the fallback is written in the workflows, in `plugin/ci/run_phase.py:2735-2741` and in `CLAUDE.md`, a guardrail file.]*
