# Session of 2026-11-03 on branch `claude/keen-mendel-3zipla`: the gap of 27 and 28 October, and the test isolation that parked #403

**Builds on:**
- `docs/handoffs/sessions/2026-10-26-ccr-ca9f0149-a29zgl-end.md`, the newest file on `main`, and the files it names (carried by reference, not re-verified, but for the rows below).
- No session file was written after it. Every session file not named in its header is older than the files it names. The branch `ccr-6ed8a82e-cxmftx` holds three commits ahead of `main` that edit `2026-10-22-ccr-6ed8a82e-cxmftx-end.md`, last committed on 2026-10-22; they were never merged, and they carry no item the later files lack (read by this session, `git log origin/main..origin/ccr-6ed8a82e-cxmftx`).

## Where the project stands
- **Framework `main` is at `51cea68`** (#398), read at 18:52 UTC on 2026-11-03, on plugin **1.0.50**, tagged `v1.0.50`. This repository's pin is still **1.0.46** (`sdlc.yaml:143`).
- **The sample** (`luissiviero/sdlc-sample-python`) is at `3fc88fa`, pinned at **1.0.47**, with no open pull request (read at 18:52 UTC on 2026-11-03).
- **The trial repository is `luissiviero/crypto-backtester`**, pinned at **1.0.50** (its `sdlc.yaml`), `main` at `cc9ff5a`, read at 18:52 UTC on 2026-11-03.

## What happened on 27 and 28 October, which no session file recorded
| Repository | PR | What | State, read at 18:52 UTC on 2026-11-03 |
|---|---|---|---|
| framework | #398 | Change 0006's incident intent, filed by the weekly security review on 2026-10-26 (its `status.yaml`: `created_at` 13:13:55 UTC): the runbook Go accepts `sdlc:go` from any account that is not a bot, not only the owner's (`plugin/detect/cli.py:1183`, decision 14) | merged by the owner (`51cea68`) |
| framework | #403 | Change 0006's design run | parked: `commands: not green: test (exit 1)`; see "This PR" below |
| trial | #1 | `/sdlc-init`, from a Claude session on `claude/practical-darwin-lwb53d` | merged |
| trial | #3 | The owner's edit: `polars` added to `commands.setup` | merged |
| trial | #4, #5 | Change 0001's intent (closed, superseded by the fast lane, decision 30) and design | #5 merged (`cc9ff5a`) |
| trial | #6 | Change 0001's build, test and deploy | parked at the deploy gate: two Important findings (signatures `192f90d781e7ed81`, `266ff10a5f51b0f4`): the project CI does not install polars, and the trial's `CLAUDE.md` is outdated. Both are files the run cannot edit |

**Why no file recorded them.** Three causes, read from the files and the branches:
1. The end file was committed at 00:17 UTC on 2026-10-27, eleven hours after #398 was opened, and says "No lane runs" without naming #398: an open pull request was missed.
2. The trial was set up by a session that worked only in `luissiviero/crypto-backtester`. `HANDOFF.md` binds the sessions of this repository, so nothing asked that session for a file here.
3. Everything after was the runner's, which writes no session file by design.

The second cause is a rule that is missing, a proposal for the owner below.

## This PR
- **The cause of #403's park.** The phase workflows export `HEAD_REF`, the run's head branch, to the runner's steps (`.github/workflows/sdlc-design.yml`, the `env:` of the phase step). The suite then ran as the project's test target in that environment. `tests/test_fix_round_gaps.py:306` and `tests/test_auto_round.py:343` build a test's environment from `os.environ`, so a fix round's cancelled-run check (`run_phase.cancel_state_refusal`, `plugin/ci/run_phase.py:3024`) compared the fixture's branch with the job's own and refused the saved state. The ten tests of `tests/test_cancelled_park.py` failed only in that environment; `Framework checks` sets no `HEAD_REF`, which is why #401's checks were green.
- **The fix.** `HEAD_REF` joins `RUNNER_NAMES` in `tests/conftest.py`, so the autouse fixture removes it before every test, as it already does for the runner's other variables. No assertion changes. The change is in `tests/` only, so there is no version bump (choice 270).
- **Verified.** Before the fix, `HEAD_REF=sdlc/0006/design python -m pytest tests/test_cancelled_park.py` failed the same ten tests as #403's run. After it, the 22 tests of that file pass with and without `HEAD_REF`, and the whole suite passes with `HEAD_REF=sdlc/0006/design` (exit 0). The output is in this session's record.

## Preconditions of the moment
- The repositories in scope: `luissiviero/sdlc-framework`, `luissiviero/sdlc-sample-python`, `luissiviero/crypto-backtester`.
- `main` at `51cea68` until this PR, tags up to `v1.0.50`, this repository's pin 1.0.46, the sample's 1.0.47, the trial's 1.0.50.

## Next steps, in order
1. **This PR**: the owner merges it when `Framework checks` is green.
2. **#403 needs `main` merged in before the `@claude` comment.** A fix round merges the default branch only for the review pass, the deploy run and a round whose gate phase is deploy (`plugin/ci/run_phase.py:3718`), never at design. So the owner first runs `gh pr update-branch 403 --repo luissiviero/sdlc-framework` (or uses the "Update branch" button). That push starts no run: `sdlc-design.yml` runs on `opened`, `reopened` and `closed` only. Then the owner comments `@claude` on #403, so the round's gate runs the suite with this PR's fix.
3. **The trial's #6.** The owner's PR on the trial's `main` comes first: `polars==2.1.0` in `.github/workflows/ci.yml`'s install step and the `CLAUDE.md` lines, given to the owner in this session's record. Then an `@claude` comment on #6. That round is at deploy, so the runner merges the trial's `main` in itself (`run_phase.py:3718`).
4. The ROADMAP candidates, in its Order column, once the trial's first change is released.

## Every open item
| Item | Where | What is left | Who acts | Blocks 1.0.0 |
|---|---|---|---|---|
| This PR | framework | Green checks, the owner's merge | owner | no |
| Change 0006 (#403) | framework | The update-branch, then `@claude` (Next steps 2); then the build of the fix the intent proposes | owner; the runner | no |
| Change 0001 (trial #6) | trial | The owner's `CLAUDE.md` and CI edit, then `@claude` (Next steps 3). The two nits (`app/data/http.py:78`, the redirect handler; `app/data/params.py:78`, a `datetime` passed to `parse_date`) are the owner's call | owner; the runner | no |
| A session file for work done elsewhere | `HANDOFF.md` | A rule that a session working in the sample or the trial for this framework writes its session file here (the second cause above). `HANDOFF.md` changes only in a PR of its own | owner decides; a session writes it | no |
| The branch `ccr-6ed8a82e-cxmftx` | framework | Three unmerged commits of 2026-10-22 on an end file; delete the branch or keep it | owner | no |
| This repository's pin | `sdlc.yaml` (1.0.46) | A move to 1.0.50 with lane G's seven guardrail rows (`docs/progress/2026-10-26-claude-r45-6-live-readers.md`). Carried from the end file; the pin re-read by this session | a lane; owner | no |
| A second close of an incident PR | the sample's runs 40409622119 and 40409702353 | Carried from the end file, not re-verified. `plugin/detect/cli.py` has not changed since 1.0.48 (`git log`), and no ROADMAP row names it | a lane, on the owner's word | no |
| A cancelled step's child processes | lane H's file | Carried from the end file, not re-verified | owner, then a lane | no |
| The sample's merge App key; its review ruleset name | the sample's settings | Carried from the end file, not re-verified (settings this session cannot read) | owner | no |
| The owner-machine managed settings | `docs/owner-machine/managed-settings.json` | Carried from the end file, not re-verified | owner | no |
| Change 0004's live checks (follow-up #4) | the sample | Carried from the end file, not re-verified | owner; the runner | no |
| Everything the files named in the end file list open | their "Every open item" | Carried, not re-verified | as there | no |

Done, dropped from the end file: "This PR" (#402, `3cc6863`); "The trial", Next steps 2 to 4 of the end file (the trial repository is named and connected, and its first intent is through: trial #1 to #5).

## What the owner does
| When | Act |
|---|---|
| Now | Merge this PR when it is green. |
| Then | #403: `gh pr update-branch 403 --repo luissiviero/sdlc-framework`, then an `@claude` comment on #403. |
| Then | The trial: the `CLAUDE.md` and CI PR (this session's record), then an `@claude` comment on trial #6. |
| When convenient | Decide on the session-file rule and on the branch `ccr-6ed8a82e-cxmftx`; the carried items above. |
