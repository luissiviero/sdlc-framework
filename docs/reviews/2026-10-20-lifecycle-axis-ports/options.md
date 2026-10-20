---
type: Review
title: "Every optional feature and mode, with a proposal for which to keep"
description: The owner asked for a list of everything optional in the framework (built, accepted, or proposed by R60) so that each can be kept as a choice or narrowed to one behaviour; this lists them with a recommendation each and decides nothing.
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

**Why this list.** The owner's concern (2026-10-20): every optional feature multiplies the combinations to try, and an option nobody turns on is work that never gets used. So each row is either a real choice worth keeping, or one behaviour for every project. **Nothing here is decided.**

**What counts as an option.** A setting that changes *how the pipeline behaves*. A fact about the project is not counted: its commands, its test paths, its risk list, its metric and its runbooks. Neither are the limits' numbers, since nobody tests their combinations.

**The recommendation column:**
- **Keep** means the choice stays, because projects really differ on it.
- **One behaviour** means the setting goes and every project behaves the same way.
- **Set by `/sdlc-init`** means it stays a setting, but the owner never picks it: `/sdlc-init` reads it from the project and writes it.

## 1. Modes built today

| Option | Where | Today | Recommendation | Why |
|---|---|---|---|---|
| Profile: `standard` or `full` | `sdlc.yaml: profile`; per change `status.yaml: profile_override` | `standard`; `full` adds the owner's label at (c) and (d) | **One behaviour: `standard`**, and drop the per-change override | `full` adds two waits per change against the owner's autonomy weight. A risky change already waits through the risk list and the R24 banner. |
| Review mode: `deferred` or `parked` | `sdlc.yaml: review`; per change `status.yaml: review_override` | `deferred` (decision 32) | **One behaviour: `deferred`**, and drop the override | `parked` stops at every judgment call. Since decision 32 nobody uses it. |
| Automation identity: the project's GitHub App or the workflow token | `vars.SDLC_APP_ID` (decision 33) | App when set, else workflow token | **One behaviour: the App** | R22 (the App merges at (e)) and R52 need it anyway, and the fallback doubles every path that pushes or opens a PR. |
| Model credential: API key or subscription token | repository secret (decision 1) | either | **Keep** | It follows the owner's account, not the pipeline. One works, and nothing else changes. |
| Declared production | `deploy.production` | `false` | **Keep, set by `/sdlc-init`** | Whether a project has a production is a fact. It turns on the release label and the production-gate hook. |
| Rollback pre-approval | `maintain.runbooks[].rehearsed_at` (decision 26) | unset = "Go" needed | **Keep** | It records an act the owner performed (a rehearsal). R39 would make it automatic. |
| Formatter on edit | `hooks.format_on_edit` | `true` | **One behaviour: on** | R33 makes the formatter follow each language. There is then no reason to switch it off, except a project with its own formatter, which R33's per-language command covers. |
| Dollar cap per change | `gate.max_budget_usd` | 150; `null` = off | **One behaviour: on** | R25's weekly ceiling assumes a cap. "Off" is a combination nobody should run. |
| Lesson staleness | `lessons.stale_after_months` | unset = 12 | **One behaviour: 12 months**, key removed | Nobody has a reason to tune it. |
| Pause everything | `paused` | `false` | **Keep** | It is the emergency stop, not a combination. |
| Automation login override | `automation_identity` | unset | **Keep, hidden** | It is needed only when CI commits under another name. `/sdlc-init` never writes it. |
| Owner's login | `owner` | unset on personal repositories | **Keep, set by `/sdlc-init`** | A fact: required on organisation repositories. |

## 2. Options that accepted or proposed candidates would add

| Option | Candidate (status) | As proposed | Recommendation | Why |
|---|---|---|---|---|
| Merge by silence | R52 (accepted, later step) | opt-in per project | **On by default**, with the owner's act at the start of each change as the consent (conclusion, question 2). The silence timer is dropped; the opt-out is the next row | The owner's direction (2026-10-20) is to make it the default. An opt-out flag keeps a second combination alive. |
| Opt out of merge by silence | R52 | (new, from the owner's direction) | **Keep, one switch** | A project with real users may want every merge read. This is the one combination worth keeping, because it is the only safety lever on unread merges. |
| Preview environment | R39 (accepted) | `deploy.preview_command`, off by default | **Keep, set by `/sdlc-init`**: on when the project has a deploy target that can run a second copy | Whether a project *can* have a preview is a fact. Asking the owner each time adds nothing. |
| Rollback rehearsal | R39 (accepted) | `rehearse_command`, off by default | **One behaviour: on whenever a rollback runbook exists** | A rollback runbook without a rehearsal is the case decision 26 already distrusts. |
| Preview teardown | R39 "What to settle" | `preview_teardown_command`, off | **Drop** | The preview command can replace the previous preview itself. A third key for one environment is not worth it. |
| Staging after the merge | R60 (this study, question 3) | `deploy.staging_command`, off | **Decide with R39**: either one ordered pair, preview then staging, set by `/sdlc-init` from the deploy action, or not at all | It matters only for behaviour that shows over time (paper trading). |
| Drive target | R14 (accepted) | `commands.drive`, optional | **Keep, set by `/sdlc-init`** | Only a project with a screen or a runnable product has one; `/sdlc-init` detects it. |
| Start by hand (no Claude secret) | R30 (accepted) | documented optional path | **Drop** | It is a second way to run every phase, which the owner will not use. The whole loop from change 0000 stays the one way. |
| Transcript upload | R11 (accepted) | a setting, off on public repositories | **One behaviour**: on for private repositories, off for public ones, no setting | Read from the repository's visibility, as the minutes meter will be. |
| A ratchet's floor | R15 (accepted, second change) | optional `min` per ratchet | **Drop** | The ratchet already never falls without a declared reason. A floor is a second knob on the same thing. |
| Detection's day boundary | R16 (proposed) | UTC offset, default `+00:00` | **Set by `/sdlc-init`** from the owner's timezone, asked once | It is a fact about the owner, not a choice to try. |
| Network allow list | R61 (proposed) | optional `sandbox.allowed_domains` | **Set by `/sdlc-init`** from the detected package registry | It is a fact about the project's language. |
| Policy sources | R27 (accepted) | the owner writes `policies/`; without it the plugin's defaults apply | **Keep** | This is the owner's content, not a mode. |
| Second opinion from Gemini | R8 (proposed) | a Gemini key in a secret; no key = off | **Decide at R8**: one behaviour after its five-change tally, either on everywhere or removed | R8 is itself an experiment. Its tally should end in one answer, not leave an option. |
| Parallel worktrees | R50 (proposed, a trigger) | — | Nothing to narrow yet | It is a question for later, not an option. |

## 3. Options this study (R60) proposed

| Option | As proposed | Recommendation |
|---|---|---|
| Actions-minutes meter | `gate.actions_minutes_warn`; on for private repositories | **One behaviour**: on for private repositories at 80%, no key |
| `CLAUDE.md` line budget | `claude_md.max_lines` (the judge's version) | **One behaviour**: 60 lines fixed in the plugin, no key (conclusion, question 5) |
| Plan-growth threshold | `gate.max_plan_growth` (Study B) | **Drop**: the banner line alone, as the judge trimmed it |
| `revisit:` on decisions | optional frontmatter field | **Drop** (excluded in the session's recommendation) |
| Serial queue | `queue: serial` (Study A) | **Drop** (the owner agreed: question 4) |

## Summary of the proposal

If every row above went as recommended, the owner would face **four real choices** per project. Everything else is either one behaviour or written by `/sdlc-init` from facts it detects.

**The four choices:**
1. the model credential;
2. opting out of merge by silence;
3. pausing everything;
4. the policy sources.

**Two decisions are left open:**
- the staging step after the merge (question 3);
- Gemini, which R8's tally decides.

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

Narrowing the built ones means removing code and decisions 18, 21 (its `parked` mode) and 33 (its fallback). Each needs a decision file through the front door, as any amendment does.
