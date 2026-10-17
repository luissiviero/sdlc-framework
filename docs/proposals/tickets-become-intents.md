---
type: Proposal
title: "Tickets become intents: a GitHub issue the owner labels starts the intent PR"
description: Beside today's routes, which all stay, the owner's label sdlc:intent on a GitHub issue starts a CI run that writes intent.md from the issue (entry route ticket, the issue as its external reference), puts what it cannot work out under "Open questions" and opens the intent PR linked to the issue, which the owner corrects and merges at gate (a) as today; only the owner's own label starts a run, and the issue text is read as data, never as instructions.
status: proposed
roadmap: R31
sources:
  - id: study-entry
    resource: docs/reviews/2026-09-28-playbook-vs-framework/target-design.md
    title: "T6, confirmed at the close of the study on 2026-10-09; from the crosswalk row plan-ticket (better: the playbook; decision: blend), 2026-10-02, with the owner's note"
  - id: crosswalk
    resource: docs/reviews/2026-09-28-playbook-vs-framework/crosswalk.json
    title: "Row plan-ticket (whole); the decision fields of maintain-tag (tickets enter through T6; a chat entry route not chosen) and plan-idea (the other intent routes, T2 and T3)"
  - id: artcraft
    resource: docs/reviews/2026-10-13-artcraft-vs-framework.md
    title: "Rows A4 and A9 and gap G8; planning-revision.md section 4 (4.3 to 4.7: T6, the project's front door stays the intent); templates-revision.md E6 (a ticket's regression joins T28's sort key when T6 gives tickets a label)"
  - id: playbook
    resource: docs/reference/ai-native-sdlc-playbook.pdf
    title: "p.9: intent.md enters by an idea, a ticket or an alert, and the product owner reviews and corrects the agent-written intent before it is committed; p.42: a ticket invokes Claude without a person in the path; p.44 step 5: the agent's intent lists any open questions; p.49: tagged on a ticket, Claude writes larger work up as intent.md"
  - id: decision-9
    resource: docs/decisions/9.md
    title: "Decision 9: the repository is the source of truth, GitHub Issues hold links (followed, not amended)"
  - id: decision-24
    resource: docs/decisions/24.md
    title: "Decision 24: the owner's verbs are labels, recorded with the label's actor (the new label sits beside them; kept)"
  - id: decision-22
    resource: docs/decisions/22.md
    title: "Decision 22: the owner's \"Request changes\" review starts the fix round, on an intent PR as on any other (kept)"
  - id: decision-25
    resource: docs/decisions/25.md
    title: "Decision 25: closing a PR at (a) to (e) abandons the change (kept)"
  - id: code
    resource: template/.github/workflows/
    title: "The twelve workflow templates' triggers and permissions; plugin/commands/sdlc-plan.md; plugin/skills/intent-template/SKILL.md; plugin/state/cli.py new-change; plugin/state/conventions.py; plugin/pr/description.py; plugin/ci/run_phase.py PHASE_COMMAND, FIX_PHASES and the tool lists; plugin/detect/cli.py and plugin/scan/route.py (the intents CI writes today); read at main 5542406, plugin 1.0.1"
generated: { by: sdlc-framework-session/ccr-01de3f80-ilnomi, at: 2026-10-15T20:00:00Z }
---

# Tickets become intents: a GitHub issue the owner labels starts the intent PR

**Status: proposed (roadmap R31), from study entry T6, confirmed by the owner on 2026-10-09.** Nothing is built. It amends no decision: decision 9's linkage rule is followed and the new label sits beside the owner's other labels (decisions 3 and 24, as amended by 27 and 28), so no decision file is written and no number is reserved. It adds a fourth way into a project beside the three of today, all of which stay; the act it adds is recorded by R11 and listed by R19, and its pull requests are placed by R20.

## The problem

The owner wants to start using GitHub issues as the place where tickets arrive[^entry]. Today an issue reaches the framework only through the owner's own session:

- **A ticket becomes an intent only by hand.** The owner opens Claude Code, runs `/sdlc-plan`, answers the brainstorm, gives route `ticket` and the ticket's number, corrects the draft and lets it open the PR (`plugin/commands/sdlc-plan.md:30-31`, `:41`, `:62`). The command is interactive by construction: "This is the only interactive phase" (`:11`), its tools end in `AskUserQuestion` (`:5`), and step 4 shows the draft and repeats "until the owner says it is right" (`:50-51`), so it cannot run unattended.
- **No workflow runs on an issue.** The twelve workflow templates name `issues` only as a token permission, never as a trigger (verified below).
- **The issue and the intent PR do not point at each other.** The ticket number reaches the intent's header and `status.yaml: external_ref` (`plugin/skills/intent-template/SKILL.md:45-46`), but the PR body's route bullet names the route alone (`plugin/pr/description.py:337`), so the issue shows nothing of the change that came from it.

Alerts, by contrast, already become intents with no person: the detection and the weekly scan write the incident intent and open its PR. Of the article's three entry routes (p.9), the ticket is the one where the request already exists in writing and still waits for the owner to start a session.

## What the article says

The intent "can enter through different routes. A person has an idea, a ticket is filed, or an incident is surfaced via an alert", and "regardless of whether the intent originates from an event trigger or an agent, the same steps apply: the product owner reviews and corrects the agent-written intent.md before it is committed" (p.9). In the maintenance stage "a continuously running monitoring agent could, off the back of a bug ticket being raised, create an intent.md"; "a trigger such as a control-band breach, a ticket, a channel message or a schedule invokes Claude without a person in the path", and people "triage and review that work, and no longer have to start it" (p.42). The agent's intent covers "the anomaly and its evidence, a proposed outcome, the affected systems and any open questions" (p.44 step 5). Tagged on a ticket, Claude writes anything larger than a small fix "up as intent.md for Stage 1: Plan" (p.49)[^playbook].

The owner's blend keeps the article's review before commit (the intent PR, merged at gate (a)) and departs from "without a person in the path" in one place: the run starts on the owner's own label, not on the ticket being filed, because anyone can open an issue on a public repository.

## What the framework does today

Read at `main` 5542406, plugin 1.0.1 (`.claude-plugin/plugin.json:4`). The entry's "Today" was read at 619f01a (plugin 0.3.5). `git diff --stat 619f01a 5542406` over `plugin/commands/sdlc-plan.md`, `plugin/skills/intent-template/SKILL.md`, `plugin/state/`, `plugin/pr/cli.py`, `plugin/pr/description.py`, `plugin/scan/route.py` and `template/.github/workflows/` touches `plugin/pr/description.py` only (the PR body's first sentence, 19 lines added and 8 removed), so the entry's "Today" still holds[^code].

- **No issue trigger** (verified). The triggers at 5542406: `workflow_dispatch` on every template but abandon and runbook; `pull_request` (`closed` or `labeled`) on design, build, test, deploy, fix, abandon, runbook and release, and `pull_request` with the default types, filtered by branch and path, on evals (`sdlc-evals.yml:29-34`); `pull_request_review` on fix; `schedule` on detect, digest, scan and evals. `issues` appears only under `permissions:` (`sdlc-build.yml:39`, `sdlc-deploy.yml:35`, `sdlc-design.yml:37`, `sdlc-detect.yml:58`, `sdlc-digest.yml:31`, `sdlc-fix.yml:59`, `sdlc-runbook.yml:34`, `sdlc-scan.yml:44`, `sdlc-test.yml:35` as `write`; `sdlc-release.yml:68` as `read`).
- **The ticket route by hand** (verified). `/sdlc-plan` asks for the entry route and, for a ticket, its number (`sdlc-plan.md:30-31`); `state/cli.py new-change --route ticket --external-ref <n>` allocates the change (`sdlc-plan.md:41`), with an id above every local folder and every remote `sdlc/<id>/*` branch (`plugin/state/cli.py:52`), and stores `external_ref` (`plugin/state/status.py:56`, decision 9's linkage). The intent's header reads `Entry route: idea | ticket <number> | incident <reference>` (`SKILL.md:18`); "Open questions" is a fixed section, "none" allowed (`SKILL.md:32-33`). `pr/cli.py upsert --phase a` opens the PR on `sdlc/<id>/a` with the label `sdlc:a-ready` (`sdlc-plan.md:62-69`).
- **Intents CI already writes** (verified). The detect step files an incident change with `new-change --route incident` (`plugin/detect/cli.py:472`) and the maintain session writes its intent, read-only on source, the gate's `design_scope` check refusing anything committed outside the change folder (`plugin/ci/run_phase.py:195-198`); the scan writes an intent per routed finding with no model and opens its PR (`plugin/scan/route.py:471`, `:516-517`). The runner has no phase for (a): `PHASE_COMMAND` runs b to f and the fix round (`run_phase.py:135-146`); a fix round may run on the PR of any phase from (a) (`FIX_PHASES`, `:157`).
- **Labels and actors** (verified). The labels the framework creates are listed in `conventions.all_labels()` (`plugin/state/conventions.py:108`), created by a real run (`run_phase.py:295-308`, `:1739`) and by `upsert` for its gate label; the entry routes are `idea`, `ticket`, `incident` (`conventions.py:61`). No label names an issue. The actor checks reject the automation identity and any `[bot]` (`plugin/state/unpark.py:59-65`; `plugin/release/approval.py:116`); none names the owner, and no `sdlc.yaml` key or `is_owner` function exists (`git grep` for `is_owner`, `repository_owner` and `^owner:` over `plugin` and `template` finds nothing).
- **Who may correct the intent PR** (verified). The fix workflow's job takes a "Request changes" review by a non-`[bot]` `OWNER`, `MEMBER` or `COLLABORATOR` (`sdlc-fix.yml:76-87`).
- **The owner's review on an automation's PR** (not verified). An intent PR the automation opens is not the owner's own PR, so GitHub's refusal of "Request changes" on the reviewer's own PR (`docs/notes/29.md`, cited by R17) should not apply to it, as the owner's note expects of today's incident intent PRs.
- **Not covered by any note:** which workflow file an `issues` `labeled` run uses, which account the event names as the label's actor, and what its token holds on a public repository (`grep -rn "sender" docs/notes/` finds nothing). Notes 11 (`docs/notes/11.md:150`, every label trigger needs the workflow file on the default branch) and 3c (a `pull_request` `labeled` run uses the PR head's copies) cover the `pull_request` label trigger, not `issues`. To verify.

## The proposal

Added beside the routes of today; nothing replaced. Alerts stay as today (the detection and the weekly scan write the incident intent and open a PR, which the owner corrects with "Request changes" and triages), and `/sdlc-plan` with route `ticket` stays (the owner's note)[^entry].

1. **The trigger.** Tickets arrive as GitHub issues. The owner applies the label `sdlc:intent` to an issue. A new workflow runs on that event and checks that the label was applied from the owner's account, not merely by a person (the check T1 asks for every approval); any other actor starts nothing.
2. **The run.** It writes `changes/<id>-<slug>/intent.md` with entry route `ticket` and the issue as its external reference, then opens the intent PR on `sdlc/<id>/a`, linked to the issue. What the run cannot work out goes to the intent's "Open questions".
3. **The owner's acts are those of today.** The owner corrects the intent in the PR (review comments, or a "Request changes" review that starts the fix round, decision 22) and accepts it by merging at gate (a). Closing the PR abandons the change (decision 25).
4. **The issue text is data, never instructions.** Anyone can open an issue on a public repository, so the run treats the title and body as quoted input, and only the owner's label starts it. How the run is told so and which tools it may use are open; see "What to settle".
5. **The record.** `intent.md` in the repository stays the record and the issue holds the link (decision 9's linkage rule).
6. **Example.** Issue #12 "Export the report as CSV"; the owner labels it `sdlc:intent`; the run writes `changes/0010-export-csv/intent.md` and opens the intent PR linked to #12.
7. **The front door stays the intent.** An issue is not a work list the agents pick from: nothing runs on an issue without the owner's label, and the work enters as an intent the owner accepts at gate (a) (ArtCraft planning revision 4.3 to 4.7; row A4's "agents take the top item" not taken)[^artcraft].

How the run is built (which step allocates, which writes, how it parks, how the PR points at the issue) is left to "What to settle", where every answer beyond the entry is marked as this proposal's recommendation.

## How it is judged

On the sample, after it ships: the owner labels an issue and, with no session opened, an intent PR on `sdlc/<id>/a` appears with route `ticket`, the issue's number in the header and in `status.yaml: external_ref`, and the issue showing the PR; what the issue left unclear is under "Open questions"; the owner corrects it with one "Request changes" review and merges it, and the design run follows as for any intent. The failures: a run started by a label from any account but the owner's; an intent or a commit that does something the issue's text told it to do rather than describes it (checked with an issue whose body carries an instruction to the model); anything committed outside the change folder. Measured before and after: the owner's acts from a filed ticket to an open intent PR, today a session with a brainstorm and a correction loop, after it one label.

## What to settle before building

The entry's three open items come first; the rows after them are this proposal's own (marked "mine").

| Question | Recommended |
|---|---|
| Whether a ticket intent gets T2's role-fed interview (the entry) | No interview in the run: a CI run cannot interview the owner, so its questions go to "Open questions" in the PR (the entry's reasoning, taken here as the recommendation). Mine: once R28 (T1 with T2) ships, the questions its roles would ask are written there too, and the owner answers them by correcting the intent in the PR |
| Where the gate (a) role briefs run for a ticket intent (mine; R28 leaves it to R31) | The intake run writes none; until R28 ships and settles it with this proposal, the ticket intent PR says "no role brief", as R28 has it for an intent not written through `/sdlc-plan` (`docs/proposals/roles-and-manager.md:173`). Once R28 ships, the briefs run in the intake run after the intent is written, as R28 has the roles review the draft in `/sdlc-plan` (`roles-and-manager.md:135`) |
| How the run is told the issue is untrusted, and which tools it may use (the entry) | The phase jobs' sandbox and settings, as today (the entry). Mine: the workflow writes the title and body to a file through the environment, never into a `run:` line (`plugin/skills/security-baseline/SKILL.md`, rule 2) nor into the prompt's instructions; the prompt names the file as quoted input from a person who may not be the owner; the session gets `Read`, `Grep`, `Glob` and `Write` only (no `Bash`, no `Edit`, no web tools); the runner, not the session, allocates the change, commits and opens the PR; anything written outside the change folder is refused, as the maintain run's `design_scope` check does (`run_phase.py:195-198`) |
| The label's name (the entry) | Judged with T4 (R45) with the other names; `sdlc:intent` is the owner's word and stands until then. Mine: under T4's phase names the gate label of (a) would read `sdlc:intent-ready`, close to it, which R45 should weigh |
| How the owner's account is known | **Settled by R17** (accepted 2026-10-14, PR #208, point 3): the repository owner by default, `sdlc.yaml: owner` for an organization repository, one shared function `is_owner_actor`, fail closed. This run calls it; whichever of R17 and R31 ships first adds it |
| How the run is built (mine) | A non-interactive variant of the plan step run by the runner with its guards, spend record and park (`/sdlc-plan` itself is interactive, `sdlc-plan.md:11`, `:50-51`); the deterministic steps are today's CLIs: `new-change --route ticket --external-ref <n>`, `commit-phase --phase a`, `upsert --phase a`; one concurrency group for the allocation, shared with R29's staging workflow if both are built (`intent-home.md:97`, `:132`), so two labels, or a label and a staging push, at once cannot take the same id |
| How the PR points at the issue (mine) | The issue number in the intent's header and in `external_ref`, as today, and a `Refs #<n>` line in the PR body, so GitHub shows the PR in the issue's timeline; no closing keyword (merging an intent ships nothing) and no comment on the issue (decision 20). Whether the cross-reference notifies the issue's author: to verify |
| One issue, one change (mine) | The runner removes the label after the PR opens, so one application is one act (as decision 24's labels are performed and removed); a label on an issue whose change is still open is a green skip with its reason; after an abandon (decision 25) a new label starts a new change |
| When the run cannot finish (mine) | The intent PR is opened anyway with what was written, parked with `sdlc:needs-human` and "what I need from you"; a failure before the branch exists is a red run for R18's "Failed runs" line; never a comment on the issue (decisions 11 and 20) |
| The change type and the profile (mine) | The run proposes `feature` or `fix` from the issue and uses the project's profile and review mode; the owner corrects in the PR. Whether a fix round at (a) may rewrite `change_type` under the runner's owner-only-fields check (choice 103, `run_phase.py:1740-1767`): to verify |
| The label R20's sort needs (mine) | The accepted fold E6 leaves this label to T6: "a ticket's regression joins the first key when T6 gives tickets a label" (R20; T28's annotation of 2026-10-14; ArtCraft row A9)[^artcraft]. The runner labels a ticket intent PR `ticket`, from the route, beside `sdlc:a-ready`, and adds `regression` when the run finds that the issue reports something that worked in a shipped version and no longer does (a model judgment, said so in the PR body); the owner removes or adds `regression` in the PR. R20's first key reads `regression` beside `incident`. Not `incident` reused: the digest reads `incident` without a gate label as a phase (f) runbook or dismissal PR (`plugin/pr/digest.py:71-74`) |
| What an `issues` `labeled` run uses and holds | To verify on the sample before the design, recorded in `docs/notes/`: the workflow file (the default branch's, expected), the label's actor in the payload, that a label on a pull request does not start it, the token on a public repository |

## Considered and not chosen

- **Tickets stay manual** (the row's question: "is an automatic 'issue labelled X → intent PR' trigger worth adding, or do tickets stay manual?"): the owner chose the trigger, "better: the playbook"[^crosswalk].
- **Replacing a route of today**: "added and nothing replaced"; alerts and `/sdlc-plan` with route `ticket` stay (the owner's note).
- **A run on every new issue, with no person in the path** (the article's p.42 trigger): only the owner's own label starts a run (the owner's safeguard).
- **A label applied by any person**: the workflow checks the label came from the owner's account, "not merely by a person".
- **The issue as the record**: decision 9's option 2, not accepted; the issue holds the link[^decision-9].
- **A chat entry route now** (option C of the row maintain-tag): not chosen there; tickets enter through T6 and intents from anywhere through T3 (R29)[^crosswalk].
- **An agent work list ranked from the issues** (ArtCraft row A4, 4.5): no agent picks its own work here; the front door stays the intent[^artcraft].

## Decisions it touches

None amended, so no decision file and no number. 9 is followed (the repository is the record, the issue holds the link); 3 and 24, as amended by 27 (the gate label alone, with its actor) and 28 (the accept label), are kept, the new label sitting beside the owner's other labels; 22 is kept (the "Request changes" round on the ticket intent PR, unchanged); 25 is kept (close abandons); 11 and 20 are kept (a park, never a comment or a notification); 5 is kept (the workflow token opens the PR, as for the incident intents); 23 is kept (issues are GitHub's). Beyond the labels the new one sits beside, decisions 27 and 28 govern gates (c) to (e), and 29 the automatic rounds after a red target; this proposal changes none of them. One contract sentence changes, no decision: `docs/OPERATING_MODEL.md:117` says phase (a) writes intent.md "interactively with the owner", with decision 22's fix round as its one exception; the intake run writing a new intent.md from the owner's labelled issue is a second exception, written into that sentence by the change that builds it.

## Order

In the study's "rest in any order" group (the record, section 8 part 2: T3, T5, T6, T7, T8, ...); the Order column is the owner's. It depends on no other proposal to be built. It adds a workflow to `template/` and a run to `plugin/`, so it ships as a plugin version with tests and reaches a project through `/sdlc-init`'s workflow copies; a change to `plugin/ci/run_phase.py` goes on HANDOFF's port list while that rule stands (`HANDOFF.md:41`). Related, not blocking: R17 (the owner check, shared), R22 (T18's entry has the step that opens T6's ticket intents post the `sdlc/review` check itself), R11 (the label recorded with its actor), R19 (the PR's "What you can do here" block), R20 (the `regression` label in its first sort key), R25 (T30's budget covers the run), R28 (the roles' briefs and questions at gate (a)), R29 (T3, the other new intent route; the allocation step and its concurrency group shared with R29's staging workflow if both are built), R32 (T7, the closing reason, for ticket intents as for any), R44 (T29's sandbox), R45 (the label's name).

| Part | Where | When |
|---|---|---|
| A live check of an `issues` `labeled` run on the sample, recorded in `docs/notes/` | the sample repository | First |
| The intake workflow (`issues` `labeled`, the label and owner checks, the issue text to a file) | `template/.github/workflows/`, `/sdlc-init` | Now |
| The non-interactive intake run and its tool list; `sdlc:intent`, `ticket` and `regression` in `all_labels()` | `plugin/ci/run_phase.py` or a script beside it, `plugin/commands/`, `plugin/state/conventions.py` | Now |
| `Refs #<n>` in the intent PR's body | `plugin/pr/description.py` | Now |
| `is_owner_actor` | `plugin/state/unpark.py` | With R17, or here if this ships first |
| The passing `sdlc/review` ("not a build PR") check on the intent PR, posted by the intake step (through R22's `upsert` change when R22 is built first) | the intake run, `plugin/pr/cli.py upsert` | Now if R22 is built; else when R22 lands, which adds it to the steps that open automation PRs |
| The act on the record; the PR's block; the sort key | R11; R19; R20 | With each |

[^entry]: `docs/reviews/2026-09-28-playbook-vs-framework/target-design.md`, T6 (Status, the owner's note, "Today", "Direction discussed", "Open"); the record `docs/reviews/2026-09-28-playbook-vs-framework.md`, section 7 (the row plan-ticket) and section 8 part 1 (the close table's row "T6 Tickets become intents | plan-ticket | none | yes | yes").
[^playbook]: `docs/reference/ai-native-sdlc-playbook.pdf` p.9, p.42, p.44, p.49.
[^code]: `template/.github/workflows/*.yml`; `plugin/commands/sdlc-plan.md`; `plugin/skills/intent-template/SKILL.md`; `plugin/state/cli.py`, `status.py`, `conventions.py`, `unpark.py`; `plugin/pr/description.py`; `plugin/ci/run_phase.py`; `plugin/detect/cli.py`; `plugin/scan/route.py`; all at 5542406.
[^crosswalk]: `docs/reviews/2026-09-28-playbook-vs-framework/crosswalk.json`, row plan-ticket (its `weigh` and `decision`), and the decision field of maintain-tag.
[^decision-9]: `docs/decisions/9.md`.
[^artcraft]: `docs/reviews/2026-10-13-artcraft-vs-framework.md`, rows A4 and A9 and gap G8; `docs/reviews/2026-10-13-artcraft-vs-framework/planning-revision.md`, section 4 (4.3 to 4.7) and 4.5; `templates-revision.md`, E6 and row 9.2; R20, `docs/proposals/digest-needs-you-first.md`.
