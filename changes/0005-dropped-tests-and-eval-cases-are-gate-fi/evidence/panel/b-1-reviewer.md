## Verdict
Accept the assumption as correct: `framework/` is properly out of scope; no fix needed to spec.md or plan.md.

## Why
- `spec-template/SKILL.md`: "Concerns fail closed... every list item... is an open concern
  unless it starts with `[x]`, `closed`, `resolved` or `decided`... the design pass opens
  them and may close only the ones the policy text itself settles." The five other concerns
  cite intent.md text that settles them and are `[x]`'d; this one says intent.md is "silent"
  on `framework/`, so it correctly stays open as a genuine assumption for this gate (decision
  21, deferred review) rather than being closed by the design pass itself.
- The assumption itself is sound. intent.md's Constraints: "No runner code. Nothing in
  `plugin/ci/run_phase.py` or the workflow templates changes" and its Proposed outcome's file
  list (lines 77-80) names only root-level `plugin/`, `template/`, `docs/` paths — `framework/`
  is absent from both.
- Decision 8 (Framework distribution, sticky): the plugin is pinned per project by version;
  `framework/` is this repo's own pinned checkout of itself (dogfooding), and OPERATING_MODEL
  §6/§8 describe CI loading enforcement from that pinned checkout, never the PR branch, as
  deliberate self-protection — a session's own diff must not immediately strengthen the gate
  judging it. Propagation is the existing pin/release process, not an in-diff edit.
- plan.md's "Options not taken" already considered and rejected editing `framework/` directly,
  for the same reason; `plan.md`'s "Not touched" list names it explicitly, so plan and spec
  agree.
- Per REVIEW.md, "Important" is reserved for findings that break behavior, leak data or
  breach policy; this is none of those — it is a correctly scoped, correctly flagged
  boundary, not a defect.
