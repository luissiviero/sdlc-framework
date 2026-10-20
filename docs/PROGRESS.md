# Progress — R63 accepted: the CLI a new project installs knows the models its sdlc.yaml names (choice 244, 2026-10-20)

This session ran on branch `ccr-a6fc1017-mkylxv`. The owner's task was to check the previous session's claims on the sample's change 0017 and on #284, take over #284 and the reading of 0017 for R7, and put the template CLI default of NOTES §54 to the owner. The previous record (decisions 35 and 36, choices 242 and 243) is now `docs/progress/2026-10-20-decisions-35-36-and-choices-242-243.md`, unchanged. The session's own file is `docs/handoffs/sessions/2026-10-20-ccr-a6fc1017-mkylxv.md`.

No change under `plugin/` or `template/` in this PR; no version bump.

## Summary
- **Choice 244**: R63 is accepted as recommended. Its proposal is `docs/proposals/template-cli-default.md`; its row is in `docs/ROADMAP.md`.
- **The root pin**: the owner raised `sdlc.yaml`'s `claude_code` from 2.1.278 to 2.1.304 (PR #287, merged as `fe315da`).

## The owner's decisions (2026-10-20)
244. **R63 is accepted as recommended** (the owner, "accept R63 as recommended"):
    - a candidate of its own, not a part of R61;
    - `/sdlc-init`'s default CLI and the pin script's fallback move from 2.1.278 to 2.1.304, the template's comment follows, the tests follow; whether the runner names an `unrecognized_model` line as a park reason of its own is decided at the build;
    - built before R24 (rank 8), once change 0017's build run shows the session on `claude-opus-5-5` under 2.1.304; no rank moves;
    - a plugin change, so it takes the next free patch version.

## Proposed edits for the owner
| Link | Row | What is there now | What it must become |
|---|---|---|---|
| [sdlc.yaml](https://github.com/luissiviero/sdlc-framework/blob/main/sdlc.yaml#L107) | 107 | `  # 2.1.278 is the CLI the jobs install and the framework's minimum.` | `  # 2.1.304 is the CLI the jobs install and the framework's minimum (NOTES §54).` |

The pin on line 108 already reads `"2.1.304"` (PR #287); this row makes its comment agree. It can wait for R63's build, which changes the same sentence in `template/sdlc.yaml`.

## Left
- **R63's build**: after 0017's build run is read (this session's next step).
- Every other open item is in the session file of `ccr-a6fc1017-mkylxv`.

## Checks (this repository)
On the final head, after `python -m pip install -e ".[dev]"`, chained with `set -o pipefail`: the four commands of `HANDOFF.md`'s standing precondition 1, plus `python tasks.py docs-lint`. Their output is in the PR.
