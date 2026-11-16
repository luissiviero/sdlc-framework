# Intent: security: authz: The release approval accepts the sdlc:release-approved label
Author: security review (phase f). Change id: 0008. Entry route: incident scan:00956e0af2c72b91.

## Problem
The weekly security review of the codebase at commit `4f7f59718e29` found an Important authz finding in `plugin/release/approval.py:296`: The release approval accepts the sdlc:release-approved label from any non-bot account (label_approval checks only is_automation_actor, never is_owner_actor), so a collaborator with only Triage access can label a merged build PR and make sdlc-release.yml run deploy.command to production, or make the production-gate hook allow a guarded command, without the owner's act that decision 34 and OPERATING_MODEL section 1 (one person holds the release manager role) require.

Until it is fixed the weakness stays in the code the project ships. The review is read-only; nothing has been changed.

## Proposed outcome
The finding is bounded (one file, one patch): `plugin/release/approval.py:296` no longer has the authz weakness, proven by a new test that reproduces it before the fix and passes after it. The review suggests this patch, stored as `evidence/suggested-patch.diff` for the build run to apply and check:

```diff
--- a/plugin/release/approval.py
+++ b/plugin/release/approval.py
@@ -293,4 +293,14 @@
             f"{actor}, which never passes a human gate",
             pr_number,
         )
+    from state.unpark import is_owner_actor  # noqa: PLC0415
+
+    if not is_owner_actor(str(actor), dict(config), None, repo):
+        return Approval(
+            False,
+            "none",
+            f"label {RELEASE_LABEL} on #{pr_number} was applied by {actor}, not by the "
+            "owner's account (decision 34)",
+            pr_number,
+        )
     return Approval(True, "label", f"label applied by {actor}", pr_number)
```

## Affected users and systems
- `plugin/release/approval.py` and whatever calls it
- Users of luissiviero/sdlc-framework

## Constraints
- The security-baseline skill applies to the fix; no new dependency without a Risks line in plan.md.
- A test that reproduces the vulnerability is written first; no pre-existing test is edited to make the fix pass.
- Never quote a credential in the change, its tests or its evidence.

## Open questions
none

## Evidence
- Where: `plugin/release/approval.py:296` (https://github.com/luissiviero/sdlc-framework/blob/4f7f59718e29240225ab65a3f6d3ab6915e97057/plugin/release/approval.py#L296)
- Class: authz; severity: Important; bounded: yes
- Commit reviewed: `4f7f59718e29240225ab65a3f6d3ab6915e97057`
- The review's words: "The release approval accepts the sdlc:release-approved label from any non-bot account (label_approval checks only is_automation_actor, never is_owner_actor), so a collaborator with only Triage access can label a merged build PR and make sdlc-release.yml run deploy.command to production, or make the production-gate hook allow a guarded command, without the owner's act that decision 34 and OPERATING_MODEL section 1 (one person holds the release manager role) require." (rule: Rule 1 Authentication (authorization checked on the server for every object))
- Finding signature: `00956e0af2c72b91` (`evidence/scan-finding.json`); closing this pull request with a comment dismisses it, and it does not return (article p.47 step 4).
