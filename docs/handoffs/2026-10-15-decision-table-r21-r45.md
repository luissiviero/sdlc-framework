# R21 to R45: what to accept, and an Order that does the structural changes first

Draft for the owner, 2026-10-15, branch `ccr-01de3f80-ilnomi`. Nothing here is decided. The owner's Order for R5 to R20 stays theirs: every move below is marked **(rec.)**, with its reason.
Weights used for the scores (crosswalk `owner.criteriaWeights`): safety 1, attention 3, autonomy 3, audit 2, cost 0, fidelity 2.

## 1. The recommendation in short

- **Drop none.** All 25 are accepted. Twelve go into wave 1, wholly or in part. Thirteen wait for a named predecessor. None scores low enough under the weights to drop, and on 2026-10-09 the owner confirmed every study entry these proposals come from.
- **Wave 1 is what must exist before the real-project trial.** It keeps the owner's ranks 1 to 4, R11, R12+R13 and R17 in their relative order, then adds the structural line in this order: R36 then R22, R24, R25 parts 1-2, R27, R28 parts 0-4, and R45 last. Beside these come three items the trial needs because it is a Node/TypeScript website: R14, R33 and R30. R21 part 1, R29 part 1 and R44 are also in wave 1; each is small.
- **R45 is split.** The names are settled in a decision file at rank 6, before R11's design. R45 already requires R11's approvals keys to be judged before that design. The rename itself is the last change of wave 1, before the trial. The study put T4 last because "a rename is cheapest once the other changes have landed". That still holds for the code: wave-1 code is renamed once, and later changes are born with the final names, because every proposal is now written and its placeholder names can be judged today. It does not hold for the owner. Renaming after the trial means learning the labels, branches and commands twice and migrating a client project.
- **Moves from the owner's Order (rec.).** R14 moves to rank 5: its intent, #173, waits only for R10, and the trial is a website whose proof is screenshots and states. R9 part 1 moves from rank 5 to wave 2: it is additive, and the owner called it the least urgent. R11, R12, R13 and R17 keep their relative order and only shift down.
- **Two ways to save owner attention.** First, write the 9 decision files as 5 documentation PRs: R45; R22+R23; R24+R25; R27+R28; and R39+R41 in wave 3. Second, wave 1 is about 20 changes. If that is too long before the trial, section 4 gives the minimal set and what the trial can safely ignore.

## 2. Table A: one row per candidate

Legend: **Now** = accept today and build in wave 1, before the trial. **Later: X** = accept today and build after X (wave 2 or 3). **Drop** = not built.

| R | Short name | Structural or additive (why) | Decision files before the intent | Hard dependencies | Recommendation | Score against the weights |
|---|---|---|---|---|---|---|
| R21 | Desktop-only acts | Additive: wording and links, no act changes | none | none; part 2 (the mark in the act table) needs R19 | **Now**, part 1 (`/sdlc-init` step 6, the digest's UNPROTECTED line, R22's App and ruleset 2), right after R22. Part 2 **later: R19** | Attention + for a phone owner setting up a new project; tiny cost |
| R22 | Gate (e) is the approval; an App merges | **Structural**: per-project setup (App, key, ruleset 2); the (e) act becomes "approve" | 13, 4, 5 | R6 and R10 built; R17's `is_owner_actor` (or R22 adds it); R13 at the release; live App checks choose C4, C3 or C1; R36 before ruleset 2 | **Now** (rank 11); run its live checks early, in parallel | Attention +++ and autonomy ++ (one act, from the phone); audit + (approval and merge lines); fidelity + (pp. 33-35) |
| R23 | Triage: a dismissal is one act | Additive: removes an act (2 → 1) | 4 | R22 (App, merge workflow); R17 | **Later: R22 and R17** (wave 2). The band-number part can ship at any time | Attention ++ and audit +, but it only matters once (f) runs |
| R24 | Risk hit is a banner line | **Structural**: a risk hit no longer parks; `sdlc:accept-risk` retires; `risk_list` takes globs at setup | 11, 21, 24 | R11 (the acceptance line); with or after R12; after 0005 (ratchet hits) | **Now** (rank 13) | Autonomy +++ (no park); attention ++ (accepted in an act already given); audit +; safety kept (an escalation still parks) |
| R25 | Weekly window guarded | **Structural**: every limit parks; ceiling and budget keys; a budget inside the design approval; a run-now label | 11, 24 | R10 (rounds, reset); R20 part 2 (for parts 3-4); R42's lesson shape (for part 5) | **Now**, parts 1-2 (every limit parks; spend shown on the PR). Parts 3-5 **later: R20 part 2 and the trial's spend data** | Parts 1-2: autonomy ++ and attention ++ (a park instead of a red run). Parts 3-5 gain mostly on cost (weight 0) |
| R26 | Measures that change a decision | Additive | none | R10's reset mark; R11's fix-round lines; R37 (part 3); R13 (DORA) | **Later**: parts 1-2 after R11 (wave 2); part 3 with R37; DORA after the trial has releases (wave 3) | Audit ++ and fidelity +; attention neutral |
| R27 | Policy sources (`policies/`) | **Structural** for guardrails only: a new owner-only path; optional sources written once per project | 6 | none | **Now** (rank 15). In client work, the client's standards and brand go here | Fidelity ++; audit + (the source's commit in the spec header); one optional setup act |
| R28 | Roles and the manager | **Structural**: changes what arrives at every approval, the interview, the per-agent keys and the role names; the manager acts in the owner's name through R22 | new decision; 4, 5, 13, 24, 21, 11 | R27; R7; R22 (for (e)); R17; R11; R24; R25 (part 7) | **Now**, parts 0-4 (rank 16). Parts 5-7 **later: R23, R43 and R25 parts 3-5** | Attention +++ (one recommendation to read); fidelity ++ (the playbook's roles); autonomy +; cost (weight 0) is one run per role. The largest item |
| R29 | Intent home | Additive: a second way to start a change; structural only at intake | none | the claude.ai route needs R17, R28 and a live connector check | **Now**, part 1 (the Examples/References section and the `Mock:` line), with R28 part 4. The claude.ai route **later: R17, R28 and the live check** | Attention ++ and autonomy + (start a change from the phone); fidelity + |
| R30 | Starting a project | Additive | none | none | **Now** (before the trial's `/sdlc-init`) | Attention + (what starts empty is said once); autonomy + (an optional start by hand); cheap |
| R31 | Tickets become intents | Additive: one optional label act | none | a live `issues labeled` check; R17; R22 (posts the check) | **Later: R17 and R22** (wave 2). Useful if the client files issues | Autonomy ++ (one label replaces a session); attention + |
| R32 | A rejection keeps its reason | Additive | none | none | **Later: any free slot** (wave 2 filler) | Audit +; tiny |
| R33 | Formatter per language | Additive: Python projects are unchanged | none | the Windows `.cmd` shim check first | **Now**: the trial is Node/TypeScript | Autonomy ++ (fewer red lint rounds); attention +; cheap |
| R34 | A fix proves itself | Additive: one new park reason, on fix changes only, using an existing act | none | 0005 built (`checks.py`); R10 for the round | **Later: 0005 and R10** (wave 2) | Audit ++ and fidelity ++ (p. 28, red before green); autonomy neutral |
| R35 | Eval suite grows | Additive: one narrow park at (e) | none (decision 17 gains a step) | R17 (or a coarse `if:` until then); R27 (the `policies/**` trigger) | **Later: R17 and R27** (wave 2). The trial supplies the 20 changes | Audit + and fidelity +; attention neutral |
| R36 | Runbook PRs reviewed | Additive | none | R41 point 3, or an interim step | **Now**, just before R22: ruleset 2 needs its check | Safety + and audit +; attention + (findings in the PR body) |
| R37 | CLAUDE.md standing PR | Additive: one merge replaces the by-hand line edits | none (the owner confirms how decision 6 reads) | a live check that a CLAUDE.md-only PR starts no run; R22 (posts the check) | **Later: R22** (wave 2); its brief with R28 | Attention ++ (one act for many lines); audit + (`repeat_of`) |
| R38 | Reviewer tuning | Additive | none | R37 (the standing-PR mechanism); R6 | **Later: R37 and the trial's review signals** (wave 3) | Attention + over time; fidelity + (p. 34); needs data |
| R39 | Preview and rehearsed rollback | Additive and opt-in. Structural only for a declared-production rollback with no `rehearse_command` (open) | 26, in one file with R41's | R10; R22 (the merge step); R18 | **Later: R10, R22 and the decision-26 file** (wave 3). Moves to wave 2 if the client wants a preview URL | Safety + and autonomy + (a red preview starts a round); attention + (the preview line); off by default |
| R40 | Detection state in the digest | Additive | none | R20 (places the line); R18; R16 first (the proposal's recommendation) | **Later: R16, R18 and R20** (wave 3). The trial's baseline needs 16 days with runs | Attention ++ (no artifacts to open); audit + (the history on a ref) |
| R41 | Acting at 3σ | Mostly additive. Narrows the Go to the owner's account; a new "Go requested" park on a declared production with no release in the window | 26 (14's Go narrowed), in one file with R39's | R17; the decision-26 file | **Later: R17 and the decision-26 file** (wave 3). Point 3 (the runner dispatches the route) can ship at any time | Safety ++ (no rollback of the wrong release); autonomy − in a rare case; audit + |
| R42 | Learning from incidents | Additive | none | R40; R20; R41 (the release reader) | **Later: R40** (wave 3). The scan-lesson part goes beside R43 | Audit +, fidelity + and attention + |
| R43 | Scan validates findings | Additive | none | none (best after R34; "Failed runs" with R18; the Scan line with R20) | **Later: R34 and R18** (wave 2). The weekly scan runs from the trial's first week | Attention ++ (low-confidence findings stop reaching the owner as Important); autonomy + |
| R44 | Sandbox closes gaps | Additive: a possible new park if the setup step finds `framework/` changed | none | the sandbox proof (queue item Q3); R27 for the `policies` entry | **Now** (rank 20): a Node install runs package scripts while the token is reachable, and this is client code | Safety ++, but safety weighs 1; other criteria neutral. See open point 5 |
| R45 | Names | **Structural**: every label, branch, command and key the owner reads or types | names only, in decisions 3, 10, 11, 13, 14, 18, 19, 25, 26 | its decision file first; every proposal is now written | **Now, split**: the decision file at rank 6; the rename as the last change of wave 1; later changes take their names from the decision file | Attention ++ (one vocabulary, learned once); fidelity ++ (the article's names); renaming wave-1 code once costs only money (weight 0) |

## 3. Table B: the proposed Order

"Owner's Order" is the current ROADMAP cell. The ranks are sequential. Items marked ∥ have no dependency and can be built in parallel with the rank before them.

### Wave 0: the queue before rank 1 (unchanged)

| Rank | Item | Owner's Order | Why / waits for |
|---|---|---|---|
| Q1 | Change 0005's build (R15 part 1, PR #211) | queued | unchanged |
| Q2 | The runs PR | queued | unchanged |
| Q3 | The sandbox proof, then the root pin | queued ("after the read") | unchanged; R44 needs it |

### Wave 1: structural changes and the trial's stack, before the real-project trial

| Rank | Item | Owner's Order (moved from) | Why / waits for |
|---|---|---|---|
| 1 | R7 | 1 | unchanged; R28 needs its model keys |
| 2 | R5 | 2 | unchanged (affects this repository only) |
| 3 | R6 | 3 | unchanged; R22 needs the accepted findings to turn `sdlc/review` green |
| 4 | R10 | 4 | unchanged. Settle open point 4 (who builds the reset) before its intent |
| 4a | The carried gaps (two plain PRs) | between 4 and 5 | unchanged |
| 5 | R14 | moved from "after R10" (no rank) **(rec.)** | its intent, #173, waits only for R10; a website's proof is screenshots and states |
| 6 | R45 part 1: the names decision file (documentation PR) | moved from "last" (study order; no rank) **(rec.)** | R45 already requires R11's keys to be judged before R11's design; every placeholder name can be judged now |
| 7 | R11 | moved from 6 (shift) | relative order unchanged |
| 8 | R12 + R13 (one change) | moved from 7-8 (shift) | relative order unchanged |
| 9 | R17 | "after R13" | unchanged; builds `is_owner_actor` for R22 |
| 10 | R36 | new | must exist before R22's ruleset 2 |
| 11 | R22 (decision file with R23's; the live App checks may run from rank 6) | new | after R6, R10, R11, R13 and R17 |
| 12 | R21 part 1 | new | puts R22's App and ruleset 2 in the desktop-only table |
| 13 | R24 (decision file with R25's) | new | after R11, R12 and 0005 |
| 14 | R25 parts 1-2 | new | after R10 |
| 15 | R27 (decision file with R28's) | new | none |
| 16 | R28 parts 0-4 | new | after R7, R27, R22 and R24 |
| 17 | R29 part 1 | new | rides with R28 part 4 (the interview's mock question) |
| 18 | R33 ∥ | new | none; the trial is Node/TypeScript |
| 19 | R30 ∥ | new | none; edits the change-0000 intent like R24, R27 and R33 do |
| 20 | R44 | new | after Q3 and R27 |
| 21 | R45 part 2: the rename, its old-name readers, the sample's migration | moved from "last" **(rec.)** | after all of wave 1, so wave-1 code is renamed once |
| — | **The real-project trial starts** (`/sdlc-init` on the client project) | | |

### Wave 2: during the trial (additive: what the owner reads, fewer acts)

| Rank | Item | Owner's Order (moved from) | Why / waits for |
|---|---|---|---|
| 22 | R18 | "after R10" | unchanged constraint; given a rank |
| 23 | R19, with R21 part 2 | "after R14" | unchanged constraint; R21's mark goes in R19's table |
| 24 | R20 | "after R18 and R19" | unchanged constraint |
| 25 | R25 parts 3-4 (ceiling, budget per change) | new | after R20 part 2, sized from the trial's spend (open point 3) |
| 26 | R23 | new | after R22 and R17; (f) begins once the trial's baseline fills |
| 27 | R15, second change | "after R10" | unchanged constraint |
| 28 | R34 | new | after 0005 and R10 |
| 29 | R43 | new | after R34 and R18 |
| 30 | R32 ∥ | new | none (filler) |
| 31 | R35 | new | after R17 and R27 |
| 32 | R31 | new | after R17 and R22; a live check first |
| 33 | R29, the claude.ai route | new | after R17 and R28; a live check first |
| 34 | R37 | new | after R22; its brief after R28 |
| 35 | R28 parts 5-6 | new | after R23 and R43 |
| 36 | R26 parts 1-3 | new | after R10's reset mark, R11 and R37 |
| 37 | R9 part 1 | moved from 5 **(rec.)** | additive; the owner's own "least urgent" |

### Wave 3: operations, once the trial has a baseline, releases and review signals

| Rank | Item | Owner's Order (moved from) | Why / waits for |
|---|---|---|---|
| 38 | R16 | no rank (proposed, "after 1.0.0") | before R40, so the record on the ref starts on one clock |
| 39 | R40 | new | after R16, R18 and R20 |
| 40 | The decision-26 file for R39 and R41 together | new | before either intent |
| 41 | R41 | new | after R17 and the decision file |
| 42 | R39 | new | after R10, R22 and the decision file; moves to wave 2 if the client wants previews |
| 43 | R42, with R25 part 5 | new | after R40 and R41; R25's overspend lesson uses its lesson shape |
| 44 | R28 part 7 | new | with R25's reset (decision 29's mark) |
| 45 | R26 part 4 (DORA) | new | after R13's release records exist on the trial |
| 46 | R38 | new | after R37 and the trial's review signals |
| 47 | R8 | "after R7" | unchanged constraint; starts after R7 has been measured on two changes |
| 48 | R45 part 3: a final sweep of any name not in the decision file | new | last; expected to be empty |

## 4. Before the real-project trial

**Minimal set** (the trial is not worth running without it):
- Queue items Q1 to Q3.
- R7, R6, R10, R11 and R17.
- R12 + R13, only if the trial declares a production.
- R36 then R22, R24, R25 parts 1-2, R27, R28 parts 0-4.
- R45: the decision file and the rename.
- For the stack: R14, R33 and R30.

**In wave 1 but not needed for the trial to start:**
- R5 (this repository only) and the carried gaps.
- R21 part 1: it helps the trial's setup from a phone.
- R29 part 1.
- R44: becomes part of the minimal set if the trial's CI holds client secrets (open point 5).

**Safe for the trial to ignore** (waves 2 and 3):
- The (f) items: R16, R23, R40, R41 and R42. Detection needs a filled baseline (16 days with runs) before it acts.
- R39: opt-in and off by default.
- Measures and tuning: R26 and R38.
- The standing PRs: R37 and R38.
- The other intake routes: R29's claude.ai route and R31. The trial starts changes with `/sdlc-plan`.
- R25 parts 3-5: cost weighs 0, and the trial supplies the spend numbers.
- R15's second change and R34 (fix-type changes only).
- R35, R32, R43, R18, R19 and R20: they change what the owner reads, not what the owner does, and today's digest works.
- R9 part 1 and R8.

## 5. Open points for the owner

1. R45: rename before the trial (rec.), or keep T4 last and migrate the client project after the trial?
2. R28 parts 0-4 before the trial (rec.; the largest piece of wave 1), or after it, with the trial on today's evidence (the acts are unchanged)?
3. R25's ceiling and budget (parts 3-5) after the trial, sized from its spend (rec.), or before it (which pulls R20 part 2 into wave 1)?
4. Who builds decision 29's manager reset: R10 (R25's recommendation) or R25 (R26 calls it open)? Answer before R10's intent.
5. R44 in wave 1 because of client code and npm install scripts (rec.), or later, since safety weighs 1?
6. R14 to rank 5 and R9 part 1 to wave 2 (both rec.): agree?
7. Batch the decision files into one documentation PR each for R22+R23, R24+R25, R27+R28 and R39+R41 (rec.)?
8. Will the trial project declare a production (`deploy.production: true`)? If not, R13 leaves the minimal set.
9. Does the client want a preview URL before approval? If yes, R39 moves to wave 2.
10. R22's fallback if the live App checks fail: C3 (an early merge is flagged) or C1 (the owner merges after approving)?
11. R41 presents the narrowing of the (c) and (d) labels to the owner's account as settled by R17, but no owner decision says so. Decide it in the decision-26 file?
12. *[Overtaken the same day: the open second-round findings and the R37-R40 cross-check findings were verified and applied by an Opus round in commit `518725e`; the few points no owner decision settles are marked open in their proposals.]*
