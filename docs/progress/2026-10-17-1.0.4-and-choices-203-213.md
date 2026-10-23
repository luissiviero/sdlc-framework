# Progress — the safety fixes of NOTES §45 (gaps 6, 7 and 8) as plugin **1.0.4**, and the owner's choices 203 to 213 on the gaps' routes (2026-10-17)

This session ran on branch `ccr-d96dbb91-v12amc`. It first verified the item-11 follow-ups' records (PR #222, merged as `cd8baf7`), then, after PR #220 (R10, 1.0.3) and PR #223 merged, built the safety PR the owner approved. The previous record, R21 to R49 and 1.0.3, is now `docs/progress/2026-10-17-r21-r49-and-1.0.3.md`, unchanged. Only `luissiviero/sdlc-framework` was changed; the sample was read, never touched. The session's own file is `docs/handoffs/sessions/2026-10-17-ccr-d96dbb91-v12amc.md`.

## Summary
- **Gap 6, the runner's fail-open `sdlc.yaml`, is fixed.** `_approved_config` (`plugin/ci/run_phase.py`) used to read an unparseable default-branch copy as `{}`. It now raises `ConfigError`. The guard also reads the checkout's copy, which the session settings use, and refuses with "<the error>: nothing runs until it is fixed" on either one, the same refusal as `paused: yes`. Before, a broken file dropped `paused`, the profile, `protected_paths`, `max_budget_usd` and the turn cap without a word. Three tests in `tests/test_ci.py` replay PR #214's indentation: on the default branch, on a work branch that kept it after the default branch was fixed, and without a remote.
- **The root `sdlc.yaml` is now read by a test** (`tests/test_scaffold.py::test_the_root_sdlc_yaml_parses`). The same loader refuses PR #214's copy (`git show 5542406:sdlc.yaml`): "bad indentation".
- **Gap 8, the tag on a broken bump, is fixed.** `.github/scripts/sdlc_tag.py` tags nothing while `marketplace.json` names another version than `plugin.json`, or cannot be read, or has no entry for the plugin; the run then ends red. `sdlc-tag.yml` also runs on a push that touches `marketplace.json`, so the commit that brings the two back into agreement gets the tag. Four tests; each fails on the old script. Waiting for `Framework checks` before tagging stays with R5.
- **Gap 7 and the validator's README warning:** `README.md` now says to merge `main` into a conflicted PR's branch before a review, and gives the install line `/plugin install sdlc --marketplace luissiviero/sdlc-framework`. `claude plugin validate .` now gives only the `CLAUDE.md`-at-the-root warning.
- **Plugin 1.0.4** (both manifests; choice 184's next free patch).
- **An independent review** (a fresh-context agent, report only) found nothing blocking. Three of its findings were fixed:
  - the work branch that keeps an unreadable copy (should-fix);
  - a non-list `plugins` in `marketplace.json` raised instead of refusing (nit);
  - the tag workflow's Report step now runs when the tag step fails (nit).

  One finding is left as it is: an automatic fix round refused on an unreadable `sdlc.yaml` parks the change, like any unfinished round. That park is how the owner is told.

## The owner's decisions (2026-10-17)
The owner approved the session's revised decision table in full ("Approve all; build the safety PR in #1").
203. **Gaps 6 and 8 ship first, as one safety PR before R17**, built by this session: the runner refuses an unparseable `sdlc.yaml`, a test reads the root `sdlc.yaml`, and the tag script refuses disagreeing manifests. This is plugin 1.0.4.
204. **Gaps 2, 3 and 4 go into one fix-round robustness PR after R17**, before the sample moves past 1.0.1 or the trial project starts. R10 runs nowhere yet: the root pin is 0.3.6 and the sample's is 1.0.1.
205. **Gaps 1 and 5 go into R48.** A panel `park` must park (fail closed), with a test. R48 also raises the template's turn default. The sprint prompt carries the line (annotated beside R48).
206. **Gap 7 is a line in `README.md`**, in 203's PR.
207. **The sample moves to the newest release once 204 has landed**, skipping 1.0.2. The upgrade includes the four workflow copies (build, test, fix, deploy) that 1.0.3 changed. A session prepares that PR and gives the pin row and the `REVIEW.md` bullet as guardrail rows.
208. **The root `REVIEW.md` skip-marker bullet is applied by the owner** (the table below).
209. **"Small defects" and "E2":** the owner tells a session in one line what they were; until then they stay the owner's open item.
210. **The README install line** goes in 203's PR.
211. **PR #173 (change 0004, R14) waits for R14's turn** in ROADMAP's Order; the sprint comes first.
212. **The sprint (R17 first) starts after 203's PR merges**, so R17 takes the next patch number after 1.0.4.
213. **R28's timing and cost and R44's timing are answered after the sprint**, as `docs/progress/2026-10-17-r21-r49-and-1.0.3.md` says.

## Proposed edit for the owner
Carried from `docs/progress/2026-10-17-item-11-follow-ups.md` (choice 208).

| File | Line | What is there now | What it must become |
|---|---|---|---|
| [`REVIEW.md`](https://github.com/luissiviero/sdlc-framework/blob/main/REVIEW.md#L26) | after 26 (the end of the `plan.md` bullet) | nothing; line 27 starts "- The second occurrence of the same finding …" | `- Each added skip marker the gate's \`ratchets\` check listed at gate (e) (\`evidence/gate-e.json\`'s \`details.skip_markers\`) must be declared in \`plan.md\` or explained in the PR; an undeclared one quietly narrowing what the suite actually runs is non-compliant.` (the same bullet `template/REVIEW.md:27-30` carries since 1.0.2) |

## Checks (this repository)
On the final head, after `python -m pip install -e ".[dev]"`, chained with `set -o pipefail`: the four commands of `HANDOFF.md`'s standing precondition 1. Their output is in the PR.

## Left
- **Next: the sprint**, from `docs/handoffs/2026-10-17-pipeline-sprint-prompt.md` (choice 212), once this PR has merged and `v1.0.4` is tagged.
- **Then the fix-round robustness PR** (choice 204), then the sample's upgrade (choice 207).
- **Port list:** this PR touches `plugin/ci/run_phase.py`. `HANDOFF.md`'s port-list rule runs "until the 1.0.0 read", which item 11 made (`docs/progress/2026-10-14-item-11.md`), so it is named here only for the trail.
