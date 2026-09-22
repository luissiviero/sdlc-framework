# Intent: connect the SDLC framework
Author: owner. Status: draft. Change id: 0000. Entry route: idea.
Framework change: yes

## Problem
sdlc-framework has no shared process for taking a change from idea to production
with the agent doing the work and the owner judging at gates.

## Proposed outcome
The SDLC framework plugin `sdlc@sdlc-framework` v0.2.9 is installed:
profile `standard`, one-command targets build=`python -m compileall -q plugin tests tasks.py`,
test=`python -m pytest`, lint=`python -m ruff check .`, guardrail hooks and permissions
in place, `changes/` as the home of every change.

## Affected users and systems
The owner; this repository's CLAUDE.md, REVIEW.md, sdlc.yaml and .claude/settings.json.

## Constraints
Only the owner merges to main. No bypass-permissions mode. Guardrail files are protected
paths from this change on.

## Open questions
- Detection notes: none
