---
type: Lesson
title: "security: authz: The runbook Go (cmd_go via _human_label_actor) accepts the"
description: "security: authz found that the runbook Go accepted the sdlc:go label from any person's account, so a collaborator with label rights could run a runbook the owner never authorized."
tags:
  - authz
  - owner-only-label
  - "security: authz"
change: "0006"
detected:
  at: "2026-10-26T13:13:55Z"
  metric: "security: authz"
  tier: 3
  rule: scan
fixed:
  pr: 405
generated:
  by: sdlc-plugin/1.0.46
  at: "2026-11-04T19:47:50Z"
status: stable
stale_after: "2027-11-04"
sources:
  - id: detection
    resource: evidence/scan-finding.json
  - id: eval
    resource: evals/cases/0006-security-authz-the-runbook-go-cmd-go-via/
  - id: fix-pr
    resource: https://github.com/luissiviero/sdlc-framework/pull/405
---

## What happened
The weekly security scan[^detection] flagged `plugin/detect/cli.py:1183`: the runbook Go
(`cmd_go` via `_human_label_actor`) accepted the `sdlc:go` label from any account that was
not a bot or the automation identity. A collaborator with only triage or label rights could
therefore make the runbook workflow run a running-system action (a rollback, a config change)
with the runbook secrets on an incident PR the owner never approved. Decision 14 makes the Go
the owner's per-incident act, and the comment trigger, the merge step and the review request
already required `is_owner_actor`.

## Root cause
The Go checked who a label was *not* from (a bot, the automation identity) instead of who it
*must* be from. "A person" was treated as "the owner", while every other owner act in the
framework went through the one owner rule of decision 34. The runbook workflow's coarse
`[bot]` check in its `if:` could not close the gap: it does not know `sdlc.yaml: owner` of
an organization repository, and the step that holds the secrets must decide for itself.

## Fix
`_human_label_actor` now refuses a label whose actor fails `state.unpark.is_owner_actor`,
with the default branch's `sdlc.yaml` as the config (`cmd_go` already passes the approved
copy, so a head branch cannot name its own owner). A refused label is left where it is and
the reason names the owner's account. No runbook ran for this incident; the fix shipped in
the build PR[^fix-pr].

## Prevention
`evals/cases/0006-security-authz-the-runbook-go-cmd-go-via/`[^eval] runs the reproducing
tests and asserts that the owner check stays in `plugin/detect/cli.py`.
`tests/test_detect_cli.py` adds `test_go_by_a_collaborator_performs_nothing` and
`test_go_reads_the_owner_from_the_default_branch` (one case where the head names the owner,
one where the default branch does). The next owner-only act should call `is_owner_actor`
from its first version and not list the accounts it refuses.

[^detection]: evidence/scan-finding.json
[^eval]: evals/cases/0006-security-authz-the-runbook-go-cmd-go-via/
[^fix-pr]: the build PR
