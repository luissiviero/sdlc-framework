## Verdict
Dismiss the finding as satisfied in substance (no pre-existing test was weakened), keeping it named in the PR summary for the owner.

## Why
- REVIEW.md lines 23-24: a fix "must not modify test files that existed before the fix; the failing test written first is the proof". The rule's purpose is to stop a fix from bending existing tests to pass; it also requires the proof test, whose natural place is the existing suite.
- The diff of `tests/test_detect_cli.py` (evidence/diff-deploy.patch, lines 17736-17842) removes no assertion and edits no pre-existing test body. It adds `test_go_by_a_collaborator_performs_nothing`, `test_go_reads_the_owner_from_the_default_branch` and its helper (the reproducing tests), and changes one fixture, `rollback_incident`, to take `monkeypatch` and set `GITHUB_REPOSITORY_OWNER=the-owner`.
- That fixture line is not a weakening: the existing Go tests already authorize as `the-owner`; the line makes that actor the repository owner, so R2's `is_owner_actor` (spec.md R2) treats it as the owner. Without it those tests would fail closed. Design panel decision 1 (evidence/decisions-design.md) settled this, and the line was committed before the test-file lock.
- The one later assertion change concerns a new test, not a pre-existing one. It was made after the owner's `sdlc:unlock-tests` (status.yaml `tests_unlocked_by: luissiviero`; fix-response.md round 2). The new assertion is stricter: the dispatch record must still say `go-requested`.
- The finding comes from `framework_findings`, which flags any pre-existing path under `test_paths` that appears in the diff, whatever changed in it. That is the letter of the rule, not evidence of a weakened test.
- Safest reading: the owner's unlock label and the design decision are the human acts that cover the deviation. Dismiss with that reason recorded rather than reverting, because reverting would remove the fix's required proof.
