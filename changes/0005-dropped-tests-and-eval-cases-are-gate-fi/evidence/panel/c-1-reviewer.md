## Verdict
Escalate: send back to fix `dropped_eval_cases`'s unconditional union of `dot_dropped`.

## Why
Confirmed by tracing the code at `plugin/gate/checks.py:1393-1411`. With a case `foo`
holding `a.yaml` and `b.yaml`, where `a.yaml` is renamed to a dot-prefixed destination and
`b.yaml` is left untouched: `src_case="foo"` goes into both `touched` and `dot_dropped`;
`b.yaml` still exists at HEAD so `survivor_cases = {"foo"}`. The return line
`dropped = set(dot_dropped) | {... not in survivor_cases}` puts `"foo"` into `dropped`
through the first operand regardless of `survivor_cases` — the filter only guards the
second operand. `foo` is reported dropped although it has a visible survivor.

This is a Bugs-pass and Compliance-pass finding under REVIEW.md: it contradicts spec.md's
explicit invariant ("a case is dropped when no path remains ... so that one file dropped
out of a multi-file case while a sibling survives is never mistaken for the whole case's
drop") and plan.md's Risks section, which states the survivor-list mitigation is meant to
close exactly this gap "inside the files this plan already lists" — it does not, for the
dot-rename branch.

Checked test coverage directly: `test_ratchets_drop_eval_case_dot_rename_fails` uses a
single-file case (`bar/only.yaml`), and `test_ratchets_eval_case_partial_delete_is_not_a_drop`
uses a plain `D`, never a dot-rename. No test exercises the combination, so the suite is
green with the bug present — matching the adversarial reviewer's angle-6 claim.

REVIEW.md reserves "Important" for findings that "would break behavior" — this one does:
`ratchets` is a deterministic gate check (decision 11/21: a failed deterministic check
parks, never goes to the panel) that runs at every (c)/(d)/(e) gate in every project the
plugin drives, and it would falsely park a legitimate partial reorganization. This is not a
nit; it must be fixed before the check ships.
