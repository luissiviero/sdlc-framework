---
type: Proposal
title: A risk-list hit is a line in the close-look banner — the merge accepts it, the reviewer briefs it, the paths are the project's
description: A risk-list hit no longer parks the change; it becomes a line of the "Needs your close look" banner on the PR the owner merges anyway (the design PR at (b), the build PR at (e)), quoting the gate's reviewer's brief on the item, and the owner's merge is the acceptance, recorded with who, when and that the banner showed it; each risk item lists the paths it covers, proposed by /sdlc-init and confirmed once; the sdlc:accept-risk label retires.
status: accepted
roadmap: R24
sources:
  - id: study-entry
    resource: docs/reviews/2026-09-28-playbook-vs-framework/target-design.md
    title: "T9, confirmed at the close of the study on 2026-10-09; from the crosswalk row build-risk (better: the framework; decision: blend, option C of three), 2026-10-03; annotation of 2026-10-13 (R15, ArtCraft row A3: a ratchet finding is a risk-list hit); index row T9"
  - id: crosswalk
    resource: docs/reviews/2026-09-28-playbook-vs-framework/crosswalk.json
    title: "Row build-risk whole; the decision fields of design-go and build-plan-approve (the banner and the acceptance line), setup-gates (the risk list), design-concerns (the never-to-the-panel list), x-roles (the Security & policy role) and test-gate (T12, which settles this entry's Full-profile item)"
  - id: record
    resource: docs/reviews/2026-09-28-playbook-vs-framework.md
    title: "Section 7, first bullet (the close, all 32 entries confirmed as recommended); section 8, part 1 (the close table row T9: rows build-risk, design-go, build-plan-approve, setup-gates, design-concerns; amends D11, D21, D24) and part 2 (the confirmed order: the gate changes T18, T23, T9, T30, T31)"
  - id: playbook
    resource: docs/reference/ai-native-sdlc-playbook.pdf
    title: "p.35: hooks can block edits to migrations and infra without a change ticket during Build, and can ask a specific person; p.36: the written list of approval gates, each a hook that allows, asks or blocks, a block that explains itself; p.37: the gate defines what counts as approval (an approved change ticket, the release manager's sign-off); p.6, p.14, p.17: humans stay accountable, higher risk goes to a technical lead, the acceptance logged with who accepted"
  - id: decision-11
    resource: docs/decisions/11.md
    title: "Decision 11: park, never page; a risk-list hit is one of the parks (amended here)"
  - id: decision-21
    resource: docs/decisions/21.md
    title: "Decision 21: deferred review; the risk-list hit is on the list that never goes to the panel and still parks (amended here: the hit leaves the hard-park list, an escalation on a risk item still parks)"
  - id: decision-24
    resource: docs/decisions/24.md
    title: "Decision 24: the owner's un-park verbs are labels, sdlc:accept-risk among them (amended here: that label retires, the by-hand command stays)"
  - id: decisions-27-29
    resource: docs/decisions/27.md
    title: "Decisions 27 (the (c) and (d) labels approve, R12), 28 (sdlc:accept-findings, named to match sdlc:accept-risk) and 29 (in CI a red target starts the next round), which postdate the study; read, none amended here"
  - id: r12-r15
    resource: docs/proposals/build-test-approvals-label.md
    title: "R12's third point (a risk hit first found at (c) or (d) shown in the waiting PR's banner, accepted only by the (e) merge), which is this entry's; with docs/proposals/ratchets.md (R15), point 3: a ratchet finding is a risk-list hit, and point 9: a measured fall recorded as one at the iteration-cap park"
  - id: code
    resource: plugin/gate/checks.py
    title: "risk_hits, check_risk_list and CHECKS_BY_PHASE; with plugin/state/unpark.py, plugin/state/status.py, plugin/state/conventions.py, plugin/ci/run_phase.py apply_owner_labels, plugin/pr/description.py, template/sdlc.yaml, template/.github/workflows/sdlc-fix.yml, template/changes/README.md, plugin/commands/sdlc-init.md, sdlc-design.md and sdlc-fix.md, plugin/agents/adversarial-reviewer.md, plugin/skills/spec-template and data-conventions, plugin/state/cli.py, plugin/release/cli.py, docs/OPERATING_MODEL.md; read at main 5542406, plugin 1.0.1"
generated: { by: sdlc-framework-session/ccr-01de3f80-ilnomi, at: 2026-10-15T20:00:00Z }
---

# A risk-list hit is a line in the close-look banner: the merge accepts it, the reviewer briefs it, the paths are the project's

**Status: proposed (roadmap R24), from study entry T9, confirmed by the owner on 2026-10-09, option C of the crosswalk row build-risk (the row's three options: today's label, B, C).** *[2026-10-20: accepted 2026-10-16 (PR #215); rank 8; the rank is read from ROADMAP's Order column]* Nothing is built. It amends decisions 11 and 21 (the risk-list hit leaves the hard-park list; an escalation on a risk item still parks) and decision 24 (`sdlc:accept-risk` retires); the decision file comes before the intent, in a documentation PR of its own, never with the intent; this proposal writes none and reserves no number. Third of the gate changes in the confirmed order (T18, T23, T9, T30, T31); it carries R12's third point, and it takes over the ratchet findings R15 records as risk-list hits.

## The problem

A risk-list hit parks the change, and accepting it costs the owner two acts and a session: the `sdlc:accept-risk` label, which starts a fix round that records the item and re-runs the phase, and then the merge the owner would give anyway[^entry]. A risk the design foresees is a flagged concern and parks at (b), before any code; one the design missed parks at (c) or (d), in an unattended build. Each park costs the same two acts and a session. And the check rarely sees a risk the design missed. It matches the item's words in the committed diff's file paths, so with the four default items most real paths pass: `db/migrations/0002.sql`, `alembic/versions/…`, `config/production.yaml`, `infra/main.tf`, `src/payments/…`, `src/authentication.py`. In practice a hit comes from the design naming the item under "Flagged concerns", and a missed risk is caught, if at all, by the adversarial reviewer's judgment. The `data-conventions` skill says a migration "parks at its next gate", which holds only for a path that carries both words.

## What the article says

The article puts risky edits behind a human approval. "Hooks can block edits to migrations and infra without a change ticket during Stage 3: Build", and a hook "can also ask, pausing the action until a specific person approves" (p.35). Engineering leadership lists "the human approval gates that must survive, such as change management sign-off, release authorization, and edits to protected paths"; each becomes a hook that can "allow, ask, or block", and "a block should explain itself", with "the reason and the route to approval" (p.36). "The gate also defines what counts as approval, whether that's an approved change ticket or the release manager's sign-off" (p.37)[^playbook]. Accepting a risk is a named person's act: "humans remain accountable for every decision that requires judgment", and the chain of commits records "who approved it" (p.6). Anything "the organization classes as higher risk" goes to a technical lead or architect (p.14, p.17), and the plan's acceptance is "logged along with who accepted it" (p.17).

## What the framework does today

Read at `main` 5542406, plugin 1.0.1. The entry's "Today" was read at 619f01a (0.3.5). Since then `git diff 619f01a 5542406` on the files below changes `run_phase.py`, `checks.py`, `description.py`, `template/sdlc.yaml` and `docs/OPERATING_MODEL.md`, but none of its added or removed lines mentions the risk list (`git diff … | grep -i risk` is empty), so every line the entry describes still holds[^code].

- **The list.** `template/sdlc.yaml:97-102` holds four items, `auth`, `data migrations`, `money movement`, `production config`, with the comment "a hit parks the change at its next gate". `/sdlc-init` asks no question about it. Its question round (`plugin/commands/sdlc-init.md:30-42`) names the risk list only in the sentence that says a hit "still park[s] in both modes".
- **The check.** `check_risk_list` (`plugin/gate/checks.py:732-779`) runs at every gate from (a) to (f) (`CHECKS_BY_PHASE`, `checks.py:1697`, `:1705`, `:1719`, `:1734`, `:1749`, `:1763`). `risk_hits` (`:715-729`) matches each item's words whole and plural-tolerant. It reads the committed diff's file paths and the "Flagged concerns" section of `spec.md` at HEAD, never the files' contents. A live hit fails the check, and the failure tells the owner to run `state/cli.py accept-risk` (`:770-777`). The word match also reads the change folder's own path. Run on the sample paths above, `risk_hits` on `main` returns `{'auth': ['auth/login.py', 'changes/0007-auth-login/intent.md'], 'data migrations': ['data/migrations/1.sql']}`: the six real paths pass, while a change whose slug carries an item's word hits (command output, this session), and so parks at each gate whose committed diff carries a file of the change folder, until the item is accepted.
- **The acceptance.** `sdlc:accept-risk` (`plugin/state/conventions.py:81`, one of `UNPARK_LABELS`, `:84`) triggers `sdlc-fix.yml` (`template/.github/workflows/sdlc-fix.yml:3`, `:85`). The runner performs the labels first (`plugin/ci/run_phase.py:2037` `apply_owner_labels`). `unpark.risk_hits` reads the hits the phase's last gate recorded (`plugin/state/unpark.py:68-84`). With none it rejects the label as "nothing to accept" (`:115-124`). Otherwise `record_owner_label` writes `risk_accepted` and `risk_accepted_by` with the label's actor (`plugin/state/status.py:222-235`), and an accepted item holds for the rest of the change (`checks.py:743`, `:768`). The runner refuses any `risk_accepted` change the session made itself (`run_phase.py:2153-2169`). The by-hand `accept-risk` command stays (`plugin/state/cli.py:14`, `:499`).
- **A merge over a park.** When the owner merges a build PR whose gate (e) parked, a risk-list hit among the reasons, the release prints the park reason and waits for `sdlc:release-approved` whether or not production is declared (`plugin/release/cli.py:32-34`, `:591-594`, `:612-631`; `docs/OPERATING_MODEL.md:60`). `release/cli.py` is unchanged between 619f01a and 5542406.
- **Where a hit comes from in practice.** The design command makes every risk-list item the design touches a flagged concern, "the gate reads that section literally and parks on every item named there" (`plugin/commands/sdlc-design.md:102-106`; `plugin/skills/spec-template/SKILL.md:61-65`). The adversarial reviewer's blast-radius angle reads `risk_list` as judgment at (b) to (d) (`plugin/agents/adversarial-reviewer.md:46-48`). Its verdict carries `verdict`, `classification` and reasons, with no field for a risk item (`checks.py:783-800` `load_verdict`).
- **No banner, no acceptance line.** `plugin/pr/description.py` has no "Needs your close look" banner; the PR bodies carry one "What needs you" line from `GATE_CHECKLIST` (`:96`, `:340`, `:409`, `:583`). `run_phase.py` writes no plan-acceptance line (no match for "plan accepted"). Both are confirmed study targets (design-go, build-plan-approve; R11's approvals list), not built.
- **The documents that say a hit parks or name the label.** That a hit parks: `template/sdlc.yaml:97`, `:105-109`; `plugin/skills/data-conventions/SKILL.md:23-26` (rule 3); `docs/OPERATING_MODEL.md:41`, `:43`, `:60`, `:105`, `:129`; `plugin/commands/sdlc-init.md:36`; `plugin/commands/sdlc-design.md:102-106`; `plugin/skills/spec-template/SKILL.md:61-65`; the check's failure text (`checks.py:770-777`). The label or the command only: `docs/OPERATING_MODEL.md:76`; `template/changes/README.md:21`; `plugin/commands/sdlc-fix.md:85`.
- **After the close.** R15 (ArtCraft A3, accepted 2026-10-13) records an undeclared dropped test or eval case as a risk-list hit named after the ratchet (`ratchet: tests`, `ratchet: evals`), accepted by `sdlc:accept-risk` until this entry is built and by the banner after. A drop the approved plan declares is to show "as a banner line once T9 is built"[^r15]. R15's second change measures the counts: a fall is a red entry of the commands step under decision 29, and only at the iteration-cap park is it recorded as a risk-list hit, "so the owner can accept a drop by the label, because no act clears a red target" (`docs/proposals/ratchets.md:82`, point 9). Its first change, 0005, passed gate (b) as PR #186 and is not built on `main` (no `ratchet` in `checks.py` at 5542406). R12 (accepted 2026-10-13, decision 27) leaves its third point to this entry: under the Full profile a hit first found at (c) or (d) shows in the waiting PR's banner, and only the (e) merge accepts it[^r12].

## The proposal

The owner's choice, condensed; nothing added to it.

1. **The banner replaces the park.** A risk-list hit no longer parks. It becomes a line of design-go's "Needs your close look" banner on the PR the owner merges anyway. A hit found at (b) goes on the design PR. A hit first found at (c), (d) or (e) goes on the build PR at (e). Under the Full profile it also shows in the banner of the PR waiting for the `sdlc:c-approved` or `sdlc:d-approved` label, so the owner can stop it with "Request changes", but only the (e) merge accepts it (settled at test-gate, T12; R12's third point).
2. **The merge is the acceptance, recorded.** The runner records which items were accepted, by whom, when, and that the banner showed them. The record goes in `status.yaml`, beside build-plan-approve's plan-acceptance line. The merge actor comes from the merged pull request, as for that line. This is the article's change ticket turned into the owner's informed merge. Settled since at x-audit (T32, R11): the (b) acceptance is a line of R11's approvals list whose details map carries the risk items accepted. Where a hit accepted at (e) is recorded, x-audit does not say (see "What to settle").
3. **The reviewer's brief on each item.** At each gate where an item hits, that gate's reviewer writes a short brief per item: what the change does to it, what could break, how to undo it. The reviewer is the adversarial reviewer at (b) to (d), the REVIEW.md pass at (e), and the Security & policy role once T1 exists (R28). The banner quotes the brief. The reviewer never accepts a risk. Its escalation on a risk item still parks for the owner, and risk items stay off the panel. No extra run: these reviewers already run at those gates.
4. **Each risk item lists its paths.** An item gains the globs it covers. `/sdlc-init` proposes them from the project's layout (a migrations folder, `infra/`, production configuration), and the owner confirms the list once in the change-0000 PR. The check matches the globs on the committed diff and, as today, the item's words in "Flagged concerns".
5. **The label retires.** `sdlc:accept-risk` is no longer needed; the by-hand `state/cli.py accept-risk` stays.
6. **What it gives up.** A risky build the design did not foresee is no longer stopped at (c) or (d); it runs on to (e) in the CI sandbox. Nothing is released before the owner's (e) merge, and on a declared production the release still waits for `sdlc:release-approved`. Without a declared production the (e) merge releases, as for any change, with the risk accepted in the same act.
7. **The ratchet findings (2026-10-13, R15).** A ratchet finding is a risk-list hit named after the ratchet. It becomes a banner line that the owner's merge accepts, as every risk-list hit does, and a drop the approved plan declares shows as a banner line too.
8. **The skill's sentence.** The `data-conventions` skill's "parks at its next gate" is corrected when this is built (recorded only, no issue filed).

What it meets elsewhere, not proposed here: the banner's other lines are the non-routine plan's reasons and, with T1, the Architect's recommendation (design-go and build-plan-approve; R28); R13's line on `sdlc:release-approved`. R22 adds no line: its (e) approval is informed by the REVIEW.md findings and this banner. The act's row in R19's "What you can do here" loses `sdlc:accept-risk`, and the acceptance shows in the merge's row instead.

## How it is judged

This proposal's suggestion; the entry names no measure. Judge it on the next changes that touch a risk item, on the sample project first:

- No change parks on a risk-list hit.
- Every hit shows in a banner with the reviewer's brief.
- Every accepted item has its line, with actor, time and "banner shown".
- With the confirmed globs, a migration, an infrastructure file and a production configuration file each hit, while the same paths miss today.

The failure is a hit that reaches the (e) merge without its banner line. Measured before and after: the owner's acts per accepted risk, two and a fix session today, none beyond the merge after.

## What to settle before building

Rows marked *(mine)* are this proposal's additions, not the entry's.

| Question | Recommended |
|---|---|
| The shape of a risk item with paths in `sdlc.yaml`, and what `/sdlc-init` proposes per stack (entry, Open) | *(mine)* A mapping per item, `item:` (its words, still matched in "Flagged concerns") and `paths:` (globs on the committed diff). A plain-string item stays valid and keeps today's word match on paths until the owner adds globs, so a project that upgrades loses nothing. `/sdlc-init` proposes only globs for folders that exist, for example `**/migrations/**`, `alembic/versions/**`, `infra/**`, `**/*.tf`, `config/production.*`, `**/auth/**`, `**/payments/**`, and the owner keeps or edits them in the change-0000 PR. `sdlc.yaml` stays the owner's guardrail edit (decision 6) |
| Where the reviewer's brief goes: a field of the adversarial reviewer's verdict file, or a file of its own, and how the REVIEW.md pass gives one at (e) (entry, Open) | *(mine)* A file of its own. x-roles point (3) settled the analogous case (the plan's three answers go to the Architect brief's file, written by the adversarial reviewer until the roles exist). Here, the brief per hit item goes to the file the Security & policy role will own under `evidence/roles/`, written by the adversarial reviewer at (b) to (d) and the REVIEW.md pass at (e) until R28. The banner then reads one place before and after T1 |
| Under Full, whether `sdlc:c-approved` or `sdlc:d-approved` also accepts a hit first found at (c) or (d) (entry, Open) | **Settled** at test-gate, 2026-10-03 (T12), and carried by R12's third point (accepted 2026-10-13): only the (e) merge accepts it; the waiting PR's banner shows the hit |
| The `data-conventions` skill's sentence that a migration parks (entry, Open) | **Settled** by the entry: corrected when T9 is built, recorded only, no issue. *(mine)* The other documents that say a hit parks (listed in "What the framework does today") are corrected in the same change |
| How an escalation "on a risk item" is told from another | *(mine)* The brief names the item and carries the reviewer's word on it. An `escalate` verdict whose reasons cite a hit item parks under `review: deferred` too, never going to the panel (decision 21's fixed list keeps risk items off it) |
| Where a hit first found at (c) to (e) and accepted by the (e) merge is recorded | *(mine)* Until R22 is built, a details map on the (e) merge line of R11's list (the items, the banner shown), the shape x-audit gives the (b) line; or a line of its own. Once R22 is built, the same map on R22's (e) approval line (next row), and R22's list of that line's fields gains the accepted risk items. The owner's words place it "beside build-plan-approve's plan-acceptance line" |
| R15's measured ratchet fall once the label retires (R15 point 9: recorded as a risk-list hit at the iteration-cap park, accepted by the label) | *(mine)* Two ways: the cap park stays and only the by-hand `accept-risk` lifts it; or the recorded hit, like every hit, no longer parks, the `ratchets` entry stops being red for the later gates, and the change runs on to (e), where the fall is a banner line the owner's merge accepts. Recommended: the second, which costs no act beyond the merge, as option C intends. It is not a reading of what is kept: it amends R15 point 9 (the recorded hit lifts the cap park for this entry) and makes one exception to decision 29's park at the iteration cap, a limit park under decision 11, so the decision file names both if the owner takes it. The first keeps both unchanged. Settled with R15's second change, which meets this one |
| The release guard on a merge over a parked gate (e) (`release/cli.py` 4c) | *(mine)* Today a hit merged over a parked gate (e) waits for the release label even without a declared production ("A merge over a park" above); since a hit no longer parks, that wait ends for it. Unchanged in the code: a guardrail change or the iteration cap still sets `parked_reason`, and a hit no longer does. `docs/OPERATING_MODEL.md:60` drops "a risk-list hit" from its list. The decision file says that, without a declared production, a hit accepted by the (e) merge releases on it |
| Whose act is the (e) acceptance once R22 is built | *(mine)* The owner's approving review, which R22 makes gate (e), recorded on R22's (e) approval line with the banner shown. The App's merge is its consequence. Until R22, the merge actor |
| A hit at (a) or (f), and the change folder's own path | *(mine)* Globs never match under `changes/`, so a slug such as `0007-auth-login` no longer hits (it does today, command output above). At (a) and (f) `design_scope` keeps the diff inside the change folder, so the check stays there as a record with nothing to accept. The exception is change 0000's install PR, which `design_scope` exempts at (a) (`checks.py:930-935`) and which carries `sdlc.yaml`, the workflows and the pin script: the globs are matched on it too, and a hit there is a banner line the owner's (a) merge accepts, the same merge that confirms the globs |
| An item accepted at (b) and touched again at (c) to (e) | *(mine)* It holds for the change, as `risk_accepted` does today. The (e) banner lists it as "accepted at (b)" with the new paths and the brief, and asks for no second acceptance |
| Which proposal builds the banner | *(mine)* One generated block in `plugin/pr/description.py`, from the gate record and the briefs, built by this proposal, or by R28's part 1 if that comes first (R28 places it so; R12 and R22 name the banner as T9's, R13 as T9's and T18's). R13, which comes earlier in the order, has its release line rendered by whichever of those two builds the block. Before T1 it shows the adversarial reviewer's class reasons and the risk hits (design-go). This proposal adds the risk lines |

## Considered and not chosen

- **Keeping today's label** (the first of build-risk's three): two acts and a fix session to accept what the owner merges anyway.
- **Option B of build-risk**: the merge accepts at (b) only, and a hit first found later still parks for the label.
- **A hook that blocks risk paths during (c) unless the item was accepted at (b)**: closer to the article (p.35), but in an unattended run it only moves the park earlier and leaves the work half done.
- **An agent that accepts a risk for the owner**: the agents run on the session's own model and share its blind spots. Accepting a risk is the accountable act the article gives a named person (p.6, p.37), and a record that reads "risk accepted by an agent" would claim more than a model can give (T1: a brief, never an approval).

## Decisions it touches

- **11 and 21 are amended.** The risk-list hit leaves the hard-park list. An escalation on a risk item still parks, and risk items stay off the panel.
- **24 is amended.** `sdlc:accept-risk` retires, one label fewer, and the by-hand `accept-risk` command stays. Decision 28's `sdlc:accept-findings` is unchanged; it was named to match `sdlc:accept-risk`, and whether that name still fits once the label retires is left to R45 (T4, the names) *(mine)*.
- **One decision file, before the intent.** It is written in a documentation PR the owner reviews on its own, never with the intent, as decisions 27, 28 and 29 were. This proposal writes no decision file and reserves no number.
- **Kept.**
  - 2 and 18: one approval at (b), no separate gate.
  - 27: the (c) and (d) labels approve the phase. That they accept no risk is R12's third point (test-gate, T12), built here.
  - 6: the risk list stays in a guardrail file.
  - 13: the release on a declared production still waits for its label; R22 amends 13 separately.
  - 29: in CI a red target starts the next fix round and parks only at the iteration cap. R15's measured ratchet fall is such a red entry, recorded as a risk-list hit only at that park (R15 point 9). Kept unless the owner takes this proposal's recommendation for that fall, which would amend R15 point 9 and make one exception to 29's cap park (see "What to settle").
  - 20: nothing notifies the owner.

## Order

Tenth of the study's proposals in the confirmed order (the record, section 8: T32, T12, T21; T17, T19, T27, T28; then the gate changes T18, T23, T9, T30, T31), after R22 and R23. *[2026-10-20: rank 8 (choice 234), before R22 (9) and R23 (31); the Order column supersedes the study's order; the rank is read from ROADMAP's Order column]* It changes `plugin/` and `template/`, so it ships as a plugin version with tests and reaches a project through `/sdlc-init`. Its dependencies:

- After **R11**: the acceptance lines are R11's.
- With or after **R12**: R12's third point is built here.
- After **R15's first change (0005)**: its ratchet hits move from the label to the banner here, and `unpark.risk_hits` reads them. Meets R15's second change: the measured fall recorded as a hit at the cap (see "What to settle").
- Meets **R13** (the banner's release line) and **R22** (the (e) act, informed by the banner).
- Meets **R19**: its acts table drops the label.
- Meets **R28**: the Security & policy brief, written by the adversarial reviewer until then. R28 already gives that role the brief on each risk-list item hit at (b) to (e), as the owner's note does (`docs/proposals/roles-and-manager.md`, its catalogue row and its (b) higher-risk and (e) gate rows), so R28 needs no change for it.
- Meets **R30** and **R33**: `/sdlc-init` proposing per stack.
- Meets **R45**: the banner's and the item key's names.

| Part | Where | When |
|---|---|---|
| The decision file amending 11, 21 and 24 | `docs/decisions/` | First, in a documentation PR of its own |
| Risk items with globs; `/sdlc-init` proposes them | `template/sdlc.yaml`, `plugin/init/`, `plugin/commands/sdlc-init.md`, `checks.py` `risk_hits` | Now |
| The check reports, never parks; the escalation on a risk item still parks | `checks.py` `check_risk_list`, the panel routing | Now |
| The brief per hit item | `plugin/agents/adversarial-reviewer.md`, the REVIEW.md pass, the brief file | Now; the Security & policy role with R28 |
| The banner's risk lines, at (b), (e) and the Full-profile waiting PR | `plugin/pr/description.py` | Now, or after R28's part 1 if that builds the banner first |
| The acceptance record | R11's approvals list, written by the runner | With or after R11 |
| `sdlc:accept-risk` retired (labels, `sdlc-fix.yml`, `unpark.py`, `conventions.py`); the CLI kept | `plugin/state/`, `template/.github/workflows/sdlc-fix.yml` | Now, with R15's ratchet hits moved to the banner |
| The release guard on a merge over a parked gate (e): unchanged, since a hit no longer sets `parked_reason` | `plugin/release/cli.py` (no change) | Same change, checked by a test |
| The documents that say a hit parks or name the label, the `data-conventions` sentence among them | `plugin/skills/`, `plugin/commands/`, `template/`, `docs/OPERATING_MODEL.md` (`:60` among them) | Same change |

[^entry]: `docs/reviews/2026-09-28-playbook-vs-framework/target-design.md`, T9 ("Today", the owner's note, "Direction discussed", "Open"); the crosswalk row build-risk.
[^playbook]: `docs/reference/ai-native-sdlc-playbook.pdf` p.6, p.14, p.17, p.35-37.
[^code]: At 5542406: `plugin/gate/checks.py` `risk_hits`, `check_risk_list`, `load_verdict`, `CHECKS_BY_PHASE`; `plugin/state/unpark.py`; `plugin/state/status.py`; `plugin/state/conventions.py`; `plugin/state/cli.py`; `plugin/ci/run_phase.py` `apply_owner_labels`; `plugin/pr/description.py`; `plugin/release/cli.py`; `template/sdlc.yaml`; `template/.github/workflows/sdlc-fix.yml`; `template/changes/README.md`; `docs/OPERATING_MODEL.md`; `plugin/commands/sdlc-init.md`, `sdlc-design.md`, `sdlc-fix.md`; `plugin/agents/adversarial-reviewer.md`; `plugin/skills/spec-template/SKILL.md`, `data-conventions/SKILL.md`.
[^r15]: `docs/proposals/ratchets.md`, "The proposal", points 2, 3 and 9; ROADMAP R15's status (change 0005, PR #186); the annotation of 2026-10-13 beside T9's status.
[^r12]: `docs/proposals/build-test-approvals-label.md`, point 3 and its settle row; ROADMAP R12's status ("its third point … is T9's and is built with or after T9's own proposal"); `docs/decisions/27.md`.
