# Names against the article (2026-10-20)

**Summary.** This is the name table roadmap row R45 needs before its decision file: one row per name the owner sees today, judged against the article's term where the article has one and on its own clarity where it has none. Nothing is renamed here. Read at `main` 8546217 (plugin 1.0.14); the article is `docs/reference/ai-native-sdlc-playbook.txt` (page-tagged text of the PDF, cited by PDF page; "image" marks a term read from one of the three figures, as `docs/proposals/names.md` records). The sample project `luissiviero/sdlc-sample-python` was read at `main` 0e8ae49 for the migration cost: 7 change folders, 20 `sdlc/<id>/<letter>` branches on the remote, `profile: standard`, `review: deferred`, `production: true`.

**The rule.** The owner's rule for study entry T4: a confusing name is not kept because renaming costs something; either one side's name is better or a third name is needed, and the cost is listed apart. Where the article has no term the column says "framework's own" and the row is judged on whether a first-time owner reading it on a phone understands it without the docs.

**The verdict in one line.** 43 rename rows and 45 keep rows out of 88; most renames are one rename (the six phase names, which carry the letters out of every branch, label, status value, check run, evidence file and gate sentence at once). The renames fit in five pull requests, listed at the end, after the decision file.

## 1. The phases

The article's stages are Plan, Design, Build, Test, Deploy, Maintain (table of contents, p.4; the loop, p.7), with "Stage 6: Maintenance" in cross references (p.9, p.18, p.42). Stage 1 writes `intent.md` (p.9-11); `plan.md` is written in Stage 3 Build, the plan mode play (p.15-16); the dependency graph labels the Stage 1 play "Capture intent" (p.8, image).

| # | Name the owner sees | Today | Proposed | The article's term and PDF page | Why | Cost to rename | Verdict |
|---|---|---|---|---|---|---|---|
| 1 | Phase (a) | `a` (`PHASE_NAMES["a"] = "plan"`) | `intent` | "Stage 1 — Plan" (p.4); Stage 1 produces `intent.md` (p.9-11); the play is "Capture intent" (p.8, image); `plan.md` belongs to Build (p.15-16) | The phase's only output is `intent.md`, and once it is named after it "plan" means one thing, `plan.md`. | `plugin/state/conventions.py` (`PHASES`, `PHASE_NAMES`, `WORK_PHASE`, `BRANCH_RE`), `plugin/state/status.py` (`phase`, `gate.phase`), `plugin/pr/cli.py` (check run), `plugin/gate/artifacts.py` and `limits.py` (evidence names), `plugin/panel/ledger.py`, all eight commands, the 13 template workflows' label guards, `template/changes/README.md`, `template/sdlc.yaml` (`session_model` keys), `docs/`. An existing project migrates: `status.yaml: phase` in every change folder (the sample has 7), the branches of open changes, the labels of open PRs; letters are read for one release (`LEGACY_PROFILES` is the precedent). | rename |
| 2 | Phase (b) | `b` (`design`) | `design` | "Stage 2 — Design" (p.4, p.12-14) | The name is already the article's; only the letter goes. | With row 1 (one rename). | rename |
| 3 | Phase (c) | `c` (`build`) | `build` | "Stage 3 — Build" (p.4, p.15) | Same. | With row 1. | rename |
| 4 | Phase (d) | `d` (`test`) | `test` | "Stage 4 — Test" (p.4) | Same. | With row 1. | rename |
| 5 | Phase (e) | `e` (`deploy`) | `deploy` | "Stage 5 — Deploy" (p.4, p.40) | Same. | With row 1. | rename |
| 6 | Phase (f) | `f` (`maintain`) | `maintain` | "Stage 6 — Maintain" (p.4); "Stage 6: Maintenance" (p.9, p.18, p.42) | The verb matches the command and the PR title prefix `maintain(<id>)` the owner already reads. | With row 1. | rename |
| 7 | `status.yaml: phase: abandoned` | `abandoned` | `abandoned` | framework's own (decision 25) | A closed-without-merge change; the word needs no docs. | — | keep |

## 2. The commands

| # | Name the owner sees | Today | Proposed | The article's term and PDF page | Why | Cost to rename | Verdict |
|---|---|---|---|---|---|---|---|
| 8 | The phase (a) command | `/sdlc-plan` | `/sdlc-intent` | Stage 1 is "Plan" (p.4, p.9) but its play is "Capture intent" (p.8, image) and plan mode sits in Build (p.15-16) | A command named "plan" that never writes `plan.md` sends whoever knows the article to the wrong phase twice. | `plugin/commands/sdlc-plan.md` (file and name), `plugin/commands/sdlc-fix.md`, `sdlc-maintain.md` and `sdlc-init.md` where they cite it, `docs/`; a project's `CLAUDE.md` or `.claude/settings.json` that names it is a guardrail line for the owner (the sample's `CLAUDE.md` does not). No data migrates. | rename |
| 9 | `/sdlc-design` | same | same | "Design" (p.4) | Already the article's. | — | keep |
| 10 | `/sdlc-build` | same | same | "Build" (p.4) | Same. | — | keep |
| 11 | `/sdlc-test` | same | same | "Test" (p.4) | Same. | — | keep |
| 12 | `/sdlc-deploy` | same | same | "Deploy" (p.4) | Same. | — | keep |
| 13 | `/sdlc-maintain` | same | same | "Maintain" (p.4) | Same. | — | keep |
| 14 | `/sdlc-fix` | same | same | framework's own ("review findings feed back", p.34, names no command) | "Fix" is what the owner asked for in the review; a phone reader gets it. | — | keep |
| 15 | `/sdlc-init` | same | same | framework's own | "init" is the word `git` and every package manager use for the same act. | — | keep |

## 3. The gate letters

The article names a gate by what it guards: "the production gate" (p.32, p.40-41), "the review gate" (p.43-47), "approval gates" (p.6, p.36). It never numbers a gate. The framework's generated text says "Gate (e) parked change 0001" and "wait for sdlc:c-approved"; after row 1 the letter has nothing left to stand for.

| # | Name the owner sees | Today | Proposed | The article's term and PDF page | Why | Cost to rename | Verdict |
|---|---|---|---|---|---|---|---|
| 16 | Gate (a) | "gate (a)" | "the intent gate"; in generated text `gate (intent)` | "the accept or reject decision ... recorded as the merge" (p.11-12); no letter | The gate is the intent PR's merge; its name should say so. | `plugin/gate/gate.py` (`what_i_need`), `plugin/pr/description.py`, the commands, the workflows' comments, `docs/OPERATING_MODEL.md` and 45 files with "gate (x)". With row 1; prose only, no data. | rename |
| 17 | Gate (b) | "gate (b)" | "the design gate" / `gate (design)` | "accepting the spec is what starts the plan mode play" (p.14) | Same. | With row 16. | rename |
| 18 | Gate (c) | "gate (c)" | "the build gate" / `gate (build)` | framework's own (the article's Build has no gate of its own; the code owner reviews the PR, p.29) | Same. | With row 16. | rename |
| 19 | Gate (d) | "gate (d)" | "the test gate" / `gate (test)` | framework's own | Same. | With row 16. | rename |
| 20 | Gate (e) | "gate (e)" | "the deploy gate" / `gate (deploy)` | "the production gate" (p.32, p.40-41) is the second act inside it (row 56) | "deploy gate" keeps the phase's name; "production gate" stays the name of the release-label act within it, as the article uses it. | With row 16. | rename |
| 21 | Gate (f) | "gate (f)" | "the triage gate" / `gate (maintain)` in generated text | "the service owner ... triages the queue" (p.44) | The owner's act at this gate is a triage; prose can say so while the generated text keeps the phase name for grep. | With row 16. | rename |

## 4. The labels

| # | Name the owner sees | Today | Proposed | The article's term and PDF page | Why | Cost to rename | Verdict |
|---|---|---|---|---|---|---|---|
| 22 | `sdlc:a-ready` | `sdlc:a-ready` | `sdlc:intent-ready` | framework's own (the article's gates are hooks and merges, p.36) | "ready" says a run waits for a person; the letter says nothing without a table. | `conventions.py` (`ready_label`), the workflows' `contains(labels, 'sdlc:a-ready')` guards (`sdlc-test.yml:51`, `sdlc-deploy.yml:52` and the rest), `plugin/pr/cli.py`, `plugin/pr/digest.py`, the commands, `docs/`. Open PRs in a project carry the old label: both read for one release, then the label set is recreated by `ensure_labels`. | rename |
| 23 | `sdlc:b-ready` | same pattern | `sdlc:design-ready` | framework's own | Same. | With row 22. | rename |
| 24 | `sdlc:c-ready` | same | `sdlc:build-ready` | framework's own | Same. | With row 22. | rename |
| 25 | `sdlc:d-ready` | same | `sdlc:test-ready` | framework's own | Same. | With row 22. | rename |
| 26 | `sdlc:e-ready` | same | `sdlc:deploy-ready` | framework's own | Same. | With row 22. | rename |
| 27 | `sdlc:f-ready` | same | `sdlc:maintain-ready` | framework's own | Same. | With row 22. | rename |
| 28 | `sdlc:c-approved` (Full profile) | same | `sdlc:build-approved` | "code owner's approval" (p.33) | Same; the owner's approving review plus this label passes the gate. | With row 22. | rename |
| 29 | `sdlc:d-approved` (Full profile) | same | `sdlc:test-approved` | framework's own | Same. | With row 22. | rename |
| 30 | `sdlc:release-approved` | same | same | "the release manager authorizes it, and a hook enforces the production gate" (p.40-41); the article's own switch is the env var `RELEASE_APPROVAL` (p.36-37) | The label is the article's approval in GitHub's form and says exactly what it is. | — | keep |
| 31 | `sdlc:needs-human` | same | same | "continues or is escalated to a human" (p.42) | It is the one form a GitHub visitor reads without context; "park" is what happens, "needs human" is what it means to the reader. | — | keep |
| 32 | `sdlc:fixing` | same | same | framework's own (decision 29) | "fixing" plus the digest's "nothing needed from you" is plain on a phone. | — | keep |
| 33 | `sdlc:superseded` | same | same | framework's own (decision 30) | GitHub shows it on a closed PR beside the one that replaced it; the word is the usual one. | — | keep |
| 34 | `sdlc:accept-risk` | same | same | framework's own (decision 24); the article only says "judging intent and risk" (p.29, p.32) | It names the act the owner performs. R24's question whether `sdlc:accept-findings` fits beside it is judged when R24's banner lands, not here. | — | keep |
| 35 | `sdlc:reset-iterations` | same | same | framework's own (decision 24) | Says what it does. | — | keep |
| 36 | `sdlc:unlock-tests` | same | same | framework's own (decision 24) | Says what it does. | — | keep |
| 37 | `incident` (every triage PR) | `incident` | `sdlc:triage` | items are "findings" in "the triage queue" (p.44-45); a scan finding is filed in the Stage 1 format too (p.46) | A weekly scan finding is not an incident (the sample's change 0008 is a supply-chain finding labelled `incident`), and the label is one of two without the `sdlc:` prefix that groups the framework's labels. | `conventions.py` (`INCIDENT_LABEL`), `template/.github/workflows/sdlc-scan.yml:15-16`, `:98`, `sdlc-runbook.yml`, `sdlc-digest.yml`, `plugin/detect/cli.py`, `plugin/scan/route.py`, the maintain command, `docs/`. Two code changes beyond the rename: the digest's filter keeps PRs with `incident` and no `sdlc:` label (`plugin/pr/digest.py:71-79`) and the gate-label sweep removes every `sdlc:` label outside `OWNER_LABELS` (`plugin/pr/cli.py:54`, `:189`); the new label must join `OWNER_LABELS` and the filter must read "carries `sdlc:triage` and no gate label". Open triage PRs in a project: both labels read for one release. | rename |
| 38 | `schedule` (the owner's "not now") | `schedule` | `sdlc:schedule` | "Fix now, schedule, or dismiss" (p.44) | The verb is the article's; only the prefix is missing. | With row 37 (`SCHEDULE_LABEL`, the maintain command, `sdlc-digest.yml`); `OWNER_LABELS` as above. | rename |
| 39 | `sdlc:go` | same | same | the owner's "Go." in the incident channel (p.49, image); "shall I run it?" (p.49-50) | It is the owner's answer in the article's own word. | — | keep |

## 5. The branch segments

The article gives no branch pattern; its examples are `feature-auth` and `fix-rate-limit` (p.25).

| # | Name the owner sees | Today | Proposed | The article's term and PDF page | Why | Cost to rename | Verdict |
|---|---|---|---|---|---|---|---|
| 40 | The prefix `sdlc/` | `sdlc/` | `sdlc/` | framework's own | Groups the framework's branches in a project; a reader knows which branches are the pipeline's. | — | keep |
| 41 | The id `<id>` (four digits) | `0001` | `0001` | none ("the same change", p.12, p.15) | The automation needs a key; the digits sort and are short on a phone. | — | keep |
| 42 | `sdlc/<id>/a` (the intent PR) | `/a` | `/intent` | framework's own | The letter must be decoded; the name is the phase's. | `BRANCH_RE` and `branch_name` in `conventions.py`, `WORK_PHASE`, every workflow that cuts or checks out a phase branch, `template/changes/README.md:17-24`, the commands. An existing project keeps its old branches: `parse_branch` reads `[a-f]` beside the names for one release so an open change finishes on its branch; nothing is renamed on the remote. | rename |
| 43 | `sdlc/<id>/b` (the spec+plan PR) | `/b` | `/design` | framework's own | Same. | With row 42. | rename |
| 44 | `sdlc/<id>/c` (the build PR, kept open through test and deploy) | `/c` | `/build` | framework's own | Same; "build" also says why test and deploy commit on it. | With row 42. | rename |
| 45 | `sdlc/<id>/dismiss` (the dismissal PR of a triage item) | `/dismiss` | `/dismiss` | "Dismiss with a reason, so the dismissal is recorded" (p.47) | The article's word; it says what the PR does. | — | keep |
| 46 | `sdlc/new/<slug>` (R29, not built) | placeholder | `sdlc/new/<slug>` | framework's own | "new" says the change has no id yet; nothing better is shorter. | — (judged for R29's build) | keep |

## 6. The status and configuration values

`status.yaml` is written by the plugin; `sdlc.yaml` and `bands.yaml` are the owner's.

| # | Name the owner sees | Today | Proposed | The article's term and PDF page | Why | Cost to rename | Verdict |
|---|---|---|---|---|---|---|---|
| 47 | `status.yaml: phase` | `a` … `f` | `intent` … `maintain` | the stage names (p.4) | Row 1. | With row 1; a one-off `state/cli.py` migration of every change folder in a project, or the letter read for one release (recommended: both, the read for safety and the migration so a `grep` finds no letter). | rename |
| 48 | `status.yaml: gate.result` | `passed \| parked \| approved \| changes-requested` | same | framework's own; "escalated" (p.42) is the article's word for the park | "parked" is decision 11's word and the digest's; "changes-requested" is GitHub's own. | — | keep |
| 49 | `status.yaml: change_type` | `feature \| fix` | same | the branch examples `feature-auth`, `fix-rate-limit` (p.25) | The article's two kinds. | — | keep |
| 50 | `status.yaml: entry_route` | `idea \| ticket \| incident` | same | "A person has an idea, a ticket is filed, or an incident is surfaced" (p.9) | The article's three routes; a scan finding entering as `incident` is a route question for R43, not a name. | — | keep |
| 51 | `sdlc.yaml: review` and `status.yaml: review_override` | `parked \| deferred` | same | framework's own (decision 21) | "parked" waits for you, "deferred" lets the panel decide first; both plain. | — | keep |
| 52 | `sdlc.yaml: profile` | `standard` | `standard` | framework's own (decision 18) | The default needs no explanation. | — | keep |
| 53 | `sdlc.yaml: profile` | `full` | `all-gates-human` | "human approval gates that must survive" (p.36); "human review reserved for regulated and critical code" (p.6) | "full" does not say what is full; the proposed value says what the profile does in the one place the owner sets it. | `conventions.py` (`PROFILES`, `HUMAN_GATES`, `LEGACY_PROFILES`), `template/sdlc.yaml:10`, `sdlc-init.md` (`--profile`), the commands' "Full:" sentences, `docs/`. A project's `sdlc.yaml` is a guardrail line for the owner; `full` reads as the new value for one release, as `lite` did. | rename |
| 54 | `sdlc.yaml: deploy.action` | `publish package \| schedule job \| regenerate report \| promote to paper trading \| deploy service \| none` | same | framework's own (decision 19); the article's tiers are by environment (p.40) | Plain phrases a phone reader understands. | — | keep |
| 55 | `sdlc.yaml: deploy.production` | `true \| false` | `deploy.production_gate: true \| false` | "the production gate" (p.32, p.40-41) | `production: true` reads as "this project is production"; the key turns on the article's production gate. | `template/sdlc.yaml:68`, `plugin/hooks/production_gate.py:409`, `plugin/state/cli.py:373`, `plugin/init/sdlc_init.py`, `sdlc-release.yml`, `docs/`. The sample's `sdlc.yaml` is a guardrail line for the owner; the old key reads as the new one for a release. | rename |
| 56 | `bands.yaml: authorization` | `preapproved \| go` | `allow \| ask` | "a preapproved runbook" (p.43); a hook "can allow, ask, or block" (p.36); the owner's "Go." (p.49, image) | `preapproved` is the article's word and could stay alone, but the pair must read together and `go` as a config value does not say "ask me first"; the hook verbs say exactly what each value does, and `sdlc:go` stays as the answer. | `plugin/detect/bands.py:41`, `template/bands.yaml:34-40`, `plugin/detect/routes.py`, `sdlc-runbook.yml`, the maintain command, `docs/`. A project's `bands.yaml` is the owner's edit; old values read as new for a release. | rename |
| 57 | `sdlc.yaml: session_model` per-phase keys | `a` … `f` | the phase names | the stage names (p.4) | Row 1. | With row 1; `plugin/panel/models.py`; the old keys read for a release. | rename |
| 58 | `sdlc.yaml: maintain.metric` and `maintain.source` | same | same | "picks one metric with a stable rolling baseline" (p.43) | The article's words. | — | keep |

## 7. Check runs, evidence files, PR titles and the verdict

| # | Name the owner sees | Today | Proposed | The article's term and PDF page | Why | Cost to rename | Verdict |
|---|---|---|---|---|---|---|---|
| 59 | The check run on a PR | `sdlc/a` … `sdlc/f` | `sdlc/intent` … `sdlc/maintain` | framework's own | The owner reads it in the PR's checks list; a letter there is the same code as everywhere else. | `plugin/pr/cli.py:51`; with row 1. Verify on each project whether branch protection requires a check by its old name before the rename lands (the sample's protection is the owner's setting). | rename |
| 60 | `evidence/gate-<x>.json`, `adversarial-review-<x>.json`, `run-<x>.json`, `decisions-<x>.md` | letters | phase names | framework's own | A file named `gate-deploy.json` is found without the docs. | `plugin/gate/artifacts.py:72-73`, `plugin/gate/limits.py:63`, `plugin/panel/ledger.py`, `plugin/gate/preflight.py:274`, `template/changes/README.md:12`; with row 1. Existing files in a project's merged change folders stay as they are (history); the gate reads both names for a release. | rename |
| 61 | PR title prefixes | `intent(<id>):`, `design(<id>):`, `build(<id>):`, `maintain(<id>):` | same | framework's own | They already carry the phase names; the intent PR is titled `intent(...)` on a branch called `/a` by a command called `plan`, which is the inconsistency rows 1, 8 and 42 remove. | — | keep |
| 62 | The adversarial reviewer's verdict | `continue \| escalate` | `continue \| park` | "continues or is escalated to a human" (p.42) | "Escalate" suggests paging, which decision 11 rules out; one event then has one word in the verdict, the state and the gate result. | `plugin/gate/checks.py:858`, `:894`, `:898`, `:1750`, `plugin/agents/adversarial-reviewer.md:3`, `:71`, `plugin/panel/ledger.py`, `template/sdlc.yaml:18`, `docs/`. Existing `adversarial-review-*.json` and panel ledgers in a project say `escalate`: read for one release. | rename |

## 8. The digest's section titles

The digest is the body of the issue "SDLC review queue" (`plugin/pr/digest.py`).

| # | Name the owner sees | Today | Proposed | The article's term and PDF page | Why | Cost to rename | Verdict |
|---|---|---|---|---|---|---|---|
| 63 | The issue title | "SDLC review queue" | same | framework's own ("the triage queue", p.45, is the maintain queue only) | "Review queue" is where the owner's decisions wait; plain. | — | keep |
| 64 | "Parked — `sdlc:needs-human`" | same | same | "escalated to a human" (p.42) | The label beside the word tells the reader what "parked" means. | — | keep |
| 65 | "Waiting at a human gate" | same | same | "human approval gates" (p.36) | The article's phrase. | — | keep |
| 66 | "Automatic fix round running — `sdlc:fixing` (nothing needed from you)" | same | same | framework's own (decision 29) | Says what runs and that nothing is needed. | — | keep |
| 67 | "Phase (f): runbook and dismissal PRs — `incident`" | same | "Maintain: runbook and dismissal PRs — `sdlc:triage`" | "Stage 6 — Maintain" (p.4); "the triage queue" (p.45) | Follows rows 6 and 37; the letter and the misnamed label both go. | `plugin/pr/digest.py:179`, with its filter (row 37). | rename |
| 68 | "Nothing waiting: no open PR carries an `sdlc:` label." | same | same | framework's own | True today and still true after row 37 (a triage PR then carries an `sdlc:` label and is listed). | — | keep |
| 69 | "Decisions taken for you (N)" (the PR description under deferred review) | same | same | framework's own (decision 21) | Plain. | — | keep |

## 9. The park wording

| # | Name the owner sees | Today | Proposed | The article's term and PDF page | Why | Cost to rename | Verdict |
|---|---|---|---|---|---|---|---|
| 70 | The block heading | "## What I need from you" | same | framework's own (decision 11); the article says only "escalated to a human" (p.42) | A phone reader knows at once that the next lines are their to-do. | — | keep |
| 71 | The block's first line | "Gate (e) parked change 0001 (slug) on <date>." | "Gate (deploy) parked change 0001 (slug) on <date>." | none | Row 20. | `plugin/gate/gate.py:81`; with row 16. | rename |
| 72 | The description's fifth bullet | 'parked at gate (e) - see "What I need from you" below' | 'parked at gate (deploy) - see ...' | none | Row 20. | `plugin/pr/description.py:383`; with row 16. | rename |
| 73 | The per-check line | "- **<check>**: <reason>" and "what I need: <need>" | same | none | Plain. | — | keep |
| 74 | The state words | "parked", `parked_reason` | same | "escalated" (p.42) | Decision 11's word; "park" says the run stops and waits, which is what happens. | — | keep |
| 75 | The runbook park | 'parks with "Go" requested' | same | "Go." (p.49, image) | The article's word. | — | keep |
| 76 | The automatic round's park prefix | "automatic fix round " | same | framework's own | Plain. | — | keep |

## 10. Other names the owner sees

| # | Name the owner sees | Today | Proposed | The article's term and PDF page | Why | Cost to rename | Verdict |
|---|---|---|---|---|---|---|---|
| 77 | The intent's header line | `Status: draft \| proposed \| accepted` | removed | "Author: J. Ortiz (claims operations). Status: draft." (p.11) | The article's line, but the framework has `status.yaml`, and the frozen header disagrees with it in four sample changes (`Status: draft` at phase `e`); two fields called status that disagree are worse than one. | `plugin/skills/intent-template/SKILL.md:18`, `plugin/gate/artifacts.py:29` (the required header field), the sample's intents (left as history; the gate stops requiring the line). | rename |
| 78 | The eval workflow | `sdlc-evals.yml` ("SDLC evals") | `sdlc-agent-evals.yml` | `.github/workflows/agent-evals.yml` (p.30) | The article's name says what is tested, the agent's configuration; the prefix keeps the 13 workflows together. | `template/.github/workflows/sdlc-evals.yml` (file and `name:`), `plugin/init/sdlc_init.py`, `docs/`; a project gets the new file on the next `/sdlc-init` upgrade and the old one is removed by it. | rename |
| 79 | The other 12 workflows | `sdlc-<phase or act>.yml` | same | none | The prefix groups them; each name says what it runs. | — | keep |
| 80 | The UX skill | `ux-conventions` | `ux-and-brand` | policies are "brand, security, compliance, and UX" (p.12-13) | The skill carries the brand rules and its name hides them. | `plugin/skills/ux-conventions/` (folder and `name:`), the commands that load it, `docs/`; a project's `.claude/settings.json` that names it is a guardrail line for the owner. | rename |
| 81 | The other skills | `coding-standards`, `security-baseline`, `data-conventions`, `definition-of-done`, `intent-template`, `spec-template`, `plan-template` | same | example skill `secure-api-review` (p.22) | Each says its scope; the article's example is narrower than the framework's. | — | keep |
| 82 | The agents | `verifier`, `code-simplifier`, `researcher`, `adversarial-reviewer` | same | the same names (p.25, p.42) | Already the article's. | — | keep |
| 83 | The change folder | `changes/<id>-<slug>/` | same | "an intent/ folder" (p.10) | The folder holds five kinds of file, not one; "change" is the framework's unit everywhere. | — | keep |
| 84 | The evidence folder | `evidence/` | same | "the evidence" (p.29) | The article's word. | — | keep |
| 85 | The lessons folder | `lessons/` | same | "a versioncontrolled lessons file" (p.49) | The article's word. | — | keep |
| 86 | The planning run | "the read-only planning run" | "the planning run" | "plan mode" (p.15-16) | The article's name is an interactive feature the headless run is not; "read-only" is already said by the tool list. | Wording in `sdlc-design.md` and `docs/`; no data. | rename |
| 87 | Who decides | "the owner" at every decision point | the article's role at each point: "the product owner merges the intent", "the code owner merges the build PR", "the release manager applies the release label", "the service owner triages" | product owner (p.9-12), code owner (p.29, p.33), release manager (p.37, p.40-41), service owner (p.43-44) | "The owner" does not say which kind of decision is taken, the role does, and "owner" collides with GitHub's `OWNER` author association the workflows check; `docs/OPERATING_MODEL.md:24` already says one person holds every role. | Prose and prompts only (about 86 files of wording, no code, no data); last, so that a first-time owner of a one-person project meets the roles only where a decision is asked of them. | rename |
| 88 | The profile names in prose | "Standard", "Full" | "Standard", "all-gates-human" | none | Row 53. | With row 53. | rename |

## 11. Names accepted proposals left to R45 and not yet shown

These are placeholders; the owner does not see them today. One line each, by the same rule, so each proposal is built with the name it keeps (ROADMAP R45, the 2026-10-20 note).

| Proposal | Name | Verdict | Why |
|---|---|---|---|
| R11, R12 | the approvals line's keys `act`, `by`, `at`, `via`, `pr`, `head`, `details` | keep | Judged before R11's design, as R11 requires; each is the shortest plain word for its value. |
| R17 | `sdlc-comment.yml`, the `trigger` input | keep | The workflow runs on a comment; "trigger" is GitHub's own word. |
| R18 | `refs/sdlc/failed-runs/<run_id>-<attempt>`; the heading "In plain words" | keep | Both say what they hold. |
| R19 | `/sdlc-guide` | keep | A guide is what a first-time owner looks for. |
| R24 | the banner's and item key's names; `sdlc:accept-findings` beside `sdlc:accept-risk` | judged at R24's design | The banner does not exist yet; row 34 keeps `sdlc:accept-risk` until then. |
| R25 | the label that runs a waiting change now; the spend records' ref prefix | judged at R25's design | Not named yet. |
| R27 | `policies/` | keep | The article's word for the sources ("policy owner", "brand, security, compliance, and UX", p.12-14). |
| R2 | the project's `references/` | keep | Plain. |
| R28 | the per-change Full label at the design gate; the AI role names (Product, Architect, ...) | rename the label with row 53 (`sdlc:all-gates-human`); the AI roles keep their names only where the prose says "brief", never "approved" | Rows 53 and 87. |
| R29 | "Examples/References" section; `sdlc/new/<slug>`; the new workflow | keep | Row 46. |
| R31 | the ticket label `sdlc:intent` | rename to `sdlc:ticket` before it is built | With phase `intent`, `sdlc:intent` sits one word from `sdlc:intent-ready` (R31 already flags it); "a ticket is filed" is the article's route (p.9). |
| R33 | the formatter setting | keep | Judged at its design; nothing collides. |
| R35 | the eval workflow | `sdlc-agent-evals.yml` | Row 78. |
| R36, R37, R38, R39, R40, R42, R56, R57 | the review-pass workflow, the standing PR's names, the tuning names, `preview_command`, `rehearse_command`, the detection's ref, the lesson fields (with `files`), the system pages' folder and keys | keep as proposed | Each is a plain phrase or the article's word; none carries a letter or collides with a renamed name. R57 lands after R45 so its names change once. |

## 12. The renames, in the order they should land

The decision file comes first, in a documentation PR of its own (ROADMAP R45, "a decision file before the intent"): it records rows 1 to 88 as decided, and the accepted proposals above are built with those names. Then five pull requests, each read-compatible for one release with the old names, so an open change in a project finishes on its old branch and labels, and the sample project migrates without a by-hand relabel. Guardrail lines in a project (`CLAUDE.md`, `sdlc.yaml`, `bands.yaml`, `.claude/settings.json`) are listed for the owner by each PR, never edited by it.

**PR 1 — the phases (one rename, rows 1-6, 8, 16-29, 42-44, 47, 57, 59-60, 67's phase part, 71-72, 86).** `PHASES` becomes the six names; `BRANCH_RE`, `status.yaml: phase`, the labels, the check run, the evidence file names, the `session_model` keys and the gate sentences follow; `/sdlc-plan` becomes `/sdlc-intent`; "read-only" leaves the planning run's name. Compatibility: letters read in branches, `status.yaml`, labels, evidence file names and `session_model` keys for one release; a `state/cli.py` command migrates a project's change folders. Verify each project's branch protection for a check required by its old name before merging.

**PR 2 — the labels and the verdict (rows 37-38, 62, 67's label part).** `incident` becomes `sdlc:triage`, `schedule` becomes `sdlc:schedule`, with the digest's filter and the gate-label sweep fixed for the prefix; the verdict becomes `continue | park`, with `escalate` read in existing verdict files and ledgers for one release.

**PR 3 — the configuration values (rows 53, 55-56, 88).** `full` becomes `all-gates-human`, `deploy.production` becomes `deploy.production_gate`, `authorization` becomes `allow | ask`; each old value reads as the new one for one release (`LEGACY_PROFILES` is the pattern). The sample's `sdlc.yaml` and `bands.yaml` lines are listed for the owner.

**PR 4 — the files (rows 77-78, 80).** The intent's `Status:` line leaves the template and the gate's required fields; `sdlc-evals.yml` becomes `sdlc-agent-evals.yml`, applied to a project by the next `/sdlc-init` upgrade; `ux-conventions` becomes `ux-and-brand`.

**PR 5 — the roles in prose (row 87), last.** "The owner" becomes the article's role at each decision point in `OPERATING_MODEL`, the commands and the docs; no code, no data.

One release after PR 1 to PR 4 have landed, a sixth, small PR removes the compatibility readers, and a `git grep` for each old name over `plugin/`, `template/` and `tests/` finds nothing.
