---
description: Phase (a) plan — brainstorm a change with the owner, write changes/<id>-<slug>/intent.md via the intent-template skill, let the owner correct it, commit on sdlc/<id>/a and open the intent PR. Gate (a) = the owner merges that PR.
argument-hint: [one-line description of the idea, ticket or incident]
disable-model-invocation: true
allowed-tools: Bash(python ${CLAUDE_PLUGIN_ROOT}/state/cli.py *), Bash(git *), Bash(gh *), Read, Write, Edit, Glob, Grep, AskUserQuestion
---

# /sdlc-plan — phase (a)

Source: build guide step 11 (article p.10–11, steps 1–5; governance p.11: the accept/reject
decision "is recorded as the merge"). This is the only interactive phase. Re-runnable: if a
change folder for this idea already exists, continue from its intent.md instead of creating
a new one.

## 0. Preconditions
- `sdlc.yaml` exists at the project root. If not, stop and tell the owner to run `/sdlc-init`.
- Note the current branch; work happens on `sdlc/<id>/a`, branched from the default branch.

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
- whether this change needs a profile different from the project's (`profile_override`).
Do not write files during the brainstorm.

## 2. Allocate the change
Run (from the project root):
```
python "${CLAUDE_PLUGIN_ROOT}/state/cli.py" new-change --root "${CLAUDE_PROJECT_DIR}" --title "<short title>" --route <idea|ticket|incident> --type <feature|fix> [--profile-override <standard|full|lite>] [--external-ref <ticket number>]
```
It prints the id, slug, folder and branch. Read them from the JSON; never invent an id.

## 3. Write intent.md
Use the `intent-template` skill (it defines the exact sections and header). Write
`changes/<id>-<slug>/intent.md`. Status in the header is `draft`.

## 4. The owner corrects (article p.11 step 4)
Show the draft in full and ask the owner what you misunderstood. Apply every correction.
Repeat until the owner says it is right. Then set the header status to `proposed`.

## 5. Commit on the phase branch (article p.11 step 5)
```
python "${CLAUDE_PLUGIN_ROOT}/state/cli.py" commit-phase --root "${CLAUDE_PROJECT_DIR}" --id <id> --phase a --message "intent(<id>): <title>" --start-point <default branch> --push
```
The JSON tells you the branch, the commit and whether the push happened (`pushed`) and the
GitHub repo (`github_repo`). If there is no remote, stop after the commit and report it.

## 6. Open the intent PR (gate (a))
Base: the default branch. Head: `sdlc/<id>/a`. Title: `intent(<id>): <title>`. Body: a
≤5-bullet summary first (what the change is and why · entry route and change type · affected
users and systems · open questions · what needs the owner: read, correct via review
comments, merge = approve), then a link to `changes/<id>-<slug>/intent.md`.
Label the PR `sdlc:a-ready`.
- If the `gh` CLI is available: `gh label create sdlc:a-ready --force --color 0E8A16 --description "waiting at gate (a)"` then `gh pr create --base <base> --head sdlc/<id>/a --title "..." --body "..." --label sdlc:a-ready`.
- Else, if a GitHub MCP tool such as `create_pull_request` is available in this session (cloud sessions): use it with the same base, head, title and body, then add the label with the issue-update tool.
- Else: print the compare URL `https://github.com/<github_repo>/compare/<base>...sdlc/<id>/a?expand=1` and the body text, and tell the owner to open the PR and add the label. Do not retry with other means.

## 7. Report
One line: the PR URL (or the compare URL), and "gate (a): merge the PR to approve; review
comments are the change request (then run `/sdlc-fix` — available from B3)". Do not start
phase (b).

Never edit `.claude/**`, `CLAUDE.md`, `REVIEW.md` or `sdlc.yaml`. Never notify anyone.
