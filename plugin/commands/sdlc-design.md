---
description: Phase (b) design — from the merged intent, write spec.md with the policy skills loaded (the article's p.14 prompt), then the read-only planning run that writes plan.md, run the adversarial reviewer and call gate (b). Under review: deferred, the panel settles open concerns before the gate. Open the spec+plan PR on sdlc/<id>/b with sdlc:b-ready. Re-runnable after review comments. No questions to the owner; a gap becomes a flagged concern.
argument-hint: [change id, e.g. 0001]
disable-model-invocation: true
allowed-tools: Bash(python "${CLAUDE_PLUGIN_ROOT}/plugin/state/cli.py" *), Bash(python "${CLAUDE_PLUGIN_ROOT}/plugin/gate/cli.py" *), Bash(python "${CLAUDE_PLUGIN_ROOT}/plugin/panel/cli.py" *), Bash(python "${CLAUDE_PLUGIN_ROOT}/plugin/pr/cli.py" *), Bash(git *), Bash(gh *), Read, Glob, Grep, Edit(changes/**), Write, Agent
---

# /sdlc-design — phase (b)

Source: build guide steps 22–23 (article p.13–14: the design prompt and its automation
ladder "by hand → slash command → merge-triggered job"; p.14 governance: "the spec, the
prompt that produced it, and the skill versions in force are all logged in version
control"), step 12 and decision 2 (plan.md by a read-only run at the end of phase (b)),
decision 18 (profiles). Prompt version: **v1** (the spec header records it).

This phase runs unattended: by hand or from the merge-triggered workflow.
**Never ask the owner anything.** The merged intent.md is the owner's answer; anything it
leaves open becomes a carried-forward question or a flagged concern the owner reads at the
gate. Never edit intent.md (accepted at gate (a); the gate parks a branch that changes it).
Never edit source: the only files this phase writes are under `changes/<id>-<slug>/`
(decision 2; the gate's `design_scope` check parks anything else).
One shell command per Bash call: an unattended run allows only an explicit list of
command prefixes (`git *`, `python *` and a few more, per phase: `plugin/ci/run_phase.py`
and this command's `allowed-tools`), Claude Code checks each part of a chained command
against that list on its own, and a chain with one part the list does not cover is denied
whole, so the step it carried is lost (the first `/sdlc-fix` run of 2026-09-23 lost its
final commit to `cd ... && python ...`).

## 0. Preconditions
- `sdlc.yaml` exists at the project root; otherwise stop and say `/sdlc-init` is missing.
- Change id: `$ARGUMENTS` is the four-digit id. If empty, run
  `python "${CLAUDE_PLUGIN_ROOT}/plugin/state/cli.py" list --root "${CLAUDE_PROJECT_DIR}"`
  and take the change whose phase is `a` and whose `intent.md` is on the default branch; if
  there is not exactly one, stop and report the candidates. Never invent an id.
- Read the change: `python "${CLAUDE_PLUGIN_ROOT}/plugin/state/cli.py" show --root "${CLAUDE_PROJECT_DIR}" --id <id>`.
  If `status.parked_reason` is set, stop: the owner has something to do first.
- An incident change (`entry_route: incident`) whose intent PR the owner merged is at gate
  (a) even if `status.yaml` still says `phase: f`: the maintain run leaves it there, and the
  merge is gate (a) (decision 25; in CI the runner sets `a` before this command runs).
  Proceed with the design; the intent is the one the maintain run wrote.
- Default branch: `git symbolic-ref --short refs/remotes/origin/HEAD` minus `origin/`,
  else `main`. Run `git fetch origin` first.

## 1. Branch (idempotent; re-run rule, build guide step 8)
- First run: `git switch -c sdlc/<id>/b origin/<default>` (or `<default>` when there is no
  remote). The intent is read from that branch: it is what the owner merged.
- Re-run (the branch already exists locally or on `origin`): `git switch sdlc/<id>/b`
  and `git pull --ff-only origin sdlc/<id>/b` when the remote has it. Read the existing
  `spec.md` and `plan.md`; they are the starting point, not a blank page. Read the review
  comments on the open PR (`gh pr view <n> --comments` when `gh` exists, else the GitHub
  MCP tools, else the comments the caller pasted into the prompt) and treat every
  unresolved one as a constraint. Keep concerns the owner closed closed; reopen nothing.

## 2. Register the run (build guide step 19)
`python "${CLAUDE_PLUGIN_ROOT}/plugin/gate/cli.py" start-run --root "${CLAUDE_PROJECT_DIR}" --id <id> --phase b`
The gate reads the wall clock from it; an automated gate (b) parks without it.

## 3. Spec pass — prompt v1 (article p.14, with the policy skills loaded)
Load the five policy skills before writing: `coding-standards`, `security-baseline`,
`ux-conventions`, `data-conventions`, `definition-of-done` (a project override under
`.claude/skills/<name>/` replaces the plugin's). Load the `spec-template` skill. Then apply
this prompt to `changes/<id>-<slug>/intent.md`:

> Read intent.md and produce a requirements and design spec for integrating it into this
> codebase. Load every organization skill available to you — coding-standards,
> security-baseline, ux-conventions, data-conventions, definition-of-done — and for each one
> either apply it or state in the spec that it does not apply and why; cite the rule wherever
> one constrained you. Write exactly these level-2 sections, in this order: Requirements,
> Design, Open questions from intent, Flagged concerns, Acceptance (skill spec-template).
> Answer every open question from the intent from the codebase or a policy, citing the
> source, or carry it forward with the reason; never drop one. State what you had to assume
> because the intent does not say it. Describe clearly any areas of concern, especially
> where you cannot satisfy contradicting policies, one list item each under Flagged
> concerns; prefix an item with [x] only when a policy text settles it and say which; write
> "none" if there is none. This is the design, not the implementation plan: do not list the
> files that change, the order of work, risks or estimates — plan.md does that. Read the
> codebase with Read, Grep and Glob only; write no file but spec.md.

Rules for the pass (from the three by-hand runs of build guide step 22, recorded in
`docs/PROGRESS.md`):
- Read the codebase before writing, and `CLAUDE.md` and `sdlc.yaml` (profile, risk list,
  commands): the spec integrates into what exists, and the codebase often answers an open
  question in one line (say where). If `CLAUDE.md` or `sdlc.yaml` is missing, that is a
  flagged concern, not an assumption.
- Header: paste the two lines printed by
  `python "${CLAUDE_PLUGIN_ROOT}/plugin/gate/cli.py" spec-header --root "${CLAUDE_PROJECT_DIR}" --id <id>`
  (title, change id, plugin version, skills in force, prompt version).
- A guess made because the intent is silent is a flagged concern. So is any risk-list item
  in `sdlc.yaml` the design touches, and any policy the design cannot meet. Name a risk-list
  item under "## Flagged concerns" only when the design touches it: the gate reads that
  section literally and parks on every item named there until the owner accepts it. The
  items that do not apply are said not to apply in Requirements, never listed there.
- Close a concern yourself only when the policy text settles it, and say which policy
  (`- [x] <concern>: decided <how> per <skill> rule <n>`); the closing word is the first
  word of the item — a label such as `C3:` in front of it keeps the concern open. Every
  other concern stays open; under `review: parked` the gate parks while one is open and
  the owner closes it in review (step 23; `/sdlc-fix` applies a review comment that closes
  it); under `review: deferred` the panel of step 6a closes it and the owner reads the
  decision at the gate.
- As short as the change allows: a small change gets a short spec. Requirements are
  checkable bullets; Design is the shape, not the code.
- Write `changes/<id>-<slug>/spec.md`. Nothing else.

## 4. Planning run — read-only (article p.16 steps 1–4; decision 2; skill `plan-template`)
Load the `plan-template` skill. With **Read, Grep and Glob only** on the codebase, write
`changes/<id>-<slug>/plan.md` from spec.md: files that change, order of work, risks,
options not taken, proof — then answer the skill's interrogation prompt in writing and
fold the answers into Risks and Options not taken. The plan must be implementable by an
engineer who never saw this conversation (p.16 step 4). For a `fix`-type change
(`status.change_type`), the first step of the plan is the reproducing test and Proof names
it (build guide step 25). Do not run the project's commands and do not edit source; if
something must change before the plan can be written, say so in Risks.

## 5. Commit spec.md and plan.md (article p.14 step 5)
```
python "${CLAUDE_PLUGIN_ROOT}/plugin/state/cli.py" commit-phase --root "${CLAUDE_PROJECT_DIR}" --id <id> --phase b --message "design(<id>): <title>" --push
```
It sets `status.phase` to `b`, commits the change folder on `sdlc/<id>/b` and pushes when
there is a remote. Nothing outside the change folder may be modified; if `git status`
shows anything else, revert it before committing.

## 6. Adversarial review (build guide step 17; agent `sdlc:adversarial-reviewer`)
The reviewer has no shell, so write the diff it reads first, in one call (`<base>` is the
default branch, `origin/<default>` after the fetch: the base the gate diffs against):
`git diff --stat --patch --output=changes/<id>-<slug>/evidence/diff-b.patch <base>...HEAD`,
then `git rev-parse HEAD` for the full sha. The diff file is evidence: it is committed with
the gate (b) evidence commit of step 7.
Delegate to the `sdlc:adversarial-reviewer` agent with: the change id, the phase `b`, the
project root, the full HEAD sha and the path `changes/<id>-<slug>/evidence/diff-b.patch`. It writes
`changes/<id>-<slug>/evidence/adversarial-review-b.json` for the current HEAD (the commit
of step 5) and reports a verdict. Do not argue with it and do not edit its file.


### Deferred review: the panel settles the judgment items (decision 21; build guide step 16a)
```
python "${CLAUDE_PLUGIN_ROOT}/plugin/panel/cli.py" items --root "${CLAUDE_PROJECT_DIR}" --id <id> --phase b
```
It prints the review mode (`sdlc.yaml: review`, `status.yaml: review_override`), the items
the gate would park on that belong to the panel's fixed list (an open flagged concern, a
concern naming contradicting policies, the reviewer's `escalate` verdict, an Important
finding the run cannot fix, the verifier's "does not match the plan"), which of them the
ledger already decides, and under `parks` what stays the owner's whatever the mode (a
risk-list hit, a guardrail file, a run limit, an infrastructure failure). When `mode` is
`parked` or `pending` is empty, go on to the gate. Otherwise, for each pending item `n` in
order, three fresh contexts, each with the brief printed by
`python "${CLAUDE_PLUGIN_ROOT}/plugin/panel/cli.py" prompt --root "${CLAUDE_PROJECT_DIR}" --id <id> --phase b --item <n> --member <reviewer|advocate|conciliator>`:
1. **reviewer** — delegate to a general-purpose sub-agent with the `reviewer` brief; it
   writes `evidence/panel/b-<n>-reviewer.md`.
2. **devil's advocate** — delegate to `sdlc:adversarial-reviewer` with the `advocate`
   brief, on the model `sdlc.yaml: panel_advocate_model` names (pass it as the sub-agent's
   model: the per-invocation model wins, NOTES §11c; a panel on one model shares its blind
   spots), blind to the reviewer's file; it writes `evidence/panel/b-<n>-advocate.md`.
3. **conciliator** — delegate to a general-purpose sub-agent with the `conciliator` brief;
   it reads both files and writes `evidence/panel/b-<n>-conciliator.json`.
Then record it:
`python "${CLAUDE_PLUGIN_ROOT}/plugin/panel/cli.py" record --root "${CLAUDE_PROJECT_DIR}" --id <id> --phase b --item <n>`
— one panel call counts against `gate.max_panel_calls` (its own count, not a fix
iteration; exit 3 at the cap: stop the panel, the gate parks); it appends the line to
`evidence/decisions-b.json` (and the `.md` the owner reads), for a concern closes the item
in `spec.md` as `decided (by panel #<n>): <decision> — <concern>`, and commits the change
folder itself (`design(<id>): panel decision <n>`), so the decision is in HEAD before anyone
judges it. Do not reword a closed concern line: the gate matches it to the ledger by
`#<n>`. Apply what the decision asks beyond that (an `escalate` decided `continue` needs
nothing more; a fix the decision names is made now, `plan.md` in the same commit, committed
with `commit-phase ... --phase b --message "design(<id>): panel decision <n> applied"`).
After the last item, re-run step 6 for the new HEAD, once (a verdict never
outlives the diff it judged, and the diff file must be regenerated first); from then on
nothing is committed before the gate except the gate evidence, and the verdict file never
travels in a commit with content the reviewer did not see (the first deferred run,
2026-09-24, committed each verdict beside the content it did not judge, three times, and
needed four commits to land one). An `escalate` with new reasons is a new item: run
`items` once more. The panel never decides a park item, never raises a limit, never
touches a guardrail file, and never asks the owner: the owner reads "Decisions taken for
you" at the gate and overturns any line with a review comment.

## 7. Gate (b) (build guide steps 16, 23)
```
python "${CLAUDE_PLUGIN_ROOT}/plugin/gate/cli.py" check --root "${CLAUDE_PROJECT_DIR}" --id <id> --phase b
```
Exit 3 = `wait` (gate (b) is a human gate in every profile), 4 = `park`. It writes `status.yaml` and `evidence/gate-b.json`, and prints the label to apply
and, when parked, the "What I need from you" block. Then commit the evidence:
```
python "${CLAUDE_PLUGIN_ROOT}/plugin/state/cli.py" commit-phase --root "${CLAUDE_PROJECT_DIR}" --id <id> --phase b --message "design(<id>): gate (b) evidence" --push
```

## 8. Outcome
**`wait` or `park` — open or update the spec+plan PR.**
```
python "${CLAUDE_PLUGIN_ROOT}/plugin/pr/cli.py" upsert --root "${CLAUDE_PROJECT_DIR}" --id <id> --phase b
```
Base: the default branch. Head: `sdlc/<id>/b`. Title: `design(<id>): <title>`. The builder
renders the ≤5-bullet summary from `status.yaml`, `spec.md`, `plan.md` and
`evidence/gate-b.json`:
1. what the change is and the design in one line;
2. evidence status ("design phase, no code yet" at this gate);
3. flagged concerns: how many open, how many closed, the open ones quoted verbatim;
4. open questions from the intent: answered / carried forward;
5. what needs the owner — the gate (b) checklist (build guide step 23): does the spec solve
   the stated problem? are the intent's open questions answered or carried forward? is every
   flagged concern closed? could someone who never saw this conversation implement plan.md?
   Merge = approve; a review comment = change request (`/sdlc-fix`). When parked, the
   gate's "What I need from you" block follows the bullets verbatim.
Then the links to `spec.md`, `plan.md` and `evidence/gate-b.json`. Label: the one the gate
printed (`sdlc:b-ready`, or `sdlc:needs-human` when parked); the previous `sdlc:*` label is
removed. Re-run: the same command updates the existing PR; never open a second one. Routes:
`gh`, then the REST API with `GITHUB_TOKEN`/`GH_TOKEN`, else the printed compare URL and
body for the owner (or a GitHub MCP tool with the same title, body and label). Do not retry
with other means.

## 9. Report
One line: the PR URL (or the compare URL), the gate result, the number of open concerns
and, under deferred review, the number of panel decisions. Nothing else is started.
Do not start phase (c) here: gate (b) is the owner's merge in every profile.

Never edit `.claude/**`, `CLAUDE.md`, `REVIEW.md`, `sdlc.yaml`, `intent.md` or any file
outside `changes/<id>-<slug>/`. Never use bypass-permissions mode. Never notify anyone.
