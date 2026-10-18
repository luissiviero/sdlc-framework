# Progress — the pipeline sprint, part 1: R17 (decision 34) as plugin **1.0.5**, R46 (decision 30) as plugin **1.0.6**, and the owner's choices 214 to 217 (2026-10-17 to 2026-10-18)

This session ran on branch `ccr-4900ade8-1qc1s9`, from the starting prompt `docs/handoffs/2026-10-17-pipeline-sprint-prompt.md`. The previous record (1.0.4 and choices 203 to 213) is now `docs/progress/2026-10-17-1.0.4-and-choices-203-213.md`, unchanged. Both repositories were in scope; the sample was changed only by the owner's merges of the probe PRs #64 and #65. The session's own file is `docs/handoffs/sessions/2026-10-18-ccr-4900ade8-1qc1s9.md`.

## Summary
- **Decision 34** (PR #225, `docs/decisions/34.md`): the owner's `@claude` comment starts a fix round, and only the owner's account starts a round or approves (c) and (d). It amends 22 and 27. The owner updated `CLAUDE.md`'s count to 34 in PR #226.
- **The live check of an `issue_comment` run** (NOTES §46, sample PRs #64 and #65), verified:
  - the run uses the default branch's workflow file and commit;
  - the owner's comment arrives as `OWNER`;
  - the payload has no PR head;
  - the token holds the job's `permissions:` block;
  - a `workflow_dispatch` sent with it starts a run;
  - a refused comment still creates a skipped run.

  The fork token was not verified.
- **R17 as plugin 1.0.5** (PR #227, `56896c5`, `v1.0.5`):
  - `is_owner_actor`;
  - the dispatcher `sdlc-comment.yml` with `comment_dispatch.py`;
  - the owner-only "Request changes" path and (c)/(d) labels;
  - the `trigger` input;
  - the `applied` carry-forward;
  - the optional `sdlc.yaml: owner` key.

  One review round (four should-fix findings, all fixed) and one re-review (one low finding, fixed).
- **R46 as plugin 1.0.6** (PR #228):
  - the owner's own intent PR starts the design on a branch cut from its head;
  - a routine design continues to a build stacked on the design head;
  - the recorded commits are the approved base while unmerged;
  - superseded PRs are labelled and closed with no comment;
  - every profile but Full.

  Three review rounds: 2 blocking and 8 should-fix findings, then 3 should-fix findings, then none. Every fix has a test that fails without it. Full suite 1901 passed at `3121fdb`; CI green on `630ffea`.

## The owner's decisions (2026-10-17)
214. **The live `issue_comment` check runs on the sample before R17's spec** (the session's recommendation, "Go ahead"), with two owner merges: the probe (#64) and its removal (#65).
215. **R46's gate (a) is stacked on the intent PR**: an intent PR the owner's account opens starts the design at once, cut from its head; the intent PR is closed as superseded once the design PR exists.
216. **R46's gate (b) is a stacked build**: a routine design continues to a build cut from the design head, the commit gate (b) passed on being the approved copy; the owner sees intent, spec, plan and code in one (e) PR.
217. **The fast lane applies to every existing profile but Full** ("Not full profile, but any other existing profile").
218. **The three un-park labels count only from the owner's account** (2026-10-18, option A of the session's table: "A, record it for the next session"). `sdlc:accept-risk`, `sdlc:reset-iterations` and `sdlc:unlock-tests` are judged by R17's `is_owner_actor`, fail closed, with a coarse `[bot]`-sender condition in `sdlc-fix.yml`'s `if:`. A by-hand `workflow_dispatch` stays as it is: it needs write access, and the runner's own automatic rounds use it. This makes the code match decision 24's own wording ("the owner's un-park verbs"), so no new decision file is written; decision 24 gets a note beside it when the change is built. It is built in the fix-round robustness PR (choice 204), which already touches `sdlc-fix.yml` and `state/unpark.py`, with a test that fails on the old code.

## Proposed edit for the owner
Carried from `docs/progress/2026-10-17-1.0.4-and-choices-203-213.md` (choice 208); not yet applied (`grep -n 'skip marker' REVIEW.md` finds nothing on `main` at `56896c5`).

| File | Line | What is there now | What it must become |
|---|---|---|---|
| [`REVIEW.md`](https://github.com/luissiviero/sdlc-framework/blob/main/REVIEW.md#L26) | after 26 (the end of the `plan.md` bullet) | nothing; line 27 starts "- The second occurrence of the same finding …" | `- Each added skip marker the gate's \`ratchets\` check listed at gate (e) (\`evidence/gate-e.json\`'s \`details.skip_markers\`) must be declared in \`plan.md\` or explained in the PR; an undeclared one quietly narrowing what the suite actually runs is non-compliant.` (the same bullet `template/REVIEW.md:27-30` carries since 1.0.2) |

## Left
- **The un-park labels** (`sdlc:accept-risk`, `sdlc:reset-iterations`, `sdlc:unlock-tests`) and a by-hand `workflow_dispatch` still start a fix round from any member: decision 34 covers the review and comment paths only. The owner decides whether to narrow them too. *[2026-10-18: decided by choice 218, the labels narrowed to the owner's account in the fix-round robustness PR; the by-hand dispatch stays.]*
- **R17's known limit:** on an organization repository a member's "Request changes" review still enters the fix workflow's concurrency group (the `if:` cannot read `sdlc.yaml`).
- **R46's known limits:**
  - the session writes `gate-b.json` and the verdict file (the same trust as (c)/(d), bounded by the runner's confirmation and the post-gate diff check);
  - commits pushed to the intent PR after the design started are not picked up;
  - a draft marked ready later keeps gate (a);
  - the round-3 nits: a red run after an owner close mid-session, the optional tightening of a lookup that fails open, a demotion push that fails, and a park before the R1 check that still opens a PR.
- **This repository's own pin is 0.3.6**, so neither R17 nor R46 runs here until the pin moves. The root `sdlc-design.yml` passes R46's start point through `env:`, so 0.3.6 ignores it.

## Checks (this repository)
On #228's final head, after `python -m pip install -e ".[dev]"`, chained with `set -o pipefail`: the four commands of `HANDOFF.md`'s standing precondition 1. Their output is in the PR.
