# Progress — R51 with R25 parts 1-2: concurrent changes made safe, the weekly window guarded (plugin 1.0.25, 2026-10-23)

This session ran on branch `claude/r51-r25-concurrent-spend`, from `main` at `f090652` (#341). It is lane A of the two parallel build sessions the owner started on 2026-10-23; lane B builds R44 with R59 and R3's I5 in another session. By choice 238 this PR merges first, and lane B merges `main` in after it. The plugin moves from 1.0.24 to 1.0.25 (`python tasks.py next-free`, read after `git fetch origin` at 03:40 UTC on `f090652`).

## The two GitHub facts (R51's row asked for them before the design relied on them)
Both are in `docs/notes/59.md`.
- **GH-ref, reproduced against this repository.** A push of the object a ref already holds answers "Everything up-to-date" with exit 0, with or without `--force-with-lease=<ref>:`. So the race analysis's remedy for its row 1 (the empty lease) does not refuse a second reservation of the same default-branch tip. A plain push of a child commit fast-forwards over a reservation of the tip. Only a commit unique to the allocation, pushed with the empty lease, is refused whenever the ref exists (`stale info`). The design takes both halves.
- **GH-queue, read in GitHub's documentation** (Context7; a direct fetch of docs.github.com was refused here): one pending run per group, and a newer pending run cancels the older. GitHub now also documents an optional `queue: max`; it was not tried, and nothing here relies on it.
- The two probe branches, `claude/r51-ghref-probe` and `claude/r51-ghref-probe2`, stay on `origin`: the session's proxy refused their deletion (HTTP 403), and it was not worked around.

## What was built
### R51 (`docs/proposals/concurrent-changes.md`; the checks of `docs/reviews/2026-10-20-r51-race-analysis.md`)
1. **G2, the id reservation** (checks 1 to 5):
   - `new-change` reserves `sdlc/<id>/a` on the remote before it writes the folder (`gitops.reserve_change_id`, `state/cli.py reserve_new_id`). The reservation is an empty commit of its own, made on the default branch's tip with a random nonce, and pushed with the empty lease.
   - Only git's own refusal counts as "taken". Each retry reads `ls-remote` afresh and skips every refused id, five tries at most. Any other failure keeps today's best-effort id and says so on stderr.
   - A local `sdlc/<id>/a` is made at the reservation, so the id's first `commit-phase` checks it out and its push fast-forwards, even from a stale local default branch.
   - `remote_change_ids` is never remembered (check 4); the module comment says so.
2. **G1 before gate (e)** (checks 6 and 7): before the REVIEW.md pass, the (e) run and a fix round at (e), the runner merges the default branch into the work branch (1.0.10's `merge_default_branch`, with a message of its own) and runs the three targets itself on the merged tree. A conflict or a red target parks as `base_update` (`plugin/ci/base_update.py`). The merge commit is pushed by the run's next push.
3. **A rejected push** (check 12): `gitops.push` fetches the moved branch, merges it with a merge commit and pushes once more. A conflict or a second rejection is an error. `commit-phase` reports the merge as `remote_merged`, and the runner re-runs the targets on that tree after the run record's push and parks when they are red.
4. **The release** (checks 9 to 11):
   - `sdlc-release.yml` has one group for the repository, `sdlc-release`, so two `deploy.command` runs never overlap.
   - `release/cli.py` runs the three targets on the merge commit before the command, without the GitHub token in their environment. Red is a red job that prints the route back (check 10): fix the default branch in a change of its own, then dispatch the release with the PR number.
   - A merge commit that a newer recorded release (`refs/sdlc/released/<id>`) already holds is skipped, so an older tree never goes over a newer one.
5. **Check 13 already held**: every fix round reads its reviews, threads and comments from GitHub (`plugin/ci/fix_requests.py`), and a pending automatic round's targets are in `auto-round.json` on the branch. Only the trigger link is the trigger's own, and it is provenance, not a request.
6. **Choice 239's six `gitops` items:**
   - read-only queries are bounded at 60 s again, and a timeout is a `GitError`, which `gate/diff.py` maps to `GitUnavailable`;
   - the audit-hook comment is narrowed to the process starts it sees, counted at the start only;
   - a test starts real processes through `os.system`, `os.spawnv` and `subprocess` everywhere, and through `os.posix_spawn` and `os.fork` on POSIX;
   - `--git-dir`, `--work-tree`, `--namespace`, `--super-prefix`, `--config-env` and `--attr-source` with a separate value read as "not understood";
   - `is_repo` also stats the work tree's `.git` entry, so a linked worktree removed by hand loses its yes;
   - the misnamed test is renamed `…_push_set_head_and_checkout`.

### R25 parts 1-2 (`docs/proposals/weekly-window-guarded.md`; choice 257's M8 and the credential)
1. **The outer bounds park** (part 1): a session stopped by the CLI's turn limit, its budget stop or the runner's timeout parks with `limits: <the bound>` and `limits.OUTER_BOUND_NEED`. Its stored result and partial evidence are committed, and the run is green.
   - This holds at (b) to (e) and in a fix round; an automatic round with nothing to keep ends green after decision 29's own park.
   - The review pass and (f) stay red and say why: a parked review would let the (e) step of the same job run on it, and (f) hands its park to `detect/cli.py finish`.
2. **The deploy job's `timeout-minutes`** goes from 200 to 330, covering the review pass (125) and phase (e) (185), so the runner's timeout fires before the job's (the proposal's "deploy job" row).
3. **M8**: the spend the budget, the gate and the PR read is rebuilt from the stored session results (`limits.spend_from_runs`), never from `evidence/spend.json`. The runner snapshots them before each session and puts back, and parks on, any the session created, changed or deleted, as it does for its own round files.
4. **Each run line records the credential that paid** (`oauth`, the subscription token, or `api_key`), the session's wall time and whether the runner's timeout stopped it, as `sdlc_run` in the stored result. A session with no result keeps a line with no figure, counted as unknown and never invented.
5. **The spend on the PR** (part 2): one line under the counters, with the total and, per credential, the runs, their time and their USD.
6. **The Actions-minutes meter** (R60's port into R25): on a private repository the digest shows "Actions minutes this month: n of 2,000" near the top and warns at 80%. Each job is rounded up to the minute with no multiplier, at most 300 runs are read, and a busy month says "at least". A public repository gets no line. The digest workflow already held `actions: read`.
7. `gate.max_turns` was already in the template's `sdlc.yaml` (point 6 of the proposal): nothing to do.

### Documentation
- `docs/OPERATING_MODEL.md`: one dated sentence each on the id reservation (§8), the deploy row and the release row (§4.2), and the outer bounds (§6).
- ROADMAP: R51's and R25's rows annotated, as choice 259 allows a build PR.
- `docs/notes/59.md` and the regenerated notes index.

### Existing tests whose expectation changed with the behaviour
Each change follows a behaviour the accepted proposals change on purpose; no test was skipped or deleted.
- `tests/test_fix_round_gaps.py`, the turn-cap test: the run is green and the reason says "stopped at the turn limit" (R25 part 1). Before, it asserted a red run with "claude exited 0, error_max_turns".
- `tests/test_fix_round_gaps.py` and `tests/test_fix_round_edges.py`, ten gap-3 tests (three and seven): they used the turn limit only as an example of a failed session. They now use a session that failed with `error_during_execution` (`FAILED_RUN`), which no outer bound stops, and keep their assertions on the gap-3 path.
- `tests/test_gate.py`, three budget tests, and `tests/test_ci.py`'s no-budget-left test: they also write the stored session results the total is now rebuilt from (M8). The ledger assertions stay, and one more shows that an emptied ledger no longer lowers the total.
- `tests/test_templates.py` and `tests/test_ci.py`: the release group is `sdlc-release`, and the deploy job allows 330 minutes.
- `tests/test_ci_end_to_end.py`, the web-session intent test: "nothing else was pushed" now reads "the reserved `sdlc/0002/a` holds only the reservation", since `new-change` reserves the id before the round runs.

## Not built, and why
- **R51 check 8** (the (e) offer withdrawn on a later push, and the (e) run re-run on a push to the default branch for every open build PR): it needs a new trigger. Check 9 already stops an untested merge commit from deploying.
- **R51 check 11, the other half**: recording every change a release's tip holds. A release that GitHub's queue replaced stays unrecorded until the owner dispatches it with its PR number. The workflow's comment says so.
- **R25's weekly ceiling** in runs and time on the token: see "What I need from you", item 1.
- **R25 parts 3-5** and **R65's part 6** (choice 252): out of scope.

## What I need from you
1. **The weekly ceiling.** Choice 257's #5 reads "on the subscription token the weekly ceiling counts runs and time". The proposal puts the ceiling, its ledger across changes, the wait and the run-now label in part 3, after R20's part 2 and with R45's label name. This PR builds what the ceiling will count: every run line records its credential and its time. Say whether the ceiling's enforcement belongs in parts 1-2 after all; if so, name its first values (runs and hours a week).
2. **The Actions allowance.** The meter uses GitHub Free's 2,000 minutes a month, since a repository token cannot read the account's plan. Say whether your plan has another figure.
3. **Decision 11's amendment.** The proposal orders a decision file for decisions 11 and 24 before the build. Decision 11's text already parks on a "limit hit", and the outer bounds are limits, so nothing reopens it. Say whether you want the file written in a documentation PR of its own, or a dated note on decision 11 as R7 had.
4. **The two probe branches** on `origin`, `claude/r51-ghref-probe` and `claude/r51-ghref-probe2`: delete them (the session could not).

## The port list
This PR touches `plugin/ci/run_phase.py`:
- `merge_default_branch` takes a message;
- `_run_phase` gains the (e) update, the re-check after a moved push, the run-record snapshot and guard, the credential stamp (`run_line_record`) and the outer-bound park;
- `OUTER_BOUND_PARKS` is new.
It also touches `plugin/ci/base_update.py` (new), the release and deploy workflow templates and their copies in `.github/workflows/`. It goes on the port list until the 1.0.0 read.

## Proposed edits for the owner
None: no guardrail file needs to change for this PR.

## Checks (this repository)
On the final head: `python tasks.py verify` (the build, lint and test commands of `sdlc.yaml`, the docs lint, the version check and `claude plugin validate .`). Its output is in the PR.
