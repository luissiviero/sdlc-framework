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
| Profile: `standard` or `full` | Sets which phase ends wait for the owner. `standard` waits at the intent, the design and the merge. `full` also waits for the owner's label after the build (c) and after the test (d). | `sdlc.yaml: profile`; per change `status.yaml: profile_override` | `standard` | **One behaviour: `standard`**, and drop the per-change override | `full` adds two waits per change, against the owner's autonomy weight. A risky change already waits through the risk list and the R24 banner. |
| Review mode: `deferred` or `parked` | Sets what a run does with a judgment call, such as an open concern or a reviewer's "escalate". `deferred` lets a review panel decide and lists the decision in the PR. `parked` stops the change until the owner answers. | `sdlc.yaml: review`; per change `status.yaml: review_override` | `deferred` (decision 32) | **One behaviour: `deferred`**, and drop the override | `parked` stops at every judgment call. Since decision 32 nobody uses it. |
| Automation identity: the project's GitHub App or the workflow token | Sets which account pushes branches and opens PRs for the runs. Only the App's pushes start the next workflow by themselves. | `vars.SDLC_APP_ID` (decision 33) | App when set, else the workflow token | **One behaviour: the App** | R22 (the App merges at (e)) and R52 need it anyway, and the fallback doubles every path that pushes or opens a PR. |
| Model credential: API key or subscription token | Sets how CI pays for Claude: an Anthropic API key, or the owner's Pro/Max subscription token. | repository secret (decision 1) | either | **Keep** | It follows the owner's account, not the pipeline. One works, and nothing else changes. |
| Declared production | Says the project has a live system real users depend on. It turns on the second act before a release (the `sdlc:release-approved` label) and the hook that blocks deploy commands in a session. | `deploy.production` | `false` | **Keep, set by `/sdlc-init`** | Whether a project has a production is a fact. |
| Rollback pre-approval | Lets a rehearsed rollback run on a detected breach without the owner's "Go". Without it, the incident PR waits for the owner's `sdlc:go`. | `maintain.runbooks[].rehearsed_at` (decision 26) | unset = "Go" needed | **Keep** | It records an act the owner performed (a rehearsal). R39 would make it automatic. |
| Formatter on edit | Runs the formatter and linter on each file Claude edits, and feeds problems back at once. | `hooks.format_on_edit` | on | **One behaviour: on** | R33 makes the formatter follow each language. The one reason to switch it off, a project with its own formatter, is covered by R33's per-language command. |
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
| Rollback rehearsal | Runs the rollback against the preview environment weekly and records pass or fail. A recent pass is what pre-approves the real rollback. | R39 (accepted) | `rehearse_command`, off by default | **One behaviour: on whenever a rollback runbook exists** | A rollback runbook without a rehearsal is the case decision 26 already distrusts. |
| Preview teardown | Removes a preview once its PR merges or closes. | R39 "What to settle" | `preview_teardown_command`, off | **Drop** | The preview command can replace the previous preview itself. A third key for one environment is not worth it. |
| Drive target | One command that runs the product headless and saves screenshots or state as proof that a change works. | R14 (accepted) | `commands.drive`, optional | **Keep, set by `/sdlc-init`** | Only a project with a screen or a runnable product has one; `/sdlc-init` detects it. |
| Start by hand (no Claude secret) | Lets the owner run each phase from their own sessions instead of CI. The CI jobs skip themselves. | R30 (accepted) | documented optional path | **Drop** | It is a second way to run every phase, which the owner will not use. The whole loop from change 0000 stays the one way. |
| Transcript upload | Keeps each CI session's full transcript as a downloadable workflow artifact, for reading a run later. | R11 (accepted) | a setting, off on public repositories | **One behaviour**: on for private repositories, off for public ones, no setting | It follows the repository's visibility, as the minutes meter will. |
| A ratchet's floor | Sets a minimum the test or eval count can never fall below, under the "never falls without a reason" rule. | R15 (accepted, second change) | optional `min` per ratchet | **Drop** | The ratchet already never falls without a declared reason. A floor is a second knob on the same thing. |
| Detection's day boundary | Sets where detection's "day" starts, so the daily counts follow the owner's clock. | R16 (proposed) | UTC offset, default `+00:00` | **Set by `/sdlc-init`** from the owner's timezone, asked once | It is a fact about the owner, not a choice to try. |
| Network allow list | Lists extra sites a sandboxed CI session may reach, such as the language's package registry. | R61 (proposed) | optional `sandbox.allowed_domains` | **Set by `/sdlc-init`** from the detected package registry | It is a fact about the project's language. |
| Policy sources | The owner's own rules (coding, security, data, UX, done) in `policies/`, which the plugin's skills read first. | R27 (accepted) | without them the plugin's defaults apply | **Keep** | This is the owner's content, not a mode. |
| Second opinion from Gemini | Sends the design to a Gemini model at gate (b) and shows its verdict in the PR. It never parks. | R8 (proposed) | a Gemini key in a secret; no key = off | **Decide at R8**: one behaviour after its five-change tally, either on everywhere or removed | R8 is itself an experiment. Its tally should end in one answer, not leave an option. |
| Parallel worktrees | Several local sessions working on different changes at once. | R50 (proposed, a trigger) | — | Nothing to narrow yet | It is a question for later, not an option. |

## 3. Options this study (R60) proposed

| Option | What it does | As proposed | Recommendation |
|---|---|---|---|
| Actions-minutes meter | Shows GitHub Actions minutes used this month in the digest, and warns before they run out. | `gate.actions_minutes_warn`; on for private repositories | **One behaviour**: on for private repositories at 80%, no key (the owner agreed: question 1) |
| `CLAUDE.md` line budget | Caps `CLAUDE.md`'s length and lists lines to delete when a new one would pass the cap. | `claude_md.max_lines` (the judge's version) | **One behaviour**: 60 lines fixed in the plugin, no key (the owner approved: question 5) |
| Plan-growth threshold | Treats a change as non-routine when its plan grew past a size after approval. | `gate.max_plan_growth` (Study B) | **Drop**: the banner line alone, as the judge trimmed it |
| `revisit:` on decisions | A date or measure on a decision, after which the docs lint says it is due for review. | optional frontmatter field | **Drop** (excluded in the session's recommendation) |
| Serial queue | Runs one change at a time and queues the rest. | `queue: serial` (Study A) | **Drop** (the owner agreed: question 4) |

## Summary of the proposal

If every row above went as recommended, the owner would face **four real choices** per project. Everything else is either one behaviour, or written by `/sdlc-init` from facts it detects.

**The four choices:**
1. the model credential;
2. opting out of merge by silence;
3. pausing everything;
4. the policy sources.

**One decision is left open:** Gemini, which R8's tally decides. The staging step was settled by the owner on 2026-10-20: keep it.

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

Narrowing the built ones means removing code and amending decisions 18, 21 (its `parked` mode) and 33 (its fallback). Each needs a decision file through the front door, as any amendment does.
