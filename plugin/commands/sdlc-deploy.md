---
description: Phase (e) deploy — the review passes in a fresh context with REVIEW.md (bugs, security, compliance) into evidence/review-findings.json, a fix loop bounded by the iteration cap while an Important finding stands, the regenerated PR summary, then gate (e): the build PR is marked ready with sdlc:e-ready and waits for the owner's merge in every profile. The release is prepared in the PR per the project's deploy adapter (release notes, nothing executed); the release workflow runs it on the owner's merge. Re-runnable.
argument-hint: [change id, e.g. 0001]
disable-model-invocation: true
allowed-tools: Bash(python "${CLAUDE_PLUGIN_ROOT}/plugin/state/cli.py" *), Bash(python "${CLAUDE_PLUGIN_ROOT}/plugin/gate/cli.py" *), Bash(python "${CLAUDE_PLUGIN_ROOT}/plugin/panel/cli.py" *), Bash(python "${CLAUDE_PLUGIN_ROOT}/plugin/evidence/collect.py" *), Bash(python "${CLAUDE_PLUGIN_ROOT}/plugin/review/cli.py" *), Bash(python "${CLAUDE_PLUGIN_ROOT}/plugin/pr/cli.py" *), Bash(python "${CLAUDE_PLUGIN_ROOT}/plugin/release/notes.py" *), Bash(git *), Bash(gh *), Read, Glob, Grep, Edit, Write, Agent
---

# /sdlc-deploy — phase (e)

Source: build guide step 24 (composition: OPERATING_MODEL §4.1), step 26 (REVIEW.md and
the review passes, article p.32–35: "Bugs · Security · Compliance", Important vs nit, "at
most five nits"; decision 12: the review pass runs in a fresh context, writer ≠ judge),
step 27a (the PR summary), step 32 (release prepared), decision 13 (gate (e) = the owner's
merge; the release label only when `sdlc.yaml` declares a real production), decision 19
(what deploy means for a project that is not a service).

Unattended: never ask the owner; a blocker parks. The owner's merge is the only human
action in this phase; nothing is deployed here: the release is prepared in the PR and the
release workflow runs it after the merge (article p.32: "The agent does everything up to
the production gate and nothing past it").
One shell command per Bash call: an unattended run allows only an explicit list of
command prefixes (`git *`, `python *` and a few more, per phase: `plugin/ci/run_phase.py`
and this command's `allowed-tools`), Claude Code checks each part of a chained command
against that list on its own, and a chain with one part the list does not cover is denied
whole, so the step it carried is lost (the first `/sdlc-fix` run of 2026-09-23 lost its
final commit to `cd ... && python ...`).

## 0. Preconditions
- Change id `$ARGUMENTS` (or the single change whose `status.phase` is `d` with gate
  `passed` — Full profile: also labelled `sdlc:d-approved`).
- `python "${CLAUDE_PLUGIN_ROOT}/plugin/gate/preflight.py" --root "${CLAUDE_PROJECT_DIR}" --id <id> --phase e`:
  if `allow` is false, stop and report its `reasons` (a `parked: ...` reason is the
  owner's item). Never judge `status.yaml` yourself.
- `git fetch origin`, `git switch sdlc/<id>/c`, `git pull --ff-only origin sdlc/<id>/c`.
- `python "${CLAUDE_PLUGIN_ROOT}/plugin/gate/cli.py" start-run --root "${CLAUDE_PROJECT_DIR}" --id <id> --phase e`
- `python "${CLAUDE_PLUGIN_ROOT}/plugin/state/cli.py" set-phase --root "${CLAUDE_PROJECT_DIR}" --id <id> --phase e`

## 0a. Prepare the release artifact (build guide step 32; decisions 13, 19)
Article p.32: "The agent does everything up to the production gate and nothing past it."
Nothing here uploads, schedules, promotes or deploys anything. It runs before the review,
so the review pass and the gate judge HEAD with the artifact in it (the fix loop's own
re-review covers later commits). Per `sdlc.yaml: deploy.action`:
- `publish package` → the build artifact built and the version bump proposed in the PR;
  nothing uploaded.
- `regenerate report` → the report regenerated into the PR.
- `schedule job` → the schedule entry or cron change proposed in the PR; nothing scheduled.
- `promote to paper trading` → the promotion record proposed in the PR; nothing promoted.
- `deploy service` → the deploy manifest or changelog prepared in the PR; nothing deployed.
- `none` → nothing; skip the commit.
A release artifact outside the change folder (a version bump, a regenerated report, a
schedule entry, a manifest) is a departure from `plan.md` unless the plan lists it, so list
it under "## Files that change" of `plan.md` in the same commit (the plan-sync rule of
`commit-phase`). Commit and push (a re-run with the artifact already committed has nothing
to commit):
`python "${CLAUDE_PLUGIN_ROOT}/plugin/state/cli.py" commit-phase --root "${CLAUDE_PROJECT_DIR}" --id <id> --phase e --message "release(<id>): release prepared" --paths <files> --push`
(`--paths` names the artifact files and `plan.md` is in the change folder).

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
   commit as the code). A finding you believe wrong, or whose fix the run cannot make (a
   guardrail file, a `CLAUDE.md` line — `review/cli.py validate` already proposes that line
   in the PR body), is not fixed silently: under `review: parked` leave it and note why in
   `evidence/review-response.md` (the owner decides at the gate); under `review: deferred`
   it is a panel item of the deferred-review step below, which may settle it (`settled: ...`) so the gate passes
   with the finding recorded.
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

### Deferred review — the panel settles the judgment items (decision 21; build guide step 16a)
```
python "${CLAUDE_PLUGIN_ROOT}/plugin/panel/cli.py" items --root "${CLAUDE_PROJECT_DIR}" --id <id> --phase e
```
It prints the review mode (`sdlc.yaml: review`, `status.yaml: review_override`), the items
the gate would park on that belong to the panel's fixed list (an open flagged concern, a
concern naming contradicting policies, the reviewer's `escalate` verdict, an Important
finding the run cannot fix, the verifier's "does not match the plan"), which of them the
ledger already decides, and under `parks` what stays the owner's whatever the mode (a
risk-list hit, a guardrail file, a run limit, an infrastructure failure). When `mode` is
`parked` or `pending` is empty, go on to the gate. Otherwise, for each pending item `n` in
order, three fresh contexts, each with the brief printed by
`python "${CLAUDE_PLUGIN_ROOT}/plugin/panel/cli.py" prompt --root "${CLAUDE_PROJECT_DIR}" --id <id> --phase e --item <n> --member <reviewer|advocate|conciliator>`:
1. **reviewer** — delegate to a general-purpose sub-agent with the `reviewer` brief; it
   writes `evidence/panel/e-<n>-reviewer.md`.
2. **devil's advocate** — delegate to `sdlc:adversarial-reviewer` with the `advocate`
   brief, on the model `sdlc.yaml: panel_advocate_model` names (pass it as the sub-agent's
   model: the per-invocation model wins, NOTES §11c; a panel on one model shares its blind
   spots), blind to the reviewer's file; it writes `evidence/panel/e-<n>-advocate.md`.
3. **conciliator** — delegate to a general-purpose sub-agent with the `conciliator` brief;
   it reads both files and writes `evidence/panel/e-<n>-conciliator.json`.
Then record it:
`python "${CLAUDE_PLUGIN_ROOT}/plugin/panel/cli.py" record --root "${CLAUDE_PROJECT_DIR}" --id <id> --phase e --item <n>`
— one panel call is one iteration (exit 3 at the cap: stop the panel, the gate parks); it
appends the line to `evidence/decisions-e.json` (and the `.md` the owner reads), and for
a concern closes the item in `spec.md` as `decided (by panel): <decision> — <concern>`. Apply
what the decision asks beyond that (an `escalate` decided `continue` needs nothing more; a
fix the decision names is made now, `plan.md` in the same commit). When any file changed,
commit (`commit-phase ... --phase e --message "review(<id>): panel decisions"`),
then re-run step 1's `validate` for the new HEAD (a verdict never outlives the diff it
judged); an `escalate` with new reasons is a new item: run `items` once more. The panel
never decides a park item, never raises a limit, never touches a guardrail file, and never
asks the owner: the owner reads "Decisions taken for you" at the gate and overturns any
line with a review comment.

## 4. Gate (e)
`python "${CLAUDE_PLUGIN_ROOT}/plugin/gate/cli.py" check --root "${CLAUDE_PROJECT_DIR}" --id <id> --phase e`
— requires the evidence of (d) green, `review-findings.json` for HEAD with no Important
finding, the plan in sync with the diff, no guardrail or risk hit. Exit 3 `wait` is the
normal outcome (gate (e) is human in every profile); 4 = `park`. Then the release notes
(build guide step 32; deterministic: what changed, the commits since the base, the evidence
status, the final findings tally, the links):
```
python "${CLAUDE_PLUGIN_ROOT}/plugin/release/notes.py" --root "${CLAUDE_PROJECT_DIR}" --id <id> --write
```
It writes `changes/<id>-<slug>/evidence/release-notes.md`, which rides in the evidence
commit (evidence is committed after the gate, OPERATING_MODEL §4.1, so no re-review):
`python "${CLAUDE_PLUGIN_ROOT}/plugin/state/cli.py" commit-phase --root "${CLAUDE_PROJECT_DIR}" --id <id> --phase e --message "review(<id>): gate (e) evidence" --push`.
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
(first-pass merge, fix iterations), the proposed `CLAUDE.md` lines, and the
"## Release note" section quoted from `evidence/release-notes.md`. Label: `sdlc:e-ready`,
or `sdlc:needs-human` when parked. The PR is waiting for your merge: merge = gate (e)
passed; the release workflow then runs `deploy.command`. When `sdlc.yaml` says
`deploy.production: true`, the body also says: the release label `sdlc:release-approved` is
the second act: apply it on this PR after merging; the release workflow waits for it.

## 6. Hand over
Report the PR URL and "gate (e): merge = approve; a review comment is the change request
(`/sdlc-fix <id>`)". When `sdlc.yaml` says `deploy.production: true`, add "the release
label `sdlc:release-approved` is the second act: apply it on this PR after merging; the
release workflow waits for it". Nothing else runs;
the owner's merge is the trigger for the project's deploy adapter.

Never edit `.claude/**`, `CLAUDE.md`, `REVIEW.md`, `sdlc.yaml`, `intent.md` or `spec.md`.
Never use bypass-permissions mode. Never notify anyone. Never merge.
