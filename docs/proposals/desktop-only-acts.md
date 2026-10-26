---
type: Proposal
title: Desktop-only acts — say when the GitHub mobile app cannot do it, and give the link
description: Every place the framework asks the owner for an act the GitHub mobile app cannot perform (a repository setting, a secret, a ruleset) says so, tells the owner to open github.com in the phone browser's desktop mode, and gives the direct link to the settings page.
status: accepted
roadmap: R21
sources:
  - id: owner-request
    resource: "the owner's request of 2026-10-15 in session ccr-01de3f80-ilnomi: \"inform the mobile user when the app won't work and that tasks needs to be done in the browser desktop mode. Additionally, the link to it.\""
    title: "The owner asks for a desktop-mode note and a link on every act the app cannot do"
  - id: init-step-6
    resource: plugin/commands/sdlc-init.md
    title: "Step 6, 'After the merge': the workflow permission, the CI secret and the branch ruleset, as Settings menu paths with no link"
  - id: digest-unprotected
    resource: plugin/pr/digest.py
    title: "UNPROTECTED (lines 44-54): the digest's warning when the default branch has no Restrict-updates ruleset, a Settings menu path with no link"
  - id: notes-17-23
    resource: docs/notes/17.md, docs/notes/23.md
    title: "What the mobile app was seen doing: a merge under the Exempt bypass (§17) and a Request-changes review (§23)"
  - id: r19
    resource: docs/proposals/what-you-can-do-here.md
    title: "R19: the generated 'What you can do here' block and its one table of acts"
generated: { by: sdlc-framework-session/ccr-01de3f80-ilnomi, at: 2026-10-15T12:00:00Z }
---

# Desktop-only acts
**Names since R45** (decision 39; the renames built in plugin 1.0.43 to 1.0.47; added on 2026-10-26): none of the renamed names appear here. \
**Status: proposed (roadmap R21).** *[2026-10-20: accepted 2026-10-16 (PR #215)]* Nothing is built. The owner asked for it on 2026-10-15[^owner-request]; this file carries the argument and the row in `docs/ROADMAP.md` carries the status. Not urgent.

## The problem

The owner works from a phone as often as from a PC. Most acts the framework asks for work in the GitHub mobile app: a merge, under the ruleset's Exempt bypass, and a "Request changes" review were both seen working there[^notes-17-23]. A few acts are repository settings, which the app does not show. The framework asks for them as menu paths ("Settings → Rules → Rulesets → New branch ruleset"), with no link and no word that the app cannot do them[^init-step-6][^digest-unprotected]. An owner on a phone looks for the menu in the app, does not find it, and loses the step.

Today the acts known to need a browser are:
- the repository secret `CLAUDE_CODE_OAUTH_TOKEN` or `ANTHROPIC_API_KEY` (`/sdlc-init` step 6);
- Settings → Actions → General → Workflow permissions → "Allow GitHub Actions to create and approve pull requests" (`/sdlc-init` step 6; without it every phase job fails when it opens its pull request);
- the branch ruleset on the default branch, its Exempt bypass mode included (`/sdlc-init` step 6, and the digest's warning while it is missing).

Not verified, to check on the owner's phone before the design: whether the app can dispatch a workflow (`workflow_dispatch`, used for a by-hand detect or fix run), approve a bot head's runs waiting at `action_required`, and apply a label to a pull request.

## The proposal

1. **One table of desktop-only acts**, in Python beside the conventions (decision 7): each act with the settings page's URL pattern, for example `https://github.com/<owner>/<repo>/settings/secrets/actions`, `…/settings/actions` and `…/settings/rules`. The exact paths are read from GitHub's documentation and checked once in a browser before they are written; none is verified here.
2. **Every message that asks for such an act renders from that table**: the act, then one line, "Not available in the GitHub mobile app: open this link in your phone browser and switch it to desktop mode (Chrome: ⋮ → Desktop site; Safari: aA → Request Desktop Website)", then the link filled with the project's own owner and repository.
3. **Where it shows**: the `/sdlc-init` report's "After the merge" list; the digest's `UNPROTECTED` warning; any park whose reason is a missing setting (the workflow permission, the CI secret); and, once R19 is built, a "where" mark on each act in R19's table, so the "What you can do here" block flags a desktop-only act the same way.
4. **What it does not do**: it does not change any setting itself (decision 4 keeps settings with the owner) and it does not notify (decision 11).

## Order

Not placed. *[2026-10-20: Order 27 (ROADMAP R21); the rank is read from ROADMAP's Order column]* It is small and could ride with R19, which builds the table of acts this one marks; the `/sdlc-init` and digest lines need no R19 and could go in any plain PR that touches those files.
