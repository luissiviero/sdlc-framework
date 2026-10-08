# Intent: security: authz: The guardrail self-protection (protected_paths.py) only
Author: security review (phase f). Status: proposed. Change id: 0002. Entry route: incident scan:c433d0293e7a89b4.

## Problem
The weekly security review of the codebase at commit `8050b92d556e` found an Important authz finding in `plugin/hooks/hooks.json:32`: The guardrail self-protection (protected_paths.py) only hooks the Edit|Write|MultiEdit|NotebookEdit tool matcher; the Bash/PowerShell matcher runs plan_sync.py and production_gate.py but never checks a command's target path, and plugin/ci/settings.ci.json's permission allow-list grants bare 'Bash(python *)', 'Bash(python3 *)', 'Bash(node *)', 'Bash(npm *)' and 'Bash(npx *)' with --permission-prompts none, so an unattended phase session can overwrite CLAUDE.md, REVIEW.md, sdlc.yaml or .claude/** with a one-line python/node file write via Bash, bypassing the guardrail-file protection the framework's own threat model (decision 6, CLAUDE.md 'Never edit .claude/**, CLAUDE.md, REVIEW.md or sdlc.yaml in a run') relies on entirely.

Until it is fixed the weakness stays in the code the project ships. The review is read-only; nothing has been changed.

## Proposed outcome
No instance of this authz weakness remains in the codebase: the case at `plugin/hooks/hooks.json:32` and every other place with the same pattern are fixed, each proven by a test, and an eval case for the class keeps it from returning (article p.48 step 7).

## Affected users and systems
- `plugin/hooks/hooks.json` and whatever calls it; the design pass finds the other places
- Users of luissiviero/sdlc-framework

## Constraints
- The security-baseline skill applies to the fix; no new dependency without a Risks line in plan.md.
- A test that reproduces the vulnerability is written first; no pre-existing test is edited to make the fix pass.
- Never quote a credential in the change, its tests or its evidence.

## Open questions
- Where else does the authz pattern occur, and does one fix cover every place?
- Is a shared guard (a helper, a middleware, a schema) better than local fixes?
- Which eval case captures the class so it does not return?

## Evidence
- Where: `plugin/hooks/hooks.json:32` (https://github.com/luissiviero/sdlc-framework/blob/8050b92d556e6b9dc90952c51200f0fb558bc664/plugin/hooks/hooks.json#L32)
- Class: authz; severity: Important; bounded: no
- Commit reviewed: `8050b92d556e6b9dc90952c51200f0fb558bc664`
- The review's words: "The guardrail self-protection (protected_paths.py) only hooks the Edit|Write|MultiEdit|NotebookEdit tool matcher; the Bash/PowerShell matcher runs plan_sync.py and production_gate.py but never checks a command's target path, and plugin/ci/settings.ci.json's permission allow-list grants bare 'Bash(python *)', 'Bash(python3 *)', 'Bash(node *)', 'Bash(npm *)' and 'Bash(npx *)' with --permission-prompts none, so an unattended phase session can overwrite CLAUDE.md, REVIEW.md, sdlc.yaml or .claude/** with a one-line python/node file write via Bash, bypassing the guardrail-file protection the framework's own threat model (decision 6, CLAUDE.md 'Never edit .claude/**, CLAUDE.md, REVIEW.md or sdlc.yaml in a run') relies on entirely." (rule: Rule 1 Authentication (authorization inferred from which tool route is used, not enforced uniformly))
- Finding signature: `c433d0293e7a89b4` (`evidence/scan-finding.json`); closing this pull request with a comment dismisses it, and it does not return (article p.47 step 4).
