---
type: Review
title: Race analysis for R51 (concurrent changes, safe by construction), before its build
description: Every interleaving two or more runs can produce today and under R51's design, judged; the checks R51's proposal is missing.
status: report
roadmap: R51
sources:
  - id: proposal
    resource: docs/proposals/concurrent-changes.md
    title: "R51's design: gaps G1 (a build PR behind the default branch) and G2 (two allocations take one id)"
  - id: code
    resource: plugin/state/cli.py, plugin/state/gitops.py, plugin/gate/diff.py, plugin/gate/gate.py, plugin/ci/run_phase.py, plugin/ci/app_token.py, plugin/release/cli.py, .github/scripts/sdlc_tag.py
    title: "The code the windows open in, at plugin 1.0.13 (main at the time of writing)"
  - id: workflows
    resource: template/.github/workflows/sdlc-build.yml, sdlc-test.yml, sdlc-deploy.yml, sdlc-fix.yml, sdlc-release.yml, .github/workflows/sdlc-tag.yml
    title: "The concurrency groups and triggers the runs serialise on"
generated: { by: sdlc-framework-session/ccr-5636fe98-h6vfmg, at: 2026-10-20T14:00:00Z }
---

# Race analysis for R51, before its build

**Report only; nothing is changed by it.** R51 (`docs/proposals/concurrent-changes.md`) proposes two answers: G1, a build PR behind the default branch is brought up to date and re-checked before gate (e) and before the release's `deploy.command`; G2, `new-change` reserves a new id by pushing an empty `sdlc/<id>/a` at allocation and takes the next id when that push is refused. This review enumerates the interleavings two or more actors can produce, today and under that design, and judges each. Line numbers are those of `main` at plugin 1.0.13.

Readings taken where the design is silent: (1) "before gate (e) is offered" means before the review pass step of `sdlc-deploy.yml`, not only before the gate (e) record; the proposal does not say. (2) The release "refuses or re-checks": the release job holds a read-only token (`sdlc-release.yml:66-69`), so it can re-run the three targets but can neither push a merge commit nor park a PR; a refusal is the only act it has. (3) "Refused" in G2 means git's own rejection of a ref update, not a network or credential failure.

## The actors

- A **session** (the owner's PC or a cloud session) calling `new-change` and `commit-phase --push`.
- A **maintain run** (`sdlc-detect.yml`, group `sdlc-detect`) calling the same two commands for an incident intent (`plugin/detect/cli.py:472-490`).
- A **phase run** (design, build, test, deploy, fix) in the group `sdlc-<work branch>` (`sdlc-deploy.yml:62-63`, `sdlc-test.yml:61-62`, `sdlc-fix.yml:128-129`, `sdlc-build.yml:51-53`), `cancel-in-progress: false`.
- The **owner**, merging on GitHub as the ruleset's bypass actor, clicking "Update branch", applying labels.
- The **release** (`sdlc-release.yml`), one group per pull request number (`:72-74`), running `deploy.command` on the merge commit (`:102`, `:137`).
- The **tag workflow** of this repository (`.github/workflows/sdlc-tag.yml`, group `sdlc-tag`) and R5's pin-bump PR, not yet built.

Two GitHub facts the judgements lean on, named where used: **(GH-ref)** a `git push` ref update is a compare-and-swap on the ref's old value, so creating a ref that another push created first is rejected, except that pushing the *same* object id a ref already holds is "up to date" and succeeds; **(GH-queue)** a concurrency group with `cancel-in-progress: false` runs one job and keeps at most one pending; a newer pending run replaces the older pending one, which is cancelled; GitHub does not promise that runs start in the order their events happened.

## The table

| # | Scenario | Outcome today | Outcome under R51 | Window (file:line) | What closes it |
|---|---|---|---|---|---|
| 1 | Two intents reserve an id at once (session + session, or session + maintain run) | duplicate id: both `ls-remote` before either pushes | **duplicate id still possible**: both reservations point at the same default-branch tip, and the second push of the same sha to the ref that now exists is "up to date", exit 0, not refused | `plugin/state/cli.py:53-55` (id chosen from `ls-remote`, folder written before any push); `plugin/state/gitops.py:457-458` (push without lease) | a check R51 is missing: reserve with `--force-with-lease=refs/heads/sdlc/<id>/a:` (expected value empty, so the ref must not exist, GH-ref), or create the ref through the REST API, whose 422 "Reference already exists" is the refusal, or reserve with a commit unique to the allocation |
| 2 | Same as 1, the pushes reach different shas (one clone fetched later) | duplicate id | safe: the second push is rejected (non-fast-forward, GH-ref) and the next id is taken | same | GH-ref, with R51's retry; the retry must re-read `ls-remote` and recompute `max + 1`, not `id + 1`, or it collides with a third allocation |
| 3 | Reservation refused for a reason other than "exists" (no write access, network, a cloud clone with a read-only remote) | n/a (no reservation) | **lost update / runaway**: R51 reads any refusal as "taken" and walks the ids upward, or leaves an unreserved id behind; the folder `changes/<id>-<slug>/` was already created at `cli.py:55` before the push | `plugin/state/cli.py:53-55`; `gitops.py:166-177` (one `GitError` for every failure) | a check R51 is missing: refuse only on git's "already exists" / non-fast-forward text, bound the retries, fall back to today's best-effort id on any other error, and reserve before `status.new_change` writes the folder |
| 4 | The `gitops.remembered` cache survives the reservation's own push | safe: `remote_change_ids` is never remembered (`gitops.py:485-496`), and a push moves the generation (`gitops.py:95-101`) | safe as long as the reservation pushes through `subprocess`; **stale if** R51 reserves through the REST API from the same process (no process start, generation unmoved) and then reads `ref_exists("refs/remotes/origin/sdlc/<id>/a")`, or wraps the `ls-remote` answer in `remembered` | `plugin/state/gitops.py:113-125` (a hit of the current generation is returned without asking); `:44-50` (`ls-remote` counts as read-only, so it never moves the generation) | the audit hook, when the push is a process; a check R51 is missing otherwise: never remember a remote answer, and after an API reservation ask `ls-remote` again rather than `ref_exists` |
| 5 | A build PR merged while another build PR is behind `main` | **stale gate verdict**: PR2's gates (c), (d), (e) and its CI ran on the old base; the owner's merge is Exempt from "require up to date"; the release deploys the untested combination | safe at the offer, **window stays between the (e) offer and the merge**: PR1 merges after PR2's (e) ran; the release check then refuses, which parks production with no route back (reading 2) | `plugin/gate/diff.py:431-446` (the gate diffs against `refs/remotes/origin/<default>` as the checkout fetched it; nothing re-runs on a base move); `plugin/release/cli.py:556-575` (the release reads the gate (e) result, never the base it was judged against) | R51's release check closes the deploy of an untested tree; a check R51 is missing: what the refusal does next (see §5) |
| 6 | Owner clicks "Update branch" after the (e) offer, then merges | **stale gate verdict**: the gate (e) record's `head` (`plugin/gate/gate.py:52-60`) is older than the merged head; the release compares nothing (`release/cli.py:556-575`) | **stale gate verdict still**: R51's release check asks "does the head contain the default branch tip", which the owner's merge commit satisfies, though gate (d)'s deterministic checks never ran on that tree | `plugin/release/cli.py:556-575`; `sdlc-release.yml:102` | a check R51 is missing: the release re-runs the deterministic checks (the three targets, the toolchain is already installed at `sdlc-release.yml:125`) on the merge commit and refuses on red; or refuses when the merged head is not the gate (e) record's head plus the runner's own record commits |
| 7 | A release's `deploy.command` running while the owner merges a second build PR | **two deploys at once**: one group per PR (`sdlc-release.yml:72-74`); the older merge's command can finish last | unchanged: R51 adds no release serialisation | `template/.github/workflows/sdlc-release.yml:72-74` | a check R51 is missing: one repository-wide release group; with GH-queue that drops the middle of three quick merges, so the release must deploy the default branch's tip and record every change whose merge commit it contains, or refuse a merge commit that is no longer `main`'s tip while a newer release is queued |
| 8 | (e) run merges the default branch into `sdlc/<id>/c` while a fix round of the same change runs | n/a (no (e) merge today) | safe: both runs are in `sdlc-sdlc/<id>/c` (GH-queue serialises them) | `sdlc-deploy.yml:62-63`, `sdlc-fix.yml:128-129` | GitHub's concurrency group |
| 9 | Fix round on a PR whose base moved (owner's "Update branch", or R51's (e) merge in the previous run) | safe for the PR's own diff (merge base recomputed per checkout, `diff.py:442`); the deterministic checks run on the branch tree without the new base, so a red that the merge would show is **not seen** until the next gate | safe once R51 re-checks before (e); the fix round itself is still judged on the fetched tree | `plugin/gate/diff.py:431-446`; `sdlc-fix.yml:175-176` (checkout of the head ref at run start) | R51's (e) re-check, if it also runs after a fix round that lands between the offer and the merge (see §5) |
| 10 | Owner pushes to the work branch ("Update branch", a by-hand commit) while a phase or fix run is between its checkout and its push | **conflicting push**: `git push -u origin <branch>` is rejected non-fast-forward; the record is not pushed; the run ends red or parks locally (`run_phase.py:2529` prints and goes on) | unchanged; the R51 (e) run's merge commit is one more push that can be rejected the same way | `plugin/state/gitops.py:457-458` (no fetch, no lease, no retry); `plugin/ci/run_phase.py:2518-2532` | a check R51 is missing: on a rejected push, fetch, merge the remote head of the work branch (never rebase or force), re-run the gate on the merged tree, then push; a second rejection parks |
| 11 | The reservation push lands while a phase run of the same id runs | impossible: the reservation precedes every phase of the id | safe: the reserved ref is the design branch's own start; `commit-phase --start-point origin/<default>` branches from a descendant of (or the same commit as) the reservation, so the first push is a fast-forward | `plugin/detect/cli.py:487-489`; `plugin/state/gitops.py:269-279` | GH-ref; **open on a PC**: `checkout_branch` with no start point branches from the current HEAD (`gitops.py:278-279`), a stale local `main` behind the reservation makes the first push non-fast-forward — a check R51 is missing: `new-change` records the reservation sha and the first `commit-phase` of the id starts from it |
| 12 | Pin-bump PR (R5, root `sdlc.yaml` `plugin.version`) and a session PR touching the manifests merge close together | safe for the pin line: two pin-bump PRs change the same line to different values, the second conflicts and GitHub refuses the merge; **version collision unseen**: two session PRs that bump `plugin.json` to the same version merge clean (identical change on both sides is not a conflict), the tag workflow finds the tag and skips (`sdlc_tag.py:235-239`, `created=false`), the second change is never tagged and the pin-bump never fires for it | unchanged (outside R51's scope, named because the "free to start" line of 2026-10-19 carries the same hazard for decision numbers) | `.github/scripts/sdlc_tag.py:146-148`, `:235-239` | GitHub's conflict detection for the pin line; a check R51 (or R5) is missing: the tag job ends red when the version's tag exists at another commit, and the framework checks refuse a `plugin.json` version that `ls-remote --tags` already knows |
| 13 | A workflow dispatched by the App identity and one by the fallback token, for the same change | safe: both go through `dispatch()` with `head_ref` (`run_phase.py:2727-2760`), so both land in `sdlc-<head_ref>`; the App's own events start no SDLC workflow (`sdlc-test.yml:53-57`, `sdlc-deploy.yml:54-58` filter `[bot]` senders; no workflow listens to `synchronize`) | unchanged | n/a for a duplicate; **GH-queue drops a transition**: two pending runs in one group (an automatic fix round dispatched while a review event's run is pending) and the older pending one is cancelled | GitHub's group for the duplicate; a check R51 is missing for the dropped pending run: the dispatcher re-reads the state it dispatched for at the start of every run, so a cancelled pending run's work is picked up by the one that replaced it (today each run re-reads `status.yaml`, which covers most of it; the automatic fix round's trigger link is the one input only the cancelled run carried) |
| 14 | The App token goes stale at 50 minutes (`app_token.py:87`, `:108-123`) and the (e) run's R51 merge commit is pushed with the workflow token | n/a | **stale gate verdict, if R51 reads check runs**: a push by the workflow token causes no events, so the project's CI never reports on the merge commit; "no check" is not green | `plugin/ci/app_token.py:108-123`; `sdlc-deploy.yml:62-63` | a check R51 is missing: the re-check is the runner's own deterministic checks (gate (d)'s commands step), never the PR's check-run status |
| 15 | Two maintain runs allocate at once | impossible: group `sdlc-detect` | same | `sdlc-detect.yml:65-67` | GitHub's concurrency group |

## 1. Two intents reserve an id at once (rows 1 to 3)

1. Session S and maintain run M both run `new-change`. Each runs `ls-remote --heads origin refs/heads/sdlc/*` (`gitops.py:488`) and sees ids up to 0006; both compute 0007 (`conventions.py:239-245`). Today both write `changes/0007-<slug>/` (`cli.py:55`) and the collision surfaces at the first push of `sdlc/0007/a`, or never, when one of them is a cloud session whose branch is `claude/...` (decision 22).
2. Under R51, S pushes `origin/main@T0:refs/heads/sdlc/0007/a`. M, one second later, pushes `origin/main@T0:refs/heads/sdlc/0007/a` too, because both checkouts fetched the same tip. GH-ref: the ref exists and already holds that object id, so git answers "Everything up-to-date" with exit 0. M reads success and keeps 0007. **Duplicate id.**
3. When M's checkout fetched a later tip (row 2), M's push is rejected and R51's retry takes 0008. Safe, but only if the retry recomputes from a fresh `ls-remote`: `id + 1` collides with a third allocation that saw 0007 taken and took 0008 itself.
4. Row 3: the push fails because the cloud session's remote is read-only, or the network drops. One `GitError` carries every failure (`gitops.py:175-176`). A design that reads "refused" as "taken" walks upward, or ends with a folder on disk whose id is reserved by nobody.

What closes it: reserve by a ref creation that fails when the ref exists in any state — `git push --force-with-lease=refs/heads/sdlc/<id>/a: origin <sha>:refs/heads/sdlc/<id>/a` (an empty expected value means the ref must not exist), or `POST /repos/{repo}/git/refs` and treat 422 as the only refusal; reserve before `status.new_change` creates the folder; bound the retries; distinguish the refusal from every other error.

## 2. The remembered cache and the reservation (row 4)

1. `new-change` asks `remote_change_ids` (`ls-remote`, never remembered) then, under R51, pushes the reservation through `gitops.run` (`subprocess.run`). The audit hook sees `subprocess.Popen` with `git push`, which `_reads_only` rejects (`gitops.py:97`), so `_generation` moves and every remembered answer of the process is asked again. Safe today, and under R51 as proposed.
2. The window opens if the reservation is made through the REST API from the same process: no process starts, the generation stands, and an earlier `ref_exists("refs/remotes/origin/main")` or `origin_head` answer is served from the cache. Neither is wrong (the remote-tracking refs did not change locally), so the only harm is a design that then reads `ref_exists` for the reserved ref and finds the pre-push "no". A design that wraps the `ls-remote` answer in `remembered` (to save a second network call) would serve a pre-reservation list to a second allocation in the same process, which the maintain run performs when several bands breach at once (`detect/cli.py` files one change per record).

What closes it: never remember a remote answer; after an API reservation ask `ls-remote`, not `ref_exists`.

## 3. A build PR merged while another is behind `main` (rows 5, 6, 9)

1. PR1 (`sdlc/0007/c`) and PR2 (`sdlc/0008/c`) both passed (c) and (d) against `main@A`. The owner merges PR1; `main` is now `B`.
2. Today nothing runs on PR2. The owner merges PR2; the release checks out the merge commit (`sdlc-release.yml:102`), reads gate (e)'s result on the merged copy (`release/cli.py:556-575`) and runs `deploy.command`. The tree that deploys was never tested. **Stale gate verdict.**
3. Under R51 the (e) run of PR2 merges `main@B` into `sdlc/0008/c`, re-runs gate (d)'s deterministic checks, and offers gate (e) on the merge commit. The owner merges PR2: safe.
4. The window that stays: the (e) offer of PR2 happened at `main@A`; PR1 merges afterwards; the owner merges PR2. R51's release check finds PR2's head without `B` and refuses. Production now holds `main` with PR2 merged and nothing deployed; the release job cannot park (read-only token), cannot dispatch (no `actions: write`), and the PR is merged, so decision 31's review request has no PR to land on. The proposal says "the spec decides whether the release refuses or re-checks"; neither alone is enough.
5. Row 6 is the same window opened by the owner: "Update branch" after the offer produces a head that contains `main`'s tip, so R51's check passes, while gate (d)'s commands never ran on the merged tree.

What closes it: the release re-runs the three targets on the merge commit (the toolchain step already runs there, `sdlc-release.yml:124-125`) and deploys only on green; on red it ends red with the need printed, and the digest carries it (R20) — a reading, since decision 31 names no notification for a merged PR. The gate (e) offer must be withdrawn (label removed, review request dismissed) by any later push to the work branch or to `main`; the (e) run re-runs on a `push` to the default branch for every open build PR, which the App's identity makes possible (decision 33) and the fallback does not.

## 4. Two deploys at once (row 7)

1. The owner merges PR1; its release starts in group `sdlc-release-<PR1>`. The owner merges PR2 thirty seconds later; its release starts in group `sdlc-release-<PR2>`. Both run `deploy.command`, one on `main@B`, one on `main@C`.
2. Nothing orders their completion. A command that uploads a version (`twine upload`) fails harmlessly on the second; a command that applies a manifest or syncs a bucket leaves whichever finished last. **Lost update** when PR1's finishes last.
3. R51 adds no serialisation. One repository-wide group serialises them, but GH-queue then drops the middle one of three quick merges (its pending run is replaced), and its record job never runs, so its change is never marked released and a later dispatch would release it again on a tip that already carries it.

What closes it: one release group plus a release that deploys the default branch's tip, records every change whose merge commit is an ancestor of that tip, and skips a merge commit that is no longer the tip while a newer release is queued. Decision 13 is kept: the trigger stays the owner's merge; only what is deployed and recorded changes.

## 5. A push rejected under a moved branch (rows 10, 11)

1. A phase run checks out `sdlc/0007/c` at `H1` (`sdlc-fix.yml:175-176`). The owner clicks "Update branch"; the branch is now `H2`, a merge commit over `H1`.
2. The run commits its record on `H1` and runs `git push -u origin sdlc/0007/c` (`gitops.py:457-458`): rejected, non-fast-forward. `run_phase.py:2529-2532` prints "could not be pushed" and goes on; the run's verdict exists only in the runner's checkout. **Conflicting push**, and the next run finds no record of this one.
3. Under R51 the (e) run's own merge commit of the default branch is one more such push; same window, and now on the one push that R51's safety rests on.
4. Row 11: on a PC the reserved `sdlc/0007/a` points at `origin/main@T0`; the owner's first `commit-phase` with no `--start-point` branches from the current HEAD (`gitops.py:278-279`); a local `main` behind `T0` gives a first push that is non-fast-forward against the reservation. The maintain run is safe here because it passes `--start-point` (`detect/cli.py:487-489`).

What closes it: on a rejected push, fetch and merge the remote head of the work branch (a merge commit, as 1.0.10's restart), re-run the gate on the merged tree, push once more; a second rejection parks. `new-change` records the reservation sha and the id's first `commit-phase` starts from it.

## 6. The pending run that GitHub drops (rows 13, 14)

1. Run X of change 0007 is running in `sdlc-sdlc/0007/c`. The owner submits a review (a fix round is queued, pending). Run X ends by dispatching an automatic fix round with a trigger link (decision 34). GH-queue: the new pending run replaces the older pending one, which is cancelled.
2. Both dispatches go through `dispatch()` (`run_phase.py:2727-2760`) whether the App's or the fallback token signs them, so the identity changes nothing here; the loss is GitHub's queue rule. The replacement run re-reads `status.yaml`, so the phase is right; the review's own event is the input that only the cancelled run carried.
3. Row 14: the App token is stale after 50 minutes (`app_token.py:87`, `:108-123`); the (e) run pushes R51's merge commit with the workflow token; no CI runs on it. A re-check that reads the PR's check runs sees nothing and must not read nothing as green.

What closes it: every run re-reads the review threads it answers from GitHub, not from its trigger; the R51 re-check runs the deterministic checks itself.

## The checks R51's proposal is missing

1. **Reservation that fails on an existing ref in any state**: `--force-with-lease=<ref>:` with an empty expected value, or the REST ref creation and its 422; a plain push of the default-branch tip succeeds when another allocation already pushed the same tip.
2. **Reservation before the folder**: reserve before `status.new_change` writes `changes/<id>-<slug>/`; roll nothing back by hand.
3. **A refusal is only git's "exists" / non-fast-forward**: a credential or network failure falls back to today's best-effort id and says so; retries are bounded and recompute from a fresh `ls-remote`.
4. **Never remember a remote answer**; after an API reservation ask `ls-remote`, not `ref_exists`.
5. **The first `commit-phase` of a reserved id starts from the reservation sha** (a PC with a stale local `main` otherwise pushes non-fast-forward against its own reservation).
6. **The (e) update lands before the review pass step**, not only before the gate (e) record.
7. **The re-check is the runner's own deterministic checks**, never the PR's check-run status (a fallback-token push has none).
8. **The offer is withdrawn on every later push** to the work branch or to the default branch (label removed, review request dismissed), and the (e) run re-runs on a push to the default branch for every open build PR when the App identity is present.
9. **The release re-runs the three targets on the merge commit** and deploys only on green; "head contains the default branch tip" alone accepts an owner's "Update branch" that no gate judged.
10. **The release's refusal has a route back**: what is printed, where the owner reads it (the digest, R20), and that the merged change is not lost; decision 31 names no notification for a merged PR, so the spec must.
11. **One release group, deploying the default branch's tip** and recording every change whose merge commit it contains; per-PR groups let two `deploy.command` runs overlap, and a single group with GH-queue drops the middle merge of three.
12. **A rejected push fetches, merges the remote head of the work branch, re-runs the gate and pushes once more**; a second rejection parks. The (e) merge commit is one more push that an owner's "Update branch" can reject.
13. **A replaced pending run's input is re-read by the run that replaced it**: review events from GitHub, not from the trigger.
14. **Outside R51, carried to R5**: the tag job ends red when the version's tag exists at another commit, and the framework checks refuse a `plugin.json` version that `ls-remote --tags` already knows; two session PRs that bump to the same version merge clean today.

## Not verified

- GH-ref's "same object id is up to date" was read from git's receive-pack semantics, not reproduced against GitHub in this session.
- GH-queue's "the newer pending run replaces the older" is GitHub's documented concurrency rule; not reproduced here.
- That the release job cannot dispatch was read from its `permissions:` block (`sdlc-release.yml:66-69`), not tried.
