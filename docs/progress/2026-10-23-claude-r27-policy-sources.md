# Progress — R27, the policy sources, plugin 1.0.35 (2026-10-23)

This session is lane B of wave 3, started by the central session (`session_016NLfdsdfTFZUyrVGN4Ektc`) at the owner's request. Its scope is R27 as one PR, then R64 as a second after this one merges. It ran on branch `claude/r27-policy-sources`, from `main` at `2a0e7c7` (#363, plugin 1.0.34), after two documentation PRs of its own:
- **#364:** decision 40, "The project's policy sources in `policies/` are a guardrail path (amends 6)", merged as `7cac00e`.
- **#365:** the review's corrections to decision 40, annotated beside its sentences, open at the time of writing.

The scope is R27's row as accepted on 2026-10-16 ("as recommended", PR #215), so every "Recommended" of `docs/proposals/policy-sources.md`, "What to settle before building", is built as written. Exceptions are named under "Departures".

This PR changes `plugin/` and `template/`, so it bumps the patch. It took 1.0.35, the number `python tasks.py next-free` gave after `git fetch origin` on `2a0e7c7`, with nothing taken above `main`. It also takes note 61. It takes no choice number.

## What was built
1. **`policies/` is a guardrail path** (decision 40).
   - `/policies/**` joins `ALWAYS_PROTECTED` (`plugin/hooks/protected_paths.py`). Through that one list it reaches the edit hook, the shell guard, the gate's `guardrails` check and the runner's guardrail park (`run_phase.guardrail_hits`, whose docstring alone changes).
   - `plugin/ci/settings.ci.json` gains `Edit(/policies/**)` among its deny rules and `policies` in `sandbox.filesystem.denyWrite`. `ci_settings_file` rewrites both like the others, with no code change.
   - The hook's reason, the gate's failure message, every command's "Never edit" line, `template/CLAUDE.md`, `template/REVIEW.md`, `template/sdlc.yaml` and OPERATING_MODEL section 8 name the folder.
   - `docs/owner-machine/managed-settings.json` gains `Edit(policies/**)`, spelled without the slash as its other rules are (decision 40, as #365 corrects it).
   - Tests: the hook denies `policies/security-baseline.md` and `policies/README.md` but not `docs/policies/…`; the shell guard denies a redirect into the folder; the gate parks a committed source; the CI settings carry both entries.
2. **The skills read their source.**
   - Each policy skill's "no owner source yet" bullet now names `policies/<name>.md`. The skill reads that file first; the source wins where it and the skill differ, over a project override too; a rule the source does not mention still applies; no file means the skill's rules alone; and the file is never edited in a run.
   - Each skill's "Deterministic backing" now goes rule by rule: what a hook or the gate enforces, and what only the review pass re-checks. `coding-standards` gains the label.
   - `tests/test_policy_skills.py` asserts both, in place of "no owner source yet".
3. **Every reader says which copy wins.** The override replaces the plugin's skill, and the owner's source wins over either. This is stated in the design, build and fix commands, the adversarial reviewer, the code-simplifier, the panel's reviewer and advocate briefs, and the REVIEW.md pass prompt; a test holds all eight. The panel's recorded brief fixtures are regenerated, and only that sentence changed in them.
4. **`/sdlc-init` creates `policies/README.md`**, create-only like `lessons/README.md`. The README names the five sources, says how a run reads them and how they change, and has no stub source. The change-0000 commit's `--paths` gains `policies`; without it the README would not be committed. Change 0000's intent says, under Constraints, that `policies/` starts empty but for its README. A test covers the folder, the README, the intent line and a kept owner edit.
5. **The spec header records each source's commit.** `gate/cli.py spec-header` appends `; policy sources: none | policies/<name>.md@<commit>`, with the commit that last changed the file, shortened to 12, or `@uncommitted`. The gate's required header fields are unchanged, so a spec already written still passes. The `spec-template` skill shows the new field.
6. **The weekly scan quotes the owner's security source** beside the skill's rules, under the same rule (`plugin/scan/prompt.py`, `policy_source`). This is the code reader the proposal left to the owner; its recommendation, accepted with the row, was to build it.
7. **The trigger evals** (article p.22 step 4).
   - A fifth check kind, `skill`, in `plugin/evals/run.py`. A case with one runs with `--verbose`. The check passes when an assistant message holds a `Skill` tool call whose `skill` input is the name exactly (`sdlc:<name>` for the plugin's skill, the bare name for a project's own) and whose result is not an error.
   - Fifteen cases, `evals/cases/0008-*` to `0022-*`: three per policy skill, each asking for the task without naming the skill, with the tools `Read,Grep,Glob,Skill`, a budget of 0.50 USD and `sample_pkg/calc.py` unchanged.
   - `template/evals/README.md` (and this repository's copy) documents the kind, and says a project that overrides a policy skill copies the framework's three cases in the override's PR.
   - NOTES §61 records the output shape from the documentation. The live check is the first `Framework evals` run on this branch.

## Departures from the proposal, and its stale citations
- **Change 0000's list.** R30 builds the intent's "what starts empty" list, and R30 has not landed. So the `policies/` line is a sentence under Constraints, not a new section; R30 moves it into its list (`starting-a-project.md`, point 3).
- **`sdlc-test.md` no longer loads the policy skills.** The proposal cites `sdlc-test.md:44`, but the command on `2a0e7c7` names none, so it gains no sentence.
- **`REQUIRED_DENY` is unchanged** (the preflight, `plugin/gate/preflight.py`). The proposal adds `Edit(/policies/**)` to it. But `template/.claude/settings.json` is the owner's edit, so until the owner adds the rule there, every project the template initialises, the test fixture included, would fail the preflight. Point 1 of "What I need from you" asks.
- **Citations moved since 5542406**, checked on `2a0e7c7`:
  - `ALWAYS_PROTECTED` is at `protected_paths.py:50`;
  - `guardrail_changes` at `run_phase.py:938` and `ci_settings_file` at `:1968`;
  - the create-only list at `sdlc_init.py:786`;
  - the protected-paths comment at `template/sdlc.yaml:189`;
  - the gate's message at `checks.py:738`;
  - the skills' Source bullets at lines 13-16 as cited.
  Each still says what the proposal says it does.

## Not built here
- **The project's eval run on `policies/**`:** R35.
- **The brief on the owner's source PR:** R28.
- **The folder's final name:** R45.
- **A new hook per rule:** once the owner's sources exist (the proposal's point 7).

## What I need from you
1. **The template's deny rule, then the preflight's check.** Recommended: apply the row below in a PR of your own. Then a small follow-up PR (this lane or the small lane) adds `Edit(/policies/**)` to `REQUIRED_DENY`, so the preflight verifies it. A project gains the rule when `/sdlc-init` re-runs on its upgrade, since the install only adds rules. The alternative is to leave `REQUIRED_DENY` as it is: the hook, the shell guard, the gate, the runner's park and the CI settings already refuse the edit.
2. **The live trigger evals.** If a policy skill does not load on its three prompts in this branch's `Framework evals` run, that is the article's "the skill isn't triggering" (p.23). Recommended: keep the cases and fix the skill's description in this PR, not loosen the case.

## Proposed edits for the owner
| Link | Row | What is there now | What it must become |
|---|---|---|---|
| [template/.claude/settings.json](https://github.com/luissiviero/sdlc-framework/blob/main/template/.claude/settings.json#L16) | 16 | `"Edit(/.git/hooks/**)",` | `"Edit(/.git/hooks/**)",` followed by `"Edit(/policies/**)",` on the next line |

## Port list (HANDOFF.md, "Rules for every session")
This PR touches `plugin/ci/run_phase.py` (one docstring), so it goes on the port list until the 1.0.0 read.

## The fresh-context review
A fresh-context sub-agent reviewed `65fe810`, report only. It found nothing blocking; what it found, each fixed with a test where code changed:
1. **Two backing lines claimed a gate check that does not exist.** `ux-conventions` rule 7 and `definition-of-done` (d) cited the gate for screenshots, but `REQUIRED_EVIDENCE` names the verifier report and the toolchain logs only. Both lines now say no gate check requires a screenshot.
2. **The `skill` check counted a call, not a load, and matched across names.** A `Skill` call whose `tool_result` is an error is no longer counted. Names are now matched exactly, so a project override's case (the bare name) cannot pass on the plugin's `sdlc:<name>`. The framework's cases name `sdlc:<name>`.
3. **Uncommitted files:** stale; they were committed in `65fe810` while the review read the tree.
4. **Odd output crashed `skills_loaded`, and a stray line before the JSON hid every call.** Both now parse: a non-dict message or input is skipped, and a line-by-line read extends with a list.
5. **Two pages claimed a project deny rule the template does not carry yet.** `template/policies/README.md` and OPERATING_MODEL section 8 now say the rule is in CI and reaches a project with the owner's template row.
6. **Test gaps, closed:**
   - the `--paths` test lists `policies/README.md`;
   - a modified committed source reads `@uncommitted`;
   - an errored `Skill` call fails its case.
7. **The live risks.**
   - Two prompts read like the built-in review skills, so cases 0008 and 0011 are reworded around "this organization's" rules.
   - The budget is 0.50 USD, as the other cases have.

## Citations checked
- Decision 40 and #365's corrections.
- The article, p.21-23, in `docs/reference/ai-native-sdlc-playbook.txt`.
- NOTES §61's sources, read on 2026-10-23.
- The proposal's line citations, re-read on `2a0e7c7`; the ones that moved are listed above.
