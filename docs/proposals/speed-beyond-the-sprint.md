---
type: Proposal
title: Speed beyond the pipeline sprint — the speed-first order, merge by silence, faster CI jobs and the quick intent
description: After R10, R17 and R46 to R49, a routine change waits for the owner only at its intent and at gate (e); this proposal reorders the roadmap so the candidates that remove the owner's remaining waits come first, and adds three candidates (R52 to R54).
status: accepted
roadmap: R52, R53, R54
sources:
  - id: owner
    resource: "the owner's message of 2026-10-19, session ccr-70fb3ae3-39fz5m ('speed things up as much as possible when I use this plugin … even if it means giving up a bit of control for a meaningful time boost'), and the answer 'I accept all recommendations as you suggest them'"
    title: "The request and the acceptance"
  - id: measurements
    resource: "the sample's changes/0001-*/evidence/claude-*.json and changes/0002-*/evidence/claude-*.json (duration_ms); docs/proposals/pipeline-speed.md"
    title: "Model time per phase run between 15 seconds and 10 minutes on the sample; 0.3 to 6.4 model hours against 1.8 to 7.4 days per change before the sprint"
  - id: notes-48
    resource: docs/notes/48.md (on branch ccr-6281cac2-hdaob7, PR #241)
    title: "Change 0015: the App's pushes start CI with no approval click; the build caps apply; the deploy run red at the checkout check (fixed in 1.0.12)"
generated: { by: sdlc-framework-session/ccr-70fb3ae3-39fz5m, at: 2026-10-19T18:00:00Z }
---

# Speed beyond the pipeline sprint
**Names since R45** (decision 39; the renames built in plugin 1.0.43 to 1.0.47; added on 2026-10-26, the text below keeps the old names, choice 126): `(a)` -> intent; `(b)` -> design; `(e)` -> deploy; `/sdlc-plan` -> `/sdlc-intent`; `deploy.production` -> `deploy.production_gate`; `production: true` -> `production_gate: true`. \
**Status: accepted by the owner on 2026-10-19 (choice 234), as recommended.** Nothing is built.

## Where the time goes now

The model works seconds to ten minutes per phase run on the sample. Since the sprint, a routine change on the Standard profile waits for the owner twice: to write the intent, and at gate (e). A non-routine change also waits at gate (b). Any park (a risk-list hit, a run limit, an infrastructure failure, the iteration cap) adds a wait. The candidates below remove those waits or shorten the owner's time at each one; none makes a run faster except R53.

## The speed-first order

The candidates that remove the owner's waits move to the front of ROADMAP's Order. The rest keep their order among themselves after them:

| Rank | Candidate | Why it is here |
|---|---|---|
| 7 | R7 | Better first pass, fewer fix rounds (unchanged) |
| 8 | R24 | A risk-list hit stops parking; it becomes a banner line the merge accepts |
| 9 | R22 | Gate (e) becomes one approving review on the phone; the App merges |
| 10, 11 | R51 with R25 parts 1-2 | Several changes in flight, safely and within a spend ceiling *[2026-10-20: "spend ceiling" here is the per-change budget cap that exists since R48 (`gate.max_budget_usd`, 150 USD in the template); the weekly ceiling is R25's part 3, after the trial]* |
| 12 *[2026-10-20, choice 238: R44 12, R18 13, R29 part 1 with R54 14, R26 15, R52 16, R45 20 (last before the trial), R28 21 (after it); the rank is read from ROADMAP's Order column]* | R18 | A park explains itself, so the owner's diagnosis takes minutes |
| 13 *[2026-10-20, choice 238: 14]* | R29 part 1 with R54 | An intent from anywhere, in one paragraph |
| 14 *[2026-10-20, choice 238: 15]* | R26 | The measures R52 needs |
| 15 *[2026-10-20, choice 238: 16]* | R52 | Merge by silence, not before R22, R26 and R50's trigger |
| 16 onward *[2026-10-20, choice 238: 17 onward; R45 is 20, the last before the trial, and R28 is 21, after it]* | R33, R14, R27, R28, R45, R5, R6, … R8 | As before, among themselves; R28 and R14 add model time and R45 is a rename, so they come after the speed items |

R53 is measured with the live proof and built after R18 only if the measure says so. *[2026-10-20: measured on change 0015, 4 to 9 percent of each phase job (NOTES §49); no build on this measure]*

## R52, merge by silence at gate (e)

Opt-in per project. A build PR merges without the owner's act when all of these hold: the plan is routine, every check is green, the PR carries no "Decisions taken for you", no risk-list hit, and `deploy.production` is false. The App merges it after a set number of hours (a project setting) unless the owner commented, labelled or reviewed in between. It removes the last wait of a routine change. The owner gives up reading the code before it merges, so it amends decision 4 for opted-in projects only. Its decision is written at R50's trigger (20 changes past gate (e) on a real project), when R26's measures show how often a routine change needed a fix after its merge. *[2026-10-20, R60's answers carried in (the owner, 2026-10-20; `docs/reviews/2026-10-20-lifecycle-axis-ports/options.md`, section 2, rows "Merge by silence" and "Opt out of merge by silence", section 3, row "Plan-growth threshold"; `conclusion.md`, question 2 and row R52). Merge by silence is on by default, and a project opts out with one switch, so the decision amends decision 4 for every project that has not opted out. The timer goes: the owner's act at the start of each change is the consent, and the App merges as soon as the conditions hold. A per-change "read before merge" line, in the intent or a label and read from the base branch, keeps a change for the owner's merge at (e); it is the owner's way to object, since no window is left. The conditions above stay, and two are added, both fixed with no key: the locked-path floor (a diff touching `.claude/**`, `CLAUDE.md`, `REVIEW.md`, `sdlc.yaml`, `protected_paths`, `.github/**` or `evals/**` never merges unread, a rename judged on both names; `judge.md`, item 1) and the plan-growth condition (a plan grown since gate (b) by more than half its approved file list, at least 5 files). Each such merge is recorded as "merged unread" in R11's list with the conditions it met, printed on the PR and listed in the digest, and R52 builds a one-act revert of a change from that list (new work: `revert-pr` cannot be started on a chosen merged change today). The timing is unchanged.]*

## R53, faster CI jobs

Each phase job installs the Claude Code CLI, checks out the framework at the pin and runs the project's `setup` command before the session starts. That time is not measured. *[2026-10-20: measured on change 0015, 4 to 9 percent of each phase job (NOTES §49); no build on this measure]* The live-proof session reads it from the job steps of a full change; if setup is at least a fifth of a run, R53 caches the installs (actions/cache) or moves the jobs to a prebuilt image.

## R54, the quick intent

The owner writes one paragraph and opens the intent PR (the fast lane accepts it). The design run fills the rest of the intent template and lists what it assumed at the top of the design PR. The owner corrects an assumption there or at gate (e), instead of in `/sdlc-plan`'s correction loop (article p.11, step 4). Built with R29 part 1, which adds the route from claude.ai and the phone.

## The owner's other choices on 2026-10-19

- **The sample runs `review: deferred`**: applied by the owner in the sample's PR #72.
- **The profiles are used as they are** (no build): `deploy.production: false` where a project has no real production, and the Lite profile per change or project for scripts, documentation and experiments. *[2026-10-20: Lite was withdrawn by decision 21; read "Standard on the fast lane (decision 30)"]* The sample keeps `production: true`, since it exercises the release path.
- **Incident intents keep gate (a)**: the weekly scan's and the detection's intents still wait for the owner's triage.
- **The fix-round caps stay** (3, and 2 for a non-routine plan) until R26's measures show how often a change parks at the cap.

## Decisions it touches

4 (R52, amended for opted-in projects only, at R50's trigger), 13 and 31 kept, 30 kept. *[2026-10-20, R60's answers: 4 is amended for every project that has not opted out, still at R50's trigger]*
