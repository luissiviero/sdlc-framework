# Progress — the release record as owner-only fields, plugin 1.0.34 (2026-10-23)

This session ran on branch `claude/released-owner-fields`, from `main` at `be5be5e` (#359, plugin 1.0.33), as the small lane of wave 3, started by the second central session at the owner's request. Its first item is choice 268 (d) (`docs/progress/2026-10-23-ccr-545fcec0-ik69zj.md`, on its branch until that PR merges): `status.yaml`'s `released_*` fields become owner-only fields, the point of #349's "What I need from you" (`docs/progress/2026-10-23-claude-forged-release-ref.md`, "Known limits" and "What I need from you", point 1). This PR changes `plugin/`, so it bumps the patch: `python tasks.py next-free` gave 1.0.34 after `git fetch origin` on `be5be5e`, with nothing taken above `main` but choice 268. No choice, note or decision number is taken.

## What was built
1. **`run_phase.owner_fields`** gains `released`: `(released_at, released_sha, released_pr)`, the record the release workflow commits after the merge (`template/.github/workflows/sdlc-release.yml`, the record job; `release/cli.py`).
2. **`owner_field_mismatches`** parks when the session's record is neither the one the branch carried before the session nor the default branch's copy, as it does for `fast_lane` and `risk_acceptances`: a record written, moved or cleared. A cleared record parks too, since the release would run again.
3. **`restore_owner_fields`** puts the three fields back before anything is committed, and `OWNER_FIELDS_NEED` says that no session writes them.
4. **Two tests** (`tests/test_ci.py`): the mismatch for a written, cleared and moved record, and none for one carried or approved; and the full runner, where a session that commits a release of its own change parks under `owner_fields` with the fields restored.

Nothing else in `run_phase.py` changes: lanes A and B branch after this PR and touch the same file.

## Known limits, recorded
- **A release job that writes the record on `sdlc/<id>/c` during a run of the same change.** The phase commands pull the branch inside the session (`/sdlc-fix`, `/sdlc-build`, `/sdlc-test`, `/sdlc-deploy`), so a record the release workflow pushed after the runner's checkout reaches the session's copy and parks the run as "the session recorded", and the restore writes the pre-session value over the branch's copy. The release still skips, since it reads `refs/sdlc/released/<id>` first, and in the same race the ref check of #349 already parks (its record, "Known limits", first row); `risk_acceptances`, which the record job also commits, has the same race. Not fixed here.
- **A record already on the branch before the run is not checked** (a session of 1.0.33 or earlier, or a push by hand): it is `before`, so it is kept. Its effect is a release that skips, never one that runs. A baseline rule that compares it with `refs/sdlc/released/<id>` is a follow-up.
- **`docs/OPERATING_MODEL.md:108`** lists the owner-only fields the runner checks without `released_*` (or `fast_lane`); left for a documentation PR, so this one stays inside `owner_fields`.

## The fresh-context review
A fresh-context sub-agent reviewed the diff (report only) and ran the owner-field tests across `test_ci.py`, `test_risk_banner.py` and `test_fix_round_gaps.py`. Nothing blocking: the baseline check reads none of the new key, no other caller depends on the key set, a merge of `main` before the session lands in `before`, and the restore is complete. Its optional findings: the race and the baseline gap above, recorded; a restore of a record the branch carried was not tested, now a case in the first test; the `OPERATING_MODEL` line, above.

## Port list (HANDOFF.md, "Rules for every session")
This PR touches `plugin/ci/run_phase.py`, so it goes on the port list until the 1.0.0 read. The change stays inside `owner_fields`, `owner_field_mismatches`, `restore_owner_fields` and `OWNER_FIELDS_NEED`.

## Proposed edits for the owner
None.

## What the owner does
| When | Act |
|---|---|
| Now | Merge this PR when `Framework checks` is green on its final head, before wave 3's lanes A and B branch. |
