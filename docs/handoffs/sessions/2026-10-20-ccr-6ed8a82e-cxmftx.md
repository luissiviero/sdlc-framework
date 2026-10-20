# Session of 2026-10-20 on branch `ccr-6ed8a82e-cxmftx`: the Gemini study checked, choice 246, R8 as plugin 1.0.18

**Builds on:**
- `docs/handoffs/sessions/2026-10-20-ccr-8b4eb57f-uy0e8e-end.md` (#297, the Gemini study), the newest session file on `main` at `57b5a85`.
- `docs/handoffs/sessions/2026-10-20-ccr-5953b5a0-gblc0q-end.md` (#295, R64 registered), which is not named in that file's header and is newer than the files it names; read on `main` at `57b5a85`.

No other session file is newer (verified, `ls docs/handoffs/sessions/` and `git log --diff-filter=A` per file on `main` at `57b5a85`).

The owner's task: check the study independently (report only), put its four questions to the owner, then build the owner's four items as the study reads them.

## Where the project stands
- **`main` is at `57b5a85`** (verified, `git log -1 origin/main`): #295 merged as `0af0b47` and #297 as `57b5a85`. Plugin **1.0.17** on `main`; the root pin is `version: 1.0.17` (verified, `sdlc.yaml:104`).
- **The sample's `main` is at `4a429c4`** with pin 1.0.17 (verified, its `sdlc.yaml:77`), and its workflow copies are 1.0.17's: nine steps pass `GEMINI_API_KEY` to a session (verified, `grep` on its `.github/workflows`). Its secret is unset (carried from `2026-10-20-ccr-5953b5a0-gblc0q-end.md`, not re-verified).
- **Open PRs** (verified, the GitHub list): framework #173 (intent 0004) and this session's PR; sample #55.
- **The check**: `docs/reviews/2026-10-20-gemini-study-check.md`. **Choice 246** and what 1.0.18 builds are in `docs/PROGRESS.md`.
- **This session's PR, #304**, draft, plugin **1.0.18**: #290's session part undone; R8 built for (b) and (e) in a `second-opinion` job after the phase job, off by default. R8's row is under "Done" in ROADMAP.

**A correction:** `2026-10-20-ccr-8b4eb57f-uy0e8e-end.md` lists "The sample's upgrade to 1.0.17" as open. The sample was already on 1.0.17 (sample #89, #90 and #91, merged before that file was written).

## Preconditions of the moment
- The standing ones are in `HANDOFF.md`.
- **Next free numbers:**
  - candidate R65;
  - choice 247 (246 taken here);
  - note 56;
  - decision file 37 (read `docs/decisions/` first);
  - patch 1.0.19 after this PR.
- The sample's new workflow copies need its pin at 1.0.18 first: the `second-opinion` job runs `framework/plugin/external/cli.py`, which 1.0.17 does not have.

## Next steps, in order
1. **The owner merges this session's PR** once `Framework checks` is green; `sdlc-tag.yml` tags `v1.0.18`.
2. **The owner's pastes**, after the tag (the table in "What the owner does").
3. **The sample**: the secret, the `sdlc.yaml` paste, then sample #92 (the 1.0.18 workflow copies, draft, opened by this session from #304's templates), in that order.
4. **The first live (b)** on the sample: the next change the owner opens there. The session that reads it writes R8's first tally row (`docs/proposals/external-design-check.md`, "Tally") and records whether the API accepted the request's shape.
5. Then the next steps of the files this one builds on, carried unchanged, not re-verified: R60's answers into R22's row, R22's build, and the ROADMAP candidates in their Order column.

## Every open item
| Item | Where | What is left | Who acts | Blocks 1.0.0 |
|---|---|---|---|---|
| This session's PR | framework | `Framework checks` green, the owner's merge | owner | no |
| The pastes of choice 246 | both `.claude/settings.json` files; the root `sdlc.yaml` | The owner's pastes (below) | owner | no |
| The sample's second opinion | the sample | Its secret, its `sdlc.yaml` paste, then the PR of 1.0.18 workflow copies | owner, then a session | no |
| The model id | `external_review.model` | `gemini-4-argon` was read only in search extracts of Google's pages. `python plugin/external/cli.py models` with the key settles it; a wrong id is a "not run: HTTP 404" comment, never a red job. | owner (by hand) or the first live run | no |
| The request's shape | `plugin/external/gemini.py` | Not verified live: `responseSchema`, `responseMimeType`, the `x-goog-api-key` header | the session that reads the first live run | no |
| A second opinion at (e) on a deploy job that ran nothing | `sdlc-deploy.yml`, the `second-opinion` job | It runs whenever the deploy job succeeds, also when the runner's guard skipped phase (e) on that event; a re-run on the same head is free (it finds its own comment) | a later build, if the tally shows waste | no |
| R8's tally; the panel double | `docs/proposals/external-design-check.md`; a decision file with R28's amendment of 21 | After five changes, the owner keeps, promotes or drops it; the panel double later | the reading session; owner | no |
| The port list | `docs/PROGRESS.md`, "The port list" | This PR touches `plugin/ci/run_phase.py` and the detect and fix templates: on the list until the 1.0.0 read | the 1.0.0 read | no |
| R64 | `docs/proposals/template-copies-refresh.md` | The build at its rank (carried) | the session at its rank | no |
| The (d) check run beside a park after the commands step | `plugin/ci/run_phase.py` | Not fixed (carried) | a later build that touches the runner | no |
| The framework's two workflows on CLI 2.1.278 | `substrate-smoke.yml`, `framework-evals.yml` | The owner's call (carried) | owner | no |
| R60's holds and answers | `2026-10-20-ccr-d901d09c-s87xed-part-2.md` | Carried unchanged, not re-verified. The session `ccr-0522ec37-iia2ok` that was carrying them has a branch on the remote and no open PR (verified, the GitHub list). | as there | no |
| Sample #55, change 0010 | the sample | Scheduled by the owner (carried) | owner | no |
| The advocate under an Opus session; the build PR's "What changed and why" line; the gate's spend total one round late | NOTES §55 | Carried from `2026-10-20-ccr-a6fc1017-mkylxv.md`, not re-verified | as there | no |
| R24's six questions | `docs/progress/2026-10-20-r24-risk-hit-banner-1.0.15.md` | Carried, not re-verified | owner | no |
| Everything else the "-end" and 8913e578 files list open | `2026-10-20-ccr-7ef35daa-7adzh8-end.md`, `2026-10-20-ccr-8913e578-kwfegl.md` | Carried unchanged, not re-verified | as there | no |

Done, dropped:
- "The study's four questions" and "#290's session exposure" (the 8b4eb57f "-end" file): choice 246 and this PR.
- "The Gemini host only when the key is set; the read-only wrapper" (the 5953b5a0 "-end" file): the host is off the CI sandbox for every project, and the client is `plugin/external/`.
- "The Windows variable and the cloud environment secret" (the 8b4eb57f "-end" file): neither is set. A persistent Windows variable reaches every local Claude Code session and a cloud secret every cloud session, which would repeat #290's exposure. By hand, the owner sets the key in one terminal window only.
- "The sample's upgrade to 1.0.17": done before that file (above).
- "This session's last PR" (the 5953b5a0 "-end" file): merged as `0af0b47`.

## What the owner does
| When | Act |
|---|---|
| Now | Read this session's PR; merge it when `Framework checks` is green. |
| After `v1.0.18` | Paste the three framework files (the full contents are in the chat; the rows are in `docs/PROGRESS.md`, "Proposed edits for the owner"). |
| After `v1.0.18`, for the sample | First add the repository secret `GEMINI_API_KEY` (Settings, Secrets and variables, Actions). Then paste its `sdlc.yaml` (the full content is in the chat: pin 1.0.18 and `external_review: {model: gemini-4-argon, phases: [b]}`). Then merge the session's PR of the 1.0.18 workflow copies. |
| Before the first live run, optional | In one PowerShell window: `$env:GEMINI_API_KEY = "<key>"`, then `python plugin/external/cli.py models` from the framework checkout, to confirm the model id. |
| 2026-10-24 | On the PC: `git pull`, then `python -m pip install -e ".[dev]"` (the reminder, carried). |
