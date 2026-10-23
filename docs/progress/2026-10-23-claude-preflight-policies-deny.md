# Progress — the preflight checks `Edit(/policies/**)`, plugin 1.0.38 (2026-10-23)

This session ran on branch `claude/preflight-policies-deny`, from `main` at `9554cf4` (#369), as the small lane of wave 3, on the central session's message of 2026-10-23: the owner applied the guardrail row of R27's record (`docs/progress/2026-10-23-claude-r27-policy-sources.md`, "What I need from you", point 1, and "Proposed edits for the owner"), so `template/.claude/settings.json` carries `Edit(/policies/**)` (line 17, #369); the follow-up that point recommends adds the rule to the preflight's `REQUIRED_DENY`. This PR changes `plugin/`, so it bumps the patch: `python tasks.py next-free` after `git fetch origin` gave 1.0.37 on `9554cf4`, with 1.0.36 held by lane A (`claude/r18-failed-run-explains-itself`), but lane B's `claude/r64-template-copies-refresh` (#370) bumped to 1.0.37 five seconds earlier, and `python tasks.py version-check` failed this branch on the next fetch; the PR takes 1.0.38, the number `next-free` then gave, and `version-check` exits 0. It merges after R18 (1.0.36) and R64 (1.0.37), so `main`'s versions only rise. No choice, note or decision number is taken. No choice, note or decision number is taken.

## What was built
1. **`plugin/gate/preflight.py`**: `REQUIRED_DENY` gains `Edit(/policies/**)` (decision 40). A project whose `.claude/settings.json` lacks it fails the `settings` check with "deny rule Edit(/policies/**) missing" and is told to re-run `/sdlc-init`, which only adds the missing rules.
2. **`tests/test_preflight.py`**: a project initialised from the template carries the rule and passes; the same project without it fails with that problem and that need.
3. **`tests/test_templates.py`**: the settings contract reads the rules from `preflight.REQUIRED_DENY`, so the template and the preflight cannot drift apart again; `tests/test_ci.py` checks the CI settings' `//<root>` rewrite of `Edit(/policies/**)` beside the other four.
4. **`plugin/commands/sdlc-init.md`**: the upgrade note for 1.0.38, beside the earlier versions' notes: re-run `/sdlc-init` in the pin's pull request, since it adds the rule.

## The fresh-context review
A fresh-context sub-agent reviewed `5b526f3` (report only), ran the preflight, template, CI and end-to-end tests (all green) and checked a `/sdlc-init` re-run in five shapes of an older project's settings (each failed before and passed after, a custom rule kept). Its findings and what was done:
1. **Blocking, fixed:** 1.0.37 was taken first by lane B's R64; renumbered to 1.0.38 (`2f25f42`).
2. **Blocking, fixed:** the record said the preflight never runs on this repository; it does, through the pinned framework. Corrected below, with the owner's row.
3. **Optional, taken:** the `/sdlc-init` upgrade note; the CI rewrite test.
4. **Optional, left:** `plugin/skills/security-baseline/check.py` keeps its own list (under "Known limits").

## Every settings file the preflight reads, checked
- **The preflight reads one file**, the project's `.claude/settings.json` (`check_settings`). A project the template makes gets the rule from `template/.claude/settings.json:17` (verified, `git show origin/main:template/.claude/settings.json`); the test fixture `tests/fixtures/sample-python-project` is initialised from the template by `sdlc_init.py` in `tests/test_preflight.py`, so it carries it (the new test asserts it first).
- **`plugin/ci/settings.ci.json`** already carries `Edit(/policies/**)` and `policies` in `denyWrite` (R27, #367); the preflight does not read it.
- **This repository's own `.claude/settings.json`** does not carry the rule, and the preflight does run here: the repository runs the pipeline on itself (`sdlc.yaml` pins plugin 1.0.17, `changes/0001` to `0005`, `.github/workflows/sdlc-build.yml` runs `run_phase.py`, which calls the preflight). The pinned 1.0.17 preflight does not require the rule, so nothing breaks today; once the pin is raised to 1.0.38 or later, every build here parks with "deny rule Edit(/policies/**) missing". The file is a guardrail, so the edit is the owner's: "Proposed edits for the owner" below, to land no later than the PR that raises this repository's pin to 1.0.38 or later.

## Known limits, recorded
- **A project initialised before #369** fails the preflight until `/sdlc-init` re-runs on its upgrade (the sample project included), as R27's record recommended; the failure's need says so. The hook, the shell guard, the gate, the runner's park and the CI settings already refuse the edit meanwhile.
- **`plugin/skills/security-baseline/check.py`** has its own `REQUIRED_DENY` (four rules, without `REVIEW.md` either); it is the skill's advisory check, not the gate's, and is left as it is.

## Port list
This PR touches none of `plugin/detect/`, `plugin/ci/run_phase.py` or the detect, runbook and fix workflow templates.

## Proposed edits for the owner
| Link | Row | What is there now | What it must become |
|---|---|---|---|
| [.claude/settings.json](https://github.com/luissiviero/sdlc-framework/blob/main/.claude/settings.json#L16) | 16 | `"Edit(/.git/hooks/**)",` | `"Edit(/.git/hooks/**)",` followed by `"Edit(/policies/**)",` on the next line (no later than the PR that raises this repository's pin to 1.0.38 or later) |

## What the owner does
| When | Act |
|---|---|
| When the small lane says it is ready | Merge this PR when `Framework checks` is green on its final head, after R18 and R64. |
| Before this repository's pin reaches 1.0.38 | Apply the row above. |
