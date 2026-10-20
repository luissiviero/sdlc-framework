# Progress — R64 registered: /sdlc-init refreshes the files it wrote once (choice 245); the pins at 1.0.17 and the sample's upgrade (2026-10-20)

This session ran on branch `ccr-5953b5a0-gblc0q`, after #291 (R63 as plugin 1.0.16) merged. The owner's tasks: align the guardrail edits of this session and of `ccr-8b4eb57f-uy0e8e` (#290) so each file is edited once, say which PRs were ready to merge and in what order, open the sample's upgrade to 1.0.17, refresh the sample's two READMEs, then write and register the candidate behind that refresh with a rank of the session's choosing. The previous record (R63 as 1.0.16) is now `docs/progress/2026-10-20-r63-cli-default-1.0.16.md`, unchanged. The session's files are `docs/handoffs/sessions/2026-10-20-ccr-5953b5a0-gblc0q.md` (R63) and `docs/handoffs/sessions/2026-10-20-ccr-5953b5a0-gblc0q-end.md` (this part).

No change under `plugin/` or `template/` in this PR; no version bump.

## Summary
- **Choice 245**: R64 is accepted and registered; its proposal is `docs/proposals/template-copies-refresh.md`, its row in `docs/ROADMAP.md`.
- **The pins are at 1.0.17 in both repositories**:
  - the framework's root `sdlc.yaml` by the owner's #292, merged as `b3dc071`;
  - the sample's by its #89, merged as `7e27773`;
  - the sample's workflow copies follow in its #90, merged as `d8290c1`.
- **The previous record's owner edits are all done.** Its three rows went into #292 and sample #89, the 1.0.17 versions agreed with #290's session. R24's two root comment rows and the sample's three R24 rows rode in the same two PRs.

## The owner's decision (2026-10-20)
245. **R64 is accepted, its rank left to the session** (the owner, "Write it and register it in roadmap. You decide where's its best implementation order among the other items."). The session placed it after R27 (rank 19) and before R45 (rank 20), with no rank moved. Its reasons are in the proposal's "Order":
    - R45's rename rewrites the names both READMEs and every workflow copy carry, so a refresh built first carries the rename into every project in one re-run;
    - R61 changes the same `plugin/init/sdlc_init.py` earlier in the queue;
    - nothing presses sooner, since the sample is current (sample #90 and #91) and no other project exists before the trial.

## What happened after #291
- **#291 merged** as `d3bfdb4` at 15:40 UTC; `sdlc-tag.yml` tagged `v1.0.16` on it (verified, `git ls-remote --tags origin`).
- **The guardrail edits were aligned with #290's session** (`session_01DgZ9p4G2jyWVPNNc7erSZS`), so the owner edited each file once:
  - #290 moved to 1.0.17;
  - one root `sdlc.yaml` paste, `version: 1.0.17` with R24's two comment edits, after `v1.0.17`;
  - both `.claude/settings.json` files from #290's session alone;
  - the sample's `sdlc.yaml` from this session, at 1.0.17 with R24's rows and R63's comment.

  Each file the owner put in a PR (#292, #293, #294, sample #89) was compared with the agreed text: identical but for a final newline the web editor drops. Merged together with #290 on top of `main`, they passed every local check (2257 tests).
- **The merge order the owner followed**:
  - #294 before #290, so `v1.0.17` carries the template's Gemini host;
  - #290 merged as `ef39013`, and `v1.0.17` and its release page were created on it;
  - #292 after the tag;
  - on the sample, #88 (0017's gate (e)) first, then #89, then #90.

  #289 (the pin to 1.0.15) was closed unmerged at 17:07 UTC (verified, the GitHub API).
- **Sample #90** (the 13 workflow copies and the pin script from `v1.0.17`) had to follow #89. Its release record step passes `--released` and `--acceptance`, which `release/cli.py` has only from 1.0.15 on. In 1.0.17 both default to the old behaviour, so the old copies kept working between the two merges.
- **Sample #91** (`changes/README.md` and `evals/README.md` from `v1.0.17`, merged as `4a429c4`) replaced two unedited copies of the templates at `cb23707` and `e49589c`. That drift is R64's problem.

## Left
- **R64's build**, at its rank.
- **The (d) check run beside a park after the commands step** (the R63 review's finding 5): carried in the R63 session file.
- **The framework's two workflows on CLI 2.1.278** (`substrate-smoke.yml`, `framework-evals.yml`): unchanged under R63's rule; whether to align them with 2.1.304 is the owner's call.

## The port list
This PR touches no file of the port list's paths.

## Proposed edits for the owner
None.

## Checks (this repository)
On the final head, after `python -m pip install -e ".[dev]"`, chained with `set -o pipefail`: `python -m compileall -q plugin tests tasks.py .github/scripts`, `python -m ruff check .`, `python -m ruff format --check .`, `python tasks.py docs-lint`, `python -m pytest -n 4` and `claude plugin validate .`. Their output is in the PR.
