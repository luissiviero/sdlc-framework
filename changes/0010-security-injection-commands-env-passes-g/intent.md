# Intent: security: injection: commands_env passes GITHUB_ENV, GITHUB_PATH and
Author: security review (phase f). Change id: 0010. Entry route: incident scan:9d29c682b6efa91c.

## Problem
The weekly security review of the codebase at commit `4f7f59718e29` found an Important injection finding in `plugin/ci/run_phase.py:2485`: commands_env passes GITHUB_ENV, GITHUB_PATH and GITHUB_OUTPUT through to the unsandboxed targets, so a session-written test can append PYTHONPATH or a PATH entry pointing into the checkout and get its own code run by the job's later steps (Verify the project checkout, Park, Publish the explanation), which hold the App token.

Until it is fixed the weakness stays in the code the project ships. The review is read-only; nothing has been changed.

## Proposed outcome
The finding is bounded (one file, one patch): `plugin/ci/run_phase.py:2485` no longer has the injection weakness, proven by a new test that reproduces it before the fix and passes after it. The review suggests this patch, stored as `evidence/suggested-patch.diff` for the build run to apply and check:

```diff
--- a/plugin/ci/run_phase.py
+++ b/plugin/ci/run_phase.py
@@ -2478,8 +2478,13 @@ def commands_env() -> dict[str, str]:
     hidden = {
         *auth_mod.CREDENTIAL_VARS,
         *SESSION_HIDDEN_VARS,
         "GITHUB_TOKEN",
         "GH_TOKEN",
         app_token.WORKFLOW_TOKEN_ENV,
+        # the runner's command files: a target that appends to them steers the job's later
+        # steps, which hold the App token (a PYTHONPATH or PATH entry into the checkout)
+        "GITHUB_ENV",
+        "GITHUB_PATH",
+        "GITHUB_OUTPUT",
     }
     return app_token.strip_git_auth({k: v for k, v in os.environ.items() if k not in hidden})
 
```

## Affected users and systems
- `plugin/ci/run_phase.py` and whatever calls it
- Users of luissiviero/sdlc-framework

## Constraints
- The security-baseline skill applies to the fix; no new dependency without a Risks line in plan.md.
- A test that reproduces the vulnerability is written first; no pre-existing test is edited to make the fix pass.
- Never quote a credential in the change, its tests or its evidence.

## Open questions
none

## Evidence
- Where: `plugin/ci/run_phase.py:2485` (https://github.com/luissiviero/sdlc-framework/blob/4f7f59718e29240225ab65a3f6d3ab6915e97057/plugin/ci/run_phase.py#L2485)
- Class: injection; severity: Important; bounded: yes
- Commit reviewed: `4f7f59718e29240225ab65a3f6d3ab6915e97057`
- The review's words: "commands_env passes GITHUB_ENV, GITHUB_PATH and GITHUB_OUTPUT through to the unsandboxed targets, so a session-written test can append PYTHONPATH or a PATH entry pointing into the checkout and get its own code run by the job's later steps (Verify the project checkout, Park, Publish the explanation), which hold the App token." (rule: Rule 3 Secrets)
- Finding signature: `9d29c682b6efa91c` (`evidence/scan-finding.json`); closing this pull request with a comment dismisses it, and it does not return (article p.47 step 4).
