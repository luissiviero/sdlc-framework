---
type: Proposal
title: Starting a project — the whole loop from the first change, with an optional start by hand
description: The whole loop from the first change stays the default, with no staged adoption and no per-phase switch; added, nothing replaced, an optional by-hand start documented in /sdlc-init step 6 and the README (no Claude secret, every phase job ends "skipped", the owner runs the phase commands, adding the secret later turns the automation on), and a short list in the change-0000 intent of what starts empty (evals, lessons, "Things Claude gets wrong", the detection).
status: accepted
roadmap: R30
sources:
  - id: study-entry
    resource: docs/reviews/2026-09-28-playbook-vs-framework/target-design.md
    title: "T5, confirmed at the close of the study on 2026-10-09; from the crosswalk row setup-adopt (better: the framework; decision: blend), 2026-10-02"
  - id: crosswalk
    resource: docs/reviews/2026-09-28-playbook-vs-framework/crosswalk.json
    title: "Row setup-adopt (whole); the decision fields of design-trigger (the by-hand start is T5's), test-evals (T13) and maintain-detect (T22); the decision field of build-skills (T1, 2026-10-03: `policies/` created empty and listed in change 0000 as starting empty)"
  - id: record
    resource: docs/reviews/2026-09-28-playbook-vs-framework.md
    title: "Section 7, the close; section 8 part 1, the close table's T5 row (amends none; suggested yes; owner yes); part 2, the confirmed order (T5 among 'the rest in any order')"
  - id: playbook
    resource: docs/reference/ai-native-sdlc-playbook.pdf
    title: "p.7: the steps are modular, stages transformed at different times; p.8: each step prompted by hand first, the plays adopted in the dependency graph's order; p.13: by hand, then a slash command, then a job that fires on the merge; p.17: auto-accept the default for routine work as the guardrails mature"
  - id: decision-1
    resource: docs/decisions/1.md
    title: "Decision 1: hosted CI with either secret (kept; the default)"
  - id: decision-17
    resource: docs/decisions/17.md
    title: "Decision 17: evals start empty and fill from incidents (kept; stated in one more place)"
  - id: decision-16
    resource: docs/decisions/16.md
    title: "Decision 16: the weekly scan (kept; read for the open item on a scan with no secret)"
  - id: code
    resource: plugin/init/sdlc_init.py
    title: "_init_intent and maintain_observation; with plugin/commands/sdlc-init.md steps 3 and 6, README.md 'Phases by hand', plugin/ci/auth.py, plugin/ci/run_phase.py run_phase, plugin/scan/cli.py cmd_review, template/.github/workflows/sdlc-scan.yml and sdlc-design.yml, plugin/detect/stats.py, plugin/detect/source.py, plugin/evals/run.py, plugin/skills/intent-template/SKILL.md, template/evals/README.md, template/lessons/README.md, template/CLAUDE.md, template/sdlc.yaml paused, tests/test_ci.py test_no_credential_skips_instead_of_failing; read at main 5542406, plugin 1.0.1"
generated: { by: sdlc-framework-session/ccr-01de3f80-ilnomi, at: 2026-10-15T20:00:00Z }
---

# Starting a project: the whole loop from the first change, with an optional start by hand

**Status: proposed (roadmap R30), from study entry T5, confirmed by the owner on 2026-10-09; the blend of the crosswalk row setup-adopt, the two additions the owner's note numbers #2 and #3 (the row has no option letters).** *[2026-10-20: accepted 2026-10-16 (PR #215); rank 28; the rank is read from ROADMAP's Order column]* Nothing is built. It amends no decision: decision 1 (hosted CI) stays the default, and decision 17 (evals start empty) is stated in one more place. It is documentation, a change to the code that generates one file (the change-0000 intent, a plugin version) and, if the first row of "What to settle" is taken, the scan's skip; it sits among the study's "rest in any order" group; the guide command of R19 (T27) points the owner of a new project at the by-hand start this proposal documents.

## The problem

A project that runs `/sdlc-init` gets the whole loop at once, and that stays (the owner's note: "keep: no staged adoption, no per-phase switches"). Two things are missing around it:

- **The start without the Claude secret works but is not offered.** Without `CLAUDE_CODE_OAUTH_TOKEN` or `ANTHROPIC_API_KEY` every phase job already ends green as skipped and each phase can be run by hand, but `/sdlc-init` step 6 presents the secret as required ("The workflows also need the repository secret", `plugin/commands/sdlc-init.md:124-125`). The article's ladder, by hand first and then a job that fires on the merge (p.8, p.13), is available to a project only by accident.
- **What starts empty is said file by file, not where the owner looks.** The evals suite (`template/evals/README.md:11`), `lessons/` (`template/lessons/README.md`), CLAUDE.md's "Things Claude gets wrong" (`template/CLAUDE.md:23-25`, "(none yet)") and the detection's need for a CI workflow of the project's own (the install report, `sdlc_init.py:336-345`) each sit in their own file; the change-0000 intent the owner reads before merging the install names none of them (`sdlc_init.py:587-612`), and nothing says the detection needs about 16 days of data before its first verdict.

## What the article says

"The steps are modular and organizations may choose to prioritize transforming different stages at different times based on their unique needs" (p.7). "First, you prompt each step by hand with the end state being a loop in which each accepted artifact fires the next gate"; the plays are adopted in the dependency graph's order: "Start with any clay play — nothing points into it", and adopt any other play after those whose arrows point into it (p.8). For the design pass: "Run it by hand at first, then codify it as an organization-level slash command. From there make the acceptance of intent.md in the intent home the trigger, with a non-interactive job that fires on the merge" (p.13). "As the guardrails from the later plays mature ... auto-accept becomes the default for routine work" (p.17)[^playbook]. The framework's own guardrails were built that way (by hand in stage B1, CI from B3; decision 1), so a project does not repeat it; the optional by-hand start offers the ladder per project. The counting call of the same day: the organization's choice of which stages to transform first counts as a once-per-project Setup decision on the playbook's side (the record's section 6 reads 14 + 2)[^record].

## What the framework does today

Read at `main` 5542406, plugin 1.0.1. The entry has no "Today" block; its code facts sit in its "Direction discussed", written at 5a31959 (2026-10-02). `git diff --stat 5a31959 5542406` over `plugin/commands/sdlc-init.md`, `plugin/init/sdlc_init.py`, `plugin/ci/auth.py`, `plugin/detect/stats.py`, `plugin/scan/cli.py`, `template/.github/workflows/sdlc-scan.yml`, `template/evals/README.md`, `template/CLAUDE.md` and `README.md` changes `README.md`, in lines that are not "Phases by hand", and the module docstring of `plugin/scan/cli.py` (13 insertions, 12 deletions); every line the entry cites still holds.

- **The whole loop in one PR.** `/sdlc-init` step 3 writes the guardrails, `evals/` ("empty suite, filled by incidents — decision 17", `sdlc-init.md:62`), `bands.yaml`, change 0000 and the twelve `sdlc-*.yml` workflows, all in the change-0000 PR (`sdlc-init.md:55-84`, step 5 `:90-108`). No setting installs a subset; `sdlc.yaml: paused` stops every run at once (`template/sdlc.yaml:109-110`).
- **No credential: skipped, after the setup.** `auth.choose_auth` returns no credential when neither secret is set (`plugin/ci/auth.py:55-62`). `run_phase` installs the project's toolchain first and returns red when it fails (`run_phase.py:1633-1638`), then skips a run with no credential with "no credential: set the repository secret ..." and exit 0 (`:1642-1643`, `_skip` `:235-237`), verified by `tests/test_ci.py:1683-1687` (`test_no_credential_skips_instead_of_failing`). In the workflow the setup step also runs before the phase step (`sdlc-design.yml:116-120`). The fix round's runner path is the same function.
- **The weekly scan fails instead.** `scan/cli.py cmd_review` (`:162-212`) has no credential check: it runs `claude -p` and returns exit 1 when the run fails (`:201-206`). The deterministic scanners run after it on `always()` and never fail the job (`sdlc-scan.yml:111-114`). The entry's "fails red until the secret exists" follows from the code; it is not verified by a run here.
- **The secret presented as required.** Step 6 (`sdlc-init.md:110`) lists it beside the workflow permission (`:120-125`, the secret at `:124-125`) and the ruleset (`:126`), with no word on running without it. `README.md:24` ("Phases by hand") lists the by-hand commands and ends "With the workflows installed, everything after the first merge runs on its own"; it does not say that leaving the secret out is a way to start.
- **The change-0000 intent.** `_init_intent` (`sdlc_init.py:587-612`) writes Problem, Proposed outcome (the plugin version, the profile, the three targets), Affected users and systems, Constraints and Open questions (the detection notes); it is written only when absent (`:569-572`). The intent template keeps the article's five sections in order (`plugin/skills/intent-template/SKILL.md:13-14`).
- **The detection's start.** The tail is the last `TAIL = 8` points and fewer than `MIN_BASELINE = 8` baseline points give tier 0, "insufficient baseline" (`plugin/detect/stats.py:16-20`, `:56-57`), one point per UTC day with at least one counted run (`plugin/detect/source.py:159`): about 16 counted days before a first verdict. The install report already says when the project has no CI workflow of its own (`maintain_observation`, `sdlc_init.py:365-390`; `sdlc-init.md:78-83`).

## The proposal

Both additions add to the framework and replace nothing; the default stays as it is today.

1. **The default, as today.** `/sdlc-init` installs the whole loop in the change-0000 PR. No staged adoption in the p.8 order, no per-phase switch; `sdlc.yaml: paused` still stops every phase at once.
2. **An optional start by hand, documented.** One optional paragraph in `/sdlc-init` step 6 and one sentence in `README.md`, "Phases by hand": leave the repository secret (`CLAUDE_CODE_OAUTH_TOKEN` or `ANTHROPIC_API_KEY`) out, and every phase job ends green as skipped, with the reason "no credential: ..." (`{"skipped": ...}`, `run_phase.py:235-237`), once the project's setup command has succeeded, since it runs first; the owner runs each phase's command in their own Claude Code session. The weekly scan fails red instead until the secret exists. Adding the secret turns the automation on, and nothing else changes. *[2026-10-20, R60's answers (the owner; `docs/reviews/2026-10-20-lifecycle-axis-ports/options.md`, section 2, row "Start by hand (no Claude secret)"): this point is dropped. Every project gets the Claude secret at setup and runs from CI from change 0000 on; the no-credential skip stays in the code as the safe failure for a missing secret, not as an offered start. Point 3 is unaffected]*
3. **What starts empty, said in one place.** The change-0000 intent that `sdlc_init.py` writes gains a short list naming the evals suite (decision 17; it fills from incidents), `lessons/`, the "(none yet)" in CLAUDE.md's "Things Claude gets wrong", and the detection, which needs a CI workflow of the project's own and about 16 days of daily CI data before its first verdict (8 baseline points before the 8 most recent points it judges). The owner's build-skills decision (T1, 2026-10-03) adds `policies/`, which `/sdlc-init` creates empty, to the same list; R27 creates the folder and its line, and the list's slot is built here, so whichever of the two lands second adds the line.

## How it is judged

On the next project installed (and once on the sample project, `sdlc-sample-python`, without the secret): the change-0000 PR's intent lists the things that start empty; with no secret, each phase job of one change ends green, skipped with the reason "no credential: ...", and the owner carries the change to gate (e) with the phase commands alone; adding the secret makes the next merge's phase job run, with no file in the project changed. The failure is a by-hand project that needed an edit beyond the secret to turn the automation on, or an owner surprised by an empty eval suite or a detection with no verdict that the intent did not announce.

## What to settle before building

| Question | Recommended |
|---|---|
| Whether the weekly scan should end "skipped" like the phase jobs when no secret exists, instead of failing (the entry's Open item; a code change, not only documentation) | Mine: yes. `cmd_review` checks `auth.choose_auth` as `run_phase` does (`run_phase.py:1642-1643`) and skips with the same reason; the deterministic scanners still run (`sdlc-scan.yml:111-114`). Otherwise a by-hand project shows a red scan run every week, which R18's "Failed runs" line (T19) would list in the digest once R43 (T26) feeds the scan into it. Decision 16 is kept: the scan still runs weekly once a credential exists. Until settled, the paragraph says "fails red", as the owner's note does |
| The exact wording of both additions (the entry's Open item) | Written after the study with the rest, from the owner's note. Mine: step 6 then presents the secret as the switch between the two starts, not as a requirement; the paragraph names the secret as a desktop-only act with R21's link once R21 is built (both edit the same step 6 bullet) |
| Where the list goes in the change-0000 intent | Mine: the end of "Proposed outcome", one line per item, since the intent template keeps the article's five sections in order (`SKILL.md:13-14`); a new heading would break that |
| Whether "about 16 days" is written or computed | Mine: computed in `_init_intent` from `stats.MIN_BASELINE + stats.TAIL`, so the intent never disagrees with the detection; "counted days" (a day with no run of the project's own CI counts no point, `source.py:159`) |
| What else runs on a by-hand project (the digest, the release, the abandon rule, the detection's deterministic step, the evals workflow once a case exists, a breach's `finish` step with the diagnosis skipped) | Mine: to verify on the sample before the paragraph is written, and the paragraph says only what was seen; the eval runner passes an empty suite ("no cases", `plugin/evals/run.py:61-62`), a case with no credential is not verified |
| Whether existing projects get the list | Mine: no change needed. The intent is written only when absent (`sdlc_init.py:570`); the list reaches new installs, and the docs reach everyone with the plugin |

## Considered and not chosen

- A staged adoption in the p.8 order, or a per-phase switch in `sdlc.yaml`: the owner's note keeps "no staged adoption, no per-phase switches"; `paused` stays the one switch, for every phase at once.
- The by-hand start as the default: decision 1 stays the default, and the framework's own guardrails already went through the ladder (B1 by hand, CI from B3).
- Leaving each "starts empty" fact in its own file only: the intent the owner reads before merging the install is where the owner decides, so the list goes there.

## Decisions it touches

None amended, so no decision file comes before the intent. 1 is kept (hosted CI the default; the by-hand start is optional). 17 is kept and stated in one more place. 16 is read for the scan's open item and kept either way. 11 and 20 are untouched: nothing notifies the owner of a skipped run.

## Order

In the study's confirmed order, T5 is in "the rest in any order" (the record, section 8), after the gate changes (R22 to R26) and the roles (R27, R28). *[2026-10-20: at rank 28 R30 comes after R45 (20) and before R23 (31); the rank is read from ROADMAP's Order column]* It depends on no other R number. Beside it: R19 (T27, accepted) has its guide command name T5's by-hand start as a first step on a new project, so the guide's text points at this paragraph; R21 edits the same step 6 bullet (the secret as a desktop-only act), so whichever lands second keeps both; R18 (T19, accepted) lists the scan's red run, once R43 (T26) feeds the scan into its "Failed runs" line, unless the first settle row is taken; R27 (T1's sources) creates `policies/` empty and leaves its line in this list to whichever of the two lands second; R33 (T8) proposes the formatter commands in the same change-0000 PR and edits `sdlc_init.py`, so whichever lands second keeps both; R40 (T22) counts the days until the detection's baseline fills in the digest, where this intent states it once at install; R45 (T4) renames the commands this paragraph names, and goes last. *[2026-10-20: at rank 28 R30 comes after R45 (20) and before R23 (31); R45 does not go last; the rank is read from ROADMAP's Order column]* The parts:

| Part | Where | When |
|---|---|---|
| The optional by-hand paragraph and the README sentence | `plugin/commands/sdlc-init.md` step 6, `README.md` "Phases by hand" | Now, after the live check on the sample without the secret |
| The "starts empty" list in the change-0000 intent, with a test | `plugin/init/sdlc_init.py` `_init_intent`, the init tests | Now; a plugin version |
| The scan's skip with no credential, if the first settle row is taken | `plugin/scan/cli.py` `cmd_review`, its test | Now, same change |

[^playbook]: `docs/reference/ai-native-sdlc-playbook.pdf` p.7, p.8, p.13, p.17.
[^record]: `docs/reviews/2026-09-28-playbook-vs-framework.md`, sections 6 and 8; `target-design.md` T5, "Counting call".
