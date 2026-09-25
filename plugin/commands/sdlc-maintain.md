---
description: Phase (f) maintain — the diagnosis of a control-band breach the deterministic detection script filed (or, by hand, run the detection first), read-only on source, from the project's lessons and the failed runs, written as an incident intent.md with its Evidence section and a proposed route (the intent PR itself, or at 3σ a listed runbook), dispatched through the route's authorization (pre-approved runs now; go parks with "Go" requested), then gate (f): the intent PR opens with sdlc:f-ready and incident and waits for the owner's triage — merge (fix now), label schedule, or close with a reason (dismiss). Re-runnable.
argument-hint: [change id, e.g. 0007; empty = run the detection first]
disable-model-invocation: true
allowed-tools: Bash(python "${CLAUDE_PLUGIN_ROOT}/plugin/state/cli.py" *), Bash(python "${CLAUDE_PLUGIN_ROOT}/plugin/gate/cli.py" *), Bash(python "${CLAUDE_PLUGIN_ROOT}/plugin/detect/cli.py" *), Bash(python "${CLAUDE_PLUGIN_ROOT}/plugin/pr/cli.py" *), Bash(git *), Bash(gh run view *), Bash(gh run list *), Read, Glob, Grep, Write
---

# /sdlc-maintain — phase (f)

Source: build guide step 37 (article p.42–45: "A deterministic script watches production and
invokes Claude when a control band is breached"; step 3: "At 1σ the script only logs, at 2σ
it invokes Claude read-only to diagnose, and at 3σ Claude may act, though only by opening a
PR into the review gate or triggering a pre-approved runbook"; step 5: "The agent writes its
diagnosis as intent.md in the Stage 1: Plan format, covering the anomaly and its evidence, a
proposed outcome, the affected systems and any open questions"), step 36 (the lessons file
the diagnosis reads first, p.49), step 39 (gate (f) is the owner's triage of the incident PR,
decision 25), decisions 14 and 26 (routes split by blast radius; a rehearsed rollback on a
declared production is pre-approved), decision 15 (the first metric is CI test failure rate).

Unattended: never ask the owner; a route that needs a person parks with "Go" requested.
Read-only on source: this run never edits a file outside `changes/<id>-<slug>/` (the gate's
`design_scope` check refuses the commit otherwise); a runbook works on a branch of its own
and opens a pull request the review gate decides on (p.45). Detection itself has no model
in it: it ran before this command and its record is what you read.
One shell command per Bash call (an unattended run denies a chained command whole).

## 0. Preconditions
- With no `$ARGUMENTS`, run the detection first (by hand; in CI the detect workflow did):
  `python "${CLAUDE_PLUGIN_ROOT}/plugin/detect/cli.py" run --root "${CLAUDE_PROJECT_DIR}" --file --log detect-log.jsonl`
  It prints the verdict and `outcome`: `logged` (tier 0 or 1: nothing to do — report the
  line and stop), a dismissed or already-open finding (stop and report it), or
  `filed change <id>` — continue with that id.
- `python "${CLAUDE_PLUGIN_ROOT}/plugin/state/cli.py" show --root "${CLAUDE_PROJECT_DIR}" --id <id>`:
  `entry_route` is `incident`, the phase is `f` (a change at another phase is not this
  command's: stop and say so); `git fetch origin`, `git switch sdlc/<id>/a`,
  `git pull --ff-only origin sdlc/<id>/a` (the filing step created the branch).
- `python "${CLAUDE_PLUGIN_ROOT}/plugin/gate/cli.py" start-run --root "${CLAUDE_PROJECT_DIR}" --id <id> --phase f`
- Load the `intent-template` skill (the incident shape with its Evidence section).

## 1. Read before you diagnose (build guide step 36; article p.49)
1. `changes/<id>-<slug>/evidence/detection.json` — the finding: metric, tier, the rule that
   fired, mean and sigma of the baseline, the latest observation and the tail, the failed
   runs' URLs, the default branch's commits in the breach window, and `forced` (a
   rehearsal). It is the record; never edit it.
2. Every file under `lessons/` (start with `lessons/README.md`): the post-mortems of earlier
   incidents. A second incident of a class is cheaper than the first only if you read the
   first; cite the lesson you relied on in the intent's Evidence section.
3. `python "${CLAUDE_PLUGIN_ROOT}/plugin/detect/cli.py" routes --root "${CLAUDE_PROJECT_DIR}" --id <id>`
   — the routes you may propose at this tier, their resolved authorization, the arguments
   each runbook takes, and which are unsupported for this project's language.

## 2. Investigate, read-only (p.43 step 3, 2σ "invokes Claude read-only to diagnose")
Use only the tools the bands allow plus Read/Grep/Glob: `gh run view <run id> --log-failed`
on the failed runs the record lists (at most five, newest first), the tests and modules
those logs name, `git log` over the commits in the breach window. Do not run the test
suite, do not edit source, do not fix anything: the fix is a change of its own that starts
at gate (a) when the owner merges this intent. Rule things out explicitly; what you could
not determine is an open question.

## 3. Write the incident intent (skill `intent-template`)
`changes/<id>-<slug>/intent.md` with `Entry route: incident <signature>` (the signature is
in the record), `Status: proposed` (there is no owner to correct it here; the intent PR's
review comments are the correction, `/sdlc-fix`), the five sections and `## Evidence` — the
anomaly (metric, tier, rule, the numbers), when it started, where the evidence lives (the
run URLs, the log lines you read), what was ruled out, the lesson you relied on. The
Proposed outcome is the fix or the mitigation, not the diagnosis (the skill's rule); an
unknown cause is written as such with the first thing to check under Open questions.

## 4. Propose the route (decision 14; article p.43 step 3)
Write `changes/<id>-<slug>/evidence/proposal.json` in the shape `routes` printed:
`{"schema_version": 1, "tier": <the record's tier>, "route": "...", "args": {...},
"rationale": "..."}`.
- Tier 2: the route is `pull_request` — this intent PR is the diagnosis's whole output.
- Tier 3: `pull_request` when no runbook fits, else one listed runbook with its arguments:
  `runbook:quarantine-flaky-test` with `{"test": "<pytest node id>"}` when the evidence shows
  one test failing intermittently with no code change behind it; `runbook:revert-pr` with
  `{"sha": "<full sha>"}` when one commit in the breach window (the record lists them)
  introduced the failures; a project runbook by its name when the incident is what it was
  written for. Never propose a route `routes` did not list, and never an unsupported one.
The rationale says why this route and what was ruled out. A `go` route may be proposed
when it is the right action: the dispatcher parks the PR with "Go" requested and the owner's
`sdlc:go` label runs it (`sdlc-runbook.yml`); do not propose a weaker route to avoid the
wait.

## 5. Commit the diagnosis
`python "${CLAUDE_PLUGIN_ROOT}/plugin/state/cli.py" commit-phase --root "${CLAUDE_PROJECT_DIR}" --id <id> --phase f --message "maintain(<id>): diagnosis" --push`
(only the change folder is committed; `--phase f` commits on `sdlc/<id>/a`).
**When `$ARGUMENTS` carries `--diagnosis-only` (the CI runner passes it), stop here** and
report the commit: the workflow's next step (`detect/cli.py finish`, with the project's
runbook secrets in its own environment and none in this session's) dispatches the route,
runs gate (f), commits the evidence and opens the PR. Steps 6–8 are the by-hand run's.

## 6. Dispatch the route (deterministic; decisions 14 and 26)
`python "${CLAUDE_PLUGIN_ROOT}/plugin/detect/cli.py" dispatch --root "${CLAUDE_PROJECT_DIR}" --id <id> --commit`
It validates the proposal against the tier and the **default branch's** `bands.yaml` and
`sdlc.yaml` (never the checkout's: an edit in this session changes no authorization,
decision 14), resolves the authorization (the bands' value; a stricter `go` in
`sdlc.yaml: maintain.runbooks` wins; a rollback runbook with `rehearsed_at` set on a project
with `deploy.production: true` is pre-approved, decision 26; a forced finding — a rehearsal —
never pre-approves a runbook), and acts: a pre-approved runbook runs now (its branch, its pull request, the
record `evidence/runbook-<name>.json` with `status: ran`), a `go` route records
`go-requested`, `pull_request` records nothing. `--commit` commits the record on the
branch. Read its JSON; a rejected proposal (`acted: false` with a reason) is fixed by
rewriting `proposal.json` once (a listed route, the right arguments) and re-running steps
5 and 6; a second rejection stays and the gate parks with the reason.

## 7. Gate (f)
`python "${CLAUDE_PLUGIN_ROOT}/plugin/gate/cli.py" check --root "${CLAUDE_PROJECT_DIR}" --id <id> --phase f`
— the intent in its incident shape, nothing committed outside the change folder, the
guardrails and the risk list, the finding (tier 2 or 3, not dismissed) and the route (listed
for the tier; a runbook that ran; `go-requested` parks with "apply `sdlc:go`"). Exit 3
`wait` is the normal outcome (gate (f) is human in every profile); 4 = `park`. Then commit
the evidence:
`python "${CLAUDE_PLUGIN_ROOT}/plugin/state/cli.py" commit-phase --root "${CLAUDE_PROJECT_DIR}" --id <id> --phase f --message "maintain(<id>): gate (f) evidence" --push`
The change stays at phase `f` on its branch: your merge of the intent PR is gate (a) of
this change (decision 25) and the design workflow reads a merged change at `f` as at `a`.

## 8. Open the intent PR (the triage queue, build guide step 39)
`python "${CLAUDE_PLUGIN_ROOT}/plugin/pr/cli.py" upsert --root "${CLAUDE_PROJECT_DIR}" --id <id> --phase f`
— head `sdlc/<id>/a`, title `maintain(<id>): <title>`, the summary (the finding, the
proposed outcome, the route and its state, what needs the owner), labels `sdlc:f-ready` (or
`sdlc:needs-human` with "What I need from you": Go requested, or a failed check) and
`incident`. Nothing merges, nothing deploys, nobody is notified.

## 9. Report
One line: the PR URL and "gate (f): merge = fix now (the design run starts); label
`schedule` = later; close with a comment = dismiss (the comment is the reason, recorded by
the abandon workflow in a dismissal PR)". When a route waits for Go, add "apply `sdlc:go`
on the PR to run runbook <name>". Do not start phase (b).

Never edit `.claude/**`, `CLAUDE.md`, `REVIEW.md`, `sdlc.yaml`, `bands.yaml` (a bands change
is the owner's PR) or `evidence/detection.json`. Never edit source. Never use
bypass-permissions mode. Never notify anyone. Never merge.
