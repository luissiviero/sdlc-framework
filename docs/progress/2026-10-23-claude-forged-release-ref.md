# Progress — the forged release ref, plugin 1.0.29 (2026-10-23)

This session ran on branch `claude/forged-release-ref`, from `main` at `d72de6a` (#344), as the small lane beside wave 2's two build sessions, started at the owner's request on 2026-10-23. Its first item is choice 261, point 2 (`docs/progress/2026-10-23-claude-r44-r59-i5.md`, "The owner's choices"): the forged release ref of `docs/proposals/sandbox-closes-gaps.md` ("What to settle", last row). This PR changes `plugin/`, so it bumps the patch. `python tasks.py next-free` gave 1.0.29 on `d72de6a` (lane B's `claude/r29-r54-quick-intent` holds 1.0.28). No choice, note or decision number is taken.

## What was built
1. **`run_phase.released_refs`** reads `git ls-remote origin refs/sdlc/released/<id>` and keeps every ref it lists, by full name. The runner's `fetch --prune origin` brings only `refs/heads/*`, so the ref is never in `refs/remotes/`. `ls-remote` matches the pattern against the tail of a name, so `refs/tags/refs/sdlc/released/<id>` and `refs/heads/refs/sdlc/released/<id>`, which the release workflow's fetch of the short name would take for the record, are read too. When `ls-remote` fails, the ref reads `unreadable`.
2. **`run_phase.origin_urls`**: a digest of origin's fetch and push URLs as git resolves them (`insteadOf` and `pushInsteadOf` expanded). A digest, never the URLs, since a park reason is committed.
3. **`change_refs`** adds both to its map, beside the change's branches. The runner already calls it before and after the session, so neither call site changes. A session that removes or renames `origin` empties the map after it, so every key it had before differs.
4. **`session_push_mismatches`** names each in its own words: a release ref created (`absent -> <sha>`), moved or deleted (`<sha> -> absent`), with the full sha; a remote that could be read before the session and not after it; origin's URLs changed or origin removed. The run parks under `session_branch`, as a push to another branch of the change does. `SESSION_BRANCH_NEED` says how to put the ref back, and to leave it when the release workflow wrote it during the run.
5. **Two tests** (`tests/test_ci.py`), eight cases: a session that creates, moves or deletes the ref, pushes one of the two name variants, or reads through a mirror while pushing to the real remote parks under `session_branch`, run through the full runner; an untouched ref is no reason, an unreadable read after a readable one is one, and two unreadable reads are none.

## Why deletion and an unreadable read park too
The release workflow writes the ref after a release (`release/cli.py`, `remote_record`, and the record job of decision 35). A session that deletes it removes the record a later release run reads first. A read that fails after the session, when the one before it worked, cannot tell a forged ref from an untouched one, so the runner fails closed. Two failed reads are a remote the job cannot reach: the session cannot make the read before it fail, and the end-to-end tests' checkout, whose fetch URL is unreachable by design, runs that way.

## Known limits, recorded
- **A release job that runs during a phase run of the same change** (an owner's merge while a fix round runs on the PR head) moves the ref and parks that run. The park text says to look at the release workflow's run first and leave a ref it wrote.
- **The reads go through the checkout's git config.** A planted program is refused (`refuse_planted_config`, R44's I4) and a changed origin URL parks, but a planted `http.proxy` or `http.<url>.*` key could still serve the read after the session from elsewhere. The full answer is a read through the GitHub API or with a clean config, R3's fresh clone or I6's separate job; not built here. The reviewer's re-check names the one shape left: a planted `http.proxy` with a background process of the session's that serves the read, which needs the detached process of the next row.
- **A detached background push** the session starts and that fires after the read that follows it is not seen; the branch check has the same limit. Ending the session's process group when `invoke` returns would close both; not built here.
- **Only the change's own ref is read.** A session that writes another change's `refs/sdlc/released/<other>` makes that change's release skip. Reading `refs/sdlc/released/*` would park a run whenever any other change is released during it (R51's concurrent changes), so it is left; recorded.
- **The release workflow's own read** (`release/cli.py`, `_remote_ref` and `_fetch`) still takes any ref whose name ends with the pattern. The runner now parks a session that pushes such a name; matching the exact name there too is a small hardening, left for a release-side PR so this one stays local to the runner.
- **`status.yaml`'s `released_*` fields** are not owner-only fields (`run_phase.owner_fields`), so a session on `sdlc/<id>/c` can write `released_pr` and the merged copy makes the release skip. It shows in the PR's diff, unlike the ref. A sibling gap, outside choice 261's point 2; see "What I need from you".
- **Not verified live** on a runner; the tests use a local bare remote.

## Port list (HANDOFF.md, "Rules for every session")
This PR touches `plugin/ci/run_phase.py`, so it goes on the port list until the 1.0.0 read. The change stays inside `change_refs`, the two readers it calls (`released_refs`, `origin_urls`), `session_push_mismatches` and `SESSION_BRANCH_NEED`.

## The fresh-context review
A fresh-context sub-agent reviewed the first version (report only), with experiments against a local bare remote. Its findings and what was done:
1. **Blocking, fixed:** `refs/tags/refs/sdlc/released/<id>` and `refs/heads/refs/sdlc/released/<id>` got past the runner's exact-name match, and the release workflow's fetch of the short name takes them for the record. The runner now keeps every ref `ls-remote` lists; two test cases.
2. **High, fixed in part:** the session could point origin's fetch URL at a mirror (or rename origin) so the read after it saw nothing. Origin's URLs are now compared; a test case. A planted `http.*` key stays a known limit.
3. **High, outside this point's scope:** `released_*` in `status.yaml`; under "Known limits" and "What I need from you".
4. **Medium, fixed:** the park text dropped "unless the push is yours" and gave a 10-character sha; it now gives the full sha, says to fetch the ref first and to leave one the release workflow wrote.
5. **Fixed in part:** an unreadable read after a readable one parks with its own reason; two unreadable reads stay no reason, for the reason above.
6. and 7. Recorded under "Known limits".
It also found the `ruff format` failure of the first version, fixed.

A second pass on the fixes (`b955ec3`) found nothing still blocking.

## What I need from you
1. **`status.yaml`'s `released_*` fields as owner-only fields.** My recommendation: yes, in a small follow-up PR in R44's class. `run_phase.owner_fields` gains `released_at`, `released_pr` and `released_sha`, so a session that writes them parks as one that accepts a risk does; only the release workflow sets them, after the merge.

## Proposed edits for the owner
None.

## What the owner does
| When | Act |
|---|---|
| Now | Merge this PR when `Framework checks` is green on its final head. |
