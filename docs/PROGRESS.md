# Progress — 1.0.1 (2026-10-14): a writable cache folder for `gh` in the CI sandbox, plugin **1.0.1**

This session ran the 1.0.1 prompt (`docs/handoffs/2026-10-14-gh-cache-1.0.1-prompt.md`, choice 194) on branch `ccr-03233066-k1441l`. The previous record, item 11's, is now `docs/progress/2026-10-14-item-11.md`, unchanged. The sample was not touched: nothing was pushed to it, no run on it was dispatched or approved, and none of its PRs was commented on or closed.

## Summary
- **Part 1, the reading**, in full in `docs/handoffs/2026-10-14-gh-cache-1.0.1-part-1.md`, and as facts in NOTES §44:
  - A sandboxed command may write the working directory and a per-user temp folder, not `$HOME`.
  - The runner's environment reaches sandboxed commands.
  - `gh run view --log-failed` writes one thing: the run's log zip under `$XDG_CACHE_HOME/gh`, else `~/.cache/gh`. It aborts when it cannot create that folder.
  - The model's own `XDG_CACHE_HOME=… gh …` was denied because an allow rule does not match past a leading variable assignment.
  - Two research passes ran in fresh contexts. This session then re-checked the sandboxing page's lines on write roots, `$TMPDIR` and the environment against the page itself.
- **The fix (option A, choice 196)**, in `plugin/ci/run_phase.py`:
  - `session_env(env, root)` sets `XDG_CACHE_HOME` to `<root>/.sdlc-cache`, replacing any value the workflow set.
  - `RUNNER_EXCLUDES` gains `/.sdlc-cache`.
  - The session may write nowhere new: there is no sandbox or permission entry, and `plugin/ci/settings.ci.json` is unchanged.
- **The tests**, in `tests/test_ci.py`; each failed on 1.0.0's code and passes on 1.0.1:
  - `test_the_session_s_gh_cache_is_a_folder_the_sandbox_lets_it_write`, which is new;
  - `test_the_session_s_environment_leaves_the_gate_s_commands_to_the_runner`, whose expected environment gains the one new key, a deliberate change of `session_env`'s contract;
  - `test_the_run_excludes_the_runner_s_own_untracked_entries_once`, which now also checks that a cached log zip is not untracked.
- **The bump**: `.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json` from 1.0.0 to **1.0.1** (choice 184: the next free patch number). Under `plugin/`, only `plugin/ci/run_phase.py` changes. Nothing under `template/` changes.
- **Port list (choice 138)**: this PR touches `plugin/ci/run_phase.py`, not `plugin/ci/settings.ci.json`.
  - It changes the environment of every phase session: (b), (c), (d), (e), (f), review and fix.
  - It does not change the weekly scan's read-only `claude -p` (`plugin/scan/cli.py`) or the triage run. Both are composed and invoked through `run_phase.compose` and `invoke`, but not through `session_env`, and neither runs `gh`.
- **The live proof is not this session's.** It is the next real diagnosis on the sample at 1.0.1 that reads a failed run's log. That needs the sample's pin moved to 1.0.1 (a guardrail row for the owner, given after the tag) and a real breach. Until then, whether 0.3.8's `results-receiver.actions.githubusercontent.com` entry lets the download through stays unknown (NOTES §41, §43).

## The owner's decisions (2026-10-14)
196. **`gh`'s cache goes into the checkout (option A of the Part 1 file).** The runner sets `XDG_CACHE_HOME` to `<root>/.sdlc-cache` in `session_env`, and the folder joins `RUNNER_EXCLUDES`. Option B (`allowWrite: ["~/.cache/gh"]` in `settings.ci.json`) and option C (a folder under `RUNNER_TEMP` with a run-time `allowWrite`) each widen what the session may write by one folder outside the checkout, so neither was chosen.

## Checks (this repository)
On the final head, in a virtual environment with `pip install -e ".[dev]"`, chained with `set -o pipefail`: the four commands of `HANDOFF.md`'s standing precondition 1. Their output is in the PR.

## Left
- **The owner**: approve the PR's runs if they wait at `action_required`; merge once the branch is up to date with `main` and all three `Framework checks` jobs are green on its final head. The tag `v1.0.1` is created on the merge itself. *[2026-10-14: done. PR #209 merged as `d0db700`, `v1.0.1` is on it, and its `main` run passed (the session file's 20:30 section).]*
- **After `v1.0.1`**: the sample's pin row (`sdlc.yaml`, `1.0.0` → `1.0.1`), a guardrail edit given to the owner as a table. The root pin stays at 0.3.6 until the sandbox proof (choice 187). *[2026-10-14: done. The owner applied it in sample PR #63, merged at 20:29:06 UTC as `f88b262`.]*
- **Then**, as before: change 0005's build and the runs PR (choice 194), each with the next free patch number.
