# Session of 2026-10-20 on branch `ccr-6ed8a82e-cxmftx`: the Gemini study checked, choice 248, R8 as plugin 1.0.19

**Builds on:**
- `docs/handoffs/sessions/2026-10-20-ccr-8b4eb57f-uy0e8e-end.md` (#297, the Gemini study), the newest session file on `main` at `57b5a85`.
- `docs/handoffs/sessions/2026-10-20-ccr-5953b5a0-gblc0q-end.md` (#295, R64 registered), which is not named in that file's header and is newer than the files it names; read on `main` at `57b5a85`.

No other session file was newer when the session started (verified, `ls docs/handoffs/sessions/` and `git log --diff-filter=A` per file on `main` at `57b5a85`). Three reached `main` while this PR was open, and are read and carried here (`main` at `0e11ae9` merged in):
- `2026-10-20-ccr-0522ec37-iia2ok.md` (#296, R22's hold lifted; #299, decision 37);
- `2026-10-20-ccr-0522ec37-iia2ok-part-2.md` (#300, #301, #302, decision 38);
- `2026-10-20-ccr-d6ff91d5-syonv1.md` (#298, choice 246 on change 0004; #303, choice 247).
- Then, at the second merge of `main` (`18b2a22`): `2026-10-20-ccr-0522ec37-iia2ok-part-3.md` (#305, the last R60 holds lifted) and `2026-10-20-ccr-0edc2256-yax6jz.md` (#306, R22 as plugin 1.0.18).

The owner's task: check the study independently (report only), put its four questions to the owner, then build the owner's four items as the study reads them.

## Where the project stands
- **`main` is at `57b5a85`** (verified, `git log -1 origin/main`): #295 merged as `0af0b47` and #297 as `57b5a85`. Plugin **1.0.17** on `main`; the root pin is `version: 1.0.17` (verified, `sdlc.yaml:104`).
- **The sample's `main` is at `4a429c4`** with pin 1.0.17 (verified, its `sdlc.yaml:77`), and its workflow copies are 1.0.17's: nine steps pass `GEMINI_API_KEY` to a session (verified, `grep` on its `.github/workflows`). Its secret is unset (carried from `2026-10-20-ccr-5953b5a0-gblc0q-end.md`, not re-verified).
- **Open PRs** (verified, the GitHub list): framework #173 (intent 0004) and this session's PR; sample #55 and this session's sample #92.
- **`main` moved to `0e11ae9` while this PR was open** (verified, `git log origin/main`): #296, #298, #299, #300, #301, #302 and #303 merged, documentation and `tasks.py` only, still plugin 1.0.17. It is merged into this branch; the conflicts were `docs/PROGRESS.md` and `docs/progress/index.md` only.
- **The check**: `docs/reviews/2026-10-20-gemini-study-check.md`. **Choice 248** and what 1.0.19 builds are in `docs/PROGRESS.md`.
- **This session's PR, #304**, draft, plugin **1.0.19** (R22 took 1.0.18 first, #306): #290's session part undone; R8 built for (b) and (e) in a `second-opinion` job after the phase job, off by default. R8's row is under "Done" in ROADMAP.

**A correction:** `2026-10-20-ccr-8b4eb57f-uy0e8e-end.md` lists "The sample's upgrade to 1.0.17" as open. The sample was already on 1.0.17 (sample #89, #90 and #91, merged before that file was written).

## Preconditions of the moment
- The standing ones are in `HANDOFF.md`.
- **Next free numbers:**
  - candidate R65;
  - choice 249 (248 taken here; 246 and 247 by the parallel session's #298 and #303);
  - note 56;
  - decision file 39 (37 and 38 are on `main`; read `docs/decisions/` first);
  - patch 1.0.20 after this PR (R22 is 1.0.18 on `main` since #306; this PR moved to 1.0.19). The decision-38 and decision-37 builds of session `ccr-0522ec37-iia2ok` wait for the next free patch.
- The sample's new workflow copies need its pin at 1.0.19 first, and R22's setup on the sample (its App, rulesets and merge workflow; R22's record, "Left"): the `second-opinion` job runs `framework/plugin/external/cli.py`, which 1.0.17 does not have.

## Next steps, in order
1. **The owner merges this session's PR** once `Framework checks` is green; `sdlc-tag.yml` tags `v1.0.19`.
2. **The owner's pastes**, after the tag (the table in "What the owner does").
3. **The sample**: the secret, the `sdlc.yaml` paste, then sample #92 (the 1.0.19 workflow copies, R22's included, draft, opened by this session from #304's templates), in that order.
4. **The first live (b)** on the sample: the next change the owner opens there. The session that reads it writes R8's first tally row (`docs/proposals/external-design-check.md`, "Tally") and records whether the API accepted the request's shape.
5. Then the next steps of the files this one builds on, carried unchanged, not re-verified: R60's answers into R22's row, R22's build, and the ROADMAP candidates in their Order column.

## Every open item
| Item | Where | What is left | Who acts | Blocks 1.0.0 |
|---|---|---|---|---|
| This session's PR | framework | `Framework checks` green, the owner's merge | owner | no |
| The pastes of choice 248 | both `.claude/settings.json` files; the root `sdlc.yaml` | The owner's pastes (below) | owner | no |
| The sample's second opinion | the sample | Its secret, its `sdlc.yaml` paste, then the PR of 1.0.19 workflow copies | owner, then a session | no |
| The model id | `external_review.model` | `gemini-4-argon` is in Google's cookbook and SDK of 2026-10-19 and 2026-10-20 (`docs/reviews/2026-10-20-gemini-study-check.md`); whether the owner's key can call it is not verified. `python plugin/external/cli.py models` with the key settles it; a wrong id is a "not run: HTTP 404" comment, never a red job. | owner (by hand) or the first live run | no |
| The request's shape | `plugin/external/gemini.py` | Checked against the API's discovery document (revision 20261019) and Google's SDK, not live: `responseSchema`, `responseMimeType`, the `x-goog-api-key` header | the session that reads the first live run | no |
| The Developer API's terms | `ai.google.dev/gemini-api/terms`, `.../docs/logs-policy` | Not read: the container's proxy denies `ai.google.dev`. The paid tier, the Contributor tier and the 55-day abuse log rest on search extracts. The client sends `store: false` either way. | owner (on the PC), or a session whose network allows the host | no |
| A second opinion at (e) on a deploy job that ran nothing | `sdlc-deploy.yml`, the `second-opinion` job | It runs whenever the deploy job succeeds, also when the runner's guard skipped phase (e) on that event; a re-run on the same head is free (it finds its own comment) | a later build, if the tally shows waste | no |
| R8's tally; the panel double | `docs/proposals/external-design-check.md`; a decision file with R28's amendment of 21 | After five changes, the owner keeps, promotes or drops it; the panel double later | the reading session; owner | no |
| The port list | `docs/PROGRESS.md`, "The port list" | This PR touches `plugin/ci/run_phase.py` and the detect and fix templates: on the list until the 1.0.0 read | the 1.0.0 read | no |
| R64 | `docs/proposals/template-copies-refresh.md` | The build at its rank (carried) | the session at its rank | no |
| The (d) check run beside a park after the commands step | `plugin/ci/run_phase.py` | Not fixed (carried) | a later build that touches the runner | no |
| The framework's two workflows on CLI 2.1.278 | `substrate-smoke.yml`, `framework-evals.yml` | The owner's call (carried) | owner | no |
| R22's owner acts and live checks | `docs/progress/2026-10-20-r22-gate-e-approving-review-1.0.18.md`, "Proposed edits for the owner" and "Left"; `2026-10-20-ccr-0edc2256-yax6jz.md` | R22 merged as 1.0.18 (#306). Its root `sdlc.yaml` rows are folded into this session's one paste. Its other items are carried unchanged, not re-verified. | owner; that session | no |
| The narrowed modes' removal; the credential order's code | decisions 37 and 38, point 4 each | Two plugin versions, one build session at a time. Decision 38's touches `plugin/evals/run.py`, where this PR strips the Gemini key from the eval session's environment. | later build sessions | no |
| The conclusion's ports; `CLAUDE.md`'s fallback sentence; the Actions-minutes figure; the artifacts question | `2026-10-20-ccr-0522ec37-iia2ok.md`, its parts 2 and 3 | Carried unchanged, not re-verified. The holds of R11, R30, R39 and R16 were lifted by #305 (part 3). | as there | no |
| Change 0004's remaining questions | `docs/reviews/2026-10-20-0004-open-questions.md` | At R14's turn; read Q4's answer before R33 (carried from `2026-10-20-ccr-d6ff91d5-syonv1.md`, not re-verified) | the sessions at those ranks | no |
| R60's holds and answers | `2026-10-20-ccr-d901d09c-s87xed-part-2.md` | Carried in for R22 by #296 and for R52 by #301, both merged (verified, `git log origin/main`); R11, R30, R16 and R39 by #305; no hold is left | as there | no |
| Sample #55, change 0010 | the sample | Scheduled by the owner (carried) | owner | no |
| The advocate under an Opus session; the build PR's "What changed and why" line; the gate's spend total one round late | NOTES §55 | Carried from `2026-10-20-ccr-a6fc1017-mkylxv.md`, not re-verified | as there | no |
| R24's six questions | `docs/progress/2026-10-20-r24-risk-hit-banner-1.0.15.md` | Carried, not re-verified | owner | no |
| Everything else the "-end" and 8913e578 files list open | `2026-10-20-ccr-7ef35daa-7adzh8-end.md`, `2026-10-20-ccr-8913e578-kwfegl.md` | Carried unchanged, not re-verified | as there | no |

Done, dropped:
- "The study's four questions" and "#290's session exposure" (the 8b4eb57f "-end" file): choice 248 and this PR.
- "The Gemini host only when the key is set; the read-only wrapper" (the 5953b5a0 "-end" file): the host is off the CI sandbox for every project, and the client is `plugin/external/`.
- "The Windows variable and the cloud environment secret" (the 8b4eb57f "-end" file): neither is set. A persistent Windows variable reaches every local Claude Code session and a cloud secret every cloud session, which would repeat #290's exposure. By hand, the owner sets the key in one terminal window only.
- "The sample's upgrade to 1.0.17": done before that file (above).
- "This session's last PR" (the 5953b5a0 "-end" file): merged as `0af0b47`.

## What the owner does
| When | Act |
|---|---|
| Now | Read this session's PR; merge it when `Framework checks` is green. |
| After `v1.0.19` | Paste the three framework files (the full contents are in the chat; the rows are in `docs/PROGRESS.md`, "Proposed edits for the owner"). |
| After `v1.0.19`, for the sample | First R22's setup on the sample (its record, "Left"). Then add the repository secret `GEMINI_API_KEY` (Settings, Secrets and variables, Actions). Then paste its `sdlc.yaml` (the full content is in the chat: pin 1.0.19, R22's row 6 and `external_review: {model: gemini-4-argon, phases: [b]}`). Then merge sample #92, the 1.0.19 workflow copies. |
| Before the first live run, optional | In one PowerShell window: `$env:GEMINI_API_KEY = "<key>"`, then `python plugin/external/cli.py models` from the framework checkout, to confirm the model id. |
| 2026-10-24 | On the PC: `git pull`, then `python -m pip install -e ".[dev]"` (the reminder, carried). |
