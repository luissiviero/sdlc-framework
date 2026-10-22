# Progress — decision 37, one profile and one review mode, as plugin 1.0.21 (2026-10-22)

This session ran on branch `ccr-0522ec37-iia2ok-modes-code`. The owner's task (2026-10-20): build the code that decision 37 asks for (its point 4) as a plugin version of its own, after R22's build and after decision 38's. It was built while #307 (decision 38) waited, and its PR was opened once #307 merged, from `main` at `0a0554d`. It takes no decision, choice or note number.

## Coordination with the other sessions
- **The version.** #304 (R8) merged as 1.0.19 and #307 (decision 38) as 1.0.20, so this PR is **1.0.21** (choice 184). Every "1.0.20" the branch had written for decision 37 now says 1.0.21, and every "until 1.0.19" says "until 1.0.20". R8's "plugin 1.0.19" is R8's and stays.
- **Overlap with #304 and #307.** One conflict, in `docs/OPERATING_MODEL.md` §4.2's rules paragraph, merged sentence by sentence: this PR's sentences on the label events, the concurrency group and the abandon group, R8's two sentences on `GEMINI_API_KEY`, and decision 38's "Credential" sentence. R8's `second-opinion` job in `sdlc-deploy.yml` read `inputs.head_ref || github.event.pull_request.head.ref`. Since the deploy workflow now starts only from a dispatch, the job reads `inputs.head_ref` alone, in both copies.
- **The records.** Decision 38's record (1.0.20) moved unchanged to `docs/progress/2026-10-20-decision-38-auth-order-1.0.20.md`, with its index line.

## Summary
- **One profile** (decision 37, point 1). `plugin/state/conventions.py` has one set of human gates, `HUMAN_GATES = {a, b, e, f}`, and `is_human_gate(phase)`. `PROFILES`, the `full` profile, and the `sdlc:c-approved` and `sdlc:d-approved` labels are gone. Gates (c) and (d) are the confidence gate's in every project. The fast lane (decision 30) applies to every project.
- **One review mode** (point 2). A judgment item of decision 21's fixed list always goes to the review panel. The `parked` mode, the panel's `mode` subcommand and its exit code 4 are gone.
- **No per-change override** (point 3). `status.yaml: profile_override` and `review_override` are gone, and so are the gate's, the guard's and the panel's reads of the base branch's overrides.
- **The workflows.** `sdlc-test.yml` and `sdlc-deploy.yml`, in `template/` and the root copies, start only from the previous phase's `workflow_dispatch`. The label trigger and `run_phase.py label_applied_by_a_human` are gone. The fix workflow's comment no longer names the two labels.
- **The documents.** Rewritten:
  - `docs/OPERATING_MODEL.md` §3, §4, §4.2 and §9;
  - `README.md`, with an upgrade note: replace `sdlc-test.yml` and `sdlc-deploy.yml`;
  - `template/sdlc.yaml`, where one comment block replaces the two keys;
  - `changes/README.md` and its template copy;
  - the phase commands and `/sdlc-init`.

  `docs/BUILD_GUIDE.md` is annotated beside the sentence (choice 126).
- **Tests.** The tests of the removed features were deleted: the Full label gate and its actor, owner and fail-closed variants, `checkout_profile`, the approved overrides in the gate, guard and panel, `panel mode`, exit 4, the Full merge wait and the parked ledger check. Where a deleted test also covered something that stays, it was rewritten against what stays: label-event paging, automation-actor detection, early approval at (e), and the guard's refusal of an unreadable approved copy.

## The design calls decision 37 left to the build
| Call | How it was taken |
|---|---|
| A `sdlc.yaml` that still says `profile: full` or `review: parked` | Read as the one behaviour and named once in the gate's note (`conventions.retired_settings_note`): the key "is no longer read (decision 37) … the owner removes the key". Never refused. `standard`, `lite` and `deferred` stay silent, as `lite` did since 0.2.14. |
| A `status.yaml` that carries `profile_override` or `review_override` | Dropped on load (`status.RETIRED_KEYS`), because `Status.from_dict` refuses unknown keys and an older file must keep loading. Silent (review finding 3e, left: the only override either repository sets is one `review_override: deferred`, which asks for what now always happens). |
| A `sdlc.yaml` with no `review:` key | Runs deferred like every other. Decision 32's build (1.0.8) had kept it `parked` (`DEFAULT_REVIEW_MODE`) so that such a project would not switch silently; with one mode there is nothing to switch to. Said in `docs/OPERATING_MODEL.md` §9. |
| `/sdlc-init --profile` and `--review` | Still parsed, hidden and ignored, so an older command line does not fail. Neither key is written. |
| The fail-closed reads of the base branch's `status.yaml` | The runner's guard still refuses an unreadable approved copy (`_approved_status`, "nothing runs until it is fixed"), and so do the session start and `fast_lane_refusal`. The gate and the panel, run by hand, no longer read that copy, so they no longer refuse on it (finding 2a, left). |

## The independent review
A general-purpose agent in a fresh context reviewed the diff against `origin/main` at the time (`18b2a22` with #308 merged), from decision 37. It found the build matching decision 37 and nothing blocking. Its checks: 2279 passed, lint and docs-lint clean, every workflow parsing, and `/sdlc-init --profile full --review parked` writing neither key.

| # | Finding | Outcome |
|---|---|---|
| 1a | `_approved_ref`'s docstring names the removed `approved_overrides` (nit) | fixed |
| 1b | `fast_lane_refusal` keeps two unused parameters (nit) | fixed |
| 2a | The gate and the panel, run by hand, no longer fail closed on an unreadable base `status.yaml` (nit) | left: nothing they run reads that copy any more, and the runner still refuses it |
| 2b | An owner approval given before `gate-e.json` existed now merges (nit) | no change: decision 36, point 4; `only_evidence_since` still guards the code |
| 3a | `changes/README.md` and its template copy still list `sdlc:<phase>-approved` (should-fix) | fixed |
| 3b | `all_labels()` still creates `sdlc:c-ready` and `sdlc:d-ready`, which no gate applies now (nit) | left: a label nobody applies costs nothing, and a project that already has them keeps them |
| 3c | A blank line missing in `template/sdlc.yaml` (nit) | fixed |
| 3d | An older `sdlc-test.yml` or `sdlc-deploy.yml` still starts a run on the withdrawn labels; no upgrade note (nit) | fixed: README's upgrade paragraph, and below |
| 3e | A leftover override in `status.yaml` is dropped silently (nit) | left, as in the design calls |
| 4 | One dry-run assertion at a human gate narrowed (nit) | no change: `wait` is still tested at (b) |
| 5a | `docs/OPERATING_MODEL.md` §4.2's rules paragraph still described label-fired test and deploy runs (should-fix) | fixed |
| 5b | `docs/BUILD_GUIDE.md` lines 215 and 761 not annotated (nit) | annotated |
| 6 | The version and this record still to write (should-fix) | done here |
| — | A `sdlc.yaml` without `review:` switches to deferred silently, undocumented (nit) | documented in §9 |

## The port list
This PR touches `plugin/ci/run_phase.py` (the Full label gate, `label_applied_by_a_human`, `checkout_profile`, the approved overrides, `_approved_status`, `fast_lane_refusal`, `_start_point`), `plugin/detect/cli.py` (`write_park_result` no longer passes a profile) and the fix workflow template (its comment). It goes on the port list until the 1.0.0 read.

## Proposed edits for the owner
Each `sdlc.yaml` edit goes in the same pull request that moves that repository's pin to 1.0.21 or later, not before: a plugin older than 1.0.21 still reads a missing `review:` as `parked`. The keys are harmless until then; 1.0.21 says nothing about `standard` or `deferred`.

| Link | Row | What is there now | What it must become |
|---|---|---|---|
| [sdlc.yaml](https://github.com/luissiviero/sdlc-framework/blob/main/sdlc.yaml#L5) | 5-9 | the `# --- profile: which gates are human …` comment block, five lines, ending `# that still says lite reads as standard)` | the 17-line block `# --- the gates and judgment calls …` of `template/sdlc.yaml` (lines 5-21) at 1.0.21 |
| [sdlc.yaml](https://github.com/luissiviero/sdlc-framework/blob/main/sdlc.yaml#L10) | 10-11 | `profile: standard` / `review: deferred` | deleted |
| [sample sdlc.yaml](https://github.com/luissiviero/sdlc-sample-python/blob/main/sdlc.yaml#L5) | 5-11 | the `# --- profile: which gates are human …` comment block and `profile: standard` | the same 17-line block of `template/sdlc.yaml` |
| [sample sdlc.yaml](https://github.com/luissiviero/sdlc-sample-python/blob/main/sdlc.yaml#L110) | 110-124 | the `# --- review mode inside a phase …` comment block and `review: deferred` | deleted, with the blank line after it |
| [sample sdlc.yaml](https://github.com/luissiviero/sdlc-sample-python/blob/main/sdlc.yaml#L78) | 78 | `  version: 1.0.19` | `  version: 1.0.21`, at the sample's next upgrade, in the same PR as the rows above and with its `sdlc-test.yml` and `sdlc-deploy.yml` replaced by the 1.0.21 copies |
| [CLAUDE.md](https://github.com/luissiviero/sdlc-framework/blob/main/CLAUDE.md#L3) | 3 | `` … deploy → maintain with profile-based human gates. … `` | `` … deploy → maintain with human gates at (a), (b) and (e). … `` (the rest of the line unchanged) |

The root pin (line 104, `version: 1.0.17`) stays where it is: choice 249, point 2, holds it until this repository has its own App. So the root's two `sdlc.yaml` rows wait for that move.

The owner may want to know one effect: a project that pinned `full` now gets no wait after (c) and (d); its look comes at (e), with the close-look banner, and on a declared production the release label stays (decision 37, "What it gives up").

## Left
- Every other open item is in the session files.

## Checks (this repository)
On the final head, chained with `set -o pipefail`, on a full-history clone:
- `python -m compileall -q plugin tests tasks.py .github/scripts`
- `python -m ruff check .`
- `python -m ruff format --check .`
- `python tasks.py docs-lint`
- `python -m pytest -n auto --dist worksteal`
- `claude plugin validate .`

Their output is in the PR.
