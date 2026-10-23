# Progress — the preflight checks `Edit(/policies/**)`, plugin 1.0.37 (2026-10-23)

This session ran on branch `claude/preflight-policies-deny`, from `main` at `9554cf4` (#369), as the small lane of wave 3, on the central session's message of 2026-10-23: the owner applied the guardrail row of R27's record (`docs/progress/2026-10-23-claude-r27-policy-sources.md`, "What I need from you", point 1, and "Proposed edits for the owner"), so `template/.claude/settings.json` carries `Edit(/policies/**)` (line 17, #369); the follow-up that point recommends adds the rule to the preflight's `REQUIRED_DENY`. This PR changes `plugin/`, so it bumps the patch: `python tasks.py next-free` after `git fetch origin` gave 1.0.37 on `9554cf4`, with 1.0.36 held by lane A (`claude/r18-failed-run-explains-itself`); `python tasks.py version-check` exits 0. No choice, note or decision number is taken.

## What was built
1. **`plugin/gate/preflight.py`**: `REQUIRED_DENY` gains `Edit(/policies/**)` (decision 40). A project whose `.claude/settings.json` lacks it fails the `settings` check with "deny rule Edit(/policies/**) missing" and is told to re-run `/sdlc-init`, which only adds the missing rules.
2. **`tests/test_preflight.py`**: a project initialised from the template carries the rule and passes; the same project without it fails with that problem and that need.
3. **`tests/test_templates.py`**: the settings contract reads the rules from `preflight.REQUIRED_DENY`, so the template and the preflight cannot drift apart again.

## Every settings file the preflight reads, checked
- **The preflight reads one file**, the project's `.claude/settings.json` (`check_settings`). A project the template makes gets the rule from `template/.claude/settings.json:17` (verified, `git show origin/main:template/.claude/settings.json`); the test fixture `tests/fixtures/sample-python-project` is initialised from the template by `sdlc_init.py` in `tests/test_preflight.py`, so it carries it (the new test asserts it first).
- **`plugin/ci/settings.ci.json`** already carries `Edit(/policies/**)` and `policies` in `denyWrite` (R27, #367); the preflight does not read it.
- **This repository's own `.claude/settings.json`** does not carry the rule, and the preflight never runs on this repository; it has no `policies/`. Left as it is (a guardrail file).

## Known limits, recorded
- **A project initialised before #369** fails the preflight until `/sdlc-init` re-runs on its upgrade (the sample project included), as R27's record recommended; the failure's need says so. The hook, the shell guard, the gate, the runner's park and the CI settings already refuse the edit meanwhile.
- **`plugin/skills/security-baseline/check.py`** has its own `REQUIRED_DENY` (four rules, without `REVIEW.md` either); it is the skill's advisory check, not the gate's, and is left as it is.

## Port list
This PR touches none of `plugin/detect/`, `plugin/ci/run_phase.py` or the detect, runbook and fix workflow templates.

## Proposed edits for the owner
None.

## What the owner does
| When | Act |
|---|---|
| When the small lane says it is ready | Merge this PR when `Framework checks` is green on its final head. |
