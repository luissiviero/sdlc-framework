# Progress — R63 accepted: the CLI a new project installs knows the models its sdlc.yaml names (choice 244, 2026-10-20)

This session ran on branch `ccr-a6fc1017-mkylxv`. The owner's task was to check the previous session's claims on the sample's change 0017 and on #284, take over #284 and the reading of 0017 for R7, and put the template CLI default of NOTES §54 to the owner. The previous record (R24 as plugin 1.0.15, PR #286, which ran in parallel) is now `docs/progress/2026-10-20-r24-risk-hit-banner-1.0.15.md`, unchanged; the one before it (decisions 35 and 36, choices 242 and 243) is `docs/progress/2026-10-20-decisions-35-36-and-choices-242-243.md`. The session's own file is `docs/handoffs/sessions/2026-10-20-ccr-a6fc1017-mkylxv.md`.

No change under `plugin/` or `template/` in this PR; no version bump.

## Summary
- **Choice 244**: R63 is accepted as recommended. Its proposal is `docs/proposals/template-cli-default.md`; its row is in `docs/ROADMAP.md`.
- **The root pin**: the owner raised `sdlc.yaml`'s `claude_code` from 2.1.278 to 2.1.304 (PR #287, merged as `fe315da`) and its comment to match (PR #288, merged as `6b8d0e8`).
- **NOTES §55**: R7's reading of the sample's change 0017, phases (c) to (e), and the first row of the external review's retirement tally (count 1).

## The owner's decisions (2026-10-20)
244. **R63 is accepted as recommended** (the owner, "accept R63 as recommended"):
    - a candidate of its own, not a part of R61;
    - `/sdlc-init`'s default CLI and the pin script's fallback move from 2.1.278 to 2.1.304, the template's comment follows, the tests follow; whether the runner names an `unrecognized_model` line as a park reason of its own is decided at the build;
    - built before R24 (rank 8), once change 0017's build run shows the session on `claude-opus-5-5` under 2.1.304; no rank moves *[2026-10-20: R24 merged first, as 1.0.15 (PR #286), in a session that ran in parallel; R63 is the next build]*;
    - a plugin change, so it takes the next free patch version *[2026-10-20: 1.0.16, since R24 took 1.0.15]*.

## Proposed edits for the owner
None: the `sdlc.yaml` line 107 comment this record first proposed is the owner's PR #288.

## Left
- **R63's build**: its reading is in (NOTES §55, the sessions of (c) to (e) on `claude-opus-5-5` under 2.1.304); it is the next build, as 1.0.16.
- **The panel's "Total panel cost: $0.00"** (NOTES §55): a display defect, not fixed; the session's recommendation is to fold the one-line fix into R63's build, the owner's call.
- Every other open item is in the session file of `ccr-a6fc1017-mkylxv`.

## Checks (this repository)
On the final head, after `python -m pip install -e ".[dev]"`, chained with `set -o pipefail`: the four commands of `HANDOFF.md`'s standing precondition 1, plus `python tasks.py docs-lint`. Their output is in the PR.
