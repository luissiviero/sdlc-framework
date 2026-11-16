# Intent: security: secrets: block_text and label_block_text quote the raw command (up to
Author: security review (phase f). Change id: 0007. Entry route: incident scan:d8d2c7a79b3a16d8.

## Problem
The weekly security review of the codebase at commit `4f7f59718e29` found an Important secrets finding in `plugin/hooks/production_gate.py:351`: block_text and label_block_text quote the raw command (up to 100 characters) in the block reason, and log_decision redacts only the command field, not the reason, so a credential typed inline in a blocked production command (an environment assignment of a token before a deploy command) is written verbatim to the committed evidence/hook-log.jsonl.

Until it is fixed the weakness stays in the code the project ships. The review is read-only; nothing has been changed.

## Proposed outcome
The finding is bounded (one file, one patch): `plugin/hooks/production_gate.py:351` no longer has the secrets weakness, proven by a new test that reproduces it before the fix and passes after it. The review suggests this patch, stored as `evidence/suggested-patch.diff` for the build run to apply and check:

```diff
--- a/plugin/hooks/production_gate.py
+++ b/plugin/hooks/production_gate.py
@@ -350,4 +350,4 @@
 def block_text(command: str, action: str, detail: str, pr_number: int | None) -> str:
-    shown = " ".join(command.split())
+    shown = " ".join(redact(command).split())  # the reason is committed in the hook log
     if len(shown) > COMMAND_SHOWN:
         shown = shown[:COMMAND_SHOWN] + "..."
@@ -365,4 +365,4 @@
 def label_block_text(command: str) -> str:
-    shown = " ".join(command.split())
+    shown = " ".join(redact(command).split())  # the reason is committed in the hook log
     if len(shown) > COMMAND_SHOWN:
         shown = shown[:COMMAND_SHOWN] + "..."
```

## Affected users and systems
- `plugin/hooks/production_gate.py` and whatever calls it
- Users of luissiviero/sdlc-framework

## Constraints
- The security-baseline skill applies to the fix; no new dependency without a Risks line in plan.md.
- A test that reproduces the vulnerability is written first; no pre-existing test is edited to make the fix pass.
- Never quote a credential in the change, its tests or its evidence.

## Open questions
none

## Evidence
- Where: `plugin/hooks/production_gate.py:351` (https://github.com/luissiviero/sdlc-framework/blob/4f7f59718e29240225ab65a3f6d3ab6915e97057/plugin/hooks/production_gate.py#L351)
- Class: secrets; severity: Important; bounded: yes
- Commit reviewed: `4f7f59718e29240225ab65a3f6d3ab6915e97057`
- The review's words: "block_text and label_block_text quote the raw command (up to 100 characters) in the block reason, and log_decision redacts only the command field, not the reason, so a credential typed inline in a blocked production command (an environment assignment of a token before a deploy command) is written verbatim to the committed evidence/hook-log.jsonl." (rule: Rule 3 Secrets)
- Finding signature: `d8d2c7a79b3a16d8` (`evidence/scan-finding.json`); closing this pull request with a comment dismisses it, and it does not return (article p.47 step 4).
