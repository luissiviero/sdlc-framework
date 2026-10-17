---
type: Proposal
title: The policy sources — the owner's written policies in the project's policies/ folder, read by the plugin's skills, with a trigger eval per policy skill
description: The owner writes one policy source per policy skill in a policies/ folder that /sdlc-init creates empty; each plugin skill reads its source, which wins where they differ, so an edit reaches the next run with no pin bump; policies/ becomes a guardrail path, the spec header records the source's commit, and each policy skill gets a trigger eval on each plugin release.
status: proposed
roadmap: R27
sources:
  - id: study-entry
    resource: docs/reviews/2026-09-28-playbook-vs-framework/target-design.md
    title: "T1 (first of its two proposals), confirmed at the close of the study on 2026-10-09: its \"Sources and documents\" section, from the crosswalk row build-skills (better: the playbook; decision: blend), 2026-10-03, with the \"Sources first\" line of its Direction and the open item on which documentation each role reads"
  - id: record
    resource: docs/reviews/2026-09-28-playbook-vs-framework.md
    title: "Section 7, first bullet (T1 as two proposals, the policy sources first); section 8, the close, part 1 (T1's row: D6, policies/ a guardrail path; \"no code beyond the skills reading a source\") and part 2 (the confirmed order)"
  - id: crosswalk
    resource: docs/reviews/2026-09-28-playbook-vs-framework/crosswalk.json
    title: "Row build-skills whole; the decision fields of build-config (the brief that quotes the eval result), build-hooks (\"back any skill\" decided with build-skills), setup-adopt (what change 0000 lists as starting empty) and test-evals (the eval workflow on policies/**)"
  - id: playbook
    resource: docs/reference/ai-native-sdlc-playbook.pdf
    title: "p.14: the skill versions in force logged with the spec, flagged concerns routed to the named policy owners; p.21-22: skills as institutional knowledge, one policy with a named owner and a written source of truth, steps 1-6 (step 4: test that the skill triggers), governance; p.23: the skill's indicators, and hooks that back any skill whose policy has to hold"
  - id: decision-6
    resource: docs/decisions/6.md
    title: "Decision 6: where the guardrails live so the agent cannot switch them off (the decision this amends: its list of guardrail paths gains policies/)"
  - id: decision-8
    resource: docs/decisions/8.md
    title: "Decision 8: plugin plus template, the plugin version pinned per project (kept)"
  - id: decision-17
    resource: docs/decisions/17.md
    title: "Decision 17: the project's eval suite starts empty and fills from incidents (kept)"
  - id: code
    resource: plugin/skills/
    title: "The five policy skills' Source and Check sections; plugin/gate/preflight.py POLICY_SKILLS and check_policy_skills; plugin/gate/artifacts.py render_spec_header; plugin/gate/cli.py cmd_spec_header; plugin/hooks/protected_paths.py ALWAYS_PROTECTED; plugin/ci/run_phase.py guardrail_changes and ci_settings_file; plugin/ci/settings.ci.json; plugin/scan/prompt.py skill_text; plugin/evals/run.py CHECK_KINDS and compose; plugin/init/sdlc_init.py; tests/test_policy_skills.py; .github/workflows/framework-evals.yml; template/.github/workflows/sdlc-evals.yml; read at main 5542406, plugin 1.0.1"
generated: { by: sdlc-framework-session/ccr-01de3f80-ilnomi, at: 2026-10-15T20:00:00Z }
---

# The policy sources: the owner's written policies in `policies/`, read by the plugin's skills, with a trigger eval per policy skill

**Status: proposed (roadmap R27), from study entry T1 (first of its two proposals), confirmed by the owner on 2026-10-09.** Nothing is built. It amends decision 6: its list of guardrail paths gains the project's `policies/` folder. Decision 6 is sticky (`docs/decisions/6.md`, "B2 STICKY"); the owner confirmed this amendment at the close on 2026-10-09 (the record, section 8, T1's row). The decision file is written before the intent, in a documentation PR (the record, section 8, part 1); this proposal writes no decision file and reserves no number. It is the first of the roles' pair in the confirmed order. R28 (T1's second proposal, `roles-and-manager.md`) adds the roles, the manager and the agent catalogue, with T2 inside. Those roles read these sources through the skills on their cards.

## The problem

The entry puts it in one line: "A role is only as good as what it reads: without the owner's written policies a 'security lead' is the generic model under another name." The same holds today for every run that loads a policy skill:

- **The five policy skills have no owner source.** The framework wrote them from the article, and each says "no owner source yet". The article's only infrastructure for a skill is "one policy with a named owner and a written source of truth" (p.21).
- **The owner has one route for their own policy, and it replaces the framework's text whole.** That route is a full override in `.claude/skills/<name>/SKILL.md`, which is a guardrail path. It is honoured unevenly: the design command, the preflight's skills check, the REVIEW.md pass, the panel's reviewer and the weekly scan (`security-baseline` only) treat it as replacing the plugin's copy. The build, fix and test commands, the adversarial reviewer, the code-simplifier and the panel's advocate load the policy skills without saying which copy wins. The other route is a PR to the plugin's skill (build guide step 20's update rule), which reaches a project only through its pin bump (decision 8).
- **The record cannot say which policy text judged a change.** The spec header names the plugin version and the overrides, not the owner's text. The article logs "the skill versions in force" with the spec (p.14), and decision 8 chose the plugin because copies "cannot record" them.
- **Nothing shows that a policy skill triggers.** The tests check each skill's shape and run its `check.py`; none checks that the model triggers it. Article step 4 (p.22), "Ask Claude to do the relevant task in different ways and confirm the skill loads each time", is not run anywhere.

## What the article says

"Skills are how an organization makes its institutional knowledge operational. The instructions are explicit, version-controlled, applied broadly, and updated centrally when policy changes." The infrastructure is "one policy with a named owner and a written source of truth". Step 2 says "an engineer writes it from the policy owner's source of truth, using Claude to help". Step 3 puts the skill in `.claude/skills/<name>/` or "organization-wide through a plugin" (p.21). Step 4 is "test that the skill triggers. Ask Claude to do the relevant task in different ways and confirm the skill loads each time". Step 5 is "when the policy changes, change the skill and have the policy owner sign off the change". Step 6 is "engineers pick up the new version automatically in their next session" (p.22).

Governance (p.22): "A skill is a control, though an advisory one … A policy that must always hold needs something deterministic behind the skill, such as a hook that blocks the action or a review pass that re-checks the policy at the PR." The measures (p.23) are the time from the policy owner approving a change to the updated skill merging, and "PR reviews findings that cite the policy, which should fall towards zero"; where they do not, "either the skill isn't triggering or its text has drifted from the official policy". Build-phase hooks should "back any skill whose policy has to hold without exception" (p.23). At design, "the spec, the prompt that produced it, and the skill versions in force are all logged in version control", and flagged concerns go "to the named policy owners" (p.14).

In the framework the owner is the policy owner (the one-owner premise). The article's policy owners fold into R28's Security & policy role (the owner's x-roles note, point 1). Who advises the owner on a policy source's PR is the role of the source's kind (point 6 of the same note; R28).

## What the framework does today

Read at `main` 5542406, plugin 1.0.1. The entry's "Today" was read at 619f01a (plugin 0.3.5). `git diff --stat 619f01a 5542406` is empty over `plugin/skills/`, `plugin/gate/preflight.py`, `tests/test_policy_skills.py`, `plugin/init/`, `plugin/scan/prompt.py`, `plugin/panel/briefs/`, `plugin/hooks/protected_paths.py`, `template/.github/workflows/sdlc-evals.yml` and the design, build, fix and init commands, so every line the entry cites still holds. Over the same range `plugin/review/REVIEW_PROMPT.md` changed 16 lines (re-read below), and the shell guard and the sandbox's `denyWrite` list arrived in 0.3.7.

- **The skills.** Five policy skills (`preflight.py:67-73`) each carry a `## Source` section reading "**no owner source yet**": `coding-standards/SKILL.md:13`, `security-baseline:14`, `data-conventions:14`, `ux-conventions:15` and `definition-of-done:16`. Each section also names its project override (`.claude/skills/<name>/SKILL.md`, e.g. `coding-standards:15`). Each skill runs its own advisory `check.py`. Four name their backing under a "Deterministic backing:" label (`security-baseline:50`, `data-conventions:47`, `ux-conventions:47`, `definition-of-done:54`). `coding-standards` does it in a sentence without the label: the formatter hook and the gate's lint target (`:46-47`).
- **Which copy wins.** The override replaces the plugin's skill in the design pass (`sdlc-design.md:73-75`), the preflight (`check_policy_skills`, `preflight.py:144-165`, which only reports "project override" or "plugin"), the REVIEW.md pass (`REVIEW_PROMPT.md:28-31`), the panel's reviewer (`panel/briefs/reviewer.md:14-16`) and the weekly scan. The scan quotes only the `## Rules` section of `security-baseline`, from the override or the plugin (`scan/prompt.py:92-106`). The build and fix commands say "Load the policy skills" without naming a copy (`sdlc-build.md:69-70`, `sdlc-fix.md:45-46`). So do four more readers: the test command (`sdlc-test.md:44`), the adversarial reviewer (`agents/adversarial-reviewer.md:23`), the code-simplifier (`agents/code-simplifier.md:22`) and the panel's advocate (`panel/briefs/advocate.md:16`).
- **The record.** `render_spec_header` writes "Skills: <five names> (plugin <version>); overrides: none | <names>" (`artifacts.py:255-272`; `cli.py` `cmd_spec_header`, 233-254). No owner text and no commit is recorded.
- **The tests.** `tests/test_policy_skills.py` checks each skill's shape and runs its `check.py` against an initialised fixture; none checks that the model triggers it, and the docstring says so: "Whether the model triggers a skill is a live check, not a layer-1 test" (lines 1-5). Line 51 asserts that "no owner source yet" stays in each Source section, so this proposal changes that test with the behaviour.
- **The eval runners.** The framework has its own suite in `evals/cases/`. `.github/workflows/framework-evals.yml` runs it on every pull request that changes `plugin/**`, `template/**` or `evals/**`, and nightly (lines 12-21). The runner knows four check kinds: `command`, `file`, `output` and `denied` (`plugin/evals/run.py:117`). It reads `claude -p --output-format json` (`:411`), whose result carries no tool calls, so no existing check can see a skill load. Its `parse_result` already accepts the verbose shape, a list of messages, and keeps only the last `result` message (`:425-447`). `docs/notes/13.md` keeps "a `claude plugin eval` suite that only checks skill triggering (`tool_used: Skill`, …)" as an advisory option only (lines 76-77). A project's `sdlc-evals.yml` runs on `CLAUDE.md`, `.claude/**` and `evals/**` (lines 31-34).
- **The guardrail list is one list, read by four layers.** `ALWAYS_PROTECTED = ("/.claude/**", "/CLAUDE.md", "/REVIEW.md", "/sdlc.yaml")` (`protected_paths.py:46`) is joined with the project's `protected_paths` by `protected_patterns` (`:61`). That one list is read by:
  - the edit hook;
  - the shell guard (`shell_guard.py:914`);
  - the gate's `check_guardrails` (`checks.py:650-664`);
  - the runner's guardrail park before a run (`run_phase.py:691-719`, called at `:1677`).

  Three more lists name the four files on their own: the `Edit(/…)` deny rules (`template/.claude/settings.json:8-11`, `plugin/ci/settings.ci.json:9-12`), the preflight's `REQUIRED_DENY`, which checks those rules (`preflight.py:75`), and the sandbox's `denyWrite` (`settings.ci.json:56`, rewritten with the project's `protected_paths` appended by `ci_settings_file`, `run_phase.py:1144-1165`). The hook has no exception: "a change to the guardrails is made by the owner, in a session without this hook" (`protected_paths.py:13-16`).
- **`/sdlc-init`.** It creates `REVIEW.md`, `changes/README.md`, `evals/`, `bands.yaml` and `lessons/` create-only (`sdlc_init.py:527-543`). Change 0000's intent names no policy source (`_init_intent`, `:587-611`). No `policies/` path appears anywhere under `plugin/`, `template/` or `tests/` (`git grep -n policies 5542406 -- plugin template tests` finds prose only).

## The proposal

The owner's choice at build-skills (better: the playbook; decision: blend) adds to the framework and replaces nothing. The five generic policy skills stay in the pinned plugin (decision 8). A full project override in `.claude/skills/` stays the owner's to add (decision 6). A new skill version reaches the phase jobs only through the owner's pin bump.

1. **Who writes.** The owner writes the policy sources the skills derive from. Claude may draft one in a PR the owner merges, never in a run, which is today's rule for every guardrail file: a session without the protected-path hook. The skill text stays the framework's.
2. **Where they live.** In the project, one file per policy skill in a `policies/` folder (name judged with T4, R45). `/sdlc-init` creates the folder empty, and the change-0000 intent lists it as starting empty (setup-adopt). R30 builds the change-0000 list's slot and names `policies/` in it as this proposal's line; whichever of R27 and R30 lands second adds the line (`starting-a-project.md`, point 3).
3. **The skills read their source.** Each plugin skill reads its project source, and the source wins where they differ. The next run therefore picks up the owner's edit with no pin bump. The close names this proposal's scope "build-skills' part: `policies/`, the trigger evals; no code beyond the skills reading a source" (the record, section 8, T1's row). The build-skills note itself decides items that need code: `policies/` as a guardrail path, the source file's commit in the spec header, and trigger evals "seen in the run's tool calls". Which code this proposal carries is the owner's to confirm ("What to settle").
4. **A guardrail path** (amends decision 6). A run never edits the policy that judges it. The owner's PR on a source gets build-config's role brief with the eval result, and the owner's merge of that PR is the sign-off the article asks of the policy owner (p.22 step 5). Which role writes that brief, the role of the source's kind, is R28's (x-roles, point 6 of the owner's note).
5. **The record.** The spec header records the source file's commit beside the plugin version, so a change's record shows which policy text judged it.
6. **How each is tested.** Each policy skill gets a trigger eval in the framework repository, run on each plugin release. The eval sends three prompts that ask for the task without naming the skill and passes when the skill loads, seen in the run's tool calls (to verify when built; article p.22 step 4). A project override gets the same case in the project's `evals/`.
7. **Backing kept.** Every existing layer stays:
   - each skill's advisory `check.py`;
   - the REVIEW.md pass at (e), which re-checks every rule the spec cited and every rule the diff touches ("a review pass that re-checks the policy at the PR", p.22);
   - the secrets hook, the gate and the risk list.

   Each skill's "Deterministic backing" line will list, rule by rule, what a hook or the gate enforces and what only the review pass re-checks; `coding-standards` gains the label. A new hook is decided rule by rule once the owner's sources exist, so this proposal adds none. This settles T8's "back any skill" (R33, `target-design.md` T8 Open).
8. **Not proposed here:**
   - the documents column of the agent catalogue (which agent reads which skills and, through them, which sources), the product source for the Product role, the roles and the manager: R28;
   - the project's eval workflow running on `policies/**`: T13, R35;
   - the folder's name: T4, R45;
   - the guide command naming the policy sources as a new project's first step: R19.

## How it is judged

This section is the session's reading of the article's measures, not part of the entry:

- **Triggering.** On each plugin release each of the five policy skills loads on all three of its prompts in the framework's eval run. A skill that does not load is the failure the article names: "the skill isn't triggering" (p.23).
- **The record and the guardrail.** On the sample, once the owner has merged one source:
  - the next design run's spec header names that source's commit;
  - a run that edits `policies/` is denied by the hook, or else parked by the runner or the gate;
  - the owner's next edit to the source reaches the following run with no pin bump.
- **The lagging measure** is the article's own (p.23): the REVIEW.md pass's findings that cite a policy should fall toward zero over later changes. It is read from the review evidence, and no counter is proposed.

## What to settle before building

Every "Recommended" below is the session's, except where a row says the entry or a later choice settles it.

| Question | Recommended |
|---|---|
| The folder's name | **The entry leaves it to T4 (R45), placed last.** Build with `policies/`, and T4 renames it with the other names if it chooses another |
| Which code this proposal carries, given the close's "no code beyond the skills reading a source" | Mine: read the phrase as "no new reader of the source in code". The skills read their source in their own text. The code the build-skills and setup-adopt notes decide rides here: the guardrail lists, `/sdlc-init`'s folder, the spec header's commit and the eval check kind. The scan's quote of the source (row below) is a code reader beyond the phrase, so it is the owner's call |
| How a trigger eval sees that a skill loaded (to verify when built) | A fifth check kind in `plugin/evals/run.py` that reads the run's tool calls, passing on a `Skill` call that names the skill. Two outputs carry them: the verbose json list, which `parse_result` already reads (`run.py:425-447`), or a stream output; both in place of today's `--output-format json` result alone (`run.py:411`), and the live check picks one. The event's exact shape is checked on one live run and recorded in `docs/notes/` before the design |
| Where the framework's trigger evals run, "on each plugin release" | As cases in this repository's `evals/cases/`, run by `framework-evals.yml` on every PR that changes `plugin/**` and nightly (lines 12-21). That covers each release without a new workflow. Five skills times three prompts makes fifteen runs per evaluation, each with a small `budget_usd` |
| The source files' names and shape | One Markdown file per skill, named after it (`policies/security-baseline.md`, …), with no required headings: the owner writes in their own words. A missing file means the skill's generic rules, as today |
| What `/sdlc-init` puts in the "empty" folder (git keeps no empty directory) | A `policies/README.md`, create-only like `lessons/README.md`, that names the five policy files and says a missing file leaves the skill generic. R28 adds the product source's line, which the owner's x-roles note puts beside these sources. No stub source files, because a stub would read as a policy |
| Which copy of a source a run reads | The checkout's own copy. The guardrail checks keep a run from changing it, and the spec header's commit then matches what judged the change. An owner edit reaches a change already in flight when its branch takes the default branch. The alternative is the default branch's copy, read as `sdlc.yaml`'s pin is (`template/.github/scripts/sdlc_pin.py`), which would need code beyond the skills' text |
| The consumers that build a skill's text in code | The weekly scan quotes `security-baseline`'s `## Rules` only (`scan/prompt.py:92-106`), so it would never see the source. It should quote the source too, under the same rule (the source wins). That is a code reader of the source, beyond the close's phrase, so it is the owner's call. The entry does not name this gap |
| The readers' silence on which copy wins | One sentence each, as `sdlc-design.md:73-75` has, in the same change, in the build, fix and test commands, the adversarial reviewer, the code-simplifier and the panel's advocate (a row correction the entry records for build and fix, not a new rule; the other four are mine, from the re-read at 5542406) |
| How `policies/` joins the guardrails | Add `/policies/**` to `ALWAYS_PROTECTED`, which reaches the hook, the shell guard, the gate and the runner's park through one list; add `Edit(/policies/**)` to both settings files' deny rules and to the preflight's `REQUIRED_DENY` (`preflight.py:75`), so the preflight checks the new rule; add `policies` to the sandbox's `denyWrite` (`settings.ci.json:56`). T29 (R44) lists that last entry, and since 0.3.7 the list exists, so it can ride here. Every place that names the four guardrails gains the folder (`git grep` at 5542406): `template/CLAUDE.md:30`, `template/REVIEW.md:21`, `template/sdlc.yaml:137`; the commands (`sdlc-init.md:155`, `sdlc-plan.md:81`, `sdlc-design.md:229`, `sdlc-build.md:17` and `:195`, `sdlc-fix.md:148`, `sdlc-test.md:170`, `sdlc-deploy.md:246`, `sdlc-maintain.md:143`); the gate's failure message (`checks.py:691`); the hook's reason (`protected_paths.py:5`, `:51`); and `OPERATING_MODEL.md` §8 (line 121). A project's own `CLAUDE.md` and `REVIEW.md` stay the owner's edit |
| The framework-change exception (OPERATING_MODEL §3) | `policies/` follows the other guardrails: a branch whose intent says "Framework change: yes" is exempt from the runner's park (`run_phase.py:714-716`), and the gate's `check_guardrails` exempts a declared framework change and change 0000 by its id (`checks.py:681-686`), so change 0000 can create the folder |
| Who adds an override's eval case to the project's `evals/` | The owner, in the PR that adds the override, copied from the framework's case for that skill. A preflight note on an override without its case is optional |
| Which brief the owner's PR on a source gets, and when | **Settled by x-roles (2026-10-09)**: the brief is the role of the source's kind, with the eval result quoted (R28). Until R28 and R35 the owner's PR on a source gets neither: no role brief exists today, and `sdlc-evals.yml` runs on `CLAUDE.md`, `.claude/**` and `evals/**` only (lines 31-34) |

## Considered and not chosen

- **A required status check on the eval result (build-config):** the owner's Exempt bypass would skip it. The eval result reaches the owner in the brief instead (R28).
- **Claude writing or changing a source in a run:** the owner's note says "never in a run". A run never edits the policy that judges it.
- **The article's step 2 as written, a skill rewritten from each project's policy (p.21):** the owner's blend keeps the skill text the framework's. The owner's words go in the source, which wins where they differ, and a full override stays available, as today.
- **A new hook now:** the entry decides each one rule by rule, once the owner's sources exist.

## Decisions it touches

- **6 is amended:** its list of guardrail paths gains the project's `policies/` folder, with the same three layers. The decision file is written before the intent, in a documentation PR, as the close asks: "written before the intent as R6 and R10 do" (the record, section 8, part 1). This proposal writes no decision file and reserves no number.
- **Kept:**
  - 8: the skills stay in the pinned plugin and a new skill version still needs the pin bump; only the owner's source bypasses it, because it is project content;
  - 4: the owner merges the source PR, with the Exempt bypass;
  - 17: the project's suite still starts empty, and the trigger cases are framework-level, with an override's case added by the owner;
  - 7: Python only;
  - 11: a run that edits `policies/` parks like any guardrail edit.
- **Left to R28:** the new decision file for the roles and the one-owner premise.

## Order

This proposal comes first among the roles in the confirmed order (the record, section 8: the record and the approvals, the owner's surface, the gate changes, then "T1's sources, then T1 with T2"). It follows R22 to R26 and comes before R28. R28 depends on it, because the roles read these sources through the skills. It depends on no other candidate: R30's change-0000 list, R35's trigger and R44's sandbox entry each meet it but need not come first. It changes `plugin/`, `template/` and `tests/`, so it ships as a plugin version with tests and reaches a project through the pin bump and `/sdlc-init`.

| Part | Where | When |
|---|---|---|
| Decision 6's amendment | `docs/decisions/`, a documentation PR | First, before the intent |
| The skills read their source; `coding-standards` gains the "Deterministic backing" label; the readers say which copy wins | `plugin/skills/*/SKILL.md`, `plugin/commands/sdlc-build.md`, `sdlc-fix.md`, `sdlc-test.md`, `plugin/agents/adversarial-reviewer.md`, `code-simplifier.md`, `plugin/panel/briefs/advocate.md`, `tests/test_policy_skills.py` | Now |
| `policies/` created empty and listed in change 0000 | `plugin/init/sdlc_init.py`, `template/` | Now; the list itself with R30 if R30 lands first, with this proposal's `policies/` line added to it |
| `policies/` a guardrail path | `plugin/hooks/protected_paths.py`, both settings files, `plugin/gate/preflight.py` (`REQUIRED_DENY`), the sandbox's `denyWrite`, the guardrail wording | Now, after the decision file |
| The source's commit in the spec header | `plugin/gate/artifacts.py`, `plugin/gate/cli.py`, `plugin/skills/spec-template/SKILL.md`, `tests/test_gate.py` | Now |
| The trigger evals | `plugin/evals/run.py` (a check kind), `evals/cases/` | After a live check of how a skill load shows in a run's output, recorded in `docs/notes/` |
| The scan quotes the source | `plugin/scan/prompt.py` | Now, if the owner takes the recommendation |
| The project's eval run on `policies/**` | R35 | With R35 |
| The brief on the owner's source PR | R28 | With R28 |
| The folder's final name | R45 | Last |
