# Progress — decision 40's review corrections, annotated after #364 merged (2026-10-23)

This session is lane B of wave 3 (R27, then R64). The branch `claude/decision-6-policies` was restarted from `main` at `7cac00e` (#364) after #364 merged. Its first record, `2026-10-23-claude-decision-6-policies.md`, is on `main`, so this file takes a suffix (HANDOFF.md, "How a session ends", step 4). It is a documentation PR: no plugin version, no file under `plugin/` or `template/`, no choice number.

## What happened
A fresh-context review of #364 ran after its CI turned green. It checked every citation and the file's shape against decisions 26 to 32 and 38, and found one error and three overstatements in `docs/decisions/40.md`. The fixes were pushed to the branch as `9d82bc3` at about 15:25 UTC. The owner had merged #364 at 15:24:56 UTC on `f1a8ce7`, so the fixes never reached `main` (`git merge-base --is-ancestor 9d82bc3 origin/main` fails).

## What this PR changes
Four dated annotations in `docs/decisions/40.md`, each beside the sentence it corrects; the merged text is not rewritten (choice 126):
1. **Layer (ii)** (the error): the managed settings file takes `Edit(policies/**)` with no leading slash, as its other rules are spelled. A `/` rule in a machine-wide file has no project root to anchor to (`docs/notes/6.md`, `docs/notes/12.md`; `docs/owner-machine/managed-settings.json` lines 8 to 11 use bare names), so `Edit(/policies/**)` there would protect nothing. R27's build adds this line to `docs/owner-machine/managed-settings.json` or proposes it to the owner.
2. **"Today"**: it now names the paths the plugin protects beyond decision 6's own text, `sdlc.yaml` and R44's four.
3. **"Four layers read one list"**: it now says four checks, and names the lists kept by hand.
4. **The exceptions**: they are sourced to OPERATING_MODEL sections 3 and 8 rather than decision 6's text, and the gate's exemption of change 0000 by its id is named.

## Port list
None: the PR touches no file under `plugin/` or `template/`.

## What the owner does
| When | Act |
|---|---|
| Now | Merge this PR when `Framework checks` is green on its final head. |
