# Progress — merged changes no longer read "waiting for the owner" on `main`: plugin 1.0.25 (2026-10-23)

This session ran on branch `ccr-b2d02bf7-9ywgjn`, restarted from `main` at `f090652` after its third PR (#341) merged. Its earlier records in this folder are `2026-10-23-choices-257-258.md`, `2026-10-23-ccr-b2d02bf7-9ywgjn.md` and `2026-10-23-ccr-b2d02bf7-9ywgjn-r5.md`. It is a plugin patch, 1.0.25 (`python tasks.py next-free` on `f090652`: patch 1.0.25, nothing taken above `main`).

## Why
The owner asked to fix change 0005's record: `changes/0005-…/status.yaml` on `main` reads phase e, gate (e) passed, "waiting for the owner at gate (e)", although its build PR #211 merged on 2026-10-17. Changes 0002 and 0003 read the same.

What the session found:
- **The file is right to be unchanged.** Gate (e) is derived from the merge, never written to `main`: the automation has branch-only write access, so every reader that opens a `status.yaml` from the default branch derives "merged at gate (e)" in memory (`docs/OPERATING_MODEL.md` §4, decision 13 as amended by 36; `state/status.py`, `read_status(..., on_default_branch=True)`). The release fields stay empty here because this repository's `deploy.action` is `none`, and a release record goes to `refs/sdlc/released/<id>`, never to `main` (`release/cli.py`, verb `record`).
- **The derivation had a gap.** `merged_at_gate_e` lifted a park (change 0001 reads "merged at gate (e)") but returned a gate (e) that had already passed unchanged, so the build run's reason, "waiting for the owner at gate (e)", true only until the merge, was still shown after it. A test pinned that as "keeps its own record" (`tests/test_state.py`).

## What was built (plugin 1.0.25)
1. **`plugin/state/status.py`, `merged_at_gate_e`:** on the default branch, a gate (e) that already passed keeps its result and its time, and its reason, when it is the build run's waiting reason (`WAITING_AT_GATE_E_REASON`, what `gate/gate.py` records), reads as the merge reason. Any other reason is the record's own and stays. The file on disk is still never written.
2. **Tests (`tests/test_state.py`):** the default-branch test now expects the merge reason with the gate's own time, and keeps another reason as written; a new test pins the constant to the line in `gate/gate.py` that writes it.
3. **The version:** `.claude-plugin/plugin.json` and `marketplace.json` at 1.0.25.

`state/cli.py show` and `list` print the derived gate with their "derived: merged on main" marker, which they already do whenever the derived gate differs from the record. No reader depends on a passed gate's reason or time: the release reads only that gate (e) has a result, and the counters read phases and iterations.

## Live check
On this repository's `main` checkout, read at 03:48 UTC on `f090652` with the fixed reader (`read_status(..., on_default_branch=True)`): changes 0001, 0002, 0003 and 0005 all read phase e, gate passed, "merged at gate (e): the owner's approval, or the owner's merge (decision 13, as amended by decision 36)", none parked, each with its own gate time; `git status` showed no file written.

## Left
- **The parallel lanes** take the next patch after this one: `python tasks.py version-check` refuses a lane that keeps 1.0.25 once this PR is on `main`.

## What the owner does
| When | Act |
|---|---|
| Now | Merge this PR when `Framework checks` is green on its final head; `sdlc-tag.yml` then tags `v1.0.25`. |
