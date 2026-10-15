---
type: Proposal
title: Names — the phases named after what they produce, and the other names judged against the article
description: The phases are named intent, design, build, test, deploy and maintain in branches, labels and status.yaml instead of the letters (a) to (f), so /sdlc-plan becomes /sdlc-intent and "plan" means only plan.md; the other names follow the 23-row table of naming.md (the framework's name kept where it says more, the article's taken for the people who decide and for the triage queue, a third name where neither is good), with the names the other proposals left to this entry judged by the same rule, last, after every other change has landed, but for the approvals line's keys, which the accepted R11 has judged before its design.
status: proposed
roadmap: R45
sources:
  - id: study-entry
    resource: docs/reviews/2026-09-28-playbook-vs-framework/target-design.md
    title: "T4, recorded 2026-09-30 from the owner's questions, confirmed at the close of the study on 2026-10-09 and placed last; the owner's rule for the entry"
  - id: naming
    resource: docs/reviews/2026-09-28-playbook-vs-framework/naming.md
    title: "The 23-row table of names with the reason for each, the summary and \"If a row is accepted\" (order, timing, compatibility, guardrail files)"
  - id: record
    resource: docs/reviews/2026-09-28-playbook-vs-framework.md
    title: "Section 7, first bullet (the close, T4 last); section 8, part 1 (the close table's T4 row) and part 2 (the format and the confirmed order)"
  - id: crosswalk
    resource: docs/reviews/2026-09-28-playbook-vs-framework/crosswalk.json
    title: "No row for names (naming.md); the decision fields of build-start (the per-change Full label, name judged with T4) and build-skills (the policies/ folder, name judged with T4), and the decision kinds of setup-home, plan-idea, build-plan, test-evals, maintain-triage, maintain-scan, maintain-act, deploy-release and x-roles"
  - id: artcraft
    resource: docs/reviews/2026-10-13-artcraft-vs-framework/framework-target-summary.md
    title: "T4's summary, items (a) to (d); no ArtCraft row folds into T4"
  - id: playbook
    resource: docs/reference/ai-native-sdlc-playbook.pdf
    title: "p.7 the six stages; p.8 the dependency graph (PLAN: Capture intent; BUILD: Plan mode); p.9-11 Stage 1, the intent home and Status: draft; p.15-16 plan mode; p.21-22 skills; p.29, p.33 code owner; p.30 agent-evals.yml; p.32, p.40-41 the production gate; p.37, p.40-41 the release manager; p.36 allow, ask or block; p.42 escalated to a human; p.43 a preapproved runbook; p.44-45 findings and the triage queue; p.49 Go"
  - id: decisions
    resource: docs/decisions/index.md
    title: "Decisions 3 (as amended by 27), 10, 11, 13, 14 (as amended by 26), 18, 19, 25 and 26, whose names change and whose substance does not (the entry's list); 21 (the `escalate` verdict) and 22 (the `sdlc/<id>/a` head, `sdlc-plan.md`), which also carry a renamed name (this proposal's finding); 2 kept; 27, 28 and 29 read"
  - id: code
    resource: plugin/state/conventions.py
    title: "PHASES, PHASE_NAMES, PROFILES, LEGACY_PROFILES, HUMAN_GATES, the labels and BRANCH_RE; with plugin/gate/checks.py (the verdict), plugin/gate/artifacts.py, plugin/skills/intent-template/SKILL.md, plugin/detect/bands.py, template/sdlc.yaml, template/.github/workflows/, plugin/commands/sdlc-plan.md, plugin/pr/cli.py, plugin/pr/digest.py, docs/OPERATING_MODEL.md; read at main 5542406, plugin 1.0.1"
generated: { by: sdlc-framework-session/ccr-01de3f80-ilnomi, at: 2026-10-15T20:00:00Z }
---

# Names — the phases named after what they produce, and the other names judged against the article

**Status: proposed (roadmap R45), from study entry T4, confirmed by the owner on 2026-10-09.** Nothing is built. It changes the names, not the substance, of decisions 3 (as amended by 27), 10, 11, 13, 14 (as amended by 26), 18, 19, 25 and 26; the decision file comes before the intent, in a documentation PR of its own; this proposal writes no decision file and reserves no number. Decisions 21 and 22 also carry a name that changes ("Decisions it touches"). It is the last of the study's proposals by the owner's confirmed order (a rename across the plugin, the template and the docs, cheapest once the other changes have landed), and it also judges the names the other proposals left to it as placeholders.

## The problem

The owner asked on 2026-09-30 why the framework keeps changes in `changes/` and not in the article's `intent/`, which other names differ, and which name is better in each case, judged on the name alone, whatever decision approved it[^entry]. The answer is a table of 23 rows, each with its reason[^naming]. Its findings:

- **The phases are letters.** Branches (`sdlc/0001/b`), labels (`sdlc:c-approved`) and `status.yaml: phase` carry (a) to (f), so every reader keeps a table in their head; "Stage 3" in the article is the same kind of code.
- **"Plan" means two things.** `/sdlc-plan` is phase (a) and writes `intent.md`, while `plan.md` comes out of `/sdlc-design`. The clash starts in the article: its "Plan" stage does not produce `plan.md` either, which is written in Build's plan mode play (p.15-16), and its own dependency graph names the Stage 1 play "Capture intent" (p.8). Whoever knows the article looks for `plan.md` in the wrong phase twice.
- **One name is wrong today, not only unclear.** The intent's header line carries `Status: draft | proposed | accepted`, frozen at whatever it said when the intent PR merged, beside `status.yaml`, the change's real status. In the sample project change 0001 says `Status: draft` at phase `e`.
- **Other names mislead or hide what they name:** the verdict `escalate` (it suggests paging, which decision 11 rules out), `incident` for every triage item (a weekly scan finding is not an incident), `authorization: preapproved | go`, `deploy.production: true` (it reads as "this is production"), `ux-conventions` (it hides the brand rules), the profile `full`, the workflow `sdlc-evals.yml`, and "the owner" where the article names the role that decides.

**The owner's rule for this entry:** a name that confuses is not kept because renaming costs something. Either one side's name is better, or a third name is needed. The cost, and the decisions behind the current names, are listed apart for the owner to weigh[^entry].

## What the article says

- **The stages** are Plan, Design, Build, Test, Deploy, Maintain (p.7); cross references also say "Stage 6: Maintenance" (p.9, p.18, p.42). The dependency graph labels the Stage 1 play "Capture intent" and puts "Plan mode" under Build (p.8, the image `docs/reference/playbook-p8-dependency-graph.png`, read for this proposal).
- **The home of intent** is "an intent/ folder" for a single product (p.10). The intent's header line is "Author: J. Ortiz (claims operations). Status: draft." (p.11).
- **Plan mode** is an interactive Claude Code session in which "the engineer starts the session in plan mode with Claude" (p.15-16).
- **The people who decide** are named by role at each point: the product owner reviews and approves the intent (p.9, p.11), the code owner reviews and approves the PR (p.29, p.33), the release manager authorizes production (p.37, p.40-41), the service owner triages (p.44).
- **Hand-off and authorization words:** a headless stage "continues or is escalated to a human" (p.42); a hook "can allow, ask, or block" (p.36); a "preapproved runbook" (p.43); the owner's "Go." (p.49, an image).
- **Triage:** the items are "findings", the owner's verbs are "Fix now, schedule, or dismiss" (p.44), and they sit in "the triage queue" (p.45).
- **The eval workflow** is `.github/workflows/agent-evals.yml` (p.30); the skills' example is `secure-api-review` (p.22), and the policies are "brand, security, compliance, and UX" (p.12-13); the gate is "the production gate" (p.32, p.40).

## What the framework does today

Read at `main` 5542406, plugin 1.0.1 (`.claude-plugin/plugin.json:4`). The entry and `naming.md` were written at 2026-09-30, before 619f01a (plugin 0.3.5). `git diff --stat 619f01a 5542406` over `conventions.py`, `status.py`, `state/cli.py`, `bands.py`, `routes.py`, `gate/checks.py`, `gate/artifacts.py`, `gate/limits.py`, `pr/cli.py`, `pr/digest.py`, `adversarial-reviewer.md`, `intent-template/SKILL.md`, `ux-conventions/SKILL.md`, `sdlc-plan.md`, `production_gate.py`, `template/sdlc.yaml`, `template/bands.yaml` and `template/.github/workflows/` touches only `plugin/gate/checks.py` (+94, the incident lesson check), `plugin/gate/artifacts.py` (+30, the lesson fields) and `template/sdlc.yaml` (+7, a commented `lessons:` block); `git log 619f01a..5542406` over the first two files agrees. No name in the table changed. Verified at 5542406:

- **Phases are letters.** `PHASES = ("a", "b", "c", "d", "e", "f")` (`plugin/state/conventions.py:13`); the readable names exist only as a lookup, with (a) named `plan` (`:18-25`). Labels are built from the letter: `sdlc:<letter>-ready` and `sdlc:<letter>-approved` (`:96-105`, `all_labels` `:108-115`); branches match `^sdlc/(?P<id>\d{4})/(?P<phase>[a-f])$` (`:119`); `status.yaml: phase` must be a letter or `abandoned` (`plugin/state/status.py:106-108`). The workflows' guards test the letter labels by name (`template/.github/workflows/sdlc-test.yml:51`, `sdlc-deploy.yml:52`). The check runs are `sdlc/{phase}` (`plugin/pr/cli.py:43`) and the evidence files `gate-{phase}.json`, `adversarial-review-{phase}.json` (`plugin/gate/artifacts.py:72-73`) and `run-{phase}.json` (`plugin/gate/limits.py:50`).
- **`/sdlc-plan` is phase (a)** and writes `intent.md` (`plugin/commands/sdlc-plan.md:2`).
- **The intent's `Status:` line** is in the template (`plugin/skills/intent-template/SKILL.md:18`) and required by the gate's artifact check (`plugin/gate/artifacts.py:29`). In the sample project's local checkout (f88b262), `grep` gives: 0001 `Status: draft` at `phase: e`, 0002 `Status: proposed` at `phase: e`, 0005 and 0008 `Status: proposed` at `phase: f`.
- **The verdict word** is `continue | escalate` (`plugin/gate/checks.py:785-795`, `plugin/agents/adversarial-reviewer.md:3`, `:71`); the review panel's ledger keys on it (`checks.py:830-838`). The state is "parked" and the label `sdlc:needs-human` (`conventions.py:66`).
- **Triage labels** are `incident` and `schedule`, the only two without the `sdlc:` prefix (`conventions.py:91-92`); the weekly scan files its findings as incident intents with the label `incident` (`template/.github/workflows/sdlc-scan.yml:15-16`, `:98`). The entry routes are the article's `idea | ticket | incident` (`conventions.py:61`). Two code paths rely on the missing prefix: the digest's runbook and dismissal PR section keeps the PRs that carry `incident` and no `sdlc:` label (`plugin/pr/digest.py:71-79`), and each gate-label update removes every `sdlc:` label outside `OWNER_LABELS` other than the new gate label (`plugin/pr/cli.py:46`, `:151-156`).
- **Runbook authorization** is `preapproved | go` (`plugin/detect/bands.py:41`, `template/bands.yaml:34-40`); the Go label is `sdlc:go` (`conventions.py:93`).
- **The production switch** is `deploy.production` (`template/sdlc.yaml:53`), read by the production-gate hook (`plugin/hooks/production_gate.py:409`) and the state CLI (`plugin/state/cli.py:373`).
- **The UX skill** is `ux-conventions`, which covers UX and brand (`plugin/skills/ux-conventions/SKILL.md:2-3`).
- **The eval workflow** is `sdlc-evals.yml`, "SDLC evals" (`template/.github/workflows/sdlc-evals.yml:26`), one of twelve `sdlc-*.yml`.
- **Profiles** are `standard | full` (`conventions.py:41`); `full` makes (c) and (d) human on top of Standard's (a), (b), (e) and (f) (`:46-49`). An old value is already read as a new one: `LEGACY_PROFILES = {"lite": "standard"}` (`:43`), the precedent for every renamed config value.
- **The people who decide:** section 2 of `OPERATING_MODEL` already names the article's roles and says one person holds them all ("One person owns every role the article names (originator, product owner, tech lead, engineer, code owner, release manager, service owner)", `docs/OPERATING_MODEL.md:24`); the rest of the docs and the prompts say "the owner" at each decision point.
- **Size, a grep count at 5542406** (`git grep -l -E '<pattern>' 5542406 -- plugin template tests | wc -l`; an indication only, as `naming.md`'s 2026-09-30 counts were): letter labels 26 files (`sdlc:[a-f]-(ready|approved)`), letter branches 47 (`sdlc/[0-9<][^/ ]*/[a-f]\b`), `sdlc-plan` 11, `escalate` 16 (with `-w`), `preapproved` 10, `ux-conventions` 12, `sdlc-evals` 6, the `incident` label 17 (`INCIDENT_LABEL|"incident"`), the `schedule` label 9 (`SCHEDULE_LABEL|"schedule"`), `Status: draft` 4.

## The proposal

The table in `naming.md` is the proposal; this section condenses it. Row numbers are that table's.

1. **Keep the framework's name where it says more than the article's.** `changes/<id>-<slug>/` (row 1: a folder of five kinds of file, not only the intent; T3 keeps it too, R29). "Planning run" rather than "plan mode" (row 5: the run is headless and is not the interactive feature; "read-only" can go, the tool list already says it). "Park" (row 7): the adversarial reviewer's verdict becomes `continue | park`, so one event has one word; the state stays `parked` and the label `sdlc:needs-human`, the one form a GitHub visitor reads without context. `security-baseline` and the other skill names but one (row 10), the twelve `sdlc-*.yml` workflows (row 15), the spec sections (row 21), and `standard`, `deferred` and the un-park labels (row 23, but for `full`) stay. Rows 9, 11 to 13 and 18 to 20 (the agents, `evidence/`, the intent and plan sections among them) are equal or already the same, and stay unchanged.
2. **Take the article's name** for the people who decide (row 8): the article's role at each decision point ("the product owner merges the intent", "the code owner merges the build PR", "the release manager applies the release label"), with one sentence in `OPERATING_MODEL` that one person holds every role today; that sentence is already in section 2 (`docs/OPERATING_MODEL.md:24`), so the change is the role named at each decision point in the prose and the prompts. The one-owner premise is unchanged (x-roles, T1: the owner remains the only approver). And for the triage queue (row 16): the items are "findings", the labels `sdlc:triage` and `sdlc:schedule`; the verbs are already the article's. With the prefix, row 16 needs two code changes beyond the rename, since both paths rely on the triage labels lacking it: the digest's filter (`plugin/pr/digest.py:75`) and the gate-label sweep (`plugin/pr/cli.py:46`, `:151-156`). Without them the digest's runbook and dismissal section stays empty, and the next gate-label update removes the triage labels.
3. **A third name where neither is good.**
   - **The phases (rows 2, 3, 4, one rename).** Each phase is named after what it produces or does: `intent`, `design`, `build`, `test`, `deploy`, `maintain`, in branches (`sdlc/0001/design`), labels (`sdlc:build-ready`, `sdlc:build-approved`) and `status.yaml`, instead of the letters. Phase (a) becomes **Intent**: `/sdlc-intent` replaces `/sdlc-plan` (T2 and T3 name it; under this entry it becomes `/sdlc-intent`). `plan.md` stays an output of design: decision 2 is unchanged, spec and plan are approved at one gate. "Plan" then means one thing, `plan.md`.
   - **No `Status:` line in `intent.md`** (row 6): `status.yaml` is the one status; the template line and the gate's required header field go.
   - **`sdlc-agent-evals.yml`** (row 14): it says what is tested, the agent's configuration, and keeps the prefix that groups the workflows. `evals/cases/`, `check.py` and `evals-report.json` stay.
   - **`authorization: allow | ask`** for runbooks (row 17), the article's hook verbs (p.36); the owner's `sdlc:go` stays, the answer to the ask in the article's own word.
   - **`deploy.production_gate: true | false`** (row 22): what the key does is turn on the article's production gate.
   - **`ux-and-brand`** (row 10) for `ux-conventions`.
   - **A profile name that says what `full` means** (row 23); `naming.md` proposes `all-gates-human`, or a list of the human gates.
4. **The names other proposals left to this entry**, each a placeholder until R45 judges it by the same rule:
   - R11 (T32) and R12 (T12): the approvals line's keys (`act`, `by`, `at`, `via`, `pr`, `head`, `details`). These are the one exception to "last": the accepted R11 has them "judged with the study's names entry (T4) before the design" (R11, its settle table), and R11 is first of the line, so their row is judged before R11's design, ahead of the rest of this entry.
   - R17 (T17): `sdlc-comment.yml` and the `trigger` input.
   - R18 (T19): the ref `refs/sdlc/failed-runs/<run_id>-<attempt>` and the notes heading "In plain words".
   - R19 (T27): the guide command `/sdlc-guide`, and the triage label names it lists.
   - R24 (T9): the banner's and the item key's names, and whether decision 28's `sdlc:accept-findings` still fits once `sdlc:accept-risk` retires.
   - R25 (T30): the label that runs a waiting change now, and the ref prefix of the weekly spend records.
   - R27 (T1, the sources): the `policies/` folder.
   - R28 (T1 with T2): the per-change Full label at gate (b) (from the crosswalk row build-start), the product source's file and the role names.
   - R29 (T3): the "Examples/References" section, `sdlc/new/<slug>`, the new workflow.
   - R30 (T5) and R43 (T26): the commands and names they use.
   - R31 (T6): the ticket label, `sdlc:intent` until then.
   - R33 (T8): the formatter setting.
   - R35 (T13): the eval workflow, as point 3 says.
   - R36 (T14): the review-pass workflow for runbook PRs.
   - R37 (T15): the standing PR's title, branch and step names.
   - R38 (T16): the tuning workflow, PR and ref.
   - R39 (T20): `preview_command`, `rehearse_command` and the ref.
   - R40 (T22): the detection's ref.
   - R42 (T25): the lesson's field names.

   R20 (T28) leaves no name here, but its digest is touched by row 16: it reads every label from `state/conventions.py`, and its runbook and dismissal PR section keeps the PRs with `incident` and no `sdlc:` label (`plugin/pr/digest.py:71-75`), a filter the prefixed `sdlc:triage` breaks (point 2).
5. **How the rename lands** (`naming.md`, "If a row is accepted"):
   - **Order:** rows 2, 3 and 4 are one rename, since doing them apart would rename the same labels and branches twice; rows 6, 7, 10, 14, 16, 17, 22 and 23 are independent of each other.
   - **Compatibility:** a renamed config value (rows 17, 22, 23) reads the old value as the new one for a release, as `lite` reads as `standard`, so a project's `sdlc.yaml` works until its owner edits it. A renamed label (rows 3, 16) is accepted under both names by the digest and every workflow guard until the open PRs close.
   - **Guardrail files:** `CLAUDE.md`, `REVIEW.md`, `sdlc.yaml` and `.claude/**` in each project are the owner's edit; the change lists the exact lines for the owner instead of editing them.
   - **Every project on the framework** gets the rename: today the sample project, with its change folders and its open PRs' labels.
   - **The crosswalk:** `crosswalk.json` has no row for names and gets none; an accepted row is carried into the `target` of the crosswalk row of the same step (for example row 16 into maintain-triage), with the independent review the study requires for any change to `crosswalk.json`.

## How it is judged

- **The old names are gone.** After the rename, a `git grep` for each renamed name over `plugin/`, `template/` and `tests/` finds it only in the compatibility readers and their tests. No row that `naming.md` marks "playbook" or "third" still carries its old name in a branch, a label, `status.yaml`, a config key or a command.
- **The sample project moves without a by-hand relabel.** It runs a phase on a change that was opened under the old names, through the compatibility rules. The owner's only edits are the guardrail lines the change lists.
- **The owner's rule holds for every name left to this entry.** Each name in point 4 has a row with its reason, in `naming.md`'s columns, before the design. The failure is a name kept with "renaming costs too much" as its reason.

## What to settle before building

Entries marked *(mine)* go beyond the entry and are this proposal's recommendations.

| Question | Recommended |
|---|---|
| T1's AI roles against the owner's roles (the entry's first open item) | The owner's decisions are named by the article's roles (point 2). R28's AI role names (Product, Architect, …) are judged in R45's table, so that none reads as a person who approves. T1 already writes "security brief", never "security lead: approved". Left to R45 by R28 (T1 with T2), its settle table |
| T2 and T3 name `/sdlc-plan` (the entry's second open item) | **Settled by the entry:** it becomes `/sdlc-intent`. R29 builds with `/sdlc-plan` as a placeholder, and R45 renames it (R29 (T3), its settle table) |
| When: every rename must reach each project; `webapp-example` is the last point with one project to migrate (the entry's third open item) | **Placed last by the owner** (the record, section 8, the close table and the confirmed order). *(Mine:)* if `webapp-example` is initialised before R45, it is migrated with the sample under the compatibility rules. Rows 2 to 4 are the part to weigh if the owner wants it to start on the new names. The Order column is the owner's |
| Whether branch names, `status.yaml: phase` letters and the stored verdict word are read under both names, like the labels and config values | *(Mine:)* yes, for a release. Read `sdlc/<id>/<letter>` beside the new form (`BRANCH_RE`, `conventions.py:119`), a letter in `status.yaml` (`status.py:106-108`) and `escalate` in an existing `adversarial-review-*.json` and panel ledger (`checks.py:794`, `:834`). Otherwise an open change breaks at its next run |
| Whether the check runs (`sdlc/{phase}`), the evidence files (`gate-{phase}.json`, `adversarial-review-{phase}.json`, `run-{phase}.json`) and "gate (e)" in prose follow the phase names | *(Mine:)* yes, by the entry's own reason: a letter needs a table. Whether a project's branch protection requires an `sdlc/<letter>` check is to verify on each project before the check runs are renamed |
| The name for `full` | `naming.md`'s `all-gates-human`. *(Mine:)* the list form only if a later profile adds another combination of gates |
| Whether `entry_route: incident` follows the triage labels | *(Mine:)* no; the three route values are the article's (p.9, `conventions.py:61`). Whether a scan finding needs a route value of its own is judged in R45's design with R43 (T26) |
| The names other proposals left here (point 4) | *(Mine:)* one row each in `naming.md`'s columns (thing, current, better, proposed, why), in the design, by the owner's rule; the placeholders stand until then. The approvals line's keys get their row earlier, before R11's design, as the accepted R11 requires. R31 already flags that `sdlc:intent` sits close to `sdlc:intent-ready` (R31 (T6), its settle table) |
| One decision file for every renamed name, or one per decision | *(Mine:)* one file, since no substance changes and one owner review covers the nine the entry names and decisions 21 and 22, as decisions 28 and 29 were reviewed together. It names decision 27's labels too, which postdates the study and carries `sdlc:c-approved` and `sdlc:d-approved` |
| The triage labels' prefix (row 16) against the digest's filter and the gate-label sweep | *(Mine:)* add `sdlc:triage` and `sdlc:schedule` to `OWNER_LABELS` (`plugin/pr/cli.py:46`) or exempt them from the sweep (`:151-156`), and filter the digest on the triage label and no gate label instead of no `sdlc:` label (`plugin/pr/digest.py:75`), with both forms read while the old labels are accepted |

## Considered and not chosen

- **Keeping a confusing name because renaming costs something.** An earlier answer called row 4 "the most confusing clash" and then advised keeping it for the cost; the owner pointed out the contradiction, and the rule above replaced it (`naming.md`, "How the verdict was reached").
- **The article's `intent/` folder** for the change's home (row 1): it names one of the five files the folder holds; decision 10's reason stands.
- **"Plan mode"** for the planning run (row 5): it promises an interview the headless run does not hold.
- **"Escalate"** kept as the verdict, or the label renamed to match "park" (row 7): "escalate" suggests paging, and the label is the one form a visitor reads without context.
- **"The owner"** kept everywhere (row 8): it does not say which kind of decision is being taken, and it collides with GitHub's `OWNER` author association, which the framework's runner checks (`plugin/ci/fix_requests.py:53`, `plugin/detect/cli.py:1366`).
- **Stage numbers** ("Stage 3") in place of letters (row 3): another code to decode.
- **Renaming rows 2, 3 and 4 apart:** the same labels and branches would be renamed twice.
- **The article's `RELEASE_APPROVAL` variable** in place of the release label (row 12): equal as names, and the label exists because a run must not approve itself (decisions 5 and 13), which is behaviour, not naming.
- **The article's `agent-evals.yml` without the prefix, and `result.json` for the suite's report** (row 14): the prefix groups the workflows; `result.json` is one run's raw output, a different thing.

## Decisions it touches

The names, not the substance, of:

- **3** as amended by **27**: the labels `sdlc:c-approved` and `sdlc:d-approved`.
- **10**: the branches `sdlc/<id>/<phase>`; the folder is kept.
- **11**: the verdict's word.
- **13** and **19**: the production switch.
- **14** and **26**: the runbook authorization values; 26 also names `deploy.production`.
- **18**: the profile names.
- **25**: the triage labels.

The entry's list ends there. *(Mine:)* two more decision files carry a name that changes, and the decision file should name them too:

- **21**: the verdict word, "an `escalate` verdict of the adversarial reviewer" (`docs/decisions/21.md:17`), as amended into 11.
- **22**: the branch `sdlc/<id>/a` and `sdlc-plan.md` (`docs/decisions/22.md:13`).

In 11, 13 and 19 the change is to the wording or the concept, not to a literal name: 11 names the verdict only through the article's "escalates to a human", and 13 and 19 never write `deploy.production`, which only 26 does (`docs/decisions/26.md:13`).

A decision file before the intent, in a documentation PR of its own; this proposal reserves no number. **2** stays: `plan.md` is still written in the design phase and approved with the spec. **28** is kept (`sdlc:accept-findings` keeps the prefix); whether its name still fits once R24 retires `sdlc:accept-risk` is the question R24 leaves here (point 4), and a new name would touch 28's name only. **29** is read: its check run `sdlc/d` follows the check-run question above. Decisions 10 and 19 are sticky in their substance, which does not change here.

## Order

Last of the study's proposals, by the owner's confirmed order (the record, section 8: "and T4 last"). It comes after every proposal that leaves a name to it (point 4: R11, R12, R17, R18, R19, R24, R25, R27, R28, R29, R30, R31, R33, R35, R36, R37, R38, R39, R40, R42, R43), and after the rest of the line (R10, R13 to R16, R20 to R23, R26, R32, R34, R41, R44), so that each name is renamed once. The one exception is the approvals line's keys, which the accepted R11 has judged with this entry before its own design (point 4); that row is written then, and R11 and R12 build on the names it settles. It changes `plugin/`, `template/` and the docs, so it ships as plugin versions with tests and reaches each project through `/sdlc-init`'s copies and a migration of that project. The docs are edited with the Edit tool, sentence by sentence, never by a scripted rewrite (`CLAUDE.md`, "Things Claude gets wrong"). The parts:

| Part | Where | When |
|---|---|---|
| The decision file for the renamed names | `docs/decisions/` | First, before the intent, in a documentation PR of its own |
| The phase vocabulary (rows 2, 3, 4): labels, branches, `status.yaml`, `/sdlc-intent`, and the check runs and evidence files if settled so, with the readers of the old names | `plugin/state/conventions.py`, `status.py`, `plugin/commands/`, `template/.github/workflows/`, `plugin/pr/`, `plugin/gate/`, the docs | One change |
| The independent renames (rows 6, 7, 10, 14, 16, 17, 22, 23), each with its compatibility reader; row 16 also with the digest's filter and the gate-label sweep (point 2) | `intent-template`, `gate/artifacts.py`, `gate/checks.py`, `adversarial-reviewer.md`, `plugin/skills/`, `sdlc-evals.yml`, `conventions.py`, `pr/digest.py`, `pr/cli.py`, `detect/bands.py`, `template/sdlc.yaml`, `template/bands.yaml` | Any order, after the decision file |
| The roles' wording (row 8): the role at each decision point; the section 2 sentence already exists | `docs/OPERATING_MODEL.md` and the prompts | With the phase vocabulary or after it |
| The crosswalk targets of the rows the entry names (setup-home, plan-idea, build-plan, build-skills, test-evals, maintain-triage, maintain-scan, maintain-act, deploy-release, x-roles) | `docs/reviews/2026-09-28-playbook-vs-framework/crosswalk.json` | With each accepted row, after the independent review the study requires |
| The names left by other proposals (point 4) | Where each proposal put them | After each has landed; the approvals line's keys before R11's design, as the accepted R11 requires |
| Each project's migration, with the owner's guardrail lines listed | The sample project; `webapp-example` if it is initialised by then | After the plugin version that carries the readers |

[^entry]: `docs/reviews/2026-09-28-playbook-vs-framework/target-design.md`, T4 (its Status, "The owner's rule for this entry", "Direction discussed", "Open"), and the index row.
[^naming]: `docs/reviews/2026-09-28-playbook-vs-framework/naming.md`, the 23 rows, the summary and "If a row is accepted".
