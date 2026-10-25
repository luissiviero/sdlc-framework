---
description: Renamed — the intent phase is now /sdlc-intent (decision 39, row 8). This name stays for one release and only points there; run /sdlc-intent instead.
argument-hint: [one-line description of the idea, ticket or incident]
disable-model-invocation: true
allowed-tools: Read
---

# /sdlc-plan — renamed to /sdlc-intent

The intent phase's command is now `/sdlc-intent` (decision 39, row 8: the phase writes
`intent.md`, and "plan" means `plan.md` only, which the design phase writes). This name stays
for one release and then goes (choice 273).

Do nothing else here: tell the owner, in one line, to run `/sdlc-intent $ARGUMENTS` instead.
Write no file, allocate no change and open no pull request.

Never edit `.claude/**`, `CLAUDE.md`, `REVIEW.md`, `sdlc.yaml` or `policies/**`. Never use
bypass-permissions mode. Never notify anyone.
