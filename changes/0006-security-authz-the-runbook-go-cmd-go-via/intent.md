# Intent: security: authz: The runbook Go (cmd_go via _human_label_actor) accepts the
Author: security review (phase f). Change id: 0006. Entry route: incident scan:a9b4ac78d2494f59.

## Problem
The weekly security review of the codebase at commit `80d7de5cebd4` found an Important authz finding in `plugin/detect/cli.py:1183`: The runbook Go (cmd_go via _human_label_actor) accepts the sdlc:go label from any account that is not a bot or the automation identity, so a collaborator with only triage/label rights can make the runbook workflow run a running-system action (rollback, config change) with the runbook secrets on an incident PR the owner never approved, although decision 14 makes Go the owner's per-incident act and the comment trigger, merge step and review request all require is_owner_actor.

Until it is fixed the weakness stays in the code the project ships. The review is read-only; nothing has been changed.

## Proposed outcome
The finding is bounded (one file, one patch): `plugin/detect/cli.py:1183` no longer has the authz weakness, proven by a new test that reproduces it before the fix and passes after it. The review suggests this patch, stored as `evidence/suggested-patch.diff` for the build run to apply and check:

```diff
--- a/plugin/detect/cli.py
+++ b/plugin/detect/cli.py
@@ -1181,12 +1181,17 @@
 
 # --- go: the owner's per-incident authorization (decision 14) ----------------------------------
 def _human_label_actor(repo: str, number: int, label: str, config: dict[str, Any]):
+    from state.unpark import is_owner_actor  # noqa: PLC0415
+
     found = _github().label_actor(repo, number, label)
     if not found.get("ok"):
         return None, f"could not read the label events: {found.get('reason') or 'failed'}"
     actor = found.get("actor")
     if not actor:
         return None, f"no `labeled` event for {label} on #{number}"
     if BOT_RE.search(actor) or is_automation(actor, "", automation_identity(config)):
         return None, f"{label} was applied by {actor}, not by a person: left where it is"
+    if not is_owner_actor(actor, config, None, repo):
+        # decision 14: the Go is the owner's act; config is the default branch's copy
+        return None, f"{label} was applied by {actor}, not by the owner's account (decision 34)"
     return actor, ""
```

## Affected users and systems
- `plugin/detect/cli.py` and whatever calls it
- Users of luissiviero/sdlc-framework

## Constraints
- The security-baseline skill applies to the fix; no new dependency without a Risks line in plan.md.
- A test that reproduces the vulnerability is written first; no pre-existing test is edited to make the fix pass.
- Never quote a credential in the change, its tests or its evidence.

## Open questions
none

## Evidence
- Where: `plugin/detect/cli.py:1183` (https://github.com/luissiviero/sdlc-framework/blob/80d7de5cebd482d8e1f4885b85dafb2b8dc3bf25/plugin/detect/cli.py#L1183)
- Class: authz; severity: Important; bounded: yes
- Commit reviewed: `80d7de5cebd482d8e1f4885b85dafb2b8dc3bf25`
- The review's words: "The runbook Go (cmd_go via _human_label_actor) accepts the sdlc:go label from any account that is not a bot or the automation identity, so a collaborator with only triage/label rights can make the runbook workflow run a running-system action (rollback, config change) with the runbook secrets on an incident PR the owner never approved, although decision 14 makes Go the owner's per-incident act and the comment trigger, merge step and review request all require is_owner_actor." (rule: Rule 1 Authentication (authorization checked on the server))
- Finding signature: `a9b4ac78d2494f59` (`evidence/scan-finding.json`); closing this pull request with a comment dismisses it, and it does not return (article p.47 step 4).
