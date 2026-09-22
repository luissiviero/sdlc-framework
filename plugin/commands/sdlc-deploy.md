---
description: Phase (e) deploy — the review passes in a fresh context with REVIEW.md (bugs, security, compliance) into evidence/review-findings.json, a fix loop bounded by the iteration cap while an Important finding stands, the regenerated PR summary, then gate (e): the build PR is marked ready with sdlc:e-ready and waits for the owner's merge in every profile. The release itself (deploy adapter, production gate) is B4. Re-runnable.
argument-hint: [change id, e.g. 0001]
disable-model-invocation: true
allowed-tools: Bash(python "${CLAUDE_PLUGIN_ROOT}/plugin/state/cli.py" *), Bash(python "${CLAUDE_PLUGIN_ROOT}/plugin/gate/cli.py" *), Bash(python "${CLAUDE_PLUGIN_ROOT}/plugin/evidence/collect.py" *), Bash(python "${CLAUDE_PLUGIN_ROOT}/plugin/review/cli.py" *), Bash(python "${CLAUDE_PLUGIN_ROOT}/plugin/pr/cli.py" *), Bash(git *), Bash(gh *), Read, Glob, Grep, Edit, Write, Agent
---

# /sdlc-deploy — phase (e)

Source: build guide step 24 (composition: OPERATING_MODEL §4.1), step 26 (REVIEW.md and
the review passes, article p.32–35: "Bugs · Security · Compliance", Important vs nit, "at
most five nits"; decision 12: the review pass runs in a fresh context, writer ≠ judge),
step 27a (the PR summary), decision 13 (gate (e) = the owner's merge; the release label
only when `sdlc.yaml` declares a real production, B4).

Unattended: never ask the owner; a blocker parks. The owner's merge is the only human
action in this phase; nothing is deployed here (steps 29 and 32 are B4).

## 0. Preconditions
- Change id `$ARGUMENTS` (or the single change whose `status.phase` is `d` with gate
  `passed` — Full profile: also labelled `sdlc:d-approved`).
- `python "${CLAUDE_PLUGIN_ROOT}/plugin/gate/preflight.py" --root "${CLAUDE_PROJECT_DIR}" --id <id> --phase e`:
  if `allow` is false, stop and report its `reasons` (a `parked: ...` reason is the
  owner's item). Never judge `status.yaml` yourself.
- `git fetch origin`, `git switch sdlc/<id>/c`, `git pull --ff-only origin sdlc/<id>/c`.
- `python "${CLAUDE_PLUGIN_ROOT}/plugin/gate/cli.py" start-run --root "${CLAUDE_PROJECT_DIR}" --id <id> --phase e`
- `python "${CLAUDE_PLUGIN_ROOT}/plugin/state/cli.py" set-phase --root "${CLAUDE_PROJECT_DIR}" --id <id> --phase e`

## 1. Review passes in a fresh context (build guide step 26; article p.33–34)
If `changes/<id>-<slug>/evidence/review-findings.json` already exists for HEAD (the
merge-triggered workflow runs the review as its own `claude -p` job first), run only the
`validate` command below and skip the delegation.
The reviewer must not be the context that wrote the code. In the merge-triggered workflow
the review is its own `claude -p` job (`plugin/review/`); by hand, delegate to a
general-purpose sub-agent in a fresh context with this brief: the project root, the change
id, `REVIEW.md`, the review prompt printed by
```
python "${CLAUDE_PLUGIN_ROOT}/plugin/review/cli.py" prompt --root "${CLAUDE_PROJECT_DIR}" --id <id>
```
and the instruction to write `changes/<id>-<slug>/evidence/review-findings.json` in the
recorded shape (`schema_version`, `head` = `git rev-parse HEAD`, `findings[]` with `pass`,
`severity` `important|nit`, `file`, `line`, `summary`, `signature`; `tally`). Then validate
it and compute the tally:
```
python "${CLAUDE_PLUGIN_ROOT}/plugin/review/cli.py" validate --root "${CLAUDE_PROJECT_DIR}" --id <id>
```
A malformed or stale file (wrong `head`) is re-requested from the reviewer once; then park.

## 2. Fix loop while an Important finding stands (article p.34 step 5: "babysit to green")
While `tally.important` > 0:
1. `python "${CLAUDE_PLUGIN_ROOT}/plugin/gate/cli.py" bump-iteration --root "${CLAUDE_PROJECT_DIR}" --id <id>`;
   at the cap stop and go to step 4 (the gate parks with the findings listed).
2. Fix each Important finding in the code (a fix-type change never touches the locked
   tests; a compliance finding about `plan.md` is fixed by updating `plan.md` in the same
   commit as the code). A finding you believe wrong is not fixed silently: leave it and
   note why in `evidence/review-response.md`; the owner decides at the gate.
3. Re-collect the evidence (`evidence/collect.py`), commit
   (`commit-phase ... --phase e --message "review(<id>): fix <finding>" --paths <files>`),
   push, and re-run step 1 for a fresh verdict on the new HEAD.
Nits are not fixed in this loop; the reviewer lists at most five and the owner reads them.

## 3. Second-occurrence rule (article p.35; REVIEW.md "Framework rules")
`review/cli.py validate` compares each finding's `signature` with
`changes/.review-seen.json` (the project's record of past findings). For every finding seen
before, it prints the one-line `CLAUDE.md` entry to propose under "Things Claude gets
wrong". Put those lines in the PR description's "Proposed CLAUDE.md lines" block; never
edit `CLAUDE.md` yourself (protected path: the owner applies the line in the PR review).

## 4. Gate (e)
`python "${CLAUDE_PLUGIN_ROOT}/plugin/gate/cli.py" check --root "${CLAUDE_PROJECT_DIR}" --id <id> --phase e`
— requires the evidence of (d) green, `review-findings.json` for HEAD with no Important
finding, the plan in sync with the diff, no guardrail or risk hit. Exit 3 `wait` is the
normal outcome (gate (e) is human in every profile); 4 = `park`. Commit:
`commit-phase ... --phase e --message "review(<id>): gate (e) evidence" --push`.
In CI (a token is present), publish the review tally as a check run:
`python "${CLAUDE_PLUGIN_ROOT}/plugin/review/cli.py" check-run --root "${CLAUDE_PROJECT_DIR}" --id <id> --phase e`
(route "none" by hand; nothing else changes).

## 5. Mark the PR ready with the final summary (build guide step 27a, decision 20)
```
python "${CLAUDE_PLUGIN_ROOT}/plugin/pr/cli.py" upsert --root "${CLAUDE_PROJECT_DIR}" --id <id> --phase e --ready
```
The description opens with the ≤5 bullets (what changed and why · evidence status ·
findings by severity with the nits listed · plan conformance · what needs the owner: merge
= approve, review comments = `/sdlc-fix`), the two counters of build guide step 42
(first-pass merge, fix iterations), the proposed `CLAUDE.md` lines, and the release note
paragraph (what a user of the project would read). Label: `sdlc:e-ready`, or
`sdlc:needs-human` when parked.

## 6. Hand over
Report the PR URL and "gate (e): merge = approve; a review comment is the change request
(`/sdlc-fix <id>`)". When `sdlc.yaml` says `deploy.production: true`, add "the release label
and the production gate are B4". Nothing else runs; the owner's merge is the trigger for
the project's deploy adapter.

Never edit `.claude/**`, `CLAUDE.md`, `REVIEW.md`, `sdlc.yaml`, `intent.md` or `spec.md`.
Never use bypass-permissions mode. Never notify anyone. Never merge.
