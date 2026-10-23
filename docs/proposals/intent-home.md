---
type: Proposal
title: The intent home — in the repository, written from anywhere, with examples
description: Intents stay in changes/<id>-<slug>/ in the project repository; a second route writes them from claude.ai on a computer or a phone and must arrive as a PR on sdlc/<id>/a, never a commit to main; the intent template gains an Examples/References section and is overridable per project; for a screen change the interview asks for a mock and spec.md's Acceptance gets a fixed "Mock:" line.
status: accepted
roadmap: R29
sources:
  - id: study-entry
    resource: docs/reviews/2026-09-28-playbook-vs-framework/target-design.md
    title: "T3, confirmed at the close of the study on 2026-10-09; from the crosswalk rows setup-home (better: the framework; decision: blend), plan-idea and design-mock (better: the playbook; decision: blend, 2026-10-02); annotation of 2026-10-13 (R14, ArtCraft row A1); T2's open item on examples"
  - id: crosswalk
    resource: docs/reviews/2026-09-28-playbook-vs-framework/crosswalk.json
    title: "Rows setup-home, plan-idea and design-mock (whole)"
  - id: record
    resource: docs/reviews/2026-09-28-playbook-vs-framework.md
    title: "Section 7, the close; section 8, part 1 (the T3 row: amends none, confirmed) and part 2 (the format and the confirmed order)"
  - id: drive-target
    resource: docs/proposals/drive-target-and-proof.md
    title: "R14 (ArtCraft row A1, accepted 2026-10-13): the plan's Proof gains the state kind; its settle row on how T3's Mock: line and the screenshot item relate (D2)"
  - id: playbook
    resource: docs/reference/ai-native-sdlc-playbook.pdf
    title: "p.10: the intent home, an intent/ folder for a single product, a connector that commits from claude.ai or Cowork; p.11: the template as a skill signed off by a lead, the merge or the closing review as the record; p.12: the leading and lagging indicators; p.12-13: the product owner's mock in Claude Design"
  - id: decision-10
    resource: docs/decisions/10.md
    title: "Decision 10: changes/<id>-<slug>/ and sdlc/<id>/<phase> (kept)"
  - id: decision-4
    resource: docs/decisions/4.md
    title: "Decision 4: only the owner's account may push or merge to main (kept; the reason the claude.ai route is a PR)"
  - id: decision-9
    resource: docs/decisions/9.md
    title: "Decision 9: the repository is the source of truth (kept)"
  - id: code
    resource: plugin/commands/sdlc-plan.md
    title: "/sdlc-plan steps 1 to 6; plugin/skills/intent-template/SKILL.md; plugin/skills/spec-template/SKILL.md Acceptance; plugin/state/cli.py new-change, conventions.py next_change_id, gitops.py remote_change_ids, status.py new_change; plugin/gate/artifacts.py INTENT_SECTIONS and INTENT_HEADER_FIELDS; plugin/gate/checks.py check_artifacts and CHECKS_BY_PHASE; plugin/ci/run_phase.py find_change; template/.github/workflows/sdlc-design.yml; plugin/pr/digest.py sdlc_labels; read at main 5542406, plugin 1.0.1"
generated: { by: sdlc-framework-session/ccr-01de3f80-ilnomi, at: 2026-10-15T20:00:00Z }
---

# The intent home: in the repository, written from anywhere, with examples

**Status: proposed (roadmap R29), from study entry T3, confirmed by the owner on 2026-10-09.** *[2026-10-20: accepted 2026-10-16 (roadmap R29, PR #215)]* Nothing is built. It amends no settled decision: the home stays where decisions 8, 9 and 10 put it, and the route it adds opens the intent PR on `sdlc/<id>/a` and never commits to `main`, which keeps decisions 4 and 10 whole. It owns the intent's home, the template's Examples/References section and its override, the `Mock:` line and the claude.ai route; the Product brief at gate (a) and the interview are R28's (T1, with T2 inside), the label-started ticket route is R31 (T6), the plan's `state` Proof kind is R14's, and the rename of `/sdlc-plan` is R45's (T4).

## The problem

The owner works alone, looks in once or twice a day, and has ideas away from the keyboard. Today an idea becomes an intent in one place, and the intent has no room for what the owner wants to show:

- **Only from a Claude Code session.** `/sdlc-plan` is "the only interactive phase" (`plugin/commands/sdlc-plan.md:11`): it allocates the change through `plugin/state` (`:38-43`), writes the intent with the `intent-template` skill (`:45-47`), commits on `sdlc/<id>/a` (`:53-58`) and opens the intent PR (`:60-74`). The crosswalk row plan-idea asked whether "Claude Code only" matters "for ideas that start away from the keyboard"; the owner's answer is a second route, from claude.ai on a computer or a phone[^crosswalk].
- **No place for examples.** The template fixes "exactly this shape": the five article sections, plus Evidence for incidents (`plugin/skills/intent-template/SKILL.md:13-38`). Examples of what is wanted, references and links have no section; the only named slot is `mock/`, committed with the spec at (b) (`template/changes/README.md:15`).
- **Nothing asks for a mock, and the spec never says there is none.** The spec's Acceptance asks in free prose for "the screenshot or mock to match for UI" (`plugin/skills/spec-template/SKILL.md:39-42`); the interview's questions do not mention a mock (`sdlc-plan.md:23-36`); the (d) screenshot loop runs only when the plan or the spec names one (`plugin/commands/sdlc-test.md:75-80`).
- **The template is the plugin's alone, as far as anything documents.** `/sdlc-plan` names the plugin skill and says nothing of a project copy (`sdlc-plan.md:45-47`); a project override is documented only for the five policy skills (`plugin/commands/sdlc-design.md:73-75` and each policy skill's "Project override" line, e.g. `plugin/skills/coding-standards/SKILL.md:15`); nothing documents one for `intent-template`.

## What the article says

The Plan stage's prerequisites are "Claude access for people who are not engineers (claude.ai or Cowork); an agreed intent.md template; a shared, version-controlled home for intent that the product owner watches. For a single product the simplest home is an intent/ folder in the product repo"; "a dedicated intent repo is only worth the overhead when intent spans many repositories". A technical team member stands up the home and decides "who can write to it", and then "a connector to the version-control system (e.g. GitHub) lets Claude commit markdown files on their behalf from claude.ai or Cowork" (p.10). The originator describes the problem, Claude asks an analyst's questions (p.10 steps 1-2) and writes intent.md from "the organization's template, which can be encoded as a skill, set up by a technical team member and signed off by a lead"; the originator corrects it and commits it to the shared home, and "the accept or reject decision ... is recorded as the merge or the closing review" (p.11). The leading indicator is the time "from first conversation to a committed intent.md"; the lagging one the share of intents accepted rather than closed (p.12). For front-end work "the product owner mocks the design up in Claude Design (beta) from the intent.md, iterates on the mock, and then exports it to Claude Code to build" (p.12-13)[^playbook].

The framework departs from the article's home on purpose: decision 10 chose `changes/<id>-<slug>/`, a folder of five kinds of file, over an `intent/` folder, and the owner kept it (setup-home: better, the framework). The article's template (p.11) has no examples section; the owner adds one.

## What the framework does today

Read at `main` 5542406, plugin 1.0.1 (`.claude-plugin/plugin.json:4`). The entry has no "Today" paragraph: its code references are in its Open items, which reached `main` on 2026-10-01 and 2026-10-02 (`904f4ec`, `35e64b5`, plugin 0.3.1). `git diff --stat 35e64b5 5542406` over `plugin/commands/sdlc-plan.md`, `sdlc-design.md`, `sdlc-init.md`, `plugin/skills/intent-template/`, `plugin/skills/spec-template/`, `plugin/state/`, `template/changes/README.md` and `plugin/gate/artifacts.py` touches `sdlc-design.md` (+8, a rule on foreground sub-agents), `plugin/state/cli.py` and `conventions.py` (+18, +14, the review record of 0.3.5) and `artifacts.py` (+77, the lesson and deferred-evidence fields), none of `new-change`, `next_change_id` or the intent's constants, so every line the entry cites still holds.

- **The home.** `/sdlc-init` writes `changes/README.md` and `changes/0000-sdlc-init/` with its intent (`plugin/commands/sdlc-init.md:58-64`). Each later folder comes from `plugin/state`.
- **The id.** `new-change` (`plugin/state/cli.py:48-72`) takes the next id after the checkout's change folders and, when there is a remote, its `sdlc/<id>/*` heads (`plugin/state/conventions.py:210-216`, `plugin/state/gitops.py:324-335`), so a change started on the PC and one started in a cloud session do not collide; it writes `status.yaml` and `evidence/` (`plugin/state/status.py:422-459`). The template forbids inventing an id (`intent-template/SKILL.md:44`). A run that cannot read a change's `status.yaml` stops with "status.yaml is unreadable" (`plugin/ci/run_phase.py:975-978`).
- **The workflow does not filter on the head.** The design workflow fires on the merge of any pull request into the default branch and on `workflow_dispatch`, with no push trigger (`template/.github/workflows/sdlc-design.yml:19-32`, `:51-59`); the runner takes the id from an `sdlc/<id>/a` head and falls back to the merged PR's one `changes/<id>-<slug>/` folder for any other head (`run_phase.py:748-799`), such as the `claude/...` branch to which a Claude Code web session pushes `/sdlc-plan`'s intent (HANDOFF 4(a), recorded at `run_phase.py:737-739`). So a direct commit to `main` starts no design run, and also passes no gate (a).
- **The PR and the queue.** `pr/cli.py upsert` writes the generated description and the label `sdlc:a-ready` (`sdlc-plan.md:60-74`); the digest lists a PR as waiting only when it carries an `sdlc:` label (`plugin/pr/digest.py:138` and `:187`, through the helper `sdlc_labels`, `:78-79`), so an intent PR opened without that step is in no queue.
- **What gate (a) checks.** The owner's merge is the gate. The checks defined for (a), `artifacts`, `design_scope`, `guardrails` and `risk_list` (`plugin/gate/checks.py:1694-1697`), run in a fix round at (a); the intent's sections and header fields are the plugin's constants (`artifacts.py:19-31`), checked by `check_artifacts` (`checks.py:186-212`), and every later gate requires `intent.md` (`artifacts.py:76-83`). A project template could add a section, never drop or rename one, while the gate reads these constants.
- **Corrections on the owner's own PR.** GitHub refuses "Request changes" on the reviewer's own pull request (verified, `docs/notes/29.md:38`), which every intent PR the owner opens is; R17 (accepted 2026-10-14) adds the owner's `@claude` comment as the trigger there.
- **The mock.** `mock/` is optional, committed with the spec (`template/changes/README.md:15`); the build reads it and names in Proof the screenshot (d) compares (`plugin/commands/sdlc-build.md:85-87`); `git grep -n "Mock:" 5542406 -- plugin template` finds nothing, so the fixed line does not exist. R14 (accepted 2026-10-13) records how a `Mock:` line and the plan's `screenshot` item relate once both exist: the verifier compares them at (d)[^drive-target].
- **claude.ai.** Nothing in the framework reaches claude.ai, and no note in `docs/notes/` records what a claude.ai GitHub connector on the owner's account can do (create a branch, commit a file, open a pull request or an issue, read the repository): not verified.

## The proposal

Added, nothing replaced (the owner's words on plan-idea and design-mock). Six parts; the first is today's, kept.

1. **Where: unchanged.** Ideas stay in `changes/<id>-<slug>/` in the project repository, set up by `/sdlc-init`, each folder created through `plugin/state`. Decisions 8, 9 and 10 are unchanged; the article's `intent/` folder is not taken (decision 10's reason: one folder pairs the intent, spec and plan of a change, p.12 and p.15; it departs from p.10's advice on purpose); the folder's name is kept by R45 (T4).

2. **Written from anywhere.** A second route writes an intent from claude.ai, on a computer or a phone, beside `/sdlc-plan` in Claude Code. The owner's rule: it arrives as a PR on `sdlc/<id>/a`, never as a commit to `main`. The entry's premise, to verify with the connector check below: a claude.ai GitHub connector acts as the owner's account, the ruleset's only bypass actor (decision 4), so a direct commit would skip gate (a) (decision 10). The route needs three things `/sdlc-plan` has: the template in the conversation, an id from `plugin/state`, and the PR opened as `upsert` opens it (generated description, `sdlc:a-ready`). The entry leaves the second open: how the id is allocated is in "What to settle", with the session's recommendation.

   Corrections after that are today's: review comments and the fix round at (a) (decision 22); on the owner's own PRs, R17's `@claude` comment.

3. **Accepted by the owner's merge**, after the gate (a) briefs of T1 (Product, Architect), which R28 builds. Until R28, the merge alone, as today. R28 leaves to this proposal where the briefs run for an intent written on the claude.ai route (`roles-and-manager.md:172`); the session's recommendation is in "What to settle".

4. **The template: the plugin's by default, overridable per project (to verify).** The plugin's `intent-template` stays the default. A project may carry its own copy; a change to it gets the Product role's review (R28) and the owner's approval, the merge. Two owner notes bear on that review: T3's note gives it to "a Product role", and the later x-roles note of 2026-10-09, point (6), gives the brief on the owner's own skill PRs to Platform & release, with "a policy source read by the role of its kind". R28 (proposed) reconciles them: it reads the project's copy as Product's source, as a policy source is read by the role of its kind, wherever the copy lives, and gives the brief on a change to it to Product (`roles-and-manager.md:164`, `:215`); this proposal follows that reading. *[2026-10-20: R28 is accepted (2026-10-16), not proposed]* While the gate reads the plugin's constants, an override adds sections and never drops or renames the five article sections or the header fields. The claude.ai conversation uses the same template, the project's copy when there is one (the session's recommendation, below).

5. **Examples and references.** The intent gains a section, "Examples/References" (heading wording judged with R45), where the owner puts examples of what is wanted and references such as a competitor's screens. "none" is a valid answer (the template's rule, `intent-template/SKILL.md:49`). `mock/` stays the slot for screens. The `intent-template` skill fixes "exactly this shape", so this is a change to the plugin's template, not only to one intent. One rule goes into the template and into `/sdlc-build`: the build matches the owner's mock, never the referenced screens. Whether the roles read the section is T2's open item, inside R28.

6. **The mock (design-mock, 2026-10-02).** When a change touches a screen, the interview asks "Do you have a mock or example screens?" (`/sdlc-plan` step 1 now; this proposal adds the question to the interview text, as the entry assigns it to T3, and R28's manager-led interview, which lists it at its point 7, inherits it), and `spec.md`'s Acceptance gets one fixed line, "Mock: mock/<file>" or "Mock: none, screens follow the UX conventions". The owner makes a mock in Claude Design when wanted; a missing mock never blocks. The 2026-10-13 annotation keeps the line as it is; the plan's Proof gaining the `state` kind is R14's part, not this one.

## How it is judged

On the next three intents the owner starts away from the keyboard: each arrives as a PR on `sdlc/<id>/a` with an id `plugin/state` allocated, the `sdlc:a-ready` label and the generated description (and, if the recommended staging route is chosen, the owner's commit in its history); no intent commit lands on `main`. On the next screen change: the spec carries a `Mock:` line, naming a file or "none". Measured before and after, an adaptation of the article's leading indicator (p.12: the time from the first conversation to a committed intent.md, read from git): git records no conversation, so the session recommends measuring from the intent's first commit (on the staging route, the owner's staging commit) to the intent PR's creation. The failure is an intent on `main` without a merged PR, an invented or colliding id, or a screen change whose spec has no `Mock:` line.

## What to settle before building

| Question | Recommended |
|---|---|
| Whether a project can override `intent-template` for `/sdlc-plan` (the entry's first open item) | To verify, as the entry says; the session suggests the sample: whether a project skill of the same name wins over the plugin's namespaced one in a `/sdlc-plan` session. The session's recommendation: the copy lives where R27 (T1's policy sources) puts a project's own sources if that place covers this skill, else under `.claude/skills/intent-template/`, a guardrail path the owner changes in a reviewed PR (decision 6); additions only, while the gate reads `INTENT_SECTIONS` |
| How an intent written in claude.ai gets its change id and folder (the entry's second open item) | The session's recommendation, a staging route with no model: (1) the conversation, after the analyst's questions, commits the draft through the connector to a staging branch, `sdlc/new/<slug>`, as `changes/new-<slug>/intent.md`, its header reading "Change id: to be allocated"; (2) a small workflow on that push checks that the pusher is the owner's account (the shared owner check R17 introduces) and that the commit touches that one file and nothing else, then runs `new-change` as `/sdlc-plan` does, moves the file into the allocated folder, writes the id into the header, commits on `sdlc/<id>/a` on top of the owner's own commit (so "author and timestamp join the record", p.11), pushes, runs `pr/cli.py upsert --phase a` and deletes the staging branch, under one concurrency group so two pushes never take the same id; (3) a refusal publishes nothing and ends red with its reason, for R18's "Failed runs" line; nothing notifies the owner (decisions 11 and 20). A PR the workflow token opens is not the owner's own, so "Request changes" would work on it (to verify on the sample). If the connector cannot write files, the fallback is an issue the owner labels, R31's route (T6). Never the conversation computing the id itself |
| What a claude.ai GitHub connector can do on the owner's account | To verify on the sample before the design (create a branch, commit a file, open a pull request or an issue, read the repository), recorded in `docs/notes/` |
| How the template reaches the conversation | The session's recommendation: the conversation reads it from the repository through the connector, the project's copy first, then the plugin's file at the version `sdlc.yaml` pins; to verify with the connector |
| Where the section sits and how it names a file | The session's recommendation: after "Open questions", before the incident-only Evidence; a link, or a file saved in the change folder (files there ride with the intent PR today) named by its path; screens the build must match go in `mock/`, never here |
| Whether the gate checks the new section | The session's recommendation: no at first. The section goes into the template; `INTENT_SECTIONS` is unchanged, so changes in flight and the detection's incident intents do not park on it |
| Whether the gate checks the `Mock:` line | The session's recommendation: no. Only the design pass knows whether a change touches a screen; the line is a rule in `spec-template` |
| How the `Mock:` line and the plan's Proof relate | **Settled by R14** (decision D2 of its revision, accepted 2026-10-13): the spec's `Mock:` names the target image, the plan's `screenshot` item names the file the drive writes, and the verifier compares them at (d) |
| Where the gate (a) briefs run for an intent written on the claude.ai route (R28 leaves it to this proposal and R31, `roles-and-manager.md:172`) | The session's recommendation: until R28 ships, the intent PR the staging workflow opens says "no role brief", as R28 has it for an intent not written through `/sdlc-plan` (a missing brief is shown, never parks). Once R28 ships, the staging workflow, which runs no model, dispatches a run after `upsert` that writes the Product and Architect briefs on `sdlc/<id>/a`, as R31 has them run in its intake run after the intent is written (`tickets-become-intents.md:95`); dispatched explicitly, since a push or PR made with the workflow token starts no workflow run |
| Whether the roles read the examples | T2's open item, inside R28 |
| The Product brief's decision 11 question | T1's, inside R28 |
| A Claude Code web session's `claude/...` head (HANDOFF 4(a)) | Unchanged here: that is the `/sdlc-plan` route; the owner's `sdlc/<id>/a` rule binds the claude.ai route |
| The names: the section, `sdlc/new/<slug>`, the workflow, `/sdlc-plan` | Judged with R45 (T4), under which `/sdlc-plan` becomes `/sdlc-intent`; the names here are placeholders |

## Considered and not chosen

- **The article's `intent/` folder** (p.10): decision 10 kept `changes/<id>-<slug>/`, and the owner kept it at setup-home.
- **A dedicated intent repository**: "only worth the overhead when intent spans many repositories" (p.10), not this case (decision 10).
- **The claude.ai route in place of `/sdlc-plan`**: the owner chose a second route, nothing replaced.
- **A commit to `main` from claude.ai**, the article's literal "commit to the shared home" (p.11): the owner's account bypasses the ruleset (decision 4), so it would skip gate (a); the owner requires the PR.
- **A required mock for every screen change**, the article's front-end flow as a rule (p.12-13): considered and not chosen at design-mock; a missing mock never blocks.
- **The conversation computing the next id through the connector** (the session's addition): the template forbids an invented id, and it would miss the remote `sdlc/<id>/*` heads that `new-change` counts.

## Decisions it touches

None is amended, so no decision file is written and no number is reserved. 8, 9 and 10 are kept (the plugin and the template, the repository as the record, the folder and the branch). 4 is kept and is why the claude.ai route is a PR. 6 is read: under `.claude/skills/` the copy is a guardrail the owner changes in a reviewed PR; R27's place is R27's to settle. 22 is kept (corrections at (a) are a fix round). 11 and 20 are kept (a refused staging push is a red run, never a notification). 23 is kept (the connector is GitHub's). 27, 28 and 29 are not touched. The Product brief's decision 11 question is R28's.

## Order

In the confirmed order (the record, section 8, part 2) T3 is in "the rest in any order", after the roles (R27, R28). *[2026-10-20: R29 part 1 is rank 14 (with R54), before R27 (19) and R28 (21); only the parts that need them wait; the rank is read from ROADMAP's Order column]* The parts it takes:

| Part | Where | When |
|---|---|---|
| The Examples/References section and the build's rule | `plugin/skills/intent-template/SKILL.md`, `plugin/commands/sdlc-build.md` | Any time, a plain change with no runner code |
| The mock question and the `Mock:` line | `plugin/commands/sdlc-plan.md` step 1, `plugin/skills/spec-template/SKILL.md` | The same change; R14 reads the line once it is built |
| The template override | `/sdlc-plan`, the place R27 gives a project's sources or `.claude/skills/` | After the live check; with or after R27 |
| The claude.ai route: the connector check, the allocation (recommended, not decided: the staging workflow) | `docs/notes/`, `template/.github/workflows/`, `/sdlc-init` | After the live check; after R17, whose owner check it calls; the allocation step shared with R31 if both are built |
| The Product brief at gate (a) and on a template change (R28's part 6, `roles-and-manager.md:215`); the roles reading the examples | R28 | With R28 |
| The gate (a) briefs on the claude.ai route (recommended: a run the staging workflow dispatches) | `template/.github/workflows/` | With R28 and the claude.ai route, whichever comes later |
| The names | R45 | Last |

[^crosswalk]: `docs/reviews/2026-09-28-playbook-vs-framework/crosswalk.json`, rows setup-home, plan-idea and design-mock, and `target-design.md` T3.
[^playbook]: `docs/reference/ai-native-sdlc-playbook.pdf` p.10-13.
[^drive-target]: `docs/proposals/drive-target-and-proof.md`, the settle row "How the `Mock:` line (T3) and the `screenshot` item relate", D2 accepted 2026-10-13.
