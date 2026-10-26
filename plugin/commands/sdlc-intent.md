---
description: The intent phase — brainstorm a change with the owner, write changes/<id>-<slug>/intent.md via the intent-template skill, let the product owner correct it, commit on sdlc/<id>/intent and open the intent PR. The intent gate = the product owner merges that PR; an intent PR the owner's own account opens starts the design at once (the fast lane, decision 30).
argument-hint: [one-line description of the idea, ticket or incident]
disable-model-invocation: true
allowed-tools: Bash(python "${CLAUDE_PLUGIN_ROOT}/plugin/state/cli.py" *), Bash(python "${CLAUDE_PLUGIN_ROOT}/plugin/pr/cli.py" *), Bash(git *), Bash(gh *), Read, Write, Edit, Glob, Grep, AskUserQuestion
---

# /sdlc-intent — the intent phase

Until plugin 1.0.42 this command was `/sdlc-plan` (decision 39, row 8).

Source: build guide step 11 (article p.10–11, steps 1–5; governance p.11: the accept/reject
decision "is recorded as the merge"). This is the only interactive phase. Re-runnable: if a
change folder for this idea already exists, continue from its intent.md instead of creating
a new one.

## 0. Preconditions
- `sdlc.yaml` exists at the project root. If not, stop and tell the owner to run `/sdlc-init`.
- Note the current branch; work happens on `sdlc/<id>/intent`, branched from the default branch.
- Re-run rule: list the existing changes first —
  `python "${CLAUDE_PLUGIN_ROOT}/plugin/state/cli.py" list --root "${CLAUDE_PROJECT_DIR}"` —
  and if one in phase `intent` (an older change may say `a`) has the same title or clearly the same idea, continue with that id
  and its intent.md (skip step 2) instead of allocating a new one.

## 1. Brainstorm until the idea is concrete (article p.10 step 2)
Start from `$ARGUMENTS` (may be empty). Ask the questions an analyst would ask, a few at a
time, until you can fill every section of the intent template without guessing:
- scope: what is in, what is explicitly out;
- users and systems affected;
- constraints (security, data, compatibility, budget, deadline);
- what success looks like, stated so it can be checked later;
- entry route: idea, ticket or incident (for a ticket ask for its number; for an incident ask
  for the evidence: what was observed, where, when);
- change type: feature or fix (a fix is proven by a failing test written first);
- when the change touches a screen: "Do you have a mock or example screens?" A mock goes
  into `changes/<id>-<slug>/mock/` once the change is allocated; example screens and other
  references go into the intent's Examples/References. No mock is a valid answer and never
  blocks (ROADMAP R29).
The gates and the review mode are not asked: one behaviour for every change (decision 37).
Do not write files during the brainstorm.

**The quick intent** (ROADMAP R54): when the owner asks for a quick intent, or
`$ARGUMENTS` starts with `quick:`, skip the brainstorm. Take the owner's one paragraph
(`$ARGUMENTS` after `quick:`, else ask for it once), and ask nothing more, except the change
type when the paragraph does not make it plain. The route is `idea`. In step 3 write the
quick intent's shape (skill `intent-template`, "Quick intent"), skip step 4's correction
loop and set the header status to `proposed`: the design run states what it assumed at
the top of the design PR, and the product owner corrects it there, or the code owner at the deploy gate.

## 2. Allocate the change
Run (from the project root):
```
python "${CLAUDE_PLUGIN_ROOT}/plugin/state/cli.py" new-change --root "${CLAUDE_PROJECT_DIR}" --title "<short title>" --route <idea|ticket|incident> --type <feature|fix> [--external-ref <ticket number>]
```
It prints the id, slug, folder and branch. Read them from the JSON; never invent an id.

## 3. Write intent.md
Use the `intent-template` skill (it defines the exact sections and header). Write
`changes/<id>-<slug>/intent.md`. The header carries no status line (`status.yaml` holds the
phase).

## 4. The product owner corrects (article p.11 step 4)
Show the draft in full and ask the owner, as the product owner, what you misunderstood. Apply
every correction. Repeat until they say it is right.

## 5. Commit on the phase branch (article p.11 step 5)
```
python "${CLAUDE_PLUGIN_ROOT}/plugin/state/cli.py" commit-phase --root "${CLAUDE_PROJECT_DIR}" --id <id> --phase intent --message "intent(<id>): <title>" --start-point <default branch> --push
```
The JSON tells you the branch, the commit and whether the push happened (`pushed`) and the
GitHub repo (`github_repo`). If there is no remote, stop after the commit and report it.

## 6. Open the intent PR (the intent gate)
```
python "${CLAUDE_PLUGIN_ROOT}/plugin/pr/cli.py" upsert --root "${CLAUDE_PROJECT_DIR}" --id <id> --phase intent
```
It opens (or updates, on a re-run) the PR — base the default branch, head `sdlc/<id>/intent`,
title `intent(<id>): <title>` — with the generated description: a ≤5-bullet summary first
(what the change is and why · entry route and change type · affected users and systems ·
open questions · what needs the product owner: nothing when the owner's own account opens it, not as
a draft (the fast lane, decision 30), else read, correct via review comments, merge = approve),
then the link to `changes/<id>-<slug>/intent.md`; and applies the label `sdlc:intent-ready`
(created if missing). Routes, in order: the GitHub REST API with the token
(`GITHUB_TOKEN`/`GH_TOKEN`) first, then the `gh` CLI, then it prints the compare URL
`https://github.com/<github_repo>/compare/<base>...sdlc/<id>/intent?expand=1` and the body for
the owner to paste (in a cloud session without `gh`, a GitHub MCP tool such as
`create_pull_request` may be used with that title, body and label instead). Do not retry
with other means.

## 7. Report
One line: the PR URL (or the compare URL), and "gate (intent): as the product owner, merge the PR to approve; review
comments are the change request (then run `/sdlc-fix`)". Add that an intent PR opened from the owner's own account takes the fast lane (decision 30):
opening it accepts the intent, the design workflow starts at once without a merge, and the
intent PR is closed as `sdlc:superseded` once the design PR carries the intent. For a PR
opened (or reopened) as a draft or by any other account, or one that changes
anything outside its change folder, the merge stays the intent gate. Do not start
the design phase.

Never edit `.claude/**`, `CLAUDE.md`, `REVIEW.md`, `sdlc.yaml` or `policies/**`. Never use
bypass-permissions mode. Never notify anyone.
