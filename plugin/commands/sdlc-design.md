---
description: Phase (b) design — from the merged intent, write spec.md with the policy skills loaded (the article's p.14 prompt), then the read-only planning run that writes plan.md, run the adversarial reviewer and call gate (b). Standard/Full: open the spec+plan PR on sdlc/<id>/b with sdlc:b-ready. Lite: commit and hand over to /sdlc-build. Re-runnable after review comments. No questions to the owner; a gap becomes a flagged concern.
argument-hint: [change id, e.g. 0001]
disable-model-invocation: true
allowed-tools: Bash(python "${CLAUDE_PLUGIN_ROOT}/plugin/state/cli.py" *), Bash(python "${CLAUDE_PLUGIN_ROOT}/plugin/gate/cli.py" *), Bash(python "${CLAUDE_PLUGIN_ROOT}/plugin/pr/cli.py" *), Bash(git *), Bash(gh *), Read, Glob, Grep, Edit(changes/**), Write(changes/**), Agent
---

# /sdlc-design — phase (b)

Source: build guide steps 22–23 (article p.13–14: the design prompt and its automation
ladder "by hand → slash command → merge-triggered job"; p.14 governance: "the spec, the
prompt that produced it, and the skill versions in force are all logged in version
control"), step 12 and decision 2 (plan.md by a read-only run at the end of phase (b)),
decision 18 (profiles). Prompt version: **v1** (the spec header records it).

This phase runs unattended: by hand today, from the merge-triggered workflow from B3 on.
**Never ask the owner anything.** The merged intent.md is the owner's answer; anything it
leaves open becomes a carried-forward question or a flagged concern the owner reads at the
gate. Never edit intent.md (accepted at gate (a); the gate parks a branch that changes it).
Never edit source: the only files this phase writes are under `changes/<id>-<slug>/`
(decision 2; the gate's `design_scope` check parks anything else).

## 0. Preconditions
- `sdlc.yaml` exists at the project root; otherwise stop and say `/sdlc-init` is missing.
- Change id: `$ARGUMENTS` is the four-digit id. If empty, run
  `python "${CLAUDE_PLUGIN_ROOT}/plugin/state/cli.py" list --root "${CLAUDE_PROJECT_DIR}"`
  and take the change whose phase is `a` and whose `intent.md` is on the default branch; if
  there is not exactly one, stop and report the candidates. Never invent an id.
- Read the change: `python "${CLAUDE_PLUGIN_ROOT}/plugin/state/cli.py" show --root "${CLAUDE_PROJECT_DIR}" --id <id>`.
  If `status.parked_reason` is set, stop: the owner has something to do first.
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
  in `sdlc.yaml` the design touches, and any policy the design cannot meet.
- Close a concern yourself only when the policy text settles it, and say which policy
  (`- [x] <concern>: decided <how> per <skill> rule <n>`); the closing word is the first
  word of the item — a label such as `C3:` in front of it keeps the concern open. Every
  other concern stays open;
  the gate parks while one is open and the owner closes it in review (step 23; `/sdlc-fix`
  applies a review comment that closes it).
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
Delegate to the `sdlc:adversarial-reviewer` agent with: the change id, the phase `b`, the
project root and the default branch. It writes
`changes/<id>-<slug>/evidence/adversarial-review-b.json` for the current HEAD (the commit
of step 5) and reports a verdict. Do not argue with it and do not edit its file.

## 7. Gate (b) (build guide steps 16, 23)
```
python "${CLAUDE_PLUGIN_ROOT}/plugin/gate/cli.py" check --root "${CLAUDE_PROJECT_DIR}" --id <id> --phase b
```
Exit 3 = `wait` (a human gate: Standard and Full profiles), 0 = `continue` (Lite), 4 =
`park`. It writes `status.yaml` and `evidence/gate-b.json`, and prints the label to apply
and, when parked, the "What I need from you" block. Then commit the evidence:
```
python "${CLAUDE_PLUGIN_ROOT}/plugin/state/cli.py" commit-phase --root "${CLAUDE_PROJECT_DIR}" --id <id> --phase b --message "design(<id>): gate (b) evidence" --push
```

## 8. Outcome
**`wait` (Standard, Full) or `park` in any profile — open or update the spec+plan PR.**
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

**`continue` (Lite profile only).** No PR at (b). The spec and plan are committed on
`sdlc/<id>/b` and pushed; `/sdlc-build` starts `sdlc/<id>/c` from that branch. By hand:
report that the next step is `/sdlc-build <id>`; in the merge-triggered workflow the job
dispatches the build workflow itself (build guide step 30). Do not start phase (c) here.

## 9. Report
One line: the PR URL (or the compare URL, or "continue → /sdlc-build <id>"), the gate
result, and the number of open concerns. Nothing else is started.

Never edit `.claude/**`, `CLAUDE.md`, `REVIEW.md`, `sdlc.yaml`, `intent.md` or any file
outside `changes/<id>-<slug>/`. Never use bypass-permissions mode. Never notify anyone.
