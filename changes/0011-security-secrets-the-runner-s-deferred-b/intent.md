# Intent: security: secrets: The runner's deferred build/test/lint targets run code the
Author: security review (phase f). Change id: 0011. Entry route: incident scan:533685077d1fa81c.

## Problem
The weekly security review of the codebase at commit `4f7f59718e29` found an Important secrets finding in `plugin/ci/run_phase.py:2470`: The runner's deferred build/test/lint targets run code the session just wrote outside the sandbox, with no network allow-list, as the same user as the parent run_phase.py process whose own environment holds the App token (as GITHUB_TOKEN), the workflow token and the model credential; commands_env strips them only from the child's environment, so a session-written test can read them from /proc/<ancestor pid>/environ and exfiltrate them or push with the App identity.

Until it is fixed the weakness stays in the code the project ships. The review is read-only; nothing has been changed.

## Proposed outcome
No instance of this secrets weakness remains in the codebase: the case at `plugin/ci/run_phase.py:2470` and every other place with the same pattern are fixed, each proven by a test, and an eval case for the class keeps it from returning (article p.48 step 7).

## Affected users and systems
- `plugin/ci/run_phase.py` and whatever calls it; the design pass finds the other places
- Users of luissiviero/sdlc-framework

## Constraints
- The security-baseline skill applies to the fix; no new dependency without a Risks line in plan.md.
- A test that reproduces the vulnerability is written first; no pre-existing test is edited to make the fix pass.
- Never quote a credential in the change, its tests or its evidence.

## Open questions
- Where else does the secrets pattern occur, and does one fix cover every place?
- Is a shared guard (a helper, a middleware, a schema) better than local fixes?
- Which eval case captures the class so it does not return?

## Evidence
- Where: `plugin/ci/run_phase.py:2470` (https://github.com/luissiviero/sdlc-framework/blob/4f7f59718e29240225ab65a3f6d3ab6915e97057/plugin/ci/run_phase.py#L2470)
- Class: secrets; severity: Important; bounded: no
- Commit reviewed: `4f7f59718e29240225ab65a3f6d3ab6915e97057`
- The review's words: "The runner's deferred build/test/lint targets run code the session just wrote outside the sandbox, with no network allow-list, as the same user as the parent run_phase.py process whose own environment holds the App token (as GITHUB_TOKEN), the workflow token and the model credential; commands_env strips them only from the child's environment, so a session-written test can read them from /proc/<ancestor pid>/environ and exfiltrate them or push with the App identity." (rule: Rule 3 Secrets)
- Finding signature: `533685077d1fa81c` (`evidence/scan-finding.json`); closing this pull request with a comment dismisses it, and it does not return (article p.47 step 4).
