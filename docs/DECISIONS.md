# Decisions — accepted and applied in build guide v3

Companion to `BUILD_GUIDE.md`. Step numbers refer to that guide. The accepted alternative is marked **[ACCEPTED]**.

Decisions 21–26 were added on 2026-09-23 after the plan was audited against the owner's original objective and the article (session record: PR #22). The mechanism of 21 is the owner's, the rest are the session's suggestions adopted on the owner's instruction to proceed; all six were **confirmed on 2026-09-23** by the owner's merge of PR #22.


## 1. Where unattended claude -p runs execute and how they authenticate

*Reference: step 3*

- Local for B1 → hosted CI + API key from B3. Phase commands run on your PC by hand only in B1; from B3 every phase runs in GitHub Actions with an API key. **[ACCEPTED]**
- Hosted CI with the Max subscription. Cheapest if allowed; depends on current Claude Code terms/docs — must be verified, not assumed.
- Local only, with a scheduler. No CI cost, but an always-on machine you must keep alive.

**Accepted:** Local only for B1; hosted CI + API key from B3 on; check (2) first and take it if permitted REVISED

*Applied 2026-09-21 (not a reopening):* the product docs permit (2) for Pro, so every workflow accepts both secrets — `ANTHROPIC_API_KEY` preferred, `CLAUDE_CODE_OAUTH_TOKEN` otherwise — and the owner starts on the token and moves to the key from `/usage` data. Facts and setup in `docs/NOTES.md` §2.

**Why:** The article's own ladder is "by hand → slash command → trigger" (p.13), so B1–B3 need no CI at all. Hosted CI is the only option with zero local maintenance, which matches your constraint; the API cost is bounded per change by step 19's limits. Option 2 is worth one check because it removes that cost, but building on it unverified could strand the design. Revised: hands-off means you should not be the one launching phases either, so merge-triggered CI moves up from B4 to B3 — the first autonomous phase should already fire on its own.

**Decide by / reversibility:** B3 REVERSIBLE


## 2. Where plan.md is produced and approved

*Reference: step 12 (already applied in the guide)*

- A — end of phase (b) , read-only planning run; approved with spec.md at one gate. **[ACCEPTED]**
- B — inside phase (c) , approval replaced by the confidence gate; you see plan.md with the diff at gate (c).
- C — its own gate between (b) and (c): one more approval per change.

**Accepted:** A

**Why:** The article calls plan review the moment when "changing course is still a matter of editing a document" (p.17) — the cheapest gate there is, and it costs you one extra read at a gate you already have. B risks a full autonomous build on a wrong plan; C adds an interruption your objective explicitly avoids. Keep B as a later "promotion" if you ever want fewer approvals.

**Decide by / reversibility:** B0 STICKY


## 3. How you approve gates (c) and (d), which sit on one open PR

*Reference: steps 1, 27, 28*

- Approving review + phase label ( sdlc:c-approved , sdlc:d-approved ) on the single build PR; merge only at (e). **[ACCEPTED]**
- One PR per phase (build PR merged to an integration branch, test PR, release PR).
- A comment command (e.g. /approve c ) parsed by the orchestrator.

**Accepted:** Review + label

**Why:** The article keeps one PR from Build through Review to merge (p.34 "babysit the PR to merge") and makes the PR "the audit record" (p.35); splitting it into three PRs breaks that record and multiplies merges. Labels are native, visible in the PR list, and trivially readable by a workflow; a comment command is a second mechanism to maintain.

**Decide by / reversibility:** B0 REVERSIBLE


## 4. Branch rule that keeps the agent off main

*Reference: step 6*

- Ruleset: only your account may push/merge to main ; automation identity has branch-only write access. **[ACCEPTED]**
- Require one approving review (classic branch protection).
- Both.

**Accepted:** Ruleset (1); add (2) only if a second reviewer ever exists

**Why:** "Require a review" does not count the author's own approval, so the intent PR you author in phase (a) would be blocked — the first gate of the loop would need a workaround. A merge-restricted ruleset gives exactly what the article asks for ("the agent has no route to push to main", p.40) with your merge as the approval for every PR, whoever opened it.

**Decide by / reversibility:** B0 REVERSIBLE


## 5. Automation identity for non-interactive runs

*Reference: steps 5, 6*

- CI platform's built-in workflow token (GitHub's github-actions[bot] ). **[ACCEPTED]**
- A GitHub App you register (private key, token minting).
- A second personal (machine) account.

**Accepted:** Built-in token first; GitHub App only when its limits bite

**Why:** Zero setup and zero secrets to rotate — the maintenance profile you asked for — and it already separates "what the agent did" from "what you approved" in the log (p.41). Its known limit (events it causes — pushes, PRs, labels — do not start workflow runs, except `workflow_dispatch` and `repository_dispatch`) is designed around in steps 9 and 30: the owner's own merges and labels fire workflows normally, and every automated transition dispatches the next workflow explicitly (NOTES §11a). A machine account is a second login to protect for no benefit.

**Decide by / reversibility:** B3 REVERSIBLE


## 6. Where the guardrails live so the agent cannot switch them off

*Reference: steps 7, 15*

- Project .claude/settings.json only (in the repo the agent edits).
- Project settings + a self-protecting hook that denies edits to .claude/** , CLAUDE.md, REVIEW.md and the hook scripts.
- (2) + a user-level managed settings file on your PC + CI loads hooks from the pinned plugin, never from the PR branch. **[ACCEPTED]**

**Accepted:** All three layers (option 3)

**Why:** The article's only non-advisory layer is the one "individual engineers cannot switch off" (p.36) — and in your framework the "engineer" being controlled is the agent. Option 1 turns every hook into a suggestion; option 2 still lets a run edit settings through a path the hook missed; option 3 is one extra file on your machine and one line in each workflow.

**Decide by / reversibility:** B2 STICKY


## 7. Runtime for hooks, gate checks, detection scripts and eval checks (you are on Windows)

*Reference: step 2*

- Python for everything, one make -like task runner that works on Windows and Linux. **[ACCEPTED]**
- Bash + jq as in the article's examples, via Git Bash locally.
- PowerShell locally, bash in CI.

**Accepted:** Python

**Why:** The article's scripts are bash/jq/make (p.20, 28, 36–37) but say nothing about Windows. One runtime that runs identically on your PC and on a Linux runner removes a whole class of "works in CI, fails locally" bugs, and it is the language you already write the detection statistics in. Verify once how Claude Code on Windows invokes hook commands before committing.

**Decide by / reversibility:** B0 STICKY


## 8. Framework distribution

*Reference: step 2*

- Plugin (process) + template (project files) , plugin version pinned per project. **[ACCEPTED]**
- Copy .claude/ into every repo (no plugin).
- Git submodule / subtree of the framework repo.

**Accepted:** Plugin + template

**Why:** The article's own distribution answer is the plugin/marketplace (p.21, p.38, p.51) and it fits the three-layer layout you already run. Copies drift and cannot record "the skill versions in force" (p.14); submodules put the whole framework, including CI workflows, inside each project's diff surface.

**Decide by / reversibility:** B0 STICKY


## 9. Source of truth for artifacts and work items

*Reference: step 4*

- Repo is the source of truth ; GitHub Issues / vault hold links (linkage rule). **[ACCEPTED]**
- GitHub Issues as the record , markdown as working copies written back via MCP.
- Your knowledge vault as the record.

**Accepted:** Repo + linkage

**Why:** You have no auditor or other team depending on a legacy tool, which is the only reason the article gives for option 2 (p.18). One timestamp authority (git) also makes every metric in the guide a two-timestamp query. Linkage costs one issue number in a header and one SHA in an issue.

**Decide by / reversibility:** B0 REVERSIBLE


## 10. Change folder and naming convention

*Reference: step 9*

- changes/<id>-<slug>/ holding intent.md, spec.md, plan.md, evidence/, status.yaml; branches sdlc/<id>/<phase> . **[ACCEPTED]**
- Article-literal intent/ folder , spec/plan next to the code.
- Separate intent repo.

**Accepted:** changes/<id>-<slug>/

**Why:** The article never says how to pair intent, spec and plan "for the same change" although three of its metrics need it (p.12, p.15); one folder per change answers that and gives the orchestrator a place for state. A separate repo is "only worth the overhead when intent spans many repositories" (p.10) — not your case.

**Decide by / reversibility:** B0 STICKY


## 11. What happens when a phase cannot finish on its own

*Reference: steps 5, 16, 18, 19*

- Escalate whenever a plan is "non-routine" (large blast radius, untested code).
- Escalate (notify you) on gate failure, limit hit, or an explicit risk list.
- Park, never page. On gate failure, limit hit or a risk-list hit the run stops, finishes every artifact it can, writes a "what I need from you" section into the PR, labels it sdlc:needs-human — and nobody is notified. You find it when you next review; "non-routine" only tightens the gate. **[ACCEPTED]**

**Accepted:** Park, never page (3) REVISED

*Amended by decision 21 (2026-09-23):* under deferred review a judgment item that would park is put to the review panel and the run continues; the hard parks (risk-list hit, guardrail file change, run limit, infrastructure failure) still park, and nobody is ever notified.

**Why:** In a new project almost nothing is "routine" by the article's definition (p.17), so option 1 would page you constantly and defeat point 3 of your objective. Option 2 was my first answer; your hands-off constraint changes it: escalation and notification are different things. The article's headless gate "escalates to a human" (p.42) but says nothing about paging one. Parking keeps the safety property (nothing risky proceeds unreviewed) without ever calling you — the parked PR simply joins the queue you review in one sitting. The only cost is latency on that change, which you have said you accept.

**Decide by / reversibility:** B2 REVERSIBLE


## 12. Where the AI review pass runs

*Reference: step 26*

- Managed Code Review service (admin-enabled; may not be available to a personal repo).
- claude -p review job in CI with REVIEW.md, fresh context, findings as a check run with a severity tally. **[ACCEPTED]**
- Reviewer subagent inside the same local session.

**Accepted:** CI job (2); use (3) only while you are still on the local substrate

**Why:** Separation of duties needs the reviewer in a different context from the writer (p.27, p.35); a CI job under the automation identity gives that plus a machine-readable tally the gate can read (p.33). Option 1 is the article's "fastest start" but only if your plan offers it; option 3 shares the session that wrote the code, so it is acceptable only as a stopgap.

**Decide by / reversibility:** B3 REVERSIBLE


## 13. Shape of gate (e) — merge only, or merge + release authorization

*Reference: steps 29, 32*

- Merge is the whole gate until a project has a real production environment; then add a release label the production-gate hook reads. **[ACCEPTED]**
- Always two acts (merge, then release label/tag).
- Deploy fully autonomous after merge , rollback as the only control.

**Accepted:** Option 1

**Why:** The article tiers autonomy by environment (p.40): dev deploys freely, production waits for a named authorization. For a library, a research repo or a dev-only service, a second act is ceremony; for anything that touches live trading it is exactly the "release manager" gate the article insists on. Option 3 contradicts "nothing past the production gate" (p.32).

**Decide by / reversibility:** B4 REVERSIBLE


## 14. Authorization model for 3σ runbooks in phase (f)

*Reference: step 37*

- Pre-approved runbooks run with no human in the path (p.43–44).
- Per-incident "Go" from you before any runbook runs (p.49–50).
- Split by blast radius: pre-approve CI-scoped, reversible actions (quarantine a flaky test, open a revert PR); require "Go" for anything that touches a running system (rollback, config change). **[ACCEPTED]**

**Accepted:** Split by blast radius (3)

*Amended by decision 26 (2026-09-23):* on a project that declares a real production, a rollback that has been rehearsed is pre-approved; every other running-system action still waits for "Go".

**Why:** The article shows both models for the same action and never reconciles them. For systems that move money the asymmetry is clear: a missed auto-quarantine costs minutes, a wrong automatic rollback at 3 a.m. can cost a position. Write the split into bands.yaml per route so it is enforced, not remembered.

**Decide by / reversibility:** B5 REVERSIBLE


## 15. First metric to close the loop on

*Reference: step 37*

- CI test failure rate (the article's own example, needs only the CI API). **[ACCEPTED]**
- PR cycle time (process metric).
- A production metric (post-deploy error rate, strategy PnL drift…).

**Accepted:** CI test failure rate first; a production metric once a project runs live

**Why:** It exists on day one for every project, the bands.yaml on p.44 is written for it, and its 3σ actions are reversible — which lets you exercise the whole f→a loop safely before wiring anything to a live system. A production metric is the real prize but should reuse a proven loop.

**Decide by / reversibility:** B5 REVERSIBLE


## 16. Recurring security scans

*Reference: step 38*

- Claude Security (requires a Claude Enterprise org and cloud github.com).
- Weekly claude -p run of a security-review skill , read-only, findings → PR gate or intent.md, fixed classes → evals; deterministic scanners stay in CI. **[ACCEPTED]**
- Deterministic scanners only (dependency audit, SAST).

**Accepted:** Option 2 (unless your plan includes Claude Security)

**Why:** The pattern — scheduled, no human in the invocation path, same gates as any change (p.46) — is what matters, and it is reproducible with the plumbing you build anyway. Option 3 misses the "context-dependent vulnerabilities those checks are not built to find" (p.48).

**Decide by / reversibility:** B5 REVERSIBLE


## 17. When to start evals and parallel worktrees

*Reference: steps 33, 35*

- Day one for both.
- Evals after ~20 real changes exist (empty evals/ from day one, filled by incidents); worktrees only once review keeps up, i.e. probably never for one person. **[ACCEPTED]**
- Skip both.

**Accepted:** Option 2

**Why:** The article's eval suite starts from "20 to 50 real tasks from recent work" (p.30) — you cannot write it before the work exists — but the incident→eval rule (p.44, p.47) pays from the first incident, so the folder must exist. Parallel sessions' ceiling is "how many streams one person can review properly" (p.25), and you review only at phase ends.

**Decide by / reversibility:** B5 REVERSIBLE


## 18. How many human gates per change — project and change profiles

*Reference: step 9a (also 1, 16, 24) · NEW*

- Always five gates (a, b, c, d, e) as literally stated in your objective.
- Profiles. Standard (default): human gates at (a), (b: spec+plan) and (e: merge); gates (c) and (d) are passed by the confidence gate and only parked on failure. Full : all five human gates — for projects with a live production or money at stake. Lite : (a) and (e) only — scripts, experiments, docs. Profile set by /sdlc-init , overridable per change in status.yaml. **[ACCEPTED]**
- Size-based : gate count from the diff size / files touched.

**Accepted:** Profiles, default Standard (3 gates)

*Amended by decision 21 (2026-09-23):* Standard stays the default; the Lite profile is withdrawn — it removed the human from gate (b), which the article keeps human (p.14 "A human team mate always makes this call", p.15 "Nothing is implemented without an accepted plan") — and deferred review (step 16a) replaces what Lite was for. Lite stays in the code, and `/sdlc-init` still offers it, until step 16a ships and removes it; do not choose it for a new project.

**Why:** This is the biggest consequence of your two constraints. Literally "input at the end of each step" is five interactions per change, and for a small project that is more ceremony than the change itself. The article's own end state runs gates as "a deterministic check or an adversarial reviewing agent" with humans only on escalation (p.42), and its Deploy row reserves "human review for regulated and critical code" (p.6). Gate (e) already shows you plan conformance, evidence and review findings on one PR, so reviewing there is reviewing (c) and (d) after the fact — which is what "review once it's done" means. Keep Full for the projects where a wrong autonomous step is expensive.

**Decide by / reversibility:** B0 REVERSIBLE


## 19. What "deploy" and "maintain" mean for non-service projects

*Reference: step 9b (also 24, 31, 37) · NEW*

- Code-only semantics as in the article (deploy = ship a service; maintain = production bands); projects without them skip phases (e) and (f).
- Per-project phase adapters declared at /sdlc-init : deploy = "publish the package / schedule the job / regenerate the report / promote the strategy to paper trading"; maintain = the metric that project actually emits (job success rate, data freshness, backtest-vs-live drift) with the same bands.yaml machinery. **[ACCEPTED]**
- Two frameworks (one for services, one for research/data work).

**Accepted:** Phase adapters (2)

**Why:** The article assumes a service with a pipeline and production traffic; "any sort of project" does not. Skipping (e) and (f) for research code loses the loop — and the closing-the-loop play works for "process metrics as well as production ones" (p.45), so the machinery transfers; only the deploy action and the watched metric are project-specific. Two frameworks would double the maintenance you want to avoid.

**Decide by / reversibility:** B0 STICKY


## 20. How finished work reaches you

*Reference: step 27a (also 8, 27, 32) · NEW*

- Per-event notifications (PR opened, gate parked, review done).
- A review queue you open on your own cadence : the PR list filtered by sdlc:* labels, each PR description opening with a ≤5-bullet summary (what changed, evidence status, findings by severity, what needs you), plus a daily digest PR/issue that lists the queue. **[ACCEPTED]**
- No aggregation ; you read PRs raw.

**Accepted:** Queue + digest (2)

**Why:** Hands-off review works only if the review itself is cheap: the article's principle is that human attention "concentrates at the gates, reviewing what the agent flagged rather than starting each stage from scratch" (p.8). A generated summary at the top of every PR is that flagging; a daily digest replaces notifications with one predictable touchpoint. Nothing pushes to you.

**Decide by / reversibility:** B2 REVERSIBLE


## 21. Deferred review inside a phase — the owner reviews once, at the end (replaces the Lite profile)

*Reference: steps 9a, 16, 23, 16a · NEW (2026-09-23)*

- Lite profile: no human gate at (b); the confidence gate accepts spec.md + plan.md. Withdrawn: it contradicts the article's human acceptance of the spec (p.14, p.15).
- Park on every judgment item and wait for the owner (the behaviour as built): the first design run parks on 6–9 open concerns, and each round is a commit, a workflow run and a review — so many that no single change gets read carefully.
- Deferred review: a per-project setting (`sdlc.yaml: review: deferred`, per-change override in `status.yaml`). Inside a phase, a judgment item that would otherwise park is put to a **review panel** — a reviewer (the REVIEW.md pass) and a devil's advocate (the adversarial reviewer), each in its own fresh context and blind to the other, then a conciliator (fresh context) that reads both verdicts and writes the decision with its rationale. The run applies the decision and continues. Every panel decision is one line in `evidence/decisions-<phase>.md`; the PR summary at the next human gate opens with "Decisions taken for you (N)", and any of them is overturned by a review comment that `/sdlc-fix` applies. The human gates at the end of each phase are unchanged (Standard: a, b, e; Full: all five). **[ACCEPTED]**

**Accepted:** Deferred review (3); Lite withdrawn

**What goes to the panel — a fixed list, never the run's own judgment:** an open flagged concern in spec.md; contradicting policy skills; an `escalate` verdict of the adversarial reviewer (its routine / non-routine classification never parks, it only lowers the iteration cap); an Important review finding whose fix the run cannot determine; a verifier disagreement. **What never goes to the panel and still parks:** a risk-list hit (auth, data migrations, money movement, production config), a guardrail file change, a run limit (iterations, wall clock, budget, pause flag), an infrastructure failure, and anything that merges to `main` or deploys.

**Why:** The owner's account of the live runs: the commit → workflow → review rounds inside one phase are so many that the changes stop being read carefully; one review per phase, everything at once, is what point 3 of the objective ("my input at the end of each step") meant. The article's own end state is the same mechanism — "an independent confidence gate between stages, a deterministic check or an adversarial reviewing agent, deciding whether the previous stage's output continues or is escalated to a human" (p.42) — applied here to the parks inside a phase, while the human gate at the end of (b) is kept, so p.14 and p.15 hold. Human accountability (p.6) is kept by the decisions ledger: nothing is decided without a line the owner reads. A panel reduces variance, not bias — three judges on one model share its blind spots — so the devil's advocate runs on a different model than the reviewer (`--model` on its `claude -p` run, or the agent's `model` frontmatter when it runs as a sub-agent; NOTES §11b, §11c), and the panel is reserved for the fixed list, never for deterministic checks. Cost: three fresh runs per panel call, bounded by `gate.max_budget_usd`. A wrong panel decision at (b) yields a spec the owner still reads before anything is built, the cheapest place to be wrong; inside (c)–(e) the framework already runs unattended and the hard parks stay.

**Decide by / reversibility:** B4 (step 16a) REVERSIBLE — confirmed on 2026-09-23


## 22. How "ask for changes" runs by itself

*Reference: steps 8, 11, 26, 30 · NEW (2026-09-23)*

- Manual: the owner launches `/sdlc-fix` after commenting (as built; the command carries `disable-model-invocation: true` and refuses phase (a)).
- A label the owner applies (`sdlc:fix`) starts a fix workflow.
- The owner's **"Request changes" review submission** starts a fix workflow: `template/.github/workflows/sdlc-fix.yml` on `pull_request_review` `submitted` with state `changes_requested`, actor not the workflow token, the change found from `status.yaml` as HANDOFF item 4(a) settles and not from the head name alone (a web-session intent PR does not carry an `sdlc/<id>/a` head) → `run_phase.py --phase fix` → `/sdlc-fix <id>`. `/sdlc-fix` is extended to gate (a): on an intent PR it applies the comments to `intent.md` without re-running the brainstorm, so `sdlc-plan.md`'s pointer to it becomes true. **[ACCEPTED]**

**Accepted:** "Request changes" starts the fix run (3); the label is not added

**Why:** "Request changes" is already the owner's second verb in GitHub, so no new mechanism is introduced; a review the owner submits starts workflows normally, since only events caused by the workflow token are ignored (NOTES §11a); and it closes the audit's finding that applying the owner's change requests was the one non-autonomous step between gates. The article's loop is the same: "Claude addresses the comment and pushes the fix" (p.33) and "let Claude babysit the PR to merge" (p.34). One exception to OPERATING_MODEL §4.1 ("nothing in a run edits intent.md") and §8 ("interactively") follows: `/sdlc-fix` on the unmerged intent PR edits `intent.md` from the owner's comments.

**Decide by / reversibility:** B4 REVERSIBLE — confirmed on 2026-09-23


## 23. Hosting scope: GitHub only

*Reference: steps 2, 6, 21, 30 · NEW (2026-09-23)*

- Record GitHub hosting as a precondition of "any new project"; `/sdlc-init` refuses a project whose `origin` is not GitHub, with the reason. **[ACCEPTED]**
- Abstract the hosting layer (Actions, PRs, labels, rulesets, workflow token, check runs, the pinned issue) behind an interface.

**Accepted:** Record it (1)

**Why:** Every piece of plumbing the plan relies on is GitHub-specific — the merge and label triggers, the token identity, the ruleset, the check runs, the digest issue — and the audit found that nothing said so. An abstraction has no consumer today; recording the limit costs one sentence and one check in `/sdlc-init`.

**Decide by / reversibility:** B4 REVERSIBLE — confirmed on 2026-09-23


## 24. The owner's un-park verbs are labels

*Reference: steps 5, 9, 16, 19 · NEW (2026-09-23)*

- CLI commands only (as built): `accept-risk`, `set-iterations`, `unlock-tests`, `paused: false` in `sdlc.yaml`.
- Labels the owner applies on the PR — `sdlc:accept-risk`, `sdlc:reset-iterations`, `sdlc:unlock-tests` — read by the next run and recorded in `status.yaml` with the label's actor; the CLI commands stay for by-hand runs; the pause flag stays in `sdlc.yaml` because pausing is a reviewed change. **[ACCEPTED]**

**Accepted:** Labels (2), CLI kept

**Why:** Point 3 of the objective puts the owner's input in the PR, not in a terminal; GitHub records who applied a label, so the `owner_actions` check can read the actor instead of inferring from the commit author (PROGRESS choice 17), which is the stronger separation-of-duties check (p.34–35, p.41).

**Decide by / reversibility:** B4 REVERSIBLE — confirmed on 2026-09-23


## 25. Gate (f) is per-finding triage; closing a PR at (a)–(e) abandons the change

*Reference: steps 9, 39 · NEW (2026-09-23)*

- (f): per-finding triage of each incident intent PR — merge (fix now), label (schedule), close with a reason (dismiss) — is the gate; there is no phase-level sign-off, because maintain is a standing loop and each incident re-enters at gate (a). **[ACCEPTED]**
- (f): add a periodic sign-off of the maintain loop.
- Closing a PR at gates (a)–(e) without merging = abandon: `status.yaml: phase: abandoned`, branches kept, every workflow skips the change; closing an incident intent PR both dismisses the finding (signature suppressed) and abandons its change. **[ACCEPTED]**
- Leave closing undefined.

**Accepted:** Triage as the gate; close = abandon

**Why:** The article's loop has no end-of-maintain approval; its human point is "the review gate decides" per proposal (p.45). Abandon is cheap to add and prevents orphaned state files and workflows that fire on a closed change.

**Decide by / reversibility:** B4 REVERSIBLE — confirmed on 2026-09-23


## 26. Rollback authorization on a declared production (amends 14)

*Reference: steps 37, 39 · NEW (2026-09-23)*

- Keep "Go" for every running-system action (decision 14 as accepted).
- Allow one notification for a 3σ breach on a declared production.
- Pre-approve a **rehearsed** rollback on a project with `deploy.production: true` — `maintain.runbooks[].rehearsed_at` recorded in `sdlc.yaml` by the owner after a staging rehearsal; every other running-system action keeps "Go" as a parked item; still no notification. **[ACCEPTED]**

**Accepted:** Pre-approve rehearsed rollback (3)

**Why:** The article has the agent trigger the rollback pipeline itself at 3σ (p.45), and the p.49 figure makes a rehearsal the precondition Claude states before asking for "Go" ("The rollback was rehearsed in staging this morning; shall I run it?"); this decision goes one step further than the article by dropping the "Go" for that case, with p.45 as the precedent. A "Go" that waits silently in the queue brings back the problem the loop exists to remove — "an alert … can be missed" (p.42) — for exactly the case where minutes matter. Notification is still ruled out (decision 20).

**Decide by / reversibility:** B5 REVERSIBLE — confirmed on 2026-09-23


Sticky decisions (2, 6, 7, 8, 10, 19) shape files and conventions every later step writes to.
