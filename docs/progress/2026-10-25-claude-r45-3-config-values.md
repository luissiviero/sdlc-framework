# Progress — R45's third rename PR: the configuration values (2026-10-25, plugin 1.0.45)

This session ran on branch `claude/r45-3-config-values`, built on R45's second rename PR (#390, merged as `dc9692b`, plugin 1.0.44, tagged `v1.0.44`), with `main` merged in by a merge commit (it carries #391, decision 41). It is section 12's PR 3 of `docs/reviews/2026-10-20-names-against-the-article.md`, as decision 39's points 2 and 4 amend it: rows 53 and 88 are moot (decision 37 removed the Full profile), and it gains N11. Plugin **1.0.45** (`python tasks.py next-free` after `git fetch origin` on `7ac4131`). No numbered choice, note or decision is taken.

## What was built
1. **`deploy.production` is `deploy.production_gate`** (row 55): one reader, `production_gate(config)` in `plugin/hooks/_common.py` beside `config_flag`, reads the new key, else the old one, with the same strict boolean rule; the two set and disagreeing is a `ConfigError` naming both (fail closed, as `config_flag` does). The production-gate hook, `detect/routes.py`, the PR description, the release step and `state/cli.py` read it. `template/sdlc.yaml` writes `production_gate:`; `/sdlc-init --deploy-production` keeps its flag name (decision 39 does not rename it). An upgrade of a project whose file has the old key no longer adds the new one beside it (which would have made every reader fail closed): `keep_legacy_keys` leaves it out and the report's `legacy_keys` names each old key for the owner.
2. **`bands.yaml: authorization` is `allow | ask`** (row 56, the hook verbs, article p.36): `detect/routes.py` holds `ALLOW`, `ASK` and `authorization_value`, which reads `preapproved` and `go` as the new values for one release; `bands.py` stores what it read under the new names. `sdlc.yaml: maintain.runbooks[].authorization`, the stricter value a project may set on a runbook, takes the same two words. The label `sdlc:go`, the `detect/cli.py go` subcommand, the `go-requested` status and "Go requested" stay (rows 39 and 75).
3. **`external_review` is `second_opinion`** (N11): `plugin/external/cli.py` reads `second_opinion`, else `external_review`; with both, the new one wins and the old one is reported once in the record and the PR comment (`config_note`), never refused, as `retired_settings_note` treats a retired key; the sub-keys stay.
4. **The decisions it renames, annotated** (decision 39, "What it amends"; choice 126): decision 26 (`deploy.production`) and 14 (the `bands.yaml` split), each beside its sentence. Decision 13 names no key; no decision but 39 names `external_review`.

## How it was built
One sub-agent built the three renames on this branch; this session merged `main`, bumped the version, regenerated `plugin/init/template_hashes.json` and ran the suite. Tests that asserted the old names assert the new ones; none was deleted or skipped; tests show each old name is still read and the two production keys disagreeing fail closed.

## The fresh-context review
A fresh-context sub-agent reviewed the diff (report only). It found nothing blocking. It traced the production gate with the old key, the new key, both agreeing, both disagreeing and neither, and found it never fails open; no authorization value is compared without the normaliser, and an old `go` never becomes `allow`. Its findings and what was done:
1. **Fixed:** `docs/OPERATING_MODEL.md` still said "a `go` here is stricter".
2. **Fixed:** a project that renames `deploy.production` before its pin reads the new key (a pin below 1.0.45) turns the production gate off, since the older plugin reads only `production`. `/sdlc-init`'s `legacy_keys` line, its command text and `template/sdlc.yaml`'s comment now say the rename waits for the pin at 1.0.45 or later.
3. **Fixed:** a project runbook's `authorization` that is neither `allow` nor `ask` (a typo, `Ask`) was ignored, so the bands' value stood; it now reads as `ask`, since a runbook entry may only tighten (`detect/routes.py`), with a test. This also keeps an entry still saying `go` strict once the sixth PR drops the old values.
4. **Optional, taken:** `/sdlc-deploy`'s body and hand-over name the old key beside the new; `/sdlc-init` and the second opinion's note now give the same advice when both `external_review` and `second_opinion` are set ("remove it").
5. **Optional, not taken:** a run-time note for the old production key (the release log prints the value it read; `/sdlc-init` reports the key); the second opinion's note on an "off" record that writes no file; three more compatibility tests whose logic the reviewer confirmed by reading; the ROADMAP proposal that still names `deploy.production` (a proposal's text, not this PR's).

## Port list
This PR touches `plugin/detect/` and the detect and runbook workflow templates: it goes on the port list until the 1.0.0 read.

## Proposed edits for the owner
For this repository's pin-move PR (the old names keep working until the sixth PR):

| Link | Row | What is there | What it must become |
|---|---|---|---|
| `sdlc.yaml` | 41 | `  production: false` | `  production_gate: false` |
| `sdlc.yaml` | 43 | `  # build PR's merge (and, when production is true, after the release label): e.g.` | `  # build PR's merge (and, when production_gate is true, after the release label): e.g.` |
| `sdlc.yaml` | 55 | `  # "python scripts/promote.py"). Only read when production is true.` | `  # "python scripts/promote.py"). Only read when production_gate is true.` |
| `sdlc.yaml` | 63 | `  # runbooks the 3-sigma tier may call; authorization: preapproved (CI-scoped, reversible)` | `  # runbooks the 3-sigma tier may call; authorization: allow (CI-scoped, reversible)` |
| `sdlc.yaml` | 64 | `  # or go (touches a running system; waits for the owner's "Go" as a parked item)` | `  # or ask (touches a running system; waits for the owner's "Go" as a parked item)` |
| `bands.yaml` | 20 | `    # radius): preapproved = CI-scoped and reversible, runs with no human in the path;` | `    # radius): allow = CI-scoped and reversible, runs with no human in the path;` |
| `bands.yaml` | 21 | `    # go = touches a running system, parks with "what I need from you" until the owner` | `    # ask = touches a running system, parks with "what I need from you" until the owner` |
| `bands.yaml` | 25 | `        authorization: preapproved` | `        authorization: allow` |
| `bands.yaml` | 27 | `        authorization: preapproved` | `        authorization: allow` |
| `bands.yaml` | 29 | `        authorization: preapproved` | `        authorization: allow` |
| `bands.yaml` | 31 | `        authorization: go` | `        authorization: ask` |

The root `sdlc.yaml` has no `external_review` block. The sample's lines are read at its own pin-move PR.

## What the owner does
| When | Act |
|---|---|
| Now | Write and commit the workflow copies on `claude/r45-3-config-values` with `python tasks.py workflow-copies` (the PR body's commands), then merge the PR when `Framework checks` is green on its final head. |
| At this repository's pin move | The table above. |
